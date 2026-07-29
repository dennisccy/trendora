# Goal Iteration 32 Functional Test Plan

**Phase:** goal-ops-hardening-iter-32
**Date:** 2026-07-29
**Frontend Present:** no

## Phase Goal

Restructure `compute_forward_aggregates` to stop materializing `stock_obs` — a full list of ~9-field dicts per observation (~771K-800K entries per horizon on the live basis) — and instead drive all per-group/per-run/per-ticker consumers from state built incrementally inside the existing per-chunk loop, bounded by the number of distinct groups/runs/tickers rather than by total observation count. This fixes the last unbounded accumulator in the function's family and removes the crash-risk at the live scale.

## Test Cases

### TC-01 — Accumulator-size scaling does not grow with observation count

**Type:** api
**Preconditions:** 
- Test fixture with fixed small number of distinct groups/runs/tickers (e.g., 5 runs, 10 tickers, 4 groups)
- Observation count doubled from baseline (e.g., 1K → 2K observations per horizon)
- `compute_forward_aggregates` ready to run for one horizon

**Steps:**
1. Record peak memory consumption for by-group/per-stock accumulation paths via `tracemalloc` at baseline observation count
2. Double the observation count in the fixture while keeping group/run/ticker cardinality constant
3. Run `compute_forward_aggregates` again for the same horizon
4. Record peak memory consumption for the same accumulation paths
5. Compare memory growth ratio (should not scale proportionally with observation count)

**Expected outcome:** 
Peak size attributable to by-group/per-stock accumulation paths remains roughly constant or grows sub-linearly (not proportional to observation count). The disclosed bare-`float` `distribution` list may still scale with N.

**Pass criteria:** 
Peak memory growth ratio < 1.5x when observation count doubles (i.e., not 2x or higher). This proves the restructuring removed the O(N) dict accumulation and was not merely compressed.

---

### TC-02 — Byte-identity with reference oracle across all top-level keys

**Type:** api
**Preconditions:**
- `test_forward_testing_aggregates_streaming.py` with `_reference_compute_forward_aggregates` already loaded
- Same fixture inputs as existing byte-identity oracle tests
- Restructured `compute_forward_aggregates` implementation in place

**Steps:**
1. Run `_reference_compute_forward_aggregates` for a fixed fixture and `(horizon, as_of)` pair
2. Run the real (restructured) `compute_forward_aggregates` for identical fixture and `(horizon, as_of)` pair
3. Compare all top-level keys: `by_bucket`, `by_setup`, `by_regime`, `by_vcp`, `by_pullback_to_rising_dma`, `by_flat_base_breakout`, `control_group`, `attribution`, `overall`, `excess`
4. Verify exact byte-identity (same serialization, not just semantic equivalence)

**Expected outcome:** 
Real and reference implementations return identical results for every top-level key in the response dict.

**Pass criteria:** 
```bash
python3 -c "assert compute_forward_aggregates(...) == _reference_compute_forward_aggregates(...); print('PASS')"
```
All 10 top-level keys match exactly.

---

### TC-03 — All nine `_attribution_slices` direct-call tests updated to new contract

**Type:** api
**Preconditions:**
- All nine existing direct-call unit tests for `_attribution_slices` identified in `test_forward_testing.py` (lines ~1094-1236):
  - `test_attribution_consistency_with_aggregate`
  - `test_attribution_distribution_exact`
  - `test_attribution_per_stock_named_contributors_and_detractors`
  - `test_attribution_top_contributors_k_controls_list_length`
  - `test_attribution_rank_bands_come_from_config`
  - `test_attribution_rank_band_with_no_members_is_padded`
  - `test_attribution_empty_observations_are_all_na`
  - `test_attribution_single_observation_dispersion_is_null`
  - `test_attribution_is_pure_over_passed_observations_no_new_query`

**Steps:**
1. Run `pytest apps/backend/tests/test_forward_testing.py::test_attribution_consistency_with_aggregate -v`
2. Run each of the remaining eight tests in sequence
3. Verify each test passes with the new `_attribution_slices` signature (lifted on purpose)
4. Confirm none of the tests have been deleted or weakened

**Expected outcome:** 
All nine tests pass. Each test still asserts its documented behavior:
- Empty observations → all-NA output
- Single observation → null dispersion
- Config-derived rank-band padding applied
- Config-derived sector order preserved
- Consistent attribution totals

**Pass criteria:** 
```bash
pytest apps/backend/tests/test_forward_testing.py -k "attribution" -v
# Expected: 9 passed, 0 failed
```

---

### TC-04 — Live full-deep-basis warm runs with zero MemoryError and healthy `GET /api/health`

**Type:** api
**Preconditions:**
- Full deep-basis data loaded (all 5 configured `walk_forward.horizons`)
- Backend started with `scripts/start-backend.sh` and host-guard caps applied
- `logs/backend.log` initialized and cleared
- Background health-check script ready to poll `GET /api/health` at ≥1 Hz

**Steps:**
1. Start backend service: `scripts/start-backend.sh`
2. Wait for boot banner to appear in `logs/backend.log`
3. Record boot-banner line number as start marker
4. Launch health-check poller: `while true; do curl -s http://localhost:8000/api/health -w "HTTP %{http_code} at $(date +%s.%N)\n" >> health.log; sleep 1; done &`
5. Trigger forward-aggregate warm: invoke `_refresh_ingest_aggregates` or run full backtest computation across all 5 horizons
6. Monitor `logs/backend.log` in real-time for any `MemoryError` lines
7. Collect health-check results
8. Confirm process completes without crash
9. Stop backend service and health poller

**Expected outcome:** 
- Process completes forward-aggregate warm successfully across all 5 horizons
- No `MemoryError` line appears in `logs/backend.log` after the boot-banner line
- Every `GET /api/health` poll returns HTTP 200 within existing budget (< 100ms at rest per anti-goal AG-10)
- Process remains responsive throughout

**Pass criteria:** 
```bash
grep -c MemoryError logs/backend.log  # Must output: 0
grep "HTTP 200" health.log | wc -l    # Must be > 0, ideally all polls
# No non-200 status codes in health-check log
```

---

### TC-05 — Peak VmPeak recorded under memory cap with margin

**Type:** artifact
**Preconditions:**
- Same live warm as TC-04 completed successfully
- Process PID captured during warm
- `reports/perf-budgets.md` exists with existing measurement sections

**Steps:**
1. During the live warm (TC-04), sample `/proc/<pid>/status` at ≥1 Hz to capture `VmPeak` line
2. Store all sampled `VmPeak` values (in kB)
3. Identify the maximum `VmPeak` across all samples
4. Calculate margin to the 6144 MB cap: `margin_mb = 6144 - (peak_vmPeak_kB / 1024)`
5. Write new dated section to `reports/perf-budgets.md` under "Iteration 32" header recording peak VmPeak and margin

**Expected outcome:** 
- Peak VmPeak recorded is < 6144 MB (the `server.memory_cap_mb` cap)
- Positive margin exists (e.g., peak 4800 MB → margin 1344 MB)
- Entry appears in `reports/perf-budgets.md` under a new "Iteration 32" section with timestamp and measurement

**Pass criteria:** 
```bash
grep -A2 "Iteration 32" reports/perf-budgets.md | grep "VmPeak"
# Must show: Peak VmPeak: XXXX MB, Margin: YYYY MB (where XXXX < 6144)
```

---

### TC-06 — Control groups RNG cohort sampling is deterministic and unchanged

**Type:** api
**Preconditions:**
- `_control_groups` function updated to use incremental path (per-chunk RNG re-seed and cohort draws)
- Test fixture with known `control_group.seed` and run/sector/pool configuration
- Pre-change reference output available or recomputable

**Steps:**
1. Call `_control_groups` with fixed fixture, `control_group.seed = 12345`, fixed run list, config
2. Capture output `top_ranked`, `random_same_sector`, `spy`, `qqq`, `sector_etf` cohorts with their `mean_return` and `n` values
3. Call `_control_groups` again with identical inputs (deterministic re-seeding should produce same draw order)
4. Verify output is byte-identical to step 2
5. Compare against pre-change reference output (if available)

**Expected outcome:** 
RNG cohort sampling produces identical output when seeded with the same value, even when driven by the incremental (per-chunk) path instead of a full materialized list. The deterministic draw order is preserved across runs.

**Pass criteria:** 
```bash
assert control_group_output_iter32 == control_group_output_reference
# All cohort mean_return and n values must match exactly
```

---

### TC-07 — `compute_run_scorecard`'s per-run `stock_obs` stays byte-unchanged

**Type:** api
**Preconditions:**
- `compute_run_scorecard` function and its per-run `stock_obs` builder (around `forward_testing.py:1832`)
- Source code diff available showing which lines changed

**Steps:**
1. Run `git diff HEAD~1 apps/backend/app/engine/forward_testing.py | grep -A5 -B5 "line 1832" | grep "stock_obs"`
2. Confirm that source lines in `compute_run_scorecard` building per-run `stock_obs` are unchanged
3. Run existing unit tests for `compute_run_scorecard`
4. Verify tests still pass (confirming behavior is unchanged)

**Expected outcome:** 
`compute_run_scorecard`'s own separate per-run `stock_obs` accumulator (different from the restructured `compute_forward_aggregates` one) remains byte-unchanged. This is a separate accumulator inside the same producer, not reopened.

**Pass criteria:** 
```bash
git diff HEAD -- apps/backend/app/engine/forward_testing.py | grep -A10 "def compute_run_scorecard"
# No changes shown in the per-run stock_obs builder section
pytest apps/backend/tests/test_forward_testing.py -k "scorecard" -v
# All scorecard tests pass
```

---

### TC-08 — AG-8 findings re-derived: only iter-29/c marked resolved if TC-1 and TC-4 hold

**Type:** api
**Preconditions:**
- Four carried AG-8 findings from previous iterations are documented:
  - iter-29/b: `warmup.py:194` boot warm-up whole-table prefill (unchanged this iteration)
  - iter-29/c: `stock_obs` unbounded accumulator (TARGET of this iteration)
  - iter-29/d: `prices.py:141` ingest coverage refresh prefill (unchanged this iteration)
  - iter-31/e: Factor-Lab-all `pools[h]` 2.63x constant-factor residual (unchanged this iteration)
- TC-1 (accumulator scaling) and TC-4 (live warm MemoryError count = 0) have passed

**Steps:**
1. If TC-1 FAILED: mark iter-29/c as unresolved, return
2. If TC-4 FAILED: mark iter-29/c as unresolved, return
3. If both TC-1 and TC-4 PASS: mark iter-29/c as `resolved: true` in the evaluator's findings log
4. For iter-29/b, iter-29/d, iter-31/e: verify they remain unchanged (no new fixes applied this iteration)
5. Mark those three as `resolved: false` in the findings log

**Expected outcome:** 
- iter-29/c (`stock_obs`) → `resolved: true` only if TC-1 AND TC-4 both pass
- iter-29/b, iter-29/d, iter-31/e → `resolved: false` (unchanged from prior evaluations)
- All four findings carry forward to the next evaluator with updated state

**Pass criteria:** 
Evaluator writes a structured findings JSON or markdown table with:
```
Finding,Iteration,Resolved,Reason
"warmup.py:194 prefill","iter-29/b","false","unchanged this iteration"
"stock_obs accumulator","iter-29/c","true","TC-1 + TC-4 both PASS"
"prices.py:141 prefill","iter-29/d","false","unchanged this iteration"
"Factor-Lab pools constant-factor","iter-31/e","false","unchanged this iteration"
```

---

### TC-09 — Required-still-passing journeys replay green

**Type:** api
**Preconditions:**
- Six required journeys (J-01, J-03, J-04, J-05, J-08, J-09) with golden deterministic replay scripts ready
- This iteration's build deployed to a clean backend

**Steps:**
1. Start backend: `scripts/start-backend.sh`
2. For each journey (J-01, J-03, J-04, J-05, J-08, J-09):
   - Run its deterministic golden replay script: `python scripts/goal/replay-j-XX.py --build-version iter-32 --strict`
   - Capture output: pass count, fail count, reconciliation overturns
3. Aggregate results across all six journeys
4. Stop backend

**Expected outcome:** 
All six journeys pass their deterministic replays with zero FAIL rows and zero reconciliation overturns. The backend correctly serves the same computed results as prior iterations.

**Pass criteria:** 
```bash
python scripts/goal/replay-journeys.py --journeys "J-01,J-03,J-04,J-05,J-08,J-09" --build-version iter-32
# Expected output:
# J-01: PASS (0 fails, 0 overturns)
# J-03: PASS (0 fails, 0 overturns)
# J-04: PASS (0 fails, 0 overturns)
# J-05: PASS (0 fails, 0 overturns)
# J-08: PASS (0 fails, 0 overturns)
# J-09: PASS (0 fails, 0 overturns)
```

---

## Summary

**Total test cases:** 9
- **API tests:** 9 (TC-01 through TC-09)
- **Browser tests:** 0 (Frontend Present: no)
- **Artifact checks:** 1 (TC-05 — VmPeak recording in perf-budgets.md)

**Depth:** These tests form the binding acceptance criteria for the phase goal. They verify:
1. The memory bound is real and removes O(N) accumulators (TC-01, TC-04)
2. Byte-identity with the reference oracle is maintained (TC-02)
3. All lifted unit tests pass the new contract (TC-03)
4. The recorded measurement proves the bound holds at live scale (TC-05)
5. Determinism and correctness are preserved (TC-06, TC-07, TC-08, TC-09)

Each test maps directly to a numbered Definition of Done criterion in the phase spec.
