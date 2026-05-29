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
