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

"""Classify Redis failures into a small, stable set of reasons (HLD 8.6.2).

A sidecar that is alive but cannot write is invisible to Kubernetes probes and
to Redis Sentinel (which only checks reachability/topology). The remediation,
however, depends on *why* the write failed -- and most causes are NOT fixed by
a Sentinel failover because the replicas share the same data and config:

    reason       typical cause                       failover helps?
    ---------    --------------------------------    ----------------
    oom          maxmemory reached (OOM)             no  (replica is full too)
    noreplicas   min-replicas-to-write not met       no  (often worse)
    noauth       wrong password / NOAUTH / WRONGPASS no  (same auth everywhere)
    noperm       ACL denies the command (NOPERM)     no
    misconf      AOF/RDB write error (MISCONF)       maybe (if node-local)
    readonly     client hit a replica (READONLY)     no  (re-resolve master)
    loading      replica still loading dataset       no  (transient)
    conn         connection refused/reset/timeout    n/a (re-discover/retry)
    timeout      socket timeout                       n/a
    response     other server-side ResponseError     depends
    local_io     local file read error (not Redis)   n/a (not a Redis fault)
    other        anything unclassified               unknown

Classification is done by inspecting the exception's class names and message
WITHOUT importing redis-py, so this module stays stdlib-only and unit testable
with fakes (matching the rest of the package's lazy-import discipline).
"""

from __future__ import annotations

# Canonical, fixed label set. Pre-seeded to 0 in metrics so every series is
# present for dashboards/alerts before the first error occurs.
REDIS_ERROR_REASONS: tuple[str, ...] = (
    "oom",
    "noreplicas",
    "noauth",
    "noperm",
    "misconf",
    "readonly",
    "loading",
    "conn",
    "timeout",
    "response",
    "local_io",
    "other",
)

# redis-py exception class name -> reason. Matched by name (not isinstance) so
# this module never imports redis-py and stays unit testable with fakes. The
# lookup walks the exception's MRO most-derived-first, so a subclass wins over
# its base -- e.g. a specific ``ReadOnlyError`` is classified before the shared
# ``ResponseError`` it inherits from.
_CLASS_REASONS: dict[str, str] = {
    "OutOfMemoryError": "oom",
    "ReadOnlyError": "readonly",
    "NoPermissionError": "noperm",
    "AuthenticationError": "noauth",
    "AuthenticationWrongNumberOfArgsError": "noauth",
    "BusyLoadingError": "loading",
    "TimeoutError": "timeout",
    "ConnectionError": "conn",
    "ResponseError": "response",
}


def classify_redis_error(exc: BaseException) -> str:
    """Map an exception to one of :data:`REDIS_ERROR_REASONS`.

    Message-coded server errors (shared ``ResponseError`` class) are matched
    first because they are the most specific; redis-py exception class names are
    the fallback. Never raises -- an unknown exception classifies as ``other``.
    """
    if isinstance(exc, OSError):
        return "local_io"

    msg = str(exc).upper()
    # Redis server error string codes (most specific first). Substring matching,
    # so this stays an ordered chain rather than a dict lookup.
    if "OOM " in msg or "OUT OF MEMORY" in msg or "OUTOFMEMORY" in msg:
        return "oom"
    if "NOREPLICAS" in msg:
        return "noreplicas"
    if "MISCONF" in msg:
        return "misconf"
    if "READONLY" in msg or "READ ONLY REPLICA" in msg:
        return "readonly"
    if "WRONGPASS" in msg or "NOAUTH" in msg:
        return "noauth"
    if "NOPERM" in msg:
        return "noperm"
    if "LOADING" in msg:
        return "loading"

    # redis-py exception classes: first reason found along the MRO wins.
    for cls in type(exc).__mro__:
        reason = _CLASS_REASONS.get(cls.__name__)
        if reason is not None:
            return reason
    return "other"
