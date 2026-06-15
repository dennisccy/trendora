# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-17 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-17
**Date:** 2026-06-15
**Agent:** developer
**Status:** complete

## What Was Built

Two pure-frontend presentation upgrades of already-served payloads — **no backend change** (`git diff -- apps/backend/` is empty), no new endpoint, no new column, no recompute.

- **J-74 — Availability heatmap multi-hue legibility (`/data`).** Replaced the old single-hue
  teal-opacity ramp (where density buckets 1–3 were near-identical) with a **perceptually-ordered,
  clearly-separated multi-hue scale** across the six density buckets (0–5): slate → blue → cyan →
  teal-green → green → amber, so neighbouring buckets are unambiguously different on the dark
  background. The scale **and** the per-bucket day-number text-contrast classes are defined **once**
  from the existing design-token system (new `heat-*` / `heat-text-*` Tailwind tokens, backed by
  CSS vars in `globals.css`) — **no hardcoded hex in any individual cell**. The existing legend now
  maps each colour to its coverage level (it reuses the same bucket class map, so it updates
  automatically). Per-bucket day-number contrast is hardened (near-white on the dark slate/blue
  buckets 0–1, dark base on the bright cyan→amber buckets 2–5). All J-61/J-70 semantics preserved
  verbatim — same `GET /api/data/availability` payload, all `data-*` attributes, hover-exact-figures
  readout, snapshot ring marker, honest partial/empty rendering, descending month + two-up layout,
  and cell-click-prefills-the-job-form-NEVER-the-as-of (J-18).

- **J-76 — Stock-detail price-chart per-bar hover box (`/stocks/[ticker]`).** Added a
  crosshair-tracking detail box mirroring the existing `index-regime-chart.tsx` `subscribeCrosshairMove`
  tooltip pattern. On hover of any bar it shows: the bar's **date** (via the shared `formatIsoDate`,
  J-42), **open / high / low / close**, **volume**, the bar's **% change**, and **each rendered moving
  average value**. All values are read from the **already-served** `/api/stocks/{ticker}/bars` data
  (OHLCV + `is_forward` from `bars`, each MA from the same server `ma[period]` arrays the chart plots
  — no extra request, no recompute). The **% change** is a display derivation of the bar's close vs the
  previous bar's close (presentation math over two already-served closes, exactly like the index-chart
  tooltip — not a stored canonical value). A **forward (post-as-of) bar is labelled** "after as-of
  (display only)" (J-20) and stays visualization-only. An absent MA at the warm-up edge shows honestly
  as **"NA"**, never a fabricated number. The box is `pointer-events-none`, pinned to the top-left so it
  never obscures the as-of marker / forward divider (J-20) or the regime bands (J-45); leaving the chart
  hides it. It works for every timeframe the chart renders (it is keyed on the rendered bars).

## Files Changed

- `apps/frontend/app/globals.css` -- added the J-74 `--heat-0..--heat-5` multi-hue density tokens
  (slate→blue→cyan→teal-green→green→amber) + the `--heat-text-0..--heat-text-5` per-bucket day-number
  contrast tokens (the only place these hex values live).
- `apps/frontend/tailwind.config.ts` -- registered the `heat.{0..5}` and `heat-text.{0..5}` colour
  tokens so cells reference design tokens (`bg-heat-N` / `border-heat-N` / `text-heat-text-N`), never hex.
- `apps/frontend/components/availability-heatmap.tsx` -- `BUCKET_CLASS` now maps each bucket to its
  distinct hue token; `BUCKET_TEXT_CLASS` now maps each bucket to its contrast token; legend swatches +
  footer caption updated to describe the multi-hue scale. All `data-*` attributes / behaviours unchanged.
- `apps/frontend/components/price-chart.tsx` -- added the `HoverDetail` type, an ISO-date→bar-index
  lookup, a `buildHover` reader over the already-served arrays, a `subscribeCrosshairMove` handler (with
  unsubscribe on cleanup), and the `BarTooltip` detail-box component.

## Tests Run

Command: `cd apps/frontend && npx tsc --noEmit`  (the frontend gate — ESLint is not installed here, iter-1 lesson)
Result: **EXIT 0 — clean** (no type errors).

Command: `cd apps/frontend && npm run build`
Result: **EXIT 0 — compiled successfully**, all 14 routes built. Verified the generated CSS contains the
new utility classes (`bg-heat-0`…`bg-heat-5`, `border-heat-1`, `text-heat-text-0`, `text-heat-text-2`),
confirming Tailwind picked up the dynamic class strings from the bucket maps. The prod `.next` was then
removed so a subsequent `next dev` (browser QA) rebuilds a fresh dev cache (avoids the dead-shell trap).

Backend: **no pytest run** — backend diff is empty this iteration (per the iter spec, the full suite is
not a gate when `git diff -- apps/backend/` is empty).

## Known Issues

- **J-74 buckets 0–3 are not live-renderable from the committed seed** (every committed day has full
  coverage → only buckets 4–5 appear). Per the iter-16 lesson this is expected: their colour + day-number
  contrast must be verified at **source level** on the static `BUCKET_CLASS` / `BUCKET_TEXT_CLASS` token
  maps (a static className map's correctness is provable without a live render of every branch). Buckets
  4–5 + the legend render live and should be captured full-viewport. The mapping is: bucket 0 `bg-heat-0`
  (slate) + `text-heat-text-0` (near-white); 1 `bg-heat-1` (blue) + near-white; 2 `bg-heat-2` (cyan) +
  dark; 3 `bg-heat-3` (teal-green) + dark; 4 `bg-heat-4` (green) + dark; 5 `bg-heat-5` (amber) + dark.
- **J-76 forward-bar label requires a historical as-of** so a forward region exists. To browser-QA the
  forward label, set a historical as-of D first (so the `through=latest` chart shows post-D bars), then
  hover into the post-as-of region — the box should carry the "after as-of (display only)" badge.
- No live external integration in this iteration (no adapter/scraper/API added) — nothing to live-test.
