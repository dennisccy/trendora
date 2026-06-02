# Phase goal-i_can_see_the_wealthy_future_forever-iter-6 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-6
**Date:** 2026-06-02
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/stocks/[ticker]` | `PriceChart` (candles + volume) | Changed behavior | J-20: chart now requests `through=latest`, drawing post-as-of bars | At a **historical** as-of (use the global as-of switcher to pick a past date, e.g. 2025-04-04), open a ticker (e.g. NVDA) and confirm the chart shows muted/greyed candles to the right of the as-of boundary, while the ≤ as-of candles render in normal up/down colours |
| `/stocks/[ticker]` | `PriceChart` as-of divider marker | New element | J-20: boundary marker shows where the as-of date ends | Confirm an arrow marker labelled "as-of {date}" sits at the last ≤ as-of candle; switch the global as-of to **Latest** and confirm the marker and forward region disappear (chart unchanged) |
| `/stocks/[ticker]` | `ChartLegend` "Forward — after as-of" swatch | New element | J-20: legend explains the muted region | At a historical as-of, confirm the legend shows "Forward — after as-of {date} (display only)"; at the latest as-of, confirm that legend entry is absent |
| `/stocks/[ticker]` | Display-only caption above chart | New element | J-20: clarifies forward bars don't affect scores | At a historical as-of, confirm a one-line caption appears stating forward bars are display-only and don't affect the scores/setup/VCP; confirm the score/setup/VCP panels' values are identical to what they show with no forward region |
| `/backtest` | `BacktestResults` / section ordering | Updated layout | J-21: lists relocated below attribution | Load `/backtest` and confirm top-to-bottom order: As-of scan summary → Forward-test scorecard → Return Attribution → Top Sectors → Top Themes → Ranked Cohort |
| `/backtest` | `AsOfScanSummary` | New component (split out) | J-21: regime + candidate counts isolated at top | Confirm the top summary shows the regime label and candidate counts only (no leadership lists) |
| `/backtest` | `LeadershipListsSection` → Top Sectors | New table column | J-21: realized return per sector ETF at horizon | Confirm each sector row shows a realized-return value; pick a sector (e.g. XLK) and verify it matches the sector ETF's own forward return at the selected horizon |
| `/backtest` | `LeadershipListsSection` → Top Themes | New table column | J-21: equal-weight member-mean return at horizon | Confirm each theme row shows a return; for a theme with members (e.g. semiconductors), verify the value is the mean over members that have a return and that the sample count (n) is shown |
| `/backtest` | `LeadershipListsSection` → Ranked Cohort | New table column | J-21: per-ticker realized return at horizon | Confirm every cohort row resolves a return value (or "—"/NA); on a narrow viewport (~640px) confirm the table scrolls horizontally to reveal the new column |
| `/backtest` | `HorizonViewSelector` (in Return Attribution header) | Changed behavior | J-21: one selector now drives attribution + all 3 return columns | Change the horizon in the selector and confirm BOTH the Return Attribution panels AND the return columns on all three lists update simultaneously, with no page reload and no as-of date change |
| `/backtest` | Return column NA / low-sample states | New element | J-21: honest "—"/NA and ⚠ when data is thin | Select a horizon with no post-as-of data and confirm rows show "—"/NA; confirm rows with n below the minimum sample show the low-sample ⚠ marker |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/prices.py` — `bars_through_latest` accessor — feeds only the chart endpoint; not a directly user-visible surface on its own (its effect is visible via the chart row above).
- `apps/backend/app/engine/forward_testing.py` — `_leadership_returns` helper — read-only projection wired into the scorecard; its output is visible via the Backtest return columns above.
- `apps/backend/app/api/stocks.py` — `through` query param on `GET /api/stocks/{ticker}/bars` — consumed only by the chart; default (no `through`) response is byte-identical to before.
- `apps/backend/tests/test_prices_asof.py`, `test_bars.py`, `test_backtest_scorecard.py` — test files only, no UI impact.

---

## Summary

- **Frontend surfaces changed:** 2 routes (`/stocks/[ticker]`, `/backtest`)
- **New pages/routes:** 0
- **Modified components:** `PriceChart`, `ChartLegend`, `StockChartPanel`; `BacktestResults`, `AsOfScanSummary`, `LeadershipListsSection`, `HorizonViewSelector`
- **Navigation changes:** no (no sidebar/nav/route additions; blueprint nav-skeleton unchanged)
- **Backend-only changes:** 3 source files + 3 test files (all additive; default contracts preserved)
