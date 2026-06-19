# Iteration Summary — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35

**Verdict:** REGRESSION
**Iteration type:** goal-lean
**Date:** 2026-06-19
**Iteration:** 35

## In plain words

**What you can do now:** See a live dashboard with a regime score, Market Phase & Severity panel, phase history timeline, and dated downtrend episodes with a fenced retrospective sub-view. Explore a Recovery-Turn Edge study and a Downtrend Opportunity study on the Research page. Step to any past snapshot date and every surface re-points instantly. Browse the stocks leaderboard — which now shows the honest point-in-time universe (empty before October 2021, growing to roughly 544 stocks by the latest date). Open any stock for an explainable score breakdown with a regime-banded chart and five forward-return columns each paired with a colour-graded drawdown figure. Sort, filter, and search every leaderboard by sector, theme, or pattern. Click any sample count to see the exact stored observations. Save stocks to a watchlist. Manage imports with live progress tracking. Use the Data Manager to see per-date admitted and excluded stock counts with reasons, macro feed panel, and confirm-gated controls.

**What changed this time:** The stocks leaderboard now correctly shows different numbers of stocks depending on the date you've selected — empty before October 2021, and growing to roughly 544 stocks by today. This fixes the old behaviour where every date always showed the same 122 stocks regardless of when you looked. However, this fix also caused the Data Manager page (the one with the membership timeline and coverage breakdown) to stop loading — the page now hangs because the underlying computation has to work through all 1,369 historical dates at once without any shortcut. The coverage diagnostic that was working before is now broken.

**What's next:** Next we'll make the Data Manager page load quickly again by caching or pre-computing the heavy date-by-date calculation, then re-confirm both the timeline chart and the coverage diagnostic render correctly in the browser.

## Headline

Verify-only iter: J-85 rebuild fixed sliding universe on /stocks (J-93 passes), but exposed uncached 1369-date /api/data hang — J-94 regressed.

## Direction

**Signal:** regressing
**Why:** J-93 (dynamic universe slides on /stocks) flipped from failing to passing on genuine differential live evidence — a real gain. But the same rebuild that fixed J-93 made `GET /api/data` hang indefinitely (>300 s) because `_membership_timeline` now loops all 1369 snapshot dates calling `universe_resolver.resolve_with_reasons()` with no cache. J-94 (per-date coverage diagnostic), which rendered fully in iter-34, can no longer hydrate in the browser — a previously-passing Must-have is now broken. The loop halts for human review; resume with `--acknowledge-regression` after the read-path fix is applied in iter-36.

**Trend (last 5 iters):**
- Newly passing this iter: J-93
- Newly passing in last 5 iters total: J-94 (iter-34), J-95 (iter-34), J-89 (iter-31), J-90 (iter-31), J-93 (iter-35)
- Regressions in last 5 iters: J-94 regressed (iter-35)
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The out-of-band J-85 rebuild (job eb48cbf1, 1369/1369 dates; NOT re-triggered this iteration — the source diff is empty) genuinely fixed J-93: the persisted ScannerResult snapshots now ARE the per-date dynamic membership and the universe slides 0→494→504→544 on /stocks, proven by three byte-distinct, evaluator-viewed frames. But the same rebuild regressed the /data page: the J-96 membership-timeline computation makes GET /api/data hang >300 s, so the /data page that rendered J-94 fully in iter-34 no longer hydrates at all. A previously-passing Must-have (J-94) is now broken in the browser — the loop halts for human review.

## What was done

- Verified (read-only, source diff empty) that the completed J-85 out-of-band rebuild populated genuine per-date dynamic membership into stored ScannerResult snapshots: 0 rows at 2021-01-04, 504 rows at 2022-02-01, 544 rows at 2026-06-16
- Confirmed committed price seed untouched: `daily_prices` bar count 793,218 before and after rebuild (bars_before == bars_after invariant)
- Browser-QA confirmed J-93 via three byte-distinct /stocks frames (md5 e6595c7b / 8d43b252 / dfd985fd) — row counts differ: 0, 504, 544
- Re-verified J-06 single-source reconciliation: resolver-direct 544 == served /api/stocks 544; NVDA detail scores match leaderboard at 2026-06-16
- Re-verified J-07 (Risk-Off → 0 Actionable CRITICAL): 195 Risk-off snapshot dates all return 0 Actionable
- Re-verified J-18 CRITICAL (0 input[type=date] on /backtest); J-87/J-88 dashboard panels unperturbed at multiple dates
- Diagnosed J-94/J-96 root cause: `_membership_timeline` (data_manager.py:469-528) loops all 1369 snapshot dates calling `universe_resolver.resolve_with_reasons()` per date with no cache — intractable post-rebuild, causing GET /api/data to hang >300 s; all /data frames are un-hydrated skeletons

## What's left

- Journey J-94 (Min-history sufficiency gate / per-date coverage diagnostic) — REGRESSED: /data page hangs, diagnostic no longer renders in browser
- Journey J-96 (Membership timeline + survivorship/coverage labels) — PARTIAL: data correct DB-direct (rising step 0→544, entries/exits populated), but /data page hangs so rendered timeline is not visible
- Fix required: cache or precompute `universe_resolver.resolve_with_reasons()` per (date,cfg) and/or warm-up the membership_timeline during background daemon startup, and/or paginate the timeline, so GET /api/data responds in bounded time without changing any served value
- Full backend suite EXIT 0 still needed — nohup-async suite was in flight at eval time, not yet flushed
- J-22 / J-23 / J-24 remain honestly blocked-NA (data-walled, non-vetoing)
- J-95 real backward-history fetch and true index-constituent feed remain honestly blocked-NA (data-walled)

## Next step

iter-36 **FULL** — make `GET /api/data` responsive WITHOUT changing any served value:
- Cache `universe_resolver.resolve_with_reasons()` per `(date, cfg)` and/or precompute the J-96 `membership_timeline` during the background warm-up daemon (the J-40/J-41 serve-fast lifespan precedent) and/or paginate the timeline so the first `/data` render is bounded.
- Assert **byte-identity** of the served coverage block before/after the perf fix (no value drift).
- LIVE re-verify **J-94** (the universe-resolution diagnostic renders again) and **J-96** (the rising step function from ~2021-10-18 with populated Entries/Exits + the three honesty labels scrolled into the viewport and VIEWED — md5sum the dir first; reject any skeleton frame).
- Re-smoke the co-located `/data` journeys **J-36/J-37/J-39/J-85**, re-confirm **J-93** still slides on `/stocks` (the fast `/api/stocks` snapshot path, unaffected), and the CRITICAL **J-18/J-07**.
- Do **NOT** re-trigger `kind:"rebuild"` (~11 h, destructive; the data is correct).
- Gate any GOAL_ACHIEVED candidacy on the FLUSHED full-suite `0 failed, EXIT 0` line, nohup-async to the pump, never blocking the evaluator (iter-11/29/30 lesson).

After J-94 re-renders and J-96 flips to passing with COHERENCE-PASS and a GREEN suite, the next evaluation is a GOAL_ACHIEVED candidate (J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing).

## Quick verify

From `reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35-what-to-click.md`:

1. Open `http://localhost:3835/stocks` in your browser
2. Set the global as-of date to `2021-01-04`
3. Set the global as-of date to `2022-02-01`
4. Set the global as-of date back to `2026-06-16` (or latest), locate NVDA in the leaderboard and note its scores, then click NVDA to open its detail page
5. Navigate to `http://localhost:3835/data` and scroll down until the membership timeline panel is visible

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35-dev.md |
| Review | PASS | reports/reviews/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35-review.md |
| Browser QA | FAIL | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35-user-visible-changes.md |
| What to click | — | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35-what-to-click.md |
| UI surface map | — | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35-ui-surface-map.md |
| QA | PASS | reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35-qa.md |
| Goal evaluation | REGRESSION | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/iter-35/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/journey-history.json |
