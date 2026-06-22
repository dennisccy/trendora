# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44
**Date:** 2026-06-22
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `MajorIndexesCard` (in `page.tsx`) | Removed element | J-101a: the cross-view card pane 0 already renders the same index/regime series; duplicate removed | Navigate to `/`; confirm no "Major indexes & regime" card appears anywhere on the page — only one market chart (the cross-view) is visible |
| `/` | `PhaseCrossViewCard` (in `page.tsx`) | Updated layout | J-101a: now the sole market chart on the Dashboard after the duplicate is removed | Navigate to `/`; confirm the two-pane cross-view card is present and both panes render (regime bands in top pane, phase bands in bottom pane) |
| `/` — cross-view bottom pane | `phase-cross-view-chart.tsx` — plotted line | Changed behavior | J-102: P(bear) line replaced by zero-centered severity-velocity line | On the cross-view chart, hover over a date well into stored history (not the warm-up head); confirm the bottom pane shows a line that crosses zero and has a dashed zero baseline, and that no "Filtered P(bear)" line is visible |
| `/` — cross-view chart legend | `phase-cross-view-chart.tsx` — legend swatch | Changed behavior | J-102: legend swatch relabeled from "Filtered P(bear)" to "Severity velocity (0-centered; + = worsening)" | Inspect the chart legend; confirm the swatch reads "Severity velocity (0-centered; + = worsening)" and no swatch labeled "Filtered P(bear)" is present |
| `/` — cross-view hover tooltip | `CrossTooltipBox` in `phase-cross-view-chart.tsx` | Added new rows | J-102: regime label + score and severity-velocity value added to the hover tooltip | Hover over a date in the middle of the stored history; confirm the tooltip shows a regime label row (e.g. "Bull / 72"), a severity-velocity row (e.g. "+0.44" or "-1.20"), AND still shows date, index %, phase, severity, and P(bear) rows |
| `/` — cross-view hover tooltip at warm-up head | `CrossTooltipBox` in `phase-cross-view-chart.tsx` | Changed behavior | J-102: earliest dates have no valid slope yet; severity-velocity must show "NA" | Hover over one of the first 4–5 dates in the phase pane; confirm the severity-velocity tooltip row shows "NA" rather than a numeric value |
| `/` — cross-view bottom pane at a historical as-of | `phase-cross-view-chart.tsx` — phase band rendering | Changed behavior | J-101b: phase bands now span full stored history regardless of selected as-of | Use the as-of date selector to pick a historical date (e.g. 2022-10-07); confirm the bottom pane's colored phase bands extend both before AND after the vertical as-of marker across the full stored history, not just up to the marker |
| `/` — cross-view bottom pane at an early as-of | `phase-cross-view-chart.tsx` — phase band rendering (empty state) | Changed behavior | J-101b: an as-of with no phase history must show an honest-empty pane, not a fabricated band | Use the as-of date selector to pick a date before stored history begins; confirm the bottom pane renders empty (no fabricated phase coloring) |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/config.py` — added `severity_velocity_window` (default 5, validated >= 2) to `MarketPhaseCfg`; consumed only through the engine and served via the existing `GET /api/market-phase` endpoint — no direct UI surface beyond what the frontend already consumes.
- `apps/backend/app/engine/market_phase.py` `SCHEMA_VERSION` bump `s1` → `s2` — internal cache key change that forces old cached rows to recompute; no user-visible behavior other than ensuring the new `severity_velocity` field is present in the served data.
- `config/config.yaml` — added `market_phase.severity_velocity_window: 5`; operational config only.
- `apps/backend/tests/` (five test files) — inline test config dicts updated to include the new required key; test-only changes with no UI surface.
- `apps/frontend/lib/api.ts` — added `severity_velocity: number | null` to the `MarketPhaseTimelinePoint` TypeScript type; a type annotation change that enables the frontend chart and tooltip to consume the new backend field; no direct UI element of its own.

---

## Summary

- **Frontend surfaces changed:** 4 (Dashboard page layout, cross-view chart line, cross-view chart tooltip, cross-view chart legend)
- **New pages/routes:** 0
- **Modified components:** 3 (`page.tsx`, `phase-cross-view-chart.tsx`, `phase-cross-view-card.tsx`)
- **Navigation changes:** no
- **Backend-only changes:** 5 (config class, engine/cache, config.yaml, tests x4, api.ts type)
