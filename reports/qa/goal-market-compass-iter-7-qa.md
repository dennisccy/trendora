# goal-market-compass-iter-7 QA Report

**Phase:** goal-market-compass-iter-7  
**Date:** 2026-08-20  
**Agent:** qa  
**Status:** QA Validation Complete

**Verdict:** PASS

---

## Executive Summary

Iteration 7 successfully implements J-10's fail-closed adjustment-convention gate with vendor swap from Stooq to Yahoo. The real run against the live database returned `mismatch` verdict (CVX exceeded 0.75% tolerance by ~0.11 percentage points), and the gate correctly stopped all writes before reaching any fetch/backfill operations. All backend tests pass; database state is unchanged and verified; structural gate guarantee holds.

---

## Artifact Verification

All required artifacts present and valid:

- ✓ `/home/dennis-chan/Git/trendora/docs/handoffs/goal-market-compass-iter-7-dev.md` — Exists, complete, authoritative.
- ✓ `/home/dennis-chan/Git/trendora/reports/reviews/goal-market-compass-iter-7-review.md` — Verdict: **PASS_WITH_NOTES** (reviewer confirmed gate structure, zero writes on real run, scope confinement).
- ✓ `/home/dennis-chan/Git/trendora/runs/goal-market-compass-iter-7/status.json` — Exists, phase state in_progress, review_passed.

---

## Backend Test Results

**Test 1: test_j10_recovery.py**

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_j10_recovery.py -v`

Result: **23 passed**, 0 failed, 1.64s

```
tests/test_j10_recovery.py::test_rejects_date_on_or_after_2026_08_13 PASSED
tests/test_j10_recovery.py::test_rejects_date_range_extending_past_the_window PASSED
tests/test_j10_recovery.py::test_rejects_date_before_the_window PASSED
tests/test_j10_recovery.py::test_rejects_symbol_outside_the_derived_missing_set PASSED
tests/test_j10_recovery.py::test_rejects_mnst_explicitly_the_documented_ambiguous_exclusion PASSED
tests/test_j10_recovery.py::test_rejects_wrong_source PASSED [vendor validation: stooq now rejected]
tests/test_j10_recovery.py::test_rejects_empty_symbol_list PASSED
tests/test_j10_recovery.py::test_accepts_a_fully_in_scope_request PASSED
tests/test_j10_recovery.py::test_out_of_scope_orchestration_call_never_reaches_the_provider PASSED
tests/test_j10_recovery.py::test_fetch_restores_only_the_missing_rows_and_never_touches_survivors PASSED
tests/test_j10_recovery.py::test_second_invocation_after_full_recovery_is_a_true_zero_work_noop PASSED
tests/test_j10_recovery.py::test_still_missing_symbols_is_read_only_and_deterministic PASSED
tests/test_j10_recovery.py::test_backfill_creates_snapshots_only_for_the_two_recovery_dates PASSED
tests/test_j10_recovery.py::test_recovery_constants_shape PASSED [vendor: yahoo]
tests/test_j10_recovery.py::test_data_provider_run_538_is_the_authoritative_removal_record_shape PASSED
tests/test_j10_recovery.py::test_convention_check_default_sample_is_documented_and_in_scope PASSED
tests/test_j10_recovery.py::test_convention_check_agree_when_all_sampled_pairs_within_tolerance PASSED
tests/test_j10_recovery.py::test_convention_check_mismatch_when_a_sampled_pair_exceeds_tolerance PASSED
tests/test_j10_recovery.py::test_convention_check_inconclusive_when_provider_fails PASSED
tests/test_j10_recovery.py::test_convention_check_never_writes_regardless_of_verdict PASSED
tests/test_j10_recovery.py::test_gated_recovery_stops_on_mismatch_before_any_write_capable_call PASSED [CRITICAL]
tests/test_j10_recovery.py::test_gated_recovery_stops_on_inconclusive_before_any_write_capable_call PASSED [CRITICAL]
tests/test_j10_recovery.py::test_gated_recovery_reaches_fetch_and_backfill_on_agree PASSED
```

**Test 2: test_provider_clients.py (Regression)**

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_provider_clients.py -v`

Result: **44 passed**, 0 failed, 0.13s

All tests covering `YahooProvider.get_daily` and existing provider clients pass. Confirms the additive `get_adjusted_close` method changed nothing about existing behavior.

---

## Database Integrity Verification

Read-only queries verified the zero-side-effects claim. Expected state fully confirmed:

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| `daily_prices` MAX(date) | 2026-08-10 | 2026-08-10 | ✓ PASS |
| Rows on 2026-08-11 | 0 | 0 | ✓ PASS |
| Rows on 2026-08-12 | 0 | 0 | ✓ PASS |
| `data_provider_runs` MAX(id) | 541 | 541 | ✓ PASS |
| id=541 provider | stooq | stooq | ✓ PASS |
| id=541 status | failed | failed | ✓ PASS |
| id=541 job_id | de9f...92 | de9f13209b174890a728f837ef008e92 | ✓ PASS |
| `next_session_manifests` count | 24 | 24 | ✓ PASS |
| MAX(as_of) | 2026-08-12 | 2026-08-12 | ✓ PASS |
| Total `daily_prices` rows | — | 3,309,204 | ✓ Unchanged |
| Total `scanner_runs` rows | — | 3,118 | ✓ Unchanged |

**Conclusion:** Database is exactly as expected. No rows written during iteration 7.

---

## Structural Gate Verification

Code analysis of `run_gated_recovery()` (apps/backend/app/engine/j10_recovery.py, lines 532-567):

```python
def run_gated_recovery(...) -> GatedRecoveryOutcome:
    """The ONE J-10 retry entry point (steps 2a->3): run the adjustment-convention 
    check FIRST; only a verdict of EXACTLY "agree" reaches 
    `run_bounded_recovery_fetch` / `run_bounded_recovery_backfill`"""
    
    check = check_adjustment_convention(...)  # Line 553
    
    if check.verdict != "agree":              # Line 560 — GATE HERE
        return GatedRecoveryOutcome(          # Line 561-564
            convention_check=check,
            stopped_reason=f"...",
        )
    
    # Only reached if verdict == "agree"
    fetch = run_bounded_recovery_fetch(...)   # Line 565
    backfill = run_bounded_recovery_backfill(...)  # Line 566
    return GatedRecoveryOutcome(...)           # Line 567
```

**Structural Guarantee:** The fetch/backfill calls are positioned AFTER the conditional return. No code path can reach the write-capable functions on any verdict other than `"agree"`. This is a textual and causal gate, enforced by Python's control flow semantics.

**Verified:** 
- ✓ Fetch and backfill calls are unreachable on `mismatch` verdict
- ✓ Fetch and backfill calls are unreachable on `inconclusive` verdict
- ✓ Real run returned `mismatch` and correctly exited before any write

---

## Real Run Evidence

The developer ran `check_adjustment_convention()` against the LIVE database on 2026-08-20:

- **20 sample symbols** from `CONVENTION_CHECK_SAMPLE_SYMBOLS` (AAPL, AMZN, BAC, CSCO, CVX, DIS, GOOGL, HD, INTC, JNJ, JPM, KO, META, MRK, MSFT, NVDA, PEP, PG, WMT, XOM)
- **5 trading dates** (2026-08-04, 2026-08-05, 2026-08-06, 2026-08-07, 2026-08-10)
- **88 sampled pairs** compared (20 symbols × 5 dates minus 12 pairs with no stored baseline)

**Verdict: `mismatch`**

| Symbol | Pairs | Relative Delta | Within 0.75%? |
|--------|-------|-----------------|---------------|
| AAPL | 4 | 0.08617% | yes |
| XOM | 4 | 0.64334% | yes |
| CVX | 5 | 0.86517% | **no** — exceeded tolerance |
| (others) | 76 | 0.0% (exact match) | yes |

**Trigger:** CVX's 5 pairs all showed a uniform ~0.8652% delta, just over the 0.75% tolerance threshold. The deviation is internally consistent (same value across 5 independent trading days), signature of a single real proportionally-applied dividend adjustment, not noise. However, the tolerance was fixed at 0.75% per goal.md's proposed default BEFORE the run; it was not adjusted after seeing the result.

**Outcome:** Zero writes executed. The gate correctly returned `mismatch` and prevented both fetch and backfill operations.

---

## Browser Checks

**Status: SKIPPED**

Per operational constraint (database damage from prior deletion, lane gate in docs/goal.md): 
> "no lane may verify journeys against this dataset before J-10's post-recovery verification passes"

The recovery verification did NOT pass (convention check returned `mismatch`). The database remains damaged at the 2026-08-10 frontier. Frontend is not running (`Frontend Present: no` for this iteration per operational override). Browser checks are not executed.

This is correct per the operational gate — browser/Chrome MCP checks are blocked until post-recovery verification succeeds in a later iteration.

---

## Code Quality Review (from reviewer)

Reviewer verdict: **PASS_WITH_NOTES**

- ✓ Structural gate is genuine (no code path reaches writes on non-agree verdict)
- ✓ Real run verified via direct read-only SQL
- ✓ Vendor swap correct (stooq → yahoo)
- ✓ Additive capability correct (`get_adjusted_close` fetches `indicators.adjclose`, not raw `quote.close`)
- ✓ No scope creep
- ✓ No interchangeability claims
- ✓ Tolerance not loosened after borderline result

Minor issue: `_parse_adjusted_close` branches have no synthetic unit test (only one-time non-repeatable live probe as evidence). Not a blocker; existing test patterns in `test_provider_clients.py` could add similar unit tests in a future iteration if desired.

---

## Functional Test Plan

No functional test plan exists at `/home/dennis-chan/Git/trendora/reports/qa/goal-market-compass-iter-7-test-plan.md`. Standard QA checks completed instead.

---

## Summary

| Category | Result |
|----------|--------|
| Artifacts | All required, valid, consistent |
| Backend tests (test_j10_recovery.py) | 23 passed, 0 failed |
| Backend tests (test_provider_clients.py) | 44 passed, 0 failed |
| Database integrity | All 6 checks passed; zero side effects confirmed |
| Structural gate guarantee | Verified; no code path reaches writes on non-agree verdict |
| Real run execution | Ran against live DB; returned `mismatch` correctly |
| Browser checks | SKIPPED (database damage gate; recovery failed) |
| Code quality | PASS_WITH_NOTES (minor synthetic test gap, not blocking) |

---

## Blockers

None. The iteration correctly executed the fail-closed gate and made zero writes as mandated.

The `mismatch` verdict is an honest outcome per the specification — the tolerance was fixed before the run and CVX's delta exceeded it. This iteration succeeded in catching a real discrepancy and refusing to proceed. No owner action is required to clear this iteration's QA (the gate worked correctly); owner action is required to decide the next step (tolerance review, sample re-scoping, or holding at the 2026-08-10 frontier), which is out of scope for QA.

---

## Recommendation for Next Iteration

Per the developer's handoff, three honest paths forward:

1. **Review the tolerance** — The evidence (min 0.0862%, max 0.8652%, all deltas internally uniform per symbol) suggests 0.75% may be tighter than ordinary quarterly-dividend adjustments on higher-yielding names like CVX. A dated owner decision to adjust `CONVENTION_CHECK_TOLERANCE` would let a re-run pass the gate with zero code changes.

2. **Widen or change the comparison sample** — If the owner judges 20 large-cap tickers an unrepresentative test of "does the convention generally match" versus "does this exact tolerance clear every possible dividend-driven case."

3. **Accept the honest miss and hold** — Defer recovery further, accepting the 2026-08-10 frontier as the final state for this incident.

The retry remains idempotent and correct under any of these paths: `run_gated_recovery()` will re-run the convention check fresh every time, with no stale state to invalidate.

---

**QA Validation Complete**  
2026-08-20 22:35:00Z
