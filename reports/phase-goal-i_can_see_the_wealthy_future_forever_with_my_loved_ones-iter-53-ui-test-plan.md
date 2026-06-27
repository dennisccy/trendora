# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-53 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-53
**Date:** 2026-06-27
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Research hub loads with Regime Lab tile (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and healthy

**Steps:**
1. Navigate to `http://localhost:3255/research`
2. Wait for the page to fully load (the LABS tile grid is visible)

**Expected Result:**
- Page renders with the heading "Research" (or equivalent hub title) visible
- The LABS tile grid is visible and populated
- A tile labelled "Regime Lab" is present in the tile grid
- The "Regime Lab" tile displays a Gauge icon
- No blank screen, spinner-only page, or error message appears

---

### UT-02 — Clicking the Regime Lab hub tile navigates to the correct page (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3255
- User is on the `/research` hub page with the LABS tile grid fully loaded

**Steps:**
1. Navigate to `http://localhost:3255/research`
2. Locate the tile labelled "Regime Lab" with a Gauge icon in the LABS tile grid
3. Click the "Regime Lab" tile

**Expected Result:**
- Browser navigates to `http://localhost:3255/research/regime-lab`
- The Regime Lab page begins loading (a loading skeleton or data tables appear)
- No 404 or "Page not found" error is shown

---

### UT-03 — Regime Lab page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/regime-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and healthy (responding to `/api/research/regime-lab`)

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-lab`
2. Wait until both tables are visible (no loading skeleton remains)

**Expected Result:**
- Page renders with a visible page title for the Regime Lab
- A descriptive subtitle or caveat text is visible below the title
- A "by-label" summary table is present on the page
- A "regime-score decile" table is present below the by-label table
- No "Backend unavailable" error card is shown
- No blank or white screen appears

---

### UT-04 — By-label table shows exactly 6 regime-label rows with correct column structure (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/regime-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- `/research/regime-lab` page is fully loaded with data (no loading skeleton)

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-lab`
2. Wait for both tables to finish loading
3. Locate the by-label summary table (the first of the two stacked tables)
4. Count the number of data rows in the by-label table (excluding any header rows)
5. Read the row labels to identify the regime names (e.g., "Risk-on", "Risk-off")
6. Inspect the column headers to confirm horizons 1d, 5d, 10d, 20d, and 60d are present
7. Inspect one data cell to confirm it contains either a numeric percentage value or the text "NA"

**Expected Result:**
- The by-label table has exactly 6 data rows (one per canonical regime label)
- Row labels include regime names such as "Risk-on" and "Risk-off" (six distinct labels visible)
- Column headers reference each of the five horizons: 1d (or 1-day), 5d, 10d, 20d, 60d
- Each horizon has a paired return column and a max-drawdown (MDD) column
- Each data cell contains either a numeric value (e.g., "+2.4%") or the text "NA"
- An `N=` chip (showing an observation count) is visible on at least one return cell

---

### UT-05 — Regime-score decile table shows D1–D10 rows with score range and rank-IC (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/regime-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- `/research/regime-lab` page is fully loaded with data

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-lab`
2. Wait for both tables to finish loading
3. Locate the regime-score decile table (the second of the two stacked tables)
4. Count the number of data rows in the decile table (excluding header rows and the Rank-IC row)
5. Read the row labels to confirm they are labelled D1 through D10
6. Inspect the Rank-IC row that appears above the D1–D10 data rows
7. Inspect one decile row to confirm a score-range cell is present (e.g., "0–10" or "10.5–22.3")

**Expected Result:**
- The decile table has exactly 10 data rows labelled D1, D2, D3, D4, D5, D6, D7, D8, D9, D10
- A "Rank-IC" header row is visible above the D1 row, with a numeric value (or "NA") per horizon
- Each decile row has a score-range column showing the min–max range for that decile's regime scores
- Each decile row has a paired forward-return and max-drawdown cell per horizon
- An `N=` chip is visible on at least one return cell in the decile table

---

### UT-06 — Survivorship-bias caveat banner is visible on the page (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research/regime-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- `/research/regime-lab` page is fully loaded

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-lab`
2. Wait for the page to fully load
3. Read the text near the top of the page (below the page title and subtitle)
4. Look for a banner or highlighted text block containing the words "survivorship" or "descriptive" or similar caveat language

**Expected Result:**
- A caveat banner (the `ResearchCaveat` component) is visible near the top of the page
- The banner text includes the word "survivorship" or "descriptive evidence" or comparable disclaimer language
- The banner is not collapsed, hidden behind an accordion, or off-screen
- The banner renders in a visually distinct style (e.g., muted background, alert styling) that draws attention

---

### UT-07 — No native HTML date input element appears on the Regime Lab page (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research/regime-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- `/research/regime-lab` page is fully loaded
- Browser developer tools are accessible (press F12)

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-lab`
2. Wait for the page to fully load
3. Open browser developer tools (press F12) and switch to the Console tab
4. Type the following into the console and press Enter:
   ```
   document.querySelectorAll('input[type="date"]').length
   ```

**Expected Result:**
- The console outputs `0`
- No native calendar date picker appears on the page (no `<input type="date">` element is present)
- The As-of control (if visible) uses a custom toggle or URL-parameter mechanism, not a native date input

---

### UT-08 — Clicking a sort header reorders the by-label table rows (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/regime-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- `/research/regime-lab` page is fully loaded with data in the by-label table
- At least two by-label rows have different numeric return values for the same horizon

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-lab`
2. Wait for the by-label table to finish loading
3. Note the order of the regime-label rows before sorting (e.g., "Risk-on" is in row 1)
4. Click the column sort control for the 1-day return column (look for an up/down arrow icon or a sortable header; the column is identifiable by the "1d" or "1-day" label)
5. Wait for the table to re-render (no full page reload should occur)
6. Read the new order of regime-label rows

**Expected Result:**
- The regime-label rows are reordered by the 1-day return values in ascending order
- The row order after clicking is different from the row order before clicking
- The page does NOT reload (the URL does not change, no loading skeleton reappears)
- All 6 rows remain visible after the sort

---

### UT-09 — Clicking the same sort header again reverses to descending order (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/regime-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- `/research/regime-lab` by-label table is sorted ascending by a return column (continue from UT-08, or re-click once to reach ascending state)

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-lab`
2. Wait for the by-label table to finish loading
3. Click the 1-day return column sort header once to sort ascending
4. Note the current row order (top row has the lowest return value)
5. Click the same 1-day return column sort header a second time
6. Note the new row order

**Expected Result:**
- After the second click, the rows are sorted in descending order (highest return value at the top)
- The row at the top after the second click has a higher return value than the row that was at the top after the first click
- No page reload occurs

---

### UT-10 — NA values remain at the bottom of the list regardless of sort direction (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/regime-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- `/research/regime-lab` page is fully loaded
- At least one cell in the table shows "NA" for the selected column (use the 60d horizon column where thin-sample NAs are more likely)

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-lab`
2. Wait for the by-label table to finish loading
3. Click the 60-day return column sort header to sort ascending
4. Scroll to the bottom of the by-label table and check whether "NA" cells appear at the end (bottom rows)
5. Click the 60-day return column sort header again to sort descending
6. Scroll to the bottom of the by-label table and check whether "NA" cells still appear at the end

**Expected Result:**
- In ascending sort: any row with "NA" in the 60d return column appears after all numeric rows
- In descending sort: any row with "NA" in the 60d return column still appears after all numeric rows
- "NA" cells are never mixed into the middle of the sorted list

---

### UT-11 — As-of toggle reduces the observation counts (n) shown in cells (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/regime-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- `/research/regime-lab` page is fully loaded in All-history mode (default)
- The global As-of date control in the Research Controls section shows the latest date

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-lab`
2. Wait for the page to fully load in All-history mode
3. Locate the As-of / All-history toggle in the Research Controls section of the page (near the top, shared across lab pages)
4. Read and note the `N=` chip value on the "Risk-on" 20-day return cell (or any visible cell with a numeric n value, e.g., "N=150")
5. Click the As-of toggle to switch to As-of mode (the toggle label should change, or a date is applied)
6. Wait for the tables to re-fetch and re-render
7. Read the `N=` chip value on the same cell (e.g., "Risk-on" 20-day return)

**Expected Result:**
- After switching to As-of mode, the `N=` chip value on the inspected cell is smaller than or equal to the All-history value
- At least one cell's n value visibly decreases (e.g., from "N=150" to "N=92")
- The table rows (regime labels and deciles) remain the same — no new labels appear
- No second date picker or native `<input type="date">` element appears when As-of mode is active

---

### UT-12 — Clicking an N= chip opens the Samples page in a new browser tab (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/regime-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- `/research/regime-lab` page is fully loaded with data
- A cell with an `N=` chip is visible (e.g., the "Risk-on" 20-day return cell showing "N=42")

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-lab`
2. Wait for the by-label table to finish loading
3. Locate an `N=` chip on any return cell in the by-label table (e.g., the chip labelled "N=42" on the "Risk-on" row, 20d horizon)
4. Note the n value shown in the chip (e.g., 42)
5. Click the `N=` chip (or right-click and select "Open in new tab" if clicking opens in the same tab)
6. Switch to the newly opened browser tab

**Expected Result:**
- A new browser tab opens at a URL starting with `http://localhost:3255/research/samples`
- The Samples page shows a "Total observations" count (or equivalent) equal to the n value noted in step 4 (e.g., 42)
- The URL in the new tab includes parameters that identify the cohort (regime label and horizon), e.g., `?regime_label=Risk-on&horizon=20d` or equivalent
- The original `/research/regime-lab` tab remains open and unchanged

---

### UT-13 — N= chip href carries the current as-of date when As-of mode is active (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/regime-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- `/research/regime-lab` page is loaded in As-of mode (As-of toggle is active)
- Browser developer tools are accessible (press F12)

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-lab`
2. Switch to As-of mode using the As-of / All-history toggle
3. Wait for the tables to re-render with the filtered n values
4. Right-click an `N=` chip on any return cell in the by-label table and select "Inspect" in browser dev tools (or hover to read the link target in the status bar)
5. Read the `href` attribute of the chip link element

**Expected Result:**
- The `href` attribute of the `N=` chip contains an `asof=` parameter (e.g., `href="/research/samples?regime_label=Risk-on&horizon=20d&asof=2025-06-15"`)
- The date in the `asof=` parameter matches the current as-of date applied to the page
- The `asof=` parameter is present in the URL and is not omitted or empty

---

### UT-14 — Loading skeleton appears while data is being fetched (error)

**Type:** error
**Priority:** P2
**Surface:** `/research/regime-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Browser developer tools are accessible (press F12)

**Steps:**
1. Open browser developer tools (press F12) and switch to the Network tab
2. Set the network throttle to "Slow 3G" or "Fast 3G" to slow down API responses
3. Navigate to `http://localhost:3255/research/regime-lab`
4. Observe the page immediately after navigation, before data loads

**Expected Result:**
- A loading skeleton (shimmering placeholder rows or placeholder blocks) appears in place of the tables while the API request is in-flight
- The skeleton is visible for at least a moment — the page does NOT show a blank white screen
- Once data loads, the skeleton is replaced by the actual by-label and decile tables
- No error card appears if the backend responds successfully

---

### UT-15 — Backend-unavailable error card appears when the API cannot be reached (error)

**Type:** error
**Priority:** P2
**Surface:** `/research/regime-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The backend server is stopped or unreachable (stop the backend process before this test)

**Steps:**
1. Stop the backend server (or disconnect the frontend from the backend)
2. Navigate to `http://localhost:3255/research/regime-lab`
3. Wait for the page to finish its fetch attempt (approximately 5–10 seconds)

**Expected Result:**
- A "Backend unavailable" error card appears on the page (not a blank white screen)
- The page title and layout remain intact (the page does not crash entirely)
- The error card includes text indicating the backend is unavailable or the request failed
- No partial table data or fabricated numbers are shown

**Note:** Restart the backend before continuing with subsequent tests.

---

### UT-16 — Thin-sample cells show NA with observation count, not a fabricated return value (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research/regime-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- `/research/regime-lab` page is fully loaded
- At least one cell is expected to have n below the minimum sample threshold (the 60-day horizon near the latest as-of date is a likely candidate)

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-lab`
2. Wait for both tables to finish loading
3. Locate the 60-day return column in the by-label table or decile table
4. Look for cells showing "NA" in the 60d column
5. Read the full cell content for one "NA" cell (it should show both "NA" and a count, e.g., "NA (n=2)" or "NA n=2")

**Expected Result:**
- Any cell with insufficient observations shows "NA" (or a dash "—") rather than a numeric percentage
- The "NA" cell also displays the actual n count (e.g., "n=2"), not just "NA" alone
- No fabricated numeric return value appears in thin-sample cells
- The NA cell is styled differently from cells with real values (muted appearance)

---

### UT-17 — Existing Research hub lab tiles remain accessible (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/research`
2. Wait for the LABS tile grid to fully load
3. Confirm that the following tiles are still visible: "Factor Lab" (or equivalent tile from iter-52), at least one other existing lab tile (e.g., "Regime × Setup × Pattern", "Event Study")
4. Click the "Factor Lab" tile (or the equivalent tile name that existed before this iteration)
5. Confirm the Factor Lab page loads without errors

**Expected Result:**
- The `/research` hub still shows all existing lab tiles alongside the new "Regime Lab" tile
- Clicking an existing lab tile (e.g., Factor Lab) navigates to its page (e.g., `/research/factor-lab`)
- The existing lab page loads without errors — the new Regime Lab tile has not broken other tiles or their routes

---

### UT-18 — Regime Lab is discoverable within 2 clicks from the Research nav link (ux)

**Type:** ux
**Priority:** P2
**Surface:** navigation → `/research` → `/research/regime-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- User starts at the home page or any page in the application

**Steps:**
1. Navigate to `http://localhost:3255` (the home/dashboard page)
2. Look at the top navigation bar or sidebar for a "Research" link
3. Click the "Research" link in the navigation (click 1)
4. On the `/research` hub page, locate the "Regime Lab" tile with the Gauge icon
5. Click the "Regime Lab" tile (click 2)

**Expected Result:**
- After exactly 2 clicks, the user arrives at `http://localhost:3255/research/regime-lab`
- The "Research" link is visible in the top navigation without scrolling
- The "Regime Lab" tile is visible on the `/research` hub without scrolling past the fold
- The user has not needed to type a URL or use browser history to reach the page

---

### UT-19 — Tables scroll horizontally on a narrow viewport instead of dropping columns (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research/regime-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- `/research/regime-lab` page is fully loaded

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-lab`
2. Wait for both tables to load with data
3. Narrow the browser window to approximately 768px wide (drag the window edge, or use browser dev tools device emulation: press F12 → toggle device toolbar → set width to 768)
4. Observe the by-label table at this viewport width
5. Scroll horizontally within the table area

**Expected Result:**
- The by-label table does not truncate or drop any columns at 768px width
- A horizontal scroll bar (or swipe area) appears within the table container
- All 5 horizon columns (1d, 5d, 10d, 20d, 60d) remain present and reachable by scrolling right
- The table does not overflow outside its container and cause a full-page horizontal scroll

---

### UT-20 — Risk-Off regime shows zero Actionable stocks (regression, J-07 critical)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255
- A snapshot with Risk-Off regime label is available in the backend (use a historical as-of date that corresponds to a Risk-Off period, or use the global as-of control to navigate to one)

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Apply a historical as-of date corresponding to a known Risk-Off regime period using the global as-of control
3. Wait for the stock list to re-render
4. Inspect the stock list for any stocks labelled "Actionable"

**Expected Result:**
- In a Risk-Off regime state, the stock list shows zero stocks labelled "Actionable"
- All stocks show a status of "Watchlist" or equivalent non-actionable label
- This critical rule has not been broken by the Regime Lab implementation

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Research hub loads with Regime Lab tile | smoke | P1 | `/research` |
| UT-02 | Clicking Regime Lab hub tile navigates correctly | happy-path | P1 | `/research` |
| UT-03 | Regime Lab page loads without errors | smoke | P1 | `/research/regime-lab` |
| UT-04 | By-label table shows 6 rows with correct structure | happy-path | P1 | `/research/regime-lab` |
| UT-05 | Decile table shows D1–D10 with score range and rank-IC | happy-path | P1 | `/research/regime-lab` |
| UT-06 | Survivorship-bias caveat banner is visible | ux | P2 | `/research/regime-lab` |
| UT-07 | No native date input on page (J-18 compliance) | ux | P2 | `/research/regime-lab` |
| UT-08 | Sort header reorders by-label table rows | happy-path | P1 | `/research/regime-lab` |
| UT-09 | Second sort click reverses to descending order | happy-path | P1 | `/research/regime-lab` |
| UT-10 | NA values remain at bottom in both sort directions | happy-path | P1 | `/research/regime-lab` |
| UT-11 | As-of toggle reduces observation counts (n) | happy-path | P1 | `/research/regime-lab` |
| UT-12 | N= chip opens count-coherent Samples page in new tab | happy-path | P1 | `/research/regime-lab` |
| UT-13 | N= chip href carries as-of date in As-of mode | happy-path | P1 | `/research/regime-lab` |
| UT-14 | Loading skeleton appears during data fetch | error | P2 | `/research/regime-lab` |
| UT-15 | Backend-unavailable error card appears when API is down | error | P2 | `/research/regime-lab` |
| UT-16 | Thin-sample cells show NA with count, not fabricated value | validation | P2 | `/research/regime-lab` |
| UT-17 | Existing Research hub lab tiles remain accessible | regression | P1 | `/research` |
| UT-18 | Regime Lab discoverable within 2 clicks from nav | ux | P2 | nav → `/research` |
| UT-19 | Tables scroll horizontally on narrow viewport | ux | P2 | `/research/regime-lab` |
| UT-20 | Risk-Off regime shows zero Actionable stocks (J-07) | regression | P1 | `/stocks` |

**P1 tests must all pass for browser QA verdict to be PASS.**
