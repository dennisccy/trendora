# Iteration 37 — Coherence Audit

**Iteration:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37
**Date:** 2026-06-19
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

This iteration modifies three files:

- `apps/backend/app/engine/prices.py` — `_BarCache.prefill`, `_BarCache.trailing_count`, `prefilled_bar_cache`
- `apps/backend/app/engine/data_manager.py` — `_membership_timeline`, `_do_backfill`
- `apps/backend/tests/test_bar_cache.py` — new regression guard + shim update

The Data Contract registers `membership_timeline` and `coverage + per-date coverage diagnostic` under the single canonical module `data_manager:compute_coverage` -> `GET /api/data`. Both are untouched in their computation and serving:

- No new computation function or module for any registered value.
- No new endpoint serving any registered value.
- No client-side recomputation introduced.
- The change is exclusively HOW the trailing-bar count is sourced inside the prefilled cache (empty series recorded up front for no-bar candidate-pool symbols) — the served value is byte-identical (0 trailing bars from cache = 0 trailing bars from a per-date re-load).
- No new displayed value is introduced; no unregistered value appears in the diff.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `membership_timeline` (J-96) | OK | `apps/backend/app/engine/data_manager.py:515` passes `pool_symbols` to `prefilled_bar_cache` — same module, same endpoint, served values byte-identical; no second computation path |
| Coverage + per-date diagnostic (J-94) | OK | `apps/backend/app/engine/data_manager.py:484-515` — `pool_count` derivation unchanged; `pool_symbols` extracted as a named variable for reuse only; `compute_coverage` unchanged |
| Bar-load-once invariant (J-46) | OK | `apps/backend/app/engine/prices.py:89-96` records no-bar candidates as empty series in `prefill`; `prices.py:126-145` `trailing_count` memoizes the no-bar result — restores the invariant, does not introduce a second computation of any served value |

## Information Architecture check

The UI surface map (`reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37-ui-surface-map.md`) confirms: 0 new pages, 0 new routes, 0 navigation changes. All changed files are backend-internal engine code and tests. No new feature requires a navigation path check.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| No new route or feature introduced | OK | UI surface map: "Frontend surfaces changed: 0; New pages/routes: 0; Navigation changes: no" |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None. This is a pure backend correctness and performance fix. All served values are byte-identical before and after the change. No formatting drift, no label inconsistency, and no unregistered value.
