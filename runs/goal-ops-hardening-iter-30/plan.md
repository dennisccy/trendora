# goal-ops-hardening-iter-30 Execution Plan

## Alignment check
Directly advances `docs/goal.md` J-07 ("heavy aggregates never take the service down", AG-8) and closes
the last mechanical gap on J-06 (perf budgets / replay). Backend-only, no new journey, no new UI, no
proven-language — consistent with the goal's "Loop mechanics" (J-01…J-06 carry no Evidence Claims) and
this session's established compute-at-ingest / bounded-memory discipline (iter-14's AG-8 recovery, iter-29's
sibling fix in `research.py`). No drift from goal.md detected; the spec's own scope matches the session's
Ground-truth/offenders list (`compute_forward_aggregates` is offender-cluster item, J-07's named producer).

## What to Build

1. **Bound `compute_forward_aggregates`'s three unbounded in-RAM containers**
   (`apps/backend/app/engine/forward_testing.py:857-995`): `ret_by_run_symbol`, `mdd_by_run_symbol` (dicts)
   and `stock_obs` (list) today accumulate one entry per `(run_id, symbol)`/`(run_id, ticker)` across the
   FULL horizon-partition of `forward_returns`/`scanner_results` at once (measured ~770K-803K entries/horizon
   on the live basis at iter-29's audit — this function reads the SAME `forward_returns WHERE horizon==h`
   population research.py's now-fixed `_factor_observations` reads, so the same order-of-magnitude applies
   here, unconfirmed until the developer re-measures against THIS function's own accumulators).
   - Chunk the `runs_with_fr` walk into RUN-count slices (mirrors iter-29's audit-fixed `_fr_slice_map`
     pattern in `research.py`) so peak added memory is bounded by chunk-width × symbols-per-run, not by the
     full horizon-partition.
   - Restructure `_group_means`, `_control_groups`, `_attribution_slices`, and the VCP/pullback/breakout
     groupings (all in `forward_testing.py`) to consume bounded/incremental per-chunk accumulation and
     produce the SAME grouped output — not to change their public shape.
   - **Known hard constraint to flag for the developer, not to solve here:** `_attribution_slices`'s
     `distribution` cell calls `_distribution(returns)`, which needs an exact `median` and exact sample
     `stdev` (`statistics` module) over the FULL flat return list for the horizon — these are not reducible
     to a per-chunk running sum the way `mean`/`n` are. A byte-identity-safe design either (a) retains one
     lean flat list of floats (not the full `stock_obs` list of ~10-key dicts — an order-of-magnitude memory
     win on its own) purely for this one cell, or (b) an exact two-pass/online algorithm. Silently swapping
     in an approximate or reordered computation would violate TC-2's byte-identity requirement.
   - `_control_groups`'s random same-sector cohort draws from a SINGLE seeded `random.Random` in a
     run-then-sorted-sector iteration order — the RNG object must persist ACROSS chunks (not be re-seeded
     per chunk) and chunks must be walked in ascending `run_id` order, or the draw sequence (and therefore
     the byte-identical output) breaks.
2. **New dedicated config knob** — its own key, RUN-count unit, added to `WalkForwardCfg`
   (`apps/backend/app/config.py:729-777`, mirrors iter-29's audit-added `ResearchCfg.factor_join_run_chunk`
   pattern) with a boot validator (`>= 1`) and a `config.yaml` entry carrying the live measurement in a
   comment. MUST NOT reuse `research.read_batch_size` (a ROWS knob, already the `yield_per` batch here) or
   `research.factor_join_run_chunk` (a different function's own dedicated knob) — iter-29's binding lesson
   on unit/ownership mismatch is the exact failure mode this spec calls out by name.
3. **Byte-identity fixture test**: pinned pre-chunk reference implementation vs. the chunked
   implementation, all 5 configured horizons, with and without `as_of`, deep-equal on every returned slice
   (`by_bucket`, `by_setup`, `by_regime`, `by_sector`, `by_rank_band`, `control_group`, `attribution`,
   VCP/pullback/breakout, `excess`).
4. **Shipped-config-actually-chunks test**: against the REAL `load_config()` value and the LIVE DB's actual
   distinct-run count for a representative horizon (never a fixture-sized width) — proves >1 chunk, mirrors
   iter-29's audit-added `test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis`.
5. **Error-case tests**: a chunk boundary that splits one run's observations across two chunks must not
   double-count or drop that run's contribution to any grouped mean; an empty chunk (zero qualifying
   observations) must not crash the merge.
6. **J-06 mechanical closure** (no code change): append a new dated section to `reports/perf-budgets.md`
   with this iteration's fresh 11-page on-load-latency sweep (developer's own curl-based pass, per this
   session's established pattern — see `reports/perf-budgets.md`'s prior "developer pass" entries) plus the
   ≤5s boot-to-health measurement, every reading scored PASS/WARN against its committed budget. The
   established convention in this codebase is that the developer's curl-based entry is NOT a substitute for
   browser-qa-agent's own real-Chrome TTI confirmation pass — both are expected; only the developer's half
   is this plan's scope.

## Explicitly out of scope (carried from the phase spec — do not touch)
- `warmup.py:194` boot-warm-up `MemoryError` / stuck-initializing badge (ties J-04) — deferred.
- `prices.py:141` whole-table `daily_prices` prefill in the coverage refresh (ties J-05) — deferred.
- `research.py`'s `_all_factor_observations_by_horizon` (Factor-Lab `?all=true`, the iter-29-audit "B2" gap)
  — a separate, already-identified redesign; this iteration only regression-spot-checks
  `/research/factor-lab` still works (TC-5), it does not fix that function.
- `resolved_forward_aggregate_evidence`, `ensure_historical_forward_aggregates_dispatched`, J-08's serving
  split, the session-live demo JSON, the owner's BCW budget amendment — byte-frozen per
  `iteration-state.md` "Do not redo".
- No new proven-language, Evidence Claim, or referee-touching change.

## Agents Required
- developer: yes -- implements the accumulator-bounding fix in `forward_testing.py`, the new config knob,
  the byte-identity/shipped-chunk/error-case tests, and appends the developer-side `reports/perf-budgets.md`
  measurement pass. Backend-only.
- backend-data: yes (same work as above — this pipeline's `developer` agent covers both backend and
  frontend; there is no separate backend-data role)
- frontend-ux: no -- zero UI/frontend files touched this iteration

## Frontend Present: no

(No new/changed UI surface. Browser-based verification still occurs this iteration — J-06's real-browser
sweep and J-07's `/research/factor-lab` regression spot-check (TC-5) — but that is measurement/QA of
*existing* UI against a backend-only fix, not new frontend work, and goal-mode's own target-journey override
runs the browser lane regardless of this line per `detect_frontend_in_plan`'s documented iter-8 lesson.)

## Files to Create/Modify
- `apps/backend/app/engine/forward_testing.py` -- bound the three accumulators in
  `compute_forward_aggregates`; restructure `_group_means`/`_control_groups`/`_attribution_slices` (and the
  VCP/pullback/breakout groupings) to consume bounded/chunked accumulation; docstrings extended per this
  module's established convention.
- `apps/backend/app/config.py` -- new dedicated RUN-count field on `WalkForwardCfg` + boot validator.
- `config.yaml` -- new `walk_forward.<new-key>` value with the live measurement recorded in a comment.
- `apps/backend/tests/test_forward_testing.py` (or a new sibling file mirroring
  `apps/backend/tests/test_research_streaming.py`'s pattern, e.g. `test_forward_testing_streaming.py`) --
  byte-identity fixture test (5 horizons × with/without `as_of`), shipped-config-actually-chunks test
  against the live run count, chunk-boundary and empty-chunk error-case tests.
- `reports/perf-budgets.md` -- new dated section, developer's curl-based 11-page sweep + boot-to-health
  reading, PASS/WARN scored, `git diff` non-empty for this iteration.
- `docs/handoffs/goal-ops-hardening-iter-30-dev.md` -- dev handoff (required DoD item).

## Key Test Scenarios
(Mapped to the phase spec's Test-first contract; TC numbers refer to `docs/phases/goal-ops-hardening-iter-30.md`)

- **TC-2 (developer, unit):** byte-identical deep-equal payload, pre-chunk vs. post-chunk, all 5 horizons,
  with/without `as_of`, every returned slice — the primary correctness gate for this iteration.
- **TC-3 (developer, unit):** the shipped `load_config()` chunk-width value produces >1 chunk against the
  LIVE DB's actual distinct-run count for a representative horizon (not a fixture-sized width).
- **Error cases (developer, unit):** a run split across a chunk boundary contributes exactly once to every
  grouped mean it belongs to; an empty chunk does not crash the merge step.
- **TC-1 / TC-4 (QA/browser-qa-agent, live):** the ingest-time forward-aggregate warm (all 5 horizons, full
  deep basis, one long-lived process) completes with zero `MemoryError` carrying a
  `compute_forward_aggregates`/`stock_obs`/`ret_by_run_symbol` frame in `logs/backend.log`, while
  `GET /api/health` polled at 1 Hz answers 200 throughout within its committed budget. Per the spec's own
  NOTES: do not artificially induce memory pressure to test this — measure the real warm; if the bound does
  not fully eliminate the failure, record the actual measured figures honestly rather than claim success.
- **TC-5 (QA/browser-qa-agent, live):** `/research/factor-lab` opened in a real browser on a verifiably idle
  host renders its decile table + rank-IC figures with real numeric values, HTTP 200, zero console errors —
  a regression spot-check only (this iteration does not fix that page's own separate `?all=true` crash
  path, per Out of Scope above; TC-5 is checking the accumulator-bounding *pattern* doesn't regress it
  further, not that it is fully fixed).
- **TC-6 (developer + browser-qa-agent):** `reports/perf-budgets.md` git-diff non-empty this iteration, all
  readings PASS/WARN scored.
- **TC-7 / TC-8 (QA, deterministic replay):** `J-06.json` replay PASS/zero-FAIL; required-still-passing set
  (J-01, J-03, J-04, J-05, J-08, J-09) replay PASS/zero-FAIL/zero reconciliation overturns.
- **TC-9 (QA process requirement):** any "zero MemoryError" claim in a QA report must cite the exact
  `logs/backend.log` line number of the boot banner it counted from.

## Host/process constraints (binding on every agent this iteration)
- Never run the full test suite or two concurrent pytest processes (host-guard capped hardware; prior
  iterations' hard-reset history). Use targeted test files/selectors, taskset/BLAS-capped per
  `project-extensions/host-guard/host-guard.env`, exactly like iter-29's dev/audit commands.
- Never remove, weaken, or bypass a HOST-GUARD marked block in a launch script (AG-10, critical).
- Any live backfill/ingest trigger needed to observe TC-1 should prefer the session's already-consumed
  historical dates list (2011-03-10, 2015-09-09, 2018-02-15, 2018-03-15, 2022-04-12, 2026-05-02..29) over
  consuming a new one, per the spec's NOTES.
- Do not re-open byte-frozen functions listed in "Explicitly out of scope" above.
