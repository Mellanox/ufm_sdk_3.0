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

"""Classify Kubernetes API failures into a small, stable set of reasons.

The ConfigMap backend (HLD 5.3.x) talks to the apiserver, so its failure modes
differ from Redis -- and, like Redis, a sidecar that is alive but cannot write
is invisible to probes. The remediation depends on *why* the write failed:

    reason       typical cause                              remediation
    ---------    ----------------------------------------   -----------------------
    forbidden    RBAC denies the verb (403)                 fix Role/RoleBinding
    notfound     object/namespace absent (404)              bootstrap path / benign
    conflict     resourceVersion clash (409)                retry read-modify-write
    toolarge     object exceeds the ~1 MiB etcd limit (413) shrink / use Redis
    invalid      object rejected by validation (422)        fix payload
    conn         connection refused/reset/DNS               apiserver reachability
    timeout      socket / read timeout                      transient, retry
    server       apiserver 5xx                              transient, retry
    other        anything unclassified                      unknown

Classification inspects the exception's ``status`` attribute and class names
WITHOUT importing the kubernetes client, so this module stays stdlib-only and
unit testable with fakes (matching the package's lazy-import discipline).
"""

from __future__ import annotations

# Canonical, fixed label set. Pre-seeded to 0 in metrics so every series is
# present for dashboards/alerts before the first error occurs.
K8S_ERROR_REASONS: tuple[str, ...] = (
    "forbidden",
    "notfound",
    "conflict",
    "toolarge",
    "invalid",
    "conn",
    "timeout",
    "server",
    "other",
)

_STATUS_REASONS: dict[int, str] = {
    403: "forbidden",
    404: "notfound",
    409: "conflict",
    413: "toolarge",
    422: "invalid",
}


def _status_code(exc: BaseException) -> int | None:
    raw = getattr(exc, "status", None)
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def classify_k8s_error(exc: BaseException) -> str:
    """Map an exception to one of :data:`K8S_ERROR_REASONS`.

    HTTP status codes (carried by ``ApiException.status``) are the most specific
    signal and are matched first; transport exception class names and message
    text are the fallback. Never raises -- an unknown exception is ``other``.
    """
    status = _status_code(exc)
    if status is not None:
        mapped = _STATUS_REASONS.get(status)
        if mapped:
            return mapped
        if 500 <= status < 600:
            return "server"

    names = {c.__name__ for c in type(exc).__mro__}
    if "ReadTimeoutError" in names or "TimeoutError" in names:
        return "timeout"
    if (
        "MaxRetryError" in names
        or "NewConnectionError" in names
        or "ConnectionError" in names
        or "ProtocolError" in names
    ):
        return "conn"

    msg = str(exc).upper()
    if "TOO LARGE" in msg or "REQUESTENTITYTOOLARGE" in msg or "REQUEST ENTITY TOO LARGE" in msg:
        return "toolarge"
    if "TIMED OUT" in msg or "TIMEOUT" in msg:
        return "timeout"
    if "CONNECTION REFUSED" in msg or "CONNECTION RESET" in msg or "NAME OR SERVICE" in msg:
        return "conn"
    if isinstance(exc, OSError):
        return "conn"
    return "other"
