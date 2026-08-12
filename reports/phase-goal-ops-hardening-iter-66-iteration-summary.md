# Iteration Summary — goal-ops-hardening-iter-66

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-08-12
**Iteration:** 66

## In plain words

**What you can do now:** Load any stock-ranking, sector, theme, backtest, or research page with an honest "starting up" / "backend unavailable" status while the app boots. Kick off a historical data backfill over any date range with no hidden limit, and get a clear explanation when there's nothing new to fetch. See precomputed rankings and analytics right after data loads, instead of waiting for on-the-fly number crunching. Pages load quickly because they only fetch what they currently need. View backtest results instantly, pulled straight from storage. See a live indicator when the app is still crunching numbers in the background.

**What changed this time:** Nothing new appears on any screen this round. Behind the scenes, the team fixed a bug in the Data Manager's job-history log: a background data-import job that gets killed and resumed used to create two log entries for itself — it now correctly reuses one. They also built one shared stopwatch tool so every speed test measures the app's response time the same way, and used it to learn the app is slower under one specific heavy calculation step than any round has shown before (about 7 out of every 100 health checks took longer than 2 seconds during that step, though the app never crashed or went down).

**What's next:** Next, the team will watch the running app directly while it works through that heavy calculation step (instead of testing the step separately, which has found nothing twice), to pin down exactly why some health checks are slow during it.

## Headline

This round found the answer to the question it was chartered to ask, but not the one it expected.

## Direction

**Signal:** holding
**Why:** J-07 ("Heavy aggregates never take the service down") stays `partial` again this round — no journey moved to `failing` or regressed, and none newly passed, so the shape holds at 7 passing / 1 partial. This round's newly-unified health-poll measurement found the worst breach rate of the session (70 of 1,024 polls over the 2.0s ceiling, concentrated inside the `factor_lab_all_warm` phase) even though availability stayed perfect — zero errors, zero MemoryErrors, all 1,174 polls across both lanes answered. Because a concrete, testable next step exists (watch the live serving process during that phase, rather than re-profile it standalone) instead of every unblock path being human-owned, this reads as holding at 7/8 while the team narrows in on the remaining gap, not stalling.

**Trend (last 2 iters):**
- Newly passing this iter: none
- Newly passing in last 2 iters total: none
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: 11 total, all minor (4 in iter-65, 7 in iter-66); 0 critical
- Iters with no journey state change: 2 of 2

**Latest evaluator reasoning:** This round found the answer to the question it was chartered to ask, but not the answer it expected. The team profiled the coverage-and-membership step twice and found nothing slow in it, so no code was changed there — an honest empty result. It also shipped the two small fixes it promised and one real repair: a job that dies mid-run now reuses its own history row instead of writing a second one. The important news came from the measurement itself: both test lanes now use the same stopwatch, and both say the app is slower under load than any round so far.

## What was done

- Product changes: apps/backend/app/engine/data_manager.py
- Fixed the duplicate job-history bug (iter-64/d): a job killed and resumed inside a graceful 429 pause's two-commit window no longer creates a second `data_provider_runs` row — new `_reopen_interrupted_run_record` helper reclaims the interrupted row, covered by two new tests.
- Profiled `coverage_membership_timeline_refresh`'s call chain twice (solo in-process, and concurrent with the real `/api/health` route) — found zero stalls either time, so no code fix was made or warranted there this round.
- Canonicalized the session's health-poll measurement into one checked-in script, `scripts/qa/poll_health.py` (with a host-load column), replacing the two ad hoc counters that disagreed by ~40x last round.
- Corrected `journey-scripts/J-05.json`'s mis-stated sentinel window to the actual shipped dates (2005-03-01..2016-12-31).
- Ran the TC-1 acceptance drill through the new canonical script during a real live ingest: 1,024 polls, 70 over the 2.0s ceiling (6.8%, the worst rate of the session) — recorded honestly in `reports/perf-budgets.md` Addendum 32.
- Verified 8 of 8 target/required journeys pass merged browser QA and raw deterministic replay (zero overturned rows).

## What's left

- Journey J-07 (Heavy aggregates never take the service down) stays `partial` — 70 of 1,024 health-poll checks exceeded the 2.0s ceiling this round (worst 4.4s), concentrated in the `factor_lab_all_warm` phase.
- A discrepancy between the dev handoff's headline ("1 breach") and the full drill count in `perf-budgets.md` (70 breaches) is logged but not yet reconciled (iter-66/a).
- The owner's 18-times-asked question — whether the 2-second health-check promise applies to long background jobs or short jobs only — remains unanswered.
- Owner sign-off is still pending on the one-line ordering fix in `scripts/automation/browser-qa-phase.sh`.
- Owner cost decision is still pending — this round again ran two real multi-minute ingest jobs and finished well over budget (8,641s against a 3,600s budget, the sixth over-budget round running).
- The J-05 walkthrough capture remains unrecorded for an 8th round.
- A long-carried backlog (iter-29/b through iter-65/d, ~28 items including iter-33/g the Regime Lab, deferred a 32nd time) remains untouched.

## Next step

Keep the next round lean. Re-open the `factor_lab_all_warm` step as the target — despite last round's "do not redo" — because this round's own measurement puts 68 of 70 breaches inside its window with zero breaches in the 382 polls right after it. Change the method, not just the target: watch the live serving process during a real job (an in-app watchdog timing how long a health request waits) instead of re-running the computation in a standalone script, which has found nothing twice. Run one no-job control drill on the same host and script to test whether an idle machine also breaches, since this round's own host-load data argues against "the machine was busy." Small items to also close: iter-66/a (put the whole-run breach count in the handoff), iter-66/c (the mis-placed breach), iter-66/d (the browser lane's timezone error). The owner's 2-second-ceiling policy question, the `browser-qa-phase.sh` ordering fix, and the recurring over-budget cost question all remain open and human-owned.

## Assumptions made

- iter-66 · goal-evaluator — Ambiguity: iteration-state's binding "Do not redo" list barred re-profiling `factor_lab_all_warm`, but this round's drill puts 68 of 70 health-check breaches inside that exact phase's window with zero breaches in the 382 polls right after it, and no rule says what outranks a binding ban when fresh measurement contradicts the finding that created it. We chose: recommend reopening `factor_lab_all_warm` as the next iteration's target, with an explicit method change (watch the live serving process instead of re-running the computation standalone). Reversible: yes.
- iter-66 · goal-decomposer (2 of 2) — Ambiguity: iter-65's "use ONE counter everywhere" could mean canonicalizing the measurement script itself, or editing the browser-qa-agent's own framework instructions/prompt (out of product scope, per iter-56's own precedent). We chose: canonicalize `scripts/qa/poll_health.py` and direct this iteration's own TESTING REQUIREMENTS to invoke it explicitly, without touching any `.claude/agents/` or `agents/` framework file. Reversible: yes.
- iter-66 · goal-decomposer (1 of 2) — Ambiguity: iter-65's next-step item flatly said "stop one job writing two history rows," but the underlying finding (iter-64/d) was only a described pattern, not yet root-caused — taking it as a literal mandate risked a second risky product-code change alongside this iteration's primary GIL-bound work. We chose: scope iter-64/d as investigate-and-fix-only-if-small (a verified single-row fix, or a named cause with the fix explicitly deferred as non-trivial). Reversible: yes.
- iter-65 · goal-evaluator (2 of 2) — Ambiguity: the ledger's "resolved" flag has no defined meaning for a finding (iter-64/a, a one-off `/scanner-runs` error boundary) that was investigated exactly as specified but whose cause could not be found. We chose: mark it resolved with the residual unknown and next step (if it recurs) written into the evidence string, rather than leaving it open indefinitely. Reversible: yes.
- iter-65 · goal-evaluator (1 of 2) — Ambiguity: this round's drill met TC-1's own acceptance bar (0 breaches inside `factor_lab_all_warm`), but J-07 step 2's broader wording ("every poll answers") was still missed once, and the spec explicitly delegates the promotion call to the evaluator. We chose: keep J-07 `partial` — the metric alternates on byte-identical code across rounds and the browser-QA lane's own counter disagreed with the dev's count the same round. Reversible: yes.
- iter-64 · goal-evaluator (2 of 2) — Ambiguity: J-07 step 2 requires every poll to answer HTTP 200 within budget; this round one poll of 930 got no answer at all within the client's 5.0s ceiling — the session's first unanswered poll — while the ceiling itself is the subject of an undecided owner question. We chose: keep J-07 `partial`, log it as iter-64/b, and put the fact in the owner paragraph rather than converting it into a halt. Reversible: yes.
- iter-64 · goal-evaluator (1 of 2) — Ambiguity: AG-8 (critical) requires a widened data basis never crash a page while also prescribing a contained-error-boundary failure mode as the honest outcome; this round's `/scanner-runs` frame showed both at once, and the anti-goal doesn't say which half governs. We chose: score it a minor ledger entry (iter-64/a), keep J-05 `passing`, no critical call. Reversible: yes.
- iter-64 · goal-decomposer — Ambiguity: iter-63's next-step recommendation, read literally, implied two separate real ~15-20 minute ingest jobs this round (a fresh attribution drill plus a live J-05 self-renewal replay) stacked on the one live ingest a lean iteration already carries by default. We chose: piggyback the attribution drill on J-05's own mandatory live backfill, and prove the sentinel resolver's self-renewal property at the unit level instead of a second live 20-minute replay. Reversible: yes.
- iter-63 · goal-evaluator (2 of 2) — Ambiguity: methodology says the `evidence_makeup` flag clears "the moment a fresh capture lands, whatever the outcome," but the only fresh J-07 capture this round was a thin single frame not showing the clause's full crash-free-warm-plus-healthy-check sequence, and J-05 got no capture at all. We chose: clear the flag on J-07 (the rule is literal) and keep it on J-05 (nothing was captured). Reversible: yes.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-66.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-66-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-66-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-66-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-66/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
