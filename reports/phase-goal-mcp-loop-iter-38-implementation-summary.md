# Phase goal-mcp-loop-iter-38 — Implementation Summary

**Phase:** goal-mcp-loop-iter-38
**Date:** 2026-07-15
**Written by:** developer

---

## Features Implemented

- **Watchlist concentration X-ray**: the Watchlist page now shows a new "Concentration X-ray" section
  that tells the owner how concentrated their saved list of stocks really is — not just a flat list of
  names, but how many of those names actually move together. It shows a grid of how correlated every
  pair of watchlist stocks is with every other one, groups stocks that move together into visual
  clusters, and gives one headline number: "effective independent bets" (for example, "≈ 2.0 over the
  last 126 trading days"), which answers "how many genuinely different bets does my watchlist actually
  represent, versus how many names are just duplicates of each other in disguise."
- **Sector, theme, and shared-setup breakdowns**: alongside the correlation view, three small bar
  charts show what fraction of the watchlist sits in each sector, each investment theme, and each
  current setup classification (e.g. how many names are currently "Actionable" versus "Avoid"). This
  surfaces crowding the owner might not otherwise notice — for example, five names that are all
  technology stocks in the same theme.
- **Honest gaps, never guesses**: a stock that was only recently added to the watchlist (or otherwise
  has too little price history) shows up as a clearly marked "not enough data" cell in the grid instead
  of a made-up number. A watchlist with only 0 or 1 names shows an honest "add one more name" message
  instead of an empty or broken chart.

---

## Changed Behavior

- **`GET /api/watchlist` response is now richer**: the API response the Watchlist page already used
  now carries one additional piece of information (the concentration data described above) alongside
  everything it already returned. Nothing that was there before was removed or renamed — existing
  behavior (adding a stock, removing a stock, the existing table of saved stocks) is unchanged.

---

## Backend-Only Items

None — every new computation this phase introduces (the correlation grid, the clusters, the "effective
independent bets" figure, and the sector/theme/setup breakdowns) is visible on the `/watchlist` page.

---

## Incomplete Items

None from this phase's scope. Two closely related, larger features were intentionally deferred to
future phases per the plan (not part of this phase's job):
- A per-stock "how much can this hurt" risk card (a separate future phase).
- Phase-conditional drawdown/dry-spell expectation panels (a separate future phase).
- A similar correlation view on the Evidence page for certified claims (a separate future item this
  phase's underlying math will be reused for later, but that page itself is untouched this phase).

---

## Config and Environment Changes

- New settings section in the project's `config.yaml` (`watchlist.xray`) controls three tuning knobs
  for the new feature:
  - How many trading days of price history the correlation view looks back over (default: 126 days,
    about 6 trading months).
  - How strongly two stocks must move together before they're grouped into the same visual cluster
    (default: 0.70 on a −1..+1 correlation scale).
  - The minimum amount of price history a stock needs before it can be included in the correlation
    math at all (default: 60 trading days) — below that floor, the stock is shown as "not enough data"
    rather than a guess.
  - These are pre-set to sensible defaults; no action is required to use the feature, and no
    environment variable was added.
- No database schema change. No new API endpoint. No new page or navigation entry — the feature lives
  as a new section on the page that already existed.

---

## Known Limitations

- The correlation view needs at least 2 stocks on the watchlist to show anything meaningful (a
  correlation, by definition, requires a pair). With 0 or 1 names saved, the section shows a clear
  "not enough names yet" message rather than an empty or broken chart.
- A stock is excluded from the correlation math (shown as "not enough data") if it has under 60 trading
  days of price history within the lookback window — this is a deliberate honesty floor, not a bug: the
  alternative would be showing a correlation number that isn't statistically meaningful.
- This section is purely descriptive — it does not tell the owner to buy, sell, trim, or rebalance
  anything. It only shows what the data says about how the watchlist behaves.
- The project's automated backend test suite includes one file (`test_api_watchlist.py`) that takes
  several minutes to run because it loads and warms up the full historical price dataset as part of its
  setup — this is a pre-existing characteristic of the test suite on this project's 30-year data basis,
  not something this phase introduced or slowed down further.
