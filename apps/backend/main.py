"""Trendora FastAPI application — uvicorn entry `main:app`.

Run via `scripts/start-backend.sh` (uvicorn `main:app --app-dir apps/backend`). Startup order:
load config -> create tables -> load the committed seed if the DB is empty. The app reads
the offline `SeedProvider` only — it never touches the network on boot or a request. CORS
origins come from the `CORS_ORIGINS` env var set by the start script.
"""
from __future__ import annotations

import logging
import os
import signal
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    backtest,
    budget,
    dashboard,
    data,
    evidence,
    graveyard,
    health,
    indexes,
    market_phase,
    methodology,
    referee_audit,
    regime_history,
    registry,
    research,
    runs,
    sectors,
    stocks,
    themes,
    watchlist,
)
from app.config import load_config
from app.db import create_db_and_tables, get_engine
from app.engine.data_manager import sweep_orphaned_runs
from app.engine.warmup import ensure_latest_snapshot, start_warmup
from app.logging_config import configure_app_logging
from app.seed_loader import load_seed

# ops-hardening iter-39: attach a root-logger handler at INFO level BEFORE any `trendora.*`
# logger is used below (or by any imported engine module) — see `app.logging_config`'s own
# docstring for why this was needed (routine `.info()` calls were previously dropped silently).
configure_app_logging()

logger = logging.getLogger("trendora.lifespan")

# ops-hardening iter-41 (C7) — DIAGNOSTIC ONLY, opt-in via env var, never on by default: arms
# `faulthandler.register(SIGUSR1, all_threads=True)` so a throwaway-DB wedge-drill can send
# `kill -USR1 <pid>` to a suspected-frozen process and get an ALL-THREAD stack dump on stderr
# WITHOUT killing it — the exact tool iter-40's run 1 needed but didn't have (`gdb` attach was
# denied by this host's `yama.ptrace_scope` policy; no `py-spy` was installed). Deliberately NOT a
# launch-script change (AG-10's byte-frozen `scripts/start-backend.sh` stays untouched) — the drill
# sets `TRENDORA_DIAG_FAULTHANDLER_SIGUSR1=1` in its own environment before invoking that SAME
# unmodified script, which inherits it like any other env var. Every real deployment leaves this
# unset, so `signal.SIGUSR1` is never touched outside an explicit diagnostic drill.
if os.environ.get("TRENDORA_DIAG_FAULTHANDLER_SIGUSR1") == "1":
    import faulthandler

    faulthandler.register(signal.SIGUSR1, all_threads=True)
    logger.info("diagnostic: faulthandler armed on SIGUSR1 (TRENDORA_DIAG_FAULTHANDLER_SIGUSR1=1)")


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
    # J-60 boot sweep: mark any orphaned `running` DataProviderRun rows (a Data Manager job whose process
    # died mid-run) as `interrupted` — a fresh boot owns no in-flight jobs, so a `running` row found here
    # is by definition orphaned. Idempotent + non-fatal (a sweep failure never blocks the boot).
    try:
        swept = sweep_orphaned_runs(engine)
        if swept:
            logger.info("boot: swept %d orphaned 'running' job record(s) → 'interrupted'", swept)
    except Exception:  # noqa: BLE001 — the sweep is non-fatal; the server must still boot
        logger.warning("boot: orphaned-run sweep failed (non-fatal)", exc_info=True)
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


def _cors_origin_regex() -> str | None:
    """Optional DEV-ONLY origin-allow regex (J-108). When `./scripts/dev.sh` advertises the app at the
    machine's LAN IP (`http://<LAN_IP>:<frontendPort>`), a browser opened there sends that LAN-IP Origin
    on its `/api/health` (and every other) request — which a localhost-only `CORS_ORIGINS` list rejects,
    so the readiness badge sticks on "Backend unavailable". When `CORS_ORIGIN_REGEX` is set (dev.sh sets
    it to a private-LAN pattern), that LAN-IP frontend origin is also accepted. It is NOT set in
    production, so this widens nothing outside local development."""
    raw = os.environ.get("CORS_ORIGIN_REGEX", "").strip()
    return raw or None


def create_app() -> FastAPI:
    """Build the Trendora FastAPI app. A factory (not just a module-level singleton) so the CORS policy —
    which reads `CORS_ORIGINS` / `CORS_ORIGIN_REGEX` from the environment — is testable: a test can set
    the env and construct a fresh app to assert the allowed origins (J-108)."""
    application = FastAPI(title="Trendora API", version="0.1.0", lifespan=lifespan)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_origin_regex=_cors_origin_regex(),  # dev-only LAN-IP allowance (None in prod)
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )

    application.include_router(health.router, prefix="/api")
    application.include_router(sectors.router, prefix="/api")
    application.include_router(dashboard.router, prefix="/api")
    application.include_router(stocks.router, prefix="/api")
    application.include_router(themes.router, prefix="/api")
    application.include_router(runs.router, prefix="/api")
    application.include_router(backtest.router, prefix="/api")
    application.include_router(watchlist.router, prefix="/api")
    application.include_router(methodology.router, prefix="/api")
    application.include_router(data.router, prefix="/api")
    application.include_router(research.router, prefix="/api")
    application.include_router(regime_history.router, prefix="/api")
    application.include_router(indexes.router, prefix="/api")
    application.include_router(market_phase.router, prefix="/api")
    # goal-mcp-loop iter-1 — the read-only certified-claims ledger surface (GET /api/evidence).
    application.include_router(evidence.router, prefix="/api")
    # goal-mcp-loop iter-30 (J-18) — the read-only pre-registration registry (GET /api/research/registry).
    application.include_router(registry.router, prefix="/api")
    # goal-mcp-loop iter-31 (J-19) — the read-only negative-results graveyard (GET /api/research/graveyard).
    application.include_router(graveyard.router, prefix="/api")
    # goal-mcp-loop iter-32 (J-17) — the read-only certification-budget accounting panel
    # (GET /api/research/budget).
    application.include_router(budget.router, prefix="/api")
    # goal-mcp-loop iter-36 (J-22) — the read-only referee-calibration report
    # (GET /api/research/referee-audit).
    application.include_router(referee_audit.router, prefix="/api")
    return application


app = create_app()
