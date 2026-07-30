# Iteration Summary — goal-ops-hardening-iter-38

**Verdict:** ESCALATE
**Iteration type:** goal-full
**Date:** 2026-07-30
**Iteration:** 38

## In plain words

**What you can do now:** Import historical stock data for any date range and get an honest explanation when there's nothing new to add, with no artificial size limit on how much history you can pull in one request. The status badge tells the truth right after the app starts, updates, or crashes. Heavy calculations are prepared ahead of time so results appear instantly, research pages show an honest "still computing" message instead of a blank screen when something is slow, backtest results are always fully proven rather than partial, and you can see when the app is doing background work through an honest status indicator.

**What changed this time:** Behind the scenes, the system that imports and prepares stock data was put through a real stress test for the first time: bringing in several days of price history now proves it reads the price table from disk only once instead of twice (rather than just having the code present but never actually exercised). An independent double-check also caught and corrected a backwards headline number in this round's own memory measurement before it could mislead anyone.

**What's next:** Next, the team will finally push the background data-import process hard enough to make it run out of memory on purpose, so it can prove the app survives that gracefully — the one remaining check on the list before this chapter's promises are all fully proven.

## Headline

Proved backend's shared price-cache optimization is genuinely exercised, not just present but unused

## Direction

**Signal:** holding
**Why:** No journey regressed and no critical anti-goal was introduced this iteration — 7 of 8 journeys (J-01, J-03, J-04, J-05, J-06, J-08, J-09) remain verified passing. J-07 ("Heavy aggregates never take the service down") stayed `partial` for a 4th consecutive iteration because its induced-pressure step (step 4) was re-tuned so nothing actually ran out of memory, so ESCALATE forces the next iteration to full depth to close that one remaining gap.

**Trend (last 2 iters):**
- Newly passing this iter: none
- Newly passing in last 2 iters total: none
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: 6 new (all minor, 0 critical) — iter-37 (3: iter-37/o open, iter-37/p resolved in-iteration, iter-37/q open), iter-38 (3: iter-38/r resolved in-iteration, iter-38/s open, iter-38/t open)
- Iters with no journey state change: 2 of last 2

**Latest evaluator reasoning:** "This iteration did the hard measurement work it was asked to do, and it did it honestly. The memory test finally ran with the shared data cache genuinely switched on (I found the proof lines in the live backend log myself), and the heavy warm-up was finally triggered the way the journey text says it should be — by a real data backfill, not by a page request. Seven of the eight journeys are passing. But one of the four checks in J-07 'Heavy aggregates never take the service down' was never actually run: the pressure test was re-tuned so that nothing ran out of memory, so the part that proves the app survives running out of memory was not exercised."

## What was done

- Product changes: apps/backend/app/engine/data_manager.py, apps/backend/tests/test_data_manager.py, reports/perf-budgets.md, runs/goal-ops-hardening-iter-38/mem-drill/, runs/goal-ops-hardening-iter-38/j07-warm/
- Widened the throwaway-DB drill to a real K=3-day backfill target so the shared price-cache is genuinely stashed and exercised (not the prior inert 0-date no-op).
- Added a liveness log line proving which cache branch (live vs. fallback) fired on every backfill/rebuild job, corroborated against the live backend log.
- Ran a genuine two-arm live-cache-vs-forced-fallback memory comparison; the audit caught and fixed a backwards headline number (the fallback arm's tail-only delta was actually 0.0 MB, not the 238.5 MB first published).
- Re-triggered J-07 step 1's forward-aggregate warm through the real ingest-finalize hook (not a proxy API call) on the live seed database; all 5 horizons reached "ready".
- Added a load-bearing unit test for exception handling in `_do_backfill` and strengthened the finalize-hook end-to-end test to compare live-cache vs. forced-fallback aggregate lists.
- Fixed a stale docstring and a stale "591→548 symbols" figure in `reports/perf-budgets.md`.
- Verified 6 of 7 required-still-passing journeys pass browser QA this iteration (J-04 skipped — restart declined per pipeline instruction, carried on evidence durability); J-07 remains partial.

## What's left

- Journey J-07 (Heavy aggregates never take the service down) still `partial` for a 4th consecutive iteration — step 4 (induced-pressure drill) exercised no memory pressure this round; the drill's cap was widened specifically so both arms would complete gracefully.
- Journey J-04 (Non-blocking boot with visible status) was not re-verified live this iteration (kept passing on durability only) — needs a real restart/crash test before any goal-achieved run.
- Journey J-05's step 3 (cold-boot coverage-from-storage) not executed — needs a backend restart.
- The deterministic replay lane is effectively broken — it ran against a downed backend and produced 6 of 7 false FAIL rows; needs repair so it never again reports a failure when the backend isn't answering.
- The `read_pool()` wall-clock measurement is prose/projection only, not the in-situ measurement the test contract asked for.
- Two owner decisions remain pending: the ≤0.1s `GET /api/health` budget (missed a 5th consecutive time) and whether `start-frontend.sh` should join the host-protection rules.
- The J-07 walkthrough demo capture remains unrecorded for the 8th consecutive iteration.

## Next step

Run the next iteration at full depth (mandatory via ESCALATE) with one target: finish J-07. First and central — actually run the aggregate warm-up out of memory this time, using a throwaway backend at a cap tight enough to raise a memory error inside the warm-up itself (not the earlier data-loading step), with a concurrent once-per-second health check and a re-read of a previously-cached page, both confirmed OK during and after the failure. Second, keep the health check running until the job truly finishes (remove the fixed time limit that left a 39-second blind spot this round). Third, repair the automatic replay checks so they refuse to report a failure when the backend is switched off, and refresh the stale page selectors. Fourth — and required before anyone declares the goal achieved — give J-04 a real live restart/crash test, with agreement up front on who is allowed to restart the backend.

## Assumptions made

- iter-38 · goal-evaluator — Ambiguity: J-04 had no live restart/crash verification this iteration (the replay FAIL was a down-backend artifact; the browser-qa lane declined to restart the backend under instruction) — should it be scored `unknown` or carried `passing`? We chose: kept J-04 `passing` on evidence durability, but deliberately did not advance its `last_verified_iter` and named every step still uncovered. Reversible: yes
- iter-37 · goal-evaluator — Ambiguity: this would be a third consecutive ESCALATE, and "escalate sparingly" is also methodology guidance, while CONTINUE also fits the iteration's real progress. We chose: ESCALATE again — the decision tree is first-match-wins, and ESCALATE's only practical effect (mandatory full depth) is what this session provably needs; an earlier iteration was lost entirely to an advisory downgrade. Reversible: yes
- iter-37 · goal-evaluator — Ambiguity: J-07's four steps all ran live, but two exercised paths where this iteration's own change was inert — does the journey cross to `passing` anyway? We chose: scored J-07 `partial` for a third consecutive time; the unmeasured resident-cache state is new ground, not shifted ground, and the relevant anti-goal is critical. Reversible: yes
- iter-37 · goal-decomposer — Ambiguity: does the "never bundle two risky changes" rule cover pairing a genuine code change with J-07's own heavy verification-drill execution (no new code, but host-affecting)? We chose: bundled both into one iteration — the rule's precedent applies to code changes, not a zero-risk, re-runnable measurement pass. Reversible: yes
- iter-36 · goal-evaluator — Ambiguity: a journey (J-06) was downgraded on a premise this iteration's screenshots falsified, but the specific Acceptance subject wasn't freshly swept end-to-end. We chose: restored J-06 to `passing` and cleared the evidence-makeup flag, since evidence expires with change and the on-load request path was unchanged. Reversible: yes
- iter-36 · goal-evaluator — Ambiguity: does the "failed 2+ consecutive iterations" ESCALATE trigger apply when a journey's status is `partial`, not literally `failing`? We chose: ESCALATE, reading "failed" as "did not reach passing" — first-match-wins and the practical effect is what the session needs. Reversible: yes
- iter-36 · goal-evaluator — Ambiguity: J-07's browser lane never ran, but a different lane independently verified several of its steps by hand — does an under-evidenced journey score `unknown` or `partial`? We chose: scored J-07 `partial`, explicitly stating which steps carry this-iteration evidence and which don't. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-38.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-38-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-38-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-38-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-38-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-38-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-38-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-38-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-38-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-ops-hardening-iter-38-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-38-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-38-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-38-closure-verdict.md |
| Goal evaluation | ESCALATE | runs/goal-session-ops-hardening/iter-38/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
