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

"""Unit tests for the Phase 5 SQLite handler: WAL enablement, integrity-checked
restore, online-backup snapshots, and WAL-shipping (rotation + incremental)."""

import os
import sqlite3

import pytest

from state_mirror import wire
from state_mirror.classifier import Entry
from state_mirror.handlers.sqlite import (
    DEFAULT_WAL_THRESHOLD_BYTES,
    SqliteHandler,
    _env_threshold,
)
from state_mirror.store import RedisStore

UFM_VERSION = "7.0.1"
WRITTEN_BY = "state-mirror:test"


def _make_db(path, rows):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
    conn.executemany("INSERT INTO t (v) VALUES (?)", [(r,) for r in rows])
    conn.commit()
    conn.close()


def _row_count(path):
    conn = sqlite3.connect(path)
    try:
        return conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
    finally:
        conn.close()


def _journal_mode(path):
    conn = sqlite3.connect(path)
    try:
        return conn.execute("PRAGMA journal_mode;").fetchone()[0].lower()
    finally:
        conn.close()


def _handler(path, fake_redis, **entry_overrides):
    raw = {
        "path": str(path),
        "handler": "sqlite",
        "redis_key": "ufm:sqlite:gv.db",
        "snapshot_method": "online_backup",
    }
    raw.update(entry_overrides)
    entry = Entry.from_dict(raw)
    return SqliteHandler(entry, RedisStore(fake_redis), UFM_VERSION, WRITTEN_BY)


class TestThresholdConfig:
    def test_default_threshold(self, monkeypatch):
        monkeypatch.delenv("STATE_MIRROR_WAL_THRESHOLD_BYTES", raising=False)
        assert _env_threshold() == DEFAULT_WAL_THRESHOLD_BYTES

    def test_env_threshold(self, monkeypatch):
        monkeypatch.setenv("STATE_MIRROR_WAL_THRESHOLD_BYTES", "12345")
        assert _env_threshold() == 12345

    def test_env_threshold_invalid_falls_back(self, monkeypatch):
        monkeypatch.setenv("STATE_MIRROR_WAL_THRESHOLD_BYTES", "not-a-number")
        assert _env_threshold() == DEFAULT_WAL_THRESHOLD_BYTES

    def test_per_entry_override_wins(self, fake_redis, tmp_path, monkeypatch):
        monkeypatch.setenv("STATE_MIRROR_WAL_THRESHOLD_BYTES", "999999")
        h = _handler(tmp_path / "gv.db", fake_redis, wal_threshold_bytes=4096)
        assert h._threshold == 4096


class TestWalEnable:
    def test_enable_wal(self, tmp_path):
        db = str(tmp_path / "gv.db")
        _make_db(db, ["a"])
        assert _journal_mode(db) == "delete"
        assert SqliteHandler.enable_wal(db) is True
        assert _journal_mode(db) == "wal"

    def test_integrity_check_ok(self, tmp_path):
        db = str(tmp_path / "gv.db")
        _make_db(db, ["a", "b"])
        SqliteHandler.integrity_check(db)  # no raise

    def test_integrity_check_raises_on_corruption(self, tmp_path):
        db = str(tmp_path / "gv.db")
        _make_db(db, ["a", "b", "c"])
        with open(db, "r+b") as f:
            f.seek(4096)  # clobber page 2
            f.write(b"\xde\xad\xbe\xef" * 512)
        with pytest.raises(sqlite3.Error):
            SqliteHandler.integrity_check(db)


class TestSnapshotMode:
    def test_mirror_skips_missing_and_empty(self, fake_redis, tmp_path):
        h = _handler(tmp_path / "absent.db", fake_redis)
        assert h.mirror() is False
        empty = tmp_path / "empty.db"
        empty.write_bytes(b"")
        assert _handler(empty, fake_redis).mirror() is False

    def test_snapshot_roundtrip_restores_wal_mode(self, fake_redis, tmp_path):
        db = tmp_path / "gv.db"
        _make_db(str(db), ["a", "b", "c"])
        h = _handler(db, fake_redis)  # default 256MiB threshold -> snapshot mode
        assert h.mirror() is True
        assert h.mirror() is False  # unchanged -> no-op
        assert fake_redis.get("ufm:sqlite:gv.db") is not None
        assert fake_redis.get("ufm:sqlite:gv.db:epoch") is None  # snapshot, no WAL keys

        dest = tmp_path / "restored" / "gv.db"
        rh = _handler(dest, fake_redis)
        assert rh.restore() is True
        assert _row_count(str(dest)) == 3
        assert _journal_mode(str(dest)) == "wal"  # restore-init forces WAL

    def test_restore_missing_returns_false(self, fake_redis, tmp_path):
        assert _handler(tmp_path / "x.db", fake_redis).restore() is False

    def test_signature_changes_on_write(self, fake_redis, tmp_path):
        db = str(tmp_path / "gv.db")
        _make_db(db, ["a"])
        h = _handler(db, fake_redis)
        sig1 = h.signature()
        conn = sqlite3.connect(db)
        conn.execute("INSERT INTO t (v) VALUES ('b')")
        conn.commit()
        conn.close()
        assert h.signature() != sig1


class TestWalShipping:
    """Force WAL-shipping with a tiny threshold relative to the DB size."""

    @staticmethod
    def _big_rows(n):
        return ["x" * 1000 for _ in range(n)]

    def test_rotation_roundtrip(self, fake_redis, tmp_path):
        db = tmp_path / "gv.db"
        _make_db(str(db), self._big_rows(200))
        threshold = 64 * 1024
        assert os.path.getsize(str(db)) >= threshold
        h = _handler(db, fake_redis, wal_threshold_bytes=threshold)

        assert h.mirror() is True  # epoch 0 -> rotate
        assert fake_redis.get("ufm:sqlite:gv.db:epoch") == b"1"
        assert fake_redis.get("ufm:sqlite:gv.db") is not None

        dest = tmp_path / "restored" / "gv.db"
        rh = _handler(dest, fake_redis, wal_threshold_bytes=threshold)
        assert rh.restore() is True
        assert _row_count(str(dest)) == 200
        assert _journal_mode(str(dest)) == "wal"

    def test_incremental_segment_roundtrip(self, fake_redis, tmp_path):
        db = tmp_path / "gv.db"
        _make_db(str(db), self._big_rows(200))
        threshold = 64 * 1024
        h = _handler(db, fake_redis, wal_threshold_bytes=threshold)

        assert h.mirror() is True  # rotate -> epoch 1, base shipped

        # Keep a long-lived connection (no close-checkpoint) and disable
        # auto-checkpoint so the WAL accumulates and is shipped incrementally.
        w = sqlite3.connect(str(db))
        try:
            w.execute("PRAGMA journal_mode=WAL;")
            w.execute("PRAGMA wal_autocheckpoint=0;")
            w.executemany("INSERT INTO t (v) VALUES (?)", [("y" * 1000,) for _ in range(5)])
            w.commit()

            assert h.mirror() is True  # incremental WAL segment
            assert fake_redis.get("ufm:sqlite:gv.db:wal:1") is not None
        finally:
            w.close()

        dest = tmp_path / "restored" / "gv.db"
        rh = _handler(dest, fake_redis, wal_threshold_bytes=threshold)
        assert rh.restore() is True
        assert _row_count(str(dest)) == 205  # base 200 + 5 from the WAL segment

    def test_checkpoint_advance_triggers_reship(self, fake_redis, tmp_path):
        """If the DB is checkpointed out-of-band (counter advances), the handler
        re-ships a fresh base instead of an incremental WAL that lost the pages."""
        db = tmp_path / "gv.db"
        _make_db(str(db), self._big_rows(200))
        threshold = 64 * 1024
        h = _handler(db, fake_redis, wal_threshold_bytes=threshold)
        assert h.mirror() is True  # epoch 1

        # A short-lived connection that closes -> auto-checkpoint folds into the
        # main file and bumps the change counter.
        conn = sqlite3.connect(str(db))
        conn.executemany("INSERT INTO t (v) VALUES (?)", [("z" * 1000,) for _ in range(5)])
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        conn.close()

        assert h.mirror() is True  # counter advanced -> rotate to epoch 2
        assert fake_redis.get("ufm:sqlite:gv.db:epoch") == b"2"

        dest = tmp_path / "restored" / "gv.db"
        rh = _handler(dest, fake_redis, wal_threshold_bytes=threshold)
        assert rh.restore() is True
        assert _row_count(str(dest)) == 205

    def test_fallback_to_snapshot_clears_wal_keys(self, fake_redis, tmp_path):
        db = tmp_path / "gv.db"
        _make_db(str(db), self._big_rows(200))
        threshold = 64 * 1024
        h = _handler(db, fake_redis, wal_threshold_bytes=threshold)
        assert h.mirror() is True  # WAL-ship -> epoch key set
        assert fake_redis.get("ufm:sqlite:gv.db:epoch") == b"1"

        # Raise the threshold above the DB size -> next mirror uses snapshot mode
        # and must clear the stale WAL keys so restore won't apply an old segment.
        # (The base is byte-identical, so the snapshot itself may be a no-op; the
        # point is that the WAL keys are gone.)
        h._threshold = 10 * 1024 * 1024
        h.mirror()
        assert fake_redis.get("ufm:sqlite:gv.db:epoch") is None
        assert fake_redis.get("ufm:sqlite:gv.db:wal:1") is None

        dest = tmp_path / "restored" / "gv.db"
        rh = _handler(dest, fake_redis)
        assert rh.restore() is True
        assert _row_count(str(dest)) == 200


class TestRestoreFailClosed:
    def test_restore_raises_on_corrupt_base(self, fake_redis, tmp_path):
        # Store a base whose bytes are not a valid DB; restore must fail closed.
        key = "ufm:sqlite:gv.db"
        body = b"this is not a sqlite database" * 10
        meta = wire.build_meta(
            body, handler="sqlite", ufm_version=UFM_VERSION, written_by=WRITTEN_BY
        )
        wire.write_pair(fake_redis, key, body, meta)
        rh = _handler(tmp_path / "gv.db", fake_redis)
        with pytest.raises(sqlite3.Error):
            rh.restore()
