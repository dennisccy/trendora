# Phase goal-i_can_see_the_wealthy_future_forever-iter-3 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-3 (J-17 — Data Manager: grow the dataset by date / date range)
**Date:** 2026-06-01
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- UT-XX = UI/browser tests. These complement (do not duplicate) the functional API/artifact TC-XX cases. -->
<!-- Backend assumed running at http://localhost:8000 with the committed seed (158 symbols, quarterly bootstrap snapshots). -->

---

### UT-01 — Data Manager page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend running at http://localhost:8000

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load (coverage skeleton resolves to numbers)

**Expected Result:**
- Page renders without a blank screen, 404, or error overlay
- The page heading text "Data Manager" is visible
- Four panels are present: "Dataset coverage", "Start a fetch / backfill job", "Job progress", and "Run history"
- No red "Backend unavailable" card appears
- No console errors

---

### UT-02 — Coverage panel shows real dataset metrics (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data` → `CoveragePanel`

**Preconditions:**
- Frontend + backend running, committed seed loaded

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the "Dataset coverage" panel
3. Read each of the five metrics

**Expected Result:**
- "Price history" shows a range in `YYYY-MM-DD → YYYY-MM-DD` form (e.g. `2021-01-04 → 2026-05-28`), not blank or `null`
- "Symbols" shows a non-zero count of approximately 158
- "Trading days" shows a non-zero integer
- "Snapshot dates" shows a non-zero integer
- "Backfill gaps" shows an integer count; if greater than 0 the number is rendered amber and a "Gap range" line shows a `first → last` gap date pair; if 0, it reads "no backfill gaps" in green
- No value displays as `NaN`, `undefined`, or `0` for symbols/trading days

---

### UT-03 — Job form pre-fills date range from gap dates (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data` → `JobForm`

**Preconditions:**
- Frontend + backend running; coverage reports at least one backfill gap

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for coverage to load
3. Inspect the "Start date" and "End date" inputs in the "Start a fetch / backfill job" panel

**Expected Result:**
- Both the "Start date" and "End date" `<input type="date">` fields are pre-populated with real dates (not empty)
- The pre-filled dates fall within the gap range shown in the coverage panel
- The "Job kind" dropdown defaults to a visible option (e.g. "Backfill snapshots")
- The "Start" button is visible and enabled

---

### UT-04 — Job kind dropdown exposes all three kinds (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/data` → `JobForm` → Job kind `Select`

**Preconditions:**
- Frontend + backend running

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Click the "Job kind" dropdown in the job form
3. Read the list of options

**Expected Result:**
- Exactly three options are present and selectable: "Backfill snapshots", "Fetch EOD prices", and "Fetch + backfill"
- Selecting "Fetch EOD prices" and re-opening the dropdown shows it as the chosen value
- No empty or duplicate options appear

---

### UT-05 — Start a backfill job and watch live progress to completion (happy path, PRIMARY)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` → `JobForm` + `JobProgressPanel`

**Preconditions:**
- Frontend + backend running
- Coverage shows at least one backfill gap (date with bars but no snapshot)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for coverage and the pre-filled date range to load
3. In the "Job kind" dropdown select "Backfill snapshots"
4. Leave the pre-filled "Start date" and "End date" (a valid gap range), or set them to a known gap range from the coverage "Gap range" line
5. Click the "Start" button
6. Immediately observe the "Start" button and the "Job progress" panel
7. Wait for the job to reach a terminal state

**Expected Result:**
- On click, the "Start" button shows a spinner and the text "Job running…" (button becomes busy/disabled)
- The "Job progress" panel replaces its idle placeholder with a live status badge
- The "Snapshots backfilled" progress bar advances (the `A/B` dates counter rises over time, roughly each second)
- Snapshot count and forward-return counts increase as the job runs
- The job ends with a status badge of "ok" (or "partial" / "failed") and a final summary message
- After completion the "Start" button returns to its normal enabled label (no longer "Job running…")

---

### UT-06 — Run history records the completed job (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` → `RunHistoryPanel`

**Preconditions:**
- UT-05 has just completed at least one backfill job

**Steps:**
1. Remain on `http://localhost:3835/data` after the job in UT-05 completes
2. Locate the "Run history" table
3. Read the top (most recent) row

**Expected Result:**
- A new row appears at the top of the "Run history" table
- The row shows: a "Started" timestamp, a Kind badge ("Backfill snapshots"), the date Range that was submitted, a Status badge ("ok"/"partial"/"failed"), Symbols ok/failed counts, a Snapshots-created count, and a Summary message
- The values match what was observed in the Job progress panel for that run
- No "No fetch / backfill runs yet" empty-state card is shown (history is non-empty)

---

### UT-07 — Backfilled date becomes selectable in global as-of switcher without reload (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` → global as-of switcher (`asof-provider.tsx`)

**Preconditions:**
- UT-05 completed a backfill that created at least one new snapshot date
- The page has NOT been hard-reloaded since the job finished

**Steps:**
1. After the backfill job in UT-05 completes, do NOT refresh the browser
2. Open the global as-of date switcher in the page header / top bar
3. Look for the date(s) just backfilled (from the job's date range)
4. Note the currently selected as-of date before and after opening

**Expected Result:**
- The newly backfilled date(s) now appear as selectable options in the as-of switcher
- They appeared WITHOUT a hard page reload (refresh() additive behavior)
- The currently selected as-of date is unchanged — backfilling older dates did NOT switch the user's current selection
- The "latest" date shown is unchanged when only older dates were backfilled

---

### UT-08 — Newly backfilled date resolves across the dashboard (regression / downstream)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`, `/` (driven by global as-of)

**Preconditions:**
- A newly backfilled date is selectable per UT-07

**Steps:**
1. From the global as-of switcher, select the newly backfilled date
2. Navigate to `http://localhost:3835/stocks` via in-app navigation (not a reload)
3. Observe the per-date content
4. Navigate to `http://localhost:3835/` (home/dashboard)
5. Observe the per-date content

**Expected Result:**
- `/stocks` renders a valid per-date scorecard/leaderboard for the selected backfilled date — no error message, no empty state, no blank table
- `/` renders valid as-of-driven content for the same date — no error, no empty state
- The selected date is reflected consistently in the switcher across both pages

---

### UT-09 — System Health sample size (n) grows after backfill (regression / downstream)

**Type:** regression
**Priority:** P2
**Surface:** `/system-health`

**Preconditions:**
- Able to record `n` before running a backfill (do this step first)

**Steps:**
1. BEFORE starting any backfill, navigate to `http://localhost:3835/system-health` and record the sample size value labelled `n`
2. Navigate to `http://localhost:3835/data` and run a backfill over new seed-bar gap dates (per UT-05) so new snapshots are created
3. After the job completes, navigate back to `http://localhost:3835/system-health`
4. Read the sample size `n` again

**Expected Result:**
- The sample size `n` after the backfill is strictly greater than the `n` recorded before
- No error appears on `/system-health`

---

### UT-10 — Fetch EOD prices job surfaces an honest provider failure (error)

**Type:** error
**Priority:** P2
**Surface:** `/data` → `JobProgressPanel` error list

**Preconditions:**
- Frontend + backend running
- Live Stooq provider is unavailable in this environment (expected: free CSV endpoint requires an API key)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. In the "Job kind" dropdown select "Fetch EOD prices"
3. Keep a valid date range and click the "Start" button
4. Wait for the job to reach a terminal state
5. Read the "Job progress" panel error block

**Expected Result:**
- The job ends with a "failed" or "partial" status badge — NOT a fake "ok"
- An error block lists per-symbol failures
- The panel states plainly that no data was fabricated (text such as "(no data fabricated)")
- No new price bars or snapshots are claimed for the failed symbols
- A corresponding "failed"/"partial" row is appended to the "Run history" table

---

### UT-11 — /data date inputs do not change the global as-of date (validation / J-18 guard)

**Type:** validation
**Priority:** P1
**Surface:** `/data` → `JobForm` date inputs vs global as-of switcher

**Preconditions:**
- Frontend + backend running

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Note the date currently shown in the global as-of switcher in the header
3. In the job form, change the "End date" input to a different date
4. Re-check the global as-of switcher value in the header

**Expected Result:**
- Changing the "Start date" or "End date" in the job form changes ONLY the form's local value
- The global as-of switcher value in the header is unchanged (exactly-one-date-selector / J-18 preserved)
- No other page reacts to the form date change until a job is actually run

---

### UT-12 — Invalid date range is rejected without a fake job (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data` → `JobForm`

**Preconditions:**
- Frontend + backend running

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Set "Start date" to a date AFTER the "End date" (start > end)
3. Click the "Start" button

**Expected Result:**
- The job is not silently accepted as a successful run
- An explicit, visible error/validation message is shown to the user (or the request is rejected and surfaced as a failed state), not a fabricated "ok" progress run
- No bogus "ok" row with reversed dates appears in the Run history

---

### UT-13 — Run history empty state on a fresh DB (smoke / empty state)

**Type:** smoke
**Priority:** P3
**Surface:** `/data` → `RunHistoryPanel` empty state

**Preconditions:**
- A fresh DB with NO fetch/backfill runs recorded (note: the committed seed may already record an initial seed-load run — if so this case is informational/N/A)

**Steps:**
1. With no prior runs, navigate to `http://localhost:3835/data`
2. Locate the "Run history" panel

**Expected Result:**
- The "No fetch / backfill runs yet" empty-state card is shown
- No empty table headers with zero rows are shown instead of the empty state
- (If the seed already logs a run, document that history is non-empty by design and mark this case N/A)

---

### UT-14 — Backend-unavailable error card on /data (error)

**Type:** error
**Priority:** P2
**Surface:** `/data` → loading skeleton / "Backend unavailable" card

**Preconditions:**
- Backend at http://localhost:8000 is STOPPED; frontend still running

**Steps:**
1. Stop the backend service
2. Navigate to `http://localhost:3835/data`
3. Wait for the coverage fetch to fail

**Expected Result:**
- A styled red "Backend unavailable" error card appears
- The card explicitly states no figures are fabricated (no zeros, no placeholder numbers shown as if real)
- The page does not crash to a blank screen or unhandled error overlay

---

### UT-15 — Data Manager is discoverable from the sidebar (ux)

**Type:** ux
**Priority:** P1
**Surface:** (global) `Sidebar` `NAV` → "Data Manager" link

**Preconditions:**
- Frontend running

**Steps:**
1. Navigate to `http://localhost:3835/` (home)
2. Look at the bottom of the left sidebar
3. Click the "Data Manager" entry (database icon, last item in the sidebar)

**Expected Result:**
- A "Data Manager" navigation item with a database icon is the last entry in the left sidebar
- The item is present on every page (visible from `/`, `/stocks`, etc.)
- Clicking it routes to `http://localhost:3835/data`
- The "Data Manager" item is marked active/highlighted while on `/data`

---

### UT-16 — Loading skeleton appears while coverage loads (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/data` → loading skeleton

**Preconditions:**
- Frontend + backend running (a slightly slow first request makes this easier to observe)

**Steps:**
1. Navigate to `http://localhost:3835/data` with a fresh (uncached) load
2. Observe the coverage panel during the first moment of load

**Expected Result:**
- A loading skeleton is shown in place of the coverage metrics while data is fetching
- The skeleton is replaced by real numbers once coverage resolves (no permanent skeleton, no flash of `0`/`undefined`)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Data Manager page loads | smoke | P1 | `/data` |
| UT-02 | Coverage shows real metrics | smoke | P1 | `/data` CoveragePanel |
| UT-03 | Job form pre-fills gap range | smoke | P1 | `/data` JobForm |
| UT-04 | Job kind dropdown options | happy-path | P2 | `/data` JobForm |
| UT-05 | Backfill job live progress (PRIMARY) | happy-path | P1 | `/data` JobForm + Progress |
| UT-06 | Run history records job | happy-path | P1 | `/data` RunHistoryPanel |
| UT-07 | Backfilled date selectable w/o reload | happy-path | P1 | as-of switcher |
| UT-08 | Backfilled date resolves on dashboard | regression | P1 | `/stocks`, `/` |
| UT-09 | System Health n grows | regression | P2 | `/system-health` |
| UT-10 | Fetch job honest provider failure | error | P2 | `/data` Progress error list |
| UT-11 | Form dates don't move global as-of (J-18) | validation | P1 | `/data` JobForm vs switcher |
| UT-12 | Invalid range rejected, no fake job | validation | P2 | `/data` JobForm |
| UT-13 | Run history empty state | smoke | P3 | `/data` RunHistoryPanel |
| UT-14 | Backend-unavailable error card | error | P2 | `/data` |
| UT-15 | Data Manager discoverable in sidebar | ux | P1 | Sidebar nav |
| UT-16 | Loading skeleton on coverage load | ux | P3 | `/data` |

**P1 tests must all pass for browser QA verdict to be PASS:** UT-01, UT-02, UT-03, UT-05, UT-06, UT-07, UT-08, UT-11, UT-15.

> Note: UT-05 is the primary J-17 multi-step flow (coverage → start → live progress → summary). UT-07 + UT-08 verify the no-reload `refresh()` + downstream resolution. UT-10/UT-12/UT-14 enforce the real-data-only / no-fabrication anti-goals at the UI layer. UT-11 enforces the "exactly one date selector" (J-18) guard. API/artifact coverage (coverage correctness, immutability, lookahead-free, no second computation path) is owned by the functional test plan (TC-01..TC-19) — not duplicated here.
