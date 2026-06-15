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

"""Select and build the sidecar's single ``Store`` backend (HLD 5.2.3, 5.3.11).

Exactly **one** backend is chosen at install time and used for the entire
sidecar -- there is no per-file routing. The operator sets it once (Helm value
surfaced as the ``STATE_MIRROR_BACKEND`` env var), the init container and the
runtime sidecar both build that one ``Store`` at startup and hand it to every
handler. The default is ``configmap`` (etcd-backed, no external store to run);
``redis`` is the alternative for deployments whose state does not fit the
ConfigMap ~1 MiB object cap.

The backend constructors are injected, keeping selection unit-testable without
the redis-py or kubernetes dependency.
"""

from __future__ import annotations

import logging
import os
from enum import Enum
from typing import Callable

from state_mirror.store import Store

log = logging.getLogger(__name__)


class Backend(str, Enum):
    """The durable backend the sidecar mirrors to (install-wide, HLD 5.2.3)."""

    CONFIGMAP = "configmap"
    REDIS = "redis"


# ConfigMap is the default: no external store to run, state lives in the
# cluster's own etcd (HLD 5.2.3). Redis is opted into for large/high-churn state.
DEFAULT_BACKEND = Backend.CONFIGMAP

BACKEND_ENV = "STATE_MIRROR_BACKEND"


def backend_from_env() -> Backend:
    """Resolve the install-wide backend from ``STATE_MIRROR_BACKEND``.

    Defaults to :data:`DEFAULT_BACKEND` (configmap). Raises ``ValueError`` on an
    unrecognized value so a misconfigured install fails closed at startup rather
    than silently mirroring to the wrong place.
    """
    raw = os.environ.get(BACKEND_ENV, DEFAULT_BACKEND.value).strip().lower()
    try:
        return Backend(raw)
    except ValueError:
        allowed = ", ".join(b.value for b in Backend)
        raise ValueError(f"invalid {BACKEND_ENV} '{raw}' (allowed: {allowed})") from None


def default_redis_store() -> Store:
    """Build the production Redis store from the pod environment (HLD 8.8)."""
    from state_mirror.redis_client import RedisConfig, master_client
    from state_mirror.store import RedisStore

    return RedisStore(master_client(RedisConfig.from_env()))


def default_configmap_store() -> Store:
    """Build the production ConfigMap store via in-cluster config (HLD 5.3.x).

    Imported lazily so a Redis-backend deployment never loads the kubernetes
    client (and a unit test never needs it installed).
    """
    from state_mirror.k8s_client import configmap_api_from_env
    from state_mirror.store import ConfigMapStore

    return ConfigMapStore(configmap_api_from_env())


def build_store(
    backend: Backend,
    *,
    redis_factory: Callable[[], Store] = default_redis_store,
    configmap_factory: Callable[[], Store] = default_configmap_store,
) -> Store:
    """Construct the single ``Store`` for the chosen install-wide backend."""
    if backend is Backend.CONFIGMAP:
        log.info("storage backend: configmap (etcd-backed)")
        return configmap_factory()
    if backend is Backend.REDIS:
        log.info("storage backend: redis (BYO)")
        return redis_factory()
    raise ValueError(f"unsupported backend: {backend!r}")  # pragma: no cover
