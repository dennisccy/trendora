# Iteration Summary — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-06-22
**Iteration:** 47

## In plain words

**What you can do now:** See a live dashboard with a single market chart, step to any past date and have every screen update instantly, read a severity-velocity line showing whether market stress is worsening or easing, hover the chart for the regime label and score, view a stock leaderboard showing only stocks tradable on any selected past date, open any stock for a score breakdown with forward-return and max-drawdown columns, save stocks to a watchlist, check the Data Manager for a membership-growth timeline with filters and pagination, and explore six of the seven Research labs — including the Setup & Pattern event study and the multi-factor combination lab, both of which are working again after being repaired this round.

**What changed this time:** The Setup & Pattern event study and the multi-factor combination research lab are working again. Both had stopped loading last round because the research engine was trying to load the entire forward-return history (over three million rows) into memory at once on a database that has grown too large for that approach. This round, the code was rewritten to read those rows in small, efficient streams instead, so the labs can now serve real data without running out of memory. One lab — the Factor Lab's decile and rank analysis — is still broken for the same underlying reason on a different section of code that was not yet fixed; that fix comes next.

**What's next:** The Factor Lab's decile sort and rank analysis will be fixed by applying the same streaming approach to the remaining unstreamed section of code, restoring full lab reliability.

## Headline

Streamed 7 unbounded ForwardReturn reads in research engine, restoring event-study (J-29) and factor-combination (J-26); J-25 (Factor Lab decile) still OOMs at research.py:216 (ScannerResult side unstreamed).

## Direction

**Signal:** improving

**Why:** This iteration net-restored two of the three journeys that regressed in iter-46 (J-29 and J-26 flip from regressed back to passing on live rendered evidence). No prior-passing journey went from passing to failing this iter. The remaining failure (J-25) is an incomplete fix of the same known root cause — the ScannerResult read at research.py:216 was not streamed — with the precise next step identified. The trend over the last five iterations is positive: four iters moved journeys forward and only one (iter-46) introduced a regression, which is now being unwound.

**Trend (last 5 iters):**
- Newly passing this iter: J-29 (Setup & Pattern event study), J-26 (Factor Lab multi-factor composite)
- Newly passing in last 5 iters total: J-103 (iter-45), J-104 (iter-45), J-29 (iter-47), J-26 (iter-47)
- Regressions in last 5 iters: iter-46 — J-25, J-26, J-29 (all three from MemoryError on grown DB); iter-47 closes J-26 and J-29, J-25 still open
- Anti-goal violations in last 5 iters: none (the lone ever-recorded iter-20 minor magic-number stays resolved since iter-21)
- Iters with no journey state change: 1 of last 5 (iter-46 was a verify-only pass with zero source diff that exposed the regression; it moved journey status)

**Latest evaluator reasoning:** "The iter-47 J-105 fix is real but INCOMPLETE. I independently confirmed both halves: (1) the ForwardReturn reads ARE streamed — research.py:211 is `yield_per(batch)` and the two event-study builders were reordered (subject-matching ScannerResults streamed first, FR scan pruned to needed runs), and the live evidence restores J-29 and J-26; (2) the fix LEFT the ScannerResult side unstreamed — research.py:216 in `_factor_observations` is still `select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr)).all()` over ~609K rows, and because factor-lab is UNCACHED it recomputes every request and OOMs. NOT REGRESSION: J-25/J-26/J-29 were already `regressed` (iter-46, acknowledged) — no prior-PASSING Must-have went passing→failing this iter, and iter-47 NET-RESTORED two of the three. Progress made (2 journeys restored, 0 newly broken), tractable next step, COHERENCE-PASS → CONTINUE."

## What was done

- Replaced all 7 unbounded `select(ForwardReturn)…all()` ORM reads in `research.py` with column-projected, `yield_per`-streamed, cohort-bounded reads across all heavy-lab builders (`_factor_observations`, `_combination_observations`, `_event_study_members`, `_event_study_members_by_horizon`, `_regime_setup_pattern_observations`, `_recovery_turn_observation_set`, `_severity_velocity_observation_set`)
- Reordered the two event-study builders so subject-matching `ScannerResult` rows are streamed first, then the `ForwardReturn` scan is pruned to only the needed run IDs — reducing peak memory to O(subject matches) instead of O(table)
- Replaced the warm-up idempotency full-table scan in `forward_testing.py` `_backfill` with a new `_streamed_existing_keys` helper that streams a column-projected `(run_id, symbol, horizon)` key scan
- Added `research.read_batch_size` config key (required, boot-validated >= 1, default 2000) as the single source of the `yield_per` batch size — no inline batch literal in calculation code
- Added `test_research_streaming.py` (32 tests: deep-equality / chunk-independence of streamed builders vs per-horizon reference under `read_batch_size=1`/huge, all-history/as-of, pooled/episodes, zero-N cohort) and `test_forward_testing_streaming.py` (5 tests); added `read_batch_size` to all inline test config fixtures across 4 test files
- Verified J-29 (event-study) and J-26 (factor-combination) restored on live 3.3 GB DB via browser-QA 14/19 PASS; J-77, J-91, J-90, J-103, J-51, J-63, J-65, J-06, J-13, J-18, J-07, J-72, J-32 re-verified passing

## What's left

- Journey J-25 (Factor Lab — decile sort and rank-IC per factor) failing — `_factor_observations` (research.py:216) still has an unstreamed `select(ScannerResult)…all()` over ~609K rows; factor-lab is uncached so it OOMs on every request
- Journey J-104 (research-labs reliability) partial — 5/7 labs reliable; Factor Lab still OOMs so the "labs load reliably without error" acceptance is unmet
- Journey J-105 (bounded/streamed read path) partial — ForwardReturn side complete and verified; ScannerResult side at research.py:216 (and latent cold-miss at research.py:421) not yet streamed
- Flushed full-suite `0 failed, EXIT 0` not yet confirmed (suite launched nohup-async; not a GOAL_ACHIEVED candidate this iter regardless)
- Journey J-22 (expanded universe ~500 names) blocked-NA — data-walled, non-vetoing per goal.md:105-108
- Journey J-23 (multi-timeframe bars) blocked-NA — data-walled, non-vetoing
- Journey J-24 (timeframe selector) blocked-NA — data-walled, non-vetoing

## Next step

iter-48 FULL — finish J-105 by streaming/column-projecting the ScannerResult reads in the UNPRUNED observation builders, **factor-lab (J-25) first**: replace research.py:216 (`_factor_observations`) `session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()` with a column-projected `yield_per`-streamed read (project only the ticker + per-factor value columns the decile/rank-IC study reads), keeping every figure byte-identical. This is the genuine OOM site (live backend log: `MemoryError` at research.py:216, ~609K ScannerResult rows; factor-lab is UNCACHED so it recomputes every request). Also stream `_combination_observations` (research.py:421) — the same unstreamed `select(ScannerResult)…all()` is a latent cold-miss OOM, currently masked only by the J-104 EventStudyCache hit. Required-still-passing for iter-48: J-29/J-26/J-77/J-91/J-103 (must STAY passing — re-render on a quiet, warmed, single-fetch-at-a-time backend), J-51/J-63/J-65 (factor-lab N= drill-down now testable once J-25 serves), J-06/J-18 (CRITICAL)/J-07 (CRITICAL), J-72/J-32 (byte-identity of the streamed builders). Suite-gate: pump nohup-async; gate the eventual GOAL_ACHIEVED candidacy on the FLUSHED `0 failed, EXIT 0` line — never block the evaluator on the in-flight suite. Evidence-hygiene: PLAN the Playwright fallback up front; md5sum the dir FIRST; NEVER run the full backend suite concurrently with the heavy-lab probes; fetch one heavy lab at a time; for the factor-lab cold compute over ~598K rows allow ~50-60s before the first cache hit. After J-25 flips to passing with byte-identical figures + a flushed-GREEN suite + COHERENCE-PASS + zero regression, the next evaluation is a sound GOAL_ACHIEVED candidate (J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing per goal.md:105-108).

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-dev.md |
| Review | PASS | reports/reviews/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-review.md |
| Browser QA | FAIL | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/iter-47/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/journey-history.json |
