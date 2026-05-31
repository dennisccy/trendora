# Iteration Summary — goal-i_can_see_the_wealthy_future-iter-8

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-05-31
**Iteration:** 8

## In plain words

**What you can do now:** Open a daily dashboard showing the market's mood, breadth, the top sectors and themes, how many stocks are worth acting on, and the data date; browse and filter a ranked list of stocks, each with three plain-English grades (strength, buy-point quality, risk) and a one-line reason; open any stock's own page for its price chart, its themes, and the price level that would prove the idea wrong; rank investing themes and every sector and industry; trust that every score reads the same on every page; reopen any earlier trading day from a permanent scan history (including past downturns where it correctly flagged nothing worth acting on); pick any past trading day from a top-bar switcher to see the whole dashboard exactly as it stood then; check a System Health page that grades — with honest sample sizes and a fair control group — whether its high grades actually predicted better returns; and keep a personal watchlist that survives a restart.

**What changed this time:** You can now time-travel. A new drop-down in the top bar lets you pick any past trading day and see the entire dashboard — market mood, stocks, themes, sectors, and any stock's page and chart — exactly as it stood that day, with a clear amber "viewing a historical date" label so you always know whether you're looking at today or the past. Behind the scenes, the pages now load their numbers from the daily snapshot the app saved for that date instead of recalculating everything on each visit, so they stay fast and perfectly consistent.

**What's next:** Next we'll add a Backtest page where you pick a past date and see a scorecard of how that day's top-graded stocks actually performed over the following days, weeks, and months — measured against fair benchmarks.

## Headline

Time-travel the whole dashboard via a global as-of switcher; pages now serve from immutable saved snapshots.

## Direction

**Signal:** improving
**Why:** This iter re-pointed the five read endpoints (and `/bars` + watchlist) to serve canonical values from the persisted immutable snapshot, and added a global top-bar as-of switcher — landing **J-15** (snapshot-served reads) and **J-13** (global as-of switcher) as newly passing. All eleven previously-green journeys (J-01–J-11) held through the read-path re-point, the iteration's real risk, and no critical anti-goal was violated (coherence is COHERENCE-PASS). J-12, J-14, and J-16 remain unbuilt by design, with J-14 (Backtest) as the clear, tractable next target.

**Trend (last 5 iters):**
- Newly passing this iter: J-13, J-15
- Newly passing in last 5 iters total: J-05, J-07, J-08, J-09, J-10, J-11, J-13, J-15
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The keystone read-path consolidation landed cleanly: the five live read endpoints plus `/bars` and the watchlist now serve canonical values from the persisted immutable snapshot for a resolved as-of date (computed once, then read from storage — never recomputed per request), and a global top-bar as-of switcher time-travels the whole dashboard. J-15 and J-13 are newly passing, verified directly from on-disk evidence + source. No previously-green journey regressed and no critical anti-goal was violated; coherence is COHERENCE-PASS. This is not GOAL_ACHIEVED — the goal was re-opened with five new Must-haves and J-12, J-14, J-16 remain unbuilt by design → CONTINUE.

## What was done

- Added a global top-bar **as-of date switcher**: pick any stored trading day to time-travel the Dashboard, Stocks (list + detail), Themes, and Sectors; "Latest" restores the live view, and the chosen date persists across in-app navigation.
- Added an amber **"Viewing as-of D (historical)" indicator** (quiet "Latest" badge otherwise) plus per-page "Data as-of D" labels.
- **Re-pointed** the five read endpoints (`/api/dashboard`, `/api/stocks`, `/api/stocks/{ticker}`, `/api/sectors`, `/api/themes`) plus `/bars` and the watchlist to serve canonical values from the persisted immutable snapshot for the resolved date — no live recompute per request.
- Added an **as-of resolver** (`resolve_as_of_date` / `resolve_run` in `scanner.py`) that returns the stored snapshot for a date or creates it exactly once (INSERT-only, bars ≤ D), and a new `snapshot_serving.py` that reshapes stored rows into the existing payloads and maps bad dates to explicit 4xx/503 (no fabrication).
- Made the **as-of price chart** honest: `/bars` honors `as_of`, returning only bars ≤ D (no lookahead).
- Backend suite **196 passed / 0 failed** — including the keystone monkeypatch-to-raise no-recompute test, create-once immutability, and on-demand no-lookahead; frontend builds all 10 routes.
- Verified **2 target journeys (J-13, J-15) pass** browser QA (QA mode-2 self-healed and captured 4 distinct evidence PNGs; the dedicated browser-qa SKIPPED an 8th time on the standing harness flap).

## What's left

- Journey J-12 (Understand what each setup/pattern means — glossary + inline tooltips) failing — unbuilt, out of scope this iter.
- Journey J-14 (Backtest a past date and read its forward-test scorecard) failing — unbuilt; the recommended next target.
- Journey J-16 (VCP — detected, explained, filterable, forward-tested) failing — unbuilt.
- Known limitation: the selected as-of date lives in client state and survives in-app navigation, but a full browser reload returns to "Latest" (not a bookmarkable URL).
- Known limitation: the switcher only offers dates that already have a stored snapshot (the run-history dates); there is no free-form calendar to reach an arbitrary uncomputed date (the create-once path is exercised by tests, not the UI).
- Runner-script debt (NON-product): the dedicated browser-qa SKIPPED an 8th consecutive iteration on the HTTP-000/CORS flap, and the audit handoff is missing an 8th consecutive full-depth iter — both belong in the runner, not the spec.

## Next step

iter-9 at full depth — **J-14 (Backtest / Time-Machine + per-date forward-test scorecard).** It builds directly on this iteration's as-of resolver (`resolve_run`) plus the existing forward-testing engine (iter-6): pick a historical as-of date, render its full as-of scan from the canonical snapshot, and show a per-date forward-test scorecard — realized 1/5/10/20/60-day returns, excess vs SPY/QQQ/sector, and a random same-sector control — computed only from seed bars after D (no-lookahead), with sample size and partial/NA horizons shown honestly. This adds a new `/backtest` nav entry, so it will need `blueprint.reapproval-requested`. After J-14: J-16 (VCP detected pattern) then J-12 (config-backed glossary incl. the VCP entry) finish the new round. Separately (runner-owner debt, non-gating): finally make browser-qa own/await/self-heal its frontend with `CORS_ORIGINS` set to the frontend port, and emit the audit handoff from the runner script.

## Quick verify

From `reports/phase-goal-i_can_see_the_wealthy_future-iter-8-what-to-click.md`:

1. Open `http://localhost:3835/` in your browser.
2. Click the date drop-down in the top bar and read its options.
3. Select a past date (**D_OLD**) from the drop-down.
4. Click "Stocks" in the left sidebar.
5. Note NVDA's three scores (Leadership, Entry Quality, Risk) on `/stocks`, then click the NVDA row.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future-iter-8.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future-iter-8-dev.md |
| Frontend handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future-iter-8-frontend.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-i_can_see_the_wealthy_future-iter-8-review.md |
| Browser QA | SKIPPED | reports/phase-goal-i_can_see_the_wealthy_future-iter-8-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-i_can_see_the_wealthy_future-iter-8-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-i_can_see_the_wealthy_future-iter-8-user-visible-changes.md |
| What to click | — | reports/phase-goal-i_can_see_the_wealthy_future-iter-8-what-to-click.md |
| UI surface map | — | reports/phase-goal-i_can_see_the_wealthy_future-iter-8-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-i_can_see_the_wealthy_future-iter-8-ui-test-plan.md |
| QA | PASS | reports/qa/goal-i_can_see_the_wealthy_future-iter-8-qa.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future/iter-8/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future/state/journey-history.json |
