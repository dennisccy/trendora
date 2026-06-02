# Phase goal-i_can_see_the_wealthy_future_forever-iter-11 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-11
**Date:** 2026-06-02
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research` | `RegimeEffectivenessTable` (`data-testid="regime-effectiveness-table"`) | New table | J-27: shows per-regime factor effectiveness (rank-IC + raw & downside-risk-adjusted top−bottom decile spread) | Load `/research`; scroll below the decile/rank-IC grid; confirm a table titled "Factor effectiveness by market regime" with exactly one row per configured regime label (Strong risk-on, Risk-on, Narrow leadership, Choppy, Defensive, Risk-off) and 7 columns (Regime, n, Rank-IC, Top-decile mean, Bottom-decile mean, Spread, Risk-adjusted spread). |
| `/research` | `RegimeEffectivenessTable` — populated row | New table | Per-regime IC + spread from stored evidence | Set Horizon to a short value (e.g. 5d) so a high-sample regime (e.g. Risk-on) clears `min_sample`; confirm that row shows a numeric Rank-IC, Top/Bottom-decile mean, and a numeric Spread, with its `n` chip showing a count ≥ min_sample. |
| `/research` | `RegimeCell` — NA cell | New component | Honest low-sample / no-downside treatment | Find a sparse or empty regime (e.g. Strong risk-on or Defensive, or set Horizon to 60d); confirm its Rank-IC / Spread / Risk-adjusted spread cells render the muted text "NA" (not blank, not 0) while the `n` column still shows the honest count (incl. n=0). |
| `/research` | `RegimeEffectivenessTable` — risk-adjusted column | New table | Downside-only honesty | Find a regime whose top decile has no downside; confirm "Risk-adjusted spread" shows "NA" while the raw "Spread" column shows a numeric value (downside-only — never a total-volatility number). |
| `/research` | Factor selector (existing) → regime table | Changed behavior (re-point) | Table re-points on factor change with no new control | Change the Factor dropdown; confirm the regime table's Rank-IC/Spread values change (capture distinct before/after DOM text + observe a `GET /api/research/factor-lab?factor=…&horizon=…` request firing). |
| `/research` | Horizon selector (existing) → regime table | Changed behavior (re-point) | Table re-points on horizon change | Change the Horizon selector; confirm the regime table values and `n` chips update and a new `factor-lab` request fires with the new horizon. |
| `/research` | Global as-of switcher (top bar) vs. Factor Lab | Unchanged (regression check) | J-18: `/research` is a cross-date aggregate with no date state | Toggle the global top-bar as-of switcher; confirm the entire Factor Lab — decile table, rank-IC card, AND the new regime table — is byte-identical and that ZERO requests carrying an `as_of` param are made. |
| `/research` | Decile table + rank-IC card (existing) | Unchanged (regression check) | J-25 must remain green | Confirm the existing decile table and rank-IC card still render and still re-point on factor/horizon change after the new panel was added. |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/research.py` — `_factor_observations` now attaches the stored `scanner_runs.regime_label` (read verbatim, SELECT-only) to each observation, and a new `_regime_effectiveness(...)` helper builds the `by_regime` slice added to `compute_factor_lab(...)`. This is the data source for the new table; it surfaces entirely through the existing `/api/research/factor-lab` payload (no new endpoint, no API view change).
- `apps/backend/tests/test_research.py` — extended read-only keystone (also patches `regime.score_regime` to raise) + 6 new J-27 scenarios. Tests only — no UI surface.

---

## Summary

- **Frontend surfaces changed:** 1 route (`/research`), 1 new panel/table + 1 new cell renderer
- **New pages/routes:** 0
- **Modified components:** `apps/frontend/app/research/page.tsx` (added `RegimeEffectivenessTable` + `RegimeCell`), `apps/frontend/lib/api.ts` (added `RegimeEffectivenessRow` type + `by_regime` field)
- **Navigation changes:** no
- **Backend-only changes:** 2 files (`research.py` engine logic, `test_research.py` tests)
