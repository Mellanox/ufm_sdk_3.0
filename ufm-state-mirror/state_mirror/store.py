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

import logging
from abc import ABC, abstractmethod
from typing import Iterable, Optional

from state_mirror import wire
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
