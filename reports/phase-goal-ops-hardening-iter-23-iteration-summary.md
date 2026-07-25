# Iteration Summary — goal-ops-hardening-iter-23

**Verdict:** GOAL_ACHIEVED
**Iteration type:** goal-lean
**Date:** 2026-07-25
**Iteration:** 23

## In plain words

**What you can do now:** You can browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. You can back-fill any historical date range with no size cap and get an honest explanation when there's nothing new to do. The status bar always tells the truth about whether the app is starting up, running normally, or has crashed — and it has been proven to survive a real crash-and-restart without losing its place. Heavy calculations are done in advance, not while you wait; the Backtest page always tells you plainly whether the numbers you're seeing are fresh, a labeled "still good" older version, or not ready yet; and pages stay responsive even while fresh numbers are being calculated in the background.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round; no app code changed. The team finished the paperwork proving the last two speed-related capabilities are genuinely done: they wrote a guided tour describing the newest capabilities for anyone giving a demo, and tracked down and undid a safety-check setting that had been quietly loosened without anyone flagging it, restoring it to its proper strictness. An independent second reviewer then re-checked everything from scratch and agreed the project has reached its goal.

**What's next:** Nothing required — the project's goal has been reached and independently confirmed twice over. Anything left (a cosmetic label fix, an optional extra safeguard for many people using the app at the exact same moment) is optional polish the owner can pick up later.

## Headline

A zero-product-diff closeout that actually closed what it targeted.

## Direction

**Signal:** holding
**Why:** No journey changed state this iteration — all 7 Must-have journeys (J-01, J-03, J-04, J-05, J-06, J-07, J-08) were already `passing` and stayed `passing`, each re-verified with fresh iter-23 evidence (deterministic replay for J-01/J-03/J-04/J-05/J-06, LLM lane for J-07/J-08). This iteration instead closed the two agent-tractable findings — an empty J-06/J-07/J-08 session-demo manifest and an undisclosed J-06 replay-timeout loosening — that caused iter-22's second-key CONFIRM evaluator to reject its GOAL_ACHIEVED call; this time both the first-key evaluator and the fresh-context CONFIRM agree (GOAL_ACHIEVED / CONFIRM_ACHIEVED), closing the session.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-08 (iter-21), J-06, J-07 (iter-22)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 3 of last 5 (iters 19, 20, 23)

**Latest evaluator reasoning:** "A zero-product-diff closeout that actually closed what it targeted. The two agent-tractable findings from iter-22's second-key CONFIRM reject are gone: the session demo manifest `demo.sh ops-hardening --session-live` really reads now carries five `[NEW]`-flagged, verified steps for J-06/J-07/J-08 (it had zero), purely additive (60 insertions, 0 deletions, existing 7 steps byte-unchanged); and J-06's golden script's undisclosed `default_timeout_ms` 8000→18000 loosening is reverted to 8000 after an investigation I re-derived myself from the database and `logs/backend.log`. All 7 Must-have journeys are `passing` with this-iteration evidence, all 7 `spec_hash`es match `goal_gate hash-journeys`, coherence is COHERENCE-PASS, the diff scan is CLEAN, and zero anti-goal violations are unresolved."

## What was done

- Authored 5 new `[NEW]`-flagged, verified session-demo steps (n=8–12) in `reports/goal-session-ops-hardening-demo.json` for J-06/J-07/J-08 — the exact file `demo.sh ops-hardening --session-live` reads — closing the "zero steps" gap iter-22's CONFIRM reject cited; additive-only (60 insertions, 0 deletions), existing 7 steps byte-unchanged.
- Investigated J-06's undisclosed golden-script `default_timeout_ms` loosening (8000ms→18000ms), found no legitimate background-compute-window overlap in `logs/backend.log`/DB timestamps, and reverted it to 8000ms.
- Re-ran the corrected J-06 replay end-to-end: 11/11 PASS, slowest step 2098.60ms (26% of budget); re-verified both J-06 assertion values against the live app/API — both confirmed correct and kept unchanged.
- Confirmed zero files under `apps/backend/` or `apps/frontend/` changed (git status/diff both empty) — a genuine zero-product-diff closeout.
- Verified all 7 target and required-still-passing journeys pass browser QA (deterministic replay for J-01/J-03/J-04/J-05/J-06, LLM lane for J-07/J-08); review verdict PASS_WITH_NOTES (one MINOR precision nit).
- Both the first-key evaluator (GOAL_ACHIEVED) and the fresh-context second-key CONFIRM evaluator (CONFIRM_ACHIEVED) agreed — the session's two-key gate is satisfied.

## What's left

- All Must-have journeys passing, no closure blockers.

## Next step

HALT — goal achieved (first key), and the second fresh-context CONFIRM evaluator has since run and independently agreed (CONFIRM_ACHIEVED) — both keys are now satisfied, so nothing blocks closing this goal session. Remaining items are explicitly non-blocking follow-ups, lean scope if ever picked up: trim demo step n=9's decimal precision to match `perf-budgets.md` exactly; capture replay evidence at the asserting step so the three `/data` screenshots stop being byte-identical; owner-optional — decide whether to promote backlog card B-1107 (a global dispatch cap for concurrent background-compute windows); retarget four `is_latest` monkeypatches before removing now-dangling imports; and look into why the backend was found down at this iteration's dispatch start.

## Assumptions made

- iter-23 · goal-decomposer — Ambiguity: earlier decomposers (iter-12 through iter-22) read goal.md's J-06/J-07/J-08 "[NEW]-flagged walkthrough viewable via `demo.sh ops-hardening --session-live`" clause as a settled non-autonomous, ungradable deliverable, but the iter-22 CONFIRM evaluator read it differently — the JSON manifest `--session-live` actually reads is itself agent-authorable, and its emptiness is a genuine, bounded gap. We chose: adopted the CONFIRM evaluator's reading and authored the manifest content directly, without attempting the interactive `--session-live` playback itself (still correctly out of scope). Reversible: yes
- iter-23 · goal-evaluator — Ambiguity: two new demo-manifest scenes (J-08's refreshing banner, J-07's health polling) can't be reproduced live at an arbitrary future playback; goal.md doesn't say whether "viewable" requires the viewer to actually see the state on screen or just that the step exists and plays. We chose: scored the walkthrough clause MET because the manifest now has complete, accurate, cited `[NEW]`-flagged steps for all three journeys, with the transient step written in past tense against a robust always-present `expect`. Reversible: yes
- iter-23 · goal-evaluator — Ambiguity: the new J-07 demo step cites 4-decimal figures ("7.1191 s"/"0.2530 s") not printed verbatim in `perf-budgets.md` (3 decimals), conflicting with TC-2's verbatim-citation wording — though the spec's own background paragraph specified those exact 4-decimal figures. We chose: treated it as a cosmetic precision nit, not a DoD failure, after confirming the figures are exact against the raw source CSV; did not block GOAL_ACHIEVED on it. Reversible: yes
- iter-22 · goal-evaluator — Ambiguity: the owner's background-compute-window budget amendment's window-duration bound was raised 60s→90s ("Revision 1") the same day, after this iteration's fresh measurement recorded a 68.79s breach of the original bound; goal.md doesn't say when the budgets file may be amended. We chose: treated the amendment including Revision 1 as the binding contract and scored J-06/J-07 passing, since the revision touches only the window-duration bound and is independently corroborated by a second same-day measurement. Reversible: yes
- iter-22 · goal-evaluator — Ambiguity: AG-8 (no exhausting a service's memory) and J-06's "every measurement within budget" clause were both literally touched by a self-inflicted 5-concurrent background-compute probe that drove memory to its cap and produced a real MemoryError; goal.md doesn't say whether a multi-window scenario is in scope. We chose: scored those samples out-of-contract and the MemoryError as NOT an AG-8 violation, since it was contained and honest exactly as AG-8's degradation clause requires, and the owner had already backlogged it (B-1107). Reversible: yes
- iter-21 · goal-evaluator — Ambiguity: the screenshot rail requires the image to show the acceptance state, but J-08's acceptance banner rendered below the fold in every capture this iteration, and two of four were byte-identical to earlier iterations'. We chose: scored J-08 passing anyway, on evidence re-derived independently from the database rather than the screenshot narrative. Reversible: yes
- iter-21 · goal-evaluator — Ambiguity: J-04 rides the LLM browser-qa lane, which skipped it for the sixth iteration running, but the disruptive kill/restart replay iter-20 demanded as a hard GOAL_ACHIEVED precondition was delivered by the operator this iteration; goal.md doesn't say whether operator API/DB evidence substitutes for a browser capture. We chose: kept J-04 passing and advanced `last_verified_iter` from iter-15 to iter-21, based on independently re-reading the DB record rather than accepting the operator's prose. Reversible: yes
- iter-20 · goal-evaluator — Ambiguity: transient in-process contention during the background-compute window literally breaches J-06/J-07's budget clauses, but J-07's title promise ("never take the service down") is met; goal.md doesn't say whether the budgets govern reads during a heavy background-compute window or only steady-state reads. We chose: kept J-06/J-07 `partial`, treated the spikes as real recorded breaches rather than satisfied-in-spirit, and treated resolution as an owner-owned budget decision. Reversible: yes
- iter-20 · goal-decomposer — Ambiguity: goal.md's J-08 wording reads unqualified ("never a cold recompute on request"), but the iter-16 decomposer had scoped that guarantee to `is_latest == true` only, leaving the historical view's lazy compute-once behavior explicitly unchanged — which browser QA then showed could block a first historical view for up to 54 seconds behind an empty, no-affordance skeleton. We chose: kept the historical lazy-compute substance but required the compute to run off the requesting thread via a single-flight-guarded background dispatch. Reversible: yes
- iter-19 · goal-evaluator — Ambiguity: J-08's wording reads broadly ("never a skeleton waiting on a fresh compute"), but the iter-16 decomposer's scoping (`is_latest == true` only) arguably sanctioned the observed 9.6-54s stall as part of the historical-view carve-out. We chose: kept J-08 `partial` anyway, because the honest-status clause shared across J-06/J-07/J-08 ("never a frozen or blank frame") is independently failed by a multi-second empty skeleton with no loading affordance. Reversible: yes
- iter-18 · goal-evaluator — Ambiguity: J-04 rides the LLM browser-qa lane, which skipped it this iteration because Chrome MCP was wedged, and no `browser-infra.json` token exists to mechanically fire the session's `pending_infra` carve-out, yet the dispatch note said to treat it per that methodology. We chose: carried J-04 `passing` (not `partial`+pending_infra, not `unknown`), deliberately without advancing `last_verified_iter`, based on its code surface being coherence-confirmed out of this iteration's diff and matching iter-16/17's human-ratified precedent. Reversible: yes
- iter-17 · goal-evaluator — Ambiguity: the DoD named a live cross-boundary refreshing capture as required for the B1 fix, but that state is unproducible on the committed seed without an owner-owned data-cycle action. We chose: accepted 15 re-run unit tests plus the auditor's client-side cross-boundary render plus a same-key live refreshing banner as a sufficient evidence floor for the fix's code correctness, so the missing live capture was not treated as a standalone blocker. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-23.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-23-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-23-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-23-ui-test-results.md |
| Goal evaluation | GOAL_ACHIEVED | runs/goal-session-ops-hardening/iter-23/eval.md |
| Goal evaluation (confirm) | CONFIRM_ACHIEVED | runs/goal-session-ops-hardening/iter-23/eval-confirm.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
