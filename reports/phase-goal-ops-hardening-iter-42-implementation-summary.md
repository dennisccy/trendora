# goal-ops-hardening-iter-42 — Implementation Summary

**Phase:** goal-ops-hardening-iter-42
**Date:** 2026-07-31
**Written by:** developer

---

## Features Implemented

This is a backend/tooling-only iteration — no new user-facing capability, no UI change. Two
infrastructure/reliability closures:

- **Target-journey verification lane**: the automated test pipeline now treats an iteration's own
  "journeys this iteration exists to verify" (`Target journeys:`) with the same fresh-evidence
  guarantee it already gave to "journeys that must stay passing" (`Required-still-passing
  journeys:`). Previously, a spec could name a target journey and the pipeline would still report a
  clean "all tests passed" headline even if that specific journey was never actually checked at all
  — the prior iteration shipped exactly that outcome. Now, a missing or skipped-only target journey
  forces the run to report "blocked, not verified" instead of a false clean pass.
- **A fifth attempt at bounding a known memory hot spot** in the data engine's bar-price cache
  (`_BarCache.prefill`): the load now skips loading price history for ~43 index/sector benchmark
  symbols (SPY, the VIX, sector ETFs) that are never part of the tradeable candidate universe, only
  loading them on the rare occasions they're actually needed. This produces a real, measured but
  modest memory reduction (~2.5%), not a fundamental fix — documented honestly below.
- **A defensive data-shape fix**: if a future data widening ever introduces a missing (NULL) price
  value, the price cache will now record it as an honest "not available" marker instead of crashing.
  This cannot happen against today's database schema; it is forward-looking hardening only.
- **A frontend-restart reliability fix**: two internal retry paths in the automated test pipeline
  (used when the pipeline restarts the app mid-run and then immediately retries a check) now give the
  restarting frontend a fair, bounded chance to finish starting up before concluding it's
  unreachable — closing a gap that previously voided an entire test run's evidence on one premature
  timeout.

---

## Changed Behavior

- **Automated pipeline test-plan generation**: a backend-only iteration spec that names journeys on
  either `Required-still-passing journeys:` or `Target journeys:` now always gets a regression test
  row for each one. Previously only the "required" line was honored.
- **Automated pipeline result merging**: a merged test-results file can no longer read as a clean
  "all passed" or "all skipped" summary if any journey named as this iteration's own target has zero
  test rows or only a "not executed" row. It will instead read "blocked" with the specific missing
  journey named.
- **Data engine bar-price loading**: for the same real workloads (nightly backfills, coverage
  refreshes), the price cache now loads a smaller set of symbols up front (the tradeable pool only,
  not the full priced-symbol table) — everything else about what data is served is unchanged
  (byte-identical values, same load-once-per-job guarantee).

---

## Backend-Only Items

- The target-journey verification-gap fix and the frontend-restart reliability fix are both
  automation/pipeline-tooling changes with no product-facing surface at all — there is nothing for an
  end user or operator to see in the running application.
- The `_BarCache.prefill` bound and NULL-tolerance changes are internal to the data engine's price
  cache — no API response shape, no page, and no displayed value changes.

---

## Incomplete Items

- **The memory bound on `_BarCache.prefill` is real but only modest** (measured ~2.5% peak-memory
  reduction, ~5.9% fewer rows loaded). It is NOT a fundamental fix — the cache still loads roughly
  93% of the price table's distinct symbols for every real job. A genuinely different-order-of-
  magnitude bound would require redesigning how the callers ask for data (a bigger, out-of-scope
  change), not just filtering the existing query further. This is disclosed honestly, per this
  iteration's own instructions, rather than claimed as resolved.
- **A newly discovered, previously-unmeasured performance regression**: while measuring the price
  cache's read speed (a task this iteration was specifically asked to do, since it was never
  measured before), a substantial slowdown was found in a change from *last* iteration — reading
  price history through the new, more memory-efficient storage format is roughly 70-80× slower per
  call than the older format it replaced. In absolute terms this is small for short reads, but can
  add up to real time on longer historical reads used throughout scoring and backfills. This was NOT
  fixed in this iteration — it was outside the authorized scope (this iteration's job was to bound
  memory further and MEASURE the read-speed impact, not redesign the storage format) — but it is
  flagged prominently for the next reviewer/owner decision.

---

## Config and Environment Changes

None. No new environment variables, config keys, or migrations.

---

## Known Limitations

- The two owner-decision items already deferred by prior iterations (the health-check response-time
  budget, and whether the frontend launch script should apply host-resource caps) remain untouched,
  as directed by this iteration's own scope.
- The price-cache read-speed regression noted above needs a decision from the team: is the ~70-80×
  slower per-call read speed (introduced by last iteration's memory-saving change, only measured for
  the first time this iteration) an acceptable trade-off, or does it need its own fix in a future
  iteration?
- A pre-existing automated test (unrelated to this iteration's own plan) needed a small fix: this
  iteration's price-cache change exposed a flaw in how that test counted memory-loading events under
  concurrent access. The test's counting method was corrected (not the underlying feature) so it no
  longer produces intermittent false failures.
