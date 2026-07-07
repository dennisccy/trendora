# Phase goal-mcp-loop-iter-18 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-18
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running (no login needed anywhere in this product)
- No seed data setup needed — the 30-year price history and the regenerated evidence ledger are already loaded

---

## What this iteration changed, in one sentence

The product now shows real price history back to each stock's actual first trading day (instead of a
short fixed window), a much larger list of tickers, and an honestly-reset evidence ledger where **every**
score currently reads "Not yet proven" — that dark, unproven state is the CORRECT result of this run, not
a bug.

---

## Verification Steps

1. Open `http://localhost:3255/stocks/AAPL` in your browser
   - **Expect:** The page loads with a "Price & moving averages" chart card. In that card's header you should see a new two-button control reading "Recent" / "Full history", next to the existing "Regime on" button.

2. Click the "Full history" button
   - **Expect:** The chart briefly shows a gray placeholder box, then re-renders showing decades of price history (not just a few years). The small caption text next to the buttons should read something like "`N` bars · as of `DATE` · history since **1996-01-02** · older bars weekly-sampled".
   - **Broken looks like:** the chart goes blank and stays blank, or the caption never changes/updates.

3. Click "Recent" to switch back
   - **Expect:** The chart returns to a shorter (~5-year) view within a second or two. The caption still says "history since 1996-01-02" (just without the "weekly-sampled" suffix) — confirming the honest depth is disclosed either way.

4. Navigate to `http://localhost:3255/stocks`
   - **Expect:** A leaderboard loads with a row count shown near the search box reading something like "`N` / `N`" where `N` is several hundred — clearly more than ~122. Under every row's Leadership/Entry Quality/Risk score, you should see a small gray badge reading "**Not yet proven**".

5. Navigate to `http://localhost:3255/evidence`
   - **Expect:** Exactly **7** claim cards render. Each one shows a verdict badge reading "**FAIL**" and a "Registration date" of "**2026-07-03**". You should NOT see the word "PASS" or "Proven" on this page at all.

6. Navigate to `http://localhost:3255/watchlist`. Type `ABBV` into the "Ticker" field and click the "Add" button
   - **Expect:** A new row for ABBV appears in the table below, with its own live scores — no "unknown ticker" error. (ABBV is a real stock outside the app's original ~122-name list, proving the wider pool is actually being served.)

7. Refresh the page (press F5)
   - **Expect:** The ABBV row you just added is still there after the refresh — confirming it was actually saved, not just shown temporarily.

8. Navigate to `http://localhost:3255/data` and scroll to the "Universe resolution as of..." panel
   - **Expect:** A row of **5** small metric cards: "Admitted", "Below min history", "**Stale series**" (this one is new), "Below min price", "Below min liquidity".

9. Back on `http://localhost:3255/watchlist`, type `ZZZZZ` into the "Ticker" field and click "Add"
   - **Expect:** A red error message appears reading "**unknown ticker: ZZZZZ**", and no new row is added — a made-up ticker is still correctly rejected.

10. Navigate to `http://localhost:3255/stocks/ARM`
    - **Expect:** The chart caption reads "history since **2023-09-14**" (ARM's real IPO date) even if you click "Full history" — no invented years of price history appear before that date.

---

## What "Working Correctly" Looks Like

- Every score badge on `/stocks` and `/stocks/{ticker}` reads "Not yet proven" — a calm gray badge, never an alarming color, and never the word "Proven" anywhere in the app right now.
- The Stock Detail chart's "Recent"/"Full history" toggle changes the visible price span, and the caption's disclosed first-available date is always real (1996-01-02 for AAPL, 1999-01-22 for NVDA, 2023-09-14 for ARM) — never fabricated.
- Adding a ticker like ABBV (outside the original ~122-name list) to the Watchlist now succeeds, while a nonsense ticker like ZZZZZ is still honestly rejected.

## Common Issues

- **Blank page / error screen anywhere:** confirm the backend is running (`curl http://localhost:8255/health` — this project's backend/frontend ports share one deterministic offset, so port 8255 pairs with frontend port 3255).
- **Chart stays blank after clicking "Full history":** wait a couple of seconds — deep history takes slightly longer to fetch than the bounded "Recent" view. If it never resolves, that's a real defect.
- **New ticker not appearing on Watchlist after "Add":** check for a red error line below the form — if it says "unknown ticker", the ticker you typed genuinely isn't in the stored price data; try ABBV, ABT, or ACGL instead.
- **Chart still shows "Full history" span on a new ticker page you didn't expect:** this is a persisted browser preference (not a bug) — click "Recent" to reset it.
- **Seeing the word "Proven" anywhere, or seeing any of these old numbers — +21.34%, +8.91%, p=0.0004998, or a register date of 2026-06-30/07-01:** this WOULD be a real defect this iteration — the ledger reset should have replaced all of them.
