# Phase goal-ops-hardening-iter-51 — UI Test Plan

**Phase:** goal-ops-hardening-iter-51
**Date:** 2026-08-07
**Written by:** ui-impact-analyst (combined mode — standing in for ui-test-designer)
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255

---

## Before you start

- Zero frontend files changed this iteration (`Frontend Present: no` in `plan.md`). Every test below
  exercises an **existing** page whose behavior or content changed because of a backend-only fix — not a
  new page. See `reports/phase-goal-ops-hardening-iter-51-ui-surface-map.md` for the full mapping.
- Both servers were confirmed live and healthy at the time this plan was written:
  `curl http://localhost:8255/api/health` → `200` in ~0.1s; `curl http://localhost:3255/data` and
  `curl http://localhost:3255/research/factor-lab` → both `200`. No login/auth gate exists in this
  codebase (no redirect observed on either curl).
- A completed backfill that already exercises this iteration's change exists on this build right now
  (2011-03-16, `aggregates_refreshed` includes `factor_lab_all`) — most tests below do **not** require you
  to trigger a fresh ~15–20 minute ingest; they read the already-warmed state. Tests that specifically
  need a *fresh* job say so explicitly.

---

## Test Cases

---

### UT-01 — Factor Lab page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend running at http://localhost:3255; backend running at http://localhost:8255
- No login required

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait up to 5 seconds for the page to settle

**Expected Result:**
- Page renders without a blank screen or an unhandled application error
- The heading "Research — Factor Lab" is visible
- No new browser console errors
- Either the factor comparison table, or a labelled loading/"still computing"/error card is shown —
  never an indefinite unlabeled spinner

---

### UT-02 — Factor Lab is a fast cache HIT with real data right after ingest (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- A fetch/backfill/rebuild job that bumped the dataset-version stamp has reached status "ok" (the
  already-completed 2011-03-16 backfill on this build satisfies this — no fresh job needed)

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Watch the page continuously for the first 3+ seconds after navigating
3. Once content settles, click the "RANK IC" column header to trigger a client-side sort
4. Click anywhere on the first data row to expand its decile detail

**Expected Result:**
- The amber "Still computing — Xs elapsed" card (`data-testid="slow-compute-notice"`) never appears
- The factor table shows real, non-placeholder rows (multiple rows, e.g. "Leadership score"; not every
  cell reading "NA")
- Sorting re-orders rows immediately, with no page reload/new network fetch
- Expanding the row reveals its D1…D10 decile grid with no error
- (Optional cross-check from a terminal:
  `curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" "http://localhost:8255/api/research/factor-lab?all=true"`
  → expect `200` and well under 1s; confirmed 0.008–0.043s live on this build, vs. the 578–875s this same
  call took on the request path before this iteration)

---

### UT-03 — `/data`'s "Refreshed" line lists "factor lab all" after a warming job (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- None beyond both servers running — a warmed run already exists on this build

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Locate the "Job progress" card (if no job has started this browser session, it falls back to the most
   recent persisted run's summary — this is expected, not an error)
3. Read the small grey text line starting "Refreshed:" beneath the snapshot/day count

**Expected Result:**
- A paragraph with `data-testid="aggregates-refreshed"` is present, reading "Refreshed: " followed by a
  comma-separated list
- The list includes the term "factor lab all" (confirmed present for the most recent run on this build,
  alongside "coverage", "research hot keys", and the other pre-existing terms)
- If you instead just started a **new** job yourself, this line will not show "factor lab all" until that
  job's own finalize tail completes — budget roughly 15–20 minutes end-to-end for a freshly-triggered job
  (see "Known Issues" in the dev handoff; this is a disclosed, accepted trade-off, not a bug)

---

### UT-04 — Start-job form still blocks invalid/incomplete dates (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data` ("Start a fetch / backfill job" card)

**Preconditions:**
- Navigate to `/data`

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the "Start date" field (aria-label "Job start date", `data-testid="job-start-date"`), clear it and
   type `2026-13-40`
3. Leave "End date" (aria-label "Job end date") as its prefilled value
4. Observe the "Start" button

**Expected Result:**
- An inline error, "Enter a valid date as YYYY-MM-DD", appears under the Start date field
  (`data-testid="job-start-date-error"`)
- The "Start" button is disabled (cannot be clicked) while the field is invalid
- No job is created

*(Not touched by this iteration — included because this form is the only entry point that can trigger the
changed finalize-tail code path; a broken guard here would block verifying every other case in this
plan.)*

---

### UT-05 — A degraded factor-lab warm is honestly omitted; the job still completes cleanly (error)

**Type:** error
**Priority:** P1
**Surface:** `/data` (job outcome) + `logs/backend.log`

**Preconditions:**
- Restart the backend with the project's existing, committed, test-only `MemoryError` fault-injection
  hook aimed at this exact site:
  `TRENDORA_FAULT_INJECT_MEMORY_ERROR=factor_lab_all scripts/start-backend.sh`
  (see `apps/backend/app/engine/data_manager.py` around line 3247 — `_FAULT_INJECT_SITES` already includes
  `"factor_lab_all"` from iter-50. This induces **no real memory pressure**, so it is safe under AG-10 —
  the launch script itself is invoked unmodified, only an env var is set before calling it.)

**Steps:**
1. With the backend started as above, go to `http://localhost:3255/data`
2. Start a small backfill job that creates at least one new snapshot date (fill Start/End date, leave
   Job kind = "Backfill snapshots", click "Start")
3. Wait for the status badge (`data-testid="job-status"`) to leave "running"
4. Read the "Refreshed:" line for this job

**Expected Result:**
- The job still reaches a normal terminal status (e.g. "ok") — it does not hang, crash, or show a 500
- The "Refreshed:" line is present but does **not** include "factor lab all"; every other category that
  legitimately succeeded (e.g. "coverage") still appears
- `logs/backend.log` contains a `"J-05 finalize-tail phase timing: ... phase=factor_lab_all_warm ..."`
  line and an "ingest factor-lab-all warm" isolation-failure log line, with **no unhandled traceback**
- **Afterward:** restart the backend without the env var so later verification isn't run against an
  artificially-degraded build

---

### UT-06 — Factor Combination results are unchanged after the cohort-members allocation fix (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/factor-combination`

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-combination`
2. Click "Add condition" twice to configure two factor conditions (default factor/threshold each control
   offers is fine)
3. Read the resulting single/strict/composite member counts and the samples drill-down

**Expected Result:**
- The page loads and returns results — no error state
- The counts and sample lists match what the same two conditions produced before this iteration (or, if
  no prior live baseline is available, match `test_research_streaming.py`'s pinned-oracle fixture) — this
  iteration's `_combination_cohort_members` change is an allocation-strategy change only and must not move
  any displayed number

---

### UT-07 — Factor Lab's sort/expand/mode controls still work on cache-warmed data (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/research/factor-lab`

**Preconditions:**
- Page has loaded with data (per UT-02)

**Steps:**
1. On `http://localhost:3255/research/factor-lab`, click the "N" column's sort header twice (ascending,
   then descending)
2. Click the "As of date" toggle (`data-testid="analysis-mode-asof"`), then click "All history"
   (`data-testid="analysis-mode-all"`) to switch back

**Expected Result:**
- Each sort click visibly re-orders rows, and the header's arrow indicator (`data-testid="sort-indicator"`)
  flips direction
- Switching analysis mode re-fetches and re-renders without an error card
- No regression from the fact that the underlying data now arrives via the ingest-time warm path instead
  of a request-time compute — client-side behavior is identical either way

---

### UT-08 — `/api/health` and concurrent research requests survive a live finalize-tail warm (regression / resilience)

**Type:** regression
**Priority:** P1
**Surface:** backend (`/api/health`, `/research/factor-lab`, `/research/factor-combination`) during a
live `/data` job

**Preconditions:**
- None, but this test takes as long as a full ingest job (~15–20 minutes) — budget time separately from
  the rest of this plan

**Steps:**
1. Start a fresh fetch/backfill job on `http://localhost:3255/data` that will bump the dataset-version
   stamp
2. From a terminal, poll
   `curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" http://localhost:8255/api/health`
   once per second for the job's full duration plus 300 seconds past completion; log every non-200 or
   connection failure
3. Partway through — once the job card still shows "running" — in a second browser tab open
   `http://localhost:3255/research/factor-lab` and separately `http://localhost:3255/research/factor-combination`

**Expected Result:**
- Record the health-poll non-200/connection-failure count. The dev's own solo run (no concurrent request)
  already found 9/653 connection-level non-responses inside the new warm phase's window — this step
  specifically checks whether adding a *concurrent* research request changes that count
- The two concurrent research page loads complete quickly (consistent with UT-02's cache-HIT timing)
  rather than blocking for minutes, and neither shows a `MemoryError`/500
- This is the exact concurrent drill named TC-5/TC-6 in the phase spec, and it is flagged as
  **still-outstanding** in the dev handoff's "Suggested Next Phase" (the developer's own pass ran only a
  solo, non-concurrent measurement). Treat a failure here as scoping input for the next iteration, not
  automatically a blocker for this one — goal.md explicitly carries the ≤2s-during-ingest ceiling as a
  known, disclosed, not-yet-closed gap, out of this iteration's stated scope.

---

### UT-09 — Factor Lab stays reachable from the Research hub (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research`

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3255/research`
2. Locate the tile titled "Factor Lab" (`data-testid="research-lab-link-factor-lab"`) in the lab grid
3. Click it

**Expected Result:**
- The tile is visible among the other research lab tiles, unchanged in wording/position
- Clicking it navigates to `/research/factor-lab` (optionally with an `?asof=` query param) and the page
  loads per UT-01

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Factor Lab loads without errors | smoke | P1 | `/research/factor-lab` |
| UT-02 | Factor Lab is a fast cache HIT with real data | happy-path | P1 | `/research/factor-lab` |
| UT-03 | `/data` Refreshed line lists "factor lab all" | happy-path | P1 | `/data` |
| UT-04 | Start-job form blocks invalid dates | validation | P2 | `/data` |
| UT-05 | Degraded warm honestly omitted; job still completes | error | P1 | `/data` + `logs/backend.log` |
| UT-06 | Factor Combination results unchanged | regression | P1 | `/research/factor-combination` |
| UT-07 | Factor Lab sort/expand/mode controls still work | regression | P2 | `/research/factor-lab` |
| UT-08 | Health + concurrent requests survive a live warm | regression | P1 | backend, cross-page |
| UT-09 | Factor Lab discoverable from Research hub | ux | P2 | `/research` |

**P1 tests must all pass for browser QA verdict to be PASS.**
