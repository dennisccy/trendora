# Goal Iteration 24 Functional Test Plan

**Phase:** goal-ops-hardening-iter-24  
**Date:** 2026-07-26  
**Frontend Present:** yes

## Phase Goal

Disclose the existing background historical forward-aggregate dispatch so operators can see it live via the top-bar readiness badge and a new `/data` panel, instead of reconstructing its timing from raw database timestamps.

## Test Cases

### TC-01 — Warm Backend at Rest, No Dispatch

**Type:** api  
**Preconditions:** Backend has been running for ≥10s with no background dispatch ever triggered since boot.

**Steps:**
1. Poll `GET /api/health`

**Expected outcome:** HTTP 200 response with `background_compute.active == []` and `background_compute.recent_outcomes == []`; `readiness == "ready"`.

**Pass criteria:** Response contains `{"background_compute": {"active": [], "recent_outcomes": []}}` and `readiness` field value is `"ready"`.

---

### TC-02 — Dispatch Registry Gains Active Entry on Historical Request

**Type:** api  
**Preconditions:** Backend is running; forward-aggregate evidence for a historical as-of date is not `"ready"` for the current `dataset_version`.

**Steps:**
1. Trigger a `/backtest` request (or MCP `query_backtest` call) for that historical as-of
2. Verify the request returns within J-08's existing budget (no blocking)
3. Immediately poll `GET /api/health`

**Expected outcome:** Response HTTP 200 with `background_compute.active` containing exactly one entry with keys: `asof_key`, `dataset_version`, `started_at`, `elapsed_ms`, `horizons_done == 0`, `horizons_total == len(cfg.walk_forward.horizons)`.

**Pass criteria:** `active` array has length 1; `horizons_total` matches the configured horizon count; `horizons_done == 0` (dispatch just started).

---

### TC-03 — Badge Indicator Renders During In-Flight Dispatch

**Type:** browser  
**Preconditions:** A historical as-of dispatch is in flight (from TC-02 setup or a fresh `/backtest` request).

**Steps:**
1. On any page (e.g., homepage or `/data`), inspect the top-bar health badge area
2. Poll `GET /api/health` during the window
3. Verify the badge displays an active-compute indicator

**Expected outcome:** Element with `data-testid="background-compute-indicator"` is present, rendering text naming the count of in-flight windows (e.g., "(1)").

**Pass criteria:** Indicator element is rendered and visible in the top bar; text shows the correct in-flight count; existing readiness pill is NOT hidden or replaced.

---

### TC-04 — /data Panel Displays In-Flight Window Detail

**Type:** browser  
**Preconditions:** The `/data` page is open while a background dispatch is in-flight (same as TC-03).

**Steps:**
1. Navigate to or stay on `/data`
2. Locate the `BackgroundComputePanel` (element `data-testid="background-compute-panel"`)
3. Verify the panel displays the active window detail

**Expected outcome:** Panel shows the as-of key, elapsed time (a value > 0), and the current `horizons_done`/`horizons_total` pair (e.g., "Horizons: 2/8 (started 3s ago)").

**Pass criteria:** All three pieces of information are visible and correct; elapsed time is a positive number; horizon counts match the `/api/health` active entry.

---

### TC-05 — Recent Outcome Recorded on Dispatch Completion

**Type:** api  
**Preconditions:** A background dispatch (from TC-02 setup) has completed successfully.

**Steps:**
1. Poll `GET /api/health` after the dispatch finishes
2. Verify the response contains the outcome record
3. Query the `forward_aggregate_cache` table for the corresponding `(asof_key, dataset_version)` row's `created_at` timestamp

**Expected outcome:** 
- `background_compute.active` no longer contains the identity
- `background_compute.recent_outcomes[0]` (newest entry) shows:
  - `outcome == "completed"`
  - `finished_at` timestamp (ISO 8601 UTC)
  - `duration_ms >= 0`
  - `reason == null`
  - `finished_at` is within 2s of the DB row's `created_at`

**Pass criteria:** Outcome entry is recorded; outcome is "completed"; `finished_at` and `duration_ms` are present and consistent with DB timestamps; `reason` is null.

---

### TC-06 — Failed Dispatch Releases Guard and Allows Re-dispatch

**Type:** api  
**Preconditions:** A test is configured to inject a failure into one horizon's `forward_aggregates_ingest_cached` call inside `_run_historical_forward_aggregates_dispatch`.

**Steps:**
1. Trigger the injected-failure dispatch scenario
2. Poll `GET /api/health` after the worker's exception is caught
3. Verify the active slot is released
4. Trigger another `/backtest` request for the SAME `(asof_key, dataset_version)` identity
5. Verify the dispatch is re-attempted (a new `active` entry appears)

**Expected outcome:**
- After the failure, `background_compute.recent_outcomes[0]` shows:
  - `outcome == "failed"`
  - `reason` is a non-null string (the caught exception message)
  - The corresponding identity is NOT in `active`
- A subsequent request for the same identity creates a new `active` entry (re-dispatch allowed)

**Pass criteria:** Failed outcome is recorded with a reason string; active slot is released; re-dispatch proceeds without a permanent wedge.

---

### TC-07 — Steady-State Health Endpoint Latency Within Budget

**Type:** api  
**Preconditions:** Backend at rest; no background compute in flight; no concurrent ingest.

**Steps:**
1. Poll `GET /api/health` repeatedly (e.g., 100 times in succession, 10ms apart) using an existing latency harness
2. Record max observed response latency
3. Update `reports/perf-budgets.md`'s Iteration 24 section with the result

**Expected outcome:** Max observed latency is `<= 0.1s` (100ms).

**Pass criteria:** All polls complete in ≤0.1s; recorded latency in perf-budgets.md confirms the budget is met.

---

### TC-08 — Backend Restart Clears In-Memory State

**Type:** api  
**Preconditions:** At least one background dispatch has completed since the current backend process started; the outcome is recorded in `recent_outcomes`.

**Steps:**
1. Stop the backend process
2. Start the backend process
3. Poll `GET /api/health` after boot

**Expected outcome:** Response shows `background_compute.active == []` and `background_compute.recent_outcomes == []`; the process-lifetime history is cleared.

**Pass criteria:** Both arrays are empty after restart; in-memory state is not persisted.

---

### TC-09 — Bounded Ring Respects Config Cap

**Type:** api  
**Preconditions:** `startup.background_compute_history_size` is set to a small value (e.g., 2); more than that many dispatches are completed.

**Steps:**
1. Trigger N background dispatches where N > `startup.background_compute_history_size` (e.g., trigger 5 dispatches with history cap = 2)
2. Poll `GET /api/health`
3. Verify the `recent_outcomes` length

**Expected outcome:** 
- `len(background_compute.recent_outcomes) <= startup.background_compute_history_size`
- Most recent entry is first in the array (newest-first ordering)

**Pass criteria:** Outcomes array length does not exceed the configured cap; entries are ordered newest-first.

---

### TC-10 — End-to-End Browser Walkthrough (J-09 Primary Test)

**Type:** browser  
**Preconditions:** Backend is running; a historical as-of date that is NOT yet `"ready"` for the current `dataset_version` is known and accessible.

**Steps:**
1. Open the app to any page
2. Navigate to `/backtest` (or use MCP `query_backtest`)
3. Request a backtest for the historical as-of from step 1
4. Observe the top-bar badge for the in-flight indicator (should appear within 2-5s)
5. Navigate to `/data` and observe the `BackgroundComputePanel` with active dispatch detail
6. Wait for the dispatch to complete (typically 10-60s depending on horizon count)
7. Observe the badge indicator disappear
8. Refresh `/data` and verify the new outcome appears in `recent_outcomes`
9. Verify the outcome's `duration_ms` is > 0 and `finished_at` is a recent timestamp

**Expected outcome:**
- Badge indicator (`data-testid="background-compute-indicator"`) is present during dispatch, absent after
- `/data` panel displays the active window during dispatch, then shows the completed outcome
- Outcome record includes real measured `duration_ms` matching the observed elapsed time (±2s)
- All numbers displayed match the `/api/health` payload values

**Pass criteria:** All steps complete; badge and panel visibility toggle correctly; outcome is recorded with correct timestamps and duration; no fabricated/estimated completion times shown.

---

### TC-11 — Config Validation: background_compute_history_size

**Type:** api  
**Preconditions:** Config validation tests are running.

**Steps:**
1. Attempt to start the backend with `startup.background_compute_history_size: 0` (invalid)
2. Attempt to start the backend with `startup.background_compute_history_size: 1` (valid minimum)
3. Attempt to start the backend with `startup.background_compute_history_size: 5` (valid default)

**Expected outcome:** 
- Step 1 fails at startup with a config validation error
- Steps 2 and 3 succeed and boot normally

**Pass criteria:** Validation enforces `>= 1`; default value of 5 is applied when not specified.

---

### TC-12 — Health Endpoint Degrade-on-Error

**Type:** api  
**Preconditions:** A test injects an error into `get_background_compute_status()` (e.g., a mock exception).

**Steps:**
1. Poll `GET /api/health` while the injected error is active
2. Verify the response is HTTP 200 (not a 5xx error)
3. Verify `background_compute` field is present with safe defaults

**Expected outcome:** Response HTTP 200 with `background_compute` degrading to `{"active": [], "recent_outcomes": []}` on any compute error; the endpoint does not blank or return 5xx.

**Pass criteria:** HTTP 200 is returned; `background_compute` field is present; it mirrors the existing readiness/preflight degrade-on-error convention.

---

### TC-13 — Regression: J-01, J-03, J-04, J-05, J-06, J-07, J-08 Still Passing

**Type:** browser  
**Preconditions:** All seven required-still-passing journeys have been previously validated in earlier iterations.

**Steps:**
1. Run deterministic replay for each journey or execute its core flow via browser
2. Verify each journey's test cases pass

**Expected outcome:** All 7 journeys remain green; no regression introduced by the background-compute disclosure changes.

**Pass criteria:** 7/7 journeys pass; no new failures in previously-passing tests.

---

## Summary

**Total test cases:** 13  
**API tests:** TC-01, TC-02, TC-05, TC-06, TC-07, TC-08, TC-09, TC-11, TC-12 (9 tests)  
**Browser tests:** TC-03, TC-04, TC-10, TC-13 (4 tests)  

**Key verification points:**
- Background-compute registry bookkeeping (`started_at`, `horizons_done`, `horizons_total`)
- Bounded `recent_outcomes` ring (config-capped, newest-first)
- Top-bar badge indicator appearance/disappearance
- `/data` panel display and content correctness
- Outcome correctness against database timestamps (±2s tolerance)
- Error handling and guard-release semantics
- No regressions to existing journeys
