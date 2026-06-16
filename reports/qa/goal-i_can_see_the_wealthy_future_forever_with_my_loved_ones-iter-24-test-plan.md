# Goal Iteration 24 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-24
**Date:** 2026-06-16
**Frontend Present:** no

## Phase Goal

Reconcile two stale `served == engine_output` byte-equality guards in `test_api_engine.py` that J-81's legitimate additive `forward_returns` key broke, turning the full backend pytest suite GREEN (EXIT_CODE=0) with zero served-payload or endpoint changes.

## Test Cases

### TC-01 — test_api_themes_equals_engine_output: Canonical payload byte-equality modulo forward_returns

**Type:** api
**Preconditions:**
- Backend pytest environment configured with `apps/backend/.venv/`
- Loaded test fixture (loaded_engine) with seeded price data
- Test file `apps/backend/tests/test_api_engine.py` updated per spec

**Steps:**
1. Run the targeted test: `cd apps/backend && .venv/bin/python -m pytest tests/test_api_engine.py::test_api_themes_equals_engine_output -xvs`
2. Verify test calls `score_themes(session, asof, cfg)` to get `expected` engine output
3. Fetch `/api/themes` via TestClient and store as `served`
4. Strip `forward_returns` key from each row in served: `stripped = {"rows": [{k: v for k, v in row.items() if k != "forward_returns"} for row in served["rows"]]}`
5. Assert `stripped == expected` (byte-for-byte equality on canonical scored payload)
6. Assert each served row's `forward_returns` exists with `[fr["horizon"] for fr in row["forward_returns"]] == list(cfg.walk_forward.horizons)`
7. Assert `len(served["rows"]) == len(cfg.themes)` (existing assertion kept)

**Expected outcome:** 
- Byte-equality assertion passes on all canonical fields (scores, ranks, components, breadth, trend, members)
- `forward_returns` field verified to exist on every served row with exactly the configured horizons
- Test passes with exit code 0

**Pass criteria:** 
- Test exits with `PASSED` verdict (no assertion failures)
- Canonical payload (excluding `forward_returns`) is byte-identical to engine output
- Each row carries `forward_returns` array with length == `len(cfg.walk_forward.horizons)`

---

### TC-02 — test_api_sectors_equals_engine_output: Canonical payload byte-equality modulo forward_returns

**Type:** api
**Preconditions:**
- Backend pytest environment configured with `apps/backend/.venv/`
- Loaded test fixture (loaded_engine) with seeded price data
- Test file `apps/backend/tests/test_api_engine.py` updated per spec

**Steps:**
1. Run the targeted test: `cd apps/backend && .venv/bin/python -m pytest tests/test_api_engine.py::test_api_sectors_equals_engine_output -xvs`
2. Verify test calls `score_sectors(session, asof, cfg)` to get `expected` engine output
3. Fetch `/api/sectors` via TestClient and store as `served`
4. Strip `forward_returns` key from each row in served: `stripped = {"rows": [{k: v for k, v in row.items() if k != "forward_returns"} for row in served["rows"]]}`
5. Assert `stripped == expected` (byte-for-byte equality on canonical scored payload)
6. Assert each served row's `forward_returns` exists with `[fr["horizon"] for fr in row["forward_returns"]] == list(cfg.walk_forward.horizons)`
7. Assert `served["benchmark"] == "SPY"` (existing assertion kept)
8. Assert `len(served["rows"]) == 31` (existing assertion kept)

**Expected outcome:** 
- Byte-equality assertion passes on all canonical fields (scores, ranks, components, breadth, trend, members)
- `forward_returns` field verified to exist on every served row with exactly the configured horizons
- Benchmark and row count assertions pass
- Test passes with exit code 0

**Pass criteria:** 
- Test exits with `PASSED` verdict (no assertion failures)
- Canonical payload (excluding `forward_returns`) is byte-identical to engine output
- Each row carries `forward_returns` array with length == `len(cfg.walk_forward.horizons)`
- Benchmark == "SPY" and row count == 31

---

### TC-03 — Full backend pytest suite reaches EXIT_CODE=0 with no regressions

**Type:** api
**Preconditions:**
- Backend pytest environment configured with `apps/backend/.venv/`
- All seeded test fixtures available
- Both targeted tests (TC-01 and TC-02) pass
- No source code changes outside `apps/backend/tests/test_api_engine.py`

**Steps:**
1. Run the full backend test suite: `cd apps/backend && .venv/bin/python -m pytest tests/ -v 2>&1 | tee test_output.log`
2. Capture both stdout and stderr
3. Extract final summary line (e.g., `844 passed, 4 skipped, 0 failed`)
4. Verify EXIT_CODE == 0
5. Confirm the two prior failures (`test_api_themes_equals_engine_output` and `test_api_sectors_equals_engine_output`) are now in the PASSED count
6. Confirm no NEW failures are present
7. Confirm no regressions in other passing tests

**Expected outcome:**
- Full suite completes with EXIT_CODE=0
- Summary shows approximately 846 passed tests and 4 skipped (0 failed)
- The two previously failing tests now pass
- All anti-goal tests remain green (single-source, no-recompute, immutability, no-lookahead, no-fabrication)

**Pass criteria:**
- `EXIT_CODE == 0` (command exit status)
- Final summary line shows `0 failed` and no exception tracebacks
- Count of passed tests >= 844 (at least the prior 2 failures now pass)
- Skipped count remains at 4
- No new failures or regressions since iter-23

---

### TC-04 — Target journeys J-81, J-82 served payloads byte-identical (regression check)

**Type:** api
**Preconditions:**
- Backend running with seeded data
- Full test suite passing (TC-03 passes)
- No served-payload or endpoint changes introduced

**Steps:**
1. Access `/api/themes` endpoint
2. Verify response status code is 200
3. Access `/api/sectors` endpoint
4. Verify response status code is 200
5. Verify both endpoints' `rows` array is non-empty and contains expected themed/sector objects with `forward_returns` field
6. Verify `/api/stocks` endpoint returns 200 with canonical payload (modulo `forward_returns`) unchanged

**Expected outcome:**
- Both endpoints return 200 status with valid JSON
- Theme rows carry `forward_returns` (J-81 feature intact)
- Sector rows carry `forward_returns` (J-81 feature intact)
- Stock rows carry `forward_returns` with expected structure
- No served-value mutations or drift from iter-23

**Pass criteria:**
- `/api/themes` returns HTTP 200
- `/api/sectors` returns HTTP 200
- Each row in themes/sectors payload contains `forward_returns` with > 0 entries
- `/api/stocks` returns 200 with canonical scores intact (tested by TC-03 byte-equality assertion)

---

### TC-05 — Required-still-passing journeys J-03, J-04, J-06, J-09, J-21, J-75 remain green

**Type:** api
**Preconditions:**
- Full backend test suite passing (TC-03)
- Tests for target journeys exist in `test_api_engine.py` or related test files

**Steps:**
1. Verify test suite output includes passing test cases for:
   - J-03: Dashboard setup status (test_api_dashboard_equals_engine_with_real_candidate_counts)
   - J-04: Sector endpoint (test_api_sectors_equals_engine_output)
   - J-06: Single-source coherence (test_api_stock_detail_equals_list_row_single_source_j06)
   - J-09: Sector properties (test_api_sectors_serves_config_name_description_and_members)
   - J-21: As-of resolution (test_repointed_endpoints_echo_resolved_asof)
   - J-75: Forward returns on stocks (test_api_stocks_equals_engine_output)
2. Confirm none of these journey tests are in the failed list
3. Confirm no assertion failures in any of these test outputs

**Expected outcome:**
- All six required-still-passing journey tests pass
- No regressions in single-source guarantees
- No served-value changes for these journeys

**Pass criteria:**
- All six test cases exit with PASSED verdict
- J-06 byte-identity (detail == list row) still holds
- J-75 forward_returns field structure unchanged on `/api/stocks`

---

## Summary

**Total test cases:** 5
**API tests:** 5
**Browser tests:** 0
**Artifact checks:** 0

**Scope:** Test-only reconciliation of two stale byte-equality guards to accept J-81's legitimate additive `forward_returns` field while maintaining all anti-goal guarantees (single-source of truth, no-recompute, immutability, no-lookahead, no-fabrication). Success = full suite GREEN with EXIT_CODE=0 and zero served-payload drift.
