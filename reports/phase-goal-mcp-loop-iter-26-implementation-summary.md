# Phase goal-mcp-loop-iter-26 — Implementation Summary

**Phase:** goal-mcp-loop-iter-26
**Date:** 2026-07-10 (updated after the audit FAIL — memory/VSZ fix-mode pass)
**Written by:** developer

---

## Features Implemented

- **Faster data jobs on the deep (30-year) basis ("item F")**: the Backfill and warm-up jobs now compute
  each day's scores from a bounded, recent slice of each stock's price history (the most recent ~320
  trading days) instead of feeding the entire multi-decade history into the scoring math every time. Every
  displayed score, ranking, and pattern flag is unchanged — this only removes wasted computation on price
  history that no indicator actually reads.
- **Faster realized-return backfill inside warm-up**: the step that records "what actually happened" after
  each historical scan (the realized forward returns) reuses the same in-memory price data the scan step
  already loaded, instead of re-reading it from the database one query at a time.
- **Lower memory churn in the realized-return step (this fix-mode pass)**: those same forward-return
  lookups used to build large temporary copies of a stock's price history and throw most of them away.
  They now read only the values they actually need. The numbers produced are byte-for-byte identical; only
  the wasted temporary memory is removed.
- **Automated correctness safety net**: dedicated tests prove, over real historical dates and the full
  stock pool, that scores and forward-return values computed the new way are byte-for-byte identical to
  the old way.

---

## Changed Behavior

- **Backfill / warm-up scoring**: previously fed a stock's entire stored price history (thousands of
  trading days) into every indicator; now feeds the bounded recent window. Output unchanged.
- **Backfill / warm-up realized-return step**: previously allocated (and largely discarded) big temporary
  copies of price history per stock per date; now allocates only what it uses. Output unchanged.

No user-visible screen, number, or control changed in this iteration.

---

## Backend-Only Items

- All changes are internal to the scoring/price-cache engine (`config.yaml`, `apps/backend/app/config.py`,
  `apps/backend/app/engine/scoring.py`, `apps/backend/app/engine/warmup.py`,
  `apps/backend/app/engine/prices.py`). No API, endpoint, or UI surface changed.

---

## Incomplete Items — READ THIS FIRST

- **The full-universe rebuild still has an unresolved memory crash. This iteration is NOT done.** During
  the audit, running the `/data` → "Rebuild snapshots for current universe" job (the full 322-date,
  full-universe backfill) exhausted the backend's **virtual-memory** ceiling (6144 MB) and crashed the
  whole backend. This fix-mode pass removed the extra memory churn that *this iteration* added to that
  job's realized-return step (and proved it changes no output), but the crash itself happens in a
  **different, pre-existing part of the job** — the market-regime computation plus the up-front load of the
  entire 30-year price universe into memory — which was not built or modified by this iteration and was
  not in scope to re-engineer here. The auditor explicitly recommended that root-cause fix be handled as
  its own dedicated "memory-hardening" iteration. **Until that lands, expect the full-universe rebuild to
  remain at risk of crashing.**
- **Live full-scale crash reproduction not run to completion**: reproducing the exact failure means
  running the entire multi-hour full-universe rebuild. Instead, this pass measured the memory effect of
  its own fix directly at the same full-universe data shape (see Known Limitations). No "crash fixed"
  claim is made.

---

## Config and Environment Changes

- **This fix-mode pass**: none.
- **Earlier in the iteration**: `indicators.max_lookback_bars` was added to `config.yaml` (committed value
  `320`) — it bounds how much recent price history the scoring math reads. It does not change any displayed
  value.

---

## Known Limitations

- **Memory measurement — the honest result.** On the committed 30-year database (3,293,160 bars, 590
  symbols) under the real production ceiling (`ulimit -v` 6144 MB), the realized-return step was measured
  at the full-universe shape: full universe loaded into cache (peak virtual memory 1,365 MB), then 216,530
  forward-return lookups. Peak virtual memory stayed at 1,365 MB with both the new and the old code —
  because in isolation each temporary copy is freed immediately and its memory reused. So the fix is a
  real, provably output-identical reduction of wasted allocation, but it is **not, by itself, the cure for
  the crash**; the crash is driven by the pre-existing whole-universe load + regime computation.
- **Correctness proven, not assumed.** Output-identity was checked three ways: five targeted cache/boundary
  unit tests pass; a 3,000-sample old-vs-new comparison on the real 30-year database found 0 differences;
  and the scoring code path was not touched by this pass, so the primary scoring byte-identity test's
  result cannot change.
- **Full regression suite not run in-pass** (~10+ hours at the 30-year data scale, per standing project
  guidance) — that is the separate full-suite lane's job.
- **Journey status.** Because the root-cause crash remains open, target journey J-16 ("data jobs fast +
  honest") should not be treated as passing on the full-universe rebuild until the separate
  memory-hardening iteration lands.
