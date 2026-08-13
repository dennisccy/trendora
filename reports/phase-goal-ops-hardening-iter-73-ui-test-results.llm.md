# Goal Iteration 73 — UI Test Results (Browser QA, target journey J-07)

**Phase:** goal-ops-hardening-iter-73
**Date:** 2026-08-13
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: the sole target journey this dispatch (J-07, P1) does not meet its full Acceptance —
     step 3 (peak-memory margin under realistic pool pressure, recorded in reports/perf-budgets.md)
     was not obtained this round, per the developer's own honest Addendum 38 write-up. This is a
     CONTINUATION of an already-disclosed gap (journey-history has carried J-07 as "partial" since
     iter-42, blocked on this exact step since iter-72), NOT a newly discovered live regression —
     the parts of J-07 that ARE browser-observable (serving stays healthy, readiness badge, /backtest,
     /api/health) are clean with fresh evidence below. See "What is and isn't reflected in this FAIL"
     under UT-J-07 for the full breakdown. -->

**Overall:** 0/1 tests passed (0 skipped)

Scope note: per this dispatch's explicit "test EXACTLY these journeys this run: J-07" instruction,
this report covers ONLY J-07. A separate lane this same iteration already re-verified J-05 and J-06
live (both PASS — see `reports/phase-goal-ops-hardening-iter-73-ui-test-results.canary.md`); J-01,
J-03, J-04, J-08, J-09 are covered by the deterministic replay lane per the dispatch's "do NOT test
these" list. No golden replay script is written for J-07 this round (only PASS journeys get one, per
the agent instructions).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | Heavy aggregates never take the service down | regression/resilience | P1 | All 4 numbered steps hold: (1) a full deep-basis forward-aggregate warm runs while `/api/backtest` keeps serving every horizon; (2) `GET /api/health` answers HTTP 200 on every 1 Hz poll throughout, no frozen window; (3) the process's peak VmPeak during the warm is measured and recorded under `server.memory_cap_mb` with its margin in `reports/perf-budgets.md`; (4) an induced memory-pressure abort during a warm is graceful — the SAME process keeps serving `/api/health` and cached reads, never wedged/restarted | Steps 1+2 (the browser/live-observable half): fresh evidence is clean — see body below (readiness badge `ready`, `/backtest` serving 2,917 stored snapshots with no "Refreshing" banner, 20/20 steady-state health polls just now, plus this iteration's own real warm activity — a 17m41s backfill and a 26-minute pressure-free rebuild arm — both recorded 0 non-200 health polls). Step 3 (the round's actual target): **not closed** — this iteration's developer pass ran the live pool-pressure drill 4 times; the 3 pressure-added attempts all collided with a separate, already-disclosed uvicorn admission-control 503 issue before completing, and the 1 pressure-free attempt that did run clean did not reach the warm's finalize tail before its own time bound, so no complete VmPeak-under-realistic-pool-pressure figure exists (`reports/perf-budgets.md` Addendum 38). Step 4: not exercised this round by any lane (code byte-unchanged — durability carry from earlier iterations, not independently re-verified here). | FAIL | `reports/qa/goal-ops-hardening-iter-73-evidence/UT-J-07-result.png` |

---

## Failed Tests

### UT-J-07 — Heavy aggregates never take the service down
**Verdict:** FAIL
**Evidence:** `reports/qa/goal-ops-hardening-iter-73-evidence/UT-J-07-result.png` (screenshot of the live, healthy `/backtest` page taken during this check) plus `reports/qa/goal-ops-hardening-iter-73-evidence/J-07-steady-state-poll.csv` (this round's own fresh 20-poll health sample)

**Why this is a FAIL, precisely — and what is NOT wrong:**

J-07's Acceptance has four clauses tied to the journey's four numbered steps. This iteration
(`Frontend Present: no`, a measurement-only round) made **zero production-code changes**
(`config.yaml` byte-unchanged, confirmed via `git diff HEAD -- config.yaml` in the dev handoff) — its
whole job was to close step 3, the one open gap journey-history has carried since iter-72
("STEP 3 IS WHY THIS IS partial AND NOT passing"). It did not close it. Concretely:

- **Step 1 (trigger the full warm) + Step 2 (health stays responsive throughout):** these are the
  parts a browser/HTTP-level check can actually exercise, and they are clean. I did not re-run a
  fresh full-basis warm myself this dispatch (see "What I did and did not run" below for why), but
  three independent pieces of evidence converge, all from earlier TODAY in this same session:
  1. This iteration's own dev-conducted drill (`reports/perf-budgets.md` Addendum 38): a real
     `rebuild` job (the same "full deep-basis forward-aggregate warm" J-07 step 1 names) ran for a
     complete, uninterrupted 26-minute pressure-free window with the canonical 1 Hz
     `scripts/qa/poll_health.py` poller running throughout: **1,063/1,063 `GET /api/health` polls
     HTTP 200, zero non-200s, zero timeouts.**
  2. An earlier browser-QA lane this same iteration (see
     `reports/phase-goal-ops-hardening-iter-73-ui-test-results.canary.md`, UT-J-05) drove a real
     in-app backfill (job `1273b81dcb9d4616bc4a260d80fbc89d`, 2026-08-13T02:26:06.779Z →
     02:43:29.224Z, ~17m41s) whose finalize hook refreshed `forward_aggregates` (one of 9 listed
     categories) while `scripts/qa/poll_health.py` ran concurrently:
     **1,232/1,232 polls HTTP 200, zero non-200s, zero breaches** of the ≤2s BCW ceiling (raw file:
     `reports/qa/goal-ops-hardening-iter-73-evidence/poll_health.csv`, meta confirms `rows: 1232`,
     `health_ceiling_s: 2.0`).
  3. My own live check just now (see below): the live backend is healthy at steady state, and both
     of J-07's UI homes (global readiness badge, `/backtest`) render correctly with no regression.

- **Step 3 (peak VmPeak under the resized 68-connection pool, margin recorded):** **not obtained
  this round.** This is the actual target of this iteration's spec, and the developer's own handoff
  is explicit that it stayed open: three independent, full-length live attempts (10, then 8, then 5
  concurrent pool-pressure workers, each against the real `rebuild` job) all hit a sustained
  `logs/backend.log` "Exceeded concurrency limit" 503 streak before completing — the SAME
  already-disclosed, out-of-scope uvicorn admission-control finding `reports/perf-budgets.md`
  Addendum 37 recorded (attributed to host CPU contention: `uptime` showed 1-minute load swinging
  0.51-4.74 across the dev's session, with other concurrent Claude Code sessions and Chrome
  processes confirmed live via `ps aux`), not the DB-pool/memory question this round targets. The
  one pressure-free attempt that DID run clean (item 1 above) reached VmPeak 2,390,872 kB (71.5%
  margin against the 8192 MB cap) but explicitly did **not** reach the warm's finalize tail — the
  historically memory-heaviest phase — before its own 1,800s bound, because today's committed dev DB
  has grown to ~8.4 GB (vs. the 811 MB 2026-07-18 "ground truth" figure), making a full `rebuild`
  dramatically slower than its historical ~16-34 min figures. So step 3's own Acceptance ("assert it
  stays under the declared `server.memory_cap_mb`, with the margin recorded") has a number on record,
  but not the complete, realistic-concurrency number this round set out to get — the developer's own
  "Known Issues" section says this plainly rather than presenting the partial 71.5% figure as if it
  answered the question. I read that section and am relaying its conclusion, not softening it.

- **Step 4 (induce memory pressure, confirm graceful abort without wedging):** not exercised by any
  lane this round. `compute_forward_aggregates`/the isolation convention are byte-unchanged this
  iteration (confirmed via the diff), so this stays a durability carry from whichever earlier
  iteration last exercised it — I did not independently re-verify it, and inducing memory pressure
  against the shared live QA backend is both outside what Chrome MCP can do (it needs "a test hook or
  a tightened cap in a throwaway process" per the journey's own step 4 wording) and inappropriate for
  this dispatch given I may not restart the app if it were to wedge.

**What I did and did not run, and why:** I did not trigger a fresh full deep-basis warm or a
pool-pressure drill myself this dispatch. The developer already ran this exact live drill four times
this same session (documented above), spending well over an hour of wall-clock live-drilling time
and encountering a process-hygiene incident (an over-broad `pkill` briefly killed one attempt's own
in-progress backend). Re-running the identical drill within this QA dispatch would very likely
reproduce the same host-contention outcome (nothing about the ambient load or DB size has changed —
`uptime` just now still showed load average 0.32/0.61/0.89, and the DB is still the grown ~8.4 GB
basis), would take on the order of 30+ minutes to multiple hours with no new instrumentation beyond
what the dev's pytest-based `_MemSampler`/`_HealthPoller` already provides, and would risk repeating
the same kill-the-wrong-process hazard against the shared QA backend other lanes depend on. Per this
role's standing rule against debugging/redoing already-covered ground and the explicit note that I
"may not restart the app," I judged that redoing it would not produce meaningfully different evidence
and instead verified what browser automation actually can: that the live, currently-running backend
(confirmed launched via `scripts/start-backend.sh` — boot header at `logs/backend.log:348694`,
`launching at 2026-08-13T02:13:14Z`, `memory_cap_mb=8192 malloc_arena_max=2`, `host-guard:
cpu_list=0-15 blas_threads=8`; frontend confirmed `next start -p 3255`, never `dev.sh`, per the
iter-71 lesson) is healthy right now, with no regression versus the dev's own evidence.

**Fresh live checks performed this dispatch (Chrome MCP + `scripts/qa/poll_health.py`):**
1. Navigated to `http://localhost:3255/` — `[data-testid="readiness-badge"]` read
   `data-state="ready"`, text "Ready".
2. Navigated to `http://localhost:3255/backtest` — `evidence-summary` read "Snapshots contributing
   (≤ 2026-08-03): 2917 · As-of range: 1999-11-02 → 2026-05-06 · Mean stock fwd return (60d): +3.76%
   (n=1259571)"; no "Refreshing" banner present (a stable, complete evidence version, not a mid-warm
   transitional state); readiness badge still `ready`. Screenshot at
   `reports/qa/goal-ops-hardening-iter-73-evidence/UT-J-07-result.png` shows this state (preflight
   "GO — today's board is current" banner, Backtest heading, as-of 2026-08-03 latest view).
3. Ran the canonical poller for a short, bounded, fresh steady-state sample:
   `python3 scripts/qa/poll_health.py http://localhost:8255/api/health <out>.csv <out>.stop --count 20`
   → **20/20 polls HTTP 200**, elapsed 0.006-0.022s (well inside the ≤2s BCW ceiling and the
   steady-state budget both), load_avg_1m 1.09-1.34 throughout. Raw CSV:
   `reports/qa/goal-ops-hardening-iter-73-evidence/J-07-steady-state-poll.csv`.

**Net assessment:** nothing observed this dispatch, this iteration, or in the developer's own
extensive live-drill evidence indicates any live regression — the app serves correctly, the readiness
badge and `/backtest` are healthy, and every health-poll sample taken today (steady-state and during
two different real warms) came back 100% clean. The FAIL verdict reflects that J-07's own step 3
Acceptance criterion — a complete peak-memory measurement under the resized pool at realistic
concurrency, recorded in `reports/perf-budgets.md` — remains unmet this round, exactly as the
developer's own handoff discloses (`docs/handoffs/goal-ops-hardening-iter-73-dev.md`, "Known Issues").
This continues journey-history's existing `"status": "partial"` for J-07 (open since iter-72 on this
same step); it is not a new failure mode.

---

## Environment

- **Frontend URL:** http://localhost:3255 (confirmed `next start -p 3255`, prod mode, launched
  2026-08-13T02:13 local session)
- **Backend URL:** http://localhost:8255 (confirmed launched via `scripts/start-backend.sh`,
  `logs/backend.log` boot header `2026-08-13T02:13:14Z`, `memory_cap_mb=8192 malloc_arena_max=2`,
  host-guard `cpu_list=0-15 blas_threads=8`)
- **Browser:** Chromium via `mcp__plugin_superpowers-chrome_chrome__use_browser` (Chrome MCP)
- **Test Date:** 2026-08-13
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-73-evidence/`
- **Host load at time of this dispatch's own checks:** `uptime` load average 0.32 / 0.61 / 0.89
  (quieter than the 0.51-4.74 range the developer's own drills saw earlier this session)
