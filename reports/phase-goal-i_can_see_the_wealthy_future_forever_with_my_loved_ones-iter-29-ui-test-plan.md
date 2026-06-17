# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29
**Date:** 2026-06-17
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Dashboard loads with new Market Phase card present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Backend is running at `http://localhost:8835`
- At least one snapshot exists in the database (the seed data is sufficient)

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Wait for the page to fully load (all cards visible, no loading spinners remaining)
3. Scroll down past the "Major Indexes & Regime" card
4. Locate the card with heading "Market Phase & Severity"

**Expected Result:**
- The Dashboard page renders without a blank screen or JavaScript error overlay
- The "Major Indexes & Regime" card is visible near the top of the page
- A card titled "Market Phase & Severity" appears directly below the "Major Indexes & Regime" card
- The Market Phase card header shows a colored phase badge (e.g., "Expansion") and a P(bear) badge (e.g., "P(bear) 0.05")
- No "Market phase unavailable" error alert is visible under normal conditions

---

### UT-02 — Market Phase card body displays severity score and component breakdown (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Backend is running at `http://localhost:8835`
- Database contains snapshots covering a recent trading date (2024 or later)

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Wait for the "Market Phase & Severity" card to finish loading (skeleton disappears)
3. Inspect the card body for a numeric severity score in the format "X.XX / 100 severity"
4. Scroll within the card body to see the component breakdown table

**Expected Result:**
- A numeric severity score is visible in the format "X.XX / 100 severity" (e.g., "28.75 / 100 severity") — not "NA" or blank
- A "Drawdown" percentage is visible (e.g., "Drawdown: -5.2%")
- An "Off trough" percentage is visible (e.g., "Off trough: +3.1%")
- The component breakdown table is visible with exactly five labeled rows:
  1. "Drawdown depth" with a numeric Value and a numeric Contribution
  2. "Time underwater" with a numeric Value and a numeric Contribution
  3. "Market regime (stored)" with a numeric Value and a numeric Contribution
  4. "Breadth below 200-DMA" with a numeric Value and a numeric Contribution
  5. "VIX stress gate" with a numeric Value and a numeric Contribution
- No row shows a blank or "NA" value for the latest date

---

### UT-03 — Loading skeleton appears before data arrives (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Backend is running at `http://localhost:8835`

**Steps:**
1. Open Chrome DevTools (press F12), click the "Network" tab, set throttling to "Slow 3G" using the throttle dropdown
2. Navigate to `http://localhost:3835/`
3. Immediately watch the "Market Phase & Severity" card area before data loads
4. Reset throttling to "No throttling" after observing the loading state

**Expected Result:**
- Before the backend response arrives, the Market Phase card body shows an animated gray skeleton block (height approximately 176 px) — not a blank white area, not a flash of numbers, and not a fabricated phase label
- After data loads, the skeleton is replaced by the phase badge, severity score, and component breakdown

---

### UT-04 — Phase badge color is green for Expansion on a recent date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Backend is running at `http://localhost:8835`
- Database contains snapshots for late 2024 (the seed covers this period)

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Confirm the page is showing the latest available date (check the date stamp in the "Market Phase & Severity" card header, e.g., "as of 2025-xx-xx" or the most recent trading day)
3. Look at the phase badge in the card header row

**Expected Result:**
- The phase badge displays the label "Expansion" (or "Recovery")
- The badge color is green — not amber and not red
- The P(bear) badge in the same header row shows a low value (e.g., "P(bear) 0.05" or similar near-zero value) and is colored green

---

### UT-05 — Navigating global as-of to 2022-10-07 shows Bear phase with red badge (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Backend is running at `http://localhost:8835`
- Database contains seed snapshots covering the 2022 bear market period (seed covers 2021–2026)

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Locate the global as-of date navigation control on the Dashboard (the date picker or prev/next arrow buttons in the page header or the as-of panel)
3. Step the date back to 2022-10-07 (use the date input or the backward arrow buttons; the URL should update to include `?asof=2022-10-07`)
4. Wait for the "Market Phase & Severity" card to reload its data (skeleton may briefly appear)
5. Inspect the phase badge in the card header

**Expected Result:**
- The URL contains `?asof=2022-10-07`
- The phase badge displays the label "Bear" (not "Expansion", "Pullback", "Correction", or "Recovery")
- The badge color is red — not green and not amber
- The severity score in the card body is a high number (70 or above out of 100)
- The P(bear) badge in the header shows a high value near "P(bear) 1.00" and is colored red
- The drawdown percentage is a large negative number (e.g., below -20%)

---

### UT-06 — Observation vector chips appear below the breakdown table (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Backend is running at `http://localhost:8835`
- Database contains at least several weeks of snapshots so the Hamilton filter has observations to show

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Wait for the "Market Phase & Severity" card to fully load
3. Scroll to the bottom of the card body, below the five-row component breakdown table
4. Locate the row labeled "Filter observations · drives P(bear)"
5. Hover the mouse cursor over one of the date chips in that row

**Expected Result:**
- A row labeled "Filter observations · drives P(bear)" is visible below the component breakdown table
- The row contains multiple date-labeled chips, each showing a stress reading (e.g., a date and a numeric value)
- When hovering a chip, a tooltip appears showing at minimum a stress value and a per-date P(bear) reading
- The total number of observations is disclosed (e.g., "Showing last 10 of 45 observations" or a similar count label)

---

### UT-07 — Insufficient-history date shows explicit NA message, not fabricated data (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Backend is running at `http://localhost:8835`
- The seed data begins around 2021-01-04 (use a date in early January 2021 when few bars exist)

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Use the global as-of date control to navigate to the date `2021-01-05`
3. Wait for the "Market Phase & Severity" card to respond (skeleton may appear briefly)
4. Inspect the card body

**Expected Result:**
- The card body does NOT show a numeric severity score (e.g., "28.75 / 100 severity")
- The card body does NOT show a phase badge with a specific label ("Expansion", "Bear", etc.) as a computed value
- The card body shows the message "Not enough history to derive a market phase for this date" (exact or close wording) with a minimum-bar count figure (e.g., "requires at least 252 bars")
- The P(bear) badge in the header is either absent or shows "N/A" — no fabricated probability

---

### UT-08 — Backend-unreachable shows styled alert in Market Phase card (error)

**Type:** error
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Backend at `http://localhost:8835` is NOT running (stop it or use DevTools to block the request)

**Steps:**
1. Stop the backend server (or open Chrome DevTools, go to the "Network" tab, right-click on a `market-phase` API request and select "Block request URL")
2. Navigate to `http://localhost:3835/`
3. Wait several seconds for the request to fail
4. Inspect the "Market Phase & Severity" card body

**Expected Result:**
- The card body shows an amber (yellow/orange) warning alert box
- The alert contains the text "Market phase unavailable" (exact or close wording)
- The alert contains instructions such as "confirm the backend is running and reload"
- The card does NOT show a blank white area, a JavaScript crash, or any fabricated phase/severity/probability values
- Other Dashboard cards (e.g., "Major Indexes & Regime") show their own error state independently — the Market Phase card error does not crash the whole page

---

### UT-09 — Market Phase card has no independent date control of its own (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Backend is running at `http://localhost:8835`

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Wait for the page to fully load
3. Visually inspect the entire "Market Phase & Severity" card — header, body, footer — for any date input, date picker, calendar icon, or text field that accepts a date
4. Also inspect the area between the "Market Phase & Severity" card and the "Major Indexes & Regime" card for any new date controls

**Expected Result:**
- No date input, date picker, calendar widget, or date-related text field exists anywhere inside the "Market Phase & Severity" card
- No new date control appears between the two cards or anywhere on the Dashboard that was not there before this iteration
- The only date controls on the Dashboard are the existing global as-of navigation controls (prev/next arrows, year/month dropdowns, or date input) that were present before this iteration

---

### UT-10 — Changing global as-of updates Market Phase card without page reload (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Backend is running at `http://localhost:8835`
- Database contains seed data for both 2022 and 2024

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Record the phase label shown in the "Market Phase & Severity" card header badge (e.g., "Expansion")
3. Use the global as-of date control to change the date to `2022-07-15` (use prev arrows or the date input field; do NOT press F5 or reload the page)
4. Wait for the card to update (a loading skeleton may appear briefly inside the card)
5. Record the new phase label in the card header badge

**Expected Result:**
- The URL changes to include `?asof=2022-07-15` without a full page reload
- The "Market Phase & Severity" card updates its content to reflect 2022-07-15 data without the user navigating away or pressing reload
- The phase label changes from what it was at the latest date (expected "Expansion") to "Bear"
- The severity score in the card body increases significantly compared to the latest-date value
- The P(bear) value in the header badge increases toward 1.00

---

### UT-11 — Market Phase card date is consistent with URL as-of parameter on direct load (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Backend is running at `http://localhost:8835`
- Database contains seed snapshots for 2022

**Steps:**
1. Navigate directly to `http://localhost:3835/?asof=2022-07-15` (paste the full URL including `?asof=2022-07-15` into the browser address bar and press Enter)
2. Wait for the page to fully load and the "Market Phase & Severity" card to show data
3. Record the as-of date stamp shown inside the card header (e.g., "as of 2022-07-15")
4. Record the phase label badge (expected: "Bear")
5. Refresh the page (press F5)
6. Wait for the page to fully reload
7. Verify the phase label and date stamp match the pre-refresh values

**Expected Result:**
- On first load, the card header shows "as of 2022-07-15" and the phase badge shows "Bear"
- After refreshing, the phase badge still shows "Bear" and the as-of date stamp still shows "2022-07-15"
- The severity score is the same numeric value before and after the refresh (deterministic result)
- The URL remains `http://localhost:3835/?asof=2022-07-15` after refresh

---

### UT-12 — Major Indexes & Regime card is unaffected by this iteration (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Backend is running at `http://localhost:8835`
- Database contains seed snapshots for 2024

**Steps:**
1. Navigate to `http://localhost:3835/?asof=2024-12-31`
2. Wait for the page to fully load
3. Locate the "Major Indexes & Regime" card near the top of the Dashboard
4. Verify all index charts (SPY, QQQ, and/or other standard indexes) are visible with price charts
5. Verify the regime label and regime score are displayed in that card
6. Verify the card layout and styling appear normal with no new buttons, badges, or controls added to it

**Expected Result:**
- The "Major Indexes & Regime" card renders with the same layout as before this iteration
- Index price charts are visible and not blank
- The regime label (e.g., "Risk-On") and score are visible in that card
- No new UI controls appear inside the "Major Indexes & Regime" card
- The card does not show an error state under normal conditions

---

### UT-13 — Regime label in Market Phase card matches Major Indexes card for the same date (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Backend is running at `http://localhost:8835`
- Database contains snapshots for 2024-12-31

**Steps:**
1. Navigate to `http://localhost:3835/?asof=2024-12-31`
2. Wait for the page to fully load
3. In the "Major Indexes & Regime" card, read and note the regime label (e.g., "Risk-On", "Risk-Off", or similar)
4. Scroll down to the "Market Phase & Severity" card
5. In the "Market Phase & Severity" card's component breakdown table, locate the row labeled "Market regime (stored)"
6. Read the value in the "Value" column for that row

**Expected Result:**
- The regime label or score shown in the "Market Phase & Severity" card breakdown table for "Market regime (stored)" is consistent with the regime label shown in the "Major Indexes & Regime" card
- There is no contradiction between the two cards for the same as-of date (J-06 coherence)

---

### UT-14 — Stocks leaderboard still works after this iteration (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Backend is running at `http://localhost:8835`
- Database contains at least one stock with snapshots

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Wait for the page to fully load
3. Verify the stocks table/leaderboard is visible with at least one row
4. Verify a stock score or ranking is displayed for at least one row
5. Click on any stock ticker link to open the stock detail page
6. Verify the stock detail page loads without a blank screen or error

**Expected Result:**
- The `/stocks` page renders normally with a visible leaderboard containing stock rows
- Clicking a ticker navigates to `/stocks/<TICKER>` and that page loads without error
- No JavaScript crash or "Market Phase" error appears on the stocks page
- Stock scores and setups are displayed as before this iteration

---

### UT-15 — Market Phase card is discoverable from the Dashboard without scrolling past unrelated content (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Backend is running at `http://localhost:8835`

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Look at the Dashboard without scrolling — note what is visible in the initial viewport
3. Scroll down slowly until you reach the "Market Phase & Severity" card
4. Note how much scrolling was required to reach it and whether the card heading is clearly visible

**Expected Result:**
- The "Market Phase & Severity" card is reachable by scrolling down from the top of the Dashboard (no navigation to a new page or tab required)
- The card heading "Market Phase & Severity" is clearly readable in the card header
- The phase badge label (e.g., "Expansion") and the P(bear) badge (e.g., "P(bear) 0.05") are visible in the card header without needing to expand or toggle anything
- A new user encountering this card for the first time can understand it shows a market cycle state (the heading and badge labels are self-explanatory)

---

### UT-16 — Amber badge for Pullback phase is visually distinct from green and red (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Backend is running at `http://localhost:8835`
- Database contains seed snapshots that include a Pullback date (explore dates in 2023 if needed; the phase label will guide you)

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Use the global as-of date control to navigate backward through dates in 2023 (e.g., try `2023-03-15`, `2023-06-01`, `2023-10-01`) until the phase badge shows "Pullback"
3. Note the badge color at a Pullback date
4. Navigate to a recent 2024/2025 date and note the badge color for "Expansion"
5. Navigate to `2022-10-07` and note the badge color for "Bear"

**Expected Result:**
- At a Pullback date, the phase badge color is amber (yellow-orange) — visually distinct from both the green used for Expansion/Recovery and the red used for Correction/Bear
- The three colors (green, amber, red) are each clearly distinguishable at a glance without needing to read the label text to tell them apart

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Dashboard loads with new Market Phase card present | smoke | P1 | `/` |
| UT-02 | Market Phase card body displays severity score and component breakdown | smoke | P1 | `/` |
| UT-03 | Loading skeleton appears before data arrives | smoke | P1 | `/` |
| UT-04 | Phase badge color is green for Expansion on a recent date | happy-path | P1 | `/` |
| UT-05 | Navigating global as-of to 2022-10-07 shows Bear phase with red badge | happy-path | P1 | `/` |
| UT-06 | Observation vector chips appear below the breakdown table | happy-path | P1 | `/` |
| UT-07 | Insufficient-history date shows explicit NA message, not fabricated data | validation | P2 | `/` |
| UT-08 | Backend-unreachable shows styled alert in Market Phase card | error | P2 | `/` |
| UT-09 | Market Phase card has no independent date control of its own | validation | P2 | `/` |
| UT-10 | Changing global as-of updates Market Phase card without page reload | happy-path | P1 | `/` |
| UT-11 | Market Phase card date is consistent with URL as-of parameter on direct load | happy-path | P1 | `/` |
| UT-12 | Major Indexes & Regime card is unaffected by this iteration | regression | P1 | `/` |
| UT-13 | Regime label in Market Phase card matches Major Indexes card for the same date | regression | P1 | `/` |
| UT-14 | Stocks leaderboard still works after this iteration | regression | P1 | `/stocks` |
| UT-15 | Market Phase card is discoverable from the Dashboard without scrolling past unrelated content | ux | P2 | `/` |
| UT-16 | Amber badge for Pullback phase is visually distinct from green and red | ux | P3 | `/` |

**P1 tests (UT-01 through UT-06, UT-10 through UT-14) must all pass for browser QA verdict to be PASS.**
