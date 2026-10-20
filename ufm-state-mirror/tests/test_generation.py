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

"""Crash/retry and fencing contracts, exercised on both Store implementations."""

import json
import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest
from test_upgrade import OPERATION_ID, _env, _mount_handoff, _preflight, _put, backend, classifier

from state_mirror import wire
from state_mirror.checkpoint import final_checkpoint
from state_mirror.classifier import Classifier
from state_mirror.generation import (
    FENCE_PREFIX,
    GENERATION_PREFIX,
    FencedStore,
    GenerationError,
    GenerationStore,
    fence_key,
    publish_snapshot,
    verify_inventory,
)
from state_mirror.mirror import Mirror
from state_mirror.restore import restore_store, run
from state_mirror.upgrade import MANIFEST_KEY, UpgradeError, commit, load_manifest

# Reuse the Redis and ConfigMap fixtures, including their CAS race injection hooks.
__all__ = ["backend", "classifier"]


def _checkpoint(store, api, classifier, *, quiesced=True):
    values = _env(api)
    manifest = load_manifest(store)
    view = FencedStore(
        store,
        manifest.generation if manifest else "",
        classifier.digest(),
        values["STATE_MIRROR_SOURCE_VERSION"],
    )
    mirror = Mirror(classifier, view, view.version, "test")
    request = {
        "quiesced": quiesced,
        "operation_id": values["STATE_MIRROR_OPERATION_ID"],
        "target_version": values["STATE_MIRROR_TARGET_VERSION"],
        "digest": classifier.digest(),
    }
    return mirror, request


def _prepare(backend, classifier, tmp_path):
    store, api = backend
    _put(store, "ufm:state:a", "7.0.0", b"source")
    _preflight(store, api, classifier)
    handoff = _mount_handoff(tmp_path, api, store, classifier)
    Path(classifier.entries[0].path).write_bytes(b"migrated")
    return store, api, handoff


def _commit(store, api, handoff, classifier):
    return commit(
        classifier=classifier,
        handoff_dir=handoff,
        target_version="7.1.0",
        store=store,
        configmaps=api,
    )


def test_generation_commit_publishes_migrated_bytes_and_preserves_source(
    backend, classifier, tmp_path
):
    store, api, handoff = _prepare(backend, classifier, tmp_path)
    source = store.get("ufm:state:a")
    manifest = _commit(store, api, handoff, classifier)
    active = GenerationStore(store, manifest.generation)
    assert active.get("ufm:state:a")[0] == b"migrated"
    assert store.get("ufm:state:a") == source
    assert manifest.classifier_digest == classifier.digest()
    verify_inventory(active)
    Path(classifier.entries[0].path).unlink()
    assert run(classifier, store, "7.1.0", handoff_dir=handoff) == 1
    assert not Path(classifier.entries[0].path).exists()
    # Simulate the projected ConfigMap catching up before UFM may migrate.
    Path(handoff, "upgrade.env").write_text(api.objs["ufm-upgrade"]["data"]["upgrade.env"])
    assert run(classifier, store, "7.1.0", handoff_dir=handoff) == 0
    assert Path(classifier.entries[0].path).read_bytes() == b"migrated"


@pytest.mark.parametrize(
    "stage", ["first-object", "inventory", "manifest-before", "manifest-after"]
)
def test_interrupted_publication_selects_only_complete_generation(
    backend, classifier, tmp_path, monkeypatch, stage
):
    store, api, handoff = _prepare(backend, classifier, tmp_path)
    put, cas = store.put, store.put_if_unchanged

    def interrupted_put(key, body, meta):
        if key.startswith(GENERATION_PREFIX) and (
            stage == "first-object"
            or (stage == "inventory" and key.endswith("state-mirror:inventory"))
        ):
            put(key, body, meta)
            raise OSError("interrupted publication")
        return put(key, body, meta)

    def interrupted_cas(key, expected, body, meta):
        if key == MANIFEST_KEY and stage.startswith("manifest"):
            if stage == "manifest-after":
                assert cas(key, expected, body, meta)
            raise OSError("interrupted publication")
        return cas(key, expected, body, meta)

    monkeypatch.setattr(store, "put", interrupted_put)
    monkeypatch.setattr(store, "put_if_unchanged", interrupted_cas)
    with pytest.raises(OSError, match="interrupted publication"):
        _commit(store, api, handoff, classifier)
    manifest = load_manifest(store)
    if stage == "manifest-after":
        verify_inventory(GenerationStore(store, manifest.generation))
    else:
        assert manifest is None
        assert store.get("ufm:state:a")[0] == b"state"
    monkeypatch.setattr(store, "put", put)
    monkeypatch.setattr(store, "put_if_unchanged", cas)
    completed = _commit(store, api, handoff, classifier)
    assert completed == load_manifest(store)
    assert GenerationStore(store, completed.generation).get("ufm:state:a")[0] == b"migrated"


def test_readback_corruption_never_commits(backend, classifier, tmp_path, monkeypatch):
    store, api, handoff = _prepare(backend, classifier, tmp_path)
    get = store.get

    def corrupt_read(key):
        result = get(key)
        if key.startswith(GENERATION_PREFIX) and key.endswith("ufm:state:a") and result:
            return result[0], replace(result[1], content_hash="sha256:incorrect")
        return result

    monkeypatch.setattr(store, "get", corrupt_read)
    # The corrupted hash is captured into the inventory too; verify body/meta
    # consistency independently of the backend's contract during readback.
    with pytest.raises((GenerationError, wire.WireError)):
        _commit(store, api, handoff, classifier)
    assert load_manifest(store) is None


def test_checkpoint_requires_quiescence_and_preserves_retry_ack(backend, classifier):
    store, api = backend
    _put(store, "ufm:state:a", "7.0.0")
    _preflight(store, api, classifier)
    mirror, request = _checkpoint(store, api, classifier, quiesced=False)
    with pytest.raises(UpgradeError, match="quiescence"):
        final_checkpoint(mirror, classifier, api, request)
    request["quiesced"] = True
    ack = final_checkpoint(mirror, classifier, api, request)
    assert ack["acknowledged"] is True
    assert final_checkpoint(mirror, classifier, api, request) == ack
    with pytest.raises(GenerationError, match="fenced"):
        mirror.store.put("ufm:state:a", b"late", wire.build_meta(b"late", "blob", "7.0.0", "old"))


def test_checkpoint_blocks_unresolved_deletes_and_drift(backend, classifier):
    store, api = backend
    _put(store, "ufm:state:a", "7.0.0")
    _put(store, "ufm:plugins:lost", "7.0.0")
    _preflight(store, api, classifier)
    mirror, request = _checkpoint(store, api, classifier)
    with pytest.raises(UpgradeError, match="unresolved drift"):
        final_checkpoint(mirror, classifier, api, request)
    assert json.loads(store.get(fence_key(""))[0])["state"] != "frozen"


def test_inflight_and_uncertain_mutation_cannot_be_checkpointed(backend, classifier, monkeypatch):
    store, api = backend
    _put(store, "ufm:state:a", "7.0.0")
    _preflight(store, api, classifier)
    mirror, request = _checkpoint(store, api, classifier)
    put = store.put

    def uncertain_put(key, body, meta):
        put(key, body, meta)
        with pytest.raises(GenerationError, match="in flight"):
            mirror.store.freeze(OPERATION_ID, "7.1.0")
        raise OSError("response lost")

    monkeypatch.setattr(store, "put", uncertain_put)
    with pytest.raises(OSError, match="response lost"):
        mirror.store.put("ufm:state:a", b"new", wire.build_meta(b"new", "blob", "7.0.0", "old"))
    assert json.loads(store.get(fence_key(""))[0])["lock"]
    monkeypatch.setattr(store, "put", put)
    with pytest.raises(UpgradeError, match="final checkpoint"):
        final_checkpoint(mirror, classifier, api, request)
    with pytest.raises(UpgradeError, match="interrupted writer"):
        restore_store(classifier, store, "7.0.0")


def test_restore_and_commit_require_checkpoint(backend, classifier, tmp_path):
    store, api = backend
    _put(store, "ufm:state:a", "7.0.0")
    _preflight(store, api, classifier)
    mount = tmp_path / "unacknowledged"
    mount.mkdir()
    for name, value in api.objs["ufm-upgrade"]["data"].items():
        (mount / name).write_text(value)
    with pytest.raises(GenerationError, match="checkpoint"):
        restore_store(classifier, store, "7.1.0", str(mount))
    with pytest.raises(GenerationError, match="checkpoint"):
        _commit(store, api, str(mount), classifier)
    assert load_manifest(store) is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("rate_limit_ms", 999),
        ("redis_key", "other"),
        ("handler", "atomic_blob"),
        ("baseline", "empty"),
    ],
)
def test_classifier_semantics_bound_to_restore_and_commit(
    backend, classifier, tmp_path, field, value
):
    store, api, handoff = _prepare(backend, classifier, tmp_path)
    changed = Classifier([replace(classifier.entries[0], **{field: value}), classifier.entries[1]])
    with pytest.raises(UpgradeError, match="digest"):
        restore_store(changed, store, "7.1.0", handoff)
    with pytest.raises(UpgradeError, match="digest"):
        _commit(store, api, handoff, changed)
    assert load_manifest(store) is None


def test_digest_is_canonical_and_uses_effective_defaults(classifier):
    reordered = Classifier(list(reversed(classifier.entries)))
    assert reordered.digest() == classifier.digest()
    entry = classifier.entries[0]
    from_dict = Classifier.from_dict(
        {"entries": [{"path": entry.path, "handler": "blob", "redis_key": entry.redis_key}]}
    )
    assert from_dict.digest() == Classifier([entry]).digest()


def test_active_writer_updates_verified_inventory_and_old_writer_stays_fenced(
    backend, classifier, tmp_path
):
    store, api, handoff = _prepare(backend, classifier, tmp_path)
    manifest = _commit(store, api, handoff, classifier)
    active = FencedStore(store, manifest.generation, classifier.digest(), "7.1.0")
    body = b"runtime change"
    active.put("ufm:state:a", body, wire.build_meta(body, "blob", "7.1.0", "new"))
    verify_inventory(active)
    active.delete("ufm:state:a")
    verify_inventory(active)
    old = FencedStore(store, "", classifier.digest(), "7.0.0")
    with pytest.raises(GenerationError, match="fenced"):
        old.delete("ufm:state:a")


def test_sqlite_snapshot_and_directory_fanout_are_complete(backend, classifier, tmp_path):
    store, _api = backend
    db_path = tmp_path / "live.db"
    with sqlite3.connect(db_path) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("CREATE TABLE t (value TEXT)")
        db.execute("INSERT INTO t VALUES ('durable')")
        db.commit()
        db_entry = replace(classifier.entries[0], path=str(db_path), handler="sqlite")
        # Handler is an Enum in the effective classifier.
        from state_mirror.classifier import Handler

        db_entry = replace(db_entry, handler=Handler.SQLITE)
        tree = Path(classifier.entries[1].path)
        (tree / "nested").mkdir()
        (tree / "nested/data").write_bytes(b"directory")
        generation = publish_snapshot(Classifier([db_entry, classifier.entries[1]]), store, "7.1.0")
    staged = GenerationStore(store, generation)
    verify_inventory(staged)
    assert staged.get("ufm:plugins:nested/data")[0] == b"directory"
    restored = tmp_path / "snapshot.db"
    restored.write_bytes(staged.get("ufm:state:a")[0])
    with sqlite3.connect(restored) as db:
        assert db.execute("SELECT value FROM t").fetchone() == ("durable",)


def test_control_namespaces_are_reserved(backend, classifier):
    store, api = backend
    for prefix in (GENERATION_PREFIX, FENCE_PREFIX):
        bad = Classifier([replace(classifier.entries[0], redis_key=prefix + "bad")])
        with pytest.raises(UpgradeError, match="ownership conflict"):
            _preflight(store, api, bad)


def test_fence_cas_metadata_survives_slow_backend_operation(backend, classifier, monkeypatch):
    store, _api = backend
    stamp = ["2026-10-20T12:00:00Z"]
    monkeypatch.setattr(wire, "_utcnow_iso", lambda: stamp[0])
    view = FencedStore(store, "", classifier.digest(), "7.0.0")
    put = store.put

    def slow_put(key, body, meta):
        stamp[0] = "2026-10-20T12:00:10Z"
        put(key, body, meta)

    monkeypatch.setattr(store, "put", slow_put)
    body = b"slow"
    view.put("ufm:state:a", body, wire.build_meta(body, "blob", "7.0.0", "test"))
    assert json.loads(store.get(fence_key(""))[0])["lock"] == ""
    view.freeze(OPERATION_ID, "7.1.0")


@pytest.mark.parametrize("divergent", [False, True])
def test_ordinary_restore_cannot_bypass_legacy_version_authority(backend, classifier, divergent):
    store, _api = backend
    _put(store, "ufm:state:a", "7.0.0")
    if divergent:
        _put(store, "ufm:plugins:tool", "6.9.0")
    with pytest.raises(UpgradeError, match="divergent legacy|release change"):
        restore_store(classifier, store, "7.1.0")


@pytest.mark.parametrize("divergent", [False, True])
def test_writer_startup_cannot_launder_legacy_versions(backend, classifier, monkeypatch, divergent):
    import state_mirror.backends
    import state_mirror.mirror

    store, _api = backend
    _put(store, "ufm:state:a", "7.0.0")
    if divergent:
        _put(store, "ufm:plugins:tool", "6.9.0")
    monkeypatch.setenv("UFM_RELEASE_VERSION", "7.1.0")
    monkeypatch.delenv("STATE_MIRROR_TARGET_VERSION", raising=False)
    monkeypatch.setattr(Classifier, "load_file", lambda _path: classifier)
    monkeypatch.setattr(state_mirror.backends, "build_store", lambda _backend: store)
    monkeypatch.setattr(state_mirror.mirror.HealthServer, "start", lambda _server: True)
    assert state_mirror.mirror.main() == 1
    assert store.get("ufm:state:a")[1].ufm_version == "7.0.0"


def test_runtime_requires_authoritative_release_not_component_version(monkeypatch):
    from state_mirror.upgrade import release_version_from_env

    monkeypatch.delenv("STATE_MIRROR_TARGET_VERSION", raising=False)
    monkeypatch.delenv("UFM_RELEASE_VERSION", raising=False)
    monkeypatch.setenv("UFM_VERSION", "component-build-999")
    with pytest.raises(UpgradeError, match="missing or invalid"):
        release_version_from_env()
    monkeypatch.setenv("UFM_RELEASE_VERSION", "7.1.0")
    assert release_version_from_env() == "7.1.0"


def test_lost_checkpoint_ack_is_retryable_with_a_restarted_sidecar(
    backend, classifier, monkeypatch
):
    store, api = backend
    _put(store, "ufm:state:a", "7.0.0")
    _preflight(store, api, classifier)
    mirror, request = _checkpoint(store, api, classifier)
    cas = store.put_if_unchanged

    def lost_ack(key, expected, body, meta):
        accepted = cas(key, expected, body, meta)
        if key.startswith(FENCE_PREFIX) and json.loads(body)["state"] == "frozen":
            assert accepted
            raise OSError("checkpoint acknowledgement lost")
        return accepted

    monkeypatch.setattr(store, "put_if_unchanged", lost_ack)
    with pytest.raises(OSError, match="acknowledgement lost"):
        final_checkpoint(mirror, classifier, api, request)
    monkeypatch.setattr(store, "put_if_unchanged", cas)
    restarted, retry = _checkpoint(store, api, classifier)
    assert final_checkpoint(restarted, classifier, api, retry)["acknowledged"] is True


def test_resolved_historical_drop_does_not_permanently_block_checkpoint(backend, classifier):
    store, api = backend
    _put(store, "ufm:state:a", "7.0.0")
    _preflight(store, api, classifier)
    mirror, request = _checkpoint(store, api, classifier)
    mirror.state.inc_dropped_events()
    # Full reconciliation proves all current files durable and no unresolved
    # missing objects remain; the historical counter itself is not a veto.
    assert final_checkpoint(mirror, classifier, api, request)["acknowledged"]


def test_second_upgrade_switches_complete_generation(backend, classifier, tmp_path):
    store, api, handoff = _prepare(backend, classifier, tmp_path)
    first = _commit(store, api, handoff, classifier)
    source = GenerationStore(store, first.generation).get("ufm:state:a")
    from state_mirror.upgrade import preflight

    preflight(
        classifier=classifier,
        target_version="7.2.0",
        handoff_configmap="ufm-upgrade",
        source_gv_configmap="ufm-gv-cfg",
        source_gv_key="gv.cfg",
        store=store,
        configmaps=api,
        operation_id="f" * 32,
    )
    second_mount = tmp_path / "second-upgrade"
    second_mount.mkdir()
    second_handoff = _mount_handoff(second_mount, api, store, classifier)
    Path(classifier.entries[0].path).write_bytes(b"second migration")
    second = commit(
        classifier=classifier,
        handoff_dir=second_handoff,
        target_version="7.2.0",
        store=store,
        configmaps=api,
    )
    assert second.generation != first.generation
    assert GenerationStore(store, first.generation).get("ufm:state:a") == source
    assert GenerationStore(store, second.generation).get("ufm:state:a")[0] == b"second migration"


def test_frozen_or_busy_writer_restart_never_becomes_ready(backend, classifier, monkeypatch):
    store, api = backend
    _put(store, "ufm:state:a", "7.0.0")
    _preflight(store, api, classifier)
    mirror, request = _checkpoint(store, api, classifier)
    final_checkpoint(mirror, classifier, api, request)
    restarted, _retry = _checkpoint(store, api, classifier)
    monkeypatch.setattr(
        restarted, "start_watching", lambda: pytest.fail("frozen writer armed watcher")
    )
    assert restarted.startup_once() is False
    assert not restarted.state.is_ready()


def test_large_migrated_sqlite_preserves_source_when_configmap_cannot_publish(
    backend, classifier, tmp_path
):
    from state_mirror.classifier import Handler
    from state_mirror.store import ConfigMapStore

    store, api = backend
    db_path = Path(classifier.entries[0].path)
    db_path.unlink()
    with sqlite3.connect(db_path) as db:
        db.execute("CREATE TABLE t (payload BLOB)")
        db.execute("INSERT INTO t VALUES (?)", (b"small",))
    classifier = Classifier([replace(classifier.entries[0], handler=Handler.SQLITE)])
    body = db_path.read_bytes()
    store.put("ufm:state:a", body, wire.build_meta(body, "sqlite", "7.0.0", "test"))
    _preflight(store, api, classifier)
    handoff = _mount_handoff(tmp_path, api, store, classifier)
    before = store.get("ufm:state:a")
    with sqlite3.connect(db_path) as db:
        db.execute("UPDATE t SET payload=?", (b"x" * (1024 * 1024),))
    if isinstance(store, ConfigMapStore):
        with pytest.raises(wire.WireError, match="exceeds ConfigMap limit"):
            _commit(store, api, handoff, classifier)
        assert load_manifest(store) is None
    else:
        manifest = _commit(store, api, handoff, classifier)
        assert len(GenerationStore(store, manifest.generation).get("ufm:state:a")[0]) > 1024 * 1024
    assert store.get("ufm:state:a") == before


def test_classifier_document_relocation_does_not_change_digest(classifier, tmp_path):
    import yaml

    entry = classifier.entries[0]
    doc = {"entries": [{"path": entry.path, "handler": "blob", "redis_key": entry.redis_key}]}
    first = tmp_path / "first.yaml"
    second = tmp_path / "relocated.yaml"
    first.write_text(yaml.safe_dump(doc))
    second.write_text("# relocated document\n" + yaml.safe_dump(doc, sort_keys=False))
    assert Classifier.load_file(str(first)).digest() == Classifier.load_file(str(second)).digest()


def test_fresh_commit_rechecks_no_legacy_writer_appeared(backend, classifier, tmp_path):
    store, api = backend
    _preflight(store, api, classifier)
    handoff = _mount_handoff(tmp_path, api, store, classifier)
    _put(store, "ufm:state:a", "7.0.0")
    with pytest.raises(UpgradeError, match="fresh commit conflicts"):
        _commit(store, api, handoff, classifier)
    assert load_manifest(store) is None


@pytest.mark.parametrize("target", ["7.0.0", "7.1.0"])
def test_existing_schema1_committed_handoff_is_adopted_with_new_digest(
    backend, classifier, tmp_path, target
):
    from state_mirror.upgrade import UpgradeManifest
    from state_mirror.upgrade_contract import HANDOFF_LABEL, HANDOFF_LABEL_VALUE

    store, api = backend
    _put(store, "ufm:state:a", "7.0.0")
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
    transaction = _preflight(store, api, classifier, target=target)
    assert transaction.classifier_digest == classifier.digest()
    assert transaction.operation_id == OPERATION_ID
    assert _env(api)["STATE_MIRROR_UPGRADE_MODE"] == "upgrade"
    handoff = _mount_handoff(tmp_path, api, store, classifier)
    current = commit(
        classifier=classifier,
        handoff_dir=handoff,
        target_version=target,
        store=store,
        configmaps=api,
    )
    assert current.schema_version == 2
    verify_inventory(GenerationStore(store, current.generation))


@pytest.mark.parametrize("alias", [False, True])
@pytest.mark.parametrize("handler", ["blob", "directory"])
def test_helm_ownership_rejects_symlinked_parents_and_aliases(
    tmp_path, monkeypatch, alias, handler
):
    from state_mirror.upgrade import validate_path_ownership

    real = tmp_path / "real"
    real.mkdir()
    symlink = tmp_path / "link"
    symlink.symlink_to(real, target_is_directory=True)
    owned = symlink / "gv.cfg"
    owned.write_text("helm-owned")
    root = real if alias else symlink
    path = root / "gv.cfg" if handler == "blob" else root
    raw = {"path": str(path), "handler": handler}
    raw["redis_key" if handler == "blob" else "redis_key_prefix"] = "state:"
    classified = Classifier.from_dict({"entries": [raw]})
    monkeypatch.setattr("state_mirror.upgrade.HELM_OWNED_PATHS", (str(owned),))
    with pytest.raises(UpgradeError, match="ownership conflict"):
        validate_path_ownership(classified)


@pytest.mark.parametrize("field", ["STATE_MIRROR_OPERATION_ID", "STATE_MIRROR_TARGET_VERSION"])
def test_legacy_committed_handoff_cannot_override_manifest_authority(backend, classifier, field):
    from state_mirror.upgrade import UpgradeManifest
    from state_mirror.upgrade_contract import HANDOFF_LABEL, HANDOFF_LABEL_VALUE

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
    values = {
        "STATE_MIRROR_UPGRADE_MODE": "committed",
        "STATE_MIRROR_TARGET_VERSION": "7.0.0",
        "STATE_MIRROR_OPERATION_ID": "a" * 32,
    }
    values[field] = "b" * 32 if field == "STATE_MIRROR_OPERATION_ID" else "8.0.0"
    api.write_cm(
        "ufm-upgrade",
        labels={HANDOFF_LABEL: HANDOFF_LABEL_VALUE},
        annotations={},
        data={"upgrade.env": "".join(f"{key}={value}\n" for key, value in values.items())},
        binary_data={},
    )
    before = api.read_cm("ufm-upgrade")
    with pytest.raises(UpgradeError, match="legacy committed handoff conflicts"):
        _preflight(store, api, classifier)
    assert api.read_cm("ufm-upgrade") == before
    assert load_manifest(store) == previous


def test_legacy_handoff_adoption_retries_after_lost_configmap_response(
    backend, classifier, monkeypatch
):
    from state_mirror.upgrade import UpgradeManifest
    from state_mirror.upgrade_contract import HANDOFF_LABEL, HANDOFF_LABEL_VALUE

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
    cas = api.write_cm_cas

    def lost_response(name, **kwargs):
        accepted = cas(name, **kwargs)
        if name == "ufm-upgrade":
            assert accepted
            raise OSError("adoption response lost")
        return accepted

    monkeypatch.setattr(api, "write_cm_cas", lost_response)
    with pytest.raises(OSError, match="adoption response lost"):
        _preflight(store, api, classifier)
    monkeypatch.setattr(api, "write_cm_cas", cas)
    retry = _preflight(store, api, classifier)
    assert retry.operation_id == OPERATION_ID
    assert retry.classifier_digest == classifier.digest()
    assert load_manifest(store) == previous
