# Phase goal-ops-hardening-iter-1 — UI Test Plan

**Phase:** goal-ops-hardening-iter-1
**Date:** 2026-07-19
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Scope note

This plan verifies what an operator SEES and CLICKS on `/data` (and the consequential effect on
`/scanner-runs`). It intentionally does NOT re-verify the exact breakdown-arithmetic invariants
(`non_trading_days + dates_total == calendar_days`, etc.), the `rebuild`-kind cadence math, or raw
API status codes — those are already covered by `reports/qa/goal-ops-hardening-iter-1-test-plan.md`
(TC-09, TC-10, TC-12). Where this plan states an exact number (e.g. "28 calendar days"), it is
checking that the already-computed number **renders correctly in the right UI element with the
right copy** — a rendering check, not a recomputation of the arithmetic.

**Priority note:** several regression checks below are marked P1 (not the skill-default P2/P3)
because they map directly to this phase's own Definition-of-Done "must not regress" items (J-04's
four sub-behaviors; the inverted-range rejection). A P1 failure here means this iteration broke
something it explicitly promised not to.

**Sequencing note:** UT-12/UT-13 (the >370-day backfill) start a job that keeps the Start button
disabled on that browser tab until it finishes or the page reloads — do them LAST. UT-14/UT-15
both involve restarting the backend — do them together at the end (UT-14 can reuse the still-running
UT-12 job as the one that gets interrupted, if it hasn't finished yet). Every other test below is
independently runnable in any order.

---

## Test Cases

---

### UT-01 — `/data` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and reachable
- No login is required (this app has no auth gate)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the page to fully load (the loading skeleton disappears)

**Expected Result:**
- The heading "Data Manager" is visible, with the subtitle beginning "Grow the dataset on demand…"
- The "Dataset coverage" panel, the "Start a fetch / backfill job" panel, the "Job progress" panel,
  and the "Run history" section are all visible
- No red "Backend unavailable" error card appears
- No blank white screen or unhandled crash

---

### UT-02 — Explicit May-2026 backfill actually creates snapshots (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Backend running with the committed seed (`snapshot_cadence.daily_start=2026-06-01`)
- No prior job has been started in this browser tab's session
- The May 2026 range below has not already been backfilled in this database (if it has — e.g. a
  prior automated run already executed this exact range — you will instead see the zero-work
  outcome described in UT-04; that is not a failure of THIS test, skip to UT-04's expected result)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the "Start a fetch / backfill job" panel, confirm the "Job kind" dropdown reads "Backfill snapshots" (leave it as-is; this is the default)
3. Click into the "Start date" field, select all existing text (Ctrl+A) and type `2026-05-02`
4. Click into the "End date" field, select all existing text (Ctrl+A) and type `2026-05-29`
5. Click the "Start" button
6. Watch the "Job progress" panel: the status badge first reads "running" (blue/accent, with a spinning icon), then settles to a final state within a few seconds
7. Read the final badge text, the "chunk" badge, the "Snapshots backfilled" line, and the breakdown line

**Expected Result:**
- The status badge (top of "Job progress" panel) settles to plain green text reading exactly "ok" — NOT the grey "no new snapshots" badge
- A grey "chunk 1/1" badge appears next to the status badge (the whole 28-day range fits in one date-window chunk)
- The line "Snapshots backfilled" shows "19/19 dates" with a fully-filled progress bar
- Below that, a line reads "19 snapshots · N forward returns inserted" (N is any non-negative number — the exact forward-returns count is not pinned by this test)
- Below that, the breakdown line (small grey text) reads exactly: "28 calendar days · 0 already snapshotted · 9 non-trading"
- No "Zero-work outcome" note box appears anywhere in this panel
- Scrolling to the "Run history" table below shows a new top row: Kind badge "backfill", Range "2026-05-02 → 2026-05-29", Status badge green "ok", and the same "28 calendar days · 0 already snapshotted · 9 non-trading" breakdown text under the Snapshots column

---

### UT-03 — Weekend-only backfill renders the distinct zero-work state (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Backend running
- `/data` page loaded, no job currently running in this tab

**Steps:**
1. On `/data`, click into the "Start date" field, select all text, and type `2026-05-02` (a Saturday)
2. Click into the "End date" field, select all text, and type `2026-05-03` (a Sunday)
3. Confirm "Job kind" still reads "Backfill snapshots"
4. Click the "Start" button
5. Wait for the job to finish (this is near-instant — a zero-target job completes immediately)
6. Read the status badge's color and text, and look for the explanatory note box

**Expected Result:**
- The status badge reads exactly "no new snapshots" in the neutral grey/default badge style — visibly NOT the same green used for a productive "ok" run in UT-02
- A bordered note box (below the snapshot line) reads exactly: "Zero-work outcome — every requested trading day already had a snapshot (or the range contains no trading days). No new computation was needed; this is not a failure."
- The "Snapshots backfilled" line shows "0/0 dates"
- The breakdown line reads exactly: "2 calendar days · 0 already snapshotted · 2 non-trading"
- The matching new row in the "Run history" table below also shows the grey "no new snapshots" badge (not green "ok")

---

### UT-04 — Identical re-run of a completed range shows zero-work with all-already-snapshotted (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- UT-02 has completed in this same database (the 2026-05-02 → 2026-05-29 range already has snapshots)
- No job currently running in this tab

**Steps:**
1. On `/data`, click into "Start date", select all text, type `2026-05-02`
2. Click into "End date", select all text, type `2026-05-29` (the exact same range as UT-02)
3. Click "Start"
4. Wait for the job to finish (near-instant — nothing new to compute)
5. Read the status badge and breakdown line

**Expected Result:**
- The status badge reads exactly "no new snapshots" (grey/default) — the same visual style as UT-03's zero-work badge, NOT green
- The "Zero-work outcome — …" note box appears (same exact text as UT-03)
- The "Snapshots backfilled" line shows "19/19 dates" (fully accounted for, nothing new)
- The breakdown line reads exactly: "28 calendar days · 19 already snapshotted · 9 non-trading"
- This is visibly different from UT-02's breakdown line only in the middle number (19 vs 0 already-snapshotted) — everything else about the badge/note styling matches UT-03, not UT-02

---

### UT-05 — Page reload preserves run history and never shows the empty-session text (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- UT-02, UT-03, and UT-04 have all completed in this same browser tab

**Steps:**
1. On `/data`, scroll to the "Run history" table and count the visible rows
2. Reload the page (press F5 or click your browser's refresh button)
3. Wait for the page to fully load
4. Scroll to "Run history" again and count the rows
5. Use your browser's page search (Ctrl+F) to search for the text "No job has been started this session"

**Expected Result:**
- The "Run history" table shows the same number of rows after reload as before, including the three rows from UT-02/03/04 with the same status badges and breakdown text
- The browser search for "No job has been started this session" finds zero matches anywhere on the page

---

### UT-06 — Fresh session with history but no session job shows the latest persisted run (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- At least one backfill job has completed in this database (e.g. UT-02, UT-03, or UT-04)
- You have NOT started any job in the tab/window you use for this test (open a new private/incognito window, or a hard-refresh of a tab that never clicked "Start")

**Steps:**
1. Open a new private/incognito browser window
2. Navigate to `http://localhost:3255/data`
3. Wait for the page to load, WITHOUT clicking "Start" on the job form
4. Look at the "Job progress" panel (top-right of the two-column layout)

**Expected Result:**
- The "Job progress" panel does NOT show the text "No job has been started this session"
- Instead it shows a status badge (either green "ok" or grey "no new snapshots", whichever the most recent run was), a message line, a line reading "N snapshots · N trading days in range", and — if the latest run was a backfill/both/rebuild — the calendar/already-snapshotted/non-trading breakdown line
- The panel's small heading hint above "Job progress" mentions the run's kind and date range, ending in "from a previous session"

---

### UT-07 — Inverted date range is still rejected (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- `/data` loaded, no job currently running in this tab

**Steps:**
1. Click into "Start date", select all text, type `2026-06-01`
2. Click into "End date", select all text, type `2026-05-01` (end before start)
3. Click the "Start" button

**Expected Result:**
- The job is NOT accepted — the "Job progress" panel does NOT switch to a running/live job view
- A red error message appears in the "Start a fetch / backfill job" panel (below the form), reading (verbatim, dates will match what you typed): "start date 2026-06-01 must be on or before end date 2026-05-01"
- The page does not crash or show a blank error screen
- This must NOT now silently succeed — the >370-day acceptance in UT-12 relaxed the SIZE cap only, not this ordering check

---

### UT-08 — Malformed date text shows an inline field error (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- `/data` loaded

**Steps:**
1. Click into the "Start date" field
2. Select all existing text and type `2026-13-40` (an impossible month/day)
3. Click anywhere else on the page to move focus away from the field

**Expected Result:**
- Directly below the "Start date" field, a red inline message appears reading exactly: "Enter a valid date as yyyy-MM-dd"
- The field itself gets a red border
- The "Start" button remains visibly disabled (greyed out, not clickable) even if the End date field holds a valid value
- No form submission occurs and no request is sent

---

### UT-09 — Backend unavailable shows an explicit error card, not a crash (error)

**Type:** error
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- You are able to stop the backend process for this test

**Steps:**
1. Stop the backend process (however your environment normally stops it)
2. Navigate to `http://localhost:3255/data` (or reload it if already open)
3. Wait a few seconds for the fetch to fail

**Expected Result:**
- A red-bordered card appears with a warning icon, heading "Backend unavailable", and body text: "Dataset coverage could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry."
- No panel shows fabricated coverage numbers or a blank white crash screen
- Restart the backend and reload the page afterward to leave the environment ready for further testing

---

### UT-10 — Breakdown line is absent (not a fabricated zero) for a non-backfill run (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- The "Run history" table contains at least one row whose "Kind" badge reads "seed load" (present from the committed database's initial seed — no action needed to create it) or any "fetch"/"expand"-kind row. If no such row exists in the current database, this test is not executable — skip it and note "N/A — no non-backfill row in history" rather than failing it.

**Steps:**
1. On `/data`, scroll to the "Run history" table
2. Find a row whose "Kind" badge reads "seed load" (or "fetch"/"expand")
3. Look at that row's "Snapshots" column

**Expected Result:**
- That row shows only a snapshot count (or "—") — it does NOT show any "N calendar days · N already snapshotted · N non-trading" breakdown line
- The breakdown line is completely ABSENT for this row, not shown as "0 calendar days · 0 already snapshotted · 0 non-trading" (which would be a fabricated value for a kind where the concept does not apply)

---

### UT-11 — `/scanner-runs` gains entries from the new backfill (happy path, consequential)

**Type:** happy-path
**Priority:** P1
**Surface:** `/scanner-runs`

**Preconditions:**
- UT-02 has completed (the 2026-05-02 → 2026-05-29 backfill created snapshots)

**Steps:**
1. Navigate to `http://localhost:3255/scanner-runs`
2. Look at the "As of" column in the table
3. Find and click the row for `2026-05-04`

**Expected Result:**
- Rows exist in the "As of" column for `2026-05-04`, `2026-05-15`, and `2026-05-29` (dates that would never have appeared before this iteration's fix)
- Clicking the `2026-05-04` row navigates to a URL beginning `/scanner-runs/` and shows the heading "Scanner Run" with subtitle "The exact, immutable as-of view the scanner produced on this date"
- A regime badge and a table of stock rows render for that date — NOT an empty state, NOT an error card

---

### UT-12 — Large (>370-day) backfill is accepted, not rejected (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- `/data` loaded, no job currently running in this tab
- Run this test near the END of your test session — the job may run for a long time and will keep the "Start" button on this tab disabled until it finishes or you reload

**Steps:**
1. Click into "Start date", select all text, type `2025-06-01`
2. Click into "End date", select all text, type `2026-07-17` (a 412-calendar-day span)
3. Click "Start"
4. Watch the "Job progress" panel immediately after submission

**Expected Result:**
- The job IS accepted — the panel switches to the running job view (status badge reads "running" with a spinner)
- No "date range too large" or similar rejection error appears anywhere
- A grey "chunk N/M" badge appears next to the status badge, where M (the total) is greater than 1 (this range spans multiple 90-day date windows)

---

### UT-13 — Chunk progress advances while the large backfill runs (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- UT-12's job was just submitted and is still running

**Steps:**
1. Without navigating away, watch the "chunk N/M" badge in the "Job progress" panel for about 30 seconds
2. Also watch the "Snapshots backfilled" line's "done/total dates" figure

**Expected Result:**
- The chunk badge's N (first number) advances from 0 to 1 or higher during the observation window
- The "dates done" figure in "Snapshots backfilled" advances above 0
- No error message mentioning "range" or "cap" appears in the panel
- Full completion is NOT required for this test to pass — only visible forward progress

---

### UT-14 — Interrupted job still shows a distinct neutral badge after a backend restart (regression, J-04)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- A backfill job is currently running in this tab (reuse UT-12's job if it's still going, or start a fresh small backfill — e.g. 2024-01-01 → 2024-01-05 — first)
- You are able to stop and restart the backend process

**Steps:**
1. While the job is running, stop the backend process
2. Restart the backend process
3. Reload `http://localhost:3255/data`
4. Find the interrupted run's row in the "Run history" table (or the "Job progress" panel if it's the latest run)
5. Read its status badge

**Expected Result:**
- The badge reads "interrupted" in the same neutral grey/default style as the zero-work "no new snapshots" badge — but with the distinct text "interrupted", not confused with either "ok", "no new snapshots", or "failed"
- The interrupted run remains visible in "Run history" — it is not silently dropped

---

### UT-15 — Header readiness badge shows the correct boot-state sequence (regression, J-04)

**Type:** regression
**Priority:** P2
**Surface:** global app shell (visible on every page, including `/data`)

**Preconditions:**
- You can restart the backend and immediately reload a page (can be combined with UT-14's restart)

**Steps:**
1. Restart the backend
2. Immediately load (or reload) `http://localhost:3255/data`
3. Watch the small status badge in the page header (top of every page) over the next 10-30 seconds
4. Separately, with the backend stopped, reload the page once more

**Expected Result:**
- Briefly on load: a grey badge reading "Checking backend…"
- During historical warm-up: an amber badge reading "Initializing… history N/M" (N/M are numbers that increase over time)
- Once warm-up finishes: a green badge reading exactly "Ready"
- With the backend stopped: a red badge reading exactly "Backend unavailable"
- All four states are visually distinct from one another (different badge colors, different text)

---

### UT-16 — Zero-work and breakdown information is self-explanatory (UX)

**Type:** ux
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- At least one productive run (UT-02) and one zero-work run (UT-03 or UT-04) exist in "Run history"

**Steps:**
1. Without reading any developer documentation or this test plan's explanations, look only at the "Job progress" panel and a zero-work row in "Run history"
2. Try to answer, from the on-screen text alone: "did this run do anything, and if not, why not?"

**Expected Result:**
- The badge text ("no new snapshots") and the note box ("Zero-work outcome — every requested trading day already had a snapshot…") together answer the question in plain English, with no raw internal field names (e.g. no literal "dates_total" or "snapshots_created" text visible anywhere in the panel)
- The breakdown line ("N calendar days · N already snapshotted · N non-trading") is readable as plain language, not a cryptic code
- No new navigation, page, or menu item was needed to find any of this — it is all on the same `/data` page the operator already uses to submit jobs

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/data` loads without errors | smoke | P1 | `/data` |
| UT-02 | May-2026 backfill creates snapshots | happy-path | P1 | `/data` |
| UT-03 | Weekend-only backfill = zero-work state | happy-path | P1 | `/data` |
| UT-04 | Identical re-run = zero-work state | happy-path | P1 | `/data` |
| UT-05 | Reload preserves run history | regression | P1 | `/data` |
| UT-06 | Fresh session shows latest persisted run | happy-path | P1 | `/data` |
| UT-07 | Inverted range still rejected | regression | P1 | `/data` |
| UT-08 | Malformed date shows inline error | validation | P2 | `/data` |
| UT-09 | Backend unavailable shows error card | error | P2 | `/data` |
| UT-10 | Breakdown absent for non-backfill run | regression | P2 | `/data` |
| UT-11 | `/scanner-runs` gains new dates | happy-path | P1 | `/scanner-runs` |
| UT-12 | >370-day backfill accepted | happy-path | P1 | `/data` |
| UT-13 | Chunk progress advances | happy-path | P2 | `/data` |
| UT-14 | Interrupted job badge after restart | regression | P1 | `/data` |
| UT-15 | Readiness badge boot-state sequence | regression | P2 | global |
| UT-16 | Zero-work info is self-explanatory | ux | P2 | `/data` |

**P1 tests must all pass for browser QA verdict to be PASS.**
