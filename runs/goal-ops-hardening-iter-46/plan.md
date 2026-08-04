# goal-ops-hardening-iter-46 Execution Plan

## What to Build

- **Bound `_combination_observations`** (`apps/backend/app/engine/research.py:748-807`). Today it builds
  `ret_by_run_symbol` as ONE dict over the entire horizon's `forward_returns` population (a streamed
  QUERY via `yield_per`, but an unbounded RETAINED dict — 1,285,609 rows at horizon=20 measured live) and
  then streams `ScannerResult` over ALL `runs_with_fr` in one pass. Refactor to the SAME
  discover-once/chunk-and-discard pattern its sibling `_factor_observations` already uses
  (`research.py:206-326`, fixed iter-29): reuse the shared `_runs_with_fr` helper to discover run ids
  once (bounded by run count, not pair count), walk them in slices of the EXISTING
  `research.factor_join_run_chunk` knob, build a per-slice join map mirroring `_fr_slice_map`
  (`research.py:206-223`), stream that slice's `ScannerResult`s ordered `(run_id, id)`, extend
  `observations`, and let the slice's dict be GC-eligible before the next slice starts. No new config
  knob. Slices walk the sorted `runs_with_fr` list in non-overlapping increasing ranges, so the
  concatenated output reproduces the exact prior global order — `observations` must stay byte-identical.
- **Bound `compute_drawdown_expectations`** (`apps/backend/app/engine/forward_testing.py:2270-2392`). The
  QUERY is already ticker-chunked (`research.drawdown_expectations_ticker_chunk`) and `yield_per`-streamed
  (lines 2332-2343), but every chunk's rows land in the SAME `stored_by_key` dict, which is retained
  whole until the separate phase-aggregation loop (lines 2354-2370) runs afterward over the full `rows`
  list. Restructure so each chunk's `stored_by_key` slice is folded into
  `by_phase_mdd`/`by_phase_uw`/`by_phase_ttr`/`by_phase_returns` immediately (this requires indexing the
  already-in-memory `rows` list — the `compute_samples` cohort, not the accumulator being bounded — by
  ticker once, e.g. `rows_by_ticker`, so each chunk's aggregation pass only touches that chunk's tickers)
  and the slice discarded before the next chunk begins. No new config knob. `by_phase` payload must stay
  byte-identical. This is the exact "bounded read, unbounded retention" shape the session's iter-40 lesson
  names — `.yield_per()` bounds the cursor, not the accumulator.
- **Fixture-backed byte-identity tests** for both refactors against a pinned pre-fix reference oracle
  (TC-3), including a reproduction of the live ledger's one `kind == "combination"` claim
  (`runs/goal-session-mcp-loop/state/certified-claims.jsonl`).
- **Live/instrumented size-bound assertions** (TC-1, TC-2) proving peak live accumulator size for both
  refactored functions is bounded by one chunk's width — mirror the existing pattern at
  `apps/backend/tests/test_research_streaming.py:678` (`test_factor_observations_accumulator_is_chunk_bounded`,
  which monkeypatches `_fr_slice_map` to record each slice's live size) for `_combination_observations`,
  and the analogous pattern for `compute_drawdown_expectations`'s per-chunk `stored_by_key` slice.
- **Guard the last two unprotected `logger.exception` calls** in `data_manager.py`: `_fail_unlaunched_job`
  (line 5058) and `_fail_unlaunched_resume` (line 5091) — replace with the existing `_log_isolation_failure`
  helper (already defined at `data_manager.py:3649`, already applied at the other 19 sites per iter-44/45).
  Add a parametrized textless-`MemoryError` test (TC-5) proving neither call escapes its handler.
- **Verify/correct `journey-scripts/J-07.json`'s dataset-size anchor** (TC-6). The committed file currently
  reads `"n=14647"` for step 2 (`/backtest`) and `"2532"` for step 3 (`/data`) — both were live-verified
  during iter-45's audit fix pass, but iter-45's own dev handoff disclosed this anchor is a derived
  aggregate that moves with every ingest (including this iteration's own TC-4/TC-7 live drills). Re-check
  both values against the CURRENT running backend/DB state at QA time and correct if stale — never assume
  the iter-45 values still hold.
- **Live drill: TC-7 (J-05's defining case).** Confirm a historical trading day absent from `/scanner-runs`
  (checked via the UI/API, not assumed), submit exactly that one day as a single-day backfill via `/data`,
  and record the honest outcome within 300s — reaches `ok` with `aggregates_refreshed` including
  `"membership_timeline"`, OR still fails but `logs/backend.log` now names the failure (per the TC-5
  logging convention). Per `runs/goal-session-ops-hardening/state/assumptions.md` iter-46: this iteration's
  diff does NOT accelerate the historical gap-fill path (only the append-forward case), and per
  `iteration-state.md`'s "Do not redo" list every live-testable gap today (`gap_last = 2019-02-25` vs
  latest snapshot `2026-07-31`) IS a gap-fill — so TC-7 is very likely to still hit the existing
  full-recompute fallback. Score it honestly either way; do not fabricate a pass.
- **Live drill: TC-4 (Evidence page under concurrent load)** — the actual proof the two accumulator bounds
  hold under real memory pressure, not just unit scale. With a heavy backfill/forward-aggregate-warm job
  running, load `GET /api/evidence` (rendering all 7 live ledger claims, so both hot spots are genuinely
  exercised) and confirm HTTP 200 within its committed budget (`/evidence` ≤ 3s steady-state per
  `reports/perf-budgets.md`), while `GET /api/health` stays responsive (HTTP 200) at every 1Hz poll
  throughout — closes iter-45/ap (the ~42-minute outage where 16/24 `MemoryError`s entered through
  `evidence.py:168`).
- **Full regression replay** of the required-still-passing set (J-01, J-03, J-04, J-06, J-08, J-09) plus
  the two target journeys (J-05, J-07) — 8 unique, dated, checksum-distinct screenshots (TC-9). The PNG
  provenance stamping landed in iter-45 (`demo_runner.py`) should prevent the J-03/J-04 duplicate-hash
  defect (TC-11) from recurring — re-verify it actually produces 8 distinct captures this run.

No frontend change — this is a backend-only reliability fix; the Evidence page, readiness badge, and
`/data` panels keep their existing shape and byte-identical served values (per the phase spec's own
"Frontend: None" and "UI surface changes: None").

## Agents Required
- developer: yes -- implement both accumulator-bound refactors (research.py, forward_testing.py), guard
  the two remaining `logger.exception` sites in data_manager.py, write the byte-identity + size-bound +
  TC-5 tests, verify/correct the J-07.json anchor, run the two live drills (TC-4, TC-7) against the real
  backend on the committed seed DB (via `scripts/start-backend.sh`/`scripts/start-frontend.sh` only, per
  AG-10), and write the dev handoff. No frontend-specific work — one agent covers this entire iteration.

## Frontend Present
no

## Files to Create/Modify
- `apps/backend/app/engine/research.py` -- refactor `_combination_observations` (~lines 748-807) to the
  chunked discover-once/slice-and-discard pattern mirroring `_fr_slice_map`/`_factor_observations`
  (~lines 206-326); no other function changes; `observations` output byte-identical.
- `apps/backend/app/engine/forward_testing.py` -- refactor `compute_drawdown_expectations` (~lines
  2270-2392) so each ticker chunk's `stored_by_key` slice folds into the by-phase accumulators immediately
  and is discarded before the next chunk; `by_phase` output byte-identical.
- `apps/backend/app/engine/data_manager.py` -- guard `_fail_unlaunched_job` (~line 5058) and
  `_fail_unlaunched_resume` (~line 5091) with `_log_isolation_failure` (already defined ~line 3649).
- `apps/backend/tests/test_research_streaming.py` -- new TC-1 (size-bound) and TC-3 (byte-identity) tests
  for `_combination_observations`, mirroring `test_factor_observations_accumulator_is_chunk_bounded`
  (~line 678) and `test_factor_observations_chunked_equals_unchunked_reference` (~line 708); include the
  live ledger's one `combination`-kind claim reproduction.
- `apps/backend/tests/test_forward_testing.py` -- new TC-2 (size-bound) and TC-3 (byte-identity) tests for
  the `compute_drawdown_expectations` refactor, alongside the existing chunking tests at ~line 1839
  (`test_drawdown_expectations_chunked_byte_identical_to_pinned_reference`) and ~line 1853.
- `apps/backend/tests/test_data_manager.py` -- new parametrized textless-`MemoryError` test (TC-5) for
  `_fail_unlaunched_job` / `_fail_unlaunched_resume`.
- `runs/goal-session-ops-hardening/journey-scripts/J-07.json` -- correct the dataset-size anchor(s) if the
  live-verified value has drifted from the currently-committed `"n=14647"` / `"2532"` (TC-6).
- `docs/handoffs/goal-ops-hardening-iter-46-dev.md` -- dev handoff (required by Definition of Done).

## Key Test Scenarios
- TC-1: `_combination_observations`'s refactored peak live accumulator size is bounded by (chunk width ×
  symbols-per-run), never the full ~1.28M-row horizon-20 population.
- TC-2: `compute_drawdown_expectations`'s refactored peak live `stored_by_key` size is bounded by one
  `research.drawdown_expectations_ticker_chunk` slice, never the claim's whole cohort.
- TC-3: both refactors are byte-identical to a pinned pre-fix reference oracle for the same inputs,
  including the live ledger's one `combination`-kind claim.
- TC-4: `GET /api/evidence` (all 7 live claims) stays within budget and `GET /api/health` stays responsive
  at every poll while a heavy ingest job runs concurrently — no MemoryError-triggered outage.
- TC-5: a parametrized textless-`MemoryError` test proves neither `data_manager.py:5058` nor `:5091`
  escapes its handler once guarded by `_log_isolation_failure`.
- TC-6: `journey-scripts/J-07.json`'s dataset-size anchor(s) match the live, verified dataset at QA time.
- TC-7: J-05's defining case (a day confirmed absent from `/scanner-runs`) gets a full-scale live drill,
  scored honestly whichever way it lands — this iteration's diff does not itself accelerate the
  gap-fill path, so a fail here is expected and must not be silently rounded to a pass.
- TC-8 (regression): J-07 steps 1-4 (full-basis warm, 1Hz health poll, VmPeak margin, induced-pressure
  abort) all hold, unchanged from iter-45's passing state.
- TC-9: the full required-still-passing set (J-01, J-03, J-04, J-06, J-08, J-09) plus J-05/J-07 all
  produce PASS-scored, dated, and — critically — checksum-unique evidence screenshots (no two journeys
  sharing one capture file; this has reopened twice already, iter-43/iter-45).
- Error-case: a per-claim compute failure (`MemoryError` or otherwise) at either bounded site still
  degrades via the existing isolate-and-continue contract (`expectations_status: "unavailable"` for that
  one claim only) — `GET /api/evidence` still returns HTTP 200 with every other claim rendered, never a
  crash or blank response.
- No anti-goal violation: AG-8's unbounded-load ban and AG-10's `memory_cap_mb=8192`/host-guard caps stay
  enforced end-to-end; no new proven-language introduced (AG-1/AG-4/AG-6 N/A — this cycle carries no
  Evidence Claims).

## Notes for the pipeline
- Coordinator instruction: do NOT run the full pytest suite (~10-11h on this data basis; it fork-locks the
  box). Run only the targeted test files/selections listed above, plus the two live drills through the
  real app via the launch scripts.
- Scope check against `docs/goal.md`: this iteration is a direct, in-scope continuation of J-05/J-07's
  standing AG-8 requirement ("`forward_returns` / `scanner_results` read column-projected and/or chunked
  into bounded accumulators") and the iter-45 evaluator's explicit next-step. No drift detected; the
  out-of-process watchdog and other carried items are correctly excluded per the phase spec's own OUT OF
  SCOPE section — no scope-creep flag needed.
