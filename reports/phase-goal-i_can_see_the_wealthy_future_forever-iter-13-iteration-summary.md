# Iteration Summary — goal-i_can_see_the_wealthy_future_forever-iter-13

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-06-02
**Iteration:** 13

## In plain words

**What you can do now:** See the day's market at a glance and browse ranked stocks, sectors, and themes; filter the stock list by sector, setup, or any of three chart patterns; open any stock for a plain-English scorecard that reads the same on the list and the detail page, next to the price that would prove the idea wrong; rewind the whole app to any past day with one shared date control and watch a price chart keep drawing right up to today; and read forward-tested evidence of how past picks actually performed by stock, sector, and ranking tier. You can also open the Research area's Factor Lab to test whether a signal sorted future returns — across ten ranked groups and a correlation score, shown raw and on a downside-only risk-adjusted basis, split by market mood, combined two or three signals at once, and now across a whole family of volatility signals — save a watchlist that survives a restart, grow the dataset by date or range, and look up every label and pattern in a plain-language glossary, always with honest "not enough data yet" marks instead of made-up numbers.

**What changed this time:** The Factor Lab can now test volatility as a family of four measures — overall price swing, historical volatility, whether volatility is drying up, and downside-only volatility — gathered under a single "Volatility" heading in the signal dropdown. For each one you can read whether, and in which direction, that kind of volatility lined up with future returns, reported honestly even when the answer is "no real edge in this data." None of this changed any stock's score, bucket, or ranking.

**What's next:** Next the Research area will add a Setup & Pattern lab that studies how every past occurrence of a setup or pattern actually played out — its typical gain, how far it dipped along the way, and the best holding period.

## Headline

Volatility is now a four-measure factor family on the Research Factor Lab.

## Direction

**Signal:** improving
**Why:** This iter built J-30 — volatility as a four-measure Factor-Lab family (HV, VCP-style contraction, downside/semivol added to ATR%), computed once in the scoring path and read by the read-only lab — and it passed browser QA 13/13. The riskiest part (a new value on the critical scoring/snapshot path plus a full DB regeneration) held: the critical J-06 score-consistency and J-07 Risk-Off gates were re-verified byte-identical post-regen. Five journeys remain failing — J-22/J-23/J-24 externally Yahoo-429 data-walled, J-29/J-31 unbuilt — with J-29 (event study) flagged as the next target.

**Trend (last 5 iters):**
- Newly passing this iter: J-30
- Newly passing in last 5 iters total: J-28 (iter-9), J-25 (iter-10), J-27 (iter-11), J-26 (iter-12), J-30 (iter-13)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none (the single historical "exactly one date selector" minor one stays RESOLVED)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** J-30 (volatility as a first-class Factor-Lab family) landed cleanly and is newly passing: three new stored volatility factor values (`hv`, `vcp_contraction`, `downside_vol`) are computed once in the scoring/snapshot path from as-of bars (≤ D, no lookahead), stored as append-only `ScannerResult` columns, and read verbatim by the existing read-only Factor Lab. The single biggest risk — a volatility value leaking into a weighted score and shifting J-06/J-07 — did not materialize: the critical post-DB-regen gates hold (Risk-Off → Actionable=0; NVDA scores byte-identical across leaderboard↔detail), proven both in source and live against the regenerated DB. Not GOAL_ACHIEVED — 5 journeys remain failing (J-22/J-23/J-24 externally Yahoo-429 data-walled; J-29/J-31 unbuilt).

## What was done

- Added three new volatility indicator functions (`indicators.py`) — historical volatility, a continuous VCP-style contraction ratio, and downside semivol about MAR=0 — all pure, DB-free, NA-graceful, and config-windowed (no magic numbers).
- Computed the three values once per stock in `score_stocks` from the as-of bars already in hand (date ≤ D, no lookahead) and stored them as append-only typed `ScannerResult` columns; the read-only `compute_factor_lab` reads them verbatim via `getattr` (no new research function, no new endpoint).
- Added three config-driven Factor-Lab catalog members (`hv`, `vcp_contraction`, `downside_vol`, family `volatility`) plus four new validated `indicators` windows in `config.yaml`.
- Grouped the `/research` Factor dropdown by family via native `<optgroup>` (config-driven, purely presentational — no recompute, no new value).
- Regenerated the database from the committed offline seed so every immutable snapshot carries the three new values; full backend suite **428 passed / 4 skipped** after regen.
- Locked the critical constraint with a score-invariance keystone test that forces the three values to a constant and asserts every score, A–E bucket, setup status, and rank stays byte-identical (guards J-06/J-07).
- Verified the target journey (J-30) passes browser QA **13/13**; the critical post-regen gates J-07 (Risk-Off → Actionable=0) and J-06 (NVDA byte-identical leaderboard↔detail) were re-verified live against the regenerated DB.

## What's left

- Journey J-22 (Transparent, rule-based, expanded universe ~500 names) failing — externally data-walled (Yahoo HTTP 429 on the one-shot OHLCV+market-cap fetch); infra complete and tested, auto-heals via its committed finish runbook only on operator confirmation of a reachable no-key egress.
- Journey J-23 (Multi-timeframe bars — intraday seed + timeframe-aware pipeline) failing — unbuilt and data-walled (needs fresh Yahoo intraday fetches, same provider wall).
- Journey J-24 (Timeframe selector on the stock chart 1D/1h/15m/5m) failing — unbuilt; depends on J-23's intraday data.
- Journey J-29 (Setup & Pattern research lab — event study across all snapshots) failing — unbuilt; the recommended next target. Larger lift: needs the post-snapshot daily high/low excursion path (MAE/MFE) extracted and stored first.
- Journey J-31 (Find a high-return driver end-to-end — synthesis) failing — unbuilt; requires J-29 to connect lab evidence → leaderboard filter → detail.
- The three new volatility values are stored for Factor-Lab consumption only (by design) — intentionally not shown on the `/stocks` leaderboard or stock-detail breakdowns.

## Next step

Next iteration: full depth, target J-29 (Setup & Pattern research lab — event study across all snapshots). This is the last large autonomous lift before the J-31 synthesis. It requires extracting and storing the post-snapshot daily high/low excursion path (MAE/MFE) first — the larger lift prior evaluators flagged — then pooling every historical occurrence of a setup/pattern to report the forward-return distribution, hit-rate, expectancy, MAE/MFE, best exit-horizon, and regime/sector slices, plus the `return/MAE` risk-adjusted ratio that J-30 deferred. The "Setup & Pattern Lab" lives on the already-approved `/research` home (no nav re-approval), but the decomposer should determine up front whether MAE/MFE needs a new stored excursion path on the snapshot (likely — `forward_testing` currently stores realized returns, not daily-high/low excursions) and keep the read-only seam intact (derive once from stored data; the API/view recomputes nothing). After J-29, J-31 (synthesis) becomes buildable. Strategic: GOAL_ACHIEVED is NOT autonomously reachable while J-22/J-23/J-24 stay externally Yahoo-429 data-walled — expect operator confirmation of a reachable egress or a correct STALLED on the data-walled remainder once the labs are done. Do NOT autonomously retry J-22/J-23/J-24.

## Quick verify

From `reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-13-what-to-click.md`:

1. Open `http://localhost:3835/research` in your browser.
2. Click the "Factor" dropdown (top-right, under the "Factor" label) and look at how options are grouped.
3. Select "Historical volatility (HV)" from the Volatility group.
4. Select "Volatility contraction (VCP-style)" from the Volatility group.
5. Select "Downside volatility (semivol)", then scan the "Risk-adjusted (downside)" column and the "Factor effectiveness by market regime" table for an "NA".

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever-iter-13.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-13-dev.md |
| Review | PASS | reports/reviews/goal-i_can_see_the_wealthy_future_forever-iter-13-review.md |
| Browser QA | PASS | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-13-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-13-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-13-user-visible-changes.md |
| What to click | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-13-what-to-click.md |
| UI surface map | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-13-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-13-ui-test-plan.md |
| QA | PASS | reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-13-qa.md |
| Coherence | COHERENCE-PASS | runs/goal-session-i_can_see_the_wealthy_future_forever/iter-13/coherence.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever/iter-13/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever/state/journey-history.json |
