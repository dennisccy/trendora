# Goal Iteration 27 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27
**Date:** 2026-06-17
**Frontend Present:** yes

## Phase Goal

The operator can confirm-gate a from-scratch snapshot rebuild that makes newly-expanded universe members appear in every read surface with an "N members absent" diagnostic, and every forward-return column on all read surfaces is now paired with a max-drawdown read from the same stored data.

## Test Cases

### TC-01 — Coverage diagnostic banner renders when members absent

**Type:** browser
**Preconditions:** System is running with a resolved universe that has members absent from the latest snapshot (verify via backend API `GET /api/data` response `coverage.absent_from_latest_snapshot > 0`)

**Steps:**
1. Navigate to `/data` page
2. Inspect the page for a diagnostic banner message

**Expected outcome:** A yellow/warn-colored banner is visible stating "N universe members absent from the latest snapshot — rebuild to include them" where N is the exact count of absent members
**Pass criteria:** Banner text is visible and matches the count from the API `coverage` response

---

### TC-02 — Coverage diagnostic banner does not render when all members present

**Type:** browser
**Preconditions:** System has a resolved universe where all members are present in the latest snapshot (verify via `GET /api/data` response `coverage.absent_from_latest_snapshot == 0`)

**Steps:**
1. Navigate to `/data` page
2. Inspect the page for the diagnostic banner

**Expected outcome:** No banner is visible
**Pass criteria:** The page renders normally without the "members absent" banner; banner is conditionally hidden when count is 0

---

### TC-03 — Rebuild action exists and is confirm-gated

**Type:** browser
**Preconditions:** Coverage diagnostic banner is visible (TC-01 state)

**Steps:**
1. On `/data` page, locate the "Rebuild snapshots for current universe" button
2. Click the button
3. A confirm modal appears
4. Inspect the modal for the Confirm button

**Expected outcome:** A modal overlay appears with a message describing the rebuild action and a visible, accessible Confirm button
**Pass criteria:** Modal is confirm-gated; Confirm button exists and is persistently visible (not obscured by scroll); Cancel option also available

---

### TC-04 — Rebuild job POSTs kind="rebuild" to API

**Type:** api
**Preconditions:** Rebuild modal is open (from TC-03)

**Steps:**
1. Click Confirm in the modal
2. Capture the HTTP request sent to the backend (via browser network tab or curl simulation)

**Expected outcome:** A POST request is sent to `POST /api/data/jobs` with JSON body containing `{"kind": "rebuild"}`
**Pass criteria:** HTTP 200/201 response; response includes a job record with `kind: "rebuild"` and `status: "running"`

---

### TC-05 — Rebuild progress updates in real-time

**Type:** browser
**Preconditions:** Rebuild job is running (from TC-04)

**Steps:**
1. Observe the job-progress card on `/data` page (via the existing J-66 job-card UI)
2. Wait 2–5 seconds and refresh or poll the page
3. Verify progress counters (e.g., "snapshots 10/X", "dates processed") are incrementing

**Expected outcome:** Progress card shows live progress ticks, current activity line, and counters that increase over time
**Pass criteria:** Progress counters increment; no counter exceeds its total; activity line shows meaningful status

---

### TC-06 — Rebuild completes and snapshot set is regenerated

**Type:** browser
**Preconditions:** Rebuild job is in progress (from TC-05)

**Steps:**
1. Monitor the rebuild job until it completes (status changes to a terminal state)
2. Navigate to `/stocks` page
3. Verify that stock rows are still being served (page is not broken)
4. Navigate back to `/data` and inspect the run-history section
5. Verify that the rebuild run is recorded with a terminal status (e.g., "completed")

**Expected outcome:** Rebuild completes; `/stocks` page still renders and serves rows; run-history shows the rebuild record with a success status; scanner_runs table has been cleared and repopulated with new rows
**Pass criteria:** Terminal job status visible; `/stocks` rows served; run-history entry shows the rebuild with `kind: "rebuild"` and a terminal status

---

### TC-07 — Price seed (bars table) is untouched after rebuild

**Type:** api
**Preconditions:** Rebuild job completed (from TC-06)

**Steps:**
1. Query the backend API for the committed seed bars count: `curl -s http://localhost:8835/api/data/debug/bars-count`
2. Compare against the known seed count before the iteration (from committed seed manifest)

**Expected outcome:** The bars table row count remains unchanged; no committed price data was deleted during rebuild
**Pass criteria:** Bars count matches the pre-rebuild baseline; seed integrity is preserved

---

### TC-08 — Max-drawdown columns appear on /stocks leaderboard

**Type:** browser
**Preconditions:** System is at a historical as-of date with post-snapshot seed bars available (e.g., `?asof=2025-12-31`)

**Steps:**
1. Navigate to `/stocks?asof=2025-12-31`
2. Locate the forward-return columns (1d, 5d, 10d, 20d, 60d)
3. Scroll right or inspect the table to see if max-drawdown columns are rendered beside the forward-return columns

**Expected outcome:** Five max-drawdown columns are visible and labeled (MDD-1d, MDD-5d, MDD-10d, MDD-20d, MDD-60d) or similar; each cell shows a percentage ≤ 0 (e.g., "-5.2%", "-0.8%")
**Pass criteria:** All five MDD columns present; values are ≤ 0 or NA; column headers are sortable (J-48)

---

### TC-09 — Max-drawdown columns match return columns (NA discipline)

**Type:** browser
**Preconditions:** Same as TC-08

**Steps:**
1. On `/stocks?asof=2025-12-31`, find a row where the 10d return column shows "NA"
2. Check the corresponding 10d MDD column

**Expected outcome:** When the forward-return is NA (not enough post-bars), the MDD is also NA (not fabricated as 0)
**Pass criteria:** MDD shows NA (em dash or "—") wherever the return is NA; no fabricated 0 values

---

### TC-10 — Max-drawdown columns are colour-graded

**Type:** browser
**Preconditions:** Same as TC-08

**Steps:**
1. On `/stocks?asof=2025-12-31`, inspect the styling of MDD cells
2. Find cells with different MDD values (e.g., -0.5%, -5%, -15%)

**Expected outcome:** Cells are colour-graded on a red/negative scale (more negative = redder)
**Pass criteria:** Negative palette tokens applied; colour intensity correlates with magnitude of loss

---

### TC-11 — Max-drawdown columns are sortable (J-48)

**Type:** browser
**Preconditions:** Same as TC-08

**Steps:**
1. On `/stocks?asof=2025-12-31`, click the header of a max-drawdown column (e.g., MDD-10d)
2. Verify the table re-orders by that column
3. Click the header again to reverse sort

**Expected outcome:** Table rows reorder by the MDD value (least negative first, then most negative); clicking again reverses the order; no refetch or recompute occurs (client-side sort only)
**Pass criteria:** Sort order changes; rows reorder correctly; no API call is triggered (view transform only)

---

### TC-12 — Max-drawdown on Stock Detail matches /stocks

**Type:** browser
**Preconditions:** On `/stocks?asof=2025-12-31` with a visible stock row

**Steps:**
1. Click on a stock row to open Stock Detail (new tab)
2. On the Stock Detail page, locate the forward-return panel
3. Verify max-drawdown columns are rendered alongside the forward-return columns

**Expected outcome:** Stock Detail shows the same five MDD columns for the same ticker and as-of date as the leaderboard; values match exactly
**Pass criteria:** MDD values on detail page == MDD values on leaderboard for the same stock/horizon (J-06 identity)

---

### TC-13 — Max-drawdown on /themes leaderboard matches Backtest

**Type:** browser
**Preconditions:** Navigate to `/themes?asof=2025-12-31` with historical seed bars available

**Steps:**
1. On `/themes?asof=2025-12-31`, locate the max-drawdown columns
2. Note the MDD values for a specific theme at a specific horizon (e.g., Technology theme, 10d MDD)
3. Navigate to `/backtest` (keeping the same `?asof`)
4. Find the same theme in the Backtest "Top Themes" section
5. Compare the MDD value

**Expected outcome:** Theme MDD on `/themes` == Theme MDD on `/backtest` for the same date and horizon (equal-weight member-basket drawdown)
**Pass criteria:** Values match exactly (J-06 single-source principle); no recompute in the read path

---

### TC-14 — Max-drawdown on /sectors leaderboard matches Backtest

**Type:** browser
**Preconditions:** Navigate to `/sectors?asof=2025-12-31`

**Steps:**
1. On `/sectors?asof=2025-12-31`, locate a sector row and its MDD values
2. Navigate to `/backtest` with the same `?asof`
3. Find the same sector in the Backtest "Top Sectors" section
4. Compare the MDD value for the same horizon

**Expected outcome:** Sector MDD on `/sectors` == Sector MDD on `/backtest` for the same date and horizon (sector ETF's own return)
**Pass criteria:** Values match exactly; sector = the ETF's own stored drawdown, not a derived average

---

### TC-15 — Aggregate mean-MDD appears on Backtest evidence table

**Type:** browser
**Preconditions:** Navigate to `/backtest?asof=2025-12-31`

**Steps:**
1. Scroll to the Return Attribution section
2. Locate the aggregate statistics table (by bucket, by setup, by regime)
3. Inspect the table columns for a "Mean MDD" or similar column beside "Mean Return"

**Expected outcome:** A mean-MDD column is visible alongside the mean-return column; values show aggregate average max-drawdown for the cohort
**Pass criteria:** Column exists; values are ≤ 0; NA shown where sample size is below threshold; `n` count visible

---

### TC-16 — Aggregate mean-MDD on Research tables

**Type:** browser
**Preconditions:** Navigate to `/research` (any Research tab: Factor Lab, Setup & Pattern Lab, Regime×Setup×Pattern)

**Steps:**
1. On the Setup & Pattern Lab (Event Study), scroll to the aggregates table
2. Inspect the columns for a "Mean MDD" column beside "Mean Return"
3. Repeat for the Regime×Setup×Pattern table if visible

**Expected outcome:** Mean-MDD columns are rendered alongside return stats; values follow the same NA discipline (not fabricated when N < min-sample)
**Pass criteria:** Column present; values are ≤ 0 or NA; sample size `n` is visible; consistent with Backtest values

---

### TC-17 — Max-drawdown is NA at/near latest (not fabricated)

**Type:** browser
**Preconditions:** Navigate to `/stocks` (without `?asof`, or with `?asof` set to the latest date)

**Steps:**
1. On `/stocks` (latest date), inspect the MDD columns
2. Check that every MDD value is either a real ≤0 value OR NA (never a fabricated 0)
3. If any bar is within 60 days of the latest date, the corresponding 60d MDD should be NA (insufficient post-bars)

**Expected outcome:** At the latest as-of date, MDD is NA where there are fewer than the horizon's required post-bars; never a fabricated 0 or positive value
**Pass criteria:** All MDD cells at latest are either NA or genuine values; no fabrication; consistency with the no-lookahead principle

---

### TC-18 — Max-drawdown math: running peak and ≤ 0

**Type:** api
**Preconditions:** Access the backend directly (pytest or test endpoint)

**Steps:**
1. Run the unit test `test_max_drawdown_calculation` in the test suite (verify it exists)
2. The test checks: (a) MDD is computed as `min over j of ( low_j / max(entry_close, high_1…high_j) − 1 )` over the horizon window; (b) MDD is ≤ 0; (c) running peak is seeded at the as-of-D close

**Expected outcome:** Test passes; MDD helper correctly implements the running-peak logic; no tail-invariance violation (the MDD at day 30 equals the MDD at day 31 if no new low occurs)
**Pass criteria:** Test passes with 0 failures

---

### TC-19 — Max-drawdown NULL when realized_return NULL

**Type:** api
**Preconditions:** Access backend test data

**Steps:**
1. Run the unit test `test_forward_returns_max_drawdown_na_gate` in the test suite
2. The test checks that for any `(run, symbol, horizon)` in the `forward_returns` table, if `realized_return` is NULL then `max_drawdown` is also NULL

**Expected outcome:** Test passes; NA gate is identical for both fields
**Pass criteria:** Test passes; every NULL `realized_return` has a NULL `max_drawdown`

---

### TC-20 — _ADDITIVE_COLUMNS registry updated for max_drawdown

**Type:** artifact
**Preconditions:** Inspect `apps/backend/app/db.py`

**Steps:**
1. Locate the `_ADDITIVE_COLUMNS` list
2. Verify that `("forward_returns", "max_drawdown", "ALTER TABLE forward_returns ADD COLUMN max_drawdown <type>")` is registered

**Expected outcome:** Entry exists in the registry; the DDL matches the nullable float pattern of existing columns (`mae`, `mfe`)
**Pass criteria:** Entry is present; nullable REAL/float type; matches the schema in `models.py` `ForwardReturn.max_drawdown`

---

### TC-21 — test_api_stocks_equals_engine_output updated

**Type:** api
**Preconditions:** Run backend tests

**Steps:**
1. Run the test `test_api_stocks_equals_engine_output` from `apps/backend/tests/test_api_engine.py`
2. Verify the test strips the additive `max_drawdown` key before the byte-equality check
3. Verify the test separately asserts the field exists and that configured horizons are present

**Expected outcome:** Test passes; the byte-equality guard is updated to exclude the new additive key; new assertion confirms the field and horizons
**Pass criteria:** Test passes; no "unexpected key" failure; separate assertion for `max_drawdown` and horizons passes

---

### TC-22 — test_api_themes_equals_engine_output updated

**Type:** api
**Preconditions:** Run backend tests

**Steps:**
1. Run the test `test_api_themes_equals_engine_output` from `apps/backend/tests/test_api_engine.py`
2. Verify it strips the additive `max_drawdown` key and asserts the field exists

**Expected outcome:** Test passes; MDD field is excluded from byte-equality, then separately verified
**Pass criteria:** Test passes; no additive-key conflicts

---

### TC-23 — test_api_sectors_equals_engine_output updated

**Type:** api
**Preconditions:** Run backend tests

**Steps:**
1. Run the test `test_api_sectors_equals_engine_output` from `apps/backend/tests/test_api_engine.py`
2. Verify it strips the additive `max_drawdown` key and asserts the field exists

**Expected outcome:** Test passes
**Pass criteria:** Test passes; MDD field handled correctly

---

### TC-24 — frontend: tsc --noEmit passes

**Type:** artifact
**Preconditions:** Run TypeScript compiler

**Steps:**
1. In `apps/frontend`, run `tsc --noEmit`
2. Capture the exit code

**Expected outcome:** Exit code 0; no TypeScript compilation errors
**Pass criteria:** EXIT_CODE=0; all type checks pass

---

### TC-25 — Required-still-passing journeys remain green

**Type:** api
**Preconditions:** Run backend test suite with full depth

**Steps:**
1. Run the full pytest suite: `cd apps/backend && python -m pytest --tb=short -v`
2. Verify that journeys J-06, J-08, J-75, J-81, J-18, J-66, J-60 pass (the critical immutability, single-source, date-control checks)

**Expected outcome:** All required journeys pass; zero regressions introduced
**Pass criteria:** Full suite exits with 0 failures; no red tests for immutability, single-source, or date-control journeys

---

## Summary

**Total test cases:** 25
**Browser tests:** 13 (TC-01 through TC-17)
**API tests:** 10 (TC-04, TC-07, TC-18 through TC-23, TC-25)
**Artifact checks:** 2 (TC-20, TC-24)
