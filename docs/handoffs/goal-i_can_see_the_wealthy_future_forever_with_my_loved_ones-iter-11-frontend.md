# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11
**Date:** 2026-06-13
**Agent:** developer
**Status:** complete

## What Was Built

`/sectors` expanded-row panel now mirrors the `/themes` member pattern (J-57) verbatim — re-used, not
re-invented — so the two leaderboards stay consistent and the coherence surface stays clean.

- **Type extension (`lib/api.ts`)**: `SectorRow` gained `description: string | null` and
  `members: string[]`, served verbatim by `GET /api/sectors`.
- **Description line**: each expanded ETF row shows `TICKER — Name` (bold) and, when present, a config
  description paragraph below it. A sector ETF (or a stored run predating the column) has no description
  and renders without the line — no crash.
- **Expandable universe-member list**: the first `MEMBER_PREVIEW_LIMIT = 6` members render inline as
  ticker chips; a `+n` button (`data-testid="sector-members-toggle"`) reveals every remaining member in
  place, toggling to "Show fewer". Each chip is a `next/link` that opens the dated stock detail in a
  **new tab** — `href={asofHref('/stocks/<TICKER>')}` (carries `?asof` while historical via the shared
  `useAsOfHref` helper, clean at latest), `target="_blank"`, `rel="noopener noreferrer"`,
  `data-testid="sector-member-link"`.
- **Empty state**: an ETF with zero members renders an explicit honest line
  (`data-testid="sector-members-empty"`): "No universe members are mapped to this ETF (config-defined)."
  — never fabricated members.
- **Industry honesty label**: the member header for industry ETFs reads "Members (config-defined)" so
  the source of the mapping is transparent.

## iter-5 nested-interactive hazard — handled

The member links and the `+n` toggle live in the **separate, non-clickable expanded `<tr>`** (NOT inside
the `role="button"` summary row). Each chip and the toggle call `e.stopPropagation()` so a member/toggle
click can never bubble up and toggle the summary row. This is the exact arrangement `/themes` uses.

## Files Changed

- `apps/frontend/lib/api.ts` — `SectorRow` gains `description: string | null` + `members: string[]`.
- `apps/frontend/app/sectors/page.tsx` — import `next/link` + `useAsOfHref`; pass `asofHref` into
  `SectorRows`; add `MEMBER_PREVIEW_LIMIT`; render the description line + expandable member list / empty
  state in the expanded `<tr>` (port of the `/themes` `ThemeRows` member block).

## Design System Conformance

- Re-used existing primitives only: `Card`, `table`, `Badge`, `ScoreBadge`, `ComponentBreakdown`,
  `EmptyState` (page-level), `next/link` chips. No new component invented.
- Member chips + `+n` use the same classes as `/themes` (`border-border bg-surface ... text-accent
  hover:border-accent`, focus-visible ring; the `+n` is a dashed-border `<button>`). No ad-hoc effects.
- Every interactive element has hover + focus-visible states (inherited from the ported classes).
- Loading skeleton, backend-error card, and zero-ranked-rows empty state are pre-existing and unchanged;
  the NEW per-ETF zero-member empty state is added.

## How To Verify (operator, ~2 min)

1. Open `/sectors`. Confirm an industry row that previously read just "KRE" now reads a name like
   "Regional Banks (SPDR)" in its expanded panel header.
2. Expand a sector ETF row (e.g. **XLK**) — see its `stock_sectors` members listed as chips, with a
   `+n` button if more than 6. Click a chip — it opens that stock's detail in a new tab.
3. Expand an industry ETF row with members (e.g. **SMH**) — see its description line and its
   `stock_industries` members (NVDA, AMD, ...), labelled "Members (config-defined)".
4. Expand **KRE** — see the explicit "No universe members are mapped to this ETF (config-defined)."
   empty state and **zero** member chips.
5. Switch to a historical as-of date (via the global as-of control) and confirm a member chip's `href`
   now carries `?asof=<date>` (and is clean at latest). The chip still opens in a new tab.

## Verification Run

- `npx tsc --noEmit` → exit 0 (clean). No type errors from the new fields or the ported member block.
- Lint: `next lint`/eslint is not configured in this repo (no `eslint.config.js`); the changes are a
  verbatim style port of the passing `/themes` page.
