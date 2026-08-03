# goal-ops-hardening-iter-43 Execution Plan

## Context (for the developer, not re-derived)

Resume from the iter-42 REGRESSION_HALT. The owner already committed the memory-envelope raise
(`1376601c`, 2026-07-31): `config.yaml` `server.memory_cap_mb` 6144→**8192** (confirmed live at
`config.yaml:1363`), `host-guard.env` `HOST_GUARD_MEMORY_HIGH` 10G→**12G** (confirmed live at
`host-guard.env:66`) — **these values are NOT this iteration's diff, do not touch them.** This
iteration executes the four follow-up actions that amendment commissioned, plus one separately-named
job-launch honesty fix. Verified directly against the current tree (HEAD `1376601c`, clean except
goal-engine bookkeeping):
- `apps/backend/app/engine/prices.py:247-258` still applies the iter-42 `WHERE symbol IN
  (expected_symbols)` filter inside `_BarCache.prefill` (`prices.py:172`) — the revert has not landed.
- `apps/backend/app/engine/data_manager.py:4682` and `:4705` call `thread.start()` with no
  try/except in `start_data_job`/`start_resume_job` — the guard has not landed.
- `scripts/start-frontend.sh` has no HOST-GUARD block at all (confirmed by direct read); `host-guard.env:86`
  still reads `HOST_GUARD_MARKER_FILES="scripts/dev.sh scripts/start-backend.sh"`.
- `reports/perf-budgets.md`'s last dated section is the owner's own "OWNER AMENDMENT" (line 5607,
  re-expressed old numbers only, no new live measurement) — a fresh "## Iteration 43" section is
  needed, following the existing per-iteration naming convention (`## Iteration NN — <summary>
  (<date>, developer)`, see lines 5422, 5329, 5211 for the pattern).

## What to Build

1. **Revert `_BarCache.prefill`'s iter-42 symbol filter** (`prices.py`) back to the unconditional
   whole-table streamed scan. Keep iter-41's `_SymbolColumns` columnar storage AND the B6 NULL-tolerance
   sentinel — only the `WHERE symbol IN (...)` filtering layer added in iter-42 comes out. Keep the B1
   `KeyError` publish-race lock-barrier fix in `bars_asof`/`bars_asof_window` (`prices.py:364-377`,
   `:422-427`) byte-for-byte unchanged — it is a correctness fix, independent of the filter, and must
   survive the revert with its regression test still passing (TC-2).
2. **Guard the two unguarded `thread.start()` calls** in `start_data_job`/`start_resume_job`
   (`data_manager.py:4682`, `:4705`) so a launch failure (the live incident:
   `RuntimeError: can't start new thread`) reaches the SAME `prog.status = "failed"` +
   `_record_error(prog, message)` mechanism `_run_job`'s own outer handler already uses
   (`data_manager.py:4505-4506`), instead of leaving the job at its `create_job()`-time `running`
   default forever (the exact B5 signature: `dates_done 0/1`, frozen `last_progress_at`, no worker
   line, ever). The two HTTP call sites (`apps/backend/app/api/data.py:191`, `:254`) currently build a
   response dict with a hardcoded `"status": "running"` unconditionally after calling
   `start_data_job`/`start_resume_job` — wire an honest error response for this case (the file's own
   existing idiom is `raise HTTPException(status_code=503, detail=...)`, used two lines above the
   `start_data_job` call at `api/data.py:177`), never a 200 over an orphaned job.
3. **Add a HOST-GUARD block to `scripts/start-frontend.sh`**, mirroring `scripts/start-backend.sh`'s
   existing block (`start-backend.sh:68-94`: source `host-guard.env`, export
   `OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/`MKL_NUM_THREADS`/`NUMEXPR_NUM_THREADS` from
   `HOST_GUARD_BLAS_THREADS`, prefix the launched process with `taskset -c "$HOST_GUARD_CPU_LIST"` when
   `HOST_GUARD_ENABLED=1`). Add `scripts/start-frontend.sh` to `HOST_GUARD_MARKER_FILES` in
   `project-extensions/host-guard/host-guard.env:86` (currently lists only `dev.sh` and
   `start-backend.sh`).
4. **Live re-verify J-07 (steps 1-4)** against the committed `memory_cap_mb: 8192`: full-horizon
   forward-aggregate warm through the real ingest-finalize path, `GET /api/health` polled at 1Hz
   throughout (every poll HTTP 200 within the rescoped ≤2s bounded-compute-window budget —
   `reports/perf-budgets.md` line ~5654), a previously-cached `GET /api/backtest` read served
   concurrently, VmPeak recorded with its margin under 8192 MB in the new dated section. Re-run step
   4's EXISTING sanctioned induced-pressure test hook (do not tune a fresh cap — binding iter-39
   lesson) and confirm the SAME process keeps serving `/api/health` + cached reads through the abort.
5. **Live re-verify J-05** via `runs/goal-session-ops-hardening/journey-scripts/J-05.json`: a
   single-day backfill against the reverted prefill + raised cap serves stored aggregates with zero
   recompute-on-read, and the persisted run record lists the finalize hook's refreshed aggregates.
6. **Conditional, only if step 4's live measurement shows the warm still over 8192 MB or the
   pressure-abort still wedging the process:** bound `compute_forward_aggregates` /
   `_forward_agg_slice_map` / `_fr_slice_map` / `ensure_historical_forward_aggregates_dispatched`
   (`apps/backend/app/engine/forward_testing.py`) — now permitted (not mandated) by goal.md's "warm
   seam is UNFROZEN" clause. Byte-identical output required for all 5 configured horizons, with and
   without `as_of`. **If the measurement passes comfortably (ground-truth prior: 2.6-3.7 GB VmPeak
   against the new 8192 MB cap, i.e. 32-44%), do NOT touch these functions — document the passing
   measurement instead.**
7. **Full regression replay** of the six required-still-passing journeys (J-01, J-03, J-04, J-06, J-08,
   J-09) against this iteration's build — the six passes recorded at iter-42 were photographed minutes
   before that iteration's live outage, so they need fresh dated evidence, not a carry-forward.
8. Dev handoff at `docs/handoffs/goal-ops-hardening-iter-43-dev.md`.

## Agents Required

- backend-data: yes -- all in-scope work is backend engine code, one API error-handling path, two
  launch scripts, and a perf-budgets measurement/write-up (items 1-6 above). No product database
  migration is implied (no schema change — same `DataProviderRun`/`JobProgress` fields, reused
  vocabulary).
- frontend-ux: no -- no `apps/frontend/` file is in scope. J-05/J-07 re-verification drives existing
  pages (badge, `/backtest`, `/data`) through the browser-QA replay lane, not through any frontend code
  change.

Frontend Present: no

## Files to Create/Modify

- `apps/backend/app/engine/prices.py` -- revert `_BarCache.prefill`'s (`:172`) `WHERE symbol IN
  (expected_symbols)` filter (`:247-258`) to the unconditional whole-table scan; keep `_SymbolColumns`,
  the NULL-tolerance sentinel, and the `bars_asof`/`bars_asof_window` lock-barrier fix (`:364-377`,
  `:422-427`) unchanged.
- `apps/backend/tests/test_bar_cache.py` -- replace/update the filter-specific tests
  (`test_prefill_symbol_filtered_query_when_expected_symbols_given` at `:148`,
  `test_prefill_empty_expected_symbols_loads_nothing_no_malformed_query` at `:204`) with a
  byte-identity oracle against the pre-iter-42 (unfiltered) reference body (TC-1); keep
  `test_prefill_null_numeric_column_degrades_without_crashing` (`:217`, B6) and the B1 KeyError-race
  regression test passing unmodified (TC-2).
- `apps/backend/app/engine/data_manager.py` -- guard `thread.start()` in `start_data_job` (`:4682`)
  and `start_resume_job` (`:4705`); on a launch exception, set `prog.status = "failed"` +
  `_record_error(prog, message)` (mirrors the outer handler at `:4505-4506`) and surface the failure to
  the caller instead of returning `job.job_id` as if the job is live.
- `apps/backend/app/api/data.py` -- the two call sites (`:191` `start_data_job`, `:254`
  `start_resume_job`, both currently building an unconditional `"status": "running"` response) must
  return an honest HTTP error (e.g. `HTTPException`, matching the file's own existing idiom at `:177`)
  when the launch itself failed, never a 200 over an orphaned job.
- `apps/backend/tests/test_data_manager.py` -- new tests: mock `threading.Thread.start()` to raise
  `RuntimeError` inside `start_data_job` (TC-3) and `start_resume_job` (TC-4); assert the job reaches
  `failed` with a descriptive message and the HTTP layer's response is an honest error, not a 200.
- `scripts/start-frontend.sh` -- add the HOST-GUARD block mirroring `start-backend.sh:68-94`
  (source `host-guard.env`; export BLAS/OMP/numexpr thread-count env vars; prefix the launched `next
  start` with `taskset -c "$HOST_GUARD_CPU_LIST"` when enabled).
- `project-extensions/host-guard/host-guard.env` -- add `scripts/start-frontend.sh` to
  `HOST_GUARD_MARKER_FILES` (`:86`).
- `reports/perf-budgets.md` -- new dated "## Iteration 43" section (append-only, after the OWNER
  AMENDMENT section) with the live J-07 steps 1-3 VmPeak measurement + margin under 8192 MB, the step-4
  induced-pressure re-run outcome, and (if step 6 was skipped) an explicit note that the warm-seam
  functions were left untouched because the measurement passed.
- (Conditional, only if step 6 above triggers) `apps/backend/app/engine/forward_testing.py` --
  bounded-footprint change to `compute_forward_aggregates`/`_forward_agg_slice_map`/`_fr_slice_map`/
  `ensure_historical_forward_aggregates_dispatched`; byte-identity fixture test alongside it.
- `docs/handoffs/goal-ops-hardening-iter-43-dev.md` -- new dev handoff.

## Out of Scope (carry forward, do not attempt)

- A sixth `_BarCache.prefill` bound attempt beyond this revert (the "compression, not a bound"
  disposition on `daily_prices` stays carried, unresolved — state this honestly in the QA report's
  AG-8 row, never an unqualified pass).
- T2's `bars_asof` 70-80x latency regression (iter-41's `_SymbolColumns`, unrelated to the filter
  reverted here).
- The same thread-launch-guard gap in `warmup.start_warmup` / `forward_testing`'s background-dispatch
  thread (`forward_testing.py:1691`) -- same class of gap, no evidenced incident, deliberately deferred.
- iter-33/g Regime Lab's cold `view=pooled` dispatch (deferred an eighth time).
- J-07's `[NEW]` walkthrough recording (capture-only, not this iteration's goal).
- Any further change to `memory_cap_mb` / `HOST_GUARD_MEMORY_HIGH` / the machine-wide budget beyond
  the owner's already-committed values -- byte-frozen this iteration.
- Any further `docs/goal.md` edit.

## Key Test Scenarios

- TC-1: `_BarCache.prefill` reverted -- called with an `expected_symbols` subset, the returned `Bar`
  sequence for every symbol is byte-identical to the pre-iter-42 (unfiltered) oracle; no `WHERE symbol
  IN (...)` applied to the SELECT.
- TC-2: the B1 `KeyError` publish-race regression test (concurrent `bars_asof`/`bars_asof_window`
  under the reverted prefill) still passes unmodified.
- TC-3: `threading.Thread.start()` mocked to raise `RuntimeError("can't start new thread")` inside
  `start_data_job` -- the created job's `status` reaches `failed` with a message naming the
  thread-launch failure; no row left at `running` with zero further updates.
- TC-4: same mocked failure inside `start_resume_job` -- the resumed import's row reaches `failed`
  with a descriptive message via the same mechanism.
- TC-5: `scripts/start-frontend.sh` applies the same HOST-GUARD block `start-backend.sh` already
  applies when `host-guard.env` declares the values; `HOST_GUARD_MARKER_FILES` lists all three
  launchers.
- TC-6: browser-qa replay of `journey-scripts/J-05.json` -- single-day backfill; `/scanner-runs` lists
  the ingested date with its stored snapshot; persisted run record lists the finalize hook's refreshed
  aggregates; zero recompute-on-read.
- TC-7/TC-8: full-horizon forward-aggregate warm via ingest finalize with `memory_cap_mb: 8192`;
  `GET /api/health` polled at 1Hz throughout returns HTTP 200 within the rescoped ≤2s bounded-window
  budget on every poll; a concurrent cached `GET /api/backtest` read returns HTTP 200 throughout; VmPeak
  recorded with its margin under 8192 MB.
- TC-9: the sanctioned J-07 step-4 induced-pressure hook (throwaway process, tightened cap, launched
  only via `start-backend.sh`) aborts the warm honestly while the SAME process keeps serving
  `/api/health` and previously-cached reads -- no deadlock, wedge, or restart.
- TC-10 (conditional -- only if TC-7/TC-9 show the cap or abort path insufficient): the bounded
  `compute_forward_aggregates` implementation is byte-identical to the pre-bound reference for all 5
  horizons, with and without `as_of`.
- TC-11: full regression replay of J-01, J-03, J-04, J-06, J-08, J-09 -- all six report PASS with fresh
  dated evidence (screenshot or replay row) against this iteration's build, not a carry-forward from
  iter-42.

## Notes for reviewer / QA / auditor

- Binding iter-42 lesson (apply verbatim): a memory measurement that only measures the work REMOVED is
  not a measurement -- any before/after figure for the revert, or for the conditional warm-seam bound,
  must measure the whole job (prefill + the lazy loads it now forces), not a narrowed function. This is
  exactly the mistake iter-42's own TC-6 script made (B2) -- do not repeat it in reverse.
- Binding iter-39 lesson: reuse the ALREADY-sanctioned J-07 step-4 induced-pressure test hook; do not
  tune a fresh cap.
- Six consecutive evaluators called the `GET /api/health` steady-state budget an owner decision; the
  owner has now rescoped it (not waived it). This iteration re-measures against the NEW table (steady
  state ≤0.1s unchanged, BCW ≤2s) -- it does not revisit the decision itself.
- AG-10 stays enforced end-to-end throughout (strengthened, not weakened, by the `start-frontend.sh`
  addition) -- never remove/weaken/bypass a host-guard cap block regardless of test outcome.
