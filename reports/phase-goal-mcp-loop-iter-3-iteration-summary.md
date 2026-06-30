# Iteration Summary — goal-mcp-loop-iter-3

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-06-30
**Iteration:** 3

## In plain words

**What you can do now:** Browse a ranked list of stocks and see a clear "Proven" or "Not yet proven" badge beside the Leadership, Entry Quality, and Risk score for every row. Click any stock to open its detail page, then tap "Why proven?" on the Leadership card to read the out-of-sample test that earned it that label — a statistical PASS, a +6.36% edge over 12,297 observations, a very small p-value (~0.0005), and a comparison against the S&P 500 as a control. Entry Quality and Risk are honestly shown as "Not yet proven" with no drill-down, so there is no risk of seeing invented proof. Visit the Evidence page from the sidebar to read the full certified claim in one place, and follow the links back and forth to the stock rankings.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The automated browser-test system was fixed so it could actually photograph the evidence features working in a real browser. The "Proven" badge, proof panel, and Evidence page were already built; this round confirmed all 16 browser checks pass and that every number displayed matches the backend exactly.

**What's next:** Next we'll build a regime-conditioned evidence claim — surfacing proof that a factor's edge holds specifically in the current market regime — so the last outstanding user journey can be verified and the goal can be declared achieved.

## Headline

QA bring-up hardened (`next start`); browser lane runs clean — J-02 + J-05 newly passing; 16/16 PASS

## Direction

**Signal:** improving
**Why:** J-02 (proof drill-down) and J-05 (evidence ledger) moved from unknown/partial to passing this iteration, both backed by real screenshots and 16/16 browser test passes with zero skips. J-01 and J-03 were re-confirmed fresh after the iter-2 skip. The only remaining journey is J-04 (regime-conditioned evidence), which has a clear and tractable path forward via the post-decompose referee gate in iter-4.

**Trend (last 4 iters):**
- Newly passing this iter: J-02, J-05
- Newly passing in last 4 iters total: J-01 (iter-1), J-03 (iter-1), J-02 (iter-3), J-05 (iter-3)
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: none
- Iters with no journey state change: 1 of last 4 (iter-2, browser lane skipped all tests)

**Latest evaluator reasoning:** The iter-2 hard verification gap is closed — the browser-QA lane actually ran this time (browser_checks_run=true, 16/16 PASS, 0 skipped, real populated screenshots, telemetry record present). J-02 and J-05 are newly passing; J-01/J-03 are re-confirmed fresh. Anti-goal check PASS and Coherence PASS with zero apps/ source diff. Not GOAL_ACHIEVED: J-04 is a Must-have journey still unknown — it has never been attempted and has no backing certified claim.

## What was done

- Diagnosed the iter-2 bring-up failure: `next dev` dev-vs-prod `.next` clobber under concurrent full-pipeline fanout caused the browser lane to emit all-SKIP ("Frontend not running")
- Fixed `scripts/start-frontend.sh`: switched from `next dev` to stamp-guarded `next start`, serving a pre-built production bundle (ready in 249 ms, no per-request compile, no clobber race); stamp file `.next/.qa-serve-base` detects stale builds and self-heals within the harness budget
- Pre-flight bring-up gate confirmed before browser lane: `/api/health` → 200, `/api/evidence` → `proven_signals.leadership_score.proven == true`, `/stocks` → 120 leaderboard rows
- Ran browser-QA lane: 16/16 tests PASS, 0 skipped, real screenshots captured in `reports/qa/goal-mcp-loop-iter-3-evidence/`
- Backend unit tests: 12 passed (evidence resolver + API, including empty-ledger-200 invariant); frontend unit tests: 21 passed (transpiled via tsc due to missing `tsx`)
- Verified 4 target journeys pass browser QA (J-01, J-02, J-03, J-05); zero app-source diff — verification-only iteration

## What's left

- Journey J-04 (Regime-conditioned evidence) — unknown; no regime-scoped certified claim exists yet; sole remaining Must-have journey before GOAL_ACHIEVED is reachable
- Frontend test runner needs `tsx` as a devDependency so `node lib/*.test.ts` runs without manual TypeScript transpile workaround (reviewer NOTE; non-blocking)
- Browser-QA should scroll below-fold disclosures into viewport before capturing screenshots — J-02 proof panel was confirmed via DOM assertions rather than a pixel capture of the expanded panel; directly relevant to J-04's regime panel next

## Next step

Run **iter-4 (full)** to tackle **J-04 (regime-conditioned evidence)** — the single remaining Must-have journey. The iteration spec MUST include a narrow, regime-conditioned `## Evidence Claim` (a regime-scoped cohort, e.g. a factor decile conditioned on the current Risk-on regime) so the post-decompose gate runs the referee BEFORE any code is built; prefer a narrow regime slice over a broad data-mined one (the referee counts independent holdout dates and will refuse a thin sample). On a PASS, surface the regime-conditioned evidence labeled with the regime it holds in (J-04 acceptance), reachable from the Dashboard regime + the Evidence/Research surface. If the gate returns FAIL/INSUFFICIENT the iteration is blocked — that is the correct anti-overfit behavior, and the next attempt should propose a different narrow regime cohort. Once J-04 is browser-proven, all five Must-have journeys pass and GOAL_ACHIEVED becomes reachable. Depth = full because J-04 introduces a new certified claim through the referee gate AND a new regime-labeled surface (needs ui-impact → ui-test-design → browser-qa → ux-regression → closure), and it is the last journey before completion.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-3.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-3-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-mcp-loop-iter-3-review.md |
| Browser QA | PASS | reports/phase-goal-mcp-loop-iter-3-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-3-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-3-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-3-what-to-click.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-3-qa.md |
| Goal evaluation | CONTINUE | runs/goal-session-mcp-loop/iter-3/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
