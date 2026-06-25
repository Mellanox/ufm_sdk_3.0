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
            # scandir reuses the stat already done by the OS (one syscall per
            # entry instead of listdir + isfile). follow_symlinks=True keeps the
            # prior os.path.isfile semantics: a symlink to a file still counts.
            with os.scandir(root) as it:
                for de in sorted(it, key=lambda e: e.name):
                    if de.is_file(follow_symlinks=True):
                        yield de.name, de.path

    def _iter_redis_relpaths(self):
        prefix = self.entry.redis_key_prefix
        for key in self.store.list_keys(prefix):
            if key.endswith(wire.META_SUFFIX):
                continue
            yield key[len(prefix) :]

    def restore(self) -> bool:
        count = 0
        root = os.path.realpath(self.entry.path)
        for relpath in self._iter_redis_relpaths():
            dest = os.path.join(self.entry.path, relpath)
            # Restore is the fail-closed boundary: a corrupt/hostile backend key
            # containing ``..`` must not let us write outside the entry root.
            if not self._within(root, dest):
                log.error("restore: skipping child key with out-of-root path %r", relpath)
                continue
            if self._restore_one(self.store, self._key_for_rel(relpath), dest) is not None:
                count += 1
        log.info("restore: %s restored %d child file(s)", self.entry.path, count)
        return count > 0

    @staticmethod
    def _within(root: str, dest: str) -> bool:
        real = os.path.realpath(dest)
        return real == root or real.startswith(root + os.sep)

    def mirror(self) -> bool:
        sent_any = False
        for relpath, full in self._iter_local_files():
            # A local read error for one child (e.g. it vanished mid-scan) is
            # skipped so the rest of the tree still mirrors. A backend error
            # (WireError) is NOT swallowed -- it propagates so the caller records
            # the outage via record_store_down instead of seeing a healthy run.
            try:
                body = self._read_file(full)
            except OSError:
                log.exception("mirror: cannot read child %s; skipping", full)
                continue
            key = self._key_for_rel(relpath)
            if self._push_if_changed(key, body):
                log.info("mirror: shipped %s -> %s", full, key)
                sent_any = True
        return sent_any

    def on_delete_child(self, relpath: str) -> None:
        log.info("on_delete_child: dropping %s", relpath)
        self.store.delete(self._key_for_rel(relpath))

    def on_delete(self) -> None:
        for relpath in list(self._iter_redis_relpaths()):
            self.on_delete_child(relpath)

    def key_for_fs_path(self, fs_path: str) -> str:
        """Per-child store key for a deleted file under the watched directory."""
        return self._key_for_rel(os.path.relpath(fs_path, self.entry.path))

    def drift_keys(self) -> list[str]:
        """Per-child orphans: backend children with no local file (HLD 5.3.7)."""
        local = {relpath for relpath, _full in self._iter_local_files()}
        return [
            self._key_for_rel(relpath)
            for relpath in self._iter_redis_relpaths()
            if relpath not in local
        ]

    def bootstrap(self) -> None:
        # Directories have no single-file baseline; first-install is whatever
        # the image ships, mirrored on the first full scan.
        pass
