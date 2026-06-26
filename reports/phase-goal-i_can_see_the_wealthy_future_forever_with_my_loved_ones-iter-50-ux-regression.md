# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50 — UX Regression Review

**Date:** 2026-06-26

**Verdict:** UX-REGRESSION-PASS

---

## New Capability Discoverability

### J-107 — All-factors comparison table on `/research/factor-lab`

**Navigation path:** Dashboard → Research (sidebar nav) → Factor Lab (hub card) → `/research/factor-lab`

- Click 1: "Research" sidebar link → `/research` hub
- Click 2: "Factor Lab" card → `/research/factor-lab` with all-factors table loaded

Verified by UT-17 (PASS with evidence `UT-17-factor-lab-navigation.png`). Reachable within 2 clicks from the home page.

**Label clarity:** The page heading "Research — Factor Lab" is unchanged. The subtitle now reads "Which factors actually sort future returns? Every catalog factor's rank-IC + a downside risk-adjusted figure at the chosen horizon — sortable, and expandable in place to its full decile sort." This is clear to a non-technical user: it describes what the table shows and what actions are available without requiring developer knowledge.

**Visual feedback:**
- Sorting: clicking a column header produces an immediate client-side reorder; sort-direction caret is present on the active header (reuses the `SortHeader` pattern from `/sectors` and `/stocks`).
- Expand/collapse: clicking a factor row reveals or hides the `DecileTable` panel (aria-expanded toggle pattern borrowed from the Sectors page).
- Horizon / As-of changes: all rows update simultaneously with a loading skeleton transition (UT-11 and UT-12 both PASS).
- Error state: "Backend unavailable" panel renders explicitly; no fabricated rows (UT-16 PASS).

### New actions within the table

| Action | Entry point | Clicks from home | Verdict |
|---|---|---|---|
| Sort all factors by Rank-IC / N / Risk-adjusted | Column header button on `/research/factor-lab` | 2 + header click | Discoverable |
| Expand a factor row to see D1–D10 decile sort | Click any factor row | 2 + row click | Discoverable |
| Collapse an expanded factor row | Click expanded row again | 2 + row click | Discoverable |
| Drill into Research Samples from a decile N= chip | Click N= chip inside expanded row | 2 + row click + chip click | Discoverable (3 clicks but the chip is visible in context) |

The N= chip drill-down requires 3 actions from home (navigate → expand → click chip), which is 1 click beyond the 2-click ideal. However, the chip is contextually exposed (only after expanding a row), which is the appropriate progressive-disclosure pattern. This is NOT flagged as undiscoverable because the chip is part of a nested detail view, not a standalone capability.

---

## Regression Risk

### `apps/frontend/app/research/_labs.tsx` — contains both FactorLabPage and FactorCombinationPage

**Risk level: Low**

The file is shared but the changes were scoped exclusively to `FactorLabPage` internals. `FactorCombinationPage` (J-26, line 3301 in _labs.tsx) was not modified. Shared utilities (`DecileTable`, `HorizonSelector`, `ResearchControls`, `SampleLink`, `WarmingState`, `ResearchError`, `LabSkeleton`) are all preserved and still consumed by `FactorCombinationPage` and the event-study lab pages. The `fetchFactorCombination` import and call site are untouched.

A `by_regime` reference remains at line 1587 of `_labs.tsx` — this is in the `EventStudyRegimeTable` component used by the event-study labs (J-77, J-91, J-103), not the `RegimeEffectivenessTable` that was removed from the Factor Lab. These are different components. No regression risk here.

### `apps/frontend/lib/api.ts` — additive additions only

**Risk level: None**

`FactorTableRow`, `FactorLabAllResponse`, and `fetchFactorLabAll` were added. The existing `FactorLabResponse` interface and `fetchFactorLab` function are preserved and exported unchanged (confirmed at lines 1092–1126). The single-factor API endpoint still works and is used by the Research Samples cohort drill-down links.

### Prior feature navigation integrity

All routes from prior phases continue to be served:
- `/research/factor-lab` — now shows all-factors table (J-107 replaces J-25 single-factor dropdown, by design)
- `/research/factor-combination` — `FactorCombinationPage` component untouched
- `/stocks` — J-106 "Proximity to 52w high" column unchanged (files `app/stocks/page.tsx`, `lib/high-proximity.ts` not touched in iter-50)
- Readiness badge (J-108) — `lib/api-base.ts` and `lib/api.ts` host-aware resolution unchanged in iter-50

---

## UI vs Backend Parity

| Backend capability | UI exposure | Parity |
|---|---|---|
| All-factors aggregate via `GET /api/research/factor-lab?all=true` | `FactorsTable` on `/research/factor-lab` — all 11 catalog factors rendered with family, Rank-IC, N, risk-adjusted | Full parity |
| Per-factor D1–D10 decile rows in `factors_table[].deciles` | `DecileTable` in click-to-expand row panels | Full parity |
| Horizon selection (HorizonSelector) | Remains in controls bar; updates all rows simultaneously | Full parity |
| As-of mode filter (single global as-of) | Remains in controls bar; N values change globally (UT-12 PASS) | Full parity |
| `by_regime` slice (per-regime effectiveness) in single-factor API response | Intentionally not displayed on this view (spec-driven removal) | Intentional backend-only data — acceptable |
| Single-factor API mode (`?factor=<key>`) | Not displayed as a user-facing page; still called internally for SampleLink cohort coherence | Acceptable — no UI entry point needed for the internal path |

---

## Flags

### Hidden Capabilities

None. All backend capabilities delivered in this iteration are surfaced in the UI.

### Undiscoverable Capabilities

None. All new actions are reachable within the Factor Lab page which is itself 2 clicks from home.

### Potential Regressions

None requiring action. The one shared file (`_labs.tsx`) was modified only within `FactorLabPage`'s scope, and all shared components consumed by other lab pages are unchanged. The browser QA summary states "all smoke and regression tests pass," which is consistent with the narrow change footprint.

### Visual Consistency

The all-factors table reuses established design-system patterns throughout:
- `Card` lab shell (same as all other research lab pages)
- `SortHeader` column sort buttons (same pattern as `/sectors` and `/stocks`)
- `aria-expanded` expandable-row pattern (same as Sectors page)
- `DecileTable` and `SampleLink` chips (same components as before, rehoused inside the expand panel)
- `returnClass` / `fmtRatio` / `fmtPct` formatters for coloured numeric cells
- `border/surface/accent` tokens and `num` font class for numeric columns
- No ad-hoc colours, no new component-library primitives

No visual inconsistency detected.

### UT-03 Sort Behavior Note

The browser QA result recorded UT-03 as FAIL (first column-header click produced ascending order, not descending). This is a test-plan expectation error, not a product defect. The table defaults to descending Rank-IC on load (strongest factors first). The first click on the already-descending Rank-IC header correctly toggles to ascending — standard sortable-table UX behavior. UT-04 (second click reverses to descending) PASSED, confirming the toggle mechanism works. The iter-50 spec explicitly documents this correction. No UX regression.

---

## Recommendation

No action required.

The iter-50 Factor Lab redesign is fully discoverable, visually consistent with the established design system, and does not regress any prior user journey. The one browser QA failure (UT-03) is a documented test-plan expectation bug that the spec pre-corrected; the underlying sort behavior is correct. The two P2 skips (UT-14 loading skeleton, UT-15 zero-N rows) are environment-driven precondition gaps and do not indicate missing UI behavior.
