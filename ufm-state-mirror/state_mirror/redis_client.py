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

"""Redis/Valkey client construction with Sentinel-aware master discovery
(HLD 5.2, 8.6).

The sidecar always writes to the *current* Redis master. Redis/Valkey is
bring-your-own (UFM does not deploy it): when the operator points the sidecar
at a Sentinel-managed deployment, the master is discovered through Sentinel so a
failover is handled by re-resolving ``master_for`` rather than reconnecting to a
fixed address. A direct (non-Sentinel) endpoint is also supported for a
single-node Redis.

redis-py is imported lazily so the rest of the package (classifier, wire,
handlers, health) stays import-light and unit testable without the dependency.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Optional

log = logging.getLogger(__name__)


def _env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _parse_hosts(raw: str) -> list[tuple[str, int]]:
    """Parse ``"h1:26379,h2:26379"`` into ``[("h1", 26379), ("h2", 26379)]``."""
    hosts: list[tuple[str, int]] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            host, _, port = item.rpartition(":")
            hosts.append((host, int(port)))
        else:
            hosts.append((item, 26379))
    return hosts


@dataclass
class RedisConfig:
    """Connection settings, populated from the pod's environment (HLD 5.2)."""

    sentinel_hosts: list[tuple[str, int]] = field(default_factory=list)
    master_name: str = "ufm"
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    sentinel_password: Optional[str] = None
    use_tls: bool = False
    ca_cert: Optional[str] = None
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0

    @classmethod
    def from_env(cls) -> "RedisConfig":
        sentinel_raw = os.environ.get("REDIS_SENTINEL_HOSTS", "")
        return cls(
            sentinel_hosts=_parse_hosts(sentinel_raw),
            master_name=os.environ.get("REDIS_MASTER_NAME", "ufm"),
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=int(os.environ.get("REDIS_PORT", "6379")),
            password=os.environ.get("REDIS_PASSWORD") or None,
            sentinel_password=os.environ.get("REDIS_SENTINEL_PASSWORD") or None,
            use_tls=_env_bool("REDIS_USE_TLS", False),
            ca_cert=os.environ.get("REDIS_CA_CERT") or None,
            socket_timeout=float(os.environ.get("REDIS_SOCKET_TIMEOUT", "5.0")),
            socket_connect_timeout=float(os.environ.get("REDIS_CONNECT_TIMEOUT", "5.0")),
        )

    def _common_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "socket_timeout": self.socket_timeout,
            "socket_connect_timeout": self.socket_connect_timeout,
        }
        if self.password:
            kwargs["password"] = self.password
        if self.use_tls:
            kwargs["ssl"] = True
            if self.ca_cert:
                kwargs["ssl_ca_certs"] = self.ca_cert
        return kwargs


def master_client(config: RedisConfig):
    """Return a redis client bound to the current master.

    When Sentinel hosts are configured the client resolves the master via
    ``Sentinel.master_for`` so it follows failovers automatically; otherwise it
    connects to the direct ``host:port`` endpoint.
    """
    import redis

    common = config._common_kwargs()
    if config.sentinel_hosts:
        from redis.sentinel import Sentinel

        sentinel_kwargs: dict[str, Any] = {}
        if config.sentinel_password:
            sentinel_kwargs["password"] = config.sentinel_password
        if config.use_tls:
            sentinel_kwargs["ssl"] = True
            if config.ca_cert:
                sentinel_kwargs["ssl_ca_certs"] = config.ca_cert
        log.info(
            "connecting via Sentinel %s (master=%s)",
            config.sentinel_hosts,
            config.master_name,
        )
        sentinel = Sentinel(
            config.sentinel_hosts,
            sentinel_kwargs=sentinel_kwargs,
            **common,
        )
        return sentinel.master_for(config.master_name, **common)

    log.info("connecting directly to %s:%d", config.host, config.port)
    return redis.Redis(host=config.host, port=config.port, **common)
