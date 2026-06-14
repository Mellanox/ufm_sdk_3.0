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

"""Unit tests for per-entry backend routing (build_stores + make_handler)."""

from state_mirror.backends import build_stores, selected_backends
from state_mirror.classifier import Backend, Classifier
from state_mirror.handlers import make_handler

UFM_VERSION = "7.0.1"
WRITTEN_BY = "state-mirror:test"


def _classifier(*entries):
    return Classifier.from_dict({"entries": list(entries)})


def _redis_entry(key="ufm:state:a", path="/opt/ufm/files/conf/a.json"):
    return {"path": path, "handler": "blob", "redis_key": key}


def _cm_entry(key="ufm:cfg:plugins", path="/opt/ufm/files/conf/plugins.json"):
    return {"path": path, "handler": "blob", "backend": "configmap", "redis_key": key}


class _Recorder:
    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return object()  # stand-in Store


class TestSelectedBackends:
    def test_default_is_redis_only(self):
        c = _classifier(_redis_entry())
        assert selected_backends(c) == {Backend.REDIS}

    def test_mixed(self):
        c = _classifier(_redis_entry(), _cm_entry())
        assert selected_backends(c) == {Backend.REDIS, Backend.CONFIGMAP}


class TestBuildStores:
    def test_pure_redis_does_not_build_configmap(self):
        redis, cm = _Recorder(), _Recorder()
        stores = build_stores(
            _classifier(_redis_entry()), redis_factory=redis, configmap_factory=cm
        )
        assert set(stores) == {Backend.REDIS}
        assert redis.calls == 1
        assert cm.calls == 0  # never construct the K8s client for a Redis-only classifier

    def test_configmap_only_does_not_build_redis(self):
        redis, cm = _Recorder(), _Recorder()
        stores = build_stores(_classifier(_cm_entry()), redis_factory=redis, configmap_factory=cm)
        assert set(stores) == {Backend.CONFIGMAP}
        assert redis.calls == 0
        assert cm.calls == 1

    def test_mixed_builds_both_once(self):
        redis, cm = _Recorder(), _Recorder()
        stores = build_stores(
            _classifier(_redis_entry(), _cm_entry()),
            redis_factory=redis,
            configmap_factory=cm,
        )
        assert set(stores) == {Backend.REDIS, Backend.CONFIGMAP}
        assert redis.calls == 1
        assert cm.calls == 1


class TestMakeHandlerRouting:
    def test_mapping_routes_per_entry_backend(self):
        redis_store = object()
        cm_store = object()
        stores = {Backend.REDIS: redis_store, Backend.CONFIGMAP: cm_store}

        c = _classifier(_redis_entry(), _cm_entry())
        redis_entry, cm_entry = c.entries

        h_redis = make_handler(redis_entry, stores, UFM_VERSION, WRITTEN_BY)
        h_cm = make_handler(cm_entry, stores, UFM_VERSION, WRITTEN_BY)
        assert h_redis.store is redis_store
        assert h_cm.store is cm_store

    def test_single_store_used_for_all(self):
        only = object()
        c = _classifier(_redis_entry())
        h = make_handler(c.entries[0], only, UFM_VERSION, WRITTEN_BY)
        assert h.store is only
