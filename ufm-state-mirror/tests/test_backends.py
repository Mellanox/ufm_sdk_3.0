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

"""Unit tests for install-wide backend selection (backend_from_env + build_store)."""

import pytest

from state_mirror.backends import (
    BACKEND_ENV,
    DEFAULT_BACKEND,
    Backend,
    backend_from_env,
    build_store,
)
from state_mirror.classifier import Classifier
from state_mirror.handlers import make_handler

UFM_VERSION = "7.0.1"
WRITTEN_BY = "state-mirror:test"


def _classifier(*entries):
    return Classifier.from_dict({"entries": list(entries)})


def _entry(key="ufm:state:a", path="/opt/ufm/files/conf/a.json"):
    return {"path": path, "handler": "blob", "redis_key": key}


class _Recorder:
    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return object()  # stand-in Store


class TestBackendFromEnv:
    def test_default_is_configmap(self, monkeypatch):
        monkeypatch.delenv(BACKEND_ENV, raising=False)
        assert backend_from_env() is Backend.CONFIGMAP
        assert DEFAULT_BACKEND is Backend.CONFIGMAP

    def test_explicit_redis(self, monkeypatch):
        monkeypatch.setenv(BACKEND_ENV, "redis")
        assert backend_from_env() is Backend.REDIS

    def test_case_and_whitespace_insensitive(self, monkeypatch):
        monkeypatch.setenv(BACKEND_ENV, "  ConfigMap  ")
        assert backend_from_env() is Backend.CONFIGMAP

    def test_invalid_fails_closed(self, monkeypatch):
        monkeypatch.setenv(BACKEND_ENV, "postgres")
        with pytest.raises(ValueError, match="invalid"):
            backend_from_env()


class TestBuildStore:
    def test_configmap_builds_only_configmap(self):
        redis, cm = _Recorder(), _Recorder()
        store = build_store(Backend.CONFIGMAP, redis_factory=redis, configmap_factory=cm)
        assert cm.calls == 1
        assert redis.calls == 0  # never construct the Redis client for a ConfigMap install
        assert store is not None

    def test_redis_builds_only_redis(self):
        redis, cm = _Recorder(), _Recorder()
        store = build_store(Backend.REDIS, redis_factory=redis, configmap_factory=cm)
        assert redis.calls == 1
        assert cm.calls == 0  # never load the K8s client for a Redis install
        assert store is not None


class TestMakeHandler:
    def test_single_store_used_for_all(self):
        only = object()
        c = _classifier(_entry(), _entry(key="ufm:state:b", path="/opt/ufm/files/conf/b.json"))
        for entry in c.entries:
            h = make_handler(entry, only, UFM_VERSION, WRITTEN_BY)
            assert h.store is only
