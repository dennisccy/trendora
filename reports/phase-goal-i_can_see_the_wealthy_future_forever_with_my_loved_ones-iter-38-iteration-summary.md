# Iteration Summary — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-06-20
**Iteration:** 38

## In plain words

**What you can do now:** See a live dashboard with a regime score and market-phase panel, browse a phase history timeline with dated downtrend episodes and an optional retrospective view, check the recovery-turn edge and downtrend opportunity studies on the Research page, step to any past snapshot date and have every surface update instantly, view a stock leaderboard that shows only the stocks that were actually tradable on that past date (empty before late 2021, roughly 544 stocks today), open any stock for a score breakdown with colour-graded forward-return and drawdown columns, sort and filter every leaderboard, click any sample count to see the exact stored observations, save stocks to a watchlist, and check the Data Manager for membership growth, coverage counts, import progress, and a macro-series feed.

**What changed this time:** The dashboard home page has been reorganised to show the most important summary numbers first — a compact market-regime score and a compact market-phase severity figure are now the first things you see, with a hide-able "More detail" section below for the breadth metrics and sector/theme cards. A new two-pane chart that overlays market-phase colour bands with regime bands on the same timeline was built and placed on the page, but a technical caching issue means the phase bands in the lower chart panel are currently empty — that fix is coming next.

**What's next:** Fix the caching issue so the two-pane market-phase chart shows the coloured phase bands, severity line, and bear-probability line in the bottom panel, then capture live visual proof of both the chart and the reorganised dashboard.

## Headline

Dashboard at-a-glance restructure + two-pane regime×phase cross-view chart built; bottom pane blocked by stale-cache schema bug

## Direction

**Signal:** holding
**Why:** J-97 and J-98 are brand-new journeys registered for the first time this iteration — neither was ever passing, so there is no regression. No prior-passing Must-have broke. However, no journey moved to passing either: J-97 fails live due to a precisely root-caused stale-cache schema-versioning defect (the market-phase cache key does not include a payload-schema component, so the pre-iter-38 row for the live as-of is served without `timeline_full`), and J-98 is held partial for lack of any live visual evidence (Chrome MCP timed out, evidence directory empty). The fix is one-step and tractable; direction is not improving yet but also not stalling (meaningful code shipped and new journeys registered).

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-94 (iter-37), J-96 (iter-37) — both were regressed/partial and flipped to passing in iter-37; no newly passing in iters 34–36 beyond that
- Regressions in last 5 iters: J-94 regressed in iter-35 (CLOSED in iter-37)
- Anti-goal violations in last 5 iters: none (the lone ever-recorded violation, iter-20 minor magic-number, stays resolved since iter-21)
- Iters with no journey state change: 1 of last 5 (iter-36 — cause-fixed but held, no journey flipped status)

**Latest evaluator reasoning:** iter-38 built J-97 (backend `?full=true` market-phase serialization + a two-pane synced regime×phase cross-view chart) and J-98 (Dashboard at-a-glance restructure), coherence COHERENCE-PASS, review PASS. But J-97's primary deliverable FAILS live: the evaluator independently confirmed `GET /api/market-phase?full=true` at the current as-of returns no `timeline_full` key, so the bottom pane renders no phase bands / severity line / P(bear) line — a stale-cache schema-versioning bug. J-98's restructure is built and DOM-confirmed but held PARTIAL because it embeds the broken J-97 chart and the evidence dir is empty (Chrome MCP timed out — zero screenshots).

## What was done

- Added `?full=true` query param to `GET /api/market-phase`; the extended payload carries `timeline_full` (full causal history series) verbatim from the existing `compute_market_phase` derivation; default (`full=false`) response stays byte-identical
- Added `market_phase_full_cached` pass-through and `market_phase_default_payload` strip-helper so the card endpoint is unaffected
- Built new shared `lib/phase.ts` (one phase-label → design-token colour mapping, replacing private duplicates), `phase-band-primitive.ts` (config-coloured step-function band for lightweight-charts), and `phase-cross-view-chart.tsx` (two-pane chart sharing one time scale: pane 0 = regime bands + index lines, pane 1 = phase bands + severity line + P(bear) line)
- Built `phase-cross-view-card.tsx` hosting the chart with loading/empty/error states and a persisted hide toggle
- Restructured `app/page.tsx` (J-98): compact regime + phase/severity glance cards render first; cross-view chart below; breadth/sectors/themes/phase-detail cards moved into a collapsed, persisted "More detail" section
- Ran 6 targeted backend tests GREEN (full-mode byte-identity, `timeline_full` verbatim == engine, no smoothed/true-bear on full series, tail-invariance, honest-empty); `test_no_magic_numbers` + `test_db` PASS; `tsc --noEmit` EXIT 0
- Browser QA ran 13/20 (5 SKIPped — Chrome MCP CDP timeout; 2 FAIL — UT-09/UT-16 J-97 bottom pane empty due to stale-cache bug); full backend suite handed to pump nohup-async

## What's left

- Journey J-97 (Dashboard two-pane synced regime×phase cross-view chart) failing — stale-cache schema-versioning bug: `market_phase_cache` key lacks a payload-schema component; pre-iter-38 rows served without `timeline_full`; bottom pane empty
- Journey J-98 (Dashboard at-a-glance restructure) partial — DOM/source-confirmed but zero live visual evidence (Chrome MCP timed out, evidence dir empty); blocked until J-97 cache fix lands and a live browser-QA runs
- Journey J-99 (unbuilt Must-have — `/data` pagination + year/month filter) not yet started
- Journey J-100 (unbuilt Must-have — bounded-resource backend hardening + concurrency load test) not yet started
- Full backend pytest suite result not yet confirmed (nohup-async in-flight at iteration close)

## Next step

iter-39 **FULL** — fix the J-97 stale-cache schema-versioning defect, then capture genuine LIVE evidence for J-97 + J-98 (the iter-38 evidence dir was empty).

1. **Cache fix (backend, root cause):** `market_phase_cached` (`apps/backend/app/engine/market_phase.py:810-811`) serves a HIT for `(asof_key, dataset_version)` verbatim, but `_dataset_version` tracks DATA changes (backfill/removal) — NOT the payload SCHEMA. iter-38 added `timeline_full` to the payload without changing the dataset, so every pre-iter-38 cache row (including the live current as-of `2026-06-16` under unchanged `r1370-f3078889`) is served without `timeline_full`, and `market_phase_full_cached` (a pass-through) returns it. Fix by invalidating for the schema bump: add a payload-schema-version component to the `MarketPhaseCache` key (preferred — survivor-proof for future additive fields), OR clear rows whose payload lacks `timeline_full` / one-time prune pre-iter-38 rows. Assert: `?full=true` at the live as-of now serves `timeline_full` (causal, byte-identical to `compute_market_phase`'s `timeline_full`), and `?full=false` (card) stays byte-identical. Apply the same fix to the `retrospective` cache path if it shares the schema risk.
2. **LIVE browser-QA (this iter had ZERO screenshots):** with a working Chrome MCP **or the Playwright fallback** (iter-34 precedent — do not accept API/source-only evidence; iter-36 lesson), md5sum the evidence dir FIRST and reject blank/skeleton/byte-identical frames. Capture: J-97 bottom pane with phase-colored bands + 0–100 severity line + filtered P(bear) line over the same index lines + the as-of marker; the SYNCHRONIZED zoom as **two byte-DISTINCT before/after frames** (UT-10, skipped this iter); an early-as-of honest-empty bottom pane; J-98 first-paint compact summary + the More-detail expand (UT-12) + as-of-change updating both figures (UT-18).
3. **Required-still-passing live smoke:** J-18 (0 native date inputs; synced zoom adds no date state), J-07 (Risk-Off → 0 Actionable), J-06 (figures == served values; pane-1 series == card series for the overlap), J-44/J-49 (pane 0 unchanged), J-87/J-88 (card phase/severity/P(bear) unchanged), J-13/J-43 (as-of switch drives both panes).
4. **Suite gate:** hand the FULL backend pytest suite to the pump nohup-async; gate the next evaluator on the FLUSHED `0 failed, EXIT 0` line — never block on the in-flight stream (iter-11/29/37); re-run any single `test_warmup.py` / `test_data_manager_jobs_pipeline.py` F in isolation before attributing it.

After J-97/J-98 close green on LIVE evidence with COHERENCE-PASS and the suite GREEN, build the remaining buildable Must-haves J-99 (lean, `/data` pagination + year/month filter) then J-100 (full, bounded-resource backend hardening + concurrency load test). Only after J-97..J-100 all pass with a GREEN suite, zero regression, and COHERENCE-PASS does the next evaluation become a GOAL_ACHIEVED candidate (J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing per goal.md:105-108).

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38-dev.md |
| Review | PASS | reports/reviews/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38-review.md |
| Browser QA | FAIL | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/iter-38/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/journey-history.json |
