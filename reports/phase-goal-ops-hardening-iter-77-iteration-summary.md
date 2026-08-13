# Iteration Summary — goal-ops-hardening-iter-77

**Verdict:** ESCALATE
**Iteration type:** goal-full
**Date:** 2026-08-13
**Iteration:** 77

## In plain words

**What you can do now:** Browse stock rankings, sector/theme views, backtests and the research tools while the app always shows an honest status message during startup. Backfills accept any date range with no hidden cap and say plainly when there's nothing new to fetch. Freshly calculated numbers are ready right after a data import instead of being computed on the fly, backtest results load instantly from storage, pages fetch only what they need, and the app tells you when it's crunching numbers in the background and how long that took. New this round: the status badge and the green "board is current" strip now also tell you how fresh that reading is, and the "Ready" pill no longer hides itself when you're on a smaller screen during background work.

**What changed this time:** The status badge (top of every page) and the green "GO — today's board is current" strip now show a small "as of Ns ago" freshness note next to the status. A layout bug that could hide the green "Ready" pill behind the "background compute running" chip at common window sizes (1280×800) is fixed — the row now wraps instead of hiding it. Behind the scenes, the team also closed a bug where a routine build check could accidentally break the running app so it couldn't restart.

**What's next:** Next, the team needs to fix the official test report so it stops saying three of this round's new features were never tested — they were tested and did pass, the passing results just never got copied into the report everyone reads — then re-run the finishing check so this round is no longer marked incomplete.

## Headline

Readiness badge and preflight banner now disclose how stale the shown status is ("as of Ns ago")

## Direction

**Signal:** holding
**Why:** All eight Must-have journeys (J-01 through J-09) remain `passing` this iteration, with fresh evidence produced this round for the three targets (J-04, J-07, J-09) after the code lane restarted and shipped the staleness disclosure, a layout fix, and a stronger J-07 test hook. No regression and no newly-passing journey occurred — this was a re-confirmation round, not a movement round — and the round ended `blocked` on a failed closure gate (an unmerged test-results artifact plus a false-positive regex check), which is why the evaluator escalated rather than declared success.

**Trend (last 2 iters):**
- Newly passing this iter: none
- Newly passing in last 2 iters total: none
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: iter-76 opened 6 new (all minor); iter-77 opened 8 new (all minor); 0 unresolved critical in either iter
- Iters with no journey state change: 2 of last 2

**Latest evaluator reasoning:** The programming step worked again after two empty rounds, and it delivered. Thirteen files changed, all eight journeys pass on evidence from this round, and the app answered 6,806 requests without a single error while running heavy jobs. But the round did not finish cleanly: the automatic end-of-round check failed, so the iteration is recorded as blocked.

## What was done

- Product changes: scripts/start-frontend.sh, apps/frontend/next.config.mjs, apps/frontend/lib/api.ts, apps/frontend/lib/staleness-annotation.ts, apps/frontend/components/readiness-provider.tsx, apps/frontend/components/health-badge.tsx, apps/frontend/components/preflight-banner.tsx, apps/frontend/app/layout.tsx, apps/frontend/app/backtest/page.tsx, apps/backend/tests/test_start_frontend_script.py, scripts/automation/lib/demo_runner.py
- Rendered `stale_for_s` as an "as of Ns ago" staleness disclosure on the readiness badge and preflight banner — the first UI consumer of a backend field served since iter-71.
- Fixed the header layout bug that could hide the "Ready" pill behind the background-compute chip at a 1280×800 viewport.
- Root-caused and closed the intermittent asset-less-frontend defect: added a build lock plus a defense-in-depth Next.js build guard that refuses out-of-band builds into the live/served dist directory (the mechanism that actually broke this round).
- Strengthened the J-07 golden with a real `scorecard-row-1d` selector and re-ran it plus J-09 through deterministic replay.
- Fixed the walkthrough recorder's byte-identical before/after frames and cleared the stale `goldens-regen-pending` queue.
- Housekeeping: deleted the stray zero-byte `=` file and captured live evidence for the `/data` honest-fallback fault-injection hook.
- Verified all 8 journeys (5 required-still-passing + 3 targets) pass deterministic replay and browser QA on the delivered tree.

## What's left

- Closure gate FAILED: the official browser-QA artifact of record still reads BLOCKED with J-04, J-07 and J-09 marked "no test case executed," even though they passed after the fix pass — the passing results sit in an unmerged side file and need to be re-merged (or the browser lane re-run) before the round can close.
- Second closure blocker is a harness false positive (`closure_gate.py:72`'s regex) flagging a sentence that actually denies a backend-only gap — needs owner sign-off to fix.
- The launcher-residue defect (a test that can leave a broken file blocking the next build) was fixed once inside the round but is not defended against recurrence.
- The staleness annotation freezes for up to 30 seconds between polls instead of ticking client-side, so "as of <1s ago" can sit stale for a while.
- J-09's walkthrough step still doesn't show the background-compute chip; J-05 and J-07 walkthroughs remain unrecorded for the 19th round running.
- Session cost is now 5.6x over its time budget — the 17th consecutive overrun.
- 140 unresolved (minor) housekeeping ledger entries remain; the owner has not yet said whether to finish the loop now and hand these over as a to-do list, or spend more rounds clearing them first.

## Next step

Run the next round at full depth with a developer. First, make the official test-results file tell the truth — merge in (or re-run) the post-fix replay so it stops saying J-04, J-07 and J-09 were never tested, then re-run the closure check so this round stops being recorded as blocked. Get the owner's permission to fix the closure-gate's false-positive backend-only check. Stop the test that can leave the app unable to start (never run it under a short time limit, or make the launcher ignore its leftover file). Make the freshness note keep counting instead of freezing for up to 30 seconds. Everything else — missing walkthroughs, page-timing logging, the long carried backlog — rides along without being the round's goal.

## Assumptions made

- iter-77 · goal-evaluator (3 of 3) — Ambiguity: none of C.4's three literal ESCALATE triggers fit (nothing failed twice, review was PASS_WITH_NOTES with no fail-open, and this iteration ran `full` not `lean`), yet the round ended blocked on a CLOSURE-FAIL whose remediation only exists in the full pipeline, and a CONTINUE verdict would be demoted to a developer-less evidence-only round. We chose: ESCALATE, stating openly this relies on substance and mechanism rather than a literal rule fit — the same reasoning was validated at iter-76 (it produced a real 13-file code lane). Reversible: yes.
- iter-77 · goal-evaluator (2 of 3) — Ambiguity: the binding "do not redo" carry says J-07's memory-pressure drill steps are valid "while the diff stays empty," but this round's diff is not empty, and the spec explicitly hands the evaluator the call between fresh drill evidence or the disjoint-files argument. We chose: keep the carry and score J-07 passing, since no backend runtime file changed (only a test file) and this round's own clean log (6,806 requests, zero MemoryError across nine concurrent background computes) is new positive evidence for the same acceptance. Reversible: yes.
- iter-77 · goal-evaluator (1 of 3) — Ambiguity: the "merged file wins" rule assumes a disagreement, but here the merged artifact records an ABSENCE for J-04/J-07/J-09 captured before the fix pass, while a later, unmerged replay executed and passed all three — nothing states whether that later result may fill the absence. We chose: score the three journeys passing on the post-fix replay plus frames opened and matched against the database, while logging the stale artifact of record as this round's first open item. Reversible: yes.
- iter-77 · goal-decomposer — Ambiguity: the carried item names the asset-less-frontend defect as un-root-caused with an unconfirmed theory, and nothing states which specific mechanism this round must chase. We chose: direct the developer at the concurrent-invocation race (two `start-frontend.sh` runs serving the same live `.next` dir) as the leading hypothesis to confirm or rule out first, while allowing a different named cause if instrumentation disproves it. Reversible: yes.
- iter-76 · goal-evaluator (2 of 2) — Ambiguity: whether flagging a majority of journeys (5 of 8) as needing a fresh capture is appropriate, given a large flag set could later be misread as "every remaining gap is a capture task." We chose: flag all five truthfully and state explicitly they must never set a future round's depth to evidence-only. Reversible: yes.
- iter-76 · goal-evaluator (1 of 2) — Ambiguity: none of the decision tree's literal ESCALATE triggers fit, yet the round surfaced a structural fault — an automatic backstop demoting every lean spec to evidence-only while all 8 journeys pass, making the developer lane unreachable. We chose: ESCALATE for its documented mechanical effect (forces the next round to run full), verified deterministic by reading the engine source. Reversible: yes.
- iter-76 · goal-decomposer — Ambiguity: the carried item names two mutually exclusive remedies for the unguarded fault-injection hook (capture live evidence vs. remove the hook) and nothing states which one closes the carry. We chose: capture the live evidence rather than remove the hook, since removing it would delete a working resilience proof-of-concept with no defect to fix. Reversible: yes.
- iter-75 · goal-evaluator (2 of 2) — Ambiguity: the rule says clear the "needs fresh capture" flag the moment a fresh capture lands "whatever the outcome," but fresh captures for J-01 and J-07 landed still defective in the same way as before. We chose: clear the flag on J-08/J-09 (their defects are cured) but re-derive it as true on J-01/J-07 from this round's own still-defective captures. Reversible: yes.

## Quick verify

From `reports/phase-goal-ops-hardening-iter-77-what-to-click.md`:

1. Open `http://localhost:3255` in your browser
2. Look directly below the top bar, at the thin green strip
3. Refresh the page (press F5 or Cmd+R)
4. Resize your browser window to about 1280 pixels wide by 800 tall (or use your browser's responsive/device toolbar and set a custom size of 1280×800)
5. Click "Backtest" in the left sidebar

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-77.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-77-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-77-review.md |
| Browser QA | BLOCKED | reports/phase-goal-ops-hardening-iter-77-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-77-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-77-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-77-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-77-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-77-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-ops-hardening-iter-77-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-77-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-77-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-ops-hardening-iter-77-closure-verdict.md |
| Goal evaluation | ESCALATE | runs/goal-session-ops-hardening/iter-77/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
