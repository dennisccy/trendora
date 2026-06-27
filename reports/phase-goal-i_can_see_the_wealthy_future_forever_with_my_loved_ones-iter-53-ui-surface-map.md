# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-53 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-53
**Date:** 2026-06-27
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|---|---|---|---|---|
| `/research` | Research hub `LABS` tile list | Navigation added | New Regime Lab capability needs a hub entry point | Navigate to `/research`; confirm a tile labelled "Regime Lab" with a Gauge icon is present and its link resolves to `/research/regime-lab` |
| `/research/regime-lab` | `RegimeLabPage` (new lazy sub-route) | New page | J-110: new cross-sectional regime-return lab | Navigate to `/research/regime-lab`; confirm the page title renders, the survivorship-bias caveat banner (`ResearchCaveat`) is visible, and no native `input[type=date]` element is present on the page |
| `/research/regime-lab` | `RegimeLabByLabelTable` (6-row by-label table) | New table | Shows mean return + MDD per regime label at each configured horizon | Confirm exactly 6 rows appear (one per canonical regime label, e.g. "Risk-on", "Risk-off"); confirm each row has a forward-return cell and a paired max-drawdown cell for each of the 1/5/10/20/60-day horizons |
| `/research/regime-lab` | `RegimeLabDecileTable` (D1–D10 decile table) | New table | Shows return + MDD per regime-score decile with rank-IC | Confirm a Rank-IC header row appears above D1–D10 rows; confirm each decile row shows a score range and paired (return, MDD) cells per horizon; confirm 10 data rows render (D1 through D10) |
| `/research/regime-lab` | `RegimeSortHeader` on both tables | New component | Columns must be sortable NA-last in both directions | Click the sort header for a return column (resolve by `aria-label`); confirm the by-label table rows reorder and NA values appear last; click again to confirm reverse sort produces a byte-distinct frame |
| `/research/regime-lab` | As-of / All-history toggle (`ResearchControls`) | New component | Enables point-in-time filtering of the observation pool | Toggle the mode to As-of; confirm the n values shown in the `N=` chips decrease compared to All-history mode; confirm no second date picker or `input[type=date]` appears |
| `/research/regime-lab` | `N=` chip on each return cell (both tables) | New component | Count-coherent drill-down into Research Samples | Click the `N=` chip on a by-label return cell (e.g. Risk-on, 20d); confirm `/research/samples` opens in a new browser tab; confirm the Samples page "Total observations" value matches the number shown in the clicked chip |
| `/research/regime-lab` | `N=` chip carrying `?asof` query param | New component | As-of scope must flow through to Samples so counts stay coherent | With As-of mode active, click any `N=` chip; confirm the new-tab URL contains `asof=` and the Samples "Total observations" matches the n shown in the chip under As-of mode |
| `/research/regime-lab` | Loading skeleton (`LabSkeleton`) | New component | Page must handle in-flight fetch gracefully | Throttle the network or load the page with a slow connection; confirm a loading skeleton (not a blank page or spinner-less white screen) appears before data loads |
| `/research/regime-lab` | Error card (`ResearchError`) | New component | Page must handle backend-unavailable state | Stop the backend; load `/research/regime-lab`; confirm a "Backend unavailable" card appears instead of a broken or blank layout |
| `/research/regime-lab` | `EmptyState` + explicit NA cells | New component | Thin-sample and near-latest buckets must show NA, never a fabricated number | If any decile or label bucket has n below the configured `min_sample`, confirm the cell shows "NA" with the count, not a numeric return value |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/research.py` — `compute_regime_lab`, `_regime_lab_members_by_horizon`, `regime_lab_cached`, `_REGIME_LAB_SCHEMA_TOKEN`, `_regime_meta_by_run` — computation engine and cache layer consumed via the new API route; no independent UI surface
- `apps/backend/app/engine/samples.py` — `KIND_REGIME_LAB`, `_regime_lab_samples`, `ALL_KINDS` update — samples cohort builder consumed via the existing `/research/samples` endpoint; no new UI surface (the endpoint already exists)
- `apps/backend/tests/test_regime_lab.py` (new) — test file; no UI impact
- `apps/backend/tests/test_api_research.py` — updated test file; no UI impact
- `apps/backend/tests/test_samples.py` — updated test file; no UI impact
- `apps/frontend/lib/api.ts` — `fetchRegimeLab` + `RegimeLab*` response/row types — frontend API client and type definitions; not a rendered surface; consumed by `RegimeLabPage`
- `apps/frontend/lib/samples-link.ts` — `RegimeLabCohortParams` + `buildSamplesHref` serialization — link-building utility; not a rendered surface; consumed by `N=` chip hrefs

---

## Summary

- **Frontend surfaces changed:** 11
- **New pages/routes:** 1 (`/research/regime-lab`)
- **Modified components:** 1 (Research hub `/research` — new tile added)
- **Navigation changes:** yes (new "Regime Lab" tile on `/research` hub; no top-level nav skeleton change)
- **Backend-only changes:** 7
