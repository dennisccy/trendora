# Iteration Summary — goal-ops-hardening-iter-20

**Verdict:** STALLED
**Iteration type:** goal-full
**Date:** 2026-07-24
**Iteration:** 20

## In plain words

**What you can do now:** You can browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. You can back-fill any historical date range with no size cap and get an honest explanation when there's nothing new to do. The status bar always tells the truth about whether the app is starting up, running normally, or has crashed. Heavy calculations are done in advance, not while you wait, and the Backtest page tells you plainly whether the numbers you're seeing are fresh, a labeled "still good" older version, or not ready yet.

**What changed this time:** The one remaining slow spot on the Backtest page is fixed. Previously, the very first time anyone opened an older, never-before-viewed date, the page could hang on a blank skeleton for anywhere from 10 seconds to nearly a minute while it crunched the numbers. Now that first view comes back in a fraction of a second showing an honest "computing this in the background" message, the calculation happens off to the side, and the finished numbers appear on a reload about half a minute later — identical to what the old slow path would have produced. Combined with last round's fix, the Backtest page never does a heavy from-scratch calculation while you wait, on any date.

**What's next:** This is a decision point for the project owner. The remaining work to declare the availability goal fully met isn't something the automation can do by itself — it needs the owner to either (a) authorize a controlled heavy-ingest test run so the operator can measure the last two scenarios (backtest speed *while a data import is running*, and a live crash-and-recover drill), or (b) accept and record a slightly relaxed speed target for the brief window while a background calculation is running. Once the owner picks a direction, the loop resumes.

## Headline

Both Backtest cold-recompute paths are now off the request thread (verified: historical first-view 9.6–54 s → 0.082 s, `ensure_loop_ms` ~54 000 ms → ~3 ms) — but the session halts STALLED because every remaining path to the goal is owner-owned, not agent-tractable.

## Direction

**Signal:** stalling

**Why:** J-06/J-07/J-08 have sat at `partial` for five iterations (16–20), and iter-20 completed the last *agent-tractable* piece of the latency chain — the historical-as-of cold recompute is now dispatched to a single-flight-guarded background thread, so J-08's literal "never a cold recompute on request" is met on both the latest-run (iter-19) and historical (iter-20) paths. No journey crossed to passing because the decisive remaining blocker for each target is now human-owned: J-08's ≤1.5 s budget under its own concurrent-ingest scenario (TC-13) and J-04's disruptive replay (TC-14) both need a real backfill the AG-10 safety classifier blocks, and J-07's only residual (transient in-process contention during the ~30 s background compute) has no spec-permitted agent fix. Unlike iter-19 (agent-tractable → CONTINUE), the next step is genuinely the owner's — the same class as iter-15's STALLED, but with a far smaller residual.

**Trend (last 5 iters):** iter-16 partial → iter-17 partial → iter-18 partial (diagnosis) → iter-19 partial (primary fix, 63× collapse) → iter-20 partial (historical fix) — no newly-passing, no regressions, agent-tractable latency work now exhausted.

**Latest evaluator reasoning:** The historical `/backtest` cold-recompute is genuinely off the request thread (`ensure_loop_ms` 9288–54281 ms → ~1.67–3.34 ms, first-response 0.082 s; screenshots confirm honest interim states, never a frozen skeleton; AG-5 preserved in the older-complete fallback). But no journey crossed to passing, and every remaining unblock path is human-owned (decision-tree C.2): J-08's ingest-overlay budget (TC-13) is AG-10-gated, J-07's health-latency breach is transient in-process contention whose only in-scope fix is an owner budget decision plus owner-gated TC-14, and J-06 shares that budget decision. Did not launder the transient budget breach green; did not pick STALLED to escalate — there is genuinely no agent step to a pass.

## What was done

- Moved the historical-as-of forward-aggregate compute OFF the `/backtest` request thread into a single-flight-guarded background daemon dispatch (`ensure_historical_forward_aggregates_dispatched`, keyed on `(asof_key, dataset_version)`); the request now returns the already-stored evidence immediately with an honest `refreshing`/`not_yet_computed` state and never a cold synchronous recompute. `compute_forward_aggregates` / `resolved_forward_aggregate_evidence` / `forward_aggregates_ingest_cached` untouched (110 insertions / 0 deletions).
- Frontend: `RefreshingEvidenceBanner` and the `not_yet_computed` `EmptyState` copy now branch on `is_latest` so a historical first-view truthfully states the compute was started by viewing the page.
- Updated the three tests that encoded the old synchronous behavior + added two concurrency tests (dispatch-exactly-once under 5-way concurrency; owner-failure recovery). 91 scoped tests pass.
- Operator live re-measurement (perf-budgets.md "Iteration 20"): cold historical first view 9.6–54 s → 0.082 s, `ensure_loop_ms` ~2–3 ms, background compute completes ~30 s later → `ready` byte-identical, `/api/health` 200/ready throughout (16/16).
- All 7 gates PASS: review PASS_WITH_NOTES, QA PASS (91 tests + browser), browser-QA PASS (11/12 live, Chrome MCP worked), ux-regression PASS, audit PASS_WITH_GAPS, closure CLOSURE-PASS, coherence COHERENCE-PASS.

## What's left

- **Owner-gated (the decisive blockers):** TC-13 — prove the ≤1.5 s `/backtest` budget under a *concurrent ingest overlay* (the original 11/68 @ 12.655 s condition); TC-14 — a fresh *disruptive* J-04 kill/restart checkpoint-survival replay (owed since iter-15). Both need a real backfill the AG-10 safety classifier blocks — they require the owner to authorize the ingest trigger.
- **Owner budget decision:** during the ~30 s background compute, concurrent requests transiently reach 3.0–6.3 s and `/api/health` ~1.6 s (in-process GIL contention; service never wedges). The only in-scope fixes (off-process worker / precompute-all-historical-dates) were spec-rejected as unbounded ingest cost, so closing this needs either an accepted budget amendment or an owner decision to fund a bigger change.
- **Agent-tractable but out-of-scope / diminishing-returns:** a cold historical view of a *fully-elapsed* date still totals ~1.3–1.9 s from pre-existing `scorecard_ms` + `resolved_run_ms` (a separate subsystem, not iter-20's dispatch). Minor cleanup: auditor B3 (exotic guard-strand on `thread.start()` failure, self-healing on next version bump); dead import at `mcp/tools.py:38`.

## Next step

Owner picks a direction, then `./scripts/automation/run-goal.sh --session-id ops-hardening --resume` (at full depth). The owner's menu: (a) authorize the AG-10-gated ingest trigger so the operator can run TC-13 + TC-14 under the host-guard ritual; or (b) accept-and-log a budget amendment (goal.md / perf-budgets.md) for the bounded transient-contention window. Either unblocks the path to GOAL_ACHIEVED.

## Assumptions made

- J-08's "never a cold recompute on request" was scoped by the iter-16 decomposer (human-un-vetoed) to `is_latest == true`; iter-19+20 nonetheless removed the request-path recompute on *both* paths, so the literal clause now holds broadly. The transient budget breach during a background compute was recorded honestly rather than laundered into a pass (assumptions.md, iter-20 entry).

## Quick verify

1. Open `/backtest`, pick a never-viewed historical date via the as-of calendar → page responds in well under a second with an honest "computing in the background" affordance (not a blank multi-second hang).
2. Reload the same date ~30 s later → real ready evidence renders.
3. The latest (default) `/backtest` view is unchanged and fast.
4. `reports/perf-budgets.md` "Iteration 20" — the operator's live before/after numbers.

## Artifacts

| Artifact | Verdict / content |
|---|---|
| `runs/goal-session-ops-hardening/iter-20/eval.md` | STALLED |
| `reports/reviews/goal-ops-hardening-iter-20-review.md` | PASS_WITH_NOTES |
| `reports/qa/goal-ops-hardening-iter-20-qa.md` | PASS (91 tests) |
| `reports/phase-goal-ops-hardening-iter-20-ui-test-results.md` (+ `.llm.md`) | Browser QA PASS (11/12 live) |
| `reports/phase-goal-ops-hardening-iter-20-ux-regression.md` | UX-REGRESSION-PASS |
| `docs/handoffs/goal-ops-hardening-iter-20-audit.md` | PASS_WITH_GAPS |
| `reports/phase-goal-ops-hardening-iter-20-closure-verdict.md` | CLOSURE-PASS |
| `runs/goal-session-ops-hardening/iter-20/coherence.md` | COHERENCE-PASS |
| `reports/perf-budgets.md` (§ Iteration 20) | live before/after latency measurement |
| `docs/handoffs/goal-ops-hardening-iter-20-dev.md` + `-frontend.md` | dev + frontend handoffs |
