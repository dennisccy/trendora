# Phase goal-ops-hardening-iter-48 — UI Test Plan

**Phase:** goal-ops-hardening-iter-48
**Date:** 2026-08-04
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3255
**Backend port (for the readiness badge / health-poll context only, never called directly by these
steps):** 8255

---

## Notes for the tester

- **Do not start a second data job while one is still finishing.** Run these test cases in order —
  UT-02/UT-03/UT-08 all share the same live backfill job and must not overlap with each other or with any
  other ingest.
- **Target date:** `2012-06-15` is J-05's own golden target (rotated by this iteration to be unconsumed).
  If `2012-06-15` already appears as a row on `/scanner-runs` when you start (e.g. a prior test pass already
  consumed it), pick any other date in the window `2005-05-24` … `2019-02-25` that does NOT yet appear on
  `/scanner-runs`, and substitute it consistently across UT-02, UT-03, and UT-08.
- **A historical-gap backfill's specific fixed step resolves in seconds, but the job as a whole is not
  guaranteed to finish within 20 minutes on every run** (a separate, out-of-scope step,
  `drawdown_expectations_warm`, can still run long — see the dev handoff's Known Issues). UT-02 sets
  realistic wait expectations for both the fixed step and the honest caveat on the overall job.

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

### UT-02 — Historical-gap backfill reaches a terminal status for its own fixed step (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- UT-01 passed
- No other data job is currently running (the "Job progress" panel does not show a live job, or shows a
  prior job already at a terminal status)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the field with `data-testid="job-start-date"`, type `2012-06-15`
3. In the field with `data-testid="job-end-date"`, type `2012-06-15`
4. Confirm the "Job kind" dropdown reads "Backfill snapshots" (the default — do not change it)
5. Click the "Start" button
6. Immediately after clicking, observe the "Job progress" panel

**Expected Result (immediately after step 5):**
- The badge with `data-testid="job-status"` shows a spinning icon and the text "running"
- Below it, "Snapshots backfilled" shows `0/1 dates` with an empty progress bar

**Expected Result (within ~30 seconds):**
- The line with `data-testid="aggregates-refreshed"` appears, starting with "Refreshed:" and mentioning
  "membership timeline" (word-boundary match; underscores render as spaces, e.g.
  "membership timeline refresh") — this is the specific step this iteration fixed, and it must NOT take
  minutes.

**Expected Result (within ~5 minutes, typical run):**
- The badge with `data-testid="job-status"` stops showing the spinner and reads one of: `ok`,
  `no new snapshots`, `partial`, `failed at backfill`, or `failed` (any of these counts as "terminal" — the
  point is it is no longer `running`).
- "Snapshots backfilled" shows `1/1 dates` with a full progress bar (or `0/1` with the `zero-work-note`
  panel if the date somehow already had a snapshot — see UT-08).

**Honest caveat (do not fail the test solely on this):** if the badge is STILL showing the spinning
"running" state after 20 minutes, this is the known, disclosed gap from the dev handoff (the unrelated
`drawdown_expectations_warm` step can still run long) — record it as a note, not a UT-02 failure, and
proceed to UT-05 to confirm the app itself stayed responsive throughout. Do not start a second job while
waiting.

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
3. Click the date link reading `2012-06-15`

**Expected Result (step 2):**
- A table row exists whose "As of" cell shows `2012-06-15` as a clickable, accent-colored link

**Expected Result (step 3):**
- The page navigates to `http://localhost:3255/scanner-runs/<runId>`
- The text "Immutable snapshot — as of 2012-06-15" is visible
- The heading "Market Regime · as of 2012-06-15" is visible
- A leaderboard table below renders at least one stock row (not a loading skeleton, not a "not found" state)

---

### UT-04 — Job form still blocks Start with an incomplete date range (validation, pre-existing behavior)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Navigate to `/data` with no job currently running

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Clear the field with `data-testid="job-start-date"` if it has a value (leave it empty)
3. Type `2012-06-16` into the field with `data-testid="job-end-date"`
4. Do NOT type anything into the start-date field
5. Observe the "Start" button

**Expected Result:**
- The "Start" button remains disabled (greyed out / not clickable) — the form is blocked until BOTH date
  fields hold a valid `yyyy-MM-dd` value
- No job starts, no "Job progress" panel appears for a new job
- This is pre-existing behavior (untouched by this iteration's diff) — a regression here would indicate an
  unrelated break, not this iteration's own defect

---

### UT-05 — Backend stays responsive while a historical-gap backfill finalizes (error/resilience)

**Type:** error
**Priority:** P1
**Surface:** `/data` (readiness badge), any page (the badge is global via `layout.tsx`)

**Preconditions:**
- UT-02's job is still `running` (or has just gone terminal — start this test as early as possible during
  UT-02's wait window for the strongest signal)

**Steps:**
1. While still on `http://localhost:3255/data` with the UT-02 job visible, look at the readiness badge
   (`data-testid="readiness-badge"`) in the page header
2. Note its `data-state` attribute / label
3. Wait 30 seconds, then look again
4. Repeat step 3 two or three more times over the next few minutes while the job is still `running`

**Expected Result:**
- The readiness badge shows `data-state="ready"` ("Ready", green) at every observation — it must NEVER show
  `data-state="unavailable"` ("Backend unavailable", red/danger) while the backfill job is finalizing
- The page itself (nav, other panels) remains interactive throughout — clicking to another page (e.g.
  `/scanner-runs`) and back to `/data` works normally at any point during the wait

---

### UT-06 — Evidence page's drawdown-expectations panel renders correctly after the memory bound (regression)

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
- No browser console errors mentioning `MemoryError` or a 500 response from `/api/evidence`

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
   the UNCHANGED `decile` branch, confirming this iteration's `total`/`regime` changes in the same file
   didn't disturb it)

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
- UT-02's backfill for `2012-06-15` has already completed with `snapshots_created >= 1`

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Repeat UT-02 steps 2–5 with the SAME date, `2012-06-15`, for both start and end date
3. Wait for the job to reach a terminal status

**Expected Result:**
- The badge with `data-testid="job-status"` reads `no new snapshots` (NOT `ok`) — it must render visually
  distinct from a productive success (a neutral/default badge color, not green)
- The panel with `data-testid="zero-work-note"` appears with text beginning "Zero-work outcome — every
  requested trading day already had a snapshot…"
- "Snapshots backfilled" shows `0/1 dates` (or `1/1` with `0` new snapshots depending on exact wording —
  the key check is `snapshots_created` reads `0`, not a nonzero fabricated value)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/data` loads | smoke | P1 | `/data` |
| UT-02 | Historical-gap backfill reaches terminal status for its fixed step | happy-path | P1 | `/data` |
| UT-03 | Backfilled date renders on Scanner Runs | happy-path | P1 | `/scanner-runs`, `/scanner-runs/[runId]` |
| UT-04 | Job form blocks incomplete date range | validation | P2 | `/data` |
| UT-05 | Backend stays responsive during finalize tail | error | P1 | `/data` (readiness badge) |
| UT-06 | Evidence drawdown-expectations panel still renders correctly | regression | P2 | `/evidence` |
| UT-07 | Factor Lab decile drill-down still works | regression | P3 | `/research/factor-lab`, `/research/samples` |
| UT-08 | Zero-work re-run reads honestly | ux | P2 | `/data` |

**P1 tests (UT-01, UT-02, UT-03, UT-05) must all pass for browser QA verdict to be PASS.** UT-02's honest
caveat (overall job duration not bounded) does not itself fail the P1 gate as long as UT-05 confirms the
app stayed responsive — that is exactly what the dev handoff discloses and what TC-4 (not TC-1's literal
20-minute bound) actually guarantees this iteration.
