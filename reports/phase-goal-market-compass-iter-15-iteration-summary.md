# Iteration Summary — goal-market-compass-iter-15

**Verdict:** STALLED
**Iteration type:** goal-full
**Date:** 2026-08-25
**Iteration:** 15

## In plain words

**What you can do now:** See an honest sector label for nearly every stock instead of a vague "Unassigned" tag. Read a plain-English reason why each next-session candidate was picked, and why others were not. Trust that the two trading days lost in the August data problem are back in the price history.

**What changed this time:** Nothing changed on any screen. This was all behind-the-scenes work on the checking tools that decide when it is safe to rebuild the 11 damaged trading days. The team used a one-time permission to check one company's (stock ticker AVB) real trading-volume numbers against an outside source, found its two recovered days record trading value about 2.8 times too high, and fixed the tool so it can never again miss a problem like this.

**What's next:** Next, the team needs the owner to approve a safety fix so starting the app can't accidentally write bad data, and then decide how to handle that one company's mismatched trading-volume numbers before the real repair can begin.

## Headline

J-11 STAGE D READY: NO (AVB-C) — AVB's price/volume conventions genuinely disagree

## Direction

**Signal:** stalling
**Why:** J-11 advanced within its own `partial` status by finally settling the AVB price/volume question on real fetched evidence (calibration window `bridged+compensating`, recovered dates `bridged+raw` → AVB-C), fixing iteration 14's price-only tautology — but no journey crossed a status boundary this iteration. Iterations 13-15 have now gone three straight rounds with zero journey-status movement while J-07 and J-08 stay failing throughout, and Stage D itself still needs a fresh owner decision on the AVB convention plus a new pre-boot safety guard before the engine can proceed.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: none
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: 1 critical (iter-14, AG-17/C5 — a test briefly overwrote three committed evidence files, caught in review and restored byte-for-byte within the same iteration)
- Iters with no journey state change: 3 of last 3

**Latest evaluator reasoning:** "The one question that blocked this repair is now answered with real measured data, and the answer is "the two restored days are on the wrong scale". One company, AVB, had two trading days restored in an earlier run. This run was allowed to make one small, read-only download to check them. It shows that on the four surrounding days Trendora's own stored figures keep the money value of trading steady: the price is multiplied by 2.793 and the share count is divided by the same 2.793."

## What was done

- Product changes: apps/backend/app/engine/j11_avb_diagnostic.py, apps/backend/app/engine/j11_stage_d.py, apps/backend/app/engine/j11_avb_provider_fetch.py, apps/backend/scripts/run_j11_stage_d_preflight.py, apps/backend/scripts/run_j11_avb_bridge_diagnostic.py, apps/backend/scripts/run_j11_avb_provider_fetch.py, apps/backend/scripts/run_j11_stage_d_readiness.py, apps/backend/scripts/run_j11_reconcile_iteration_14_truth.py, apps/backend/tests/test_j11_avb_diagnostic.py, apps/backend/tests/test_j11_stage_d.py, apps/backend/tests/test_j11_avb_provider_fetch.py, apps/backend/tests/test_j11_stage_d_cli_scripts.py
- Reconciled iteration 14's contradictory readiness verdict against a fresh, independent read-only re-derivation of the live database — 12 of 13 figures matched exactly; the one mismatch is a hash-recipe difference, not a data difference.
- Executed the single owner-authorized bounded AVB volume fetch (Yahoo, 6 dates, close+volume only, exactly one call site) — AG-9's dated exception #2 is now exhausted.
- Fixed iteration 14's price-only tautology in the AVB diagnostic so representation B now uses genuinely fetched provider volume, making the `bridged+compensating` label reachable for the first time.
- Measured from real evidence that AVB's stored data preserves dollar volume on the four calibration days but leaves volume untransformed on the two recovered days (2026-08-11/12) — a 2.793x dollar-volume overstatement — producing classification AVB-C and `J-11 STAGE D READY: NO`.
- Closed two filesystem evidence-path footguns (diagnostic CLI scripts now require an explicit output path and refuse before any DB/network access) and added 8 new negative-precondition tests (49 total in test_j11_stage_d.py, up from 26).
- Built a committed, deterministic readiness-artifact producer so the machine-readable verdict can no longer silently contradict the evaluator's conclusion, and proved zero writes to the live 8.4 GB database across the whole iteration (25/25 checks pass).
- Identified a critical, previously-unflagged safety gap: booting the backend at all would silently write a new day's results into the live database and irreversibly mint 7 immutable manifests, because the newest stored price date is itself one of the 11 emptied incident dates.
- Browser QA skipped under maintenance isolation (contract, not a gap) — 0 journeys re-verified this iteration; all 10 keep their prior recorded status.

## What's left

- Journey J-07 "The Today page answers the ten-second read" — failing, unchanged since iteration 0.
- Journey J-08 "Market page moves over intact and history stays honest" — failing, unchanged since iteration 1.
- Journey J-11 "Incident-bounded clean regeneration of derived state" — Stage D (the actual rebuild of the 11 incident dates) is still not ready and not authorized; blocked on an owner decision about AVB's 2.793x volume mismatch.
- A pre-boot safety guard is still missing: nothing in code today stops the backend from silently writing to the live database on ordinary startup while 11 incident dates sit empty.
- The AVB stored-data fingerprint quoted in the spec (`0257c56d…0b11cd`) still shows an unresolved, low-risk hash-recipe mismatch against the owner's captured value — the underlying data itself is confirmed identical by independent checks.
- Six journeys (J-02, J-03, J-05, J-06, J-09) remain `partial` and cannot be re-verified until the Stage D-G rebuild completes and browser testing resumes.
- Two small non-blocking fixes are queued: the readiness check should compare a database fingerprint (not just a clock), and an error message prints the wrong label when evidence is missing.

## Next step

One safety job and one decision are needed from the owner. First: add a start-up guard that refuses to boot Trendora normally while any of the 11 emptied incident days is still empty — today, simply starting the backend silently and irreversibly writes new results into the real database for 2026-08-12, so this must land before browser testing resumes. Second: decide how to handle AVB's two restored days recording trading value 2.793 times too high — accept it in writing with a recorded caveat, order a correction to the stored share counts first (a database write the current plan forbids without new dated permission), reword the rule so a bounded difference of this size doesn't block the rebuild, or change the plan in `docs/goal.md`. Whichever is chosen, Stage D (the actual rebuild) still needs a separate, fresh owner instruction, so this iteration ends `J-11 STAGE D AUTHORIZED: NO`.

## Assumptions made

- iter-15 · goal-evaluator — Ambiguity: iterations 13 and 14 both stalled while tractable non-owner work existed, but this iteration's tractable work includes a safety item (a pre-boot guard against an irreversible unauthorized database write) that is armed right now, a much stronger pull toward continuing. We chose: STALLED again, but promoted the pre-boot guard to the first item of the recommendation, ahead of the AVB decision — every route through the current blocker is owner-owned, the guard is itself a design decision, and halting is strictly safer since a stopped engine starts no backend. Reversible: yes.
- iter-15 · goal-evaluator — Ambiguity: J-10 is closed by the owner, but this iteration's fetch proved from measurement that its own output is defective for AVB (dollar volume 2.793x too high on the two recovered days), and goal.md does not say whether a closed journey's status may be reopened by a later measurement of its own output. We chose: keep J-10 `passing`, do not re-stamp it as freshly verified, and record the full measurement as a prominent caveat instead, since the finding already gates real work through J-11's AVB-C block. Reversible: yes.
- iter-15 · goal-decomposer — Ambiguity: whether re-deriving the engine identity again this iteration, for readiness-reporting purposes, counts as "redoing" the binding "do not redo" protection on iteration 14's frozen Stage D attempt-identity artifact. We chose: re-deriving is not a violation — the protected item is Stage D's own freeze-for-execution act, not the general capability of computing the identity read-only — and required the new observation to be written to a distinctly-labelled, non-reusable artifact. Reversible: yes.
- iter-15 · goal-decomposer — Ambiguity: the coordinator's brief for the AVB "compensating" volume hypothesis did not state the exact formula for how price and volume rebasing should compensate. We chose: model it as an inverse relationship (`expected_inverse_volume_ratio = 1/bridge_factor`), reusing the same tolerance idiom the existing price-ratio check uses, and required the developer to validate the formula against real fetched evidence rather than trust it blindly. Reversible: yes.
- iter-14 · goal-evaluator — Ambiguity: real, non-owner-owned tractable work existed (closing the classifier gap, adding a readiness producer, porting missing tests), which reads like it should allow continuing. We chose: STALLED anyway, offering the honesty fix as an explicit option, because that work cannot change the gate's answer and every path that can actually clear the gate is owner-owned. Reversible: yes.
- iter-14 · goal-evaluator — Ambiguity: whether an anti-goal violation caught and fully reversed within the same iteration (a test that briefly overwrote three committed iteration-13 evidence files) belongs in the ledger, given a critical+unresolved pair would force a REGRESSION halt. We chose: record it as critical severity but resolved, since the byte-for-byte restoration was independently confirmed three times and omitting it would make the ledger dishonest. Reversible: yes.
- iter-14 · goal-evaluator — Ambiguity: four review lanes read the AVB diagnostic's own evidence as "AVB-B" (safe), but the diagnostic's classifier could never even emit the one label that would flag a volume problem, and the spec requires classification from measuring the stored series, not convention alone. We chose: AVB-D (not ready), because the two "rescuing" arguments other lanes used do not survive checking against the actual call sites. Reversible: yes.
- iter-14 · goal-decomposer — Ambiguity: how to obtain a "raw provider close" for the two recovered dates without a new network fetch, since AG-9's recovery exception was already exhausted. We chose: derive it arithmetically from the stored bridged close divided by the persisted bridge factor, since the bridge transform is a known, invertible single-scalar multiply that was never applied to volume. Reversible: yes.
- iter-14 · goal-decomposer — Ambiguity: whether "closing" the iteration-13 identity-comparison blind spot means patching the already-executed Stage C function that captures but never compares the identity, or building new comparison logic for Stage D. We chose: realize the fix entirely as new Stage D code, leaving the completed, audited Stage C function untouched, since the captured-but-uncompared value was always inert for Stage C. Reversible: yes.

## Quick verify

From `reports/phase-goal-market-compass-iter-15-what-to-click.md`:

1. Open `http://localhost:3255/` in your browser (do not add any `?asof=` to the URL)
2. Look at the top market-state band's regime score and the phase tile's severity value
3. Read the plain-English summary card, then click `"Show cited facts"`
4. Read the "What changed" card's header
5. Click into one card under "Next-session focus"

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-15.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-15-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-market-compass-iter-15-review.md |
| Browser QA | SKIPPED | reports/phase-goal-market-compass-iter-15-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-market-compass-iter-15-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-market-compass-iter-15-user-visible-changes.md |
| What to click | — | reports/phase-goal-market-compass-iter-15-what-to-click.md |
| UI surface map | — | reports/phase-goal-market-compass-iter-15-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-market-compass-iter-15-ui-test-plan.md |
| QA | PASS | reports/qa/goal-market-compass-iter-15-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-market-compass-iter-15-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-market-compass-iter-15-closure-verdict.md |
| Goal evaluation | STALLED | runs/goal-session-market-compass/iter-15/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
