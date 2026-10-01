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

"""Kubernetes ConfigMap API adapter for the ConfigMap backend (HLD 5.3.x).

Bridges :class:`state_mirror.store.ConfigMapStore` (which speaks a tiny,
dict-oriented :class:`~state_mirror.store.ConfigMapApi` protocol) to the real
``kubernetes`` client. All translation to/from ``V1ConfigMap`` and the
``404 -> None`` mapping lives here so the store stays backend-neutral and unit
testable with a fake.

The ``kubernetes`` package is imported lazily (inside the factory / methods),
matching redis-py's treatment in :mod:`state_mirror.redis_client`, so importing
the store does not require the dependency to be installed.
"""

from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)

_NAMESPACE_FILE = "/var/run/secrets/kubernetes.io/serviceaccount/namespace"


class K8sConfigMapApi:
    """Namespace-bound adapter over ``CoreV1Api`` for ConfigMap CRUD.

    Returns ``None`` from :meth:`read_cm` and silently absorbs ``404`` from
    :meth:`delete_cm` so the store's bootstrap/idempotent paths work; every
    other ``ApiException`` propagates and is classified by the store.
    """

    def __init__(self, core_v1, namespace: str):
        self._api = core_v1
        self._ns = namespace

    def read_cm(self, name: str):
        from kubernetes.client.exceptions import ApiException

        try:
            cm = self._api.read_namespaced_config_map(name, self._ns)
        except ApiException as exc:
            if exc.status == 404:
                return None
            raise
        return self._to_dict(cm)

    def write_cm(self, name, *, labels, annotations, data, binary_data) -> None:
        from kubernetes import client
        from kubernetes.client.exceptions import ApiException

        def body(resource_version=None):
            return client.V1ConfigMap(
                metadata=client.V1ObjectMeta(
                    name=name,
                    namespace=self._ns,
                    labels=labels or None,
                    annotations=annotations or None,
                    resource_version=resource_version,
                ),
                data=data or None,
                binary_data=binary_data or None,
            )

        # Kubernetes replace requires the current resourceVersion. Re-read and
        # retry a bounded number of times on an optimistic-concurrency conflict;
        # the StateMirror writer is idempotent, so replacing the complete object
        # with the same desired data is safe.
        for attempt in range(3):
            try:
                current = self._api.read_namespaced_config_map(name, self._ns)
            except ApiException as exc:
                if exc.status != 404:
                    raise
                try:
                    self._api.create_namespaced_config_map(self._ns, body())
                    return
                except ApiException as create_exc:
                    if create_exc.status != 409 or attempt == 2:
                        raise
                    continue

            resource_version = current.metadata.resource_version
            try:
                self._api.replace_namespaced_config_map(
                    name, self._ns, body(resource_version=resource_version)
                )
                return
            except ApiException as exc:
                if exc.status != 409 or attempt == 2:
                    raise

    def delete_cm(self, name: str) -> None:
        from kubernetes.client.exceptions import ApiException

        try:
            self._api.delete_namespaced_config_map(name, self._ns)
        except ApiException as exc:
            if exc.status != 404:
                raise

    def write_cm_cas(
        self,
        name,
        *,
        expected_resource_version,
        labels,
        annotations,
        data,
        binary_data,
    ) -> bool:
        """Create-if-absent or resourceVersion-guarded replace."""
        from kubernetes import client
        from kubernetes.client.exceptions import ApiException

        body = client.V1ConfigMap(
            metadata=client.V1ObjectMeta(
                name=name,
                namespace=self._ns,
                labels=labels or None,
                annotations=annotations or None,
                resource_version=expected_resource_version,
            ),
            data=data or None,
            binary_data=binary_data or None,
        )
        try:
            if expected_resource_version is None:
                self._api.create_namespaced_config_map(self._ns, body)
            else:
                self._api.replace_namespaced_config_map(name, self._ns, body)
        except ApiException as exc:
            if exc.status == 409:
                return False
            raise
        return True

    def list_cms(self, label_selector: str) -> list[dict]:
        resp = self._api.list_namespaced_config_map(self._ns, label_selector=label_selector)
        return [self._to_dict(cm) for cm in resp.items]

    @staticmethod
    def _to_dict(cm) -> dict:
        meta = cm.metadata
        return {
            "name": meta.name,
            "resource_version": meta.resource_version,
            "annotations": dict(meta.annotations or {}),
            "data": dict(cm.data or {}),
            "binary_data": dict(cm.binary_data or {}),
        }


def detect_namespace() -> str:
    """Resolve the namespace to write ConfigMaps into.

    Prefers an explicit env override, then the pod's projected namespace via the
    downward API (``POD_NAMESPACE``), then the serviceaccount token's namespace
    file, falling back to ``default``.
    """
    ns = os.environ.get("STATE_MIRROR_NAMESPACE") or os.environ.get("POD_NAMESPACE")
    if ns:
        return ns.strip()
    try:
        with open(_NAMESPACE_FILE, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        log.warning("could not read %s; defaulting namespace to 'default'", _NAMESPACE_FILE)
        return "default"


def configmap_api_from_env() -> K8sConfigMapApi:
    """Build a :class:`K8sConfigMapApi` using in-cluster config (HLD 5.3.x)."""
    from kubernetes import client, config

    config.load_incluster_config()
    namespace = detect_namespace()
    log.info("ConfigMap backend bound to namespace %s", namespace)
    return K8sConfigMapApi(client.CoreV1Api(), namespace)
