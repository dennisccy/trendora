# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8835` (quick check: open `http://localhost:8835/health` in a new tab — you should see `{"status":"ok"}` or similar)
- Seed data is loaded — at least a few stock rows must appear on the `/stocks` leaderboard

---

## Verification Steps

1. Navigate to `http://localhost:3835/stocks?asof=2025-12-31` in your browser
   - **Expect:** The stocks leaderboard table loads and shows stock rows. To the right of the existing return columns (1d, 5d, 10d, 20d, 60d) you see five additional column headers labelled "1d MDD", "5d MDD", "10d MDD", "20d MDD", "60d MDD". Each MDD cell shows either a negative percentage (e.g., "−4.1%") or "NA". No positive MDD value appears.
   - **Broken looks like:** The five MDD columns are missing from the table header, or you see positive values such as "+2.3%" in any MDD cell.

2. Click the "5d MDD" column header on the same `/stocks` page
   - **Expect:** The table immediately re-sorts (no page reload). All rows with "NA" in the "5d MDD" column sink to the bottom; rows with real negative values are at the top, ordered by magnitude. Clicking the header a second time reverses the order among real values; NA rows stay at the bottom either way.
   - **Broken looks like:** "NA" rows are mixed in between real-value rows, or the page reloads when sorting.

3. Click any stock ticker link in the leaderboard to open its detail page (opens at `/stocks/[TICKER]?asof=2025-12-31`)
   - **Expect:** The stock detail page opens. In the forward-return horizon panel, each of the five horizon cards (1d, 5d, 10d, 20d, 60d) now has two lines: the top line is the return value and the bottom line reads "Max drawdown" followed by a negative percentage or "NA". Every card shows this sub-line — none are missing it.
   - **Broken looks like:** Only one line per card (no "Max drawdown" sub-line), or the sub-line shows a positive number.

4. Navigate to `http://localhost:3835/themes?asof=2025-12-31`
   - **Expect:** The themes leaderboard loads with five MDD columns to the right of the return columns. Click the expand control on any theme row (the "+" button or chevron). The expanded member list appears and visually spans the full table width — the member content does not end short of the MDD columns.
   - **Broken looks like:** MDD columns are missing, or the expanded member row creates a visual gap or truncation where the MDD columns are.

5. Navigate to `http://localhost:3835/backtest?asof=2025-12-31`
   - **Expect:** The Backtest page loads. In the evidence breakdown tables (by-bucket, by-setup, or by-regime), a "Mean MDD" column appears alongside the mean-return column. Cell values are negative percentages or "NA" — never positive. The evidence summary header also shows a "Mean max drawdown" figure.
   - **Broken looks like:** No "Mean MDD" column in the breakdown tables, or positive values in any "Mean MDD" cell.

6. Navigate to `http://localhost:3835/data`
   - **Expect:** The Data page loads. A "RebuildPanel" section is visible on the page containing a "Rebuild snapshots for current universe" button. If all snapshot members are accounted for, a calm note such as "all members present" is shown (no amber banner). If there are absent members, an amber banner lists the count and ticker names.
   - **Broken looks like:** No RebuildPanel or rebuild button on the page, or the page crashes on load.

7. On `http://localhost:3835/data`, click the "Rebuild snapshots for current universe" button
   - **Expect:** A confirm modal overlay appears on screen. The modal contains a description of the rebuild action and a "Confirm" button that is fully visible without any scrolling. A "Cancel" button or close icon is also visible. No rebuild job has started yet.
   - **Broken looks like:** Clicking the button immediately starts a job with no confirmation dialog, or the button does nothing.

8. In the confirm modal, click "Cancel" (or the close icon)
   - **Expect:** The modal closes. No rebuild job is running — the "Rebuild snapshots for current universe" button is still enabled and no job-progress card appears.
   - **Broken looks like:** The modal closes but a rebuild job starts anyway, or the button becomes permanently disabled after cancelling.

---

## What "Working Correctly" Looks Like

- The `/stocks?asof=2025-12-31` leaderboard shows exactly ten return-related columns: five forward-return columns followed immediately by five MDD columns, all labelled clearly.
- Every MDD cell across `/stocks`, `/themes`, and `/sectors` is either a negative percentage or "NA" — never a positive number, never a zero percentage that should be "NA".
- The `/data` page has a visible rebuild button that is confirm-gated: clicking it shows a modal, and the job only starts after the operator clicks "Confirm".

## Common Issues

- **MDD columns not visible on /stocks or /themes**: The frontend may be serving a cached build. Hard-refresh the browser (Ctrl+Shift+R or Cmd+Shift+R) or clear the browser cache and reload.
- **Positive MDD values appearing**: This indicates a data integrity issue — the max-drawdown computation may have used the wrong sign convention. Report the specific ticker, horizon, and as-of date.
- **Rebuild button missing from /data page**: The backend may be running an older version that does not serve the coverage diagnostic. Verify the backend is on the correct build by checking `http://localhost:8835/health`.
- **Confirm modal not appearing when rebuild button is clicked**: Hard-refresh the frontend. If the issue persists, open browser developer tools (F12), check the Console tab for JavaScript errors, and report any error messages.
