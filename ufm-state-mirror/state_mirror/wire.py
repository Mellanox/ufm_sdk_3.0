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

"""Wire format for StateMirror <-> Redis (HLD 5.3.6).

Each classified file occupies two Redis keys:
    <key>        -> raw file bytes (byte-identical to the on-disk file)
    <key>:meta   -> JSON metadata (schema below)

The two keys are written together in a MULTI/EXEC transaction so a reader never
sees a body without its matching metadata. On restore the body is verified
against the metadata's content hash and format version, failing closed on any
mismatch.

This module is stdlib-only and takes a duck-typed Redis client (anything with
``get``, ``pipeline`` and ``delete``) so it is unit testable with a fake.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any, Optional

from state_mirror.redis_errors import classify_redis_error

log = logging.getLogger(__name__)

# Bump only on a breaking change to the on-Redis layout. The init container
# refuses to restore a format it does not recognize (HLD 5.3.6 step 2).
FORMAT_VERSION = 1

META_SUFFIX = ":meta"


class WireError(Exception):
    """Raised on a corrupt / unrecognized / mismatched stored object.

    ``reason`` carries the classified Redis failure category (see
    :mod:`state_mirror.redis_errors`) when the error originated from a Redis
    operation, so the mirror loop can record it as a labeled metric. It is
    ``None`` for pure data-integrity failures (hash/size/format mismatch).
    """

    def __init__(self, *args, reason: str | None = None):
        super().__init__(*args)
        self.reason = reason


def meta_key(body_key: str) -> str:
    return f"{body_key}{META_SUFFIX}"


def content_hash(body: bytes) -> str:
    return "sha256:" + hashlib.sha256(body).hexdigest()


@dataclass
class Meta:
    handler: str
    content_hash: str
    size_bytes: int
    ufm_version: str
    written_by: str
    schema_version: int = 1
    format_version: int = FORMAT_VERSION
    written_at: Optional[str] = None

    def to_json(self) -> bytes:
        payload = {
            "format_version": self.format_version,
            "ufm_version": self.ufm_version,
            "schema_version": self.schema_version,
            "handler": self.handler,
            "content_hash": self.content_hash,
            "size_bytes": self.size_bytes,
            "written_at": self.written_at or _utcnow_iso(),
            "written_by": self.written_by,
        }
        return json.dumps(payload, separators=(",", ":")).encode("utf-8")

    @staticmethod
    def from_json(raw: bytes) -> "Meta":
        try:
            d: dict[str, Any] = json.loads(raw)
        except (ValueError, TypeError) as exc:
            raise WireError(f"metadata is not valid JSON: {exc}") from exc
        try:
            return Meta(
                handler=d["handler"],
                content_hash=d["content_hash"],
                size_bytes=int(d["size_bytes"]),
                ufm_version=d.get("ufm_version", "unknown"),
                written_by=d.get("written_by", "unknown"),
                schema_version=int(d.get("schema_version", 1)),
                format_version=int(d["format_version"]),
                written_at=d.get("written_at"),
            )
        except KeyError as exc:
            raise WireError(f"metadata missing required field: {exc}") from exc


def build_meta(body: bytes, handler: str, ufm_version: str, written_by: str) -> Meta:
    return Meta(
        handler=handler,
        content_hash=content_hash(body),
        size_bytes=len(body),
        ufm_version=ufm_version,
        written_by=written_by,
    )


def write_pair(client: Any, body_key: str, body: bytes, meta: Meta) -> None:
    """Atomically SET <key> and <key>:meta (HLD 5.3.6).

    Wraps the underlying client error in a WireError so callers get a single,
    well-typed failure with the key for context.
    """
    try:
        pipe = client.pipeline(transaction=True)
        pipe.set(body_key, body)
        pipe.set(meta_key(body_key), meta.to_json())
        pipe.execute()
    except Exception as exc:  # redis.RedisError, connection drops, etc.
        reason = classify_redis_error(exc)
        log.error(
            "write_pair failed for %s (%d bytes) [%s]: %s",
            body_key,
            meta.size_bytes,
            reason,
            exc,
        )
        raise WireError(f"{body_key}: write failed: {exc}", reason=reason) from exc
    log.debug("wrote %s (%d bytes, %s)", body_key, meta.size_bytes, meta.content_hash)


def delete_pair(client: Any, body_key: str) -> None:
    """Atomically DEL <key> and <key>:meta (HLD 5.3.9)."""
    try:
        pipe = client.pipeline(transaction=True)
        pipe.delete(body_key)
        pipe.delete(meta_key(body_key))
        pipe.execute()
    except Exception as exc:
        reason = classify_redis_error(exc)
        log.error("delete_pair failed for %s [%s]: %s", body_key, reason, exc)
        raise WireError(f"{body_key}: delete failed: {exc}", reason=reason) from exc
    log.info("deleted key pair for %s", body_key)


def read_and_verify(client: Any, body_key: str) -> Optional[tuple[bytes, Meta]]:
    """Read body+meta, fail closed on any inconsistency (HLD 5.3.6).

    Returns ``None`` when the key has never been written (meta absent) so the
    caller can fall back to first-install bootstrap (HLD 5.3.8). Raises
    ``WireError`` on a present-but-corrupt object.
    """
    try:
        raw_meta = client.get(meta_key(body_key))
    except Exception as exc:
        reason = classify_redis_error(exc)
        log.error("read of metadata for %s failed [%s]: %s", body_key, reason, exc)
        raise WireError(f"{body_key}: metadata read failed: {exc}", reason=reason) from exc
    if raw_meta is None:
        log.debug("%s has no metadata in Redis (bootstrap path)", body_key)
        return None  # never written -> bootstrap path

    meta = Meta.from_json(raw_meta)
    if meta.format_version > FORMAT_VERSION:
        log.error(
            "%s stored format_version %d newer than supported %d",
            body_key,
            meta.format_version,
            FORMAT_VERSION,
        )
        raise WireError(
            f"{body_key}: stored format_version {meta.format_version} is newer "
            f"than supported {FORMAT_VERSION} (refusing downgrade)"
        )

    try:
        body = client.get(body_key)
    except Exception as exc:
        reason = classify_redis_error(exc)
        log.error("read of body for %s failed [%s]: %s", body_key, reason, exc)
        raise WireError(f"{body_key}: body read failed: {exc}", reason=reason) from exc
    if body is None:
        log.error("%s: metadata present but body key missing", body_key)
        raise WireError(f"{body_key}: metadata present but body key missing")

    actual = content_hash(body)
    if actual != meta.content_hash:
        log.error(
            "%s content hash mismatch (stored %s, computed %s)",
            body_key,
            meta.content_hash,
            actual,
        )
        raise WireError(
            f"{body_key}: content hash mismatch (stored {meta.content_hash}, " f"computed {actual})"
        )
    if len(body) != meta.size_bytes:
        log.error("%s size mismatch (stored %d, got %d)", body_key, meta.size_bytes, len(body))
        raise WireError(f"{body_key}: size mismatch (stored {meta.size_bytes}, got {len(body)})")
    log.debug("verified %s (%d bytes, %s)", body_key, meta.size_bytes, meta.content_hash)
    return body, meta


def _utcnow_iso() -> str:
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
