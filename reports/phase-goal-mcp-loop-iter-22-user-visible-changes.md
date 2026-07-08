# Phase goal-mcp-loop-iter-22 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-22
**Date:** 2026-07-08
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On the Dashboard (`/`), in the **"Regime × phase cross-view"** card (the two-pane chart shown just below the Market Regime / Market Phase summary cards), users can now see three deep equity-index benchmark lines — **S&P 500 (^SPX)**, **Nasdaq 100 (^NDX)**, and **Dow Jones Industrial Average (^DJI)** — that extend back to **1996-01-02**, well before the existing SPY/QQQ/IWM/RSP/DIA ETF lines' own starting points (~1999–2005). This renders automatically on page load (the default range is "all" and the card always fetches full history) — no new click or control is required.
- The same chart now also plots a volatility line, **CBOE Volatility Index (^VIX)**, and one macro-proxy line, **"10Y-2Y spread proxy (^TNX)"**, alongside the equity lines.
- Users can see, directly in that chart's legend and in its hover tooltip, exactly which data vendor supplied each line — **"Stooq"**, **"Yahoo"**, or **"FRED-macro proxy"** — printed right next to the line's name (e.g. "S&P 500 Index (^SPX) (Stooq)"). Lines with no recorded vendor (the 5 original ETF lines) show no vendor text at all, rather than a guessed or fabricated one.
- Users can open **`/data`** and see a new **"Index & benchmark data provenance"** panel — a table listing every line from that chart together with its data vendor and its true first-recorded date, in one place, instead of needing to hover over each line on the chart individually.

---

## What Changed in the Visible UI

- The Dashboard's "Regime × phase cross-view" card now plots **up to 10 lines instead of 5**.
- That chart's legend and hover tooltip now show a **vendor label** next to a series' name wherever one is recorded, e.g. "CBOE Volatility Index (^VIX) (Yahoo)" and "10Y-2Y spread proxy (^TNX) (FRED-macro proxy)".
- The 5 newly added lines render in **5 newly added, visually distinct colors**, so none of the 10 simultaneous lines look identical to another (previously only 5 colors existed, which would have started repeating once a 6th line appeared).
- `/data` gained a new card, **"Index & benchmark data provenance,"** placed directly beneath the existing "Macro feed" panel. It has its own loading skeleton, its own error message ("Vendor disclosure unavailable"), and its own "no data" message, independent of the rest of the page.

---

## What Old Behavior Changed

- **None functionally.** The 5 pre-existing ETF lines (SPY/QQQ/IWM/RSP/DIA) keep their exact original values and exact original colors — this change only adds fields and additional lines, verified byte-identical for the existing lines. No existing chart control (range switcher, hover, zoom), endpoint shape (aside from new optional fields), page layout, or navigation item changed.
- **Minor visual density note (not a functional change):** the chart legend can now list up to 10 entries instead of 5, so it occupies more horizontal/vertical space on screen than before.

---

## Not Visible Yet

- A one-time data-loading script (`apps/backend/scripts/load_missing_index_symbols.py`) was used to backfill the three new deep-benchmark symbols' historical prices into the local database. This has no UI or API trigger — it is a command-line tool an operator/developer runs directly, not an ongoing user-facing capability.
- The identical vendor-label and color-palette fix was **also** applied to a second, older chart component (`components/index-regime-chart.tsx`, wrapped by `components/major-indexes-card.tsx` — the original "J-44 Major indexes & regime" card). This card is **not linked from any page in the app today** — an earlier iteration replaced it with the "Regime × phase cross-view" card as the Dashboard's one live chart (confirmed: zero imports of either file anywhere in the route tree). The fix is present and correct in the code but has **no live effect for any user** unless a future iteration reconnects that card to a page.
