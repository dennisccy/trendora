# Iteration Summary — goal-ops-hardening-iter-9

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-22
**Iteration:** 9

## In plain words

**What you can do now:** Browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any historical date range with no size cap and get an honest explanation when there's nothing new to add, and can trust that even the heaviest back-to-back data updates won't slow down or crash the app. The status badge tells the truth during startup, a data update, or a crash.

**What changed this time:** The fix for last week's "back-to-back big update freezes the app" scare is now proven, not just built: the team ran the actual worst-case scenario — a full data rebuild immediately followed by another big update, in one process, on the real machine — and it held up cleanly for 18 minutes with room to spare. The app's startup scripts also now automatically apply the machine's safety limits every time, whichever of the two ways someone starts it. Along the way, testing caught and fixed a real bug: a data job interrupted by a crash used to forget all its progress and show "nothing happened" even after processing hundreds of days — it now remembers correctly, though one more click-through check is needed to fully confirm it.

**What's next:** One more click-through check to confirm an interrupted data job now shows its true progress, then a refresh of a stale test report — the last steps before this operations chapter can close.

## Headline

Both launch scripts now actually apply the machine's declared safety limits.

## Direction

**Signal:** improving
**Why:** J-05 (the session's regression target since iter-7) is recovered and proven, for the first time, by a real 18-minute heavy-ingest run under the launcher's own safety caps; J-01 and J-03 also moved from unknown to passing, closing iter-8's evidence gap. J-04 improved to partial (5 of 6 steps pass; its interrupted-job defect was fixed this iteration but still needs one browser re-check). A carried-forward critical anti-goal item (a distinct on-load memory-exhaustion path) remains open and blocks GOAL_ACHIEVED, but it was neither introduced nor worsened this iteration.

**Trend (last 5 iters):**
- Newly passing this iter: J-01, J-03, J-05
- Newly passing in last 5 iters total: J-04 (iter-6), J-05 (iter-6, then regressed iter-7, passing again iter-9), J-01 (iter-9), J-03 (iter-9)
- Regressions in last 5 iters: J-05 (iter-7)
- Anti-goal violations in last 5 iters: 3 (iter-7 AG-8 critical — resolved iter-9; iter-8 AG-10 minor — resolved iter-9; iter-9 AG-8 critical distinct dimension — unresolved, carried forward)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** J-05 — the session's regressed target since iter-7 — is genuinely recovered and, for the first time, proven by a qualified lane: all four acceptance steps carry live browser evidence and step 4 was closed by the 18-minute operator-authorized heavy-ingest run whose raw CSVs the evaluator re-derived independently (439/439 `GET /api/health` polls HTTP 200, peak VmPeak 4,738,948 KB vs the 6,291,456 KB cap). J-01 and J-03 move out of `unknown` on live LLM re-verification, and the AG-10 launcher gap is closed and live-verified on `/proc`. But J-04 does NOT pass: its step 6 failed in a real browser (an interrupted job persisted "0 snapshots · 0 trading days"), the product defect was fixed intra-iteration (F1 `_checkpoint_run_record`) and confirmed post-fix at the API level by the operator — but no browser lane re-drove `/data` after the fix, so J-04 is scored `partial`, not `passing`.

## What was done

- Both launch scripts (`scripts/start-backend.sh` and `scripts/dev.sh`'s backend subshell) now apply `host-guard.env`'s CPU-affinity mask and BLAS/OMP/numexpr thread caps, additive to the pre-existing memory-ceiling enforcement.
- Tightened the heavy back-to-back ingest safety-net test to reject a "partial" outcome and require full aggregate-refresh bookkeeping for both jobs.
- Added automated checks proving the safety caps apply correctly, and stay a no-op when the safety-limits file is absent or disabled.
- Fixed a newly-discovered defect (F1): an interrupted data job now checkpoints and keeps its last real progress instead of always showing zero.
- Memoized a repeated low-level system lookup used during memory cleanup so it resolves once per server run instead of on every call.
- Ran the previously-deferred live heavy-ingest measurement (18 minutes, full rebuild immediately followed by a second heavy backfill in one process): both jobs reached `ok`, peak memory stayed 24.7% under the cap, 439/439 health polls returned 200, no host reset.
- Verified 17 of 19 browser-qa rows pass (2 FAIL: an interrupted-job progress display pre-dating this fix, and the required-still-passing J-04 step 6 it drives); J-05, J-01, and J-03 moved to `passing`, J-04 moved to `partial`.

## What's left

- J-04 ("Non-blocking boot with visible status") is scored `partial` — steps 1-5 pass; step 6's defect was fixed intra-iteration but needs one browser-lane kill/restart re-verification before it can be scored passing.
- Closure gate is FAILING: `reports/phase-goal-ops-hardening-iter-9-regression-replay-results.md` still records J-04 failing at step 6, despite credible operator-level post-fix evidence — needs updating once the browser re-run lands.
- The QA report (`reports/qa/goal-ops-hardening-iter-9-qa.md`) is stale — generated before the browser-qa lane and the heavy-ingest run completed, and still concludes "PASS ... ready to move forward"; needs regeneration or a dated addendum before the closure gate can re-run.
- J-06 ("Pages load only what they need") stays `partial`, carried forward and not re-tested this iteration; a distinct, unresolved critical anti-goal item (an on-load memory-exhaustion path) hard-blocks GOAL_ACHIEVED and awaits an owner decision.
- The `demo.sh ops-hardening --session-live` walkthroughs for J-05 and J-06 are still not produced — need an explicit human deferral or new scope before any GOAL_ACHIEVED gate.
- Non-blocking carry-forwards: no `command -v taskset` guard in the launch scripts; the shared merge-script drops bolded **FAIL** cells (under-reporting browser-qa results, flagged for the framework maintainer); a pre-existing unrelated test failure (`test_create_all_produces_expected_tables`) since iteration 2.
- Owner decision needed: whether to extend the session's iteration budget — `session.json max_iterations: 9` was this iteration, and the session is not yet GOAL_ACHIEVED.

## Next step

Full depth, verification-and-currency only, no new features. Priority order: (1) close J-04 step 6 with one browser-lane kill/restart cycle against the current fixed tree, reading the rendered Run History / Job progress panel, then supersede the auditor addendum in the regression-replay-results artifact — the single item standing between the session and all-five-passing; (2) emit an explicit `UT-J-05` verdict row so J-05's pass stops needing manual citation assembly; (3) regenerate or date-addendum the stale QA report, then re-run the closure gate; (4) owner decisions only, not to be invented by an agent: the deferred on-load `/api/backtest` memory-exhaustion path (J-06/AG-8), the unproduced J-05/J-06 `demo.sh --session-live` walkthroughs, whether to flip `HOST_GUARD_REQUIRE_MARKERS` to 1, and an iteration-budget extension since `session.json`'s `max_iterations: 9` was reached this iteration; (5) framework maintainer item (still unfixed): the merge script that drops bolded **FAIL** cells, and the `Frontend Present: no` browser-qa-skip misrouting.

## Assumptions made

- iter-9 · goal-evaluator — Ambiguity: no artifact anywhere emits a `UT-J-05` verdict row, yet J-05 is the iteration's target journey and its evidence is scattered across several other rows. We chose: treated the per-step citation trace as satisfying the evidence bar rather than scoring J-05 `unknown` on a missing summary row, personally re-walking the mapping against the journey's four steps and opening each cited row. Reversible: yes
- iter-9 · goal-evaluator — Ambiguity: a deferred on-load memory-exhaustion path is a recorded critical anti-goal dimension, and the decision tree read literally would re-halt on a finding already human-acknowledged. We chose: recorded it fail-closed as a distinct critical, unresolved entry (hard-blocking GOAL_ACHIEVED) while not firing the regression branch, since it was neither introduced nor worsened this iteration; separately marked the original iter-7 finding resolved, refuted by this iteration's qualified evidence. Reversible: yes
- iter-9 · goal-evaluator — Ambiguity: J-04's step-6 evidence is split across two builds — failed pre-fix in the browser, fixed intra-iteration, and only confirmed post-fix at the operator/API level, with no journey status matching this exact situation. We chose: scored J-04 `partial` — steps 1-5 verified, step 6's defect fixed and credibly evidenced but not re-verified in a browser; rejected `failing`, `passing`, and `unknown` as each misrepresenting the current tree. Reversible: yes
- iter-9 · goal-decomposer — Ambiguity: a prior recommendation was to fix the shared framework harness's browser-qa skip bug, but that defect lives outside this project's product scope. We chose: did not touch the framework; instead set this iteration's own spec to the honest `Frontend Present: yes` value, routing around the bug without patching shared automation, and flagged it for the framework maintainer. Reversible: yes
- iter-8 · goal-evaluator — Ambiguity: an unmet MUST-apply clause on a critical anti-goal, with no guidance on whether it carries the same severity as the regression trigger it names. We chose: recorded it minor rather than critical — nothing was stripped or weakened, and the goal's own notes treat closing the gap as scheduled next-iteration work; flagged as not fully certain of this severity call. Reversible: yes
- iter-8 · goal-evaluator — Ambiguity: a journey still carried a `regressed` status from the prior iteration's human-acknowledged halt, creating tension with a rule that any `regressed` status forces a regression verdict. We chose: treated the operative decision-tree rule (fires only when a journey moves passing→failing) as controlling and returned CONTINUE, since no journey moved passing→failing this iteration and every unblock path was agent-owned. Reversible: yes
- iter-7 · goal-evaluator — Ambiguity: a journey's failure was hit by a multi-minute hang, but the deep cause was contested as possibly pre-existing rather than newly introduced by this iteration's diff. We chose: scored the journey `regressed` and returned REGRESSION on the observed passing→failing move regardless of proximate cause, recording the anti-goal violation fail-closed with the attribution caveat stated explicitly. Reversible: yes
- iter-7 · goal-decomposer — Ambiguity: a prior recommendation named re-issuing a past iteration's own artifacts to replace a retracted framing, but the artifact model is append-only per iteration. We chose: did not retroactively edit the prior iteration's artifacts; instead this iteration's own fix removes the underlying issue the retracted framing was about, and this iteration's fresh artifacts describe the current state on their own terms. Reversible: yes
- iter-6 · goal-decomposer — Ambiguity: a sibling endpoint had no committed performance budget, and the spec only named two other endpoints as required additions. We chose: to commit an explicit budget for it this iteration rather than leave it permanently unbudgeted, since it shares the same root cause and a prior evaluator recommended folding it in. Reversible: yes
- iter-6 · goal-evaluator — Ambiguity: a journey's acceptance named a committed budget with a cold-miss clause that could be read as either satisfied or not satisfying the journey's real intent, given a very slow first view on the live dev DB. We chose: scored the journey `partial` rather than `passing` — the target endpoints are genuinely fixed, but did not let the letter of the cold-miss clause bless a very slow first view; a human reading the clause as fully dispositive may override to `passing`. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-9-what-to-click.md`:

1. Open `http://localhost:3255/data` in your browser
2. In the "Start a fetch / backfill job" panel, type `2026-05-15` into both the "Start date" and "End date" fields, leave "Job kind" set to "Backfill snapshots", then click the "Start" button
3. Wait for the job to finish (watch the "Job progress" panel — do not refresh the page)
4. Navigate to `http://localhost:3255/scanner-runs`
5. Click the `May 15, 2026` date link in that row

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-9.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-9-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-9-review.md |
| Browser QA | FAIL | reports/phase-goal-ops-hardening-iter-9-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-9-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-9-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-9-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-9-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-9-ui-test-plan.md |
| UX regression | UX-REGRESSION-WARN | reports/phase-goal-ops-hardening-iter-9-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-9-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-9-audit.md |
| Closure | FAIL | reports/phase-goal-ops-hardening-iter-9-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-9/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
