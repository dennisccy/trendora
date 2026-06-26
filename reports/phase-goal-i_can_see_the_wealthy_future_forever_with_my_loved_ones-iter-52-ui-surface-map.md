# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52
**Date:** 2026-06-26
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research/factor-lab` | Horizon `<select>` dropdown | Removed element | Page now shows all horizons at once; per-horizon selection is obsolete | Navigate to `/research/factor-lab`; confirm no dropdown labelled "Horizon" or similar is rendered anywhere on the page |
| `/research/factor-lab` | `FactorsTable` — column headers | New columns | Added 5 "Fwd {h}d" + 5 "MDD {h}d" paired columns for all configured horizons (1d, 5d, 10d, 20d, 60d) | Confirm the table header row contains columns for each of 1d, 5d, 10d, 20d, 60d, each appearing as a "Fwd Xd" column immediately followed by an "MDD Xd" column |
| `/research/factor-lab` | `TopDecileCell` — forward-return cells | New component | Shows top-decile (D10) mean realized forward return per horizon for each factor | Verify that the "Fwd 20d" cell for at least one factor displays a percentage value coloured green (positive) or red (negative), not blank or "NA" |
| `/research/factor-lab` | `TopDecileCell` — max-drawdown cells | New component | Shows top-decile (D10) mean max-drawdown per horizon, colour-graded by severity | Verify that the "MDD 20d" cell for at least one factor displays a negative percentage that is shaded red; a factor with a larger drawdown value should show a deeper red than one with a smaller drawdown |
| `/research/factor-lab` | `FactorsTable` — Rank-IC column label | Changed display | Rank-IC is now fixed at the config default horizon (20d) and labelled with it | Confirm the Rank-IC column header reads "Rank-IC (20d)" (or equivalent fixed-horizon label) and does NOT change when clicking any sort control |
| `/research/factor-lab` | `FactorsTable` — Risk-adjusted column label | Changed display | Risk-adjusted figure is now fixed at the config default horizon (20d) and labelled with it | Confirm the Risk-adjusted column header includes "(20d)" (or equivalent) and is static, matching the Rank-IC label's horizon |
| `/research/factor-lab` | `FactorSortHeader` — per-horizon sort controls | Changed behavior | Each "Fwd {h}d" and "MDD {h}d" column header is now independently sortable; sort is NA-last and view-only | Click the "Fwd 1d" column header; confirm the table rows reorder so the highest "Fwd 1d" value appears first; then click again and confirm the order reverses; confirm any factor with "NA" in that column remains at the bottom in both directions |
| `/research/factor-lab` | Factor row expand chevron → `DecileTable` | Changed behavior | Expanding a factor now shows the all-horizon paired decile grid (D1–D10 × all horizons) instead of a single-horizon decile list | Click the expand chevron on any factor row; confirm a sub-grid appears with 10 rows (D1 through D10) and that columns show "Fwd Xd" and "MDD Xd" pairs for all five horizons |
| `/research/factor-lab` | `DecileReturnCell` — N= chip on each decile/horizon cell | New feature | Each forward-return cell in the decile grid carries an N= chip linking to the exact (factor, horizon, decile) cohort on `/research/samples` | Expand a factor, locate the D10 row's "Fwd 20d" cell, note the N= chip value (e.g. "N=12,297"); click it; confirm a new browser tab opens at `/research/samples` scoped to that factor/horizon/decile, and the "Total observations" shown there equals the chip value |
| `/research/factor-lab` | `DecileMddCell` — per-decile max-drawdown cells in decile grid | New component | Each decile row now shows a paired MDD cell at every horizon, colour-graded by severity | In the expanded decile grid, verify that the "MDD 20d" cell for D10 shows a negative percentage; verify that D1 (typically highest drawdown) is shaded more intensely red than D10 (typically lower drawdown) |
| `/research/factor-lab` | `DecileTable` — "Factor range" column | Changed display | Shows the factor value range at the default horizon; per-horizon range is on hover | In the expanded decile grid, confirm a "Factor range" column is visible as a static column (not duplicated per horizon); hover a "Fwd Xd" cell and confirm a tooltip appears showing that horizon's factor range |
| `/research/factor-lab` | As-of / All-history mode toggle | Unchanged (regression check) | Must continue to drive all N= values globally via the single top-bar date with no page-local date state | Toggle "All-history" mode; confirm N= chips in the decile grid update their values across all factors and all horizons; toggle back to "As-of"; confirm chips revert and no second date input has appeared on the page |
| `/research/samples` (opened via chip) | Samples cohort display | Changed behavior (upstream) | Now reached via new per-`(factor, horizon, decile)` chip from the all-horizon decile grid | From the Factor Lab decile grid, click the N= chip on D5's "Fwd 5d" cell; confirm the Samples page opens in a new tab, the cohort header shows the correct factor name + 5d horizon + D5 decile, and the "Total observations" matches the chip value |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/research.py` (cache schema token `_ALL_FACTORS_SCHEMA_TOKEN = "allh-mdd-v1"` folded into `factor_lab_all_cached` key) — ensures any pre-iter-52 cached Factor Lab payload is treated as a miss and is recomputed with the new shape; this is transparent to the user (they see the correct data either way) — no visible UI surface
- `apps/backend/app/engine/research.py` (`_all_factor_observations_by_horizon` streaming bounds, `ScannerResult` ordered by `(run_id, id)`) — OOM-safety and byte-identity implementation details; no UI surface affected
- `apps/backend/tests/test_factor_lab_all.py` — test file; no UI surface
- `apps/backend/tests/test_research_streaming.py` — test file; no UI surface
- `apps/backend/tests/test_api_research.py` — test file; no UI surface

---

## Summary

- **Frontend surfaces changed:** 1 route (`/research/factor-lab`), 13 surface rows
- **New pages/routes:** 0 (all changes are to the existing `/research/factor-lab` route)
- **Modified components:** `FactorLabPage`, `FactorsTable`, `FactorRows`, `TopDecileCell` (new), `DecileTable`, `DecileReturnCell` (new), `DecileMddCell` (new), `FactorSortHeader`; `FactorLabAllResponse` / `fetchFactorLabAll` in `apps/frontend/lib/api.ts`
- **Navigation changes:** no (no new top-level nav entry; no new route)
- **Backend-only changes:** 5 (cache schema token, streaming implementation, 3 test files)
