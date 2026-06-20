# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39
**Date:** 2026-06-20
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` (Dashboard) | Cross-view chart — bottom pane (phase bands, severity line, P(bear) line) | Changed behavior | Backend cache-key fix makes `timeline_full` series available at the live current as-of, where it was missing before | Navigate to `/`, scroll below the top pane of the cross-view chart; confirm the bottom pane shows colored phase bands, a 0–100 severity line, and a filtered P(bear) line (not a blank/empty canvas) at the current date |
| `/` (Dashboard) | Cross-view chart — synced zoom between top and bottom pane | Changed behavior | With the bottom pane now populated, zoom in using the range selector on either pane; both panes must move together and produce two visually distinct frames (different time windows) | Click-drag a zoom region on the top pane; verify the bottom pane zooms to the same time window simultaneously; then zoom to a different region and confirm the resulting screenshot differs from the first |
| `/` (Dashboard) | Compact at-a-glance "Market Phase & Severity" figure (iter-38 restructure) | Changed behavior | The at-a-glance panel calls the same `?full=true` endpoint as the cross-view chart; the previously-cached miss means it was receiving a payload without `timeline_full`, causing the bottom-pane figure to be empty | Navigate to `/` at the current date; confirm the compact Market Phase & Severity figure shows a severity number and a phase label, and that clicking its disclosure expands named component breakdown rows (not a blank expansion) |
| `/` (Dashboard) | Cross-view chart bottom pane — early/historical as-of | Changed behavior | At a very early as-of date (before market-phase history), the bottom pane must show an honestly-empty canvas, not a fabricated or error state | Use the as-of selector to set a date in 2010 or earlier; scroll to the cross-view chart bottom pane; confirm it is visually empty (no colored bands, no lines) rather than showing an error or stale data |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/market_phase.py` — added `SCHEMA_VERSION = "s1"` constant and `_cache_version()` helper; folded the schema token into the `MarketPhaseCache` key for both `market_phase_cached` and `retrospective_cached`. Only the cache key string changed; no new endpoint, no changed response payload, no new DB column. The effect is visible indirectly (correct data now served to the existing frontend chart) but there is no new UI surface.
- `apps/backend/tests/test_market_phase.py` — new and updated unit tests for cache-HIT correctness. No UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 1 (Dashboard `/`)
- **New pages/routes:** 0
- **Modified components:** 0 (no frontend code was edited; the existing `phase-cross-view-chart.tsx` and `phase-cross-view-card.tsx` components are unchanged; behavior changed because the backend now sends the data they were already wired to consume)
- **Navigation changes:** no
- **Backend-only changes:** 2 (`market_phase.py` cache-key logic, `test_market_phase.py` tests)
