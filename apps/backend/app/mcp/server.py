"""Trendora "window" — a READ-ONLY MCP **stdio** server over the live computed evidence.

Run it as a stdio MCP server::

    cd apps/backend && .venv/bin/python -m app.mcp.server

Every ``@mcp.tool()`` opens a short-lived ``Session`` on the app's process engine
(``app.db.get_engine`` — the SAME database the FastAPI app serves) and delegates to
``app.mcp.tools``, which reuses the exact engine / serving functions the read routers call. So each
tool's output is byte-identical to the matching ``GET /api`` endpoint — output PARITY is the point.

READ-ONLY w.r.t. the snapshot DB: the reads expose computed evidence (regime, scores, market phase,
backtest scorecard, factor-lab / event-study / samples, regime history, runs, methodology, indexes) —
NO watchlist write, NO data-manager job, NO snapshot mutation. The single write-bearing tool is the
referee ``verify_edge``, which is read-only against the snapshot DB and writes ONLY the append-only
certified-claims ledger (a file) — it certifies whether a proposed edge is real before it may ship.

On launch the server performs the SAME minimal, idempotent boot readiness the FastAPI app does
(create tables + load the committed offline seed) so it works against a fresh checkout; it is a no-op
once the DB is populated. Importing this module does NOT touch the DB — readiness + ``mcp.run()`` run
only under ``__main__``.

NOTE: this module intentionally does NOT use ``from __future__ import annotations``. FastMCP (1.12.x)
builds each tool's input schema by reflecting on the live parameter annotations, so they must remain
real typing objects at runtime (PEP 563 stringized annotations break its parameter inspection).
"""
import logging
from contextlib import contextmanager
from typing import Iterator, Optional

from mcp.server.fastmcp import FastMCP
from sqlmodel import Session

from app.db import get_engine
from app.mcp import tools

logger = logging.getLogger("trendora.mcp")

mcp = FastMCP("trendora-window")


@contextmanager
def _session() -> Iterator[Session]:
    """A short-lived read session on the app's process engine — the same way the app obtains one."""
    with Session(get_engine()) as session:
        yield session


# --------------------------------------------------------------------------------------------------
# Snapshot-served reads
# --------------------------------------------------------------------------------------------------
@mcp.tool()
def get_dashboard(as_of: Optional[str] = None) -> dict:
    """Market regime panel + universe-relative breadth + stored candidate counts for the resolved as-of
    date (latest stored run by default). Mirrors GET /api/dashboard."""
    with _session() as session:
        return tools.get_dashboard(session, as_of)


@mcp.tool()
def get_leaderboard(
    as_of: Optional[str] = None,
    sector: Optional[str] = None,
    theme: Optional[str] = None,
    pattern: Optional[str] = None,
    ticker: Optional[str] = None,
) -> dict:
    """Per-stock leaderboard (three 0-100 scores + buckets, setup, detected patterns, themes, stored
    forward returns) for the resolved as-of date. Optional filters post-filter the SAME stored rows:
    `ticker` (exact), `sector`, `theme` (slug or name), `pattern` (vcp | pullback_to_rising_dma |
    flat_base_breakout, kept when flagged). No filters => byte-identical to GET /api/stocks."""
    with _session() as session:
        return tools.get_leaderboard(
            session, asof=as_of, sector=sector, theme=theme, pattern=pattern, ticker=ticker
        )


@mcp.tool()
def get_stock_evidence(ticker: str, as_of: Optional[str] = None) -> dict:
    """Full evidence for one ticker — the SAME stored row the leaderboard serves, with its stored
    forward returns. Mirrors GET /api/stocks/{ticker}."""
    with _session() as session:
        return tools.get_stock_evidence(session, ticker, as_of)


@mcp.tool()
def get_sectors(as_of: Optional[str] = None) -> dict:
    """Canonical Sector Score rows (score + bucket + components + the ETF's own stored forward returns)
    for the resolved as-of date. Mirrors GET /api/sectors."""
    with _session() as session:
        return tools.get_sectors(session, as_of)


@mcp.tool()
def get_themes(as_of: Optional[str] = None) -> dict:
    """Canonical Theme Score rows (score + bucket + members + the basket's stored forward returns) for
    the resolved as-of date. Mirrors GET /api/themes."""
    with _session() as session:
        return tools.get_themes(session, as_of)


# --------------------------------------------------------------------------------------------------
# Market phase
# --------------------------------------------------------------------------------------------------
@mcp.tool()
def get_market_phase(
    as_of: Optional[str] = None, retrospective: bool = False, full: bool = False
) -> dict:
    """Market Phase & Severity derivation for the resolved as-of date (phase, 0-100 severity breakdown,
    cycle legs, forward filtered P(bear), causal timeline + episodes + recovery-turn). `full` attaches
    the full-history `timeline_full`; `retrospective` attaches the fenced analysis-only smoothed series.
    Mirrors GET /api/market-phase."""
    with _session() as session:
        return tools.get_market_phase(session, asof=as_of, retrospective=retrospective, full=full)


# --------------------------------------------------------------------------------------------------
# Backtest
# --------------------------------------------------------------------------------------------------
@mcp.tool()
def query_backtest(as_of: Optional[str] = None) -> dict:
    """Per-date forward-test scorecard (cohort return + excess vs SPY/QQQ/sector + control cohorts, each
    with n) plus the as-of-scoped evidence aggregate per horizon and `is_latest`. Mirrors
    GET /api/backtest."""
    with _session() as session:
        return tools.query_backtest(session, as_of)


# --------------------------------------------------------------------------------------------------
# Research lab
# --------------------------------------------------------------------------------------------------
@mcp.tool()
def query_factor_lab(
    factor: Optional[str] = None,
    horizon: Optional[int] = None,
    all_factors: bool = False,
    as_of: Optional[str] = None,
) -> dict:
    """Factor Lab: per-factor decile table of mean forward return + downside risk-adjusted + n, the
    Spearman rank-IC, and the by-regime effectiveness split. `all_factors=True` serves the all-factors
    aggregate. Optional `as_of` scopes to snapshots <= D. Mirrors GET /api/research/factor-lab."""
    with _session() as session:
        return tools.query_factor_lab(
            session, factor=factor, horizon=horizon, all_factors=all_factors, asof=as_of
        )


@mcp.tool()
def query_event_study(
    subject: Optional[str] = None,
    horizon: Optional[int] = None,
    view: Optional[str] = None,
    as_of: Optional[str] = None,
) -> dict:
    """Setup & Pattern event study for a subject + horizon + view (episodes | pooled): forward-return
    distribution + expectancy + MAE/MFE + downside risk-adjusted + best-exit-horizon + by-regime/
    by-sector slices. Optional `as_of` scopes to snapshots <= D. Mirrors GET /api/research/event-study."""
    with _session() as session:
        return tools.query_event_study(
            session, subject=subject, horizon=horizon, view=view, asof=as_of
        )


@mcp.tool()
def drill_samples(
    kind: str,
    horizon: Optional[int] = None,
    factor: Optional[str] = None,
    slice_kind: Optional[str] = None,
    decile: Optional[int] = None,
    regime: Optional[str] = None,
    sector: Optional[str] = None,
    condition: Optional[list[str]] = None,
    cohort: Optional[str] = None,
    single_index: Optional[int] = None,
    subject: Optional[str] = None,
    view: Optional[str] = None,
    setup: Optional[str] = None,
    pattern: Optional[str] = None,
    phase: Optional[str] = None,
    dimension: Optional[str] = None,
    family: Optional[str] = None,
    velocity_sign: Optional[str] = None,
    regime_decile: Optional[int] = None,
    severity_decile: Optional[int] = None,
    factor_decile: Optional[int] = None,
    as_of: Optional[str] = None,
) -> dict:
    """Research samples drill-down: the exact member observations behind ONE published `N=` figure (the
    response `total` equals that N). `kind` selects the lab (factor | combination | event-study |
    regime-setup-pattern | recovery-turn | downtrend-opportunity | severity-velocity | regime-lab |
    phase-severity-lab | regime-phase-factor); the per-kind selectors reproduce the exact cohort slice.
    Optional `as_of` scopes to snapshots <= D. Mirrors GET /api/research/samples."""
    with _session() as session:
        return tools.drill_samples(
            session, kind=kind, horizon=horizon, factor=factor, slice_kind=slice_kind, decile=decile,
            regime=regime, sector=sector, condition=condition, cohort=cohort,
            single_index=single_index, subject=subject, view=view, setup=setup, pattern=pattern,
            phase=phase, dimension=dimension, family=family, velocity_sign=velocity_sign,
            regime_decile=regime_decile, severity_decile=severity_decile, factor_decile=factor_decile,
            asof=as_of,
        )


# --------------------------------------------------------------------------------------------------
# Edge certification — the referee (the one tool that writes, and ONLY the append-only ledger; it is
# read-only w.r.t. the snapshot DB).
# --------------------------------------------------------------------------------------------------
@mcp.tool()
def verify_edge(claim: dict, ledger_path: str, register_date: str) -> dict:
    """Certify (PASS) or reject (FAIL/INSUFFICIENT) a proposed edge — a research cohort's forward-return
    advantage over a same-dates benchmark control — and APPEND the verdict to the append-only
    certified-claims ledger at `ledger_path`. READ-ONLY w.r.t. the snapshot DB; the SOLE write is the
    ledger append.

    The referee runs a sealed temporal holdout (purge+embargo), a block-bootstrap p-value, Bonferroni
    multiple-testing deflation against the ledger's cumulative trial count, and a Thresholdout-style
    alpha-budget charge (overfit edges cost budget; an exhausted budget refuses with INSUFFICIENT).

    `claim` mirrors `drill_samples`' selectors + a `horizon` (and optional `direction` /
    `min_effect_size`), e.g. ``{"kind": "factor", "horizon": 20, "factor": "<key>",
    "slice_kind": "decile", "decile": 10}``. `register_date` is the caller-stamped certification date."""
    with _session() as session:
        return tools.verify_edge(session, claim, ledger_path, register_date=register_date)


# --------------------------------------------------------------------------------------------------
# Additional read-only mirrors
# --------------------------------------------------------------------------------------------------
@mcp.tool()
def get_regime_history(as_of: Optional[str] = None, full: bool = False) -> dict:
    """Stored per-date `{date -> {label, score}}` market-regime series, bounded to dates <= the resolved
    as-of (read verbatim; nothing recomputed). Mirrors GET /api/regime-history."""
    with _session() as session:
        return tools.get_regime_history(session, asof=as_of, full=full)


@mcp.tool()
def get_indexes(
    range_key: Optional[str] = None, as_of: Optional[str] = None, full: bool = False
) -> dict:
    """Server-side normalized-% lines for the config-listed index ETFs over the selected `range_key`
    preset (rebased to the range start). Mirrors GET /api/indexes."""
    with _session() as session:
        return tools.get_indexes(session, range_key=range_key, asof=as_of, full=full)


@mcp.tool()
def get_methodology() -> dict:
    """Config-backed Setup & Pattern catalog (the single source for the methodology page + the /stocks
    badge tooltips + setup-filter vocabulary). Mirrors GET /api/methodology."""
    return tools.get_methodology()


@mcp.tool()
def list_runs() -> dict:
    """Immutable as-of scanner-run history (descending by date), each with its stored regime label/score,
    candidate counts, and stock count. Mirrors GET /api/runs."""
    with _session() as session:
        return tools.list_runs(session)


@mcp.tool()
def get_run(run_id: int) -> dict:
    """One run's full STORED snapshot: regime panel, universe-relative breadth, candidate counts, and the
    ranked stored stock rows. Mirrors GET /api/runs/{run_id}."""
    with _session() as session:
        return tools.get_run(session, run_id)


def _ensure_ready() -> None:
    """Minimal, idempotent boot readiness — the SAME steps the FastAPI app does at startup (create
    tables + load the committed offline seed). A no-op once the DB is populated; it lets the stdio
    server work against a fresh checkout without any network access."""
    # Imported lazily so module import stays side-effect-free (no config/DB work on `import`).
    from app.config import load_config
    from app.db import create_db_and_tables
    from app.seed_loader import load_seed

    config = load_config()
    engine = get_engine()
    create_db_and_tables(engine)
    load_seed(engine, config)  # idempotent — no-op once the DB is populated


if __name__ == "__main__":
    _ensure_ready()
    mcp.run()  # stdio transport (default)
