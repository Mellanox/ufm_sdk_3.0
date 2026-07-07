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
import stat

from state_mirror import wire
from state_mirror.handlers.base import BaseHandler, MirrorResult

log = logging.getLogger(__name__)


class DirectoryHandler(BaseHandler):
    def _key_for_rel(self, relpath: str) -> str:
        return self.entry.redis_key_prefix + relpath

    def _iter_local_files(self):
        root = self.entry.path
        try:
            root_stat = os.stat(root)
        except FileNotFoundError:
            return
        if not stat.S_ISDIR(root_stat.st_mode):
            raise NotADirectoryError(f"classified directory path is not a directory: {root}")
        if self.entry.recursive:
            for dirpath, _dirs, files in os.walk(root, onerror=self._raise_walk_error):
                for name in sorted(files):
                    full = os.path.join(dirpath, name)
                    # Do not pre-stat here: _read_file_nofollow performs the
                    # authoritative open/fstat and returns any inspection error
                    # through MirrorResult instead of silently skipping a child.
                    yield os.path.relpath(full, root), full
        else:
            # Preserve the existing traversal behavior in the outcome-accounting
            # change; symlink hardening is delivered by the next stacked PR.
            with os.scandir(root) as it:
                for de in sorted(it, key=lambda e: e.name):
                    if de.is_file(follow_symlinks=True):
                        yield de.name, de.path

    @staticmethod
    def _raise_walk_error(exc: OSError) -> None:
        """Make an unreadable recursive subtree fail reconciliation."""
        raise exc

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

    def mirror(self) -> MirrorResult:
        writes = 0
        reads = 0
        failures: list[BaseException] = []
        try:
            for relpath, full in self._iter_local_files():
                try:
                    body = self._read_file(full)
                    key = self._key_for_rel(relpath)
                    if self._push_if_changed(key, body):
                        log.info("mirror: shipped %s -> %s", full, key)
                        writes += 1
                    else:
                        reads += 1
                except Exception as exc:
                    log.exception("mirror: child failed %s; continuing with siblings", full)
                    failures.append(exc)
        except Exception as exc:
            log.exception("mirror: directory traversal failed for %s", self.entry.path)
            failures.append(exc)
        return MirrorResult(writes=writes, reads=reads, failures=tuple(failures))

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
        return self.drift_scan()[0]

    def drift_scan(self) -> tuple[list[str], int]:
        """Return per-child drift after one backend-prefix enumeration."""
        local = {relpath for relpath, _full in self._iter_local_files()}
        drift = [
            self._key_for_rel(relpath)
            for relpath in self._iter_redis_relpaths()
            if relpath not in local
        ]
        return drift, 1

    def bootstrap(self) -> None:
        # Directories have no single-file baseline; first-install is whatever
        # the image ships, mirrored on the first full scan.
        pass
