# goal-market-compass-iter-1 Frontend Handoff

**Phase:** goal-market-compass-iter-1
**Date:** 2026-08-20
**Agent:** developer
**Status:** complete

## What Was Built

A single new disclosure subsection on the existing `/methodology` page's Universe Selection card —
no new page, route, nav entry, or user-facing control.

- `apps/frontend/lib/api.ts`: the `UniverseSelection` TypeScript interface gained one new required
  field, `sector_basis: string`, documented alongside the existing `membership_rule` /
  `per_date_rule` fields it's served next to on the SAME `GET /api/methodology` payload.
- `apps/frontend/app/methodology/page.tsx`: `UniverseSelectionCard` renders a new bordered
  subsection ("Stock sector labels" / "Data basis" badge) directly below the existing "Per-date
  membership rule" subsection, showing `selection.sector_basis` verbatim as plain prose — the exact
  same `<div className="space-y-1.5 border-t border-border pt-3">` pattern the adjacent, already-
  shipped subsection uses. No new component, no new styling primitive, no new visual effect.
- `/stocks` (leaderboard Sector column, Sector filter, stock detail header): **zero code change.**
  Confirmed by direct inspection that these surfaces already read `row.sector` /
  `sectorLabel(row.sector)` as-is with a null-safe "Unassigned" fallback (`lib/sector-label.ts`).
  They will simply show far fewer "Unassigned" rows once a fresh backfill runs under the new
  backend mapping — no frontend deploy beyond this iteration's `/methodology` change is needed for
  that improvement to appear.

## Files Changed

- `apps/frontend/lib/api.ts` -- `UniverseSelection` interface: added `sector_basis: string`.
- `apps/frontend/app/methodology/page.tsx` -- `UniverseSelectionCard`: added the new subsection
  (13 lines total, including the updated doc comment).

## Tests Run

No new frontend logic/threshold computation was introduced (the new field is rendered verbatim,
with zero client-side comparison or derivation), so no new `apps/frontend/lib/*.test.ts` node
script was needed, consistent with this project's "frontend logic tests are plain node scripts"
constraint applying only to actual computed logic.

Command: `cd apps/frontend && node_modules/.bin/tsc --noEmit`
Result: exit code 0, zero type errors, zero warnings.

Live verification against the running dev server (`scripts/dev.sh`):
- `/methodology` returns HTTP 200 with no "Application error" text in the rendered output.
- The new subsection's specific markup could **not** be visually confirmed live, because
  `GET /api/methodology`'s `universe_selection` block (the whole card, not just the new
  subsection) is gated off in this environment by a pre-existing, out-of-scope condition — see the
  dev handoff's "Known Issues" #1 for the full explanation (the committed offline screen record
  `data/seed/universe.json` does not exist in this repo). The new JSX was instead verified via (a)
  a clean `tsc --noEmit` pass against the `UniverseSelection` interface it consumes, and (b) it is
  a close structural copy of the immediately-adjacent, already-shipped, already-working "Per-date
  membership rule" subsection in the same component.

## Known Issues

> **SUPERSEDED BY THE AUDIT (2026-08-20) — see finding B1 in
> `docs/handoffs/goal-market-compass-iter-1-audit.md`.** The disclosure is no longer invisible. The
> audit moved `sector_basis` out of the gated `universe_selection` block into a sibling top-level
> `MethodologyCatalog.sector_basis`, and moved the render out of `UniverseSelectionCard` into its own
> always-shown `SectorBasisCard`. Verified live in Chrome at 1440x900:
> `[data-testid="universe-sector-basis"]` present and visible (h=144px at y=318), full prose rendered,
> while `[data-testid="universe-selection"]` stays correctly absent (the J-22 gate is still enforced
> for the screen claim). Evidence:
> `reports/qa/goal-market-compass-iter-1-evidence/AUDIT-01-methodology-sector-basis-visible.png`.
> The note below is retained as the historical record of the state at dev-handoff time, and remains
> accurate for the Universe Selection card itself.

Same as dev handoff item #1: the entire Universe Selection card (not just this iteration's new
subsection) is invisible on the live `/methodology` page in this environment until
`data/seed/universe.json` is built via the separate, out-of-scope "Expand" job. This is a
pre-existing condition, unrelated to and unintroduced by this iteration.
