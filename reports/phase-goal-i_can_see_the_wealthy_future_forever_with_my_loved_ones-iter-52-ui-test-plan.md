# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52
**Date:** 2026-06-27
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Factor Lab page loads without blank screen or errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and reachable

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait up to 10 seconds for the page to fully load

**Expected Result:**
- The page heading "Factor Lab" (or equivalent) is visible in the page body
- An all-factors table is rendered with at least one factor row containing data
- No error banner reading "Backend unavailable", "Something went wrong", or similar is displayed
- The page is not blank or entirely white
- No unhandled JavaScript error dialog is shown

---

### UT-02 — Horizon dropdown is absent from the page (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Factor Lab page is fully loaded (UT-01 passes)

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Scan every visible region of the page — top bar, table controls area, sidebar, and above the table — for any dropdown, `<select>` element, or radio button group labelled "Horizon", "Select horizon", or presenting options such as "1d", "5d", "10d", "20d", "60d" as selectable choices

**Expected Result:**
- No dropdown, select control, or horizon-picker of any kind is present anywhere on the page
- No text such as "Select a horizon to view data" or "Horizon:" label exists
- The page does NOT show a prompt to select a horizon before displaying data

---

### UT-03 — All ten paired Fwd/MDD horizon columns appear in the all-factors table header (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- All-factors table is fully rendered (spinner has stopped, factor rows are visible)

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the all-factors table to fully render
3. Read each column header in the all-factors table header row from left to right

**Expected Result:**
- The header row contains a "Fwd 1d" column immediately followed by an "MDD 1d" column
- The header row contains a "Fwd 5d" column immediately followed by an "MDD 5d" column
- The header row contains a "Fwd 10d" column immediately followed by an "MDD 10d" column
- The header row contains a "Fwd 20d" column immediately followed by an "MDD 20d" column
- The header row contains a "Fwd 60d" column immediately followed by an "MDD 60d" column
- All 10 paired columns are present (5 forward-return columns and 5 max-drawdown columns)
- The table scrolls horizontally if columns extend beyond the visible viewport

---

### UT-04 — Rank-IC column header shows the fixed "(20d)" label (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- All-factors table is fully rendered

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Locate the "Rank-IC" column header in the all-factors table (typically near the right side of the table)
3. Read the full text of that column header

**Expected Result:**
- The Rank-IC column header reads "Rank-IC (20d)" or includes both "Rank-IC" and "20d" in its text
- The label is static text — no embedded dropdown or interactive control is inside the header cell
- Clicking any other column's sort header does NOT change the text of the Rank-IC column header

---

### UT-05 — Risk-adjusted column header shows the fixed "(20d)" label (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- All-factors table is fully rendered

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Locate the "Risk-adjusted" or "Risk-Adj" column header in the all-factors table
3. Read the full text of that column header

**Expected Result:**
- The header includes "(20d)" — for example "Risk-Adj (20d)" or "Risk-adjusted (20d)"
- The horizon shown matches the Rank-IC column header (both use 20d)
- The label is static text, not a selector

---

### UT-06 — Top-decile Fwd 20d cell displays a non-empty percentage value (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- All-factors table is fully rendered with at least one factor that has 20d forward-return data

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Locate the "Fwd 20d" column in the all-factors table
3. Look at the "Fwd 20d" cell in the first factor row (the topmost factor, e.g., MeanRev)

**Expected Result:**
- The cell displays a percentage value such as "+2.34%" or "-0.87%" — it is NOT blank, "NA", or a loading spinner
- If the value is positive, the text or cell is rendered in green
- If the value is negative, the text or cell is rendered in red
- A "N=" chip (sample count label) is visible inside or adjacent to the cell, showing a count such as "N=12,297"

---

### UT-07 — Top-decile MDD 20d cell displays a red-shaded negative percentage (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- All-factors table is fully rendered with at least one factor that has 20d max-drawdown data

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Locate the "MDD 20d" column in the all-factors table
3. Look at the "MDD 20d" cell in the first factor row

**Expected Result:**
- The cell displays a negative percentage value such as "-5.12%" (max-drawdown is always expressed as a negative number)
- The cell background or text colour is shaded in red — it is NOT grey, white, or green
- The cell does NOT display a positive value
- The cell is NOT blank or "NA"

---

### UT-08 — Clicking "Fwd 1d" column header sorts factors descending, NA rows last (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- All-factors table is rendered with at least two factor rows that have non-null 1d forward-return values

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Note the factor name in row 1 and row 2 of the all-factors table before sorting
3. Click the "Fwd 1d" column header
4. Wait for the table to reorder (no spinner should appear — sort is instant)
5. Observe the order of factor rows after the click
6. Look at the bottom of the table for any factor that shows "NA" or blank in the "Fwd 1d" column

**Expected Result:**
- The factor rows reorder so that the factor with the highest "Fwd 1d" percentage value appears in row 1
- Factors that show "NA" or a blank in the "Fwd 1d" column appear at the very bottom of the sorted table (below all numeric values)
- No "Loading…" spinner or network activity indicator appears during the sort — the reorder is instantaneous
- A sort direction indicator (arrow or similar icon) appears on the "Fwd 1d" column header

---

### UT-09 — Second click on "Fwd 1d" column header reverses sort order, NA rows still last (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- The all-factors table is already sorted descending by "Fwd 1d" (UT-08 has been completed)

**Steps:**
1. Click the "Fwd 1d" column header a second time
2. Observe the new order of factor rows

**Expected Result:**
- The factor rows reorder so that the factor with the lowest (most negative) "Fwd 1d" value appears in row 1
- Factors showing "NA" or blank in the "Fwd 1d" column still appear at the very bottom (after all numeric values, even the most negative)
- The sort direction indicator on the "Fwd 1d" column header flips (e.g., from a downward arrow to an upward arrow)
- No "Loading…" spinner appears

---

### UT-10 — Expanding a factor row reveals the D1–D10 decile grid with all-horizon paired columns (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- All-factors table is fully rendered; at least one factor row is visible

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Find the expand chevron (a triangle or ">" arrow icon) at the left edge of the first factor row in the table
3. Click the expand chevron on the first factor row
4. Wait up to 5 seconds for the decile sub-grid to render below that factor row

**Expected Result:**
- A sub-table (decile grid) appears directly below the first factor row, indented inside the table
- The sub-table contains exactly 10 rows labelled D1, D2, D3, D4, D5, D6, D7, D8, D9, and D10
- The sub-table columns include "Fwd 1d", "MDD 1d", "Fwd 5d", "MDD 5d", "Fwd 10d", "MDD 10d", "Fwd 20d", "MDD 20d", "Fwd 60d", "MDD 60d" — all ten paired columns across all five horizons
- Each decile row shows a "N=" chip on at least one forward-return cell

---

### UT-11 — N= chip in decile grid opens Samples page in a new tab with matching observation count (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab` → `/research/samples`

**Preconditions:**
- The decile grid is expanded for the first factor row (UT-10 passes)
- Backend is running and reachable

**Steps:**
1. In the expanded decile sub-grid, scroll down to locate the D5 row
2. Find the "Fwd 5d" cell in the D5 row
3. Read and note the exact N= chip value displayed in that cell (e.g., "N=4,512")
4. Click the N= chip

**Expected Result:**
- A new browser tab opens automatically
- The URL of the new tab includes query parameters that identify the factor name, horizon=5 (or 5d), and decile=5 (or D5)
- The new tab does NOT show a 404, 500, or any other error page
- The Samples page on the new tab shows a "Total observations" figure that exactly matches the N= chip value noted in step 3 (e.g., 4,512)
- The cohort description on the Samples page shows the correct factor name matching the factor you expanded

---

### UT-12 — Factor Lab shows an error banner when backend is unavailable (error)

**Type:** error
**Priority:** P2
**Surface:** `/research/factor-lab`

**Preconditions:**
- The backend service is temporarily stopped or unreachable (stop the backend process before this test)

**Steps:**
1. With the backend stopped, navigate to `http://localhost:3255/research/factor-lab`
2. Wait up to 10 seconds

**Expected Result:**
- The page renders an app shell (header and navigation are still visible)
- A visible error message is displayed — such as "Backend unavailable", "Failed to load factor data", or similar explanatory text
- The page is NOT entirely blank or a plain white screen
- No unhandled JavaScript error dialog is thrown

*After completing this test, restart the backend before proceeding to the next test.*

---

### UT-13 — D1 max-drawdown cell is shaded more intensely red than D10 in expanded decile grid (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research/factor-lab`

**Preconditions:**
- Decile grid is expanded for the first factor row (UT-10 passes)
- Both D1 and D10 rows have non-null "MDD 20d" values

**Steps:**
1. In the expanded decile sub-grid, locate the "MDD 20d" column
2. Look at the background colour of the "MDD 20d" cell in the D1 row (the topmost decile row, lowest-return decile)
3. Look at the background colour of the "MDD 20d" cell in the D10 row (the bottom decile row, highest-return decile)

**Expected Result:**
- The D1 "MDD 20d" cell has a visibly more intense (deeper, darker) red background than the D10 "MDD 20d" cell
- Both cells display negative percentage values (not blank or "NA")
- Neither cell is completely unstyled white

---

### UT-14 — "Factor range" column appears as one static column in the expanded decile grid (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research/factor-lab`

**Preconditions:**
- Decile grid is expanded for the first factor row (UT-10 passes)

**Steps:**
1. In the expanded decile sub-grid, scan the column headers from left to right
2. Count the number of columns labelled "Factor range" or "Factor Range"

**Expected Result:**
- Exactly one column labelled "Factor range" (or "Factor Range") exists in the decile sub-grid — it is not duplicated per horizon
- Each decile row (D1 through D10) shows a factor value range in that column (e.g., "0.02–0.15" or a similar range format)
- The column is visible without horizontal scrolling, or is accessible by scrolling

---

### UT-15 — Hovering a "Fwd Xd" cell in the decile grid shows a tooltip with that horizon's factor range (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research/factor-lab`

**Preconditions:**
- Decile grid is expanded for the first factor row (UT-10 passes)

**Steps:**
1. In the expanded decile sub-grid, move the mouse cursor over the "Fwd 5d" cell in the D5 row
2. Hold the cursor still for 1–2 seconds

**Expected Result:**
- A tooltip appears near the cursor position
- The tooltip text contains a factor value range specific to the 5d horizon (e.g., a numeric interval such as "0.03–0.12")
- Moving the cursor away from the cell causes the tooltip to disappear

---

### UT-16 — As-of/All-history toggle updates N= chips globally; no second date picker appears (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Factor Lab is fully loaded
- Decile grid is expanded for the first factor row (UT-10 passes)
- N= chip values are visible in the decile grid

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab` (or reload the page to start from a clean state)
2. Expand the first factor row to reveal its decile grid
3. Note the exact N= chip value in the D10 "Fwd 20d" cell (e.g., "N=12,297")
4. Locate the as-of date control in the top navigation bar (the single global date selector)
5. Click the global date control and switch to "All-history" mode or select an earlier date than the current as-of date
6. Wait for the Factor Lab table to reload with updated data
7. Look at the D10 "Fwd 20d" N= chip value in the (now reloaded) decile grid
8. Scan the entire Factor Lab page body for any date input, date picker, or date selector that is NOT in the top navigation bar

**Expected Result:**
- After switching the global date (step 5), the N= chip values in the decile grid change from the values noted in step 3 (in "All-history" mode the counts will typically be larger)
- No second date input or date picker appears anywhere inside the Factor Lab page body — the only date control on the page remains the one in the top navigation bar
- Data reloads without a full page refresh (the URL stays at `/research/factor-lab`)

---

### UT-17 — All catalog factors still appear in the all-factors table (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Factor Lab page fully loaded

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the all-factors table to finish loading (no spinner visible)
3. Count the visible factor rows in the table

**Expected Result:**
- At least 11 factor rows are visible in the table (the full catalog, including MeanRev, Seasonality, and other configured factors)
- No factor row displays a blank name or placeholder text such as "Loading…", "Factor 1", or "undefined"
- Every visible factor row contains at least one non-blank data value across its columns

---

### UT-18 — Factor Lab navigation link is reachable from the main app menu (ux)

**Type:** ux
**Priority:** P2
**Surface:** navigation

**Preconditions:**
- Frontend running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255` (the app home page or dashboard)
2. Look at the main navigation sidebar or top navigation menu
3. Locate a link labelled "Factor Lab" or a "Research" section containing a "Factor Lab" sub-link
4. Click the "Factor Lab" navigation link

**Expected Result:**
- A "Factor Lab" link (or "Research > Factor Lab") is visible in the navigation without any special interaction such as expanding a hidden submenu
- Clicking the link navigates to `http://localhost:3255/research/factor-lab`
- The Factor Lab page loads as described in UT-01

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Factor Lab loads without blank screen or errors | smoke | P1 | `/research/factor-lab` |
| UT-02 | Horizon dropdown is absent from the page | smoke | P1 | `/research/factor-lab` |
| UT-03 | All ten paired Fwd/MDD horizon columns in table header | smoke | P1 | `/research/factor-lab` |
| UT-04 | Rank-IC column shows fixed "(20d)" label | smoke | P1 | `/research/factor-lab` |
| UT-05 | Risk-adjusted column shows fixed "(20d)" label | smoke | P1 | `/research/factor-lab` |
| UT-06 | Top-decile Fwd 20d cell shows non-empty percentage value | happy-path | P1 | `/research/factor-lab` |
| UT-07 | Top-decile MDD 20d cell shows red-shaded negative percentage | happy-path | P1 | `/research/factor-lab` |
| UT-08 | "Fwd 1d" sort: factors reorder descending, NA rows last | happy-path | P1 | `/research/factor-lab` |
| UT-09 | Second click on "Fwd 1d": sort reverses, NA still last | happy-path | P1 | `/research/factor-lab` |
| UT-10 | Expand factor chevron: D1–D10 decile grid with all-horizon paired columns | happy-path | P1 | `/research/factor-lab` |
| UT-11 | N= chip in D5 "Fwd 5d" cell opens Samples page with matching count | happy-path | P1 | `/research/factor-lab` → `/research/samples` |
| UT-12 | Backend-unavailable shows error banner, not blank screen | error | P2 | `/research/factor-lab` |
| UT-13 | D1 MDD 20d cell shaded deeper red than D10 | ux | P2 | `/research/factor-lab` |
| UT-14 | "Factor range" column appears once in expanded decile grid | ux | P2 | `/research/factor-lab` |
| UT-15 | Hover on "Fwd 5d" cell shows tooltip with that horizon's factor range | ux | P2 | `/research/factor-lab` |
| UT-16 | As-of toggle updates N= chips globally; no second date picker | regression | P1 | `/research/factor-lab` |
| UT-17 | All catalog factors still appear in table after changes | regression | P1 | `/research/factor-lab` |
| UT-18 | Factor Lab navigation link reachable from main app menu | ux | P2 | navigation |

**P1 tests must all pass for browser QA verdict to be PASS.**
