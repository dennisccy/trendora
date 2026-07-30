# goal-ops-hardening-iter-37 — Implementation Summary

**Phase:** goal-ops-hardening-iter-37
**Date:** 2026-07-30
**Written by:** developer

---

## Features Implemented

- **None — this is a backend correctness/resilience fix, not a new capability.** Multi-date historical
  backfills (importing several days of price history in one request) now load the full price history
  table from disk only ONCE for the whole request instead of up to twice — the job runs faster and uses
  less peak memory, but nothing new appears on screen and no page behaves differently.

---

## Changed Behavior

- **Multi-date backfill jobs are faster and use less peak memory.** Previously, backfilling several
  historical days in one request loaded the entire price-history table from the database twice: once
  while computing the day-by-day snapshots, and again afterward while updating the coverage/availability
  summary shown on the Data page. Now it is loaded once and shared between those two steps. The numbers
  shown on every page (coverage stats, backfill summaries, backtest evidence) are unchanged — this only
  changes how the data is fetched internally, never what is computed or displayed.
- **The backend now proves, with a live measurement, that it never freezes or crashes while warming up
  backtest evidence for the whole history.** A full run of that warm-up (all five configured time
  horizons) was measured live: it completed in about 70 seconds, the "is the backend alive" health check
  kept responding instantly and correctly the entire time, and memory use stayed flat with well over half
  the configured ceiling still free.

---

## Backend-Only Items

- None — this iteration touches only internal backend orchestration, with no new capability to wire to
  the UI.

---

## Incomplete Items

- None from this iteration's plan.
- One live measurement (the "does a previously-computed backtest result still load correctly right after
  a simulated out-of-memory event" check, on a disposable throwaway test database) did not reproduce
  cleanly the way a similar check did in a prior iteration, because this test database's own automatic
  startup routine created a few extra historical snapshots that made the specific cached value being
  checked go stale before the check ran — a timing quirk of the disposable test setup, not the real
  product database, and not a defect in this iteration's fix. The same "backend survives and keeps
  answering" guarantee was still proven using two other checks (the health endpoint, and the job-status
  endpoint) that both worked correctly throughout. See the developer handoff for full detail.

---

## Config and Environment Changes

- None. No new environment variables, no config schema changes, no database migration.

---

## Known Limitations

- Two OTHER, unrelated read requests were found to fail under an artificially very tight memory ceiling
  during this iteration's stress-test (a request for the full data-coverage overview page, and a direct
  request for one specific historical date's backtest evidence). Neither is part of what this iteration
  changed, and neither happens under the real memory ceiling the product actually runs with — this was
  only visible because the test intentionally set an extremely low ceiling to try to trigger a failure.
  It is recorded as a finding for a future iteration to look at, not something broken by this change.
- Everything else this iteration was scoped to leave alone (a handful of small known cosmetic/labeling
  issues carried from earlier iterations) remains unchanged, as intended.
