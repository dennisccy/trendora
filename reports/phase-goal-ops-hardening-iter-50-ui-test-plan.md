# Phase goal-ops-hardening-iter-50 — UI Test Plan

**Phase:** goal-ops-hardening-iter-50
**Date:** 2026-08-05
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3255
**Backend port (health poll / restart context; never called directly except where a step says so):** 8255

---

## Notes for the tester

- **Golden target date:** `2012-01-04` is the current `journey-scripts/J-05.json` golden target
  (`runs/goal-session-ops-hardening/journey-scripts/J-05.json`, step 2). Before running UT-02/UT-03, check
  `/scanner-runs` — if `2012-01-04` already appears as a row, pick any OTHER date in the window
  `2005-05-24` … `2019-02-25` not yet on `/scanner-runs`, and substitute it consistently across UT-02 and
  UT-03 (they share the SAME job).
- **UT-02/UT-03 share one live backfill job — do not start a second data job while it is running.** Do not
  overlap these with any other ingest.
- **Expect the full UT-02/UT-03 wait to take roughly 15-20 minutes**, not seconds — this iteration's whole
  point is that the entire finalize tail (forward-aggregate warm + drawdown-expectations warm) now completes
  reliably within the 20-minute budget, and TC-1's specific claim is that a `/research/factor-lab` view
  survives being loaded WHILE that tail is still running. A materially longer wait (comfortably past 20
  minutes) is itself a finding worth reporting.
- **UT-08 and UT-09 require restarting the backend** (with an environment variable, and a cold restart,
  respectively) — these are advanced/optional checks for a tester with shell access to the backend process,
  not part of the fast 5-minute walkthrough (`what-to-click.md`).
- This iteration touched no frontend file. Every test below is either proving the backend no longer crashes
  under a scenario that used to crash it, or confirming an already-existing page still renders correctly.

---

## Test Cases

---

### UT-01 — `/research/factor-lab` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and warm (readiness badge shows "Ready")
- No login required

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error card
- The heading "Research — Factor Lab" is visible
- The all-factors table renders at least one row with a real (non-placeholder) rank-IC value and, for at
  least one horizon column, a non-"NA" forward-return figure
- No browser console errors mentioning a 500 response from `/api/research/factor-lab`
- No console errors

---

### UT-02 — Historical-day backfill (J-05's defining case) reaches a terminal status (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`, `/scanner-runs`

**Preconditions:**
- UT-01 passed
- No other data job is currently running

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the field with `data-testid="job-start-date"`, type `2012-01-04`
3. In the field with `data-testid="job-end-date"`, type `2012-01-04`
4. Confirm the "Job kind" dropdown reads "Backfill snapshots" (the default — do not change it)
5. Click the "Start" button
6. Observe the "Job progress" panel

**Expected Result (immediately after step 5):**
- The badge with `data-testid="job-status"` shows a spinning icon and the text "running"

**Expected Result (within ~30 seconds):**
- The line with `data-testid="aggregates-refreshed"` appears, starting with "Refreshed:" and mentioning
  "membership timeline"

**Expected Result (within ~15-20 minutes):**
- The badge with `data-testid="job-status"` stops spinning and reads a terminal value: `ok`,
  `no new snapshots`, `partial`, `failed at backfill`, or `failed` (any of these is "terminal" — the point
  is it is no longer `running`)
- Navigate to `http://localhost:3255/scanner-runs` and confirm a row with "As of" text `2012-01-04` appears
  as a clickable link; click it and confirm the detail page shows text containing "as of 2012-01-04" with a
  populated leaderboard table below it

**Fail condition:** the badge is still showing "running" after 20 full minutes on an otherwise-idle host —
this iteration's own purpose is closing exactly this gap, so a genuine timeout here is a real regression
finding.

---

### UT-03 — Factor Lab survives a concurrent finalize-tail warm; backend stays responsive (error / resilience — TC-1)

**Type:** error
**Priority:** P1
**Surface:** `/research/factor-lab`, `/data` (readiness badge)

**Preconditions:**
- UT-02's job is `running` and has already shown the "Refreshed: … membership timeline" line (i.e. it has
  moved past the fast first stage into the slow finalize-tail phases this iteration bounds)

**Steps:**
1. While UT-02's job is still `running`, open a SECOND browser tab
2. In the new tab, navigate to `http://localhost:3255/research/factor-lab`
3. Wait for the page to finish loading
4. Switch back to the first tab (still on `/data`) and look at the readiness badge in the page header
5. Repeat steps 2-4 two or three more times over the remaining wait, at a few-minutes' spacing

**Expected Result:**
- Each time, `/research/factor-lab` finishes loading with a populated all-factors table (same as UT-01) —
  it never hangs indefinitely, crashes to a blank page, or shows "Backend unavailable"
- The readiness badge (`data-testid="readiness-badge"`) shows `data-state="ready"` at every check in the
  first tab, both while the Factor Lab tab is loading and afterward
- UT-02's own job in the first tab continues progressing toward its terminal status unaffected — opening
  Factor Lab does not stall or restart it

**Fail condition:** `/research/factor-lab` fails to load, the tab hangs indefinitely, OR the readiness
badge in the OTHER tab flips to `data-state="unavailable"` and stays there — this is the exact scenario
that killed the backend for 12m45s in the prior round; a recurrence here is this iteration's single most
important finding.

---

### UT-04 — Job form still blocks Start with an incomplete date range (validation, pre-existing behavior)

**Type:** validation
**Priority:** P3
**Surface:** `/data`

**Preconditions:**
- Navigate to `/data` with no job currently running (or wait until UT-02/UT-03's job has reached a
  terminal status)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Leave the field with `data-testid="job-start-date"` empty
3. Type `2012-01-06` into the field with `data-testid="job-end-date"`
4. Observe the "Start" button

**Expected Result:**
- The "Start" button remains disabled (greyed out) — the form is blocked until BOTH date fields hold a
  valid `yyyy-MM-dd` value
- No job starts
- This is pre-existing behavior, untouched by this iteration's diff (which changed no frontend file); a
  regression here indicates an unrelated break, not this iteration's own defect

---

### UT-05 — Evidence page's drawdown-expectations panel still renders correctly (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/evidence`

**Preconditions:** None (independent of UT-02/UT-03's backfill)

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the page to load
3. Find a claim card that shows a badge with `data-testid="evidence-claim-regime"`
4. Scroll to that card's "Historical drawdown & dry-spell expectations" section

**Expected Result:**
- The page loads without an error card or blank screen
- The section's table (`data-testid="evidence-expectations-table"`) renders at least one row with real
  percentage/numeric figures — not the `data-testid="evidence-expectations-unavailable"` fallback
- No browser console errors mentioning a 500 response from `/api/evidence`

---

### UT-06 — Backtest page still renders forward-test scorecard numbers correctly (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/backtest`

**Preconditions:** None (independent of UT-02/UT-03's backfill; exercises already-cached data)

**Steps:**
1. Navigate to `http://localhost:3255/backtest`
2. Wait for the page to load
3. Under "As-of scan summary," confirm a horizon is selected (the default selector)

**Expected Result:**
- The page loads without an error card or blank screen
- The scorecard panel renders real numeric values (hit rate, mean/median return, sample count) for the
  selected horizon — not an empty state, not all zeros/`NaN`, not `—` where a number is expected for a
  horizon known to have data
- The "Leadership cohorts" section below renders populated ticker lists
- No browser console errors mentioning a 500 response from `/api/backtest`

---

### UT-07 — Data page's background-compute panel still renders correctly (regression — required-still-passing J-09)

**Type:** regression
**Priority:** P2
**Surface:** `/data`

**Preconditions:** None

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Scroll to the panel with `data-testid="background-compute-panel"`

**Expected Result:**
- The panel renders EITHER `data-testid="background-compute-idle"` (text "No background compute running…")
  OR, if a background-compute window happens to be active, `data-testid="background-compute-active-row"`
  with a real as-of date and elapsed time
- The panel never renders blank, and never throws a visible JS error boundary
- This confirms this iteration's warm-in-progress guard (a DIFFERENT mechanism from J-09's background-compute
  dispatch) did not disturb this unrelated existing disclosure

---

### UT-08 — A degraded Factor Lab response reuses the "empty" state, not a distinct message (UX finding, advanced/optional)

**Type:** ux
**Priority:** P3
**Surface:** `/research/factor-lab`

**Preconditions:**
- Requires shell access to restart the backend with an environment variable set — skip this test if you
  only have browser access
- Stop the currently-running backend

**Steps:**
1. Restart the backend via `scripts/start-backend.sh` with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=factor_lab_all`
   set in its environment (this is an existing test-only switch — it deterministically simulates a
   memory-pressure event on every `compute_factor_lab_all` call; it has no effect unless explicitly set)
2. Navigate to `http://localhost:3255/research/factor-lab`
3. Observe what the page shows
4. Restart the backend again WITHOUT that environment variable set
5. Reload `http://localhost:3255/research/factor-lab`

**Expected Result (step 3):**
- The page shows the "No forward-tested factors" empty state (icon + the text "No stored snapshot has a
  factor value with a realized forward return at any horizon…") — NOT a crash, NOT a blank screen, NOT a
  raw error stack
- **This is the finding, not a pass/fail bug:** this message is misleading in this exact scenario — real
  data exists; the true cause is the simulated memory-pressure degrade, not an empty store. Confirm the
  page gives no other indication (no distinct banner, no "temporarily unavailable" wording) that this is a
  transient degrade rather than genuinely missing data.

**Expected Result (step 5, confirms the reuse claim):**
- The SAME page now renders the SAME populated all-factors table as UT-01 — proving the empty state in
  step 3 was the fault injection's degrade path being reused, not a genuine data gap.

---

### UT-09 — Cold restart: `/data` renders from the persisted payload within budget, no whole-table prefill (regression — TC-11, advanced)

**Type:** regression
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- UT-02's backfill has already completed with a terminal status
- Requires shell access to restart the backend

**Steps:**
1. Stop the backend, then restart it via `scripts/start-backend.sh`
2. As soon as the frontend is reachable, navigate to `http://localhost:3255/data`
3. Time how long the coverage summary panel (universe count, candidate universe count) takes to populate
   with real numbers after the page loads

**Expected Result:**
- Coverage renders from the persisted payload within its committed budget (a few seconds on a warm restart
  — not a multi-minute wait)
- The backend's own startup log shows no full `daily_prices` table scan/prefill (if you have log access,
  confirm no line describing a whole-table read of `daily_prices` appears during startup)
- The `2012-01-04` (or substituted date) row from UT-02 still appears on `/scanner-runs` after the restart

---

### UT-10 — `/research/factor-lab` page-load timing is measured (performance — TC-12/J-06)

**Type:** ux
**Priority:** P2
**Surface:** `/research/factor-lab`

**Preconditions:**
- Backend and frontend running via their PRODUCTION launch scripts (`scripts/start-backend.sh` /
  `scripts/start-frontend.sh` — never `dev.sh`), backend warm (not mid-restart)
- Open your browser's DevTools Network tab before navigating

**Steps:**
1. Open DevTools (F12), go to the Network tab, and clear it
2. Navigate to `http://localhost:3255/research/factor-lab`
3. Wait until the all-factors table finishes rendering (same "done" condition as UT-01)
4. In the Network tab, find the `factor-lab?all=true` request and note its duration; note the wall-clock
   time from navigation start to the table's rows appearing (time-to-interactive)

**Expected Result:**
- **No committed budget exists yet for this specific page as of this iteration** (the dev handoff's Known
  Issues section confirms TC-12 has not been live-measured yet) — this test's purpose is to produce the
  FIRST live measurement and record it in `reports/perf-budgets.md`, not to pass/fail against a pre-set
  number
- As a sanity check: on a WARM backend (the underlying data already cached from a prior request), the page
  should feel responsive — low single-digit seconds, not the multi-minute cold-compute range this same
  endpoint can take on a genuine cache MISS (documented as ~2-4 minutes in the dev handoff's TC-2 live
  drill). If the warm load takes noticeably longer than a few seconds, flag it as a finding rather than
  assuming it is expected.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Factor Lab loads | smoke | P1 | `/research/factor-lab` |
| UT-02 | Historical-day backfill reaches terminal status | happy-path | P1 | `/data`, `/scanner-runs` |
| UT-03 | Factor Lab survives a concurrent finalize-tail warm | error | P1 | `/research/factor-lab`, `/data` |
| UT-04 | Job form blocks incomplete date range | validation | P3 | `/data` |
| UT-05 | Evidence drawdown-expectations panel still renders | regression | P2 | `/evidence` |
| UT-06 | Backtest scorecard still renders | regression | P2 | `/backtest` |
| UT-07 | Background-compute panel still renders | regression | P2 | `/data` |
| UT-08 | Degraded response reuses the empty-state (UX finding) | ux | P3 | `/research/factor-lab` |
| UT-09 | Cold restart renders coverage within budget | regression | P2 | `/data` |
| UT-10 | Factor Lab page-load timing measured | ux | P2 | `/research/factor-lab` |

**P1 tests (UT-01, UT-02, UT-03) must all pass for browser QA verdict to be PASS.** UT-03 is this
iteration's single most important test — it directly exercises the exact concurrent-load scenario
(`TC-1`) that killed the backend for 12m45s in the prior round. UT-08 and UT-09 require backend restart
access and are advanced/optional for a browser-only tester; they should still be attempted by browser-qa
when shell access is available, since UT-08 documents a genuine (if minor) UX finding and UT-09 proves
TC-11 directly.
