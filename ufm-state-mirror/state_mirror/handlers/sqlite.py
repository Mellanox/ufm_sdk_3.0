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

"""SQLite handler (HLD 5.3.4 / Phase 5).

Naive file-level mirroring of a live SQLite DB can capture a mid-transaction
state, so we never copy the file bytes directly. Two strategies, chosen by DB
size against a configurable threshold (default 256 MiB):

* **snapshot** (DB < threshold) -- the common case for every realistic UFM
  deployment (gv.db is typically < 50 MiB; telemetry history is opt-in). Take a
  consistent copy with the SQLite online backup API and mirror the whole DB as
  one blob, only when the DB actually changed.

* **WAL-shipping** (DB >= threshold) -- a safety valve for very large DBs where
  re-sending the whole file each cycle is wasteful. Mirror a periodic base
  snapshot plus the incremental ``-wal`` segment; rotate to a fresh base (and
  drop the old WAL) once the WAL itself grows past the threshold. Each base/WAL
  pair is tagged with an epoch so restore only ever pairs a base with the WAL
  that belongs to it.

WAL ownership: these DBs ship from UFM in rollback-journal mode. The
``state-mirror-restore`` init container converts every restored DB to WAL mode
before UFM starts (see ``restore()``), and the running sidecar enables WAL
lazily for fresh-install DBs created after restore (``_ensure_wal``). UFM never
sets the journal mode itself, so the sidecar owns it end to end.

Change detection: in WAL mode a write lands in ``-wal`` and does NOT bump the
main DB header's change counter until a checkpoint, so a counter-only poll would
miss live writes. ``signature()`` therefore combines the header change counter
with the ``-wal`` file's size and mtime.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import tempfile

from state_mirror import wire
from state_mirror.handlers.base import BaseHandler

log = logging.getLogger(__name__)

# SQLite DB header layout: the 4-byte big-endian file change counter lives at
# offset 24 (https://www.sqlite.org/fileformat.html#file_change_counter).
_CHANGE_COUNTER_OFFSET = 24
_CHANGE_COUNTER_SIZE = 4
_HEADER_MIN_SIZE = _CHANGE_COUNTER_OFFSET + _CHANGE_COUNTER_SIZE

# Default DB-size threshold to switch from full snapshots to WAL-shipping.
# Overridable per-entry (classifier ``wal_threshold_bytes``) or globally via the
# STATE_MIRROR_WAL_THRESHOLD_BYTES env var.
DEFAULT_WAL_THRESHOLD_BYTES = 256 * 1024 * 1024
_WAL_THRESHOLD_ENV = "STATE_MIRROR_WAL_THRESHOLD_BYTES"


def _env_threshold() -> int:
    raw = os.environ.get(_WAL_THRESHOLD_ENV)
    if not raw:
        return DEFAULT_WAL_THRESHOLD_BYTES
    try:
        value = int(raw)
    except ValueError:
        log.warning("%s=%r is not an integer; using default", _WAL_THRESHOLD_ENV, raw)
        return DEFAULT_WAL_THRESHOLD_BYTES
    if value <= 0:
        log.warning("%s=%d must be > 0; using default", _WAL_THRESHOLD_ENV, value)
        return DEFAULT_WAL_THRESHOLD_BYTES
    return value


class SqliteHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._threshold = self.entry.wal_threshold_bytes or _env_threshold()
        # WAL is enabled lazily (once) on the live DB the first time we mirror a
        # fresh-install DB; restored DBs already get WAL set in restore().
        self._wal_enabled = False
        # Header change counter captured when the current WAL-ship base was last
        # shipped. Used to detect that the DB was checkpointed out-of-band (e.g.
        # UFM closing a connection auto-checkpoints, folding the WAL into the main
        # file): the counter advances, so we re-ship a fresh base rather than an
        # incremental WAL that no longer contains those pages.
        self._last_base_cc: int | None = None

    # ---- key helpers (WAL-shipping layout) --------------------------------
    @property
    def _epoch_key(self) -> str:
        return f"{self.entry.redis_key}:epoch"

    def _wal_key(self, epoch: int) -> str:
        return f"{self.entry.redis_key}:wal:{epoch}"

    @staticmethod
    def _wal_path(db_path: str) -> str:
        return db_path + "-wal"

    # ---- change detection --------------------------------------------------
    @staticmethod
    def read_change_counter(path: str) -> int:
        """Return the DB header's file_change_counter (0 if unreadable)."""
        try:
            with open(path, "rb") as f:
                header = f.read(_HEADER_MIN_SIZE)
        except FileNotFoundError:
            return 0
        except OSError as exc:
            log.warning("change-counter read of %s failed: %s; treating as unchanged", path, exc)
            return 0
        if len(header) < _HEADER_MIN_SIZE:
            return 0
        return int.from_bytes(header[_CHANGE_COUNTER_OFFSET:_HEADER_MIN_SIZE], "big")

    def signature(self) -> tuple[int, int, int]:
        """A cheap change fingerprint: (header change counter, wal size, wal mtime).

        Includes the ``-wal`` file because WAL-mode writes don't bump the header
        change counter until a checkpoint.
        """
        cc = self.read_change_counter(self.entry.path)
        try:
            st = os.stat(self._wal_path(self.entry.path))
            return (cc, st.st_size, st.st_mtime_ns)
        except OSError:
            return (cc, -1, -1)

    # ---- WAL mode management ----------------------------------------------
    @staticmethod
    def enable_wal(path: str) -> bool:
        """Switch a DB to WAL journal mode. Best-effort; returns True on success."""
        try:
            conn = sqlite3.connect(path, timeout=30.0)
            try:
                mode = conn.execute("PRAGMA journal_mode=WAL;").fetchone()
            finally:
                conn.close()
        except sqlite3.Error as exc:
            log.warning("could not enable WAL on %s: %s", path, exc)
            return False
        ok = bool(mode) and str(mode[0]).lower() == "wal"
        if not ok:
            log.warning("WAL not enabled on %s (journal_mode=%s)", path, mode)
        return ok

    @staticmethod
    def integrity_check(path: str) -> None:
        """Run PRAGMA integrity_check; raise sqlite3.DatabaseError if not 'ok'."""
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=30.0)
        try:
            row = conn.execute("PRAGMA integrity_check;").fetchone()
        finally:
            conn.close()
        result = row[0] if row else None
        if result != "ok":
            raise sqlite3.DatabaseError(f"integrity_check failed for {path}: {result!r}")

    def _ensure_wal(self) -> None:
        if not self._wal_enabled:
            self._wal_enabled = self.enable_wal(self.entry.path)

    # ---- snapshot (online backup) -----------------------------------------
    def snapshot_bytes(self, wal_mode: bool = False) -> bytes:
        """Consistent copy of the DB via the online backup API.

        When ``wal_mode`` is set the returned bytes are a WAL-mode DB (header
        marked WAL, no outstanding frames) so a shipped ``-wal`` can be applied
        on restore; otherwise a plain rollback-journal copy is returned.
        """
        fd, tmp = tempfile.mkstemp(prefix="statemirror-sqlite-", suffix=".db")
        os.close(fd)
        try:
            src = sqlite3.connect(f"file:{self.entry.path}?mode=ro", uri=True, timeout=30.0)
            try:
                dst = sqlite3.connect(tmp, timeout=30.0)
                try:
                    src.backup(dst)
                    if wal_mode:
                        dst.execute("PRAGMA journal_mode=WAL;")
                        dst.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                finally:
                    dst.close()
            finally:
                src.close()
            with open(tmp, "rb") as f:
                return f.read()
        except sqlite3.Error as exc:
            log.error("sqlite snapshot of %s failed: %s", self.entry.path, exc)
            raise
        finally:
            for suffix in ("", "-wal", "-shm"):
                self._safe_unlink(tmp + suffix)

    @staticmethod
    def _safe_unlink(path: str) -> None:
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            log.warning("could not remove temp file %s", path)

    # ---- mirror ------------------------------------------------------------
    def mirror(self) -> bool:
        if not os.path.exists(self.entry.path):
            log.debug("mirror: sqlite db %s does not exist yet, skipping", self.entry.path)
            return False
        try:
            size = os.path.getsize(self.entry.path)
        except OSError as exc:
            log.warning("mirror: cannot stat %s: %s; skipping", self.entry.path, exc)
            return False
        if size == 0:
            log.debug("mirror: sqlite db %s is empty, skipping", self.entry.path)
            return False
        self._ensure_wal()
        if size < self._threshold:
            return self._mirror_snapshot()
        return self._mirror_wal_ship()

    def _mirror_snapshot(self) -> bool:
        body = self.snapshot_bytes()
        sent = self._push_if_changed(self.entry.redis_key, body)
        if sent:
            log.info(
                "mirror: shipped sqlite snapshot %s (%d bytes) -> %s",
                self.entry.path,
                len(body),
                self.entry.redis_key,
            )
        # Always drop any WAL-shipping keys left over from a time the DB was
        # large, so a later restore never applies a stale segment on the base.
        self._clear_wal_keys()
        return sent

    def _mirror_wal_ship(self) -> bool:
        epoch = self._read_epoch()
        wal_size = self._wal_size()
        cc = self.read_change_counter(self.entry.path)
        # Rotate (re-ship a fresh base) when: there is no base yet, this handler
        # has not established a base since it started, the WAL has grown past the
        # threshold, or the DB was checkpointed out-of-band (counter advanced).
        if (
            epoch == 0
            or self._last_base_cc is None
            or cc != self._last_base_cc
            or wal_size >= self._threshold
        ):
            sent = self._rotate(new_epoch=epoch + 1, old_epoch=epoch)
            # Capture the post-checkpoint counter so plain WAL growth (no
            # checkpoint) afterwards is shipped incrementally.
            self._last_base_cc = self.read_change_counter(self.entry.path)
            return sent
        return self._ship_wal_segment(epoch)

    def _ship_wal_segment(self, epoch: int) -> bool:
        wal_path = self._wal_path(self.entry.path)
        try:
            with open(wal_path, "rb") as f:
                wal_body = f.read()
        except FileNotFoundError:
            return False
        except OSError as exc:
            log.warning("mirror: cannot read %s: %s", wal_path, exc)
            return False
        sent = self._push_if_changed(self._wal_key(epoch), wal_body)
        if sent:
            log.info(
                "mirror: shipped wal segment %s (%d bytes, epoch=%d) -> %s",
                wal_path,
                len(wal_body),
                epoch,
                self._wal_key(epoch),
            )
        return sent

    def _rotate(self, new_epoch: int, old_epoch: int) -> bool:
        """Checkpoint the live DB, ship a fresh WAL-mode base, advance the epoch.

        The base + epoch advance + old-WAL delete are written in one transaction
        so a restore never pairs a new base with a stale WAL (or vice versa).
        """
        self._checkpoint_truncate()
        base = self.snapshot_bytes(wal_mode=True)
        meta = wire.build_meta(
            base,
            handler=self.entry.handler.value,
            ufm_version=self.ufm_version,
            written_by=self.written_by,
        )
        body_key = self.entry.redis_key
        self.store.write_transaction(
            puts=[(body_key, base, meta)],
            value_puts=[(self._epoch_key, str(new_epoch).encode("ascii"))],
            deletes=[self._wal_key(old_epoch)] if old_epoch else [],
        )
        log.info(
            "mirror: rotated %s to epoch=%d (base %d bytes) -> %s",
            self.entry.path,
            new_epoch,
            len(base),
            body_key,
        )
        return True

    def _checkpoint_truncate(self) -> None:
        try:
            conn = sqlite3.connect(self.entry.path, timeout=30.0)
            try:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            finally:
                conn.close()
        except sqlite3.Error as exc:
            log.warning("checkpoint of %s failed: %s", self.entry.path, exc)

    def _read_epoch(self) -> int:
        raw = self.store.get_value(self._epoch_key)
        if raw is None:
            return 0
        try:
            return int(raw)
        except (ValueError, TypeError):
            log.warning("invalid epoch %r for %s; treating as 0", raw, self.entry.redis_key)
            return 0

    def _wal_size(self) -> int:
        try:
            return os.path.getsize(self._wal_path(self.entry.path))
        except OSError:
            return 0

    def _clear_wal_keys(self) -> None:
        """Drop any WAL-shipping keys when we fall back to snapshot mode."""
        self._last_base_cc = None
        epoch = self._read_epoch()
        if epoch == 0:
            return
        try:
            self.store.write_transaction(
                deletes=[self._wal_key(epoch)],
                value_deletes=[self._epoch_key],
            )
        except Exception as exc:
            log.warning("could not clear stale wal keys for %s: %s", self.entry.redis_key, exc)

    # ---- restore -----------------------------------------------------------
    def restore(self) -> bool:
        """Restore base (+ matching WAL segment), enable WAL, verify integrity.

        Fails closed (raises) on an integrity-check failure so the init
        container never lets UFM start on a corrupt DB.
        """
        result = self.store.get(self.entry.redis_key)
        if result is None:
            log.debug("restore: no stored object for %s", self.entry.path)
            return False
        base, _meta = result
        self._write_file(self.entry.path, base)

        epoch = self._read_epoch()
        if epoch:
            wal = self.store.get(self._wal_key(epoch))
            if wal is not None:
                self._write_file(self._wal_path(self.entry.path), wal[0])
                log.info(
                    "restore: applied wal segment epoch=%d (%d bytes) for %s",
                    epoch,
                    len(wal[0]),
                    self.entry.path,
                )

        self._finalize_restore(self.entry.path)
        log.info(
            "restore: wrote %s (%d bytes base) from %s",
            self.entry.path,
            len(base),
            self.entry.redis_key,
        )
        return True

    def _finalize_restore(self, path: str) -> None:
        """Fold any restored WAL into the DB, leave it WAL-mode, verify integrity."""
        try:
            conn = sqlite3.connect(path, timeout=30.0)
            try:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            finally:
                conn.close()
        except sqlite3.Error as exc:
            log.error("restore finalize of %s failed: %s", path, exc)
            raise
        self.integrity_check(path)
        self._wal_enabled = True
