# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-17 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-17
**Date:** 2026-06-15
**Agent:** developer
**Status:** complete

## What Was Built (UI)

Two presentation upgrades on existing surfaces — no new page, no new nav entry, no new fetch.

### J-74 — `/data` availability heatmap: multi-hue scale + legend + per-bucket legible day numbers
- The density grid now uses a **perceptually-ordered multi-hue scale** across the six buckets:
  - bucket 0 (none) — **slate** `bg-heat-0`, day number near-white `text-heat-text-0`
  - bucket 1 (<25%) — **blue** `bg-heat-1`, day number near-white `text-heat-text-1`
  - bucket 2 (25–50%) — **cyan** `bg-heat-2`, day number dark `text-heat-text-2`
  - bucket 3 (50–75%) — **teal-green** `bg-heat-3`, day number dark `text-heat-text-3`
  - bucket 4 (75–<100%) — **green** `bg-heat-4`, day number dark `text-heat-text-4`
  - bucket 5 (full) — **amber** `bg-heat-5`, day number dark `text-heat-text-5`
- The **legend** (`data-testid="availability-legend"`) renders one swatch per bucket using the same
  `BUCKET_CLASS` map, so each colour is keyed to its coverage level (none / <25% / 25–50% / 50–75% /
  75–<100% / full), plus the snapshot-ring example.
- Tokens are defined once: `--heat-*` / `--heat-text-*` in `globals.css`, registered as `heat` /
  `heat-text` Tailwind colours. **No per-cell hex.**
- Unchanged: hover-exact-figures readout (`data-testid="availability-hover-readout"`), the snapshot ring,
  descending month bands, the two-up responsive grid, honest empty/partial rendering, and
  click/shift-click prefilling the **job form** Start/End (never the global as-of — J-18).

### J-76 — `/stocks/[ticker]` price chart: per-bar hover detail box
- Hovering any bar shows a `data-testid="price-chart-hover"` box with:
  - **date** (`data-testid="price-chart-hover-date"`) rendered `yyyy-MM-dd` via the shared formatter (J-42)
  - **Open / High / Low / Close**, **Volume**, **% chg** (green/red; "NA" at the first bar)
  - **each rendered moving-average value** (one row per plotted MA, dot colour matching the chart line;
    "NA" where the MA is absent at the warm-up edge)
- A **post-as-of (forward) bar** carries an "after as-of (display only)" badge
  (`data-testid="price-chart-hover-forward"`, J-20) — visualization-only, never a signal.
- The box is `pointer-events-none`, pinned top-left, and disappears when the cursor leaves the chart.

## States Handled
- **Heatmap:** loading (spinner), error (no fabricated cells), empty DB (EmptyState), partial-coverage
  day (distinct lower-bucket hue), full-coverage day (top bucket) — all preserved from J-61/J-70.
- **Hover box:** no-hover (box absent), first-bar % change (NA), warm-up-edge MA (NA), forward bar
  (labelled), off-chart (box clears).

## Interactive states
- Heatmap cells keep `hover:brightness-110 hover:ring-1 hover:ring-accent` and
  `focus-visible:ring-2 focus-visible:ring-accent`; selection/anchor/snapshot rings unchanged.
- The hover box itself is non-interactive (pointer-events-none) by design so it never intercepts the
  crosshair or obscures the as-of marker (J-20) / regime bands (J-45).

## Design-system conformance
- All new colour/contrast come from registered Tailwind tokens (`heat-*`, `heat-text-*`) backed by
  `globals.css` CSS vars — no arbitrary hex, no arbitrary spacing/typography. The hover box reuses the
  same `border-border-strong` / `bg-surface-2/95` / `backdrop-blur-sm` glass treatment as the existing
  `index-regime-chart` tooltip, so the two charts read consistently.

## Gate
`cd apps/frontend && npx tsc --noEmit` → **EXIT 0**. `npm run build` → **EXIT 0** (heat utility classes
present in the generated CSS). Prod `.next` cleared afterward for clean browser-QA dev startup.
