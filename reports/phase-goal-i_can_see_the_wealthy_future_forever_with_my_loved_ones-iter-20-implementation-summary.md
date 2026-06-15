# Goal iter-20 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20
**Date:** 2026-06-15
**Written by:** developer

---

## Features Implemented

- **Faster research labs (J-72)**: The Setup & Pattern event study now serves its figures from a saved
  cache instead of recomputing them on every request. The first time a given study is asked for it is
  computed once and stored; every later request reads the stored result. The exact numbers are unchanged —
  this is purely a speed improvement. Live check: a repeated event-study request dropped from ~28 seconds
  to ~0.02 seconds. The cache refreshes by itself whenever the data set changes (a backfill adds data, or a
  removal deletes it), so it can never show stale numbers. The `/research` page also loads section by
  section, so one slow query no longer blocks the whole page.

- **Forward returns on the leaderboard and stock detail (J-75)**: Every row on `/stocks` now shows five
  realized forward-return columns — 1, 5, 10, 20, and 60 trading days — colour-graded (green positive, red
  negative). These are the SAME stored figures the Backtest workspace already showed; they are read
  straight from storage, never recalculated. The columns are sortable. Where there are not yet enough days
  of price after the chosen date to measure a return, the cell honestly shows "NA" (so at or near the
  latest date all five are NA). The Stock Detail page shows the same five returns for the chosen date in a
  new "Realized forward returns" panel.

- **Regime × Setup × Pattern evidence table (J-77)**: A new study on `/research` shows, as a ranked
  sortable table, which combinations of (market regime + setup status + detected pattern) have historically
  produced the strongest risk-adjusted forward returns. Each row reports the sample count, mean and median
  return, hit-rate, expectancy, and two downside-only risk-adjusted figures. It honours the Episodes/Pooled
  overlap toggle and the All-history / As-of-date mode. Every row's sample-count chip opens a drill-down (in
  a new tab) listing the exact observations behind that combination — and the drill-down count always
  matches the published count exactly. "Risk" here only ever means downside risk, never normal upside
  movement.

---

## Changed Behavior

- **`/research` event study**: Previously recomputed on every request. Now served from a self-refreshing
  cache (identical numbers, much faster). No visible change to the figures.

- **`/api/stocks` and `/api/stocks/{ticker}`**: Previously the per-stock rows carried scores, setup,
  patterns, and themes. Now each row additionally carries its five realized forward returns (read from
  stored data). This is an additive field — every existing value is unchanged.

---

## Backend-Only Items

- None. Every backend addition has corresponding UI: the new `/api/research/regime-setup-pattern` endpoint
  drives the new `/research` study table; the new `/api/research/samples?kind=regime-setup-pattern` cohort
  drives its drill-down; the new per-stock forward returns drive the `/stocks` columns and the Stock Detail
  panel.

---

## Incomplete Items

- None of the iter-20 spec items are deferred. J-72, J-75, J-77 are fully implemented backend + frontend.
- The full backend test suite (~790 tests, ~35-46 min) is NOT run inside the dev turn (it cannot finish in
  a single turn) — it is handed to the pump as a background run for the final green gate. The targeted
  modules for the changed code were run to completion and pass (see "Config and Environment Changes" →
  none; see the dev handoff for exact counts).
- The data-walled journeys J-22/J-23/J-24 remain honestly blocked (no code change this iteration), as
  planned.

---

## Config and Environment Changes

- **No new config section** and **no new environment variable**. The Regime × Setup × Pattern study reuses
  the existing config catalogs (regime labels, setup statuses, pattern keys) and the existing
  `walk_forward.min_sample` threshold, so no config-narrowing site needed touching.
- **New database table** `event_study_cache` (created automatically on startup; no migration step). It only
  stores a cache of already-computed research figures — it is not part of any immutable snapshot and can be
  safely deleted (it rebuilds on demand).

---

## Known Limitations

- The event-study cache's first computation for a given (subject, view, date) is still as slow as before
  (it must compute once to populate the cache); only repeated requests are fast. This is the intended
  cache-on-first-use behaviour.
- On the committed seed the market sits mostly in a Defensive regime with most names "Avoid", so the
  Regime × Setup × Pattern table shows a small number of populated combinations (the rest are honestly NA /
  low-sample). This reflects the real seed data, not a bug.
- When the long full-database warm-up or test suite is running on the same machine, the single live backend
  worker competes for CPU and a first-time (uncached) research request can be slow or time out — a resource
  contention effect, not a defect.
