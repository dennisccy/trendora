# goal-ops-hardening-iter-32 Dev Handoff

**Phase:** goal-ops-hardening-iter-32
**Date:** 2026-07-29
**Agent:** developer
**Status:** complete

## What Was Built

- **Eliminated `stock_obs`, the last unbounded accumulator in `compute_forward_aggregates`'s own function
  family.** The function used to grow one ~9-field dict per `(run_id, ticker)` observation across the
  WHOLE horizon-partition (770K-800K live per horizon) purely so `_group_means`/`_group_mdd`/
  `_control_groups`/`_attribution_slices` could each re-derive their own group buckets from it at the very
  end. Every one of those consumers is now driven by state built INCREMENTALLY inside the existing
  per-chunk loop (`walk_forward.forward_agg_run_chunk`-sized run-id slices, iter-30), bounded by the
  number of distinct groups/runs/tickers rather than by the observation count:
  - **`_ExactMeanAcc`** — a new streaming-mean class that reproduces `statistics.mean`'s own exact
    algorithm (group floats by their exact `as_integer_ratio()` denominator, sum the per-denominator
    numerators once, convert to float on read). Fraction addition is exact and therefore
    associative/commutative, so the result is bit-for-bit identical to `statistics.mean(values)`
    regardless of add order — proven directly (200 random trials, shuffled order, zero mismatches) before
    relying on it. Its own memory is bounded by the number of DISTINCT denominators IEEE-754 doubles can
    produce (at most a few thousand), never by how many values were added.
  - **`_GroupAcc`** — one group value's paired return-mean + max-drawdown-mean state (the bounded
    replacement for `_group_means`/`_group_mdd`'s per-group lists). `_accumulate_group` + `_group_means_
    from_accs` mirror `_group_means`'s exact row/order/pad contract, sourced from a `dict[value, _GroupAcc]`
    instead of a raw observation list.
  - **`_control_group_run_contribution`** — the per-run body of `_control_groups`'s cohort sampling,
    extracted (behavior-preserving refactor; `_control_groups` itself is otherwise unchanged) so
    **`_ControlGroupBuilder`** can drive the IDENTICAL logic one run at a time, sharing ONE `random.Random`
    instance across every run in the SAME ascending run-id order `_control_groups` walks — the draw
    sequence, and therefore every cohort's `mean_return`/`n`, is identical to the old full-list call (TC-6).
  - **`_AttributionAccumulator`** — bounded incremental state for `_attribution_slices`'s `per_stock`/
    `by_sector`/`by_rank_band` panels, plus the ONE disclosed bare-`float` exception: `distribution`'s
    exact median/stdev has no O(1) streaming equivalent, so its return list (never a full observation
    dict) is the one piece that still scales with N.
  - `compute_forward_aggregates`'s per-chunk loop now feeds every observation into these accumulators as
    it is read, plus a per-chunk `chunk_obs_by_run` dict (bounded to chunk-width x symbols-per-run, the
    SAME bound iter-30 already established for `_forward_agg_slice_map`) that drives
    `_ControlGroupBuilder.consume_run` before being discarded.
  - The top-level `overall.mean_return`/`overall.mean_max_drawdown` (previously two O(N) float lists built
    AFTER `stock_obs`) are now `_ExactMeanAcc` running accumulators, per the plan's explicit flag.
- **`_attribution_slices`'s frozen, test-pinned `(stock_obs, cfg)` signature is lifted ON PURPOSE** (spec-
  authorized) to `(acc: _AttributionAccumulator, cfg)`. `_AttributionAccumulator.from_observations(...)`
  reconstructs the old convenience for callers that still have (or want) a small, already-materialized
  observation list — used by `compute_run_scorecard`'s own per-run `stock_obs` and by the reference oracle.
- **`_group_means`, `_group_mdd`, and `_control_groups` themselves are UNCHANGED** (same signatures, same
  bodies apart from `_control_groups`'s internal-only behavior-preserving refactor to share
  `_control_group_run_contribution`) — used by `compute_run_scorecard`'s own already-small per-run
  `stock_obs` builder and by the byte-identity reference oracle.
- **New TC-1 test** (`test_accumulator_peak_size_does_not_scale_with_observation_count_at_fixed_
  cardinality`) proving the bound holds at a discriminating scale — see "A methodology correction found
  mid-implementation" below for why it feeds the accumulation primitives directly rather than going
  through `compute_forward_aggregates`.
- **Extended the existing `_reference_compute_forward_aggregates` byte-identity oracle** (in
  `test_forward_testing_aggregates_streaming.py`) to wrap its own full `stock_obs` via
  `_AttributionAccumulator.from_observations(...)` before calling `_attribution_slices` — the reference
  stays the "obviously correct" full-list implementation; only its ONE call site needed updating to match
  the authorized signature lift.
- **Live full-deep-basis forward-aggregate warm** across all 5 configured `walk_forward.horizons`, run
  TWICE against independent historical dates on the real committed seed (~4.97 GB, 1,879 distinct
  run dates) — see "Live verification" below and `reports/perf-budgets.md`'s new "Iteration 32" section.

## Files Changed

- `apps/backend/app/engine/forward_testing.py` — added `_ExactMeanAcc`, `_GroupAcc`, `_accumulate_group`,
  `_group_means_from_accs`, `_control_group_run_contribution`, `_ControlGroupBuilder`,
  `_AttributionAccumulator`; rewrote `compute_forward_aggregates`'s accumulation section to build these
  incrementally inside the per-chunk loop instead of a full `stock_obs` list; lifted `_attribution_slices`'s
  signature; refactored `_control_groups`'s body to share the extracted per-run helper (signature/output
  unchanged); updated `compute_run_scorecard`'s ONE call site to `_attribution_slices` to wrap its own
  small `stock_obs` via `_AttributionAccumulator.from_observations` (its `stock_obs` BUILDER, lines
  ~2090-2105, is byte-unchanged — only this one call line needed the mechanical wrap the signature lift
  requires); extended the function's docstring.
- `apps/backend/tests/test_forward_testing.py` — updated the three `_attribution_slices` direct-call tests
  (`test_attribution_empty_observations_are_all_na`, `test_attribution_single_observation_dispersion_is_
  null`, `test_attribution_is_pure_over_passed_observations_no_new_query`) to build an
  `_AttributionAccumulator` instead of passing a raw list; the "no new query" test's structural signature
  assertion now checks `{"acc", "cfg"}`. The other six attribution-adjacent tests in this file
  (`test_attribution_consistency_with_aggregate`, `..._distribution_exact`, `..._per_stock_named_...`,
  `..._top_contributors_k_...`, `..._rank_bands_come_from_config`, `..._rank_band_with_no_members_is_
  padded`) call `compute_forward_aggregates` rather than `_attribution_slices` directly and needed NO
  changes — they passed unmodified.
- `apps/backend/tests/test_forward_testing_aggregates_streaming.py` — updated `_reference_compute_forward_
  aggregates`'s `_attribution_slices` call site to the new contract; added the new `test_accumulator_peak_
  size_does_not_scale_with_observation_count_at_fixed_cardinality` test (TC-1).
- `reports/perf-budgets.md` — new dated "Iteration 32" section recording the live full-deep-basis warm's
  peak `VmPeak` + margin under `server.memory_cap_mb` (J-07 step 3).
- `docs/handoffs/goal-ops-hardening-iter-32-dev.md` — this handoff.

## A methodology correction found mid-implementation

The plan asked for a TC-1 test "mirroring `test_shipped_factor_join_run_chunk_actually_binds_on_the_live_
basis`'s discipline" — I initially wrote one that called the REAL `compute_forward_aggregates(session,
...)` against two engines (same small ticker/sector cardinality, run count tripled to grow observation
count) and compared `tracemalloc`-measured peaks. That version FAILED even against the fixed, restructured
code (peak grew ~2.06x for a 3x observation-count increase) — investigating with `tracemalloc.take_
snapshot()` traced it to `run_rows = session.exec(select(ScannerRun).where(...)).all()`, an EXISTING,
UNCHANGED, iter-14-documented-as-"bounded, small" accumulator (one ORM object per RUN) that this iteration
was never asked to touch. Tripling run count alone (isolated, no `compute_forward_aggregates` involved)
reproduced a ~2.96x peak growth from `run_rows` by itself — nearly the entire explanation for what I'd
attributed to a bug. Since raising observation count in this schema structurally requires raising run
count (one ScannerResult+ForwardReturn row per `(run, ticker)`), a whole-function `tracemalloc` measurement
cannot isolate THIS iteration's accumulators from that pre-existing, accepted, run-count-proportional
overhead. I rewrote the test to feed synthetic observations directly into the real accumulation primitives
(`_GroupAcc`/`_accumulate_group`/`_AttributionAccumulator`, imported from the module, not reimplemented),
bypassing the DB/ORM path entirely — this isolates exactly what TC-1 asks about. I calibrated the
threshold (5x observation count, `peak_large < peak_small * 4.0`) against a dev-pass measurement of the
OLD full-`stock_obs`-list design under the identical delta (observed ratio ~5.6x, essentially
proportional) vs the new design's observed range (~2.0-2.8x across several (n_small, n_large) pairs at
this delta) — the disclosed `distribution` bare-float list does still grow linearly, so the ratio is not
1.0x, only PROPORTIONAL-to-old growth would be a regression. The live full-deep-basis warm (TC-4/TC-5,
below) is the end-to-end proof that the real function does not crash at the actual ~800K-observation live
scale; this unit test is the isolated, mechanism-level proof of the actual bound.

## Tests Run

Command (host-guard `taskset -c 0-3,8-11` + `NUMEXPR_NUM_THREADS=4` per
`project-extensions/host-guard/host-guard.env`):

```
cd apps/backend && NUMEXPR_NUM_THREADS=4 taskset -c 0-3,8-11 .venv/bin/python -m pytest \
  tests/test_forward_testing_aggregates_streaming.py \
  tests/test_backtest_scorecard.py \
  tests/test_forward_testing.py \
  --deselect tests/test_forward_testing.py::test_backfill_inserts_forward_returns_without_mutating_snapshot \
  --deselect tests/test_forward_testing.py::test_backfill_is_idempotent \
  --deselect tests/test_forward_testing.py::test_backfill_populates_mae_mfe_within_band \
  --deselect tests/test_forward_testing.py::test_backfill_populates_max_drawdown_same_na_gate \
  --deselect tests/test_forward_testing.py::test_backfill_latest_run_has_zero_post_bars \
  --deselect tests/test_forward_testing.py::test_stored_scores_identical_with_and_without_forward_returns \
  --deselect tests/test_forward_testing.py::test_walk_forward_asof_dates_are_real_trading_days_with_full_horizon \
  -q
```

**Result: 143 passed, 7 deselected in 15.80s.** The deselected 7 depend on the session-scoped `loaded_
engine` (full 30-year seed bootstrap + historical-cadence warm-up) or module-scoped `backfilled_engine`
fixtures — neither touches `compute_forward_aggregates`'s accumulator shape (they test `backfill_forward_
returns`'s INSERT-only/idempotency behavior and `walk_forward_asof_dates`), and this project's own prior
iterations (iter-29, iter-30) established the same exclusion for the same reason (the 30-year basis makes
`loaded_engine` alone take 10+ minutes without necessarily finishing in a bounded window). Discovered this
by first running the file unmodified and having it stall for 16+ minutes at the SAME point before I traced
it to `loaded_engine`'s real-seed historical-cadence bootstrap and added it to the deselect list.

Included in the 143: all 46 tests in `test_forward_testing_aggregates_streaming.py` (the byte-identity
oracle across 5 horizons x 2 `as_of` values x 3 batch sizes, the run-chunk-width byte-identity matrix, the
run-chunk-boundary/all-excluded-chunk error cases, the shipped-config-actually-chunks tests including the
one against the REAL committed seed DB, and the new TC-1 accumulator-size test); all 20
`test_backtest_scorecard.py` tests (confirming `compute_run_scorecard`'s minimal call-site wrap didn't
change its output); 77 of 84 `test_forward_testing.py` tests including all attribution tests, all
control-group tests (`test_aggregates_control_groups`, `test_control_group_determinism_same_seed_same_
cohort`), all VCP/new-pattern-cohort tests, all `as_of`-scoping tests, and the 3 `forward_aggregates_
ingest_cached` tests.

**RED check performed before implementing:** wrote the new TC-1 test and the reference-oracle's updated
attribution call against the OLD (unmodified) code first — both failed as expected (`AttributeError:
module 'app.engine.forward_testing' has no attribute '_AttributionAccumulator'`), confirming the tests
exercise the new code path rather than passing vacuously.

**Correctness spot-check (not a pytest test, a standalone verification before trusting the design):** 200
random trials comparing `_ExactMeanAcc.add()`-in-shuffled-order against `statistics.mean()` on the same
values in original order — zero mismatches, confirming the exact-Fraction streaming mean is genuinely
bit-for-bit order-independent before relying on that property for TC-2.

**`test_no_magic_numbers.py`** — ran `tests/test_no_magic_numbers.py -q`: still fails (pre-existing,
carried per the spec's OUT OF SCOPE list), offending literals unchanged from before this iteration
(`indicators.py: 0.5, 0.95`; `forward_testing.py: 45.0, 0.5, 0.9` — none of which this iteration's diff
touches or adds; confirmed by inspection that none of my new code contains a numeric literal beyond
structural `0`/`1`).

**Not run:** the full pytest suite (project convention — the 30-year `loaded_engine`-based tests make it
~10-11h) and `test_api_backtest.py`/MCP tool tests (both heavily `loaded_engine`-dependent, and the live
full-deep-basis warm below independently exercises the SAME `GET /api/backtest` call path against the
SAME real committed seed at the real endpoint, making a second multi-minute `loaded_engine` bootstrap
redundant for this iteration's purposes).

## Live verification (TC-4/TC-5, J-07 step 3 — never done across the prior 31 iterations)

Started `scripts/start-backend.sh` (prod mode, host-guard caps applied) against the live deep-basis DB
(~4.97 GB, 1,879 distinct scanner-run dates, `dataset_version=r1879-f3971375`). Waited for boot warm-up to
fully stabilize (`VmPeak`/`VmHWM` unchanged across 30 consecutive 3s polls) before triggering the measured
compute. `GET /api/backtest?as_of=<date>` on a historical date not yet cached under the current
`dataset_version` (confirmed by a read-only query first) triggers the background dispatch that computes
all 5 configured horizons via `forward_aggregates_ingest_cached` -> `compute_forward_aggregates` — no
cache-row deletion or DB mutation needed. Ran twice against independent historical dates (`2026-07-20`,
then `2026-07-17`) on the same live process.

**TC-4:** zero `MemoryError` in `logs/backend.log` from the boot banner (line 133070) forward, checked
after both trials. `GET /api/health` polled at ~1 Hz throughout both trials: **77/77 polls returned HTTP
200** (34 during trial 1's 57.81s compute, 43 during trial 2's 58.91s compute). Both trials' `evidence_
status` read `"ready"` with a fresh `evidence_generated_at` after completion — the warm genuinely computed
and persisted.

**TC-5:** `VmPeak` (`/proc/<pid>/status`) was flat at **2,691,600 kB across the ENTIRE measurement window**
— pre-trigger stabilized baseline, both 5-horizon live warms, and post-completion, all identical (107
total samples). Against `server.memory_cap_mb` = 6144 MB (6,291,456 kB): **margin = 3,599,856 kB ≈
3,515.5 MB (57.2% headroom)**. Full table and methodology in `reports/perf-budgets.md`'s new "Iteration
32" section.

Restart hygiene: stopped the backend (found and killed both this run's PID and one stray leftover PID from
an earlier session on the same port), confirmed the port free, restarted cleanly (HTTP 200 within 2 poll
attempts, no port conflict), then stopped again before finishing — `ps aux`/`lsof` confirmed no `uvicorn`
process remained on port 8255.

## Known Issues

- **The RNG-order-preservation constraint on `_control_groups` (TC-6) did NOT prove materially harder than
  expected** — flagging this explicitly since the spec's NOTES anticipated it might. The design hint in
  the plan (chunk boundaries never split a run, so a run's complete observation set is always available at
  once) held exactly as described; sharing one `random.Random` instance across `_ControlGroupBuilder.
  consume_run` calls in ascending run-id order reproduced the byte-identical cohort output on the first
  attempt, confirmed by the full byte-identity oracle (46/46 tests passing, including `control_group` as
  one of the compared top-level keys across all run-chunk widths).
- **`compute_run_scorecard`'s call site to `_attribution_slices` (one line) changed**, even though its
  `stock_obs` BUILDER did not. TC-7 as literally worded ("that function's source lines... byte-unchanged")
  could be read as covering the whole function; I read it as covering the BUILDER specifically (the
  parenthetical in the plan calls the builder out by line number, `forward_testing.py:1832`, and the
  restructuring this iteration ships makes updating every caller of the lifted-on-purpose signature
  unavoidable — there is no way to call `_attribution_slices` with its NEW contract using OLD syntax).
  Flagging this reading explicitly rather than silently asserting full compliance; the reviewer/auditor
  should judge whether the one-line, purely-mechanical wrap (`_AttributionAccumulator.from_observations
  (stock_obs, ...)`) satisfies the spirit of "not reopened."
- Everything the spec explicitly carries as out-of-scope and unchanged this iteration remains unchanged and
  untouched: `warmup.py:194`, `prices.py:141`, the Factor-Lab-all constant-factor residual, `merge_ui_test_
  results.py`'s `_ROW_RE` bug, `test_no_magic_numbers.py`'s pre-existing red state, UT-04's fixture, the
  four `test_forward_testing_serving_split.py` monkeypatches, audit B2, `GET /api/health`'s 0.127787s
  reading, and the `J-01/J-03/J-04-verify.png` capture-tooling issue.
- No frontend work this iteration (spec: "New user-facing capability: None"); `/backtest`'s served payload
  is byte-identical before and after, confirmed by the 46-test byte-identity oracle plus the live warm's
  `evidence_by_horizon` re-read.

## Pre-handoff verification

- **Service startup:** `scripts/start-backend.sh` started cleanly against the real seed DB (used for the
  live TC-4/TC-5 measurement above), stopped (full process-group kill, verified via `lsof`), and restarted
  cleanly with no port conflict — see "Live verification" above for the full sequence. No frontend changes
  this iteration, so `scripts/start-frontend.sh` was not exercised.
- **External integrations:** N/A this iteration (no new adapter/scraper/external API call; AG-9
  offline-deterministic ingest unaffected — the live warm reads only the already-committed local seed DB).
- **Native dependency binaries:** N/A this iteration (no new dependency).
