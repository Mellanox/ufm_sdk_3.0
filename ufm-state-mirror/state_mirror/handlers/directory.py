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

"""Directory handler: mirror every child file under a watched directory, one
Redis key per file derived from a key prefix + relative path (HLD 5.3.2).

Used for config trees (e.g. plugin conf directories) where the set of files is
not known in advance. Restore enumerates the Redis keys under the prefix and
recreates the tree; per-child deletes are propagated individually.
"""

from __future__ import annotations

import logging
import os

from state_mirror import wire
from state_mirror.handlers.base import BaseHandler

log = logging.getLogger(__name__)


class DirectoryHandler(BaseHandler):
    def _key_for_rel(self, relpath: str) -> str:
        return self.entry.redis_key_prefix + relpath

    def _iter_local_files(self):
        root = self.entry.path
        if not os.path.isdir(root):
            return
        if self.entry.recursive:
            for dirpath, _dirs, files in os.walk(root):
                for name in sorted(files):
                    full = os.path.join(dirpath, name)
                    yield os.path.relpath(full, root), full
        else:
            for name in sorted(os.listdir(root)):
                full = os.path.join(root, name)
                if os.path.isfile(full):
                    yield name, full

    def _iter_redis_relpaths(self):
        prefix = self.entry.redis_key_prefix
        for key in self.store.list_keys(prefix):
            if key.endswith(wire.META_SUFFIX):
                continue
            yield key[len(prefix) :]

    def restore(self) -> bool:
        count = 0
        for relpath in self._iter_redis_relpaths():
            dest = os.path.join(self.entry.path, relpath)
            if self._restore_one(self.store, self._key_for_rel(relpath), dest) is not None:
                count += 1
        log.info("restore: %s restored %d child file(s)", self.entry.path, count)
        return count > 0

    def mirror(self) -> bool:
        sent_any = False
        for relpath, full in self._iter_local_files():
            try:
                body = self._read_file(full)
                key = self._key_for_rel(relpath)
                if self._push_if_changed(key, body):
                    log.info("mirror: shipped %s -> %s", full, key)
                    sent_any = True
            except Exception:
                log.exception("mirror: failed to ship child %s; continuing", relpath)
        return sent_any

    def on_delete_child(self, relpath: str) -> None:
        log.info("on_delete_child: dropping %s", relpath)
        self.store.delete(self._key_for_rel(relpath))

    def on_delete(self) -> None:
        for relpath in list(self._iter_redis_relpaths()):
            self.on_delete_child(relpath)

    def reconcile_deletes(self) -> int:
        """Delete Redis children that have no local file (orphans) (D2 recovery).

        Recovers per-child deletes lost to a delete-queue overflow or a Redis
        outage by diffing the Redis key set under the prefix against the local
        tree. Returns the number of orphaned children removed.
        """
        local = {relpath for relpath, _full in self._iter_local_files()}
        removed = 0
        for relpath in list(self._iter_redis_relpaths()):
            if relpath not in local:
                self.on_delete_child(relpath)
                removed += 1
        return removed

    def bootstrap(self) -> None:
        # Directories have no single-file baseline; first-install is whatever
        # the image ships, mirrored on the first full scan.
        pass
