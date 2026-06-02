# goal-i_can_see_the_wealthy_future_forever-iter-14 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-14
**Date:** 2026-06-02
**Agent:** developer
**Status:** complete

## What Was Built

A new **Setup & Pattern Lab — event study** section on `/research`, rendered BELOW the existing Factor Lab
and Multi-factor Combination Lab (a sibling component modeled on `CombinationLab`). No new page, route, or
nav entry; no new date control (it reuses the page's shared horizon — a cross-date aggregate, J-18).

- **`EventStudyLab`** (in `app/research/page.tsx`): owns a `subject` selection + fetch state; reuses the
  page's shared `horizon`. Renders its own loading skeleton, "Backend unavailable" error block, and an
  empty-state when a subject has zero occurrences at every horizon — never a fabricated value.
- **Subject selector** (`SubjectSelector`): one `<select>` grouped into **Setups** vs **Patterns**
  `<optgroup>`s, built entirely from the payload's `subjects` catalog (config-driven — no hard-coded
  setup/pattern list in the frontend), mirroring the factor selector's `<optgroup>` pattern.
- **Per-horizon distribution / exit-horizon table** (`EventStudyHorizonTable`): one row per configured
  horizon with Mean / Median / % Positive / Dispersion / Expectancy / Mean MAE / Mean MFE /
  Return ÷ downside-dev / Return ÷ MAE / n. The best-exit-horizon row is highlighted with a "best exit"
  badge; low-sample rows render NA + n (the `EsValue` cell + `SampleSize` chip).
- **By-market-regime panel** (`EventStudyRegimeTable`): one row per configured regime label (server-driven),
  each with n / mean / hit-rate / downside risk-adjusted; empty/low-sample regimes render NA + n.
- **By-sector panel** (`EventStudySectorTable`): one row per stored sector with members (present-only),
  each with n / mean / downside risk-adjusted; an empty slice shows an honest note.
- **Caveat**: the section renders the shared `CaveatBanner` fed by the payload's `survivorship_bias` +
  `descriptive_caveat`, so the survivorship-bias + descriptive labels are visible within the lab.
- **api.ts**: new `fetchEventStudy(subject?, horizon?, signal?)` + `EventStudyResponse` and row types
  (`EventStudySubject`, `EventStudyExpectancy`, `EventStudyHorizonRow`, `EventStudyRegimeRow`,
  `EventStudySectorRow`). Throws on non-200 so the UI shows the explicit unavailable state.

## Design system compliance
- Uses shadcn `Card` + `Select`; palette tokens only (`--pos`/`--neg`/`--warn`/`--accent`/`--text*`);
  `tabular-nums` (`num`) monospace for every number; raw shown beside risk-adjusted; loading skeleton,
  empty state, and styled error all handled. Wide table sits in `overflow-x-auto` (mobile-scrollable per
  the single ~640px breakpoint). Matches the established Factor Lab / Combination Lab look.
- Re-formats server values ONLY — recomputes no return / excursion / ratio. NA (null / low-sample) renders
  literal "NA" with the honest `n` chip — never a fabricated number.

## Test IDs (for browser QA)
- Section: `data-testid="event-study-section"`
- Subject select: `data-testid="subject-select"`
- Tables: `event-study-horizon-table`, `event-study-regime-table`, `event-study-sector-table`
- (Existing shared: `horizon-select` drives this section too.)

## How to verify (operator)
1. Open `/research`, scroll to **Setup & Pattern Lab — event study**.
2. The default subject is **Actionable** (a rare setup) → it honestly shows NA + n=2. Open the **Subject**
   selector and pick a data-rich subject to see numbers: **Breakout-watch** (Setups group) or
   **Pullback to a rising DMA** (Patterns group).
3. Read the per-horizon table (mean / median / %positive / dispersion / expectancy / mean-MAE / mean-MFE /
   return-per-downside-dev / return-per-MAE / n); the **best exit** horizon row is highlighted.
4. Read the **By market regime** panel (every regime label; empty regimes show NA + n) and the
   **By sector** panel (only sectors with members).
5. Change the shared **Horizon** buttons above — the by-regime / by-sector panels re-point to that horizon.
6. J-18: toggling the global as-of date control leaves this section byte-identical (it sends no `as_of`).

## Tests Run
- Frontend `npm run build` — compiles + typechecks; `/research` route built (9.21 kB).
- Backend endpoint live-verified on :8835 (then stopped): subject + horizon re-point, NA honesty, caveats.

## Known Issues
- The default subject (Actionable) renders honest NA + n=2 (a genuinely rare setup, < min_sample=30). This
  is correct low-sample behavior, not a rendering bug — pick a data-rich subject to see numbers (see the
  cohort-size list in the dev handoff).
