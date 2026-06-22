# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45
**Date:** 2026-06-22
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Research hub page loads as a card grid (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the page to fully load (no loading spinner or "Checking backend…" message)

**Expected Result:**
- Page renders a card grid listing seven named lab cards — no heavy analysis table, chart, or matrix appears on this page
- Each card shows a lab name and a short description
- No console error messages appear
- The URL in the browser address bar shows `http://localhost:3835/research`

---

### UT-02 — Severity-velocity study page loads with matrix (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/severity-velocity`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835 with seed data loaded

**Steps:**
1. Navigate to `http://localhost:3835/research/severity-velocity`
2. Wait for the matrix table to load (allow up to 30 seconds for first load)

**Expected Result:**
- Page renders without a blank screen or "Checking backend…" placeholder
- A matrix table is visible with 3 rows labelled "Risk-on", "Neutral", and "Risk-off"
- The matrix has 3 columns labelled "Rising", "Flat", and "Falling"
- A horizon selector control is visible on the page
- The verdict card section is visible below the matrix

---

### UT-03 — Factor Lab sub-route loads independently (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/research/factor-lab`
2. Wait for the page to fully load

**Expected Result:**
- Page renders a Factor Lab analysis (not an error page or 404)
- The Factor Lab content is visible (figures or table)
- No "Checking backend…" skeleton persists after load completes

---

### UT-04 — Event Study sub-route loads independently (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/event-study`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/research/event-study`
2. Wait for the page to fully load

**Expected Result:**
- Page renders an Event Study analysis
- A study table or matrix with N= chips is visible
- No 404 error and no blank page

---

### UT-05 — Severity-velocity matrix cell values and horizon selector work (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/severity-velocity`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835 with seed data loaded
- Page at `/research/severity-velocity` has loaded the matrix with at least one non-NA cell

**Steps:**
1. Navigate to `http://localhost:3835/research/severity-velocity`
2. Wait for the matrix to load and confirm at least one cell shows a numeric mean return value (e.g., "+1.2%") and a win-rate value
3. Locate the horizon selector (labelled "5d", "10d", "20d", "60d" or similar)
4. Click the "5d" option in the horizon selector
5. Wait 2 seconds for the matrix to update
6. Note the mean return value in the "Risk-off / Rising" cell (or any populated cell)
7. Click the "60d" option in the horizon selector
8. Wait 2 seconds for the matrix to update

**Expected Result:**
- After clicking "5d": matrix cells display numeric mean return, win-rate percentage, and an N= chip for the 5-day forward-return horizon
- After clicking "60d": the numeric values in the matrix cells change (different from the 5d values) to reflect the 60-day forward-return horizon
- Both updates happen without a page reload — only the cell values change in place
- No error message appears during or after the horizon change

---

### UT-06 — Severity-velocity verdict card shows honest finding with all three caveats (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/severity-velocity`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- Page at `/research/severity-velocity` has loaded

**Steps:**
1. Navigate to `http://localhost:3835/research/severity-velocity`
2. Scroll down past the matrix table to locate the verdict card section
3. Read the verdict card text

**Expected Result:**
- The verdict card contains the text "NOT supported" (in any casing)
- The verdict card contains the word "survivorship"
- The verdict card contains the phrase "bull-dominated" (or "bull dominated")
- The verdict card contains the phrase "underpowered-for-crashes" (or "underpowered for crashes")
- The verdict card does NOT display a positive/optimistic conclusion contradicting the "NOT supported" finding
- The text states that rising stress under a red (Risk-off) regime preceded a bounce, not a decline

---

### UT-07 — N= chip opens reproducing cohort in a new tab (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/severity-velocity` → `/research/samples`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- Page at `/research/severity-velocity` has loaded with at least one non-zero N= chip visible in the matrix

**Steps:**
1. Navigate to `http://localhost:3835/research/severity-velocity`
2. Wait for the matrix to load and locate any cell showing a non-zero N value (e.g., a chip displaying "N=32")
3. Note the exact N count shown on that chip (e.g., 32)
4. Click that N= chip
5. Switch to the newly opened browser tab

**Expected Result:**
- A new browser tab opens (the original tab remains on `/research/severity-velocity`)
- The new tab URL contains `/research/samples` and includes query parameters identifying the cohort (regime family, velocity sign, horizon)
- The Samples page in the new tab displays a human-readable cohort description (e.g., "Risk-off / Rising / 5-day" or similar — NOT a raw JSON dump)
- The total sample count shown on the Samples page matches the N count noted in step 3 (e.g., exactly 32)
- No 4xx error page appears in the new tab

---

### UT-08 — Research hub card navigation carries global as-of date (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` hub

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/research?asof=2025-06-30`
2. Wait for the hub card grid to render
3. Click the lab card for "Severity-velocity" (or the card labelled with the severity-velocity study name)

**Expected Result:**
- The browser navigates to `/research/severity-velocity`
- The URL in the address bar contains `asof=2025-06-30` (the same date passed to the hub)
- The severity-velocity page loads its matrix in as-of mode, scoped to dates on or before 2025-06-30
- No second date state appears — only the single global `?asof` is present in the URL

---

### UT-09 — As-of mode toggle on severity-velocity narrows observations (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/severity-velocity`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- Page at `/research/severity-velocity` has loaded in "All history" mode (default)

**Steps:**
1. Navigate to `http://localhost:3835/research/severity-velocity`
2. Wait for the matrix to load and note the N value in any populated cell (e.g., "N=85" in Risk-off / Rising)
3. Locate the As-of mode toggle or control (labelled "All history" or "As of" or similar)
4. Click the "As of" option or toggle to enable point-in-time mode
5. If a date field appears, type `2022-12-31` into it
6. Wait for the matrix to refresh

**Expected Result:**
- After enabling As-of mode with date 2022-12-31: the N values in the matrix cells decrease (fewer observations) compared to the "All history" values noted in step 2
- No cell shows the same N as the all-history view if data exists beyond 2022-12-31
- No fabricated data appears — cells with zero observations for the narrowed date range show "NA" or a low-sample indicator, not a numeric mean return
- No error message appears

---

### UT-10 — Regime-setup-pattern sub-route loads with pre-split figures (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/regime-setup-pattern`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/research/regime-setup-pattern`
2. Wait for the matrix table to load (allow up to 30 seconds)
3. Confirm that the matrix table renders with numeric values (not an error or empty state)

**Expected Result:**
- The Regime × Setup × Pattern matrix renders with the same figures that appeared on the old `/research` monolith page before this iteration's split
- N= chips are present and clickable in the table
- No 404 error, no blank page, no "Checking backend…" skeleton that never resolves

---

### UT-11 — Factor-combination sub-route loads with pre-split figures (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/factor-combination`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/research/factor-combination`
2. Wait for the analysis table to load (allow up to 30 seconds for first load; second load should be faster due to caching)
3. Confirm that the analysis table renders with numeric values

**Expected Result:**
- The Multi-factor Combination analysis table renders with data matching the pre-split baseline figures
- N= chips or linkable cells are present where expected
- Second visit to the same URL (navigate away and return) loads noticeably faster (cache hit)
- No 404 or blank page

---

### UT-12 — Downtrend-opportunity sub-route loads (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/downtrend-opportunity`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/research/downtrend-opportunity`
2. Wait for the downtrend analysis table to load

**Expected Result:**
- The Downtrend Opportunity analysis table renders with the same figures as before this iteration's split
- No 404 error, no blank page
- The table shows historical run data consistent with the pre-split `/research` page

---

### UT-13 — Recovery-turn-edge sub-route loads (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/recovery-turn-edge`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/research/recovery-turn-edge`
2. Wait for the Recovery-Turn Edge study to load

**Expected Result:**
- The Recovery-Turn Edge analysis renders with figures and N= chips
- N= chips in the Recovery-Turn Edge table open valid cohort tabs in `/research/samples`
- No 404 error or blank page

---

### UT-14 — Old research page (/research) no longer shows heavy analysis content (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the page to fully load
3. Scroll through the entire page

**Expected Result:**
- The page shows ONLY the hub card grid — no analysis matrix, no heavy study chart, no regime × setup table is embedded on this page
- Page load completes without issuing backend calls to `/api/research/factor-combination`, `/api/research/event-study`, `/api/research/regime-setup-pattern`, or `/api/research/downtrend-opportunity` (opening the hub page alone does NOT trigger those fetches)
- Seven lab cards are listed with names and descriptions

---

### UT-15 — Sidebar Research link highlights for any /research/* sub-route (regression)

**Type:** regression
**Priority:** P2
**Surface:** sidebar navigation

**Preconditions:**
- Frontend is running at http://localhost:3835
- Sidebar is visible

**Steps:**
1. Navigate to `http://localhost:3835/research/event-study`
2. Look at the sidebar navigation

**Expected Result:**
- The "Research" entry in the sidebar is highlighted (active state — typically bold text, a colored left border, or a filled background)
- No other sidebar link shows an active/highlighted state
- The highlight appears without requiring a return click to `/research`

---

### UT-16 — Sidebar Research link highlights for severity-velocity sub-route (regression)

**Type:** regression
**Priority:** P2
**Surface:** sidebar navigation

**Preconditions:**
- Frontend is running at http://localhost:3835
- Sidebar is visible

**Steps:**
1. Navigate to `http://localhost:3835/research/severity-velocity`
2. Look at the sidebar navigation entry for "Research"

**Expected Result:**
- The "Research" sidebar entry is in an active/highlighted state
- No other sidebar entry is highlighted simultaneously

---

### UT-17 — Zero-N cells in severity-velocity matrix show NA, not fabricated numbers (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research/severity-velocity`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/research/severity-velocity?asof=2021-06-30`
2. Wait for the matrix to load
3. Identify any cell that would have few or zero observations (e.g., "Risk-off / Falling" in early data)

**Expected Result:**
- Any cell with zero observations shows "NA", "—", or a "low sample" label — NOT a numeric mean return value
- Any cell with below-minimum sample count shows a partial/NA indicator — NOT a fabricated statistic
- A broken placeholder or "Checking backend…" spinner does NOT persist in any cell after loading completes

---

### UT-18 — Samples page shows readable description for severity-velocity cohort kind (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research/samples`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- The severity-velocity matrix has loaded with at least one non-zero N= chip

**Steps:**
1. Navigate to `http://localhost:3835/research/severity-velocity`
2. Click any non-zero N= chip in the matrix
3. Switch to the new tab that opens at `/research/samples`
4. Read the cohort description or page title shown on the Samples page

**Expected Result:**
- The Samples page shows a human-readable description identifying: the regime family (e.g., "Risk-off"), the velocity sign (e.g., "Rising"), and the horizon (e.g., "5-day")
- The description is NOT a raw JSON dump of parameters
- The description is NOT a generic "samples" label with no context
- The Samples page does NOT show a 404, 422, or 500 error

---

### UT-19 — Navigating from hub to event-study does not trigger other lab fetches (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research` hub → `/research/event-study`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Browser DevTools Network tab is open (press F12, select Network)
- Clear the network log before starting

**Steps:**
1. Navigate to `http://localhost:3835/research` with the Network tab visible
2. Wait for the hub to load
3. Click the "Event Study" lab card on the hub
4. Wait for `/research/event-study` to fully load
5. In the Network tab, search for requests to `/api/research/factor-combination`, `/api/research/regime-setup-pattern`, `/api/research/downtrend-opportunity`, or `/api/research/severity-velocity`

**Expected Result:**
- Network log shows a request to `/api/research/event-study` (the selected lab's endpoint)
- Network log does NOT show concurrent requests to `/api/research/factor-combination`, `/api/research/regime-setup-pattern`, `/api/research/downtrend-opportunity`, or `/api/research/severity-velocity` triggered by navigating to the event-study route
- Only ONE heavy research fetch fires for the selected lab

---

### UT-20 — Research hub is reachable via sidebar Research link (ux)

**Type:** ux
**Priority:** P2
**Surface:** sidebar navigation → `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835` (dashboard)
2. Look at the left sidebar and find the "Research" navigation link
3. Click "Research" in the sidebar

**Expected Result:**
- Browser navigates to `http://localhost:3835/research`
- The hub card grid is displayed with seven lab cards
- The "Research" sidebar entry appears highlighted/active

---

### UT-21 — Severity-velocity lab is reachable within 2 clicks from sidebar (ux)

**Type:** ux
**Priority:** P2
**Surface:** sidebar → `/research` hub → `/research/severity-velocity`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835` (dashboard)
2. Click "Research" in the sidebar (click 1)
3. On the `/research` hub, locate the card for the severity-velocity study (look for a card mentioning "Severity-velocity" or "Severity Velocity × Regime" or similar)
4. Click that card (click 2)

**Expected Result:**
- After click 1: browser is at `http://localhost:3835/research` showing the hub card grid
- After click 2: browser navigates to `http://localhost:3835/research/severity-velocity`
- The severity-velocity matrix loads on the destination page
- Total clicks from dashboard sidebar to the study page: exactly 2

---

### UT-22 — Each hub lab card label is clear and matches its destination page (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/research` hub

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Read the label on each lab card
3. Click the "Factor Lab" card (or equivalently labelled card)
4. Confirm the destination page heading matches the card label
5. Navigate back to `/research`
6. Click the "Severity-velocity" (or similarly named) card
7. Confirm the destination page heading matches the card label

**Expected Result:**
- Each card label on the hub corresponds to the heading shown on the destination lab page
- No card is labelled in a way that is ambiguous or misleading (e.g., a card should not say "Lab 1" without a descriptive name)
- Seven distinct cards are visible, each with a name and a one-line description

---

### UT-23 — All seven research sub-routes are directly deep-linkable (ux)

**Type:** ux
**Priority:** P2
**Surface:** all `/research/*` sub-routes

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Open a new browser tab and navigate directly to `http://localhost:3835/research/factor-lab`
2. Confirm the page loads (not a 404)
3. Open a new browser tab and navigate directly to `http://localhost:3835/research/factor-combination`
4. Confirm the page loads (not a 404)
5. Open a new browser tab and navigate directly to `http://localhost:3835/research/event-study`
6. Confirm the page loads (not a 404)
7. Open a new browser tab and navigate directly to `http://localhost:3835/research/regime-setup-pattern`
8. Confirm the page loads (not a 404)
9. Open a new browser tab and navigate directly to `http://localhost:3835/research/recovery-turn-edge`
10. Confirm the page loads (not a 404)
11. Open a new browser tab and navigate directly to `http://localhost:3835/research/downtrend-opportunity`
12. Confirm the page loads (not a 404)
13. Open a new browser tab and navigate directly to `http://localhost:3835/research/severity-velocity`
14. Confirm the page loads (not a 404)

**Expected Result:**
- All seven sub-routes (`/research/factor-lab`, `/research/factor-combination`, `/research/event-study`, `/research/regime-setup-pattern`, `/research/recovery-turn-edge`, `/research/downtrend-opportunity`, `/research/severity-velocity`) load directly without a 404 error
- Each page shows its respective lab content, not a generic error page

---

### UT-24 — Event-study N= chip count coherence after lab relocation (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/event-study` → `/research/samples`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- `/research/event-study` has loaded with at least one non-zero N= chip

**Steps:**
1. Navigate to `http://localhost:3835/research/event-study`
2. Wait for the study table to load
3. Locate any non-zero N= chip (e.g., "N=47") and note the exact count
4. Click that N= chip
5. Switch to the new tab that opens at `/research/samples`
6. Read the total sample count displayed on the Samples page

**Expected Result:**
- The Samples page total count matches the N count noted in step 3 (e.g., exactly 47)
- No 4xx error appears in the new tab
- The Samples page renders a valid cohort description

---

### UT-25 — Dashboard still loads and charts render after research split (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (dashboard)

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835`
2. Wait for the dashboard to fully load
3. Confirm charts are rendered (not blank boxes or skeleton placeholders)
4. Confirm the current regime label (Risk-on / Neutral / Risk-off) is displayed somewhere on the dashboard

**Expected Result:**
- Dashboard loads without a blank screen or "Checking backend…" message that fails to resolve
- At least one chart renders with data
- The regime label is visible and reads one of: "Risk-on", "Neutral", or "Risk-off"
- No console error related to research routes appears

---

## Test Summary

| ID    | Name                                                               | Type        | Priority | Surface                                     |
|-------|--------------------------------------------------------------------|-------------|----------|---------------------------------------------|
| UT-01 | Research hub page loads as a card grid                             | smoke       | P1       | `/research`                                 |
| UT-02 | Severity-velocity study page loads with matrix                     | smoke       | P1       | `/research/severity-velocity`               |
| UT-03 | Factor Lab sub-route loads independently                           | smoke       | P1       | `/research/factor-lab`                      |
| UT-04 | Event Study sub-route loads independently                          | smoke       | P1       | `/research/event-study`                     |
| UT-05 | Severity-velocity matrix cell values and horizon selector work     | happy-path  | P1       | `/research/severity-velocity`               |
| UT-06 | Verdict card shows honest finding with all three caveats           | happy-path  | P1       | `/research/severity-velocity`               |
| UT-07 | N= chip opens reproducing cohort in a new tab                      | happy-path  | P1       | `/research/severity-velocity` → `/research/samples` |
| UT-08 | Research hub card navigation carries global as-of date             | happy-path  | P1       | `/research` hub                             |
| UT-09 | As-of mode toggle narrows observations                             | happy-path  | P1       | `/research/severity-velocity`               |
| UT-10 | Regime-setup-pattern sub-route loads with pre-split figures        | regression  | P1       | `/research/regime-setup-pattern`            |
| UT-11 | Factor-combination sub-route loads with pre-split figures          | regression  | P1       | `/research/factor-combination`              |
| UT-12 | Downtrend-opportunity sub-route loads                              | regression  | P1       | `/research/downtrend-opportunity`           |
| UT-13 | Recovery-turn-edge sub-route loads                                 | regression  | P1       | `/research/recovery-turn-edge`              |
| UT-14 | Old /research page no longer shows heavy analysis content          | regression  | P1       | `/research`                                 |
| UT-15 | Sidebar Research link highlights for any /research/* sub-route     | regression  | P2       | sidebar navigation                          |
| UT-16 | Sidebar Research link highlights for severity-velocity sub-route   | regression  | P2       | sidebar navigation                          |
| UT-17 | Zero-N cells in severity-velocity matrix show NA                   | validation  | P2       | `/research/severity-velocity`               |
| UT-18 | Samples page shows readable description for severity-velocity kind | validation  | P2       | `/research/samples`                         |
| UT-19 | Hub-to-event-study navigation does not trigger other lab fetches   | validation  | P2       | `/research` hub → `/research/event-study`   |
| UT-20 | Research hub is reachable via sidebar Research link                | ux          | P2       | sidebar → `/research`                       |
| UT-21 | Severity-velocity lab is reachable within 2 clicks from sidebar    | ux          | P2       | sidebar → hub → `/research/severity-velocity` |
| UT-22 | Each hub lab card label is clear and matches destination page      | ux          | P3       | `/research` hub                             |
| UT-23 | All seven research sub-routes are directly deep-linkable           | ux          | P2       | all `/research/*` sub-routes                |
| UT-24 | Event-study N= chip count coherence after lab relocation           | regression  | P1       | `/research/event-study` → `/research/samples` |
| UT-25 | Dashboard still loads and charts render after research split       | regression  | P1       | `/` (dashboard)                             |

**P1 tests must all pass for browser QA verdict to be PASS.**
