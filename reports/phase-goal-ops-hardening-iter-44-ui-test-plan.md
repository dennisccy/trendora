# Phase goal-ops-hardening-iter-44 — UI Test Plan

**Phase:** goal-ops-hardening-iter-44
**Date:** 2026-08-03
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3255
**Backend health URL:** http://localhost:8255/api/health

---

## Scope note (read before executing)

`Frontend Present: no` for this iteration. The phase spec's own metadata states "New user-facing
capability: None", "New information displayed: None planned", "New user actions: None", and "UI
surface changes: None", and `git diff --stat HEAD` confirms **zero files under `apps/frontend/`**
changed this iteration (`apps/frontend/tsconfig.json` was checked and confirmed already clean — no
revert was needed, unlike iter-43). Every changed file this iteration is a backend script
(`incredible_auto_dev/scripts/start-backend.sh`), backend API/engine code
(`apps/backend/app/api/data.py`, `apps/backend/app/engine/data_manager.py`), or backend tests/reports.
Per the "Backend-only phase handling" rule, this test plan emits exactly one `UT-<journey-id>`
regression test case for **every journey named on EITHER** the phase spec's
`Required-still-passing journeys:` line **OR** its `Target journeys:` line.

This iteration's metadata names:
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09
- **Target journeys:** J-05, J-07

Union of both lines = 8 distinct journeys, no duplicates — the same journey set as iter-43's plan
(the prior evaluator verdict was ESCALATE, which triggers full-depth + full six-journey regression
again this iteration).

**Grounding:** each test case below combines two sources — (1) the exact, checked-in automated
replay script at `runs/goal-session-ops-hardening/journey-scripts/J-<NN>.json` (canonical
URLs/testids/button roles/expected text strings — confirmed unchanged from iter-43 via `git log`
against both `J-05.json` and `J-07.json`, whose last content-changing commit predates iter-43), and
(2) the fuller narrative "Steps"/"Acceptance" text for that journey in `docs/goal.md`'s "Must-have
user journeys" section. Where the two diverge in a figure, the JSON script's asserted text is
authoritative — it is the literal string the running app renders.

**Not covered by this document (no browser-observable surface exists for these):**
- The `ServerOpsCfg` launcher-flag wiring (`start-backend.sh` — TC-1/TC-2) — a process-launch and
  signal-handling behavior, not a rendered page; verified by
  `apps/backend/tests/test_start_backend_script.py`'s new
  `test_start_backend_wires_server_ops_cfg_flags_into_uvicorn_cmdline` (checks the REAL launched
  process's `/proc/<pid>/cmdline`) and
  `test_start_backend_self_terminates_on_sigterm_with_stuck_background_task`.
- The live SIGUSR1 all-thread diagnostic itself (TC-3/TC-4) — an operator-triggered
  `TRENDORA_DIAG_FAULTHANDLER_SIGUSR1=1` + `kill -USR1 <pid>` diagnostic tool, not something a
  browser user can see or trigger; the verbatim stack dumps naming the blocked calls
  (`_excluded_counts_by_date`'s `resolve_with_reasons` loop; `compute_forward_aggregates`'s
  bounded-slice read) are recorded in `reports/perf-budgets.md`'s "Iteration 44" §2 and the dev
  handoff.
- `POST /data/jobs/{run_id}/retry`'s new 503 parity (TC-9) — reachable through the existing "Retry"
  button on `/data`'s Run History table for a `failed`/`partial` job, but the failure mode itself
  (`RuntimeError`/`MemoryError` from a thread-launch failure) is not practically triggerable through
  the browser — it needs a mocked `threading.Thread.start()`, exactly as iter-43's equivalent
  `start_job`/`resume_job` guard was. It renders through the SAME already-displayed error surface
  every other job-launch failure uses, so there is no NEW field or component to test; verified by
  `apps/backend/tests/test_api_data.py`'s new `test_retry_thread_launch_failure_is_503`.
- `_run_job`'s failed-job message honesty fix (TC-10) — surfaces through the existing Run History
  "message" text for a job that fails via the outer exception handler, but a genuine `_run_job`
  failure is not practically triggerable through the browser either; verified by
  `apps/backend/tests/test_data_manager.py`'s new
  `test_run_job_outer_exception_preserves_real_message_not_final_summary` and
  `test_run_job_normal_completion_still_gets_final_summary` (confirms a normally-completed job's
  message text is byte-identical to before).

**KNOWN OPEN RISK — read before executing UT-J-05 and UT-J-07.** This iteration's own dev handoff
and `reports/perf-budgets.md` §2 disclose that the `horizons_done: 0/5` stall from iter-43 is now
**diagnosed with two live, corroborating SIGUSR1 stack dumps** (~888s apart) naming the exact blocked
calls — but it is **NOT fixed**. The named root cause: every ingest that bumps the global
`dataset_version` forces `_excluded_counts_by_date` to fully recompute membership history over
**every** `ScannerRun.asof_date` ever created (2,860+ rows) × the ~591-symbol candidate pool, even
for a single-day backfill — this recompute runs *before* the forward-aggregates loop, inside the
same job's finalize tail. Both this iteration's live drill (~1,058s, two concurrent heavy computes)
and its clean single-trigger re-measurement (600s observation window) left their backfill job's
finalize tail **still running when observation ended** — neither reached a terminal `ok`/`partial`
state. **The user-visible part (the new day's data + scanner-run leaderboard) still finishes in well
under a minute** — it is specifically the background "Refreshed: forward aggregates" completion and
the Background Compute panel's in-flight window that can run 15+ minutes. Availability held cleanly
this iteration: 240/240 `/api/health` polls returned HTTP 200 in the clean re-measurement (0 non-200
across the whole 600s window), and the port never went connection-refused even in the more severe
1,058s two-concurrent-compute diagnostic run — a clear improvement over iter-43's total outage.
Latency also improved: 93.3% of polls stayed within the rescoped ≤2s budget (max 2.354s) in the clean
re-measurement, versus iter-43's 63.6% miss rate — but 6.7% of polls still exceeded 2s, so this is a
disclosed partial improvement, not a closed finding. **Whoever executes UT-J-05 (steps 8-9) and
UT-J-07 (step 5) below must record the actual measured numbers and actual elapsed time to any
terminal state, not a rounded-up "it eventually finished" impression** — and must expect the
finalize tail may still be running when the observation window ends; that is the honestly-disclosed,
current behavior, not necessarily a fresh bug.

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
  evidence). Note: this step is a hard `kill`, not a `SIGTERM`, so it does NOT exercise this
  iteration's new graceful-shutdown wiring (TC-1/TC-2) — that is covered separately by the automated
  subprocess test named in "Not covered" above, not by this browser journey.
- Step 8: any job that was mid-flight at the kill now shows an explicit interrupted/error state on
  `/data` — never a still-"running" row with no living process.

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
- Before starting, confirm the chosen date is genuinely absent from `/scanner-runs` (per this
  iteration's own TC-12 requirement — do NOT assume the golden script's default date
  `2005-04-12` is still unsnapshotted; this session's DB has accumulated 2,860+ scanner runs across
  43 prior iterations, and this iteration's own dev handoff had to pick `2019-02-28`/`2019-02-27`
  specifically because they were confirmed absent). Check by navigating to
  `http://localhost:3255/scanner-runs` and searching for the date, or via
  `GET /api/scanner-runs?asof_date=<date>`. If `2005-04-12` is already listed, pick any other
  historical trading day (e.g. `2019-02-26`) and use its date in place of `2005-04-12` and its
  resulting run ID in place of `1882` below.
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-05.json`
  (`default_timeout_ms: 60000` for its fast path)

**See the "KNOWN OPEN RISK" note at the top of this document before running steps 8-9.**

**Steps:**
1. Navigate to `http://localhost:3255/data` (confirm heading "Data Manager")
2. Type `2005-04-12` (or your confirmed-unsnapshotted substitute date) into the "Start date" field
   (`data-testid="job-start-date"`)
3. Type the SAME date into the "End date" field (`data-testid="job-end-date"`)
4. Click the "Start" button
5. While the job runs, watch the top-bar readiness badge (`data-testid="readiness-badge"`)
6. Navigate to `http://localhost:3255/scanner-runs/1882` (or the new run's actual ID if you
   substituted a different date — find it in the "Run history" table's row for the run started in
   step 4)
7. Return to `http://localhost:3255/data`
8. Find the "Run history" row for the run started in step 4
9. Read its "Refreshed:" text (`data-testid="aggregates-refreshed"`) — per this iteration's own
   disclosed finding, this may still read "running" for 15+ minutes after the new day's data and
   scanner-run page already show correctly (step 6 should resolve in well under a minute
   independently). If it still reads "running" after checking, re-check every few minutes for up to
   20 minutes and record the ACTUAL wall-clock time when (and if) it reaches a terminal state — do
   not assume it is stuck just because it has not finished yet
10. Restart the backend via `scripts/start-backend.sh`; immediately load `http://localhost:3255/data`
    cold (the first request after restart)
11. Tail `logs/backend.log` around the restart and the cold `/data` request from step 10

**Expected Result:**
- Step 5: the badge stays at `data-state="ready"` throughout — never switches to
  `data-state="unavailable"` while the backfill and its finalize warm run
- Step 6: the scanner-run page shows the text "as of <your date>" with a populated leaderboard —
  this should resolve quickly (within the golden script's 60s timeout), since it does not wait on the
  full forward-aggregate/membership-timeline warm to complete (confirmed this iteration:
  `dates_done: 1/1`, `snapshots_created: 1` complete within the create-once scan stage, unaffected by
  the disclosed finalize-tail slowness)
- Step 9: the "Refreshed:" text lists at minimum "latest snapshot" and "coverage". Per this
  iteration's own disclosed finding, it may still read "running" at the 20-minute mark — report the
  row's literal text and the elapsed time exactly. If it does eventually complete, it should ALSO
  list "forward aggregates". Either outcome (terminal completion with the timing recorded, or an
  honest still-"running" state at 20 minutes) is consistent with this iteration's disclosed,
  unresolved TC-4 finding — do not infer a silent pass or fail; report the literal observed state.
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
  least one request) — note this iteration's launcher now applies
  `--limit-concurrency`/`--timeout-keep-alive`/`--timeout-graceful-shutdown`, so confirm the backend
  is reachable normally before timing pages
- Frontend running in prod mode via `scripts/start-frontend.sh` (not `dev.sh`)
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
  `reports/perf-budgets.md`'s "Iteration 44" section — no page hangs indefinitely or shows a
  blank/error frame
- Flag explicitly (do not round to "close enough") any page whose load time exceeds its budget —
  `/stocks`, `/sectors`, and `/themes` remain the pages most exposed to the still-unresolved T2
  (`_SymbolColumns.__getitem__`/`bars_asof`) slicing cost, which this iteration's live diagnostic
  newly CONFIRMED as a real contributor (inside `resolve_with_reasons`'s bar lookups during the
  membership-timeline scan) rather than an unconfirmed hypothesis — no code fix shipped for it this
  iteration, so no change in these pages' load times is expected from this iteration's diff, but any
  observed regression should still be flagged

---

### UT-J-07 — Heavy aggregates never take the service down (regression, target journey)

**Type:** regression
**Priority:** P1
**Surface:** Global readiness badge (any page), `/backtest`, `/data`

**Scope note:** this covers J-07 acceptance steps 1-2 only (the browser/operator-observable subset).
Steps 3-4 (VmPeak measurement, a synthetic memory-pressure abort via a test hook) are not observable
through the UI — see `reports/perf-budgets.md`'s "Iteration 44" §4 and
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
   "forward aggregates", reload `http://localhost:3255/backtest`. Per the KNOWN OPEN RISK note, this
   may not happen within a short observation window this iteration — if the row still reads "running"
   after 20+ minutes, record that literally rather than waiting indefinitely.

**Expected Result:**
- Steps 1-3: all three golden anchors render (confirms the baseline surfaces are healthy before the
  heavy job starts)
- Step 5: this iteration's own clean single-trigger re-measurement found EVERY polled response
  returned HTTP 200 across a 600s/240-poll window (zero non-200, zero connection failures) — expect
  the same. For `time_total`: the same re-measurement found 93.3% of polls completed within the
  rescoped ≤2s budget (max observed 2.354s) — an improvement over iter-43's 63.6% miss rate, but NOT
  a clean 100%. Report the ACTUAL pass rate and max latency observed rather than assuming a pass;
  values in the same range (roughly 90-95% within budget) are consistent with this iteration's
  disclosed, still-open finding — do not treat a handful of over-budget polls as a fresh regression
  on their own, but DO flag anything meaningfully worse (e.g. non-200 responses, or latency spikes
  well above ~2.5s)
- Step 6: the badge stays at `data-state="ready"` throughout — never `data-state="unavailable"`
- Step 7: `/backtest` renders promptly — either normal evidence values, or the "Refreshing — showing
  the last complete evidence" banner (`data-testid="evidence-refreshing"`) — never a blank page or an
  indefinitely-frozen skeleton, even while the heavy warm runs in the background. This iteration's own
  clean re-measurement confirmed a concurrent cached `/api/backtest` read returns HTTP 200 in ~0.16s
  with `evidence_status="refreshing"` (honestly served from the last-good version, not a cold
  recompute)
- Step 8: `/backtest` now shows the new version's values and the "Refreshing…" banner is gone — OR,
  per the KNOWN OPEN RISK note, the row may still read "running" well past 20 minutes; report the
  literal state rather than waiting indefinitely or assuming failure

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
   (`data-testid="aggregates-refreshed"`), reload `http://localhost:3255/backtest`. Per this
   iteration's disclosed finding (see KNOWN OPEN RISK), the finalize tail can now take 15+ minutes to
   reach this state — if it has not completed within a reasonable wait, it is acceptable to confirm
   steps 4-5's behavior thoroughly and record step 6 as "not reached within the observation window"
   rather than waiting indefinitely.

**Expected Result:**
- Step 1: the text "Forward-tested evidence" is visible
- Steps 4-5: `/backtest` renders promptly — either normal served values from the PREVIOUS version, or
  the banner "Refreshing — showing the last complete evidence" (`data-testid="evidence-refreshing"`)
  — never a blank page or an indefinite loading skeleton waiting on a fresh compute
- Step 6 (if reached): `/backtest` now shows the new version's values (a different served as-of /
  updated numbers from step 2) and the "Refreshing…" banner is gone

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
  disclosure is honest about its own scope — a restart clears it). This iteration's own live
  diagnostic confirms `horizons_done` can legitimately stay at "0/5" for many minutes on a genuinely
  slow (not stuck) computation — the panel should still show live elapsed-time movement even while
  `horizons_done` itself has not incremented yet
- Step 7: after completion, the chip disappears from the badge and the panel's "Last outcome" section
  shows the completed window's outcome with a real measured duration — never a silent failure or an
  unexplained forever-refreshing state. If the window does not complete within a practical wait,
  record that honestly (matches this iteration's own disclosed finding that a full-horizon warm can
  run well past 15 minutes)

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
`SKIPPED`/`PASS` without fresh, non-carried-forward evidence this iteration, and TC-13 requires a
unique, checksum-distinct evidence screenshot per journey — no two journeys sharing one file.

**Zero NEW-surface test cases** — confirmed: no `UT-01`/`UT-02`-style new-capability case exists in
this plan, consistent with `Frontend Present: no`, zero changed files under `apps/frontend/`, and
"New user-facing capability: None".

**Two test cases carry an explicit KNOWN OPEN RISK flag (UT-J-05 steps 8-9, UT-J-07 step 5, UT-J-08
step 6, UT-J-09 step 7)** — all trace to the SAME diagnosed-but-unfixed finalize-tail slowness this
iteration named for the first time with live evidence. Whoever executes this plan should treat those
measurements as the highest-value evidence in the whole document, and report the actual numbers/
elapsed times observed rather than a rounded pass/fail impression.
