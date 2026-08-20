# Iteration Summary — goal-market-compass-iter-7

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-21
**Iteration:** 7

## In plain words

**What you can do now:** Look up any stock and see its real sector, not a placeholder "Unassigned" label. See the next-session candidate list with a plain-English reason why each pick was chosen, and honest reasons why other stocks were not.

**What changed this time:** Nothing changed on screen. Behind the scenes, the two-day price repair tool was pointed at a new data supplier (Yahoo) and given a new safety check: before restoring anything, it compares a handful of Yahoo's prices against what Trendora already stores, to make sure the two suppliers count prices the same way. Run for real, the check found one stock's numbers (Chevron's) were just outside the allowed margin, so it correctly refused to restore anything — the two missing days are still missing, and nothing else was touched.

**What's next:** Next, the team will rebuild that safety check the way the owner asked — comparing how prices move over time instead of their raw level — and then try the two-day repair again, with extra safety review switched on.

## Headline

New Yahoo-vendor recovery gated by a fail-closed convention check, which correctly refused to write.

## Direction

**Signal:** holding
**Why:** Iter-7's sole target, J-10 (Bounded recovery of the two deleted days), advanced substantially — the new Yahoo convention gate ran live on 88 real comparisons and correctly refused to write after CVX's price gap breached the precommitted tolerance — but its status label stays `partial` because zero bars were restored. The independent audit caught and fixed a critical fail-open in that same gate (AG-9) before it touched real data, so nothing regressed and every other journey's label carried over unchanged from iter-6. J-07 and J-08 remain `failing` but are still deliberately out of scope, so the project is holding rather than advancing its passing count this round.

**Trend (last 4 iters):**
- Newly passing this iter: none
- Newly passing in last 4 iters total: none (iter-3, iter-4, iter-6, iter-7 all report "Newly passing: none")
- Regressions in last 4 iters: none scored (iter-6's J-02/J-03 dropped passing→partial from an earlier, un-evaluated iteration's data-deletion drill, but was explicitly not scored as a regression — see iter-6 reasoning)
- Anti-goal violations in last 4 iters: 2 critical (iter-3 AG-12 export-overwrite; iter-7 AG-9 fail-open convention gate) — both found and fixed within the same iteration, 0 unresolved; plus 1 minor evidence-hygiene note (iter-6, AG-17, non-blocking)
- Iters with no journey state change: 1 of last 4 (iter-7 only; iter-3, iter-4 and iter-6 each moved at least one journey's status label)

**Latest evaluator reasoning:** The repair tool was pointed at the new supplier (Yahoo) and a new safety check was added: before writing anything, compare prices the system already has against the same days from the new supplier. The check ran for real, on 88 real price comparisons, and it said "these do not match closely enough" — so the tool wrote nothing at all. I checked the database myself, read-only: the two missing days are still missing, no new download record exists, and the database file has not been touched since before this iteration started. The tool did not move the pass mark after seeing a near-miss, which is the honest thing to do.

## What was done

- Product changes: apps/backend/app/engine/j10_recovery.py, apps/backend/app/data_providers/yahoo_provider.py, apps/backend/tests/test_j10_recovery.py
- Swapped the J-10 recovery vendor from Stooq (blocked by an anti-bot challenge) to Yahoo, guarded by a new fail-closed adjustment-convention gate that only allows a write on an "agree" verdict.
- Added `YahooProvider.get_adjusted_close` (the correct split/dividend-adjusted price field) so the gate compares like with like, not raw close against adjusted close.
- Ran the gate for real against the live database — 88 sampled pairs, 20 symbols x 5 surviving days; CVX's ~0.865% delta breached the precommitted 0.75% tolerance; the tolerance was not loosened after seeing the result, and zero rows were written.
- Independent audit found and fixed a CRITICAL fail-open (AG-9): the gate had returned "agree" on zero compared pairs; added a minimum-evidence floor plus 4 regression tests (27/27 passing).
- Verified via direct read-only SQL that `daily_prices`, `scanner_runs`, `data_provider_runs`, and `next_session_manifests` are all byte-unchanged (the database file's mtime predates the iteration).
- 23 updated/new unit tests plus a 44-test provider-client regression run all pass.
- Browser QA lane did not run this iteration (backend-only change plus the damaged-database lane gate) — 0 journeys verified via browser.

## What's left

- Journey J-07 (The Today page answers the ten-second read) failing — out of scope this iteration.
- Journey J-08 (Market page moves over intact and history stays honest) failing — out of scope this iteration.
- J-10 (Bounded recovery of the two trading days) still partial: zero bars restored; the two missing dates (2026-08-11, 2026-08-12) remain unavailable.
- J-02 (What changed since the previous session) and J-03 (Plain-English summary with cited facts) remain partial — both blocked on the same missing dates.
- Audit found two unresolved gaps in the new convention gate: it validates one price series (Yahoo's adjusted close) while the restore path would write a different one (raw close); and the 88 comparison deltas were never saved to a file.
- J-01–J-04 browser-lane re-verification is deferred to iteration 8 regardless of this iteration's outcome — four walkthrough recordings are now five iterations overdue.
- Five owner decisions remain open and non-blocking: whether J-09's 3.44 GB memory result is acceptable, the J-06 "underlying run unavailable" wording, rewording J-01's first two test steps, whether an empty "next-session focus" is an acceptable honest result, and whether the stock MNST should join the recovery set.

## Next step

Build the owner's redesigned safety check, then run the repair — one iteration, at full depth, targeting J-10 alone. The redesign must do four things together: compare how the two price series move day to day rather than comparing price levels; convert a passing company's new prices onto the existing stored scale across all four price fields before inserting them, never storing raw values; measure and store the same version of the supplier's price through one code path; and save every comparison to a file before anyone reads the verdict. Also make the pass marks impossible for a caller to override, and add the missing tests for the new price-reading code. Only after the two days are restored should the following iteration re-check J-01–J-04 in the browser and record their overdue walkthroughs. Nothing here is blocked on the owner — the redesign was already specified in `docs/goal.md` mid-iteration.

## Assumptions made

- iter-7 · goal-evaluator — Ambiguity: the owner rewrote J-10 step 2a in `docs/goal.md` mid-iteration (uncommitted), after the code was already built to the old text, so it was unclear which text the journey's recorded status/hash should be verified against. We chose: judged the developer's conduct against the OLD text (a correct outcome under it) but recorded J-10's status and hash against the CURRENT text, since J-10 is "partial" under both wordings so nothing unsupported is asserted. Reversible: yes.
- iter-7 · developer — Ambiguity: the real convention check returned a genuine but narrow mismatch (CVX ~0.865% vs. a 0.75% tolerance) that looked technically explainable as an ordinary dividend adjustment. We chose: did not loosen the tolerance after seeing the near-miss — treated it as a real mismatch and made zero writes, exactly as the "never loosen a failing tolerance to force a pass" rule requires. Reversible: yes, an owner-approved dated tolerance change would let a later retry of the same scope pass.
- iter-7 · goal-decomposer — Ambiguity: whether J-10's "J-01/J-02/J-03 replay clean" check must run through the browser-QA/replay pipeline, or may be satisfied by the developer's own direct database queries and API calls. We chose: satisfied it with direct checks this iteration and explicitly deferred ALL browser-QA re-verification of J-01–J-04 to iteration 8, to avoid a third repeat of "QA ran against a database whose damage status was still unresolved." Reversible: yes.
- iter-7 · goal-decomposer — Ambiguity: whether the new convention-check's tolerance/sample-size/window numbers count as a settings-file threshold or as single-use incident-response constants. We chose: kept them as literals scoped to the check itself, not new settings entries — the same reasoning already accepted for iter-6's recovery-date/symbol constants. Reversible: yes, moving them into settings later would be a low-risk follow-up.
- iter-6 · goal-evaluator — Ambiguity: J-10's finish line ("the two dates are restored...") was entirely unmet even though the recovery mechanism itself was complete, correct, and honestly blocked only by an external vendor; there was no rule for scoring a mechanism that's right but externally blocked. We chose: scored J-10 "partial" (not "failing"), writing every unmet item into the journey's notes, since both labels block the goal equally. Reversible: yes.
- iter-6 · goal-evaluator — Ambiguity: J-02 and J-03 were recorded "passing" but are functionally broken by data an earlier, un-evaluated iteration deleted; there was no rule for who owns a break from an iteration that was superseded before it was ever scored. We chose: scored J-02/J-03 "partial" (not "regressed" or "broken"), since the owner had already reviewed and authorized the repair twice. Reversible: yes, could be reclassified at any point with no gate impact.
- iter-6 · developer — Finding: the previously authorized data supplier (Stooq) is unreachable — it now serves a "prove you're human" puzzle instead of data. We chose: did not substitute a different vendor or attempt to defeat the challenge; stopped for owner review rather than broadening the fetch. Reversible: yes, a future owner-authorized vendor swap needs only a written amendment.
- iter-6 · goal-decomposer — Ambiguity: three evidence sources for the exact set of missing prices mostly agreed on 587 stocks, but one stock (MNST) was ambiguous — two contemporaneous sources said it wasn't in scope, one older snapshot said it was. We chose: excluded MNST from the recovery set rather than guess, leaving one unprovable item out rather than widening or abandoning the whole derivation. Reversible: yes, MNST's status can be revisited if new evidence resolves the conflict.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-7.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-7-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-market-compass-iter-7-review.md |
| Browser QA | SKIPPED | reports/phase-goal-market-compass-iter-7-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-market-compass-iter-7-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-market-compass-iter-7-user-visible-changes.md |
| What to click | — | reports/phase-goal-market-compass-iter-7-what-to-click.md |
| UI surface map | — | reports/phase-goal-market-compass-iter-7-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-market-compass-iter-7-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-market-compass-iter-7-ux-regression.md |
| QA | PASS | reports/qa/goal-market-compass-iter-7-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-market-compass-iter-7-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-market-compass-iter-7-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-market-compass/iter-7/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
