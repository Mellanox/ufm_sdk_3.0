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

import os
import sqlite3

import pytest

from state_mirror import wire
from state_mirror.classifier import Entry
from state_mirror.handlers.base import MirrorOutcome
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
        assert h.mirror().outcome is MirrorOutcome.LOCAL_NOOP
        empty = tmp_path / "empty.db"
        empty.write_bytes(b"")
        assert _handler(empty, fake_redis).mirror().outcome is MirrorOutcome.LOCAL_NOOP

    def test_snapshot_roundtrip(self, fake_redis, tmp_path):
        db = tmp_path / "gv.db"
        _make_db(str(db), ["a", "b", "c"])
        h = _handler(db, fake_redis)
        assert h.mirror().outcome is MirrorOutcome.WROTE
        assert h.mirror().outcome is MirrorOutcome.LOCAL_NOOP
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

    def test_signature_propagates_local_wal_inspection_error(
        self, fake_redis, tmp_path, monkeypatch
    ):
        db = tmp_path / "gv.db"
        _make_db(str(db), ["a"])
        h = _handler(db, fake_redis)
        real_stat = os.stat

        def deny_wal_stat(path):
            if str(path).endswith("-wal"):
                raise PermissionError("cannot inspect WAL")
            return real_stat(path)

        with monkeypatch.context() as patch:
            patch.setattr("state_mirror.handlers.sqlite.os.stat", deny_wal_stat)
            with pytest.raises(PermissionError):
                h.signature()

    def test_mirror_reships_after_change(self, fake_redis, tmp_path):
        db = tmp_path / "gv.db"
        _make_db(str(db), ["a"])
        h = _handler(db, fake_redis)
        assert h.mirror().outcome is MirrorOutcome.WROTE
        conn = sqlite3.connect(str(db))
        conn.execute("INSERT INTO t (v) VALUES ('b')")
        conn.commit()
        conn.close()
        assert h.mirror().outcome is MirrorOutcome.WROTE

        dest = tmp_path / "restored" / "gv.db"
        rh = _handler(dest, fake_redis)
        assert rh.restore() is True
        assert _row_count(str(dest)) == 2

    def test_signature_detects_same_counter_main_file_replacement(self, fake_redis, tmp_path):
        db = tmp_path / "gv.db"
        _make_db(str(db), ["a"])
        h = _handler(db, fake_redis)
        original = h.signature()
        stat = db.stat()
        replacement = tmp_path / "replacement.db"
        _make_db(str(replacement), ["different" * 100 for _ in range(1000)])
        # Force the header counter and mtime back to the original values; size
        # remains part of the signature and must still detect replacement.
        data = bytearray(replacement.read_bytes())
        data[24:28] = db.read_bytes()[24:28]
        db.write_bytes(data)
        db.touch()
        os.utime(db, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        assert h.signature() != original

    def test_signature_detects_same_size_mtime_counter_replacement(self, fake_redis, tmp_path):
        db = tmp_path / "gv.db"
        replacement = tmp_path / "replacement.db"
        _make_db(str(db), ["a"])
        _make_db(str(replacement), ["b"])
        h = _handler(db, fake_redis)
        original = h.signature()
        original_stat = db.stat()
        data = bytearray(replacement.read_bytes())
        data[24:28] = db.read_bytes()[24:28]
        replacement.write_bytes(data)
        assert replacement.stat().st_size == original_stat.st_size
        os.replace(replacement, db)
        os.utime(db, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
        assert h.signature() != original


def _snapshot_rows(h, tmp_path):
    out = tmp_path / "snapshot.db"
    out.write_bytes(h.snapshot_bytes())
    conn = sqlite3.connect(out)
    try:
        return [r[0] for r in conn.execute("SELECT v FROM t ORDER BY id")]
    finally:
        conn.close()


def _wal_db(path, rows):
    """WAL database whose writer stays open, so its commits remain in -wal."""
    conn = sqlite3.connect(path)
    assert conn.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
    conn.execute("PRAGMA wal_autocheckpoint=0")
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
    conn.executemany("INSERT INTO t (v) VALUES (?)", [(r,) for r in rows])
    conn.commit()
    return conn


@pytest.fixture
def _cannot_create_wal_files(monkeypatch):
    """Model the sidecar's read-only mount: ``mode=ro`` on a WAL DB without -wal/-shm fails."""
    real = sqlite3.connect

    def connect(target, *args, **kwargs):
        if isinstance(target, str) and "mode=ro" in target:
            db = target[len("file:") :].split("?")[0]
            if not (os.path.exists(db + "-wal") or os.path.exists(db + "-shm")):
                raise sqlite3.OperationalError("unable to open database file")
        return real(target, *args, **kwargs)

    monkeypatch.setattr("state_mirror.handlers.sqlite.sqlite3.connect", connect)


class TestWalSnapshot:
    def test_uncheckpointed_commit_is_in_snapshot(self, fake_redis, tmp_path):
        db = tmp_path / "gv.db"
        writer = _wal_db(str(db), ["checkpointed"])
        writer.execute("PRAGMA wal_checkpoint(FULL)")
        writer.execute("INSERT INTO t (v) VALUES ('uncheckpointed')")
        writer.commit()
        try:
            assert os.path.getsize(str(db) + "-wal") > 0
            h = _handler(db, fake_redis)
            assert _snapshot_rows(h, tmp_path) == ["checkpointed", "uncheckpointed"]
            assert sqlite3.connect(db).execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        finally:
            writer.close()

    @pytest.mark.usefixtures("_cannot_create_wal_files")
    def test_wal_db_without_wal_files_snapshots_when_they_cannot_be_created(
        self, fake_redis, tmp_path
    ):
        db = tmp_path / "gv.db"
        _wal_db(str(db), ["a", "b"]).close()
        for suffix in ("-wal", "-shm"):
            if os.path.exists(str(db) + suffix):
                os.remove(str(db) + suffix)
        h = _handler(db, fake_redis)
        assert _snapshot_rows(h, tmp_path) == ["a", "b"]
        assert h.last_snapshot_seconds is not None

    def test_never_reads_around_an_existing_wal(self, fake_redis, tmp_path, monkeypatch):
        """immutable=1 would silently drop the uncheckpointed row, so the error must surface."""
        db = tmp_path / "gv.db"
        writer = _wal_db(str(db), ["only-in-wal"])
        real = sqlite3.connect

        def connect(target, *args, **kwargs):
            if isinstance(target, str) and "mode=ro" in target:
                raise sqlite3.OperationalError("unable to open database file")
            return real(target, *args, **kwargs)

        monkeypatch.setattr("state_mirror.handlers.sqlite.sqlite3.connect", connect)
        try:
            with pytest.raises(sqlite3.OperationalError):
                _handler(db, fake_redis).snapshot_bytes()
        finally:
            writer.close()

    @pytest.mark.usefixtures("_cannot_create_wal_files")
    def test_rejects_snapshot_when_a_writer_appears_during_the_fallback(
        self, fake_redis, tmp_path, monkeypatch
    ):
        db = tmp_path / "gv.db"
        _wal_db(str(db), ["a"]).close()
        for suffix in ("-wal", "-shm"):
            if os.path.exists(str(db) + suffix):
                os.remove(str(db) + suffix)
        h = _handler(db, fake_redis)
        original = h._backup_to

        def backup_then_write(uri, tmp):
            original(uri, tmp)
            open(str(db) + "-wal", "wb").close()

        monkeypatch.setattr(h, "_backup_to", backup_then_write)
        with pytest.raises(sqlite3.OperationalError, match="changed while"):
            h.snapshot_bytes()


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

    def test_restore_does_not_clobber_live_db_on_corrupt_snapshot(self, fake_redis, tmp_path):
        # A pre-existing, valid live DB must survive a corrupt stored snapshot:
        # restore verifies on a temp copy first and fails closed WITHOUT touching
        # the live file (FIX-1).
        live = tmp_path / "gv.db"
        _make_db(str(live), ["keep1", "keep2"])
        key = "ufm:sqlite:gv.db"
        body = b"this is not a sqlite database" * 10
        meta = wire.build_meta(
            body, handler="sqlite", ufm_version=UFM_VERSION, written_by=WRITTEN_BY
        )
        wire.write_pair(fake_redis, key, body, meta)
        rh = _handler(live, fake_redis)
        with pytest.raises(sqlite3.Error):
            rh.restore()
        # The live DB is intact -- its rows were never overwritten.
        assert _row_count(str(live)) == 2
