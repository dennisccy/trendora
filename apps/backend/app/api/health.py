"""GET /api/health — backend connectivity + offline-seed-spine status + readiness (iter-28, J-40).

Carries no canonical score (per the blueprint Data Contract). Reports DB reachability, the active
provider, the latest seed date present, and how many symbols are loaded. `last_run_date` is null until a
scanner run exists (iter-5+).

iter-28 (J-40) extends this SINGLE canonical endpoint with the honest backend `readiness` state ∈
{`ready`, `initializing`, `unavailable`} + the background warm-up progress `warmup {done, total, status,
message}`, both computed ONCE by `app.engine.readiness.compute_readiness` (the single readiness producer)
— there is NO second readiness read path. The frontend readiness badge and the Backtest/Research
"warming up (n/m)" states are the ONLY readers; the frontend never computes readiness itself.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import distinct, func, select
from sqlmodel import Session

from app.config import get_config
from app.db import get_engine, get_session
from app.engine.readiness import compute_readiness
from app.models import DailyPrice

router = APIRouter(tags=["health"])


@router.get("/health")
def health(session: Session = Depends(get_session)) -> dict:
    cfg = get_config()
    provider = cfg.provider
    try:
        latest = session.scalar(select(func.max(DailyPrice.date)))
        symbol_count = int(session.scalar(select(func.count(distinct(DailyPrice.symbol)))) or 0)
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
            "warmup": {"done": 0, "total": 0, "status": "pending", "message": "history 0/0"},
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
        "warmup": readiness["warmup"],
        # the config-derived poll cadences the frontend badge derives its interval from (no client-side
        # poll literal — anti-goal: No magic numbers). `poll_interval_seconds` is the fast cadence used
        # while warming (so the flip to Ready shows within a poll of completion); `poll_idle_interval_
        # seconds` is the slower cadence the badge backs off to once Ready.
        "poll_interval_seconds": cfg.startup.health_poll_interval_seconds,
        "poll_idle_interval_seconds": cfg.startup.health_poll_idle_interval_seconds,
    }
