# Goal Iter-13 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13
**Date:** 2026-06-13
**Frontend Present:** yes

## Phase Goal

The user can see exactly which dates have data (a per-trading-date availability heatmap on `/data`) and pick the as-of date from a calendar popover that marks only the selectable snapshot dates — both read from existing single sources, neither introducing a second date state.

---

## Test Cases

### TC-01 — Availability heatmap renders on `/data` with legend

**Type:** browser
**Preconditions:** Frontend is running; backend has at least 10 trading days of bars data.

**Steps:**
1. Navigate to `http://localhost:3000/data`
2. Locate the availability heatmap card in the page
3. Verify the legend is present and visible

**Expected outcome:** The heatmap card appears on `/data` with a color legend showing coverage density.
**Pass criteria:** The card is rendered with title, grid, and legend visible; no 404 or missing-component errors.

---

### TC-02 — Heatmap cells color by symbols_with_bars density

**Type:** browser
**Preconditions:** Backend `/api/data/availability` returns mixed data: some dates with 0 symbols, some with 50%, some with 100%.

**Steps:**
1. Navigate to `/data`
2. Observe the heatmap grid cells
3. Compare color intensity across sparse days (e.g. 3-of-158), medium days (e.g. 80-of-158), and full days (158-of-158)

**Expected outcome:** Sparse days visually distinct (lighter color) from full days (darker color); no two-state rendering (all cells rendered).
**Pass criteria:** Cells with different `symbols_with_bars` values have visibly different colors; a zero-bar trading day renders as empty (lightest or explicitly blank).

---

### TC-03 — Heatmap hover tooltip shows exact figures

**Type:** browser
**Preconditions:** Heatmap is rendered on `/data`; a trading day has 50 symbols with bars and 158 total.

**Steps:**
1. Hover over a heatmap cell with a known data count
2. Wait for tooltip to appear
3. Read the tooltip text

**Expected outcome:** Tooltip displays date (ISO format yyyy-MM-dd), symbol count (e.g. "50 / 158"), and snapshot yes/no indicator.
**Pass criteria:** Tooltip text exactly matches backend payload for that date; formatting is consistent (monospace or tabular style).

---

### TC-04 — Heatmap shows snapshot marker on computed snapshot dates

**Type:** browser
**Preconditions:** At least one trading day has an associated snapshot (run_date).

**Steps:**
1. Navigate to `/data`
2. Locate a trading day that has a snapshot in the backend data
3. Observe the cell rendering

**Expected outcome:** The cell has a distinct visual marker (dot, ring, or badge) indicating a snapshot was computed.
**Pass criteria:** Cells with `snapshot_exists=true` show the marker; cells with `snapshot_exists=false` do not.

---

### TC-05 — Clicking a heatmap day prefills job-form Start date (not as-of state)

**Type:** browser
**Preconditions:** Heatmap is rendered; job form (Start/End date inputs) is visible on `/data`.

**Steps:**
1. Verify the current as-of date via the top-bar control (take note of current value)
2. Click a heatmap day with date 2026-01-15
3. Observe the job form's Start date input
4. Verify the top-bar as-of control is unchanged

**Expected outcome:** The job-form Start input is prefilled with 2026-01-15; the as-of state and historical badge remain unchanged.
**Pass criteria:** Job form Start date = clicked heatmap day; as-of control shows the same date as before the click; URL `?asof` parameter is unchanged.

---

### TC-06 — Heatmap re-reads availability after a job completes

**Type:** browser
**Preconditions:** Heatmap is rendered showing sparse initial data; a job (fetch/backfill) can be triggered.

**Steps:**
1. Note the current coverage (e.g. symbols_with_bars on a specific date)
2. Trigger a fetch/backfill job via the job form (do not actually fetch external data; use a quick local mock if needed)
3. Wait for the job to complete
4. Observe the heatmap

**Expected outcome:** The heatmap re-fetches from `/api/data/availability` and updates the grid to reflect new coverage (if the job added bars).
**Pass criteria:** After job completion, the heatmap cell counts match the new backend state; no manual page refresh required.

---

### TC-07 — Empty DB renders gracefully with no fabricated cells

**Type:** browser
**Preconditions:** Backend is fresh with no bars or runs data.

**Steps:**
1. Clear the backend data (via test fixture or direct DB reset)
2. Navigate to `/data`
3. Locate the heatmap card

**Expected outcome:** The heatmap renders (no 404 or 500); cells are absent, blank, or explicitly marked as "no data"; no fabricated coverage values shown.
**Pass criteria:** The heatmap div is present; no cells are rendered with false data; the legend is visible but grayed out or disabled.

---

### TC-08 — As-of calendar popover opens from the top-bar control

**Type:** browser
**Preconditions:** Frontend is running; top-bar as-of switcher is visible.

**Steps:**
1. Locate the as-of control in the top bar (was a dropdown, now a calendar button/trigger)
2. Click the control to open the popover

**Expected outcome:** A calendar popover (month grid) appears anchored to the control.
**Pass criteria:** Popover is visible, displays a month grid with day cells, a month header, and navigation arrows or buttons.

---

### TC-09 — Calendar popover marks selectable snapshot dates and disables non-selectable dates

**Type:** browser
**Preconditions:** Backend `/api/runs` returns a list of snapshot dates; at least 5 snapshot dates exist, and some trading dates have no snapshot.

**Steps:**
1. Open the as-of calendar popover
2. Observe the current month's cells
3. Identify a date with a snapshot (marked/enabled) vs. a trading date with no snapshot (unmarked/disabled)

**Expected outcome:** Selectable dates (those in the `dates` array from `asof-provider`) are visually distinct (highlighted, clickable); non-selectable dates are muted or disabled (no hover, no click reaction).
**Pass criteria:** At least one selectable and one non-selectable date are visible; clicking a non-selectable date has no effect; clicking a selectable date works (see TC-10).

---

### TC-10 — Selecting a date from the calendar calls setAsOf and updates app state exactly as today

**Type:** browser
**Preconditions:** Calendar popover is open; at least one historical snapshot date is available.

**Steps:**
1. Open the calendar popover
2. Navigate to a previous month (if needed to reach a historical date)
3. Click a selectable date from, e.g., 2 months ago
4. Observe the popover closes
5. Check the top-bar as-of control shows the selected date
6. Check the historical badge appears
7. Verify the `?asof` URL parameter is set
8. Verify href stamping (e.g. on a ticker link) includes the `?asof` param

**Expected outcome:** Clicking the date re-points the entire app to the historical snapshot state exactly as if the user had selected it via the old dropdown (no behavioral difference).
**Pass criteria:** As-of control displays the selected date; historical badge is shown; `?asof=YYYY-MM-DD` is in the URL; all data and links reflect the historical as-of; app behavior is identical to pre-calendar behavior.

---

### TC-11 — Calendar popover month navigation reaches the oldest stored month

**Type:** browser
**Preconditions:** Backend has 6+ months of snapshot data.

**Steps:**
1. Open the calendar popover
2. Click the previous-month button repeatedly until no further navigation is possible
3. Note the displayed month
4. Verify it contains selectable dates

**Expected outcome:** The month navigation reaches the earliest month with stored snapshots; further back navigation is disabled or loops back.
**Pass criteria:** The oldest month with selectable dates is reachable; clicking prev/back when on the oldest month has no effect or cycles forward.

---

### TC-12 — Calendar popover "Latest" button returns to the latest view

**Type:** browser
**Preconditions:** Calendar popover is open; a historical date is currently selected (as-of is in the past).

**Steps:**
1. Verify the current as-of shows a past date (e.g. 2026-01-15)
2. Locate the "Latest" button in the popover
3. Click "Latest"
4. Observe the popover closes
5. Check the top-bar as-of control

**Expected outcome:** The app returns to the latest snapshot date; the historical badge disappears; the `?asof` URL parameter is removed or set to the latest date.
**Pass criteria:** Top-bar shows the latest date and is no longer marked as historical; `?asof` param is absent (or points to today's date); all data resets to live view.

---

### TC-13 — Calendar popover is keyboard operable

**Type:** browser
**Preconditions:** Calendar popover is open.

**Steps:**
1. With popover open, press arrow keys to navigate days
2. Press Enter or Space to select the focused day
3. Press Escape to dismiss the popover

**Expected outcome:** All keyboard interactions work without mouse; the selected date is applied on Enter; the popover closes on Escape.
**Pass criteria:** Arrow navigation moves focus within the grid; Enter selects the focused date and applies it (no mouse needed); Escape closes the popover.

---

### TC-14 — Invalid ?asof URL parameter degrades to latest view

**Type:** browser
**Preconditions:** Backend has snapshot dates; no snapshot exists for 2099-12-31.

**Steps:**
1. Navigate directly to `http://localhost:3000/stocks?asof=2099-12-31` (an invalid/future date)
2. Observe the page loading

**Expected outcome:** The page loads without error; the as-of control shows the latest date; no historical badge is shown; data reflects the latest view.
**Pass criteria:** App gracefully handles the invalid `?asof` parameter; the as-of state is set to the latest valid snapshot (matching J-43 behavior, unchanged from pre-calendar version).

---

### TC-15 — Availability endpoint returns correct per-date counts

**Type:** api
**Preconditions:** Backend is running; `/api/data/availability` endpoint exists.

**Steps:**
1. Run: `curl -s http://localhost:8000/api/data/availability | jq '.' | head -30`
2. Pick a known date (e.g. 2026-01-15) with verified bar counts in the DB
3. Find that date's entry in the response

**Expected outcome:** The response is valid JSON with array of `{ date, symbols_with_bars, total_symbols, snapshot_exists }` objects; counts match the backend data for that date.
**Pass criteria:** Response status is 200; structure matches spec; `symbols_with_bars` on a known date equals the stored bar count; `total_symbols` is consistent across dates (same universe); `snapshot_exists` is true only for dates with a stored run.

---

### TC-16 — Availability endpoint empty DB returns graceful empty payload

**Type:** api
**Preconditions:** Backend is reset to empty (no bars, no runs).

**Steps:**
1. Clear the database
2. Run: `curl -s http://localhost:8000/api/data/availability`
3. Observe the response

**Expected outcome:** HTTP 200 with an empty array `[]` (no 500 error, no fabricated cells).
**Pass criteria:** Status code is 200; response body is `[]` or valid JSON with no cell entries; no error message in the response.

---

### TC-17 — Zero-bar trading day renders as 0, not omitted

**Type:** api
**Preconditions:** Backend has a trading day with no bars (e.g. 2026-03-10) but the day is within the SPY trading calendar.

**Steps:**
1. Run: `curl -s http://localhost:8000/api/data/availability | jq '.[] | select(.date == "2026-03-10")'`
2. Observe the entry

**Expected outcome:** A cell entry exists for 2026-03-10 with `symbols_with_bars=0`; it is not omitted or filtered out.
**Pass criteria:** Entry is present with exact date and `symbols_with_bars=0`; the day is visible on the heatmap (empty/lightest color).

---

### TC-18 — Availability counts match compute_coverage semantics

**Type:** api
**Preconditions:** Backend has a multi-day history; `compute_coverage` returns a summary of symbol coverage.

**Steps:**
1. Call `GET /api/data/overview` (which internally calls `compute_coverage`)
2. Note the coverage figures (e.g. `symbol_count=158`)
3. Call `GET /api/data/availability`
4. Verify `total_symbols` on any date matches `symbol_count`
5. For a date with "full" coverage (on the `/data` page overview), verify `symbols_with_bars >= 150` (for the seed, 158-symbol universe)

**Expected outcome:** The availability endpoint's `total_symbols` and symbol counts are consistent with `compute_coverage`'s universe and bar counts.
**Pass criteria:** `total_symbols` is the same across all availability dates (and matches the universe size from `compute_coverage`); sparse dates have `symbols_with_bars < total_symbols`; full dates have `symbols_with_bars >= 95%` of `total_symbols`.

---

### TC-19 — Required-still-passing journey: J-13 (one date control, no second state)

**Type:** browser
**Preconditions:** App is running; multiple date controls exist in old behavior.

**Steps:**
1. Navigate to `/data`
2. Click a heatmap day to prefill job form (TC-05)
3. Verify only the job-form Start date changes
4. Open and select a historical date from the calendar popover (TC-10)
5. Verify only the global as-of state changes (all data re-points)
6. Confirm no page-local independent date state exists (no second as-of, no page-specific calendar)

**Expected outcome:** Only one date selector (the top-bar calendar) controls the global as-of; job form Start/End are independent job parameters; no page-local date state.
**Pass criteria:** The heatmap click does not affect as-of; the calendar popover click does not affect job-form dates; only one control re-points the whole app.

---

### TC-20 — Required-still-passing journey: J-18 (heatmap click ≠ as-of write)

**Type:** browser
**Preconditions:** Job form is visible on `/data`.

**Steps:**
1. Note the current as-of date from the top-bar control
2. Click a heatmap day with a different date
3. Verify the job-form Start date is prefilled
4. Verify the top-bar as-of control is still showing the original date
5. Perform a background check: `curl -s http://localhost:8000/api/runs | jq '.runs[0].asof_date'` to confirm the backend's as-of is unchanged

**Expected outcome:** Clicking the heatmap prefills a job parameter, not the global as-of state.
**Pass criteria:** As-of control is visually unchanged; backend `/api/runs` asof_date is unchanged; job-form date input is updated.

---

### TC-21 — Required-still-passing journey: J-43 (URL ?asof serialization and invalid degradation)

**Type:** browser
**Preconditions:** App is running.

**Steps:**
1. Select a historical date from the as-of calendar (TC-10)
2. Verify the URL shows `?asof=YYYY-MM-DD`
3. Copy the URL and reload the page
4. Verify the same historical view is restored
5. Manually edit the URL to an invalid date (e.g. `?asof=2099-01-01`)
6. Reload; verify the app degrades to latest (TC-14)

**Expected outcome:** Valid `?asof` serializes and restores the view; invalid `?asof` degrades gracefully to latest.
**Pass criteria:** URL round-trip restores state; invalid `?asof` parameter is handled without error (app shows latest, no 404).

---

### TC-22 — Required-still-passing journey: J-50 (href stamping with ?asof)

**Type:** browser
**Preconditions:** Historical date is selected (as-of is in the past).

**Steps:**
1. Select a historical date from the calendar (e.g. 2026-01-15)
2. Locate a ticker link (e.g. a symbol in the members list or data table)
3. Hover and inspect the link's href attribute

**Expected outcome:** The href includes `?asof=2026-01-15` (or equivalent as-of date), so navigating the link preserves the historical context.
**Pass criteria:** Link href contains the current as-of date as a query parameter; clicking the link opens the symbol page with the historical as-of applied.

---

## Summary

**Total test cases:** 22
- **Browser tests:** 17 (TC-01 to TC-14, TC-19 to TC-22)
- **API tests:** 5 (TC-15 to TC-18)
- **Artifact checks:** 0
