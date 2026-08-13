# Goal Iteration 74 — UI Test Results (Browser QA, target journey J-07)

**Phase:** goal-ops-hardening-iter-74
**Date:** 2026-08-13
**Written by:** browser-qa-agent (Chrome MCP)

---

**Browser QA Verdict:** PASS

<!-- PASS: sole target journey this dispatch (J-07, P1) meets its Acceptance on the combination of this
     pass's own fresh live evidence (steps 1/2, browser-observable) and this iteration's dev-side Addendum
     39 measurement (step 3, closed — a complete 9/9-phase VmPeak profile under realistic pool pressure,
     42.3% margin), with step 4 carried on its own prior durable evidence (iter-58's organically-witnessed
     MemoryError-survival) per this iteration's own testing requirements. -->

**Overall:** 1/1 tests passed (0 skipped)

**Dispatch scope:** per this dispatch's explicit "test EXACTLY these journeys this run: J-07" instruction,
this report covers ONLY J-07. J-01/J-03/J-04/J-05/J-06/J-08/J-09 are verified separately by deterministic
replay + an already-completed LLM-fallback lane this same iteration
(`reports/phase-goal-ops-hardening-iter-74-ui-test-results.canary.md`, 2/2 PASS on J-05/J-06; the other five
were not re-dispatched to this LLM lane, implying their replays held).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | Heavy aggregates never take the service down | target | P1 | All 4 numbered steps hold: (1) a full deep-basis forward-aggregate warm runs while `/api/backtest` keeps serving every horizon; (2) `GET /api/health` answers HTTP 200 on every 1 Hz poll throughout, no frozen window; (3) the process's peak VmPeak during the warm is measured and recorded under `server.memory_cap_mb` with its margin in `reports/perf-budgets.md`; (4) an induced memory-pressure abort during a warm is graceful — the SAME process keeps serving `/api/health` and cached reads, never wedged/restarted | Steps 1+2 (browser-observable): readiness badge `data-state="ready"` on `/`; `/backtest` served real stored scorecard/leadership-cohort/expanding-window content (2,919 contributing snapshots) with no "Refreshing" banner; all 5 `GET /api/backtest?horizon={1,5,10,20,60}` calls answered HTTP 200 in 0.05–0.13s; a fresh 150-poll (2.5 min) 1 Hz `GET /api/health` run via the canonical `scripts/qa/poll_health.py` returned 150/150 HTTP 200, 0 breaches, max 0.098s. Step 3 (this round's actual target): **CLOSED** — this iteration's dev pass (`reports/perf-budgets.md` Addendum 39, corroborated directly: code diff confirmed in `test_start_backend_script.py`, `pytest --collect-only` re-confirmed 23 tests collected, `config.yaml` confirmed byte-unchanged) produced a COMPLETE, clean 9-of-9-finalize-tail-phase VmPeak profile under realistic pool pressure — peak 4,837,420 kB / 4,724.0 MB, 42.3% margin against the 8192 MB cap — plus 1,795/1,795 clean `GET /api/health` polls DURING that same real warm (bonus corroboration of step 2 under actual load, stronger than this pass's own steady-state poll). Step 4: not re-exercised this round (no live fault-injection lane in this dispatch or this iteration's dev scope) — carried on iter-58's own organically-witnessed real MemoryError (VmPeak pegged at the then-6144 MB cap) that left `/api/health` at 0 non-200 across 229 samples and the SAME process (pid 782444) serving a clean J-05 backfill minutes later; no lane this pass found any contradiction to that finding. | PASS | `reports/qa/goal-ops-hardening-iter-74-evidence/J-07-backtest-live.png` |

---

## Passed Tests

### UT-J-07 — Heavy aggregates never take the service down

**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-74-evidence/J-07-backtest-live.png`, `runs/goal-ops-hardening-iter-74/browser-qa-health-poll/j07-health-poll.csv`

J-07 has no dedicated page — its two declared UI homes (per `blueprint.md`'s Information Architecture) are
the global readiness badge (every page's top bar) and `/backtest`. Step 3 (the actual VmPeak measurement)
is inherently a backend-instrumentation reading (`/proc/<pid>/status`), not something a browser can observe
directly; this iteration's own TESTING REQUIREMENTS scope browser-QA to re-verifying step 3's *closure* and
carrying steps 1/2/4 on durable evidence unless a contradiction is found. None was found.

**1. Readiness badge (`/`):**
- `document.querySelector('[data-testid="readiness-badge"]')` → `{"state":"ready","text":"Ready"}`.
- Page loaded fully styled (nav, "Dashboard" heading, 14 buttons / 12 links) — no "Checking backend…"
  stuck state, no asset-less rendering.

**2. `/backtest` (step 1's UI home, J-08's serve-from-storage guarantee):**
- Navigated to `/backtest`. "Backtest" heading, "Forward-test scorecard" section present, real
  as-of-2026-08-03 content: Market Regime "Risk-on 66.07/100", ranked cohort (NTAP/SNOW/GRMN/…), the
  expanding-window aggregate ("Snapshots contributing (≤ 2026-08-03): 2919", "Mean stock fwd return (60d):
  +3.76% (n=1260166)") — all read from stored forward returns, never a live recompute banner.
- Direct `GET /api/backtest?horizon={1,5,10,20,60}`: all 5 calls **HTTP 200** in 0.050–0.131s each —
  storage-speed, consistent with J-08 and with step 1's "serve `GET /api/backtest` for each horizon
  throughout" requirement (baseline confirmation; the SAME endpoint was also hit 968 times during this
  iteration's own dev-side full warm, all 200 — see Addendum 39, quoted below).
- Screenshot: `reports/qa/goal-ops-hardening-iter-74-evidence/J-07-backtest-live.png`.

**3. Fresh live `GET /api/health` poll (step 2, steady-state corroboration):**
- Ran the canonical `scripts/qa/poll_health.py http://localhost:8255/api/health <csv> <stopfile> --count 150`
  (per this session's standing correction: use the canonical poller, started before any job — here run as a
  steady-state baseline since no heavy job was in flight at dispatch time; `background_compute.active` was
  `[]` on arrival).
- Result: **150/150 HTTP 200, 0 non-200s, 0 breaches of the 2s ceiling, elapsed_s range 0.004–0.098s**
  (2026-08-13T05:48:39Z → 05:51:08Z, 150 continuous 1 Hz samples). Raw CSV:
  `runs/goal-ops-hardening-iter-74/browser-qa-health-poll/j07-health-poll.csv`.
- `logs/backend.log`'s tail for this window showed no error/traceback/MemoryError lines; a follow-up
  `GET /api/health` re-check confirmed `readiness: "ready"`, `background_compute: {"active": [], "recent_outcomes": []}`.

**4. Step 3 — VmPeak measurement, verified as CLOSED via this iteration's dev evidence (not independently
re-measured by this browser-QA pass — a live realistic-pool-pressure warm takes ~33 minutes per this same
iteration's own dev drill, and the dispatch environment note directs reading Addendum 39 rather than
re-running it):**
- `reports/perf-budgets.md` Addendum 39 (dated 2026-08-13, this iteration): a `backfill`-triggered finalize
  tail (chosen deliberately over `rebuild`, whose unconditional full-range scan defeated all four of
  Addendum 38's iter-73 attempts) ran under `_POOL_PRESSURE_WORKERS=5` realistic concurrent load, launched
  only via `scripts/start-backend.sh`. **All 9 finalize-tail phases + all 5 `forward_aggregates_warm`
  horizons captured** a joined VmPeak-at-completion reading; overall peak **4,837,420 kB = 4,724.0 MB**,
  margin against `memory_cap_mb` (8192 MB) = **42.3%** (comfortably above the 20% TC-4 threshold — no
  `config.yaml` change made, confirmed byte-unchanged below). **1,795/1,795 `GET /api/health` polls HTTP
  200** during that SAME real warm, zero non-200s, max latency 1.987s (inside the relaxed ≤2s
  bounded-background-compute-window ceiling) — this is materially stronger step-2-under-load evidence than
  this pass's own steady-state 150-poll baseline.
- Independently corroborated (not just re-read from the report) before accepting the claim: `git status
  --porcelain -- apps/backend/tests/test_start_backend_script.py reports/perf-budgets.md docs/goal.md
  config.yaml` shows the three claimed-modified files modified and `config.yaml` NOT modified (matching
  TC-4's "left byte-unchanged" claim); `grep` confirmed `_local_asctime_to_epoch`, `_parse_phase_timing_
  lines`, `_vmpeak_at`, `_join_phase_vmpeak` exist in the test file at the claimed line numbers; a fresh
  `pytest --collect-only -q tests/test_start_backend_script.py` (run by this QA pass, not reused from the
  handoff) returned **"23 tests collected"**, matching the dev handoff's claim exactly; `config.yaml`'s
  `server.memory_cap_mb: 8192` line confirmed directly, matching the addendum's margin arithmetic
  (4,724.0 / 8192 = 57.7% used → 42.3% margin).
- This closes the gap that FAILed J-07 in iter-73 (`reports/phase-goal-ops-hardening-iter-73-ui-test-results.llm.md`:
  "Step 3 (the round's actual target): **not closed**" — all 4 live-drill attempts that round were defeated
  by either the uvicorn admission-control 503 issue or the drill's own time bound before reaching the
  finalize tail). This round's `backfill`-based method reached and captured the ENTIRE finalize tail
  cleanly, closing that gap.

**5. Step 4 — deliberate memory-pressure fault injection: not exercised by any lane this round (disclosed,
not silently skipped).** Neither this browser-QA pass nor this iteration's dev scope (IN SCOPE explicitly
limits the round's one risky action to the phase-by-phase join, not fault injection) attempted a deliberate
OOM/memory-cap-tightening drill this iteration. Carried on **iter-58's own organically-witnessed instance**
(`reports/phase-goal-ops-hardening-iter-58-ui-test-results.llm.md`, UT-J-07): a live, unplanned
forward-aggregate warm hit a genuine `MemoryError` (VmPeak pegged exactly at the then-6144 MB
`memory_cap_mb` ulimit-v ceiling), `background_compute.recent_outcomes` honestly recorded
`outcome:"failed"`, yet `GET /api/health` never returned non-200 across 229 live samples and the SAME
backend process (pid 782444) went on to serve a clean J-05 backfill to completion minutes later — the exact
acceptance property step 4 asks for (graceful abort, no wedge, no restart), witnessed live rather than
artificially induced. Nothing in this pass's own checks (readiness `ready`, clean logs, clean health poll)
contradicts that finding.

**Journey verdict: PASS.** Steps 1, 2, and 3 have direct, current-session evidence (this pass's own live
checks plus this iteration's own dev-side measurement, independently corroborated rather than taken on
faith); step 4 is carried on a prior real (not simulated) organic observation with no contradiction found.

---

## Failed Tests

None.

## Skipped Tests

None. Both services (`backend :8255`, `frontend :3255`) were live and healthy throughout (confirmed
`HTTP 200` before starting, and the frontend served fully styled content — no unstyled/asset-less
"Checking backend…" state was observed at any point this pass).

---

## Golden Replay Script

`runs/goal-session-ops-hardening/journey-scripts/J-07.json` — steps unchanged (the existing 2-step
`/`→"Ready", `/backtest`→"Forward-test scorecard" structural smoke check remains accurate; re-verified live
against both assertions this pass). Appended an iter-74 `_notes` entry recording this pass's live
re-confirmation, the fresh 150/150 clean health-poll baseline, and the Addendum 39 step-3 closure. Lint
clean (`demo_runner.py --mode lint`, see below).

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chromium via `mcp__plugin_superpowers-chrome_chrome__use_browser` (Chrome MCP)
- **Launcher:** confirmed production launcher (pump-verified `scripts/start-backend.sh` /
  `scripts/start-frontend.sh` pair, both HTTP 200 immediately before this dispatch began)
- **Test Date:** 2026-08-13
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-74-evidence/`
