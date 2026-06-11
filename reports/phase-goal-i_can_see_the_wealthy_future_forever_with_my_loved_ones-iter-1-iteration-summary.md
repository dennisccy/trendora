# Iteration Summary — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-06-11
**Iteration:** 1

## In plain words

**What you can do now:** See the latest market-regime score and top-ranked stocks on a dashboard; browse and filter 122 ranked stocks by setup, sector, or pattern; explore theme and sector leaderboards; open any stock for a full explainable score breakdown with price chart; step back to any past date with the global date switcher and every score, regime label, and ranked list reflects that exact historical snapshot; view walk-forward backtest evidence with honest NA values and control groups; save stocks to a persistent watchlist; manage price-data imports from multiple providers; explore factor-effectiveness research in the Factor Lab. All dates throughout the app now display in consistent YYYY-MM-DD format regardless of where you are browsing or what browser locale your device uses. When entering dates on the Data Manager page, you type them directly as text and the app immediately tells you if the format is wrong before you can submit.

**What changed this time:** Every date shown across the entire app — in the date switcher, on stock pages, on scanner run lists, in chart tooltips, in job cards, in coverage summaries — now always reads in YYYY-MM-DD format no matter what country or locale settings your browser uses. The date entry fields on the Data Manager page were replaced with text boxes that validate your input immediately: if you type something like "13/40/2026" or "10/06/2026", you see a clear error message and the submit button stays disabled until you type a valid date. Work also began on making historical date links shareable: when you select a past date, the URL already updates to include that date (so you can copy it), and pasting an invalid date link degrades safely to the latest view — but reloading or opening the link in a new tab does not yet preserve the date in the URL. That last step is the target for next time.

**What's next:** Fix the shareable historical date link so that reloading the page or opening the URL in a new tab keeps the selected past date visible in both the switcher and the URL bar.

## Headline

Shared ISO date formatter + validated `/data` text inputs land (J-42 passing); J-43 deep-link URL persistence partially working, reload/fresh-tab leg root-caused.

## Direction

**Signal:** improving
**Why:** J-42 (uniform ISO date presentation) flipped from partial to fully passing this iteration with browser-verified evidence across every date surface. J-43 (deep-linkable as-of) moved from failing to partial — interactive serialization, degradation, and restore-into-control all confirmed working; only the reload/fresh-tab URL persistence leg fails, with a precise, one-file root cause already identified in `asof-provider.tsx`. No regressions; all five required-still-passing journeys (J-06, J-13, J-17, J-18, J-20) re-verified green with fresh per-journey screenshots. The baseline's full-pytest debt was also paid (622/4/0).

**Trend (last 2 iters):**
- Newly passing this iter: J-42
- Newly passing in last 2 iters total: J-42
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: none
- Iters with no journey state change: 0 of last 2

**Latest evaluator reasoning:** J-42 (uniform ISO date presentation) is newly passing with strong, fresh evidence: a single shared formatter (`apps/frontend/lib/dates.ts`) is now the format authority across every date surface, the four `/data` native date pickers became validated ISO text inputs (invalid `2026-13-40` / `10/06/2026` show an inline error and block submit), and the coherence audit independently confirmed no per-component format literal remains. J-43 (deep-linkable as-of) moved from failing to partial: interactive selection writes `?asof=D`, invalid params degrade safely, latest removes the param, and a deep-linked `?asof` restores into the one global control — but the URL is stripped after hydration on reload / fresh tab / post-click-through, so deep links are not yet durable (browser-QA FAIL with a precise root cause). All five required-still-passing journeys (J-06, J-13, J-17, J-18, J-20) re-verified green with fresh per-journey screenshots, and the baseline's full-pytest debt was paid (622 passed / 4 skipped / 0 failed).

## What was done

- Created `apps/frontend/lib/dates.ts` as the single ISO date format authority — exports `ISO_DATE_FORMAT`, `formatIsoDate()`, `formatIsoDateTime()`, and `isValidIsoDate()` (calendar-valid, locale-proof)
- Swept every date-display surface through the shared formatter: as-of switcher, historical indicator, stock/sector/theme/watchlist/backtest/scanner-run pages, evidence-panels, and chart tooltip/crosshair via `localization.timeFormatter`
- Replaced four native `<input type="date">` pickers on `/data` with validated ISO text inputs (`IsoDateInput`): inline error on bad format, submit blocked while invalid; fetch/remove forms both covered
- Extended `asof-provider.tsx` with `AsOfUrlSync` (Suspense-wrapped) to serialize the global as-of state to `?asof=D` in the URL and restore it on load; interactive legs and degradation paths verified passing
- Re-verified five required-still-passing journeys (J-06, J-13, J-17, J-18, J-20) with fresh per-journey screenshots
- Ran the full backend pytest suite (622 passed / 4 skipped / 0 failed, 36m39s) — closing the baseline collect-only gate gap
- Verified J-43 reload/fresh-tab URL-persistence leg failing with root cause confirmed: serialize effect in `AsOfUrlSync` omits `searchParams` from its dependency array

## What's left

- Journey J-43 (Deep-linkable as-of — `?asof` URL serialization) partial: reload / fresh-tab / click-through URL-preservation legs still failing; fix is surgical (`searchParams` missing from serialize effect deps in `asof-provider.tsx`)
- Journey J-44 (Dashboard major-indexes chart with regime bands) failing — no endpoint or UI card yet; planned iter-2
- Journey J-45 (Market-regime bands behind the stock-detail chart) failing — depends on same stored-regime-history endpoint as J-44; planned iter-2
- Journey J-46 (Fetch + backfill materially faster — parallel, vectorized, benchmarked) failing — no worker pool, no benchmark script yet
- Journey J-47 (Full ≥100-term glossary + inline term help) failing — methodology page has ~32 items, no categorized catalog or inline tooltips yet
- Journeys J-22, J-23, J-24 blocked-NA (data-walled, non-halting per goal definition)

## Next step

Iter-2 **lean**, primary target: **finish J-43** — fix the serialize-effect stale-`searchParams` dependency in `apps/frontend/components/asof-provider.tsx` (root-caused above; a small, surgical change) and re-run the reload / fresh-tab / click-through legs in browser QA. The fix is small enough that the decomposer may bundle it with starting **J-44 + J-45** (stored-regime-history + server-side index-series endpoints per the blueprint TARGET rows), which was the planned next target and whose QA will navigate via the now-working `?asof` deep links. Required-still-passing set should again include J-13/J-18/J-06. The decomposer should flip the **J-42** blueprint annotation to built (J-43 stays TARGET until the reload/fresh-tab legs pass). Also: drop the `npm run lint` DoD line — ESLint is genuinely not installed in this project; `tsc --noEmit` is the working frontend gate.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1-dev.md |
| Browser QA | FAIL | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/iter-1/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/journey-history.json |
