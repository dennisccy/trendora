"""GET /api/backtest — the per-date forward-test scorecard endpoint (Data Contract:
app.engine.forward_testing). The Backtest / Time-Machine workspace's NEW value (J-14).

Resolves ?as_of= to its IMMUTABLE stored snapshot via the iter-8 resolver
(`snapshot_serving.resolved_run`: default = latest stored run; create-once for a not-yet-stored date;
invalid date -> explicit 4xx/503 via the shared `_STATUS_BY_KIND` map, never a fabricated snapshot),
populates that run's realized forward returns CREATE-ONCE (`backfill_run_forward_returns` — INSERT-only
into the append-only `forward_returns` table; the "first view computes once" path the No-recompute-in-
the-read-path anti-goal explicitly permits), then returns `compute_run_scorecard(...)` — the SINGLE
canonical per-date scorecard (cohort return + excess vs SPY/QQQ/sector + the five control cohorts, each
with sample size `n` and honest NA, plus the survivorship-bias label and `min_sample` threshold) — AND
(iter-17) the as-of-scoped forward-tested evidence aggregate.

`evidence_by_horizon` (iter-17, J-09/J-10): per configured horizon, the as-of-scoped forward-return
aggregation (by bucket / setup / regime, excess vs SPY/QQQ, VCP-vs-non-VCP + the new-pattern breakdowns,
and the control-group cohorts, each with `n`) scoped to the EXPANDING WINDOW of snapshots dated <= the
resolved as-of date. All horizons ride the one payload so the client-side horizon selector needs no
refetch (J-15/J-18). This RELOCATES the value off the retired System Health page (its single home is now
Backtest) under the single global as-of control; it recomputes no return/score/bucket, reading the stored
`forward_returns` exactly as System Health did — now filtered to <= D.

ops-hardening iter-16 (J-08): for the LATEST view (`is_latest == True`) this endpoint NEVER triggers a
forward-aggregate compute on the request — `evidence_by_horizon` (plus the new `evidence_status` /
`evidence_generated_at`) comes ONLY from `resolved_forward_aggregate_evidence`, a pure reader that is
structurally incapable of calling `compute_forward_aggregates`. A HISTORICAL (`is_latest == False`)
`?as_of=` request keeps its pre-existing lazy create-once-and-cache behavior UNCHANGED (an explicit,
logged interpretation call — see the iter-16 dev handoff): this endpoint first ensures every configured
horizon is cached for that date (computing any still-missing one via `forward_aggregates_ingest_cached`,
exactly as before iter-16), then reads the result back through the SAME resolver, so both branches share
one code path for building the response's evidence fields.

It serves the per-date SCORECARD + the as-of-scoped evidence aggregate. Regime / sector / theme / stock
values stay single-sourced on their own endpoints (`/api/dashboard`, `/api/sectors`, `/api/themes`,
`/api/stocks` with `?as_of=`) — this endpoint re-serves none of them, and it recomputes no
score/bucket/return in the read path.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.config import Config, get_config
from app.db import get_session
from app.engine.forward_testing import (
    backfill_run_forward_returns,
    compute_run_scorecard,
    forward_aggregates_ingest_cached,
    resolved_forward_aggregate_evidence,
)
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
    is_latest = run.asof_date == _latest_stored_run_date(session)
    # ops-hardening iter-16 (J-08): the historical (is_latest == False) carve-out keeps its pre-existing
    # lazy create-once-and-cache behavior UNCHANGED (TC-13) — ensure every configured horizon is cached
    # for this date (a no-op for an already-warmed date). For the LATEST view this loop never runs, so
    # this request path never reaches `forward_aggregates_ingest_cached` — let alone
    # `compute_forward_aggregates` — under any circumstance (J-08's zero-compute-on-request guarantee).
    if not is_latest:
        for h in cfg.walk_forward.horizons:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=run.asof_date)
    # iter-17 (J-09/J-10) + iter-16 (J-08): the as-of-scoped forward-tested evidence aggregate, ALL
    # configured horizons resolved together in ONE call (never a per-horizon-independent read — the read
    # path can otherwise observe a mixed-dataset_version row set, see the resolver's own docstring) plus
    # the honest `evidence_status` / `evidence_generated_at` disclosure.
    evidence = resolved_forward_aggregate_evidence(session, run.asof_date, cfg)
    return {
        **card,
        "is_latest": is_latest,
        "evidence_by_horizon": evidence["evidence_by_horizon"],
        "evidence_status": evidence["evidence_status"],
        "evidence_generated_at": evidence["evidence_generated_at"],
    }
