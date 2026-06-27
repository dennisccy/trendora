# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-54 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-54
**Date:** 2026-06-27
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research` | Research hub tile list | Added navigation | New lab page requires an entry point on the hub | Click the "Market Phase & Severity Lab" tile (data-testid `research-lab-link-phase-severity-lab`) and confirm it navigates to `/research/phase-severity-lab` |
| `/research/phase-severity-lab` | `PhaseSeverityLabPage` (new page) | New page | J-111: read-only cross-sectional study of returns/MDD across market-phase labels and severity-score deciles | Navigate to `/research/phase-severity-lab` and verify the page title "Market Phase & Severity Lab" is visible and the survivorship-bias caveat text appears in the page header |
| `/research/phase-severity-lab` | `PhaseSeverityLabByLabelTable` (by-phase table) | New table | Display per-horizon mean return + MDD grouped by the five market-phase labels | Confirm the table (data-testid `phase-severity-label-table`) renders exactly five rows — one each for Expansion, Pullback, Correction, Bear, Recovery (data-testids `phase-severity-label-row-<phase>`) — and that each row shows numeric return and MDD cells under at least one horizon column |
| `/research/phase-severity-lab` | `PhaseSeverityLabDecileTable` (by-decile table) | New table | Display per-horizon return + MDD grouped by D1–D10 severity-score deciles, plus a Rank-IC header row | Confirm the table (data-testid `phase-severity-decile-table`) renders a Rank-IC header row (data-testid `phase-severity-decile-rank-ic-row`) followed by exactly ten decile rows (data-testids `phase-severity-decile-row-1` through `phase-severity-decile-row-10`); verify each decile row shows a severity-score range in the first column |
| `/research/phase-severity-lab` | Column sort controls | New feature | Every numeric column must be sortable NA-last in both directions | Click the "Sort by Fwd 20d" column header (aria-label), record the MD5 of the rendered rows, click it again to reverse the sort, and confirm the MD5 changes; then confirm any NA cells appear at the bottom of the sorted order in both directions |
| `/research/phase-severity-lab` | As-of filter toggle | New feature | Users must be able to scope the evidence to a historical date using the single global as-of (no second date input allowed) | Enable As-of to a mid-history date (e.g. `?asof=2024-06-01`); confirm the displayed `N=` values decrease compared to All-history; confirm there is no `input[type="date"]` element anywhere on the page |
| `/research/phase-severity-lab` | `N=` drill chips (SampleLink) | New feature | Each bucket's chip must open the exact matching cohort in Research Samples (count-coherent) | Click the `N=` chip for the Bear phase at the 20-day horizon; confirm it opens `/research/samples` in a new tab and that the "Total observations" figure on the Samples page equals the `N=` value that was clicked |
| `/research/samples` | `describeCohort` cohort header | Changed behavior | Regime-lab and phase-severity-lab cohorts previously fell through to a generic label | Drill into any Regime Lab `N=` chip; confirm the Samples page heading identifies the cohort as "Regime Lab" (not "Setup & Pattern Lab"); drill into a phase-severity-lab chip and confirm the heading identifies the cohort correctly |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/research.py` (new engine functions) — `compute_phase_severity_lab`, `phase_severity_lab_cached`, observation builders — consumed by the new API endpoint and surfaced via the new frontend page; classified as full-stack, not backend-only.
- `apps/backend/app/engine/samples.py` (new `KIND_PHASE_SEVERITY_LAB`) — consumed by the Samples API and surfaced via `N=` chips; classified as full-stack, not backend-only.
- `apps/backend/tests/test_phase_severity_lab.py` (new, 32 tests) — test file only; no UI surface affected.
- `apps/backend/tests/test_api_research.py` (7 new phase-severity tests) — test file only; no UI surface affected.
- `apps/backend/tests/test_samples.py` (new fixture for phase-severity-lab cohort) — test file only; no UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 4 (Research hub, new phase-severity-lab page, phase-severity-lab tables/sort/filter/chips, Samples cohort header)
- **New pages/routes:** 1 (`/research/phase-severity-lab`)
- **Modified components:** 3 (`apps/frontend/app/research/page.tsx` hub, `apps/frontend/app/research/_labs.tsx` lab components, `apps/frontend/app/research/samples/page.tsx` cohort header)
- **Navigation changes:** yes — one new hub tile under the existing Research section
- **Backend-only changes:** 0 (all backend capabilities are wired to the new page or existing chip drill-downs; only test files have no UI impact)
