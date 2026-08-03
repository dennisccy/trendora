# Phase goal-ops-hardening-iter-43 — UI Test Plan

**Phase:** goal-ops-hardening-iter-43
**Date:** 2026-07-31
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend health URL:** http://localhost:8255/api/health

---

## Scope note (read before executing)

`Frontend Present: no` for this iteration. The phase spec's own metadata states "New user-facing
capability: None", "New information displayed: None new", "UI surface changes: None", and the dev
handoff (`docs/handoffs/goal-ops-hardening-iter-43-dev.md`) confirms zero files under
`apps/frontend/` were touched — the only "script" changed is `scripts/start-frontend.sh`, a launch
wrapper, not application code. Per the "Backend-only phase handling" rule, this test plan emits
exactly one `UT-<journey-id>` regression test case for **every journey named on EITHER** the phase
spec's `Required-still-passing journeys:` line **OR** its `Target journeys:` line.

This iteration's metadata names:
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09
- **Target journeys:** J-05, J-07

Union of both lines = 8 distinct journeys, no duplicates. This plan therefore contains **8 test
cases, all type `regression`, all Priority P1, zero NEW-surface cases** — identical journey set to
iter-42's plan (the memory-envelope owner decision unblocked the same two journeys iter-42 found
failing, and the same six journeys must be re-proven fresh rather than carried forward, since
iter-42's own passes were "photographed minutes before that iteration's outage").

**Grounding:** each test case below combines two sources — (1) the exact, checked-in automated
replay script at `runs/goal-session-ops-hardening/journey-scripts/J-<NN>.json` (canonical
URLs/testids/button roles/expected text strings, confirmed live against the current, untouched
frontend source), and (2) the fuller narrative "Steps"/"Acceptance" text for that journey in
`docs/goal.md`'s "Must-have user journeys" section (richer manual coverage than the lean automated
script alone provides). Where the two diverge in a figure (e.g. a calendar-day count), the JSON
script's asserted text is authoritative, since it is the literal string the running app renders.

**Not covered by this document (no browser-observable surface exists for these):**
- The `_BarCache.prefill` filter revert itself (`prices.py`) — a query-shape change with no UI
  surface; verified by `apps/backend/tests/test_bar_cache.py`'s byte-identity oracles (TC-1) and the
  B1 `KeyError` regression test (TC-2).
- The `start_data_job`/`start_resume_job` thread-launch guard — the failure mode
  (`RuntimeError: can't start new thread`) is only reachable via a mocked `threading.Thread.start()`
  in `apps/backend/tests/test_data_manager.py` (TC-3, TC-4); it reaches the SAME already-displayed
  Job history `status`/`message` fields every other job failure already surfaces through, so there is
  no NEW field or component to test, and the failure cannot be practically triggered through the
  browser.
- The `scripts/start-frontend.sh` HOST-GUARD block and `HOST_GUARD_MARKER_FILES` extension (TC-5) —
  a launch-script behavior (CPU affinity, thread-cap env vars), not a rendered page; verified by
  `apps/backend/tests/test_start_frontend_script.py`.
- J-07 acceptance steps 3-4 (VmPeak measurement; a synthetic memory-pressure abort via a throwaway
  process) — not observable through the UI; verified by `reports/perf-budgets.md`'s "Iteration 43"
  section and `apps/backend/tests/test_ingest_finalize_memory_pressure.py` /
  `test_ingest_finalize_fault_injection.py`.

**KNOWN OPEN RISK — read before executing UT-J-05 and UT-J-07.** This iteration's own dev handoff
discloses that a live, real-DB attempt at the full forward-aggregate warm did NOT reach a terminal
state within a 1,001-second (16.7 min) observation window this session. Memory (32.4% of the new
8192 MB cap) and availability (272/272 `/api/health` polls returned HTTP 200) both held cleanly, but
a NEW, unresolved latency finding was disclosed: 63.6% of those 272 polls exceeded the rescoped ≤2s
bounded-compute-window (BCW) budget (up to 6.6s), and the trend worsened over the window (mean 1.7s
in the first third vs 3.2s in the last third) rather than staying flat. Two unconfirmed causes are
on record (T2's `_SymbolColumns` slicing cost now applying to all 591 symbols instead of 548 post-
revert; or a self-inflicted concurrent second dispatch from a manual probe) — neither was fixed this
iteration. **Whoever executes UT-J-05 (step 9) and UT-J-07 (step 5) below must record the actual
measured numbers, not a rounded-up "it eventually returned 200" impression** — the open question
this iteration leaves is specifically about latency, not availability.

---

## Test Cases

---

### UT-J-01 — Backfill honors the requested range and explains zero-work (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`, `/scanner-runs/748`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running and reachable at
  http://localhost:8255/api/health
- No login required
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-01.json`

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Type `2026-05-02` into the "Start date" field (`data-testid="job-start-date"`)
3. Type `2026-05-03` into the "End date" field (`data-testid="job-end-date"`)
4. Click the "Start" button
5. Watch the "Job progress" panel (`data-testid="job-status"`) until it leaves the "running" state
6. Reload `http://localhost:3255/data`
7. Type `2026-05-02` into "Start date" and `2026-05-29` into "End date"
8. Click "Start" again
9. Watch "Job progress" (`data-testid="job-status"`) until it leaves "running"
10. Reload `http://localhost:3255/data`
11. Navigate to `http://localhost:3255/scanner-runs/748`

**Expected Result:**
- After step 5: the run's summary text includes "2 non-trading" (the weekend-only 2026-05-02 →
  2026-05-03 span — 0 trading-day targets, 2 non-trading days)
- After step 9: the run's summary text includes "19 already snapshotted" (re-running the full May
  range is zero-work in this DB's current state)
- Both zero-work outcomes (steps 5 and 9) render as a visually distinct explanatory badge/state — NOT
  the same plain green success badge a productive first-time run would show
- After step 10: the "Run history" table still lists BOTH runs from steps 4 and 8 — reloading does
  not clear job history, and it is never presented as "no job started this session"
- Step 11: `/scanner-runs/748` renders the text "as of 2026-05-29" with a populated leaderboard table
  (not the "No stored stock rows" empty state)

---

### UT-J-03 — No per-run range cap (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend running at http://localhost:3255, backend reachable
- Navigate to a fresh load of `/data` (no job currently running)
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-03.json`

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Type `2025-06-01` into the "Start date" field (`data-testid="job-start-date"`)
3. Type `2026-07-17` into the "End date" field (`data-testid="job-end-date"`) — a 412-calendar-day
   span
4. Click the "Start" button
5. Watch the "Job progress" panel (`data-testid="job-status"`) and the live activity line
   (`data-testid="job-live-activity"`, `data-testid="job-heartbeat"`) for at least 30 seconds
6. Once the job reaches a terminal status, reload `http://localhost:3255/data`

**Expected Result:**
- No text such as "date range too large" (or any range-cap rejection message) appears near the form
  at any point
- Step 5: the job transitions to and stays in a running state with visible heartbeat/activity
  movement — confirms the request was accepted and is chunk-executing, not rejected outright
- Step 6: the run's summary text in "Run history" includes the literal text "412 calendar days"

---

### UT-J-04 — Non-blocking boot with visible status (regression)

**Type:** regression
**Priority:** P1
**Surface:** Global readiness badge (any page), `/`, `/data`, preflight banner

**Preconditions:**
- Frontend already open at `http://localhost:3255/`
- Operator has terminal access to stop/restart the backend via `scripts/start-backend.sh` and to send
  a hard `kill`
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-04.json`

**Steps:**
1. With `http://localhost:3255/` open, stop the backend, then restart it via
   `scripts/start-backend.sh`
2. Immediately watch the top-bar readiness badge (`data-testid="readiness-badge"`) and, in a
   terminal, poll `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8255/api/health`
3. Once the badge reads "Ready", reload `http://localhost:3255/` and confirm the page text includes
   "provider: seed"
4. Navigate to `http://localhost:3255/data` and confirm the page shows a "Run history" section
5. Kill the backend process directly (`kill <pid>`, NOT a clean `scripts/start-backend.sh` stop —
   simulates a crash)
6. Watch the badge/banner again
7. Tail `logs/backend.log` around the kill
8. Restart the backend again via `scripts/start-backend.sh`; navigate to `/data`

**Expected Result:**
- Step 2: the badge passes through `data-state="loading"` or `data-state="initializing"` before
  settling on `data-state="ready"` with visible text "Ready" — the header is never blank during this
  window; the first `/api/health` HTTP 200 arrives within 5 seconds of process start
- Step 3: the dashboard renders the text "provider: seed" (confirms the backend is genuinely serving,
  not a stale cached shell)
- Step 4: `/data` renders a populated "Run history" section — not blank, not stuck loading
- Step 6: the badge shows `data-state="unavailable"` with text "Backend unavailable", and/or the
  preflight banner renders the unreachable reason — visibly distinct from the initializing
  presentation in step 2
- Step 7: the tailed log shows boot entries but the log ends abruptly with no clean-shutdown entry
  right before the gap (a killed process writes no crash line — the abrupt truncation is itself the
  evidence)
- Step 8: any job that was mid-flight at the kill now shows an explicit interrupted/error state on
  `/data` — never a still-"running" row with no living process. (Supporting evidence already on
  record: this iteration's own dev handoff exercised an abrupt `SIGTERM` + restart during its J-05
  live attempt and confirmed the interrupted run correctly read `"interrupted"`, plus a 0.489s cold
  `/data` load post-restart — a real prior data point, not a substitute for this browser-level check.)

---

### UT-J-05 — Aggregates are precomputed at ingest, never on the fly (regression, target journey)

**Type:** regression
**Priority:** P1
**Surface:** `/data`, `/scanner-runs/1882`, global readiness badge

**Preconditions:**
- Frontend running at http://localhost:3255, backend running and reachable at
  http://localhost:8255/api/health
- Operator has terminal/log access to tail `logs/backend.log` and can restart the backend via
  `scripts/start-backend.sh`
- No login required
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-05.json`
  (`default_timeout_ms: 60000` for its fast path)

**See the "KNOWN OPEN RISK" note at the top of this document before running step 9.**

**Steps:**
1. Navigate to `http://localhost:3255/data` (confirm heading "Data Manager")
2. Type `2005-04-12` into the "Start date" field (`data-testid="job-start-date"`)
3. Type `2005-04-12` into the "End date" field (`data-testid="job-end-date"`)
4. Click the "Start" button
5. While the job runs, watch the top-bar readiness badge (`data-testid="readiness-badge"`)
6. Navigate to `http://localhost:3255/scanner-runs/1882`
7. Return to `http://localhost:3255/data`
8. Find the "Run history" row for the run started in step 4
9. Read its "Refreshed:" text (`data-testid="aggregates-refreshed"`) — if it still reads "running",
   re-check every few minutes for up to 20 minutes and record the ACTUAL wall-clock time when (and
   if) it reaches a terminal state
10. Restart the backend via `scripts/start-backend.sh`; immediately load `http://localhost:3255/data`
    cold (the first request after restart)
11. Tail `logs/backend.log` around the restart and the cold `/data` request from step 10

**Expected Result:**
- Step 5: the badge stays at `data-state="ready"` throughout — never switches to
  `data-state="unavailable"` while the backfill and its finalize warm run
- Step 6: `/scanner-runs/1882` shows the text "as of 2005-04-12" with a populated leaderboard — this
  should resolve quickly (within the golden script's 60s timeout), since it does not wait on the full
  forward-aggregate warm to complete
- Step 9: the "Refreshed:" text lists at minimum "latest snapshot" and "coverage"; per J-05's full
  acceptance it should ALSO eventually list "forward aggregates" once that warm finishes. Report the
  row's literal text and the elapsed time exactly — if it is still "running" after 20 minutes, report
  that literally as an open/incomplete result, do not infer a pass
- Step 10: `/data`'s "Dataset coverage" panel (`data-testid="universe-count"`,
  `data-testid="candidate-universe-count"`) renders populated numeric values promptly, not a
  blank/error panel and not an indefinite spinner
- Step 11: the tailed log around the restart and cold `/data` request contains no line indicating a
  full-table / 3.3M-row bar prefill for that request

---

### UT-J-06 — Pages load only what they need (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`,
`/scanner-runs`, `/backtest`, `/watchlist`, `/research/regime-lab`

**Preconditions:**
- Backend running in prod mode via `scripts/start-backend.sh` (not `dev.sh`), warm (already served at
  least one request)
- Frontend running in prod mode via `scripts/start-frontend.sh` (not `dev.sh` — now HOST-GUARD-wrapped
  by this iteration's own change; confirm it still boots normally)
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-06.json`

**Steps:**
1. Navigate to `http://localhost:3255/` and note time-to-interactive — confirm text "Dashboard"
2. Navigate to `http://localhost:3255/stocks` — confirm text "Stocks"
3. Navigate to `http://localhost:3255/stocks/AAPL` — confirm text "AAPL"
4. Navigate to `http://localhost:3255/sectors` — confirm text "Sectors"
5. Navigate to `http://localhost:3255/themes` — confirm text "Themes"
6. Navigate to `http://localhost:3255/data` — confirm text "Data Manager"
7. Navigate to `http://localhost:3255/evidence` — confirm text "Evidence"
8. Navigate to `http://localhost:3255/scanner-runs` — confirm text "Scanner Runs"
9. Navigate to `http://localhost:3255/backtest` — confirm text "Backtest"
10. Navigate to `http://localhost:3255/watchlist` — confirm text "Watchlist"
11. Navigate to `http://localhost:3255/research/regime-lab` — confirm text "Research — Regime Lab"

For each page, record time-to-interactive and note any on-load API call that errors or takes
noticeably long.

**Expected Result:**
- Every page above renders its listed anchor text within its committed budget in
  `reports/perf-budgets.md`'s "Iteration 43" section — no page hangs indefinitely or shows a
  blank/error frame
- Flag explicitly (do not round to "close enough") any page whose load time exceeds its budget — pay
  particular attention to `/stocks`, `/sectors`, and `/themes`: this iteration's revert of
  `_BarCache.prefill`'s symbol filter removes the faster lazy-load path that had been routing 43
  ETF/index symbols away from the ~70-80× slower `_SymbolColumns.__getitem__` per-call cost (T2,
  carried unresolved from iter-41/42) — the revert widens T2's exposure from 548 to all 591 symbols,
  so these pages are the most likely to show a fresh regression even though T2 itself stays out of
  this iteration's scope

---

### UT-J-07 — Heavy aggregates never take the service down (regression, target journey)

**Type:** regression
**Priority:** P1
**Surface:** Global readiness badge (any page), `/backtest`, `/data`

**Scope note:** this covers J-07 acceptance steps 1-2 only (the browser/operator-observable subset).
Steps 3-4 (VmPeak measurement, a synthetic memory-pressure abort via a test hook) are not observable
through the UI — see `reports/perf-budgets.md`'s "Iteration 43" section §4 and
`apps/backend/tests/test_ingest_finalize_memory_pressure.py` / `test_ingest_finalize_fault_injection.py`.

**See the "KNOWN OPEN RISK" note at the top of this document — it applies directly to step 5 below.**

**Preconditions:**
- Frontend running at http://localhost:3255, backend running in prod mode via
  `scripts/start-backend.sh` (not `dev.sh`), reachable at http://localhost:8255/api/health
- Operator has a terminal to time-poll health, e.g.
  `curl -s -o /dev/null -w "%{http_code} %{time_total}\n" http://localhost:8255/api/health`
- A wide, not-yet-fully-snapshotted date range is available to trigger a heavy multi-date backfill and
  its forward-aggregate warm (reuse UT-J-03's `2025-06-01` → `2026-07-17`, or any multi-month
  unsnapshotted range)
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-07.json`

**Steps:**
1. Navigate to `http://localhost:3255/` — confirm text "Ready" (fast sanity anchor)
2. Navigate to `http://localhost:3255/backtest` — confirm text "n=8878"
3. Navigate to `http://localhost:3255/data` — confirm text "3508" (fast sanity anchor)
4. On `/data`, type a wide unsnapshotted date range into "Start date"
   (`data-testid="job-start-date"`) and "End date" (`data-testid="job-end-date"`), then click "Start"
   — this triggers the full-horizon forward-aggregate warm via the ingest finalize path
5. While the job runs, in a terminal run the timed curl command above once every 5-10 seconds for at
   least 5 minutes (longer if practical); log EVERY response's HTTP code AND its `time_total`
6. At the same time, watch the top-bar readiness badge (`data-testid="readiness-badge"`)
7. Still while the job runs, open `http://localhost:3255/backtest` in a second tab
8. After the "Run history" row's "Refreshed:" text (`data-testid="aggregates-refreshed"`) includes
   "forward aggregates", reload `http://localhost:3255/backtest`

**Expected Result:**
- Steps 1-3: all three golden anchors render (confirms the baseline surfaces are healthy before the
  heavy job starts)
- Step 5: EVERY polled response should return HTTP 200 (this matches the developer's own clean
  availability result — 272/272 this iteration). For `time_total`: per the rescoped budget, every
  poll should complete within 2 seconds; report the ACTUAL pass rate and max latency observed rather
  than assuming a pass — this iteration's own live measurement found 63.6% of polls exceeding 2s
  (worsening over time, up to 6.6s), and that finding is still unresolved
- Step 6: the badge stays at `data-state="ready"` throughout — never `data-state="unavailable"`
- Step 7: `/backtest` renders promptly — either normal evidence values, or the "Refreshing — showing
  the last complete evidence" banner (`data-testid="evidence-refreshing"`) — never a blank page or an
  indefinitely-frozen skeleton, even while the heavy warm runs in the background
- Step 8: `/backtest` now shows the new version's values and the "Refreshing…" banner is gone

---

### UT-J-08 — Backtest serves stored evidence, never a cold recompute (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/backtest`, `/data`

**Preconditions:**
- A forward-aggregate warm has completed at least once already for the current dataset version (so a
  "last-good" version exists to fall back to)
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-08.json`

**Steps:**
1. Navigate to `http://localhost:3255/backtest` — confirm text "Forward-tested evidence"
2. Note the served as-of date shown on the page
3. Navigate to `http://localhost:3255/data`; start a small single-day backfill on a date not yet
   snapshotted (set both "Start date" and "End date", `data-testid="job-start-date"` /
   `job-end-date`, to the same date, then click "Start")
4. While that job's finalize warm is still running (Job progress panel reads "running"), navigate back
   to `http://localhost:3255/backtest`
5. Observe the evidence panel
6. After the "Run history" row for the job lists "forward aggregates" among its refreshed aggregates
   (`data-testid="aggregates-refreshed"`), reload `http://localhost:3255/backtest`

**Expected Result:**
- Step 1: the text "Forward-tested evidence" is visible
- Steps 4-5: `/backtest` renders promptly — either normal served values from the PREVIOUS version, or
  the banner "Refreshing — showing the last complete evidence" (`data-testid="evidence-refreshing"`)
  — never a blank page or an indefinite loading skeleton waiting on a fresh compute
- Step 6: `/backtest` now shows the new version's values (a different served as-of / updated numbers
  from step 2) and the "Refreshing…" banner is gone

---

### UT-J-09 — Background-compute activity is disclosed on the badge and `/data` panel (regression)

**Type:** regression
**Priority:** P1
**Surface:** Global readiness badge (any page), `/backtest`, `/data`

**Preconditions:**
- Backend warm; at least one historical as-of exists whose forward-aggregate evidence is not yet
  complete for the current dataset version (to trigger a background-compute window on request)
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-09.json`

**Steps:**
1. Navigate to `http://localhost:3255/backtest` — confirm text "Time-machine"
2. Click the "Previous available date" button (`aria-label="Previous available date"`) enough times
   to land on a historical as-of whose evidence is not yet computed for the current dataset version
3. Confirm the page shows text "(historical)"
4. Immediately look at the top-bar badge (`data-testid="readiness-badge"`)
5. Navigate to `http://localhost:3255/data` and find the "Background compute" panel
   (`data-testid="background-compute-panel"`)
6. Read the panel's disclosure text
7. Wait for the window to complete, then re-check the badge and the panel's "Last outcome" section

**Expected Result:**
- Step 3: the page shows "(historical)" next to the selected as-of — confirms the request returned
  immediately without blocking on the background dispatch (J-08 unchanged)
- Step 4: the badge still reads "Ready" AND shows an additional accent chip
  (`data-testid="background-compute-indicator"`) — never a bare "Ready" that hides an in-flight
  compute
- Step 6: the panel lists the in-flight window with elapsed time and horizons done/total, and
  somewhere on the page the text "process-lifetime only, never persisted" is visible (confirms the
  disclosure is honest about its own scope — a restart clears it)
- Step 7: after completion, the chip disappears from the badge and the panel's "Last outcome" section
  shows the completed window's outcome with a real measured duration — never a silent failure or an
  unexplained forever-refreshing state

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-J-01 | Backfill honors requested range, explains zero-work | regression | P1 | `/data`, `/scanner-runs/748` |
| UT-J-03 | No per-run range cap | regression | P1 | `/data` |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | global badge, `/`, `/data`, preflight banner |
| UT-J-05 | Aggregates precomputed at ingest, never on the fly (target) | regression | P1 | `/data`, `/scanner-runs/1882`, global badge |
| UT-J-06 | Every page loads within budget | regression | P1 | 11 listed routes |
| UT-J-07 | Heavy aggregate warm never takes health/`/backtest` down (target) | regression | P1 | global badge, `/backtest`, `/data` |
| UT-J-08 | Backtest serves stored evidence, never cold-recomputes | regression | P1 | `/backtest`, `/data` |
| UT-J-09 | Background-compute activity disclosed | regression | P1 | global badge, `/backtest`, `/data` |

**All 8 test cases are P1** — every journey in this table is named on this iteration's
`Required-still-passing journeys:` line (J-01, J-03, J-04, J-06, J-08, J-09) or its `Target
journeys:` line (J-05, J-07); per the phase's own Definition of Done, none may merge as clean
`SKIPPED`/`PASS` without fresh, non-carried-forward evidence this iteration.

**Zero NEW-surface test cases** — confirmed: no `UT-01`/`UT-02`-style new-capability case exists in
this plan, consistent with `Frontend Present: no` and "New user-facing capability: None".

**Two test cases carry an explicit KNOWN OPEN RISK flag (UT-J-05 step 9, UT-J-07 step 5)** — both
trace to the SAME unresolved latency finding disclosed in this iteration's own dev handoff. Whoever
executes this plan should treat those two measurements as the highest-value evidence in the whole
document, and report the actual numbers observed rather than a rounded pass/fail impression.
