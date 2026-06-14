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

"""Unit tests for the readiness/liveness/metrics server."""

import urllib.error
import urllib.request

from state_mirror.health import HealthServer, HealthState, handle_request, render_metrics


def _get(url):
    """GET returning (status, body), treating HTTP error codes as responses."""
    try:
        with urllib.request.urlopen(url) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


class TestReadiness:
    def test_not_ready_until_milestones(self):
        s = HealthState()
        assert s.is_ready() is False
        s.mark_watching(watchdog_active=True)
        assert s.is_ready() is False
        s.mark_startup_scan_done()
        assert s.is_ready() is True

    def test_ready_route(self):
        s = HealthState()
        status, _ct, body = handle_request("/ready", s)
        assert status == 503
        assert body == b"not ready\n"
        s.mark_watching(watchdog_active=True)
        s.mark_startup_scan_done()
        status, _ct, body = handle_request("/ready", s)
        assert status == 200
        assert body == b"ready\n"


class TestLiveness:
    def test_alive_before_loop_starts(self):
        s = HealthState()
        assert s.is_alive() is True

    def test_alive_with_recent_tick(self):
        s = HealthState()
        s.tick(0, 0)
        assert s.is_alive() is True

    def test_dead_when_loop_stalls(self):
        s = HealthState()
        s.tick(0, 0)
        s.last_loop_tick = 1.0
        assert s.is_alive(now=1000.0, timeout=30.0) is False

    def test_healthz_route(self):
        s = HealthState()
        status, _ct, _body = handle_request("/healthz", s)
        assert status == 200

    def test_liveness_ignores_redis_down(self):
        s = HealthState()
        s.tick(0, 0)
        s.record_redis_down()
        assert s.is_alive() is True


class TestMetrics:
    def test_metrics_route_content_type(self):
        s = HealthState()
        status, content_type, body = handle_request("/metrics", s)
        assert status == 200
        assert "text/plain" in content_type
        assert b"state_mirror_ready" in body

    def test_metrics_reflect_state(self):
        s = HealthState()
        s.mark_watching(watchdog_active=True)
        s.mark_startup_scan_done()
        s.record_redis_ok()
        s.add_mirror_ops(3)
        s.inc_full_scans()
        s.inc_events()
        text = render_metrics(s)
        assert "state_mirror_ready 1" in text
        assert "state_mirror_redis_reachable 1" in text
        assert "state_mirror_watchdog_active 1" in text
        assert "state_mirror_mirror_ops_total 3" in text
        assert "state_mirror_full_scans_total 1" in text
        assert "state_mirror_events_total 1" in text
        assert text.count("# HELP") == text.count("# TYPE")

    def test_unknown_route_404(self):
        s = HealthState()
        status, _ct, body = handle_request("/nope", s)
        assert status == 404
        assert body == b"not found\n"

    def test_redis_errors_series_present_at_zero(self):
        text = render_metrics(HealthState())
        assert 'state_mirror_redis_errors_total{reason="oom"} 0' in text
        assert 'state_mirror_redis_errors_total{reason="conn"} 0' in text

    def test_redis_errors_counter_increments_by_reason(self):
        s = HealthState()
        s.record_redis_down("oom")
        s.record_redis_down("oom")
        s.record_redis_down("readonly")
        text = render_metrics(s)
        assert 'state_mirror_redis_errors_total{reason="oom"} 2' in text
        assert 'state_mirror_redis_errors_total{reason="readonly"} 1' in text
        assert s.redis_reachable is False

    def test_unknown_reason_buckets_to_other(self):
        s = HealthState()
        s.record_redis_down("not-a-real-reason")
        text = render_metrics(s)
        assert 'state_mirror_redis_errors_total{reason="other"} 1' in text

    def test_dropped_events_counter(self):
        s = HealthState()
        assert "state_mirror_dropped_events_total 0" in render_metrics(s)
        s.inc_dropped_events(5)
        assert "state_mirror_dropped_events_total 5" in render_metrics(s)


class TestLiveServer:
    def test_end_to_end_over_http(self):
        s = HealthState()
        server = HealthServer(s, port=0)
        assert server.start() is True
        try:
            port = server._httpd.server_address[1]
            base = f"http://127.0.0.1:{port}"
            status, body = _get(base + "/ready")
            assert status == 503
            assert body == b"not ready\n"
            s.mark_watching(watchdog_active=True)
            s.mark_startup_scan_done()
            status, body = _get(base + "/ready")
            assert status == 200
            assert body == b"ready\n"
            status, body = _get(base + "/metrics")
            assert b"state_mirror_ready 1" in body
        finally:
            server.stop()
