# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20
**Date:** 2026-06-15
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/stocks` | Leaderboard table — five new forward-return columns (1d / 5d / 10d / 20d / 60d) | New columns | J-75: expose stored realized forward returns per stock | At a historical date (e.g. `?asof=2021-01-04`) click the "5d" column header and verify the table re-orders with highest 5d returns first and any "NA" cells sort to the bottom |
| `/stocks` | Leaderboard table — forward-return cells | Updated layout | J-75: colour-grade cells by sign; NA where no stored row | Pick a stock row at a historical date and confirm a positive return shows in green text, a negative return in red, and a cell with no post-date data shows "NA" in muted text |
| `/stocks/[ticker]` | "Realized forward returns" panel (new card above price chart) | New component | J-75: show the same five returns on the Stock Detail page | Navigate to `/stocks/AAPL?asof=2021-01-04`, confirm the new "Realized forward returns" panel appears above the chart and displays five tiles (1d, 5d, 10d, 20d, 60d) with colour-graded values matching the leaderboard row for AAPL at that date |
| `/stocks/[ticker]` | "Realized forward returns" panel — NA state | Updated layout | J-75: near latest date all five are honestly NA | Navigate to `/stocks/AAPL` (no `?asof`, latest date), confirm all five tiles in the "Realized forward returns" panel show "NA" |
| `/research` | "Regime × Setup × Pattern" study section (new section below Event Study) | New component | J-77: ranked evidence table for regime/setup/pattern combinations | Scroll to the new study section, confirm the table renders with columns Regime, Setup, Pattern, N, Mean, Median, Hit-rate, Expectancy, and two risk-adjusted columns; click the "Mean" header and confirm the table re-orders |
| `/research` | Regime × Setup × Pattern — Episodes / Pooled toggle | New component | J-77: independent view toggle for the new study | Click "Pooled" on the new study's toggle, confirm the table re-fetches/re-renders independently without reloading the rest of the page or resetting other study toggles |
| `/research` | Regime × Setup × Pattern — N= chip (sample count link) | New component | J-77: each row's chip must open the exact drill-down in a new tab | Click the `N=` chip on any non-NA row in the Regime × Setup × Pattern table and confirm a new tab opens at `/research/samples` showing the correct combination in the heading and a total sample count equal to the published N in the table row |
| `/research` | Regime × Setup × Pattern — low-sample / NA rows | Updated layout | J-77: combinations below min-sample threshold render NA + n | Confirm that rows with low observation counts display "NA" in the return columns while still showing the actual n count in the N column |
| `/research` | Per-section independent loading skeleton | Changed behavior | J-72/J-15: each lab section fetches independently so no single slow query blocks the page | On a cold backend (first load), watch the `/research` page and confirm the Combination Lab and Regime × Setup × Pattern sections become interactive before the Event Study section finishes loading (each section shows its own skeleton separately) |
| `/research` | Event Study section — figures (unchanged values, faster) | Changed behavior | J-72: event-study now served from cache; numbers must be byte-identical | Load the Event Study on `/research` twice in succession; confirm the second load is visibly faster and the displayed figures (mean, median, hit-rate) are identical between the two loads |
| `/research/samples` | Cohort heading for `regime-setup-pattern` kind | Changed behavior | J-77: `describeCohort` gains a new branch rendering the combination description | Open the samples drill-down from a Regime × Setup × Pattern N= chip and confirm the page heading identifies the specific combination (e.g., "Bear / Avoid / — (none) — Episodes") rather than showing a generic or empty heading |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/models.py` — new `EventStudyCache` table (standalone cache for computed event-study payloads, keyed by subject + view + as-of + dataset-version). Created automatically on startup; no migration step required; not user-visible (it is an internal speed cache).
- `apps/backend/tests/test_iter20_research_cluster.py` — 15 new unit/property tests for J-72 byte-identity, J-75 serving, and J-77 grouping/count-coherence. Tests only; no UI surface.
- `apps/backend/tests/test_api_research.py` — 10 appended API-level tests. Tests only; no UI surface.

---

## Summary

- **Frontend surfaces changed:** 4 (routes: `/stocks`, `/stocks/[ticker]`, `/research`, `/research/samples`)
- **New pages/routes:** 0 (all surfaces land on existing IA homes; no new top-level route)
- **Modified components:** 6 frontend files changed (`lib/api.ts`, `lib/samples-link.ts`, `app/research/page.tsx`, `app/stocks/page.tsx`, `app/stocks/[ticker]/page.tsx`, `app/research/samples/page.tsx`)
- **Navigation changes:** no (no new top-level nav entry; drill-down via N= chips reuses the existing `/research/samples` route)
- **Backend-only changes:** 3 (cache table model, two test files)
