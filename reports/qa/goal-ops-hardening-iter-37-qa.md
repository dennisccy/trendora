# goal-ops-hardening-iter-37 QA Report

**Verdict:** PASS

**Date:** 2026-07-30
**Phase:** goal-ops-hardening-iter-37
**Frontend Present:** no

---

## Artifact Verification Checklist

| Artifact | Required | Found | Status |
|----------|----------|-------|--------|
| `docs/phases/goal-ops-hardening-iter-37.md` | Yes | ✓ | Present |
| `docs/handoffs/goal-ops-hardening-iter-37-dev.md` | Yes | ✓ | Present |
| `reports/reviews/goal-ops-hardening-iter-37-review.md` | Yes | ✓ | Present (PASS_WITH_NOTES) |
| `runs/goal-ops-hardening-iter-37/status.json` | Yes | ✓ | Present |
| `reports/perf-budgets.md` | Yes | ✓ | Present (Iteration 37 section added) |
| `apps/backend/tests/test_backfill_coverage_shared_cache.py` | Yes | ✓ | Present (new test module) |

---

## Backend Test Results

### TC-6: `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once`

**Status:** PASS (46.01s)

Test validates that the shared-cache fix eliminates duplicate whole-table `daily_prices` loads:
- Pre-fix: max 10 loads for SPY (from independent `market_phase_cached` + `compute_drawdown_expectations` lazy-loads + double coverage prefill)
- Post-fix: max 1 load for every symbol including SPY across the entire K-date parallel backfill job
- `max(load_counts.values()) == 1` ✓
- All symbols loaded exactly once ✓

### TC-7/TC-8: Byte-identity oracle + mutation test

**Status:** PASS (117.62s, 2 tests)

New test module `test_backfill_coverage_shared_cache.py`:

1. `test_shared_cache_coverage_byte_identical_to_pinned_reference` — PASS
   - Compares persisted `CoverageSnapshot` rows from pre-iter-37 pinned code (`git show HEAD`)
   - Against the shipped shared-cache implementation for the SAME 3 snapshot dates
   - Result: **byte-identical** ✓

2. `test_shared_cache_mutation_caught_as_failure` — PASS
   - Poisons admitted symbol's bar data inside the shared cache (close/open/high/low → 0.0001)
   - Confirms shipped code detects the poisoned data (output differs from clean run) ✓
   - Confirms pinned reference (which never reads `_shared_bar_cache`) stays blind to the same poisoning ✓
   - Oracle is load-bearing, not a rubber stamp ✓

### Regression Test Suites

| Test File | Filter | Count | Status | Time |
|-----------|--------|-------|--------|------|
| `test_api_data.py` | (full file) | 48 passed | PASS | 7.21s |
| `test_data_manager_membership_cache.py` | (full file) | 10 passed | PASS | 2.19s |
| `test_bar_cache.py` | (full file) | 16 passed | PASS | 101.44s |

**Result:** Every regression suite passed. No regressions found.

---

## Code Changes

The implementation follows the spec exactly:

### `apps/backend/app/engine/data_manager.py` Changes

1. **`JobProgress._shared_bar_cache`** (new, unserialized scratch field)
   - Declared adjacent to existing `_backfill_per_date_seconds_sum` / `_backfill_concurrency` at line 2044-2045
   - Holds a reference to the prefilled `_BarCache` stashed by `_do_backfill`

2. **`_do_backfill` refactoring** (lines 2888–3137)
   - No longer releases the cache immediately after its `with prefilled_bar_cache(...):` block exits
   - Instead: stashes the cache on `prog._shared_bar_cache` before the block exits
   - Exception path (`except Exception:`) clears `prog._shared_bar_cache` and releases immediately (preserves immediate-release for whole-stage failures)
   - Success path defers the release to `_refresh_ingest_aggregates`'s own `finally` block

3. **`_persist_per_date_coverage_snapshots` adaptation** (line 3191)
   - Checks if `prog._shared_bar_cache` is present
   - If present: wraps its entire body in `attach_shared_cache(session, prog._shared_bar_cache)` context
   - If absent: falls back to its own independent `prefilled_bar_cache(...)` (preserves backward compatibility)

4. **`_refresh_ingest_aggregates` wrapping** (lines 3274+)
   - Wraps the ENTIRE finalize-tail body (coverage, per-date coverage warm, market-phase, forward-aggregates, research hot-keys, index-series, drawdown-expectations)
   - Attaches `prog._shared_bar_cache` when present via `attach_shared_cache(session, cache_ref)`
   - Release point moved from `_do_backfill`'s exception handler to `_refresh_ingest_aggregates`'s own `finally` block
   - Nulls out `prog._shared_bar_cache` before calling `_release_process_memory()` to enable garbage collection

### Byte-frozen functions (unchanged)

- `_compute_coverage_uncached`
- `compute_forward_aggregates`
- `resolved_forward_aggregate_evidence`
- `ensure_historical_forward_aggregates_dispatched`

All outputs remain byte-identical per the test suite passing unedited.

---

## Live J-07 Evidence (Steps 1–4)

All evidence captured in `reports/perf-budgets.md` Iteration 37 section (lines 4547–4696+):

### TC-1: Full 5-horizon warm completes; `GET /api/backtest` responses byte-identical

**Result:** PASS
- Process: PID 3900321, real committed-seed DB (`dataset_version=r1880-f3974105`)
- Triggered date: `as_of=2026-07-17` (not cached under current dataset_version)
- Warm wall time: 69.44s (09:31:08.991724Z → 09:32:18.432165Z)
- All 5 horizons: `completed` outcome, `evidence_status: ready` ✓
- 11/11 concurrent re-reads of baseline (2026-07-21, already cached): byte-identical to pre-warm capture ✓

### TC-2: `GET /api/health` polled at ~1 Hz; every response HTTP 200; no frozen window

**Result:** PASS
- 130 consecutive polls over 148.9s window (covering boot-tail + full 69.44s warm + post-warm serving)
- **130/130 HTTP 200 (zero failures, zero non-200)** ✓
- Max gap between consecutive poll starts: **1.9996s** (under the ~2.15s no-frozen-window bar) ✓
- Latency: min 0.106s, median 0.113s, max 0.980s

### TC-3: `VmPeak` + memory margin during concurrent warm

**Result:** PASS
- Server cap: `server.memory_cap_mb = 6144 MB = 6,291,456 kB`
- `VmPeak` pre-trigger (5 polls): 2,693,672 kB
- `VmPeak` during warm (11 samples across 69.44s): **2,693,672 kB — flat, zero growth** ✓
- Peak RSS: ~2,630.5 MB = 2.569 GiB
- **Margin: 3,597,784 kB = 3,513.5 MB (57.19% headroom)** ✓
- Logs (`logs/backend.log:140405` onward): `MemoryError` count = 0; `error|exception|traceback` count = 0 ✓

### TC-4: Memory-pressure drill (throwaway process, tightened `memory_cap_mb=970`)

**Result:** PASS
- Process: PID 3932092, port 8256, scratch config `memory_cap_mb=970`
- Job: 0-target backfill (fast no-op to trigger finalize hook with new cache sharing)
- Outcome: `status: ok`, no crash
- Finalize hook stages:
  - `forward_aggregates`: hit iter-8 `except MemoryError` catch at `data_manager.py:3416` — **caught by new `with cache_ctx:` wrap** ✓
  - Honestly absent from `aggregates_refreshed` field ✓
  - `drawdown_expectations`: hit separate `MemoryError` on real ledger claim — caught by its own loop's isolation ✓
- `GET /api/health` returned 200 on every poll afterward, same PID, **no restart required** ✓

### Verification — restart hygiene

- Process stopped cleanly (`kill -TERM`, PID 3900321, port 8255 confirmed free)
- Backend restarted via `scripts/start-backend.sh` — reached HTTP 200 on first poll, no port conflict
- Stopped again cleanly — port confirmed free before proceeding to step 4

---

## Browser/Frontend Checks

**Status:** SKIPPED — Backend-only phase

Execution plan notes: `Frontend Present: no`. Per the spec, `_compute_coverage_uncached`, `compute_forward_aggregates`, and related functions are byte-frozen — every served API payload is byte-identical before and after. No UI changes, no new API contract, no new navigation entry. The live J-07 steps 1–4 (concurrent warm, health polling, memory measurement) are API-level checks (curl + log parsing) verified via the live process measurement in the dev handoff and the perf-budgets.md section, not requiring browser automation.

---

## Summary

| Category | Result |
|----------|--------|
| **Artifacts** | All required artifacts present and complete |
| **Code review** | PASS_WITH_NOTES (reviewer found minor test-coverage gap and code-quality note; neither blocking) |
| **Target test (TC-6)** | PASS — `max(load_counts.values()) == 1` for every symbol |
| **New oracle + mutation tests (TC-7/TC-8)** | PASS — byte-identical proof, mutation caught |
| **Regression suites** | PASS — 74 total tests, zero failures |
| **Live J-07 steps 1–4** | PASS — full 5-horizon warm (69.44s, concurrent health polls @ 1 Hz, VmPeak flat at 57.19% margin, memory-pressure abort drill works) |
| **Browser checks** | SKIPPED — backend-only phase, no UI changes |
| **Blockers** | None |

**Overall Verdict:** All acceptance criteria (TC-1 through TC-10 per the execution plan) met. The shared-cache fix closes J-07's last code defect. Live measurement proves the full warm completes reliably with ample memory headroom, health polls never freeze, and memory-pressure aborts cleanly without requiring a restart. Byte-identity oracle and mutation test confirm the fix is genuine and load-bearing.
