# goal-i_can_see_the_wealthy_future_forever-iter-17 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-17
**Date:** 2026-06-04
**Agent:** developer
**Status:** complete

## What Was Built

**Backend — as-of-scope the forward-test evidence aggregate + relocate it onto Backtest; retire System Health**

- **`compute_forward_aggregates(..., *, as_of: Optional[date] = None)`** (`app/engine/forward_testing.py`).
  When `as_of` is given, a SINGLE membership filter joins each forward return to its run and restricts the
  pool to snapshots with `ScannerRun.asof_date <= as_of` (an expanding walk-forward window). It bounds
  everything derived from `fr_rows` (`runs_with_fr`, `results`, `run_rows`, the SPY/QQQ benchmark lists);
  the grouping / excess / control-group / attribution math is untouched. `as_of=None` adds no clause →
  byte-identical to today's all-history result (== the latest-date case). The cutoff reads
  `ScannerRun.asof_date` (the canonical snapshot date), not the denormalized `ForwardReturn.asof_date`.
- **`GET /api/backtest` now returns `evidence_by_horizon`** (`app/api/backtest.py`): for each configured
  horizon, `compute_forward_aggregates(session, h, cfg, as_of=run.asof_date)` using the already-resolved
  run's date — all horizons in the one payload so the client-side horizon selector needs no refetch. The
  per-date scorecard is unchanged and still served alongside it.
- **System Health retired**: deleted `app/api/system_health.py` and unregistered its router/import in
  `main.py`. `compute_forward_aggregates` is kept (now the Backtest evidence source). Provenance docs in
  `forward_testing.py` / `backtest.py` / `research.py` updated off the dead endpoint.
- **No scoring/scanner/regime/pattern/snapshot change, no DB regen, no new config key.** The six canonical
  scores, buckets, setups, and the Risk-Off→Actionable gate stay byte-identical (J-06/J-07 unaffected).

**Frontend — Backtest evidence sections; remove System Health page/nav/client** (details in the frontend handoff)

- New `components/evidence-panels.tsx` (`EvidenceAggregateSection` + the panels extracted from the deleted
  System Health page). Rendered at the very bottom of `/backtest` from `evidence_by_horizon[selectedHorizon]`
  — re-points on the global as-of switcher and on the existing horizon selector (no refetch). J-21 order
  preserved (exactly one "Return attribution" section; leadership lists stay below it).
- `lib/api.ts`: `SystemHealthResponse`→`EvidenceAggregate`, added `evidence_by_horizon` to `BacktestResponse`,
  removed `fetchSystemHealth`. Sidebar lost the System Health entry + `Activity` import. SH page deleted.

## Files Changed

**Backend**
- `apps/backend/app/engine/forward_testing.py` — add `as_of` kwarg + the single membership filter to
  `compute_forward_aggregates`; module/function docstrings updated. (Only logic change.)
- `apps/backend/app/api/backtest.py` — add `evidence_by_horizon` (per config horizon, `as_of=run.asof_date`);
  docstring updated.
- `apps/backend/app/api/system_health.py` — **deleted**.
- `apps/backend/main.py` — removed the `system_health` import + `include_router`.
- `apps/backend/app/api/research.py` — provenance docstring no longer names the retired endpoint.
- `apps/backend/tests/test_forward_testing.py` — +6 as-of scoping tests (incl. the relocated consistency
  invariant on the as-of-scoped aggregate — moved, not deleted).
- `apps/backend/tests/test_api_backtest.py` — +4 API tests (evidence shape/keys, expanding-window scoping,
  default==all-history, system-health 404); updated the exact-top-level-keys test to include `evidence_by_horizon`.
- `apps/backend/tests/test_api_system_health.py` — **deleted** (re-homed onto the Backtest tests).
- `config.yaml` — corrected one stale `default_horizon` comment that named the retired endpoint (no value changed).

**Frontend**
- `apps/frontend/components/evidence-panels.tsx` — **new** shared evidence panels + `EvidenceAggregateSection`.
- `apps/frontend/app/backtest/page.tsx` — render the evidence section at the bottom of `BacktestResults`.
- `apps/frontend/lib/api.ts` — `EvidenceAggregate` type + `BacktestResponse.evidence_by_horizon`; removed `fetchSystemHealth`.
- `apps/frontend/components/sidebar.tsx` — removed the System Health NAV entry + unused `Activity` import.
- `apps/frontend/app/system-health/page.tsx` — **deleted**.

**Markers (verified, decomposer-authored — not re-written)**
- `runs/goal-session-.../state/blueprint.md` (IA + Data Contract) and `state/blueprint.reapproval-requested`
  already describe this exact relocation; confirmed consistent with the shipped code.

## Tests Run

- **Backend** — `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
  Result: **454 passed, 4 skipped, 0 failed** (1119.95s ≈ 18m39s), run **once**. The 4 skips are
  pre-existing and unrelated to this iteration: `test_stooq_real_fetch_single_symbol_or_skip` (network
  integration, skipped offline) and 3 `test_universe_screen` tests (gated on the Yahoo-429 data-walled
  J-22 market-cap record).
  Iter-17 tests, all PASSED: `test_aggregates_as_of_*` (6), `test_backtest_evidence_by_horizon_shape_and_keys`,
  `test_backtest_evidence_is_as_of_scoped_expanding_window`, `test_backtest_evidence_default_equals_full_all_history_aggregate`,
  `test_system_health_route_is_retired_404`, `test_backtest_does_not_reserve_regime_or_stock_values` (updated).
- **Frontend** — `cd apps/frontend && npm run build`
  Result: **✓ Compiled successfully**, type-check clean, 13 routes generated (was 14 — `/system-health`
  gone), `/backtest` 9.54 kB. The production `.next` was removed afterward so browser QA starts `next dev`
  on a clean cache (iter-15 lesson).
- **Backend import smoke** — `python -c "import main"` clean; route table shows `/api/backtest` present and
  `/api/system-health` absent.

## Known Issues

- **No live external integration in scope.** This iteration touches only the read path over the committed
  seed (no scraper/adapter/API call added), so no live integration test applies. The data-walled
  J-22/J-23/J-24 remain honestly NA and non-halting per the re-scoped goal — not re-probed (per spec).
- **Per-request computation, no new cache table** (by scope): `/api/backtest` now calls
  `compute_forward_aggregates` five times (one per horizon, filtered to ≤ D). For the committed seed this
  is well within the warm-load budget; the full suite (which boots the walk-forward) is unchanged in
  character. Per-request memoization was explicitly optional and not added.
- **Browser QA prerequisite**: start `next dev` on a clean `.next` (stop by port 3835, `rm -rf
  apps/frontend/.next`, restart, confirm `/_next/static/chunks/main-app.js → 200`) before driving the UI —
  the standing iter-15 dead-shell lesson. The evidence section exposes `data-testid="evidence-aggregate"`
  and `data-testid="evidence-summary"` to anchor the J-09 before/after-as-of assertions.

## Suggested Next Phase

Per the spec sequencing and the `blueprint.reapproval-requested` pause: after the operator confirms the
System Health retirement, **iter-18 → J-26** (composite percentile-rank-blend cohort, replacing the strict
AND-intersection at `research.py:479` so the Combined cohort is non-empty and scales to all factors), then
**iter-19 → J-32** (Research all-history ⟷ as-of toggle, reusing this iteration's `asof_date ≤ D` scoping
seam on the `research.py` lab functions as a MODE, not a second date control). Once those land and nothing
regresses, GOAL_ACHIEVED is reachable with J-22/J-23/J-24 recorded as honestly blocked (NA), non-halting.
