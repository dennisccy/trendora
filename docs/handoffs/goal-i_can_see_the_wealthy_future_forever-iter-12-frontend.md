# goal-i_can_see_the_wealthy_future_forever-iter-12 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-12
**Date:** 2026-06-02
**Agent:** developer
**Status:** complete

## What Was Built

A single additive **"Multi-factor combination cohort"** section appended to the existing `/research`
Factor Lab page, **below** the regime-effectiveness table. **No new page, route, or sidebar entry.**

- **Condition controls (config-driven):** 2–3 condition rows, each a **Factor** `<Select>`, a **Side**
  Top/Bottom segmented toggle, and a **Quantile** `<Select>`. The factor and quantile option lists come
  **from the payload** (`data.factors` / `data.quantiles`) — no hard-coded factor or quantile list in the
  frontend. **+ Add condition** (disabled at `max_conditions`) and a per-row **Remove** (disabled at
  `min_conditions`). The initial conditions come from the server's resolved `default_conditions`.
- **Comparison table:** rows = **Baseline (all names)**, one row per single condition (labelled e.g.
  "Relative strength vs SPY (3m) · top Quintile (20%)"), and **Combined (AND)** (visually emphasised).
  Columns = **Cohort**, **n**, **Mean fwd return**, **Median**, **Hit-rate**, **Risk-adjusted (downside)**.
- **Honest NA + n:** a low-sample (n < `min_sample`), empty (n = 0), or null cell renders **"NA"** with the
  honest `n` via the existing `SampleSize` chip — reusing the same NA treatment as the decile/regime tables.
  Returns and the risk-adjusted ratio are colour-graded (`returnClass`); the hit-rate stays neutral so a
  low hit-rate is not painted "good".
- **States:** loading skeleton on first load; a subtle dim on the table during re-fetch; the existing
  "Backend unavailable" error card; an honest empty-pool message (`pool_n === 0`) via `EmptyState`.
- **Honest scope note:** a line states the risk-adjusted column is **downside-deviation only** and that
  return/MAE / MAE-MFE excursion measures arrive with the event-study lab (J-29) — so the single
  risk-adjusted column is not silently read as "all" risk measures.

## Single date control / J-18

The section reuses the **page's shared `horizon`** (one selector for the whole page) and adds **only**
`conditions` state — **no as-of/date state**. The combination fetch never sends an `as_of` param, so
toggling the global as-of date does not re-fetch or change this table (J-18 preserved).

## Files Changed

- `apps/frontend/lib/api.ts` — **modified.** Added types `QuantileOption`, `FactorCombinationCondition`,
  `CohortStats`, `FactorCombinationCohort`, `FactorCombinationSingle`, `FactorCombinationResponse`, and the
  `fetchFactorCombination(conditions, horizon, signal)` fetcher (builds repeated
  `condition=<factor>:<side>:<quantile>` query params; throws on non-200 → explicit "Backend unavailable").
- `apps/frontend/app/research/page.tsx` — **modified.** Added the `CombinationLab` section component +
  `ConditionControls`, `SideToggle`, `CombinationTable`, `CohortCell`, `CombinationSkeleton`, and the
  `conditionLabel` helper; wired `<CombinationLab horizon={horizon} />` below `<FactorLab />`.

## Components / patterns reused

`Card`, `PanelTitle`, `Select`, `EmptyState`, `SampleSize`, `fmtPct`, `fmtRatio`, `returnClass`, `cn`, and
the segmented-control styling from `HorizonSelector`. Dark analytical workstation tokens only; numbers are
`num` (tabular). Interactive elements carry hover/focus/disabled states; the table is horizontally
scrollable on mobile (`overflow-x-auto`).

## Tests Run

Command: `cd apps/frontend && npm run build`
Result: **Compiled successfully**; types valid; all 14 routes generated. `/research` route size 7.51 kB.

## Test IDs for browser QA

- `combination-section` (the section Card), `combination-table` (the comparison table).
- `condition-factor-<i>`, `condition-side-<i>`, `condition-quantile-<i>`, `condition-remove-<i>` (per row),
  `condition-add` (the add control). Reuses the existing page `factor-select` / `horizon-select` testids.

## Known Issues

- The combined cohort is the strict AND-intersection and can become thin quickly → renders NA + n honestly
  (never a fabricated number). This is expected behavior, not a defect.
- One extra initial fetch is avoided: `conditions` stays `null` (server defaults) until the user first
  edits, and the last good `data` persists across re-fetches so the controls do not flicker.
