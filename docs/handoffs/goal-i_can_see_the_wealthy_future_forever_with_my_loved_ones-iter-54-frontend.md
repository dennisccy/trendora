# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-54 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-54
**Date:** 2026-06-27
**Agent:** developer
**Status:** complete

## What Was Built

A new user-facing **Market Phase & Severity Lab** page at `/research/phase-severity-lab`, opened from a new
tile on the `/research` hub (≤2 clicks from nav, deep-linkable). It mirrors the iter-53 Regime Lab visually
and behaviorally; the only difference is the grouping subject (market-phase label + 0–100 severity score
instead of the regime score/label).

- **Two Card-wrapped wide tables** (`overflow-x-auto`):
  - **By market phase** — five rows (one per `config.market_phase.labels` value), per config horizon a paired
    (mean forward-return, mean max-drawdown) column + the count-coherent `N=` chip.
  - **By severity-score decile** — a header Rank-IC row (severity score ↔ forward return per horizon), the
    decile's severity-score range at the default horizon, then per horizon the paired return/MDD columns + the
    `N=` chip; D1…D10.
- **Colour-graded cells**: return tokens (`returnClass`) for the forward-return column; `mddClass` for the
  max-drawdown column. Explicit NA (never a fabricated number) for low-sample / empty / null cells.
- **Sortable** every numeric column NA-last in both directions (J-48/J-82 view-transform — reorders rendered
  rows only, recomputes/refetches nothing); headers resolvable by `aria-label` (`Sort by …`).
- **As-of vs All-history** toggle (J-32) that only FILTERS the observation set; the single global as-of stays
  the only date control (J-18) — no native `input[type=date]` on the page.
- **`N=` chips** open `/research/samples` in a NEW tab (J-65) for the exact `(phase label | severity decile,
  horizon)` cohort, with `?asof` carried via the J-50 href helper; the Samples "Total observations" equals the
  clicked n (count-coherent). View pinned `pooled` on BOTH the lab fetch and every chip (iter-53 lesson — the
  first-trigger Episodes collapse degenerates for a whole-cross-section study). NO Episodes/Pooled toggle.
- **Survivorship-bias / descriptive-evidence** caveats rendered in the SSR shell (`ResearchCaveat`).
- **States handled**: loading (`LabSkeleton`), warming (`WarmingState`), error / backend-unavailable
  (`ResearchError`), and honest empty/NA for thin or zero-n buckets.

## Files Changed

- `apps/frontend/app/research/_labs.tsx` — `PhaseSeverityLabPage`, `PhaseSeverityLabByLabelTable`,
  `PhaseSeverityLabDecileTable`; reuses the Regime-Lab cell/sort helpers (`RegimeSortHeader`,
  `RegimeReturnCell`, `RegimeMddCell`, `useRegimeSort`, `sortRegimeRows`, `regimeCellAt`, `RatioCell`,
  `PanelTitle`).
- `apps/frontend/app/research/phase-severity-lab/page.tsx` (new) — lazy sub-route page.
- `apps/frontend/app/research/page.tsx` — new **Market Phase & Severity Lab** hub tile (Thermometer icon).
- `apps/frontend/app/research/samples/page.tsx` — `describeCohort` branches for the phase-severity-lab kind
  (and the regime-lab kind, previously unhandled).
- `apps/frontend/lib/api.ts` — `PhaseSeverityLabHorizonCell` (reuses Regime cell types),
  `PhaseSeverityLabLabelRow`, `PhaseSeverityLabDecileRow`, `PhaseSeverityLabResponse`,
  `fetchPhaseSeverityLab` (sends `as_of=` via `withAsOf`); extended `SampleCohort` kind union.
- `apps/frontend/lib/samples-link.ts` — `PhaseSeverityLabCohortParams` + its `buildSamplesHref` serialization
  (`slice` + `view` + `phase`/`decile`).

## Test data-testids (for browser QA)

- Hub tile link: `research-lab-link-phase-severity-lab`.
- By-phase table: `phase-severity-label-table`; rows `phase-severity-label-row-<phase>`.
- By-decile table: `phase-severity-decile-table`; rows `phase-severity-decile-row-<n>`; rank-IC row
  `phase-severity-decile-rank-ic-row`.
- Sort headers resolvable by `aria-label` (e.g. "Sort by Fwd 20d", "Sort by Market phase").
- `N=` chips render via the shared `SampleLink` component (new-tab Samples drill-down).

## Tests Run

Command: `cd apps/frontend && npx tsc --noEmit` → **EXIT 0** (no type errors).
(`next lint` is not configured in this project — interactive setup prompt; TypeScript typecheck is the gate.)

Live render verified with both servers up (`scripts/dev.sh`): `/research/phase-severity-lab` → HTTP 200,
title present, 3 survivorship mentions, 0 native date inputs; `/research` hub carries the tile. See the dev
handoff for the full live-render evidence (real figures, count-coherent N= drill-downs, as-of shrink).

## Known Issues

- None specific to the UI. The page reuses the established Regime-Lab patterns/tokens, so it matches the dark
  research theme; no new visual effects introduced.
