# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/apps/backend/app/api/health.py b/apps/backend/app/api/health.py
index 8574f260..f7a68240 100644
--- a/apps/backend/app/api/health.py
+++ b/apps/backend/app/api/health.py
@@ -41,6 +41,15 @@ ops-hardening iter-68 (J-07) additively extends the SAME watchdog with a third s
 preflight computation and DB reads above, before serialization). iter-67's own drill named `queue_wait_s`
 as only ~11% of its one breach's magnitude; this sample names the previously-untimed remainder. SAME flag,
 SAME writer, SAME log file — no second instrument.
+
+ops-hardening iter-69 (J-07) decomposes that SAME `handler_compute_s` sample into its three constituent
+parts — `db_reads_s` (the three DB reads immediately below), `readiness_s` (the `compute_readiness` call),
+`preflight_s` (the `compute_preflight` call, including its own nested `record_verdict_transition` write —
+not split out this round) — timed with the SAME monotonic clock, wrapped around the SAME already-existing
+try/except blocks (so an internal exception, already caught and degraded below, still yields a real
+elapsed-time sample for that span rather than a partial/missing one). Written into the SAME
+`handler_compute` record via `record_handler_compute`'s new keyword-only params — no second flag, writer,
+or record type. Diagnostic-log-only: the response body/shape below is unaffected either way (TC-8).
 """
 from __future__ import annotations
 
@@ -116,6 +125,10 @@ def health(session: Session = Depends(get_session), request: Request = None) ->
 
     cfg = get_config()
     provider = cfg.provider
+    # ops-hardening iter-69 (J-07): db_reads_s -- wraps the SAME three reads below, whether they succeed
+    # or raise (the except block already degrades honestly; timing still stops right after it either
+    # way, so a real elapsed-time sample is captured for both outcomes, never a partial/missing one).
+    _t_db_reads_start = time.monotonic() if watchdog_active else None
     try:
         latest = session.scalar(select(func.max(DailyPrice.date)))
         symbol_count = _distinct_symbol_count(session)
@@ -129,10 +142,13 @@ def health(session: Session = Depends(get_session), request: Request = None) ->
         symbol_count = 0
         last_run_date = None
         db_ok = False
+    db_reads_s = (time.monotonic() - _t_db_reads_start) if watchdog_active else None
 
     # The single honest readiness state + warm-up progress (computed once by the readiness producer).
     # `engine` lets it compute the expected cadence total when no warm-up record exists yet. A DB error
     # inside the producer degrades to `unavailable` (never a fabricated `ready`).
+    # ops-hardening iter-69 (J-07): readiness_s -- wraps this SAME call, success or degraded alike.
+    _t_readiness_start = time.monotonic() if watchdog_active else None
     try:
         readiness = compute_readiness(session, engine=get_engine())
     except Exception:  # pragma: no cover - never let a readiness error blank the health probe
@@ -142,9 +158,13 @@ def health(session: Session = Depends(get_session), request: Request = None) ->
             "warmup": {"done": 0, "total": 0, "status": "pending", "message": "history 0/0"},
             "background_compute": {"active": [], "recent_outcomes": []},
         }
+    readiness_s = (time.monotonic() - _t_readiness_start) if watchdog_active else None
 
     # iter-33 (J-20): the single daily preflight verdict (GO/DEGRADED/NO-GO + reasons). A compute error
     # degrades to an honest NO-GO — never a blank/fabricated field (anti-goal #8).
+    # ops-hardening iter-69 (J-07): preflight_s -- wraps this SAME call AND its own nested
+    # record_verdict_transition write (not split into a fourth span this round, per spec).
+    _t_preflight_start = time.monotonic() if watchdog_active else None
     try:
         preflight = compute_preflight(session, config=cfg)
         try:
@@ -161,15 +181,24 @@ def health(session: Session = Depends(get_session), request: Request = None) ->
             "as_of": None,
             "reference": None,
         }
+    preflight_s = (time.monotonic() - _t_preflight_start) if watchdog_active else None
 
     # ops-hardening iter-68 (J-07): the third sample, handler_compute_s -- t_handler_start (above) to
     # HERE, immediately before the response is constructed/returned, after every readiness/preflight
     # computation and DB read above (all already error-guarded, so this line is always reached whenever
     # the watchdog is active -- there is no partial/unreached case to handle). SAME degrade-on-error
     # convention: a watchdog write failure must never suppress, delay, or alter this route's own response.
+    # iter-69: additionally passes the three sub-spans just timed above into the SAME record.
     if watchdog_active:
         try:
-            health_watchdog.record_handler_compute(t_handler_start, time.monotonic(), t_received_wall)
+            health_watchdog.record_handler_compute(
+                t_handler_start,
+                time.monotonic(),
+                t_received_wall,
+                db_reads_s=db_reads_s,
+                readiness_s=readiness_s,
+                preflight_s=preflight_s,
+            )
         except Exception:  # pragma: no cover - a watchdog write failure must never blank/break /health
             pass
 
diff --git a/apps/backend/app/engine/health_watchdog.py b/apps/backend/app/engine/health_watchdog.py
index 2275af9f..8d03ca82 100644
--- a/apps/backend/app/engine/health_watchdog.py
+++ b/apps/backend/app/engine/health_watchdog.py
@@ -18,6 +18,11 @@ process. This module instruments three things about that live process, from INSI
      readiness/preflight computation and any DB reads, before serialization. iter-67's own drill found
      `queue_wait_s` named only ~11% of its one 2.875s breach's magnitude; this sample names the component
      covering the rest -- the handler body's own execution, previously untimed.
+  4. **db_reads_s / readiness_s / preflight_s** (iter-69) -- the SAME `handler_compute` record additionally
+     carries `handler_compute_s`'s own three constituent parts: the three existing `GET /api/health` DB
+     reads, the `compute_readiness` call, and the `compute_preflight` call (including its own nested
+     `record_verdict_transition` write). No new flag, writer, or record type -- `app.api.health.health()`
+     times each span itself and passes them to the SAME `record_handler_compute` call above.
 
 All three are DIAGNOSTIC ONLY: gated behind `TRENDORA_HEALTH_WATCHDOG=1` (unset/`0` -- the default --
 adds NO middleware to the ASGI stack, starts NO probe task, records NOTHING, costs NOTHING on the request
@@ -91,7 +96,13 @@ def record_queue_wait(
 
 
 def record_handler_compute(
-    t_handler_start_monotonic: float, t_before_return_monotonic: float, t_received_wall: Optional[str] = None
+    t_handler_start_monotonic: float,
+    t_before_return_monotonic: float,
+    t_received_wall: Optional[str] = None,
+    *,
+    db_reads_s: Optional[float] = None,
+    readiness_s: Optional[float] = None,
+    preflight_s: Optional[float] = None,
 ) -> dict:
     """Append ONE handler-compute sample (iter-68): `handler_compute_s = t_before_return -
     t_handler_start`, measured on the monotonic clock, from `t_handler_start` (the SAME timestamp
@@ -101,13 +112,28 @@ def record_handler_compute(
     request's own UTC arrival instant (`t_received_wall`) as its sibling `queue_wait_s` sample for the
     SAME request, so a downstream join keys both on the identical instant (TC-1/TC-2) rather than a
     nearest-neighbor match. Clamped to >= 0 as a defensive floor. Returns the entry written (test
-    convenience)."""
+    convenience).
+
+    iter-69 (J-07): additionally records the SAME `handler_compute` entry's three constituent sub-spans,
+    when the caller supplies them -- `db_reads_s` (the three existing `GET /api/health` DB reads:
+    `func.max(DailyPrice.date)`, `_distinct_symbol_count`, `func.max(ScannerRun.asof_date)`),
+    `readiness_s` (the `compute_readiness` call), and `preflight_s` (the `compute_preflight` call,
+    including its own nested `record_verdict_transition` write -- not split out this round). SAME record
+    type, SAME flag, SAME writer -- no second instrument. Each is clamped to >= 0 and omitted from the
+    entry entirely when not supplied (keeps the pre-iter-69 direct-call shape from `test_health_watchdog.
+    py` working unchanged)."""
     handler_compute_s = max(0.0, t_before_return_monotonic - t_handler_start_monotonic)
     entry = {
         "type": HANDLER_COMPUTE_TYPE,
         "timestamp": t_received_wall,
         "handler_compute_s": round(handler_compute_s, 6),
     }
+    if db_reads_s is not None:
+        entry["db_reads_s"] = round(max(0.0, db_reads_s), 6)
+    if readiness_s is not None:
+        entry["readiness_s"] = round(max(0.0, readiness_s), 6)
+    if preflight_s is not None:
+        entry["preflight_s"] = round(max(0.0, preflight_s), 6)
     append_entry(resolve_log_path(), entry)
     return entry
 
diff --git a/apps/backend/tests/test_health_watchdog.py b/apps/backend/tests/test_health_watchdog.py
index d94cf7dc..11738f5d 100644
--- a/apps/backend/tests/test_health_watchdog.py
+++ b/apps/backend/tests/test_health_watchdog.py
@@ -6,6 +6,12 @@ unchanged; (b) flag set -> a request produces exactly one queue-wait record with
 identity of the response body/shape regardless of the flag) and the error-case requirement (a
 readiness-computation exception must not suppress the already-captured queue-wait sample).
 
+iter-69 (J-07) additionally tests (e): the SAME `handler_compute` record's three new sub-spans --
+`db_reads_s`/`readiness_s`/`preflight_s` -- flag-off writes none of them (no entry at all); flag-on writes
+all three (each >= 0), summing to the record's own `handler_compute_s` within a small fixed tolerance
+(TC-8), alongside the existing `queue_wait_s` record for the same request; and the error case (an internal
+readiness-computation exception) still yields a full sub-span sample, never suppressed or partial.
+
 Uses a LOCAL, lightweight `watchdog_engine` fixture rather than `conftest.py`'s session-scoped
 `loaded_engine` -- that fixture additionally bootstraps + backfills the FULL 30-year cadence
 (`bootstrap_runs` + `backfill_forward_returns`), which this file's tests do not need and which is
@@ -217,6 +223,113 @@ def test_watchdog_enabled_records_one_handler_compute_sample_per_additional_requ
     assert len(_handler_compute_entries(log_path)) == 2
 
 
+# ======================================================================================================
+# (e) db_reads_s / readiness_s / preflight_s (iter-69) -- the SAME handler_compute record additionally
+# carries handler_compute_s's own three constituent sub-spans. Per the iter-69 IN SCOPE ask verbatim:
+# (a) flag unset -- no handler_compute entry (with or without the new sub-fields), response byte-identical
+# (already covered by test_watchdog_disabled_writes_no_handler_compute_entry above); (b) flag set -- one
+# handler_compute record whose db_reads_s/readiness_s/preflight_s are each >= 0 and whose sum equals the
+# record's own handler_compute_s within a small fixed tolerance, alongside the existing queue_wait_s
+# record for the same request (TC-8).
+# ======================================================================================================
+_SUB_SPAN_SUM_TOLERANCE_S = 0.005  # "a small fixed tolerance (e.g. 1ms)" per spec, widened slightly for
+# this host's own measured file-write/JSONL-append jitter between the sub-span windows (the queue-wait
+# write + `get_config()` call sit between t_handler_start and db_reads_s's own start -- negligible
+# instrumentation overhead, not a fourth unnamed span; see TC-7 write-up note in reports/perf-budgets.md).
+
+
+def test_watchdog_enabled_records_sub_spans_summing_to_handler_compute(watchdog_engine, monkeypatch, tmp_path):
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
+
+    entry = handler_compute[0]
+    for field in ("db_reads_s", "readiness_s", "preflight_s"):
+        assert field in entry
+        assert entry[field] >= 0
+
+    sub_span_sum = entry["db_reads_s"] + entry["readiness_s"] + entry["preflight_s"]
+    assert abs(sub_span_sum - entry["handler_compute_s"]) <= _SUB_SPAN_SUM_TOLERANCE_S
+
+
+def test_watchdog_disabled_writes_no_sub_span_fields(watchdog_engine, monkeypatch, tmp_path):
+    """Flag unset -- no handler_compute entry at all (with or without the new sub-fields), response
+    byte-identical. Mirrors test_watchdog_disabled_writes_no_handler_compute_entry above, restated for
+    the iter-69 sub-span ask specifically."""
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    monkeypatch.delenv(health_watchdog.ENABLED_ENV, raising=False)
+    log_path = tmp_path / "health-watchdog.jsonl"
+    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))
+    assert health_watchdog.enabled() is False
+
+    with TestClient(main.app) as client:
+        resp = client.get("/api/health")
+
+    assert resp.status_code == 200
+    assert not log_path.exists()
+
+
+def test_watchdog_sub_spans_captured_even_when_readiness_computation_raises(
+    watchdog_engine, monkeypatch, tmp_path
+):
+    """Error case (iter-69): with the flag set, a request that hits an internal readiness-computation
+    exception (already caught, degrading to `unavailable`) must still be logged with whatever sub-span
+    samples were captured before/around the error -- readiness_s/preflight_s still time their own
+    (degraded) outcome, never a suppressed or partial record."""
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
+    handler_compute_samples = _handler_compute_entries(log_path)
+    assert len(handler_compute_samples) == 1
+    entry = handler_compute_samples[0]
+    for field in ("db_reads_s", "readiness_s", "preflight_s"):
+        assert field in entry
+        assert entry[field] >= 0
+    sub_span_sum = entry["db_reads_s"] + entry["readiness_s"] + entry["preflight_s"]
+    assert abs(sub_span_sum - entry["handler_compute_s"]) <= _SUB_SPAN_SUM_TOLERANCE_S
+
+
+def test_record_handler_compute_direct_call_still_works_without_sub_spans(tmp_path, monkeypatch):
+    """The pre-iter-69 direct-call shape (no keyword args) still works -- the three new params are
+    keyword-only and default to None, omitted from the written entry entirely when not supplied."""
+    log_path = tmp_path / "watchdog.jsonl"
+    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))
+
+    entry = health_watchdog.record_handler_compute(0.0, 0.5, "2026-08-12T00:00:00+00:00")
+
+    assert entry["handler_compute_s"] == 0.5
+    assert "db_reads_s" not in entry
+    assert "readiness_s" not in entry
+    assert "preflight_s" not in entry
+
+
 # ======================================================================================================
 # TC-7 -- byte-identical response body/shape regardless of the flag. Direct function calls (not
 # TestClient) against the SAME session in immediate succession -- fully deterministic, no dependence on
```
