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
    "data_manager": {
        "providers": [{"id": "yahoo", "label": "Yahoo", "needs_key": False}],
        "default_source": "yahoo", "gap_preview": 60, "run_history_limit": 50,
        "import_chunking": {  # iter-22 (J-34) required block
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
    "etfs": {"index": ["SPY"], "sector": {"XLK": "Technology", "XLF": "Financials"}, "industry": {"SMH": {"name": "Semiconductors", "description": "Chip makers."}}, "volatility": ["^VIX"]},
    "index_chart": {  # J-44 required block (chart symbols/names + range presets from config)
        "symbols": [{"symbol": "SPY", "name": "S&P 500 (SPY)"}],
        "range_presets": [{"key": "all", "label": "All", "days": None}], "default_range": "all",
    },
    "themes": {"t1": ["AAA", "BBB"]},
    "buckets": {"A": 90, "B": 80, "C": 70, "D": 60},
    "indicators": {
        "ma_periods": [5, 10], "rs_windows": {"1m": 3, "3m": 5, "6m": 10},
        "atr_period": 5, "high_window_52w": 20, "vol_avg_period": 5,
        "min_history_bars": 40, "breadth_short_ma": 5, "breadth_long_ma": 10,
        # iter-13 volatility-family windows (required + validated positive) — synthetic small scale.
        "hv_window": 5, "semivol_window": 5, "vol_contraction_recent": 3, "vol_contraction_prior": 5,
        # iter-26 (J-16 item F): required window; >= this fixture's own max (high_window_52w=20) and
        # >= the patterns block's min_history_bars below (20).
        "max_lookback_bars": 20,
        # iter-40 (J-24 / B-201 risk-budget) required windows — synthetic small scale.
        "gap_window": 5, "worst_window_days": 5,
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
    # J-58: AAA is an SMH industry member; BBB is intentionally unmapped (proves the empty-state path).
    "stock_industries": {"AAA": ["SMH"]},
    "scanner": {"bootstrap_dates": ["2022-10-07"]},  # iter-5: scanner is a required config section
    "startup": {  # iter-28: startup is a required config section (fast-ready boot + warm-up tunables)
        "readiness_budget_seconds": 30.0,
        "warmup_batch_size": 1,
        "health_poll_interval_seconds": 2.0,
        "health_poll_idle_interval_seconds": 30.0,
    },
    "readiness": {  # iter-33: readiness is a required config section (daily preflight-verdict tunables)
        "freshness_max_age_days": 5,
        "severity": {"servability": "no-go", "freshness": "degraded", "integrity": "no-go", "drift": "degraded"},
        "verdict_history_path": "runs/x/preflight-verdict-history.jsonl",
    },
    "walk_forward": {  # iter-6: walk_forward is a required config section
        "history_years": 2, "asof_cadence": "quarterly", "horizons": [1, 5, 10, 20, 60],
        "min_sample": 30, "default_horizon": 20,
        "control_group": {"seed": 20240601, "top_n": 20, "peers_per_sector": 5},
        # iter-41 (J-25): required drawdown-expectations tunables (the /evidence panel).
        "underwater_horizons": [1, 5, 10, 20, 60], "streak_min_n": 10,
        "attribution": {  # J-19: attribution is a required walk_forward sub-section
            "top_contributors_k": 5,
            "rank_bands": [
                {"label": "1–10", "min": 1, "max": 10},
                {"label": "11–50", "min": 11, "max": 50},
                {"label": "51+", "min": 51, "max": None},
            ],
        },
    },
    "patterns": {  # iter-11: patterns is a required config section (small-scale to match this synth cfg)
        "vcp": {
            "lookback_bars": 20, "min_contractions": 2, "max_contractions": 4,
            "min_contraction_pct": 3, "max_base_depth_pct": 35, "contraction_shrink_ratio": 0.8,
            "max_last_contraction_pct": 12, "pivot_proximity_pct": 8, "volume_dryup_ratio": 0.9,
            "volume_window": 5, "min_history_bars": 20,
        },
        # iter-9: the two new detected patterns are required too (small-scale to match this synth cfg)
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
    "research": {  # iter-10: research is a required config section (Factor Lab — typed-column factor)
        "read_batch_size": 2000,  # iter-47 (J-105) required, boot-validated >= 1 streaming batch size
        "factor_lab": {
            "deciles": 10,
            "factors": [
                {"key": "leadership_score", "label": "Leadership", "family": "score",
                 "direction": "higher_better", "source": "leadership_score"},
            ],
            "combination": {  # iter-12/iter-18: combination is a required factor_lab sub-block
                "min_conditions": 2, "max_conditions": 3,
                "quantiles": [{"key": "half", "label": "Half (50%)", "fraction": 0.5}],
                # iter-18: composite rank-blend is a required sub-block (quantile = a real quantiles key)
                "composite": {"quantile": "half", "weighting": {"scheme": "equal", "default_weight": 1.0}},
                "default_conditions": [
                    {"factor": "leadership_score", "side": "top", "quantile": "half"},
                    {"factor": "leadership_score", "side": "bottom", "quantile": "half"},
                ],
            },
        },
    },
    "methodology": {  # iter-12: methodology is a required config section (one entry whose ref resolves)
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


# --- J-58: config-named/described industry ETFs + universe-member lists --------------------
# These are ADDITIVE reference metadata. The two central guarantees the iteration must prove:
#   1. every ranked ETF carries a config name + (for industry ETFs) a config description, and its
#      member list (sector -> stock_sectors, industry -> stock_industries), with an explicit EMPTY
#      list for an unmapped ETF (never fabricated);
#   2. attaching that metadata does NOT move any canonical value — score / rank / components /
#      rs_vs_spy / dist-52w / trend are byte-identical to a baseline computed with the metadata
#      stripped (the no-recompute guard; J-04 / J-06 must not move).
def test_industry_etf_name_and_description_come_from_config(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        result = score_sectors(session, asof, cfg)
    by_ticker = {r["ticker"]: r for r in result["rows"]}

    # An industry ETF reads its name/description from the etfs.industry catalog — NOT the bare ticker.
    kre = by_ticker["KRE"]
    assert kre["kind"] == "industry"
    assert kre["name"] == cfg.etfs.industry["KRE"].name == "Regional Banks (SPDR)"
    assert kre["name"] != "KRE"  # the bare-ticker fallback is gone
    assert kre["description"] == cfg.etfs.industry["KRE"].description
    assert kre["description"] is not None

    # A sector ETF keeps its etfs.sector name and has no description (named only, by contract).
    xlk = by_ticker["XLK"]
    assert xlk["kind"] == "sector"
    assert xlk["name"] == cfg.etfs.sector["XLK"] == "Technology"
    assert xlk["description"] is None


def test_member_lists_resolve_from_the_correct_mapping(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        result = score_sectors(session, asof, cfg)
    by_ticker = {r["ticker"]: r for r in result["rows"]}

    # Sector ETF members == the stocks whose stock_sectors value is this ETF's sector name.
    xlk = by_ticker["XLK"]
    expected_sector_members = sorted(t for t, s in cfg.stock_sectors.items() if s == "Technology")
    assert xlk["members"] == expected_sector_members
    assert len(xlk["members"]) > 0

    # Industry ETF members == the stocks mapped to this ETF ticker in stock_industries.
    smh = by_ticker["SMH"]
    expected_smh_members = sorted(t for t, etfs in cfg.stock_industries.items() if "SMH" in etfs)
    assert smh["members"] == expected_smh_members
    assert "NVDA" in smh["members"]
    # Every reported member is a real universe symbol (no fabrication).
    universe = set(cfg.universe.symbols)
    assert all(m in universe for m in smh["members"])


def test_unmapped_industry_etf_has_empty_member_list(loaded_engine):
    """KRE (Regional Banks) has NO mapped stock_industries member in the real config (the universe has
    no regional bank) — it must report an EMPTY member list (the UI then shows the explicit empty
    state), never a fabricated one. Its name still comes from config."""
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        result = score_sectors(session, asof, cfg)
    kre = next(r for r in result["rows"] if r["ticker"] == "KRE")
    # config ground truth: KRE is genuinely unmapped
    assert not any("KRE" in etfs for etfs in cfg.stock_industries.values())
    assert kre["members"] == []          # explicit empty — never fabricated
    assert kre["name"] == "Regional Banks (SPDR)"   # but still config-named


def test_metadata_does_not_move_any_canonical_value(loaded_engine):
    """The no-recompute guard (J-04 / J-06): stripping the J-58 reference metadata must leave the
    score / rank / components / rs_vs_spy / dist-52w / trend BYTE-IDENTICAL. We build the baseline by
    removing the additive keys from the engine output and comparing — if any canonical value moved,
    this fails loudly."""
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        result = score_sectors(session, asof, cfg)

    # The additive metadata keys — everything else is canonical and must be unchanged.
    additive_keys = {"description", "members"}
    canonical_keys = {
        "ticker", "kind", "name", "score", "bucket", "rs_vs_spy",
        "dist_from_52w_high_pct", "trend_label", "components", "rank",
    }
    for row in result["rows"]:
        # the row exposes exactly the canonical keys plus the two additive ones — nothing else moved
        assert set(row.keys()) == canonical_keys | additive_keys
        # description is None for sector rows, a string-or-None for industry rows; members is a list
        assert row["description"] is None or isinstance(row["description"], str)
        assert isinstance(row["members"], list)

    # Reconstruct the pre-J-58 baseline (metadata stripped) and assert the ordered ranking is intact:
    # ranks remain a dense 1..N descending-by-score sequence (the scored ordering is untouched).
    baseline = [{k: v for k, v in r.items() if k not in additive_keys} for r in result["rows"]]
    scores = [r["score"] for r in baseline]
    assert scores == sorted(scores, reverse=True)
    assert [r["rank"] for r in baseline] == list(range(1, len(baseline) + 1))
    # the row count is unchanged: 11 sector SPDRs + 20 industry ETFs
    assert len(baseline) == len(cfg.etfs.sector) + len(cfg.etfs.industry) == 31


def test_synthetic_industry_members_and_empty_state(tmp_path):
    """Synthetic end-to-end on _SYNTH_CFG: AAA is mapped to SMH (member), BBB is intentionally
    unmapped. The SMH industry row lists [AAA]; nothing fabricated for BBB."""
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(_SYNTH_CFG))
    cfg = load_config(path)

    engine = make_engine("sqlite:///:memory:")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for sym in ("SPY", "XLK", "XLF", "SMH"):
            _insert_ascending(session, sym, 60)
        session.commit()
        asof = latest_data_date(session)
        result = score_sectors(session, asof, cfg)

    by_ticker = {r["ticker"]: r for r in result["rows"]}
    smh = by_ticker["SMH"]
    assert smh["name"] == "Semiconductors"           # from the catalog, not "SMH"
    assert smh["description"] == "Chip makers."
    assert smh["members"] == ["AAA"]                  # AAA mapped; BBB intentionally absent
