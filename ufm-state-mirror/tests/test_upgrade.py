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

import base64
import copy

import pytest

from state_mirror import wire
from state_mirror.checkpoint import final_checkpoint
from state_mirror.classifier import Classifier
from state_mirror.generation import FencedStore
from state_mirror.mirror import Mirror
from state_mirror.store import ConfigMapStore, RedisStore
from state_mirror.upgrade import (
    HANDOFF_LABEL,
    HANDOFF_LABEL_VALUE,
    MANIFEST_KEY,
    UpgradeError,
    UpgradeManifest,
    _commit_target_from_env,
    commit,
    compare_versions,
    load_manifest,
    preflight,
)

OPERATION_ID = "0123456789abcdef0123456789abcdef"


class FakeConfigMaps:
    def __init__(self):
        self.objs = {}
        self.next_resource_version = 1
        self.before_cas = None

    def read_cm(self, name):
        value = self.objs.get(name)
        return copy.deepcopy(value) if value is not None else None

    def write_cm(self, name, *, labels, annotations, data, binary_data):
        self.objs[name] = {
            "name": name,
            "resource_version": str(self.next_resource_version),
            "labels": dict(labels),
            "annotations": dict(annotations),
            "data": dict(data),
            "binary_data": dict(binary_data),
        }
        self.next_resource_version += 1

    def write_cm_cas(
        self,
        name,
        *,
        expected_resource_version,
        labels,
        annotations,
        data,
        binary_data,
    ):
        if self.before_cas is not None:
            hook, self.before_cas = self.before_cas, None
            hook(self)
        current = self.objs.get(name)
        current_version = current["resource_version"] if current is not None else None
        if current_version != expected_resource_version:
            return False
        self.write_cm(
            name,
            labels=labels,
            annotations=annotations,
            data=data,
            binary_data=binary_data,
        )
        return True

    def delete_cm(self, name):
        self.objs.pop(name, None)

    def list_cms(self, label_selector):
        key, value = label_selector.split("=", 1)
        return [
            copy.deepcopy(obj)
            for obj in self.objs.values()
            if obj.get("labels", {}).get(key) == value
        ]

    def source_gv(self, value="old-gv\n", binary=False):
        encoded = base64.b64encode(value.encode("utf-8")).decode("ascii")
        self.objs["ufm-gv-cfg"] = {
            "name": "ufm-gv-cfg",
            "labels": {},
            "annotations": {},
            "data": {} if binary else {"gv.cfg": value},
            "binary_data": {"gv.cfg": encoded} if binary else {},
        }


@pytest.fixture(params=["configmap", "redis"])
def backend(request, fake_redis):
    api = FakeConfigMaps()
    store = ConfigMapStore(api) if request.param == "configmap" else RedisStore(fake_redis)
    return store, api


@pytest.fixture
def classifier(tmp_path, monkeypatch):
    root = tmp_path / "files"
    monkeypatch.setattr("state_mirror.upgrade.FILES_ROOT", str(root))
    (root / "conf/plugins").mkdir(parents=True)
    (root / "conf/a.json").write_bytes(b"state")
    return Classifier.from_dict(
        {
            "entries": [
                {
                    "path": str(root / "conf/a.json"),
                    "handler": "blob",
                    "redis_key": "ufm:state:a",
                },
                {
                    "path": str(root / "conf/plugins"),
                    "handler": "directory",
                    "redis_key_prefix": "ufm:plugins:",
                    "recursive": True,
                },
            ]
        }
    )


def _put(store, key, version, body=b"state", written_at=None):
    meta = wire.build_meta(body, "blob", version, "test")
    if written_at is not None:
        meta.written_at = written_at
    store.put(key, body, meta)


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


def _mount_handoff(tmp_path, api, store, classifier):
    values = _env(api)
    if values["STATE_MIRROR_UPGRADE_MODE"] == "upgrade":
        manifest = load_manifest(store)
        view = FencedStore(
            store,
            manifest.generation if manifest else "",
            classifier.digest(),
            values["STATE_MIRROR_SOURCE_VERSION"],
        )
        mirror = Mirror(classifier, view, values["STATE_MIRROR_SOURCE_VERSION"], "test")
        final_checkpoint(
            mirror,
            classifier,
            api,
            {
                "quiesced": True,
                "operation_id": values["STATE_MIRROR_OPERATION_ID"],
                "target_version": values["STATE_MIRROR_TARGET_VERSION"],
                "digest": classifier.digest(),
            },
        )
    path = tmp_path / "handoff"
    path.mkdir()
    for name, value in api.objs["ufm-upgrade"]["data"].items():
        (path / name).write_text(value, encoding="utf-8")
    return str(path)


class TestPreflight:
    def test_handoff_cannot_overwrite_source_gv_configmap(self, backend, classifier):
        store, api = backend
        with pytest.raises(UpgradeError, match="must be different"):
            preflight(
                classifier=classifier,
                target_version="7.1.0",
                handoff_configmap="same-configmap",
                source_gv_configmap="same-configmap",
                source_gv_key="gv.cfg",
                store=store,
                configmaps=api,
            )

    def test_fresh_state_produces_no_upgrade_transaction(self, backend, classifier):
        store, api = backend
        transaction = _preflight(store, api, classifier)
        assert transaction is None
        assert _env(api) == {
            "STATE_MIRROR_UPGRADE_MODE": "fresh",
            "STATE_MIRROR_TARGET_VERSION": "7.1.0",
            "STATE_MIRROR_OPERATION_ID": OPERATION_ID,
            "STATE_MIRROR_CLASSIFIER_DIGEST": classifier.digest(),
        }
        assert store.get(MANIFEST_KEY) is None

    def test_fresh_preflight_retry_reuses_operation(self, backend, classifier):
        store, api = backend
        api.source_gv()
        kwargs = {
            "classifier": classifier,
            "target_version": "7.1.0",
            "handoff_configmap": "ufm-upgrade",
            "source_gv_configmap": "ufm-gv-cfg",
            "source_gv_key": "gv.cfg",
            "store": store,
            "configmaps": api,
        }
        assert preflight(**kwargs) is None
        first_operation = _env(api)["STATE_MIRROR_OPERATION_ID"]
        assert preflight(**kwargs) is None
        assert _env(api)["STATE_MIRROR_OPERATION_ID"] == first_operation

    def test_fresh_preflight_rejects_conflicting_target(self, backend, classifier):
        store, api = backend
        assert _preflight(store, api, classifier, target="7.1.0") is None
        with pytest.raises(UpgradeError, match="existing handoff conflicts"):
            _preflight(store, api, classifier, target="7.2.0")
        assert _env(api)["STATE_MIRROR_TARGET_VERSION"] == "7.1.0"

    @pytest.mark.parametrize(
        "data",
        [
            pytest.param({}, id="missing-upgrade-env"),
            pytest.param(
                {
                    "upgrade.env": (
                        "STATE_MIRROR_UPGRADE_MODE=unknown\n"
                        "STATE_MIRROR_TARGET_VERSION=7.1.0\n"
                        f"STATE_MIRROR_OPERATION_ID={OPERATION_ID}\n"
                    )
                },
                id="unsupported-mode",
            ),
            pytest.param(
                {
                    "upgrade.env": (
                        "STATE_MIRROR_UPGRADE_MODE=upgrade\n"
                        "STATE_MIRROR_SOURCE_VERSION=7.0.0\n"
                        "STATE_MIRROR_TARGET_VERSION=7.1.0\n"
                        f"STATE_MIRROR_OPERATION_ID={OPERATION_ID}\n"
                    )
                },
                id="incomplete-upgrade-payload",
            ),
            pytest.param(
                {
                    "upgrade.env": (
                        "STATE_MIRROR_UPGRADE_MODE=committed\n"
                        "STATE_MIRROR_TARGET_VERSION=7.1.0\n"
                        f"STATE_MIRROR_OPERATION_ID={OPERATION_ID}\n"
                    ),
                    "unexpected.txt": "must fail closed\n",
                },
                id="unexpected-committed-payload",
            ),
        ],
    )
    def test_labeled_malformed_handoff_fails_closed(self, backend, classifier, data):
        store, api = backend
        api.write_cm(
            "ufm-upgrade",
            labels={HANDOFF_LABEL: HANDOFF_LABEL_VALUE},
            annotations={},
            data=data,
            binary_data={},
        )

        with pytest.raises(
            UpgradeError, match="handoff ConfigMap|handoff .*payload|handoff .*environment"
        ):
            _preflight(store, api, classifier)
        assert api.objs["ufm-upgrade"]["data"] == data

    def test_concurrent_fresh_preflight_does_not_overwrite_winner(self, backend, classifier):
        store, api = backend

        def competing_handoff(cm_api):
            cm_api.write_cm(
                "ufm-upgrade",
                labels={HANDOFF_LABEL: HANDOFF_LABEL_VALUE},
                annotations={},
                data={
                    "upgrade.env": (
                        "STATE_MIRROR_UPGRADE_MODE=fresh\n"
                        "STATE_MIRROR_TARGET_VERSION=7.1.0\n"
                        f"STATE_MIRROR_OPERATION_ID={'f' * 32}\n"
                        f"STATE_MIRROR_CLASSIFIER_DIGEST={classifier.digest()}\n"
                    )
                },
                binary_data={},
            )

        api.before_cas = competing_handoff
        with pytest.raises(UpgradeError, match="operation ID conflicts"):
            preflight(
                classifier=classifier,
                target_version="7.1.0",
                handoff_configmap="ufm-upgrade",
                source_gv_configmap="ufm-gv-cfg",
                source_gv_key="gv.cfg",
                store=store,
                configmaps=api,
            )
        assert _env(api)["STATE_MIRROR_OPERATION_ID"] == "f" * 32

    def test_resolves_one_legacy_source_version(self, backend, classifier):
        store, api = backend
        _put(store, "ufm:state:a", "7.0.0")
        _put(store, "ufm:plugins:nested/tool.json", "7.0.0")
        transaction = _preflight(store, api, classifier)
        assert transaction.source_version == "7.0.0"
        assert transaction.target_version == "7.1.0"
        assert _env(api)["STATE_MIRROR_UPGRADE_MODE"] == "upgrade"

    @pytest.mark.parametrize("field", ["source-gv.cfg", "preserve-paths.txt"])
    def test_upgrade_retry_rejects_changed_payload(self, backend, classifier, field):
        store, api = backend
        _put(store, "ufm:state:a", "7.0.0")
        _preflight(store, api, classifier)
        if field == "source-gv.cfg":
            api.objs["ufm-gv-cfg"]["data"]["gv.cfg"] = "different-old-gv\n"
        else:
            api.objs["ufm-upgrade"]["data"][field] = "different/path\n"
        with pytest.raises(UpgradeError, match="handoff payload conflicts"):
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

    @pytest.mark.parametrize("same_timestamp", [True, False])
    def test_divergent_metadata_is_rejected(self, backend, classifier, same_timestamp):
        store, api = backend
        _put(store, "ufm:plugins:tool.json", "6.9.0", written_at="2026-01-02T03:04:05Z")
        stamp = "2026-01-02T03:04:05Z" if same_timestamp else "2026-02-03T04:05:06Z"
        _put(store, "ufm:state:a", "7.0.0", written_at=stamp)
        with pytest.raises(UpgradeError, match="divergent legacy release versions"):
            _preflight(store, api, classifier)
        assert "ufm-upgrade" not in api.objs

    def test_invalid_legacy_write_timestamp_fails_closed(self, backend, classifier):
        store, api = backend
        _put(store, "ufm:state:a", "7.0.0", written_at="not-a-timestamp")

        with pytest.raises(UpgradeError, match="invalid persisted object .* timestamp"):
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

    def test_partial_manifest_fails_closed(self, backend, classifier):
        store, api = backend
        body = b"{}"
        if isinstance(store, RedisStore):
            store._client.store[MANIFEST_KEY] = body
        else:
            _put(store, MANIFEST_KEY, "7.0.0", body)
            name = next(
                name
                for name, cm in api.objs.items()
                if cm.get("annotations", {}).get("state-mirror.nvidia.com/key") == MANIFEST_KEY
            )
            api.objs[name]["data"].clear()
        with pytest.raises(UpgradeError, match="missing body or metadata"):
            _preflight(store, api, classifier)

    def test_downgrade_fails_closed(self, backend, classifier):
        store, api = backend
        _put(store, "ufm:state:a", "7.2.0")
        with pytest.raises(UpgradeError, match="downgrade refused"):
            _preflight(store, api, classifier, target="7.1.0")

    def test_newest_write_still_refuses_downgrade(self, backend, classifier):
        store, api = backend
        _put(
            store,
            "ufm:plugins:tool.json",
            "7.0.0",
            written_at="2026-01-02T03:04:05Z",
        )
        _put(store, "ufm:state:a", "9.9.0", written_at="2026-02-03T04:05:06Z")

        with pytest.raises(UpgradeError, match="divergent legacy release versions"):
            _preflight(store, api, classifier)
        assert "ufm-upgrade" not in api.objs

    def test_reads_source_gv_from_chart_binary_data(self, backend, classifier):
        store, api = backend
        _put(store, "ufm:state:a", "7.0.0")
        api.source_gv(binary=True)

        transaction = preflight(
            classifier=classifier,
            target_version="7.1.0",
            handoff_configmap="ufm-upgrade",
            source_gv_configmap="ufm-gv-cfg",
            source_gv_key="gv.cfg",
            store=store,
            configmaps=api,
            operation_id=OPERATION_ID,
        )

        assert transaction.source_version == "7.0.0"
        assert api.objs["ufm-upgrade"]["data"]["source-gv.cfg"] == "old-gv\n"

    @pytest.mark.parametrize(
        "encoded",
        [
            pytest.param("not-base64!", id="invalid-base64"),
            pytest.param(base64.b64encode(b"\xff").decode("ascii"), id="invalid-utf8"),
        ],
    )
    def test_invalid_binary_source_gv_fails_closed(self, backend, classifier, encoded):
        store, api = backend
        _put(store, "ufm:state:a", "7.0.0")
        api.source_gv(binary=True)
        api.objs["ufm-gv-cfg"]["binary_data"]["gv.cfg"] = encoded

        with pytest.raises(UpgradeError, match="not decodable UTF-8 text"):
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
        assert "ufm-upgrade" not in api.objs

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

    def test_classifier_cannot_overlap_upgrade_manifest(self, backend):
        store, api = backend
        classifier = Classifier.from_dict(
            {
                "entries": [
                    {
                        "path": "/opt/ufm/files/conf/plugins",
                        "handler": "directory",
                        "redis_key_prefix": "state-mirror:",
                        "recursive": True,
                    }
                ]
            }
        )
        with pytest.raises(UpgradeError, match="durable upgrade manifest"):
            _preflight(store, api, classifier)

    def test_semantically_equal_but_distinct_versions_conflict(self, backend, classifier):
        store, api = backend
        _put(store, "ufm:state:a", "7.1")
        with pytest.raises(UpgradeError, match="target/source version conflict"):
            _preflight(store, api, classifier, target="7.1.0")
        assert store.get(MANIFEST_KEY) is None


def test_version_comparison_is_symmetric_for_punctuation_equivalent_suffixes():
    assert compare_versions("7.1.0-rc.1", "7.1.0-rc1") == -1
    assert compare_versions("7.1.0-rc1", "7.1.0-rc.1") == 1


class TestCommit:
    def test_environment_target_versions_must_agree(self, monkeypatch):
        monkeypatch.setenv("STATE_MIRROR_TARGET_VERSION", "7.1.0")
        monkeypatch.setenv("UFM_RELEASE_VERSION", "7.2.0")
        with pytest.raises(UpgradeError, match="target version conflict"):
            _commit_target_from_env()

    def test_fresh_handoff_commits_without_running_an_upgrade(self, backend, classifier, tmp_path):
        store, api = backend
        assert _preflight(store, api, classifier) is None

        manifest = commit(
            classifier=classifier,
            handoff_dir=_mount_handoff(tmp_path, api, store, classifier),
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
        handoff_dir = _mount_handoff(tmp_path, api, store, classifier)

        first = commit(
            classifier=classifier,
            handoff_dir=handoff_dir,
            target_version="7.1.0",
            store=store,
            configmaps=api,
        )
        second = commit(
            classifier=classifier,
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
            "STATE_MIRROR_CLASSIFIER_DIGEST": classifier.digest(),
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
                classifier=classifier,
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
            classifier=classifier,
            handoff_dir=_mount_handoff(tmp_path, api, store, classifier),
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
        handoff_dir = _mount_handoff(tmp_path, api, store, classifier)
        commit(
            classifier=classifier,
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
                classifier=classifier,
                handoff_dir=handoff_dir,
                target_version="7.1.0",
                store=store,
                configmaps=api,
            )

    def test_live_handoff_conflict_does_not_write_manifest(self, backend, classifier, tmp_path):
        store, api = backend
        _put(store, "ufm:state:a", "7.0.0")
        _preflight(store, api, classifier)
        handoff_dir = _mount_handoff(tmp_path, api, store, classifier)
        api.objs["ufm-upgrade"]["data"]["upgrade.env"] = api.objs["ufm-upgrade"]["data"][
            "upgrade.env"
        ].replace("7.1.0", "7.2.0")

        with pytest.raises(UpgradeError, match="live handoff ConfigMap conflicts"):
            commit(
                classifier=classifier,
                handoff_dir=handoff_dir,
                target_version="7.1.0",
                store=store,
                configmaps=api,
            )
        assert store.get(MANIFEST_KEY) is None

    @pytest.mark.parametrize("field", ["source-gv.cfg", "preserve-paths.txt"])
    def test_live_payload_change_does_not_write_manifest(
        self, backend, classifier, tmp_path, field
    ):
        store, api = backend
        _put(store, "ufm:state:a", "7.0.0")
        _preflight(store, api, classifier)
        handoff_dir = _mount_handoff(tmp_path, api, store, classifier)
        api.objs["ufm-upgrade"]["data"][field] += "changed\n"

        with pytest.raises(UpgradeError, match="payload conflicts"):
            commit(
                classifier=classifier,
                handoff_dir=handoff_dir,
                target_version="7.1.0",
                store=store,
                configmaps=api,
            )
        assert store.get(MANIFEST_KEY) is None

    def test_committed_handoff_without_manifest_fails_preflight(self, backend, classifier):
        store, api = backend
        _preflight(store, api, classifier)
        env = api.objs["ufm-upgrade"]["data"]["upgrade.env"]
        api.objs["ufm-upgrade"]["data"] = {
            "upgrade.env": env.replace("MODE=fresh", "MODE=committed")
        }
        with pytest.raises(UpgradeError, match="no durable upgrade manifest"):
            _preflight(store, api, classifier)

    def test_committed_handoff_operation_must_match_manifest(self, backend, classifier, tmp_path):
        store, api = backend
        _put(store, "ufm:state:a", "7.0.0")
        _preflight(store, api, classifier)
        commit(
            classifier=classifier,
            handoff_dir=_mount_handoff(tmp_path, api, store, classifier),
            target_version="7.1.0",
            store=store,
            configmaps=api,
        )
        api.objs["ufm-upgrade"]["data"]["upgrade.env"] = api.objs["ufm-upgrade"]["data"][
            "upgrade.env"
        ].replace(OPERATION_ID, "f" * 32)
        with pytest.raises(UpgradeError, match="conflicts with durable upgrade manifest"):
            _preflight(store, api, classifier, target="7.1.0")

    def test_concurrent_manifest_change_is_not_overwritten(self, backend, classifier, tmp_path):
        store, api = backend
        _put(store, "ufm:state:a", "7.0.0")
        _preflight(store, api, classifier)
        handoff_dir = _mount_handoff(tmp_path, api, store, classifier)
        competing = UpgradeManifest(
            source_version="7.0.0",
            target_version="7.0.1",
            operation_id="f" * 32,
            committed_at="2026-09-22T00:00:00Z",
            schema_version=1,
        )
        body = competing.to_bytes()
        meta = wire.build_meta(body, "upgrade_manifest", "7.0.1", "test")
        if isinstance(store, RedisStore):
            store._client.before_eval = lambda client: wire.write_pair(
                client, MANIFEST_KEY, body, meta
            )
        else:
            api.before_cas = lambda cm_api: ConfigMapStore(cm_api).put(MANIFEST_KEY, body, meta)

        with pytest.raises(UpgradeError, match="changed during commit"):
            commit(
                classifier=classifier,
                handoff_dir=handoff_dir,
                target_version="7.1.0",
                store=store,
                configmaps=api,
            )
        assert load_manifest(store) == competing
        assert _env(api)["STATE_MIRROR_UPGRADE_MODE"] == "upgrade"

    def test_handoff_change_after_validation_is_not_overwritten(
        self, fake_redis, classifier, tmp_path
    ):
        store = RedisStore(fake_redis)
        api = FakeConfigMaps()
        _put(store, "ufm:state:a", "7.0.0")
        _preflight(store, api, classifier)
        handoff_dir = _mount_handoff(tmp_path, api, store, classifier)

        def competing_handoff(cm_api):
            current = cm_api.objs["ufm-upgrade"]
            cm_api.write_cm(
                "ufm-upgrade",
                labels=current["labels"],
                annotations={},
                data={
                    "upgrade.env": current["data"]["upgrade.env"].replace(OPERATION_ID, "f" * 32)
                },
                binary_data={},
            )

        api.before_cas = competing_handoff
        with pytest.raises(UpgradeError, match="handoff ConfigMap changed during commit"):
            commit(
                classifier=classifier,
                handoff_dir=handoff_dir,
                target_version="7.1.0",
                store=store,
                configmaps=api,
            )
        assert load_manifest(store).operation_id == OPERATION_ID
        assert _env(api)["STATE_MIRROR_OPERATION_ID"] == "f" * 32


def test_redis_manifest_cas_detects_metadata_only_change(fake_redis):
    store = RedisStore(fake_redis)
    old_body = b"old"
    old_meta = wire.build_meta(old_body, "upgrade_manifest", "7.0.0", "test")
    store.put(MANIFEST_KEY, old_body, old_meta)
    fake_redis.before_eval = lambda client: client.store.__setitem__(
        wire.meta_key(MANIFEST_KEY), b"changed-meta"
    )
    new_body = b"new"
    new_meta = wire.build_meta(new_body, "upgrade_manifest", "7.1.0", "test")

    assert not store.put_if_unchanged(MANIFEST_KEY, (old_body, old_meta), new_body, new_meta)
    assert fake_redis.store[MANIFEST_KEY] == old_body
    assert fake_redis.store[wire.meta_key(MANIFEST_KEY)] == b"changed-meta"


class TestConsumerInspection:
    def inspect(self, store, api, classifier):
        from state_mirror.upgrade import inspect_handoff

        return inspect_handoff(
            classifier=classifier,
            target_version="7.1.0",
            handoff_configmap="ufm-upgrade",
            store=store,
            configmaps=api,
        )

    def test_inspection_is_read_only_and_checkpoint_is_explicit(self, backend, classifier):
        store, api = backend
        _put(store, "ufm:state:a", "7.0.0")
        _preflight(store, api, classifier)
        before = copy.deepcopy(api.objs)
        assert self.inspect(store, api, classifier)["checkpoint_acknowledged"] is False
        assert api.objs == before
        view = FencedStore(store, "", classifier.digest(), "7.0.0")
        mirror = Mirror(classifier, view, "7.0.0", "test")
        final_checkpoint(
            mirror,
            classifier,
            api,
            {
                "quiesced": True,
                "operation_id": OPERATION_ID,
                "target_version": "7.1.0",
                "digest": classifier.digest(),
            },
        )
        assert self.inspect(store, api, classifier)["checkpoint_acknowledged"] is True

    def test_lost_commit_response_can_be_normalized_without_mutation(
        self, backend, classifier, tmp_path, monkeypatch
    ):
        store, api = backend
        _put(store, "ufm:state:a", "7.0.0")
        _preflight(store, api, classifier)
        mounted = _mount_handoff(tmp_path, api, store, classifier)
        real_cas = api.write_cm_cas
        monkeypatch.setattr(
            api,
            "write_cm_cas",
            lambda name, **kw: False if name == "ufm-upgrade" else real_cas(name, **kw),
        )
        with pytest.raises(UpgradeError, match="changed during commit"):
            commit(
                classifier=classifier,
                handoff_dir=mounted,
                target_version="7.1.0",
                store=store,
                configmaps=api,
            )
        before = copy.deepcopy(api.objs)
        result = self.inspect(store, api, classifier)
        assert result["mode"] == "committed"
        assert api.objs == before
        normalized = tmp_path / "normalized"
        normalized.mkdir()
        for name, value in result["handoff"].items():
            (normalized / name).write_text(value)
        monkeypatch.setattr(api, "write_cm_cas", real_cas)
        committed = commit(
            classifier=classifier,
            handoff_dir=str(normalized),
            target_version="7.1.0",
            store=store,
            configmaps=api,
        )
        assert committed.generation == result["generation"]
        assert _env(api)["STATE_MIRROR_UPGRADE_MODE"] == "committed"

    def test_same_release_operation_requires_its_own_checkpoint(
        self, backend, classifier, tmp_path
    ):
        store, api = backend
        _preflight(store, api, classifier)
        manifest = commit(
            classifier=classifier,
            handoff_dir=_mount_handoff(tmp_path, api, store, classifier),
            target_version="7.1.0",
            store=store,
            configmaps=api,
        )
        api.source_gv()
        transaction = preflight(
            classifier=classifier,
            target_version="7.1.0",
            handoff_configmap="ufm-upgrade",
            source_gv_configmap="ufm-gv-cfg",
            source_gv_key="gv.cfg",
            store=store,
            configmaps=api,
            operation_id="b" * 32,
            checkpoint_required=True,
            source_pod_uid="source-uid",
        )
        assert transaction.operation_id == "b" * 32
        assert self.inspect(store, api, classifier)["checkpoint_acknowledged"] is False
        assert _env(api)["STATE_MIRROR_UPGRADE_MODE"] == "upgrade"
        assert load_manifest(store) == manifest

    def test_source_uid_cannot_change_during_active_operation(self, backend, classifier):
        store, api = backend
        _put(store, "ufm:state:a", "7.0.0")
        api.source_gv()
        arguments = dict(
            classifier=classifier,
            target_version="7.1.0",
            handoff_configmap="ufm-upgrade",
            source_gv_configmap="ufm-gv-cfg",
            source_gv_key="gv.cfg",
            store=store,
            configmaps=api,
            operation_id=OPERATION_ID,
            checkpoint_required=True,
        )
        preflight(**arguments, source_pod_uid="original")
        with pytest.raises(UpgradeError, match="source pod UID conflicts"):
            preflight(**arguments, source_pod_uid="replacement")

    def test_replaced_source_cannot_acknowledge_checkpoint(self, backend, classifier, monkeypatch):
        from state_mirror.upgrade_contract import SOURCE_UID_ANNOTATION

        store, api = backend
        _put(store, "ufm:state:a", "7.0.0")
        _preflight(store, api, classifier)
        api.objs["ufm-upgrade"]["annotations"][SOURCE_UID_ANNOTATION] = "original"
        monkeypatch.setenv("STATE_MIRROR_POD_UID", "replacement")
        mirror = Mirror(
            classifier, FencedStore(store, "", classifier.digest(), "7.0.0"), "7.0.0", "test"
        )
        with pytest.raises(UpgradeError, match="source pod UID conflicts"):
            final_checkpoint(
                mirror,
                classifier,
                api,
                {
                    "quiesced": True,
                    "operation_id": OPERATION_ID,
                    "target_version": "7.1.0",
                    "digest": classifier.digest(),
                },
            )

    def test_capabilities_and_inspection_are_actual_cli_commands(
        self, backend, classifier, monkeypatch, capsys
    ):
        import json

        from state_mirror import upgrade

        store, api = backend
        _preflight(store, api, classifier)
        monkeypatch.setenv("UFM_RELEASE_VERSION", "7.1.0")
        monkeypatch.setattr(upgrade.Classifier, "load_file", lambda path: classifier)
        monkeypatch.setattr(upgrade, "_runtime", lambda namespace: (store, api))
        assert upgrade.main(["capabilities"]) == 0
        assert "live_handoff_inspection" in json.loads(capsys.readouterr().out)["capabilities"]
        assert upgrade.main(["inspect", "--handoff-configmap", "ufm-upgrade"]) == 0
        assert json.loads(capsys.readouterr().out)["mode"] == "fresh"


class TestRuntimeGenerationPin:
    @pytest.mark.parametrize("pin", ["f" * 32, "", "not-a-generation"])
    def test_restarted_mirror_cannot_switch_generation_before_writing(
        self, backend, classifier, tmp_path, monkeypatch, pin
    ):
        from unittest.mock import Mock

        from state_mirror import generation, mirror

        store, api = backend
        _preflight(store, api, classifier)
        commit(
            classifier=classifier,
            handoff_dir=_mount_handoff(tmp_path, api, store, classifier),
            target_version="7.1.0",
            store=store,
            configmaps=api,
        )
        source_pin = tmp_path / "source-generation"
        source_pin.write_text(pin)
        monkeypatch.setenv("STATE_MIRROR_GENERATION_FILE", str(source_pin))
        monkeypatch.setenv("UFM_RELEASE_VERSION", "7.1.0")
        monkeypatch.setattr(mirror.Classifier, "load_file", lambda path: classifier)
        monkeypatch.setattr("state_mirror.backends.build_store", lambda backend: store)
        monkeypatch.setattr(mirror, "HealthServer", Mock())
        writer = Mock()
        monkeypatch.setattr(generation, "FencedStore", writer)
        before = copy.deepcopy(api.objs)
        assert mirror.main() == 1
        writer.assert_not_called()
        assert api.objs == before

    def test_current_pod_pin_matches_authority(self, backend, classifier, tmp_path, monkeypatch):
        from state_mirror.generation import validate_runtime_generation

        store, api = backend
        _preflight(store, api, classifier)
        manifest = commit(
            classifier=classifier,
            handoff_dir=_mount_handoff(tmp_path, api, store, classifier),
            target_version="7.1.0",
            store=store,
            configmaps=api,
        )
        pin = tmp_path / "generation"
        pin.write_text(manifest.generation)
        monkeypatch.setenv("STATE_MIRROR_GENERATION_FILE", str(pin))
        validate_runtime_generation(manifest)


class TestSourceUIDAdoption:
    def test_new_committed_operation_can_bind_a_replacement_source(
        self, backend, classifier, tmp_path
    ):
        from state_mirror.upgrade_contract import SOURCE_UID_ANNOTATION

        store, api = backend
        _preflight(store, api, classifier)
        commit(
            classifier=classifier,
            handoff_dir=_mount_handoff(tmp_path, api, store, classifier),
            target_version="7.1.0",
            store=store,
            configmaps=api,
        )
        api.objs["ufm-upgrade"]["annotations"][SOURCE_UID_ANNOTATION] = "previous-source"
        api.source_gv()
        preflight(
            classifier=classifier,
            target_version="7.2.0",
            handoff_configmap="ufm-upgrade",
            source_gv_configmap="ufm-gv-cfg",
            source_gv_key="gv.cfg",
            store=store,
            configmaps=api,
            operation_id="b" * 32,
            checkpoint_required=True,
            source_pod_uid="new-source",
        )
        assert api.objs["ufm-upgrade"]["annotations"][SOURCE_UID_ANNOTATION] == "new-source"

    def test_schema_one_handoff_can_be_adopted_with_source_uid(self, backend, classifier):
        store, api = backend
        previous = UpgradeManifest(
            source_version="6.9.0",
            target_version="7.0.0",
            operation_id="a" * 32,
            committed_at="2026-10-20T12:00:00Z",
            schema_version=1,
        )
        body = previous.to_bytes()
        store.put(MANIFEST_KEY, body, wire.build_meta(body, "upgrade_manifest", "7.0.0", "old"))
        api.write_cm(
            "ufm-upgrade",
            labels={HANDOFF_LABEL: HANDOFF_LABEL_VALUE},
            annotations={},
            data={
                "upgrade.env": "STATE_MIRROR_UPGRADE_MODE=committed\n"
                "STATE_MIRROR_TARGET_VERSION=7.0.0\n"
                f"STATE_MIRROR_OPERATION_ID={'a' * 32}\n"
            },
            binary_data={},
        )
        api.source_gv()
        transaction = preflight(
            classifier=classifier,
            target_version="7.1.0",
            handoff_configmap="ufm-upgrade",
            source_gv_configmap="ufm-gv-cfg",
            source_gv_key="gv.cfg",
            store=store,
            configmaps=api,
            operation_id=OPERATION_ID,
            checkpoint_required=True,
            source_pod_uid="source",
        )
        assert transaction.operation_id == OPERATION_ID
