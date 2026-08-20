# goal-market-compass-iter-1 — Implementation Summary

**Phase:** goal-market-compass-iter-1
**Date:** 2026-08-20
**Written by:** developer

---

## Features Implemented

- **Pool-CSV sector fallback**: When a stock's sector isn't in Trendora's original curated list of
  122 names, the system now looks it up in the broader candidate-pool file instead of giving up.
  This means most of the ~400 stocks that used to show "Unassigned" on the Stocks page now show
  their real sector (Technology, Financials, Health Care, etc.).
- **Two-source sector disclosure on Methodology**: The Methodology page now explains, in plain
  language, exactly where a stock's sector label comes from — the curated list first, then the
  broader pool file as a backup — and states clearly that this only reflects a stock's sector
  *today*, not what it was on some past date.

## Changed Behavior

- **Stocks page (`/stocks`) Sector column and "Unassigned" filter**: Previously, about 78% of
  scored stocks showed "Unassigned" because only the original 122 names had a sector on file. Now,
  far fewer show "Unassigned" — only stocks that genuinely aren't listed anywhere still show it.
  Nothing on the page's layout changed; only the underlying data got more complete. A stock that
  truly has no sector information anywhere still honestly shows "Unassigned" — nothing is guessed.

## Backend-Only Items

None — every change made here is either already visible on `/stocks` (once fresh data is scored)
or newly visible on `/methodology`.

## Incomplete Items

None from this iteration's scope. One important **environment caveat** to know about: the
Methodology page's "Universe Selection" card — which now includes the new sector-basis
explanation — currently doesn't display at all in this environment, for a reason that has nothing
to do with this iteration's work. That card only appears once a separate, one-time setup step (an
"Expand" job that builds a reference file called `universe.json`) has been run, and that step has
never been run in this copy of the project. This is a pre-existing gap — three older tests already
in the project quietly skip themselves for the same reason. The new backend logic and its automated
tests all pass regardless; only the *visual* confirmation on the live page is blocked by this
unrelated, already-existing setup gap.

## Config and Environment Changes

- `config.yaml` → `universe.pool_sector_aliases` (new, empty by default) — a place to fix up sector
  names if a future data refresh spells them differently than Trendora expects. Not used today
  because the names already match.
- `config.yaml` → `methodology.universe_selection.sector_basis` (new) — the plain-language
  explanation text shown on the Methodology page.
- No database changes, no new environment variables, no new dependencies.

## Known Limitations

- To actually see the improved sector coverage on `/stocks`, a fresh scan needs to run (this
  happens automatically whenever the "Remove + backfill" data-refresh steps are used on the Data
  Manager page, or on the next scheduled data update) — a stock's sector value only ever gets
  written once, when it's first scored, so already-scored history keeps its old value and won't be
  fixed retroactively. This is intentional — it keeps historical records honest and unchanged.
- The new Methodology explanation can't currently be seen on the live page in this environment,
  for the pre-existing, unrelated reason explained above (a one-time setup step was never run
  here). The explanation itself is built and automatically verified to be correct; it's a display
  gate, not a bug in this iteration's work.
- While running the full automated test file for stock scoring (to triple-check this iteration's
  changes), one older, unrelated test failed — it checks a "risk budget" display feature that has
  nothing to do with sectors. Traced it back with git history: the code it's testing hasn't changed
  in about three months, and the test itself was written for a different, already-completed
  project phase. This is a pre-existing gap unrelated to this iteration, worth someone taking a
  look at separately, but it does not affect anything built here.
