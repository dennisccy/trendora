# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37
**Date:** 2026-06-19
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Context

No frontend code changed in this iteration. The three changed files are backend engine internals (`prices.py`, `data_manager.py`, `test_bar_cache.py`). The `Frontend Present: yes` flag was set exclusively to force a live browser verification of `/data` — the page that was silently broken by the iter-36 cold-miss optimization (connection-pool exhaustion under concurrent reads). This plan covers:

1. A reliability smoke test of `/data` page hydration (the direct target of this iteration's fix).
2. Regression checks confirming adjacent pages (`/stocks`, `/stocks/NVDA`, `/`) are unaffected.

No new components, routes, forms, or navigation items exist to test. Validation and error-input tests are not applicable for this iteration.

---

## Important Constraint — /data Page Load Protocol

`GET /api/data` takes approximately 10–12 seconds on the full 1370-date database. The `/data` page fetches this endpoint exactly **once** on page load (no polling). Follow this protocol for all `/data` test steps:

1. Before loading `/data`, confirm backend readiness: open `http://localhost:8835/api/health` in a new tab and verify the response contains `"readiness":"ready"`.
2. Load `/data` **once** and wait up to **30 seconds** for full hydration.
3. Do **not** reload the page mid-test, open a second concurrent tab to `/data`, or navigate away and back rapidly — doing so risks connection-pool exhaustion (skeleton frame, never hydrates).

---

## Test Cases

---

### UT-01 — Backend health confirms readiness before /data load (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/api/health` (backend health endpoint — prerequisite gate)

**Preconditions:**
- Backend is running at `http://localhost:8835`
- At least one boot cycle has completed (background warm-up is done)

**Steps:**
1. Open a new browser tab and navigate to `http://localhost:8835/api/health`
2. Wait up to 10 seconds for the response to appear
3. Read the JSON body returned in the browser

**Expected Result:**
- HTTP 200 response is received
- The JSON body contains `"readiness": "ready"` (not `"warming"` or `"unavailable"`)
- The JSON body contains `"db_ok": true`
- No error message or HTML error page is shown

**Broken looks like:** JSON shows `"readiness": "warming"` or the page returns a 503/502. If this occurs, wait 60 seconds and retry before proceeding to UT-02.

---

### UT-02 — /data page hydrates without skeleton frame (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- UT-01 passed: backend health endpoint returns `"readiness": "ready"` and `"db_ok": true`
- Frontend is running at `http://localhost:3835`
- No other browser tab is open to `/data` or running a concurrent `/api/data` fetch

**Steps:**
1. Open a fresh browser tab and navigate to `http://localhost:3835/data`
2. Wait up to 30 seconds for the page to fully hydrate (observe the content area)
3. After 30 seconds, look at the main content area of the page

**Expected Result:**
- The page title or heading "Data Manager" (or equivalent) is visible in the content area
- The membership-timeline section renders with a chart or table — not an empty placeholder or spinning loader
- The coverage-diagnostic section renders with at least one numeric value (admitted count or excluded-by-reason counts)
- The text "Checking backend…" does NOT persist in the content area after 30 seconds
- No full-page blank white screen or "Error loading data" message appears

**Broken looks like:** The content area still shows "Checking backend…" or a skeleton placeholder after 30 seconds. This is the iter-36 regression symptom (connection-pool exhaustion). Do not reload the page — record as FAIL with a screenshot.

---

### UT-03 — /data page membership-timeline chart is visible (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — membership-timeline section

**Preconditions:**
- UT-02 passed: `/data` page is fully hydrated (no skeleton, content is visible)
- The membership-timeline section is in or can be scrolled to in the viewport

**Steps:**
1. On the already-loaded `http://localhost:3835/data` page (do not reload), scroll down to the membership-timeline section
2. Locate the chart that shows the step-function of admitted-symbol count over time
3. Observe the chart area for rendered content
4. Scroll horizontally or vertically if needed to see the full chart

**Expected Result:**
- A chart is rendered (SVG lines, canvas pixels, or bar segments are visible — not blank/white)
- The chart shows a rising step-function pattern with at least two distinct count levels
- The chart is not hidden behind an overflow clip or collapsed to zero height
- Three honesty labels are present somewhere near the chart area: the words "Survivorship", "Warm-up", and "Universe-relative" each appear at least once in the membership-timeline panel

**Broken looks like:** Chart area is blank/white, zero-height, or shows only axes with no data plotted. Or one of the three honesty labels is absent from the panel.

---

### UT-04 — /data page coverage-diagnostic section shows admitted and exclusion counts (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — coverage-diagnostic section

**Preconditions:**
- UT-02 passed: `/data` page is fully hydrated
- The coverage-diagnostic section is in or can be scrolled to in the viewport

**Steps:**
1. On the already-loaded `http://localhost:3835/data` page, scroll down to the coverage-diagnostic section (cards or table showing per-date counts)
2. Locate the "admitted" count display (a number representing how many symbols are in the current universe for the displayed date)
3. Locate the three exclusion-reason displays labeled: "below_history", "below_price", and "below_ADV" (or equivalent readable labels)
4. Verify that at least one of the exclusion counts is a non-zero number

**Expected Result:**
- The admitted count is a positive integer (greater than 0)
- The three exclusion-reason fields ("below_history", "below_price", "below_ADV" or their display equivalents) are each present with a numeric value
- At least one exclusion count is non-zero (not all three are 0 simultaneously on every visible date)
- No field shows "NaN", "undefined", or "–" where a number is expected

**Broken looks like:** All exclusion counts show 0 on every date (suggests payload was not loaded), or the fields are absent entirely.

---

### UT-05 — /stocks page loads and shows stock list unaffected by backend change (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- Backend is running and warmed up

**Steps:**
1. Open a new browser tab and navigate to `http://localhost:3835/stocks`
2. Wait up to 10 seconds for the page to hydrate
3. Observe the main stock list content area
4. Count the approximate number of stock rows visible or noted in any count badge

**Expected Result:**
- The page title or heading containing "Stocks" is visible
- A list of stock ticker symbols is rendered in the main content area (at least several rows visible)
- No "Checking backend…" skeleton persists after 10 seconds
- An as-of date selector is visible somewhere on the page (exactly one date control)
- The page does NOT show a blank screen or "Error" message

**Broken looks like:** The stock list does not populate after 10 seconds, or the page shows an error message.

---

### UT-06 — /stocks/NVDA detail page loads and shows scores (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/NVDA`

**Preconditions:**
- Frontend is running at `http://localhost:3835`
- NVDA is present in the stock universe (it should be in the live database)

**Steps:**
1. Open a new browser tab and navigate to `http://localhost:3835/stocks/NVDA`
2. Wait up to 10 seconds for the page to hydrate
3. Observe the detail view for NVDA
4. Look for score and bucket values (e.g., a "Bucket" label showing A–E, a numeric score value, and a "Setup" field)

**Expected Result:**
- The page heading or ticker display shows "NVDA"
- A bucket label (one of A, B, C, D, or E) is displayed
- At least one numeric score value is displayed (not blank or "–")
- A "Setup" or "VCP" indicator is present
- The page does NOT show a 404 or "Not found" error

**Broken looks like:** Page returns 404, or all score/bucket fields are blank.

---

### UT-07 — Single as-of date selector present on /stocks page (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:**
- `/stocks` page is fully loaded from UT-05

**Steps:**
1. On the already-loaded `http://localhost:3835/stocks` page, look at the page header or toolbar area
2. Count the number of visible date input controls or date-picker elements on the page
3. Look for any additional hidden date inputs by scanning the full page top to bottom

**Expected Result:**
- Exactly one date input control is visible on the page (a calendar input, date picker, or text field in date format)
- No second date input or date picker appears elsewhere on the page
- The single date control shows the currently selected as-of date (a date in YYYY-MM-DD or similar format)

**Broken looks like:** Two date controls are visible, or no date control is visible at all.

---

### UT-08 — Dashboard page loads and shows market-phase indicator (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/` or `/dashboard`

**Preconditions:**
- Frontend is running at `http://localhost:3835`

**Steps:**
1. Open a new browser tab and navigate to `http://localhost:3835/` (the home or dashboard page)
2. Wait up to 10 seconds for the page to hydrate
3. Look for a market-phase label (e.g., "Expansion", "Bear Market", "Contraction") in the main dashboard area
4. Look for a P(bear) value (a decimal number between 0 and 1, e.g., "0.35" or "35%") in the dashboard area

**Expected Result:**
- The dashboard page renders without a blank screen or persistent skeleton
- A market-phase text label is visible (one of: "Expansion", "Bear Market", "Contraction", "Recovery", or similar regime label)
- A P(bear) numeric value is visible somewhere on the page
- Neither value shows "NaN", "–", or "loading…"

**Broken looks like:** Dashboard renders but the market-phase label or P(bear) value is missing or shows a loading placeholder indefinitely.

---

### UT-09 — /data page content identical to iter-36 baseline (ux / data-integrity check)

**Type:** ux
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- UT-02 passed: `/data` page is fully hydrated
- Operator has access to iter-36 screenshots or recall of the iter-36 state for visual comparison

**Steps:**
1. On the already-loaded `http://localhost:3835/data` page, note the admitted count number shown in the coverage-diagnostic section
2. Note the shape of the membership-timeline chart (rising step function, approximate final count level)
3. Note any symbol names or counts visible in the membership-timeline panel
4. Compare these values against any prior screenshot or known reference values from iter-36

**Expected Result:**
- The admitted count, exclusion-reason counts, and membership-timeline chart all show values consistent with the iter-36 state
- No new symbols appeared, no existing symbols disappeared from the coverage view
- The membership-timeline chart's final (rightmost) count is identical to what was shown before this iteration
- No numeric value changed as a result of this backend-only fix

**Broken looks like:** The admitted count or excluded counts show different numbers from iter-36, suggesting the bar-cache fix inadvertently changed the resolution math.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Backend health confirms readiness before /data load | smoke | P1 | `/api/health` |
| UT-02 | /data page hydrates without skeleton frame | smoke | P1 | `/data` |
| UT-03 | /data membership-timeline chart is visible | happy-path | P1 | `/data` |
| UT-04 | /data coverage-diagnostic section shows admitted and exclusion counts | happy-path | P1 | `/data` |
| UT-05 | /stocks page loads and shows stock list unaffected | regression | P1 | `/stocks` |
| UT-06 | /stocks/NVDA detail page loads and shows scores | regression | P1 | `/stocks/NVDA` |
| UT-07 | Single as-of date selector present on /stocks | regression | P2 | `/stocks` |
| UT-08 | Dashboard page loads and shows market-phase indicator | regression | P2 | `/` |
| UT-09 | /data content identical to iter-36 baseline | ux | P2 | `/data` |

**P1 tests (UT-01 through UT-06) must all pass for browser QA verdict to be PASS.**

**Known limitation:** `GET /api/data` latency is ~10–12 s on the full production database. UT-02 allows 30 s wait — this is intentional and expected, not a test failure.
