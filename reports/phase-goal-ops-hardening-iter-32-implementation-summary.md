# Phase goal-ops-hardening-iter-32 — Implementation Summary

**Phase:** goal-ops-hardening-iter-32
**Date:** 2026-07-29
**Written by:** developer

---

## Features Implemented

- **No new user-facing feature.** This iteration is an internal reliability fix: it removes the last
  remaining "could crash the server" weak spot inside the calculation that powers the Backtest page's
  historical evidence. Nothing new is visible to a user — the numbers on screen are exactly the same as
  before, they're just produced by code that can no longer run the server out of memory while producing
  them.

---

## Changed Behavior

- **How the forward-return evidence is calculated internally, not what it shows.** Previously, computing
  the historical evidence for one lookback period built one temporary "note card" in memory for every
  single stock-pick-and-date pair ever scored — on the real dataset, roughly 800,000 note cards, all
  held in memory at once, for each of the 5 lookback periods the page can show. That was the exact cause
  of two earlier real crashes this project experienced. Now the calculation keeps only small running
  tallies (one small tally per pattern-bucket, per setup type, per market regime, per sector, per stock
  ticker) instead of the full pile of note cards — the running tallies produce mathematically identical
  results, verified by an automated test that compares the new calculation against the old one line-by-
  line across many scenarios.

---

## Backend-Only Items

- None. This iteration touches only internal calculation code (`compute_forward_aggregates`) — no new
  endpoint, no new database field, no new UI hook.

---

## Incomplete Items

- None from this iteration's own scope. Everything the plan asked for was completed: the memory-hungry
  calculation was restructured, all existing behavior was proven unchanged, and a real end-to-end test
  was run against the live, full-size database (see "Known Limitations" below for what this DOES prove
  and what remains for future work).

---

## Config and Environment Changes

- None. No new environment variable, no new config.yaml key, no database migration. The existing
  `walk_forward.forward_agg_run_chunk` setting (already added in a prior iteration) is reused as-is.

---

## Known Limitations

- **Live-scale verification result:** with the fix in place, running the affected calculation for all 5
  lookback periods against the real, full-history database (roughly 5 million data points on disk) twice
  in a row caused **zero out-of-memory errors** and **zero dip in server responsiveness** — the health
  check answered normally the whole time, every single time it was polled. The server's peak memory usage
  did not grow at all while the calculation ran; it stayed exactly at the level already reached during
  normal startup, with well over half the memory ceiling still unused as headroom.
- **What this does NOT cover:** three other previously-identified "could theoretically run out of memory
  under the right conditions" spots elsewhere in the codebase (the boot-time data warm-up, the price-data
  refresh step, and one leftover inefficiency in a different report) are unrelated to this iteration and
  were deliberately left untouched — they are each their own separate, already-tracked item for a future
  iteration to pick up one at a time, per this project's "one risky change at a time" rule.
- **A related decision, also deliberately deferred:** whether the frontend should be launched in
  "development" mode or "production" mode is a separate open question, unaffected by this iteration, and
  scoped to a future iteration as well.
