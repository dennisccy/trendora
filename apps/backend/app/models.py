"""SQLModel tables.

The reference/universe tables, daily prices, and the data-quality log (iter-1) PLUS the
append-only scanner-snapshot tables (iter-5): `scanner_runs` and its child `scanner_results`,
`sector_scores`, `theme_scores`. Integer auto-increment PKs; dates stored ISO; engine URL comes
from config (Postgres-ready — no SQLite-only SQL).

IMMUTABILITY (anti-goal: Snapshots are immutable): the snapshot tables are APPEND-ONLY — once a
`ScannerRun` row and its children are written, no code path UPDATEs them. Forward returns (iter-6)
will live in a SEPARATE append-only table keyed to the snapshot (run_id, stock, horizon), so the
snapshot itself is never mutated. The `forward_returns`, `paper_portfolio*` tables remain
DESIGNED-but-not-created this session.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, Index, SQLModel, UniqueConstraint


class Sector(SQLModel, table=True):
    __tablename__ = "sectors"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    etf_ticker: str = Field(index=True)


class Industry(SQLModel, table=True):
    __tablename__ = "industries"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    sector_id: Optional[int] = Field(default=None, foreign_key="sectors.id")
    etf_ticker: Optional[str] = None


class Stock(SQLModel, table=True):
    __tablename__ = "stocks"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True, unique=True)
    name: Optional[str] = None
    sector_id: Optional[int] = Field(default=None, foreign_key="sectors.id")
    industry_id: Optional[int] = Field(default=None, foreign_key="industries.id")
    market_cap: Optional[float] = None
    is_common: bool = True
    active: bool = True


class ETF(SQLModel, table=True):
    __tablename__ = "etfs"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True, unique=True)
    name: Optional[str] = None
    kind: str  # index | sector | industry | volatility
    tracks_sector_id: Optional[int] = Field(default=None, foreign_key="sectors.id")
    tracks_industry_id: Optional[int] = Field(default=None, foreign_key="industries.id")


class Theme(SQLModel, table=True):
    __tablename__ = "themes"

    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(index=True, unique=True)
    name: str
    description: Optional[str] = None


class ThemeMember(SQLModel, table=True):
    __tablename__ = "theme_members"

    id: Optional[int] = Field(default=None, primary_key=True)
    theme_id: int = Field(foreign_key="themes.id", index=True)
    stock_id: int = Field(foreign_key="stocks.id", index=True)
    category_tag: Optional[str] = None


class DailyPrice(SQLModel, table=True):
    __tablename__ = "daily_prices"
    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_daily_prices_symbol_date"),
        Index("ix_daily_prices_symbol_date", "symbol", "date"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float  # split/dividend-adjusted (the committed seed is pre-adjusted)
    volume: float  # raw (unadjusted) share volume


class DataProviderRun(SQLModel, table=True):
    __tablename__ = "data_provider_runs"

    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    symbols_ok: int = 0
    symbols_failed: int = 0
    status: str  # ok | partial | failed
    message: Optional[str] = None


# --- iter-5 scanner snapshots (APPEND-ONLY — never updated after creation) -------------------
class ScannerRun(SQLModel, table=True):
    """One immutable scan snapshot for an as-of date. `asof_date` is unique — there is exactly
    ONE run per date (idempotent re-creation from the frozen seed yields the same content). The
    regime/breadth/candidate-count fields are STORED COPIES of the canonical engine outputs read
    once at scan time (single source — never recomputed when served)."""

    __tablename__ = "scanner_runs"

    id: Optional[int] = Field(default=None, primary_key=True)
    asof_date: date = Field(index=True, unique=True)
    created_at: datetime
    provider: str
    benchmark: str
    regime_score: float
    regime_label: str
    regime_components_json: str
    breadth_above_50dma: Optional[float] = None  # universe-relative; NA when insufficient history
    breadth_above_200dma: Optional[float] = None
    new_high_low_json: str
    candidate_counts_json: str


class ScannerResult(SQLModel, table=True):
    """One stored per-stock result within a run. Typed columns mirror the canonical `StockRow`
    for ordering/filtering/immutability checks; `record_json` holds the COMPLETE `score_stocks`
    row dict (three score blocks + components, setup+reason, themes, invalidation) for lossless
    detail. The detail page rehydrates the `StockRow` from `record_json`."""

    __tablename__ = "scanner_results"

    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="scanner_runs.id", index=True)
    ticker: str = Field(index=True)
    name: str
    sector: Optional[str] = None
    leadership_score: float
    leadership_bucket: str
    entry_quality_score: float
    entry_quality_bucket: str
    risk_score: float
    risk_bucket: str
    setup_status: str = Field(index=True)
    rank: int
    record_json: str  # complete canonical score_stocks row dict (lossless)


class SectorScoreRow(SQLModel, table=True):
    """One stored sector/industry leadership row within a run (a stored copy of the canonical
    `SectorRow` shape from `score_sectors`)."""

    __tablename__ = "sector_scores"

    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="scanner_runs.id", index=True)
    ticker: str
    kind: str  # sector | industry
    name: str
    score: float
    bucket: str
    rs_vs_spy: Optional[float] = None
    dist_from_52w_high_pct: Optional[float] = None
    trend_label: str
    components_json: str
    rank: int


class ThemeScoreRow(SQLModel, table=True):
    """One stored theme leadership row within a run (a stored copy of the canonical `ThemeRow`
    shape from `score_themes`)."""

    __tablename__ = "theme_scores"

    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="scanner_runs.id", index=True)
    slug: str
    name: str
    score: float
    bucket: str
    members_json: str
    return_1m: Optional[float] = None
    return_3m: Optional[float] = None
    breadth_pct: Optional[float] = None
    breadth_label: str
    trend_label: str
    components_json: str
    rank: int
