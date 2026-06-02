# Iteration 6 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-6
**Date:** 2026-06-02
**Written by:** developer

---

## Features Implemented

- **See what happened after a snapshot, on the chart (J-20)**: When you time-travel to a past date and open a stock's detail page, the price chart now draws the **full price history through the latest available date** — not just up to the date you picked. The part of the chart *after* your selected date is greyed out, marked with an "as-of {date}" divider and a legend label that says "Forward — after as-of (display only)". This lets you see how the stock actually behaved after the snapshot, while a caption makes clear those later bars are **for viewing only** — they do not change the stock's scores, setup, or pattern flag (those still reflect only what was known on the selected date).

- **See which names/sectors/themes actually delivered, on Backtest (J-21)**: The Backtest page now shows, for the date you're viewing, the **realized forward return** of each Top Sector, each Top Theme, and each Ranked-Cohort stock — right next to its score. One "Horizon" selector (1 / 5 / 10 / 20 / 60 trading days) now drives **both** the Return Attribution panels and these three new return columns at once: flip it and every return re-points together. Returns that haven't fully played out yet show "—" (not a fake number).

---

## Changed Behavior

- **Stock-detail chart**: Previously the chart stopped at the selected as-of date. Now (at a historical date) it extends through the latest date with the selected date marked and the later region greyed out and labelled display-only. At the latest date the chart looks exactly as before (there is nothing "after" to show).

- **Backtest page layout**: Previously the Top Sectors / Top Themes / Ranked-Cohort lists sat near the top, above the forward-test scorecard. Now the order is: scan summary (market regime + candidate counts) → forward-test scorecard → Return Attribution → the three leadership lists. The three lists moved **below** Return Attribution and each gained a realized-return column tied to the Horizon selector.

- **Backtest Horizon selector**: Previously it only re-pointed the Return Attribution panels. Now the same single selector also re-points the realized-return columns on the three leadership lists. There is still no second date picker on the page — the global date switcher in the top bar remains the only date control.

---

## Backend-Only Items

- None. Both backend additions are wired into the UI:
  - the chart's full-path option (`?through=latest` on the bars endpoint) is consumed by the stock-detail chart;
  - the leadership realized returns (added to the existing backtest response) are shown as the new return columns.

---

## Incomplete Items

- None for this iteration's scope (J-20 and J-21). The rest of the new wave is intentionally out of scope and deferred: the ~500-name universe (J-22), multi-timeframe bars and a chart timeframe selector (J-23/J-24), the Factor Lab / Setup & Pattern Lab on a new `/research` page (J-25–J-29), the volatility factor family (J-30), and the end-to-end synthesis (J-31). The goal is **not** fully achieved after this iteration — these remain unbuilt.

---

## Config and Environment Changes

- None. No new environment variables, no config additions, no database migration. Everything reads the existing committed offline price seed; no network/provider call was added.

---

## Known Limitations

- **The chart's forward region is genuinely display-only.** By design, the price/volume/moving-average bars drawn after your selected date never feed any score, bucket, setup status, pattern flag, or ranking — those always come from the snapshot for the selected date (data on or before it). This is the core no-lookahead guarantee, verified in the tests and in source (the full-path data is used only by the chart, never by the scoring engine).

- **Realized returns are read, never recomputed.** The new Backtest return columns are a direct read of the forward returns already stored for that snapshot — the sector value is its sector-ETF's stored return, the theme value is the equal-weight average of its members' stored returns, and each cohort stock's value is its own stored return. Returns for a horizon that hasn't elapsed yet (or for a name with no post-snapshot data) honestly show "—" rather than a fabricated 0%.

- **Survivorship bias still applies** to all forward-tested figures (the existing banner on the Backtest page is unchanged): the evidence is measured on the current-membership universe, so it should be read as an upper bound.
