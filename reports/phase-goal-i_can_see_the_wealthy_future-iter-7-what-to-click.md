# Phase goal-i_can_see_the_wealthy_future-iter-7 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future-iter-7
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3836`
- Backend running at `http://localhost:8835` (so the page can load and save)
- Watchlist DB empty to start (so the empty state shows). `ANET` is a valid ticker.
- For step 7 (restart check): ability to restart the backend (`bash scripts/start-backend.sh`).

---

## Verification Steps

<!-- Prioritizes: 1) the new save action works, 2) data persists across restart, 3) old pages still work. -->

1. Open `http://localhost:3836` in your browser, then click "Watchlist" in the left sidebar.
   - **Expect:** Navigate to `http://localhost:3836/watchlist`. Heading "Watchlist" is visible, with an Add panel (Ticker field, Reason field, "Add" button) and the empty-state star card "Your watchlist is empty" below it. (Not a "coming soon" stub.)

2. Type `ANET` in the "Ticker" field and `strong leader, watching pullback` in the "Reason" field, then click the "Add" button.
   - **Expect:** Both fields clear. A new table appears with an "as of <date>" badge and "1 saved" count. A row shows `ANET` (blue/accent link), a date, your reason, three score badges (Leadership / Entry Quality / Risk, each a letter + number), a Setup badge, a "Since added" %, and an Invalidation note.

3. Look at the "Since added" cell of the ANET row.
   - **Expect:** It reads `+0.00%` (or `0.00%`) in muted/neutral gray — NOT green, red, blank, or "NaN". This is the honest value against the frozen seed.

4. Open `http://localhost:3836/stocks` in a new tab, find the ANET row, and compare its Leadership / Entry / Risk badges to the ones on the watchlist row.
   - **Expect:** The bucket letters and numbers are identical on both pages (single source). The Risk badge reads red for high danger.

5. Back on `http://localhost:3836/watchlist`, click the `ANET` ticker link.
   - **Expect:** Navigate to `http://localhost:3836/stocks/ANET` and the ANET detail page loads.

6. Go back to `http://localhost:3836/watchlist`, type `ZZZZ` in the "Ticker" field with any reason, and click "Add".
   - **Expect:** A red inline error appears under the Add panel (warning triangle) with the backend's message. NO `ZZZZ` row is added. (This proves failures are honest, never faked.)

7. Restart the backend (stop uvicorn on `:8835`, run `bash scripts/start-backend.sh`, wait for `http://localhost:8835/api/health` to be ok), then reload `http://localhost:3836/watchlist` (F5).
   - **Expect:** The `ANET` row is STILL there with the same date and reason — proving the watchlist is database-backed, not in memory.

8. Click the trash/Remove button on the far right of the `ANET` row.
   - **Expect:** The ANET row disappears and the empty-state card "Your watchlist is empty" returns (no full page reload).

---

## What "Working Correctly" Looks Like

- After step 2, the new ANET row shows real score badges identical to the `/stocks` leaderboard — proving scores are read live, not stored or fabricated.
- After step 7, the entry persists across a backend restart — the J-11 persistence crux.
- Failures (step 6) surface as a visible red inline error with no fabricated row.

## Common Issues

- **"Backend unavailable" red card instead of the empty state / table**: The backend on `:8835` is not running — start it and reload.
- **Add seems to do nothing and the button looks faded**: The "Add" button is disabled while the Ticker field is empty; type a ticker first.
- **ANET row missing after restart (step 7)**: Persistence is broken — the entry was held in memory rather than the database. This is a fail.
- **Watchlist scores differ from `/stocks` (step 4)**: Single-source violation — report it.
