# Phase goal-i_can_see_the_wealthy_future-iter-7 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future-iter-7
**Date:** 2026-05-30
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

<!-- This is the goal-completing iteration: J-11 (Watchlist with persistence) — the product's first user-write/mutation surface. -->

- Users can now **save a stock to a persistent watchlist** by opening `/watchlist`, typing a ticker (e.g. `ANET`) and a free-text reason into the Add panel, and clicking **Add**. The stock appears as a new row, fetched back from the server.
- Users can now **see each saved stock's current research evidence at a glance** — its live Leadership / Entry Quality / Risk scores (A–E bucket + 0–100 number), setup status, and invalidation level — all read live from the scanner, identical to the `/stocks` leaderboard.
- Users can now **see how a saved stock has moved since they added it** via the "Since added" column (signed %, green when up, red when down, muted at 0.00%).
- Users can now **jump from a watchlist entry to that stock's full detail** by clicking its ticker, which links to `/stocks/[ticker]`.
- Users can now **remove a saved stock** by clicking the trash/Remove button on its row; the list re-fetches without it.
- Users can now **trust the watchlist survives a backend restart** — entries are stored in the database, not held in memory, so they are still present after the backend is restarted.
- Users see an **honest inline error** (never a fake success) when adding fails: an unknown ticker, a ticker already on the list, or no price data each surface the backend's explicit message.

---

## What Changed in the Visible UI

- The **`/watchlist` page** graduated from an empty "coming soon"-style stub (EmptyState only) to a working page with an **Add panel** (Ticker input + Reason input + Add button) and an **entries table**.
- The new **entries table** has columns: Ticker (link), Added (date), Reason, Leadership, Entry Quality, Risk, Setup, Since added, Invalidation, and a per-row Remove button.
- A small **"as of <date>" badge and an "<N> saved" count** appear above the table when there is at least one entry.
- The watchlist scores reuse the existing **`ScoreBadge`** component (Risk uses `invert` so high danger reads red) so they look identical to the `/stocks` leaderboard.
- An **inline alert** (`role="alert"`, red) appears under the Add panel when an add or remove action fails.
- A **"Backend unavailable" error card** appears (instead of any fabricated rows) when the watchlist cannot be loaded from the API.
- The **EmptyState** (Star icon) is retained for the zero-entry case, now with copy describing what each saved stock will show.
- **No navigation change** — the sidebar already linked "Watchlist"; that link now leads to a functional page rather than a stub.

---

## What Old Behavior Changed

- **`/watchlist` route:** previously displayed only an empty-state placeholder with no actions. Now it is a fully interactive save-list with add/remove and a live data table.
- **No other page changed.** The dashboard, stocks, sectors, themes, runs, and system-health pages and their APIs are byte-identical (J-01–J-10 are explicitly held green). The price-since-added of `0.00%` for a just-added entry against the frozen seed is the correct, honest value, not a changed behavior or defect.

---

## Not Visible Yet

- **None for this phase's scope.** Every backend capability added this iteration (POST/GET/DELETE `/api/watchlist`) is wired into the `/watchlist` UI.
- Intentionally out of scope (not a hidden capability — these were never built): order/position/quantity/P&L, per-user accounts, alerts/notifications, watchlist groups/tags, CSV export, and reordering. The watchlist is deliberately a research save-list, not a portfolio or order surface.
