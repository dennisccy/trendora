# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-55 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-55
**Date:** 2026-06-27
**Agent:** developer
**Status:** complete

## What Was Built
- New lazy sub-route page `/research/regime-phase-factor` rendering the **Regime × Phase × Factor** lab
  (J-112): a ranked, filterable, paginated combination table over the `(regime-score decile × severity-score
  decile × factor decile)` interaction for a SELECTED factor, with paired forward-return + max-drawdown
  columns per horizon + `n`.
- New **Regime × Phase × Factor** tile on the `/research` hub (lucide `Boxes` icon), linking to the new route
  (deep-linkable, carries the global as-of via `useAsOfHref`).
- Controls: a **factor selector** (from the served config catalog), three **decile filters** (regime /
  severity / factor, each default "All"), **column sort** (NA-last both directions, headers resolvable by
  `aria-label`), **pagination at 30 rows/page** (page size read from the payload — config-sourced), and the
  shared **As-of vs All-history** mode toggle.
- Every combination's **`N=` chip** opens `/research/samples` in a new tab for the exact
  `(regime-decile, severity-decile, factor-decile, horizon)` cohort, pinned `view=pooled`.
- The view is **pinned to pooled** (no Episodes/Pooled toggle) on both the lab fetch and every chip, per the
  iter-53 whole-cross-section lesson.

## Files Changed
- `apps/frontend/app/research/_labs.tsx` -- added `RegimePhaseFactorPage` (+ `RegimePhaseFactorTable`,
  `RpfSortHeader`, `RpfDecileFilter`, `useRpfSort`, `sortRpfRows`, `RpfSortKey`, the pinned-pooled constant);
  reuses the existing `RegimeReturnCell` / `RegimeMddCell` cells, the `regimeCellAt`/`regimeCellIsNa`/
  `regimeCellValue` NA-last helpers, `SampleLink`, `CaveatBanner`, `ResearchControls`, `Select`.
- `apps/frontend/app/research/regime-phase-factor/page.tsx` (new) -- the lazy sub-route page.
- `apps/frontend/app/research/page.tsx` -- new hub tile (icon `Boxes`).
- `apps/frontend/app/research/samples/page.tsx` -- `describeCohort` branch for the `regime-phase-factor` kind.
- `apps/frontend/lib/api.ts` -- `RegimePhaseFactorRow` / `RegimePhaseFactorResponse` types +
  `fetchRegimePhaseFactor` (sends `as_of=` via `withAsOf`); extended `SampleCohort` with the new kind + the
  three decile fields.
- `apps/frontend/lib/samples-link.ts` -- `RegimePhaseFactorCohortParams` + its `buildSamplesHref` branch
  (`factor` + `regime_decile`/`severity_decile`/`factor_decile` + `view`).

## Tests Run
Command: `cd apps/frontend && npx tsc --noEmit`
Result: EXIT 0 (no type errors).

Note: `next lint` is not configured in this repo (interactive setup prompt); `tsc --noEmit` is the type gate
and passes. Browser/live verification is the dedicated browser-qa-agent step (servers left up on
backend :8255 / frontend :3255).

## Known Issues
- None observed at type-check time. The 3-way grid is sparse (many low-sample combinations) — handled with the
  config min-sample "NA + n" discipline + pagination, as designed.
