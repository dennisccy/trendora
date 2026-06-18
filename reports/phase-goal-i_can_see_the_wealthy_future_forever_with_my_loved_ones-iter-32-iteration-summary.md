# Iteration Summary — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-06-18
**Iteration:** 32

## In plain words

**What you can do now:** See a live market dashboard with a regime score, a phase & severity panel (Expansion/Pullback/Correction/Bear/Recovery + 0–100 severity + named component drivers + bear probability), a scrollable phase history timeline, and dated causal downtrend episodes. Toggle a clearly labelled full-sample retrospective view showing smoothed probability and true-bear dating for research purposes. See a recovery-turn signal and explore the Recovery-Turn Edge study on the Research page. Browse a new Downtrend Opportunity study that groups past market observations by the causal phase, severity, or bear-probability band at the time and shows which stocks held up best or fell hardest, along with per-horizon forward returns and downside risk figures — with a mandatory "research evidence only" label on the fell-hardest angle. See a Data Manager panel listing four macro data series (Treasury spread, unemployment, credit spread, dollar index) whose current availability and any optional config-controlled wiring to the phase score is visible at a glance. Step to any past snapshot date across any page, sort every leaderboard by forward-return or drawdown columns, search and filter by sector, theme, or pattern, and click any sample count to see the exact stored observations.

**What changed this time:** A new Downtrend Opportunity study appeared on the Research page. It groups the same walk-forward observations by the market phase, severity band, or bear-probability band that was in effect at the time, showing which stocks held up best and which fell hardest under each condition — along with the recovery-turn edge for that phase. Each row's sample count links to the exact stored observations. A new macro data panel appeared on the Data Manager page, listing four FRED economic series with their publication lags and proxy tickers; the panel shows clearly that all macro inputs are off by default and that the existing dashboard scores are unchanged.

**What's next:** Next we'll build the dynamic point-in-time universe resolver — a system that determines which stocks were eligible on each historical date based on price, trading volume, and how much history they had at the time, plus a membership timeline showing when each stock entered and left the universe.

## Headline

Downtrend Opportunity three-angle study + optional FRED macro feed land; full suite RED by exactly one stale guard.

## Direction

**Signal:** improving
**Why:** J-91 (Downtrend-conditioned Opportunity study) and J-92 (FRED macro feed, config-default-OFF) both newly pass with 23/23 live browser-QA and primary evaluator-viewed evidence, moving two more Must-have journeys from failing to passing. The full backend suite is held RED by exactly one stale over-strict guard tripped by J-92's correct additive `macro` key — the verbatim iter-20/23 additive-trips-blanket-guard pattern, not a regression. J-93/J-94/J-95/J-96 remain unbuilt but tractable.

**Trend (last 5 iters):**
- Newly passing this iter: J-91, J-92
- Newly passing in last 5 iters total: J-89 (iter-31), J-90 (iter-31), J-91 (iter-32), J-92 (iter-32)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none (the lone ever-recorded iter-20 minor magic-number stays resolved since iter-21)
- Iters with no journey state change: 1 of last 5 (iter-30, where J-89/J-90 stayed unknown due to Chrome being down)

**Latest evaluator reasoning:** J-91 and J-92 are genuinely passing with primary, evaluator-VIEWED evidence. The authoritative full suite is RED by exactly ONE stale failure — `test_api_data.py::test_get_data_overview_shape`, an over-strict exact-set guard tripped by J-92's correct blueprint-registered additive `macro` key on `GET /api/data` (the verbatim iter-20/23 additive-trips-blanket-guard pattern, NOT a regression). NOT GOAL_ACHIEVED regardless: J-93/J-94/J-95/J-96 are unbuilt buildable Must-haves.

## What was done

- Built `compute_downtrend_opportunity_study` in research.py: groups the existing enriched event-study observations by causal phase/severity/P(bear) band at snapshot date, returns three angles (held-up-best, fell-hardest labelled evidence-only, recovery-turn-edge reuse), per-horizon stats + honest low-sample NA
- Added `GET /api/research/downtrend-opportunity` endpoint and `KIND_DOWNTREND_OPPORTUNITY` samples kind; drill-down count-coherent same-instant in both Episodes/Pooled and All-history/As-of modes
- Built `FredProvider` with env-only key, publication-lag alignment (`published_date <= D`), no fabrication on missing key, URL-redacted error path (FRED key never leaks to job errors)
- Added standalone `MacroSeries` table and committed offline seed for four series (T10Y2Y, UNRATE, BAMLH0A0HYM2, DTWEXBGS) plus `^TNX`/`^DXY`/`^VXN` proxy price bars; every macro leg config-default-OFF so all existing figures are byte-identical unchanged
- Surfaced macro feed catalog on `/data` via additive `macro` block on `GET /api/data`; env-var NAME only shown, no key value
- Delivered `DowntrendOpportunityLab` three-angle panel on `/research` and `MacroFeedPanel` on `/data`; no new nav entry; conditioning controls + episodes/pooled + as-of/all-history toggles wired; survivorship and publication-lag labels present
- Full backend suite: 945 passed, 1 failed (stale exact-set guard in `test_api_data.py`), 4 skipped; not a regression
- Verified 23/23 browser-QA PASS; J-18 CRITICAL re-verified (0 date inputs on /research; new components add no date state)

## What's left

- Journey J-93 (dynamic point-in-time universe resolver — per-as-of-date screening by price + ADV + min-history) — failing, unbuilt
- Journey J-94 (min-history sufficiency gate + honest warm-up period) — failing, unbuilt
- Journey J-95 (backward-history / point-in-time membership data-dependent envelope) — failing, unbuilt; non-halting data-walled, non-vetoing
- Journey J-96 (membership timeline + survivorship/coverage labels) — failing, unbuilt
- Full backend suite still RED by one stale guard (`test_api_data.py::test_get_data_overview_shape`) — one-line fix needed before next GOAL_ACHIEVED candidacy
- J-22/J-23/J-24 — honestly blocked-NA (data-walled, non-vetoing per goal.md)

## Next step

iter-33 begins with reconciling the single stale guard, then the J-93/J-94/J-96 dynamic point-in-time universe cluster + J-95's data-walled envelope (FULL depth — backend engine + endpoints + the full pytest gate):

1. **Consolidation (one-line):** update `apps/backend/tests/test_api_data.py::test_get_data_overview_shape` to accept the additive `macro` key — either compare as a superset (`{...} <= set(payload)`) or add `"macro"` to the expected set, mirroring the iter-21/iter-24 additive-key reconciliation. Re-run the FULL suite to EXIT=0 (pump nohup-async; gate on the FLUSHED `0 failed, EXIT 0` line — never block the evaluator on the in-flight suite, iter-11 lesson).
2. **J-93/J-94/J-96** (per-as-of-date resolver screening price+ADV+min-history; min-history sufficiency gate + honest warm-up; membership timeline + survivorship/coverage labels) + **J-95** (backward-history / point-in-time-membership data-dependent envelope, non-halting blocked-NA). Required-still-passing: J-87/J-88 (consumed layer byte-identity), J-89/J-90/J-91 (the layer this cluster reads), J-06/J-18 (CRITICAL), J-29/J-32/J-63/J-51/J-65/J-77/J-82 (research labs + samples count-coherence).
3. **Perf/cache (advisory, fold in if cheap):** warm `downtrend_opportunity_cached` during background warm-up so the first cold request on a many-run host does not take ~5 min.

After the cluster lands green with the full suite GREEN, zero regression, and COHERENCE-PASS, the next evaluation is a GOAL_ACHIEVED candidate. J-22/J-23/J-24 stay honestly blocked-NA (data-walled, non-vetoing per goal.md lines 105-108).

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32-dev.md |
| Review | PASS | reports/reviews/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32-review.md |
| Browser QA | PASS | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/iter-32/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/journey-history.json |
