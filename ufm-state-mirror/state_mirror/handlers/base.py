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

"""Base handler: shared restore/mirror/delete logic over a pluggable store.

A handler is the per-path policy object (HLD 5.3.2): it knows how to read a
classified file, push it to the store (only when changed), restore it on
startup, seed a first-install baseline, and propagate deletes. Subclasses
specialize the read/snapshot behavior (atomic blob, directory fan-out, sqlite
online backup). *Where* the bytes are persisted is the store's concern, not the
handler's (see :mod:`state_mirror.store`).
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from state_mirror import wire
from state_mirror.classifier import Baseline, Entry
from state_mirror.store import Store

log = logging.getLogger(__name__)


class BaseHandler:
    def __init__(self, entry: Entry, store: Store, ufm_version: str, written_by: str):
        self.entry = entry
        self.store = store
        self.ufm_version = ufm_version
        self.written_by = written_by

    def restore(self) -> bool:
        """Materialize this entry's file(s) from the store.

        Returns True if a stored object was restored, False if the store has no
        object yet (first install -> caller should bootstrap).
        """
        result = self.store.get(self.entry.redis_key)
        if result is None:
            log.debug("restore: no stored object for %s", self.entry.path)
            return False
        body, _meta = result
        self._write_file(self.entry.path, body)
        log.info(
            "restore: wrote %s (%d bytes) from %s", self.entry.path, len(body), self.entry.redis_key
        )
        return True

    def bootstrap(self) -> None:
        """First-install: seed the file from its baseline and push to Redis."""
        if self.entry.baseline is Baseline.SKIP:
            log.debug("bootstrap: %s baseline=skip, nothing to seed", self.entry.path)
            return
        if self.entry.baseline is Baseline.EMPTY:
            body = b""
        elif self.entry.baseline is Baseline.IMAGE:
            try:
                with open(self.entry.baseline_path, "rb") as f:
                    body = f.read()
            except OSError as exc:
                log.error("bootstrap: cannot read baseline %s: %s", self.entry.baseline_path, exc)
                raise
        else:
            raise ValueError(f"unknown baseline {self.entry.baseline}")
        self._write_file(self.entry.path, body)
        self._push(self.entry.redis_key, body)
        log.info(
            "bootstrap: seeded %s (%d bytes, baseline=%s)",
            self.entry.path,
            len(body),
            self.entry.baseline.value,
        )

    def mirror(self) -> bool:
        """Push the current file to Redis if it differs. Returns True if sent.

        Idempotent: compares the stored content hash before writing so an
        unchanged file is a cheap no-op.
        """
        if not os.path.exists(self.entry.path):
            log.debug("mirror: %s does not exist yet, skipping", self.entry.path)
            return False
        body = self._read_file(self.entry.path)
        sent = self._push_if_changed(self.entry.redis_key, body)
        if sent:
            log.info(
                "mirror: shipped %s (%d bytes) -> %s",
                self.entry.path,
                len(body),
                self.entry.redis_key,
            )
        return sent

    def on_delete(self) -> None:
        """Propagate a local delete to the store (HLD 5.3.9)."""
        log.info("on_delete: dropping %s from store", self.entry.redis_key)
        self.store.delete(self.entry.redis_key)

    def key_for_fs_path(self, fs_path: str) -> str:
        """Store key for a deleted local path. Single-file handlers ignore the
        path and use their one key; the directory handler derives a per-child key.
        """
        return self.entry.redis_key

    def drift_keys(self) -> list[str]:
        """Keys present in the backend but whose local file is gone (HLD 5.3.7).

        Reports drift without deleting -- the caller surfaces it via
        ``state_mirror_unexpected_delete_total`` and the backend object wins on
        ambiguity (the next restore re-materializes the file). An empty list means
        no drift.
        """
        if os.path.exists(self.entry.path):
            return []
        if self.store.get_meta(self.entry.redis_key) is None:
            return []
        return [self.entry.redis_key]

    def _push_if_changed(self, key: str, body: bytes) -> bool:
        meta = self.store.get_meta(key)
        if meta is not None and meta.content_hash == wire.content_hash(body):
            return False
        self._push(key, body)
        return True

    def _push(self, key: str, body: bytes) -> None:
        meta = wire.build_meta(
            body,
            handler=self.entry.handler.value,
            ufm_version=self.ufm_version,
            written_by=self.written_by,
        )
        self.store.put(key, body, meta)

    @staticmethod
    def _read_file(path: str) -> bytes:
        try:
            with open(path, "rb") as f:
                return f.read()
        except OSError as exc:
            log.error("read of %s failed: %s", path, exc)
            raise

    @staticmethod
    def _write_file(path: str, body: bytes) -> None:
        """Write atomically (tmp + os.replace) so readers never see a torn file."""
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        tmp = path + ".statemirror.tmp"
        try:
            with open(tmp, "wb") as f:
                f.write(body)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        except OSError as exc:
            log.error("atomic write of %s failed: %s", path, exc)
            if os.path.exists(tmp):
                os.remove(tmp)
            raise

    @staticmethod
    def _restore_one(store: Store, key: str, dest_path: str) -> Optional[wire.Meta]:
        result = store.get(key)
        if result is None:
            return None
        body, meta = result
        BaseHandler._write_file(dest_path, body)
        return meta
