# Phase goal-ops-hardening-iter-9 — UI Test Plan

**Phase:** goal-ops-hardening-iter-9
**Date:** 2026-07-22
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Context

Per `reports/phase-goal-ops-hardening-iter-9-ui-surface-map.md` and
`reports/phase-goal-ops-hardening-iter-9-user-visible-changes.md`, **zero frontend files changed** this
iteration. `Frontend Present: yes` was set solely to force browser-qa to re-verify four already-shipped
journeys (J-01, J-03, J-04, J-05) that iter-8 shipped a backend fix for but never checked live. Every test
case below is therefore a **re-verification** case, not a new-feature case — "Type" reflects the nature of
the check (smoke / happy-path / validation / error / regression / ux), not whether the underlying code is
new. Do not duplicate the API-only checks already in `reports/qa/goal-ops-hardening-iter-9-test-plan.md`
(TC-05 through TC-14, the host-guard/`taskset`/replay/libc-memoization checks) — those have no browser
surface. This plan covers only what a human operator can see and click.

**Preconditions common to all cases below (unless a case states otherwise):**
- Backend running at `http://localhost:8255` (or the project's configured backend port), launched via
  `scripts/start-backend.sh` with `project-extensions/host-guard/host-guard.env` present and
  `HOST_GUARD_ENABLED=1` (this iteration's AG-10 fix is active on this launch path — TC-1/TC-5's evidence
  depends on the launch script actually applying it).
- Frontend running at `http://localhost:3255`.
- No prior scanner snapshot exists for `2026-05-15` (an unsnapshotted historical trading day — confirm on
  `/data`'s coverage panel before starting; pick a different unsnapshotted date if `2026-05-15` is already
  covered from a prior run).

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/data` page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Backend and frontend both running (see Context above)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the page to finish loading

**Expected Result:**
- The page renders the heading "Data Manager" with subtitle text starting "Grow the dataset on demand"
- The "Dataset coverage" panel is visible with defined metrics: "Price history", "Universe (as of date)",
  "Candidate universe", "Symbols", "Trading days", "Snapshot dates", "Backfill gaps"
- The "Start a fetch / backfill job" panel and the "Job progress" panel are both visible
- No red "Backend unavailable" error card appears
- No blank screen or unhandled application error page

---

### UT-02 — `/scanner-runs` page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/scanner-runs`

**Preconditions:**
- Backend and frontend both running
- At least one scanner run already exists (true after any prior iteration's ingest)

**Steps:**
1. Navigate to `http://localhost:3255/scanner-runs`
2. Wait for the page to finish loading

**Expected Result:**
- The page renders the heading "Scanner Runs" with subtitle "History of immutable, dated scan snapshots — open one to see exactly what the scanner said on that date"
- A table with column headers "As of", "Regime", "Actionable", "Breakout-watch", "Pullback-watch", "Stocks" is visible, with at least one row
- No red "Backend unavailable" error card appears

---

### UT-03 — Home page (`/`) loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend and frontend both running

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Wait for the page to finish loading

**Expected Result:**
- The "Market Phase & Severity" card is visible in the at-a-glance summary row
- The card shows either a numeric severity value with "/ 100 severity", or (if not enough history) the text
  "Not enough history to derive a market phase for this date — reported NA, never fabricated" — never a red
  "Market-phase data unavailable — backend not reachable." message
- No blank screen or unhandled application error page

---

### UT-04 — Backfill for one historical day reaches `"ok"` with populated aggregates (happy-path, J-05 step 1)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- `2026-05-15` (or another confirmed-unsnapshotted trading day) has no existing scanner snapshot
- No job is already running on `/data`

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the "Start a fetch / backfill job" panel, type `2026-05-15` into the "Start date" field
3. Type `2026-05-15` into the "End date" field
4. In the "Job kind" dropdown, select "Backfill snapshots"
5. Click the "Start" button
6. Wait for the "Job progress" panel's status badge to leave the animated "running" state (poll every few
   seconds; do not refresh the page)

**Expected Result:**
- The job status badge (`data-testid="job-status"`) reads exactly "ok" — never "partial" or "failed"
- Below the snapshot progress bar, a line reading "Refreshed: " followed by a comma-separated, non-empty
  list of aggregate category names (e.g. "latest date snapshot, coverage payload, membership timeline,
  market phase, research hot key caches") is visible — this is the `aggregates_refreshed` field rendered
  live
- "Snapshots backfilled" shows `1/1 dates` and "1 snapshots · ... forward returns inserted" (a productive
  run, not a zero-work outcome)

---

### UT-05 — Scanner leaderboard renders the new date immediately (happy-path, J-05 step 2a / TC-2)

**Type:** happy-path
**Priority:** P1
**Surface:** `/scanner-runs`

**Preconditions:**
- UT-04's backfill for `2026-05-15` has completed

**Steps:**
1. Navigate to `http://localhost:3255/scanner-runs`
2. Locate the table row whose "As of" column shows the date `May 15, 2026` (or the formatted equivalent of
   `2026-05-15`)
3. Observe the row's "Regime", "Actionable", "Breakout-watch", "Pullback-watch", and "Stocks" columns

**Expected Result:**
- The row for `2026-05-15` is present and renders immediately with populated values in every column (a
  Regime badge with a non-empty label, and numeric counts) — no loading skeleton, no blank/dash cells, and
  no "computing" or pending state of any kind
- The row does not require a manual page refresh to appear

---

### UT-06 — Scanner run detail page matches the stored snapshot (happy-path, J-01 step 4 / J-05 step 2a / TC-2)

**Type:** happy-path
**Priority:** P1
**Surface:** `/scanner-runs/[runId]`

**Preconditions:**
- UT-05 confirmed the `2026-05-15` row exists on `/scanner-runs`

**Steps:**
1. From `http://localhost:3255/scanner-runs`, click the `May 15, 2026` date link in the "As of" column
2. Wait for the page to load

**Expected Result:**
- The page renders the heading "Scanner Run" with subtitle "The exact, immutable as-of view the scanner produced on this date"
- A header strip shows the as-of date and regime badge
- The leaderboard table below it lists stock rows with a setup-status badge and score for each — the same
  row count and values implied by the leaderboard counts seen in UT-05 (e.g. the same "Actionable" count)
- No "Run not found" empty state and no red "Backend unavailable" error card appears
- Clicking "All runs" navigates back to `http://localhost:3255/scanner-runs`

---

### UT-07 — Market Phase card reflects the new as-of with no visible delay (happy-path, J-05 step 2a / TC-3)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- UT-04's backfill for `2026-05-15` has completed
- The global as-of switcher (top of any page) is available to select `2026-05-15`

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Use the global as-of switcher to select `2026-05-15`
3. Observe the "Market Phase & Severity" card immediately after the as-of changes

**Expected Result:**
- The "Market Phase & Severity" card updates to show a phase badge, severity number, and "P(bear) ..." value
  for `2026-05-15` within roughly one second — no visible spinner, blank flash, or multi-second stall before
  the numbers appear (this proves the value is served from `market_phase_cache`, not recomputed live)
- The card never shows "Market-phase data unavailable — backend not reachable" during this check

---

### UT-08 — Cold `/data` load after restart respects the coverage budget (regression, J-05 step 3 / TC-4)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- UT-04's ingest has completed
- Operator can restart the backend process (`scripts/start-backend.sh`)

**Steps:**
1. Stop the running backend process
2. Restart it via `scripts/start-backend.sh`
3. Immediately navigate to `http://localhost:3255/data` (a cold load — no prior visit to `/data` in this
   browser session since the restart)
4. Time how long it takes for the "Dataset coverage" panel's metric values to render

**Expected Result:**
- The "Dataset coverage" panel renders its metric values within the committed budget in
  `reports/perf-budgets.md` (≤ 3 s for the `/data` page; the underlying `GET /api/data` call is budgeted at
  ≤ 1.5 s warm / ≤ 60 s cold-worst-case per that report) — no multi-second stall or spinner hang beyond that
  window
- No red "Backend unavailable" error card appears
- (Developer-verifiable, not operator-verifiable from the browser alone: the backend process should not
  perform a full `daily_prices` table prefill for this request — record this as PASS/FAIL from backend logs
  or process RSS if available, otherwise defer to the functional test plan's TC-04)

---

### UT-09 — Job form rejects an invalid date with an inline error (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- No job is currently running on `/data`

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Click into the "Start date" field in the "Start a fetch / backfill job" panel
3. Type `2026-13-40` (an invalid calendar date) into the "Start date" field
4. Click anywhere else on the page to move focus out of the field

**Expected Result:**
- A red inline error reading "Enter a valid date as yyyy-MM-dd" appears directly below the "Start date"
  field
- The "Start" button remains disabled (greyed out, not clickable) while the invalid value is present
- No job is submitted and no network request for `startDataJob` fires

---

### UT-10 — Interrupted job shows an explicit state, never a stuck "running" row (error, J-04 step 6 / UnfinishedImportsPanel)

**Type:** error
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Operator can kill and restart the backend process
- A long-running job kind is available to start (e.g. a multi-day `fetch` or `backfill` spanning several
  weeks, so it is still running when the backend is killed)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Start a backfill job for a multi-week range not yet snapshotted (e.g. Start `2026-06-01`, End
   `2026-06-30`, Job kind "Backfill snapshots"), click "Start"
3. While the "Job progress" panel still shows the job status badge animating (mid-run), kill the backend
   process (simulate a crash — e.g. `kill -9` the uvicorn PID)
4. Restart the backend via `scripts/start-backend.sh`
5. Reload `http://localhost:3255/data`
6. Locate the affected job's row in the "Unfinished imports" panel

**Expected Result:**
- The "Unfinished imports" panel is visible (it only renders when at least one unfinished import exists)
- The affected job's row shows an explicit status badge reading "interrupted" (not "running", not a spinner,
  not a blank/missing row)
- The row shows its last persisted progress counts (done / remaining / failed symbols or dates) frozen at
  the point of the crash — not reset to zero and not silently advancing
- A "Retry" or "Resume" control and a "Dismiss" control are visible on the row

---

### UT-11 — Backend crash shows a NO-GO preflight banner distinct from initializing (error, J-04 step 4)

**Type:** error
**Priority:** P1
**Surface:** global (all pages)

**Preconditions:**
- Operator can kill the backend process
- Frontend is currently loaded in the browser, showing a "GO" or normal preflight banner state

**Steps:**
1. With `http://localhost:3255/` (or any page) open and the preflight banner showing its normal "GO" thin
   green strip, kill the backend process
2. Wait up to one health-poll interval (a few seconds) without reloading the page
3. Observe the banner at the top of the page

**Expected Result:**
- The banner switches to a loud, full-width red banner reading exactly "NO-GO — do not rely on today's
  board." with the reason "Backend is unavailable — the preflight check could not run." listed below it
- This NO-GO presentation is visually distinct from the earlier thin "GO — today's board is current." strip
  and from the neutral "Checking board status…" loading strip — never a blank page or unhandled crash

---

### UT-12 — Health badge shows boot-phase detail during initializing window (regression, J-04 steps 2–3)

**Type:** regression
**Priority:** P1
**Surface:** top bar (all pages)

**Preconditions:**
- Operator can restart the backend process
- Frontend is already open in the browser before the restart

**Steps:**
1. With `http://localhost:3255/` open in the browser, restart the backend via `scripts/start-backend.sh`
2. Immediately watch the top-bar readiness badge (next to the Trendora logo/nav) without reloading the page
3. Capture the badge's text during the pre-ready window (before it turns green)

**Expected Result:**
- During the pre-ready window, the badge shows an amber pill reading "Initializing…" followed by
  `history n/m` (a progress fraction, e.g. "history 3/12") — matching the boot phase/progress the raw
  `GET /api/health` payload reports in the same window
- The badge never shows a bare "Backend unavailable" during this initializing window
- Once boot completes, the badge turns to a green pill reading exactly "Ready"

---

### UT-13 — Repeating an identical backfill shows a distinct "no new snapshots" outcome, never fake success (regression, J-01 step 6/8)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- A backfill has already been run once for a given range (e.g. UT-04's `2026-05-15` run, or J-01's own
  `2026-05-02` → `2026-05-29` range) so every trading day in that range already has a snapshot
- No job is currently running

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Re-enter the exact same Start/End dates as a previously-completed backfill (e.g. Start `2026-05-15`, End
   `2026-05-15`) with Job kind "Backfill snapshots"
3. Click the "Start" button
4. Wait for the job to complete

**Expected Result:**
- The job status badge shows a distinct neutral/grey label reading "no new snapshots" — NOT the same green
  "ok" badge styling used for a productive run
- The breakdown line below the progress bar shows the day counted as "already snapshotted" (not a fresh
  ingest)
- No "Refreshed: ..." aggregates line implies fresh work was performed for a day that was, in fact, already
  covered

---

### UT-14 — Persisted job history survives a page reload (regression, J-01 step 7)

**Type:** regression
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- At least one job (e.g. UT-04's backfill) has completed this session

**Steps:**
1. On `http://localhost:3255/data`, confirm the "Job progress" panel shows the completed job from UT-04
2. Refresh the page (press F5 or Cmd+R)
3. Scroll to the "Run history" panel at the bottom of the page

**Expected Result:**
- The "Run history" panel lists the `2026-05-15` run (or whichever run(s) completed this session) with the
  same status, kind, and date range as before the reload
- The page never shows "No job has been started this session" if a persisted run exists — that copy is
  reserved for a cold session with zero persisted runs

---

### UT-15 — A backfill spanning more than 370 days is accepted, not rejected (regression, J-03 steps 1–2)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- No job is currently running on `/data`

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Type `2025-06-01` into the "Start date" field
3. Type `2026-07-17` into the "End date" field (a span of more than 370 calendar days)
4. Select "Backfill snapshots" in the "Job kind" dropdown
5. Click the "Start" button

**Expected Result:**
- No "date range too large" (or similarly worded) rejection message appears anywhere on the page
- The "Job progress" panel shows the job status badge in its running/animated state with a non-zero
  "chunk N/M" indicator, and the snapshot progress bar begins advancing — proving the request was accepted
  and is executing in visible chunks
- (Full completion may extend beyond a 5-minute operator check — it is sufficient to confirm the job was
  accepted and at least the first chunk's progress advances; full completion is tracked via the persisted
  job history per UT-14)

---

### UT-16 — Readiness state is discoverable and consistent on every page (ux)

**Type:** ux
**Priority:** P2
**Surface:** top bar + global banner (all pages)

**Preconditions:**
- Backend and frontend both running normally (a "Ready" / "GO" steady state)

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Note the top-bar readiness badge state and the preflight banner state
3. Navigate to `http://localhost:3255/data`
4. Note the same two elements
5. Navigate to `http://localhost:3255/scanner-runs`
6. Note the same two elements

**Expected Result:**
- The top-bar readiness badge (green "Ready" pill) and the preflight banner (thin green "GO — today's board
  is current." strip) are visible on every one of the three pages, in the same position, with identical
  wording — a user does not need to hunt for backend status information; it is always in view without
  navigating anywhere extra
- Neither element requires more than glancing at the top of the page to find

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/data` loads | smoke | P1 | `/data` |
| UT-02 | `/scanner-runs` loads | smoke | P1 | `/scanner-runs` |
| UT-03 | Home page loads | smoke | P1 | `/` |
| UT-04 | Backfill reaches `"ok"` with aggregates | happy-path | P1 | `/data` |
| UT-05 | Leaderboard renders new date immediately | happy-path | P1 | `/scanner-runs` |
| UT-06 | Run detail matches stored snapshot | happy-path | P1 | `/scanner-runs/[runId]` |
| UT-07 | Market phase card updates with no delay | happy-path | P1 | `/` |
| UT-08 | Cold `/data` load respects budget | regression | P1 | `/data` |
| UT-09 | Invalid date shows inline error | validation | P2 | `/data` |
| UT-10 | Crash mid-job shows "interrupted" | error | P1 | `/data` |
| UT-11 | Backend crash shows NO-GO banner | error | P1 | global |
| UT-12 | Health badge shows boot-phase detail | regression | P1 | top bar |
| UT-13 | Repeat backfill shows "no new snapshots" | regression | P1 | `/data` |
| UT-14 | Job history survives reload | regression | P2 | `/data` |
| UT-15 | >370-day backfill accepted | regression | P1 | `/data` |
| UT-16 | Readiness state discoverable everywhere | ux | P2 | global |

**P1 tests must all pass for browser QA verdict to be PASS.**

**Coverage cross-reference:**
- J-05 (target, all 4 steps): UT-04 (step 1), UT-05/UT-06/UT-07 (step 2a), UT-08 (step 3), UT-11 (step 4
  is exercised as part of the required-still-passing J-04 crash check — the same health-responsiveness
  claim; the heavy-ingest health-poll itself is an API-level check, see functional TC-05)
- J-01 (required-still-passing): UT-01, UT-05, UT-06, UT-13, UT-14
- J-03 (required-still-passing): UT-15
- J-04 (required-still-passing): UT-10, UT-11, UT-12
