# goal-ops-hardening-iter-55 Execution Plan

## What to Build

- **Honest-status fix (data_manager.py):** `_refresh_ingest_aggregates`'s forward-aggregate warm loop
  currently sets `forward_aggregates_warmed = False` once (line 4234), flips it `True` the moment ANY
  configured horizon succeeds (line 4267, inside the per-horizon `try`), and never resets it on a later
  `MemoryError` `break`. Result: `refreshed.append("forward_aggregates")` (line 4280) fires even when
  horizons 20/60 never ran. Change the gate so it reads `True` only when EVERY horizon in
  `cfg.walk_forward.horizons` completed for that run — mirror the drop-on-incomplete convention already
  used by this same function's `drawdown_warmed`/`research_hot_keys` flags elsewhere in the file. The
  run's overall `status` field is untouched (isolate-and-continue stays AG-8-compliant) — only the
  completeness claim for `"forward_aggregates"` changes. No new field, no new status value (per
  `assumptions.md` iter-55, interpretation #1).
- **Existing test to invert, not just extend:** `test_finalize_hook_forward_aggregates_memory_error_after_partial_success_reports_honestly`
  (`apps/backend/tests/test_data_manager.py`, ~line 2049) currently asserts `assert "forward_aggregates"
  in refreshed` after horizon 1 succeeds and horizon 2 raises `MemoryError` with horizons 3..N never
  attempted — i.e. it currently encodes the PRE-FIX (buggy) behavior as correct. This test's assertion
  must be inverted to `assert "forward_aggregates" not in refreshed` (partial completion is no longer
  "honest partial report", it's incomplete) and its docstring corrected. Do not leave it passing
  unchanged — that would mean the fix didn't actually change behavior.
- **New fault-injection test for the exact live-incident shape (TC-1/TC-2/TC-4):** horizons 1, 5, 10
  succeed, horizon 20 raises `MemoryError`, horizon 60 never attempted (`cfg.walk_forward.horizons ==
  [1, 5, 10, 20, 60]`, confirmed in `config.yaml:777` — this is directly usable as the test fixture's
  horizon list, no synthetic override needed). Assert `"forward_aggregates"` is OMITTED from
  `aggregates_refreshed`/`refreshed`, and every other member that actually completed this run (e.g.
  `coverage`, `market_phase`, `latest_snapshot`) is still present. Also add the zero-horizons-completed
  boundary case (`MemoryError` on horizon 1 itself) — the existing
  `test_finalize_hook_forward_aggregates_memory_error_on_first_horizon_aborts_loop` test already covers
  this boundary and already asserts omission; confirm it still passes unchanged and cite it rather than
  duplicating it.
- **GIL-holding fix, profile-first (forward_testing.py):** profile the per-horizon call chain
  (`forward_aggregates_ingest_cached` → `compute_forward_aggregates`, `forward_testing.py:1143`) to find
  the actual non-yielding stretch between the h5/h10 sub-phase boundaries the developer's own 1,821-poll
  drill localized (iter-54 evidence, `reports/perf-budgets.md` Addendum 17) — NOT at the loop's existing
  per-horizon yield points (`prog.tick()` / `time.sleep(0)` before each horizon in
  `data_manager.py:4239-4245`, already added iter-52), and NOT at the existing per-run-chunk yield inside
  `compute_forward_aggregates` itself (`time.sleep(0)` at the top of `for start in
  range(0, len(runs_with_fr), run_chunk):`, `forward_testing.py:~1263`). Candidate stretch worth profiling
  first (not to be assumed as the answer — profile, then apply what the data shows): the per-chunk inner
  loop reading `ScannerResult` rows and updating six accumulators
  (`forward_testing.py:~1295-1330`, `for (res_run_id, ticker, ...) in
  session.exec(res_stmt).yield_per(batch): ...`) runs with no yield point between the outer chunk-level
  `time.sleep(0)` calls — a chunk's observation count (bounded by `run_chunk` runs × symbols-per-run) can
  still be large enough to hold the GIL for the whole h5–h10 window uninterrupted. Do not force-fit a
  prior iteration's specific mechanism (`_cooperative_sorted`/`_cyclic_gc_paused`/`bars_asof_window`)
  without re-profiling first — binding iter-48/50/53 discipline, restated in the phase spec. Whatever
  bounded/chunked/cooperative-yield construct the profile supports must keep
  `compute_forward_aggregates` the SOLE producer, called from the SAME three sites
  (`GET /api/backtest`, MCP `query_backtest`, the ingest finalize warm) — and must return byte-identical
  output for every horizon (1/5/10/20/60), with and without `as_of`, against a pinned pre-fix reference
  oracle (AG-3/AG-5, TC-7).
- **Live health-poll drill (TC-5/TC-6):** a ≥1,800-sample, 1 Hz `GET /api/health` drill spanning a real
  `forward_aggregates_warm` (reuse the proven concurrent-drill harness from iter-53/54,
  `runs/goal-ops-hardening-iter-54/evidence-drill/run_drill_concurrent.py`, unmodified where possible)
  must record zero connection-level non-answers (`http_code=000`), down from the iter-54 baseline of
  6/1,821 — all six were previously inside this exact phase. Disclose (not silently drop) the count of
  polls answering slower than the relaxed 2.0s BCW ceiling (iter-54 baseline: 53/1,821), whether it
  improved or not. Append a new dated addendum to `reports/perf-budgets.md` (do not edit prior
  addenda — append-only, per the file's own convention).
- **Golden replay execution (TC-8/TC-9/TC-10):** `journey-scripts/J-05.json` and `journey-scripts/J-07.json`
  already exist (authored, never replayed) — execute both via the regression-replay lane this iteration so
  each produces a real row in `regression-replay-results.md`. Before replaying `J-04.json`
  (`runs/goal-session-ops-hardening/journey-scripts/J-04.json`), fix its step 2 (currently asserts
  `[data-testid="readiness-badge"][data-state="ready"]` immediately after `goto /` with no wait — this is
  the exact race the iter-54 lesson names): add a `wait_for` on the readiness/health-derived steady state
  before the `data-state` assertion, so it passes against a backend still mid-boot at replay start. J-04's
  product behavior itself is already proven (iter-53/54) — this is a script-only regression-hardening fix,
  not a rebuild.
- **Blueprint update:** additively update `runs/goal-session-ops-hardening/state/blueprint.md` per the
  spec's "Blueprint conformance" section — a new top-level "iter-55 update" changelog paragraph; iter-55
  entries on the "Job history & per-date exclusion reasons" and "Backfill run-summary contract" rows
  describing both fixes; retag the "Regime score, market phase, realized forward-returns" and "Coverage
  payload" rows' iter-54 entries from "targeted, not yet built" to "BUILT + EVALUATOR-CONFIRMED" per the
  iter-54 coherence-auditor's advisory. No new row, no new Information Architecture surface.
- **Lane-ordering discipline (TC-11, carried forward verbatim):** the full 8-journey browser lane
  (J-01, J-03, J-04, J-05, J-07, J-08, J-09 required-still-passing/target set) runs LAST, after all code
  changes and unit tests are in place. If the post-lane audit finds a defect needing a further product-code
  change, it is filed as a note for iter-56 — not applied — so no `apps/backend/**`/`apps/frontend/**` file's
  mtime postdates the lane's own earliest artifact.

## Agents Required

- backend-data: yes -- the honest-status flag fix and the profiled GIL-holding fix, both in
  `apps/backend/app/engine/data_manager.py` and `apps/backend/app/engine/forward_testing.py`, plus their
  unit/fault-injection tests, the live health-poll drill, and the three golden-script executions/fixes.
- frontend-ux: no -- Frontend Present is `no` this iteration; zero `apps/frontend/` changes (the spec's
  own IN SCOPE "Frontend" section states this explicitly). The `aggregates_refreshed` list already renders
  on `/data`'s existing run-detail panel — it becomes accurate for the partial-completion case with no
  markup change.

## Frontend Present
no

## Files to Create/Modify

- `apps/backend/app/engine/data_manager.py` -- forward-aggregate warm loop (~lines 4234-4281): gate
  `forward_aggregates_warmed` on all-configured-horizons-complete instead of any-horizon-succeeded.
- `apps/backend/app/engine/forward_testing.py` -- `compute_forward_aggregates`
  (`~line 1143`) / its per-chunk inner loop (`~line 1295-1330`) / `_forward_agg_slice_map`
  (`~line 1121`): apply the profiled bounded/chunked/cooperative-yield fix for the h5-h10 GIL-holding
  stretch. Byte-identity is non-negotiable — do not touch grouping/math, only scheduling.
- `apps/backend/tests/test_data_manager.py` -- invert
  `test_finalize_hook_forward_aggregates_memory_error_after_partial_success_reports_honestly` (~line 2049)
  to assert omission; add the new TC-1/TC-2 fault-injection test for the horizons-[1,5,10,20,60]
  1/5/10-succeed-20-fails-60-never-attempted shape; confirm the existing first-horizon-fails test
  (~line 2028) still passes unchanged (TC-4 boundary case, already covered).
- `apps/backend/tests/test_forward_testing_aggregates_streaming.py` -- the existing home for
  `compute_forward_aggregates`'s streaming/chunking-bound regression tests (iter-14/29/30/32's own tests
  live here); add the new byte-identity test against a pinned pre-fix reference oracle for every horizon
  (1/5/10/20/60), with and without `as_of` (TC-7). Related files also exercising
  `compute_forward_aggregates`/`forward_aggregates_ingest_cached` if the fix's profiled mechanism touches
  concurrency or the ingest-cache split: `test_forward_testing_concurrency.py`,
  `test_forward_testing_serving_split.py`, `test_forward_testing.py`, `test_ingest_finalize_memory_pressure.py`
  -- re-run all four to confirm zero regressions even if unedited.
- `runs/goal-session-ops-hardening/journey-scripts/J-04.json` -- fix step 2 to `wait_for` the
  readiness/health-derived steady state before asserting `data-state` (TC-10).
- `runs/goal-session-ops-hardening/journey-scripts/J-05.json`,
  `runs/goal-session-ops-hardening/journey-scripts/J-07.json` -- execute as-is via the regression-replay
  lane (no edits expected unless replay surfaces a script bug).
- `reports/perf-budgets.md` -- new dated addendum for the TC-5/TC-6 live drill (append-only).
- `runs/goal-session-ops-hardening/state/blueprint.md` -- additive iter-55 update paragraph + row entries
  per "Blueprint conformance" above.
- `runs/goal-session-ops-hardening/state/assumptions.md` -- already carries the two iter-55 entries per
  the phase spec's NOTES section (verified present); no further edit expected unless a new interpretation
  call arises.
- `reports/phase-goal-ops-hardening-iter-55-regression-replay-results.md` (or session-standard path) --
  real executed rows for J-01, J-03, J-04, J-05, J-07, J-08, J-09 (J-06 informational only, not a target).
- `docs/handoffs/goal-ops-hardening-iter-55-dev.md` -- names both fixes with cited evidence (file:line, a
  measured number, or a test name) for each, per TC-13.

## UI Evolution
N/A -- Frontend Present: no. No new user-facing capability, no new information displayed beyond the
existing `aggregates_refreshed` field becoming accurate, no new user actions, no UI surface or navigation
changes.

## Visual Requirements
N/A -- Frontend Present: no.

## Key Test Scenarios

- TC-1/TC-4: fault-inject `MemoryError` at horizon 20 (after 1/5/10 succeed, 60 never attempted) and
  separately at horizon 1 (zero-horizons-completed boundary) -- both must OMIT `"forward_aggregates"`
  from the persisted run's `aggregates_refreshed`; the run's own `status` field is unaffected.
- TC-2: same fault-injected scenario -- every OTHER finalize-tail item that actually completed
  (`coverage`, `market_phase`, `latest_snapshot`, etc.) is still present in `aggregates_refreshed`.
- TC-3: all five configured horizons complete with no fault -- `aggregates_refreshed` still includes
  `"forward_aggregates"` exactly as before (no regression to the success path).
- TC-7: the profiled GIL-holding fix's output is byte-identical to a pinned pre-fix reference oracle for
  every horizon (1/5/10/20/60), with and without `as_of`.
- TC-5/TC-6: a live ≥1,800-sample, 1 Hz `GET /api/health` drill spanning `forward_aggregates_warm` records
  zero connection-level non-answers (down from 6/1,821) and discloses (not drops) the count of polls
  slower than the 2.0s BCW ceiling.
- TC-8/TC-9/TC-10: J-05.json and J-07.json each produce a real executed row in the regression-replay
  results (never SKIPPED/BLOCKED); J-04.json's fixed step 2 passes against a backend still mid-boot at
  replay start (no boot-race failure).
- TC-11: no `apps/backend/**`/`apps/frontend/**` file's mtime postdates the 8-journey lane's own earliest
  artifact -- any post-lane audit finding is filed as an iter-56 note, not applied.
- TC-12: every `data_provider_runs` row created this iteration reads `provider='seed'` (AG-9); the 5
  frozen host-guard paths (`config.yaml`, `host-guard.env`, `start-backend.sh`, `dev.sh`,
  `start-frontend.sh`) show empty `git diff --stat`/`git status --porcelain` (AG-10).
- Full regression: `apps/backend/tests/test_data_manager.py` and the forward-testing test file(s) run
  clean with zero failures; J-01, J-03, J-08, J-09 replay green (required-still-passing, full regression
  per this session's ESCALATE-cadence rule); J-05, J-07 scored as target journeys using real behavioral
  evidence (DB rows, HTTP statuses, log phase-timing lines), never a lane's sparse-poll summary alone.
