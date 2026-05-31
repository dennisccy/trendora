"""GET /api/backtest — the per-date forward-test scorecard endpoint (Data Contract:
app.engine.forward_testing). The Backtest / Time-Machine workspace's NEW value (J-14).

Resolves ?as_of= to its IMMUTABLE stored snapshot via the iter-8 resolver
(`snapshot_serving.resolved_run`: default = latest stored run; create-once for a not-yet-stored date;
invalid date -> explicit 4xx/503 via the shared `_STATUS_BY_KIND` map, never a fabricated snapshot),
populates that run's realized forward returns CREATE-ONCE (`backfill_run_forward_returns` — INSERT-only
into the append-only `forward_returns` table; the "first view computes once" path the No-recompute-in-
the-read-path anti-goal explicitly permits), then returns `compute_run_scorecard(...)` — the SINGLE
canonical per-date scorecard (cohort return + excess vs SPY/QQQ/sector + the five control cohorts, each
with sample size `n` and honest NA, plus the survivorship-bias label and `min_sample` threshold).

It serves the per-date SCORECARD ONLY. Regime / sector / theme / stock values stay single-sourced on
their own endpoints (`/api/dashboard`, `/api/sectors`, `/api/themes`, `/api/stocks` with `?as_of=`) —
this endpoint re-serves none of them, and it recomputes no score/bucket/return in the read path.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.config import Config, get_config
from app.db import get_session
from app.engine.forward_testing import backfill_run_forward_returns, compute_run_scorecard
from app.engine.scanner import _latest_stored_run_date
from app.engine.snapshot_serving import resolved_run

router = APIRouter(tags=["backtest"])


@router.get("/backtest")
def backtest(
    as_of: Optional[str] = Query(
        default=None, description="historical as-of date (YYYY-MM-DD); omitted = latest stored run"
    ),
    session: Session = Depends(get_session),
) -> dict:
    """Serve the per-date forward-test scorecard for the resolved as-of date. `as_of` omitted = the
    latest stored run; a historical date time-travels to that date's immutable snapshot; an invalid
    date raises an explicit 4xx/503 (never a fabricated scorecard). The run's forward returns are
    populated create-once on first view, then READ; the scorecard recomputes no score/bucket/return."""
    cfg: Config = get_config()
    run = resolved_run(session, as_of, cfg)          # immutable snapshot (create-once) or explicit 4xx/503
    backfill_run_forward_returns(session, run, cfg)  # create-once: INSERT-only realized forward returns
    card = compute_run_scorecard(session, run, cfg)  # SINGLE canonical per-date scorecard (reads stored)
    # `is_latest` reuses the canonical "latest stored run date" (no second query/source for it).
    return {**card, "is_latest": run.asof_date == _latest_stored_run_date(session)}
