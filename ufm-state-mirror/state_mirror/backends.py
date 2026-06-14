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

"""Build the per-backend ``Store`` map for a classifier (HLD 5.2.3, 5.3.11).

The init container and the runtime sidecar both bind each classifier entry to a
``Store`` by its ``backend``. This module decides *which* backends a given
classifier actually needs and constructs only those, so a pure-Redis deployment
never imports the kubernetes client (and never needs ConfigMap RBAC), and a
ConfigMap-only deployment never dials Redis. The backend constructors are
injected, keeping this routing logic unit-testable without either dependency.
"""

from __future__ import annotations

import logging
from typing import Callable

from state_mirror.classifier import Backend, Classifier
from state_mirror.store import Store

log = logging.getLogger(__name__)


def default_redis_store() -> Store:
    """Build the production Redis store from the pod environment (HLD 5.2)."""
    from state_mirror.redis_client import RedisConfig, master_client
    from state_mirror.store import RedisStore

    return RedisStore(master_client(RedisConfig.from_env()))


def default_configmap_store() -> Store:
    """Build the production ConfigMap store via in-cluster config (HLD 5.3.x).

    Imported lazily so a pure-Redis deployment never loads the kubernetes
    client (and a unit test never needs it installed).
    """
    from state_mirror.k8s_client import configmap_api_from_env
    from state_mirror.store import ConfigMapStore

    return ConfigMapStore(configmap_api_from_env())


def selected_backends(classifier: Classifier) -> set[Backend]:
    """Return the distinct set of backends referenced by the classifier."""
    return {entry.backend for entry in classifier.entries}


def build_stores(
    classifier: Classifier,
    *,
    redis_factory: Callable[[], Store],
    configmap_factory: Callable[[], Store],
) -> dict[Backend, Store]:
    """Construct exactly the stores the classifier's entries require.

    A factory is invoked only when at least one entry selects that backend, so
    importing/connecting a backend is pay-for-what-you-use.
    """
    backends = selected_backends(classifier)
    counts = {b: sum(1 for e in classifier.entries if e.backend is b) for b in backends}
    stores: dict[Backend, Store] = {}
    if Backend.REDIS in backends:
        log.info("Redis backend selected by %d classifier entr(y/ies)", counts[Backend.REDIS])
        stores[Backend.REDIS] = redis_factory()
    if Backend.CONFIGMAP in backends:
        log.info(
            "ConfigMap backend selected by %d classifier entr(y/ies)", counts[Backend.CONFIGMAP]
        )
        stores[Backend.CONFIGMAP] = configmap_factory()
    return stores
