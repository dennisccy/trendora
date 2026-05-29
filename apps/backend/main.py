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

from app.api import dashboard, health, sectors
from app.config import load_config
from app.db import create_db_and_tables, get_engine
from app.seed_loader import load_seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config()
    engine = get_engine()
    create_db_and_tables(engine)
    load_seed(engine, config)  # idempotent — no-op once the DB is populated
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
