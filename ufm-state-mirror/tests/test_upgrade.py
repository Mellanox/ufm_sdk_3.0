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

"""Tests for the transactional UFM no-PVC upgrade handoff."""

import copy

import pytest

from state_mirror import wire
from state_mirror.classifier import Classifier
from state_mirror.store import ConfigMapStore, RedisStore
from state_mirror.upgrade import (
    HANDOFF_LABEL,
    HANDOFF_LABEL_VALUE,
    MANIFEST_KEY,
    UpgradeError,
    _commit_target_from_env,
    commit,
    load_manifest,
    preflight,
)

OPERATION_ID = "0123456789abcdef0123456789abcdef"


class FakeConfigMaps:
    def __init__(self):
        self.objs = {}

    def read_cm(self, name):
        value = self.objs.get(name)
        return copy.deepcopy(value) if value is not None else None

    def write_cm(self, name, *, labels, annotations, data, binary_data):
        self.objs[name] = {
            "name": name,
            "labels": dict(labels),
            "annotations": dict(annotations),
            "data": dict(data),
            "binary_data": dict(binary_data),
        }

    def delete_cm(self, name):
        self.objs.pop(name, None)

    def list_cms(self, label_selector):
        key, value = label_selector.split("=", 1)
        return [
            copy.deepcopy(obj)
            for obj in self.objs.values()
            if obj.get("labels", {}).get(key) == value
        ]

    def source_gv(self, value="old-gv\n"):
        self.objs["ufm-gv-cfg"] = {
            "name": "ufm-gv-cfg",
            "labels": {},
            "annotations": {},
            "data": {"gv.cfg": value},
            "binary_data": {},
        }


@pytest.fixture(params=["configmap", "redis"])
def backend(request, fake_redis):
    api = FakeConfigMaps()
    store = ConfigMapStore(api) if request.param == "configmap" else RedisStore(fake_redis)
    return store, api


@pytest.fixture
def classifier():
    return Classifier.from_dict(
        {
            "entries": [
                {
                    "path": "/opt/ufm/files/conf/a.json",
                    "handler": "blob",
                    "redis_key": "ufm:state:a",
                },
                {
                    "path": "/opt/ufm/files/conf/plugins",
                    "handler": "directory",
                    "redis_key_prefix": "ufm:plugins:",
                    "recursive": True,
                },
            ]
        }
    )


def _put(store, key, version, body=b"state"):
    store.put(key, body, wire.build_meta(body, "blob", version, "test"))


def _env(api):
    return dict(
        line.split("=", 1) for line in api.objs["ufm-upgrade"]["data"]["upgrade.env"].splitlines()
    )


def _preflight(store, api, classifier, target="7.1.0"):
    api.source_gv()
    return preflight(
        classifier=classifier,
        target_version=target,
        handoff_configmap="ufm-upgrade",
        source_gv_configmap="ufm-gv-cfg",
        source_gv_key="gv.cfg",
        store=store,
        configmaps=api,
        operation_id=OPERATION_ID,
    )


def _mount_handoff(tmp_path, api):
    path = tmp_path / "handoff"
    path.mkdir()
    (path / "upgrade.env").write_text(
        api.objs["ufm-upgrade"]["data"]["upgrade.env"], encoding="utf-8"
    )
    return str(path)


class TestPreflight:
    def test_fresh_state_produces_no_upgrade_transaction(self, backend, classifier):
        store, api = backend
        transaction = _preflight(store, api, classifier)
        assert transaction is None
        assert _env(api) == {
            "STATE_MIRROR_UPGRADE_MODE": "fresh",
            "STATE_MIRROR_TARGET_VERSION": "7.1.0",
            "STATE_MIRROR_OPERATION_ID": OPERATION_ID,
        }
        assert store.get(MANIFEST_KEY) is None

    def test_resolves_one_legacy_source_version(self, backend, classifier):
        store, api = backend
        _put(store, "ufm:state:a", "7.0.0")
        _put(store, "ufm:plugins:nested/tool.json", "7.0.0")
        transaction = _preflight(store, api, classifier)
        assert transaction.source_version == "7.0.0"
        assert transaction.target_version == "7.1.0"
        assert _env(api)["STATE_MIRROR_UPGRADE_MODE"] == "upgrade"

    def test_inconsistent_metadata_fails_closed(self, backend, classifier):
        store, api = backend
        _put(store, "ufm:state:a", "7.0.0")
        _put(store, "ufm:plugins:tool.json", "6.9.0")
        with pytest.raises(UpgradeError, match="inconsistent source-version"):
            _preflight(store, api, classifier)
        assert "ufm-upgrade" not in api.objs

    def test_corrupt_metadata_or_body_fails_closed(self, backend, classifier):
        store, api = backend
        _put(store, "ufm:state:a", "7.0.0")
        if isinstance(store, RedisStore):
            store._client.store["ufm:state:a"] = b"corrupt"
        else:
            name = next(
                name
                for name, cm in api.objs.items()
                if cm.get("annotations", {}).get("state-mirror.nvidia.com/key") == "ufm:state:a"
            )
            api.objs[name]["binary_data"]["body"] = "Y29ycnVwdA=="
        with pytest.raises(wire.WireError, match="content hash mismatch"):
            _preflight(store, api, classifier)

    def test_downgrade_fails_closed(self, backend, classifier):
        store, api = backend
        _put(store, "ufm:state:a", "7.2.0")
        with pytest.raises(UpgradeError, match="downgrade refused"):
            _preflight(store, api, classifier, target="7.1.0")

    def test_reads_exact_gv_key_and_generates_preserve_paths(self, backend, classifier):
        store, api = backend
        _put(store, "ufm:state:a", "7.0.0")
        api.source_gv("exact-old-helm-gv\n")
        preflight(
            classifier=classifier,
            target_version="7.1.0",
            handoff_configmap="ufm-upgrade",
            source_gv_configmap="ufm-gv-cfg",
            source_gv_key="gv.cfg",
            store=store,
            configmaps=api,
            operation_id=OPERATION_ID,
        )
        data = api.objs["ufm-upgrade"]["data"]
        assert data["source-gv.cfg"] == "exact-old-helm-gv\n"
        assert data["preserve-paths.txt"] == "conf/a.json\nconf/plugins\n"
        assert api.objs["ufm-upgrade"]["labels"] == {HANDOFF_LABEL: HANDOFF_LABEL_VALUE}

    def test_classifier_cannot_own_helm_gv(self, backend):
        store, api = backend
        classifier = Classifier.from_dict(
            {
                "entries": [
                    {
                        "path": "/opt/ufm/files/conf/gv.cfg",
                        "handler": "blob",
                        "redis_key": "ufm:gv",
                    }
                ]
            }
        )
        with pytest.raises(UpgradeError, match="ownership conflict"):
            _preflight(store, api, classifier)


class TestCommit:
    def test_environment_target_versions_must_agree(self, monkeypatch):
        monkeypatch.setenv("STATE_MIRROR_TARGET_VERSION", "7.1.0")
        monkeypatch.setenv("UFM_VERSION", "7.2.0")
        with pytest.raises(UpgradeError, match="target version conflict"):
            _commit_target_from_env()

    def test_fresh_handoff_commits_without_running_an_upgrade(self, backend, classifier, tmp_path):
        store, api = backend
        assert _preflight(store, api, classifier) is None

        manifest = commit(
            handoff_dir=_mount_handoff(tmp_path, api),
            target_version="7.1.0",
            store=store,
            configmaps=api,
        )

        assert manifest.source_version == manifest.target_version == "7.1.0"
        assert _env(api)["STATE_MIRROR_UPGRADE_MODE"] == "committed"

    def test_commit_is_idempotent_on_both_backends(self, backend, classifier, tmp_path):
        store, api = backend
        _put(store, "ufm:state:a", "7.0.0")
        _preflight(store, api, classifier)
        handoff_dir = _mount_handoff(tmp_path, api)

        first = commit(
            handoff_dir=handoff_dir,
            target_version="7.1.0",
            store=store,
            configmaps=api,
        )
        second = commit(
            handoff_dir=handoff_dir,
            target_version="7.1.0",
            store=store,
            configmaps=api,
        )

        assert second == first
        assert load_manifest(store) == first
        assert _env(api) == {
            "STATE_MIRROR_UPGRADE_MODE": "committed",
            "STATE_MIRROR_TARGET_VERSION": "7.1.0",
            "STATE_MIRROR_OPERATION_ID": OPERATION_ID,
        }

        # A restarted pod mounts the now-committed ConfigMap, which deliberately
        # no longer contains STATE_MIRROR_SOURCE_VERSION. Commit remains a no-op.
        committed_mount = tmp_path / "committed"
        committed_mount.mkdir()
        (committed_mount / "upgrade.env").write_text(
            api.objs["ufm-upgrade"]["data"]["upgrade.env"], encoding="utf-8"
        )
        assert (
            commit(
                handoff_dir=str(committed_mount),
                target_version="7.1.0",
                store=store,
                configmaps=api,
            )
            == first
        )

    def test_committed_transaction_prevents_replay_after_restart(
        self, backend, classifier, tmp_path
    ):
        store, api = backend
        _put(store, "ufm:state:a", "7.0.0")
        _preflight(store, api, classifier)
        commit(
            handoff_dir=_mount_handoff(tmp_path, api),
            target_version="7.1.0",
            store=store,
            configmaps=api,
        )

        transaction = _preflight(store, api, classifier, target="7.1.0")
        assert transaction is None
        assert _env(api)["STATE_MIRROR_UPGRADE_MODE"] == "committed"
        assert _env(api)["STATE_MIRROR_OPERATION_ID"] == OPERATION_ID

    def test_rejects_conflicting_transaction(self, backend, classifier, tmp_path):
        store, api = backend
        _put(store, "ufm:state:a", "7.0.0")
        _preflight(store, api, classifier)
        handoff_dir = _mount_handoff(tmp_path, api)
        commit(
            handoff_dir=handoff_dir,
            target_version="7.1.0",
            store=store,
            configmaps=api,
        )
        mounted = tmp_path / "handoff" / "upgrade.env"
        mounted.write_text(
            mounted.read_text(encoding="utf-8").replace(OPERATION_ID, "f" * 32),
            encoding="utf-8",
        )
        with pytest.raises(UpgradeError, match="conflicts"):
            commit(
                handoff_dir=handoff_dir,
                target_version="7.1.0",
                store=store,
                configmaps=api,
            )
