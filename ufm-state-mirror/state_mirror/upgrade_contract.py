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

"""Upgrade wire contracts, release identities and strict validation."""

from __future__ import annotations

import datetime
import json
import re
from dataclasses import dataclass
from typing import Optional, Protocol

FILES_ROOT = "/opt/ufm/files"
HELM_OWNED_PATHS = (
    f"{FILES_ROOT}/conf/gv.cfg",
    f"{FILES_ROOT}/ufm_version",
    f"{FILES_ROOT}/.helm_config_checksum",
)

MANIFEST_KEY = "state-mirror:upgrade-manifest"
MANIFEST_SCHEMA_VERSION = 2
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

    def write_cm_cas(
        self,
        name: str,
        *,
        expected_resource_version: Optional[str],
        labels: dict[str, str],
        annotations: dict[str, str],
        data: dict[str, str],
        binary_data: dict[str, str],
    ) -> bool: ...


@dataclass(frozen=True)
class UpgradeManifest:
    source_version: str
    target_version: str
    operation_id: str
    committed_at: str
    classifier_digest: str = ""
    generation: str = ""
    schema_version: int = MANIFEST_SCHEMA_VERSION

    def to_bytes(self) -> bytes:
        return json.dumps(
            {
                "schema_version": self.schema_version,
                "classifier_digest": self.classifier_digest,
                "generation": self.generation,
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
                classifier_digest=data.get("classifier_digest", ""),
                generation=data.get("generation", ""),
                source_version=_validated_version(data["source_version"], "manifest source"),
                target_version=_validated_version(data["target_version"], "manifest target"),
                operation_id=_validated_operation_id(data["operation_id"]),
                committed_at=_validated_timestamp(data["committed_at"]),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise UpgradeError(f"durable upgrade manifest is corrupt: {exc}") from exc
        if manifest.schema_version not in (1, MANIFEST_SCHEMA_VERSION):
            raise UpgradeError(
                "unsupported durable upgrade manifest schema "
                f"{manifest.schema_version} (expected {MANIFEST_SCHEMA_VERSION})"
            )
        if manifest.schema_version == 2:
            _validated_digest(manifest.classifier_digest)
            _validated_operation_id(manifest.generation)
        if compare_versions(manifest.source_version, manifest.target_version) > 0:
            raise UpgradeError("durable upgrade manifest records a downgrade")
        return manifest


@dataclass(frozen=True)
class UpgradeTransaction:
    source_version: str
    target_version: str
    operation_id: str
    classifier_digest: str


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


def _validated_digest(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise UpgradeError("classifier digest is missing or invalid")
    return value


def _validated_operation_id(value: object) -> str:
    if not isinstance(value, str) or not _OPERATION_ID_RE.fullmatch(value):
        raise UpgradeError(f"invalid StateMirror operation ID: {value!r}")
    return value


def _validated_timestamp(value: object, description: str = "manifest") -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value
    ):
        raise UpgradeError(f"invalid {description} timestamp: {value!r}")
    try:
        datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise UpgradeError(f"invalid {description} timestamp: {value!r}") from exc
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
