"""Theme leadership engine against the REAL committed seed (deterministic) + a synthetic
no-history case proving graceful NA (never a crash or fabricated value).

Asserts the canonical contract (J-03): themes rank non-increasing by Theme Score; the top theme
exposes member tickers, numeric 1m & 3m basket returns, a breadth %, and a trend label; every row
carries its named component breakdown (explainability); breadth is labelled universe-relative.
"""
from __future__ import annotations

from datetime import date, timedelta

import yaml
from sqlalchemy import insert
from sqlmodel import Session

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.prices import latest_data_date
from app.engine.themes import basket_return, score_themes, total_return
from app.models import DailyPrice


def test_themes_ranked_descending_with_required_fields(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        result = score_themes(session, asof, cfg)

    rows = result["rows"]
    assert len(rows) == len(cfg.themes) >= 3  # at least 3 themes (J-03)

    scores = [r["score"] for r in rows]
    assert scores == sorted(scores, reverse=True)            # non-increasing (J-03)
    assert [r["rank"] for r in rows] == list(range(1, len(rows) + 1))

    top = rows[0]
    assert isinstance(top["members"], list) and len(top["members"]) >= 1   # member tickers
    assert isinstance(top["return_1m"], (int, float))        # numeric 1m basket return
    assert isinstance(top["return_3m"], (int, float))        # numeric 3m basket return
    assert isinstance(top["breadth_pct"], (int, float))      # breadth %
    assert 0 <= top["breadth_pct"] <= 100
    assert isinstance(top["trend_label"], str) and top["trend_label"]
    assert top["bucket"] in {"A", "B", "C", "D", "E"}
    assert top["breadth_label"] == "universe-relative"       # honest-limitation label
    # every score carries its named component breakdown (no bare number)
    assert len(top["components"]) == len(cfg.theme_scores.weights)
    assert {c["name"] for c in top["components"]} == set(cfg.theme_scores.weights)
    assert any(c["available"] for c in top["components"])


def test_score_themes_is_deterministic(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        first = score_themes(session, asof, cfg)
        second = score_themes(session, asof, cfg)
    assert first == second


def test_basket_return_is_equal_weight_mean_of_member_returns(loaded_engine):
    """basket_return = mean of each member's own multiplicative total return over the window."""
    cfg = load_config()
    members = cfg.themes["semiconductors"]
    window = cfg.indicators.rs_windows["1m"]
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        from app.engine.prices import bars_asof, closes
        expected = [total_return(closes(bars_asof(session, m, asof)), window) for m in members]
        expected = [r for r in expected if r is not None]
        got = basket_return(session, members, asof, window)
    assert abs(got - sum(expected) / len(expected)) < 1e-9


# --- synthetic: a theme whose members all lack history degrades gracefully (no crash) --------
_SYNTH_CFG = {
    "provider": "seed",
    "database": {"url": "sqlite:///:memory:"},
    "universe": {"symbols": ["AAA", "BBB", "CCC", "DDD"], "filters": {"min_market_cap": 1, "min_dollar_vol": 1, "min_price": 1}},
    "etfs": {"index": ["SPY"], "sector": {"XLK": "Technology"}, "industry": ["SMH"], "volatility": ["^VIX"]},
    "themes": {"have_data": ["AAA", "BBB"], "no_data": ["CCC", "DDD"]},
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
        "theme_floor": 70, "actionable": {"leadership": 80, "entry": 70, "risk": 60},
        "extended": {"leadership": 85, "entry": 50}, "watch": {"leadership": 75}, "avoid_risk": 80,
    },
    "stock_sectors": {"AAA": "Technology", "BBB": "Technology", "CCC": "Technology", "DDD": "Technology"},
}


def _insert_ascending(session, symbol, n_bars):
    base = date(2026, 1, 1)
    rows = [
        {"symbol": symbol, "date": base + timedelta(days=i), "open": 100.0 + i,
         "high": 101.0 + i, "low": 99.0 + i, "close": 100.0 + i, "volume": 1000.0}
        for i in range(n_bars)
    ]
    session.execute(insert(DailyPrice.__table__), rows)


def test_theme_with_no_member_history_degrades_to_na_not_crash(tmp_path):
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(_SYNTH_CFG))
    cfg = load_config(path)

    engine = make_engine("sqlite:///:memory:")
    create_db_and_tables(engine)
    with Session(engine) as session:
        _insert_ascending(session, "SPY", 30)
        _insert_ascending(session, "AAA", 30)
        _insert_ascending(session, "BBB", 30)
        # CCC / DDD intentionally have NO bars -> theme "no_data" has no member history
        session.commit()

        asof = latest_data_date(session)
        result = score_themes(session, asof, cfg)  # must NOT crash

    by_slug = {r["slug"]: r for r in result["rows"]}
    no_data = by_slug["no_data"]
    assert no_data["score"] == 0                      # no available components -> 0, not fabricated
    assert all(c["available"] is False for c in no_data["components"])
    assert no_data["return_1m"] is None and no_data["breadth_pct"] is None
    # the theme that DOES have data still computes
    assert by_slug["have_data"]["return_1m"] is not None
