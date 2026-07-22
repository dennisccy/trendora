# Iteration Summary — goal-ops-hardening-iter-8

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-22
**Iteration:** 8

## In plain words

**What you can do now:** You can browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. You can pull in any historical date range during a data update with no size limit, and the system tells you plainly when there's nothing new to add. Whether the app is starting up, recovering from a restart, or has genuinely gone down, the on-screen status message tells you the truth about what's happening. (These are the same capabilities as last round — this round's work happened entirely behind the scenes and its effect on the app has not yet been re-confirmed by hands-on testing.)

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The team hardened how the app copes with running low on memory during a big data update: previously, one memory hiccup made the app immediately try the next task anyway, digging the hole deeper; now it stops that one step early, cleans up, and moves on to the next independent task instead. A careful second check also found and fixed a broken safety test hiding behind a false "passed" result. However, this round did not include the usual hands-on run-through of the app to confirm the fix holds up and nothing else broke — that confirmation is still pending.

**What's next:** Next, the team will click through the app to confirm the memory fix genuinely works and nothing else regressed, then tighten up how the app's safety limits (CPU and memory caps) actually get switched on when it starts.

## Headline

Ingest warm loops now back off on MemoryError instead of hammering the next allocation

## Direction

**Signal:** regressing
**Why:** The backend memory-handling fix itself is real and well-tested, but J-05 stays recorded as `regressed` (iter-7's still-unresolved regression, carried forward unverified) and the critical AG-8 anti-goal violation remains unresolved — this iteration's browser-qa lane was skipped entirely, so the fix was never confirmed against the app itself and J-01/J-03/J-04 dropped from `passing` to `unknown` for lack of re-verification. Until a qualified browser-qa pass confirms J-05's recovery, the project's honest state is still "known regression, unconfirmed fix," not forward progress.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-05 (iter-4), J-04 (iter-6), J-05 (iter-6)
- Regressions in last 5 iters: J-05 (iter-7)
- Anti-goal violations in last 5 iters: 2 (AG-8 critical unresolved — iter-7; AG-10 minor unresolved — iter-8)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** iter-8's backend fix for J-05's regression is real, correctly scoped, and independently audited: all four ingest-finalize warm loops now catch MemoryError distinctly and back off instead of hammering the next allocation, the audit found and fixed a serious test-integrity defect on top of it, and the literal DoD test command now reports 134 passed / 1 skipped / 0 failures. But the iteration verified nothing — the browser-qa lane was skipped outright on a "Frontend Present: no" rule, so J-05's spec-mandated four-step re-verification never happened and the J-01/J-03/J-04 replay lane never ran. Audit (V1/V2) and closure (CLOSURE-FAIL) independently reached the same conclusion, and the audit states explicitly: "The evaluator must not flip J-05 regressed → passing on this handoff alone." I did not.

## What was done

- Added distinct `MemoryError` handling to all four ingest-finalize warm loops (per-date coverage, per-date market-phase, per-horizon forward-aggregates, per-claim drawdown-expectations): on the first `MemoryError` in a loop it now stops that loop, releases memory, and logs honestly instead of retrying under pressure.
- Added 9 new unit tests covering first-item abort, partial-success honest reporting, same-process recovery with no leaked lock, and byte-identity to a fresh compute.
- Ran a live back-to-back heavy-ingest measurement (real spawned backend, real jobs) under host-guard protections: 468/468 health polls succeeded, peak memory 3,465.6 MB — a 43.6% margin under the enforced 6144 MB cap.
- Audit found and fixed a serious shipped test-integrity defect (a spliced-in test block had silently deleted another test's real assertions and left the new test with a guaranteed `NameError`), plus a memory-release-timing gap and the byte/char logfile-slice bug — the literal DoD test command now runs 134 passed / 1 skipped / 0 failures.
- Recorded a new dated section in `reports/perf-budgets.md` documenting the live measurement, root cause, and fix.
- Browser QA was skipped this iteration on a "Frontend Present: no" rule — 0 target journeys were verified via browser QA; J-05's spec-mandated re-verification and the J-01/J-03/J-04 replay lane never ran.

## What's left

- Journey J-05 ("Aggregates are precomputed at ingest, never on the fly") stays `regressed` — the fix is coded and unit-tested, but the spec-mandated browser-qa pass over all 4 acceptance steps has not run against the current build.
- Journeys J-01, J-03, J-04 dropped from `passing` to `unknown` this iteration — their required-still-passing re-verification lane (golden replay / LLM acceptance) never ran.
- Journey J-06 ("Pages load only what they need") stays `partial` — unchanged, out of scope this iteration.
- Closure blocker: no browser-qa evidence directory or raw `.llm.md` exists for iter-8; `status.json` records `browser_checks_run: false`.
- AG-8 (critical): memory exhaustion + ungraceful health hang is materially mitigated but not closed — the clean live run never actually hit enough memory pressure to exercise the new abort branches, and it ran under different host-affinity conditions than iter-7's failing run.
- AG-10 (minor): launch scripts (`scripts/start-backend.sh`, `scripts/dev.sh`) still don't apply `host-guard.env`'s CPU-affinity mask or BLAS/OMP thread caps.
- Still deferred: the separate on-load `/api/backtest` → `forward_aggregates_cached` MemoryError (J-06/AG-8), and the J-05/J-06 `demo.sh --session-live` walkthroughs owed before the GOAL_ACHIEVED gate.

## Next step

Iteration 9 (the last budgeted iteration), full depth, a pure verification-and-compliance closeout with no new features: (1) run browser-qa over J-05's four acceptance steps on the audit-repaired build with host-guard active, driving step 4 via the now-opt-in `TRENDORA_RUN_HEAVY_INGEST_TEST=1 pytest ...::test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap` (never executable before the audit's fixes — run it at least once), read the raw `.llm.md`, retain the sampler CSV, and replace the "SKIPPED" stub with the real outcome; (2) run J-01/J-03 golden replay and J-04 LLM acceptance and emit a regression-replay-results artifact — this is what moves three journeys out of `unknown`; (3) close the AG-10 launcher gap by adding HOST-GUARD blocks applying `host-guard.env`'s taskset mask and BLAS/OMP caps to `scripts/start-backend.sh` and to `dev.sh`'s backend subshell only (never the frontend subshell); (4) fix the harness misrouting so "Frontend Present: no" cannot suppress browser-qa when the spec's testing requirements name browser journeys; (5) if capacity allows, memoize the libc handle used by `_release_process_memory()` and tighten the heavy test to reject "partial" status. Still deferred: the on-load `/api/backtest` MemoryError (J-06/AG-8) and the J-05/J-06 `--session-live` walkthroughs — both need scope or explicit human deferral before the GOAL_ACHIEVED gate.

## Assumptions made

- iter-8 · goal-decomposer — Ambiguity: iter-7's evaluator offered three undirected recovery options for J-05's AG-8 memory exhaustion without mandating one, and didn't specify whether "fail-fast" recovery meant new code in health.py or removing the underlying memory pressure. We chose: bound peak RAM at the source — harden the per-item warm loops to catch MemoryError distinctly and stop+gc.collect() on first occurrence, rather than raising the memory cap or isolating ingest into a separate process; no new code in health.py itself. Reversible: yes
- iter-8 · goal-evaluator — Ambiguity: J-05 still carries status `regressed` and AG-8 is still unresolved, but that regression is iter-7's, already halted on and human-acknowledged, with iter-8 dispatched as the sanctioned recovery; the methodology's self-check says any `regressed` status forces a REGRESSION verdict, while the decision tree fires only on a journey that moved passing→failing this iteration. We chose: treated the decision tree as operative and returned CONTINUE — no journey moved passing→failing in iter-8 and no new critical violation was introduced; J-05 stays regressed and AG-8 stays unresolved (nothing softened), only the halt was withheld. Reversible: yes
- iter-8 · goal-evaluator — Ambiguity: AG-10 (critical anti-goal) has an unsatisfied MUST-apply clause (host-guard.env's caps aren't applied by the launch scripts), but goal.md doesn't say whether an unmet MUST-apply clause is as severe as the REGRESSION trigger it names (stripping a HOST-GUARD block). We chose: recorded it as minor, unresolved rather than critical — nothing was stripped or weakened, and goal.md's own notes treat closing the gap as scheduled next-iteration work; flagged as blocking GOAL_ACHIEVED and stated uncertainty about the severity call. Reversible: yes
- iter-7 · goal-decomposer — Ambiguity: none of the four numbered depth triggers literally fire for this iteration's narrow one-function fix, but iter-6's evaluator recommended full depth for the closeout iteration. We chose: full depth anyway on a broader reading of the structural/cross-cutting trigger — J-06's acceptance needs a real-browser 11-page re-measurement plus a perf-budgets.md update, and this is the session's last failing/partial journey after two prior iterations' documented closure-narrative drift. Reversible: yes
- iter-7 · goal-decomposer — Ambiguity: iter-6's evaluator named re-issuing iter-6's own user-visible-changes.md/ui-surface-map.md to replace retracted framing, but goal mode's artifact model is append-only per iteration. We chose: not to retroactively edit iter-6's artifacts — this iteration's own fresh artifacts describe the current, fixed state, and the stale iter-6 files remain as historical record. Reversible: yes
- iter-7 · goal-evaluator — Ambiguity: J-05's step-4 hang had contested attribution (browser-qa flagged pre-existing /api/backtest MemoryErrors as a possible pre-existing cause), but goal.md's decision tree triggers REGRESSION on any passing→failing move without requiring proven causation. We chose: scored J-05 regressed and returned REGRESSION on the observed move (strong live evidence); did not downgrade to CONTINUE on the contested-attribution argument — a human should adjudicate cause and pick the fix. Reversible: yes
- iter-6 · goal-decomposer — Ambiguity: iter-5's evaluator offered three alternative directions to close J-06's Dashboard browser-latency violation without mandating one. We chose: a frontend-only fetch-scheduling/staggering fix — no new backend endpoint, no TLS/HTTP2 launcher change, no budget loosening — since a coalescing endpoint would create a second serving path and curl's own baseline already sat under the budget. Reversible: yes
- iter-6 · goal-decomposer — Ambiguity: GET /api/data/availability has no committed budget in perf-budgets.md, and goal.md's J-06 step 2 only names the boot and cold /api/data budgets. We chose: committed an explicit ≤1.5s budget for it this iteration rather than leaving it permanently unbudgeted, since it shares J-06's exact Dashboard-class root cause. Reversible: yes
- iter-6 · goal-evaluator — Ambiguity: /evidence's committed budget clause ("warm ≤3s + a bounded one-time cold miss") could be read as satisfied by a ~73s first-view cold miss, or as failing J-06's "loads only what it needs" intent. We chose: scored J-06 partial rather than passing — the two target endpoints are fixed and in budget, but did not let the letter of the cold-miss clause bless a ~73s first view on the session's last Must-have journey. Reversible: yes
- iter-5 · goal-decomposer — Ambiguity: J-06's DoD step 3 requires an audit that no on-load endpoint performs an unbounded scan, but goal.md doesn't say what to do if a genuine violation is found outside the "four offenders" list it already names. We chose: scoped the iteration to include a bounded, minimal fix only if it fits the existing ingest-time-cache convention through an existing computing module/endpoint; a violation needing a new architectural decision stays out of scope. Reversible: yes
- iter-5 · goal-decomposer — Ambiguity: J-06 carries the same [NEW] demo.sh --session-live walkthrough acceptance bullet that iter-4 already deferred for J-05 as a session-closure showcase artifact. We chose: applied the same reading to J-06 for consistency — the walkthrough stays a session-closeout showcase artifact, not part of this iteration's Definition of Done. Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: J-01's deterministic golden-script replay failed step-6 with no LLM-fallback adjudication, and the methodology expects an in-pipeline reconciliation footer that was absent. We chose: scored J-01 passing, adjudicating the miss as a stale proxy (steps 1-5 passed, the run exists in the DB, the display code path is untouched, a healthy 750-row table renders); flagged the golden-script fix as a next-iter blocker. Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: J-04 and J-05 received zero regression-replay coverage this cycle even though the shared function they depend on was modified, with no failing evidence but no fresh passing evidence either. We chose: scored both unknown rather than silently carrying passing forward — honest about the missing this-cycle evidence and flagging them for mandatory re-verification; did not treat the coverage gap as a regression. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-8.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-8-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-8-review.md |
| Browser QA | SKIPPED | reports/phase-goal-ops-hardening-iter-8-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-8-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-8-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-8-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-8-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-8-ui-test-plan.md |
| QA | PASS_WITH_NOTES | reports/qa/goal-ops-hardening-iter-8-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-8-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-ops-hardening-iter-8-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-8/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
