# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35
**Date:** 2026-06-19
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Overview

This iteration has zero frontend source-code changes. All nine affected UI surfaces changed because the J-85 rebuild repopulated the stored snapshot data they read. The test plan therefore focuses on verifying that the DATA shown in the existing UI is now correct:

- `/stocks` row count slides by as-of date (0 before warm-up, ~495–544 at full universe)
- `/data` membership timeline shows a rising step function with populated Entries/Exits columns and intact honesty labels
- `/data` J-94 diagnostic count agrees with the `/stocks` served count at the same date
- `/stocks/NVDA` detail scores match the NVDA row on the leaderboard list
- Existing regression guards (single global as-of, Risk-Off → 0 Actionable, regime panel, immutability) remain green

No validation or error test cases are written for this iteration because no new forms, inputs, or interactive controls were added. The only structural control change (the J-85 rebuild panel) already existed and was used; testing that it still renders safely is covered under regression.

---

## Test Cases

---

### UT-01 — /stocks page loads at latest date without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Wait for the page to fully load (leaderboard table appears)
3. Observe the page heading and table

**Expected Result:**
- Page renders without a blank screen or "Checking backend…" placeholder
- The stocks leaderboard table is visible with column headers (e.g., "Symbol", "Leadership", "Entry", "Risk" or equivalent)
- The row count shown is approximately 544 (not 122)
- No full-page error overlay or "Something went wrong" message is displayed

---

### UT-02 — /data page loads and membership timeline panel is visible (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Scroll down until the membership timeline panel comes into the viewport

**Expected Result:**
- Page renders without a blank screen or error message
- The membership timeline panel is visible (contains a table or chart with date rows)
- The panel has columns for SIZE (or equivalent count label), Entries, and Exits
- No "Checking backend…" spinner remains after load

---

### UT-03 — /stocks row count is 0 at a pre-warm-up date (J-93 early/empty state — happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- The J-85 rebuild has completed (job eb48cbf1, 1369/1369 dates)

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Locate the global as-of date control at the top of the page (the single date switcher — NOT a local date input)
3. Set the as-of date to `2021-01-04` using the global switcher (click the control and type or select `2021-01-04`)
4. Wait for the page to reload or the leaderboard to refresh
5. Count the number of rows in the stocks leaderboard table

**Expected Result:**
- The stocks leaderboard table shows 0 rows (completely empty) — the honest pre-warm-up state
- An empty-state message or "No results" indicator is visible (exact wording may vary, but the table is not populated with stock rows)
- The table does NOT show any stock symbols — specifically, there should be no rows at all, not even a partial list of 122
- The as-of date control shows `2021-01-04`

---

### UT-04 — /stocks row count is approximately 495–544 at a full-universe date (J-93 full state — happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- The J-85 rebuild has completed

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Locate the global as-of date control at the top of the page
3. Set the as-of date to `2022-02-01` using the global switcher
4. Wait for the leaderboard table to refresh
5. Count the number of rows in the stocks leaderboard table (or read the displayed count if one is shown)

**Expected Result:**
- The stocks leaderboard table shows approximately 495–504 rows — the full dynamic universe for that date
- The row count is clearly NOT 122 (the stale pre-rebuild value)
- The first several rows show stock symbols with Leadership, Entry, and Risk scores populated
- The as-of date control shows `2022-02-01`

---

### UT-05 — /stocks row count at 2021-01-04 is byte-distinct from row count at 2022-02-01 (J-93 differential — happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- UT-03 and UT-04 have been completed
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/stocks` and set the as-of date to `2021-01-04` (following UT-03 steps)
2. Note the total number of visible table rows (should be 0)
3. Without refreshing the browser, set the as-of date to `2022-02-01` using the global switcher
4. Wait for the leaderboard to update
5. Note the new total number of visible table rows (should be approximately 495–504)
6. Compare the two row counts

**Expected Result:**
- The row count at `2021-01-04` is 0 (empty)
- The row count at `2022-02-01` is approximately 495–504
- The difference between the two counts is at least 400 rows — confirming the universe is NOT flat at every date
- The table contents are visibly different between the two dates (different symbols, different scores)

---

### UT-06 — /stocks row count at latest date is approximately 544 (J-93 latest state — happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Set the as-of date to `2026-06-16` using the global date switcher (or leave it at the default latest date)
3. Wait for the leaderboard table to load
4. Count the total number of rows (or read the displayed count)

**Expected Result:**
- The stocks leaderboard table shows approximately 544 rows
- The count is NOT 122
- Stock symbols with scores are visible in the rows
- The as-of date control shows `2026-06-16` (or the latest available date)

---

### UT-07 — /data membership timeline SIZE column varies across date rows (J-96 step function — happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll down until the membership timeline panel is fully visible in the viewport
3. Locate the SIZE column (or equivalent column that shows the number of universe members at each date row)
4. Compare the SIZE values across the first several date rows (early dates) and the last several date rows (latest dates)

**Expected Result:**
- Early date rows (around October 2021) show a SIZE value near 0 or a small number (less than 50)
- Later date rows (around 2022-02 and beyond) show SIZE values of approximately 495–544
- The SIZE values are NOT a uniform 122 on every row
- The progression of SIZE values forms a visible upward step pattern — small numbers at the top (earliest dates) rising to large numbers further down (later dates)

---

### UT-08 — /data membership timeline Entries and Exits columns are populated (J-96 entries/exits — happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- Membership timeline panel is visible (UT-07 preconditions met)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll down until the membership timeline table is visible
3. Locate the Entries column and Exits column
4. Scan at least 10 visible date rows in the table

**Expected Result:**
- At least 5 of the 10 visible rows show a non-dash, non-blank value in the Entries column (e.g., a number such as "42" or a comma-separated list of symbols)
- At least 5 of the 10 visible rows show a non-dash, non-blank value in the Exits column
- The columns are NOT entirely filled with "—" placeholders
- Values in the Entries and Exits columns are consistent with the corresponding SIZE changes between adjacent rows

---

### UT-09 — /data membership timeline honesty labels are present verbatim (J-96 labels — regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Membership timeline panel is visible

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll down until the membership timeline panel header, legend, or inline annotation area is visible
3. Search the visible text for the following three phrases (read the panel text carefully):
   - Any text containing "survivorship" (as in survivorship bias warning)
   - Any text containing "warm-up" (as in warm-up period or minimum history boundary)
   - Any text containing "universe-relative" (as in universe-relative coverage or membership)
4. Verify all three phrases are visible somewhere in the panel

**Expected Result:**
- The word "survivorship" (or phrase "survivorship bias") is present in the panel text
- The phrase "warm-up" (or "warm-up boundary" or "minimum history") is present
- The phrase "universe-relative" is present
- All three labels appear exactly as they did before the J-85 rebuild — none have been removed or replaced
- No label is replaced with an error message or blank

---

### UT-10 — /data J-94 diagnostic admitted count agrees with /stocks row count at same date (J-06 reconciliation — happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the per-date coverage diagnostic section (J-94) — this may be labelled "Universe Coverage", "Admitted Members", or similar; it shows a count of members admitted by the live resolver for a given date
3. Find or set the diagnostic to the date `2026-06-16` (or the latest available date)
4. Record the admitted-member count shown in the diagnostic (expected: approximately 544)
5. Navigate to `http://localhost:3835/stocks` and set the global as-of date to `2026-06-16`
6. Count or read the total row count in the leaderboard table (expected: approximately 544)
7. Compare the two counts

**Expected Result:**
- The J-94 diagnostic count and the `/stocks` leaderboard row count at the same date (`2026-06-16`) agree within a small margin (at most 5 rows difference, per the documented benchmark-vs-stocks-only distinction)
- Both counts are approximately 544
- The counts are NOT inconsistent (e.g., diagnostic 544 vs leaderboard 122, which was the iter-34 discrepancy)

---

### UT-11 — NVDA scores on /stocks list match NVDA scores on /stocks/NVDA detail (J-06 single-source — happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`, `/stocks/NVDA`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- The global as-of date is set to `2026-06-16`

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Set the global as-of date to `2026-06-16` if not already set
3. Locate the row for NVDA in the leaderboard table (use the search or scroll to find it)
4. Record the three score values for NVDA: Leadership score, Entry score, Risk score (note the exact numbers shown)
5. Click on the NVDA row or the NVDA symbol link to navigate to the detail page
6. Verify the URL is now `http://localhost:3835/stocks/NVDA` (with `as_of=2026-06-16` in the URL or query string)
7. On the NVDA detail page, locate the Leadership, Entry, and Risk score values
8. Compare each of the three scores to the values recorded in step 4

**Expected Result:**
- The Leadership score on the NVDA detail page exactly matches the Leadership score shown in the NVDA row on the leaderboard list
- The Entry score on the detail page exactly matches the Entry score on the leaderboard list
- The Risk score on the detail page exactly matches the Risk score on the leaderboard list
- No score discrepancy exists between the list view and the detail view — both read from the same rebuilt snapshot

---

### UT-12 — Single global as-of control: no local date inputs on /stocks (J-18 regression — regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Wait for the page to fully load
3. Visually scan the entire page for any date picker or calendar widget beyond the single global as-of switcher at the top
4. Look in the header, sidebar, table filters, and any visible panel for additional date inputs

**Expected Result:**
- There is exactly ONE as-of date control on the page — the single global switcher in the top bar or header
- No secondary or local `<input type="date">` field exists anywhere on the page
- The single global switcher is present and functional
- Changing the global switcher date updates the leaderboard table (no separate "apply" button needed for the core flow)

---

### UT-13 — Risk-Off regime date shows 0 Actionable stocks on /stocks (J-07 regression — regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- A Risk-Off date is available in the historical data (a bear-market date such as 2022-06-13 or similar)

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Set the global as-of date to `2022-06-13` (a known Risk-Off date from the 2022 bear market period)
3. Wait for the leaderboard table to load
4. Look at the Status column (or filter the table by status "Actionable")
5. Count how many rows show a status of "Actionable"

**Expected Result:**
- Zero rows with "Actionable" status appear in the leaderboard for the Risk-Off date
- The table may still show stock rows (non-Actionable statuses like "Watch" or "Avoid" may appear), but none are marked Actionable
- No change in this behavior from before the rebuild — the risk-gating logic is unaffected

---

### UT-14 — Regime / market phase panel renders correctly at a full-universe date (J-87 regression — regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Dashboard)

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/` (the Dashboard)
2. Set the global as-of date to `2022-02-01` (a full-universe date)
3. Wait for the page to load
4. Locate the Market Phase or Regime panel on the Dashboard
5. Read the regime label shown (e.g., "Risk-On", "Risk-Off", "Normal")

**Expected Result:**
- The regime/market-phase panel renders a label without a loading spinner or error
- The label is a valid regime value (e.g., "Risk-On" or "Risk-Off") — not blank, not "undefined", not "Error"
- The J-85 rebuild has not altered the regime state for this date (regime is independent of the stock universe snapshot data)

---

### UT-15 — /data Rebuild panel renders as confirm-gated control (J-08/J-15 immutability regression — regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the "Rebuild snapshots" or "Regenerate" panel — this is the J-85 confirm-gated control used to trigger a full rebuild
3. Observe the state of the control

**Expected Result:**
- The rebuild panel is present and visible on the page
- The rebuild control requires a confirmation step before any destructive action can proceed (it is confirm-gated, not a single-click destructive button)
- The panel does NOT show a spinner or in-progress state (the previous rebuild is complete)
- The panel does NOT allow triggering a new rebuild with a single click (it must require an explicit confirmation — e.g., a checkbox, typed confirmation text, or a two-step confirm dialog)

---

### UT-16 — /stocks table shows honest empty state (not padded or fabricated) at 2021-01-04 (UX — ux)

**Type:** ux
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Set the global as-of date to `2021-01-04`
3. Wait for the leaderboard table to update

**Expected Result:**
- The table shows an explicit empty state — either the message "No stocks found", "No data for this date", or a similar human-readable message
- The empty state is NOT a blank white rectangle with no explanation
- The page does NOT show fabricated rows (e.g., 122 stale placeholder stocks from the old rebuild)
- An operator reading this page for the first time would understand they are looking at a period before any stocks qualified for the universe — the empty state communicates the honest pre-warm-up situation

---

### UT-17 — /stocks as-of date is reflected in the page URL (UX serialization — ux)

**Type:** ux
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Set the global as-of date to `2021-10-25` using the global switcher
3. Wait for the page to update
4. Look at the browser address bar

**Expected Result:**
- The URL in the browser address bar contains `asof=2021-10-25` (or equivalent query parameter) after the date is changed
- An operator can copy the URL and share it, and the recipient will see the same date-filtered view
- The page does NOT revert to the latest date on refresh when the `asof` parameter is in the URL

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | /stocks page loads at latest date without errors | smoke | P1 | `/stocks` |
| UT-02 | /data page loads and membership timeline panel is visible | smoke | P1 | `/data` |
| UT-03 | /stocks row count is 0 at a pre-warm-up date | happy-path | P1 | `/stocks` |
| UT-04 | /stocks row count is ~495–504 at 2022-02-01 | happy-path | P1 | `/stocks` |
| UT-05 | /stocks row counts at 2021-01-04 vs 2022-02-01 are byte-distinct | happy-path | P1 | `/stocks` |
| UT-06 | /stocks row count is ~544 at latest date | happy-path | P1 | `/stocks` |
| UT-07 | /data timeline SIZE column varies — rising step function | happy-path | P1 | `/data` |
| UT-08 | /data timeline Entries and Exits columns are populated | happy-path | P1 | `/data` |
| UT-09 | /data timeline honesty labels present verbatim | regression | P1 | `/data` |
| UT-10 | J-94 diagnostic count agrees with /stocks row count at 2026-06-16 | happy-path | P1 | `/data` |
| UT-11 | NVDA scores on list match NVDA scores on detail | happy-path | P1 | `/stocks`, `/stocks/NVDA` |
| UT-12 | Single global as-of — zero local date inputs on /stocks | regression | P1 | `/stocks` |
| UT-13 | Risk-Off date shows 0 Actionable stocks | regression | P1 | `/stocks` |
| UT-14 | Regime/market phase panel renders at full-universe date | regression | P1 | `/` |
| UT-15 | /data Rebuild panel renders as confirm-gated control | regression | P1 | `/data` |
| UT-16 | /stocks shows honest empty state at 2021-01-04 | ux | P2 | `/stocks` |
| UT-17 | as-of date reflected in page URL after selection | ux | P2 | `/stocks` |

**P1 tests must all pass for browser QA verdict to be PASS.**
