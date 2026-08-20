# Iteration Summary — goal-market-compass-iter-3

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-20
**Iteration:** 3

## In plain words

**What you can do now:** See real industry sectors for almost every stock instead of "Unassigned". Read a plain-English summary of today's market on the home page, with the numbers it's based on. See what changed since the last trading session. See which stocks are worth watching next, each with a plain reason, honest cautions, and honest notes on names that almost qualified but didn't.

**What changed this time:** The Dashboard's home page now has a new "Manifest" card — the last card in the daily briefing stack — showing that a given day's briefing was locked and time-stamped, with a list of every stock that almost made the cut and why not, and a way to make a clearly labeled copy of an old day's briefing without touching the original. This has not yet been watched happening on a real overnight market close, so it is not fully proven yet.

**What's next:** Next, the team will make the backend use less computer memory so this machine doesn't freeze again, before finishing and proving the locked daily record on a real market close.

## Headline

Frozen, stamped next-session manifests: every close now produces one permanent, tamper-evident record

## Direction

**Signal:** holding
**Why:** J-05 and J-06 (the frozen next-session manifest pair) advanced from failing to partial — the freeze/regenerate/hash/audit-table machinery is built and independently audited, but the flagship "a real close seals the record" scenario was never observed live, so browser QA came back BLOCKED and the deterministic closure gate failed. J-01 through J-04 all re-verified passing with no regressions, and the one critical anti-goal violation found this iteration (AG-12, an export-overwrite bug) was caught and fixed by the auditor before it touched a real file. The evaluator is redirecting the next iteration to J-09 (host memory safety) ahead of the J-05/J-06 make-up run, so the passing count is unchanged at 4 of 9 this cycle even though real progress happened underneath.

**Trend (last 4 iters):**
- Newly passing this iter: none
- Newly passing in last 4 iters total: J-01, J-02, J-03, J-04
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: 2 total (1 minor — AG-2, iter-2, resolved iter-3; 1 critical — AG-12, iter-3, resolved same iteration) — 0 unresolved
- Iters with no journey state change: 1 of last 4 (iter-1)

**Latest evaluator reasoning:** But the two journeys this iteration existed to finish are **not finished**. The test lane never ran the half that matters most — the part where a real market close seals the record — so the headline claim of J-05 "Each close freezes one next-session manifest" has never been watched happening. The automatic gate agreed and stopped the iteration (`CLOSURE-FAIL`).

## What was done

- Product changes: apps/backend/app/engine/compass.py, apps/backend/app/engine/engine_identity.py, apps/backend/app/engine/scanner.py, apps/backend/app/engine/data_manager.py, apps/backend/app/api/compass.py, POST /api/compass/regenerate (new route), apps/backend/app/models.py, apps/backend/app/db.py, apps/backend/app/config.py, config.yaml, apps/frontend/lib/api.ts, apps/frontend/lib/format-fact.ts, apps/frontend/components/compass-manifest-strip.tsx, apps/frontend/components/compass-summary-card.tsx, apps/frontend/app/page.tsx, docs/handoffs/trendora-next-session-manifest-v1.schema.json
- Built the freeze/integrity pair: every close now writes one permanent, tamper-evident "next-session manifest" (mode/version/frozen/prospective-eligible, dual hashes, three split rule-identity hashes) through a single writer behind three producer paths (ingest-finalize, historical create-once, confirm-gated regenerate).
- Added a new "Manifest" card on the Dashboard (`/`) with an expandable audit table (comparison cohort + near-threshold shadow, 539 rows) and a confirm-gated "Regenerate manifest" control.
- Added a byte-identical JSON export writer for the freeze artifact, plus a committed JSON Schema (`trendora-next-session-manifest-v1.schema.json`) validated against real frozen manifests.
- Fixed three passenger items: the summary card's raw float display artifact now rounds to 2 decimals; the ATR caution no longer ends with an advice-sounding tail; the banned-language guard now also scans candidate reason/caution/why-not strings.
- Re-verified all 4 required-still-passing journeys (J-01-J-04) green with no regressions.
- Auditor found and fixed one CRITICAL anti-goal violation (AG-12: the export writer could silently overwrite an already-frozen artifact) and closed iter-2's MINOR AG-2 finding.
- Verified 0 target journeys pass browser QA end-to-end — J-05 and J-06 both scored `partial`: the flagship live-close scenario and one basis-disclosure branch (audit finding B2) remain unverified or unmet.

## What's left

- Journey J-05 (Each close freezes one next-session manifest, exported byte-consistently) — partial: the flagship "a real close seals a version-1, prospective-eligible manifest" scenario has never been observed live; the export byte-equality claim has only a manual check, no automated test.
- Journey J-06 (A frozen manifest never changes) — partial: step 2's "the underlying run is unavailable" basis disclosure is provably unreachable — a plain page load silently rebuilds a deleted day instead — and needs an owner decision on the as-of contract before it can be fixed.
- Journey J-07 (The Today page answers the ten-second read) — still failing, not tested this iteration (out of scope).
- Journey J-08 (Market page moves over intact and history stays honest) — still failing, not tested this iteration (out of scope).
- Journey J-09 (The backend fits the host) — status unknown; the owner added it today after the machine froze, it has never been measured, and goal.md says it jumps the queue next.
- Closure gate result is CLOSURE-FAIL: no lane executed a real test case for J-05 or J-06, so the browser-QA headline reads BLOCKED; needs a genuine browser/replay pass before closure can re-run.
- J-01-J-04 still carry an open evidence gap: the required `[NEW]` session-live walkthrough recording is now two iterations overdue.
- Two owner decisions remain open from iteration 2: rewording J-01's destructive test-step wording, and whether an empty "next-session focus" list on the newest date is an accepted honest result.
- A leftover, unrelated build-artifact folder (`apps/frontend/.next-verify/`) is checked into git from an older session — flagged for the owner to clean up separately.

## Next step

Build J-09 "The backend fits the host" next, alone, at lean depth: change one number in `config.yaml` so each database connection keeps 64 MB of pages instead of 256 MB, measure the backend's peak memory and prove it stays under 2.5 GB (it was 4.8 GB), append the dated figure beside the old one, re-run the burst-of-requests check, and confirm a stored day's numbers don't move — this comes first because finishing J-05/J-06 means running real data rebuilds, exactly the heavy jobs that helped freeze the host machine. After that, run the J-05/J-06 make-up iteration: remove and re-add the last two trading days to actually watch a close seal a fresh record, then delete and restore a day to watch the basis line change, and re-capture the still-missing walkthroughs and blank screenshots. Two decisions still need the owner: how the "underlying run is unavailable" wording should work, and the two items still open from iteration 2 (J-01's test-step wording; whether an empty next-session-focus list is an accepted honest result).

## Assumptions made

- iter-3 · goal-evaluator — Ambiguity: the status vocabulary has no rule for a journey with both a proven defect and proven working parts (J-06's "unavailable" wording is unreachable per audit finding B2, but its other steps are met). We chose: scored J-06 `partial` rather than `failing`, writing the unmet step out in full so nothing is hidden; neither label reaches GOAL_ACHIEVED, so the choice costs nothing at the gate. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: J-01-J-04 carry `evidence_makeup: true` for a missing walkthrough; the rule says the flag clears "the moment a fresh capture lands," and fresh captures did land this iteration, but not the specific walkthrough recording asked for. We chose: kept `evidence_makeup: true` on all four, reading the flag as tracking the outstanding capture KIND (a walkthrough), not any newer image — clearing it would delete the only scheduling hook for a make-up that is now two iterations overdue; does not affect their passing status. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: AG-12 says "a historical view never substitutes a newer manifest," but goal.md doesn't say whether that means a newer DATE's manifest or a newer VERSION of the same date's manifest, and a regenerate now serves the newest version by default. We chose: read it as date-scoped, not version-scoped — J-06's own acceptance step requires the newest version to appear after a regenerate, and a later journey (J-08) is where the date-substitution rule actually lives; recorded as OK, not a violation. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: the priority rubric warns against bundling two risky journeys, but the prior iteration's evaluator explicitly recommended building J-05 and J-06 together, and nothing says whether a sequentially-dependent pair counts as "two risky journeys." We chose: treated J-05+J-06 as one feature examined from two angles (freeze-and-stamp, then prove immutability) and built them together at full depth, since J-06's every step depends on J-05's manifest already existing — splitting them would not improve diagnosability. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: J-01's destructive test step was skipped and its "select Unassigned filter" step is unexecutable now that coverage is 100%, and goal.md doesn't say whether a journey can pass with an unexecutable step. We chose: scored J-01 `passing` because the Acceptance block (not the Steps list) is the bar and every acceptance clause is evidenced; the owner-facing request to reword both steps stays open. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: J-04's steps require opening a candidate card, but on the latest stored date zero members clear the selection rule, so no candidate card exists, and goal.md doesn't say which date to use when the frontier is legitimately empty. We chose: verified the empty-state steps live on the latest date and the candidate-card steps on a historical date with a real candidate, since the assertions are about traceability to stored rows, not a specific calendar date. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: J-01-J-04 each require a `[NEW]`-flagged walkthrough, but the pipeline ran at lean depth so no demo lane executed and none exists, and goal.md doesn't say whether a missing walkthrough blocks an otherwise-evidenced journey. We chose: scored all four `passing` with `evidence_makeup: true` (a capture defect, not a status blocker) since each has its own screenshot proving the acceptance state; the walkthrough rides the next iteration as a passenger task. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: the blueprint names `/` as the home for the new cards, but `/` is still the unmodified legacy Dashboard, and the full Today-page chrome/ordering is a later journey's (J-07/J-08) job. We chose: added the three new cards to the existing `/` page above the current dashboard body, leaving final ordering, chrome separation and the old body's removal to J-07/J-08's own iterations. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: the manifest's baseline Data Contract doesn't say which fields this iteration must persist versus which stay unbuilt until the freeze iteration, even though one acceptance step names `content_hash` explicitly. We chose: this iteration builds only the content-computation logic and `content_hash`; freeze/versioning, `manifest_hash`, provenance, frozen cohort storage, `prospective_eligible`, `available_at_utc` and export stay out of scope, deferred to J-05/J-06. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: the browser-QA run permanently destroyed two days of user-added test data, and no anti-goal names data destruction, so the decision tree gives no rule for scoring it. We chose: did not treat the loss as a regression or anti-goal violation — the destroyed bars were outside the committed seed, the product refused to fabricate replacements, and no journey depended on those dates; flagged it prominently and requested a goal.md wording amendment instead. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: the browser-QA lane FAILed J-01 because its precondition step died against a stale backend, while the auditor separately verified the journey's substance live, and goal.md doesn't say how to score that split outcome. We chose: scored J-01 `partial` with `evidence_makeup: true` (capture defect) — not `passing`, because the required screenshot/walkthrough genuinely doesn't exist, and not `failing`, because the behavior was independently re-measured and confirmed. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: the agent instructions describe two not-quite-identical trigger sets for depth=full, and neither says how "brand-new full-stack journey" (the condition that holds here) maps onto the four numbered triggers required in the metadata line. We chose: cited numbered Trigger 1 (structural/cross-cutting), grounded in the objective fact that this iteration's sector wiring touches four modules whose combined interaction has no existing test, rather than the softer "first UI" framing. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: goal.md says depth is "full when an iteration first lands user-visible UI changes," but doesn't say whether J-01's mostly-backend sector wiring plus one new Methodology paragraph counts as a user-visible UI change. We chose: treated it as user-visible and recommended `full` depth, because the owner will see different sector labels on `/stocks` and new disclosure text on `/methodology`, and because J-01's "never fabricate a sector" claim benefits from the audit lane on the session's first product change. Reversible: yes

## Quick verify

From `reports/phase-goal-market-compass-iter-3-what-to-click.md`:

1. Open `http://localhost:3255/` in your browser
2. In the top bar, click the "◀" arrow button once (just left of the date badge that reads "Latest")
3. Scroll down to the "Manifest" card and look at it
4. On the Manifest card, click the row that starts with "Audit table — comparison cohort ("
5. Click the "Regenerate manifest" button on the Manifest card

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-3.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-3-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-market-compass-iter-3-review.md |
| Browser QA | BLOCKED | reports/phase-goal-market-compass-iter-3-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-market-compass-iter-3-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-market-compass-iter-3-user-visible-changes.md |
| What to click | — | reports/phase-goal-market-compass-iter-3-what-to-click.md |
| UI surface map | — | reports/phase-goal-market-compass-iter-3-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-market-compass-iter-3-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-market-compass-iter-3-ux-regression.md |
| QA | PASS | reports/qa/goal-market-compass-iter-3-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-market-compass-iter-3-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-market-compass-iter-3-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-market-compass/iter-3/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
