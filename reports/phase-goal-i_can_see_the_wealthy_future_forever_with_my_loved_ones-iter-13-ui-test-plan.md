# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13
**Date:** 2026-06-13
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Data page loads with availability heatmap card visible (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8000
- Backend has at least 10 trading days of bars data

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load (all cards visible)
3. Scroll down past the "Dataset Coverage" panel
4. Look for the "Availability Heatmap" card

**Expected Result:**
- The `/data` page loads without a blank screen or error message
- The "Dataset Coverage" panel is visible (existing feature, unchanged)
- A new card titled "Availability Heatmap" (or similar) appears below the Dataset Coverage panel
- The heatmap card contains a month-banded grid of day cells — colored squares or rectangles arranged in calendar rows
- A legend explaining the color ramp (sparse to dense) and the snapshot ring marker is visible inside or below the card
- No "Failed to load" or console error messages appear

---

### UT-02 — Heatmap cells are color-coded by data density (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend has a mix of trading days: some with 0 symbols, some partial, some with full coverage

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Availability Heatmap" card
3. Visually examine the day cells in the grid
4. Identify cells that appear lighter/muted (fewer symbols with bars)
5. Identify cells that appear darker/saturated (more symbols with bars)
6. Look for any cell that displays a ring or dot marker overlay

**Expected Result:**
- Cells with few symbols having bars appear in a lighter, low-saturation color
- Cells with many symbols having bars appear in a darker, high-saturation color
- At least one cell has a visible ring or dot marker indicating a snapshot was computed on that date
- The legend in the card maps the color scale to coverage density (e.g., labels "sparse" at one end and "full" at the other) and identifies the snapshot ring marker

---

### UT-03 — Hovering a heatmap cell shows exact date, symbol count, and snapshot status (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — heatmap hover readout

**Preconditions:**
- Frontend is running at http://localhost:3835
- Availability heatmap is rendered with at least one cell visible

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Availability Heatmap" card
3. Move the mouse cursor over any day cell in the heatmap grid and hold it there for 1 second
4. Read the readout text that appears in the header area above the grid (or in a tooltip near the cell)

**Expected Result:**
- The header readout above the heatmap grid updates (or a tooltip appears) with text in this format:
  - A date in yyyy-MM-dd format (e.g., "2026-01-15")
  - A symbol count fraction (e.g., "50 / 158" or "50 of 158 symbols")
  - A snapshot indicator such as "snapshot: yes" or "snapshot: no"
- The readout changes when the mouse moves to a different cell
- Moving the mouse off all cells returns the readout to a default/empty state or retains the last hovered cell

---

### UT-04 — Clicking a heatmap day prefills the job form Start date and End date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — heatmap click to job form prefill

**Preconditions:**
- Frontend is running at http://localhost:3835
- Availability heatmap is rendered with multiple cells visible
- The Job form on the same page has visible "Start date" and "End date" input fields
- The as-of switcher in the top bar is showing "Latest" or a specific date (take note of the current value)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to see both the Availability Heatmap card and the Job form section
3. Note the current value in the top-bar as-of switcher (e.g., "Latest")
4. Note the current value in the Job form "Start date" input field
5. Click any single day cell in the heatmap grid (remember the date shown in the hover readout)
6. Observe the Job form "Start date" input field value
7. Observe the Job form "End date" input field value
8. Observe the top-bar as-of switcher value

**Expected Result:**
- The Job form "Start date" input changes to the date of the clicked heatmap cell (yyyy-MM-dd format)
- The Job form "End date" input also changes to the same date (single-day click sets both to the same date)
- The top-bar as-of switcher remains unchanged (same value it had before the click)
- The URL does not gain or change a `?asof=` parameter due to the heatmap click
- The heatmap visually highlights the selected cell (distinct border or background color)

---

### UT-05 — Shift-clicking a second heatmap cell sets a date range in the job form (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — heatmap shift-click range prefill

**Preconditions:**
- Frontend is running at http://localhost:3835
- Availability heatmap is rendered with multiple cells across different dates

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the Availability Heatmap card
3. Click one day cell as the range anchor (note the date, e.g., 2026-01-05 — an earlier date)
4. Hold Shift and click a different day cell that is later in the calendar (e.g., 2026-01-20)
5. Release Shift
6. Observe the Job form "Start date" input field value
7. Observe the Job form "End date" input field value

**Expected Result:**
- The Job form "Start date" input shows the earlier of the two clicked dates (e.g., "2026-01-05")
- The Job form "End date" input shows the later of the two clicked dates (e.g., "2026-01-20")
- The top-bar as-of switcher remains unchanged
- The heatmap visually highlights both selected cells and optionally the range between them

---

### UT-06 — As-of switcher in top bar is now a button with chevron, not a select dropdown (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** Top bar (all pages) — `AsOfSwitcher` trigger button

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Look at the top navigation bar
3. Locate the as-of date control (previously a dropdown `<select>` labeled with a date or "Latest")
4. Examine how it is rendered

**Expected Result:**
- The as-of control renders as a button element (not a `<select>` dropdown)
- The button displays either "Latest" (if no historical date is selected) or a yyyy-MM-dd date string
- The button has a chevron icon (down arrow or similar) indicating it opens a popover
- There is no visible `<select>` dropdown control in the top bar for the as-of date

---

### UT-07 — Clicking the as-of button opens a calendar popover with a month grid (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** Top bar (all pages) — `AsOfCalendar` popover

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend has at least one snapshot date in its run history

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Locate the as-of switcher button in the top bar (labeled "Latest" or a yyyy-MM-dd date)
3. Click the as-of switcher button once
4. Observe what appears

**Expected Result:**
- A popover (floating panel) opens below or near the as-of button
- The popover displays a month grid: a header showing the current month and year, day-of-week labels, and a grid of date cells
- Previous-month (`<`) and next-month (`>`) navigation arrows are visible in the popover header
- A "Latest" button is visible inside the popover
- At least one day cell in the grid appears as a distinct, clickable button (snapshot date)
- Other day cells appear muted/disabled (non-snapshot trading days or non-trading days)
- The popover is anchored to the as-of button and does not cover the full page

---

### UT-08 — Selecting a date from the as-of calendar popover updates app state (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** Top bar (all pages) — as-of calendar date selection

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend has at least one historical snapshot date (in a month prior to the current month, or earlier in the current month)
- The as-of switcher currently shows "Latest"

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Click the as-of switcher button in the top bar to open the calendar popover
3. If the current month has no selectable (highlighted) snapshot dates, click the back-arrow (`<`) once to go to the previous month
4. Click one of the visually distinct (enabled/highlighted) day buttons in the popover (a snapshot date)
5. Observe the popover
6. Observe the as-of switcher button label in the top bar
7. Observe the URL in the browser address bar
8. Observe whether a historical badge or indicator appears near the top bar

**Expected Result:**
- The popover closes immediately after clicking the date
- The as-of switcher button label changes from "Latest" to the selected yyyy-MM-dd date (e.g., "2026-05-15")
- The URL changes to include `?asof=2026-05-15` (or the actual selected date)
- A historical indicator badge (e.g., "Historical" or a colored label) appears in the top bar or near the as-of switcher
- The data on the page (stocks list, etc.) re-loads to reflect the selected historical snapshot

---

### UT-09 — Disabled (non-snapshot) days in the as-of calendar cannot be selected (validation)

**Type:** validation
**Priority:** P2
**Surface:** Top bar (all pages) — as-of calendar disabled days

**Preconditions:**
- Frontend is running at http://localhost:3835
- Calendar popover is open and shows a mix of enabled (snapshot) and disabled (non-snapshot) day cells

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Click the as-of switcher button to open the calendar popover
3. Note the current as-of switcher label (e.g., "Latest")
4. Identify a day cell that appears muted or grayed out (a non-snapshot date)
5. Click that muted/disabled day cell
6. Observe the as-of switcher label and the popover state

**Expected Result:**
- The muted day cell does not respond to the click (no visual active/pressed state)
- The popover remains open (does not close on clicking a disabled day)
- The as-of switcher label remains unchanged
- The URL does not gain a `?asof=` parameter for the disabled date

---

### UT-10 — As-of calendar month navigation back-arrow clamps at the oldest snapshot month (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** Top bar (all pages) — as-of calendar month navigation

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend has snapshot dates spanning at least 2 months

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Click the as-of switcher button to open the calendar popover
3. Click the back-arrow (`<`) in the popover header repeatedly until it stops responding or becomes visually disabled
4. Note the month and year displayed in the popover header
5. Attempt to click the back-arrow one more time
6. Observe whether the forward-arrow (`>`) is available

**Expected Result:**
- The back-arrow becomes visually disabled (grayed out, no hover effect) when the oldest snapshot month is displayed
- Clicking the disabled back-arrow has no effect (the month does not change)
- The forward-arrow (`>`) is enabled (not grayed out) when on the oldest month
- The displayed month contains at least one selectable (highlighted) snapshot date

---

### UT-11 — As-of calendar "Latest" button returns to the live view from a historical month (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** Top bar (all pages) — as-of calendar "Latest" button

**Preconditions:**
- Frontend is running at http://localhost:3835
- A historical as-of date is currently selected (the top-bar as-of switcher shows a yyyy-MM-dd date)

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. If the as-of switcher already shows "Latest", first select a historical date via the calendar popover (see UT-08) to put the app into historical mode
3. Verify the as-of switcher button shows a yyyy-MM-dd date and a historical badge is visible
4. Click the as-of switcher button to open the calendar popover
5. Locate the "Latest" button inside the popover
6. Click the "Latest" button
7. Observe the popover state
8. Observe the as-of switcher button label in the top bar
9. Observe the URL

**Expected Result:**
- The popover closes immediately after clicking "Latest"
- The as-of switcher button label changes back to "Latest"
- The historical indicator badge disappears from the top bar
- The URL no longer contains `?asof=` parameter (or it is removed)
- The page data reloads to reflect the current (non-historical) view

---

### UT-12 — As-of calendar popover is keyboard operable (ux)

**Type:** ux
**Priority:** P2
**Surface:** Top bar (all pages) — as-of calendar keyboard navigation

**Preconditions:**
- Frontend is running at http://localhost:3835
- No historical as-of date is selected (switcher shows "Latest")

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Click once on the as-of switcher button in the top bar to open the calendar popover
3. Press the Tab key once or twice until a selectable day button in the popover gains keyboard focus (a focus ring should be visible around the day cell)
4. Press Enter on the focused day button
5. Observe the popover and as-of switcher
6. Open the calendar popover again (click the as-of switcher button)
7. Press the Escape key
8. Observe the popover state and as-of switcher label

**Expected Result:**
- Step 3: Tab key moves focus visibly through the popover elements (arrows, "Latest" button, day buttons)
- Step 4: Pressing Enter on a focused selectable day button selects that date and closes the popover; the as-of switcher updates to show the selected date
- Step 7: Pressing Escape closes the popover without changing the selected date
- After Escape, the as-of switcher button label remains the same as it was before opening (the date selected in step 4 persists)

---

### UT-13 — Heatmap automatically re-fetches after a job completes (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — heatmap post-job re-fetch

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running and has some symbols loaded
- The availability heatmap is visible with initial cell states

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to and observe the Availability Heatmap card — note the state of a specific date's cell (the exact count shown on hover)
3. Scroll to the Job form section
4. Fill in the "Start date" field with a date (e.g., yesterday's date in yyyy-MM-dd format)
5. Fill in the "End date" field with the same date
6. Select "Backfill" as the job type (or the available mode that does not trigger external fetches if one exists)
7. Click the "Run Job" (or equivalent submit) button
8. Watch the job status until it shows a completion state (e.g., "Complete", "Done")
9. Scroll back to the Availability Heatmap card without refreshing the page
10. Hover over the same date cell noted in step 2

**Expected Result:**
- After the job completes (step 8), the heatmap card re-renders its grid without a full page reload
- The cell for the date used in the job now reflects any updated coverage counts
- No browser page reload was required to see the updated heatmap

---

### UT-14 — Heatmap shows a loading state on initial page load (smoke)

**Type:** smoke
**Priority:** P2
**Surface:** `/data` — heatmap loading placeholder

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Open browser developer tools (F12) and go to the Network tab
2. Enable network throttling to "Slow 3G" or equivalent
3. Navigate to `http://localhost:3835/data`
4. Observe the area where the Availability Heatmap card will appear during the loading phase
5. Disable network throttling after the page loads

**Expected Result:**
- While the heatmap data is loading, the heatmap card area shows a loading indicator (spinner, skeleton grid, or placeholder text such as "Loading availability data...")
- After loading completes, the loading indicator is replaced by the actual colored grid
- No unhandled error or blank area appears during the loading phase

---

### UT-15 — Selecting as-of date via calendar still drives ?asof URL and historical badge (regression)

**Type:** regression
**Priority:** P1
**Surface:** Top bar (all pages) — as-of calendar → URL + badge behavior

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend has at least one historical snapshot date
- The app is in "Latest" view (no historical date selected)

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Note the current URL (should have no `?asof=` parameter)
3. Note the as-of switcher label ("Latest")
4. Click the as-of switcher button to open the calendar popover
5. Navigate to a prior month if needed by clicking the back-arrow (`<`)
6. Click a selectable (highlighted) snapshot date cell in the calendar
7. Observe the browser URL bar
8. Observe whether the historical badge/indicator is present near the top bar
9. Copy the URL and open a new browser tab, paste the URL, and press Enter
10. Observe the as-of state in the new tab

**Expected Result:**
- Step 7: The URL now contains `?asof=YYYY-MM-DD` (the selected date)
- Step 8: A historical indicator ("Historical" badge or colored label) is visible in the top bar
- Step 10: The new tab opens with the same historical date applied — the as-of switcher shows the same yyyy-MM-dd date and the historical badge is visible
- All data on the page reflects the historical snapshot, not the latest data

---

### UT-16 — Old dropdown-based as-of behavior is gone (regression)

**Type:** regression
**Priority:** P1
**Surface:** Top bar (all pages) — as-of switcher replacement

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Inspect the top bar visually — look for any `<select>` dropdown control labeled with a date or "Latest"
3. Open browser developer tools (F12), go to the Elements tab
4. Search (Ctrl+F in Elements) for `<select` to find any select elements in the top bar
5. Close developer tools

**Expected Result:**
- No `<select>` dropdown element for the as-of date exists in the top bar
- The only as-of control is the button that opens the calendar popover (tested in UT-06)
- The page still renders correctly without the old dropdown

---

### UT-17 — Heatmap click does not modify the as-of global state (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data` — heatmap click isolation from as-of state

**Preconditions:**
- Frontend is running at http://localhost:3835
- The as-of switcher shows "Latest" (no historical date selected)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Note the as-of switcher button label in the top bar (e.g., "Latest")
3. Note the browser URL (no `?asof=` parameter)
4. Scroll to the Availability Heatmap card
5. Click any day cell in the heatmap grid
6. Observe the top-bar as-of switcher button label
7. Observe the browser URL

**Expected Result:**
- The as-of switcher button label remains unchanged after the heatmap cell click (still "Latest" or whatever it was before)
- The URL does not gain a `?asof=` parameter
- No historical badge appears in the top bar
- Only the Job form "Start date" and "End date" inputs are affected (as tested in UT-04)

---

### UT-18 — Previously working stocks page still loads with as-of calendar in place (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend has snapshot data

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Wait for the page to fully load
3. Verify the stocks list table is visible
4. Click the as-of switcher button to open the calendar popover
5. Press Escape to close the popover without selecting a date
6. Verify the stocks list is still visible and correct

**Expected Result:**
- Step 2-3: The `/stocks` page loads normally with a visible data table; no error page or blank screen appears
- Step 4: The calendar popover opens correctly (not broken by the page context)
- Step 5: Pressing Escape closes the popover without altering any page data
- Step 6: The stocks data table is still visible and unchanged after the popover interaction

---

### UT-19 — Heatmap card is discoverable by scrolling below Dataset Coverage panel (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Without scrolling, observe whether the Availability Heatmap card is immediately visible or if the user must scroll to find it
3. Scroll down the page
4. Identify where the Availability Heatmap card appears relative to the Dataset Coverage panel

**Expected Result:**
- The Availability Heatmap card appears below the Dataset Coverage panel when the user scrolls down
- The card has a clear title or heading (e.g., "Availability Heatmap" or "Data Coverage Calendar") that identifies its purpose
- The card is visually separate from the Dataset Coverage panel (distinct card border or background)
- No navigation link is required to reach the heatmap — it is on the same `/data` page

---

### UT-20 — As-of calendar popover is discoverable from the top bar (ux)

**Type:** ux
**Priority:** P2
**Surface:** Top bar (all pages) — as-of switcher discoverability

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Without any prior knowledge of the calendar feature, look at the top navigation bar
3. Identify any element in the top bar that appears interactive and relates to a date or time period
4. Click that element

**Expected Result:**
- The as-of switcher button in the top bar is visually distinct from static text — it has a button appearance with a chevron/arrow icon
- Clicking it opens a calendar popover that is immediately recognizable as a date picker (month grid layout)
- The popover shows the current month's days and highlights selectable dates without requiring any additional clicks or instructions

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Data page loads with availability heatmap card visible | smoke | P1 | `/data` |
| UT-02 | Heatmap cells are color-coded by data density | happy-path | P1 | `/data` |
| UT-03 | Hovering a heatmap cell shows exact date, symbol count, and snapshot status | happy-path | P1 | `/data` |
| UT-04 | Clicking a heatmap day prefills the job form Start date and End date | happy-path | P1 | `/data` |
| UT-05 | Shift-clicking a second heatmap cell sets a date range in the job form | happy-path | P1 | `/data` |
| UT-06 | As-of switcher in top bar is now a button with chevron, not a select dropdown | smoke | P1 | Top bar |
| UT-07 | Clicking the as-of button opens a calendar popover with a month grid | happy-path | P1 | Top bar |
| UT-08 | Selecting a date from the as-of calendar popover updates app state | happy-path | P1 | Top bar |
| UT-09 | Disabled (non-snapshot) days in the as-of calendar cannot be selected | validation | P2 | Top bar |
| UT-10 | As-of calendar month navigation back-arrow clamps at the oldest snapshot month | happy-path | P1 | Top bar |
| UT-11 | As-of calendar "Latest" button returns to the live view from a historical month | happy-path | P1 | Top bar |
| UT-12 | As-of calendar popover is keyboard operable | ux | P2 | Top bar |
| UT-13 | Heatmap automatically re-fetches after a job completes | happy-path | P1 | `/data` |
| UT-14 | Heatmap shows a loading state on initial page load | smoke | P2 | `/data` |
| UT-15 | Selecting as-of date via calendar still drives ?asof URL and historical badge | regression | P1 | Top bar |
| UT-16 | Old dropdown-based as-of behavior is gone | regression | P1 | Top bar |
| UT-17 | Heatmap click does not modify the as-of global state | regression | P1 | `/data` |
| UT-18 | Previously working stocks page still loads with as-of calendar in place | regression | P1 | `/stocks` |
| UT-19 | Heatmap card is discoverable by scrolling below Dataset Coverage panel | ux | P2 | `/data` |
| UT-20 | As-of calendar popover is discoverable from the top bar | ux | P2 | Top bar |

**P1 tests must all pass for browser QA verdict to be PASS.**
