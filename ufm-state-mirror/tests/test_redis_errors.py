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

"""Unit tests for Redis error classification."""

import pytest

from state_mirror.redis_errors import REDIS_ERROR_REASONS, classify_redis_error


# Mimic the redis-py exception hierarchy by class name (classify matches on the
# class name via __mro__, without importing redis-py).
class RedisError(Exception):
    pass


class ResponseError(RedisError):
    pass


class ConnectionError(RedisError):  # noqa: A001 - intentionally shadows builtin
    pass


class TimeoutError(RedisError):  # noqa: A001 - intentionally shadows builtin
    pass


class ReadOnlyError(ResponseError):
    pass


class OutOfMemoryError(ResponseError):
    pass


class NoPermissionError(ResponseError):
    pass


class AuthenticationError(ResponseError):
    pass


class BusyLoadingError(ResponseError):
    pass


class TestMessageCoded:
    @pytest.mark.parametrize(
        ("message", "expected"),
        [
            ("OOM command not allowed when used memory > 'maxmemory'.", "oom"),
            ("NOREPLICAS Not enough good replicas to write.", "noreplicas"),
            ("MISCONF Redis is configured to save RDB snapshots but is failing.", "misconf"),
            ("READONLY You can't write against a read only replica.", "readonly"),
            ("NOAUTH Authentication required.", "noauth"),
            ("WRONGPASS invalid username-password pair", "noauth"),
            ("NOPERM this user has no permissions to run the 'set' command", "noperm"),
            ("LOADING Redis is loading the dataset in memory", "loading"),
        ],
    )
    def test_server_string_codes(self, message, expected):
        assert classify_redis_error(ResponseError(message)) == expected


class TestExceptionClasses:
    @pytest.mark.parametrize(
        ("exc", "expected"),
        [
            (OutOfMemoryError("server full"), "oom"),
            (ReadOnlyError("nope"), "readonly"),
            (NoPermissionError("denied"), "noperm"),
            (AuthenticationError("auth"), "noauth"),
            (BusyLoadingError("loading"), "loading"),
            (TimeoutError("timed out"), "timeout"),
            (ConnectionError("refused"), "conn"),
            (ResponseError("some other server error"), "response"),
        ],
    )
    def test_by_class_name(self, exc, expected):
        assert classify_redis_error(exc) == expected

    def test_oserror_is_local_io(self):
        assert classify_redis_error(OSError("disk gone")) == "local_io"

    def test_unknown_is_other(self):
        assert classify_redis_error(ValueError("???")) == "other"

    def test_every_reason_is_known(self):
        for exc in (
            OutOfMemoryError("OOM"),
            ConnectionError("x"),
            OSError("x"),
            ValueError("x"),
        ):
            assert classify_redis_error(exc) in REDIS_ERROR_REASONS
