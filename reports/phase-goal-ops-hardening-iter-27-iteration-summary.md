# Iteration Summary — goal-ops-hardening-iter-27

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-27
**Iteration:** 27

## In plain words

**What you can do now:** You can browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. You can back-fill any historical date range and get an honest explanation when there's nothing new to fetch. The app's status badge stays truthful through startup, updates, or a crash, and a live panel shows whenever background number-crunching is happening plus what happened last time. Heavy calculations are pre-computed rather than made while you wait, and the Backtest page tells you whether its numbers are fresh, a labeled still-good version, or not ready yet — and it can no longer crash when two requests for the same old date collide. The Data Manager page's coverage panel now also says plainly when its figures are a real, slightly older reading instead of quietly looking empty.

**What changed this time:** Two rare glitches found during last round's testing are now fixed. Opening the Backtest page for the same old, never-checked date from two places at once used to sometimes show a server error — that can't happen anymore. The Data Manager page used to sometimes show a blank-looking, all-zero dataset even though years of real data were stored — it now shows the real numbers with a plain note explaining they're a moment behind. While double-checking the fix, the team also caught and corrected a subtler bug of its own before it ever reached anyone (an early version could have shown the wrong count of newly added records). The team's own automatic browser double-check of these two fixes didn't finish this round — an outside usage limit cut it short — so a full independent recheck is planned for next round before this work is called fully verified.

**What's next:** Next we'll re-run the browser checks that got cut short for these two fixes, tidy up one stale test script, and stop a separate page (Evidence) from occasionally running out of memory.

## Headline

Backtest page no longer crashes under a race

## Direction

**Signal:** holding
**Why:** Iter-27 closed both of iter-26's ESCALATE-flagged anti-goal findings (the concurrent `/backtest` race, AG-8, and the stale `/data` coverage panel, AG-3) with reviewed and audited code fixes — the audit itself caught and fixed an in-audit fabrication defect (B1) before sign-off. But the browser-QA agent was killed by an account usage limit before it produced any evidence for this iteration's own three target journeys (J-05, J-07, J-08), so the evaluator scored them `unknown` rather than `passing`, and phase-closure returned CLOSURE-FAIL on exactly that gap. J-06 downgraded to `partial` on a stale, cross-session golden-script assertion unrelated to this diff. No regression and no newly-passing journey this round, so direction holds rather than advances.

**Trend (last 4 iters):**
- Newly passing this iter: none
- Newly passing in last 4 iters total: J-09 (iter-25)
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: 3, all minor — iter-26: AG-8 (concurrent `/backtest` 500) + AG-3 (stale `/data` coverage showing zeros), both since resolved this iteration; iter-27: AG-8 (unhandled `MemoryError` on `GET /api/evidence`), unresolved
- Iters with no journey state change: 1 of last 4 (iter-26)

**Latest evaluator reasoning:** This iteration fixed the two problems the last round flagged, and the code fixes look right. But the browser check that was supposed to prove them was cut off part-way by an account usage limit. So the three journeys this iteration exists to fix — J-05 "Aggregates are precomputed at ingest", J-07 "Heavy aggregates never take the service down", and J-08 "Backtest evidence serves from storage only" — have no test result at all this round. They are marked "not known" rather than pass or fail. Five other journeys were replayed; four passed, and the one that reported a failure (J-06 "Pages load only what they need") failed on a stale line in its own test script, not on anything the product does.

## What was done

- Fixed the Backtest-page race (AG-8): concurrent requests for the same never-scanned historical date no longer occasionally return a server error; verified with new unit tests plus a live two-request reproduction.
- Fixed the Data Manager coverage panel's honesty (AG-3): it now serves a `coverage_status` of "current" / "stale" / "not_yet_computed" and shows real prior figures with a calm "as of a prior scan" note instead of a misleading all-zero display.
- Auditor found and fixed an in-audit defect (B1): the collision-tolerant rollback could fabricate a "rows inserted" count; added a regression test, bringing the combined backend suite to 201 passing tests.
- Corrected a mislabeled boot timestamp in `reports/perf-budgets.md`'s Iteration 26 section.
- Review PASS, audit PASS_WITH_GAPS, coherence PASS — no scope creep, no anti-goal introduced by the diff itself.
- Re-verified J-01, J-03, J-04, J-09 passing via deterministic golden replay this iteration.
- Browser QA verified 0 of this iteration's 3 target journeys — J-05 "Aggregates are precomputed at ingest", J-07 "Heavy aggregates never take the service down", J-08 "Backtest evidence serves from storage only" — the QA agent was killed mid-run by an account usage limit before producing any row for them.

## What's left

- Journey J-05 "Aggregates are precomputed at ingest, never on the fly" — status unknown; no browser-QA evidence collected this iteration, only developer self-verification.
- Journey J-07 "Heavy aggregates never take the service down" — status unknown; the concurrent-race browser check (UT-06) never ran.
- Journey J-08 "Backtest evidence serves from storage only" — status unknown; none of its own steps were exercised this iteration.
- Journey J-06 "Pages load only what they need" — status partial; its replay failed on a stale, cross-session shared test artifact unrelated to this iteration's diff, not a product break.
- Closure blocker: phase-closure-auditor returned CLOSURE-FAIL because Definition-of-Done bullet 1 (browser-QA pass for J-05/J-07/J-08) is unmet.
- New anti-goal finding (AG-8, minor, unresolved): two unhandled `MemoryError` exceptions escaped to uvicorn on `GET /api/evidence`, rooted in an unbounded in-RAM dict in `research.py` — needs a bound plus a graceful degraded response.
- Carried, non-blocking: audit finding B2 (`_backfill`'s cross-call rollback residual) needs its own scoped follow-up (SAVEPOINT or per-run commits).
- Carried, non-blocking: `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches need retargeting before removing dangling imports at `backtest.py:75` / `mcp/tools.py:38`.

## Next step

Run one more round at full depth, no new features. Priority order: (1) re-run the browser checks for J-05, J-07 and J-08 — the only thing blocking closure — covering the stale-disclosure and concurrent-race test cases plus the regression cases; (2) fix the J-06 golden script, not the product (drop the incidental "DEGRADED" expectation and scope the drift-report path per goal-mode session); (3) bound `research.py`'s in-memory accumulation on `/api/evidence` and give it a calm degraded state instead of a crash, planned by the decomposer, not patched opportunistically; (4) for the owner, not urgent: decide whether the 12-24 minute historical `/backtest` latencies observed this round change the open cold-load budget question. What should happen next: approve one more round whose main job is simply re-running the browser checks that were cut short, fixing one stale test script line, and stopping the Evidence page from crashing.

## Assumptions made

- iter-27 · goal-evaluator — Ambiguity: whether a `MemoryError`-driven 500 on `/api/evidence`, surfacing on pre-existing untouched code while the host was under the pipeline's own test load, counts as critical or minor under AG-8's "exhaust a service's memory" clause. We chose: minor — service never went down, zero product code in this diff, every unblock path agent-tractable — verdict CONTINUE, not a REGRESSION halt. Reversible: yes
- iter-27 · goal-evaluator — Ambiguity: whether developer self-verification (a real concurrent-curl race, a real screenshot of the new label) can stand in for the browser-QA pass the DoD names, given the browser-QA lane was killed mid-run by a quota. We chose: scored J-05/J-07/J-08 `unknown`, not `passing`, and blocked GOAL_ACHIEVED on the missing evidence rather than crediting the developer's own capture. Reversible: yes
- iter-27 · goal-decomposer — Ambiguity: whether the AG-3 fix should recompute coverage live on the request path (option a) or serve a labeled stale prior snapshot (option b), since goal.md doesn't say which remedy is compliant with the compute-at-ingest principle. We chose: option (b), a stale-row fallback + honest `coverage_status` label, never a request-path recompute. Reversible: yes
- iter-26 · goal-evaluator — Ambiguity: whether a server-side 500 on `/api/backtest` (AG-8) and an all-zero `/data` coverage panel for a populated database (AG-3) — neither introduced by that diff, neither witnessed reaching the user as a broken page — count as critical or minor. We chose: minor for both, so the verdict was ESCALATE rather than a REGRESSION halt. Reversible: yes
- iter-26 · goal-decomposer — Ambiguity: whether J-09's "shows a failed background compute" Acceptance clause requires an actual witnessed live failure capture, or whether a deterministic code-level round-trip test is sufficient citable evidence (the only way to trigger a genuine failure reproduces an unsafe memory-pressure pattern already tracked as owner-optional). We chose: a backend test plus a frontend rendering unit test, never re-triggering the unsafe live failure. Reversible: yes
- iter-25 · goal-evaluator — Ambiguity: whether a required-still-passing journey (J-07) that failed its deterministic replay because the host was under the test harness's own memory pressure counts as verified. We chose: accepted the overturn and scored J-07 `passing`, after tracing the cause to a logged `MemoryError` and confirming J-07's substance in the LLM lane's post-restart run. Reversible: yes
- iter-25 · goal-evaluator — Ambiguity: which of two disagreeing `/api/health` latency series (developer's 10-sample max 0.127788s vs QA's max 0.094604s) binds for J-09's unchanged `<= 0.1s` budget clause. We chose: scored the clause met at the same bar this session already applied to J-06/J-07, since the tightness is pre-existing and the diff adds zero DB work; routed to the owner as open question B5. Reversible: yes
- iter-24 · goal-evaluator — Ambiguity: whether J-09's Acceptance walkthrough clause (viewable via the session-live demo) is binding on the journey even though the iteration spec never scoped it into IN SCOPE or DoD. We chose: scored J-09 `partial`, treating the clause as binding on the journey regardless of iteration scope, since this session had already adjudicated the same clause twice before. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-27-what-to-click.md`:

1. Open `http://localhost:3255/data` in your browser
2. Look directly below the words "Dataset coverage" (above the grid of small figure boxes)
3. Click "Backtest" in the left sidebar
4. Click the date button near the top of the page (it shows "Latest" with a small calendar icon and a down-arrow), then click any date shown in the calendar that appears
5. Press F5 (or Cmd+R) to refresh the page

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-27.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-27-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-27-review.md |
| Browser QA | FAIL | reports/phase-goal-ops-hardening-iter-27-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-27-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-27-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-27-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-27-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-27-ui-test-plan.md |
| UX regression | UX-REGRESSION-WARN | reports/phase-goal-ops-hardening-iter-27-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-27-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-27-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-ops-hardening-iter-27-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-27/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
