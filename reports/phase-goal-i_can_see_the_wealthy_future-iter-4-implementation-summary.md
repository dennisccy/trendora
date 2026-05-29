# Goal Iteration 4 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future-iter-4
**Date:** 2026-05-29
**Written by:** developer

---

## Features Implemented

- **Stock Detail price chart**: Opening any stock from the leaderboard (e.g. NVDA) now shows a
  candlestick price chart with 20/50/150/200-day moving-average overlay lines and a volume bar
  series underneath — the full picture of how the stock has traded.
- **Theme chips on Stock Detail**: The page lists which themes the stock belongs to (e.g. "Ai Data
  Centre", "Semiconductors", "Megacap Leaders") as clickable tags that jump to the Themes page.
- **Concrete invalidation level**: The page now states, in plain language, the price below which the
  idea is wrong — e.g. "Invalid below the 50-DMA at $198.73". This sentence is written by the
  backend; the page just displays it. When a stock is too new to have enough history, it honestly
  says "Invalidation level NA — insufficient history" instead of inventing a number.
- **New price-history data feed**: A new backend address, `GET /api/stocks/{ticker}/bars`, supplies
  the chart's daily price bars and the moving-average lines. The moving averages are calculated once
  on the server; the page only draws them.

---

## Changed Behavior

- **Stock Detail page** (`/stocks/[ticker]`): Previously it showed only the three scores plus a note
  saying the chart "arrives in the next iteration". Now it shows the chart, the theme chips, and the
  invalidation level alongside those same three scores. The scores themselves are unchanged and
  still match the leaderboard exactly.
- **Stock data rows**: Every stock row returned by the API now also carries its theme list and its
  invalidation level. This is additive — existing pages that don't use these fields are unaffected,
  and the leaderboard still renders all rows.

---

## Backend-Only Items

- None. Every new backend capability (the price/MA/volume feed, the invalidation level, the theme
  membership) is surfaced on the Stock Detail page.

---

## Incomplete Items

- **Score history across past snapshots** on the detail page is intentionally NOT included — it
  depends on snapshot persistence, which is scheduled for the next iteration (iter-5). It is not
  required for this iteration's goal.
- Everything in this iteration's spec (chart, volume, theme chips, server-computed invalidation) is
  complete.

---

## Config and Environment Changes

- `config.yaml` → added `decision_rules.invalidation: { ma_period: 50 }` — chooses which moving
  average defines the invalidation level (must be one of the configured MA periods; validated at
  startup). Default: the 50-day moving average.
- Supply-chain allowlist (`config/install-security-policy.json`) → added `lightweight-charts` to the
  approved npm packages, so the charting library installs cleanly through the security gate.
- New frontend dependency: `lightweight-charts@5.2.0` (the charting library — free, open-source
  Apache-2.0, runs entirely in the browser, needs no account, key, or network access). Installed via
  `npm install` (recorded in `package.json` / `package-lock.json`).
- No environment variables, database schema, or migrations changed.

---

## Known Limitations

- **Chart rendering must be confirmed in a real browser by QA.** Automated build/type checks confirm
  the page compiles, but the chart paints to an HTML canvas — only a browser test confirms the
  candles, MA lines, and volume bars are actually visible.
- **Fresh servers required for QA.** During verification, a leftover backend from a previous run was
  still occupying the project's usual port (8835) and served outdated code (the chart's data address
  returned "Not Found"). QA and the orchestrator must ensure the backend and frontend they test are
  freshly started on the expected ports, or the chart evidence will be stale/blank.
- **Pre-existing security advisories in Next.js** (the web framework, version 15.1.3) and its bundled
  PostCSS remain. They are unrelated to this iteration's work; the new charting library adds none.
  Addressing them means upgrading Next.js, which is out of scope here.
- The "stack notes" describe the charting library as MIT-licensed; it is actually Apache-2.0 — both
  are permissive and key-free, so there is no practical difference. Noted for accuracy.
