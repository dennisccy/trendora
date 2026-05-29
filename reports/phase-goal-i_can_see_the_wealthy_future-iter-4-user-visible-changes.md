# Phase goal-i_can_see_the_wealthy_future-iter-4 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future-iter-4
**Date:** 2026-05-29
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

<!-- Target journey: J-05 — the Stock Detail page becomes the full per-stock research view. -->

- Users can now **study a price candlestick chart** for any leader by opening its Stock Detail page (e.g. from `/stocks`, click the **NVDA** row → `/stocks/NVDA`). The chart shows daily OHLC candles for the full available history up to the as-of date.
- Users can now **read the moving-average trend** directly on the chart: the 20-, 50-, 150-, and 200-DMA overlays are drawn as coloured lines over the candles, with a legend mapping each colour to its period.
- Users can now **gauge participation/volume** via a volume histogram pinned to the bottom of the same chart pane.
- Users can now **see which themes a stock belongs to** as clickable chips (e.g. NVDA → "Ai Data Centre", "Semiconductors", "Megacap Leaders"); each chip links to the `/themes` page.
- Users can now **read a concrete, server-computed invalidation level** in plain language — e.g. "Invalid below the 50-DMA at $198.73" — telling them the price level where the idea is wrong. When history is too short to compute it, an honest "Invalidation level NA — insufficient history" note appears in amber instead of a fabricated number.
- Users continue to see the three explainable scores (Leadership, Entry Quality, Risk) with A–E bucket, 0–100 value, and named component breakdown — now alongside the chart, themes, and invalidation, all on one page.

---

## What Changed in the Visible UI

- The **Stock Detail page** (`/stocks/[ticker]`) replaced its iter-3 placeholder paragraph ("the chart … arrives next iteration") with real content.
- A new **"Themes / Invalidation" card** appears below the setup/reason header: a row of theme chips on the left and the invalidation note on the right. "Not a member of any tracked theme." shows when the stock has no themes.
- A new **"Price & moving averages" card** appears below the themes card: a full-width candlestick chart with MA overlays, a volume sub-pane, a compact legend, and a "{N} bars · as of {date}" caption in the card header.
- The chart card has its own **loading skeleton**, **empty state** ("No price history is available for {ticker}."), and **error state** ("Chart unavailable" — explicit, with a note that the scores above are unaffected and nothing is fabricated).
- **Theme chips are interactive**: each is a focusable link to `/themes` with hover/focus-visible styling.
- All chart colours match the existing dark-workstation palette (candles green/red, MA overlays in accent→warn→muted→faint, muted volume); numbers stay monospace/tabular.

---

## What Old Behavior Changed

- **Stock Detail page layout**: previously showed only the setup/reason header plus the three score cards and a placeholder note. Now the same page additionally renders the themes/invalidation card and the price chart card between the header and the scores. The three score cards themselves are unchanged.
- **Per-stock API row shape**: `/api/stocks` (list) and `/api/stocks/{ticker}` (detail) rows now each carry two new fields, `invalidation` and `themes`. This is additive — the three scores/buckets/components remain byte-identical between list and detail (J-06 preserved). Testers should re-verify J-06 because the row shape grew.

---

## Not Visible Yet

- The new **`GET /api/stocks/{ticker}/bars`** endpoint is fully consumed by the chart on the Stock Detail page — nothing about bars/MA series is hidden.
- The **`invalidation` field also rides on every `/api/stocks` list row**, but the leaderboard list view does not display it (only the detail page does). This is intentional: the field is shared from the single scoring source; the list simply does not surface it.
- The **`themes` field likewise rides on every list row** but is only displayed on the detail page; the leaderboard does not show per-row theme chips. Intentional, not a gap blocking J-05.
