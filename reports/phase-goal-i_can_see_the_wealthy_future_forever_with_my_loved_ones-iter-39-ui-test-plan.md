# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39
**Date:** 2026-06-20
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->
<!-- Vague steps like "test the form" or "verify it works" are not acceptable. -->

---

### UT-01 — Dashboard loads with cross-view chart visible (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/` (Dashboard)

**Preconditions:**
- Backend is running at `http://localhost:8835`
- Frontend is running at `http://localhost:3835`

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Wait for the page to fully load (up to 10 seconds)
3. Verify the page heading or logo area is visible in the header
4. Scroll down until a two-pane chart is visible below the at-a-glance figures

**Expected Result:**
- Page renders without a blank white screen or a "Checking backend..." spinner that stays indefinitely
- The Dashboard layout is visible with at least one chart area in view after scrolling
- No full-page error message (e.g., "Failed to load" or "500 Internal Server Error") is present

---

### UT-02 — Cross-view chart bottom pane renders phase bands and severity line at live date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (Dashboard) — cross-view chart bottom pane

**Preconditions:**
- Backend is running at `http://localhost:8835`
- Frontend is running at `http://localhost:3835`
- The page is at the current (live) as-of date (today or the most recent trading date shown by default)

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Wait for the page to fully load (the at-a-glance compact figures near the top should show a regime label such as "Bull" or "Bear")
3. Scroll down past the at-a-glance compact figures and past the top pane of the cross-view chart until the bottom pane of that chart comes into view
4. Observe the bottom pane of the cross-view chart

**Expected Result:**
- The bottom pane shows colored phase bands spanning the horizontal time axis (not a blank/white canvas)
- A numeric scale from 0 to 100 is visible on the vertical axis of the bottom pane (the severity axis)
- A line is drawn over the phase bands representing the filtered P(bear) probability (a value between 0 and 1, or 0–100 depending on scale)
- A vertical marker line is visible at the current as-of date

---

### UT-03 — Bottom pane is visually distinct from the top pane (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (Dashboard) — cross-view chart, both panes

**Preconditions:**
- Backend is running at `http://localhost:8835`
- Frontend is running at `http://localhost:3835`
- Page is at the current (live) as-of date

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Scroll down until both the top pane and the bottom pane of the cross-view chart are in view simultaneously (or view each pane in turn)
3. Observe the top pane: it shows normalized index paths (line series, no colored background bands)
4. Observe the bottom pane: it should show a different type of visualization — colored background bands and a line overlay

**Expected Result:**
- The top pane contains line series showing normalized index price paths (no colored background fills)
- The bottom pane contains colored background phase bands with a line overlay (severity/P(bear))
- The two panes are visually distinct — they do not look identical

---

### UT-04 — Synced zoom: dragging a zoom region on either pane updates both panes (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (Dashboard) — cross-view chart synced zoom

**Preconditions:**
- Backend is running at `http://localhost:8835`
- Frontend is running at `http://localhost:3835`
- Both panes of the cross-view chart are fully rendered (bottom pane shows phase bands, top pane shows index paths)

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Scroll down until both panes of the cross-view chart are visible
3. Note the current x-axis time range shown on both panes (e.g., the earliest and latest dates visible)
4. Click and drag across a sub-region of the top pane's chart area to zoom into a narrower time window (e.g., drag from the center-left to the center-right of the chart)
5. Release the mouse button to apply the zoom
6. Observe both the top pane and the bottom pane immediately after the zoom

**Expected Result:**
- Both the top pane and the bottom pane update their x-axis to show the narrower time window selected
- The x-axis date labels on both panes reflect the same shorter time range
- The bottom pane is still not empty — phase bands and the P(bear) line remain visible within the zoomed range
- The two panes are still visually distinct from each other after zooming

---

### UT-05 — Compact "Market Phase & Severity" at-a-glance figure shows phase label and severity score (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (Dashboard) — compact at-a-glance Market Phase & Severity card

**Preconditions:**
- Backend is running at `http://localhost:8835`
- Frontend is running at `http://localhost:3835`
- Page is at the current (live) as-of date

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Wait for the page to fully load
3. Locate the compact "Market Phase & Severity" figure near the top of the Dashboard (it should be visible without much scrolling, near or below the regime at-a-glance figure)
4. Read the phase label text (e.g., "Recovery", "Distribution", "Accumulation") and the numeric severity score (a number between 0 and 100)

**Expected Result:**
- A phase label text is shown (one of: Recovery, Distribution, Accumulation, Markup, or similar — not blank or "undefined")
- A numeric severity score in the range 0–100 is displayed alongside the phase label
- The figure is not a loading skeleton or a blank placeholder

---

### UT-06 — Early as-of date shows an honestly empty cross-view bottom pane (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/` (Dashboard) — cross-view chart bottom pane at historical as-of

**Preconditions:**
- Backend is running at `http://localhost:8835`
- Frontend is running at `http://localhost:3835`
- The as-of date picker is accessible on the Dashboard

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Locate the as-of date selector (a calendar icon or date display element near the top of the Dashboard)
3. Click the as-of date selector to open the date picker
4. Select the date `2010-01-15` (or the earliest date allowed by the picker if 2010 is not available)
5. Wait for the Dashboard to reload with the new as-of date
6. Scroll down to the cross-view chart bottom pane

**Expected Result:**
- The bottom pane is visually empty — no colored phase bands, no severity line, no P(bear) line (because market-phase history does not exist this far back)
- The bottom pane does not show an error message or a red error state
- The top pane may also be empty or sparse (expected for an early date with limited data)
- The bottom pane canvas is present (not removed from the DOM) — it is simply empty

---

### UT-07 — As-of date change updates both the cross-view chart and the at-a-glance figures (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Dashboard) — as-of selector, cross-view chart, at-a-glance figures

**Preconditions:**
- Backend is running at `http://localhost:8835`
- Frontend is running at `http://localhost:3835`
- The Dashboard has loaded at the current (live) as-of date with data visible

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Wait for the page to fully load — note the current regime label shown in the at-a-glance figure (e.g., "Bull") and the current as-of date shown in the date picker
3. Click the as-of date selector to open the date picker
4. Select the date `2026-06-10` (approximately one week earlier than the current date)
5. Wait for the Dashboard to re-render with data for `2026-06-10`
6. Observe the at-a-glance regime figure and the at-a-glance Market Phase & Severity figure
7. Scroll down and observe the cross-view chart bottom pane

**Expected Result:**
- The as-of date shown in the date picker updates to `2026-06-10`
- The at-a-glance figures may show the same or different values from step 2 (acceptable either way, but values must have updated from the API for that date)
- The cross-view chart bottom pane remains non-empty and still shows phase bands and lines for the new as-of date
- The as-of vertical marker line in the chart moves to `2026-06-10`

---

### UT-08 — Other Dashboard sections remain functional after the cache fix (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Dashboard) — Major-indexes card, stocks summary, navigation links

**Preconditions:**
- Backend is running at `http://localhost:8835`
- Frontend is running at `http://localhost:3835`

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Wait for the page to fully load
3. Verify the Major-indexes card (or equivalent top-of-page market summary card) is visible and shows at least one index (e.g., "SPY", "QQQ", or similar)
4. Click the "Stocks" navigation link in the top header or sidebar
5. Verify the page navigates to `http://localhost:3835/stocks` and a list or table of stocks is visible

**Expected Result:**
- The Major-indexes card is visible with at least one index entry
- The "Stocks" link navigates to the stocks page without a blank screen or error
- The stocks page renders a list of tickers (not a loading spinner that never resolves)

---

### UT-09 — Bottom pane visible below the fold without horizontal scroll (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` (Dashboard) — page layout, cross-view chart positioning

**Preconditions:**
- Browser window is at a typical desktop width (1280px or wider)
- Frontend is running at `http://localhost:3835`

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Without changing the browser window width, scroll vertically downward until the cross-view chart is visible
3. Observe the cross-view chart layout — does it require horizontal scrolling to see both the top and bottom panes?

**Expected Result:**
- The cross-view chart fits within the page width without requiring horizontal scrolling
- Both the top pane and bottom pane are reachable by vertical scrolling only
- The bottom pane's colored phase bands and lines are visible without any additional user action other than scrolling

---

### UT-10 — Cross-view bottom pane content is distinct from the top pane on the same date (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` (Dashboard) — cross-view chart, both panes

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Page is at the current (live) as-of date
- Both panes of the cross-view chart are rendered with data

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Scroll to the cross-view chart so both the top pane and bottom pane are visible
3. Look at the top pane: it should show labeled line series (e.g., "SPY", "QQQ") drawn as thin lines on a neutral background
4. Look at the bottom pane: it should show colored rectangular bands in the background (phase color coding) with at least one line overlay (P(bear))
5. Verify the axis labels differ: the top pane y-axis should show a normalized index value or percentage; the bottom pane y-axis should show a 0–100 severity scale

**Expected Result:**
- The top pane y-axis shows a different scale or label from the bottom pane y-axis
- The top pane background has no colored bands (neutral background)
- The bottom pane background has clearly colored bands (distinguishable colors indicating different market phases)
- A line overlay is visible on the bottom pane that is not present as a background element on the top pane

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Dashboard loads with cross-view chart visible | smoke | P1 | `/` |
| UT-02 | Cross-view bottom pane renders phase bands and severity line at live date | happy-path | P1 | `/` |
| UT-03 | Bottom pane is visually distinct from the top pane | happy-path | P1 | `/` |
| UT-04 | Synced zoom: dragging updates both panes | happy-path | P1 | `/` |
| UT-05 | Compact "Market Phase & Severity" figure shows phase label and severity score | happy-path | P1 | `/` |
| UT-06 | Early as-of date shows honestly empty cross-view bottom pane | validation | P2 | `/` |
| UT-07 | As-of date change updates cross-view chart and at-a-glance figures | regression | P1 | `/` |
| UT-08 | Other Dashboard sections remain functional after cache fix | regression | P1 | `/` |
| UT-09 | Bottom pane visible below the fold without horizontal scroll | ux | P2 | `/` |
| UT-10 | Cross-view bottom pane content is distinct from top pane on same date | ux | P2 | `/` |

**P1 tests (UT-01 through UT-05, UT-07, UT-08) must all pass for browser QA verdict to be PASS.**
