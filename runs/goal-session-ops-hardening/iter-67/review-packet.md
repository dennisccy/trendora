# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/app/api/health.py b/apps/backend/app/api/health.py
index 340c0151..7160acb8 100644
--- a/apps/backend/app/api/health.py
+++ b/apps/backend/app/api/health.py
@@ -28,15 +28,25 @@ ops-hardening iter-24 (J-09) additively extends this SAME endpoint with the `bac
 introduced (previously visible only by reconstructing it from raw DB timestamps). Degrades to
 `{"active": [], "recent_outcomes": []}` on any compute error — the SAME degrade-on-error convention as
 `readiness`/`preflight` above, never a blank/fabricated field.
+
+ops-hardening iter-67 (J-07) additively wires in the optional, env-flag-gated health-request-wait
+watchdog (`app.engine.health_watchdog`) — DIAGNOSTIC ONLY, off by default (`TRENDORA_HEALTH_WATCHDOG`
+unset/`0`). When armed it times how long THIS request waited between arriving at the ASGI layer and this
+handler body starting to execute, appending the sample to `logs/health-watchdog.jsonl` — it never
+changes what is computed or what this endpoint returns (the `request` param defaults to `None` so the
+pre-existing direct-call test shape, `health(session)`, is unaffected).
 """
 from __future__ import annotations
 
-from fastapi import APIRouter, Depends
+import time
+
+from fastapi import APIRouter, Depends, Request
 from sqlalchemy import func, select, text
 from sqlmodel import Session
 
 from app.config import get_config
 from app.db import get_engine, get_session
+from app.engine import health_watchdog
 from app.engine.readiness import compute_preflight, compute_readiness, record_verdict_transition
 from app.models import DailyPrice, ScannerRun
 
@@ -75,7 +85,25 @@ def _distinct_symbol_count(session: Session) -> int:
 
 
 @router.get("/health")
-def health(session: Session = Depends(get_session)) -> dict:
+def health(session: Session = Depends(get_session), request: Request = None) -> dict:
+    # ops-hardening iter-67 (J-07): the watchdog's own t_handler_start, taken BEFORE any of the
+    # readiness/preflight computation below runs, so a queue-wait sample is captured for THIS request
+    # regardless of what happens later in the handler (a readiness-computation exception is already
+    # caught below and degrades honestly -- it never reaches here). Only does anything when the flag is
+    # armed AND `HealthWatchdogMiddleware` actually ran for this request (real ASGI traffic); a
+    # direct-call test invoking `health(session)` with no `request` is untouched. A watchdog write
+    # failure must never suppress, delay, or alter this route's own response (AG-8: never a wedge) --
+    # mirrors this file's own existing degrade-on-error convention.
+    if health_watchdog.enabled() and request is not None:
+        try:
+            t_handler_start = time.monotonic()
+            t_received = getattr(request.state, "health_watchdog_t_received_monotonic", None)
+            t_received_wall = getattr(request.state, "health_watchdog_t_received_wall", None)
+            if t_received is not None and t_received_wall is not None:
+                health_watchdog.record_queue_wait(t_received, t_received_wall, t_handler_start)
+        except Exception:  # pragma: no cover - a watchdog write failure must never blank/break /health
+            pass
+
     cfg = get_config()
     provider = cfg.provider
     try:
diff --git a/apps/backend/main.py b/apps/backend/main.py
index bf408ff2..eff198d5 100644
--- a/apps/backend/main.py
+++ b/apps/backend/main.py
@@ -7,6 +7,8 @@ origins come from the `CORS_ORIGINS` env var set by the start script.
 """
 from __future__ import annotations
 
+import asyncio
+import contextlib
 import logging
 import os
 import signal
@@ -39,6 +41,7 @@ from app.api import (
 )
 from app.config import load_config
 from app.db import create_db_and_tables, get_engine
+from app.engine import health_watchdog
 from app.engine.data_manager import sweep_orphaned_runs
 from app.engine.warmup import ensure_latest_snapshot, start_warmup
 from app.logging_config import configure_app_logging
@@ -106,7 +109,20 @@ async def lifespan(app: FastAPI):
     # inside the worker; the server keeps serving persisted snapshots and the next boot finishes it).
     if latest is not None:
         start_warmup(engine, config)
+    # ops-hardening iter-67 (J-07): the optional event-loop-lag probe -- started on THIS SAME event loop
+    # (the one the health route is served from) only when TRENDORA_HEALTH_WATCHDOG=1. Returns None (no
+    # task created) on the default path -- zero added overhead when unset.
+    watchdog_task = health_watchdog.start_loop_lag_probe()
+    if watchdog_task is not None:
+        logger.info(
+            "health watchdog: TRENDORA_HEALTH_WATCHDOG=1 -- loop-lag probe started "
+            "(samples -> logs/health-watchdog.jsonl)"
+        )
     yield
+    if watchdog_task is not None:
+        watchdog_task.cancel()
+        with contextlib.suppress(asyncio.CancelledError):
+            await watchdog_task
 
 
 def _cors_origins() -> list[str]:
@@ -139,6 +155,12 @@ def create_app() -> FastAPI:
         allow_headers=["*"],
         allow_credentials=False,
     )
+    # ops-hardening iter-67 (J-07): the health-request-wait watchdog middleware is added to the ASGI
+    # stack ONLY when TRENDORA_HEALTH_WATCHDOG=1 -- read once here, at app-construction time (mirrors
+    # `_cors_origins`/`_cors_origin_regex` above). The default (unset) path never installs it, so it
+    # costs nothing on every other request.
+    if health_watchdog.enabled():
+        application.add_middleware(health_watchdog.HealthWatchdogMiddleware)
 
     application.include_router(health.router, prefix="/api")
     application.include_router(sectors.router, prefix="/api")
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 175 +++++++++++++++++++++
 ...al-ops-hardening-iter-66-ui-test-results.llm.md |  27 ++++
 ...e-goal-ops-hardening-iter-66-ui-test-results.md |  10 +-
 runs/goal-session-ops-hardening/telemetry.jsonl    |   7 +
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   1 +
 6 files changed, 220 insertions(+), 2 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
