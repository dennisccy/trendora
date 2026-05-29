# goal-i_can_see_the_wealthy_future-iter-4 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-4
**Date:** 2026-05-29
**Agent:** developer
**Status:** complete
**Surface changed:** `/stocks/[ticker]` only (Stock Detail)

## What Was Built (UI)

The Stock Detail page graduates from a scores-only consistency proof into the full per-stock research
view. Below the existing setup/reason header and above the three score cards, the page now shows:

1. **Theme membership + invalidation card** (`ThemeAndInvalidationCard`):
   - **Theme chips** — one `Badge` per theme the stock belongs to, each wrapped in a `Link` to the
     existing `/themes` page (hover + focus-visible states). "Not a member of any tracked theme."
     when the list is empty.
   - **Invalidation note** — `row.invalidation.note` rendered **verbatim** (e.g. "Invalid below the
     50-DMA at $198.73"). The frontend never assembles the "$X" string. When `level` is null
     (short history) the honest NA note renders in amber (`--warn`).

2. **Price & moving-averages card** (`StockChartPanel` → `PriceChart`):
   - A candlestick chart (OHLC) with **20/50/150/200-DMA overlays drawn from the server `ma` series**
     and a muted **volume** histogram sub-pane.
   - Loading (skeleton), empty ("No price history…"), and error ("Chart unavailable" — honest, the
     scores above are unaffected) states.
   - A compact legend mapping each plotted series to its colour.

## Key implementation notes

- **Single source of truth preserved.** `PriceChart` PLOTS the server `ma[period]` arrays; it does
  **not** compute any moving average from the close array. The three scores still come from the same
  `/api/stocks/{ticker}` row as the leaderboard (J-06 unchanged).
- **New dependency:** `lightweight-charts@5.2.0` (Apache-2.0, client-side, no key, no runtime network
  callout). `PriceChart` is `"use client"` and **dynamically imports** the library inside a
  `useEffect` (the lib touches `document`, so this avoids SSR evaluation) and disposes the chart on
  unmount. Uses the v5 series API (`chart.addSeries(CandlestickSeries, …)`).
- **Design system discipline:** all chart colours are read at runtime from the SAME CSS palette
  tokens in `app/globals.css` (`--pos`, `--neg`, `--accent`, `--warn`, `--text-muted`,
  `--text-faint`) — no arbitrary hex. Candles green/red = `--pos`/`--neg`; MA overlays cycle
  accent → warn → muted → faint (shortest brightest); volume muted (`--text-faint`). Numbers use the
  `.num` (monospace tabular) class. Chart height set via the `h-80` Tailwind class.
- **New fetcher:** `fetchStockBars(ticker, signal)` → `BarsResponse` in `lib/api.ts`; throws on
  non-200 so the chart shows an explicit unavailable state (never fabricated).

## Files Changed

- `apps/frontend/components/price-chart.tsx` *(new)* — client-only Lightweight-Charts wrapper
- `apps/frontend/app/stocks/[ticker]/page.tsx` — chart panel + theme chips + invalidation note
  (placeholder paragraph removed)
- `apps/frontend/lib/api.ts` — `ThemeChip`, `Invalidation`, `PriceBar`, `BarsResponse` types;
  `fetchStockBars`; `StockRow` extended with `themes` + `invalidation`
- `apps/frontend/package.json`, `apps/frontend/package-lock.json` — `lightweight-charts@5.2.0` pinned

## How to verify (operator)

1. Start backend + frontend (`bash scripts/dev.sh`, or the QA start scripts) on a **fresh** pair of
   ports — make sure no stale server from a previous run is bound (see the dev handoff's lesson-#1
   note about port 8835).
2. Open `/stocks`, click a leader row (e.g. **NVDA**).
3. On `/stocks/NVDA` confirm: the candle chart renders with visible MA overlay lines and a volume
   sub-pane; theme chips (`Ai Data Centre`, `Semiconductors`, `Megacap Leaders`) render and link to
   `/themes`; the invalidation note shows a concrete level ("Invalid below the 50-DMA at $…"); and
   the three score cards still show bucket + 0-100 + ≥3 named components.
4. Open `/stocks/NOTREAL` → "Unknown ticker"; stop the backend and reload a stock → "Backend
   unavailable" / "Chart unavailable" (nothing fabricated).

## Tests Run

- `cd apps/frontend && npm run build` → compiled + typechecked successfully (all routes).
- `next dev` boot + on-demand compile of `/stocks/[ticker]` → 200, no errors.
- Live backend smoke confirmed the chart's data source (`/api/stocks/NVDA/bars`) returns 1356 bars
  and per-period MA series; canvas rendering itself is validated by browser-QA.

## Known Issues

- Canvas pixel rendering (candles/overlays/volume actually drawn) must be confirmed by browser-QA on
  a fresh server — `npm run build` and `next dev` verify compilation/typing, not the painted canvas.
- Pre-existing `next@15.1.3` advisories remain (unrelated to this change; see dev handoff).
