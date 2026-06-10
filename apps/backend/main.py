"""Trendora FastAPI application — uvicorn entry `main:app`.

Run via `scripts/start-backend.sh` (uvicorn `main:app --app-dir apps/backend`). Startup order:
load config -> create tables -> load the committed seed if the DB is empty. The app reads
the offline `SeedProvider` only — it never touches the network on boot or a request. CORS
origins come from the `CORS_ORIGINS` env var set by the start script.
"""
from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    backtest,
    dashboard,
    data,
    health,
    methodology,
    research,
    runs,
    sectors,
    stocks,
    themes,
    watchlist,
)
from app.config import load_config
from app.db import create_db_and_tables, get_engine
from app.engine.warmup import ensure_latest_snapshot, start_warmup
from app.seed_loader import load_seed

logger = logging.getLogger("trendora.lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # FAST-READY BOOT (iter-28, J-40): do ONLY the minimal synchronous work needed to serve the LATEST
    # as-of snapshot, then yield so the server begins accepting connections (it never blocks /health or
    # the core read pages on the multi-minute historical backfill). The full historical walk-forward —
    # the bootstrap cadence dates (minus the latest, done here) + forward-returns — warms up in the
    # BACKGROUND after yield, reusing the canonical engines (only the scheduling moves).
    config = load_config()
    engine = get_engine()
    create_db_and_tables(engine)
    load_seed(engine, config)  # idempotent — no-op once the DB is populated
    # The SINGLE minimal latest-snapshot step: persist (idempotently) ONLY the latest data date's
    # immutable snapshot so the read pages serve the latest as-of immediately. Instant on a warm DB; one
    # snapshot compute on a fresh DB, soft-bounded by config.startup.readiness_budget_seconds (logged on
    # overrun — the boot does NOT abort, so a cold DB still becomes serving-ready, just slower).
    started = time.monotonic()
    latest = ensure_latest_snapshot(engine, config)
    elapsed = time.monotonic() - started
    if latest is None:
        logger.warning("boot: no price data — readiness will report 'unavailable' until a seed is loaded")
    elif elapsed > config.startup.readiness_budget_seconds:
        logger.warning(
            "boot: latest-snapshot ready in %.1fs (over the %.1fs readiness budget) — serving anyway",
            elapsed, config.startup.readiness_budget_seconds,
        )
    # Launch the background historical warm-up (cadence snapshots + forward returns) AFTER the server is
    # already serving. It is idempotent, concurrency-safe, and NON-FATAL (a failure is caught + logged
    # inside the worker; the server keeps serving persisted snapshots and the next boot finishes it).
    if latest is not None:
        start_warmup(engine, config)
    yield


def _cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(title="Trendora API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

app.include_router(health.router, prefix="/api")
app.include_router(sectors.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(stocks.router, prefix="/api")
app.include_router(themes.router, prefix="/api")
app.include_router(runs.router, prefix="/api")
app.include_router(backtest.router, prefix="/api")
app.include_router(watchlist.router, prefix="/api")
app.include_router(methodology.router, prefix="/api")
app.include_router(data.router, prefix="/api")
app.include_router(research.router, prefix="/api")
