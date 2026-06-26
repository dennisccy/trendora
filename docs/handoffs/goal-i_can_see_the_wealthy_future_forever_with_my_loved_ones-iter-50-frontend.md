# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50
**Date:** 2026-06-26
**Agent:** developer
**Status:** complete

## What Was Built

`/research/factor-lab` now shows **every catalog factor at once** instead of one-at-a-time via a dropdown.

- **All-factors table (`FactorsTable`)** — one row per config-catalog factor, columns:
  **Factor** (label + direction hint) · **Family** · **Rank-IC** · **N** · **Risk-adjusted (downside)** ·
  expander chevron. Built entirely from the `?all=true` payload (`fetchFactorLabAll`) — no hard-coded
  factor/family list.
- **Client-side sortable NA-last** — every column header is a `FactorSortHeader` button (resolved in tests
  by `aria-label="Sort by <label>…"`; the visible label is a nested `<span>`). The sort is a pure view
  transform (re-orders only, recomputes/refetches nothing). Numeric columns push NA rows LAST regardless of
  direction; the NA predicate mirrors the cell render (rank-IC NA when value null; risk-adjusted NA when the
  top decile is low-sample / empty / null). Default sort: rank-IC descending (strongest edge first).
- **Click-to-expand per factor** — each summary `<tr>` is the keyboard-accessible expandable-row control
  (`role="button"` + `aria-expanded`, Enter/Space toggles) the Sectors page uses. Expanding reveals that
  factor's full decile sort via the EXISTING `DecileTable` (hidden by default) in a separate, non-clickable
  panel `<tr>`. The summary row carries no nested interactive element (the iter-5 hazard).
- **Decile `N=` drill-down preserved** — inside the expanded `DecileTable`, each decile's `N=` chip is still
  a `SampleLink` opening Research Samples in a new tab (`cohort={{kind:"factor", factor, horizon,
  slice:"decile", decile}}`) — count-coherent.
- **Per-regime effectiveness table REMOVED from this view** (`RegimeEffectivenessTable` / `data.by_regime`).
  The backend still computes it byte-identically — only the frontend retires the table here.
- **Controls preserved** — the HorizonSelector and the As-of mode toggle remain (single global as-of, no
  second date state, J-18). The factor dropdown is gone.
- **Honest states preserved** — warming (`WarmingState`), load error (`ResearchError`), loading skeleton
  (`LabSkeleton`), honest empty (no forward-tested factors → `EmptyState`, never a fabricated row), the
  survivorship + descriptive caveats (`ResearchCaveat`), and per-cell NA + n.

## Files Changed

- `apps/frontend/lib/api.ts` -- added `FactorTableRow`, `FactorLabAllResponse`, `fetchFactorLabAll`.
- `apps/frontend/app/research/_labs.tsx` -- rewrote `FactorLabPage` (fetch `?all=true`, render
  `FactorsTable`); added `FactorsTable` / `FactorRows` / `FactorSortHeader` / `RatioCell` + the
  `FactorSortKey` sort helpers; removed `FactorSelector` / `groupByFamily` / `FactorLab` / `RankICCard` /
  `RegimeCell` / `RegimeEffectivenessTable`; kept `familyLabel` (reused by the Family column) and
  `DecileTable` / `DecileValue` (reused in the expand panel).

## Tests Run

- `npx tsc --noEmit` → exit 0 (clean).
- The running `next dev` hot-reloaded the change: `/research/factor-lab` serves HTTP 200, the SSR HTML
  carries the new subtitle ("Which factors actually sort future returns"), and there is no build/runtime
  error overlay.

## Design System Conformance

- Reuses the existing research-lab shell: `Card`, `ResearchControls` / `ResearchCaveat` / `ResearchError`,
  the `SortHeader` sortable-header pattern (mirrors `/sectors` + `/stocks`), the Sectors `aria-expanded`
  expandable-row pattern, the existing `DecileTable` + decile `SampleLink` chips, and the shared
  `returnClass` / `fmtRatio` / `fmtPct` formatters. No new component-library primitives, no ad-hoc colours —
  border/surface/accent tokens + the `num` font only. Interactive elements carry hover/focus/active states.

## Known Issues

- The **Risk-adjusted column is the factor's top (D10) decile** downside risk-adjusted figure (re-presented
  from `deciles[-1]`, an existing canonical value — no recompute). Direction is conveyed by the rank-IC sign
  and the per-row `(direction)` hint, not by switching to the bottom decile for `lower_better` factors.
- For the browser J-32 (As-of) leg, toggle to a **mid-history** date — at the very earliest snapshot the
  scoped n is honestly 0 (no realized forward returns yet), which is a less obvious "values changed" frame.
