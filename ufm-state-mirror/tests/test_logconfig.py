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

"""Unit tests for the StateMirror logging setup."""

import logging
from logging.handlers import RotatingFileHandler

import pytest

from state_mirror import logconfig


def _file_handlers():
    return [h for h in logging.getLogger().handlers if isinstance(h, RotatingFileHandler)]


@pytest.fixture(autouse=True)
def _reset_logging():
    """Isolate each test from global logging state.

    pytest attaches its own capture handlers to the root logger, so we snapshot
    and restore the handler list around every test and reset the module's
    one-shot ``_configured`` guard.
    """
    root = logging.getLogger()
    saved_handlers = root.handlers[:]
    saved_level = root.level
    logconfig._configured = False
    yield
    root.handlers[:] = saved_handlers
    root.setLevel(saved_level)
    logconfig._configured = False


class TestResolveLevel:
    def test_default_is_info(self, monkeypatch):
        monkeypatch.delenv("STATE_MIRROR_LOG_LEVEL", raising=False)
        assert logconfig._resolve_level() == logging.INFO

    def test_explicit_level(self, monkeypatch):
        monkeypatch.setenv("STATE_MIRROR_LOG_LEVEL", "debug")
        assert logconfig._resolve_level() == logging.DEBUG

    def test_garbage_falls_back_to_info(self, monkeypatch):
        monkeypatch.setenv("STATE_MIRROR_LOG_LEVEL", "not-a-level")
        assert logconfig._resolve_level() == logging.INFO


class TestSetupLogging:
    def test_stdout_only_when_file_disabled(self, monkeypatch):
        monkeypatch.setenv("STATE_MIRROR_LOG_TO_FILE", "false")
        logconfig.setup_logging("state_mirror.test")
        assert logconfig._configured is True
        assert _file_handlers() == []

    def test_file_handler_created(self, monkeypatch, tmp_path):
        monkeypatch.setenv("STATE_MIRROR_LOG_TO_FILE", "true")
        monkeypatch.setenv("STATE_MIRROR_LOG_DIR", str(tmp_path / "log"))
        logconfig.setup_logging("state_mirror.test")
        logging.getLogger("state_mirror.test").info("hello")
        assert len(_file_handlers()) == 1
        log_file = tmp_path / "log" / logconfig.LOG_FILE_NAME
        assert log_file.exists()
        assert "hello" in log_file.read_text()

    def test_file_failure_degrades_to_stdout(self, monkeypatch, tmp_path):
        afile = tmp_path / "afile"
        afile.write_text("x")
        monkeypatch.setenv("STATE_MIRROR_LOG_TO_FILE", "true")
        monkeypatch.setenv("STATE_MIRROR_LOG_DIR", str(afile / "nested"))
        logconfig.setup_logging("state_mirror.test")
        assert logconfig._configured is True
        assert _file_handlers() == []

    def test_idempotent(self, monkeypatch, tmp_path):
        monkeypatch.setenv("STATE_MIRROR_LOG_TO_FILE", "true")
        monkeypatch.setenv("STATE_MIRROR_LOG_DIR", str(tmp_path / "log"))
        logconfig.setup_logging("state_mirror.test")
        before = len(logging.getLogger().handlers)
        logconfig.setup_logging("state_mirror.test")
        after = len(logging.getLogger().handlers)
        assert after == before
        assert len(_file_handlers()) == 1
