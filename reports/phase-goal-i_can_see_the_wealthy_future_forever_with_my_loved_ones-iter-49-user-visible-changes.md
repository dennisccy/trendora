# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49
**Date:** 2026-06-26
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see each stock's distance below its 52-week high directly in the Stock Leaderboard at `/stocks`, without opening a stock's detail page.
- Users can now sort the leaderboard by proximity to 52-week high by clicking the new "Proximity to 52w high" column header; clicking again reverses the sort order.
- Users can now hover the info icon on the "Proximity to 52w high" column header to read its config-backed glossary definition.
- Users who open the app at the network (LAN-IP) address printed by the start script now see live data and a correct readiness badge — previously the entire app appeared broken ("Backend unavailable") at that address.

---

## What Changed in the Visible UI

- The Stock Leaderboard table at `/stocks` now has a "Proximity to 52w high" column placed directly to the right of the "Risk" column. It shows a percentage (≤ 0; `0.00%` means the stock is at a fresh 52-week high) or a muted "NA" for stocks with insufficient price history.
- The "Proximity to 52w high" column header includes a sortable click control (with an ascending/descending arrow indicator) and an info icon that shows the glossary definition when hovered — consistent with every other numeric column in the leaderboard.
- On any stock's Detail page, the Leadership score component breakdown now shows the actual distance below the 52-week high (e.g., `-0.53%`) in the "Proximity to 52w high" row. Previously that row displayed an internal ranking figure ("pctl XX") that did not match the leaderboard value.
- The top-bar readiness badge now correctly displays its three honest states (Ready / Initializing… history n/m / Backend unavailable) when the app is opened via the LAN-IP address in addition to localhost. No visual change to the badge itself — only the conditions under which it reaches "Ready" were corrected.

---

## What Old Behavior Changed

- **Stock Detail Leadership breakdown — "Proximity to 52w high" row**: previously showed an opaque internal percentile rank ("pctl XX"). Now shows the actual distance-below-high percentage (e.g., `-0.53%`), identical to the new leaderboard column for the same ticker. All other Leadership breakdown rows are unchanged.
- **Readiness badge and data loading at the LAN-IP address**: previously the badge was permanently stuck on "Backend unavailable" and all data fetches failed when the app was opened at the network address (e.g., `http://192.168.1.68:3255`). The badge now reaches Ready/Initializing and all pages load data correctly at that address. Behavior when opening at `localhost` is unchanged.

---

## Not Visible Yet

- None. Both J-106 (new leaderboard column) and J-108 (honest readiness badge) are fully user-visible. The backend CORS allowance added by J-108 is a development-mode infrastructure change that exists solely to make the existing badge work at the LAN address; it adds no new endpoint or data to the UI.
