# Iteration Summary — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-06-22
**Iteration:** 45

## In plain words

**What you can do now:** See the live dashboard with a single, de-duplicated market chart showing phase bands and a severity-velocity line; step to any past snapshot date and have every surface update instantly; view a stock leaderboard showing only stocks that were tradable on each selected past date; open any stock for a score breakdown with colour-graded forward-return and max-drawdown columns; sort and filter every leaderboard; save stocks to a watchlist; check the Data Manager for a membership-growth timeline with Year/Month filters and pagination, a coverage diagnostic, and import tracking; and explore the Research section — now a hub of seven individually-loaded labs — covering factor analysis, event studies, regime patterns, downtrend opportunities, recovery-turn signals, and a new Severity-velocity study that answers whether rising or falling market stress predicts the next move, each with honest caveats and sample drill-downs.

**What changed this time:** The Research section now opens as a hub of seven individually-loaded labs instead of one page that triggered four heavy computations at once. Each lab lives on its own address, so opening one no longer slows down the others. A brand-new Severity-velocity study answers the question "does rising market stress under a given regime predict the next move?" — it shows a 3-by-3 grid of average forward returns grouped by regime type and whether stress is rising, flat, or falling, across multiple time horizons. The study honestly reports that on the available data, rising stress under a bearish regime preceded a bounce rather than a continuation, and explains why the finding should be treated with caution. The caching layer for two other studies (multi-factor combination and regime pattern) was also upgraded so repeat visits are fast.

**What's next:** Next, a clean re-run of the product on a fresh backend will confirm the relocated labs load their figures correctly and a full suite of automated tests passes cleanly — completing the verification needed to close out the final two journeys.

## Headline

Research section split into a 7-lab hub + new Severity-velocity × Regime study built and passing; lean live re-verify owed

## Direction

**Signal:** improving
**Why:** J-103 (Severity-velocity × Regime study) and J-104 (research-labs route-split + caching) both flipped from failing to passing this iteration, confirmed on live rendered evidence for J-103 and by isolated tests for J-104. The browser-QA FAIL verdict is a false picture — the evaluator root-caused all four P1 failures as a wrong-param curl (UT-09) and a saturated live backend from concurrent heavy fetches (UT-03/UT-04/UT-24/UT-25), neither of which reflects a code defect. No prior-passing journey regressed.

**Trend (last 5 iters):**
- Newly passing this iter: J-103, J-104
- Newly passing in last 5 iters total: J-101, J-102 (iter-44), J-103, J-104 (iter-45)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none (the lone ever-recorded iter-20 minor magic-number stays resolved since iter-21)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** J-103 and J-104 are genuinely BUILT and CORRECT — the browser-QA FAIL (19/25) is NOT a code regression. All four P1 failures are explained: UT-09 is a selector false-negative (QA curled `?asof=` instead of the endpoint's `?as_of=`; the engine's as-of filter is proven by `test_as_of_filter_shrinks_pool_no_recompute` passing), and UT-03/UT-04 (plus UT-24/UT-25 skips) are a SATURATED/hung live backend (PID 72189, still consuming ~25% CPU at evaluation time from earlier event-study hammering), not iter-45 code — `test_research.py`+`test_samples.py` (event-study, downtrend, recovery, samples count-coherence) pass 108/108 in isolation. This is NOT GOAL_ACHIEVED only because the standing flushed-GREEN full-suite gate is unmet and a clean live re-render is owed.

## What was done

- Built `compute_severity_velocity_study` — a read-only grouping of stored SPY forward returns by regime family and severity-velocity sign, served via the existing `EventStudyCache` + `_dataset_version` idiom under a new `_SEVERITY_VELOCITY_SUBJECT` sentinel (no new table)
- Added `GET /api/research/severity-velocity` endpoint with `horizon`/`as_of` params, 422 on bad horizon, 503 on no data; new samples cohort kind `severity-velocity` so each N= chip reproduces its exact cohort
- Added new config block `research.severity_velocity` with config-backed regime family and velocity-sign vocabularies; cross-validator ensures families reference real labels; no magic numbers
- Cached `compute_factor_combination` and `compute_regime_setup_pattern_study` via the existing `EventStudyCache` pattern; byte-identical figures; cache refreshes on dataset change (J-104a)
- Bounded the full `select(ScannerRun)` scan in `_downtrend_opportunity_observation_set` with `where(ScannerRun.asof_date <= as_of)`; figures stay byte-identical (J-104b)
- Split the monolithic `/research` page into a 7-card hub + seven lazy sub-routes (`/research/factor-lab`, `/research/factor-combination`, `/research/event-study`, `/research/regime-setup-pattern`, `/research/recovery-turn-edge`, `/research/downtrend-opportunity`, `/research/severity-velocity`); at most one heavy fetch fires per page; hub is 2.3 kB down from ~25 kB monolith
- Verified J-103 live: matrix renders (3 families × 3 velocity signs), verdict states "NOT supported" + "bounce, not continuation" + all four caveats verbatim, N= chip (n=241 risk-on/rising) opens `/research/samples` with matching total; targeted tests 26/26 + API tests 29 passed; `tsc --noEmit` clean, `next build` successful

## What's left

- J-103 As-of mode not yet confirmed live in browser (UT-09 was a wrong-param curl false-negative; needs positive rendered evidence of N values decreasing at an early date)
- J-29 (Setup & Pattern event study) + J-25/J-26 (factor lab) figures not re-rendered on a quiet backend (UT-03/UT-04 were backend-saturation failures, not code regressions)
- Full pytest suite not yet flushed to `0 failed, EXIT 0` — suite hung at ~98% on warm-up/watchlist contention tail (`test_warmup.py` + `test_watchlist_persistence.py`), not in touched research code (test_research + test_samples 108/108 pass in isolation)
- Live re-render owed for the relocated labs (byte-identical figures + N= drill-downs confirmed on a quiet backend)
- J-22 / J-23 / J-24 remain honestly blocked-NA (data-walled; non-vetoing per goal.md:105-108)

## Next step

iter-46 LEAN live re-verification + flushed-suite confirmation (NO code rework — J-103/J-104 are correct, byte-identity + as-of filter proven by isolated tests). (1) FIRST restart the hung live backend cleanly (kill PID 72189; bring up :8835 and WAIT for `GET /api/health` "ready" so warm-up finishes) — the iter-45 browser-QA ran against a saturated backend, which is the sole cause of UT-03/UT-04/UT-24/UT-25. (2) PLAN the Playwright fallback up front (Chrome MCP CDP has emptied/contended the dir on iters 38/39/40/42/45); md5sum the dir FIRST; NEVER concurrently probe heavy /research/* endpoints (one heavy fetch at a time — the J-104 invariant; MEMORY pool-exhaustion). (3) Re-capture the relocated labs on a QUIET backend with figures+N= chips actually rendered (not the "Backend unavailable" banner): J-29 event-study (UT-04 re-do), J-25/J-26 factor-lab (UT-03 re-do), J-77 regime-setup-pattern, J-91 downtrend, recovery-turn-edge; assert each relocated lab's figures are byte-identical to pre-split + its N= drill-down still works (J-51/J-65 count-coherence). (4) Re-verify J-103's As-of mode in the BROWSER by toggling "As of date" at ?asof=2022-12-31 and confirming the rendered N values DECREASE (do NOT re-curl `?asof=`; the correct param is `?as_of=`, which the frontend sends automatically) — close the UT-09 false-negative with positive rendered evidence. (5) Required-still-passing live smoke: J-18 (0 native date inputs, CRITICAL), J-07 (Risk-Off → 0 Actionable, CRITICAL), J-101/J-102/J-97/J-98 (Dashboard cross-view + severity-velocity line/tooltip unchanged). (6) Suite gate: confirm the FLUSHED full-suite `0 failed, EXIT 0` from the pump's nohup-async re-run on the now-quiet host BEFORE any GOAL_ACHIEVED candidacy — re-run any isolated test_warmup.py / test_watchlist_persistence.py E/F (the documented slow-boot/warm-up contention flake) before attributing it. After the relocated labs + J-103 As-of re-render green on a quiet backend AND the full suite flushes 0-failed, the next evaluation is a sound GOAL_ACHIEVED candidate: every buildable Must-have (J-01..J-21, J-25..J-104) positive-evidenced; J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing per goal.md:105-108). Do NOT re-trigger the J-85 kind:rebuild (~11h destructive; data is correct).

## Quick verify

From `reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-what-to-click.md`:

1. Open `http://localhost:3835/research` — expect a card grid of seven named lab cards with no heavy study matrix or analysis table on the page.
2. Click the severity-velocity card — expect browser navigates to `/research/severity-velocity` and a 3×3 matrix (Risk-on/Neutral/Risk-off rows, Rising/Flat/Falling columns) loads with a horizon selector and verdict card.
3. Click "5d" in the horizon selector — expect numeric values in the matrix cells update without a page reload.
4. Scroll to the verdict card — expect text contains "NOT supported" and mentions "survivorship", "bull-dominated", and "underpowered" caveats alongside "bounce, not continuation".
5. Click any non-zero N= chip — expect a new tab opens at `/research/samples` with a human-readable description and a total count matching the chip label.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-review.md |
| Browser QA | FAIL | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-ui-test-results.md |
| What to click | — | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-what-to-click.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/iter-45/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/journey-history.json |
