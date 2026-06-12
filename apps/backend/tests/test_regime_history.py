"""Unit tests for the stored regime-history series (J-44 + J-45 / Capability 37).

Covers the anti-goal-bearing behaviors of `app.engine.regime_history.get_regime_history`:
  - label + score are read VERBATIM from the stored `scanner_runs` rows (no recompute)
  - as-of bounding — a row dated AFTER the resolved as-of date is never returned (no-lookahead;
    bands must not render past the as-of date)
  - ascending-by-date ordering
  - an as-of resolving before any stored run yields an honest empty `points` list (no crash)
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import insert
from sqlmodel import Session

from app.db import create_db_and_tables, make_engine
from app.engine.regime_history import get_regime_history
from app.models import DailyPrice, ScannerRun

_BASE = date(2026, 1, 1)


def _insert_bars(session, symbol, n):
    rows = [
        {"symbol": symbol, "date": _BASE + timedelta(days=i), "open": 100.0 + i,
         "high": 101.0 + i, "low": 99.0 + i, "close": 100.0 + i, "volume": 1000.0}
        for i in range(n)
    ]
    session.execute(insert(DailyPrice.__table__), rows)


def _insert_run(session, d, label, score):
    """Insert one immutable ScannerRun row with a stored regime label + score (the verbatim values
    the read path must echo). Children are not needed for the regime-history read."""
    session.add(
        ScannerRun(
            asof_date=d,
            created_at=datetime(2026, 1, 1, 12, 0, 0),
            provider="seed",
            benchmark="SPY",
            regime_score=score,
            regime_label=label,
            regime_components_json="{}",
            breadth_above_50dma=None,
            breadth_above_200dma=None,
            new_high_low_json="{}",
            candidate_counts_json="{}",
        )
    )


def _engine():
    engine = make_engine("sqlite:///:memory:")
    create_db_and_tables(engine)
    return engine


def test_reads_label_and_score_verbatim_in_date_order():
    engine = _engine()
    with Session(engine) as session:
        _insert_bars(session, "SPY", 10)  # so as-of resolution has price data
        # insert out of order to prove ordering is by date, not insertion
        _insert_run(session, date(2026, 1, 5), "Risk-on", 70.5)
        _insert_run(session, date(2026, 1, 1), "Risk-off", 12.0)
        _insert_run(session, date(2026, 1, 3), "Choppy", 48.25)
        session.commit()
        result = get_regime_history(session, as_of="2026-01-05")

    assert result["asof_date"] == "2026-01-05"
    assert result["points"] == [
        {"date": "2026-01-01", "label": "Risk-off", "score": 12.0},
        {"date": "2026-01-03", "label": "Choppy", "score": 48.25},
        {"date": "2026-01-05", "label": "Risk-on", "score": 70.5},
    ]


def test_as_of_bounding_excludes_rows_after_resolved_date():
    engine = _engine()
    with Session(engine) as session:
        _insert_bars(session, "SPY", 10)
        _insert_run(session, date(2026, 1, 1), "Risk-off", 12.0)
        _insert_run(session, date(2026, 1, 3), "Choppy", 48.0)
        _insert_run(session, date(2026, 1, 5), "Risk-on", 70.0)  # AFTER the as-of below
        session.commit()
        result = get_regime_history(session, as_of="2026-01-03")

    assert result["asof_date"] == "2026-01-03"
    # the Jan 5 run must NOT appear — bands never render past the resolved as-of date
    assert [p["date"] for p in result["points"]] == ["2026-01-01", "2026-01-03"]
    assert all(p["date"] <= "2026-01-03" for p in result["points"])


def test_as_of_none_resolves_to_latest_stored_run():
    engine = _engine()
    with Session(engine) as session:
        _insert_bars(session, "SPY", 10)
        _insert_run(session, date(2026, 1, 1), "Risk-off", 12.0)
        _insert_run(session, date(2026, 1, 5), "Risk-on", 70.0)
        session.commit()
        result = get_regime_history(session, as_of=None)

    # default = latest stored run date; both points included
    assert result["asof_date"] == "2026-01-05"
    assert [p["date"] for p in result["points"]] == ["2026-01-01", "2026-01-05"]


def test_as_of_before_any_run_yields_empty_points():
    engine = _engine()
    with Session(engine) as session:
        # bars exist from Jan 1, but the only run is dated Jan 5; as-of Jan 2 resolves (a bar exists
        # on/before it) but no run is dated <= Jan 2 -> honest empty series, no crash.
        _insert_bars(session, "SPY", 10)
        _insert_run(session, date(2026, 1, 5), "Risk-on", 70.0)
        session.commit()
        result = get_regime_history(session, as_of="2026-01-02")

    assert result["asof_date"] == "2026-01-02"
    assert result["points"] == []


# --- J-49: clamp-optional (full-history) serving on the regime series -----------------------------
# full=True returns the ENTIRE stored per-run regime series (labels + scores VERBATIM, never
# recomputed) through the latest run, while still echoing the resolved as-of (the client draws the
# vertical marker from it). Default (full=False) stays clamped at the as-of (the stock-detail consumer
# keeps it — J-45). The overlapping <= D portion is value-identical between modes (no second path).


def test_full_mode_includes_runs_after_asof_through_latest():
    engine = _engine()
    with Session(engine) as session:
        _insert_bars(session, "SPY", 10)
        _insert_run(session, date(2026, 1, 1), "Risk-off", 12.0)
        _insert_run(session, date(2026, 1, 3), "Choppy", 48.0)
        _insert_run(session, date(2026, 1, 5), "Risk-on", 70.0)  # AFTER the as-of below
        session.commit()
        result = get_regime_history(session, as_of="2026-01-03", full=True)

    # full mode serves the whole stored series through the latest run (Jan 5), NOT clamped at Jan 3
    assert [p["date"] for p in result["points"]] == ["2026-01-01", "2026-01-03", "2026-01-05"]
    # the resolved as-of is still echoed verbatim (the marker position D)
    assert result["asof_date"] == "2026-01-03"
    # labels/scores are the verbatim stored values — nothing recomputed
    assert result["points"][2] == {"date": "2026-01-05", "label": "Risk-on", "score": 70.0}


def test_full_mode_default_is_byte_identical_clamped():
    engine = _engine()
    with Session(engine) as session:
        _insert_bars(session, "SPY", 10)
        _insert_run(session, date(2026, 1, 1), "Risk-off", 12.0)
        _insert_run(session, date(2026, 1, 3), "Choppy", 48.0)
        _insert_run(session, date(2026, 1, 5), "Risk-on", 70.0)
        session.commit()
        absent = get_regime_history(session, as_of="2026-01-03")
        explicit_false = get_regime_history(session, as_of="2026-01-03", full=False)
    assert absent == explicit_false
    # default stays clamped at the as-of (the stock-detail consumer — J-45 — keeps this)
    assert [p["date"] for p in absent["points"]] == ["2026-01-01", "2026-01-03"]


def test_full_and_default_value_identical_on_overlapping_range():
    """No second path: the <= D portion of the full series equals the clamped series exactly."""
    engine = _engine()
    with Session(engine) as session:
        _insert_bars(session, "SPY", 10)
        _insert_run(session, date(2026, 1, 1), "Risk-off", 12.0)
        _insert_run(session, date(2026, 1, 3), "Choppy", 48.25)
        _insert_run(session, date(2026, 1, 5), "Risk-on", 70.5)
        session.commit()
        clamped = get_regime_history(session, as_of="2026-01-03")
        full = get_regime_history(session, as_of="2026-01-03", full=True)
    overlap = [p for p in full["points"] if p["date"] <= "2026-01-03"]
    assert overlap == clamped["points"]
