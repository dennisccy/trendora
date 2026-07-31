"""TC-12 (ops-hardening iter-39) — `app.logging_config.configure_app_logging()` actually gets an
`.info()`-level record from a `trendora.*` logger to a configured handler, closing the gap iter-38
discovered live: with no root-logger handler/level configured anywhere in the app, Python's global
WARNING-only `logging.lastResort` fallback was the only thing ever writing these records, so an
`.info()` call was silently dropped before it ever reached `logs/backend.log`."""
from __future__ import annotations

import io
import logging
import sys

from app import logging_config


def test_configure_app_logging_lets_info_reach_configured_handler(monkeypatch):
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    saved_level = root.level
    for h in saved_handlers:
        root.removeHandler(h)
    # mirror the real pre-fix starting point: an unconfigured root sits at the module default
    # (WARNING) with zero handlers of its own.
    root.setLevel(logging.WARNING)

    stream = io.StringIO()
    monkeypatch.setattr(sys, "stderr", stream)
    # force a fresh configure even if some earlier test/import already ran it this session.
    monkeypatch.setattr(logging_config, "_CONFIGURED", False)
    try:
        logging_config.configure_app_logging()

        probe = logging.getLogger("trendora.test_logging_config")
        probe.info("TC-12 probe line: %s", "hello")

        assert "TC-12 probe line: hello" in stream.getvalue(), (
            "an .info() call on a trendora.* logger did not reach the handler "
            "configure_app_logging() is supposed to attach"
        )
    finally:
        for h in list(root.handlers):
            root.removeHandler(h)
        for h in saved_handlers:
            root.addHandler(h)
        root.setLevel(saved_level)


def test_configure_app_logging_does_not_double_write_self_handled_loggers(monkeypatch):
    """iter-39 audit (B1) regression — `trendora.backtest` and `trendora.mcp_backtest` attach a
    handler to their OWN logger (iter-18) and keep `propagate = True` for caplog. Once a root
    handler exists, an unfiltered root handler emits a SECOND copy of each of their records: every
    `backtest_timing` line was written to `logs/backend.log` twice (confirmed live). A logger that
    carries its own handler must keep exactly ONE line; a logger without one must still get the
    root handler's copy."""
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    saved_level = root.level
    for h in saved_handlers:
        root.removeHandler(h)
    root.setLevel(logging.WARNING)

    root_stream = io.StringIO()
    own_stream = io.StringIO()
    monkeypatch.setattr(sys, "stderr", root_stream)
    monkeypatch.setattr(logging_config, "_CONFIGURED", False)

    # mirror app/api/backtest.py's real shape: own handler + level, propagate left True.
    self_handled = logging.getLogger("trendora.test_self_handled")
    self_handled.setLevel(logging.INFO)
    own_handler = logging.StreamHandler(own_stream)
    self_handled.addHandler(own_handler)
    try:
        logging_config.configure_app_logging()

        self_handled.info("timing_probe one")
        assert own_stream.getvalue().count("timing_probe one") == 1, "the logger's own handler must still emit"
        assert "timing_probe one" not in root_stream.getvalue(), (
            "the root handler emitted a SECOND copy of a record its own logger already handled — "
            "this is the duplicate-line regression B1 found live in logs/backend.log"
        )

        # a logger WITHOUT its own handler must still reach the root handler.
        logging.getLogger("trendora.test_plain").info("plain_probe two")
        assert "plain_probe two" in root_stream.getvalue()
    finally:
        self_handled.removeHandler(own_handler)
        self_handled.setLevel(logging.NOTSET)
        for h in list(root.handlers):
            root.removeHandler(h)
        for h in saved_handlers:
            root.addHandler(h)
        root.setLevel(saved_level)


def test_configure_app_logging_is_idempotent(monkeypatch):
    """A second call must not attach a second handler (which would double-emit every record)."""
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    saved_level = root.level
    for h in saved_handlers:
        root.removeHandler(h)
    root.setLevel(logging.WARNING)

    monkeypatch.setattr(logging_config, "_CONFIGURED", False)
    try:
        logging_config.configure_app_logging()
        count_after_first = len(root.handlers)
        logging_config.configure_app_logging()
        assert len(root.handlers) == count_after_first, "a second call must be a no-op (idempotent)"
    finally:
        for h in list(root.handlers):
            root.removeHandler(h)
        for h in saved_handlers:
            root.addHandler(h)
        root.setLevel(saved_level)
