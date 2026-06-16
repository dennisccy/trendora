# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23
**Date:** 2026-06-16
**Agent:** developer
**Status:** complete

## What Was Built

### J-81 — Themes leaderboard (`/themes`)
- Five forward-return columns (1d/5d/10d/20d/60d), one per server-supplied horizon (read from the first row's `forward_returns` order — no hardcoded `[1,5,10,20,60]` in the UI).
- Each cell is the served **equal-weight member-basket** realized forward return, colour-graded by sign via the shared `@/components/forward-return` helper (`fmtPct` + `returnClass`). NA-honest: a horizon with no member return renders muted "NA", never a fabricated 0%.
- The `#` and `Theme Score` columns plus all five forward-return columns are client-side sortable (`SortHeader`). Sort is a pure J-48 view transform — it re-orders the already-served rows, recomputes/refetches nothing, default order stays the served theme rank, and NA cells sink last in both directions (stable rank tie-break).

### J-81 — Sectors leaderboard (`/sectors`)
- The same five sortable, colour-graded, NA-honest columns, each showing the **sector/industry ETF's own** realized forward return. Industry ETFs without a stored bar render NA honestly.
- The page already had a local no-sign `fmtPct` (dist-from-52w-high); the shared forward-return `fmtPct` is imported aliased as `fmtFwdPct` to avoid the collision.

### J-82 — Research Regime × Setup × Pattern table (`/research`)
- **NA-last sort (a):** the numeric-column sort now treats a cell as NA with the SAME predicate the cell display uses (`low_sample || n === 0 || value === null`), so a low-sample row whose raw value is non-null (DISPLAYS NA) now also SORTS NA — last in both directions.
- **Filter dropdowns (b):** three "All"-default `<Select>` controls (Regime / Setup / Pattern), vocabulary from the config-driven payload (`regime_labels` / `setups` / `patterns` + the `pattern_none` sentinel rendered as "— (none)"). Pure view transforms that compose with the sort; an honest empty-after-filter state when no combination matches.
- **N= chip (c):** every displayed row's N= chip (including `pattern = none` rows) opens `/research/samples` for that exact `(regime, setup, pattern)` combination in a new tab without a 4xx (the backend reconciliation makes this hold; the chip already passed `row.pattern` verbatim).
- **Pooled default (d):** the RSP section's Episodes ⇄ Pooled toggle now initialises to **Pooled** (Episodes one click away). The rest of `/research` keeps its Episodes default — separate, independent toggle state; no canonical figure changed.

## Files Changed
- `apps/frontend/lib/api.ts` — `forward_returns: ForwardReturnEntry[]` added to `ThemeRow` and `SectorRow`; new shared `ForwardReturnEntry` type (`StockForwardReturn` aliased to it).
- `apps/frontend/app/themes/page.tsx` — sort state, stable NA-last memo, `SortHeader` + `ForwardReturnCell`, five columns + cells; expanded-panel colSpan recomputed for the new columns.
- `apps/frontend/app/sectors/page.tsx` — same as themes; aliased shared `fmtPct`.
- `apps/frontend/app/research/page.tsx` — RSP NA-last sort (display predicate), `RspFilters` (three dropdowns) + filter state + empty-after-filter state, Pooled default toggle initial state.

## Tests Run
- `cd apps/frontend && npx tsc --noEmit` → exit 0 (no type errors).
- ESLint is not configured in this project (`next lint` prompts for setup) — not run.
- Backend API endpoints exercised end-to-end via FastAPI TestClient in `apps/backend/tests/test_iter23_leaderboard_returns.py` (the served `forward_returns` field and the RSP samples drill-down are proven against the real app).

## Visual / Design Notes
- All new cells reuse the existing leaderboard table + sortable column-header pattern (matching the J-75 forward-return columns on `/stocks`) and the shared `@/components/forward-return` colour grading (positive/negative/neutral design tokens) — no parallel formatter, no new visual effects.
- Layout is additive only: extra columns inside the existing tables; the three RSP filters sit in the section's existing controls row alongside the Episodes/Pooled toggle.
- States handled: NA-honest cells; "All"-default filters with empty-after-filter; existing loading/empty/error treatments unchanged.

## Known Issues
- Live browser verification (set as-of to a historical date with post-D bars; cross-check a theme/sector value against Backtest; exercise the RSP filters/sort/N= chip incl. a `pattern = none` row) is the browser-qa stage's job. Use ports backend 8835 / frontend 3835; never broad-`pkill`. Drive the controlled filter `<select>`s via native-setter + bubbling `change` event, then assert live DOM (Chrome MCP `select` doesn't fire React onChange on this frontend).
