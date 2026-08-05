# Phase goal-ops-hardening-iter-49 — UI Test Plan

**Phase:** goal-ops-hardening-iter-49
**Date:** 2026-08-05
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3255
**Backend port (for the readiness badge / health-poll context only, never called directly by these
steps):** 8255

---

## Notes for the tester

- **Do not start a second data job while one is still finishing.** Run these test cases in order —
  UT-02/UT-03/UT-08 all share the same live backfill job and must not overlap with each other or with any
  other ingest.
- **Target date:** `2012-01-05` is the current `journey-scripts/J-05.json` golden target, confirmed
  untouched by this iteration's dev pass (the developer's own live drills used fresh throwaway DB copies
  and a separately-picked historical date, never the shared committed DB or this golden's target). If
  `2012-01-05` already appears as a row on `/scanner-runs` when you start, pick any other date in the
  window `2005-05-24` … `2019-02-25` that does NOT yet appear on `/scanner-runs`, and substitute it
  consistently across UT-02, UT-03, and UT-08.
- **This iteration's proof was measured on an otherwise-idle host against fresh throwaway copies of the
  real committed DB**, per TC-1's own stated precondition — not against the literal shared dev instance at
  port 8255/3255. Behavior should generalize (the dev handoff's own diagnosis attributes the historical
  13x variance to host contention, not DB growth, and an isolated re-measurement at the CURRENT DB size
  landed at the lower historical samples), but a concurrent heavy process (another test suite, another
  ingest job) running on this same host WHILE you test can genuinely slow the run down — if you suspect
  that, re-run on an idle host before treating a slow result as a regression.
- **Expect the full UT-02 wait to take roughly 17-18 minutes**, not seconds — this iteration's whole point
  is that the ENTIRE finalize tail (not just one fast step) now finishes reliably within the 20-minute
  budget. A materially longer wait (comfortably past 20 minutes) would be a genuine finding, not expected
  behavior.

---

## Test Cases

---

### UT-01 — `/data` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3255
- No login required

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error message
- The heading "Data Manager" is visible
- The "Start a fetch / backfill job" panel is visible, with a "Start date" field
  (`data-testid="job-start-date"`), an "End date" field (`data-testid="job-end-date"`), and a "Job kind"
  dropdown defaulted to "Backfill snapshots"
- The readiness badge (`data-testid="readiness-badge"`) in the page header shows `data-state="ready"`
  ("Ready", green)
- No console errors

---

### UT-02 — Historical-gap backfill reaches a terminal status for its ENTIRE finalize tail (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- UT-01 passed
- No other data job is currently running (the "Job progress" panel does not show a live job, or shows a
  prior job already at a terminal status)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the field with `data-testid="job-start-date"`, type `2012-01-05`
3. In the field with `data-testid="job-end-date"`, type `2012-01-05`
4. Confirm the "Job kind" dropdown reads "Backfill snapshots" (the default — do not change it)
5. Click the "Start" button
6. Immediately after clicking, observe the "Job progress" panel

**Expected Result (immediately after step 5):**
- The badge with `data-testid="job-status"` shows a spinning icon and the text "running"
- Below it, "Snapshots backfilled" shows `0/1 dates` with an empty progress bar

**Expected Result (within ~30 seconds):**
- The line with `data-testid="aggregates-refreshed"` appears, starting with "Refreshed:" and mentioning
  "membership timeline" — this is iter-48's fix, still in place, and confirms the run is proceeding
  normally before this iteration's own two bounded phases begin.

**Expected Result (within ~17-18 minutes, and comfortably before 20 minutes):**
- The badge with `data-testid="job-status"` stops showing the spinner and reads one of: `ok`,
  `no new snapshots`, `partial`, `failed at backfill`, or `failed` (any of these counts as "terminal" — the
  point is it is no longer `running`). This is THIS iteration's own proof: on 3 independent live runs the
  developer measured 1,012.71s / 1,048.22s / 1,044.77s (≈16m53s–17m28s) end to end.
- "Snapshots backfilled" shows `1/1 dates` with a full progress bar (or `0/1` with the `zero-work-note`
  panel if the date somehow already had a snapshot — see UT-08).

**Fail condition:** the badge is STILL showing the spinning "running" state after 20 full minutes on an
otherwise-idle host — unlike iter-48 (where this was an accepted, disclosed gap), this iteration's whole
purpose is closing that gap, so a run that genuinely exceeds the 1,200s budget on an idle host is a real
regression finding, not an expected caveat.

---

### UT-03 — Backfilled historical date renders its stored snapshot on Scanner Runs (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/scanner-runs`, `/scanner-runs/[runId]`

**Preconditions:**
- UT-02's job has reached a terminal status (`ok` or `no new snapshots`)

**Steps:**
1. Navigate to `http://localhost:3255/scanner-runs`
2. Look at the "As of" column of the run history table
3. Click the date link reading `2012-01-05`

**Expected Result (step 2):**
- A table row exists whose "As of" cell shows `2012-01-05` as a clickable, accent-colored link

**Expected Result (step 3):**
- The page navigates to `http://localhost:3255/scanner-runs/<runId>`
- Text containing "as of 2012-01-05" is visible (page heading / immutable-snapshot banner)
- A leaderboard table below renders at least one stock row (not a loading skeleton, not a "not found" state)

---

### UT-04 — Job form still blocks Start with an incomplete date range (validation, pre-existing behavior)

**Type:** validation
**Priority:** P3
**Surface:** `/data`

**Preconditions:**
- Navigate to `/data` with no job currently running

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Clear the field with `data-testid="job-start-date"` if it has a value (leave it empty)
3. Type `2012-01-06` into the field with `data-testid="job-end-date"`
4. Do NOT type anything into the start-date field
5. Observe the "Start" button

**Expected Result:**
- The "Start" button remains disabled (greyed out / not clickable) — the form is blocked until BOTH date
  fields hold a valid `yyyy-MM-dd` value
- No job starts, no new "Job progress" panel appears
- This is pre-existing behavior, untouched by this iteration's diff (which changed no frontend file and no
  form-validation logic) — a regression here would indicate an unrelated break, not this iteration's own
  defect

---

### UT-05 — Backend stays responsive while a historical-gap backfill finalizes (error/resilience)

**Type:** error
**Priority:** P1
**Surface:** `/data` (readiness badge), any page (the badge is global via `layout.tsx`)

**Preconditions:**
- UT-02's job is `running` — start observing as early as possible after the job accepts (within the first
  minute) for the strongest signal, since the one known gap (below) is early in the run

**Steps:**
1. As soon as UT-02's job shows `running`, look at the readiness badge (`data-testid="readiness-badge"`)
   in the page header
2. Note its `data-state` attribute / label
3. Check again every 15-20 seconds for the first 2 minutes of the run
4. After that, check every minute or two for the remainder of the run (through UT-02's full ~17-18 minute
   duration)

**Expected Result:**
- The readiness badge shows `data-state="ready"` ("Ready", green) at nearly every observation
- **Known, disclosed caveat (do not treat this alone as a NEW regression):** roughly 40-45 seconds into the
  run, 2 of the developer's 3 automated live runs logged exactly one ~10-second `GET /api/health` timeout
  (before either of this iteration's own two bounded phases even starts). If you happen to check the badge
  in that exact narrow window, you MAY see it briefly flip to `data-state="unavailable"` ("Backend
  unavailable", red) before recovering on its own within about 10 seconds. This is a real, newly-surfaced,
  but already out-of-scope gap this iteration explicitly did not fix (see the dev handoff's Known Issues).
- **Genuine failure conditions (these WOULD be new problems):** the badge stays on `data-state=
  "unavailable"` for longer than roughly 15 seconds at a stretch, OR it flips to `unavailable` at any point
  OTHER than that early ~40-45 second window, OR the page itself (nav, other panels) stops being
  interactive at any point — clicking to another page (e.g. `/scanner-runs`) and back to `/data` should
  work normally throughout.

---

### UT-06 — Evidence page's drawdown-expectations panel renders correctly after the speed fix (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/evidence`

**Preconditions:**
- None (independent of the backfill in UT-02/UT-03)

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the page to load
3. Find a claim card that shows a badge with `data-testid="evidence-claim-regime"` (a regime-conditioned
   claim, e.g. text "Regime: Risk-on" or similar)
4. Scroll to that card's "Historical drawdown & dry-spell expectations" section

**Expected Result:**
- The page loads without an error card or blank screen
- The section's table (`data-testid="evidence-expectations-table"`) renders at least one row
  (`data-testid="evidence-expectations-phase-row"`) with real percentage/numeric figures — not the
  `data-testid="evidence-expectations-unavailable"` fallback text
- No browser console errors mentioning a 500 response from `/api/evidence`

---

### UT-07 — Factor Lab still loads and its existing decile drill-down link still works (regression)

**Type:** regression
**Priority:** P3
**Surface:** `/research/factor-lab`, `/research/samples`

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the page to load
3. Find any factor's decile breakdown and click its sample-count "N=" link for one decile (this exercises
   the same `research.py` module this iteration's column-projection change touched, confirming the
   drill-down path still works)

**Expected Result:**
- `/research/factor-lab` loads without an error card
- Clicking the "N=" link navigates to `http://localhost:3255/research/samples?...` and the page shows
  `data-testid="cohort-summary"` with a `data-testid="samples-total"` figure and a member-observation table
  below it (ticker, snapshot date, factor value, forward return columns)

---

### UT-08 — A zero-work re-run reads honestly, never as a fabricated success (UX)

**Type:** ux
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- UT-02's backfill for `2012-01-05` has already completed with `snapshots_created >= 1`

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Repeat UT-02 steps 2–5 with the SAME date, `2012-01-05`, for both start and end date
3. Wait for the job to reach a terminal status

**Expected Result:**
- The badge with `data-testid="job-status"` reads `no new snapshots` (NOT `ok`) — it must render visually
  distinct from a productive success (a neutral/default badge color, not green)
- The panel with `data-testid="zero-work-note"` appears with text beginning "Zero-work outcome — every
  requested trading day already had a snapshot…"
- "Snapshots backfilled" shows `0/1 dates` (or `1/1` with `0` new snapshots depending on exact wording —
  the key check is `snapshots_created` reads `0`, not a nonzero fabricated value)
- This re-run should also finish quickly (well under 20 minutes), since a zero-work run typically skips the
  heavy per-date aggregate work this iteration's fix targets

---

### UT-09 — Backtest page renders forward-aggregate numbers correctly after the accumulator change (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/backtest`

**Preconditions:**
- None (independent of the backfill in UT-02/UT-03; exercises already-cached data)

**Steps:**
1. Navigate to `http://localhost:3255/backtest`
2. Wait for the page to load
3. Select or confirm a horizon that already has cached aggregate data (e.g. the default/20-day horizon)

**Expected Result:**
- The page loads without an error card or blank screen
- The aggregate stats table/panel renders real numeric values (hit rate, mean/median return, sample count,
  etc.) — not an empty state or a value that looks obviously wrong (e.g. all zeros, `NaN`, or `—` where a
  number is expected for a horizon known to have data)
- No browser console errors mentioning a 500 response from `/api/backtest`

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/data` loads | smoke | P1 | `/data` |
| UT-02 | Historical-gap backfill reaches terminal status for its ENTIRE finalize tail | happy-path | P1 | `/data` |
| UT-03 | Backfilled date renders on Scanner Runs | happy-path | P1 | `/scanner-runs`, `/scanner-runs/[runId]` |
| UT-04 | Job form blocks incomplete date range | validation | P3 | `/data` |
| UT-05 | Backend stays responsive during finalize tail (known early-window caveat) | error | P1 | `/data` (readiness badge) |
| UT-06 | Evidence drawdown-expectations panel still renders correctly | regression | P2 | `/evidence` |
| UT-07 | Factor Lab decile drill-down still works | regression | P3 | `/research/factor-lab`, `/research/samples` |
| UT-08 | Zero-work re-run reads honestly | ux | P2 | `/data` |
| UT-09 | Backtest forward-aggregate numbers still render correctly | regression | P2 | `/backtest` |

**P1 tests (UT-01, UT-02, UT-03, UT-05) must all pass for browser QA verdict to be PASS.** UT-05's known
early-window caveat (a brief, self-recovering health-check blip roughly 40-45 seconds into the run) does
NOT itself fail the P1 gate — it is an explicitly disclosed, out-of-scope gap this iteration did not fix.
A badge that stays down longer, or flips outside that window, DOES fail UT-05. UT-02's fail condition (job
still `running` past 20 minutes on an idle host) is a genuine regression this time — unlike iter-48, this
iteration's entire purpose is guaranteeing the WHOLE job's terminal status within budget, so there is no
"known gap" exception left for UT-02 itself.
