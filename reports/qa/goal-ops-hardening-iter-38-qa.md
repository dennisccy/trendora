# QA Validation Report — goal-ops-hardening-iter-38

**Phase:** goal-ops-hardening-iter-38  
**Date:** 2026-07-30  
**Frontend Present:** no  
**QA Agent:** qa (validation mode)

---

## Verdict

**Verdict:** PASS

---

## Artifact Verification Checklist

| Artifact | Required | Present | Status |
|----------|----------|---------|--------|
| `docs/handoffs/goal-ops-hardening-iter-38-dev.md` | YES | ✓ | Complete |
| `reports/reviews/goal-ops-hardening-iter-38-review.md` | YES | ✓ | PASS_WITH_NOTES |
| `runs/goal-ops-hardening-iter-38/status.json` | YES | ✓ | Present |
| `runs/goal-ops-hardening-iter-38/plan.md` | YES | ✓ | Present |

**All required handoff and status artifacts verified present and valid.**

---

## Review Report Summary

**Review Verdict:** PASS_WITH_NOTES  
**Reviewer Date:** 2026-07-30

The review confirmed:
- Definition of Done: complete
- Scope creep: none
- No changes to byte-frozen functions (`compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, `ensure_historical_forward_aggregates_dispatched`)
- New unit tests (TC-6: exception handling; TC-7: two-arm comparison) pass and are load-bearing (not vacuous)
- All code quality standards: PASS (state transitions, test quality, no dead code, no hardcoded localhost, architecture principles)

**Review Note:** logger.warning usage for liveness assertion (not .info) is pragmatic due to app's missing root-logger config that would drop .info records. Disclosed as non-incorrect; follow-up on root-logger config is out of scope.

---

## Backend Test Results

**Command:**
```bash
cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py tests/test_bar_cache.py tests/test_backfill_coverage_shared_cache.py -q
```

**Exit Code:** 0  
**Status:** PASS

**Output:**
```
157 passed in 614.45s (0:10:14)
```

**Test Summary:**
- Total tests run: 157
- Passed: 157
- Failed: 0
- Skipped: 0

**Coverage:**
- `test_data_manager.py` — includes both new TC-6 test and strengthened TC-7 test
- `test_bar_cache.py` — existing shared-cache coverage, no regressions
- `test_backfill_coverage_shared_cache.py` — existing cache reference/mutation tests, no regressions

**Key Tests Verified:**
- TC-6: `test_do_backfill_whole_stage_exception_releases_shared_cache_and_reraises` — NEW test confirming whole-stage exception inside `with prefilled_bar_cache(...)` block releases `prog._shared_bar_cache` and re-raises
- TC-7: `test_run_data_job_backfill_wires_finalize_hook_end_to_end` — STRENGTHENED to compare live-cache vs forced-fallback run's `aggregates_refreshed` lists (now identical, as expected)

---

## Code Changes Verification

### Files Modified
1. **`apps/backend/app/engine/data_manager.py`**
   - Liveness assertion log line (`logger.warning`) at ~line 3361 proving `cache_ctx` resolved to `attach_shared_cache` (live) or `nullcontext` (no cache)
   - TEST-ONLY `TRENDORA_FORCE_LEGACY_BAR_CACHE` env toggle at ~line 3110 to force fallback behavior
   - Stale docstring fix at ~line 650-659 for `membership_timeline_cached` cost description
   - ✓ Verified: No changes to byte-frozen functions

2. **`apps/backend/tests/test_data_manager.py`**
   - New test (TC-6): `test_do_backfill_whole_stage_exception_releases_shared_cache_and_reraises` (~line 2168)
   - Strengthened test (TC-7): `test_run_data_job_backfill_wires_finalize_hook_end_to_end` adds monkeypatch parameter for forced-fallback comparison
   - `contextlib.contextmanager` import added
   - ✓ Verified: Both new/strengthened tests passed

3. **`reports/perf-budgets.md`**
   - Line 4466: "591 symbols" → "548 symbols" correction (audit B8/iter-37)
   - New "Iteration 38" section (lines ~4773+) with:
     - Two-arm cache-liveness comparison (live vs forced-fallback VmPeak)
     - Live-basis re-trigger step-1 VmPeak margin
     - `read_pool()` wall-clock cost measurement
   - ✓ Verified: All corrections and measurements recorded

### Evidence Directories
- **`runs/goal-ops-hardening-iter-38/mem-drill/`** (NEW)
  - `seed_throwaway_db.py` — widened fixture targeting K=3-trading-day range
  - Monitor scripts and CSV outputs for both arms (live cache vs forced-fallback)
  - Job status JSON files confirming `dates_total >= 3` and liveness assertion
  - Log excerpts corroborating cache_ctx resolution (binding iter-37 lesson)
  - Two-arm summary JSON with measurement results
  - ✓ 23 evidence files present

- **`runs/goal-ops-hardening-iter-38/j07-warm/`** (NEW)
  - Monitor script for continuous VmPeak + 1Hz health poll
  - Pre/post-warm `GET /api/backtest` captures
  - Final job status confirming all 5 horizons reached `evidence_status: "ready"`
  - Health-latency CSV with 234 total polls, zero non-200 responses
  - Log excerpt corroborating warm completion
  - ✓ 10 evidence files present

---

## Functional Test Plan

No functional test plan file exists at `reports/qa/goal-ops-hardening-iter-38-test-plan.md`.

**Status:** N/A — backend-only verification iteration; no new user-facing capability. Acceptance criteria (TC-1 through TC-11) are all backend test/measurement items covered by unit tests and drill evidence (see Development Handoff).

---

## Browser/UI Checks

**Status:** SKIPPED — Frontend Present: no

This is a backend-only measurement/verification iteration:
- No new user-facing capability
- No new UI surface, navigation, or information display
- No new user actions
- Zero frontend files modified

Per phase spec and execution plan, all four of J-07's acceptance criteria are verified through backend unit tests, drill measurements, and log assertions — not through UI walkthrough.

---

## Development Work Summary

### What Was Built (per dev handoff)

1. **Liveness assertion for finalize-tail `cache_ctx`** (~line 3361)
   - `logger.warning` line records whether cache_ctx resolved to `attach_shared_cache` (live) or `nullcontext` (no cache)
   - Binding iter-37 lesson: assertion must be explicit, never assumed from lexical wrap alone
   - Corroborable against bounded line range in live `logs/backend.log`

2. **TEST-ONLY forced-fallback env toggle** (`TRENDORA_FORCE_LEGACY_BAR_CACHE=1`)
   - Skips the `prog._shared_bar_cache` stash at the single choke point
   - Every downstream consumer's own `is not None` check then falls back to pre-iter-37 behavior
   - Enables genuine two-arm VmPeak comparison (live vs fallback)
   - Unset in every real deployment

3. **Widened throwaway-DB drill fixture**
   - Real K=3-trading-day window (2026-06-16 → 2026-06-18) instead of deliberate 0-target no-op
   - Makes `_do_backfill` genuinely stash `prog._shared_bar_cache`
   - Finalize-tail `cache_ctx` resolves to real `attach_shared_cache`, never `nullcontext()`

4. **Two-arm live-cache-vs-forced-fallback VmPeak comparison** (throwaway DB, launched via `scripts/start-backend.sh`)
   - Both arms confirmed via liveness log
   - Both produced identical `aggregates_refreshed` category list (TC-7)
   - Fallback arm consistently 2.6x-3.9x slower across trials
   - Finalize-tail-only VmPeak deltas: 229.0 MB (live) vs 238.5 MB (fallback) — close margin, not dramatic difference
   - Supplementary trial at tighter 3072 MB cap: fallback crashed while live completed — disclosed as data point, not overclaimed as proof

5. **Live full-deep-basis warm re-trigger** (TC-3/TC-4)
   - Genuine single-day backfill (2025-05-23) on real committed-seed DB
   - Triggered real cold recompute of all 5 configured horizons via ingest-finalize hook (not `GET /api/backtest`)
   - All 5 horizons reached `evidence_status: "ready"`
   - VmPeak: 58.6% of 6144 MB cap
   - Concurrent 1Hz health poll (234 total polls): zero non-200 responses, max-gap 2.355s (measurement-script-attributable, not scored as failure per plan)
   - Boot took ~1s (within J-04's ≤5s budget)

6. **New unit test (TC-6)**
   - `test_do_backfill_whole_stage_exception_releases_shared_cache_and_reraises`
   - Whole-stage exception inside `with prefilled_bar_cache(...)` block
   - Fires strictly AFTER `prog._shared_bar_cache` genuinely stashed (faults `_checkpoint_run_record` conditionally on cache being set)
   - Load-bearing test, not vacuous
   - Asserts except branch clears reference and calls `_release_process_memory()` before re-raising

7. **Strengthened end-to-end test (TC-7)**
   - `test_run_data_job_backfill_wires_finalize_hook_end_to_end`
   - Now runs forced-fallback job (monkeypatching `_refresh_ingest_aggregates`)
   - Asserts `aggregates_refreshed` sets are IDENTICAL between live-cache and forced-fallback runs
   - Closes audit finding T2 (iter-37)

8. **Docstring fix** (`membership_timeline_cached`, ~line 650-659)
   - Stale comment described pre-iter-36 whole-pool scan behavior
   - Updated to accurately reflect current batched/active-cache-reuse behavior
   - Verified via `git log -p` that text predates iter-36's batching fix and was never updated

9. **perf-budgets.md corrections and measurements**
   - Line 4466: "591 symbols" → "548 symbols" (audit B8/iter-37)
   - New Iteration 38 section with:
     - Two-arm cache-liveness comparison narrative
     - Live-basis re-trigger VmPeak margin
     - `read_pool()` wall-clock cost: 0.5628 ms/call (micro-benchmarked)
     - Projected cost: ~11.6s vs pre-batching ~1.1s = ~10.6s added constant on cold path (small vs dominant per-symbol work)

### Binding Lessons Applied

1. **iter-37 lesson** — drill on a conditional path must ASSERT the condition was live, never assume from lexical wrap
   - ✓ New logger.warning line proves cache_ctx resolution for EVERY backfill/rebuild job

2. **iter-34 lesson** — throwaway-DB approach (via `scripts/start-backend.sh` with host-guard caps) is safe isolation
   - ✓ Both TC-1/TC-2 drills run on K=3 throwaway DB, launched only via startup script

3. **iter-36 lesson** — test plan taking backend down must schedule those tests LAST
   - ✓ Induced-pressure drill (step 4) inherently disruptive, scheduled strictly last per execution plan

4. **iter-34 other lesson** — saved log excerpt is not the log; corroborate against LIVE bounded line range
   - ✓ All drill claims corroborated against live `logs/backend.log`, not trimmed excerpts

### Anti-Goals Compliance

- **AG-10 (Host resource ceiling):** All heavy compute (throwaway-DB drill + live-basis warm) launched only via `scripts/start-backend.sh` with host-guard caps applied ✓
- **AG-5 (No lookahead):** No forward-looking computation introduced ✓
- **AG-3 (Displayed numbers correct):** All measurements recorded with source data and corroborating log lines ✓
- **AG-8 (Resilience to data change):** No new unbounded ORM loads or data-shape brittleness ✓
- **AG-9 (Offline-deterministic ingest):** No external network calls introduced ✓

---

## Known Issues & Disclosures

### NOTE (from review, not a blocker)
- **logger.warning usage for liveness line:** App never configures root-logger handler, so uvicorn's last-resort handler only surfaces WARNING and above. `.info`-level version was silently dropped live. Using `.warning` for routine liveness logging is pragmatic workaround; follow-up on root-logger config is out of this iteration's scope (disclosed, non-incorrect).

### Measured Findings (reported honestly, not as failures)

1. **Fallback-arm true from-boot baseline lost (one trial):** First fallback-arm drill used `nohup setsid bash` which forked internally, capturing setsid wrapper PID instead of uvicorn's. Two monitor windows failed before finding real PID. Canonical two-arm comparison in perf-budgets.md compares live's TRUE from-boot baseline vs fallback's EARLIEST SUCCESSFULLY-CAPTURED sample (already past backfill-compute stage). Finalize-tail-only delta (the actual TC-2 metric) unaffected since computed from end-of-backfill-stage forward (captured for both arms). Disclosed, not patched over.

2. **1Hz health-poll max-gap 2.355s (vs ~2.15s reference):** Attributable to monitor script's own sequential pattern (health check + job-status check + 1.0s sleep), not genuine backend unresponsiveness. Every poll still answered HTTP 200. Not scored as TC-4 failure per plan's own convention (honest disclosed miss, same as iter-37).

3. **Two-arm comparison did not corroborate iter-37 auditor's "resident cache raises peak" hypothesis:** At K=3/throwaway-DB scale, tail-only deltas within ~4% of each other. Clearer findings: fallback consistently 2.6x-3.9x slower in wall-clock, and in one supplementary tighter-cap trial, fallback crashed while live completed (though same code path in both arms, not proven deterministic). Reported as honest measurement outcome, not adjusted to fit narrative.

4. **J-07 step 1 live-basis warm took 5.6 minutes (338s) vs "well under 5 minutes" framing:** Dominated by membership-timeline cache invalidation-by-new-snapshot recompute over ~1,881 stored dates (expected O(dates) cost, not a regression). VmPeak stayed comfortably under cap (58.6%). Disclosed.

---

## Summary

**Status:** PASS

All acceptance criteria verified:

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Unit tests pass | ✓ PASS | 157/157 tests passed in 614.45s |
| TC-6 (exception handling) | ✓ PASS | New test present and passing |
| TC-7 (two-arm comparison) | ✓ PASS | Strengthened test passing |
| TC-1 (throwaway drill dates_total≥3) | ✓ PASS | Job status confirms K=3 date range |
| TC-2 (cache liveness assertion) | ✓ PASS | Logger.warning line corroborable in logs |
| TC-3 (live-basis warm) | ✓ PASS | All 5 horizons reached evidence_status: "ready" |
| TC-4 (health poll during warm) | ✓ PASS | 234 polls, zero non-200s |
| Docstring fix | ✓ PASS | Verified accurate vs current behavior |
| perf-budgets.md corrections | ✓ PASS | "591→548" and Iteration 38 section present |
| No regressions (J-01, J-03, J-04, J-05, J-06, J-08, J-09) | ✓ PASS | Shared-cache coverage tests passing |
| No byte-frozen function changes | ✓ PASS | Verified in diff |
| AG-10 compliance (host-guard caps) | ✓ PASS | All heavy compute via `scripts/start-backend.sh` |

**Blockers:** None  
**Warnings:** None (disclosure items above are not failures, per plan's own convention)

---

## Next Actions

1. **Goal Evaluator** — reads this QA report + dev handoff + review report to produce iteration verdict (CONTINUE / GOAL_ACHIEVED / etc.) and update journey-history for J-07
2. **Status Update** — mark `runs/goal-ops-hardening-iter-38/status.json` complete
3. **Post-QA Steps** — auditor review (post-QA auditor reads spec/handoff/review/QA report), then goal-evaluator produces final verdict for the iteration
