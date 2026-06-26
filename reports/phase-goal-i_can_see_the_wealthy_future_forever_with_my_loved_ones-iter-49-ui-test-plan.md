# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49
**Date:** 2026-06-26
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Leaderboard shows "Proximity to 52w high" column directly after "Risk" (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and serving `/api/stocks`

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait up to 5 seconds for the table to render
3. Locate the "Risk" column header in the table header row
4. Look at the column immediately to the right of "Risk"

**Expected Result:**
- A column header reading exactly "Proximity to 52w high" is visible directly to the right of the "Risk" column header
- Each table row shows either a percentage value (e.g., `-0.53%`) or the muted text "NA" in that column cell
- No blank screen, no "Backend unavailable" error banner, and no JavaScript error visible on the page

---

### UT-02 — Proximity column value matches the stock's Leadership breakdown on the detail page (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks` and `/stocks/:ticker`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and at least one stock row shows a percentage (not "NA") in the "Proximity to 52w high" column

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the table rows to appear
3. In the "Proximity to 52w high" column, find any row displaying a percentage value (e.g., `-2.31%`); note the ticker symbol and the exact value shown
4. Click the ticker symbol link in that row to open the Stock Detail page
5. On the Stock Detail page, scroll down to the "Leadership" or "Leadership Score" section
6. Locate the component row labeled "Proximity to 52w high" inside the Leadership breakdown

**Expected Result:**
- The "Proximity to 52w high" row in the Leadership component breakdown shows a percentage (e.g., `-2.31%`), not an internal rank string like "pctl 73"
- The percentage displayed in the breakdown is byte-identical to the value noted in step 3 (same sign, same decimal places, same number)

---

### UT-03 — Clicking "Proximity to 52w high" header sorts the table and shows sort indicator (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255
- At least two stock rows are visible with non-NA proximity values

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the table to fully load
3. Note the ticker symbols in the first three rows (before any sorting)
4. Click the "Proximity to 52w high" column header
5. Wait 1 second for the table to re-sort
6. Note the ticker symbols in the first three rows after sorting
7. Observe which column header has a sort-direction arrow indicator

**Expected Result:**
- The ticker symbols in the first three rows are different from those noted in step 3 (the row order changed)
- A sort-direction arrow (↑ or ↓) appears on the "Proximity to 52w high" column header
- No other column header shows a sort arrow (only this column is the active sort)

---

### UT-04 — Clicking the column header a second time reverses the sort direction (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Table is already sorted by "Proximity to 52w high" (UT-03 was performed or column was clicked once)
- The sort arrow on "Proximity to 52w high" is visible

**Steps:**
1. Confirm the "Proximity to 52w high" column header shows a sort arrow
2. Note the ticker in the first row and the value in the "Proximity to 52w high" column for that row
3. Click the "Proximity to 52w high" column header a second time
4. Wait 1 second for the table to re-sort
5. Note the ticker now in the first row

**Expected Result:**
- The ticker in the first row is different from the one noted in step 2 (order reversed)
- The sort arrow on the "Proximity to 52w high" header has flipped direction (from ↑ to ↓ or from ↓ to ↑)

---

### UT-05 — "NA" cells are muted and sort to the bottom in both ascending and descending order (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255
- At least one stock row shows "NA" in the "Proximity to 52w high" column

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Locate any cell displaying "NA" in the "Proximity to 52w high" column
3. Compare the text color of "NA" to a nearby numeric percentage cell in the same column (e.g., `-1.05%`)
4. Click the "Proximity to 52w high" column header to sort
5. Scroll to the very bottom of the table and observe the last rows in the "Proximity to 52w high" column
6. Click the "Proximity to 52w high" column header again to reverse the sort
7. Scroll to the very bottom of the table again and observe the last rows

**Expected Result:**
- The "NA" text in step 3 appears in a muted/grayed-out color, visually distinct from numeric percentage values in the same column
- After step 5 (first sort direction): all rows showing "NA" are at the bottom of the table; rows with numeric percentage values appear above them
- After step 7 (reversed sort direction): rows showing "NA" are still at the bottom; only the numeric rows have reordered

---

### UT-06 — Hovering the info icon on the "Proximity to 52w high" header shows a glossary tooltip (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the table header row to render
3. Locate the small info icon (ⓘ or circle-i marker) on the "Proximity to 52w high" column header
4. Move the mouse cursor over the info icon and hold for 2 seconds

**Expected Result:**
- A tooltip popover appears near the icon
- The tooltip contains a plain-language explanation involving proximity to the 52-week high (e.g., percentage below 52-week peak, distance from high, or similar definition from the methodology catalog)
- The tooltip text is not empty, does not say "undefined", and does not read "term not found" or any similar missing-entry message

---

### UT-07 — Stock Detail "Proximity to 52w high" shows raw distance value, not a percentile rank (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/:ticker`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and at least one stock's Leadership breakdown is accessible

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Click any ticker link visible in the leaderboard table
3. On the Stock Detail page, scroll to the "Leadership" or "Leadership Score" section
4. Find the row labeled "Proximity to 52w high" in the component breakdown list
5. Read the value displayed next to that label

**Expected Result:**
- The value is a percentage string (e.g., `-0.53%`) or "NA", not an internal rank label (e.g., NOT "pctl 73", NOT a plain integer like "73")
- If the value is a percentage, it has the same sign convention as values shown on the `/stocks` leaderboard (zero means at a fresh 52-week high; negative means below the high)

---

### UT-08 — Readiness badge reaches "Ready" when the app is opened at the LAN-IP address (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** All pages — top-bar readiness badge

**Preconditions:**
- App is started with `./scripts/dev.sh` (both backend and frontend are running)
- The terminal output from `./scripts/dev.sh` includes a LAN-IP URL (e.g., `http://192.168.1.68:3255`)
- A browser on the same machine or same LAN can reach that URL

**Steps:**
1. Run `./scripts/dev.sh` and note the LAN-IP URL printed in the terminal (e.g., `http://192.168.1.68:3255`)
2. Open a browser and navigate to that LAN-IP URL (do NOT use `localhost`)
3. Wait up to 15 seconds, watching the readiness badge in the top bar of the application

**Expected Result:**
- The badge initially shows "Initializing… history n/m" (where n and m are actual numbers, not placeholders)
- Within 15 seconds the badge transitions to "Ready"
- The badge does NOT remain stuck on "Backend unavailable"
- Data sections on the page begin to populate (e.g., stock list or dashboard content appears)

**What "broken" looks like:** Badge stays on "Backend unavailable" the entire time, or the page shows an error screen instead of the app. This means the LAN-IP CORS/host fix did not apply.

---

### UT-09 — Readiness badge shows "Backend unavailable" when the backend is genuinely stopped (error)

**Type:** error
**Priority:** P1
**Surface:** All pages — top-bar readiness badge

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend service is stopped (the Python/FastAPI server is not running)

**Steps:**
1. Confirm the frontend responds by navigating to `http://localhost:3255` (the page shell should load even without a backend)
2. Ensure the backend is stopped (do not start it)
3. Wait 5–10 seconds after the page loads
4. Observe the readiness badge in the top bar

**Expected Result:**
- The readiness badge displays exactly "Backend unavailable" (not "Ready", not "Initializing…")
- Data sections show empty or error states, not fabricated data
- The badge does NOT flip to "Ready" at any point while the backend remains stopped

**What "broken" looks like:** Badge shows "Ready" even though no backend is serving — this would indicate the honest-readiness fix was incorrectly applied.

---

### UT-10 — Dashboard loads data correctly at localhost after API_BASE change (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Dashboard)

**Preconditions:**
- Frontend running at http://localhost:3255
- Backend running and serving data

**Steps:**
1. Navigate to `http://localhost:3255` (the Dashboard / home page)
2. Wait up to 5 seconds for the page to load
3. Observe whether content sections render (e.g., market regime indicator, sector scores, or theme cards)
4. Open browser DevTools (F12), click the "Network" tab, filter by "Fetch/XHR", and look for any API calls with status 0, 403, or error labels

**Expected Result:**
- The Dashboard page displays content (regime label, sector or theme data) — not a blank page or "Backend unavailable" banner
- The readiness badge shows "Ready" or "Initializing… n/m"
- No API calls in the Network tab show status 0, 403, or any CORS-related error

---

### UT-11 — Stocks leaderboard loads all existing columns at localhost (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend running at http://localhost:3255
- Backend running and serving stock data

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait up to 5 seconds for the table to load
3. Confirm the following column headers are all visible in the table header row: a ticker/name column, "Leadership Score" (or "Leadership"), "Risk", "Proximity to 52w high", "Setup", and at least one forward-return column (e.g., "1D Return" or "5D Return")
4. Check that multiple stock rows are populated with data in all those columns

**Expected Result:**
- All pre-existing columns remain present (ticker, Leadership Score, Risk, Setup, forward-return columns) plus the new "Proximity to 52w high" column
- The leaderboard table contains populated rows with actual stock data
- No "Backend unavailable" error is shown and no columns have disappeared compared to before this iteration

---

### UT-12 — Research lab page loads after API_BASE change (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/research` (or Research Lab route)

**Preconditions:**
- Frontend running at http://localhost:3255
- Backend running and serving research/factor data

**Steps:**
1. Navigate to `http://localhost:3255/research`
2. Wait up to 5 seconds
3. Observe whether any data sections render (factor analysis tables, research metrics, or similar content)

**Expected Result:**
- The Research page renders at least one content section (factor table, analytics panel, or similar) without a "Backend unavailable" error banner
- The page is not blank
- Browser console (F12 → Console) does not show CORS errors or `API_BASE`-related fetch failures

---

### UT-13 — Column sort on a pre-existing column still reorders the leaderboard (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend running at http://localhost:3255
- At least two stock rows visible

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the table to load
3. Note the ticker symbol in the first row
4. Click the "Leadership Score" column header (one of the existing sortable columns from before this iteration)
5. Wait 1 second
6. Note the ticker symbol now in the first row

**Expected Result:**
- The ticker symbol in the first row after step 5 is different from the one noted in step 3 (the table reordered)
- A sort-direction arrow appears on the "Leadership Score" header
- The "Proximity to 52w high" column header does NOT show a sort arrow (only the clicked column is active)
- This confirms the addition of the new sort key did not break the existing sort mechanism

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Proximity column renders after Risk column | smoke | P1 | `/stocks` |
| UT-02 | Proximity value matches Leadership breakdown | happy-path | P1 | `/stocks`, `/stocks/:ticker` |
| UT-03 | Clicking header sorts table and shows arrow | happy-path | P1 | `/stocks` |
| UT-04 | Second click reverses sort direction | happy-path | P1 | `/stocks` |
| UT-05 | NA cells are muted and sort last in both directions | validation | P2 | `/stocks` |
| UT-06 | Info icon tooltip shows glossary definition | ux | P2 | `/stocks` |
| UT-07 | Detail page shows raw distance, not percentile | regression | P1 | `/stocks/:ticker` |
| UT-08 | Badge reaches Ready at LAN-IP address | happy-path | P1 | All pages |
| UT-09 | Badge shows Unavailable when backend is stopped | error | P1 | All pages |
| UT-10 | Dashboard loads data at localhost | regression | P1 | `/` |
| UT-11 | Leaderboard retains all existing columns at localhost | regression | P1 | `/stocks` |
| UT-12 | Research lab loads after API_BASE change | regression | P2 | `/research` |
| UT-13 | Pre-existing column sort still reorders the table | regression | P1 | `/stocks` |

**P1 tests must all pass for browser QA verdict to be PASS.**
