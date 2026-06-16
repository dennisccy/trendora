# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23
**Date:** 2026-06-16
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/themes` | Leaderboard table — five forward-return columns (1d/5d/10d/20d/60d) | New columns | J-81: surface equal-weight member-basket realized forward returns from stored data | Set as-of to a historical date with post-D bars; confirm five new column headers appear and each cell shows a percentage (not 0 or blank) for themes with member data |
| `/themes` | `SortHeader` on each forward-return column | New sortable header | J-81: allow user to sort leaderboard by realized return at any horizon | Click the "5d" column header twice; verify first click orders themes ascending with NA rows at the bottom, second click orders descending with NA rows still at the bottom |
| `/themes` | Forward-return cells — NA state (at/near latest date) | Changed behavior | J-81: honest NA where no future price bars exist yet | Navigate to `/themes` with as-of at the latest available date; confirm all five forward-return cells show muted "NA" text, not "0%" |
| `/themes` | `ForwardReturnCell` — colour grading | New component usage | J-81: sign-based colour grading reusing shared `@/components/forward-return` helper | On a historical as-of date, confirm a positive return cell is rendered in green and a negative return cell in red (matching the colour grading already visible on `/stocks`) |
| `/sectors` | Leaderboard table — five forward-return columns (1d/5d/10d/20d/60d) | New columns | J-81: surface each sector/industry ETF's own realized forward return | Set as-of to a historical date; confirm five new columns appear on the Sectors leaderboard with values for ETFs that have stored price bars |
| `/sectors` | `SortHeader` on each forward-return column | New sortable header | J-81: sort Sectors leaderboard by any forward-return horizon | Click the "20d" column header; verify rows reorder by that horizon's value with NA rows sinking to the bottom |
| `/sectors` | Forward-return cells — NA state for ETFs with no stored bar | Changed behavior | J-81: honest NA for industry ETFs with insufficient future data | On a historical as-of date, identify a sector ETF known to lack bars; confirm its forward-return cells show "NA" rather than a fabricated value |
| `/research` | Regime × Setup × Pattern table — Pooled default | Changed behavior | J-82(d): RSP section opens in Pooled mode by default | Navigate to `/research` and scroll to the RSP section; confirm the Pooled toggle is active on initial page load before any user interaction |
| `/research` | RSP table — NA-last sort | Changed behavior | J-82(a): numeric sort now pushes displayed-NA rows to the bottom in both directions | On the RSP table, click a numeric column header (e.g., Win Rate) to sort ascending; confirm all rows displaying "NA" appear below all rows with a numeric value; click again for descending and confirm the same |
| `/research` | RSP table — three filter dropdowns (Regime / Setup / Pattern) | New component | J-82(b): narrow RSP table rows by dimension without reloading | Open the Regime dropdown; select a specific regime label; confirm the table immediately shows only rows matching that regime; then also set the Pattern dropdown to a specific pattern and confirm both filters compose correctly |
| `/research` | RSP table — empty-after-filter state | New behavior | J-82(b): honest empty state when no rows match the active filters | Select a Regime and Pattern combination unlikely to appear together; confirm a non-broken empty state is displayed (not a blank table with no message) |
| `/research` | RSP table — N= chip for `pattern = none` rows | Changed behavior | J-82(c): samples backend now accepts the "none" pattern; chip previously 4xx'd | In the RSP table, locate a row where the Pattern cell shows "— (none)"; click its N= chip; confirm `/research/samples` opens in a new tab, loads successfully (no error page), and the displayed total matches the N value on the chip |
| `/research` | RSP table — N= chip for all other rows | Changed behavior | J-82(c): count coherence guaranteed for all emitted combinations | Click the N= chip on any RSP row in both Pooled and Episodes views; confirm the samples page loads without error and the count shown equals the row's N value |
| `/research` | Episodes / Pooled toggle — RSP section only | Changed behavior | J-82(d): RSP section now initialises to Pooled; rest of page unchanged | Navigate to `/research`; confirm the RSP section's toggle shows Pooled selected; then scroll to the event-study / cluster sections and confirm they still default to Episodes |
| `/research/samples` | Samples drill-down — RSP combinations kind | Changed behavior | J-82(c): non-emitted combinations now return 4xx instead of empty 200 | (Operator/dev test) Directly request `/research/samples` with a `(regime, setup, pattern)` combination that has no row in the RSP table; confirm the page shows an error rather than an empty cohort |
| `apps/frontend/lib/api.ts` | `ThemeRow` / `SectorRow` types — `forward_returns` field | Type update | J-81: frontend type contract updated to include `ForwardReturnEntry[]` | TypeScript build (`npx tsc --noEmit`) exits 0; the new columns compile without casting or `any` |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/snapshot_serving.py` — added `_leadership_returns_by_horizon` and `_forward_returns_from_projection` helpers; attaches `forward_returns` to each `/api/themes` and `/api/sectors` row. This directly powers the new leaderboard columns — not backend-only; UI impact accounted for above.
- `apps/backend/app/engine/samples.py` — widened `_regime_setup_pattern_samples` validation to exactly the emitted-combination set; removed `ALL_STATUSES`/`PATTERN_NONE` imports; added `_rsp_combination_members`. Directly powers the RSP N= chip drill-downs — not backend-only; UI impact accounted for above.
- `apps/backend/tests/test_iter23_leaderboard_returns.py` — new test file (12 tests for J-81 coherence and J-82 count correctness). Test-only; no UI surface impact.
- `apps/backend/tests/test_iter20_research_cluster.py` — updated `test_j77_samples_invalid_selectors_raise` to the reconciled J-82(c) contract. Test-only; no UI surface impact.

---

## Summary

- **Frontend surfaces changed:** 5 (themes page, sectors page, research page, research/samples page behavior, frontend type definitions)
- **New pages/routes:** 0
- **Modified components:** 4 frontend files (`themes/page.tsx`, `sectors/page.tsx`, `research/page.tsx`, `lib/api.ts`)
- **Navigation changes:** no (no new top-level nav, no new pages)
- **Backend-only changes:** 0 (all backend changes are fully surfaced in the UI; 2 test files are test-only artifacts)
