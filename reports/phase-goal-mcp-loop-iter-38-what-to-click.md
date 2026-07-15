# Phase goal-mcp-loop-iter-38 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-38
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`, backend running and reachable. No login is
  required — this app has no authentication.
- The watchlist should currently contain at least ABBV and MSFT (the seeded real watchlist). If
  it's empty, add any 2+ real tickers first (e.g. type "AAPL" into the Ticker field, "MSFT" into
  a second add) via the "Add" button on `/watchlist` so the new section below has enough names to
  render.

---

## Verification Steps

1. Open `http://localhost:3255/watchlist` in your browser
   - **Expect:** The "Watchlist" page loads with the existing entries table showing rows for
     ABBV and MSFT (or whatever names are currently saved). No error message.

2. Scroll down below the entries table
   - **Expect:** A new card titled **"Concentration X-ray"** appears, subtitled "Descriptive
     only — how correlated, clustered, and concentrated your watchlist really is. No
     recommendations."

3. Read the headline just above the correlation grid, then hover the cell where the "ABBV" row
   crosses the "MSFT" column
   - **Expect:** The headline reads "≈ 2.0" followed by "effective independent bets (over the
     last 126 trading days)". The hovered cell shows "-0.11" in red text, and a tooltip states
     the precise correlation and "126 trading days".

4. Look at the "Clusters" badges, then the three bar sections below them (Sector concentration /
   Theme concentration / Shared setup)
   - **Expect:** Two separate gray badges reading "ABBV" and "MSFT" (not merged into one badge);
     a "Technology" bar and an "Unassigned" bar (both "1 · 50%"); three theme bars each
     "1 · 50%"; one red "Avoid" setup bar reading "2 · 100%".

5. Click the small "i" info icon immediately to the right of the "effective independent bets"
   headline
   - **Expect:** A text panel opens explaining the methodology, stating "126 trading days" and
     "60 days" as explicit numbers. Click anywhere else on the page and the panel closes again.

6. Type "AAPL" into the field labeled "Ticker", then click the "Add" button
   - **Expect:** A new "AAPL" row appears in the entries table, and the correlation grid below
     grows from a 2×2 grid to a 3×3 grid that includes AAPL as a row and column.

7. Click the trash-can icon at the right end of the new AAPL row
   - **Expect:** The AAPL row disappears from the entries table, and the correlation grid shrinks
     back to the original 2×2 ABBV/MSFT grid.

8. Refresh the page (press F5)
   - **Expect:** ABBV and MSFT are still the only two entries, and the "Concentration X-ray"
     section shows the same figures as in step 3 — confirms steps 6–7 didn't corrupt the
     watchlist or the X-ray data.

---

## What "Working Correctly" Looks Like

- The "Concentration X-ray" card sits directly below the entries table with a real, populated
  correlation grid, an "≈ 2.0 effective independent bets" headline (window always stated next to
  it), cluster badges, and three concentration bar rows — never a blank box, a spinner that never
  resolves, or a wall of "—" cells.
- Every figure in the X-ray section (the -0.11 correlation, the 2.0 ENB, the 50%/100% bars) is
  identical before and after adding/removing a throwaway ticker and refreshing — nothing about
  the existing ABBV/MSFT data is disturbed just by viewing or interacting with the new section.

## If Something Looks Wrong

- **"Concentration X-ray" section is missing entirely (only the old entries table shows):** the
  frontend production build is likely stale. This project has hit this exact trap before — force
  a rebuild (`rm -rf apps/frontend/.next` then restart the frontend) before concluding the
  feature is broken.
- **Blank page / "Backend unavailable" card:** confirm the backend process is running and
  reachable; the error card's own text will confirm this is the cause.
- **Every correlation cell shows "—" instead of numbers:** the two watchlist names don't have
  enough overlapping price history (need ≥ 60 trading days each) — check you're using ABBV/MSFT
  or another pair of well-established tickers, not a very recently added one.
- **Add/Remove buttons produce no visible change:** open the browser console and look for a
  failed request to `/api/watchlist` — this is the same pre-existing form/control from before
  this phase, so a failure here is not new to this phase's changes.
