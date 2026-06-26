**Verdict:** COHERENCE-PASS

---

## Coherence Audit — iter-50 (J-107)

**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration:** 50
**Snapshot SHA:** bd97d19caf8b5cee989f4b27f62a41fc450d21af
**Files changed (uncommitted):** apps/backend/app/api/research.py, apps/backend/app/engine/research.py, apps/backend/tests/test_api_research.py, apps/frontend/app/research/_labs.tsx, apps/frontend/lib/api.ts
**New files:** apps/backend/tests/test_factor_lab_all.py

---

## Part A — Data Contract Check

### Factor-Lab analytics (J-107)

Blueprint registration (blueprint.md line ~425): canonical computing module = `research:compute_factor_lab`; serving endpoint = `GET /api/research/factor-lab`. The J-107 annotation on this row explicitly pre-registers the all-factors restructure: "the SAME `compute_factor_lab`/`_rank_ic`/`_risk_adjusted`/`_deciles` builders over ONE shared streamed/column-projected observation pass... served from a derived-once `EventStudyCache`+`_dataset_version` aggregate on the EXISTING `GET /api/research/factor-lab` (additive param — NO new endpoint, NO new `table=True` model)."

**Backend diff (apps/backend/app/engine/research.py):** Three new functions are added:

- `_all_factor_observations` — builds ONE shared observation pool (column-projected, `yield_per`-streamed) carrying every catalog factor's stored value per observation. This is a read-only pool builder, not an independent metric computation.
- `compute_factor_lab_all` — iterates the pool per factor, filters to each factor's non-null subset (preserving the shared pool's `(run_id, id)` order, matching `_factor_observations` row-for-row), and calls the SAME `_deciles` and `_rank_ic` builders that `compute_factor_lab` calls. No new rank-IC formula, no new decile math, no new risk-adjusted formula. The code comment states "BYTE-IDENTICAL to compute_factor_lab per factor (Single source of truth)."
- `factor_lab_all_cached` — wraps `compute_factor_lab_all` in the existing `EventStudyCache` pattern under sentinel namespace `_ALL_FACTORS_SUBJECT`/`_ALL_FACTORS_VIEW`. No new `table=True` model.

These functions are called via the existing `GET /api/research/factor-lab` endpoint (apps/backend/app/api/research.py) through an additive `all=true` query parameter. The registered canonical endpoint is unchanged in path.

**Frontend diff (apps/frontend/lib/api.ts):** `fetchFactorLabAll` calls `GET /api/research/factor-lab?all=true&horizon=...` — the registered canonical endpoint. The `FactorLabAllResponse` interface documents every field as a re-presentation of the existing `FactorLabResponse` values. No client-side rank-IC or decile computation.

**Frontend diff (apps/frontend/app/research/_labs.tsx):** The new `FactorsTable` component uses `useState` for `expanded`, `sortKey`, and `sortDir` — all pure view-transform state (expand/collapse rows; client-side sort). The sort comparator reorders an already-fetched `factors_table` array; it performs no arithmetic on any metric value. `fetchFactorLabAll` is the single fetch call; no fallback re-derivation.

No duplicate computation. No non-canonical source. The `_rank_ic` and `_deciles` builders remain the sole implementation of those metrics. **No violation.**

### Other registered values

No other registered Data Contract value is touched by this iteration. The `by_regime` slice is no longer rendered in the Factor Lab view but its computation in `compute_factor_lab` is explicitly noted as untouched. Not a violation — a value not rendered is not a coherence issue.

### New displayed values

Rank-IC (value + N) and downside risk-adjusted per catalog factor at the selected horizon are newly displayed side by side. The blueprint's J-107 registration confirms these are byte-identical re-presentations of existing Factor-Lab analytics — the same values the single-factor dropdown previously showed for each factor, now displayed together in one table. No new canonical concept; no synonym or re-derivation of a separately registered value. **No violation.**

---

## Part B — Information Architecture Check

### New routes and pages

Zero. The spec states "No new top-level nav section and NO new page: J-107 on the existing `/research/factor-lab` route." The diff confirms no new file under `app/` routing directories beyond `apps/backend/tests/`.

### J-107 canonical home

Blueprint extension (blueprint.md lines ~319-356) places J-107 on the existing `/research/factor-lab` route. The UI surface map confirms the only changed surface is `/research/factor-lab`. Navigation path verified statically:

- `apps/frontend/components/sidebar.tsx:37` — `{ href: "/research", label: "Research", icon: Microscope }` — 1 click from the persistent sidebar.
- `apps/frontend/app/research/page.tsx:32-33` — `{ href: "/research/factor-lab", title: "Factor Lab" }` — 1 more click from the Research hub.

Total: 2 clicks. **No violation.**

### Parallel shell / duplicate home

No new layout or shell introduced. No existing entity given a second home. The `/research/factor-lab` route uses the established app shell. **No violation.**

---

## Part C — Advisory Observations

None. The `fetchFactorLab` / `FactorLabResponse` export remains in `apps/frontend/lib/api.ts` (no longer imported by `_labs.tsx`). The spec explicitly accepts "annotate it as intentionally retained for the single-factor backend contract" as an alternative to cleanup. Since `fetchFactorLab` still calls the same canonical `GET /api/research/factor-lab` endpoint and is not used to display any value, this is a code-hygiene note only and not a coherence issue.

---

## Summary

All Part A and Part B checks pass with no violations. The iteration adds the all-factors Factor Lab table to the existing `/research/factor-lab` home, reuses the same canonical `_rank_ic`/`_deciles`/`_risk_adjusted` builders via a shared observation pool, serves through the same registered endpoint with an additive parameter, and leaves every other navigation path and data-contract source intact. The blueprint's J-107 annotation pre-registers and explicitly sanctions this implementation pattern.
