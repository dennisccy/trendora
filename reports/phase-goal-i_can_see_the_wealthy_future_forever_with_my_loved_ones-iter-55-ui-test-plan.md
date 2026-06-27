# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-55 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-55
**Date:** 2026-06-27
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->
<!-- Vague steps like "test the form" or "verify it works" are not acceptable. -->
<!-- API-only tests (TC-16 through TC-21 in the functional test plan) are not duplicated here. -->

---

### UT-01 — Research hub page loads with new Regime × Phase × Factor tile visible (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8255

**Steps:**
1. Navigate to `http://localhost:3255/research`
2. Wait for the page to fully load (check that the LABS section heading is visible)
3. Scan the LABS tile grid for a tile labelled "Regime × Phase × Factor"
4. Confirm the tile displays a Boxes icon (grid-of-squares icon, distinct from the icons on the Regime Lab and Phase & Severity Lab tiles)

**Expected Result:**
- The page renders without a blank screen, "Backend unavailable" skeleton, or error message
- A tile labelled "Regime × Phase × Factor" is visible in the LABS section alongside the existing research tiles
- The tile carries a Boxes icon that is visually distinct from the icons on sibling tiles
- The tile displays a one-line description beneath the title

---

### UT-02 — Clicking the hub tile navigates to the new lab page (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → `/research/regime-phase-factor`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The Research hub page at `/research` is loaded and the "Regime × Phase × Factor" tile is visible (see UT-01)

**Steps:**
1. Navigate to `http://localhost:3255/research`
2. Click the tile labelled "Regime × Phase × Factor" in the LABS section
3. Wait for the browser to navigate

**Expected Result:**
- The browser URL changes to `http://localhost:3255/research/regime-phase-factor`
- The page renders (no 404 page, no "Backend unavailable" skeleton, no blank screen)
- A page heading that includes "Regime" and "Factor" (e.g. "Regime × Phase × Factor") is visible at the top of the page

---

### UT-03 — New lab page shell loads with all required controls present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/regime-phase-factor`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8255
- The database contains at least one completed scanner run with forward-return data

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-phase-factor`
2. Wait for the page to finish loading (loading skeleton or spinner disappears)
3. Check for the presence of each of the following controls in order:
   a. A factor selector (dropdown or `<select>` component at the top of the page)
   b. An As-of / All-history toggle (labelled or visually distinct toggle control)
   c. A combination table with at least one data row
   d. A pagination footer with a "Previous" and a "Next" button at the bottom of the table
4. Confirm the page does NOT show an "error" or "could not load" message as the final state

**Expected Result:**
- Factor selector is present and shows a pre-selected default factor
- As-of / All-history toggle is present
- The combination table is rendered with at least one row (not empty)
- Pagination footer with Previous and Next controls is visible below the table
- No runtime error or "Backend unavailable" message is shown as the steady-state view

---

### UT-04 — Regime × Phase × Factor tile is discoverable within two clicks from the Research nav entry (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255` (Dashboard home page)
2. Click the "Research" link in the left-hand navigation sidebar (or wherever the Research nav entry appears)
3. Confirm you arrive at `http://localhost:3255/research`
4. Locate the "Regime × Phase × Factor" tile in the page without scrolling past more than one screenful
5. Click the tile

**Expected Result:**
- Clicking "Research" in the nav lands on the hub at `/research`
- The "Regime × Phase × Factor" tile is visible within the LABS section without requiring more than one screenful of scrolling
- Clicking the tile navigates to `/research/regime-phase-factor` — the full lab page loads
- The two-click journey (Research nav → tile click) is self-explanatory; no developer knowledge is required

---

### UT-05 — Factor selector changes the combination table rows (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/regime-phase-factor`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8255
- The lab page at `/research/regime-phase-factor` is loaded and the combination table shows rows (not empty)

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-phase-factor`
2. Wait for the table to load with rows
3. Note the factor label currently shown in the factor selector (e.g. "leadership_score")
4. Note the n value shown in the first visible table row
5. Click the factor selector to open the dropdown
6. Confirm the dropdown lists at least 3 distinct factor names
7. Select a factor that is different from the current selection (e.g. "entry_quality_score")
8. Wait for the table to re-render

**Expected Result:**
- The dropdown lists at least 3 factors
- After selecting the new factor, the table re-renders
- The n values in the first visible row are different from the values noted in step 4 (the table content has changed)
- No error message or "Backend unavailable" skeleton appears after the factor switch

---

### UT-06 — Combination table shows correct column structure (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/regime-phase-factor`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The lab page is loaded and the combination table is rendering rows (see UT-03)

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-phase-factor`
2. Wait for the table to load
3. Examine the leftmost three columns of the table header:
   - Confirm the first column header refers to regime score decile (e.g. "Regime D", "Regime Decile", or similar)
   - Confirm the second column header refers to severity (phase) decile (e.g. "Severity D", "Phase Decile", or similar)
   - Confirm the third column header refers to factor decile (e.g. "Factor D", "Factor Decile", or similar)
4. Confirm the table has at least five further columns grouped by horizon, labelled with time periods such as "1d", "5d", "10d", "20d", and "60d"
5. Within each horizon group, confirm both a forward-return column and a max-drawdown column are present
6. Confirm an "n" (sample count) value column is visible for at least one horizon group
7. Scroll the table horizontally if needed to confirm all five horizon groups are accessible

**Expected Result:**
- The first three table columns clearly identify the three decile dimensions (regime, severity, factor)
- Forward-return and max-drawdown columns appear for every horizon (1d, 5d, 10d, 20d, 60d)
- An n (sample count) is visible on each combination row
- The table is horizontally scrollable if columns extend beyond the viewport

---

### UT-07 — Regime decile filter narrows visible rows to the selected decile (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/regime-phase-factor`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The lab page is loaded and the combination table shows rows with multiple distinct regime-score decile values

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-phase-factor`
2. Wait for the table to load
3. Locate the regime decile filter control (labelled "Regime Decile", "Regime D", or similar); confirm it defaults to "All"
4. Note the total number of rows currently visible in the table
5. Select decile "D10" (or "10") from the regime decile filter
6. Observe the table rows after filtering
7. Confirm that every visible row shows "D10" (or equivalent) in the regime-decile column
8. Confirm that rows showing any other regime decile value are no longer visible
9. Select "All" from the regime decile filter to restore the full row set
10. Confirm the number of visible rows returns to approximately the count noted in step 4

**Expected Result:**
- Selecting "D10" in the regime decile filter removes all rows with a regime-decile other than D10
- Only D10 regime rows remain visible
- Selecting "All" restores all rows
- No network/API request is triggered by the filter change (the filter is a pure client-side view transform)

---

### UT-08 — Severity decile filter narrows visible rows to the selected decile (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/regime-phase-factor`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The lab page is loaded and the combination table shows rows with multiple distinct severity-decile values

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-phase-factor`
2. Wait for the table to load
3. Locate the severity decile filter control (labelled "Severity Decile", "Phase Decile", or similar); confirm it defaults to "All"
4. Select "D3" (or "3") from the severity decile filter
5. Observe the table rows
6. Confirm that every visible row shows "D3" in the severity-decile column
7. Confirm rows with other severity decile values are no longer visible
8. Select "All" to restore the full row set

**Expected Result:**
- Selecting "D3" removes rows with any other severity-decile value
- Only D3 severity rows remain visible
- Selecting "All" restores all rows
- The filter is a client-side view transform; no loading spinner triggered

---

### UT-09 — Factor decile filter narrows visible rows to the selected decile (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/regime-phase-factor`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The lab page is loaded and the combination table shows rows with multiple distinct factor-decile values

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-phase-factor`
2. Wait for the table to load
3. Locate the factor decile filter control (labelled "Factor Decile" or similar); confirm it defaults to "All"
4. Select "D8" (or "8") from the factor decile filter
5. Observe the table rows
6. Confirm every visible row shows "D8" in the factor-decile column
7. Confirm rows with other factor decile values are no longer visible
8. Select "All" to restore the full row set

**Expected Result:**
- Selecting "D8" removes rows with any other factor-decile value
- Only D8 factor rows remain visible
- Selecting "All" restores all rows

---

### UT-10 — Column sort reorders rows with NA values sinking to bottom in both directions (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/regime-phase-factor`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The lab page is loaded and the combination table shows rows with a mix of numeric return values and "NA" cells

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-phase-factor`
2. Wait for the table to load and confirm at least one row shows an "NA" value in a return or MDD column
3. Note the order of the first five visible rows (e.g. write down the regime/severity/factor decile labels)
4. Click the sort-header button for the "1d forward return" column (or the first return column)
5. Observe the row order after the click
6. Confirm the rows have reordered (the order is different from step 3)
7. Confirm every "NA" value row appears at the BOTTOM of the visible page, below all rows that have numeric values in that column
8. Click the same sort-header button again (reverse sort)
9. Confirm the rows reorder again (reversed direction)
10. Confirm "NA" rows still appear at the BOTTOM, not at the top

**Expected Result:**
- First sort click reorders the rows in ascending or descending order
- NA cells (below min-sample combinations) always sink to the bottom regardless of sort direction
- Second click reverses sort direction and NA cells remain at the bottom
- No error or blank table appears after either click

---

### UT-11 — Pagination shows 30 rows per page; next and previous buttons navigate correctly (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/regime-phase-factor`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The lab page is loaded with the default factor selected and no decile filters applied
- The total combination count for the default factor exceeds 30 rows (confirmed by seeing a "Next" button that is not disabled)

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-phase-factor`
2. Wait for the table to load
3. Count the visible rows on the current page
4. Confirm the count is exactly 30 (or all rows if fewer than 30 exist in total)
5. Confirm the pagination footer shows a page indicator (e.g. "Page 1 of N" or "1–30")
6. Click the "Next" button in the pagination footer
7. Wait for the table to re-render
8. Count the visible rows on the new page
9. Confirm the rows displayed are DIFFERENT from page 1 (the row content has changed — regime/severity/factor decile labels differ)
10. Click the "Previous" button in the pagination footer
11. Confirm the original 30 rows from page 1 reappear

**Expected Result:**
- Page 1 shows exactly 30 rows (or all rows if total < 30)
- Clicking "Next" shows the next set of rows (different content from page 1)
- Clicking "Previous" returns to page 1 with the original rows
- No network request is triggered by pagination (it is a pure client-side view transform)

---

### UT-12 — As-of toggle causes n values to decrease compared to All-history view (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/regime-phase-factor`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8255
- The database contains historical forward-return data spanning multiple dates (the observation set has history before 2024-06-01)
- The lab page is loaded in the default All-history view

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-phase-factor`
2. Wait for the table to load in the All-history view
3. Note the n values shown for the first 3 visible rows (e.g. write down each row's n column value)
4. Locate the As-of / All-history toggle control and confirm it is currently in the "All-history" position
5. Click the toggle to switch to the "As-of" (historical date) mode
6. If a date appears, confirm only a single date control is shown (no second date selector)
7. Wait for the table to re-render with the historical date applied (use 2024-06-01 as the test date if the toggle allows choosing)
8. Compare the n values for the same rows noted in step 3
9. Confirm the n values have DECREASED compared to the All-history view
10. Click the toggle again to switch back to the "All-history" mode
11. Confirm the n values return to their original counts from step 3

**Expected Result:**
- Switching to As-of mode triggers an API request and re-renders the table with reduced n values
- At least one of the 3 noted rows shows a lower n value than in the All-history view
- Switching back to All-history restores the original n values
- Only one date control exists on the page at all times (no second date input visible)

---

### UT-13 — No native date input element exists on the page (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research/regime-phase-factor`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The lab page is loaded in both the default state and with the As-of toggle enabled

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-phase-factor`
2. Wait for the page to fully load
3. Open browser developer tools (F12) and switch to the Console tab
4. Type the following into the console and press Enter:
   `document.querySelectorAll('input[type="date"]').length`
5. Read the returned number
6. Click the As-of / All-history toggle to enable the As-of mode
7. Run the same console check again:
   `document.querySelectorAll('input[type="date"]').length`

**Expected Result:**
- In step 5, the console returns `0` — no native date inputs exist on the page in the default state
- In step 7, the console still returns `0` — enabling As-of mode does not add a native date `<input type="date">` element
- The As-of control uses a toggle switch or dropdown, NOT a text-input date field

---

### UT-14 — No Episodes/Pooled toggle exists on the page (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research/regime-phase-factor`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The lab page is loaded

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-phase-factor`
2. Wait for the page to fully load
3. Visually scan the entire page — controls bar, table header area, and pagination footer — for any toggle, tab, or selector labelled "Episodes", "Pooled", "View: Episodes", or "View: Pooled"
4. Confirm no such control is present

**Expected Result:**
- No Episodes / Pooled toggle or selector is visible anywhere on the page
- The page does not expose a mechanism to switch between Episodes and Pooled view modes
- The table renders data without any view-mode selector

---

### UT-15 — N= chip opens Research Samples page in a new tab with a matching observation count (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/regime-phase-factor` → `/research/samples`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8255
- The lab page is loaded and the combination table shows at least one row with a non-zero n value

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-phase-factor`
2. Wait for the table to load
3. Locate a row that shows a numeric n value (not "NA" or "0") in the 1-day horizon column
4. Note the exact number shown in that chip (e.g. "N=42")
5. Also note the regime-decile, severity-decile, and factor-decile values for that row
6. Middle-click (or Ctrl+click / Cmd+click) the N= chip to open it in a new tab
7. Switch to the newly opened tab
8. Wait for the page to load at `/research/samples`
9. Read the "Total observations" count displayed on the Samples page

**Expected Result:**
- A new tab opens at a URL starting with `http://localhost:3255/research/samples`
- The URL contains query parameters for regime_decile, severity_decile, factor_decile, and horizon matching the row from step 5
- The "Total observations" count on the Samples page exactly matches the n value noted in step 4 (e.g. the page shows "42" total observations if the chip read "N=42")
- No 4xx or error page is shown

---

### UT-16 — Survivorship-bias / descriptive-evidence banner is visible on the page (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research/regime-phase-factor`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The lab page is loaded

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-phase-factor`
2. Wait for the page to fully load
3. Scan the page — both above and below the combination table — for any text containing:
   - "survivorship" or "survivorship bias"
   - or "descriptive evidence"
   - or "current-membership universe"
4. Confirm such text is visible without needing to interact with any control

**Expected Result:**
- A caution banner or disclaimer label containing "survivorship" (and "bias") or "descriptive evidence" is visible on the page
- The banner is visible in the default page state without any extra user action
- The disclaimer is styled similarly to the caution banners on the sibling labs (Regime Lab, Phase & Severity Lab)

---

### UT-17 — Arriving via N= chip drill-down shows a human-readable cohort description in Research Samples (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/samples`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8255
- The user has performed UT-15 and a new tab is open at `/research/samples` with the regime-phase-factor cohort parameters

**Steps:**
1. After completing UT-15, on the newly opened `/research/samples` tab, scroll to the top of the page
2. Locate the cohort description section (visible near the top of the samples view, above the sample rows or table)
3. Confirm the description includes the following specific values:
   - The regime decile (e.g. "Regime Decile 10" or "D10")
   - The severity decile (e.g. "Severity Decile 3" or "D3")
   - The factor decile (e.g. "Factor Decile 8" or "D8")
   - The horizon (e.g. "1-day", "5-day", or similar)
4. Confirm the cohort description does NOT show an unrecognised or generic label like "Unknown cohort" or an empty string

**Expected Result:**
- The Research Samples page shows a human-readable cohort description naming the regime decile, severity decile, factor decile, and horizon from the N= chip that was clicked
- The description is clearly laid out and reads as plain language (e.g. "Regime Decile 10 × Severity Decile 3 × Factor Decile 8 — 1-day horizon")
- No "Unknown cohort" or empty cohort label is shown

---

### UT-18 — Research hub still shows all prior tiles unchanged (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/research`
2. Wait for the page to load
3. Confirm the following tiles are all still present in the LABS section:
   - "Regime Lab" tile (with its original icon)
   - "Phase & Severity Lab" tile (with its original icon)
4. Confirm each existing tile still shows its original one-line description
5. Click the "Regime Lab" tile
6. Confirm the browser navigates to `/research/regime-lab` and the page renders with a table (not blank, not error)
7. Navigate back to `http://localhost:3255/research`
8. Click the "Phase & Severity Lab" tile
9. Confirm the browser navigates to `/research/phase-severity-lab` and the page renders with a table

**Expected Result:**
- "Regime Lab" and "Phase & Severity Lab" tiles remain in the hub with their original icons and descriptions
- Both tiles navigate to the correct routes and those pages render real data tables
- The addition of the new "Regime × Phase × Factor" tile has not displaced or hidden any existing tile

---

### UT-19 — Regime Lab still renders with real data after the new lab was added (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/regime-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8255

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-lab`
2. Wait for the page to fully load
3. Confirm the page heading references "Regime" (e.g. "Regime Lab")
4. Confirm the table renders with at least one row showing a numeric regime score (not "NA" for every row)
5. Confirm no "Backend unavailable" or "could not load" message is the final page state

**Expected Result:**
- Regime Lab page loads without error
- The regime-score table renders with at least one row of real numeric values
- No regression in layout or data caused by the new Regime × Phase × Factor lab

---

### UT-20 — Phase & Severity Lab still renders with real data after the new lab was added (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/phase-severity-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8255

**Steps:**
1. Navigate to `http://localhost:3255/research/phase-severity-lab`
2. Wait for the page to fully load
3. Confirm the page heading references "Phase" or "Severity" (e.g. "Phase & Severity Lab")
4. Confirm the table renders with at least one row showing numeric severity values (not "NA" for every row)
5. Confirm no "Backend unavailable" or "could not load" message is the final page state

**Expected Result:**
- Phase & Severity Lab page loads without error
- The table renders with at least one row of real numeric severity figures
- No regression in layout or data caused by the new Regime × Phase × Factor lab

---

### UT-21 — Research Samples page still loads correctly when accessed directly (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/samples`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/research/samples` directly (without any query parameters)
2. Wait for the page to load
3. Confirm the page renders without a crash or blank screen
4. Confirm the page does not show an unhandled exception or "undefined is not an object" error

**Expected Result:**
- Research Samples page renders with a valid empty or default cohort state (not a crash)
- The new regime-phase-factor `describeCohort` branch has not broken the page when no cohort params are present

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Research hub page loads with new tile visible | smoke | P1 | `/research` |
| UT-02 | Clicking the hub tile navigates to the new lab page | happy-path | P1 | `/research` |
| UT-03 | New lab page shell loads with all controls present | smoke | P1 | `/research/regime-phase-factor` |
| UT-04 | Tile is discoverable within two clicks from Research nav | ux | P2 | `/research` |
| UT-05 | Factor selector changes the combination table rows | happy-path | P1 | `/research/regime-phase-factor` |
| UT-06 | Combination table shows correct column structure | smoke | P1 | `/research/regime-phase-factor` |
| UT-07 | Regime decile filter narrows visible rows | happy-path | P1 | `/research/regime-phase-factor` |
| UT-08 | Severity decile filter narrows visible rows | happy-path | P1 | `/research/regime-phase-factor` |
| UT-09 | Factor decile filter narrows visible rows | happy-path | P1 | `/research/regime-phase-factor` |
| UT-10 | Column sort reorders rows with NA sinking to bottom | happy-path | P1 | `/research/regime-phase-factor` |
| UT-11 | Pagination shows 30 rows/page with working next/previous | happy-path | P1 | `/research/regime-phase-factor` |
| UT-12 | As-of toggle reduces n values vs All-history view | happy-path | P1 | `/research/regime-phase-factor` |
| UT-13 | No native date input exists on the page | ux | P2 | `/research/regime-phase-factor` |
| UT-14 | No Episodes/Pooled toggle exists on the page | ux | P2 | `/research/regime-phase-factor` |
| UT-15 | N= chip opens Research Samples with matching count | happy-path | P1 | `/research/regime-phase-factor` |
| UT-16 | Survivorship-bias banner is visible on the page | ux | P2 | `/research/regime-phase-factor` |
| UT-17 | Arriving via N= chip shows cohort description in Samples | happy-path | P1 | `/research/samples` |
| UT-18 | Research hub still shows all prior tiles unchanged | regression | P1 | `/research` |
| UT-19 | Regime Lab still renders with real data | regression | P1 | `/research/regime-lab` |
| UT-20 | Phase & Severity Lab still renders with real data | regression | P1 | `/research/phase-severity-lab` |
| UT-21 | Research Samples page still loads without crash | regression | P1 | `/research/samples` |

**P1 tests must all pass for browser QA verdict to be PASS.**
