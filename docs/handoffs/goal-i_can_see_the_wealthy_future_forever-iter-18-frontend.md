# goal-i_can_see_the_wealthy_future_forever-iter-18 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-18
**Date:** 2026-06-04
**Agent:** developer
**Status:** complete

## What Was Built (UI)

On `/research` → Factor Lab → **"Multi-factor combination cohort"**:

- The comparison table now renders, in order: **Baseline (all names)** → each single-factor cohort →
  **Combined (composite rank-blend)** (the HEADLINE row, emphasized with `bg-surface-2` + semibold) →
  **Strict overlap (AND)** (the SECONDARY row, muted text). Columns are unchanged: Cohort / n / Mean fwd
  return / Median / Hit-rate / Risk-adjusted (downside).
- The **Combined (composite)** row is populated for a sensible selection (mean / median / hit-rate /
  downside-risk-adjusted / n) instead of perpetually NA. The **Strict overlap (AND)** row shows honest
  **NA + n** (via the existing `CohortCell` + `SampleSize`) when the exact intersection is empty — both
  visible in the same view (composite populated while strict-overlap NA).
- The "Add condition" / "Remove" controls are **payload-driven**: with `max_conditions` now 11 the user can
  add conditions up to **all 11 catalog factors** (no hard-coded cap in the UI — `atMax`/`atMin` read
  `data.max_conditions`/`data.min_conditions`).
- The section **hint text** now describes the composite rank-blend honestly: "the top {composite_quantile}
  of the pool by a {scheme}-weighted blend of the conditions' percentile ranks (a transparent ranking of
  stored values, NOT a fitted/ML model)", and that Strict overlap (AND) is the optional secondary column.
  The quantile label + weighting scheme are read from the echoed payload (config-driven, never hard-coded).

## Files Changed

- `apps/frontend/lib/api.ts` — `FactorCombinationResponse`: `combined` replaced by `composite` +
  `strict_overlap`; added `composite_quantile: QuantileOption` + `weighting: CompositeWeighting`. New
  `CompositeWeighting` interface. Re-format only — no cohort is computed client-side.
- `apps/frontend/app/research/page.tsx` — `CombinationTable`: row order (Baseline → singles → composite →
  strict_overlap), composite emphasized / strict_overlap muted, `data-testid="combination-row-{emphasis}"`
  added per emphasized row for QA; `CombinationLab`: updated hint text (config-driven blend labelling).

## Design / States

- Reuses the existing `Card` + `PanelTitle` section, the `combination-table` `<table>`, `CohortCell`,
  `SampleSize`, `EmptyState`, and skeleton — **no new component types**. Dense dark analytical table,
  monospace tabular-nums for figures, green/red return grading via palette tokens only.
- States handled (unchanged paths): loading (`CombinationSkeleton`/dim), backend-unavailable (error card —
  no fabricated cohorts), empty pool (`pool_n === 0` `EmptyState`), and per-cell NA + n for any
  low-sample/empty cohort (the composite is populated while the strict overlap may render NA).
- **No date/as-of control added (J-18):** the section reuses the page's shared `horizon` selector only; no
  second date state.

## Tests Run

`cd apps/frontend && npm run build` — compiled + typechecked clean (13 routes; `/research` 9.75 kB First
Load 126 kB). UI behaviour is covered by browser QA (J-26 on `/research`), not a unit suite.

## Notes for Browser QA

- Default load → assert the **Combined (composite)** row (`combination-row-composite`) is populated (n ≥ 30,
  numeric mean/median/hit-rate/risk-adjusted), distinct from Baseline; the **Strict overlap (AND)** row
  (`combination-row-strict_overlap`) renders.
- Add conditions up to (near) all catalog factors → composite stays non-empty (n > 0).
- Drive an empty-strict-overlap selection (e.g. the same factor Top **and** Bottom, or many factors) →
  composite populated AND strict-overlap = NA + n in the same shot (membership-driven NA, not horizon).
- J-18 re-verify: toggle the global as-of in-app (not hard reload) → the lab is byte-identical, zero
  `/api/research/*?as_of=` requests; exactly one date `<select>` on the page (none on `/research`). Per
  `react-controlled-select-needs-native-setter`, drive selects via native-setter + bubbling change event.
