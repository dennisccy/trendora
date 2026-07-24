# goal-ops-hardening-iter-20 Execution Plan

Scope check: no drift found. This iteration keeps the historical `/backtest` carve-out lazy/create-once
(consistent with goal.md's own "cannot be precomputed (user-parameterized)" direction) while moving the
compute off the request thread — it reuses the codebase's existing `data_manager.start_data_job` /
`warmup.start_warmup` background-thread-plus-own-session idiom rather than inventing a new concurrency
abstraction (Simplicity First). The spec itself already excludes the two broader alternatives (removing
the carve-out; precomputing every historical date at ingest) and a long list of adjacent surfaces
(boot/health/readiness/warmup, the four sibling lazy caches, a generic job-queue framework). Nothing to
flag as out-of-bounds beyond what the spec itself already scopes out.

## What to Build

- A request-triggered, single-flight-guarded **background** dispatch in
  `apps/backend/app/engine/forward_testing.py` for a historical (`is_latest == False`) `asof_key` whose
  forward-aggregate evidence isn't `"ready"`: a daemon thread with its own `Session(engine)` that loops
  `cfg.walk_forward.horizons` calling the existing, unchanged `forward_aggregates_ingest_cached`. An outer
  guard (new lock + in-flight map keyed on `(asof_key, dataset_version)` — the SAME identity the resolver
  already uses) ensures at most one dispatch is ever in flight per identity; it is released in a `finally`
  on success AND on an owner exception, so a later request can always re-dispatch (no permanent wedge).
- `GET /api/backtest`'s historical branch (`apps/backend/app/api/backtest.py`) stops calling
  `forward_aggregates_ingest_cached` synchronously and re-resolving in-request. It triggers the new
  dispatch (a no-op if one is already in flight or the evidence is already `"ready"`) and returns
  immediately with whatever `resolved_forward_aggregate_evidence` already found. `ensure_loop_ms` is
  renamed/repurposed to a sub-millisecond dispatch-decision cost — never a compute-wait duration.
- Mirror the identical change in MCP `query_backtest` (`apps/backend/app/mcp/tools.py`), which today
  duplicates the same ensure-loop lines 279-298.
- Update the three existing tests that currently assert **synchronous same-call** completion of the
  historical ensure-loop, without weakening their compute-count/byte-identity assertions:
  - `test_historical_asof_keeps_pre_iter16_create_once_and_cache_behavior` and its iter-17 sibling
    `test_historical_asof_still_computes_once_even_when_older_fallback_evidence_exists`
    (`test_forward_testing_serving_split.py`) — must wait for the dispatched background compute to finish
    before asserting `evidence_status == "ready"`; keep asserting exactly `len(HORIZONS)` real
    `compute_forward_aggregates` calls total and zero more on the repeat view.
  - `test_backtest_evidence_is_as_of_scoped_expanding_window` (`test_api_backtest.py`) — same wait, then
    keep its existing `n_runs`/`asof_dates <= D` (AG-5) assertions unchanged.
- Add a new concurrency test (in or alongside `test_forward_testing_concurrency.py`) proving: (a) N=5
  concurrent first-touch `GET /api/backtest` requests for the SAME never-warmed historical date invoke
  `compute_forward_aggregates` exactly `len(horizons)` times total (never `5x`, never zero) and every
  response completes within budget without waiting on the compute (TC-3); (b) a dispatch-owner-thread
  failure releases the outer guard so a subsequent request can re-dispatch and eventually reach `"ready"`
  (TC-7), mirroring the existing `test_forward_aggregates_ingest_cached_waiter_does_not_deadlock_when_
  owner_raises` fixture (~line 468 of that file).
- Audit and correct (only where untrue under the new trigger) `RefreshingEvidenceBanner`'s and the
  `not_yet_computed` `EmptyState`'s copy in `apps/frontend/app/backtest/page.tsx` — no new component,
  fetch, or field.
- Write `docs/handoffs/goal-ops-hardening-iter-20-dev.md` stating how the outer guard is keyed and why it
  cannot duplicate work or wedge, backed by the TC-1/TC-3/TC-7 evidence actually produced.

## Agents Required

- developer: yes -- implements the backend dispatch mechanism + both caller updates, updates/adds the
  backend tests above, makes the frontend copy audit, and writes the dev handoff. This project's agent
  catalog has one `developer` role covering both backend and frontend (no separate backend-data/
  frontend-ux split) — the same agent does the small `page.tsx` copy fix alongside the backend work.

Frontend Present: yes

(Per this iteration's own goal-mode metadata and because TC-8/TC-9 require a live-rendered copy check and
TC-12 requires a browser walk of a first-ever historical `/backtest` view — no NEW UI capability, component,
or nav change is introduced; the only frontend diff is corrected copy in two pre-existing components.)

## Files to Create/Modify

- `apps/backend/app/engine/forward_testing.py` -- new outer single-flight dispatch guard + background
  thread function (own `Session(engine)`, mirrors `data_manager.start_data_job`/`warmup.start_warmup`);
  the existing per-horizon lock inside `forward_aggregates_ingest_cached` (~line 1016) stays unchanged.
- `apps/backend/app/api/backtest.py` -- historical branch (~lines 168-196): replace the synchronous
  ensure-loop with a non-blocking dispatch trigger; rename/repurpose the `ensure_loop_ms` timing field
  (check `test_backtest_timing.py`'s regex still matches before landing).
- `apps/backend/app/mcp/tools.py` -- mirror the same change (~lines 279-298).
- `apps/backend/tests/test_forward_testing_serving_split.py` -- update the two named tests (~lines 758,
  802) to wait for background-dispatch completion.
- `apps/backend/tests/test_api_backtest.py` -- update `test_backtest_evidence_is_as_of_scoped_expanding_
  window` the same way; this file's other 11 tests share the ~80-minute `loaded_engine` fixture (binding,
  "Do not redo" — cite, do not run wholesale); confirm whether the one updated test can run isolated from
  that fixture or needs a lighter double, per the file's own existing pattern.
- `apps/backend/tests/test_forward_testing_concurrency.py` (or a co-located new file matching its naming
  convention) -- add TC-3 and TC-7.
- `apps/frontend/app/backtest/page.tsx` -- correct `RefreshingEvidenceBanner` copy (~296-304, currently an
  unconditional "the dataset has changed... reload after the next ingest finishes" claim that is untrue
  for a historical-view-triggered dispatch with no ingest involved) and the `not_yet_computed` `EmptyState`
  copy (~236-240, currently states only "backfilling or fetching data" starts a compute — viewing the page
  now also does).
- `docs/handoffs/goal-ops-hardening-iter-20-dev.md` -- new dev handoff (required by DoD).
- `reports/perf-budgets.md` -- append a TC-13 section ONLY if the owner authorizes the concurrent-ingest
  trigger this iteration (contingent, AG-10-gated); otherwise no developer-side edit — record the block
  plainly in the handoff instead.

## UI Evolution

- New user-facing capability: none new — a first-ever view of a not-yet-warmed historical `/backtest` date
  (already possible since J-14/17/18) becomes honestly responsive (renders within the ≤1.5s budget) instead
  of blocking up to ~54s.
- New information displayed: none — reuses the existing `evidence_status`/`evidence_generated_at`/
  `evidence_asof`/`evidence_by_horizon` fields exactly as already displayed.
- New user actions: none.
- UI surface changes: none new — `RefreshingEvidenceBanner`/the `not_yet_computed` `EmptyState` (both
  pre-existing) may get corrected copy only; no new panel, page, or control.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing `Card` + `Loader2` (spinning, warn-toned) for
  `RefreshingEvidenceBanner` and the existing `EmptyState` component — no new component library usage.
- Layout: unchanged — same position in the `/backtest` page (bottom, after the leadership lists, above/around
  the evidence aggregate section).
- Key visual effects: none new.
- States to handle: the three existing `evidence_status` states (`ready` / `refreshing` /
  `not_yet_computed`) — only the copy under `refreshing` and `not_yet_computed` needs re-verification
  against the NEW historical-view-dispatch trigger (distinct from the pre-existing latest-view
  version-bump / true fresh-install triggers that copy was originally written for); correct only what is
  now factually untrue, keep the calm/factual/never-fabricated tone already established on this page.

## Key Test Scenarios

Developer-executable via scoped pytest (host-guard-confined: `taskset -c 0-3,8-11`, BLAS/OMP=4, never the
full suite, never concurrent pytest runs — AG-10):
- TC-1: a never-warmed historical `as_of` returns HTTP 200 fast with `evidence_status` in
  `{"refreshing","not_yet_computed"}` (never blocking on its own compute) and dispatches exactly one
  background compute.
- TC-2: the timing log's dispatch-decision field is sub-millisecond, never a multi-second wait.
- TC-3: 5 concurrent first-touch requests for the same never-warmed date → `compute_forward_aggregates`
  invoked exactly `len(horizons)` times total (never 5x, never 0), every response fast.
- TC-4: once the dispatched compute completes, a later request serves `"ready"`, byte-identical to a direct
  `compute_forward_aggregates` call, every horizon.
- TC-5: `GET /api/health` stays within its ≤0.1s budget throughout a dispatched background warm.
- TC-6: MCP `query_backtest` behaves identically to the HTTP endpoint for the same never-warmed date.
- TC-7: a dispatch-owner-thread failure releases the outer guard; a subsequent request re-dispatches and
  eventually reaches `"ready"`.
- TC-8 / TC-9: `RefreshingEvidenceBanner` / `EmptyState` copy contains no claim untrue for the
  historical-view-dispatch cause; corrected if it fails this check.
- TC-10 / TC-11: the three updated tests still hold their original compute-count/byte-identity/no-lookahead
  guarantees under the new dispatch model.
- TC-16: `compute_forward_aggregates` and `resolved_forward_aggregate_evidence`'s fallback logic are
  byte-unchanged vs. iter-19 (no second producer/resolver introduced) — a diff check, not a new test.
- Regression: `test_forward_testing_serving_split.py`, `test_forward_testing_concurrency.py`,
  `test_forward_testing.py` (cite, its shared fixture already timed out for iter-19 on this host — do not
  force it), `test_backtest_timing.py` keep passing; the pre-existing `test_db.py::test_create_all_
  produces_expected_tables` failure is carried, not new.

QA-stage / browser (not developer-run):
- TC-12: a live browser view of a never-viewed historical `/backtest?as_of=` renders within budget showing
  `RefreshingEvidenceBanner` or the `EmptyState` (never blank/frozen), and a reload after the background
  compute completes shows that date's own real evidence. Operator-curl fallback for the timing half only if
  Chrome MCP (port 9224) is still wedged; the copy-correctness half (TC-8/TC-9) needs a live render.
- TC-15: deterministic golden replay confirms J-01/J-03/J-05 (Required-still-passing) did not regress.

Operator-gated, contingent, not this iteration's blocker (document attempt/outcome plainly either way):
- TC-13: concurrent-ingest-overlay `/backtest` re-measurement (owed since iter-17/18/19, AG-10 ingest-trigger
  classifier).
- TC-14: disruptive J-04 kill/restart replay (owed since iter-15, same gate).
