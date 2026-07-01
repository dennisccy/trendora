# Iteration Summary — goal-mcp-loop-iter-12

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-01
**Iteration:** 12

## In plain words

**What you can do now:** Browse the stock leaderboard and see "Proven" or "Not yet proven" on every score; expand the proof panel on any Leadership stock card to read the sealed out-of-sample evidence; confirm that Entry Quality and Risk are honestly marked "not yet proven"; follow the Breakout-watch setup's certified regime edge on the Evidence page; browse all five certified claims with round-trip links to each research surface; and see the volatility-contraction pattern marked "Proven" in the Research Factor Lab at both the 20-day and 60-day horizons, while all shorter horizons and most other factors honestly read "not yet proven."

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The app's statistical referee was extended to test two-factor combinations of stock characteristics. A small, fixed, pre-approved shortlist of three combinations was run through the same strict out-of-sample check that guards all live evidence badges. Two of the three did not hold up; the third — momentum leaders that are also near their 52-week high — passed comfortably, giving the next iteration a real, evidence-backed winner to show users on the Combination lab and Evidence pages.

**What's next:** Next we'll show users a certified two-factor combination edge on the Combination lab and Evidence pages, completing the final milestone in the product's evidence surface.

## Headline

Combination staging explorer built; rs_spy_3m + high_proximity clears the canonical divisor-6 bar, giving iter-13 a promotable winner

## Direction

**Signal:** holding
**Why:** Iter-12 is a deliberate discovery/enablement milestone by design — no journey flipped to passing (J-08 stays `unknown` per the proven two-step discover→surface pattern). J-01 through J-07 remain passing with zero regressions, verified via byte-identical canonical output and unedited DO-NOT-EDIT test suites. J-08 now has a real recorded staging winner (rs_spy_3m + high_proximity, p ≈ 0.001, clears the divisor-6 bar with margin) ready for promotion in iter-13; no journeys are failing, so direction is on course.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-06 (iter-8), J-07 (iter-11)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 2 of last 5 (iter-10, iter-12)

**Latest evaluator reasoning:** iter-12 delivered exactly its scoped, backend-only discovery/enablement deliverable — the deferred "combinations" half of goal.md Part B Phase 1 — cleanly through the full pipeline (Review PASS, QA PASS 134/134, Audit PASS, Closure passed, coherence COHERENCE-PASS). It landed the previously-missing recorded staging basis that J-08 promotion needs: a FIXED pre-registered 3-pair 2-factor combination candidate set was certified through the UNCHANGED referee into the internal staging ledger (4→7 entries), producing one real promotable winner. No journey flips this iteration — by design — so NOT GOAL_ACHIEVED (J-08 stays `unknown`); no regression, no anti-goal violation, and a concrete tractable next step exists (surface J-08 in iter-13).

## What was done

- Registered a FIXED pre-registered 2-factor combination candidate set in a new `config.triad.combination_candidates` block (3 pairs: rs_spy_3m+atr_pct, leadership_score+atr_pct, rs_spy_3m+high_proximity; each with horizon 20, direction positive, and economic rationale)
- Mirrored the same three pairs verbatim into `project-extensions/proposer-guidance.md` §4.2 — the anti-data-mining keystone (fixed set only, never the full factor × pair × horizon cross-product)
- Implemented `explore_combination_staging` and `_combination_staging_candidates` in `triad_scan.py` as clean siblings to the single-factor explorer; reused the unchanged referee cert path; `verify_edge` stays the sole ledger writer
- Extended the fail-closed canonical-path guard to the combination explorer (raises `ValueError` if pointed at the canonical ledger path)
- Ran all three pre-registered combinations through the referee under LORD++ FDR economy; staging ledger grew 4→7 entries: rs_spy_3m+atr_pct FAIL (p≈0.727, holdout −0.0046), leadership_score+atr_pct FAIL (p≈0.791, holdout −0.0067), rs_spy_3m+high_proximity PASS (p≈0.0010, holdout +0.0469, clears divisor-6 canonical bar with margin)
- Added 4 new combination-explorer unit tests; 134 tests passed total (0 failed); DO-NOT-EDIT suites (test_referee.py, test_forward_walk.py, test_evidence.py) unedited and green
- Re-verified J-01..J-07 via the byte-identity / frozen-golden path: canonical `certified-claims.jsonl` (5 entries) and `proven_signals` byte-identical; zero diff on all serving and compute paths

## What's left

- Journey J-08 (Multi-factor combination certified edge surfaced on the Combination lab + Evidence) — status: `unknown`; discovery prerequisite complete this iter; surfacing deferred to iter-13

## Next step

iter-13 (FULL) — surface J-08 and reach GOAL_ACHIEVED. Promote the SINGLE recorded staging winner — `rs_spy_3m:top:quintile` + `high_proximity:top:tertile` (staging-ledger.jsonl #7, raw block-bootstrap p=0.0009995, holdout +0.0469) — to the canonical ledger via a `## Evidence Claim` that sets `"ledger":"canonical"` EXPLICITLY (iter-9b lesson: an omitted key silently re-stages and never surfaces). It faces Bonferroni divisor 6 (required_p ≈ 0.00833); the recorded raw p clears it with margin. Then surface J-08 on `/research/factor-combination` (composite-cohort "Proven" badge) + a new `/evidence` combination claim row — both as additional READERS of the SAME `GET /api/evidence` payload (no new module/endpoint). Read the recorded staging verdict; do NOT recompute. HONEST-STOP GUARD: if the winner no longer clears the divisor-6 bar against fresh data, report it rather than force an overfit promotion (anti-goal #1/#4). BROWSER-QA HARD REQUIREMENT (recurring iter-3/iter-11 lesson): scroll each asserted badge/row into the viewport and capture DISTINCT screenshots (md5-check them) — do not accept a single relabeled full-page frame. GOAL_ACHIEVED becomes reachable the moment J-08 lands browser-verified with J-01..J-07 non-regressed.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-12.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-12-dev.md |
| Review | PASS | reports/reviews/goal-mcp-loop-iter-12-review.md |
| Browser QA | SKIPPED | reports/phase-goal-mcp-loop-iter-12-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-12-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-12-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-12-what-to-click.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-12-qa.md |
| Audit | PASS | docs/handoffs/goal-mcp-loop-iter-12-audit.md |
| Closure | PASS | reports/phase-goal-mcp-loop-iter-12-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-mcp-loop/iter-12/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
