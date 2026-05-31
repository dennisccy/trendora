# Phase goal-i_can_see_the_wealthy_future-iter-8 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future-iter-8
**Date:** 2026-05-31
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| (all pages) | `AsOfSwitcher` (top-bar `Select`, `components/asof-switcher.tsx`) | New component | J-13: global control to pick a past trading day | Open the top-bar date drop-down; confirm it lists "Latest" plus the stored run dates from `/api/runs`; select a past date (e.g. `2022-10-07`) and confirm the page re-fetches that date |
| (all pages) | `AsOfSwitcher` indicator `Badge` (`data-testid="asof-indicator"`) | New component | J-13: clear historical labelling | Select a past date → confirm an amber "Viewing as-of {date} (historical)" badge appears; reset to Latest → confirm a quiet "Latest" badge shows instead |
| (all pages) | `AsOfProvider` context (`components/asof-provider.tsx`), mounted in `app/layout.tsx` | New component | J-13: hold selected date across navigation | Pick `2022-10-07` on `/`, then click the sidebar to `/stocks`, `/themes`, `/sectors` → confirm each still shows `2022-10-07` without re-selecting |
| `/` (Dashboard) | `app/page.tsx` data fetch + "Data as-of {date}" label | Changed behavior | J-15/J-13: serves stored snapshot; passes `as_of` | Load `/`; confirm regime/breadth/candidate panels render and the "Data as-of" label equals the switcher date; select a past date → confirm panels reflect that date's Scanner Run |
| `/stocks` | `app/stocks/page.tsx` leaderboard + "as of {date}" label | Changed behavior | J-15/J-13: stored rows; passes `as_of` | Load `/stocks` at latest → confirm rows render fast (< ~1.5 s) and "as of" label = latest; select a past date → confirm rows + label switch to that date; confirm leaderboard filters still work |
| `/stocks/[ticker]` | `app/stocks/[ticker]/page.tsx` detail + "as of {date}" label | Changed behavior | J-15 (J-06 coherence); passes `as_of` | Open NVDA detail at latest → confirm Leadership/Entry/Risk match NVDA's row on `/stocks` exactly; select a past date → confirm detail reflects that date |
| `/stocks/[ticker]` | `StockChartPanel` (price/MA chart, "{n} bars · as of {date}") | Changed behavior | J-15/J-13: as-of chart, no-lookahead | Open NVDA detail at a past date → confirm the chart shows only bars up to/including that date and the bar count/"as of" label reflect the historical slice |
| `/themes` | `app/themes/page.tsx` theme table + "as of {date}" label | Changed behavior | J-15/J-13: stored `ThemeScoreRow`; passes `as_of` | Load `/themes`; select a past date → confirm theme scores + "as of" label reflect that date's run |
| `/sectors` | `app/sectors/page.tsx` sector table + "as of {date}" label | Changed behavior | J-15/J-13: stored `SectorScoreRow`; passes `as_of` | Load `/sectors`; select a past date → confirm sector scores + "as of" label reflect that date's run |
| (all pages) | `lib/api.ts` fetchers (`fetchDashboard`/`fetchStocks`/`fetchStock`/`fetchStockBars`/`fetchSectors`/`fetchThemes`) | Changed behavior | Accept optional `asof` → append `?as_of=` | Select a past date and inspect the network calls → confirm each request carries `?as_of={date}`; reset to Latest → confirm no `as_of` param is sent |

---

## Backend-Only Changes (No UI Impact)

- `app/engine/scanner.py` (`resolve_as_of_date`, `resolve_run`, `AsOfError`, `_latest_stored_run_date`) — as-of resolution + create-once snapshot logic — no direct UI surface; consumed by the re-pointed endpoints.
- `app/engine/snapshot_serving.py` (new) — reshapes a stored snapshot into the existing payloads and maps `AsOfError` → HTTP (422/400/503) — no direct UI surface; the error mapping only surfaces as the existing per-page "Backend unavailable"/error states for a bad/missing date.
- `app/api/watchlist.py` — now reads current values from the latest stored snapshot row instead of live `score_stocks` — user-invisible (the Watchlist page output is unchanged).
- Backend tests (`tests/test_asof_resolver.py` new, `tests/test_api_engine.py`, `tests/test_bars.py`) — resolver/immutability/no-lookahead/coherence/error-case coverage — no UI impact.
- The **create-once-on-first-view** path for an arbitrary uncomputed seed date works but has no UI entry point (no free-form calendar) — backend capability without UI wiring this iteration.

---

## Summary

- **Frontend surfaces changed:** 10 (1 global switcher + 1 indicator + 1 provider + 5 as-of-aware pages incl. chart + the shared `lib/api.ts` fetchers)
- **New pages/routes:** 0
- **Modified components:** 5 pages (Dashboard, Stocks list, Stock detail + chart, Themes, Sectors) + `layout.tsx`; 3 new components (`AsOfSwitcher`, `AsOfProvider`, indicator badge usage)
- **Navigation changes:** no (additive top-bar control only — no sidebar/route change)
- **Backend-only changes:** 4 (resolver, snapshot-serving layer, watchlist re-point, create-once path) + tests
