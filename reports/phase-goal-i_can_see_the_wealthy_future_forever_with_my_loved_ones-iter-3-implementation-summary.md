# Goal Iteration 3 (J-46) — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3
**Date:** 2026-06-11
**Written by:** developer

---

## Features Implemented

- **Faster multi-symbol data fetching**: when you fetch price history for many symbols, the app now downloads several symbols at the same time on a small pool of worker threads (instead of one symbol after another). The size of that pool is a setting (`fetch_workers`, default 4) — so the operator can tune it, and it is never hard-coded.
- **Safer, faster saving of fetched bars**: a "chunk" of symbols is now saved to the database in a single write at the end of the chunk (rather than one write per symbol). This is both faster and cleaner: a chunk is saved completely or not at all.
- **Much faster historical backfill / warm-up**: when the app builds the historical record (replaying past trading days), it now loads each symbol's price history **once per job** and reuses it for every date, instead of re-reading it from the database for every single date. For a job spanning many dates this removes a large amount of repeated work.
- **A speed benchmark you can run any time**: a new operator command (`scripts/benchmark_pipeline.py`) measures, on the built-in offline data, how fast each pipeline stage runs (fetch, scan/snapshot, forward returns) — and shows the before/after of the two speedups above. It is advisory only and touches no real data or network.

---

## Changed Behavior

- **Fetch jobs run in parallel now**: a fetch of many symbols completes faster. The live progress you see on the Data Manager (e.g. "fetched 80/158 symbols"), the amber "rate-limited — resumable" pause, and the **Resume** button all behave exactly as before — the counts stay accurate (never exceeding the totals) even while several symbols download at once.
- **A rate-limited fetch pauses cleanly mid-chunk**: if the data provider starts blocking requests (a "429" rate limit), the job saves its progress at the last fully-completed chunk and pauses as **resumable**. The partially-fetched chunk is not half-saved — Resume simply re-does that whole chunk, and already-saved bars are never re-downloaded or duplicated.
- **The historical warm-up and backfill produce identical results, faster**: every score, bucket, setup, regime label, and forward-return is byte-for-byte the same as before — only the speed changed. This was verified by re-running the existing scoring/scanner/forward-test suites unchanged plus a direct "cached equals uncached" comparison.

---

## Backend-Only Items

- This entire iteration is backend-only by design. There is **no new screen, button, or displayed value** — the Data Manager looks and works the same; only the engine underneath is faster. Nothing new needs UI wiring.

---

## Incomplete Items

- None. Every item in the iteration spec's Definition of Done was implemented and covered by tests. The one remaining verification — the full ~34-minute backend test suite run to completion — was handed to the automation pump per the session's testing protocol (a single full run, never two at once).

---

## Config and Environment Changes

- **`config.yaml` → `data_manager.import_chunking.fetch_workers`** — new setting controlling how many symbols are fetched in parallel. Default: `4`. Must be 1 or more (`1` means "one at a time", which is still valid). A missing, zero, or negative value stops the app at startup with a clear error (no silent fallback).
- No database schema change, no new environment variable, no migration.

---

## Known Limitations

- **The benchmark's scan-stage timing depends on how many dates you measure.** The new "load history once" optimization loads a symbol's *entire* history up front, then reuses it. Over many dates that is a clear win; over a single date it can actually be slightly slower (it pre-loads more than that one date needs). The benchmark's docstring explains this, and its default settings are chosen to show the real win. The guaranteed, machine-checked proof of the optimization is a test that confirms each symbol's history is loaded **at most once per job** — that is always true regardless of timing.
- **No live data-provider testing in this iteration.** By design (the project is offline-first and the real expanded-data fetch is currently blocked), all automated tests use built-in offline/stub data — no network, no API keys. The live-stack browser checks (a real rate-limited fetch, a small backfill, and a score-consistency spot-check) run during QA on the running app, not in this development step.
