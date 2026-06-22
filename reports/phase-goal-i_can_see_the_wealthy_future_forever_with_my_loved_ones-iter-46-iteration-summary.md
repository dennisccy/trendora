# Iteration Summary — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-46

**Verdict:** REGRESSION
**Iteration type:** goal-lean
**Date:** 2026-06-22
**Iteration:** 46

## In plain words

**What you can do now:** See a live dashboard with a single de-duplicated market chart and a severity-velocity line that shows whether market stress is worsening or easing; step to any past snapshot date and have every surface update instantly; view a stock leaderboard showing only stocks that were tradable on any selected past date; open any stock for a plain-language score breakdown with colour-graded forward-return and max-drawdown columns; save stocks to a watchlist; check the Data Manager for a membership-growth timeline with Year/Month filters and pagination plus a per-date coverage diagnostic; explore the Research section as a hub of seven individually-loaded labs — including a Severity-velocity × Regime study with an honest forward-return matrix and verbatim caveats. Note: two Research labs (the Factor Lab and the Setup & Pattern event study) are currently unavailable due to a memory issue that is being fixed.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. This was a verify-only pass with no code changes. During testing, a pre-existing memory issue was uncovered: the Factor Lab and the Setup & Pattern event study try to load millions of stored data rows all at once, which exceeds available memory on the current machine. These two labs now show an error instead of their results. The root cause has been identified and a targeted fix is queued for next time.

**What's next:** Next we will fix the memory issue in the Factor Lab and event study by loading historical data in smaller, bounded chunks rather than all at once, restoring those two labs to full working order.

## Headline

Verify-only lean re-verification surfaces a standing MemoryError on the heavy research labs (J-25/J-26/J-29 regressed); no code changed.

## Direction

**Signal:** regressing
**Why:** Three previously-passing Must-have journeys — Factor Lab decile/rank-IC (J-25), Factor Lab multi-factor composite (J-26), and Setup & Pattern event study (J-29) — are now user-observably failing with a MemoryError on the live 3.3 GB / 3.08M-row database. The root cause is an unbounded `.all()` materialization of ~3M ORM objects originating in iter-20, exposed by the J-85 data rebuild and a host RAM reduction, not by any code change this iteration. J-104's "labs load reliably" acceptance is also now only partially met (5/7 labs serve; event-study and factor-lab do not).

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-99 (iter-41), J-100 (iter-43), J-101 (iter-44), J-102 (iter-44), J-103 (iter-45), J-104 (iter-45)
- Regressions in last 5 iters: J-25, J-26, J-29 regressed in iter-46
- Anti-goal violations in last 5 iters: none (0)
- Iters with no journey state change: 1 of last 5 (iter-46 had no newly-passing journeys; iter-43 closed GOAL_ACHIEVED; iters 44/45 added passing journeys)

**Latest evaluator reasoning:** "This verify-only lean re-verification pass (zero source diff, COHERENCE-PASS, review PASS_WITH_NOTES) surfaced a GENUINE standing defect that I independently reproduced: the two heavy research labs `/api/research/event-study` (J-29) and `/api/research/factor-lab` (J-25/J-26) raise `MemoryError` on the live 3.3 GB / 3,081,454-row `forward_returns` DB because `_event_study_members_by_horizon` (apps/backend/app/engine/research.py:823-828) materializes the entire `select(ForwardReturn).where(horizon.in_(horizons)).all()` into ORM objects. These three journeys plus J-104's "labs load reliably without error" acceptance were `passing` in prior iterations and are now user-observably broken on the live system, so per the REGRESSION rule the loop halts for human review."

## What was done

- Executed a verify-only lean re-verification pass — confirmed zero source diff against HEAD across all `apps/`, `scripts/`, and source files
- Brought up a fresh backend (:8835), waited for health/ready, confirmed warm-up completed before any fetch
- Verified J-103 (Severity-velocity × Regime study): 3×3 matrix renders, As-of N shrinks 1147→301 at `?as_of=2022-12-31`, count-coherent N= drill-down confirmed — closes the iter-45 false-negative
- Confirmed 5 of 7 relocated `/research/*` labs (regime-setup-pattern, recovery-turn-edge, factor-combination, severity-velocity, downtrend-opportunity) return HTTP 200 with real figures
- Re-verified J-06 (score consistency), J-07 (Risk-Off gate, CRITICAL), and J-18 (one date selector, CRITICAL) on live evidence
- Independently reproduced the MemoryError: the `_event_study_members_by_horizon` all-history fetch materialized 3,081,454 ORM objects at peak RSS 5,466 MiB in 172 s on the live DB
- Identified root cause: unbounded `.all()` from iter-20 (commit 6733c1d), byte-identical through GOAL_ACHIEVED states, exposed by data growth (~3.08M rows) and host RAM dropping from ~18 GiB to ~10 GiB

## What's left

- Journey J-25 (Factor Lab — decile sort and rank-IC) regressed — `_event_study_members_by_horizon` MemoryError on 3.08M-row live DB
- Journey J-26 (Factor Lab — multi-factor composite) regressed — same MemoryError path
- Journey J-29 (Setup & Pattern lab — event study) regressed — same MemoryError path
- Journey J-104 (Research labs load reliably) partial — 5/7 labs OK; event-study and factor-lab reliability acceptance unmet
- Full backend suite `0 failed, EXIT 0` not yet confirmed flushed (nohup-async launched; not blocked on per iter-11/29/37 lesson)
- J-22/J-23/J-24 remain blocked-NA (data-walled, non-vetoing)

## Next step

iter-47 FULL (resume with `--acknowledge-regression`) — bound the all-history `ForwardReturn` materialization so event-study (J-29) and factor-lab (J-25/J-26) load without `MemoryError` on the 3.08M-row live DB, restoring J-104's "labs load reliably" acceptance. Options: (a) `session.exec(...).yield_per(N)` / server-side streaming so peak memory is bounded; (b) push the per-(subject, horizon) grouping into the cached `EventStudyCache` aggregate so the read path never materializes the full table; (c) project to lightweight columns/tuples (not full ORM rows) for the join. Whichever is chosen, the served per-horizon member lists and every downstream figure MUST stay byte-identical (assert with a seeded test; re-run `test_research.py`/`test_samples.py` count-coherence — J-29/J-63/J-51/J-65). Apply the same bounding to the warm-up `backfill_forward_returns` step (warmup.py:155 also MemoryError'd — non-fatal). Then LIVE re-verify on a quiet, warmed, single-fetch-at-a-time backend (Playwright fallback planned up front; md5sum the dir first; reject "Loading…"/"Backend unavailable"/skeleton frames): event-study (J-29), factor-lab (J-25/J-26), each rendering REAL figures + a working N= drill-down; plus the light labs (J-77/J-91/J-90) and J-103 As-of mode. Gate GOAL_ACHIEVED candidacy on the FLUSHED full-suite `0 failed, EXIT 0` (nohup-async; never block the evaluator; re-run any isolated test_warmup.py/test_watchlist_persistence.py E/F before attributing). Do NOT re-trigger the J-85 `kind:rebuild`. J-22/J-23/J-24 stay blocked-NA (non-vetoing per goal.md:105-108).

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-46.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-46-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-46-review.md |
| Browser QA | PASS | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-46-ui-test-results.md |
| Goal evaluation | REGRESSION | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/iter-46/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/journey-history.json |
