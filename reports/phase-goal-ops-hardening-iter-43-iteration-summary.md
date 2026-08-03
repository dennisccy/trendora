# Iteration Summary — goal-ops-hardening-iter-43

**Verdict:** ESCALATE
**Iteration type:** goal-full
**Date:** 2026-08-03
**Iteration:** 43

## In plain words

**What you can do now:** Request a backfill for any date range and get an honest explanation when nothing new needed fetching. Request a wide, multi-month date range without hitting an artificial limit. See a clear "Ready" status badge while the app starts up or recovers from a crash. Browse stocks, sectors, themes, backtests and every research page, each loading only the data it needs. View backtest evidence that always comes from storage, never a live recompute. See a status chip whenever a background calculation is running.

**What changed this time:** Behind the scenes: the team undid an experimental change to how the app loads price history into memory, because it turned out to make memory use slightly worse instead of better. A rare case where a data job fails to even start now correctly shows up as "failed" with an explanation, instead of getting stuck on "running" forever with no updates. The script that starts the website itself now respects the same hardware safety limits as the one that starts the backend.

**What's next:** Next, the team will focus on keeping the app reachable when a heavy background calculation gets stuck — right now it can freeze the whole app for several minutes — and then try the "bring in a brand-new day of data" case that still hasn't been successfully tested.

## Headline

Reverted iter-42's net-negative memory filter; fixed silent stuck-job failures

## Direction

**Signal:** holding
**Why:** No journey moved to fully passing and none regressed this iteration — J-05 "Aggregates are precomputed at ingest" recovered from `regressed` to `partial`, closing the iter-42 stuck-job defect, but its core new-data ingest case remains untested. J-07 "Heavy aggregates never take the service down" failed for a second consecutive iteration: memory now stays safely within the raised cap (32.4%), but a stalled background calculation left the service completely unreachable for several minutes — a different failure mode than last iteration's memory exhaustion. With zero regressions and zero critical anti-goal violations this iteration, direction holds rather than regresses, but the target journey remains unresolved.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: J-04 "Non-blocking boot with visible status" (iter-41); the evaluator log also references two further journeys recovered from `unknown` at iter-41 without naming their IDs in the trimmed excerpt
- Regressions in last 3 iters: J-05 "Aggregates are precomputed at ingest" (iter-42, `unknown` → `regressed`; recovered to `partial` at iter-43)
- Anti-goal violations in last 3 iters: 10 total across iter-41 (2: z, ab — both later resolved), iter-42 (3 new: ac, ad, ae — ad resolved in-audit), and iter-43 (5 new: af, ag, ah, ai, aj — aj resolved in-audit); all minor, 0 critical
- Iters with no journey state change: 0 of last 3

**Latest evaluator reasoning:** The owner raised the memory limit, and that decision worked: the heavy background calculation ran for about 17 minutes and its memory use stayed completely flat at about one third of the new limit. The job that could not even start last round now starts, runs and finishes honestly, so J-05 "Aggregates are precomputed at ingest" is no longer broken. But J-05 was tested on a day that had already been saved, so the part of the journey that matters most — bringing in a brand-new day of data — was never actually tried, and I score it part-done rather than working. J-07 "Heavy aggregates never take the service down" fails again: while a heavy calculation was running the app stopped answering completely for several minutes, and separately 64 of every 100 health checks were slower than the owner's new 2-second promise.

## What was done

- Product changes: apps/backend/app/engine/prices.py, apps/backend/app/engine/data_manager.py, apps/backend/app/api/data.py, incredible_auto_dev/scripts/start-frontend.sh, project-extensions/host-guard/host-guard.env
- Reverted iter-42's `_BarCache.prefill` symbol filter back to the unfiltered whole-table scan after the auditor proved it was a net +5.1% memory regression, not the claimed 2.5% win.
- Added an honest failure path for backfill/resume jobs that fail to launch: they now mark `failed` with a message and return HTTP 503, instead of silently sitting at "running" forever (widened mid-iteration by the auditor to also catch `MemoryError`, not just `RuntimeError`).
- Extended the host machine's CPU/thread safety caps to the frontend launch script, matching the backend launcher.
- Live re-verified J-05 and J-07 against the owner's raised 8192 MB memory cap: memory stayed flat at 32.4% of cap over a 1,001s observed warm, but the service still went fully unreachable for several minutes due to a stalled (not memory-starved) background calculation.
- Verified 6 of 8 target/required journeys (J-01, J-03, J-04, J-06, J-08, J-09) pass browser QA this iteration; J-05 partially verified; J-07 failed.

## What's left

- Journey J-07 "Heavy aggregates never take the service down" failing — the service went fully unreachable for several minutes when a background calculation stalled; no fix has landed yet.
- Journey J-05 "Aggregates are precomputed at ingest, never on the fly" partial — the core case of ingesting a brand-new, never-before-saved day has still never completed in testing (the one live attempt ran 1,001 seconds without finishing).
- The app's start-up script has no shutdown time limit, so one stuck background job can hold the whole app hostage — a concrete, unaddressed lead for next iteration.
- Health-check response times run slower than the owner's 2-second budget during heavy background work (up to 6.6 seconds, and getting worse) — unresolved, suspected to be an amplified version of a known slow price-reading path from two iterations ago.
- The price-history loading code is memory-efficient in format but still loads a symbol's full history at once rather than a bounded slice — a long-carried, accepted limitation.
- Two evidence screenshots from this iteration's testing are accidentally identical files, with one wrongly standing in as proof for both a pass and a failure — needs fixing so evidence review can be trusted.
- This iteration's QA report said "no blockers to shipping" 32 minutes before the browser test found the app failing — a process gap in how quickly the team's own reports catch problems.

## Next step

Full depth again, and the order matters. (1) Stop the app from going silent when a heavy calculation gets stuck — the backend start script has no shutdown time limit, so give shutdown a deadline and make a calculation that stops progressing give up and say so instead of freezing. (2) Find out why the calculation stalled at zero of five horizons after 137 seconds — the diagnostic tool built for exactly this three rounds ago has still never been used on a live freeze. (3) Re-test J-05 "Aggregates are precomputed at ingest" on a day that has NOT been saved before, which is what the journey actually asks for. (4) Deal with the slow health checks — 64 of every 100 were over the owner's new 2-second promise and getting worse; either measure the suspect slow price-reading path cleanly on its own (one trigger, no side probes) or fix it. (5) Several small, already-scoped fixes: make a failed job's saved message name the real reason instead of a generic summary, give the Retry action the same honest error code as its siblings, and drop a stray unrelated file change. (6) Fix how evidence is captured — two screenshots this round were duplicate files, with one cited as proof for both a pass and a failure.

## Assumptions made

- iter-43 · goal-evaluator — Ambiguity: decision tree C.4's first clause matches (J-07 failed 2+ consecutive iterations), but this is the seventh ESCALATE in eight iterations and this iteration already ran full depth. We chose: ESCALATE — the audit lane caught load-bearing findings (a latency regression and a total outage) that review, QA and the deterministic closure gate all passed over, the seventh consecutive iteration where only the auditor caught the substantive defect. Reversible: yes
- iter-43 · goal-evaluator — Ambiguity: J-05's merged results row reads PASS with real dated evidence, but its own step 1 requires an unsnapshotted day and the tested day was already snapshotted, so the ingest-to-fresh-aggregates half was never exercised. We chose: `partial`, not `passing`, with every unexercised step named. Reversible: yes
- iter-43 · goal-decomposer — Ambiguity: the owner's amendment commissions four follow-up actions "for the iterations that follow" without saying whether they are one iteration's scope, and separately makes a warm-seam rewrite permissive, not mandatory. We chose: bundle the revert, job-launch fix, host-guard extension, and live re-verification into one iteration, but make the warm-seam rewrite conditional on what the live measurement actually shows. Reversible: yes
- iter-42 · goal-evaluator — Ambiguity: the six required-still-passing journeys had genuine dated evidence, but it was captured minutes before that same run's service outage; it is unclear whether evidence taken before an outage still certifies a journey. We chose: keep all six `passing`, with the caveat recorded verbatim in each journey's note — the outage was induced by a different journey's own warm, not these six's own paths. Reversible: yes
- iter-42 · goal-evaluator — Ambiguity: J-05's immediate prior status was "unknown" (not tested), not "passing", so the decision tree's literal "moved passing → failing" clause for REGRESSION doesn't strictly match. We chose: score it `regressed` (and REGRESSION) anyway — the schema defines `regressed` as "was passing in a prior iteration," and J-05 was verified passing at iter-39; treating an untested gap as erasing a prior pass would let a regression go unlabeled. Reversible: yes
- iter-42 · goal-decomposer — Ambiguity: the prior evaluator offered two dispositions (write a real per-symbol memory bound, or amend goal.md's success criteria) without marking either as the owner's call, after four prior attempts at the same code already fell short. We chose: plan a fifth, narrower-scoped dev attempt (reusing an already-proven filtering pattern from a sibling function) rather than escalating to the owner, since a genuinely new lever exists. Reversible: yes
- iter-41 · goal-evaluator — Ambiguity: J-04 moved `unknown` → `passing` on a replay script covering only 2 of the journey's 6 steps, and the code behind an untested step had just changed. We chose: `passing`, with every uncovered step named — the tested half is fresh and dated, the untested part only makes checkpoints more frequent (unit-proven), and scoring it `unknown` would discard real evidence. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-43-what-to-click.md`:

1. Open `http://localhost:3255/` in your browser
2. Click "Data Manager" in the left sidebar (or go directly to `http://localhost:3255/data`)
3. Type `2005-04-12` in "Start date" and `2005-04-12` in "End date", then click the "Start" button (accent button, play icon)
4. Back on `http://localhost:3255/data`, type `2025-06-01` in "Start date" and `2026-07-17` in "End date" (a wide, 412-day range), then click "Start"
5. While that job keeps running, watch the top-bar badge for a couple of minutes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-43.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-43-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-43-review.md |
| Browser QA | FAIL | reports/phase-goal-ops-hardening-iter-43-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-43-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-43-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-43-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-43-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-43-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-ops-hardening-iter-43-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-43-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-43-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-43-closure-verdict.md |
| Goal evaluation | ESCALATE | runs/goal-session-ops-hardening/iter-43/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
