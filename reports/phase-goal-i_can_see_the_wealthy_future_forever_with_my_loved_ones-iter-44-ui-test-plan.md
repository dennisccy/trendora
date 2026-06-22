# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44
**Date:** 2026-06-22
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Dashboard loads with a single market chart (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835 and serving `/api/market-phase` and `/api/regime-history`
- Database is seeded with 2021-2026 history

**Steps:**
1. Navigate to `http://localhost:3835`
2. Wait for all cards to finish loading (no spinner visible)
3. Count the number of market chart cards on the page by looking for chart headings containing the words "Major" or "Regime" or "Cross-view" or "indexes"
4. Look specifically for a standalone card labeled "Major indexes & regime" anywhere on the page

**Expected Result:**
- Page renders without a blank screen, spinner, or error message
- Exactly one market chart card is visible — the two-pane "Regime x phase cross-view" card
- No separate "Major indexes & regime" standalone card appears anywhere on the page

---

### UT-02 — Cross-view card renders both panes (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- Database seeded with 2021-2026 history

**Steps:**
1. Navigate to `http://localhost:3835`
2. Wait for the cross-view card to finish loading
3. Observe the cross-view chart area — look for two vertically stacked chart panes
4. Check that the top pane shows colored bands (regime bands) and line traces (index percent lines)
5. Check that the bottom pane shows colored phase bands and a line overlay

**Expected Result:**
- The cross-view card is present on the page with two visually distinct stacked panes
- Top pane contains colored regime bands and line data
- Bottom pane contains colored phase bands and a line overlay
- Neither pane shows a loading spinner or "No data" message

---

### UT-03 — MajorIndexesCard is absent from the Dashboard (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- Dashboard was previously showing two separate market charts (before iter-44)

**Steps:**
1. Navigate to `http://localhost:3835`
2. Wait for all Dashboard cards to render
3. Scroll the full page from top to bottom
4. Look at each card's heading/title text
5. Specifically search for any card with a title containing "Major" followed by a word like "indexes" or "index"

**Expected Result:**
- The page contains no card titled "Major indexes & regime" or any variant thereof
- The only market-related chart visible is the two-pane cross-view card (the "Regime x phase" card)
- No duplicate index/regime series is visible

---

### UT-04 — Cross-view bottom pane shows severity-velocity line with zero baseline (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — cross-view chart bottom pane

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend serving `/api/market-phase` with `severity_velocity` field populated
- Database has at least 10 dates of history so the velocity warm-up is past
- Dashboard is visible and the cross-view chart has fully loaded

**Steps:**
1. Navigate to `http://localhost:3835`
2. Wait for the cross-view chart to fully render
3. Look at the bottom pane (phase pane) of the cross-view chart
4. Observe whether there is a line overlay in the bottom pane that crosses the horizontal midpoint
5. Look for a dashed horizontal reference line at the zero level of the bottom pane's overlay scale
6. Check that the line oscillates above and below that dashed reference

**Expected Result:**
- The bottom pane contains a line that visibly crosses zero — it goes both above and below the dashed reference line
- A dashed horizontal line marks the zero level on the bottom pane's overlay scale
- No line labeled "Filtered P(bear)" or styled as a 0-to-1 probability curve is visible in the bottom pane

---

### UT-05 — Cross-view chart legend shows "Severity velocity" label (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — cross-view chart legend

**Preconditions:**
- Frontend is running at http://localhost:3835
- Cross-view card has fully loaded

**Steps:**
1. Navigate to `http://localhost:3835`
2. Wait for the cross-view chart to fully render
3. Locate the chart legend (typically below or above the chart panes, showing colored swatches with labels)
4. Read each label in the legend

**Expected Result:**
- The legend contains a swatch labeled "Severity velocity (0-centered; + = worsening)"
- No swatch in the legend is labeled "Filtered P(bear)"
- All other existing legend swatches (index names, regime label) remain present

---

### UT-06 — Cross-view tooltip shows regime label and severity-velocity on hover (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — cross-view hover tooltip

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend serving `/api/market-phase` with `severity_velocity` field and `/api/regime-history`
- Database has 2021-2026 history so mid-history dates have numeric velocity values (not NA)
- Dashboard is visible and the cross-view chart has fully loaded

**Steps:**
1. Navigate to `http://localhost:3835`
2. Wait for the cross-view chart to fully render
3. Move the mouse cursor to hover over a point in the middle of the cross-view chart (approximately the 2023–2024 area of the timeline)
4. Wait for the tooltip to appear (it should appear within 1 second of hovering)
5. Read the tooltip rows — identify each labeled row

**Expected Result:**
- The tooltip appears and contains a row showing a market-regime label (e.g., "Bull", "Bear", "Risk-Off", or similar) alongside a numeric score between 0 and 100 (e.g., "Bull / 72")
- The tooltip contains a row for severity velocity showing a formatted numeric value with a sign prefix (e.g., "+0.44" or "-1.20")
- The tooltip still contains all of the following rows: date, index percent value, phase label, severity value, and P(bear) value

---

### UT-07 — Cross-view tooltip shows "NA" for severity-velocity at earliest dates (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/` — cross-view hover tooltip at warm-up head

**Preconditions:**
- Frontend is running at http://localhost:3835
- Database has at least 10 dates of history
- Cross-view chart is fully loaded

**Steps:**
1. Navigate to `http://localhost:3835`
2. Wait for the cross-view chart to fully render
3. Move the mouse cursor to hover over the leftmost 4 to 5 data points on the cross-view chart timeline (the earliest dates in stored history)
4. Wait for the tooltip to appear
5. Read the severity-velocity row in the tooltip

**Expected Result:**
- The tooltip's severity-velocity row displays "NA" (not a numeric value like "+0.00" or "0.44") for the first several dates where fewer than 5 prior snapshots exist
- No fabricated velocity value is shown — the absence of enough history is represented honestly as "NA"

---

### UT-08 — Cross-view bottom pane phase bands span full history at a historical as-of (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — cross-view bottom pane at historical as-of

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend serving full market-phase history
- Database has at least 2021-2026 history
- The as-of date selector is accessible on the Dashboard

**Steps:**
1. Navigate to `http://localhost:3835`
2. Wait for the Dashboard to fully load
3. Locate the as-of date selector control (a dropdown, calendar widget, or arrow buttons — not a native HTML date input)
4. Select a historical date: use the selector to choose 2022-10-07 (approximately 2–3 years before present)
5. Wait for the cross-view chart to re-render after the date change
6. Observe the bottom pane (phase pane) of the cross-view chart
7. Check whether the colored phase bands extend all the way to the right edge of the chart (past the vertical as-of marker line)
8. Check whether the colored phase bands extend all the way to the left edge of the chart (before 2022-10-07)

**Expected Result:**
- The colored phase bands in the bottom pane extend from the leftmost (earliest stored) date to the rightmost (most recent stored) date — spanning the full chart width
- A vertical line (the as-of marker) appears at 2022-10-07 within the bands, but the bands do NOT stop at that marker
- The area of the chart to the right of the as-of marker still shows phase coloring as display-only context
- No bands are truncated or clipped at the as-of marker position

---

### UT-09 — Cross-view bottom pane renders honestly empty at a pre-history as-of (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/` — cross-view bottom pane at early as-of

**Preconditions:**
- Frontend is running at http://localhost:3835
- Database has 2021-2026 history (no phase data before the database start)
- The as-of date selector is accessible on the Dashboard

**Steps:**
1. Navigate to `http://localhost:3835`
2. Wait for the Dashboard to fully load
3. Locate the as-of date selector control
4. Select the earliest possible date using the selector (the leftmost/earliest option available, typically January 2021 or the database start)
5. Wait for the cross-view chart to re-render
6. Observe the bottom pane (phase pane)

**Expected Result:**
- The bottom pane renders as an empty chart area — no colored phase bands appear
- The pane is clean and clearly has no data (an empty grid or empty axes)
- No fabricated or synthetic phase coloring fills the empty pane

---

### UT-10 — Tooltip still shows P(bear) value on hover (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — cross-view hover tooltip

**Preconditions:**
- Frontend is running at http://localhost:3835
- Database has 2021-2026 history
- Cross-view chart is fully loaded

**Steps:**
1. Navigate to `http://localhost:3835`
2. Wait for the cross-view chart to fully render
3. Move the mouse cursor to hover over a point in the middle of the chart timeline
4. Wait for the tooltip to appear
5. Look for a row in the tooltip labeled "P(bear)" or similar probability label

**Expected Result:**
- The tooltip shows a row with the P(bear) label and a numeric value (e.g., "P(bear): 0.23")
- This row is present in addition to (not replaced by) the new severity-velocity row

---

### UT-11 — Cross-view synced panes share the same date axis (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — cross-view chart

**Preconditions:**
- Frontend is running at http://localhost:3835
- Database has 2021-2026 history
- Cross-view chart is fully loaded with both panes visible

**Steps:**
1. Navigate to `http://localhost:3835`
2. Wait for the cross-view chart to fully render (both the regime pane on top and the phase pane on bottom)
3. Hover the mouse cursor over a date in the top pane (regime pane)
4. Observe whether a corresponding vertical highlight or marker appears in the bottom pane at the same date
5. Move the cursor to a different date in the top pane
6. Observe whether the bottom pane's highlight follows

**Expected Result:**
- When hovering over a date in the top pane, the same date is highlighted in the bottom pane simultaneously
- Moving the cursor along the top pane causes the bottom pane highlight to follow in sync
- The two panes share the same X-axis alignment (the same calendar date maps to the same horizontal position in both panes)

---

### UT-12 — Market-Phase card still shows P(bear) unchanged (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — Market-Phase card

**Preconditions:**
- Frontend is running at http://localhost:3835
- Dashboard has loaded all cards

**Steps:**
1. Navigate to `http://localhost:3835`
2. Wait for all cards to render
3. Locate the "Market Phase" card (separate from the cross-view card — this is the compact summary card)
4. Look at the metrics displayed on this card
5. Verify P(bear) is shown as a value or label within this card

**Expected Result:**
- The Market-Phase card displays a P(bear) label with a numeric value
- The card has NOT been replaced with a severity-velocity line or any other chart
- The card looks the same as it did before iter-44 (P(bear) is unchanged and unmodified)

---

### UT-13 — "At a Glance" card still shows P(bear) and expand works (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — At-a-Glance card

**Preconditions:**
- Frontend is running at http://localhost:3835
- Dashboard has loaded all cards

**Steps:**
1. Navigate to `http://localhost:3835`
2. Wait for all cards to render
3. Locate the compact "At a Glance" or "At-a-Glance" card on the Dashboard
4. Read the metric labels visible without expanding
5. Verify P(bear) is visible in the compact view
6. Click the "Expand" button (or equivalent toggle) on the At-a-Glance card
7. Observe the expanded view

**Expected Result:**
- The At-a-Glance card shows P(bear) in the compact view
- Clicking "Expand" successfully expands the card to a larger view
- The expanded view still shows P(bear) and the same metrics as before iter-44
- No severity-velocity line has been injected into this card

---

### UT-14 — Dashboard has no native date input elements (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835`
2. Wait for the page to fully load
3. Open browser developer tools (press F12)
4. In the Elements/Inspector panel, search for `input[type="date"]` using the search or find functionality
5. Count how many native HTML date input elements are found anywhere on the page

**Expected Result:**
- Zero native HTML `<input type="date">` elements exist on the Dashboard
- The as-of date selector (if visible) is a custom component — a dropdown, a calendar widget with custom styling, or navigation arrows — not a browser-native date picker

---

### UT-15 — Severity-velocity feature is discoverable from the Dashboard (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835`
2. Look at the cross-view chart without hovering — check the legend for any label that communicates the concept of "stress worsening/easing" or "velocity"
3. Move the mouse over the bottom pane of the cross-view chart
4. Read the tooltip that appears
5. Look for the dashed zero reference line in the bottom pane

**Expected Result:**
- Without hovering, the legend swatch labeled "Severity velocity (0-centered; + = worsening)" is clearly visible in the chart legend — a user seeing the chart for the first time can identify what the bottom pane line represents
- On hover, the tooltip provides a clearly labeled "Severity velocity" row with a formatted sign-prefixed value
- The dashed zero reference line in the bottom pane visually anchors the meaning of positive vs. negative velocity
- A new user can understand "above the dashed line = stress worsening, below = stress easing" without additional explanation

---

### UT-16 — Cross-view bottom pane at historical as-of does not show marker-truncated bands (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` — cross-view bottom pane at historical as-of

**Preconditions:**
- Frontend is running at http://localhost:3835
- Database has 2021-2026 history
- As-of date selector is accessible

**Steps:**
1. Navigate to `http://localhost:3835`
2. Wait for the Dashboard to fully load
3. Locate the as-of date selector and choose a date in 2022 (e.g., navigate backwards using the left arrow or select 2022-06-01 from the calendar)
4. Wait for the cross-view chart to update
5. Look at the bottom pane to see if the phase bands appear after the as-of vertical marker
6. Look to see if the phase coloring on the right side of the marker is visually distinct (slightly dimmed or labeled "after as-of") vs the active area to the left

**Expected Result:**
- Phase bands extend visibly past the as-of vertical marker to the right
- The vertical marker line is clearly visible at the selected 2022 date
- The post-marker area shows phase coloring as useful display-only context (the layout is informative, not confusing — the user can see both where they are and what came after)
- There is no abrupt cutoff of phase coloring at the marker position

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Dashboard loads with a single market chart | smoke | P1 | `/` |
| UT-02 | Cross-view card renders both panes | smoke | P1 | `/` |
| UT-03 | MajorIndexesCard is absent from the Dashboard | happy-path | P1 | `/` |
| UT-04 | Cross-view bottom pane shows severity-velocity line with zero baseline | happy-path | P1 | `/` — bottom pane |
| UT-05 | Cross-view chart legend shows "Severity velocity" label | happy-path | P1 | `/` — chart legend |
| UT-06 | Cross-view tooltip shows regime label and severity-velocity on hover | happy-path | P1 | `/` — hover tooltip |
| UT-07 | Cross-view tooltip shows "NA" for severity-velocity at earliest dates | validation | P2 | `/` — hover tooltip |
| UT-08 | Cross-view bottom pane phase bands span full history at a historical as-of | happy-path | P1 | `/` — bottom pane |
| UT-09 | Cross-view bottom pane renders honestly empty at a pre-history as-of | validation | P2 | `/` — bottom pane |
| UT-10 | Tooltip still shows P(bear) value on hover | regression | P1 | `/` — hover tooltip |
| UT-11 | Cross-view synced panes share the same date axis | regression | P1 | `/` — cross-view chart |
| UT-12 | Market-Phase card still shows P(bear) unchanged | regression | P1 | `/` — Market-Phase card |
| UT-13 | "At a Glance" card still shows P(bear) and expand works | regression | P1 | `/` — At-a-Glance card |
| UT-14 | Dashboard has no native date input elements | regression | P1 | `/` |
| UT-15 | Severity-velocity feature is discoverable from the Dashboard | ux | P2 | `/` |
| UT-16 | Cross-view bottom pane at historical as-of does not show marker-truncated bands | ux | P2 | `/` — bottom pane |

**P1 tests must all pass for browser QA verdict to be PASS.**
