"""GET /api/health — backend connectivity + offline-seed-spine status + readiness (iter-28, J-40).

Carries no canonical score (per the blueprint Data Contract). Reports DB reachability, the active
provider, the latest seed date present, and how many symbols are loaded. `last_run_date` is null until a
scanner run exists (iter-5+).

iter-28 (J-40) extends this SINGLE canonical endpoint with the honest backend `readiness` state ∈
{`ready`, `initializing`, `unavailable`} + the background warm-up progress `warmup {done, total, status,
message}`, both computed ONCE by `app.engine.readiness.compute_readiness` (the single readiness producer)
— there is NO second readiness read path. The frontend readiness badge and the Backtest/Research
"warming up (n/m)" states are the ONLY readers; the frontend never computes readiness itself.

iter-33 (J-20) additively extends this SAME endpoint with the `preflight` field — the composite
GO/DEGRADED/NO-GO verdict from `app.engine.readiness.compute_preflight` (which itself reuses this
module's own `readiness`/`warmup` computation — no second computation). The layout-level
`PreflightBanner` is the ONLY reader; existing `readiness`/`warmup`/`status`/etc. keys are unchanged
(byte-identical — J-40 not regressed).

ops-hardening iter-4 (B3 fix) additively extends this SAME endpoint with the `readiness_detail` field —
the sibling `detail` string from `compute_readiness`'s own return (`null` except for the new
`awaiting_snapshot` state). Previously `compute_readiness`'s dict was discarded down to just
`readiness["state"]`, so this value was computed correctly but never reached the frontend; this is the
wiring fix. `readiness` itself stays the SAME bare string it always was (byte-identical contract).

ops-hardening iter-24 (J-09) additively extends this SAME endpoint with the `background_compute` field —
`compute_readiness`'s own composed `app.engine.forward_testing.get_background_compute_status()` output
(`{active, recent_outcomes}`), disclosing the in-process historical background-compute dispatch iter-20
introduced (previously visible only by reconstructing it from raw DB timestamps). Degrades to
`{"active": [], "recent_outcomes": []}` on any compute error — the SAME degrade-on-error convention as
`readiness`/`preflight` above, never a blank/fabricated field.

ops-hardening iter-67 (J-07) additively wires in the optional, env-flag-gated health-request-wait
watchdog (`app.engine.health_watchdog`) — DIAGNOSTIC ONLY, off by default (`TRENDORA_HEALTH_WATCHDOG`
unset/`0`). When armed it times how long THIS request waited between arriving at the ASGI layer and this
handler body starting to execute, appending the sample to `logs/health-watchdog.jsonl` — it never
changes what is computed or what this endpoint returns (the `request` param defaults to `None` so the
pre-existing direct-call test shape, `health(session)`, is unaffected).

ops-hardening iter-68 (J-07) additively extends the SAME watchdog with a third sample, `handler_compute_s`
— from the SAME `t_handler_start` to immediately before this function returns (after the readiness/
preflight computation and DB reads above, before serialization). iter-67's own drill named `queue_wait_s`
as only ~11% of its one breach's magnitude; this sample names the previously-untimed remainder. SAME flag,
SAME writer, SAME log file — no second instrument.

ops-hardening iter-69 (J-07) decomposes that SAME `handler_compute_s` sample into its three constituent
parts — `db_reads_s` (the three DB reads immediately below), `readiness_s` (the `compute_readiness` call),
`preflight_s` (the `compute_preflight` call, including its own nested `record_verdict_transition` write —
not split out this round) — timed with the SAME monotonic clock, wrapped around the SAME already-existing
try/except blocks (so an internal exception, already caught and degraded below, still yields a real
elapsed-time sample for that span rather than a partial/missing one). Written into the SAME
`handler_compute` record via `record_handler_compute`'s new keyword-only params — no second flag, writer,
or record type. Diagnostic-log-only: the response body/shape below is unaffected either way (TC-8).
"""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select, text
from sqlmodel import Session

from app.config import get_config
from app.db import get_engine, get_session
from app.engine import health_watchdog
from app.engine.readiness import compute_preflight, compute_readiness, record_verdict_transition
from app.models import DailyPrice, ScannerRun

router = APIRouter(tags=["health"])

# ops-hardening iter-57 (J-06 closure): a plain `SELECT COUNT(DISTINCT symbol) FROM daily_prices` makes
# SQLite do a full COVERING INDEX SCAN of every (symbol, date) row to compute the distinct count — live
# profiling on the grown 8.37 GB dev DB (3.3M rows) measured this ALONE at 0.117-0.119s (`EXPLAIN QUERY
# PLAN`: `SCAN daily_prices USING COVERING INDEX ...`), the confirmed majority of this endpoint's
# 0.16-0.241s steady-state latency against the committed <=0.1s budget (`reports/perf-budgets.md`, new
# dated addendum). `symbol` is the LEADING column of that same unique index, so a recursive-CTE "walk
# the index for the next distinct value" query (the standard SQLite loose-index-scan idiom) makes SQLite
# do ~591 indexed SEARCHes (one per distinct symbol) instead of a 3.3M-row scan — confirmed live:
# `EXPLAIN QUERY PLAN` shows `SEARCH daily_prices USING COVERING INDEX ... (symbol>?)`, same exact
# result (591), 0.001-0.003s (roughly 100x). This is a pure query-SHAPE change — still a fully live,
# request-time count (no staleness introduced, no persisted/cached value, no response field/shape
# change) — the SAME "keep it lazy/indexed, never precomputed-and-stale" convention this endpoint's
# contract already commits to.
_DISTINCT_SYMBOL_COUNT_SQL = text(
    """
    WITH RECURSIVE syms(sym) AS (
        SELECT (SELECT MIN(symbol) FROM daily_prices)
        UNION ALL
        SELECT (SELECT MIN(symbol) FROM daily_prices WHERE symbol > sym) FROM syms WHERE sym IS NOT NULL
    )
    SELECT COUNT(*) FROM syms WHERE sym IS NOT NULL
    """
)


def _distinct_symbol_count(session: Session) -> int:
    """The distinct count of symbols with >= 1 stored `daily_prices` bar — byte-identical to
    `SELECT COUNT(DISTINCT symbol) FROM daily_prices` for the SAME DB state, via the fast indexed-walk
    query above instead of a full covering-index scan."""
    return int(session.execute(_DISTINCT_SYMBOL_COUNT_SQL).scalar_one() or 0)


@router.get("/health")
def health(session: Session = Depends(get_session), request: Request = None) -> dict:
    # ops-hardening iter-67/68 (J-07): the watchdog's own t_handler_start, taken BEFORE any of the
    # readiness/preflight computation below runs, so a queue-wait sample is captured for THIS request
    # regardless of what happens later in the handler (a readiness-computation exception is already
    # caught below and degrades honestly -- it never reaches here). Only does anything when the flag is
    # armed AND `HealthWatchdogMiddleware` actually ran for this request (real ASGI traffic); a
    # direct-call test invoking `health(session)` with no `request` is untouched. A watchdog write
    # failure must never suppress, delay, or alter this route's own response (AG-8: never a wedge) --
    # mirrors this file's own existing degrade-on-error convention. `t_handler_start`/`t_received_wall`
    # are kept (not scoped to this block) so the iter-68 `handler_compute_s` sample near the bottom of
    # this function can time against the SAME start instant.
    watchdog_active = health_watchdog.enabled() and request is not None
    t_handler_start = time.monotonic() if watchdog_active else None
    t_received_wall = None
    if watchdog_active:
        try:
            t_received = getattr(request.state, "health_watchdog_t_received_monotonic", None)
            t_received_wall = getattr(request.state, "health_watchdog_t_received_wall", None)
            if t_received is not None and t_received_wall is not None:
                health_watchdog.record_queue_wait(t_received, t_received_wall, t_handler_start)
        except Exception:  # pragma: no cover - a watchdog write failure must never blank/break /health
            pass

    cfg = get_config()
    provider = cfg.provider
    # ops-hardening iter-69 (J-07): db_reads_s -- wraps the SAME three reads below, whether they succeed
    # or raise (the except block already degrades honestly; timing still stops right after it either
    # way, so a real elapsed-time sample is captured for both outcomes, never a partial/missing one).
    _t_db_reads_start = time.monotonic() if watchdog_active else None
    try:
        latest = session.scalar(select(func.max(DailyPrice.date)))
        symbol_count = _distinct_symbol_count(session)
        # goal-ops-hardening iter-62: the SAME query shape `app.engine.data_manager` already uses to
        # resolve the latest scanner run date (e.g. its `latest_run_date` reads) -- no second derivation.
        # Null on an empty DB (no scanner run yet), matching this module's own docstring contract.
        last_run_date = session.scalar(select(func.max(ScannerRun.asof_date)))
        db_ok = True
    except Exception:  # pragma: no cover - DB unreachable is surfaced, never faked
        latest = None
        symbol_count = 0
        last_run_date = None
        db_ok = False
    db_reads_s = (time.monotonic() - _t_db_reads_start) if watchdog_active else None

    # The single honest readiness state + warm-up progress (computed once by the readiness producer).
    # `engine` lets it compute the expected cadence total when no warm-up record exists yet. A DB error
    # inside the producer degrades to `unavailable` (never a fabricated `ready`).
    # ops-hardening iter-69 (J-07): readiness_s -- wraps this SAME call, success or degraded alike.
    _t_readiness_start = time.monotonic() if watchdog_active else None
    try:
        readiness = compute_readiness(session, engine=get_engine())
    except Exception:  # pragma: no cover - never let a readiness error blank the health probe
        readiness = {
            "state": "unavailable",
            "detail": None,
            "warmup": {"done": 0, "total": 0, "status": "pending", "message": "history 0/0"},
            "background_compute": {"active": [], "recent_outcomes": []},
        }
    readiness_s = (time.monotonic() - _t_readiness_start) if watchdog_active else None

    # iter-33 (J-20): the single daily preflight verdict (GO/DEGRADED/NO-GO + reasons). A compute error
    # degrades to an honest NO-GO — never a blank/fabricated field (anti-goal #8).
    # ops-hardening iter-69 (J-07): preflight_s -- wraps this SAME call AND its own nested
    # record_verdict_transition write (not split into a fourth span this round, per spec).
    _t_preflight_start = time.monotonic() if watchdog_active else None
    try:
        preflight = compute_preflight(session, config=cfg)
        try:
            # Append-only, ONLY on a transition (never on every ~2s poll) -- a history-write failure must
            # never blank the health probe (mirrors the readiness try/except immediately above).
            record_verdict_transition(preflight["verdict"], preflight["reasons"], preflight["reference"])
        except Exception:  # pragma: no cover - a history-log write failure must never blank /health
            pass
    except Exception:  # pragma: no cover - never let a preflight error blank the health probe
        preflight = {
            "verdict": "NO-GO",
            "reasons": ["The preflight check itself failed to run."],
            "components": {},
            "as_of": None,
            "reference": None,
        }
    preflight_s = (time.monotonic() - _t_preflight_start) if watchdog_active else None

    # ops-hardening iter-68 (J-07): the third sample, handler_compute_s -- t_handler_start (above) to
    # HERE, immediately before the response is constructed/returned, after every readiness/preflight
    # computation and DB read above (all already error-guarded, so this line is always reached whenever
    # the watchdog is active -- there is no partial/unreached case to handle). SAME degrade-on-error
    # convention: a watchdog write failure must never suppress, delay, or alter this route's own response.
    # iter-69: additionally passes the three sub-spans just timed above into the SAME record.
    if watchdog_active:
        try:
            health_watchdog.record_handler_compute(
                t_handler_start,
                time.monotonic(),
                t_received_wall,
                db_reads_s=db_reads_s,
                readiness_s=readiness_s,
                preflight_s=preflight_s,
            )
        except Exception:  # pragma: no cover - a watchdog write failure must never blank/break /health
            pass

    return {
        "status": "ok" if db_ok else "degraded",
        "db_ok": db_ok,
        "provider": provider,
        "last_run_date": last_run_date.isoformat() if last_run_date else None,
        "seed_latest_date": latest.isoformat() if latest else None,
        "symbol_count": symbol_count,
        # iter-28 (J-40): the single canonical readiness value (state + warm-up progress).
        "readiness": readiness["state"],
        # ops-hardening iter-4 (B3 fix): the sibling detail string -- null except for the new
        # `awaiting_snapshot` state (naming the condition + recovery action). Same computing module,
        # same endpoint -- `compute_readiness` already produced this; it was just never served before.
        "readiness_detail": readiness.get("detail"),
        "warmup": readiness["warmup"],
        # ops-hardening iter-24 (J-09): the historical background-dispatch registry's disclosure --
        # `compute_readiness` already composed this (degrading to the honest empty shape on its own
        # compute error); `.get(...)` with the SAME empty-shape fallback covers the (currently
        # unreachable, but defensive) case of an older cached/degraded readiness dict predating this key.
        "background_compute": readiness.get("background_compute", {"active": [], "recent_outcomes": []}),
        # the config-derived poll cadences the frontend badge derives its interval from (no client-side
        # poll literal — anti-goal: No magic numbers). `poll_interval_seconds` is the fast cadence used
        # while warming (so the flip to Ready shows within a poll of completion); `poll_idle_interval_
        # seconds` is the slower cadence the badge backs off to once Ready.
        "poll_interval_seconds": cfg.startup.health_poll_interval_seconds,
        "poll_idle_interval_seconds": cfg.startup.health_poll_idle_interval_seconds,
        # iter-33 (J-20): the single daily preflight verdict (additive) -- the layout-level
        # PreflightBanner's ONLY read path (see app.engine.readiness.compute_preflight).
        "preflight": preflight,
    }
