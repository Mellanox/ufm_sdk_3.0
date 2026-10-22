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

"""ConfigMap handoff preparation and mounted/live transaction validation."""

from __future__ import annotations

import base64
import os
import re
import uuid
from typing import Optional

from state_mirror.upgrade_contract import (
    HANDOFF_LABEL,
    HANDOFF_LABEL_VALUE,
    HANDOFF_SELECTOR,
    ConfigMapApi,
    UpgradeError,
    UpgradeManifest,
    UpgradeTransaction,
    _validated_digest,
    _validated_operation_id,
    _validated_version,
)


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


def _validate_handoff_payload(data: object) -> dict[str, str]:
    if not isinstance(data, dict):
        raise UpgradeError("handoff ConfigMap data is missing or invalid")
    raw = data.get("upgrade.env")
    if not isinstance(raw, str):
        raise UpgradeError("handoff ConfigMap is missing text key 'upgrade.env'")
    values = _parse_env(raw)
    mode = values.get("STATE_MIRROR_UPGRADE_MODE")
    common = {
        "STATE_MIRROR_UPGRADE_MODE",
        "STATE_MIRROR_TARGET_VERSION",
        "STATE_MIRROR_OPERATION_ID",
        "STATE_MIRROR_CLASSIFIER_DIGEST",
    }
    if mode == "upgrade":
        expected_env = common | {"STATE_MIRROR_SOURCE_VERSION"}
        expected_files = {"upgrade.env", "source-gv.cfg", "preserve-paths.txt"}
    elif mode in ("fresh", "committed"):
        expected_env = common
        expected_files = {"upgrade.env"}
    else:
        raise UpgradeError(f"handoff ConfigMap has unsupported mode {mode!r}")
    if set(values) != expected_env:
        raise UpgradeError(f"handoff {mode} environment keys are invalid: {sorted(values)!r}")
    if set(data) != expected_files or any(not isinstance(data[name], str) for name in data):
        raise UpgradeError(f"handoff {mode} payload files are invalid: {sorted(map(str, data))!r}")
    _validated_version(values["STATE_MIRROR_TARGET_VERSION"], "handoff target")
    _validated_operation_id(values["STATE_MIRROR_OPERATION_ID"])
    _validated_digest(values["STATE_MIRROR_CLASSIFIER_DIGEST"])
    if mode == "upgrade":
        _validated_version(values["STATE_MIRROR_SOURCE_VERSION"], "handoff source")
    return values


def _upgrade_env(transaction: UpgradeTransaction, mode: str = "upgrade") -> str:
    lines = [f"STATE_MIRROR_UPGRADE_MODE={mode}"]
    if mode == "upgrade":
        lines.append(f"STATE_MIRROR_SOURCE_VERSION={transaction.source_version}")
    lines.extend(
        [
            f"STATE_MIRROR_TARGET_VERSION={transaction.target_version}",
            f"STATE_MIRROR_OPERATION_ID={transaction.operation_id}",
            f"STATE_MIRROR_CLASSIFIER_DIGEST={transaction.classifier_digest}",
        ]
    )
    return "\n".join(lines) + "\n"


def _fresh_env(target_version: str, operation_id: str, digest: str) -> str:
    return (
        "STATE_MIRROR_UPGRADE_MODE=fresh\n"
        f"STATE_MIRROR_TARGET_VERSION={target_version}\n"
        f"STATE_MIRROR_OPERATION_ID={operation_id}\n"
        f"STATE_MIRROR_CLASSIFIER_DIGEST={digest}\n"
    )


def _handoff_data(
    mode: str,
    transaction: UpgradeTransaction,
    *,
    source_gv: Optional[str] = None,
    paths: Optional[list[str]] = None,
) -> dict[str, str]:
    if mode == "fresh":
        return {
            "upgrade.env": _fresh_env(
                transaction.target_version, transaction.operation_id, transaction.classifier_digest
            )
        }
    if mode == "committed":
        return {"upgrade.env": _upgrade_env(transaction, mode="committed")}
    assert source_gv is not None
    assert paths is not None
    return {
        "upgrade.env": _upgrade_env(transaction),
        "source-gv.cfg": source_gv,
        "preserve-paths.txt": "".join(f"{path}\n" for path in paths),
    }


def _read_source_gv(api: ConfigMapApi, name: str, key: str) -> str:
    cm = api.read_cm(name)
    if cm is None:
        raise UpgradeError(f"source gv.cfg ConfigMap {name!r} does not exist")
    value = (cm.get("data") or {}).get(key)
    if isinstance(value, str):
        return value
    encoded = (cm.get("binary_data") or {}).get(key)
    if isinstance(encoded, str):
        try:
            return base64.b64decode(encoded, validate=True).decode("utf-8")
        except ValueError as exc:
            raise UpgradeError(
                f"source ConfigMap {name!r} key {key!r} is not decodable UTF-8 text: {exc}"
            ) from exc
    raise UpgradeError(f"source ConfigMap {name!r} is missing text key {key!r}")


def _is_legacy_committed(data, manifest):
    """Recognize only a completed schema-1 handoff backed by matching authority.

    Legacy active transactions remain invalid: they never bound a classifier
    digest. Adoption creates a new, digest-bound checkpoint transaction.
    """
    if manifest is None or manifest.schema_version != 1:
        return False
    if not isinstance(data, dict) or set(data) != {"upgrade.env"}:
        return False
    raw = data.get("upgrade.env")
    if not isinstance(raw, str):
        return False
    values = _parse_env(raw)
    if set(values) != {
        "STATE_MIRROR_UPGRADE_MODE",
        "STATE_MIRROR_TARGET_VERSION",
        "STATE_MIRROR_OPERATION_ID",
    }:
        return False
    if values["STATE_MIRROR_UPGRADE_MODE"] != "committed":
        return False
    if (
        values["STATE_MIRROR_TARGET_VERSION"] != manifest.target_version
        or values["STATE_MIRROR_OPERATION_ID"] != manifest.operation_id
    ):
        raise UpgradeError("legacy committed handoff conflicts with durable manifest")
    return True


def _operation_for_preflight(
    api: ConfigMapApi,
    handoff_name: str,
    mode: str,
    source_version: str,
    target_version: str,
    requested_operation_id: Optional[str],
    classifier_digest: str,
    source_gv: Optional[str] = None,
    paths: Optional[list[str]] = None,
    legacy_manifest: Optional[UpgradeManifest] = None,
) -> tuple[str, Optional[str]]:
    """Reuse an identical retry and reject any globally active conflict."""
    named_handoff = None
    legacy_named = False
    for existing in api.list_cms(HANDOFF_SELECTOR):
        if existing.get("name") == handoff_name:
            named_handoff = existing
            if _is_legacy_committed(existing.get("data"), legacy_manifest):
                legacy_named = True
                continue
        values = _validate_handoff_payload(existing.get("data"))
        if values["STATE_MIRROR_CLASSIFIER_DIGEST"] != classifier_digest:
            raise UpgradeError("handoff classifier digest conflicts with requested transaction")
        live_mode = values["STATE_MIRROR_UPGRADE_MODE"]
        if live_mode == "committed":
            live_operation = values["STATE_MIRROR_OPERATION_ID"]
            live_target = values["STATE_MIRROR_TARGET_VERSION"]
            if mode == "committed":
                if requested_operation_id != live_operation or live_target != target_version:
                    raise UpgradeError("committed handoff conflicts with durable manifest")
                transaction = UpgradeTransaction(
                    source_version, target_version, live_operation, classifier_digest
                )
                if (existing.get("data") or {}) != _handoff_data(mode, transaction):
                    raise UpgradeError("committed handoff payload is inconsistent")
                return live_operation, _resource_version(existing)
            if live_target == target_version:
                raise UpgradeError("committed handoff conflicts with requested transaction")
            continue
        operation_id = values["STATE_MIRROR_OPERATION_ID"]
        if existing.get("name") != handoff_name:
            raise UpgradeError(
                f"active upgrade handoff {existing.get('name')!r} conflicts with {handoff_name!r}"
            )
        if mode == "committed":
            if (
                requested_operation_id == operation_id
                and values["STATE_MIRROR_TARGET_VERSION"] == target_version
            ):
                return operation_id, _resource_version(existing)
            raise UpgradeError("active handoff conflicts with committed transaction")
        identity = (
            live_mode,
            values.get("STATE_MIRROR_SOURCE_VERSION") if live_mode == "upgrade" else "",
            values["STATE_MIRROR_TARGET_VERSION"],
        )
        requested = (mode, source_version if mode == "upgrade" else "", target_version)
        if identity != requested:
            raise UpgradeError(
                "existing handoff conflicts with requested transaction: "
                f"stored={identity!r}, requested={requested!r}"
            )
        if requested_operation_id is not None and requested_operation_id != operation_id:
            raise UpgradeError("requested operation ID conflicts with existing handoff")
        transaction = UpgradeTransaction(
            source_version, target_version, operation_id, classifier_digest
        )
        expected_data = _handoff_data(mode, transaction, source_gv=source_gv, paths=paths)
        if (existing.get("data") or {}) != expected_data:
            raise UpgradeError("existing handoff payload conflicts with requested transaction")
        return operation_id, _resource_version(existing)
    resource_version = _resource_version(named_handoff) if named_handoff is not None else None
    if named_handoff is not None and not legacy_named:
        values = _parse_env((named_handoff.get("data") or {}).get("upgrade.env", ""))
        if (
            mode != "committed"
            and values.get("STATE_MIRROR_UPGRADE_MODE") == "committed"
            and values.get("STATE_MIRROR_TARGET_VERSION") == target_version
        ):
            raise UpgradeError("handoff transaction was already committed")
    return _validated_operation_id(requested_operation_id or uuid.uuid4().hex), resource_version


def _resource_version(configmap: dict) -> str:
    value = configmap.get("resource_version")
    if not isinstance(value, str) or not value:
        raise UpgradeError(f"ConfigMap {configmap.get('name')!r} is missing resourceVersion")
    return value


def _write_preflight_handoff(
    api: ConfigMapApi,
    *,
    handoff_name: str,
    mode: str,
    source_version: str,
    target_version: str,
    requested_operation_id: Optional[str],
    classifier_digest: str,
    source_gv: Optional[str] = None,
    paths: Optional[list[str]] = None,
    legacy_manifest: Optional[UpgradeManifest] = None,
) -> UpgradeTransaction:
    operation_id = requested_operation_id
    for _attempt in range(3):
        operation_id, resource_version = _operation_for_preflight(
            api,
            handoff_name,
            mode,
            source_version,
            target_version,
            operation_id,
            classifier_digest,
            source_gv,
            paths,
            legacy_manifest=legacy_manifest,
        )
        transaction = UpgradeTransaction(
            source_version, target_version, operation_id, classifier_digest
        )
        data = _handoff_data(mode, transaction, source_gv=source_gv, paths=paths)
        if api.write_cm_cas(
            handoff_name,
            expected_resource_version=resource_version,
            labels={HANDOFF_LABEL: HANDOFF_LABEL_VALUE},
            annotations={},
            data=data,
            binary_data={},
        ):
            return transaction
    raise UpgradeError("handoff ConfigMap changed during preflight")


def _validate_committed_authority(
    api: ConfigMapApi,
    handoff_name: str,
    manifest: Optional[UpgradeManifest],
) -> None:
    for handoff in api.list_cms(HANDOFF_SELECTOR):
        if handoff.get("name") != handoff_name:
            continue
        if _is_legacy_committed(handoff.get("data"), manifest):
            return
        values = _validate_handoff_payload(handoff.get("data"))
        if values.get("STATE_MIRROR_UPGRADE_MODE") != "committed":
            return
        if manifest is None:
            raise UpgradeError("committed handoff has no durable upgrade manifest")
        transaction = UpgradeTransaction(
            manifest.source_version,
            manifest.target_version,
            manifest.operation_id,
            manifest.classifier_digest,
        )
        if (handoff.get("data") or {}) != _handoff_data("committed", transaction):
            raise UpgradeError("committed handoff conflicts with durable upgrade manifest")
        return


def _read_handoff_dir(path: str) -> tuple[dict[str, str], dict[str, str]]:
    env_path = os.path.join(path, "upgrade.env")
    try:
        with open(env_path, encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        raise UpgradeError(f"cannot read mounted handoff {env_path}: {exc}") from exc
    values = _parse_env(raw)
    data = {"upgrade.env": raw}
    if values.get("STATE_MIRROR_UPGRADE_MODE") == "upgrade":
        for name in ("source-gv.cfg", "preserve-paths.txt"):
            file_path = os.path.join(path, name)
            try:
                with open(file_path, encoding="utf-8") as fh:
                    data[name] = fh.read()
            except OSError as exc:
                raise UpgradeError(f"cannot read mounted handoff {file_path}: {exc}") from exc
    return _validate_handoff_payload(data), data


def _find_handoff(api: ConfigMapApi, operation_id: str) -> dict:
    matches: list[dict] = []
    for cm in api.list_cms(HANDOFF_SELECTOR):
        values = _validate_handoff_payload(cm.get("data"))
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
    classifier_digest: str,
    mounted_mode: str,
    source_version: str,
    target_version: str,
    operation_id: str,
    existing: Optional[UpgradeManifest],
    mounted_data: dict[str, str],
) -> None:
    values = _validate_handoff_payload(handoff.get("data"))
    live_mode = values.get("STATE_MIRROR_UPGRADE_MODE")
    live_target = values.get("STATE_MIRROR_TARGET_VERSION")
    live_operation = values.get("STATE_MIRROR_OPERATION_ID")
    if values["STATE_MIRROR_CLASSIFIER_DIGEST"] != classifier_digest:
        raise UpgradeError("live handoff classifier digest conflicts")
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
        transaction = UpgradeTransaction(
            source_version, target_version, operation_id, classifier_digest
        )
        expected_data = _handoff_data("committed", transaction)
        if (handoff.get("data") or {}) != expected_data:
            raise UpgradeError("committed handoff payload is inconsistent")
        if mounted_mode == "committed" and mounted_data != expected_data:
            raise UpgradeError("mounted committed handoff payload is inconsistent")
        return
    if (handoff.get("data") or {}) != mounted_data:
        raise UpgradeError("live handoff payload conflicts with mounted transaction")
    if live_mode != mounted_mode:
        raise UpgradeError(
            f"live handoff mode {live_mode!r} conflicts with mounted mode {mounted_mode!r}"
        )
    if live_mode == "upgrade" and values.get("STATE_MIRROR_SOURCE_VERSION") != source_version:
        raise UpgradeError("live handoff source version conflicts with mounted transaction")
