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

"""Unit tests for the StateMirror handlers (blob, directory, sqlite)."""

import os
import sqlite3

import pytest

from state_mirror import wire
from state_mirror.classifier import Entry
from state_mirror.handlers import base, make_handler
from state_mirror.handlers.base import BaseHandler
from state_mirror.handlers.blob import BlobHandler
from state_mirror.handlers.directory import DirectoryHandler
from state_mirror.handlers.sqlite import SqliteHandler
from state_mirror.store import RedisStore

UFM_VERSION = "7.0.1"
WRITTEN_BY = "state-mirror:test"


def _handler(entry, client):
    return make_handler(entry, RedisStore(client), UFM_VERSION, WRITTEN_BY)


class TestBlobHandler:
    def test_mirror_then_restore_roundtrip(self, fake_redis, tmp_path):
        src = tmp_path / "a.json"
        src.write_bytes(b'{"v": 1}')
        entry = Entry.from_dict({"path": str(src), "handler": "blob", "redis_key": "ufm:state:a"})
        handler = _handler(entry, fake_redis)
        assert isinstance(handler, BlobHandler)

        assert handler.mirror() is True
        # unchanged -> idempotent no-op
        assert handler.mirror() is False
        # change -> ships again
        src.write_bytes(b'{"v": 2}')
        assert handler.mirror() is True

        # restore into a fresh location
        dest = tmp_path / "restored" / "a.json"
        restore_entry = Entry.from_dict(
            {"path": str(dest), "handler": "blob", "redis_key": "ufm:state:a"}
        )
        assert _handler(restore_entry, fake_redis).restore() is True
        assert dest.read_bytes() == b'{"v": 2}'

    def test_restore_missing_returns_false(self, fake_redis, tmp_path):
        entry = Entry.from_dict(
            {
                "path": str(tmp_path / "x"),
                "handler": "blob",
                "redis_key": "ufm:state:none",
            }
        )
        assert _handler(entry, fake_redis).restore() is False

    def test_bootstrap_empty(self, fake_redis, tmp_path):
        dest = tmp_path / "empty.conf"
        entry = Entry.from_dict(
            {
                "path": str(dest),
                "handler": "blob",
                "redis_key": "ufm:state:empty",
                "baseline": "empty",
            }
        )
        _handler(entry, fake_redis).bootstrap()
        assert dest.read_bytes() == b""
        # bootstrap also pushed to redis, so a fresh restore now succeeds
        assert _handler(entry, fake_redis).restore() is True

    def test_on_delete(self, fake_redis, tmp_path):
        src = tmp_path / "a.json"
        src.write_bytes(b"x")
        entry = Entry.from_dict({"path": str(src), "handler": "blob", "redis_key": "ufm:state:a"})
        h = _handler(entry, fake_redis)
        h.mirror()
        h.on_delete()
        assert fake_redis.get("ufm:state:a") is None
        assert fake_redis.get("ufm:state:a:meta") is None


class TestDirectoryHandler:
    def test_directory_roundtrip(self, fake_redis, tmp_path):
        root = tmp_path / "plugins"
        (root / "sub").mkdir(parents=True)
        (root / "a.conf").write_bytes(b"AAA")
        (root / "sub" / "b.conf").write_bytes(b"BBB")
        entry = Entry.from_dict(
            {
                "path": str(root),
                "handler": "directory",
                "redis_key_prefix": "ufm:cfg:plugins:",
                "recursive": True,
            }
        )
        handler = _handler(entry, fake_redis)
        assert isinstance(handler, DirectoryHandler)
        assert handler.mirror() is True
        assert fake_redis.get("ufm:cfg:plugins:a.conf") == b"AAA"
        assert fake_redis.get("ufm:cfg:plugins:sub/b.conf") == b"BBB"

        dest = tmp_path / "restored"
        restore_entry = Entry.from_dict(
            {
                "path": str(dest),
                "handler": "directory",
                "redis_key_prefix": "ufm:cfg:plugins:",
                "recursive": True,
            }
        )
        assert _handler(restore_entry, fake_redis).restore() is True
        assert (dest / "a.conf").read_bytes() == b"AAA"
        assert (dest / "sub" / "b.conf").read_bytes() == b"BBB"

    def test_child_delete(self, fake_redis, tmp_path):
        root = tmp_path / "plugins"
        root.mkdir()
        (root / "a.conf").write_bytes(b"AAA")
        entry = Entry.from_dict(
            {
                "path": str(root),
                "handler": "directory",
                "redis_key_prefix": "ufm:cfg:plugins:",
            }
        )
        handler = _handler(entry, fake_redis)
        handler.mirror()
        handler.on_delete_child("a.conf")
        assert fake_redis.get("ufm:cfg:plugins:a.conf") is None

    def test_mirror_propagates_backend_error(self, fake_redis, tmp_path, monkeypatch):
        # A backend failure on a child must NOT be swallowed: it propagates so
        # the caller records the outage instead of seeing a healthy run (FIX-2).
        root = tmp_path / "plugins"
        root.mkdir()
        (root / "a.conf").write_bytes(b"AAA")
        entry = Entry.from_dict(
            {"path": str(root), "handler": "directory", "redis_key_prefix": "ufm:cfg:plugins:"}
        )
        handler = _handler(entry, fake_redis)

        def boom(*_a, **_k):
            raise wire.WireError("backend down", reason="conn")

        monkeypatch.setattr(handler.store, "get_meta", boom)
        with pytest.raises(wire.WireError):
            handler.mirror()

    def test_mirror_skips_unreadable_child(self, fake_redis, tmp_path, monkeypatch):
        # A local read error for one child is skipped (not fatal) so the rest of
        # the tree still mirrors (FIX-2).
        root = tmp_path / "plugins"
        root.mkdir()
        (root / "a.conf").write_bytes(b"AAA")
        (root / "b.conf").write_bytes(b"BBB")
        entry = Entry.from_dict(
            {"path": str(root), "handler": "directory", "redis_key_prefix": "ufm:cfg:plugins:"}
        )
        handler = _handler(entry, fake_redis)
        real_read = base.BaseHandler._read_file

        def selective(path):
            if path.endswith("a.conf"):
                raise OSError("unreadable")
            return real_read(path)

        monkeypatch.setattr(base.BaseHandler, "_read_file", staticmethod(selective))
        assert handler.mirror() is True  # b.conf still shipped despite a.conf failing
        assert fake_redis.get("ufm:cfg:plugins:a.conf") is None
        assert fake_redis.get("ufm:cfg:plugins:b.conf") == b"BBB"


class TestSqliteHandler:
    @staticmethod
    def _make_db(path, rows):
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
        conn.executemany("INSERT INTO t (v) VALUES (?)", [(r,) for r in rows])
        conn.commit()
        conn.close()

    def test_change_counter_increases(self, tmp_path):
        db = str(tmp_path / "gv.db")
        self._make_db(db, ["a"])
        c1 = SqliteHandler.read_change_counter(db)
        assert c1 > 0
        conn = sqlite3.connect(db)
        conn.execute("INSERT INTO t (v) VALUES ('b')")
        conn.commit()
        conn.close()
        assert SqliteHandler.read_change_counter(db) > c1

    def test_change_counter_missing_file(self, tmp_path):
        assert SqliteHandler.read_change_counter(str(tmp_path / "nope.db")) == 0

    def test_snapshot_mirror_and_restore(self, fake_redis, tmp_path):
        db = str(tmp_path / "gv.db")
        self._make_db(db, ["a", "b", "c"])
        entry = Entry.from_dict(
            {
                "path": db,
                "handler": "sqlite",
                "redis_key": "ufm:sqlite:gv.db",
                "snapshot_method": "online_backup",
            }
        )
        handler = _handler(entry, fake_redis)
        assert isinstance(handler, SqliteHandler)
        assert handler.mirror() is True

        # restore to a new path and confirm it opens with the same rows
        dest = str(tmp_path / "restored" / "gv.db")
        restore_entry = Entry.from_dict(
            {"path": dest, "handler": "sqlite", "redis_key": "ufm:sqlite:gv.db"}
        )
        assert _handler(restore_entry, fake_redis).restore() is True
        assert os.path.exists(dest)
        conn = sqlite3.connect(dest)
        count = conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
        conn.close()
        assert count == 3


class TestRestorePreservesIdentity:
    """The root-run restore must not strip a file's original owner/mode when it
    overwrites it via tmp+rename (e.g. conf/* is ufmapp 731:731)."""

    def test_reapplies_owner_and_mode_on_overwrite(self, tmp_path, monkeypatch):
        dest = tmp_path / "conf" / "unhealthy_ports_counters.csv"
        dest.parent.mkdir(parents=True)
        dest.write_bytes(b"old")

        real_stat = os.stat
        # Pretend the pre-existing file is owned by ufmapp 731:731, mode 0640.
        seeded = os.stat_result((0o100640, 0, 0, 1, 731, 731, 3, 0, 0, 0))

        def fake_stat(p, *a, **k):
            if os.fspath(p) == str(dest):
                return seeded
            return real_stat(p, *a, **k)

        chown_calls: list = []
        chmod_calls: list = []
        monkeypatch.setattr(base.os, "stat", fake_stat)
        monkeypatch.setattr(base.os, "geteuid", lambda: 0)  # pretend root
        monkeypatch.setattr(
            base.os, "chown", lambda p, u, g: chown_calls.append((os.fspath(p), u, g))
        )
        monkeypatch.setattr(base.os, "chmod", lambda p, m: chmod_calls.append((os.fspath(p), m)))

        BaseHandler._write_file(str(dest), b"new content")

        assert dest.read_bytes() == b"new content"
        assert chown_calls == [(str(dest), 731, 731)]
        assert chmod_calls == [(str(dest), 0o640)]

    def test_skips_chown_when_not_root(self, tmp_path, monkeypatch):
        dest = tmp_path / "f.conf"
        dest.write_bytes(b"old")
        chown_calls: list = []
        monkeypatch.setattr(base.os, "geteuid", lambda: 1000)
        monkeypatch.setattr(base.os, "chown", lambda p, u, g: chown_calls.append(p))

        BaseHandler._write_file(str(dest), b"new")

        assert dest.read_bytes() == b"new"
        assert chown_calls == []  # non-root: best-effort skip, never raises

    def test_new_destination_is_left_to_default_ownership(self, tmp_path, monkeypatch):
        dest = tmp_path / "brand_new.conf"  # does not pre-exist
        chown_calls: list = []
        monkeypatch.setattr(base.os, "geteuid", lambda: 0)
        monkeypatch.setattr(base.os, "chown", lambda p, u, g: chown_calls.append(p))

        BaseHandler._write_file(str(dest), b"hello")

        assert dest.read_bytes() == b"hello"
        assert chown_calls == []  # first-install file -> consumer owns it
