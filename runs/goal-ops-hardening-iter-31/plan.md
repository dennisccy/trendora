# goal-ops-hardening-iter-31 Execution Plan

## Context (read, not built here)

This is goal-mode iteration 31 of the `ops-hardening` session (full depth). Iter-29 bounded
`_all_factor_observations_by_horizon`'s join accumulator (`fr_by_h` / `_all_fr_slice_map`) via
run-id chunking (`research.factor_join_run_chunk`), but explicitly left the function's RETURN
VALUE — `pools[h]`, one full list per configured horizon, all 5 held resident at once
(~771,129 observations × 5 horizons on the live basis) — unbounded "by design." Iter-30 fixed
the analogous accumulator in a *different* function (`forward_testing.compute_forward_
aggregates`) but the evaluator/auditor named the Factor-Lab `pools[h]` return-value gap "deferred
twice" and made it this iteration's mandatory target. The auditor's B5 finding separately proved a
concurrent duplicate `compute_factor_lab_all` invocation raced and both wrote the same cache row —
`factor_lab_all_cached` has no single-flight guard, unlike its sibling caches. This iteration closes
both, together, because they are causally linked (a duplicate concurrent compute doubles the exact
peak this iteration is trying to bound).

Two existing idioms MUST be reused, not reinvented:
- **Single-flight lock+event**: `data_manager.compute_coverage`'s `_COVERAGE_LOCK` /
  `_COVERAGE_INFLIGHT: dict[key, threading.Event]` pattern (`app/engine/data_manager.py` ~633-777)
  — owner computes outside the lock, waiters `event.wait()`, `finally` always pops+sets.
- **Bounded-wait failure path**: `forward_testing.forward_aggregates_ingest_cached`'s
  `_FORWARD_AGG_WAIT_TIMEOUT_S = 45.0` convention (`app/engine/forward_testing.py` ~1112-1284) — a
  waiter whose bounded wait elapses (owner raised or genuinely wedged) falls through to an
  independent compute, never a hang. Proven by
  `test_forward_aggregates_ingest_cached_waiter_does_not_deadlock_when_owner_raises`
  (`tests/test_forward_testing_concurrency.py:468`).

## What to Build

- **Bound `_all_factor_observations_by_horizon`'s RETURN VALUE** (`apps/backend/app/engine/
  research.py`, currently lines ~502-589), not merely its join accumulator (already bounded at
  iter-29). Peak resident memory of the structure returned to `compute_factor_lab_all` must no
  longer scale with holding all 5 configured horizons' full observation pools simultaneously.
  Constraints that rule out the easy answers:
  - The existing "ONE shared read serves every factor at every horizon" property MUST be
    preserved (`test_all_factors_fires_one_shared_pool_read_not_n`) — do NOT fix this by
    re-reading `ScannerResult`/`ForwardReturn` once per horizon.
  - Output must stay byte-identical for every `(factor, horizon, decile)` tuple, for BOTH callers:
    `GET /research/factor-lab?all=true` (`app/api/research.py:126`) and the MCP tool
    (`app/mcp/tools.py:344`).
  - A genuine memory-representation redesign is required (e.g. a more compact per-observation
    encoding than 5× parallel Python dict-lists, and/or restructuring so `compute_factor_lab_all`'s
    consumption no longer requires every horizon's full pool resident at once) — not just a
    smaller constant. Leave the exact representation to implementation, but it must be proven
    against the REAL live basis (see test requirement below), and it must not reintroduce a
    per-horizon re-read.
  - `_factor_observations`, `_runs_with_fr`, `_fr_slice_map` (the single-factor path, shares
    `_runs_with_fr` with this function, evaluator-confirmed fixed at iter-29) stay BYTE-FROZEN —
    read-only reuse of `_runs_with_fr` is fine, no behavior change to those three.
- **Add a single-flight de-dup guard to `factor_lab_all_cached`'s cache-MISS path**
  (`apps/backend/app/engine/research.py`, currently lines ~2993-3047), mirroring
  `compute_coverage`'s lock+in-flight-event idiom exactly (never a new abstraction). A waiting
  caller that times out on a bounded wait (mirror the `forward_aggregates_ingest_cached` 45s
  convention — reuse that pattern, name the new constant appropriately if a literal is needed,
  no magic numbers) falls back to an independent compute, never a hang, and never raises.
- **New config knob** for the return-value pool bound, on `ResearchCfg` (`apps/backend/app/
  config.py`, near `factor_join_run_chunk` at ~line 1349) — its OWN field, never reusing
  `read_batch_size` (a ROWS knob) or `factor_join_run_chunk` (the accumulator's own run-chunk
  knob, a documented iter-29 unit-confusion lesson: reusing another knob's unit is exactly how a
  prior bound went inert). Boot-validated `>= 1` inside `ResearchCfg._validate` (~line 1369-1377).
  Document the live measured basis it must bind against in a `config.yaml` comment, per the
  `factor_join_run_chunk` precedent.
- **Tests** (`apps/backend/tests/test_factor_lab_all.py`):
  - Extend the byte-identity oracle (`test_shared_pools_chunked_equal_the_pinned_unchunked_
    reference` / `test_all_horizons_per_factor_is_byte_identical_to_compute_factor_lab` pattern)
    to prove the restructured return value is unchanged, all-history and an `as_of` window.
  - A new test proving the return-value bound against the SHIPPED `config.yaml` (real run/
    observation count, not a fixture-sized width) — mirrors `test_shared_pool_accumulator_is_
    chunk_bounded_at_the_shipped_config`'s convention, but asserts the RETURN VALUE's peak
    resident size, not the accumulator's.
  - A single-flight test: N concurrent MISS callers for the SAME identity trigger exactly ONE
    real `compute_factor_lab_all` invocation (instrumented counter — mirror the `data_manager`
    J-100 test at `tests/test_data_manager_concurrency_load.py:130`).
  - A dedicated failure-path test: the owner computation raises, a waiting caller's bounded wait
    elapses, it falls back to an independent compute — no deadlock, no unbounded wait (mirror
    `test_forward_aggregates_ingest_cached_waiter_does_not_deadlock_when_owner_raises`).
  - Re-run unmodified (regression guard, must still pass): `test_all_factors_fires_one_shared_
    pool_read_not_n`, `test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis`
    (`test_research_streaming.py`), and the rest of `test_factor_lab_all.py`'s existing suite.
- **Dev handoff must record the ACTUAL measured peak memory** (traced peak and/or `VmPeak`) of one
  full `/research/factor-lab?all=true` cold-MISS compute against the live deep basis, compared
  plainly to `server.memory_cap_mb` (6144 MB) — state the margin honestly even if thin (do not
  round a thin margin to "fixed"; this is a named iter-29/iter-30 lesson).
- **Ride-along, capture-only, non-blocking** (do not let these become the iteration's goal):
  (a) run `J-06.json` through the deterministic replay lane and confirm a discoverable PASS/FAIL
  artifact exists; (b) if time permits, the real-browser 11-page TTI sweep J-06 step 1 still needs.

## Explicitly out of scope (per phase spec, session rule 5: one risky change per iteration)

- `stock_obs` (`forward_testing.py:988`), `warmup.py:194`'s boot MemoryError, `prices.py:141`'s
  whole-table `daily_prices` coverage-refresh prefill — all three carried to future iterations.
- Warming `factor_lab_all_cached` into `research_hot_keys` at ingest time (lazy-only stays as-is).
- `_combination_observations` / `_event_study_members` (named sibling deferred risks) — not
  touched.
- `docs/goal.md`, `readiness.py`/`compute_preflight`, the `GET /api/health` ≤0.1s budget amendment
  — untouched, owner-owned (the 0.127787s WARN is a known non-blocking carry-over).
- `merge_ui_test_results.py`'s `_ROW_RE` framework bug (drops `TC-`-prefixed rows) — flagged again
  in the phase spec for owner/framework action; not developer scope this iteration.

No drift from `docs/goal.md` found: this directly serves J-06 (pages load only what they need,
without crashing) and J-07 (heavy aggregates never take the service down) under AG-8's resilience
mandate, using the compute-at-storage/bounded-read architecture already established. No UI change
is implied or should be made — the spec is explicit that the Factor Lab page's existing rendering
is unchanged; it simply stops 500ing.

## Agents Required

- developer: yes -- implement the return-value memory bound in `_all_factor_observations_by_horizon`,
  the single-flight guard in `factor_lab_all_cached`, the new config knob, and all tests listed above;
  measure live peak memory and record it in the dev handoff.

## Frontend Present

no

## Files to Create/Modify

- `apps/backend/app/engine/research.py` -- restructure `_all_factor_observations_by_horizon`'s
  return-value memory representation (bound peak resident size); add single-flight lock+event guard
  to `factor_lab_all_cached`'s MISS path with a bounded-wait fallback.
- `apps/backend/app/config.py` -- new `ResearchCfg` field (return-value pool bound), its own unit,
  boot-validated `>= 1`.
- `config.yaml` -- set the new knob with a comment recording the live measured basis it must bind
  against (mirrors the `factor_join_run_chunk` comment precedent).
- `apps/backend/tests/test_factor_lab_all.py` -- byte-identity extension for the restructured return
  value, shipped-config return-value bound test, single-flight test, failure-path test.
- `apps/backend/tests/test_research_streaming.py` -- re-run unmodified as a regression guard (only
  touch if a genuine unrelated collision forces it; flag in handoff if so).
- `docs/handoffs/goal-ops-hardening-iter-31-dev.md` -- dev handoff with measured peak memory vs
  `server.memory_cap_mb` (6144 MB) stated plainly, plus single-flight proof summary.

## Key Test Scenarios

- TC-1/TC-2: cold-MISS `GET /research/factor-lab?all=true` in a real browser on a warm live-basis
  backend returns HTTP 200 with real numeric deciles/rank-IC for every factor at every horizon,
  zero console errors, and zero `MemoryError` with a `research.py` frame counted from THIS run's
  boot-banner line number in `logs/backend.log` (line number must be cited in the QA report).
- TC-3/TC-4: two concurrent cold-MISS requests for the SAME Factor-Lab-all cache identity trigger
  exactly ONE real `compute_factor_lab_all` invocation (instrumented unit test); a simulated
  owner-raises case proves a waiting caller falls back to an independent compute rather than
  hanging.
- TC-5/TC-6: fixture-backed byte-identity of the restructured `compute_factor_lab_all` output vs
  the pre-iteration reference (all-history + an `as_of` window); a shipped-`config.yaml` unit test
  proves the new bound binds against the REAL live run/observation count, not a fixture-sized width.
- TC-7: `_factor_observations`/`_runs_with_fr`/`_fr_slice_map`'s existing tests (incl.
  `test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis`) pass UNMODIFIED.
- TC-8: required-still-passing journeys J-01, J-03, J-04, J-05, J-08, J-09 all PASS via
  deterministic replay with zero FAIL rows and zero reconciliation overturns.
- TC-9 (ride-along, non-blocking): `J-06.json` deterministic replay produces a discoverable
  PASS/FAIL artifact (path cited in the QA/audit report).
