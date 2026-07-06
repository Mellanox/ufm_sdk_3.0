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
import sqlite3

from state_mirror import mirror as mirror_mod
from state_mirror import wire
from state_mirror.classifier import Classifier
from state_mirror.handlers.base import MirrorResult
from state_mirror.health import HealthState
from state_mirror.mirror import Mirror
from state_mirror.store import RedisStore
from state_mirror.watcher import ObserverSetup

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
        self.ping_calls = 0

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

    def ping(self):
        self.ping_calls += 1
        return True


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


class _AliveObserver:
    def is_alive(self):
        return True


class _NeverStartedObserver:
    def start(self):
        raise AssertionError("incomplete setup must not start observer")


class _DiesDuringScanObserver:
    def __init__(self):
        self._checks = 0

    def is_alive(self):
        self._checks += 1
        return self._checks == 1

    def stop(self):
        pass

    def join(self, timeout=None):
        pass


class _DeadEmitter:
    def is_alive(self):
        return False


class _ObserverWithDeadEmitter(_AliveObserver):
    emitters = (_DeadEmitter(),)

    def __init__(self):
        self.stopped = False

    def stop(self):
        self.stopped = True

    def join(self, timeout=None):
        pass


class TestReadinessAndHealth:
    def test_partial_watcher_setup_blocks_strict_readiness(self, fake_redis, tmp_path, monkeypatch):
        state = HealthState()
        m = _mirror(_blob_classifier(tmp_path / "missing"), fake_redis, state=state)
        setup = ObserverSetup(
            observer=_NeverStartedObserver(),
            required=2,
            scheduled=1,
            failures=(OSError("inotify exhausted"),),
        )
        monkeypatch.setattr(mirror_mod, "build_observer", lambda *_args: setup)
        assert m.startup_once() is False
        assert state.is_ready() is False
        assert state.watchdog_active is False

    def test_startup_failure_does_not_latch_then_recovery_does(self, fake_redis, tmp_path):
        state = HealthState()
        m = _mirror(_blob_classifier(tmp_path / "missing"), fake_redis, state=state)
        m._observer = _AliveObserver()
        original = m.full_scan
        m.full_scan = lambda: MirrorResult(failures=(RuntimeError("backend down"),))
        assert m.startup_once() is False
        assert state.is_ready() is False
        m.full_scan = original
        assert m.startup_once() is True
        assert state.is_ready() is True

    def test_recovered_watcher_cannot_latch_before_current_scan(self, fake_redis, tmp_path):
        state = HealthState()
        m = _mirror(_blob_classifier(tmp_path / "missing"), fake_redis, state=state)
        m.start_watching = lambda: False
        m.full_scan = lambda: MirrorResult(reads=1)
        assert m.startup_once() is False
        assert state.initial_reconcile_ok is True

        def recover_watcher():
            m._observer = _AliveObserver()
            state.mark_watching(True, all_required_armed=True)
            return True

        m.start_watching = recover_watcher
        m.full_scan = lambda: MirrorResult(failures=(RuntimeError("scan failed"),))
        assert m.startup_once() is False
        assert state.is_ready() is False

    def test_watcher_dying_during_scan_blocks_strict_readiness(self, fake_redis, tmp_path):
        state = HealthState()
        m = _mirror(_blob_classifier(tmp_path / "missing"), fake_redis, state=state)
        m._observer = _DiesDuringScanObserver()
        assert m.startup_once() is False
        assert state.is_ready() is False
        assert state.watchdog_active is False

    def test_dead_required_emitter_blocks_strict_readiness(self, fake_redis, tmp_path):
        state = HealthState()
        m = _mirror(_blob_classifier(tmp_path / "missing"), fake_redis, state=state)
        observer = _ObserverWithDeadEmitter()
        m._observer = observer
        m.start_watching = lambda: False
        assert m.startup_once() is False
        assert state.is_ready() is False
        assert observer.stopped is True

    def test_local_noop_does_not_clear_backend_down(self, fake_redis, tmp_path):
        state = HealthState()
        m = _mirror(_blob_classifier(tmp_path / "missing"), fake_redis, state=state)
        entry = m._handlers[0].entry
        state.record_store_down("conn")
        m._mark_dirty(entry)
        m.drain_once(now=0.0, rate_limited=False)
        assert state.backend_reachable is False

    def test_successful_read_does_not_advance_write_timestamp(self, fake_redis, tmp_path):
        path = tmp_path / "state"
        path.write_bytes(b"v1")
        state = HealthState()
        m = _mirror(_blob_classifier(path), fake_redis, state=state)
        m.full_scan()
        written_at = state.last_store_write
        state.record_store_down("conn")
        m.full_scan()
        assert state.backend_reachable is True
        assert state.last_store_write == written_at

    def test_successful_drift_read_clears_backend_down(self, fake_redis, tmp_path):
        path = tmp_path / "missing"
        body = b"durable"
        wire.write_pair(
            fake_redis,
            "ufm:state:o",
            body,
            wire.build_meta(body, "blob", UFM_VERSION, WRITTEN_BY),
        )
        state = HealthState()
        m = _mirror(_blob_classifier(path), fake_redis, state=state)
        state.record_store_down("conn")
        result = m.full_scan()
        assert result.reads == 1
        assert state.backend_reachable is True
        assert state.last_store_write == 0.0

    def test_partial_failure_advances_write_but_failure_wins_reachability(
        self, fake_redis, tmp_path
    ):
        state = HealthState()
        m = _mirror(_blob_classifier(tmp_path / "state"), fake_redis, state=state)
        failure = wire.WireError("one child failed", reason="conn")
        m._handlers[0].mirror = lambda: MirrorResult(writes=2, failures=(failure,))
        result = m.full_scan()
        assert result.writes == 2
        assert result.failures == (failure,)
        assert state.last_store_write > 0
        assert state.backend_reachable is False
        assert state.backend_errors["conn"] == 1

    def test_runtime_batch_failure_wins_over_later_success(self, fake_redis, tmp_path):
        first = tmp_path / "first"
        second = tmp_path / "second"
        first.write_bytes(b"first")
        second.write_bytes(b"second")
        classifier = Classifier.from_dict(
            {
                "entries": [
                    {"path": str(first), "handler": "blob", "redis_key": "ufm:first"},
                    {"path": str(second), "handler": "blob", "redis_key": "ufm:second"},
                ]
            }
        )
        state = HealthState()
        m = _mirror(classifier, fake_redis, state=state)
        failure = wire.WireError("first failed", reason="conn")
        results = iter((MirrorResult(failures=(failure,)), MirrorResult(writes=1)))
        m._mirror_handler = lambda _handler: next(results)
        m._mark_dirty(m._handlers[0].entry)
        m._mark_dirty(m._handlers[1].entry)
        assert m.drain_once(now=0.0, rate_limited=False) == 1
        assert state.backend_reachable is False

    def test_zero_backend_op_startup_uses_probe(self, tmp_path):
        client = FlakyRedis()
        state = HealthState(allow_poll_only=True)
        m = _mirror(_blob_classifier(tmp_path / "missing"), client, state=state)
        m.start_watching = lambda: False
        # Avoid drift's get_meta so this is a true all-local-noop scan from the
        # startup aggregator's perspective; startup_once must still probe.
        m._scan_unexpected_deletes = lambda: MirrorResult()
        assert m.startup_once() is True
        assert client.ping_calls == 1
        assert state.backend_reachable is True

    def test_failed_zero_op_startup_does_not_probe(self, tmp_path):
        client = FlakyRedis()
        state = HealthState(allow_poll_only=True)
        m = _mirror(_blob_classifier(tmp_path / "missing"), client, state=state)
        m.start_watching = lambda: False
        m.full_scan = lambda: MirrorResult(failures=(RuntimeError("scan failed"),))
        assert m.startup_once() is False
        assert client.ping_calls == 0
        assert state.backend_reachable is False


class TestSqliteDeletePolicy:
    def test_reappearance_during_drift_scan_does_not_leave_stale_onset(self, fake_redis, tmp_path):
        path = tmp_path / "gv.db"
        classifier = Classifier.from_dict(
            {
                "entries": [
                    {
                        "path": str(path),
                        "handler": "sqlite",
                        "redis_key": "ufm:sqlite:gv.db",
                    }
                ]
            }
        )
        m = _mirror(classifier, fake_redis)

        def reappear_while_scanning():
            path.write_bytes(b"reappeared")
            return ["ufm:sqlite:gv.db"]

        m._handlers[0].drift_keys = reappear_while_scanning
        m._scan_unexpected_deletes()
        assert "ufm:sqlite:gv.db" not in m._known_drift
        assert m.state.unexpected_deletes_total == 0

    def test_stale_delete_after_reappearance_is_treated_as_dirty(self, fake_redis, tmp_path):
        path = tmp_path / "gv.db"
        path.write_bytes(b"recreated")
        classifier = Classifier.from_dict(
            {
                "entries": [
                    {
                        "path": str(path),
                        "handler": "sqlite",
                        "redis_key": "ufm:sqlite:gv.db",
                    }
                ]
            }
        )
        m = _mirror(classifier, fake_redis)
        entry = m._handlers[0].entry
        m._mark_delete(entry, str(path))
        assert m.state.unexpected_deletes_total == 0
        assert entry.path in m._dirty

    def test_sqlite_delete_keeps_backend_and_counts_once_per_onset(self, fake_redis, tmp_path):
        path = tmp_path / "gv.db"
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()
        classifier = Classifier.from_dict(
            {
                "entries": [
                    {
                        "path": str(path),
                        "handler": "sqlite",
                        "redis_key": "ufm:sqlite:gv.db",
                    }
                ]
            }
        )
        m = _mirror(classifier, fake_redis)
        m.full_scan()
        body = fake_redis.get("ufm:sqlite:gv.db")
        path.unlink()
        entry = m._handlers[0].entry
        m._mark_delete(entry, str(path))
        m._mark_delete(entry, str(path))
        assert fake_redis.get("ufm:sqlite:gv.db") == body
        assert m.state.unexpected_deletes_total == 1
        assert not m._pending_deletes

        path.write_bytes(body)
        m._mark_dirty(entry)
        path.unlink()
        m._mark_delete(entry, str(path))
        assert m.state.unexpected_deletes_total == 2

    def test_missing_backend_does_not_reset_sqlite_delete_onset(self, fake_redis, tmp_path):
        path = tmp_path / "gv.db"
        classifier = Classifier.from_dict(
            {
                "entries": [
                    {
                        "path": str(path),
                        "handler": "sqlite",
                        "redis_key": "ufm:sqlite:gv.db",
                    }
                ]
            }
        )
        m = _mirror(classifier, fake_redis)
        entry = m._handlers[0].entry
        m._mark_delete(entry, str(path))
        m.full_scan()
        m._mark_delete(entry, str(path))
        assert m.state.unexpected_deletes_total == 1
