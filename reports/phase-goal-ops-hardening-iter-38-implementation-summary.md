# Phase goal-ops-hardening-iter-38 — Implementation Summary

**Phase:** goal-ops-hardening-iter-38
**Date:** 2026-07-30
**Written by:** developer

---

## Features Implemented

This iteration is a verification/measurement iteration — it does not add a new user-facing feature. Its
purpose is to finish PROVING that a fix shipped last iteration actually works the way it's supposed to, and
to close a handful of small documentation/test gaps a previous review flagged.

- **Proof that the backend's "hold one price-data cache in memory across a data-import job" optimization is
  genuinely exercised, not just present in the code but never actually used.** Last iteration's fix (share
  one in-memory cache across the several steps of an import job instead of loading the same data twice) was
  tested, but through paths that turned out to accidentally bypass the very thing being tested — like
  testing a car's cruise control by pushing the car by hand. This iteration built a proper test that
  actually exercises the real mechanism, confirmed it with a log line that proves which code path ran, and
  measured what it does to the backend's memory use with the feature ON versus OFF.
- **A one-time backend data-import re-run against the real production-sized database**, triggered the
  correct way (through a real data-import job, not a side door), to prove the specific promise this session
  has been building toward: heavy background computation never makes the app unresponsive. During the
  ~5.5-minute import, the app's health-check endpoint was polled once per second the entire time and
  answered every single time.

## Changed Behavior

- None visible to a user. The only behavioral change is a new optional environment-variable switch
  (`TRENDORA_FORCE_LEGACY_BAR_CACHE`) that exists purely for this iteration's own measurement — it is never
  set in normal operation and does not affect any user-visible output.

## Backend-Only Items

- The measurement/comparison tooling built this iteration (`runs/goal-ops-hardening-iter-38/mem-drill/`,
  `runs/goal-ops-hardening-iter-38/j07-warm/`) is developer/operator tooling, not a product feature — no UI
  wiring is expected or was built.

## Incomplete Items

None from this iteration's own scope. All items in the execution plan were completed: the widened test
fixture, the two-arm memory comparison, the real-database re-trigger with concurrent health polling, the two
new/strengthened automated tests, the documentation fix, the stale-figure correction, and the wall-clock
measurement.

Two items outside this iteration's assigned scope remain open (unchanged, not regressed, both explicitly
deferred by the plan): a slow first-load issue on one research page (queued next), and an owner decision
about a strict health-check speed target that occasionally gets missed under heavy background load.

## Config and Environment Changes

- `TRENDORA_FORCE_LEGACY_BAR_CACHE` — TEST-ONLY environment variable. When set to any truthy value, forces
  the backend to skip its memory-saving optimization for one data-import job (used only by this iteration's
  own measurement drill). Default: unset (normal behavior, unaffected).
- No database schema changes, no new dependencies, no changes to how the app is started or configured for
  normal operation.

## Known Limitations

- The memory comparison's headline finding is more nuanced than a simple "yes it helps" or "no it doesn't":
  the memory-saving feature makes a data-import job run noticeably faster (roughly 2.5-4x, measured across
  three separate trials), but its effect on the PEAK amount of memory used during that job was close to a
  wash in the main comparison (within about 4%). A separate trial under a tighter memory limit did show the
  OLD (pre-fix) behavior crashing where the NEW behavior did not — but because that crash happened in a
  piece of code shared by both the old and new behavior, it's reported as a real observation rather than
  proof the fix is what prevented it.
- One measurement run hit an operator mistake (a process-tracking slip while launching a comparison backend)
  that cost some of the very earliest data points in that run; the affected numbers are disclosed as such in
  `reports/perf-budgets.md` rather than silently patched over, and the final headline numbers used the
  portion of the measurement that was captured correctly.
- The full-database re-trigger took about 5.5 minutes — a bit longer than the roughly-5-minute expectation
  set by the previous iteration's similar test, due to an expected (not new) cost: any new data snapshot
  invalidates a separate cache that then has to rebuild itself by scanning ~1,880 stored dates. This is not
  a new problem introduced this iteration; it is disclosed as a measured fact for whoever tackles that cache
  next.
