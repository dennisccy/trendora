"""Trendora FastAPI application — uvicorn entry `main:app`.

Run via `scripts/start-backend.sh` (uvicorn `main:app --app-dir apps/backend`). Startup order:
load config -> create tables -> load the committed seed if the DB is empty. The app reads
the offline `SeedProvider` only — it never touches the network on boot or a request. CORS
origins come from the `CORS_ORIGINS` env var set by the start script.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    backtest,
    dashboard,
    health,
    methodology,
    runs,
    sectors,
    stocks,
    system_health,
    themes,
    watchlist,
)
from app.config import load_config
from app.db import create_db_and_tables, get_engine
from app.engine.forward_testing import backfill_forward_returns
from app.engine.scanner import bootstrap_runs
from app.seed_loader import load_seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config()
    engine = get_engine()
    create_db_and_tables(engine)
    load_seed(engine, config)  # idempotent — no-op once the DB is populated
    # Persist an immutable snapshot per configured bootstrap date + the latest data date.
    # Idempotent: subsequent boots skip already-persisted dates.
    bootstrap_runs(engine, config)
    # Walk-forward (iter-6): persist the cadence as-of snapshots and INSERT their realized forward
    # returns into the append-only `forward_returns` table (idempotent; reads the frozen seed only).
    # Coexists with bootstrap_runs. A FRESH-DB first boot scans each cadence as-of date through the
    # full pipeline before serving, so it is slower than the bootstrap alone — accounted for in
    # readiness probing; subsequent boots skip already-persisted work and are fast.
    backfill_forward_returns(engine, config)
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
app.include_router(system_health.router, prefix="/api")
app.include_router(backtest.router, prefix="/api")
app.include_router(watchlist.router, prefix="/api")
app.include_router(methodology.router, prefix="/api")
