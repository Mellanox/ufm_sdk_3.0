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

"""StateMirror per-handler logic (HLD 5.3.2)."""

from collections.abc import Mapping

from state_mirror.classifier import Entry, Handler
from state_mirror.handlers.atomic_blob import AtomicBlobHandler
from state_mirror.handlers.base import BaseHandler
from state_mirror.handlers.blob import BlobHandler
from state_mirror.handlers.directory import DirectoryHandler
from state_mirror.handlers.sqlite import SqliteHandler

_REGISTRY = {
    Handler.BLOB: BlobHandler,
    Handler.ATOMIC_BLOB: AtomicBlobHandler,
    Handler.DIRECTORY: DirectoryHandler,
    Handler.SQLITE: SqliteHandler,
}


def make_handler(entry: Entry, store, ufm_version: str, written_by: str) -> BaseHandler:
    """Instantiate the handler class for a classifier entry over its store.

    ``store`` is either a single :class:`~state_mirror.store.Store` (used for
    every entry) or a mapping of :class:`~state_mirror.classifier.Backend` to
    ``Store``, in which case the entry's ``backend`` selects the one to bind --
    this is what routes a ``backend: configmap`` entry to the ConfigMap store
    while everything else stays on Redis (HLD 5.2.3).
    """
    try:
        cls = _REGISTRY[entry.handler]
    except KeyError:  # pragma: no cover - guarded by classifier validation
        raise ValueError(f"no handler registered for {entry.handler}") from None
    resolved = store[entry.backend] if isinstance(store, Mapping) else store
    return cls(entry, resolved, ufm_version, written_by)


__all__ = [
    "BaseHandler",
    "BlobHandler",
    "AtomicBlobHandler",
    "DirectoryHandler",
    "SqliteHandler",
    "make_handler",
]
