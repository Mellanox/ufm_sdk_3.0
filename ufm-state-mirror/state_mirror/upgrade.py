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

"""Transactional StateMirror handoff for UFM no-PVC upgrades.

``preflight`` runs while the old UFM pod is still alive.  It proves that the
durable backend is readable, resolves one authoritative source version, and
writes the old Helm-owned ``gv.cfg`` plus the classifier preserve list to a
handoff ConfigMap.  ``commit`` runs only after UFM's migration, captures and verifies an isolated
complete generation, and atomically publishes its pointer and release before
marking the handoff committed.

The order is intentional: a failure after the manifest write is retryable, but
a handoff must never say ``committed`` before the durable manifest exists.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Optional

from state_mirror import wire
from state_mirror.backends import Backend, backend_from_env, build_store
from state_mirror.classifier import Classifier, Entry
from state_mirror.k8s_client import K8sConfigMapApi, detect_namespace
from state_mirror.logconfig import setup_logging
from state_mirror.store import Store
from state_mirror.upgrade_contract import (
    DEFAULT_HANDOFF_DIR,
    FILES_ROOT,
    HANDOFF_DIR_ENV,
    HANDOFF_LABEL,
    HANDOFF_LABEL_VALUE,
    HELM_OWNED_PATHS,
    MANIFEST_HANDLER,
    MANIFEST_KEY,
    TARGET_VERSION_ENV,
    ConfigMapApi,
    UpgradeError,
    UpgradeManifest,
    UpgradeTransaction,
    _utcnow_iso,
    _validated_operation_id,
    _validated_timestamp,
    _validated_version,
    compare_versions,
)
from state_mirror.upgrade_handoff import (
    _find_handoff,
    _read_handoff_dir,
    _read_source_gv,
    _resource_version,
    _upgrade_env,
    _validate_committed_authority,
    _validate_live_handoff,
    _write_preflight_handoff,
)

__all__ = [
    "preflight",
    "commit",
    "load_manifest",
    "UpgradeError",
    "UpgradeManifest",
    "UpgradeTransaction",
]

log = logging.getLogger(__name__)


def preserve_paths(classifier: Classifier) -> list[str]:
    """Return canonical classifier paths relative to ``/opt/ufm/files``."""
    root = os.path.abspath(os.path.normpath(FILES_ROOT))
    paths: set[str] = set()
    for entry in classifier.entries:
        path = os.path.abspath(os.path.normpath(entry.path))
        try:
            relative = os.path.relpath(path, root)
        except ValueError as exc:
            raise UpgradeError(f"classifier path is outside {FILES_ROOT}: {entry.path}") from exc
        if relative in (".", "..") or relative.startswith(".." + os.sep):
            raise UpgradeError(f"classifier path is outside {FILES_ROOT}: {entry.path}")
        paths.add(relative.replace(os.sep, "/"))
    return sorted(paths)


def validate_preservation(classifier: Classifier, data: dict[str, str]) -> None:
    expected = "".join(f"{path}\n" for path in preserve_paths(classifier))
    if data.get("preserve-paths.txt") != expected:
        raise UpgradeError("preservation paths conflict with classifier digest")


def validate_path_ownership(classifier: Classifier) -> None:
    """Reject classifier entries that can own files controlled by Helm/UFM."""
    conflicts: list[str] = []
    for entry in classifier.entries:
        for owned in HELM_OWNED_PATHS:
            if _entry_owns_path(entry, owned):
                conflicts.append(f"{entry.path} overlaps Helm-owned {owned}")
        key = entry.redis_key_prefix if entry.is_directory else entry.redis_key
        assert key is not None
        reserved = (
            MANIFEST_KEY,
            wire.meta_key(MANIFEST_KEY),
            "state-mirror:generation:",
            "state-mirror:fence:",
            "state-mirror:inventory",
        )
        if (
            entry.is_directory
            and any(key.startswith(item) or item.startswith(key) for item in reserved)
        ) or (not entry.is_directory and any(key.startswith(item) for item in reserved)):
            conflicts.append(f"backend key {key!r} overlaps the durable upgrade manifest")
    if conflicts:
        raise UpgradeError("classifier/Helm path ownership conflict: " + "; ".join(conflicts))


def _entry_owns_path(entry: Entry, candidate: str) -> bool:
    entry_path = os.path.realpath(entry.path)
    candidate_path = os.path.realpath(candidate)
    if entry_path == candidate_path:
        return True
    if not entry.is_directory:
        return False
    try:
        relative = os.path.relpath(candidate_path, entry_path)
    except ValueError:
        return False
    if relative == ".." or relative.startswith(".." + os.sep):
        return False
    return entry.recursive or os.sep not in relative


def _load_manifest_record(
    store: Store,
) -> tuple[Optional[UpgradeManifest], Optional[tuple[bytes, wire.Meta]]]:
    result = store.get(MANIFEST_KEY)
    if result is None:
        keys = set(store.list_keys(MANIFEST_KEY))
        if MANIFEST_KEY in keys or wire.meta_key(MANIFEST_KEY) in keys:
            raise UpgradeError("durable upgrade manifest is missing body or metadata")
        return None, None
    body, meta = result
    if meta.handler != MANIFEST_HANDLER:
        raise UpgradeError(f"durable upgrade manifest has unexpected handler {meta.handler!r}")
    manifest = UpgradeManifest.from_bytes(body)
    if meta.ufm_version != manifest.target_version:
        raise UpgradeError("durable upgrade manifest metadata version is inconsistent")
    return manifest, (body, meta)


def load_manifest(store: Store) -> Optional[UpgradeManifest]:
    return _load_manifest_record(store)[0]


def _entry_store_keys(raw_keys: set[str], entry: Entry) -> set[str]:
    key = entry.redis_key_prefix if entry.is_directory else entry.redis_key
    assert key is not None
    if entry.is_directory:
        return {
            candidate[: -len(wire.META_SUFFIX)]
            if candidate.endswith(wire.META_SUFFIX)
            else candidate
            for candidate in raw_keys
            if candidate.startswith(key)
            if candidate != MANIFEST_KEY and candidate != wire.meta_key(MANIFEST_KEY)
        }
    if key in raw_keys or wire.meta_key(key) in raw_keys:
        return {key}
    return set()


def resolve_legacy_source_version(store: Store, classifier: Classifier) -> Optional[str]:
    """Accept legacy metadata only when every verified object agrees exactly.

    Timestamps and maximum versions cannot prove which release owns a dataset.
    A release manifest is authoritative once present; divergent legacy stamps
    require explicit operator recovery before any handoff is prepared.
    """
    candidates: list[tuple[str, str]] = []
    raw_keys = set(store.list_keys(""))
    for entry in classifier.entries:
        for key in sorted(_entry_store_keys(raw_keys, entry)):
            result = store.get(key)
            if result is None:
                raise UpgradeError(f"persisted object {key!r} is missing metadata")
            _body, meta = result
            version = _validated_version(meta.ufm_version, f"persisted object {key!r}")
            stamp = (
                ""
                if meta.written_at is None
                else _validated_timestamp(meta.written_at, f"persisted object {key!r}")
            )
            candidates.append((stamp, version))
    if not candidates:
        return None
    distinct = sorted({version for _stamp, version in candidates})
    if len(distinct) != 1:
        raise UpgradeError("divergent legacy release versions: " + ", ".join(distinct))
    return distinct[0]


def release_authority(store: Store, classifier: Classifier):
    """Resolve install-level authority before restore, preflight or writer startup."""
    manifest = load_manifest(store)
    if manifest is not None:
        if manifest.classifier_digest and manifest.classifier_digest != classifier.digest():
            raise UpgradeError("classifier digest conflicts with durable release")
        return manifest, manifest.target_version
    source = resolve_legacy_source_version(store, classifier)
    import json

    from state_mirror.generation import fence_key, record

    fence = record(store, fence_key(""))
    if fence is not None:
        value = json.loads(fence[0])
        release = _validated_version(value.get("version"), "writer release")
        if source is not None and source != release:
            raise UpgradeError("legacy objects conflict with writer release authority")
        if value.get("digest") != classifier.digest():
            raise UpgradeError("classifier digest conflicts with writer release authority")
        return None, release
    return None, source


def preflight(
    *,
    classifier: Classifier,
    target_version: str,
    handoff_configmap: str,
    source_gv_configmap: str,
    source_gv_key: str,
    store: Store,
    configmaps: ConfigMapApi,
    operation_id: Optional[str] = None,
) -> Optional[UpgradeTransaction]:
    target_version = _validated_version(target_version, "target")
    if handoff_configmap == source_gv_configmap:
        raise UpgradeError("handoff and source gv.cfg ConfigMaps must be different")
    store.probe()
    validate_path_ownership(classifier)
    paths = preserve_paths(classifier)
    classifier_digest = classifier.digest()

    manifest, source_version = release_authority(store, classifier)
    _validate_committed_authority(configmaps, handoff_configmap, manifest)
    if source_version is None:
        _write_preflight_handoff(
            configmaps,
            handoff_name=handoff_configmap,
            mode="fresh",
            source_version="",
            target_version=target_version,
            requested_operation_id=operation_id,
            classifier_digest=classifier_digest,
        )
        log.info("fresh durable state: no upgrade transaction required")
        return None

    comparison = compare_versions(target_version, source_version)
    if comparison < 0:
        raise UpgradeError(
            "downgrade refused: durable source "
            f"{source_version} is newer than target {target_version}"
        )
    if comparison == 0 and target_version != source_version:
        raise UpgradeError("target/source version conflict: equivalent but distinct releases")
    if comparison == 0 and manifest is not None and manifest.schema_version == 2:
        if manifest.classifier_digest != classifier_digest:
            raise UpgradeError("classifier digest conflicts with durable release")
        _write_preflight_handoff(
            configmaps,
            handoff_name=handoff_configmap,
            mode="committed",
            source_version=manifest.source_version,
            target_version=target_version,
            requested_operation_id=manifest.operation_id,
            classifier_digest=classifier_digest,
        )
        return None

    from state_mirror.generation import ensure_fence

    generation = manifest.generation if manifest is not None else ""
    if (
        manifest is not None
        and manifest.classifier_digest
        and manifest.classifier_digest != classifier_digest
    ):
        raise UpgradeError("classifier digest conflicts with durable release")
    ensure_fence(store, generation, classifier_digest, source_version)

    source_gv = _read_source_gv(configmaps, source_gv_configmap, source_gv_key)
    transaction = _write_preflight_handoff(
        configmaps,
        handoff_name=handoff_configmap,
        mode="upgrade",
        source_version=source_version,
        target_version=target_version,
        requested_operation_id=operation_id,
        classifier_digest=classifier_digest,
        source_gv=source_gv,
        paths=paths,
        legacy_manifest=manifest,
    )
    log.info(
        "prepared StateMirror upgrade %s -> %s (%s)",
        source_version,
        target_version,
        transaction.operation_id,
    )
    return transaction


def _candidate_manifest(
    existing, mode, source_version, target_version, operation_id, classifier_digest
):
    if mode == "committed":
        return existing, False
    write_manifest = False
    if existing is not None:
        identity = (existing.source_version, existing.target_version, existing.operation_id)
        requested = (source_version, target_version, operation_id)
        if identity == requested:
            manifest = existing
        elif mode == "fresh" or existing.target_version != source_version:
            raise UpgradeError(
                "durable manifest conflicts with requested transaction: "
                f"stored={identity!r}, requested={requested!r}"
            )
        else:
            manifest = UpgradeManifest(
                source_version=source_version,
                target_version=target_version,
                operation_id=operation_id,
                committed_at=_utcnow_iso(),
                classifier_digest=classifier_digest,
            )
            write_manifest = True
    else:
        manifest = UpgradeManifest(
            source_version=source_version,
            target_version=target_version,
            operation_id=operation_id,
            committed_at=_utcnow_iso(),
            classifier_digest=classifier_digest,
        )
        write_manifest = True

    return manifest, write_manifest


def _publish_manifest(
    manifest, existing, existing_record, mode, classifier, store, configmaps, handoff
):
    classifier_digest = manifest.classifier_digest
    operation_id = manifest.operation_id
    target_version = manifest.target_version
    from dataclasses import replace

    from state_mirror.generation import publish_snapshot, require_checkpoint

    if mode == "upgrade":
        if release_authority(store, classifier)[1] != manifest.source_version:
            raise UpgradeError("commit source release conflicts with durable authority")
        source_generation = existing.generation if existing is not None else ""
        require_checkpoint(
            store, source_generation, classifier_digest, operation_id, target_version
        )
    generation = publish_snapshot(classifier, store, target_version)
    manifest = replace(manifest, generation=generation)
    # Revalidate the handoff after a potentially long capture/readback.
    current_handoff = _find_handoff(configmaps, operation_id)
    if current_handoff != handoff:
        raise UpgradeError("handoff ConfigMap changed during publication")
    body = manifest.to_bytes()
    meta = wire.build_meta(body, MANIFEST_HANDLER, target_version, "state-mirror:upgrade")
    if not store.put_if_unchanged(MANIFEST_KEY, existing_record, body, meta):
        raise UpgradeError("durable upgrade manifest changed during commit")
    return manifest


def commit(
    *,
    classifier: Classifier,
    handoff_dir: str,
    target_version: str,
    store: Store,
    configmaps: ConfigMapApi,
) -> UpgradeManifest:
    target_version = _validated_version(target_version, "target")
    values, mounted_data = _read_handoff_dir(handoff_dir)
    classifier_digest = classifier.digest()
    validate_path_ownership(classifier)
    if values["STATE_MIRROR_CLASSIFIER_DIGEST"] != classifier_digest:
        raise UpgradeError("mounted handoff classifier digest conflicts")
    if values["STATE_MIRROR_UPGRADE_MODE"] == "upgrade":
        validate_preservation(classifier, mounted_data)
    mode = values.get("STATE_MIRROR_UPGRADE_MODE")
    handoff_target = _validated_version(values.get("STATE_MIRROR_TARGET_VERSION"), "handoff target")
    operation_id = _validated_operation_id(values.get("STATE_MIRROR_OPERATION_ID"))
    if handoff_target != target_version:
        raise UpgradeError(
            "target version conflict: handoff has "
            f"{handoff_target}, environment has {target_version}"
        )
    if mode not in ("fresh", "upgrade", "committed"):
        raise UpgradeError(f"handoff is not an upgrade transaction (mode={mode!r})")

    store.probe()
    existing, existing_record = _load_manifest_record(store)
    if mode == "committed":
        if existing is None:
            raise UpgradeError("committed handoff has no durable upgrade manifest")
        if existing.target_version != target_version or existing.operation_id != operation_id:
            raise UpgradeError("committed handoff conflicts with durable upgrade manifest")
        source_version = existing.source_version
        manifest = existing
    elif mode == "fresh":
        if existing is None and release_authority(store, classifier)[1] is not None:
            raise UpgradeError("fresh commit conflicts with existing durable release authority")
        source_version = target_version
    else:
        source_version = _validated_version(values.get("STATE_MIRROR_SOURCE_VERSION"), "source")
        if compare_versions(source_version, target_version) > 0:
            raise UpgradeError(
                f"invalid transaction versions: source {source_version}, target {target_version}"
            )

    manifest, write_manifest = _candidate_manifest(
        existing, mode, source_version, target_version, operation_id, classifier_digest
    )

    # Validate the authoritative live object before changing durable state.
    # The mounted ConfigMap can lag an earlier successful API update, so a live
    # committed mode is accepted only when the durable manifest already agrees.
    handoff = _find_handoff(configmaps, operation_id)
    _validate_live_handoff(
        handoff,
        classifier_digest=classifier_digest,
        mounted_mode=mode,
        source_version=source_version,
        target_version=target_version,
        operation_id=operation_id,
        existing=existing,
        mounted_data=mounted_data,
    )

    if write_manifest:
        manifest = _publish_manifest(
            manifest, existing, existing_record, mode, classifier, store, configmaps, handoff
        )

    if manifest.classifier_digest != classifier_digest:
        raise UpgradeError("durable manifest classifier digest conflicts")
    transaction = UpgradeTransaction(
        source_version, target_version, operation_id, classifier_digest
    )
    if not configmaps.write_cm_cas(
        handoff["name"],
        expected_resource_version=_resource_version(handoff),
        labels={HANDOFF_LABEL: HANDOFF_LABEL_VALUE},
        annotations={},
        data={"upgrade.env": _upgrade_env(transaction, mode="committed")},
        binary_data={},
    ):
        raise UpgradeError("handoff ConfigMap changed during commit")
    log.info("committed StateMirror upgrade to %s (%s)", target_version, operation_id)
    return manifest


def _configmap_api(namespace: str) -> K8sConfigMapApi:
    from kubernetes import client, config

    config.load_incluster_config()
    return K8sConfigMapApi(client.CoreV1Api(), namespace)


def _runtime(namespace: str) -> tuple[Store, ConfigMapApi]:
    api = _configmap_api(namespace)
    backend = backend_from_env()
    if backend is Backend.CONFIGMAP:
        from state_mirror.store import ConfigMapStore

        return ConfigMapStore(api), api
    return build_store(backend), api


def release_version_from_env() -> str:
    """Require an explicitly supplied install/release version from the consumer."""
    target = os.environ.get(TARGET_VERSION_ENV)
    release = os.environ.get("UFM_RELEASE_VERSION")
    if target and release and target != release:
        raise UpgradeError(
            f"target version conflict: {TARGET_VERSION_ENV}={target!r}, "
            f"UFM_RELEASE_VERSION={release!r}"
        )
    # The UFM chart explicitly sets UFM_VERSION from Chart.AppVersion. Accept
    # that existing release input only when no dedicated authority is supplied;
    # never default it to an engine/component version or "unknown".
    authority = target or release or os.environ.get("UFM_VERSION")
    if not authority:
        raise UpgradeError(
            f"{TARGET_VERSION_ENV}, UFM_RELEASE_VERSION or UFM_VERSION must specify the release"
        )
    return _validated_version(authority, "release")


def _commit_target_from_env() -> str:
    return release_version_from_env()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="StateMirror UFM upgrade transaction")
    subparsers = parser.add_subparsers(dest="command", required=True)
    pre = subparsers.add_parser("preflight")
    pre.add_argument("--classifier", required=True)
    pre.add_argument("--target-version", required=True)
    pre.add_argument("--namespace", required=True)
    pre.add_argument("--handoff-configmap", required=True)
    pre.add_argument("--source-gv-configmap", required=True)
    pre.add_argument("--source-gv-key", required=True)
    subparsers.add_parser("commit")
    checkpoint_parser = subparsers.add_parser("checkpoint")
    checkpoint_parser.add_argument("--quiesced", action="store_true", required=True)
    checkpoint_parser.add_argument("--handoff-configmap", required=True)
    checkpoint_parser.add_argument("--timeout", type=float, default=120.0)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    setup_logging("state_mirror.upgrade")
    args = _parser().parse_args(argv)
    try:
        if args.command == "preflight":
            classifier = Classifier.load_file(args.classifier)
            store, api = _runtime(args.namespace)
            preflight(
                classifier=classifier,
                target_version=args.target_version,
                handoff_configmap=args.handoff_configmap,
                source_gv_configmap=args.source_gv_configmap,
                source_gv_key=args.source_gv_key,
                store=store,
                configmaps=api,
            )
        elif args.command == "checkpoint":
            from state_mirror.checkpoint import request_checkpoint

            request_checkpoint(
                _configmap_api(detect_namespace()), args.handoff_configmap, timeout=args.timeout
            )
        else:
            namespace = detect_namespace()
            store, api = _runtime(namespace)
            commit(
                classifier=Classifier.load_file(
                    os.environ.get("CLASSIFIER_PATH", "/etc/state_mirror/state_mirror.yaml")
                ),
                handoff_dir=os.environ.get(HANDOFF_DIR_ENV, DEFAULT_HANDOFF_DIR),
                target_version=_commit_target_from_env(),
                store=store,
                configmaps=api,
            )
    except Exception as exc:
        log.error("StateMirror upgrade %s failed: %s", args.command, exc)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
