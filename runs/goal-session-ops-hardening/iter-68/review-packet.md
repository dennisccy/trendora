# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/apps/backend/app/api/health.py b/apps/backend/app/api/health.py
index 7160acb8..8574f260 100644
--- a/apps/backend/app/api/health.py
+++ b/apps/backend/app/api/health.py
@@ -35,6 +35,12 @@ unset/`0`). When armed it times how long THIS request waited between arriving at
 handler body starting to execute, appending the sample to `logs/health-watchdog.jsonl` — it never
 changes what is computed or what this endpoint returns (the `request` param defaults to `None` so the
 pre-existing direct-call test shape, `health(session)`, is unaffected).
+
+ops-hardening iter-68 (J-07) additively extends the SAME watchdog with a third sample, `handler_compute_s`
+— from the SAME `t_handler_start` to immediately before this function returns (after the readiness/
+preflight computation and DB reads above, before serialization). iter-67's own drill named `queue_wait_s`
+as only ~11% of its one breach's magnitude; this sample names the previously-untimed remainder. SAME flag,
+SAME writer, SAME log file — no second instrument.
 """
 from __future__ import annotations
 
@@ -86,17 +92,21 @@ def _distinct_symbol_count(session: Session) -> int:
 
 @router.get("/health")
 def health(session: Session = Depends(get_session), request: Request = None) -> dict:
-    # ops-hardening iter-67 (J-07): the watchdog's own t_handler_start, taken BEFORE any of the
+    # ops-hardening iter-67/68 (J-07): the watchdog's own t_handler_start, taken BEFORE any of the
     # readiness/preflight computation below runs, so a queue-wait sample is captured for THIS request
     # regardless of what happens later in the handler (a readiness-computation exception is already
     # caught below and degrades honestly -- it never reaches here). Only does anything when the flag is
     # armed AND `HealthWatchdogMiddleware` actually ran for this request (real ASGI traffic); a
     # direct-call test invoking `health(session)` with no `request` is untouched. A watchdog write
     # failure must never suppress, delay, or alter this route's own response (AG-8: never a wedge) --
-    # mirrors this file's own existing degrade-on-error convention.
-    if health_watchdog.enabled() and request is not None:
+    # mirrors this file's own existing degrade-on-error convention. `t_handler_start`/`t_received_wall`
+    # are kept (not scoped to this block) so the iter-68 `handler_compute_s` sample near the bottom of
+    # this function can time against the SAME start instant.
+    watchdog_active = health_watchdog.enabled() and request is not None
+    t_handler_start = time.monotonic() if watchdog_active else None
+    t_received_wall = None
+    if watchdog_active:
         try:
-            t_handler_start = time.monotonic()
             t_received = getattr(request.state, "health_watchdog_t_received_monotonic", None)
             t_received_wall = getattr(request.state, "health_watchdog_t_received_wall", None)
             if t_received is not None and t_received_wall is not None:
@@ -152,6 +162,17 @@ def health(session: Session = Depends(get_session), request: Request = None) ->
             "reference": None,
         }
 
+    # ops-hardening iter-68 (J-07): the third sample, handler_compute_s -- t_handler_start (above) to
+    # HERE, immediately before the response is constructed/returned, after every readiness/preflight
+    # computation and DB read above (all already error-guarded, so this line is always reached whenever
+    # the watchdog is active -- there is no partial/unreached case to handle). SAME degrade-on-error
+    # convention: a watchdog write failure must never suppress, delay, or alter this route's own response.
+    if watchdog_active:
+        try:
+            health_watchdog.record_handler_compute(t_handler_start, time.monotonic(), t_received_wall)
+        except Exception:  # pragma: no cover - a watchdog write failure must never blank/break /health
+            pass
+
     return {
         "status": "ok" if db_ok else "degraded",
         "db_ok": db_ok,
diff --git a/apps/backend/app/engine/health_watchdog.py b/apps/backend/app/engine/health_watchdog.py
index efce92e6..2275af9f 100644
--- a/apps/backend/app/engine/health_watchdog.py
+++ b/apps/backend/app/engine/health_watchdog.py
@@ -1,10 +1,10 @@
-"""Health-request-wait watchdog (ops-hardening iter-67, J-07) -- DIAGNOSTIC ONLY, off by default.
+"""Health-request-wait watchdog (ops-hardening iter-67/68, J-07) -- DIAGNOSTIC ONLY, off by default.
 
 iter-66's own next-step order was explicit: the standalone-script profiling method (re-running the
 suspect compute chain in isolation) has now produced TWO consecutive null results on two different
 phases (iter-65 on `factor_lab_all_warm`, iter-66 on `coverage_membership_timeline_refresh`) -- a third
 repeat has low expected value. The genuinely different method it ordered instead: watch the LIVE serving
-process. This module instruments two things about that live process, from INSIDE it:
+process. This module instruments three things about that live process, from INSIDE it:
 
   1. **queue_wait_s** -- how long a `GET /api/health` request waits between arriving at the ASGI layer
      (`t_received`, timestamped by `HealthWatchdogMiddleware` at the very top of the middleware/dispatch
@@ -13,15 +13,20 @@ process. This module instruments two things about that live process, from INSIDE
      inside `app.api.health.health()`, before the readiness computation runs).
   2. **loop_lag_s** -- how far the SAME event loop the health route is served from overruns a fixed 0.1s
      `asyncio.sleep` wake-up (`run_loop_lag_probe`), sampled continuously while the flag is set.
-
-Both are DIAGNOSTIC ONLY: gated behind `TRENDORA_HEALTH_WATCHDOG=1` (unset/`0` -- the default -- adds NO
-middleware to the ASGI stack, starts NO probe task, records NOTHING, costs NOTHING on the request path).
-`app.engine.readiness`'s computed value and `GET /api/health`'s response body/shape are byte-identical
-either way (TC-7) -- this module never touches what is computed or returned, only when. Samples are
-appended as JSON lines to `logs/health-watchdog.jsonl` via the EXISTING append-only JSONL writer
-(`app.engine.ledger.append_entry` -- no second implementation, mirrors
+  3. **handler_compute_s** (iter-68) -- how long the handler BODY itself takes, from the SAME
+     `t_handler_start` (above) to immediately before the route returns its response -- after the
+     readiness/preflight computation and any DB reads, before serialization. iter-67's own drill found
+     `queue_wait_s` named only ~11% of its one 2.875s breach's magnitude; this sample names the component
+     covering the rest -- the handler body's own execution, previously untimed.
+
+All three are DIAGNOSTIC ONLY: gated behind `TRENDORA_HEALTH_WATCHDOG=1` (unset/`0` -- the default --
+adds NO middleware to the ASGI stack, starts NO probe task, records NOTHING, costs NOTHING on the request
+path). `app.engine.readiness`'s computed value and `GET /api/health`'s response body/shape are
+byte-identical either way (TC-7) -- this module never touches what is computed or returned, only when.
+Samples are appended as JSON lines to `logs/health-watchdog.jsonl` via the EXISTING append-only JSONL
+writer (`app.engine.ledger.append_entry` -- no second implementation, mirrors
 `app.engine.readiness.record_verdict_transition`'s own reuse of the same helper), one shared file with a
-`type` discriminator (`"queue_wait"` / `"loop_lag"`) rather than two files.
+`type` discriminator (`"queue_wait"` / `"loop_lag"` / `"handler_compute"`) rather than separate files.
 """
 from __future__ import annotations
 
@@ -47,6 +52,7 @@ LOG_PATH_ENV = "TRENDORA_HEALTH_WATCHDOG_LOG_PATH"
 
 QUEUE_WAIT_TYPE = "queue_wait"
 LOOP_LAG_TYPE = "loop_lag"
+HANDLER_COMPUTE_TYPE = "handler_compute"
 LOOP_LAG_INTERVAL_S = 0.1
 
 _HEALTH_PATH = "/api/health"
@@ -84,6 +90,28 @@ def record_queue_wait(
     return entry
 
 
+def record_handler_compute(
+    t_handler_start_monotonic: float, t_before_return_monotonic: float, t_received_wall: Optional[str] = None
+) -> dict:
+    """Append ONE handler-compute sample (iter-68): `handler_compute_s = t_before_return -
+    t_handler_start`, measured on the monotonic clock, from `t_handler_start` (the SAME timestamp
+    `record_queue_wait` above already uses, taken as the first statement inside
+    `app.api.health.health()`) to immediately before the route returns its response -- after the
+    readiness/preflight computation and any DB reads, before serialization. Timestamped with the SAME
+    request's own UTC arrival instant (`t_received_wall`) as its sibling `queue_wait_s` sample for the
+    SAME request, so a downstream join keys both on the identical instant (TC-1/TC-2) rather than a
+    nearest-neighbor match. Clamped to >= 0 as a defensive floor. Returns the entry written (test
+    convenience)."""
+    handler_compute_s = max(0.0, t_before_return_monotonic - t_handler_start_monotonic)
+    entry = {
+        "type": HANDLER_COMPUTE_TYPE,
+        "timestamp": t_received_wall,
+        "handler_compute_s": round(handler_compute_s, 6),
+    }
+    append_entry(resolve_log_path(), entry)
+    return entry
+
+
 async def run_loop_lag_probe(
     interval_s: float = LOOP_LAG_INTERVAL_S, *, iterations: Optional[int] = None
 ) -> int:
diff --git a/apps/backend/tests/test_health_watchdog.py b/apps/backend/tests/test_health_watchdog.py
index 58652cd2..d94cf7dc 100644
--- a/apps/backend/tests/test_health_watchdog.py
+++ b/apps/backend/tests/test_health_watchdog.py
@@ -60,6 +60,10 @@ def _loop_lag_entries(log_path) -> list[dict]:
     return [e for e in read_entries(str(log_path)) if e.get("type") == health_watchdog.LOOP_LAG_TYPE]
 
 
+def _handler_compute_entries(log_path) -> list[dict]:
+    return [e for e in read_entries(str(log_path)) if e.get("type") == health_watchdog.HANDLER_COMPUTE_TYPE]
+
+
 # ======================================================================================================
 # (a) flag unset (the default) -- no log entries, response unchanged
 # ======================================================================================================
@@ -153,6 +157,66 @@ def test_loop_lag_probe_writes_at_least_n_records_over_short_interval(tmp_path,
         assert isinstance(sample["timestamp"], str) and sample["timestamp"]
 
 
+# ======================================================================================================
+# (d) handler_compute_s (iter-68) -- the third sample, t_handler_start to immediately before the route
+# returns its response. Per the iter-68 IN SCOPE ask verbatim: (a) flag unset -- no handler_compute_s
+# entry, response unchanged; (b) flag set -- exactly one handler_compute_s record with
+# handler_compute_s >= 0, alongside the existing queue_wait_s record for the SAME request.
+# ======================================================================================================
+def test_watchdog_disabled_writes_no_handler_compute_entry(watchdog_engine, monkeypatch, tmp_path):
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
+    assert not log_path.exists()  # neither queue_wait_s, loop_lag_s, nor handler_compute_s is written
+
+
+def test_watchdog_enabled_records_handler_compute_alongside_queue_wait(watchdog_engine, monkeypatch, tmp_path):
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
+    queue_wait = _queue_wait_entries(log_path)
+    handler_compute = _handler_compute_entries(log_path)
+    assert len(queue_wait) == 1
+    assert len(handler_compute) == 1
+    assert handler_compute[0]["handler_compute_s"] >= 0
+    assert isinstance(handler_compute[0]["timestamp"], str) and handler_compute[0]["timestamp"]
+    # SAME request -> both sibling samples share the identical t_received wall-clock timestamp, so a
+    # downstream join keys on it directly rather than a nearest-neighbor match (TC-1/TC-2).
+    assert handler_compute[0]["timestamp"] == queue_wait[0]["timestamp"]
+
+
+def test_watchdog_enabled_records_one_handler_compute_sample_per_additional_request(
+    watchdog_engine, monkeypatch, tmp_path
+):
+    """Two requests -> two handler_compute_s samples (never batched, never deduped, never dropped) --
+    mirrors the existing queue_wait_s two-request test above."""
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
+    assert len(_handler_compute_entries(log_path)) == 2
+
+
 # ======================================================================================================
 # TC-7 -- byte-identical response body/shape regardless of the flag. Direct function calls (not
 # TestClient) against the SAME session in immediate succession -- fully deterministic, no dependence on
@@ -189,7 +253,11 @@ def test_watchdog_records_sample_even_when_readiness_computation_raises(watchdog
     """The watchdog's queue-wait record is written BEFORE readiness/preflight computation runs, so a
     readiness-computation exception (already caught internally, degrading to `unavailable` -- this
     endpoint's own pre-existing convention) never suppresses, delays, or alters the sample the watchdog
-    already captured, nor the route's own honest degraded response (AG-8: never a wedge)."""
+    already captured, nor the route's own honest degraded response (AG-8: never a wedge). iter-68: because
+    the exception is caught INSIDE the endpoint (never escapes `health()`), execution still reaches the
+    handler_compute_s recording point near the end of the function -- so a full (not partial) sample is
+    captured for this request too, satisfying the iter-68 error-case requirement (whatever samples were
+    captured before/around the error are never suppressed)."""
     import app.api.health as health_module
 
     monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
@@ -212,3 +280,6 @@ def test_watchdog_records_sample_even_when_readiness_computation_raises(watchdog
     samples = _queue_wait_entries(log_path)
     assert len(samples) == 1
     assert samples[0]["queue_wait_s"] >= 0
+    handler_compute_samples = _handler_compute_entries(log_path)
+    assert len(handler_compute_samples) == 1
+    assert handler_compute_samples[0]["handler_compute_s"] >= 0
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 190 +++++++++++++++++++++
 .../state/preflight-verdict-history.jsonl          |   2 +
 runs/goal-session-ops-hardening/telemetry.jsonl    |   7 +
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   1 +
 5 files changed, 201 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
