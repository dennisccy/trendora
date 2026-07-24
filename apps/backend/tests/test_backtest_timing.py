"""ops-hardening iter-18 — per-request timing instrumentation for `GET /api/backtest`
(`app.api.backtest.backtest`) and the MCP `query_backtest` tool (TC-1, TC-2, TC-3, TC-4).

Diagnostic-only: `logs/backend.log` carries zero per-request timing lines today (confirmed by direct
read — the iter-18 spec's own investigation: `grep -cE '^[0-9]{4}-[0-9]{2}-[0-9]{2}' logs/backend.log`
-> 0), so `/backtest`'s undiagnosed >=1.5s serving-budget breaches (J-06/J-07/J-08) cannot be
phase-attributed. This module proves the new instrumentation itself works. Observability only — the
served payload is unchanged (proved elsewhere by the pre-existing byte-identity tests); this file never
asserts on scorecard/evidence CONTENT, only on the new timing log line's shape and presence.

All fixtures here are small, hand-built SQLite engines — mirrors test_forward_testing_serving_split.py's
own established pattern — never the ~80-minute `loaded_engine` seed+warm fixture (out of scope this
session, host-guard-confined/targeted-tests-only; see docs/handoffs/goal-ops-hardening-iter-18-dev.md).
Every call below is a DIRECT function call (`app.api.backtest.backtest(...)` /
`app.mcp.tools.query_backtest(...)`) — no TestClient, no live server, no socket — so the new timing
fields are captured via `caplog` (TC-4: "provable without a running process").
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timezone

import pytest
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.models import DailyPrice, ForwardReturn, ScannerResult, ScannerRun

HORIZONS = load_config().walk_forward.horizons  # [1, 5, 10, 20, 60] today — read from config


def _utc() -> datetime:
    return datetime.now(timezone.utc)


def _add_run(session: Session, asof: date, regime_label: str = "Risk-on") -> ScannerRun:
    run = ScannerRun(
        asof_date=asof, created_at=_utc(), provider="seed", benchmark="SPY", regime_score=50.0,
        regime_label=regime_label, regime_components_json="[]", new_high_low_json="{}",
        candidate_counts_json="{}",
    )
    session.add(run)
    session.flush()
    return run


def _add_result(session: Session, run_id: int, ticker: str, rank: int = 1) -> None:
    session.add(ScannerResult(
        run_id=run_id, ticker=ticker, name=ticker, sector="Technology", leadership_score=50.0,
        leadership_bucket="A", entry_quality_score=50.0, entry_quality_bucket="B", risk_score=50.0,
        risk_bucket="C", setup_status="Actionable", rank=rank, record_json="{}", is_vcp=False,
        is_pullback_to_rising_dma=False, is_flat_base_breakout=False,
    ))


@pytest.fixture()
def timing_engine(tmp_path):
    """ONE run ("AAA", 2025-01-10) with an entry-day bar PLUS one post-snapshot bar (2025-01-13) — enough
    for `resolved_run`'s `latest_data_date` check AND for `backfill_run_forward_returns` to perform a
    REAL INSERT for horizon=1 (TC-2's own precondition: "a date whose forward returns are not yet
    backfilled"). No `ForwardAggregateCache` warm at all (irrelevant to this module — the timing line
    itself, not evidence content, is under test)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'timing.db'}")
    create_db_and_tables(engine)
    asof = date(2025, 1, 10)
    with Session(engine) as session:
        run = _add_run(session, asof)
        _add_result(session, run.id, "AAA")
        session.add(DailyPrice(
            symbol="AAA", date=asof, open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0,
        ))
        session.add(DailyPrice(
            symbol="AAA", date=date(2025, 1, 13), open=101.0, high=102.0, low=100.0, close=101.0, volume=1.0,
        ))
        session.commit()
    return engine, asof


# Matches "<prefix>_timing ts=... is_latest=... total_ms=... resolved_run_ms=... "
# "backfill_forward_returns_ms=... scorecard_ms=... evidence_ms=..." with an optional trailing
# " ensure_loop_ms=...". Deliberately does not anchor the leading prefix word, since TC-3 only requires
# the SAME field names, not the same message prefix, between the API and MCP loggers.
_TIMING_LINE_RE = re.compile(
    r"ts=(?P<ts>\S+) is_latest=(?P<is_latest>\S+) total_ms=(?P<total_ms>[\d.]+) "
    r"resolved_run_ms=(?P<resolved_run_ms>[\d.]+) "
    r"backfill_forward_returns_ms=(?P<backfill_forward_returns_ms>[\d.]+) "
    r"scorecard_ms=(?P<scorecard_ms>[\d.]+) evidence_ms=(?P<evidence_ms>[\d.]+)"
    r"(?: ensure_loop_ms=(?P<ensure_loop_ms>[\d.]+))?"
)


def _parsed_timing_fields(message: str) -> dict:
    m = _TIMING_LINE_RE.search(message)
    assert m, f"timing line did not match the expected key=value shape: {message!r}"
    return m.groupdict()


def _timing_records(caplog, logger_name: str, needle: str) -> list:
    return [r for r in caplog.records if r.name == logger_name and needle in r.getMessage()]


# ======================================================================================================
# TC-1 / TC-4 — GET /api/backtest's route function emits exactly one parseable timing log line per
# request, carrying an ISO-8601 wall-clock timestamp + total_ms, provable without a running process.
# ======================================================================================================
def test_backtest_route_emits_timing_log_line_with_iso_timestamp_and_total_ms(timing_engine, caplog):
    import app.api.backtest as backtest_module

    engine, _asof = timing_engine
    caplog.set_level(logging.INFO, logger="trendora.backtest")
    with Session(engine) as session:
        result = backtest_module.backtest(as_of=None, session=session)

    assert result["is_latest"] is True  # sanity: the endpoint itself still works (byte-identical return)
    records = _timing_records(caplog, "trendora.backtest", "backtest_timing")
    assert len(records) == 1, f"expected exactly one timing log line; got {len(records)}"

    fields = _parsed_timing_fields(records[0].getMessage())
    # TC-1: an ISO-8601 wall-clock timestamp + a total-elapsed-time field in milliseconds.
    parsed_ts = datetime.fromisoformat(fields["ts"])
    assert parsed_ts.tzinfo is not None, "expected a timezone-aware ISO-8601 timestamp"
    assert float(fields["total_ms"]) >= 0.0
    # TC-4: the per-phase fields are present too, captured via caplog alone (no live server/socket).
    for key in ("resolved_run_ms", "backfill_forward_returns_ms", "scorecard_ms", "evidence_ms"):
        assert float(fields[key]) >= 0.0
    # the LATEST view never reaches the historical ensure-loop -> no ensure_loop_ms field at all.
    assert fields["ensure_loop_ms"] is None


# ======================================================================================================
# TC-2 — a request whose forward returns are not yet backfilled (a real INSERT on the read path): the
# four named phases sum within 5ms or 5% (whichever is larger) of the logged total.
# ======================================================================================================
def test_backtest_route_timing_phase_sum_matches_total_within_tolerance(timing_engine, caplog):
    import app.api.backtest as backtest_module

    engine, _asof = timing_engine
    caplog.set_level(logging.INFO, logger="trendora.backtest")
    with Session(engine) as session:
        # TC-2's own precondition: no ForwardReturn rows exist yet for this run.
        assert session.exec(select(ForwardReturn)).all() == []
        result = backtest_module.backtest(as_of=None, session=session)
        # the call above must have performed a real INSERT (horizon=1 has exactly one post-snapshot bar).
        inserted = session.exec(select(ForwardReturn)).all()
        assert len(inserted) >= 1, "expected backfill_run_forward_returns to insert at least one row"

    assert result["is_latest"] is True
    records = _timing_records(caplog, "trendora.backtest", "backtest_timing")
    assert len(records) == 1
    fields = _parsed_timing_fields(records[0].getMessage())

    total_ms = float(fields["total_ms"])
    phase_sum = (
        float(fields["resolved_run_ms"]) + float(fields["backfill_forward_returns_ms"])
        + float(fields["scorecard_ms"]) + float(fields["evidence_ms"])
    )
    tolerance = max(5.0, 0.05 * total_ms)
    assert abs(total_ms - phase_sum) <= tolerance, (
        f"phase sum {phase_sum:.2f}ms not within {tolerance:.2f}ms of total {total_ms:.2f}ms"
    )


# ======================================================================================================
# TC-3 — the MCP query_backtest tool emits a timing log line carrying the SAME field names as TC-1/TC-2.
# ======================================================================================================
def test_query_backtest_mcp_tool_emits_timing_log_line_with_same_field_names(timing_engine, caplog):
    import app.mcp.tools as tools_module

    engine, _asof = timing_engine
    caplog.set_level(logging.INFO, logger="trendora.mcp_backtest")
    with Session(engine) as session:
        result = tools_module.query_backtest(session, asof=None)

    assert result["is_latest"] is True
    records = _timing_records(caplog, "trendora.mcp_backtest", "query_backtest_timing")
    assert len(records) == 1, f"expected exactly one timing log line; got {len(records)}"

    fields = _parsed_timing_fields(records[0].getMessage())
    parsed_ts = datetime.fromisoformat(fields["ts"])
    assert parsed_ts.tzinfo is not None
    assert float(fields["total_ms"]) >= 0.0
    for key in ("resolved_run_ms", "backfill_forward_returns_ms", "scorecard_ms", "evidence_ms"):
        assert float(fields[key]) >= 0.0
    assert fields["ensure_loop_ms"] is None


# ======================================================================================================
# IN SCOPE (not individually TC-numbered): `ensure_loop_ms` is present ONLY on the historical/
# non-`is_latest` ensure-loop branch — mirrored identically by both the API route and the MCP tool.
# ======================================================================================================
def test_backtest_route_timing_includes_ensure_loop_ms_on_historical_not_ready_branch(timing_engine, caplog):
    import app.api.backtest as backtest_module

    engine, older_asof = timing_engine
    with Session(engine) as session:
        # a genuinely LATER run makes `older_asof` historical (is_latest False); its own
        # forward-aggregate cache is empty, so the resolver's first read is not "ready" and the
        # ensure-loop below must run.
        later_run = _add_run(session, date(2025, 6, 1), "Risk-off")
        _add_result(session, later_run.id, "BBB")
        session.add(DailyPrice(
            symbol="BBB", date=date(2025, 6, 1), open=10.0, high=11.0, low=9.0, close=10.0, volume=1.0,
        ))
        session.commit()

    caplog.set_level(logging.INFO, logger="trendora.backtest")
    with Session(engine) as session:
        result = backtest_module.backtest(as_of=older_asof.isoformat(), session=session)

    assert result["is_latest"] is False
    records = _timing_records(caplog, "trendora.backtest", "backtest_timing")
    assert len(records) == 1
    fields = _parsed_timing_fields(records[0].getMessage())
    assert fields["ensure_loop_ms"] is not None, "expected ensure_loop_ms on the historical not-ready branch"
    assert float(fields["ensure_loop_ms"]) >= 0.0


def test_query_backtest_mcp_tool_timing_includes_ensure_loop_ms_on_historical_not_ready_branch(
    timing_engine, caplog
):
    """Mirrors the API-route test directly above for the MCP tool (TC-3's "same field names" claim
    extended to the conditional field too)."""
    import app.mcp.tools as tools_module

    engine, older_asof = timing_engine
    with Session(engine) as session:
        later_run = _add_run(session, date(2025, 6, 1), "Risk-off")
        _add_result(session, later_run.id, "BBB")
        session.add(DailyPrice(
            symbol="BBB", date=date(2025, 6, 1), open=10.0, high=11.0, low=9.0, close=10.0, volume=1.0,
        ))
        session.commit()

    caplog.set_level(logging.INFO, logger="trendora.mcp_backtest")
    with Session(engine) as session:
        result = tools_module.query_backtest(session, asof=older_asof.isoformat())

    assert result["is_latest"] is False
    records = _timing_records(caplog, "trendora.mcp_backtest", "query_backtest_timing")
    assert len(records) == 1
    fields = _parsed_timing_fields(records[0].getMessage())
    assert fields["ensure_loop_ms"] is not None
    assert float(fields["ensure_loop_ms"]) >= 0.0
