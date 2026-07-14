"""Config loader: loads + validates the real config.yaml; rejects invalid configs explicitly."""
from __future__ import annotations

import copy

import pytest
import yaml

from app.config import ConfigError, load_config

MINIMAL_VALID = {
    "provider": "seed",
    "database": {"url": "sqlite:///:memory:"},
    # iter-3 made `data_manager` required (the Data Manager job limits come from config, never code).
    # iter-21 (J-33) added the required import provider catalog + default_source (the import sources +
    # each source's key requirement/env-var name come from config, never a hardcoded list).
    "data_manager": {
        "providers": [
            {"id": "yahoo", "label": "Yahoo", "needs_key": False, "supports_market_cap": True},
            {"id": "tiingo", "label": "Tiingo", "needs_key": True, "env_var": "TIINGO_API_KEY"},
        ],
        "default_source": "yahoo",
        "max_range_days": 370,
        "gap_preview": 60,
        "run_history_limit": 50,
        # iter-22 (J-34) made `import_chunking` required (the chunk/backoff/sleep tunables come from
        # config, never code). The smallest valid block: all sizes/retries/backoff positive, cap >= base.
        "import_chunking": {
            "symbol_batch_size": 25, "date_window_days": 90, "max_retries": 4,
            "backoff_base_seconds": 1.0, "backoff_cap_seconds": 30.0, "inter_request_sleep_seconds": 0.0,
            "fetch_workers": 4,  # J-46: bounded parallel fetch-pool size (>= 1)
            "backfill_workers": 4,  # J-53: bounded parallel backfill-pool size (>= 1)
        },
        # iter-29 (J-66) made `job_progress` required (the poll/heartbeat/granularity knobs come from
        # config, never code). The smallest valid block: both time knobs positive.
        "job_progress": {
            "poll_interval_seconds": 1.0, "heartbeat_stale_seconds": 20.0, "per_symbol_ticks": True,
        },
    },
    "universe": {
        "symbols": ["AAA", "BBB"],
        "filters": {"min_market_cap": 1, "min_dollar_vol": 1, "min_price": 1},
    },
    "etfs": {
        "index": ["SPY"],
        "sector": {"XLK": "Technology"},
        # J-58: etfs.industry is now a {ticker: {name, description}} catalog (name required).
        "industry": {"SMH": {"name": "Semiconductors", "description": "Chip makers."}},
        "volatility": ["^VIX"],
    },
    # J-44 made `index_chart` required (the major-indexes chart symbols/names + range presets come
    # from config, never code). The smallest valid block: >= 1 symbol, >= 1 preset, default a real key.
    "index_chart": {
        "symbols": [{"symbol": "SPY", "name": "S&P 500 (SPY)"}],
        "range_presets": [{"key": "all", "label": "All", "days": None}],
        "default_range": "all",
    },
    "themes": {"t1": ["AAA", "BBB"]},
    "buckets": {"A": 90, "B": 80, "C": 70, "D": 60},
    # iter-2 made these sections required + validated (see test_config_engine.py for the
    # validation-failure cases); a minimal *valid* config must now include them.
    "indicators": {
        "ma_periods": [20, 50, 150, 200],
        "rs_windows": {"1m": 21, "3m": 63, "6m": 126},
        "atr_period": 14,
        "high_window_52w": 252,
        "vol_avg_period": 50,
        "min_history_bars": 200,
        "breadth_short_ma": 50,
        "breadth_long_ma": 200,
        # iter-13 (J-30) volatility-factor-family windows (required + validated positive).
        "hv_window": 21,
        "semivol_window": 63,
        "vol_contraction_recent": 21,
        "vol_contraction_prior": 63,
        # iter-26 (J-16 item F): required window; mirrors config.yaml's real value (>= high_window_52w
        # 252 + margin; >= the patterns block's largest min_history_bars, 90).
        "max_lookback_bars": 320,
    },
    "sectors": {
        "weights": {
            "rs_spy_1m": 0.20,
            "rs_spy_3m": 0.25,
            "rs_spy_6m": 0.20,
            "ma_stack": 0.15,
            "dist_from_high": 0.10,
            "vol_trend": 0.10,
        },
        "trend_edges": [
            {"min": 70, "label": "Strong uptrend"},
            {"min": 0, "label": "Downtrend"},
        ],
    },
    "regime": {
        "vix_threshold": 20,
        "weights": {
            "index_ma_stack": 0.35,
            "breadth_above_50dma": 0.25,
            "breadth_above_200dma": 0.25,
            "new_high_low": 0.15,
        },
        "labels": ["Strong risk-on", "Risk-on", "Narrow leadership", "Choppy", "Defensive", "Risk-off"],
        "label_edges": [
            {"min": 80, "label": "Strong risk-on"},
            {"min": 0, "label": "Risk-off"},
        ],
    },
    # iter-3 made these sections required + validated (see test_config_engine.py for the
    # validation-failure cases); a minimal *valid* config must now include them.
    "scores": {
        "leadership": {"weights": {
            "rs_spy_1m": 0.15, "rs_spy_3m": 0.20, "rs_sector": 0.15, "rs_theme": 0.10,
            "ma_stack": 0.20, "high_proximity": 0.10, "up_down_vol": 0.10,
        }},
        "entry_quality": {"weights": {
            "dist_rising_20": 0.25, "contraction": 0.20, "support_nearby": 0.15,
            "structure": 0.20, "reward_risk": 0.20,
        }},
        "risk": {"weights": {
            "extension": 0.20, "atr_pct": 0.15, "liquidity": 0.10, "regime": 0.15,
            "sector_strength": 0.10, "gap_climax": 0.15, "below_ma": 0.10, "rs_deterioration": 0.05,
        }},
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
        "invalidation": {"ma_period": 50},
    },
    "stock_sectors": {"AAA": "Technology", "BBB": "Technology"},
    # J-58: stock -> industry-group ETF membership (config-defined, many-to-many; each ticker must be
    # in etfs.industry). Optional (default-empty) but exercised here so the validator path is covered.
    "stock_industries": {"AAA": ["SMH"]},
    # iter-5 made `scanner` required (bootstrap dates come from config, never code).
    "scanner": {"bootstrap_dates": ["2022-10-07", "2025-04-04"]},
    # iter-28 made `startup` required (fast-ready boot + warm-up tunables come from config, never code).
    "startup": {
        "readiness_budget_seconds": 30.0,
        "warmup_batch_size": 1,
        "health_poll_interval_seconds": 2.0,
        "health_poll_idle_interval_seconds": 30.0,
    },
    # iter-33 made `readiness` required (the daily preflight-verdict tunables come from config, never
    # code): the freshness threshold + the per-component severity map (must cover all four components —
    # iter-35 added `drift` — and include at least one "degraded" and one "no-go").
    "readiness": {
        "freshness_max_age_days": 5,
        "severity": {"servability": "no-go", "freshness": "degraded", "integrity": "no-go", "drift": "degraded"},
        "verdict_history_path": "runs/x/preflight-verdict-history.jsonl",
    },
    # iter-6 made `walk_forward` required (forward-testing params come from config, never code).
    # J-19 made `walk_forward.attribution` required (rank-band edges + list size come from config).
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
    # iter-11 made `patterns` required (the VCP detector thresholds come from config, never code);
    # iter-9 made `pullback_to_rising_dma` + `flat_base_breakout` required too (same pattern as every
    # newly-required section — a from-scratch valid config must include them).
    "patterns": {
        "vcp": {
            "lookback_bars": 65, "min_contractions": 2, "max_contractions": 4,
            "min_contraction_pct": 3, "max_base_depth_pct": 35, "contraction_shrink_ratio": 0.8,
            "max_last_contraction_pct": 12, "pivot_proximity_pct": 8, "volume_dryup_ratio": 0.9,
            "volume_window": 10, "min_history_bars": 65,
        },
        "pullback_to_rising_dma": {
            "ma_period": 50, "min_history_bars": 90, "trend_lookback_bars": 40,
            "min_dma_slope_pct": 1.5, "max_dist_above_dma_pct": 5.0, "max_undercut_pct": 2.0,
            "max_pullback_depth_pct": 18, "volume_window": 10,
        },
        "flat_base_breakout": {
            "lookback_bars": 45, "min_history_bars": 45, "base_window": 25,
            "max_base_depth_pct": 15, "pivot_proximity_pct": 6.0,
            "volume_window": 10, "min_breakout_volume_ratio": 1.0,
        },
    },
    # iter-10 made `research` required (the Factor Lab decile count + factor catalog come from config,
    # never code). The smallest valid block: deciles > 1 + >= 1 factor whose source resolves (a typed
    # score column needs no scores.* component lookup) — the established pattern for a newly-required section.
    "research": {
        # iter-47 (J-105): research.read_batch_size is a required, boot-validated (>= 1) streaming batch
        # size for the heavy read-path builders (no inline batch literal in research.py / forward_testing.py).
        "read_batch_size": 2000,
        "factor_lab": {
            "deciles": 10,
            "factors": [
                {"key": "leadership_score", "label": "Leadership", "family": "score",
                 "direction": "higher_better", "source": "leadership_score"},
            ],
            # iter-12 made `combination` required (the multi-factor cohort limits + quantile vocabulary +
            # default conditions come from config, never code). The smallest valid block: 1 <= min <= max,
            # >= 1 quantile (fraction in (0,1), unique key), and default_conditions referencing the single
            # factor + a real quantile key, count within [min, max]. iter-18 adds the required `composite`
            # rank-blend sub-block (quantile = a real quantiles key; weighting scheme + default_weight > 0).
            "combination": {
                "min_conditions": 2,
                "max_conditions": 3,
                "quantiles": [{"key": "half", "label": "Half (50%)", "fraction": 0.5}],
                "composite": {"quantile": "half", "weighting": {"scheme": "equal", "default_weight": 1.0}},
                "default_conditions": [
                    {"factor": "leadership_score", "side": "top", "quantile": "half"},
                    {"factor": "leadership_score", "side": "bottom", "quantile": "half"},
                ],
            },
        },
    },
    # iter-12 made `methodology` required (the config-backed Setup & Pattern catalog). The smallest
    # valid catalog: >= 1 entry whose refs resolve (completeness is build_catalog's job, not the loader's).
    "methodology": {
        "intro": "Glossary.",
        "entries": [
            {
                "key": "Actionable",
                "kind": "setup",
                "name": "Actionable",
                "meaning": "A strong leader at a constructive entry.",
                "example": "Leadership high, Entry high, Risk low in Risk-on -> Actionable.",
                "thresholds": [
                    {"label": "Leadership", "cmp": ">=", "ref": "decision_rules.actionable.leadership"},
                    {"label": "Regime", "text": "Risk-on only."},
                ],
            },
        ],
    },
    # iter-29 made `market_phase` + `regime_switching` required (the read-only Market Phase & Severity
    # layer's edges/weights/thresholds + the deterministic 2-state filter params come from config, never
    # code). The smallest valid blocks: the five severity weights covering the named set + summing ~1.0,
    # phase edges descending covering 0..100, positive scalars; the 2x2 transition (rows summing ~1.0,
    # both states), initial_bear in [0,1], per-state emissions.
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


def _write(tmp_path, data, name="cfg.yaml"):
    path = tmp_path / name
    path.write_text(yaml.safe_dump(data))
    return path


def test_loads_real_config():
    cfg = load_config()
    assert cfg.provider == "seed"
    assert len(cfg.universe.symbols) >= 100
    assert "SPY" in cfg.etfs.index
    assert len(cfg.etfs.sector) == 11
    assert "ai_data_centre" in cfg.themes
    assert cfg.buckets.A > cfg.buckets.B > cfg.buckets.C > cfg.buckets.D


def test_minimal_valid_config_loads(tmp_path):
    cfg = load_config(_write(tmp_path, MINIMAL_VALID))
    assert cfg.provider == "seed"
    assert cfg.universe.symbols == ["AAA", "BBB"]


def test_unknown_provider_raises(tmp_path):
    data = copy.deepcopy(MINIMAL_VALID)
    data["provider"] = "bogus_provider"
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_missing_required_key_raises(tmp_path):
    data = copy.deepcopy(MINIMAL_VALID)
    del data["universe"]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_empty_universe_raises(tmp_path):
    data = copy.deepcopy(MINIMAL_VALID)
    data["universe"]["symbols"] = []
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_buckets_not_descending_raises(tmp_path):
    data = copy.deepcopy(MINIMAL_VALID)
    data["buckets"] = {"A": 60, "B": 70, "C": 80, "D": 90}
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_theme_member_outside_universe_raises(tmp_path):
    data = copy.deepcopy(MINIMAL_VALID)
    data["themes"]["t1"] = ["AAA", "ZZZ_NOT_IN_UNIVERSE"]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_missing_file_raises(tmp_path):
    with pytest.raises(ConfigError):
        load_config(tmp_path / "does_not_exist.yaml")


# iter-47 (J-105) — research.read_batch_size is required + boot-validated `>= 1` (mirrors
# startup.warmup_batch_size). It is the single source of the streaming batch size the heavy research
# read-path builders pass to yield_per — there is NO inline batch literal in research.py/forward_testing.py.
def test_research_read_batch_size_below_one_raises(tmp_path):
    """read_batch_size < 1 is a loud ConfigError — never a silent default (a 0/negative batch would break
    the streamed reads)."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["research"]["read_batch_size"] = 0
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_research_read_batch_size_missing_raises(tmp_path):
    """read_batch_size is REQUIRED (like warmup_batch_size) — omitting it fails the boot."""
    data = copy.deepcopy(MINIMAL_VALID)
    del data["research"]["read_batch_size"]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_research_read_batch_size_loads_from_real_config():
    """The real config.yaml supplies a valid (>= 1) research.read_batch_size."""
    cfg = load_config()
    assert isinstance(cfg.research.read_batch_size, int)
    assert cfg.research.read_batch_size >= 1


# --- J-58: etfs.industry catalog + stock_industries membership validation -------------------
def test_industry_catalog_loads_with_name_and_description(tmp_path):
    """The new etfs.industry catalog (ticker -> {name, description}) loads and exposes typed access."""
    cfg = load_config(_write(tmp_path, MINIMAL_VALID))
    assert cfg.etfs.industry["SMH"].name == "Semiconductors"
    assert cfg.etfs.industry["SMH"].description == "Chip makers."


def test_industry_catalog_missing_name_raises(tmp_path):
    """A malformed industry entry (no `name`) is a loud ConfigError — never a silent default."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["etfs"]["industry"] = {"SMH": {"description": "no name here"}}
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_industry_catalog_blank_name_raises(tmp_path):
    """An empty-string name is also rejected (min_length=1) — no bare fallback."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["etfs"]["industry"] = {"SMH": {"name": ""}}
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_stock_industries_member_outside_universe_raises(tmp_path):
    """A stock_industries KEY that is not a universe symbol is a loud error."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["stock_industries"] = {"ZZZ_NOT_IN_UNIVERSE": ["SMH"]}
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_stock_industries_unknown_etf_ticker_raises(tmp_path):
    """A stock_industries value ticker that is not in the etfs.industry catalog is a loud error."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["stock_industries"] = {"AAA": ["NOT_AN_INDUSTRY_ETF"]}
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_stock_industries_is_optional(tmp_path):
    """stock_industries is optional (default-empty) — a config omitting it still loads honestly."""
    data = copy.deepcopy(MINIMAL_VALID)
    del data["stock_industries"]
    cfg = load_config(_write(tmp_path, data))
    assert cfg.stock_industries == {}


def test_real_config_industry_catalog_and_memberships(tmp_path):
    """The REAL config.yaml has a fully-named industry catalog and a valid stock_industries map."""
    cfg = load_config()
    # every industry ETF is named (no bare-ticker fallback anywhere)
    assert all(entry.name and entry.name != ticker for ticker, entry in cfg.etfs.industry.items())
    # every membership references a real universe symbol + a real catalog ticker
    universe = set(cfg.universe.symbols)
    catalog = set(cfg.etfs.industry.keys())
    for stock, etfs in cfg.stock_industries.items():
        assert stock in universe
        assert all(e in catalog for e in etfs)


# --- iter-12: methodology section (J-12) ----------------------------------------------------

def test_methodology_minimal_valid_loads(tmp_path):
    """MINIMAL_VALID (incl. the now-required methodology section) still loads — the from-scratch
    fixture stays valid (the established pattern for every newly-required section, iter-2/3/5/6/11)."""
    cfg = load_config(_write(tmp_path, MINIMAL_VALID))
    assert cfg.methodology.entries
    assert cfg.methodology.entries[0].key == "Actionable"


def test_methodology_unresolvable_ref_raises(tmp_path):
    """A threshold whose ref points at a non-existent config path fails the boot loudly (anti-goal:
    No fabricated data — never a silent/placeholder threshold)."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["methodology"]["entries"][0]["thresholds"][0]["ref"] = "decision_rules.nope.missing"
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_methodology_threshold_requires_ref_xor_text(tmp_path):
    """Each threshold row carries EXACTLY one of `ref`/`text` — both (or neither) is rejected."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["methodology"]["entries"][0]["thresholds"][0]["text"] = "oops both"
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# --- iter-3: data_manager section (J-17) ----------------------------------------------------

def test_data_manager_minimal_valid_loads(tmp_path):
    """MINIMAL_VALID (incl. the now-required data_manager section + the iter-21 import catalog) still
    loads, and the real config exposes the typed limits (the established pattern for every newly-required
    section)."""
    cfg = load_config(_write(tmp_path, MINIMAL_VALID))
    assert cfg.data_manager.default_source == "yahoo"
    assert cfg.data_manager.provider_ids() == ["yahoo", "tiingo"]
    assert cfg.data_manager.max_range_days == 370
    real = load_config()
    assert real.data_manager.max_range_days > 0 and real.data_manager.gap_preview > 0


def test_data_manager_nonpositive_limit_raises(tmp_path):
    """A non-positive job limit fails the boot loudly — never a silent default (anti-goal: explicit)."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["data_manager"]["max_range_days"] = 0
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# --- iter-22 (J-34): the config-driven chunked-import block + boot validation ----------------
def test_import_chunking_minimal_valid_loads(tmp_path):
    """MINIMAL_VALID (incl. the now-required import_chunking block) still loads, and the real config
    exposes the typed chunk tunables (the established pattern for every newly-required section)."""
    cfg = load_config(_write(tmp_path, MINIMAL_VALID))
    assert cfg.data_manager.import_chunking.symbol_batch_size == 25
    assert cfg.data_manager.import_chunking.max_retries == 4
    real = load_config()
    ic = real.data_manager.import_chunking
    assert ic.symbol_batch_size > 0 and ic.date_window_days > 0 and ic.max_retries > 0
    assert ic.backoff_cap_seconds >= ic.backoff_base_seconds > 0
    assert ic.inter_request_sleep_seconds >= 0


@pytest.mark.parametrize(
    "field", ["symbol_batch_size", "date_window_days", "max_retries", "backoff_base_seconds", "backoff_cap_seconds"]
)
def test_import_chunking_nonpositive_raises(tmp_path, field):
    """A non-positive chunk/retry/backoff value fails the boot loudly — never a silent default (anti-goal:
    No magic numbers — every chunk/backoff number comes from config and is validated)."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["data_manager"]["import_chunking"][field] = 0
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_import_chunking_inter_request_sleep_may_be_zero(tmp_path):
    """`inter_request_sleep_seconds` MAY be 0 (no polite delay) — that is a VALID config, not an error."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["data_manager"]["import_chunking"]["inter_request_sleep_seconds"] = 0.0
    cfg = load_config(_write(tmp_path, data))
    assert cfg.data_manager.import_chunking.inter_request_sleep_seconds == 0.0


def test_import_chunking_cap_below_base_raises(tmp_path):
    """The backoff cap MUST be >= the base (an exponential backoff can't shrink below its starting wait)."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["data_manager"]["import_chunking"]["backoff_base_seconds"] = 10.0
    data["data_manager"]["import_chunking"]["backoff_cap_seconds"] = 5.0
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# --- J-46: the config-set parallel fetch-pool size + boot validation -------------------------
def test_fetch_workers_loads_from_config(tmp_path):
    """`fetch_workers` is a typed required field on the import_chunking block — the real committed config
    sets it > 1 (a parallel pool, not a magic-number literal in data_manager.py), and MINIMAL_VALID loads."""
    cfg = load_config(_write(tmp_path, MINIMAL_VALID))
    assert cfg.data_manager.import_chunking.fetch_workers == 4
    real = load_config()
    assert real.data_manager.import_chunking.fetch_workers >= 1
    assert real.data_manager.import_chunking.fetch_workers > 1  # committed default is a real parallel pool


def test_fetch_workers_one_is_valid_serial(tmp_path):
    """`fetch_workers: 1` is VALID — it is effectively serial (a degenerate single-worker pool), not an error."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["data_manager"]["import_chunking"]["fetch_workers"] = 1
    cfg = load_config(_write(tmp_path, data))
    assert cfg.data_manager.import_chunking.fetch_workers == 1


@pytest.mark.parametrize("bad", [0, -1])
def test_fetch_workers_below_one_raises(tmp_path, bad):
    """`fetch_workers` of 0 / negative fails the boot loudly (a pool must have >= 1 worker) — never a
    silent default (anti-goal: No magic numbers — the pool size comes from config and is validated)."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["data_manager"]["import_chunking"]["fetch_workers"] = bad
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_fetch_workers_missing_raises(tmp_path):
    """A missing `fetch_workers` key fails the boot (it is a required typed field, like the other
    import_chunking tunables) — never a silent default."""
    data = copy.deepcopy(MINIMAL_VALID)
    del data["data_manager"]["import_chunking"]["fetch_workers"]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_backfill_workers_loads_from_config(tmp_path):
    """`backfill_workers` (J-53) is a typed required field on the import_chunking block — the real
    committed config sets it > 1 (a parallel backfill pool, not a magic-number literal in
    data_manager.py), and MINIMAL_VALID loads it."""
    cfg = load_config(_write(tmp_path, MINIMAL_VALID))
    assert cfg.data_manager.import_chunking.backfill_workers == 4
    real = load_config()
    assert real.data_manager.import_chunking.backfill_workers >= 1
    assert real.data_manager.import_chunking.backfill_workers > 1  # committed default is a real parallel pool


def test_backfill_workers_one_is_valid_serial(tmp_path):
    """`backfill_workers: 1` is VALID — it is the sequential baseline (a degenerate single-worker pool),
    not an error (the byte-identical sequential path the parallel build must equal)."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["data_manager"]["import_chunking"]["backfill_workers"] = 1
    cfg = load_config(_write(tmp_path, data))
    assert cfg.data_manager.import_chunking.backfill_workers == 1


@pytest.mark.parametrize("bad", [0, -1])
def test_backfill_workers_below_one_raises(tmp_path, bad):
    """`backfill_workers` of 0 / negative fails the boot loudly (a pool must have >= 1 worker) — never a
    silent default (anti-goal: No magic numbers — the J-53 pool size comes from config and is validated)."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["data_manager"]["import_chunking"]["backfill_workers"] = bad
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_backfill_workers_missing_raises(tmp_path):
    """A missing `backfill_workers` key fails the boot (it is a required typed field, like the other
    import_chunking tunables) — never a silent default."""
    data = copy.deepcopy(MINIMAL_VALID)
    del data["data_manager"]["import_chunking"]["backfill_workers"]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# --- iter-29 (J-66): the fine-grained job-progress knobs (poll/heartbeat/granularity) ------------
def test_job_progress_loads_from_config(tmp_path):
    """`job_progress` (J-66) is a required typed block — the poll/heartbeat/granularity knobs come from
    config, never a literal in the frontend job card or data_manager.py. The real committed config and
    MINIMAL_VALID both load it; the time knobs are positive and `per_symbol_ticks` is a bool."""
    cfg = load_config(_write(tmp_path, MINIMAL_VALID))
    jp = cfg.data_manager.job_progress
    assert jp.poll_interval_seconds == 1.0
    assert jp.heartbeat_stale_seconds == 20.0
    assert jp.per_symbol_ticks is True
    real = load_config()
    assert real.data_manager.job_progress.poll_interval_seconds > 0
    assert real.data_manager.job_progress.heartbeat_stale_seconds > 0
    assert isinstance(real.data_manager.job_progress.per_symbol_ticks, bool)


@pytest.mark.parametrize("field", ["poll_interval_seconds", "heartbeat_stale_seconds"])
def test_job_progress_nonpositive_raises(tmp_path, field):
    """A non-positive poll/heartbeat time knob fails the boot loudly — never a silent default
    (anti-goal: No magic numbers — the J-66 progress knobs come from config and are validated)."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["data_manager"]["job_progress"][field] = 0
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_job_progress_missing_raises(tmp_path):
    """A missing `job_progress` block fails the boot (it is a required typed section, like
    import_chunking) — never a silent default."""
    data = copy.deepcopy(MINIMAL_VALID)
    del data["data_manager"]["job_progress"]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# --- iter-21 (J-33): the config-driven import provider catalog + boot validation -----------
def test_provider_catalog_is_config_driven(tmp_path):
    """The catalog (the source list + each source's key requirement/env-var NAME) comes from config —
    not a hardcoded list in code. The real config exposes the named sources with their requirements."""
    real = load_config()
    ids = real.data_manager.provider_ids()
    assert "yahoo" in ids and "tiingo" in ids and "stooq" in ids
    yahoo = real.data_manager.provider_by_id("yahoo")
    assert yahoo.needs_key is False and yahoo.env_var is None
    tiingo = real.data_manager.provider_by_id("tiingo")
    assert tiingo.needs_key is True and tiingo.env_var == "TIINGO_API_KEY"


def test_provider_needs_key_without_env_var_raises(tmp_path):
    """A `needs_key` source MUST declare its env_var NAME (so the key can be read from the environment) —
    a missing env_var fails the boot loudly (anti-goal: keys are env-or-session, never hard-coded)."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["data_manager"]["providers"] = [
        {"id": "yahoo", "label": "Yahoo", "needs_key": False},
        {"id": "tiingo", "label": "Tiingo", "needs_key": True},  # needs_key but no env_var
    ]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_provider_duplicate_id_raises(tmp_path):
    """Two catalog entries with the same `id` fail the boot loudly (the id is the resolution key)."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["data_manager"]["providers"] = [
        {"id": "yahoo", "label": "Yahoo", "needs_key": False},
        {"id": "yahoo", "label": "Yahoo Two", "needs_key": False},
    ]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_default_source_not_in_catalog_raises(tmp_path):
    """`default_source` MUST be a real catalog id — a default outside the catalog fails the boot loudly
    (otherwise an omitted-source fetch could not resolve a provider)."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["data_manager"]["default_source"] = "not_a_source"
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# --- iter-9: the two new detected-pattern blocks (J-28) -------------------------------------

def test_new_patterns_minimal_valid_loads(tmp_path):
    """MINIMAL_VALID (incl. the now-required pullback/flat-base blocks) still loads, and the real
    config exposes the typed thresholds (the established pattern for every newly-required section)."""
    cfg = load_config(_write(tmp_path, MINIMAL_VALID))
    assert cfg.patterns.pullback_to_rising_dma.ma_period == 50
    assert cfg.patterns.flat_base_breakout.base_window == 25
    real = load_config()
    assert real.patterns.pullback_to_rising_dma.max_pullback_depth_pct > 0
    assert real.patterns.flat_base_breakout.max_base_depth_pct > 0


def test_pullback_ma_period_not_an_indicator_raises(tmp_path):
    """The pullback MA basis MUST be one of indicators.ma_periods (a single canonical MA) — a value
    outside that set fails the boot loudly (cross-field check on the top-level Config), not a silent
    second MA basis."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["patterns"]["pullback_to_rising_dma"]["ma_period"] = 999  # not in [20, 50, 150, 200]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_pullback_insufficient_history_for_slope_raises(tmp_path):
    """min_history_bars must cover ma_period + trend_lookback_bars (else the DMA slope is uncomputable)
    — an under-sized history fails the boot, never a silent default."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["patterns"]["pullback_to_rising_dma"]["min_history_bars"] = 50  # < 50 + 40
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_pullback_nonpositive_percent_raises(tmp_path):
    """A non-positive pullback-depth cap is invalid (a pullback must have some depth budget)."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["patterns"]["pullback_to_rising_dma"]["max_pullback_depth_pct"] = 0
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_pullback_undercut_may_be_zero(tmp_path):
    """`max_undercut_pct` MAY be 0 (no undercut tolerated) — that is a VALID config, not an error."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["patterns"]["pullback_to_rising_dma"]["max_undercut_pct"] = 0
    cfg = load_config(_write(tmp_path, data))
    assert cfg.patterns.pullback_to_rising_dma.max_undercut_pct == 0


def test_flat_base_base_window_exceeds_lookback_raises(tmp_path):
    """The base must fit inside the lookback window — base_window > lookback_bars fails the boot."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["patterns"]["flat_base_breakout"]["base_window"] = 50  # > lookback_bars (45)
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_flat_base_nonpositive_ratio_raises(tmp_path):
    """A non-positive breakout-volume ratio is invalid (volume must be a positive multiple)."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["patterns"]["flat_base_breakout"]["min_breakout_volume_ratio"] = 0
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# ==================================================================================================
# iter-32 — J-91 conditioning-band catalog + J-92 macro config validation (typed/validated blocks).
# ==================================================================================================
def test_real_config_carries_downtrend_opportunity_and_macro():
    """The real config.yaml carries the J-91 conditioning-band catalog + the J-92 macro block (env-var
    name + series + default-OFF legs)."""
    cfg = load_config()
    do = cfg.research.downtrend_opportunity
    assert [b.key for b in do.severity_bands]  # contiguous full-cover validated at load
    assert [b.key for b in do.pbear_bands]
    assert cfg.macro.env_var  # the env-var NAME only (never a key value)
    assert [s.id for s in cfg.macro.series]
    # macro ships DEFAULT-OFF on every leg (so default figures stay byte-identical)
    assert cfg.macro.enable.severity is False
    assert cfg.macro.enable.regime_switching is False
    assert cfg.macro.enable.study is False


def test_conditioning_band_catalog_must_be_contiguous_full_cover():
    """J-91: a band catalog with a GAP (not full-cover) is rejected at load — so every displayable reading
    lands in exactly one band (the study never drops a row)."""
    from app.config import ConditioningBand, DowntrendOpportunityCfg

    good_pbear = [
        ConditioningBand(key="lo", label="lo", min=0.0, max=0.5),
        ConditioningBand(key="hi", label="hi", min=0.5, max=1.0),
    ]
    # a severity catalog with a GAP (50..70 missing) -> ValueError
    with pytest.raises(ValueError, match="contiguous|must end|must start"):
        DowntrendOpportunityCfg(
            severity_bands=[
                ConditioningBand(key="a", label="a", min=0.0, max=50.0),
                ConditioningBand(key="b", label="b", min=70.0, max=100.0),  # gap 50..70
            ],
            pbear_bands=good_pbear,
        )
    # a catalog that does not reach the scale top -> ValueError
    with pytest.raises(ValueError, match="must end"):
        DowntrendOpportunityCfg(
            severity_bands=[ConditioningBand(key="a", label="a", min=0.0, max=80.0)],
            pbear_bands=good_pbear,
        )


def test_macro_config_validates_unique_ids_and_lag():
    """J-92: macro config validation — duplicate series ids rejected; a negative publication lag rejected;
    a duplicate proxy symbol rejected."""
    from app.config import MacroCfg, MacroSeriesCfg

    with pytest.raises(ValueError, match="duplicate ids"):
        MacroCfg(env_var="FRED_API_KEY", series=[
            MacroSeriesCfg(id="x", fred_series_id="A", label="A", publication_lag_days=1),
            MacroSeriesCfg(id="x", fred_series_id="B", label="B", publication_lag_days=1),
        ])
    with pytest.raises(ValueError, match="publication_lag_days must be >= 0"):
        MacroSeriesCfg(id="x", fred_series_id="A", label="A", publication_lag_days=-1)
    with pytest.raises(ValueError, match="duplicate proxy_symbol"):
        MacroCfg(env_var="FRED_API_KEY", series=[
            MacroSeriesCfg(id="x", fred_series_id="A", label="A", publication_lag_days=1, proxy_symbol="^Z"),
            MacroSeriesCfg(id="y", fred_series_id="B", label="B", publication_lag_days=1, proxy_symbol="^Z"),
        ])


def test_macro_defaults_when_omitted(tmp_path):
    """J-92: a config OMITTING the macro block + the downtrend block still loads (additive, default-OFF) —
    so a config predating these blocks (and the inline test fixtures) is unaffected."""
    cfg = load_config(_write(tmp_path, MINIMAL_VALID))
    assert cfg.macro.enable.severity is False
    assert cfg.macro.series == []
    assert [b.key for b in cfg.research.downtrend_opportunity.severity_bands]  # built-in default catalog


# ==================================================================================================
# iter-9 — the online-FDR (LORD++) staging economy config (evidence.staging_ledger_path + evidence.fdr).
# ==================================================================================================
def test_real_config_activates_fdr_for_staging_iter10():
    """The real config.yaml carries the iter-9 staging ledger + the online-FDR block, and goal-mcp-loop
    iter-10 ACTIVATES the economy (`fdr.enabled: true`) for the wide multi-horizon staging exploration. The
    honesty fence in `verify_edge` keeps this fenced to staging — the canonical `/evidence` bar stays strict
    Bonferroni. The CODE default is still off (proven by `test_fdr_and_staging_default_when_omitted`)."""
    cfg = load_config()
    assert cfg.evidence.ledger_path.endswith("certified-claims.jsonl")
    assert cfg.evidence.staging_ledger_path.endswith("staging-ledger.jsonl")
    # the two ledgers are DIFFERENT files — exploration cannot contaminate canonical.
    assert cfg.evidence.staging_ledger_path != cfg.evidence.ledger_path
    assert cfg.evidence.fdr.enabled is True           # iter-10: ACTIVATED for the staging economy only
    assert 0.0 < cfg.evidence.fdr.alpha < 1.0
    assert cfg.evidence.fdr.gamma_exponent > 1.0      # a summable spending sequence


def test_real_config_opens_multi_horizon_triad_aperture_iter10():
    """goal-mcp-loop iter-10 (Part B Phase 1): the real config opens the triad scan aperture beyond h20 and
    raises the multiple-testing haircut, and carries the FIXED, PRE-REGISTERED multi-horizon candidate set
    (the anti-data-mining keystone) — a factor×horizon list the staging exploration iterates VERBATIM."""
    cfg = load_config()
    triad = cfg.triad
    assert triad["horizons"] == [1, 5, 10, 20, 60]        # aperture opened beyond the old default [20]
    assert triad["top_k"] == 50                            # raised from 20 for the ~5x wider field
    assert triad["screen"]["haircut_coef"] == 0.0025      # raised from the near-inert 0.001
    # the PRE-REGISTERED candidate set: exactly the 4 multi-horizon single-factor hypotheses, in order,
    # each carrying an economic rationale (never the full factor×horizon×decile cross-product).
    candidates = triad["candidates"]
    assert [(c["factor"], c["horizon"], c["decile"], c["direction"]) for c in candidates] == [
        ("vcp_contraction", 10, 10, "positive"),
        ("vcp_contraction", 60, 10, "positive"),
        ("rs_spy_3m", 60, 10, "positive"),
        ("leadership_score", 60, 10, "positive"),
    ]
    assert all(c.get("rationale") for c in candidates)    # every candidate is reasoned, not ad-hoc


def test_fdr_and_staging_default_when_omitted(tmp_path):
    """A config OMITTING the staging_ledger_path + fdr block still loads (additive, default-populated) — so
    a config / inline fixture predating iter-9 is unaffected and stays default-off (Bonferroni everywhere)."""
    cfg = load_config(_write(tmp_path, MINIMAL_VALID))
    assert cfg.evidence.fdr.enabled is False
    assert cfg.evidence.staging_ledger_path  # the built-in default path
    assert cfg.evidence.fdr.alpha == 0.05 and cfg.evidence.fdr.gamma_exponent == 1.6


def test_fdr_config_validation_rejects_bad_tunables():
    """Every LORD++ tunable is bounds-checked — a bad value is a loud error, NEVER a silent weakening."""
    from app.config import FdrCfg

    with pytest.raises(ValueError, match="alpha must be in"):
        FdrCfg(alpha=1.5)
    with pytest.raises(ValueError, match="w0_fraction must be in"):
        FdrCfg(w0_fraction=-0.1)
    with pytest.raises(ValueError, match="gamma_exponent must be > 1"):
        FdrCfg(gamma_exponent=1.0)
    with pytest.raises(ValueError, match="gamma_terms must be >= 1"):
        FdrCfg(gamma_terms=0)


def test_malformed_fdr_block_in_full_config_raises(tmp_path):
    """A malformed `evidence.fdr` block in a full config raises ConfigError at load (not a silent
    fall-through) — the honesty guard: the canonical bar can never be silently weakened by bad config."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["evidence"] = {
        "ledger_path": "runs/x/certified-claims.jsonl",
        "staging_ledger_path": "runs/x/staging-ledger.jsonl",
        "fdr": {"enabled": True, "alpha": 2.0},  # alpha out of (0,1)
    }
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# ==================================================================================================
# iter-30 — the pre-registration registry config (evidence.registry.{path,enforce}; J-18 / backlog B-901).
# ==================================================================================================
def test_real_config_activates_registry_enforcement_iter30():
    """The real config.yaml carries the iter-30 pre-registration registry, ACTIVATED (`enforce: true`)
    after the backfill was verified complete — the gate's teeth are on. The CODE default is still off
    (proven by `test_registry_defaults_when_omitted`)."""
    cfg = load_config()
    assert cfg.evidence.registry.path.endswith("pre-registrations.jsonl")
    assert cfg.evidence.registry.enforce is True


def test_registry_defaults_when_omitted(tmp_path):
    """A config OMITTING the `evidence.registry` block still loads (additive, default-populated) — so a
    config / inline test fixture predating iter-30 is unaffected and stays default-OFF (the gate's
    registry cross-check is skipped entirely, byte-identical to pre-iter-30 behavior)."""
    cfg = load_config(_write(tmp_path, MINIMAL_VALID))
    assert cfg.evidence.registry.enforce is False
    assert cfg.evidence.registry.path  # the built-in default path


def test_registry_config_omitted_inside_a_present_evidence_block(tmp_path):
    """A full config that DOES carry `evidence` but omits the nested `registry` sub-block (e.g. an
    iter-9-era fixture) still loads, default-populated and default-OFF — the same additive guarantee
    `fdr`/`staging_ledger_path` already have."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["evidence"] = {"ledger_path": "runs/x/certified-claims.jsonl"}
    cfg = load_config(_write(tmp_path, data))
    assert cfg.evidence.registry.enforce is False
    assert cfg.evidence.registry.path.endswith("pre-registrations.jsonl")
