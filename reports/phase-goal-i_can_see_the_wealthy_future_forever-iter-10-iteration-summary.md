# Iteration Summary — goal-i_can_see_the_wealthy_future_forever-iter-10

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-06-02
**Iteration:** 10

## In plain words

**What you can do now:** See the day's market at a glance; browse ranked stocks, sectors, and themes and filter the stock list by sector, by setup, or by any of three chart patterns; open any stock for a plain-English scorecard (identical on the list and its detail page) plus the price that would prove the idea wrong; rewind the whole app to any past day with one shared date control and watch a stock's chart keep drawing past that day; read forward-tested evidence of how past picks performed, broken down by stock, sector, and ranking tier; open the new Research lab to test whether a chosen signal actually sorts future returns; save a watchlist that survives a restart; grow the dataset on demand by date or range; and look up every label and pattern in a plain-language glossary — always with honest "not enough data" marks instead of made-up numbers.

**What changed this time:** A brand-new Research area opened, with its first tool — the Factor Lab. You can now pick any of eight signals (like relative strength, moving-average trend, distance from a 52-week high, or volatility) and a time horizon, then see — across all the history the product has stored — whether stocks with more of that signal actually went on to earn higher returns: it sorts them into ten groups and shows each group's average return, a version of that return that only counts downside swings against it, and a single score for how well the signal lines up with future returns. Where there isn't enough data, it says so honestly rather than inventing a number.

**What's next:** Next, the Research area gains a tool that shows whether each signal works better in calm versus turbulent markets.

## Headline

Research → Factor Lab launched: per-factor decile sort, downside risk-adjusted column, and rank-IC (J-25).

## Direction

**Signal:** improving
**Why:** This iter built J-25 — the Factor Lab on the new `/research` home — and verified it passes browser QA, with the read-only decile/rank-IC seam confirmed SELECT-only in `app/engine/research.py` source. The diff is purely additive, so the required-still-passing set (J-01/J-09/J-12/J-15/J-18/J-19) carries green; J-18 was the principal risk and held (no date state added to `/research`). 8 journeys remain failing — J-22/J-23/J-24 externally Yahoo-429 data-walled, J-26/J-27/J-29/J-30/J-31 now-unblocked unbuilt labs — and the last several iters have each moved a journey forward, so direction is healthy.

**Trend (last 5 iters):**
- Newly passing this iter: J-25
- Newly passing in last 5 iters total: J-20, J-21 (iter-6), J-28 (iter-9), J-25 (iter-10)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none (the lone historical minor one — "exactly one date selector" — stays RESOLVED)
- Iters with no journey state change: 2 of last 5 (iter-7, iter-8 — both externally data-walled on J-22)

**Latest evaluator reasoning:** J-25 landed cleanly: the Research sidebar home (`/research`) now hosts its first lab — the Factor Lab — a read-only decile sort (D1…D10 raw mean forward return + a downside-risk-adjusted column + n per decile) plus a Spearman rank-IC, all config-driven and derived once from the already-stored forward returns + factor values. This establishes the new nav home and the read-only lab-analytics seam every later lab (J-26/J-27/J-29/J-30/J-31) reuses. Every critical anti-goal seam was verified directly in source (read-only SELECT-only; downside-only risk; config-driven catalog; J-18 no date state); COHERENCE-PASS; diff purely additive so the required-still-passing set cannot have regressed.

## What was done

- Stood up the new **Research** sidebar home and `/research` route — the product's first analysis lab, reached in ≤2 clicks (microscope icon between System Health and Watchlist).
- Built the **Factor Lab**: a config-driven dropdown of 8 factors (the three scores + RS-vs-SPY 3m, MA-stack, 52-week-high proximity, up/down volume, ATR% volatility) and a horizon selector (1/5/10/20/60d).
- Added the **D1…D10 decile table** — raw mean forward return + a **downside-only risk-adjusted** column + sample size `n` per decile, colour-graded — plus the factor's **Spearman rank-IC** (signed, with n) and a survivorship / universe-relative / descriptive caveat banner; low-sample cells render honest "NA" + n.
- Backend: new read-only `app/engine/research.py` (SELECT-only over `ForwardReturn` + `ScannerResult`, recomputes no score/return/factor) + `GET /api/research/factor-lab` (422/422/503) + typed `research.factor_lab` config block with boot validators; **no DB regeneration, no schema change**.
- Verified the critical seams in source: read-only (patch-to-raise keystone), downside-only risk (`_downside_deviation`, never total stdev), config-driven catalog + `deciles:10` sentinel in `test_no_magic_numbers`, and J-18 (page useState = `{factor, horizon, state}` only).
- Tests: full backend suite **379 passed / 4 skipped** (exit 0); frontend `npm run build` typechecks all 14 routes incl. `/research` (5.41 kB).
- Verified **1 target journey (J-25) passes browser QA** — 12/15 tests pass (3 documented non-failing skips: NA-cell/empty/error states not triggerable on the committed seed, unit/source-covered), 0 failures; all 6 screenshots sha256-distinct.

## What's left

- Journey J-22 (Transparent, rule-based, expanded universe ~500 names) failing — externally Yahoo-429 data-walled; do NOT autonomously retry (auto-heals via its committed runbook on operator confirmation of a reachable no-key feed).
- Journey J-23 (Multi-timeframe bars — intraday seed + timeframe-aware pipeline) failing — same provider data wall.
- Journey J-24 (Timeframe selector on the stock chart) failing — depends on J-23 (data-walled).
- Journey J-27 (Factor Lab — regime-conditioned factor effectiveness) failing — now unblocked, compute-only over the stored seed; recommended next target.
- Journey J-26 (Factor Lab — multi-factor combination cohorts) failing — now unblocked, compute-only.
- Journey J-29 (Setup & Pattern research lab — event study) failing — needs the post-snapshot daily high/low excursion path (MAE/MFE) extracted first; larger lift.
- Journey J-30 (Volatility as a return driver — factor family, risk-adjusted + regime-conditioned) failing — extends the Factor Lab + J-27.
- Journey J-31 (Find a high-return driver end-to-end — synthesis) failing — the final `/research` journey; needs J-27 + J-29 to connect lab evidence → leaderboard filter → detail.
- Only the Factor Lab is live under `/research` so far; the remaining labs have no UI yet. (The NA/low-sample decile rendering is real and unit-tested but is not triggerable on the committed seed — honest behaviour, not a gap.)

## Next step

**full** depth. Target the next compute-only `/research` lab on the seam just established:

- **Primary — J-27 (regime-conditioned factor effectiveness):** the smallest direct extension of J-25 — add a `regime` field to each observation from the stored `scanner_runs.regime_label`, then split the existing decile table / rank-IC / top-minus-bottom-decile spread by regime, with honest per-regime n/NA. Reuses `compute_factor_lab`'s read-only observation builder + the `/research` page shell. No nav re-approval (additive section under the approved home); not data-walled.
- **Alternative — J-26 (multi-factor combination cohorts):** intersect two/three factors' top/bottom quantile membership; report the cohort's raw + risk-adjusted return, hit-rate, n vs the unconditional baseline and single-factor cohorts.
- **Defer J-29 (event study):** needs the post-snapshot daily high/low excursion path (MAE/MFE) extracted first — a larger lift. Then **J-30** (extend the volatility family already seeded by `atr_pct` with HV / contraction / downside-semivol + regime split) and **J-31** (synthesis: lab evidence → leaderboard filter → detail).
- Keep verifying the read-only seam in source on each new lab (no recompute) and de-dup evidence by sha256 — this remains a verify-by-source session (no `-audit.md` handoff was produced again this iter).
- Do **NOT** autonomously retry J-22/J-23/J-24 — the Yahoo-429 wall persists; J-22 auto-heals via its committed runbook only on operator confirmation of a reachable no-key egress.

## Quick verify

From `reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-10-what-to-click.md`:

1. Open `http://localhost:3835/` in your browser.
2. In the left sidebar, find the "Research" item (microscope icon) between "System Health" and "Watchlist", and click it.
3. Wait for the loading bars to resolve, then look at the page body.
4. Check the decile table column headers.
5. Confirm the factor dropdown shows "Leadership score" and the highlighted horizon button is "20d".

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever-iter-10.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-10-dev.md |
| Frontend handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-10-frontend.md |
| Review | PASS | reports/reviews/goal-i_can_see_the_wealthy_future_forever-iter-10-review.md |
| Browser QA | PASS | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-10-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-10-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-10-user-visible-changes.md |
| What to click | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-10-what-to-click.md |
| UI surface map | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-10-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-10-ui-test-plan.md |
| QA | PASS | reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-10-qa.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever/iter-10/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever/state/journey-history.json |
