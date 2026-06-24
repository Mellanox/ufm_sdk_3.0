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

"""Unit tests for the ConfigMap-backed Store."""

import base64
import re

import pytest

from state_mirror import store as store_mod
from state_mirror import wire
from state_mirror.store import (
    BODY_FIELD,
    KEY_ANNOTATION,
    MANAGED_BY_LABEL,
    MANAGED_BY_VALUE,
    ConfigMapStore,
    configmap_name,
)

# DNS-1123 subdomain (what a ConfigMap name must satisfy).
_DNS1123 = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$")


class _ApiException(Exception):
    def __init__(self, status):
        super().__init__(f"status={status}")
        self.status = status


class FakeConfigMapApi:
    """In-memory CoreV1-ish ConfigMap API for unit tests."""

    def __init__(self):
        self.objs: dict[str, dict] = {}

    def read_cm(self, name):
        obj = self.objs.get(name)
        if obj is None:
            return None
        return {
            "name": name,
            "annotations": dict(obj["annotations"]),
            "data": dict(obj["data"]),
            "binary_data": dict(obj["binary_data"]),
        }

    def write_cm(self, name, *, labels, annotations, data, binary_data):
        self.objs[name] = {
            "labels": dict(labels),
            "annotations": dict(annotations),
            "data": dict(data),
            "binary_data": dict(binary_data),
        }

    def delete_cm(self, name):
        self.objs.pop(name, None)

    def list_cms(self, label_selector):
        out = []
        for name, obj in self.objs.items():
            if obj["labels"].get(MANAGED_BY_LABEL) == MANAGED_BY_VALUE:
                out.append(
                    {
                        "name": name,
                        "annotations": dict(obj["annotations"]),
                        "data": dict(obj["data"]),
                        "binary_data": dict(obj["binary_data"]),
                    }
                )
        return out


@pytest.fixture
def cm_api():
    return FakeConfigMapApi()


@pytest.fixture
def cm_store(cm_api):
    return ConfigMapStore(cm_api)


def _put(store, key, body, handler="blob", ufm_version="7.0.1"):
    meta = wire.build_meta(body, handler, ufm_version, "state-mirror:test")
    store.put(key, body, meta)
    return meta


class TestRoundTrip:
    def test_put_then_get(self, cm_store):
        _put(cm_store, "ufm:cfg:plugins", b"payload")
        body, meta = cm_store.get("ufm:cfg:plugins")
        assert body == b"payload"
        assert meta.size_bytes == 7
        assert meta.handler == "blob"

    def test_binary_safe(self, cm_store):
        raw = bytes(range(256))  # non-UTF-8 / NUL bytes
        _put(cm_store, "ufm:cfg:blob", raw)
        body, _ = cm_store.get("ufm:cfg:blob")
        assert body == raw

    def test_get_meta(self, cm_store):
        _put(cm_store, "ufm:cfg:plugins", b"abc")
        meta = cm_store.get_meta("ufm:cfg:plugins")
        assert meta is not None
        assert meta.size_bytes == 3

    def test_absent_key(self, cm_store):
        assert cm_store.get("ufm:cfg:absent") is None
        assert cm_store.get_meta("ufm:cfg:absent") is None

    def test_overwrite(self, cm_store):
        _put(cm_store, "ufm:cfg:plugins", b"v1")
        _put(cm_store, "ufm:cfg:plugins", b"v2-longer")
        body, meta = cm_store.get("ufm:cfg:plugins")
        assert body == b"v2-longer"
        assert meta.size_bytes == len(b"v2-longer")

    def test_delete(self, cm_store):
        _put(cm_store, "ufm:cfg:plugins", b"abc")
        cm_store.delete("ufm:cfg:plugins")
        assert cm_store.get("ufm:cfg:plugins") is None

    def test_delete_absent_is_idempotent(self, cm_store):
        cm_store.delete("ufm:cfg:never")  # must not raise


class TestListKeys:
    def test_prefix_filtering(self, cm_store):
        _put(cm_store, "ufm:cfg:a", b"1")
        _put(cm_store, "ufm:cfg:b", b"2")
        _put(cm_store, "ufm:other:c", b"3")
        assert sorted(cm_store.list_keys("ufm:cfg:")) == ["ufm:cfg:a", "ufm:cfg:b"]
        assert cm_store.list_keys("ufm:other:") == ["ufm:other:c"]

    def test_annotation_carries_original_key(self, cm_api, cm_store):
        _put(cm_store, "ufm:cfg:plugins:child.json", b"x")
        name = configmap_name("ufm:cfg:plugins:child.json")
        assert cm_api.objs[name]["annotations"][KEY_ANNOTATION] == "ufm:cfg:plugins:child.json"


class TestFailClosed:
    def test_corrupt_body_raises(self, cm_api, cm_store):
        _put(cm_store, "ufm:cfg:plugins", b"payload")
        name = configmap_name("ufm:cfg:plugins")
        cm_api.objs[name]["binary_data"][BODY_FIELD] = base64.b64encode(b"tampered").decode()
        with pytest.raises(wire.WireError, match="content hash mismatch"):
            cm_store.get("ufm:cfg:plugins")

    def test_missing_body_raises(self, cm_api, cm_store):
        _put(cm_store, "ufm:cfg:plugins", b"payload")
        name = configmap_name("ufm:cfg:plugins")
        cm_api.objs[name]["binary_data"].clear()
        with pytest.raises(wire.WireError, match="body key missing"):
            cm_store.get("ufm:cfg:plugins")

    def test_ceiling_fails_closed(self, cm_api):
        store = ConfigMapStore(cm_api, max_object_bytes=128)
        meta = wire.build_meta(b"x" * 512, "blob", "7.0.1", "state-mirror:test")
        with pytest.raises(wire.WireError, match="exceeds ConfigMap limit") as ei:
            store.put("ufm:cfg:big", b"x" * 512, meta)
        assert ei.value.reason == "toolarge"
        # Nothing was written.
        assert cm_api.objs == {}


class TestErrorClassification:
    def test_read_404_returns_none(self, cm_store, cm_api):
        def boom(_name):
            raise _ApiException(404)

        cm_api.read_cm = boom
        assert cm_store.get("ufm:cfg:plugins") is None

    def test_write_403_raises_forbidden(self, cm_store, cm_api):
        def boom(*_a, **_k):
            raise _ApiException(403)

        cm_api.write_cm = boom
        meta = wire.build_meta(b"x", "blob", "7.0.1", "state-mirror:test")
        with pytest.raises(wire.WireError) as ei:
            cm_store.put("ufm:cfg:plugins", b"x", meta)
        assert ei.value.reason == "forbidden"

    def test_read_409_propagates_as_wire_error(self, cm_store, cm_api):
        def boom(_name):
            raise _ApiException(409)

        cm_api.read_cm = boom
        with pytest.raises(wire.WireError) as ei:
            cm_store.get("ufm:cfg:plugins")
        assert ei.value.reason == "conflict"


class TestConfigMapName:
    @pytest.mark.parametrize(
        "key",
        [
            "ufm:opensm:opensm.conf",
            "ufm:cfg:plugins:child.json",
            "UFM:Mixed:Case",
            "a",
            "x" * 400,
        ],
    )
    def test_name_is_dns1123(self, key):
        name = configmap_name(key)
        assert len(name) <= 253
        assert _DNS1123.match(name), name

    def test_name_is_deterministic(self):
        assert configmap_name("ufm:cfg:a") == configmap_name("ufm:cfg:a")

    def test_distinct_keys_distinct_names(self):
        # Keys that sanitize to the same base must still differ (hash suffix).
        assert configmap_name("ufm:cfg:a") != configmap_name("ufm.cfg.a")


def test_protocol_symbols_exported():
    # Guard against accidental rename of the public field/label constants the
    # consumer Helm wiring and tests depend on.
    assert store_mod.MANAGED_BY_VALUE == "state-mirror"
    assert store_mod.BODY_FIELD == "body"
    assert store_mod.META_FIELD == "meta"
