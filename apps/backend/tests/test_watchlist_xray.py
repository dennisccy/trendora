"""app.engine.watchlist_xray — the watchlist concentration X-ray composer (iter-38, J-23 / B-204).

FAST synthetic tests: tiny hand-made DBs (no seed boot), mirroring the `test_iter33_dynamic_universe.py`
/ `test_bars_windowing.py` synthetic-DB pattern. The B-204 numeric fixture (ENB ≈ 2 from exact
correlation/eigenvalue math) is proven directly against `app.engine.concentration` in
`test_concentration.py`; this file proves the COMPOSER'S OWN responsibilities: bounded reads, the
`min_overlap_days` honesty floor (never a fabricated correlation), null-sector grouping (never a crash,
never dropped), the shared-setup reuse of `summarize_candidates`, multi-membership theme concentration,
determinism, and the insufficient-watchlist / missing-bars / empty error cases.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pytest
from sqlmodel import Session

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.setups import ALL_STATUSES
from app.engine.watchlist_xray import build_xray_payload
from app.models import DailyPrice, ScannerResult, ScannerRun

ASOF = date(2026, 1, 30)


def _engine(tmp_path, name: str):
    engine = make_engine(f"sqlite:///{tmp_path / name}")
    create_db_and_tables(engine)
    return engine


def _mk_run(session: Session, asof: date) -> ScannerRun:
    """Minimal valid ScannerRun row (mirrors test_iter33_dynamic_universe.py's `_mk_run`)."""
    run = ScannerRun(
        asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
        regime_score=50.0, regime_label="Choppy", regime_components_json="{}",
        new_high_low_json="{}", candidate_counts_json="{}",
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def _mk_result(
    session: Session, run_id: int, ticker: str, *, sector: str | None, themes: list[dict], status: str
) -> None:
    """A ScannerResult whose `record_json` carries the minimum keys `filtered_stock_rows` /
    `build_xray_payload` actually read (ticker/sector/themes/setup) — unlike the bare `"{}"` some other
    synthetic fixtures use (those never exercise `filtered_stock_rows`' JSON rehydration path)."""
    record = {"ticker": ticker, "sector": sector, "themes": themes, "setup": {"status": status, "reason": "fixture"}}
    session.add(ScannerResult(
        run_id=run_id, ticker=ticker, name=ticker, sector=sector,
        leadership_score=50.0, leadership_bucket="C",
        entry_quality_score=50.0, entry_quality_bucket="C",
        risk_score=50.0, risk_bucket="C",
        setup_status=status, rank=1, record_json=json.dumps(record),
    ))
    session.commit()


def _insert_prices(session: Session, symbol: str, closes_: list[float], end: date) -> None:
    """Consecutive daily bars ending exactly at `end` (calendar days — the composer only cares about
    ordering and `date <= asof`, mirroring `test_bars_windowing.py`'s synthetic fixture)."""
    start = end - timedelta(days=len(closes_) - 1)
    rows = [
        {
            "symbol": symbol, "date": start + timedelta(days=i),
            "open": c, "high": c, "low": c, "close": c, "volume": 1_000_000.0,
        }
        for i, c in enumerate(closes_)
    ]
    session.execute(DailyPrice.__table__.insert(), rows)
    session.commit()


def _linear_series(n: int, start: float = 100.0, step: float = 1.0) -> list[float]:
    return [start + step * i for i in range(n)]


# --- insufficient-watchlist (0-1 names) --------------------------------------------------------
def test_insufficient_watchlist_zero_names(tmp_path):
    cfg = load_config()
    engine = _engine(tmp_path, "zero.db")
    with Session(engine) as session:
        payload = build_xray_payload(session, cfg, [], ASOF)
    assert payload["status"] == "insufficient"
    assert payload["tickers"] == []
    assert payload["correlation_matrix"] == {}
    assert payload["clusters"] == []
    assert payload["effective_number_of_bets"] is None
    assert payload["sector_concentration"] == []


def test_insufficient_watchlist_one_name_no_crash(tmp_path):
    cfg = load_config()
    engine = _engine(tmp_path, "one.db")
    with Session(engine) as session:
        _mk_run(session, ASOF)
        _insert_prices(session, "SOLO", _linear_series(200), ASOF)
        payload = build_xray_payload(session, cfg, ["SOLO"], ASOF)
    assert payload["status"] == "insufficient"
    assert payload["tickers"] == ["SOLO"]
    assert payload["effective_number_of_bets"] is None


# --- sufficient-history pair: correlation / clusters / ENB ---------------------------------------
def test_two_names_sufficient_history_correlate_and_render_ok(tmp_path):
    cfg = load_config()
    engine = _engine(tmp_path, "two.db")
    aaa = _linear_series(200, start=100.0, step=1.0)
    bbb = [2.0 * v for v in aaa]  # a pure positive scalar multiple -> IDENTICAL returns -> corr == 1.0 exactly
    with Session(engine) as session:
        _mk_run(session, ASOF)
        _insert_prices(session, "AAA", aaa, ASOF)
        _insert_prices(session, "BBB", bbb, ASOF)
        payload = build_xray_payload(session, cfg, ["AAA", "BBB"], ASOF)
    assert payload["status"] == "ok"
    assert payload["tickers"] == ["AAA", "BBB"]
    assert payload["correlation_matrix"]["AAA"]["BBB"] == pytest.approx(1.0, abs=1e-9)
    assert payload["correlation_matrix"]["BBB"]["AAA"] == pytest.approx(1.0, abs=1e-9)
    assert payload["clusters"] == [["AAA", "BBB"]]  # one merged cluster
    assert payload["effective_number_of_bets"] == pytest.approx(1.0, abs=1e-9)  # fully redundant pair
    assert payload["enb_member_count"] == 2


def test_uncorrelated_pair_is_two_separate_clusters_and_enb_two(tmp_path):
    cfg = load_config()
    engine = _engine(tmp_path, "uncorr.db")
    rng = np.random.default_rng(20240601)
    a = (1000.0 + np.cumsum(rng.normal(0, 1, size=200))).tolist()
    b = (1000.0 + np.cumsum(rng.normal(0, 1, size=200))).tolist()  # a fresh, independent draw
    with Session(engine) as session:
        _mk_run(session, ASOF)
        _insert_prices(session, "IND1", a, ASOF)
        _insert_prices(session, "IND2", b, ASOF)
        payload = build_xray_payload(session, cfg, ["IND1", "IND2"], ASOF)
    corr = payload["correlation_matrix"]["IND1"]["IND2"]
    assert corr is not None and abs(corr) < 0.3  # ~uncorrelated (loose, deterministic-seed bound)
    assert payload["clusters"] == [["IND1"], ["IND2"]]  # no qualifying edge -> two singletons
    assert 1.0 <= payload["effective_number_of_bets"] <= 2.0  # exact math bound for any 2-asset pair


# --- the min_overlap_days honesty floor ---------------------------------------------------------
def test_short_history_member_is_honest_na_never_fabricated(tmp_path):
    cfg = load_config()
    engine = _engine(tmp_path, "short.db")
    with Session(engine) as session:
        _mk_run(session, ASOF)
        _insert_prices(session, "OLD", _linear_series(200), ASOF)
        _insert_prices(session, "NEW", _linear_series(10), ASOF)  # far under min_overlap_days
        payload = build_xray_payload(session, cfg, ["OLD", "NEW"], ASOF)
    assert payload["status"] == "ok"
    assert payload["history_days"]["NEW"] == 9  # 10 closes -> 9 returns
    assert payload["history_days"]["NEW"] < cfg.watchlist.xray.min_overlap_days
    assert payload["correlation_matrix"]["OLD"]["NEW"] is None
    assert payload["correlation_matrix"]["NEW"]["OLD"] is None
    assert payload["correlation_matrix"]["NEW"]["NEW"] is None  # excluded from the honest sub-matrix too
    assert payload["clusters"] == [["NEW"], ["OLD"]]  # NEW has no qualifying edge -> its own singleton
    assert payload["effective_number_of_bets"] == 1.0  # only OLD is ENB-eligible -> a single "1 bet"
    assert payload["enb_member_count"] == 1


def test_missing_bars_member_is_na_not_a_crash(tmp_path):
    cfg = load_config()
    engine = _engine(tmp_path, "missing.db")
    with Session(engine) as session:
        _mk_run(session, ASOF)
        _insert_prices(session, "HASDATA", _linear_series(200), ASOF)
        # "NODATA" has literally zero stored bars for the whole window.
        payload = build_xray_payload(session, cfg, ["HASDATA", "NODATA"], ASOF)
    assert payload["status"] == "ok"
    assert payload["history_days"]["NODATA"] == 0
    assert payload["correlation_matrix"]["NODATA"]["HASDATA"] is None
    assert payload["correlation_matrix"]["HASDATA"]["NODATA"] is None


# --- sector / theme / setup concentration --------------------------------------------------------
def test_sector_concentration_groups_null_sector_without_crash(tmp_path):
    cfg = load_config()
    engine = _engine(tmp_path, "sector.db")
    with Session(engine) as session:
        run = _mk_run(session, ASOF)
        _mk_result(session, run.id, "TECH1", sector="Technology", themes=[], status="Actionable")
        _mk_result(session, run.id, "TECH2", sector="Technology", themes=[], status="Actionable")
        _mk_result(session, run.id, "NOSEC", sector=None, themes=[], status="Avoid")
        for ticker in ("TECH1", "TECH2", "NOSEC"):
            _insert_prices(session, ticker, _linear_series(200), ASOF)
        payload = build_xray_payload(session, cfg, ["TECH1", "TECH2", "NOSEC"], ASOF)
    by_sector = {e["sector"]: e for e in payload["sector_concentration"]}
    assert by_sector["Technology"]["count"] == 2
    assert by_sector[None]["count"] == 1  # the null-sector bucket — grouped, never dropped, never crashed
    assert by_sector[None]["pct"] == pytest.approx(1 / 3)
    assert sum(e["count"] for e in payload["sector_concentration"]) == 3  # every ticker counted once


def test_setup_concentration_reuses_summarize_candidates_all_six_statuses(tmp_path):
    cfg = load_config()
    engine = _engine(tmp_path, "setup.db")
    with Session(engine) as session:
        run = _mk_run(session, ASOF)
        _mk_result(session, run.id, "A1", sector="Technology", themes=[], status="Actionable")
        _mk_result(session, run.id, "A2", sector="Technology", themes=[], status="Actionable")
        _mk_result(session, run.id, "B1", sector="Health Care", themes=[], status="Avoid")
        for ticker in ("A1", "A2", "B1"):
            _insert_prices(session, ticker, _linear_series(200), ASOF)
        payload = build_xray_payload(session, cfg, ["A1", "A2", "B1"], ASOF)
    statuses = {e["status"] for e in payload["setup_concentration"]}
    assert statuses == set(ALL_STATUSES)  # always all six, 0 where absent (mirrors summarize_candidates)
    by_status = {e["status"]: e["count"] for e in payload["setup_concentration"]}
    assert by_status["Actionable"] == 2
    assert by_status["Avoid"] == 1
    assert by_status["Breakout-watch"] == 0


def test_theme_concentration_counts_multi_membership(tmp_path):
    cfg = load_config()
    engine = _engine(tmp_path, "theme.db")
    with Session(engine) as session:
        run = _mk_run(session, ASOF)
        _mk_result(session, run.id, "T1", sector="Technology", themes=[{"slug": "ai", "name": "AI"}], status="Actionable")
        _mk_result(
            session, run.id, "T2", sector="Technology",
            themes=[{"slug": "ai", "name": "AI"}, {"slug": "cloud", "name": "Cloud"}], status="Actionable",
        )
        _mk_result(session, run.id, "T3", sector="Technology", themes=[], status="Actionable")
        for ticker in ("T1", "T2", "T3"):
            _insert_prices(session, ticker, _linear_series(200), ASOF)
        payload = build_xray_payload(session, cfg, ["T1", "T2", "T3"], ASOF)
    by_slug = {e["slug"]: e for e in payload["theme_concentration"]}
    assert by_slug["ai"]["count"] == 2
    assert by_slug["cloud"]["count"] == 1
    assert by_slug["ai"]["pct"] == pytest.approx(2 / 3)
    assert "cloud" in by_slug and "ai" in by_slug and len(payload["theme_concentration"]) == 2  # T3 contributes nothing


# --- determinism ----------------------------------------------------------------------------------
def test_determinism_byte_identical_regardless_of_input_order(tmp_path):
    cfg = load_config()
    engine = _engine(tmp_path, "det.db")
    aaa = _linear_series(200, start=100.0, step=1.0)
    bbb = [2.0 * v for v in aaa]
    with Session(engine) as session:
        run = _mk_run(session, ASOF)
        _mk_result(session, run.id, "AAA", sector="Technology", themes=[], status="Actionable")
        _mk_result(session, run.id, "BBB", sector="Health Care", themes=[], status="Avoid")
        _insert_prices(session, "AAA", aaa, ASOF)
        _insert_prices(session, "BBB", bbb, ASOF)
        first = build_xray_payload(session, cfg, ["BBB", "AAA"], ASOF)  # reversed input order
        second = build_xray_payload(session, cfg, ["AAA", "BBB"], ASOF)
    assert first == second
