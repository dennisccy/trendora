# Iteration Summary — goal-ops-hardening-iter-41

**Verdict:** ESCALATE
**Iteration type:** goal-full
**Date:** 2026-07-31
**Iteration:** 41

## In plain words

**What you can do now:** Kick off a price-history backfill for any date range with no hidden size limit and see an honest message when nothing new needed fetching. Watch the app boot with a clear "Ready" status (or an honest "unavailable" message) instead of a blank screen. Browse stock rankings, sectors, themes, and research pages that only load the data they actually need. Backtest results always come from stored, already-computed evidence — never a slow live recalculation while you wait. A live indicator shows you whenever background number-crunching is happening.

**What changed this time:** Nothing new to see on screen — but the price-history loading behind the Data page now uses about half the memory it used to (roughly 1.34 GB down to 0.65 GB) while producing the exact same numbers, and if a backfill job gets killed mid-way, its saved progress is now accurate to within about 5 days instead of drifting much further off.

**What's next:** Next we'll properly re-check the precomputed-calculations and heavy-load resilience features that this round worked on but didn't actually get tested yet.

## Headline

Verification pipeline repaired — 3 journeys re-confirmed passing; two target journeys still unverified

## Direction

**Signal:** improving
**Why:** J-01, J-04, and J-06 moved from unknown to passing this iteration on genuine, dated browser evidence, and J-03/J-08/J-09 were freshly re-verified — the verification lane that had gone dark for two iterations is demonstrably back. But the iteration's own two target journeys, J-05 and J-07, got zero browser-QA rows despite a clean merged "PASS 6/6" headline, and J-07 has now missed passing for 7 consecutive iterations, so ESCALATE fires again.

**Trend (last 2 iters):**
- Newly passing this iter: J-01, J-04, J-06
- Newly passing in last 2 iters total: J-01, J-04, J-06 (none newly passed in iter-40)
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: 4 new, all minor, 0 critical (iter-40/y, iter-41/z, iter-41/aa, iter-41/ab)
- Iters with no journey state change: 0 of last 2

**Latest evaluator reasoning:** "This is the best iteration in six, and I want that said before the verdict is read. For the first time in five tries, real people-facing checks ran again: six journeys were driven through a live browser today and each left a dated picture I opened myself. Three journeys that were untested last time are now confirmed working. Nothing broke."

## What was done

- Product changes: apps/backend/app/engine/prices.py, apps/backend/app/engine/data_manager.py, apps/backend/main.py
- Repaired the browser-QA verification lane so backend-only iterations still re-check required-still-passing journeys instead of silently skipping them (fixed three shell-level gates plus the ui-test-designer agent's backend-only handling).
- Fixed the health-check URL the browser-qa dispatch polls (was the generic `/health`, now Trendora's real `/api/health`) so a live backend answering the wrong path is never misreported as down.
- Added missing-required-journey / all-SKIP detection to the results merger so a clean PASS/SKIPPED headline can no longer hide an unverified required journey (new BLOCKED verdict class).
- Bounded `_BarCache.prefill`'s in-memory accumulator with a columnar store — 51.5% VmPeak reduction (1,371,032 → 664,580 kB), byte-identical output proven by a fixture test.
- Added a count-based checkpoint floor (every 5th date) so a killed backfill's persisted progress is at most ~5 dates stale, instead of potentially much further off.
- Armed an opt-in SIGUSR1 thread-dump diagnostic and extended the wedge-drill monitor to keep polling past terminal job status; re-ran the memory-freeze drill once — the freeze did not recur.
- Verified 6 required-still-passing journeys (J-01, J-03, J-04, J-06, J-08, J-09) pass browser QA with fresh dated evidence; the iteration's own 2 target journeys (J-05, J-07) got zero browser-QA rows despite the merged file's clean "PASS 6/6" headline.

## What's left

- Journey J-05 ("Aggregates are precomputed at ingest, never on the fly") is `unknown` — got zero browser-QA evidence this iteration; promoting it to a target journey moved it out of the replay lane rather than into fresh evidence.
- Journey J-07 ("Heavy aggregates never take the service down") is `partial` for a 7th consecutive iteration — the memory accumulator was compressed, not bounded, and the freeze from several iterations ago still isn't positively diagnosed (it did not recur this time).
- A target journey still cannot get a browser-QA test case on a backend-only iteration — the results merger can show a clean "PASS" while both of an iteration's own target journeys are unverified (audit finding B2, ledger iter-41/z, open).
- `_BarCache.prefill` still holds the whole `daily_prices` table resident in memory (51.5% cheaper per row, not a real bound) — goal.md's "no code path streams the full table into RAM" clause is still not literally met (audit finding B3, open 12 iterations).
- The QA report's AG-8 compliance row inaccurately claims "no whole-table loads" (ledger iter-41/ab, open).
- Owner decision still open: the `GET /api/health` ≤0.1s response-time budget, missed for the 8th consecutive iteration (max 1.73s this round).
- Owner decision still open: whether `start-frontend.sh` should join the host-guard marker-file list.
- Regime Lab's cold `view=pooled` background compute still takes about a minute (iter-33/g, deferred a 6th time).

## Next step

Run the next iteration at full depth (mandatory via ESCALATE). In order: (1) make the two journeys under active work (J-05, J-07) get checked too — write a target-journey test case for backend-only rounds AND teach the results merger to refuse a clean PASS when a target journey has no row (both halves are needed; the merger fix alone would wrongly flag normal rounds); (2) re-check J-05 and J-07 in the browser using the existing golden scripts (`journey-scripts/J-05.json`, `J-07.json`); (3) decide what "no whole-table load" means for `_BarCache.prefill` — either write the real per-symbol bound or amend goal.md to a per-row budget the current design meets, and correct the QA report's AG-8 row either way; (4) small already-written-down items: one line of null-tolerance for the new columnar store, and a before/after page-speed measurement for it; (5) two owner decisions remain outside agent scope and should be settled before any GOAL_ACHIEVED attempt: the `/api/health` ≤0.1s budget (missed 8 times) and whether `start-frontend.sh` joins the host-guard file list.

## Assumptions made

- iter-41 · goal-evaluator — Ambiguity: J-04's replay script covers only 2 of its 6 acceptance steps (boot-ready state and job history), and the code that changed this iteration (the checkpoint count-based floor) sits inside one of the uncovered steps. We chose: score J-04 `passing`, naming every uncovered step explicitly rather than downgrading it for a partial-coverage script. Reversible: yes
- iter-41 · goal-evaluator — Ambiguity: this is the sixth consecutive ESCALATE on the same J-07 stall, weighed against "escalate sparingly" guidance and the fact this was the best iteration in six. We chose: ESCALATE again — first-match-wins session precedent plus an independent trigger (the fifth consecutive iteration where only the auditor caught a load-bearing defect: the new guard didn't catch the exact incident it was built to prevent) outweigh escalation fatigue. Reversible: yes
- iter-41 · goal-decomposer — Ambiguity: whether the evaluator's five ordered next-step items should be one iteration's scope or split across several. We chose: bundle all five into iter-41, since only the `_BarCache.prefill` bound is risky product code (the one-risky-item rule still holds) and splitting would strand it unverified for a whole extra iteration. Reversible: yes
- iter-40 · goal-evaluator — Ambiguity: fifth consecutive ESCALATE weighed against "escalate sparingly" methodology guidance, even though the iteration delivered its mandated target well. We chose: ESCALATE again — first-match-wins precedent plus an independent trigger (a DoD checkbox shipped entirely unexecuted and seven required journeys unverified, with review/QA/closure all reporting clean). Reversible: yes
- iter-40 · goal-evaluator — Ambiguity: whether a journey with zero this-iteration evidence but a behavior-neutral diff should stay `passing` (durability) or drop to `unknown`. We chose: a code-path split — a journey stays `passing` only if no diff hunk lies on the path it asserts on; otherwise it drops to `unknown`, which discarded J-01/J-04/J-05/J-06's inherited passing status that iteration. Reversible: yes
- iter-39 · goal-evaluator — Ambiguity: fourth consecutive ESCALATE weighed against methodology's "use sparingly" guidance, even though the iteration delivered its mandated target. We chose: ESCALATE again, citing an independent trigger (audit FAIL on a critical missing MemoryError isolation that review and QA both passed) and the cost asymmetry of one extra full pipeline versus a potentially lost iteration. Reversible: yes
- iter-39 · goal-evaluator — Ambiguity: whether J-07's "no unbounded whole-table load" clause is scoped narrowly (to the two named tables in its parenthetical) or broadly (per goal.md's headline Success Criteria), given a violation was found on a third table (`daily_prices`). We chose: the broad reading, consistent with iter-37 precedent and goal.md's unqualified Success Criteria wording, keeping J-07 `partial`. Reversible: yes
- iter-38 (header truncated in the trimmed log) · goal-evaluator — Ambiguity: J-04's deterministic replay returned FAIL because the backend was down during the run, while the LLM fallback lane declined and the merged file recorded SKIPPED, leaving it unclear whether J-04 should score `unknown` or keep `passing` on durability. We chose: kept J-04 `passing` without advancing its verified iteration, naming every uncovered acceptance step. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-41-what-to-click.md`:

1. Open `http://localhost:3255/` in your browser
2. Click "Data" in the top navigation (or go directly to `http://localhost:3255/data`)
3. Type `2026-05-02` in "Start date" and `2026-05-29` in "End date", then click the "Start" button (accent button, play icon)
4. Scroll down to "Run history"
5. Refresh the page (press F5)

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-41.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-41-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-41-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-41-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-41-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-41-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-41-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-41-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-41-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-ops-hardening-iter-41-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-41-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-41-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-41-closure-verdict.md |
| Goal evaluation | ESCALATE | runs/goal-session-ops-hardening/iter-41/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
