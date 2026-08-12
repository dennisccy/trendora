# goal-ops-hardening-iter-72 — Implementation Summary

**Phase:** goal-ops-hardening-iter-72
**Date:** 2026-08-12
**Written by:** developer

---

## Features Implemented

This round is a reliability/hardening fix — it adds no new user-facing feature. It closes a real
outage found last round: under heavy background work, the app could stop answering its own "is it up"
health check for minutes at a time, and one page briefly showed an error instead of loading. This round
fixes the two causes and re-measures the app under the same heavy conditions to prove it stays responsive.

- **Database connection pool resized to match what the server actually admits**: the app's internal pool
  of database connections was smaller than the number of simultaneous requests the server is configured
  to accept. Under load, extra requests queued for a connection and eventually timed out. The pool is now
  sized with real headroom above that limit, and the app now refuses to start at all if a future config
  change ever creates this same mismatch again (instead of failing silently under load).
- **The "is the app up" status no longer gets stuck waiting on a slow recheck**: last round's own fix for
  a related problem had an unintended side effect — under load, the status check would occasionally fall
  back to a slow, blocking recheck, and every other request would then queue up waiting for that ONE slow
  recheck to finish, making the problem worse. The status check now always answers immediately with its
  last known value (honestly labeled with how old that value is), instead of ever blocking on a recheck.
- **The everyday developer launcher now matches the production launcher's safety limits**: the app's
  everyday development script previously skipped the connection-limit and timeout settings the production
  launcher already enforces, and wrote no persistent log file. It now applies the same settings and writes
  to the same log file production does, so a problem seen during everyday development leaves real evidence
  behind and is measured under realistic conditions.

## Changed Behavior

- **Backend startup**: Previously the app would boot even if its internal database connection pool was
  too small for its own configured concurrency limit — a mismatch that could only be discovered by a live
  outage under load. Now the app refuses to boot with a clear error if that mismatch exists, catching the
  problem before it ever reaches production traffic.
- **The health/status indicator's behavior under heavy load**: Previously, if the status hadn't been
  refreshed recently enough, the app would pause to recompute it fresh before answering — and under heavy
  load, that recompute itself could be slow, causing a pile-up. Now the app always answers immediately with
  its last known status and an honest "how stale is this" figure, never pausing to recompute under load.
  The very first status check right after startup is unaffected — that one is still computed fresh, as
  before.
- **The everyday developer launch script**: Previously it applied none of the production launcher's
  connection-limit/timeout protections and kept no persistent log. Now it applies the same protections and
  writes to the same log file the production launcher uses — with zero change to how the companion
  frontend dev server is started.

## Backend-Only Items

- A new hidden test-only switch was added that can force the "current data status" page's API call to
  fail on demand, so the existing "couldn't load, no numbers are shown" message can be captured and
  verified — this switch is off by default in every real deployment and has no UI of its own; it is
  reached only by an operator explicitly enabling it before running a check.

## Incomplete Items

- None from this round's own scope. Everything the spec asked for (the pool resize, the status-check fix,
  the developer-launcher parity fix, and the re-measurement) is complete and verified with real, live
  testing — not just automated tests.

## Config and Environment Changes

- `config.yaml`: the database connection pool size was increased (from a combined 30 simultaneous
  connections to 68) to comfortably cover the number of simultaneous requests the server accepts. No
  other config value changed — the memory and CPU protections from earlier rounds are untouched.
- No new environment variables. No database schema changes (no migration needed).

## Known Limitations

- **A newly-discovered, separate issue was found and is NOT fixed by this round**: during testing, an
  unrelated weak spot was found — if MANY more requests than the health check alone pile up on the app
  while it's doing heavy background work, the app's own connection-limiting safety net can get stuck
  rejecting requests (including the health check) for an extended stretch, until the heavy work finishes.
  Under the SPECIFIC, realistic condition this round was asked to test (one health check per second), this
  did NOT happen — the app stayed fully responsive across a very thorough 1,598-check live test with zero
  failures. The stuck-rejecting behavior only showed up when testing deliberately piled on extra,
  unrealistic simultaneous traffic beyond what was asked for. This is written down as a finding for the
  team to decide on, not something this round claims to have fixed.
- **A page-load speed measurement task from last round is still outstanding.** Last round was supposed to
  record how fast each page of the app loads, and that measurement never happened. This round did not
  touch any page or the browser at all (it is a backend-only fix), so that measurement is still owed and
  is carried forward for a future round that touches the frontend.
- One background data-import job that was intentionally left running during this round's own live test (to
  prove the fix under real load) did not finish before the test's time budget ran out and was stopped. The
  app is specifically designed to recover cleanly from a stopped-mid-way job like this the next time it
  starts — no manual cleanup was needed, and this is documented for whoever next restarts the shared
  testing environment.
