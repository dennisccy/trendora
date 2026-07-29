# Goal Ops-Hardening Iter-31 Functional Test Plan

**Phase:** goal-ops-hardening-iter-31
**Date:** 2026-07-29
**Frontend Present:** no

## Phase Goal

Close AG-8 finding (a): bound Factor Lab's all-factors view to stop crashing with `MemoryError` and add a single-flight de-dup guard to prevent duplicate concurrent computes of the same cache identity.

## Test Cases

### TC-01 — Cold-MISS Factor Lab all-factors request succeeds (HTTP 200)

**Type:** api
**Preconditions:** 
- Backend is warm, running on the live deep basis under the declared `server.memory_cap_mb` ulimit
- No `EventStudyCache` row exists for the current `(__all_factors__, factors_table, asof_key, dataset_version+schema_token, default_horizon)` identity (genuine cold cache MISS)

**Steps:**
1. Send HTTP GET request to `/research/factor-lab?all=true` (against the running backend)
2. Capture response status code and response body (including decile table and rank-IC figures)
3. Verify the response completes without `MemoryError`

**Expected outcome:** 
HTTP 200 response body contains `factors_table` with real numeric values for every catalog factor at every configured horizon, and `rank_ic_by_horizon` data populated.

**Pass criteria:** 
Status code is 200 AND response contains valid JSON with non-empty decile tables and rank-IC figures for all horizons AND no `MemoryError` in response body.

---

### TC-02 — Zero MemoryError with research.py frame across cold-MISS and repeat request

**Type:** api
**Preconditions:** 
- Backend has just booted; log window is defined by THIS run's boot-banner line number (exact line number MUST be cited in QA report)
- No errors have been logged yet in this backend session

**Steps:**
1. Record the boot-banner line number from `logs/backend.log` 
2. Execute TC-01 (cold-MISS `/research/factor-lab?all=true` request)
3. Execute the request a second time (concurrent load spot-check)
4. Grep `logs/backend.log` for lines AFTER the boot-banner containing both `research.py` in the traceback AND the string `MemoryError`
5. Count matching lines

**Expected outcome:** 
Zero lines matching the pattern in step 4.

**Pass criteria:** 
Line count from step 4 is exactly 0. QA report MUST state the boot-banner line number it counted from.

---

### TC-03 — Single-flight guard: two concurrent MISS requests trigger exactly ONE compute

**Type:** api
**Preconditions:** 
- Unit test environment with instrumentation: an in-process counter tracking `compute_factor_lab_all` invocations
- Cache is cold (no row for the test identity)

**Steps:**
1. Instrument `compute_factor_lab_all` with an entry/exit counter
2. Spawn two concurrent requests for the SAME Factor-Lab-all cache identity on a cold MISS (both requests should reach `factor_lab_all_cached` at approximately the same time)
3. Record the counter's final value (how many times the real compute was invoked)
4. Verify both requests received a response

**Expected outcome:** 
Both requests return HTTP 200 with identical payloads; the counter shows exactly 1 real invocation of `compute_factor_lab_all`.

**Pass criteria:** 
Counter value is 1 AND both requests returned successfully with byte-identical response bodies (same decile table, rank-IC figures for all horizons).

---

### TC-04 — Single-flight guard failure path: owner exception does not hang waiting caller

**Type:** api
**Preconditions:** 
- Unit test environment with ability to inject exceptions
- Two concurrent callers waiting on the same cache identity
- The "owner" computation (the one actually running `compute_factor_lab_all`) is configured to raise a simulated exception

**Steps:**
1. Patch `compute_factor_lab_all` to raise a test exception midway
2. Spawn two concurrent requests for the SAME Factor-Lab-all cache identity on a cold MISS
3. The first becomes the owner and raises; the second waits on the lock+event
4. Measure the second caller's wait time; verify it does NOT exceed the bounded timeout (e.g., 45 seconds)
5. Verify the second caller does NOT hang indefinitely

**Expected outcome:** 
The waiting caller's wait elapses within the declared timeout, it falls back to an independent compute, and both eventually return a result (the fallback payload may differ from a fresh owner-initiated compute due to the injected exception, but crucially, no hang occurs).

**Pass criteria:** 
Waiting caller's total time ≤ timeout + fallback compute time AND no deadlock (process remains responsive) AND no unbounded wait.

---

### TC-05 — Byte-identity: restructured compute output matches pre-iteration reference (all-history + as_of window)

**Type:** api
**Preconditions:** 
- Fixture DB loaded with a small number of ScannerResult and ForwardReturn rows
- Pre-iteration reference vectors available (existing oracle)
- Both all-history and a windowed as_of available in the fixture

**Steps:**
1. Run the restructured `compute_factor_lab_all` against the fixture for all-history
2. Extract every `(factor, horizon, decile)` value from the response
3. Compare against the pre-iteration pinned reference vector element-wise
4. Repeat the same for an as_of window that spans part of the fixture's runs
5. Verify every value matches byte-identically

**Expected outcome:** 
Every `(factor, horizon, decile)` output value is identical to the reference (not merely close; exact byte-for-byte match).

**Pass criteria:** 
All extracted values match the reference vectors with zero deviations (use strict equality, not approximate). Test mirrors existing `test_all_horizons_per_factor_is_byte_identical_to_compute_factor_lab` pattern.

---

### TC-06 — Shipped config return-value bound: peak resident size is bounded against real live basis

**Type:** api
**Preconditions:** 
- SHIPPED `config.yaml` (no test-override; real `factor_all_return_pool_size_limit_observations`)
- Backend loaded with the full deep basis (real run and observation counts, ~771,129 observations × 5 horizons)
- A fixture-sized reproduction that requires real chunking (enough runs/observations to trigger the bound)

**Steps:**
1. Instrument `_all_factor_observations_by_horizon` to measure peak resident memory of the returned `pools` structure
2. Execute the function against the live deep basis for all-history
3. Capture the peak VmRSS or traced peak
4. Record the config value that governs the bound (e.g., `factor_all_return_pool_size_limit_observations`)
5. Verify the peak is actually bounded by that config value

**Expected outcome:** 
Peak resident memory of the returned pools is strictly less than `server.memory_cap_mb` (6144 MB) with a measurable margin stated in the dev handoff.

**Pass criteria:** 
Measured peak ≤ `server.memory_cap_mb` AND margin is explicitly documented in the dev handoff (e.g., "peak was 5200 MiB, margin 944 MiB"). The bound must be proven against the REAL live run/observation count, not a fixture-sized width.

---

### TC-07 — Single-factor path regression guard: existing tests pass unmodified

**Type:** api
**Preconditions:** 
- Existing test suite in `test_research_streaming.py` and `test_factor_lab_all.py` (the single-factor Evidence page tests)
- Specifically: `test_all_factors_fires_one_shared_pool_read_not_n`, `test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis`, and related tests

**Steps:**
1. Run the existing `_factor_observations` / `_runs_with_fr` / `_fr_slice_map` test suite unchanged
2. Execute `pytest apps/backend/tests/test_research_streaming.py -v` and the byte-identity tests from `test_factor_lab_all.py`
3. Capture pass/fail results

**Expected outcome:** 
All existing tests pass; no test code is modified; output confirms the Evidence page's AG-8 fix (iter-29) is untouched.

**Pass criteria:** 
All tests in the run PASS (exit code 0) AND test count is unchanged from the pre-iteration baseline (no new test failures, no tests removed).

---

### TC-08 — Required-still-passing journeys: J-01, J-03, J-04, J-05, J-08, J-09 deterministic replay

**Type:** api
**Preconditions:** 
- Golden journey-scripts exist: `journey-scripts/J-01.json`, `J-03.json`, `J-04.json`, `J-05.json`, `J-08.json`, `J-09.json`
- Deterministic replay runner available
- No LLM intervention expected (or LLM fallback applied for journeys without prior golden)

**Steps:**
1. Run the deterministic replay lane for each of J-01, J-03, J-04, J-05, J-08, J-09
2. Capture results: PASS/FAIL row for each journey
3. Aggregate: count passes and fails
4. Check for any reconciliation overturns (LLM fallback used)

**Expected outcome:** 
All six journeys return PASS; zero FAIL rows; zero reconciliation overturns.

**Pass criteria:** 
Pass count = 6, Fail count = 0, Reconciliation overturns = 0.

---

### TC-09 — Ride-along: J-06.json deterministic replay produces discoverable artifact (non-blocking)

**Type:** artifact
**Preconditions:** 
- `journey-scripts/J-06.json` exists
- Deterministic replay runner available
- A designated artifact output location configured (e.g., `reports/qa/`)

**Steps:**
1. Run J-06.json through the deterministic replay lane
2. Capture or locate the results artifact (file path or result record)
3. Verify the artifact is discoverable and citable in the QA/audit report

**Expected outcome:** 
A PASS or FAIL row exists for J-06 in a discoverable artifact (closing the "no artifact exists" gap named at iter-30).

**Pass criteria:** 
Artifact path is non-empty AND file exists AND contains a valid PASS or FAIL result row for J-06 (the outcome itself—PASS or FAIL—is NOT a blocker; existence is the pass criterion).

---

## Summary

| Test ID | Type | Scope |
|---------|------|-------|
| TC-01 | api | Cold-MISS HTTP 200 success |
| TC-02 | api | Zero MemoryError verification |
| TC-03 | api | Single-flight guard (exactly ONE compute) |
| TC-04 | api | Failure-path no-hang (timeout + fallback) |
| TC-05 | api | Byte-identity (all-history + window) |
| TC-06 | api | Shipped-config return-value bound proof |
| TC-07 | api | Single-factor regression guard |
| TC-08 | api | Required-still-passing journeys (6 journeys) |
| TC-09 | artifact | Ride-along J-06 artifact existence |

**Total:** 9 test cases  
**API tests:** 8  
**Artifact checks:** 1  
**Browser tests:** 0 (Frontend Present: no)
