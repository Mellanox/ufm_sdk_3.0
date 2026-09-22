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
handoff ConfigMap.  ``commit`` runs only after UFM's migration and records the
new version in the durable backend before marking the handoff committed.

The order is intentional: a failure after the manifest write is retryable, but
a handoff must never say ``committed`` before the durable manifest exists.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import re
import sys
import uuid
from dataclasses import dataclass
from typing import Optional, Protocol

from state_mirror import wire
from state_mirror.backends import Backend, backend_from_env, build_store
from state_mirror.classifier import Classifier, Entry
from state_mirror.k8s_client import K8sConfigMapApi, detect_namespace
from state_mirror.logconfig import setup_logging
from state_mirror.store import Store

log = logging.getLogger(__name__)

FILES_ROOT = "/opt/ufm/files"
HELM_OWNED_PATHS = (
    f"{FILES_ROOT}/conf/gv.cfg",
    f"{FILES_ROOT}/ufm_version",
    f"{FILES_ROOT}/.helm_config_checksum",
)

MANIFEST_KEY = "state-mirror:upgrade-manifest"
MANIFEST_SCHEMA_VERSION = 1
MANIFEST_HANDLER = "upgrade_manifest"
HANDOFF_LABEL = "state-mirror.nvidia.com/upgrade-handoff"
HANDOFF_LABEL_VALUE = "true"
HANDOFF_SELECTOR = f"{HANDOFF_LABEL}={HANDOFF_LABEL_VALUE}"
HANDOFF_DIR_ENV = "STATE_MIRROR_UPGRADE_HANDOFF_DIR"
DEFAULT_HANDOFF_DIR = "/var/run/state-mirror-upgrade"
TARGET_VERSION_ENV = "STATE_MIRROR_TARGET_VERSION"

_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)*(?:[-+][0-9A-Za-z][0-9A-Za-z.-]*)?$")
_OPERATION_ID_RE = re.compile(r"^[0-9a-f]{32}$")


class UpgradeError(RuntimeError):
    """An unsafe or inconsistent upgrade state was detected."""


class ConfigMapApi(Protocol):
    def read_cm(self, name: str) -> Optional[dict]: ...

    def write_cm(
        self,
        name: str,
        *,
        labels: dict[str, str],
        annotations: dict[str, str],
        data: dict[str, str],
        binary_data: dict[str, str],
    ) -> None: ...

    def list_cms(self, label_selector: str) -> list[dict]: ...


@dataclass(frozen=True)
class UpgradeManifest:
    source_version: str
    target_version: str
    operation_id: str
    committed_at: str
    schema_version: int = MANIFEST_SCHEMA_VERSION

    def to_bytes(self) -> bytes:
        return json.dumps(
            {
                "schema_version": self.schema_version,
                "source_version": self.source_version,
                "target_version": self.target_version,
                "operation_id": self.operation_id,
                "committed_at": self.committed_at,
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    @staticmethod
    def from_bytes(raw: bytes) -> "UpgradeManifest":
        try:
            data = json.loads(raw)
            manifest = UpgradeManifest(
                schema_version=int(data["schema_version"]),
                source_version=_validated_version(data["source_version"], "manifest source"),
                target_version=_validated_version(data["target_version"], "manifest target"),
                operation_id=_validated_operation_id(data["operation_id"]),
                committed_at=str(data["committed_at"]),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise UpgradeError(f"durable upgrade manifest is corrupt: {exc}") from exc
        if manifest.schema_version != MANIFEST_SCHEMA_VERSION:
            raise UpgradeError(
                "unsupported durable upgrade manifest schema "
                f"{manifest.schema_version} (expected {MANIFEST_SCHEMA_VERSION})"
            )
        if compare_versions(manifest.source_version, manifest.target_version) > 0:
            raise UpgradeError("durable upgrade manifest records a downgrade")
        return manifest


@dataclass(frozen=True)
class UpgradeTransaction:
    source_version: str
    target_version: str
    operation_id: str


def _utcnow_iso() -> str:
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _validated_version(value: object, description: str) -> str:
    if not isinstance(value, str) or not _VERSION_RE.fullmatch(value.strip()):
        raise UpgradeError(f"{description} version is missing or invalid: {value!r}")
    return value.strip()


def _validated_operation_id(value: object) -> str:
    if not isinstance(value, str) or not _OPERATION_ID_RE.fullmatch(value):
        raise UpgradeError(f"invalid StateMirror operation ID: {value!r}")
    return value


def _version_parts(value: str) -> tuple[tuple[int, ...], Optional[str]]:
    value = _validated_version(value, "UFM")
    release, sep, suffix = value.partition("-")
    if not sep:
        release, _plus, suffix = value.partition("+")
        suffix = None  # build metadata does not affect ordering
    parts = tuple(int(part) for part in release.split("."))
    while len(parts) > 1 and parts[-1] == 0:
        parts = parts[:-1]
    return parts, suffix or None


def compare_versions(left: str, right: str) -> int:
    """Compare strict numeric UFM versions, with a suffix treated as pre-release."""
    left_release, left_suffix = _version_parts(left)
    right_release, right_suffix = _version_parts(right)
    width = max(len(left_release), len(right_release))
    left_release += (0,) * (width - len(left_release))
    right_release += (0,) * (width - len(right_release))
    if left_release != right_release:
        return -1 if left_release < right_release else 1
    if left_suffix == right_suffix:
        return 0
    if left_suffix is None:
        return 1
    if right_suffix is None:
        return -1
    left_tokens = tuple(_natural_tokens(left_suffix))
    right_tokens = tuple(_natural_tokens(right_suffix))
    if left_tokens != right_tokens:
        return -1 if left_tokens < right_tokens else 1
    left_normalized = left_suffix.lower()
    right_normalized = right_suffix.lower()
    if left_normalized == right_normalized:
        return 0
    return -1 if left_normalized < right_normalized else 1


def _natural_tokens(value: str):
    for token in re.findall(r"[0-9]+|[A-Za-z]+", value.lower()):
        yield (0, int(token)) if token.isdigit() else (1, token)


def preserve_paths(classifier: Classifier) -> list[str]:
    """Return canonical classifier paths relative to ``/opt/ufm/files``."""
    root = os.path.realpath(FILES_ROOT)
    paths: set[str] = set()
    for entry in classifier.entries:
        path = os.path.realpath(entry.path)
        try:
            relative = os.path.relpath(path, root)
        except ValueError as exc:
            raise UpgradeError(f"classifier path is outside {FILES_ROOT}: {entry.path}") from exc
        if relative in (".", "..") or relative.startswith(".." + os.sep):
            raise UpgradeError(f"classifier path is outside {FILES_ROOT}: {entry.path}")
        paths.add(relative.replace(os.sep, "/"))
    return sorted(paths)


def validate_path_ownership(classifier: Classifier) -> None:
    """Reject classifier entries that can own files controlled by Helm/UFM."""
    conflicts: list[str] = []
    for entry in classifier.entries:
        for owned in HELM_OWNED_PATHS:
            if _entry_owns_path(entry, owned):
                conflicts.append(f"{entry.path} overlaps Helm-owned {owned}")
        key = entry.redis_key_prefix if entry.is_directory else entry.redis_key
        assert key is not None
        reserved = (MANIFEST_KEY, wire.meta_key(MANIFEST_KEY))
        if (
            entry.is_directory
            and any(key.startswith(item) or item.startswith(key) for item in reserved)
        ) or (not entry.is_directory and key in reserved):
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


def load_manifest(store: Store) -> Optional[UpgradeManifest]:
    result = store.get(MANIFEST_KEY)
    if result is None:
        return None
    body, meta = result
    if meta.handler != MANIFEST_HANDLER:
        raise UpgradeError(f"durable upgrade manifest has unexpected handler {meta.handler!r}")
    manifest = UpgradeManifest.from_bytes(body)
    if meta.ufm_version != manifest.target_version:
        raise UpgradeError("durable upgrade manifest metadata version is inconsistent")
    return manifest


def _entry_store_keys(store: Store, entry: Entry) -> set[str]:
    key = entry.redis_key_prefix if entry.is_directory else entry.redis_key
    assert key is not None
    raw_keys = set(store.list_keys(key))
    if entry.is_directory:
        return {
            candidate[: -len(wire.META_SUFFIX)]
            if candidate.endswith(wire.META_SUFFIX)
            else candidate
            for candidate in raw_keys
            if candidate != MANIFEST_KEY and candidate != wire.meta_key(MANIFEST_KEY)
        }
    if key in raw_keys or wire.meta_key(key) in raw_keys:
        return {key}
    return set()


def resolve_legacy_source_version(store: Store, classifier: Classifier) -> Optional[str]:
    """Resolve exactly one version from verified legacy classifier objects.

    Missing optional classifier objects are valid.  Any object which is present
    must have a valid body/metadata pair, and every present object must agree on
    its UFM version.  No objects means this is genuinely fresh durable state.
    """
    versions: set[str] = set()
    found = False
    for entry in classifier.entries:
        for key in sorted(_entry_store_keys(store, entry)):
            found = True
            result = store.get(key)
            if result is None:
                raise UpgradeError(f"persisted object {key!r} is missing metadata")
            _body, meta = result
            versions.add(_validated_version(meta.ufm_version, f"persisted object {key!r}"))
    if not found:
        return None
    if len(versions) != 1:
        raise UpgradeError("inconsistent source-version metadata: " + ", ".join(sorted(versions)))
    return next(iter(versions))


def _parse_env(raw: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, line in enumerate(raw.splitlines(), 1):
        if not line:
            continue
        if "=" not in line:
            raise UpgradeError(f"invalid upgrade.env line {number}")
        key, value = line.split("=", 1)
        if not key or key in values or not re.fullmatch(r"[A-Z0-9_]+", key):
            raise UpgradeError(f"invalid or duplicate upgrade.env key on line {number}")
        values[key] = value
    return values


def _upgrade_env(transaction: UpgradeTransaction, mode: str = "upgrade") -> str:
    lines = [f"STATE_MIRROR_UPGRADE_MODE={mode}"]
    if mode == "upgrade":
        lines.append(f"STATE_MIRROR_SOURCE_VERSION={transaction.source_version}")
    lines.extend(
        [
            f"STATE_MIRROR_TARGET_VERSION={transaction.target_version}",
            f"STATE_MIRROR_OPERATION_ID={transaction.operation_id}",
        ]
    )
    return "\n".join(lines) + "\n"


def _fresh_env(target_version: str, operation_id: str) -> str:
    return (
        "STATE_MIRROR_UPGRADE_MODE=fresh\n"
        f"STATE_MIRROR_TARGET_VERSION={target_version}\n"
        f"STATE_MIRROR_OPERATION_ID={operation_id}\n"
    )


def _read_source_gv(api: ConfigMapApi, name: str, key: str) -> str:
    cm = api.read_cm(name)
    if cm is None:
        raise UpgradeError(f"source gv.cfg ConfigMap {name!r} does not exist")
    value = (cm.get("data") or {}).get(key)
    if not isinstance(value, str):
        raise UpgradeError(f"source ConfigMap {name!r} is missing text key {key!r}")
    return value


def _write_handoff(api: ConfigMapApi, name: str, data: dict[str, str]) -> None:
    api.write_cm(
        name,
        labels={HANDOFF_LABEL: HANDOFF_LABEL_VALUE},
        annotations={},
        data=data,
        binary_data={},
    )


def _transaction_for_preflight(
    api: ConfigMapApi,
    handoff_name: str,
    source_version: str,
    target_version: str,
    requested_operation_id: Optional[str],
) -> UpgradeTransaction:
    """Reuse a retry of the same preflight and reject an in-flight conflict."""
    existing = api.read_cm(handoff_name)
    if existing is not None:
        raw = (existing.get("data") or {}).get("upgrade.env")
        if isinstance(raw, str):
            values = _parse_env(raw)
            if values.get("STATE_MIRROR_UPGRADE_MODE") == "upgrade":
                identity = (
                    values.get("STATE_MIRROR_SOURCE_VERSION"),
                    values.get("STATE_MIRROR_TARGET_VERSION"),
                )
                requested = (source_version, target_version)
                if identity != requested:
                    raise UpgradeError(
                        "existing handoff conflicts with requested transaction: "
                        f"stored={identity!r}, requested={requested!r}"
                    )
                operation_id = _validated_operation_id(values.get("STATE_MIRROR_OPERATION_ID"))
                if requested_operation_id is not None and requested_operation_id != operation_id:
                    raise UpgradeError("requested operation ID conflicts with existing handoff")
                return UpgradeTransaction(source_version, target_version, operation_id)
    return UpgradeTransaction(
        source_version=source_version,
        target_version=target_version,
        operation_id=_validated_operation_id(requested_operation_id or uuid.uuid4().hex),
    )


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
    store.probe()
    validate_path_ownership(classifier)
    paths = preserve_paths(classifier)

    manifest = load_manifest(store)
    source_version = (
        manifest.target_version
        if manifest is not None
        else resolve_legacy_source_version(store, classifier)
    )
    if source_version is None:
        fresh_operation = _validated_operation_id(operation_id or uuid.uuid4().hex)
        _write_handoff(
            configmaps,
            handoff_configmap,
            {"upgrade.env": _fresh_env(target_version, fresh_operation)},
        )
        log.info("fresh durable state: no upgrade transaction required")
        return None

    comparison = compare_versions(target_version, source_version)
    if comparison < 0:
        raise UpgradeError(
            "downgrade refused: durable source "
            f"{source_version} is newer than target {target_version}"
        )
    if comparison == 0:
        if target_version != source_version:
            raise UpgradeError(
                "target/source version conflict: versions compare equal but are not identical "
                f"({source_version!r} != {target_version!r})"
            )
        operation = manifest.operation_id if manifest is not None else uuid.uuid4().hex
        transaction = UpgradeTransaction(source_version, target_version, operation)
        if manifest is None:
            # A same-version Helm change needs no UFM migration, but it still
            # needs durable authority so the committed handoff remains valid
            # across pod restarts.
            manifest = UpgradeManifest(
                source_version=source_version,
                target_version=target_version,
                operation_id=operation,
                committed_at=_utcnow_iso(),
            )
            body = manifest.to_bytes()
            meta = wire.build_meta(body, MANIFEST_HANDLER, target_version, "state-mirror:upgrade")
            store.put(MANIFEST_KEY, body, meta)
        _write_handoff(
            configmaps,
            handoff_configmap,
            {"upgrade.env": _upgrade_env(transaction, mode="committed")},
        )
        log.info(
            "target %s already matches durable state; migration will not replay", target_version
        )
        return None

    transaction = _transaction_for_preflight(
        configmaps,
        handoff_configmap,
        source_version,
        target_version,
        operation_id,
    )
    source_gv = _read_source_gv(configmaps, source_gv_configmap, source_gv_key)
    _write_handoff(
        configmaps,
        handoff_configmap,
        {
            "upgrade.env": _upgrade_env(transaction),
            "source-gv.cfg": source_gv,
            "preserve-paths.txt": "".join(f"{path}\n" for path in paths),
        },
    )
    log.info(
        "prepared StateMirror upgrade %s -> %s (%s)",
        source_version,
        target_version,
        transaction.operation_id,
    )
    return transaction


def _read_handoff_dir(path: str) -> tuple[dict[str, str], str]:
    env_path = os.path.join(path, "upgrade.env")
    try:
        with open(env_path, encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        raise UpgradeError(f"cannot read mounted handoff {env_path}: {exc}") from exc
    return _parse_env(raw), raw


def _find_handoff(api: ConfigMapApi, operation_id: str) -> dict:
    matches: list[dict] = []
    for cm in api.list_cms(HANDOFF_SELECTOR):
        raw = (cm.get("data") or {}).get("upgrade.env")
        if not isinstance(raw, str):
            continue
        values = _parse_env(raw)
        if values.get("STATE_MIRROR_OPERATION_ID") == operation_id:
            matches.append(cm)
    if len(matches) != 1:
        raise UpgradeError(
            f"expected one handoff ConfigMap for operation {operation_id}, found {len(matches)}"
        )
    return matches[0]


def _validate_live_handoff(
    handoff: dict,
    *,
    mounted_mode: str,
    source_version: str,
    target_version: str,
    operation_id: str,
    existing: Optional[UpgradeManifest],
) -> None:
    values = _parse_env((handoff.get("data") or {}).get("upgrade.env", ""))
    live_mode = values.get("STATE_MIRROR_UPGRADE_MODE")
    live_target = values.get("STATE_MIRROR_TARGET_VERSION")
    live_operation = values.get("STATE_MIRROR_OPERATION_ID")
    if live_target != target_version or live_operation != operation_id:
        raise UpgradeError("live handoff ConfigMap conflicts with mounted transaction")
    if live_mode == "committed":
        identity = (source_version, target_version, operation_id)
        if (
            existing is None
            or (
                existing.source_version,
                existing.target_version,
                existing.operation_id,
            )
            != identity
        ):
            raise UpgradeError("committed handoff conflicts with durable upgrade manifest")
        return
    if live_mode != mounted_mode:
        raise UpgradeError(
            f"live handoff mode {live_mode!r} conflicts with mounted mode {mounted_mode!r}"
        )
    if live_mode == "upgrade" and values.get("STATE_MIRROR_SOURCE_VERSION") != source_version:
        raise UpgradeError("live handoff source version conflicts with mounted transaction")


def commit(
    *,
    handoff_dir: str,
    target_version: str,
    store: Store,
    configmaps: ConfigMapApi,
) -> UpgradeManifest:
    target_version = _validated_version(target_version, "target")
    values, _raw = _read_handoff_dir(handoff_dir)
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
    existing = load_manifest(store)
    write_manifest = False
    if mode == "committed":
        if existing is None:
            raise UpgradeError("committed handoff has no durable upgrade manifest")
        if existing.target_version != target_version or existing.operation_id != operation_id:
            raise UpgradeError("committed handoff conflicts with durable upgrade manifest")
        source_version = existing.source_version
        manifest = existing
    elif mode == "fresh":
        source_version = target_version
    else:
        source_version = _validated_version(values.get("STATE_MIRROR_SOURCE_VERSION"), "source")
        if compare_versions(source_version, target_version) >= 0:
            raise UpgradeError(
                f"invalid transaction versions: source {source_version}, target {target_version}"
            )

    if mode in ("fresh", "upgrade") and existing is not None:
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
            )
            write_manifest = True
    elif mode in ("fresh", "upgrade"):
        manifest = UpgradeManifest(
            source_version=source_version,
            target_version=target_version,
            operation_id=operation_id,
            committed_at=_utcnow_iso(),
        )
        write_manifest = True

    # Validate the authoritative live object before changing durable state.
    # The mounted ConfigMap can lag an earlier successful API update, so a live
    # committed mode is accepted only when the durable manifest already agrees.
    handoff = _find_handoff(configmaps, operation_id)
    _validate_live_handoff(
        handoff,
        mounted_mode=mode,
        source_version=source_version,
        target_version=target_version,
        operation_id=operation_id,
        existing=existing,
    )

    if write_manifest:
        body = manifest.to_bytes()
        meta = wire.build_meta(body, MANIFEST_HANDLER, target_version, "state-mirror:upgrade")
        store.put(MANIFEST_KEY, body, meta)

    transaction = UpgradeTransaction(source_version, target_version, operation_id)
    _write_handoff(
        configmaps,
        handoff["name"],
        {"upgrade.env": _upgrade_env(transaction, mode="committed")},
    )
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


def _commit_target_from_env() -> str:
    state_mirror_target = os.environ.get(TARGET_VERSION_ENV)
    ufm_target = os.environ.get("UFM_VERSION")
    if state_mirror_target and ufm_target and state_mirror_target != ufm_target:
        raise UpgradeError(
            f"target version conflict: {TARGET_VERSION_ENV}={state_mirror_target!r}, "
            f"UFM_VERSION={ufm_target!r}"
        )
    target = state_mirror_target or ufm_target
    if not target:
        raise UpgradeError(f"{TARGET_VERSION_ENV} or UFM_VERSION must specify the commit target")
    return _validated_version(target, "target")


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
        else:
            namespace = detect_namespace()
            store, api = _runtime(namespace)
            commit(
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
