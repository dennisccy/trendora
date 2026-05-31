# goal-i_can_see_the_wealthy_future-iter-8 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-8
**Date:** 2026-05-31
**Agent:** developer
**Status:** complete

## What Was Built

- **Global as-of date switcher (top bar)** — a new `AsOfSwitcher` mounted in the app-shell `<header>`
  (next to the health badge). It offers "Latest" plus every stored Scanner-Run date (from the canonical
  `GET /api/runs`) and lets the user time-travel the whole dashboard. No new page or sidebar entry.
- **"Viewing as-of D (historical)" indicator** — an amber (`--warn`) `Badge` shown whenever a past date
  is selected; a quiet "Latest" badge otherwise. Clearly distinguishes a historical view from today's.
- **Global as-of state (`AsOfProvider`)** — a client React context mounted in `app/layout.tsx`, wrapping
  all pages. It loads the run dates once, holds the selected date, and exposes
  `{ asOf, setAsOf, latest, dates, isHistorical, ready }`. Because it lives in the shell it SURVIVES
  client-side navigation, so a date chosen on `/` persists onto `/stocks`, `/themes`, `/sectors`, and a
  stock's detail page without rewriting any link.
- **As-of-aware pages** — Dashboard (`/`), Stocks (`/stocks`), Themes (`/themes`), Sectors (`/sectors`),
  and Stock Detail (`/stocks/[ticker]`, incl. its price chart) now read `asOf` from the hook, pass it to
  their fetchers, and re-fetch on a date change. Switching back to "Latest" restores the current view.

## Files Changed

- `apps/frontend/components/asof-provider.tsx` — NEW. Client context for the global as-of date; loads
  `fetchRuns()` dates; default = latest; degrades to latest-only if `/api/runs` is unavailable.
- `apps/frontend/components/asof-switcher.tsx` — NEW. Top-bar `Select` of run dates + reset-to-latest +
  the "(historical)" / "Latest" indicator badge (reuses `Badge variant="warn"` and `Select`).
- `apps/frontend/app/layout.tsx` — wrap the shell in `<AsOfProvider>`; mount `<AsOfSwitcher/>` in the
  existing sticky `<header>` beside `<HealthBadge/>`.
- `apps/frontend/lib/api.ts` — add optional `asof?: string` (first arg) to `fetchDashboard`,
  `fetchSectors`, `fetchStocks`, `fetchStock`, `fetchStockBars`, `fetchThemes`; new `withAsOf` helper
  appends `?as_of=` only when a date is selected. No score/bucket/return is ever computed client-side.
- `apps/frontend/app/page.tsx` — Dashboard reads `asOf`; all three fetches (dashboard/sectors/themes)
  use the same as-of date; `useEffect` deps `[asOf]`.
- `apps/frontend/app/stocks/page.tsx` — Stocks list reads `asOf`; deps `[asOf]`.
- `apps/frontend/app/sectors/page.tsx` — Sectors reads `asOf`; deps `[asOf]`.
- `apps/frontend/app/themes/page.tsx` — Themes reads `asOf`; deps `[asOf]`.
- `apps/frontend/app/stocks/[ticker]/page.tsx` — Stock Detail + its `StockChartPanel` read `asOf`; deps
  `[ticker, asOf]` (the as-of chart returns only bars ≤ D).

## Design-System Compliance

- Reuses existing components only: `Select` (`components/ui/select`) for the picker, `Badge`
  (`variant="warn"`) for the historical indicator. No raw control markup, no new colours/effects.
- The historical state uses the `--warn` (#fbbf24) amber token; the latest state is visually quiet.
- Dates are monospace/tabular (`.num`). The switcher disables while dates load and when none are
  available (graceful, no crash). Each page keeps its existing loading / empty / "Backend unavailable"
  treatments and re-fetches on a date change.

## Tests Run

Command: `cd apps/frontend && NEXT_PUBLIC_API_URL=http://localhost:8835 npm run build`
Result: **build succeeded** — all 10 routes compiled + typechecked (0 errors). The 5 as-of-aware pages
remain static-prerenderable; `/stocks/[ticker]` and `/scanner-runs/[runId]` stay dynamic as before.

## Known Issues

- The selected as-of date is live client state (survives in-app navigation) but is NOT a bookmarkable
  URL parameter, so a full browser reload returns to "Latest". This is a deliberate choice to keep the
  build free of a `useSearchParams` Suspense boundary; the switcher is a live control. In-app navigation
  (sidebar links, leaderboard→detail row links) preserves the date — which is what J-13 step 3 requires.
- The switcher only offers dates that have a stored immutable snapshot (the run-history dates), which
  always resolve instantly and reproducibly. There is no free-form calendar (out of scope this iter).
