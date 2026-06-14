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

"""Centralized logging setup for the StateMirror sidecar.

The sidecar always logs to **stdout** -- the canonical place for container logs
(kubectl logs / log aggregation). It can *additionally* log to a rotating file
under the UFM log directory (``/opt/ufm/files/log``) when
``STATE_MIRROR_LOG_TO_FILE`` is enabled, so its activity sits alongside the rest
of UFM's logs on the shared volume. File logging degrades gracefully to
stdout-only if the directory is not writable.
"""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

DEFAULT_LOG_DIR = "/opt/ufm/files/log"
LOG_FILE_NAME = "state_mirror.log"
_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_MAX_BYTES = 10485760  # 10 MiB
_BACKUP_COUNT = 5

_configured = False


def setup_logging(component: str) -> logging.Logger:
    """Configure root logging once and return the component logger.

    ``component`` is e.g. ``"state_mirror.restore"`` or
    ``"state_mirror.mirror"``. Safe to call more than once; only the first call
    installs handlers.
    """
    global _configured
    root = logging.getLogger()
    if not _configured:
        level = _resolve_level()
        root.setLevel(level)
        formatter = logging.Formatter(_LOG_FORMAT)

        stream = logging.StreamHandler(stream=sys.stdout)
        stream.setFormatter(formatter)
        root.addHandler(stream)

        log = logging.getLogger(component)
        _maybe_add_file_handler(root, formatter, log)
        _configured = True
        log.info(
            "logging initialized (level=%s, component=%s)",
            logging.getLevelName(level),
            component,
        )
    return logging.getLogger(component)


def _resolve_level() -> int:
    raw = os.environ.get("STATE_MIRROR_LOG_LEVEL", "INFO").upper()
    level = logging.getLevelName(raw)
    if isinstance(level, int):
        return level
    return logging.INFO


def _maybe_add_file_handler(
    root: logging.Logger, formatter: logging.Formatter, log: logging.Logger
) -> None:
    if os.environ.get("STATE_MIRROR_LOG_TO_FILE", "true").lower() != "true":
        return
    log_dir = os.environ.get("STATE_MIRROR_LOG_DIR", DEFAULT_LOG_DIR)
    path = os.path.join(log_dir, LOG_FILE_NAME)
    try:
        os.makedirs(log_dir, exist_ok=True)
        handler = RotatingFileHandler(
            path, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, encoding="utf-8"
        )
        handler.setFormatter(formatter)
        root.addHandler(handler)
        log.info("file logging enabled at %s", path)
    except OSError as exc:
        log.warning("file logging to %s unavailable (%s); continuing on stdout only", path, exc)
