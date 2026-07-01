# Iteration 13 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

iter-13 landed the terminal J-08 basis correctly at the data/logic layer — a genuine, honest 6th canonical PASS (the `rs_spy_3m × high_proximity` composite, promoted with ~8x margin over the Bonferroni divisor-6 bar), served proven=true/signal-less through the existing `GET /api/evidence`, with a pure read-side combination resolver (37/37 unit tests) and COHERENCE-PASS. But J-08 is **not cleanly browser-verified**: the browser-qa lane returned an overall **FAIL** (UT-05/UT-14 deep-link scroll), phase-closure independently returned **CLOSURE-FAIL**, the audit's scroll fix was applied *after* the browser run and never re-verified, and the "Proven"-badge screenshot is a relabeled default-state frame that actually shows the *failed* pair reading "Not yet proven." The substantive capability is very likely correct; the *verification* is not clean enough to declare the terminal goal achieved. One lean confirmation iteration closes it.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing (re-verified, non-regressed) | reports/qa/goal-mcp-loop-iter-13-evidence/UT-12-stocks-result.png |
| J-02 | passing | passing (re-verified, non-regressed) | reports/qa/goal-mcp-loop-iter-13-evidence/UT-12-stocks-result.png |
| J-03 | passing | passing (reinforced) | reports/qa/goal-mcp-loop-iter-13-evidence/UT-03-result.png |
| J-04 | passing | passing (re-verified) | reports/qa/goal-mcp-loop-iter-13-evidence/UT-10-result.png |
| J-05 | passing | passing (extended to 6 rows) | reports/qa/goal-mcp-loop-iter-13-evidence/UT-10-result.png |
| J-06 | passing | passing (re-verified) | reports/qa/goal-mcp-loop-iter-13-evidence/UT-10-result.png |
| J-07 | passing | passing (re-verified) | reports/qa/goal-mcp-loop-iter-13-evidence/UT-10-result.png |
| J-08 | unknown | **partial** (not cleanly browser-verified) | reports/qa/goal-mcp-loop-iter-13-evidence/UT-05-fail.png |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Nothing shown proven without a passing certified-claim | OK | 6th row backed by a real referee PASS; every other combination reads "Not yet proven" (UT-04/08/09 DOM; the UT-03 pixel literally shows the default failed pair as "Not yet proven"). |
| Decision-quality only (no return/price/buy-sell) | OK | Honest title "rs_spy_3m × high_proximity — composite", subtitle "Out-of-sample edge" (audit + coherence confirm). |
| Displayed numbers correct (byte-match engine) | OK | +4.69% byte-matches ledger `holdout_edge=0.046932` / `control_excess=0.046932` (QA + audit curl-verified; UT-06 DOM). |
| No overfit edges (survived referee) | OK | Sealed OOS holdout + SPY control + Bonferroni divisor 6; p=0.0009995 < 0.008333, ~8x margin. |
| Preserve determinism / no-lookahead | OK | `git diff HEAD -- apps/backend/app` is empty; no engine change. |
| No iteration ships if evidence-claim lacks a passing referee verdict | OK | The claim is a genuine PASS (honest-stop guard satisfied). |
| No hard-coded credentials/keys/tokens | OK | None observed in the diff. |

## Next-Step Recommendation

iter-14 (LEAN) — verification-only, no new feature code (J-08 is the SOLE remaining Must-have journey):

1. Bring the stack up (frontend :3255, backend :8255) and KEEP the backend up for the entire run — a red "Backend unavailable" pill appeared mid-run in iter-13 (`UT-05-fail`, `UT-06`), which would force a fail-safe "Not yet proven" and invalidate any badge reading.
2. Re-run the canonical `browser-qa-agent` lane WITH the audit's `apps/frontend/app/evidence/page.tsx` hash-scroll fix already in the tree; confirm **UT-05 + UT-14 flip FAIL -> PASS** (`./scripts/automation/browser-qa-phase.sh goal-mcp-loop-iter-13`, or the iter-14 equivalent).
3. Capture md5-DISTINCT, correctly-labeled screenshots that actually show: (a) the `/research/factor-combination` composite **"Proven"** badge for the certified `rs_spy_3m:top:quintile × high_proximity:top:tertile @ h20` selection scrolled into the viewport — compose `high_proximity` as leg 2, since the config default `atr_pct` is the FAILED pair and correctly reads "Not yet proven"; and (b) the 6th `/evidence` combination row scrolled into view.
4. Write a PASS `ui-test-results.md` so phase-closure passes.

On that clean re-run, J-08 flips to `passing` and **GOAL_ACHIEVED becomes declarable** (J-01..J-07 already non-regressed, coherence COHERENCE-PASS, zero anti-goal violations).

## Halt Justification (if halting)

Not halting. CONTINUE — real progress was made (the terminal J-08 certified basis and its badge/row code landed and passed review + unit tests + coherence with zero anti-goal violations), and a single tractable, verification-only remediation remains. This is explicitly **not** GOAL_ACHIEVED: the browser-qa verdict is FAIL, phase-closure is CLOSURE-FAIL, the audit's scroll fix is unverified (no re-run), and the "Proven"-badge pixel evidence is a mislabeled default-state frame — so J-08 lacks the clean positive verification the terminal gate requires. It is **not** a REGRESSION: the deep-link scroll gap is pre-existing and product-wide (it equally affects the already-passing J-02/J-05/J-06/J-07 deep-links) and iter-13 improved it; no previously-passing journey now fails and the prior 5 ledger rows are byte-identical.
