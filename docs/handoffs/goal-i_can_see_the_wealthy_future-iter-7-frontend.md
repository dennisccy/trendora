# goal-i_can_see_the_wealthy_future-iter-7 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-7
**Date:** 2026-05-30
**Agent:** developer
**Status:** complete

## What Was Built (UI)

The `/watchlist` page graduated from the iter-1 EmptyState stub to a working **research save-list** —
the product's first user-write surface. It is decision-support, not a portfolio: no quantity, position,
cost-basis, P&L, or order/buy/sell verb anywhere.

- **Add panel** (top `Card`): a free-text **Ticker** input (upper-cased as you type) + a free-text
  **Reason** input + an **Add** button → `POST /api/watchlist`. On success the inputs clear and the
  list re-fetches from the server (never an optimistic/fabricated row). On `404` (unknown ticker),
  `409` (already on the list), or `503` (no data) the backend's honest `detail` is shown inline as a
  styled `role="alert"` message — never a fake success.
- **Entries table** (when ≥1 entry): columns —
  - **Ticker** → links to `/stocks/[ticker]` (teal accent link).
  - **Added** → the date-added (`date_added`, sliced to the ISO date, monospace `num`).
  - **Reason** → the user's text, verbatim (2-line clamp with full text on hover).
  - **Leadership / Entry Quality / Risk** → the existing `ScoreBadge` (A–E + raw 0–100); Risk uses
    `invert` (high danger = red), identical to the `/stocks` leaderboard.
  - **Setup** → a status `Badge` (same `setupVariant` colour mapping as `/stocks`).
  - **Since added** → `price_since_added` as a signed % (monospace `num`); `text-pos` when positive,
    `text-neg` when negative, muted at `0.00%`/NA — palette tokens only.
  - **Invalidation** → `invalidation.note` rendered **verbatim** (the "$X" string is built server-side;
    the UI never assembles it).
  - **Remove** → a per-row icon button → `DELETE /api/watchlist/{id}` → list re-fetches.
- **States:** loading skeleton; "Backend unavailable" error card (no fabricated rows); EmptyState
  (`Star` icon) for zero entries; success refresh after add/remove.
- All values are server-computed and **re-displayed only** — no score, bucket, or return is computed
  client-side (single source of truth → J-06 holds on this new surface).

## Files Changed

- `apps/frontend/app/watchlist/page.tsx` — stub → client component with Add form + entries table,
  reusing `ScoreBadge`, `Badge`, `Card`, `EmptyState`, `PageHeading`. Form controls and the Add/Remove
  buttons use the established design tokens (the `Select` field tokens; `bg-accent`/`text-bg` button
  with `brightness` hover/active; `focus-visible:ring-accent`). No new component library.
- `apps/frontend/lib/api.ts` — `WatchlistEntry` (reuses `ScoreBlock`/`StockSetup`/`Invalidation`) +
  `WatchlistResponse`; a `sendJSON` POST/DELETE helper that throws the backend `detail` on non-2xx;
  `fetchWatchlist()`, `addWatchlistEntry(ticker, reason)`, `removeWatchlistEntry(id)`.

## Design System Conformance

- shadcn/ui-style components reused; no raw `<div>` soup where a `Card`/`Badge` exists. Form `<input>`
  and the Add/Remove `<button>` are styled with palette tokens (mirrors the existing `Select` wrapper
  and the system-health horizon `<button>` — the project has no dedicated Input/Button primitive).
- Palette tokens only — `--bg/--surface/--surface-2/--border/--border-strong/--accent/--pos/--neg/
  --text*`; no arbitrary hex. All numbers monospace/tabular (`num`). 4px spacing grid.
- Every interactive element has hover/focus-visible/active + disabled states; the table is
  horizontally scrollable (`overflow-x-auto`) at the mobile breakpoint, matching `/stocks`.
- Visually consistent with the existing dense-dark leaderboard pages.

## Tests Run

- `cd apps/frontend && npm run build` → **passed**; `/watchlist` compiles and typechecks (4.57 kB
  route, prerendered static). All 10 routes build clean.
- Behaviour verified end-to-end against the live backend (see dev handoff live smoke test): add ANET →
  row renders all required fields with the canonical scores; duplicate/unknown errors surface inline;
  remove clears the row.

## Known Issues

- None. `price_since_added` shows `0.00%` for a freshly added entry on the frozen seed — the correct,
  honest value (no post-add bars yet), not a UI bug.
