# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20
**Date:** 2026-06-15
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->
<!-- Vague steps like "test the form" or "verify it works" are not acceptable. -->

---

### UT-01 — Stocks leaderboard loads with forward-return columns (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running and accessible
- At least one historical scan date is available in the system

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Wait for the leaderboard table to fully render (skeleton disappears)

**Expected Result:**
- Page renders without a blank screen or error message
- The leaderboard table is visible with stock rows
- Five new column headers are visible to the right of the existing columns: "1d", "5d", "10d", "20d", "60d"
- No console errors

---

### UT-02 — Forward returns displayed at historical date with colour grading (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835
- A historical scan date with complete forward-return data exists (e.g., 2021-01-04 — scan data for that date was followed by enough trading days)

**Steps:**
1. Navigate to `http://localhost:3835/stocks?asof=2021-01-04`
2. Wait for the leaderboard table to render
3. Locate any stock row that shows a numeric value (not "NA") in the "5d" column
4. Observe the cell colour for a positive value
5. Locate a stock row that shows a negative numeric value in the "5d" column
6. Observe the cell colour for that negative value

**Expected Result:**
- A cell with a positive return value is displayed in green text
- A cell with a negative return value is displayed in red text
- Cells where no post-date data exists show "NA" in muted (grey) text
- All five columns (1d, 5d, 10d, 20d, 60d) are populated or show "NA" — no cells are empty/blank

---

### UT-03 — Forward-return columns are sortable; NA values sort last (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835
- A historical scan date with at least some forward-return data and at least some NA values exists

**Steps:**
1. Navigate to `http://localhost:3835/stocks?asof=2021-01-04`
2. Wait for the leaderboard table to render
3. Click the "5d" column header
4. Observe the table re-order
5. Scroll to the bottom of the table and inspect the last few rows

**Expected Result:**
- The table re-orders with the highest 5d return values at the top
- All rows displaying "NA" in the 5d column appear at the bottom of the sorted table, not interspersed with numeric values
- No page reload or network spinner occurs during the sort — the table re-orders client-side instantly
- Clicking the "5d" header a second time reverses the order (lowest values first, NA still at bottom)

---

### UT-04 — Stock Detail page shows "Realized forward returns" panel at historical date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/[ticker]`

**Preconditions:**
- Frontend is running at http://localhost:3835
- AAPL exists in the system with forward-return data for 2021-01-04

**Steps:**
1. Navigate to `http://localhost:3835/stocks/AAPL?asof=2021-01-04`
2. Wait for the page to fully load
3. Observe the area above the price chart

**Expected Result:**
- A card or panel labelled "Realized forward returns" (or equivalent heading) appears above the price chart
- The panel contains exactly five tiles, one each for the horizons: 1d, 5d, 10d, 20d, 60d
- Each tile shows a numeric return value (not "NA") that is colour-graded green (positive) or red (negative)
- The values in the five tiles match the values shown in the corresponding row for AAPL in the `/stocks?asof=2021-01-04` leaderboard

---

### UT-05 — Stock Detail "Realized forward returns" panel shows NA honestly at latest date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/[ticker]`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The latest available scan date has no forward-return data (expected by design — no future bars to compute from)

**Steps:**
1. Navigate to `http://localhost:3835/stocks/AAPL` (no `?asof` parameter — defaults to latest date)
2. Wait for the page to fully load
3. Locate the "Realized forward returns" panel above the price chart

**Expected Result:**
- The "Realized forward returns" panel is present above the price chart
- All five tiles (1d, 5d, 10d, 20d, 60d) each show "NA" in muted text
- No tile shows a fabricated numeric value
- The panel does not hide or collapse just because all values are NA

---

### UT-06 — Research page loads with new "Regime x Setup x Pattern" section (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running and accessible

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the page to load (individual sections may load at different times — wait until skeleton loaders disappear from all sections)
3. Scroll down past the Event Study and Combination Lab sections

**Expected Result:**
- The page renders without a blank screen or error message
- A new section labelled "Regime x Setup x Pattern" (or equivalent) is visible below the existing Event Study / Combination Lab sections
- The section contains a table with columns including: Regime, Setup, Pattern, N, Mean, Median, Hit-rate, Expectancy, and at least one risk-adjusted return column
- A survivorship-bias caveat or disclaimer banner is visible within or near the new section
- No console errors

---

### UT-07 — Regime x Setup x Pattern study table sorts by column header click (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The Regime x Setup x Pattern study table has rendered with at least three visible rows

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Regime x Setup x Pattern" study section
3. Wait for the table to fully render (skeleton disappears, rows visible)
4. Note the order of the first three rows (record Regime/Setup/Pattern values in column 1)
5. Click the "Mean" column header
6. Observe the table re-order
7. Note the new order of the first three rows

**Expected Result:**
- The table re-orders after clicking "Mean": highest mean values appear at the top
- The first three rows in the new order are different from the original order (confirming the sort changed the display)
- No page reload occurs — the sort is client-side and instant
- The default order (before clicking "Mean") reflects the risk-adjusted rank served by the backend

---

### UT-08 — Regime x Setup x Pattern Episodes/Pooled toggle works independently (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The Regime x Setup x Pattern study table is visible with data

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Regime x Setup x Pattern" study section
3. Verify the toggle shows "Episodes" as the current selection
4. Record the N value from the first non-NA row in the table
5. Click the "Pooled" option on the study's own toggle
6. Wait for the table to re-render
7. Record the N value from the same first row (same Regime/Setup/Pattern combination if visible)
8. Observe the other study sections on the page (Event Study, Combination Lab)

**Expected Result:**
- The Regime x Setup x Pattern table re-fetches and re-renders showing Pooled data
- The N value for the same combination changes between Episodes and Pooled modes (Pooled typically includes more observations)
- The Event Study and Combination Lab sections do NOT reload, flash, or reset their own toggles
- Switching the Regime x Setup x Pattern toggle does not affect any other section on the page

---

### UT-09 — N= chip opens drill-down in new tab with correct cohort heading (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` and `/research/samples`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The Regime x Setup x Pattern study table has at least one row where N > 0 and is NOT shown as NA

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Regime x Setup x Pattern" study section
3. Wait for the table to fully render
4. Locate any row with a non-NA N value (e.g., a chip showing "N=12" or similar)
5. Note the Regime, Setup, and Pattern values for that row
6. Click the N= chip (e.g., the "N=12" link/chip)
7. Switch to the newly opened browser tab
8. Read the heading at the top of the samples page

**Expected Result:**
- A new browser tab opens (original tab stays on `/research`)
- The new tab loads `/research/samples` with the correct combination parameters in the URL
- The heading on the samples page identifies the specific combination (e.g., "Bull / Trending / VCP — Episodes" or equivalent format), NOT a generic or empty heading
- A table of sample observations is visible below the heading
- The total count of rows in the samples table equals the N value that was shown in the chip on the research page

---

### UT-10 — Low-sample rows show NA in return columns but still display N (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The Regime x Setup x Pattern study table contains at least one combination with a low observation count (below the minimum sample threshold)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Regime x Setup x Pattern" study section
3. Identify a row where all return statistic columns (Mean, Median, Hit-rate, Expectancy) show "NA"
4. Observe the N column for that same row

**Expected Result:**
- The row shows a numeric value in the N column (e.g., "3" or "2")
- The Mean, Median, Hit-rate, Expectancy, and risk-adjusted columns all show "NA" or equivalent muted placeholder
- No fabricated numeric values appear in the statistic columns for that row
- The row is still visible in the table (it is not hidden or omitted)

---

### UT-11 — Research page sections load independently (UX)

**Type:** ux
**Priority:** P2
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running (a cold backend where the event-study cache is empty makes this easier to observe)

**Steps:**
1. Open a new browser tab (Ctrl+T or Cmd+T to ensure a fresh page load)
2. Navigate to `http://localhost:3835/research`
3. Immediately observe all sections of the page during the loading phase (do not wait for full load)
4. Watch which sections become interactive first

**Expected Result:**
- Individual loading skeletons appear per section (Combination Lab, Event Study, Regime x Setup x Pattern each have their own skeleton state)
- The Combination Lab or Regime x Setup x Pattern section becomes interactive and shows data BEFORE the Event Study section finishes loading
- There is NO single full-page spinner blocking the entire page
- Each section transitions from skeleton to live data independently without the others resetting

---

### UT-12 — Event Study cached figures match on second load (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running with the event-study cache populated (load the page once first to warm the cache)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the Event Study section to fully load (skeletons disappear)
3. Record the first three visible figures in the Event Study section (e.g., Mean return for the first horizon, Median, Hit-rate)
4. Refresh the page by pressing F5 (or Cmd+R on Mac)
5. Wait for the Event Study section to fully load again
6. Compare the figures to the values recorded in step 3

**Expected Result:**
- The figures in the Event Study section after the second load are identical to the values recorded before the refresh
- The second page load is visibly faster (the Event Study section appears to load more quickly than the first time)
- No values change, round differently, or disappear between the first and second load

---

### UT-13 — Leaderboard existing score and rank columns still work after new columns added (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835
- At least one historical scan date is available

**Steps:**
1. Navigate to `http://localhost:3835/stocks?asof=2021-01-04`
2. Wait for the leaderboard table to render
3. Note the stock name and score value in the first (rank 1) row
4. Click on the stock name in the first row to navigate to the Stock Detail page
5. On the Stock Detail page, note the score displayed
6. Press the browser back button to return to `/stocks`
7. Verify the table is still showing the same data in the original sort order

**Expected Result:**
- The existing columns (Score, Rank, Setup, Patterns, Themes) are all still present and correctly populated
- The score on the Stock Detail page matches the score shown for that stock in the leaderboard
- The browser back button returns to the leaderboard with the same data intact
- No existing columns were removed or replaced by the five new forward-return columns

---

### UT-14 — Leaderboard and Stock Detail forward returns are identical for same date (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks` and `/stocks/[ticker]`

**Preconditions:**
- Frontend is running at http://localhost:3835
- AAPL exists with complete forward-return data at 2021-01-04

**Steps:**
1. Navigate to `http://localhost:3835/stocks?asof=2021-01-04`
2. Wait for the leaderboard table to render
3. Find the AAPL row and record its 5d forward return value (write down the exact number displayed)
4. Click on "AAPL" to navigate to the Stock Detail page
5. On the Stock Detail page, locate the "Realized forward returns" panel
6. Read the value shown in the "5d" tile

**Expected Result:**
- The 5d value displayed in the "Realized forward returns" panel on the Stock Detail page exactly matches the value shown in the "5d" column of the leaderboard for AAPL
- Both values are identical (same numeric display, same colour grading)

---

### UT-15 — Samples page heading is meaningful for Regime x Setup x Pattern cohort (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/samples`

**Preconditions:**
- Frontend is running at http://localhost:3835
- A Regime x Setup x Pattern N= chip has been clicked in a previous step (or navigate directly via the URL from a chip click)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Regime x Setup x Pattern" study section
3. Find any row with a non-NA N= chip
4. Note the exact Regime, Setup, and Pattern values for that row
5. Click the N= chip for that row
6. In the new tab that opens, read the page heading

**Expected Result:**
- The page heading explicitly names the combination (e.g., "Bear / Avoid / (none) — Episodes" or "Bull / Trending / VCP — Pooled")
- The heading does NOT show a generic fallback like "Unknown cohort", an empty string, or a raw URL parameter dump
- The heading accurately reflects the Regime, Setup, and Pattern values noted in step 4

---

### UT-16 — Research page Combination Lab and other existing sections still work (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- At least one scan date with research data is available

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the Combination Lab section to finish loading (skeleton disappears)
3. Observe the Combination Lab table and confirm it has data rows
4. Click any N= chip in the Combination Lab (not the new Regime x Setup x Pattern section)
5. Observe the new tab that opens

**Expected Result:**
- The Combination Lab section renders normally with its own data rows
- The N= chip in the Combination Lab opens `/research/samples` in a new tab (same as before this phase)
- The samples page heading correctly identifies the Combination Lab cohort (not confused with Regime x Setup x Pattern cohort)
- No existing Combination Lab functionality was broken by the addition of the new study section

---

### UT-17 — Stocks page forward-return sort does not refetch data (UX)

**Type:** ux
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Browser developer tools are open to the Network tab (optional but helpful)

**Steps:**
1. Navigate to `http://localhost:3835/stocks?asof=2021-01-04`
2. Wait for the leaderboard table to fully render
3. Open the browser's Developer Tools (press F12) and click the "Network" tab
4. Click the "1d" column header in the leaderboard
5. Observe the Network tab for any new requests

**Expected Result:**
- The table re-orders immediately after clicking "1d" without any visible loading delay
- No new network requests appear in the Network tab after clicking the column header (the sort is client-side only)
- The URL in the address bar does NOT change when clicking a column header (sort state is not persisted in the URL)

---

### UT-18 — Stock Detail page still loads existing content with new panel added (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks/[ticker]`

**Preconditions:**
- Frontend is running at http://localhost:3835
- AAPL exists in the system

**Steps:**
1. Navigate to `http://localhost:3835/stocks/AAPL`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error message
- The stock ticker/name heading is visible at the top of the page
- The "Realized forward returns" panel appears above the price chart (new this phase)
- The price chart itself still renders below the panel
- Existing stock details (score, setup status, patterns) are still visible
- No console errors

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Stocks leaderboard loads with forward-return columns | smoke | P1 | `/stocks` |
| UT-02 | Forward returns displayed at historical date with colour grading | happy-path | P1 | `/stocks` |
| UT-03 | Forward-return columns are sortable; NA values sort last | happy-path | P1 | `/stocks` |
| UT-04 | Stock Detail shows "Realized forward returns" panel at historical date | happy-path | P1 | `/stocks/[ticker]` |
| UT-05 | Stock Detail "Realized forward returns" panel shows NA honestly at latest date | happy-path | P1 | `/stocks/[ticker]` |
| UT-06 | Research page loads with new "Regime x Setup x Pattern" section | smoke | P1 | `/research` |
| UT-07 | Regime x Setup x Pattern study table sorts by column header click | happy-path | P1 | `/research` |
| UT-08 | Regime x Setup x Pattern Episodes/Pooled toggle works independently | happy-path | P1 | `/research` |
| UT-09 | N= chip opens drill-down in new tab with correct cohort heading | happy-path | P1 | `/research` + `/research/samples` |
| UT-10 | Low-sample rows show NA in return columns but still display N | validation | P2 | `/research` |
| UT-11 | Research page sections load independently | ux | P2 | `/research` |
| UT-12 | Event Study cached figures match on second load | regression | P1 | `/research` |
| UT-13 | Leaderboard existing score and rank columns still work after new columns added | regression | P1 | `/stocks` |
| UT-14 | Leaderboard and Stock Detail forward returns are identical for same date | regression | P1 | `/stocks` + `/stocks/[ticker]` |
| UT-15 | Samples page heading is meaningful for Regime x Setup x Pattern cohort | regression | P1 | `/research/samples` |
| UT-16 | Research page Combination Lab and other existing sections still work | regression | P1 | `/research` |
| UT-17 | Stocks page forward-return sort does not refetch data | ux | P2 | `/stocks` |
| UT-18 | Stock Detail page still loads existing content with new panel added | smoke | P1 | `/stocks/[ticker]` |

**P1 tests must all pass for browser QA verdict to be PASS.**
