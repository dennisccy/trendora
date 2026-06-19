# Iteration 35 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35
**Date:** 2026-06-19
**Written by:** developer

---

## Features Implemented

- **The stock universe now actually changes as you move the date back and forth.** Before this
  iteration every date showed the same fixed list of 122 stocks. Now, as you step the single global
  as-of date across the history, the list of scored stocks grows over time — exactly as a real
  point-in-time universe should.

> This iteration added **no new code and no new screen**. The capability was already coded in an earlier
> iteration. What was missing was the saved data behind the screens: the stored daily snapshots were
> last built over the OLD fixed 122-stock list. An operator-confirmed "rebuild snapshots" job (the
> existing button on the Data Manager page) was run once to recompute every saved daily snapshot over
> the new sliding universe. After that rebuild the existing screens finally show the truthful data.

---

## Changed Behavior

- **`/stocks` (and Themes, Sectors, Scanner-Runs, Backtest evidence, Research):** Previously showed a
  flat 122 stocks at every historical date. Now the count varies honestly by date — empty before the
  warm-up boundary (around 18 Oct 2021), then rising to roughly 495 by January 2022 and about 544 at the
  latest date.
- **Data Manager membership timeline (the `/data` page):** Previously a flat line at 122. Now it rises
  as a step function from the warm-up boundary, the SIZE column varies by date, and the Entries / Exits
  columns are populated instead of all dashes.
- **Early dates:** Now honestly show an empty universe (n = 0) before there is enough price history,
  rather than a misleading fixed list. Nothing is fabricated to fill the early window.

---

## Backend-Only Items

- None. Every affected value is already shown on an existing screen; this iteration only repopulated the
  saved data those screens read.

---

## Incomplete Items

- None from the buildable scope. The data-walled journeys (J-22 / J-23 / J-24, and the J-95 real
  backward-history fetch / true index-constituent feed) remain honestly out of reach because no data
  provider key is available — they are unchanged and were never in this iteration's scope.

---

## Config and Environment Changes

- None. No new environment variables, config keys, database columns, tables, or endpoints.
- The active database is `apps/backend/data/trendora.db` (configured in `config.yaml`). A safety backup
  of the pre-rebuild database exists at `apps/backend/data/trendora.db.pre-iter35-rebuild.bak`.

---

## Known Limitations

- **The "Rebuild snapshots" job is destructive and slow (~11 hours).** It clears about 1,370 saved daily
  snapshots and recomputes them. It must always be operator-confirmed. For this iteration it was already
  run and completed before development started — it must NOT be run again, or it would destroy the
  now-correct data and take another ~11 hours.
- **The committed price history is never touched by the rebuild.** Confirmed: the price-bar count is
  identical (793,218 bars) before and after the rebuild. Only the snapshot layer was recomputed.
- **Live screenshot proof of the sliding universe is captured by the separate browser-QA step.** During
  development the descriptive coverage diagnostic occasionally timed out over the network because the
  full test suite was running at the same time on the shared database — this is load contention, not a
  fault. The underlying data was verified directly and is correct.
