# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-55 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-55
**Date:** 2026-06-27
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research` | Research hub tile list | Added navigation | New "Regime × Phase × Factor" tile (Boxes icon) added to the LABS list | Navigate to `/research`; confirm a tile labelled "Regime × Phase × Factor" with a Boxes icon is visible and its link points to `/research/regime-phase-factor` |
| `/research/regime-phase-factor` | `RegimePhaseFactorPage` — full page | New page | J-112 lab: 3-way decile combination study for a selected factor | Navigate to `/research/regime-phase-factor`; confirm the page title renders, the factor selector dropdown is present, and no native `<input type="date">` element exists on the page |
| `/research/regime-phase-factor` | `RegimePhaseFactorPage` — factor selector | New component | Drives which factor's decile is the third dimension in the combination table | Change the factor selector from the default (e.g. `leadership_score`) to a different factor (e.g. `entry_quality_score`); confirm the combination table rows change (n values differ) |
| `/research/regime-phase-factor` | `RegimePhaseFactorPage` — combination table | New table | Shows (regime-decile × severity-decile × factor-decile) combinations with return/MDD/n per horizon | Confirm the table shows rows whose leftmost three columns are labelled as regime decile, severity decile, and factor decile, and that forward-return and max-drawdown columns appear for each configured horizon |
| `/research/regime-phase-factor` | `RpfDecileFilter` — regime/severity/factor decile filters | New component | Allow narrowing the visible rows by decile without re-fetching | Set the regime decile filter to "D10"; confirm only rows whose regime-decile column shows D10 remain visible in the table |
| `/research/regime-phase-factor` | `RpfSortHeader` — column sort | New component | NA-last sort in both directions on any return/MDD/n column | Click the sort header for the 1-day forward-return column; confirm rows reorder and any NA cells move to the bottom; click again; confirm order reverses and NA cells remain at the bottom |
| `/research/regime-phase-factor` | Pagination footer (prev/next) | New component | Table has up to ~1000 combinations per factor; 30 rows/page | With the default factor and no filters applied, confirm only 30 rows are visible; click the next-page button; confirm the next 30 rows appear and the previous 30 are no longer shown |
| `/research/regime-phase-factor` | As-of vs All-history toggle | New component | Scopes the observation set to snapshots up to a historical date | Enable the As-of toggle (or navigate with `?asof=2024-06-01`); confirm that the n values in the table decrease compared to the All-history view, and that no second date input control appears on the page |
| `/research/regime-phase-factor` | N= chip on a combination row | New component | Drill-down to Research Samples for the exact triple cohort | Click an N= chip on a row (e.g. the highest-n combination); confirm a new tab opens at `/research/samples` showing a regime-phase-factor cohort whose "Total observations" count matches the number displayed on the chip |
| `/research/regime-phase-factor` | `CaveatBanner` — survivorship-bias label | New component | Honest limitations surfaced per goal anti-goal | Confirm a survivorship-bias or descriptive-evidence disclaimer is visible on the page |
| `/research/samples` | `describeCohort` — cohort description text | Changed behavior | New `regime-phase-factor` kind added; samples page now describes the cohort when arriving from an N= chip | Navigate to `/research/samples` via an N= chip drill-down from the Regime × Phase × Factor lab; confirm the page shows a human-readable cohort description that includes the regime decile, severity decile, factor decile, and horizon values from the chip |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/research.py` (engine functions: `compute_regime_phase_factor_study`, `regime_phase_factor_cached`, `_regime_phase_factor_members_by_horizon`, `_regime_phase_factor_observation_set`, `_assign_triple_deciles`) — computes the 3-way study and caches it in `event_study_cache`; no UI surface affected directly (consumed only via the API endpoint)
- `apps/backend/app/engine/samples.py` (`KIND_REGIME_PHASE_FACTOR`, `_regime_phase_factor_samples`) — implements the regime-phase-factor samples cohort logic; no UI surface affected directly (consumed only via the samples API endpoint)
- `apps/backend/app/config.py` + `config.yaml` (`regime_phase_factor_page_size: 30`) — adds the config-sourced page size; the value is served in the API payload and read by the frontend (making it config-sourced rather than an inline literal), but this field is not directly user-visible
- `apps/backend/tests/test_regime_phase_factor.py` (new, 38 tests) — backend test coverage; no UI surface affected
- `apps/backend/tests/test_api_research.py` (7 new test cases) — backend test coverage; no UI surface affected
- `apps/backend/tests/test_samples.py` (1 new triple-cohort test case) — backend test coverage; no UI surface affected

---

## Summary

- **Frontend surfaces changed:** 11
- **New pages/routes:** 1 (`/research/regime-phase-factor`)
- **Modified components:** 2 (`/research` hub tile list, `/research/samples` describeCohort branch)
- **Navigation changes:** yes — one new tile added to the Research hub
- **Backend-only changes:** 6 (engine functions, samples logic, config field, 3 test files)
