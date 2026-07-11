# Iteration Summary — goal-mcp-loop-iter-27

**Verdict:** PASS
**Iteration type:** goal-full
**Date:** 2026-07-12
**Iteration:** 27

## In plain words

**What you can do now:** Browse a leaderboard of hundreds of companies with an honest "proven" or "not yet proven" status on every score, open the full evidence ledger to see every trading idea tested so far (all currently read "FAIL" while the deeper thirty-year history is re-proven), and follow the market-regime panel through to the evidence backing it. View up to thirty years of price history for any stock in a recent or full view, browse the company list as it looked on any past date, see three decades of major-index history plus a volatility gauge and a rate indicator on the dashboard chart (each labeled by its source), and check the Data Manager page's color-coded calendar of data availability across the whole company list.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round, but a real fix landed: the "Rebuild snapshots" job on the Data Manager page, the heaviest data-refresh job in the app, used to crash the whole backend if you ran it twice in a row. That's now fixed and proven live — the team watched it succeed three times back to back without the app going dark.

**What's next:** Next, work turns back to re-proving the trading ideas on the newer, deeper price history so some can earn a "proven" badge again — that only happens once a candidate honestly clears the statistical bar, so it may take another round or two before a new one shows up.

## Headline

Crash-proof repeated full-universe rebuilds — the backend no longer OOMs on a second Rebuild run

## Direction

**Signal:** improving
**Why:** iter-27 resolved the unresolved critical anti-goal #8 violation that halted iter-26: after a first windowing pass proved insufficient, a second allocator-hardening pass (capped glibc arenas + `gc.collect()`/`malloc_trim(0)` between jobs) was live-verified by the canonical browser-qa lane across three consecutive full-universe rebuilds with no crash and 1,116 MB margin under the 6,144 MB ceiling. Target journey J-16 flips from failing to passing and all 8 required-still-passing journeys (J-01/J-03/J-04/J-05/J-10/J-12/J-13/J-15) were re-driven live PASS — the first forward step since the iter-24/26 regression cycle. J-02/J-06/J-07/J-08/J-09 remain sanctioned-partial, unaffected by this pass.

**Trend (last 5 iters):**
- Newly passing this iter: J-16
- Newly passing in last 5 iters total: J-14 (iter-23), J-13 (iter-25), J-15 (iter-25), J-16 (iter-27)
- Regressions in last 5 iters: J-13 (iter-24, recovered iter-25)
- Anti-goal violations in last 5 iters: 2 critical — anti-goal #8 (iter-24, resolved iter-25) and anti-goal #8 again (iter-26, resolved iter-27)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The live browser lane reproduced a MemoryError (VSZ exhaustion at the ulimit -v ceiling) that took the entire backend down during the 322-date × 541-member "Rebuild snapshots" job — the exact job class J-16 is about. This was an UNRESOLVED critical anti-goal #8 violation, scored REGRESSION at iter-26; iter-27 is the dedicated fix-verification pass that closes it (the goal-evaluator has not yet scored iter-27 itself — this summary sources the outcome from the review/QA/browser-QA/UX-regression/audit/closure gate reports instead).

## What was done

- Fixed the "Rebuild snapshots" memory crash: routed `regime.py`/`scoring.py`'s price-history reads through a new bounded accessor (`bars_asof_window`) instead of materializing full history per symbol/date (first-pass windowing).
- Added allocator hardening after the first pass failed a live re-test: capped glibc memory arenas (`MALLOC_ARENA_MAX=2`) and added `gc.collect()`/`malloc_trim(0)` cleanup after each backfill job, eliminating cross-job memory retention.
- Extended the byte-identity test suite (`test_scoring_window.py`) with windowed-vs-unwindowed equivalence tests for `score_regime` and the new `bars_asof_window` accessor — 4/4 green, plus 12/12 `test_bar_cache.py`, 5/5 `test_forward_testing.py` cache-awareness, 111/111 config tests.
- Measured the full 322-date × 590-symbol universe rebuild live, twice back-to-back, under the real 6,144 MB memory ceiling: peak memory fell ~926 MB per run and stopped growing between consecutive runs (recorded in `reports/perf-budgets.md` Items G & H).
- Verified 1 target journey (J-16) passes browser QA — three consecutive live full-universe rebuilds all reached "ok" with no crash, plus all 8 required-still-passing journeys (J-01/J-03/J-04/J-05/J-10/J-12/J-13/J-15) re-verified live PASS.

## What's left

- Journeys J-02/J-06/J-07/J-08/J-09 remain sanctioned-partial — the 30-year ledgers stay all-FAIL and no staging winner currently clears the canonical Bonferroni divisor-8 bar (separate priority-2 evidence work).
- Cold-start-first `/data` repro (UT-01) and the backend-down "Backend unavailable" contained-card repro (UT-13/UT-14) were SKIPPED by the canonical browser-qa lane this round (permission denial to stop/restart the coordinator-managed backend) — covered at the HTTP level but not re-exercised live by the canonical lane.
- `IndicatorsCfg._validate`'s guard omits `breadth_short_ma`/`breadth_long_ma` — latent, byte-safe today only because `breadth_long_ma` (200) coincides with `max(ma_periods)` (200).
- Two pre-existing `/data` UX affordance gaps remain: no guardrail against clicking "Rebuild" twice back-to-back, and no client-side readiness-poll timeout so a wedged backend would show a perpetual loading skeleton instead of the "Backend unavailable" card.
- `server.malloc_arena_max` has no dedicated unit test (mirrors the equally-untested sibling `memory_cap_mb`).
- The full pytest suite (~10-11h at the 30-year basis) was not run this iteration — targeted tests only, per coordinator instruction.

## Next step

Proceed — iter-27 closes PASS_WITH_GAPS; the unresolved critical anti-goal #8 that blocked iter-26 is resolved and live-verified, with all 8 required-still-passing journeys re-verified live PASS. GOAL_ACHIEVED remains out of reach afterward: J-02/J-06/J-07/J-08/J-09 stay sanctioned-partial (no staging winner currently clears the canonical Bonferroni divisor-8 bar) — the separate priority-2 evidence work. Carry forward, non-blocking: close the `IndicatorsCfg._validate` guard gap (`breadth_short_ma`/`breadth_long_ma`) the next time config is touched; grant the browser-qa agent backend-lifecycle permission (or have the coordinator perform the stop/cold-start) so the cold-start and backend-down repros (UT-01/13/14) are re-driven by the canonical lane; optionally add a `/data` re-rebuild guardrail and a client-side readiness-poll timeout.

## Assumptions made

none recorded

## Quick verify

From `reports/phase-goal-mcp-loop-iter-27-what-to-click.md`:

1. Open `http://localhost:3255/data` in your browser
2. Click the "Rebuild snapshots for current universe" button, then click "Rebuild snapshots" in the confirmation dialog that appears
3. Watch that counter every 1-2 minutes without closing the tab, all the way through to completion
4. Immediately after run 1 reaches "ok" — in the same browser tab, with the backend NOT restarted — click "Rebuild snapshots for current universe" again and confirm a second run
5. Once run 2 also reaches "ok", open a new tab and go to `http://localhost:3255/stocks`

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-27.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-27-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-mcp-loop-iter-27-review.md |
| Browser QA | PASS | reports/phase-goal-mcp-loop-iter-27-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-27-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-27-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-27-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-27-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-27-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-mcp-loop-iter-27-ux-regression.md |
| QA | PASS_WITH_NOTES | reports/qa/goal-mcp-loop-iter-27-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-mcp-loop-iter-27-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-mcp-loop-iter-27-closure-verdict.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
