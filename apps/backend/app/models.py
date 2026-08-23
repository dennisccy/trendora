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
    # goal-market-compass iter-3 (J-05/J-06): the engine-code + config identity stamp
    # (`app.engine.engine_identity.compute_engine_identity`), written ONCE at persist time by
    # `scanner.persist_run_payload` — an ADDITIVE nullable column (`db._ADDITIVE_COLUMNS`). An existing
    # pre-iter-3 row stays NULL forever ("pre-stamping era" — never backfilled); only NEWLY created runs
    # carry a stamp. Read (never recomputed) by the next-session manifest freeze writer's read-time basis
    # disclosure (compares this against the manifest's own frozen `generation.engine_identity`).
    engine_identity: Optional[str] = Field(default=None)


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
    Backtest + the Research event study — never recomputed when served.

    `underwater_days` / `time_to_recover_days` (iter-41, J-25) are the NEW append-only "dry spell" columns —
    the count of the FIRST `horizon` post-snapshot bars (date > D, via `bars_after`) whose close sits below
    the RUNNING high-water mark (seeded at the as-of-D `entry_close`, the SAME running-peak convention
    `max_drawdown` uses), and the number of bars from the max-drawdown trough until the close first returns
    to the entry level within the horizon (NA — never a fabricated horizon-sentinel — if it never recovers
    in-window). Both are computed ONCE in the SAME `_insert_run_forward_returns` INSERT path via the pure
    `underwater_days` / `time_to_recover_days` helpers, sharing the EXACT no-lookahead NA gate as
    `forward_return`/`max_drawdown` (`underwater_days` is non-None iff `realized_return` exists;
    `time_to_recover_days` is additionally None within an existing row when no recovery occurs in-window —
    never a fabricated value). Forward-side only — no snapshot row is ever UPDATEd. `Optional[int]`, default
    `None` (backward-compatible; a fresh frozen-seed DB carries them from the start; an existing live DB
    gains them via the `db._ADDITIVE_COLUMNS` ALTER). Read VERBATIM by
    `app.engine.forward_testing.compute_drawdown_expectations` — never recomputed when served."""

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
    # iter-41 (J-25) append-only "dry spell" columns — days below the running high-water mark, and days from
    # the max-drawdown trough back to the entry level (None if never recovered in-window). Computed once with
    # realized_return, same no-lookahead NA gate; None on short history. Read verbatim by
    # compute_drawdown_expectations (the /evidence expectations panel) — never recomputed elsewhere.
    underwater_days: Optional[int] = Field(default=None)  # bars below the running high-water mark, first h post-bars
    time_to_recover_days: Optional[int] = Field(default=None)  # bars from the MDD trough to entry-level recovery (NA if none)


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


# --- ops-hardening iter-5 (J-06) forward-aggregate derived-cache ---------------------------------
class ForwardAggregateCache(SQLModel, table=True):
    """A STANDALONE, create_all-managed cache of the derived per-horizon forward-return aggregate
    (`app.engine.forward_testing.compute_forward_aggregates`), served on `GET /api/backtest`'s
    `evidence_by_horizon` (ops-hardening iter-5, J-06).

    Like `EventStudyCache` / `MarketPhaseCache` / `CoverageSnapshot`, this is EXPLICITLY NOT a scanner
    snapshot — the *Snapshots are immutable* critical anti-goal binds ONLY `scanner_runs` /
    `scanner_results` / `*_scores` / `forward_returns`. This is legitimately mutable derived/cache
    state: it stores the SERIALIZED `compute_forward_aggregates(...)` payload (forward return by
    bucket/setup/regime, excess vs SPY/QQQ, VCP/new-pattern breakdowns, control-group cohorts — each
    with `n`) keyed by the horizon + the resolved as-of cutoff + a dataset-version stamp, so a read
    serves the stored aggregate instead of re-deriving it per request (No recompute in the read path).
    The cached figures are BYTE-IDENTICAL to a fresh compute — a cache of the deterministic read-only
    aggregation, never a second computation.

    WHY: `compute_forward_aggregates` scans the WHOLE horizon-partition of `forward_returns`
    (`select(ForwardReturn).where(horizon == h)`, then groups it in Python) — `GET /api/backtest`
    called it once per configured horizon (5) on EVERY request. Measured live at the current DB depth
    (`reports/perf-budgets.md`, iter-5): 34.77s for one request — the confirmed J-06 violation.

    A STANDALONE table (its own `create_all`-managed table) is used deliberately so the iter-12
    `_ADDITIVE_COLUMNS` trap does NOT apply — a fresh DB carries it from `create_db_and_tables`, and no
    existing table gains a column.

    CACHE KEY: `(horizon, asof_key, dataset_version)`:
      - `horizon` is the requested horizon (one of `config.walk_forward.horizons`).
      - `asof_key` is the resolved as-of cutoff ISO date — `compute_forward_aggregates`'s `as_of` is
        always a concrete date at its one call site (`GET /api/backtest` always resolves `?as_of=` to a
        real `ScannerRun.asof_date` before calling it — never the bare `as_of=None` all-history case),
        so unlike `EventStudyCache`/`MarketPhaseCache` this key carries no separate "all" sentinel.
      - `dataset_version` is the SAME stamp `app.engine.research._dataset_version` produces
        (single-sourced with J-72/J-87/J-96/J-100) — a read computes the current stamp and looks up
        THIS exact key; a stale row keyed to an older stamp is never hit (and is pruned on write), so
        the cache can NEVER serve a stale figure (it refreshes after any dataset change — a backfill
        that adds runs/returns anywhere changes the global stamp, correctly invalidating even an
        unrelated as-of's cached row, since an expanding as-of window can gain new in-range runs from a
        backfill dated earlier than it).

    `payload_json` is the full serialized aggregate. Unique on the composite key so a write is an
    idempotent upsert."""

    __tablename__ = "forward_aggregate_cache"
    __table_args__ = (
        UniqueConstraint("horizon", "asof_key", "dataset_version", name="uq_forward_aggregate_cache_key"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    horizon: int = Field(index=True)
    asof_key: str  # resolved as-of ISO cutoff date (compute_forward_aggregates's concrete `as_of`)
    dataset_version: str  # the SAME stamp research._dataset_version produces; changes on any dataset change
    payload_json: str  # the serialized compute_forward_aggregates(...) aggregate (byte-identical to a fresh compute)
    created_at: datetime


# --- ops-hardening iter-13 (J-06) index-series ingest-time serving cache -------------------------
class IndexSeriesCache(SQLModel, table=True):
    """A STANDALONE, create_all-managed cache of the derived J-44 major-indexes normalized-% display
    series (`app.engine.indexes.compute_index_series`), served on `GET /api/indexes`'s SINGLE
    unparameterized default hot key (ops-hardening iter-13, J-06) — the request `PhaseCrossViewCard`
    (`/`) and `IndexVendorPanel` (`/data`) both issue unparameterized on mount.

    Like `EventStudyCache` / `MarketPhaseCache` / `ForwardAggregateCache`, this is EXPLICITLY NOT a
    scanner snapshot — the *Snapshots are immutable* critical anti-goal binds ONLY `scanner_runs` /
    `scanner_results` / `*_scores` / `forward_returns`. This is legitimately mutable derived/cache
    state: it stores the SERIALIZED `compute_index_series(...)` payload keyed by the request identity
    plus a dataset-version stamp, so a read serves the stored payload instead of re-deriving it (No
    recompute in the read path). The cached figures are BYTE-IDENTICAL to a fresh compute — a cache of
    the deterministic read-only derivation, never a second computation.

    WHY: `compute_index_series(..., full=True)` hydrates each `index_chart.symbols` ETF's FULL stored
    price history via `bars_through_latest` on EVERY request — measured live (`reports/perf-budgets.md`,
    iter-11/iter-12): 2138.7-2257.7ms for one request against its committed <=1.5s budget — the
    confirmed J-06 violation this cache fixes.

    A STANDALONE table (its own `create_all`-managed table) is used deliberately so the iter-12
    `_ADDITIVE_COLUMNS` trap does NOT apply — a fresh DB carries it from `create_db_and_tables`, and no
    existing table gains a column.

    CACHE KEY: `(range_key, full, dataset_version)`:
      - `range_key` + `full` are the request identity — this cache ONLY ever stores the SINGLE
        unparameterized default hot key (`range_key=cfg.index_chart.default_range`, `full=True`); every
        other range/as-of combination stays on the existing lazy, uncached `compute_index_series` path
        (the "cannot be precomputed — user-parameterized" carve-out).
      - `dataset_version` is a NARROW stamp scoped ONLY to the inputs this series actually reads — the
        configured `index_chart.symbols`' stored bars (`max(date)` + `count(*)`, filtered to those few
        symbols, a bounded indexed read) — deliberately NOT the broad `research._dataset_version` (which
        folds in the `forward_returns` row count and would invalidate on unrelated ingest activity that
        never touches an index symbol's bars), mirroring `_membership_dataset_version`'s own narrow-stamp
        precedent. A read computes the CURRENT stamp and looks up THIS exact key; a stale row keyed to an
        older stamp is never hit (and is pruned on write), so the cache can NEVER serve a stale figure —
        it refreshes the moment any configured index symbol gains a new bar, anywhere.

    The echoed `asof_date` field is RE-DERIVED at read time (never trusted from the stored payload): for
    this specific hot key (`range_key="all"`, i.e. `days=None`), `compute_index_series`'s own series
    computation does not depend on the resolved as-of at all (`bars_through_latest` ignores it, and
    `start` is `None` for the all-history preset) — the ONLY as-of-dependent part of the response is the
    echoed `asof_date`. Re-deriving it at read time (rather than baking a stale one into the stored
    payload) avoids an unnecessary correctness trap on a cache HIT (goal.md iter-13's own technical note).

    `payload_json` is the serialized `series`/`range`/`ranges` (the `asof_date` field it may also carry
    is overwritten at read time, never trusted from storage). Unique on the composite key so a write is
    an idempotent upsert."""

    __tablename__ = "index_series_cache"
    __table_args__ = (
        UniqueConstraint("range_key", "full", "dataset_version", name="uq_index_series_cache_key"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    range_key: str = Field(index=True)
    full: bool
    dataset_version: str  # narrow stamp: max(date)+count(*) over index_chart.symbols' stored bars
    payload_json: str  # the serialized compute_index_series(...) payload (asof_date re-derived at read)
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


# --- ops-hardening iter-56 (J-06) availability-heatmap ingest-time serving cache ------------------
class AvailabilityCache(SQLModel, table=True):
    """A STANDALONE, create_all-managed cache of the J-61 per-trading-date availability heatmap
    (`app.engine.data_manager.compute_availability`), served on `GET /api/data/availability` (the
    `/data` heatmap widget).

    Like `IndexSeriesCache` / `MembershipTimelineCache` / `CoverageSnapshot`, this is EXPLICITLY NOT a
    scanner snapshot — the *Snapshots are immutable* critical anti-goal binds ONLY `scanner_runs` /
    `scanner_results` / `*_scores` / `forward_returns`. This is legitimately mutable derived/cache
    state: it stores the SERIALIZED `compute_availability(...)` payload keyed by a single
    dataset-version stamp, so a read serves the stored payload instead of re-deriving it (No recompute
    in the read path). The cached payload is BYTE-IDENTICAL to a fresh `compute_availability(...)`
    compute — a cache of the deterministic read-only derivation, never a second computation.

    WHY: `compute_availability` runs an unbounded, uncached `GROUP BY daily_prices.date` scan across
    the FULL benchmark trading calendar on EVERY request — measured live (`reports/perf-budgets.md`
    Addendum 18/20): 15.1-21.2s against the committed <=1.5s budget on the grown 8.37 GB dev DB, the
    confirmed J-06 latency source this cache fixes (goal.md's aggregation candidate #7).

    A STANDALONE table (its own `create_all`-managed table) is used deliberately so the iter-12
    `_ADDITIVE_COLUMNS` trap does NOT apply — a fresh DB carries it from `create_db_and_tables`, and no
    existing table gains a column.

    CACHE KEY: `(dataset_version)`:
      - `compute_availability` has NO as-of/range parameter (it always spans the WHOLE benchmark
        trading calendar), so there is no as-of slot — exactly one row per dataset version, mirroring
        `MembershipTimelineCache`'s single-row convention (never `IndexSeriesCache`'s multi-key shape,
        which exists only because THAT function is parameterized by `range_key`/`full`).
      - `dataset_version` reuses the SAME narrow `_membership_dataset_version` stamp (J-100)
        `CoverageSnapshot`/`MembershipTimelineCache` already key on — the snapshot set + bars manifest
        (`max(daily_prices.date)` + `count(*)`), exactly what `compute_availability` reads (ALL stored
        bars for `symbols_with_bars`/`total_symbols`, plus the `ScannerRun.asof_date` set for
        `snapshot_exists`). A read computes the CURRENT stamp and looks up THIS exact key; a stamp
        mismatch is the EXPECTED, tested, INTENDED case while an ingest job is genuinely in flight
        (`app.engine.data_manager.availability_from_storage`, iter-57 J-06 / iter-58 B2 fix) — the
        stamp-mismatched row IS served (with `stale=true`, `served_dataset_version` set to the row's own
        prior stamp), not skipped. It is pruned on write (this table holds at most one row at a time),
        so the cache never serves a heatmap OLDER than its own most recent successful warm.

    `payload_json` is the full serialized `total_symbols`/`trading_day_count`/`cells` payload. Unique
    on `dataset_version` so a write is an idempotent upsert."""

    __tablename__ = "availability_cache"
    __table_args__ = (
        UniqueConstraint("dataset_version", name="uq_availability_cache_key"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_version: str = Field(index=True)  # the SAME narrow stamp _membership_dataset_version produces
    payload_json: str  # the serialized compute_availability(...) payload (byte-identical to a fresh compute)
    created_at: datetime


class NextSessionManifest(SQLModel, table=True):
    """One next-session manifest VERSION row for one `(as_of, version)` pair (goal-market-compass iter-2,
    J-02/J-03/J-04 — the CONTENT block; iter-3, J-05/J-06 — the freeze/integrity block: `mode`/`version`/
    `frozen`/`generation`/three hashes/provenance/cohort-storage/`prospective_eligible`/
    `available_at_utc`/`export_path`, added ADDITIVELY).

    UNLIKE the `*Cache` tables above (`MarketPhaseCache` et al.), this is NOT a cache of a re-derivable
    read — it is a first-class IMMUTABLE record, like `ScannerRun`: computed ONCE per `(as_of, version)`
    (at ingest finalize for the frontier date, on the first `GET /api/compass` for a not-yet-computed
    HISTORICAL `as_of` — create-once-on-GET, never the frontier — or via the explicit confirm-gated
    regenerate action) and NEVER updated or deleted afterward (anti-goal AG-12 — manifest immutability).
    `(as_of, version)` is unique — `version` starts at 1 and is dense/append-only per `as_of`; a
    concurrent create-once race is resolved the SAME way `scanner.persist_run_payload` resolves a
    `ScannerRun` race: roll back the losing INSERT and return the already-committed row (never raise,
    never duplicate, never overwrite). `next_session_manifests` joins NEITHER `clear_snapshot_set` NOR
    the remove-data cascade — no code path deletes a row here.

    The three CONTENT blocks (`session_delta`, `narrative`, `selection` — the `selection` block now also
    carries `comparison_cohort` / `near_threshold_shadow`, iter-3) are stored as their OWN JSON columns
    rather than one combined blob so a future column-projected read never has to deserialize a block it
    does not need (AG-8 posture). `content_hash` is the sha256 hex digest of the sorted-key JSON of
    exactly these three blocks (see `app.engine.compass.build_manifest_payload`) — NOT of this row's
    other columns; it stays invariant across legitimate generation-metadata-only differences (e.g. a
    regenerate with unchanged inputs).

    The FREEZE/INTEGRITY columns below are all ADDITIVE and nullable/defaulted (`db._ADDITIVE_COLUMNS`)
    so an existing pre-iter-3 row backfills `version=1`, `frozen=False`, `mode`/every hash/JSON-block
    column NULL, `prospective_eligible=False` — an honest "pre-freeze era" marker, NEVER retroactively
    marked frozen or eligible. Every column here is written ONCE, together, by
    `app.engine.compass._freeze_manifest` (the single writer behind all three producer paths) and never
    touched again. `generation_json`/`candidate_rule_config_json`/`cohort_rule_config_json`/
    `manifest_config_subset_json`/`dataset_json`/`universe_json`/`comparison_cohort_json`/
    `near_threshold_shadow_json`/`caveats_json` hold their block's OWN verbatim JSON (AG-8 posture, same
    reasoning as the three content columns above). `engine_identity`/`candidate_rule_hash`/
    `cohort_rule_hash`/`manifest_config_hash`/`prospective_eligible`/`manifest_hash` are ALSO typed
    top-level columns (not just JSON-nested) so a future consumer can column-project-filter without
    parsing `generation_json` (`prospective_eligible` is explicitly called out for this in goal.md).
    `export_path` stays NULL when the at-ingest export write fails (isolate-and-continue — an honest gap,
    never a half-written file silently treated as present)."""

    __tablename__ = "next_session_manifests"
    __table_args__ = (
        UniqueConstraint("as_of", "version", name="uq_next_session_manifests_as_of_version"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    as_of: date = Field(index=True)
    # iter-3: version starts at 1 (the finalize freeze or the first historical on-demand GET); a
    # confirm-gated regenerate mints version N+1 for an existing as_of. Pre-iter-3 rows backfill 1.
    version: int = Field(default=1)
    # goal-market-compass iter-10 (J-11 Stage B1): the LIVE `FOREIGN KEY(source_run_id) REFERENCES
    # scanner_runs (id)` DDL is DROPPED from the model declaration here (model-declaration change only --
    # no live-DB migration; the already-created live table keeps its existing DDL untouched, per
    # `.claude/project-template.md`'s additive-ALTER-only schema-evolution rule). This was a LATENT
    # contradiction, not a new one: enforcement was already OFF on the live DB (`PRAGMA foreign_keys` reads
    # `0` -- `app.db._apply_sqlite_pragmas` never issues `PRAGMA foreign_keys=ON`), and
    # `PRAGMA foreign_key_check(next_session_manifests)` already reports 12 violations on the live DB
    # today, all on incident-dated manifests -- so the FK declaration was never actually enforced; it was
    # only ever aspirational. Declaring it here as `foreign_key=...` documents a contract the design does
    # NOT want: AG-12 (manifest immutability) requires a manifest to survive its source `ScannerRun` being
    # deleted and canonically rebuilt (J-11 Stages C/D, a LATER iteration), and a rebuilt run legitimately
    # gets a fresh row (or, since `scanner_runs.id` is a plain SQLite rowid alias with no `AUTOINCREMENT`
    # and no `sqlite_sequence` table, can even REUSE a freed numeric id).
    #
    # Intended end state (docs/goal.md J-11 step 11, verbatim): "`source_run_id` remains stored historical
    # provenance; it is not required to dereference to a live `ScannerRun` forever; manifest survival must
    # not depend on foreign-key enforcement being off; current-run reconciliation is by `as_of` + frozen
    # source timing/provenance, never by FK rebinding; a rebuilt run may legitimately carry a different id;
    # and even when it reuses the same numeric id it is still a rebuilt run whenever the frozen
    # timestamp/provenance differs. Never mutate a manifest to 'repair' an orphaned foreign key."
    #
    # Reconciliation after a delete/rebuild is therefore by `as_of` + `source_run_created_at` (carried
    # inside `generation_json`) + the frozen `engine_identity` -- NEVER by dereferencing `source_run_id`.
    # `app.engine.compass.basis_disclosure` already implements exactly this (it resolves the CURRENT run
    # by `as_of` and compares `source_run_created_at` against that run's `created_at` -- it never reads
    # `source_run_id` at all) and needs NO change here. `source_run_id` stays `index=True` (still a useful
    # lookup/audit column) and its VALUE is still written once and never mutated (AG-12) -- only the live
    # `FOREIGN KEY` constraint declaration is removed.
    source_run_id: int = Field(index=True)
    session_delta_json: str
    narrative_json: str
    selection_json: str
    content_hash: str = Field(index=True)
    created_at: datetime

    # --- iter-3 freeze/integrity block (additive; NULL/False on a pre-iter-3 row) -----------------
    mode: Optional[str] = Field(default=None)  # "at_ingest" | "retrospective" — data-driven, never chosen
    frozen: bool = Field(default=False)  # True for every row minted by the iter-3 freeze writer
    generation_json: Optional[str] = Field(default=None)  # {producer, frontier_bar_date, generated_at,
    # preflight_verdict, engine_identity, source_run_created_at}
    engine_identity: Optional[str] = Field(default=None)  # mirror of generation.engine_identity (typed)
    candidate_rule_hash: Optional[str] = Field(default=None, index=True)
    candidate_rule_config_json: Optional[str] = Field(default=None)
    cohort_rule_hash: Optional[str] = Field(default=None, index=True)
    cohort_rule_config_json: Optional[str] = Field(default=None)
    manifest_config_hash: Optional[str] = Field(default=None)
    manifest_config_subset_json: Optional[str] = Field(default=None)
    dataset_json: Optional[str] = Field(default=None)  # {"stamp": ...}
    universe_json: Optional[str] = Field(default=None)  # {pool_hash, resolver_gate, member_count, profile}
    comparison_cohort_json: Optional[str] = Field(default=None)  # list of frozen non-candidate rows
    near_threshold_shadow_json: Optional[str] = Field(default=None)  # subset of the above, near the floor
    caveats_json: Optional[str] = Field(default=None)  # {evidence, survivorship, sector_basis, cohort_semantics}
    # fail-closed, write-once: true iff mode=at_ingest, producer=ingest_finalize, version=1, frozen=True,
    # a well-formed available_at_utc, and complete provenance — derived ONCE at write, NEVER at read.
    prospective_eligible: bool = Field(default=False, index=True)
    available_at_utc: Optional[datetime] = Field(default=None)
    manifest_hash: Optional[str] = Field(default=None)  # whole-document integrity hash (excl. itself)
    export_path: Optional[str] = Field(default=None)  # NULL when never exported / export write failed


# --- ops-hardening iter-2 (J-05) coverage derived-aggregate snapshot (a PERFORMANCE cache, not a
# snapshot) -----------------------------------------------------------------------------------
class CoverageSnapshot(SQLModel, table=True):
    """A STANDALONE, create_all-managed persisted snapshot of `GET /api/data`'s coverage block
    (`app.engine.data_manager._compute_coverage_uncached`).

    Like `EventStudyCache` / `MarketPhaseCache` / `MembershipTimelineCache`, this is EXPLICITLY NOT a
    scanner snapshot — the *Snapshots are immutable* critical anti-goal binds ONLY `scanner_runs` /
    `scanner_results` / `*_scores` / `forward_returns`. This is legitimately mutable derived/cache state:
    it stores the SERIALIZED `_compute_coverage_uncached(...)` payload (byte-identical to a fresh compute
    — a cache of the deterministic read-only derivation, never a second computation or a hand-authored
    value) keyed by the resolved as-of + a dataset-version stamp, so `GET /api/data` serves the stored
    aggregate instead of recomputing it on the request path (No recompute in the read path).

    WHY: `_compute_coverage_uncached` wraps the whole derivation in one shared `prefilled_bar_cache`
    (a one-time whole-universe bar load) so a cold `/api/data` request paid this cost synchronously on
    the request path — the documented OOM/hang source (iter-24 evidence). This table moves that compute
    to the ingest finalize hook (`app.engine.data_manager._run_job`, on a successful backfill/both/rebuild)
    and a boot-time warm-up safety net (`app.engine.warmup._run_warmup`), so the request path only ever
    reads a stored row (or serves an honest "not yet computed" sentinel — never a live whole-table
    compute on that path).

    A STANDALONE table (its own `create_all`-managed table) is used deliberately so the iter-12
    `_ADDITIVE_COLUMNS` trap does NOT apply — a fresh DB carries it from `create_db_and_tables`, and no
    existing table gains a column.

    CACHE KEY: `(asof_key, dataset_version)`:
      - `asof_key` is the resolved as-of cutoff ISO date — the SAME value `_coverage_cache_key` already
        computes for the in-process single-flight cache (`_resolve_coverage_asof`).
      - `dataset_version` is the SAME narrow `_membership_dataset_version` stamp (J-100) the in-process
        coverage cache and `MembershipTimelineCache` already key on (snapshot set + bars manifest +
        `min_history_bars` — NOT the forward-return count), so this row refreshes exactly when a real
        membership/bars change could change the served coverage, and is reused across the warm-up's
        forward-return churn.

    `payload_json` is the full serialized `_compute_coverage_uncached(...)` derivation (byte-identical to
    a fresh compute); `computed_at` is bookkeeping/audit only (no freshness indicator is rendered this
    iteration). Unique on the composite key so a write is an idempotent upsert."""

    __tablename__ = "coverage_snapshot"
    __table_args__ = (
        UniqueConstraint("asof_key", "dataset_version", name="uq_coverage_snapshot_key"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    asof_key: str = Field(index=True)  # resolved as-of ISO cutoff date (matches _coverage_cache_key)
    dataset_version: str  # the SAME narrow stamp _membership_dataset_version produces
    payload_json: str  # the serialized _compute_coverage_uncached(...) derivation (byte-identical)
    computed_at: datetime  # UTC bookkeeping/audit timestamp — not rendered as a freshness indicator


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
