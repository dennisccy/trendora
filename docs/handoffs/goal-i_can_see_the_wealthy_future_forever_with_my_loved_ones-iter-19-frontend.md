# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-19 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-19
**Date:** 2026-06-15
**Agent:** developer
**Status:** complete

## What Was Built (UI)

### J-73 — No as-of date-flash (synchronous URL hydration)
The single global as-of state (`components/asof-provider.tsx`) now hydrates **synchronously from the
`?asof` URL param on first mount** instead of only after the `GET /api/runs` fetch resolves. This
removes the visible latest→D flash on every historical arrival path (deep link, reload, new tab /
middle-click, in-app nav from another historical page): the destination page's first data fetch is
already keyed to D, so the user never sees the latest-date values render then swap to D.

- **No visual surface change** — J-73 is the ABSENCE of a flash. The historical badge, the dated
  values, and the `?asof` URL all look identical once settled; they are now simply correct from first
  paint. There is no new control, no new column, no new copy.
- The as-of switcher UI, the calendar popover, keyboard stepping, and all consuming pages are
  **unchanged** — only the *timing* of the one global state's first read changed.

### J-78 — Dashboard major-indexes range defaults to All
The Dashboard `/` "Major indexes & regime" card's range selector now reads **"All"** active on a fresh
load (was "6M"), and the chart spans the full available history. This required **no frontend code
change**: `components/major-indexes-card.tsx` already initializes `rangeKey = null` ("server's config
default") and reads the active preset back from the server payload (`indexes.range.key`). The change is
driven entirely by the backend config (`index_chart.default_range = "all"`). All four presets
(3M / 6M / 1Y / All) still switch the view.

## Files Changed (frontend)
- `apps/frontend/components/asof-provider.tsx` — J-73: lazy `useState` initializer (`readAsofFromUrl`)
  seeds the existing `asOf` state synchronously from `?asof` on first mount (server-safe, window-guarded);
  the run-list `ready` step is now the J-43 validate/degrade pass with a fixed `setAsOf(null)` degrade.
  No new state, no new listener; sole `?asof` owner preserved; iter-2 `searchKey` dep + `restored` guard
  untouched.
- (J-78 needed no frontend file edit — `major-indexes-card.tsx` already reads the server default.)

## How To Verify (operator / browser-qa-agent — 5 minutes)
Latest run date = `2026-06-12`; a historical date = `2026-05-28`. Frontend `:3835`, backend `:8835`.

1. **J-78 fresh dashboard**: open `http://localhost:3835/`. The "Major indexes & regime" card's range
   selector shows **All** active and the chart spans full history. Click 3M / 6M / 1Y / All — each
   re-renders the lines.
2. **J-73 deep link (no flash)**: open `http://localhost:3835/stocks?asof=2026-05-28` in a fresh tab.
   The leaderboard's first painted data must already be the 2026-05-28 snapshot — there must be **no**
   momentary latest (2026-06-12) values that then swap to D. The historical badge shows D. After
   hydration, `window.location.href` still carries `?asof=2026-05-28`.
3. **J-73 reload**: reload that URL — same result (no flash; URL keeps `?asof=2026-05-28`).
4. **J-73 in-app nav from a historical page**: from a historical page, click a leaderboard row (new tab
   per J-54) — the detail opens at the same D, no flash, href carries `?asof=2026-05-28`.
5. **J-73 latest**: open `http://localhost:3835/` (no `?asof`) — latest view, date-free URL, no flash,
   no historical badge.
6. **J-73 invalid degrade**: open `http://localhost:3835/stocks?asof=2026-13-99` — it degrades to the
   latest view, the stale param is stripped from the URL, and no wrong date is ever flashed.
7. **Regression smoke**: J-18 (exactly one date control — no page-local date picker appears), J-43
   (`?asof` serialization durable across reload), J-50 (`?asof` embedded in in-app hrefs / new tabs),
   J-13, J-44, J-49, J-42 (`yyyy-MM-dd` dates).

## Design System Compliance
No new UI was introduced (J-73 is behavioural; J-78 flips an existing selector's default value). No new
colors, spacing, typography, components, or effects — the existing shadcn/ui `Card` / `Select` and the
established dark analytical style are unchanged.

## Known Issues
- The no-flash behaviour and the post-hydration `window.location.href` assertion require an actual
  browser (Chrome DevTools `:9222`) — HTTP-200 smokes cannot catch the deep-link-vs-serializer race
  (iter-1/iter-2 `searchKey` lesson). This is the browser-qa-agent's primary gate this iteration.
