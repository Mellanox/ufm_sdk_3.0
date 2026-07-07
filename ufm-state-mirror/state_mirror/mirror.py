#
# Copyright © 2009-2026 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

"""StateMirror runtime sidecar: continuously mirror emptyDir -> storage backend
(HLD 5.3.2 / 5.3.7).

Change detection is event-driven (watchdog) and drained on a short loop so the
watch callback never blocks on backend I/O. A periodic full scan reconciles
anything events missed, and SQLite DBs are polled by their change-counter. All
backend failures are caught, classified, and surfaced via the health/metrics
state -- a backend outage degrades mirroring but never crashes the sidecar
(which would lose the emptyDir).
"""

from __future__ import annotations

import logging
import os
import sqlite3
import threading
import time
from collections import OrderedDict
from contextlib import suppress

from state_mirror.classifier import Classifier, Entry, Handler
from state_mirror.handlers import MirrorResult, make_handler
from state_mirror.handlers.base import path_exists
from state_mirror.handlers.sqlite import SqliteHandler
from state_mirror.health import DEFAULT_PORT, HealthServer, HealthState
from state_mirror.redis_errors import classify_redis_error
from state_mirror.watcher import MirrorEventHandler, PathResolver, build_observer

log = logging.getLogger("state_mirror.mirror")

# D2: upper bound on the in-memory delete queue. The dirty queue is a set keyed
# by entry path, so it is already bounded by the number of classifier entries;
# the delete queue fans out per directory child and is the one that can grow
# during a long backend outage, so it gets an explicit cap with a drop policy.
DEFAULT_MAX_QUEUE = 100_000


def _reason(exc: BaseException) -> str:
    """Best reason for a failed mirror op: the WireError's classified reason if
    present (set at the store boundary, by the active backend's classifier),
    else fall back to a generic transport/OS classification.
    """
    if isinstance(exc, sqlite3.Error):
        return "local_io"
    return getattr(exc, "reason", None) or classify_redis_error(exc)


class Mirror:
    def __init__(
        self,
        classifier: Classifier,
        store,
        ufm_version: str,
        written_by: str,
        state: HealthState | None = None,
        max_queue: int = DEFAULT_MAX_QUEUE,
    ):
        self.store = store
        self._handlers = [
            make_handler(e, store, ufm_version, written_by) for e in classifier.entries
        ]
        self._by_path = {h.entry.path: h for h in self._handlers}
        # Per-sqlite-DB last-poll time so a DB is fingerprinted no more often than
        # its poll_interval_ms. The change fingerprint itself lives on the handler
        # (SqliteHandler gates its own snapshot), so there is no signature cache here.
        self._sql_last_poll: dict[str, float] = {}
        self.state = state or HealthState()
        self._resolver = PathResolver(classifier.entries)
        self._lock = threading.Lock()
        self._dirty: set[str] = set()
        # Deletes the sidecar actually *observed* (watchdog delete/move-out),
        # awaiting propagation. Keyed by store key so duplicates collapse and the
        # drift scan can exclude them; value is (entry_path, fs_path). Only keys in
        # here are ever removed from the backend -- an unobserved missing file is
        # drift, never a delete (HLD 5.3.7/5.3.9, "the backend wins on ambiguity").
        self._pending_deletes: OrderedDict[str, tuple[str, str]] = OrderedDict()
        self._max_queue = max(1, max_queue)
        # Keys already counted as missing-local drift. Usually the backend still
        # has the object; an observed SQLite deletion is retained here even if
        # its backend snapshot is absent, because only local reappearance ends
        # that operator-error onset (HLD 5.3.7/5.3.9).
        self._known_drift: set[str] = set()
        self._last_ship: dict[str, float] = {}
        self._wakeup = threading.Event()
        self._event_handler = MirrorEventHandler(
            self._resolver, self._mark_dirty, self._mark_delete
        )
        self._observer = None

    def _mark_dirty(self, entry: Entry) -> None:
        with self._lock:
            self._dirty.add(entry.path)
        if entry.handler is Handler.SQLITE and entry.redis_key:
            try:
                reappeared = path_exists(entry.path)
            except OSError as exc:
                log.error("cannot inspect dirty SQLite path %s: %s", entry.path, exc)
                self.state.record_error(_reason(exc), backend_unreachable=False)
            else:
                if reappeared:
                    with self._lock:
                        self._known_drift.discard(entry.redis_key)
        self.state.inc_events()
        self._wakeup.set()

    def _mark_delete(self, entry: Entry, fs_path: str) -> None:
        handler = self._by_path.get(entry.path)
        if handler is None:
            return
        key = handler.key_for_fs_path(fs_path)
        if isinstance(handler, SqliteHandler):
            try:
                reappeared = path_exists(fs_path)
            except OSError as exc:
                log.error("cannot inspect deleted SQLite path %s: %s", fs_path, exc)
                with self._lock:
                    self._dirty.add(entry.path)
                self.state.record_error(_reason(exc), backend_unreachable=False)
                self.state.inc_events()
                self._wakeup.set()
                return
            if reappeared:
                # The delete event raced with DB recreation. Mirror the current
                # file, but do not open an unexpected-delete onset.
                with self._lock:
                    self._dirty.add(entry.path)
                    self._known_drift.discard(key)
                self.state.inc_events()
                self._wakeup.set()
                return
            with self._lock:
                new_onset = key not in self._known_drift
                self._known_drift.add(key)
            log.error(
                "sqlite database deleted locally; retaining backend snapshot for restore: %s",
                entry.path,
            )
            if new_onset:
                self.state.inc_unexpected_deletes()
            self.state.inc_events()
            self._wakeup.set()
            return
        dropped = 0
        with self._lock:
            # Collapse duplicate observations of the same key; keep it newest.
            self._pending_deletes.pop(key, None)
            self._pending_deletes[key] = (entry.path, fs_path)
            # D2 drop policy: bound memory during a long backend outage by dropping
            # the OLDEST pending delete (O(1) on an OrderedDict). A dropped delete
            # is simply not propagated -- the file stays in the backend and is
            # re-materialized on the next restore (the backend wins), so we never
            # leak unbounded memory and never mistakenly delete on ambiguity.
            while len(self._pending_deletes) > self._max_queue:
                self._pending_deletes.popitem(last=False)
                dropped += 1
        if dropped:
            log.warning(
                "delete queue full (max=%d); dropped %d oldest delete(s); "
                "those files stay in the backend until next restore",
                self._max_queue,
                dropped,
            )
            self.state.inc_dropped_events(dropped)
        self.state.inc_events()
        self._wakeup.set()

    def drain_once(self, now: float, rate_limited: bool = True) -> int:
        """Process queued watchdog marks. Returns the number of store ops.

        Honors each entry's ``rate_limit_ms`` so a hot file is coalesced rather
        than shipped on every event; deferred paths are requeued.
        """
        with self._lock:
            dirty = list(self._dirty)
            self._dirty = set()
        ops = 0
        aggregate = MirrorResult()
        requeue: set[str] = set()
        for path in dirty:
            self.state.heartbeat()
            handler = self._by_path.get(path)
            if handler is None:
                continue
            entry = handler.entry
            if (
                rate_limited
                and entry.rate_limit_ms
                and path in self._last_ship
                and (now - self._last_ship[path]) * 1000.0 < entry.rate_limit_ms
            ):
                requeue.add(path)
                continue
            result = self._mirror_handler(handler)
            self._record_result(result)
            aggregate = aggregate.plus(result)
            ops += result.writes
            if result.failures:
                log.error("event mirror failed for %s; will retry", path)
                requeue.add(path)
            else:
                self._last_ship[path] = now
        if requeue:
            with self._lock:
                self._dirty |= requeue
        deleted = self.flush_pending_deletes()
        aggregate = aggregate.plus(deleted)
        ops += deleted.writes
        if aggregate.backend_failures:
            self.state.mark_backend_unreachable()
        if ops:
            self.state.add_mirror_ops(ops)
        return ops

    def flush_pending_deletes(self) -> MirrorResult:
        """Propagate observed deletes to the backend; retry the ones that failed.

        Only keys the sidecar actually observed being deleted are in
        ``_pending_deletes``, so this never removes a backend object for a file
        that merely went missing unobserved (that is drift -- see
        :meth:`_scan_unexpected_deletes`). A delete whose file reappeared before
        we propagated it is dropped (no longer a delete). The result preserves
        successful deletes and failures separately for aggregate health.
        """
        with self._lock:
            items = list(self._pending_deletes.items())
        writes = 0
        failures: list[BaseException] = []
        for key, (entry_path, fs_path) in items:
            self.state.heartbeat()
            try:
                reappeared = path_exists(fs_path)
            except OSError as exc:
                reason = _reason(exc)
                log.exception("cannot inspect pending delete %s [%s]; retaining it", key, reason)
                self.state.record_error(reason, backend_unreachable=False)
                failures.append(exc)
                continue
            if reappeared:
                with self._lock:
                    self._pending_deletes.pop(key, None)
                continue
            try:
                self._apply_delete(entry_path, fs_path)
                with self._lock:
                    self._pending_deletes.pop(key, None)
                writes += 1
                self.state.record_write_ok()
            except Exception as exc:
                reason = _reason(exc)
                log.exception("delete failed for %s [%s]; will retry next cycle", key, reason)
                self.state.record_store_down(reason)
                failures.append(exc)
        return MirrorResult(writes=writes, failures=tuple(failures))

    def _apply_delete(self, entry_path: str, fs_path: str) -> None:
        handler = self._by_path.get(entry_path)
        if handler is None:
            return
        if handler.entry.is_directory:
            handler.on_delete_child(os.path.relpath(fs_path, entry_path))
        else:
            handler.on_delete()

    def full_scan(self) -> MirrorResult:
        """Mirror every entry and report all work and failures.

        Also retries any observed-but-unpropagated deletes and accounts for
        unobserved drift (HLD 5.3.7). Heartbeats per entry so a slow backend can
        extend the scan without tripping the liveness probe.
        """
        aggregate = MirrorResult()
        for handler in self._handlers:
            self.state.heartbeat()
            result = self._mirror_handler(handler)
            self._record_result(result)
            aggregate = aggregate.plus(result)
        flushed = self.flush_pending_deletes()
        aggregate = aggregate.plus(flushed)
        aggregate = aggregate.plus(self._scan_unexpected_deletes())
        if aggregate.backend_failures:
            # Successful siblings may have followed a failed operation. Preserve
            # their write/read accounting, but let any backend failure win final
            # reachability for this aggregate reconcile. Local failures still
            # make the reconcile unsuccessful without misreporting the backend.
            self.state.mark_backend_unreachable()
        elif aggregate.reads:
            # Drift enumeration is itself a backend read. This matters when all
            # local entries were no-ops: a successful scan must clear a prior
            # outage even though no handler read or wrote an object body.
            self.state.record_read_ok()
        self.state.inc_full_scans()
        if aggregate.writes:
            self.state.add_mirror_ops(aggregate.writes)
        return aggregate

    def _scan_unexpected_deletes(self) -> MirrorResult:
        """Count keys present in the backend whose local file vanished (HLD 5.3.7).

        Does not delete anything (the backend wins on ambiguity); only bumps
        ``state_mirror_unexpected_delete_total`` for keys newly entering drift, so
        the gap is visible instead of silent. Keys with an observed delete still
        pending propagation are excluded -- those are intended deletes, not drift.
        Reads only, so it never updates the last-write timestamp (which would
        mask mirror lag).
        """
        with self._lock:
            pending = set(self._pending_deletes)
            known_at_start = set(self._known_drift)
        current: set[str] = set()
        failures: list[BaseException] = []
        reads = 0
        for handler in self._handlers:
            self.state.heartbeat()
            try:
                # The handler reports actual backend activity; inferring it from
                # path presence is racy when a file appears during the scan.
                handler_drift, backend_reads = handler.drift_scan()
                current.update(handler_drift)
                if (
                    isinstance(handler, SqliteHandler)
                    and handler.entry.redis_key in known_at_start
                    and not path_exists(handler.entry.path)
                ):
                    # Observed SQLite deletion is an operator-error onset even
                    # when no durable snapshot exists. Do not count it again
                    # until the DB actually reappears.
                    current.add(handler.entry.redis_key)
                reads += backend_reads
            except Exception as exc:
                reason = _reason(exc)
                log.exception("drift check failed for %s [%s]", handler.entry.path, reason)
                self.state.record_error(
                    reason, backend_unreachable=MirrorResult.failure_affects_backend(exc)
                )
                failures.append(exc)
                # A failed scope is unknown, not healthy. Retain its previous
                # drift-onset state so a transient outage cannot double-count
                # the same missing SQLite DB on the next successful scan.
                current.update(
                    key for key in known_at_start if self._key_belongs_to_handler(key, handler)
                )
        current -= pending
        final_presence_errors: list[BaseException] = []
        with self._lock:
            # Watchdog callbacks may add a SQLite onset or clear one on local
            # reappearance while this backend scan is running. Merge additions
            # and honor removals so the scan cannot overwrite newer event state.
            current |= self._known_drift - known_at_start
            current -= known_at_start - self._known_drift
            for handler in self._handlers:
                if not isinstance(handler, SqliteHandler) or not handler.entry.redis_key:
                    continue
                try:
                    present = path_exists(handler.entry.path)
                except OSError as exc:
                    final_presence_errors.append(exc)
                    # Presence is unknown: preserve the latest onset state,
                    # including a watchdog update that arrived during the scan.
                    if handler.entry.redis_key in self._known_drift:
                        current.add(handler.entry.redis_key)
                    else:
                        current.discard(handler.entry.redis_key)
                    continue
                if present:
                    current.discard(handler.entry.redis_key)
            new_drift = current - self._known_drift
            self._known_drift = current
        for exc in final_presence_errors:
            reason = _reason(exc)
            log.exception("final SQLite presence check failed [%s]", reason, exc_info=exc)
            self.state.record_error(reason, backend_unreachable=False)
            failures.append(exc)
        if new_drift:
            log.warning(
                "drift: %d object(s) present in backend but missing locally; "
                "keeping backend copy (HLD 5.3.7): %s",
                len(new_drift),
                sorted(new_drift),
            )
            self.state.inc_unexpected_deletes(len(new_drift))
        return MirrorResult(reads=reads, failures=tuple(failures))

    @staticmethod
    def _key_belongs_to_handler(key: str, handler) -> bool:
        if handler.entry.is_directory:
            return key.startswith(handler.entry.redis_key_prefix)
        return key == handler.entry.redis_key

    def poll_sqlite(self, now: float | None = None) -> int:
        now = time.monotonic() if now is None else now
        sent = 0
        aggregate = MirrorResult()
        for handler in self._handlers:
            if handler.entry.handler is not Handler.SQLITE or not isinstance(
                handler, SqliteHandler
            ):
                continue
            path = handler.entry.path
            # Per-DB rate limit: bound snapshot frequency (cheap for small DBs,
            # important once a DB is large).
            interval_s = handler.entry.poll_interval_ms / 1000.0
            last = self._sql_last_poll.get(path)
            if last is not None and (now - last) < interval_s:
                continue
            self._sql_last_poll[path] = now
            self.state.heartbeat()
            result = self._mirror_handler(handler)
            self._record_result(result)
            aggregate = aggregate.plus(result)
            sent += result.writes
            if handler.last_snapshot_seconds is not None:
                self.state.set_snapshot_duration(
                    os.path.basename(path), handler.last_snapshot_seconds
                )
        if sent:
            self.state.add_mirror_ops(sent)
        if aggregate.backend_failures:
            self.state.mark_backend_unreachable()
        return sent

    def _mirror_handler(self, handler) -> MirrorResult:
        try:
            return handler.mirror()
        except Exception as exc:
            reason = _reason(exc)
            log.exception("mirror failed for %s [%s]", handler.entry.path, reason)
            return MirrorResult(failures=(exc,))

    def _record_result(self, result: MirrorResult) -> None:
        """Apply activity first, then record failures by their health domain."""
        if result.writes:
            self.state.record_write_ok()
        elif result.reads:
            self.state.record_read_ok()
        for exc in result.failures:
            self.state.record_error(
                _reason(exc),
                backend_unreachable=MirrorResult.failure_affects_backend(exc),
            )

    def _cleanup_observer(self, observer) -> None:
        with suppress(Exception):
            observer.stop()
        with suppress(RuntimeError, AttributeError):
            observer.join(timeout=5.0)

    @staticmethod
    def _observer_healthy(observer) -> bool:
        """Require the dispatcher and every scheduled emitter to be alive."""
        if observer is None or not observer.is_alive():
            return False
        emitters = getattr(observer, "emitters", None)
        return emitters is None or all(emitter.is_alive() for emitter in emitters)

    def start_watching(self) -> bool:
        """Arm every required watchdog watch; return whether strict setup passed."""
        try:
            setup = build_observer(self._resolver, self._event_handler)
            if not setup.complete:
                for exc in setup.failures:
                    log.error("required watchdog setup failed: %s", exc)
                self.state.mark_watching(False, all_required_armed=False)
                return False
            observer = setup.observer
            observer.start()
            if not self._observer_healthy(observer):
                raise RuntimeError("watchdog observer or required emitter did not become active")
            self._observer = observer
            log.info("watchdog observer started")
            self.state.mark_watching(True, all_required_armed=True)
            return True
        except Exception:
            log.exception("watchdog observer failed to start")
            if "observer" in locals():
                self._cleanup_observer(observer)
            self._observer = None
            self.state.mark_watching(False, all_required_armed=False)
            return False

    def startup_once(self) -> bool:
        """Attempt watcher setup plus one fail-closed startup reconcile.

        Clear the reconcile gate first: a watcher recovered from an earlier
        attempt must not combine with that attempt's successful scan and expose
        readiness before the current scan has completed.
        """
        self.state.mark_initial_reconcile(False)
        watchers_ok = self._observer_healthy(self._observer)
        if not watchers_ok and self._observer is not None:
            self._cleanup_observer(self._observer)
            self._observer = None
            self.state.mark_watching(False, all_required_armed=False)
        if watchers_ok:
            self.state.mark_watching(True, all_required_armed=True)
        if not watchers_ok:
            watchers_ok = self.start_watching()
        result = self.full_scan()
        if not result.backend_failures and result.backend_ops == 0:
            try:
                self.store.probe()
                self.state.record_read_ok()
                result = result.plus(MirrorResult(reads=1))
            except Exception as exc:
                log.exception("startup backend probe failed")
                self.state.record_store_down(_reason(exc))
                result = result.plus(MirrorResult(failures=(exc,)))

        # The initial reconcile can be slow. Recheck after it completes so an
        # observer that died during the scan cannot satisfy strict readiness.
        watchers_ok = self._observer_healthy(self._observer)
        if not watchers_ok and self._observer is not None:
            self._cleanup_observer(self._observer)
            self._observer = None
        self.state.mark_watching(watchers_ok, all_required_armed=watchers_ok)
        if not watchers_ok and self.state.allow_poll_only:
            log.warning("UNSUPPORTED poll-only mode enabled; readiness may pass without watchdog")
        watcher_gate = watchers_ok or self.state.allow_poll_only
        self.state.mark_initial_reconcile(result.succeeded)
        return result.succeeded and watcher_gate

    def run_forever(
        self,
        scan_interval_s: float = 60.0,
        poll_interval_s: float = 0.5,
        startup_retry_s: float = 2.0,
    ) -> None:
        """Run the mirror loop until the process is killed.

        ``scan_interval_s`` (default 60s) is how often the periodic full scan
        reconciles anything the watch events missed. ``poll_interval_s`` (default
        0.5s) is the loop wake interval that drains queued watch events -- it is
        NOT the per-DB SQLite cadence, which is each entry's ``poll_interval_ms``
        enforced inside :meth:`poll_sqlite`.
        """
        while not self.startup_once():
            log.error("startup reconcile incomplete; retrying in %.1fs", startup_retry_s)
            self._wakeup.wait(timeout=startup_retry_s)
            self._wakeup.clear()
        log.info("startup reconcile complete; sidecar ready")
        last_scan = time.monotonic()
        while True:
            try:
                if self._observer is not None and not self._observer_healthy(self._observer):
                    log.error("watchdog observer stopped after readiness; running degraded")
                    self._cleanup_observer(self._observer)
                    self._observer = None
                    self.state.mark_watching(False, all_required_armed=False)
                self._wakeup.wait(timeout=poll_interval_s)
                self._wakeup.clear()
                now = time.monotonic()
                self.drain_once(now=now)
                # poll_sqlite enforces each DB's own poll_interval_ms internally.
                self.poll_sqlite(now=now)
                if now - last_scan >= scan_interval_s:
                    self.full_scan()
                    last_scan = now
                with self._lock:
                    dirty_depth = len(self._dirty)
                    pending = len(self._pending_deletes)
                self.state.tick(dirty_depth=dirty_depth, pending_deletes=pending)
            except Exception:
                log.exception("mirror loop iteration failed; retrying")


def main() -> int:
    from state_mirror.backends import backend_from_env, build_store
    from state_mirror.logconfig import setup_logging

    global log
    log = setup_logging("state_mirror.mirror")
    classifier_path = os.environ.get("CLASSIFIER_PATH", "/etc/state_mirror/state_mirror.yaml")
    ufm_version = os.environ.get("UFM_VERSION", "unknown")
    written_by = "state-mirror:" + os.environ.get("STATE_MIRROR_GIT_SHA", "dev")
    port = int(os.environ.get("STATE_MIRROR_METRICS_PORT", DEFAULT_PORT))
    max_queue = int(os.environ.get("STATE_MIRROR_MAX_QUEUE", DEFAULT_MAX_QUEUE))
    log.info("state-mirror sidecar starting (ufm_version=%s, max_queue=%d)", ufm_version, max_queue)

    allow_poll_only = os.environ.get("STATE_MIRROR_ALLOW_POLL_ONLY", "false").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    state = HealthState(allow_poll_only=allow_poll_only)
    HealthServer(state, port=port).start()
    try:
        classifier = Classifier.load_file(classifier_path)
        store = build_store(backend_from_env())
        mirror = Mirror(
            classifier, store, ufm_version, written_by, state=state, max_queue=max_queue
        )
    except Exception:
        log.exception("state-mirror sidecar failed to initialize")
        return 1
    mirror.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
