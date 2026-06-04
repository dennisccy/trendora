# Phase goal-i_can_see_the_wealthy_future_forever-iter-17 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-17
**Date:** 2026-06-04
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/backtest` | `EvidenceAggregateSection` (`components/evidence-panels.tsx`, `data-testid="evidence-aggregate"`) | New component | J-09/J-10/J-16/J-28 evidence relocated here from retired System Health, now as-of-scoped | Scroll to the bottom of `/backtest`; confirm a section headed "Forward-tested evidence (expanding window ≤ <date>)" appears below the leadership lists |
| `/backtest` | Evidence summary line (`data-testid="evidence-summary"`) | New component | Shows snapshots contributing, as-of range, mean forward return + `n` — proves the window is expanding | Read the "Snapshots contributing (≤ <date>)" count and "Mean stock fwd return (Nd) (n=…)"; move the global as-of switcher to an earlier date and confirm the count and `n` both DECREASE in a distinct screenshot |
| `/backtest` | `BucketPanel` ("Forward return by score bucket") | New table | J-09 headline — forward return by A–E bucket, as-of-scoped | Confirm rows A–E each show a mean forward return and `n`; confirm a low-sample cell shows the ⚠ flag and an empty bucket shows "—" not 0 |
| `/backtest` | `ExcessPanel` ("Excess vs benchmarks") | New table | Excess vs SPY and vs QQQ for the as-of window | Confirm two rows "Excess vs SPY (SPY)" and "Excess vs QQQ (QQQ)", each showing Stocks / Benchmark / Excess columns with numeric values and `n` |
| `/backtest` | `BreakdownPanel` ("Forward return by setup type") | New table | By-setup breakdown relocated + as-of-scoped | Confirm setup-type rows each show a return and `n`; if none, confirm the empty label text rather than a blank table |
| `/backtest` | `BreakdownPanel` ("Forward return by market regime") | New table | By-regime breakdown relocated + as-of-scoped | Confirm regime rows (e.g. Risk-On / Risk-Off) each show a return and `n` |
| `/backtest` | `BreakdownPanel` ("Forward return: VCP vs non-VCP") | New table | J-16 VCP breakdown now homes on Backtest | Confirm a "VCP" and a "non-VCP" row each with a return and `n` |
| `/backtest` | `BreakdownPanel` ("Pullback-to-rising-DMA vs not") | New table | J-28 pattern breakdown now homes on Backtest | Confirm the pullback-to-rising-DMA cohort rows render with returns and `n` |
| `/backtest` | `BreakdownPanel` ("Flat-base breakout vs not") | New table | J-28 pattern breakdown now homes on Backtest | Confirm the flat-base-breakout cohort rows render with returns and `n` |
| `/backtest` | `ControlGroupPanel` ("Control-group comparison — selection vs sector beta") | New table | J-10 control group rides the same aggregate | Confirm rows for top-ranked cohort, random same-sector, and SPY/QQQ/sector ETF, each numeric and labelled; confirm the top-ranked row is visually highlighted |
| `/backtest` | Existing Backtest horizon selector | Changed behavior | Now also drives the evidence aggregate (selects a different key in the already-fetched payload, no refetch) | Change the horizon selector; confirm ALL evidence panels' numbers update and that NO new network request to `/api/backtest` fires (check Network tab) |
| `/backtest` | Page URL / date controls | Changed behavior (invariant guard) | J-18: evidence cutoff is the single global as-of, not a new control | Confirm there is NO page-local date dropdown anywhere in the evidence section; confirm the page URL carries no `as_of` (or date) query param; confirm only the global switcher changes the date |
| `/backtest` | `EvidenceAggregateSection` empty state | New component | Honest NA when the ≤ D window has no measurable return | Move the global as-of to the earliest available date; confirm "No forward-tested evidence for this window yet" empty state shows instead of zeros |
| Sidebar (all pages) | `Sidebar` NAV (`components/sidebar.tsx`) | Removed element | System Health retired; its nav entry removed | Confirm the left sidebar no longer contains a "System Health" link and now lists 10 items |
| `/system-health` | (entire route) | Removed element | Route, page, and client deleted; evidence consolidated onto Backtest | Navigate to `/system-health` directly and confirm a 404 (page no longer exists) |
| `/backtest` | Per-date scorecard / Return Attribution / leadership lists | Changed behavior (regression guard) | New section must not disturb existing J-14/J-19/J-21 surfaces | Confirm exactly ONE "Return attribution" heading; confirm Top Sectors / Top Themes / Ranked Cohort remain BELOW Return Attribution and ABOVE the new evidence section |

---

## Backend-Only Changes (No UI Impact)

- `app/engine/forward_testing.py` — added optional `as_of` cutoff kwarg to `compute_forward_aggregates`
  (single membership filter on `ScannerRun.asof_date <= as_of`). Pure data-path change; its output is the
  data behind the new Backtest section (no independent UI surface).
- `app/api/backtest.py` — added `evidence_by_horizon` to the `GET /api/backtest` response. Consumed by the
  evidence section above; no separate UI surface.
- `app/api/system_health.py` — **deleted** route handler (backend removal; its UI effect is the `/system-health`
  404 and sidebar removal listed above).
- `apps/backend/main.py` — unregistered the system_health router. No direct UI surface.
- `app/api/research.py` — provenance docstring only (named the retired endpoint). No behavior or UI change.
- `apps/backend/tests/*` (`test_forward_testing.py`, `test_api_backtest.py`, deleted `test_api_system_health.py`) — test-only.
- `config.yaml` — stale comment correction only; no value changed. No UI impact.
- `apps/frontend/lib/api.ts` — type rename `SystemHealthResponse` → `EvidenceAggregate`, added
  `evidence_by_horizon` to `BacktestResponse`, removed `fetchSystemHealth`. Plumbing for the surfaces above;
  no independent UI surface.

---

## Summary

- **Frontend surfaces changed:** 16 (1 new section composed of 9 panels/tables + summary line, horizon
  selector behavior, J-18 guard, empty state, sidebar removal, `/system-health` 404, regression-guard region)
- **New pages/routes:** 0 (evidence is added to an existing page; one route removed)
- **Modified components:** `backtest/page.tsx`, `sidebar.tsx`, new `evidence-panels.tsx`
- **Navigation changes:** yes — "System Health" removed from the sidebar
- **Backend-only changes:** 8
