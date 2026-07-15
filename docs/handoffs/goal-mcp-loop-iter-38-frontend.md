# goal-mcp-loop-iter-38 Frontend Handoff

**Phase:** goal-mcp-loop-iter-38
**Date:** 2026-07-15
**Agent:** developer
**Status:** complete

## What Was Built

- **New "Concentration X-ray" section on `/watchlist`** (additive — one new `Card` block stacked
  below the existing entries table, same `space-y-4` layout rhythm, no new page/route, no navigation
  change): pairwise return-correlation matrix heatmap, deterministic correlation-threshold clusters
  (rendered as `Badge` chips), a headline "≈ N.N effective independent bets (over the last W trading
  days)" with an `InfoTooltip` explaining the methodology, and three concentration-bar breakdowns
  (sector, theme, shared setup status).
- **`components/correlation-heatmap.tsx`** (new) — the correlation matrix grid: a compact cell-grid
  table (same spirit as `availability-heatmap.tsx`'s cell grid, far smaller — no virtualization needed
  at watchlist scale). Cells reuse the page's EXISTING sign tokens (`text-pos` / `text-neg` / muted) —
  the SAME family `price_since_added` already uses on this page — never a new color scale. An
  undefined/insufficient-history pair renders an honest NA cell (`—`, muted text, dashed border)
  rather than a fabricated number; hovering any cell shows the exact figure (or the exact reason for
  NA — how many days of history each side actually has) via `title`.
- **`WatchlistXraySection` / `ConcentrationBars`** local components in `app/watchlist/page.tsx`
  (mirroring the file's existing pattern of page-local components like `WatchlistRow`): the ENB
  headline, the matrix, the cluster badges, and the three concentration-bar lists. The shared-setup
  bars reuse the existing `setupVariant()` Badge coloring (the SAME mapping the entries table's Setup
  column already uses) since setup status carries an established, meaningful color vocabulary; sector
  and theme names carry no such established meaning, so they stay plain-text labels next to their bars
  rather than an arbitrary/misleading color.
- **Honest empty/insufficient state**: a watchlist with fewer than 2 names renders a distinct
  `EmptyState` ("Not enough names yet for an X-ray") — same visual family as the existing zero-entries
  `EmptyState`, deliberately different copy. The existing page-level "Backend unavailable" error state
  already covers the X-ray section since it rides the same `GET /api/watchlist` response — no separate
  fetch/error/loading state was added (the existing `WatchlistSkeleton` already covers the loading
  window for the whole page, including where the X-ray will render).
- **Zero browser-side recompute**: every number in the section — correlations, cluster membership, the
  ENB figure, and all three concentration breakdowns — is read verbatim from `data.xray` (the additive
  field `GET /api/watchlist` now serves). No client-side correlation, eigenvalue, or grouping logic.
- **`WatchlistXray` type family** in `lib/api.ts` (see the dev handoff) so the page and the new
  component are fully typed against the served payload shape.

## Files Changed

- `apps/frontend/lib/api.ts` — added `WatchlistXray`, `WatchlistXraySectorConcentration`,
  `WatchlistXrayThemeConcentration`, `WatchlistXraySetupConcentration`; extended `WatchlistResponse`
  with `xray: WatchlistXray`
- `apps/frontend/components/correlation-heatmap.tsx` (new) — `CorrelationHeatmap` component
- `apps/frontend/app/watchlist/page.tsx` — imports + `WatchlistXraySection` render call after the
  existing entries table (gated on `entries.length > 0`); new `WatchlistXraySection` and
  `ConcentrationBars` local components

## Visual / UX Notes

- Component library: `Card`, `Badge` (existing variants only — `ok`/`warn`/`danger`/`accent`/`default`),
  `EmptyState`, `InfoTooltip` — no new UI primitives introduced.
- Design tokens only: `text-pos`/`text-neg`/`text-text-muted`/`text-text-faint`, `bg-accent`,
  `bg-surface`/`bg-surface-2`, `border-border`/`border-dashed` — no arbitrary colors, no new effects
  (no glassmorphism/glow, matching this page's existing dense/minimal look).
- `data-testid` hooks added for browser-qa: `watchlist-xray`, `watchlist-xray-matrix`,
  `watchlist-xray-cell` (with `data-row`/`data-col`/`data-na` attributes), `watchlist-xray-enb`,
  `watchlist-xray-clusters`, `watchlist-xray-sector`, `watchlist-xray-theme`, `watchlist-xray-setup`.

## Tests Run

Command: `cd apps/frontend && npx tsc --noEmit`
Result: exit 0, zero type errors

Frontend has no configured test runner (`package.json` defines no `test` script; the few existing
`lib/*.test.ts` files test pure frontend logic like `sector-label.ts` and are not wired to any CI
command in this repo). This iteration introduces no new frontend pure-function logic warranting a unit
test (the component is presentation-only, reading the server payload verbatim) — consistent with the
existing convention, no new `.test.ts` file was added.

**Live browser verification** (Chrome DevTools automation against `scripts/dev.sh`, real production
seed): navigated to `/watchlist`, confirmed the X-ray section renders with the correlation matrix
(symmetric, correct sign coloring, correct hover-title text), the ENB headline (`≈ 2.0` for the two
real watchlist entries, matching the closed-form 2-asset math), working cluster badges, sector/theme
bars (correctly bucketing a null-sector member visually via the existing `sectorLabel()` helper), and
the shared-setup bar with the `setupVariant()`-colored "Avoid" badge matching the main table's Setup
column color. Clicked the `InfoTooltip` trigger and confirmed the methodology panel opens with the
expected text. Checked the browser console — no errors (`get_console_messages` returned only the
standard React DevTools info line). Confirmed all `data-testid` hooks resolve in the live DOM.

## Known Issues

- None specific to the frontend. See the dev handoff's "Known Issues" for the shared backend/test-suite
  notes (slow `loaded_engine` fixture, no project-wide lint config — both pre-existing).
