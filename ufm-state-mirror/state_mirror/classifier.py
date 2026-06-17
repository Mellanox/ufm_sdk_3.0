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

"""StateMirror classifier: the single source of truth for which UFM files are
durable and how they are mirrored to/from Redis (HLD 5.3.3, 5.4).

The classifier is a YAML document of entries; each entry binds an on-disk path
to a handler (blob, atomic_blob, directory, sqlite), a storage key (or key prefix
for directories), and a first-install baseline. The document is validated at load
time and fails closed on any structural error so a malformed classifier never
silently drops state. Unknown keys are ignored, so a consumer may carry extra
descriptive fields without breaking the load.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

log = logging.getLogger(__name__)


class ClassifierError(ValueError):
    """Raised when a classifier document is structurally invalid.

    Failing closed at load time is deliberate: a bad classifier would
    otherwise silently stop mirroring some files, which is invisible until a
    pod restart loses that state.
    """


class Handler(str, Enum):
    BLOB = "blob"
    ATOMIC_BLOB = "atomic_blob"
    DIRECTORY = "directory"
    SQLITE = "sqlite"


class Baseline(str, Enum):
    """First-install behavior when the backend has no key yet (HLD 5.3.8)."""

    IMAGE = "image"
    EMPTY = "empty"
    SKIP = "skip"


@dataclass(frozen=True)
class Entry:
    """A single classified path. Mirrors one HLD 5.3.3 classifier entry."""

    path: str
    handler: Handler
    redis_key: Optional[str] = None
    redis_key_prefix: Optional[str] = None
    rate_limit_ms: int = 100
    recursive: bool = False
    baseline: Baseline = Baseline.SKIP
    baseline_path: Optional[str] = None
    snapshot_method: Optional[str] = None
    poll_interval_ms: int = 200

    @property
    def is_directory(self) -> bool:
        return self.handler is Handler.DIRECTORY

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> "Entry":
        if not isinstance(raw, dict):
            raise ClassifierError(f"entry must be a mapping, got {type(raw).__name__}")
        path = raw.get("path")
        if not path or not isinstance(path, str):
            raise ClassifierError("entry is missing a non-empty string 'path'")
        handler = _coerce_enum(Handler, raw.get("handler"), "handler", path)
        baseline = _coerce_enum(
            Baseline, raw.get("baseline", Baseline.SKIP.value), "baseline", path
        )
        rate_limit_ms = _coerce_positive_int(raw.get("rate_limit_ms", 100), "rate_limit_ms", path)
        poll_interval_ms = _coerce_positive_int(
            raw.get("poll_interval_ms", 200), "poll_interval_ms", path
        )
        entry = Entry(
            path=path,
            handler=handler,
            redis_key=raw.get("redis_key"),
            redis_key_prefix=raw.get("redis_key_prefix"),
            rate_limit_ms=rate_limit_ms,
            recursive=bool(raw.get("recursive", False)),
            baseline=baseline,
            baseline_path=raw.get("baseline_path"),
            snapshot_method=raw.get("snapshot_method"),
            poll_interval_ms=poll_interval_ms,
        )
        entry.validate()
        return entry

    def validate(self) -> None:
        """Enforce handler-specific invariants. Raises ClassifierError."""
        if self.is_directory:
            if not self.redis_key_prefix:
                raise ClassifierError(f"{self.path}: directory handler requires 'redis_key_prefix'")
            if self.redis_key:
                raise ClassifierError(
                    f"{self.path}: directory handler must not set 'redis_key' "
                    f"(use 'redis_key_prefix')"
                )
        else:
            if not self.redis_key:
                raise ClassifierError(
                    f"{self.path}: {self.handler.value} handler requires 'redis_key'"
                )
            if self.redis_key_prefix:
                raise ClassifierError(
                    f"{self.path}: 'redis_key_prefix' is only valid for the directory handler"
                )
        if self.baseline is Baseline.IMAGE and not self.baseline_path:
            raise ClassifierError(f"{self.path}: baseline 'image' requires 'baseline_path'")
        if self.baseline_path and self.baseline is not Baseline.IMAGE:
            raise ClassifierError(
                f"{self.path}: 'baseline_path' is only valid with baseline 'image'"
            )


@dataclass
class Classifier:
    """A validated collection of classifier entries."""

    entries: list[Entry] = field(default_factory=list)

    @staticmethod
    def from_dict(doc: dict[str, Any]) -> "Classifier":
        if not isinstance(doc, dict):
            raise ClassifierError("classifier document must be a mapping")
        entries = doc.get("entries")
        if not entries or not isinstance(entries, list):
            raise ClassifierError("classifier must define a non-empty 'entries' list")
        classifier = Classifier([Entry.from_dict(e) for e in entries])
        classifier._check_uniqueness()
        return classifier

    @staticmethod
    def load_file(yaml_path: str) -> "Classifier":
        """Load and validate a classifier YAML file (imports PyYAML lazily)."""
        import yaml

        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                doc = yaml.safe_load(f)
        except OSError as exc:
            log.error("cannot read classifier %s: %s", yaml_path, exc)
            raise ClassifierError(f"cannot read classifier {yaml_path}: {exc}") from exc
        except yaml.YAMLError as exc:
            log.error("classifier %s is not valid YAML: %s", yaml_path, exc)
            raise ClassifierError(f"classifier {yaml_path} is not valid YAML: {exc}") from exc
        classifier = Classifier.from_dict(doc)
        log.info("loaded classifier %s with %d entries", yaml_path, len(classifier))
        return classifier

    def _check_uniqueness(self) -> None:
        paths = set()
        keys = set()
        for e in self.entries:
            if e.path in paths:
                raise ClassifierError(f"duplicate path in classifier: {e.path}")
            paths.add(e.path)
            key = e.redis_key_prefix if e.is_directory else e.redis_key
            if key in keys:
                raise ClassifierError(f"duplicate redis key/prefix in classifier: {key}")
            keys.add(key)

    def __len__(self) -> int:
        return len(self.entries)


def _coerce_enum(enum_cls, value, field_name: str, path: str):
    if value is None:
        raise ClassifierError(f"{path}: missing '{field_name}'")
    try:
        return enum_cls(value)
    except ValueError:
        allowed = ", ".join(e.value for e in enum_cls)
        raise ClassifierError(
            f"{path}: invalid {field_name} '{value}' (allowed: {allowed})"
        ) from None


def _coerce_positive_int(value: Any, field_name: str, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ClassifierError(f"{path}: '{field_name}' must be an integer")
    if value <= 0:
        raise ClassifierError(f"{path}: '{field_name}' must be > 0")
    return value
