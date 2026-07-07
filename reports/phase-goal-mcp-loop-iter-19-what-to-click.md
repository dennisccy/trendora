# Phase goal-mcp-loop-iter-19 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-19
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running at `http://localhost:8000` (the Stocks and Data pages show a "Backend unavailable" card if it isn't)
- No login required
- No special setup — the shipped 30-year/548-name dataset already has the ~78%-null-sector condition this guide checks, and at least one scanner run/watchlist entry is not required for these steps

---

## Verification Steps

1. Open `http://localhost:3255/stocks` in your browser
   - **Expect:** The Stock Leaderboard loads with a table (columns include Ticker, Sector, Leadership, Entry Quality, Risk); the left sidebar navigation is visible.

2. Click the word "Sector" in the column header row of the table
   - **Expect:** The table re-sorts by sector name and a small up-arrow appears next to "Sector." The page does NOT crash and the sidebar stays visible. **This is the exact click that used to blank the entire application** — it must complete cleanly now.

3. Click "Sector" again
   - **Expect:** The table re-sorts in the opposite order (the arrow flips to point down). Still no crash.

4. Above the table, click the dropdown labeled "Sector" (it currently reads "All sectors") and select "Unassigned"
   - **Expect:** The table narrows to only rows with no mapped sector (roughly 400+ of the ~541 total rows). The small counter next to the filters (e.g. "422 / 541") reflects the narrower count.

5. Look underneath any score badge (Leadership, Entry Quality, or Risk) in the narrowed list
   - **Expect:** Small text reading "Not yet proven" appears under each score. This must still be there after the sector fix — if it's ever missing or reads anything else, that's a separate regression.

6. Click any ticker in the filtered list (it opens in a new browser tab)
   - **Expect:** The stock detail page loads at `/stocks/{TICKER}`. Near the top, beside the setup-status badge, you should see the word "Unassigned" (since you filtered to that bucket).

7. On that detail page, find the "Price & moving averages" card and click the "Full history" button (next to "Recent")
   - **Expect:** The price chart redraws with a longer date range and the caption next to the buttons updates its "history since" date. No blank chart, no error.

8. Navigate to `http://localhost:3255/data`
   - **Expect:** The page finishes loading within about 20 seconds, showing a "Dataset coverage" panel with real numbers (not stuck on a loading skeleton) and no "Backend unavailable" message. This page used to risk hanging or crashing the backend on a fresh load.

9. On the same `/data` page, scroll down to the panel titled "Universe resolution as of ..." and find the tile labeled "Stale series"
   - **Expect:** A visible number with a one-line explanation beneath it (starting "Last bar more than...").

10. Go back to `http://localhost:3255/stocks` one more time
    - **Expect:** The leaderboard loads cleanly with no leftover error state from steps 2–3 — confirming the fix is stable, not just a one-time lucky pass.

---

## What "Working Correctly" Looks Like

- Clicking "Sector" (either direction) on the Stocks leaderboard never blanks the page or hides the sidebar — the single most important thing this iteration fixes.
- The Sector filter offers, and correctly filters to, an "Unassigned" option instead of having no way to isolate unmapped companies.
- Every score everywhere still shows its "Not yet proven" evidence text (this iteration touched sector display only, not the evidence ledger).
- `/data` finishes loading in well under a minute, every time, even right after a restart.

## Common Issues

- **Whole page goes blank / white screen, sidebar disappears**: this is the exact prior regression this iteration fixes. Treat it as broken and note exactly which click (step 2 or 3) caused it.
- **"Backend unavailable" card on any page**: confirm the backend process is actually running (a developer can check with `curl http://localhost:8000/health`) before treating it as a UI bug — this guide assumes both services are already up.
- **`/data` hangs for more than about a minute, or the backend becomes unresponsive on other tabs while it loads**: this is the memory/OOM issue this iteration specifically fixes — note how long it took and whether other pages (like `/stocks`) still respond while `/data` is loading.
- **Sector filter dropdown shows a blank option instead of "Unassigned"**: the fix for the honest "Unassigned" label didn't take effect — treat as broken.
