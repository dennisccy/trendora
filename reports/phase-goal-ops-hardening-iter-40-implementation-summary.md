# goal-ops-hardening-iter-40 — Implementation Summary

**Phase:** goal-ops-hardening-iter-40
**Date:** 2026-07-31
**Written by:** developer

---

## Features Implemented

- **No new user-facing capability this iteration.** This was a correctness/hardening fix on
  already-shipped behavior (J-07 "heavy aggregates never take the service down" and J-04's checkpoint
  honesty) plus two tooling-only corrections. There is no new screen, button, or displayed field for an
  operator to discover.

---

## Changed Behavior

- **The "Missing-data diagnostic" behind `GET /api/data`'s coverage panel and the ingest-time coverage
  refresh no longer risks exhausting server memory on a large dataset.** Previously, one internal query
  (checking which trading days each stock actually has price data for) pulled its full result into memory
  before processing it — on the full 30-year, 590-symbol dataset that is roughly 3.3 million rows held at
  once. It now processes that same data in small batches instead. The displayed coverage numbers are
  unchanged — same data, same categories (no-history / thin history / gaps), same counts — only the
  internal fetching method changed. A live drill re-running the exact scenario that previously caused a
  multi-minute unresponsive freeze showed no freeze this time, with the backend answering health checks
  normally throughout.
- **A backfill job interrupted mid-run (e.g. a crash or forced restart) now shows a much more accurate
  "how far did it get" figure after restart.** Previously, a fast job could crash and show almost no
  progress in its history record even if it had actually completed nearly all of its work (observed
  previously: 18 of 18 dates truly done, but only a handful shown as done after restart). A live drill
  this iteration deliberately killed a running job partway through (12 of 25 dates truly complete,
  confirmed independently) and restarted the backend — the recovered history record showed 11 of 25, off
  by only one date instead of an order of magnitude. This makes the `/data` page's Run History panel a
  more trustworthy record of what actually happened when something goes wrong mid-job.

---

## Backend-Only Items

- The streaming fix and the checkpoint-timing fix are both internal engine changes with no new API surface
  and no new field for the frontend to read — the existing `/data` page and `/api/data` payload already
  display the affected values (coverage diagnostic, Run History `dates_done`) unchanged in shape.

---

## Incomplete Items

- None from this iteration's scope. All seven in-scope items (the diagnostic-query fix, the checkpoint-
  cadence fix, the post-fix wedge re-check drill, the checkpoint-honesty live drill, the perf-budgets.md
  correction, and the QA-tooling BLOCKED-verdict fix) were completed with tests and/or live evidence.

---

## Config and Environment Changes

- None. No new environment variables, no config.yaml schema change, no database migration. The
  checkpoint-cadence tightening (10.0 s → 1.0 s) is a code-level constant change, not a new config field
  (a deliberate, minimal-footprint choice — see the dev handoff's reasoning).

---

## Known Limitations

- The checkpoint-honesty fix bounds staleness by wall-clock time (now roughly 1 second instead of 10), not
  by an exact per-date guarantee — an extremely fast future job could in principle still show more than a
  1-date gap if per-date processing ever becomes faster than about 100ms. Not expected to matter at
  today's processing speed (observed ~120-140ms/date in the fastest measured burst), and proven safe by a
  live drill plus a dedicated unit test, but flagged for awareness.
- One of the two live memory-pressure drill attempts this iteration was inconclusive due to a test-setup
  timing issue on the developer's own end (not a product bug) — the corrected, clean re-run is the
  authoritative result and showed no freeze. Full detail in the dev handoff's "Known Issues."
- No visible product surface changed this iteration — an operator opening `/data` after this deploy will
  see exactly the same page, with more resilient behavior underneath during heavy operations and crash
  recovery.
