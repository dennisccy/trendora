# Phase goal-i_can_see_the_wealthy_future-iter-10 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-10
**Date:** 2026-05-31
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- These are browser/operator tests of the NEW /backtest workspace (J-14) + sidebar nav + System Health refactor regression. API-level behavior is covered by the functional test plan (TC-01..TC-10) and is not duplicated here. -->

---

### UT-01 — Backtest page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend running on :8835 with seed data (at least one stored scanner run)

**Steps:**
1. Navigate to `http://localhost:3835/backtest`
2. Wait for the page to fully load (loading skeleton disappears)

**Expected Result:**
- Page renders without a blank screen or error overlay
- The page heading "Backtest" is visible (top-left)
- The subtitle text starting "Time-machine to a past scan date..." is visible
- An "As-of date" dropdown is visible (top-right)
- A "Survivorship bias" warning card is visible
- A "Forward-test scorecard" table is visible further down
- No "Backend unavailable" card appears
- No browser console errors

---

### UT-02 — Backtest is discoverable from the sidebar (ux / nav)

**Type:** ux
**Priority:** P1
**Surface:** sidebar (all pages)

**Preconditions:**
- Frontend running; on any page (e.g., `http://localhost:3835/`)

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Look at the left sidebar navigation
3. Confirm a "Backtest" item (flask/conical icon) appears between "Scanner Runs" and "System Health"
4. Click the "Backtest" sidebar item

**Expected Result:**
- A nav item labeled "Backtest" with a flask icon is visible, ordered after "Scanner Runs" and before "System Health"
- After clicking, the URL becomes `http://localhost:3835/backtest`
- The "Backtest" sidebar item shows the active-state highlight
- The Backtest workspace (heading "Backtest" + "As-of date" picker) renders

---

### UT-03 — As-of scan summary renders for a full-window historical date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/backtest` — As-of scan summary section

**Preconditions:**
- `/backtest` loaded; at least one older historical run date with data is selectable in the picker

**Steps:**
1. Navigate to `http://localhost:3835/backtest`
2. Click the "As-of date" dropdown (top-right)
3. Select the oldest date listed (an early historical date most likely to have a full forward window)
4. Wait for the page to re-fetch (skeleton → content)
5. Read the "As-of scan summary" section

**Expected Result:**
- An "As-of scan summary" heading is visible
- A "Market Regime" card shows a regime label badge (one of: Strong risk-on, Risk-on, Narrow leadership, Choppy, Defensive, Risk-off) and a numeric score formatted like "NN.NN / 100"
- A "Candidate Counts" card shows three rows: "Actionable", "Breakout-watch", "Pullback-watch", each with a numeric value
- A "Top Sectors" card lists ranked sectors (each row: rank number, ticker, trend label, score badge)
- A "Top Themes" card lists ranked themes (each row: rank number, name, trend label, score badge)
- A "Ranked cohort" table shows up to 10 rows with columns "#", "Ticker", "Setup", "Leadership"
- No "Scan summary unavailable" card appears

---

### UT-04 — Forward-test scorecard shows numeric returns for a full-window date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/backtest` — Forward-test scorecard table

**Preconditions:**
- `/backtest` loaded; oldest historical date (≥60 post-snapshot bars) selected as in UT-03

**Steps:**
1. Navigate to `http://localhost:3835/backtest`
2. Select the oldest date in the "As-of date" dropdown
3. Scroll to the "Forward-test scorecard" table
4. Inspect the rows and columns

**Expected Result:**
- The table header shows columns: "Horizon", "Cohort", "vs SPY", "vs QQQ", "vs Sector", "Random peers", "SPY", "QQQ", "Sector ETF"
- There are 5 horizon rows labeled "1d", "5d", "10d", "20d", "60d"
- At least one row shows a numeric "Cohort" return formatted like "+1.23%" or "-0.45%", paired with a sample size "n=N" (N ≥ 1)
- The "vs SPY", "vs QQQ", "vs Sector" cells in that row show numeric excess values with their own "n=" tokens
- The "Random peers", "SPY", "QQQ", "Sector ETF" cells show numeric returns with "n=" tokens
- The "No elapsed forward window for this date yet" empty state does NOT appear
- No cell shows a numeric percent while displaying "n=0"

---

### UT-05 — Page-local date picker time-travels independently of the global switcher (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/backtest` — `BacktestDatePicker` + as-of badge

**Preconditions:**
- `/backtest` loaded with at least two distinct dates in the picker (Latest + ≥1 historical)

**Steps:**
1. Navigate to `http://localhost:3835/backtest`
2. Note the as-of badge text near the top (initially the latest date)
3. Click the "As-of date" dropdown and select a historical date D (not "Latest")
4. Wait for re-fetch
5. Observe the as-of badge and the scorecard/scan-summary update

**Expected Result:**
- The dropdown default option reads "Latest · <date>"; historical dates are listed below it
- After selecting D, the as-of badge changes to read "Viewing as-of <D> (historical)" with an amber/warn style and a history icon
- The scan summary and scorecard re-fetch and reflect date D (content visibly changes from the latest view)
- The global top-bar as-of switcher is NOT required and does NOT drive this change

---

### UT-06 — As-of badge reflects historical vs latest (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/backtest` — As-of indicator `Badge` (`data-testid="backtest-asof"`)

**Preconditions:**
- `/backtest` loaded

**Steps:**
1. Navigate to `http://localhost:3835/backtest` (defaults to Latest)
2. Read the as-of badge
3. Open the "As-of date" dropdown and select a historical date
4. Read the as-of badge again
5. Re-open the dropdown and select "Latest · <date>"
6. Read the as-of badge again

**Expected Result:**
- On default load, badge reads "Viewing as-of <date> (latest)" with a clock icon, neutral/default style
- After selecting a historical date, badge reads "Viewing as-of <D> (historical)" with a history icon, amber/warn style
- After resetting to Latest, badge returns to "Viewing as-of <date> (latest)" (latest style)

---

### UT-07 — Recent/latest date shows honest NA, never fabricated numbers (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/backtest` — `ScorecardSection` NA/partial rendering

**Preconditions:**
- `/backtest` loaded; the Latest (or a very recent) date is the one with few/zero post-snapshot bars

**Steps:**
1. Navigate to `http://localhost:3835/backtest`
2. Ensure "Latest · <date>" is selected in the "As-of date" dropdown
3. Inspect the longer-horizon rows ("20d", "60d") of the Forward-test scorecard

**Expected Result:**
- Horizons whose forward window has not elapsed render an em dash "—" paired with "n=0"
- No horizon shows a numeric percent value while its sample size reads "n=0" (no fabricated returns)
- If every horizon is NA, the empty state "No elapsed forward window for this date yet" appears with explanatory text mentioning "no realized forward return is observable yet" and "No numbers are fabricated to fill the gap."

---

### UT-08 — Low-sample figures are flagged with the ⚠ warn token (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/backtest` — low-sample flag (`SampleSize`)

**Preconditions:**
- `/backtest` loaded; a date/horizon exists where a cohort's `n` is below `min_sample`

**Steps:**
1. Navigate to `http://localhost:3835/backtest`
2. Read the scorecard sub-caption noting "figures with n < N ⚠ are low-sample"
3. Scan scorecard cells for any "n=" value below the stated minimum
4. Hover the flagged sample-size token

**Expected Result:**
- The caption explicitly states the minimum sample threshold (e.g., "n < 5 ⚠")
- Any cell whose `n` is below that minimum renders its sample size in the warn (amber) color with a trailing "⚠"
- Hovering the flagged token shows a tooltip like "Low sample — n below the N minimum; treat as indicative only"
- Cells with `n` at/above the minimum render the sample size in the faint (non-warn) color, no ⚠

---

### UT-09 — Survivorship-bias banner is visible and honest (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/backtest` — `SurvivorshipBanner`

**Preconditions:**
- `/backtest` loaded

**Steps:**
1. Navigate to `http://localhost:3835/backtest`
2. Locate the warning card near the top of the page (below the as-of badge)

**Expected Result:**
- A warn-styled (amber border, shield-alert icon) card with the bold title "Survivorship bias" is visible
- Its body text describes the survivorship-bias limitation of the walk-forward evidence (e.g., mentions current-membership universe / results may be overstated)

---

### UT-10 — Backend-unavailable degrades safely, no fabricated figures (error)

**Type:** error
**Priority:** P2
**Surface:** `/backtest` — error state card

**Preconditions:**
- Backend stopped (or `/api/backtest` made to fail), frontend still running

**Steps:**
1. Stop the backend service on :8835
2. Navigate to `http://localhost:3835/backtest`
3. Wait for the loading skeleton to resolve

**Expected Result:**
- A card titled "Backend unavailable" appears with the message that the scorecard could not load and "No figures are shown rather than fabricated values."
- The scorecard table and scan summary do NOT render
- No fabricated numbers or "0.00%" placeholders appear in place of real data
- The page does not crash to a blank screen

---

### UT-11 — Scan summary degrades when only dashboard endpoint fails (error)

**Type:** error
**Priority:** P3
**Surface:** `/backtest` — `ScanSummarySection` fallback

**Preconditions:**
- A date where `/api/backtest` succeeds but the dashboard/sectors/themes/stocks fetches are unavailable (best-effort, independent of the scorecard)

**Steps:**
1. Navigate to `http://localhost:3835/backtest`
2. Select a date where scan-summary endpoints do not respond but the scorecard does
3. Observe the scan-summary area and the scorecard

**Expected Result:**
- If the dashboard endpoint fails, a muted card reads "Scan summary unavailable for this date... The forward-test scorecard below is unaffected."
- If only a sub-endpoint fails (sectors/themes/stocks), the corresponding card shows "Sector data unavailable." / "Theme data unavailable." / "Stock data unavailable." while the rest renders
- The Forward-test scorecard still renders independently

---

### UT-12 — Scan-summary values match canonical pages for the same date (regression / single-source)

**Type:** regression
**Priority:** P2
**Surface:** `/backtest` vs `/` (Dashboard) and `/sectors`

**Preconditions:**
- `/backtest`, `/`, and `/sectors` all reachable for the same historical date D

**Steps:**
1. Navigate to `http://localhost:3835/backtest`, select date D in the "As-of date" picker
2. Note the Market Regime label + score, the Actionable candidate count, and the #1 Top Sector ticker/score
3. Navigate to `http://localhost:3835/` and switch the global top-bar as-of switcher to date D
4. Compare the regime label/score and Actionable count
5. Navigate to `http://localhost:3835/sectors` switched to date D and compare the #1 sector

**Expected Result:**
- The regime label and score on `/backtest` match the Dashboard for date D exactly
- The Actionable candidate count matches the Dashboard for date D
- The #1 Top Sector ticker and score on `/backtest` match `/sectors` for date D
- No value is recomputed/different between views (single canonical source)

---

### UT-13 — System Health return figures render identically after the shared-helper refactor (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/system-health`

**Preconditions:**
- Backend running with forward-return data; `/system-health` reachable

**Steps:**
1. Navigate to `http://localhost:3835/system-health`
2. Locate the realized forward-return figures / percentages on the page
3. Inspect their formatting, sample-size tokens, and low-sample flags

**Expected Result:**
- Forward-return percentages render in the same "+1.23%" / "-0.45%" / "—" format as before
- Positive returns are green, negative red, NA muted
- Sample sizes render as "n=N"; low-sample (`n < min`) figures still show the amber "⚠" flag
- No visual change vs the pre-refactor System Health page; no console errors, no missing values

---

### UT-14 — Global top-bar as-of switcher did not regress (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` and `/stocks` (global switcher)

**Preconditions:**
- Frontend + backend running

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Use the global top-bar as-of switcher to select a historical date
3. Observe the dashboard values update
4. Navigate to `http://localhost:3835/stocks` and confirm the switcher still drives the page

**Expected Result:**
- The global switcher time-travels the Dashboard/Stocks pages to the chosen date (values update without error)
- The global switcher's scope is unchanged and does NOT alter the `/backtest` page's own picker selection

---

### UT-15 — Scorecard table is horizontally scrollable on narrow viewports (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/backtest` — scorecard table overflow

**Preconditions:**
- `/backtest` loaded with a full-window date

**Steps:**
1. Navigate to `http://localhost:3835/backtest`, select a full-window date
2. Narrow the browser window (or use a ~1024px viewport)
3. Attempt to scroll the scorecard table horizontally

**Expected Result:**
- All nine columns ("Horizon" through "Sector ETF") remain reachable via horizontal scroll within the table container
- The table does not overflow the page layout or clip content without a scrollbar

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Backtest page loads | smoke | P1 | `/backtest` |
| UT-02 | Discoverable from sidebar | ux | P1 | sidebar |
| UT-03 | As-of scan summary renders | happy-path | P1 | `/backtest` |
| UT-04 | Scorecard numeric returns | happy-path | P1 | `/backtest` |
| UT-05 | Page-local time-travel | happy-path | P1 | `/backtest` |
| UT-06 | As-of badge historical/latest | ux | P2 | `/backtest` |
| UT-07 | Honest NA, no fabrication | validation | P1 | `/backtest` |
| UT-08 | Low-sample ⚠ flag | validation | P2 | `/backtest` |
| UT-09 | Survivorship banner | ux | P2 | `/backtest` |
| UT-10 | Backend unavailable | error | P2 | `/backtest` |
| UT-11 | Scan-summary partial degrade | error | P3 | `/backtest` |
| UT-12 | Values match canonical pages | regression | P2 | `/backtest` vs `/`,`/sectors` |
| UT-13 | System Health refactor regression | regression | P1 | `/system-health` |
| UT-14 | Global switcher no regression | regression | P1 | `/`, `/stocks` |
| UT-15 | Scorecard horizontal scroll | ux | P3 | `/backtest` |

**P1 tests must all pass for browser QA verdict to be PASS:** UT-01, UT-02, UT-03, UT-04, UT-05, UT-07, UT-13, UT-14.
