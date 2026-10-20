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

"""Isolated data generations and backend-neutral, fail-closed writer fencing.

All supported writers serialize mutations using a CAS fence object. A crashed
or uncertain mutation leaves the fence busy; it is never stolen on a timeout.
This is necessary on ConfigMap, which has no cross-object transaction primitive.
"""

from __future__ import annotations

import json
import os
import uuid

from state_mirror import wire
from state_mirror.classifier import Classifier, Handler
from state_mirror.handlers import make_handler
from state_mirror.handlers.base import path_exists
from state_mirror.store import Store
from state_mirror.upgrade_contract import UpgradeError

GENERATION_PREFIX = "state-mirror:generation:"
FENCE_PREFIX = "state-mirror:fence:"
INVENTORY_KEY = "state-mirror:inventory"


class GenerationError(UpgradeError):
    """A generation or its writer fence cannot be safely used."""


def encode(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def record(store, key):
    result = store.get(key)
    if result is None and store.list_keys(key):
        raise GenerationError(f"incomplete control object {key}")
    return result


def cas(store, key, expected, value, version):
    body = encode(value)
    meta = wire.build_meta(body, "generation_control", version, "state-mirror:transaction")
    # Pin written_at before returning an expected CAS record. Meta.to_json()
    # otherwise generates a new timestamp when an operation crosses a second.
    meta = wire.Meta.from_json(meta.to_json())
    if not store.put_if_unchanged(key, expected, body, meta):
        raise GenerationError(f"control object changed: {key}")
    return body, meta


class GenerationStore(Store):
    """A pinned logical keyspace; it never follows a moving active pointer."""

    def __init__(self, store: Store, generation: str = "", *, readonly=False):
        if generation and (
            len(generation) != 32 or any(c not in "0123456789abcdef" for c in generation)
        ):
            raise GenerationError("invalid generation ID")
        self.raw = store
        self.generation = generation
        self.prefix = f"{GENERATION_PREFIX}{generation}:" if generation else ""
        self.readonly = readonly

    def get(self, key):
        return self.raw.get(self.prefix + key)

    def get_meta(self, key):
        return self.raw.get_meta(self.prefix + key)

    def put(self, key, body, meta):
        if self.readonly:
            # Restore bootstrap materializes baselines locally. Only a later
            # mirror or commit may publish them, never an init-container restore.
            return
        self.raw.put(self.prefix + key, body, meta)

    def put_if_unchanged(self, key, expected, body, meta):
        if self.readonly:
            raise GenerationError("read-only generation")
        return self.raw.put_if_unchanged(self.prefix + key, expected, body, meta)

    def delete(self, key):
        if self.readonly:
            raise GenerationError("read-only generation")
        self.raw.delete(self.prefix + key)

    def list_keys(self, prefix):
        keys = self.raw.list_keys(self.prefix + prefix)
        return [key[len(self.prefix) :] for key in keys]

    def probe(self):
        self.raw.probe()


def fence_key(generation):
    return FENCE_PREFIX + (generation or "legacy")


def ensure_fence(store, generation, digest, version):
    key = fence_key(generation)
    current = record(store, key)
    if current is None:
        value = {"digest": digest, "version": version, "state": "open", "lock": ""}
        try:
            return cas(store, key, None, value, version)
        except GenerationError:
            current = record(store, key)
    value = json.loads(current[0])
    if value.get("digest") != digest or value.get("version") != version:
        raise GenerationError("writer fence classifier digest or release version conflict")
    return current


class FencedStore(GenerationStore):
    def __init__(self, store, generation, digest, version):
        super().__init__(store, generation)
        self.digest = digest
        self.version = version
        ensure_fence(store, generation, digest, version)

    def assert_writable(self):
        current = ensure_fence(self.raw, self.generation, self.digest, self.version)
        value = json.loads(current[0])
        if value.get("state") != "open" or value.get("lock"):
            raise GenerationError("writer fenced or mutation still in flight")
        return current, value

    def _mutate(self, logical_key, action):
        key = fence_key(self.generation)
        current, value = self.assert_writable()
        busy = dict(value, lock=uuid.uuid4().hex)
        locked = cas(self.raw, key, current, busy, self.version)
        # Never unlock on an exception: the backend may have accepted a write
        # whose response was lost. Recovery must prove this writer has stopped.
        result = action()
        if self.generation:
            inventory_record = self.get(INVENTORY_KEY)
            if inventory_record is None:
                raise GenerationError("active generation inventory is missing")
            inventory = json.loads(inventory_record[0])
            item = self.get(logical_key)
            if item is None:
                inventory.pop(logical_key, None)
            else:
                inventory[logical_key] = item[1].content_hash
            body = encode(inventory)
            self.raw.put(
                self.prefix + INVENTORY_KEY,
                body,
                wire.build_meta(body, "inventory", self.version, "state-mirror:writer"),
            )
        cas(self.raw, key, locked, value, self.version)
        return result

    def put(self, key, body, meta):
        return self._mutate(key, lambda: self.raw.put(self.prefix + key, body, meta))

    def put_if_unchanged(self, key, expected, body, meta):
        return self._mutate(
            key, lambda: self.raw.put_if_unchanged(self.prefix + key, expected, body, meta)
        )

    def delete(self, key):
        return self._mutate(key, lambda: self.raw.delete(self.prefix + key))

    def freeze(self, operation_id, target_version):
        key = fence_key(self.generation)
        current = ensure_fence(self.raw, self.generation, self.digest, self.version)
        value = json.loads(current[0])
        requested = dict(
            value, state="frozen", operation_id=operation_id, target_version=target_version
        )
        if value == requested and not value.get("lock"):
            return requested
        if value.get("state") != "open" or value.get("lock"):
            raise GenerationError("writer fenced or mutation still in flight")
        cas(self.raw, key, current, requested, self.version)
        return requested


def require_checkpoint(store, generation, digest, operation_id, target_version):
    current = record(store, fence_key(generation))
    value = json.loads(current[0]) if current else {}
    if (
        value.get("state") != "frozen"
        or value.get("lock")
        or value.get("digest") != digest
        or value.get("operation_id") != operation_id
        or value.get("target_version") != target_version
    ):
        raise GenerationError("acknowledged final checkpoint is missing or conflicts")
    return current


def verify_inventory(store, expected=None):
    result = store.get(INVENTORY_KEY)
    if result is None:
        raise GenerationError("generation inventory is missing")
    inventory = json.loads(result[0])
    if expected is not None and inventory != expected:
        raise GenerationError("generation inventory changed during publication")
    actual = set(store.list_keys("")) - {INVENTORY_KEY, wire.meta_key(INVENTORY_KEY)}
    wanted = {item for key in inventory for item in (key, wire.meta_key(key))}
    # ConfigMap lists logical objects, Redis lists body and metadata keys.
    if actual - wanted or any(key not in actual for key in inventory):
        raise GenerationError("generation inventory/key set mismatch")
    for key, content_hash in inventory.items():
        value = store.get(key)
        if value is not None:
            wire.verify_body(value[0], value[1], key)
        if value is None or value[1].content_hash != content_hash:
            raise GenerationError(f"generation verification failed: {key}")
    return inventory


def validate_snapshot_paths(classifier):
    for entry in classifier.entries:
        if (
            entry.handler is Handler.SQLITE
            and path_exists(entry.path)
            and os.path.getsize(entry.path) == 0
        ):
            raise GenerationError(f"cannot checkpoint an empty SQLite database: {entry.path}")


def verify_classified(store, classifier):
    if store.generation:
        verify_inventory(store)
        return
    for entry in classifier.entries:
        if entry.is_directory:
            keys = {
                key[: -len(wire.META_SUFFIX)] if key.endswith(wire.META_SUFFIX) else key
                for key in store.list_keys(entry.redis_key_prefix)
            }
        else:
            raw = set(store.list_keys(entry.redis_key))
            present = entry.redis_key in raw or wire.meta_key(entry.redis_key) in raw
            keys = {entry.redis_key} if present else set()
        for key in keys:
            result = store.get(key)
            if result is None:
                raise GenerationError(f"checkpoint object is incomplete: {key}")
            wire.verify_body(result[0], result[1], key)


def publish_snapshot(classifier: Classifier, raw: Store, version: str):
    """Capture every local object into a fresh generation, then verify readback.

    Fresh handlers force SQLite online backup and do not reuse poll fingerprints.
    Missing optional paths are represented by absence in the complete inventory.
    """
    validate_snapshot_paths(classifier)
    generation = uuid.uuid4().hex

    class StagingStore(GenerationStore):
        def put(self, key, body, meta):
            wire.verify_body(body, meta, key)
            super().put(key, body, meta)
            inventory[key] = wire.content_hash(body)

    inventory = {}
    staged = StagingStore(raw, generation)
    for entry in classifier.entries:
        handler = make_handler(entry, staged, version, "state-mirror:upgrade")
        result = handler.mirror()
        if result.failures:
            raise GenerationError(f"snapshot failed for {entry.path}") from result.failures[0]
    body = encode(inventory)
    GenerationStore.put(
        staged,
        INVENTORY_KEY,
        body,
        wire.build_meta(body, "inventory", version, "state-mirror:upgrade"),
    )
    verify_inventory(staged, inventory)
    return generation
