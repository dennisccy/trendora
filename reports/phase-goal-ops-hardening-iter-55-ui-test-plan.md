# Phase goal-ops-hardening-iter-55 — UI Test Plan

**Phase:** goal-ops-hardening-iter-55
**Date:** 2026-08-10
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3255

---

## Scope note

This iteration shipped zero `apps/frontend/` file changes (`Frontend Present: no`, independently
re-verified: empty `git diff --stat` / `git status --porcelain` for `apps/frontend/`). Every test below
exercises an *existing, code-unchanged* UI surface whose underlying backend correctness (the `/data`
"Refreshed: …" line) or reliability (the global health badge/banner during `forward_aggregates_warm`) was
targeted this iteration. Read `reports/phase-goal-ops-hardening-iter-55-user-visible-changes.md` first —
the reliability target (TC-5) was **NOT met** this iteration (regressed from 6 to 11 non-answers,
`reports/perf-budgets.md` Addendum 19); UT-04 below is written to record that honestly, not to expect a
clean pass.

---

## Test Cases

---

### UT-01 — `/data` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and has reached `data-state="ready"` on the readiness badge (no login required)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or an unhandled error boundary
- The "Start a fetch / backfill job" panel is visible with a heading of that exact text
- The readiness pill in the top-right of the header (`data-testid="readiness-badge"`) reads `data-state="ready"`
- No browser console errors

---

### UT-02 — A completed backfill job's "Refreshed: …" line lists "forward aggregates" on the happy path (happy-path / correctness regression check)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Navigate to `http://localhost:3255/data`; the "Start date" and "End date" fields are pre-filled from the
  first detected coverage gap

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Leave the pre-filled "Start date" (`data-testid="job-start-date"`) and "End date"
   (`data-testid="job-end-date"`) values as-is
3. Confirm "Job kind" shows "Backfill snapshots" (the default option)
4. Click the "Start" button (play-icon button at the end of the form row)
5. Wait for the "Job progress" card's status badge (`data-testid="job-status"`) to leave the "running…"
   spinner state and reach a terminal label (e.g. "ok") — this can take several minutes for a job that
   triggers a full forward-aggregate warm; poll every 15-30s rather than a fixed short wait

**Expected Result:**
- `data-testid="job-status"` reaches a terminal, non-spinner label
- The "Refreshed: …" line (`data-testid="aggregates-refreshed"`) appears below the job status and its text
  includes "forward aggregates" among the comma-separated categories (e.g. "coverage, market phase,
  forward aggregates, latest snapshot, …")
- No category is missing that a pre-iter-55 run of the same job would have shown — this proves the
  honest-status fix did not regress the normal (all-horizons-complete) path

---

### UT-03 — Job form stays blocked with an incomplete/invalid date, unaffected by this iteration (validation regression check)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Navigate to `http://localhost:3255/data`

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Clear the "End date" field (`data-testid="job-end-date"`) entirely, leaving "Start date" filled
3. Observe the "Start" button

**Expected Result:**
- The "Start" button is disabled (greyed out, `disabled:opacity-50` styling, not clickable) — the form was
  never touched this iteration and must still block submission with an incomplete date pair
- No job is created and no `POST /api/data/jobs` request fires

---

### UT-04 — Health badge/banner stability while a forward-aggregate warm runs (error / reliability observation — this iteration's own target, disclosed as NOT met)

**Type:** error
**Priority:** P1
**Surface:** global header (`HealthBadge`) + sub-header (`PreflightBanner`), observed from `/data`

**Preconditions:**
- A backfill/rebuild job is about to run that will trigger a full forward-aggregate warm (a job spanning
  at least one previously-unsnapshotted trading day with all five configured horizons computing:
  `[1, 5, 10, 20, 60]`)

**Steps:**
1. Navigate to `http://localhost:3255/data` and start a backfill job per UT-02's steps 1-4
2. From the moment the job's status badge (`data-testid="job-status"`) shows "running…", keep the tab open
   and continuously observe the readiness pill (`data-testid="readiness-badge"`, top-right of header) and
   the preflight banner (`data-testid="preflight-banner"`, directly below the header) for the full duration
   of the job, paying particular attention to the second half of the run (this iteration's own evidence
   points to the horizon=10 sub-phase of the warm)
3. Record every timestamp where the pill's `data-state` attribute flips away from `"ready"` (e.g. to
   `"unavailable"`) or the banner's `data-verdict` flips to `"NO-GO"`, and how long each flip lasts before
   recovering

**Expected Result — recorded honestly, not graded as a hard pass/fail against zero:**
- This iteration's own live drill (Addendum 19) measured **11** connection-level non-answers this run
  (up from the iter-54 baseline of 6), 9 of which land inside this exact phase — so occasional brief flips
  during a job resembling this run's profile are the KNOWN, disclosed, not-yet-closed condition, not
  automatically a new regression
- DO flag as a genuine new defect: a flip that never recovers (the badge stays `"unavailable"` after the
  job finishes), or the badge falsely reporting `"ready"` while `GET /api/health` is actually failing
  (checkable via the Network tab)
- Do NOT flag a brief flip-and-recover during the job as a new bug introduced by this iteration — it is the
  same class of pre-existing, root-caused issue this iteration attempted and failed to close, per the
  addendum

---

### UT-05 — `/backtest` scorecard and evidence section are unaffected (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Backend is running and reachable at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/backtest`
2. Wait for the page to load
3. Scroll to the evidence section

**Expected Result:**
- The forward-test scorecard renders with real (non-placeholder, non-"—") numeric rows — `GET /api/backtest`
  serves from the SAME `compute_forward_aggregates` producer this iteration's scheduling fix touched, and
  its output is proven byte-identical pre/post-fix
- The evidence section shows "Snapshots contributing" with a real numeric count, not a cold-recompute
  spinner or an error state

---

### UT-06 — `/data`'s Background compute panel still reflects in-flight/last-outcome activity (regression, J-09)

**Type:** regression
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- At least one as-of view has been requested on `/backtest` this session

**Steps:**
1. Navigate to `http://localhost:3255/backtest` and click "Previous available date" two or three times
2. Navigate to `http://localhost:3255/data`
3. Locate the "Background compute" panel (`data-testid="background-compute-panel"`)

**Expected Result:**
- The panel shows either an active in-flight entry or an updated "Last outcome" summary
- The footer text "Since the last backend restart — this history is process-lifetime only, never
  persisted." is still present, unchanged in wording

---

### UT-07 — Readiness badge/banner render consistently across all pages (ux)

**Type:** ux
**Priority:** P2
**Surface:** navigation / all pages

**Steps:**
1. Navigate to `http://localhost:3255/` (Dashboard)
2. Click "Data Manager" in the left sidebar
3. Click "Backtest" in the left sidebar

**Expected Result:**
- The readiness pill (`data-testid="readiness-badge"`) appears in the same header position on all three
  pages, showing the same `data-state` value throughout the click sequence (assuming no job is in flight)
- When not in a quiet "GO" state, the preflight banner (`data-testid="preflight-banner"`) also appears
  identically on all three pages

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/data` loads | smoke | P1 | `/data` |
| UT-02 | Happy-path "Refreshed: …" includes forward aggregates | happy-path | P1 | `/data` |
| UT-03 | Job form stays blocked on incomplete dates | validation | P2 | `/data` |
| UT-04 | Health badge/banner stability during forward-aggregate warm | error | P1 | global header/banner |
| UT-05 | `/backtest` scorecard/evidence unaffected | regression | P1 | `/backtest` |
| UT-06 | Background compute panel unaffected | regression | P2 | `/data` |
| UT-07 | Badge/banner render consistently across pages | ux | P2 | nav |

**P1 tests must all pass for browser QA verdict to be PASS.** Note UT-04 is graded per its own "Expected
Result" section (a KNOWN, disclosed baseline), not against a literal zero-non-answer bar — grading it
against zero would misrepresent this iteration's own honestly-reported miss as a new regression.

---

## Cannot Be Tested Via Browser This Iteration

- **The fault-omission path itself** (a genuine `MemoryError` aborting a real horizon mid-warm, causing
  "forward aggregates" to correctly disappear from the "Refreshed: …" line) cannot be reliably triggered
  on demand through the running UI — reproducing a real out-of-memory condition inside one specific horizon
  is exactly what the unit-level fault injector exists for. This is proven by
  `test_finalize_hook_forward_aggregates_live_incident_shape_omits_but_preserves_siblings`
  (`apps/backend/tests/test_data_manager.py`), not by a browser test in this plan.
