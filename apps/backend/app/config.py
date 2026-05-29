"""Typed config loader — the ONLY entry point to tunables (anti-goal: No magic numbers).

`load_config()` reads the repo-root `config.yaml`, validates the keys iter-1 consumes, and
returns typed pydantic settings. Missing/invalid required keys raise an explicit
`ConfigError` — never a silent default. Sections that are scaffolded-but-not-yet-wired
(scores / regime / decision_rules / walk_forward) are accepted via `extra="allow"`.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

# config.py -> app -> backend -> apps -> <repo root>
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config.yaml"


class ConfigError(Exception):
    """Raised when config.yaml is missing or fails validation. Explicit, never silent."""


class UniverseFilters(BaseModel):
    model_config = ConfigDict(extra="allow")
    min_market_cap: float
    min_dollar_vol: float
    min_price: float


class UniverseCfg(BaseModel):
    model_config = ConfigDict(extra="allow")
    symbols: list[str] = Field(min_length=1)
    filters: UniverseFilters


class ETFsCfg(BaseModel):
    model_config = ConfigDict(extra="allow")
    index: list[str] = Field(min_length=1)
    sector: dict[str, str] = Field(min_length=1)
    industry: list[str] = Field(min_length=1)
    volatility: list[str] = Field(default_factory=list)


class BucketsCfg(BaseModel):
    model_config = ConfigDict(extra="allow")
    A: int
    B: int
    C: int
    D: int

    @model_validator(mode="after")
    def _strictly_descending(self) -> "BucketsCfg":
        if not (self.A > self.B > self.C > self.D):
            raise ValueError("bucket edges must be strictly descending: A > B > C > D")
        return self


class LabelEdge(BaseModel):
    """One (min-score -> label) cutoff: a score `>= min` maps to `label`."""

    model_config = ConfigDict(extra="allow")
    min: float
    label: str


# Validation parameters (NOT scoring tunables — these live in config.py, never the engine).
_WEIGHT_SUM_TOLERANCE = 0.01
_SCORE_MAX = 100
_SCORE_MIN = 0
SECTOR_WEIGHT_KEYS = {"rs_spy_1m", "rs_spy_3m", "rs_spy_6m", "ma_stack", "dist_from_high", "vol_trend"}
REQUIRED_RS_WINDOWS = {"1m", "3m", "6m"}


def _validate_edges_descending_and_cover_zero(edges: list[LabelEdge], field: str) -> None:
    """Edges must be strictly descending by `min` and cover the full 0..100 score range
    (lowest `min` == 0, highest `min` <= 100). Anything else is a coverage gap -> reject."""
    mins = [e.min for e in edges]
    if len(set(mins)) != len(mins) or mins != sorted(mins, reverse=True):
        raise ValueError(f"{field} must be ordered by strictly descending `min`")
    if mins[-1] != _SCORE_MIN:
        raise ValueError(f"{field} must cover down to {_SCORE_MIN} (lowest `min` must be 0)")
    if mins[0] > _SCORE_MAX:
        raise ValueError(f"{field} top `min` must be <= {_SCORE_MAX}")


class IndicatorsCfg(BaseModel):
    """Indicator periods/windows (trading days). Every period the engine math uses is here."""

    model_config = ConfigDict(extra="allow")
    ma_periods: list[int] = Field(min_length=1)
    rs_windows: dict[str, int] = Field(min_length=1)
    atr_period: int
    high_window_52w: int
    vol_avg_period: int
    min_history_bars: int
    breadth_short_ma: int
    breadth_long_ma: int

    @model_validator(mode="after")
    def _validate(self) -> "IndicatorsCfg":
        if any(p <= 0 for p in self.ma_periods):
            raise ValueError("indicators.ma_periods must all be positive")
        missing = REQUIRED_RS_WINDOWS - set(self.rs_windows)
        if missing:
            raise ValueError(f"indicators.rs_windows missing required keys: {sorted(missing)}")
        if any(w <= 0 for w in self.rs_windows.values()):
            raise ValueError("indicators.rs_windows values must be positive")
        scalars = {
            "atr_period": self.atr_period,
            "high_window_52w": self.high_window_52w,
            "vol_avg_period": self.vol_avg_period,
            "min_history_bars": self.min_history_bars,
            "breadth_short_ma": self.breadth_short_ma,
            "breadth_long_ma": self.breadth_long_ma,
        }
        nonpositive = sorted(k for k, v in scalars.items() if v <= 0)
        if nonpositive:
            raise ValueError(f"indicators values must be positive: {nonpositive}")
        return self


class SectorsCfg(BaseModel):
    """Sector/industry leadership: component weights (cover every component, sum ~1.0) +
    trend-label cutoffs (Sector Score -> trend label)."""

    model_config = ConfigDict(extra="allow")
    weights: dict[str, float] = Field(min_length=1)
    trend_edges: list[LabelEdge] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate(self) -> "SectorsCfg":
        missing = SECTOR_WEIGHT_KEYS - set(self.weights)
        if missing:
            raise ValueError(f"sectors.weights missing components: {sorted(missing)}")
        total = sum(self.weights.values())
        if abs(total - 1.0) > _WEIGHT_SUM_TOLERANCE:
            raise ValueError(f"sectors.weights must sum to ~1.0, got {total}")
        _validate_edges_descending_and_cover_zero(self.trend_edges, "sectors.trend_edges")
        return self


class RegimeCfg(BaseModel):
    """Market Regime: component weights (sum ~1.0) + VIX gate threshold + score->label edges."""

    model_config = ConfigDict(extra="allow")
    vix_threshold: float
    weights: dict[str, float] = Field(min_length=1)
    labels: list[str] = Field(min_length=1)
    label_edges: list[LabelEdge] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate(self) -> "RegimeCfg":
        if self.vix_threshold <= 0:
            raise ValueError("regime.vix_threshold must be positive")
        total = sum(self.weights.values())
        if abs(total - 1.0) > _WEIGHT_SUM_TOLERANCE:
            raise ValueError(f"regime.weights must sum to ~1.0, got {total}")
        labelset = set(self.labels)
        unknown = [e.label for e in self.label_edges if e.label not in labelset]
        if unknown:
            raise ValueError(f"regime.label_edges reference unknown labels: {unknown}")
        _validate_edges_descending_and_cover_zero(self.label_edges, "regime.label_edges")
        return self


class DatabaseCfg(BaseModel):
    model_config = ConfigDict(extra="allow")
    url: str = Field(min_length=1)


class Config(BaseModel):
    """Validated view of config.yaml. Only the iter-1-consumed sections are typed/validated;
    scaffolded sections ride along via extra="allow" so they can be tuned without code edits."""

    model_config = ConfigDict(extra="allow")

    provider: Literal["seed", "stooq"]
    database: DatabaseCfg
    universe: UniverseCfg
    etfs: ETFsCfg
    themes: dict[str, list[str]] = Field(min_length=1)
    buckets: BucketsCfg
    indicators: IndicatorsCfg
    sectors: SectorsCfg
    regime: RegimeCfg

    @field_validator("themes")
    @classmethod
    def _each_theme_nonempty(cls, v: dict[str, list[str]]) -> dict[str, list[str]]:
        empty = [slug for slug, members in v.items() if not members]
        if empty:
            raise ValueError(f"themes with no members: {empty}")
        return v

    @model_validator(mode="after")
    def _theme_members_in_universe(self) -> "Config":
        universe = set(self.universe.symbols)
        missing = sorted({t for members in self.themes.values() for t in members if t not in universe})
        if missing:
            raise ValueError(f"theme members not present in universe.symbols: {missing}")
        return self


def load_config(path: Optional[str | Path] = None) -> Config:
    """Load + validate config.yaml. `path` overrides the default (repo-root config.yaml);
    the TRENDORA_CONFIG env var is honored when no explicit path is given (used by tests)."""
    if path is None:
        env = os.environ.get("TRENDORA_CONFIG")
        path = Path(env) if env else DEFAULT_CONFIG_PATH
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"config file not found: {path}")
    try:
        with path.open() as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:  # pragma: no cover - defensive
        raise ConfigError(f"config YAML parse error in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"config root must be a mapping, got {type(data).__name__}: {path}")
    try:
        return Config(**data)
    except ValidationError as exc:
        raise ConfigError(f"invalid config {path}:\n{exc}") from exc


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Process-wide cached config for the running app (not for tests that load alt configs)."""
    return load_config()
