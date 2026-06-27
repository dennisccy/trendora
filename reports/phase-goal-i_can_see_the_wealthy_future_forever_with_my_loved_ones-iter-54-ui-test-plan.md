# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-54 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-54
**Date:** 2026-06-27
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->
<!-- Vague steps like "test the form" or "verify it works" are not acceptable. -->

---

### UT-01 — Research hub loads with new Phase & Severity Lab tile (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and responsive

**Steps:**
1. Navigate to `http://localhost:3255/research`
2. Wait for the page to fully load (all tiles visible)
3. Scan the LABS section of the hub page for the tile with a Thermometer icon

**Expected Result:**
- Page renders without blank screen or error message
- The heading "Research" (or equivalent hub heading) is visible
- A tile labelled "Market Phase & Severity Lab" is present in the labs grid, showing a Thermometer icon
- No console errors are visible

---

### UT-02 — Phase & Severity Lab page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/phase-severity-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and responsive

**Steps:**
1. Navigate directly to `http://localhost:3255/research/phase-severity-lab`
2. Wait for the page to fully load (both tables must finish rendering — spinner or skeleton must disappear)

**Expected Result:**
- Page renders without blank screen, "Backend unavailable" banner, or unhandled error
- The heading "Market Phase & Severity Lab" is visible at the top of the page
- A survivorship-bias / descriptive-evidence caveat message is visible in the page header (e.g., text containing "survivorship" or "descriptive evidence")
- Two distinct tables are present on the page (by-phase-label table and by-decile table)

---

### UT-03 — Navigating from Research hub to Phase & Severity Lab via tile (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → `/research/phase-severity-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/research`
2. Wait for the Research hub to fully load
3. Locate the tile labelled "Market Phase & Severity Lab" (Thermometer icon)
4. Click the "Market Phase & Severity Lab" tile

**Expected Result:**
- Browser navigates to `http://localhost:3255/research/phase-severity-lab`
- The page heading "Market Phase & Severity Lab" is visible
- Both tables begin loading (spinner or data renders immediately)
- User is not redirected back to the hub or shown an error

---

### UT-04 — By-phase-label table renders five phase rows with paired return/MDD columns (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/phase-severity-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running with seeded data (phase labels and forward returns populated)

**Steps:**
1. Navigate to `http://localhost:3255/research/phase-severity-lab`
2. Wait for both tables to finish loading (no spinner visible)
3. Locate the by-phase-label table (data-testid `phase-severity-label-table`)
4. Count the data rows in the by-phase-label table (excluding the header row)
5. Confirm the row for phase label "Expansion" is present (data-testid `phase-severity-label-row-Expansion`)
6. Confirm the row for phase label "Recovery" is present (data-testid `phase-severity-label-row-Recovery`)
7. Confirm the row for phase label "Pullback" is present (data-testid `phase-severity-label-row-Pullback`)
8. Confirm the row for phase label "Correction" is present (data-testid `phase-severity-label-row-Correction`)
9. Confirm the row for phase label "Bear" is present (data-testid `phase-severity-label-row-Bear`)
10. In the "Expansion" row, locate the cell under the 1-day horizon forward-return column and confirm it shows a numeric value or "NA"

**Expected Result:**
- Exactly five data rows are present in the by-phase-label table: Expansion, Recovery, Pullback, Correction, Bear
- Each row shows at least one column with a numeric value (not blank or empty string)
- At least one horizon column shows both a forward-return cell and a max-drawdown cell paired together
- No row shows a raw number like "undefined" or "[object Object]"

---

### UT-05 — By-decile table renders Rank-IC header row plus D1–D10 rows with score ranges (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/phase-severity-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running with seeded data (severity scores and decile groupings populated)

**Steps:**
1. Navigate to `http://localhost:3255/research/phase-severity-lab`
2. Wait for both tables to finish loading
3. Locate the by-severity-decile table (data-testid `phase-severity-decile-table`)
4. Confirm the Rank-IC header row is present (data-testid `phase-severity-decile-rank-ic-row`)
5. Count the decile data rows (data-testids `phase-severity-decile-row-1` through `phase-severity-decile-row-10`)
6. In row D1 (data-testid `phase-severity-decile-row-1`), look at the first column and confirm it shows a score range (e.g., "0–10" or two numbers separated by a dash or dash-like character)
7. In row D10 (data-testid `phase-severity-decile-row-10`), confirm a score range is also visible in the first column

**Expected Result:**
- Exactly ten decile data rows are present: D1 through D10
- A Rank-IC header row appears above the D1–D10 rows (or as a distinct labelled row at the top of the table body)
- Each decile row shows a severity-score range in the first column (two numeric values separated by a range indicator)
- The Rank-IC row shows numeric or "NA" values per horizon (not blank)

---

### UT-06 — Column sort reorders rows and keeps NA cells at the bottom (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/phase-severity-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Both tables are fully loaded with data

**Steps:**
1. Navigate to `http://localhost:3255/research/phase-severity-lab`
2. Wait for both tables to finish loading
3. Note the current order of the five phase-label rows in the by-phase-label table (write down the first row's phase label, e.g., "Expansion")
4. Locate a sortable column header for a numeric horizon (e.g., the header for the forward-return column at the 20-day horizon); it must have an `aria-label` attribute (check by hovering — it should show a tooltip or cursor change)
5. Click that column header once
6. Wait for the table to re-render
7. Note the new order of the five phase-label rows (write down the first row's phase label again)
8. Click the same column header a second time to reverse the sort
9. Note the order again
10. Look at the bottom of the sorted column and confirm any "NA" cells appear at the very bottom (not interspersed with numeric rows)

**Expected Result:**
- After the first click, the row order is different from the original order (the first row's phase label has changed)
- After the second click (reverse), the row order changes again
- At no point do "NA" cells appear above numeric cells in the sorted column
- No page reload or API request is triggered (sort is client-side — the URL does not change)

---

### UT-07 — As-of filter reduces observation counts and adds no second date control (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/phase-severity-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The backend has historical data covering at least 6 months

**Steps:**
1. Navigate to `http://localhost:3255/research/phase-severity-lab`
2. Wait for both tables to finish loading
3. Note an N= value from any chip visible in the by-phase-label table (e.g., the chip for "Expansion" at the 20-day horizon shows "N=254"); write this number down
4. In the browser address bar, append `?asof=2024-06-01` to the URL and press Enter (full URL: `http://localhost:3255/research/phase-severity-lab?asof=2024-06-01`)
5. Wait for the page to reload and both tables to re-render
6. Note the N= value for the same "Expansion" at 20-day horizon chip again
7. Inspect the page for any `<input type="date">` element by right-clicking and choosing "Inspect" or using browser developer tools; search the Elements panel for `type="date"`

**Expected Result:**
- The N= value for the same bucket is smaller than the value noted in step 3 (observation count decreased when scoped to a historical date)
- No `<input type="date">` element exists anywhere in the page's DOM
- The URL retains `?asof=2024-06-01` after reload — the page does not strip the parameter
- The page heading and both tables are still visible (page did not error)

---

### UT-08 — N= chip opens matching Samples cohort in new tab with count-coherent total (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/phase-severity-lab` → `/research/samples`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running with seeded data
- Both tables are fully loaded (no spinner)

**Steps:**
1. Navigate to `http://localhost:3255/research/phase-severity-lab`
2. Wait for both tables to finish loading
3. In the by-phase-label table, find the "Bear" phase row and locate the N= chip for the 20-day horizon column (it should display a number, e.g., "N=31")
4. Write down the number shown on the chip (e.g., 31)
5. Middle-click or Ctrl+click (Cmd+click on Mac) the N= chip to open it in a new browser tab
6. Switch to the new tab and wait for `/research/samples` to finish loading
7. Locate the "Total observations" count displayed on the Samples page (usually in the page header or near the top of the results)
8. Compare this number with the number written down in step 4

**Expected Result:**
- A new browser tab opens at a URL starting with `http://localhost:3255/research/samples`
- The Samples page loads successfully (no error page, no blank screen)
- The "Total observations" number on the Samples page exactly matches the N= number written down in step 4
- The cohort description on the Samples page references the "Bear" phase and the 20-day horizon (not a generic or wrong cohort label)

---

### UT-09 — Samples page cohort header identifies Regime Lab drill-downs correctly (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/samples` (cohort header for Regime Lab drill)

**Preconditions:**
- Frontend is running at http://localhost:3255
- Regime Lab page has data loaded (`/research/regime-lab`)

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-lab`
2. Wait for the Regime Lab page to fully load (tables visible)
3. Locate any N= chip in the Regime Lab tables (pick one with a numeric value, e.g., "N=120")
4. Ctrl+click (Cmd+click on Mac) the N= chip to open it in a new tab
5. Switch to the new tab and wait for `/research/samples` to load
6. Read the cohort heading or filter description shown at the top of the Samples page

**Expected Result:**
- The Samples page cohort heading identifies the cohort as originating from the "Regime Lab" (exact text may vary but must NOT say "Setup & Pattern Lab")
- The observation count matches the N= value that was clicked
- The page does not show a generic or wrong lab label in the cohort description

---

### UT-10 — Existing Research hub lab tiles still navigate to their respective pages (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/research`
2. Wait for the Research hub to fully load
3. Locate the "Regime Lab" tile (it was present before iter-54)
4. Click the "Regime Lab" tile
5. Wait for the page to load
6. Navigate back to `http://localhost:3255/research`
7. Locate any other pre-existing lab tile (e.g., "Factor Lab" or "Setup & Pattern Lab") and click it
8. Wait for the page to load

**Expected Result:**
- Clicking the "Regime Lab" tile navigates to `/research/regime-lab` — page heading includes "Regime Lab" text and the page loads without error
- Clicking the second pre-existing tile navigates to its correct route (not `/research/phase-severity-lab`) — page heading matches the tile label
- The Research hub still shows all pre-existing tiles alongside the new "Market Phase & Severity Lab" tile (no tiles removed or repositioned causing confusion)

---

### UT-11 — Phase & Severity Lab page shows error/unavailable state when backend is down (error)

**Type:** error
**Priority:** P2
**Surface:** `/research/phase-severity-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is either stopped or the API endpoint is unreachable (simulate by navigating while backend is down, or by blocking the network request in developer tools)

**Steps:**
1. Stop the backend service (or in browser developer tools, open the Network tab, right-click the API request pattern and select "Block request URL" for `/api/research/phase-severity-lab`)
2. Navigate to `http://localhost:3255/research/phase-severity-lab`
3. Wait for the page to attempt to load data

**Expected Result:**
- The page does NOT show a blank white screen or an unhandled JS exception
- A visible error or unavailable state is displayed (e.g., "Backend unavailable", "Unable to load data", or a spinner that eventually transitions to an error message)
- The page heading "Market Phase & Severity Lab" remains visible even in the error state
- The user is not shown raw stack trace text or a Next.js error overlay in a production-like environment

---

### UT-12 — NA cells display the text "NA" and never show blank or fabricated values (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research/phase-severity-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend has data; some buckets are expected to have thin or zero observation counts (typical near the latest date at long horizons)

**Steps:**
1. Navigate to `http://localhost:3255/research/phase-severity-lab`
2. Wait for both tables to fully load
3. Scan the rightmost horizon column (the 60-day horizon) across all rows in the by-phase-label table
4. Identify at least one cell that shows "NA" (thin data for recent dates at long horizons is expected here)
5. Confirm the text in that cell is exactly "NA" (not blank, not "–", not "0", not "null", not "undefined")
6. Repeat for the by-decile table at the 60-day horizon if any "NA" cells are present

**Expected Result:**
- Cells with insufficient data show exactly the text "NA"
- No cell shows a blank space, a dash character only, the string "null", the string "undefined", or the number "0" where the displayed convention for missing data is "NA"

---

### UT-13 — Phase & Severity Lab is discoverable from the Research hub within 2 clicks (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research` navigation

**Steps:**
1. Navigate to `http://localhost:3255/research` (this is 1 click or 1 navigation from anywhere in the app)
2. Without scrolling excessively, verify the "Market Phase & Severity Lab" tile is visible in the labs section of the page
3. Click the tile (this is the 2nd click)

**Expected Result:**
- The "Market Phase & Severity Lab" tile is visible on the `/research` hub without requiring the user to scroll past many unrelated tiles
- Clicking the tile immediately navigates to `/research/phase-severity-lab`
- The tile label "Market Phase & Severity Lab" clearly describes what the page contains (not a cryptic abbreviation)
- The Thermometer icon alongside the label provides a visual cue distinct from other lab tiles

---

### UT-14 — Survivorship-bias caveat is visible and legible on the page header (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research/phase-severity-lab`

**Steps:**
1. Navigate to `http://localhost:3255/research/phase-severity-lab`
2. Wait for the page to fully load
3. Read the text in the page header area (above or near the tables)

**Expected Result:**
- A caveat statement is visible that warns the user about survivorship bias or the descriptive/non-predictive nature of the data (e.g., text containing "survivorship" or "descriptive evidence" or "not forward-looking")
- The caveat is rendered in a legible font size and colour (not invisible due to low contrast against background)
- The caveat does not obstruct the tables or require the user to dismiss it to use the page

---

### UT-15 — Colour grading on return/MDD cells is visually distinct between positive and negative values (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/research/phase-severity-lab`

**Steps:**
1. Navigate to `http://localhost:3255/research/phase-severity-lab`
2. Wait for both tables to fully load
3. Locate a cell showing a positive forward-return value (e.g., "+3.2%") in the by-phase-label table
4. Locate a cell showing a negative forward-return value (e.g., "–4.1%") in the same table
5. Compare the background colour or text colour of the two cells

**Expected Result:**
- The positive return cell has a visually different colour from the negative return cell (e.g., green-tinted vs red-tinted background)
- Cells showing "NA" have a neutral colour (neither green nor red), distinct from both positive and negative cells
- The colour grading is consistent across both the by-phase-label table and the by-decile table

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Research hub loads with new Phase & Severity Lab tile | smoke | P1 | `/research` |
| UT-02 | Phase & Severity Lab page loads without errors | smoke | P1 | `/research/phase-severity-lab` |
| UT-03 | Navigate from Research hub to Phase & Severity Lab via tile | happy-path | P1 | `/research` → `/research/phase-severity-lab` |
| UT-04 | By-phase-label table renders five phase rows with paired columns | happy-path | P1 | `/research/phase-severity-lab` |
| UT-05 | By-decile table renders Rank-IC row plus D1–D10 rows with score ranges | happy-path | P1 | `/research/phase-severity-lab` |
| UT-06 | Column sort reorders rows and keeps NA cells at the bottom | happy-path | P1 | `/research/phase-severity-lab` |
| UT-07 | As-of filter reduces observation counts and adds no second date control | happy-path | P1 | `/research/phase-severity-lab` |
| UT-08 | N= chip opens matching Samples cohort in new tab with count-coherent total | happy-path | P1 | `/research/phase-severity-lab` → `/research/samples` |
| UT-09 | Samples page cohort header identifies Regime Lab drill-downs correctly | regression | P1 | `/research/samples` |
| UT-10 | Existing Research hub lab tiles still navigate to their respective pages | regression | P1 | `/research` |
| UT-11 | Phase & Severity Lab page shows error/unavailable state when backend is down | error | P2 | `/research/phase-severity-lab` |
| UT-12 | NA cells display the text "NA" and never show blank or fabricated values | validation | P2 | `/research/phase-severity-lab` |
| UT-13 | Phase & Severity Lab is discoverable from the Research hub within 2 clicks | ux | P2 | `/research` |
| UT-14 | Survivorship-bias caveat is visible and legible on the page header | ux | P2 | `/research/phase-severity-lab` |
| UT-15 | Colour grading on return/MDD cells is visually distinct | ux | P3 | `/research/phase-severity-lab` |

**P1 tests must all pass for browser QA verdict to be PASS.**
