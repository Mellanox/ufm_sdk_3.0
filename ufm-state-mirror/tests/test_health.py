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

    def test_liveness_ignores_backend_down(self):
        s = HealthState()
        s.tick(0, 0)
        s.record_store_down()
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
        s.record_store_ok()
        s.add_mirror_ops(3)
        s.inc_full_scans()
        s.inc_events()
        text = render_metrics(s)
        assert "state_mirror_ready 1" in text
        assert "state_mirror_backend_reachable 1" in text
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

    def test_backend_errors_series_present_at_zero(self):
        text = render_metrics(HealthState())
        # A reason from each backend's label set is pre-seeded to 0.
        assert 'state_mirror_backend_errors_total{reason="oom"} 0' in text  # redis
        assert 'state_mirror_backend_errors_total{reason="forbidden"} 0' in text  # configmap
        assert 'state_mirror_backend_errors_total{reason="conn"} 0' in text  # shared

    def test_backend_errors_counter_increments_by_reason(self):
        s = HealthState()
        s.record_store_down("oom")
        s.record_store_down("oom")
        s.record_store_down("forbidden")
        text = render_metrics(s)
        assert 'state_mirror_backend_errors_total{reason="oom"} 2' in text
        assert 'state_mirror_backend_errors_total{reason="forbidden"} 1' in text
        assert s.backend_reachable is False

    def test_unknown_reason_buckets_to_other(self):
        s = HealthState()
        s.record_store_down("not-a-real-reason")
        text = render_metrics(s)
        assert 'state_mirror_backend_errors_total{reason="other"} 1' in text

    def test_dropped_events_counter(self):
        s = HealthState()
        assert "state_mirror_dropped_events_total 0" in render_metrics(s)
        s.inc_dropped_events(5)
        assert "state_mirror_dropped_events_total 5" in render_metrics(s)

    def test_unexpected_delete_counter(self):
        s = HealthState()
        assert "state_mirror_unexpected_delete_total 0" in render_metrics(s)
        s.inc_unexpected_deletes(2)
        assert "state_mirror_unexpected_delete_total 3" not in render_metrics(s)
        s.inc_unexpected_deletes()
        assert "state_mirror_unexpected_delete_total 3" in render_metrics(s)

    def test_snapshot_duration_gauge_labeled_by_db(self):
        s = HealthState()
        # Present (with HELP/TYPE) even before any snapshot.
        assert "state_mirror_snapshot_duration_seconds" in render_metrics(s)
        s.set_snapshot_duration("gv.db", 0.42)
        text = render_metrics(s)
        assert 'state_mirror_snapshot_duration_seconds{db="gv.db"} 0.42' in text


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
