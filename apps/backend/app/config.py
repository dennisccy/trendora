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

# iter-3 per-stock score component key sets — the scoring engine blends exactly these named
# components per score, so config.scores.* MUST cover each set (completeness) and sum ~1.0.
LEADERSHIP_WEIGHT_KEYS = {
    "rs_spy_1m", "rs_spy_3m", "rs_sector", "rs_theme", "ma_stack", "high_proximity", "up_down_vol",
}
ENTRY_QUALITY_WEIGHT_KEYS = {
    "dist_rising_20", "contraction", "support_nearby", "structure", "reward_risk",
}
RISK_WEIGHT_KEYS = {
    "extension", "atr_pct", "liquidity", "regime", "sector_strength", "gap_climax",
    "below_ma", "rs_deterioration",
}
THEME_SCORE_WEIGHT_KEYS = {"rs_spy_1m", "rs_spy_3m", "breadth", "ma_participation"}


def _require_complete_weights(weights: dict[str, float], expected: set[str], field: str) -> None:
    """A score's weights must cover its expected component set and sum ~1.0 (anti-goal: every
    weight present in config, none invented in code)."""
    missing = expected - set(weights)
    if missing:
        raise ValueError(f"{field} missing components: {sorted(missing)}")
    total = sum(weights.values())
    if abs(total - 1.0) > _WEIGHT_SUM_TOLERANCE:
        raise ValueError(f"{field} must sum to ~1.0, got {total}")


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


class WeightBlock(BaseModel):
    """One score's component weights (e.g. `scores.leadership`)."""

    model_config = ConfigDict(extra="allow")
    weights: dict[str, float] = Field(min_length=1)


class ScoresCfg(BaseModel):
    """Per-stock score weights consumed by `app.engine.scoring` (iter-3). Each of the three
    independent scores blends a complete, config-defined set of named components summing ~1.0."""

    model_config = ConfigDict(extra="allow")
    leadership: WeightBlock
    entry_quality: WeightBlock
    risk: WeightBlock

    @model_validator(mode="after")
    def _validate(self) -> "ScoresCfg":
        _require_complete_weights(self.leadership.weights, LEADERSHIP_WEIGHT_KEYS, "scores.leadership.weights")
        _require_complete_weights(self.entry_quality.weights, ENTRY_QUALITY_WEIGHT_KEYS, "scores.entry_quality.weights")
        _require_complete_weights(self.risk.weights, RISK_WEIGHT_KEYS, "scores.risk.weights")
        return self


class ThemeScoresCfg(BaseModel):
    """Theme leadership: component weights (cover every component, sum ~1.0) + trend-label
    cutoffs (Theme Score -> trend label). Consumed by `app.engine.themes` (iter-3)."""

    model_config = ConfigDict(extra="allow")
    weights: dict[str, float] = Field(min_length=1)
    trend_edges: list[LabelEdge] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate(self) -> "ThemeScoresCfg":
        _require_complete_weights(self.weights, THEME_SCORE_WEIGHT_KEYS, "theme_scores.weights")
        _validate_edges_descending_and_cover_zero(self.trend_edges, "theme_scores.trend_edges")
        return self


class ActionableCutoffs(BaseModel):
    model_config = ConfigDict(extra="allow")
    leadership: float
    entry: float
    risk: float


class ExtendedCutoffs(BaseModel):
    model_config = ConfigDict(extra="allow")
    leadership: float
    entry: float


class WatchCutoffs(BaseModel):
    model_config = ConfigDict(extra="allow")
    leadership: float


class InvalidationCfg(BaseModel):
    """Which moving average defines the per-stock invalidation level (iter-4). `ma_period` MUST
    be one of `indicators.ma_periods` (validated on `Config`) so the invalidation MA is the SAME
    canonical `sma` that draws the chart overlay and feeds scoring — never a second MA basis."""

    model_config = ConfigDict(extra="allow")
    ma_period: int


class DecisionRulesCfg(BaseModel):
    """Setup-classification cutoffs consumed by `app.engine.setups.classify_setup` (iter-3) plus
    the invalidation MA basis consumed by `app.engine.scoring.score_stocks` (iter-4). The required
    keys must be present; pydantic raises if any is missing. Additional forward-looking keys (e.g.
    `theme_floor`) ride along via extra='allow'."""

    model_config = ConfigDict(extra="allow")
    actionable: ActionableCutoffs
    extended: ExtendedCutoffs
    watch: WatchCutoffs
    avoid_risk: float
    invalidation: InvalidationCfg


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
    scores: ScoresCfg
    theme_scores: ThemeScoresCfg
    decision_rules: DecisionRulesCfg
    stock_sectors: dict[str, str] = Field(min_length=1)

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

    @model_validator(mode="after")
    def _stock_sectors_cover_universe(self) -> "Config":
        """Every universe symbol must map to a sector, and each mapped sector name must be one
        of the etfs.sector names (so scoring can resolve a stock's sector ETF). Reference data,
        validated like the universe/theme lists — never a silent default."""
        universe = set(self.universe.symbols)
        missing = sorted(universe - set(self.stock_sectors))
        if missing:
            raise ValueError(f"stock_sectors missing universe symbols: {missing}")
        valid = set(self.etfs.sector.values())
        bad = sorted(f"{t}={s}" for t, s in self.stock_sectors.items() if s not in valid)
        if bad:
            raise ValueError(f"stock_sectors values must be one of {sorted(valid)}; invalid: {bad}")
        return self

    @model_validator(mode="after")
    def _invalidation_ma_period_is_an_indicator_period(self) -> "Config":
        """The invalidation MA basis must be one of the configured `indicators.ma_periods`, so the
        invalidation level reuses an already-charted canonical MA (single source — no second MA)."""
        period = self.decision_rules.invalidation.ma_period
        if period not in self.indicators.ma_periods:
            raise ValueError(
                f"decision_rules.invalidation.ma_period ({period}) must be one of "
                f"indicators.ma_periods ({self.indicators.ma_periods})"
            )
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
