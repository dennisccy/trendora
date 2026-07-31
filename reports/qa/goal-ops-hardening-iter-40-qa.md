# goal-ops-hardening-iter-40 QA Report

**Phase:** goal-ops-hardening-iter-40
**Date:** 2026-07-31
**Agent:** qa
**Status:** validation_complete

**Verdict:** PASS

---

## Artifact Verification Checklist

All required artifacts present and verified:

- [x] `docs/handoffs/goal-ops-hardening-iter-40-dev.md` — complete dev handoff with implementation details
- [x] `reports/reviews/goal-ops-hardening-iter-40-review.md` — PASS_WITH_NOTES verdict
- [x] `runs/goal-ops-hardening-iter-40/status.json` — tracking in_progress → review_passed
- [x] `runs/goal-ops-hardening-iter-40/wedge-drill/` — post-fix wedge-recurrence drill evidence
- [x] `runs/goal-ops-hardening-iter-40/checkpoint-drill/` — live kill -9 checkpoint-honesty drill evidence

No functional test plan was present at `reports/qa/goal-ops-hardening-iter-40-test-plan.md`; standard QA verification conducted.

---

## Backend Test Results

### Primary test suite: test_data_manager.py

**Command:** `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py -v`

**Result:** ✓ **142 passed in 300.91s (0:05:00)**

Test coverage includes:
- `test_diagnostic_own_dates_streamed_fetch_byte_identical_to_whole_result` (TC-1) — PASS
  - Fixture-backed equality test proving `_missing_data_diagnostic`'s pre/post-fix output (`no_history`/`thin`/`intra_series_gap` lists) is byte-identical for the same DB state
- `test_checkpoint_cadence_density_and_throttle_control` (TC-4 unit-level) — PASS
  - Proves per-date checkpoint invocation density and that the throttle interval still bounds write volume
- All 140 existing tests continue to pass (no regressions)

### Regression test suite: test_data_manager_jobs_pipeline.py + test_ingest_finalize_fault_injection.py

**Command:** `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager_jobs_pipeline.py tests/test_ingest_finalize_fault_injection.py -q`

**Result:** ✓ **26 passed in 636.87s (0:10:36)**

Confirms iter-39's per-item `MemoryError` isolation and the pre-existing checkpoint-throttle unit test are unaffected by this iteration's changes.

### merge_ui_test_results.py self-tests

**Command:** `python3 incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py self-test`

**Result:** ✓ **14 passed, 0 failed** (12 pre-existing + 2 new: TC-6, TC-7)

Tests for BLOCKED verdict class and priority ordering (`FAIL > BLOCKED > PASS > SKIP`).

### replay-lane integration tests

**Command:** `bash incredible_auto_dev/tests/automation/test-replay-lane.sh`

**Result:** ✓ **65 passed, 0 failed**

Confirms the `merge_ui_test_results.py` change did not regress the replay-lane integration tests that already exercise it.

---

## Live Evidence Drills

### TC-2/TC-3: Wedge-recurrence drill (post-fix verification)

**Location:** `runs/goal-ops-hardening-iter-40/wedge-drill/`

**Setup:**
- Throwaway DB via `scripts/start-backend.sh` with `memory_cap_mb: 2650` (same cap family as iter-39 trial 3, never widened)
- Offline seeded from committed seed (AG-9 compliance)
- Same ingest/coverage-compute path post-fix

**Outcome:** ✓ **Wedge did NOT recur**

Evidence:
- Job finished `status: ok` in 35.9 s
- `GET /api/health` answered 200 on all 28 polls (0 non-200, max inter-poll gap 1.826 s) — no unresponsive window
- `VmPeak` peaked at exactly 2,713,600 kB (2650 MB, the declared cap) and did not exceed it
- A `MemoryError` fired at a DIFFERENT site (`data_manager.py:898`, a COUNT-DISTINCT aggregate), NOT at the fixed site (`_missing_data_diagnostic` / `data_manager.py:271` / `_raw_all_rows`)
- The MemoryError was caught cleanly by the existing non-fatal isolation handler with zero downtime
- Job continued and finished cleanly afterward

**Interpretation (signal, not certainty — per binding iter-40 instruction):**
This is consistent with the hypothesis that iter-39 trial 3's wedge was caused by the fixed allocation. At the identical 2650 MB ceiling and identical single-job shape, the fixed code now (a) never reaches the old uncaught-materialization site, (b) still hits SOME memory pressure at this tight cap (expected), and (c) that pressure is fully absorbed by the existing non-fatal isolation handler with zero downtime.

### TC-4: Checkpoint-honesty kill -9 + restart drill

**Location:** `runs/goal-ops-hardening-iter-40/checkpoint-drill/`

**Setup:**
- Throwaway DB via `scripts/start-backend.sh` with committed `memory_cap_mb: 6144` (not a memory-pressure test)
- Offline seeded from committed seed
- K=25-trading-day window (2026-03-30 → 2026-05-04)

**Method:**
1. Combined trigger+poll+kill script (single script, no round-trip gaps)
2. Polled `dates_done` every 0.1 s from the job's `GET /api/data/jobs/{id}` endpoint
3. Sent `kill -9` to backend when polled `dates_done` first reached M=12 of 25
4. Restarted backend with same config
5. Read persisted `data_provider_runs` row directly from `drill.db`

**Outcome:** ✓ **Checkpoint gap reduced to 1 date**

Evidence:
- M (true in-memory progress at kill time): 12 of 25 dates
- Persisted `dates_done` after restart: 11
- Gap: **1 date** (vs. iter-39's order-of-magnitude gap: 18 in memory vs. 2 persisted)
- Job-summary contract holding: `snapshots_created: 10`, `already_snapshotted: 1`, `error_other: 0` → `10 + 1 + 0 = 11 = dates_done` (internally consistent)

**Interpretation:**
The 1-date gap is well within "one checkpoint interval" of true progress for a job whose per-date burst rate (~120-140 ms/date) is far faster than the old 10 s throttle could track. The new 1.0 s throttle tracks closely, closing the honesty gap as intended.

### TC-5: perf-budgets.md retraction

**Location:** `reports/perf-budgets.md`

**Verification:** ✓ Inline retraction notes added in place at trial-3 table row (~line 4996) and the "Recommendation" paragraph (~line 5018), both pointing forward to the already-existing "Audit B2" correction and this iteration's own new "Iteration 40" section.

No unqualified sentence in the file still names `backfill_workers` as the wedge's cause.

---

## Code Quality Checks

### Streaming `_missing_data_diagnostic`

**File:** `apps/backend/app/engine/data_manager.py:271-274`

**Change:** Replaced bare `session.exec(select(...))` iteration (which SQLAlchemy materializes WHOLE-RESULT via `cursor._raw_all_rows()` before the loop body runs, ~3.3M rows) with `.yield_per(cfg.research.read_batch_size)`, mirroring the exact idiom already used in `prices.py`'s `_BarCache.prefill`.

**Verification:** ✓ 
- Grouping into `own_dates_by_symbol` and every downstream consumer are byte-identical
- Only the fetch strategy changed
- Test TC-1 proves byte-identical output pre/post-fix

### Comment correction

**File:** `apps/backend/app/engine/data_manager.py:262-274`

**Change:** Corrected in-code comment from "no unbounded whole-table scan" (true of scope, false of materialization) to plainly state: query bounded by symbol set but was previously materialized whole-result in memory, now streamed.

**Verification:** ✓ Comment now accurately describes both scope and materialization strategy.

### Checkpoint cadence tightening

**File:** `apps/backend/app/engine/data_manager.py:~4055`

**Change:** `_RUN_RECORD_CHECKPOINT_INTERVAL_S` tightened from 10.0 s → 1.0 s

**Verification:** ✓
- Per-date call sites unchanged
- Throttle mechanism unchanged
- `message` field unchanged
- `_run_detail()` serializer unchanged
- Only the interval value + documented reasoning changed
- Test TC-4 proves density guarantee holds and throttle still bounds write volume
- Live drill TC-4 confirms 1-date gap at burst rate of ~120-140 ms/date (vs. order-of-magnitude at 10 s threshold)

### merge_ui_test_results.py BLOCKED verdict class

**File:** `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py`

**Changes:**
- `parse_rows` now recognizes `BLOCKED` (both primary cell scan and annotated-cell fallback regex)
- `compute_overall` applies `FAIL > BLOCKED > PASS > SKIP/SKIPPED` priority (both row-verdicts and file-headline fallback branches)
- `merge()` output gained "## Blocked Tests" section and blocked count for consistency with `demo_runner.py`

**Verification:** ✓
- Unit tests TC-6 and TC-7 prove the headline behavior (all-BLOCKED → BLOCKED headline; FAIL over BLOCKED when both present)
- Existing 65 replay-lane integration tests continue to pass
- 12 pre-existing self-tests unaffected

---

## Summary

**Test Results:**
- Backend test suite (test_data_manager.py): 142/142 ✓
- Regression suite (jobs_pipeline + fault_injection): 26/26 ✓
- merge_ui_test_results.py self-tests: 14/14 ✓
- replay-lane integration tests: 65/65 ✓
- **Total: 247 tests passed, 0 failed**

**Live Evidence Drills:**
- TC-2/TC-3 (wedge-recurrence): wedge did NOT recur at 2650 MB with fixed code ✓
- TC-4 (checkpoint-honesty): 1-date gap vs. order-of-magnitude gap pre-fix ✓
- TC-5 (perf-budgets.md correction): retraction notes in place ✓

**Code Quality:**
- All definition-of-done items implemented and evidenced
- No regressions in existing test suites
- Requirements met:
  - `_missing_data_diagnostic` streams via `yield_per` (byte-identical output)
  - Comment accurately describes scope vs. materialization
  - Checkpoint interval tightened to 1.0 s with density proven mathematically and live
  - merge_ui_test_results.py BLOCKED verdict class implemented with correct priority
  - perf-budgets.md corrected in place
  - Dev handoff complete

**Frontend:** SKIPPED — phase spec explicitly states `Frontend Present: no` (backend-only iteration)

**Browser checks:** SKIPPED — no frontend present

**Functional test plan:** Not available at reports/qa/goal-ops-hardening-iter-40-test-plan.md; standard verification conducted

---

## Blockers

None. All tests pass. All evidence drills completed successfully. All implementation requirements met.

---

## Notes

1. The wedge-recurrence drill's first run (run 1) was confounded by a test-setup bug (job triggered mid-warmup), so it was discarded and superseded by run 2 (clean, authoritative). This deviation does not re-tune the cap and does not violate the "don't chase a fourth cap value" intent — both runs used identical 2650 MB cap.

2. Checkpoint-cadence density guarantee remains wall-clock-time-based, not count-based. An extremely fast future job (sub-100ms/date) could still show a multi-date gap under the time-based mechanism. Not addressed this iteration (plan explicitly scoped as "tighten the interval," not "redesign the mechanism") — flagged for awareness only (documented in dev handoff's Known Issues).

3. The reviewer raised two NOTE-severity issues (dev handoff honesty, already resolved), neither blocking this QA validation.

---

**Report completed:** 2026-07-31 02:45 UTC
