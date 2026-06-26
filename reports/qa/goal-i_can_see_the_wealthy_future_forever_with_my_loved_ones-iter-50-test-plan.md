# Goal Iteration 50 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50  
**Date:** 2026-06-26  
**Frontend Present:** yes

## Phase Goal

Restructure `/research/factor-lab` into an all-factors sortable table showing one row per config-catalog factor with family, Rank-IC (value + N), and downside-risk-adjusted figure at the selected horizon, with click-to-expand rows revealing each factor's D1..D10 decile sort — replacing the single-factor dropdown view with all values byte-identical to the per-factor lab and served from a derived-once cached, bounded read path.

## Test Cases

### TC-01 — All-factors table renders with correct columns

**Type:** browser  
**Preconditions:** Backend is running, frontend is running, Factor Lab page is accessible at `/research/factor-lab`

**Steps:**
1. Navigate to `/research/factor-lab`
2. Wait for the page to load completely (page shows "Factor Lab" title)
3. Observe the table structure

**Expected outcome:** The page displays a table with one row per config-catalog factor. Column headers visible are: family, Rank-IC (value + N), and risk-adjusted figure at the selected horizon.

**Pass criteria:** Table renders with ≥5 factor rows visible, each row contains the expected columns (family, Rank-IC value, Rank-IC N, risk-adjusted figure), no dropdown selector is present, no per-regime effectiveness table is visible.

---

### TC-02 — Column sort reorders table NA-last

**Type:** browser  
**Preconditions:** All-factors table is rendered with ≥2 factors

**Steps:**
1. Take an initial screenshot of the table (capture row order and values)
2. Click the "Rank-IC" column header to sort by rank-IC value
3. Wait 1s for sort to complete
4. Take a second screenshot of the table (capture new row order)
5. Compare the two screenshots byte-by-byte using md5sum

**Expected outcome:** Rows reorder by Rank-IC value ascending/descending. Rows with NA, n=0, or null values appear at the end of the sorted list. The two screenshots are byte-distinct (different row order).

**Pass criteria:** md5sum of screenshot-1 ≠ md5sum of screenshot-2; rows are reordered; NA/n=0 rows are at the bottom; sort is reversible (click again reverses order).

---

### TC-03 — Factor row expands to show decile table

**Type:** browser  
**Preconditions:** All-factors table is rendered with ≥1 factor row

**Steps:**
1. Take a screenshot of the table before expand
2. Click on the first factor row (or its expand icon/chevron)
3. Wait 500ms for animation to complete
4. Take a screenshot showing the expanded decile table
5. Verify the decile table contains columns: decile (D1..D10), mean return, risk-adjusted, N, low-sample flag

**Expected outcome:** The factor row expands in place, revealing a full-width detail panel below the row containing the D1..D10 decile breakdown. The decile table shows all 10 deciles with their values.

**Pass criteria:** Expanded panel is visible and contains a decile table; each decile row shows D1 through D10; the panel is byte-distinct from the collapsed state; the table structure matches the existing `FactorDecileTable` shape.

---

### TC-04 — Factor row collapse hides decile table

**Type:** browser  
**Preconditions:** A factor row is expanded and showing its decile table

**Steps:**
1. Take a screenshot of the expanded row with decile table visible
2. Click on the expanded factor row (or its collapse icon) to collapse it
3. Wait 500ms for animation to complete
4. Take a screenshot of the collapsed table

**Expected outcome:** The decile table panel disappears and the row returns to collapsed state. The table view returns to its original appearance.

**Pass criteria:** Expanded panel is hidden; the row is no longer expanded; screenshot after collapse is byte-identical to the initial unexpanded state from TC-03 step 1.

---

### TC-05 — Decile N= chip opens Research Samples in new tab with count-coherent cohort

**Type:** browser  
**Preconditions:** A factor row is expanded, showing its decile table with N values

**Steps:**
1. Expand a factor row to see its decile table
2. Locate the first decile (D1) row and its "N=X" chip
3. Record the N value shown in the chip (e.g., N=145)
4. Right-click the "N=X" chip and select "Open in new tab" (or middle-click)
5. Switch to the new tab
6. Wait for the Research Samples page to load
7. Verify the page shows a filtered sample set with the exact N value
8. Verify the URL contains cohort parameters matching the decile (e.g., `kind=factor`, `factor=X`, `slice=decile`, `decile=1`)

**Expected outcome:** A new tab opens with the Research Samples page showing the exact cohort for that decile. The sample count equals the published N value. The URL shows `kind=factor`, the selected factor name, `slice=decile`, and `decile=1` (or the clicked decile number).

**Pass criteria:** New tab opens; Research Samples page loads; the total sample count visible on the page equals the N value from the chip; URL contains cohort parameters (`kind=factor`, factor name, `slice=decile`, decile number); the samples listed match the decile definition.

---

### TC-06 — Per-regime effectiveness table is absent from Factor Lab view

**Type:** browser  
**Preconditions:** Factor Lab page is fully loaded

**Steps:**
1. Navigate to `/research/factor-lab`
2. Wait for page to load completely
3. Scroll through the entire page
4. Search for any table section labeled "Regime Effectiveness", "by_regime", or "Per-Regime"

**Expected outcome:** The Factor Lab page does NOT contain a per-regime effectiveness table. Only the all-factors table and the horizon/as-of controls are visible.

**Pass criteria:** No per-regime effectiveness table is visible on the page; the page contains only the all-factors sortable table, horizon selector, and as-of toggle.

---

### TC-07 — Horizon selector controls the displayed risk-adjusted figure

**Type:** browser  
**Preconditions:** All-factors table is rendered; multiple horizons are available (e.g., 5d, 10d, 20d, 60d)

**Steps:**
1. Take a screenshot of the table showing risk-adjusted values at the current horizon
2. Click the Horizon selector (dropdown)
3. Select a different horizon (e.g., from 5d to 20d)
4. Wait for the table to update
5. Take a screenshot showing the updated risk-adjusted values
6. Compare the two screenshots

**Expected outcome:** The risk-adjusted figure column updates with new values when the horizon changes. The new values correspond to the selected horizon. The all-factors table remains visible with the same factors but different risk-adjusted figures.

**Pass criteria:** Horizon selector changes the value in the risk-adjusted column; the two screenshots show different risk-adjusted values; the table structure remains the same; no page reload occurs.

---

### TC-08 — As-of mode toggle reads the single global as-of control

**Type:** browser  
**Preconditions:** All-factors table is rendered; historical as-of dates are available

**Steps:**
1. Take a screenshot of the current table with N values visible
2. Toggle the "As-of date" mode to a historical date (e.g., 30 days ago)
3. Wait for the table to update
4. Take a screenshot showing the updated table with as-of-scoped N values
5. Compare the N values between the two screenshots

**Expected outcome:** Toggling the as-of mode changes the observation set and the N values in the table. The same single global as-of control is used (no second independent date control). The Rank-IC N values decrease as the as-of date is moved to the past.

**Pass criteria:** As-of toggle changes the N values; the two screenshots show different N counts; the as-of mode is a single control (not two independent date fields); the table reloads with filtered observations.

---

### TC-09 — Byte-identity: all-factors aggregate per factor equals compute_factor_lab per factor

**Type:** api  
**Preconditions:** Backend is running; the EventStudyCache is populated (cold compute has completed at least once)

**Steps:**
1. Call `GET /api/research/factor-lab?view=all&horizon=20` to retrieve the all-factors aggregate
2. Record the Rank-IC value, N, risk-adjusted figure, and first decile (D1) mean return for factor "momentum"
3. Call `GET /api/research/factor-lab?factor=momentum&horizon=20` to retrieve the per-factor compute
4. Record the same fields from the per-factor response
5. Compare the two responses field-by-field

**Expected outcome:** The all-factors aggregate's "momentum" factor row matches exactly the per-factor compute for "momentum" across all fields: Rank-IC value, N, risk-adjusted, and all decile rows (D1..D10 mean return, risk-adjusted, N, low-sample flag).

**Pass criteria:** All-factors aggregate[factor="momentum"] == compute_factor_lab(factor="momentum") byte-for-byte (exact dict equality including nested deciles); JSON structure is identical.

---

### TC-10 — Cache correctness: EventStudyCache HIT returns byte-identical to fresh compute

**Type:** api  
**Preconditions:** Backend is running; an all-factors query has been run at least once to populate the cache

**Steps:**
1. Call `GET /api/research/factor-lab?view=all&horizon=20` (cache HIT — the row is already populated)
2. Record the full response payload and its md5sum
3. Call the same endpoint again (cache HIT)
4. Record the response payload and md5sum
5. Manually delete the EventStudyCache row for the all-factors view from the database (simulating a stale cache)
6. Call the endpoint a third time (cache MISS — forces fresh compute)
7. Record the fresh-compute response and md5sum
8. Compare all three md5sums

**Expected outcome:** Cache HIT response is byte-identical to the second cache HIT. Cache MISS response (fresh compute) is also byte-identical to the cached response. All three md5sums are equal.

**Pass criteria:** md5(cache-hit-1) == md5(cache-hit-2) == md5(cache-miss-fresh-compute); no floating-point drift; the payload is deterministic across compute paths (cached vs fresh).

---

### TC-11 — Bounded read: no unbounded select().all() in all-factors builder

**Type:** artifact  
**Preconditions:** Source code is available; the research.py module is accessible

**Steps:**
1. Open `apps/backend/app/engine/research.py`
2. Locate the function that builds the all-factors aggregate (e.g., `factor_lab_all_cached` or similar)
3. Search for any `.all()` call or unbounded query materialization
4. Verify that all ScannerResult/ScannerRun reads use `yield_per(config.research.read_batch_size)` for streaming
5. Verify that any ORDER BY clause on ScannerResult/ScannerRun uses `(run_id, id)` (NOT bare `id`)

**Expected outcome:** No unbounded `select(...).all()` calls exist in the all-factors builder. All reads are streamed via `yield_per`. ScannerResult/ScannerRun reads are ordered by `(run_id, id)` to avoid temp B-tree spill on a full disk.

**Pass criteria:** Grep finds zero matches for `\.all\(\)` in the all-factors builder function; all observation reads use `yield_per`; `ORDER BY` clauses use `(run_id, id)` composite key; no bare `ORDER BY id` is present.

---

### TC-12 — Factor catalog and horizons are config-sourced (no magic numbers)

**Type:** artifact  
**Preconditions:** Source code is available; config files are accessible

**Steps:**
1. Grep `apps/backend/app/engine/` CALC_FILES for any numeric literal for factor count, horizon count, or horizon values
2. Verify that the factor catalog is read from `config.research.factors` (or similar)
3. Verify that horizons are read from `config.walk_forward.horizons`
4. Verify that decile count (10) is sourced from config, not hardcoded
5. Verify that `read_batch_size` is sourced from `config.research.read_batch_size`

**Expected outcome:** No magic numbers for factor/horizon/decile definitions in the CALC_FILES. All values are config-sourced.

**Pass criteria:** `test_no_magic_numbers` test passes; no numeric literals for factors, horizons, decile count, or batch size are found in calculation code; grep `CALC_FILES` for `\b[0-9]+\b` in horizon/factor/decile contexts returns zero matches.

---

### TC-13 — test_db.py expected-tables guard UNCHANGED (no new table)

**Type:** artifact  
**Preconditions:** Test suite is available; `test_db.py` is accessible

**Steps:**
1. Open `apps/backend/tests/test_db.py`
2. Locate the `test_create_all_produces_expected_tables` test
3. Review the expected tables list
4. Verify that no new `table=True` ORM model is added for the all-factors aggregate
5. Confirm that `EventStudyCache` is still the only cache model

**Expected outcome:** The `test_create_all_produces_expected_tables` list is UNCHANGED from the previous iteration. No new table row is added. The all-factors aggregate reuses `EventStudyCache` with a new `subject`/`view` namespace.

**Pass criteria:** The expected-tables list has not grown by 1; `EventStudyCache` is still listed but no new cache or aggregation table appears; the test passes with the same table count as before.

---

### TC-14 — Unknown factor / unknown horizon returns 422

**Type:** api  
**Preconditions:** Backend is running

**Steps:**
1. Call `GET /api/research/factor-lab?factor=nonexistent_factor&horizon=20`
2. Record the HTTP status code and response body

**Expected outcome:** The API returns a 422 (Unprocessable Entity) status code with an error message indicating that the factor or horizon is unknown.

**Pass criteria:** HTTP status == 422; response contains an error message mentioning "unknown factor" or "invalid factor"; no 500 error.

---

### TC-15 — No price data available returns 503

**Type:** api  
**Preconditions:** Backend is running; a scenario with no price data is possible (or mock it)

**Steps:**
1. Call `GET /api/research/factor-lab?view=all&horizon=20` when the database has no forward return or price data
2. Record the HTTP status code and response body

**Expected outcome:** The API returns a 503 (Service Unavailable) status code indicating that no price data is available.

**Pass criteria:** HTTP status == 503; response indicates unavailable data or data error; no fabricated row is returned.

---

### TC-16 — As-of before history / future / unparseable returns 400/422

**Type:** api  
**Preconditions:** Backend is running

**Steps:**
1. Call `GET /api/research/factor-lab?view=all&as_of=1900-01-01` (before history)
2. Record the status code
3. Call `GET /api/research/factor-lab?view=all&as_of=2099-12-31` (future date)
4. Record the status code
5. Call `GET /api/research/factor-lab?view=all&as_of=invalid-date` (unparseable)
6. Record the status code

**Expected outcome:** All three calls return either 400 (Bad Request) or 422 (Unprocessable Entity), never a 200 with fabricated data.

**Pass criteria:** Status code is 400 or 422 for all three calls; no 200 response with fake data; error message is clear.

---

### TC-17 — Zero-N / low-sample factor renders NA + n

**Type:** browser  
**Preconditions:** All-factors table is rendered; at least one factor has zero observations or low sample size

**Steps:**
1. Observe the all-factors table
2. Locate a factor row where N is zero or below the low-sample threshold
3. Verify that the Rank-IC value and risk-adjusted figure columns show "NA" or a placeholder

**Expected outcome:** Factors with zero observations or low sample counts display "NA" in the Rank-IC value and risk-adjusted columns, with the N value shown alongside (e.g., "NA (n=5)").

**Pass criteria:** Low-sample/zero-N factors show "NA" in value columns and display the N count; no fabricated numeric value is shown; the row is sortable and placed at the end (NA-last).

---

### TC-18 — Empty observation set renders honest empty state

**Type:** browser  
**Preconditions:** All-factors table is loaded; a scenario with zero observations exists (or mock it by filtering as-of to before all data)

**Steps:**
1. Set the as-of date to a date before any observations exist in the database
2. Wait for the table to load
3. Observe the page content

**Expected outcome:** The page displays an honest empty state (e.g., "No factors available for this period") instead of an empty table or fabricated rows.

**Pass criteria:** The page shows a clear empty state message; no blank table is rendered; no fabricated factor rows appear; the page is not broken or showing an error.

---

### TC-19 — Smoke test: single-factor decile values match all-factors row (byte-identical)

**Type:** browser  
**Preconditions:** All-factors table is rendered; single-factor Factor Lab view is accessible

**Steps:**
1. On the all-factors table, expand a factor row (e.g., "momentum") and note its D1 mean return, D5 mean return, D10 mean return
2. Navigate to the single-factor Factor Lab view (or call the single-factor endpoint)
3. Select the same factor ("momentum") and same horizon
4. Compare the decile values in the single-factor view to the all-factors deciles

**Expected outcome:** The decile mean returns, risk-adjusted figures, and N values in the single-factor view match exactly the values shown in the expanded all-factors row.

**Pass criteria:** D1, D5, D10 mean returns are byte-identical between all-factors expansion and single-factor view; decile N counts match; risk-adjusted figures match (to floating-point precision).

---

### TC-20 — Smoke test: J-25 (single-factor lab) still loads and is unchanged

**Type:** browser  
**Preconditions:** The single-factor Factor Lab interface is still available

**Steps:**
1. Navigate to the Factor Lab page (if a dropdown selector is still present, use it; if not, call the per-factor endpoint)
2. Select a factor (e.g., "momentum") and horizon
3. Verify that the single-factor view loads without errors
4. Compare the displayed decile table to a previous baseline screenshot

**Expected outcome:** The single-factor Factor Lab view still works. The decile table displays correctly. The interface is unchanged from the previous iteration.

**Pass criteria:** Single-factor view loads without error; decile table is visible and correct; no regression in the single-factor feature.

---

## Summary

**Total test cases:** 20  
**Browser tests:** 9 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-17, TC-18, TC-19, TC-20)  
**API tests:** 6 (TC-09, TC-10, TC-14, TC-15, TC-16)  
**Artifact checks:** 4 (TC-11, TC-12, TC-13, TC-20 smoke)  

**Key focus areas:**
- Byte-identity across all-factors aggregate vs per-factor compute (TC-09, TC-19)
- Sorting with NA-last reordering (TC-02)
- Expandable row pattern with decile drill-down (TC-03, TC-04)
- Count-coherent sample linking (TC-05)
- Cache correctness and bounded reads (TC-10, TC-11)
- No magic numbers, config-sourced definitions (TC-12)
- Honest error handling and empty states (TC-14 through TC-18)
- Regression smoke tests on required-still-passing journeys (TC-20)
