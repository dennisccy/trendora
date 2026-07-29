# goal-ops-hardening-iter-32 Execution Plan

## What to Build

- Restructure `compute_forward_aggregates` (`apps/backend/app/engine/forward_testing.py`) so it stops
  materializing `stock_obs`: a full list of one ~9-field dict per observation (~771K-800K entries per
  horizon on the live basis) across the WHOLE horizon-partition. This is the last unbounded accumulator in
  the function's own family (iter-29 fixed `research.py`'s sibling; iter-30 bounded this function's OWN
  join dicts `ret_by_run_symbol`/`mdd_by_run_symbol` but explicitly left `stock_obs` unbounded; iter-31
  bounded Factor-Lab-all's `pools[h]`).
- Drive every per-group/per-run/per-ticker consumer from state built INCREMENTALLY inside the EXISTING
  per-chunk loop (`walk_forward.forward_agg_run_chunk`-sized run-id slices, already in place from iter-30),
  bounded by the number of distinct groups/runs/tickers, not by total observation count:
  - `_group_means`'s six callers: `by_bucket`, `by_setup`, `by_regime`, `by_vcp`,
    `by_pullback_to_rising_dma`, `by_flat_base_breakout`
  - `_group_mdd` (paired mean-max-drawdown per group)
  - `_control_groups`'s per-run cohort sampling (`top_ranked` / `random_same_sector` / `spy` / `qqq` /
    `sector_etf`)
  - `_attribution_slices`'s `per_stock` (contributors/detractors) and `by_sector` / `by_rank_band` slices
- **Design hint worth handing to the developer (not a mandate — verify before relying on it):** chunk
  boundaries are by run id and a run's observations already never split across chunks
  (`test_forward_agg_run_chunk_boundary_never_splits_a_run` proves this today). That means each chunk sees
  one or more runs' COMPLETE observation sets at once, so `_control_groups`'s per-run RNG sampling (which
  needs a whole run's observations to determine `top_sectors`/sector pools before it draws) can likely be
  driven chunk-by-chunk in the same ascending run-id order used today, preserving the deterministic RNG
  draw order (AG-5, TC-6) without a second RNG state.
- **One disclosed exception, per spec:** `_attribution_slices`'s `distribution` slice (exact
  `median`/`dispersion`) may keep ONE list sized to N, but of bare `float` return values only — never the
  ~9-field dict. No O(1) exact streaming median exists.
- **Watch this one too — not explicitly named in the spec's bullet list, but the same crash-dimension
  applies:** `compute_forward_aggregates`'s top-level `overall.mean_return` / `overall.mean_max_drawdown`
  are currently derived from `stock_returns = [o["return"] for o in stock_obs]` and a similar
  `overall_mdds` list — both O(N) float lists built AFTER `stock_obs` is fully assembled. Unlike
  `distribution`, a plain mean does not need the full multiset — flag to the developer that a running
  sum/count accumulator (updated per chunk) is preferable to leaving a second untracked O(N) list, even
  though a bare-float list is smaller than the ~9-field dicts it replaces.
- Lift `_attribution_slices`'s frozen, test-pinned `(stock_obs, cfg)` signature ON PURPOSE (explicitly
  authorized by the spec). Update all nine existing direct-call unit tests in
  `apps/backend/tests/test_forward_testing.py` (currently lines ~1094-1236:
  `test_attribution_consistency_with_aggregate`, `test_attribution_distribution_exact`,
  `test_attribution_per_stock_named_contributors_and_detractors`,
  `test_attribution_top_contributors_k_controls_list_length`, `test_attribution_rank_bands_come_from_config`,
  `test_attribution_rank_band_with_no_members_is_padded`, `test_attribution_empty_observations_are_all_na`,
  `test_attribution_single_observation_dispersion_is_null`,
  `test_attribution_is_pure_over_passed_observations_no_new_query`) to the new contract — none deleted,
  none weakened, every documented behavior preserved (empty-observations all-NA, single-observation null
  dispersion, config-derived rank-band padding, config-derived sector order).
- Keep byte-unchanged: `compute_forward_aggregates`'s three call sites (`GET /api/backtest`, MCP
  `query_backtest`, ingest finalize warm `_refresh_ingest_aggregates`) and `compute_run_scorecard`'s own
  separate, already-small per-run `stock_obs` builder (`forward_testing.py:1832`, its own call into
  `_control_groups`/`_attribution_slices`) — a different accumulator inside the same producer, not reopened.
- Extend `apps/backend/tests/test_forward_testing_aggregates_streaming.py`'s existing
  `_reference_compute_forward_aggregates` byte-identity oracle (already reused across iter-14's row-stream
  and iter-30's run-chunk-width dimensions) to also cover this restructuring — every top-level key
  (`by_bucket`, `by_setup`, `by_regime`, `by_vcp`, `by_pullback_to_rising_dma`, `by_flat_base_breakout`,
  `control_group`, `attribution`, `overall`, `excess`) byte-identical between the real and reference
  implementations for the same fixture inputs.
- Add a dedicated live-scale accumulator-size test mirroring
  `test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis`'s discipline: at a FIXED small
  group/run/ticker cardinality, doubling observation count must not proportionally grow the peak size
  attributable to the by-group/per-stock accumulation paths — a test that fails if reverted to the current
  full-list design.
- Run a live full-deep-basis forward-aggregate warm across all 5 configured `walk_forward.horizons` in one
  long-lived backend process (mirrors iter-14/iter-30's measurement protocol, and iter-31's `VmPeak`
  table format): confirm `grep -c MemoryError` on `logs/backend.log` from this run's own boot-banner line
  forward is 0; poll `GET /api/health` at >=1 Hz throughout, every poll HTTP 200 within its existing
  budget; record peak `VmPeak` (sampled from `/proc/<pid>/status`) + margin under the 6144 MB
  `server.memory_cap_mb` cap in a new dated section of `reports/perf-budgets.md`.
- Confirm `_control_groups`'s deterministic RNG cohort sampling is unchanged for the same
  seed/config/fixture inputs (TC-6) and that `compute_run_scorecard`'s own separate per-run `stock_obs`
  builder stays byte-unchanged by diff (TC-7).
- Write dev handoff at `docs/handoffs/goal-ops-hardening-iter-32-dev.md` (mirror iter-30/31's rigor: files
  changed, tests run with exact commands/counts, live verification numbers, honest disclosure of any
  constraint — e.g. RNG-preservation difficulty — that proved harder than expected, per the spec's own
  NOTES permission to say so plainly rather than silently reverting `_control_groups`).

## Agents Required
- backend-data: yes -- all work is backend engine restructuring (`forward_testing.py`), backend unit/
  integration tests, a live-process memory measurement, and a `reports/perf-budgets.md` update. No API
  contract, schema, or endpoint changes.
- frontend-ux: no -- zero UI/page/component changes; `GET /api/backtest`'s served payload is byte-identical
  before and after.

Frontend Present: no

## Files to Create/Modify
- `apps/backend/app/engine/forward_testing.py` -- restructure `compute_forward_aggregates`'s per-observation
  accumulation into incremental per-chunk group/run/ticker accumulators; adjust `_group_means`, `_group_mdd`,
  `_control_groups`, `_attribution_slices` signatures/bodies as needed to consume the new incremental state
  (frozen `_attribution_slices` signature lifted on purpose); `compute_run_scorecard`'s own per-run
  `stock_obs` (line ~1832) stays byte-unchanged.
- `apps/backend/tests/test_forward_testing.py` -- update the nine `_attribution_slices` direct-call tests
  (~lines 1094-1236) to the new contract; add/extend RNG-reproducibility coverage for `_control_groups`
  (TC-6) if not already exercised by the byte-identity oracle.
- `apps/backend/tests/test_forward_testing_aggregates_streaming.py` -- extend
  `_reference_compute_forward_aggregates` byte-identity coverage for this restructuring (TC-2); add the new
  live-scale accumulator-size test (TC-1); add/extend error-case tests (zero-observation group still emits
  `n=0`/`mean=None` under `pad=True`; an `as_of` cutoff excluding all runs returns the same all-NA/empty
  shape as today's `stock_obs=[]` case).
- `reports/perf-budgets.md` -- new dated "Iteration 32" section recording the live full-deep-basis warm's
  peak `VmPeak` + margin under `server.memory_cap_mb` (J-07 step 3).
- `docs/handoffs/goal-ops-hardening-iter-32-dev.md` -- new dev handoff (create).
- Do NOT add a new config knob unless the restructuring genuinely requires one beyond the existing
  `walk_forward.forward_agg_run_chunk` (iter-30) -- reuse it as the incremental loop's chunk boundary rather
  than introducing a second, overlapping chunk-width setting (iter-29's binding unit/ownership lesson).

## Frontend Present
no

## UI Evolution
N/A -- no frontend work this iteration (see spec: "New user-facing capability: None"; "Product surface
delta: None visible to the user").

## Visual Requirements
N/A -- no frontend work this iteration.

## Key Test Scenarios

Restating the spec's test-first contract (TC-1..TC-9) as the acceptance bar:

- TC-1: fixed small group/run/ticker cardinality, doubled observation count -> peak size attributable to
  the by-group/per-stock accumulation paths does not grow proportionally (only the disclosed bare-`float`
  `distribution` list may still scale with N).
- TC-2: real (restructured) `compute_forward_aggregates` byte-identical to
  `_reference_compute_forward_aggregates` across every top-level key, same fixture inputs.
- TC-3: all nine `_attribution_slices` direct-call tests updated to the lifted contract, none deleted, none
  weakened, same documented behaviors.
- TC-4: live full-deep-basis warm across all 5 horizons in one process -> zero `MemoryError` in
  `logs/backend.log` from this run's boot banner forward; `GET /api/health` HTTP 200 at every 1 Hz poll
  throughout.
- TC-5: peak `VmPeak` + margin under `server.memory_cap_mb` (6144 MB) recorded in a new dated
  `reports/perf-budgets.md` section.
- TC-6: `_control_groups`'s `top_ranked`/`random_same_sector`/`spy`/`qqq`/`sector_etf` cohort
  `mean_return`/`n` identical to pre-change output for the same seed/config/fixture inputs.
- TC-7: `compute_run_scorecard`'s own separate per-run `stock_obs` builder (`forward_testing.py:1832`) --
  source lines and existing tests byte-unchanged (confirmed by diff).
- TC-8: evaluator re-derives (not inherits) all four carried AG-8 findings (iter-29/b `warmup.py:194`,
  iter-29/c `stock_obs` -- this iteration's target, iter-29/d `prices.py:141`, iter-31/e Factor-Lab-all
  constant-factor residual); only iter-29/c may flip to `resolved: true`, and only if TC-4 + TC-1 both hold.
- TC-9: required-still-passing journeys (J-01, J-03, J-04, J-05, J-08, J-09) replay green via their
  deterministic golden replay scripts, zero FAIL rows, zero reconciliation overturns.

Error cases (explicit in spec's Testing Requirements):
- A chunk whose slice produces zero observations for a group still emits that group at `n=0`/`mean=None`
  under the existing `pad=True` contract (unchanged NA discipline).
- An `as_of` cutoff excluding all runs returns the SAME all-NA/empty shape as today's `stock_obs=[]` case
  (`test_attribution_empty_observations_are_all_na`'s exact behavior, now reached via the new path).

Note on J-07's evaluation channel: the spec's Testing Requirements list "Browser: J-07 (four acceptance
steps...)" even though `Frontend Present: no` -- this matches iter-30/31 precedent, where the four steps
(full warm, 1 Hz health poll, VmPeak margin, memory-pressure isolation carve-out) were verified via a live
long-running process + `curl`/log-grep, not real-Chrome UI interaction (there is no new page or click path
to test; `/backtest`'s served payload is unchanged). QA should run these as live-process/API-level checks,
not skip them because no Chrome MCP pass is required.

## Out of Scope (flagged per spec, do not implement this iteration)
- J-06's `scripts/start-frontend.sh` dev-vs-prod launcher decision + its real-browser TTI sweep (separate
  risky/cross-cutting decision, next iteration's scope per rule 5).
- `warmup.py:194` boot warm-up whole-table prefill and `prices.py:141` ingest coverage-refresh prefill
  (both carried, unchanged, iter-29/b and iter-29/d).
- The Factor-Lab-all `pools[h]` 2.63x constant-factor residual (iter-31/e).
- J-07 step 4 (synthetic memory-pressure test-hook + honest-abort assertion) -- candidate for a future lean
  iteration, not required to close this one.
- The stray unprefixed `GET /research/factor-lab?all=true` 404 -- no reproducible call site found this
  session; not re-planned without a fresh, reproducible browser-QA capture.
- `merge_ui_test_results.py`'s `_ROW_RE` framework bug -- outside product code; escalate to the human/
  framework maintainer per the spec's NOTES (two consecutive evaluators have called it a pre-achievement
  blocker), not a developer task this iteration.
- `test_no_magic_numbers.py` red on `indicators.py`/`forward_testing.py`; UT-04's fixture; the four
  `test_forward_testing_serving_split.py` monkeypatches; audit B2 -- all carried, unchanged.
- `GET /api/health`'s 0.127787s vs its <=0.1s-at-rest budget -- owner-decision item, non-blocking, unchanged.
- `J-01/J-03/J-04-verify.png` byte-identity recurrence -- capture-tooling issue, not product scope.

No drift from `docs/goal.md` detected: this iteration is a pure hardening step toward the Vision's
"never recomputed on the fly" / no-crash operational-solidity criteria (AG-8), introduces no new claim,
score, or UI surface, and does not touch AG-1/AG-2/AG-4 territory. Builds directly on iter-29/30/31's
established chunking pattern in the same function family without duplicating it.
