# Phase goal-i_can_see_the_wealthy_future-iter-1 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future-iter-1
**Date:** 2026-05-29
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| (all routes) | `Sidebar` (`components/sidebar.tsx`) | Added navigation | First app shell; full approved IA nav | Confirm all 7 links (Dashboard, Stocks, Themes, Sectors, Scanner Runs, System Health, Watchlist) are visible; click each and confirm the URL changes and the clicked link becomes highlighted (accent dot + surface background) |
| (all routes) | `HealthBadge` (`components/health-badge.tsx`) | New component | Visible proof of backend connectivity | With backend up, confirm badge turns green and reads "Backend OK" with `provider: seed`, `seed 2026-05-28`, and `158 symbols`; on page load confirm it first shows the "Checking backend…" loading state |
| (all routes) | `HealthBadge` — error state | New component (error path) | App must never fake a healthy status | Stop the backend (or block `/api/health`), reload, and confirm the badge turns red and reads "Backend unavailable" instead of "OK" |
| `/` | Dashboard page (`app/page.tsx`) → `EmptyState` | New page | Dashboard shell before scoring lands | Navigate to `/`; confirm a styled empty-state card renders (not a blank page or raw string) with a `PageHeading` |
| `/stocks` | Stocks page (`app/stocks/page.tsx`) → `EmptyState` | New page | Stocks list shell | Navigate to `/stocks`; confirm the empty-state card and heading render and the Stocks link is highlighted |
| `/themes` | Themes page (`app/themes/page.tsx`) → `EmptyState` | New page | Themes shell | Navigate to `/themes`; confirm the empty-state card and heading render |
| `/sectors` | Sectors page (`app/sectors/page.tsx`) → `EmptyState` | New page | Sectors shell | Navigate to `/sectors`; confirm the empty-state card and heading render |
| `/scanner-runs` | Scanner Runs page (`app/scanner-runs/page.tsx`) → `EmptyState` | New page | Scanner runs list shell | Navigate to `/scanner-runs`; confirm the empty-state card (e.g. "No scan yet") and heading render |
| `/system-health` | System Health page (`app/system-health/page.tsx`) → `EmptyState` | New page | System health shell | Navigate to `/system-health`; confirm the empty-state card and heading render |
| `/watchlist` | Watchlist page (`app/watchlist/page.tsx`) → `EmptyState` | New page | Watchlist shell | Navigate to `/watchlist`; confirm the empty-state card and heading render |
| `/stocks/[ticker]` | Stock detail stub (`app/stocks/[ticker]/page.tsx`) | New page (stub) | Future row-click target resolves | Visit `/stocks/NVDA` directly; confirm it returns HTTP 200 and renders an empty-state page (not a 404) |
| `/scanner-runs/[runId]` | Scanner run detail stub (`app/scanner-runs/[runId]/page.tsx`) | New page (stub) | Future row-click target resolves | Visit `/scanner-runs/1` directly; confirm it returns HTTP 200 and renders an empty-state page (not a 404) |
| (all routes) | Dark theme tokens (`app/globals.css`) | Updated layout | Dense-dark analytical palette | Confirm the background is near-black (`#0a0e14`), accents are teal (`#4fd1c5`), and the layout is sidebar + main content (no light/default theme) |

---

## Backend-Only Changes (No UI Impact)

- `config.yaml` + `app/config.py` (typed loader) — single source of all tunables — no UI surface affected.
- `app/db.py` + `app/models.py` (8 SQLModel tables) — schema creation — no page reads these tables yet.
- `app/data_providers/` (`PriceProvider` ABC + `SeedProvider`) — offline price access layer — not surfaced in UI.
- `app/seed_loader.py` + `scripts/ingest_seed.py` + committed seed CSVs (158 symbols, ~5.4 yrs) — data ingest/load — loaded but not displayed.
- `GET /api/health` (`app/api/health.py`) — **partial UI impact**: consumed by the header `HealthBadge` only; its `db_ok`, `last_run_date`, and `seed_latest_date` fields are connectivity signals, not yet a dedicated System Health view.
- Backend test suite (`tests/*.py`, 25 passing incl. the seed-integrity keystone) — no UI surface.

---

## Summary

- **Frontend surfaces changed:** 13 (sidebar, health badge w/ 2 states, 7 section pages, 2 detail stubs, theme tokens)
- **New pages/routes:** 9 (7 nav pages + 2 detail-route stubs)
- **Modified components:** 0 modified — all components are new this iteration (`Sidebar`, `HealthBadge`, `EmptyState`, `PageHeading`, `Card`, `Badge`)
- **Navigation changes:** yes — new persistent sidebar with all 7 approved IA destinations
- **Backend-only changes:** 6 areas (config, db/models, providers, seed ingest/load, health endpoint [partially consumed], test suite)
