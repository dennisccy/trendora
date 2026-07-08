# Phase goal-mcp-loop-iter-22 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-22
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running at `http://localhost:8255`
- No login is required anywhere in this app
- The local database already has the 3 new deep benchmark symbols loaded (this was done as part of
  building this feature — you don't need to run anything yourself)

---

## Verification Steps

1. Open `http://localhost:3255` in your browser
   - **Expect:** The "Dashboard" heading loads with no red error banner. Scroll down slightly until you
     see a card titled **"Regime × phase cross-view"** (directly below the "Market Regime" / "Market Phase
     & Severity" cards). If you instead see a dashed button reading "Show regime × phase cross-view",
     click it once to reveal the chart.

2. Look at the row of labels (the legend) directly below the chart, and the small colored dot to the left
   of each label
   - **Expect:** 10 entries total. 5 of them — `S&P 500 Index (^SPX)`, `Nasdaq 100 Index (^NDX)`,
     `Dow Jones Industrial Average (^DJI)`, `CBOE Volatility Index (^VIX)`, and
     `10Y-2Y spread proxy (^TNX)` — each show a small gray tag in parentheses right after the name:
     `(Stooq)`, `(Stooq)`, `(Stooq)`, `(Yahoo)`, and `(FRED-macro proxy)` respectively. The other 5 —
     `S&P 500 (SPY)`, `Nasdaq 100 (QQQ)`, `Russell 2000 (IWM)`, `S&P 500 Equal-Weight (RSP)`,
     `Dow 30 (DIA)` — show no such tag. Also confirm all 10 colored dots look different from each other —
     in particular, the 1st dot (`S&P 500 (SPY)`) and the 6th dot (`S&P 500 Index (^SPX)`) must be
     visibly different colors, not the same.

3. Move your mouse pointer anywhere over the chart's plotted lines
   - **Expect:** A small tooltip box appears in the top-right corner of the chart, listing the hovered
     date and each visible line's symbol plus its `%` value. The new benchmark lines show a small
     `· Stooq`, `· Yahoo`, or `· FRED-macro proxy` tag right after their symbol (e.g. `^SPX · Stooq`);
     the 5 original lines (`SPY`, `QQQ`, `IWM`, `RSP`, `DIA`) show no such tag.

4. Refresh the page (press F5)
   - **Expect:** The exact same 10-line legend with the same vendor tags reappears — this confirms the
     data comes from the server (not a one-time fluke or client-only state).

5. Click **"Data Manager"** in the left sidebar
   - **Expect:** The page navigates to `http://localhost:3255/data`; the heading "Data Manager" is
     visible.

6. Scroll down the `/data` page until you pass the existing **"Macro feed"** card
   - **Expect:** A new card titled **"Index & benchmark data provenance"** appears directly after it,
     showing a 3-column table (Series / Vendor / First bar). The row for `S&P 500 Index (^SPX)` shows
     Vendor `Stooq` and First bar `1996-01-02`. The row for `S&P 500 (SPY)` shows Vendor `—` (a plain
     dash, not blank or "null").

7. Click **"Stocks"** in the left sidebar
   - **Expect:** The leaderboard loads at `http://localhost:3255/stocks` with normal-looking ticker rows.
     Scan the symbol column — you should **not** see any row for `^SPX`, `^NDX`, `^DJI`, `^VIX`, or
     `^TNX`. This confirms the new benchmark/macro lines did not leak into the scored leaderboard.

---

## What "Working Correctly" Looks Like

- The Dashboard's "Regime × phase cross-view" chart shows 10 legend entries (not 5), and 5 of them carry
  a small `(Stooq)` / `(Yahoo)` / `(FRED-macro proxy)` tag.
- All 10 line colors in the legend are visually distinct from one another.
- The new `/data` card "Index & benchmark data provenance" lists all 10 series with a vendor badge (or
  `—`) and a real first-bar date for every row.
- Everything from before this change still works: `/stocks` still shows only real stock tickers, and the
  Dashboard's "Market Regime" card and its "See evidence proven in this regime →" link still work.

## Common Issues

- **Blank page / error screen anywhere**: check the backend is running —
  `curl http://localhost:8255/api/health` should respond, not time out.
- **Chart still shows only 5 lines / no vendor tags at all**: this usually means the frontend is serving a
  stale cached build. Hard-refresh (Ctrl+Shift+R); if that doesn't help, the frontend's `.next` build
  cache likely needs clearing and restarting.
- **The 1st and 6th legend dots look like the exact same color**: this is the specific color-collision
  defect this iteration was supposed to fix — if you see it, the palette fix did not ship correctly.
- **The new "Index & benchmark data provenance" card is missing entirely under "Macro feed"**: hard-refresh
  first (it's a brand new card, easy to miss if the page was cached from before this change);  if it's
  still missing after a hard refresh, that's a real defect.
- **A row in `/stocks` shows a symbol starting with `^`**: this would mean a deep index/macro symbol leaked
  into the scored leaderboard — a real regression, not expected under any circumstance.
