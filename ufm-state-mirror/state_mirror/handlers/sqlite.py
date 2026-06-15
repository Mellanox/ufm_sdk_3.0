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

"""SQLite handler (HLD 5.3.4 / Phase 5): snapshot-only.

Naive file-level mirroring of a live SQLite DB can capture a mid-transaction
state, so we never copy the file bytes directly. Instead we take a consistent
copy with the SQLite online backup API and mirror the whole DB as one blob,
only when the DB actually changed. This is the right fit for UFM's DBs, which
are small (gv.db is typically < 50 MiB) and comfortably under the backend's
object size limits.

There is no WAL-shipping: every cycle ships a full, consistent snapshot rather
than a base + incremental ``-wal`` segment (HLD 5.5). The handler never changes
a DB's journal mode -- it only reads.

Change detection: a counter-only poll would miss live writes on a WAL-mode DB,
because in WAL mode a write lands in ``-wal`` and does NOT bump the main DB
header's change counter until a checkpoint. ``signature()`` therefore combines
the header change counter with the ``-wal`` file's size and mtime, so it is
correct whether the DB is in rollback-journal or WAL mode.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import tempfile
import time

from state_mirror.handlers.base import BaseHandler

log = logging.getLogger(__name__)

# SQLite DB header layout: the 4-byte big-endian file change counter lives at
# offset 24 (https://www.sqlite.org/fileformat.html#file_change_counter).
_CHANGE_COUNTER_OFFSET = 24
_CHANGE_COUNTER_SIZE = 4
_HEADER_MIN_SIZE = _CHANGE_COUNTER_OFFSET + _CHANGE_COUNTER_SIZE


class SqliteHandler(BaseHandler):
    # Wall-clock (seconds) of the most recent online-backup snapshot, surfaced as
    # state_mirror_snapshot_duration_seconds{db=...} for the Phase 5 / R2 gate
    # ("snapshot-duration headroom under load"). None until the first snapshot.
    last_snapshot_seconds: float | None = None

    # ---- change detection --------------------------------------------------
    @staticmethod
    def _wal_path(db_path: str) -> str:
        return db_path + "-wal"

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

    # ---- snapshot (online backup) -----------------------------------------
    def snapshot_bytes(self) -> bytes:
        """Consistent copy of the live DB via the SQLite online backup API.

        Records the wall-clock of the backup in :attr:`last_snapshot_seconds` so
        the loop can publish ``state_mirror_snapshot_duration_seconds`` (HLD 5.3.4).
        """
        fd, tmp = tempfile.mkstemp(prefix="statemirror-sqlite-", suffix=".db")
        os.close(fd)
        try:
            started = time.perf_counter()
            src = sqlite3.connect(f"file:{self.entry.path}?mode=ro", uri=True, timeout=30.0)
            try:
                dst = sqlite3.connect(tmp, timeout=30.0)
                try:
                    src.backup(dst)
                finally:
                    dst.close()
            finally:
                src.close()
            self.last_snapshot_seconds = time.perf_counter() - started
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
        body = self.snapshot_bytes()
        sent = self._push_if_changed(self.entry.redis_key, body)
        if sent:
            log.info(
                "mirror: shipped sqlite snapshot %s (%d bytes) -> %s",
                self.entry.path,
                len(body),
                self.entry.redis_key,
            )
        return sent

    # ---- restore -----------------------------------------------------------
    def restore(self) -> bool:
        """Restore the snapshot and verify integrity.

        Fails closed (raises) on an integrity-check failure so the init
        container never lets UFM start on a corrupt DB.
        """
        result = self.store.get(self.entry.redis_key)
        if result is None:
            log.debug("restore: no stored object for %s", self.entry.path)
            return False
        body, _meta = result
        self._write_file(self.entry.path, body)
        self.integrity_check(self.entry.path)
        log.info(
            "restore: wrote %s (%d bytes) from %s",
            self.entry.path,
            len(body),
            self.entry.redis_key,
        )
        return True
