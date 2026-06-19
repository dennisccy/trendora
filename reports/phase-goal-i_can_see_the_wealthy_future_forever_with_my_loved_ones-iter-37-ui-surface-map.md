# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37
**Date:** 2026-06-19
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

No UI surfaces were changed in this iteration. `Frontend Present: yes` was set exclusively to force the browser-QA live-verify step on `/data` (the iter-36 auto-skip lesson) — not because any frontend code changed.

The table below is intentionally empty; no row can be written without a corresponding frontend-direct or full-stack code change.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| — | — | — | — | — |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/prices.py` — `_BarCache.prefill` now records an empty series for every expected candidate-pool symbol that has no rows in `daily_prices`, so zero-bar symbols resolve to trailing count 0 from the shared cache on the first (and only) load; `trailing_count` hardened to memoize the no-bar result. Default per-request path untouched. No API contract change, no served-value change.
- `apps/backend/app/engine/data_manager.py` — `_do_backfill` and `_membership_timeline` now pass the committed candidate-pool symbol set to `prefilled_bar_cache`. No resolver math, scoring formula, or coverage computation changed. No API response schema change.
- `apps/backend/tests/test_bar_cache.py` — Added fast unit test `test_prefill_expected_symbols_records_zero_bar_symbol_once`; updated `_counting_prefill` shim for the new optional kwarg. `test_kdate_backfill_loads_each_symbol_at_most_once` assertion (`max(load_counts.values()) == 1`) is unchanged. No UI impact.

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 3 files (`prices.py`, `data_manager.py`, `test_bar_cache.py`)

**Classification rationale:** All three changed files are backend-internal engine and test code. No API endpoint schema, response shape, or served value changed. The `/data` page hydration improvement is an indirect reliability effect of restoring the load-once cache invariant — it is not caused by any frontend code change and produces no change in what the user sees.
