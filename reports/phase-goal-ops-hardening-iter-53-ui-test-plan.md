# Phase goal-ops-hardening-iter-53 — UI Test Plan

**Phase:** goal-ops-hardening-iter-53
**Date:** 2026-08-08
**Written by:** ui-impact-analyst (combined mode — standing in for ui-test-designer)
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255

---

## Before you start

- Zero frontend files changed this iteration (`Frontend Present: no` in `plan.md`). Every test below
  exercises an **existing** page/component. See
  `reports/phase-goal-ops-hardening-iter-53-ui-surface-map.md` for the full surface mapping.
- Both servers were confirmed live at the time this plan was written:
  `curl http://localhost:8255/api/health` → `200` in 0.10s; `curl http://localhost:3255/` and `/data` →
  both `200`. No login/auth gate exists in this codebase.
- **Read this before grading UT-03/UT-04.** This iteration's own developer pass ran a live concurrent
  drill and found the specific reliability improvement it targeted **was achieved for the two treated
  causes** (zero non-answers from `coverage_membership_timeline_refresh` and `market_phase_warm`, down
  from 1 each) but the drill still recorded **one** non-answer overall, now traced to a third, untreated
  step (`per_date_coverage_warm`), and the job's total finalize-tail time is measured **worse** for reasons
  unrelated to this iteration's change (`reports/perf-budgets.md` Item X / Addendum 15). UT-03/UT-04 below
  test whether the UI behaves **honestly and recovers** around that known, disclosed, partially-improved
  condition — not whether zero flips occur system-wide, which is already known not to be the case.
- UT-03/UT-04/UT-11 require starting a real backfill job, which can take 25–40+ minutes to reach a terminal
  status (this iteration's own drill measured 1,684.84s total, ~28 minutes). Budget that time separately.
- UT-05/UT-06/UT-07 require terminal access to stop/restart/kill the backend process — this is the first
  time this specific evidence (J-04 steps 3–5) has ever been captured for this session; treat these as
  high-priority, not optional.

---

## Test Cases

---

### UT-01 — Dashboard, Data Manager, and Backtest load without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`, `/data`, `/backtest`

**Preconditions:**
- Frontend running at http://localhost:3255; backend running at http://localhost:8255
- No login required

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Wait up to 5 seconds for the page to settle
3. Click "Backtest" in the left sidebar
4. Wait up to 5 seconds for the page to settle
5. Click "Data Manager" in the left sidebar
6. Wait up to 5 seconds for the page to settle

**Expected Result:**
- All three pages render without a blank screen or an unhandled application error
- No new browser console errors on any page
- The header's readiness pill and the left sidebar are visible on all three pages

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

### UT-03 — Badge/banner no longer flip to unavailable because of the two treated finalize-tail steps specifically (regression / resilience — the core TC-1 check)

**Type:** regression
**Priority:** P1
**Surface:** global (header/sub-header) + `/data`

**Preconditions:**
- Backend running via `scripts/start-backend.sh` (AG-10 caps live)
- Budget 25–40+ minutes separately from the rest of this plan

**Steps:**
1. (Optional but recommended, for a rigorous replay) In a separate terminal, start a 1-second health
   poller that logs every non-200/timeout event:
   `while true; do curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" --max-time 5 http://localhost:8255/api/health || echo "NON-ANSWER $(date +%s)"; sleep 1; done | tee /tmp/j53-health-poll.log`
2. Navigate to `http://localhost:3255/data`
3. Leave the "Start date"/"End date" fields at their pre-filled default values (auto-filled from the first
   detected coverage gap) and leave "Job kind" set to "Backfill snapshots"
4. Click the "Start" button
5. From this moment, watch the header's readiness pill (`data-testid="readiness-badge"`) continuously
   until the "Job progress" card's status badge (`data-testid="job-status"`) reaches a terminal state
   (e.g. "ok")
6. Note every timestamp the pill flips from green "Ready" to red "Backend unavailable", and roughly how
   long each flip lasts before it recovers on its own

**Expected Result (what MUST hold — a real fail):**
- The job itself still reaches a normal terminal status — it must not hang forever, crash, or leave the
  page in an error state
- Whenever the pill/banner do flip to their failure state, they show the correct, honest labels ("Backend
  unavailable" / "NO-GO — do not rely on today's board") — never a fabricated "Ready"/"GO" while a poll is
  actually failing
- Every flip to the failure state recovers on its own (flips back to "Ready"/quiet "GO") within a few
  polling cycles once `/api/health` next answers successfully — it must never stay stuck on red
  indefinitely

**Expected Result (what to record, not grade as pass/fail against zero):**
- This iteration's own developer drill measured **zero** non-answers traceable to
  `coverage_membership_timeline_refresh` or `market_phase_warm` specifically (down from 1 each in the
  prior drill) — but **one** non-answer overall, now inside a third, untreated step
  (`per_date_coverage_warm`). A single red flip on your run, if it happens, is the known, disclosed,
  not-yet-fully-fixed condition (`reports/perf-budgets.md` Item X), not automatically a new bug. Zero
  flips entirely would be better than the developer's own measurement — worth noting if you see it. More
  than one or two flips, or a flip lasting more than ~30s without recovering, is worth flagging as
  possibly new.

---

### UT-04 — Job duration: the two treated steps are faster in isolation, but the total can still run over budget for unrelated reasons (regression measurement)

**Type:** regression
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Same running job as UT-03 (observe in parallel with it)

**Steps:**
1. Note the wall-clock time when "Start" was clicked in UT-03
2. Periodically check the "Job progress" card's status badge and the "updated Ns ago" heartbeat text
   beside it
3. Once the job reaches a terminal status, read the per-phase breakdown in the "stage-timings" block
   (`data-testid="stage-timings"`)

**Expected Result:**
- The "updated Ns ago" heartbeat keeps advancing throughout (never frozen for minutes at a time) — this
  is what distinguishes "slow but alive" from an actual stall
- If the stage-timings breakdown lists `coverage_membership_timeline_refresh` and `market_phase_warm`
  individually, both should read faster than a pre-iter-53 build would show (this iteration's own
  concurrent-load drill: `market_phase_warm` 26.26s → 0.73s; `coverage_membership_timeline_refresh`
  46.05s → 40.54s)
- Record the total elapsed time. This iteration's own drill measured 1,559.30s (~26 minutes) against the
  product's ~1,200s (20-minute) budget — an overage is the currently known, disclosed condition (the
  developer's own analysis attributes it to two OTHER, untouched steps, not to the two phases this
  iteration treated), not automatically a new bug. A run finishing well within 20 minutes is good news
  worth noting distinctly.

---

### UT-05 — J-04 evidence: badge shows the initializing-phase detail (boot phase + n/m) during a pre-ready poll window (TC-6a, first capture)

**Type:** smoke
**Priority:** P1
**Surface:** global header + terminal + backend process

**Preconditions:**
- Terminal access to stop/start the backend process
- Frontend open at `http://localhost:3255/` before the restart

**Steps:**
1. Stop the currently-running backend: `pkill -f "uvicorn app.main:app"` (or the project's documented stop
   method)
2. Immediately restart it in one terminal: `scripts/start-backend.sh`
3. In a second terminal, from the same moment, poll and capture the raw payload at short intervals:
   `for i in $(seq 1 40); do curl -s http://localhost:8255/api/health; echo; sleep 0.2; done | tee /tmp/j53-boot-poll.log`
4. With the frontend already open at `http://localhost:3255/`, watch the top-right header pill
   (`data-testid="readiness-badge"`) during the same window and capture a screenshot/DOM read the moment
   it shows anything other than "Checking backend…" or "Ready"

**Expected Result:**
- At least one line in `/tmp/j53-boot-poll.log` shows a non-ready readiness payload carrying a boot phase
  and an `n/m`-shaped progress figure (the warmup/progress field) before the first `ready` response
- The screenshot/DOM read from step 4 shows the pill in its `data-state="initializing"` form:
  "Initializing… history n/m" — the SAME phase/progress detail as the terminal payload from the same
  window, never a bare "Backend unavailable"
- The first HTTP 200 (any readiness state) arrives within 5 seconds of the restart command in step 2
  (J-04's ≤5s boot budget)

---

### UT-06 — J-04 evidence: crashed/unreachable presentation is visibly distinct from initializing, and the persistent logfile shows the truncation (TC-6b/c, first capture)

**Type:** error
**Priority:** P1
**Surface:** global header/sub-header + `logs/backend.log`

**Preconditions:**
- Backend running normally (post-UT-05); frontend open at `http://localhost:3255/`

**Steps:**
1. Note the current tail of the logfile: `tail -5 logs/backend.log` (path relative to the repo root)
2. Kill the backend process abruptly to simulate a crash: `pkill -9 -f "uvicorn app.main:app"`
3. Within the next ~10 seconds, watch the header pill and the strip beneath it; capture a
   screenshot/DOM read
4. Re-run `tail -5 logs/backend.log` and compare to step 1
5. Restart the backend (`scripts/start-backend.sh`) before running any later test in this plan

**Expected Result:**
- The pill flips to red `data-state="unavailable"`, text "Backend unavailable" — visibly distinct
  (different color/icon/text) from the amber `data-state="initializing"` captured in UT-05
- The banner beneath the header flips to `data-verdict="NO-GO"`, text "NO-GO — do not rely on today's
  board." with reason "Backend is unavailable — the preflight check could not run."
- The logfile read in step 4 ends at essentially the same content as step 1 — no new
  "shutdown"/"stopping" line was appended after the kill (a `SIGKILL`'d process cannot write one); boot
  entries from the earlier startup remain present earlier in the file

---

### UT-07 — After restart, a job that was mid-flight at the kill shows an honest interrupted state (J-04 step 6, regression on already-proven code)

**Type:** regression
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- A job was running at the moment of UT-06's kill (if none was in flight, start one deliberately and
  repeat the kill from UT-06 once it is running)

**Steps:**
1. With the backend restarted (post-UT-06), navigate to `http://localhost:3255/data`
2. Find the row in the "Run History" table corresponding to the job that was running at the kill

**Expected Result:**
- That row's status reads a distinct "interrupted" state (not "running" forever, not silently dropped),
  rendered with the muted-neutral badge treatment — visibly distinct from a hard red "failed"
- No living process is implied for that row — no spinner, no "running" badge

*(Not modified by this iteration — J-04's own already-shipped contract. This iteration's own drill
incidentally observed this exact contract firing correctly on a real, unplanned process interruption — see
`reports/perf-budgets.md` Item X.)*

---

### UT-08 — Dashboard's "Market Phase & Severity" card is unaffected by the fetch-bounding change (regression, AG-3 byte-identity)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Dashboard)

**Preconditions:**
- At least one completed ingest exists (true on this build)

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Locate the "Market Phase & Severity" card
3. Note the phase label and the 0–100 severity score, then click its "Why this regime — component
   breakdown" disclosure

**Expected Result:**
- The card renders a real phase label (not "—"/NA) and a numeric severity score
- The expanded breakdown shows real component rows, not an error or empty state
- Values match what the same as-of date showed before this iteration — this iteration's fix only changed
  HOW MANY bars are fetched to compute the VIX gate and the benchmark-drawdown window, never the computed
  value (proven primarily by three new byte-identity unit tests in `test_market_phase.py`; this step is a
  live spot-check, not the primary proof)

---

### UT-09 — `/data`'s coverage, universe-diagnostic, and membership-timeline panels are unaffected (regression, AG-3 byte-identity)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Read the "Dataset coverage" panel's "Universe (as of date)" figure (`data-testid="universe-count"`)
3. Scroll to the "Universe resolution as of …" panel (`data-testid="universe-diagnostic-panel"`) and read
   the "Admitted" figure (`data-testid="universe-diagnostic-admitted"`) plus the four excluded-by-reason
   figures
4. Scroll to the membership-timeline panel and confirm it renders a populated table/chart, not an error

**Expected Result:**
- All figures render as real numbers, not "—"/NA/error
- The "Admitted" figure plus the four excluded-reason figures sum to the candidate-pool count shown in the
  same panel — internal consistency, unaffected by this iteration's change to how much history is fetched
  per candidate
- Values match what the same as-of showed before this iteration (this iteration's fix bounds the fetch
  window for the resolver's trailing-liquidity/history read, never the resolver's decision — proven
  primarily by 4 new tests in `test_universe_resolver.py` and 1 new integration test in
  `test_data_manager_membership_cache.py`; this step is a live spot-check)

---

### UT-10 — Start-job form still blocks invalid dates (validation)

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
- An inline validation error appears under the "Start date" field ("Enter a valid date as yyyy-MM-dd")
- The "Start" button is disabled (cannot be clicked) while the field is invalid
- No job is created

*(Not touched by this iteration — included because this form is the only entry point that can trigger the
two treated finalize-tail code paths; a broken guard here would block verifying UT-03/UT-04.)*

---

### UT-11 — A MemoryError on either newly-treated phase is honestly isolated while the job/process keeps serving (error, TC-5 manual mirror)

**Type:** error
**Priority:** P2
**Surface:** `/data` + `logs/backend.log`

**Preconditions:**
- Restart the backend with the fault-injection env var aimed at one (or both, comma-separated) of this
  iteration's two new sites:
  `TRENDORA_FAULT_INJECT_MEMORY_ERROR=coverage_membership_timeline,market_phase scripts/start-backend.sh`
  (induces no real memory pressure — safe under AG-10; the launch script itself is invoked unmodified,
  only an env var precedes it)

**Steps:**
1. With the backend started as above, go to `http://localhost:3255/data`
2. Start a backfill job (leave the pre-filled Start/End dates, "Job kind" = "Backfill snapshots", click
   "Start")
3. Wait for the status badge to leave its running state
4. Read the "Refreshed:" line (`data-testid="aggregates-refreshed"`) for this job

**Expected Result:**
- The job still reaches a normal terminal status — it does not hang, crash, or show a 500
- The "Refreshed:" line does **not** include "coverage" / "membership timeline" (if
  `coverage_membership_timeline` was armed) and/or "market phase" (if `market_phase` was armed); every
  other category that legitimately succeeded (e.g. "forward aggregates") still appears
- Throughout this run, the header's readiness pill still recovers normally (per UT-03's "what MUST hold")
- **Afterward:** restart the backend without the env var before running any other test in this plan

---

### UT-12 — Backtest evidence still serves from storage only (J-08 regression)

**Type:** regression
**Priority:** P2
**Surface:** `/backtest`

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3255/backtest`
2. Wait up to 5 seconds for the page to settle
3. Scroll to the bottom evidence section (`data-testid="evidence-aggregate"` /
   `data-testid="evidence-summary"`)

**Expected Result:**
- The page renders the forward-test scorecard with real (non-placeholder) rows, no error state
- The evidence section shows "Snapshots contributing" with a real numeric count, not a cold-recompute
  spinner
- Nothing about this section is touched this iteration; included as a required-still-passing check (J-08)

---

### UT-13 — Background-compute panel still discloses correctly (J-09 regression)

**Type:** regression
**Priority:** P2
**Surface:** `/backtest`, `/data`

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3255/backtest`
2. Click the "Previous available date" control enough times to land on a historical as-of date
3. Navigate to `http://localhost:3255/data` and scroll to the "Background compute" panel
   (`data-testid="background-compute-panel"`)

**Expected Result:**
- The panel shows either an active in-flight entry or, once it finishes, an updated "Last outcome"
  summary — never an error state
- The panel's footer reads "Since the last backend restart — this history is process-lifetime only, never
  persisted."
- Unaffected by this iteration (not touched); included as a required-still-passing check (J-09)

---

### UT-14 — Badge/banner render consistently across pages (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`, `/data`, `/backtest`

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3255/`, then click "Data Manager", then click "Backtest" in the left
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
| UT-01 | Dashboard/Data Manager/Backtest load without errors | smoke | P1 | `/`, `/data`, `/backtest` |
| UT-02 | Badge/banner show honest state at rest | smoke | P1 | global |
| UT-03 | Badge/banner no longer flip because of the two treated causes | regression | P1 | global, `/data` |
| UT-04 | Job duration: treated steps faster, total mixed | regression | P2 | `/data` |
| UT-05 | J-04 evidence: initializing badge detail (first capture) | smoke | P1 | global, terminal |
| UT-06 | J-04 evidence: crashed presentation + logfile truncation (first capture) | error | P1 | global, `logs/backend.log` |
| UT-07 | J-04: interrupted job shown honestly after restart | regression | P2 | `/data` |
| UT-08 | Market Phase & Severity card unaffected | regression | P1 | `/` |
| UT-09 | Coverage/universe-diagnostic/membership panels unaffected | regression | P1 | `/data` |
| UT-10 | Start-job form blocks invalid dates | validation | P2 | `/data` |
| UT-11 | Degraded treated phase honestly disclosed; job still completes | error | P2 | `/data` + `logs/backend.log` |
| UT-12 | Backtest evidence unaffected | regression | P2 | `/backtest` |
| UT-13 | Background-compute panel unaffected | regression | P2 | `/backtest`, `/data` |
| UT-14 | Badge/banner consistent across pages | ux | P2 | `/`, `/data`, `/backtest` |

**P1 tests must all pass for browser QA verdict to be PASS.** Per "Before you start": UT-03's P1 status
covers the UI's *honesty and self-recovery* around the known, partially-improved reliability picture, not
whether the system-wide non-answer count reached zero — grade it on those criteria. UT-05/UT-06 are P1
because they satisfy this iteration's own DoD item (TC-6, J-04's first-ever evidence capture), not because
any regression risk was found in that code.
