"""SQLModel tables — iter-1 subset ONLY.

Exactly the eight tables this iteration exercises: the reference/universe tables, daily
prices, and the data-quality log. The snapshot / score / forward-return / watchlist tables
(design doc Section 5) are DEFERRED to their iterations and intentionally not defined here,
so `create_all()` produces exactly this set. Integer auto-increment PKs; dates stored ISO;
engine URL comes from config (Postgres-ready — no SQLite-only SQL).
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
