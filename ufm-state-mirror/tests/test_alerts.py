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

"""Tests for the StateMirror Prometheus alert contract."""

from pathlib import Path

import yaml

RULE_PATH = Path(__file__).resolve().parents[1] / "deploy" / "state-mirror-prometheusrule.yaml"


def _rule_text() -> str:
    return RULE_PATH.read_text(encoding="utf-8")


def _rule_doc() -> dict:
    return yaml.safe_load(_rule_text())


def _alert(name: str) -> dict:
    rules = _rule_doc()["spec"]["groups"][0]["rules"]
    return next(rule for rule in rules if rule["alert"] == name)


def test_prometheusrule_contract_is_valid_yaml():
    doc = _rule_doc()
    assert doc["apiVersion"] == "monitoring.coreos.com/v1"
    assert doc["kind"] == "PrometheusRule"


def test_configmap_toolarge_alert_is_shipped():
    alert = _alert("StateMirrorConfigMapTooLarge")
    assert (
        alert["expr"].strip()
        == 'increase(state_mirror_backend_errors_total{reason="toolarge"}[5m]) > 0'
    )
    assert alert["for"] == "5m"
    assert alert["labels"]["severity"] == "critical"
    assert alert["labels"]["component"] == "state-mirror"


def test_configmap_toolarge_alert_documents_remediation():
    description = _alert("StateMirrorConfigMapTooLarge")["annotations"]["description"]
    assert "ConfigMap" in description
    assert "not durable" in description
    assert "BYO" in description
    assert "Redis/Valkey" in description
