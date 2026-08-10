# goal-ops-hardening-iter-55 Dev Handoff

**Phase:** goal-ops-hardening-iter-55
**Date:** 2026-08-10
**Agent:** developer
**Status:** complete

## What Was Built

- **Honest-status fix (TC-1/TC-2/TC-4, DONE + unit-verified):** `_refresh_ingest_aggregates`'s
  `forward_aggregates_warmed` gate (`apps/backend/app/engine/data_manager.py:4230-4302`) now requires EVERY
  horizon in `cfg.walk_forward.horizons` to complete before `"forward_aggregates"` is appended to
  `aggregates_refreshed` — replacing the old any-horizon-succeeded gate that let a `MemoryError`-aborted
  warm (e.g. horizons 1/5/10 succeed, 20 aborts, 60 never attempted — the exact live-incident shape, run
  351/`logs/backend.log:233042`) still claim a full refresh. Tracks `_forward_horizons_completed` vs.
  `_forward_horizons_total`; the run's own `status` field and every sibling gate (`coverage`,
  `market_phase`, `latest_snapshot`, etc.) are untouched.
- **GIL-holding fix, profiled (partial result — see Known Issues):** added `_FORWARD_AGG_ROW_YIELD_CHUNK =
  5,000` intra-chunk `time.sleep(0)` yields inside both `_forward_agg_slice_map`'s row loop and
  `compute_forward_aggregates`'s own per-observation loop (`apps/backend/app/engine/forward_testing.py`) —
  previously these loops ran a WHOLE chunk (measured 24,272-51,778 rows live) with zero yield points between
  the existing once-per-chunk `time.sleep(0)`. Scheduling-only; byte-identity proven (see Tests below).
- **Golden-script hardening (TC-10):** `runs/goal-session-ops-hardening/journey-scripts/J-04.json` step 2
  race fixed — inserted a `wait_for` on the SAME ready CSS selector step 3 (now) asserts, with a 20,000ms
  budget, before the assertion, so the golden no longer fails on its own target behavior (an honest
  `data-state="initializing"` mid-boot at replay start).
- **Golden replay execution (TC-8/TC-9/TC-10):** J-05.json and J-07.json executed via the regression-replay
  lane for the first time this session — both PASS. J-04.json's fixed step 2 also PASSES against a
  cold-restarted backend.
- **Blueprint update:** `runs/goal-session-ops-hardening/state/blueprint.md` — the iter-55 top-level
  changelog paragraph and the "Job history"/"Backfill run-summary contract" row entries were already
  pre-authored by the decomposer (committed at `7cc9d2a2`); retagged both from `(targeted, not yet built)`
  to `(BUILT, pending evaluator confirmation)` with the specific test names that verify each fix. The
  iter-54 retags on "Regime score, market phase, realized forward-returns" / "Coverage payload" (the
  coherence-auditor's advisory) were already present — no further edit needed there.
- **Live TC-5/TC-6 drill + perf-budgets Addendum 19 (NOT MET, root-caused — see Known Issues).**

## Files Changed

- `apps/backend/app/engine/data_manager.py` -- `forward_aggregates_warmed` gate now requires all configured
  horizons to complete (lines ~4230-4302).
- `apps/backend/app/engine/forward_testing.py` -- new `_FORWARD_AGG_ROW_YIELD_CHUNK` constant + intra-chunk
  yields in `_forward_agg_slice_map` and `compute_forward_aggregates`'s per-observation loop.
- `apps/backend/tests/test_data_manager.py` -- inverted
  `test_finalize_hook_forward_aggregates_memory_error_after_partial_success_reports_honestly` (now asserts
  omission); added `test_finalize_hook_forward_aggregates_live_incident_shape_omits_but_preserves_siblings`
  (TC-1/TC-2/TC-4, the exact 1/5/10-succeed/20-fails/60-never-attempted shape, `cfg.walk_forward.horizons ==
  [1,5,10,20,60]` pinned).
- `apps/backend/tests/test_forward_testing_aggregates_streaming.py` -- added
  `test_compute_forward_aggregates_byte_identical_with_row_yield_firing_every_row` (TC-7): monkeypatches
  `_FORWARD_AGG_ROW_YIELD_CHUNK` to 1 (forces the new yield on every row) and re-runs the existing
  byte-identity comparison against the pinned pre-rewrite reference oracle for every horizon (1/5/10/20/60),
  with and without `as_of`.
- `runs/goal-session-ops-hardening/journey-scripts/J-04.json` -- new step 2 (`wait_for` the ready selector,
  20,000ms budget) inserted before the existing `data-state="ready"` assertion (now step 3); steps
  renumbered.
- `runs/goal-session-ops-hardening/state/blueprint.md` -- retagged the two iter-55 row entries from
  "(targeted, not yet built)" to "(BUILT, pending evaluator confirmation)" with cited test names.
- `reports/perf-budgets.md` -- Addendum 19 (TC-5/TC-6 live drill, full root-cause diagnosis).
- `reports/phase-goal-ops-hardening-iter-55-regression-replay-results.md` -- new; 6/7 PASS on the
  authoritative run + a reconciliation note for the one self-inflicted-contamination FAIL (see Known
  Issues).
- `runs/goal-ops-hardening-iter-55/evidence-drill/*.py` -- byte-identical copies of iter-54's proven drill
  harness (`run_drill_concurrent.py`, `poll_health.py`, `load_research.py`, `analyze.py`), unmodified.
- `runs/goal-ops-hardening-iter-55/replay-lane/j01-recheck-*` -- isolated single-instance J-01 re-run
  (evidence for the reconciliation note above).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/<file>.py -q` (TMPDIR set per the
coordinator's env note).

- `test_data_manager.py`: **202 passed** (includes the inverted test and the new live-incident-shape test).
- `test_forward_testing_aggregates_streaming.py` + `test_forward_testing_concurrency.py` +
  `test_forward_testing_serving_split.py`: **89 passed** (includes the new TC-7 row-yield-every-row test,
  10/10 parametrized cases).
- `test_ingest_finalize_memory_pressure.py`: **2 passed** (run standalone, 251.73s — spawns real
  memory-capped subprocesses).
- `test_forward_testing.py` (93 tests, uses the session-scoped `loaded_engine` fixture — a fresh temp DB
  backfilled + warmed across the FULL 30-year committed basis): started, ran for ~30 minutes without
  completing, and was killed by the harness's own background-task ceiling. This fixture's slowness is
  documented session-wide (session memory: "iter-18's 30y basis makes the full pytest suite ~10-11h,
  test-only, not a hang"), not a regression signal from this iteration's diff — none of the OTHER four test
  files (which exercise the exact functions this iteration touched, `compute_forward_aggregates` and
  `_refresh_ingest_aggregates`) showed any slowdown or failure. Flagged honestly below; a follow-up
  confirmation of `test_forward_testing.py` alone (ideally started early in a session with a longer budget)
  is recommended before this iteration is considered fully regression-clean on that one file.
- Live regression-replay lane (`demo_runner.py --mode verify`, J-01/J-03/J-04/J-05/J-07/J-08/J-09): **6/7
  PASS** on the authoritative run; the 1 FAIL (J-01) was traced to a self-inflicted process-management
  mistake (an orphaned `demo_runner.py` instance from an earlier launch attempt raced the surviving one
  against the SAME live backend state) and reproduced as a clean PASS on an isolated single-instance re-run
  — see `reports/phase-goal-ops-hardening-iter-55-regression-replay-results.md`'s reconciliation note. J-01
  is not a Target journey this iteration and no product code was touched in response.

## Known Issues

- **TC-5 (zero connection-level `/api/health` non-answers) is NOT MET.** The live drill (Addendum 19,
  `reports/perf-budgets.md`) recorded **11 non-answers** (up from the iter-54 baseline of 6), of which 9
  land inside `forward_aggregates_warm`'s horizon=10 sub-phase — the SAME phase this iteration's fix
  targets. Root-caused, not assumed: the SAME drill's own concurrent research-load process recorded its
  `GET /api/research/factor-lab?all=true` request receiving **no response within its own 600s client
  ceiling** (a fresh, uncached `compute_factor_lab_all` compute, triggered because the backfill's new
  snapshot bumped `dataset_version` and invalidated the concurrent load's cache key), followed by a
  `GET /api/research/factor-combination` request that took 429.412s — both overlapping
  `forward_aggregates_warm[10]`'s entire window. This is the well-documented CPython "GIL convoy" effect:
  two independently-yielding CPU-bound computations (this iteration's now-finer-grained
  `compute_forward_aggregates` chunk loop, AND the concurrent request's `compute_factor_lab_all`/
  `compute_factor_combination`, both already treated with `_cooperative_sorted`/`_cyclic_gc_paused` at
  iter-50/52) can still starve a third (health-check) thread for multi-second stretches, because a released
  GIL is not guaranteed to go to the longest-waiting thread. This is concrete, first-hand evidence for the
  STILL-OPEN owner decision named in this session's NOTES since iter-50/51: "(a) may heavy compute move to
  a separate process/worker boundary — the only way to guarantee the ≤2s health ceiling under ALL
  conditions." Fixing `compute_factor_lab_all`/`compute_factor_combination` further, or moving heavy compute
  to a separate process, is OUT OF this iteration's IN SCOPE list (`forward_testing.py`'s per-horizon call
  chain only) and is not attempted here — filed for the owner/next iteration with full evidence in Addendum
  19. TC-6 is disclosed (57/1,828 polls > 2.0s, comparable to the 53/1,815 baseline, not improved) and
  TC-7 (byte-identity of the fix itself) IS met.
- **The honest-status fix's own live drill did not exercise a fault.** All 5 horizons completed normally in
  the TC-5/TC-6 drill (no `MemoryError` injected), so `"forward_aggregates"` correctly remained in that
  job's `aggregates_refreshed` (DB-verified: `data_provider_runs.id=352`). The fix's actual FAULT PATH
  (omission on a mid-horizon abort) is proven only by unit test (fault-injection), not by this drill — an
  honest gap, not a defect: reproducing a genuine `MemoryError` live, on demand, inside a specific horizon
  is what the unit-level fault injector exists for precisely because a live drill cannot reliably trigger it.
- **`test_forward_testing.py`'s full run did not finish this dispatch** (see Tests Run above) — recommend a
  dedicated, early-session re-run to get a clean pass/fail signal on that one file specifically.
- **2 non-answers landed outside `forward_aggregates_warm`** this drill (`coverage_membership_timeline_
  refresh`, `per_date_coverage_warm` — both previously closed to zero at iter-53/54). Disclosed in Addendum
  19; not re-profiled this pass (a 1-event sample each is too small to diagnose without contaminating this
  iteration's one-risky-change scope; neither phase's code was touched this iteration, confirmed by
  `git diff --stat`).
- **J-06 stays out of scope**, per the phase spec's explicit deferral (the `/api/runs`/`/api/data/
  availability` DB-growth latency regression, `assumptions.md` iter-55) — not attempted, not claimed fixed.
