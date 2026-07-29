# Iteration Summary — goal-ops-hardening-iter-28

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-07-27
**Iteration:** 28

## In plain words

**What you can do now:** You can browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. You can back-fill any historical date range and get an honest explanation when there's nothing new to fetch, with no limit on how large a range you request. The status badge stays truthful through startup, updates, or a crash, and a live panel shows whenever background number-crunching is happening plus what happened last time. Heavy calculations are done ahead of time, so restarts serve stored numbers right away, and the Backtest page tells you whether its numbers are fresh, a labeled still-good version, or not ready yet — even when two people open the same old date at once.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The team finished independently re-checking two fixes from last round in the browser (the Backtest page's two-people-same-date handling, and the Data Manager page's "slightly older data" note), and both are now fully confirmed working. They also fixed a test mistake that was making one unrelated page falsely report a problem, by cleaning up a leftover setting left pointing at a different, already-finished project.

**What's next:** Next we'll fix the Evidence page's out-of-memory problem so it never fails under heavy use.

## Headline

Closed the browser-QA evidence gap for J-05, J-07, J-08 — all 8 journeys now pass

## Direction

**Signal:** improving
**Why:** Iter-28 finished the browser verification that iter-27's account-usage-limit kill left incomplete — a completed re-run of the unchanged iter-27 build put J-05, J-07, and J-08 at passing for the first time, and a golden-script fix corrected J-06's false failure, bringing all 8 Must-have journeys to passing simultaneously. Review PASS, coherence PASS, and no new anti-goal findings surfaced this iteration. The sole remaining blocker to GOAL_ACHIEVED is the carried, unresolved AG-8 finding in `research.py:215` (unbounded in-RAM accumulation on `/api/evidence`), which the evaluator recommends fixing next at full depth.

**Trend (last 3 iters):**
- Newly passing this iter: J-05, J-06, J-07, J-08
- Newly passing in last 3 iters total: J-05, J-06, J-07, J-08 (all this iter; iter-26 and iter-27 had none)
- Regressions in last 3 iters: none (J-05/J-06/J-07/J-08 dipped to unknown/partial at iter-27 for missing evidence, never scored as "regressed")
- Anti-goal violations in last 3 iters: 3 minor total — 2 new at iter-26 (AG-8 concurrent-request 500, AG-3 stale coverage zeros, both resolved by iter-27) and 1 new at iter-27 (AG-8 MemoryError on `/api/evidence`, still open at iter-28); no critical violations
- Iters with no journey state change: 1 of last 3 (iter-26)

**Latest evaluator reasoning:** This iteration had one job: finish the browser checks that iteration 27 could not finish, because its testing agent was stopped part-way by an account usage limit. That job is done. All four journeys that were missing proof — J-05 "Aggregates are precomputed at ingest, never on the fly", J-06 "Pages load only what they need", J-07 "Heavy aggregates never take the service down" and J-08 "Backtest evidence serves from storage only" — now have fresh screenshots and passing test rows, and the other four journeys were replayed and still pass. All eight journeys pass.

## What was done

- Relocated `data_quality.drift.report_path` (`config.yaml` + `config.py`'s `_DEFAULT_DRIFT_REPORT_PATH`) out of another, closed goal session's folder into this session's own state directory — byte-identical computation and consumers, file-location change only.
- Moved the drift-report artifact itself via git rename (byte-identical content), so the drift preflight component keeps reporting its real "clean" status through the move.
- Fixed J-06 "Pages load only what they need"'s self-poisoning golden script: step 1 now checks for stable "Market Regime" Dashboard content instead of the incidental "DEGRADED" preflight string.
- Ran the four DoD-named drift-selector tests in one combined pytest invocation — 20 passed, 0 failed (TC-11 met); review verdict PASS with independent verification of diff scope.
- Re-ran the full iter-27 browser-QA plan (UT-01 through UT-09) against the unchanged iter-27 build, closing the evidence gap an account-usage-limit kill had left open.
- Verified all 4 target journeys — J-05, J-06, J-07, J-08 — pass browser QA (8/9 test rows PASS, 1 documented SKIP); all 8 Must-have journeys now pass.

## What's left

- Anti-goal finding AG-8 (open, minor, carried since iter-27): `research.py:207-217`'s unbounded `ret_by_run_symbol` accumulation on `GET /api/evidence` and the ingest-finalize path — the sole blocker to GOAL_ACHIEVED.
- J-06 "Pages load only what they need" passed via the LLM browser lane's live reproduction, not the deterministic replay lane — the automated replay mechanism for the fixed script is still unexercised.
- J-05's DoD sub-case UT-04 ("not yet computed" coverage state) was SKIPPED — unreachable on this seeded database (1872+ snapshot rows); needs a fresh-install DB fixture or an explicit waiver.
- Documentation correction owed: `test_readiness.py -k drift` is not actually fixture-free (pulls the 30-year `loaded_engine` fixture, ~1h37m runtime) — future lean-iteration specs should budget for it.
- Carried, non-blocking: audit finding B2 (`_backfill`'s cross-call rollback residual) needs its own scoped follow-up.
- Carried, non-blocking: `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches need retargeting before removing dangling imports at `backtest.py:75` / `mcp/tools.py:38`.
- Owner, non-blocking: the never-scanned historical `/backtest` first-touch latency (206-273s this run) still has no written time budget; backlog card B-1107 stays optional.

## Next step

Run the next iteration at full depth with one blocking job: stop the Evidence page from loading the whole forward-returns table into memory at once (`research.py:215`), and give `GET /api/evidence` an honest reduced/degraded response instead of failing — the same defect also breaks the background job that finishes an import (`data_manager.py:3361`). Full depth is right because this change puts a new message in front of the user, which `docs/goal.md` itself names as the trigger for full depth, and because it needs the extra review, UX-regression, and closure checks. Ride-alongs: replay the fixed `J-06.json` script through the automated deterministic-replay lane once so its literal mechanism is exercised by machine, not only by hand; flag that `test_readiness.py -k drift` is not actually fixture-free (it pulled the 30-year fixture and cost 1h37m); either build a genuinely empty-database fixture for the skipped UT-04 case or write an explicit waiver; and have the testing agent report actual request counts and each request's `write_taken` flag whenever it claims a concurrency result. Carried, unchanged: audit item B2 (`_backfill`'s rollback residual) and retargeting `test_forward_testing_serving_split.py`'s `is_latest` monkeypatches before removing dangling imports. For the owner, nothing blocking: the never-scanned historical `/backtest` load took 206-273s this run (down from 12-24 minutes last round) but still has no written time budget; backlog card B-1107 stays optional.

## Assumptions made

- iter-29 · goal-decomposer — Ambiguity: whether reusing the Evidence page's existing "render nothing" behavior already satisfies AG-8's "honest NA placeholder" for a new failure cause (a caught per-claim compute exception), or whether that cause must be visually distinguishable from the pre-existing case. We chose: make it distinguishable — add a new optional `expectations_status: "unavailable"` field and a calm inline note, rather than silently reusing the existing empty-render path. Reversible: yes
- iter-28 · goal-evaluator — Ambiguity: how much of J-07/J-08 must be re-exercised to restore `passing` after iter-27 touched part of their path, since several steps (J-07's VmPeak re-record and induced memory-pressure abort; J-08's refreshing-marker and never-warmed states) were not re-run this iteration. We chose: scored both `passing` on a scope-of-change test — confirmed iter-27's diff was confined to functions outside those steps' paths, and re-exercised the one path that did change under a genuine concurrent race. Reversible: yes
- iter-28 · goal-evaluator — Ambiguity: whether an environmentally-unreachable DoD sub-case (UT-04, J-05's "not yet computed" coverage state, impossible on this seeded 1872+-row database) blocks the journey it's attached to. We chose: scored J-05 `passing` with the skip recorded as an open, named gap — the unreachable state isn't one of J-05's four goal.md steps, and all four were verified this run. Reversible: yes
- iter-28 · goal-evaluator — Ambiguity: whether J-07's "no unbounded whole-table ORM materialization" acceptance clause is scoped to J-07's own named producer or to every warm/serving path in the backend, given the still-open AG-8 finding sits in a neighbouring `research.py` aggregate. We chose: scored J-07 `passing`, reading the clause as scoped to its own producer and `/api/backtest` path (exercised cleanly this run), while keeping the `research.py` defect tracked as a separate, open AG-8 finding. Reversible: yes
- iter-27 · goal-evaluator — Ambiguity: whether a memory-exhaustion 500 on pre-existing, untouched code (two unhandled `MemoryError`s on `GET /api/evidence`) while the host was under the pipeline's own test load counts as AG-8's critical "exhaust a service's memory" violation or a minor open finding. We chose: recorded it as a new, unresolved finding but scored it minor rather than critical, keeping the verdict CONTINUE rather than a REGRESSION halt. Reversible: yes
- iter-27 · goal-evaluator — Ambiguity: whether a prior iteration's passing status carries forward across a build that changed that journey's serving path when browser-QA was killed mid-run (J-05/J-07/J-08), and whether developer self-verification can stand in for the missing browser-QA pass. We chose: scored all three `unknown`, not `passing`, and blocked GOAL_ACHIEVED on the missing evidence rather than crediting the developer's own capture. Reversible: yes
- iter-27 · goal-decomposer — Ambiguity: whether the AG-3 coverage-panel fix should recompute live on the request path (option a) or serve a labeled stale prior snapshot (option b), since goal.md's compute-at-ingest principle doesn't resolve which remedy is compliant. We chose: option (b) — a stale-row fallback with an honest `coverage_status` label, never a request-path recompute. Reversible: yes
- iter-26 · goal-evaluator — Ambiguity: whether a server-side 500 on `/api/backtest` (AG-8) and an all-zero `/data` coverage panel for a populated database (AG-3) — neither introduced by that diff, neither witnessed reaching the user as a broken page — count as critical or minor. We chose: minor for both, so the verdict was ESCALATE rather than a REGRESSION halt. Reversible: yes
- iter-26 · goal-decomposer — Ambiguity: whether J-09's "shows a failed background compute" clause requires an actual witnessed live failure capture, or whether a deterministic code-level round-trip test is sufficient citable evidence, given the only known way to trigger a genuine failure reproduces an unsafe memory-pressure pattern. We chose: a backend test plus a frontend rendering unit test, never re-triggering the unsafe live failure. Reversible: yes
- iter-25 · goal-evaluator — Ambiguity: whether a required-still-passing journey (J-07) that failed its deterministic replay because the host was under the test harness's own memory pressure counts as verified. We chose: accepted the overturn and scored J-07 `passing`, after tracing the cause to a logged `MemoryError` and confirming J-07's substance in the LLM lane's post-restart run. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-28.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-28-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-28-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-28-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-28/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
