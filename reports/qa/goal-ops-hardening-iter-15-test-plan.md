# goal-ops-hardening-iter-15 Functional Test Plan

**Phase:** goal-ops-hardening-iter-15
**Date:** 2026-07-23
**Frontend Present:** no

## Phase Goal

Root-cause and fix `/backtest`'s concurrent cache-miss latency (211.8s finding from UT-04) by eliminating redundant same-key recomputation and/or resolving GIL/WAL contention, ensuring `GET /api/backtest` responds within the committed ≤1.5s budget even when the ingest finalize warm is running concurrently.

## Test Cases

### TC-01 — Same-Key Concurrent Cache-Miss De-duplication

**Type:** api  
**Preconditions:**
- Backend is running with the iter-15 fix deployed
- Engine is loaded with committed seed data
- No prior cache entries exist for the test horizons

**Steps:**
1. In a test harness, create N≥5 concurrent caller threads targeting `forward_aggregates_cached` with identical never-yet-cached `(horizon, asof_key, dataset_version)` keys
2. Instrument the underlying `compute_forward_aggregates` function with a call-count monkeypatch to record invocations
3. Issue all N concurrent calls simultaneously against the shared engine
4. Wait for all N calls to complete
5. Assert that `compute_forward_aggregates`'s row-scan body was invoked exactly 1 time for that key (via the instrumentation counter)
6. Assert that all N callers received byte-identical payload responses

**Expected outcome:** The fix's de-duplication mechanism prevents redundant computation; the first caller computes and persists, the remaining N-1 callers either wait for or reuse the single in-flight result without re-running the heavy aggregation.

**Pass criteria:** Instrumented call count = 1, and all N payloads `==` to each other (byte-identical).

---

### TC-02 — Concurrent Write During Read Wall-Clock Ratio

**Type:** api  
**Preconditions:**
- Backend is running with the iter-15 fix deployed
- Engine is loaded and a fixture is pre-sized so a single uncontended `compute_forward_aggregates` call measures ≥1.0 second wall-clock
- A background writer thread can issue committed writes (e.g., inserting new rows into `scanner_results` or updating `JobProgress`)

**Steps:**
1. Measure the wall-clock baseline: invoke `compute_forward_aggregates` once in isolation with no concurrent writes; record elapsed time `T_baseline`
2. Start a background writer thread that issues repeated committed writes throughout step 3
3. Invoke `compute_forward_aggregates` again with the background write activity live; record elapsed time `T_concurrent`
4. Calculate the ratio `ratio = T_concurrent ÷ T_baseline`
5. Assert `ratio ≤ 5.0x` (smoke guard — a gross regression would yield ratio >> 5x)

**Expected outcome:** The fix maintains reasonable performance under concurrent writes; the ratio indicates whether GIL or WAL contention is significant. A ratio ≤ 5x indicates the fix has not introduced uncontrolled overhead.

**Pass criteria:** `T_baseline ≥ 1.0s` (fixture sized correctly), `T_concurrent` recorded, `ratio ≤ 5.0x`.

---

### TC-03 — Byte-Identity of compute_forward_aggregates Remains Unchanged

**Type:** api  
**Preconditions:**
- Backend is running with the iter-15 fix deployed
- Engine is loaded with committed seed data
- The existing pinned reference implementation from iter-14 is available (32-test suite in `test_forward_testing_aggregates_streaming.py`)

**Steps:**
1. Run the existing 32-test suite in `test_forward_testing_aggregates_streaming.py` unchanged
2. For each configured horizon (all 5) and both `as_of` conditions (as_of=None, historical as_of):
   - Invoke `compute_forward_aggregates` with the test fixture
   - Assert the output `==` the pre-rewrite reference payload

**Expected outcome:** The iter-15 wrapper/de-dup fix changes only `forward_aggregates_cached`'s concurrency handling, not `compute_forward_aggregates` itself. All computed values remain identical to iter-14's proven reference.

**Pass criteria:** All 32 existing tests pass with zero changes to the suite; output byte-identity confirmed for all 5 horizons and all `as_of` variants.

---

### TC-04 — Operator-Supervised Full-Basis Cache-Miss Latency Reproduction

**Type:** api  
**Preconditions:**
- Backend is NOT currently running; a fresh start is required
- Host is cooled and at idle Tctl
- Current DB has `scanner_results` ≥775,094 rows, `forward_returns` ≥3,935,930 rows (confirmed by direct read)
- Operator is available to start the backend via `scripts/start-backend.sh` under host-guard confinement with 1Hz hwmon sampler and thermal watchdog armed
- The iter-15 fix is deployed

**Steps:**
1. Operator starts the backend via `scripts/start-backend.sh` with host-guard caps active; records process PID and exact start timestamp
2. Operator allows services to reach ready state
3. While the ingest finalize warm (all 5 configured horizons) is running, operator issues a live `GET /api/backtest` request for a not-yet-warmed horizon (triggering a cache-miss)
4. Server-side timing is recorded: measure the request's wall-clock duration from request reception to response completion
5. Operator records the measured latency and attaches any relevant console output, hwmon sampler data, and backend logfile entries for the measurement window
6. Developer transcribes the result into `reports/perf-budgets.md` immediately below the original iter-14 211.8s finding, labeled PASS if ≤1.5s or WARN if > 1.5s with the exact measured value

**Expected outcome:** The fix reduces the concurrent cache-miss latency from 211.8s to within or near the committed ≤1.5s budget. Even if still elevated, the fix should show a material improvement; any remaining slowness is honestly recorded and attributed via cross-reading `logs/backend.log` and `logs/hwmon/hwmon.csv` for ambient load.

**Pass criteria:** A fresh backend start, measured latency recorded in `reports/perf-budgets.md`, verdict assigned (PASS or WARN). Measurement window artifacts (console output, timestamps, hwmon data) attached with attribution.

---

### TC-05 — Spot-Check Page Loads Under Concurrent Warm

**Type:** api  
**Preconditions:**
- Same as TC-04: the operator-supervised pass is running; backend is warm and the ingest finalize warm for all 5 horizons is in progress
- The pages `/stocks`, `/sectors`, `/scanner-runs`, and `/evidence` are reachable

**Steps:**
1. While the warm is running (same pass as TC-04), issue requests to the on-load endpoints for each page:
   - `/api/stocks` (or `/stocks` HTTP GET)
   - `/api/sectors` (or `/sectors` HTTP GET)
   - `/api/scanner-runs` (or `/scanner-runs` HTTP GET)
   - `/api/evidence` (or `/evidence` HTTP GET)
2. Record the response time and HTTP status for each request
3. For each response, confirm it is not a blank or frozen frame (i.e., the body contains expected data structures or HTML elements)
4. Compare each response time against its committed budget (if budgets exist in `reports/perf-budgets.md` for these pages)
5. Record the results: each page receives a verdict PASS (within budget and renders fully) or WARN (measured time, page still renders)

**Expected outcome:** Under the concurrent warm, the four pages either load within their budgets or degrade gracefully with visible progress—never a blank, frozen, or application-error page.

**Pass criteria:** All four pages respond with HTTP 200 (or equivalent success); each is recorded as PASS (on budget) or WARN (over budget, with recorded time); none render blank or frozen.

---

### TC-06 — Health Endpoint Availability During Concurrent Warm

**Type:** api  
**Preconditions:**
- Same as TC-04: the operator-supervised pass is running; backend is warm and the ingest finalize warm for all 5 horizons is in progress
- The health check endpoint is reachable at `GET /api/health`

**Steps:**
1. For the full duration of the concurrent warm (TC-04/TC-05), poll `GET /api/health` at 1Hz throughout
2. Record every response: HTTP status code, wall-clock latency, and any response body
3. Assert every poll returns HTTP 200 within its existing committed budget
4. Assert no poll hangs or wedges the request (no indefinite wait)

**Expected outcome:** The health endpoint remains responsive and never locked up or wedged, confirming the concurrent warm does not deadlock or freeze the service.

**Pass criteria:** Every 1Hz poll returns HTTP 200 within budget; no poll times out or hangs; at least 100+ successful polls during the measurement window (indicating the warm ran ≥100 seconds).

---

### TC-07 — Regression: Required-Still-Passing Journeys J-01/J-03/J-04/J-05

**Type:** browser  
**Preconditions:**
- Backend is running with the iter-15 fix deployed
- Frontend is running
- Deterministic golden scripts exist for J-01, J-03, J-04, J-05 (or LLM fallback is used for journeys without a current golden)

**Steps:**
1. Execute the deterministic golden replay for J-01 (backfill honors requested range, zero-work explanation)
2. Execute the deterministic golden replay for J-03 (no per-run range cap)
3. Execute the deterministic golden replay for J-04 (non-blocking boot with visible status)
4. Execute the deterministic golden replay for J-05 (aggregates precomputed at ingest)
5. For any journey without a current golden script, invoke the LLM browser-qa fallback
6. Assert each journey either re-verifies PASS or (for LLM fallback) returns a PASS verdict

**Expected outcome:** The iter-15 fix does not regress any of the four required-still-passing journeys. Each continues to pass the same assertions.

**Pass criteria:** All four journeys report PASS (either golden replay or LLM fallback); none transitions from passing to failing.

---

### TC-08 — Failure Path: In-Flight Computation Exception Does Not Deadlock

**Type:** api  
**Preconditions:**
- Backend is running with the iter-15 fix deployed
- Engine is loaded with committed seed data
- A test harness can artificially inject an exception into an in-flight `compute_forward_aggregates` invocation

**Steps:**
1. Create N concurrent callers requesting the same never-yet-cached `(horizon, asof_key, dataset_version)` key
2. Configure the first caller (or a monkeypatched `compute_forward_aggregates`) to raise an exception after entering the computation
3. Issue all N concurrent calls simultaneously
4. Assert that the N-1 waiting callers do not block indefinitely (i.e., all resolve or timeout within a bounded time, e.g., 45 seconds, matching the existing test file's `BOUNDED_TIMEOUT_S`)
5. Each waiting caller either:
   - Receives a clean, isolated error (propagated from the failed computation), or
   - Independently recomputes and returns a correct payload

**Expected outcome:** The fix's in-flight-computation mechanism gracefully handles failure; a waiting caller does not hang permanently if the owning computation crashes.

**Pass criteria:** All N-1 waiting callers resolve within `BOUNDED_TIMEOUT_S` (e.g., 45s); none hang; each either raises a clean error or returns a correct payload.

---

## Summary

**Total test cases:** 8

**Breakdown by type:**
- **API tests:** 7 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-08)
- **Browser tests:** 1 (TC-07)
- **Artifact checks:** 0

**Key validation gates:**
- Same-key de-duplication mechanism (TC-01) proves the fix eliminates redundant computation
- Wall-clock ratio under concurrent writes (TC-02) bounds GIL/WAL overhead
- Byte-identity preservation (TC-03) confirms `compute_forward_aggregates` is untouched
- Operator-supervised full-basis reproduction (TC-04) proves the fix closes the 211.8s finding (PASS if ≤1.5s; WARN otherwise)
- Page loads and health endpoint (TC-05/TC-06) confirm the concurrent warm does not break other surfaces
- Regression suite (TC-07) confirms J-01/J-03/J-04/J-05 remain passing
- Failure-path handling (TC-08) proves waiting callers never deadlock
