# Phase goal-i_can_see_the_wealthy_future-iter-1 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future-iter-1
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running and reachable (so the health badge can connect)
- No login or seed setup required — the committed seed loads automatically on backend boot
- This iteration ships an **app shell only**: every section page is an intentional empty state. You are verifying that the shell renders, navigation works, and the backend connectivity badge is honest — not that any stock/scan data appears (none exists yet).

---

## Verification Steps

1. Open `http://localhost:3835/` in your browser
   - **Expect:** A dark-themed page loads with a left sidebar (brand "Trendora" at top), heading "Dashboard", subtitle "The daily snapshot at a glance", and an empty-state card titled "No scan yet". No error page.

2. Look at the top-right of the header
   - **Expect:** A green badge "Backend OK", plus badges "provider: seed", "seed 2026-05-28", and "158 symbols". (On first load it may briefly show "Checking backend…".)
   - **Broken looks like:** a red "Backend unavailable" badge while the backend is actually running.

3. Confirm the sidebar lists all 7 destinations
   - **Expect:** "Dashboard", "Stocks", "Themes", "Sectors", "Scanner Runs", "System Health", "Watchlist" — and a footer "Offline seed spine · v0.1".

4. Click "Stocks" in the sidebar
   - **Expect:** URL becomes `http://localhost:3835/stocks`; heading "Stocks" with an empty-state card "No ranked stocks yet"; the "Stocks" link is highlighted with a teal accent dot.

5. Click "Scanner Runs" in the sidebar
   - **Expect:** URL becomes `http://localhost:3835/scanner-runs`; heading "Scanner Runs"; empty-state card "No scanner runs yet"; "Scanner Runs" link now highlighted (Stocks no longer highlighted).

6. Click through "Themes", "Sectors", "System Health", and "Watchlist" in turn
   - **Expect:** Each navigates to its route and shows a heading matching the link and a distinct empty-state card ("No ranked themes yet", "No ranked sectors yet", "No evidence yet", "Your watchlist is empty"). The header + health badge stay visible the whole time.

7. Navigate directly to `http://localhost:3835/stocks/NVDA`
   - **Expect:** Heading "NVDA" with subtitle "Stock detail" and an empty-state card "Detail not available yet" — NOT a 404 page. (This route is reachable directly but is not in the sidebar.)

8. Navigate directly to `http://localhost:3835/scanner-runs/1`
   - **Expect:** Heading "Run #1" with an empty-state card "Run detail not available yet" — NOT a 404.

9. Stop the backend, then reload `http://localhost:3835/`
   - **Expect:** The page still renders, but the header badge now turns red and reads "Backend unavailable" — and shows NO provider/seed/symbol values. This proves the app never fakes a healthy status. (Restart the backend afterward.)

---

## What "Working Correctly" Looks Like

- A dense dark (near-black) layout with a fixed left sidebar + top header; one sidebar link is always highlighted with a teal accent dot for the current page.
- A green "Backend OK" badge showing `provider: seed`, `seed 2026-05-28`, and `158 symbols` when the backend is up — and a red "Backend unavailable" badge when it is down.
- Every section page shows a styled empty-state card (never a blank screen, raw text, or 404).

## Common Issues

- **Red "Backend unavailable" while backend is running:** Check the backend is up and reachable, and that the frontend's `NEXT_PUBLIC_API_URL` / CORS origin is configured so the browser can reach `GET /api/health`.
- **404 on `/stocks/NVDA` or `/scanner-runs/1`:** The dynamic detail-route stubs failed to build/deploy; check the frontend build succeeded.
- **Light/white theme instead of dark:** The dark theme tokens in `globals.css` didn't load; hard-refresh (Ctrl/Cmd+Shift+R) to clear cached CSS.
