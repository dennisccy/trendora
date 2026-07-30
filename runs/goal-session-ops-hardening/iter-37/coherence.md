# Iteration 37 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-37
**Date:** 2026-07-30
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Summary

This iteration is a backend-only internal-mechanism fix (confirmed by
`reports/phase-goal-ops-hardening-iter-37-ui-surface-map.md`: zero `apps/frontend/` files touched,
no route/component/API-contract change). The only code files touched are
`apps/backend/app/engine/data_manager.py` (`git diff a120163717ae... -- apps/backend/app/engine/data_manager.py`)
and a new test file, `apps/backend/tests/test_backfill_coverage_shared_cache.py` (both read in full).
Everything else in the diff/status (`runs/*`, `reports/*`, `docs/handoffs/*`, `docs/phases/*.md`) is
harness bookkeeping / spec / measurement-ledger noise, out of review scope per the invocation prompt.

The change: `_do_backfill` (`data_manager.py:3096-3113`) now stashes its already-loaded whole-table
`_BarCache` onto `JobProgress._shared_bar_cache` instead of releasing it immediately on success;
`_persist_per_date_coverage_snapshots` (`data_manager.py:3230-3246`) and `_refresh_ingest_aggregates`
(`data_manager.py:3316-3539`) now `attach_shared_cache(session, shared)` that SAME pre-loaded cache
(falling back to their own `prefilled_bar_cache` when no shared cache was stashed — i.e. when
`_do_backfill` had zero in-range targets or was never the caller) instead of each opening a second
independent whole-table `daily_prices` prefill for the same job. `attach_shared_cache` and
`prefilled_bar_cache` are pre-existing primitives in `apps/backend/app/engine/prices.py` (added in the
earlier `i_can_see_the_wealthy_future_forever_with_my_loved_ones` session, commit `78da69ae`, for the
K-date parallel-worker case) — this iteration wires two more call sites in the SAME module to reuse
them; it introduces no new cache primitive, no new module, and no new function that recomputes a
Data Contract value.

Every warm call inside `_refresh_ingest_aggregates`'s newly-indented `with cache_ctx:` block —
`refresh_coverage_snapshot`, `_persist_per_date_coverage_snapshots`, `market_phase.market_phase_cached`,
`forward_testing.forward_aggregates_ingest_cached`, `event_study_cached`,
`indexes.index_series_cached_with_status`, `forward_testing.compute_drawdown_expectations_cached` — is
otherwise byte-unchanged (diff confirms these are pure reindentation, no logic edits). The new test file
adds a `git show HEAD`-pinned reference-oracle test (TC-7, byte-identity) and a mutation test (TC-8)
proving the shared-cache wiring actually reads bar values from the shared cache rather than silently
falling back to an independent reload, plus a leak-safety test (audit B1: the cache is released even if
the finalize hook never runs, so a `JobProgress` retained forever in `_JOBS` cannot pin ~1.13 GB). This
matches the blueprint's iter-37 update paragraph and the iter spec's "Data-contract additions: None" /
"Blueprint conformance: No new page/nav" claims exactly.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Coverage payload (universe counts, per-symbol coverage, gaps, capacity) | OK | `apps/backend/app/engine/data_manager.py:3230-3246` — `_persist_per_date_coverage_snapshots` still calls the SAME `refresh_coverage_snapshot_for`/`_compute_coverage_uncached` derivation; only the bar-cache *acquisition* mechanism (own prefill vs. attach-shared) changed. Served by the unchanged `GET /api/data` endpoint. |
| Backfill run-summary contract (`dates_total`, exclusion breakdown, `aggregates_refreshed`) | OK | `apps/backend/app/engine/data_manager.py:3316-3539` — the `aggregates_refreshed` category list (`coverage`, `membership_timeline`, `market_phase`, `forward_aggregates`, `research_hot_keys`, `index_series`, `drawdown_expectations`) and every append condition are unchanged; only wrapped in an outer `with cache_ctx:` / `finally`-release. |
| Membership timeline / research hot-key caches (incl. `index_series`, `drawdown_expectations`) | OK | Same file/lines as above — each producer call (`market_phase_cached`, `forward_aggregates_ingest_cached`, `event_study_cached`, `index_series_cached_with_status`, `compute_drawdown_expectations_cached`) is byte-identical; no second producer introduced. |
| Bar-series cache sharing mechanism (`_BarCache`/`attach_shared_cache`) | OK — not a Data Contract value | Pre-existing primitive in `apps/backend/app/engine/prices.py:414` (added commit `78da69ae`, unrelated prior session); this iteration only adds two new call sites in `data_manager.py`, no new implementation. |

No new displayed value is introduced (backend-only iteration, confirmed by the UI surface map — zero
`apps/frontend/` changes). No duplicate computation, no non-canonical source, no unregistered value.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route/feature this iteration) | OK | `reports/phase-goal-ops-hardening-iter-37-ui-surface-map.md` confirms zero `apps/frontend/` files touched; `docs/phases/goal-ops-hardening-iter-37.md`'s "Blueprint conformance" and "UI surface changes: None" sections concur. No sidebar/nav file needed inspection since no route changed. |

J-07 retains its existing cross-cutting home (global readiness badge + `/backtest`) and `/data` retains
its existing Coverage payload / Backfill run-summary contract home, both already registered in
`runs/goal-session-ops-hardening/state/blueprint.md`'s Information Architecture table — neither changed
this iteration.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `runs/goal-session-ops-hardening/journey-scripts/J-07.json` (harness test-plan file, not product code)
  updates its step-2/step-3 expected-text assertions (`"Snapshots contributing (≤ 2026-07-15): 1873"` →
  `"n=8878"` on `/backtest`, plus a new step 3 checking `"3508"` on `/data`) to match the live basis's
  current counts. This is journey-script maintenance tracking a growing dev DB, not a Data Contract
  change — noted for completeness only, no action needed.
- No coherence debt is being carried forward by this iteration.
