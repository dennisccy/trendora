# Phase goal-i_can_see_the_wealthy_future-iter-7 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future-iter-7
**Date:** 2026-05-30
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/watchlist` | `WatchlistPage` (whole page) | New page (stub → working) | Graduated from EmptyState stub to the product's first user-write surface (J-11) | Open `/watchlist` with an empty DB; confirm the Add panel renders and the Star EmptyState ("Your watchlist is empty") shows instead of a table |
| `/watchlist` | Add panel — Ticker input + Reason input + Add button | New form | User can save a stock with a free-text reason (POST `/api/watchlist`) | Type `ANET` and reason "ANET — strong leader, watching pullback", click **Add**; confirm inputs clear and a new `ANET` row appears in the table |
| `/watchlist` | Entries `table` | New table | Displays each saved stock with live canonical scores | After adding `ANET`, confirm the row shows Added date, the reason text, Leadership/Entry Quality/Risk badges (A–E + number), a Setup badge, a "Since added" %, and an Invalidation note |
| `/watchlist` | `ScoreBadge` (Leadership / Entry Quality / Risk cells) | New component usage | Reads canonical `score_stocks` row verbatim — single source (J-06) | Open `/stocks`, note ANET's Leadership/Entry/Risk score+bucket; confirm the `/watchlist` ANET row shows byte-identical values (Risk badge inverted = red for high danger) |
| `/watchlist` | "Since added" column (`price_since_added`) | New table | Shows price change since add, server-computed | After adding `ANET` on the frozen seed, confirm the cell reads `0.00%` (muted), not a fabricated non-zero figure or "NaN" |
| `/watchlist` | Invalidation cell | New table | Renders the canonical invalidation note verbatim | Confirm the ANET row's Invalidation cell shows the same "Invalid below the 50-DMA at $X" string as ANET's `/stocks/[ticker]` detail, not a UI-assembled value |
| `/watchlist` | Ticker link → `/stocks/[ticker]` | Added navigation | Cross-link to full stock detail | Click the `ANET` ticker in the watchlist row; confirm it navigates to `/stocks/ANET` |
| `/watchlist` | Per-row Remove button (Trash2) | New action | User can delete an entry (DELETE `/api/watchlist/{id}`) | Click the Remove button on the ANET row; confirm the row disappears and the table/EmptyState updates without a page reload |
| `/watchlist` | Inline error alert (`role="alert"`) | New behavior | Honest, non-fabricated failure feedback | Add `ZZZZ` (unknown) → confirm a red inline error (no row created); add `ANET` twice → confirm a "already on the watchlist" error (no duplicate row) |
| `/watchlist` | "Backend unavailable" error card | New behavior | No fabricated rows when the API is down | Stop the backend, reload `/watchlist`; confirm the "Backend unavailable" card shows and no entries are fabricated |
| `/watchlist` | Restart-persistence (whole page) | New behavior | DB-backed, survives restart (J-11 crux) | Add `ANET`, restart the backend, reload `/watchlist`; confirm the `ANET` row is still present (capture an md5-distinct screenshot vs the after-add capture) |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/models.py` — new `Watchlist(table=True)` SQLModel table (`{id, ticker, reason, created_at, asof_date_added, entry_close}`). Backing store for the UI above; not itself a UI surface. Stores no scores (single-source guarantee).
- `apps/backend/app/api/watchlist.py` — new POST/GET/DELETE router. The API behind the `/watchlist` page; reads `score_stocks` + `close_on` + `latest_data_date` and validates tickers against `config.universe.symbols`. (Its effects ARE visible via the page above, but the file is server-side.)
- `apps/backend/main.py` — registers the watchlist router (`prefix="/api"`). Wiring only.
- `apps/backend/tests/test_api_watchlist.py`, `tests/test_watchlist_persistence.py`, `tests/test_db.py` — new/updated tests (roundtrip, restart-persistence crux, single-source equality, immutability isolation, error cases). No UI surface.
- `apps/frontend/lib/api.ts` — new `WatchlistEntry`/`WatchlistResponse` types + `sendJSON` helper + `fetchWatchlist`/`addWatchlistEntry`/`removeWatchlistEntry` (the first mutating client calls). Consumed by the `/watchlist` page; not a surface on its own.

---

## Summary

- **Frontend surfaces changed:** 1 route (`/watchlist`) with ~11 distinct testable elements/behaviors
- **New pages/routes:** 0 new routes (existing `/watchlist` stub graduated to working); 0 new sidebar links
- **Modified components:** 1 page (`app/watchlist/page.tsx`) + 1 client lib (`lib/api.ts`); reuses existing `ScoreBadge`, `Badge`, `Card`, `EmptyState`, `PageHeading`
- **Navigation changes:** no (sidebar already linked Watchlist; ticker→`/stocks/[ticker]` cross-link added within the page)
- **Backend-only changes:** 6 files (1 model, 1 router, 1 main wiring, 3 test files) + the api.ts client helpers
