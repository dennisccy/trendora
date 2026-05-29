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
