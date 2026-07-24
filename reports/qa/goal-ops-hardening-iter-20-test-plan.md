# Goal Iteration 20 Functional Test Plan

**Phase:** goal-ops-hardening-iter-20
**Date:** 2026-07-24
**Frontend Present:** yes

## Phase Goal

A first-ever view of any historical `/backtest` as-of date never blocks the request on a multi-second forward-aggregate compute — it renders instantly with an honest interim state while that date's evidence finishes warming off the request thread, unblocking J-06/J-07/J-08.

## Test Cases

### TC-01 — Historical First-Touch Returns Fast Without Blocking

**Type:** api
**Preconditions:** Backend is running; a historical as-of date D (e.g., `2025-05-30`) has no cached `ForwardAggregateCache` row for the current `dataset_version` (never-before-warmed).

**Steps:**
1. Measure request start time
2. Send `GET /api/backtest?as_of=<D>` 
3. Record HTTP status code, response time, and `evidence_status` field
4. Check backend logs for dispatch initialization

**Expected outcome:** HTTP 200 within ≤1.5 s; `evidence_status` is `"refreshing"` or `"not_yet_computed"`; background compute has been dispatched without blocking the request thread.

**Pass criteria:** Response completes in ≤1.5 s AND `evidence_status ∈ {"refreshing", "not_yet_computed"}` AND backend logs show dispatch triggered but NOT synchronous compute blocking.

---

### TC-02 — Dispatch-Decision Timing is Sub-Millisecond

**Type:** api
**Preconditions:** Same as TC-01.

**Steps:**
1. Send `GET /api/backtest?as_of=<D>` and capture the complete HTTP response
2. Parse the response's `backtest_timing` object or `_log_backtest_timing` log line
3. Extract the dispatch-decision cost field (renamed from `ensure_loop_ms`)
4. Verify it records sub-millisecond cost, not multi-second compute-wait duration

**Expected outcome:** The dispatch-decision field in the timing log is <1 ms (never a multi-second compute-wait duration like the old ensure-loop).

**Pass criteria:** Dispatch-decision cost < 1 ms across 10 consecutive calls for the same never-warmed date.

---

### TC-03 — Concurrent First-Touch Requests Dispatch Once, Never Duplicate

**Type:** api
**Preconditions:** Backend is running with instrumented logging; a historical as-of date D has no cached evidence for the current `dataset_version`.

**Steps:**
1. Fire 5 concurrent `GET /api/backtest?as_of=<D>` requests (all issued simultaneously)
2. Capture the backend logs for `compute_forward_aggregates` invocations
3. Count total invocations across all 5 requests
4. Record response times for all 5 requests
5. Verify all 5 complete within budget

**Expected outcome:** `compute_forward_aggregates` is invoked exactly `len(cfg.walk_forward.horizons)` times total across all 5 requests (not `5 × len(horizons)`, not zero); all 5 HTTP responses complete within ≤1.5 s.

**Pass criteria:** Invocation count = `len(horizons)` (exactly 5 if horizons = {1, 2, 4, 8, 12} weeks) AND all 5 response times ≤1.5 s AND no `RuntimeError` due to duplicate guard acquisition.

---

### TC-04 — After Background Compute Completes, Served Evidence is Ready and Byte-Identical

**Type:** api
**Preconditions:** TC-01's background compute for date D has completed (poll for `evidence_status == "ready"` or wait 30 s); D's forward-aggregate evidence is now in cache.

**Steps:**
1. Send a second `GET /api/backtest?as_of=<D>`
2. Capture the response and extract `evidence_status` and `evidence_by_horizon`
3. In a separate Python session, directly call `compute_forward_aggregates(session, h, cfg, as_of=D)` for each configured horizon h
4. Compare byte-for-byte: response's `evidence_by_horizon[h]` == direct-compute result for each h

**Expected outcome:** `evidence_status == "ready"`; `evidence_asof == D`; `evidence_by_horizon[h]` is byte-identical to direct `compute_forward_aggregates` for every configured horizon.

**Pass criteria:** Byte-for-byte match for all horizons AND `evidence_asof` equals the queried date D AND `evidence_status == "ready"`.

---

### TC-05 — Health Endpoint Stays Responsive During Background Compute

**Type:** api
**Preconditions:** Backend is running; a historical as-of date D's background compute is in flight (just triggered TC-01 or TC-03).

**Steps:**
1. Poll `GET /api/health` once per second for the next 15 seconds
2. Record response time and `readiness` status for each poll
3. Monitor backend CPU to confirm D's compute is active
4. Continue polling until `readiness == "ready"` or 15 s elapsed

**Expected outcome:** Every poll returns HTTP 200 within ≤0.1 s; no frozen or unresponsive window; `readiness` stays `"ready"` throughout.

**Pass criteria:** All ≥15 health polls complete in ≤0.1 s AND no single poll exceeds 0.1 s AND `readiness == "ready"` for all polls.

---

### TC-06 — MCP query_backtest Behaves Identically to HTTP Endpoint

**Type:** api
**Preconditions:** Backend is running; a historical as-of date D has no cached evidence for the current `dataset_version`.

**Steps:**
1. Call MCP `query_backtest(session, asof=D)` and capture the result
2. Simultaneously send `GET /api/backtest?as_of=<D>` and capture the HTTP response
3. Compare both responses for `evidence_status`, `evidence_asof`, `evidence_by_horizon` shape
4. Record timing for both calls

**Expected outcome:** Both return identical `evidence_status` (either both `"refreshing"`/`"not_yet_computed"` or both `"ready"` if pre-warmed); both dispatch exactly once per identity; both complete within ≤1.5 s.

**Pass criteria:** Identical `evidence_status` AND identical `evidence_asof` AND identical behavior (both dispatch or neither dispatch) AND both complete within budget.

---

### TC-07 — Dispatch-Owner Failure Releases Guard, Re-Dispatch Succeeds

**Type:** api
**Preconditions:** Backend running; a test harness can inject a failure into the background-dispatch owner thread; a historical as-of date D has never been warmed.

**Steps:**
1. Trigger a first `GET /api/backtest?as_of=<D>` to start a background dispatch
2. Inject an exception into the owner thread (e.g., simulate a DB connection drop mid-compute)
3. Confirm the dispatch-owner thread exits with the exception
4. Send a second `GET /api/backtest?as_of=<D>`
5. Verify the second request can re-dispatch and eventually D reaches `"ready"`
6. Wait for the new dispatch to complete (poll for `evidence_status == "ready"` with 30 s timeout)
7. Send a third `GET /api/backtest?as_of=<D>` and verify it serves `"ready"`

**Expected outcome:** After the owner-thread failure, the outer guard is released (never permanently wedged); a subsequent request re-dispatches and D eventually reaches `"ready"` on a later view.

**Pass criteria:** Third request returns `"ready"` AND no `RuntimeError` about a locked guard AND backend logs show two separate dispatch attempts (one failed, one succeeded).

---

### TC-08 — RefreshingEvidenceBanner Copy is Correct for Historical-Dispatch Trigger

**Type:** browser
**Preconditions:** Frontend is running at http://localhost:3000 (or `$CHAIN_FRONTEND_URL`); a historical as-of date D is rendered on `/backtest?as_of=<D>` with `evidence_status == "refreshing"` (actively computing its own evidence in the background, not a latest-view version bump).

**Steps:**
1. Navigate to `/backtest?as_of=<historical-date>` where the historical date's evidence is actively refreshing in the background
2. Locate the `RefreshingEvidenceBanner` component on the page
3. Read the banner's text in full
4. Verify each claim against the current system state (a historical-view-triggered background dispatch with no ingest involved)

**Expected outcome:** The banner contains no false claims for this scenario. Specifically:
- NO unconditional assertion that "the dataset has changed" (only true for version-bump triggers, not historical-dispatch)
- NO statement that reloading "after the next ingest finishes" is what surfaces the new value (no ingest is involved here)
- The copy acknowledges that viewing the page itself may trigger a background compute of that date's evidence

**Pass criteria:** Every sentence in the banner is factually true for a historical-first-view dispatch trigger AND the tone remains calm/factual/never fabricated.

---

### TC-09 — EmptyState Copy is Correct for Never-Warmed Fresh-Install Scenario

**Type:** browser
**Preconditions:** Frontend is running; the backend has no complete evidence at or before the requested as-of date for any as-of (a genuinely never-warmed fresh-install shape); a user requests `/backtest?as_of=<D>`.

**Steps:**
1. Clear backend evidence cache (or use a date far in the past with no computed aggregates)
2. Navigate to `/backtest?as_of=<old-date>` where no evidence exists
3. Locate the `EmptyState` component on the page
4. Read its text in full
5. Verify each claim against the state (a never-warmed store; viewing the page triggers background compute)

**Expected outcome:** The `EmptyState` copy contains no false claims. Specifically:
- The copy must NOT state only "backfilling or fetching data" starts a compute
- The copy must acknowledge that viewing the page itself can trigger a background compute (distinct from ingest/backfill-only triggers)
- No claim that is demonstrably untrue for the never-warmed fresh-install case

**Pass criteria:** Every sentence in the `EmptyState` is factually true AND the copy acknowledges viewing the page as a trigger for background compute.

---

### TC-10 — Historical Create-Once Behavior Preserved After Updates

**Type:** artifact
**Preconditions:** Backend tests have been updated; `test_historical_asof_keeps_pre_iter16_create_once_and_cache_behavior` and `test_historical_asof_still_computes_once_even_when_older_fallback_evidence_exists` in `apps/backend/tests/test_forward_testing_serving_split.py` have been modified to wait for dispatched background computes.

**Steps:**
1. Run `pytest apps/backend/tests/test_forward_testing_serving_split.py::test_historical_asof_keeps_pre_iter16_create_once_and_cache_behavior -xvs`
2. Verify it waits for the dispatched background compute to complete
3. Verify it still asserts exactly `len(HORIZONS)` real `compute_forward_aggregates` calls total
4. Verify it still asserts zero additional calls on a repeat view
5. Run `pytest apps/backend/tests/test_forward_testing_serving_split.py::test_historical_asof_still_computes_once_even_when_older_fallback_evidence_exists -xvs`
6. Verify the same contract (exactly `len(HORIZONS)` calls, byte-identity across repeated calls)

**Expected outcome:** Both tests pass; the wait-for-completion logic is integrated; the compute-count and byte-identity assertions are unchanged and still hold.

**Pass criteria:** Both tests pass; test output shows exactly `len(HORIZONS)` `compute_forward_aggregates` calls per test AND no "compute invoked more than expected" warnings.

---

### TC-11 — No-Lookahead Expanding-Window Proof Holds After Update

**Type:** artifact
**Preconditions:** `test_backtest_evidence_is_as_of_scoped_expanding_window` in `apps/backend/tests/test_api_backtest.py` has been updated to wait for the dispatched background compute before asserting.

**Steps:**
1. Run `pytest apps/backend/tests/test_api_backtest.py::test_backtest_evidence_is_as_of_scoped_expanding_window -xvs` (in isolation if needed, per the file's pattern)
2. Verify the test waits for the dispatch to complete
3. Verify the assertions on `n_runs` (oldest < latest) still hold
4. Verify `asof_dates <= D` (no lookahead) still holds
5. Check the test output for any "future bar included" or lookahead violations

**Expected outcome:** Test passes; the expanding-window proof (n_runs strictly increasing, no future bars) is preserved under the new dispatch model.

**Pass criteria:** Test passes AND test output confirms `n_runs[oldest] < n_runs[latest]` AND no asof_date exceeds the query date D.

---

### TC-12 — Browser First-Ever Historical View Renders Fast Without Freezing

**Type:** browser
**Preconditions:** Backend and frontend are running; a historical as-of date D (e.g., `2025-05-30`) has never been viewed in this browser session and is not yet warmed in the cache.

**Steps:**
1. Note the current time
2. Navigate to `/backtest?as_of=<D>` (a never-viewed historical date)
3. Wait up to 1.5 s and observe the page rendering
4. Capture a screenshot of the initial rendered state
5. If `RefreshingEvidenceBanner` or `EmptyState` is visible, note the component and copy
6. Wait for the background compute to complete (poll backend health or observe the page re-rendering)
7. Reload the page after the compute completes
8. Capture a screenshot of the final rendered state with evidence displayed
9. Measure total time from initial navigation to final render

**Expected outcome:** 
- Initial render completes within ≤1.5 s (never a blank/frozen skeleton)
- Page shows either `RefreshingEvidenceBanner` or `EmptyState` (honest interim state)
- After the background compute finishes, a reload shows the date's own real per-horizon evidence
- No crash or error page at any stage

**Pass criteria:** Initial render ≤1.5 s AND interim state component rendered AND final render shows evidence byte-identically matching backend TC-04 AND no blank/frozen skeleton observed AND screenshots saved under `reports/qa/goal-ops-hardening-iter-20-evidence/`.

**Fallback (if Chrome MCP port 9224 remains wedged):** Operator captures `curl -s http://localhost:8255/api/backtest?as_of=<D> | jq '.backtest_timing'` to verify timing and `evidence_status`, documenting the attempt in notes. Copy-correctness check (TC-8/TC-9) still requires live browser render.

---

### TC-13 — Concurrent-Ingest-Overlay /backtest Re-Measurement (OPERATOR-GATED)

**Type:** api
**Preconditions:** Owner has authorized the concurrent-ingest trigger via AG-10 approval; both `scripts/start-backend.sh` and the ingest launcher are available; a deep-basis backend is available.

**Steps:**
1. Start the backend via `scripts/start-backend.sh` (confirms host-guard caps are in place)
2. In one terminal, start a concurrent ingest job targeting the deep basis
3. In a second terminal, poll `GET /api/backtest?as_of=<historical-date>` once per second for 60 seconds
4. Record the timestamp, response time, and HTTP status for each poll
5. Count any polls that exceed 1.5 s (breach count)
6. Record the maximum latency observed
7. Let the ingest complete and the polling finish
8. Append results to `reports/perf-budgets.md` in a new dated section

**Expected outcome:** Breach count and max latency are recorded and directly comparable to iter-16/17 baseline (11/68 breaches, max 12.655 s). If the ingest trigger remains blocked this session, the section records that plainly.

**Pass criteria:** Measurement completes without crashing the backend; breach count and max latency are documented; results are comparable to iter-16/17 baseline.

---

### TC-14 — Disruptive J-04 Kill/Restart Checkpoint-Survival Replay (OPERATOR-GATED)

**Type:** api
**Preconditions:** Owner has authorized the disruptive kill/restart scenario via AG-10 approval; the backend is running with checkpointing enabled; a backfill can be submitted and interrupted.

**Steps:**
1. Start the backend via `scripts/start-backend.sh`
2. Submit a real backfill via the `/data` Run History panel UI
3. Once the backfill is in progress (confirmed by backend logs), forcibly kill the backend process: `kill -9 $(pgrep -f "uvicorn.*--port")`
4. Wait 5 seconds
5. Restart the backend via `scripts/start-backend.sh`
6. Navigate to the `/data` Run History panel
7. Locate the interrupted run and inspect its checkpoint progress (last-checkpointed bar, asset count, etc.)
8. Verify the run's progress matches the last checkpoint, not all-zero creation-time defaults

**Expected outcome:** After restart, the `/data` Run History panel shows the interrupted run's last-checkpointed progress, not reset to creation-time defaults.

**Pass criteria:** Run History panel displays last-checkpoint progress AND the progress is non-zero AND no crash banner appears after restart.

**Fallback (if owner blocks the disruptive trigger):** Record a non-disruptive sanity check instead: send `GET /api/health` after restart, verify HTTP 200, `readiness: "ready"`, no new crash banner. Document the attempt and outcome plainly in the handoff.

---

### TC-15 — Required-Still-Passing Journeys Regression Check

**Type:** artifact
**Preconditions:** This iteration's code changes have been merged; deterministic golden-replay scripts for J-01/J-03/J-05 are available; J-04's LLM-fallback status is documented.

**Steps:**
1. Run `pytest scripts/automation/browser-qa/J-01-deterministic.py -xvs` (J-01 deterministic replay)
2. Run `pytest scripts/automation/browser-qa/J-03-deterministic.py -xvs` (J-03 deterministic replay)
3. Run `pytest scripts/automation/browser-qa/J-05-deterministic.py -xvs` (J-05 deterministic replay)
4. Document J-04's status (LLM-fallback or carried, per the session pattern)
5. Verify no transition from passing to failing

**Expected outcome:** J-01, J-03, J-05 all pass deterministic replay; J-04 maintains its carried/LLM status; no regression.

**Pass criteria:** All three deterministic replays return pass verdict AND no journey transitions from passing to failing.

---

### TC-16 — Coherence Check: Byte-Identity of Forward-Aggregate Logic

**Type:** artifact
**Preconditions:** This iteration's code diff is available; iter-19's version of `compute_forward_aggregates` and `resolved_forward_aggregate_evidence` is known.

**Steps:**
1. Diff the current `apps/backend/app/engine/forward_testing.py:compute_forward_aggregates` against iter-19
2. Diff the current `resolved_forward_aggregate_evidence` against iter-19
3. Verify both are byte-unchanged (no logic changes, only dispatch-trigger-timing changes)
4. Confirm no second producer or resolver was introduced

**Expected outcome:** Both `compute_forward_aggregates` and `resolved_forward_aggregate_evidence` are bit-for-bit identical to iter-19; no new compute path or resolver logic.

**Pass criteria:** Diff output shows zero changes in function bodies AND no second producer/resolver exists in the codebase.

---

## Summary

**Total test cases:** 16
- **API tests:** 10 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-13, TC-14, plus health/timing verifications)
- **Browser tests:** 4 (TC-08, TC-09, TC-12, TC-15)
- **Artifact checks:** 4 (TC-10, TC-11, TC-14 fallback, TC-16)
- **Operator-gated:** 2 (TC-13, TC-14 — contingent on owner approval; document attempt and outcome plainly if blocked)

**Key test scenarios cover:**
- Non-blocking dispatch on first-touch historical as-of (TC-01, TC-02)
- Concurrency-safe single-flight guarantee (TC-03, TC-07)
- Byte-identical served evidence after compute (TC-04, TC-16)
- Health endpoint responsiveness during compute (TC-05)
- MCP parity with HTTP endpoint (TC-06)
- Copy correctness for new trigger (TC-08, TC-09)
- Updated test contracts (TC-10, TC-11, TC-15)
- Live browser validation of responsive rendering (TC-12)
- Operator-performed deep-basis and disruptive scenarios (TC-13, TC-14)
