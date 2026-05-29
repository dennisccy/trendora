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
