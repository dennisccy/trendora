# Phase goal-mcp-loop-iter-22 — UI Surface Map

**Phase:** goal-mcp-loop-iter-22
**Date:** 2026-07-08
**Written by:** ui-impact-analyst

---

## File Classification

Per `.claude/skills/diff-to-ui-impact.md`, verified against the live codebase (grep + diff), not just the dev handoff's claims:

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `config.yaml` | config | indirect (confirmed) | Adds 5 `index_chart.symbols` entries (`^SPX`/`^NDX`/`^DJI`/`^VIX`/`^TNX`). Feeds `compute_index_series` → `GET /api/indexes` → both live chart surfaces and the new `/data` panel. |
| `apps/backend/app/engine/indexes.py` | backend-api | indirect (confirmed) | `compute_index_series` gains additive `vendor`/`first` fields on `GET /api/indexes`. Confirmed consumed: `lib/api.ts`'s `IndexSeries` type, rendered in the live chart's legend/tooltip and in `IndexVendorPanel`. |
| `apps/backend/app/engine/data_manager.py` | backend-internal | none (direct) | New `load_seed_meta` / `_read_seed_meta_rows` helpers are internal to the engine layer; only `indexes.py` calls them. No route/UI touches this file directly. |
| `apps/backend/scripts/load_missing_index_symbols.py` (new) | backend-internal | none | One-time CLI data-loading script; not reachable from any API route or UI action. |
| `apps/backend/tests/test_indexes.py`, `test_api_indexes.py`, `test_data_manager.py`, `test_load_missing_index_symbols.py` (new) | backend-internal (tests) | none | Test coverage only. |
| `apps/frontend/lib/api.ts` | frontend-direct (typed contract) | direct | `IndexSeries` gains `vendor: string \| null` and `first: string`, consumed directly by the components below. |
| `apps/frontend/app/globals.css` | frontend-direct | direct | 4 new CSS custom properties (`--chart-orange`/`--chart-lime`/`--chart-blue`/`--chart-pink`) directly change on-screen line colors. |
| `apps/frontend/components/index-regime-chart.tsx` | frontend-direct | **none — dead code** | Vendor label + palette fix applied, but this component is not imported by any route (verified independently via repo-wide grep: zero import hits). Zero live effect. |
| `apps/frontend/components/phase-cross-view-chart.tsx` | frontend-direct | **direct — LIVE** | The actual chart rendered on the Dashboard (via `PhaseCrossViewCard` in `app/page.tsx`). The vendor label + palette fix here is what users actually see. |
| `apps/frontend/components/index-vendor-panel.tsx` (new) | frontend-direct | **direct — LIVE** | New `/data` panel component. |
| `apps/frontend/app/data/page.tsx` | frontend-direct | **direct — LIVE** | Wires `<IndexVendorPanel />` into the page, directly after `<MacroFeedPanel />`. |
| `apps/frontend/components/major-indexes-card.tsx` | frontend-direct | none — unmodified | Not changed this iteration (verified: 0 diff). Listed for context only — it is the orphaned wrapper around `index-regime-chart.tsx` above. |

**Load-bearing finding (verified independently, not just taken from the dev handoff):** `app/page.tsx` imports and renders `PhaseCrossViewCard` only. A repo-wide grep for `MajorIndexesCard`, `major-indexes-card`, and `IndexRegimeChart` returns zero import sites anywhere in `apps/frontend/`. `app/page.tsx`'s own code comment (line ~157) confirms the old "Major indexes & regime" card was removed in a prior iteration (J-101a) as a duplicate of this chart's pane 0. **The phase spec and plan's references to "the Dashboard major-indexes chart" and the file `index-regime-chart.tsx` describe a component that is not currently reachable by any user** — the actual live surface satisfying J-14's DoD is `phase-cross-view-chart.tsx` / the "Regime × phase cross-view" card. This is reflected in the rows below.

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | "Regime × phase cross-view" card — legend (`PhaseCrossViewChart` in `components/phase-cross-view-chart.tsx`, rendered via `PhaseCrossViewCard`) | Changed behavior | J-14: surface deep `^SPX`/`^NDX`/`^DJI` benchmarks + `^VIX`/`^TNX` overlays, each with an honest vendor label | Load `/`, scroll to the "Regime × phase cross-view" card, and confirm its legend lists 10 series including "S&P 500 Index (^SPX) (Stooq)", "CBOE Volatility Index (^VIX) (Yahoo)", and "10Y-2Y spread proxy (^TNX) (FRED-macro proxy)"; confirm the 5 original entries (S&P 500 (SPY), Nasdaq 100 (QQQ), Russell 2000 (IWM), S&P 500 Equal-Weight (RSP), Dow 30 (DIA)) show **no** vendor suffix. |
| `/` | same chart — hover tooltip | Changed behavior | Vendor label must also appear on hover, not only in the legend | Hover over any date on the chart and confirm the tooltip lists each visible series with a "· <vendor>" suffix (e.g. "^SPX · Stooq") for the 5 new lines, and **no** "·" suffix for the 5 ETF lines. |
| `/` | same chart — line color palette (`LINE_PALETTE_VARS`, extended 5→10) | Changed behavior (visual) | Verified defect: the old 5-color array would wrap (`index % 5`) once more than 5 lines render, making line 6 visually identical to line 1 | With the default "all" range (all 10 lines visible), compare the 10 legend color swatches and confirm no two are the same color — specifically confirm the 6th line's swatch (the `--snapshot` purple token) is visibly different from the 1st line's swatch (the `--accent` teal token), which is what the old 5-slot palette would have produced as an exact repeat. |
| `/` | same chart — deep history range | New data | `^SPX`/`^NDX`/`^DJI` real first bar is 1996-01-02 per `meta.json`, ~9–25 years before the ETF lines | On the default "all" range, confirm the ^SPX line's plotted path starts visibly earlier on the x-axis than the SPY line's path (SPY has no data before ~2005); zoom toward the left edge of the timeline and confirm a point exists for ^SPX around 1996-01-02 where no SPY point exists. |
| `/data` | new "Index & benchmark data provenance" panel (`components/index-vendor-panel.tsx`) | New component | J-14 disclosure requirement — same `GET /api/indexes` data as the chart, listed in a standalone table | Load `/data`, scroll to directly below the existing "Macro feed" panel, and confirm a new card titled "Index & benchmark data provenance" renders a table with columns Series / Vendor / First bar, containing a row for "S&P 500 Index (^SPX)" showing vendor badge "Stooq" and First bar "1996-01-02". |
| `/data` | same panel — honest-omission rows | New component (data honesty) | ETF lines have no vendor record in `meta.json`; the panel must never fabricate one | In the same table, confirm the row for "S&P 500 (SPY)" shows vendor badge "—" (not a fabricated vendor name) and First bar "—" (an honest dash, not "Invalid Date" or a blank/broken cell). |
| `/data` | same panel — error state | New component (states) | DoD requires honest degrade — "could not load," never a blank/fabricated row | Stop the backend, reload `/data`, and confirm the new panel shows the "Vendor disclosure unavailable" alert with an AlertTriangle icon (not a blank area or a crashed page), while the rest of `/data` continues to render normally. |
| `/data` | same panel — loading state | New component (states) | Panel has its own independent loading state | Throttle the network or observe the initial page load and confirm the panel briefly shows an animated skeleton block before the table appears, rather than a layout jump or blank gap. |
| *(no route — confirms non-surface)* | `components/major-indexes-card.tsx` / `components/index-regime-chart.tsx` (orphaned "J-44 Major indexes & regime" card) | Changed behavior (code only, unreachable) | The plan's literal file list named `index-regime-chart.tsx`; the developer applied the identical fix here too for consistency even though it is dead code | Grep the frontend route tree (`apps/frontend/app/**/*.tsx`) and the rest of `apps/frontend/components/` for imports of `MajorIndexesCard` or `IndexRegimeChart` and confirm **zero** results outside their own defining files — this card must not be reachable from any page. QA should not spend time looking for a second "Major indexes & regime" card on any route; only the "Regime × phase cross-view" card (rows above) is live. |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/data_manager.py` (`load_seed_meta`, `_read_seed_meta_rows`) — internal seed-manifest reader helpers, called only by `indexes.py`; no route or component reads this file directly — no UI surface affected on its own.
- `apps/backend/scripts/load_missing_index_symbols.py` (new) — a one-time, idempotent CLI script that backfilled `^SPX`/`^NDX`/`^DJI` bars into the local `daily_prices` table. Run once by hand outside the running application; no UI/API trigger exists or is intended — no UI surface affected.
- `apps/backend/tests/test_indexes.py`, `test_api_indexes.py`, `test_data_manager.py`, `test_load_missing_index_symbols.py` (new) — test coverage for the above; no UI surface affected.

---

## Summary

- **Frontend surfaces changed (live, user-reachable):** 2 (Dashboard "Regime × phase cross-view" chart; `/data` "Index & benchmark data provenance" panel)
- **New pages/routes:** 0 (both surfaces are on existing routes: `/` and `/data`)
- **Modified/new frontend files:** 6 (`lib/api.ts`, `globals.css`, `index-regime-chart.tsx` [dead code], `phase-cross-view-chart.tsx` [live], `index-vendor-panel.tsx` [new, live], `app/data/page.tsx` [live])
- **Navigation changes:** no
- **Backend-only changes:** 6 files (`data_manager.py`, `load_missing_index_symbols.py`, and 4 test files)
