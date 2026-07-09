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
from contextlib import suppress

from state_mirror import wire
from state_mirror.handlers.base import BaseHandler, MirrorResult

log = logging.getLogger(__name__)

DEFAULT_RESTORED_FILE_MODE = 0o644
DEFAULT_RESTORED_DIR_MODE = 0o755


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
                    if os.path.islink(full):
                        continue
                    yield os.path.relpath(full, root), full
        else:
            with os.scandir(root) as it:
                for de in sorted(it, key=lambda e: e.name):
                    if de.is_file(follow_symlinks=False):
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
        """Restore children only after every backend path passes containment.

        Validation is deliberately a separate first pass. If one malicious or
        corrupt key escapes the configured root, no earlier safe child should
        already have been written before the entry fails closed.
        """
        count = 0
        children = list(self._iter_redis_relpaths())
        for relpath in children:
            self._validate_relpath(relpath)
        os.makedirs(self.entry.path, exist_ok=True)
        for relpath in children:
            if self._restore_child_secure(relpath):
                count += 1
        log.info("restore: %s restored %d child file(s)", self.entry.path, count)
        return count > 0

    @staticmethod
    def _validate_relpath(relpath: str) -> list[str]:
        parts = relpath.split(os.sep)
        if not relpath or os.path.isabs(relpath) or any(part in ("", ".", "..") for part in parts):
            raise wire.WireError(f"directory child has out-of-root path {relpath!r}")
        return parts

    def _open_parent(self, relpath: str, *, create: bool) -> tuple[int, str]:
        """Open a child's parent via no-follow directory descriptors."""
        parts = self._validate_relpath(relpath)
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        parent_fd = os.open(self.entry.path, flags)
        try:
            for part in parts[:-1]:
                created = False
                if create:
                    try:
                        os.mkdir(part, DEFAULT_RESTORED_DIR_MODE, dir_fd=parent_fd)
                        created = True
                    except FileExistsError:
                        created = False
                next_fd = os.open(part, flags, dir_fd=parent_fd)
                try:
                    if created:
                        os.fchmod(next_fd, DEFAULT_RESTORED_DIR_MODE)
                except Exception:
                    os.close(next_fd)
                    raise
                os.close(parent_fd)
                parent_fd = next_fd
            return parent_fd, parts[-1]
        except Exception:
            os.close(parent_fd)
            raise

    def _restore_child_secure(self, relpath: str) -> bool:
        result = self.store.get(self._key_for_rel(relpath))
        if result is None:
            return False
        body, _meta = result
        parent_fd, name = self._open_parent(relpath, create=True)
        tmp = name + ".statemirror.tmp"
        prev = None
        try:
            try:
                prev = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
                if not stat.S_ISREG(prev.st_mode):
                    raise OSError(f"refusing to replace non-regular file: {relpath}")
            except FileNotFoundError:
                pass
            flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
            # New children must stay readable regardless of the restore process umask.
            fd = os.open(tmp, flags, 0o666, dir_fd=parent_fd)
            try:
                if prev is None:
                    os.fchmod(fd, DEFAULT_RESTORED_FILE_MODE)
                with os.fdopen(fd, "wb") as fh:
                    fd = -1
                    fh.write(body)
                    fh.flush()
                    os.fsync(fh.fileno())
            finally:
                if fd >= 0:
                    os.close(fd)
            os.replace(tmp, name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
            if prev is not None:
                dest_fd = os.open(
                    name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_fd
                )
                try:
                    try:
                        os.fchmod(dest_fd, stat.S_IMODE(prev.st_mode))
                    except OSError as exc:
                        log.debug("fchmod of restored child %s failed: %s", relpath, exc)
                    if hasattr(os, "geteuid") and os.geteuid() == 0:
                        try:
                            os.fchown(dest_fd, prev.st_uid, prev.st_gid)
                        except OSError as exc:
                            log.warning("fchown of restored child %s failed: %s", relpath, exc)
                finally:
                    os.close(dest_fd)
            return True
        except Exception:
            with suppress(FileNotFoundError):
                os.unlink(tmp, dir_fd=parent_fd)
            raise
        finally:
            os.close(parent_fd)

    def mirror(self) -> MirrorResult:
        writes = 0
        reads = 0
        failures: list[BaseException] = []
        try:
            for relpath, full in self._iter_local_files():
                try:
                    body = self._read_file_nofollow(relpath)
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

    def _read_file_nofollow(self, relpath: str) -> bytes:
        """Read one regular child without following any path component."""
        parent_fd, name = self._open_parent(relpath, create=False)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        fd = -1
        try:
            fd = os.open(name, flags, dir_fd=parent_fd)
            mode = os.fstat(fd).st_mode
            if not stat.S_ISREG(mode):
                raise OSError(f"refusing to mirror non-regular file: {relpath}")
            with os.fdopen(fd, "rb") as fh:
                fd = -1
                return fh.read()
        finally:
            if fd >= 0:
                os.close(fd)
            os.close(parent_fd)

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
