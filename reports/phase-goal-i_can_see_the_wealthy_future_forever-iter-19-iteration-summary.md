# Iteration Summary — goal-i_can_see_the_wealthy_future_forever-iter-19

**Verdict:** GOAL_ACHIEVED
**Iteration type:** goal-full
**Date:** 2026-06-04
**Iteration:** 19

## In plain words

**What you can do now:** See the day's market at a glance; browse ranked stocks, sectors, and themes and filter by sector, setup, or chart pattern using shareable links; open any stock for a plain-English scorecard that matches between the list and the detail page, plus the price that would prove the idea wrong; rewind the whole app to any past day with one shared date control and watch a chart keep drawing past that date to today; read forward-tested evidence by score grade, benchmark, and control group on the Backtest page as of any past date; explore the Research area to test whether a signal sorts future returns — by group, by market mood, as a populated multi-signal blend, and across a volatility family — and study any setup or pattern's full track record; travel from any finding to the names behind it and on to a stock's scorecard; save a watchlist that survives a restart; grow the dataset by date; and look up every label in a plain-language glossary — always with honest "not enough data yet" marks instead of invented numbers.

**What changed this time:** The Research area gained an "All history ⟷ As of date" switch. You can now read every research figure either across all history (exactly as before) or rewound to a chosen past date, so you see only what was known by that day. At early dates the sample shrinks and the app honestly marks "not enough data yet" rather than filling the gap with a made-up number. There is still only one shared date control for the whole app — the new switch is a mode, not a second calendar.

**What's next:** This was the last buildable feature, so the product is delivered. The only remaining wishes — a much bigger list of stocks and intraday chart timeframes — are waiting on a free data source that currently can't be reached, and they are recorded as honestly blocked rather than holding up the project.

## Headline

Research labs gain an all-history vs point-in-time as-of-date toggle — the last buildable journey; goal achieved.

## Direction

**Signal:** improving
**Why:** This iter delivered J-32 (the Research All-history ⟷ As-of-date point-in-time toggle), the last buildable must-have journey, verified passing in source, live browser flows (12/12), and unit tests (backend 476 passed). The principal anti-goal risk J-18 ("exactly one date control") was the maximal test this round — the as-of mode was the greatest temptation to add a second date control — and it held; nothing regressed (additive `/research`-only diff, scoring/snapshot path git-verified untouched, no DB regen). With J-32 the buildable set is 29/29 passing → GOAL_ACHIEVED; J-22/J-23/J-24 stay externally data-walled and are explicitly non-halting/non-vetoing per the operator's re-scoped goal.

**Trend (last 5 iters):**
- Newly passing this iter: J-32
- Newly passing in last 5 iters total: J-31 (iter-16), J-26 (iter-18), J-32 (iter-19); J-09 + J-10 re-delivered in re-scoped form, relocated to Backtest (iter-17)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none (the single historical minor "one date selector" stays RESOLVED, re-confirmed held)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** J-32 (the Research All-history ⟷ As-of-date point-in-time toggle) — the last buildable must-have journey — landed cleanly and is verified passing in source, live browser flows, and unit tests. With it, the entire buildable set is 29/29 passing (J-01…J-21, J-25…J-32). The principal anti-goal risk (J-18, "exactly one date selector") was re-confirmed held in source and live; nothing regressed; coherence is COHERENCE-PASS. J-22/J-23/J-24 remain externally data-walled, recorded honestly blocked (NA), and are non-halting/non-vetoing per the operator's re-scoped `docs/goal.md`.

## What was done

- Added the Research "All history ⟷ As of date" mode toggle (J-32) on `/research` — a segmented button group (mode switch, not a second date control) driven entirely by the existing single global as-of switcher.
- Backend: threaded a keyword-only `as_of` parameter into the three lab functions (`compute_factor_lab`, `compute_factor_combination`, `compute_event_study`) and their three SELECT-only observation builders, applying one membership filter on the canonical `ScannerRun.asof_date`; `as_of=None` adds no clause → byte-identical all-history.
- Added the optional `?as_of=YYYY-MM-DD` query param to the three research read endpoints (factor-lab, factor-combination, event-study); each payload echoes the resolved `asof_date`; validation returns 422 (unparseable) / 400 (future).
- Frontend: `mode:"all"|"asof"` string state with `asofCutoff = mode==="asof" ? asOf : null` read from `useAsOf()`; the three lab fetch effects key on the resolved cutoff — preserving J-15 (no refetch in All-history mode) and J-18 (one date control).
- Added an inline point-in-time context label that explains in plain language what the active mode pools and shows the resolved cutoff date when scoped.
- Updated the three `*_no_date_control_present` invariant tests to the J-32 truth (not deleted, per the iter-2 lesson); backend 476 passed / 4 skipped; review PASS; QA 16/16.
- Verified J-32 passes browser QA (12/12), including both critical anti-goal gates: UT-07 (J-15 — All-history fires 0 `/research/*` refetches on a global-date change, network-asserted) and UT-08 (J-18 — exactly one date control in the header; the toggle is a button group, not a date picker).

## What's left

- Journey J-22 (Transparent, rule-based, expanded universe ~500 names) failing — externally data-walled (no reachable no-key OHLCV+market-cap feed); recorded honestly blocked (NA), non-halting/non-vetoing per the re-scoped goal; auto-heals via the committed finish runbook on operator confirmation of a reachable egress.
- Journey J-23 (Multi-timeframe bars — intraday seed + timeframe-aware pipeline) failing — same data wall (needs fresh intraday fetches); recorded honestly blocked (NA), non-halting.
- Journey J-24 (Timeframe selector on the stock chart, 1D/1h/15m/5m) failing — depends on J-23 intraday data; recorded honestly blocked (NA), non-halting.
- Minor cosmetic advisory (carried, non-blocking): the Data Manager page subtitle still reads "grow the System Health evidence" — stale prose after System Health's retirement; no dangling route; tidy in a future touch.

## Next step

Halt — goal achieved. No outstanding buildable work: the entire buildable set (J-01…J-21, J-25…J-32 = 29 journeys) is passing with directly-verified evidence, anti-goals hold, and coherence passes. The three remaining journeys (J-22/J-23/J-24) are externally Yahoo-429 data-walled and explicitly non-halting/non-vetoing per the re-scoped goal — they auto-heal via the committed finish runbook (no code change) once an operator confirms a reachable no-key OHLCV+market-cap (J-22) / intraday (J-23/J-24) egress. Do NOT autonomously re-probe them. If the session is ever resumed, only a lean re-verify is warranted — there is nothing left to build.

## Quick verify

From `reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-19-what-to-click.md`:

1. Open `http://localhost:3835/research` in your browser.
2. Note the current sample sizes: the "Observations:" number above the Decile table and the "Pooled occurrences (Nd):" number in the Setup & Pattern Lab.
3. Click the **As of date** button in the Analysis-mode control.
4. In the top header bar, open the global **as-of date** dropdown (the only date control on the page) and pick one of the earliest dates near the bottom of the list.
5. Re-read the "Observations:" number and the "Pooled occurrences" number (both should be smaller, with **NA** in thin cells — never a made-up number).

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever-iter-19.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-19-dev.md |
| Frontend handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-19-frontend.md |
| Review | PASS | reports/reviews/goal-i_can_see_the_wealthy_future_forever-iter-19-review.md |
| Browser QA | PASS | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-19-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-19-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-19-user-visible-changes.md |
| What to click | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-19-what-to-click.md |
| UI surface map | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-19-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-19-ui-test-plan.md |
| QA | PASS | reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-19-qa.md |
| Goal evaluation | GOAL_ACHIEVED | runs/goal-session-i_can_see_the_wealthy_future_forever/iter-19/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever/state/journey-history.json |
