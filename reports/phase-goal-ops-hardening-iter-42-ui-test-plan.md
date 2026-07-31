# Phase goal-ops-hardening-iter-42 — UI Test Plan

**Phase:** goal-ops-hardening-iter-42
**Date:** 2026-07-31
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend health URL:** http://localhost:8255/api/health

---

## Scope note (read before executing)

`Frontend Present: no` for this iteration — the phase spec's own metadata states "New user-facing
capability: None", "UI surface changes: None", and the dev handoff confirms **zero files under
`apps/frontend/` were touched**. Per the "Backend-only phase handling" rule this iteration itself
implemented in `ui-test-designer` (`incredible_auto_dev/agents/ui-test-designer/body.md` — this
iteration's own headline closure, item A of the plan), a backend-only spec now emits exactly one
`UT-<journey-id>` regression test case for **every journey named on EITHER** the spec's
`Required-still-passing journeys:` line **OR** its `Target journeys:` line — not the
`Required-still-passing`-only scope iter-41's plan used.

This iteration's metadata names:
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09 (widened to the full
  passing set per ESCALATE cadence guidance)
- **Target journeys:** J-05, J-07

Union of both lines = 8 distinct journeys, no duplicates (none is named on both lines). This test
plan therefore contains **8 test cases, all type `regression`, all Priority P1, zero NEW-surface
cases** — this is exactly the shape TC-1 of this iteration's own phase spec requires: a backend-only
spec with `Target journeys: J-05` (and `J-07`) must get `UT-J-05`/`UT-J-07` rows, not only rows for
the required-still-passing set.

J-05 and J-07 are backend/process-level journeys with no dedicated new UI surface (J-05 is a
cold-boot/coverage-payload + ingest-finalize check; J-07 is a memory/health-polling check during a
forward-aggregate warm) — their test cases below exercise the SAME existing surfaces
(`/data`, `/scanner-runs`, `/backtest`, the global readiness badge) that J-01/J-08/J-09 already use,
translating each journey's own "Steps"/"Acceptance" text from `docs/goal.md` into exact click paths.
J-07's steps 3-4 (VmPeak measurement, a synthetic memory-pressure test hook) are NOT
browser/operator-observable and are out of this plan's scope — they are covered by
`apps/backend/tests/test_bar_cache.py` and the live measurement scripts under
`runs/goal-ops-hardening-iter-42/`, per this iteration's own TC-5 (which explicitly scopes browser
replay to "J-07's golden script steps 1-2" only) and the dev handoff's own "Known Issues" /
"J-05/J-07 browser-level re-verification is QA/browser-qa-agent scope" note.

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
2. Type `2026-05-02` into the "Start date" field (`data-testid="job-start-date"`,
   `aria-label="Job start date"`)
3. Type `2026-05-29` into the "End date" field (`data-testid="job-end-date"`,
   `aria-label="Job end date"`)
4. Confirm the "Job kind" dropdown (`aria-label="Job kind"`) reads "Backfill snapshots" (its default
   value)
5. Click the "Start" button (the accent button with the play icon, to the right of the "Job kind"
   dropdown)
6. Watch the "Job progress" panel (`data-testid="job-status"`) until its status leaves "running"
7. Navigate to `http://localhost:3255/scanner-runs`
8. Confirm rows exist for `2026-05-04`, `2026-05-15`, and `2026-05-29`
9. Click the `2026-05-29` row

**Expected Result:**
- The job reaches a terminal status (not stuck on "running" indefinitely)
- If this is the first time this range has been backfilled in the current DB state: the summary text
  reports `dates_total = 19` (trading days 2026-05-04 … 2026-05-29, Memorial Day 2026-05-25 excluded)
- If the range was already backfilled earlier: the run renders a visually distinct "no new snapshots"
  explanatory badge (`runStatusLabel` returns "no new snapshots" for a zero-work backfill/both/rebuild
  run) — NOT the same plain success badge as a productive run
- Step 9: the "Scanner Run" detail page opens and renders a populated leaderboard table (not the "No
  stored stock rows" empty state)

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

### UT-J-05 — Aggregates are precomputed at ingest, never on the fly (regression, target journey)

**Type:** regression
**Priority:** P1
**Surface:** `/data`, `/scanner-runs`, `/scanner-runs/[runId]`, global readiness badge

**Preconditions:**
- Frontend running at http://localhost:3255, backend running and reachable at
  http://localhost:8255/api/health
- Operator has terminal/log access to tail `logs/backend.log` and can restart the backend via
  `scripts/start-backend.sh`
- No login required

**Steps:**
1. Navigate to `http://localhost:3255/scanner-runs` and note which dates already have a listed run —
   pick a historical trading day that is NOT listed (e.g. `2026-04-15`; if UT-J-01 already ran in this
   session, the whole 2026-05-04 → 2026-05-29 range will already be listed, so pick a date outside
   that range instead)
2. Navigate to `http://localhost:3255/data`
3. Type the chosen unsnapshotted date into BOTH the "Start date" field (`data-testid="job-start-date"`)
   and the "End date" field (`data-testid="job-end-date"`) — a single-day backfill
4. Confirm "Job kind" (`aria-label="Job kind"`) reads "Backfill snapshots"
5. Click the "Start" button
6. While the job runs (Job progress panel `data-testid="job-status"` reads "running"), watch the
   top-bar readiness badge (`data-testid="readiness-badge"`)
7. Watch the "Job progress" panel until its status leaves "running"
8. In the "Run history" table, find the row for the run just started and read its "Refreshed:" text
   (`data-testid="aggregates-refreshed"`)
9. Navigate to `http://localhost:3255/scanner-runs`, confirm the chosen date now appears in the list,
   then click its row
10. Restart the backend process via `scripts/start-backend.sh` (terminal), then load
    `http://localhost:3255/data` cold (first request after restart)
11. Tail `logs/backend.log` around the restart and the cold `/data` request from step 10

**Expected Result:**
- Step 6: the readiness badge stays at `data-state="ready"` throughout the ingest job — it never
  switches to `data-state="unavailable"` while the backfill (and its finalize aggregate warm) runs
- Step 7: the job reaches a terminal status, not stuck on "running"
- Step 8: the "Refreshed:" text lists at least "latest snapshot" and "coverage" (additional entries
  such as "membership timeline", "market phase", "research hot keys" may also appear) — never blank
  for a successful backfill of a new date
- Step 9: the Scanner Run detail page renders a populated leaderboard table (not "No stored stock
  rows")
- Step 10: `/data`'s "Dataset coverage" panel — Universe count (`data-testid="universe-count"`) and
  Candidate universe (`data-testid="candidate-universe-count"`) — renders populated numeric values
  promptly (within the cold-load budget recorded in `reports/perf-budgets.md`), not a blank/error
  panel and not an indefinite spinner
- Step 11: the tailed `logs/backend.log` around the restart and cold `/data` request from step 10
  contains no line indicating a full-table / 3.3M-row bar prefill for that request (cross-check
  against the "no 3.3M-row bar prefill trace" wording in this iteration's own TC-4)

---

### UT-J-06 — Every page loads within its committed budget (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`,
`/scanner-runs`, `/backtest`, `/watchlist`, one `/research` lab

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
  `reports/perf-budgets.md` (cross-check against the "Iteration 42" section's recorded figures for
  this run — note this iteration's own T2 finding that `bars_asof`'s per-call cost over
  `_SymbolColumns` rose ~72-75× versus the pre-iter-41 baseline; pages that call `bars_asof` heavily
  per ticker per date, e.g. `/stocks`, `/sectors`, `/themes`, are the ones most likely to show this
  regression if it pushes any page over its committed budget — flag any budget miss explicitly rather
  than rounding it to "close enough")

---

### UT-J-07 — Heavy aggregate warm never takes the health endpoint or `/backtest` down (regression, target journey)

**Type:** regression
**Priority:** P1
**Surface:** Global readiness badge (any page), `/backtest`, `/data`

**Scope note:** this covers J-07 steps 1-2 only (the browser/operator-observable subset), matching
this iteration's own TC-5. J-07 steps 3-4 (peak-memory/VmPeak measurement, a synthetic
memory-pressure abort via a test hook) are not observable through the UI and are verified instead by
`apps/backend/tests/test_bar_cache.py` and the live measurement scripts under
`runs/goal-ops-hardening-iter-42/bar-cache-prefill-bench/` — not part of this test case.

**Preconditions:**
- Frontend running at http://localhost:3255, backend running in prod mode via
  `scripts/start-backend.sh` (not `dev.sh`), reachable at http://localhost:8255/api/health
- Operator has a terminal to poll `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8255/api/health`
  repeatedly (e.g. once per second) alongside browser observation
- A wide, not-yet-fully-snapshotted date range is available to trigger a heavy multi-date backfill and
  its forward-aggregate warm (e.g. reuse UT-J-03's 2025-06-01 → 2026-07-17 span, or any multi-month
  unsnapshotted range)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Type a wide unsnapshotted date range into "Start date" (`data-testid="job-start-date"`) and "End
   date" (`data-testid="job-end-date"`) — e.g. `2025-06-01` to `2026-07-17`
3. Click the "Start" button
4. While the job runs (Job progress panel `data-testid="job-status"` reads "running"), in a terminal
   poll `GET http://localhost:8255/api/health` about once per second for at least 60 seconds
5. At the same time, in the browser, watch the top-bar readiness badge (`data-testid="readiness-badge"`)
6. Still while the job runs, open `http://localhost:3255/backtest` in a second tab
7. After the job's "Run history" row shows "forward aggregates" among its "Refreshed:" text
   (`data-testid="aggregates-refreshed"`), reload `http://localhost:3255/backtest`

**Expected Result:**
- Step 4: every polled response returns HTTP 200 for the whole 60+ second window — no connection
  refused, no timeout, no non-200 status, no gap longer than the existing poll-interval budget
- Step 5: the badge stays at `data-state="ready"` throughout — never `data-state="unavailable"`, and
  the header is never blank or frozen
- Step 6: `/backtest` renders promptly — either normal evidence values, or the "Refreshing — showing
  the last complete evidence" banner (`data-testid="evidence-refreshing"`) — never a blank page or an
  indefinitely-frozen skeleton, even while the heavy warm runs in the background
- Step 7: `/backtest` now shows the new version's values and the "Refreshing…" banner is gone

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
| UT-J-05 | Aggregates precomputed at ingest, never on the fly (target) | regression | P1 | `/data`, `/scanner-runs`, global badge |
| UT-J-06 | Every page loads within budget | regression | P1 | 11 listed routes |
| UT-J-07 | Heavy aggregate warm never takes health/`/backtest` down (target) | regression | P1 | global badge, `/backtest`, `/data` |
| UT-J-08 | Backtest serves stored evidence, never cold-recomputes | regression | P1 | `/backtest`, `/data` |
| UT-J-09 | Background-compute activity disclosed | regression | P1 | global badge, `/data` |

**All 8 test cases are P1** — every journey in this table is named on this iteration's
`Required-still-passing journeys:` line (J-01, J-03, J-04, J-06, J-08, J-09) or its `Target
journeys:` line (J-05, J-07); per the phase's own Definition of Done, none may merge as clean
`SKIPPED`/`PASS` without fresh, non-carried-forward evidence this iteration — and per this
iteration's own `merge_ui_test_results.py` fix, a target journey (UT-J-05, UT-J-07) with zero
executed rows or an all-SKIP-only row now ALSO forces the merged headline to `BLOCKED`, the same
guarantee the required-still-passing rows already had.

**Zero NEW-surface test cases** — confirmed: no `UT-01`/`UT-02`-style new-capability case exists in
this plan, consistent with `Frontend Present: no` and "New user-facing capability: None".
