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
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlmodel import Session

from app.config import get_config
from app.db import get_engine, get_session
from app.engine.readiness import compute_preflight, compute_readiness, record_verdict_transition
from app.models import DailyPrice

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
def health(session: Session = Depends(get_session)) -> dict:
    cfg = get_config()
    provider = cfg.provider
    try:
        latest = session.scalar(select(func.max(DailyPrice.date)))
        symbol_count = _distinct_symbol_count(session)
        db_ok = True
    except Exception:  # pragma: no cover - DB unreachable is surfaced, never faked
        latest = None
        symbol_count = 0
        db_ok = False

    # The single honest readiness state + warm-up progress (computed once by the readiness producer).
    # `engine` lets it compute the expected cadence total when no warm-up record exists yet. A DB error
    # inside the producer degrades to `unavailable` (never a fabricated `ready`).
    try:
        readiness = compute_readiness(session, engine=get_engine())
    except Exception:  # pragma: no cover - never let a readiness error blank the health probe
        readiness = {
            "state": "unavailable",
            "detail": None,
            "warmup": {"done": 0, "total": 0, "status": "pending", "message": "history 0/0"},
            "background_compute": {"active": [], "recent_outcomes": []},
        }

    # iter-33 (J-20): the single daily preflight verdict (GO/DEGRADED/NO-GO + reasons). A compute error
    # degrades to an honest NO-GO — never a blank/fabricated field (anti-goal #8).
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

    return {
        "status": "ok" if db_ok else "degraded",
        "db_ok": db_ok,
        "provider": provider,
        "last_run_date": None,
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
