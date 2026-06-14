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

"""Unit tests for the watchdog change-detection layer (resolver + dispatch)
and the event-driven drain on the mirror loop.
"""

import os
from types import SimpleNamespace

from state_mirror.classifier import Classifier, Entry
from state_mirror.mirror import Mirror
from state_mirror.store import RedisStore
from state_mirror.watcher import (
    EVENT_CLOSED,
    EVENT_DELETED,
    EVENT_MOVED,
    MirrorEventHandler,
    PathResolver,
)

UFM_VERSION = "7.0.1"
WRITTEN_BY = "state-mirror:test"


def _entries():
    return [
        Entry.from_dict(
            {"path": "/opt/ufm/files/conf/pkey.conf", "handler": "blob", "redis_key": "ufm:pkey"}
        ),
        Entry.from_dict(
            {
                "path": "/opt/ufm/files/conf/plugins",
                "handler": "directory",
                "redis_key_prefix": "ufm:plugins:",
                "recursive": True,
            }
        ),
        Entry.from_dict(
            {
                "path": "/opt/ufm/files/conf/flat",
                "handler": "directory",
                "redis_key_prefix": "ufm:flat:",
            }
        ),
    ]


def _evt(event_type, src_path, dest_path=None, is_directory=False):
    return SimpleNamespace(
        event_type=event_type,
        src_path=src_path,
        dest_path=dest_path,
        is_directory=is_directory,
    )


class TestPathResolver:
    def setup_method(self):
        self.resolver = PathResolver(_entries())

    def test_single_file_exact_match(self):
        e = self.resolver.resolve("/opt/ufm/files/conf/pkey.conf")
        assert e is not None
        assert e.redis_key == "ufm:pkey"

    def test_recursive_directory_child(self):
        e = self.resolver.resolve("/opt/ufm/files/conf/plugins/sub/a.conf")
        assert e is not None
        assert e.redis_key_prefix == "ufm:plugins:"

    def test_nonrecursive_directory_direct_child(self):
        e = self.resolver.resolve("/opt/ufm/files/conf/flat/a.conf")
        assert e is not None
        assert e.redis_key_prefix == "ufm:flat:"

    def test_nonrecursive_directory_nested_child_is_ignored(self):
        assert self.resolver.resolve("/opt/ufm/files/conf/flat/sub/a.conf") is None

    def test_directory_object_itself_is_not_a_child(self):
        assert self.resolver.resolve("/opt/ufm/files/conf/plugins") is None

    def test_unknown_path(self):
        assert self.resolver.resolve("/etc/passwd") is None

    def test_watch_dirs_dedup_and_recursive(self):
        d = dict(self.resolver.watch_dirs())
        assert d["/opt/ufm/files/conf"] is False
        assert "/opt/ufm/files/conf/plugins" in d
        assert "/opt/ufm/files/conf/flat" in d


class TestMirrorEventHandler:
    def setup_method(self):
        self.resolver = PathResolver(_entries())
        self.dirty = []
        self.deletes = []
        self.handler = MirrorEventHandler(
            self.resolver,
            lambda entry: self.dirty.append(entry.path),
            lambda entry, path: self.deletes.append((entry.path, path)),
        )

    def test_closed_marks_dirty(self):
        self.handler.dispatch(_evt(EVENT_CLOSED, "/opt/ufm/files/conf/pkey.conf"))
        assert self.dirty == ["/opt/ufm/files/conf/pkey.conf"]

    def test_moved_uses_dest_path(self):
        self.handler.dispatch(
            _evt(EVENT_MOVED, "/opt/ufm/files/conf/.tmp", "/opt/ufm/files/conf/pkey.conf")
        )
        assert self.dirty == ["/opt/ufm/files/conf/pkey.conf"]

    def test_deleted_marks_delete(self):
        self.handler.dispatch(_evt(EVENT_DELETED, "/opt/ufm/files/conf/plugins/a.conf"))
        assert self.deletes == [
            ("/opt/ufm/files/conf/plugins", "/opt/ufm/files/conf/plugins/a.conf")
        ]

    def test_directory_event_ignored(self):
        self.handler.dispatch(
            _evt(EVENT_CLOSED, "/opt/ufm/files/conf/plugins/sub", is_directory=True)
        )
        assert self.dirty == []

    def test_unknown_path_is_dropped(self):
        self.handler.dispatch(_evt(EVENT_CLOSED, "/etc/passwd"))
        assert self.dirty == []
        assert self.deletes == []

    def test_real_watchdog_event_objects(self):
        import pytest

        pytest.importorskip("watchdog.events")
        from watchdog.events import FileClosedEvent, FileDeletedEvent, FileMovedEvent

        self.handler.dispatch(FileClosedEvent("/opt/ufm/files/conf/pkey.conf"))
        self.handler.dispatch(
            FileMovedEvent("/opt/ufm/files/conf/.t", "/opt/ufm/files/conf/pkey.conf")
        )
        self.handler.dispatch(FileDeletedEvent("/opt/ufm/files/conf/plugins/a.conf"))
        assert self.dirty == [
            "/opt/ufm/files/conf/pkey.conf",
            "/opt/ufm/files/conf/pkey.conf",
        ]
        assert self.deletes == [
            ("/opt/ufm/files/conf/plugins", "/opt/ufm/files/conf/plugins/a.conf")
        ]


class TestDrain:
    def _mirror(self, entries, client):
        return Mirror(Classifier(entries), RedisStore(client), UFM_VERSION, WRITTEN_BY)

    def test_dirty_drain_ships(self, fake_redis, tmp_path):
        p = tmp_path / "pkey.conf"
        p.write_bytes(b"v1")
        entry = Entry.from_dict({"path": str(p), "handler": "blob", "redis_key": "ufm:pkey"})
        m = self._mirror([entry], fake_redis)
        m._mark_dirty(entry)
        assert m.drain_once(now=0.0) == 1
        assert fake_redis.get("ufm:pkey") == b"v1"
        assert m.drain_once(now=10.0) == 0

    def test_rate_limit_defers_then_ships(self, fake_redis, tmp_path):
        p = tmp_path / "pkey.conf"
        p.write_bytes(b"v1")
        entry = Entry.from_dict(
            {"path": str(p), "handler": "blob", "redis_key": "ufm:pkey", "rate_limit_ms": 100}
        )
        m = self._mirror([entry], fake_redis)
        m._mark_dirty(entry)
        assert m.drain_once(now=0.0) == 1
        p.write_bytes(b"v2")
        m._mark_dirty(entry)
        assert m.drain_once(now=0.05) == 0
        assert fake_redis.get("ufm:pkey") == b"v1"
        assert m.drain_once(now=0.2) == 1
        assert fake_redis.get("ufm:pkey") == b"v2"

    def test_delete_drain_single_file(self, fake_redis, tmp_path):
        p = tmp_path / "pkey.conf"
        p.write_bytes(b"v1")
        entry = Entry.from_dict({"path": str(p), "handler": "blob", "redis_key": "ufm:pkey"})
        m = self._mirror([entry], fake_redis)
        m._mark_dirty(entry)
        m.drain_once(now=0.0)
        assert fake_redis.get("ufm:pkey") == b"v1"
        m._mark_delete(entry, str(p))
        m.drain_once(now=1.0)
        assert fake_redis.get("ufm:pkey") is None
        assert fake_redis.get("ufm:pkey:meta") is None

    def test_delete_drain_directory_child(self, fake_redis, tmp_path):
        root = tmp_path / "plugins"
        root.mkdir()
        (root / "a.conf").write_bytes(b"AAA")
        entry = Entry.from_dict(
            {"path": str(root), "handler": "directory", "redis_key_prefix": "ufm:plugins:"}
        )
        m = self._mirror([entry], fake_redis)
        m._mark_dirty(entry)
        m.drain_once(now=0.0)
        assert fake_redis.get("ufm:plugins:a.conf") == b"AAA"
        m._mark_delete(entry, str(root / "a.conf"))
        m.drain_once(now=1.0)
        assert fake_redis.get("ufm:plugins:a.conf") is None

    def test_drain_skips_unknown_path(self, fake_redis):
        m = self._mirror([], fake_redis)
        with m._lock:
            m._dirty.add("/nope")
        assert m.drain_once(now=0.0) == 0
        assert os.path.exists("/nope") is False
