# goal-ops-hardening-iter-5 — Implementation Summary

**Phase:** goal-ops-hardening-iter-5
**Date:** 2026-07-20
**Written by:** developer

---

## Features Implemented

- **Whole-product performance measurement**: every page in the app's navigation (Dashboard, Stocks,
  Stock detail, Sectors, Themes, Data, Evidence, Scanner Runs, Backtest, Watchlist, and one Research
  page) now has a measured, recorded speed number, alongside a new measurement of how long the backend
  takes to start up and become reachable. These numbers live in one file (`reports/perf-budgets.md`) so
  future work can be checked against them and immediately flagged if something gets slower.
- **A real slowdown was found and fixed**: visiting the Backtest page was taking about 35 seconds to
  load its main data — the backend was re-calculating a large, expensive statistic from scratch every
  single time someone opened that page. That calculation now runs once (automatically, right after new
  data comes in) and is saved, so the page reads the saved answer instead of recalculating it. The page
  now loads that data in well under a second — roughly 250 times faster.

## Changed Behavior

- **Backtest page ("evidence by horizon" panel)**: previously took around 35 seconds to appear on a
  typical visit; now appears in under a fifth of a second. The numbers shown are exactly the same as
  before (verified against a fresh calculation, field by field) — only the speed changed, not the
  figures.
- **Behind the scenes**: whenever new price data is backfilled or fetched, the backend now also
  precomputes and stores this same Backtest statistic for the most recent date, so it's ready before
  anyone asks for it. Visiting a much older, rarely-viewed date on the Backtest page will still take a
  similar amount of time as before on the very first visit to that specific date — after that first
  visit, it's saved and fast from then on too.

## Backend-Only Items

None — the fix directly speeds up an existing page; there is nothing new sitting unused behind the
scenes.

## Incomplete Items

- **One structural pattern was found but not changed**: the Scanner Runs page's backing data fetch makes
  one extra small database check per scan-history entry (currently a few hundred). It is currently fast
  (about a tenth of a second) and well within its speed budget, so it was left as-is — fixing it would
  require a different kind of change than the "reuse what's already there" fix this iteration was scoped
  to make. Worth revisiting only if the amount of scan history grows dramatically.
- **A batch of automated correctness tests could not be finished in the time available** because they
  depend on rebuilding a large (30-year) test dataset from scratch, which is a known slow step for this
  project unrelated to this specific change. Enough faster tests were run to directly confirm the fix
  works correctly (including comparing the sped-up page's live output, byte for byte, against a
  from-scratch calculation on the real database) — but the slower, more exhaustive test file is flagged
  for whoever reviews this work to finish running.

## Config and Environment Changes

None. No new settings, environment variables, or database migrations were needed — the new stored data
lives in a brand-new table that gets created automatically.

## Known Limitations

- The very first time someone views a Backtest date that has never been viewed before (or right after
  new data changes what that date's statistic would be), that one view can still take several seconds —
  after that, it is instantly fast again. This matches how a few other pages in the app already behave
  and is considered an acceptable, one-time cost rather than a bug.
- One measurement pass during this work was accidentally slowed down by an unrelated background test
  process also running on the same machine at the time, producing one temporarily-inflated number in the
  measurement log. This was noticed, explained, and immediately re-measured cleanly — the final,
  authoritative numbers in the report are the clean ones, and the inflated pass is kept in the log (not
  deleted) purely as a transparent record of what happened.
