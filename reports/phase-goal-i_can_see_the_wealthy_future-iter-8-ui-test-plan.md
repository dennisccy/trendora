# Phase goal-i_can_see_the_wealthy_future-iter-8 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-8
**Date:** 2026-05-31
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- UT-XX IDs are distinct from the functional plan's TC-XX (API/artifact) IDs. -->
<!-- These cover the user-visible, browser-driven surfaces only. -->

> **Notation:** "the as-of switcher" = the date drop-down in the top bar (right side, left of the
> health pill, `aria-label="View as-of date"`). "the as-of indicator" = the badge immediately to its
> left (`data-testid="asof-indicator"`). A "past date" = any option listed **below** the top
> "Latest · {date}" option in that drop-down (e.g. `2022-10-07`); use whatever older dates the
> drop-down actually offers on the machine under test. "{latest}" = the date shown next to the word
> "Latest" in the drop-down.

---

### UT-01 — Dashboard loads with as-of switcher in top bar (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3835, backend at http://localhost:8835
- At least one stored Scanner Run exists

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Wait for the page to fully load
3. Look at the top bar (the sticky header row above the page content)

**Expected Result:**
- The "Dashboard" heading and the subtitle "The daily snapshot at a glance" are visible
- In the top bar, a date drop-down (`aria-label="View as-of date"`) is visible, left of the health pill
- The drop-down's selected value reads "Latest · {latest}" (e.g. "Latest · 2025-…")
- To the left of the drop-down a quiet badge reads "Latest" (with a clock icon)
- A "Data as-of {latest}" badge is visible in the page body next to the "Dashboard" heading
- No blank screen, no "Backend unavailable" card, no console errors

---

### UT-02 — As-of switcher offers Latest plus stored run dates (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** top bar (all pages)

**Preconditions:**
- On `http://localhost:3835/` with the page loaded
- `GET /api/runs` returns ≥2 run dates

**Steps:**
1. Click the as-of switcher drop-down in the top bar
2. Read the list of options

**Expected Result:**
- The first option reads "Latest · {latest}"
- Below it, one option per older stored run date appears, in descending (newest-first) order, each formatted `YYYY-MM-DD`
- The latest date is NOT duplicated as a separate option below "Latest"
- Each option is a real date string (no blank/"undefined"/"NaN" entries)

---

### UT-03 — Select a past date time-travels the Dashboard (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` + top bar

**Preconditions:**
- On `http://localhost:3835/`, page loaded, ≥2 run dates available
- Note the Dashboard's regime label/score panel values and the "Data as-of {latest}" badge before changing the date

**Steps:**
1. Click the as-of switcher drop-down
2. Select a past date (e.g. `2022-10-07`) — call it D_OLD
3. Wait for the Dashboard panels to re-render

**Expected Result:**
- The "Data as-of" badge in the page body now reads "Data as-of {D_OLD}" (not {latest})
- The regime / breadth / candidate panels render populated values for D_OLD (no "Backend unavailable" card, no empty panels)
- At least one visible value (regime label or score, or a candidate count) differs from what was shown at latest, confirming a genuine re-point rather than an unchanged page

---

### UT-04 — Historical indicator badge appears and clears (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** top bar (all pages)

**Preconditions:**
- On `http://localhost:3835/`, page loaded, ≥2 run dates available

**Steps:**
1. Confirm the indicator badge left of the drop-down currently reads "Latest"
2. Click the as-of switcher and select a past date D_OLD
3. Observe the indicator badge
4. Click the as-of switcher and select the top "Latest · {latest}" option
5. Observe the indicator badge again

**Expected Result:**
- After step 2–3: the indicator turns into an amber badge reading exactly "Viewing as-of {D_OLD} (historical)" with a history (clock-rewind) icon
- After step 4–5: the amber badge disappears and the quiet "Latest" badge returns
- The drop-down's selected value returns to "Latest · {latest}"

---

### UT-05 — Selected date carries across in-app navigation (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`, `/stocks`, `/themes`, `/sectors`

**Preconditions:**
- On `http://localhost:3835/`, page loaded, ≥2 run dates available

**Steps:**
1. Select a past date D_OLD in the as-of switcher
2. Click "Stocks" in the left sidebar
3. Read the "as of {date}" badge near the "Stocks" heading and the top-bar indicator
4. Click "Themes" in the left sidebar; read its "as of {date}" badge
5. Click "Sectors" in the left sidebar; read its "as of {date}" badge

**Expected Result:**
- On `/stocks`: the body badge reads "as of {D_OLD}" and the top-bar indicator still reads "Viewing as-of {D_OLD} (historical)"
- On `/themes`: the body badge reads "as of {D_OLD}"
- On `/sectors`: the body badge reads "as of {D_OLD}"
- The drop-down kept D_OLD selected throughout — the date was not reset when navigating between pages

---

### UT-06 — Stocks leaderboard reflects the selected date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend + backend running; ≥2 run dates available

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Confirm the body badge reads "as of {latest}" and rows are populated; note NVDA's rank/scores if present
3. Select a past date D_OLD in the top-bar as-of switcher
4. Wait for the leaderboard to re-render

**Expected Result:**
- After step 4: the body badge reads "as of {D_OLD}"
- The leaderboard still shows ranked stock rows (non-empty)
- At least one stock's row position or score differs from the latest view, confirming the historical snapshot is served (not the latest)

---

### UT-07 — Leaderboard filters still work after re-point (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- On `http://localhost:3835/stocks` with rows rendered (latest view)

**Steps:**
1. Click the "Filter by sector" drop-down (labelled "Sector") above the leaderboard
2. Select any single sector other than "All sectors"
3. Observe the leaderboard rows
4. Set the sector filter back to "All sectors"

**Expected Result:**
- After step 2–3: the row set shrinks to only stocks in the chosen sector
- After step 4: all rows return
- The "as of {latest}" badge is unchanged by filtering (the filter does not alter the as-of date)

---

### UT-08 — Stock detail matches leaderboard scores at latest and historical (regression / coherence)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`, `/stocks/[ticker]`

**Preconditions:**
- Frontend + backend running; NVDA present in the snapshot

**Steps:**
1. Navigate to `http://localhost:3835/stocks` (latest view)
2. Note NVDA's Leadership, Entry Quality, and Risk scores from its row
3. Click the NVDA row to open `http://localhost:3835/stocks/NVDA`
4. Read NVDA's Leadership, Entry Quality, and Risk scores on the detail page
5. Select a past date D_OLD in the top-bar switcher (stay on the detail page)
6. Go back to `/stocks` (sidebar "Stocks") and re-read NVDA's three scores for D_OLD, then reopen `/stocks/NVDA`

**Expected Result:**
- At latest: the three scores on `/stocks/NVDA` are identical to NVDA's row on `/stocks`
- The detail page's body badge reads "as of {latest}" initially, then "as of {D_OLD}" after step 5
- At D_OLD: the three scores again match between list and detail (coherence holds in the historical view too)

---

### UT-09 — Stock price chart shows no future bars in a historical view (happy path / no-lookahead)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/[ticker]` — `StockChartPanel`

**Preconditions:**
- On `http://localhost:3835/stocks/NVDA`; chart panel visible

**Steps:**
1. At latest, read the chart caption "{n} bars · as of {latest}" and note the right-most (most recent) bar date
2. Select a past date D_OLD in the top-bar as-of switcher
3. Wait for the chart to re-render and read the caption again

**Expected Result:**
- After step 3: the caption reads "{n} bars · as of {D_OLD}"
- The chart's right-most bar is on or before D_OLD — no bar dated after D_OLD is plotted
- The bar count is ≤ the latest-view bar count (the historical slice is truncated, not extended)
- The moving-average line ends at/before D_OLD as well

---

### UT-10 — Themes page reflects the selected date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/themes`

**Preconditions:**
- Frontend + backend running; ≥2 run dates available

**Steps:**
1. Navigate to `http://localhost:3835/themes`
2. Confirm the body badge reads "as of {latest}" and theme rows render; note the top theme's score
3. Select a past date D_OLD in the top-bar as-of switcher
4. Wait for the theme table to re-render

**Expected Result:**
- After step 4: the body badge reads "as of {D_OLD}"
- The theme table still renders populated rows
- At least one theme's score or ordering differs from the latest view, confirming the historical snapshot is served

---

### UT-11 — Sectors page reflects the selected date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/sectors`

**Preconditions:**
- Frontend + backend running; ≥2 run dates available

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Confirm the body badge reads "as of {latest}" and sector rows render; note the top sector's score
3. Select a past date D_OLD in the top-bar as-of switcher
4. Wait for the sector table to re-render

**Expected Result:**
- After step 4: the body badge reads "as of {D_OLD}"
- The sector table still renders populated rows
- At least one sector's score or ordering differs from the latest view, confirming the historical snapshot is served

---

### UT-12 — Reset to Latest restores the current view everywhere (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`, `/stocks`, `/themes`, `/sectors` + top bar

**Preconditions:**
- A past date D_OLD is currently selected (continue from any historical test above)

**Steps:**
1. With D_OLD selected, navigate to `/stocks`
2. Open the as-of switcher and select the top "Latest · {latest}" option
3. Read the body "as of" badge and the top-bar indicator
4. Navigate to `/`, `/themes`, `/sectors` in turn

**Expected Result:**
- After step 3: the body badge reads "as of {latest}"; the top-bar indicator reads "Latest" (quiet, not amber)
- On `/`, `/themes`, `/sectors`: each shows its latest-date badge ("Data as-of {latest}" / "as of {latest}")
- All pages show the same values they showed before any historical date was selected

---

### UT-13 — Hard refresh returns to Latest (ux / known limitation)

**Type:** ux
**Priority:** P3
**Surface:** any as-of-aware page

**Preconditions:**
- A past date D_OLD is selected on `http://localhost:3835/stocks`

**Steps:**
1. With D_OLD selected and "as of {D_OLD}" shown, press F5 (hard browser reload)
2. Wait for the page to reload and read the badge + indicator

**Expected Result:**
- After reload: the body badge reads "as of {latest}" and the top-bar indicator reads "Latest"
- This is the documented behavior — the as-of date is held in client state only and is intentionally not encoded in the URL, so a hard reload returns to Latest. (In-app navigation preserves it; a hard refresh does not.)

---

### UT-14 — As-of-aware page surfaces a clear error on backend failure (error)

**Type:** error
**Priority:** P2
**Surface:** `/` (and other as-of pages)

**Preconditions:**
- Frontend running; backend at :8835 stopped (or unreachable) — coordinate with the operator to stop it for this single check, then restart

**Steps:**
1. With the backend stopped, navigate to `http://localhost:3835/`
2. Observe the page body

**Expected Result:**
- A "Backend unavailable" card appears reading "The dashboard could not load the market regime from the API. Nothing is fabricated — confirm the backend is running and reload."
- The page does NOT show a blank white screen or a fabricated/placeholder dataset
- After restarting the backend and reloading, the Dashboard renders normally with the "Data as-of {latest}" badge

---

### UT-15 — Switcher discoverability and labelling (ux)

**Type:** ux
**Priority:** P2
**Surface:** top bar (all pages)

**Preconditions:**
- On `http://localhost:3835/`

**Steps:**
1. Without prior instruction, locate the control that lets you view a past trading day
2. Read its accessible label and the indicator beside it

**Expected Result:**
- The date drop-down is visible in the top bar on every page (it persists across navigation), within one glance of the page header — no extra navigation needed
- Its accessible label is "View as-of date"; the current state is communicated by the adjacent badge ("Latest" vs amber "Viewing as-of {date} (historical)")
- The historical state is unmistakable: amber colour + the explicit word "(historical)" + the date

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Dashboard loads with switcher | smoke | P1 | `/` |
| UT-02 | Switcher lists Latest + run dates | smoke | P1 | top bar |
| UT-03 | Past date time-travels Dashboard | happy-path | P1 | `/` |
| UT-04 | Historical indicator appears/clears | happy-path | P1 | top bar |
| UT-05 | Date carries across navigation | happy-path | P1 | `/`,`/stocks`,`/themes`,`/sectors` |
| UT-06 | Stocks leaderboard re-points | happy-path | P1 | `/stocks` |
| UT-07 | Leaderboard filters still work | regression | P1 | `/stocks` |
| UT-08 | List↔detail score coherence | regression | P1 | `/stocks`, `/stocks/[ticker]` |
| UT-09 | Chart no-lookahead historical | happy-path | P1 | `/stocks/[ticker]` |
| UT-10 | Themes page re-points | happy-path | P1 | `/themes` |
| UT-11 | Sectors page re-points | happy-path | P1 | `/sectors` |
| UT-12 | Reset to Latest restores view | happy-path | P1 | all as-of pages |
| UT-13 | Hard refresh returns to Latest | ux | P3 | any |
| UT-14 | Backend-failure error surfaced | error | P2 | `/` |
| UT-15 | Switcher discoverability/labels | ux | P2 | top bar |

**P1 tests (UT-01 through UT-12) must all pass for the browser QA verdict to be PASS.**
