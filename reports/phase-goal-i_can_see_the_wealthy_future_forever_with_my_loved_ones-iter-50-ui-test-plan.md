# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50
**Date:** 2026-06-26
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->
<!-- Vague steps like "test the form" or "verify it works" are not acceptable. -->

---

### UT-01 — Factor Lab page loads with all-factors table visible (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and has completed at least one warm-up (data is loaded)

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait up to 120 seconds for the page to finish loading (first cold load can take ~25 s on the backend)
3. Look at the page content

**Expected Result:**
- Page renders without a blank white screen or a red error panel
- A table is visible with multiple rows (at least 3), each showing data in columns for factor name, family, Rank-IC, N, and a risk-adjusted figure
- The page title or heading contains the text "Factor Lab"
- No dropdown/select element for choosing a single factor is visible on the page

---

### UT-02 — All-factors table shows one row per catalog factor with all required columns (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and has completed at least one warm-up so the all-factors table is populated

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the table to finish loading (skeleton/spinner disappears and rows are visible)
3. Count the number of rows in the table
4. Inspect the column headers of the table
5. Look at the first data row and read the values across each column

**Expected Result:**
- The table has at least 3 rows (one per catalog factor)
- Column headers visible include: "Factor" (or factor name/label), "Family", "Rank-IC", "N", and a risk-adjusted figure column (e.g., "Risk-adjusted" or "Downside adj.")
- Each row shows a non-empty factor label, a family label, a numeric Rank-IC value or "NA", a sample count (N) or 0, and a numeric or "NA" risk-adjusted figure
- No single-factor body text (e.g., "Select a factor to view…") is visible anywhere on the page

---

### UT-03 — Clicking a column header sorts the table by that column ascending (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab` — `FactorSortHeader`

**Preconditions:**
- The all-factors table is visible with at least 3 rows of data (UT-01 passes)

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab` and wait for the table to load
2. Look at the first column header labeled "Rank-IC" (or "Rank IC")
3. Note the order of the first three factor rows (write down or remember the factor labels in positions 1, 2, 3)
4. Click the "Rank-IC" column header once
5. Wait 1 second for the table to reorder
6. Look at the order of the first three factor rows again

**Expected Result:**
- After clicking "Rank-IC", the factor rows are reordered
- The factor that had the highest Rank-IC value is now at or near the top of the list
- The order in positions 1, 2, 3 is different from what was noted before clicking
- Rows whose Rank-IC is "NA" (due to zero observations or low sample count) are at the bottom of the sorted list, not intermixed with the numeric values

---

### UT-04 — Clicking the same column header a second time reverses the sort, NA rows remain at the bottom (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab` — `FactorSortHeader`

**Preconditions:**
- The all-factors table is sorted by Rank-IC ascending (UT-03 passed)
- At least one row shows "NA" in the Rank-IC column

**Steps:**
1. With the table already sorted by Rank-IC ascending (from UT-03), note the factor in row 1 (the highest Rank-IC)
2. Click the "Rank-IC" column header a second time
3. Wait 1 second for the table to reorder
4. Look at the factor now in row 1
5. Scroll to the bottom of the table and look at the last visible rows

**Expected Result:**
- The factor that was previously at position 1 (highest Rank-IC) is now near the bottom of the numeric rows
- The factor that was previously at the bottom of the numeric rows (lowest Rank-IC) is now at position 1
- Any rows that show "NA" in the Rank-IC column are still at the very bottom of the table (after all numeric rows), regardless of the sort direction

---

### UT-05 — Clicking a factor row expands it to reveal the D1–D10 decile panel (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab` — expand/collapse rows + `DecileTable`

**Preconditions:**
- The all-factors table is visible with at least 1 factor row (UT-01 passes)

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab` and wait for the table to load
2. Locate the first factor row in the table (the top-most data row)
3. Click anywhere on that factor row (or on its expand arrow/chevron if visible)
4. Wait up to 2 seconds for the expansion animation to complete
5. Look below the clicked row for a new panel that has appeared

**Expected Result:**
- A full-width panel (spanning the table width) appears directly below the clicked factor row
- Inside the panel, a decile table is visible with 10 rows labeled D1 through D10
- Each decile row shows: a decile label (e.g., "D1", "D2"), a mean return value, a risk-adjusted figure, an N count, and optionally a low-sample indicator
- The clicked row itself shows a visual indicator that it is expanded (e.g., an arrow pointing down, or a highlighted state)
- The rest of the factor rows above and below the expanded row remain visible and unchanged

---

### UT-06 — Clicking an expanded factor row collapses the decile panel (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab` — expand/collapse rows

**Preconditions:**
- A factor row is currently expanded and its decile panel (D1–D10) is visible (UT-05 passed)

**Steps:**
1. With the decile panel visible below the expanded row, click the same factor row a second time
2. Wait up to 2 seconds for the collapse animation to complete
3. Look at the location where the decile panel previously appeared

**Expected Result:**
- The decile panel (D1–D10 breakdown) is no longer visible
- The clicked factor row returns to its normal compact height with no expanded indicator
- The table looks the same as it did before the row was expanded in UT-05
- No other rows shifted or disappeared

---

### UT-07 — Decile N= chip opens Research Samples in a new browser tab with matching cohort count (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab` — `SampleLink` N= chips inside `DecileTable`

**Preconditions:**
- A factor row is expanded and its decile table is visible with at least one decile row whose N value is greater than 0

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab` and wait for the table to load
2. Click the first factor row to expand it
3. In the decile panel, locate the row labeled "D1" (first decile)
4. Find the "N=" chip or link in that D1 row (it shows the sample count, e.g., "N=145")
5. Note the number shown in the chip (e.g., 145)
6. Click the "N=" chip (or middle-click to open in a new tab)
7. Switch to the newly opened browser tab
8. Wait for the Research Samples page to load
9. Look at the total sample count shown on the Research Samples page
10. Look at the page URL

**Expected Result:**
- A new browser tab opens (the Factor Lab tab remains open and unchanged)
- The new tab shows a Research Samples page
- The total count of samples shown on the Research Samples page equals the N value noted in step 5 (e.g., 145)
- The URL of the new tab contains query parameters including `kind=factor`, the factor name, `slice=decile`, and the decile number (e.g., `decile=1`)

---

### UT-08 — Factor selector dropdown is absent from the Factor Lab page (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/factor-lab` — removed `FactorSelector`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the page to load completely (table is visible)
3. Scan the entire page — controls bar, page header, and table area — for any dropdown, select element, or combo box that allows choosing a single factor by name
4. Look specifically for an element labeled "Factor", "Select factor", "Choose a factor", or any similar label

**Expected Result:**
- No dropdown, select box, or combo box for selecting a single factor is present anywhere on the page
- The page shows only the controls bar (HorizonSelector + As-of toggle), the research caveat warning(s), and the all-factors table

---

### UT-09 — Single-factor body and RankIC card are absent from the Factor Lab page (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/factor-lab` — removed `FactorLab` single-factor body + `RankICCard`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the page to load completely
3. Look for a standalone Rank-IC card displayed at the top of the page body (a card with a single large Rank-IC percentage or value for one specific factor)
4. Look for a single-factor decile table rendered directly on the page body (outside any expandable row panel)
5. Scroll down to check the full page

**Expected Result:**
- No standalone Rank-IC card is visible at the page body level
- No single-factor decile table is rendered directly on the main page body (a decile table only appears inside an expanded row panel)
- The page body shows only the all-factors table as its main content

---

### UT-10 — Per-regime effectiveness table is absent from the Factor Lab page (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/factor-lab` — removed `RegimeEffectivenessTable`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the page to load completely
3. Scroll through the entire page from top to bottom
4. Look for any section or table labeled "Regime Effectiveness", "Per-Regime Breakdown", "Market Regime", "by_regime", or any table whose rows are labeled with market regime names (e.g., "Bull", "Bear", "Recovery", "Risk-Off")

**Expected Result:**
- No market-regime effectiveness table is visible anywhere on the page
- No regime-labelled rows or columns appear in the table or in any expanded panel
- Scrolling to the very bottom of the page shows no regime section

---

### UT-11 — Changing the horizon selector updates Rank-IC and risk-adjusted values in all rows simultaneously (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/factor-lab` — `HorizonSelector`

**Preconditions:**
- The all-factors table is visible with numeric Rank-IC and risk-adjusted values in at least 2 rows
- At least 2 distinct horizons are available in the horizon selector (e.g., "20d" and "60d")

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab` and wait for the table to load
2. Look at the controls bar at the top of the page; locate the horizon selector (a dropdown or set of buttons labeled with time periods such as "5d", "10d", "20d", "60d")
3. Note the current horizon selection and the Rank-IC value shown in the first two factor rows
4. Click the horizon selector and choose a different horizon (e.g., if currently "20d", click "60d")
5. Wait up to 30 seconds for the table to update (first load at a new horizon triggers a backend compute)
6. Look at the Rank-IC and risk-adjusted values in the same first two factor rows

**Expected Result:**
- The Rank-IC values and/or risk-adjusted figures in the table rows change after the horizon is switched
- Both factor rows you noted show updated values at the same time (not one at a time)
- The table structure (columns, row count) remains the same
- No page reload or navigation occurred — the same URL is shown in the browser address bar

---

### UT-12 — Toggling to As-of date mode changes N values across all rows (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/factor-lab` — As-of mode toggle

**Preconditions:**
- The all-factors table is visible with N values greater than 0 in at least 2 rows
- The As-of mode toggle is in "All history" state

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab` and wait for the table to load
2. Look at the controls bar; locate the "All history" / "As of date" toggle (a two-state button or tab)
3. Note the N value shown in the first two factor rows while in "All history" mode
4. Click the "As of date" toggle to switch to as-of mode
5. A date input or date picker should appear; enter a date that is approximately 1 year in the past from today (e.g., 2025-06-01) in the date field
6. Wait up to 30 seconds for the table to update
7. Look at the N values in the same first two factor rows

**Expected Result:**
- After switching to as-of mode with a historical date, the N values in the table rows decrease compared to the "All history" values noted in step 3
- Both factor rows show updated (smaller) N values at the same time
- Only one date input is visible in the controls bar (not two independent date selectors)
- The table structure (columns, row count) remains the same

---

### UT-13 — ResearchCaveat warnings are still visible on the page (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/research/factor-lab` — `ResearchCaveat`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the page to load completely
3. Scan the page above or below the all-factors table for any warning, disclaimer, or caveat text

**Expected Result:**
- At least one research caveat warning is visible on the page
- The caveat text mentions survivorship bias, descriptive nature of the research, or a similar disclaimer
- The warning is not hidden behind a collapsed section; it is visible without extra interaction

---

### UT-14 — Loading skeleton or WarmingState indicator displays before data arrives (error)

**Type:** error
**Priority:** P2
**Surface:** `/research/factor-lab` — `LabSkeleton` / `WarmingState`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The backend is running but the Factor Lab cache may need to cold-compute (first load after a backend restart)

**Steps:**
1. If possible, restart the backend to clear any warm cache, then immediately navigate to `http://localhost:3255/research/factor-lab`
2. Observe the page during the first 5–10 seconds before data arrives
3. Note whether a loading indicator, skeleton layout, or warming message is shown

**Expected Result:**
- During the loading period, the page shows either: a skeleton layout (placeholder grey bars in the table area), a "Warming" or "Computing" status message, or a spinner/loading indicator
- The page does NOT show a blank white screen or a fabricated table row with zero values during loading
- Once data arrives (up to ~120 seconds on cold load), the skeleton/warming state is replaced by the actual all-factors table

---

### UT-15 — Zero-N and low-sample factor rows display "NA" in value columns and appear at the table bottom after sorting (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research/factor-lab` — `FactorsTable` rows with NA values

**Preconditions:**
- The all-factors table is visible
- At least one factor row shows a zero N or low-sample indicator (visible as N=0 or a low-sample badge)

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab` and wait for the table to load
2. Scan the table rows for any row where the N column shows 0 or where a low-sample indicator is shown
3. For that row, look at the Rank-IC value column and the risk-adjusted figure column
4. Click the "Rank-IC" column header to sort by Rank-IC
5. Locate the zero-N or low-sample row in the sorted table

**Expected Result:**
- The zero-N or low-sample row shows "NA", "—", or a blank placeholder (not a numeric value) in the Rank-IC value column and the risk-adjusted figure column
- After sorting by Rank-IC, the zero-N / low-sample row appears at the bottom of the table — below all rows that have valid numeric Rank-IC values
- The N=0 or low-sample indicator is still visible in that row

---

### UT-16 — ResearchError panel shows when backend returns an error response (error)

**Type:** error
**Priority:** P2
**Surface:** `/research/factor-lab` — `ResearchError`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is stopped or returning an error (simulate by stopping the backend service or using a broken API URL)

**Steps:**
1. Stop the backend server (or simulate an unreachable backend)
2. Navigate to `http://localhost:3255/research/factor-lab`
3. Wait for the page to load (or time out waiting for data)
4. Observe what the page shows in the main content area

**Expected Result:**
- The page shows a `ResearchError` panel or error message in the main content area (not a blank page)
- The error message indicates that data could not be loaded (e.g., "Unable to load Factor Lab data", "Backend unavailable", or similar)
- The page does NOT show fabricated factor rows with zero or placeholder values
- The page controls bar (HorizonSelector, As-of toggle) may still be visible

---

### UT-17 — Factor Lab is reachable from the Research navigation within 2 clicks (ux)

**Type:** ux
**Priority:** P2
**Surface:** Navigation / Research menu

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255` (the app home / dashboard)
2. Look for a "Research" link or section in the navigation sidebar or top navigation bar
3. Click the "Research" navigation link
4. On the Research landing page or hub, look for a "Factor Lab" link or card
5. Click the "Factor Lab" link

**Expected Result:**
- Starting from the home page, the user reaches the Factor Lab page in at most 2 clicks
- The Factor Lab link or navigation item is clearly labeled "Factor Lab" (not abbreviated or hidden)
- After clicking, the browser navigates to `http://localhost:3255/research/factor-lab` and the all-factors table loads

---

### UT-18 — Page subtitle or section heading reflects the multi-factor scope (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/research/factor-lab` — page subtitle

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the page to load
3. Look at any subtitle, description text, or secondary heading below the "Factor Lab" title

**Expected Result:**
- A subtitle or description line reads "Which factors actually sort future returns" (or very close to this phrasing)
- The subtitle does NOT reference a single factor or say "Select a factor to begin"

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Factor Lab page loads with all-factors table visible | smoke | P1 | `/research/factor-lab` |
| UT-02 | All-factors table shows one row per catalog factor with all required columns | happy-path | P1 | `/research/factor-lab` |
| UT-03 | Clicking column header sorts table ascending | happy-path | P1 | `/research/factor-lab` |
| UT-04 | Second click on column header reverses sort, NA rows stay at bottom | happy-path | P1 | `/research/factor-lab` |
| UT-05 | Clicking factor row expands decile panel (D1–D10) | happy-path | P1 | `/research/factor-lab` |
| UT-06 | Clicking expanded factor row collapses decile panel | happy-path | P1 | `/research/factor-lab` |
| UT-07 | Decile N= chip opens Research Samples in new tab with matching count | happy-path | P1 | `/research/factor-lab` |
| UT-08 | Factor selector dropdown is absent | regression | P1 | `/research/factor-lab` |
| UT-09 | Single-factor body and RankIC card are absent | regression | P1 | `/research/factor-lab` |
| UT-10 | Per-regime effectiveness table is absent | regression | P1 | `/research/factor-lab` |
| UT-11 | Horizon selector updates all rows simultaneously | regression | P1 | `/research/factor-lab` |
| UT-12 | As-of mode toggle changes N values globally | regression | P1 | `/research/factor-lab` |
| UT-13 | ResearchCaveat warnings still visible | regression | P2 | `/research/factor-lab` |
| UT-14 | Loading skeleton / WarmingState shows before data arrives | error | P2 | `/research/factor-lab` |
| UT-15 | Zero-N and low-sample rows show NA and sort to bottom | validation | P2 | `/research/factor-lab` |
| UT-16 | ResearchError panel shows on backend failure | error | P2 | `/research/factor-lab` |
| UT-17 | Factor Lab reachable from Research navigation in 2 clicks | ux | P2 | navigation |
| UT-18 | Page subtitle reflects multi-factor scope | ux | P3 | `/research/factor-lab` |

**P1 tests must all pass for browser QA verdict to be PASS.**
