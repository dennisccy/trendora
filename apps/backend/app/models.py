"""SQLModel tables.

The reference/universe tables, daily prices, and the data-quality log (iter-1) PLUS the
append-only scanner-snapshot tables (iter-5): `scanner_runs` and its child `scanner_results`,
`sector_scores`, `theme_scores`. Integer auto-increment PKs; dates stored ISO; engine URL comes
from config (Postgres-ready — no SQLite-only SQL).

IMMUTABILITY (anti-goal: Snapshots are immutable): the snapshot tables are APPEND-ONLY — once a
`ScannerRun` row and its children are written, no code path UPDATEs them. Forward returns (iter-6)
live in a SEPARATE append-only table `forward_returns`, keyed to the snapshot (run_id, symbol,
horizon), so the snapshot itself is never mutated — the walk-forward engine only INSERTs realized
post-snapshot returns there, never touching a `scanner_runs` / `scanner_results` / `*_scores` row.
The `paper_portfolio*` tables remain DESIGNED-but-not-created this session.
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
    row dict (three score blocks + components, setup+reason, themes, invalidation, the VCP block)
    for lossless detail. The detail page rehydrates the `StockRow` from `record_json`.

    `is_vcp` (iter-11) is the denormalized typed MIRROR of `record_json`'s `vcp.flagged` — written
    once in the SAME `run_scan` transaction, exactly as `leadership_bucket` / `setup_status` already
    mirror the record (NOT a second source/computation; one `detect_vcp` call per run). It exists only
    so the forward-test `by_vcp` grouping can read it verbatim like `by_setup` / `by_bucket`; the full
    `vcp` block (reason / pivot / invalidation / contractions) stays in `record_json`. It is an
    APPEND-only column addition — no existing snapshot row is ever UPDATEd (anti-goal: Snapshots
    immutable); a fresh DB re-created from the frozen seed carries it from the start.

    `is_pullback_to_rising_dma` / `is_flat_base_breakout` (iter-9) are the SAME design for the two new
    detected patterns: each is the denormalized mirror of `record_json`'s `<name>.flagged`, written
    once from the single detector output per run, so the forward-test `by_<name>` grouping reads it
    verbatim. The full pattern blocks ride losslessly in `record_json`; the mirrors are only the fast
    grouping flags. Append-only column additions — the frozen-seed DB carries them from the start.

    `hv` / `vcp_contraction` / `downside_vol` (iter-13, J-30) are the three NEW volatility-family factor
    values — the denormalized typed mirror of `record_json`'s same-named keys, each computed ONCE per run
    in `score_stocks` from the as-of bars (date <= D, no lookahead) and STORED here so the read-only
    Factor Lab can read them VERBATIM (the SAME computed-once-stored-then-read pattern the score columns
    follow). They are `Optional[float]` because short-history stocks have NA volatility — a NULL is
    honestly EXCLUDED by the lab, never bucketed/fabricated. They are STORED FOR LAB CONSUMPTION ONLY and
    enter NO weighted score (deliberately absent from every `scores.<block>.weights`), so every stock's
    Leadership/Entry/Risk score, bucket, setup status, and the Risk-Off→Actionable gate are byte-identical
    with these columns present. Append-only additions — a fresh frozen-seed DB carries them from the start."""

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
    is_vcp: bool = Field(default=False, index=True)  # mirror of record_json's vcp.flagged (iter-11)
    # iter-9 mirrors of record_json's <name>.flagged for the two new detected patterns (same design as
    # is_vcp; one detector call per run, never recomputed — only the fast forward-test grouping flag).
    is_pullback_to_rising_dma: bool = Field(default=False, index=True)
    is_flat_base_breakout: bool = Field(default=False, index=True)
    # iter-13 (J-30) volatility-family factor values — stored for the read-only Factor Lab only; NOT a
    # score input. NULL on short history (honestly excluded by the lab, never fabricated).
    hv: Optional[float] = Field(default=None)
    vcp_contraction: Optional[float] = Field(default=None)
    downside_vol: Optional[float] = Field(default=None)


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


# --- iter-6 walk-forward forward returns (SEPARATE append-only table — the snapshot is NEVER
# mutated; anti-goals: No lookahead + Snapshots are immutable) -------------------------------
class ForwardReturn(SQLModel, table=True):
    """One realized forward return: the return of `symbol` over `horizon` trading days measured
    from the close ON a run's `asof_date` (D, via `bars_asof`) to the close of the h-th POST-snapshot
    bar (date > D, via `bars_after`). INSERT-only and keyed to the immutable snapshot by `run_id`,
    so persisting forward returns never UPDATEs a `scanner_runs` / `scanner_results` / `*_scores`
    row. Unique on (run_id, symbol, horizon) — exactly one realized return per snapshot/symbol/horizon
    (idempotent re-backfill inserts no duplicate).

    `symbol` covers BOTH universe stocks and the benchmark ETFs (SPY, QQQ, the 11 sector ETFs) so
    excess-vs-benchmark is a stored subtraction. `realized_return` is the stored value
    (`measured_close / entry_close - 1`); `entry_close` (close on D), `asof_date` (D) and
    `measured_date` (the h-th post-bar's date) are kept for auditability. A (symbol, horizon) with
    fewer than `horizon` post-snapshot bars yields NO row (n=0) — never a fabricated/zero return.

    `mae` / `mfe` (iter-14, J-29) are the NEW append-only post-snapshot excursion columns — the max
    ADVERSE excursion (`min(low_i)/entry_close - 1`, <= ~0) and max FAVORABLE excursion
    (`max(high_i)/entry_close - 1`, >= ~0) over the FIRST `horizon` post-snapshot bars (date > D,
    via `bars_after`), computed ONCE in the SAME `_insert_run_forward_returns` INSERT path via the
    pure `forward_excursions` helper, which shares the EXACT no-lookahead NA gate as `forward_return`
    (so a row exists iff `realized_return` does — `< horizon` post-bars yields NO row, never a
    fabricated excursion). They are forward-side only: no `scanner_runs`/`scanner_results`/`*_scores`
    row is ever UPDATEd. `Optional[float]` so they are backward-compatible (default `None`); a fresh
    frozen-seed DB carries them from the start. Read VERBATIM only by the read-only event study
    (`app.engine.research.compute_event_study`) — never recomputed in the read path."""

    __tablename__ = "forward_returns"
    __table_args__ = (
        UniqueConstraint("run_id", "symbol", "horizon", name="uq_forward_returns_run_symbol_horizon"),
        Index("ix_forward_returns_run_symbol", "run_id", "symbol"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="scanner_runs.id", index=True)
    symbol: str = Field(index=True)  # universe stock OR benchmark ETF (SPY / QQQ / sector ETF)
    horizon: int  # forward window in trading days (from config.walk_forward.horizons)
    asof_date: date  # the run's as-of date D (close on D is the entry) — auditable context
    entry_close: float  # close ON asof_date (date <= D)
    measured_date: date  # date of the h-th post-snapshot bar (date > D) the return is measured to
    realized_return: float  # measured_close / entry_close - 1 (stored so excess is a subtraction)
    # iter-14 (J-29) append-only post-snapshot excursion columns — computed once with realized_return,
    # same no-lookahead NA gate; None on short history. Read verbatim by the read-only event study.
    mae: Optional[float] = Field(default=None)  # max adverse excursion: min(low)/entry_close - 1 (<= ~0)
    mfe: Optional[float] = Field(default=None)  # max favorable excursion: max(high)/entry_close - 1 (>= ~0)


# --- iter-7 watchlist (USER-MUTABLE — the product's FIRST user-write surface; J-11) ----------
class Watchlist(SQLModel, table=True):
    """One user-saved stock on the persistent research watchlist (iter-7). The product's FIRST
    user-mutable table — INSERT on add, DELETE on remove — and the entry survives a backend restart
    because it is DB-backed (the J-11 crux), not an in-memory dict/module global.

    This is explicitly NOT a snapshot table: no code path UPDATEs/INSERTs/touches a `scanner_runs` /
    `scanner_results` / `*_scores` / `forward_returns` row, so the *Snapshots-immutable* critical
    anti-goal is unaffected. It is also NOT an order/position — it carries no quantity, cost-basis,
    P&L, or order field; a research save-list only (*No order/execution path*, critical).

    It stores ONLY user/identity + entry-price-capture columns — NEVER any score / bucket / setup /
    invalidation. Those *current* values are READ LIVE at serve time from the canonical
    `app.engine.scoring.score_stocks` row (the SAME computation `/api/stocks` serves) and taken
    verbatim, so the watchlist can never become a second, drifting source (*Single source of truth*
    → J-06 on a write surface). This parallels how `ForwardReturn` stores a captured `entry_close`
    with no score.
      - `ticker` is unique — exactly one entry per ticker (a duplicate add is rejected, never duplicated).
      - `created_at` is the wall-clock "date added"; `asof_date_added` is the canonical
        `latest_data_date()` at add time; `entry_close` is the canonical close ON `asof_date_added`
        (captured once via `app.engine.prices.close_on`) so price-since-added is an honest realized
        figure (NA when `entry_close` is null — never fabricated).
    """

    __tablename__ = "watchlist"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True, unique=True)  # one entry per ticker
    reason: str  # free-text user note
    created_at: datetime  # wall-clock "date added"
    asof_date_added: date  # latest_data_date() captured at add time
    entry_close: Optional[float] = None  # canonical close on asof_date_added (None ⇒ price-since-added NA)
