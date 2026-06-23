# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48
**Date:** 2026-06-23
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Context

This iteration is a backend memory-safety fix. No frontend source files were changed. The user-visible outcome is that `/research/factor-lab` now renders a real decile table (D1–D10) and rank-IC value instead of a "Backend unavailable" error banner. `/research/factor-combination` cold-miss path is also hardened. All page structure, layout, labels, and navigation are unchanged.

**Frontend Present:** yes — the acceptance criterion is a rendered lab, so browser verification is required even though no frontend code changed.

---

## Test Cases

---

### UT-01 — Factor Lab page loads without error banner (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Backend is running at `http://localhost:8835` and health endpoint returns "ready" (warm-up complete)
- Frontend is running at `http://localhost:3835`
- No other heavy API requests in flight (quiet backend)

**Steps:**
1. Navigate to `http://localhost:3835/research/factor-lab`
2. Wait up to 10 seconds for the initial page skeleton to appear

**Expected Result:**
- The page renders a heading or panel labelled "Factor Lab" (or equivalent research-lab title)
- The factor dropdown selector is visible on the page
- The horizon selector is visible on the page
- The text "Backend unavailable" does NOT appear anywhere on the page
- No JavaScript error dialog or blank white screen appears

---

### UT-02 — Factor Lab renders real decile table with a column factor (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Backend is running at `http://localhost:8835`, health "ready", warm-up complete
- Frontend is running at `http://localhost:3835`
- No concurrent heavy API requests in flight
- Live database contains at least one scanner run with ForwardReturn rows

**Steps:**
1. Navigate to `http://localhost:3835/research/factor-lab`
2. Wait for the factor dropdown to become interactive (not greyed out or loading)
3. Open the factor dropdown and select "RS 3m" (a column-type factor)
4. Open the horizon dropdown and select "20d"
5. Wait up to 120 seconds for the decile table to populate — the compute is cold and takes 50–120 seconds on the full live dataset

**Expected Result:**
- A decile table appears with exactly 10 rows labelled D1 through D10
- Each row shows a numeric mean return value (e.g. "1.23%" or "−0.45%"), not blank or "NaN"
- Each row shows a numeric risk-adjusted return value
- Each row shows a non-zero sample count (n), e.g. "N=312"
- A rank-IC value is displayed (e.g. "Rank IC: 0.006" or "Rank IC: −0.012") — the value is a numeric figure, not blank or "Loading…"
- The "Backend unavailable — No figures are shown rather than fabricated values" error banner does NOT appear

---

### UT-03 — Factor Lab renders real decile table with a component factor reading record_json (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Backend is running at `http://localhost:8835`, health "ready", warm-up complete
- Frontend is running at `http://localhost:3835`
- No concurrent heavy API requests in flight
- Live database contains ScannerResult rows with populated record_json fields

**Steps:**
1. Navigate to `http://localhost:3835/research/factor-lab`
2. Wait for the factor dropdown to become interactive
3. Open the factor dropdown and select a component factor (a factor labelled "RS SPY 3m" or any factor whose name suggests a nested/derived value — if unsure, select the second or third item in the dropdown that is not "RS 3m")
4. Open the horizon dropdown and select "5d"
5. Wait up to 120 seconds for the decile table to populate

**Expected Result:**
- A decile table appears with exactly 10 rows labelled D1 through D10
- Each row shows a numeric mean return, numeric risk-adjusted return, and a non-zero sample count
- The rank-IC statistic displays a numeric value
- The "Backend unavailable" error banner does NOT appear
- No row shows "NaN" or a blank value for mean return where n > 0

---

### UT-04 — N= chip on a decile row opens samples drill-down in a new tab (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab` and `/research/samples`

**Preconditions:**
- Factor Lab decile table is visible with real figures (UT-02 or UT-03 has been completed in the same browser session, or the table has been loaded fresh)
- Browser is configured to allow pop-ups or new tabs from localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/research/factor-lab`
2. Select "RS 3m" from the factor dropdown and "20d" from the horizon dropdown
3. Wait up to 120 seconds for the decile table to load
4. Note the exact sample count shown in the "N=" chip on the D1 row (e.g. "N=312")
5. Click the "N=312" chip (or the chip on any decile row that shows a non-zero n)

**Expected Result:**
- A new browser tab opens navigating to `http://localhost:3835/research/samples` (with query parameters encoding the factor, horizon, and decile)
- The samples page loads and displays a total observation count
- The total count shown on the samples page equals the n value that was displayed in the chip clicked in step 5 (e.g. if the chip said "N=312", the samples page total is 312)
- No error page or "Backend unavailable" banner appears on the samples tab

---

### UT-05 — Factor Lab shows honest error banner on a genuine backend fault, not fabricated data (error)

**Type:** error
**Priority:** P2
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Backend is intentionally stopped or unreachable (the operator can test this by navigating to the page while the backend is not running, then starting the backend afterward)

**Steps:**
1. Stop the backend server (or ensure it is not running at `http://localhost:8835`)
2. Navigate to `http://localhost:3835/research/factor-lab`
3. Wait up to 15 seconds for the page to attempt a data load
4. Observe what the page displays

**Expected Result:**
- The page displays the error banner containing the text "Backend unavailable" (or equivalent honest error message)
- The decile table does NOT show any numeric return values — no fabricated figures appear
- The page does not crash (blank white screen or JavaScript exception dialog)
- No data rows appear with synthetic values like "0.00%" or placeholder numbers

---

### UT-06 — Factor Combination page loads with real figures (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/factor-combination`

**Preconditions:**
- Backend is running at `http://localhost:8835`, health "ready"
- Frontend is running at `http://localhost:3835`
- At least two factors are available in the factor combination UI
- No concurrent heavy API requests in flight

**Steps:**
1. Navigate to `http://localhost:3835/research/factor-combination`
2. Wait for the page to load and factor selectors to become interactive
3. Select any two factors from the factor selector (e.g. select "RS 3m" as the first factor and a second available factor)
4. Wait up to 90 seconds for the combined cohort table to populate

**Expected Result:**
- A "Combined" cohort table or section appears showing composite and strict-overlap cohort rows
- At least one cohort row displays a numeric mean return value and a non-zero sample count (pool_n or n)
- The "Backend unavailable" error banner does NOT appear
- The page does not show a loading skeleton that persists past 90 seconds

---

### UT-07 — Event Study page still renders real figures after this iteration (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/setup-pattern` (or the Event Study tab under `/research`)

**Preconditions:**
- Backend is running at `http://localhost:8835`, health "ready", warm-up complete
- Frontend is running at `http://localhost:3835`
- Backend is quiet (no concurrent heavy research requests)

**Steps:**
1. Navigate to `http://localhost:3835/research/setup-pattern`
2. Wait for the page to load
3. If a setup type or pattern selector is visible, select any available option
4. Select a horizon of "5d" from the horizon selector
5. Wait up to 30 seconds for event-study cells to populate

**Expected Result:**
- Event-study cells appear showing numeric mean return, risk-adjusted return, and sample count (n) values
- No "Backend unavailable" error banner appears
- The page does not show an unresolved loading skeleton
- Both "first-trigger" and "pooled" mode toggles (if present) display real figures when switched

---

### UT-08 — All five heavy research labs are reachable in a single session (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/factor-lab`, `/research/factor-combination`, `/research/setup-pattern`, `/research/downtrend-opportunity`, and the event-study surface

**Preconditions:**
- Backend is running at `http://localhost:8835`, health "ready"
- Frontend is running at `http://localhost:3835`
- Each lab is loaded one at a time — wait for each to finish before opening the next

**Steps:**
1. Navigate to `http://localhost:3835/research/setup-pattern` (Event Study)
   - Wait up to 30 seconds; confirm numeric cells appear and no error banner is shown
2. Navigate to `http://localhost:3835/research/factor-lab` (Factor Lab)
   - Select "RS 3m" and horizon "20d"; wait up to 120 seconds; confirm decile table with numeric figures appears
3. Navigate to `http://localhost:3835/research/factor-combination` (Factor Combination)
   - Select two factors; wait up to 90 seconds; confirm the combined cohort row shows numeric figures
4. Navigate to the Regime x Setup x Pattern lab (accessible from the research navigation — look for a menu item containing "Regime" or "Pattern")
   - Wait up to 30 seconds; confirm a results table with numeric figures appears and no error banner shows
5. Navigate to the Downtrend Opportunity lab (accessible from the research navigation — look for a menu item containing "Downtrend")
   - Wait up to 30 seconds; confirm results appear with numeric figures and no error banner shows

**Expected Result:**
- All five labs render results with numeric figures at least once during the session
- No lab displays the "Backend unavailable" error banner
- No lab shows a loading skeleton that does not resolve within its budget (30s for cached/fast labs, 120s for Factor Lab)
- Each lab completes before the next is opened

---

### UT-09 — Factor Lab result rank-IC value is numeric, not blank or "NaN" (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Backend is running and warm
- Frontend is running at `http://localhost:3835`
- Factor Lab decile table has been loaded with a valid factor and horizon selection (as in UT-02)

**Steps:**
1. Navigate to `http://localhost:3835/research/factor-lab`
2. Select "RS 3m" from the factor dropdown
3. Select "20d" from the horizon dropdown
4. Wait up to 120 seconds for the decile table to populate
5. Locate the rank-IC statistic displayed on the page (typically labelled "Rank IC", "Rank-IC", or "IC")
6. Read the displayed value

**Expected Result:**
- The rank-IC value is a numeric figure (positive or negative, e.g. "0.006" or "−0.012")
- The value is NOT "NaN", blank, "Loading…", "N/A", or hidden behind any overlay or spinner
- The value does not change to "Backend unavailable" text or disappear after the table renders

---

### UT-10 — Research pages use no native date picker input elements (regression / J-18)

**Type:** regression
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Browser DevTools are accessible (press F12)

**Steps:**
1. Navigate to `http://localhost:3835/research/factor-lab`
2. Wait for the page to fully load
3. Open browser DevTools (press F12)
4. Navigate to the "Elements" or "Inspector" tab
5. Use the search function within DevTools (Ctrl+F or Cmd+F in the Elements panel) and search for `input[type="date"]`

**Expected Result:**
- Zero `<input type="date">` elements are found in the page DOM
- Date navigation (if any as-of date control is visible) uses the application's custom date control, not a native browser date input
- Historical as-of date state, when present in the URL, appears as `?asof=YYYY-MM-DD` (no native date picker required to change it)

---

### UT-11 — Factor Lab page is reachable from the Research navigation (ux)

**Type:** ux
**Priority:** P2
**Surface:** navigation / research hub

**Preconditions:**
- Frontend is running at `http://localhost:3835`

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Look at the navigation items, tabs, or sidebar links on the research page
3. Identify an item labelled "Factor Lab" or containing the word "Factor"
4. Click that navigation item

**Expected Result:**
- The URL changes to `http://localhost:3835/research/factor-lab` (or a route containing "factor-lab")
- The Factor Lab page loads showing the factor dropdown and horizon selector
- The navigation item for Factor Lab is visible without scrolling (not hidden in a collapsed menu) and requires no more than one click from the `/research` hub

---

### UT-12 — Factor Lab loading state transitions correctly from spinner to table (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research/factor-lab`

**Preconditions:**
- Backend is running and warm
- Frontend is running at `http://localhost:3835`

**Steps:**
1. Navigate to `http://localhost:3835/research/factor-lab`
2. Select "RS 3m" from the factor dropdown and "5d" from the horizon dropdown
3. Immediately observe the page state (within the first 5 seconds of submitting the selection)
4. Continue watching the page for up to 120 seconds

**Expected Result:**
- Within the first 5 seconds: the page displays a loading indicator (skeleton rows, spinner, or "Loading…" text) — this confirms the request is in progress
- Within 120 seconds: the loading indicator is replaced by the real decile table (D1–D10 rows with numeric values)
- The loading indicator does not persist past 120 seconds — it either resolves to real data or to the "Backend unavailable" error banner (never stays frozen on "Loading…" indefinitely)
- No layout shift or content jump occurs when the table replaces the loading state

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Factor Lab page loads without error banner | smoke | P1 | `/research/factor-lab` |
| UT-02 | Factor Lab renders real decile table with a column factor | happy-path | P1 | `/research/factor-lab` |
| UT-03 | Factor Lab renders real decile table with a component factor | happy-path | P1 | `/research/factor-lab` |
| UT-04 | N= chip opens samples drill-down in a new tab | happy-path | P1 | `/research/factor-lab`, `/research/samples` |
| UT-05 | Factor Lab shows honest error banner on backend fault | error | P2 | `/research/factor-lab` |
| UT-06 | Factor Combination page loads with real figures | regression | P1 | `/research/factor-combination` |
| UT-07 | Event Study page still renders real figures | regression | P1 | `/research/setup-pattern` |
| UT-08 | All five heavy research labs reachable in one session | regression | P1 | multiple `/research/*` |
| UT-09 | Factor Lab rank-IC value is numeric, not blank or NaN | validation | P1 | `/research/factor-lab` |
| UT-10 | Research pages use no native date picker input elements | regression | P1 | `/research/factor-lab` |
| UT-11 | Factor Lab reachable from Research navigation | ux | P2 | research navigation |
| UT-12 | Factor Lab loading state transitions from spinner to table | ux | P2 | `/research/factor-lab` |

**P1 tests (UT-01 through UT-04, UT-06 through UT-10) must all pass for browser QA verdict to be PASS.**

**Critical note on timing:** UT-02, UT-03, UT-04, UT-08, UT-09, and UT-12 all involve Factor Lab cold compute. Allow up to 120 seconds. Run only one Factor Lab request at a time — do not open a second Factor Lab tab while one is computing. Never run the backend test suite concurrently with these browser checks.
