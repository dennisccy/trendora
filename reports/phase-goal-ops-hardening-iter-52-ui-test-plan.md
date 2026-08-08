# Phase goal-ops-hardening-iter-52 — UI Test Plan

**Phase:** goal-ops-hardening-iter-52
**Date:** 2026-08-07
**Written by:** ui-impact-analyst (combined mode — standing in for ui-test-designer)
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255

---

## Before you start

- Zero frontend files changed this iteration (`Frontend Present: no` in `plan.md`). Every test below
  exercises an **existing** page/component. See
  `reports/phase-goal-ops-hardening-iter-52-ui-surface-map.md` for the full surface mapping.
- Both servers were confirmed live at the time this plan was written:
  `curl http://localhost:8255/api/health` → `200` in 0.12s; `curl http://localhost:3255/`,
  `/data`, and `/research/factor-lab` → all `200`. No login/auth gate exists in this codebase.
- **Read this before grading UT-03/UT-04.** This iteration's own developer pass already ran a live
  measurement and found the specific reliability improvement it targeted was **not achieved** — connection-
  level `/api/health` non-answers went from 9 (pre-fix baseline) to 22 (this iteration), and the finalize-
  tail job duration exceeded its existing budget (`reports/perf-budgets.md` Item U / Addendum 12). UT-03 and
  UT-04 below are written to test whether the **UI behaves honestly and recovers** around that known,
  already-disclosed condition — not to re-assert the zero-non-answer target, which is already known unmet
  and is the goal-evaluator's call to weigh, not a UI test's. Do not fail this plan solely because
  non-answers occur; fail it if the UI misbehaves (gets stuck, lies about state, or crashes) around them.
- UT-03/UT-04/UT-08 require starting a real backfill job, which can now take a long time (this iteration's
  own drill did not finish inside 30 minutes on one date). Budget that time separately from the rest of this
  plan, exactly as iter-51's equivalent test flagged for its own (shorter) 15–20 minute job.

---

## Test Cases

---

### UT-01 — Dashboard and Data Manager load without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`, `/data`

**Preconditions:**
- Frontend running at http://localhost:3255; backend running at http://localhost:8255
- No login required

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Wait up to 5 seconds for the page to settle
3. Click "Data Manager" in the left sidebar
4. Wait up to 5 seconds for the page to settle

**Expected Result:**
- Both pages render without a blank screen or an unhandled application error
- No new browser console errors on either page
- The header's readiness pill and the row of navigation links are visible on both pages

---

### UT-02 — Readiness badge and preflight banner show their normal, honest state at rest (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** global (every page's header/sub-header)

**Preconditions:**
- No fetch/backfill/rebuild job currently running
- Backend has completed at least one prior ingest (true on this build)

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Look at the pill in the top-right of the header
3. Look at the thin strip directly beneath the header

**Expected Result:**
- The pill reads "Ready" with a solid green dot (not "Checking backend…", not red)
- The strip beneath the header is either absent or a quiet green line reading
  "GO — today's board is current." — it must NOT be a loud red banner while no job is running and the
  backend is healthy
- This establishes the healthy baseline that UT-03 will compare against once a job starts

---

### UT-03 — Readiness badge/banner behave honestly and self-recover during a heavy backfill job (regression / resilience — read "Before you start" first)

**Type:** regression
**Priority:** P1
**Surface:** global (header/sub-header) + `/data`

**Preconditions:**
- None, but this test takes as long as a full backfill job — this iteration's own measured drill did not
  finish inside 30 minutes on one date. Budget time separately from the rest of this plan.

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the "Start a fetch / backfill job" panel, leave the "Start date" and "End date" fields at their
   pre-filled default values (the page automatically fills them from the first detected coverage gap on
   load — no manual date entry needed) and leave "Job kind" set to "Backfill snapshots"
3. Click the "Start" button
4. From this moment, watch the header's readiness pill continuously until the job's status badge
   (in the "Job progress" card) reaches a terminal state (e.g. "ok")
5. Note every timestamp/approximate moment the pill flips from green "Ready" to red
   "Backend unavailable", and how many seconds elapse before it flips back on its own

**Expected Result (what MUST hold — a real fail):**
- The job itself still reaches a normal terminal status — it must not hang forever, crash, or leave the
  page in an error state
- Whenever the pill/banner do flip to their failure state, they show the correct, honest labels ("Backend
  unavailable" / "NO-GO — do not rely on today's board") — never a fabricated "Ready"/"GO" while a poll is
  actually failing
- Every flip to the failure state recovers on its own (flips back to "Ready"/quiet "GO") within a few
  polling cycles once `/api/health` next answers successfully — it must never stay stuck on red
  indefinitely

**Expected Result (what to record, not grade as pass/fail):**
- The number of times the pill flipped to red and roughly how long each flip lasted. **Do not expect
  zero** — this iteration's own developer-pass drill recorded 22 connection-level non-answers in one run
  (worse than the 9 measured before this fix). A similar or worse count on your run is the currently
  known, disclosed, unresolved condition (`reports/perf-budgets.md` Item U), not a new bug you found.

---

### UT-04 — Job duration against the existing ~20-minute finalize-tail budget (regression / resilience measurement)

**Type:** regression
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Same running job as UT-03 (can be observed in parallel with it)

**Steps:**
1. Note the wall-clock time when you clicked "Start" in UT-03
2. Periodically check the job's status badge (in the "Job progress" card) and the "updated Ns ago"
   heartbeat text next to it
3. Note the wall-clock time when the status badge leaves its running state

**Expected Result:**
- The "updated Ns ago" heartbeat keeps advancing throughout (never frozen for minutes at a time) — this
  is what distinguishes "slow but alive" from an actual stall
- Record the total elapsed time. This iteration's own drill measured 1,670.95s+ (partial, ~27.8+ minutes)
  against the product's existing ~1,200s (20-minute) budget on one date — an overage is the currently
  known, disclosed condition, not automatically a new bug. Treat a run finishing well within 20 minutes as
  good news worth noting, and a run taking 45+ minutes or never finishing as worth flagging distinctly
  (the developer's own drill did not reach completion within its 30-minute measurement ceiling)

---

### UT-05 — Start-job form still blocks invalid dates (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data` ("Start a fetch / backfill job" panel)

**Preconditions:**
- Navigate to `/data`

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the "Start date" field (aria-label "Job start date"), clear it and type `2026-13-40`
3. Leave "End date" (aria-label "Job end date") as its prefilled value
4. Observe the "Start" button

**Expected Result:**
- An inline validation error appears under the "Start date" field
- The "Start" button is disabled (cannot be clicked) while the field is invalid
- No job is created

*(Not touched by this iteration — included because this form is the only entry point that can trigger the
changed finalize-tail code path; a broken guard here would block verifying UT-03/UT-04.)*

---

### UT-06 — Factor Lab results are unaffected by the scheduling change (regression, TC-4)

**Type:** regression
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- At least one completed ingest exists (true on this build)

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait up to 5 seconds for the page to settle
3. Click the "N" column header to trigger a client-side sort
4. Click anywhere on the first data row to expand its decile detail

**Expected Result:**
- The factor table shows real, non-placeholder rows (not every cell reading "NA")
- Sorting re-orders rows immediately with no page reload or error
- Expanding the row reveals its decile grid with no error
- Values match what the same page showed before this iteration (this iteration's yield points are
  scheduling-only — the pinned-oracle unit-test suite already confirms byte-identical output; this step is
  a live spot-check, not the primary proof)

---

### UT-07 — Factor Combination results are unaffected (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/research/factor-combination`

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-combination`
2. Click "Add condition" twice to configure two factor conditions
3. Read the resulting single/strict/composite member counts

**Expected Result:**
- The page loads and returns results — no error state
- The counts match what the same two conditions produced before this iteration (this iteration did not
  touch this code path; included as a broad regression check on the shared `research.py` module)

---

### UT-08 — A degraded background calculation is still honestly disclosed while the job completes cleanly (error, TC-6 manual mirror)

**Type:** error
**Priority:** P2
**Surface:** `/data` + `logs/backend.log`

**Preconditions:**
- Restart the backend with the project's existing, committed, test-only fault-injection hook aimed at the
  same site this iteration's own new automated test uses:
  `TRENDORA_FAULT_INJECT_MEMORY_ERROR=factor_lab_all scripts/start-backend.sh`
  (induces no real memory pressure — safe under AG-10; the launch script itself is invoked unmodified,
  only an env var is set before calling it)

**Steps:**
1. With the backend started as above, go to `http://localhost:3255/data`
2. Start a backfill job (leave the pre-filled Start/End dates, "Job kind" = "Backfill snapshots", click
   "Start")
3. Wait for the status badge to leave its running state
4. Read the "Refreshed:" line for this job

**Expected Result:**
- The job still reaches a normal terminal status — it does not hang, crash, or show a 500
- The "Refreshed:" line is present but does **not** include "factor lab all"; every other category that
  legitimately succeeded (e.g. "coverage") still appears
- Throughout this run, the header's readiness pill still recovers normally (per UT-03's "what MUST hold")
- **Afterward:** restart the backend without the env var before running any other test in this plan

---

### UT-09 — Readiness badge/banner render consistently across pages (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`, `/data`, `/research`

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3255/`, then click "Data Manager", then click "Research" in the left
   sidebar
2. On each of the three pages, look at the top-right header pill and the strip beneath the header

**Expected Result:**
- The pill and (when not in a quiet "GO" state) the banner appear in the same position, with the same
  wording, on all three pages — confirming the global, layout-level element this iteration's backend
  change targets is genuinely shared, not duplicated per-page

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Dashboard/Data Manager load without errors | smoke | P1 | `/`, `/data` |
| UT-02 | Badge/banner show honest state at rest | smoke | P1 | global |
| UT-03 | Badge/banner behave honestly & self-recover during a heavy job | regression | P1 | global, `/data` |
| UT-04 | Job duration vs. existing budget | regression | P2 | `/data` |
| UT-05 | Start-job form blocks invalid dates | validation | P2 | `/data` |
| UT-06 | Factor Lab results unaffected | regression | P1 | `/research/factor-lab` |
| UT-07 | Factor Combination results unaffected | regression | P2 | `/research/factor-combination` |
| UT-08 | Degraded category honestly disclosed; job still completes | error | P2 | `/data` + `logs/backend.log` |
| UT-09 | Badge/banner consistent across pages | ux | P2 | `/`, `/data`, `/research` |

**P1 tests must all pass for browser QA verdict to be PASS.** Per "Before you start": UT-03's P1 status
covers the UI's *honesty and self-recovery* around the known reliability gap, not the gap's existence —
grade it on those criteria, not on whether non-answers occurred at all.
