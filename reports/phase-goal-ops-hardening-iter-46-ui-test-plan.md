# Phase goal-ops-hardening-iter-46 — UI Test Plan

**Phase:** goal-ops-hardening-iter-46
**Date:** 2026-08-04
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3255
**Backend health URL:** http://localhost:8255/api/health

---

## Scope note (read before executing)

`Frontend Present: no` for this iteration. The phase spec's own metadata states "Frontend: None", "New
information displayed: None", "New user actions: None", and "UI surface changes: None — no new
component; the Evidence page, global readiness badge, and `/data` panels keep their existing shape and
byte-identical values." The dev handoff's changed-files list confirms **zero files under
`apps/frontend/`** changed this iteration. Every changed file is backend engine code
(`apps/backend/app/engine/research.py`, `apps/backend/app/engine/forward_testing.py`,
`apps/backend/app/engine/data_manager.py`), a backend test file (`test_research_streaming.py`,
`test_forward_testing.py`, `test_data_manager.py`), or a journey-script anchor that was **checked but NOT
modified** (`runs/goal-session-ops-hardening/journey-scripts/J-07.json` — both anchors matched live at
the dev's own check time). Per the "Backend-only phase handling" convention, this test plan emits exactly
one `UT-<journey-id>` regression test case for **every journey named on EITHER** the phase spec's
`Required-still-passing journeys:` line **OR** its `Target journeys:` line.

This iteration's metadata names:
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09
- **Target journeys:** J-05, J-07

Union of both lines = 8 distinct journeys, no duplicates — matching iter-44/45's precedent (the prior
verdict was ESCALATE, forcing full-depth + full regression again this iteration).

**Grounding:** each test case below combines (1) the checked-in automated replay script at
`runs/goal-session-ops-hardening/journey-scripts/J-<NN>.json` (canonical URLs/testids/button
roles/expected text — `git log` confirms J-01/J-03/J-04/J-06/J-08/J-09 have been unchanged since well
before iter-45, and J-05/J-07 are unchanged this iteration too), (2) this iteration's dev handoff
(`docs/handoffs/goal-ops-hardening-iter-46-dev.md`), and (3) a LIVE check of the running backend/frontend
at http://localhost:8255 / http://localhost:3255 performed while writing this plan, several hours after
the dev handoff — the shared DB has moved on since then (see KNOWN OPEN RISK). Where a figure has drifted,
the live-verified value at plan-writing time is stated explicitly, with an instruction to re-read the
actual on-screen number at execution time rather than trust either figure blindly.

**Not covered by this document (no browser-observable surface exists for these):**
- **TC-1 / TC-2** — the two refactored accumulators' live peak-size bounds
  (`_combination_observations`'s `ret_by_run_symbol`, `compute_drawdown_expectations`'s `stored_by_key`).
  Properties of server-side memory behavior with no rendered difference in any response shape — verified
  by `apps/backend/tests/test_research_streaming.py::test_combination_observations_accumulator_is_chunk_bounded`
  and `apps/backend/tests/test_forward_testing.py::test_drawdown_expectations_stored_by_key_accumulator_is_chunk_bounded`.
- **TC-3** — byte-identity of both refactors against a pinned pre-fix reference oracle. A server-side
  equality property; verified by the new tests in `test_research_streaming.py` (as_of=None + a historical
  as_of) and the pre-existing `test_drawdown_expectations_chunked_byte_identical_to_pinned_reference` in
  `test_forward_testing.py` (re-run green against the refactor, unchanged).
- **TC-5** — the two newly-guarded `logger.exception` call sites (`data_manager.py:5058`/`:5091`). Both
  are bookkeeping-failure handlers inside a rare double-failure path (a job's own persistence/checkpoint
  logging call itself raising) with no user-triggerable browser path — verified by
  `test_data_manager.py::test_fail_unlaunched_job_persistence_failure_survives_a_raising_logging_call` and
  `::test_fail_unlaunched_resume_checkpoint_rebuild_failure_survives_a_raising_logging_call` (both drive a
  textless `MemoryError()` and assert it does not escape the handler).

**KNOWN OPEN RISK — read before executing UT-J-05 and UT-J-07. This is the single most important thing in
this document, and this iteration's live state has moved even beyond what the dev handoff disclosed.**

**1. This iteration's own dev handoff reported BOTH live drills NOT MET, honestly:**
- **TC-7 (J-05):** the dev submitted `2005-05-16` (confirmed absent from `/scanner-runs` at the time) as a
  single-day backfill. It did NOT reach a terminal state within the 300s budget — still `"running"` at
  handoff time (~16+ minutes elapsed), stuck in the historical gap-fill's full membership-timeline
  recompute (not the append-forward fast path, which this iteration's diff does not extend to
  historical gaps — by design, out of scope). Not a deadlock: VmRSS was still growing slowly, one worker
  thread stayed runnable.
- **TC-4 (Evidence page under concurrent load):** while that same backfill's finalize tail ran,
  `GET /api/evidence` never returned within 40 seconds on any of 15+ attempts; `GET /api/health` degraded
  severely (several client-timeouts at 5s, up to 4.5s response times) but stayed intermittently
  reachable. Root-caused via `/proc/<pid>/task/*/stat`: exactly ONE of 31 threads was CPU-runnable
  throughout — classic GIL starvation from the SAME synchronous historical-gap-fill recompute, **not**
  memory exhaustion. Zero `MemoryError` entries in `logs/backend.log` in that window; VmRSS peaked ~6.1GB,
  well under the 8192MB cap. **This iteration's actual product change (the two accumulator bounds) was
  never implicated** — the narrower "no MemoryError-triggered outage" objective this diff targets was met;
  the stricter DoD wording ("stays within budget… stays responsive throughout") was not.

**2. A fresh, direct check performed WHILE WRITING THIS PLAN (several hours after the dev handoff, on the
now-settled DB, with NO deliberately-triggered backfill running) found the SAME symptom persists and is,
if anything, worse:**
- `GET http://localhost:8255/api/evidence` did not return within **at least 157 seconds** on a direct,
  timed check (process elapsed-time confirmed, request then killed). A follow-up attempt timed out again
  at 15 seconds.
- At the moment of this check, `GET /api/health`'s own `background_compute.active` array was **empty**
  (idle — the app's own bookkeeping reports no window in flight) and no `data_provider_runs` row was in
  `"running"` status. `GET /api/health` itself responded in 0.2s.
- **This means the multi-minute `/evidence` latency is not purely a symptom of a concurrent backfill job**
  as the dev handoff's root-cause narrative concluded — it reproduced with nothing else visibly running.
  It may be the two bounded functions' own inherent compute cost at this DB's ~30-year scale (chunking
  bounds peak memory, not necessarily wall-clock time — folding/discarding each chunk adds its own
  overhead), a lingering effect of the still-orphaned job below, or something else. **Do not assume
  either explanation without a fresh, dedicated timed check at execution time** — this is exactly the kind
  of thing this document must report literally, not round to a guess.
- For scale: the committed budget is `/evidence` ≤3s **steady-state (warm)**; the historical worst-case
  disclosed COLD-miss precedent in `reports/perf-budgets.md` (Item I, iter-41) was 73.3 seconds, a
  one-time cost since fixed. **157+ seconds with zero visible concurrent job exceeds even that disclosed
  worst case** — this is worth flagging prominently to QA/the evaluator as a new, unresolved finding, not
  a rediscovery of Item I.

**3. The dev's own TC-7 job did not cleanly resolve — it appears to have been orphaned by a backend
restart, not a completion**, per a live query of `GET /api/data`'s `runs` list performed while writing
this plan:
- `data_provider_runs` id **282** (`2005-05-16`, the dev's own TC-7 job) now shows **`status: "interrupted"`**
  (not `"ok"`, not still `"running"`), `aggregates_refreshed: null`, `finished_at:
  2026-08-04T04:30:53` — several hours after the dev handoff's own "~16+ minutes, still running" note.
  This is consistent with a backend restart (by any pipeline lane) cutting the job off mid-finalize-tail,
  not with the job ever reaching a terminal `ok`/`failed` state on its own.
  **However, the underlying data DID land**: `2005-05-16` is no longer in `/api/data`'s gap list —
  `coverage.gap_first` has advanced from `2005-05-16` to `2005-05-17`. So the snapshot + forward-return
  insert survived the interruption; only the aggregate-refresh bookkeeping never completed and the run
  record now honestly discloses `"interrupted"` rather than a false `"ok"` or a forever-stuck `"running"`
  — arguably a POSITIVE data point for J-04's "a job interrupted mid-flight shows an explicit
  interrupted/error state" acceptance class, distinct from J-05/J-07's own acceptance.
  **`2005-05-16` is therefore NO LONGER a valid "confirmed absent" target for a fresh UT-J-05 run** — pick
  a currently-absent date instead (see below).
- A **separate** recent attempt to backfill `2019-02-25` (`data_provider_runs` id **281**) **FAILED**
  outright with the message **`"MemoryError (no message)"`**, finished
  `2026-08-04T00:43:00` (about 4 hours before this plan was written). `2019-02-25` is still, as of this
  plan's writing, the LIVE `coverage.gap_last` (the nearest remaining gap to the cached boundary) —
  confirmed via a direct `GET /api/data` check. This is the SAME date `assumptions.md` iter-46 and the
  phase spec both predict as the only live-testable gap-fill case right now.

**Positive, disclosed finding carried into UT-J-07:** the dev's drill found `GET /api/health` never
returned a non-200 across the whole ~320s observation window (though several individual polls
client-timed-out or took multiple seconds) — no hard crash, no connection-refused. This is favorable
evidence for J-07's "health stays reachable" acceptance class, independent of whether it meets the
strict latency budget.

**Bottom line for whoever executes UT-J-05 and UT-J-07 below:** this iteration's DIFF (the two
accumulator bounds + two logger guards) is very likely CORRECT on its own narrow terms (no `MemoryError`
observed anywhere in the drills above, matching TC-1/TC-2/TC-3's green unit tests) — but the JOURNEY-level
acceptance criteria for J-05 and J-07 are, on the evidence gathered so far, **NOT met on this DB's current
scale**, for a reason (GIL/CPU contention from a long synchronous compute, not memory) this iteration's
own spec explicitly scoped OUT. Record the ACTUAL observed outcome; do not round either journey to a pass
because the underlying memory fix is real, and do not round it to a "regression" because the underlying
symptom (a slow synchronous call) already existed before this iteration and is not new.

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
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-01.json` (unchanged this
  iteration and since well before iter-45)
- Note: `2026-05-02`→`2026-05-03` and the wider `2026-05-02`→`2026-05-29` range are BOTH already fully
  snapshotted in the current live DB (confirmed via `GET /api/data`'s `runs` list — multiple prior `"ok"`
  completions for both ranges) — expect both steps below to resolve as zero-work, matching the script's
  own expected text

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
- After step 5: the run's summary text includes "2 non-trading" (the weekend-only span — 0 trading-day
  targets, 2 non-trading days)
- After step 9: the run's summary text includes "19 already snapshotted" (re-running the full May range
  is zero-work in this DB's current state)
- Both zero-work outcomes render as a visually distinct explanatory badge/state — NOT the same plain
  green success badge a productive first-time run would show
- After step 10: the "Run history" table still lists BOTH runs from steps 4 and 8 — reloading does not
  clear job history
- Step 11: `/scanner-runs/748` renders the text "as of 2026-05-29" with a populated leaderboard table
  (not the "No stored stock rows" empty state) — confirmed live via `GET /api/runs/748` while writing this
  plan (`asof_date: "2026-05-29"`)

---

### UT-J-03 — No per-run range cap (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend running at http://localhost:3255, backend reachable
- Navigate to a fresh load of `/data` (no job currently running — confirmed via `GET /api/health`'s
  `background_compute.active: []` at the time of writing this plan)
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-03.json` (unchanged this
  iteration and since iter-2)
- Note: this exact 412-day range is already fully snapshotted in the current live DB (`GET /api/data`'s
  `runs` list shows a clean `"ok"` completion, `dates_done: 283/283`, `already_snapshotted: 283`) — expect
  this to resolve very quickly as zero-work, not a multi-minute run

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Type `2025-06-01` into the "Start date" field (`data-testid="job-start-date"`)
3. Type `2026-07-17` into the "End date" field (`data-testid="job-end-date"`) — a 412-calendar-day span
4. Click the "Start" button
5. Watch the "Job progress" panel (`data-testid="job-status"`) and the live activity line
   (`data-testid="job-live-activity"`, `data-testid="job-heartbeat"`) for at least a few seconds
6. Once the job reaches a terminal status, reload `http://localhost:3255/data`

**Expected Result:**
- No text such as "date range too large" (or any range-cap rejection message) appears near the form at
  any point
- Step 5: the job transitions to (and, briefly, stays in) a running state — confirms the request was
  accepted, not rejected outright
- Step 6: the run's summary text in "Run history" includes the literal text "412 calendar days"

---

### UT-J-04 — Non-blocking boot with visible status (regression)

**Type:** regression
**Priority:** P1
**Surface:** Global readiness badge (any page), `/`, `/data`, preflight banner

**Preconditions:**
- Frontend already open at `http://localhost:3255/`
- Operator has terminal access to stop/restart the backend via `scripts/start-backend.sh` and to send a
  hard `kill`
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-04.json` (unchanged this
  iteration and since iter-22)
- Note: a live, un-staged example of this exact acceptance class already exists in the current DB —
  `data_provider_runs` id 282 (this iteration's own dev TC-7 job, `2005-05-16`) shows
  `status: "interrupted"` with `aggregates_refreshed: null` after an apparent mid-flight backend restart,
  yet its underlying snapshot data still landed cleanly (the date is no longer a gap) — a real precedent
  for what step 8 below should look like

**Steps:**
1. With `http://localhost:3255/` open, stop the backend, then restart it via `scripts/start-backend.sh`
2. Immediately watch the top-bar readiness badge (`data-testid="readiness-badge"`) and, in a terminal,
   poll `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8255/api/health`
3. Once the badge reads "Ready", reload `http://localhost:3255/` and confirm the page text includes
   "provider: seed"
4. Navigate to `http://localhost:3255/data` and confirm the page shows a "Run history" section
5. Kill the backend process directly (`kill <pid>`, NOT a clean `scripts/start-backend.sh` stop —
   simulates a crash)
6. Watch the badge/banner again
7. Tail `logs/backend.log` around the kill
8. Restart the backend again via `scripts/start-backend.sh`; navigate to `/data`

**Expected Result:**
- Step 2: the badge passes through `data-state="loading"` or `data-state="initializing"` before settling
  on `data-state="ready"` with visible text "Ready" — never blank; the first `/api/health` HTTP 200
  arrives within 5 seconds of process start. Note: at the time of writing this plan, readiness briefly
  read `"initializing"` with `warmup.status: "running"` even at `done==total` (89/89), then settled to
  `"ready"` within roughly a minute of the last observed change — a normal warm-up transition, not a bug,
  but worth confirming it does settle and does not stay stuck at "initializing"
- Step 3: the dashboard renders the text "provider: seed"
- Step 4: `/data` renders a populated "Run history" section — not blank, not stuck loading. Expect many
  historical rows accumulated from this session's own extensive drilling (ids into the 280s+) — this is
  expected, disclosed accumulation, not a fresh bug
- Step 6: the badge shows `data-state="unavailable"` with text "Backend unavailable", and/or the preflight
  banner renders the unreachable reason
- Step 7: the tailed log shows boot entries but ends abruptly with no clean-shutdown entry right before
  the gap
- Step 8: any job that was mid-flight at the kill now shows an explicit `"interrupted"` state on `/data`
  (never a still-"running" row with no living process) — id 282 above is a live, already-observed example
  of exactly this outcome from an EARLIER restart this session

---

### UT-J-05 — Aggregates are precomputed at ingest, never on the fly (regression, target journey)

**Type:** regression
**Priority:** P1
**Surface:** `/data`, `/scanner-runs/<new run id>`, global readiness badge

**Preconditions:**
- Frontend running at http://localhost:3255, backend running and reachable at
  http://localhost:8255/api/health
- Operator has terminal/log access to tail `logs/backend.log` and can restart the backend via
  `scripts/start-backend.sh`
- No login required
- **Before starting, confirm the chosen date is genuinely absent from `/scanner-runs`** by navigating to
  `http://localhost:3255/scanner-runs` and searching for the date, or via
  `GET http://localhost:8255/api/data` and reading `coverage.gap_last`. Do NOT use the golden script's
  baked-in default (`2005-04-12`) — it is already snapshotted (run id 258/237, both `"ok"`). Do NOT reuse
  `2005-05-16` — this iteration's own dev drill already filled it (see KNOWN OPEN RISK #3 above; it is no
  longer a gap even though its own run record reads `"interrupted"`). At the time this plan was written,
  the live-verified nearest gap was **`2019-02-25`** (`coverage.gap_last`) — the SAME date a very recent
  attempt (`data_provider_runs` id 281, finished 2026-08-04T00:43:00) already **FAILED** with
  `"MemoryError (no message)"`. Use `2019-02-25` unless a re-check at execution time shows the gap has
  since moved, in which case use whatever `coverage.gap_last` reports then.
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-05.json`
  (`default_timeout_ms: 60000` — very likely NOT to be met; see below)

**See the "KNOWN OPEN RISK" section at the top of this document — it applies directly to steps 4, 8-9
below. Retrying `2019-02-25` specifically is the single highest-value action in this whole plan: it is a
date with a DOCUMENTED recent MemoryError failure, now being retried against this iteration's own
memory-accumulator fix. Report the literal outcome (a fresh MemoryError, a different failure, a
long-running-but-eventually-successful run, or a run still going after 20 minutes) — do not round any of
these to a pass or a fail without recording exactly what happened.**

**Steps:**
1. Navigate to `http://localhost:3255/data` (confirm heading "Data Manager")
2. Type `2019-02-25` (or your freshly re-confirmed unsnapshotted date) into the "Start date" field
   (`data-testid="job-start-date"`)
3. Type the SAME date into the "End date" field (`data-testid="job-end-date"`)
4. Click the "Start" button; note the wall-clock start time
5. While the job runs, watch the top-bar readiness badge (`data-testid="readiness-badge"`)
6. In the "Run history" table, find the new row and note its run id; navigate to
   `http://localhost:3255/scanner-runs/<that id>`
7. Return to `http://localhost:3255/data`
8. Find the "Run history" row for the run started in step 4
9. Read its "Refreshed:" text (`data-testid="aggregates-refreshed"`). Given the SAME date already failed
   once with a MemoryError (run id 281) and every remaining gap is a historical gap-fill (out of this
   iteration's accelerated-path scope), expect either: (a) a fresh failure — check whether it is now a
   MemoryError again or something else, and whether `logs/backend.log` names it explicitly; (b) the row
   still reading "running" well past the 300-second TC-7 budget, mirroring this iteration's own dev drill
   of the adjacent `2005-05-16` date; or (c) an actual `"ok"` completion. Check every few minutes for up to
   20 minutes and record the ACTUAL wall-clock time and terminal state
10. Restart the backend via `scripts/start-backend.sh`; immediately load `http://localhost:3255/data` cold
    (the first request after restart)
11. Tail `logs/backend.log` around the restart and the cold `/data` request from step 10

**Expected Result:**
- Step 5: the badge stays at `data-state="ready"` throughout — never switches to `data-state="unavailable"`
  while the backfill runs (this is the ONE part of J-05/J-07's acceptance this session's drilling has
  found the most consistent evidence for)
- Step 6: IF the scan stage itself completes (distinct from the finalize/aggregate tail), the scanner-run
  page shows the text "as of 2019-02-25" (or your substitute date) with a populated leaderboard. Given the
  same date's prior attempt failed with a MemoryError before any snapshot was created
  (`snapshots_created: 0` on run 281), this step may simply have nothing to navigate to yet if the SAME
  failure recurs — record what actually happens rather than assuming the scan stage always resolves first
- Step 9: **record the literal observed text/outcome and elapsed time — do not assume pass or fail.**
  Given this iteration's own accumulator-bound fix targets exactly the memory shape that caused run 281's
  MemoryError, a clean pass here (no repeat MemoryError, "Refreshed:" eventually lists "latest snapshot",
  "coverage", and "forward aggregates") would be a strong, concrete, positive signal for this iteration's
  product change — but per the KNOWN OPEN RISK section, a GIL/CPU-contention stall (not a MemoryError) is
  also a plausible, already-disclosed outcome given the SAME class of job. Either outcome is honest
  evidence; report it exactly, and flag it to QA/the evaluator as the reviewer's/dev's own scope note
  already anticipates
- Step 10: `/data`'s "Dataset coverage" panel (`data-testid="universe-count"`,
  `data-testid="candidate-universe-count"`) renders populated numeric values promptly, not a blank/error
  panel and not an indefinite spinner
- Step 11: the tailed log around the restart and cold `/data` request contains no line indicating a
  full-table / multi-million-row bar prefill for that request

---

### UT-J-06 — Pages load only what they need (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`,
`/scanner-runs`, `/backtest`, `/watchlist`, `/research/regime-lab`

**Preconditions:**
- Backend running in prod mode via `scripts/start-backend.sh` (not `dev.sh`), warm (already served at
  least one request)
- Frontend running in prod mode via `scripts/start-frontend.sh` (not `dev.sh`)
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-06.json` (unchanged this
  iteration and since iter-33)
- **Note:** at the time this plan was written, a direct `GET /api/evidence` check took 157+ seconds to
  return (see KNOWN OPEN RISK #2) with no concurrent job running. If `/evidence` (step 7 below) is
  similarly slow when you reach it, this is a REAL, currently-live finding worth recording precisely
  (elapsed time), not silently accepted as "the page is just slow" — it is the single biggest open
  question this plan carries into QA

**Steps:**
1. Navigate to `http://localhost:3255/` and note time-to-interactive — confirm text "Dashboard"
2. Navigate to `http://localhost:3255/stocks` — confirm text "Stocks"
3. Navigate to `http://localhost:3255/stocks/AAPL` — confirm text "AAPL"
4. Navigate to `http://localhost:3255/sectors` — confirm text "Sectors"
5. Navigate to `http://localhost:3255/themes` — confirm text "Themes"
6. Navigate to `http://localhost:3255/data` — confirm text "Data Manager"
7. Navigate to `http://localhost:3255/evidence` — confirm text "Evidence"; **time this specific
   navigation** (start a stopwatch on click, stop it when the claim rows or an error state render)
8. Navigate to `http://localhost:3255/scanner-runs` — confirm text "Scanner Runs"
9. Navigate to `http://localhost:3255/backtest` — confirm text "Backtest"
10. Navigate to `http://localhost:3255/watchlist` — confirm text "Watchlist"
11. Navigate to `http://localhost:3255/research/regime-lab` — confirm text "Research — Regime Lab"

For each page, record time-to-interactive and note any on-load API call that errors or takes noticeably
long.

**Expected Result:**
- Every page renders its listed anchor text within its committed budget in `reports/perf-budgets.md` — no
  page hangs indefinitely or shows a blank/error frame. This iteration's diff touches
  `_combination_observations` and `compute_drawdown_expectations`, BOTH of which feed `/evidence`'s
  serving path (`GET /api/evidence`) — so, unlike most prior iterations' UT-J-06, this page's load time IS
  directly relevant to this iteration's own change and should be reported precisely, not assumed unchanged
- Step 7 specifically: either the page renders the 7 claim rows (`data-testid="evidence-claim-list"`,
  `data-testid="evidence-claim-row"`) promptly, OR it takes an extended time (record exact seconds) before
  showing them or an error state — either outcome must be reported with a real number, given the KNOWN
  OPEN RISK finding above
- Flag explicitly (do not round to "close enough") any page whose load time regresses versus the last
  recorded budget

---

### UT-J-07 — Heavy aggregates never take the service down (regression, target journey)

**Type:** regression
**Priority:** P1
**Surface:** Global readiness badge (any page), `/backtest`, `/evidence`, `/data`

**Scope note:** this covers J-07's browser/operator-observable acceptance PLUS this iteration's own new
DoD item TC-4 (`GET /api/evidence` under concurrent load — the Evidence page is J-05's blueprint home per
`state/blueprint.md`, but TC-4 and J-07 share the exact same "heavy job + service resilience" theme, so
both are exercised here rather than splitting into a 9th test case). VmPeak measurement and the synthetic
memory-pressure abort (J-07's steps 3-4) are not browser-observable — see
`apps/backend/tests/test_ingest_finalize_memory_pressure.py` /
`test_ingest_finalize_fault_injection.py`.

**See the "KNOWN OPEN RISK" section at the top of this document in full — it applies to nearly every step
below.**

**Preconditions:**
- Frontend running at http://localhost:3255, backend running in prod mode via
  `scripts/start-backend.sh` (not `dev.sh`), reachable at http://localhost:8255/api/health
- Operator has a terminal to time-poll health, e.g.
  `curl -s -o /dev/null -w "%{http_code} %{time_total}\n" http://localhost:8255/api/health`, and to time
  the evidence endpoint, e.g.
  `curl -s -o /dev/null -w "%{http_code} %{time_total}\n" http://localhost:8255/api/evidence`
- A wide, not-yet-fully-snapshotted date range is available to trigger a heavy multi-date backfill and its
  forward-aggregate warm. `2019-01-01`→`2019-02-25` still spans genuine gaps (confirmed live via
  `coverage.gap_last = 2019-02-25`); re-check `GET /api/data`'s `coverage.gaps_preview` if this has since
  changed
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-07.json`. Its two committed
  anchors are `"n=14647"` (step 2, `/backtest`) and `"2532"` (step 3, `/data`) — **both were checked live
  by the dev before the TC-7 drill and matched at that time.** A fresh check performed while writing this
  plan found: `n=14647` STILL matches exactly (confirmed via `GET /api/backtest`'s
  `evidence_by_horizon.60.by_bucket[0].n`); the "Backfill gaps" figure is now **2531** (one FEWER than the
  committed `2532`), because the dev's own TC-7 drill (`2005-05-16`) landed its snapshot after the anchor
  was captured. Expect this number to have possibly moved again by execution time — read the actual figure
  shown and treat an exact match OR a plausibly-nearby number as a PASS for "renders a real, current
  count"; treat a blank panel, an error, or a wildly different number as a FAIL

**Steps:**
1. Navigate to `http://localhost:3255/` — confirm text "Ready" (fast sanity anchor)
2. Navigate to `http://localhost:3255/backtest` — confirm text "n=14647" (this is a byte-identity
   guarantee this iteration's own refactor is contractually required to preserve — a mismatch here would
   be a genuine regression, not drift)
3. Navigate to `http://localhost:3255/data` — look for the "Backfill gaps" stat (the labeled number under
   "Backfill gaps"). Read the actual number shown and record it — see the Preconditions note above for how
   to score it
4. **Before triggering any job**, navigate to `http://localhost:3255/evidence` and time how long it takes
   to render the 7 claim rows (`data-testid="evidence-claim-list"`) or an error state. Record the exact
   elapsed time. This establishes a BASELINE — a direct API check while writing this plan found this can
   take 157+ seconds even with nothing else running (see KNOWN OPEN RISK #2), so this step matters on its
   own, independent of the heavy job triggered next
5. Back on `/data`, type the wide unsnapshotted date range from Preconditions into "Start date"
   (`data-testid="job-start-date"`) and "End date" (`data-testid="job-end-date"`), then click "Start".
   This triggers the full-horizon forward-aggregate warm via the ingest finalize path
6. While the job runs, in a terminal run the timed health curl command above once every 5-10 seconds for
   at least 5 minutes; log EVERY response's HTTP code AND its `time_total`
7. At the same time, watch the top-bar readiness badge (`data-testid="readiness-badge"`)
8. Still while the job runs, open `http://localhost:3255/backtest` in a second tab, and separately time a
   fresh `GET http://localhost:8255/api/evidence` call (or reload `/evidence` in a third tab and time it)
9. After the "Run history" row's "Refreshed:" text (`data-testid="aggregates-refreshed"`) includes "forward
   aggregates", reload `http://localhost:3255/backtest`. Per the KNOWN OPEN RISK note, if the range
   includes a historical gap-fill this may not happen within a short observation window — if the row still
   reads "running" after 20+ minutes, record that literally rather than waiting indefinitely

**Expected Result:**
- Steps 1-2: both anchors render (confirms the baseline surfaces are healthy before the heavy job starts)
- Step 3: a real numeric "Backfill gaps" value renders
- Step 4 (baseline, no job running): report the ACTUAL elapsed time for `/evidence` to render. This
  iteration's own dev drill did not test this baseline case (it only tested `/evidence` WHILE a job ran) —
  this plan's own live check found it slow (157+s) even at baseline, so this step's result is new,
  first-class evidence, not a formality
- Step 6: the dev's own drill found EVERY polled `/api/health` response returned HTTP 200 across a ~320s
  observation window (though several individual polls took multiple seconds or client-timed-out at 5s) —
  report the ACTUAL pass rate and any latency spikes rather than assuming a clean pass; any non-200
  response is worth flagging as new
- Step 7: the badge stays at `data-state="ready"` throughout — never `data-state="unavailable"`
- Step 8: the dev's own drill found `GET /api/evidence` did NOT return within 40 seconds on any of 15+
  attempts while a heavy job ran; expect the same or worse, and record the actual elapsed time (or
  timeout) observed. `/backtest` itself should render promptly — either normal evidence values, or the
  "Refreshing — showing the last complete evidence" banner (`data-testid="evidence-refreshing"`) — never a
  blank page or an indefinitely-frozen skeleton (at the time of writing, `/backtest`'s `evidence_status` is
  already `"refreshing"` from earlier drilling this session — this is expected, not new)
- Step 9: `/backtest` now shows the new version's values and the "Refreshing…" banner is gone — OR, per
  the KNOWN OPEN RISK note, the row may still read "running" well past 20 minutes; report the literal
  state rather than waiting indefinitely or assuming failure

---

### UT-J-08 — Backtest serves stored evidence, never a cold recompute (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/backtest`, `/data`

**Preconditions:**
- A forward-aggregate warm has completed at least once already for the current dataset version — already
  true right now: `GET /api/backtest` currently serves `evidence_status="refreshing"` with the last-good
  figures (`evidence_asof: "2026-07-30"`, Bucket A `n=14647`), a live, ready-made example of exactly the
  behavior this test verifies
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-08.json` (unchanged this
  iteration and since iter-22)

**Steps:**
1. Navigate to `http://localhost:3255/backtest` — confirm text "Forward-tested evidence"
2. Note the served as-of date and evidence figures shown on the page right now
3. Navigate to `http://localhost:3255/data`; start a small single-day backfill on a date not yet
   snapshotted (set both "Start date" and "End date", `data-testid="job-start-date"` / `job-end-date`, to
   `2019-02-25` — reuse UT-J-05's target if that test already ran and this date is still unfilled — then
   click "Start")
4. While that job's finalize warm is still running (Job progress panel reads "running"), navigate back to
   `http://localhost:3255/backtest`
5. Observe the evidence panel
6. After the "Run history" row for the job lists "forward aggregates" among its refreshed aggregates
   (`data-testid="aggregates-refreshed"`), reload `http://localhost:3255/backtest`. Per this iteration's
   disclosed finding (see KNOWN OPEN RISK), a gap-fill's finalize tail can take well over 15 minutes to
   reach this state — if it has not completed within a reasonable wait, it is acceptable to confirm steps
   4-5's behavior thoroughly and record step 6 as "not reached within the observation window"

**Expected Result:**
- Step 1: the text "Forward-tested evidence" is visible
- Steps 4-5: `/backtest` renders promptly — either normal served values from the PREVIOUS version, or the
  banner "Refreshing — showing the last complete evidence" (`data-testid="evidence-refreshing"`) — never a
  blank page or an indefinite loading skeleton
- Step 6 (if reached): `/backtest` now shows the new version's values (a different served as-of / updated
  numbers from step 2) and the "Refreshing…" banner is gone

---

### UT-J-09 — Background-compute activity is disclosed on the badge and `/data` panel (regression)

**Type:** regression
**Priority:** P1
**Surface:** Global readiness badge (any page), `/backtest`, `/data`

**Preconditions:**
- Backend warm; at least one historical as-of exists whose forward-aggregate evidence is not yet complete
  for the current dataset version — currently true (`evidence_status="refreshing"` is already being
  served, confirmed live)
- Canonical golden script: `runs/goal-session-ops-hardening/journey-scripts/J-09.json` (unchanged this
  iteration and since iter-24)

**Steps:**
1. Navigate to `http://localhost:3255/backtest` — confirm text "Time-machine"
2. Click the "Previous available date" button (`aria-label="Previous available date"`) enough times to
   land on a historical as-of whose evidence is not yet computed for the current dataset version
3. Confirm the page shows text "(historical)"
4. Immediately look at the top-bar badge (`data-testid="readiness-badge"`)
5. Navigate to `http://localhost:3255/data` and find the "Background compute" panel
   (`data-testid="background-compute-panel"`)
6. Read the panel's disclosure text
7. Wait for the window to complete, then re-check the badge and the panel's "Last outcome" section

**Expected Result:**
- Step 3: the page shows "(historical)" next to the selected as-of — confirms the request returned
  immediately without blocking on the background dispatch
- Step 4: the badge still reads "Ready" AND shows an additional accent chip
  (`data-testid="background-compute-indicator"`) whenever a window is actually in flight — as of this
  plan's writing `GET /api/health`'s `background_compute.active` array is empty (idle), so if no window is
  currently in flight when you reach this step, trigger one first (e.g. via UT-J-05/UT-J-07's backfill) or
  note the idle state honestly rather than reporting a false PASS
- Step 6: when a window IS in flight, the panel lists it with elapsed time and horizons done/total, and
  somewhere on the page the text "process-lifetime only, never persisted" is visible
- Step 7: after completion, the chip disappears from the badge and the panel's "Last outcome" section
  shows the completed window's outcome with a real measured duration — never a silent failure or an
  unexplained forever-refreshing state. If the window does not complete within a practical wait (see the
  KNOWN OPEN RISK note), record that honestly

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-J-01 | Backfill honors requested range, explains zero-work | regression | P1 | `/data`, `/scanner-runs/748` |
| UT-J-03 | No per-run range cap | regression | P1 | `/data` |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | global badge, `/`, `/data`, preflight banner |
| UT-J-05 | Aggregates precomputed at ingest, never on the fly (target) | regression | P1 | `/data`, `/scanner-runs/<new id>`, global badge |
| UT-J-06 | Every page loads within budget | regression | P1 | 11 listed routes |
| UT-J-07 | Heavy aggregate warm never takes health/`/backtest`/`/evidence` down (target, + TC-4) | regression | P1 | global badge, `/backtest`, `/evidence`, `/data` |
| UT-J-08 | Backtest serves stored evidence, never cold-recomputes | regression | P1 | `/backtest`, `/data` |
| UT-J-09 | Background-compute activity disclosed | regression | P1 | global badge, `/backtest`, `/data` |

**All 8 test cases are P1** — every journey in this table is named on this iteration's
`Required-still-passing journeys:` line (J-01, J-03, J-04, J-06, J-08, J-09) or its `Target journeys:`
line (J-05, J-07); per the phase's own Definition of Done, none may merge as clean `SKIPPED`/`PASS`
without fresh, non-carried-forward evidence this iteration, and TC-9 (this iteration's regression-replay
scenario) requires a unique, checksum-distinct evidence screenshot per journey — no two journeys sharing
one file.

**Zero NEW-surface test cases** — confirmed: no `UT-01`/`UT-02`-style new-capability case exists in this
plan, consistent with `Frontend Present: no`, zero changed files under `apps/frontend/`, and "New
user-facing capability: None".

**Every test case in this plan carries at least an indirect KNOWN OPEN RISK note; UT-J-05, UT-J-06 (step
7), and UT-J-07 carry it directly.** All trace to the SAME disclosed limitation this iteration's own dev
handoff reported honestly (NOT MET on TC-4 and TC-7's strict acceptance wording, root-caused to GIL/CPU
contention from a long synchronous historical-gap-fill recompute — a pre-existing, out-of-scope mechanism,
not a regression this diff introduced) PLUS a fresh, MORE concerning live finding from writing this plan:
`GET /api/evidence` took 157+ seconds to respond with NO concurrent job visibly running at all. Whoever
executes this plan should treat UT-J-05's actual measured elapsed time and UT-J-07 step 4's baseline
`/evidence` timing as the two highest-value pieces of evidence in the whole document, and report the
actual numbers observed rather than a rounded pass/fail impression.
