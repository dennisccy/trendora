# Iteration 23 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23
**Date:** 2026-06-16
**Written by:** developer

---

## Features Implemented

- **Forward-return columns on the Themes leaderboard (J-81)**: The Themes page now shows, for every theme, how its members actually performed over the next 1, 5, 10, 20, and 60 trading days — the equal-weight average return of the stocks in that theme. You can sort the table by any of these columns. Cells that don't have enough future data yet (for example near the latest date) show "NA" rather than a made-up number.
- **Forward-return columns on the Sectors leaderboard (J-81)**: The Sectors page gains the same five columns, showing each sector/industry ETF's own realized return over the next 1/5/10/20/60 days, sortable. An industry ETF with no stored price bar shows NA honestly.
- **These numbers exactly match Backtest (J-81)**: A theme's or sector's forward return on its leaderboard is the same value the Backtest workspace's "Top Themes" / "Top Sectors" already showed for the same date and horizon — read from the same stored evidence, never computed a second way. So you can now read this evidence at the leaderboard level instead of only on Backtest.
- **Research combinations table — correct NA sorting (J-82)**: On the Research page, the "Regime × Setup × Pattern" table now pushes every row that displays "NA" to the bottom when you sort a numeric column (in both directions). Previously a low-sample row could jump to the top even though its cell read "NA".
- **Research combinations table — three filters (J-82)**: The table gains Regime, Setup, and Pattern filter dropdowns (each defaulting to "All"). Pick any combination to narrow the rows; the filters work together with sorting.
- **Research combinations table — drill-down works for every row (J-82)**: Clicking the "N=" sample-count chip on any row — including a row with no detected pattern ("— (none)") — now opens the exact list of underlying observations in a new tab, with a count that always equals the row's published N. Previously some of these chips returned an error.
- **Research combinations table — defaults to the Pooled view (J-82)**: This one table now opens in "Pooled" mode (every signal-day counted), with "Episodes" one click away. The rest of the Research page still defaults to Episodes.

---

## Changed Behavior

- **Themes / Sectors leaderboards**: Previously they showed only the score, recent basket returns (1m/3m for themes), breadth, and trend. Now they also show five realized forward-return columns and let you sort by them.
- **Research "Regime × Setup × Pattern" table**: Previously it had no filters, sorted NA cells inconsistently, opened in Episodes mode, and could error when drilling into certain rows. Now it filters by regime/setup/pattern, sorts NA to the bottom, opens in Pooled mode, and every visible row's drill-down works.
- **Research samples drill-down for the combinations table (technical contract)**: Previously, drilling into a combination whose three labels were each individually valid but which the table never showed would return an empty result. Now it returns an honest "not available" error — because the table only ever shows combinations that have data, so there is no chip to click for an empty one. (This only affects the combinations table; other sample drill-downs are unchanged.)

---

## Backend-Only Items

- None. Every backend change is surfaced in the UI (the new `forward_returns` field powers the Themes/Sectors columns; the samples-validation fix powers the Research drill-down chips).

---

## Incomplete Items

- None of the in-scope items are deferred. J-81 and J-82 are fully implemented.
- The full automated backend test suite (about 34 minutes) was not run in this development turn — it is handed off to the automation runner ("the pump") to execute. The targeted tests covering every changed area pass, and the frontend type-checks cleanly.

---

## Config and Environment Changes

- None. No new configuration keys, environment variables, or database migrations were introduced. The forward-return horizons are read from the existing `config.walk_forward.horizons`.

---

## Known Limitations

- Forward-return cells are honestly "NA" wherever there is not enough future price data yet (especially at and near the latest date for the longer horizons) — this is by design, never a fabricated value.
- A theme's forward return is the equal-weight average over only the members that have a stored return; members without one are skipped (not treated as 0). A theme where no member has a stored return shows NA.
- This evidence carries survivorship bias (the same honest caveat shown across the Backtest and Research surfaces) — it describes what historically happened, it is not a prediction.
- Live in-browser confirmation of the new columns/filters is performed in the subsequent QA step, not in this development turn.
