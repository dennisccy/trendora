"""Config loader: loads + validates the real config.yaml; rejects invalid configs explicitly."""
from __future__ import annotations

import copy

import pytest
import yaml

from app.config import ConfigError, load_config

MINIMAL_VALID = {
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
    },
    "stock_sectors": {"AAA": "Technology", "BBB": "Technology"},
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
