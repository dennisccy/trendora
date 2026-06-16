# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23
**Date:** 2026-06-16
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Themes leaderboard loads with five new forward-return column headers (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/themes`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- At least one historical snapshot exists

**Steps:**
1. Navigate to `http://localhost:3835/themes`
2. Wait for the page to fully load (the leaderboard table appears)
3. Scan the table header row for column labels

**Expected Result:**
- Page renders without a blank screen or error message
- The Themes leaderboard table is visible
- The table header row contains five column labels corresponding to forward-return horizons: "1d", "5d", "10d", "20d", and "60d" (exact label text may include a "%" sign or similar — all five must be present)
- No JavaScript error banner or "Something went wrong" text appears

---

### UT-02 — Sectors leaderboard loads with five new forward-return column headers (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/sectors`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Wait for the page to fully load
3. Scan the table header row for column labels

**Expected Result:**
- Page renders without a blank screen or error message
- The Sectors leaderboard table is visible
- The table header row contains five column labels: "1d", "5d", "10d", "20d", and "60d"
- No JavaScript error banner appears

---

### UT-03 — Research page loads with RSP filter dropdowns visible (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the page to fully load
3. Scroll down to the "Regime × Setup × Pattern" table section

**Expected Result:**
- Page renders without a blank screen or error message
- The Regime × Setup × Pattern section is visible
- Three filter dropdowns labelled "Regime", "Setup", and "Pattern" (or equivalent) are visible in the controls row near the top of that section
- Each dropdown shows "All" as its default selected value
- No JavaScript error banner appears

---

### UT-04 — Themes forward-return columns display numeric values at a historical as-of date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/themes`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- A historical snapshot exists with post-date price bars (e.g., a date at least 60 trading days before the latest available date)

**Steps:**
1. Navigate to `http://localhost:3835/themes`
2. Locate the global as-of date picker in the page header
3. Click the date picker and select a historical date that is at least 60 trading days before the most recent date (e.g., 2024-01-15 or another date known to have post-D bars)
4. Wait for the page to reload and the themes table to appear
5. Observe the five forward-return columns (1d / 5d / 10d / 20d / 60d) in the table
6. Inspect at least three rows across those five columns

**Expected Result:**
- The five forward-return columns each contain cells for every theme row
- At least one cell in the 1d and 5d columns shows a numeric percentage value (e.g., "+2.3%" or "-1.1%") — not blank, not "0%", not "undefined"
- Cells that show a numeric positive value are rendered in green text (or a green-tinted background)
- Cells that show a numeric negative value are rendered in red text (or a red-tinted background)
- Cells where no data exists show "NA" in muted/grey text (not "0%" and not blank)

---

### UT-05 — Sectors forward-return columns display numeric values at a historical as-of date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/sectors`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- A historical snapshot exists with post-date price bars for at least some sector ETFs

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Locate the global as-of date picker
3. Click the date picker and select the same historical date used in UT-04 (e.g., 2024-01-15)
4. Wait for the page to reload and the sectors table to appear
5. Observe the five forward-return columns (1d / 5d / 10d / 20d / 60d) in the table
6. Inspect at least three sector rows

**Expected Result:**
- The five forward-return columns each contain cells for every sector row
- At least one cell in the 1d and 5d columns shows a numeric percentage value
- Cells with positive returns are rendered in green; cells with negative returns in red
- Cells without data show "NA" in muted text (not "0%")

---

### UT-06 — Themes leaderboard can be sorted by the 5d forward-return column (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/themes`

**Preconditions:**
- UT-04 completed successfully (themes displayed at a historical as-of date with numeric values in the 5d column)
- At least two theme rows have numeric (non-NA) values in the 5d column

**Steps:**
1. Navigate to `http://localhost:3835/themes` and set the as-of date to the same historical date used in UT-04
2. Note the order of the top three theme rows (write down the theme names)
3. Click the "5d" column header
4. Observe the new row order
5. Confirm no loading spinner or page reload occurred
6. Click the "5d" column header a second time
7. Observe the new row order

**Expected Result:**
- After the first click: rows with numeric 5d values are reordered smallest-to-largest (ascending); any rows displaying "NA" appear below all numeric rows
- After the second click: rows with numeric 5d values are reordered largest-to-smallest (descending); any rows displaying "NA" still appear below all numeric rows
- At no point does a network loading spinner appear — the sort is purely a view transform
- The theme names and other column values remain intact (only the order changes)

---

### UT-07 — Sectors leaderboard can be sorted by the 20d forward-return column (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/sectors`

**Preconditions:**
- UT-05 completed successfully (sectors displayed at a historical as-of date with numeric values)
- At least two sector rows have numeric (non-NA) values in the 20d column

**Steps:**
1. Navigate to `http://localhost:3835/sectors` and set the as-of date to the same historical date used in UT-05
2. Note the order of the top three sector rows
3. Click the "20d" column header
4. Observe the new row order
5. Confirm no loading spinner appeared
6. Click the "20d" column header a second time
7. Observe the new row order

**Expected Result:**
- After the first click: rows reorder smallest-to-largest by 20d return with NA rows at the bottom
- After the second click: rows reorder largest-to-smallest with NA rows still at the bottom
- No network request is triggered — the sort is a client-side view transform

---

### UT-08 — Research RSP section defaults to Pooled view on page load (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/research` (fresh load — no prior navigation to this page in this session)
2. Wait for the page to fully load
3. Scroll to the Regime × Setup × Pattern section
4. Look at the Episodes / Pooled toggle or tabs in that section

**Expected Result:**
- The Regime × Setup × Pattern section shows "Pooled" as the active/selected view without any user interaction
- The table in that section displays pooled-aggregated data (rows represent regime/setup/pattern combinations, not individual episodes)
- The toggle control visually indicates "Pooled" is selected (e.g., highlighted button, underline, or active state)
- Other research sections visible on the same page (e.g., Event Study, Cluster) still show "Episodes" as their default — those sections are unchanged

---

### UT-09 — Research RSP Regime filter narrows the table to matching rows only (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend running; RSP table shows multiple rows with at least two distinct Regime values (e.g., "Uptrend" and "Neutral")

**Steps:**
1. Navigate to `http://localhost:3835/research` and scroll to the Regime × Setup × Pattern section
2. Locate the "Regime" dropdown (default shows "All")
3. Click the "Regime" dropdown to open it
4. Observe the available options — there should be at least two regime labels plus an "All" option
5. Select any one specific regime label (e.g., the first non-"All" option in the list)
6. Observe the RSP table

**Expected Result:**
- The RSP table immediately redraws to show only rows where the Regime column matches the selected regime label
- Rows with other regime values are hidden (not deleted — they reappear when "All" is selected again)
- No page reload or loading spinner occurs — the filter is a pure client-side view transform
- The row count visible in the table decreases (or stays the same if all rows share that regime)

---

### UT-10 — Research RSP Regime + Pattern filters compose correctly (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- UT-09 completed; RSP table shows at least some rows
- At least one row in the RSP table has a specific Pattern value visible (not "—")

**Steps:**
1. Navigate to `http://localhost:3835/research` and scroll to the RSP section
2. Click the "Regime" dropdown and select a specific regime (e.g., the first non-"All" option)
3. Note the number of rows currently shown
4. Click the "Pattern" dropdown and select a specific pattern (e.g., the first non-"All" non-"none" option)
5. Observe the RSP table

**Expected Result:**
- The table shows only rows matching BOTH the selected Regime AND the selected Pattern simultaneously
- The visible row count is less than or equal to the count after the Regime-only filter in step 2
- No page reload occurs
- Resetting both dropdowns back to "All" restores all original rows

---

### UT-11 — Research RSP numeric sort pushes NA rows to the bottom (ascending) (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend running; RSP table is visible with Pooled default active; at least one row displays "NA" in a numeric column (e.g., "Win Rate" or "Return 1d")

**Steps:**
1. Navigate to `http://localhost:3835/research` and scroll to the RSP section
2. Identify a numeric column header in the RSP table (e.g., "Win Rate", "Return 1d", or similar)
3. Click that column header once to sort ascending
4. Scroll through the sorted table and observe where "NA" cells appear

**Expected Result:**
- All rows with a numeric value in the sorted column appear first, sorted smallest to largest
- All rows displaying "NA" in that column appear after (below) every row with a numeric value
- No "NA" row appears between two numeric-value rows
- No page reload occurs

---

### UT-12 — Research RSP numeric sort keeps NA rows at the bottom (descending) (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- UT-11 completed (table sorted ascending with NA at bottom)

**Steps:**
1. Click the same column header used in UT-11 a second time to sort descending
2. Scroll through the sorted table

**Expected Result:**
- All rows with numeric values in the sorted column appear first, now sorted largest to smallest
- All rows displaying "NA" in that column still appear at the bottom (below all numeric rows)
- NA rows do not float to the top in descending sort
- No page reload occurs

---

### UT-13 — Research RSP N= chip for a standard pattern row opens samples drill-down without error (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → `/research/samples`

**Preconditions:**
- Frontend running; RSP table is visible with at least one row that has a non-zero N value and a named pattern (not "— (none)")
- Browser allows opening new tabs

**Steps:**
1. Navigate to `http://localhost:3835/research` and scroll to the RSP section
2. Locate any row with a visible pattern name (not "— (none)") and an N= chip (e.g., "N=34")
3. Note the exact N value on the chip (e.g., 34) and the row's Regime, Setup, and Pattern labels
4. Click the N= chip
5. Switch to the newly opened browser tab

**Expected Result:**
- A new tab opens to `http://localhost:3835/research/samples` (or equivalent) with query parameters for the selected Regime, Setup, and Pattern
- The samples page loads successfully — no error page, no "404 Not Found", no "500 Internal Server Error"
- The samples table is visible and the total count shown (e.g., "34 observations" or a row count of 34) matches the N value noted in step 3

---

### UT-14 — Research RSP N= chip for a "none" pattern row opens samples drill-down without error (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → `/research/samples`

**Preconditions:**
- Frontend running; RSP table is visible; at least one row exists where the Pattern column shows "— (none)" or similar "no pattern" indicator

**Steps:**
1. Navigate to `http://localhost:3835/research` and scroll to the RSP section
2. If no "— (none)" pattern row is immediately visible, click the "Pattern" dropdown and select the "none" option to filter down to those rows
3. Locate a row displaying "— (none)" in the Pattern column with an N= chip (e.g., "N=18")
4. Note the exact N value (e.g., 18) and the row's Regime and Setup labels
5. Click the N= chip
6. Switch to the newly opened browser tab

**Expected Result:**
- A new tab opens to `/research/samples` with query parameters that include `pattern=none` (or the app's equivalent encoding for "no pattern")
- The samples page loads successfully — no error page, no 4xx/5xx response visible
- The total observation count shown matches the N value noted in step 4
- The table content is non-empty (the cohort has observations)

---

### UT-15 — Forward-return cells show "NA" (not 0%) at the latest available as-of date (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/themes`

**Preconditions:**
- Frontend running; backend running with data up to approximately the current date

**Steps:**
1. Navigate to `http://localhost:3835/themes`
2. If an as-of date picker is visible, confirm it is set to the most recent available date ("Latest" or today's date) — do not change it if it already defaults to the latest
3. Observe the 60d forward-return column in the themes table
4. Also observe the 20d and 10d columns

**Expected Result:**
- Most or all cells in the 60d column show "NA" in muted/grey text (because 60 trading days of post-date price bars do not exist from the latest snapshot date)
- No cell shows "0%" in the 60d column as a substitute for NA
- No cell is blank/empty in the 60d column — it must show "NA" explicitly
- Some cells in the 1d column may show numeric values if very recent bars exist, but cells in the 60d column should not

---

### UT-16 — Research RSP empty-after-filter state displays an informative message (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research`

**Preconditions:**
- Frontend running; RSP table is visible with data

**Steps:**
1. Navigate to `http://localhost:3835/research` and scroll to the RSP section
2. Click the "Regime" dropdown and select a specific regime label
3. Click the "Pattern" dropdown and select a pattern that is unlikely to appear alongside the chosen regime (choose a pattern that, combined with the chosen regime, likely has no matching row in the table)
4. Observe the RSP table content

**Expected Result:**
- If no rows match, the table area shows a clear empty state — this could be a message such as "No matching combinations" or similar text, or at minimum a clearly empty table with a visible "0 rows" indicator
- The empty state is NOT a broken/blank layout (no half-rendered table skeleton with no content and no explanation)
- The filter dropdowns remain visible and operable so the operator can change filters
- Resetting both dropdowns to "All" restores all rows

---

### UT-17 — Themes page scores and existing columns still work after forward-return additions (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/themes`

**Preconditions:**
- Frontend running; backend running

**Steps:**
1. Navigate to `http://localhost:3835/themes`
2. Observe the existing theme score columns (the columns that existed before this iteration — e.g., theme name, composite score, momentum, trend, or similar)
3. Verify these columns still show data
4. Click a theme name (or any existing row link) to navigate to a theme detail page, if such navigation existed before this iteration

**Expected Result:**
- The original theme columns (name, score, or any pre-existing columns) still display data correctly alongside the new five forward-return columns
- No existing column is missing, misaligned, or replaced by a forward-return column
- If theme rows were previously clickable (navigating to a detail page), that navigation still works

---

### UT-18 — Sectors page scores and existing columns still work after forward-return additions (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/sectors`

**Preconditions:**
- Frontend running; backend running

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Observe the existing sector columns (sector name, ETF ticker, composite score, or similar pre-existing columns)
3. Verify these columns still show data
4. Confirm the table does not have duplicated or displaced columns

**Expected Result:**
- The original sector/ETF columns still display data correctly alongside the new five forward-return columns
- No pre-existing column is missing or corrupted
- The total number of theme and sector rows in the table is consistent with prior iterations (no rows dropped)

---

### UT-19 — Research Event Study and Cluster sections still default to Episodes after RSP Pooled default change (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend running; backend running; `/research` page contains sections other than RSP (e.g., Event Study, Cluster analysis)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the RSP section — confirm it shows Pooled as the default (already tested in UT-08)
3. Scroll to the Event Study section (or Cluster section, whichever is present)
4. Observe the Episodes / Pooled toggle for that section

**Expected Result:**
- The Event Study section (and any other non-RSP research sections) shows "Episodes" as the active default view — NOT Pooled
- These sections are unaffected by the RSP Pooled default change
- The data displayed in these sections is unchanged from prior iterations

---

### UT-20 — Themes and Sectors forward-return sort resets to served order after navigating away and back (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/themes`, `/sectors`

**Preconditions:**
- Frontend running; as-of set to a historical date with numeric forward-return values visible on `/themes`

**Steps:**
1. Navigate to `http://localhost:3835/themes` at a historical as-of date
2. Click the "5d" column header to sort ascending (rows reorder)
3. Note the new order of the top three rows
4. Navigate away — click another page (e.g., `/sectors` or `/stocks`)
5. Click "Themes" in the navigation to return to `/themes`
6. Observe the row order

**Expected Result:**
- After returning to `/themes`, the rows are displayed in the default served order (not the sorted order from step 2)
- The "5d" sort state does not persist across navigation — each page load returns to default
- The five forward-return columns are still visible after the navigation cycle

---

### UT-21 — Themes forward-return value matches Backtest Top Themes value for the same date and horizon (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/themes` and `/backtest`

**Preconditions:**
- Frontend running; a historical as-of date with non-NA forward-return values on `/themes` is available
- The `/backtest` page has a Top Themes section that also shows forward-return values

**Steps:**
1. Navigate to `http://localhost:3835/themes` with the as-of date set to a historical date (e.g., 2024-01-15)
2. Locate a theme with a non-NA value in the 5d column — note both the theme name and the exact percentage value (e.g., "Technology" with "3.21%")
3. Navigate to `http://localhost:3835/backtest`
4. Set the as-of date to the same historical date
5. Locate the Top Themes section
6. Find the same theme by name
7. Read its 5d forward-return value

**Expected Result:**
- The 5d value shown in Backtest for the matched theme is identical (to the same number of decimal places) to the value noted in step 2 from the `/themes` leaderboard
- The values match because both read from the same stored data source, not a re-computation

---

### UT-22 — New forward-return columns are discoverable without instructions (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/themes`

**Preconditions:**
- Frontend running

**Steps:**
1. Navigate to `http://localhost:3835/themes`
2. Without any prior knowledge of this feature, scan the leaderboard table header row
3. Identify whether the forward-return column headers (1d / 5d / 10d / 20d / 60d) are clearly labelled
4. Hover over (or click) one of the column headers and observe if a sort affordance is visible (e.g., an arrow icon, cursor change, or visual highlight)

**Expected Result:**
- The five column labels are readable without zooming or scrolling horizontally — they are not hidden under a toggle or collapsed
- Column header labels clearly communicate a time horizon (e.g., "1d", "5d" — a new user can infer these are forward-return periods)
- At least one visual affordance (sort arrow icon, cursor change to pointer, or bold/underline on hover) indicates the headers are clickable sort controls
- The colour grading on cells (green / red / muted) is consistent across the entire table — no mixed colour conventions

---

### UT-23 — RSP filter dropdowns are discoverable in the section controls row (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research`

**Preconditions:**
- Frontend running

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the Regime × Setup × Pattern section without any prior knowledge of the new dropdowns
3. Observe the section's controls row (the row above the table that typically contains the Episodes/Pooled toggle)

**Expected Result:**
- The three filter dropdowns (Regime, Setup, Pattern) are visually co-located with the Episodes/Pooled toggle in the same controls row — they are not hidden, collapsed, or in a secondary menu
- Each dropdown has a visible label ("Regime", "Setup", "Pattern" or equivalent) that makes its purpose clear
- The default "All" selection is visible in each dropdown before any user interaction
- The overall RSP section does not appear more cluttered or broken — controls row layout accommodates all four controls (toggle + three dropdowns)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Themes leaderboard loads with five forward-return column headers | smoke | P1 | `/themes` |
| UT-02 | Sectors leaderboard loads with five forward-return column headers | smoke | P1 | `/sectors` |
| UT-03 | Research page loads with RSP filter dropdowns visible | smoke | P1 | `/research` |
| UT-04 | Themes forward-return columns display numeric values at historical as-of | happy-path | P1 | `/themes` |
| UT-05 | Sectors forward-return columns display numeric values at historical as-of | happy-path | P1 | `/sectors` |
| UT-06 | Themes leaderboard can be sorted by the 5d forward-return column | happy-path | P1 | `/themes` |
| UT-07 | Sectors leaderboard can be sorted by the 20d forward-return column | happy-path | P1 | `/sectors` |
| UT-08 | Research RSP section defaults to Pooled view on page load | happy-path | P1 | `/research` |
| UT-09 | Research RSP Regime filter narrows the table to matching rows | happy-path | P1 | `/research` |
| UT-10 | Research RSP Regime + Pattern filters compose correctly | happy-path | P1 | `/research` |
| UT-11 | Research RSP numeric sort pushes NA rows to the bottom (ascending) | happy-path | P1 | `/research` |
| UT-12 | Research RSP numeric sort keeps NA rows at the bottom (descending) | happy-path | P1 | `/research` |
| UT-13 | Research RSP N= chip for standard pattern row opens samples without error | happy-path | P1 | `/research` → `/research/samples` |
| UT-14 | Research RSP N= chip for "none" pattern row opens samples without error | happy-path | P1 | `/research` → `/research/samples` |
| UT-15 | Forward-return cells show "NA" not "0%" at the latest as-of date | validation | P2 | `/themes` |
| UT-16 | Research RSP empty-after-filter state shows an informative message | validation | P2 | `/research` |
| UT-17 | Themes existing columns still work after forward-return additions | regression | P1 | `/themes` |
| UT-18 | Sectors existing columns still work after forward-return additions | regression | P1 | `/sectors` |
| UT-19 | Research Event Study / Cluster sections still default to Episodes | regression | P1 | `/research` |
| UT-20 | Themes/Sectors forward-return sort resets to default order after navigation | regression | P2 | `/themes`, `/sectors` |
| UT-21 | Themes forward-return value matches Backtest value for same date + horizon | regression | P1 | `/themes`, `/backtest` |
| UT-22 | New forward-return columns are discoverable without instructions | ux | P2 | `/themes` |
| UT-23 | RSP filter dropdowns are discoverable in the section controls row | ux | P2 | `/research` |

**P1 tests (UT-01 through UT-14, UT-17 through UT-19, UT-21) must all pass for browser QA verdict to be PASS.**
