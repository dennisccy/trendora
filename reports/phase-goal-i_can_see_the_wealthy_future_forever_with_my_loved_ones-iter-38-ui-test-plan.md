# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38
**Date:** 2026-06-20
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

---

### UT-01 — Dashboard loads without blank screen or crash (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Backend is running at `http://localhost:8835`
- Database contains at least one daily snapshot

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Wait up to 10 seconds for the page to fully render

**Expected Result:**
- Page renders without a blank white screen or unhandled error boundary
- At least one visible heading or card element is present in the viewport
- Browser console does not show an uncaught React render error

---

### UT-02 — Compact summary row is the first visible content at first paint (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running
- Dashboard has not been opened in this browser tab before (open in a fresh incognito window or clear local storage with `localStorage.clear()` in the browser console before navigating)

**Steps:**
1. Open a new incognito browser window
2. Navigate to `http://localhost:3835/`
3. Without scrolling, observe what is visible in the initial viewport

**Expected Result:**
- A "Market Regime" figure is visible at the top of the page showing a non-empty text label (e.g., "Risk-On", "Risk-Off") and a numeric score between 0 and 100
- A "Market Phase & Severity" figure is visible at the top of the page showing a phase badge (e.g., "Contraction", "Expansion"), a numeric severity value between 0 and 100, and a bear-probability chip
- No breadth metrics card, no "Top Sectors" card, no "Candidate Counts" card, and no "Top Themes" card is visible without scrolling

---

### UT-03 — Market Regime compact figure shows label and score (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running
- Database contains snapshots for the current as-of date

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Locate the "Market Regime" figure near the top of the page (before any chart)
3. Read the displayed regime label and numeric score

**Expected Result:**
- The figure displays a non-empty regime label such as "Risk-On" or "Risk-Off" (not blank, not "undefined", not "null")
- A numeric score is displayed alongside the label, formatted as a whole number between 0 and 100 (e.g., "74")
- No loading spinner persists after the page finishes loading

---

### UT-04 — Market Regime component breakdown expands inline (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running
- "Market Regime" compact figure is visible at the top of the Dashboard

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Locate the "Why this regime — component breakdown" disclosure link or toggle directly below the "Market Regime" figure
3. Click that disclosure link or toggle

**Expected Result:**
- A breakdown section expands inline below the "Market Regime" figure without navigating away from the page
- The expanded section shows named driver rows (e.g., component names such as "Momentum", "Breadth", "VIX" with associated sub-scores or weights)
- The disclosure remains expanded if the rest of the page is scrolled
- No full-page navigation or modal dialog appears

---

### UT-05 — Market Phase & Severity compact figure shows phase badge, severity, and P(bear) (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running
- Database contains snapshots covering enough history for causal phase computation

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Locate the "Market Phase & Severity" figure near the top of the page (alongside the "Market Regime" figure)
3. Read the phase badge text, the numeric severity, and the bear-probability chip

**Expected Result:**
- A phase badge is displayed with a non-empty label (e.g., "Contraction", "Expansion", "Recovery") — not blank or "N/A"
- A numeric severity between 0 and 100 is shown
- A bear-probability chip (e.g., "P(bear): 23%") is visible next to or below the severity
- No loading spinner persists

---

### UT-06 — Market Phase & Severity component breakdown expands inline (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running
- "Market Phase & Severity" compact figure is visible at the top of the Dashboard

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Locate the "Why this phase — component breakdown" disclosure link or toggle directly below the "Market Phase & Severity" figure
3. Click that disclosure link or toggle

**Expected Result:**
- A breakdown section expands inline below the "Market Phase & Severity" figure without navigating away from the page
- The expanded section lists named severity-component rows (e.g., component names with associated numeric contributions)
- No full-page navigation or modal dialog appears

---

### UT-07 — Cross-view chart card is present and renders below Major-indexes (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running
- Dashboard data has loaded

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Scroll down past the compact summary figures and the Major-indexes chart
3. Look for a card titled "Regime x phase cross-view" or "Regime × phase cross-view"

**Expected Result:**
- A card with that title is present between the Major-indexes card and the "More detail" section
- The card body shows a rendered chart (not a loading skeleton, not a blank area)
- Two stacked chart panes are visible inside the card

---

### UT-08 — Cross-view chart top pane shows regime bands over index lines (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running
- Cross-view chart card is visible (scroll down from compact summary)

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Scroll down to the "Regime × phase cross-view" card
3. Observe the top pane (pane 0) of the chart

**Expected Result:**
- The top pane shows normalized-percentage index lines (at least one coloured line is visible)
- Coloured background bands representing market regimes are visible behind the index lines
- A vertical as-of marker line is present in the top pane at the current as-of date

---

### UT-09 — Cross-view chart bottom pane shows phase bands, severity line, and P(bear) line (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running
- Cross-view chart card is visible

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Scroll down to the "Regime × phase cross-view" card
3. Observe the bottom pane (pane 1) of the chart

**Expected Result:**
- The bottom pane shows the same normalized-percentage index lines as the top pane
- Coloured background bands representing market phases are visible behind the index lines (different colour scheme from regime bands)
- A 0–100 severity line is plotted (a distinct line that moves between 0 and 100)
- A P(bear) line is plotted (a second distinct line, often lower than severity)
- A vertical as-of marker line is visible in the bottom pane at the same date as the top pane marker

---

### UT-10 — Cross-view chart synchronized zoom: scrolling top pane moves both panes (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running
- Cross-view chart card is fully in viewport (scroll so both panes are visible)

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Scroll down so the "Regime × phase cross-view" card is fully in view
3. Note the date range visible on the x-axis of the top pane (e.g., the leftmost and rightmost date labels)
4. Place your mouse cursor on the top pane and scroll the mouse wheel inward (zoom in) to narrow the visible date range
5. After the top pane adjusts, observe the bottom pane's x-axis date labels

**Expected Result:**
- The top pane zooms in to a narrower date range (x-axis labels change to a shorter window)
- The bottom pane's x-axis labels change to match the same narrower date window as the top pane
- Both panes display the same leftmost and rightmost date after the zoom

---

### UT-11 — "More detail" section is collapsed by default (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Fresh incognito window (no persisted expand state) or local storage cleared

**Steps:**
1. Open a new incognito browser window
2. Navigate to `http://localhost:3835/`
3. Scroll to the bottom of the visible page content below the cross-view chart
4. Look for a "More detail" section header or button

**Expected Result:**
- A "More detail" section header or button is present below the cross-view chart
- The section is collapsed (breadth metrics, Candidate Counts, Top Sectors, Top Themes, and Market Phase detail card are NOT visible)
- No content from those cards is rendered in the DOM in an expanded state

---

### UT-12 — "More detail" expands to show all supporting cards (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running
- "More detail" section is collapsed (default state)

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Scroll to the "More detail" section header below the cross-view chart
3. Click the "More detail" section header or its expand button
4. Wait 500 ms for the expand animation to complete
5. Observe the content that becomes visible

**Expected Result:**
- The section expands and all five supporting areas become visible: breadth metrics card, Candidate Counts card, Top Sectors card, Top Themes card, and the full Market Phase & Severity detail card
- Each visible card shows data (not empty placeholders or spinners)
- No page navigation occurs

---

### UT-13 — "More detail" persists expand state across page reload (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Scroll to the "More detail" section header
3. Click the section header to expand it
4. Reload the page (press F5 or Cmd+R)
5. After the page reloads, scroll to the same position

**Expected Result:**
- The "More detail" section is still expanded after the reload (the five supporting cards are visible without clicking again)
- Next, click the "More detail" section header to collapse it
- Reload the page again (F5 or Cmd+R)
- After the reload, the "More detail" section remains collapsed (the five supporting cards are NOT visible)

---

### UT-14 — Cross-view card hide toggle persists across reload (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running
- Cross-view chart card is visible

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Scroll to the "Regime × phase cross-view" card
3. Locate the hide toggle on that card (typically an "X", eye icon, or "Hide" button in the card header)
4. Click the hide toggle to dismiss the chart
5. Verify the cross-view chart disappears from view
6. Reload the page (F5 or Cmd+R)

**Expected Result:**
- After the reload, the cross-view chart remains hidden (the card is not re-rendered)
- The compact summary figures and "More detail" section are still visible
- To restore: locate any "Show cross-view" control (if provided) or clear local storage and reload

---

### UT-15 — Market Phase detail card inside "More detail" uses correct phase band colours (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running
- "More detail" section is expanded (click "More detail" header if needed)

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Click the "More detail" section header to expand it
3. Locate the full "Market Phase & Severity" detail card within the expanded section
4. Observe the phase-timeline SVG bands inside that card

**Expected Result:**
- Each phase band in the SVG timeline is coloured with a posture-appropriate tone:
  - Positive / expansion phases show a green-toned band
  - Warning / contraction phases show an amber/orange-toned band
  - Negative / bear phases show a red-toned band
- No band is blank, white, or grey (which would indicate a missing colour mapping)
- The colours match those used for the phase bands in the cross-view chart bottom pane

---

### UT-16 — Hover tooltip on cross-view bottom pane shows date, index values, phase, severity, P(bear) (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running
- Cross-view chart card is visible and fully rendered (no skeleton)

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Scroll to the "Regime × phase cross-view" card
3. Move the mouse cursor slowly across the bottom pane (pane 1) of the chart and hold it over a data point
4. Observe any tooltip or legend that appears

**Expected Result:**
- A tooltip or crosshair legend appears showing the hovered date (formatted as a date string, e.g., "2025-06-15")
- The tooltip includes at least one index percentage value
- The tooltip includes the phase label for that date (e.g., "Contraction")
- The tooltip includes a numeric severity value
- The tooltip includes a P(bear) numeric value (e.g., "P(bear): 0.18" or "18%")

---

### UT-17 — Phase summary shows honest-empty state when as-of date has no causal history (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend and backend running
- As-of date calendar is available (the global date selector at the top of the Dashboard)
- The earliest available phase history is known (typically after 2021-10-01 for a freshly seeded database)

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Click the as-of date selector (global date picker in the page header or Dashboard top)
3. Select a date well before phase history exists, such as 2020-01-15
4. Wait for the Dashboard to refresh

**Expected Result:**
- The "Market Phase & Severity" compact figure does NOT display a fabricated phase label or fabricated score
- Instead it displays a message indicating insufficient history, such as "Not enough history", "Reported NA", or similar explicit empty-state text
- The cross-view bottom pane shows no phase-coloured bands and no severity or P(bear) lines for dates before phase history begins
- No JavaScript error or blank crash is displayed

---

### UT-18 — Global as-of date change updates both compact summary figures (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running
- Database contains snapshots for at least two different historical dates

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Note the regime label shown in the "Market Regime" compact figure (e.g., "Risk-On")
3. Note the phase label shown in the "Market Phase & Severity" compact figure (e.g., "Expansion")
4. Click the global as-of date selector
5. Select a different historical date where you expect a different regime (e.g., during 2022-10-15 which was a bear-market period)
6. Wait for the Dashboard to refresh

**Expected Result:**
- The "Market Regime" figure updates to show the regime label for the newly selected date (e.g., "Risk-Off")
- The "Market Phase & Severity" figure updates to show the phase and severity for the newly selected date
- Both compact figures reflect the newly selected as-of date (not the previous values)
- Both chart panes update their as-of marker position and band data to match the new date

---

### UT-19 — Cross-view chart loading skeleton appears before data arrives (smoke)

**Type:** smoke
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend and backend running
- Network throttle can be simulated in Chrome DevTools (open DevTools > Network tab > set throttle to "Slow 3G")

**Steps:**
1. Open Chrome DevTools (F12)
2. Navigate to the Network tab and set network throttle to "Slow 3G"
3. Navigate to `http://localhost:3835/`
4. Immediately observe the area where the cross-view chart should appear (below the Major-indexes card)

**Expected Result:**
- Before chart data arrives, a pulsing grey skeleton placeholder of approximately the same height as the two-pane chart (around 28rem tall) is visible in the card area
- Once data arrives, the skeleton is replaced by the rendered two-pane chart
- No blank white area or unrendered gap appears in the card's place

---

### UT-20 — Prior Dashboard cards in "More detail" section still function after expand (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running
- "More detail" section expanded by clicking its header

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Click the "More detail" section header to expand it
3. Locate the "Top Sectors" card in the expanded section and verify it shows a list of sector names and associated data
4. Locate the "Top Themes" card and verify it shows theme names and associated data
5. Locate the "Candidate Counts" card and verify it shows numeric count values
6. Locate the breadth metrics card and verify it shows breadth indicators (e.g., advance-decline values or similar metrics)

**Expected Result:**
- "Top Sectors" card shows at least one row with a sector name and a numeric value (not blank)
- "Top Themes" card shows at least one row with a theme name and a numeric value (not blank)
- "Candidate Counts" card shows numeric count values (not blank or zero across all fields for a normal risk-on date)
- Breadth metrics card shows at least one named metric and its value
- No card shows an error state or an empty UI placeholder without an explicit empty-data reason

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Dashboard loads without blank screen or crash | smoke | P1 | `/` |
| UT-02 | Compact summary row is the first visible content at first paint | smoke | P1 | `/` |
| UT-03 | Market Regime compact figure shows label and score | happy-path | P1 | `/` |
| UT-04 | Market Regime component breakdown expands inline | happy-path | P1 | `/` |
| UT-05 | Market Phase & Severity figure shows badge, severity, and P(bear) | happy-path | P1 | `/` |
| UT-06 | Market Phase & Severity component breakdown expands inline | happy-path | P1 | `/` |
| UT-07 | Cross-view chart card is present and renders below Major-indexes | happy-path | P1 | `/` |
| UT-08 | Cross-view chart top pane shows regime bands over index lines | happy-path | P1 | `/` |
| UT-09 | Cross-view chart bottom pane shows phase bands, severity line, P(bear) line | happy-path | P1 | `/` |
| UT-10 | Cross-view chart synchronized zoom moves both panes | happy-path | P1 | `/` |
| UT-11 | "More detail" section is collapsed by default | smoke | P1 | `/` |
| UT-12 | "More detail" expands to show all supporting cards | happy-path | P1 | `/` |
| UT-13 | "More detail" persists expand state across page reload | happy-path | P1 | `/` |
| UT-14 | Cross-view card hide toggle persists across reload | happy-path | P1 | `/` |
| UT-15 | Market Phase detail card inside "More detail" uses correct phase band colours | regression | P1 | `/` |
| UT-16 | Hover tooltip on bottom pane shows date, index values, phase, severity, P(bear) | happy-path | P1 | `/` |
| UT-17 | Phase summary shows honest-empty state when as-of has no causal history | validation | P2 | `/` |
| UT-18 | Global as-of date change updates both compact summary figures | regression | P1 | `/` |
| UT-19 | Cross-view chart loading skeleton appears before data arrives | smoke | P2 | `/` |
| UT-20 | Prior Dashboard cards in "More detail" section still function after expand | regression | P1 | `/` |

**P1 tests must all pass for browser QA verdict to be PASS.**
