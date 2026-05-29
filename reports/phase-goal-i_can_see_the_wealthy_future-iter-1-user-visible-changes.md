# Phase goal-i_can_see_the_wealthy_future-iter-1 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future-iter-1
**Date:** 2026-05-29
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

This is the foundation iteration — it ships a navigable **app shell**, not data. Every page is an intentional empty state; no scoring, scans, or stock data appear yet.

- Users can now open the Trendora workstation and see a persistent **left sidebar** with all 7 destinations: Dashboard (`/`), Stocks (`/stocks`), Themes (`/themes`), Sectors (`/sectors`), Scanner Runs (`/scanner-runs`), System Health (`/system-health`), and Watchlist (`/watchlist`).
- Users can now **navigate between all 7 sections** by clicking sidebar links; the active section is highlighted (highlighted background + accent dot).
- Users can now see **whether the backend is connected** via the header health badge — it shows the data provider (`seed`), the latest seed date (`2026-05-28`), and the universe symbol count (`158`) when connected.
- Users can now see an explicit **"Backend unavailable"** state in the header when the backend is down — the app never fabricates a healthy status.
- Each section page shows a **styled empty-state card** describing what will appear there once scoring lands in later iterations (instead of a blank screen or raw text).

---

## What Changed in the Visible UI

This is the first iteration with any UI, so all surfaces are new:

- A new persistent **left sidebar** (`components/sidebar.tsx`) lists the 7 top-level destinations with hover/focus states and active-route highlighting.
- A new **header health badge** (`components/health-badge.tsx`) shows three states: loading ("Checking backend…", pulsing dot) → connected (green "Backend OK" + provider + seed date + symbol count) → error (red "Backend unavailable"). It re-checks every 30 seconds.
- 7 new section pages, each rendering a shared **`EmptyState` card** plus a `PageHeading`: Dashboard, Stocks, Themes, Sectors, Scanner Runs, System Health, Watchlist.
- 2 new **detail-route stubs** — `/stocks/[ticker]` (e.g. `/stocks/NVDA`) and `/scanner-runs/[runId]` (e.g. `/scanner-runs/1`) — that resolve to empty-state pages. These are not in the nav; they exist so future row-click navigation resolves.
- A new **dense-dark analytical visual theme** (`app/globals.css`): dark background (`#0a0e14`), teal accent (`#4fd1c5`), and monospace tabular-nums styling for numeric cells (no numbers shown yet, but the chrome is in place).

---

## What Old Behavior Changed

- None. This is the first iteration that produces a user-facing application; there is no prior UI behavior to change or regress.

---

## Not Visible Yet

These backend capabilities exist but have **no UI surface** this iteration (by design — they feed later iterations):

- The committed **price seed** (122 stocks + 36 ETFs + `^VIX`, ~5.4 years of real EOD bars, 158 symbols) is loaded into the database but is **not displayed anywhere** — no charts, tables, or price views exist yet.
- The **8 database tables** (stocks, etfs, sectors, industries, themes, theme_members, daily_prices, data_provider_runs) hold reference + price data that no page reads yet.
- The `data_provider_runs` ingest log exists in the backend but is **not surfaced** on the System Health page (that page is still an empty state).
- Only **one API endpoint** is consumed by the UI: `GET /api/health` (by the badge). No stock/theme/sector/scan endpoints exist yet — all 11 target user journeys (J-01…J-11) remain `failing` as planned for this infra iteration.
