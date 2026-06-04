# Phase goal-i_can_see_the_wealthy_future_forever-iter-18 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-18
**Date:** 2026-06-04
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research` | `CombinationTable` — Combined (composite) row (`data-testid="combination-row-composite"`) | Changed behavior | Headline Combined cohort is now a populated composite rank-blend instead of the empty strict-AND | On default load, read the `combination-row-composite` row: confirm n ≥ 30 and that Mean / Median / Hit-rate / Risk-adjusted are numeric (not "NA"), and that its values differ from the Baseline row |
| `/research` | `CombinationTable` — Strict overlap (AND) row (`data-testid="combination-row-strict_overlap"`) | New table row | Exact AND-intersection demoted to a secondary, clearly-labelled row | Confirm a row labelled "Strict overlap (AND)" renders below the composite row; with the default selection check it shows either numbers or honest "NA" with an n value (never a fabricated 0) |
| `/research` | `CombinationTable` — row order & emphasis | Updated layout | Row order is Baseline → singles → Combined (composite, emphasized) → Strict overlap (AND, muted) | Confirm visual order top-to-bottom is Baseline, then single-factor rows, then the emphasized (highlighted background, bold) composite row, then the muted strict-overlap row |
| `/research` | `CombinationLab` — section hint text (`combination-section` PanelTitle) | Changed behavior | Hint rewritten to describe the composite rank-blend, the config quantile/weighting, and the secondary strict-overlap | Read the hint under "Multi-factor combination cohort": confirm it names "composite rank-blend", shows a quantile label (e.g. "Quintile (20%)") and a weighting scheme (e.g. "equal"), and states it is NOT a fitted/ML model |
| `/research` | `CombinationLab` — "Add condition" control | Changed behavior | Condition cap raised 3 → 11 (payload-driven `max_conditions`) | Click "Add condition" repeatedly: confirm conditions can be added up to 11 (all catalog factors) before the control disables, and the composite row stays populated (n > 0) as conditions are added |
| `/research` | `CombinationTable` — empty-strict-overlap state | Changed behavior | Membership-driven NA: composite stays populated when the exact intersection is empty | Drive an empty-intersection selection (e.g. same factor Top + Bottom, or many factors): in the same view confirm the composite row is populated (n > 0) while the Strict overlap (AND) row shows NA + n |
| `/research` | Page-level date state (J-18 anti-goal guard) | No change (verify) | Spec forbids any new date/as-of state on `/research` | Toggle the global as-of control in-app (not a hard reload): confirm the Factor Lab content is byte-identical, no `/api/research/*?as_of=` request fires, and there is exactly one date `<select>` on the page (none inside `/research`) |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/research.py` — `compute_factor_combination` rewrite + new pure helpers `_percentile_rank_fractions` / `_composite_scores` — produces the composite + strict_overlap payload consumed by the surfaces above (its output IS visible; the code itself is internal).
- `apps/backend/app/api/research.py` — `factor_combination` endpoint; only the module docstring changed, signature unchanged. Serves the reshaped payload to the UI; no independent UI surface.
- `apps/backend/app/config.py` — new `CompositeWeightingCfg` / `CompositeCfg` types + boot validation. No UI surface; affects only startup validation (invalid config raises `ConfigError` at boot).
- `config.yaml` — `combination.max_conditions: 3 → 11` and new required `composite` sub-block (`quantile`, `weighting`). Drives the UI cap and blend labels but is not itself a UI surface.
- `apps/frontend/lib/api.ts` — `FactorCombinationResponse` type reshape (`composite` + `strict_overlap` + metadata replacing `combined`); type-only, no rendered surface of its own (consumed by `CombinationTable`).
- Test files (`tests/test_research.py`, `tests/test_api_research.py`, `tests/test_config.py`, `tests/test_config_engine.py`, `tests/test_sectors.py`, `tests/test_themes.py`) — no UI impact.

---

## Summary

- **Frontend surfaces changed:** 1 page (`/research`), 1 section ("Multi-factor combination cohort")
- **New pages/routes:** 0
- **Modified components:** 2 (`CombinationTable`, `CombinationLab`)
- **Navigation changes:** no
- **Backend-only changes:** 6 (engine, API, config typing, config.yaml, api.ts type, tests)
