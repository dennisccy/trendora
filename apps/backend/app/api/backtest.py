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
forward-aggregate compute on the request — `evidence_by_horizon` (plus `evidence_status` /
`evidence_generated_at`) comes ONLY from `resolved_forward_aggregate_evidence`, a pure reader that is
structurally incapable of calling `compute_forward_aggregates`. A HISTORICAL (`is_latest == False`)
`?as_of=` request keeps its pre-existing lazy create-once-and-cache behavior UNCHANGED (an explicit,
logged interpretation call — see the iter-16 dev handoff): this endpoint resolves first, and only when
that read is not already `"ready"` (audit B5 — never unconditionally) does it ensure every configured
horizon is cached for that date (computing any still-missing one via `forward_aggregates_ingest_cached`,
exactly as before iter-16) and re-resolve, so both branches still share ONE code path for building the
response's evidence fields.

ops-hardening iter-17 (audit B1): the resolver's OWN fallback now crosses `asof_key` boundaries — when
the resolved as-of has never had a complete forward-aggregate version of its own (the common shape right
after a new latest trading day lands and its ingest-finalize warm has not yet completed), it serves the
most recent OLDER as-of's complete evidence, labeled `"refreshing"` with the NEW `evidence_asof` field
disclosing WHICH as-of's evidence is actually being shown (never mixed with a newer, incomplete version —
AG-5 preserved: the fallback never serves a row dated after the request). `evidence_asof` equals the
resolved `asof_date` itself when `evidence_status == "ready"`, an older date when `"refreshing"` crosses
an as-of boundary, and `null` when `"not_yet_computed"`.

It serves the per-date SCORECARD + the as-of-scoped evidence aggregate. Regime / sector / theme / stock
values stay single-sourced on their own endpoints (`/api/dashboard`, `/api/sectors`, `/api/themes`,
`/api/stocks` with `?as_of=`) — this endpoint re-serves none of them, and it recomputes no
score/bucket/return in the read path.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
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

# ops-hardening iter-18 -- per-request timing instrumentation (observability only; never a served value,
# TC-1/TC-2/TC-4/TC-8). `logs/backend.log` is populated by redirecting the uvicorn process's own
# stdout/stderr (scripts/start-backend.sh); this process's ROOT logger carries NO handler and defaults to
# WARNING (confirmed by direct inspection), so an otherwise-unconfigured `trendora.*` logger's
# `.info(...)` calls are silently dropped -- Python's `logging.lastResort` fallback itself only emits
# WARNING+. Explicitly setting THIS logger's own level to INFO and attaching a plain `StreamHandler`
# (guarded against double-attachment across repeated imports) makes this module self-sufficient for that
# without touching main.py's boot sequence or any global logging config (out of scope this iteration,
# "Do not redo"). `propagate` is left at its default `True` so `caplog`-based tests (TC-4) still observe
# these records via the root logger, exactly as production emits them via this handler.
logger = logging.getLogger("trendora.backtest")
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())


def _log_backtest_timing(
    is_latest: bool,
    total_ms: float,
    resolved_run_ms: float,
    backfill_forward_returns_ms: float,
    scorecard_ms: float,
    evidence_ms: float,
    ensure_loop_ms: Optional[float],
) -> None:
    """One INFO-level, key=value structured timing line per `/backtest` request: an ISO-8601 wall-clock
    timestamp plus the elapsed-ms breakdown the iter-18 spec calls for -- run resolution, the
    `backfill_run_forward_returns` step, `compute_run_scorecard`, and `resolved_forward_aggregate_
    evidence`. `ensure_loop_ms` (the historical/non-`is_latest` ensure-loop's `forward_aggregates_
    ingest_cached` calls plus its re-resolve) is present ONLY when that branch actually ran -- never a
    fabricated 0 for the `is_latest` request path, which never reaches it. Purely an operational log
    line for the iter-18/iter-19 latency diagnosis -- never a served/displayed value (Data Contract
    untouched)."""
    fields = [
        f"ts={datetime.now(timezone.utc).isoformat()}",
        f"is_latest={is_latest}",
        f"total_ms={total_ms:.2f}",
        f"resolved_run_ms={resolved_run_ms:.2f}",
        f"backfill_forward_returns_ms={backfill_forward_returns_ms:.2f}",
        f"scorecard_ms={scorecard_ms:.2f}",
        f"evidence_ms={evidence_ms:.2f}",
    ]
    if ensure_loop_ms is not None:
        fields.append(f"ensure_loop_ms={ensure_loop_ms:.2f}")
    logger.info("backtest_timing %s", " ".join(fields))


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
    populated create-once on first view, then READ; the scorecard recomputes no score/bucket/return.

    ops-hardening iter-18: wrapped in per-request, phase-broken-down wall-clock timing instrumentation
    (`_log_backtest_timing`, TC-1/TC-2/TC-4/TC-8) diagnosing the still-undiagnosed <=1.5s serving-budget
    breaches (J-06/J-07/J-08) — observability only, the returned payload stays byte-identical (TC-6)."""
    t_request_start = time.perf_counter()
    cfg: Config = get_config()

    t0 = time.perf_counter()
    run = resolved_run(session, as_of, cfg)          # immutable snapshot (create-once) or explicit 4xx/503
    resolved_run_ms = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    backfill_run_forward_returns(session, run, cfg)  # create-once: INSERT-only realized forward returns
    backfill_forward_returns_ms = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    card = compute_run_scorecard(session, run, cfg)  # SINGLE canonical per-date scorecard (reads stored)
    scorecard_ms = (time.perf_counter() - t0) * 1000.0

    # `is_latest` reuses the canonical "latest stored run date" (no second query/source for it).
    is_latest = run.asof_date == _latest_stored_run_date(session)
    # iter-17 (J-09/J-10) + iter-16 (J-08): the as-of-scoped forward-tested evidence aggregate, ALL
    # configured horizons resolved together in ONE call (never a per-horizon-independent read — the read
    # path can otherwise observe a mixed-dataset_version row set, see the resolver's own docstring) plus
    # the honest `evidence_status` / `evidence_generated_at` / `evidence_asof` disclosure.
    t0 = time.perf_counter()
    evidence = resolved_forward_aggregate_evidence(session, run.asof_date, cfg)
    evidence_ms = (time.perf_counter() - t0) * 1000.0
    # ops-hardening iter-16 (J-08): the historical (is_latest == False) carve-out keeps its pre-existing
    # lazy create-once-and-cache behavior UNCHANGED (TC-13) — ensure every configured horizon is cached
    # for this date, then re-resolve. For the LATEST view this never runs, so this request path never
    # reaches `forward_aggregates_ingest_cached` — let alone `compute_forward_aggregates` — under any
    # circumstance (J-08's zero-compute-on-request guarantee).
    #
    # iter-17 (audit B5): gated on the resolver's OWN first read rather than unconditional — on an
    # already-warmed historical date (the common repeat-view case for the Backtest/Time-Machine
    # workspace) the resolver above already found `evidence_status == "ready"`, so the ensure loop below
    # is skipped entirely, avoiding a redundant per-horizon cache-hit read+deserialize immediately
    # followed by the SAME resolver re-reading and re-parsing those same rows a second time. Byte-
    # identical either way (still one producer, one serving read): a cold historical date still ensures
    # every horizon is cached (computing any still-missing one) and re-resolves once, exactly as before.
    #
    # ops-hardening iter-18: `ensure_loop_ms` times this WHOLE block (the per-horizon
    # `forward_aggregates_ingest_cached` calls plus the re-resolve) — present in the timing log line ONLY
    # when this branch actually runs, mirroring exactly when `forward_aggregates_ingest_cached` fires.
    ensure_loop_ms: Optional[float] = None
    if not is_latest and evidence["evidence_status"] != "ready":
        t0 = time.perf_counter()
        for h in cfg.walk_forward.horizons:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=run.asof_date)
        evidence = resolved_forward_aggregate_evidence(session, run.asof_date, cfg)
        ensure_loop_ms = (time.perf_counter() - t0) * 1000.0

    total_ms = (time.perf_counter() - t_request_start) * 1000.0
    _log_backtest_timing(
        is_latest, total_ms, resolved_run_ms, backfill_forward_returns_ms, scorecard_ms, evidence_ms,
        ensure_loop_ms,
    )
    return {
        **card,
        "is_latest": is_latest,
        "evidence_by_horizon": evidence["evidence_by_horizon"],
        "evidence_status": evidence["evidence_status"],
        "evidence_generated_at": evidence["evidence_generated_at"],
        "evidence_asof": evidence["evidence_asof"],
    }
