# Phase goal-market-compass-iter-27 — Implementation Summary

**Phase:** goal-market-compass-iter-27
**Date:** 2026-08-28
**Written by:** developer

---

## Features Implemented

- **Honest "data missing" state for the Today page's manifest strip**: when a past decision snapshot
  (the "next-session manifest" frozen at a prior close) has its underlying scanner data removed — for
  example during a data-repair or cleanup operation — the page now honestly shows "Basis: unavailable"
  instead of silently rebuilding that scanner data behind the scenes and showing "Basis: rebuilt" (or
  "available") as if nothing had happened. This was an already-built, already-tested display state that
  the system could never actually reach in real use before this fix — it only fixes WHEN that honest state
  becomes visible, not what it looks like.

---

## Changed Behavior

- **`GET /api/compass` (the endpoint behind the Today page's manifest strip)**: Previously, this endpoint
  always regenerated the underlying scanner data for a date if it happened to be missing, before checking
  whether a frozen decision snapshot already existed — meaning a missing data problem was silently
  papered over. Now, it checks for an existing frozen snapshot FIRST, and only regenerates missing scanner
  data when no snapshot exists yet for that date. This means: for a date that already has a frozen
  snapshot, the system never quietly re-creates missing underlying data anymore — it reports the honest
  state instead. Nothing about how manifests are frozen, exported, or numbered changed; nothing about how
  other pages (Stocks, Sectors, Themes, dashboards) work changed — they still self-heal missing data
  exactly as before.

---

## Backend-Only Items

None — no new UI, no new endpoint. This iteration only changed the internal read order inside an existing,
already-shipped endpoint so an existing, already-shipped display state ("Basis: unavailable") becomes
reachable.

---

## Incomplete Items

None from this iteration's scope. All items in the phase spec's checklist were completed and verified.

---

## Config and Environment Changes

None. No new environment variables, config keys, or schema changes.

---

## Known Limitations

- This fix was verified two ways: (1) against a small, hand-built test database where a scanner-data
  removal was deliberately simulated — proving the honest "unavailable" state, the recovery back to
  "available"/"rebuilt", and that no automatic data regeneration fires; and (2) against the real production
  database, where two existing, already-frozen decision snapshots were read twice each to prove nothing
  changed (zero rows added or altered anywhere) — but no scanner data was actually removed from the real
  production database during this verification, since that kind of destructive test is intentionally
  reserved for the isolated test database only, per this project's data-safety rules. The "unavailable"
  state itself was therefore proven only against the test database, not screenshotted live in production
  — this matches how the equivalent prior fix (last cycle) was verified and accepted.
- One pre-existing, unrelated test failure was noticed while running checks (a code-style rule about
  numeric literals in three files unrelated to this change). It was not introduced by this work and was
  left untouched, as fixing it was outside this iteration's scope.
