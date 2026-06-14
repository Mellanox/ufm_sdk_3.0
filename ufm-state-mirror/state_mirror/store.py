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

"""Storage-backend abstraction for StateMirror (HLD 5.3.2 / 5.3.6).

A *handler* knows *what* to capture from the filesystem and *when* (blob,
atomic-blob, directory fan-out, sqlite online-backup). A ``Store`` knows *where*
durable state lives and how to read it back. Splitting the two axes lets the
same handlers run against different backends without change -- Redis today
(:class:`RedisStore`), and (for example) a ConfigMap-backed store in the future
-- so the choice of durable backing is a single, swappable component.

Each logical object is a body plus its verified metadata (:class:`wire.Meta`):
the store persists the two atomically and, on read, verifies the body against
the metadata (content hash / size / format version), failing closed on any
mismatch. The interface is intentionally backend-neutral -- ``write_transaction``
(atomic multi-key writes) and ``get_value`` (raw, meta-less pointer values) are
both expressible on a ConfigMap backend as well as on Redis.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import re
from abc import ABC, abstractmethod
from typing import Iterable, Optional, Protocol

from state_mirror import wire
from state_mirror.k8s_errors import classify_k8s_error
from state_mirror.wire import Meta

log = logging.getLogger(__name__)


class Store(ABC):
    """A durable ``key -> (bytes, Meta)`` backend the handlers mirror to/from."""

    @abstractmethod
    def get(self, key: str) -> Optional[tuple[bytes, Meta]]:
        """Read and verify a stored object.

        Returns ``None`` when the key was never written (so the caller can fall
        back to first-install bootstrap). Fails closed (raises) on a
        present-but-corrupt object.
        """

    @abstractmethod
    def get_meta(self, key: str) -> Optional[Meta]:
        """Read just the metadata for ``key`` (``None`` if absent)."""

    @abstractmethod
    def get_value(self, key: str) -> Optional[bytes]:
        """Read a raw, meta-less value (e.g. a pointer key); ``None`` if absent."""

    @abstractmethod
    def put(self, key: str, body: bytes, meta: Meta) -> None:
        """Atomically write a body together with its metadata."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Atomically delete a body together with its metadata."""

    @abstractmethod
    def list_keys(self, prefix: str) -> list[str]:
        """Return every stored key (decoded) beginning with ``prefix``."""

    @abstractmethod
    def write_transaction(
        self,
        *,
        puts: Iterable[tuple[str, bytes, Meta]] = (),
        value_puts: Iterable[tuple[str, bytes]] = (),
        deletes: Iterable[str] = (),
        value_deletes: Iterable[str] = (),
    ) -> None:
        """Apply several writes/deletes atomically.

        ``puts`` write body+meta pairs; ``value_puts`` write raw, meta-less
        values; ``deletes`` drop body+meta pairs; ``value_deletes`` drop raw
        values. Used where several keys must move together (e.g. the sqlite
        WAL-ship base/epoch rotation), so a reader never sees a partial update.
        """


class RedisStore(Store):
    """:class:`Store` backed by Redis/Valkey: one body key + one ``:meta`` key.

    Wraps a duck-typed redis-py-style client (``get``/``set``/``delete``/
    ``pipeline``/``keys``) and delegates the body+meta wire format and
    fail-closed verification to :mod:`state_mirror.wire`.
    """

    def __init__(self, client):
        self._client = client

    def get(self, key: str) -> Optional[tuple[bytes, Meta]]:
        return wire.read_and_verify(self._client, key)

    def get_meta(self, key: str) -> Optional[Meta]:
        raw = self._client.get(wire.meta_key(key))
        return Meta.from_json(raw) if raw is not None else None

    def get_value(self, key: str) -> Optional[bytes]:
        return self._client.get(key)

    def put(self, key: str, body: bytes, meta: Meta) -> None:
        wire.write_pair(self._client, key, body, meta)

    def delete(self, key: str) -> None:
        wire.delete_pair(self._client, key)

    def list_keys(self, prefix: str) -> list[str]:
        keys = []
        for key in self._client.keys(prefix + "*"):
            keys.append(key.decode() if isinstance(key, (bytes, bytearray)) else key)
        return keys

    def write_transaction(
        self,
        *,
        puts: Iterable[tuple[str, bytes, Meta]] = (),
        value_puts: Iterable[tuple[str, bytes]] = (),
        deletes: Iterable[str] = (),
        value_deletes: Iterable[str] = (),
    ) -> None:
        try:
            pipe = self._client.pipeline(transaction=True)
            for key, body, meta in puts:
                pipe.set(key, body)
                pipe.set(wire.meta_key(key), meta.to_json())
            for key, value in value_puts:
                pipe.set(key, value)
            for key in deletes:
                pipe.delete(key)
                pipe.delete(wire.meta_key(key))
            for key in value_deletes:
                pipe.delete(key)
            pipe.execute()
        except Exception as exc:  # redis.RedisError, connection drops, etc.
            reason = wire.classify_redis_error(exc)
            log.error("store transaction failed [%s]: %s", reason, exc)
            raise wire.WireError(f"store transaction failed: {exc}", reason=reason) from exc


# --- ConfigMap backend (HLD 5.3.x) ---------------------------------------
#
# A second :class:`Store` for small, low-churn files (e.g. plugin enablement
# config) that should live in the cluster's own state rather than in Redis. The
# handlers and wire format are unchanged: the choice of backing is a swappable
# component, selected per classifier entry (``backend: configmap``).

# ConfigMaps are managed objects we own; this label lets ``list_keys`` enumerate
# only ours, and the annotation carries the authoritative logical key (the
# object name is a sanitized + hashed derivative and is not reversible).
MANAGED_BY_LABEL = "app.kubernetes.io/managed-by"
MANAGED_BY_VALUE = "state-mirror"
KEY_ANNOTATION = "state-mirror.nvidia.com/key"

# Field names within a ConfigMap object. The body is binary (base64 in the API,
# so arbitrary file bytes survive); the metadata is UTF-8 JSON.
BODY_FIELD = "body"
META_FIELD = "meta"

# Hard etcd object ceiling (~1 MiB). We fail closed *before* the apiserver would
# (HLD 5.2.3): a ConfigMap-eligible file that grows past this must move to Redis
# rather than silently stop mirroring.
DEFAULT_MAX_OBJECT_BYTES = 1024 * 1024

_NAME_SANITIZE_RE = re.compile(r"[^a-z0-9]+")
_NAME_PREFIX = "state-mirror-"
_DNS1123_MAX = 253
_HASH_LEN = 10


def configmap_name(key: str, prefix: str = _NAME_PREFIX) -> str:
    """Map a logical key to a deterministic, DNS-1123-valid ConfigMap name.

    Keys contain ``:`` and ``.`` which are not legal in an object name, so the
    key is lowercased and squeezed to ``[a-z0-9-]`` and a short hash of the
    *original* key is appended to keep names unique even after sanitization
    collisions. The original key is preserved verbatim in an annotation.
    """
    base = _NAME_SANITIZE_RE.sub("-", key.lower()).strip("-")
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:_HASH_LEN]
    keep = _DNS1123_MAX - len(prefix) - len(digest) - 1
    if len(base) > keep:
        base = base[:keep].strip("-")
    name = f"{prefix}{base}-{digest}" if base else f"{prefix}{digest}"
    return name


class ConfigMapApi(Protocol):
    """Namespace-bound, dict-oriented view of the K8s ConfigMap API.

    Kept deliberately tiny and free of kubernetes-client types so the store is
    unit testable with an in-memory fake. The real adapter (which translates to
    ``CoreV1Api`` and maps ``404 -> None``) lives in
    :mod:`state_mirror.k8s_client` and imports the client lazily.
    """

    def read_cm(self, name: str) -> Optional[dict]:
        ...

    def write_cm(
        self,
        name: str,
        *,
        labels: dict[str, str],
        annotations: dict[str, str],
        data: dict[str, str],
        binary_data: dict[str, str],
    ) -> None:
        ...

    def delete_cm(self, name: str) -> None:
        ...

    def list_cms(self, label_selector: str) -> list[dict]:
        ...


class ConfigMapStore(Store):
    """:class:`Store` backed by Kubernetes ConfigMaps: one object per key.

    Each logical key maps to one ConfigMap carrying the file bytes in
    ``binaryData[body]`` and the :class:`wire.Meta` JSON in ``data[meta]``;
    writing the single object is therefore naturally atomic for that key.
    Restore re-uses :func:`wire.verify_body`, so a ConfigMap-restored file is
    validated byte-for-byte exactly like a Redis-restored one.
    """

    def __init__(self, api: ConfigMapApi, *, max_object_bytes: int = DEFAULT_MAX_OBJECT_BYTES):
        self._api = api
        self._max = max_object_bytes

    def get(self, key: str) -> Optional[tuple[bytes, Meta]]:
        cm = self._read(key)
        if cm is None:
            return None
        meta = self._meta_of(cm)
        if meta is None:
            log.debug("%s present without metadata (bootstrap path)", key)
            return None  # value-only object or never fully written
        return wire.verify_body(self._body_of(cm), meta, key), meta

    def get_meta(self, key: str) -> Optional[Meta]:
        cm = self._read(key)
        return self._meta_of(cm) if cm is not None else None

    def get_value(self, key: str) -> Optional[bytes]:
        cm = self._read(key)
        return self._body_of(cm) if cm is not None else None

    def put(self, key: str, body: bytes, meta: Meta) -> None:
        self._write(key, body=body, meta=meta)

    def delete(self, key: str) -> None:
        try:
            self._api.delete_cm(configmap_name(key))
        except Exception as exc:
            reason = classify_k8s_error(exc)
            if reason == "notfound":
                return  # already gone -> idempotent
            log.error("configmap delete failed for %s [%s]: %s", key, reason, exc)
            raise wire.WireError(f"{key}: configmap delete failed: {exc}", reason=reason) from exc
        log.info("deleted configmap for %s", key)

    def list_keys(self, prefix: str) -> list[str]:
        selector = f"{MANAGED_BY_LABEL}={MANAGED_BY_VALUE}"
        try:
            items = self._api.list_cms(selector)
        except Exception as exc:
            reason = classify_k8s_error(exc)
            log.error("configmap list failed [%s]: %s", reason, exc)
            raise wire.WireError(f"configmap list failed: {exc}", reason=reason) from exc
        keys: list[str] = []
        for cm in items:
            key = (cm.get("annotations") or {}).get(KEY_ANNOTATION)
            if key is not None and key.startswith(prefix):
                keys.append(key)
        return keys

    def write_transaction(
        self,
        *,
        puts: Iterable[tuple[str, bytes, Meta]] = (),
        value_puts: Iterable[tuple[str, bytes]] = (),
        deletes: Iterable[str] = (),
        value_deletes: Iterable[str] = (),
    ) -> None:
        # Kubernetes has no multi-object transaction, so this is NOT atomic
        # across keys. That is acceptable because ConfigMap-eligible entries are
        # single small blobs; anything needing cross-key atomicity (e.g. the
        # sqlite WAL-ship rotation) stays on Redis (HLD 5.2.3). Apply puts before
        # deletes and fail closed on the first error.
        for key, body, meta in puts:
            self._write(key, body=body, meta=meta)
        for key, value in value_puts:
            self._write(key, body=value, meta=None)
        for key in deletes:
            self.delete(key)
        for key in value_deletes:
            self.delete(key)

    # --- internals -------------------------------------------------------

    def _read(self, key: str) -> Optional[dict]:
        try:
            return self._api.read_cm(configmap_name(key))
        except Exception as exc:
            reason = classify_k8s_error(exc)
            if reason == "notfound":
                return None
            log.error("configmap read failed for %s [%s]: %s", key, reason, exc)
            raise wire.WireError(f"{key}: configmap read failed: {exc}", reason=reason) from exc

    def _write(self, key: str, *, body: bytes, meta: Optional[Meta]) -> None:
        b64 = base64.b64encode(body).decode("ascii")
        binary_data = {BODY_FIELD: b64}
        data = {META_FIELD: meta.to_json().decode("utf-8")} if meta is not None else {}

        total = len(b64) + sum(len(k) + len(v) for k, v in data.items())
        if total > self._max:
            log.error("%s encoded object %d bytes exceeds limit %d", key, total, self._max)
            raise wire.WireError(
                f"{key}: encoded object {total} bytes exceeds ConfigMap limit {self._max}",
                reason="toolarge",
            )

        try:
            self._api.write_cm(
                configmap_name(key),
                labels={MANAGED_BY_LABEL: MANAGED_BY_VALUE},
                annotations={KEY_ANNOTATION: key},
                data=data,
                binary_data=binary_data,
            )
        except Exception as exc:
            reason = classify_k8s_error(exc)
            log.error(
                "configmap write failed for %s (%d bytes) [%s]: %s", key, len(body), reason, exc
            )
            raise wire.WireError(f"{key}: configmap write failed: {exc}", reason=reason) from exc
        log.debug("wrote configmap for %s (%d bytes)", key, len(body))

    @staticmethod
    def _meta_of(cm: dict) -> Optional[Meta]:
        raw = (cm.get("data") or {}).get(META_FIELD)
        if raw is None:
            return None
        return Meta.from_json(raw.encode("utf-8") if isinstance(raw, str) else raw)

    @staticmethod
    def _body_of(cm: dict) -> Optional[bytes]:
        encoded = (cm.get("binary_data") or {}).get(BODY_FIELD)
        if encoded is None:
            return None
        return base64.b64decode(encoded)
