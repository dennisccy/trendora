# Phase goal-i_can_see_the_wealthy_future-iter-4 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future-iter-4
**Date:** 2026-05-29
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/stocks/[ticker]` | `PriceChart` (candlesticks) | New component | J-05 adds the price candle chart | Open `/stocks/NVDA`; confirm the chart `<canvas>` paints visible green/red OHLC candles (not a blank box), and the header shows "1356 bars · as of <date>". |
| `/stocks/[ticker]` | `PriceChart` (MA overlays) | New component | J-05 adds 20/50/150/200-DMA overlays from the server `ma` series | On `/stocks/NVDA`, confirm 4 coloured MA lines are drawn over the candles and the legend lists `20-DMA`, `50-DMA`, `150-DMA`, `200-DMA`; the lines start after a warm-up gap (no line for the earliest bars). |
| `/stocks/[ticker]` | `PriceChart` (volume) | New component | J-05 adds a volume series | On `/stocks/NVDA`, confirm a volume histogram is visible pinned to the bottom of the chart pane and "Volume" appears in the legend. |
| `/stocks/[ticker]` | `StockChartPanel` card | New page section | Hosts the chart with its own load/empty/error states | Stop the backend and reload `/stocks/NVDA`; confirm the chart card shows "Chart unavailable" (amber) with the "Nothing is fabricated" note, while the rest of the page is unaffected. |
| `/stocks/[ticker]` | `ThemeAndInvalidationCard` (theme chips) | New page section | J-05 adds theme-membership chips | On `/stocks/NVDA`, confirm chips "Ai Data Centre", "Semiconductors", "Megacap Leaders" render under "Themes"; click one and confirm it navigates to `/themes`. |
| `/stocks/[ticker]` | `ThemeAndInvalidationCard` (empty themes) | New behavior | Honest empty state | Open a stock with no theme membership; confirm "Not a member of any tracked theme." renders instead of chips. |
| `/stocks/[ticker]` | `ThemeAndInvalidationCard` (invalidation note) | New page section | J-05 adds the server-computed invalidation level | On `/stocks/NVDA`, confirm the "Invalidation" note reads verbatim "Invalid below the 50-DMA at $198.73" (a concrete dollar level, in muted text). |
| `/stocks/[ticker]` | Invalidation NA state | New behavior | No-fabrication on short history | Open a short-history ticker; confirm the invalidation note reads "Invalidation level NA — insufficient history" and renders in amber (`--warn`), with no fabricated dollar value. |
| `/stocks/[ticker]` | Three `ScoreCard`s (J-06 guard) | Changed behavior (row grew) | `invalidation`+`themes` added to the shared row | On `/stocks/NVDA`, confirm Leadership / Entry Quality / Risk still each show an A–E bucket, a 0–100 value, and ≥3 named components, and that these match the same row on `/stocks` (byte-identical). |
| `/stocks/[ticker]` | Unknown-ticker state | Unchanged (must still work) | Row shape grew; verify no regression | Open `/stocks/NOTREAL`; confirm "Unknown ticker" card renders (no chart, no fabricated data) and the link back to the leaderboard works. |

<!-- Change Type options: New page | New component | Updated layout | Added navigation | Changed behavior | Removed element | New form | New table | New modal -->

---

## Backend-Only Changes (No UI Impact)

- `app/engine/indicators.py` — adds `sma_series(values, period)` (rolling MA aligned to input, reusing the existing `sma`); pure computation, consumed by the `/bars` endpoint — no direct UI surface.
- `app/engine/themes.py` — extracts `theme_name(slug)` as a shared naming helper; behaviour of `score_themes` unchanged — no UI surface.
- `app/config.py` — new `InvalidationCfg { ma_period }` + cross-field validator (period ∈ `indicators.ma_periods`); config wiring only.
- `config.yaml` — adds `decision_rules.invalidation: { ma_period: 50 }`; sources the invalidation MA basis (no magic number) — no UI surface.
- `incredible_auto_dev/config/install-security-policy.json` — adds `lightweight-charts` to the npm allowlist (supply-chain gate); build/security config only.
- Backend tests (`test_bars.py` new, `test_indicators.py`, `test_scoring.py`, `test_config_engine.py`, `test_config.py`, `test_sectors.py`, `test_themes.py`) — verification only, no UI surface.

> Note on `app/api/stocks.py`: the new `GET /api/stocks/{ticker}/bars` endpoint is a backend-API change, but it **is consumed by the frontend** (`fetchStockBars` → `PriceChart`), so its impact is captured in the surface table above (it is **not** "not visible yet"). The `invalidation`/`themes` additions in `app/engine/scoring.py` also surface on the detail page and are captured above.

---

## Summary

- **Frontend surfaces changed:** 1 route (`/stocks/[ticker]`)
- **New pages/routes:** 0 (no new route; existing detail page completed)
- **Modified components:** `app/stocks/[ticker]/page.tsx` (added `ThemeAndInvalidationCard` + `StockChartPanel`), `lib/api.ts` (types + `fetchStockBars`); 1 new component `components/price-chart.tsx`
- **Navigation changes:** no (theme chips link to the existing `/themes` home; no nav-skeleton change)
- **Backend-only changes:** 6 (indicators series helper, themes helper, config model, config.yaml, install policy, tests)
