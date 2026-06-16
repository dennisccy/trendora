# Iteration Summary — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-06-17
**Iteration:** 25

## In plain words

**What you can do now:** See today's market regime and a ranked top-five themes strip on the Stocks leaderboard header; step back to any past snapshot date using always-visible back/forward buttons, optional keyboard arrow keys, or the calendar popover with year/month jump menus; open any historical date link and see the correct data from the very first moment the page appears — no flash of today's figures before switching; open any stock for an explainable score breakdown with a regime-banded price chart, a per-bar hover box, and realized forward returns at five horizons; sort and search the stock leaderboard by any column; filter by theme and expand member stocks as dated new-tab links; browse the Sectors leaderboard with every ETF named and mapped; see five forward-return columns on the Themes and Sectors leaderboards, colour-graded and sortable, matching Backtest exactly; run walk-forward backtest evidence with control groups; explore factor effectiveness, an event study, and a Regime x Setup x Pattern ranked study with filter dropdowns and correct NA-last sorting; click any sample count to open the exact stored observations; save stocks to a watchlist; and manage imports with live progress, stage-aware resume, per-date failure isolation, a multi-hue availability heatmap, reliable multi-month backfill, and a deliberate range-scoped data-removal flow.

**What changed this time:** When someone shares or bookmarks a link to a specific historical date and another user opens it in a new tab or reloads it, the page now shows the correct date's badge and navigation links from the very first moment — no brief flicker to today's data, and no browser console error. This was a behind-the-scenes rendering fix; no new data, page, or action was added.

**What's next:** Next we will add the ability to expand the universe of tracked stocks to roughly 500 names, with proper authentication to fetch market-cap data from the data provider.

## Headline

J-83 passes: historical deep links render SSR-correct with no hydration mismatch — server-seeded as-of for first paint.

## Direction

**Signal:** improving
**Why:** J-83 (server-aware SSR seeding for as-of deep links) is newly passing this iteration with live browser console evidence of zero hydration errors on direct-open, reload, and new-tab. No journey regressed and no anti-goal was violated. Three queued Must-have journeys (J-84, J-85, J-86) remain unbuilt, so the session is CONTINUE rather than GOAL_ACHIEVED, but progress is clear and tractable work remains.

**Trend (last 5 iters):**
- Newly passing this iter: J-83
- Newly passing in last 5 iters total: J-83 (iter-25), J-79, J-80 (iter-22), J-81, J-82 (iter-23)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** "J-83 verified beyond the report. The diff is exactly the 4 expected frontend files (middleware.ts new + layout.tsx/asof-provider.tsx/lib/dates.ts modified) with ZERO backend code change... Browser-QA 12/12 PASS with the load-bearing LIVE console check (a hydration mismatch is only observable at runtime): 'Hydration failed'/'server rendered HTML'/'did not match' all ABSENT on direct-open + reload + new-tab; badge 'Viewing as-of 2026-06-10 (historical)' with the lucide-history icon from first paint; all 10 sidebar links carry ?asof from server HTML."

## What was done

- Added a new Next.js App Router middleware (`middleware.ts`) that reads the `?asof` query param and forwards it as the `x-asof` request header to page routes — shape-validated `yyyy-MM-dd` only; no other param and no provider key forwarded.
- Made the server-component root layout (`app/layout.tsx`) async so it can read the `x-asof` header via `next/headers` and pass it as `initialAsOf` into `<AsOfProvider>`.
- Updated `AsOfProvider` to accept an optional `initialAsOf` prop; the existing single `asOf` lazy `useState` initializer now prefers that server-provided value over the client-only `readAsofFromUrl()` — closing the SSR/client divergence that caused the hydration mismatch.
- Added shared constants `ASOF_PARAM` and `ASOF_HEADER` to `@/lib/dates` so the Edge-runtime middleware and the client provider share one canonical literal.
- Verified zero backend code change; `tsc --noEmit` exits clean; `git diff --stat -- apps/backend` shows only pre-existing out-of-scope seed artifacts.
- Verified 12/12 browser QA tests pass including the load-bearing live console check (no "Hydration failed" on direct-open, reload, new-tab) and the critical J-18 single-date-selector invariant.

## What's left

- Journey J-84 (expand-universe market-cap fetch with Yahoo cookie+crumb auth — systemic auth failure must pause the resumable import) failing (unbuilt)
- Journey J-85 (confirm-gated regenerate-from-scratch snapshot rebuild + read-only coverage diagnostic — guards the Snapshots-immutable / seed-never-deletable / no-lookahead anti-goals) failing (unbuilt)
- Journey J-86 (max-drawdown columns from stored forward_returns, NA-honest, all surfaces including backtest and research) failing (unbuilt)
- Journey J-22 (transparent rule-based expanded universe ~500 names) — blocked-NA, data-walled; non-vetoing per goal.md
- Journey J-23 (multi-timeframe bars — intraday seed + pipeline) — blocked-NA, data-walled; non-vetoing per goal.md
- Journey J-24 (timeframe selector on the stock chart) — blocked-NA, depends on J-23; non-vetoing per goal.md

## Next step

Run J-84 at FULL depth (the cleanest next backend journey of the queued three; it touches the live YahooProvider market-cap auth path + the J-34/J-35 resumable-import machinery, so the full ~790-test pytest suite becomes the gate — hand it to the pump, nohup-async, and gate the next evaluator on the flushed `0 failed` summary line; never block the evaluator dispatch on the in-flight suite — iter-11 lesson). J-84 = expand-universe market-cap fetch authenticates with Yahoo (cookie + crumb), and a systemic auth failure pauses resumable (never silently omitting all candidates); its auth, pause-resumable, and zero-duplicate-fetch-on-resume legs are buildable/testable offline with an injected provider (a stub returning caps or raising 401/429) — only an actual successful real Yahoo screen (and thus J-22 fully green) is data-gated/non-halting. Then J-85 (confirm-gated regenerate-from-scratch snapshot rebuild + read-only coverage diagnostic — guard the Snapshots are immutable / seed never deletable / no-lookahead anti-goals hard) and J-86 (max-drawdown columns from the stored append-only forward_returns, no recompute in the read path, NA-honest, horizons from config). Required-still-passing each iter: the J-18 single-date-selector invariant, plus J-35/J-34/J-38 (J-84) and J-06/J-75/J-81/J-21/J-09 single-source byte-identity + the immutability/seed-safe set (J-08/J-39/J-69) for J-85/J-86. After J-84/J-85/J-86 land green with a GREEN full suite, zero regression, and COHERENCE-PASS, the next evaluation is a GOAL_ACHIEVED candidate (J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing).

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25-dev.md |
| Review | PASS | reports/reviews/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25-review.md |
| Browser QA | PASS | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/iter-25/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/journey-history.json |
