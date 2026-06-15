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
import threading
import time

from state_mirror.classifier import Classifier, Entry, Handler
from state_mirror.handlers import make_handler
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
        # Per-sqlite-DB change fingerprint and last-poll time, so a DB is only
        # snapshotted when it changed and no more often than its poll_interval_ms.
        self._sql_sigs: dict[str, tuple] = {}
        self._sql_last_poll: dict[str, float] = {}
        self.state = state or HealthState()
        self._resolver = PathResolver(classifier.entries)
        self._lock = threading.Lock()
        self._dirty: set[str] = set()
        self._deletes: list[tuple[str, str]] = []
        self._max_queue = max(1, max_queue)
        # Set when a delete is dropped (overflow) or fails (backend down) so the
        # next full scan reconciles orphaned stored objects (D2 recovery).
        self._delete_reconcile_needed = False
        self._last_ship: dict[str, float] = {}
        self._wakeup = threading.Event()
        self._event_handler = MirrorEventHandler(
            self._resolver, self._mark_dirty, self._mark_delete
        )
        self._observer = None

    def _mark_dirty(self, entry: Entry) -> None:
        with self._lock:
            self._dirty.add(entry.path)
        self.state.inc_events()
        self._wakeup.set()

    def _mark_delete(self, entry: Entry, fs_path: str) -> None:
        dropped = 0
        with self._lock:
            # D2 drop policy: bound memory during a long backend outage. When the
            # delete queue is full, drop the OLDEST pending delete and flag a
            # reconcile so the dropped delete is recovered by the next full scan
            # (eventual consistency) rather than leaking a stale stored key.
            while len(self._deletes) >= self._max_queue:
                self._deletes.pop(0)
                dropped += 1
                self._delete_reconcile_needed = True
            self._deletes.append((entry.path, fs_path))
        if dropped:
            log.warning(
                "delete queue full (max=%d); dropped %d oldest delete(s), will reconcile",
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
            deletes = list(self._deletes)
            self._dirty = set()
            self._deletes = []
        ops = 0
        requeue: set[str] = set()
        for path in dirty:
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
            try:
                if handler.mirror():
                    ops += 1
                self._last_ship[path] = now
                self.state.record_store_ok()
            except Exception as exc:
                reason = _reason(exc)
                log.exception("event mirror failed for %s [%s]; will retry", path, reason)
                self.state.record_store_down(reason)
                requeue.add(path)
        for entry_path, fs_path in deletes:
            handler = self._by_path.get(entry_path)
            if handler is None:
                continue
            try:
                ops += self._apply_delete(handler.entry, fs_path)
                self.state.record_store_ok()
            except Exception as exc:
                reason = _reason(exc)
                log.exception("event delete failed for %s [%s]; will reconcile", entry_path, reason)
                self.state.record_store_down(reason)
                # Don't requeue (avoids unbounded growth / busy-loop on a long
                # outage); flag a reconcile so the next full scan drops the
                # orphaned stored object once the backend is reachable again (D2).
                with self._lock:
                    self._delete_reconcile_needed = True
        if requeue:
            with self._lock:
                self._dirty |= requeue
        if ops:
            self.state.add_mirror_ops(ops)
        return ops

    def _apply_delete(self, entry: Entry, fs_path: str) -> int:
        handler = self._by_path.get(entry.path)
        if handler is None:
            return 0
        if entry.is_directory:
            handler.on_delete_child(os.path.relpath(fs_path, entry.path))
        else:
            handler.on_delete()
        return 1

    def full_scan(self) -> int:
        """Mirror every entry whose body differs from the store. Returns #sent.

        Also runs a delete reconcile when a delete was previously dropped or
        failed (D2), so orphaned stored objects are removed once the backend recovers.
        """
        sent = 0
        for handler in self._handlers:
            try:
                if handler.mirror():
                    sent += 1
                self.state.record_store_ok()
            except Exception as exc:
                reason = _reason(exc)
                log.exception("mirror failed for %s [%s]", handler.entry.path, reason)
                self.state.record_store_down(reason)
        with self._lock:
            reconcile_needed = self._delete_reconcile_needed
        if reconcile_needed and self._reconcile_deletes():
            with self._lock:
                self._delete_reconcile_needed = False
        self.state.inc_full_scans()
        if sent:
            self.state.add_mirror_ops(sent)
        return sent

    def _reconcile_deletes(self) -> bool:
        """Remove stored objects whose local file no longer exists (D2 recovery).

        Returns True only if every handler reconciled without a backend error, so
        the caller keeps the reconcile flag set (and retries next scan) until it
        fully succeeds.
        """
        ok = True
        removed = 0
        for handler in self._handlers:
            try:
                removed += handler.reconcile_deletes()
                self.state.record_store_ok()
            except Exception as exc:
                reason = _reason(exc)
                log.exception("delete reconcile failed for %s [%s]", handler.entry.path, reason)
                self.state.record_store_down(reason)
                ok = False
        if removed:
            log.warning("delete reconcile removed %d orphaned stored object(s)", removed)
            self.state.add_mirror_ops(removed)
        return ok

    def poll_sqlite(self, now: float | None = None) -> int:
        now = time.monotonic() if now is None else now
        sent = 0
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
            # WAL-aware change fingerprint: skip if nothing changed.
            sig = handler.signature()
            if sig == self._sql_sigs.get(path):
                continue
            try:
                if handler.mirror():
                    sent += 1
                self._sql_sigs[path] = sig
                self.state.record_store_ok()
            except Exception as exc:
                reason = _reason(exc)
                log.exception("sqlite snapshot failed for %s [%s]", path, reason)
                self.state.record_store_down(reason)
        if sent:
            self.state.add_mirror_ops(sent)
        return sent

    def start_watching(self) -> None:
        """Arm the watchdog observer. Fail-soft: poll-only if it can't start."""
        try:
            self._observer = build_observer(self._resolver, self._event_handler)
            self._observer.start()
            log.info("watchdog observer started")
            self.state.mark_watching(watchdog_active=True)
        except Exception:
            log.exception("watchdog observer failed to start; running poll-only")
            self.state.mark_watching(watchdog_active=False)

    def run_forever(self, scan_interval_s: float = 60.0, poll_interval_s: float = 0.5) -> None:
        self.start_watching()
        log.info("startup full scan (%d entries)", len(self._handlers))
        self.full_scan()
        self.state.mark_startup_scan_done()
        last_scan = time.monotonic()
        while True:
            try:
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
                    pending = len(self._deletes)
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

    state = HealthState()
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
