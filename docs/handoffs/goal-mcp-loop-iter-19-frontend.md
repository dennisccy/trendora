# goal-mcp-loop-iter-19 Frontend Handoff

**Phase:** goal-mcp-loop-iter-19
**Date:** 2026-07-07
**Agent:** developer
**Status:** complete

## What Was Built

- **The J-01 crash fix (`apps/frontend/app/stocks/page.tsx`).** The exact regression: clicking the
  "Sector" leaderboard column called `a.sector.localeCompare(b.sector)` — on the broadened 548-name
  pool ~78% of rows have `sector === null` (unmapped in `config.stock_sectors`), so this threw an
  uncaught `TypeError` the instant a user sorted by Sector, and with no error boundary in place the
  whole page (nav included) collapsed to a blank "Application error" screen. Fixed at the root: the
  comparator now calls the new null-safe `compareSectors(a.sector, b.sector)` helper.
- **The honest "Unassigned" bucket (`apps/frontend/lib/sector-label.ts`, new).** A stock with no mapped
  GICS sector is never shown as blank or a literal `null` — it reads `"Unassigned"` everywhere: the
  Sector filter dropdown (alphabetically between "Technology" and "Utilities"), the leaderboard's
  Sector column, the Stock Detail page's sector chip, and the Scanner-Run detail table's Sector column.
  Selecting "Unassigned" in the filter narrows the leaderboard to exactly the null-sector rows (verified
  live: 422/541 rows — byte-exact match with a direct `/api/stocks` count).
- **The widened contract type (`apps/frontend/lib/api.ts`).** `StockRow.sector: string` →
  `string | null` — the type now matches what the backend has always honestly served; `tsc --noEmit`
  against the whole project (0 errors) is the evidence every consumer was found and fixed.
- **Crash containment — `apps/frontend/app/error.tsx` (new).** A route-level Next.js error boundary:
  any future uncaught client exception anywhere in `app/` now degrades to a contained card
  ("Something went wrong on this page" + "Try again") rendered INSIDE the root layout, so the sidebar
  nav and header keep working. Live-verified (not just inspected): monkey-patched
  `Array.prototype.sort` to throw, clicked a sort header, confirmed via screenshot that the card
  rendered with the full nav still visible and clickable.
- **`apps/frontend/app/global-error.tsx` (new).** The root-layout error boundary (only fires if the
  root layout itself, or `error.tsx`, throws) — Next.js requires it to render its own `<html>`/`<body>`
  since it replaces the root layout; it deliberately imports no app components/providers so this
  last-resort fallback cannot itself fail the way the layout it substitutes for might.

## Files Changed

- `apps/frontend/lib/sector-label.ts` — new. `UNASSIGNED_SECTOR`, `sectorLabel(sector)`,
  `compareSectors(a, b)` — the one shared null → "Unassigned" mapping.
- `apps/frontend/lib/sector-label.test.ts` — new. Unit tests (node:assert convention; see the dev
  handoff's Tests Run for the execution note).
- `apps/frontend/lib/api.ts` — `StockRow.sector: string` → `string | null`, with a comment pointing
  consumers at `sector-label.ts`.
- `apps/frontend/app/stocks/page.tsx` — `SORT_COMPARATORS.sector` uses `compareSectors`; the `sectors`
  filter-vocabulary memo and the `visible` filter predicate use `sectorLabel`; the leaderboard Sector
  cell renders `sectorLabel(row.sector)`.
- `apps/frontend/app/stocks/[ticker]/page.tsx` — the sector chip renders `sectorLabel(row.sector)`.
- `apps/frontend/app/scanner-runs/[runId]/page.tsx` — the Sector table cell renders
  `sectorLabel(row.sector)`.
- `apps/frontend/app/error.tsx` — new.
- `apps/frontend/app/global-error.tsx` — new.

## Design system conformance

- No new component library usage was needed for the sector fix (plain text cells / native `<select>`
  `<option>`s, matching the existing leaderboard markup exactly — no new UI surface).
- `error.tsx` reuses the EXISTING `Card` component and the established inline-error visual language
  already used on this same page (`stocks/page.tsx`'s "Backend unavailable" card: `border-neg
  bg-surface`, `AlertTriangle`, `text-neg`/`text-text-muted` tokens) — no new colors, no arbitrary
  values. The "Try again" button matches the existing primary-action button convention from
  `app/data/page.tsx` (`inline-flex h-9... rounded-md border...` — adapted to a smaller `h-8` size
  appropriate for a secondary in-card action) with hover/focus-visible/active states.
- `global-error.tsx` deliberately does NOT use the `Card` component or any app component — see the dev
  handoff's rationale (it must not depend on the very layout/provider tree it substitutes for). It
  still uses the SAME design tokens (`bg-bg`, `border-neg`, `bg-surface`, `text-neg`, `text-text-muted`,
  `bg-surface-2`, `border-border`) directly as Tailwind utility classes, so it reads as Trendora, not a
  generic crash page, even in this maximally-defensive special case.
- Both new pages/components are dark-theme only (matching `app/layout.tsx`'s fixed `className="dark"` —
  this app has no light-mode toggle to support).

## Tests Run

See the dev handoff (`docs/handoffs/goal-mcp-loop-iter-19-dev.md`) for the full test log. Summary:
`tsc --noEmit` 0 errors (whole project); `lib/sector-label.test.ts` 8/8 assertions pass (verified via a
`tsc`-compiled-to-JS workaround — this sandbox's Node lacks native TS execution, a pre-existing gap
affecting all `.test.ts` files in this repo, not introduced here). Live-browser-verified: Sector sort
(no crash, nav intact), Sector filter "Unassigned" option (422/541 rows, byte-exact vs. API), stock
detail sector chip, scanner-run detail sector column (both via `sectorLabel`, non-null case unaffected —
e.g. NVDA still reads "Technology"), and the forced-exception `error.tsx` containment.

## Known Issues

- The plan's non-blocking F1 carry-over item (whether the Full-history chart plots pre-2018 weekly bars
  for a >8y name) was checked opportunistically while live-verifying NVDA's detail page: it already
  works correctly (3,025 bars back to 1999-01-22, "older bars weekly-sampled" disclosed) — no fix was
  needed. Noting this so it isn't mistaken for an unverified item.
- No new frontend test-runner infrastructure was added (out of scope) even though the existing
  `.test.ts` convention doesn't currently execute in this sandbox — see the dev handoff's Known Issues
  for the full note and a suggested remediation (pin a Node build with `--experimental-strip-types`, or
  add `tsx`/`ts-node` + a `package.json` script).
