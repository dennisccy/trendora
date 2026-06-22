"""Typed config loader — the ONLY entry point to tunables (anti-goal: No magic numbers).

`load_config()` reads the repo-root `config.yaml`, validates the keys the app consumes, and
returns typed pydantic settings. Missing/invalid required keys raise an explicit
`ConfigError` — never a silent default. As of iter-6 every section the engines consume is typed
and validated, including `walk_forward` (promoted from the iter-1 scaffolded passthrough to the
typed `WalkForwardCfg`); any remaining forward-looking keys still ride along via `extra="allow"`.
"""
from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

# config.py -> app -> backend -> apps -> <repo root>
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config.yaml"
# The committed canonical universe-membership artifact (written by the offline screen / the J-35 expand
# job). When present it is the SINGLE source of `universe.symbols` — see `_merge_committed_universe`.
BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_UNIVERSE_JSON = BACKEND_DIR / "data" / "seed" / "universe.json"


class ConfigError(Exception):
    """Raised when config.yaml is missing or fails validation. Explicit, never silent."""


class UniverseFilters(BaseModel):
    """The config-recorded universe screen thresholds (J-22 / J-35). `min_market_cap` / `min_dollar_vol`
    / `min_price` are the three-threshold cutoffs the pure `screen_reasons` predicate reads (the single
    source of the membership rule). `adv_window_days` is the trailing window (trading days) the
    average-daily-dollar-volume liquidity measure is computed over — OPTIONAL with the documented default
    so it is tunable from config (No magic numbers) without becoming a new REQUIRED key in every fixture.
    Validated positive on the parent `UniverseCfg`."""

    model_config = ConfigDict(extra="allow")
    min_market_cap: float
    min_dollar_vol: float
    min_price: float
    adv_window_days: int = 63  # ~3 trading months — the ADV liquidity window (the offline screen default)


class UniverseCfg(BaseModel):
    model_config = ConfigDict(extra="allow")
    symbols: list[str] = Field(min_length=1)
    filters: UniverseFilters

    @model_validator(mode="after")
    def _validate(self) -> "UniverseCfg":
        if self.filters.adv_window_days <= 0:
            raise ValueError(
                f"universe.filters.adv_window_days must be positive, got {self.filters.adv_window_days}"
            )
        return self


class IndustryETFEntry(BaseModel):
    """One industry-group ETF's display reference data (J-58): a REQUIRED plain-language `name`
    (a missing/blank name is a loud `ConfigError`, never a silent default — the leaderboard would
    otherwise fall back to a bare ticker) and an optional one-line `description`. CONFIG-DEFINED —
    no name or description literal lives in code. Resolved once by `sectors:score_sectors` and
    stored on each `SectorScoreRow`; served verbatim by `GET /api/sectors`."""

    model_config = ConfigDict(extra="allow")
    name: str = Field(min_length=1)
    description: Optional[str] = None


class ETFsCfg(BaseModel):
    model_config = ConfigDict(extra="allow")
    index: list[str] = Field(min_length=1)
    sector: dict[str, str] = Field(min_length=1)
    # J-58: `industry` is now a catalog (ticker -> {name, description}) instead of a bare ticker list,
    # so each industry ETF reads as a named/described row on the Sectors leaderboard. Iterate `.keys()`
    # for the ticker set; read `.items()` for (ticker, entry). A malformed entry (e.g. missing `name`)
    # raises a loud ConfigError via `IndustryETFEntry` — never a silent default.
    industry: dict[str, IndustryETFEntry] = Field(min_length=1)
    volatility: list[str] = Field(default_factory=list)


class IndexChartSymbol(BaseModel):
    """One config-listed major-index ETF on the J-44 dashboard chart: its ticker `symbol` and the
    `name` shown in the legend / tooltip. The symbol list + display names are config, never a hardcoded
    frontend list (anti-goal: No magic numbers). A configured symbol with no stored bars (e.g. DIA
    before its one-shot fetch) is honestly omitted server-side — listing it here is safe."""

    model_config = ConfigDict(extra="allow")
    symbol: str
    name: str


class IndexRangePreset(BaseModel):
    """One range-preset option for the major-index chart: `key` is the stable API/URL value, `label`
    the displayed text, `days` the trailing-calendar-day window (`None` ⇒ all available history). The
    presets come from config so the frontend switcher never hardcodes a range (anti-goal: No magic
    numbers). `days` (when set) MUST be `>= 1`."""

    model_config = ConfigDict(extra="allow")
    key: str
    label: str
    days: Optional[int] = None

    @model_validator(mode="after")
    def _days_positive(self) -> "IndexRangePreset":
        if self.days is not None and self.days < 1:
            raise ValueError(f"index_chart range preset {self.key!r} days must be >= 1 (got {self.days})")
        return self


class IndexChartCfg(BaseModel):
    """Config for the J-44 "Major indexes & regime" dashboard chart (Capability 37): the index ETF
    symbols + display names and the range presets, all config-driven (anti-goal: No magic numbers — no
    symbol list / display name / range window literal in the engine or the frontend). `default_range`
    MUST be one of the `range_presets` keys; preset keys + symbol tickers MUST be unique. A configured
    symbol with no stored bars (e.g. DIA before its one-shot fetch) is honestly OMITTED at serve time
    (never fabricated) — this list is the chart's presentation universe and is intentionally independent
    of `etfs.index`/the scoring inputs, so listing DIA here never touches regime/scoring computation."""

    model_config = ConfigDict(extra="allow")
    symbols: list[IndexChartSymbol] = Field(min_length=1)
    range_presets: list[IndexRangePreset] = Field(min_length=1)
    default_range: str

    @model_validator(mode="after")
    def _validate(self) -> "IndexChartCfg":
        keys = [preset.key for preset in self.range_presets]
        dupes = sorted({k for k in keys if keys.count(k) > 1})
        if dupes:
            raise ValueError(f"index_chart.range_presets keys must be unique; duplicates: {dupes}")
        if self.default_range not in keys:
            raise ValueError(
                f"index_chart.default_range ({self.default_range!r}) must be one of the preset keys {keys}"
            )
        symbols = [s.symbol for s in self.symbols]
        sym_dupes = sorted({s for s in symbols if symbols.count(s) > 1})
        if sym_dupes:
            raise ValueError(f"index_chart.symbols must be unique; duplicates: {sym_dupes}")
        return self


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

# iter-10 Factor Lab (J-25). A factor's stored `source` is EITHER one of these typed `ScannerResult`
# columns OR a `<block>.components.<name>.raw` dotted path read from `record_json`, where `<block>` is
# one of these score blocks and `<name>` is a component in `config.scores.<block>.weights`. The three
# score columns are never NULL; the iter-13 volatility-family columns (`hv`/`vcp_contraction`/
# `downside_vol`, J-30) MAY be NULL on short history — a NULL observation is honestly EXCLUDED by the
# read-only lab, never bucketed/fabricated. The volatility values are STORED for lab consumption only
# and enter NO weighted score (they are deliberately absent from every `scores.<block>.weights`).
FACTOR_TYPED_COLUMNS = {
    "leadership_score", "entry_quality_score", "risk_score",
    "hv", "vcp_contraction", "downside_vol",
}
FACTOR_SOURCE_BLOCKS = {"leadership", "entry_quality", "risk"}
_FACTOR_SOURCE_PARTS = 4  # the dotted shape "<block>.components.<name>.raw"


def parse_factor_source(source: str) -> dict:
    """Parse a Factor-Lab `source` string into its structured READ form (anti-goal: No magic numbers —
    the factor catalog + its sources live in config, never code). Returns either
    ``{"kind": "column", "column": <typed ScannerResult column>}`` or
    ``{"kind": "component", "block": <score block>, "name": <component name>}``. Raises ``ValueError``
    on a string that is neither a known typed column nor a `<block>.components.<name>.raw` path — the
    boot validator turns that into a loud ``ConfigError`` (never a silent default). Used at BOTH boot
    (validation, cross-checked against `scores.<block>.weights`) and serve time (the read-only
    `app.engine.research` extractor) so there is exactly one source-shape definition."""
    if source in FACTOR_TYPED_COLUMNS:
        return {"kind": "column", "column": source}
    parts = source.split(".")
    if (
        len(parts) == _FACTOR_SOURCE_PARTS
        and parts[0] in FACTOR_SOURCE_BLOCKS
        and parts[1] == "components"
        and parts[3] == "raw"
    ):
        return {"kind": "component", "block": parts[0], "name": parts[2]}
    raise ValueError(
        f"factor source {source!r} must be a typed score column {sorted(FACTOR_TYPED_COLUMNS)} "
        "or a '<block>.components.<name>.raw' path"
    )


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
    # iter-13 (J-30) volatility-factor-family windows — consumed by the new indicator math
    # (hist_volatility / vol_contraction / downside_vol). Typed + validated positive like every other
    # indicator period so a missing/non-positive window fails the boot loudly (anti-goal: No magic numbers).
    hv_window: int
    semivol_window: int
    vol_contraction_recent: int
    vol_contraction_prior: int

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
            "hv_window": self.hv_window,
            "semivol_window": self.semivol_window,
            "vol_contraction_recent": self.vol_contraction_recent,
            "vol_contraction_prior": self.vol_contraction_prior,
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


class ScannerCfg(BaseModel):
    """Scanner snapshot bootstrap (iter-5). `bootstrap_dates` are the historical as-of dates the
    scanner persists an immutable snapshot for (the latest data date is added programmatically in
    code, not listed here). ISO strings in config.yaml are coerced to `datetime.date` — there is no
    date literal in calc code (anti-goal: No magic numbers); the scanner reads these."""

    model_config = ConfigDict(extra="allow")
    bootstrap_dates: list[date] = Field(min_length=1)


class StartupCfg(BaseModel):
    """Fast-ready boot + background warm-up tunables (iter-28, J-40/J-41). EVERY startup/readiness/poll
    number the boot path, the readiness module, and the frontend badge derive from lives here
    (anti-goal: No magic numbers — NO budget/poll/backoff literal in `main.py`, `app.engine.readiness`,
    `app.engine.warmup`, or the frontend health badge; mirrors how `import_chunking` lives in config).

      - `readiness_budget_seconds` — the soft budget for the minimal synchronous boot work (config/db/
        seed + the SINGLE latest-snapshot compute) before the server begins serving. Surfaced to
        operators / the readiness payload; the boot does not abort on overrun (it logs), it bounds
        what "fast-ready" means.
      - `warmup_batch_size` — how many cadence as-of dates the background warm-up persists per progress
        tick (the warm-up loop's batch granularity). MUST be `>= 1`.
      - `health_poll_interval_seconds` — the cadence the frontend readiness badge polls the readiness
        endpoint at while warming (fast enough that the flip to Ready shows within a poll of warm-up
        completion — NOT a slow 30 s cycle). MUST be `> 0`.
      - `health_poll_idle_interval_seconds` — the slower cadence the badge MAY back off to once Ready
        (a healthy backend needs no fast poll). MUST be `>= health_poll_interval_seconds`.

    Boot-validated: the budget + both poll intervals MUST be `> 0`, the batch size `>= 1`, and the idle
    interval `>= the active interval`. An invalid block raises `ConfigError`, never a silent default."""

    model_config = ConfigDict(extra="allow")
    readiness_budget_seconds: float
    warmup_batch_size: int
    health_poll_interval_seconds: float
    health_poll_idle_interval_seconds: float

    @model_validator(mode="after")
    def _validate(self) -> "StartupCfg":
        positive = {
            "readiness_budget_seconds": self.readiness_budget_seconds,
            "health_poll_interval_seconds": self.health_poll_interval_seconds,
            "health_poll_idle_interval_seconds": self.health_poll_idle_interval_seconds,
        }
        nonpositive = sorted(k for k, v in positive.items() if v <= 0)
        if nonpositive:
            raise ValueError(f"startup values must be positive: {nonpositive}")
        if self.warmup_batch_size < 1:
            raise ValueError("startup.warmup_batch_size must be >= 1")
        if self.health_poll_idle_interval_seconds < self.health_poll_interval_seconds:
            raise ValueError(
                "startup.health_poll_idle_interval_seconds must be >= health_poll_interval_seconds"
            )
        return self


class ServerOpsCfg(BaseModel):
    """iter-42 (J-100) — bounded-resource SERVER ops guards. The SINGLE source of the uvicorn concurrency
    cap, the keep-alive + graceful-shutdown timeouts, and the per-process virtual-memory cap the start
    script (`scripts/start-backend.sh`) enforces (anti-goal: No magic numbers — NO concurrency/timeout/
    memory literal lives in the script; it reads every value from here via the venv python). These keep the
    backend responsive + memory-bounded under concurrent dashboard / goal-mode UI-test load:

      - `limit_concurrency`        — uvicorn `--limit-concurrency`: the max simultaneous connections before
                                     a 503, so a heavy `/api/data` burst never starves `/health` + light
                                     reads (paired with the single-flight coverage cache, N parallel probes
                                     cost ~one heavy compute, not N connection-holding resolves).
      - `timeout_keep_alive_seconds` — uvicorn `--timeout-keep-alive`: the idle keep-alive timeout; a heavy
                                     warm `/api/data` read is ~10 s, so this is bounded generously above it.
      - `graceful_timeout_seconds` — uvicorn `--timeout-graceful-shutdown`: bounds how long a heavy in-flight
                                     request may delay shutdown.
      - `memory_cap_mb`            — `ulimit -v` virtual-memory cap (MB) for the backend process: clears the
                                     one-copy ~1.3M-row bar prefill + headroom, so a pathological N-copy
                                     spike is OOM-killed as ONE process rather than swap-thrashing the VM.

    Default-populated (a config predating it — and the inline test fixtures — still loads unchanged). Every
    value MUST be positive; an invalid block raises `ValueError` at load, never a silent default."""

    model_config = ConfigDict(extra="allow")
    limit_concurrency: int = 64
    timeout_keep_alive_seconds: int = 65
    graceful_timeout_seconds: int = 120
    memory_cap_mb: int = 6144

    @model_validator(mode="after")
    def _validate(self) -> "ServerOpsCfg":
        bad = sorted(
            k for k, v in {
                "limit_concurrency": self.limit_concurrency,
                "timeout_keep_alive_seconds": self.timeout_keep_alive_seconds,
                "graceful_timeout_seconds": self.graceful_timeout_seconds,
                "memory_cap_mb": self.memory_cap_mb,
            }.items() if v <= 0
        )
        if bad:
            raise ValueError(f"server ops values must be positive: {bad}")
        return self


class ControlGroupCfg(BaseModel):
    """Walk-forward control-group parameters (iter-6). The random same-sector cohort is drawn with a
    deterministic RNG re-seeded from `seed` on every computation (reproducible across calls/restarts
    — never bare `random`); `top_n` is the top-ranked cohort cutoff; `peers_per_sector` is the number
    of random peers drawn per sector. All from config (anti-goal: No magic numbers)."""

    model_config = ConfigDict(extra="allow")
    seed: int
    top_n: int
    peers_per_sector: int

    @model_validator(mode="after")
    def _validate(self) -> "ControlGroupCfg":
        if self.top_n <= 0:
            raise ValueError("walk_forward.control_group.top_n must be positive")
        if self.peers_per_sector <= 0:
            raise ValueError("walk_forward.control_group.peers_per_sector must be positive")
        return self


class RankBand(BaseModel):
    """One rank band for return attribution (J-19): a STORED rank in [`min`, `max`] maps to `label`.
    `max: null` marks the open top band (no upper bound). Every edge comes from config — no band edge
    literal lives in calc code (anti-goal: No magic numbers)."""

    model_config = ConfigDict(extra="allow")
    label: str
    min: int
    max: Optional[int] = None


class AttributionCfg(BaseModel):
    """Return-attribution parameters (J-19 CONSUMED by `forward_testing._attribution_slices`).
    `rank_bands` is the ORDERED list of display bands a stored rank is mapped to (1–10 / 11–50 / 51+,
    the last open via `max: null`); `top_contributors_k` is how many per-stock contributors / detractors
    to list. Both come from config so no band edge or list size literal lives in calc code (anti-goal:
    No magic numbers). Validated like `ControlGroupCfg`: each edge positive, `min <= max`, bands strictly
    ascending and non-overlapping, only the LAST band open, and `top_contributors_k > 0`."""

    model_config = ConfigDict(extra="allow")
    rank_bands: list[RankBand] = Field(min_length=1)
    top_contributors_k: int

    @model_validator(mode="after")
    def _validate(self) -> "AttributionCfg":
        if self.top_contributors_k <= 0:
            raise ValueError("walk_forward.attribution.top_contributors_k must be positive")
        prev_max: Optional[int] = 0
        for index, band in enumerate(self.rank_bands):
            is_last = index == len(self.rank_bands) - 1
            if band.min <= 0:
                raise ValueError(f"walk_forward.attribution rank_band {band.label!r} min must be positive")
            if band.max is None and not is_last:
                raise ValueError("only the last walk_forward.attribution rank_band may be open (max: null)")
            if band.max is not None and band.max < band.min:
                raise ValueError(f"walk_forward.attribution rank_band {band.label!r} max must be >= min")
            if prev_max is None or band.min <= prev_max:
                raise ValueError("walk_forward.attribution rank_bands must be ascending and non-overlapping")
            prev_max = band.max  # None after the open last band
        return self


class WalkForwardCfg(BaseModel):
    """Walk-forward forward-testing parameters (iter-6 CONSUMED). The forward-testing engine reads
    EVERY tunable here — replay window (`history_years`), as-of cadence (`asof_cadence`), the forward
    `horizons` (trading days), the `min_sample` honesty threshold, the default served `horizon`, the
    `control_group` block, and the `attribution` block (J-19) — so no walk-forward literal lives in calc
    code (anti-goal: No magic numbers). Promoted from the iter-1 scaffolded passthrough to a typed
    section."""

    model_config = ConfigDict(extra="allow")
    history_years: int
    asof_cadence: Literal["daily", "weekly", "monthly", "quarterly"]
    horizons: list[int] = Field(min_length=1)
    min_sample: int
    default_horizon: int
    control_group: ControlGroupCfg
    attribution: AttributionCfg

    @model_validator(mode="after")
    def _validate(self) -> "WalkForwardCfg":
        if self.history_years <= 0:
            raise ValueError("walk_forward.history_years must be positive")
        if any(h <= 0 for h in self.horizons):
            raise ValueError("walk_forward.horizons must all be positive")
        if self.min_sample <= 0:
            raise ValueError("walk_forward.min_sample must be positive")
        if self.default_horizon not in self.horizons:
            raise ValueError(
                f"walk_forward.default_horizon ({self.default_horizon}) must be one of "
                f"walk_forward.horizons ({self.horizons})"
            )
        return self


class VcpCfg(BaseModel):
    """VCP (Volatility Contraction Pattern) detector thresholds (iter-11 CONSUMED). EVERY tunable the
    `app.engine.patterns.detect_vcp` detector reads lives here — windows, contraction counts, depth
    caps, the shrink ratio, the pivot-proximity band, and the volume-dry-up ratio — so NO detection
    literal lives in calc code (anti-goal: No magic numbers). Validated like `WalkForwardCfg`: every
    window/count is positive, the shrink ratio is in (0, 1], and every percentage is positive — an
    invalid block raises `ConfigError`, never a silent default."""

    model_config = ConfigDict(extra="allow")
    lookback_bars: int
    min_contractions: int
    max_contractions: int
    min_contraction_pct: float
    max_base_depth_pct: float
    contraction_shrink_ratio: float
    max_last_contraction_pct: float
    pivot_proximity_pct: float
    volume_dryup_ratio: float
    volume_window: int
    min_history_bars: int

    @model_validator(mode="after")
    def _validate(self) -> "VcpCfg":
        windows = {
            "lookback_bars": self.lookback_bars,
            "min_contractions": self.min_contractions,
            "max_contractions": self.max_contractions,
            "volume_window": self.volume_window,
            "min_history_bars": self.min_history_bars,
        }
        nonpositive = sorted(k for k, v in windows.items() if v <= 0)
        if nonpositive:
            raise ValueError(f"patterns.vcp windows/counts must be positive: {nonpositive}")
        if self.min_contractions > self.max_contractions:
            raise ValueError(
                f"patterns.vcp.min_contractions ({self.min_contractions}) must be <= "
                f"max_contractions ({self.max_contractions})"
            )
        if not (0 < self.contraction_shrink_ratio <= 1):
            raise ValueError(
                f"patterns.vcp.contraction_shrink_ratio must be in (0, 1], got {self.contraction_shrink_ratio}"
            )
        pcts = {
            "min_contraction_pct": self.min_contraction_pct,
            "max_base_depth_pct": self.max_base_depth_pct,
            "max_last_contraction_pct": self.max_last_contraction_pct,
            "pivot_proximity_pct": self.pivot_proximity_pct,
            "volume_dryup_ratio": self.volume_dryup_ratio,
        }
        bad_pct = sorted(k for k, v in pcts.items() if v <= 0)
        if bad_pct:
            raise ValueError(f"patterns.vcp percentages/ratios must be positive: {bad_pct}")
        return self


class PullbackToRisingDmaCfg(BaseModel):
    """Pullback-to-rising-DMA detector thresholds (iter-9 CONSUMED). EVERY tunable the
    `app.engine.patterns.detect_pullback_to_rising_dma` detector reads lives here — the MA basis, the
    rising-trend lookback + minimum slope, the pulled-back-to-the-DMA proximity band (how far above and
    how far below the DMA still counts), the maximum pullback depth from the recent high, the minimum
    history, and the volume window — so NO detection literal lives in calc code (anti-goal: No magic
    numbers). `ma_period` is cross-checked against `indicators.ma_periods` on the top-level `Config`
    (a sub-model cannot see `indicators`), exactly like the VCP invalidation MA. Validated like
    `VcpCfg`: every window/count positive, history long enough to compute the slope, the slope/dist
    percents positive, and `max_undercut_pct` non-negative (it MAY be 0) — an invalid block raises
    `ConfigError`, never a silent default."""

    model_config = ConfigDict(extra="allow")
    ma_period: int
    min_history_bars: int
    trend_lookback_bars: int
    min_dma_slope_pct: float
    max_dist_above_dma_pct: float
    max_undercut_pct: float
    max_pullback_depth_pct: float
    volume_window: int

    @model_validator(mode="after")
    def _validate(self) -> "PullbackToRisingDmaCfg":
        windows = {
            "ma_period": self.ma_period,
            "min_history_bars": self.min_history_bars,
            "trend_lookback_bars": self.trend_lookback_bars,
            "volume_window": self.volume_window,
        }
        nonpositive = sorted(k for k, v in windows.items() if v <= 0)
        if nonpositive:
            raise ValueError(
                f"patterns.pullback_to_rising_dma windows/counts must be positive: {nonpositive}"
            )
        if self.min_history_bars < self.ma_period + self.trend_lookback_bars:
            raise ValueError(
                "patterns.pullback_to_rising_dma.min_history_bars "
                f"({self.min_history_bars}) must be >= ma_period + trend_lookback_bars "
                f"({self.ma_period + self.trend_lookback_bars}) so the DMA slope is computable"
            )
        positive_pcts = {
            "min_dma_slope_pct": self.min_dma_slope_pct,
            "max_dist_above_dma_pct": self.max_dist_above_dma_pct,
            "max_pullback_depth_pct": self.max_pullback_depth_pct,
        }
        bad_pct = sorted(k for k, v in positive_pcts.items() if v <= 0)
        if bad_pct:
            raise ValueError(
                f"patterns.pullback_to_rising_dma percentages must be positive: {bad_pct}"
            )
        if self.max_undercut_pct < 0:
            raise ValueError(
                "patterns.pullback_to_rising_dma.max_undercut_pct must be >= 0 "
                f"(it may be 0), got {self.max_undercut_pct}"
            )
        return self


class FlatBaseBreakoutCfg(BaseModel):
    """Flat-base-breakout detector thresholds (iter-9 CONSUMED). EVERY tunable the
    `app.engine.patterns.detect_flat_base_breakout` detector reads lives here — the lookback window,
    the base window, the maximum (flat) base depth, the pivot-proximity band, the minimum history, and
    the volume window + minimum breakout-volume ratio — so NO detection literal lives in calc code
    (anti-goal: No magic numbers). Validated like `VcpCfg`: every window/count positive, the base fits
    inside the lookback, history covers the lookback, and every percent/ratio positive — an invalid
    block raises `ConfigError`, never a silent default."""

    model_config = ConfigDict(extra="allow")
    lookback_bars: int
    min_history_bars: int
    base_window: int
    max_base_depth_pct: float
    pivot_proximity_pct: float
    volume_window: int
    min_breakout_volume_ratio: float

    @model_validator(mode="after")
    def _validate(self) -> "FlatBaseBreakoutCfg":
        windows = {
            "lookback_bars": self.lookback_bars,
            "min_history_bars": self.min_history_bars,
            "base_window": self.base_window,
            "volume_window": self.volume_window,
        }
        nonpositive = sorted(k for k, v in windows.items() if v <= 0)
        if nonpositive:
            raise ValueError(
                f"patterns.flat_base_breakout windows/counts must be positive: {nonpositive}"
            )
        if self.base_window > self.lookback_bars:
            raise ValueError(
                f"patterns.flat_base_breakout.base_window ({self.base_window}) must be <= "
                f"lookback_bars ({self.lookback_bars})"
            )
        if self.min_history_bars < self.lookback_bars:
            raise ValueError(
                f"patterns.flat_base_breakout.min_history_bars ({self.min_history_bars}) must be >= "
                f"lookback_bars ({self.lookback_bars})"
            )
        pcts = {
            "max_base_depth_pct": self.max_base_depth_pct,
            "pivot_proximity_pct": self.pivot_proximity_pct,
            "min_breakout_volume_ratio": self.min_breakout_volume_ratio,
        }
        bad_pct = sorted(k for k, v in pcts.items() if v <= 0)
        if bad_pct:
            raise ValueError(
                f"patterns.flat_base_breakout percentages/ratios must be positive: {bad_pct}"
            )
        return self


class PatternsCfg(BaseModel):
    """Detected-pattern catalog. Holds one typed sub-block per detected pattern; the FIRST is `vcp`
    (iter-11). iter-9 adds two more — `pullback_to_rising_dma` and `flat_base_breakout` — each a typed
    sub-block riding alongside VCP exactly the same way. Designed so a future pattern is a new typed
    sub-block here (the catalog grows additively)."""

    model_config = ConfigDict(extra="allow")
    vcp: VcpCfg
    pullback_to_rising_dma: PullbackToRisingDmaCfg
    flat_base_breakout: FlatBaseBreakoutCfg


class FactorLabFactor(BaseModel):
    """One catalogued Factor-Lab factor (iter-10, J-25). `source` declares WHERE the stored value is
    read from — a typed `ScannerResult` score column, or a `record_json` component `raw` path
    (`<block>.components.<name>.raw`) — validated at boot via `parse_factor_source` + the Config-level
    cross-check against `scores.<block>.weights`. `direction` / `family` are DESCRIPTIVE metadata only:
    they do NOT flip the decile sort (the stored raw is read VERBATIM, already oriented by scoring)."""

    model_config = ConfigDict(extra="allow")
    key: str
    label: str
    family: str
    direction: Literal["higher_better", "lower_better"]
    source: str


class QuantileOption(BaseModel):
    """One entry of the multi-factor-combination quantile vocabulary (iter-12, J-26). `fraction` is the
    tail size a `top`/`bottom` condition selects (e.g. `0.20` = a quintile); the dropdown is built from
    this config-driven list (a config-only quantile needs no frontend edit). `fraction ∈ (0, 1)` and the
    `key` uniqueness are validated on `CombinationCfg`."""

    model_config = ConfigDict(extra="allow")
    key: str
    label: str
    fraction: float


class DefaultCondition(BaseModel):
    """One canonical default condition shown on first load (iter-12, J-26) — a catalog factor at its
    `top`/`bottom` `quantile`. `factor` references a sibling `FactorLabCfg.factors` key (cross-checked on
    `FactorLabCfg`, which can see both `factors` and `combination`); `quantile` references a
    `CombinationCfg.quantiles` key (cross-checked on `CombinationCfg`). `side` is validated by the
    `Literal` — an invalid side raises `ConfigError` at boot, never a silent default."""

    model_config = ConfigDict(extra="allow")
    factor: str
    side: Literal["top", "bottom"]
    quantile: str


class CompositeWeightingCfg(BaseModel):
    """The composite rank-blend's weighting scheme (iter-18, J-26). `scheme` is the config-declared blend
    weighting (currently `equal` — each condition's oriented percentile rank weighted by `default_weight`,
    then normalized to sum to 1 by the engine, so NO `1/k` weight literal lives in calc code — anti-goal:
    No magic numbers). `default_weight` is the per-condition base weight, validated `> 0` on `CompositeCfg`.
    An unknown scheme fails the `Literal` at boot (loud `ConfigError`, never a silent default)."""

    model_config = ConfigDict(extra="allow")
    scheme: Literal["equal"]
    default_weight: float


class CompositeCfg(BaseModel):
    """The composite percentile-rank-blend cohort config (iter-18, J-26) — the HEADLINE `Combined` cohort.
    The cohort is the top `quantile` of the pool by a config-`weighting` blend of the conditions' oriented
    percentile ranks of the STORED factor values: a deterministic ranking / GROUPING (the same read-only
    class as the J-25 decile sort) — NOT a fitted/learned/ML model and NOT a recomputed factor. `quantile`
    MUST be a real `CombinationCfg.quantiles` key (cross-checked on `CombinationCfg`, which can see both);
    `weighting.default_weight` MUST be `> 0`. An invalid block raises `ConfigError` at boot — never a silent
    default."""

    model_config = ConfigDict(extra="allow")
    quantile: str
    weighting: CompositeWeightingCfg

    @model_validator(mode="after")
    def _validate(self) -> "CompositeCfg":
        if self.weighting.default_weight <= 0:
            raise ValueError(
                "research.factor_lab.combination.composite.weighting.default_weight must be > 0, got "
                f"{self.weighting.default_weight}"
            )
        return self


class CombinationCfg(BaseModel):
    """Multi-factor-combination config (iter-12 / iter-18 re-scoped, J-26). EVERY tunable the read-only
    `app.engine.research.compute_factor_combination` reads lives here (anti-goal: No magic numbers — no
    condition count, quantile fraction, blend weight, or default in calc code): `min_conditions`/
    `max_conditions` bound the condition count (`max_conditions` is raised to the catalog-factor count so a
    user can combine UP TO ALL catalog factors — the cap lives in config, not code); `quantiles` is the
    ordered, config-driven top/bottom tail vocabulary; `composite` (iter-18) is the rank-blend's tunables
    (its `quantile` selects the headline Combined cohort, config-`weighting`); and `default_conditions` is
    the canonical 2-condition default served on first load. The low-sample threshold is REUSED from
    `walk_forward.min_sample` (no new threshold). Validated: `1 <= min_conditions <= max_conditions`; every
    `quantiles[*].fraction ∈ (0, 1)` and `key` unique; `composite.quantile` is a real `quantiles` key;
    `min_conditions <= len(default_conditions) <= max_conditions`; every `default_conditions[*].quantile`
    is a real `quantiles` key (the factor-key cross-check sits on `FactorLabCfg`). An invalid block raises
    `ConfigError` at boot — never a silent default."""

    model_config = ConfigDict(extra="allow")
    min_conditions: int
    max_conditions: int
    quantiles: list[QuantileOption] = Field(min_length=1)
    composite: CompositeCfg
    default_conditions: list[DefaultCondition] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate(self) -> "CombinationCfg":
        if not (1 <= self.min_conditions <= self.max_conditions):
            raise ValueError(
                "research.factor_lab.combination requires 1 <= min_conditions <= max_conditions, got "
                f"min_conditions={self.min_conditions}, max_conditions={self.max_conditions}"
            )
        bad_fraction = sorted(q.key for q in self.quantiles if not (0 < q.fraction < 1))
        if bad_fraction:
            raise ValueError(
                f"research.factor_lab.combination quantile fractions must be in (0, 1): {bad_fraction}"
            )
        keys = [q.key for q in self.quantiles]
        dupes = sorted({k for k in keys if keys.count(k) > 1})
        if dupes:
            raise ValueError(f"research.factor_lab.combination.quantiles have duplicate keys: {dupes}")
        quantile_keys = set(keys)
        if self.composite.quantile not in quantile_keys:
            raise ValueError(
                f"research.factor_lab.combination.composite.quantile {self.composite.quantile!r} is not a "
                f"real quantiles key (valid: {sorted(quantile_keys)})"
            )
        if not (self.min_conditions <= len(self.default_conditions) <= self.max_conditions):
            raise ValueError(
                f"research.factor_lab.combination.default_conditions count ({len(self.default_conditions)}) "
                f"must be in [{self.min_conditions}, {self.max_conditions}]"
            )
        bad_quantile = sorted(
            {c.quantile for c in self.default_conditions if c.quantile not in quantile_keys}
        )
        if bad_quantile:
            raise ValueError(
                "research.factor_lab.combination.default_conditions reference unknown quantiles: "
                f"{bad_quantile} (valid: {sorted(quantile_keys)})"
            )
        return self


# iter-32 (J-91) — the conditioning-band vocabulary for the Downtrend Opportunity study. Each band is a
# half-open `[min, max)` numeric range (the LAST band is inclusive at its max so the top of the scale is
# covered). The phase dimension reuses `config.market_phase.labels` (no separate catalog); only the two
# CONTINUOUS dimensions (severity 0..100, P(bear) 0..1) need an explicit band catalog so the study slices
# them into named cohorts without a hard-coded edge in calc code (anti-goal: No magic numbers).
class ConditioningBand(BaseModel):
    """One named conditioning band (J-91) over a continuous causal reading. `key` is the stable cohort id
    a samples drill-down round-trips; `label` is the display string; `min`/`max` are the half-open band
    edges (`min <= value < max`, with the band whose `max` is the scale top inclusive at `max`). A fixed
    structural membership rule — only the edges + labels live in config (no edge literal in calc code)."""

    model_config = ConfigDict(extra="allow")
    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    min: float
    max: float

    @model_validator(mode="after")
    def _validate(self) -> "ConditioningBand":
        if self.max <= self.min:
            raise ValueError(
                f"conditioning band {self.key!r} must have max ({self.max}) > min ({self.min})"
            )
        return self


def _validate_band_catalog(bands: list["ConditioningBand"], name: str, scale_top: float) -> None:
    """Validate one conditioning-band catalog (J-91): unique keys, ascending non-overlapping coverage of
    `[0, scale_top]` (the first band starts at 0, each band's `min` equals the prior band's `max`, the last
    band's `max` equals `scale_top`). A gap/overlap/partial-cover raises `ValueError` at boot — never a
    silent default (so every displayable value lands in exactly one band; the study never drops a row)."""
    keys = [b.key for b in bands]
    dupes = sorted({k for k in keys if keys.count(k) > 1})
    if dupes:
        raise ValueError(f"{name} have duplicate keys: {dupes}")
    ordered = sorted(bands, key=lambda b: b.min)
    if ordered[0].min != 0:
        raise ValueError(f"{name} must start at 0, got {ordered[0].min}")
    if ordered[-1].max != scale_top:
        raise ValueError(f"{name} must end at {scale_top}, got {ordered[-1].max}")
    for prev, nxt in zip(ordered, ordered[1:]):
        if nxt.min != prev.max:
            raise ValueError(
                f"{name} must be contiguous (no gap/overlap): band {prev.key!r} ends at {prev.max} "
                f"but band {nxt.key!r} starts at {nxt.min}"
            )


class DowntrendOpportunityCfg(BaseModel):
    """The Downtrend Opportunity study's conditioning vocabulary (iter-32, J-91 — consumed by
    `app.engine.research.compute_downtrend_opportunity_study`). The study groups the SAME stored
    event-study observation set, additively tagged with the CAUSAL as-of phase / severity band / P(bear)
    band at each observation's snapshot date (read from the read-only `market_phase` derivation, <= D).

    The PHASE dimension reuses `config.market_phase.labels` (no separate list). The two continuous
    dimensions need an explicit band catalog so the study slices them deterministically WITHOUT a
    hard-coded edge in calc code (anti-goal: No magic numbers):
      - `severity_bands` — named bands over the 0..100 severity scale (contiguous, covering 0..100).
      - `pbear_bands` — named bands over the 0..1 filtered-P(bear) scale (contiguous, covering 0..1).

    The horizons + min-sample threshold are REUSED from `config.walk_forward` (no new threshold). Both
    catalogs are boot-validated for unique keys + contiguous full coverage so every displayable reading
    lands in exactly one band (the study never drops or fabricates a cohort)."""

    model_config = ConfigDict(extra="allow")
    severity_bands: list[ConditioningBand] = Field(min_length=1)
    pbear_bands: list[ConditioningBand] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate(self) -> "DowntrendOpportunityCfg":
        _validate_band_catalog(self.severity_bands, "research.downtrend_opportunity.severity_bands", 100.0)
        _validate_band_catalog(self.pbear_bands, "research.downtrend_opportunity.pbear_bands", 1.0)
        return self


class FactorLabCfg(BaseModel):
    """Factor-Lab config (iter-10, J-25). `deciles` (validated > 1) is the equal-count quantile count;
    `factors` is the ordered, config-driven catalog; `combination` (iter-12, J-26) is the typed
    multi-factor-combination block. The decile count + the factor catalog living in config (not code) is
    the No-magic-numbers keystone; the low-sample threshold is REUSED from `walk_forward.min_sample` (no
    new threshold). Validated: `deciles > 1`, every factor `key` unique, and every
    `combination.default_conditions[*].factor` references a real `factors` key (cross-checked here — this
    model can see BOTH `factors` and `combination`, exactly like the Config-level source cross-check).
    An invalid block raises `ConfigError`, never a silent default (factor-source resolvability is
    cross-checked on the top-level `Config`, which can see `scores`)."""

    model_config = ConfigDict(extra="allow")
    deciles: int
    factors: list[FactorLabFactor] = Field(min_length=1)
    combination: CombinationCfg

    @model_validator(mode="after")
    def _validate(self) -> "FactorLabCfg":
        if self.deciles <= 1:
            raise ValueError(f"research.factor_lab.deciles must be > 1, got {self.deciles}")
        keys = [f.key for f in self.factors]
        dupes = sorted({k for k in keys if keys.count(k) > 1})
        if dupes:
            raise ValueError(f"research.factor_lab.factors have duplicate keys: {dupes}")
        factor_keys = set(keys)
        bad_factor = sorted(
            {c.factor for c in self.combination.default_conditions if c.factor not in factor_keys}
        )
        if bad_factor:
            raise ValueError(
                "research.factor_lab.combination.default_conditions reference unknown factors: "
                f"{bad_factor} (valid: {sorted(factor_keys)})"
            )
        return self


class ResearchCfg(BaseModel):
    """The Research-lab analytics config (iter-10). Holds one typed sub-block per lab; the FIRST is the
    Factor Lab (J-25). Designed to grow additively (event study J-29, downtrend opportunity J-91, etc.)
    exactly like `PatternsCfg` grew its detector sub-blocks.

    `downtrend_opportunity` (iter-32, J-91) is the conditioning-band vocabulary for the Downtrend
    Opportunity study. It defaults to a sane built-in catalog so a config predating it (and the inline test
    fixtures) still loads — the real `config.yaml` supplies the tuned bands. The forward `DowntrendOpportunityCfg`
    is constructed below the class so the default can name it."""

    model_config = ConfigDict(extra="allow")
    factor_lab: FactorLabCfg
    downtrend_opportunity: "DowntrendOpportunityCfg" = Field(
        default_factory=lambda: _default_downtrend_opportunity()
    )


def _default_downtrend_opportunity() -> "DowntrendOpportunityCfg":
    """The built-in default Downtrend Opportunity conditioning catalog (J-91) — used when a config predating
    the block (or an inline test fixture) omits `research.downtrend_opportunity`. The real `config.yaml`
    supplies the tuned bands; this default keeps the smallest valid config loading. Contiguous, full-cover
    over 0..100 (severity) and 0..1 (P(bear)), so every displayable reading lands in exactly one band."""
    return DowntrendOpportunityCfg(
        severity_bands=[
            ConditioningBand(key="calm", label="Calm (0–30)", min=0.0, max=30.0),
            ConditioningBand(key="elevated", label="Elevated (30–50)", min=30.0, max=50.0),
            ConditioningBand(key="stressed", label="Stressed (50–70)", min=50.0, max=70.0),
            ConditioningBand(key="severe", label="Severe (70–100)", min=70.0, max=100.0),
        ],
        pbear_bands=[
            ConditioningBand(key="low", label="Low P(bear) (0–0.25)", min=0.0, max=0.25),
            ConditioningBand(key="moderate", label="Moderate P(bear) (0.25–0.50)", min=0.25, max=0.50),
            ConditioningBand(key="high", label="High P(bear) (0.50–0.75)", min=0.50, max=0.75),
            ConditioningBand(key="extreme", label="Extreme P(bear) (0.75–1.0)", min=0.75, max=1.0),
        ],
    )


# iter-29 (J-87 / J-88) — the named severity-component weight set. The deterministic drawdown-severity
# score blends EXACTLY these five named components, so `config.market_phase.weights` MUST cover this
# set (completeness) and sum ~1.0 (mirroring `regime.weights` / `scores.<block>.weights`). Each weight
# lives in config, never invented in code (anti-goal: No magic numbers).
MARKET_PHASE_WEIGHT_KEYS = {
    "drawdown_depth",        # trailing-peak peak-to-trough drawdown depth of the benchmark
    "time_underwater",       # fraction of the lookback window spent below the trailing peak
    "regime_risk",           # the STORED regime score inverted to a risk reading (read verbatim)
    "breadth_below_200dma",  # fraction of the universe BELOW its 200-DMA (1 - stored breadth)
    "vix_gate",              # the ^VIX stress reading relative to the configured gate threshold
}
# The two regime-switching states (J-88). A fixed structural vocabulary (not a tunable) — the config
# carries the transition probabilities + per-state emission params keyed by these names.
REGIME_SWITCHING_STATES = ("bear", "risk_on")


class MarketPhaseCfg(BaseModel):
    """Market Phase & drawdown-Severity config (iter-29, J-87 — consumed by `app.engine.market_phase`).

    Every number the read-only phase/severity derivation uses lives here (anti-goal: No magic numbers —
    no edge/weight/threshold/gate literal in `app/engine/market_phase.py`):
      - `labels` / `phase_edges` — the discrete phase vocabulary (Expansion / Pullback / Correction /
        Bear / Recovery) and the SEVERITY -> phase cutoffs (`severity >= min -> label`, descending,
        covering 0..100 — the SAME shape `regime.label_edges` uses, validated by the shared helper).
      - `weights` — the five named severity components (drawdown depth, time-underwater, regime-risk,
        breadth-below-200DMA, ^VIX gate), summing ~1.0 (validated like `regime.weights`).
      - `lookback_days` — the trailing window (calendar days) the trailing peak + time-underwater are
        measured over (a finite causal window <= D).
      - `drawdown_full_severity_pct` — the peak-to-trough drawdown magnitude (%) that maps the drawdown
        component to its full 1.0; a shallower drawdown scales linearly, a deeper one clamps at 1.0.
      - `vix_gate` — the ^VIX level that maps the VIX component to its full 1.0 (a calmer tape scales
        below it, a more stressed tape clamps at 1.0).
      - `recovery_min_off_trough_pct` — once OFF the trough by this %, a still-underwater tape reads
        Recovery rather than Bear/Correction (the rebound leg of the cycle).
      - `min_history_bars` — below this many benchmark bars <= D the window is insufficient -> NA/partial
        (never a fabricated phase/severity).
      - `observation_disclosure_limit` — how many of the MOST RECENT filter observations the served
        payload discloses (the deterministic forward filter still consumes EVERY observation <= D — this
        only bounds the disclosed tail so a daily-history host doesn't serve thousands of chips; the
        served P(bear) is unchanged). MUST be `>= 1`.
      - `severity_velocity_window` — the lookback window (in snapshots) the per-date `severity_velocity`
        (iter-44, J-102) ordinary-least-squares slope of the served 0-100 severity is fit over. STRICTLY
        causal (severity at dates <= each date only); NA at the warm-up head where fewer than this many
        snapshots precede a date; positive sign = severity worsening. MUST be `>= 2` (a slope needs at
        least two points). No magic number — the engine reads this window from config, never a literal.

    iter-30 (J-89 / J-90) ADDITIVE downtrend-history + recovery-turn keys (consumed by the new read-only
    timeline / episode / retrospective / recovery-turn-signal derivations — every threshold from config,
    No magic numbers; `market_phase.py` stays in `test_no_magic_numbers`'s `CALC_FILES`):
      - `downtrend_pbear_threshold` — a per-date filtered P(bear) at/above this (OR a Bear/Correction
        phase) opens a CAUSAL downtrend episode (J-89). In [0, 1].
      - `recovery_signal_pbear_exit` — the filtered P(bear) the as-of must cross BELOW (a downtrend-exit
        transition) for the causal recovery/turn signal to fire (J-90), gated by the trailing-MA reclaim.
        In [0, 1]; MUST be `<= downtrend_pbear_threshold` (you cannot signal a recovery at a P(bear) that
        still opens a downtrend).
      - `recovery_trailing_ma_days` — the trailing moving-average window (calendar days) the index close
        must RECLAIM (close above its trailing MA) to confirm the recovery turn (J-90). Positive.
      - `bry_boschan_min_phase_days` — the FENCED retrospective true-bear dater's minimum phase length
        (calendar days) — a peak->trough decline shorter than this is not a true-bear phase (a Bry-Boschan/
        NBER-style minimum-duration censoring rule). Positive. Retrospective ONLY (never an as-of value).
      - `bry_boschan_min_amplitude_pct` — the retrospective true-bear dater's minimum peak-to-trough
        DRAWDOWN amplitude (%) — a decline shallower than this is not a true-bear phase. Positive.
        Retrospective ONLY."""

    model_config = ConfigDict(extra="allow")
    labels: list[str] = Field(min_length=1)
    phase_edges: list[LabelEdge] = Field(min_length=1)
    weights: dict[str, float] = Field(min_length=1)
    lookback_days: int
    drawdown_full_severity_pct: float
    vix_gate: float
    recovery_min_off_trough_pct: float
    min_history_bars: int
    observation_disclosure_limit: int
    # iter-44 (J-102) — the lookback window (snapshots) the per-date severity_velocity OLS slope is fit over.
    severity_velocity_window: int
    # iter-30 (J-89 / J-90) — downtrend-history + recovery-turn thresholds (every threshold from config).
    downtrend_pbear_threshold: float
    recovery_signal_pbear_exit: float
    recovery_trailing_ma_days: int
    bry_boschan_min_phase_days: int
    bry_boschan_min_amplitude_pct: float

    @model_validator(mode="after")
    def _validate(self) -> "MarketPhaseCfg":
        _require_complete_weights(self.weights, MARKET_PHASE_WEIGHT_KEYS, "market_phase.weights")
        labelset = set(self.labels)
        unknown = [e.label for e in self.phase_edges if e.label not in labelset]
        if unknown:
            raise ValueError(f"market_phase.phase_edges reference unknown labels: {unknown}")
        _validate_edges_descending_and_cover_zero(self.phase_edges, "market_phase.phase_edges")
        positive = {
            "lookback_days": self.lookback_days,
            "drawdown_full_severity_pct": self.drawdown_full_severity_pct,
            "vix_gate": self.vix_gate,
            "recovery_min_off_trough_pct": self.recovery_min_off_trough_pct,
            "min_history_bars": self.min_history_bars,
            # iter-30 (J-89 / J-90) positive scalars
            "recovery_trailing_ma_days": self.recovery_trailing_ma_days,
            "bry_boschan_min_phase_days": self.bry_boschan_min_phase_days,
            "bry_boschan_min_amplitude_pct": self.bry_boschan_min_amplitude_pct,
        }
        nonpositive = sorted(k for k, v in positive.items() if v <= 0)
        if nonpositive:
            raise ValueError(f"market_phase values must be positive: {nonpositive}")
        if self.observation_disclosure_limit < 1:
            raise ValueError("market_phase.observation_disclosure_limit must be >= 1")
        # iter-44 (J-102): the severity-velocity OLS slope needs at least two points; a window < 2 (or a
        # non-positive one) is incoherent and rejected loudly at load (No magic numbers — the window is the
        # ONLY source of the lookback; the engine never hard-codes it).
        if self.severity_velocity_window < 2:
            raise ValueError(
                "market_phase.severity_velocity_window must be >= 2 "
                f"(got {self.severity_velocity_window}) — a slope needs at least two points"
            )
        # iter-30 (J-89 / J-90): the two probability thresholds must be valid [0, 1] probabilities, and a
        # recovery-exit threshold ABOVE the downtrend-open threshold would be incoherent (you cannot signal
        # a recovery turn at a P(bear) that still opens a downtrend episode) — rejected at load.
        in_unit = {
            "downtrend_pbear_threshold": self.downtrend_pbear_threshold,
            "recovery_signal_pbear_exit": self.recovery_signal_pbear_exit,
        }
        out_of_range = sorted(k for k, v in in_unit.items() if not (0 <= v <= 1))
        if out_of_range:
            raise ValueError(f"market_phase P(bear) thresholds must be in [0, 1]: {out_of_range}")
        if self.recovery_signal_pbear_exit > self.downtrend_pbear_threshold:
            raise ValueError(
                "market_phase.recovery_signal_pbear_exit "
                f"({self.recovery_signal_pbear_exit}) must be <= downtrend_pbear_threshold "
                f"({self.downtrend_pbear_threshold})"
            )
        return self


class RegimeSwitchingEmission(BaseModel):
    """One state's emission parameters for the J-88 2-state filter (consumed VERBATIM — NEVER EM-fit at
    serve time). The per-observation likelihood of belonging to this state is a Gaussian on the stored
    observation reading (the same severity-style stress reading the filter runs over): `mean` is the
    state's central reading and `std` its spread (positive). Both come from a committed deterministic
    offline calibration (running that calibration live is out of scope; only these committed params are
    read)."""

    model_config = ConfigDict(extra="allow")
    mean: float
    std: float

    @model_validator(mode="after")
    def _validate(self) -> "RegimeSwitchingEmission":
        if self.std <= 0:
            raise ValueError("regime_switching emission std must be positive")
        return self


class RegimeSwitchingCfg(BaseModel):
    """The deterministic 2-state regime-switching params for the forward FILTERED P(bear) (iter-29,
    J-88 — consumed by `app.engine.market_phase`). EVERY number is read VERBATIM from config; the filter
    is a closed-form Hamilton recursion, NEVER EM-fit at serve time (anti-goal: No magic numbers + the
    filter is deterministic).

      - `transition` — the 2x2 Markov transition matrix as a nested dict keyed by the two states
        (`bear`/`risk_on`): `transition[from][to]` is P(next=to | current=from). Each row must sum ~1.0
        and reference exactly the two states (validated below).
      - `initial_bear` — the prior P(state=bear) at the first observation (in [0, 1]).
      - `emissions` — the per-state Gaussian emission params (mean + std) keyed by the two states.

    The observation the filter ingests per date is the SAME stress reading severity is built from (a
    causal [0,1] reading <= D), so 2022 (deep drawdown, high VIX, low breadth) drives P(bear) toward 1
    and a calm 2024/2026 tape pulls it back — deterministically, from committed params only."""

    model_config = ConfigDict(extra="allow")
    transition: dict[str, dict[str, float]] = Field(min_length=1)
    initial_bear: float
    emissions: dict[str, RegimeSwitchingEmission] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate(self) -> "RegimeSwitchingCfg":
        states = set(REGIME_SWITCHING_STATES)
        if set(self.transition) != states:
            raise ValueError(
                f"regime_switching.transition must have exactly the states {sorted(states)}; "
                f"got {sorted(self.transition)}"
            )
        for from_state, row in self.transition.items():
            if set(row) != states:
                raise ValueError(
                    f"regime_switching.transition[{from_state!r}] must reference exactly "
                    f"{sorted(states)}; got {sorted(row)}"
                )
            total = sum(row.values())
            if abs(total - 1.0) > _WEIGHT_SUM_TOLERANCE:
                raise ValueError(
                    f"regime_switching.transition[{from_state!r}] must sum to ~1.0, got {total}"
                )
        if not (0 <= self.initial_bear <= 1):
            raise ValueError(f"regime_switching.initial_bear must be in [0, 1], got {self.initial_bear}")
        missing = states - set(self.emissions)
        if missing:
            raise ValueError(f"regime_switching.emissions missing states: {sorted(missing)}")
        return self


class MethodologyThreshold(BaseModel):
    """One row of a methodology entry's threshold list (iter-12). EITHER a config-referenced numeric
    row ({label, ref, cmp?, unit?}) whose displayed value resolves LIVE from the canonical config
    block `ref` points at (so it always matches the engine — never re-typed), OR a plain prose rule
    ({label, text}). EXACTLY one of `ref`/`text` is present (anti-goal: No magic numbers — the numbers
    are never hard-coded in the catalog copy)."""

    model_config = ConfigDict(extra="allow")
    label: str
    ref: Optional[str] = None
    cmp: Optional[str] = None
    unit: Optional[str] = None
    text: Optional[str] = None

    @model_validator(mode="after")
    def _exactly_one_of_ref_or_text(self) -> "MethodologyThreshold":
        if (self.ref is None) == (self.text is None):
            raise ValueError(
                f"methodology threshold {self.label!r} must have exactly one of `ref` or `text`"
            )
        return self


class MethodologyEntry(BaseModel):
    """One glossary entry (iter-12) — a setup status or a detected pattern. `key` matches the
    canonical identifier (a setup status in `app.engine.setups.ALL_STATUSES`, or a pattern key in
    `config.patterns`); `name`/`meaning`/`example` are plain-language COPY; `thresholds` reference
    the config keys that define the entry (resolved live by `app.engine.methodology.build_catalog`)."""

    model_config = ConfigDict(extra="allow")
    key: str
    kind: Literal["setup", "pattern"]
    name: str
    meaning: str
    example: str
    thresholds: list[MethodologyThreshold] = Field(default_factory=list)


class UniverseSelectionCfg(BaseModel):
    """The config-backed Universe Selection section (J-22). `membership_rule` is the plain-language
    prose describing how the universe is sourced (an index-membership union, screened); `thresholds`
    references the SAME `universe.filters` keys the offline screen reads, resolved LIVE at boot/serve
    via the `ref` mechanism (so the displayed numbers always match the screen — never re-typed; the
    matching-config keystone, anti-goal: No magic numbers). The resolved member count is NOT stored
    here — it is read live from the one canonical `config.universe.symbols` by `build_catalog`."""

    model_config = ConfigDict(extra="allow")
    membership_rule: str
    thresholds: list[MethodologyThreshold] = Field(min_length=1)


class GlossaryCategory(BaseModel):
    """One ordered glossary category (iter-4 goal-mode, J-47) — a group of terms shown together on
    /methodology and the lookup namespace tooltips read. `key` is the stable identifier a term's
    `category` points at; `label` is the display heading (e.g. "Scores & Buckets"). The category LIST
    order is the catalog order rendered on the page (a stable, ordered list)."""

    model_config = ConfigDict(extra="allow")
    key: str = Field(min_length=1)
    label: str = Field(min_length=1)


class GlossaryTerm(BaseModel):
    """One authored glossary term (iter-4 goal-mode, J-47). `term` is the LITERAL UI string as shown on
    a page (the tooltip/lookup key — e.g. "rank-IC", "breadth > 50-DMA"); `category` references a
    `GlossaryCategory.key`; `definition` is the plain-language explanation (the product's skeptical,
    plain voice — never filler). `where` optionally notes where-it-appears. `thresholds` optionally cite
    config thresholds via the SAME `ref` mechanism the setup/pattern entries use (resolved live at boot —
    never a re-typed number; anti-goal: No magic numbers).

    The Setups & Patterns glossary category is DERIVED from `methodology.entries` by `build_catalog`, so
    a term here MUST NOT re-describe a setup/pattern: a `term`/`category`/key colliding with a setup or
    pattern entry is rejected at boot (anti-goal: Glossary copy lives in one catalog)."""

    model_config = ConfigDict(extra="allow")
    term: str = Field(min_length=1)
    category: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    where: Optional[str] = None
    thresholds: list[MethodologyThreshold] = Field(default_factory=list)

    @field_validator("definition")
    @classmethod
    def _definition_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("glossary term definition must not be blank")
        return value


class MethodologyCfg(BaseModel):
    """The single config-backed Setup & Pattern catalog (iter-12, J-12). One ORDERED list of entries
    (the setup statuses + the detected patterns) carrying the human copy + threshold references. The
    /methodology page, the /stocks badge tooltips, AND the /stocks setup-filter vocabulary ALL read
    this one catalog (anti-goal: Setup & pattern vocabulary is config-driven in the UI too). Every
    threshold `ref` is resolved against the loaded Config at boot (see `Config._methodology_refs_resolve`)
    so an unresolvable reference fails loudly — never a silent placeholder number.

    `universe_selection` (J-22, optional) adds the config-backed Universe Selection section served on
    /methodology — the membership rule + the `universe.filters` screen thresholds (resolved live).

    `categories` + `terms` (J-47, iter-4 goal-mode) add the ≥100-term terminology glossary served on the
    SAME GET /api/methodology payload. The Setups & Patterns category is DERIVED from `entries` (never
    re-described) — see `app.engine.methodology.build_catalog`. Both default empty so the smallest valid
    catalog (and the inline test fixtures) need no glossary block; boot validation (term/category/ref/
    collision checks) only fires for the terms that ARE authored."""

    model_config = ConfigDict(extra="allow")
    intro: Optional[str] = None
    universe_selection: Optional[UniverseSelectionCfg] = None
    entries: list[MethodologyEntry] = Field(min_length=1)
    categories: list[GlossaryCategory] = Field(default_factory=list)
    terms: list[GlossaryTerm] = Field(default_factory=list)

    @model_validator(mode="after")
    def _glossary_terms_well_formed(self) -> "MethodologyCfg":
        """Boot validation for the J-47 glossary (the parts that don't need the whole Config):

          - category keys are unique;
          - every authored term's `category` references a declared category key;
          - authored term keys are unique;
          - an authored term key MUST NOT collide with a setup/pattern entry `key` OR `name` (no second
            copy of a setup/pattern — the Setups & Patterns category is derived from `entries`).

        (Threshold `ref` resolution needs the full Config and is checked in `Config._methodology_refs_resolve`.)"""
        category_keys = [c.key for c in self.categories]
        if len(category_keys) != len(set(category_keys)):
            raise ValueError("methodology glossary category keys must be unique")
        category_key_set = set(category_keys)

        entry_identifiers = {e.key for e in self.entries} | {e.name for e in self.entries}

        seen_terms: set[str] = set()
        for term in self.terms:
            if term.category not in category_key_set:
                raise ValueError(
                    f"glossary term {term.term!r} references unknown category {term.category!r}"
                )
            if term.term in seen_terms:
                raise ValueError(f"duplicate glossary term key {term.term!r}")
            seen_terms.add(term.term)
            if term.term in entry_identifiers:
                raise ValueError(
                    f"glossary term {term.term!r} collides with a setup/pattern entry — the Setups & "
                    "Patterns category is derived from `entries`; a setup/pattern is explained in exactly "
                    "one place (anti-goal: Glossary copy lives in one catalog)"
                )
        return self


def _node_keys(node: object) -> set[str]:
    """The traversable keys at `node`: a pydantic model's declared fields + any extra='allow' keys,
    or a mapping's keys. A scalar has none (it cannot be descended into)."""
    if isinstance(node, BaseModel):
        keys = set(type(node).model_fields)
        if node.__pydantic_extra__:
            keys |= set(node.__pydantic_extra__)
        return keys
    if isinstance(node, Mapping):
        return set(node)
    return set()


def resolve_ref(config: "Config", ref: str) -> object:
    """Resolve a dotted-path reference (e.g. "decision_rules.actionable.leadership") to its LIVE value
    in the loaded `Config`, traversing pydantic-model attributes, mappings, AND sequence INDICES (a
    numeric segment indexes into a list/tuple, e.g. "regime.label_edges.0.min"). Raises `ConfigError` on
    any unresolvable segment — the methodology glossary never shows a placeholder threshold (anti-goal:
    No fabricated data)."""
    node: object = config
    for part in ref.split("."):
        # numeric segment into a sequence (but not a str/bytes/Mapping) — supports list-element refs
        if (
            part.lstrip("-").isdigit()
            and isinstance(node, Sequence)
            and not isinstance(node, (str, bytes))
        ):
            index = int(part)
            if not -len(node) <= index < len(node):
                raise ConfigError(
                    f"methodology threshold ref {ref!r} is unresolvable at segment {part!r} "
                    f"(index out of range for length-{len(node)} sequence)"
                )
            node = node[index]
            continue
        if part not in _node_keys(node):
            raise ConfigError(f"methodology threshold ref {ref!r} is unresolvable at segment {part!r}")
        node = node[part] if isinstance(node, Mapping) else getattr(node, part)
    return node


class DatabaseCfg(BaseModel):
    model_config = ConfigDict(extra="allow")
    url: str = Field(min_length=1)


class ProviderCatalogEntry(BaseModel):
    """One import-source provider in the config-driven catalog (J-33). The catalog (the list, and each
    provider's key requirement + env-var NAME) lives in `config.yaml` `data_manager.providers` — there is
    NO hardcoded provider list in code (anti-goal: the provider catalog is config-driven).

      - `id`     — the stable provider key `make_provider` resolves and a job's `source` selects.
      - `label`  — the display name shown in the import-source picker.
      - `needs_key` — whether a credential is required (read from the environment, or pasted session-only).
      - `env_var`   — the environment-variable NAME the key is read from (the NAME only, never the value);
                      REQUIRED whenever `needs_key` (validated below) so availability can be env-detected.
      - `supports_market_cap` — whether the source can supply the market-cap field the J-35 expand job
                      gates on. Declared NOW so the catalog schema is stable; consumed only in J-35
                      (default `False` — a source is assumed NOT market-cap-capable unless it says so).

    Anti-goal *Import keys are env-or-session, never persisted*: NO key VALUE is ever stored in or served
    from this model — it carries only the env-var name + the boolean requirement + a display label."""

    model_config = ConfigDict(extra="allow")
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    needs_key: bool = False
    env_var: Optional[str] = None
    supports_market_cap: bool = False

    @model_validator(mode="after")
    def _env_var_present_when_needs_key(self) -> "ProviderCatalogEntry":
        if self.needs_key and not self.env_var:
            raise ValueError(
                f"provider {self.id!r} has needs_key=true but no env_var — the environment-variable "
                "name is required so the key can be read from the environment (never hard-coded)"
            )
        return self


class ImportChunkingCfg(BaseModel):
    """Chunked-import tunables (iter-22 CONSUMED, J-34). EVERY chunk/backoff/sleep number the resilient
    live-FETCH loop reads lives here (anti-goal: No magic numbers — NO chunk/backoff/sleep literal in
    `app.engine.data_manager` or the providers; mirrors how `max_range_days` etc. live in config).

      - `symbol_batch_size` — symbols fetched per chunk (the symbol-batch dimension of the chunk plan).
      - `date_window_days`  — max calendar days per date-window chunk (the other plan dimension); the
                              chunk plan = symbol-batches × date-windows, so `chunk_total` derives from
                              both.
      - `max_retries`       — 429 retry attempts (after the first try) before the import pauses resumable.
      - `backoff_base_seconds` / `backoff_cap_seconds` — exponential backoff `min(base * 2**attempt, cap)`
                              between 429 retries; `cap` MUST be `>= base`.
      - `inter_request_sleep_seconds` — polite delay between per-symbol requests (MAY be 0).
      - `fetch_workers` — the bounded parallel fetch-pool size (J-46): symbols within a chunk fetch on
                          this many worker threads (network I/O only — DB writes stay serialized on the
                          orchestrating thread). MUST be `>= 1` (1 = effectively serial, still valid).
      - `backfill_workers` — the bounded parallel BACKFILL-pool size (J-53): the multi-date snapshot
                          backfill fans the per-date COMPUTE out to this many worker threads (each on its
                          own read-only session — pure compute, no DB write), while the orchestrating
                          thread owns every snapshot/forward-return WRITE serially. MUST be `>= 1`
                          (1 = effectively serial, the byte-identical sequential baseline — still valid).

    Boot-validated: the four sizes/retries/backoff numbers MUST be positive, `fetch_workers >= 1`,
    `backfill_workers >= 1`, and `cap >= base`; the inter-request sleep MUST be `>= 0` (a zero polite
    delay is valid). An invalid block raises `ConfigError`, never a silent default."""

    model_config = ConfigDict(extra="allow")
    symbol_batch_size: int
    date_window_days: int
    max_retries: int
    backoff_base_seconds: float
    backoff_cap_seconds: float
    inter_request_sleep_seconds: float
    fetch_workers: int
    backfill_workers: int

    @model_validator(mode="after")
    def _validate(self) -> "ImportChunkingCfg":
        positive = {
            "symbol_batch_size": self.symbol_batch_size,
            "date_window_days": self.date_window_days,
            "max_retries": self.max_retries,
            "backoff_base_seconds": self.backoff_base_seconds,
            "backoff_cap_seconds": self.backoff_cap_seconds,
        }
        nonpositive = sorted(k for k, v in positive.items() if v <= 0)
        if nonpositive:
            raise ValueError(f"data_manager.import_chunking values must be positive: {nonpositive}")
        if self.fetch_workers < 1:
            raise ValueError(
                "data_manager.import_chunking.fetch_workers must be >= 1 (1 = serial, still valid)"
            )
        if self.backfill_workers < 1:
            raise ValueError(
                "data_manager.import_chunking.backfill_workers must be >= 1 (1 = serial, still valid)"
            )
        if self.inter_request_sleep_seconds < 0:
            raise ValueError(
                "data_manager.import_chunking.inter_request_sleep_seconds must be >= 0"
            )
        if self.backoff_cap_seconds < self.backoff_base_seconds:
            raise ValueError(
                "data_manager.import_chunking.backoff_cap_seconds must be >= backoff_base_seconds"
            )
        return self


class JobProgressCfg(BaseModel):
    """J-66 fine-grained, honest job-progress knobs (the live job card's poll/heartbeat/granularity
    settings). EVERY polling/heartbeat/granularity number the progress instrumentation + the `/data`
    live job card read lives here (anti-goal: No magic numbers — NO poll/heartbeat literal in the
    frontend job card or `app.engine.data_manager`).

      - `poll_interval_seconds`   — how often the `/data` live job card re-polls the job-status endpoint.
      - `heartbeat_stale_seconds` — the "updated Ns ago" staleness threshold past which the UI flags the
                                    job as possibly stalled (a slow-but-alive job ticks its heartbeat
                                    under this; a genuinely stalled one does not).
      - `per_symbol_ticks`        — tick the fetch symbols counter at per-SYMBOL completion granularity
                                    (true) instead of per-chunk; the workers tick a thread-safe distinct-
                                    symbol completion counter while ALL DB writes stay on the orchestrating
                                    thread (false = per-chunk fallback).

    Boot-validated: the two time knobs MUST be positive. An invalid block raises `ConfigError`, never a
    silent default."""

    model_config = ConfigDict(extra="allow")
    poll_interval_seconds: float
    heartbeat_stale_seconds: float
    per_symbol_ticks: bool = True

    @model_validator(mode="after")
    def _validate(self) -> "JobProgressCfg":
        positive = {
            "poll_interval_seconds": self.poll_interval_seconds,
            "heartbeat_stale_seconds": self.heartbeat_stale_seconds,
        }
        nonpositive = sorted(k for k, v in positive.items() if v <= 0)
        if nonpositive:
            raise ValueError(f"data_manager.job_progress values must be positive: {nonpositive}")
        return self


class DataManagerCfg(BaseModel):
    """Data Manager job limits / display caps + the import provider catalog (iter-3 / iter-21 CONSUMED,
    J-17 / J-33) + the iter-22 (J-34) chunked-import block. EVERY tunable the on-demand fetch/backfill
    orchestration reads lives here (anti-goal: No magic numbers — no job/range/preview/chunk/backoff
    literal in `app.engine.data_manager` or `app.api.data`).

      - `providers` — the config-driven import-source catalog (J-33). The FETCH path resolves the
        job-selected `source` against this list — there is NO hardcoded provider list in code. The
        offline boot/runtime `provider: seed` is the DEFAULT offline provider, NOT an import source, and
        is deliberately kept OUT of this catalog. (Retired the old 2-value `live_provider` Literal — the
        import source is validated against the catalog instead.)
      - `default_source` — the catalog `id` used when a job omits `source` (preserves J-17 fetch
        behavior); MUST be a real catalog id (validated below), and is a no-key source in `config.yaml`
        so an omitted-source fetch never fails the key gate.
      - `max_range_days` bounds a single job's inclusive calendar span; `gap_preview` /
        `run_history_limit` are payload display caps.

    Validated like the other typed sections — every limit positive, catalog ids unique, and
    `default_source` ∈ the catalog — an invalid block raises `ConfigError`, never a silent default."""

    model_config = ConfigDict(extra="allow")
    providers: list[ProviderCatalogEntry] = Field(min_length=1)
    default_source: str = Field(min_length=1)
    max_range_days: int
    gap_preview: int
    run_history_limit: int
    import_chunking: ImportChunkingCfg  # J-34 chunked-import tunables (boot-validated above)
    job_progress: JobProgressCfg  # J-66 fine-grained progress knobs (poll/heartbeat/granularity)

    def provider_ids(self) -> list[str]:
        """The catalog ids, in config order (the import-source vocabulary)."""
        return [p.id for p in self.providers]

    def provider_by_id(self, source_id: str) -> Optional[ProviderCatalogEntry]:
        """The catalog entry for `source_id`, or None when it is not in the catalog."""
        return next((p for p in self.providers if p.id == source_id), None)

    @model_validator(mode="after")
    def _validate(self) -> "DataManagerCfg":
        limits = {
            "max_range_days": self.max_range_days,
            "gap_preview": self.gap_preview,
            "run_history_limit": self.run_history_limit,
        }
        nonpositive = sorted(k for k, v in limits.items() if v <= 0)
        if nonpositive:
            raise ValueError(f"data_manager limits must be positive: {nonpositive}")
        ids = [p.id for p in self.providers]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            raise ValueError(f"data_manager.providers have duplicate ids: {dupes}")
        if self.default_source not in ids:
            raise ValueError(
                f"data_manager.default_source {self.default_source!r} is not in the provider catalog "
                f"(valid: {sorted(ids)})"
            )
        return self


# iter-32 (J-92) — the optional FRED macro feed config. EVERY tunable the macro provider + the
# config-default-OFF macro-conditioning legs read lives here (anti-goal: No magic numbers — no series id /
# publication-lag / enable literal in calc code). Macro ships DEFAULT-OFF so with it absent/disabled every
# J-87..J-91 figure is byte-identical to the price/breadth/VIX-only path.
class MacroSeriesCfg(BaseModel):
    """One configured FRED macro series (iter-32, J-92). `id` is the stable internal key the
    `MacroSeries` table stores + a wiring leg references; `fred_series_id` is the upstream FRED series
    identifier the provider fetches (e.g. `T10Y2Y`); `label` is the display string; `publication_lag_days`
    is the calendar-day reporting lag — a value is only usable for date D when `published_date <= D` (so
    `published_date = reference_date + publication_lag_days`); using the reference-date value on D is
    forbidden lookahead. `proxy_symbol` (optional) is the OHLCV `DailyPrice` proxy ticker (`^TNX`/`^DXY`/
    `^VXN`) the same series may also ride as a plain price bar. No key VALUE is ever stored here."""

    model_config = ConfigDict(extra="allow")
    id: str = Field(min_length=1)
    fred_series_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    publication_lag_days: int
    proxy_symbol: Optional[str] = None
    # the OPTIONAL severity-leg scaling (consumed ONLY when `macro.enable.severity`): the macro value is
    # scaled to a [0, 1] stress reading via `min(1, abs(value) / stress_gate)` and blended at `weight`
    # into the severity components (mirroring the ^VIX gate). Both default 0/None so an enabled leg with
    # no scaling configured contributes NOTHING (never a fabricated component); a configured `weight` must
    # be >= 0 and `stress_gate` (when present) must be positive. No magic number — every tunable is config.
    stress_gate: Optional[float] = None
    weight: float = 0.0

    @model_validator(mode="after")
    def _validate(self) -> "MacroSeriesCfg":
        if self.publication_lag_days < 0:
            raise ValueError(
                f"macro.series {self.id!r} publication_lag_days must be >= 0, got {self.publication_lag_days}"
            )
        if self.weight < 0:
            raise ValueError(f"macro.series {self.id!r} weight must be >= 0, got {self.weight}")
        if self.stress_gate is not None and self.stress_gate <= 0:
            raise ValueError(
                f"macro.series {self.id!r} stress_gate must be positive when set, got {self.stress_gate}"
            )
        return self


class MacroEnableCfg(BaseModel):
    """The per-leg config-default-OFF enable flags for the optional macro inputs (iter-32, J-92). Each leg
    is OFF by default, so with macro disabled every J-87..J-91 figure is byte-identical to the
    price/breadth/VIX-only path (the byte-identity-when-disabled keystone). Enabling a leg is a deliberate
    config edit — the default boot never changes a figure."""

    model_config = ConfigDict(extra="allow")
    severity: bool = False           # wire macro into the J-87 severity score
    regime_switching: bool = False   # wire macro into the J-88 regime-switching observation/emissions
    study: bool = False              # wire macro into the J-91 study conditioning


class MacroCfg(BaseModel):
    """The optional FRED macro-feed config (iter-32, J-92 — consumed by the macro provider + the
    config-default-OFF macro-conditioning legs). EVERY series id / publication-lag / enable flag lives here
    (anti-goal: No magic numbers). The FRED key is read FROM THE ENVIRONMENT ONLY via `env_var` (the NAME
    only — never a key VALUE here, in the DB, the run log, or any committed file).

      - `env_var` — the environment-variable NAME the FRED key is read from (the NAME only).
      - `series` — the configured macro series (id + FRED series id + publication lag + optional proxy).
      - `enable` — the per-leg config-default-OFF flags (severity / regime_switching / study).

    Boot-validated: unique series ids; unique non-null proxy symbols. Default-disabled with an empty series
    list is valid (the smallest config / the inline test fixtures need no macro block tuning)."""

    model_config = ConfigDict(extra="allow")
    env_var: str = Field(min_length=1)
    series: list[MacroSeriesCfg] = Field(default_factory=list)
    enable: MacroEnableCfg = Field(default_factory=MacroEnableCfg)

    @model_validator(mode="after")
    def _validate(self) -> "MacroCfg":
        ids = [s.id for s in self.series]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            raise ValueError(f"macro.series have duplicate ids: {dupes}")
        proxies = [s.proxy_symbol for s in self.series if s.proxy_symbol]
        proxy_dupes = sorted({p for p in proxies if proxies.count(p) > 1})
        if proxy_dupes:
            raise ValueError(f"macro.series have duplicate proxy_symbol values: {proxy_dupes}")
        return self

    def series_by_id(self, series_id: str) -> Optional["MacroSeriesCfg"]:
        """The configured series for `series_id`, or None when it is not configured."""
        return next((s for s in self.series if s.id == series_id), None)


def _default_macro() -> "MacroCfg":
    """The built-in default macro config (J-92) — used when a config predating the block (or an inline test
    fixture) omits `macro`. DEFAULT-OFF with NO configured series, so it changes no figure and adds no
    macro proxy; the real `config.yaml` supplies the env-var name + the series + (still default-off) legs."""
    return MacroCfg(env_var="FRED_API_KEY")


class Config(BaseModel):
    """Validated view of config.yaml. Only the iter-1-consumed sections are typed/validated;
    scaffolded sections ride along via extra="allow" so they can be tuned without code edits."""

    model_config = ConfigDict(extra="allow")

    provider: Literal["seed", "stooq"]
    database: DatabaseCfg
    data_manager: DataManagerCfg
    universe: UniverseCfg
    etfs: ETFsCfg
    index_chart: IndexChartCfg  # J-44 major-indexes chart symbols + display names + range presets
    themes: dict[str, list[str]] = Field(min_length=1)
    buckets: BucketsCfg
    indicators: IndicatorsCfg
    sectors: SectorsCfg
    regime: RegimeCfg
    scores: ScoresCfg
    theme_scores: ThemeScoresCfg
    decision_rules: DecisionRulesCfg
    stock_sectors: dict[str, str] = Field(min_length=1)
    # J-58: stock -> industry-group ETF membership (many-to-many, config-defined reference data, like
    # `themes`). Each key must be a universe symbol; each value ticker must be in `etfs.industry`. An
    # unmapped stock / ETF is allowed (renders an explicit empty state) — but a STRAY ticker is a loud
    # ConfigError (see `_stock_industries_valid`). Default-empty so a config predating it still loads.
    stock_industries: dict[str, list[str]] = Field(default_factory=dict)
    scanner: ScannerCfg
    startup: StartupCfg  # iter-28 (J-40/J-41) fast-ready boot + warm-up tunables (boot-validated above)
    # iter-42 (J-100) — bounded-resource server ops guards (uvicorn concurrency/timeout caps + the process
    # ulimit -v memory cap) the start script reads. Default-populated so a config/test fixture predating it
    # still loads unchanged and serves the documented bounds.
    server: ServerOpsCfg = Field(default_factory=ServerOpsCfg)
    walk_forward: WalkForwardCfg
    patterns: PatternsCfg
    methodology: MethodologyCfg
    research: ResearchCfg
    # iter-29 (J-87 / J-88) — the read-only Market Phase & Severity layer's typed/validated config:
    # the phase vocabulary + severity weights/thresholds (`market_phase`) and the deterministic 2-state
    # regime-switching params for the forward filtered P(bear) (`regime_switching`). Consumed VERBATIM by
    # `app.engine.market_phase`; no literal lives in that module.
    market_phase: MarketPhaseCfg
    regime_switching: RegimeSwitchingCfg
    # iter-32 (J-92) — the OPTIONAL FRED macro feed config (provider env-var name + per-series id +
    # publication-lag + the per-leg config-default-OFF enable flags). Defaults to a DEFAULT-OFF, no-series
    # block so a config predating it (and the inline test fixtures) still loads and changes no figure.
    macro: MacroCfg = Field(default_factory=_default_macro)

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
    def _stock_industries_valid(self) -> "Config":
        """J-58: every `stock_industries` key must be a universe symbol and every value ticker must be
        an `etfs.industry` catalog ticker — reference data validated like `themes`/`stock_sectors`,
        never a silent default. Unmapped stocks/ETFs are fine (explicit empty state); a STRAY ticker
        (a member not in universe, or an ETF not in the catalog) is a loud error."""
        universe = set(self.universe.symbols)
        industry_tickers = set(self.etfs.industry.keys())
        bad_keys = sorted(k for k in self.stock_industries if k not in universe)
        if bad_keys:
            raise ValueError(f"stock_industries keys not present in universe.symbols: {bad_keys}")
        bad_members = sorted(
            f"{stock}->{etf}"
            for stock, etfs in self.stock_industries.items()
            for etf in etfs
            if etf not in industry_tickers
        )
        if bad_members:
            raise ValueError(
                f"stock_industries values must be tickers in etfs.industry {sorted(industry_tickers)}; "
                f"invalid: {bad_members}"
            )
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

    @model_validator(mode="after")
    def _pattern_ma_period_is_an_indicator_period(self) -> "Config":
        """The pullback-to-rising-DMA detector's MA basis must be one of the configured
        `indicators.ma_periods`, so the DMA it pulls back to is an already-charted canonical MA — the
        SAME single source the chart overlay / invalidation / scoring use, never a second MA basis.
        Cross-checked here (not in the sub-model) because a sub-model cannot see `indicators` — exactly
        like the VCP/invalidation `ma_period` above."""
        period = self.patterns.pullback_to_rising_dma.ma_period
        if period not in self.indicators.ma_periods:
            raise ValueError(
                f"patterns.pullback_to_rising_dma.ma_period ({period}) must be one of "
                f"indicators.ma_periods ({self.indicators.ma_periods})"
            )
        return self

    @model_validator(mode="after")
    def _factor_lab_sources_resolve(self) -> "Config":
        """Every Factor-Lab factor `source` must resolve to a stored value at boot (anti-goal: No magic
        numbers / No fabricated data) — a typed `ScannerResult` score column, or a
        `<block>.components.<name>.raw` path whose `<name>` is a real component in `scores.<block>.weights`.
        An unresolvable source fails the boot loudly, never a silent default. Cross-checked here (not in
        the sub-model) because resolving a component source needs `scores` — exactly like the pattern/
        invalidation `ma_period` checks above."""
        block_weights = {
            "leadership": self.scores.leadership.weights,
            "entry_quality": self.scores.entry_quality.weights,
            "risk": self.scores.risk.weights,
        }
        bad: list[str] = []
        for factor in self.research.factor_lab.factors:
            try:
                parsed = parse_factor_source(factor.source)
            except ValueError as exc:
                bad.append(str(exc))
                continue
            if parsed["kind"] == "component" and parsed["name"] not in block_weights[parsed["block"]]:
                bad.append(
                    f"factor {factor.key!r} source component {parsed['name']!r} is not in "
                    f"scores.{parsed['block']}.weights"
                )
        if bad:
            raise ValueError("research.factor_lab unresolvable factor sources: " + "; ".join(bad))
        return self

    @model_validator(mode="after")
    def _methodology_refs_resolve(self) -> "Config":
        """Every methodology threshold `ref` must resolve to a live config value at boot — an
        unresolvable reference fails the boot loudly (anti-goal: No fabricated data — the glossary
        never shows a silent/placeholder threshold). This is the load-time half of the matching-config
        keystone served by `app.engine.methodology.build_catalog`."""
        unresolved: list[str] = []
        threshold_lists = [entry.thresholds for entry in self.methodology.entries]
        if self.methodology.universe_selection is not None:
            threshold_lists.append(self.methodology.universe_selection.thresholds)
        # J-47: glossary terms may cite config thresholds via the same `ref` mechanism — resolve them too.
        threshold_lists.extend(term.thresholds for term in self.methodology.terms)
        for thresholds in threshold_lists:
            for threshold in thresholds:
                if threshold.ref is not None:
                    try:
                        resolve_ref(self, threshold.ref)
                    except ConfigError:
                        unresolved.append(threshold.ref)
        if unresolved:
            raise ValueError(f"methodology threshold refs are unresolvable: {sorted(set(unresolved))}")
        return self


def _merge_committed_universe(data: dict, universe_json: Path) -> None:
    """Grow `universe.symbols` from the committed `universe.json` screen result — keeping ONE universe
    source (J-22/J-35).

    `config.yaml` ships a seed `universe.symbols` list; the offline screen and the on-demand `expand` job
    grow membership by writing `universe.json` (the canonical screen-pass artifact whose `members` are the
    names that PASSED the config screen — `universe_pool.csv` is `prior universe ∪ S&P 500 ∪ Nasdaq-100`,
    so a passing prior name is already among them). To keep the J-22 invariant `/api/data universe_count
    == /methodology resolved_size == len(config.universe.symbols)` TRUE BY CONSTRUCTION (all three read
    `len(universe.symbols)`), we resolve `universe.symbols` to the UNION of the YAML symbols and the
    artifact members, in-place on the parsed `data` before validation, and merge each new member's `sector`
    into `stock_sectors`.

    The UNION (not a replace) is deliberate: it lets the screen GROW the universe while never silently
    dropping a committed name out from under the config `themes` / `stock_sectors` that reference it (which
    would break boot validation) — so the merge is safe for ANY artifact content, and a grown universe is
    `base ∪ new screened passers`. This is a READ of the committed screen result (no recompute, no second
    computation) — consistent with the "universe membership comes from the config-recorded screen"
    anti-goal.

    Applied ONLY for the default config (see `load_config`) so alternate/inline test configs are never
    affected. A new member takes its sector from the artifact (the screen records each member's sector); a
    name already mapped keeps its YAML sector. Absent/unreadable/empty artifact ⇒ no-op (the YAML `symbols`
    stand — graceful fallback). Never fabricates a member or a sector."""
    if not universe_json.exists():
        return
    try:
        record = json.loads(universe_json.read_text())
    except (OSError, ValueError):
        return  # unreadable artifact → fall back to the YAML symbols (never crash the boot)
    members = record.get("members") if isinstance(record, dict) else None
    if not isinstance(members, list) or not members:
        return
    universe = data.get("universe")
    if not isinstance(universe, dict):
        return
    base_symbols = list(universe.get("symbols") or [])
    seen = set(base_symbols)
    new_sectors: dict[str, str] = {}
    grown = list(base_symbols)
    for member in members:
        if not isinstance(member, dict):
            continue
        sym = member.get("symbol")
        if not sym or sym in seen:
            continue
        seen.add(sym)
        grown.append(sym)
        sector = member.get("sector")
        if sector:
            new_sectors[sym] = sector
    if grown == base_symbols:
        return  # the artifact added no new member — nothing to merge
    universe["symbols"] = grown  # the universe = YAML base ∪ the committed screen passers (single source)
    stock_sectors = data.setdefault("stock_sectors", {})
    if isinstance(stock_sectors, dict):
        # the YAML mapping wins for an already-mapped name; a new member takes the artifact's sector so
        # `_stock_sectors_cover_universe` stays satisfied by construction (never a silent default).
        for sym, sector in new_sectors.items():
            stock_sectors.setdefault(sym, sector)


def load_config(path: Optional[str | Path] = None) -> Config:
    """Load + validate config.yaml. `path` overrides the default (repo-root config.yaml);
    the TRENDORA_CONFIG env var is honored when no explicit path is given (used by tests).

    For the DEFAULT config only, the committed `universe.json` (when present) becomes the single source of
    `universe.symbols` via `_merge_committed_universe` — so the J-22 single-source invariant holds by
    construction and the J-35 `expand` write naturally flows into `universe_count` + `/methodology`."""
    is_default = path is None and not os.environ.get("TRENDORA_CONFIG")
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
    if is_default:
        _merge_committed_universe(data, DEFAULT_UNIVERSE_JSON)
    try:
        return Config(**data)
    except ValidationError as exc:
        raise ConfigError(f"invalid config {path}:\n{exc}") from exc


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Process-wide cached config for the running app (not for tests that load alt configs)."""
    return load_config()
