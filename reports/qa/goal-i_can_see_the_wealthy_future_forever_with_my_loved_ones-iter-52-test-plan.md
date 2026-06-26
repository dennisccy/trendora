# Goal Iteration 52 — Factor Lab All-Horizon Paired Columns Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52
**Date:** 2026-06-26
**Frontend Present:** yes

## Phase Goal

The Factor Lab drops its single-horizon selector and shows every configured horizon (1/5/10/20/60d) at once as paired forward-return + max-drawdown columns on both the all-factors table and each factor's expandable decile sort, with no number recomputed.

## Test Cases

### TC-01 — All-Factors Table Renders All Horizons with Paired Columns

**Type:** browser
**Preconditions:**
- Backend is running and warmed (single-fetch-at-a-time)
- `/research/factor-lab` is reachable via Chrome MCP
- No pending backend unavailable/skeleton frame persists

**Steps:**
1. Navigate to `/research/factor-lab` via Chrome MCP
2. Wait for the all-factors table to fully load
3. Capture evidence (md5sum directory first per iter-40 lesson)
4. Inspect table column headers
5. Count forward-return columns (should be 5: 1d, 5d, 10d, 20d, 60d)
6. Count max-drawdown columns (should be 5: one paired per horizon)
7. Verify all 11 catalog factors are visible (not truncated or in "Loading…" state)

**Expected outcome:**
- All-factors table renders with exactly 11 factors (MeanRev, Seasonality, etc.)
- Five forward-return columns are present (labeled per horizon: 1d, 5d, 10d, 20d, 60d)
- Five paired max-drawdown columns are present (one adjacent to each forward-return)
- No "Loading…" / "Backend unavailable" / skeleton frames are visible
- Table is not in an error state

**Pass criteria:**
- Visible column count = 5 forward-return + 5 max-drawdown = 10 paired columns
- All 11 factors rendered in all-factors table (no truncation, no empty rows)
- Evidence directory contains non-skeleton screenshots (md5sum confirms byte-distinct from loading state)

---

### TC-02 — All-Factors Table Shows Top-Decile (D10) Cohort Values

**Type:** api
**Preconditions:**
- Backend is running and reachable at `http://localhost:8000`
- `/api/research/factor-lab?all=true` endpoint responds

**Steps:**
1. Issue the following curl command:
   ```bash
   curl -s "http://localhost:8000/api/research/factor-lab?all=true" | jq '.factors[0]'
   ```
2. Inspect response structure for first factor
3. Verify presence of per-horizon forward-return and max-drawdown fields
4. For one horizon (e.g., 20d), extract the forward-return value and max-drawdown value
5. Verify values are either a number or explicit `null` (no missing fields, no fabricated defaults)

**Expected outcome:**
- HTTP 200 response
- Response contains `factors` array with 11 entries
- First factor contains `horizons` or flat structure with paired `forward_return_<horizon>` and `max_drawdown_<horizon>` fields
- All horizons (1, 5, 10, 20, 60) present in response
- D10 cohort values match pre-computed `compute_factor_lab` output for the same horizon (byte-identical assertion in unit tests)

**Pass criteria:**
- Status code = 200
- Response shape includes all five horizons with paired (forward_return, max_drawdown) per horizon
- No missing fields; null values explicit (never omitted or replaced with defaults)
- All 11 factors present in response array

---

### TC-03 — Extended Cache Key Produces MISS on Old-Schema Cache Row

**Type:** artifact
**Preconditions:**
- Database is running and populated with factor-lab data
- An old-schema cached row exists in `event_study_cache` table (pre-iter-52 without paired MDD columns)
- Backend code has folded a schema token into the `factor_lab_all_cached` cache key

**Steps:**
1. Read the `event_study_cache` table and locate an old-schema row (identified by cache key without schema token)
2. Trigger a factor-lab `all=true` fetch on the same as-of date and factor
3. Inspect the cache table for a new row with the extended key (schema token appended)
4. Verify the old row is NOT modified (immutability check)
5. Verify the new row contains the full all-horizons + paired-MDD shape

**Expected outcome:**
- Old-schema cache row remains unchanged (no in-place schema upgrade)
- A new cache row with extended key is inserted (MISS → recompute once)
- New row contains all five horizons with paired (forward_return, max_drawdown) per horizon
- Subsequent same-date fetch hits the new row (cache HIT, not re-computed)

**Pass criteria:**
- Old-schema cache row unchanged (immutable snapshot guarantee)
- New-schema cache key is distinct from old-schema key (folded token visible)
- New row count = 1 (not duplicated); old row count unchanged
- New row's payload includes all horizon pairs (no truncation)

---

### TC-04 — Byte-Identical Forward-Return and Max-Drawdown vs Single-Horizon Reference

**Type:** artifact
**Preconditions:**
- Unit test file `apps/backend/tests/test_factor_lab_all.py` exists
- Test contains deep-equality assertion comparing all-horizons output to single-horizon `compute_factor_lab(factor, horizon, …)` calls
- Tests cover as-of, all-history, and zero-N edge cases

**Steps:**
1. Read `test_factor_lab_all.py` test cases
2. Verify test loops over all five horizons (1, 5, 10, 20, 60)
3. Verify test loops over all 11 catalog factors
4. Verify test loops over all three as-of/all-history/zero-N scenarios
5. Inspect assertion logic (deep-equality, not approximate)

**Expected outcome:**
- Test cases cover all (5 horizons × 11 factors × 3 scenarios) combinations
- Each combination compares `all_horizons_output[factor][horizon]` to `single_horizon_output[factor][horizon]`
- Assertion is deep-equality (byte-identical, not tolerance-based)
- Test passes (no assertion failures)

**Pass criteria:**
- Test file exists at correct path
- Test cases assert byte-identity for all horizon/factor/scenario combinations
- Test runs without failures
- Assertion logic is deep-equality (e.g., `==` or `.assert_equal()`, not `.assert_almost_equal()`)

---

### TC-05 — Bounded Streamed Read Path Serves Full Live Forward-Returns Without MemoryError

**Type:** artifact
**Preconditions:**
- Backend is running on a quiet (single-fetch-at-a-time) machine
- `forward_returns` table contains ~3M rows (full live dataset)
- Backend code uses `yield_per()` and column projection (no unbounded `select(...).all()`)
- Backend code orders `ScannerResult` reads by `(run_id, id)` (idx_scanner_results_run_id)

**Steps:**
1. Read `apps/backend/app/engine/research.py` and inspect `_all_factor_observations` and `_factor_observations` builders
2. Verify they use `yield_per()` or streaming pattern (not `all()`)
3. Verify they project only required columns (`realized_return`, `max_drawdown`)
4. Verify no temporary materialization of `ScannerResult` (all rows in memory)
5. Verify `ScannerResult` order clause is `(run_id, id)` (indexed path)
6. Run integration test `test_research_streaming.py` on cold cache to trigger full dataset read
7. Verify no MemoryError, no OOM exception

**Expected outcome:**
- Code review shows proper streaming patterns (no `all()` on large tables)
- Code review shows proper column projection (narrow SELECT, not `SELECT *`)
- `ScannerResult` ordered by indexed columns (`(run_id, id)`)
- Integration test completes without MemoryError
- Integration test can serve all ~3M forward_returns rows in time budget

**Pass criteria:**
- `_all_factor_observations` and `_factor_observations` use `yield_per()` or equivalent streaming
- Only `realized_return` and `max_drawdown` are selected (not full row)
- `ScannerResult` order is `(run_id, id)` (indexed, no temp sort)
- Test `test_research_streaming.py` exits with status 0 (no MemoryError)

---

### TC-06 — Horizon Selector Removed from Frontend

**Type:** browser
**Preconditions:**
- Frontend is running at `http://localhost:3000`
- `/research/factor-lab` page is loaded

**Steps:**
1. Navigate to `/research/factor-lab`
2. Inspect the DOM for any `<select>` element related to horizon selection
3. Look for `HorizonSelector` component or any element with `aria-label` containing "horizon" or "days"
4. Verify absence of horizon selector UI control

**Expected outcome:**
- No `<select>` element for horizon selection
- No "Select horizon" or similar label
- No radio/button group for horizon switching
- Page layout indicates all horizons are displayed by default (no picker needed)

**Pass criteria:**
- Horizon selector `<select>` or equivalent is NOT present in DOM
- No horizon-picker `aria-label` found via Chrome MCP accessibility tree
- Page loads without "Error: horizon not selected" or similar validation error

---

### TC-07 — Expand Factor Row to Show D1–D10 Decile Sort with All-Horizon Paired Columns

**Type:** browser
**Preconditions:**
- Factor Lab all-factors table is rendered and visible
- At least one factor row is accessible

**Steps:**
1. Click the expand chevron on the first factor row (MeanRev)
2. Wait for decile sort to render below the factor row
3. Inspect decile table for column headers
4. Count forward-return columns (should be 5)
5. Count max-drawdown columns (should be 5)
6. Verify all 10 deciles are present (D1 through D10)
7. Verify per-decile `N=` chips are rendered (one per decile, showing sample count)

**Expected outcome:**
- Decile sort expands in-place below factor row
- Decile table contains all 10 rows (D1, D2, ..., D10)
- Five forward-return columns are present (1d, 5d, 10d, 20d, 60d)
- Five paired max-drawdown columns are present
- Per-decile sample count chips (`N=` displayed, clickable)

**Pass criteria:**
- Expand chevron changes state (rotated or color changed)
- Decile table renders with 10 rows (D1–D10)
- Column count = 5 forward-return + 5 max-drawdown = 10 paired columns
- All `N=` chips are rendered and visible

---

### TC-08 — Per-Decile N= Chip Opens Samples Cohort Without 4xx

**Type:** browser
**Preconditions:**
- Factor Lab decile sort is expanded for one factor
- A decile `N=` chip is visible and clickable
- Backend is ready to serve the samples endpoint

**Steps:**
1. Click the `N=` chip for decile D5 (middle decile) on the first factor
2. Verify a new browser tab opens
3. Inspect the new tab's URL for query parameters: `?factor=...&horizon=...&decile=...&asof=...`
4. Wait for `/research/samples` page to load
5. Inspect the sample table for rows matching the cohort
6. Count total displayed observations (should match the `N=` chip value)

**Expected outcome:**
- New tab opens to `/research/samples` with exact `(factor, horizon, decile)` query parameters
- No 4xx or 5xx error
- Sample table displays the correct observations for that cohort
- Total observation count equals the `N=` chip value
- Survivorship-bias label is visible

**Pass criteria:**
- URL includes all four query parameters (factor, horizon, decile, asof)
- HTTP status 200 (no 4xx)
- Displayed observation count matches `N=` value
- Sample table is non-empty (at least 1 row)
- Survivorship-bias disclaimer is rendered

---

### TC-09 — Sort Per-Horizon Forward-Return Column (NA Sinks Last)

**Type:** browser
**Preconditions:**
- All-factors table is rendered with all horizons visible
- At least two factors have non-null forward-return values for a given horizon
- Evidence directory has been md5sum'd (iter-40 lesson)

**Steps:**
1. Screenshot the initial all-factors table (descending sort, default state)
2. Click the column header for the 20d forward-return column
3. Wait for table to re-render (view-only reorder, no refetch)
4. Screenshot the sorted table
5. Inspect both screenshots for byte-distinctness (md5sum)
6. Verify factors with null (NA) forward-return values appear at the bottom of the sorted column
7. Verify non-null values are sorted descending (highest return first)

**Expected outcome:**
- First click sorts descending by 20d forward-return (default sort direction)
- Factors with NA/null values appear at the bottom
- Non-null values are ordered numerically (highest first)
- Before/after screenshots are byte-distinct (md5sum differs)
- No refetch or "Loading…" appears during sort

**Pass criteria:**
- Before/after screenshots have different md5sum (byte-distinct)
- Table rows are reordered (not identical before/after)
- NA values are at the bottom (last in sort order)
- No network request is made during sort (view-transform only)

---

### TC-10 — Toggle As-of vs All-History Updates N Values Globally via Top-Bar Date

**Type:** browser
**Preconditions:**
- Factor Lab page is loaded
- As-of date selector is visible at the top of the page
- As-of is currently set to latest date (default)

**Steps:**
1. Capture current N values from one factor row (e.g., D10 decile all horizons)
2. Click the as-of date selector (top-bar date control)
3. Select a historical date (e.g., 50 trading days ago)
4. Wait for Factor Lab to reload with historical data
5. Inspect the same factor row and compare N values
6. Verify N values have changed (historical snapshot has different cohort sizes)
7. Click the as-of date selector again
8. Select "Latest" or today's date
9. Verify N values return to their original state

**Expected outcome:**
- As-of date selector is a single global control (no per-page duplicate selector)
- Switching as-of date triggers a data refresh (not a page reload)
- N values update globally across all factors and horizons
- Historical date shows historically-correct N values
- Switching back to latest restores original N values

**Pass criteria:**
- Only one date control visible in the top bar (J-18: exactly one date selector)
- N values are different between as-of and all-history views (not identical)
- No native `input[type=date]` control in Factor Lab component (date control is at global app level)
- Data reloads without page refresh (XHR request is made, not hard reload)

---

### TC-11 — Rank-IC and Risk-Adjusted Figures Relabelled with Default Horizon

**Type:** browser
**Preconditions:**
- Factor Lab all-factors table is rendered
- Rank-IC and risk-adjusted columns are visible (typically right side of table)

**Steps:**
1. Inspect the table for Rank-IC column header or label
2. Verify the header includes the fixed default horizon (e.g., "Rank-IC @ 20d" or "Risk-Adj (20d)")
3. Capture a screenshot showing the Rank-IC label
4. Verify the horizon is NOT a user selector (it's static/read-only text)
5. Verify all factors show Rank-IC at the SAME fixed horizon (not per-factor variants)

**Expected outcome:**
- Rank-IC column header is labelled with default horizon (= 20d, per config)
- Risk-adjusted column header is labelled with default horizon
- Horizon is displayed as text/label (not a selector)
- All factors use the same fixed horizon for these computed figures

**Pass criteria:**
- Rank-IC label includes explicit horizon text (e.g., "@ 20d" or "(20d)")
- Risk-adjusted label includes explicit horizon text
- Horizon is static (no selector, no per-row variant)
- Label is readable in screenshot evidence

---

### TC-12 — Error Case — Horizon with Insufficient Post-D Bars Shows NA + NA

**Type:** artifact
**Preconditions:**
- Backend is running with historical test data
- An as-of date exists where one horizon (e.g., 60d) lacks sufficient post-date bars
- Unit test covers this edge case

**Steps:**
1. Read `test_factor_lab_all.py` for edge-case test covering insufficient-bars scenario
2. Inspect test logic: verify it sets as-of to near end-of-history where N+60d extends beyond data
3. Run the test
4. Inspect output: verify forward-return value is `null` (not a fabricated default)
5. Inspect output: verify max-drawdown value is `null` (not a fabricated default)

**Expected outcome:**
- Unit test exists covering insufficient-bars edge case
- Test sets as-of near end of dataset
- For the out-of-bounds horizon, both forward_return and max_drawdown are `null`
- Never a synthesized or fabricated value (honest NA, per anti-goal "No fabricated data")

**Pass criteria:**
- Edge-case test passes (no assertion failure)
- Null values are returned (not omitted, not replaced with 0 or -1)
- Test explicitly covers the anti-goal requirement (no fabrication)

---

### TC-13 — Error Case — Low-Sample Decile Shows NA + n

**Type:** artifact
**Preconditions:**
- As-of is set to a date with sparse historical data
- A factor-horizon-decile combination has fewer than the minimum sample threshold
- Unit test covers this edge case

**Steps:**
1. Read `test_factor_lab_all.py` or backend test logic for low-sample edge case
2. Identify a decile with low sample count (< min threshold in config)
3. Verify the returned value for that decile is `null` (NA)
4. Verify the `N=` chip still displays the exact sample count (not omitted)

**Expected outcome:**
- Low-sample decile returns `null` for forward-return and max-drawdown
- Sample count chip (`N=`) displays the actual count (e.g., "N=3")
- Data is not fabricated or extrapolated
- Table cell shows "NA" or similar label with the sample count chip

**Pass criteria:**
- Forward-return value is `null` (not estimated or zero-filled)
- Max-drawdown value is `null`
- `N=` chip displays the true count (1, 2, 3, etc.)
- Test passes (no assertion failure)

---

### TC-14 — Samples Cohort Count-Coherence (J-51/J-65): Total == Published n

**Type:** api
**Preconditions:**
- Backend samples endpoint is running
- A factor-horizon-decile cohort is queried with all-history as-of
- The cohort's total observation count is known from the broker/API

**Steps:**
1. Query `/api/research/samples?factor=MeanRev&horizon=20&decile=10`
2. Inspect response: count total observations in array
3. Inspect the `total` or summary field in the response
4. Compare published N (from Factor Lab table `N=` chip) to actual array length
5. Verify equality

**Expected outcome:**
- HTTP 200 response
- Observation array length equals the published `N=` value
- Response includes a `total` or count field confirming the same number
- No missing or duplicate observations

**Pass criteria:**
- Observation array length == published N value
- Response includes explicit count confirmation field
- No discrepancy between array size and published total

---

### TC-15 — No New Table Created — expected_tables Guard Unchanged

**Type:** artifact
**Preconditions:**
- Test file `test_db.py::test_create_all_produces_expected_tables` exists
- Test defines the expected set of `table=True` models in the SQLAlchemy ORM

**Steps:**
1. Read `test_db.py` and locate `test_create_all_produces_expected_tables`
2. Inspect the test for the expected set of tables (should include `forward_returns`, `event_study_cache`, etc.)
3. Count expected tables
4. Run the test on a fresh database schema
5. Verify the test passes (no `AssertionError: unexpected table X`)

**Expected outcome:**
- Test passes without assertion error
- Expected table count remains the same as before iter-52
- No new `table=True` model was added
- `event_study_cache` table is REUSED (not a new table)

**Pass criteria:**
- Test `test_create_all_produces_expected_tables` passes
- No new tables in expected set
- Test output shows table count is unchanged

---

### TC-16 — No Magic Numbers — Horizons and Default Horizon from Config

**Type:** artifact
**Preconditions:**
- Unit test `test_no_magic_numbers` or equivalent exists
- Test scans backend code for hardcoded numeric literals in the research path

**Steps:**
1. Read `test_no_magic_numbers` (or similar test in `test_research.py`)
2. Inspect test logic: verify it checks for hardcoded `[1, 5, 10, 20, 60]` horizon list
3. Verify test checks for hardcoded default_horizon (should be 20, read from config only)
4. Run the test on the code
5. Verify test passes (no hardcoded literal found)

**Expected outcome:**
- Test checks that horizons are loaded from `config.walk_forward.horizons` (not hardcoded)
- Test checks that default_horizon is loaded from `config.walk_forward.default_horizon` (not hardcoded)
- Test passes (no magic numbers detected in research code path)

**Pass criteria:**
- Test passes without assertion error
- Test explicitly verifies horizons come from config
- Test explicitly verifies default_horizon comes from config
- No hardcoded `[1, 5, 10, 20, 60]` or `20` literal appears in research builders

---

### TC-17 — Required-Still-Passing Journeys Remain Green (J-25, J-26, J-29, J-107, J-104, J-105, J-86, J-51, J-65)

**Type:** browser
**Preconditions:**
- Backend is running and warmed
- Frontend is running
- Existing journey test fixtures or manual test steps exist for each journey

**Steps:**
1. For each required journey (J-25, J-26, J-29, J-107, J-104, J-105, J-86, J-51, J-65):
   a. Execute the journey's test steps (either deterministic replay or live navigation)
   b. Verify the expected outcome is met (no regression)
   c. Capture screenshot evidence if manual
2. Record pass/fail for each journey

**Expected outcome:**
- J-25 (?) — still passes
- J-26 (?) — still passes
- J-29 (?) — still passes
- J-107 (?) — All-factors table still renders correctly (existing view)
- J-104 (?) — still passes
- J-105 (?) — Bounded/streamed read path still works (J-105 guarded this iter)
- J-86 (?) — Max-drawdown column is used (J-86 introduced it)
- J-51 (?) — Sample count coherence still holds
- J-65 (?) — Sample count still displays correctly

**Pass criteria:**
- All 9 required-still-passing journeys pass their regression tests
- No new failures introduced in existing functionality
- Evidence captured for each journey (screenshot or test output)

---

### TC-18 — Critical Journeys: J-06 (Single Source), J-18 (One Date Selector), J-07 (Risk-Off)

**Type:** browser
**Preconditions:**
- Backend is running with config and seed data
- Frontend is running

**Steps:**
1. **J-06 (Single source):** Verify that Factor Lab D10 forward-return/max-drawdown values read identically across multiple pages (e.g., Factor Lab table vs Backtest workspace or detail page, if applicable). Capture the same factor value from two different surfaces and compare.
2. **J-18 (Exactly one date selector):** Verify there is only one as-of date control visible in the top bar (not multiple per-page selectors). Verify Factor Lab has no local date picker.
3. **J-07 (Risk-Off → 0):** In a Risk-Off regime snapshot, verify that Factor Lab shows the expected zero Actionable status (if this applies to Factor Lab; if not, verify regime label is correct).

**Expected outcome:**
- J-06: Factor Lab forward-return/max-drawdown values are identical when read from different surfaces
- J-18: Only one global date selector exists; Factor Lab does not introduce a second per-page selector
- J-07: Risk-Off regime is reflected correctly (regime label, zero Actionable count, or equivalent)

**Pass criteria:**
- J-06: Values match across surfaces (screenshot comparison or value inspection)
- J-18: No second date control in Factor Lab component; only global as-of selector
- J-07: Risk-Off regime is rendered correctly in Factor Lab view

---

## Summary

| Type | Count | Notes |
|------|-------|-------|
| **Browser tests** | 10 | TC-01, TC-07, TC-09, TC-10, TC-11, TC-17, TC-18 (partial) + UI evolution checks |
| **API tests** | 2 | TC-02, TC-14 |
| **Artifact/Unit tests** | 6 | TC-03, TC-04, TC-05, TC-12, TC-13, TC-15, TC-16 |

**Total test cases: 18**

### Test Breakdown

- **Frontend-facing (browser):** 10 test cases (UI rendering, interactions, regression checks)
- **API/backend:** 2 test cases (JSON response shape, sample count coherence)
- **Unit/integration tests & code artifacts:** 6 test cases (cache schema, byte-identity, streaming, error handling, config sourcing)

### Key Coverage

- **All-horizon paired-column rendering:** TC-01, TC-02, TC-07, TC-11
- **Cache schema and byte-identity:** TC-03, TC-04
- **Bounded streaming and OOM prevention:** TC-05
- **Horizon selector removal:** TC-06
- **User interactions (expand, sort, drill-down):** TC-07, TC-08, TC-09, TC-10
- **Error cases (NA, low-sample, out-of-bounds):** TC-12, TC-13
- **Data integrity (count-coherence, no fabrication):** TC-14, TC-15
- **No hardcoded literals:** TC-16
- **Regression on existing journeys:** TC-17, TC-18

### Quality Rules Applied

- Tests are specific and reproducible
- Tests reflect user perspective (navigation, interaction, visual changes)
- Edge cases covered (insufficient bars, low-sample deciles, NA honesty)
- Every test maps to a specific spec requirement or anti-goal
