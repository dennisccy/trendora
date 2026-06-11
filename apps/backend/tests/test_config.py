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
        },
    },
    "universe": {
        "symbols": ["AAA", "BBB"],
        "filters": {"min_market_cap": 1, "min_dollar_vol": 1, "min_price": 1},
    },
    "etfs": {
        "index": ["SPY"],
        "sector": {"XLK": "Technology"},
        "industry": ["SMH"],
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
    # iter-5 made `scanner` required (bootstrap dates come from config, never code).
    "scanner": {"bootstrap_dates": ["2022-10-07", "2025-04-04"]},
    # iter-28 made `startup` required (fast-ready boot + warm-up tunables come from config, never code).
    "startup": {
        "readiness_budget_seconds": 30.0,
        "warmup_batch_size": 1,
        "health_poll_interval_seconds": 2.0,
        "health_poll_idle_interval_seconds": 30.0,
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
