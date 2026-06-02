# Iteration Summary — goal-i_can_see_the_wealthy_future_forever-iter-11

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-06-02
**Iteration:** 11

## In plain words

**What you can do now:** See the day's market at a glance and browse ranked stocks, sectors, and themes — filtering the stock list by sector, by setup, or by any of three chart patterns. Open any stock for a plain-English scorecard (the same numbers on the list and the detail page) plus the price that would prove the idea wrong, rewind the whole app to any past day with one shared date control, and read honest evidence of how past picks actually performed by stock, sector, and ranking tier. In the Research area's Factor Lab you can test whether any of eight signals really sorted future returns — raw and downside-risk-adjusted — and now whether it works in calm, choppy, or risk-off markets. You can also save a watchlist that survives a restart, grow the dataset by date or range, and look up every label in a plain-language glossary — always with honest "not enough data yet" marks instead of made-up numbers.

**What changed this time:** On the Research area's Factor Lab, you can now see whether a signal that looks useful overall actually holds up in each kind of market — calm, choppy, narrow, or risk-off. A new table breaks each signal's effectiveness down by market mood, so a factor that scores well across all history can be revealed as really only working in certain conditions. Periods with too few days to judge are honestly marked "not enough data" rather than shown as a fabricated number.

**What's next:** Next the Factor Lab will let you combine two signals at once and see whether the pair sorts future returns better than either signal alone.

## Headline

Factor Lab now splits each factor's effectiveness by market regime, raw and downside-risk-adjusted (J-27).

## Direction

**Signal:** improving
**Why:** This iter added J-27 (regime-conditioned factor effectiveness) on `/research` as a purely additive, read-only slice over `research.py` — verified passing by browser QA (11/12, 1 N/A code-verified) and 18/18 QA functional cases, with all five critical seams confirmed in source. Seven journeys remain failing: J-26/J-29/J-30/J-31 are unbuilt compute-only labs and J-22/J-23/J-24 are externally data-walled (Yahoo 429). The last three iters each moved a journey forward (J-28 iter-9, J-25 iter-10, J-27 iter-11), so direction is healthy.

**Trend (last 5 iters):**
- Newly passing this iter: J-27
- Newly passing in last 5 iters total: J-28 (iter-9), J-25 (iter-10), J-27 (iter-11)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none (the single historical minor one was resolved back in iter-1)
- Iters with no journey state change: 2 of last 5 (iter-7 STALLED, iter-8 — both externally data-walled on J-22)

**Latest evaluator reasoning:** J-27 (regime-conditioned factor effectiveness on `/research`) landed exactly as specified — a textbook-clean, purely additive read-only slice. The new "Factor effectiveness by market regime" table renders one row per configured regime label with per-regime `n`, rank-IC, top/bottom decile means, and raw + downside-risk-adjusted top-minus-bottom-decile spreads; low-sample/empty regimes show honest NA + n. All five critical seams were verified directly in source (the regime is read verbatim from `scanner_runs.regime_label` — `research.py` doesn't even import the regime engine). Not GOAL_ACHIEVED: 7 journeys remain failing.

## What was done

- Extended `_factor_observations` (`research.py`) to attach each run's stored `scanner_runs.regime_label` to its observation — read verbatim via one added `select(ScannerRun)`, SELECT-only, no regime recomputed.
- Added the read-only `_regime_effectiveness(...)` helper emitting one row per `config.regime.labels` entry: `n`, rank-IC, top/bottom decile means, and the raw + downside-risk-adjusted top-minus-bottom-decile spreads; both spreads are honest `None` (NA) when the regime is low-sample or either decile leg is null.
- Added the `by_regime` key to `compute_factor_lab` over the SAME observation pool — no new endpoint, no new query param, no nav change, no new config key, no schema/DB change.
- Added the server-driven `RegimeEffectivenessTable` panel on `/research` (below the decile table + rank-IC card); low-sample/null cells render NA + the honest `n` chip; no date control added so J-18 is preserved.
- Extended the read-only keystone test to also patch `regime.score_regime` to raise + added 5 new J-27 unit scenarios; full backend suite 384 passed / 4 skipped / 0 failed; frontend builds (14 routes, `/research` 5.79 kB).
- Verified the target journey (J-27) passes browser QA — 11/12 UI tests (1 N/A empty-state code-verified) and 18/18 QA functional cases; Σ per-regime n == n_total invariant holds (1218==1218 h5, 1217==1217 h60).

## What's left

- Journey J-26 (Factor Lab — multi-factor combination cohorts) failing — unbuilt compute-only lab; the recommended next target on the now-proven read-only seam.
- Journey J-30 (Volatility as a return driver — factor family, risk-adjusted and regime-conditioned) failing — unbuilt compute-only lab, now directly enabled by J-25 + J-27.
- Journey J-29 (Setup & Pattern research lab — event study across all snapshots) failing — unbuilt; larger lift, needs the post-snapshot daily high/low MAE/MFE excursion path extracted first.
- Journey J-31 (Find a high-return driver end-to-end — synthesis) failing — unbuilt; depends on J-29 + J-27.
- Journey J-22 (Transparent, rule-based, expanded universe ~500 names) failing — externally data-walled (Yahoo 429); auto-heals via its committed runbook only on operator confirmation of a reachable no-key feed. Do NOT autonomously retry.
- Journey J-23 (Multi-timeframe bars — intraday seed) failing — same external provider wall.
- Journey J-24 (Timeframe selector on the stock chart) failing — depends on J-23 (data-walled).
- Known limitation (honest, not a defect): with the frozen dataset, the "Strong risk-on" and "Defensive" regimes have no qualifying days, so they correctly render NA + n=0 rather than a fabricated number.

## Next step

Next iteration: full depth — target J-26 (Factor Lab — multi-factor combination cohorts). It is the smallest direct extension of the now-proven read-only seam: intersect two catalog factors' top/bottom quantile membership over the SAME `_factor_observations` pool and report the joint cohort's forward return (raw + risk-adjusted), hit-rate, and `n` against the unconditional baseline and each single-factor cohort. It reuses `compute_factor_lab`'s observation builder + the `/research` page shell — no new endpoint, no nav re-approval, not data-walled. Dispatch full for the same reasons J-25/J-27 were: it adds backend aggregation logic needing real unit tests plus coherence + ux-regression + closure on the critical read-only research-lab surface. Strategic note: even after the four compute-only labs (J-26/J-29/J-30/J-31) land, GOAL_ACHIEVED cannot be reached autonomously — J-22/J-23/J-24 are externally Yahoo-429 data-walled and unblock only on operator confirmation of a reachable feed.

## Quick verify

From `reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-11-what-to-click.md`:

1. Open `http://localhost:3835` in your browser, then click **"Research"** in the left sidebar.
2. Scroll down past the "Decile sort" table and the "Rank-IC" card to the panel titled **"Factor effectiveness by market regime"**.
3. In the Horizon button group (top-right), click **"5d"**.
4. Click the **"60d"** Horizon button.
5. Open the **"Factor"** dropdown (top-right) and pick a different factor (e.g. "Risk score").

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever-iter-11.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-11-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-i_can_see_the_wealthy_future_forever-iter-11-review.md |
| Browser QA | PASS | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-11-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-11-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-11-user-visible-changes.md |
| What to click | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-11-what-to-click.md |
| UI surface map | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-11-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-11-ui-test-plan.md |
| QA | PASS | reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-11-qa.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever/iter-11/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever/state/journey-history.json |
