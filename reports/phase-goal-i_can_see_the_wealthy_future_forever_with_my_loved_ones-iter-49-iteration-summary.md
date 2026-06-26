# Iteration Summary — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-06-26
**Iteration:** 49

## In plain words

**What you can do now:** See a live market dashboard with regime score, severity panel, and regime-aware tooltips; browse a stock leaderboard that now includes a sortable "proximity to 52-week high" column right after the Risk column; open any stock for a full score breakdown showing the same proximity percentage as the leaderboard; step to any past date and have every surface update; save stocks to a watchlist; check the Data Manager for a membership-growth timeline with filters, pagination, and coverage diagnostics; and explore all seven Research labs — Factor Lab (decile-sorted scores and rank-IC on 598,000 observations), multi-factor combination, Setup and Pattern event study, Severity-velocity × Regime study, Downtrend Opportunity, Recovery-Turn Edge, and Regime × Setup × Pattern study. The readiness badge now correctly shows Ready, Initializing, or Unavailable whether you open the app at localhost or your machine's local network address.

**What changed this time:** The stocks leaderboard now has a sortable "Proximity to 52w high" column right after Risk — it shows how far below its one-year high each stock is trading, as a percentage, and you can click the header to sort the whole list by it. Stocks with too little history show "NA" and always sort to the bottom. The Leadership score breakdown on any individual stock's page now also shows that same distance percentage instead of an opaque internal rank, so the two views always agree. And the status badge in the top bar now correctly reaches "Ready" even when you open the app using your machine's local network address — it was previously stuck on "Backend unavailable" in that scenario.

**What's next:** Next we'll build a comprehensive all-factors view in the Factor Lab — showing rank correlation and decile returns for every tracked factor at once — which will complete all the planned capabilities.

## Headline

Added sortable 52w-high proximity column to Stocks leaderboard and fixed LAN-address readiness badge (J-106, J-108)

## Direction

**Signal:** improving
**Why:** J-106 and J-108 both flip from unknown to passing on evaluator-viewed live browser-QA evidence (12/13 PASS, 1 non-blocking SKIP). Zero regressions this iteration. J-107 is the sole remaining unbuilt Must-have and is the natural target for iter-50, making the path to GOAL_ACHIEVED concrete and close.

**Trend (last 5 iters):**
- Newly passing this iter: J-106, J-108
- Newly passing in last 5 iters total: J-103 (iter-45), J-104 (iter-45), J-29 (iter-47, restored), J-26 (iter-47, restored), J-25 (iter-48, restored), J-105 (iter-48), J-106 (iter-49), J-108 (iter-49)
- Regressions in last 5 iters: iter-46 — J-25, J-26, J-29 (all fully restored by iter-48)
- Anti-goal violations in last 5 iters: none (the lone ever-recorded violation was iter-20, minor, resolved since iter-21)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** J-106 (Proximity-to-52w-high leaderboard column) and J-108 (honest readiness-badge fix) both flip unknown → passing on genuine, evaluator-VIEWED live browser-QA evidence (12/13 PASS, 1 non-blocking SKIP). The diff matches the coherence snapshot exactly and is anti-goal-clean: a frontend-only re-display of the already-served `high_proximity` component (no new `/api/stocks` field) plus a host-aware client base + dev-only CORS widening; main.py changed only its CORS factory. This is NOT a GOAL_ACHIEVED candidate — J-107 (the all-factors Factor Lab table) is the sole remaining unbuilt, NOT-data-dependent buildable Must-have and was deliberately deferred to iter-50. Progress made, zero regressions, COHERENCE-PASS → CONTINUE.

## What was done

- Added "Proximity to 52w high" sortable column to the Stocks leaderboard (`/stocks`) — frontend-only re-display of the stored `high_proximity` Leadership component value; NA-last comparator; `aria-label` sort control; config-backed glossary tooltip from `config.yaml:1212`
- Updated the Leadership component breakdown (`component-breakdown.tsx`) to render the raw distance percentage for `high_proximity` instead of the prior opaque percentile rank, making the detail view byte-identical to the new leaderboard column (single source)
- Added host-aware `resolveApiBase()` helper (`lib/api-base.ts`) so every data fetch uses the correct backend host when the page is opened at a non-localhost (LAN-IP) address
- Diagnosed and fixed J-108 readiness-badge root causes: wrong fetch host (module-load-time `API_BASE` constant sent to viewer's own `localhost`, not the dev-host) and CORS block (LAN-IP origin not in allow-list)
- Added `create_app()` factory + optional `CORS_ORIGIN_REGEX` to `main.py`; `scripts/dev.sh` now adds the LAN-IP frontend origin and sets a dev-only private-LAN CORS regex (production allow-list unchanged)
- Verified 12/13 browser tests PASS (UT-05 SKIPPED — no NA row in seed; NA-last logic mirror-verified); re-confirmed J-01, J-06, J-07, J-18, J-40, J-48, J-75, J-80, J-104 all still passing

## What's left

- Journey J-107 (Factor Lab — all-factors Rank-IC + risk-adjusted table with expandable per-factor decile sort) — `unknown`, not built this iter, sole remaining unbuilt buildable Must-have, blocks GOAL_ACHIEVED
- J-22 (Transparent rule-based expanded universe ~500 names) — data-walled, blocked-NA, non-vetoing per goal.md:105-108
- J-23 (Multi-timeframe bars — intraday seed + pipeline) — data-walled, blocked-NA, non-vetoing
- J-24 (Timeframe selector on the stock chart) — data-walled, blocked-NA, non-vetoing

## Next step

iter-50 FULL — build J-107 (Factor Lab all-factors Rank-IC + risk-adjusted table with expandable per-factor decile sort; supersedes the single-factor dropdown view, retires the per-regime effectiveness table from that view). This touches the cached-aggregate / streamed research read path — the iter-46/47/48 OOM-sensitive area — so: build on `EventStudyCache` + `_dataset_version` (byte-identical figures), keep the read path streamed/column-projected per J-105 (no unbounded `select(...).all()`), order ScannerResult reads by `(run_id, id)` not bare `id` (the iter-48 temp-sort / disk-full lesson; host disk ~93% full), and register any new table in test_db.py's expected-tables guard (iter-12/20 trap). Required-still-passing: J-25/J-26/J-29/J-77/J-91/J-103 (the research labs J-107 reorganizes), J-51/J-63/J-65 (N= sample coherence), J-104 (labs load reliably), J-06/J-18/J-07 (CRITICAL), J-106/J-108 (this iter). Gate iter-50's GOAL_ACHIEVED candidacy on the FLUSHED full-suite `0 failed, EXIT 0` (pump nohup-async; never block the evaluator; NEVER concurrently probe heavy /research while load-testing — pool-exhaustion lesson). Evidence-hygiene: PLAN the Playwright fallback up front; md5sum the dir FIRST; resolve sort/decile/N= controls by aria-label not text(). After J-107 lands green on live evidence with a flushed-GREEN suite + COHERENCE-PASS + zero regression, the next evaluation is a sound GOAL_ACHIEVED candidate (J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing per goal.md:105-108).

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-dev.md |
| Review | PASS | reports/reviews/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-review.md |
| Browser QA | PASS | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-user-visible-changes.md |
| What to click | — | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-what-to-click.md |
| QA | PASS | reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-qa.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/iter-49/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/journey-history.json |
