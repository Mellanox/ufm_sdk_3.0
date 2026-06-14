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

"""Unit tests for Kubernetes API error classification."""

import pytest

from state_mirror.k8s_errors import K8S_ERROR_REASONS, classify_k8s_error


class _ApiException(Exception):
    """Stand-in for kubernetes.client.exceptions.ApiException (has .status)."""

    def __init__(self, status, message=""):
        super().__init__(message)
        self.status = status


class ReadTimeoutError(Exception):
    """Mirrors urllib3.exceptions.ReadTimeoutError (matched by class name)."""


class MaxRetryError(Exception):
    """Mirrors urllib3.exceptions.MaxRetryError (matched by class name)."""


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (403, "forbidden"),
        (404, "notfound"),
        (409, "conflict"),
        (413, "toolarge"),
        (422, "invalid"),
        (500, "server"),
        (503, "server"),
    ],
)
def test_status_codes(status, expected):
    assert classify_k8s_error(_ApiException(status)) == expected


def test_unmapped_4xx_is_other():
    assert classify_k8s_error(_ApiException(418)) == "other"


def test_timeout_by_class_name():
    assert classify_k8s_error(ReadTimeoutError("nope")) == "timeout"


def test_conn_by_class_name():
    assert classify_k8s_error(MaxRetryError("nope")) == "conn"


def test_oserror_is_conn():
    assert classify_k8s_error(ConnectionRefusedError("refused")) == "conn"


def test_too_large_by_message():
    exc = _ApiException(None, "Request entity too large: limit is 3145728")
    assert classify_k8s_error(exc) == "toolarge"


def test_unknown_is_other():
    assert classify_k8s_error(RuntimeError("boom")) == "other"


def test_every_reason_is_declared():
    # Sampling of inputs must only ever produce declared reasons.
    samples = [
        _ApiException(403),
        _ApiException(404),
        _ApiException(409),
        _ApiException(413),
        _ApiException(422),
        _ApiException(500),
        ReadTimeoutError(),
        MaxRetryError(),
        ConnectionRefusedError(),
        RuntimeError("x"),
    ]
    for exc in samples:
        assert classify_k8s_error(exc) in K8S_ERROR_REASONS
