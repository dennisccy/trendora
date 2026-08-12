# Iteration Summary — goal-ops-hardening-iter-71

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-08-12
**Iteration:** 71

## In plain words

**What you can do now:** Request a backfill for any date range and get an honest explanation when there's nothing new to fetch (even for ranges over a year, with no hidden limit). See an honest "Ready" status while the app starts up. Browse stock rankings, sectors, themes, backtests, and research pages, each loading only what it needs. View backtest results instantly, served from storage rather than recalculated live. See a live progress indicator when the app is crunching numbers in the background.

**What changed this time:** Behind-the-scenes work — nothing new to click this round. The app's own status-check system (behind the "Ready" badge) was hardened so it can never quietly keep serving a frozen "everything's fine" answer if its background updater ever stalls. The team also re-tested all eight promises against the live app for the first time in two rounds, and that check caught a real problem: during a 20-minute data job, the status check briefly stopped answering altogether, including one unbroken two-and-a-half-minute silence.

**What's next:** Next we'll re-run that outage check the proper way, using the app's real production startup scripts, fix the shortage of database connections that caused it, and ask you to decide whether the two-second health-check promise should still apply during long background jobs.

## Headline

Readiness/preflight cache gains a monotonic staleness bound with synchronous fallback

## Direction

**Signal:** improving
**Why:** Six of eight journeys — J-01 "Backfill honors the requested range and explains zero-work", J-03 "No per-run range cap", J-04 "Non-blocking boot with visible status", J-06 "Pages load only what they need", J-08 "Backtest evidence serves from storage only", and J-09 "The backend discloses its own background-compute activity" — moved from untested/partial to passing this iteration, the first real re-verification since iter-69. J-07 "Heavy aggregates never take the service down" moved from partial to failing on measured evidence (a 165-second health-check outage during a real ingest job), and J-05 dropped to partial because it shares that same failed step. No regression fired and no critical anti-goal violation was found; the evaluator escalated (not regressed) to pull in the audit and ux-regression lanes for the outage's root cause next round.

**Trend (last 2 iters):**
- Newly passing this iter: J-01, J-03, J-04, J-06, J-08, J-09
- Newly passing in last 2 iters total: J-01, J-03, J-04, J-06, J-08, J-09 (iter-70 produced zero journey evidence — its QA backend died mid-round)
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: none critical (iter-70: 0 critical, several minor; iter-71: 0 critical, 8 new minor findings a-h)
- Iters with no journey state change: 1 of last 2 (iter-70)

**Latest evaluator reasoning:** "All eight journeys were checked against a live app again, after the previous round checked nothing. Seven of them work: the backfill jobs, the long-range request, the page loads, the stored backtest evidence and the new 'background compute running' disclosure all showed real, correct numbers that I re-checked in the database myself. One journey failed badly. While a real 20-minute data job ran, the app stopped answering its health check 58 times out of 900, including one unbroken stretch of 165 seconds with no answer at all, and it returned one server error to the `/data` page."

## What was done

- Product changes: apps/backend/app/engine/readiness.py, apps/backend/app/api/health.py, apps/backend/app/config.py, config.yaml, apps/backend/tests/test_readiness.py, apps/backend/tests/test_health.py, apps/backend/tests/test_data_manager.py
- Stamped every readiness/preflight cache tick with a monotonic `computed_at` timestamp and added a synchronous-fallback path once an entry ages past `readiness.max_stale_intervals × refresh_interval_seconds` (default 1.5s) — a wedged/dead background tick can no longer serve arbitrarily-stale data.
- Added `stale_for_s: float>=0` to `GET /api/health`'s response body — a backend-only diagnostic field this round, not yet rendered in the UI.
- Fixed `health.py:174` to explicitly assign `cached = None` in the preflight-fallback branch, closing iter-70's reviewer/audit MINOR.
- Added an integration test proving a real ingest finalize-hook state flip is served by `GET /api/health` within one refresh tick (composed TC-4, closes audit T1).
- Re-verified all 8 target journeys against a confirmed-live backend for the first time since iter-69, clearing `pending_infra` on every one.
- Verified 6 target journeys pass browser QA (J-01, J-03, J-04, J-06, J-08, J-09); found J-07 failing on a measured 165-second health-check outage during a real heavy ingest job, and J-05 dropped to partial because it shares that same failed step.

## What's left

- Journey J-07 (Heavy aggregates never take the service down) failing — 58 of 900 health-check polls got no answer at all during a real 20-minute ingest job, including one 165-second unbroken outage, caused by database connection-pool exhaustion (`QueuePool` limit reached) while running on the development launcher.
- Journey J-05 (Aggregates are precomputed at ingest, never on the fly) partial — its own "stays responsive throughout" step failed on the same outage that failed J-07, even though its ingest/backfill correctness steps passed cleanly.
- This round's outage was measured on the development launcher (`scripts/dev.sh`), which omits production's concurrent-request limit; the measurement must be repeated on the production launcher (`scripts/start-backend.sh`) before the outage's true size is confirmed.
- The J-07 health-poll drill still started polling ~2m46s after the ingest job began, not the required 2 seconds before it — the opening window remains unmeasured for a second round running.
- The database connection pool (30 total) is undersized relative to the production concurrency limit (64) — needs a dedicated health-check connection, a no-DB fast path, or a larger pool.
- This iteration's own staleness-bound fix has no post-lock recheck in `_tick_and_cache`, so queued requests during a stale window each pay a full synchronous compute — a plausible contributor to the outage that needs ruling in or out.
- `scripts/dev.sh` still lacks production's server guards (`--limit-concurrency`, `--timeout-keep-alive`, `--timeout-graceful-shutdown`) and a persistent logfile.
- Owner decisions still outstanding: the 2-second health-check ceiling policy (23 rounds asked), permission to fix the `browser-qa-phase.sh` ordering bug, whether to bound concurrent heavy computations (card B-1107), and a cost-budget sanction (11 consecutive over-budget rounds).

## Next step

Run the next round at full depth: repeat the health-poll measurement on the production launcher (`scripts/start-backend.sh` / `scripts/start-frontend.sh`, never `dev.sh`) with the poller armed before the job starts; fix the database connection-pool exhaustion behind the outage (a dedicated health-check connection, a no-DB fast path, or a larger pool); rule this round's own staleness-bound change in or out as a contributing cause (add a post-lock recheck, or serve the aged value with its staleness disclosed); and bring `scripts/dev.sh` up to production's server guards. Also ask the owner to finally answer the 2-second health-check ceiling question and the B-1107 concurrency-bounding question so this last journey can be closed or re-scoped.

## Assumptions made

- iter-71 · goal-evaluator — Ambiguity: J-05 step 4 ("stays responsive throughout") is textually the same assertion the browser-QA lane scored only against J-07, not J-05. We chose: score it against both journeys — J-05 drops to partial (steps 1-2 passed, step 4 failed) while J-07 goes failing. Reversible: yes.
- iter-71 · goal-evaluator — Ambiguity: J-07's drill ran on the development launcher (`scripts/dev.sh`), which omits the production concurrency guard the observed failure (database pool exhaustion) is documented to prevent; nothing states whether a severe failure under non-conforming launch conditions should score `failing` or `partial` pending a conforming re-measurement. We chose: `failing`, naming the launcher confound first in every summary and making a production-launcher re-measurement item (1) of the next round. Reversible: yes.
- iter-71 · goal-decomposer — Ambiguity: iter-70's next-step order for the readiness-cache staleness bound didn't name a field, threshold multiplier, or whether to surface it in the UI. We chose: field `stale_for_s: float>=0`, a new `readiness.max_stale_intervals` config knob (default 3), and NOT rendering it in the UI this round (would be the cycle's first user-visible change, requiring full depth). Reversible: yes.
- iter-70 · goal-evaluator — Ambiguity: no `browser-infra.json` token was written for this round's mid-round backend death (a service death, not a browser-classified infra reason), so it's unclear whether the pending-infra carve-out (`partial` + `pending_infra`) or the plain "no evidence → `unknown`" fallback applies. We chose: apply the pending-infra carve-out to all 8 journeys anyway, since the engine schedules the verify-only make-up ride from the `pending_infra` flag itself. Reversible: yes.
- iter-70 · goal-decomposer — Ambiguity: iter-69's recommendation to serve readiness/preflight "from a stored/bounded value" didn't name a mechanism (persisted DB table vs. in-process cache). We chose: an in-process, bounded-interval background-refresh cache inside `app.engine.readiness`, mirroring the existing warmup daemon-thread pattern, leaving the DB-reachability reads on the request path unchanged. Reversible: yes.
- iter-69 · goal-evaluator — Ambiguity: whether a 5-second client-side timeout with no answer (while the server itself logged only 200s) counts as J-07 step 2's "no frozen or unresponsive window" failure. We chose: keep J-07 at `partial`, recording the deterioration explicitly rather than flipping the status. Reversible: yes.
- iter-69 · goal-evaluator — Ambiguity: whether the Do-not-redo ban on bounding `factor_lab_all_warm`/`coverage_membership_timeline_refresh`, written as conditional on the sub-timing naming components, should be treated as released now that this round's sub-timing did name them. We chose: declare it released and rewrite the bullet, without making it the recommended target. Reversible: yes.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-71.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-71-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-71-review.md |
| Browser QA | FAIL | reports/phase-goal-ops-hardening-iter-71-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-ops-hardening/iter-71/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
