# goal-market-compass-iter-17 — Implementation Summary

**Phase:** goal-market-compass-iter-17
**Date:** 2026-08-25
**Written by:** developer

---

## Features Implemented

- **Safer boot-time incident check**: the code that decides "should the server refuse to write today's
  scanner snapshot because it falls inside an active maintenance quarantine" no longer reads the entire
  maintenance-boundary table on every boot. It now reads only the handful of rows that could possibly
  matter, with a hard cap, and it refuses (fails safe) rather than crashing if that cap is ever exceeded or
  the table doesn't exist yet.
- **A way to turn the incident quarantine on**: a new command-line tool that registers/activates the J-11
  incident boundary — the same one iteration 16 built the checking logic for. Running it twice in a row is
  safe (it doesn't create a duplicate). It only ever touches the one small table it's meant to; nothing
  else in the database changes.
- **A way to turn the incident quarantine off**: a companion command-line tool that deactivates one named
  boundary by name, leaving every other maintenance boundary untouched. It never deletes the historical
  record — it marks it inactive so there's still an audit trail.
- **Live-database proof, not just fixture proof**: a small tool that connects to the real (production)
  database in a strictly read-only mode and confirms, using the exact same code the server would use, that
  (a) the incident-quarantine table genuinely doesn't exist there yet, and (b) the checking logic still
  behaves safely and correctly even so — returning "not blocked" cleanly instead of crashing.
- **A correction to a stale readiness reading**: last iteration's calculation of whether it's safe to
  proceed to the next stage of data-recovery work (Stage D) was pairing two numbers that didn't belong
  together, making the result look worse than it actually was. This iteration re-runs that same
  calculation with the two numbers correctly matched, and the honest result is now the more favorable one
  ("AVB-A" instead of "AVB-B") — though the practical outcome for readiness ("YES") does not change.

## Changed Behavior

- **The maintenance-boundary safety check**: previously it loaded every row in the maintenance-boundary
  table on every server boot, with no upper bound — a theoretical scaling risk if that table ever grew
  large. Now it loads only the rows that could actually affect the day's decision, with a hard cap, and it
  is explicitly tested against the case where the table doesn't exist at all (today's actual situation on
  the real database) — it now handles that cleanly instead of the possibility of an unhandled error.

## Backend-Only Items

- The two new command-line tools (turn the quarantine on / turn it off) are complete and tested, but this
  iteration does not run them against the real database — the table they would write to doesn't exist
  there yet, and creating it requires a separate owner decision that has not been made. There is no UI for
  any of this; it was never meant to have one — it is an internal safety mechanism, not a feature customers
  see.

## Incomplete Items

- **Actually arming the live safety check**: this remains blocked. The owner's instructions were explicit
  that creating the required database table on the real (production) database is a separate decision, not
  yet made, and this iteration correctly stopped rather than creating it. The reason to care: until that
  table exists and the safety check is armed, the safety net this whole feature exists to provide is not
  yet actively protecting anything on the real database — it protects correctly whenever it's tested on a
  disposable copy, but there is currently nothing for it to protect against on the real one because that
  table has never been created there.
- **Stage D of the data-recovery work** (regenerating 11 days of scanner data affected by an earlier
  incident) remains explicitly not authorized and was not attempted or planned in detail this iteration,
  consistent with every iteration since the incident was discovered.

## Config and Environment Changes

None. No `config.yaml` entries were added or changed. One new internal safety-limit number ("no more than
100 maintenance-boundary rows will be read at once") was added directly in the relevant code file rather
than the shared configuration file — this matches how five earlier pieces of this same recovery work have
handled similarly narrow, non-business-facing numbers, and was a deliberate choice, not an oversight.

## Known Limitations

- The two new command-line tools have only been tested against disposable, throwaway copies of the
  database — never the real one. This is intentional for this iteration (the owner explicitly did not
  authorize touching the real database's schema), but it does mean the "turn the quarantine on" tool's very
  first real-world use will be its first-ever run against production data.
- One pre-existing, unrelated test failure was found in the codebase (in three files this iteration never
  touched) and is reported honestly rather than silently ignored — it existed before this iteration started
  and was left alone, since fixing it was outside this iteration's assigned scope.
