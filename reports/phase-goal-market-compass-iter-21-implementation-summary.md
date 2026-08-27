# goal-market-compass-iter-21 — Implementation Summary

**Phase:** goal-market-compass-iter-21
**Date:** 2026-08-27
**Written by:** developer

---

## Features Implemented

- **J-11 Stage F — stale cache cleanup**: this iteration is a database maintenance step, not a product
  feature. It classified all seven internal "cache" tables that could have been left showing outdated
  numbers after the previous two maintenance steps (Stage D and Stage E, run in earlier iterations)
  rebuilt eleven trading days' worth of data, and deleted the ones proven to hold outdated content — 1,643
  rows total, across five tables. Nothing about this is visible on any page; it runs with the app
  completely turned off.

---

## Changed Behavior

- None. No page, API response, or displayed number changes as a result of this iteration. The affected
  tables are internal performance caches — once the application is eventually allowed to restart (after a
  later "Stage G" verification step, not yet run), each of the emptied caches will simply recompute itself
  automatically the first time something asks for that data, the same way it always has.

---

## Backend-Only Items

- The entire iteration is backend-only, maintenance-only, database-only. There is no UI wiring because
  there is nothing to wire — no new user-facing capability was added.

---

## Incomplete Items

- **Stage G (final verification)**: deliberately not attempted this iteration — it was explicitly out of
  scope. Stage G is the only step allowed to declare the underlying incident (from a data-deletion mishap
  several weeks ago) fully resolved. Until Stage G runs and passes, the app stays paused for normal use,
  and the "quarantine" flag that has been blocking that trading-day data since the incident stays turned
  on. This is expected and intentional — it is the next step in an ongoing four-part repair plan (already
  two-thirds done: parts one and two ran cleanly in the two prior iterations).

---

## Config and Environment Changes

- None. No configuration file, environment variable, or database schema changed. This iteration only
  deleted rows from existing tables — no new tables, no new columns, no new settings.

---

## Known Limitations

- The most important finding this iteration made and fixed: one of the seven caches (a "data availability"
  summary shown on the Data Manager page) had a real bug risk — if left alone, the very first time someone
  loaded that page after the app restarts, it would have shown the OLD (pre-repair) picture of what data is
  available, without any warning that it was stale. That cache row is now deleted, so the page will
  correctly show "not yet computed" and recompute fresh instead of silently showing outdated information.
- One cache (tracking which stocks were in the research universe on which day) was deliberately left in
  place rather than deleted, because doing so lets the app avoid an expensive multi-minute recomputation
  the next time it's needed — verified live, before making that choice, that this shortcut is provably safe
  given the exact rows involved.
- The app remains intentionally offline for this whole iteration and will stay offline until the next
  maintenance step (Stage G) runs and passes.
