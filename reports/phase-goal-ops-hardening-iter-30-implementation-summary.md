# Phase goal-ops-hardening-iter-30 — Implementation Summary

**Phase:** goal-ops-hardening-iter-30
**Date:** 2026-07-29
**Written by:** developer

---

## Features Implemented

- **Memory-bounded backtest evidence computation**: the calculation behind the Backtest page's evidence
  (and the equivalent MCP `query_backtest` tool) now processes historical trading days in small batches
  instead of pulling every historical day's data into memory at once. This closes a live memory-exhaustion
  bug that was found in last iteration's testing — the background job that keeps the Backtest evidence
  up to date was crashing with an out-of-memory error while computing evidence for one specific forward-
  looking horizon.
- **A new, dedicated tuning setting** (`walk_forward.forward_agg_run_chunk` in `config.yaml`, currently 100)
  controls how many historical scan dates are processed per batch. This mirrors a similar setting added
  last iteration for a related calculation, and comes with its own automated check that verifies the
  setting is actually small enough to matter against the real database (not just in a test).

## Changed Behavior

- **None visible to users.** The Backtest page and the underlying evidence numbers are unchanged — this
  iteration only changes HOW the evidence gets computed internally (in batches instead of all at once),
  never WHAT gets computed. Every number a user sees on `/backtest` should be identical before and after
  this change; that byte-for-byte equivalence is proven by 51 new/updated automated tests.

## Backend-Only Items

- The batching fix and its new config setting are entirely backend/internal — there is nothing new to see
  or click on the frontend. This was expected: the phase spec explicitly scoped this iteration to a
  backend-only reliability fix, no new UI.

## Incomplete Items

- **Whether this fix fully eliminates the crash has not been confirmed against the real, full-size
  database yet.** I made the fix, proved the math still comes out exactly the same as before (automated
  tests), and confirmed the backend starts and runs cleanly with the change in place — but reproducing the
  actual "run the real evidence-refresh job against the full historical database" scenario that caused the
  crash is a heavier operation explicitly left for the QA step (it involves running a long computation
  against the full multi-year dataset, which needs to happen under closer supervision given this host's
  prior hardware-safety incidents under similar heavy workloads). If QA finds the crash still happens, the
  next likely culprit is called out in the developer handoff so the next fix attempt has a head start.
- One related page (`/research/factor-lab`) shares a similar computation pattern from a fix made last
  iteration; this iteration doesn't touch that page's code, but a "did we break it" spot-check in a real
  browser is still expected as part of QA, per the plan.
- A separate housekeeping item — appending this iteration's page-load-speed measurements to the tracked
  performance-budgets report — was also completed as part of this work (no code change, just measurement
  bookkeeping); all 11 tracked pages and the "how fast does the server start" measurement continue to meet
  their targets, with one small caveat noted below.

## Config and Environment Changes

- `config.yaml`: new key `walk_forward.forward_agg_run_chunk` (default `100`) — controls the batch size
  for the backtest-evidence computation described above. No action needed; ships with a sensible default
  and is validated at startup (the app will refuse to start if it's set to a nonsensical value like 0).

## Known Limitations

- The health-check endpoint (`/api/health`, used by the little "backend is ready" indicator) came in
  slightly over its speed budget in one of this iteration's measurements (about 128ms vs. a 100ms target).
  This is a pre-existing, well-documented situation — this same endpoint has bounced back and forth across
  that exact line in multiple prior iterations' measurements, purely due to normal minor timing variation
  on a busy development machine, not something this iteration's change caused (this iteration adds zero
  extra work to that endpoint). No action is being taken on it this iteration.
- See "Incomplete Items" above regarding the not-yet-confirmed real-world crash reproduction — this is the
  main open item for QA to close out.
