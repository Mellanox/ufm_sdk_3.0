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

"""Event-driven change detection for the StateMirror sidecar (HLD 5.3.2).

Uses the ``watchdog`` library for cross-platform filesystem events. This module
maps raw events to classifier entries (``PathResolver``), translates them into
mirror/delete marks (``MirrorEventHandler``), and schedules the watches
(``build_observer``). The actual Redis work is deferred to the mirror loop's
drain so the watch callback stays fast and never blocks on I/O.

watchdog itself is imported lazily inside ``build_observer`` so the resolver and
dispatch logic stay unit testable without the dependency.
"""

from __future__ import annotations

import logging
import os
from typing import Callable, Optional

from state_mirror.classifier import Entry

log = logging.getLogger(__name__)

# watchdog event_type values we care about.
EVENT_CLOSED = "closed"
EVENT_MOVED = "moved"
EVENT_DELETED = "deleted"


class PathResolver:
    """Map a filesystem path to the classifier entry that governs it."""

    def __init__(self, entries: list[Entry]):
        self._single: dict[str, Entry] = {}
        self._dirs: list[tuple[str, Entry]] = []
        for e in entries:
            if e.is_directory:
                self._dirs.append((os.path.normpath(e.path), e))
            else:
                self._single[os.path.normpath(e.path)] = e
        # Longest (most specific) directory first.
        self._dirs.sort(key=lambda re: len(re[0]), reverse=True)

    def resolve(self, path: str) -> Optional[Entry]:
        p = os.path.normpath(path)
        entry = self._single.get(p)
        if entry is not None:
            return entry
        for dirpath, e in self._dirs:
            if p.startswith(dirpath + os.sep) and (e.recursive or os.path.dirname(p) == dirpath):
                return e
        return None

    def watch_dirs(self) -> list[tuple[str, bool]]:
        """Return deduped ``(directory, recursive)`` pairs to schedule.

        Single-file entries are watched via their parent directory (watchdog
        watches directories, not files), non-recursively.
        """
        dirs: dict[str, bool] = {}
        for p in self._single:
            dirs.setdefault(os.path.dirname(p), False)
        for dirpath, e in self._dirs:
            dirs[dirpath] = bool(e.recursive) or dirs.get(dirpath, False)
        return list(dirs.items())


class MirrorEventHandler:
    """Duck-typed watchdog handler: watchdog only needs a ``dispatch(event)``.

    Deliberately does no Redis I/O -- it only marks work for the mirror loop so
    the watch thread never blocks.
    """

    def __init__(
        self,
        resolver: PathResolver,
        mark_dirty: Callable[[Entry], None],
        mark_delete: Callable[[Entry, str], None],
    ):
        self._resolver = resolver
        self._mark_dirty = mark_dirty
        self._mark_delete = mark_delete

    def dispatch(self, event) -> None:
        if getattr(event, "is_directory", False):
            return
        event_type = getattr(event, "event_type", None)
        if event_type == EVENT_CLOSED:
            self._dirty(event.src_path)
        elif event_type == EVENT_MOVED:
            dest = getattr(event, "dest_path", None) or event.src_path
            self._dirty(dest)
            # The move is observed, so honor it: if the OLD path was a tracked
            # entry (a renamed single file, or a child inside a watched dir), its
            # backend key must be dropped or a later restore revives the file at
            # the old location. Safe against atomic write-temp-then-rename -- the
            # drain only deletes when the source path is actually gone and
            # store.delete is idempotent, so a move-then-recreate is a no-op.
            if event.src_path != dest:
                src_entry = self._resolver.resolve(event.src_path)
                if src_entry is not None:
                    log.debug(
                        "watchdog move: queuing delete for old path %s -> entry %s",
                        event.src_path,
                        src_entry.path,
                    )
                    self._mark_delete(src_entry, event.src_path)
        elif event_type == EVENT_DELETED:
            entry = self._resolver.resolve(event.src_path)
            if entry is not None:
                log.debug("watchdog deleted %s -> entry %s", event.src_path, entry.path)
                self._mark_delete(entry, event.src_path)

    def _dirty(self, path: str) -> None:
        entry = self._resolver.resolve(path)
        if entry is not None:
            log.debug("watchdog change %s -> entry %s", path, entry.path)
            self._mark_dirty(entry)


def build_observer(resolver: PathResolver, handler: MirrorEventHandler):
    """Create, schedule, and return a watchdog ``Observer`` (not started).

    Missing watch directories are created; a directory that cannot be watched is
    logged and skipped (the periodic full scan still covers it).
    """
    from watchdog.observers import Observer

    observer = Observer()
    scheduled = 0
    for directory, recursive in resolver.watch_dirs():
        try:
            if not os.path.isdir(directory):
                log.info("creating missing watch directory %s", directory)
            os.makedirs(directory, exist_ok=True)
            observer.schedule(handler, directory, recursive=recursive)
            log.info("watching %s (recursive=%s)", directory, recursive)
            scheduled += 1
        except OSError as exc:
            log.error("cannot watch %s: %s (relying on periodic scan)", directory, exc)
    log.info("watchdog scheduled %d watch(es)", scheduled)
    return observer
