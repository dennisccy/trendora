"""GET /api/health — backend connectivity + offline-seed-spine status probe.

Carries no canonical score (per the blueprint Data Contract). Reports DB reachability, the
active provider, the latest seed date present, and how many symbols are loaded. `last_run_date`
is null until a scanner run exists (iter-5+).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import distinct, func, select
from sqlmodel import Session

from app.config import get_config
from app.db import get_session
from app.models import DailyPrice

router = APIRouter(tags=["health"])


@router.get("/health")
def health(session: Session = Depends(get_session)) -> dict:
    provider = get_config().provider
    try:
        latest = session.scalar(select(func.max(DailyPrice.date)))
        symbol_count = int(session.scalar(select(func.count(distinct(DailyPrice.symbol)))) or 0)
        db_ok = True
    except Exception:  # pragma: no cover - DB unreachable is surfaced, never faked
        latest = None
        symbol_count = 0
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "db_ok": db_ok,
        "provider": provider,
        "last_run_date": None,
        "seed_latest_date": latest.isoformat() if latest else None,
        "symbol_count": symbol_count,
    }
