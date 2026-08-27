# Iteration 22 — Implementation Summary

**Phase:** goal-market-compass-iter-22
**Date:** 2026-08-27
**Written by:** developer

---

## Features Implemented

- **J-11 incident closure (Stage G — the final verification gate)**: this iteration ran the last of a
  five-stage database repair (Stages C through G) that fixed the damage left behind by an old testing
  mistake (iteration 5's destructive drill, back in mid-August). Every one of the twelve required checks
  passed — the raw price data, the eleven rebuilt daily snapshots, the derived statistics, the historical
  "next-session" reports, and every cache all came back clean and consistent. The incident is now formally
  closed: **`J-11 INCIDENT STATUS: FULLY REPAIRED`**.
- **One small safety fix**: closed a gap where, once the app is running normally again, a single page visit
  to one of the eleven previously-damaged dates could have quietly re-created a stale cache entry the
  repair had just cleared out. That path is now blocked while the repair's safety lock is active, using
  the exact same safety mechanism already protecting two other parts of the system.
- **A genuine bug found and fixed during verification**: one small piece of cached data (part of the
  "which stocks are actively tracked" history) turned out to still hold an outdated value for one of the
  eleven repaired dates. The verification step caught this, discarded the outdated cache entry, and the
  system will recompute it correctly the next time it's needed. Nothing else was affected.

---

## Changed Behavior

- **Data page (`/data`) caching**: when someone visits a historical date's coverage numbers, the system
  now double-checks that date isn't still under an active maintenance lock before caching fresh numbers for
  it. For every date NOT under such a lock (i.e., everything, once the repair's lock is lifted), behavior
  is completely unchanged. This only matters while the (now-lifted) repair lock is active.

---

## Backend-Only Items

- None. This iteration made no changes reachable through the app's user interface. No page, screen, or
  visible feature changed. The repair work itself has no UI of its own (by design — see `docs/goal.md`).

---

## Incomplete Items

- None from this iteration's own scope. Everything the iteration set out to verify, verified successfully.

---

## Config and Environment Changes

- None. No config file changes, no new environment variables, no schema/database migration.
- One database change was made as this iteration's sole intended outcome: a single administrative
  "maintenance lock" record (covering the eleven repaired dates) was switched from active to inactive,
  now that the repair is confirmed complete. The record itself is kept (not deleted) as an audit trail.

---

## Known Limitations

- Two previously-known, deliberately out-of-scope gaps remain exactly as before: two specific, narrow
  situations (both requiring an unusual manual URL request) that, in theory, could still recreate stale
  data if someone hit them WHILE a future maintenance lock were active. Neither is reachable under normal
  use, and both are explicitly scheduled for a future hardening pass — not part of this repair.
- While double-checking related work, ten existing automated tests (unrelated to anything in this
  iteration) were found already failing before this iteration started. They involve some background
  "warm-up" calculations after a data import, not anything a user would see. Confirmed these failures
  exist independent of this iteration's changes; logged for a future cleanup, not fixed here (outside this
  iteration's assigned scope).
- The app itself (backend and frontend) was deliberately kept off for the entire iteration, per the
  repair's own safety rules — this was a database-only verification pass. A person now needs to decide
  when to next start the app normally; that step is intentionally left to a human, not automated here.
