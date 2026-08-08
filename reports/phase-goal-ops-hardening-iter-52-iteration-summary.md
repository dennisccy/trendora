# Iteration Summary — goal-ops-hardening-iter-52

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-08-08
**Iteration:** 52

## In plain words

**What you can do now:** Start a historical data backfill for any date range and get an honest on-screen message when there's nothing new to fetch. Request more than a year of history in a single job without hitting a hidden limit. See backtest results appear instantly, since they come from storage rather than a live recalculation. See an honest "still working" indicator whenever the app is crunching numbers in the background.

**What changed this time:** Behind the screens, the part of the app that crunches years of stock data in the background got reworked. The big sorting and memory-cleanup steps used to freeze everything for over a second at a time, so the little "Ready" status light could occasionally go quiet during a heavy data-loading job. Now that light answers almost every single check during the same kind of job — only 2 missed out of 1,285, down from 19 out of 892 before — and the Factor Lab research page's background number-crunching finished about a fifth faster. No page, button, or number changed appearance.

**What's next:** Next, the team will re-check that this fix really works with no new code, then apply the same treatment to the two remaining data-loading steps that can still make the status light go quiet.

## Headline

Chunked sorting and a paused garbage-collector cut the finalize tail's worst CPU stalls

## Direction

**Signal:** holding
**Why:** Zero journeys changed status this iteration — J-04, J-05, J-06 and J-07 all stay `partial`, and no critical anti-goal violation fired, so this isn't a regression either. The health-stall fix is real and reproduced independently at the engineering level (0/1,021 non-answers solo, 2/1,285 under concurrency — versus 19/892 before), but the only journey-level lane run predates the actual fix by 58 minutes, breaching the TC-9 lane-must-run-last rule for the sixth time in seven rounds, so nothing could legitimately move up the scoreboard yet. Direction reads "holding": real progress happened, but it hasn't been independently certified.

**Trend (last 2 iters):**
- Newly passing this iter: none
- Newly passing in last 2 iters total: none
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: iter-51 opened 5 new findings (0 critical); iter-52 logged 5 minor violations — AG-8 (pre-existing Regime Lab memory error), TC-9 sequencing, Definition-of-Done honesty, golden-script quality, walkthrough capture (0 critical)
- Iters with no journey state change: 1 of last 2 (iter-52 only; iter-51 moved J-07 failing → partial)

**Latest evaluator reasoning:** This round did the hardest thing well and then could not prove it. The team found the real reason the app stops answering during a data job — two pieces of work the computer cannot be interrupted during — and fixed both, and the fix is honest and well tested. But the eight journey checks ran *before* that fix was written, so the only independent check of the round measured software that no longer exists, and it failed the two journeys the round existed to close. The pipeline noticed this itself and stopped: the run is marked "blocked", waiting for the checks to be run again.

## What was done

- Product changes: apps/backend/app/engine/data_manager.py, apps/backend/app/engine/forward_testing.py, apps/backend/app/engine/research.py, apps/backend/tests/test_data_manager.py, apps/backend/tests/test_forward_testing_aggregates_streaming.py, apps/backend/tests/test_research_streaming.py, apps/backend/tests/test_start_backend_script.py
- Diagnosed the real root cause via live GIL-stall profiling — an unyielding sort call (1.09-1.23s per call, 55 times) plus 154 uninterruptible garbage-collection sweeps (121s total) inside the Factor Lab warm-up; the first pass's plain yield points had made the health-check gap worse (22 misses vs. a 9-miss baseline), not better.
- Implemented a chunked cooperative sort (50,000-row slices merged with `heapq.merge`, object-identity verified byte-identical) and a per-entry paused garbage collector with bounded release of spent records — cut the Factor Lab warm-up 19% (571.94s → 462.49s) and the worst single stall from 1.23s to 0.045s.
- Live acceptance drill on the shipped tree: 0/1,021 health-check misses solo (down from 22), and 2/1,285 (0.16%) under concurrency for the first time (down from 19/892, ~14x better) — the concurrent case is not yet fully zero.
- Added the missing throwaway-process fault-injection test for J-07 step 4 (memory error mid-job) and re-ran it live on the shipped tree — passed in 1,076s.
- Measured and recorded the Factor Lab page's real-browser load time in `reports/perf-budgets.md` (owed for two rounds) — interactive in ~21-25ms, data call 10-65ms warm.
- Corrected two audit-flagged doc/comment overstatements: the sort's byte-identity precondition, and the paused collector's true scope (the whole warm phase, not "seconds").
- Verified 2 of 4 target journeys (J-04, J-06) pass browser QA; J-05 and J-07 show FAIL in the lane's own run, but that run predates the fix by 58 minutes (TC-9 breach) — the lane must re-run against the frozen, fixed tree before the iteration can be scored.

## What's left

- Journey J-04 (Non-blocking boot with visible status) stays partial — boot timing and crash/restart both hold, but no screenshot exists at all, so the badge/banner half and the crash logfile remain unobserved.
- Journey J-05 (Aggregates are precomputed at ingest) stays partial — ingest-time storage holds, but step 4 (health stays responsive throughout) still fails: 2 of 1,285 (0.16%) health checks missed under concurrency, far better than before but not zero.
- Journey J-06 (Pages load only what they need) stays partial — its Regime Lab step only checks the page heading while that page's own data call is throwing a pre-existing, unrelated memory error live; the code-level "no unbounded scan" audit is still missing.
- Journey J-07 (Heavy aggregates never take the service down) stays partial — memory headroom and induced-failure recovery both now hold, but the same 2-of-1,285 health-check miss applies here too.
- The 8-journey browser/replay lane ran 58 minutes before the actual fix landed and must be re-run against the now-frozen, fixed tree before this iteration can be scored — this is the run's current blocker (`status.json`: blocked / audit_qa_failed).
- Two finalize-tail steps — the snapshot-write stage and the market-phase warm-up — never received the chunked-sort/paused-cleanup treatment; together they account for 11 of the 16 remaining slow health checks (worst 3.8s).
- The status check itself is not cheap: it does about 0.14 seconds of real database work on every call, already above the product's own 0.1-second steady-state target.
- A single research-page request can still wait more than ten minutes if it lands during a heavy data job — newly measured, not newly caused.
- The 20-minute finalize-tail budget runs 5% over when a research page is being used at the same time as a data job (1,261s vs. 1,200s) — on-budget only when nobody else is on the site; whether it should hold under both conditions is an open owner question.
- The Regime Lab page (separate, pre-existing issue, deferred 18 rounds running) threw two live memory errors during this round's own checking; its own journey check only verifies the page title, not its data.

## Next step

FULL depth is required next (mandatory via ESCALATE). First, re-run the eight journey checks with zero new code — the app hasn't changed since 03:55 and the run is already blocked waiting for exactly this; the checks that ran this round tested the app before the repair landed, so they cannot say whether the repair worked. Then finish the same chunked-sort/paused-cleanup treatment in the two finalize-tail steps that never got it — the coverage refresh and the market-phase warm-up, which now account for the remaining health-check misses. Then run the eight checks one final time and change nothing afterward — better, move the check to run after the final review, since this ordering rule has now broken in six of the last seven rounds. Separately, look at the Regime Lab page: its data call ran out of memory twice during this round's own testing, its check only verifies the page title, and it has been deferred for eighteen rounds. Two owner decisions remain open: whether a future round may move the heavy calculation into a separate process (asked at rounds 50 and 51), and whether the 20-minute finalize-tail budget is meant to hold when the app is also serving users, since it was met idle and missed by 5% when busy.

## Assumptions made

- iter-52 · goal-evaluator — Ambiguity: the browser-lane results file records FAIL for both UT-J-05 and UT-J-07, but the methodology doesn't say whether a lane FAIL forces a journey to `failing`. We chose: score both `partial`, not `failing` — it matches the literal shape (most steps hold, one still fails) and stays consistent with how J-07 was already scored last round for the same unmet step. Reversible: yes.
- iter-52 · goal-evaluator — Ambiguity: the 8-journey lane's results predate this iteration's actual code fix by 58 minutes (a TC-9 sequencing breach); neither goal.md nor the methodology says whether a stale lane's rows may still be used to score journeys. We chose: score from the lane's rows anyway, cross-checked against shipped-tree measurements verified independently (screenshots opened, database rows read, error counts recounted) — refusing to score would make all four target journeys "unknown," strictly worse information than what was actually confirmed. Reversible: yes.
- iter-52 · goal-decomposer — Ambiguity: the prior evaluator's recommendation to "check first, change no code, then fix" reads as wanting a full journey-lane run before this iteration's code change, but the standing rule says the lane must run LAST, once, after all code lands — the two read as in tension. We chose: run ONE full 8-journey lane at the end, after this iteration's scheduling fix lands, covering both this iteration's and the prior iteration's changes in a single pass, rather than adding a separate pre-dev check-only pass. Reversible: yes.
- iter-52 · goal-decomposer — Ambiguity: whether to fix the health-check stalling by scheduling the existing in-process computation more cooperatively (yield points) or by moving the heavy work to a separate process — goal.md doesn't choose between them, and the owner's question about this (first asked at iter-51) is still unanswered. We chose: in-process cooperative-yield scheduling, not a new process/worker boundary — it directly targets the diagnosed cause without a new structural risk, though it may leave some residual latency an off-process fix would fully close. Reversible: yes.
- iter-51 · goal-evaluator — Ambiguity: the screenshot cited for J-05's "run record lists refreshed aggregates" claim doesn't actually show that line on screen — the methodology says a screenshot outranks prose, but not what to do when the citation itself is a capture defect. We chose: treat it as a capture defect, not a failed assertion, and keep the claim — the underlying value was independently verified in the database and shown in full in a different screenshot from the same round. Reversible: yes.
- iter-51 · goal-evaluator — Ambiguity: J-07 had no dedicated journey-level executed row this round, only cross-cutting evidence — goal.md doesn't say whether a journey may move up on indirect evidence like that. We chose: move J-07 from `failing` to `partial` — the specific facts that made it `failing` (a 12-45-minute outage, then a 17-30-minute wedge) were verified absent, and its current shape (one step holds with a large margin, one step fails) literally matches the `partial` definition. Reversible: yes.
- iter-51 · goal-decomposer — Ambiguity: the rule that one iteration may carry one risky journey doesn't say how many already-diagnosed small sub-fixes may ride inside that one risky change. We chose: bundle the `factor_lab_all` ingest-warm with a separate, small, already-diagnosed memory-bound fix as ONE risky change for the iteration, since both sit in the same module and the second fix needed no new diagnosis. Reversible: yes.
- iter-51 · goal-decomposer — Ambiguity: not captured in the pre-trimmed log excerpt (this entry's text began mid-sentence). We chose: warm `factor_lab_all_cached`'s default all-history key inside the existing ingest finalize tail, reusing an already-audited code pattern, rather than introducing a new process/IPC boundary. Reversible: yes.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-52.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-52-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-52-review.md |
| Browser QA | FAIL | reports/phase-goal-ops-hardening-iter-52-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-52-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-52-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-52-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-52-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-52-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-ops-hardening-iter-52-ux-regression.md |
| QA | FAIL | reports/qa/goal-ops-hardening-iter-52-qa.md |
| Audit | FAIL | docs/handoffs/goal-ops-hardening-iter-52-audit.md |
| Goal evaluation | ESCALATE | runs/goal-session-ops-hardening/iter-52/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
