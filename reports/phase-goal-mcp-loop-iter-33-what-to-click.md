# Phase goal-mcp-loop-iter-33 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-33 (J-20 — Daily Preflight Verdict)
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and reachable (its API is at `http://localhost:8255`; you don't need to visit it directly for the steps below)
- No login is required — Trendora is a local-first, single-user tool
- No special data setup is needed — the banner appears the same way whether or not you have any watchlist entries

---

## Verification Steps

1. Open `http://localhost:3255/` in your browser
   - **Expect:** The Dashboard loads, heading "Dashboard" is visible, no error screen

2. Look directly below the header bar (below the "Research-only · decision support · no orders" text, underneath the top row)
   - **Expect:** A thin, quiet, green-tinted line reading exactly **"GO — today's board is current."** with a small green dot to its left — this is the new feature: a single trust verdict for today's board

3. Click "Stocks" in the left sidebar
   - **Expect:** Navigate to `http://localhost:3255/stocks`; the identical "GO — today's board is current." strip appears in the same place, directly above the stock leaderboard table

4. Click "Watchlist" in the left sidebar, then click "Evidence" in the left sidebar
   - **Expect:** Both pages show the identical "GO — today's board is current." strip in the same position; the Evidence ledger table is fully visible beneath it, not obscured

5. Look at the top-right of the header bar (to the right of the date control)
   - **Expect:** The pre-existing "Ready" badge (green dot) is still there, showing "provider", "seed `<date>`", and "`<N>` symbols" exactly as it did before this phase — this is a different, older element from the new strip below the header, and it must still work unchanged

6. On the Stocks page, look at a few rows of the leaderboard table
   - **Expect:** Each row still fully shows its ticker, its three scores, and an evidence badge reading "Not yet proven" — nothing is hidden or cut off by the new strip above the table

7. Refresh the page (press F5)
   - **Expect:** The same "GO — today's board is current." strip reappears right away — the verdict is a live backend check performed on every load, not a value that could go stale

---

## Optional bonus step (requires shell/terminal access — skip if you don't have it)

8. Stop the backend, restart it with the environment variable `TRENDORA_LEDGER_PATH` pointed at a file that does not exist, then reload `http://localhost:3255/`
   - **Expect:** The strip turns into a full-width **red** banner reading **"NO-GO — do not rely on today's board."** with a bullet explaining which file is missing. Restart the backend normally afterward and reload — the strip should return to the green "GO" line within about 30 seconds, or immediately on refresh.

---

## What "Working Correctly" Looks Like

- The exact same thin green "GO — today's board is current." line appears in the exact same position (just below the header) on every page you visit — Dashboard, Stocks, Watchlist, Evidence, and everywhere else in the sidebar
- The older "Ready" badge in the top-right of the header keeps working exactly as it did before this phase — the new strip is an addition, not a replacement
- Nothing on any page is hidden, cut off, or broken by the new strip
- If something is genuinely wrong with today's data (step 8), the same strip turns into a loud amber or red full-width banner with a specific, plain-English reason — it never just goes blank

## Common Issues

- **Blank white page or a Next.js error overlay**: this is a real bug — even when the backend is completely unreachable, the strip should still render a red "NO-GO — do not rely on today's board." banner with the reason "Backend is unavailable — the preflight check could not run.", not a blank page. Confirm the frontend process itself is running.
- **Strip stuck on gray "Checking board status…" for more than a few seconds**: the backend likely isn't responding — check whether the "Ready" badge in the top-right (step 5) shows "Backend unavailable" instead; if so, restart the backend.
- **Strip missing entirely on some page**: this is a bug — it is mounted once in the shared layout and must appear on every page in the sidebar (Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Evidence, Watchlist, Methodology, Data Manager), not just the ones checked above.
- **New strip visually collides with `/data`'s own pre-existing warning banner**: not expected — the two should be clearly separate (the new strip is a thin single line right under the header; `/data`'s own banner, when it appears, sits further down inside the page body).
