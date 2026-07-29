# Iteration Summary — goal-ops-hardening-iter-29

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-07-29
**Iteration:** 29

## In plain words

**What you can do now:** Today you can browse stock rankings, sector pages, theme pages, backtests, research tools, and evidence-backed scores. Backfilling any historical date range gives you an honest explanation when there's nothing new to fetch, with no size limit on the range. The status badge tells the truth through startup, updates, or a crash, and a live panel shows background number-crunching as it happens. Because heavy calculations are prepared ahead of time, the Backtest page always serves stored numbers instead of recalculating on the spot.

**What changed this time:** The Evidence page's claim cards can now show a calm note — "Unavailable — monitored and refreshed as new data arrives." — on any single claim whose historical drawdown-and-dry-spell figures briefly fail to compute, instead of risking that one failure breaking the whole page. Behind the scenes, the same page's calculation was rewritten to use a fixed, bounded amount of memory instead of memory that grows with the site's price history — though the first version of that fix didn't actually work at today's scale, and had to be corrected during this iteration's own review before it took effect.

**What's next:** Next, we'll make sure the Factor Lab research page really works after a late fix, and close three more spots where the app can quietly run low on memory in the background.

## Headline

The Evidence page can no longer run the backend out of memory

## Direction

**Signal:** holding
**Why:** The session's oldest AG-8 finding (research.py's unbounded accumulator, open since iter-27) is now genuinely closed, confirmed via a 136-request page sweep and a 1,109-request backfill window with zero related MemoryError lines — but only after the audit caught and fixed a shipped chunk-width bug that had made the developer's original fix inert (0% memory reduction at every horizon). J-06 and J-07, this iteration's two target journeys, both moved from passing to partial (a skipped `perf-budgets.md` write, and a caught MemoryError inside J-07's own named producer), and the mandated regression check turned up a live, 100%-reproducible crash on `/research/factor-lab` that both the audit and ux-regression review scored FAIL. No journey regressed to failing and every new finding stayed minor, so the loop continues, but four new anti-goal findings are unresolved and full-depth re-verification is next.

**Trend (last 3 iters):**
- Newly passing this iter: none (all deltas were re-verifications of already-passing journeys, or demotions to partial)
- Newly passing in last 3 iters total: J-05, J-06, J-07, J-08 (all at iter-28; iter-27 and iter-29 had none)
- Regressions in last 3 iters: none scored as "regressed" — iter-29 did demote J-06 and J-07 from passing to partial (see Why), but neither crossed to failing/regressed
- Anti-goal violations in last 3 iters: 5 minor findings surfaced (1 at iter-27, resolved this iteration; 4 new at iter-29, unresolved); zero critical
- Iters with no journey state change: 0 of last 3

**Latest evaluator reasoning:** The main fix worked. The Evidence page now builds its drawdown figures in small bounded batches, and I saw the proof myself: the full-page picture of /evidence shows all 7 claim cards with real numbers, and the backend log has no memory failure from that page at all. The session's oldest open problem is closed. But this same run turned up three NEW out-of-memory failures on three other paths, and the browser report said there were none — that claim is wrong, and I checked the log line by line.

## What was done

- Product changes: apps/backend/app/engine/research.py, apps/backend/app/engine/evidence.py, apps/backend/tests/test_research_streaming.py, apps/backend/tests/test_evidence.py, apps/frontend/lib/evidence.ts, apps/frontend/lib/evidence.test.ts, apps/frontend/app/evidence/page.tsx
- Bounded `research.py`'s `_factor_observations` join accumulator into per-run-id slices so the Evidence page's drawdown-expectations computation no longer grows without limit as price history accumulates; output proven byte-identical and no-lookahead-preserving (TC-1/TC-2/TC-3).
- Added a per-claim isolate-and-continue guard to `evidence.py`'s `build_evidence_payload` — a single claim's compute failure now shows a calm "Unavailable" note instead of breaking the whole `/evidence` response (TC-4/TC-5).
- Audit caught and fixed a critical gap in the shipped fix: the chunk width had been reused from a row-count config value as a run count, producing exactly 1 chunk and 0% memory reduction at every horizon on the live basis; the audit added a dedicated `research.factor_join_run_chunk` config key (default 100), achieving 19 chunks and a 14.4x lower peak.
- Backend regression sweep: 312-435 tests passed across the touched and adjacent suites (0 failures, dev/QA/audit's combined runs); frontend: 46 evidence-resolver checks plus 5 factor-lab checks passed, `tsc --noEmit` clean.
- Re-verified 6 required-still-passing journeys (J-01, J-03, J-04, J-05, J-08, J-09) via deterministic golden replay — 6/6 PASS, zero FAIL rows, zero reconciliation overturns.
- Closed the session's longest-open AG-8 finding (`research.py`'s unbounded accumulator, open since iter-27) — confirmed via a 136-request page sweep and a 1,109-request backfill window with zero MemoryError lines tied to that function.

## What's left

- Journey J-06 (Pages load only what they need) — partial: `reports/perf-budgets.md` was not updated with this iteration's fresh `/evidence` readings, so its own step 2 and DoD item TC-8 are unmet.
- Journey J-07 (Heavy aggregates never take the service down) — partial: its own named producer, `compute_forward_aggregates`, raised a live MemoryError this window, even though the service stayed up throughout.
- `/research/factor-lab` returns HTTP 500 on every visit from an unbounded sibling accumulator (`_all_factor_observations_by_horizon`); the audit and the ux-regression review both returned FAIL on this. An undocumented, unreviewed fix landed after the audit and one live request returned 200, but nobody has re-verified it in a browser.
- Three new live MemoryErrors surfaced this window, all caught non-fatal: the boot warm-up (leaves the readiness pill stuck "Initializing…" forever), the ingest-time coverage refresh (still streams the whole `daily_prices` table), and the byte-frozen `compute_forward_aggregates` function.
- Open question, unsettled: the 2022-04-12 backfill's run record says "coverage refreshed" while the log shows that exact refresh failing with a MemoryError in the same window — whether the disclosure shown to users is accurate is not yet established.
- Carried, unchanged: audit finding B2 (`_backfill`'s cross-call rollback residual); `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches before removing dangling imports; UT-04's fresh-install DB fixture or a written waiver; `test_no_magic_numbers.py` red on unrelated files (`indicators.py`, `forward_testing.py`).

## Next step

Run the next round at full depth. Do five things, in this order: (1) Prove the Factor Lab page actually works now — open `/research/factor-lab` in a real browser and capture the decile table and rank-IC figures; if it still fails, bound the returned pools too, not just the lookup map. (2) Stop the three new out-of-memory failures on the start-up warm-up, the background forward-aggregate job (inside the byte-frozen `compute_forward_aggregates` — the planner must lift that freeze on purpose), and the ingest coverage refresh, which still reads the whole price table into memory. (3) Decide what the top-bar badge should say when start-up warm-up fails for good — "Initializing…" forever is not honest. (4) Write this iteration's page-load timings into `reports/perf-budgets.md` — that one edit closes J-06 — and run the J-06 replay script through the deterministic lane. (5) Require the browser-testing step to cite the log line it counted from whenever it claims "zero memory errors" — this run claimed zero and there were three.

## Assumptions made

- iter-29 · goal-evaluator — Ambiguity: whether a caught MemoryError inside J-07's own named producer (`compute_forward_aggregates`), while the service stayed up, breaks the journey or merely dents it. We chose: scored J-07 `partial` — not `passing` (the acceptance clause is contradicted by live evidence) and not `failing` (the service was never taken down, which is the journey's actual headline promise). Reversible: yes
- iter-29 · goal-evaluator — Ambiguity: whether measuring-and-comparing this iteration's `/evidence` timings without recording them in the committed `reports/perf-budgets.md` file satisfies J-06's own step 2. We chose: scored J-06 `partial`, not `passing` — the step is literal, checkable, and unmet, and the audit independently recorded the same gap. Reversible: yes
- iter-29 · goal-evaluator — Ambiguity: whether a caught, non-fatal memory exhaustion that leaves the service serving and the UI showing a contained error box (the Factor Lab crash plus three other new MemoryErrors) is AG-8's critical violation or a minor open finding. We chose: scored all four `minor`, keeping the verdict CONTINUE rather than a REGRESSION halt, on the grounds the service was never taken down and every failure was caught and logged non-fatal. Reversible: yes
- iter-29 · goal-decomposer — Ambiguity: whether reusing the Evidence page's existing "render nothing" behavior already satisfies AG-8's "honest NA placeholder" for a new failure cause, or whether that cause must be visually distinguishable from the pre-existing case. We chose: make it distinguishable — a new `expectations_status: "unavailable"` field and a calm inline note, rather than silently reusing the existing empty-render path. Reversible: yes
- iter-28 · goal-evaluator — Ambiguity: whether J-07's "no unbounded whole-table ORM materialization" acceptance clause is scoped to its own named producer or to every warm/serving path in the backend. We chose: scored J-07 `passing`, reading the clause as scoped to its own named producer, while tracking the neighbouring `research.py` defect as a separate, open AG-8 finding. Reversible: yes
- iter-28 · goal-evaluator — Ambiguity: whether an environmentally-unreachable DoD sub-case (UT-04, J-05's "not yet computed" coverage state, unreachable on this seeded 1872+-row database) blocks the journey it's attached to. We chose: scored J-05 `passing` with the skip recorded as an open, named gap. Reversible: yes
- iter-28 · goal-evaluator — Ambiguity: how much of J-07/J-08 must be re-exercised to restore `passing` after iter-27 touched part of their path. We chose: scored both `passing` on a scope-of-change test, confirming iter-27's diff was confined to functions outside the un-re-run steps' paths. Reversible: yes
- iter-27 · goal-evaluator — Ambiguity: whether a memory-exhaustion 500 on pre-existing, untouched code, occurring while the host was under the pipeline's own test load, is AG-8's critical violation or a minor open finding. We chose: recorded it as a new, unresolved finding but scored it minor, keeping the verdict CONTINUE rather than a REGRESSION halt. Reversible: yes
- iter-27 · goal-evaluator — Ambiguity: whether a prior iteration's passing status carries forward across a build that changed that journey's serving path when browser-QA was killed mid-run (J-05/J-07/J-08), and whether developer self-verification can stand in for the missing browser-QA pass. We chose: scored all three `unknown`, not `passing`, and blocked GOAL_ACHIEVED on the missing evidence. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-29.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-29-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-29-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-29-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-29-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-29-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-29-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-29-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-29-ui-test-plan.md |
| UX regression | UX-REGRESSION-FAIL | reports/phase-goal-ops-hardening-iter-29-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-29-qa.md |
| Audit | FAIL | docs/handoffs/goal-ops-hardening-iter-29-audit.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-29/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
