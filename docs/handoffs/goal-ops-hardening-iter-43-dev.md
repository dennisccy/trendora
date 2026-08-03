# goal-ops-hardening-iter-43 Dev Handoff

**Phase:** goal-ops-hardening-iter-43
**Date:** 2026-07-31
**Agent:** developer
**Status:** complete (code + unit/regression tests); live full-basis J-07 warm re-verification is
**incomplete** — see Known Issues, this is the honest headline finding of this pass.

## What Was Built

- **`_BarCache.prefill` iter-42 filter reverted** (`apps/backend/app/engine/prices.py`): the
  `WHERE symbol IN (expected_symbols)` filtered SELECT is removed; `prefill` is back to the
  unconditional whole-table streamed scan for every `expected_symbols` value (`None`, a non-empty
  list, or `[]`), byte-identical to the pre-iter-42 shape. `_SymbolColumns` (iter-41, B5) and the
  NULL-tolerance sentinel substitution (iter-42, B6) are UNCHANGED — only the filtering layer came
  out. The `bars_asof`/`bars_asof_window` lock-barrier fix for the publish race (iter-42 audit B1,
  `prices.py:364-377`/`:422-427`) was left byte-for-byte untouched, as directed — it is a correctness
  fix independent of the filter. Reason for the revert: the iter-42 auditor re-measured the filter's
  cost over the WHOLE job it runs inside (not `prefill` in isolation) and found a net **+5.1%
  peak-memory REGRESSION**, not the 2.5% reduction iter-42's own narrower measurement claimed — see
  `reports/perf-budgets.md`'s iteration-42 "AUDIT CORRECTION" section.
- **Job-launch-failure honesty** (`apps/backend/app/engine/data_manager.py`,
  `apps/backend/app/api/data.py`): `start_data_job`/`start_resume_job` now guard their
  `threading.Thread(...).start()` calls. A launch failure (the live incident:
  `RuntimeError: can't start new thread`) is caught and routed through two new helpers,
  `_fail_unlaunched_job`/`_fail_unlaunched_resume`, which mirror `_run_job`'s own outer
  `except Exception` mechanism (`prog.status = "failed"` + `_record_error`) and then close the
  run-history row via the existing `_finalize_run_record` (its documented no-open-row fallback
  correctly INSERTs a fresh terminal row for `start_data_job`'s case, since a launch failure never
  reaches `_create_run_record`; `_fail_unlaunched_resume` first rebuilds the minimal `JobProgress`
  shape `resume_data_job` would have, from the checkpoint, so the EXISTING open row from the paused
  attempt is closed instead of a duplicate being inserted). Both `thread.start()` call sites re-raise
  after recording the failure, so `POST /api/data/jobs` and `POST /api/data/jobs/{id}/resume`
  (`api/data.py`) catch `RuntimeError` and return `HTTPException(503, ...)` — never a
  `200 {"status": "running"}` over a job that never started.
- **`scripts/start-frontend.sh` HOST-GUARD block** (real path:
  `incredible_auto_dev/scripts/start-frontend.sh`, reached via the repo's own `scripts` ->
  `incredible_auto_dev/scripts` symlink): mirrors `start-backend.sh`'s block — sources
  `host-guard.env`, exports `OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/`MKL_NUM_THREADS`/
  `NUMEXPR_NUM_THREADS` from `HOST_GUARD_BLAS_THREADS`, prefixes the launched process with
  `taskset -c "$HOST_GUARD_CPU_LIST"` when `HOST_GUARD_ENABLED=1`. Placed BEFORE the existing
  build-if-stale section (not just around the final `next start`) so it also wraps the `next build`
  invocation — a stale-build path's multi-worker TypeScript/webpack compile is real CPU pressure
  from the QA/demo lanes, which is the concern goal.md names for this item.
  `project-extensions/host-guard/host-guard.env`'s `HOST_GUARD_MARKER_FILES` now lists all three
  launchers (`scripts/dev.sh scripts/start-backend.sh scripts/start-frontend.sh`).
- **Live re-verification (partial — see Known Issues):**
  - J-07 step 4 (induced-pressure drill): live re-run against the ALREADY-sanctioned env-gated fault
    injector, throwaway DB, launched only via `scripts/start-backend.sh` — full, clean PASS on all
    four acceptance clauses. Details + evidence: `reports/perf-budgets.md` "Iteration 43" §4.
  - J-07 steps 1-3 (live full-basis forward-aggregate warm) and J-05 step 2 (aggregates-refreshed
    confirmation): attempted live against the real committed-seed DB; the memory and availability
    axes both passed cleanly over a 1,001 s observation window, but the run never reached a terminal
    status within the session and a new latency finding (worsening `/api/health` response time
    during the compute window) is disclosed, unresolved. Full honest account:
    `reports/perf-budgets.md` "Iteration 43" §5/§6.
  - J-05 steps 1, 3, 4: confirmed (single-day backfill create-once, cold-restart coverage render,
    health responsive during a heavy job).

## Files Changed

- `apps/backend/app/engine/prices.py` -- reverted `_BarCache.prefill`'s iter-42 symbol filter to the
  unconditional whole-table scan; added an iter-43 docstring paragraph recording the revert and why
  (kept the iter-42 paragraph as historical record, per the file's own convention).
- `apps/backend/tests/test_bar_cache.py` -- replaced
  `test_prefill_symbol_filtered_query_when_expected_symbols_given` and
  `test_prefill_empty_expected_symbols_loads_nothing_no_malformed_query` with
  `test_prefill_expected_symbols_no_longer_filters_the_eager_scan` and
  `test_prefill_empty_expected_symbols_still_loads_full_table` (byte-identity oracles proving the
  revert). All other tests in the file (including the B1/B6 regression tests) left unmodified.
- `apps/backend/app/engine/data_manager.py` -- added `_fail_unlaunched_job`/`_fail_unlaunched_resume`;
  wrapped `thread.start()` in `start_data_job` (was `:4682`) and `start_resume_job` (was `:4705`) in
  `try/except RuntimeError`. **[AMENDED BY AUDIT — B3]** the two guards now catch `Exception` (always
  re-raised), not `RuntimeError` alone: `Thread.start()`'s other failure exit under the same memory
  ceiling is `MemoryError`, which left the job orphaned at `running` with no run-history row at all
  (live-proved, then fixed + regression-tested during the audit). `apps/backend/app/api/data.py`'s two
  503 mappings widened to `(RuntimeError, MemoryError)` to match. See
  `docs/handoffs/goal-ops-hardening-iter-43-audit.md` §2 B3 / §4.
- `apps/backend/app/api/data.py` -- `start_job` (`POST /api/data/jobs`) and `resume_job`
  (`POST /api/data/jobs/{import_id}/resume`) now catch `RuntimeError` from the `data_manager` call and
  raise `HTTPException(503, ...)`, matching the file's own existing 503 idiom two lines above
  `start_job`'s call site.
- `apps/backend/tests/test_data_manager.py` -- added
  `test_start_data_job_thread_launch_failure_marks_job_failed` (TC-3) and
  `test_start_resume_job_thread_launch_failure_marks_job_failed` (TC-4), placed after the
  `unfinished_engine` fixture (reuses `_add_resumable_checkpoint` for TC-4's setup).
- `scripts/start-frontend.sh` (real file: `incredible_auto_dev/scripts/start-frontend.sh`) -- added the
  HOST-GUARD block; the `next build` and final `next start` invocations are both now prefixed with
  `"${HOST_GUARD_CMD_PREFIX[@]}"`.
- `project-extensions/host-guard/host-guard.env` -- `HOST_GUARD_MARKER_FILES` now includes
  `scripts/start-frontend.sh`.
- `apps/backend/tests/test_start_frontend_script.py` -- added
  `test_start_frontend_applies_host_guard_and_skips_when_absent_or_disabled` (TC-5, one real `next
  build` shared across the enabled/absent/disabled cases via the skip-rebuild fast path) and
  `test_host_guard_marker_files_lists_start_frontend` (marker-registration check), plus their small
  supporting helpers (`_read_host_guard_env`, `_parse_cpu_list`, `_read_proc_status_cpus_allowed`,
  `_read_proc_environ` -- duplicated from `test_start_backend_script.py`, matching this file's own
  established convention of not cross-importing between test modules).
- `reports/perf-budgets.md` -- new "## Iteration 43" section (append-only) with the full live-drill
  and live-warm evidence, including the honest incomplete-measurement account.
- `docs/handoffs/goal-ops-hardening-iter-43-dev.md` -- this file.

No product database migration -- no schema change (same `DataProviderRun`/`JobProgress` fields reused).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_bar_cache.py -v`
Result: **22 passed** in 97.35s.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py -k "thread_launch_failure" -v`
Result: **2 passed** in 0.71s (TC-3, TC-4 in isolation, fast feedback).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py -q`
Result: **146 passed** in 402.16s (0:06:42) -- full file, includes TC-3/TC-4.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_ingest_finalize_fault_injection.py -v`
Result: **5 passed** in 0.65s -- the J-07 step-4 sanctioned hook's own unit suite, unmodified by this
iteration, confirmed still green post-revert.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_ingest_finalize_memory_pressure.py -v`
Result: **2 passed** in 157.37s -- the real, non-monkeypatched `ulimit -v` subprocess induction test,
unmodified, confirmed still green post-revert.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_start_frontend_script.py -k "host_guard" -v`
Result: **2 passed** in 83.56s -- the two new host-guard tests (one real `next build` shared across the
enabled/absent/disabled cases). The pre-existing TC-1/2/3 build-mode tests in this file were NOT re-run
this pass (no code they cover changed; time-bounded given this iteration's live-measurement cost).

Live drills (not pytest -- real launched processes, `runs/goal-ops-hardening-iter-43/`):
- `fault-drill/` -- J-07 step 4 live re-run: **full PASS**, all evidence captured (see perf-budgets.md
  §4). Clean start, clean stop, port confirmed free, no stray processes.
- `j05-live/` -- J-05/J-07-steps-1-3 live attempt: **partial** (see Known Issues below and
  perf-budgets.md §5/§6). Backend was stopped mid-run after 1,001 s of continuous, clean observation;
  a subsequent clean restart confirmed DB integrity and restart resilience. Port confirmed free, no
  stray processes, `logs/backend.log` shows a clean `Shutting down` / `Application shutdown complete`
  sequence for every boot in this session.

Full backend test suite was NOT run (per project convention -- the complete suite takes on the order
of hours against the 30-year basis; targeted files above cover every change this iteration made).

## Known Issues

**The live full-basis J-07 steps 1-3 re-verification did not complete this session, and this is the
single most important honest disclosure in this handoff.** A single-day backfill was triggered against
the real committed-seed DB (591 symbols, ~1,920 accumulated `ScannerRun` dates) to drive the ingest
finalize hook's full-horizon forward-aggregate warm through the SAME code path J-05/J-07 both depend
on. Observed continuously for 1,001 s (16.7 min; ~28 min including setup) before this pass stopped it:

- **Memory: a clean, wide-margin PASS.** `VmPeak` stayed PERFECTLY FLAT at 2,720,636 kB (32.4% of the
  8192 MB cap, 67.6% margin) for the entire observed window -- zero growth despite one OS thread
  running at ~90-99% CPU essentially continuously. This directly answers the question this iteration's
  mandated revert exists to answer, and the answer is unambiguous: no unbounded accumulation.
- **Availability: a clean PASS.** All 272 recorded `GET /api/health` polls (and the final poll issued
  immediately before this pass sent `SIGTERM`) returned HTTP 200. No freeze, no non-200, at any point.
- **Latency: a genuine, newly-disclosed regression against the rescoped ≤2s bounded-compute-window
  ceiling, NOT resolved this iteration.** 63.6% of the 272 polls exceeded 2s (up to 6.6s), and the
  trend WORSENED over the window (mean 1.7s in the first third, 3.2s in the last third) rather than
  staying flat the way every prior BCW measurement in `reports/perf-budgets.md` has. Two plausible,
  UNCONFIRMED explanations are recorded in the perf-budgets.md write-up: (a) iter-42's own carried,
  out-of-scope T2 finding (`_SymbolColumns.__getitem__`'s ~70-80x per-call slicing cost vs the
  `list[Bar]` it replaced) now applies to all 591 symbols instead of iter-42's 548, since the revert
  removes the filter that had been routing 43 ETF/index symbols through the faster lazy path; (b) a
  self-inflicted confound -- a manual `GET /api/backtest?as_of=2026-07-20` probe issued mid-session
  missed the freshly-bumped `dataset_version` and triggered a SECOND, concurrent forward-aggregate
  dispatch, so the later two-thirds of the observation window measure two competing GIL-bound warms,
  not one. **Neither hypothesis was confirmed or fixed.** T2 itself is explicitly out of this
  iteration's scope per goal.md's own carried disposition -- no change was made to `_SymbolColumns` or
  any warm-seam function in response to this finding.
- The run was stopped via `SIGTERM` (clean shutdown, confirmed) rather than left to complete
  unobserved or run indefinitely. A subsequent clean restart confirmed the interrupted job's own
  snapshot survived (transactionally committed before the finalize tail was stopped), the run-history
  row correctly reads `"interrupted"` (never stuck at `"running"`), and cold `GET /api/data` served
  the persisted coverage payload in 0.489 s -- an unplanned but useful confirmation that J-04's
  restart-resilience contract holds even under this session's own abrupt interruption.
- **Practical consequence:** J-05's step 2 (run record lists which aggregates the finalize hook
  refreshed) and J-07's full step-1/3 completion-and-cache-round-trip proof were NOT obtained live
  this session. TC-8 (a concurrent cached read staying 200 against the real deep-basis DB specifically)
  was also not cleanly obtained, for the same reason. The plan's conditional step 6 (bounding
  `compute_forward_aggregates` et al.) was correctly NOT triggered -- its trigger condition is
  specifically "over cap" or "wedging," and neither happened; the latency finding is a different axis
  the plan's conditional does not name.
- **Recommendation, not a decision made here:** the next iteration attempting this closure should
  either isolate T2's contribution cleanly (a single-trigger repeat with no manual mid-run probing) or
  address T2 directly (a bounded-window `_SymbolColumns` accessor for `bars_asof` that avoids
  reconstructing a full `Bar` per element). This is an owner/evaluator disposition call.

**`_BarCache.prefill` remains a COMPRESSION, not a BOUND, on `daily_prices`** after this revert -- carried
disposition from iter-42, unchanged by this iteration (explicitly out of scope: "a sixth
`_BarCache.prefill` bound attempt beyond this revert").

**T2's `bars_asof`/`bars_asof_window` ~70-80x latency regression** (iter-41's `_SymbolColumns`) remains
unresolved and out of this iteration's scope, per goal.md's own explicit carry-forward -- see the live
finding above for new evidence of its real-world cost, not a fix.

**The same thread-launch-guard gap in `warmup.start_warmup` / `forward_testing`'s background-dispatch
thread** (`forward_testing.py:1691`) is the same class of gap as the one fixed here, with no evidenced
incident -- deliberately deferred per the plan's own OUT OF SCOPE list.

**A full browser-driven regression replay of J-01/J-03/J-04/J-06/J-08/J-09 (TC-11) was not run by this
developer pass** -- per this iteration's TESTING REQUIREMENTS, that is the browser-qa lane's own step.
Backend-level spot checks during this session (J-09's `background_compute.active` disclosure confirmed
live and accurate in §5 of the perf-budgets.md write-up; J-03's `max_range_days` removal confirmed
still absent from config; J-08's storage-serving contract exercised live and cleanly against the
throwaway DB in §4) are offered as supporting evidence, not a substitute for the browser lane's own
pass.

## Pre-handoff verification

- **Service startup:** `scripts/start-backend.sh` was started and stopped cleanly three times this
  session (the fault-drill throwaway DB, the real-DB live-warm attempt, and its post-abort restart),
  each time reaching `/api/health` 200 within 1s and shutting down cleanly on `SIGTERM` with no port
  conflict on retry. `scripts/start-frontend.sh` was exercised three times within the new host-guard
  test (one real build + two skip-rebuild fast boots), all clean.
- **External integrations:** N/A for this iteration (no new adapter/scraper/external API -- all work is
  internal engine/launch-script code).
- **Native dependency binaries:** N/A -- no new dependency was added.
- **Process cleanup confirmed:** at the end of this session, `ss -ltn` shows ports 8255, 3255, 18999,
  19999, and the `test_start_frontend_script.py`/`test_start_backend_script.py` port ranges all free;
  `ps aux` shows no stray `uvicorn`, `next-server`, `monitor.py`, or `backtest_poller.py` process from
  this session (only the orchestrating `run-phase.sh`/`dev-phase.sh` pipeline processes that dispatched
  this developer pass remain, as expected).
