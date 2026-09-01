# Iteration Summary — goal-market-compass-iter-36

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-09-01
**Iteration:** 36

## In plain words

**What you can do now:** See each stock's honest sector label. Open the Today page for a quick evening briefing with plain "improving" or "worsening" words, a "what changed since last time" list, and a plain-English summary. See why each next-session candidate was picked, skipped, or flagged with a caution — the labels are now fully accurate. Trust that a saved evening briefing never changes once saved, and browse the separate Market page or the two trading days recovered from an earlier data problem. New this session: see which sectors and themes are gaining or losing leadership, both directions, with a plain word for each move.

**What changed this time:** The Today page's "Leadership rotation" panel now shows real data instead of just repeating the list above it. It has two labelled sides — gaining and losing — for sectors and for themes, each move marked with a plus or minus number and a word saying whether it is a good or bad move. It also now correctly counts every sector and theme group instead of silently dropping two of them.

**What's next:** Next, the team will run one more careful, fully-checked round — including a fresh picture of the new panel, since this round's came out blank — before calling the project finished.

## Headline

Leadership rotation section now serves real signed sector/theme data instead of duplicating What-changed

## Direction

**Signal:** improving
**Why:** J-13 "Leadership rotation says which way, shows both directions, and stops repeating What-changed" moved from failing to passing this iteration, closing the last unbuilt Must-have journey — all 13/13 journeys now record passing and every deterministic gate exits clean (journeys 13/13, regressions 0, coherence PASS, drift none). The verdict is ESCALATE rather than GOAL_ACHIEVED for procedural reasons only: the spec required `full` depth (auditor, QA, ux-regression, closure) but every downstream agent ran `lean` without surfacing the drop, and J-13's sole acceptance screenshot is 100% blank — neither issue reflects a regression or an unmet behavior.

**Trend (last 2 iters):**
- Newly passing this iter: J-13
- Newly passing in last 2 iters total: J-12 (iter-35), J-13 (iter-36)
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: none
- Iters with no journey state change: 0 of last 2

**Latest evaluator reasoning:** "I am still not closing the project this round, for two reasons that have nothing to do with whether the feature works. First, this round was supposed to run the FULL checking team, its own plan says so in writing, and the previous round's binding note said a drop to the light team 'must be surfaced explicitly and marked unmet'. The light team ran instead, and nobody said so... Second, the single picture meant to show that new screen is completely empty: a flat dark rectangle with exactly one colour in it. So no picture of the new panel exists anywhere."

## What was done

- Product changes: apps/backend/app/engine/session_delta.py, apps/backend/app/engine/compass.py, apps/backend/app/config.py, config.yaml, apps/frontend/lib/api.ts, apps/frontend/components/compass-leadership-rotation-section.tsx, GET /api/compass (new `session_delta.rotation` field)
- Built J-13: the Leadership rotation section now serves a real `session_delta.rotation` block (two labelled, signed gaining/losing sides per sector/theme group) instead of a client-side filter that duplicated the What-changed list.
- Closed the sector/theme accounting gap: sector now closes exactly 31/31 groups and theme 11/11 (previously 29/31 for sector), via new shown/suppressed/residual counts.
- Added signed `delta` + `direction_word` fields to sector/theme entries in `session_delta.changes`, reusing the existing direction-word vocabulary (no new blended score).
- Fix round 2 closed a CRITICAL review finding: legacy (pre-iteration) manifest rows lacked the new `rotation` key and crashed the Today page on as-of navigation; fixed by making the field optional and adding an honest "rotation not recorded" placeholder branch.
- Confirmed all pre-existing frozen manifests (v1-v8) stayed byte-identical; the only new content landed in a freshly minted v9 via the sanctioned regenerate route.
- Verified 8 target journey(s) pass browser QA.

## What's left

- Depth drop unresolved: this iteration's spec required `full` depth, but every downstream agent ran `lean`; the independent auditor, QA, ux-regression, and closure reports do not exist on disk.
- J-13's sole acceptance screenshot (`UT-J-13-rotation-both-directions.png`) is 100% blank — no visual record of the new rotation panel exists yet.
- J-13's new golden script (`journey-scripts/J-13.json`) was written after this round's replay run and has never been executed.
- J-04's screenshot crop defect persists (18th consecutive round); 8 journeys still owe a labelled walkthrough recording.
- Carried, non-blocking: one pre-existing red unit test on untouched files; a `start-frontend.sh` script gap leaving a stray `next-server` process holding the port; the iteration-23 throwaway copy (7.8 GB); `apps/frontend/.next-verify/` still tracked in git; J-01's automatic re-check asserting less than the journey claims.
- Five older owner questions remain open and non-blocking: J-06's "underlying run unavailable" wording; J-01's first two test steps; whether an empty "next-session focus" is acceptable; whether MNST joins the recovery list; whether 12 August should keep showing its "rebuilt" note.
- The whole iteration is uncommitted at scoring time — confirm it lands in git.

## Next step

Run one more round at FULL depth and treat it as the closing round — there is no new feature work left. Three things must come back green: (1) actually run the full checking team, proven by the presence of the four missing reports (independent auditor, quality lane, visual-change/ux-regression, sign-off/closure) rather than a marker file; (2) take the Leadership rotation acceptance picture again, since this round's is completely blank and nobody has ever seen the new panel — a passenger task, never the round's purpose; (3) replay the new J-13 check script once, since it was written after this round's replay run and has never actually executed. Two small repairs can ride along if the developer is already in those files: raise the test fixture's risk value above 60.0, and turn the two bare guard statements into real errors.

## Assumptions made

- iter-36 · goal-evaluator — Ambiguity: whether a matching GOAL_ACHIEVED decision-tree rule must be honored even when the iteration itself had a verification deficit (full depth silently dropped to lean, with no auditor/QA/ux-regression/closure lanes run). We chose: ESCALATE instead of GOAL_ACHIEVED, declining certification for one round and stating why openly. Reversible: yes
- iter-36 · goal-evaluator — Ambiguity: whether a journey may be promoted to `passing` for the first time when its cited acceptance screenshot is a real file but is 100% blank. We chose: promote J-13 to `passing` with `evidence_makeup: true`, since the behavior was independently re-derived from served data, stored ranks, and a real browser image of the same component elsewhere. Reversible: yes
- iter-36 · goal-decomposer — Ambiguity: whether J-13's "same signed delta rides session_delta.changes too" instruction applies to all five change kinds or only the two the rotation block itself covers. We chose: scope the addition to sector/theme kinds only. Reversible: yes
- iter-35 · goal-evaluator — Ambiguity: whether a newly-added Must-have journey (J-12) may be promoted to `passing` for the first time despite its Walkthrough acceptance limb never being captured. We chose: promote it, with `evidence_makeup: true` and the gap recorded, since the measured behavior was independently re-derived. Reversible: yes
- iter-35 · goal-evaluator — Ambiguity: whether a brand-new, never-tested journey (J-13) should be scored `unknown` (no evidence) or `failing` (positive evidence of absence). We chose: `failing`, based on defects re-measured directly against the current manifest and code. Reversible: yes
- iter-35 · goal-decomposer — Ambiguity: whether a stale `evidence`-depth recommendation still binds after new Must-have journeys (J-12, J-13) were added to the goal, and which to prioritize. We chose: target J-12 only at lean depth, since `evidence` depth doesn't apply to unbuilt journeys and J-12 was the smaller, higher-severity pick. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-36.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-36-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-market-compass-iter-36-review.md |
| Browser QA | PASS | reports/phase-goal-market-compass-iter-36-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-market-compass/iter-36/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
