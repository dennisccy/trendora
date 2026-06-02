# goal-i_can_see_the_wealthy_future_forever-iter-6 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-6
**Date:** 2026-06-02
**Agent:** developer
**Status:** complete

## What Was Built (UI)

### J-20 — Stock-Detail chart through latest (display-only)
- The price chart on `/stocks/[ticker]` now requests the **full path through the latest seed date** (`fetchStockBars(ticker, asOf, signal, "latest")`). At a historical as-of D the chart shows the post-D region; at the latest as-of there is no forward region and the chart is visually unchanged.
- `PriceChart` (`components/price-chart.tsx`) splits the series at the as-of boundary using the per-bar `is_forward` flag:
  - **Forward candles** (date > D) are drawn in a muted palette token (`--text-faint`) so they read as "after the as-of date"; their **volume bars** are muted further (`--border-strong`).
  - An **as-of divider marker** (arrow + "as-of {D}" label, `--warn` token) is placed at the last ≤ D bar via lightweight-charts v5 `createSeriesMarkers`.
  - The **legend** gains a "Forward — after as-of {D} (display only)" swatch when a forward region exists.
- A one-line caption above the chart states the forward bars are display-only and do NOT affect the scores/setup/VCP below (which still read the ≤ D snapshot via `fetchStock`, unchanged).
- All colours are CSS palette tokens read at runtime — no ad-hoc hex.

### J-21 — Backtest reorg + horizon-linked return columns
- New section order on `/backtest`: **As-of scan summary (regime + candidate counts) → Forward-test scorecard → Return Attribution → Top Sectors, Top Themes, Ranked Cohort**. The three leadership lists moved BELOW Return Attribution (previously above the scorecard).
- Each of the three lists gained a **realized forward-return column** at the selected horizon, rendered with the existing `<Return>` component (honest "—"/NA when a horizon lacks post-bars; the existing low-sample ⚠ when `n < min_sample`). Returns are joined from `by_horizon[viewHorizon].leadership_returns` onto the rows already fetched from `/api/sectors` (by sector-ETF ticker), `/api/themes` (by slug), `/api/stocks` (by ticker) — re-formatted only, never recomputed.
- The horizon **view** selector's state (`viewHorizon`) was **lifted to page level** (`BacktestResults`). The single existing `HorizonViewSelector` (rendered in the Return Attribution header) now re-points BOTH the attribution panels AND the three return columns at once. It stays a VIEW selector — no refetch, no fetch param, no date state; the global as-of switcher remains the only date control (J-18 preserved).

## Files Changed

- `apps/frontend/lib/api.ts` — `PriceBar.is_forward?`, `BarsResponse.latest_date?`, optional `through` param on `fetchStockBars`; `LeadershipSectorReturn`/`LeadershipThemeReturn`/`LeadershipCohortReturn`/`LeadershipReturns` types + `leadership_returns` on `BacktestScorecardHorizonRow`.
- `apps/frontend/components/price-chart.tsx` — `asofDate` prop; muted forward candles/volume; as-of divider marker; forward-region legend item; `ChartLegend` extended with `hasForward`/`asofDate`.
- `apps/frontend/app/stocks/[ticker]/page.tsx` — `StockChartPanel` opts into `through=latest`, threads `asofDate` to `PriceChart`, shows a display-only caption when a forward region is present.
- `apps/frontend/app/backtest/page.tsx` — `BacktestResults` (lifts `viewHorizon`), `AsOfScanSummary` (regime + counts only), `LeadershipListsSection` (the three lists below attribution with return columns); old `ScanSummarySection` + `BacktestAttributionSection` removed/replaced.

## Visual / Design-System Notes

- Component reuse only: `PriceChart`, `Card`/`CardHeader`/`CardContent`, `ScoreBadge`, `Badge`, `<Return>`, the existing `HorizonViewSelector`, `ReturnAttributionSection`. No new component-library pieces.
- Palette tokens only — `--text-faint` / `--border-strong` (muted forward region), `--warn` (as-of marker + NA/low-sample), `--pos`/`--neg` (≤ D candles), the `<Return>` colour grading. No arbitrary hex; numbers stay monospace/tabular (`num`).
- States handled: chart loading/empty/error preserved; latest-as-of → no forward region; return columns render "—" (NA) when a horizon lacks post-bars; low-sample ⚠ preserved; per-endpoint "unavailable" messages for sectors/themes/stocks preserved.
- Responsive: the Ranked-Cohort table is horizontally scrollable (`overflow-x-auto`, `min-w-[40rem]`) for the added column at the ~640px breakpoint.

## Tests Run

- `cd apps/frontend && npm run build` → compiled + typechecked successfully; all 13 routes generated (no type errors).
- UI workflow verification (the as-of divider shot, the horizon before/after on the return columns, the latest-as-of no-forward case, the NA case) is for the browser-QA agent — driven via the global as-of switcher with in-app navigation (the as-of provider is in-memory and resets to Latest on a hard reload).

## Known Issues

- None specific to the frontend. The chart's forward MA lines extend continuously past D (display-only, as designed); the muted candles + as-of marker + legend label make the forward region unmistakable.
