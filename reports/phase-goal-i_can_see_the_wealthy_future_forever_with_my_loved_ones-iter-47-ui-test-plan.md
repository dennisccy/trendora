# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47
**Date:** 2026-06-22
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Context

This iteration is a backend read-path refactor (J-105) that restores five heavy Research labs
to operational status on the full 3.3 GB live dataset. No frontend source files were changed.
`Frontend Present: yes` was set deliberately so browser-QA captures real rendered figures for
J-29/J-25/J-26 in this iteration rather than auto-skipping.

The load-bearing checks are: each of the five labs loads real figures (no "Backend unavailable"
or permanent skeleton), and each lab's N= drill-down count is coherent with the parent cell.
Labs must be tested one at a time — never concurrently — because of pool-exhaustion risk.

---

## Test Cases

---

### UT-01 — Event-Study matrix loads with real figures (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/event-study`

**Preconditions:**
- Backend is freshly restarted and has completed warm-up (GET http://localhost:8835/api/health returns `"status": "ready"`)
- No other heavy `/research/*` request is in flight
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/research/event-study`
2. Wait for the loading skeleton to disappear (allow up to 90 seconds on a cold cache)
3. Observe the event-study matrix table

**Expected Result:**
- The event-study matrix renders with visible rows for horizons (e.g., 1d, 5d, 10d, 20d, 60d)
- At least one cell in the matrix shows a numeric mean_return value (e.g., "+2.34%") — not a blank cell, not "Backend unavailable", and not a spinning skeleton
- The page heading or section label for "Event Study" is visible
- No red error banner or "Backend unavailable" message is visible anywhere on the page

---

### UT-02 — Event-Study matrix renders per-horizon mean_return, win-rate, and N values (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/event-study`

**Preconditions:**
- Backend freshly restarted and warmed (health check returns `"ready"`)
- No other heavy `/research/*` request is in flight
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/research/event-study`
2. Wait for the loading skeleton to disappear (allow up to 90 seconds)
3. Locate the per-horizon row for the 5d horizon in the matrix
4. Verify the 5d row contains: a numeric mean_return value (e.g., "+1.87%"), a numeric win-rate value (e.g., "58%"), and an N= chip (e.g., "N=142")
5. Verify at least two additional horizon rows (e.g., 10d, 20d) are also populated with numeric values

**Expected Result:**
- The matrix shows multiple horizon rows, each with non-empty numeric mean_return, win-rate, and N= values
- No row shows "Loading…" or an empty dash where a figure should appear
- The N= chip on each populated cell shows a positive integer (greater than zero)

---

### UT-03 — Event-Study N= chip drills into count-coherent /research/samples (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/event-study` and `/research/samples`

**Preconditions:**
- Backend freshly restarted and warmed
- No other heavy `/research/*` request is in flight
- Frontend is running at http://localhost:3835
- Event-study matrix is already loaded and populated with at least one N= chip

**Steps:**
1. Navigate to `http://localhost:3835/research/event-study`
2. Wait for the matrix to fully populate (loading skeleton gone, at least one N= chip visible)
3. Read and note the exact integer shown on one N= chip in the matrix (e.g., if the chip shows "N=142", write down 142)
4. Click that N= chip
5. Wait for the `/research/samples` page to load
6. Count or observe the total number of rows/samples displayed on the `/research/samples` page (look for a "total" row count, a row counter, or a paginated record count)

**Expected Result:**
- Clicking the N= chip navigates to a URL of the form `http://localhost:3835/research/samples?...`
- The `/research/samples` page loads without error — no "Backend unavailable" message
- The total sample count displayed on `/research/samples` matches the integer noted from the N= chip (e.g., 142 rows)

---

### UT-04 — Factor Lab decile table and rank-IC figure load with real figures (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Backend freshly restarted and warmed (previous event-study fetch must be complete before starting this test)
- No other heavy `/research/*` request is in flight
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the page to fully load (allow up to 90 seconds on a cold cache)
3. Locate the Factor Lab section on the page

**Expected Result:**
- The Factor Lab section renders visibly — no blank placeholder, no "Backend unavailable" message
- The decile table shows at least one factor row with numeric decile values (e.g., a column for "Decile 1" containing a numeric return like "+3.12%")
- A rank-IC figure or value is visible somewhere in the Factor Lab section
- No spinning skeleton persists after 90 seconds

---

### UT-05 — Factor Lab decile sort per factor renders 10 decile rows with real figures (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Backend freshly restarted and warmed
- No other heavy `/research/*` request is in flight
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the Factor Lab section to fully populate (loading skeleton gone)
3. Locate the decile sort table for a factor (e.g., "leadership_score" or whichever factor is default-selected)
4. Count the number of decile rows in the table
5. Verify each decile row shows a numeric mean_return value (not blank or "—")
6. Verify a rank-IC figure is displayed for the selected factor

**Expected Result:**
- The decile table shows 10 rows (Decile 1 through Decile 10)
- Each row has a numeric mean_return value (e.g., "+2.1%", "-0.4%") — no empty or "N/A" cells where figures are expected
- The rank-IC value displayed is a numeric decimal (e.g., "0.23") — not blank
- No "Backend unavailable" or HTTP 500 error is shown

---

### UT-06 — Factor Lab N= chip drills into count-coherent /research/samples (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` and `/research/samples`

**Preconditions:**
- Backend freshly restarted and warmed
- No other heavy `/research/*` request is in flight
- Factor Lab decile table is already loaded with at least one N= chip visible

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the Factor Lab decile table to fully populate
3. Locate an N= chip in the decile table (e.g., "N=89" on the top-decile row)
4. Note the exact integer from the chip
5. Click the N= chip
6. Wait for the `/research/samples` page to load
7. Observe the total sample count or row count on the `/research/samples` page

**Expected Result:**
- Clicking the N= chip navigates to a URL of the form `http://localhost:3835/research/samples?...`
- The `/research/samples` page loads without error
- The total samples count on the page matches the integer noted from the N= chip

---

### UT-07 — Factor-combination composite cohort renders real figures (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Backend freshly restarted and warmed
- No other heavy `/research/*` request is in flight
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the page to fully load
3. Locate the multi-factor composite section (factor-combination area)
4. Verify the composite section shows a result card or table with a numeric pool_n value (e.g., "N=234") and at least one row of composite cohort data
5. Verify the composite row(s) show numeric mean_return and win-rate values

**Expected Result:**
- The factor-combination section is visible on the page
- A pool_n value is shown as a positive integer
- At least one composite cohort row displays numeric mean_return and win-rate (e.g., "+1.9%", "61%")
- No "Backend unavailable" or "Loading…" state persists after the page has loaded

---

### UT-08 — Regime x Setup x Pattern ranked table loads with real figures (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/regime-setup-pattern`

**Preconditions:**
- Backend freshly restarted and warmed
- No other heavy `/research/*` request is in flight
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/research/regime-setup-pattern`
2. Wait for the page to fully load (allow up to 90 seconds)
3. Observe the ranked table

**Expected Result:**
- The ranked table renders with visible rows — no permanent "Loading…" state or skeleton
- At least one row shows a numeric mean_return value and a non-zero n_total
- No "Backend unavailable" message or red error banner is visible

---

### UT-09 — Regime x Setup x Pattern ranked table shows rows with numeric mean_return and n_total (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/regime-setup-pattern`

**Preconditions:**
- Backend freshly restarted and warmed
- No other heavy `/research/*` request is in flight
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/research/regime-setup-pattern`
2. Wait for the ranked table to populate (loading skeleton disappears)
3. Locate the first ranked row in the table
4. Verify the row shows: a regime label (e.g., "Bull"), a setup label, a pattern label, a numeric mean_return (e.g., "+3.4%"), and a non-zero n_total (e.g., "n=47")
5. Scroll down to verify at least 3 rows are populated with numeric values

**Expected Result:**
- The table contains at least 3 rows
- Every visible row has a non-empty regime label, setup label, pattern label, numeric mean_return, and non-zero n_total
- No row shows an empty mean_return cell where a figure should appear
- The table does not show an error state

---

### UT-10 — Downtrend Opportunity lab loads with real figures (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/downtrend-opportunity`

**Preconditions:**
- Backend freshly restarted and warmed
- No other heavy `/research/*` request is in flight
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/research/downtrend-opportunity`
2. Wait for the page to fully load (allow up to 60 seconds)
3. Observe the result table or figures section

**Expected Result:**
- The page renders — no blank screen, no "Backend unavailable" message
- At least one row in the result table shows a numeric mean_return value
- No spinning skeleton persists after 60 seconds

---

### UT-11 — Downtrend Opportunity lab shows rows with numeric mean_return within 30 seconds (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/downtrend-opportunity`

**Preconditions:**
- Backend freshly restarted and warmed
- No other heavy `/research/*` request is in flight
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/research/downtrend-opportunity`
2. Note the time on your clock
3. Wait until the result table populates or 30 seconds elapses (whichever comes first)
4. Locate the first row in the result table
5. Verify the row shows a numeric mean_return value (e.g., "+1.2%") and a non-zero n value

**Expected Result:**
- Within 30 seconds (on a warm cache), at least one result row with a numeric mean_return and n > 0 is visible
- No "Backend unavailable" message appears at any point during the wait

---

### UT-12 — Event-Study page shows honest partial/NA state for low-sample horizons (error handling)

**Type:** error
**Priority:** P2
**Surface:** `/research/event-study`

**Preconditions:**
- Backend freshly restarted and warmed
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/research/event-study`
2. Wait for the matrix to populate
3. Look for any cell that shows "NA", "—", or a partial-window indicator instead of a numeric return
4. Verify that any such cell also shows a sample size (e.g., "N=3") or an explicit "insufficient samples" label

**Expected Result:**
- If any cell lacks sufficient samples, it shows "NA" or "—" with a sample count indicator (not a blank unmarked cell and not a fabricated numeric return)
- Cells with real data still show numeric values — the NA state appears only for genuinely low-sample cohorts
- No cell fabricates a return value to fill a gap

---

### UT-13 — Navigating directly to /research/samples without a valid cohort shows a handled empty state (error handling)

**Type:** error
**Priority:** P2
**Surface:** `/research/samples`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/research/samples` (no query parameters)
2. Wait for the page to load

**Expected Result:**
- The page loads without crashing (no unhandled exception screen)
- The page shows either an empty-state message (e.g., "No samples to display", "Select a cohort"), or an instruction to navigate back to a lab
- The page does NOT show a 500 error or a blank white screen

---

### UT-14 — All five Research labs still accessible from the Research navigation hub (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research` (navigation hub)

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Look at the navigation links or tabs within the Research section
3. Verify there is a visible link or tab to "Event Study" (or similar label)
4. Click the "Event Study" link/tab
5. Verify the URL changes to `http://localhost:3835/research/event-study` and the page loads
6. Use browser back button to return to `http://localhost:3835/research`
7. Verify there is a visible link or tab to "Regime x Setup x Pattern" (or similar label)
8. Click that link/tab
9. Verify the URL changes to `http://localhost:3835/research/regime-setup-pattern` and the page loads
10. Use browser back button to return to `http://localhost:3835/research`
11. Verify there is a visible link or tab to "Downtrend Opportunity" (or similar label)
12. Click that link/tab
13. Verify the URL changes to `http://localhost:3835/research/downtrend-opportunity` and the page loads

**Expected Result:**
- All three sub-routes (event-study, regime-setup-pattern, downtrend-opportunity) are reachable from the Research hub via visible navigation links or tabs
- Each route loads without error
- The Research hub's own layout and navigation structure is unchanged from the previous iteration

---

### UT-15 — N= count coherence holds across multiple labs (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/event-study`, `/research`, `/research/samples`

**Preconditions:**
- Backend freshly restarted and warmed
- Only one heavy research fetch at a time — complete event-study load fully before starting the Factor Lab fetch

**Steps:**
1. Navigate to `http://localhost:3835/research/event-study`
2. Wait for the matrix to fully populate
3. Note the N= value from one chip in the matrix (e.g., "N=67")
4. Click that N= chip and verify `/research/samples` total count equals 67
5. Press the browser back button to return to `http://localhost:3835/research/event-study`
6. Navigate to `http://localhost:3835/research` (Factor Lab)
7. Wait for the decile table to fully populate
8. Note the N= value from one chip in the decile table (e.g., "N=45")
9. Click that N= chip and verify `/research/samples` total count equals 45

**Expected Result:**
- In both cases the total count on `/research/samples` exactly matches the integer shown on the N= chip that was clicked
- No mismatch between displayed N and actual drill-down count

---

### UT-16 — Previously-working stock leaderboard (NVDA) scores remain consistent (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks` and `/stocks/<ticker>`

**Preconditions:**
- Backend freshly restarted and warmed
- NVDA is present in the dataset
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Locate NVDA in the leaderboard list
3. Note the Leadership score, Entry Quality score, and Risk score shown for NVDA in the leaderboard row
4. Click on "NVDA" to open the NVDA detail page
5. On the NVDA detail page, locate the Leadership score, Entry Quality score, and Risk score

**Expected Result:**
- The NVDA detail page scores for Leadership, Entry Quality, and Risk are exactly identical (digit for digit) to the values shown on the leaderboard
- No discrepancy between the leaderboard and detail page scores (single-source-of-truth invariant)

---

### UT-17 — As-of date toggle still switches between current and historical views (regression)

**Type:** regression
**Priority:** P1
**Surface:** dashboard and as-of panel

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is warmed

**Steps:**
1. Navigate to `http://localhost:3835` (dashboard)
2. Locate the as-of date panel or control on the dashboard
3. Note the current as-of date displayed
4. Click the back-navigation control (e.g., the "previous date" arrow or a calendar control) to move to a date approximately 30 days in the past
5. Wait for the page to update (allow up to 15 seconds)
6. Verify the figures on the dashboard change to reflect the historical date
7. Click the "All history" or "latest" control to return to the current date
8. Wait for the page to update
9. Verify the dashboard returns to showing current figures

**Expected Result:**
- Navigating to a historical date causes visible figure updates on the dashboard
- The as-of date indicator in the panel reflects the selected historical date
- Returning to the latest date restores the current figures
- No error message appears during either transition

---

### UT-18 — Research hub and sub-pages are discoverable from main navigation (ux)

**Type:** ux
**Priority:** P2
**Surface:** main navigation / sidebar

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835` (home/dashboard)
2. Look at the main navigation sidebar or header menu
3. Verify a "Research" link or menu item is visible without scrolling or expanding a hidden menu
4. Click the "Research" link
5. Verify the page navigates to `http://localhost:3835/research`
6. Verify the Research page shows visible tabs or links to sub-labs (Event Study, Regime x Setup x Pattern, Downtrend Opportunity)

**Expected Result:**
- "Research" is a clearly labeled link in the main navigation — reachable within 1 click from the dashboard
- The Research page itself shows visible navigation to the five lab sub-pages
- No sub-lab is hidden behind an unmarked icon or requires developer knowledge to find

---

### UT-19 — Five heavy labs each load independently (one-at-a-time) without interfering with each other (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research/event-study`, `/research`, `/research/regime-setup-pattern`, `/research/downtrend-opportunity`

**Preconditions:**
- Backend freshly restarted and warmed
- Frontend is running at http://localhost:3835
- This test must be run sequentially: complete each lab load fully before navigating to the next

**Steps:**
1. Navigate to `http://localhost:3835/research/event-study`, wait for full population, verify real figures visible
2. Navigate to `http://localhost:3835/research`, wait for Factor Lab to fully populate, verify real decile figures visible
3. Navigate to `http://localhost:3835/research/regime-setup-pattern`, wait for ranked table to populate, verify real rows visible
4. Navigate to `http://localhost:3835/research/downtrend-opportunity`, wait for result table to populate, verify real rows visible

**Expected Result:**
- Each lab loads real figures when visited one at a time
- No lab causes the next lab to fail (no residual resource contention visible to the user)
- Each lab's loading indicator (skeleton/spinner) eventually disappears and is replaced by real data — not permanently stuck

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Event-Study matrix loads without errors | smoke | P1 | `/research/event-study` |
| UT-02 | Event-Study per-horizon mean/win-rate/N values render | happy-path | P1 | `/research/event-study` |
| UT-03 | Event-Study N= drill-down is count-coherent | happy-path | P1 | `/research/event-study` + `/research/samples` |
| UT-04 | Factor Lab decile table and rank-IC render | smoke | P1 | `/research` |
| UT-05 | Factor Lab 10 decile rows with real figures | happy-path | P1 | `/research` |
| UT-06 | Factor Lab N= drill-down is count-coherent | happy-path | P1 | `/research` + `/research/samples` |
| UT-07 | Factor-combination composite cohort renders real figures | happy-path | P1 | `/research` |
| UT-08 | Regime x Setup x Pattern table loads without errors | smoke | P1 | `/research/regime-setup-pattern` |
| UT-09 | Regime x Setup x Pattern rows have numeric mean_return and n_total | happy-path | P1 | `/research/regime-setup-pattern` |
| UT-10 | Downtrend Opportunity loads without errors | smoke | P1 | `/research/downtrend-opportunity` |
| UT-11 | Downtrend Opportunity shows real figures within 30 seconds | happy-path | P1 | `/research/downtrend-opportunity` |
| UT-12 | Low-sample horizons show honest NA/partial state | error | P2 | `/research/event-study` |
| UT-13 | /research/samples without params shows handled empty state | error | P2 | `/research/samples` |
| UT-14 | All five Research labs reachable from navigation hub | regression | P1 | `/research` (hub) |
| UT-15 | N= count coherence holds across multiple labs | regression | P1 | `/research/*` + `/research/samples` |
| UT-16 | NVDA leaderboard scores match detail page | regression | P1 | `/stocks` + `/stocks/NVDA` |
| UT-17 | As-of date toggle still works after backend refactor | regression | P1 | dashboard |
| UT-18 | Research section discoverable from main navigation | ux | P2 | navigation |
| UT-19 | Five heavy labs load independently without interfering | ux | P2 | `/research/*` |

**P1 tests (UT-01 through UT-11, UT-14 through UT-17) must all pass for browser QA verdict to be PASS.**

**Critical load-bearing checks (per task specification):**
- Each of the five labs renders real figures (no "Backend unavailable" / skeleton) on the full live dataset
- Each lab is fetched individually (never concurrently)
- Each lab's N= drill-down count is coherent with the parent cell's reported N
