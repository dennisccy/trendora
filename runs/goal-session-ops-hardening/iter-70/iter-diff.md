# Iteration diff (bounded)

Files changed: 10. Shown in full: 10.

```diff
diff --git a/apps/backend/app/api/health.py b/apps/backend/app/api/health.py
index f7a68240..f9a9291d 100644
--- a/apps/backend/app/api/health.py
+++ b/apps/backend/app/api/health.py
@@ -43,13 +43,20 @@ as only ~11% of its one breach's magnitude; this sample names the previously-unt
 SAME writer, SAME log file — no second instrument.
 
 ops-hardening iter-69 (J-07) decomposes that SAME `handler_compute_s` sample into its three constituent
-parts — `db_reads_s` (the three DB reads immediately below), `readiness_s` (the `compute_readiness` call),
-`preflight_s` (the `compute_preflight` call, including its own nested `record_verdict_transition` write —
-not split out this round) — timed with the SAME monotonic clock, wrapped around the SAME already-existing
-try/except blocks (so an internal exception, already caught and degraded below, still yields a real
-elapsed-time sample for that span rather than a partial/missing one). Written into the SAME
+parts — `db_reads_s` (the three DB reads immediately below), `readiness_s` (the readiness read),
+`preflight_s` (the preflight read) — timed with the SAME monotonic clock, wrapped around the SAME
+already-existing try/except blocks (so an internal exception, already caught and degraded below, still
+yields a real elapsed-time sample for that span rather than a partial/missing one). Written into the SAME
 `handler_compute` record via `record_handler_compute`'s new keyword-only params — no second flag, writer,
 or record type. Diagnostic-log-only: the response body/shape below is unaffected either way (TC-8).
+
+ops-hardening iter-70 (J-07) replaces the direct `compute_readiness`/`compute_preflight` calls (and the
+request-path `record_verdict_transition` write) with a single read from `app.engine.readiness`'s new
+bounded-interval background-refresh cache (`get_readiness_and_preflight`) — the SAME two producer
+functions, the SAME one endpoint, no second implementation. Under the new cached-read path `readiness_s`/
+`preflight_s` (above) time a cache-dict read, not a compute call — near-zero in steady state (TC-7), which
+is what keeps this endpoint answering promptly during a heavy background aggregate warm (J-07 step 2). The
+three DB reads below are unaffected (out of scope — iter-69's attribution never implicated them).
 """
 from __future__ import annotations
 
@@ -62,7 +69,7 @@ from sqlmodel import Session
 from app.config import get_config
 from app.db import get_engine, get_session
 from app.engine import health_watchdog
-from app.engine.readiness import compute_preflight, compute_readiness, record_verdict_transition
+from app.engine.readiness import get_readiness_and_preflight
 from app.models import DailyPrice, ScannerRun
 
 router = APIRouter(tags=["health"])
@@ -144,13 +151,17 @@ def health(session: Session = Depends(get_session), request: Request = None) ->
         db_ok = False
     db_reads_s = (time.monotonic() - _t_db_reads_start) if watchdog_active else None
 
-    # The single honest readiness state + warm-up progress (computed once by the readiness producer).
-    # `engine` lets it compute the expected cadence total when no warm-up record exists yet. A DB error
-    # inside the producer degrades to `unavailable` (never a fabricated `ready`).
-    # ops-hardening iter-69 (J-07): readiness_s -- wraps this SAME call, success or degraded alike.
+    # ops-hardening iter-70 (J-07): the single honest readiness state + warm-up progress, now served from
+    # `app.engine.readiness`'s bounded-interval background-refresh cache instead of computed on this
+    # request thread -- `get_readiness_and_preflight` degrades to the honest `unavailable` fallback shape
+    # on its own internal errors and never raises; this try/except is defensive belt-and-braces (mirrors
+    # every other block in this handler) and is what a test exercises by monkeypatching the accessor.
+    # ops-hardening iter-69 (J-07): readiness_s -- wraps this SAME call. Under the cached-read path this
+    # is a near-zero cache-dict read in steady state (TC-7), not a compute_readiness call.
     _t_readiness_start = time.monotonic() if watchdog_active else None
     try:
-        readiness = compute_readiness(session, engine=get_engine())
+        cached = get_readiness_and_preflight(session, engine=get_engine(), config=cfg)
+        readiness = cached["readiness"]
     except Exception:  # pragma: no cover - never let a readiness error blank the health probe
         readiness = {
             "state": "unavailable",
@@ -160,20 +171,15 @@ def health(session: Session = Depends(get_session), request: Request = None) ->
         }
     readiness_s = (time.monotonic() - _t_readiness_start) if watchdog_active else None
 
-    # iter-33 (J-20): the single daily preflight verdict (GO/DEGRADED/NO-GO + reasons). A compute error
-    # degrades to an honest NO-GO — never a blank/fabricated field (anti-goal #8).
-    # ops-hardening iter-69 (J-07): preflight_s -- wraps this SAME call AND its own nested
-    # record_verdict_transition write (not split into a fourth span this round, per spec).
+    # ops-hardening iter-70 (J-07): the single daily preflight verdict, read from the SAME cached payload
+    # fetched above (a bare dict-key access, not a second compute) — `record_verdict_transition`'s
+    # append-only, only-on-a-transition write now fires from INSIDE the background tick, never on this
+    # request path (moved alongside the compute itself).
+    # ops-hardening iter-69 (J-07): preflight_s -- wraps this SAME read.
     _t_preflight_start = time.monotonic() if watchdog_active else None
     try:
-        preflight = compute_preflight(session, config=cfg)
-        try:
-            # Append-only, ONLY on a transition (never on every ~2s poll) -- a history-write failure must
-            # never blank the health probe (mirrors the readiness try/except immediately above).
-            record_verdict_transition(preflight["verdict"], preflight["reasons"], preflight["reference"])
-        except Exception:  # pragma: no cover - a history-log write failure must never blank /health
-            pass
-    except Exception:  # pragma: no cover - never let a preflight error blank the health probe
+        preflight = cached["preflight"]
+    except Exception:  # pragma: no cover - never let a preflight read error blank the health probe
         preflight = {
             "verdict": "NO-GO",
             "reasons": ["The preflight check itself failed to run."],
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 9cbbddcb..cebf864d 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -580,15 +580,25 @@ class ReadinessCfg(BaseModel):
         verdict changes, never on every ~2s poll). A relative path resolves against the repo root; the
         `READINESS_VERDICT_HISTORY_PATH` env override takes precedence (test/gate seam — mirrors
         `app.engine.evidence.LEDGER_PATH_ENV`).
+      - `refresh_interval_seconds` (ops-hardening iter-70, J-07) — the bounded-interval background-refresh
+        cache's tick cadence (`app.engine.readiness`'s new daemon thread, started alongside
+        `app.engine.warmup.start_warmup`): how often `compute_readiness`/`compute_preflight` are
+        recomputed and published to the cache `GET /api/health` now reads from, instead of recomputing on
+        every request. MUST be well under `startup.health_poll_interval_seconds` (2.0s) so a fresh cached
+        value always predates the badge's next poll — MUST be `> 0`. Defaults to `0.5` (present so a
+        config fixture predating this field still loads unchanged — the established `extra="allow"`/
+        back-compat-default convention this class already uses, mirroring `StartupCfg`'s own
+        `background_compute_history_size` default).
 
     Boot-validated: `severity` must name exactly `{servability, freshness, integrity, drift}` with every
-    value one of `"degraded"`/`"no-go"`, covering both. An invalid block raises `ConfigError`, never a
-    silent default."""
+    value one of `"degraded"`/`"no-go"`, covering both, and `refresh_interval_seconds` must be `> 0`. An
+    invalid block raises `ConfigError`, never a silent default."""
 
     model_config = ConfigDict(extra="allow")
     freshness_max_age_days: int
     severity: dict[str, str]
     verdict_history_path: str
+    refresh_interval_seconds: float = 0.5
 
     @model_validator(mode="after")
     def _validate(self) -> "ReadinessCfg":
@@ -605,6 +615,8 @@ class ReadinessCfg(BaseModel):
                 "readiness.severity must configure at least one component as 'degraded' and at least "
                 "one as 'no-go' so the fixture matrix can induce both states"
             )
+        if self.refresh_interval_seconds <= 0:
+            raise ValueError("readiness.refresh_interval_seconds must be > 0")
         return self
 
 
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 6f1d0f18..af1b1535 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -4821,6 +4821,19 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
         # this job's peak footprint.
         _exit_ingest_heavy_warm(prog.job_id)
 
+    # ops-hardening iter-70 (J-07): immediate-refresh trigger for the readiness/preflight background-
+    # refresh cache -- the SAME finalize hook every other ingest-time aggregate above already refreshes
+    # from, so a job-completion state flip (e.g. awaiting_snapshot -> ready) is reflected within one tick
+    # rather than waiting up to a full readiness.refresh_interval_seconds period (TC-4). Deferred import
+    # (mirrors this module's own `indexes`/`market_phase` deferred-import convention): `readiness` imports
+    # `warmup`, which imports THIS module at load time, so a top-level import here would cycle. Reuses
+    # THIS session (not a fresh one) so the trigger sees this job's own just-persisted rows even before an
+    # outer caller's own commit. Non-fatal -- `trigger_readiness_refresh` never raises (mirrors this
+    # function's own "never raises" contract).
+    from app.engine import readiness as readiness_module
+
+    readiness_module.trigger_readiness_refresh(session, config=cfg)
+
     return refreshed
 
 
diff --git a/apps/backend/app/engine/readiness.py b/apps/backend/app/engine/readiness.py
index 86a2ce26..319b0074 100644
--- a/apps/backend/app/engine/readiness.py
+++ b/apps/backend/app/engine/readiness.py
@@ -34,7 +34,9 @@ progress and the analytics pages show their "warming up (n/m)" state — both re
 from __future__ import annotations
 
 import json
+import logging
 import os
+import threading
 from datetime import date as date_cls
 from pathlib import Path
 from typing import Optional
@@ -460,3 +462,212 @@ def record_verdict_transition(
         return False
     append_entry(resolved, {"verdict": verdict, "reasons": reasons, "reference": reference})
     return True
+
+
+# ====================================================================================================
+# Bounded-interval background-refresh cache (ops-hardening iter-70, J-07) -- serves `compute_readiness`/
+# `compute_preflight`'s combined output from a periodically-refreshed cache instead of recomputing them
+# synchronously on every `GET /api/health` request. iter-69's own watchdog sub-span instrumentation named
+# `readiness_s`/`preflight_s` as the dominant components (43/31 of 74 answered health-poll breaches, at
+# ~256x/~89x above idle p90) while a heavy background aggregate warm is live -- this closes that gap the
+# SAME way this session's other heavy computations were already moved off the request path: compute at a
+# bounded interval, publish to a cache, serve reads from storage (here, in-process memory, since
+# readiness/preflight are liveness state, not data that must survive a restart -- see the iter-70
+# assumption-ledger entry for the interpretation call).
+#
+# SAME two producers (`compute_readiness`/`compute_preflight`), SAME one endpoint (`GET /api/health`) --
+# this section adds ONLY a caching/scheduling layer around them, never a second implementation.
+# ====================================================================================================
+logger = logging.getLogger("trendora.readiness")
+
+
+def _log_tick_failure(msg: str) -> None:
+    """ops-hardening iter-70 AUDIT FIX (B1) — the SAME guard `data_manager._log_isolation_failure`
+    (iter-45, reviewer CRITICAL) already applies to every isolation handler inside
+    `_refresh_ingest_aggregates`, applied here for the SAME reason and the SAME reachable path.
+    `logger.exception()` formats and renders the FULL live traceback, which itself ALLOCATES; under the
+    exhausted `ulimit -v` cap that produced the exception being logged, that allocation can raise a SECOND
+    exception — and it is raised INSIDE the `except` clause, past the point that clause's own `try`
+    protects, so it propagates. Two callers below make that propagation matter: `_tick_and_cache`, reached
+    from `data_manager._refresh_ingest_aggregates`'s finalize hook (where an escape discards the whole
+    `refreshed` list, reporting a completed 17-minute finalize as zero aggregates refreshed), and
+    `_refresh_loop`, where an escape KILLS the daemon thread — leaving `GET /api/health` serving a frozen
+    cached value forever with no error surfaced anywhere. Full traceback first (unchanged behavior for
+    every normal failure); on ANY failure while logging, a minimal-allocation, traceback-free record; if
+    even that raises, give up silently — logging is diagnostic-only and must never itself be the reason a
+    "never raises" contract breaks."""
+    try:
+        logger.exception(msg)
+    except Exception:  # pragma: no cover - the logging allocation itself failed (memory pressure)
+        try:
+            logger.error(msg)
+        except Exception:  # pragma: no cover - nothing left to try; diagnostics are never load-bearing
+            pass
+
+# Serializes tick EXECUTION (compute + the verdict-transition write + the cache swap) -- guards against
+# two concurrent callers (the periodic background thread's own tick and an ingest finalize hook's
+# immediate-refresh trigger, `trigger_readiness_refresh` below) racing `record_verdict_transition`'s own
+# read-last-entry-then-maybe-append sequence (which would otherwise risk a duplicate transition record --
+# TC-5), and so two concurrent computes never interleave.
+_TICK_LOCK = threading.Lock()
+
+# The shared cache: the last completed tick's `{"readiness": ..., "preflight": ...}` payload, or `None`
+# before the first tick has ever completed in this process. A reader always gets either the PRIOR complete
+# payload or the NEW complete payload, never a torn mix of the two -- this single name is only ever
+# reassigned to a FRESH, fully-built dict (never mutated in place), and a bare name rebind is one atomic
+# bytecode operation under the GIL, so no lock is needed on the READ side.
+_READINESS_CACHE: Optional[dict] = None
+
+# Single-flight guard for the background thread's own lifecycle (mirrors `warmup._WARMUP_LOCK`'s shape).
+# Unlike warmup's one-shot job, this thread runs for the process's life -- `stop_readiness_refresh` (called
+# symmetrically from `main.lifespan`, mirroring the health-watchdog loop-lag probe's own start/cancel
+# shape) ends it cleanly, so repeated TestClient lifespan entries in tests each get a thread scoped to
+# their OWN engine rather than a stale thread from an earlier test/engine still ticking against a
+# torn-down DB.
+_REFRESH_LOCK = threading.Lock()
+_REFRESH_THREAD: Optional[threading.Thread] = None
+_REFRESH_STOP: Optional[threading.Event] = None
+
+
+def _compute_tick(session: Session, cfg: Config, engine=None) -> dict:
+    """One readiness+preflight compute -- byte-identical to the pre-cache per-request compute (the SAME
+    two producer calls), including the verdict-transition write (moved here from the request path -- SAME
+    dedup-against-last-recorded-verdict logic, SAME verdict-history file). This SAME body backs the
+    periodic background tick, the immediate-refresh trigger, and the cold-start synchronous fallback --
+    only the SCHEDULING differs between the three callers."""
+    readiness_result = compute_readiness(session, engine=engine, config=cfg)
+    preflight_result = compute_preflight(session, config=cfg)
+    try:
+        record_verdict_transition(
+            preflight_result["verdict"], preflight_result["reasons"], preflight_result["reference"]
+        )
+    except Exception:  # pragma: no cover - a history-log write failure must never break the tick
+        _log_tick_failure("readiness verdict-history write failed (non-fatal)")
+    return {"readiness": readiness_result, "preflight": preflight_result}
+
+
+def _tick_and_cache(session: Session, cfg: Config, engine=None) -> Optional[dict]:
+    """Run one tick and, on success, atomically publish it as the shared cache. Serialized by `_TICK_LOCK`
+    so two concurrent callers (the periodic thread and an ingest finalize hook's immediate trigger) never
+    interleave a compute or double-write a verdict transition (TC-5). Degrade-on-error (TC-6): a raising
+    compute is caught, logged, and leaves the PRIOR cache (if any) completely untouched -- the caller keeps
+    serving the last-known-good value, never a blank/partial one. Returns the fresh payload on success, or
+    `None` when the tick itself failed."""
+    global _READINESS_CACHE
+    with _TICK_LOCK:
+        try:
+            payload = _compute_tick(session, cfg, engine=engine)
+        except Exception:  # pragma: no cover - a tick failure must never crash the thread or blank the cache
+            _log_tick_failure("readiness refresh tick failed (non-fatal) -- serving last-known-good cache")
+            return None
+        _READINESS_CACHE = payload
+        return payload
+
+
+def get_readiness_and_preflight(session: Session, engine=None, config: Optional[Config] = None) -> dict:
+    """The SINGLE read accessor `GET /api/health` calls: serves `{"readiness": ..., "preflight": ...}`
+    from the shared cache. Cold-start fallback (TC-1): before the background thread's first tick
+    completes (boot, or a direct `health(session)` call with no thread running), computes once
+    synchronously here -- byte-identical to the pre-cache per-request behavior, so boot-time and
+    unit-test call shapes are unaffected. Never raises: even a first-ever tick failure (e.g. DB
+    unreachable at boot) degrades to the SAME honest fallback shape `compute_readiness`/`compute_preflight`
+    already produce on their own internal errors -- `GET /api/health` never serves an undefined value."""
+    cache = _READINESS_CACHE
+    if cache is not None:
+        return cache
+    cfg = config or get_config()
+    ticked = _tick_and_cache(session, cfg, engine=engine)
+    if ticked is not None:
+        return ticked
+    return {
+        "readiness": {
+            "state": UNAVAILABLE,
+            "detail": None,
+            "warmup": {"done": 0, "total": 0, "status": "pending", "message": "history 0/0"},
+            "background_compute": {"active": [], "recent_outcomes": []},
+        },
+        "preflight": {
+            "verdict": NO_GO,
+            "reasons": ["The preflight check itself failed to run."],
+            "components": {},
+            "as_of": None,
+            "reference": None,
+        },
+    }
+
+
+def trigger_readiness_refresh(session: Session, config: Optional[Config] = None, engine=None) -> None:
+    """Immediate-refresh trigger (TC-4): called from `data_manager._refresh_ingest_aggregates`'s own
+    finalize hook -- the SAME finalize hook every other ingest-time aggregate already refreshes from --
+    runs one tick right now (reusing the ingest job's OWN session, so it sees this job's just-persisted
+    rows) rather than waiting up to a full `readiness.refresh_interval_seconds` period for the periodic
+    thread's next tick. Non-fatal: `_tick_and_cache` already degrades a failure to a no-op (the prior
+    cache, if any, is left untouched) -- this never raises out into the calling ingest job."""
+    cfg = config or get_config()
+    _tick_and_cache(session, cfg, engine=engine)
+
+
+def _refresh_loop(engine, cfg: Config, stop: threading.Event) -> None:
+    """The background thread body: tick immediately (so the cache is warm as soon as possible after
+    boot), then repeat every `readiness.refresh_interval_seconds`, until `stop` is set. Opens its OWN
+    session per tick on `engine` (mirrors `warmup._run_warmup`'s own session-per-worker pattern) -- never
+    a request session."""
+    interval = cfg.readiness.refresh_interval_seconds
+    while not stop.is_set():
+        try:
+            with Session(engine) as session:
+                _tick_and_cache(session, cfg, engine=engine)
+        except Exception:  # pragma: no cover - opening the session itself must never kill the loop
+            _log_tick_failure("readiness refresh loop iteration failed (non-fatal)")
+        stop.wait(interval)
+
+
+def start_readiness_refresh(engine, config: Optional[Config] = None) -> None:
+    """Start the bounded-interval background-refresh daemon thread (single-flight: a re-entry while one
+    is already alive is a no-op, mirroring `warmup.start_warmup`'s guard shape). Started from the SAME
+    `lifespan` boot sequence that already starts `app.engine.warmup.start_warmup` -- reuses that existing
+    daemon-thread idiom, no second threading abstraction.
+
+    Resets the shared cache to `None` whenever it actually spawns a fresh thread (never on the single-
+    flight no-op path): a genuinely new boot must never go on serving a value some UNRELATED earlier
+    engine/process cached (`get_readiness_and_preflight`'s cold-start fallback then computes fresh,
+    synchronously, for the first request that lands before this boot's own first tick completes -- the
+    SAME TC-1 behavior a true process boot already relies on). In real deployment this reset is a no-op
+    (`start_readiness_refresh` runs exactly once per process, and the cache already starts `None`); it
+    matters only where one process re-enters `lifespan` repeatedly against DIFFERENT engines -- every
+    `TestClient` block in the test suite -- which is exactly the scenario that, unfixed, let one test's
+    monkeypatched/stale cached value leak into an unrelated later test's request."""
+    cfg = config or get_config()
+    global _REFRESH_THREAD, _REFRESH_STOP, _READINESS_CACHE
+    with _REFRESH_LOCK:
+        if _REFRESH_THREAD is not None and _REFRESH_THREAD.is_alive():
+            return
+        _READINESS_CACHE = None
+        stop = threading.Event()
+        thread = threading.Thread(
+            target=_refresh_loop, args=(engine, cfg, stop), daemon=True, name="readiness-refresh",
+        )
+        _REFRESH_STOP = stop
+        _REFRESH_THREAD = thread
+        thread.start()
+
+
+def stop_readiness_refresh(timeout: float = 2.0) -> None:
+    """Signal the background thread to stop and join briefly (best-effort -- mirrors `main.lifespan`'s
+    own `watchdog_task.cancel()` symmetry for the health-watchdog loop-lag probe). A thread mid-tick past
+    the timeout is left to finish on its own; it never blocks shutdown."""
+    global _REFRESH_THREAD, _REFRESH_STOP
+    with _REFRESH_LOCK:
+        stop = _REFRESH_STOP
+        thread = _REFRESH_THREAD
+    if stop is not None:
+        stop.set()
+    if thread is not None:
+        thread.join(timeout=timeout)
+
+
+def reset_readiness_refresh_cache() -> None:
+    """Test seam: clear the shared cache so the next `get_readiness_and_preflight` call takes the
+    cold-start synchronous path -- mirrors `reset_readiness_cache`'s existing cadence-memo reset above."""
+    global _READINESS_CACHE
+    _READINESS_CACHE = None
diff --git a/apps/backend/main.py b/apps/backend/main.py
index eff198d5..02257d3d 100644
--- a/apps/backend/main.py
+++ b/apps/backend/main.py
@@ -43,6 +43,7 @@ from app.config import load_config
 from app.db import create_db_and_tables, get_engine
 from app.engine import health_watchdog
 from app.engine.data_manager import sweep_orphaned_runs
+from app.engine.readiness import start_readiness_refresh, stop_readiness_refresh
 from app.engine.warmup import ensure_latest_snapshot, start_warmup
 from app.logging_config import configure_app_logging
 from app.seed_loader import load_seed
@@ -109,6 +110,12 @@ async def lifespan(app: FastAPI):
     # inside the worker; the server keeps serving persisted snapshots and the next boot finishes it).
     if latest is not None:
         start_warmup(engine, config)
+    # ops-hardening iter-70 (J-07): start the bounded-interval readiness/preflight background-refresh
+    # cache thread -- the SAME boot sequence that starts the warm-up above, reusing that daemon-thread
+    # idiom. Started unconditionally (even on an empty DB): `compute_readiness`/`compute_preflight`
+    # already degrade to their own honest `unavailable`/`NO-GO` shape when there is no data, so the cache
+    # is useful from its first tick regardless of `latest`.
+    start_readiness_refresh(engine, config)
     # ops-hardening iter-67 (J-07): the optional event-loop-lag probe -- started on THIS SAME event loop
     # (the one the health route is served from) only when TRENDORA_HEALTH_WATCHDOG=1. Returns None (no
     # task created) on the default path -- zero added overhead when unset.
@@ -119,6 +126,11 @@ async def lifespan(app: FastAPI):
             "(samples -> logs/health-watchdog.jsonl)"
         )
     yield
+    # ops-hardening iter-70 (J-07): stop the readiness-refresh thread symmetrically with its own start
+    # above -- mirrors the watchdog loop-lag probe's own start/cancel shape immediately below, so each
+    # lifespan entry/exit cycle (every TestClient block in tests; a real process's own shutdown) leaves no
+    # stale thread ticking against a torn-down engine.
+    stop_readiness_refresh()
     if watchdog_task is not None:
         watchdog_task.cancel()
         with contextlib.suppress(asyncio.CancelledError):
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 1bb28266..9f3ee9c5 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -1435,6 +1435,34 @@ def test_finalize_hook_index_series_second_run_hit_not_reported_as_refreshed(fin
     assert len(rows) == 1  # still exactly one row — the second run never wrote a duplicate
 
 
+# ==================================================================================================
+# ops-hardening iter-70 (J-07) -- the finalize hook fires the readiness/preflight cache's immediate-
+# refresh trigger, the SAME finalize hook every other ingest-time aggregate above already refreshes from.
+# ==================================================================================================
+def test_finalize_hook_triggers_immediate_readiness_refresh(finalize_hook_engine, monkeypatch):
+    """TC-4: `_refresh_ingest_aggregates` fires the readiness/preflight cache's immediate-refresh trigger
+    exactly once, with THIS SAME session (so it sees this job's just-persisted rows immediately), at the
+    end of the finalize hook. The cache's own correctness (cold-start, steady-state, degrade-on-error,
+    concurrency) is covered by test_readiness.py's dedicated tests; this test only proves the finalize
+    hook actually FIRES the trigger."""
+    import app.engine.readiness as readiness_module
+
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    calls: list[Session] = []
+
+    def _recording(session_arg, config=None, engine=None):
+        calls.append(session_arg)
+
+    monkeypatch.setattr(readiness_module, "trigger_readiness_refresh", _recording)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="readiness-trigger-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        data_manager._refresh_ingest_aggregates(session, cfg, prog)
+        assert len(calls) == 1
+        assert calls[0] is session  # the SAME session -- sees this job's just-persisted rows immediately
+
+
 def test_finalize_hook_index_series_memory_error_isolated_and_not_reported(
     finalize_hook_engine, monkeypatch
 ):
diff --git a/apps/backend/tests/test_health.py b/apps/backend/tests/test_health.py
index ede652bb..eb8ed0a2 100644
--- a/apps/backend/tests/test_health.py
+++ b/apps/backend/tests/test_health.py
@@ -196,15 +196,17 @@ def test_health_background_compute_serves_failed_outcome_verbatim(loaded_engine,
 
 
 def test_health_background_compute_degrades_honestly_when_readiness_fails(loaded_engine, monkeypatch):
-    """A total `compute_readiness` failure degrades the WHOLE readiness payload to `unavailable` (the
+    """A total readiness-cache-accessor failure degrades the WHOLE readiness payload to `unavailable` (the
     pre-existing convention) -- `background_compute` still serves the honest empty shape, never omitted
-    and never left dangling on a partially-constructed fallback dict."""
+    and never left dangling on a partially-constructed fallback dict. ops-hardening iter-70: the fault is
+    now injected at `get_readiness_and_preflight` (the cache accessor `health()` actually calls) rather
+    than `compute_readiness` directly, since the request path no longer calls that function itself."""
     import app.api.health as health_module
 
     def _boom(session, engine=None, config=None):
         raise RuntimeError("simulated readiness failure")
 
-    monkeypatch.setattr(health_module, "compute_readiness", _boom)
+    monkeypatch.setattr(health_module, "get_readiness_and_preflight", _boom)
     with TestClient(main.app) as client:
         body = client.get("/api/health").json()
     assert body["readiness"] == "unavailable"
@@ -341,3 +343,57 @@ def test_health_symbol_count_matches_naive_count_distinct_on_loaded_engine(loade
     with TestClient(main.app) as client:
         body = client.get("/api/health").json()
     assert body["symbol_count"] == naive
+
+
+# ==================================================================================================
+# ops-hardening iter-70 (J-07) -- GET /api/health reads the bounded-interval background-refresh cache
+# (app.engine.readiness) instead of computing readiness/preflight on the request thread.
+# ==================================================================================================
+def test_health_cold_start_direct_call_matches_live_compute(loaded_engine, tmp_path, monkeypatch):
+    """TC-1 at the handler level: with no completed tick (`readiness.reset_readiness_refresh_cache()`
+    forces the cold-start path), a direct `health(session)` call still returns a valid readiness/preflight
+    payload, computed synchronously -- byte-identical to a direct `compute_readiness`/`compute_preflight`
+    call taken immediately after (the DB is unchanged between the two calls)."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    readiness.reset_readiness_refresh_cache()
+    cfg = load_config()
+    with Session(loaded_engine) as session:
+        body = health(session)
+        direct_readiness = readiness.compute_readiness(session, config=cfg)
+        direct_preflight = readiness.compute_preflight(session, config=cfg)
+    assert body["readiness"] == direct_readiness["state"]
+    assert body["readiness_detail"] == direct_readiness["detail"]
+    assert body["preflight"] == direct_preflight
+
+
+def test_health_repeated_calls_serve_cache_not_recompute(loaded_engine, tmp_path, monkeypatch):
+    """TC-2 at the handler level: once the cache holds a completed tick, several direct `health(session)`
+    calls in a row never invoke `compute_readiness`/`compute_preflight` again -- proven by a
+    call-counting monkeypatch (mirrors test_readiness.py's own steady-state test), not merely by comparing
+    output values."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    readiness.reset_readiness_refresh_cache()
+    with Session(loaded_engine) as session:
+        health(session)  # warms the cache via the cold-start path
+    assert readiness._READINESS_CACHE is not None
+
+    calls = {"readiness": 0, "preflight": 0}
+    real_readiness = readiness.compute_readiness
+    real_preflight = readiness.compute_preflight
+
+    def _counting_readiness(*a, **kw):
+        calls["readiness"] += 1
+        return real_readiness(*a, **kw)
+
+    def _counting_preflight(*a, **kw):
+        calls["preflight"] += 1
+        return real_preflight(*a, **kw)
+
+    monkeypatch.setattr(readiness, "compute_readiness", _counting_readiness)
+    monkeypatch.setattr(readiness, "compute_preflight", _counting_preflight)
+
+    with Session(loaded_engine) as session:
+        for _ in range(10):
+            health(session)
+
+    assert calls == {"readiness": 0, "preflight": 0}
diff --git a/apps/backend/tests/test_health_watchdog.py b/apps/backend/tests/test_health_watchdog.py
index 11738f5d..6c700b85 100644
--- a/apps/backend/tests/test_health_watchdog.py
+++ b/apps/backend/tests/test_health_watchdog.py
@@ -286,7 +286,9 @@ def test_watchdog_sub_spans_captured_even_when_readiness_computation_raises(
     """Error case (iter-69): with the flag set, a request that hits an internal readiness-computation
     exception (already caught, degrading to `unavailable`) must still be logged with whatever sub-span
     samples were captured before/around the error -- readiness_s/preflight_s still time their own
-    (degraded) outcome, never a suppressed or partial record."""
+    (degraded) outcome, never a suppressed or partial record. ops-hardening iter-70: the fault is now
+    injected at `get_readiness_and_preflight` (the cache accessor `health()` actually calls under the new
+    cached-read path) rather than `compute_readiness` directly."""
     import app.api.health as health_module
 
     monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
@@ -297,7 +299,7 @@ def test_watchdog_sub_spans_captured_even_when_readiness_computation_raises(
     def _boom(session, engine=None, config=None):
         raise RuntimeError("simulated readiness failure")
 
-    monkeypatch.setattr(health_module, "compute_readiness", _boom)
+    monkeypatch.setattr(health_module, "get_readiness_and_preflight", _boom)
     fake_request = SimpleNamespace(state=SimpleNamespace(
         health_watchdog_t_received_monotonic=0.0,
         health_watchdog_t_received_wall="2026-08-12T00:00:00+00:00",
@@ -370,7 +372,9 @@ def test_watchdog_records_sample_even_when_readiness_computation_raises(watchdog
     the exception is caught INSIDE the endpoint (never escapes `health()`), execution still reaches the
     handler_compute_s recording point near the end of the function -- so a full (not partial) sample is
     captured for this request too, satisfying the iter-68 error-case requirement (whatever samples were
-    captured before/around the error are never suppressed)."""
+    captured before/around the error are never suppressed). ops-hardening iter-70: the fault is now
+    injected at `get_readiness_and_preflight` (the cache accessor `health()` actually calls under the new
+    cached-read path) rather than `compute_readiness` directly."""
     import app.api.health as health_module
 
     monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
@@ -381,7 +385,7 @@ def test_watchdog_records_sample_even_when_readiness_computation_raises(watchdog
     def _boom(session, engine=None, config=None):
         raise RuntimeError("simulated readiness failure")
 
-    monkeypatch.setattr(health_module, "compute_readiness", _boom)
+    monkeypatch.setattr(health_module, "get_readiness_and_preflight", _boom)
     fake_request = SimpleNamespace(state=SimpleNamespace(
         health_watchdog_t_received_monotonic=0.0,
         health_watchdog_t_received_wall="2026-08-12T00:00:00+00:00",
@@ -396,3 +400,33 @@ def test_watchdog_records_sample_even_when_readiness_computation_raises(watchdog
     handler_compute_samples = _handler_compute_entries(log_path)
     assert len(handler_compute_samples) == 1
     assert handler_compute_samples[0]["handler_compute_s"] >= 0
+
+
+# ======================================================================================================
+# ops-hardening iter-70 (J-07) -- under the NEW cached-read path, readiness_s/preflight_s read near-zero
+# (a cache-dict read, not a compute_readiness/compute_preflight call) while db_reads_s is unaffected. This
+# is the request-path half of the fix iter-69's own attribution motivated (readiness_s/preflight_s
+# dominated 43/31 of 74 answered health-poll breaches at ~256x/~89x above idle p90 during a heavy warm).
+# ======================================================================================================
+_NEAR_ZERO_CACHE_READ_CEILING_S = 0.01  # generous vs. a plain dict-key lookup; far below any real compute
+
+
+def test_readiness_and_preflight_sub_spans_read_near_zero_under_cached_path(
+    watchdog_engine, monkeypatch, tmp_path
+):
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    monkeypatch.setenv(health_watchdog.ENABLED_ENV, "1")
+    log_path = tmp_path / "health-watchdog.jsonl"
+    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))
+
+    app = main.create_app()
+    with TestClient(app) as client:
+        client.get("/api/health")  # warms the cache -- may itself be a cold-start compute
+        resp = client.get("/api/health")  # measured: must be a pure cache-dict read
+    assert resp.status_code == 200
+
+    entries = _handler_compute_entries(log_path)
+    assert len(entries) == 2
+    entry = entries[-1]  # the SECOND request's own record
+    assert entry["readiness_s"] < _NEAR_ZERO_CACHE_READ_CEILING_S
+    assert entry["preflight_s"] < _NEAR_ZERO_CACHE_READ_CEILING_S
diff --git a/apps/backend/tests/test_readiness.py b/apps/backend/tests/test_readiness.py
index ac64458a..6699a29a 100644
--- a/apps/backend/tests/test_readiness.py
+++ b/apps/backend/tests/test_readiness.py
@@ -16,6 +16,8 @@ and that `record_verdict_transition` appends ONLY on a verdict change (bounded g
 """
 from __future__ import annotations
 
+import threading
+import time
 from datetime import date, datetime, timedelta
 
 import pytest
@@ -683,3 +685,334 @@ def test_resolve_verdict_history_path_defaults_to_config(monkeypatch):
     cfg = load_config()
     resolved = resolve_verdict_history_path()
     assert resolved.endswith(cfg.readiness.verdict_history_path)
+
+
+# ==================================================================================================
+# ops-hardening iter-70 (J-07) -- config validation for the new readiness.refresh_interval_seconds knob
+# ==================================================================================================
+def test_readiness_cfg_refresh_interval_defaults_to_half_second():
+    from app.config import ReadinessCfg
+
+    cfg = ReadinessCfg(
+        freshness_max_age_days=5,
+        severity={"servability": "no-go", "freshness": "degraded", "integrity": "no-go", "drift": "degraded"},
+        verdict_history_path="x.jsonl",
+    )
+    assert cfg.refresh_interval_seconds == 0.5
+
+
+def test_readiness_cfg_rejects_nonpositive_refresh_interval():
+    from app.config import ReadinessCfg
+
+    with pytest.raises(ValueError, match="refresh_interval_seconds must be > 0"):
+        ReadinessCfg(
+            freshness_max_age_days=5,
+            severity={"servability": "no-go", "freshness": "degraded", "integrity": "no-go", "drift": "degraded"},
+            verdict_history_path="x.jsonl",
+            refresh_interval_seconds=0,
+        )
+
+
+# ==================================================================================================
+# ops-hardening iter-70 (J-07) -- bounded-interval background-refresh cache: cold-start fallback (TC-1),
+# steady-state cache-read vs. recompute (TC-2), concurrency/atomic-swap, degrade-on-error (TC-6), the
+# verdict-transition write firing exactly once under concurrent ticks (TC-5), the immediate-refresh
+# trigger, and the single-flight thread guard. A tiny, dedicated `cache_engine` fixture (NOT the shared
+# `loaded_engine`/`empty_engine`/etc. fixtures above) keeps these tests fast; an autouse fixture stops any
+# live background thread and resets the shared cache before AND after every test in this file, so nothing
+# here can leak a ticking thread or a stale cached value into another test module.
+# ==================================================================================================
+@pytest.fixture(autouse=True)
+def _isolated_readiness_cache():
+    readiness.stop_readiness_refresh()
+    readiness.reset_readiness_refresh_cache()
+    yield
+    readiness.stop_readiness_refresh()
+    readiness.reset_readiness_refresh_cache()
+
+
+@pytest.fixture
+def cache_engine(tmp_path, config):
+    """A tiny, fast, dedicated DB with one servable snapshot, for the background-refresh CACHE tests
+    only -- independent of the shared fixtures above."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'cache_test.db'}")
+    create_db_and_tables(engine)
+    benchmark = config.etfs.index[0]
+    d0 = date(2024, 3, 4)
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol=benchmark, date=d0, open=1, high=1, low=1, close=1, volume=1))
+        session.add(ScannerRun(
+            asof_date=d0, created_at=datetime(2024, 3, 4), provider="seed", benchmark=benchmark,
+            regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        ))
+        session.commit()
+    return engine
+
+
+def test_readiness_cache_cold_start_matches_direct_compute(cache_engine, config, monkeypatch, tmp_path):
+    """TC-1: before the background thread's first tick completes, `get_readiness_and_preflight` computes
+    once synchronously -- byte-identical to a direct `compute_readiness`/`compute_preflight` call taken
+    at the same moment (no thread has been started against `cache_engine` in this test)."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    with Session(cache_engine) as session:
+        cached = readiness.get_readiness_and_preflight(session, engine=cache_engine, config=config)
+        direct_readiness = compute_readiness(session, engine=cache_engine, config=config)
+        direct_preflight = compute_preflight(session, config=config)
+    assert cached["readiness"] == direct_readiness
+    assert cached["preflight"] == direct_preflight
+
+
+def test_readiness_cache_cold_start_never_raises_on_a_first_tick_failure(cache_engine, config, monkeypatch):
+    """A first-ever tick failure (before any completed tick exists) degrades to the SAME honest
+    unavailable/NO-GO fallback shape `compute_readiness`/`compute_preflight` already produce on their own
+    internal errors -- `get_readiness_and_preflight` never raises."""
+    def _boom(session, engine=None, config=None):
+        raise RuntimeError("simulated DB failure")
+
+    monkeypatch.setattr(readiness, "compute_readiness", _boom)
+    with Session(cache_engine) as session:
+        result = readiness.get_readiness_and_preflight(session, engine=cache_engine, config=config)
+    assert result["readiness"]["state"] == "unavailable"
+    assert result["preflight"]["verdict"] == "NO-GO"
+
+
+def test_readiness_cache_steady_state_reads_do_not_recompute(cache_engine, config, monkeypatch, tmp_path):
+    """TC-2: once the background thread has ticked at least once, repeated `get_readiness_and_preflight`
+    calls serve the SAME cached payload without re-invoking `compute_readiness`/`compute_preflight` --
+    proven by a call-counting monkeypatch (output-value equality alone would also hold under a per-call
+    recompute on an unchanging DB, so this proves the READ PATH itself, not just the result)."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    readiness.start_readiness_refresh(cache_engine, config)
+    deadline = time.monotonic() + 5.0
+    while readiness._READINESS_CACHE is None and time.monotonic() < deadline:
+        time.sleep(0.01)
+    assert readiness._READINESS_CACHE is not None, "background thread never completed its first tick"
+
+    calls = {"readiness": 0, "preflight": 0}
+    real_compute_readiness = readiness.compute_readiness
+    real_compute_preflight = readiness.compute_preflight
+
+    def _counting_readiness(*a, **kw):
+        calls["readiness"] += 1
+        return real_compute_readiness(*a, **kw)
+
+    def _counting_preflight(*a, **kw):
+        calls["preflight"] += 1
+        return real_compute_preflight(*a, **kw)
+
+    monkeypatch.setattr(readiness, "compute_readiness", _counting_readiness)
+    monkeypatch.setattr(readiness, "compute_preflight", _counting_preflight)
+
+    with Session(cache_engine) as session:
+        results = [
+            readiness.get_readiness_and_preflight(session, engine=cache_engine, config=config)
+            for _ in range(50)
+        ]
+    readiness.stop_readiness_refresh()  # before the NEXT (interval-away) tick could fire and get counted
+
+    assert calls == {"readiness": 0, "preflight": 0}
+    assert all(r == results[0] for r in results)
+
+
+def test_readiness_cache_degrades_to_last_known_good_on_tick_failure(cache_engine, config, monkeypatch, tmp_path):
+    """TC-6: a tick whose compute raises leaves the cache serving the PRIOR last-known-good value -- never
+    blanked, never raised out to the caller. The thread keeps ticking on schedule: once the failure clears,
+    the NEXT tick resumes normal cache updates."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    real_compute_readiness = readiness.compute_readiness
+    with Session(cache_engine) as session:
+        good = readiness._tick_and_cache(session, config, engine=cache_engine)
+    assert good is not None
+
+    def _boom(session, engine=None, config=None):
+        raise RuntimeError("simulated DB/ledger read failure")
+
+    monkeypatch.setattr(readiness, "compute_readiness", _boom)
+    with Session(cache_engine) as session:
+        failed = readiness._tick_and_cache(session, config, engine=cache_engine)
+    assert failed is None
+    assert readiness._READINESS_CACHE == good  # untouched by the failed tick
+
+    with Session(cache_engine) as session:
+        served = readiness.get_readiness_and_preflight(session, engine=cache_engine, config=config)
+    assert served == good  # a reader still gets the last-known-good value -- HTTP 200 shape intact
+
+    monkeypatch.setattr(readiness, "compute_readiness", real_compute_readiness)  # the failure clears
+    with Session(cache_engine) as session:
+        recovered = readiness._tick_and_cache(session, config, engine=cache_engine)
+    assert recovered is not None
+    assert readiness._READINESS_CACHE == recovered
+
+
+def test_readiness_cache_verdict_transition_fires_once_under_concurrent_ticks(
+    cache_engine, config, monkeypatch, tmp_path
+):
+    """TC-5: when the SAME new verdict is observed by two ticks racing concurrently (e.g. the periodic
+    thread and an ingest finalize hook's immediate-refresh trigger landing at the same instant),
+    `record_verdict_transition` still appends exactly ONE entry for that transition -- `_TICK_LOCK`
+    serializes the read-last-entry-then-maybe-append sequence so two concurrent ticks never both observe
+    'no transition recorded yet' and both append."""
+    history_path = tmp_path / "history.jsonl"
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(history_path))
+
+    def _fixed_preflight(session, config=None):
+        return {
+            "verdict": "DEGRADED", "reasons": ["forced"], "components": {},
+            "as_of": "2024-03-04", "reference": "2024-03-04",
+        }
+
+    monkeypatch.setattr(readiness, "compute_preflight", _fixed_preflight)
+
+    barrier = threading.Barrier(2)
+
+    def _run():
+        barrier.wait()
+        with Session(cache_engine) as session:
+            readiness._tick_and_cache(session, config, engine=cache_engine)
+
+    threads = [threading.Thread(target=_run) for _ in range(2)]
+    for t in threads:
+        t.start()
+    for t in threads:
+        t.join()
+
+    entries = read_entries(str(history_path))
+    assert [e["verdict"] for e in entries] == ["DEGRADED"]
+
+
+def test_readiness_cache_read_never_observes_a_torn_write(cache_engine, config, monkeypatch, tmp_path):
+    """Concurrency: a cache read on one thread never observes a torn/partial write from an in-flight tick
+    on another thread. `readiness["state"]` and `preflight["verdict"]` observed together in ONE read are
+    always tagged from the SAME tick (an incrementing counter shared by both crafted producers), never a
+    mix of two different ticks' halves -- proving the cache swap is atomic, not merely usually-fast."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    monkeypatch.setattr(readiness, "record_verdict_transition", lambda *a, **kw: False)
+    tick_counter = {"n": 0}
+
+    def _tagged_readiness(session, engine=None, config=None):
+        tick_counter["n"] += 1
+        tag = tick_counter["n"]
+        time.sleep(0.001)  # widen the window a torn read would need to land in
+        return {
+            "state": f"tag-{tag}", "detail": None,
+            "warmup": {"done": tag, "total": tag, "status": "ok", "message": f"history {tag}/{tag}"},
+            "background_compute": {"active": [], "recent_outcomes": []},
+        }
+
+    def _tagged_preflight(session, config=None):
+        tag = tick_counter["n"]  # the SAME counter value the readiness call just used
+        return {"verdict": f"tag-{tag}", "reasons": [], "components": {}, "as_of": None, "reference": None}
+
+    monkeypatch.setattr(readiness, "compute_readiness", _tagged_readiness)
+    monkeypatch.setattr(readiness, "compute_preflight", _tagged_preflight)
+
+    stop_flag = {"stop": False}
+    observed: list[dict] = []
+
+    def _writer():
+        with Session(cache_engine) as session:
+            while not stop_flag["stop"]:
+                readiness._tick_and_cache(session, config, engine=cache_engine)
+
+    def _reader():
+        with Session(cache_engine) as session:
+            for _ in range(200):
+                observed.append(readiness.get_readiness_and_preflight(session, engine=cache_engine, config=config))
+
+    writer_thread = threading.Thread(target=_writer)
+    reader_threads = [threading.Thread(target=_reader) for _ in range(4)]
+    writer_thread.start()
+    for t in reader_threads:
+        t.start()
+    for t in reader_threads:
+        t.join()
+    stop_flag["stop"] = True
+    writer_thread.join()
+
+    assert observed, "no reads were captured -- the test setup itself is broken"
+    for cached in observed:
+        readiness_tag = cached["readiness"]["state"].split("-")[1]
+        preflight_tag = cached["preflight"]["verdict"].split("-")[1]
+        assert readiness_tag == preflight_tag, f"torn read observed: {cached}"
+
+
+def test_trigger_readiness_refresh_updates_the_cache_immediately(cache_engine, config, monkeypatch, tmp_path):
+    """The immediate-refresh trigger (called from the ingest finalize hook) runs one tick right now and
+    publishes it to the shared cache -- TC-4's cache-level half (the finalize hook actually FIRING the
+    trigger is covered by test_data_manager.py's own dedicated test)."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    assert readiness._READINESS_CACHE is None
+    with Session(cache_engine) as session:
+        readiness.trigger_readiness_refresh(session, config=config, engine=cache_engine)
+    assert readiness._READINESS_CACHE is not None
+    assert readiness._READINESS_CACHE["readiness"]["state"] in {
+        "ready", "initializing", "unavailable", "awaiting_snapshot",
+    }
+
+
+def test_start_readiness_refresh_is_single_flight(cache_engine, config):
+    """Mirrors `warmup.start_warmup`'s own single-flight guard shape: a re-entry while the thread is
+    already alive is a no-op (no second concurrent thread spawned)."""
+    readiness.start_readiness_refresh(cache_engine, config)
+    first_thread = readiness._REFRESH_THREAD
+    readiness.start_readiness_refresh(cache_engine, config)
+    assert readiness._REFRESH_THREAD is first_thread
+    readiness.stop_readiness_refresh()
+    assert readiness._REFRESH_THREAD.is_alive() is False
+
+
+# ==================================================================================================
+# ops-hardening iter-70 AUDIT (finding B1) -- a tick failure whose OWN `logger.exception` render also
+# raises (the `MemoryError`-under-an-exhausted-`ulimit -v` class `data_manager._log_isolation_failure`
+# was built for in iter-45) must still not escape. Two callers make the escape matter: the ingest
+# finalize hook (`_refresh_ingest_aggregates` -> `trigger_readiness_refresh`), where an escape discards
+# the whole `refreshed` list, and `_refresh_loop`, where an escape kills the daemon thread and freezes
+# the cache forever with no error surfaced.
+# ==================================================================================================
+def test_tick_failure_never_escapes_even_when_its_own_logging_raises(cache_engine, config, monkeypatch, tmp_path):
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+
+    def _boom(session, engine=None, config=None):
+        raise MemoryError()
+
+    def _logging_also_boom(*a, **kw):
+        raise MemoryError()
+
+    monkeypatch.setattr(readiness, "compute_readiness", _boom)
+    monkeypatch.setattr(readiness.logger, "exception", _logging_also_boom)
+    monkeypatch.setattr(readiness.logger, "error", _logging_also_boom)
+
+    with Session(cache_engine) as session:
+        # `_tick_and_cache`'s own contract: returns None, never raises.
+        assert readiness._tick_and_cache(session, config, engine=cache_engine) is None
+        # the ingest finalize hook's contract: "never raises out into the calling ingest job".
+        readiness.trigger_readiness_refresh(session, config=config, engine=cache_engine)
+
+
+def test_refresh_loop_survives_a_tick_whose_logging_raises(cache_engine, config, monkeypatch, tmp_path):
+    """The background thread keeps ticking (and stays alive) even when both the tick AND its own failure
+    logging raise -- a dead thread would freeze the cache indefinitely while `GET /api/health` went on
+    serving the stale value with no error anywhere."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    ticks = {"n": 0}
+
+    def _boom(session, engine=None, config=None):
+        ticks["n"] += 1
+        raise MemoryError()
+
+    def _logging_also_boom(*a, **kw):
+        raise MemoryError()
+
+    monkeypatch.setattr(readiness, "compute_readiness", _boom)
+    monkeypatch.setattr(readiness.logger, "exception", _logging_also_boom)
+    monkeypatch.setattr(readiness.logger, "error", _logging_also_boom)
+
+    readiness.start_readiness_refresh(cache_engine, config)
+    deadline = time.monotonic() + 5.0
+    while ticks["n"] < 2 and time.monotonic() < deadline:
+        time.sleep(0.01)
+    assert ticks["n"] >= 2, "the refresh thread stopped ticking after the first failing tick"
+    assert readiness._REFRESH_THREAD.is_alive() is True
+    assert readiness._READINESS_CACHE is None  # never blanked into a partial/undefined value
+    readiness.stop_readiness_refresh()
diff --git a/config.yaml b/config.yaml
index 52bc63a5..291f5b77 100644
--- a/config.yaml
+++ b/config.yaml
@@ -1345,6 +1345,7 @@ readiness:
     integrity: no-go
     drift: degraded
   verdict_history_path: runs/goal-session-mcp-loop/state/preflight-verdict-history.jsonl
+  refresh_interval_seconds: 0.5    # ops-hardening iter-70 (J-07): background-refresh cache tick cadence -- well under startup.health_poll_interval_seconds (2.0s)
 
 # ----------------------------------------------------------------------------------------
 # iter-42 (J-100) CONSUMED — bounded-resource SERVER ops guards. The SINGLE source of the uvicorn
```
