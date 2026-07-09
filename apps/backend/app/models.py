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
    # iter-24 fast-platform item C: the explicit `ix_daily_prices_symbol_date` index that used to live
    # here was a byte-for-byte DUPLICATE of the index SQLite already builds for the `UniqueConstraint`
    # below (a second index write on every bar insert, no query-plan benefit) — removed. A live DB still
    # carrying it from an older model version has it swept by the guarded `app.db._ensure_index_hygiene`
    # startup step (DROP INDEX IF EXISTS), which also ADDS `ix_daily_prices_date` (a date-only index:
    # `func.max(DailyPrice.date)` and the coverage/availability `group_by(date)` scans read it, and it is
    # NOT covered by the (symbol, date) unique index, whose leading column is symbol).
    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_daily_prices_symbol_date"),
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
    # iter-29 (J-60): the lifecycle is now `running` → ONE honest terminal transition. A job's run-history
    # record is created at START (status `running`, no finished_at) and the SAME row is UPDATEd exactly once
    # to its terminal state — `ok` | `partial` | `failed`, or `interrupted` (applied by the boot sweep to a
    # `running` row whose process is gone). A rate-limited pause does NOT write a terminal run (the durable
    # checkpoint carries `resumable`); the eventual completed resume writes its own record. This is the SAME
    # single lifecycle the job card / Run history / Unfinished-imports read — never a second bookkeeping path.
    status: str  # running | ok | partial | failed | interrupted
    message: Optional[str] = None
    # iter-25 (J-38) soft-dismiss flag for the unified Unfinished-imports panel. A MUTABLE job-control
    # column on this already-mutable operational table — NOT a new table and NOT a snapshot column. When
    # an operator Dismisses an unfinished (partial/failed) run, this flips True so the run stops being
    # OFFERED as actionable in `unfinished_imports`; the row itself is NEVER deleted/hidden from the
    # append-only Run-history audit (the run still appears there). The immutable snapshot/forward-return
    # rows are untouched. Append-only column addition — a fresh DB carries it (default False) from start.
    dismissed: bool = Field(default=False)
    # iter-29 (J-60): the in-memory `JobProgress.job_id` of the data-manager job that owns this run-history
    # record, so the create-at-start row can be looked up and UPDATEd at the terminal transition (one row,
    # one job). NULL for a plain seed-load row and for legacy rows written before this column. It is a
    # job-control correlation id — NEVER a key (anti-goal: keys are env-or-session, never persisted).
    # Append-only column addition — a fresh DB carries it (default None) from start.
    job_id: Optional[str] = Field(default=None, index=True)


class ImportCheckpoint(SQLModel, table=True):
    """Durable, MUTABLE job-control state for a chunked live import (iter-22, J-34).

    This is EXPLICITLY NOT a scanner snapshot — coherence invariant #3 (Snapshots are immutable) binds
    ONLY `scanner_runs` / `scanner_results` / `*_scores` / `forward_returns`; like `data_provider_runs`
    (and the in-memory `JobProgress`), `import_checkpoints` is legitimately mutable job-control state and
    is freely UPDATEd as chunks complete. It records a chunked fetch's resumable progress so a
    rate-limited (429) import survives a backend restart and can be RESUMED from the next un-fetched
    chunk. The fetched bars themselves still flow ONLY through the existing canonical INSERT-new-only
    `DailyPrice` path (`_existing_dates` guard), so per-`(symbol, date)` idempotency holds and a
    committed bar is NEVER overwritten — no snapshot is mutated.

    `import_id` is the SAME id as the live `JobProgress.job_id`, so one id threads both the in-memory
    job and its durable checkpoint (and the Resume endpoint / `resumable_imports` list).

    NO key value is EVER stored here (anti-goal: Import keys are env-or-session, never persisted) — there
    is deliberately no key column; the session-only `api_key` re-supplied to Resume is request-only.

      - `next_chunk_index` is the index to resume from — advanced ONLY after a chunk fully completes.
      - `symbol_plan_json` is the deterministic ordered symbol list the chunk plan was built from, so a
        resume rebuilds the SAME plan even if the live universe later changes.
      - `status` ∈ running | resumable | ok | failed | failed_backfill (only `resumable` and
        `failed_backfill` rows appear in the unfinished-imports / Resume surfaces).

    iter-29 (J-59) STAGE-AWARENESS: `completed_stages_json` records which pipeline stages
    (`fetch` / `screen` / `backfill`) have COMPLETED, so a job that failed or was interrupted AFTER a
    completed fetch is **resumable from the backfill stage with zero provider calls** (the fetch stage is
    skipped entirely on Resume). It is a JSON list of stage names — append-only within a job, MUTABLE
    job-control state (NOT a snapshot). A `failed_backfill` status with `fetch` in `completed_stages`
    drives the "failed at backfill — resumable from the backfill stage" Unfinished-imports row. The column
    defaults to "[]" so a legacy/fresh row reads an empty stage set (pre-stage behavior — fetch re-runs),
    never a crash. NO key value is EVER stored here.
    """

    __tablename__ = "import_checkpoints"

    id: Optional[int] = Field(default=None, primary_key=True)
    import_id: str = Field(index=True, unique=True)  # == the live JobProgress.job_id (threads both)
    source: str
    kind: str
    start: date
    end: date
    symbol_plan_json: str  # deterministic ordered symbol list the chunk plan was built from
    chunk_total: int
    next_chunk_index: int = 0  # resume point — advanced ONLY after a chunk fully completes
    symbols_ok: int = 0
    symbols_failed: int = 0
    bars_fetched: int = 0
    status: str = "running"  # running | resumable | ok | failed | failed_backfill (NO key column)
    # iter-29 (J-59): the JSON list of COMPLETED pipeline stages (fetch / screen / backfill). Drives the
    # zero-provider-call resume-at-backfill path. Append-only within a job; MUTABLE job-control state, NOT
    # a snapshot. Defaults to "[]" so a fresh/legacy row reads an empty stage set (no crash).
    completed_stages_json: str = "[]"
    created_at: datetime
    updated_at: datetime


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
    # J-58: config reference metadata, STORED ONCE at run_scan time into this immutable snapshot row
    # (the stored-copy pattern already on ThemeScoreRow) and served verbatim by /api/sectors — never
    # recomputed in the read path. `description` is NULL-able (None for sector ETFs and for a stored
    # run predating the column → the row still renders its ticker/name honestly). `members_json` is the
    # JSON-encoded universe-member list (empty list → explicit UI empty state; never fabricated). It
    # defaults to "[]" so a row constructed/read without it renders the honest empty state, not a crash.
    description: Optional[str] = None
    members_json: str = "[]"
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
    (`app.engine.research.compute_event_study`) — never recomputed in the read path.

    `max_drawdown` (iter-27, J-86) is the NEW append-only post-snapshot MAXIMUM-DRAWDOWN column — the
    worst peak-to-trough decline over the FIRST `horizon` post-snapshot bars (date > D, via
    `bars_after`): `MDD = min over j of ( low_j / max(entry_close, high_1..high_j) - 1 )` with the
    running peak seeded at the as-of-D `entry_close` — a true peak-to-trough drop (<= 0). Computed
    ONCE in the SAME `_insert_run_forward_returns` INSERT path via the pure `max_drawdown` helper,
    which shares the EXACT no-lookahead NA gate as `forward_return`/`forward_excursions` (so a row's
    `max_drawdown` is non-None iff `realized_return` exists — `< horizon` post-bars yields NO row,
    never a fabricated 0). Forward-side only — no snapshot row is ever UPDATEd. `Optional[float]`,
    default `None` (backward-compatible; a fresh frozen-seed DB carries it from the start; an existing
    live DB gains it via the `db._ADDITIVE_COLUMNS` ALTER). Read VERBATIM by the read path
    (`/api/stocks`, `/api/stocks/{ticker}`, `/api/themes`, `/api/sectors`) and aggregated read-only by
    Backtest + the Research event study — never recomputed when served."""

    __tablename__ = "forward_returns"
    # iter-24 fast-platform item C: the explicit `ix_forward_returns_run_symbol` index that used to live
    # here was a redundant PREFIX of the `UniqueConstraint` below (any `run_id`-leading query the prefix
    # served, the unique index already serves) — removed. A live DB still carrying it from an older model
    # version has it swept by the guarded `app.db._ensure_index_hygiene` startup step (DROP INDEX IF
    # EXISTS). The single-column `run_id`/`symbol` indexes below (from `Field(index=True)`) are NOT
    # prefixes of this 3-column unique index (a lone `symbol` filter across every run needs its own
    # index) and stay untouched.
    __table_args__ = (
        UniqueConstraint("run_id", "symbol", "horizon", name="uq_forward_returns_run_symbol_horizon"),
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
    # iter-27 (J-86) append-only max-drawdown column — the worst peak-to-trough decline over the first
    # `horizon` post-snapshot bars: min_j( low_j / max(entry_close, high_1..high_j) - 1 ), <= 0.
    # Computed once with realized_return, same no-lookahead NA gate; None on short history. Read verbatim
    # by the stocks/themes/sectors/detail read path and aggregated read-only by Backtest + Research.
    max_drawdown: Optional[float] = Field(default=None)  # true peak-to-trough drawdown over first h post-bars (<= 0)


# --- iter-20 event-study derived-aggregate cache (J-72 — a PERFORMANCE cache, not a snapshot) -----
class EventStudyCache(SQLModel, table=True):
    """A STANDALONE, create_all-managed cache of the derived event-study aggregate (J-72).

    This is EXPLICITLY NOT a scanner snapshot — the *Snapshots are immutable* critical anti-goal binds
    ONLY `scanner_runs` / `scanner_results` / `*_scores` / `forward_returns`. Like `data_provider_runs`
    and `import_checkpoints`, this is legitimately mutable derived/cache state: it stores the SERIALIZED
    `compute_event_study(...)` payload (the figures are BYTE-IDENTICAL to a fresh compute — a cache of the
    deterministic read-only aggregation, never a second computation or a hand-authored value) keyed by the
    analysis identity + a dataset-version stamp, so a read serves the stored aggregate instead of
    re-deriving it per request (No recompute in the read path / the "derived once… persisted/cached, read
    from storage" contract the as-of evidence aggregate already follows).

    A STANDALONE table (its own `create_all`-managed table) is used deliberately so the iter-12
    `_ADDITIVE_COLUMNS` trap does NOT apply — a fresh DB carries it from `create_db_and_tables`, and no
    existing table gains a column.

    CACHE KEY: `(subject, view, asof_key, dataset_version)`:
      - `subject` / `view` are the analysis identity; `asof_key` is the resolved as-of cutoff ISO date or
        the literal "all" sentinel for the all-history aggregate (so all-history and as-of-scoped reads
        never collide).
      - `dataset_version` is a stamp derived from the stored state (e.g. max run id + the forward-return
        row count) that CHANGES whenever the dataset changes (a backfill adds snapshots/returns, or a
        removal deletes them). A read computes the current stamp and looks up THIS exact key — a stale row
        keyed to an older stamp is simply never hit (and is pruned), so the cache can NEVER serve a stale
        figure (it refreshes after any dataset change).

    `payload_json` is the full serialized aggregate; `horizon` is part of the cached payload (one row per
    (subject, view, asof_key, dataset_version) holds the ALL-horizons payload, re-pointed client-side by
    the horizon selector — matching how `compute_event_study` returns every horizon's row), so the cache
    is keyed independent of the requested horizon. Unique on the composite key so a write is an idempotent
    upsert."""

    __tablename__ = "event_study_cache"
    __table_args__ = (
        UniqueConstraint(
            "subject", "view", "asof_key", "dataset_version", "horizon",
            name="uq_event_study_cache_key",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    subject: str = Field(index=True)
    view: str
    asof_key: str  # resolved as-of ISO date, or the "all" sentinel for all-history
    dataset_version: str  # stamp derived from stored state; changes on any dataset change
    horizon: int  # the requested horizon echoed into the key (the payload still carries every horizon)
    payload_json: str  # the serialized compute_event_study(...) aggregate (byte-identical to a fresh compute)
    created_at: datetime


# --- iter-29 market-phase derived-aggregate cache (J-87 / J-88 — a PERFORMANCE cache, not a snapshot) ---
class MarketPhaseCache(SQLModel, table=True):
    """A STANDALONE, create_all-managed cache of the derived Market Phase & Severity layer (J-87 / J-88).

    Like `EventStudyCache`, this is EXPLICITLY NOT a scanner snapshot — the *Snapshots are immutable*
    critical anti-goal binds ONLY `scanner_runs` / `scanner_results` / `*_scores` / `forward_returns`.
    This is legitimately mutable derived/cache state: it stores the SERIALIZED `compute_market_phase(...)`
    payload (phase label + 0-100 severity + named component breakdown + forward FILTERED P(bear) + the
    observation vector) keyed by the resolved as-of cutoff + a dataset-version stamp, so a read serves the
    stored aggregate instead of re-deriving it per request (No recompute in the read path). The cached
    figures are BYTE-IDENTICAL to a fresh compute — a cache of the deterministic read-only derivation,
    never a second computation.

    A STANDALONE table (its own `create_all`-managed table) is used deliberately so the iter-12
    `_ADDITIVE_COLUMNS` trap does NOT apply — a fresh DB carries it from `create_db_and_tables`, and no
    existing table gains a column.

    CACHE KEY: `(asof_key, dataset_version)`:
      - `asof_key` is the resolved as-of cutoff ISO date (the single global as-of the read resolved to).
      - `dataset_version` is the SAME stamp `app.engine.research._dataset_version` produces (single-sourced
        with J-72 — derived from max run id + the forward-return row count), so the layer's cache
        invalidates in lockstep with the event-study cache: a read computes the current stamp and looks up
        THIS exact key; a stale row keyed to an older stamp is never hit (and is pruned on write), so the
        cache can NEVER serve a stale figure (it refreshes after any dataset change).

    `payload_json` is the full serialized derivation. Unique on the composite key so a write is an
    idempotent upsert."""

    __tablename__ = "market_phase_cache"
    __table_args__ = (
        UniqueConstraint("asof_key", "dataset_version", name="uq_market_phase_cache_key"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    asof_key: str = Field(index=True)  # resolved as-of ISO cutoff date (the single global as-of)
    dataset_version: str  # the SAME stamp research._dataset_version produces; changes on any dataset change
    payload_json: str  # the serialized compute_market_phase(...) derivation (byte-identical to a fresh compute)
    created_at: datetime


class MacroSeries(SQLModel, table=True):
    """A STANDALONE, create_all-managed table of optional FRED macro-feed observations (iter-32, J-92).

    Like `EventStudyCache` / `MarketPhaseCache`, this is EXPLICITLY NOT a scanner snapshot — the
    *Snapshots are immutable* critical anti-goal binds ONLY `scanner_runs` / `scanner_results` /
    `*_scores` / `forward_returns`. This is a separate, additive macro store: one row per (`symbol`,
    `date`) macro observation, carrying its raw `value`, the `source` it came from (e.g. `fred` /
    `seed`), and the `published_date` — the calendar date the value first became publicly available
    (`published_date = reference_date + publication_lag_days`). A macro value is usable for a causal
    date D ONLY when `published_date <= D` (using the reference-date value on D is forbidden lookahead);
    the macro-conditioning legs read with that publication-lag filter.

    A STANDALONE table (its own `create_all`-managed table) is used deliberately so the iter-12
    `_ADDITIVE_COLUMNS` trap does NOT apply — a fresh DB carries it from `create_db_and_tables`, and no
    existing table gains a column. (The `^TNX`/`^DXY`/`^VXN` OHLCV macro PROXIES ride the EXISTING
    `daily_prices` table as plain bars — no schema change there.)

    Macro ships config-default-OFF: with no macro rows here (or every leg disabled) every J-87..J-91
    figure is byte-identical to the price/breadth/VIX-only path. A walled/uncommitted series simply has
    no rows → honest blocked-NA, never a fabricated value.

      - `symbol` is the internal macro series id (a `config.macro.series[*].id` — e.g.
        `yield_curve_10y2y`), NOT the OHLCV proxy ticker.
      - unique on (`symbol`, `date`) so a re-fetch is an idempotent upsert; indexed by
        (`symbol`, `date`) for the per-series causal read."""

    __tablename__ = "macro_series"
    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_macro_series_symbol_date"),
        Index("ix_macro_series_symbol_date", "symbol", "date"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str  # the internal macro series id (config.macro.series[*].id)
    date: date  # the macro value's reference date (the observation date)
    value: float  # the raw macro value, read verbatim (never fabricated)
    source: str  # where the value came from (e.g. "fred" / "seed") — provenance only, no key VALUE
    published_date: date  # the date the value became public (reference_date + publication_lag); causal gate


# --- iter-36 membership-timeline derived-aggregate cache (J-96 — a PERFORMANCE cache, not a snapshot) ---
class MembershipTimelineCache(SQLModel, table=True):
    """A STANDALONE, create_all-managed cache of the J-96 dynamic-universe membership timeline.

    Like `EventStudyCache` / `MarketPhaseCache`, this is EXPLICITLY NOT a scanner snapshot — the
    *Snapshots are immutable* critical anti-goal binds ONLY `scanner_runs` / `scanner_results` /
    `*_scores` / `forward_returns`. This is legitimately mutable derived/cache state: it stores the
    SERIALIZED `data_manager._membership_timeline(...)` payload (the per-snapshot-date resolved-size step
    function + entries/exits + per-date excluded-by-reason counts + the three honesty labels) keyed by a
    single dataset-version stamp, so a read serves the stored timeline instead of re-deriving it per
    request (No recompute in the read path). The cached payload is BYTE-IDENTICAL to a fresh
    `_membership_timeline(...)` compute — a cache of the deterministic read-only derivation, never a
    second computation or a hand-authored value.

    WHY: on the post-rebuild DB (~1369 sliding snapshot dates) the uncached derivation runs an
    O(dates × pool) `resolve_with_reasons` loop per `GET /api/data` and made the endpoint hang >300 s
    (the iter-35 regression). The cache (warmed off the boot path by the background warm-up daemon) makes
    the served VALUES byte-identical while the endpoint returns promptly.

    A STANDALONE table (its own `create_all`-managed table) is used deliberately so the iter-12
    `_ADDITIVE_COLUMNS` trap does NOT apply — a fresh DB carries it from `create_db_and_tables`, and no
    existing table gains a column.

    CACHE KEY: `(dataset_version)`:
      - `dataset_version` is the SAME stamp `app.engine.research._dataset_version` produces (single-sourced
        with J-72 / J-87 — derived from max run id + the forward-return row count), so this cache
        invalidates in lockstep with the event-study + market-phase caches: a read computes the current
        stamp and looks up THIS exact stamp; a stale row keyed to an older stamp is never hit (and is
        pruned on write), so the cache can NEVER serve a stale timeline (it refreshes after any dataset
        change). The timeline spans the WHOLE history (not an as-of slice), so there is no `asof_key` slot
        — exactly one row per dataset version.

    `payload_json` is the full serialized timeline. Unique on `dataset_version` so a write is an
    idempotent upsert."""

    __tablename__ = "membership_timeline_cache"
    __table_args__ = (
        UniqueConstraint("dataset_version", name="uq_membership_timeline_cache_key"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_version: str = Field(index=True)  # the SAME stamp research._dataset_version produces
    payload_json: str  # the serialized _membership_timeline(...) derivation (byte-identical to a fresh compute)
    created_at: datetime


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
