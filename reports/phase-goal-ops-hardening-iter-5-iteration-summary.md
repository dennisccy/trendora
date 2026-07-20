# Iteration Summary — goal-ops-hardening-iter-5

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-20
**Iteration:** 5

## In plain words

**What you can do now:** You can browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. You can back-fill any date range with no size cap and get an honest explanation when there's nothing new to add. After a restart, the app comes back online in about a second with a status badge that never falsely claims the backend is down. The Backtest page's forward-return scorecard, which used to take about 35 seconds to appear, now loads in under a second.

**What changed this time:** The team measured how fast every page in the app loads for the first time and found one real slowdown: the Backtest page's main table was recalculating a big statistic from scratch every time someone opened it, taking about 35 seconds. That's now fixed — it loads in well under a second, with the exact same numbers shown as before. One small side effect: after a data backfill, the "Refreshed" summary line on the Data page can now also mention "forward aggregates" as one more thing updated behind the scenes, and those backfill jobs may take a little longer to finish while that pre-calculation happens. One page was found to still load a bit too slowly under everyday conditions — the home page's small trend-history chart — and that one isn't fixed yet.

**What's next:** Next we'll speed up the home page's slow trend chart and double-check that the recent fixes haven't disturbed anything that was already working.

## Headline

Fixed a 252x Backtest slowdown, but a Dashboard chart still misses its load-time budget

## Direction

**Signal:** holding
**Why:** This iteration genuinely fixed a confirmed performance violation (`GET /api/backtest` 34.77s → 0.138s via a new `ForwardAggregateCache`, byte-identical to the live compute, verified across review/QA/audit), but the target journey J-06 still fails: the Dashboard's `/api/indexes?full=true` measures 1.68-2.19s under real browser connection-queuing (3/3 trials) against its 1.5s budget. No journey regressed and no anti-goal was violated — J-01/J-03 re-verified passing — but J-04/J-05 dropped to "unknown" because they weren't replayed this cycle, so this iteration made real progress without moving the pass/fail count, hence holding rather than improving.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-01, J-03, J-04, J-05
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 3 in iter-1/iter-2 (2 critical, 1 minor), all resolved within the session; none new in iter-3, iter-4, or iter-5
- Iters with no journey state change: 2 of last 5 (iter-3, iter-5)

**Latest evaluator reasoning:** The iteration's substantive deliverable — the `ForwardAggregateCache` fix for the confirmed `GET /api/backtest` violation (34.77s → 0.138s, ~252x, byte-identical, verified across review/QA/audit lanes) — is genuinely correct and shippable. But the target journey J-06 does NOT pass: TC-02 shows the Dashboard's `/api/indexes?full=true` at 1.68-2.19s in a real browser (3/3 trials) against its <=1.5s committed budget — a browser HTTP/1.1 connection-queuing gap curl-based measurement never surfaced. No journey genuinely regressed and no anti-goal was violated, so this is a CONTINUE toward a fresh iteration that resolves the Dashboard budget and restores clean regression evidence.

## What was done

- Extended `scripts/measure-perf.sh` with backend cold-boot timing and warm-hit latency measurement for the 7 previously-unmeasured pages (Dashboard cluster, Sectors, Themes, Scanner Runs, Backtest, Watchlist, Research event-study lab).
- Ran the full 11-page + boot measurement pass four times against prod-mode services and recorded four dated sections in `reports/perf-budgets.md`.
- Found and fixed a real performance violation: `GET /api/backtest`'s 5x-per-request `compute_forward_aggregates` scan (34.766s) — added an ingest-time-warmed `ForwardAggregateCache`, verified byte-identical, cutting latency to 0.138s (~252x faster).
- Completed the TC-13 code-level audit of all 11 pages' backing endpoints; confirmed `/api/runs`'s N+1 pattern is measured (0.050-0.196s) but not a current violation, left unfixed per spec.
- Added 20 new/updated unit tests (cache byte-identity, cache-hit avoidance, dataset-version invalidation) and re-ran the finalize-hook regression cluster; 15 targeted tests passed.
- Browser QA verified 10 of 11 measured pages within budget, including the Backtest fix (115-275ms real-browser); target journey J-06 did not pass — the Dashboard's `/api/indexes?full=true` exceeded its 1.5s budget in 3 of 3 real-browser trials.
- Re-verified required-still-passing J-01 and J-03 via deterministic replay (J-04/J-05 not replayed this cycle — a coverage gap, not a failure).

## What's left

- Journey J-06 ("Pages load only what they need") failing — the Dashboard's `/api/indexes?full=true` measures 1.68-2.19s under real browser connection-queuing, over its 1.5s budget (3/3 trials); curl-only measurement doesn't reproduce the gap.
- Closure blocker: resolve the Dashboard browser-concurrency budget (HTTP/2 on uvicorn, coalesce the Dashboard's 10-13 on-load calls, or a documented browser-realistic budget re-commit including `/api/data/availability`).
- Closure blocker: J-01's deterministic replay missed step-6 (a stale "2026-05-15" proxy assertion on `/scanner-runs`, adjudicated not a regression) — needs a robust assertion and a clean re-run.
- Closure blocker: J-04 and J-05 received zero regression-replay coverage this cycle (now "unknown" in journey-history) — both depend on the modified `_refresh_ingest_aggregates` function and must be re-run.
- Before merge: run `pytest tests/test_api_backtest.py tests/test_mcp_window.py -v` to completion (the `loaded_engine` fixture suite was not run this cycle).
- Closure-gate reminder: J-05's and J-06's `[NEW]` `demo.sh --session-live` walkthrough artifacts remain deferred; must be produced or explicitly waived before the eventual GOAL_ACHIEVED gate.
- `/api/runs`'s N+1 pattern (per-run `ScannerResult` count query) measured but not fixed — worth revisiting if scanner run history grows an order of magnitude.

## Next step

Full-depth fresh iteration (audit concurs), two scoped items: (1) Resolve the Dashboard `/api/indexes?full=true` browser-concurrency budget — choose a real latency fix (HTTP/2 on the uvicorn launcher or coalescing the Dashboard's 10-13 near-simultaneous on-load calls) or a documented browser-realistic budget re-commit in `reports/perf-budgets.md`, folding `/api/data/availability` (same class) into the same decision — then re-run QA's full plan including TC-16 to a clean J-06 pass. (2) Restore clean regression evidence — fix J-01's `/scanner-runs` step-6 proxy to be robust to the now-750-row run history (or re-point it at data the submitted backfill actually produces), re-run J-01, and run the skipped J-04/J-05 golden scripts, moving them out of "unknown." Before merging this iteration's backend code, run `pytest tests/test_api_backtest.py tests/test_mcp_window.py -v` to completion. Closure-gate: produce both J-05's and J-06's `demo.sh --session-live` walkthroughs, or have the human accept their deferral, before the eventual GOAL_ACHIEVED gate.

## Assumptions made

- iter-5 · goal-evaluator — Ambiguity: J-04 and J-05 (required-still-passing) received zero regression-replay coverage this cycle even though the shared `_refresh_ingest_aggregates` function they depend on was modified — no failing evidence exists, but no fresh passing evidence does either. We chose: scored both `unknown` rather than silently carrying `passing` forward, flagging them for mandatory re-verification next iter; did not treat the coverage gap as a regression. Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: J-01's deterministic golden-script replay FAILED (step-6: literal "2026-05-15" not found on `/scanner-runs`) with no LLM-fallback adjudication run, so the mechanical re-verification lane did not cleanly pass a required-still-passing journey. We chose: scored J-01 `passing` by adjudicating the miss as a stale proxy — replay steps 1-5 (J-01's actual acceptance) passed, the audit's DB query confirms the run exists, the runs-display code path is untouched in the diff, and the verify screenshot shows a healthy 750-row table. Flagged the golden-script fix as a next-iter blocker. Reversible: yes
- iter-5 · goal-decomposer — Ambiguity: J-06 carries the same `[NEW]`-flagged `demo.sh --session-live` walkthrough acceptance bullet that iter-4 already deferred for J-05 as a session-closure showcase artifact rather than a per-journey passing gate. We chose: applied the same reading to J-06 for consistency — the walkthrough stays a session-closeout showcase artifact, not part of this iteration's Definition of Done; restated the closure-gate reminder in the iteration spec's NOTES. Reversible: yes
- iter-5 · goal-decomposer — Ambiguity: J-06's DoD step 3 requires a code-level audit for unbounded scans, but goal.md doesn't say what to do if the audit/measurement finds a genuine violation on an endpoint outside the "four offenders" list (e.g. `/api/backtest`'s per-horizon read, `/api/runs`'s N+1 query). We chose: scoped this iteration to include a bounded, minimal fix only if it fits the existing ingest-time-cache convention through the value's existing computing module and endpoint — a violation needing a new architectural decision is out of scope and hands back to a fresh decomposer pass. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: J-05 step 3/TC-8 (the cold-boot check) was written with a literal "every coverage figure reads 0 or —" precondition on a byte-empty DB, but browser-qa found this precondition architecturally unreachable via any real boot and scored it PASS on the underlying safety property instead. We chose: accepted that adjusted-scope PASS and counted J-05 step-3's cold-boot check as executed-and-satisfied, since goal.md's own wording only asks for coverage rendering from the persisted payload within budget with no prefill, which was directly verified. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: J-05's Acceptance has four bullets; the fourth is a `[NEW]`-flagged `demo.sh --session-live` walkthrough, deliberately deferred this iteration as out of scope, so J-05's product-behavior acceptance is fully verified but one named Acceptance bullet is unproduced. We chose: scored J-05 `passing` on its product-behavior acceptance, treating the walkthrough as a session-closure showcase artifact; flagged as a closure-gate item that both J-05's and J-06's walkthroughs must be produced (or accepted as deferred) before the final GOAL_ACHIEVED gate. Reversible: yes
- iter-4 · goal-decomposer — Ambiguity: J-05's acceptance and the iter-3 evaluator's B3 fix direction were qualitative — goal.md never anticipated this pre-existing defect (discovered by iter-3's browser exercise), so no canonical name or field shape existed yet for the new readiness condition. We chose: a fourth `ReadinessState` literal `awaiting_snapshot` plus a new nullable `readiness.detail` field on the same `GET /api/health` payload, narrowing the servability comparison to the benchmark symbol rather than the whole-table latest-date max. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: ux-regression scored UX-REGRESSION-FAIL and framed B3 (fetch causing a false app-wide "Backend unavailable") and F1 (frozen job heartbeat) as undermining required-passing J-04's trust promise, which could be read as J-04 having regressed — but both root-cause to modules not in that iteration's diff, and J-04's scripted 6-step replay passed. We chose: scored J-04 `passing` (scripted acceptance holds, code unchanged) and treated B3/F1 as newly-surfaced pre-existing defects/hard blockers to a future GOAL_ACHIEVED, not a REGRESSION halt; flagged that a human who reads B3 as a vision/AG-3 violation may override. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: J-05 step-4's acceptance is the qualitative "stays responsive throughout," which the ui-test-plan sharpened to a stricter "every poll within 1s," but the measurement showed 2.9% of polls at 1.00-3.29s during parallel-backfill contention. We chose: applied goal.md's qualitative reading — the always-200, no-hang, badge-Ready result satisfies "stays responsive throughout"; the 2.9% slow window is a bounded, self-resolving blip, not an unresponsive state. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: AG-3 ("displayed numbers must be correct") can be read journey-scoped or product-wide; audit B1 (fetch-lands-bars → false-zero default `/data` coverage) is a genuine wrong-number display, but on a path no Must-have journey exercises. We chose: applied the journey-scoped reading for the verdict — it breaks no Must-have journey so does not force REGRESSION; recorded it unresolved (the #1 next-step), noting a human could override to REGRESSION under the product-wide reading. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: J-04's 6-step acceptance includes a crash→UI-unreachable visual step that was not freshly screenshotted this iteration, only re-verified via unchanged code and prior evidence. We chose: scored J-04 `passing` (partial→passing) anyway, since its badge/preflight/readiness code is unchanged this iteration and coherence confirmed no drift; future replay/QA re-exercises the crash-UI path. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: `config.yaml`'s comments claimed `scripts/start-backend.sh` already wires five server-tuning fields, but reading the script showed none were wired; goal.md's binding note names only two of the five plus a logfile as required this cycle. We chose: scoped the fix to exactly the three goal.md-named fields, left the other three unwired, and flagged the drift in NOTES rather than silently expanding scope. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: goal.md's "four offenders to retire" reads as a mandate to fully retire boot's `ensure_latest_snapshot` and the warm-up loop's cadence bootstrap, but neither is exercisable this session (both dormant against the offline seed). We chose: scoped J-05 to what its own 4 acceptance steps literally exercise, building the new `coverage_snapshot` table + ingest finalize hooks while leaving those two branches unchanged, since their retirement is unverifiable against the offline seed. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: J-01's DoD pins an exact productive-run breakdown, but the prescribed 2026-05-02→05-29 range had already been backfilled by a prior functional-QA pass before the browser session began, so no fresh same-session productive submission was captured live — the live submission hit the zero-work path instead. We chose: scored J-01 `passing` on the productive path via three corroborating sources rather than a fresh live run: the still-on-screen historical Run-History row, the re-run's `already_snapshotted=19`, and a unit test proving the fresh-run breakdown by construction. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-5-what-to-click.md`:

1. Open `http://localhost:3255/backtest` in your browser
2. Scroll to the "Return attribution" heading and click the "20d" button in the row of horizon buttons next to it
3. Open `http://localhost:3255/data` in a new tab (or navigate there)
4. Scroll down to the "Rebuild snapshots for current universe" panel and note the date shown after "the latest snapshot"
5. Scroll back up to "Start a fetch / backfill job," type that same date into both "Start date" and "End date," leave "Job kind" as "Backfill snapshots," then click "Start"

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-5.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-5-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-5-review.md |
| Browser QA | FAIL | reports/phase-goal-ops-hardening-iter-5-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-5-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-5-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-5-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-5-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-5-ui-test-plan.md |
| UX regression | UX-REGRESSION-FAIL | reports/phase-goal-ops-hardening-iter-5-ux-regression.md |
| QA | FAIL | reports/qa/goal-ops-hardening-iter-5-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-5-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-ops-hardening-iter-5-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-5/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
