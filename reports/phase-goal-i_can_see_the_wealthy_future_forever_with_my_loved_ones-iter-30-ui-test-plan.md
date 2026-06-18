# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30
**Date:** 2026-06-18
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Dashboard loads and Market-Phase panel is present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running and `/api/market-phase` responds (check: `curl http://localhost:8000/health`)

**Steps:**
1. Navigate to `http://localhost:3835`
2. Wait for the page to fully load (allow up to 60 s for cold-compute on first load)
3. Scroll down approximately 1060 px until the Market-Phase panel / major-indexes card becomes visible
4. Confirm the Market-Phase panel heading or label is visible (e.g., "Market Phase", "Market-Phase", or equivalent section title)
5. Confirm there is no blank white block or JavaScript error message anywhere on the panel

**Expected Result:**
- The Dashboard page renders without a blank screen or full-page error
- The Market-Phase panel is visible below the fold
- No red error banner is shown in place of the panel
- No "Something went wrong" or "Error loading" message is visible on the panel

---

### UT-02 — Market-Phase timeline SVG step-function chart renders (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend has served at least one day of market-phase data (timeline is non-empty)

**Steps:**
1. Navigate to `http://localhost:3835`
2. Scroll down to the Market-Phase panel
3. Look for an SVG chart element showing a colored band and a line chart; the band should contain colors corresponding to market phases (green for Expansion/Recovery, amber for Pullback, red for Correction/Bear)
4. Look for a dashed vertical line on the chart marking the current as-of date

**Expected Result:**
- An SVG step-function chart is visible inside the Market-Phase panel
- A phase-colored band (green, amber, or red region) appears behind a bear-probability polyline
- A dashed vertical as-of marker is present on the chart at the rightmost resolved date
- A swatch legend showing phase color names (e.g., "Expansion", "Recovery", "Pullback", "Correction", "Bear") is visible near the chart

---

### UT-03 — Dashboard Market-Phase panel shows causal downtrend-episode list (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The dataset contains at least the 2022 bear episode

**Steps:**
1. Navigate to `http://localhost:3835`
2. Scroll down to the Market-Phase panel
3. Look below the SVG timeline chart for a list of downtrend episodes

**Expected Result:**
- At least one episode row is visible beneath the timeline chart
- Each visible episode row shows: a date (formatted as YYYY-MM-DD), a severity value (numeric or labelled), and a status badge reading either "open" or "closed"
- The 2022 bear episode appears as exactly one row (not multiple duplicate rows) with a first-trigger date in early 2022 and a "closed" badge when using the current (live) date

---

### UT-04 — Recovery-turn signal line is visible on Market-Phase panel (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend serves the `recovery_turn` field on `GET /api/market-phase`

**Steps:**
1. Navigate to `http://localhost:3835`
2. Scroll down to the Market-Phase panel
3. Look for a dedicated recovery-turn signal line or callout (may appear as a badge, a colored row, or a labelled text block)

**Expected Result:**
- A recovery-turn signal element is visible in the Market-Phase panel
- The element shows either a green up-arrow "Recovery / turn signalled" message or a muted shield-icon "No recovery turn at this date" message — not a bare boolean value or an empty space
- A plain-language reason is visible beneath the signal indicator (e.g., "P(bear) dropped below recovery threshold" or "Index reclaimed its trailing average")

---

### UT-05 — Retrospective sub-view toggle appears collapsed by default (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835`
2. Scroll down to the Market-Phase panel
3. Look for a "Show" toggle or button near a dashed-border section labelled "Retrospective (full-sample / analysis-only)" or equivalent

**Expected Result:**
- A "Show" (or equivalent collapsed-state) toggle is visible in or near the Market-Phase panel
- The dashed-border retrospective sub-view panel is NOT expanded by default — its content (smoothed P(bear) chart, peak-to-trough dating) is hidden
- The label "Retrospective" or "full-sample / analysis-only" is visible as the toggle label

---

### UT-06 — Research page loads with Recovery-Turn Edge lab section (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend serves `GET /api/research/recovery-turn-edge`

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the page to fully load
3. Scroll down past the existing Regime×Setup×Pattern lab section to find the "Recovery-Turn Edge" section

**Expected Result:**
- The `/research` page loads without a blank screen or error message
- A section labelled "Recovery-Turn Edge" (or equivalent) is visible on the page, positioned after the Regime×Setup×Pattern lab
- The section contains at least one table with horizon rows and return-metric columns
- A survivorship-bias disclosure label (e.g., "Forward returns contain survivorship bias") is visible in or near the section

---

### UT-07 — Full timeline history renders on Dashboard Market-Phase panel (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The dataset contains snapshot history from at least 2021 onward
- No `?asof` parameter is set (live / latest date)

**Steps:**
1. Navigate to `http://localhost:3835`
2. Scroll down to the Market-Phase panel
3. Observe the SVG timeline chart; confirm it shows multiple distinct colored phase segments spanning multiple years
4. Confirm the bear-probability polyline runs across the entire span of the colored band
5. Look for the 2022 bear episode in the episode list below the chart; confirm it shows a first-trigger date in early 2022, a severity-at-trigger value, a peak-P(bear) value, and a "closed" badge (since the current date is past the 2022 bear)

**Expected Result:**
- The SVG timeline chart displays a multi-year step-function band with clearly distinct colored segments for Expansion (green), Pullback (amber), Correction/Bear (red), and Recovery (green)
- The bear-probability polyline is drawn on top of the band across all snapshot dates
- The dashed as-of marker appears at the rightmost (current) date
- In the episode list, the 2022 bear appears as exactly one row with: a first-trigger date in early 2022, a non-zero severity-at-trigger, a non-zero peak P(bear), and a "closed" status badge

---

### UT-08 — Historical as-of clamps timeline and shows 2022 episode as open (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The dataset contains snapshots for 2022-10-07

**Steps:**
1. Navigate to `http://localhost:3835/?asof=2022-10-07`
2. Wait for the page to fully load (allow up to 60 s for cold compute on a new as-of date)
3. Scroll down to the Market-Phase panel
4. Inspect the SVG timeline chart: confirm no dates after 2022-10-07 appear on the time axis
5. Inspect the episode list: locate the 2022 downtrend episode row
6. Check the status badge on the 2022 episode row

**Expected Result:**
- The SVG timeline shows only dates up to and including 2022-10-07 — the chart does not extend past the as-of marker
- The dashed as-of marker is positioned at 2022-10-07 on the chart
- The 2022 downtrend episode row shows an "open" status badge (the downtrend was not yet closed at that date)
- No dates after 2022-10-07 appear anywhere on the causal timeline or episode list

---

### UT-09 — Recovery-turn signal turns green with reason at a confirmed signal date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The dataset contains 2023-02-02 as a date where a recovery-turn signal was triggered

**Steps:**
1. Navigate to `http://localhost:3835/?asof=2023-02-02`
2. Wait for the Market-Phase panel to load
3. Scroll to the Market-Phase panel and locate the recovery-turn signal line
4. Read the signal text color, icon, and reason text

**Expected Result:**
- The recovery-turn signal callout shows a green up-arrow icon and reads "Recovery / turn signalled" (or equivalent affirmative phrasing) — NOT the muted shield-icon "No recovery turn" message
- A plain-language reason is visible directly beneath the signal (e.g., "Bear probability dropped below recovery threshold and the index reclaimed its trailing moving average" or equivalent)

---

### UT-10 — Recovery-turn signal shows negative with shield icon at current (Expansion) date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Current (live) date is in Expansion phase with P(bear) approximately 0.003

**Steps:**
1. Navigate to `http://localhost:3835` (no `?asof` parameter — live date)
2. Scroll to the Market-Phase panel and locate the recovery-turn signal line
3. Read the signal text, icon, and color

**Expected Result:**
- The recovery-turn signal callout shows a muted (grey/slate) shield icon and reads "No recovery turn at this date" (or equivalent negative phrasing)
- The signal text is in a muted color, NOT green
- A reason or explanation is still visible (e.g., "Market phase is Expansion, not a downtrend exit point")

---

### UT-11 — Fenced retrospective sub-view shows smoothed P(bear) and 2022 true-bear dating (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend returns the `retrospective` field on `GET /api/market-phase?retrospective=true`

**Steps:**
1. Navigate to `http://localhost:3835`
2. Scroll to the Market-Phase panel and locate the "Retrospective (full-sample / analysis-only)" toggle section with a "Show" button
3. Click the "Show" button/toggle
4. Wait for the dashed-border retrospective sub-view panel to appear
5. Read the content of the expanded sub-view
6. Look for the 2022 true-bear dating (should state something like "2022-01-03 to 2022-10-12, −24.5%" or equivalent peak-to-trough figures)
7. Look for a disclosure label explicitly stating this view is "future-aware analysis only" or "full-sample / analysis-only" or equivalent
8. Click the "Hide" button/toggle
9. Confirm the sub-view collapses

**Expected Result:**
- Clicking "Show" reveals a dashed-border sub-panel
- The sub-panel shows a smoothed bear-probability chart distinct from the main causal timeline
- The 2022 true-bear dating appears with a start date, end date, and a drawdown percentage (e.g., "−24.5%")
- A visible disclosure statement says explicitly that this view is "future-aware analysis only" or "full-sample" and "never feeds any score, signal, or episode" (or equivalent)
- Clicking "Hide" collapses the sub-panel; the causal timeline remains visible unchanged

---

### UT-12 — Recovery-Turn Edge lab shows per-horizon table with all required columns (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend serves `GET /api/research/recovery-turn-edge` with data
- The dataset contains at least 6 recovery-turn signal dates

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll down past the Regime×Setup×Pattern lab to the "Recovery-Turn Edge" section
3. Inspect the per-horizon edge table and confirm the following column headers are present: a horizon column (e.g., "1d", "5d", "10d", "20d", "60d"), mean return, median return, win rate (or "%-positive"), expectancy, mean MAE/MFE (or max-adverse-excursion / max-favorable-excursion), aggregate max-drawdown, and a downside risk-adjusted figure
4. Confirm the disclosure line near the top of the section states the number of signal dates (e.g., "6 signal dates" on the real host) and identifies the best-exit horizon

**Expected Result:**
- The "Recovery-Turn Edge" section is visible after the Regime×Setup×Pattern lab
- The per-horizon table has at least the following columns: Horizon, Mean Return, Median Return, Win Rate (or % Positive), Expectancy, Max Drawdown, and a downside risk-adjusted metric
- The section header or disclosure line shows the count of signal dates (≥1 on any populated dataset)
- No "buy", "sell", or order-entry button is present anywhere in this section

---

### UT-13 — N= chip on Recovery-Turn Edge lab opens count-coherent samples drill-down (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → `/research/samples`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend serves both `/api/research/recovery-turn-edge` and `/api/research/samples?kind=recovery-turn`
- Recovery-Turn Edge lab is loaded with data

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Recovery-Turn Edge" section
3. In the per-horizon edge table, locate an "N=" chip (e.g., a link or badge labelled "N=6" or "N=42")
4. Note the exact count shown on the chip (write it down)
5. Click the "N=" chip
6. A new browser tab should open; switch to that tab
7. On the `/research/samples` page that opened, read the total count of rows shown or the "total" figure in the cohort header

**Expected Result:**
- Clicking the "N=" chip opens a new browser tab (the original `/research` tab remains open)
- The new tab URL contains `/research/samples` and the query includes `kind=recovery-turn` parameters
- The samples page shows a cohort header reading "All recovery-turn dates" (for an all-recovery-turn chip)
- The qualifying columns include "Signal date", "Phase at signal", and "P(bear) at signal"
- The total row count on the samples page EXACTLY matches the N value noted in step 4

---

### UT-14 — Recovery-Turn Edge samples count matches in both Episodes and Pooled mode (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → `/research/samples`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Recovery-Turn Edge lab is loaded with data

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Recovery-Turn Edge" section
3. Ensure the page-level toggle is set to "Episodes" mode
4. In the Episodes-mode per-horizon table, locate an "N=" chip; note its count (call it N_episodes)
5. Click that chip; a new tab opens to `/research/samples`; note the samples page total count; close this tab
6. Return to the `/research` tab; switch the page-level toggle to "Pooled" mode
7. In the Pooled-mode per-horizon table, locate the corresponding "N=" chip; note its count (call it N_pooled)
8. Click that chip; a new tab opens; note the samples page total count; close this tab

**Expected Result:**
- In Episodes mode: the samples page total count EXACTLY equals N_episodes
- In Pooled mode: the samples page total count EXACTLY equals N_pooled
- The N values differ between Episodes and Pooled modes (confirming the toggle actually changes the cohort)

---

### UT-15 — Recovery-Turn Edge table columns sort on click (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Recovery-Turn Edge lab is loaded with at least 2 horizon rows

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Recovery-Turn Edge" per-horizon table
3. Click the "Mean return" column header (or the first sortable metric column)
4. Observe the row order after clicking
5. Click the same "Mean return" column header a second time
6. Observe the row order again
7. Repeat steps 3–6 for the "Win rate" (or "%-positive") column header

**Expected Result:**
- After the first click on "Mean return": rows reorder in descending order (highest mean return at top); a sort-direction indicator (arrow or caret) appears on the column header pointing down
- After the second click on "Mean return": rows reorder in ascending order (lowest mean return at top); the sort-direction indicator reverses direction
- The "Win rate" column is also sortable and shows the same descending/ascending toggle behavior

---

### UT-16 — By-signal-phase conditioning table is visible and sortable (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Recovery-Turn Edge lab is loaded with data across at least two distinct market phases at signal dates

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Recovery-Turn Edge" section
3. Locate the "by-signal-phase" conditioning table (a separate table below or beside the per-horizon table, showing rows labelled by market phase, e.g., "Pullback", "Recovery")
4. Confirm the table shows at least two phase rows
5. Sum the "n" column values across all phase rows in the by-signal-phase table; note the total (call it sum_n_phases)
6. Read the "N" value from the per-horizon table for the same scope (call it n_horizon)
7. Confirm sum_n_phases == n_horizon
8. Click a column header in the by-signal-phase table to sort

**Expected Result:**
- The by-signal-phase table shows at least two distinct market-phase rows (e.g., "Pullback" and "Recovery")
- The sum of n values across all phase rows equals the total n in the per-horizon table for the same scope and view mode
- Clicking a column header in the by-signal-phase table reorders the rows

---

### UT-17 — Recovery-Turn Edge lab respects As-of / All-history toggle (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- A historical as-of date exists where fewer recovery-turn signals have occurred (e.g., `?asof=2023-06-30`)

**Steps:**
1. Navigate to `http://localhost:3835/research?asof=2023-06-30`
2. Scroll to the "Recovery-Turn Edge" section
3. Locate the As-of / All-history toggle on the page
4. Note the N value shown in the per-horizon table when the toggle is set to "As-of"
5. Switch the toggle to "All-history"
6. Note the N value in the per-horizon table now

**Expected Result:**
- In "As-of" mode with `?asof=2023-06-30`, the N value reflects only recovery-turn signals at dates ≤ 2023-06-30 (should be a smaller or equal number than All-history)
- Switching to "All-history" updates the N value to include all recovery-turn signals across the full dataset (N_all_history ≥ N_asof)
- The table data updates without a page reload when the toggle is switched

---

### UT-18 — Recovery-Turn Edge lab respects Episodes / Pooled toggle (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Recovery-Turn Edge lab is loaded with data

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Recovery-Turn Edge" section
3. Locate the Episodes / Pooled toggle on the page (shared page-level toggle)
4. Confirm the current mode is "Pooled" (or set it to "Pooled")
5. Note the N value and by-signal-phase table row counts
6. Switch the toggle to "Episodes"
7. Note the N value and by-signal-phase table row counts again

**Expected Result:**
- Switching from Pooled to Episodes updates the N values in the per-horizon table and the by-signal-phase table
- The by-signal-phase table n values differ between Episodes and Pooled modes
- Switching back to Pooled restores the previous values

---

### UT-19 — Samples drill-down shows correct cohort header for recovery-turn kind (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/samples`

**Preconditions:**
- Frontend is running at http://localhost:3835
- User has arrived at `/research/samples` via an N= chip from the Recovery-Turn Edge lab (not by direct URL)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Recovery-Turn Edge" section
3. Click an "N=" chip in the by-signal-phase table (e.g., a chip for "Pullback" rows)
4. In the new tab that opens, read the cohort header text

**Expected Result:**
- The new tab URL contains `/research/samples` with a `kind=recovery-turn` parameter and a phase selector (e.g., `phase=Pullback`)
- The cohort header reads "Phase at signal: Pullback" (or equivalent phrasing specific to the selected phase)
- The qualifying columns include "Signal date", "Phase at signal", and "P(bear) at signal"
- The total row count on the page matches the N value from the originating chip

---

### UT-20 — Retrospective fetch is only sent after clicking "Show" toggle (error / network behavior)

**Type:** error
**Priority:** P2
**Surface:** `/` → browser DevTools Network tab

**Preconditions:**
- Frontend is running at http://localhost:3835
- Browser DevTools is open on the Network tab

**Steps:**
1. Open browser DevTools (press F12) and go to the Network tab; clear existing requests
2. Navigate to `http://localhost:3835`
3. Wait for the initial page load to complete; inspect Network requests for `GET /api/market-phase`
4. Confirm the initial request URL does NOT contain `retrospective=true`
5. Scroll to the Market-Phase panel and click the "Show" toggle for the retrospective sub-view
6. Observe the Network tab for a new request to `/api/market-phase`

**Expected Result:**
- The initial `GET /api/market-phase` request on page load does NOT include `?retrospective=true` in the URL
- After clicking the "Show" toggle, a new `GET /api/market-phase?retrospective=true` (or equivalent URL with the retrospective parameter) appears in the Network tab
- The retrospective data is only fetched on user demand, not on initial page load

---

### UT-21 — Recovery-Turn Edge API is called when the lab section becomes visible (error / network behavior)

**Type:** error
**Priority:** P2
**Surface:** `/research` → browser DevTools Network tab

**Preconditions:**
- Frontend is running at http://localhost:3835
- Browser DevTools is open on the Network tab

**Steps:**
1. Open browser DevTools (press F12) and go to the Network tab; clear existing requests
2. Navigate to `http://localhost:3835/research`
3. Wait for the page to load; scroll down to the "Recovery-Turn Edge" section
4. Look in the Network tab for a request to `/api/research/recovery-turn-edge`
5. Switch the page-level Episodes/Pooled toggle and observe the Network tab again

**Expected Result:**
- A `GET /api/research/recovery-turn-edge` request appears in the Network tab when the Recovery-Turn Edge section loads (either on scroll-into-view or on page load)
- When the Episodes/Pooled toggle is switched, a new request to `/api/research/recovery-turn-edge` is fired with the updated `view` parameter
- All requests return HTTP 200 status

---

### UT-22 — Early as-of date shows empty timeline with honest empty state (error)

**Type:** error
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3835
- 2021-01-05 is earlier than the dataset's practical start of history

**Steps:**
1. Navigate to `http://localhost:3835/?asof=2021-01-05`
2. Wait for the Market-Phase panel to load
3. Scroll to the Market-Phase panel
4. Observe the timeline chart and episode list

**Expected Result:**
- The timeline chart shows a minimal or empty plot (very short or zero-length band) — NOT a fabricated multi-year chart
- The episode list is empty or shows "No downtrend episodes" (or equivalent honest empty-state text)
- No recovery-turn signal fires (signal shows "No recovery turn at this date")
- The panel does NOT crash or show a JavaScript error; it degrades gracefully to the empty-state display

---

### UT-23 — Low-sample edge cohort shows NA with sample count visible (error)

**Type:** error
**Priority:** P2
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- A scope exists where the Recovery-Turn Edge cohort falls below the configured minimum-sample threshold (e.g., narrow as-of date + "As-of" mode)

**Steps:**
1. Navigate to `http://localhost:3835/research?asof=2022-06-01`
2. Scroll to the "Recovery-Turn Edge" section
3. Set the scope toggle to "As-of" mode
4. Look at the per-horizon table rows for entries where the return metric shows "NA", "—", or an equivalent blank indicator
5. For any NA row, confirm the "n" column value is still visible (shows the actual count even though it is below the minimum)

**Expected Result:**
- At least one table cell in the per-horizon edge table shows "NA" or "—" for return metrics in the As-of scope at an early date
- The n count is still visible next to or in the NA row (e.g., "N=1" or "n=2") — the count is NOT hidden
- No fabricated numeric return (e.g., "0.0%" or "0.5%") appears in place of the NA value

---

### UT-24 — Old Market-Phase panel values (phase, severity, P(bear)) unchanged from prior iteration (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3835
- At least one known reference date exists where phase, severity, and P(bear) values are known from prior iterations (J-87/J-88 baseline)

**Steps:**
1. Navigate to `http://localhost:3835`
2. Scroll to the Market-Phase panel
3. Read the single-date headline values: current phase label (e.g., "Expansion"), severity value, and filtered P(bear) value
4. Navigate to `http://localhost:3835/?asof=2022-10-07`
5. Read the same headline values again
6. Compare both sets of values against the known J-87/J-88 reference values for those dates

**Expected Result:**
- The phase, severity, and filtered P(bear) headline values are byte-identical to the J-87/J-88 reference values for the same dates
- The new timeline, episode list, and recovery-turn signal are additive additions — they do NOT alter the existing headline values
- No drift or recomputation of the prior single-date values is visible

---

### UT-25 — Regime×Setup×Pattern lab on Research page still works (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Regime × Setup × Pattern" lab section (the existing lab, NOT the new Recovery-Turn Edge section)
3. Confirm the table renders with regime rows, setup columns, and pattern breakdowns
4. Click a column header in the Regime×Setup×Pattern table to sort
5. Click an "N=" chip in the Regime×Setup×Pattern table

**Expected Result:**
- The Regime×Setup×Pattern lab renders correctly with data
- Column-header sorting works as before (rows reorder, arrow indicator toggles)
- An N= chip click opens a new tab to `/research/samples` with a `kind=regime-setup-pattern` (or equivalent) cohort header — NOT the recovery-turn cohort header
- The new Recovery-Turn Edge section below does NOT interfere with the existing lab's behavior

---

### UT-26 — J-01 Dashboard risk score and stock list still render (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835`
2. Wait for the page to load completely
3. Confirm the main risk score or stock-count summary is visible in the upper area of the Dashboard (above the fold)
4. Confirm the stock/theme list panels (if applicable) render without errors

**Expected Result:**
- The Dashboard risk score or primary metric is visible and shows a numeric value (not "—" or error)
- The stock or theme list panels render data (not blank or error)
- The new Market-Phase timeline additions below the fold do NOT interfere with the above-the-fold content

---

### UT-27 — As-of date selector (?asof) still controls the full page (regression / J-18 compliance)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/?asof=2023-06-30`
2. Wait for all panels to load
3. Confirm the Market-Phase panel shows data clamped to 2023-06-30 (no post-2023-06-30 dates visible on the causal timeline)
4. Confirm the Dashboard's primary stock/risk panels also reflect the 2023-06-30 date (same behavior as prior iterations)
5. Confirm there is no second date-picker or date-selector widget visible anywhere on the Market-Phase panel (the only date selector is the existing global as-of control)

**Expected Result:**
- All panels on the Dashboard respond to `?asof=2023-06-30` in the URL as the single source of truth
- The Market-Phase panel's timeline, episode list, and recovery-turn signal all use 2023-06-30 as the as-of date
- No second or independent date `useState` or date-picker is present on the Market-Phase panel

---

### UT-28 — Samples drill-down from prior Regime×Setup×Pattern lab still counts correctly (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/samples`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The Regime×Setup×Pattern lab has data with N= chips

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the Regime×Setup×Pattern lab
3. Note the N value on an N= chip in that lab
4. Click the N= chip; a new tab opens to `/research/samples`
5. On the samples page, read the total row count or the cohort header count

**Expected Result:**
- The samples page total count EXACTLY matches the N value from the Regime×Setup×Pattern chip
- The cohort header does NOT read "recovery-turn" — it reads the Regime×Setup×Pattern cohort description
- The new `kind=recovery-turn` samples wiring has NOT broken the existing samples kinds

---

### UT-29 — Timeline section is discoverable by scrolling the Dashboard (UX)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Steps:**
1. Navigate to `http://localhost:3835`
2. As a first-time operator, scroll down the Dashboard page slowly
3. At approximately 1060 px from the top, observe whether the Market-Phase panel becomes visible without any additional click or expand action

**Expected Result:**
- The Market-Phase panel with the SVG timeline, episode list, and recovery-turn signal is visible during normal scrolling — it is NOT hidden behind a collapsed accordion or requires a click to expand
- The timeline chart, episode list, and recovery-turn signal are all visible without interacting with any toggle (except the retrospective sub-view, which is correctly off by default)
- A new user can understand from the panel labels what is being shown (phase history, downtrend episodes, current recovery signal)

---

### UT-30 — Recovery-Turn Edge lab is discoverable from the Research page (UX)

**Type:** ux
**Priority:** P2
**Surface:** `/research`

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll down the research page to explore all sections
3. Confirm the "Recovery-Turn Edge" section is clearly labelled and appears in the natural reading order after the Regime×Setup×Pattern lab
4. Confirm the survivorship-bias label is visible without expanding any sub-view

**Expected Result:**
- The "Recovery-Turn Edge" section appears as a clearly titled section heading in the research page stack
- A first-time user scrolling the research page will encounter it within the normal page scroll flow
- The survivorship-bias disclosure is visible immediately (not hidden behind a toggle)
- No execution or order affordance (buy / sell button) is present anywhere in the section

---

### UT-31 — Retrospective toggle is clearly labelled as analysis-only (UX)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Steps:**
1. Navigate to `http://localhost:3835`
2. Scroll to the Market-Phase panel
3. Locate the retrospective toggle without being told its location — it should be self-describing

**Expected Result:**
- The toggle is labelled "Retrospective (full-sample / analysis-only)" or a label that makes it clear this view is hindsight analysis, not a causal/live signal
- The dashed border (or equivalent visual treatment) distinguishes the retrospective panel visually from the causal timeline after clicking "Show"
- The disclosure text inside the retrospective sub-view explicitly states it "never feeds any score, signal, episode, or study" or equivalent — a first-time operator understands this view cannot be used for trading decisions

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Dashboard loads and Market-Phase panel is present | smoke | P1 | `/` |
| UT-02 | Market-Phase timeline SVG step-function chart renders | smoke | P1 | `/` |
| UT-03 | Dashboard Market-Phase panel shows causal downtrend-episode list | smoke | P1 | `/` |
| UT-04 | Recovery-turn signal line is visible on Market-Phase panel | smoke | P1 | `/` |
| UT-05 | Retrospective sub-view toggle appears collapsed by default | smoke | P1 | `/` |
| UT-06 | Research page loads with Recovery-Turn Edge lab section | smoke | P1 | `/research` |
| UT-07 | Full timeline history renders on Dashboard Market-Phase panel | happy-path | P1 | `/` |
| UT-08 | Historical as-of clamps timeline and shows 2022 episode as open | happy-path | P1 | `/` |
| UT-09 | Recovery-turn signal turns green with reason at a confirmed signal date | happy-path | P1 | `/` |
| UT-10 | Recovery-turn signal shows negative with shield icon at current date | happy-path | P1 | `/` |
| UT-11 | Fenced retrospective sub-view shows smoothed P(bear) and true-bear dating | happy-path | P1 | `/` |
| UT-12 | Recovery-Turn Edge lab shows per-horizon table with all required columns | happy-path | P1 | `/research` |
| UT-13 | N= chip opens count-coherent samples drill-down | happy-path | P1 | `/research` → `/research/samples` |
| UT-14 | Samples count matches in both Episodes and Pooled mode | happy-path | P1 | `/research` → `/research/samples` |
| UT-15 | Recovery-Turn Edge table columns sort on click | happy-path | P1 | `/research` |
| UT-16 | By-signal-phase conditioning table is visible and sortable | happy-path | P1 | `/research` |
| UT-17 | Recovery-Turn Edge lab respects As-of / All-history toggle | happy-path | P1 | `/research` |
| UT-18 | Recovery-Turn Edge lab respects Episodes / Pooled toggle | happy-path | P1 | `/research` |
| UT-19 | Samples drill-down shows correct cohort header for recovery-turn kind | happy-path | P1 | `/research/samples` |
| UT-20 | Retrospective fetch is only sent after clicking "Show" toggle | error | P2 | `/` |
| UT-21 | Recovery-Turn Edge API is called when the lab section becomes visible | error | P2 | `/research` |
| UT-22 | Early as-of date shows empty timeline with honest empty state | error | P2 | `/` |
| UT-23 | Low-sample edge cohort shows NA with sample count visible | error | P2 | `/research` |
| UT-24 | Old Market-Phase panel values unchanged from prior iteration | regression | P1 | `/` |
| UT-25 | Regime×Setup×Pattern lab on Research page still works | regression | P1 | `/research` |
| UT-26 | J-01 Dashboard risk score and stock list still render | regression | P1 | `/` |
| UT-27 | As-of date selector (?asof) still controls the full page | regression | P1 | `/` |
| UT-28 | Samples drill-down from prior Regime×Setup×Pattern lab still counts correctly | regression | P1 | `/research/samples` |
| UT-29 | Timeline section is discoverable by scrolling the Dashboard | ux | P2 | `/` |
| UT-30 | Recovery-Turn Edge lab is discoverable from the Research page | ux | P2 | `/research` |
| UT-31 | Retrospective toggle is clearly labelled as analysis-only | ux | P2 | `/` |

**P1 tests must all pass for browser QA verdict to be PASS.**
