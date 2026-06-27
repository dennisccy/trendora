# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-53 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-53
**Date:** 2026-06-27
**Agent:** developer
**Status:** complete

## What Was Built (UI)

A new **Regime Lab** page at `/research/regime-lab`, reachable in ≤2 clicks from the nav (Research hub tile →
page). It shows, as descriptive survivorship-biased evidence, how stocks' realized forward returns and
downside risk (max-drawdown) have differed across the market regime — grouped by the six regime labels and by
deciles of the 0–100 regime score — at 1/5/10/20/60-day horizons.

- **New hub tile.** A **Regime Lab** card (Gauge icon) added to the `/research` hub `LABS` array, deep-linkable
  and carrying the global as-of in its href (J-50). Visually identical to the sibling lab tiles.
- **By-regime-label table** (6 rows, config-driven from `data.regime_labels`): per config horizon, the mean
  realized forward return (return tokens) + paired mean max-drawdown (`lib/mdd-color` severity scale) + a
  count-coherent `N=` chip on each return cell. Sortable NA-last both directions on every numeric column.
- **By-regime-score-decile table** (D1…D10): a header **Rank-IC** row (regime score ↔ forward return per
  horizon, `RatioCell`), the decile's regime-score range at the default horizon (each horizon's own range on
  the return cell's hover), then per config horizon the paired (return, max-drawdown) cell + the `N=` chip.
  Sortable NA-last both directions.
- **As-of vs All-history toggle** (the shared `ResearchControls` analysis-mode toggle, J-32) that only
  FILTERS the observation set — the single global as-of, no second/page-local date control (J-18). No native
  `input[type=date]` on the page.
- **`N=` drill-downs** open `/research/samples` in a NEW tab (J-65) for the exact `(regime label |
  regime-score decile, horizon)` cohort, carrying `?asof` (J-50) and the `pooled` view + analysis-mode
  `scope` so the Samples "Total observations" equals the clicked n (J-51/J-65 count-coherence).
- **Honest states.** Loading skeleton (`LabSkeleton`), backend-unavailable card (`ResearchError`), empty
  state (`EmptyState`), and explicit muted **NA + n** for any low-sample / empty / null cell — never a
  fabricated number. Survivorship-bias / descriptive-evidence caveat banner (`ResearchCaveat`).

## Design system conformance

- Reuses the existing `/research` lab building blocks (`ResearchControls`, `ResearchCaveat`, `LabSkeleton`,
  `ResearchError`, `EmptyState`, `Card`, `PanelTitle`, `TermInfo`, `SampleLink`), the shared
  `returnClass`/`fmtPct` + `mddClass`/`fmtMdd` formatters, and the `FactorSortHeader`-style sortable-header
  pattern (resolved in tests by `aria-label`). Design tokens only — no hardcoded hex. Matches the iter-52
  Factor Lab table treatment (wide paired-column tables scroll horizontally via `overflow-x-auto`).
- Interactive elements (sort headers, `N=` chips, mode toggle) carry hover / focus-visible / active states
  inherited from the shared components.

## Working view note

The page fetches and drills with the **pooled** overlap-honesty view (every stock × snapshot tagged by THAT
snapshot's regime). The whole-universe Episodes collapse would degenerate to each name's first appearance, so
pooled is the meaningful cross-sectional regime study. No Episodes/Pooled toggle is exposed (the spec's page
controls are the As-of toggle, column sort, and `N=` chips). The view is carried verbatim into the `N=` chip
hrefs so the Samples counts stay coherent.

## Tests Run

- `node_modules/.bin/tsc --noEmit` — EXIT 0 (typecheck clean).
- Backend byte-identity + count-coherence (the figures the page renders) — green (see the dev handoff).
- Live render evidence is produced by the dedicated browser-qa-agent step (both servers kept up).

## Known Issues

- Same as the dev handoff: no frontend component unit test harness on this box (TS correctness gated by
  `tsc`); the Episodes view is intentionally not exposed on the page.
