# goal-ops-hardening-iter-16 Functional Test Plan

**Phase:** goal-ops-hardening-iter-16  
**Date:** 2026-07-23  
**Frontend Present:** yes

## Phase Goal

The `/backtest` endpoint and MCP `query_backtest` tool never trigger a forward-aggregate compute on request — every request is served from the last COMPLETE stored version, honestly labeled `ready`, `refreshing`, or `not_yet_computed`, eliminating the cold-MISS latency residual blocking J-06 and J-07, and fulfilling the new J-08 Must-have journey.

## Test Cases

### TC-01 — GET /api/backtest ready state: zero compute invocations

**Type:** api  
**Preconditions:** Backend running; forward-aggregate cache fully warmed at `dataset_version` V1 (all 5 configured horizons cached for the current latest `asof_key`); call-count instrumentation wrapper active around `compute_forward_aggregates`.

**Steps:**
1. Issue `GET /api/backtest` with no `as_of` parameter
2. Repeat 10 times, recording response status, `evidence_status` field, `evidence_generated_at` field, and `evidence_by_horizon` payload
3. Inspect call-count wrapper to record total invocations of `compute_forward_aggregates` across all 10 requests

**Expected outcome:**  
Every response has HTTP 200, `evidence_status == "ready"`, `evidence_generated_at` equal to V1's cache `created_at`, and fully populated `evidence_by_horizon`.

**Pass criteria:** All 10 responses have `evidence_status == "ready"` and call-count wrapper records exactly 0 invocations of `compute_forward_aggregates` across all 10 requests.

---

### TC-02 — MCP query_backtest ready state: zero compute invocations

**Type:** api  
**Preconditions:** Same as TC-01 — backend running, forward-aggregate cache fully warmed at V1, call-count instrumentation active.

**Steps:**
1. Invoke MCP `query_backtest` tool with `asof=None`
2. Repeat 10 times, recording response `evidence_status` and checking `evidence_by_horizon`
3. Inspect call-count wrapper for total invocations of `compute_forward_aggregates`

**Expected outcome:**  
Every MCP response has `evidence_status == "ready"`, fully populated `evidence_by_horizon`, and same `evidence_generated_at` as TC-01.

**Pass criteria:** All 10 MCP calls have `evidence_status == "ready"` and call-count wrapper records exactly 0 invocations of `compute_forward_aggregates`.

---

### TC-03 — GET /api/backtest refreshing state: prior version served within budget

**Type:** api  
**Preconditions:** Backend running; forward-aggregate cache complete at V1; a `/data` single-day backfill has been performed bumping `dataset_version` to V2; the finalize warm has completed 2-of-5 horizons for V2 (partial-warm state test-injected).

**Steps:**
1. Request `GET /api/backtest`
2. Record response status, `evidence_status`, `evidence_generated_at`, and `evidence_by_horizon`
3. Measure response latency (time from request to HTTP 200)

**Expected outcome:**  
Response has HTTP 200, `evidence_status == "refreshing"`, `evidence_generated_at` equals V1's `created_at`, `evidence_by_horizon` contains V1's complete payload (byte-identical to prior ready state), and latency is ≤1.5 seconds.

**Pass criteria:** `evidence_status == "refreshing"` AND latency ≤1.5s AND `evidence_by_horizon` matches V1's stored payload.

---

### TC-04 — Refreshing state response: no mixed versions across horizons

**Type:** api  
**Preconditions:** Same as TC-03 — partial-warm state (V2 2-of-5 horizons complete).

**Steps:**
1. Request `GET /api/backtest`
2. Inspect all 5 horizon rows in the returned `evidence_by_horizon`
3. For each horizon, cross-reference the response payload against the DB to confirm which `dataset_version` it originated from

**Expected outcome:**  
All 5 horizons' payloads originate from V1 (the complete, serving version); none originate from V2.

**Pass criteria:** 100% of horizons in the response are confirmed to come from V1; zero horizons from V2.

---

### TC-05 — Cutover from refreshing to ready after warm completes

**Type:** api  
**Preconditions:** Backend running; V2's finalize warm has just completed all 5 horizons; the run record's `aggregates_refreshed` list contains `"forward_aggregates"`.

**Steps:**
1. Request `GET /api/backtest`
2. Record response `evidence_status`, `evidence_generated_at`, and `evidence_by_horizon`
3. Diff the response's `evidence_by_horizon` against a direct test-only call to `compute_forward_aggregates` at V2
4. Verify via DB query that V1's now-superseded rows are pruned from the cache table

**Expected outcome:**  
Response has `evidence_status == "ready"`, `evidence_generated_at` updated to V2's timestamp, and `evidence_by_horizon` matches V2's freshly computed values byte-for-byte.

**Pass criteria:** `evidence_status == "ready"` AND `evidence_by_horizon` byte-identical to fresh V2 compute AND DB shows 0 remaining rows for V1 at this `asof_key`.

---

### TC-06 — GET /api/backtest not_yet_computed state: zero compute, within budget

**Type:** api  
**Preconditions:** Backend running; forward-aggregate cache empty or never warmed for the requested `asof_key` (fresh-install or test-fixture DB).

**Steps:**
1. Request `GET /api/backtest`
2. Record response status, `evidence_status`, `evidence_generated_at`, `evidence_by_horizon`, and latency
3. Inspect call-count wrapper for invocations of `compute_forward_aggregates`

**Expected outcome:**  
Response has HTTP 200, `evidence_status == "not_yet_computed"`, `evidence_by_horizon == {}`, `evidence_generated_at == null`, latency ≤1.5s, and no `compute_forward_aggregates` invocations.

**Pass criteria:** `evidence_status == "not_yet_computed"` AND `evidence_by_horizon == {}` AND `evidence_generated_at == null` AND latency ≤1.5s AND call-count == 0.

---

### TC-07 — MCP query_backtest not_yet_computed state: mirrors endpoint

**Type:** api  
**Preconditions:** Same as TC-06 — empty cache for requested `asof_key`.

**Steps:**
1. Invoke MCP `query_backtest` with `asof=None`
2. Record response `evidence_status`, `evidence_by_horizon`, `evidence_generated_at`
3. Inspect call-count wrapper for invocations of `compute_forward_aggregates`

**Expected outcome:**  
MCP response has identical shape to TC-06 endpoint response: `evidence_status == "not_yet_computed"`, `evidence_by_horizon == {}`, `evidence_generated_at == null`.

**Pass criteria:** MCP response structure exactly mirrors endpoint response AND call-count == 0.

---

### TC-08 — Ingest finalize warm invokes compute exactly once per horizon

**Type:** api  
**Preconditions:** Backend running; finalize warm computing V2 via the existing per-horizon loop in `_refresh_ingest_aggregates`.

**Steps:**
1. Trigger ingest finalize warm for V2
2. Monitor call-count wrapper throughout the warm execution
3. Record total invocations of `compute_forward_aggregates` as the warm completes all 5 horizons
4. Simultaneously sample requests to `GET /api/backtest` and record their call-count contributions

**Expected outcome:**  
The finalize warm's per-horizon loop invokes `compute_forward_aggregates` exactly 5 times (once per horizon); concurrent request-path callers invoke it 0 times.

**Pass criteria:** Total ingest warm invocations == 5 AND request-path invocations == 0 during the same window.

---

### TC-09 — Ready-state payload: byte-identical to fresh compute

**Type:** api  
**Preconditions:** Backend running; forward-aggregate cache at `evidence_status == "ready"` for the requested `asof_key`.

**Steps:**
1. Request `GET /api/backtest`
2. Extract the `evidence_by_horizon` payload
3. For each configured horizon, call `compute_forward_aggregates` directly (test-only helper) with the same inputs
4. Diff the two payloads for each horizon

**Expected outcome:**  
Every horizon's payload from the response is byte-identical to a direct, synchronous `compute_forward_aggregates` call with matching inputs.

**Pass criteria:** All 5 horizons pass byte-identity check (==, not approximate).

---

### TC-10 — Browser: refreshing state banner rendered alongside evidence

**Type:** browser  
**Preconditions:** Frontend running; backend at refreshing state (V2 finalize warm partially complete); user navigates to `/backtest`.

**Steps:**
1. Open Chrome and navigate to `http://localhost:3000/backtest`
2. Wait for page render
3. Inspect the EvidenceAggregateSection
4. Look for a banner/badge indicating refreshing status with the generation timestamp

**Expected outcome:**  
A visible banner or badge reading a refreshing-in-progress label with the served version's timestamp is rendered ALONGSIDE (not replacing) the fully-populated EvidenceAggregateSection. No skeleton/spinner replaces the evidence section itself.

**Pass criteria:** Refreshing banner visible AND EvidenceAggregateSection still fully rendered with horizon numbers AND timestamp displayed.

---

### TC-11 — Browser: not_yet_computed empty state rendered

**Type:** browser  
**Preconditions:** Frontend running; backend at not_yet_computed state (empty cache); user navigates to `/backtest`.

**Steps:**
1. Open Chrome and navigate to `http://localhost:3000/backtest`
2. Wait for page render
3. Inspect where EvidenceAggregateSection would normally appear
4. Look for an EmptyState component with explicit message about running an ingest
5. Verify other page sections (scorecard, leadership lists, as-of scan summary) are unaffected

**Expected outcome:**  
An explicit EmptyState component with message containing "not yet computed" and a call-to-action to run an ingest is visible in place of the evidence section. No horizon numbers shown. Rest of the page (scorecard, leadership lists) renders normally.

**Pass criteria:** EmptyState visible with "not yet computed" message AND no horizon numbers AND other page sections intact.

---

### TC-12 — Browser: ready state renders without banner or empty state (regression guard)

**Type:** browser  
**Preconditions:** Frontend running; backend at ready state (fully warmed cache); user navigates to `/backtest`.

**Steps:**
1. Open Chrome and navigate to `http://localhost:3000/backtest`
2. Wait for page render
3. Inspect the EvidenceAggregateSection and surrounding area
4. Verify no refreshing banner is present
5. Verify no empty-state message is present

**Expected outcome:**  
The forward-tested evidence section renders normally with all horizon numbers populated. No refreshing banner. No empty-state message. Exactly as before TC-10/TC-11 were added.

**Pass criteria:** EvidenceAggregateSection rendered normally AND no banner AND no empty-state message.

---

### TC-13 — GET /api/backtest historical as_of: unchanged lazy compute-once behavior

**Type:** api  
**Preconditions:** Backend running; a historical date (e.g., 2 days ago) whose `evidence_by_horizon` was never warmed by any ingest finalize run.

**Steps:**
1. Request `GET /api/backtest?as_of=<historical-date>` for the first time
2. Record response and note that `compute_forward_aggregates` is invoked once
3. Request the identical URL again
4. Verify the second request hits the cache (0 new compute invocations)

**Expected outcome:**  
First request computes and caches; second request serves from cache. The request-path-zero-compute guarantee is scoped to `is_latest == true` only, not historical time-machine requests.

**Pass criteria:** First request invokes compute once (lazy create-once); second request invokes compute 0 times (cache hit).

---

### TC-14 — Unit/integration tests pass: targeted suite host-guard-confined

**Type:** api  
**Preconditions:** Backend code built; environment variables set for host-guard confinement (`taskset -c 0-3,8-11`, BLAS/OMP/numexpr threads=4).

**Steps:**
1. Run targeted test suite for modified files: `test_forward_testing_concurrency.py` (or sibling), `test_backtest_*.py` (excluding loaded_engine fixtures), `test_mcp_tools.py`
2. Record pass/fail count and any error messages
3. Note the pre-existing carried failure: `test_db.py::test_create_all_produces_expected_tables`

**Expected outcome:**  
All tests pass except the pre-existing carried failure. No NEW test failures introduced. Host-guard confinement holds throughout (CPU pinning, thread caps).

**Pass criteria:** Test pass count matches expected (0 new failures beyond `test_create_all_produces_expected_tables`).

---

### TC-15 — Regression replay: J-01, J-03, J-04, J-05 remain passing

**Type:** api  
**Preconditions:** Backend running; golden-script deterministic replay records available for the four required-still-passing journeys.

**Steps:**
1. Run deterministic replay for J-01 (regime score consistency)
2. Run deterministic replay for J-03 (forward returns accuracy)
3. Run deterministic replay for J-04 (leadership selection stability)
4. Run deterministic replay for J-05 (data integrity under refresh)
5. For any golden-script miss, fall back to LLM evaluation
6. Record pass/fail for each journey

**Expected outcome:**  
All four journeys remain in `passing` state. None regress from passing to failing.

**Pass criteria:** J-01 PASS AND J-03 PASS AND J-04 PASS AND J-05 PASS.

---

### TC-16 — Operator-supervised live measurement: all three states within 1.5s budget

**Type:** api  
**Preconditions:** All targeted tests (TC-1 through TC-14/17/18) are green; host-guard-confined environment available; operator ready to perform supervised run.

**Steps:**  
OPERATOR-PERFORMED (agents cannot start/stop services this session):
1. Operator boots backend via `scripts/start-backend.sh` with host-guard confinement active (sampler + watchdog armed)
2. Perform a small single-day `/data` backfill via the backfill API
3. While the version bump is in-flight and finalize warm is executing, continuously poll `/backtest` and record response times for:
   - `refreshing` state (V2 warm partially complete): record 3-5 sample latencies
   - `ready` state (V2 warm complete): record 3-5 sample latencies
4. Record console output, backend PID, timestamps, and hwmon sampler readings
5. Stop services cleanly

**Expected outcome:**  
All sampled response times (both `refreshing` and `ready` states) are ≤1.5 seconds. Responses are accurate and complete (no partial horizon payloads).

**Pass criteria:** All measured latencies ≤1.5s for both `refreshing` and `ready` states AND responses byte-identical to unit tests.

---

### TC-17 — Single-flight guard holds post-split: ≥4 concurrent ingest calls

**Type:** api  
**Preconditions:** Backend running; code split of ingest-only and serving paths complete; call-count instrumentation active.

**Steps:**
1. Trigger 4+ concurrent ingest finalize warm calls for the SAME never-yet-cached `(horizon, asof_key, dataset_version)` key
2. Simulate overlapping ingest jobs racing the same identity
3. Monitor call-count wrapper for invocations of `compute_forward_aggregates`
4. Record completion time and confirm all callers complete

**Expected outcome:**  
Despite 4+ concurrent callers, `compute_forward_aggregates` is invoked exactly 1 time for that key (iter-15's single-flight guard survives the split). All callers complete within the existing 45-second bounded wait.

**Pass criteria:** call-count == 1 AND all 4+ callers complete within 45s.

---

### TC-18 — Completeness query filtered by asof_key: no unfiltered table scan

**Type:** api  
**Preconditions:** Backend running; forward-aggregate cache populated with rows for many distinct historical `asof_key`s (deep scenario).

**Steps:**
1. Request `GET /api/backtest` for a specific `asof_key`
2. Capture or trace the completeness-lookup SQL query
3. Inspect the query plan to verify filtering by `asof_key`
4. Alternatively, assert row-count: verify the query touches only the handful of rows for that one `asof_key` identity, not the full table

**Expected outcome:**  
The completeness-lookup query is filtered by the requested `asof_key` and touches only rows belonging to that identity, never an unfiltered scan of the entire `forward_aggregate_cache` table.

**Pass criteria:** Query plan shows `WHERE asof_key = <value>` filter AND row count touched ≤ number of configured horizons (5).

---

## Summary

**Total test cases:** 18  
**API tests:** 13 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-13, TC-14, TC-16, TC-17, TC-18)  
**Browser tests:** 3 (TC-10, TC-11, TC-12)  
**Artifact checks:** 2 (TC-15 — journey replay verification)

**Coverage map:**
- **Zero-compute correctness:** TC-01, TC-02, TC-06, TC-07, TC-08
- **Completeness/cutover logic:** TC-03, TC-04, TC-05, TC-18
- **Byte-identity (AG-3):** TC-09
- **Browser-visible states:** TC-10, TC-11, TC-12
- **Regression guards:** TC-12 (ready state unchanged), TC-13 (historical as-of unchanged), TC-15 (required journeys), TC-17 (single-flight guard)
- **Unit/integration suite:** TC-14
- **Live performance confirmation (AG-10-class, operator-supervised):** TC-16
