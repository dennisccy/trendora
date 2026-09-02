# Iteration Summary — goal-market-compass-iter-39

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-09-02
**Iteration:** 39

## In plain words

**What you can do now:** Open the evening market briefing (the Today page) for any date across the last 30 years and have it load correctly — including the 21 older evenings that showed an error message last round. See each stock's honest sector label, see why each next-session candidate was picked or skipped (with the real reason, not a made-up one), and trust that once an evening's briefing is saved it never quietly changes. Read the plain-English daily summary, the "what changed since yesterday" list, the Leadership rotation panel showing which sectors and themes are gaining or losing ground, and the Market page's full history, and browse the two trading days recovered from an earlier data problem.

**What changed this time:** The Today page no longer shows an error message on 21 of the last 23 saved evenings — it loads the full briefing again, exactly like it did before last round's fix broke it. On those older evenings, the "Not priority" section (which explains why a stock wasn't picked) now honestly says the held-back count isn't recorded for that evening, instead of crashing the whole page. Today's newest evening (2026-08-12) looks exactly the same as before.

**What's next:** Next, the team will build the one remaining piece — making sure the "what changed" list never silently drops a stock move it already checked.

## Headline

Today page no longer crashes on historical dates

## Direction

**Signal:** improving
**Why:** This iteration restored all six journeys iter-38's AG-8 crash had broken (J-02, J-03, J-06, J-08, J-11, J-13) and promoted J-14 to passing once its own non-regression requirement was met — seven journeys moved to `passing` on read-verified, screenshot-checked evidence rather than accepted claims. J-15 remains unbuilt and is now the sole blocker to GOAL_ACHIEVED, and a new minor AG-8 finding (a `gating` field mislabeling old failure reasons as "advisory") was logged unresolved as a carried item — real forward movement with one small open item.

**Trend (last 2 iters):**
- Newly passing this iter: J-02, J-03, J-06, J-08, J-11, J-13, J-14
- Newly passing in last 2 iters total: J-02, J-03, J-06, J-08, J-11, J-13, J-14
- Regressions in last 2 iters: J-02, J-03, J-06, J-08, J-11, J-13 (iter-38)
- Anti-goal violations in last 2 iters: 2 (1 critical — AG-8, iter-38; 1 minor — AG-8 residual, iter-39)
- Iters with no journey state change: 0 of last 2

**Latest evaluator reasoning:** The repair worked. Twenty-one older dates that showed an error box yesterday now show their board again — I checked the count in the database myself and opened five of those pages as pictures. The six jobs that broke last round all work again, and this time they were tested on days that already existed, not on a day created during the test. The one hard rule that was broken last round (adding new information must never crash an old page) is fixed. I am not calling the project finished, for one plain reason: J-15 "What changed accounts for every stock move" was never built. It is the only job left.

## What was done

- Product changes: apps/frontend/lib/api.ts, apps/frontend/components/compass-focus-section.tsx, apps/frontend/lib/why-not-summary.ts, apps/frontend/lib/why-not-summary.test.ts
- Today page (`/`) no longer crashes on any of the 21 previously-crashing historical `as_of` dates — restored to render fully, same as before iter-38's regression
- "Not priority" panel now shows an honest "held-back counts unavailable for this manifest version" message on older sessions instead of crashing; the current frontier date (2026-08-12) is unchanged
- Restored four golden test scripts (J-04, J-05, J-06, J-07) byte-exact to their pre-iter-38 state, undoing iter-38's same-day goalpost edits
- Added a new fixture test (`why-not-summary.test.ts`) covering both pre-fix and post-fix manifest shapes — 6/6 checks pass, no throw on either shape
- Backend confirmed correct and untouched; backend why-not fixture tests re-run green (2/2), zero drift
- Verified 14 of 15 target/required journeys pass browser QA (J-15 remains unbuilt, explicitly out of scope this round)

## What's left

- Journey J-15 ("What changed" accounts for every stock-level crossing) — never built; the sole remaining Must-have journey and the only thing blocking GOAL_ACHIEVED
- New minor AG-8 finding (unresolved): the `gating` field is still required in the TS type but absent on pre-iter-38 stored rows, mislabeling 26 stored leadership-floor misses as "advisory" on 3 historical dates — needs a one-line optional-field fix plus honest render
- J-04's restored golden script does not re-pass replay — its click target text was deliberately changed by this fix; needs a pre-declared repair pointing at a stable selector, not the volatile summary text
- J-14's golden script has never passed replay — step 3 asserts text inside a collapsed disclosure panel; needs a click-then-assert repair
- The reconciliation-footer mechanism has converted a real replay FAIL into a merged PASS for two iterations running; needs an owner/framework decision on when it may be used
- Three walkthrough captures are still owed (J-05, J-06, J-12), and one capture (UT-10) came out blank and should be retaken with a scroll-before-photograph step
- Carried housekeeping, none urgent: one pre-existing failing test on three untouched files; a 7.8 GB throwaway copy from iteration 23; `apps/frontend/.next-verify/` still tracked in git instead of gitignored

## Next step

Run one more full round and build J-15 "What changed accounts for every stock move" — the only job never built, and the only thing between this project and finished. Carry four small items as passengers of that round, never as a round of their own: (1) fix the wrong "advisory" word on three older dates where a real gate-miss is mislabeled; (2) repair the J-04 and J-14 check scripts in the open, declaring the change before running them; (3) take the three still-missing walkthrough photographs (J-05, J-06, J-12) and retake J-14's from the actual list rather than the top of the page; (4) have the browser step scroll before it photographs, since one picture this round came out blank. Separately, for the owner: two rounds running, the same boilerplate footer has turned a failing check script into a recorded pass — the footer should not be usable without a named, traced cause.

## Assumptions made

- iter-39 · goal-evaluator — Ambiguity: J-14's Walkthrough acceptance clause requires a `[NEW]`-flagged capture of the corrected "Not priority" list, but this round's walkthrough step is a top-of-page viewport with no `[NEW]` flag, and J-14's golden script has never passed deterministic replay; unstated whether a walkthrough-artifact clause can block a journey whose behaviour is proven by other evidence. We chose: score J-14 `passing` with `evidence_makeup: true`, both gaps named in the journey gap, eval and log — the behaviour is proven four ways and a capture gap is treated as non-blocking per methodology. Reversible: yes.
- iter-39 · goal-evaluator — Ambiguity: AG-8 (critical) has an outcome limb (no crash) and a method limb (re-validate consumers of widened fields); the newly found `gating` field is still required in the TS type but absent on pre-iter-38 rows, mislabeling 26 leadership-floor misses "advisory" on 3 dates — the outcome limb holds, the method limb doesn't, and it is unstated whether a method-limb-only breach of a critical anti-goal is itself critical. We chose: score it minor, log it unresolved, and state why not critical (no crash, no wrong number, the defect predates this iteration and only became visible because the crash was fixed, no journey assertion target affected). Reversible: yes.
- iter-39 · goal-decomposer — Ambiguity: the numbered Full trigger 3 reads "prior verdict ESCALATE", but iter-38's verdict was REGRESSION, not ESCALATE; the same dispatch prompt bundles REGRESSION into the same escape condition without amending trigger 3's numbered text. We chose: cite Full trigger 3 anyway, naming REGRESSION explicitly rather than mislabeling it ESCALATE, and additionally cite trigger 1 (structural/cross-cutting) as an independent, self-sufficient justification. Reversible: yes.
- iter-38 · goal-evaluator — Ambiguity: J-14's own browser row was a clean PASS with every served number independently re-derived, but its acceptance's non-regression limb (step 8, "pre-fix manifests remain readable") failed because the same change regressed 21 of 23 stored dates; unstated whether a journey with mostly-passing steps but a failing non-regression limb is `passing` or `partial`. We chose: `partial`, with the reason stated verbatim in the journey gap, eval and log — `passing` would misrecord a non-regression requirement as met when it wasn't, `failing` would erase verified work. Reversible: yes.
- iter-38 · goal-evaluator — Ambiguity: the merged results file (authoritative by contract) recorded J-06 as PASS, but that PASS rested on a golden edited after its own replay FAIL to point at a manifest minted during the same test run, deleting the immutability assertion that was J-06's own proof point; unstated whether the "merged file wins" rule still binds when the reconciliation rests on a same-run-rewritten golden. We chose: score J-06 `regressed`, stating plainly that a PASS row was overridden and why. Reversible: yes.
- iter-38 · goal-decomposer — Ambiguity: the binding depth recommendation ("evidence") was computed against iter-37's GOAL_ACHIEVED state, before J-14/J-15 were appended to `docs/goal.md` the same day; unstated whether a stale depth recommendation still binds once new Must-have journeys exist. We chose: Depth `full`, targeting J-14, citing Full trigger 1 and the brand-new-full-stack-journey escape condition rather than the evidence recommendation, stating the deviation and reasoning openly in the spec. Reversible: yes.

## Quick verify

From `reports/phase-goal-market-compass-iter-39-what-to-click.md`:

1. Open `http://localhost:3255/` in your browser
2. Navigate to `http://localhost:3255/?asof=2026-08-11`
3. Scroll down to the "Next-session focus" card and find the "Not priority (...)" line
4. Click that "Not priority (...)" line to expand it
5. Navigate to `http://localhost:3255/?asof=2026-08-12`

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-39.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-39-dev.md |
| Review | PASS | reports/reviews/goal-market-compass-iter-39-review.md |
| Browser QA | PASS | reports/phase-goal-market-compass-iter-39-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-market-compass-iter-39-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-market-compass-iter-39-user-visible-changes.md |
| What to click | — | reports/phase-goal-market-compass-iter-39-what-to-click.md |
| UI surface map | — | reports/phase-goal-market-compass-iter-39-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-market-compass-iter-39-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-market-compass-iter-39-ux-regression.md |
| QA | PASS | reports/qa/goal-market-compass-iter-39-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-market-compass-iter-39-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-market-compass-iter-39-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-market-compass/iter-39/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
