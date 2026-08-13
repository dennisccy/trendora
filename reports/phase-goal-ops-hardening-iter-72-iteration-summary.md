# Iteration Summary — goal-ops-hardening-iter-72

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-12
**Iteration:** 72

## In plain words

**What you can do now:** Fill in historical data for any date range you choose, with a clear explanation when there's nothing new to fetch. Backfill spans longer than a year in one go, with no hidden limit. See an honest status message while the app is starting up. Get freshly calculated numbers right after a data import rather than waiting for them to compute on the fly. Browse every page of the site quickly. View backtest results instantly, pulled from storage. See when the app is crunching numbers in the background.

**What changed this time:** Nothing new appeared on screen this round — the work was entirely behind the scenes. It fixed why the app's health check could go silent for minutes during heavy background jobs: the pool of spare database connections was too small for the traffic the app allows, and the status-check logic could get stuck waiting on a slow recheck. Both are fixed now, and the developer's everyday startup script was also brought up to match the safer production startup settings.

**What's next:** Next we'll measure how much memory the app now needs when it's using all of its newly-expanded pool of database connections during a heavy job, and tighten it if the margin is thin — that's the one check left before "the app never goes down under heavy load" can be marked fully working.

## Headline

Database connection pool resized to match what the server actually admits

## Direction

**Signal:** improving
**Why:** J-05 ("Aggregates are precomputed at ingest") returned to fully `passing` after the exact health-check outage from iter-71 was fixed and re-verified — every one of 1,315 polls answered during the same heavy-job scenario that previously went silent for 165 seconds. J-07 ("Heavy aggregates never take the service down") improved `failing` → `partial`: the availability fix holds, but the evaluator withheld a full pass because the round also doubled the database connection pool without measuring the resulting memory margin. No journey regressed, and the anti-goal ledger holds at 0 unresolved critical entries (245 total, 123 unresolved, all minor).

**Trend (last 2 iters):**
- Newly passing this iter: J-05
- Newly passing in last 2 iters total: J-01, J-03, J-04, J-06, J-08, J-09, J-05 (7 of 8 — all but J-07)
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: iter-71 opened 4 minor entries (a-d, all closed this round with verified evidence); iter-72 closed those 4 and opened 7 new minor entries (a-g); 0 critical in either iter
- Iters with no journey state change: 0 of last 2

**Latest evaluator reasoning:** "The app stayed up. Last round, while a long data job ran, 58 of 900 health checks got no answer at all, including one silent stretch of 165 seconds. This round the same kind of job ran on the correct launcher and all 1,315 health checks were answered, none took longer than 1.7 seconds, and not a single second went unanswered — including the whole ten-minute stage that caused every problem before. J-05 'Aggregates are precomputed at ingest' is back to passing, and J-07 'Heavy aggregates never take the service down' is much better but not fully checked: this round also made the app allowed to hold more than twice as many database connections at once, and nobody measured what that does to memory."

## What was done

- Product changes: config.yaml, apps/backend/app/config.py, apps/backend/app/engine/readiness.py, apps/backend/app/api/health.py, apps/backend/app/api/data.py, apps/backend/app/engine/data_manager.py, scripts/dev.sh
- Resized the database connection pool (30 → 68 combined connections) to cover the server's admitted concurrency, and added a boot-time check that refuses to start if that arithmetic mismatch ever recurs.
- Changed the health/readiness check so it never blocks on a slow recompute under load — it now always answers instantly with its last-known value plus an honest staleness figure, and added a post-lock recheck so queued callers reuse a freshly-published entry instead of recomputing redundantly.
- Brought the everyday `scripts/dev.sh` developer launcher up to parity with the production launcher (connection-limit/timeout flags, persistent log file), leaving the frontend subshell untouched.
- Re-measured the exact failure scenario from last round on the correct production launcher: 1,315 (browser lane) and 1,598 (dev lane) health polls, zero non-answers, zero non-200 responses — a full reversal of last round's 165-second outage.
- Added a test-only fault-injection hook on `GET /api/data` so the frontend's existing honest-fallback message can be evidenced (screenshot not yet captured — see What's left).
- Verified target journeys via browser QA: J-05 returns to `passing`; J-07 passes the browser-QA drill itself but the evaluator held it at `partial` pending a memory-margin measurement under the new pool size.

## What's left

- Journey J-07 ("Heavy aggregates never take the service down") is `partial` — peak memory under the new 68-connection pool (each allowed a 256 MB private cache) hasn't been measured against the 8 GB cap; this is the next round's first job.
- The readiness cache now serves stale data indefinitely with no on-screen disclosure — if the background refresh thread ever died, the "Ready" badge would freeze silently. The computed staleness age exists in the API but isn't shown on any page yet; rendering it needs a dedicated full-depth round since it would be this cycle's first user-visible UI change.
- The automated regression-replay baseline is unreliable: 6 of 8 deterministic replays failed this round and the recorded explanation (contention with this round's own drill) was wrong — the audit traced it to a broken test frontend instead. Needs repair on a quiet host.
- TC-10's evidence — a screenshot of `/data`'s honest fallback message under a forced API failure — was recorded as done but was never actually captured.
- A new failure mode was found (not fixed): under traffic well beyond this round's test scenario, the server's own concurrency limiter can get stuck rejecting requests, including health checks, for as long as the heavy job holds the CPU.
- J-06's page-load timing measurement (owed for a third round now) is still outstanding — this was a backend-only round with no frontend work.
- Owner decisions still pending: the 2-second health-check policy (asked 24 rounds running), whether to bound how many heavy background jobs may run at once (card B-1107), permission to fix a known ordering bug in the browser-QA automation script, and a cost-overrun sanction (this was the 12th consecutive over-budget round).
- The Regime Lab page redesign (iter-33/g) was deferred for a 39th round; roughly 40 other older carried items remain untouched.

## Next step

Run the next round at lean depth. First, measure how much memory the app can now use under the resized 68-connection database pool during a heavy job, record the margin against the 8 GB memory cap in `reports/perf-budgets.md`, and lower the per-connection cache size or the pool size if the margin is thin — this is the one thing standing between J-07 and a full pass, and the memory ceiling is a real hardware constraint on this machine, not a soft budget. Right after that, render the health check's staleness age on the badge/preflight banner as its own full-depth round (a user-visible UI change, since a frozen background refresh would otherwise go undisclosed). Then restore a trustworthy automated regression-replay baseline before working through the smaller carried items.

## Assumptions made

- iter-72 · goal-evaluator — Ambiguity: J-07's memory-margin step (VmPeak vs. `memory_cap_mb`) had been carried on evidence durability for two prior rounds since the warm-path code was unchanged, but this round changed a direct input to that assertion (the DB pool size, 30→68) without a new memory measurement — unclear whether the carry still applies when only a config input changes, not the code. We chose: the carry breaks; J-07 scored `partial` (not `passing`) with the unmeasured memory question named first, since the pool sizing directly affects peak memory and the drill never exercised more than a handful of connections. Reversible: yes — a clean measurement next round returns J-07 to `passing`; a thin one drives a config adjustment.
- iter-72 · goal-decomposer — Ambiguity: iter-71's next-step order left open whether the readiness-cache staleness fix should be an instrumented A/B (recheck-after-lock vs. serve-stale) resolved empirically across two rounds, or decided outright. We chose: ship serve-the-aged-value-with-disclosed-age as the definitive fix now, add the post-lock recheck as complementary hardening, and bundle the pool-sizing fix in the same iteration rather than isolating causation. Reversible: yes — a later iteration can add a watchdog/restart mechanism without touching the producer/endpoint identity.
- iter-71 · goal-evaluator (2 of 2) — Ambiguity: J-05's step 4 is textually the same health-responsiveness assertion as J-07's step 2, and the browser-QA lane scored J-05 PASS while attributing the failure entirely to J-07; unclear whether a shared acceptance step may be scored against only one journey. We chose: score it against both — J-05 dropped to `partial` (steps 1-2 verified, step 4 failed, step 3 carried) while J-07 went `failing`. Reversible: yes — a passing re-measurement (which happened this round) returns J-05 to `passing` with no other step needing rework.
- iter-71 · goal-evaluator (1 of 2) — Ambiguity: the drill that found the outage ran on `scripts/dev.sh`, which omits the production concurrency guard; nothing states whether a severe failure measured on a non-conforming launcher scores the journey `failing` or stays `partial` pending a conforming re-measurement. We chose: `failing`, with the launcher confound named first throughout, because the outage and the real 500 are the journey's own named failure modes regardless of launcher. Reversible: yes — the prod-launcher re-measurement (delivered this round) either reproduces or clears the outage.
- iter-71 · goal-decomposer — Ambiguity: iter-70's next-step order to add a staleness bound to the readiness cache didn't name the field, the multiplier, or whether the value should be shown in the UI. We chose: field name `stale_for_s`, a new `max_stale_intervals` config knob (default 3), and NOT rendering it in the UI that round (backend/diagnostic-only), since that would have been the cycle's first user-visible UI change under a lean-depth iteration. Reversible: yes — a later iteration can surface `stale_for_s` on the badge/banner at full depth without touching the producer/endpoint.
- iter-70 · goal-evaluator — Ambiguity: the pending-infra carve-out (score `partial` + `pending_infra`) is keyed to a browser-infra token that wasn't written this round because the failure was a backend service death, not a browser-infra classifier match — the literal fallback rule and the carve-out point at two different statuses for the same eight journeys. We chose: apply the carve-out anyway — all eight journeys scored `partial` with `pending_infra: true`, since the failure class is identical in every way that matters and the engine's make-up-ride scheduling reads the flag, not the token. Reversible: yes — a later evaluator can re-score any journey the moment a fresh frame lands.
- iter-70 · goal-decomposer — Ambiguity: iter-69's next-step order to serve readiness/preflight from a "stored/bounded value" didn't name a mechanism (a persisted DB row vs. an in-process background-refresh cache), nor whether other reads in the same handler should move off the request path too. We chose: an in-process, bounded-interval background-refresh cache inside `app.engine.readiness`, reusing the existing `app.engine.warmup` daemon-thread idiom, leaving the other reads on the request path unchanged. Reversible: yes — a later iteration can tighten the refresh cadence or promote the cache to a persisted table without changing the producer/endpoint again.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-72.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-72-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-72-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-72-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-72-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-72-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-72-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-72-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-72-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-ops-hardening-iter-72-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-72-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-72-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-72-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-72/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
