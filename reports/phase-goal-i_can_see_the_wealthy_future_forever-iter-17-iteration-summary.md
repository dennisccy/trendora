# Iteration Summary — goal-i_can_see_the_wealthy_future_forever-iter-17

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-06-04
**Iteration:** 17

## In plain words

**What you can do now:** See the day's market at a glance; browse ranked stocks, sectors, and themes and filter the list by sector, setup, or any of three chart patterns — also via shareable, bookmarkable links; open any stock for a plain-English scorecard that's identical on the list and the detail page, plus the price that would prove the idea wrong; rewind the whole app to any past day with one shared date control and watch a chart keep drawing past it; read the forward-tested track record (how the rankings actually performed, by score grade, versus the benchmarks, and against a control group) on the Backtest page — now also as of any past date; explore the Research area to test whether a signal sorts future returns by group, market mood, combination, and a volatility family, and study any setup or pattern's full pooled track record; travel from a research finding straight to the names expressing it and on to the full scorecard; save a watchlist that survives a restart; grow the dataset by date; and look up every label in a plain-language glossary — always with honest "not enough data yet" marks instead of made-up numbers.

**What changed this time:** The historical track record of how the rankings performed — which used to sit on a separate "System Health" page that always showed all of history — now lives on the **Backtest** page, and you can rewind it to any past date: it uses only the days on or before the date you picked, and the sample size honestly shrinks the further back you go. Returning to today reproduces the full all-history numbers. The old System Health page is gone, so all of this now sits under the single shared date control.

**What's next:** Next, the Research area will let you blend several signals into one combined ranking and test how that group of stocks performed, then gain a switch to view all the research either across all history or as of a chosen past date.

## Headline

Forward-tested evidence relocated onto Backtest and scoped to the global as-of date; System Health retired.

## Direction

**Signal:** improving
**Why:** This iter delivered the operator's re-scoped target — the forward-tested evidence aggregate (J-09) and its control-group (J-10) were relocated off the retired System Health onto `/backtest` and given a point-in-time `as_of` cutoff (expanding window ≤ D), with no scoring/snapshot change so J-06/J-07 stay byte-identical and the principal anti-goal risk J-18 (one date control) was held in source and live. No journey regressed and no anti-goal was violated; the last several iters newly passed J-30, J-29, and J-31, so the trajectory is healthy. The same operator re-scope raised J-26's bar (now `partial` — needs a composite blend, scheduled iter-18) and added J-32 (Research as-of toggle, `failing` — scheduled iter-19); after both land and nothing regresses, GOAL_ACHIEVED is reachable with the data-walled J-22/J-23/J-24 recorded as honestly blocked and non-halting.

**Trend (last 5 iters):**
- Newly passing this iter: none in the strict failing→passing sense — the target J-09 and J-10 were re-delivered (relocated to Backtest, now as-of-scoped) and stayed passing
- Newly passing in last 5 iters total: J-30 (iter-13), J-29 (iter-14), J-31 (iter-16)
- Regressions in last 5 iters: none (iter-17 J-26 → `partial` is an operator re-scope bar-raise, not a code regression)
- Anti-goal violations in last 5 iters: none (the single historical minor "one date selector" stays RESOLVED)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The target journeys J-09 (as-of-scoped Backtest forward-tested evidence, expanding window ≤ D) and J-10 (control-group, riding the same aggregate) were delivered exactly as the operator's re-scope (commit `d723133`) requires: `compute_forward_aggregates` gained a single `as_of` cutoff, the aggregate relocated off the retired `/system-health` onto `/backtest` under the single global as-of switcher, and System Health was fully retired. Not GOAL_ACHIEVED: the same re-scope raised J-26's bar (now a non-empty composite percentile-rank blend, still strict-AND in code → `partial`) and added J-32 (Research as-of toggle, unbuilt → `failing`); both are scheduled (iter-18, iter-19) and tractable. J-22/23/24 stay honestly blocked (NA) and are non-halting per the re-scoped goal.

## What was done

- As-of-scoped the forward-test evidence aggregate: `compute_forward_aggregates(..., *, as_of)` gained a single `ScannerRun.asof_date <= D` membership filter (expanding walk-forward window); `as_of=None` stays byte-identical to all-history, no future-run leak (both unit-tested).
- Relocated the evidence onto Backtest: `GET /api/backtest` now returns `evidence_by_horizon` (all horizons in one payload), and a new `components/evidence-panels.tsx` renders forward return by A–E bucket, excess vs SPY/QQQ, by-setup, by-regime, VCP/pattern breakdowns, and the control-group table at the bottom of `/backtest` — delivering re-scoped **J-09** and **J-10**.
- Retired System Health entirely: deleted the route, router registration, page, sidebar nav entry, data client, type, and tests → `/system-health` is a 404 and the sidebar now lists 10 items.
- Preserved the critical seams in source: J-18 (no page-local date state — reuses the global as-of + existing horizon view-selector; horizon switch = 0 refetch) and J-21 ordering (evidence section last, exactly one "Return attribution").
- Left the scoring/scanner/regime/pattern/snapshot path untouched with no DB regen → J-06/J-07 byte-identical; the consistency invariant was moved onto the as-of-scoped aggregate, not deleted.
- Verified target and regression journeys pass browser QA (J-09, J-10, plus J-14/J-15/J-16/J-18/J-19/J-21/J-28/J-13): backend 454 passed / 4 skipped (run once), frontend typecheck clean, review PASS, QA 15/15, browser QA 12/13 (1 P2 empty-state skip — unreachable with seed, source-verified).

## What's left

- Journey J-26 (Factor Lab — multi-factor composite combination cohort) `partial`: the re-scope now requires a non-empty composite percentile-rank blend; the code is still the strict AND-intersection (`research.py:479`) — iter-18 target.
- Journey J-32 (Research point-in-time toggle) `failing`: unbuilt — `/api/research/*` has no `as_of` param; add an all-history ⟷ as-of MODE reusing this iter's scoping seam — iter-19 target.
- Journey J-22 (transparent, rule-based, expanded ~500-name universe) `failing`: externally data-walled (Yahoo-429), recorded honestly blocked (NA), non-halting; do not autonomously re-probe.
- Journey J-23 (multi-timeframe intraday bars) `failing`: data-walled, non-halting.
- Journey J-24 (timeframe selector on the stock chart) `failing`: data-walled, non-halting.
- Operator gate: a blueprint re-approval (System Health retirement / single Backtest evidence home) is pending and pauses `run-goal.sh` before iter-18.
- Known limitation: `/api/backtest` now calls `compute_forward_aggregates` 5× per request (one per horizon) — fine for the seed; memoize per `(as_of, horizon)` if the universe or horizons grow.
- Minor stale prose: `apps/frontend/app/data/page.tsx:141` subtitle still says "grow the System Health evidence" (no dangling link; update to "Backtest evidence" in a future touch).

## Next step

Operator gate first: approve the pending blueprint re-approval (System Health retirement / single Backtest evidence home) at iter-18's pre-decomposer pause. Then **iter-18 → J-26 (full depth)**: replace the strict AND-intersection at `research.py:479` with the re-scoped composite percentile-rank blend (config-weighted across any number of selected factors, taking the top config-quantile of the composite) so the Combined cohort is non-empty and clears `min_sample`, keeping strict-AND as an optional secondary column; real unit tests + coherence/closure on the critical read-only research surface; verify in source it recomputes no factor/return. Then **iter-19 → J-32 (full depth)**: add the Research all-history ⟷ as-of toggle reusing this iteration's `asof_date ≤ D` scoping seam as a MODE, not a second date control (reads the single global as-of). After J-26 and J-32 land and nothing regresses, GOAL_ACHIEVED is reachable: J-22/J-23/J-24 are recorded as honestly blocked (NA) and non-halting per the re-scoped goal — they do not veto completion and must not be autonomously re-probed.

## Quick verify

From `reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-17-what-to-click.md`:

1. Open `http://localhost:3835/backtest` in your browser
2. In that bottom section, read the summary line and the panels below it
3. Note the "Snapshots contributing" number, then at the top bar open the "View as-of date" dropdown and select an earlier date
4. Re-open the "View as-of date" dropdown and select the first option "Latest · <date>"
5. Open browser DevTools → Network tab, filter for "backtest", clear the log. Then find the "Horizon" button group (in the Return Attribution header) and click a different button (e.g. "20d")

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever-iter-17.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-17-dev.md |
| Frontend handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-17-frontend.md |
| Review | PASS | reports/reviews/goal-i_can_see_the_wealthy_future_forever-iter-17-review.md |
| Browser QA | PASS | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-17-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-17-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-17-user-visible-changes.md |
| What to click | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-17-what-to-click.md |
| UI surface map | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-17-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-17-ui-test-plan.md |
| QA | PASS | reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-17-qa.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever/iter-17/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever/state/journey-history.json |
