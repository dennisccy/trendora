# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-33 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-33
**Date:** 2026-06-18
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Data Manager page loads with new coverage panels (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running and the database contains at least one snapshot

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load (all panels should render within 5 seconds)

**Expected Result:**
- Page renders without a blank screen, spinner stuck indefinitely, or error message
- The heading "Data Manager" or equivalent page title is visible
- The coverage block is visible with at least two labeled metrics
- No red error banner or "failed to fetch" message appears

---

### UT-02 — Universe (as of date) metric shows a date-dependent count (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data` — Coverage block

**Preconditions:**
- Frontend is running at http://localhost:3835
- The global as-of date is at or near the latest available date (default on page load)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Observe the coverage block at the top of the page
3. Locate the metric labeled "Universe (as of date)" or similar

**Expected Result:**
- A metric labeled "Universe (as of date)" or "Universe" with a resolved date annotation is visible
- The count shown is a number between 100 and 130 (at a recent full-universe date)
- A resolved date is shown beside or below the count (e.g., "as of 2022-06-01")
- The metric is NOT labeled with a plain static label like "Universe: 122" with no date context

---

### UT-03 — Candidate universe metric appears alongside the resolved count (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data` — Coverage block

**Preconditions:**
- Frontend is running at http://localhost:3835
- Page is at the default (latest) as-of date

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Observe the coverage block

**Expected Result:**
- A metric labeled "Candidate universe" or "Candidate pool" is visible in the coverage block
- The candidate universe count is a number equal to or greater than the "Universe (as of date)" count
- Both metrics are visible at the same time in the same panel area

---

### UT-04 — Universe Diagnostic Panel renders at a recent date (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data` — Universe Diagnostic panel

**Preconditions:**
- Frontend is running at http://localhost:3835
- The global as-of date is set to a post-warm-up date (use the default latest date)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll down through the page content until a panel titled "Universe Diagnostic" or similar is visible

**Expected Result:**
- A panel named "Universe Diagnostic" (or similar) is present on the page
- The panel contains at least one numeric count labeled "admitted" or similar
- The panel contains at least one row or entry referencing "below history", "below price", or "below liquidity"
- No spinner is stuck; no error message is shown in the panel

---

### UT-05 — Membership Timeline Panel renders with a chart (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data` — Membership Timeline panel

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll down past the Universe Diagnostic panel to find a panel titled "Membership Timeline" or similar

**Expected Result:**
- A panel named "Membership Timeline" (or similar) is visible
- An SVG or canvas chart element is present inside the panel (not a blank white rectangle)
- The chart shows a line that starts near 0 on the left and rises toward a higher value on the right
- A table of per-date rows is visible below or beside the chart
- No error message or empty state banner appears in the panel

---

### UT-06 — Universe count slides when stepping the global as-of to an early date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — Coverage block

**Preconditions:**
- Frontend is running at http://localhost:3835
- The global as-of date switcher (arrow buttons or date picker in the top bar or sidebar) is accessible

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Note the current "Universe (as of date)" count (should be ~120 at the latest date)
3. Use the global as-of date control (click the left arrow "◀" button or navigate to the date picker) to step the date backward to approximately 2021-01-04
4. Wait for the coverage block to refresh

**Expected Result:**
- The "Universe (as of date)" count changes from the previous value to a smaller number (or 0)
- The resolved date annotation beside the count updates to show the new date (2021-01-04 or the nearest available snapshot)
- The "Candidate universe" count remains the same (it is static and should not change with the as-of date)
- No error message appears

---

### UT-07 — Universe Diagnostic Panel shows admitted + excluded-by-reason counts at a recent date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — Universe Diagnostic panel

**Preconditions:**
- Frontend is running at http://localhost:3835
- Global as-of is set to a post-warm-up date (e.g., 2022-06-01 or the latest available date)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Universe Diagnostic" panel
3. Observe the panel contents

**Expected Result:**
- The panel shows a count labeled "Admitted" with a positive integer value (greater than 0)
- The panel shows three exclusion reason rows:
  - A row labeled "Below history" (or "insufficient history") with a non-negative integer count
  - A row labeled "Below price" (or "price too low") with a non-negative integer count
  - A row labeled "Below liquidity" (or "below ADV" or "ADV too low") with a non-negative integer count
- Each exclusion row displays its exact threshold value (e.g., "min price: $5.00" or similar)
- The admitted count plus excluded counts sums to approximately the candidate pool size shown in the coverage block

---

### UT-08 — Universe Diagnostic Panel shows honest empty-universe banner before warm-up (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — Universe Diagnostic panel

**Preconditions:**
- Frontend is running at http://localhost:3835
- Global as-of date can be stepped to a date before approximately 2021-10-01

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Use the global as-of date control to step the date backward to 2021-01-04
3. Scroll to the "Universe Diagnostic" panel

**Expected Result:**
- The panel does NOT show fabricated positive admitted counts
- The panel renders an explicit banner, message, or label stating the universe is empty at this date — text should include "warm-up", "empty", or "no stocks" in plain English
- The page does NOT crash or show a generic JavaScript error
- The page remains responsive (scrollable, navigable)

---

### UT-09 — Membership Timeline chart shows step-function growth from near-zero to full (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — Membership Timeline panel

**Preconditions:**
- Frontend is running at http://localhost:3835
- Database contains multiple snapshots spanning 2021 through 2022

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Membership Timeline" panel
3. Observe the SVG step-function chart

**Expected Result:**
- The chart Y-axis starts at 0 on the left (earliest dates) and shows values near 0 for 2021
- The chart rises in discrete steps (not a smooth curve; flat segments separated by jumps) toward full universe size (~120) by approximately 2022-01 or later
- The chart uses a colored line (not a black default or an invisible line against a dark background)
- The chart is not a blank rectangle — pixel content is present

---

### UT-10 — Membership Timeline per-date table shows entries and exits (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — Membership Timeline panel (per-date table)

**Preconditions:**
- Frontend is running at http://localhost:3835
- The Membership Timeline panel is visible with a populated per-date table

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Membership Timeline" panel
3. Locate the per-date table (rows of dates with size, entries, exits, excluded counts)
4. Find a row where the "Size" column increased from the previous row (entries occurred)
5. Find a row where the "Size" column decreased from the previous row (exits occurred)

**Expected Result:**
- For the row where size increased: the "Entries" column lists at least one ticker symbol (e.g., "AAPL") for that date
- For the row where size decreased: the "Exits" column lists at least one ticker symbol for that date
- Ticker symbols are readable (text, not empty cells or placeholders)

---

### UT-11 — Membership Timeline three honest labels are all visible (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — Membership Timeline panel

**Preconditions:**
- Frontend is running at http://localhost:3835
- The Membership Timeline panel is visible

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Membership Timeline" panel
3. Read the label text visible in or around the panel (may appear as footnotes, callouts, or inline labels)

**Expected Result:**
- At least one label mentioning "survivorship" is present (e.g., "survivorship bias", "current-constituent, not historical")
- At least one label mentioning "warm-up" is present (e.g., referencing the warm-up boundary date)
- At least one label mentioning "universe-relative" or "breadth" is present (e.g., noting breadth relative to the full universe)
- All three labels are readable on the page — not hidden behind a tooltip or collapsed section

---

### UT-12 — Backward History extension button renders with survivorship caveat (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — Backward History panel

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll through the page to locate a section or panel titled "Extend history backward" or containing a button with that label

**Expected Result:**
- A button labeled "Extend history backward" (or similar) is visible and clickable
- Near or inside the same panel, a label or notice mentioning "survivorship" or "current-constituent" is visible before the button is clicked
- The button is not greyed out or disabled in a way that prevents clicking

---

### UT-13 — Backward History confirm gate: modal appears on button click (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — Backward History panel + confirm modal

**Preconditions:**
- Frontend is running at http://localhost:3835
- "Extend history backward" button is visible

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Extend history backward" section
3. Click the "Extend history backward" button
4. Observe what appears on screen

**Expected Result:**
- A confirmation modal (dialog overlay) appears on the screen — the action does NOT execute immediately
- The modal contains a survivorship caveat text mentioning "current-constituent" or "survivorship"
- The modal has at least one button to confirm the action (e.g., labeled "Confirm", "Proceed", or "Yes")
- The modal has a button to cancel (e.g., labeled "Cancel" or "No")
- The main page content behind the modal is still visible but dimmed

---

### UT-14 — Backward History confirms and shows blocked/NA state (error)

**Type:** error
**Priority:** P1
**Surface:** `/data` — Backward History panel + job card

**Preconditions:**
- Frontend is running at http://localhost:3835
- Confirm modal is open (follow steps in UT-13 first)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Click "Extend history backward" to open the confirmation modal
3. Click the "Confirm" button (or equivalent confirm action) inside the modal
4. Wait up to 60 seconds for a result to appear

**Expected Result:**
- The modal closes after confirming
- A job card or progress indicator appears showing the backward history job is running
- The job card eventually (within 60 seconds on this data-walled host) transitions to a state showing "blocked", "limited coverage", or "NA" — not a generic error, crash, or "undefined"
- The page remains responsive throughout — scrollable and navigable
- No JavaScript error banner appears at the top of the page

---

### UT-15 — Stock Leaderboard shows reduced row count at a recent post-warm-up date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Global as-of is at the latest available date

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Count the total number of stock rows visible in the leaderboard (or note the count label if shown)

**Expected Result:**
- The leaderboard shows approximately 120 rows (not 122) at the latest date
- All visible rows contain real ticker symbols (not placeholder or dummy data)

---

### UT-16 — Stock Leaderboard shows honest warm-up message at early as-of date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Global as-of date can be stepped to before 2021-10-01

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Use the global as-of date control to step the date to 2021-01-04
3. Wait for the leaderboard to refresh

**Expected Result:**
- The leaderboard shows zero stock rows OR an explicit empty-state message
- The empty-state message mentions "warm-up" or references the Data Manager diagnostic — NOT a generic "No results" or "No stocks found" message
- The page does NOT show an error page (no 500 banner, no crash overlay)
- The page remains scrollable and navigable

---

### UT-17 — Stock Leaderboard row count grows stepping from early to full-universe date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Use the global as-of date control to step to 2021-01-04
3. Note the number of stock rows (expected: 0 or very small)
4. Use the global as-of date control to step the date forward to 2022-03-01
5. Note the number of stock rows

**Expected Result:**
- At 2021-01-04: row count is 0 or fewer than 10
- At 2022-03-01: row count is greater than 100
- The row count at 2022-03-01 is visibly larger than at 2021-01-04
- No padded, fabricated, or repeated rows appear at the early date

---

### UT-18 — Themes member counts reflect the point-in-time universe at early as-of (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/themes`

**Preconditions:**
- Frontend is running at http://localhost:3835
- At least one theme with members is present in the database

**Steps:**
1. Navigate to `http://localhost:3835/themes`
2. Note the member count shown for any one theme (e.g., "Cloud Computing — 12 stocks")
3. Use the global as-of date control to step the date to 2021-03-01
4. Observe the member counts on the same themes page

**Expected Result:**
- After stepping to 2021-03-01: the member counts for themes are visibly smaller than at the latest date (or 0)
- No theme shows a member count EQUAL to or greater than its latest-date count (the early date universe is smaller)
- The page does not crash or show an error banner

---

### UT-19 — Sectors member counts reflect the point-in-time universe at early as-of (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/sectors`

**Preconditions:**
- Frontend is running at http://localhost:3835
- At least one sector with members is present

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Note the member count for any one sector at the default (latest) date
3. Use the global as-of date control to step the date to 2021-03-01
4. Observe the sector member counts

**Expected Result:**
- After stepping to 2021-03-01: member counts for sectors are visibly smaller than at the latest date (or 0)
- No sector shows more members at the early date than at the latest date
- The page does not crash

---

### UT-20 — Scanner Runs shows lower stock count for a run from before full-universe date (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/scanner-runs`

**Preconditions:**
- Frontend is running at http://localhost:3835
- At least two scanner runs exist in the database — one from before 2022-01-01 and one from after

**Steps:**
1. Navigate to `http://localhost:3835/scanner-runs`
2. Find a run dated before 2022-01-01 and click it to open its detail or expand its row
3. Note the number of stocks listed in that run
4. Find a run dated after 2022-03-01 and open it
5. Note the number of stocks in that run

**Expected Result:**
- The pre-2022 run shows fewer stocks than the post-2022 run
- The pre-2022 run does not show 120 stocks (the old static universe size)
- Neither run shows a crash or error

---

### UT-21 — NVDA scores are identical on the leaderboard and detail page at a full-universe date (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks` and `/stocks/NVDA`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Global as-of is set to a full-universe date (2022-06-01 or later)
- NVDA is present in the leaderboard at that date

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Find the row for NVDA in the leaderboard
3. Note the visible scores for NVDA (Leadership Score, Entry Quality Score, Risk Score) and its bucket label (A–E)
4. Click NVDA's row or name to navigate to its detail page
5. Observe the same scores and bucket on the detail page

**Expected Result:**
- Every score shown on the detail page exactly matches what was shown on the leaderboard for NVDA
- The bucket letter (A–E) matches
- No score field shows a different value between the two views

---

### UT-22 — Risk-Off regime shows zero Actionable stocks (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835
- A Risk-Off regime date is available (check seed data; try 2020-03-16 or a date confirmed to be Risk-Off)

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Use the global as-of date control to step to a known Risk-Off date (e.g., 2020-03-16)
3. Observe the regime indicator and the Actionable column or count

**Expected Result:**
- The regime indicator (label, badge, or header) reads "Risk-Off"
- The Actionable count is 0 — zero stocks are marked as Actionable
- Stocks may still show "Watchlist" status (that is allowed in Risk-Off)
- The page does not crash

---

### UT-23 — Dashboard panels are unchanged at a full-universe as-of date (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Dashboard)

**Preconditions:**
- Frontend is running at http://localhost:3835
- Global as-of is set to a full-universe date (2022-06-01 or the latest date)

**Steps:**
1. Navigate to `http://localhost:3835/` (the Dashboard)
2. Observe all visible panels

**Expected Result:**
- The market regime chart or panel is visible and populated
- The sector leaders panel is visible with at least one sector listed
- The theme leaders panel is visible with at least one theme listed
- The stock leadership panel is visible with at least one stock row
- No blank panels, no error banners, and no layout breakage

---

### UT-24 — No second date input element exists on /data (regression — J-18 invariant)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Open the browser developer tools (press F12)
3. In the Elements/Inspector panel, search for the string `type="date"` or `<input type="date"`
4. Close developer tools and repeat the search on `http://localhost:3835/stocks`

**Expected Result:**
- Zero `<input type="date">` elements are found on the `/data` page
- Zero `<input type="date">` elements are found on the `/stocks` page
- The only date control on any page is the single global as-of switcher in the shared top bar or sidebar (which is NOT an `<input type="date">`)

---

### UT-25 — Universe Diagnostic Panel updates when as-of date changes (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data` — Universe Diagnostic panel

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Universe Diagnostic" panel and note the "Admitted" count
3. Use the global as-of date control to step the date backward by approximately 6 months
4. Observe the "Universe Diagnostic" panel again

**Expected Result:**
- The "Admitted" count in the diagnostic panel changes to a smaller value after stepping the date backward
- The threshold values displayed (price cutoff, ADV cutoff) remain the same (they are config-sourced, not date-dependent)
- The panel refreshes within 3 seconds — it does not show a stale value indefinitely

---

### UT-26 — Membership Timeline three honest labels are discoverable without scrolling far (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data` — Membership Timeline panel

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll down the page until the "Membership Timeline" panel is visible
3. Without opening any modal or expanding any collapsed section, read the label text in the panel

**Expected Result:**
- The survivorship-bias label is readable directly in the panel without requiring any click or expand action
- The warm-up boundary label is readable directly in the panel
- The universe-relative breadth label is readable directly in the panel
- A first-time user (non-developer) can understand that "these stocks may not be historically accurate" from the panel labels alone

---

### UT-27 — Data Manager Candidate universe count is discoverable in the coverage block (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data` — Coverage block

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Without scrolling or clicking, look at the coverage block at the top of the page

**Expected Result:**
- Both "Universe (as of date)" and "Candidate universe" metrics are visible without scrolling
- The labels are self-explanatory (not cryptic abbreviations)
- The relationship between the two values (candidate pool is larger than or equal to the resolved universe) is immediately apparent

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Data Manager page loads without errors | smoke | P1 | `/data` |
| UT-02 | Universe (as of date) metric shows date-dependent count | smoke | P1 | `/data` |
| UT-03 | Candidate universe metric appears in coverage block | smoke | P1 | `/data` |
| UT-04 | Universe Diagnostic Panel renders at recent date | smoke | P1 | `/data` |
| UT-05 | Membership Timeline Panel renders with a chart | smoke | P1 | `/data` |
| UT-06 | Universe count slides when stepping as-of to early date | happy-path | P1 | `/data` |
| UT-07 | Diagnostic panel shows admitted + excluded-by-reason counts | happy-path | P1 | `/data` |
| UT-08 | Diagnostic panel shows honest empty-universe banner before warm-up | happy-path | P1 | `/data` |
| UT-09 | Timeline chart shows step-function growth from near-zero to full | happy-path | P1 | `/data` |
| UT-10 | Timeline per-date table shows entries and exits | happy-path | P1 | `/data` |
| UT-11 | Membership Timeline three honest labels are all visible | happy-path | P1 | `/data` |
| UT-12 | Backward History button renders with survivorship caveat | happy-path | P1 | `/data` |
| UT-13 | Backward History confirm gate: modal appears on button click | happy-path | P1 | `/data` |
| UT-14 | Backward History confirms and shows blocked/NA state | error | P1 | `/data` |
| UT-15 | Stock Leaderboard shows ~120 rows at latest date | happy-path | P1 | `/stocks` |
| UT-16 | Stock Leaderboard shows honest warm-up message at early as-of | happy-path | P1 | `/stocks` |
| UT-17 | Stock Leaderboard row count grows from early to full-universe date | happy-path | P1 | `/stocks` |
| UT-18 | Themes member counts reflect point-in-time universe at early as-of | regression | P1 | `/themes` |
| UT-19 | Sectors member counts reflect point-in-time universe at early as-of | regression | P1 | `/sectors` |
| UT-20 | Scanner Runs shows lower stock count for pre-2022 run | regression | P1 | `/scanner-runs` |
| UT-21 | NVDA scores identical on leaderboard and detail page | regression | P1 | `/stocks`, `/stocks/NVDA` |
| UT-22 | Risk-Off regime shows zero Actionable stocks | regression | P1 | `/stocks` |
| UT-23 | Dashboard panels unchanged at full-universe as-of date | regression | P1 | `/` |
| UT-24 | No second date input element exists on /data (J-18 invariant) | regression | P1 | `/data`, `/stocks` |
| UT-25 | Universe Diagnostic Panel updates when as-of date changes | ux | P2 | `/data` |
| UT-26 | Membership Timeline honest labels are discoverable without deep scrolling | ux | P2 | `/data` |
| UT-27 | Candidate universe count is discoverable in coverage block | ux | P2 | `/data` |

**P1 tests must all pass for browser QA verdict to be PASS.**
