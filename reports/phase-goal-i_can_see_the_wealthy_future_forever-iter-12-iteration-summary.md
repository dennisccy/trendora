# Iteration Summary — goal-i_can_see_the_wealthy_future_forever-iter-12

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-06-02
**Iteration:** 12

## In plain words

**What you can do now:** See the day's market at a glance; browse ranked stocks, sectors, and themes and filter the stock list by sector, setup, or any of three chart patterns; open any stock for a plain-English scorecard — identical on the list and the detail page — plus the price that would prove the idea wrong; rewind the whole app to any past day with one shared date control and watch a stock's chart keep drawing past it; read forward-tested evidence of how past picks actually performed by stock, sector, and ranking tier; open the Research area's Factor Lab to test whether any of eight signals sorts future returns — grouped into ten buckets, raw and risk-adjusted, broken down by market mood, and now combined two or three at a time; save a watchlist that survives a restart; grow the dataset by date or range; and look up every label and pattern in a plain-language glossary — always with honest "not enough data yet" marks instead of made-up numbers.

**What changed this time:** You can now combine two or three signals at once in the Factor Lab and see whether stocks that satisfy all of them together earned better returns than each signal on its own — or than the whole market — laid out side by side with their average return, typical return, how often they were positive, and a risk-aware figure. When the combined group gets too small to trust, it is shown honestly as "not enough data" rather than a fabricated number.

**What's next:** Next the Factor Lab will add a volatility family of signals — testing whether calmer or more volatile stocks tend to lead — each measured the same careful, risk-aware way and broken down by market mood.

## Headline

Factor Lab multi-factor combination cohorts (J-26): combine 2–3 factor conditions, compare Combined-AND vs baseline.

## Direction

**Signal:** improving
**Why:** This iter added J-26 (multi-factor combination cohorts) as a strictly additive read-only slice on the `/research` Factor-Lab seam — verified passing in browser (15/16) and at source (`compute_factor_combination` is SELECT-only; `scoring`/`forward_testing`/`scanner`/`regime`/`patterns` untouched), so none of the 22 carried journeys could regress. 25/31 must-have journeys now pass, and the four `/research` labs are landing one per iteration (J-25 → J-27 → J-26) toward J-30 next. The only remaining hard blocks — J-22/J-23/J-24 — are external Yahoo-429 data walls, not code defects.

**Trend (last 5 iters):**
- Newly passing this iter: J-26
- Newly passing in last 5 iters total: J-28 (iter-9), J-25 (iter-10), J-27 (iter-11), J-26 (iter-12)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none (the single historical minor "one date selector" stays resolved)
- Iters with no journey state change: 1 of last 5 (iter-8 — J-22 stayed externally data-walled)

**Latest evaluator reasoning:** J-26 (Factor Lab multi-factor combination cohorts) landed as a textbook-clean additive slice and is newly passing — verified at the API, in browser, and in source. The user can now compose 2–3 factor conditions (each a catalog factor at its top/bottom quantile) and read the Combined-(AND) cohort beside the unconditional baseline and each single-factor cohort (mean / median / hit-rate / downside-risk-adjusted / n), with honest NA on a thin combined cohort. 25/31 must-have journeys now pass, 6 fail. Not GOAL_ACHIEVED; not REGRESSION; not STALLED; COHERENCE-PASS gives no veto.

## What was done

- Added a **Multi-factor combination cohort** section to the Factor Lab (`/research`): combine 2–3 catalog-factor conditions (each Top/Bottom at a chosen quantile) and compare the **Combined-(AND)** cohort against the **unconditional baseline** and **each single-factor** cohort — columns n / mean / median / hit-rate / downside-risk-adjusted.
- Interactive composition: pick factor + side + quantile per condition, **Add condition** (up to 3) / **Remove** (down to 2), and change the shared horizon — every change re-points the table from freshly fetched server values.
- Honest small-sample handling: a thin or empty combined cohort shows **NA + the real n** (never a fabricated 0); a combined cohort strictly smaller than each single cohort is the visible interaction signal the lab exists to surface.
- New read-only `GET /api/research/factor-combination` endpoint (SELECT-only on `ForwardReturn` + `ScannerResult`) and a new `config.research.factor_lab.combination` block (min/max conditions, quantile vocabulary, default conditions), reusing the existing `walk_forward.min_sample` threshold — no new magic numbers, no schema change.
- Strictly additive over the proven Factor-Lab read-only seam — `scoring`/`scanner`/`forward_testing`/`regime`/`patterns`/`snapshot_serving`/as-of paths untouched; no DB regeneration; J-18 (one date control) preserved — the new section adds no date state.
- Verified the target journey: browser QA PASS (15/16, 1 skipped empty-pool unreproducible, code-verified), QA 19/19 PASS, review PASS, backend 411 passed / 4 skipped.

## What's left

- Journey J-22 (Transparent, rule-based, expanded universe ~500 names) failing — externally data-walled (Yahoo HTTP 429); infra complete and tested, auto-heals via its committed finish runbook only on operator confirmation of a reachable no-key egress.
- Journey J-23 (Multi-timeframe bars — intraday seed + timeframe-aware pipeline) failing — unbuilt and data-walled (needs fresh intraday Yahoo fetches, same 429 wall).
- Journey J-24 (Timeframe selector on the stock chart) failing — unbuilt; depends on J-23 intraday data.
- Journey J-30 (Volatility as a return driver — factor family) failing — unbuilt compute-only `/research` lab; the recommended next target.
- Journey J-29 (Setup & Pattern research lab — event study across all snapshots) failing — unbuilt compute-only lab; needs the post-snapshot daily high/low MAE/MFE excursion path extracted first.
- Journey J-31 (Find a high-return driver end-to-end — synthesis) failing — unbuilt; the final `/research` journey, requires J-29 plus the existing labs to connect lab evidence → leaderboard filter → detail.
- Known limitation: the combined cohort is the strict AND-intersection, so it narrows quickly; this is shown honestly as NA + n below the minimum-sample threshold, never padded.
- Known limitation: the risk-adjusted column is downside-deviation only; return/MAE and MAE/MFE excursion measures arrive with the later event-study lab (J-29).

## Next step

**Full depth, target J-30 (volatility as a return driver — the factor family).** The smallest next extension of the now-triply-proven read-only Factor-Lab seam (J-25 decile/IC + J-27 regime split + J-26 combination): extend the `config.research.factor_lab` volatility family beyond `atr_pct` (HV / 20-day historical vol, VCP-style contraction, downside/semivol), each decile/IC-tested raw + downside-risk-adjusted and regime-conditioned via the existing J-27 by-regime helper, cross-validating the contraction measure against the VCP evidence. The decomposer must determine up front whether these volatility factor *values* are already stored on `ScannerResult`/`record_json` (then J-30 is purely additive read-only catalog entries, like J-25/J-27/J-26, kept on the `/research` seam with no nav re-approval) or must be added to `scoring.py` (then it touches the critical scoring path, requires a DB regen, and must re-verify the J-07 Risk-Off→Actionable=0 gate). Autonomous runway after J-30: J-29 (event study — larger lift; extract the post-snapshot daily high/low MAE/MFE excursion path first) → J-31 (synthesis). GOAL_ACHIEVED is not autonomously reachable while J-22/J-23/J-24 stay externally Yahoo-429 data-walled — expect operator egress confirmation or a correct STALLED once the labs are done. Do NOT autonomously retry J-22/J-23/J-24.

## Quick verify

From `reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-12-what-to-click.md`:

1. Open `http://localhost:3835/research` in your browser.
2. Scroll to the bottom of the page, below the "Factor effectiveness by market regime" table.
3. Read the comparison table (Cohort / n / Mean fwd return / Median / Hit-rate / Risk-adjusted (downside); rows Baseline, each single condition, shaded Combined (AND)).
4. In the first condition row, open the "Factor" dropdown and pick a different factor — the table dims then refreshes and the Combined (AND) row re-computes.
5. Click the "Add condition" button — a 3rd condition row appears, "Add condition" greys out, and the Combined (AND) n is ≤ the smallest single-row n.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever-iter-12.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-12-dev.md |
| Frontend handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-12-frontend.md |
| Review | PASS | reports/reviews/goal-i_can_see_the_wealthy_future_forever-iter-12-review.md |
| Browser QA | PASS | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-12-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-12-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-12-user-visible-changes.md |
| What to click | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-12-what-to-click.md |
| UI surface map | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-12-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-12-ui-test-plan.md |
| QA | PASS | reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-12-qa.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever/iter-12/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever/state/journey-history.json |
