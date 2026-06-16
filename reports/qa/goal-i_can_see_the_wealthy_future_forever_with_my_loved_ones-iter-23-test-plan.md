# Goal Iteration 23 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23
**Date:** 2026-06-16
**Frontend Present:** yes

## Phase Goal

Surface the five stored forward-return columns (1/5/10/20/60-day) on the Themes and Sectors leaderboards reading the same values Backtest reads (J-81), and fix the four read-only view/serve defects on the Research Regime × Setup × Pattern table: NA-last sorting, Regime/Setup/Pattern filter dropdowns, N= drill-down that works for every emitted combination, and Pooled default (J-82).

## Test Cases

### TC-01 — Themes leaderboard forward-return columns appear at historical as-of date

**Type:** browser
**Preconditions:** Frontend running at http://localhost:3000; backend running; a historical snapshot with post-D bars exists (e.g., 2024-01-15).

**Steps:**
1. Navigate to `/themes`
2. Open the global as-of date picker and select a historical date (e.g., 2024-01-15)
3. Observe the themes table
4. Inspect each row for forward-return columns (1d, 5d, 10d, 20d, 60d)

**Expected outcome:** Each theme row displays five forward-return columns with numeric values (positive/negative/zero) or NA cells, colour-graded by sign (positive green, negative red).
**Pass criteria:** All five column headers visible; each row has cells in all five columns; cells are either numeric or explicitly NA (not blank, not "0%").

---

### TC-02 — Themes forward-return columns are sortable (J-48 view-transform)

**Type:** browser
**Preconditions:** FC-01 passed; themes displayed at historical as-of; at least two theme rows have numeric values in the 5d column.

**Steps:**
1. Click the "5d" column header to sort ascending
2. Observe the row order change
3. Click the "5d" column header again to sort descending
4. Observe the row order change again
5. Scroll to verify the page did not refresh (no loading spinner)

**Expected outcome:** Rows reorder by 5d forward return (ascending/descending); page renders the same data with no network request.
**Pass criteria:** Rows are reordered; page state is local (no reload); default theme rank is restored if you navigate away and back.

---

### TC-03 — Sectors leaderboard forward-return columns appear at historical as-of date

**Type:** browser
**Preconditions:** Frontend running; backend running; a historical snapshot with post-D bars exists.

**Steps:**
1. Navigate to `/sectors`
2. Open the global as-of date picker and select a historical date (e.g., 2024-01-15)
3. Observe the sectors/ETF table
4. Inspect each row for forward-return columns (1d, 5d, 10d, 20d, 60d)

**Expected outcome:** Each sector/ETF row displays five forward-return columns with numeric values or NA cells, colour-graded by sign.
**Pass criteria:** All five column headers visible; each row has cells in all five columns; cells are either numeric or explicitly NA.

---

### TC-04 — Sectors forward-return columns are sortable (J-48 view-transform)

**Type:** browser
**Preconditions:** TC-03 passed; sectors displayed at historical as-of; at least two sector rows have numeric values in the 10d column.

**Steps:**
1. Click the "10d" column header to sort ascending
2. Observe the row order change
3. Click the "10d" column header again to sort descending
4. Verify no page reload (no network request)

**Expected outcome:** Rows reorder by 10d forward return; page remains interactive without refresh.
**Pass criteria:** Rows reordered; no network reload; default sector rank restored on page refresh.

---

### TC-05 — Theme forward-return value matches Backtest Top Themes at same date + horizon

**Type:** browser
**Preconditions:** TC-01 passed; a theme with a non-NA forward return value exists (e.g., Theme "Tech" 5d = 3.2%).

**Steps:**
1. On `/themes`, note the theme name and its 5d forward-return value (e.g., "Tech" = 3.2%)
2. Navigate to `/backtest`
3. Set the as-of date to match the `/themes` as-of date
4. Open the "Top Themes" section
5. Find the same theme in the Top Themes table
6. Compare its 5d forward-return value

**Expected outcome:** The 5d value on `/themes` is identical to the value shown in Backtest Top Themes at the same date (J-06 single-source proof).
**Pass criteria:** `themes[i].forward_returns[5d] === backtest.top_themes[j].forward_returns[5d]` where theme names match.

---

### TC-06 — Sector forward-return value matches Backtest Top Sectors at same date + horizon

**Type:** browser
**Preconditions:** TC-03 passed; a sector with a non-NA forward return value exists (e.g., Sector "Financials" 20d = -1.5%).

**Steps:**
1. On `/sectors`, note the sector name and its 20d forward-return value (e.g., "Financials" = -1.5%)
2. Navigate to `/backtest`
3. Set the as-of date to match the `/sectors` as-of date
4. Open the "Top Sectors" section
5. Find the same sector in the Top Sectors table
6. Compare its 20d forward-return value

**Expected outcome:** The 20d value on `/sectors` matches the Backtest Top Sectors value at the same date.
**Pass criteria:** `sectors[i].forward_returns[20d] === backtest.top_sectors[j].forward_returns[20d]` where sector names match.

---

### TC-07 — Forward-return columns honestly show NA at latest as-of date

**Type:** browser
**Preconditions:** Frontend running; backend running; latest snapshot date is known.

**Steps:**
1. Navigate to `/themes`
2. Ensure the global as-of picker is set to "Latest" (or click the date and select today)
3. Observe the forward-return columns in the themes table
4. Scroll through and count rows with NA cells in the 60d column

**Expected outcome:** Most or all 60d cells display NA (not "0%", not blank) because the latest snapshot has insufficient post-D bars to compute 60-day returns.
**Pass criteria:** At least one row has NA in the 60d column; no row shows a fabricated "0%" in place of NA; text "NA" or equivalent marker is visible.

---

### TC-08 — API /api/themes returns forward_returns field with correct shape

**Type:** api
**Preconditions:** Backend running; a recent snapshot exists.

**Steps:**
1. Run: `curl -s http://localhost:8835/api/themes | jq '.themes[0].forward_returns'`
2. Inspect the response structure

**Expected outcome:** Response contains a field `forward_returns` with keys for each horizon (1, 5, 10, 20, 60 — derived from `config.walk_forward.horizons`); values are either numeric or null.
**Pass criteria:** `forward_returns` object exists; has keys "1", "5", "10", "20", "60"; each value is a number or null; no hardcoded horizon list appears in the code (horizons come from config).

---

### TC-09 — API /api/sectors returns forward_returns field with correct shape

**Type:** api
**Preconditions:** Backend running; a recent snapshot exists.

**Steps:**
1. Run: `curl -s http://localhost:8835/api/sectors | jq '.sectors[0].forward_returns'`
2. Inspect the response structure

**Expected outcome:** Response contains a field `forward_returns` with keys for each horizon (1, 5, 10, 20, 60); values are numeric or null.
**Pass criteria:** `forward_returns` object exists; has keys "1", "5", "10", "20", "60"; each value is a number or null.

---

### TC-10 — Research RSP table NA rows sort to bottom on ascending sort

**Type:** browser
**Preconditions:** Frontend running; backend running; `/research` loaded with RSP study visible; at least one row with NA in a numeric column exists.

**Steps:**
1. Navigate to `/research`
2. Scroll to the Regime × Setup × Pattern study section
3. Click a numeric column header (e.g., "Return 1d") to sort ascending
4. Observe the row order

**Expected outcome:** All rows with NA in the sorted column appear at the bottom; rows with numeric values sort numerically at the top.
**Pass criteria:** First N rows have numeric values sorted smallest-to-largest; rows N+1 onward are all NA; stable tie-break preserves served rank among numeric rows and among NA rows.

---

### TC-11 — Research RSP table NA rows sort to bottom on descending sort

**Type:** browser
**Preconditions:** TC-10 passed.

**Steps:**
1. Click the same numeric column header again to sort descending
2. Observe the row order

**Expected outcome:** Rows with numeric values sort largest-to-smallest at the top; NA rows appear at the bottom.
**Pass criteria:** First N rows have numeric values sorted largest-to-smallest; rows N+1 onward are all NA.

---

### TC-12 — Research RSP table Regime filter dropdown exists and filters rows

**Type:** browser
**Preconditions:** Frontend running; `/research` loaded with RSP study visible; at least two distinct regime values exist in the table (e.g., "Uptrend", "Neutral").

**Steps:**
1. Locate the Regime filter dropdown in the RSP section
2. Click the dropdown and observe the options (should include "All" and each regime label from config)
3. Select "Uptrend"
4. Observe the table

**Expected outcome:** Table displays only rows with Regime = "Uptrend"; all other rows are hidden.
**Pass criteria:** Dropdown appears; shows config-driven regime labels; filtering works; page does not reload; selecting "All" restores all rows.

---

### TC-13 — Research RSP table Setup filter dropdown exists and filters rows

**Type:** browser
**Preconditions:** TC-12 passed; at least two distinct setup values exist.

**Steps:**
1. Locate the Setup filter dropdown
2. Click the dropdown and select a specific setup (e.g., "Breakout")
3. Observe the table

**Expected outcome:** Table displays only rows with Setup = "Breakout"; all other rows are hidden.
**Pass criteria:** Dropdown shows setup options; filtering works; selecting "All" restores all rows.

---

### TC-14 — Research RSP table Pattern filter dropdown exists and filters rows including pattern=none

**Type:** browser
**Preconditions:** TC-13 passed; at least one row with Pattern = "none" exists in the table.

**Steps:**
1. Locate the Pattern filter dropdown
2. Click the dropdown and observe the options (should include pattern labels from config PLUS a "none" option)
3. Select "VCP" (or any specific pattern)
4. Observe the table; note that rows with Pattern = "none" are hidden
5. Select "none"
6. Observe that only rows with Pattern = "none" are displayed

**Expected outcome:** Table filters correctly by pattern; "none" is a valid filter value; selecting "All" shows all rows.
**Pass criteria:** "none" option appears in the dropdown; filtering by "none" works; filtering by a specific pattern excludes "none" rows.

---

### TC-15 — Research RSP filters compose (Regime + Setup + Pattern together)

**Type:** browser
**Preconditions:** TC-14 passed; at least one row matches a combined filter (e.g., Regime="Uptrend" AND Setup="Breakout" AND Pattern="VCP").

**Steps:**
1. Set Regime filter to "Uptrend"
2. Set Setup filter to "Breakout"
3. Set Pattern filter to "VCP"
4. Observe the table

**Expected outcome:** Table displays only rows matching all three filters simultaneously; filtering is a pure view transform (no page reload).
**Pass criteria:** Table shows the correct intersection of rows; combining filters works; page does not reload.

---

### TC-16 — Research RSP N= chip opens samples drill-down for pattern=none row

**Type:** browser
**Preconditions:** Frontend running; `/research` loaded; a row with Pattern = "none" is visible (use the Pattern filter to show "none" rows).

**Steps:**
1. Locate a row with Pattern = "none"
2. Click the "N=" chip (e.g., "N=45")
3. Observe whether a new tab opens to `/research/samples`

**Expected outcome:** New tab opens to `/research/samples` with query parameters for the exact (regime, setup, pattern=none) combination; no 4xx error.
**Pass criteria:** New tab opens; URL contains correct query params (e.g., `?regime=Uptrend&setup=Breakout&pattern=none`); samples table loads; total row count matches the "N=" value.

---

### TC-17 — Research RSP N= chip opens samples drill-down for all emitted combinations

**Type:** browser
**Preconditions:** TC-16 passed; at least three rows with different (regime, setup, pattern) combinations visible.

**Steps:**
1. Select three different RSP rows (one with pattern="none", one with a specific pattern, one with a different setup)
2. Click each row's N= chip in a new tab
3. Verify each `/research/samples` page loads without error

**Expected outcome:** All three `/research/samples` pages load; each shows the correct sample count matching the row's N value.
**Pass criteria:** All N= chips are clickable; all drill-downs load without 4xx; sample total == row N for every combination tested.

---

### TC-18 — Research RSP section defaults to Pooled view

**Type:** browser
**Preconditions:** Frontend running; `/research` loaded; a toggle labeled "Episodes / Pooled" (or similar) is visible in the RSP section.

**Steps:**
1. Navigate to `/research`
2. Observe the RSP section toggle
3. Check which view is selected (should be "Pooled")
4. Scroll to verify the table displays pooled-aggregated data (not per-episode rows)

**Expected outcome:** The toggle initializes to "Pooled"; clicking it once switches to "Episodes"; clicking again returns to "Pooled".
**Pass criteria:** RSP section shows Pooled by default (no page reload required); toggle switches views; the rest of `/research` (J-29/J-63) remains Episodes-default.

---

### TC-19 — Research RSP Pooled view produces correct sample counts (count-coherence)

**Type:** api
**Preconditions:** Backend running; at least one RSP row exists with a known (regime, setup, pattern) combination and published N value.

**Steps:**
1. Note an RSP row's (regime, setup, pattern) and N value (e.g., Regime="Uptrend", Setup="Breakout", Pattern="VCP", N=45)
2. Run: `curl -s 'http://localhost:8835/api/research/samples?regime=Uptrend&setup=Breakout&pattern=VCP&view=pooled'`
3. Count the rows in the response (or check the response's `total` field if provided)

**Expected outcome:** The sample count matches the RSP table's published N (45 samples for the pooled query).
**Pass criteria:** `total === row.n` for the queried combination in pooled view; values computed using the same `_regime_setup_pattern_observations` builder and `_rsp_combination_filter` predicate the study uses.

---

### TC-20 — Research RSP Episodes view produces correct sample counts (count-coherence)

**Type:** api
**Preconditions:** TC-19 passed; at least one RSP row exists.

**Steps:**
1. Note an RSP row's (regime, setup, pattern) and N value
2. Run: `curl -s 'http://localhost:8835/api/research/samples?regime=Uptrend&setup=Breakout&pattern=VCP&view=episodes'`
3. Count the rows in the response (or sum the episode sample counts)

**Expected outcome:** Total sample count matches the RSP table's N in Episodes view as well.
**Pass criteria:** Sum of episode samples === row.n; same combinations work in both views.

---

### TC-21 — Unit test: theme forward_returns byte-equal to Backtest _leadership_returns

**Type:** artifact
**Preconditions:** Backend tests pass; test file exists at `apps/backend/tests/test_themes_forward_returns_coherence.py` (or similar).

**Steps:**
1. Run: `cd apps/backend && .venv/bin/python -m pytest tests/test_themes_forward_returns_coherence.py -v`
2. Inspect the test output

**Expected outcome:** Test passes; asserts that theme forward_returns on `/api/themes` matches the output of `_leadership_returns` for the same run+horizon.
**Pass criteria:** Test passes; assertion message confirms byte-equality; no recompute, no second query path.

---

### TC-22 — Unit test: sector forward_returns byte-equal to Backtest _leadership_returns

**Type:** artifact
**Preconditions:** Backend tests pass.

**Steps:**
1. Run: `cd apps/backend && .venv/bin/python -m pytest tests/test_sectors_forward_returns_coherence.py -v`
2. Inspect the test output

**Expected outcome:** Test passes; asserts that sector forward_returns match `_leadership_returns` projection for each sector/ETF.
**Pass criteria:** Test passes; assertion confirms byte-equality; all five horizons are tested.

---

### TC-23 — Unit test: RSP samples validation accepts every emitted combination

**Type:** artifact
**Preconditions:** Backend tests pass.

**Steps:**
1. Run: `cd apps/backend && .venv/bin/python -m pytest tests/test_rsp_samples_combinations.py -v`
2. Inspect output for test cases covering pattern=none and empty/None regime values

**Expected outcome:** Test passes; asserts that every (regime, setup, pattern) combination the study emits is accepted by `_regime_setup_pattern_samples` validation.
**Pass criteria:** Test covers pattern=none; test covers empty/None regime; all combinations pass validation; a genuinely non-emitted combination still returns 4xx.

---

### TC-24 — Unit test: RSP samples drill-down total equals row N in Episodes and Pooled

**Type:** artifact
**Preconditions:** Backend tests pass.

**Steps:**
1. Run: `cd apps/backend && .venv/bin/python -m pytest tests/test_rsp_samples_count_coherence.py -v`
2. Inspect for assertions covering both Episodes and Pooled views

**Expected outcome:** Test passes; asserts that the samples drill-down total matches the study row's N in both views.
**Pass criteria:** Test covers Episodes view; test covers Pooled view; all tested combinations have `total === row.n`.

---

### TC-25 — Unit test: J-29/J-63 event-study figures remain byte-identical (no regression)

**Type:** artifact
**Preconditions:** Backend tests pass; test exists asserting byte-identity of event-study output before and after J-82.

**Steps:**
1. Run: `cd apps/backend && .venv/bin/python -m pytest tests/test_event_study_regression.py -v`
2. Inspect for assertions comparing old and new event-study output

**Expected outcome:** Test passes; asserts that the event-study figures (J-29/J-63) are unchanged by the J-82 RSP changes.
**Pass criteria:** Test passes; figures are byte-identical; no anti-goal violation (J-82 changed no canonical value).

---

### TC-26 — Full pytest suite passes with no new failures

**Type:** artifact
**Preconditions:** Backend implementation complete; all changes committed; database in a clean state.

**Steps:**
1. Run: `cd apps/backend && .venv/bin/python -m pytest tests/ -v 2>&1 | tee /tmp/pytest.log`
2. Wait for all tests to complete (approx. 30–40 minutes)
3. Inspect the summary line (e.g., "639 passed in 2345s")

**Expected outcome:** All tests pass; no failures; no regressions from previous iterations.
**Pass criteria:** Exit code is 0; summary shows "X passed"; no "failed" or "error" messages; the required-still-passing journeys (J-03, J-04, J-06, J-09, J-21, J-29, J-32, J-48, J-51, J-63, J-75, J-77) are all represented in passing tests.

---

## Summary

Total test cases: 26
- Browser tests: 12 (TC-01–TC-07, TC-10–TC-18)
- API tests: 3 (TC-08, TC-09, TC-19, TC-20)
- Artifact tests: 6 (TC-21–TC-26)

**Coverage:**
- J-81 (Themes/Sectors forward-return columns): TC-01–TC-07, TC-08–TC-09, TC-21–TC-22
- J-82(a) (NA-last sorting): TC-10–TC-11
- J-82(b) (Regime/Setup/Pattern filters): TC-12–TC-15
- J-82(c) (N= drill-down, samples validation, count-coherence): TC-16–TC-20, TC-23–TC-24
- J-82(d) (Pooled default): TC-18
- Required-still-passing verification: TC-26
- Anti-goal compliance: TC-21–TC-25
