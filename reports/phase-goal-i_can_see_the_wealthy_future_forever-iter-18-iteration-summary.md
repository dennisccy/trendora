# Iteration Summary — goal-i_can_see_the_wealthy_future_forever-iter-18

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-06-04
**Iteration:** 18

## In plain words

**What you can do now:** See the day's market at a glance and browse ranked stocks, sectors, and themes — filtering the stock list by sector, setup, or chart pattern through links you can share. Open any stock for a plain-English scorecard that reads the same on the list and the detail page, plus the price level that would prove the idea wrong. Rewind the whole app to any past day with one shared date control and watch a price chart keep drawing right up to today. Read how the rankings actually performed afterwards — by score grade, against the market, and versus a fair comparison group — now also as of any past date on the Backtest page. In the Research area, test whether a signal really sorted future returns (by group, by market mood, in combination, and across a family of volatility measures), study any setup or pattern's full track record, and jump straight from a finding to the names behind it and on to a stock's scorecard. Save a watchlist that survives a restart, grow the dataset by date, and look up every label in a plain-language glossary — always with honest "not enough data yet" marks instead of made-up numbers.

**What changed this time:** In the Research area, when you combine two or more signals to see how that group of stocks behaved, the combined result is now actually filled in with real numbers instead of almost always coming up empty. The app blends your chosen signals into a single combined ranking, and you can now mix up to all eleven signals at once (the old limit was three). A separate line still shows the stricter "only the stocks that meet every signal" view, marked honestly as "not enough names" when nothing qualifies — so you can finally answer "does combining signals beat either one alone?"

**What's next:** Next, the Research area will let you view its findings as of any past date — not just across all of history — using the same single shared date control the rest of the app already uses.

## Headline

Factor Lab's Combined cohort is now a populated composite rank-blend (was a perpetually-empty strict-AND).

## Direction

**Signal:** improving
**Why:** This iter converted J-26 partial→passing by replacing the strict-AND headline in `compute_factor_combination` with a config-weighted composite percentile-rank blend (top config-quantile), demoting strict-AND to a secondary `strict_overlap` cohort; browser QA captured the headline fix live (composite n=244 populated while `strict_overlap` shows NA + n=0). The change is additive and read-only — scoring/snapshot paths git-verified empty, so J-06/J-07 stay byte-identical and the 22 carried journeys cannot regress. Only J-32 (Research as-of toggle, the last buildable must-have) remains before GOAL_ACHIEVED is reachable on the buildable set; J-22/J-23/J-24 stay externally data-walled and non-halting per the re-scoped goal.

**Trend (last 5 iters):**
- Newly passing this iter: J-26
- Newly passing in last 5 iters total: J-29 (iter-14), J-31 (iter-16), J-26 (iter-18)
- Regressions in last 5 iters: none (J-26 dropped to partial at iter-17 from an operator re-scope bar-raise, explicitly not a code regression)
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** J-26 landed exactly as the operator re-scope (commit `d723133`) requires: the Factor-Lab Combined cohort is now a non-empty composite percentile-rank blend (config-weighted, top config-quantile) that scales to all 11 catalog factors, with the perpetually-0/NA strict AND-intersection demoted to a clearly-labelled secondary `strict_overlap` cohort (honest NA + n when empty). I verified every critical seam in SOURCE (read-only, composite-non-empty, J-18 no-date-state, no DB regen, no magic numbers), not the QA table. Not GOAL_ACHIEVED — J-32 (Research as-of toggle) is a buildable, unbuilt must-have (iter-19 target), so the loop continues.

## What was done

- Replaced the strict-AND headline Combined cohort with a populated **composite percentile-rank blend** in `compute_factor_combination`: each condition's stored factor value is percentile-ranked over the same read-only pool, oriented by the chosen Top/Bottom side, config-weighted-averaged, and the top config-quantile of the blend becomes the cohort (default 2-factor selection yields n≈244 on the seed, clearing the 30-observation min-sample).
- Demoted the exact AND-intersection to a secondary **Strict overlap (AND)** cohort that honestly shows NA + n when empty (never a fabricated 0).
- Raised the combination cap from 3 to all **11** catalog factors — config-driven, no hard-coded UI/code cap.
- Added a required `composite` config sub-block (`quantile`, `weighting`) with boot validation (`CompositeCfg` / `CompositeWeightingCfg` raise `ConfigError` on a bad quantile key or non-positive weight); added the key to all 4 inline test config dicts.
- Reshaped the API payload (`combined` → `composite` + `strict_overlap` + echoed quantile/weighting metadata) and the frontend table (Baseline → singles → Combined (composite, emphasized) → Strict overlap (AND, muted)) and types; removed the old `combined` key cleanly.
- Verified target + regression journeys pass browser QA (13/13 browser tests, 18/18 QA cases); backend 461 passed / 4 skipped (run once); frontend `npm run build` clean.

## What's left

- Journey J-32 (Research point-in-time toggle — as-of vs all-history) failing — buildable, compute-only, the explicit iter-19 target (full depth).
- Journey J-22 (transparent rule-based expanded universe ~500 names) failing — externally data-walled (Yahoo 429), recorded honestly blocked (NA), non-halting per the re-scoped goal.
- Journey J-23 (multi-timeframe intraday bars) failing — unbuilt + data-walled, non-halting.
- Journey J-24 (chart timeframe selector) failing — unbuilt (depends on J-23), non-halting.
- Known limitation (carried, by design): the composite blend is **descriptive, not predictive** — a deterministic ranking of stored values, never a fitted/ML forecast; survivorship-bias caveat persists.
- Minor cosmetic NOTE (non-blocking): stale `CombinationLab` code docstring at `research/page.tsx:530` still says "compose 2–3 … combined-AND"; the user-visible hint text is correct. Carry to a future tidy.

## Next step

iter-19 → J-32 (full depth) — the last buildable journey. Add an All-history ⟷ As-of-date MODE to the three `/research` lab endpoints (`compute_factor_lab` / `compute_factor_combination` / `compute_event_study`), reusing iter-17's `asof_date ≤ D` membership-filter seam (the `compute_forward_aggregates(..., as_of=D)` pattern — a `ScannerRun.asof_date <= as_of` join on the SELECT-only observation builders; `as_of=None` ⇒ byte-identical all-history). It MUST be a MODE reading the single global as-of control — NO second date state (J-18 is again the principal anti-goal risk: the toggle is a mode, not a date picker). Full depth is justified: critical read-only research path on three lab functions + the J-18 anti-goal surface + real unit tests (as-of filter correctness, no >D leak, no second date state, low-sample NA at early dates) + coherence/closure. No nav change (lives on the approved `/research` home) → no blueprint re-approval. After J-32 lands and nothing regresses → GOAL_ACHIEVED is reachable on the buildable set: J-22/J-23/J-24 are honestly blocked (NA) and non-halting per the re-scoped goal — do NOT autonomously re-probe them.

## Quick verify

From `reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-18-what-to-click.md`:

1. Open `http://localhost:3835/research` in your browser and scroll to the panel titled "Multi-factor combination cohort".
2. In that table, find the highlighted/bold row labelled "Combined (composite rank-blend)" — its n and all return/hit-rate/risk-adjusted cells should show real numbers, not "NA".
3. Look at the row directly below it, labelled "Strict overlap (AND)" — a muted secondary row showing numbers or an honest "NA" with an n chip, never blank.
4. Read the table top-to-bottom and confirm the order: Baseline (all names) → single-factor rows → Combined (composite rank-blend) → Strict overlap (AND); no old "Combined (AND)"-only row.
5. Click "Add condition" repeatedly — you can add up to 11 rows (button disables at 11, not 3), and the Combined row stays populated.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever-iter-18.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-18-dev.md |
| Frontend handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-18-frontend.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-i_can_see_the_wealthy_future_forever-iter-18-review.md |
| Browser QA | PASS | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-18-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-18-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-18-user-visible-changes.md |
| What to click | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-18-what-to-click.md |
| UI surface map | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-18-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-18-ui-test-plan.md |
| QA | PASS | reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-18-qa.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever/iter-18/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever/state/journey-history.json |
