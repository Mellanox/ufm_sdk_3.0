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

"""Unit tests for the mirror loop's bounded queues and delete reconcile (D2)."""

import fnmatch

from state_mirror.classifier import Classifier
from state_mirror.mirror import Mirror
from state_mirror.store import RedisStore

UFM_VERSION = "7.0.1"
WRITTEN_BY = "state-mirror:test"


def _mirror(classifier, client, **kwargs):
    return Mirror(classifier, RedisStore(client), UFM_VERSION, WRITTEN_BY, **kwargs)


def _dir_classifier(root):
    return Classifier.from_dict(
        {
            "entries": [
                {
                    "path": str(root),
                    "handler": "directory",
                    "redis_key_prefix": "ufm:cfg:sites:",
                    "recursive": True,
                }
            ]
        }
    )


def _blob_classifier(path):
    return Classifier.from_dict(
        {"entries": [{"path": str(path), "handler": "blob", "redis_key": "ufm:state:o"}]}
    )


class _FlakyPipe:
    """Pipeline that raises on execute() when a delete op is present and the
    backing client is in ``fail_delete`` mode (simulates a Redis outage)."""

    def __init__(self, client):
        self._client = client
        self._ops = []

    def set(self, key, value):
        self._ops.append(("set", key, value))

    def delete(self, key):
        self._ops.append(("del", key))

    def execute(self):
        if self._client.fail_delete and any(op[0] == "del" for op in self._ops):
            raise RuntimeError("simulated redis delete failure")
        for op in self._ops:
            if op[0] == "set":
                self._client.store[op[1]] = op[2]
            else:
                self._client.store.pop(op[1], None)


class FlakyRedis:
    """FakeRedis whose deletes can be toggled to fail, for outage simulation."""

    def __init__(self):
        self.store = {}
        self.fail_delete = False

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value

    def delete(self, key):
        self.store.pop(key, None)

    def pipeline(self, transaction=True):
        return _FlakyPipe(self)

    def keys(self, pattern):
        return [k for k in self.store if fnmatch.fnmatch(k, pattern)]

    def scan_iter(self, match=None, count=None):
        pattern = match if match is not None else "*"
        return iter([k for k in list(self.store) if fnmatch.fnmatch(k, pattern)])


class TestQueueBounds:
    def test_dirty_queue_is_bounded_by_entries(self, fake_redis, tmp_path):
        m = _mirror(_blob_classifier(tmp_path / "o.conf"), fake_redis)
        entry = m._handlers[0].entry
        for _ in range(1000):
            m._mark_dirty(entry)
        # A set keyed by entry path collapses repeated marks to one.
        assert len(m._dirty) == 1

    def test_delete_queue_drops_oldest_when_full(self, fake_redis, tmp_path):
        root = tmp_path / "sites"
        root.mkdir()
        m = _mirror(_dir_classifier(root), fake_redis, max_queue=3)
        entry = m._handlers[0].entry
        for i in range(10):
            m._mark_delete(entry, str(root / f"f{i}"))
        assert len(m._pending_deletes) == 3
        assert m.state.dropped_events_total == 7
        # The newest deletes are the ones retained (oldest dropped, O(1)).
        keys = list(m._pending_deletes)
        assert keys[-1] == "ufm:cfg:sites:f9"
        assert "ufm:cfg:sites:f0" not in m._pending_deletes


class TestDeleteReconcile:
    def test_full_scan_flushes_observed_directory_delete(self, fake_redis, tmp_path):
        root = tmp_path / "sites"
        root.mkdir()
        (root / "a").write_bytes(b"A")
        (root / "b").write_bytes(b"B")
        m = _mirror(_dir_classifier(root), fake_redis)
        m.full_scan()
        assert fake_redis.get("ufm:cfg:sites:a") == b"A"
        assert fake_redis.get("ufm:cfg:sites:b") == b"B"

        # Observed delete of b (unlink + mark); a later scan flushes it.
        (root / "b").unlink()
        m._mark_delete(m._handlers[0].entry, str(root / "b"))
        m.full_scan()
        assert fake_redis.get("ufm:cfg:sites:b") is None
        assert fake_redis.get("ufm:cfg:sites:b:meta") is None
        assert fake_redis.get("ufm:cfg:sites:a") == b"A"
        assert not m._pending_deletes

    def test_full_scan_flushes_observed_blob_delete(self, fake_redis, tmp_path):
        f = tmp_path / "o.conf"
        f.write_bytes(b"X")
        m = _mirror(_blob_classifier(f), fake_redis)
        m.full_scan()
        assert fake_redis.get("ufm:state:o") == b"X"

        f.unlink()
        m._mark_delete(m._handlers[0].entry, str(f))
        m.full_scan()
        assert fake_redis.get("ufm:state:o") is None
        assert not m._pending_deletes

    def test_pending_delete_retried_until_backend_recovers(self, tmp_path):
        f = tmp_path / "o.conf"
        f.write_bytes(b"X")
        client = FlakyRedis()
        m = _mirror(_blob_classifier(f), client)
        m.full_scan()
        assert client.get("ufm:state:o") == b"X"

        # Observed delete while the backend rejects deletes -> stays pending, kept.
        f.unlink()
        client.fail_delete = True
        m._mark_delete(m._handlers[0].entry, str(f))
        m.full_scan()
        assert client.get("ufm:state:o") == b"X"
        assert "ufm:state:o" in m._pending_deletes

        # Backend recovers -> next scan flushes and clears pending.
        client.fail_delete = False
        m.full_scan()
        assert client.get("ufm:state:o") is None
        assert not m._pending_deletes


class TestUnexpectedDelete:
    def test_full_scan_counts_drift_and_keeps_key(self, fake_redis, tmp_path):
        f = tmp_path / "o.conf"
        f.write_bytes(b"X")
        m = _mirror(_blob_classifier(f), fake_redis)
        m.full_scan()
        assert fake_redis.get("ufm:state:o") == b"X"

        # File vanishes WITHOUT an observed delete -> drift.
        f.unlink()
        m.full_scan()
        # Backend key is kept (it wins on ambiguity, HLD 5.3.7)...
        assert fake_redis.get("ufm:state:o") == b"X"
        # ...and the drift is surfaced exactly once.
        assert m.state.unexpected_deletes_total == 1

        # Persistent drift is not double-counted on the next scan.
        m.full_scan()
        assert m.state.unexpected_deletes_total == 1

    def test_observed_delete_not_counted_as_drift(self, fake_redis, tmp_path):
        f = tmp_path / "o.conf"
        f.write_bytes(b"X")
        m = _mirror(_blob_classifier(f), fake_redis)
        m.full_scan()

        # An *observed* delete is propagated and excluded from drift accounting.
        f.unlink()
        m._mark_delete(m._handlers[0].entry, str(f))
        m.full_scan()
        assert fake_redis.get("ufm:state:o") is None
        assert m.state.unexpected_deletes_total == 0


class TestDrainFailureKeepsPending:
    def test_failed_event_delete_stays_pending(self, tmp_path):
        f = tmp_path / "o.conf"
        f.write_bytes(b"X")
        client = FlakyRedis()
        m = _mirror(_blob_classifier(f), client)
        m.full_scan()

        f.unlink()
        client.fail_delete = True
        m._mark_delete(m._handlers[0].entry, str(f))
        m.drain_once(now=0.0, rate_limited=False)
        # Delete failed during the "outage" -> not lost, retried next cycle.
        assert "ufm:state:o" in m._pending_deletes
        assert client.get("ufm:state:o") == b"X"

        client.fail_delete = False
        m.full_scan()
        assert client.get("ufm:state:o") is None
