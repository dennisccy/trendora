# goal-mcp-loop-iter-20 Frontend Handoff

**Phase:** goal-mcp-loop-iter-20
**Date:** 2026-07-07
**Agent:** developer
**Status:** complete

## What Was Built

Two frontend changes on `/data` (the Data Manager page), both presentation-only — no new displayed
value, no new endpoint, no new user-facing capability beyond clarity:

1. **Removed the "Expand universe" job kind** from the picker, and every now-dead supporting bit of
   code that only existed to serve it:
   - `isExpandKind` / `sourceIneligibleForExpand` derived state (page-level).
   - The `handleStart` guard that blocked submission for a market-cap-ineligible source.
   - `JobForm`'s `isExpandKind`/`sourceIneligibleForExpand` props, their types, and the `disabled`
     expression's dependency on them.
   - The `<option value="expand">Expand universe</option>` itself.
   - The per-source "cannot supply market cap — not selectable for expand" disabled-option suffix.
   - The amber "cannot supply market cap" alert box.
   - The Expand sentence in the job-kind explainer paragraph, and "expand" in the panel title/hint.
   - `JobProgressPanel`'s `isExpand` flag, its disjunct in `showFetch`, and the
     `{isExpand ? <ExpandScreenResult/> : null}` render.
   - The entire `ExpandScreenResult` component (passers/omitted-candidates job-card block).
   - Fetch / Backfill / Fetch+backfill, the gap-pull ("Pull missing data"), and Rebuild controls are
     completely untouched and still work exactly as before.
2. **Re-encoded the per-date availability heatmap's legend** so the two things it shows — how much
   price data exists for a day (the cell's fill colour) vs. whether that day has been scored into an
   immutable snapshot (a ring around the cell) — can never be mistaken for one another:
   - The single legend row became **two labeled groups**: "Price data — cell fill" and "Scored
     snapshot — indicator", each with its own `data-testid` for QA.
   - The density fill went from a 6-hue rainbow (slate→blue→cyan→teal-green→green→**amber**) to a
     **single blue hue at 6 lightness steps** — the amber "full" bucket previously read like a warning
     (amber is this page's warning colour elsewhere) and was easy to confuse with the green bucket next
     to it. All 6 steps are still clearly distinguishable from each other (validated, not eyeballed —
     see the dev handoff's Design Rationale section for the exact method and numbers).
   - The snapshot ring moved from green (which blended into the old ramp's green bucket) to a dedicated
     violet colour that doesn't share a hue family with any density bucket or any other status colour on
     the page.
   - The header text, the caption under the grid, and every cell's hover tooltip now say in plain words
     that "Fetch fills price data" and "Backfill produces scored snapshots" — so a user hovering a day
     that has bars but no snapshot sees exactly that explained, not just raw numbers.

## User-visible before/after

- **Before:** the job-kind dropdown offered Backfill / Fetch / Fetch+backfill / **Expand universe**. The
  heatmap had one "Coverage" legend row with 6 colour swatches ending in amber for "full", plus a small
  green-ringed swatch labeled "snapshot".
- **After:** the dropdown offers Backfill / Fetch / Fetch+backfill (Expand is gone). The heatmap shows
  two clearly separate legend groups — one for the 6 blue shades (no more amber), one for the violet
  ring — each with its own heading, and the surrounding text spells out which job (Fetch vs. Backfill)
  produces which signal.
- No numbers changed. The same "X of Y symbols have a bar" / "snapshot yes or no" data is shown — only
  the colours, grouping, and wording changed for clarity. Keeping the underlying data fresh (via the
  ordinary Fetch button) now covers the whole ~548-name committed pool instead of a smaller ~162-name
  set, but that is an internal change to what Fetch fetches — nothing new is displayed because of it.

## Files Changed

- `apps/frontend/app/data/page.tsx` — Expand removal (see What Was Built #1 for the full site list).
- `apps/frontend/components/availability-heatmap.tsx` — two-group legend, new ring/text colour classes,
  updated tooltip/caption/header copy, updated internal comments (including fixing one comment left over
  from a prior iteration that still described the old multi-colour ramp).
- `apps/frontend/app/globals.css` — the 6 density-bucket colours (`--heat-0`..`--heat-5`) replaced with a
  single-hue blue ramp; one new colour variable (`--snapshot`) added for the ring.
- `apps/frontend/tailwind.config.ts` — the new `--snapshot` variable registered as a usable utility class
  (`ring-snapshot`, `text-snapshot`), following the exact same pattern as the existing `pos`/`neg`/`warn`
  colours.

## Design System Compliance

- Component library: reused the existing `Card`/`Select` components on `/data`; no new component type
  introduced, no raw HTML where a project component exists.
- Colour tokens: every colour used is a CSS variable defined once in `globals.css` and registered in
  `tailwind.config.ts` — no inline hex anywhere in the changed components (matches the project's stated
  "the ONLY place raw hex values live" convention).
- The color choices were computed and checked by hand (lightness monotonicity, minimum perceptual gap
  between neighbouring steps, contrast against the card surface, hue separation from every other status
  colour on the page) via an ad hoc OKLCH + WCAG calculation done inline — not chosen by eye, and NOT
  produced by any committed palette tool (there is none in this repo). Full numbers are in the dev
  handoff's Design Rationale section.
- No new loading/empty/error state was needed — the heatmap's existing loading/error/empty states are
  unchanged and were not touched by this edit.
- Responsive layout unchanged (same breakpoints, same card position, same page structure).

## Tests Run

- `cd apps/frontend && npx tsc --noEmit` — **0 errors.** This is the primary correctness gate for this
  iteration's frontend work (the project has no component/DOM test framework installed, and this
  presentation-only iteration intentionally does not add one, per the plan). Confirms every removed
  prop/flag/component has zero dangling references anywhere in the codebase.
- DOM/visual verification (two-group legend renders, the top density bucket is not the old amber, the
  snapshot ring is not green, hovering a bars-but-no-snapshot day vs. a snapshotted day is visibly and
  textually distinguishable) is the browser-qa-agent lane's job per the plan — not run by me as the
  developer. The `data-testid`s I added (`availability-legend-density`, `availability-legend-snapshot`)
  are there specifically to make that DOM verification unambiguous.

## Known Issues

- **A separate scoped backend pytest re-run and a `scripts/dev.sh` startup check could not be completed
  this session** due to an unrelated environment failure (the Bash tool became non-functional partway
  through my final verification pass — a host/user-wide disk-quota exhaustion, confirmed via a second,
  independent subagent hitting the identical failure). This does not affect anything reported here
  (`tsc --noEmit` ran to completion successfully before the failure occurred, and this handoff covers
  frontend-only work) but it does mean I could not do a final live-browser click-through myself before
  handing off. Full detail and the exact re-run command are in the dev handoff's Known Issues section.
