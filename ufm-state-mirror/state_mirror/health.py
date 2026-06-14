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

"""Readiness / liveness / metrics HTTP server for the sidecar (HLD 8.3 / R3).

Exposes three endpoints on a small threaded HTTP server:

    /ready    200 once restore/initial-scan is done and the watcher is armed;
              503 otherwise. Gates UFM startup via the pod's native sidecar
              readiness ordering.
    /healthz  liveness of the *mirror loop itself*. Deliberately does NOT fail
              when Redis is unreachable -- a Redis outage must not get the pod
              killed (that would lose the emptyDir). Redis health is surfaced
              through metrics/alerts instead (HLD 8.6).
    /metrics  Prometheus text exposition of the gauges/counters below.

``HealthState`` is the thread-safe shared state updated by the mirror loop; the
HTTP handlers only read snapshots of it.
"""

from __future__ import annotations

import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from state_mirror.redis_errors import REDIS_ERROR_REASONS

log = logging.getLogger(__name__)

DEFAULT_PORT = 9180
LIVENESS_TIMEOUT_S = 30.0


class HealthState:
    """Mutable, thread-safe view of the sidecar's health and counters."""

    def __init__(self):
        self._lock = threading.Lock()
        self.watching_started = False
        self.startup_scan_done = False
        self.watchdog_active = False
        self.loop_started = False
        self.last_loop_tick = 0.0
        self.redis_reachable = False
        self.last_redis_write = 0.0
        self.redis_errors = {reason: 0 for reason in REDIS_ERROR_REASONS}
        self.mirror_ops_total = 0
        self.full_scans_total = 0
        self.events_total = 0
        self.unexpected_delete_total = 0
        self.dropped_events_total = 0
        self.dirty_queue_depth = 0
        self.pending_deletes = 0

    def mark_watching(self, watchdog_active: bool) -> None:
        with self._lock:
            self.watching_started = True
            self.watchdog_active = watchdog_active

    def mark_startup_scan_done(self) -> None:
        with self._lock:
            self.startup_scan_done = True

    def tick(self, dirty_depth: int, pending_deletes: int) -> None:
        with self._lock:
            self.loop_started = True
            self.last_loop_tick = time.monotonic()
            self.dirty_queue_depth = dirty_depth
            self.pending_deletes = pending_deletes

    def record_redis_ok(self) -> None:
        with self._lock:
            self.redis_reachable = True
            self.last_redis_write = time.time()

    def record_redis_down(self, reason: str = "other") -> None:
        with self._lock:
            self.redis_reachable = False
            if reason not in self.redis_errors:
                reason = "other"
            self.redis_errors[reason] += 1

    def add_mirror_ops(self, n: int) -> None:
        with self._lock:
            self.mirror_ops_total += n

    def inc_full_scans(self) -> None:
        with self._lock:
            self.full_scans_total += 1

    def inc_events(self) -> None:
        with self._lock:
            self.events_total += 1

    def inc_dropped_events(self, n: int = 1) -> None:
        with self._lock:
            self.dropped_events_total += n

    def is_ready(self) -> bool:
        with self._lock:
            return self.watching_started and self.startup_scan_done

    def is_alive(self, now: float | None = None, timeout: float = LIVENESS_TIMEOUT_S) -> bool:
        if now is None:
            now = time.monotonic()
        with self._lock:
            if not self.loop_started:
                return True
            return (now - self.last_loop_tick) <= timeout

    def snapshot(self) -> dict:
        with self._lock:
            snap = dict(self.__dict__)
            snap["redis_errors"] = dict(self.redis_errors)
        return snap


def render_metrics(state: HealthState) -> str:
    """Render the Prometheus text exposition for the current state."""
    snap = state.snapshot()
    lines: list[str] = []

    def gauge(name: str, help_text: str, value) -> None:
        lines.append(f"# HELP {name} {help_text}")
        lines.append(f"# TYPE {name} gauge")
        lines.append(f"{name} {value}")

    def counter(name: str, help_text: str, value) -> None:
        lines.append(f"# HELP {name} {help_text}")
        lines.append(f"# TYPE {name} counter")
        lines.append(f"{name} {value}")

    gauge("state_mirror_ready", "1 if the sidecar is ready", int(state.is_ready()))
    gauge(
        "state_mirror_redis_reachable",
        "1 if Redis was reachable on the last op",
        int(snap["redis_reachable"]),
    )
    gauge(
        "state_mirror_watchdog_active",
        "1 if the watchdog observer is running",
        int(snap["watchdog_active"]),
    )
    gauge(
        "state_mirror_last_redis_write_timestamp_seconds",
        "Unix time of the last successful Redis write (0 if never)",
        snap["last_redis_write"],
    )
    gauge("state_mirror_dirty_queue_depth", "Entries pending mirror", snap["dirty_queue_depth"])
    gauge("state_mirror_pending_deletes", "Deletes pending propagation", snap["pending_deletes"])
    counter(
        "state_mirror_mirror_ops_total", "Total Redis write/delete ops", snap["mirror_ops_total"]
    )
    counter("state_mirror_full_scans_total", "Total full reconcile scans", snap["full_scans_total"])
    counter("state_mirror_events_total", "Total watchdog change/delete marks", snap["events_total"])
    counter(
        "state_mirror_unexpected_delete_total",
        "Local deletes not propagated to Redis (drift)",
        snap["unexpected_delete_total"],
    )
    counter(
        "state_mirror_dropped_events_total",
        "Delete marks dropped from a full bounded queue (D2 drop policy); "
        "recovered by the next full-scan delete reconcile",
        snap["dropped_events_total"],
    )

    lines.append("# HELP state_mirror_redis_errors_total Redis op errors by classified reason")
    lines.append("# TYPE state_mirror_redis_errors_total counter")
    for reason, count in sorted(snap["redis_errors"].items()):
        lines.append(f'state_mirror_redis_errors_total{{reason="{reason}"}} {count}')

    return "\n".join(lines) + "\n"


def handle_request(path: str, state: HealthState) -> tuple[int, str, bytes]:
    """Pure router: map a request path to ``(status, content_type, body)``."""
    if path == "/ready":
        if state.is_ready():
            return 200, "text/plain", b"ready\n"
        return 503, "text/plain", b"not ready\n"
    if path == "/healthz":
        if state.is_alive():
            return 200, "text/plain", b"ok\n"
        return 503, "text/plain", b"unhealthy\n"
    if path == "/metrics":
        return 200, "text/plain; version=0.0.4", render_metrics(state).encode("utf-8")
    return 404, "text/plain", b"not found\n"


def _make_handler(state: HealthState):
    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 - required by BaseHTTPRequestHandler
            path = self.path.split("?", 1)[0]
            status, content_type, body = handle_request(path, state)
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):  # silence default stderr access logging
            pass

    return _Handler


class HealthServer:
    """Runs :func:`handle_request` over HTTP in a daemon thread. Fail-soft."""

    def __init__(self, state: HealthState, port: int = DEFAULT_PORT, host: str = "0.0.0.0"):
        self.state = state
        self.port = port
        self.host = host
        self._httpd = None
        self._thread = None

    def start(self) -> bool:
        try:
            self._httpd = ThreadingHTTPServer((self.host, self.port), _make_handler(self.state))
        except OSError as exc:
            log.error("health server failed to bind %s:%d: %s", self.host, self.port, exc)
            return False
        self._thread = threading.Thread(
            target=self._httpd.serve_forever,
            name="state-mirror-health",
            daemon=True,
        )
        self._thread.start()
        log.info("health/metrics server listening on %s:%d", self.host, self.port)
        return True

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
