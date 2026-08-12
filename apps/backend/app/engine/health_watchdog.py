"""Health-request-wait watchdog (ops-hardening iter-67, J-07) -- DIAGNOSTIC ONLY, off by default.

iter-66's own next-step order was explicit: the standalone-script profiling method (re-running the
suspect compute chain in isolation) has now produced TWO consecutive null results on two different
phases (iter-65 on `factor_lab_all_warm`, iter-66 on `coverage_membership_timeline_refresh`) -- a third
repeat has low expected value. The genuinely different method it ordered instead: watch the LIVE serving
process. This module instruments two things about that live process, from INSIDE it:

  1. **queue_wait_s** -- how long a `GET /api/health` request waits between arriving at the ASGI layer
     (`t_received`, timestamped by `HealthWatchdogMiddleware` at the very top of the middleware/dispatch
     chain, before Starlette's router -- and therefore the route handler body -- ever runs) and the route
     handler body actually starting to execute (`t_handler_start`, timestamped as the first statement
     inside `app.api.health.health()`, before the readiness computation runs).
  2. **loop_lag_s** -- how far the SAME event loop the health route is served from overruns a fixed 0.1s
     `asyncio.sleep` wake-up (`run_loop_lag_probe`), sampled continuously while the flag is set.

Both are DIAGNOSTIC ONLY: gated behind `TRENDORA_HEALTH_WATCHDOG=1` (unset/`0` -- the default -- adds NO
middleware to the ASGI stack, starts NO probe task, records NOTHING, costs NOTHING on the request path).
`app.engine.readiness`'s computed value and `GET /api/health`'s response body/shape are byte-identical
either way (TC-7) -- this module never touches what is computed or returned, only when. Samples are
appended as JSON lines to `logs/health-watchdog.jsonl` via the EXISTING append-only JSONL writer
(`app.engine.ledger.append_entry` -- no second implementation, mirrors
`app.engine.readiness.record_verdict_transition`'s own reuse of the same helper), one shared file with a
`type` discriminator (`"queue_wait"` / `"loop_lag"`) rather than two files.
"""
from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime, timezone
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import REPO_ROOT
from app.engine.ledger import append_entry

# The env var NAME that arms the watchdog (unset/"0" = today's exact behavior, checked fresh on every
# call -- never cached -- so a test can flip it per-case via `monkeypatch.setenv`).
ENABLED_ENV = "TRENDORA_HEALTH_WATCHDOG"

# Test/ops seam only (mirrors `app.engine.readiness.VERDICT_HISTORY_PATH_ENV` exactly) -- the NAME of an
# optional override, never a path VALUE literal in code.
LOG_PATH_ENV = "TRENDORA_HEALTH_WATCHDOG_LOG_PATH"

QUEUE_WAIT_TYPE = "queue_wait"
LOOP_LAG_TYPE = "loop_lag"
LOOP_LAG_INTERVAL_S = 0.1

_HEALTH_PATH = "/api/health"


def enabled() -> bool:
    """True iff `TRENDORA_HEALTH_WATCHDOG=1`."""
    return os.environ.get(ENABLED_ENV) == "1"


def resolve_log_path() -> str:
    """`TRENDORA_HEALTH_WATCHDOG_LOG_PATH` override if set, else `logs/health-watchdog.jsonl` resolved
    against `REPO_ROOT` -- mirrors `app.engine.readiness.resolve_verdict_history_path()` exactly."""
    override = os.environ.get(LOG_PATH_ENV)
    if override:
        return override
    return str(REPO_ROOT / "logs" / "health-watchdog.jsonl")


def record_queue_wait(
    t_received_monotonic: float, t_received_wall: str, t_handler_start_monotonic: float
) -> dict:
    """Append ONE queue-wait sample: `queue_wait_s = t_handler_start - t_received`, measured on the
    monotonic clock (never affected by wall-clock adjustments), timestamped with the REQUEST's own UTC
    arrival instant (`t_received_wall`) so a downstream join keys on the same instant
    `scripts/qa/poll_health.py` records for the SAME poll (TC-1/TC-2). Clamped to >= 0 as a defensive
    floor (a monotonic clock never goes backward). Returns the entry written (test convenience)."""
    queue_wait_s = max(0.0, t_handler_start_monotonic - t_received_monotonic)
    entry = {
        "type": QUEUE_WAIT_TYPE,
        "timestamp": t_received_wall,
        "queue_wait_s": round(queue_wait_s, 6),
    }
    append_entry(resolve_log_path(), entry)
    return entry


async def run_loop_lag_probe(
    interval_s: float = LOOP_LAG_INTERVAL_S, *, iterations: Optional[int] = None
) -> int:
    """Sleep `interval_s` in a loop on the CALLING event loop, appending one `loop_lag_s` sample per wake
    (actual wake time minus the expected one; a busy/contended loop wakes LATE, never early -- clamped to
    >= 0). Runs until cancelled (the production shape, started/cancelled by `main.py`'s lifespan around
    the SAME loop the health route is served from), or for exactly `iterations` wakes when given (a
    bounded, unit-testable synthetic run). Returns the count of samples written."""
    written = 0
    while iterations is None or written < iterations:
        expected_wake = time.monotonic() + interval_s
        await asyncio.sleep(interval_s)
        lag_s = max(0.0, time.monotonic() - expected_wake)
        append_entry(resolve_log_path(), {
            "type": LOOP_LAG_TYPE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "loop_lag_s": round(lag_s, 6),
        })
        written += 1
    return written


def start_loop_lag_probe() -> Optional["asyncio.Task"]:
    """Launch `run_loop_lag_probe` as a background task on the CURRENT running event loop. Returns None
    (starts nothing) when the flag is unset -- the default path never creates this task."""
    if not enabled():
        return None
    return asyncio.create_task(run_loop_lag_probe())


class HealthWatchdogMiddleware(BaseHTTPMiddleware):
    """Records `t_received` (monotonic + UTC wall-clock pair) for a `GET /api/health` request at the TOP
    of the middleware/dispatch chain -- before Starlette's router (and therefore the route handler body)
    ever runs -- and stashes it on `request.state` for `app.api.health.health()` to read. Only added to
    the ASGI stack at all when `TRENDORA_HEALTH_WATCHDOG=1` (see `main.create_app`), so the default path
    never pays for this middleware's presence. Every OTHER route passes straight through untouched (no
    timestamp taken) -- this is a health-route-scoped instrument, not a global request-timing middleware.
    """

    async def dispatch(self, request: Request, call_next):
        if request.url.path != _HEALTH_PATH:
            return await call_next(request)
        request.state.health_watchdog_t_received_monotonic = time.monotonic()
        request.state.health_watchdog_t_received_wall = datetime.now(timezone.utc).isoformat()
        return await call_next(request)
