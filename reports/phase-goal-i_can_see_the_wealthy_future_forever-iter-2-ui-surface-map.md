# Phase goal-i_can_see_the_wealthy_future_forever-iter-2 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-2
**Date:** 2026-06-01
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/system-health` | `ReturnAttributionSection` (`components/return-attribution.tsx`) | New component | J-19 adds aggregate return attribution below the control-group panel | Scroll to "Return attribution"; confirm four panels render below "Control-group comparison" and that the "Distribution & hit-rate" Mean equals the page's "Mean stock fwd return" header value |
| `/system-health` | `PerStockPanel` — "Top contributors & detractors" | New component | Surface which tickers drove/dragged the cohort | Confirm two columns (Contributors / Detractors) each list tickers with a sector label, a colored mean return, and `(n=…)`; confirm an empty side shows the "No ticker had a measurable forward return" copy |
| `/system-health` | `DistributionPanel` — "Distribution & hit-rate" | New component | Surface distribution shape, not just the mean | Confirm rows Mean, Median, "% positive (hit rate)", "Dispersion (σ)", Sample size; confirm hit rate and σ are neutral (no green/red, no +/-) while Mean/Median are color-graded |
| `/system-health` | `GroupPanel` — "Forward return by sector" | New component | Surface per-sector forward return | Confirm one row per stored sector with mean return + `n`; confirm "—" empty-label copy when no sector has data |
| `/system-health` | `GroupPanel` — "Forward return by rank band" | New component | Surface per-config-band forward return | Confirm every rank band (e.g. 1–10 / 11–50 / 51+) is listed even when empty, with empty bands showing an em-dash NA |
| `/system-health` | `HorizonSelector` (existing) → attribution | Changed behavior | Section rides the existing horizon selector | Click a different horizon (e.g. 5d); confirm the attribution panels' values update along with the rest of the page |
| `/backtest` | `BacktestAttributionSection` + `ReturnAttributionSection` | New component | J-19 adds per-date return attribution below the scorecard | Load `/backtest`, scroll below "Forward-test scorecard"; confirm the "Return attribution" section renders four panels for the current as-of date |
| `/backtest` | `HorizonViewSelector` ("Horizon" segmented buttons) | New component | Pick which already-fetched horizon's attribution to view | Click 1d / 5d / 10d / 20d / 60d; confirm only the attribution panels change, the active button shows `aria-pressed`, and the "Viewing as-of" badge and scorecard above do NOT change |
| `/backtest` | `HorizonViewSelector` — date-state regression guard (J-18) | Changed behavior | New control must not reintroduce date state | Open DevTools Network; click between horizons and confirm NO new `/api/backtest` request fires (no refetch); confirm the as-of date in the URL/badge is unchanged |
| `/backtest` | Default horizon-view selection | New behavior | Default view is the first horizon with an observed window | On a historical date with elapsed windows, confirm the section opens on a horizon that has data (not an all-NA view); on a too-recent date confirm all panels honestly show NA |

---

## Backend-Only Changes (No UI Impact)

- `config.yaml` — new `walk_forward.attribution` block (`top_contributors_k`, `rank_bands`) — drives
  the list size and the rank-band labels/edges; no direct UI surface, but its band labels appear as row
  labels in the "Forward return by rank band" panel.
- `apps/backend/app/config.py` — new `RankBand` + `AttributionCfg` typed config and validation — no UI
  surface; validation errors would surface only as a backend boot failure.
- `apps/backend/app/engine/forward_testing.py` — `_attribution_slices` and helpers derive the four
  slices from already-built per-observation data and attach them to the existing System Health and
  Backtest scorecard payloads — no new endpoint; consumed indirectly by the UI section above.
- `apps/frontend/lib/api.ts` — added `PerStockRow`, `PerStockAttribution`, `BySectorRow`,
  `ByRankBandRow`, `Distribution`, `ReturnAttribution` types and `attribution` fields on the two
  response types — type-only, no fetcher signature changed.
- Backend test files (`test_forward_testing.py`, `test_backtest_scorecard.py`,
  `test_api_system_health.py`, `test_api_backtest.py`, `test_config_engine.py`, `test_config.py`,
  `test_sectors.py`, `test_themes.py`) — added/updated tests — no UI surface.

---

## Summary

- **Frontend surfaces changed:** 2 routes (`/system-health`, `/backtest`)
- **New pages/routes:** 0
- **Modified components:** 3 frontend files (1 new shared component + 2 pages); the new section renders 4 panels per page
- **Navigation changes:** no
- **Backend-only changes:** 5 production/config files + 8 test files
