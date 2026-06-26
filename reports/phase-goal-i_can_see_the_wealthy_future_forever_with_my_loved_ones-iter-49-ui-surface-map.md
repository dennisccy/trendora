# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49
**Date:** 2026-06-26
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|---|---|---|---|---|
| `/stocks` | Leaderboard table — "Proximity to 52w high" column | New column | J-106: Added sortable column re-displaying the stored `high_proximity` Leadership value | Navigate to `/stocks` and confirm a column labeled "Proximity to 52w high" appears immediately to the right of the "Risk" column header, showing a percentage or "NA" in each row |
| `/stocks` | "Proximity to 52w high" `SortHeader` | New feature | J-106: Column header must be a clickable sort control | Click the "Proximity to 52w high" header once; verify the table rows reorder (ascending) and an arrow indicator appears on that header alone; click again and verify the order reverses to descending |
| `/stocks` | NA rows in the "Proximity to 52w high" column | New feature | J-106: Stocks with short price history must render "NA" and sort last | Sort by "Proximity to 52w high" in both ascending and descending order; verify any rows showing "NA" in that column remain at the bottom of the table in both directions |
| `/stocks` | "Proximity to 52w high" info tooltip (`TermInfo`) | New feature | J-106: Column header must carry the config-backed glossary tooltip | Hover the info icon on the "Proximity to 52w high" header; verify a tooltip appears containing the glossary definition for "52-week high proximity" (not hard-coded copy) |
| `/stocks/:ticker` (Stock Detail) | Leadership score `ComponentBreakdown` — "Proximity to 52w high" row | Changed behavior | J-106 single-source: breakdown now shows raw distance value instead of opaque percentile | Open any stock's detail page, scroll to the Leadership breakdown, find the "Proximity to 52w high" row, and verify its value (e.g., `-0.53%`) exactly matches that ticker's cell in the `/stocks` leaderboard "Proximity to 52w high" column |
| All pages | Top-bar readiness badge | Changed behavior | J-108: Badge must reach Ready/Initializing when app is opened at LAN-IP address | Start the app with `./scripts/dev.sh`; open the LAN-IP URL it prints (e.g., `http://192.168.1.68:3255`); within a few seconds the badge must display "Initializing… history n/m" and then transition to "Ready" — NOT "Backend unavailable" |
| All pages | Top-bar readiness badge — genuine-down state | Changed behavior | J-108: Badge must still show Unavailable when backend is actually down | With the frontend running, stop only the backend process; verify the badge changes to "Backend unavailable" and does not remain on "Ready" or "Initializing" |
| All pages | All data-fetching pages (Dashboard, Leaderboard, Research Lab, Scanner, Stock Detail) | Changed behavior | J-108: Host-aware API base must not break existing data loading on localhost | Open the app at `localhost` (not LAN-IP) and navigate to the Dashboard, `/stocks`, and at least one Stock Detail page; confirm all data sections load without errors, identical to before this iteration |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/main.py` — refactored into `create_app()` factory + added `CORS_ORIGIN_REGEX` support — enables the dev CORS widening that makes the badge work at the LAN-IP address; adds no new endpoint or served data field
- `scripts/dev.sh` — computes `LOCAL_IP` before CORS export; adds the LAN-IP frontend origin to `CORS_ORIGINS`; sets `CORS_ORIGIN_REGEX` — dev-only configuration change; no UI surface change
- `apps/backend/tests/test_cors_dev_lan.py` (NEW) — backend test asserting LAN-IP origin is allowed with the regex and that readiness states are unchanged — no UI surface
- `apps/frontend/lib/api-base.test.ts` (NEW) — unit tests for the `resolveApiBase()` resolver; run in CI — no UI surface

---

## Summary

- **Frontend surfaces changed:** 5 (Leaderboard table column, sort header, NA sort behavior, info tooltip, ComponentBreakdown; readiness badge behavior on LAN-IP)
- **New pages/routes:** 0
- **Modified components:** 3 (`apps/frontend/app/stocks/page.tsx`, `apps/frontend/components/component-breakdown.tsx`, `apps/frontend/lib/api.ts`)
- **New frontend files:** 3 (`lib/api-base.ts`, `lib/api-base.test.ts`, `lib/high-proximity.ts`)
- **Navigation changes:** no
- **Backend-only changes:** 3 (`main.py` CORS factory, `scripts/dev.sh` env setup, `tests/test_cors_dev_lan.py`)
