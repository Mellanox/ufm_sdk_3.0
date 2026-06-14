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

"""Unit tests for the StateMirror classifier schema + validation."""

import os

import pytest

from state_mirror.classifier import Baseline, Classifier, ClassifierError, Entry, Handler

COMPONENT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The engine ships no built-in classifier: each consumer (UFM, UFM HA) supplies
# its own via CLASSIFIER_PATH. We validate the engine against the bundled
# example. Consumer-specific file-set assertions live in the consumer repo.
EXAMPLE_CLASSIFIER = os.path.join(COMPONENT_ROOT, "examples", "classifier-example.yaml")


def _blob(**over):
    d = {"path": "/opt/ufm/files/conf/a.json", "handler": "blob", "redis_key": "ufm:state:a"}
    d.update(over)
    return d


class TestEntryValidation:
    def test_minimal_blob_ok(self):
        e = Entry.from_dict(_blob())
        assert e.handler is Handler.BLOB
        assert e.redis_key == "ufm:state:a"
        assert e.rate_limit_ms == 100
        assert e.baseline is Baseline.SKIP

    def test_blob_requires_redis_key(self):
        with pytest.raises(ClassifierError, match="requires 'redis_key'"):
            Entry.from_dict(_blob(redis_key=None))

    def test_blob_rejects_prefix(self):
        with pytest.raises(ClassifierError, match="only valid for the directory"):
            Entry.from_dict(_blob(redis_key_prefix="ufm:x:"))

    def test_directory_requires_prefix(self):
        with pytest.raises(ClassifierError, match="requires 'redis_key_prefix'"):
            Entry.from_dict({"path": "/opt/ufm/files/conf/plugins", "handler": "directory"})

    def test_directory_rejects_redis_key(self):
        with pytest.raises(ClassifierError, match="must not set 'redis_key'"):
            Entry.from_dict(
                {
                    "path": "/opt/ufm/files/conf/plugins",
                    "handler": "directory",
                    "redis_key_prefix": "ufm:cfg:plugins:",
                    "redis_key": "nope",
                }
            )

    def test_invalid_handler(self):
        with pytest.raises(ClassifierError, match="invalid handler"):
            Entry.from_dict(_blob(handler="bogus"))

    def test_missing_path(self):
        with pytest.raises(ClassifierError, match="non-empty string 'path'"):
            Entry.from_dict(_blob(path=""))

    @pytest.mark.parametrize("bad", [0, -1, "100", True])
    def test_rate_limit_must_be_positive_int(self, bad):
        with pytest.raises(ClassifierError, match="rate_limit_ms"):
            Entry.from_dict(_blob(rate_limit_ms=bad))

    def test_baseline_image_requires_path(self):
        with pytest.raises(ClassifierError, match="requires 'baseline_path'"):
            Entry.from_dict(_blob(baseline="image"))

    def test_baseline_path_without_image_rejected(self):
        with pytest.raises(ClassifierError, match="only valid with baseline 'image'"):
            Entry.from_dict(_blob(baseline="skip", baseline_path="/x"))

    def test_baseline_image_ok(self):
        e = Entry.from_dict(_blob(baseline="image", baseline_path="/opt/ufm/baseline/a"))
        assert e.baseline is Baseline.IMAGE
        assert e.baseline_path == "/opt/ufm/baseline/a"

    def test_wal_threshold_only_for_sqlite(self):
        with pytest.raises(ClassifierError, match="only valid for the sqlite"):
            Entry.from_dict(_blob(wal_threshold_bytes=1024))

    def test_wal_threshold_must_be_positive_int(self):
        with pytest.raises(ClassifierError, match="wal_threshold_bytes"):
            Entry.from_dict(
                {
                    "path": "/opt/ufm/files/sqlite/x.db",
                    "handler": "sqlite",
                    "redis_key": "ufm:sqlite:x",
                    "wal_threshold_bytes": 0,
                }
            )

    def test_sqlite_with_wal_threshold_ok(self):
        e = Entry.from_dict(
            {
                "path": "/opt/ufm/files/sqlite/x.db",
                "handler": "sqlite",
                "redis_key": "ufm:sqlite:x",
                "wal_threshold_bytes": 1024,
            }
        )
        assert e.wal_threshold_bytes == 1024


class TestClassifierDocument:
    def test_empty_entries_rejected(self):
        with pytest.raises(ClassifierError, match="non-empty 'entries'"):
            Classifier.from_dict({"entries": []})

    def test_duplicate_path_rejected(self):
        with pytest.raises(ClassifierError, match="duplicate path"):
            Classifier.from_dict({"entries": [_blob(), _blob(redis_key="ufm:state:b")]})

    def test_duplicate_key_rejected(self):
        with pytest.raises(ClassifierError, match="duplicate redis key"):
            Classifier.from_dict({"entries": [_blob(), _blob(path="/opt/ufm/files/conf/b.json")]})

    def test_by_handler(self):
        c = Classifier.from_dict(
            {
                "entries": [
                    _blob(),
                    _blob(
                        path="/opt/ufm/files/sqlite/x.db",
                        handler="sqlite",
                        redis_key="ufm:sqlite:x",
                    ),
                ]
            }
        )
        assert len(c) == 2
        assert len(c.by_handler(Handler.SQLITE)) == 1


class TestExampleClassifier:
    """Validate the engine against the bundled example classifier.

    These assertions are intentionally generic (structural invariants of the
    classifier schema). Consumer-specific file-set checks -- e.g. that UFM's
    real classifier contains ``ufm:opensm:guid2lid`` and is reconciled against
    a running UFM pod's filesystem -- belong in the consumer repo (UFM /
    UFM HA), where the authoritative classifier and the file set both live.
    """

    def test_example_yaml_is_valid(self):
        c = Classifier.load_file(EXAMPLE_CLASSIFIER)
        assert len(c) >= 1
        # Every entry resolves to exactly one of redis_key / redis_key_prefix,
        # consistent with its handler kind.
        for e in c.entries:
            if e.is_directory:
                assert e.redis_key_prefix
                assert not e.redis_key
            else:
                assert e.redis_key
                assert not e.redis_key_prefix

    def test_example_keys_are_unique(self):
        c = Classifier.load_file(EXAMPLE_CLASSIFIER)
        keys = [e.redis_key or e.redis_key_prefix for e in c.entries]
        paths = [e.path for e in c.entries]
        assert len(keys) == len(set(keys))
        assert len(paths) == len(set(paths))
