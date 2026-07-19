# Iteration Summary — goal-ops-hardening-iter-0

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-07-19
**Iteration:** 0

## In plain words

**What you can do now:** Just getting started — nothing for users to try yet.

**What changed this time:** Nothing new was built this round — it was a check-up. The team tested five planned improvements (starting up faster and more honestly, loading any amount of historical data without limits, keeping an honest record of data jobs so none look like they silently did nothing, doing the heavy number-crunching ahead of time instead of live, and making pages load faster) against how the app works today, to see exactly what's already there and what still needs to be built. One of them — showing clear messages while the app is starting up or if it crashes — turned out to already work well; the other four still need to be built.

**What's next:** Next, the team will fix how the app loads historical data, so any date range you ask for actually gets pulled in and it clearly explains when a job did no new work.

## Headline

Baseline verify-only pass: all 5 Must-have journeys measured live; 0 pass, 1 partial (J-04).

## Direction

**Signal:** holding
**Why:** This is the ops-hardening session's very first measurement (iteration 0, verify-only, zero code changes) — J-01, J-03, J-05, and J-06 are newly seen as failing and J-04 as partial, with nothing regressed and no anti-goal introduced. There's nothing yet to call improving (no journey has passed) but also nothing stalling: the evaluator identified a clear, tractable next target (the J-01+J-03 data-jobs cluster), so direction is steady heading into iteration 1.

**Trend (last 1 iters):**
- Newly passing this iter: none
- Newly passing in last 1 iters total: none
- Regressions in last 1 iters: none
- Anti-goal violations in last 1 iters: none
- Iters with no journey state change: 0 of last 1

**Latest evaluator reasoning:** Baseline verify-only iteration — no code changed (empty diff), so the browser-QA FAIL for all five journeys is an honest starting-line measurement, not an incident. J-04 scored partial (5/6 sub-steps work live — fast boot 0.909s, phase-aware initializing badge, distinct crash presentation, interrupted-job-after-restart all inherited from mcp-loop iter-28/33; only the persistent logfile + memory-cap enforcement is unbuilt). All other gaps are "surface not yet implemented," buildable offline. Nothing regressed and no anti-goal was introduced, so REGRESSION is off; clear productive next work exists, so STALLED is off; not all passing, so CONTINUE.

## What was done

- Ran a baseline verify-only pass — confirmed zero code, config, or dependency changes (`git diff` under `apps/` and `config.yaml` is empty).
- Completed a code-level (static) review of all five target journeys (J-01, J-03, J-04, J-05, J-06) with file:line evidence, producing preliminary pass/fail hypotheses.
- Exercised all five journeys live against a running backend/frontend (prod-mode scripts) via Chrome MCP, producing screenshots, timings, and DB-state evidence for each.
- Measured backend boot and crash behavior live: first `/api/health` 200 in 0.9-1.3s, a phase-aware "Initializing…" badge, a distinct crash/unavailable state, and correct recovery of a mid-flight job to "interrupted" after restart — all confirmed working.
- Measured a cold `/api/data` request live at ~10s with RSS climbing from 646MB to 1.75GB, confirming the whole-table-prefill signature goal.md names as the target to retire.
- Verified 0 of 5 target journeys pass browser QA cleanly (1 scored partial — J-04, 5 of 6 sub-checks passing live).
- Seeded `journey-history.json` with baseline statuses: J-01 failing, J-03 failing, J-04 partial, J-05 failing, J-06 failing.

## What's left

- Journey J-01 (Backfill honors the requested range and explains zero-work) failing — the cadence gate still blocks explicit backfill requests (`dates_total=0` for the May-2026 range), no exclusion-reason schema exists, and the live job-progress panel resets to the forbidden "no job started" text on reload.
- Journey J-03 (No per-run range cap) failing — `max_range_days: 370` is still enforced in config, validation, and three pinning tests; a 412-day request is rejected outright.
- Journey J-04 (Non-blocking boot with visible status) partial — boot speed, the phase-aware badge, the crash presentation, and interrupted-job recovery already work live; only the persistent logfile and `ulimit`/`MALLOC_ARENA_MAX` memory-cap enforcement remain unbuilt.
- Journey J-05 (Aggregates are precomputed at ingest, never on the fly) failing — no ingest finalize hook refreshes coverage/market-phase/membership caches; a cold `/api/data` still takes ~10s with RSS climbing to 1.75GB.
- Journey J-06 (Pages load only what they need) failing — `/data`, `/evidence`, and `/backtest` measured 5-12x over budget right after a fresh ingest; the two new required budget rows and a code-audit statement are not yet recorded in `reports/perf-budgets.md`.
- Unresolved discrepancy flagged for whoever builds J-04's enforcement: a past `perf-budgets.md` note claims `start-backend.sh` already applies a `ulimit -v` memory cap, but the current script has no such enforcement.

## Next step

Start real feature work with the data-jobs cluster (J-01 + J-03) per goal.md's suggested build order — it unblocks the owner's immediate backfill need. The load-bearing change is J-01's "requested range always wins": `_do_backfill` must stop applying `_cadence_allowed_dates` to explicit backfill requests (the cadence gate is a warm-up-density control only). This single fix is the root cause of both J-01's `dates_total=0` and J-05's un-ingestable single-day date, so it must land before J-05 can be exercised. Pair it with the `data_provider_runs` schema extension (per-date exclusion reasons + the pinned run-summary contract), the zero-work explanatory UI state (visually distinct from success), a job-progress surface that survives reload, and J-03's `max_range_days` removal (config + validation + the four pinning tests). Defer the J-05/J-06 ingest-finalize + lazy-loading cluster and the J-04 logfile/memory-cap layer to subsequent iterations. Recommended depth for iteration 1 is full: it lands the session's first user-visible UI change plus a data-model change, which triggers goal.md's full-depth rule and warrants the audit/ux-regression/closure lanes.

## Assumptions made

- iter-1 · goal-decomposer — Ambiguity: J-03's acceptance says the chunk plan derives from `import_chunking` config values and the UI progress reflects the same plan the engine executes, but `_do_backfill` today has no date-window chunking at all. We chose: read the acceptance literally and scoped J-03 to include adding real date-window chunking to `_do_backfill` (splitting the range into `import_chunking.date_window_days`-sized windows, populating the existing dormant `chunk_index`/`chunk_total` fields), not just the cap removal. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: goal.md establishes "requested range always wins" for explicit backfill requests, but doesn't state whether the cadence bypass should also extend to `rebuild` jobs (which internally widen to the full historical calendar before calling the same `_do_backfill`). We chose: scoped the bypass to explicit `backfill`/`both` requests only; `rebuild` keeps applying the cadence gate unchanged, since no Must-have journey this cycle exercises `rebuild` and the user doesn't supply its date range. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: the iter spec says "surface not yet implemented → FAIL," and browser-QA scored all five journeys FAIL under a strict PASS/FAIL/SKIP contract, yet the journey-history schema also offers a `partial` status; J-04 had 5 of 6 steps reproduce live. We chose: scored J-04 `partial` (not failing) to signal only the logfile/memory-cap layer remains, while keeping J-06 `failing` since its passing pages are pre-existing baseline behavior, not new progress. Reversible: yes
- iter-0 · goal-decomposer — Ambiguity: goal.md's Product Shape prose names only 9 nav sections as "existing nav unchanged," but the actual sidebar has 11 items, including Scanner Runs and Methodology, which aren't mentioned. We chose: treated the actual 11-item sidebar as ground truth for the blueprint's Information Architecture, reading goal.md's 9-item list as "these stay, at minimum" rather than an exact/exclusive list. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-0.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-0-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-0-review.md |
| Browser QA | FAIL | reports/phase-goal-ops-hardening-iter-0-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-0/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
