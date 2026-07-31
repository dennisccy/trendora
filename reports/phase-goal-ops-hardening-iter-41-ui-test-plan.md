# Phase goal-ops-hardening-iter-41 — UI Test Plan

**Phase:** goal-ops-hardening-iter-41
**Date:** 2026-07-31
**Written by:** ui-impact-analyst (combined mode — standing in for ui-test-designer per SPEED-24)
**Frontend URL:** http://localhost:3255
**Backend health URL:** http://localhost:8255/api/health

---

## Scope note (read before executing)

`Frontend Present: no` for this iteration and the phase spec's own metadata declares "New user-facing
capability: None" / "UI surface changes: None". Per this iteration's own fix to the `ui-test-designer`
agent (`incredible_auto_dev/agents/ui-test-designer/body.md`, item A2 in the dev handoff), a backend-only
spec now suppresses **NEW-surface test-case generation only** — it still emits exactly one `UT-J-XX`
regression test case per journey named in the phase spec's **Required-still-passing journeys** metadata
line: **J-01, J-03, J-04, J-06, J-08, J-09**.

This test plan therefore contains **6 test cases, all type `regression`, zero NEW-surface cases** — this
is the expected shape for this iteration (see plan.md's own TC-1: "contains one `UT-J-XX` regression test
case per required journey and zero NEW-surface test cases").

The phase's **target** journeys (J-05, J-07) are also backend-only this iteration (no new UI surface for
either — J-05 is a cold-boot/coverage-payload check, J-07 is a memory/health-polling check during a
forward-aggregate warm) and are verified through non-UI evidence instead: pytest fixture tests
(`test_bar_cache.py`), the wedge-drill log (`runs/goal-ops-hardening-iter-41/wedge-drill/README.md`), and
`reports/perf-budgets.md`'s measured VmPeak/health-latency figures. They are intentionally NOT given
`UT-J-XX` rows here, matching the ui-test-designer's fixed scope (required-still-passing journeys only).

---

## Test Cases

---

### UT-J-01 — Backfill honors the requested range and explains zero-work (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`, `/scanner-runs`, `/scanner-runs/[runId]`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running and reachable at
  http://localhost:8255/api/health
- No login required

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the "Start a fetch / backfill job" panel, type `2026-05-02` into the "Start date" field
   (`data-testid="job-start-date"`, `aria-label="Job start date"`)
3. Type `2026-05-29` into the "End date" field (`data-testid="job-end-date"`,
   `aria-label="Job end date"`)
4. Confirm the "Job kind" dropdown (`aria-label="Job kind"`) reads "Backfill snapshots" (its default
   value)
5. Click the "Start" button (the accent button with the play icon, to the right of the "Job kind"
   dropdown)
6. Watch the "Job progress" panel (`data-testid="job-status"`) until its status leaves "running"

**Expected Result:**
- The job reaches a terminal status (not stuck on "running" indefinitely)
- If this is the first time this range has been backfilled in the current DB state: the summary text
  reports `dates_total = 19` (trading days 2026-05-04 … 2026-05-29, Memorial Day 2026-05-25 excluded)
- If the range was already backfilled earlier: the run renders a visually distinct "no new snapshots"
  explanatory badge (`runStatusLabel` returns "no new snapshots" for a zero-work backfill/both/rebuild
  run) — NOT the same plain success badge as a productive run
7. Navigate to `http://localhost:3255/scanner-runs`
8. Confirm rows exist for `2026-05-04`, `2026-05-15`, and `2026-05-29`
9. Click the `2026-05-29` row
- The "Scanner Run" detail page opens and renders a populated leaderboard table (not the "No stored
  stock rows" empty state)

---

### UT-J-03 — No per-run range cap (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend running at http://localhost:3255, backend reachable
- Navigate to a fresh load of `/data` (no job currently running)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Type `2025-06-01` into the "Start date" field (`data-testid="job-start-date"`)
3. Type `2026-07-17` into the "End date" field (`data-testid="job-end-date"`) — a 411-calendar-day span
4. Confirm "Job kind" reads "Backfill snapshots"
5. Click the "Start" button

**Expected Result:**
- No error text such as "date range too large" (or any range-cap rejection message) appears near the
  form
- The "Job progress" panel (`data-testid="job-status"`) transitions to a running state, and the live
  activity line (`data-testid="job-live-activity"`, `data-testid="job-heartbeat"`) shows movement,
  confirming the request was accepted and is chunk-executing rather than rejected outright

---

### UT-J-04 — Non-blocking boot with visible status (regression)

**Type:** regression
**Priority:** P1
**Surface:** Global readiness badge (any page), preflight banner

**Preconditions:**
- Frontend already open at `http://localhost:3255/`
- Operator has terminal access to stop/restart the backend via `scripts/start-backend.sh`

**Steps:**
1. With `http://localhost:3255/` open in the browser, stop the backend process, then restart it via
   `scripts/start-backend.sh`
2. Immediately watch the top-bar readiness badge (`data-testid="readiness-badge"`)
3. Once the badge reads "Ready", stop the backend process again (simulated crash — `kill`, not a clean
   `scripts/start-backend.sh` stop)
4. Watch the badge / banner again

**Expected Result:**
- Step 2: the badge passes through `data-state="loading"` or `data-state="initializing"` before settling
  on `data-state="ready"` with visible text "Ready" — the header is never blank during this window
- Step 4: the badge shows `data-state="unavailable"` with text "Backend unavailable", and/or the
  preflight banner renders the reason "Backend is unavailable — the preflight check could not run." —
  visibly distinct from the initializing presentation in step 2 (different badge variant/color, explicit
  wording, not a bare loading spinner)

---

### UT-J-06 — Every page loads within its committed budget (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`,
`/scanner-runs`, `/backtest`, `/watchlist`, `/research/event-study`

**Preconditions:**
- Backend running in prod mode via `scripts/start-backend.sh` (not `dev.sh`), warm (already served at
  least one request)
- Frontend running in prod mode via `scripts/start-frontend.sh` (not `dev.sh`)

**Steps:**
1. Navigate to `http://localhost:3255/` and note the time until the dashboard's primary content renders
   (no perpetual skeleton)
2. Repeat for each of: `http://localhost:3255/stocks`, `http://localhost:3255/stocks/AAPL`,
   `http://localhost:3255/sectors`, `http://localhost:3255/themes`, `http://localhost:3255/data`,
   `http://localhost:3255/evidence`, `http://localhost:3255/scanner-runs`,
   `http://localhost:3255/backtest`, `http://localhost:3255/watchlist`,
   `http://localhost:3255/research/event-study`

**Expected Result:**
- Every page listed finishes loading (skeleton/spinner replaced by real content) without hanging
  indefinitely
- No page's load time or on-load API latency exceeds its corresponding row in
  `reports/perf-budgets.md` (cross-check against the "Iteration 41" section's recorded figures for this
  run)

---

### UT-J-08 — Backtest serves stored evidence, never a cold recompute (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/backtest`, `/data`

**Preconditions:**
- A forward-aggregate warm has completed at least once already for the current dataset version (so a
  "last-good" version exists to fall back to)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Start a small single-day backfill: set both "Start date" and "End date"
   (`data-testid="job-start-date"` / `job-end-date`) to the same unsnapshotted date, then click "Start"
3. While that job's finalize warm is still running (visible in "Job progress"), navigate to
   `http://localhost:3255/backtest`
4. Observe the evidence panel
5. After the "Run history" row for the job lists `forward_aggregates` among its refreshed aggregates,
   reload `http://localhost:3255/backtest`

**Expected Result:**
- Step 4: `/backtest` renders promptly — either normal served values from the PREVIOUS version, or the
  banner "Refreshing — showing the last complete evidence" (`data-testid="evidence-refreshing"`) — never
  a blank page or an indefinite loading skeleton waiting on a fresh compute
- Step 5: `/backtest` now shows the new version's values and the "Refreshing…" banner is gone

---

### UT-J-09 — Background-compute activity is disclosed on the badge and `/data` panel (regression)

**Type:** regression
**Priority:** P1
**Surface:** Global readiness badge (any page), `/data`

**Preconditions:**
- Backend warm; at least one historical as-of exists whose forward-aggregate evidence is not yet
  complete for the current dataset version (to trigger a background-compute window on request)

**Steps:**
1. Navigate to `http://localhost:3255/backtest` and select/load a historical as-of date whose evidence is
   not yet computed for the current dataset version (this dispatches a background-compute window without
   blocking the request — J-08 unchanged)
2. Immediately look at the top-bar badge
3. Navigate to `http://localhost:3255/data` and look at the "Background compute" panel
   (`data-testid="background-compute-panel"`)

**Expected Result:**
- Step 2: the badge still reads "Ready" AND shows an additional accent chip
  (`data-testid="background-compute-indicator"`) reading "background compute running (1)" — never a bare
  "Ready" that hides the in-flight compute
- Step 3: the panel lists the in-flight window (not the idle text "No background compute running.")
  showing elapsed time and horizons done/total
- After the window completes: re-polling the badge no longer shows the chip, and the `/data` panel's
  "Last outcome" section shows the completed window's outcome and a real measured duration

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-J-01 | Backfill honors requested range, explains zero-work | regression | P1 | `/data`, `/scanner-runs` |
| UT-J-03 | No per-run range cap | regression | P1 | `/data` |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | global badge, preflight banner |
| UT-J-06 | Every page loads within budget | regression | P1 | 11 listed routes |
| UT-J-08 | Backtest serves stored evidence, never cold-recomputes | regression | P1 | `/backtest`, `/data` |
| UT-J-09 | Background-compute activity disclosed | regression | P1 | global badge, `/data` |

**All 6 test cases are P1** — every journey in this table is a required-still-passing journey per the
phase spec's metadata; per the phase's own Definition of Done, none may merge as clean `SKIPPED`/`PASS`
without fresh, non-carried-forward evidence this iteration.

**Zero NEW-surface test cases** — confirmed: no `UT-01`/`UT-02`-style new-capability case exists in this
plan, consistent with `Frontend Present: no` and "New user-facing capability: None".
