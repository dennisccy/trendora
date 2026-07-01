# Iteration Summary — goal-mcp-loop-iter-14

**Verdict:** GOAL_ACHIEVED
**Iteration type:** goal-lean
**Date:** 2026-07-01
**Iteration:** 14

## In plain words

**What you can do now:** Browse the stock leaderboard and see "Proven" or "Not yet proven" on every score. Expand the proof panel on any Leadership card to read the sealed out-of-sample evidence (+6.36% vs. SPY). Confirm that signals without a certified track record are honestly labeled "not yet proven." Follow the Breakout-watch setup's certified edge in strong-market conditions. Browse the Evidence page with six certified research results, each with round-trip links to the research surface that backs it. See the volatility-contraction pattern marked "Proven" in the Research Factor Lab at both the 20-day (+3.33%) and 60-day (+8.91%) horizons. Use the Multi-factor combination lab to compose two-factor strategies and see an honest badge — "Proven" only for the certified momentum-and-proximity-to-high pair, "Not yet proven" for everything else — and click through to the matching Evidence row showing +4.69% out-of-sample edge.

**What changed this time:** The combination lab's "Proven" badge and its deep-link to the Evidence page were confirmed working end-to-end. Clicking the badge now scrolls the matching Evidence row neatly into view, fixing the scroll issue from the previous round. No new features were added — this round was purely about confirming what was already built actually works as intended.

**What's next:** The goal is complete. If the team decides to extend the product further, any new certified trading edge will go through the same rigorous pre-registered testing process before showing up here.

## Headline

J-08 clean browser-verified: combination "Proven" badge + deep-linked 6th Evidence row confirmed — GOAL_ACHIEVED

## Direction

**Signal:** improving
**Why:** J-08 flipped from `partial` to `passing` in this iteration, the sole remaining Must-have journey. The hash-scroll fix committed in iter-13 was confirmed sufficient via a live DOM measurement (scrollY=1034, combination row fully in viewport). All eight Must-have journeys (J-01 through J-08) are now `passing` with no anti-goal violations, satisfying the GOAL_ACHIEVED condition.

**Trend (last 5 iters):**
- Newly passing this iter: J-08
- Newly passing in last 5 iters total: J-07 (iter-11), J-08 (iter-14)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 2 of last 5 (iter-12 and iter-13 moved J-08 to `partial` but did not flip a journey to `passing`)

**Latest evaluator reasoning:** iter-14 delivered the clean, backend-up browser verification the iter-13 evaluator asked for, flipping the SOLE remaining Must-have journey J-08 from `partial` to `passing`. The `/research/factor-combination` composite "Proven" badge renders for the certified `rs_spy_3m:top:quintile × high_proximity:top:tertile @ h20` selection (composed in-frame, not the default `atr_pct` pair), and the 6th `/evidence` combination row renders every standard field with numbers that byte-match the ledger. All seven required-still-passing journeys hold; no anti-goal is violated; coherence is COHERENCE-PASS. Every Must-have journey (J-01..J-08) is now `passing` — GOAL_ACHIEVED.

## What was done

- Brought the stack up on canonical QA ports (backend :8255, frontend :3255) using a fresh production build; held the backend up for the entire browser run
- Confirmed `GET /api/evidence` returns exactly 6 claims with the combination row (`proven=true`, `signal=null`, `holdout_edge=0.046932`, `p_value=0.0009995`) — no app code changed, `certified-claims.jsonl` byte-identical
- Verified the default combination (leg 2 = `atr_pct`) badge reads `data-proven=false` "Not yet proven" — honest-marking confirmed
- Composed the certified selection (`rs_spy_3m:top:quintile × high_proximity:top:tertile @ h20`); confirmed badge flips to `data-proven=true` "Proven" with correct `data-legs` and deep-link href
- Confirmed the committed hash-scroll `useEffect` (evidence/page.tsx L57-63) auto-scrolls the 6th combination `ClaimRow` fully into the viewport on deep-link (scrollY=1034, row rect top=591/bottom=876/vh=900)
- Verified displayed numbers byte-match the ledger (+4.69% edge, +4.69% SPY control, p=0.0009995 < alpha/6=0.008333, register 2026-07-01)
- Ran 37/37 evidence unit tests green with expectation tests UNEDITED; confirmed `/stocks` has 0 combination-badge leakage and 360 inline evidence-status badges
- Verified 1 target journey (J-08) passes browser QA via the canonical browser-qa-agent lane

## What's left

- All Must-have journeys passing, no closure blockers.

## Next step

Halt — goal achieved. Every Must-have user journey (J-01 through J-08) has positive `passing` evidence, no anti-goal is violated, and coherence is COHERENCE-PASS. J-08 was the terminal journey; its clean browser verification opens and satisfies the GOAL_ACHIEVED gate. If the operator has opted into the continuous-improvement goal-self-extension loop, the next proposed journey should follow the pre-registered candidate-set discipline (never an ad-hoc data-mined cohort) and route through the staging ledger first — do NOT append another canonical claim casually, since each one permanently tightens the Bonferroni bar (now divisor 6 → 7).

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-14.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-14-dev.md |
| Review | PASS | reports/reviews/goal-mcp-loop-iter-14-review.md |
| Browser QA | PASS | reports/phase-goal-mcp-loop-iter-14-ui-test-results.md |
| Goal evaluation | GOAL_ACHIEVED | runs/goal-session-mcp-loop/iter-14/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
