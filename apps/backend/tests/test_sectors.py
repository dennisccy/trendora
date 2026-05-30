"""Sector/industry leadership engine.

Real-seed tests assert the canonical contract: rows ranked descending by Sector Score, every row
carries RS-vs-SPY + dist-from-52w-high + trend label + A-E bucket + named components, SPY (and the
other index ETFs) are EXCLUDED from the ranked rows, and the output is deterministic. A synthetic
test proves the `min_history_bars` floor forces a short-history ETF's long-window components to NA
without crashing or fabricating.
"""
from __future__ import annotations

from datetime import date, timedelta

import yaml
from sqlalchemy import insert
from sqlmodel import Session

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.prices import latest_data_date
from app.engine.sectors import score_sectors
from app.models import DailyPrice


def test_rows_ranked_descending_with_required_fields(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        result = score_sectors(session, asof, cfg)

    rows = result["rows"]
    # 11 sector SPDRs + 20 industry ETFs = 31 ranked rows
    assert len(rows) == len(cfg.etfs.sector) + len(cfg.etfs.industry) == 31

    scores = [r["score"] for r in rows]
    assert scores == sorted(scores, reverse=True)  # non-increasing
    assert [r["rank"] for r in rows] == list(range(1, len(rows) + 1))

    top = rows[0]
    assert top["rs_vs_spy"] is not None          # numeric RS-vs-SPY on the top row (J-04)
    assert top["dist_from_52w_high_pct"] is not None
    assert isinstance(top["trend_label"], str) and top["trend_label"]
    assert top["bucket"] in {"A", "B", "C", "D", "E"}
    assert len(top["components"]) == len(cfg.sectors.weights)  # every component named


def test_spy_and_index_etfs_excluded_from_ranked_rows(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        result = score_sectors(session, asof, cfg)
    tickers = {r["ticker"] for r in result["rows"]}
    assert result["benchmark"] == "SPY"
    for index_etf in cfg.etfs.index:  # SPY, QQQ, IWM, RSP
        assert index_etf not in tickers
    # every ranked row is a sector or industry ETF
    assert all(r["kind"] in {"sector", "industry"} for r in result["rows"])


def test_score_sectors_is_deterministic(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        first = score_sectors(session, asof, cfg)
        second = score_sectors(session, asof, cfg)
    assert first == second


# --- synthetic: the min_history_bars floor forces long-window components to NA ---------------
_SYNTH_CFG = {
    "provider": "seed",
    "database": {"url": "sqlite:///:memory:"},
    "universe": {"symbols": ["AAA", "BBB"], "filters": {"min_market_cap": 1, "min_dollar_vol": 1, "min_price": 1}},
    "etfs": {"index": ["SPY"], "sector": {"XLK": "Technology", "XLF": "Financials"}, "industry": ["SMH"], "volatility": ["^VIX"]},
    "themes": {"t1": ["AAA", "BBB"]},
    "buckets": {"A": 90, "B": 80, "C": 70, "D": 60},
    "indicators": {
        "ma_periods": [5, 10], "rs_windows": {"1m": 3, "3m": 5, "6m": 10},
        "atr_period": 5, "high_window_52w": 20, "vol_avg_period": 5,
        "min_history_bars": 40, "breadth_short_ma": 5, "breadth_long_ma": 10,
    },
    "sectors": {
        "weights": {"rs_spy_1m": 0.20, "rs_spy_3m": 0.25, "rs_spy_6m": 0.20, "ma_stack": 0.15, "dist_from_high": 0.10, "vol_trend": 0.10},
        "trend_edges": [{"min": 70, "label": "Strong uptrend"}, {"min": 0, "label": "Downtrend"}],
    },
    "regime": {
        "vix_threshold": 20,
        "weights": {"index_ma_stack": 0.35, "breadth_above_50dma": 0.25, "breadth_above_200dma": 0.25, "new_high_low": 0.15},
        "labels": ["Strong risk-on", "Risk-on", "Narrow leadership", "Choppy", "Defensive", "Risk-off"],
        "label_edges": [{"min": 80, "label": "Strong risk-on"}, {"min": 0, "label": "Risk-off"}],
    },
    "scores": {
        "leadership": {"weights": {"rs_spy_1m": 0.15, "rs_spy_3m": 0.20, "rs_sector": 0.15, "rs_theme": 0.10, "ma_stack": 0.20, "high_proximity": 0.10, "up_down_vol": 0.10}},
        "entry_quality": {"weights": {"dist_rising_20": 0.25, "contraction": 0.20, "support_nearby": 0.15, "structure": 0.20, "reward_risk": 0.20}},
        "risk": {"weights": {"extension": 0.20, "atr_pct": 0.15, "liquidity": 0.10, "regime": 0.15, "sector_strength": 0.10, "gap_climax": 0.15, "below_ma": 0.10, "rs_deterioration": 0.05}},
    },
    "theme_scores": {
        "weights": {"rs_spy_1m": 0.25, "rs_spy_3m": 0.30, "breadth": 0.25, "ma_participation": 0.20},
        "trend_edges": [{"min": 70, "label": "Strong uptrend"}, {"min": 0, "label": "Downtrend"}],
    },
    "decision_rules": {
        "theme_floor": 70,
        "actionable": {"leadership": 80, "entry": 70, "risk": 60},
        "extended": {"leadership": 85, "entry": 50},
        "watch": {"leadership": 75},
        "avoid_risk": 80,
        "invalidation": {"ma_period": 10},  # must be one of this synthetic config's ma_periods [5, 10]
    },
    "stock_sectors": {"AAA": "Technology", "BBB": "Financials"},
    "scanner": {"bootstrap_dates": ["2022-10-07"]},  # iter-5: scanner is a required config section
}


def _insert_ascending(session, symbol, n_bars):
    base = date(2026, 1, 1)
    rows = [
        {"symbol": symbol, "date": base + timedelta(days=i), "open": 100.0 + i,
         "high": 101.0 + i, "low": 99.0 + i, "close": 100.0 + i, "volume": 1000.0}
        for i in range(n_bars)
    ]
    session.execute(insert(DailyPrice.__table__), rows)


def test_min_history_bars_floor_reports_na_for_short_history(tmp_path):
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(_SYNTH_CFG))
    cfg = load_config(path)

    engine = make_engine("sqlite:///:memory:")
    create_db_and_tables(engine)
    with Session(engine) as session:
        _insert_ascending(session, "SPY", 60)
        _insert_ascending(session, "XLK", 60)   # long enough (>= 40)
        _insert_ascending(session, "XLF", 30)   # SHORT (< min_history_bars=40)
        _insert_ascending(session, "SMH", 60)
        session.commit()

        asof = latest_data_date(session)
        result = score_sectors(session, asof, cfg)  # must NOT crash

    by_ticker = {r["ticker"]: r for r in result["rows"]}
    assert "SPY" not in by_ticker  # benchmark excluded
    short = by_ticker["XLF"]
    comp = {c["name"]: c for c in short["components"]}
    # long-window components are NA (floor), even though 30 bars > the raw window sizes
    assert comp["rs_spy_6m"]["available"] is False
    assert comp["dist_from_high"]["available"] is False
    assert short["dist_from_52w_high_pct"] is None
    # short-window components still computed (graceful degradation, not a crash)
    assert comp["rs_spy_1m"]["available"] is True
