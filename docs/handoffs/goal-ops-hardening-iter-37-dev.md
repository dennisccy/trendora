# goal-ops-hardening-iter-37 Dev Handoff

**Phase:** goal-ops-hardening-iter-37
**Date:** 2026-07-30
**Agent:** developer
**Status:** complete

## What Was Built

- **The shared-cache fix (the one code defect, closing J-07).** `_do_backfill`
  (`apps/backend/app/engine/data_manager.py:2888`) now stashes the ONE prefilled `_BarCache` it already
  builds for a K-date backfill job onto a new internal `JobProgress._shared_bar_cache` field (unserialized
  scratch, declared next to `_backfill_per_date_seconds_sum`/`_backfill_concurrency`) instead of releasing
  it the moment it returns. `_refresh_ingest_aggregates` (the ingest finalize hook) now attaches that SAME
  cache (`attach_shared_cache`, zero re-scan) around its WHOLE finalize-tail body — not only the coverage
  sub-call — so every warm category that opens its own `bar_cache(session)` on a miss
  (`_persist_per_date_coverage_snapshots`'s coverage warm, `market_phase.market_phase_cached`'s per-date
  warm, `forward_testing.compute_drawdown_expectations_cached`'s per-claim warm, via `_causal_timeline`)
  transparently reuses the pre-loaded series (`bar_cache` is re-entrant on session id) instead of each
  opening its own fresh, unprefilled cache and lazily re-loading the benchmark (SPY) series. The release
  point (`_release_process_memory()`) moved from immediately after `_do_backfill`'s own `with` block to
  `_refresh_ingest_aggregates`'s own `finally`, nulling `prog._shared_bar_cache` first so `gc.collect()`
  can actually reclaim the ~1.13 GB block — preserving iter-27's "second consecutive rebuild starts lean"
  guarantee, just moving WHEN the release happens.
  - `_persist_per_date_coverage_snapshots` falls back to its own independent `prefilled_bar_cache` only
    when `prog._shared_bar_cache` is `None` (e.g. called directly, not through `_do_backfill`) — preserving
    its pre-iter-37 behavior byte-for-byte for that call shape, per the plan's explicit test-compat
    requirement.
  - `_do_backfill`'s own `finally`/exception path was restructured from a blanket `finally:
    _release_process_memory()` to `except Exception: prog._shared_bar_cache = None;
    _release_process_memory(); raise` — a whole-stage failure (no `_refresh_ingest_aggregates` will ever
    run for that job) still releases immediately, exactly as before this change; only the SUCCESS path now
    defers.
  - `_compute_coverage_uncached` / `compute_forward_aggregates` / `resolved_forward_aggregate_evidence` /
    `ensure_historical_forward_aggregates_dispatched` are byte-frozen — untouched by this diff.

## Files Changed
- `apps/backend/app/engine/data_manager.py` -- `JobProgress` gains `_shared_bar_cache` (unserialized
  scratch); `_do_backfill` stashes its shared cache and defers release on success (releases immediately on
  a whole-stage exception); `_persist_per_date_coverage_snapshots` attaches the shared cache when present,
  falls back to its own prefill otherwise; `_refresh_ingest_aggregates` wraps its ENTIRE finalize-tail body
  (coverage, per-date coverage warm, market-phase, forward-aggregates, research hot-keys, index-series,
  drawdown-expectations) in the shared-cache context and releases it once, in its own `finally`, after
  every category has run.
- `apps/backend/tests/test_backfill_coverage_shared_cache.py` -- NEW. A pinned pre-iter-37
  `_persist_per_date_coverage_snapshots` body (`git show HEAD:...` at this iteration's dispatch commit,
  verbatim) used as a byte-identity reference oracle against the shipped shared-cache implementation
  (`test_shared_cache_coverage_byte_identical_to_pinned_reference`), plus a mutation-style test that
  poisons one admitted symbol's series inside the shared cache and proves the shipped code is genuinely
  wired to it while the pinned reference (which never reads `_shared_bar_cache`) stays blind to the SAME
  poisoning (`test_shared_cache_mutation_caught_as_failure`).
- `reports/perf-budgets.md` -- new "Iteration 37" section: the fresh pre/post `test_bar_cache.py` load-count
  measurement, the TC-7/TC-8 oracle/mutation summary, and J-07 steps 1-4's live evidence (concurrent
  VmPeak + health-poll-during-warm measurement, and the throwaway-process memory-pressure drill), with a
  disclosed distinct finding (see Known Issues).
- `runs/goal-ops-hardening-iter-37/j07-warm/` -- evidence artifacts for steps 1-3 (`monitor.py`,
  `monitor.csv`, `health-latency.csv`, baseline/trigger/post-warm JSON captures).
- `runs/goal-ops-hardening-iter-37/mem-drill/` -- evidence artifacts for step 4 (`config.scratch.yaml`,
  `drill-log-excerpt.txt`, `seed-summary.json`, job/response JSON captures). The throwaway `drill.db`
  (~1.1 GB) and its `-wal`/`-shm` files were deleted after use — never committed.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest <path> -v` (exact paths/filters below; TMPDIR set
per the environment note).

**TC-6 — the target test, re-verified fresh pre-fix, then post-fix:**
- Pre-fix (unmodified HEAD, this iteration's own dispatch commit):
  `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` — **FAILED**,
  `max(load_counts.values()) == 10` (one symbol, `SPY` — traced via temporary call-site instrumentation to
  `market_phase_cached` (3 loads, one per new snapshot date) + `compute_drawdown_expectations` (5 loads,
  one per resolvable ledger claim) + the double coverage prefill (2) = 10; every OTHER symbol loaded
  exactly 2, from the double coverage prefill alone). This supersedes the iter-36 handoff's cited "max
  10/typical 2 on WIP, max 11/typical 3 on unmodified HEAD" — the tree had moved since that measurement;
  my own fresh measurement on true unmodified HEAD was max 10/typical 2, one better than iter-36's own
  HEAD reading.
- Post-fix: **PASSED** — `max(load_counts.values()) == 1`, `all(c == 1 ...)` — every symbol including
  `SPY` loaded exactly once for the whole K-date parallel job.

**Full result, this iteration's own new/target test files:**
- `tests/test_bar_cache.py` — 16 passed (101.44s)
- `tests/test_backfill_coverage_shared_cache.py` (new) — 2 passed (115.48s)

**Regression suites (coverage-snapshot / run-summary / backfill / finalize-hook / memory-error surfaces):**
- `tests/test_data_manager.py -k "coverage or aggregates_refreshed or persist_per_date or finalize_hook"` —
  52 passed, 85 deselected (125.12s)
- `tests/test_data_manager.py -k "backfill or release_process_memory or rebuild"` — 12 passed, 125
  deselected (167.75s)
- `tests/test_api_data.py` (full file) — 48 passed (7.18s)
- `tests/test_ingest_finalize_memory_pressure.py` (real `ulimit -v` subprocess, `_refresh_ingest_
  aggregates` called directly with no shared cache — exercises the `nullcontext()` fallback path) — 2
  passed (170.89s)
- `tests/test_data_manager_backfill_parallel.py` — 10 passed (245.30s)
- `tests/test_data_manager_backfill_committed_session.py` — 6 passed (433.40s)
- `tests/test_data_manager_membership_cache.py` — 10 passed (2.14s)
- `tests/test_data_manager_parallel.py` — 7 passed (6.14s)
- `tests/test_data_manager_concurrency_load.py` — 3 passed (1.33s)
- `tests/test_data_manager_jobs_pipeline.py -k "backfill or resume or interrupted or checkpoint"` — 9
  passed, 12 deselected (388.50s) — the 12 deselected tests (job creation/lifecycle counters/fetch-window
  plan/drift-report shape) exercise fetch/expand-stage mechanics that never touch `_do_backfill`'s bar
  cache; not run this pass for time (each test in this file reseeds a full DB) — no code path they cover
  was touched by this diff.

**Result: every test run passed. No regressions found.**

## Live J-07 Steps 1-4 Evidence

Full methodology, exact timestamps, and the per-TC verdict tables are in `reports/perf-budgets.md`'s new
"Iteration 37" section — summary here:

- **Steps 1-3, run CONCURRENTLY in ONE process for the first time this session** (PID 3900321,
  `logs/backend.log:140405`, real committed-seed DB, `dataset_version=r1880-f3974105`): the full 5-horizon
  forward-aggregate warm for `as_of=2026-07-17` completed in 69.44s
  (`09:31:08.991724Z → 09:32:18.432165Z`) while a 1 Hz `GET /api/health` poll ran throughout (130/130 HTTP
  200, max gap 1.9996s) and 11 concurrent re-reads of an already-cached baseline (`as_of=2026-07-21`) all
  came back byte-identical to the pre-warm capture. `VmPeak` stayed flat at 2,693,672 kB across all 16
  samples (5 pre-trigger + 11 during-warm) — 57.19% margin under the 6144 MB `server.memory_cap_mb` cap.
  Zero `MemoryError`/error/exception/traceback lines in the log for the whole window. Restart hygiene
  verified (clean stop, clean restart, HTTP 200 on first poll, clean stop again).
- **Step 4, throwaway process** (PID 3932092, port 8256, `memory_cap_mb=970` via `TRENDORA_CONFIG` scratch
  config, launched only via `scripts/start-backend.sh`): `POST /api/data/jobs` (0-target backfill no-op)
  ended `status: "ok"`; the log shows the EXACT iter-8 `except MemoryError` catch firing at
  `data_manager.py:3416` inside this iteration's own new `with cache_ctx:` wrap — `forward_aggregates`
  honestly absent from `aggregates_refreshed`; `drawdown_expectations` hit a SEPARATE `MemoryError` on a
  real ledger claim, caught by its own loop's isolation, independent proof the per-category isolation
  holds under the new wrap. `GET /api/health` returned 200 on every poll afterward, same PID, no restart.

## Known Issues

- **Pre-handoff verification: `scripts/dev.sh` (unmodified, out of this iteration's scope) does not
  fully clean up the frontend process tree on its own SIGTERM trap.** Started via `scripts/dev.sh`;
  confirmed both backend and frontend served HTTP 200 on first check. On stopping it (`kill -TERM` on the
  script's own bash PID, triggering its `trap "kill $BACKEND_PID $FRONTEND_PID ..."`), the backend
  (`uvicorn`) exited cleanly, but the frontend's actual `next-server` worker process (a grandchild of the
  `npm exec next dev` process the trap signals — `npm exec` → `sh -c "next dev"` → `node .../next dev` →
  `next-server`) was orphaned and kept listening on port 3255 after the wrapper exited; had to be killed
  directly (`kill -9`) to free the port. This is a pre-existing `scripts/dev.sh` defect (I made zero
  changes to that file — out of this iteration's `data_manager.py`-only scope), not something this
  iteration introduced or is asked to fix; recorded here per the Pre-handoff verification checklist's
  "verify it handles child processes" instruction. All Trendora-owned processes/ports (8255, 8256, 3255)
  were confirmed free before finishing this handoff.
- **TC-4 (step 4) did not reproduce iter-34's exact "previously cached read" shape.** This throwaway DB's
  own boot warm-up added 4 cadence-anchor `ScannerRun` rows (same as iter-34's run), advancing
  `dataset_version` to `r6-f1000015` — past R1's own pre-cached `ForwardAggregateCache` rows (stamped
  `r1-f1000000`, confirmed stale by direct query). `GET /api/backtest` (no `as_of`, the `is_latest`
  branch — never triggers a compute, J-08-safe) therefore correctly served an honest `"refreshing"`/
  all-`None` interim state rather than R1's real values — CORRECT dataset-version discipline (AG-5), not a
  defect. TC-4 was instead satisfied via `GET /api/health` (reliable throughout) and
  `GET /api/data/jobs/{id}` (the persisted run-status record, read 3× successfully). See perf-budgets.md
  for the full writeup.
- **New, distinct finding (not caused by this iteration, not blocking it): two OTHER read-path calls also
  hit their OWN uncaught `MemoryError` at the same `memory_cap_mb=970` throwaway cap** — `GET /api/data`'s
  coverage overview (encoding its ~500-symbol drift-diagnostic list into JSON,
  `starlette/responses.py:183`) and a direct `GET /api/backtest?as_of=2020-01-02` probe (`api/backtest.py`'s
  per-request `backfill_run_forward_returns` call, `forward_testing.py:2032`). Neither call site is
  `_do_backfill`/`_persist_per_date_coverage_snapshots`/`_refresh_ingest_aggregates` — this iteration's
  scope never touches them. `VmPeak` was already pinned exactly at the 970 MB cap from the
  `forward_aggregates` abort onward, so any further large allocation on the SAME tight cap is expected to
  be marginal. Recorded for a future iteration (widen the drill's cap, or extend the isolate-and-continue
  convention to those two call sites) — not a regression, not this iteration's DoD item.
- The pre-existing carried items from prior iterations (`warmup.py:194` badge wording,
  `_excluded_counts_by_date` duplicate-date double-count, Audit B6, the `closure_gate.py` backend-only
  regex false-positive, iter-33/g Regime Lab dispatch, iter-34/j the ≤0.1s health budget, iter-33/i
  `start-frontend.sh`/`HOST_GUARD_MARKER_FILES`) are all unresolved, unchanged, out of this iteration's
  scope per the spec — not re-opened.
- No UI/frontend work this iteration (`Frontend Present: no`); no new API contract, no new Data Contract
  value, no schema change.
