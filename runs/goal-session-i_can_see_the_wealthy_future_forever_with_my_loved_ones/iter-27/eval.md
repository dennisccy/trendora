# Iteration 27 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

J-85 (confirm-gated regenerate-from-scratch snapshot rebuild + universe-vs-latest coverage diagnostic) lands fully verified: the coverage diagnostic, the confirm-gated rebuild panel/modal with a persistently-visible Confirm, and the offline-proven clear-then-create-once orchestration (seed untouched, deterministic, no in-place UPDATE) all pass. J-86's data-correctness is correct and complete everywhere — five MDD columns (all ≤ 0, NA-honest) on /stocks, /themes, /sectors and Stock Detail, byte-identical to Backtest, plus aggregate mean-MDD on Backtest and Research — BUT two of its UI acceptance sub-legs failed browser QA: the client-side MDD column sort does not reorder (UT-03/UT-09) and the colour-grading is flat rather than graduated by magnitude (UT-04, source-confirmed). The full backend suite is GREEN (878 passed, 0 failed, EXIT_CODE=0) and coherence is COHERENCE-PASS, so this is a small frontend consolidation away from GOAL_ACHIEVED — not a regression, not done.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-85 | failing | passing | reports/qa/.../iter-27-evidence/UT-14-data-page-before.png, UT-16-18-modal.png; apps/backend/tests/test_iter27_rebuild_mdd.py (13 passed: clear-then-create-once, seed untouched, deterministic, coverage diagnostic) |
| J-86 | failing | partial | PASS data legs: UT-01/02/05/06/07/08/10/11/12/13/21/22 (MDD columns ≤0, NA-honest, matches Backtest, aggregate mean-MDD). FAIL UI legs: UT-03/UT-09 (MDD sort no-op), UT-04 (flat colour grading, source-confirmed in forward-return.tsx mddClass) |
| J-48 | passing | passing (sort re-verify owed) | Sort code path byte-unchanged by iter-27 (additive mdd_ branch only; onSort/SortHeader/sorted memo untouched); passed iter-23 (themes/sectors) + iter-20 (TC-09 /stocks). UT-20 reported fwd-sort no-op but the XPath `button[text()='5d']` cannot match a button whose label is in a nested span — selector/env artifact most likely, must be re-verified next iter |
| J-75 | passing | passing (sort re-verify owed) | Same shared sort path as J-48; data columns intact (UT-22 row values change with as-of nav) |
| J-06 | passing | passing | UT-13 RSP / UT-11 Backtest summary MDD matches; coherence: _leadership_returns single builder; test_iter27_rebuild_mdd J-06 identity test |
| J-08 | passing | passing | clear_snapshot_set asserts bars_before==bars_after (seed never deleted); rebuild is clear-then-create-once, no in-place UPDATE (data_manager.py:828-852) |
| J-18 | passing | passing | No asof-provider/switcher/calendar in the diff; UT-22 back-arrow date nav drives the single global as-of; rebuild dates are job params, not a date control |
| J-81 | passing | passing | themes/sectors fwd-return columns intact; MDD rides the same _leadership_returns builder (coherence PASS) |
| J-05, J-09, J-21, J-29, J-63, J-77, J-82, J-17, J-33, J-34, J-35, J-36, J-37, J-38, J-39, J-40, J-41, J-46, J-53, J-59, J-60, J-66, J-67, J-68 | passing | passing (carried) | Backend diff is additive (new MDD column + rebuild kind); full suite GREEN 878 passed proves the scanner/forward-test/data-manager modules unregressed; no served value for these journeys changed |
| J-22 / J-23 / J-24 | unknown | unknown (blocked-NA) | Data-walled, non-vetoing per goal.md |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No lookahead | OK | MDD helper shares the same bars-after (date > D) window + NA gate as forward_return; full suite (incl. no-lookahead determinism tests) GREEN |
| Snapshots are immutable (rebuild = create-once, never in-place UPDATE) | OK | clear_snapshot_set does whole-row deletes (children before parents) then create-once recompute; never UPDATEs a retained snapshot row (data_manager.py:825-852); coherence PASS |
| Single source of truth | OK | max_drawdown computed once in forward_testing.max_drawdown; read verbatim on every surface; no competing computation (coherence Step 1) |
| No recompute in the read path | OK | snapshot_serving / research read fr.max_drawdown verbatim; no client-side drawdown calc (coherence) |
| No fabricated data; committed PRICE seed never deleted | OK | clear_snapshot_set never references daily_prices + asserts bars_before==bars_after; _parse_cap/MDD never synthesize; MDD NA when realized_return NA |
| Honest forward-test for partial windows (incl. MDD) | OK | MDD NULL exactly when realized_return absent (UT-12 low-n rows show NA; latest as-of NA) |
| No magic numbers | OK | only `0.0` in forward_testing.py is inside a comment (line 161); no hardcoded horizon list; test_no_magic_numbers in the GREEN suite |

## Next-Step Recommendation

Run a **lean** frontend-only consolidation (J-86 finish):
1. **Fix MDD colour grading (UT-04, confirmed defect):** `apps/frontend/components/forward-return.tsx` `mddClass()` returns a flat `text-neg` for all negatives — make it graduate by magnitude per the iter-27 spec ("colour-graded by magnitude (≤ 0)"). Use design tokens only (no hardcoded hex — J-70/J-74 token discipline). If a graduated scale is deliberately out of scope, the spec wording must be reconciled; otherwise grade it.
2. **Re-verify the column sort with CORRECT selectors and FIX if genuinely broken (UT-03/UT-09/UT-20):** the sort code path is byte-unchanged from what passed in iter-23/iter-20, and the failing browser-QA used `//th//button[text()='5d']` which cannot match a button whose label is in a nested `<span>`. Re-test by resolving the SortHeader button by its `aria-label` ("Sort by 5d", "Sort by 5d MDD") and assert the rendered row order changes (and the `data-testid="sort-indicator"` flips). Confirm J-48/J-75 forward-return sort still works (no genuine regression) and the new MDD columns sort NA-last.
3. Re-smoke the J-86 data legs (already PASS) only as needed; the backend is done and the full suite is GREEN — no backend change should be needed, so a lean depth is correct.

After the colour grading is graduated, the sort is confirmed working on all five MDD columns (and J-48/J-75 fwd-return sort confirmed unregressed), with COHERENCE-PASS and the suite still GREEN, J-86 flips to `passing` and every buildable Must-have is green — the next evaluation is a GOAL_ACHIEVED candidate (J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing).

Evidence-hygiene for next iter QA: the iter-27 evidence dir had multiple `-cors-block.png` frames (transient connectivity) and shared-byte frames (UT-08 cites UT-09-sectors-sort-fail.png; UT-21 cites UT-22-asof-nav-mdd.png) — md5sum first, resolve sort buttons by aria-label not text(), and capture the colour-graded MDD cells full-viewport wide (they sit to the RIGHT of the fwd-return columns).

## Halt Justification (if halting)

Not halting. CONTINUE: J-85 newly passing (progress made), J-86 partial with two tractable frontend defects (one source-confirmed colour-grading miss; one sort no-op that must be re-verified vs a likely selector artifact). No critical anti-goal violation, COHERENCE-PASS, full suite GREEN — so neither GOAL_ACHIEVED (J-86 acceptance legs not yet green) nor REGRESSION (sort path byte-unchanged; UT-20 not a confident regression) applies.
