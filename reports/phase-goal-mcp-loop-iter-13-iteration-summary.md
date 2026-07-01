# Iteration Summary — goal-mcp-loop-iter-13

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-01
**Iteration:** 13

## In plain words

**What you can do now:** Browse the stock leaderboard and see "Proven" or "Not yet proven" on every score; tap any Leadership card to read its out-of-sample proof (Leadership Score earned +6.36% vs. SPY); confirm Entry Quality and Risk are honestly labeled "not yet proven"; follow the Breakout-watch setup's certified edge in strong-market conditions; browse the Evidence page with six certified claims and round-trip links to each research surface; see the volatility-contraction pattern marked "Proven" in the Research Factor Lab at both the 20-day and 60-day horizons. The combination lab's "Proven" badge for the certified momentum + proximity-to-high pairing is functionally built and awaiting one final browser confirmation.

**What changed this time:** The Multi-factor combination lab now shows an evidence chip on the composite cohort row — it reads "Proven" only for the one specific certified pairing (relative-strength leaders vs. SPY that are also near their 52-week high, at the 20-day horizon) and "Not yet proven" for everything else you compose. A new 6th row appeared on the Evidence page with that combination's full details: both factor conditions, the out-of-sample "PASS" verdict, a +4.69% holdout edge beating SPY, the registration date, and a link back to the combination lab. A scroll fix was also applied so clicking the badge takes you directly to the right row on Evidence. Core capability is fully built and verified by unit tests and 12/14 browser checks; one browser re-run is pending to confirm the scroll fix.

**What's next:** A short verification pass — re-running the browser checks with the scroll fix in place — will flip the final remaining capability to confirmed and allow the product goal to be declared achieved.

## Headline

J-08 basis landed: combination "Proven" badge + 6th evidence row built; browser scroll re-verification pending

## Direction

**Signal:** holding
**Why:** J-08 moved from unknown to partial — the full combination capability (badge, 6th evidence row, reactive updates, honest "Not yet proven" fallbacks) is built, passes 37/37 unit tests and 12/14 browser checks, and carries zero anti-goal violations. No journey is failing or regressed; J-01 through J-07 are all re-verified passing this iteration. The sole remaining gap is a browser re-run to confirm the auditor's anchor-scroll fix (UT-05/UT-14) before GOAL_ACHIEVED can be declared.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-07 (iter-11)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 2 of last 5 (iter-10, iter-12)

**Latest evaluator reasoning:** iter-13 landed the terminal J-08 basis correctly at the data/logic layer — a genuine, honest 6th canonical PASS (~8x margin over the Bonferroni divisor-6 bar), served proven=true/signal-less through the existing `GET /api/evidence`, with a pure read-side combination resolver (37/37 unit tests) and COHERENCE-PASS. But J-08 is not cleanly browser-verified: the browser-qa lane returned an overall FAIL (UT-05/UT-14 deep-link scroll), phase-closure returned CLOSURE-FAIL, the audit's scroll fix was applied after the browser run and never re-verified, and the "Proven"-badge screenshot is a relabeled default-state frame that actually shows the failed pair reading "Not yet proven." One lean confirmation iteration closes it.

## What was done

- Implemented `CombinationCohort` type, `resolveCombinationEvidence` matcher, `combinationClaimId`/`combinationEvidenceAnchor`, and extended `claimAnchorId`/`claimSurface` with a combination branch in `lib/evidence.ts` (pure, read-side, no fetch)
- Attached a reactive `CombinationEvidenceBadge` ("Proven" / "Not yet proven") to the composite cohort row in `app/research/_labs.tsx`, reading the existing `fetchEvidence` / `claims[]` — no new API endpoint
- 6th canonical ledger entry (rs_spy_3m × high_proximity, composite, h20, PASS, p=0.0009995, +4.69%) written by the post-decompose gate; zero application backend code changed
- `/evidence` combination claim row renders automatically via the existing `ClaimRow` using the new `claimSurface`/`claimAnchorId` combination branch; no structural change to `app/evidence/page.tsx` beyond auditor's scroll fix
- +10 combination unit tests added; 37/37 total frontend unit tests pass; backend ledger-adjacent suite 66+ tests pass; TypeScript clean
- Auditor applied hash-scroll `useEffect` to `app/evidence/page.tsx` so anchor deep-links scroll the target `ClaimRow` into view after async claims load (fixes all evidence deep-links, not just J-08)
- Browser QA: 12/14 tests passed (UT-03/04/06/07/08/09/10/11/12/13 PASS); UT-05 + UT-14 (anchor scroll into viewport) failed pre-fix; scroll fix unverified via browser re-run

## What's left

- Journey J-08 (Multi-factor combination certified edge surfaced on the Combination lab + Evidence) — status partial; needs browser re-verification with scroll fix in place to flip to passing
- Closure blocker: browser QA overall verdict FAIL (UT-05/UT-14) — re-run `browser-qa-phase.sh` with `app/evidence/page.tsx` hash-scroll fix already in tree; confirm UT-05 + UT-14 flip to PASS
- Screenshot hygiene: capture md5-DISTINCT, correctly-labeled screenshots showing (a) the composite "Proven" badge for the certified rs_spy_3m × high_proximity @ h20 selection scrolled into the viewport (compose high_proximity as leg 2 — the default atr_pct pair correctly reads "Not yet proven"), and (b) the 6th `/evidence` combination row scrolled into view

## Next step

iter-14 (LEAN) — verification-only, no new feature code (J-08 is the SOLE remaining Must-have journey):

1. Bring the stack up (frontend :3255, backend :8255) and KEEP the backend up for the entire run — a red "Backend unavailable" pill appeared mid-run in iter-13 (UT-05-fail, UT-06), which would force a fail-safe "Not yet proven" and invalidate any badge reading.
2. Re-run the canonical `browser-qa-agent` lane WITH the audit's `apps/frontend/app/evidence/page.tsx` hash-scroll fix already in the tree; confirm UT-05 + UT-14 flip FAIL → PASS (`./scripts/automation/browser-qa-phase.sh goal-mcp-loop-iter-13`, or the iter-14 equivalent).
3. Capture md5-DISTINCT, correctly-labeled screenshots that actually show: (a) the `/research/factor-combination` composite "Proven" badge for the certified `rs_spy_3m:top:quintile × high_proximity:top:tertile @ h20` selection scrolled into the viewport — compose `high_proximity` as leg 2, since the config default `atr_pct` is the FAILED pair and correctly reads "Not yet proven"; and (b) the 6th `/evidence` combination row scrolled into view.
4. Write a PASS `ui-test-results.md` so phase-closure passes.

On that clean re-run, J-08 flips to `passing` and GOAL_ACHIEVED becomes declarable (J-01..J-07 already non-regressed, coherence COHERENCE-PASS, zero anti-goal violations).

## Quick verify

From `reports/phase-goal-mcp-loop-iter-13-what-to-click.md`:

1. Navigate to `http://localhost:3255/research/factor-combination`
2. Scroll down to the composite cohort row at the bottom of the table. Note the badge with the default factor selection (rs_spy_3m × atr_pct).
3. Change the horizon selector to 20, set Leg 1 to rs_spy_3m / top / quintile, and set Leg 2 to high_proximity / top / tertile. Then scroll back to the composite cohort row.
4. Click the "Proven" badge (the link inside it).
5. On the `/evidence` page, verify the 6th row contains chips for rs_spy_3m:top:quintile and high_proximity:top:tertile, a "PASS" verdict badge, holdout edge "+4.69%", control vs. SPY "+4.69%", registration date "2026-07-01", forward-walk status "Pending", and a linkback reading "Backs: Multi-factor combination lab →".

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-13.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-13-dev.md |
| Review | PASS | reports/reviews/goal-mcp-loop-iter-13-review.md |
| Browser QA | FAIL | reports/phase-goal-mcp-loop-iter-13-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-13-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-13-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-13-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-13-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-13-ui-test-plan.md |
| QA | PASS_WITH_NOTES | reports/qa/goal-mcp-loop-iter-13-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-mcp-loop-iter-13-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-mcp-loop-iter-13-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-mcp-loop/iter-13/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
