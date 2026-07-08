# goal-mcp-loop-iter-22 — Implementation Summary

**Phase:** goal-mcp-loop-iter-22
**Date:** 2026-07-08
**Written by:** developer

---

## Features Implemented

- **Deep market history on the Dashboard chart**: the Dashboard's regime × phase cross-view chart now
  shows three deep equity-index benchmarks — the S&P 500, Nasdaq 100, and Dow Jones — reaching back to
  1996, well beyond the existing ETF lines' ~1999/2005 starting points, and **the full 30-year window is
  the default view the moment the page loads** — no zoom, pan, or extra click is needed to see the 1990s
  history. (An audit-stage fix corrected an earlier build in which the chart quietly opened zoomed in to
  only the most recent ~8 years, leaving the deep history technically loaded but off-screen — see
  "Changed Behavior".) This lets a user see three decades of market context on one chart instead of
  roughly two.
- **Honest data-source labeling ("who supplied this line?")**: every line on the major-indexes chart —
  new and existing — now shows, in its legend and on hover, which data vendor supplied it: "Stooq",
  "Yahoo", or "FRED-macro proxy". Lines with no recorded vendor (the original five ETF lines) show no
  label at all, rather than guessing or inventing one. This is the platform's "show your sources"
  posture made visible on its flagship chart.
- **A new "Index & benchmark data provenance" panel on the Data page**: a small table listing every line
  on the major-indexes chart with its vendor and its real first-recorded date, so a user auditing the
  platform's data sources doesn't have to hover over chart lines one at a time.
- **A volatility index and one macro-proxy line added to the chart**: the CBOE Volatility Index (VIX) and
  a "10-year minus 2-year Treasury spread" proxy line now also appear on the chart, each honestly labeled
  by vendor — the proxy line is explicitly named so it is never mistaken for the real market ticker.

## Changed Behavior

- **The major-indexes chart now plots up to 10 lines instead of 5.** Previously it always showed exactly
  the five configured ETFs (S&P 500, Nasdaq 100, Russell 2000, S&P 500 Equal-Weight, Dow 30). It now also
  shows the three deep benchmarks plus VIX and the macro proxy, whenever they have data for the selected
  time window (which, for the deep benchmarks, is essentially always — they go back to 1996).
- **Chart line colors were re-planned to avoid repeats.** With more than 5 lines now possible, the
  previous 5-color rotation would have started reusing colors (a 6th line would have looked identical to
  the 1st). The color set was expanded to 10 distinct colors so every line stays visually distinguishable
  at once. The original 5 lines keep their exact original colors.
- **The chart now opens showing the full history by default (audit fix).** The charting library has a
  built-in limit on how far it will zoom out; with three decades of daily data that limit meant the chart
  opened showing only the most recent ~8 years, so the newly-added 1990s history was loaded but hidden
  until a user manually dragged the chart back in time. That limit was lowered so the chart now fits the
  entire 1996→today span on first load. This was verified live in a browser: with no interaction, the
  left edge of the chart reads March 1996 and the S&P 500 / Nasdaq / Dow / VIX lines are drawn there. The
  chart is still fully zoomable/pannable for anyone who wants to focus on a recent stretch.

## Backend-Only Items

None. Every backend change (the new config entries, the loaded bars, the new `vendor`/`first` data
fields) is wired through to a visible UI change this same iteration — the chart legend/tooltip and the
new Data-page panel.

## Incomplete Items

None from this iteration's scope. Evidence re-certification and platform performance work are explicitly
separate, already-planned iterations (not part of what this iteration set out to do).

## Config and Environment Changes

- `config.yaml` — `index_chart.symbols` grew from 5 to 10 entries (added the S&P 500 Index, Nasdaq 100
  Index, Dow Jones Industrial Average, CBOE Volatility Index, and a "10Y-2Y spread proxy" line). No
  environment variables changed; no new secrets or API keys needed (all data is already committed to the
  project, sourced from the free Stooq/Yahoo providers used earlier in this project's history).
- One-time data step: the three new deep benchmark lines needed their historical prices loaded into the
  running local database (a one-time top-up of already-downloaded data, not a new download) — this was
  run as part of this iteration and verified to touch nothing else in the database (no existing scored
  history, snapshot, or evidence record was altered).

## Known Limitations

- This project has no automated browser-style test suite for the frontend; the new panel and chart
  changes were verified by the developer via type-checking and a live data check, but the full "does it
  look right on screen" verification (screenshots of the new legend labels, the new panel, and the wider
  color palette) is done by the QA step that follows this one, not by the developer.
- One pre-existing, unrelated data-housekeeping detail was noticed but intentionally left alone (out of
  this iteration's scope): the 10-year Treasury proxy line's underlying database rows go back slightly
  further (to 2005) than the officially-committed record for that line says (2021) — a leftover from
  before this project's 30-year data expansion. The displayed "first date" for that line honestly reports
  the officially-committed value (2021), which may look slightly later than what the chart line itself
  visually extends to. This is a data-bookkeeping loose end from earlier work, not something this
  iteration introduced or was asked to fix.
