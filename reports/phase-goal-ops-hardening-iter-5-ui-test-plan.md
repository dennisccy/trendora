# Phase goal-ops-hardening-iter-5 — UI Test Plan

**Phase:** goal-ops-hardening-iter-5
**Date:** 2026-07-20
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Context for the tester

This iteration (J-06, "Pages load only what they need") is primarily a measurement + code-audit pass,
but it shipped one real functional fix and one real behavior change, both user-observable:

1. **`/backtest` is now much faster.** Its "Forward-test scorecard" used to take up to ~35 seconds to
   populate for the current date, because the backend recomputed a large statistic from scratch on
   every page view. It now populates in a fraction of a second, because the same statistic is
   pre-computed once at ingest time and read from a cache. The numbers shown are unchanged — only the
   wait is gone.
2. **A backfill/rebuild job on `/data` may now take up to ~35 seconds longer to reach "completed,"** and
   its existing "Refreshed: ..." text line can now include one new word: "forward aggregates". This
   line appears in three places that all share the same underlying data: the live Job progress panel,
   the persisted last-run summary card, and the Run history table.

No frontend file was changed this iteration, no new page/button/form was added, and no navigation
changed. Because this iteration's own scope is "every nav-listed page loads only what it needs" (all 11
pages, measured for the first time together), this plan also includes one consolidated sweep of the 9
pages that had zero code change, to confirm none of them regressed while shared backend modules were
touched.

Ports: backend prod-mode at `http://localhost:8255` (health check `/api/health`), frontend prod-mode at
`http://localhost:3255`. No login is required anywhere in this product.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Backtest page loads and populates quickly (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Backend running in prod mode via `scripts/start-backend.sh` (reachable at `http://localhost:8255/api/health`)
- Frontend running in prod mode via `scripts/start-frontend.sh`, reachable at `http://localhost:3255`
- The committed seed database is warm (already ingested; at least one scanner run exists)

**Steps:**
1. Navigate to `http://localhost:3255/backtest`
2. Watch the page immediately after navigation, for up to 10 seconds

**Expected Result:**
- The page briefly shows animated grey placeholder blocks (three small cards in a row, then one large
  card below them — the `BacktestSkeleton` loading state) — never a blank white page
- Within roughly 1-2 seconds, the placeholders are replaced by real content: the heading "Backtest", a
  "Viewing as-of ... (latest)" badge near the top, an "As-of scan summary" heading, and a "Forward-test
  scorecard" heading above a table with one row for each of 1d, 5d, 10d, 20d, and 60d
- The "Forward-test scorecard" table's "Cohort" column shows real percentage values (not "—" in every
  row) for at least the shorter horizons
- No red "Backend unavailable" banner appears
- No browser console errors

---

### UT-02 — Operator can switch the return-attribution horizon (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- UT-01 has already been completed successfully — the page is loaded and showing the scorecard for the
  latest as-of date

**Steps:**
1. Scroll down to the "Return attribution" heading (below "Forward-test scorecard")
2. In the same row as that heading, locate the horizon button group (a row of buttons reading "1d",
   "5d", "10d", "20d", "60d")
3. Click the "20d" button
4. Observe the "Return attribution" section and the "Leadership cohorts" section below it

**Expected Result:**
- The "20d" button becomes visually highlighted (accent-colored background) and whichever button was
  previously active is no longer highlighted
- No page reload or new navigation occurs — the switch is effectively instant (under half a second)
- Under the "Leadership cohorts" heading, the "Top Sectors" and "Top Themes" panel headers relabel their
  return column from "Fwd <previous>d" to "Fwd 20d", and the "Ranked cohort" table's last column header
  changes to "Fwd 20d" too
- The return values displayed in those three panels change to reflect the 20-day horizon (different
  from whatever was shown for the previously-selected horizon)

---

### UT-03 — Viewing an as-of date for the first time still populates correctly (error / edge case)

**Type:** error
**Priority:** P2
**Surface:** `/backtest`

**Preconditions:**
- UT-01 completed; page loaded on `/backtest`
- The global as-of control (top bar, visible on every page — a button with a calendar icon, currently
  reading "Latest") has not yet been moved away from "Latest" this session

**Steps:**
1. On `/backtest`, locate the small square "‹" button immediately to the left of the "Latest" date
   control in the top bar (its tooltip/aria-label is "Previous available date")
2. Click it once
3. Watch the "Forward-test scorecard" table while the page updates for this now-historical as-of date;
   wait up to 60 seconds for it to finish
4. Once it finishes and shows real values, click the "‹" button one more time, then click the "›"
   button (aria-label "Next available date", to the right of "‹") twice, to return to the exact date
   from step 2
5. Watch the "Forward-test scorecard" table again on this second visit to that same date

**Expected Result:**
- Step 1 result: the badge near the top changes to "Viewing as-of <date> (historical)"
- Step 3: the scorecard eventually repopulates with real values (not all "—") for every horizon. This
  FIRST view of that specific historical date may take noticeably longer than UT-01 — up to about 30
  seconds is acceptable — but the `BacktestSkeleton` placeholder stays visible the whole time. The page
  must never show a blank screen, a spinner stuck past ~60 seconds, or a "Backend unavailable" error
- Step 5: on this second visit to the SAME historical date, the scorecard populates quickly (a couple of
  seconds, not another long wait) — this confirms the value was cached after the first view
- The horizon values shown in step 5 exactly match what was shown at the end of step 3 (same date, same
  numbers — only the second view is faster)

---

### UT-04 — Leadership cohorts and ranked-cohort table are unaffected (regression)

**Type:** regression
**Priority:** P3
**Surface:** `/backtest`

**Preconditions:**
- UT-01 completed; page loaded for the latest as-of date

**Steps:**
1. Scroll to the "Leadership cohorts" heading
2. Inspect the "Ranked cohort" table at the bottom of that section

**Expected Result:**
- "Top Sectors" and "Top Themes" panels each list up to 5 rows, each with a rank number, a
  ticker/name, a trend label, a colored score badge, and a return figure
- The "Ranked cohort" table shows up to 10 rows with columns "#", "Ticker", "Setup", "Leadership", and
  "Fwd <n>d", fully populated (not blank, not stuck loading)
- This section's data and layout are identical in shape to before this iteration — this iteration
  changed only how fast the page underneath it loads, never what it shows

---

### UT-05 — Data Manager page loads (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Same backend/frontend prod-mode preconditions as UT-01

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait up to 5 seconds for the page to finish loading

**Expected Result:**
- The heading "Data Manager" appears
- A "Job progress" panel is visible — either the text "No job has been started this session..." or a
  summary card of the most recent persisted run, depending on session history; either is acceptable
- Further down the page, a "Rebuild snapshots for current universe" panel and a "Run history" table are
  both visible
- No red error banner and no blank page

---

### UT-06 — Starting a backfill job shows the new "forward aggregates" entry (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- On `/data`; no job is currently running this session (the "Start" button in the job form is enabled
  and does not read "Job running…")

**Steps:**
1. Scroll to the "Rebuild snapshots for current universe" panel further down the page and note the date
   shown in parentheses after "the latest snapshot" (e.g. "2026-06-15") — this is a known-good, in-range
   date
2. Scroll back to the "Start a fetch / backfill job" panel near the top of the page
3. Type the noted date from step 1 into the "Start date" field
4. Type the SAME date into the "End date" field
5. Confirm the "Job kind" dropdown shows "Backfill snapshots" (its default) — leave it as is
6. Click the "Start" button
7. Watch the "Job progress" panel below the form until the status badge stops showing a spinner, waiting
   up to 60 seconds

**Expected Result:**
- While running: the status badge shows a spinning icon with a status label; a "Snapshots backfilled"
  line with a progress bar is visible
- Once finished: the status badge shows a completed-style label. Because Start and End are the same
  already-covered date, this will likely complete as a "zero-work" outcome, with a note reading
  "Zero-work outcome — every requested trading day already had a snapshot..." — this is an expected,
  non-failure outcome, not a bug
- Directly below the snapshots/breakdown line, a new text line appears reading exactly "Refreshed: "
  followed by a comma-separated list that includes the words **"forward aggregates"** — for example,
  "Refreshed: coverage, market phase, forward aggregates, research hot keys"

---

### UT-07 — "Refreshed: ..." line is consistent across all three places it appears (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- UT-06 has just been completed successfully — a job whose "Refreshed: ..." line includes "forward
  aggregates" has just finished

**Steps:**
1. Without leaving the page, scroll down to the "Run history" table
2. Find the top row (the job just run in UT-06) and inspect its "Snapshots" column
3. Reload the page (F5) — this starts a fresh page session with no job started yet, so the "Job
   progress" panel falls back to the persisted last-run view
4. Inspect the "Job progress" panel's contents after the reload

**Expected Result:**
- Step 2: the "Run history" row's "Snapshots" column shows a "Refreshed: ..." line that also includes
  "forward aggregates", matching what was shown live in UT-06
- Step 4: the "Job progress" panel (now showing the persisted last-run summary, not the live card) also
  shows a "Refreshed: ..." line including "forward aggregates" — worded identically to the live card and
  the table row
- All three locations agree with each other — no location shows a different or missing list

---

### UT-08 — Job heartbeat stays alive during the longer finalize step (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Starting a fresh backfill/both/rebuild job, as in UT-06 (repeating the exact same date range is fine)

**Steps:**
1. Start a "Backfill snapshots" or "Fetch + backfill" job (same form as UT-06)
2. While the job's status badge still shows the spinning "running" icon, watch the small grey text near
   the progress bar that reads "updated <N>s ago" (or "<N>m <N>s ago")

**Expected Result:**
- The "updated ... ago" text keeps resetting to a small number every second or two — it should never sit
  unchanged for more than about 10-15 seconds (a longer stall would append "· possibly stalled" to the
  text, which should NOT be seen while the job is genuinely healthy)
- Even if the overall job takes noticeably longer than it used to (up to roughly 30-40 extra seconds is
  expected, per this iteration's change), this heartbeat text is the operator's visible evidence that the
  job is still alive, not frozen
- The job eventually reaches a final (non-"running") status badge

---

### UT-09 — Job start form still rejects an incomplete date range (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- On `/data`; no job currently running

**Steps:**
1. In the "Start a fetch / backfill job" panel, make sure both the "Start date" and "End date" fields
   are empty
2. Look at the "Start" button
3. Type an intentionally malformed date, `2026-13-40`, into the "Start date" field, leaving "End date"
   empty

**Expected Result:**
- Step 2: the "Start" button is visibly disabled (greyed out / dimmed) and cannot be clicked — the form
  does not submit with empty dates
- Step 3: the "Start" button remains disabled — an invalid date does not enable submission
- No job is created and no new row is added to "Run history" from either attempt
- This confirms the pre-existing date-validation behavior is unaffected by this iteration's backend-only
  changes

---

### UT-10 — Remaining nav pages still load correctly (regression sweep)

**Type:** regression
**Priority:** P1
**Surface:** `/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/scanner-runs`, `/watchlist`,
`/evidence`, `/research/event-study`

**Preconditions:**
- Backend/frontend running in prod mode, same as UT-01
- None of these 9 pages had any code change this iteration — this test exists solely to confirm none of
  them regressed while shared backend modules (touched by this iteration's cache fix) were changed

**Steps:**
1. Navigate to `http://localhost:3255/` and wait for it to finish loading
2. Navigate to `http://localhost:3255/stocks` and wait for it to finish loading
3. Navigate to `http://localhost:3255/stocks/AAPL` and wait for it to finish loading
4. Navigate to `http://localhost:3255/sectors` and wait for it to finish loading
5. Navigate to `http://localhost:3255/themes` and wait for it to finish loading
6. Navigate to `http://localhost:3255/scanner-runs` and wait for it to finish loading
7. Navigate to `http://localhost:3255/watchlist` and wait for it to finish loading
8. Navigate to `http://localhost:3255/evidence` and wait for it to finish loading
9. Navigate to `http://localhost:3255/research/event-study` and wait for it to finish loading

**Expected Result (applies independently to each step above):**
- Each page shows its own heading — respectively: "Dashboard", "Stocks", "AAPL", "Sectors", "Themes",
  "Scanner Runs", "Watchlist", "Evidence", "Research — Setup & Pattern event study"
- Each page finishes loading (its skeleton/placeholder clears) within a few seconds — none hang
  indefinitely or stay stuck on a loading placeholder
- None show a blank white page, an unhandled JavaScript error overlay, or a "Backend unavailable" banner
- `/watchlist` may legitimately show "Your watchlist is empty" if no entries are saved yet — that is a
  valid, non-error state, not a failure
- No browser console errors on any of the 9 pages

---

### UT-11 — The new "forward aggregates" wording is understandable (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/data`

**Preconditions:**
- UT-06/UT-07 completed — a "Refreshed: ..." line including "forward aggregates" is visible somewhere on
  the page (live card, last-run card, or a Run history row)

**Steps:**
1. Read the full "Refreshed: ..." line as displayed (e.g., "Refreshed: coverage, market phase, forward
   aggregates, research hot keys")
2. Without reading any source code or documentation, judge whether a non-developer operator could
   reasonably infer that "forward aggregates" refers to some kind of pre-computed background statistic

**Expected Result:**
- The phrase "forward aggregates" reads as plain English (two ordinary words, no code identifiers,
  underscores, or abbreviations), consistent in style with its neighbors ("coverage", "market phase",
  "research hot keys")
- The line requires no tooltip or explanation to parse at a basic level — it reads as "another kind of
  background data that just got refreshed," matching the rest of the line

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Backtest page loads and populates quickly | smoke | P1 | `/backtest` |
| UT-02 | Operator can switch the return-attribution horizon | happy-path | P1 | `/backtest` |
| UT-03 | Viewing an as-of date for the first time still populates correctly | error | P2 | `/backtest` |
| UT-04 | Leadership cohorts and ranked-cohort table are unaffected | regression | P3 | `/backtest` |
| UT-05 | Data Manager page loads | smoke | P1 | `/data` |
| UT-06 | Starting a backfill job shows the new "forward aggregates" entry | happy-path | P1 | `/data` |
| UT-07 | "Refreshed: ..." line is consistent across all three places | regression | P1 | `/data` |
| UT-08 | Job heartbeat stays alive during the longer finalize step | ux | P2 | `/data` |
| UT-09 | Job start form still rejects an incomplete date range | validation | P2 | `/data` |
| UT-10 | Remaining nav pages still load correctly | regression | P1 | 9 pages |
| UT-11 | The new "forward aggregates" wording is understandable | ux | P3 | `/data` |

**P1 tests must all pass for browser QA verdict to be PASS.**

Note: this plan intentionally does NOT duplicate the functional test plan's TC-01/TC-02..TC-12 (which
measure exact millisecond TTI/API latency via DevTools for all 11 pages plus backend boot time — see
`reports/qa/goal-ops-hardening-iter-5-test-plan.md`). The test cases above check the SAME pages at the
level an operator without DevTools access can observe (does it look fast, does it show real data, does
it hang) and focus on the two surfaces that actually carry a user-visible change this iteration.
