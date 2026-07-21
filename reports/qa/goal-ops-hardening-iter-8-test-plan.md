# goal-ops-hardening-iter-8 Functional Test Plan

**Phase:** goal-ops-hardening-iter-8
**Date:** 2026-07-21
**Frontend Present:** no

## Phase Goal

Restore J-05's regressed acceptance step (heavy-ingest responsiveness of `GET /api/health`) by bounding peak memory consumption in the ingest finalize hook's warm loops, closing the critical AG-8 violation introduced in iter-7.

## Test Cases

### TC-01 — Real back-to-back heavy ingest: VmPeak stays under memory cap

**Type:** api
**Preconditions:** 
- Backend is running via `scripts/start-backend.sh` (production mode) on an idle host
- `ulimit -v` memory cap is enforced at `memory_cap_mb=6144` MB
- Environment variables set: `export TMPDIR TMP TEMP=/home/dennis-chan/.cache/iad/iad.goal-ops-hard-<session>.tmp`

**Steps:**
1. Start a backend process with `scripts/start-backend.sh`, verifying it listens on `CHAIN_BACKEND_URL` (default `http://localhost:8000`)
2. Record the process PID: `PID=$(pgrep -f "uvicorn.*--port")`
3. Initiate a full-universe rebuild ingest job via the SDK/admin interface
4. Sample `/proc/<PID>/status` VmPeak and VmSize every 5 seconds throughout both ingests (write timestamps and values to a log file)
5. Once the rebuild completes, immediately initiate a second heavy backfill job
6. Continue sampling `/proc/<PID>/status` for the full duration of the second ingest
7. Record the final peak VmPeak value and compare it to `memory_cap_mb=6144`

**Expected outcome:** 
- VmPeak never exceeds 6144 MB at any sample point
- VmPeak stays below 6144 MB with a documented safety margin (e.g., ≤ 5800 MB)
- No `MemoryError` exception is raised or logged during either ingest
- Both ingests complete successfully to terminal status (`success` or `failed`, not stuck `running`)

**Pass criteria:** 
`max(VmPeak samples) <= 5800 MB AND no MemoryError in logs AND both jobs reach terminal status`

---

### TC-02 — GET /api/health responsiveness during back-to-back heavy ingest

**Type:** api
**Preconditions:**
- Backend is running with the same real back-to-back heavy ingest scenario as TC-01
- A polling loop is ready to call `GET /api/health` every 2 seconds for the full duration

**Steps:**
1. Begin the same full-universe rebuild + heavy backfill sequence as TC-01
2. Start a polling loop that calls `curl -s http://localhost:8000/api/health --max-time 5` every 2 seconds
3. Log each response: timestamp, HTTP status code, response time (ms), and any timeout/error
4. Continue polling throughout both ingests and for 30 seconds after the second ingest completes
5. Stop polling and compile a summary of all responses

**Expected outcome:**
- Every poll returns HTTP 200 within its committed budget (existing `GET /api/health` SLA, typically ≤ 500 ms)
- Zero timeouts (curl --max-time 5 never exceeded)
- Zero hangs (no poll blocks for >5 seconds without responding)
- Health status values are honest (reflect actual backend readiness state throughout)

**Pass criteria:** 
`all_polls == 200 AND max(response_time) <= 500ms AND timeout_count == 0 AND no_hangs`

---

### TC-03 — MemoryError on first item: loop aborts, category omitted

**Type:** api
**Preconditions:**
- Unit test environment with access to `apps/backend/tests/test_data_manager.py`
- Ability to monkeypatch `forward_testing.compute_drawdown_expectations_cached` to raise `MemoryError` on the first call

**Steps:**
1. Write a unit test that monkeypatches `forward_testing.compute_drawdown_expectations_cached` to raise `MemoryError` on the first invocation
2. Call `_refresh_ingest_aggregates()` within the test with a fixture ingest job that would normally warm drawdown_expectations
3. Capture the return value: the dict `aggregates_refreshed` (which lists category strings for successfully-warmed categories)
4. Verify the loop stopped attempting further items and the warm loop completed (did not propagate the exception)
5. Inspect logs for the "aborted remaining drawdown_expectations warm — memory pressure" message
6. Check the ingest job status (should reach `success` or `failed`, not stuck `running`)

**Expected outcome:**
- The drawdown-expectations warm loop stops after the first `MemoryError` is caught
- No items after the first are attempted
- `aggregates_refreshed` does NOT include `"drawdown_expectations"` (category omitted because zero items were successfully warmed)
- Ingest job reaches a terminal status without manual intervention
- Log contains the "aborted remaining drawdown_expectations warm — memory pressure" message

**Pass criteria:** 
`"drawdown_expectations" not in aggregates_refreshed AND job_status in ["success", "failed"] AND "aborted remaining" in logs`

---

### TC-04 — MemoryError in first item: same-process recovery (no leaked lock)

**Type:** api
**Preconditions:**
- Same monkeypatched scenario as TC-03 (MemoryError on first drawdown_expectations item)
- The test process is still running with the same session/transaction state

**Steps:**
1. After the injected-`MemoryError` ingest job completes (from TC-03), perform a fresh DB read in the SAME process
2. Example: call `refresh_coverage_snapshot("2024-01-01")` or make a `GET /api/data` request to the still-running backend
3. Record whether the read succeeds (HTTP 200 or successful method return) or fails (timeout, lock error, transaction error)
4. If it succeeds, verify the result is sensible (non-empty, no corruption)

**Expected outcome:**
- The subsequent DB read succeeds without timeout or lock-contention error
- No "resource temporarily unavailable" or "deadlock detected" errors
- The process did not hang or leak an open transaction from the failed warm loop

**Pass criteria:** 
`subsequent_read_status == "success" AND no_lock_error AND no_timeout`

---

### TC-05 — MemoryError after ≥1 item succeeded: category partially reported

**Type:** api
**Preconditions:**
- Unit test environment with access to `apps/backend/tests/test_data_manager.py`
- Ability to monkeypatch a warm function to raise `MemoryError` on the SECOND invocation (first succeeds)

**Steps:**
1. Write a unit test that monkeypatches `forward_testing.compute_drawdown_expectations_cached` to succeed on the first call, then raise `MemoryError` on the second and subsequent calls
2. Call `_refresh_ingest_aggregates()` with a fixture that would normally warm 3+ ledger claims
3. Capture `aggregates_refreshed`
4. Verify the loop warmed at least the first item successfully, then stopped on the second's `MemoryError`
5. Check that no items after the second are attempted
6. Verify the ingest job reaches a terminal status

**Expected outcome:**
- The first drawdown_expectations item is warmed successfully
- The loop stops on the second item's `MemoryError`
- No items after the second are attempted
- `aggregates_refreshed` DOES include `"drawdown_expectations"` (because ≥1 item was successfully warmed, the category is honestly reported)
- Log contains "aborted remaining drawdown_expectations warm — memory pressure"
- Job reaches terminal status

**Pass criteria:** 
`"drawdown_expectations" in aggregates_refreshed AND second_item_not_attempted AND job_status in ["success", "failed"]`

---

### TC-06 — Non-MemoryError exception: existing isolate-and-continue behavior unchanged

**Type:** api
**Preconditions:**
- Test `test_finalize_hook_drawdown_expectations_isolates_claim_that_raises` exists in `apps/backend/tests/test_data_manager.py`
- This test monkeypatches a warm function to raise a non-`MemoryError` exception (e.g., `ValueError`)

**Steps:**
1. Run the existing test: `pytest apps/backend/tests/test_data_manager.py::test_finalize_hook_drawdown_expectations_isolates_claim_that_raises -v`
2. Capture the exit code and pass/fail status
3. Verify the test behaves identically to its behavior before this iteration's code changes

**Expected outcome:**
- Test passes (exit code 0)
- Non-`MemoryError` exceptions are still caught and logged per-item, the loop continues attempting further items
- The generic isolate-and-continue behavior is unchanged

**Pass criteria:** 
`test_exit_code == 0 AND test_status == "PASSED"`

---

### TC-07 — Warmth correctness: byte-identical to fresh compute

**Type:** api
**Preconditions:**
- Backend is running with this iteration's code
- A ledger claim and its corresponding as-of date are selected
- Ability to directly call `forward_testing.compute_drawdown_expectations_cached` and a fresh uncached compute function

**Steps:**
1. Select a ledger claim and as-of date
2. Call the cached (warmed) version: `cached_result = forward_testing.compute_drawdown_expectations_cached(claim, as_of_date)`
3. Clear any internal cache/memoization
4. Call a fresh uncached compute (construct a fresh context, bypass any cache): `fresh_result = compute_fresh_drawdown_expectations(claim, as_of_date)`
5. Serialize both results to JSON (or pickle, or appropriate format)
6. Compare the byte-serialized outputs

**Expected outcome:**
- Cached and fresh results are byte-identical (or equivalent after deterministic serialization)
- No correctness regression from the error-handling change

**Pass criteria:** 
`serialized(cached_result) == serialized(fresh_result) OR deep_equality(cached_result, fresh_result)`

---

### TC-08 — Unit test suite: targeted files pass, zero failures

**Type:** api
**Preconditions:**
- Environment variables set: `export TMPDIR TMP TEMP=/home/dennis-chan/.cache/iad/iad.goal-ops-hard-<session>.tmp`
- Backend dependencies installed and `pytest` available

**Steps:**
1. Run the targeted test suite (do NOT run the full test suite concurrently):
   ```bash
   pytest apps/backend/tests/test_data_manager.py apps/backend/tests/test_start_backend_script.py -v
   ```
2. Capture stdout, stderr, and exit code
3. Count total tests, passes, failures, errors

**Expected outcome:**
- All tests pass (no failures, no errors)
- Exit code 0

**Pass criteria:** 
`failure_count == 0 AND error_count == 0 AND exit_code == 0`

---

### TC-09 — J-01 and J-03: golden replay scripts pass

**Type:** api
**Preconditions:**
- Golden replay scripts exist for J-01 and J-03 (deterministic test scripts that exercise past-commit scenarios)
- Backend is running with this iteration's code

**Steps:**
1. Run J-01's golden replay script: `<path-to-j01-replay-script>`
2. Record exit code and summary (pass/fail per step)
3. Run J-03's golden replay script: `<path-to-j03-replay-script>`
4. Record exit code and summary (pass/fail per step)
5. Verify no step failures are attributable to this iteration's diff (backend error-handling change)

**Expected outcome:**
- Both scripts run to completion with all steps passing
- No step failures related to ingest finalize, aggregate refresh, or memory handling
- Exit codes 0 for both scripts

**Pass criteria:** 
`j01_exit_code == 0 AND j03_exit_code == 0 AND no_unexpected_step_failures`

---

### TC-10 — J-04: non-blocking boot readiness passes

**Type:** api
**Preconditions:**
- J-04 is defined as: "Backend boots with visible readiness state, does not block startup on compute"
- Backend can be started fresh (e.g., `scripts/start-backend.sh`)

**Steps:**
1. Start a fresh backend instance
2. Verify the boot sequence completes (process listens on `CHAIN_BACKEND_URL`)
3. Call `GET /api/health` within 2 seconds of startup
4. Verify the response is honest: either `ready: true` (if warmups complete fast) or `ready: false` with a non-error reason (e.g., "warming aggregates")
5. Poll `GET /api/health` until it reaches `ready: true` (do not exceed 60 seconds)
6. Verify the startup did not block (readiness state was visible throughout, not a late error)

**Expected outcome:**
- Boot sequence completes successfully
- `GET /api/health` is reachable and honest throughout boot
- No blocking errors that require a restart
- Readiness state transitions from false → true within expected time

**Pass criteria:** 
`boot_completes AND health_responsive AND honest_status_throughout AND no_blocking_errors`

---

## Summary

**Total test cases:** 10

**Test case breakdown by type:**
- **API tests:** 10 (TC-01 through TC-10)
  - Live measurement and responsiveness: TC-01, TC-02
  - Unit tests for error-handling behavior: TC-03, TC-04, TC-05, TC-06, TC-07, TC-08
  - Integration replay and boot verification: TC-09, TC-10

**Key coverage:**
- Peak memory bounding during real back-to-back heavy ingest (TC-01)
- Health endpoint responsiveness under memory pressure (TC-02)
- MemoryError-specific early-abort behavior: first item (TC-03, TC-04), partial warm (TC-05)
- Correctness preservation (TC-07)
- Regression detection via existing tests and golden replays (TC-06, TC-08, TC-09, TC-10)

All tests must pass for the iteration to succeed; special emphasis on TC-01 and TC-02 (live measurement confirming the fix) and TC-03/TC-05 (unit verification of the new error-handling contract).
