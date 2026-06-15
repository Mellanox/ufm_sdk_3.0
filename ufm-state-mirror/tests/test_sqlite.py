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

"""Unit tests for the Phase 5 SQLite handler: snapshot-only online-backup
mirroring, change detection, and integrity-checked, fail-closed restore."""

import sqlite3

import pytest

from state_mirror import wire
from state_mirror.classifier import Entry
from state_mirror.handlers.sqlite import SqliteHandler
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


class TestIntegrity:
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


class TestSnapshot:
    def test_mirror_skips_missing_and_empty(self, fake_redis, tmp_path):
        h = _handler(tmp_path / "absent.db", fake_redis)
        assert h.mirror() is False
        empty = tmp_path / "empty.db"
        empty.write_bytes(b"")
        assert _handler(empty, fake_redis).mirror() is False

    def test_snapshot_roundtrip(self, fake_redis, tmp_path):
        db = tmp_path / "gv.db"
        _make_db(str(db), ["a", "b", "c"])
        h = _handler(db, fake_redis)
        assert h.mirror() is True
        assert h.mirror() is False  # unchanged -> no-op
        assert fake_redis.get("ufm:sqlite:gv.db") is not None
        # Snapshot-only: no WAL/epoch keys are ever written.
        assert fake_redis.get("ufm:sqlite:gv.db:epoch") is None
        assert fake_redis.get("ufm:sqlite:gv.db:wal:1") is None

        dest = tmp_path / "restored" / "gv.db"
        rh = _handler(dest, fake_redis)
        assert rh.restore() is True
        assert _row_count(str(dest)) == 3

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

    def test_mirror_reships_after_change(self, fake_redis, tmp_path):
        db = tmp_path / "gv.db"
        _make_db(str(db), ["a"])
        h = _handler(db, fake_redis)
        assert h.mirror() is True
        conn = sqlite3.connect(str(db))
        conn.execute("INSERT INTO t (v) VALUES ('b')")
        conn.commit()
        conn.close()
        assert h.mirror() is True  # content changed -> re-shipped

        dest = tmp_path / "restored" / "gv.db"
        rh = _handler(dest, fake_redis)
        assert rh.restore() is True
        assert _row_count(str(dest)) == 2


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
