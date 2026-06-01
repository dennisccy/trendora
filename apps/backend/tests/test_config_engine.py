"""iter-2 config validation: indicators / sectors / regime.label_edges.

The new sections are typed and VALIDATED at load time — a missing or invalid section raises an
explicit `ConfigError`, never a silent default (anti-goal: No magic numbers means the numbers
must actually be present and sane). The real config.yaml must load and expose the typed values.
"""
from __future__ import annotations

import copy

import pytest
import yaml

from app.config import ConfigError, load_config

# A complete, valid config (superset of the iter-1 minimal config + the iter-2 sections).
VALID = {
    "provider": "seed",
    "database": {"url": "sqlite:///:memory:"},
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
    "themes": {"t1": ["AAA", "BBB"]},
    "buckets": {"A": 90, "B": 80, "C": 70, "D": 60},
    "indicators": {
        "ma_periods": [20, 50, 150, 200],
        "rs_windows": {"1m": 21, "3m": 63, "6m": 126},
        "atr_period": 14,
        "high_window_52w": 252,
        "vol_avg_period": 50,
        "min_history_bars": 200,
        "breadth_short_ma": 50,
        "breadth_long_ma": 200,
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
            {"min": 65, "label": "Risk-on"},
            {"min": 55, "label": "Narrow leadership"},
            {"min": 45, "label": "Choppy"},
            {"min": 30, "label": "Defensive"},
            {"min": 0, "label": "Risk-off"},
        ],
    },
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
        "trend_edges": [
            {"min": 70, "label": "Strong uptrend"},
            {"min": 0, "label": "Downtrend"},
        ],
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
    "scanner": {"bootstrap_dates": ["2022-10-07", "2025-04-04"]},
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
    # iter-11 made `patterns` required (the VCP detector thresholds come from config, never code).
    "patterns": {
        "vcp": {
            "lookback_bars": 65, "min_contractions": 2, "max_contractions": 4,
            "min_contraction_pct": 3, "max_base_depth_pct": 35, "contraction_shrink_ratio": 0.8,
            "max_last_contraction_pct": 12, "pivot_proximity_pct": 8, "volume_dryup_ratio": 0.9,
            "volume_window": 10, "min_history_bars": 65,
        },
    },
    # iter-12 made `methodology` required (the config-backed Setup & Pattern catalog).
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


# --- the real config -----------------------------------------------------------------------
def test_real_config_exposes_typed_engine_sections():
    cfg = load_config()
    assert cfg.indicators.ma_periods == [20, 50, 150, 200]
    assert cfg.indicators.rs_windows["3m"] == 63
    assert cfg.indicators.min_history_bars == 200
    assert cfg.sectors.weights["rs_spy_3m"] == 0.25
    # regime.label_edges cover the full range and reference only the six labels
    edges = cfg.regime.label_edges
    assert min(e.min for e in edges) == 0
    assert all(e.label in cfg.regime.labels for e in edges)


def test_valid_config_loads(tmp_path):
    cfg = load_config(_write(tmp_path, VALID))
    assert cfg.sectors.trend_edges[-1].label == "Downtrend"


# --- indicators ----------------------------------------------------------------------------
def test_missing_indicators_section_raises(tmp_path):
    data = copy.deepcopy(VALID)
    del data["indicators"]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_indicators_missing_rs_window_raises(tmp_path):
    data = copy.deepcopy(VALID)
    del data["indicators"]["rs_windows"]["6m"]  # 6m required
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_indicators_nonpositive_period_raises(tmp_path):
    data = copy.deepcopy(VALID)
    data["indicators"]["atr_period"] = 0
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# --- sectors -------------------------------------------------------------------------------
def test_missing_sectors_section_raises(tmp_path):
    data = copy.deepcopy(VALID)
    del data["sectors"]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_sectors_weights_missing_component_raises(tmp_path):
    data = copy.deepcopy(VALID)
    del data["sectors"]["weights"]["vol_trend"]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_sectors_weights_not_summing_to_one_raises(tmp_path):
    data = copy.deepcopy(VALID)
    data["sectors"]["weights"]["rs_spy_1m"] = 0.99  # now sum is way over 1.0
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_sectors_trend_edges_not_covering_zero_raises(tmp_path):
    data = copy.deepcopy(VALID)
    data["sectors"]["trend_edges"] = [{"min": 50, "label": "Up"}]  # lowest min != 0
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# --- regime.label_edges --------------------------------------------------------------------
def test_missing_label_edges_raises(tmp_path):
    data = copy.deepcopy(VALID)
    del data["regime"]["label_edges"]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_label_edges_not_covering_zero_raises(tmp_path):
    data = copy.deepcopy(VALID)
    # drop the min:0 entry -> no longer covers down to 0
    data["regime"]["label_edges"] = [e for e in data["regime"]["label_edges"] if e["min"] != 0]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_label_edges_unknown_label_raises(tmp_path):
    data = copy.deepcopy(VALID)
    data["regime"]["label_edges"][0]["label"] = "Euphoria"  # not one of the six labels
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_label_edges_not_descending_raises(tmp_path):
    data = copy.deepcopy(VALID)
    data["regime"]["label_edges"] = [
        {"min": 30, "label": "Defensive"},
        {"min": 80, "label": "Strong risk-on"},
        {"min": 0, "label": "Risk-off"},
    ]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_regime_weights_not_summing_to_one_raises(tmp_path):
    data = copy.deepcopy(VALID)
    data["regime"]["weights"]["new_high_low"] = 0.99
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# --- iter-3: scores (leadership / entry_quality / risk) -----------------------------------
def test_real_config_exposes_typed_score_sections():
    cfg = load_config()
    assert abs(sum(cfg.scores.leadership.weights.values()) - 1.0) < 0.01
    assert abs(sum(cfg.scores.entry_quality.weights.values()) - 1.0) < 0.01
    assert abs(sum(cfg.scores.risk.weights.values()) - 1.0) < 0.01
    assert abs(sum(cfg.theme_scores.weights.values()) - 1.0) < 0.01
    # decision-rule cutoffs are present + typed
    assert cfg.decision_rules.actionable.leadership == 80
    assert cfg.decision_rules.extended.leadership == 85
    assert cfg.decision_rules.avoid_risk == 80
    # every universe symbol maps to a valid sector name
    assert set(cfg.stock_sectors) >= set(cfg.universe.symbols)
    assert set(cfg.stock_sectors.values()) <= set(cfg.etfs.sector.values())


def test_missing_scores_section_raises(tmp_path):
    data = copy.deepcopy(VALID)
    del data["scores"]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_scores_leadership_missing_component_raises(tmp_path):
    data = copy.deepcopy(VALID)
    del data["scores"]["leadership"]["weights"]["rs_sector"]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_scores_risk_weights_not_summing_to_one_raises(tmp_path):
    data = copy.deepcopy(VALID)
    data["scores"]["risk"]["weights"]["extension"] = 0.99  # now sum is way over 1.0
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# --- iter-3: theme_scores ------------------------------------------------------------------
def test_missing_theme_scores_section_raises(tmp_path):
    data = copy.deepcopy(VALID)
    del data["theme_scores"]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_theme_scores_missing_component_raises(tmp_path):
    data = copy.deepcopy(VALID)
    del data["theme_scores"]["weights"]["breadth"]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_theme_scores_trend_edges_not_covering_zero_raises(tmp_path):
    data = copy.deepcopy(VALID)
    data["theme_scores"]["trend_edges"] = [{"min": 50, "label": "Up"}]  # lowest min != 0
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# --- iter-3: decision_rules ----------------------------------------------------------------
def test_missing_decision_rules_section_raises(tmp_path):
    data = copy.deepcopy(VALID)
    del data["decision_rules"]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_decision_rules_missing_actionable_cutoff_raises(tmp_path):
    data = copy.deepcopy(VALID)
    del data["decision_rules"]["actionable"]["risk"]  # required cutoff key
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# --- iter-4: decision_rules.invalidation ---------------------------------------------------
def test_real_config_exposes_invalidation_ma_period():
    cfg = load_config()
    assert cfg.decision_rules.invalidation.ma_period == 50
    assert cfg.decision_rules.invalidation.ma_period in cfg.indicators.ma_periods


def test_missing_invalidation_block_raises(tmp_path):
    data = copy.deepcopy(VALID)
    del data["decision_rules"]["invalidation"]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_invalidation_ma_period_outside_ma_periods_raises(tmp_path):
    data = copy.deepcopy(VALID)
    data["decision_rules"]["invalidation"]["ma_period"] = 7  # not one of indicators.ma_periods
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# --- iter-3: stock_sectors reference data --------------------------------------------------
def test_stock_sectors_missing_symbol_raises(tmp_path):
    data = copy.deepcopy(VALID)
    del data["stock_sectors"]["BBB"]  # universe symbol no longer covered
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_stock_sectors_unknown_sector_name_raises(tmp_path):
    data = copy.deepcopy(VALID)
    data["stock_sectors"]["AAA"] = "Bananas"  # not one of the etfs.sector names
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# --- iter-5: scanner bootstrap dates -------------------------------------------------------
def test_real_config_exposes_scanner_bootstrap_dates():
    from datetime import date

    cfg = load_config()
    dates = cfg.scanner.bootstrap_dates
    assert len(dates) >= 1
    # ISO strings in config.yaml are coerced to datetime.date (no date literal in calc code)
    assert all(isinstance(d, date) for d in dates)
    assert date(2025, 4, 4) in dates


def test_missing_scanner_section_raises(tmp_path):
    data = copy.deepcopy(VALID)
    del data["scanner"]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_scanner_empty_bootstrap_dates_raises(tmp_path):
    data = copy.deepcopy(VALID)
    data["scanner"]["bootstrap_dates"] = []  # must list at least one as-of date
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# --- iter-11: patterns.vcp typed validation ------------------------------------------------
def test_real_config_exposes_typed_vcp_patterns():
    """The real config.yaml exposes a typed `patterns.vcp` block — every detector threshold present
    (anti-goal: No magic numbers — the values must actually be in config, sane and positive)."""
    cfg = load_config()
    vcp = cfg.patterns.vcp
    assert vcp.lookback_bars > 0 and vcp.min_history_bars > 0 and vcp.volume_window > 0
    assert 0 < vcp.min_contractions <= vcp.max_contractions
    assert 0 < vcp.contraction_shrink_ratio <= 1
    for pct in (vcp.min_contraction_pct, vcp.max_base_depth_pct, vcp.max_last_contraction_pct,
                vcp.pivot_proximity_pct, vcp.volume_dryup_ratio):
        assert pct > 0


def test_missing_patterns_section_raises(tmp_path):
    data = copy.deepcopy(VALID)
    del data["patterns"]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_vcp_nonpositive_window_raises(tmp_path):
    data = copy.deepcopy(VALID)
    data["patterns"]["vcp"]["lookback_bars"] = 0  # a window/count must be positive
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_vcp_shrink_ratio_above_one_raises(tmp_path):
    data = copy.deepcopy(VALID)
    data["patterns"]["vcp"]["contraction_shrink_ratio"] = 1.5  # must be in (0, 1]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_vcp_shrink_ratio_zero_raises(tmp_path):
    data = copy.deepcopy(VALID)
    data["patterns"]["vcp"]["contraction_shrink_ratio"] = 0  # must be > 0 (in (0, 1])
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_vcp_nonpositive_pct_raises(tmp_path):
    data = copy.deepcopy(VALID)
    data["patterns"]["vcp"]["max_base_depth_pct"] = 0  # every *_pct must be positive
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_vcp_min_contractions_above_max_raises(tmp_path):
    data = copy.deepcopy(VALID)
    data["patterns"]["vcp"]["min_contractions"] = 5
    data["patterns"]["vcp"]["max_contractions"] = 4  # min must be <= max
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# --- J-19: walk_forward.attribution typed validation (no magic numbers) --------------------
def test_real_config_exposes_typed_attribution():
    """The real config.yaml exposes a typed `walk_forward.attribution` block — the rank-band edges and
    the contributor list size are present (anti-goal: No magic numbers — they live in config, not code)."""
    attr = load_config().walk_forward.attribution
    assert attr.top_contributors_k > 0
    assert len(attr.rank_bands) >= 1
    # bands are ascending, non-overlapping, only the last open
    assert attr.rank_bands[0].min == 1
    assert attr.rank_bands[-1].max is None
    for lo, hi in zip(attr.rank_bands, attr.rank_bands[1:]):
        assert lo.max is not None and hi.min > lo.max


def test_missing_attribution_section_raises(tmp_path):
    data = copy.deepcopy(VALID)
    del data["walk_forward"]["attribution"]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_attribution_nonpositive_top_contributors_k_raises(tmp_path):
    data = copy.deepcopy(VALID)
    data["walk_forward"]["attribution"]["top_contributors_k"] = 0  # must be positive
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_attribution_overlapping_rank_bands_raises(tmp_path):
    data = copy.deepcopy(VALID)
    data["walk_forward"]["attribution"]["rank_bands"] = [
        {"label": "1–10", "min": 1, "max": 10},
        {"label": "5–20", "min": 5, "max": 20},  # overlaps the first band
    ]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_attribution_open_band_not_last_raises(tmp_path):
    data = copy.deepcopy(VALID)
    data["walk_forward"]["attribution"]["rank_bands"] = [
        {"label": "1+", "min": 1, "max": None},   # only the LAST band may be open
        {"label": "11–50", "min": 11, "max": 50},
    ]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))
