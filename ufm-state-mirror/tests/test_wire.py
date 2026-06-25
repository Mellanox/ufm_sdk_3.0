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

"""Unit tests for the StateMirror Redis wire format."""

import pytest

from state_mirror import wire


def _put(client, key, body, ufm_version="7.0.1"):
    meta = wire.build_meta(body, "blob", ufm_version, "state-mirror:test")
    wire.write_pair(client, key, body, meta)


class TestMeta:
    def test_content_hash_deterministic(self):
        assert wire.content_hash(b"abc") == wire.content_hash(b"abc")
        assert wire.content_hash(b"abc") != wire.content_hash(b"abd")

    def test_meta_json_roundtrip(self):
        meta = wire.build_meta(b"hello", "blob", "7.0.1", "state-mirror:test")
        again = wire.Meta.from_json(meta.to_json())
        assert meta.content_hash == again.content_hash
        assert again.size_bytes == 5
        assert again.handler == "blob"
        assert again.format_version == wire.FORMAT_VERSION

    def test_from_json_missing_field(self):
        with pytest.raises(wire.WireError, match="missing required field"):
            wire.Meta.from_json(b'{"handler": "blob"}')

    def test_from_json_bad_json(self):
        with pytest.raises(wire.WireError, match="not valid JSON"):
            wire.Meta.from_json(b"not-json")


class TestReadVerify:
    def test_write_then_read(self, fake_redis):
        _put(fake_redis, "ufm:state:a", b"payload")
        body, meta = wire.read_and_verify(fake_redis, "ufm:state:a")
        assert body == b"payload"
        assert meta.size_bytes == 7

    def test_missing_meta_returns_none(self, fake_redis):
        assert wire.read_and_verify(fake_redis, "ufm:state:absent") is None

    def test_body_missing_raises(self, fake_redis):
        _put(fake_redis, "ufm:state:a", b"payload")
        del fake_redis.store["ufm:state:a"]
        with pytest.raises(wire.WireError, match="body key missing"):
            wire.read_and_verify(fake_redis, "ufm:state:a")

    def test_hash_mismatch_raises(self, fake_redis):
        _put(fake_redis, "ufm:state:a", b"payload")
        fake_redis.store["ufm:state:a"] = b"tampered"
        with pytest.raises(wire.WireError, match="content hash mismatch"):
            wire.read_and_verify(fake_redis, "ufm:state:a")

    def test_newer_format_version_refused(self, fake_redis):
        meta = wire.build_meta(b"payload", "blob", "7.0.1", "state-mirror:test")
        meta.format_version = wire.FORMAT_VERSION + 1
        wire.write_pair(fake_redis, "ufm:state:a", b"payload", meta)
        with pytest.raises(wire.WireError, match="refusing downgrade"):
            wire.read_and_verify(fake_redis, "ufm:state:a")

    def test_verify_body_none_reports_body_missing_even_with_newer_format(self):
        # The cheap, more-specific presence check must win over the format check
        # when both would fire, so a missing body reports the right error (FIX-2).
        meta = wire.build_meta(b"x", "blob", "7.0.1", "state-mirror:test")
        meta.format_version = wire.FORMAT_VERSION + 1
        with pytest.raises(wire.WireError, match="body key missing"):
            wire.verify_body(None, meta, "ufm:state:a")

    def test_newer_format_refused_before_body_fetch(self):
        # read_and_verify must refuse a too-new format WITHOUT fetching the
        # (possibly huge) body -- the format check stays a pre-fetch guard (FIX-2).
        meta = wire.build_meta(b"payload", "blob", "7.0.1", "state-mirror:test")
        meta.format_version = wire.FORMAT_VERSION + 1

        class _MetaOnlyClient:
            def get(self, key):
                if key.endswith(wire.META_SUFFIX):
                    return meta.to_json()
                raise AssertionError("body must not be fetched for a too-new format")

        with pytest.raises(wire.WireError, match="refusing downgrade"):
            wire.read_and_verify(_MetaOnlyClient(), "ufm:state:a")

    def test_delete_pair(self, fake_redis):
        _put(fake_redis, "ufm:state:a", b"payload")
        wire.delete_pair(fake_redis, "ufm:state:a")
        assert wire.read_and_verify(fake_redis, "ufm:state:a") is None


class _OomClient:
    """Client whose writes/reads fail with a server OOM error."""

    def pipeline(self, transaction=True):
        raise RuntimeError("OOM command not allowed when used memory > 'maxmemory'.")

    def get(self, key):
        raise RuntimeError("OOM command not allowed when used memory > 'maxmemory'.")


class TestWireErrorReason:
    def test_write_failure_carries_reason(self):
        meta = wire.build_meta(b"x", "blob", "7.0.1", "state-mirror:test")
        with pytest.raises(wire.WireError) as ei:
            wire.write_pair(_OomClient(), "ufm:state:a", b"x", meta)
        assert ei.value.reason == "oom"

    def test_read_failure_carries_reason(self):
        with pytest.raises(wire.WireError) as ei:
            wire.read_and_verify(_OomClient(), "ufm:state:a")
        assert ei.value.reason == "oom"

    def test_integrity_failure_has_no_reason(self, fake_redis):
        _put(fake_redis, "ufm:state:a", b"payload")
        fake_redis.store["ufm:state:a"] = b"tampered"
        with pytest.raises(wire.WireError) as ei:
            wire.read_and_verify(fake_redis, "ufm:state:a")
        assert ei.value.reason is None
