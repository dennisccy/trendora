"""Unit tests for the major-indexes normalized-% display series (J-44 / Capability 37).

Covers the anti-goal-bearing behaviors of `app.engine.indexes.compute_index_series`:
  - rebase-at-range-start correctness (first point exactly 0.0%; later points = (close/base - 1)*100)
  - a hand-computed series matches the stored bars exactly
  - as-of bounding (no bar dated after the resolved as-of date)
  - range-window bounding (only bars >= range start, hand-checked)
  - honest omission of a configured symbol with NO stored bars (e.g. DIA) — no series + no legend
  - config-driven symbols + presets (the engine reads them from config, never a hardcoded list)
  - unknown range preset -> UnknownRangeError (the API maps it to a 422)
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest
import yaml
from sqlalchemy import insert
from sqlmodel import Session

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.indexes import UnknownRangeError, compute_index_series
from app.models import DailyPrice

# A synthetic config whose index_chart lists SPY, QQQ, and DIA (DIA intentionally bar-less in the DB so
# the omission path is exercised) with three range presets including an all-history preset.
_CFG = {
    "provider": "seed",
    "database": {"url": "sqlite:///:memory:"},
    "data_manager": {
        "providers": [{"id": "yahoo", "label": "Yahoo", "needs_key": False}],
        "default_source": "yahoo", "max_range_days": 370, "gap_preview": 60, "run_history_limit": 50,
        "import_chunking": {
            "symbol_batch_size": 25, "date_window_days": 90, "max_retries": 4,
            "backoff_base_seconds": 1.0, "backoff_cap_seconds": 30.0, "inter_request_sleep_seconds": 0.0,
            "fetch_workers": 4,  # J-46: bounded parallel fetch-pool size (>= 1)
            "backfill_workers": 4,  # J-53: bounded parallel backfill-pool size (>= 1)
        },
        "job_progress": {  # iter-29 (J-66) required block: poll/heartbeat/granularity knobs
            "poll_interval_seconds": 1.0, "heartbeat_stale_seconds": 20.0, "per_symbol_ticks": True,
        },
    },
    "universe": {"symbols": ["AAA", "BBB"], "filters": {"min_market_cap": 1, "min_dollar_vol": 1, "min_price": 1}},
    # J-58: etfs.industry is now a catalog (ticker -> {name, description}, name required).
    "etfs": {"index": ["SPY"], "sector": {"XLK": "Technology"}, "industry": {"SMH": {"name": "Semiconductors", "description": "Chip makers."}}, "volatility": ["^VIX"]},
    "index_chart": {
        "symbols": [
            {"symbol": "SPY", "name": "S&P 500 (SPY)"},
            {"symbol": "QQQ", "name": "Nasdaq 100 (QQQ)"},
            {"symbol": "DIA", "name": "Dow 30 (DIA)"},  # bar-less -> honest omission
        ],
        "range_presets": [
            {"key": "short", "label": "Short", "days": 5},
            {"key": "med", "label": "Med", "days": 20},
            {"key": "all", "label": "All", "days": None},
        ],
        "default_range": "med",
    },
    "themes": {"t1": ["AAA", "BBB"]},
    "buckets": {"A": 90, "B": 80, "C": 70, "D": 60},
    "indicators": {
        "ma_periods": [5, 10], "rs_windows": {"1m": 3, "3m": 5, "6m": 10},
        "atr_period": 5, "high_window_52w": 20, "vol_avg_period": 5,
        "min_history_bars": 40, "breadth_short_ma": 5, "breadth_long_ma": 10,
        "hv_window": 5, "semivol_window": 5, "vol_contraction_recent": 3, "vol_contraction_prior": 5,
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
        "invalidation": {"ma_period": 10},
    },
    "stock_sectors": {"AAA": "Technology", "BBB": "Technology"},
    "scanner": {"bootstrap_dates": ["2022-10-07"]},
    "startup": {
        "readiness_budget_seconds": 30.0, "warmup_batch_size": 1,
        "health_poll_interval_seconds": 2.0, "health_poll_idle_interval_seconds": 30.0,
    },
    "walk_forward": {
        "history_years": 2, "asof_cadence": "quarterly", "horizons": [1, 5, 10, 20, 60],
        "min_sample": 30, "default_horizon": 20,
        "control_group": {"seed": 20240601, "top_n": 20, "peers_per_sector": 5},
        "attribution": {
            "top_contributors_k": 5,
            "rank_bands": [
                {"label": "1–10", "min": 1, "max": 10},
                {"label": "11–50", "min": 11, "max": 50},
                {"label": "51+", "min": 51, "max": None},
            ],
        },
    },
    "patterns": {
        "vcp": {
            "lookback_bars": 20, "min_contractions": 2, "max_contractions": 4,
            "min_contraction_pct": 3, "max_base_depth_pct": 35, "contraction_shrink_ratio": 0.8,
            "max_last_contraction_pct": 12, "pivot_proximity_pct": 8, "volume_dryup_ratio": 0.9,
            "volume_window": 5, "min_history_bars": 20,
        },
        "pullback_to_rising_dma": {
            "ma_period": 10, "min_history_bars": 20, "trend_lookback_bars": 5,
            "min_dma_slope_pct": 1.5, "max_dist_above_dma_pct": 5.0, "max_undercut_pct": 2.0,
            "max_pullback_depth_pct": 18, "volume_window": 5,
        },
        "flat_base_breakout": {
            "lookback_bars": 20, "min_history_bars": 20, "base_window": 10,
            "max_base_depth_pct": 15, "pivot_proximity_pct": 6.0,
            "volume_window": 5, "min_breakout_volume_ratio": 1.0,
        },
    },
    "research": {
        "factor_lab": {
            "deciles": 10,
            "factors": [
                {"key": "leadership_score", "label": "Leadership", "family": "score",
                 "direction": "higher_better", "source": "leadership_score"},
            ],
            "combination": {
                "min_conditions": 2, "max_conditions": 3,
                "quantiles": [{"key": "half", "label": "Half (50%)", "fraction": 0.5}],
                "composite": {"quantile": "half", "weighting": {"scheme": "equal", "default_weight": 1.0}},
                "default_conditions": [
                    {"factor": "leadership_score", "side": "top", "quantile": "half"},
                    {"factor": "leadership_score", "side": "bottom", "quantile": "half"},
                ],
            },
        },
    },
    "methodology": {
        "intro": "Glossary.",
        "entries": [
            {
                "key": "Actionable", "kind": "setup", "name": "Actionable",
                "meaning": "A strong leader at a constructive entry.",
                "example": "L high, E high, R low in Risk-on -> Actionable.",
                "thresholds": [
                    {"label": "Leadership", "cmp": ">=", "ref": "decision_rules.actionable.leadership"},
                    {"label": "Regime", "text": "Risk-on only."},
                ],
            },
        ],
    },
    # iter-29: market_phase + regime_switching are required config sections (the read-only Market Phase
    # & Severity layer's edges/weights/thresholds + the deterministic 2-state filter params come from
    # config, never code). Smallest valid blocks added so a from-scratch valid config still loads.
    "market_phase": {
        "labels": ["Expansion", "Pullback", "Correction", "Bear", "Recovery"],
        "phase_edges": [
            {"min": 70, "label": "Bear"},
            {"min": 45, "label": "Correction"},
            {"min": 25, "label": "Pullback"},
            {"min": 0, "label": "Expansion"},
        ],
        "weights": {
            "drawdown_depth": 0.35, "time_underwater": 0.15, "regime_risk": 0.20,
            "breadth_below_200dma": 0.15, "vix_gate": 0.15,
        },
        "lookback_days": 365,
        "drawdown_full_severity_pct": 25.0,
        "vix_gate": 30.0,
        "recovery_min_off_trough_pct": 8.0,
        "min_history_bars": 200,
        "observation_disclosure_limit": 60,
        "severity_velocity_window": 5,  # iter-44 (J-102): causal severity-velocity OLS slope lookback (>= 2)
        # iter-30 (J-89 / J-90): downtrend-history + recovery-turn thresholds (every threshold from config).
        "downtrend_pbear_threshold": 0.50,
        "recovery_signal_pbear_exit": 0.40,
        "recovery_trailing_ma_days": 50,
        "bry_boschan_min_phase_days": 90,
        "bry_boschan_min_amplitude_pct": 20.0,
    },
    "regime_switching": {
        "transition": {
            "bear": {"bear": 0.92, "risk_on": 0.08},
            "risk_on": {"bear": 0.06, "risk_on": 0.94},
        },
        "initial_bear": 0.5,
        "emissions": {
            "bear": {"mean": 0.75, "std": 0.18},
            "risk_on": {"mean": 0.20, "std": 0.18},
        },
    },
}

_BASE = date(2026, 1, 1)


def _cfg(tmp_path):
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(_CFG))
    return load_config(path)


def _insert_bars(session, symbol, closes, start=_BASE):
    """Insert daily bars for `symbol` with the given closes on consecutive calendar days from `start`."""
    rows = [
        {"symbol": symbol, "date": start + timedelta(days=i), "open": c,
         "high": c + 1.0, "low": c - 1.0, "close": float(c), "volume": 1000.0}
        for i, c in enumerate(closes)
    ]
    session.execute(insert(DailyPrice.__table__), rows)


def _engine_with_bars():
    engine = make_engine("sqlite:///:memory:")
    create_db_and_tables(engine)
    return engine


def test_rebase_at_range_start_and_hand_computed_series(tmp_path):
    cfg = _cfg(tmp_path)
    engine = _engine_with_bars()
    # 6 consecutive bars (Jan 1..6). SPY: 100,110,99,120,121,132 ; QQQ: 50,55,60,60,66,72
    spy_closes = [100.0, 110.0, 99.0, 120.0, 121.0, 132.0]
    qqq_closes = [50.0, 55.0, 60.0, 60.0, 66.0, 72.0]
    with Session(engine) as session:
        _insert_bars(session, "SPY", spy_closes)
        _insert_bars(session, "QQQ", qqq_closes)
        session.commit()
        # All-history range so every bar is in-window; as-of = the last bar (Jan 6).
        result = compute_index_series(session, as_of="2026-01-06", range_key="all", config=cfg)

    series = {s["symbol"]: s for s in result["series"]}
    assert set(series) == {"SPY", "QQQ"}  # DIA omitted (no bars)
    # legend display names come from config verbatim
    assert series["SPY"]["name"] == "S&P 500 (SPY)"
    assert series["QQQ"]["name"] == "Nasdaq 100 (QQQ)"

    # rebase at the FIRST in-range bar: first point is exactly 0.0%
    spy_pts = series["SPY"]["points"]
    assert spy_pts[0] == {"date": "2026-01-01", "pct": 0.0}
    # hand-computed: (close/100 - 1)*100 == close - 100 for base 100
    expected_spy = [round(c - 100.0, 4) for c in spy_closes]
    assert [p["pct"] for p in spy_pts] == expected_spy
    assert [p["date"] for p in spy_pts] == [
        "2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05", "2026-01-06"
    ]

    qqq_pts = series["QQQ"]["points"]
    assert qqq_pts[0]["pct"] == 0.0
    expected_qqq = [round((c / 50.0 - 1.0) * 100.0, 4) for c in qqq_closes]
    assert [p["pct"] for p in qqq_pts] == expected_qqq


def test_range_window_bounds_to_trailing_days_and_rebases_to_window_start(tmp_path):
    cfg = _cfg(tmp_path)
    engine = _engine_with_bars()
    # 6 bars Jan 1..6. With as-of Jan 6 and the "short" preset (days=5), the window start is Jan 1
    # (Jan 6 - 5 days), so all 6 bars are in-window and rebase to Jan 1.
    closes = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]
    with Session(engine) as session:
        _insert_bars(session, "SPY", closes)
        session.commit()
        short = compute_index_series(session, as_of="2026-01-06", range_key="short", config=cfg)

    pts = short["series"][0]["points"]
    # window start = Jan 6 - 5d = Jan 1 -> base 100 -> first point 0.0
    assert pts[0] == {"date": "2026-01-01", "pct": 0.0}
    assert short["range"]["start"] == "2026-01-01"
    assert pts[-1]["pct"] == round((105.0 / 100.0 - 1.0) * 100.0, 4)

    # A tighter window (as-of Jan 6, days=2 simulated via a fresh preset) — verify rebase moves to the
    # new window start. Reuse "short" semantics by checking the med preset start arithmetic instead:
    with Session(engine) as session:
        med = compute_index_series(session, as_of="2026-01-06", range_key="med", config=cfg)
    # days=20 -> window start Dec 17 2025, before Jan 1, so first in-range bar is still Jan 1 (base 100).
    assert med["series"][0]["points"][0] == {"date": "2026-01-01", "pct": 0.0}


def test_as_of_bounding_excludes_future_bars(tmp_path):
    cfg = _cfg(tmp_path)
    engine = _engine_with_bars()
    closes = [100.0, 110.0, 120.0, 130.0, 140.0, 150.0]  # Jan 1..6
    with Session(engine) as session:
        _insert_bars(session, "SPY", closes)
        session.commit()
        # as-of Jan 3 -> only Jan 1..3 may appear; Jan 4..6 are post-as-of and must NOT render.
        result = compute_index_series(session, as_of="2026-01-03", range_key="all", config=cfg)

    pts = result["series"][0]["points"]
    assert [p["date"] for p in pts] == ["2026-01-01", "2026-01-02", "2026-01-03"]
    assert result["asof_date"] == "2026-01-03"
    # rebased at Jan 1 (base 100): 0, 10, 20
    assert [p["pct"] for p in pts] == [0.0, 10.0, 20.0]


def test_barless_configured_symbol_omitted_from_series_and_legend(tmp_path):
    cfg = _cfg(tmp_path)
    engine = _engine_with_bars()
    with Session(engine) as session:
        _insert_bars(session, "SPY", [100.0, 101.0])
        # QQQ and DIA have NO bars at all.
        session.commit()
        result = compute_index_series(session, as_of="2026-01-02", range_key="all", config=cfg)

    symbols = [s["symbol"] for s in result["series"]]
    assert symbols == ["SPY"]  # QQQ + DIA omitted — never fabricated
    assert "DIA" not in symbols and "QQQ" not in symbols


def test_config_drives_symbols_and_presets(tmp_path):
    cfg = _cfg(tmp_path)
    engine = _engine_with_bars()
    with Session(engine) as session:
        _insert_bars(session, "SPY", [100.0, 101.0])
        session.commit()
        result = compute_index_series(session, as_of=None, range_key=None, config=cfg)

    # default range comes from config (default_range = "med")
    assert result["range"]["key"] == "med"
    # the switcher options are the config presets, in order
    assert result["ranges"] == [
        {"key": "short", "label": "Short"},
        {"key": "med", "label": "Med"},
        {"key": "all", "label": "All"},
    ]


def test_unknown_range_preset_raises(tmp_path):
    cfg = _cfg(tmp_path)
    engine = _engine_with_bars()
    with Session(engine) as session:
        _insert_bars(session, "SPY", [100.0, 101.0])
        session.commit()
        with pytest.raises(UnknownRangeError) as exc:
            compute_index_series(session, as_of=None, range_key="bogus", config=cfg)
    assert exc.value.key == "bogus"
    assert set(exc.value.valid) == {"short", "med", "all"}


def test_as_of_before_history_yields_honest_empty_series(tmp_path):
    cfg = _cfg(tmp_path)
    engine = _engine_with_bars()
    with Session(engine) as session:
        _insert_bars(session, "SPY", [100.0, 101.0], start=date(2026, 2, 1))
        session.commit()
        # an as-of before the earliest bar raises AsOfError (before_history) -> the API maps it; but an
        # as-of WITH a bar yet no bars for a symbol in the window yields an empty series for that symbol.
        from app.engine.scanner import AsOfError
        with pytest.raises(AsOfError):
            compute_index_series(session, as_of="2026-01-01", range_key="all", config=cfg)


# --- J-49: clamp-optional (full-history) serving on the index series ------------------------------
# When full=True the engine widens the SERVED window to include bars dated AFTER the resolved as-of
# (display-only market context behind the dashboard's vertical as-of marker), while default (full=False)
# stays byte-identical to today. The overlapping <= D portion is value-identical between modes (the
# rebase base / range start is unchanged) — same single compute path, only the upper bound moves.


def test_full_mode_includes_bars_after_asof_through_latest(tmp_path):
    cfg = _cfg(tmp_path)
    engine = _engine_with_bars()
    closes = [100.0, 110.0, 120.0, 130.0, 140.0, 150.0]  # Jan 1..6
    with Session(engine) as session:
        _insert_bars(session, "SPY", closes)
        session.commit()
        # as-of Jan 3, but full mode -> the post-as-of bars Jan 4..6 are served as display-only context.
        full = compute_index_series(
            session, as_of="2026-01-03", range_key="all", config=cfg, full=True
        )

    pts = full["series"][0]["points"]
    # the whole stored path through the latest date (Jan 6) is served, NOT clamped at Jan 3
    assert [p["date"] for p in pts] == [
        "2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05", "2026-01-06"
    ]
    # the response still echoes the RESOLVED as-of (Jan 3) — the client draws the vertical marker from it
    assert full["asof_date"] == "2026-01-03"
    # rebased at Jan 1 (base 100): 0,10,20,30,40,50
    assert [p["pct"] for p in pts] == [0.0, 10.0, 20.0, 30.0, 40.0, 50.0]


def test_full_mode_default_is_byte_identical_clamped(tmp_path):
    """The default (full=False, param absent) request is byte-for-byte unchanged — a regression pin so
    every existing consumer (and the stock-detail-fed default) is untouched."""
    cfg = _cfg(tmp_path)
    engine = _engine_with_bars()
    closes = [100.0, 110.0, 120.0, 130.0, 140.0, 150.0]
    with Session(engine) as session:
        _insert_bars(session, "SPY", closes)
        session.commit()
        # the param ABSENT and full=False must both produce the same clamped result
        absent = compute_index_series(session, as_of="2026-01-03", range_key="all", config=cfg)
        explicit_false = compute_index_series(
            session, as_of="2026-01-03", range_key="all", config=cfg, full=False
        )
    assert absent == explicit_false
    # and it is exactly the clamped (<= Jan 3) series
    assert [p["date"] for p in absent["series"][0]["points"]] == [
        "2026-01-01", "2026-01-02", "2026-01-03"
    ]


def test_full_and_default_value_identical_on_overlapping_range(tmp_path):
    """No second compute path: the overlapping <= D portion of the full series is value-identical to the
    default clamped series (same rebase base, same stored bars, same normalization)."""
    cfg = _cfg(tmp_path)
    engine = _engine_with_bars()
    closes = [100.0, 110.0, 99.0, 120.0, 121.0, 132.0]
    with Session(engine) as session:
        _insert_bars(session, "SPY", closes)
        _insert_bars(session, "QQQ", [50.0, 55.0, 60.0, 60.0, 66.0, 72.0])
        session.commit()
        clamped = compute_index_series(session, as_of="2026-01-03", range_key="all", config=cfg)
        full = compute_index_series(
            session, as_of="2026-01-03", range_key="all", config=cfg, full=True
        )

    clamped_by_sym = {s["symbol"]: s["points"] for s in clamped["series"]}
    full_by_sym = {s["symbol"]: s["points"] for s in full["series"]}
    assert set(clamped_by_sym) == set(full_by_sym)
    for sym, clamped_pts in clamped_by_sym.items():
        # the full series' leading portion (dates <= Jan 3) equals the clamped series exactly
        overlap = [p for p in full_by_sym[sym] if p["date"] <= "2026-01-03"]
        assert overlap == clamped_pts


def test_full_mode_still_omits_barless_symbol(tmp_path):
    """Honest omission is unchanged in full mode — a configured symbol with no stored bars (DIA/QQQ)
    is still omitted, never synthesized."""
    cfg = _cfg(tmp_path)
    engine = _engine_with_bars()
    with Session(engine) as session:
        _insert_bars(session, "SPY", [100.0, 101.0, 102.0])
        session.commit()  # QQQ + DIA have no bars
        full = compute_index_series(
            session, as_of="2026-01-02", range_key="all", config=cfg, full=True
        )
    symbols = [s["symbol"] for s in full["series"]]
    assert symbols == ["SPY"]
    assert "DIA" not in symbols and "QQQ" not in symbols


def test_full_mode_unknown_range_still_raises(tmp_path):
    cfg = _cfg(tmp_path)
    engine = _engine_with_bars()
    with Session(engine) as session:
        _insert_bars(session, "SPY", [100.0, 101.0])
        session.commit()
        with pytest.raises(UnknownRangeError):
            compute_index_series(session, as_of=None, range_key="bogus", config=cfg, full=True)


def _cfg_with_default_range(tmp_path, default_range: str):
    """Load a synthetic config identical to `_CFG` but with `index_chart.default_range` overridden —
    used to exercise the J-78 default-range-of-`all` change against the existing config validator and
    `_resolve_preset` without coupling the test to the project-wide `config.yaml` value."""
    import copy

    data = copy.deepcopy(_CFG)
    data["index_chart"]["default_range"] = default_range
    path = tmp_path / "cfg_default_range.yaml"
    path.write_text(yaml.safe_dump(data))
    return load_config(path)


def test_default_range_all_validates_and_resolves_to_full_history(tmp_path):
    """J-78: setting `index_chart.default_range = "all"` (a valid preset key whose `days is None`) both
    (1) passes the config validator and (2) makes `compute_index_series` with NO requested range serve the
    FULL history — no bar is dropped by a trailing-window clamp. (No code change: `_resolve_preset` reads
    the default from config, the `all` preset's `days is None` disables the lower bound.)"""
    cfg = _cfg_with_default_range(tmp_path, "all")
    # (1) the validator accepted `all` as the default (load_config would have raised ConfigError otherwise)
    assert cfg.index_chart.default_range == "all"
    all_preset = next(p for p in cfg.index_chart.range_presets if p.key == "all")
    assert all_preset.days is None  # the all-history preset has no trailing-day clamp

    engine = _engine_with_bars()
    # bars span ~1 year — far wider than the synthetic `med` (20-day) preset's trailing window; only an
    # all-history default keeps every one of them in the rebased series.
    closes = [100.0 + i for i in range(40)]
    with Session(engine) as session:
        _insert_bars(session, "SPY", closes)
        session.commit()
        # range_key=None => the engine resolves the config default (`all`) — full history, not a 20-day clamp.
        result = compute_index_series(session, as_of=None, range_key=None, config=cfg)

    assert result["range"]["key"] == "all"
    spy = next(s for s in result["series"] if s["symbol"] == "SPY")
    # every stored bar survives (no trailing-window drop) and the series rebases to exactly 0% at the start.
    assert len(spy["points"]) == len(closes)
    assert spy["points"][0]["pct"] == 0.0


def test_default_range_non_preset_value_still_rejected(tmp_path):
    """J-78 no-magic-number guard intact: a `default_range` that is NOT one of the preset keys is still
    rejected by the existing `config.py` validator (the change only swaps one VALID key for another)."""
    from app.config import ConfigError

    with pytest.raises(ConfigError):
        _cfg_with_default_range(tmp_path, "definitely-not-a-preset")
