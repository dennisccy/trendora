# Iteration diff (bounded)

Files changed: 4. Shown in full: 4.

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
diff --git a/apps/backend/app/engine/health_watchdog.py b/apps/backend/app/engine/health_watchdog.py
new file mode 100644
index 00000000..efce92e6
--- /dev/null
+++ b/apps/backend/app/engine/health_watchdog.py
@@ -0,0 +1,131 @@
+"""Health-request-wait watchdog (ops-hardening iter-67, J-07) -- DIAGNOSTIC ONLY, off by default.
+
+iter-66's own next-step order was explicit: the standalone-script profiling method (re-running the
+suspect compute chain in isolation) has now produced TWO consecutive null results on two different
+phases (iter-65 on `factor_lab_all_warm`, iter-66 on `coverage_membership_timeline_refresh`) -- a third
+repeat has low expected value. The genuinely different method it ordered instead: watch the LIVE serving
+process. This module instruments two things about that live process, from INSIDE it:
+
+  1. **queue_wait_s** -- how long a `GET /api/health` request waits between arriving at the ASGI layer
+     (`t_received`, timestamped by `HealthWatchdogMiddleware` at the very top of the middleware/dispatch
+     chain, before Starlette's router -- and therefore the route handler body -- ever runs) and the route
+     handler body actually starting to execute (`t_handler_start`, timestamped as the first statement
+     inside `app.api.health.health()`, before the readiness computation runs).
+  2. **loop_lag_s** -- how far the SAME event loop the health route is served from overruns a fixed 0.1s
+     `asyncio.sleep` wake-up (`run_loop_lag_probe`), sampled continuously while the flag is set.
+
+Both are DIAGNOSTIC ONLY: gated behind `TRENDORA_HEALTH_WATCHDOG=1` (unset/`0` -- the default -- adds NO
+middleware to the ASGI stack, starts NO probe task, records NOTHING, costs NOTHING on the request path).
+`app.engine.readiness`'s computed value and `GET /api/health`'s response body/shape are byte-identical
+either way (TC-7) -- this module never touches what is computed or returned, only when. Samples are
+appended as JSON lines to `logs/health-watchdog.jsonl` via the EXISTING append-only JSONL writer
+(`app.engine.ledger.append_entry` -- no second implementation, mirrors
+`app.engine.readiness.record_verdict_transition`'s own reuse of the same helper), one shared file with a
+`type` discriminator (`"queue_wait"` / `"loop_lag"`) rather than two files.
+"""
+from __future__ import annotations
+
+import asyncio
+import os
+import time
+from datetime import datetime, timezone
+from typing import Optional
+
+from starlette.middleware.base import BaseHTTPMiddleware
+from starlette.requests import Request
+
+from app.config import REPO_ROOT
+from app.engine.ledger import append_entry
+
+# The env var NAME that arms the watchdog (unset/"0" = today's exact behavior, checked fresh on every
+# call -- never cached -- so a test can flip it per-case via `monkeypatch.setenv`).
+ENABLED_ENV = "TRENDORA_HEALTH_WATCHDOG"
+
+# Test/ops seam only (mirrors `app.engine.readiness.VERDICT_HISTORY_PATH_ENV` exactly) -- the NAME of an
+# optional override, never a path VALUE literal in code.
+LOG_PATH_ENV = "TRENDORA_HEALTH_WATCHDOG_LOG_PATH"
+
+QUEUE_WAIT_TYPE = "queue_wait"
+LOOP_LAG_TYPE = "loop_lag"
+LOOP_LAG_INTERVAL_S = 0.1
+
+_HEALTH_PATH = "/api/health"
+
+
+def enabled() -> bool:
+    """True iff `TRENDORA_HEALTH_WATCHDOG=1`."""
+    return os.environ.get(ENABLED_ENV) == "1"
+
+
+def resolve_log_path() -> str:
+    """`TRENDORA_HEALTH_WATCHDOG_LOG_PATH` override if set, else `logs/health-watchdog.jsonl` resolved
+    against `REPO_ROOT` -- mirrors `app.engine.readiness.resolve_verdict_history_path()` exactly."""
+    override = os.environ.get(LOG_PATH_ENV)
+    if override:
+        return override
+    return str(REPO_ROOT / "logs" / "health-watchdog.jsonl")
+
+
+def record_queue_wait(
+    t_received_monotonic: float, t_received_wall: str, t_handler_start_monotonic: float
+) -> dict:
+    """Append ONE queue-wait sample: `queue_wait_s = t_handler_start - t_received`, measured on the
+    monotonic clock (never affected by wall-clock adjustments), timestamped with the REQUEST's own UTC
+    arrival instant (`t_received_wall`) so a downstream join keys on the same instant
+    `scripts/qa/poll_health.py` records for the SAME poll (TC-1/TC-2). Clamped to >= 0 as a defensive
+    floor (a monotonic clock never goes backward). Returns the entry written (test convenience)."""
+    queue_wait_s = max(0.0, t_handler_start_monotonic - t_received_monotonic)
+    entry = {
+        "type": QUEUE_WAIT_TYPE,
+        "timestamp": t_received_wall,
+        "queue_wait_s": round(queue_wait_s, 6),
+    }
+    append_entry(resolve_log_path(), entry)
+    return entry
+
+
+async def run_loop_lag_probe(
+    interval_s: float = LOOP_LAG_INTERVAL_S, *, iterations: Optional[int] = None
+) -> int:
+    """Sleep `interval_s` in a loop on the CALLING event loop, appending one `loop_lag_s` sample per wake
+    (actual wake time minus the expected one; a busy/contended loop wakes LATE, never early -- clamped to
+    >= 0). Runs until cancelled (the production shape, started/cancelled by `main.py`'s lifespan around
+    the SAME loop the health route is served from), or for exactly `iterations` wakes when given (a
+    bounded, unit-testable synthetic run). Returns the count of samples written."""
+    written = 0
+    while iterations is None or written < iterations:
+        expected_wake = time.monotonic() + interval_s
+        await asyncio.sleep(interval_s)
+        lag_s = max(0.0, time.monotonic() - expected_wake)
+        append_entry(resolve_log_path(), {
+            "type": LOOP_LAG_TYPE,
+            "timestamp": datetime.now(timezone.utc).isoformat(),
+            "loop_lag_s": round(lag_s, 6),
+        })
+        written += 1
+    return written
+
+
+def start_loop_lag_probe() -> Optional["asyncio.Task"]:
+    """Launch `run_loop_lag_probe` as a background task on the CURRENT running event loop. Returns None
+    (starts nothing) when the flag is unset -- the default path never creates this task."""
+    if not enabled():
+        return None
+    return asyncio.create_task(run_loop_lag_probe())
+
+
+class HealthWatchdogMiddleware(BaseHTTPMiddleware):
+    """Records `t_received` (monotonic + UTC wall-clock pair) for a `GET /api/health` request at the TOP
+    of the middleware/dispatch chain -- before Starlette's router (and therefore the route handler body)
+    ever runs -- and stashes it on `request.state` for `app.api.health.health()` to read. Only added to
+    the ASGI stack at all when `TRENDORA_HEALTH_WATCHDOG=1` (see `main.create_app`), so the default path
+    never pays for this middleware's presence. Every OTHER route passes straight through untouched (no
+    timestamp taken) -- this is a health-route-scoped instrument, not a global request-timing middleware.
+    """
+
+    async def dispatch(self, request: Request, call_next):
+        if request.url.path != _HEALTH_PATH:
+            return await call_next(request)
+        request.state.health_watchdog_t_received_monotonic = time.monotonic()
+        request.state.health_watchdog_t_received_wall = datetime.now(timezone.utc).isoformat()
+        return await call_next(request)
diff --git a/apps/backend/tests/test_health_watchdog.py b/apps/backend/tests/test_health_watchdog.py
new file mode 100644
index 00000000..58652cd2
--- /dev/null
+++ b/apps/backend/tests/test_health_watchdog.py
@@ -0,0 +1,214 @@
+"""ops-hardening iter-67 (J-07) -- the env-flag-gated health-request-wait watchdog.
+
+Tests the IN-SCOPE ask verbatim: (a) flag unset -> no `logs/health-watchdog.jsonl` entries, response
+unchanged; (b) flag set -> a request produces exactly one queue-wait record with `queue_wait_s >= 0`;
+(c) the loop-lag probe writes at least N records over a short synthetic interval. Plus TC-7 (byte-
+identity of the response body/shape regardless of the flag) and the error-case requirement (a
+readiness-computation exception must not suppress the already-captured queue-wait sample).
+
+Uses a LOCAL, lightweight `watchdog_engine` fixture rather than `conftest.py`'s session-scoped
+`loaded_engine` -- that fixture additionally bootstraps + backfills the FULL 30-year cadence
+(`bootstrap_runs` + `backfill_forward_returns`), which this file's tests do not need and which is
+documented to take up to ~1h on this host. These tests only need a genuinely servable `GET /api/health`
+through the REAL FastAPI lifespan, which itself only does the fast single-date latest-snapshot step
+synchronously (`ensure_latest_snapshot`) and dispatches the historical warm-up on a background thread --
+never blocking. `create_db_and_tables` + `load_seed` (the committed seed's bulk price load, ~30s) is the
+full cost this fixture pays, mirroring `conftest.py::loaded_engine` minus its two expensive extra steps.
+
+Mirrors `tests/test_cors_dev_lan.py`'s established pattern for env-driven app construction: build a
+FRESH app via `main.create_app()` AFTER `monkeypatch.setenv` (the shared `main.app` singleton is built
+once at import time, so it always reflects whatever the flag was at process start -- unset in this test
+process, which is exactly what the flag-unset tests below rely on).
+"""
+from __future__ import annotations
+
+import asyncio
+from types import SimpleNamespace
+
+import pytest
+from fastapi.testclient import TestClient
+from sqlmodel import Session
+
+import main
+from app import db as db_module
+from app.api.health import health
+from app.db import create_db_and_tables, make_engine
+from app.engine import health_watchdog, readiness
+from app.engine.ledger import read_entries
+from app.seed_loader import load_seed
+
+
+@pytest.fixture(scope="module")
+def watchdog_engine(tmp_path_factory, config):
+    """A fresh, isolated temp SQLite DB with the committed seed bulk-loaded but NOT bootstrapped to the
+    full historical cadence -- see module docstring for why this file uses this instead of
+    `conftest.py::loaded_engine`. Registered as the process engine so `TestClient`/`main.create_app()`
+    read it."""
+    db_path = tmp_path_factory.mktemp("watchdog_db") / "watchdog_test.db"
+    engine = make_engine(f"sqlite:///{db_path}")
+    create_db_and_tables(engine)
+    load_seed(engine, config)
+    db_module.set_engine(engine)
+    return engine
+
+
+def _queue_wait_entries(log_path) -> list[dict]:
+    return [e for e in read_entries(str(log_path)) if e.get("type") == health_watchdog.QUEUE_WAIT_TYPE]
+
+
+def _loop_lag_entries(log_path) -> list[dict]:
+    return [e for e in read_entries(str(log_path)) if e.get("type") == health_watchdog.LOOP_LAG_TYPE]
+
+
+# ======================================================================================================
+# (a) flag unset (the default) -- no log entries, response unchanged
+# ======================================================================================================
+def test_watchdog_disabled_by_default_writes_no_log(watchdog_engine, monkeypatch, tmp_path):
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    monkeypatch.delenv(health_watchdog.ENABLED_ENV, raising=False)
+    log_path = tmp_path / "health-watchdog.jsonl"
+    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))
+    assert health_watchdog.enabled() is False
+
+    with TestClient(main.app) as client:  # the shared singleton -- built with the flag off at import time
+        resp = client.get("/api/health")
+
+    assert resp.status_code == 200
+    assert not log_path.exists()
+
+
+def test_watchdog_direct_call_with_no_request_arg_is_untouched(watchdog_engine):
+    """The pre-existing direct-call test shape (`health(session)`, no `request`) still works -- the new
+    `request` param defaults to None, so a caller that never passes one (e.g. an older/simpler test) is
+    unaffected regardless of the flag."""
+    with Session(watchdog_engine) as session:
+        body = health(session)
+    assert body["status"] == "ok"
+
+
+# ======================================================================================================
+# (b) flag set -- exactly one queue-wait record per request, queue_wait_s >= 0
+# ======================================================================================================
+def test_watchdog_enabled_records_one_queue_wait_sample_per_request(watchdog_engine, monkeypatch, tmp_path):
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    monkeypatch.setenv(health_watchdog.ENABLED_ENV, "1")
+    log_path = tmp_path / "health-watchdog.jsonl"
+    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))
+
+    app = main.create_app()
+    with TestClient(app) as client:
+        resp = client.get("/api/health")
+    assert resp.status_code == 200
+
+    samples = _queue_wait_entries(log_path)
+    assert len(samples) == 1
+    assert samples[0]["queue_wait_s"] >= 0
+    assert isinstance(samples[0]["timestamp"], str) and samples[0]["timestamp"]
+
+
+def test_watchdog_enabled_records_one_sample_per_additional_request(watchdog_engine, monkeypatch, tmp_path):
+    """Two requests -> two samples (never batched, never deduped, never dropped)."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    monkeypatch.setenv(health_watchdog.ENABLED_ENV, "1")
+    log_path = tmp_path / "health-watchdog.jsonl"
+    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))
+
+    app = main.create_app()
+    with TestClient(app) as client:
+        client.get("/api/health")
+        client.get("/api/health")
+
+    assert len(_queue_wait_entries(log_path)) == 2
+
+
+def test_watchdog_only_instruments_the_health_route(watchdog_engine, monkeypatch, tmp_path):
+    """A different route (`/api/data`) passes straight through the middleware untouched -- this is a
+    health-route-scoped instrument, never a global request-timing middleware."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    monkeypatch.setenv(health_watchdog.ENABLED_ENV, "1")
+    log_path = tmp_path / "health-watchdog.jsonl"
+    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))
+
+    app = main.create_app()
+    with TestClient(app) as client:
+        client.get("/api/data")
+
+    assert _queue_wait_entries(log_path) == []
+
+
+# ======================================================================================================
+# (c) the loop-lag probe writes at least N records over a short synthetic interval
+# ======================================================================================================
+def test_loop_lag_probe_writes_at_least_n_records_over_short_interval(tmp_path, monkeypatch):
+    log_path = tmp_path / "watchdog.jsonl"
+    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))
+
+    written = asyncio.run(health_watchdog.run_loop_lag_probe(interval_s=0.01, iterations=5))
+
+    assert written == 5
+    samples = _loop_lag_entries(log_path)
+    assert len(samples) == 5
+    for sample in samples:
+        assert sample["loop_lag_s"] >= 0
+        assert isinstance(sample["timestamp"], str) and sample["timestamp"]
+
+
+# ======================================================================================================
+# TC-7 -- byte-identical response body/shape regardless of the flag. Direct function calls (not
+# TestClient) against the SAME session in immediate succession -- fully deterministic, no dependence on
+# a background warm-up thread's progress between two separate app/lifespan instances.
+# ======================================================================================================
+def test_watchdog_flag_never_changes_response_body_or_shape(watchdog_engine, monkeypatch, tmp_path):
+    monkeypatch.delenv(health_watchdog.ENABLED_ENV, raising=False)
+    with Session(watchdog_engine) as session:
+        off_body = health(session)  # no request -> flag-off shape, exactly like today
+
+    monkeypatch.setenv(health_watchdog.ENABLED_ENV, "1")
+    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(tmp_path / "watchdog.jsonl"))
+    fake_request = SimpleNamespace(state=SimpleNamespace(
+        health_watchdog_t_received_monotonic=0.0,
+        health_watchdog_t_received_wall="2026-08-12T00:00:00+00:00",
+    ))
+    with Session(watchdog_engine) as session:
+        on_body = health(session, request=fake_request)  # flag on, watchdog state present
+
+    existing_keys = {
+        "status", "db_ok", "provider", "last_run_date", "seed_latest_date", "symbol_count",
+        "readiness", "readiness_detail", "warmup", "poll_interval_seconds", "poll_idle_interval_seconds",
+        "preflight", "background_compute",
+    }
+    assert set(off_body) == existing_keys
+    assert set(on_body) == existing_keys
+    assert off_body == on_body  # the watchdog observes timing only -- never alters what is served
+
+
+# ======================================================================================================
+# Error case -- a readiness-computation exception must not suppress the already-captured sample
+# ======================================================================================================
+def test_watchdog_records_sample_even_when_readiness_computation_raises(watchdog_engine, monkeypatch, tmp_path):
+    """The watchdog's queue-wait record is written BEFORE readiness/preflight computation runs, so a
+    readiness-computation exception (already caught internally, degrading to `unavailable` -- this
+    endpoint's own pre-existing convention) never suppresses, delays, or alters the sample the watchdog
+    already captured, nor the route's own honest degraded response (AG-8: never a wedge)."""
+    import app.api.health as health_module
+
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    monkeypatch.setenv(health_watchdog.ENABLED_ENV, "1")
+    log_path = tmp_path / "watchdog.jsonl"
+    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))
+
+    def _boom(session, engine=None, config=None):
+        raise RuntimeError("simulated readiness failure")
+
+    monkeypatch.setattr(health_module, "compute_readiness", _boom)
+    fake_request = SimpleNamespace(state=SimpleNamespace(
+        health_watchdog_t_received_monotonic=0.0,
+        health_watchdog_t_received_wall="2026-08-12T00:00:00+00:00",
+    ))
+    with Session(watchdog_engine) as session:
+        body = health(session, request=fake_request)
+
+    assert body["readiness"] == "unavailable"  # the route's own error handling still degrades honestly
+    samples = _queue_wait_entries(log_path)
+    assert len(samples) == 1
+    assert samples[0]["queue_wait_s"] >= 0
```
