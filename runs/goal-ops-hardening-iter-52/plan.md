# goal-ops-hardening-iter-52 Execution Plan

Continuation of the ops-hardening loop (session `ops-hardening`, iteration 52 of 52). Prior verdict
(iter-51) was **ESCALATE** with mandatory full depth. This iteration is scoped almost entirely by
`docs/phases/goal-ops-hardening-iter-52.md` (TC-1..TC-12, IN/OUT OF SCOPE, DEFINITION OF DONE already
fully written by the goal-decomposer) — this plan translates that spec into concrete file targets and
flags the traps a reading of `iteration-state.md` + the iter-51 audit surfaces. No drift from
`docs/goal.md`: this directly serves Key Capability 4 (instant-serving boot / phase-aware health) and
Key Capability 6 (per-page budgets) and closes an AG-8/AG-10-adjacent resilience gap the iter-51 audit
found (connection-level `/api/health` non-answers during the finalize tail).

## What to Build

- **Cooperative-yield scheduling fix (the one risky change).** Insert periodic yield points (e.g.
  `time.sleep(0)`, which forces a real OS-level GIL hand-off, not just an eval-breaker check) inside the
  CPU-bound per-item loops the ingest finalize tail runs, so the currently-longest sub-phase periodically
  cedes the CPU and `GET /api/health` never goes fully unanswered (`code=000`). Byte-identical outputs
  required — this is scheduling only, never a value/algorithm change.
- **New live-process fault-injection test** driving `TRENDORA_FAULT_INJECT_MEMORY_ERROR` at a
  finalize-tail warm site via an actual `POST /api/data/jobs` ingest job against a dedicated spawned
  backend (not a live request) — closes J-07 step 4 / TC-6's evidence gap (UT-05 was permission-denied
  twice this session).
- **Fresh dated `reports/perf-budgets.md` addendum** (append-only, after Item T/Addendum 11): health-poll
  connection-level non-answer counts before/after, solo AND concurrent; reconciled finalize-tail
  wall-clock vs. the existing 1,200s budget; J-06's Factor Lab real-browser TTI + on-load
  `GET /api/research/factor-lab?all=true` latency (currently owed — exists only inside a test report).
- **Close 2-3 rounds of verification debt.** The standing 8-journey browser/replay lane must run, LAST
  (after all code lands, TC-9), and produce a REAL executed row for J-04, J-05, J-06, J-07 — no
  "Deferred (iteration budget)", no zero-row scoring, for a third consecutive round. J-01, J-03, J-08,
  J-09 replay as regression checks (TC-12).
- Dev handoff at `docs/handoffs/goal-ops-hardening-iter-52-dev.md`.
- **Honest limit (do not overclaim):** the fix targets the connection-level non-answer specifically. It
  is not guaranteed to fully close J-07 step 2's ≤2s latency ceiling for every single poll — record what
  is actually measured, do not round a latency improvement up to full compliance.

## Agents Required

- developer: yes -- implements the scheduling fix, the new fault-injection test, the perf-budgets
  addendum, and the dev handoff. All work is backend; this project's pipeline has one implementation
  agent (no separate "backend-data"/"frontend-ux" agents exist in this repo's catalog).
- backend-data: yes -- same developer agent; 100% of the code change is backend
  (`apps/backend/app/engine/*.py`, `apps/backend/tests/*.py`, `reports/perf-budgets.md`).
- frontend-ux: no -- no frontend file is touched. Spec: "Frontend: None... the health badge, job cards,
  and Factor Lab page are unchanged in shape and payload."

## Frontend Present
Frontend Present: no

Note for QA/pipeline automation: "Frontend Present: no" reflects zero frontend CODE changes only. It
must NOT be read as "skip browser QA" — the standing 8-journey browser/replay lane (browser-qa-agent +
LLM fallback for journeys with no golden script) is a hard Definition-of-Done requirement this round
(TC-8), because J-05/J-06/J-07 have zero executed rows for two straight iterations and J-04 has been
DEFERRED-BUDGET for two straight iterations (last checked iter-49).

## Files to Create/Modify

- `apps/backend/app/engine/data_manager.py` -- add a real cooperative yield alongside the existing
  heartbeat-only `prog.tick()` calls in: `_persist_per_date_coverage_snapshots`'s per-date loop
  (`for d in todo:`, ~L3704-3705) and `_refresh_ingest_aggregates`'s per-date `market_phase_warm` loop
  (~L4100-4121) and per-horizon `forward_aggregates_warm` outer loop (~L4141-4195, `for h in
  cfg.walk_forward.horizons:`). `prog.tick()` itself only stamps a heartbeat timestamp — it is NOT a
  scheduling yield; both must coexist. Do not touch the `factor_lab_all_warm` call site's own shape
  (~L4287-4311, iter-51's "Do not redo") beyond whatever the research.py-side loops below need.
- `apps/backend/app/engine/research.py` -- add yield points inside `compute_factor_lab_all` (L1229,
  per-factor/per-horizon loop -- the confirmed LONGEST phase, 583.76s, Item T/Addendum 11, and the one
  the solo drill caught starving health 9/653), `_combination_observations` (L1378),
  `_factor_decile_observations` (L518), `_all_factor_observations_by_horizon` (L1027). Do not touch
  `_combination_cohort_members`'s bound (L1530-1573, iter-51 "Do not redo", DONE/byte-identical).
- `apps/backend/app/engine/forward_testing.py` -- add yield points inside `compute_forward_aggregates`
  (L1142)'s internal bounded chunk loop (`for start in range(0, len(runs_with_fr), run_chunk):`,
  ~L1253) -- the concurrent drill (UT-08) caught THIS phase starving health (19/892) when it was the
  longest sub-phase, confirming the "whichever phase is longest" generalization.
- `apps/backend/tests/test_start_backend_script.py` -- NEW test alongside the existing
  `spawned_backend_fault_injected` fixture (L876) and `test_factor_lab_all_survives_repeated_memory_
  pressure_live` (L931). The existing test faults `factor_lab_all` via a LIVE REQUEST
  (`GET /research/factor-lab?all=true`) -- the new test must instead drive it via `POST /api/data/jobs`
  (an actual ingest job) so the fault fires inside the finalize tail, not the request path. Assert: the
  job's terminal record omits the faulted category from `aggregates_refreshed` while other categories
  still appear; `GET /api/health` stays 200 throughout and 30s past completion; a follow-up request for a
  category that DID warm returns the correct stored value from the SAME still-running process (no
  restart). Mirror the opt-in gate (`TRENDORA_RUN_HEAVY_INGEST_TEST=1`) -- this test is heavy (a real
  ingest through a spawned backend can run minutes); do not fold it into the default fast pytest pass.
- `apps/backend/tests/test_data_manager.py`, `test_research_streaming.py` / `test_factor_lab_all.py`,
  `test_forward_testing_aggregates_streaming.py` / `test_forward_testing_streaming.py` -- TC-4
  byte-identical regression tests: pin a pre-fix reference for every already-warmed category
  (`aggregates_refreshed`, `EventStudyCache`/`MarketPhaseCache`/`ForwardAggregateCache`/
  `IndexSeriesCache`/coverage-snapshot rows) and assert byte-identical post-fix output -- the change
  alters scheduling only, never a value.
- `reports/perf-budgets.md` -- new dated section/addendum, appended after Item T/Addendum 11 (do not
  edit existing sections): health-poll non-answer counts before/after (solo + concurrent), reconciled
  finalize-tail wall-clock vs. 1,200s, J-06's Factor Lab browser TTI + on-load latency.
- `docs/handoffs/goal-ops-hardening-iter-52-dev.md` -- required dev handoff.

**Frozen -- do not touch (TC-10, AG-10; `git diff --stat` must stay EMPTY before and after):**
`config.yaml` (including for a new "yield interval" knob -- use an in-code constant, do not add a
config key), `project-extensions/host-guard/host-guard.env`, `scripts/start-backend.sh`, `scripts/dev.sh`,
`scripts/start-frontend.sh`. Also do not touch: any `apps/frontend/` file; `_try_acquire_drawdown_warm`/
`_release_drawdown_warm` (the owner-deferred `iter-50/cc` interlock contradiction);
`runs/goal-session-ops-hardening/state/blueprint.md` (already updated this iteration by the
goal-decomposer). `drawdown_expectations_warm`'s per-claim loop is NOT in this iteration's IN-SCOPE list
-- do not add yield points there (stay to the one named risky change).

## UI Evolution
N/A -- Frontend Present: no. No new user-facing capability, no new information displayed, no new user
action, no UI surface change, no navigation change. Spec: "No visible change to any page... what changes
is reliability."

## Visual Requirements
N/A -- no frontend work this iteration.

## Key Test Scenarios

Full Given/When/Then text lives in the phase spec (`docs/phases/goal-ops-hardening-iter-52.md`
TC-1..TC-12); condensed here for quick reference:

- **TC-1/TC-2 (zero connection-level non-answers, solo + concurrent):** 1/s `GET /api/health` polling
  across a full finalize tail (all 8 warm phases) plus 30s past completion, solo and with a concurrent
  Factor Lab/Factor Combination request mid-warm -- zero `code=000`/timeout polls in either drill
  (closes the 9/653 solo and 19/892 concurrent findings).
- **TC-3:** per-poll latency vs. the owner-amended ≤2s bounded-compute ceiling recorded honestly in the
  new addendum, whether or not fully met for every poll.
- **TC-4 (no value change):** every warmed value byte-identical to a pinned pre-fix reference for the
  same finalize-tail run.
- **TC-5:** finalize-tail total wall-clock recorded and reconciled against the 1,200s budget, disclosed
  not silently loosened/exceeded.
- **TC-6 (new fault-injection test):** faulted category honestly omitted from `aggregates_refreshed`,
  `/api/health` stays 200 throughout + 30s after, a successfully-warmed category still serves correctly
  from the same process -- no restart.
- **TC-7:** Factor Lab page real-browser TTI + on-load API latency written into the new addendum.
- **TC-8 (hard gate, 3rd round):** J-04, J-05, J-06, J-07 each produce a real executed row (golden
  replay, screenshot, or LLM-fallback verdict) -- none "Deferred (iteration budget)", none zero-row.
- **TC-9 (hard gate, sequencing):** the 8-journey lane runs LAST -- no product file under
  `apps/backend/`/`apps/frontend/` has an mtime later than the lane's results-file mtime; any later
  fix-mode change forces a re-run before scoring.
- **TC-10:** `git diff --stat` over the 5 frozen surfaces (see above) stays EMPTY before and after.
- **TC-11:** every drill/test-created ingest job reads `provider="seed"` / `source: null` -- no live
  network call (AG-9).
- **TC-12:** J-01, J-03, J-08, J-09 all replay PASS with no new failure vs. iter-51 evidence.
- **Unit tests:** `test_data_manager.py`, `test_research_streaming.py`,
  `test_ingest_finalize_fault_injection.py`, `test_start_backend_script.py` plus this iteration's new
  tests all pass; no regressions. Full 30y suite is not run (this project's established convention --
  targeted + downstream-of-diff files only).
- **DoD line to get right this time:** iter-51's DoD checkbox falsely read "TC-1 through TC-9 all pass"
  while TC-5/TC-6 were unmet -- reviewer/QA/auditor must verify each TC individually against actual
  evidence, not accept a blanket checkbox.
