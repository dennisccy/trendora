# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-16 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-16
**Date:** 2026-06-14
**Agent:** developer
**Status:** complete

## What Was Built (UI changes)

Two pure-presentation upgrades to existing, already-passing surfaces. No new page, no new route, no nav change, no new information displayed. Both are pure frontend on the committed seed.

### `/data` — Per-date availability heatmap (J-70)
- **Readable day numbers on every cell.** Per-bucket text token via a new `BUCKET_TEXT_CLASS` map (design tokens only): `text-text` (near-white `#e6edf3`) on the faint buckets 0–3 (dark / low-opacity-accent backgrounds), `text-bg` (dark) on the bright teal buckets 4–5. Previously the low buckets used `text-text-muted` (`#8b98a9`) which read dark-on-dark on buckets 0–1. Added `font-medium`.
- **Newest months first.** Month bands now render in descending order (top→bottom); each month's internal day order stays ascending (left→right, top→bottom).
- **Two months per row.** Container is now a responsive `grid grid-cols-1 md:grid-cols-2` (two-up on a normal viewport, one column on narrow screens) — more history visible without excessive scroll. `max-h-[28rem] overflow-auto` preserved.
- Unchanged: density buckets, legend, snapshot ring, hover readout, click/shift-click prefill into the job form (never touches the global as-of — J-18), and all `data-testid`/`data-*` attributes (`availability-cell`, `data-bucket`, `data-date`, `data-symbols`, `data-total`, `data-snapshot`, `availability-month`/`data-month`).

### Cross-cutting as-of calendar popover (J-71)
- ArrowLeft / ArrowRight on the open popover now scrub the **single global as-of** one **available snapshot date** at a time (older / newer), live, via the existing `onSelect`→`setAsOf`.
- Bounded at the ends (oldest: ArrowLeft no-op; newest: ArrowRight rests at "Latest" = `onSelect(null)`). Popover stays OPEN while scrubbing (only Escape / outside-click / Enter-on-day close it). The viewed-month cursor follows the landing date. `e.preventDefault()` stops page scroll.
- No global `window`/`document` listener (handled on the dialog's existing `onKeyDown`; dialog focused on open via `data-autofocus`). No second/page-local date state — `asof-provider.tsx` stays the sole owner of the as-of value and its `?asof` serialization.

## Design System Compliance
- **Tokens only, no hardcoded hex/arbitrary values:** `text-text`, `text-bg`, `font-medium`, `bg-accent/*` (pre-existing), `grid-cols-1`, `md:grid-cols-2`, `gap-x-5`/`gap-y-5` — all from the configured Tailwind token set in `tailwind.config.ts` / `globals.css`.
- **Responsive:** `md:` breakpoint used for the two-up→one-column collapse (matches the codebase's existing responsive grid utilities).
- **Interactive states preserved:** heatmap cells keep hover/focus-visible/selected rings; calendar day buttons keep their hover/focus-visible/selected states. No interactive element lost a state.
- **Visual continuity:** both surfaces match the established dark analytical workstation style; no new effects introduced.

## Files Changed
- `apps/frontend/components/availability-heatmap.tsx`
- `apps/frontend/components/asof-calendar.tsx`

## Typecheck
Command: `cd apps/frontend && npx tsc --noEmit`
Result: PASS (EXIT=0).

## Browser QA Pointers (for the browser-qa-agent)
- **J-70 on `/data`:** open the heatmap; read a low/empty cell's (`data-bucket="0"`/`"1"`) day number — must be legible, not dark-on-dark (capture full-viewport, not a close-up). First rendered `availability-month` `data-month` must be the most recent month (descending). At a normal width two month bands sit side-by-side per row; collapse to one column at a narrow width. Confirm a cell click still prefills the job form Start/End and does NOT change `asof-indicator` / `?asof`.
- **J-71 on the as-of popover:** open the top-bar `asof-trigger`; press ArrowRight then ArrowLeft — `asof-indicator` and the `?asof` URL param step to the next/previous available snapshot date (not an arbitrary ±1 day); popover stays open; `asof-cal-month` follows. Bounded: oldest ArrowLeft no-op; newest ArrowRight rests at Latest (clean URL, "Latest" indicator). Escape still closes; a day click still selects+closes (J-62). Exactly one date control (J-18).
- **Evidence hygiene:** `md5sum` the evidence dir; re-capture any blank/byte-identical close-up as a full-viewport screenshot; prefer DOM-text/attribute extraction (`data-bucket`, `asof-indicator`, `asof-cal-month`, URL `?asof`).

## Known Issues
- None.
