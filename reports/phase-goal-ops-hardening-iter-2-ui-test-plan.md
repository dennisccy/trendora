# Phase goal-ops-hardening-iter-2 — UI Test Plan

**Phase:** goal-ops-hardening-iter-2
**Date:** 2026-07-19
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Scope note

This phase is backend-heavy (a new persisted `coverage_snapshot` table, an ingest finalize hook, a
launch-script memory/logfile fix) with exactly one additive frontend change: a read-only "Refreshed:
..." line added to the existing `BackfillBreakdown` component on `/data` (3 render sites: the live Job
progress panel, the persisted Last-run summary card, and the Run history table). No new page, form,
button, or nav entry was added. The 21 test cases in `reports/qa/goal-ops-hardening-iter-2-test-plan.md`
already cover the API-level contracts (byte-identity, call counts, memory ceilings, network isolation)
in depth — this plan does NOT repeat those; it covers only what an operator sees and clicks in a
browser, derived from the 5 rows in `reports/phase-goal-ops-hardening-iter-2-ui-surface-map.md`.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — `/data` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Backend and frontend are running; frontend reachable at http://localhost:3255
- At least one prior fetch/backfill job exists in the database (so Run history is non-empty) — not
  required for the page to load, just to see a populated table instead of the empty-state copy

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Data Manager" is visible near the top of the page, with the subtitle beginning "Grow the
  dataset on demand — view coverage and gaps..."
- The "Dataset coverage" panel is visible with 7 stat tiles labeled "Price history", "Universe (as of
  date)", "Candidate universe", "Symbols", "Trading days", "Snapshot dates", and "Backfill gaps" — each
  showing a number or date range, never blank or the literal text "undefined"/"NaN"
- The "Start a fetch / backfill job" form is visible with "Start date", "End date", and "Job kind"
  fields and a "Start" button
- The "Job progress" panel and the "Run history" table are visible below the form
- No "Backend unavailable" red error card appears anywhere on the page
- No blank white screen and no console errors

---

### UT-02 — Backfill completion shows which aggregates were refreshed, live and after reload (happy-path, flagship)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Backend and frontend are running
- On the "Dataset coverage" panel, a "Backfill gaps" count ≥ 1 with a "Gap range: X → Y" line beneath
  the tiles naming a real gap date — if instead the panel reads "Every trading day with bars already has
  an immutable snapshot — no backfill gaps," use date `2026-05-15` (the date this iteration's own dev/QA
  handoffs used) and treat a "no new snapshots" outcome in step 7 as an acceptable pass (see note)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Read the gap date named on the "Gap range: ... → ..." line under the Dataset coverage tiles (or use
   `2026-05-15` per the precondition note)
3. In the "Start a fetch / backfill job" form, type that date into the "Start date" field (format
   `yyyy-MM-dd`)
4. Type the same date into the "End date" field
5. Confirm the "Job kind" dropdown already reads "Backfill snapshots" (its default) — leave it as is
6. Click the "Start" button
7. Watch the "Job progress" panel's status badge until it leaves the spinning "running" state (a few
   seconds to a couple of minutes depending on data volume)
8. Once finished, look directly beneath the "N calendar days · N already snapshotted · N non-trading"
   line in the "Job progress" panel
9. Reload the page (F5) and scroll down to the "Run history" table at the bottom
10. Find the row whose "Range" column matches the date you entered

**Expected Result:**
- Step 7: the status badge reads "ok" (or "no new snapshots" if that day already had a snapshot from a
  prior run — this is an acceptable, honestly-labeled zero-work outcome, not a failure)
- Step 8: a new line reading "Refreshed: " followed by a comma-separated, human-readable list (e.g.
  "Refreshed: coverage, market phase, membership timeline, research hot keys") is visible in small muted
  gray text directly under the breakdown line — it must NOT be missing, blank, or show raw
  underscore-joined identifiers like "market_phase"
- Step 10: the same run's row, in its "Snapshots" column, shows the IDENTICAL "Refreshed: ..." text
  beneath the snapshot count — proving the value was persisted to storage, not just a live-session-only
  artifact that disappears on reload

---

### UT-03 — Persisted run history still renders correctly with no job started this session (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/data` — `LastRunSummary` fallback card

**Preconditions:**
- At least one fetch/backfill/both run exists in Run history from a previous session (true after UT-02)
- Open a fresh browser tab/window (or a private/incognito window) so this browser session has not
  started any job of its own

**Steps:**
1. Open a new browser tab and navigate to `http://localhost:3255/data`
2. Do NOT click "Start" on the job form
3. Look at the "Job progress" panel

**Expected Result:**
- The panel does NOT show "No job has been started this session. Start a fetch or backfill job to watch
  its live progress and final summary here." — instead it shows the most recent persisted run's status
  badge and message text
- The "N snapshots · N trading days in range" line is visible
- The "N calendar days · N already snapshotted · N non-trading" breakdown line still renders exactly as
  it did before this iteration (same wording, same values) — this component's suppression logic changed
  internally this iteration (from "all 4 breakdown fields null" to "no breakdown AND no aggregates"), so
  this is the regression check that the change didn't break the pre-existing fallback view
- If that most recent persisted run predates this iteration or is a `fetch`/`expand` run (aggregates
  null), the "Refreshed: ..." line is completely ABSENT — no empty line, no dash, no "Refreshed: none"
  placeholder
- If that run is the backfill/both/rebuild run from UT-02, the "Refreshed: ..." line DOES appear here,
  identical to what was shown live

---

### UT-04 — Cold restart serves Dataset coverage instantly with unchanged numbers (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — "Dataset coverage" panel

**Preconditions:**
- At least one backfill has already completed (so a `coverage_snapshot` row exists for the current
  as-of)
- Terminal access to restart the backend via `scripts/start-backend.sh` (a documented, one-command
  script — no code changes needed)

**Steps:**
1. Navigate to `http://localhost:3255/data` and write down the 7 values shown in the "Dataset coverage"
   tiles (Price history range, Universe count, Candidate universe count, Symbols, Trading days, Snapshot
   dates, Backfill gaps)
2. In a terminal, stop the running backend process, then start it again via `scripts/start-backend.sh`
3. Watch the top-bar readiness badge until it reads "Ready" (not "Initializing…" or "Checking
   backend…")
4. The moment it reads "Ready," navigate to `http://localhost:3255/data` — this is the first `/data`
   load after the restart — and time how long the coverage tiles take to show numbers

**Expected Result:**
- The tiles populate in well under a second — not the multi-second delay (previously ~9–10 seconds) this
  same page used to take before this iteration
- All 7 values recorded in step 1 are IDENTICAL after the restart — same Price history range, same
  Universe/Candidate universe/Symbols/Trading days/Snapshot dates/Backfill gaps counts
- No spinner hangs indefinitely and no "Backend unavailable" error card appears

---

### UT-05 — Stepping the as-of switcher to an older date shows that date's real numbers, not a false-empty panel (regression, AG-3-critical)

**Type:** regression
**Priority:** P1 — elevated above the normal regression tier: this exact defect was introduced and then
caught and fixed within this same iteration (per the dev handoff and ui-impact-analyst report), and no
automated browser test exercised it before the fix. Treat this as a mandatory, deliberate manual check.

**Surface:** `/data` — "Dataset coverage" panel + the global as-of switcher (top bar, present on every
page)

**Preconditions:**
- At least 2 distinct snapshot dates exist (the "Snapshot dates" tile reads ≥ 2)
- Currently viewing "Latest" — the as-of badge in the top bar reads "Latest," not "Viewing as-of ...
  (historical)"

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Record the numbers in the "Dataset coverage" tiles while viewing "Latest"
3. In the top bar, click the as-of switcher's date button (it shows "Latest") to open the calendar
   popover
4. Select an older date from the calendar — one that is NOT the most recent date and that you know
   already has ingested data
5. Look at the "Dataset coverage" panel immediately after selecting that date
6. Click the as-of switcher's left-pointing step button (left of the date button, tooltip "Previous
   available date") once more to go one date further back, if another older date exists
7. Click the as-of switcher's date button again and select the newest/topmost entry in the calendar (or
   click the right-pointing step button, tooltip "Next available date," repeatedly) to return to
   "Latest"

**Expected Result:**
- Step 3: the top-bar badge changes to "Viewing as-of <date> (historical)" in amber
- Step 5: the coverage tiles show that OLDER date's genuine, non-zero Symbols / Universe / Snapshot-dates
  / Candidate-universe numbers. They must NOT all read "0," and the panel must NOT look like a fresh/
  empty database — this is the exact near-regression this iteration almost shipped
- Step 6: the further-back date also shows real numbers appropriate to that date (early dates may
  honestly show a smaller Universe count per the page's own "point-in-time universe" note, but never a
  false all-zero state for a date with real ingested data)
- Step 7: after returning to "Latest," the badge reads "Latest" again and the tiles instantly match
  exactly what was recorded in step 2

---

### UT-06 — Brand-new/never-ingested database shows an honest empty state, never a crash (error)

**Type:** error
**Priority:** P2
**Surface:** `/data` — "Dataset coverage" panel, zero-row state

**Preconditions:**
- Requires a disposable/throwaway database with zero rows — do NOT run this against any database
  holding data you want to keep. A developer/operator points the backend at a fresh, empty DB file
  before this test.
- Backend has just been started against that empty database and is still warming up

**Steps:**
1. Immediately after the backend starts against the empty database, navigate to
   `http://localhost:3255/data`
2. Observe the page while the top-bar readiness badge still reads "Initializing…"
3. Look at each of the 7 "Dataset coverage" tiles
4. Wait for the readiness badge to change from "Initializing…" to "Ready" (background warm-up
   completing; can take up to a couple of minutes)
5. Reload `http://localhost:3255/data`

**Expected Result:**
- Steps 1–3: the page loads normally — no blank white screen, no infinite spinner, no "Backend
  unavailable" red error card, no crash page
- Step 3: "Price history" reads "— → —"; "Universe (as of date)" reads `0`; "Symbols" reads `0`;
  "Trading days" reads `0`; "Snapshot dates" reads `0`; "Backfill gaps" reads `0` with the note text
  "Every trading day with bars already has an immutable snapshot — no backfill gaps." ("Candidate
  universe" is the one tile that may legitimately show a real non-zero number even here — it comes from
  static config, not the database, so it is not part of this honest-zero check.)
- Step 4: the readiness badge settles to "Ready"
- Step 5: the same tiles (Price history, Universe, Symbols, Trading days, Snapshot dates, Backfill gaps)
  now show real, non-zero/non-empty values — filled in automatically by the background warm-up, with no
  manual job run required

---

### UT-07 — "Refreshed" line never appears for fetch/expand runs or interrupted runs (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data` — "Job progress" panel and "Run history" table

**Preconditions:**
- Able to start a `fetch` job and watch it finish
- (Optional, needs developer assistance) An "interrupted" row exists in Run history from a simulated
  mid-job crash

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the "Start a fetch / backfill job" form, open the "Job kind" dropdown and select "Fetch EOD
   prices"
3. Type a start and end date, then click "Start"
4. Wait for the job to reach a finished state
5. Reload the page and find that run's row in "Run history"
6. If an "interrupted"-status row is available in Run history, inspect it too

**Expected Result:**
- Step 5: for the `fetch` run, NO "Refreshed: ..." line appears anywhere for it — not in the (now
  historical) Job progress view, not in its Run history row. The "N calendar days · ..." breakdown line
  is also absent for this run, consistent with pre-existing behavior for fetch/expand kinds
- Step 6: an "interrupted" row likewise shows no "Refreshed: ..." line — never a partial or fabricated
  list of aggregate names for a run whose finalize hook never completed

---

### UT-08 — "Refreshed" line reads clearly and sits logically in the run detail (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/data` — "Job progress" panel / Run history row

**Preconditions:**
- A completed backfill/both/rebuild run with a non-empty "Refreshed: ..." line is visible (from UT-02)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Locate a completed backfill run's "Refreshed: ..." line (Job progress panel or Run history table)
3. Read the line with no developer context or code access

**Expected Result:**
- The line reads "Refreshed: " followed by plain, space-separated words joined with commas (e.g.
  "coverage, market phase, membership timeline, research hot keys") — never raw identifiers with
  underscores such as "market_phase" or "research_hot_keys"
- The line sits directly beneath the existing "N calendar days · N already snapshotted · N non-trading"
  line, in the identical small muted-gray text style — no new color, badge, icon, or bold emphasis that
  would make it read as a warning
- A first-time reader can tell, without documentation, that this line names which background data this
  run refreshed

---

### UT-09 — Other reader pages still show correct data after this iteration's caching change (regression)

**Type:** regression
**Priority:** P3
**Surface:** `/` (Dashboard), `/scanner-runs`

**Preconditions:**
- At least one snapshot date with a completed scan exists (true after UT-02)

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Confirm the "Dashboard" heading is visible and the "Market Phase & Severity" card renders
3. Navigate to `http://localhost:3255/scanner-runs`
4. Confirm the "Scanner Runs" heading is visible and the run list renders

**Expected Result:**
- Step 2: the "Market Phase & Severity" card shows a phase badge (one of Expansion / Pullback /
  Correction / Bear / Recovery) and an "as of <date>" label — NOT the "Market phase unavailable" message
- Step 4: the list includes a row for every previously-ingested date, including any date backfilled in
  UT-02 — NOT the "No scanner runs yet" empty-state message, and no error screen
- Both pages load in normal time (a couple of seconds) with no visible difference from their behavior
  before this iteration — this iteration changed only WHEN these numbers get computed (proactively at
  ingest instead of on whichever request asks first), never WHAT they show

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/data` loads without errors | smoke | P1 | `/data` |
| UT-02 | Backfill completion shows Refreshed line, live + persisted | happy-path | P1 | `/data` |
| UT-03 | Persisted run history still renders correctly | regression | P2 | `/data` |
| UT-04 | Cold restart serves coverage instantly, unchanged numbers | happy-path | P1 | `/data` |
| UT-05 | As-of switcher shows real numbers for older dates | regression | P1 | `/data` + as-of switcher |
| UT-06 | Brand-new DB shows honest empty state, no crash | error | P2 | `/data` |
| UT-07 | Refreshed line absent for fetch/interrupted runs | validation | P2 | `/data` |
| UT-08 | Refreshed line is clear and well-placed | ux | P3 | `/data` |
| UT-09 | Other reader pages unaffected | regression | P3 | `/`, `/scanner-runs` |

**P1 tests (UT-01, UT-02, UT-04, UT-05) must all pass for browser QA verdict to be PASS.** UT-05 is
promoted to P1 despite being a "regression" test because it guards the phase's single highest-risk,
critical-anti-goal-adjacent (AG-3) defect — one that was actually introduced and fixed within this same
iteration.
