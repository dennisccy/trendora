# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50
**Date:** 2026-06-26
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|---|---|---|---|---|
| `/research/factor-lab` | `FactorsTable` (all-factors comparison table) | New component | J-107: replaces the single-factor dropdown with an all-factors overview | Navigate to `/research/factor-lab`; confirm the page renders a table with multiple rows (one per catalog factor) each showing Factor, Family, Rank-IC, N, and Risk-adjusted columns — no dropdown visible |
| `/research/factor-lab` | `FactorSortHeader` column sort buttons | New component | J-107: all-factors table must be client-side sortable NA-last | Click the "Rank-IC" column header; confirm rows reorder (highest rank-IC first); click again; confirm rows reorder (lowest first); confirm rows with no rank-IC value appear at the bottom in both directions |
| `/research/factor-lab` | Factor row expand/collapse (`aria-expanded` rows) | New component | J-107: each row must expand in place to reveal the factor's decile sort | Click any factor row; confirm a decile breakdown panel (`DecileTable`) appears beneath it showing 10 decile rows (D1–D10); click the same row again; confirm the panel collapses |
| `/research/factor-lab` | `DecileTable` (inside expanded factor row) | Changed behavior | J-107: DecileTable now renders inside the expand panel instead of as the main page body | Expand a factor row; confirm the decile table shows mean return values, N counts, and risk-adjusted figures for each of the 10 deciles |
| `/research/factor-lab` | Decile `SampleLink` `N=` chips (inside `DecileTable`) | Preserved behavior | Drill-down must remain count-coherent after the restructure | Inside an expanded factor row, click a decile's `N=` chip; confirm a new browser tab opens to the Research Samples page and the sample count shown matches the N value displayed in the Factor Lab decile row |
| `/research/factor-lab` | `FactorSelector` dropdown | Removed element | J-107: dropdown replaced by all-factors table | Navigate to `/research/factor-lab`; confirm there is no factor selector dropdown on the page |
| `/research/factor-lab` | `FactorLab` single-factor body + `RankICCard` | Removed element | J-107: single-factor body superseded by the expandable all-factors table | Navigate to `/research/factor-lab`; confirm there is no standalone rank-IC card and no single-factor decile table rendered at page level (decile table only appears inside an expanded row) |
| `/research/factor-lab` | `RegimeEffectivenessTable` (per-regime breakdown) | Removed element | J-107: per-regime table removed from this view (backend still computes it) | Navigate to `/research/factor-lab` and scroll the full page; confirm no market-regime effectiveness table or regime-labelled rows are visible anywhere on the page |
| `/research/factor-lab` | `HorizonSelector` control | Preserved behavior | Horizon selector must still update all table rows simultaneously | Change the horizon (e.g., from 20d to 60d) using the horizon selector; confirm the Rank-IC, N, and Risk-adjusted values in all visible table rows update to reflect the new horizon |
| `/research/factor-lab` | As-of mode toggle (All-history / As-of date) | Preserved behavior | As-of toggle must apply to the all-factors table as a single global filter | Toggle from "All history" to "As of date" and enter a mid-history date; confirm the N values in the factor rows change to smaller numbers; confirm the as-of date echoes in the page or caveat (not a second independent date selector) |
| `/research/factor-lab` | `WarmingState` / `ResearchError` / `LabSkeleton` honest states | Preserved behavior | Honest states must still render correctly under the new fetch path | On initial cold load (or after clearing the cache), confirm a loading skeleton or warming indicator appears before data arrives; confirm no fabricated row is shown for the empty state |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/research.py` (`_all_factor_observations`, `compute_factor_lab_all`, `factor_lab_all_cached`) — all-factors aggregate computation and derived-once cache; exposed via the existing endpoint and fully wired to the frontend — not backend-only, but the compute internals (shared pool, `yield_per` streaming, `(run_id, id)` ordering, `EventStudyCache` sentinel namespace) have no direct UI surface.
- `apps/backend/tests/test_factor_lab_all.py` — new test file covering byte-identity, cache correctness, bounded-read, and NA honesty; no UI surface.
- `apps/backend/tests/test_api_research.py` (additions) — new API-level tests for the all-factors flag; no UI surface.

---

## Summary

- **Frontend surfaces changed:** 1 (the `/research/factor-lab` page)
- **New pages/routes:** 0
- **Modified components:** 8 (FactorsTable added, FactorSortHeader added, expand/collapse row added, DecileTable rehoused, SampleLink preserved, FactorSelector removed, FactorLab+RankICCard removed, RegimeEffectivenessTable removed)
- **Navigation changes:** no (Research → Factor Lab link unchanged)
- **Backend-only changes:** 0 (all backend work feeds directly into the wired frontend table)
