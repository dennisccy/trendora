# Iteration Summary — goal-ops-hardening-iter-75

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-08-13
**Iteration:** 75

## In plain words

**What you can do now:** Import stock data for any date range with no hidden day limits, and see an honest message when there's nothing new to fetch. The app always shows a real status while it starts up instead of a blank screen, pages load only what they need, and heavy calculations run safely in the background without crashing the app. Backtest results appear instantly from storage with a "Refreshing" note while new numbers compute, and a clear on-screen notice tells you when the app is doing background work and when it finishes.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round: the team recaptured fresh proof screenshots of the Backtest page and the background-work status notice, watching both live for the first time since round 72, to confirm they still work correctly.

**What's next:** Next, the team will try to track down and fix a glitch in the automated testing setup that sometimes shows a broken, unstyled page during checks, and tighten a couple of the automatic checks themselves so they actually catch a real problem. No new product feature is planned right away — it's now the owner's turn to decide whether a list of small self-review housekeeping notes should keep the project from being called finished.

## Headline

Evidence-only iteration: no code changes were planned or made.

## Direction

**Signal:** holding
**Why:** All eight Must-have journeys remain passing, and J-08 and J-09 got their own fresh browser-QA evidence for the first time since iter-72, closing a two-round evidence gap (ledger entries iter-73/c and iter-74/b closed). But the round's actual job — root-causing the intermittent asset-less QA-frontend defect (iter-72/c) — went unattempted: the engine ran an evidence-only micro-path with zero developer/reviewer work and an empty product diff, so the defect merely failed to recur rather than being fixed. No journey regressed and none remain failing, so this reads as holding rather than improving.

**Trend (last 2 iters):**
- Newly passing this iter: none — all eight journeys entered and left the round already `passing`.
- Newly passing in last 2 iters total: J-07 (moved partial → passing in iter-74)
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: iter-74 opened 4 new (minor), closed 2; iter-75 opened 4 new (minor), closed 2 — 0 unresolved critical throughout
- Iters with no journey state change: 1 of last 2 (iter-75; iter-74 moved J-07 to passing)

**Latest evaluator reasoning:** "Good news first: all eight must-have journeys were checked this round and all eight passed, and for the first time since round 72 the two journeys about the backtest page and the background-work notice — J-08 'Backtest page always shows saved results, never waits for a fresh calculation' and J-09 'The app says when it is doing work in the background' — were watched live and photographed working. Every picture I opened shows the real, fully-drawn app; the broken, half-loaded pages that spoiled the last three rounds did not appear once. I re-checked the important numbers against the database myself and they match exactly."

## What was done

- Product changes: No product change this iteration.
- Re-verified all eight Must-have journeys (J-01, J-03–J-09) end to end; merged browser QA PASS 8/8 (0 skipped) and deterministic replay 8/8 PASS — the first clean replay round in four.
- J-08 and J-09 got their own first-party fresh evidence for the first time since iter-72, clearing `evidence_makeup` on both and ending a two-round durability carry.
- J-07 stays passing, carried on iter-74's memory-margin drill (4,724 MB peak vs 8,192 MB cap, 42.33% headroom) under an empty product diff — its golden re-tests only two page-render steps, not a fresh functional check.
- Closed 2 anti-goal ledger entries (iter-73/c, iter-74/b — "required journeys must have their own fresh evidence"); opened 4 new minor entries (depth/DoD mismatch, duplicate walkthrough frames, thin J-07/J-09 goldens, 15th consecutive over-budget round).
- Verified 2 target journeys (J-08, J-09) pass browser QA with fresh evidence; all 6 required-still-passing journeys (J-01, J-03–J-07) also re-verified passing.

## What's left

- Root-cause and fix the intermittent asset-less QA-frontend serving defect (iter-72/c, carried 3+ rounds) — it did not recur this round but remains undiagnosed and unrepaired.
- Give J-07's and J-09's goldens real assertions so deterministic replay can actually detect a regression in either (iter-75/c) — J-07's golden only checks two page-render words, J-09's passes against an idle panel.
- File TC-10's `/data` honest-fallback screenshot, or remove the unguarded fault hook at `apps/backend/app/api/data.py:119` with its test (iter-72/b, carried).
- Delete the stray zero-byte `=` file at the repo root (iter-74/c, carried a 3rd round).
- Clear `state/goldens-regen-pending` — it still names J-05..J-09 though all five now pass; regeneration was always the wrong fix.
- Fix the walkthrough recorder — it saved byte-identical before/after frames for both transitions this round (iter-75/b), so neither is actually depicted.
- 133 unresolved (minor, 0 critical) anti-goal ledger entries remain — the sole literal blocker on GOAL_ACHIEVED; the owner is asked whether housekeeping notes should count.
- Owner decisions still pending: scope of the 2-second health-ceiling promise for long vs. short jobs; B-1107 (limiting concurrent heavy computations); permission to fix the `browser-qa-phase.sh` ordering bug; a cost decision after 15 consecutive over-budget rounds.

## Next step

Run iteration 76 at lean depth, this time with a developer, and complete the work this round skipped: (1) root-cause and fix the intermittent asset-less QA-frontend defect using the frontend's own start-up log, ruling the "rebuild-while-serving" theory in or out; (2) strengthen J-07's and J-09's golden checks so replay can actually detect a regression in either; (3) two carried one-liners — delete the stray zero-byte `=` file, and file TC-10's `/data` honest-fallback screenshot or remove the unused fault hook; (4) clear the stale `goldens-regen-pending` list; (5) rides along, never the goal: proper walkthrough frames for J-05/J-07/J-08/J-09 and J-06's page timings; (6) after that, one full round to show data-freshness age on the readiness badge — the first user-visible change queued in a while. The owner is asked to decide whether the 133 open (minor, non-critical) housekeeping notes should keep blocking a GOAL_ACHIEVED call, plus the carried decisions on the health-ceiling policy, the B-1107 concurrency cap, the `browser-qa-phase.sh` ordering fix, and the cost overrun.

## Assumptions made

- iter-75 · goal-evaluator (2 of 2) — Ambiguity: the rule to clear `evidence_makeup` "the moment a fresh capture lands" conflicts with J-01 and J-07 still showing the same capture defects as before, and J-07's golden turns out to be only a two-step smoke test rather than a real re-verification. We chose: clear `evidence_makeup` on J-08/J-09 (genuinely cured), re-derive it as true on J-01/J-07 (still defective), and advance J-07's `last_verified_iter` to iter-75 while flagging in its gap that the round did not actually re-test it. Reversible: yes.
- iter-75 · goal-evaluator (1 of 2) — Ambiguity: whether "no unresolved anti-goal violation" (which blocks GOAL_ACHIEVED) means any unresolved ledger entry of any severity, or only unresolved breaches of an actual anti-goal — most of the 133 open entries are process/housekeeping notes, not product breaches. We chose: the literal reading (any unresolved entry blocks), keeping the verdict CONTINUE, and put the narrower-reading tension to the owner as an explicit choice rather than deciding it unilaterally. Reversible: yes.
- iter-74 · goal-evaluator (2 of 2) — Ambiguity: J-08 and J-09 got no valid evidence of their own for a second consecutive round; may a durability carry be renewed indefinitely once every other journey is passing. We chose: hold both passing on durability, keep `evidence_makeup` true, freeze `last_verified_iter` at iter-72, and name the pair as an explicit stated blocker on GOAL_ACHIEVED rather than let the carry quietly satisfy the gate. Reversible: yes.
- iter-74 · goal-evaluator (1 of 2) — Ambiguity: J-07 has four steps; steps 1-3 got fresh drill evidence this round but step 4 (induced memory-pressure abort) was not re-exercised — may a journey be scored passing with one of four steps carried on durability. We chose: passing, with step 4 carried on the dated 2026-07-31 live induced-pressure drill against the same memory cap, since the product diff since then is one test file plus documentation with no runtime code touched. Reversible: yes.
- iter-74 · goal-decomposer — Ambiguity: whether the owner-gated protection on `docs/goal.md`'s Must-have/Anti-goal sections also extends to the purely descriptive "Ground truth" facts appendix the iter-73 evaluator asked to be corrected. We chose: treat the Ground Truth block as ordinary engineering documentation the developer may correct, distinct from the owner-only journeys/anti-goals. Reversible: yes.
- iter-73 · goal-evaluator — Ambiguity: J-08 and J-09 got no valid evidence this round (goldens FAILed and were voided, frames were broken shells) — the literal fallback says set status to `unknown`, evidence durability (A.6) says the opposite since the product diff can't have touched either journey. We chose: hold both passing on durability, set `evidence_makeup` true on each, and deliberately do not advance `last_verified_iter` past iter-72. Reversible: yes.
- iter-73 · goal-decomposer — Ambiguity: J-07 step 3 requires recording the VmPeak margin against `memory_cap_mb` but no numeric threshold is stated for when a measured margin is "thin" enough to obligate a config reduction. We chose: treat <20% headroom as thin (obligating a reduction), ≥20% as acceptable as recorded. Reversible: yes.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-75.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-75-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-75-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-75-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-75/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
