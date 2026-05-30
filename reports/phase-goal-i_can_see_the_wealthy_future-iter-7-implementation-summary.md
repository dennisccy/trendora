# Goal Iteration 7 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future-iter-7
**Date:** 2026-05-30
**Written by:** developer

---

## Features Implemented

- **Watchlist (persistent, J-11)**: On the **Watchlist** page you can now save a stock by typing its
  ticker and a free-text reason and pressing **Add**. The saved stock appears in a table showing the
  date you added it, your reason, its **current** Leadership / Entry Quality / Risk grades (A–E plus
  the 0–100 number), its setup status, how its price has changed since you added it, and the price
  level that would invalidate the idea. You can remove any entry with its **Remove** button.
- **The list survives a restart**: saved stocks are stored in the database, so they are still there
  after the backend is stopped and started again — the watchlist is not just held in memory.
- **Always-current, never-stale scores**: the scores, setup, and invalidation shown for a saved stock
  are read live from the same scanner calculation the Stocks leaderboard uses, so a stock's numbers on
  the Watchlist always match its numbers everywhere else in the app (they are never copied or frozen
  onto the saved entry).
- **Honest errors, no fake saves**: adding a ticker that isn't in the tracked universe is rejected
  with a clear message; adding a stock that's already saved is rejected (no duplicate); and if the
  backend is unavailable the page says so instead of showing made-up data.

---

## Changed Behavior

- **Watchlist page**: Previously a placeholder that said "Adding lands in iter-7." Now a fully working
  add-form + table of saved stocks.

No other page changed. The Dashboard, Stocks, Themes, Sectors, Scanner Runs, and System Health pages
behave exactly as before.

---

## Backend-Only Items

- None. Every new capability (add / list / remove a watchlist entry) is reachable from the Watchlist
  page in the UI.

---

## Incomplete Items

- None from this iteration's spec. All Definition-of-Done items are implemented and verified: J-11
  works end to end, restart-persistence is proven by an automated test, the saved-stock scores match
  the Stocks page exactly, and the existing journeys (J-01–J-10) still pass.

---

## Config and Environment Changes

- **None.** No new environment variables, no config-file edits, no new dependencies. The database
  automatically gains one new table (`watchlist`) on startup; nothing for an operator to run.

---

## Known Limitations

- **"Price since added" reads 0.00% right after you add a stock.** The app runs on a frozen offline
  dataset whose latest date is 2026-05-28, so a stock added today has no newer prices yet — 0.00% is
  the correct, honest figure, not an error. It will show the real change once newer price data is
  loaded.
- **The watchlist is shared, not per-user.** This is a single-user local research tool, so there is
  one global watchlist and no login.
- **It is a research save-list, not a portfolio.** By design there is no share quantity, cost basis,
  profit/loss, or buy/sell action — Trendora places no orders.
- **Operational note:** an old backend process from a previous run was occupying the app's port
  without the new Watchlist feature; it was stopped so testing used the new code. The backend is
  currently stopped and will be restarted automatically by the QA step.
