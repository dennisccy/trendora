# Phase goal-i_can_see_the_wealthy_future-iter-4 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-4
**Date:** 2026-05-30
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3836

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- All routes are relative to http://localhost:3836. -->
<!-- Backend API tests live in reports/qa/...-test-plan.md (TC-01..TC-12) and are NOT duplicated here. -->

---

### UT-01 — Stock Detail page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks/NVDA`

**Preconditions:**
- Frontend running at http://localhost:3836
- Backend running and seeded; NVDA is in the scanned universe

**Steps:**
1. Navigate to `http://localhost:3836/stocks/NVDA`
2. Wait for the loading skeleton (pulsing grey cards) to disappear

**Expected Result:**
- Page heading shows "NVDA"
- The subtitle "Stock detail — the three explainable scores (identical to the leaderboard; single source of truth)" is visible
- A "Back to leaderboard" link is visible in the top-right
- Four cards are visible top-to-bottom: the setup/reason header card, a card with "Themes" and "Invalidation" labels, a "Price & moving averages" card, and a row of three score cards
- No red error card and no blank screen; no console errors

---

### UT-02 — User can study the price candle chart with MA overlays and volume (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/[ticker]` → `PriceChart`

**Preconditions:**
- Backend running and seeded with NVDA price history

**Steps:**
1. Navigate to `http://localhost:3836/stocks`
2. Click the row labelled "NVDA" in the leaderboard table
3. Confirm the URL is now `http://localhost:3836/stocks/NVDA`
4. Locate the "Price & moving averages" card
5. Inspect the chart canvas inside that card

**Expected Result:**
- URL is `http://localhost:3836/stocks/NVDA`
- The "Price & moving averages" card header shows a caption like "1356 bars · as of 2026-05-29" (a positive bar count followed by "bars · as of " and a date) in monospace text
- The chart area (~h-80, full width) paints visible green (up) and red (down) candlesticks — NOT a blank/empty box
- Four coloured moving-average lines are drawn over the candles; each line begins after an initial warm-up gap (no MA line over the earliest bars)
- A volume histogram (muted/faint bars) is pinned along the bottom of the chart pane
- A legend below the chart reads: "Candles (up / down)", "20-DMA", "50-DMA", "150-DMA", "200-DMA", and "Volume"

---

### UT-03 — Theme chips render and navigate to the Themes page (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/[ticker]` → `ThemeAndInvalidationCard`

**Preconditions:**
- Backend running; NVDA is a member of at least one configured theme

**Steps:**
1. Navigate to `http://localhost:3836/stocks/NVDA`
2. Locate the card with the "Themes" label (uppercase, top-left of the second card)
3. Confirm theme chips appear under the "Themes" label
4. Click the chip labelled "Semiconductors"

**Expected Result:**
- Under "Themes", clickable accent-coloured chips render, e.g. "Ai Data Centre", "Semiconductors", "Megacap Leaders"
- Each chip is a focusable link (shows a focus ring on Tab) and changes background on hover
- After clicking "Semiconductors", the browser navigates to `http://localhost:3836/themes`

---

### UT-04 — Concrete invalidation level renders verbatim (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/[ticker]` → `ThemeAndInvalidationCard`

**Preconditions:**
- Backend running; NVDA has sufficient history to compute the 50-DMA

**Steps:**
1. Navigate to `http://localhost:3836/stocks/NVDA`
2. Locate the "Invalidation" label (uppercase, top-right of the second card)
3. Read the note directly under "Invalidation"

**Expected Result:**
- The note reads in plain language: "Invalid below the 50-DMA at $<level>" (e.g. "Invalid below the 50-DMA at $198.73"), with a concrete dollar value
- The note renders in muted (grey) text, NOT amber
- The dollar level is a real number — no "NA", no blank, no "$0.00" placeholder

---

### UT-05 — Invalidation NA state on short history (validation / no-fabrication)

**Type:** validation
**Priority:** P2
**Surface:** `/stocks/[ticker]` → invalidation note

**Preconditions:**
- A ticker exists in the universe with fewer bars than the invalidation MA period (50). If none exists, this test is N/A — note it as not-runnable rather than failing.

**Steps:**
1. Navigate to `http://localhost:3836/stocks/<SHORT_HISTORY_TICKER>`
2. Read the note under the "Invalidation" label

**Expected Result:**
- The note reads exactly "Invalidation level NA — insufficient history"
- The note renders in amber (`--warn`) text, not muted grey
- No fabricated dollar value appears anywhere in the invalidation note

---

### UT-06 — Empty-theme honest state (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/stocks/[ticker]` → `ThemeAndInvalidationCard`

**Preconditions:**
- A ticker exists that is not a member of any configured theme. If every seeded ticker has a theme, mark this test not-runnable rather than failing.

**Steps:**
1. Navigate to `http://localhost:3836/stocks/<NO_THEME_TICKER>`
2. Look under the "Themes" label

**Expected Result:**
- Instead of chips, the text "Not a member of any tracked theme." renders in muted grey
- No empty chip outlines or stray commas appear

---

### UT-07 — Chart error state when backend is down (error)

**Type:** error
**Priority:** P2
**Surface:** `/stocks/[ticker]` → `StockChartPanel`

**Preconditions:**
- Frontend running; backend can be stopped for this test

**Steps:**
1. Stop the backend API process
2. Navigate to `http://localhost:3836/stocks/NVDA`
3. Observe the page after the loading skeletons clear

**Expected Result:**
- The whole page shows the red "Backend unavailable" card (because the scores call also fails) reading "This stock's scores could not load from the API. Nothing is fabricated — confirm the backend is running and reload."
- No candlestick chart, no fabricated prices, and no fabricated invalidation number appear
- The page does not crash to a blank/white screen

---

### UT-08 — Chart-only error state, scores intact (error)

**Type:** error
**Priority:** P2
**Surface:** `/stocks/[ticker]` → `StockChartPanel`

**Preconditions:**
- Backend running such that `/api/stocks/NVDA` (scores) returns 200 but `/api/stocks/NVDA/bars` returns an error/503. If this split cannot be induced in the environment, mark not-runnable.

**Steps:**
1. Induce a `/bars` failure for NVDA (e.g. via the no-price-data scenario) while the scores endpoint still succeeds
2. Navigate to `http://localhost:3836/stocks/NVDA`
3. Inspect the "Price & moving averages" card

**Expected Result:**
- Inside the "Price & moving averages" card, an amber-bordered box shows "Chart unavailable" with the note "The price series could not load from the API. Nothing is fabricated — the scores above are unaffected; confirm the backend is running and reload."
- The three score cards (Leadership / Entry Quality / Risk) above/below still render normally with their values
- The setup header card and themes/invalidation card are unaffected

---

### UT-09 — Empty price-history state (error / honest)

**Type:** error
**Priority:** P3
**Surface:** `/stocks/[ticker]` → `StockChartPanel`

**Preconditions:**
- A ticker that returns a 200 from `/bars` with zero bars. If unavailable, mark not-runnable.

**Steps:**
1. Navigate to `http://localhost:3836/stocks/<NO_BARS_TICKER>`
2. Inspect the "Price & moving averages" card

**Expected Result:**
- Inside the card, the message "No price history is available for <NO_BARS_TICKER>." renders centred in muted text (the ticker is interpolated)
- No empty/blank canvas and no fabricated candles appear

---

### UT-10 — Three explainable scores still render and match the leaderboard (regression, J-06 guard)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/[ticker]` → three `ScoreCard`s

**Preconditions:**
- Backend running and seeded

**Steps:**
1. Navigate to `http://localhost:3836/stocks`
2. Note the Leadership / Entry Quality / Risk bucket letters and 0–100 values shown for the NVDA row
3. Navigate to `http://localhost:3836/stocks/NVDA`
4. Inspect the three score cards titled "Leadership", "Entry Quality", and "Risk"

**Expected Result:**
- Each of the three cards shows an A–E bucket badge, a 0–100 value (e.g. "73.41 / 100"), the correct caption, and a component breakdown with ≥3 named components
- The bucket letters and numeric values for NVDA on the detail page match exactly what the `/stocks` leaderboard showed for the NVDA row (single source of truth preserved despite the new `invalidation`/`themes` fields)

---

### UT-11 — Unknown-ticker state still works (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/[ticker]` → unknown-ticker card

**Preconditions:**
- Backend running

**Steps:**
1. Navigate to `http://localhost:3836/stocks/NOTREAL`
2. Observe the page after skeletons clear
3. Click the "leaderboard" link inside the card

**Expected Result:**
- An amber card titled "Unknown ticker" renders with text: ""NOTREAL" is not in the scanned universe. Open a stock from the leaderboard."
- No chart, no theme chips, no invalidation note, and no fabricated data appear
- Clicking the "leaderboard" link navigates to `http://localhost:3836/stocks`

---

### UT-12 — Loading skeleton appears before content (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/stocks/[ticker]`

**Preconditions:**
- Backend running (slightly throttled network helps observe the skeleton)

**Steps:**
1. Navigate to `http://localhost:3836/stocks/NVDA`
2. Watch the page during the first moment after load

**Expected Result:**
- Before data arrives, pulsing grey placeholder cards appear (one ~h-20 header card and three ~h-72 score-card placeholders); the chart card shows its own pulsing ~h-80 grey block
- Once data loads, the skeletons are replaced by real content; no flash of an error card during normal loading

---

### UT-13 — Feature is discoverable from the leaderboard (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/stocks` → `/stocks/[ticker]`

**Preconditions:**
- Backend running and seeded

**Steps:**
1. Navigate to `http://localhost:3836/stocks`
2. Click any leader row (e.g. the top row)

**Expected Result:**
- The row is clickable and navigates to that ticker's detail page (`/stocks/<TICKER>`) within one click
- The detail page presents the chart, themes/invalidation, and scores together on a single page — the user reaches the full per-stock research view without hunting

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Stock Detail loads | smoke | P1 | `/stocks/NVDA` |
| UT-02 | Candle chart + MA + volume | happy-path | P1 | `PriceChart` |
| UT-03 | Theme chips → /themes | happy-path | P1 | `ThemeAndInvalidationCard` |
| UT-04 | Concrete invalidation note | happy-path | P1 | invalidation note |
| UT-05 | Invalidation NA state | validation | P2 | invalidation note |
| UT-06 | Empty-theme state | validation | P2 | `ThemeAndInvalidationCard` |
| UT-07 | Backend-down error card | error | P2 | page |
| UT-08 | Chart-only error, scores intact | error | P2 | `StockChartPanel` |
| UT-09 | Empty price-history state | error | P3 | `StockChartPanel` |
| UT-10 | Scores match leaderboard (J-06) | regression | P1 | three `ScoreCard`s |
| UT-11 | Unknown-ticker state | regression | P1 | unknown-ticker card |
| UT-12 | Loading skeleton | ux | P3 | `/stocks/[ticker]` |
| UT-13 | Discoverable from leaderboard | ux | P3 | `/stocks` → detail |

**P1 tests (UT-01, UT-02, UT-03, UT-04, UT-10, UT-11) must all pass for the browser QA verdict to be PASS.**
