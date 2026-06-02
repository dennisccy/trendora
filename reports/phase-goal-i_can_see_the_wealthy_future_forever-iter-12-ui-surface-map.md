# Phase goal-i_can_see_the_wealthy_future_forever-iter-12 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-12
**Date:** 2026-06-02
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research` | `CombinationLab` section (`combination-section`) | New component | J-26 adds multi-factor combination cohorts to the Factor Lab | Scroll below the regime-effectiveness table; confirm the "Multi-factor combination cohort" Card renders with default 2 condition rows and a populated comparison table |
| `/research` | `CombinationTable` (`combination-table`) | New table | Show Baseline vs each single vs Combined (AND) cohort | Confirm the table has a Baseline (all names) row, two single-condition rows, and a Combined (AND) row, each with non-empty n / Mean fwd return / Median / Hit-rate / Risk-adjusted columns |
| `/research` | Factor `<Select>` (`condition-factor-<i>`) | New form control | User picks the catalog factor per condition | Change the factor in condition row 0; confirm a fresh `GET /api/research/factor-combination?condition=...` fires and that row's single-cohort label and stats update to match the API |
| `/research` | Side toggle (`condition-side-<i>`) | New form control | User picks Top/Bottom quantile side | Toggle a row from Top to Bottom; confirm a new request fires and the single-cohort membership/stats change in the table |
| `/research` | Quantile `<Select>` (`condition-quantile-<i>`) | New form control | User picks the quantile (quintile/quartile/tertile/half) | Change a row's quantile (e.g. quintile → half); confirm a new request fires and the cohort `n` grows/shrinks accordingly |
| `/research` | "+ Add condition" button (`condition-add`) | New control | User extends from 2 to 3 conditions | With 2 conditions, click Add; confirm a 3rd condition row + 3rd single table row appear and that Combined `n` ≤ each single `n` ≤ pool_n |
| `/research` | Per-row Remove button (`condition-remove-<i>`) | New control | User drops a condition back toward the minimum | With 3 conditions, click Remove on one; confirm the row and its single table row disappear and the table reverts to 2 singles + Combined; confirm Remove is disabled at 2 conditions |
| `/research` | Shared `horizon` selector (`horizon-select`) | Changed behavior | Horizon now also re-points the combination table | Change the horizon; confirm the combination table re-fetches and updates alongside the decile/IC and regime tables |
| `/research` | Combined (AND) cohort cell | New behavior (honest NA) | Thin combined cohorts must show NA + n, not a fabricated number | Drive an NA fixture (two opposing extremes → small combined cohort); confirm the Combined cell shows "NA" with the honest `n` rather than a number |
| `/research` | Error / empty / loading states | New states | Honest backend-unavailable + empty-pool handling | Confirm a loading skeleton on first load; with `pool_n === 0` confirm the empty-pool message; with the backend down confirm the "Backend unavailable" card (no fabricated figures) |
| `/research` | Global as-of date control (existing) | Regression check | J-18: new section must add no date state | Toggle the global as-of date; confirm the decile table, rank-IC, regime table AND the new combination table are byte-identical with ZERO `as_of`-param requests |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/research.py` — new `compute_factor_combination` + helpers (`_combination_observations`, `_quantile_cutoff`, `_cohort_stats`, `_condition_payload`); SELECT-only read aggregation. Surfaces via the endpoint below, so user-visible through the new section.
- `apps/backend/app/api/research.py` — new `GET /api/research/factor-combination` route. Consumed by the frontend `fetchFactorCombination`, so it backs the new section (not invisible).
- `config.yaml` / `apps/backend/app/config.py` — new `research.factor_lab.combination` block (min/max conditions, quantiles vocabulary, default conditions) + typed boot-validation. Drives the server-supplied dropdown options; no standalone UI surface.
- `apps/backend/tests/*` — test additions; no UI impact.

---

## Summary

- **Frontend surfaces changed:** 1 page (`/research`), 1 new section, 1 new table, 5 new control types, 3 new states
- **New pages/routes:** 0 (additive section on existing `/research`; no nav/sidebar change)
- **Modified components:** `apps/frontend/app/research/page.tsx` (new `CombinationLab` + sub-components), `apps/frontend/lib/api.ts` (new types + `fetchFactorCombination`)
- **Navigation changes:** no
- **Backend-only changes:** 4 (engine, API route, config + config validation, tests) — the engine + API + config back the new section and are user-visible through it; tests are not
