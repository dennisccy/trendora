# goal-ops-hardening-iter-56 Dev Handoff

**Phase:** goal-ops-hardening-iter-56
**Date:** 2026-08-10
**Agent:** developer
**Status:** complete

## What Was Built

- **Live profiling (TC-1, done BEFORE committing to either fix):** a standalone instrumented script
  (`profile_j06.py`, run under manually-applied host-guard caps — `ulimit -v`, `MALLOC_ARENA_MAX`,
  `taskset`, BLAS/OMP thread caps sourced from `host-guard.env` without modifying it) opened the live
  `apps/backend/data/trendora.db` (8.37 GB, 2,945 `scanner_runs` rows) directly and counted SQL
  statements via a `before_cursor_execute` listener. **Both candidates named in the phase spec's
  BACKGROUND section were confirmed exactly as hypothesized, with no correction needed:**
  - `GET /api/runs`'s pre-fix loop issued **2,945 individual `ScannerResult` COUNT queries — one per
    stored `ScannerRun` row**, an exact 1:1 match to the row count (not "roughly" — literally equal).
  - `compute_availability` performed one unbounded `GROUP BY daily_prices.date` scan across the full
    1996-2026 benchmark calendar (5,391 trading days) on every call, with zero caching.
  - Full methodology and numbers recorded in `reports/perf-budgets.md` Addendum 20.
- **`GET /api/runs` N+1 fix (`apps/backend/app/api/runs.py`):** the per-run `ScannerResult` COUNT query
  inside the `for run in run_rows:` loop is replaced with ONE grouped aggregate query
  (`select(ScannerResult.run_id, func.count()).group_by(ScannerResult.run_id)`), read once into a dict
  before the loop. Same endpoint, same response shape, byte-identical `n_stocks` per run (a run absent
  from the grouped result — zero stored results — honestly defaults to `0`, exactly what the old
  per-run `COUNT()` returned for it).
- **`GET /api/data/availability` ingest-time cache (`apps/backend/app/models.py`,
  `apps/backend/app/engine/data_manager.py`, `apps/backend/app/api/data.py`):** a new standalone
  `AvailabilityCache` table (`create_all`-managed, unique on `dataset_version` alone — mirrors
  `MembershipTimelineCache`'s single-row convention, since `compute_availability` has no as-of/range
  parameter to key on) keyed by the SAME narrow `_membership_dataset_version` stamp
  `CoverageSnapshot`/`MembershipTimelineCache` already use.
  - `availability_cached_with_status(session, config=None) -> (payload, persisted_this_call)`: HIT
    deserializes the stored row (no recompute); MISS computes once via the UNCHANGED
    `compute_availability` (the sole producer) and persists it, pruning stale rows.
  - `availability_from_storage(session, config=None) -> dict`: `GET /api/data/availability`'s new
    serving path — reads the persisted row for the current stamp; a genuinely missing row (no warm has
    ever run) serves the honest not-yet-computed empty payload (`{"total_symbols": 0,
    "trading_day_count": 0, "cells": []}`, ZERO database queries) — never a live `compute_availability`
    call on this default request path (AG-8). Mirrors `_coverage_not_yet_computed_payload`'s convention.
  - `compute_availability` itself is byte-unchanged; still the sole producer, called directly by the
    warm and by every existing test that wants a genuine live compute.
- **Finalize-hook wiring (`_refresh_ingest_aggregates`, `apps/backend/app/engine/data_manager.py`):** a
  new `availability_heatmap_warm` phase added immediately after `index_series_warm`, mirroring its exact
  shape — unconditional (not gated on `prog.new_snapshot_dates`, since the dataset-version stamp is
  global), wrapped in the SAME iter-8 MemoryError-isolation convention (`MemoryError` caught distinctly,
  `_release_process_memory()` called, stops immediately; generic `Exception` isolate-and-continue for
  everything else), phase-timing logged. `"availability_heatmap"` is appended to `aggregates_refreshed`
  ONLY when `availability_cached_with_status` actually persisted a new row this run (a cache HIT is an
  honest omission, never a fabricated refresh) — added as a further legal member of the enumerated
  `aggregates_refreshed` list in both docstrings that name it (mirrors the iter-13 `"index_series"`
  precedent; no new field, no second record).
- **`J-05.json` golden-date rotation (test-fixture only, no product-code change):** the single-use
  target date is rotated from the now-consumed `2010-11-08` (`scanner_runs.id=2940`) to `2010-11-10`
  (steps 2/3/13/14 + the golden's `name` field), re-verified live via a direct `scanner_runs` query
  against the live DB immediately before committing the change (0 rows for `2010-11-10`; confirmed
  `2010-11-08`/`2010-11-09`/`2012-01-04`/`2013-02-14` are all already consumed). A rotation-log entry
  was appended to the file's own `_notes`.
- **`reports/perf-budgets.md` Addendum 20:** the full profiling methodology, before/after query counts,
  live HTTP measurements (3x back-to-back, idle host, `scripts/start-backend.sh`), byte-identity proof,
  and AG-9/AG-10/TC-12 verification.
- **`runs/goal-session-ops-hardening/state/blueprint.md`:** the decomposer had already pre-authored
  this iteration's changelog paragraph, the Availability heatmap Data Contract row
  (`[TARGET, iter-56 building]`), and the Backfill run-summary contract row's additive
  `"availability_heatmap"` note (`iter-56 (TARGETED, not yet built)`). Retagged both from
  `[TARGET, iter-56 building]` / `(TARGETED, not yet built)` to **BUILT, pending evaluator
  confirmation**, with the specific test names and live-measured numbers that verify the fix.

## Live measured results (before/after, `reports/perf-budgets.md` Addendum 20 for full detail)

| Endpoint | Before (Addendum 18, iter-54) | After (this iteration, 3x back-to-back, idle host) | Budget |
|---|---|---|---|
| `GET /api/runs` | 3.2-7.5s (WARN) | 1.229s / 1.010s / 1.073s | ≤1.5s — **PASS** |
| `GET /api/data/availability` | 15.1-21.2s (WARN) | 0.016s / 0.402s / 0.014s | ≤1.5s — **PASS** |

Query-count confirmation (live, 2,945-row DB): `/api/runs`'s `ScannerResult` queries per request:
**2,945 → 1**. `n_stocks` byte-identity checked for all 2,945 stored runs: **0 mismatches**.
`compute_availability`'s output vs. the warmed/served cache payload: byte-identical (`==`).

## Files Changed

- `apps/backend/app/models.py` -- new `AvailabilityCache` model (standalone, `dataset_version`-keyed).
- `apps/backend/app/engine/data_manager.py` -- `availability_cached_with_status` /
  `_availability_not_yet_computed_payload` / `availability_from_storage` (new, placed after
  `compute_availability`); new `availability_heatmap_warm` phase wired into
  `_refresh_ingest_aggregates`; both docstring `aggregates_refreshed` enum lists updated to include
  `"availability_heatmap"`; `AvailabilityCache` added to the model import block.
- `apps/backend/app/api/data.py` -- `GET /api/data/availability` now calls
  `data_manager.availability_from_storage(...)` instead of `data_manager.compute_availability(...)`
  directly.
- `apps/backend/app/api/runs.py` -- `runs()`'s per-run `ScannerResult` COUNT loop replaced with one
  grouped aggregate query read into a dict before the loop.
- `apps/backend/tests/test_api_runs.py` -- new `multi_run_engine` fixture (fast, hand-built — 3
  `ScannerRun` rows with 3/0/2 `ScannerResult` children, deliberately NOT the slow session-scoped
  `loaded_engine`) + 3 new tests: query-count (TC-2), byte-identity (TC-3), zero-result-run honesty.
- `apps/backend/tests/test_data_manager.py` -- `AvailabilityCache` added to imports; 4 new unit tests
  for `availability_cached_with_status`/`availability_from_storage` (miss-computes-and-persists,
  hit-returns-stored-no-recompute, serves-persisted-row, TC-8 honest-fallback,
  empty-DB-fallback-matches); 4 new finalize-hook tests (warms-and-persists, byte-identical-to-fresh,
  second-run-hit-not-reported, MemoryError-isolated-and-not-reported); updated the exact-set assertions
  in `test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates` and
  `test_finalize_hook_never_raises_even_when_everything_fails` to include/mock
  `"availability_heatmap"`/`availability_cached_with_status`.
- `apps/backend/tests/test_api_data.py` -- `data_api_engine` fixture now also warms the availability
  cache (mirrors its existing coverage-snapshot warm); new `test_get_data_availability_no_warm_serves_
  honest_not_yet_computed` (TC-8 at the API layer).
- `runs/goal-session-ops-hardening/journey-scripts/J-05.json` -- target date rotated
  `2010-11-08` → `2010-11-10` (steps 2/3/13/14, `name` field), rotation-log `_notes` entry appended.
- `reports/perf-budgets.md` -- new Addendum 20 (full profiling + before/after + byte-identity +
  AG-9/AG-10 verification).
- `runs/goal-session-ops-hardening/state/blueprint.md` -- retagged the Availability heatmap row and the
  Backfill run-summary contract row's iter-56 note from TARGETED to BUILT.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/<file>.py -q` (TMPDIR set per the
coordinator's env note; each file run alone — never two pytest processes concurrently, per the
coordinator's instruction).

- `test_data_manager.py`: **211 passed** (includes all 8 new availability-cache tests and the 2 updated
  exact-set tests).
- `test_api_data.py`: **51 passed** (includes the fixture change and the new TC-8 API-layer test).
- `test_api_runs.py`, selected new tests only (`-k "multi_run_engine or n_stocks"`): **3 passed** in
  0.54s — the N+1 query-count fix (TC-2), byte-identity (TC-3), and zero-result-run honesty, all against
  a fast hand-built fixture.
- `test_api_runs.py`, FULL FILE (all 9 tests, including the 6 pre-existing tests that depend on the
  session-scoped `loaded_engine` fixture): **NOT completed this dispatch.** `loaded_engine` builds a
  fresh temp DB against the full 30-year committed seed + warms the complete historical cadence — this
  is the SAME session-wide known-slow fixture flagged in `test_forward_testing.py`'s iter-55 run ("~30
  minutes without completing... this fixture's slowness is documented session-wide... not a hang"). Two
  separate attempts this dispatch each ran 30+ minutes at 99.9% CPU (confirmed making progress, not
  hung) without finishing fixture setup; both were terminated to stay within this dispatch's time
  budget, after the 3 new fast tests (which do not depend on `loaded_engine`) already confirmed the fix
  via a hand-built fixture, AND the live profiling script independently proved byte-identity across all
  2,945 real stored runs on the actual production-scale DB. See Known Issues below.
- Live measurement (real backend via `scripts/start-backend.sh`, port 8255, host-guard caps applied,
  confirmed in `logs/backend.log`): both endpoints measured 3x back-to-back on an idle host, both PASS
  (see table above). Backend started and stopped cleanly twice (once for measurement, once for the
  pre-handoff service-startup check) with no port conflicts.

## Pre-handoff verification

- [x] **Service startup works:** `scripts/start-backend.sh` started cleanly (host-guard caps applied,
  confirmed in `logs/backend.log`), `GET /api/health` answered 200 in 0.16s. Stopped, started again —
  no port conflicts, clean restart. Frontend Present: no this iteration, so no frontend start check.
- [x] **`AvailabilityCache` table creation:** confirmed live — `create_db_and_tables` (already called at
  boot, via the SAME `create_all`-managed convention every other standalone cache table this session
  uses) adds `availability_cache` to the live DB with zero schema change to any existing table;
  `git status --porcelain` on the 5 frozen host-guard paths stayed empty throughout (AG-10, TC-12).
- [x] **No unbounded scan / recompute on the request path:** confirmed by code read AND by the honest
  not-yet-computed fallback's own zero-query implementation (`_availability_not_yet_computed_payload`).
- N/A: no new dependency, no native binary, no external integration this iteration (pure DB read/cache
  work).

## Known Issues

- **`test_api_runs.py`'s FULL file run (the 6 pre-existing `loaded_engine`-dependent tests) did not
  complete this dispatch** — see Tests Run above for the full explanation (a pre-existing, session-wide
  slow-fixture issue, not something this iteration's diff caused or worsened). Confidence the 6
  pre-existing tests still pass is high but not test-confirmed this dispatch, based on: (a) none of them
  assert on query count or timing (only on VALUES: `n_stocks` ranges, regime labels, 404/503 status —
  all of which the byte-identity proofs above cover), and (b) the live profiling script independently
  verified `n_stocks` byte-identity across ALL 2,945 real stored runs on the actual production DB, a
  strictly stronger proof than what any of those 6 tests individually checks. Recommend a dedicated,
  early-session re-run of `test_api_runs.py` alone (mirroring the `test_forward_testing.py` precedent
  from iter-55) to get a clean pass/fail signal on the file as a whole.
- **`/api/runs`'s remaining ~1.0-1.2s** (well within the 1.5s budget, but not near-zero like
  `/api/data/availability`'s cache-served reads) is JSON-serializing 2,945 run summaries — a payload-size
  cost, not a query-count cost. Not re-optimized further; no DoD item asks for it, and it is comfortably
  in budget.
- TC-11 (audit lane-ordering) and the browser/golden-replay lane (J-06 target verification, J-01/J-03/
  J-04/J-08/J-09 required-still-passing) are explicitly out of the developer stage's scope per the
  spec's own lane-ordering rule — dispatched later in the pipeline.
