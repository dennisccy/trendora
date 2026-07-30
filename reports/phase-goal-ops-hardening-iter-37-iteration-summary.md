# Iteration Summary — goal-ops-hardening-iter-37

**Verdict:** ESCALATE
**Iteration type:** goal-full
**Date:** 2026-07-30
**Iteration:** 37

## In plain words

**What you can do now:** Back-fill any historical date range and get an honest explanation when there's no new work to do, watch the app boot with a truthful status badge instead of a blank screen, browse stock rankings, sector/theme views and backtests where the heavy numbers were computed once at data-import time rather than live on your screen, open any of the five research tools (Regime Lab, Factor Lab, Market Phase & Severity Lab, Regime x Phase x Factor, Severity-velocity) and see an honest "still working" message with a Retry button instead of a blank screen during a slow load, and see a truthful banner whenever the app is doing heavy work in the background. Confirming that heavy background work never takes the whole service down is still in progress, not yet fully proven.

**What changed this time:** Nothing changed on screen this round — no page or button is different. Behind the scenes, importing several days of price history in one request now loads the price-history table from disk only once instead of twice, so big data updates run faster and use less memory. The team also ran a real 70-second live test of the heaviest background calculation while the "is the app alive" check kept answering correctly the whole time, and wrote down for the first time exactly how much memory headroom the app has to spare (57%).

**What's next:** Next, the team will re-run the memory stress-test with a real multi-day data import in it (the last one used an empty test job, so it didn't actually exercise this round's change), and then run the health check the way it's supposed to be triggered — from the end of a real data import rather than from the Backtest page.

## Headline

Backfill jobs now load price history once instead of twice; J-07 steps 1-4 ran live but stayed partial

## Direction

**Signal:** holding
**Why:** No journey regressed and none newly reached "passing" this iteration — seven journeys (J-01, J-03, J-04, J-05, J-06, J-08, J-09) re-verified clean, and J-07 stayed `partial` for a third consecutive iteration because both of its live measurements this round ran through paths where the iteration's own code change is inert. Two anti-goal findings closed (iter-36/l, iter-36/m) and one in-iteration regression (iter-37/p, a possible permanent 1.13GB pin) was found and fixed by the audit before it could ship, so overall AG-8 posture improved even though the journey mix did not move.

**Trend (last 3 iters, fewer than 5 evaluator-log entries available):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: J-06 (iter-36)
- Regressions in last 3 iters: none (iter-35 built no code due to a depth mis-dispatch; iter-36 and iter-37 both explicitly report zero passing->failing moves)
- Anti-goal violations in last 3 iters: 6 new, all minor (3 in iter-36, 3 in iter-37, one of which — iter-37/p — was found and fixed in the same iteration); 0 critical in any of the 3
- Iters with no journey state change: 2 of last 3 (iter-35 and iter-37; iter-36 crossed J-06 to passing)

**Latest evaluator reasoning:** This was a strong iteration and the code work is sound. The one code defect it targeted is closed: a big multi-date data-backfill job now loads the price history into memory once instead of twice, proven by a test that was red before and is green now, plus a "same-answer-as-before" check that a second test proves is real and not a rubber stamp. All four of J-07's steps were actually run live for the first time in three tries, and I re-checked the raw numbers myself: 130 out of 130 health checks answered OK during a 69-second heavy computation, and the process used only 43% of its memory limit. But J-07 still does not fully pass, and the reason is not a code defect — it is that the measurements avoided the exact path this iteration changed.

## What was done

- Product changes: apps/backend/app/engine/data_manager.py, apps/backend/tests/test_backfill_coverage_shared_cache.py
- Shared one prefilled bar-cache across `_do_backfill` and the whole ingest-finalize tail instead of each opening its own, eliminating a duplicate whole-table `daily_prices` load on every multi-date backfill job.
- Target test `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` now passes at exactly 1 load per symbol (was max 10 pre-fix, re-measured fresh this iteration).
- Added a byte-identity reference-oracle test pinned to `git show HEAD`, plus a paired mutation test proving the oracle is load-bearing, not a rubber stamp.
- Ran J-07 steps 1-4 live for the first time this session: 130/130 health polls returned HTTP 200 during a real 69.44s five-horizon warm (VmPeak flat at 57.19% margin under the memory cap, now recorded in `reports/perf-budgets.md`), and an induced memory-pressure drill aborted honestly with the same process still serving, no restart.
- Audit found and fixed an in-iteration regression (iter-37/p) that review and QA both missed: the deferred cache release could pin ~1.13GB permanently after a rare secondary failure — fixed and mutation-tested in the same audit pass.
- Verified 9/9 target journeys pass browser QA (7 regression replays + 2 J-07 smoke checks).

## What's left

- Journey J-07 ("Heavy aggregates never take the service down") still `partial` — third consecutive iteration; both live drills this iteration ran through paths where the new shared-cache code is inert (the warm was triggered from the Backtest page, not the ingest-finalize path; the pressure drill used a zero-date job), so the code's actual memory effect on the finalize tail remains unmeasured.
- Re-run the induced-pressure drill on a throwaway DB with a real K>=3-date backfill (not a 0-target no-op) so the shared cache is genuinely exercised, and sample peak memory across the whole finalize tail.
- Re-run J-07 step 1's warm the way its own text names — triggered from the end of a real data-import job, not the Backtest page.
- Owner decision open: the `GET /api/health` <=0.1s budget missed for the 4th time (max 0.98s during a live warm) — three dispositions are still on the table.
- Owner decision open: whether `start-frontend.sh` should join `HOST_GUARD_MARKER_FILES` (new evidence this iteration: `scripts/dev.sh`'s stop signal orphaned the frontend process and held its port).
- Regime Lab's cold `view=pooled` compute still runs inline on the request thread and one path returns a bare "Internal Server Error" body — deferred twice, next in queue (iter-33/g).
- Two unrelated read paths hit their own uncaught MemoryError under an artificially tight 970MB test-only cap (not reachable at the real 6144MB production cap) — recorded as a new finding (iter-37/q) for a future iteration.
- J-07's `[NEW]` walkthrough recording is still missing — 7 iterations unrecorded; 11 minor anti-goal ledger findings remain unresolved (0 critical).

## Next step

Run the next iteration at full depth (mandatory under ESCALATE). First, measure the path this iteration actually changed: re-run the induced-memory-pressure drill on a throwaway database with a real 3-or-more-date backfill (not a zero-date no-op) so the new shared price cache is genuinely active, and sample peak memory across the whole end-of-import warm, compared against a run forced onto the old behavior — this is cheap and safe on a small throwaway database, launched only through `scripts/start-backend.sh`. Then run J-07 step 1 the way its own text says: start the heavy warm from the end of a real data-import job, not the Backtest page, with the once-per-second health check running during it. After that, take up the Regime Lab "All history" background-dispatch fix, already queued twice. Two owner decisions remain outstanding and should be settled before any achievement run: pick one of the three options for the `/api/health` <=0.1s budget (now missed a 4th time), and decide whether `start-frontend.sh` should join the host-protection marker list.

## Assumptions made

- iter-37 · goal-evaluator — Ambiguity: decision tree C.4 ("the same journey has now failed 2+ consecutive iterations") technically matches for a third consecutive ESCALATE, but the methodology also says to use ESCALATE sparingly and this iteration was already dispatched at full depth. We chose: ESCALATE again — the tree is first-match-wins, and independently this iteration's review and QA lanes both missed a real regression (iter-37/p) that only the audit lane caught, reinforcing that full depth is still needed. Reversible: yes
- iter-37 · goal-evaluator — Ambiguity: J-07's four steps all ran live, but two of them (the warm trigger and the pressure-drill job) ran through paths where this iteration's own code change is inert, so the specific new state it creates was never measured. We chose: keep J-07 `partial` for a third iteration rather than score it `passing`, because the ground is genuinely new (this iteration's change), not just re-inherited from last time. Reversible: yes
- iter-37 · goal-decomposer — Ambiguity: whether rule 5's one-risky-item-per-iteration cap covers a heavy live verification pass (J-07 steps 1-4) bundled alongside a genuine code change. We chose: bundle both into one iteration — rule 5's precedent has only ever applied to code changes, not measurement passes, and splitting them would delay J-07 by a full extra cycle with no diagnostic benefit. Reversible: yes
- iter-36 · goal-evaluator — Ambiguity: whether J-06 returns to `passing` once the specific clause that downgraded it is fixed, while a sibling clause's fresh measurement (the `/data` panel) is still unrun this iteration. We chose: restore J-06 to `passing` and clear `evidence_makeup` — the on-load request path is unchanged, and the downgrade's own stated premise (a bare unlabelled grey skeleton on every lab) was falsified by screenshots this iteration opened directly. Reversible: yes
- iter-36 · goal-evaluator — Ambiguity: whether a journey status of `partial` (not literally "failed") still triggers decision-tree clause C.4's ESCALATE after two consecutive non-passing iterations. We chose: ESCALATE, reading "failed" as "did not reach passing" — this session already lost an entire iteration once to an advisory (non-mandatory) full-depth recommendation being downgraded. Reversible: yes
- iter-36 · goal-evaluator — Ambiguity: whether J-07 should score `partial` or `unknown` when its browser lane never ran but the auditor independently verified several of its steps by hand. We chose: `partial` — it is literally what the evidence shows (some steps verified this iteration, some not), and scoring it `unknown` would discard real evidence a lane actually produced. Reversible: yes
- iter-36 · goal-decomposer — Ambiguity: whether a second, smaller memory-bound fix in the same accumulator family may be folded into an iteration that already carries one structural fix under rule 5's "one risky change" cap. We chose: fold it in as a third, explicitly small item rather than defer it to the next iteration, since it closes a live, twice-reproduced serving-path failure one iteration sooner. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-37.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-37-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-37-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-37-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-37-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-37-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-37-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-37-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-37-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-ops-hardening-iter-37-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-37-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-37-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-37-closure-verdict.md |
| Goal evaluation | ESCALATE | runs/goal-session-ops-hardening/iter-37/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
