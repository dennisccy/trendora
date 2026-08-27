# Iteration 22 — Implementation Summary

**Phase:** goal-market-compass-iter-22
**Date:** 2026-08-27
**Written by:** developer

---

## Update (fix pass, same date): a bug in the verification logic itself, now corrected

This iteration was first submitted, then **failed code review** for a serious but narrow defect: one of the
twelve automated checks that were supposed to certify the repair was written so that it could never say
"no" — it would have printed a clean bill of health even if the underlying fix had silently done nothing.
That is now fixed (details below, under "Changed Behavior"). Two important, separate facts:

1. **The database itself was never wrong.** Independent double-checking (by the code reviewer and by the
   automation pump, separately) confirmed the actual repair to the database genuinely worked — the one
   piece of stale cached data really was removed. This was a "the exam grader had a bug" problem, not a
   "the answer was wrong" problem.
2. **This fix pass changed code and automated tests only.** It did not re-run the repair against the real
   database, and did not need to — the already-completed repair's real-world result stands, it just was not
   being genuinely double-checked by the automated gate that declared it done. That gate now genuinely
   double-checks it, including for any future incident of this kind.

## Features Implemented

- **J-11 incident closure (Stage G — the final verification gate)**: this iteration ran the last of a
  five-stage database repair (Stages C through G) that fixed the damage left behind by an old testing
  mistake (iteration 5's destructive drill, back in mid-August). Every one of the twelve required checks
  passed — the raw price data, the eleven rebuilt daily snapshots, the derived statistics, the historical
  "next-session" reports, and every cache all came back clean and consistent. The incident is now formally
  closed: **`J-11 INCIDENT STATUS: FULLY REPAIRED`**. (See the update above: one of those twelve checks was
  initially unable to genuinely fail; it has since been corrected to a real check, and — separately
  confirmed — still reports the repair as genuinely correct.)
- **One small safety fix**: closed a gap where, once the app is running normally again, a single page visit
  to one of the eleven previously-damaged dates could have quietly re-created a stale cache entry the
  repair had just cleared out. That path is now blocked while the repair's safety lock is active, using
  the exact same safety mechanism already protecting two other parts of the system.
- **A genuine bug found and fixed during verification**: one small piece of cached data (part of the
  "which stocks are actively tracked" history) turned out to still hold an outdated value for one of the
  eleven repaired dates. The verification step caught this, discarded the outdated cache entry, and the
  system will recompute it correctly the next time it's needed. Nothing else was affected. (This fix pass
  hardened the check that certifies this specific repair actually took effect — see "Changed Behavior".)

---

## Changed Behavior

- **Data page (`/data`) caching**: when someone visits a historical date's coverage numbers, the system
  now double-checks that date isn't still under an active maintenance lock before caching fresh numbers for
  it. For every date NOT under such a lock (i.e., everything, once the repair's lock is lifted), behavior
  is completely unchanged. This only matters while the (now-lifted) repair lock is active.
- **The repair-verification "grader" (fix pass)**: one of the twelve automated checks used to certify this
  repair — the one confirming that a specific stale cache entry was actually removed — was written in a way
  that could only ever say "yes, that's handled," regardless of whether the removal actually happened. It
  has been rewritten so it genuinely checks: it now looks at the real, current state of that cache entry
  after the removal step runs, and only reports success if the entry is truly gone. The order of operations
  was also corrected — that check, and the actual removal step it verifies, now both run and finish *before*
  the tool decides the repair is complete and unlocks the database, instead of after (which would have been
  too late to matter). This only affects the internal repair-verification tool used for this one incident —
  nothing a regular user of the app would ever see or interact with.

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
- During the fix pass, one MORE pre-existing, unrelated automated test was found failing (a broad
  text-scanning check that flags any file mentioning the "next-session manifest" database table if that
  file also happens to contain any unrelated `.update(...)` call anywhere in it — a false-positive-prone
  check, not a real problem). Confirmed by temporarily setting this iteration's own files back to their
  pre-fix state and re-running the same test: it fails identically either way, and flags several OTHER
  files this iteration never touched. Logged for a future cleanup of that check's precision, not fixed here
  (outside this fix pass's assigned scope, and touches a file neither the review nor this iteration owns).
- The app itself (backend and frontend) was deliberately kept off for the entire iteration, per the
  repair's own safety rules — this was a database-only verification pass. A person now needs to decide
  when to next start the app normally; that step is intentionally left to a human, not automated here.
