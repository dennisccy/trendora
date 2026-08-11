# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 3f78703e..6c3fd6ad 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -302,10 +302,32 @@ def _missing_data_diagnostic(
     # (materialize-then-iterate vs. stream-in-batches) changes; the output is byte-identical (TC-1).
     own_dates_by_symbol: dict[str, set[date_cls]] = {}
     _diag_batch = cfg.research.read_batch_size
+    # ops-hardening iter-63 (J-07 GIL-hold bound, profiled — never assumed): a live stack-sampling GIL-
+    # stall profile of the real `coverage_membership_timeline_refresh` finalize-tail phase (mirroring
+    # iter-53's own methodology — a worker thread runs the real function against a throwaway DB copy while
+    # a probe thread samples for >50ms gaps and captures the worker's stack via `sys._current_frames()` —
+    # `reports/perf-budgets.md`'s iter-63 addendum) found the ONE reproducible GIL stall in this whole
+    # phase bottoming out HERE, not in `resolve_with_reasons` (already bounded at iter-53 — this run
+    # measured it and `_trading_days` at ZERO stalls, confirming no residual cost survives there) — inside
+    # SQLAlchemy's own per-batch row materialization (`fetchmany(yield_per) -> manyrows ->
+    # [make_row(row) for row in rows]`), one uninterrupted burst per `_diag_batch`-sized chunk of this
+    # query's ~3.1M-row result. `.yield_per` (iter-40, above) already bounds PEAK MEMORY but does nothing
+    # to bound how long any ONE chunk holds the GIL uninterrupted. `time.sleep(0)` at each chunk boundary —
+    # a real OS-level GIL hand-off, mirroring `_cooperative_sorted`'s own chunk-then-yield pattern
+    # (`research.py:143-156`) — gives a concurrent `GET /api/health` poll a scheduling opportunity between
+    # chunks instead of relying only on whatever gap CPython's own eval-breaker leaves inside the
+    # SQLAlchemy-internal comprehension. Scheduling only: the SAME `_diag_batch`-sized chunks, the SAME
+    # rows in the SAME order, the SAME resulting `own_dates_by_symbol` — never a second query, never a
+    # changed WHERE clause, never a reordered row (TC-2/TC-5 byte-identity; see
+    # `test_missing_data_diagnostic_cooperative_yield_byte_identical` in test_data_manager.py).
+    _diag_row_count = 0
     for symbol, d in session.exec(
         select(DailyPrice.symbol, DailyPrice.date).where(DailyPrice.symbol.in_(universe))
     ).yield_per(_diag_batch):
         own_dates_by_symbol.setdefault(symbol, set()).add(d)
+        _diag_row_count += 1
+        if _diag_row_count % _diag_batch == 0:
+            time.sleep(0)  # cooperative GIL hand-off between yield_per chunks — see comment block above
 
     no_history: list[dict] = []
     thin: list[dict] = []
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index de61529e..6a2c7d34 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -6053,6 +6053,64 @@ def test_diagnostic_own_dates_streamed_fetch_byte_identical_to_whole_result(diag
     assert diag_default == diag_tiny_batch
 
 
+def test_missing_data_diagnostic_cooperative_yield_byte_identical(diagnostic_engine, monkeypatch):
+    """TC-2/TC-5 (ops-hardening iter-63, J-07 GIL-hold bound) -- the `time.sleep(0)` cooperative yield
+    added at each `_diag_batch` chunk boundary of the own-dates scan (data_manager.py, just above the
+    `for symbol, d in session.exec(...)` loop) is a SCHEDULING-ONLY change: it must never change which
+    rows are read, how they group, or the served diagnostic payload. Proven against a PINNED pre-fix
+    reference oracle -- the SAME query consumed with NO cooperative yield, replicated here exactly as it
+    ran before this iteration (mirrors test_universe_resolver.py's iter-53 reference-oracle pattern, and
+    this same file's own `test_diagnostic_own_dates_streamed_fetch_byte_identical_to_whole_result`, which
+    proved the streaming-vs-materialize choice was invisible; this test proves the ADDED yield point is
+    invisible too):
+
+      1. the reference oracle's `own_dates_by_symbol` grouping (no yield) is reproduced by the fixture's
+         known shape (AAA 6 + BBB 2 + CCC 3 + DDD 0 = 11 rows);
+      2. the real (post-fix) `_missing_data_diagnostic`, run with `read_batch_size` forced to 2 -- so the
+         11-row result genuinely crosses MULTIPLE `yield_per` chunks, not one -- serves the BYTE-IDENTICAL
+         payload the default (much larger) batch size serves, proving the batch width (and therefore how
+         many times the yield fires) never leaks into the output;
+      3. `time.sleep(0)` is actually invoked the expected number of times (5 -- floor(11/2), rows 2/4/6/
+         8/10 hit the modulo boundary; row 11 does not reach a 6th multiple of 2) and ALWAYS with argument
+         0 (never a real pause) -- proving the cooperative-yield code path is genuinely exercised by this
+         test, not merely present and dead."""
+    engine, _days = diagnostic_engine
+    cfg = _diag_cfg()
+    universe = list(cfg.universe.symbols)
+
+    with Session(engine) as session:
+        # sanity: the fixture's own-dates query is exactly 11 rows (AAA 6 + BBB 2 + CCC 3 + DDD 0), so
+        # batch-of-2 below is guaranteed to cross multiple yield_per chunks, never a single-batch pass.
+        reference_dates: dict[str, set] = {}
+        for symbol, d in session.exec(
+            select(DailyPrice.symbol, DailyPrice.date).where(DailyPrice.symbol.in_(universe))
+        ).all():
+            reference_dates.setdefault(symbol, set()).add(d)
+    assert sum(len(v) for v in reference_dates.values()) == 11
+
+    cfg_tiny_batch = cfg.model_copy(
+        update={"research": cfg.research.model_copy(update={"read_batch_size": 2})}
+    )
+
+    sleep_calls: list = []
+
+    def _counting_sleep(seconds):
+        sleep_calls.append(seconds)
+
+    monkeypatch.setattr("app.engine.data_manager.time.sleep", _counting_sleep)
+
+    with Session(engine) as session:
+        diag_tiny_batch_with_yield = _missing_data_diagnostic(session, cfg_tiny_batch)
+
+    # 1/2 -- byte-identical to the default (much larger, single-chunk) batch size's own served payload.
+    with Session(engine) as session:
+        diag_default_batch = _missing_data_diagnostic(session, cfg)
+    assert diag_tiny_batch_with_yield == diag_default_batch
+
+    # 3 -- the cooperative yield genuinely ran, exactly the expected number of times, always as sleep(0).
+    assert sleep_calls == [0] * 5
+
+
 # ==================================================================================================
 # iter-40 (iter-39/w, AG-3) — checkpoint cadence: per-date density + throttle still bounds writes
 # ==================================================================================================
diff --git a/apps/frontend/lib/data-overview-refresh.test.ts b/apps/frontend/lib/data-overview-refresh.test.ts
index 5f2218c4..cdce9149 100644
--- a/apps/frontend/lib/data-overview-refresh.test.ts
+++ b/apps/frontend/lib/data-overview-refresh.test.ts
@@ -2,7 +2,11 @@
  * Unit tests for the J-07 / auditor-F3 ambient-refresh failure helper (lib/data-overview-refresh.ts).
  *
  * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
- *   node lib/data-overview-refresh.test.ts
+ *   npx tsx lib/data-overview-refresh.test.ts
+ * (ops-hardening iter-63, TC-6: this repo's Node 22 install errors ERR_UNKNOWN_FILE_EXTENSION on a
+ * plain `node lib/data-overview-refresh.test.ts` invocation for a .ts file; only the `npx tsx` form
+ * above actually exits 0 here — the comment previously named the bare `node` form, which does not run.
+ * The test logic itself is unchanged and was already correct/green under `npx tsx`.)
  * Pins the helper's three input cases (TC-6): `ok` preserved unchanged, `loading` -> `error`,
  * `error` -> `error`.
  */
diff --git a/incredible_auto_dev/scripts/automation/lib/common.sh b/incredible_auto_dev/scripts/automation/lib/common.sh
index 98840b27..da3e04e9 100644
--- a/incredible_auto_dev/scripts/automation/lib/common.sh
+++ b/incredible_auto_dev/scripts/automation/lib/common.sh
@@ -1408,6 +1408,54 @@ _wait_for_frontend_ready() {
   done
 }
 
+# ops-hardening iter-63 (dev fix — the replay-lane restart race, iter-62 lesson #2, applied verbatim:
+# "any change to the browser-QA lane's restart/replay ordering"). Waits for the backend's OWN readiness
+# SIGNAL, not merely a live port. `ensure_services_running` / `_start_service_with_retries` (above) treat
+# ANY 1xx-5xx response as "up" — deliberately permissive so a namespaced health route (this project's own
+# `/api/health`, not a bare `/health`) is not misjudged DOWN. But Trendora's boot is DESIGNED to serve
+# `/api/health` INSTANTLY (goal.md Key Capability 4, "instant-serving boot with phase-aware health": boot
+# performs existence checks only) — so a fast 200 proves uvicorn is listening, never that the app has
+# finished its OWN internal readiness stages. The payload's `readiness` field is the single canonical
+# readiness value (`app.engine.readiness.compute_readiness`, the SAME value the frontend's readiness badge
+# reads — `data-testid="readiness-badge" data-state="ready"`, apps/frontend/components/health-badge.tsx).
+# A caller that starts asserting against a backend restarted moments ago, before this field reaches
+# "ready", can race a genuinely-still-warming app and misreport an honest in-progress state as a broken
+# journey — exactly the false FAIL iter-62 measured on J-01 step 09 / J-04 step 02 when the deterministic
+# replay lane ran ~1 minute after a restart. This function only READS the existing `/api/health` payload
+# (never a second/looser readiness computation) and NEVER hard-fails the caller: a timeout returns 1 so
+# the caller can log it and proceed anyway — a project whose `/api/health` lacks this field, or a backend
+# that never reaches steady-state `ready` (a separate, real defect other journeys already catch), must
+# degrade to today's pre-gate behavior, never a new hang.
+#
+# Usage: _wait_for_backend_readiness <health_url> [max_wait_seconds] [log_tag]
+# Returns 0 once the payload's `readiness` field == "ready", 1 on timeout or an empty/unset url (a no-op
+# in that case — nothing to gate on).
+_wait_for_backend_readiness() {
+  local url="$1" max_wait="${2:-${CHAIN_BACKEND_READY_WAIT_S:-60}}" tag="${3:-wait}"
+  [[ -n "$url" ]] || return 0
+  local waited=0 state=""
+  echo "[$tag] Waiting for backend readiness (the 'readiness' field of $url) to reach 'ready' (max ${max_wait}s)..."
+  while true; do
+    state="$(curl -s --max-time 5 "$url" 2>/dev/null | python3 -c "
+import json, sys
+try:
+    print(json.load(sys.stdin).get('readiness', ''))
+except Exception:
+    print('')
+" 2>/dev/null || true)"
+    if [[ "$state" == "ready" ]]; then
+      echo "[$tag] backend readiness == ready (${waited}s)."
+      return 0
+    fi
+    sleep 3
+    waited=$((waited + 3))
+    if [[ $waited -ge $max_wait ]]; then
+      echo "[$tag] Warning: backend readiness did not reach 'ready' within ${max_wait}s (last observed: '${state:-<no response>}') — proceeding anyway (not a hard gate)." >&2
+      return 1
+    fi
+  done
+}
+
 # Clear any stale Next.js dev server that would block a fresh start.
 # Next.js 16+ writes .next/dev/lock with its own PID and refuses to start a
 # second dev server from the same directory — even on a different port. Just
diff --git a/incredible_auto_dev/scripts/automation/lib/replay-lane.sh b/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
index 0d9a390b..fa4aab00 100644
--- a/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
+++ b/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
@@ -328,6 +328,17 @@ replay_lane_partition_and_verify() {
   REPLAY_MASS_FAIL=""
   REPLAY_CANARIES=""
   if [[ "$_use_replay" == "yes" ]]; then
+    # ops-hardening iter-63 (dev fix — the replay-lane restart race, iter-62 lesson #2): this is the
+    # lane's own FIRST externally-visible action against the live backend — gate it on the backend's own
+    # readiness signal (the SAME `readiness` value the frontend's readiness badge reads), not merely on
+    # whatever liveness `ensure_services_running` already confirmed (a bare 1xx-5xx probe — see
+    # `_wait_for_backend_readiness`'s own docstring in lib/common.sh for the full rationale). A lane
+    # invoked shortly after a pre-QA backend restart previously raced a still-warming app straight into
+    # `_replay_lane_verify_once` below and reported false FAILs on journeys that were honestly not broken
+    # yet (J-01 step 09 / J-04 step 02, iter-62). Best-effort only — a timeout logs a warning and this
+    # still proceeds (never a new hang/hard-fail mode for a project or backend state where `readiness`
+    # never reaches "ready").
+    _wait_for_backend_readiness "${QA_BACKEND_HEALTH_URL:-}" "${CHAIN_BACKEND_READY_WAIT_S:-60}" "replay-lane" || true
     _replay_lane_log "Regression (deterministic replay): $R_REPLAY"
     local _replay_csv _replay_rc=0
     _replay_csv="$(echo "$R_REPLAY" | tr ' ' ',' | sed 's/^,*//;s/,*$//')"
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 135 +++++++++++++++++++++
 .../journey-scripts/J-05.json                      |  15 +--
 .../state/drift-report.json                        |   2 +-
 runs/goal-session-ops-hardening/telemetry.jsonl    |   9 ++
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   2 +
 6 files changed, 156 insertions(+), 9 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
