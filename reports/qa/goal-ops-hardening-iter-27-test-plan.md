# goal-ops-hardening-iter-27 Functional Test Plan

**Phase:** goal-ops-hardening-iter-27  
**Date:** 2026-07-26  
**Frontend Present:** yes

## Phase Goal

Close two ESCALATE-flagged anti-goal findings with fresh evidence: an unhandled `IntegrityError` (HTTP 500) when two concurrent `/backtest` requests race a never-scanned historical date's forward-returns write, and the Data Manager coverage panel silently rendering all-zero "not yet computed" for a fully populated database. Extend `_insert_run_forward_returns` tolerant-duplicate handling to the mid-loop autoflush point; add stale-snapshot fallback with honest labels to `coverage_from_storage`; no new user capability.

## Test Cases

### TC-01 — Concurrent `/backtest` requests both return HTTP 200 (no 500 error)

**Type:** api  
**Preconditions:**
- Backend is running
- Database contains historical price data but NO `ScannerRun` for a target never-scanned historical date (e.g., 1995-01-01)
- Both requests will attempt to create the same `ForwardReturn` keys concurrently

**Steps:**
1. In a terminal, start monitoring `logs/backend.log` for exceptions: `tail -f logs/backend.log | grep -i "exception\|error"`
2. Open two browser tabs or initiate two curl requests targeting `GET /api/backtest?as_of=1995-01-01&universe=...` simultaneously
3. Both requests race the same historical date's `_insert_run_forward_returns` call
4. Capture both HTTP response codes
5. Record the exact window (timestamps) when both requests completed
6. Stop the log monitor and extract any "Exception in ASGI application" lines from that window

**Expected outcome:**  
Both requests receive HTTP 200 status code. No unhandled ASGI exception appears in `logs/backend.log` for the request window.

**Pass criteria:**  
- HTTP status code == 200 for both requests  
- `logs/backend.log` contains zero "Exception in ASGI application" lines for the window when both requests ran  
- Both responses are valid JSON (not error frames)

---

### TC-02 — Concurrent race produces normal `/backtest` page content (full-page capture)

**Type:** browser  
**Preconditions:**
- Backend is running, frontend is accessible at http://localhost:3000
- A never-scanned historical date is selected (e.g., 1995-01-01) in the backtest form
- Browser DevTools or screenshot tool is ready to capture full page

**Steps:**
1. Navigate to `/backtest` page in the browser
2. Select the never-scanned historical date (e.g., 1995-01-01) in the form
3. In a second terminal, curl the same `/api/backtest?as_of=1995-01-01&...` request to simulate concurrent load
4. Simultaneously, submit the backtest form in the browser (pressing "Run Backtest" or equivalent)
5. Wait for both requests to complete
6. Take a full-page screenshot (not just viewport) of the browser's backtest page after both requests finish
7. Inspect the screenshot for evidence content (Scorecard, AsOfScanSummary components, etc.)

**Expected outcome:**  
The `/backtest` page displays normal evidence content with Scorecard and AsOfScanSummary rendered. No blank page, frozen content, or application-error frame appears.

**Pass criteria:**  
- Full-page screenshot shows Scorecard component rendered  
- Full-page screenshot shows AsOfScanSummary component rendered  
- No error message or blank white space where evidence should appear  
- Page is interactive (not frozen)

---

### TC-03 — Mid-loop autoflush collision caught and rolled back (unit test)

**Type:** api  
**Preconditions:**
- Unit test framework (pytest) is configured
- A test database session is created
- Helper to stage a competing `ForwardReturn` row via a separate committed connection is available

**Steps:**
1. Create a test in `apps/backend/tests/test_forward_testing_concurrency.py` (or extend the existing file)
2. Open a separate DB connection/session and insert a `ForwardReturn` row with key `(run_id, symbol, horizon)` — **commit it** to simulate a concurrent writer
3. In the main test session, call `_insert_run_forward_returns(...)` or `backfill_run_forward_returns(...)` with the same `(run_id, symbol)` pair
4. The per-symbol loop will add a colliding `ForwardReturn` to the session (step 413 in forward_testing.py)
5. On the **next** symbol's iteration, when the loop calls `close_on(...)` (line 390), SQLAlchemy's autoflush triggers
6. Autoflush encounters the still-pending duplicate insert from the prior symbol and raises `IntegrityError`
7. Assert that the exception is caught, the session is rolled back, and the loop continues for remaining symbols/horizons
8. Assert that exactly one `ForwardReturn` row exists for the colliding key (the concurrent writer's row, not duplicated)

**Expected outcome:**  
No unhandled exception propagates to the caller. The loop continues processing remaining symbols/horizons. Exactly one row per colliding key survives in the database.

**Pass criteria:**  
- Test assertion: `IntegrityError` is NOT raised to the caller  
- Test assertion: remaining symbols/horizons were processed (loop did not terminate early)  
- Test assertion: database contains exactly one `ForwardReturn` row for each `(run_id, symbol, horizon)` key (no duplicate, no missing)

---

### TC-04 — Unrelated `IntegrityError` still propagates (unit test)

**Type:** api  
**Preconditions:**
- Unit test framework (pytest) is configured
- A test database session and a constraint other than `(run_id, symbol, horizon)` uniqueness is known (e.g., a NOT NULL constraint on a required field)

**Steps:**
1. Create a test in `apps/backend/tests/test_forward_testing_concurrency.py`
2. Modify the test to inject an `IntegrityError` caused by a **different** constraint (not the `(run_id, symbol, horizon)` uniqueness)
3. Call `_insert_run_forward_returns(...)` with a condition that triggers that different constraint violation
4. Assert that the `IntegrityError` is **NOT** caught by the new narrowly-scoped handler
5. Assert that the exception propagates unchanged to the caller

**Expected outcome:**  
An `IntegrityError` from a constraint other than the targeted `(run_id, symbol, horizon)` uniqueness is NOT suppressed. It propagates with the original exception type and message.

**Pass criteria:**  
- Test assertion: `IntegrityError` is raised to the caller  
- Test assertion: exception message matches the non-targeted constraint  
- Test assertion: the catch block is narrow, not a blanket try/except around the entire loop

---

### TC-05 — Stale coverage snapshot served with correct status and figures (API test)

**Type:** api  
**Preconditions:**
- Backend is running
- Database has a `CoverageSnapshot` row for an `asof_key` under an **older** `dataset_version` (e.g., version 1)
- A request-path operation (like a historical `/backtest` create-once) has bumped the global `_membership_dataset_version` to a newer version (e.g., version 2)
- No exact-match row exists for the current version

**Steps:**
1. Verify database state: confirm a `CoverageSnapshot` row exists under `dataset_version=1` for the target `asof_key`
2. Verify the `_membership_dataset_version` is now 2 (bumped by request-path operation)
3. Call `GET /api/data` with default `as_of=None` view
4. Inspect the JSON response's `coverage` key
5. Verify the `coverage_status` field
6. Verify the `price_start`, `price_end`, `universe_count` fields match the older row's values
7. Verify `stale_dataset_version` field contains the older version number
8. Verify `stale_computed_at` is an ISO-8601 UTC timestamp from the older row

**Expected outcome:**  
The response includes `coverage_status: "stale"`, non-zero `price_start`/`price_end`/`universe_count` from the older snapshot, and `stale_dataset_version` naming that older version.

**Pass criteria:**  
- HTTP status code == 200  
- `response.coverage.coverage_status == "stale"`  
- `response.coverage.price_start` is not null and not zero  
- `response.coverage.price_end` is not null and not zero  
- `response.coverage.universe_count` is not zero  
- `response.coverage.stale_dataset_version` is present and equals the older version  
- `response.coverage.stale_computed_at` is a valid ISO-8601 UTC timestamp

---

### TC-06 — Data Manager coverage panel renders stale label with prior-snapshot figures (browser test)

**Type:** browser  
**Preconditions:**
- Frontend is running at http://localhost:3000
- Backend has the stale-snapshot state from TC-05 (older `CoverageSnapshot`, bumped `_membership_dataset_version`)
- `/data` page is accessible

**Steps:**
1. Navigate to `http://localhost:3000/data`
2. Wait for the Data Manager page to load and the coverage panel to render
3. Inspect the coverage panel section (price history and universe count display)
4. Take a screenshot of the coverage panel
5. Read the displayed text label

**Expected outcome:**  
The coverage panel displays the prior-snapshot figures (e.g., "1996-01-02 → 2026-07-22" for price history, "UNIVERSE 540" for count) instead of the all-zero sentinel ("— → —" / "UNIVERSE 0"). A visible label reads: "Coverage as of a prior scan (version {version_number}) — refreshes on the next data job"

**Pass criteria:**  
- Screenshot shows non-zero price range (not "— → —")  
- Screenshot shows non-zero universe count (not "UNIVERSE 0")  
- Screenshot displays the exact label text: "Coverage as of a prior scan (version {stale_dataset_version}) — refreshes on the next data job"  
- Label is visually distinct from the normal `current` state (calm tone, not alarming)

---

### TC-07 — Fresh-install database still serves "not_yet_computed" state (unit test)

**Type:** api  
**Preconditions:**
- A fresh test database with no `CoverageSnapshot` rows under any `dataset_version`
- `_membership_dataset_version` is properly initialized

**Steps:**
1. Create a test in `apps/backend/tests/test_api_data.py` (or `test_data_manager.py`)
2. Call `coverage_from_storage(as_of=None)` or `GET /api/data` against the fresh database
3. Inspect the returned payload

**Expected outcome:**  
The response includes `coverage_status: "not_yet_computed"`, all-zero payload shape (matching the pre-fix sentinel), and null `stale_dataset_version`/`stale_computed_at`.

**Pass criteria:**  
- `response.coverage_status == "not_yet_computed"`  
- `response.price_start`, `response.price_end`, `response.universe_count` are all zero or null (unchanged from pre-fix behavior)  
- `response.stale_dataset_version` is null  
- `response.stale_computed_at` is null  
- Payload shape is byte-identical to the pre-fix all-zero sentinel (regression guard)

---

### TC-08 — Normal ingest finalize serves "current" status (unit test)

**Type:** api  
**Preconditions:**
- Backend is running
- A normal ingest job (fetch/backfill/rebuild) has completed and its finalize hook has refreshed `CoverageSnapshot` for the current `dataset_version`

**Steps:**
1. Create a test in `apps/backend/tests/test_api_data.py` (or `test_data_manager.py`)
2. Simulate or run a normal ingest finalize that calls `_upsert_coverage_snapshot(...)`
3. Call `coverage_from_storage(as_of=None)` or `GET /api/data`
4. Inspect the returned payload

**Expected outcome:**  
The response includes `coverage_status: "current"`, non-zero figures from the freshly-computed row, and null `stale_dataset_version`/`stale_computed_at`.

**Pass criteria:**  
- `response.coverage_status == "current"`  
- `response.price_start`, `response.price_end`, `response.universe_count` are non-zero (from the current snapshot)  
- `response.stale_dataset_version` is null  
- `response.stale_computed_at` is null  
- No stale label is rendered on the `/data` page (regression guard for the common path)

---

### TC-09 — Required journeys J-01, J-03, J-04, J-06, J-09 remain green (browser replay)

**Type:** browser  
**Preconditions:**
- Golden replay scripts exist for J-01, J-03, J-04, J-06, J-09
- Frontend and backend are running
- For J-09's regression check: the test uses a date that **already has a `scanner_runs` snapshot but incomplete aggregates** (per iteration-state.md "Do not redo"); **never use a never-scanned date**

**Steps:**
1. Run each golden replay script for J-01, J-03, J-04, J-06, J-09 in sequence
2. For each replay, execute the full user journey (navigation, form fill, submission, evidence verification)
3. Record the result (PASS or FAIL) for each journey
4. Capture screenshots of any failures

**Expected outcome:**  
All five journeys replay as PASS with zero FAIL rows in the test output.

**Pass criteria:**  
- J-01: PASS  
- J-03: PASS  
- J-04: PASS  
- J-06: PASS  
- J-09: PASS (using a date with existing `scanner_runs` snapshot, not a never-scanned date)

---

### TC-10 — `perf-budgets.md` Iteration 26 timestamp corrected

**Type:** artifact  
**Preconditions:**
- `reports/perf-budgets.md` exists
- Iteration 26 section is present with the mislabeled timestamp `19:14:25Z`
- `logs/backend.log` contains the boot log entry with the correct timezone-stamped UTC timestamp

**Steps:**
1. Open `reports/perf-budgets.md` and locate the Iteration 26 section (around line 3817)
2. Read the mislabeled timestamp in the uptime line
3. Open `logs/backend.log` and search for the boot log entry (e.g., "boot" or "started" timestamp)
4. Extract the correct UTC timestamp from the boot log's own timezone-stamped line
5. Update the Iteration 26 section's label to match the correct timestamp verbatim
6. Verify that no other content in the Iteration 26 section is changed

**Expected outcome:**  
The Iteration 26 section's timestamp label now matches the boot log's own UTC-stamped line. No other content in that section is modified.

**Pass criteria:**  
- The corrected timestamp in `perf-budgets.md` matches the UTC timestamp from `logs/backend.log` **verbatim**  
- No other lines in the Iteration 26 section are changed  
- The file diffs cleanly (only the timestamp line is modified)

---

### TC-11 — All backend tests pass in ONE combined pytest invocation

**Type:** api  
**Preconditions:**
- New tests from TC-03, TC-04, TC-05, TC-07, TC-08 are implemented in:
  - `apps/backend/tests/test_forward_testing_concurrency.py` (TC-03, TC-04)
  - `apps/backend/tests/test_api_data.py` or `test_data_manager.py` (TC-05, TC-07, TC-08)
- pytest is configured with the shared `loaded_engine` fixture

**Steps:**
1. Run a **single combined pytest invocation** with a selector that includes all new tests (e.g., `pytest -k "test_mid_loop_collision or test_unrelated_integrity_error or test_stale_coverage or test_not_yet_computed or test_current_coverage"`)
2. Do NOT run multiple separate pytest commands or the full suite
3. Launch via `setsid nohup ... &` (in-turn polling pattern) rather than backgrounding across turn boundaries
4. Capture the pytest output summary line

**Expected outcome:**  
All selected tests pass. The shared `loaded_engine` fixture builds once (not per-file). A single summary line shows all tests PASSED.

**Pass criteria:**  
- Exit code == 0  
- Summary line: "X passed" where X includes at least 5 tests (TC-03, TC-04, TC-05, TC-07, TC-08)  
- No "FAILED" line in output  
- Fixture build log shows only one instance of "loaded_engine" initialization  
- Total elapsed time is reasonable for a single fixture build (~1h+, per iter-26 precedent)

---

### TC-12 — Blueprint coverage fields match actual implementation

**Type:** artifact  
**Preconditions:**
- `runs/goal-session-ops-hardening/state/blueprint.md` exists and contains the Coverage payload row
- The backend `GET /api/data` implementation is complete with the three new fields

**Steps:**
1. Open `runs/goal-session-ops-hardening/state/blueprint.md` and locate the Coverage payload row (or table)
2. Note the registered field names: `coverage_status`, `stale_dataset_version`, `stale_computed_at`
3. Make an actual `GET /api/data` request to the running backend
4. Parse the JSON response and inspect the `coverage` object's keys
5. Compare the actual response field names against the blueprint

**Expected outcome:**  
The actual JSON response includes exactly the fields registered in the blueprint: `coverage_status`, `stale_dataset_version`, `stale_computed_at`. No additional fields, no renamed fields, no dropped fields.

**Pass criteria:**  
- `response.coverage` includes `coverage_status` (string: "current" | "stale" | "not_yet_computed")  
- `response.coverage` includes `stale_dataset_version` (string | null)  
- `response.coverage` includes `stale_computed_at` (string ISO-8601 | null)  
- No additional undocumented fields appear in the response  
- Field names match the blueprint verbatim (case-sensitive)

---

## Summary

**Total test cases:** 12  
**API tests:** 6 (TC-01, TC-04, TC-05, TC-07, TC-08, TC-11)  
**Browser tests:** 3 (TC-02, TC-06, TC-09)  
**Artifact checks:** 3 (TC-10, TC-12, and implicit file integrity)

**Coverage by finding:**
- **AG-8 (concurrent `/backtest` race):** TC-01, TC-02, TC-03, TC-04
- **AG-3 (coverage honesty):** TC-05, TC-06, TC-07, TC-08
- **Regression guard (passing journeys):** TC-09
- **File integrity:** TC-10, TC-12
- **Combined fixture constraint:** TC-11

All test cases are designed to be executable within a single integration environment (backend + frontend running). No external API calls or live data services. All tests respect the shared fixture build constraint (single combined pytest invocation for backend tests).
