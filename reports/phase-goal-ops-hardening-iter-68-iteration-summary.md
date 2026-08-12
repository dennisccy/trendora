# Iteration Summary — goal-ops-hardening-iter-68

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-08-12
**Iteration:** 68

## In plain words

**What you can do now:** Pull any historical date range for backfills with no hidden limit, and get a clear explanation when there's nothing new to fetch. See an honest, never-blank status message while the app starts up. Load backtest results and other aggregates instantly from storage rather than waiting for a live recalculation. Browse pages that only load the data they need, and see a clear signal whenever the app is crunching numbers in the background, plus when it's finished.

**What changed this time:** Nothing new to look at on screen — this round worked inside the health-check endpoint (the quiet "is the app OK?" check the app answers every second). It now keeps a third, off-by-default stopwatch on itself, timing exactly how long its own work takes on each check. That let the team name, for the first time, where most (about 79%) of one slow reply actually went. The team also finally ran a test file for that same code that had been skipped last round, and it passed (17 of 17).

**What's next:** Next, the team will dig deeper inside that one slow part of the health check to find exactly which piece of work is the culprit, and turn its stopwatch on in every lane that tests it — while still waiting on you to say whether the 2-second speed promise should apply to long background jobs or just short ones.

## Headline

Health check now times its own handler body, naming 79% of the one slow reply for the first time.

## Direction

**Signal:** holding
**Why:** No journey changed pass/fail state this round — J-01, J-03, J-04, J-05, J-06, J-08, J-09 stay passing and J-07 stays `partial` (unchanged since iter-51) — but J-07 got its first majority-named breach attribution (79.4% via the new `handler_compute_s` sample) and the previously-skipped `test_health.py` finally ran clean, so the diagnostic path is narrowing rather than stalling. The next round has a specific, code-level target (splitting `handler_compute_s` into its four constituent operations) rather than another phase-level guess.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: none
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none (AG-1–AG-10 all OK in every eval.md Anti-goal Check table for iters 64-68)
- Iters with no journey state change: 5 of 5

**Latest evaluator reasoning:** This round added a third timer inside the health check and, for the first time in this project, it says where the slow time goes: about 79% of the one slow answer was spent inside the health check's own body, not waiting in a queue. All 1,609 health checks in the round answered normally, the app logged no errors at all, and the previously skipped test file for the changed code was finally run and passed (17 of 17). J-07 "Heavy aggregates never take the service down" still stays partial, because 10 of those 1,609 answers took longer than the 2-second promise (the slowest was 4.19 seconds).

## What was done

- Product changes: apps/backend/app/engine/health_watchdog.py, apps/backend/app/api/health.py, apps/backend/tests/test_health_watchdog.py
- Added a third watchdog sample (`handler_compute_s`) timing the health-check handler's own body, sharing the existing env flag, writer, and log file with the two prior samples (`queue_wait_s`, `loop_lag_s`).
- Ran a 17m10s live-job drill plus a 5.5-minute idle-control drill with the watchdog armed; joined the one breach and named 79.4% of its magnitude to `handler_compute_s` (80.4% combined with the other two samples) — the session's first majority-attributed breach.
- Ran the previously-skipped `test_health.py` module as an ordinary step (17/17 passed, ~64 min) — closes iter-67/e.
- Added 3 new unit tests (11/11 passing in `test_health_watchdog.py`) proving flag-off writes nothing and flag-on records `handler_compute_s` alongside `queue_wait_s`; response body stays byte-identical.
- Corrected two `reports/perf-budgets.md` Addendum 33 write-up defects (a misattributed loop-lag sample; a distribution conclusion that omitted the phase-level share) — closes iter-67/a and iter-67/b.
- Verified 7 of 8 journeys pass browser QA/deterministic replay (merged PASS 8/8, raw replay PASS 8/8, zero overturns); target journey J-07 remains `partial`.

## What's left

- Journey J-07 (Heavy aggregates never take the service down) is `partial` — 10 of 1,609 health-check polls this round took over the 2-second ceiling (worst: 4.19s), while availability itself is unbroken (zero non-200 responses, zero errors logged).
- ~19.6% (0.497s) of the one breach remains unattributed even after three watchdog samples; the likely remaining source (pre-receive overhead: TCP handshake, CORS middleware, the poll client's own overhead) is named but not yet measured.
- The breach landed in `coverage_membership_timeline_refresh` for a second consecutive round rather than `factor_lab_all_warm`, while the sub-2s elevation stays concentrated in `factor_lab_all_warm` (120-127 of ~131-138 over-1.0s polls) — the crossing point moved, the phase-level signal didn't.
- The J-05 walkthrough capture remains unrecorded for a 10th round (no showcase/demo lane ran this round).
- Three owner questions remain unanswered for the 19th-20th round running: whether the 2-second health-check ceiling applies to long background jobs or short jobs only; permission to fix a one-line ordering bug in `scripts/automation/browser-qa-phase.sh`; and a cost-overrun decision — this round ran 2.9x over its time budget, the 8th consecutive over-budget round.

## Next step

LEAN depth for iteration 69. Order: (1) split `handler_compute_s` into its parts — time the three DB reads, `compute_readiness`, and `compute_preflight` separately, with the same flag/writer/file; (2) arm `TRENDORA_HEALTH_WATCHDOG=1` for the whole iteration including the browser-QA lane's backend, so the lane that actually caught this round's 9 worst breaches also records their components; (3) report the pre-receive gap (poller send timestamp vs. server `t_received_wall`) from artifacts already on disk — no new instrument needed, closes most of the "unnamed 19.6%"; (4) fix two small write-up items (iter-68/a, iter-68/c); (5) record the still-unrecorded J-05 walkthrough if a showcase lane runs. The owner is still asked, for the 20th round, to decide whether the 2-second health-check ceiling applies to long background jobs or short jobs only, to approve the `browser-qa-phase.sh` ordering fix, and to make a cost decision on this session's repeated over-budget rounds.

## Assumptions made

- iter-68 · goal-evaluator — Ambiguity: J-07 step 2 doesn't say which polls count toward "every poll answers HTTP 200" — the dev's own chartered drills (1,039+330 polls, 1 breach) vs. the browser-QA lane's separate drill (240 polls, 9 breaches) during a heavier ambient workload. We chose: score J-07 against the union of all 1,609 polls this round (10 breaches, worst 4.190s) rather than the dev drill's smaller headline, since both lanes now share one canonical script/schema and reporting the smaller number would round toward "fixed." Status stays `partial` either way. Reversible: yes.
- iter-67 · goal-evaluator — Ambiguity: J-07 has four acceptance steps; this round re-ran steps 1-2 in full but step 3 (VmPeak) got only a non-authoritative point read and step 4 (memory-pressure abort) wasn't re-run at all — no rule says whether an un-re-measured step should worsen the journey's status. We chose: carry steps 3 and 4 forward on evidence durability since the warm-path code they test is byte-identical to when they last passed, and keep J-07 at `partial` on step 2's ceiling alone rather than downgrading further. Reversible: yes.
- iter-67 · goal-decomposer — Ambiguity: iter-66's next-step named the required method only conceptually ("an in-app watchdog timing how long a health request waits") — consistent with several different implementations (APM tracing, thread-stack sampling, ASGI timestamps, event-loop-lag probe). We chose: the smallest option that still answers the question — an ASGI-layer timestamp pair plus a periodic loop-lag probe, gated behind a new off-by-default env flag, writing to a new diagnostic-only log. Reversible: yes.
- iter-66 · goal-evaluator — Ambiguity: the binding "Do not redo" list forbade re-testing `factor_lab_all_warm` (four prior profiling passes found nothing), but this round's own drill put 68 of 70 health-check breaches inside that exact phase's window with zero breaches right after it — nothing says what outranks a binding ban when fresh measurement contradicts it. We chose: recommend re-opening `factor_lab_all_warm` as the next target, using a different method (watch the live serving process instead of re-profiling standalone), since the ban was written on a null result, not on a measurement showing the phase is fast in production. Reversible: yes.
- iter-66 · goal-decomposer (2 of 2) — Ambiguity: iter-65's "use ONE counter everywhere" instruction could mean canonicalizing the measurement script itself, or editing the browser-qa-agent's own framework instructions/prompt — the latter is out-of-scope framework-maintenance territory for a product iteration. We chose: canonicalize `poll_health.py` into one checked-in script and direct this iteration's own TESTING REQUIREMENTS to invoke it explicitly, rather than editing any framework/agent instruction file. Reversible: yes.
- iter-66 · goal-decomposer (1 of 2) — Ambiguity: iter-65's next-step phrased "stop one job writing two history rows" as a guaranteed-outcome directive, but the underlying finding was only "explained by mid-job backend restarts," not root-caused to a single fix. We chose: scope the item as investigate-and-fix-only-if-small, since committing to a guaranteed fix ahead of root-causing it risks a second risky code change alongside this iteration's primary work. Reversible: yes.
- iter-65 · goal-evaluator (2 of 2) — Ambiguity: the ledger's `resolved` flag has no defined meaning for a finding that was investigated exactly as specified but whose cause couldn't be found (a one-off contained error boundary on `/scanner-runs`). We chose: mark it resolved with the residual unknown written into the evidence string and a named next step if it recurs, rather than leaving it open indefinitely with no defined action. Reversible: yes.
- iter-65 · goal-evaluator (1 of 2) — Ambiguity: this round met its own stated acceptance bar (TC-1: 0 breaches inside `factor_lab_all_warm`) but J-07's own broader step-2 wording ("every poll answers HTTP 200") was still breached once elsewhere, and the spec explicitly delegates the call to the evaluator. We chose: keep `partial`, since the same metric has alternated clean/elevated on unchanged code across rounds and the same round's browser-QA lane measured a different breach count with its own counter. Reversible: yes.
- iter-64 · goal-evaluator (2 of 2) — Ambiguity: one poll of 930 got no answer at all within the client's 5-second timeout — the first time the "every poll answers" clause (as opposed to the 2-second ceiling) was breached, on a journey whose other half is an undecided owner question. We chose: keep `partial` rather than treating it as a new regression trigger, since a single client-side timeout isn't evidence the server stopped answering (zero non-200s, zero errors logged) and the journey's core promise wasn't falsified by one slow answer. Reversible: yes.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-68.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-68-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-68-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-68-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-68/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
