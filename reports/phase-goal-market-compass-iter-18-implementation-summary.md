# goal-market-compass-iter-18 — Implementation Summary

**Phase:** goal-market-compass-iter-18
**Date:** 2026-08-26
**Written by:** developer

---

## Features Implemented

This is a backend-only maintenance iteration with no new user-facing feature. It makes a previously-built
safety mechanism actually effective on the real, live database rather than only proven on disposable test
data.

- **The real database now has a working "incident quarantine" switch.** A new small table
  (`maintenance_boundaries`) was created on the live database and switched on for the eleven trading days
  damaged by an earlier data-recovery incident (2026-05-12 through 2026-08-12). With this switch on,
  starting the application can no longer silently overwrite the results Trendora is still waiting to
  properly rebuild for those eleven days.
- **Closed a second, previously-unnoticed way the app could have overwritten that same data.** While
  building the fix above, a second, separate startup code path was found that could also have written
  over the protected days — it is now protected the same way as the first.
- **Independent live proof, not just a design.** After switching the protection on, the developer directly
  checked the real database and confirmed: the protection actually blocks all eleven protected days, does
  not block any other day, and the check itself made zero changes to any data.

## Changed Behavior

- **Application startup, background history warm-up**: Previously, starting Trendora could recompute and
  overwrite results for the eleven data-recovery-damaged days as part of its normal background
  "catch up on history" step. Now, if the incident-quarantine switch is on (as it now is on the real
  database), startup skips writing to those eleven days and logs why, instead of silently overwriting
  them. For every other, unaffected day, startup behaves exactly as before.

## Backend-Only Items

- The incident-quarantine table and its one active row — a safety switch with no visible UI. It was never
  meant to have one (this is internal maintenance state, not something an end user needs to see or
  operate).
- Two new small command-line tools for creating that table and taking a before/after inventory of the
  whole database — operator-only maintenance utilities, not application features.

## Incomplete Items

- **The actual repair of the eleven damaged days (rebuilding their results) is still not done and still
  not authorized.** This iteration only builds and proves the safety switch that must be on before that
  repair work could ever safely happen — it does not do the repair itself. That remains a separate,
  future decision requiring the owner's explicit go-ahead, exactly as before this iteration.
- Nothing else from this iteration's plan is incomplete.

## Config and Environment Changes

- No `config.yaml` changes.
- Database change: one new table (`maintenance_boundaries`, 7 columns) and one new row in it, on the live
  database `apps/backend/data/trendora.db`. No existing table's schema or data changed. Confirmed
  independently: every pre-existing table's row count is unchanged; the total database file size is
  unchanged; the most recent stored trading day is unchanged.
- No new environment variables.

## Known Limitations

- A pre-existing, unrelated test-suite issue was discovered by coincidence while checking this iteration's
  changes: one specific automated test about caching efficiency during startup warm-up
  (`test_warmup_loads_each_symbol_at_most_once_across_cadence_and_forward_returns`) fails on its own,
  independent of anything built in this iteration — confirmed by testing it against the code exactly as
  it was before this iteration started. It is not fixed here (out of scope for this iteration) and does
  not affect anything this iteration built or the real database's safety.
- The Stage D repair work (rebuilding the eleven damaged days) remains entirely un-started and requires a
  separate, explicit owner decision before any future iteration may begin it.
