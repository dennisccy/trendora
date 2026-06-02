# Phase goal-i_can_see_the_wealthy_future_forever-iter-6 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-6
**Date:** 2026-06-02
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Environment Notes (read before running)

- The global **as-of** state lives in an in-memory provider. A **hard reload (F5) resets it to "Latest"**. Therefore, after setting a historical as-of date, you MUST navigate between pages using **in-app links/clicks**, never the browser refresh or a fresh URL paste. If a "forward region" disappears unexpectedly, you almost certainly hard-reloaded — re-set the as-of and use in-app nav.
- "Historical as-of" below means a past date `D` that has price bars dated *after* it (e.g. `2025-04-04`). "Latest as-of" means the most recent seed date (no bars after it).
- The horizon control in the Return Attribution header is a **view selector** — it changes which horizon's numbers are displayed; it does NOT change the as-of date and does NOT trigger a network refetch.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Stock-detail page loads with chart (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks/[ticker]`

**Preconditions:**
- Frontend running at http://localhost:3835, backend on :8000
- As-of is at default (Latest)

**Steps:**
1. Navigate to `http://localhost:3835/stocks/NVDA`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error banner
- The ticker heading "NVDA" is visible
- The price chart (candles + volume bars) renders with visible candles
- No forward/greyed region is present (default as-of is Latest)
- No console errors

---

### UT-02 — Chart draws muted forward region at a historical as-of (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/[ticker]` → `PriceChart`

**Preconditions:**
- Start from any page with the global as-of switcher visible
- A historical as-of `D = 2025-04-04` exists with bars dated after it

**Steps:**
1. Navigate to `http://localhost:3835/stocks/NVDA`
2. Open the global as-of switcher (top of the page) and select the historical date `2025-04-04`
3. Without refreshing the browser, observe the price chart (if needed, click an in-app nav link to another ticker and back to NVDA — do NOT press F5)
4. Look at the candles to the right of the as-of boundary

**Expected Result:**
- Candles dated **on or before** `2025-04-04` render in normal up (green) / down (red) colours
- Candles dated **after** `2025-04-04` render **greyed/muted**, and their volume bars are likewise greyed
- The chart extends all the way to the latest seed date (it does not stop at the as-of date)
- The scores / setup / VCP panels below the chart still render

---

### UT-03 — As-of divider marker sits at the boundary (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/[ticker]` → `PriceChart` as-of divider marker

**Preconditions:**
- Continue from UT-02 (historical as-of `2025-04-04` on `/stocks/NVDA`, set via in-app interaction)

**Steps:**
1. On the historical-as-of NVDA chart, locate the boundary between normal and greyed candles
2. Read the marker label at that boundary

**Expected Result:**
- An arrow marker labelled `as-of 2025-04-04` (the selected date) sits at the last on-or-before-as-of candle
- The marker is positioned at the transition between the coloured region and the greyed forward region

---

### UT-04 — Forward swatch appears in the chart legend at historical as-of (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/stocks/[ticker]` → `ChartLegend`

**Preconditions:**
- Continue from UT-02 (historical as-of `2025-04-04` on `/stocks/NVDA`)

**Steps:**
1. Locate the chart legend (the row of coloured swatches identifying chart series)
2. Read the legend entries

**Expected Result:**
- The legend contains an entry reading `Forward — after as-of 2025-04-04 (display only)` with a greyed/muted swatch
- The date in the legend matches the selected as-of date

---

### UT-05 — Display-only caption appears above chart at historical as-of (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/stocks/[ticker]` → display-only caption above chart

**Preconditions:**
- Continue from UT-02 (historical as-of `2025-04-04` on `/stocks/NVDA`)

**Steps:**
1. Look at the one-line caption directly above the price chart

**Expected Result:**
- A single-line caption is visible stating that the forward (after-as-of) bars are **display-only** and do **not** affect the scores / setup / VCP shown below
- The caption is present ONLY because a forward region exists at this historical as-of

---

### UT-06 — Scores/setup/VCP are identical with and without the forward region (regression / no-lookahead)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/[ticker]` score / setup / VCP panels

**Preconditions:**
- Able to view NVDA at both Latest and a historical as-of

**Steps:**
1. Navigate to `http://localhost:3835/stocks/NVDA` at the default Latest as-of
2. Record the three score-card values, the setup status text, the VCP badge state, and the invalidation note
3. Using the global as-of switcher (and in-app nav, no F5), set the as-of to `2025-04-04`
4. Re-read the three score-card values, setup status, VCP badge, and invalidation note (note: these reflect the as-of snapshot, which legitimately differs by date)
5. Now confirm the *forward region itself* did not alter the as-of snapshot: compare the displayed values against `http://localhost:8000/api/stocks/NVDA?as_of=2025-04-04` (snapshot row)

**Expected Result:**
- The displayed scores, setup status, VCP flag, and invalidation note exactly match the values served by the snapshot API for `as_of=2025-04-04`
- The presence of greyed forward candles does NOT shift any score / setup / VCP / invalidation value

---

### UT-07 — Latest as-of shows no forward region (regression / edge)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/[ticker]` → `PriceChart`

**Preconditions:**
- On `/stocks/NVDA`

**Steps:**
1. Set the global as-of switcher to **Latest**
2. Navigate (in-app) to `/stocks/NVDA`
3. Observe the chart, legend, and the area above the chart

**Expected Result:**
- No greyed/muted forward candles are present
- No `as-of {date}` divider marker for a forward boundary is shown beyond the chart end
- The `Forward — after as-of …` legend entry is ABSENT
- The display-only caption above the chart is ABSENT
- The chart looks the same as the pre-iter-6 Latest view

---

### UT-08 — Backtest page loads with correct section order (smoke + happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/backtest` → section ordering / `BacktestResults`

**Preconditions:**
- Frontend + backend up; set a historical as-of `2025-04-04` via the global switcher, then navigate in-app to `/backtest` (no F5)

**Steps:**
1. With historical as-of `2025-04-04` set, click the in-app nav link to `/backtest`
2. Scroll from the top of the results to the bottom and note the vertical order of sections

**Expected Result:**
- Sections appear top-to-bottom in this exact order:
  1. **As-of scan summary** (regime label + candidate counts)
  2. **Forward-test scorecard**
  3. **Return Attribution**
  4. **Top Sectors**
  5. **Top Themes**
  6. **Ranked Cohort**
- The three leadership lists (Top Sectors, Top Themes, Ranked Cohort) appear **below** Return Attribution (not above the scorecard as before)

---

### UT-09 — As-of scan summary shows only regime + counts (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/backtest` → `AsOfScanSummary`

**Preconditions:**
- Continue from UT-08 (`/backtest` at historical as-of `2025-04-04`)

**Steps:**
1. Look at the topmost section of the Backtest results (the as-of scan summary)

**Expected Result:**
- The top summary shows the **regime label** and **candidate counts** only
- It does NOT contain any of the leadership lists (Top Sectors / Top Themes / Ranked Cohort)

---

### UT-10 — Top Sectors list shows a realized-return column (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/backtest` → `LeadershipListsSection` → Top Sectors

**Preconditions:**
- Continue from UT-08 (`/backtest` at historical as-of with post-bars)

**Steps:**
1. Locate the **Top Sectors** list
2. Inspect each row for a realized forward-return value at the currently selected horizon
3. For a sector row (e.g. XLK), note its return value

**Expected Result:**
- Each sector row displays a realized-return value (or "—"/NA when the horizon has no after-the-as-of data)
- The value for a sector equals that sector ETF's own forward return at the selected horizon (cross-checkable against the scorecard / `/api/backtest`)

---

### UT-11 — Top Themes list shows a member-mean return column with sample count (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/backtest` → `LeadershipListsSection` → Top Themes

**Preconditions:**
- Continue from UT-08

**Steps:**
1. Locate the **Top Themes** list
2. Inspect each row's realized-return value at the selected horizon
3. For a theme with members (e.g. semiconductors), note the return and the sample count (n)

**Expected Result:**
- Each theme row shows a realized-return value at the selected horizon
- The value is the equal-weight mean over the members that have a return, and a sample count (n) is shown
- A theme with no member returns shows "—"/NA (n = 0), not a fabricated number

---

### UT-12 — Ranked Cohort list shows a per-ticker return column (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/backtest` → `LeadershipListsSection` → Ranked Cohort

**Preconditions:**
- Continue from UT-08

**Steps:**
1. Locate the **Ranked Cohort** table
2. Inspect each row for a realized forward-return value at the selected horizon

**Expected Result:**
- Every cohort row resolves to a return value (the ticker's own realized return) or "—"/NA where data is missing
- No row shows a fabricated 0% in place of missing data

---

### UT-13 — Ranked Cohort table scrolls horizontally on a narrow viewport (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/backtest` → Ranked Cohort table (responsive)

**Preconditions:**
- On `/backtest` at a historical as-of with the new return column present

**Steps:**
1. Resize the browser window (or device toolbar) to ~640px wide
2. Locate the Ranked Cohort table
3. Attempt to scroll the table horizontally

**Expected Result:**
- The Ranked Cohort table is horizontally scrollable, revealing the new return column without breaking the page layout
- No column is clipped/hidden with no way to reach it

---

### UT-14 — One horizon selector re-points attribution AND all three return columns (happy path — defining proof)

**Type:** happy-path
**Priority:** P1
**Surface:** `/backtest` → `HorizonViewSelector` (in Return Attribution header)

**Preconditions:**
- Continue from UT-08 (`/backtest` at historical as-of with post-bars); at least two horizons have differing data

**Steps:**
1. Note the current horizon selected in the Return Attribution header (call it H1)
2. Record a value in the Top Sectors return column and a value in the Return Attribution panel at H1
3. Open the **horizon view selector** in the Return Attribution header and choose a different horizon (H2)
4. Without refreshing, re-read the same Top Sectors return column value AND the Return Attribution panel

**Expected Result:**
- Switching the single selector updates BOTH the Return Attribution panel AND the realized-return columns on all three leadership lists at the same time
- The change happens with **no page reload and no network refetch** (no loading spinner / no flash of the whole page)
- The as-of date is unchanged (the global as-of switcher still shows the same date)

---

### UT-15 — Return columns render honest NA at a recent as-of (validation / error)

**Type:** validation
**Priority:** P2
**Surface:** `/backtest` → Return column NA states

**Preconditions:**
- A **recent** as-of date `R` exists that has little or no after-the-as-of data for some horizons

**Steps:**
1. Set the global as-of switcher to a recent date `R` (e.g. within the last few days of seed data)
2. Navigate in-app to `/backtest` (no F5)
3. Select a horizon that has no post-as-of data
4. Inspect the return columns on Top Sectors, Top Themes, and Ranked Cohort

**Expected Result:**
- Rows lacking after-the-as-of data show "—" / NA
- No fabricated or synthesized numeric return (e.g. a misleading 0%) appears for missing data

---

### UT-16 — Low-sample warning marker renders when sample is thin (validation)

**Type:** validation
**Priority:** P3
**Surface:** `/backtest` → leadership list low-sample state

**Preconditions:**
- An as-of / horizon combination where some rows have a return but a sample count below the minimum

**Steps:**
1. On `/backtest`, find a leadership row that has a return but a small sample
2. Inspect the cell for the low-sample marker

**Expected Result:**
- Rows whose sample (n) is below the configured minimum show the existing low-sample ⚠ marker alongside the value
- The marker matches the existing low-sample treatment already used elsewhere in the app (no new ad-hoc style)

---

### UT-17 — No page-local date control exists on Backtest (regression — single date selector)

**Type:** regression
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- On `/backtest`

**Steps:**
1. Scan the entire Backtest page for any date picker / date dropdown / calendar control
2. Confirm the only date control is the **global** as-of switcher (shared across pages)
3. Open the horizon view selector and confirm it lists horizons (e.g. 5D / 21D / 63D), not dates

**Expected Result:**
- There is exactly one date control (the global as-of switcher); no second/page-local date picker exists on `/backtest`
- The horizon selector offers horizons, not dates, and changing it does not change the as-of date

---

### UT-18 — Core stock-detail and backtest journeys still work (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/[ticker]`, `/backtest`

**Preconditions:**
- Frontend + backend up; default Latest as-of

**Steps:**
1. Navigate to `http://localhost:3835/stocks/NVDA` and confirm the score cards, setup status, VCP badge, invalidation note, and chart all render
2. Navigate in-app to `/backtest` and confirm the scorecard and Return Attribution render at the default as-of
3. Use the global as-of switcher once, then navigate in-app, and confirm pages re-render against the new as-of without error

**Expected Result:**
- All core stock-detail panels render as before this phase
- The backtest scorecard and Return Attribution render as before
- The single global as-of control still drives both pages with no broken page or missing data

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Stock-detail loads with chart | smoke | P1 | `/stocks/[ticker]` |
| UT-02 | Muted forward region at historical as-of | happy-path | P1 | `/stocks/[ticker]` chart |
| UT-03 | As-of divider marker at boundary | happy-path | P1 | `/stocks/[ticker]` marker |
| UT-04 | Forward swatch in legend | happy-path | P2 | `/stocks/[ticker]` legend |
| UT-05 | Display-only caption above chart | happy-path | P2 | `/stocks/[ticker]` caption |
| UT-06 | Scores/VCP unchanged by forward region | regression | P1 | `/stocks/[ticker]` panels |
| UT-07 | Latest as-of: no forward region | regression | P1 | `/stocks/[ticker]` chart |
| UT-08 | Backtest section order correct | happy-path | P1 | `/backtest` order |
| UT-09 | As-of scan summary = regime + counts only | happy-path | P2 | `/backtest` summary |
| UT-10 | Top Sectors return column | happy-path | P1 | `/backtest` sectors |
| UT-11 | Top Themes member-mean + n column | happy-path | P1 | `/backtest` themes |
| UT-12 | Ranked Cohort per-ticker return column | happy-path | P1 | `/backtest` cohort |
| UT-13 | Cohort table horizontal scroll @640px | ux | P3 | `/backtest` cohort responsive |
| UT-14 | One selector re-points all columns + attribution | happy-path | P1 | `/backtest` selector |
| UT-15 | Honest NA at recent as-of | validation | P2 | `/backtest` NA |
| UT-16 | Low-sample ⚠ marker | validation | P3 | `/backtest` low-sample |
| UT-17 | No page-local date control | regression | P1 | `/backtest` |
| UT-18 | Core journeys still work | regression | P1 | `/stocks/[ticker]`, `/backtest` |

**P1 tests must all pass for browser QA verdict to be PASS.**
