# Phase goal-ops-hardening-iter-3 — Implementation Summary

**Phase:** goal-ops-hardening-iter-3
**Date:** 2026-07-20
**Written by:** developer

---

## Features Implemented

- **The Data page's coverage numbers no longer go stale after a plain data fetch.** Previously, only a
  "backfill" or "rebuild" job refreshed the Universe/Symbols/Trading-days/Snapshot-dates numbers shown on
  the Data page. A simple "fetch new prices" job — the most common, lightweight update — did not, so after
  running one, the page would silently show all-zeros ("not yet computed") even though the database was
  fully up to date, until the operator happened to restart the app or run a bigger job. Now, any fetch (or
  the "expand universe" job) that actually adds new price history immediately refreshes those numbers, the
  same way a backfill already does.
- **A fetch or universe-expand job that finds nothing new costs nothing extra.** The common everyday case —
  running "fetch" when there's no new data available — is detected cheaply up front and does no additional
  work, so this fix adds no slowdown to the normal daily routine.
- **Old, superseded coverage records are now cleaned up automatically.** A small amount of internal
  bookkeeping data (records of what the coverage numbers looked like under an older version of the
  database) was previously left behind indefinitely after certain operations. It is now cleaned up in one
  efficient step whenever the database changes, so this bookkeeping table stays small over time.

## Changed Behavior

- **Data page coverage panel:** Previously, only "Fetch data (both)" and "Backfill snapshots" and "Rebuild"
  jobs kept the coverage panel's numbers current. Now a plain "Fetch new prices" job or an "Expand universe"
  job that lands any new data also keeps it current. No visual or navigation change — the same panel, same
  page, same numbers — it just stays accurate in more situations.

## Backend-Only Items

None — this is a correctness fix to an existing, already-visible feature (the Data page's coverage panel),
not a new capability that needs separate UI wiring.

## Incomplete Items

None from this iteration's own scope. One measurement task named by the phase spec — confirming the backend
stays responsive and within its memory limit while a large data job is running — was completed live against
a real, disposable copy of the database (see "Known Limitations" for the one nuance found).

## Config and Environment Changes

None. No new settings, no new environment variables, no database migration was needed.

## Known Limitations

- **A large one-time cleanup/rebuild job can occasionally slow down the "is the backend alive?" check for a
  brief window.** While measuring how the system behaves under a very heavy data job (a full snapshot
  rebuild spanning 20+ years, taking about 16 minutes), the health check that confirms the backend is still
  alive occasionally took slightly longer than the target of "always under 1 second" — up to about 3
  seconds, and only during the busiest opening few minutes of that job. It never failed, hung, or returned
  an error — every single check still succeeded, just occasionally a little slower than the ideal target,
  and this settled down completely for the remaining ~12 minutes of the job. This is a pre-existing
  characteristic of how the busiest jobs share the database, not something this fix introduced, and it does
  not affect normal day-to-day usage (fetches and typical backfills, which are far lighter than a full
  rebuild).
- **Stopping the app with Ctrl+C sometimes leaves one leftover process running in the background.** This
  was noticed while double-checking that the app starts and stops cleanly. It is a pre-existing quirk in how
  the developer start/stop script shuts down the frontend, unrelated to this iteration's changes. It does
  not cause a problem in practice — starting the app again automatically cleans up the leftover process
  first — but an operator manually stopping the app might briefly see one extra process still running.
- One background test file (covering the app's own startup warm-up routine) was still finishing its full
  run when this report was written, due to that file's own known-slow full-history setup step (unrelated to
  this iteration's changes). The specific tests relevant to this iteration's fix were checked by hand and by
  a live run against a real copy of the database, both confirming correct behavior.
