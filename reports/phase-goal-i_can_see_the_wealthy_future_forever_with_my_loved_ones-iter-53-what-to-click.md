# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-53 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-53
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and healthy (verify with: `curl http://localhost:8000/health`)
- No specific login required — the app is accessible without authentication

---

## Verification Steps

1. Navigate to `http://localhost:3255/research` in your browser
   - **Expect:** The Research hub page loads showing a grid of lab tiles. A tile labelled "Regime Lab" with a Gauge icon is visible alongside existing tiles such as "Factor Lab". If you see only a blank page or a spinner that never resolves, the backend may be down.

2. Click the "Regime Lab" tile on the Research hub
   - **Expect:** The browser navigates to `http://localhost:3255/research/regime-lab`. The page displays a loading skeleton (shimmering placeholder rows) briefly, then two stacked tables appear: a by-label summary table and a regime-score decile table. A survivorship-bias caveat banner is visible near the top of the page.
   - **Broken looks like:** A "Backend unavailable" card, a blank white page, or a 404 "Page not found" error.

3. Count the rows in the first (by-label) table
   - **Expect:** Exactly 6 data rows are present, each labelled with a regime name (e.g., "Risk-on", "Risk-off"). Each row has numeric values or "NA" in the columns. An `N=` chip showing an observation count is visible on at least one return cell.
   - **Broken looks like:** Fewer than 6 rows, all cells showing "NA", or the table header appearing with no data rows.

4. Count the rows in the second (regime-score decile) table
   - **Expect:** Exactly 10 data rows labelled D1 through D10, plus a "Rank-IC" row above D1. Each decile row shows a score-range value (e.g., "10.5–22.3") and paired return/MDD values per horizon.
   - **Broken looks like:** Fewer than 10 rows, missing decile labels, or no Rank-IC row.

5. Click the column sort header for the "1d" (1-day) return column in the by-label table (look for an up/down arrow icon on the column header)
   - **Expect:** The 6 regime-label rows reorder immediately without a page reload. The row that was at the top before clicking is no longer at the top (unless all values were already sorted). Clicking the same header a second time reverses the order.
   - **Broken looks like:** Rows do not change order, the page reloads, or the sort header has no effect.

6. Click the As-of / All-history toggle (located in the Research Controls section near the top of the page)
   - **Expect:** The tables briefly show a loading state, then re-render with reduced `N=` chip values. At least one chip that previously showed a higher count (e.g., "N=150") now shows a smaller count (e.g., "N=92"). No native date picker calendar popup appears.
   - **Broken looks like:** The n values do not change after toggling, a browser date picker opens, or the page crashes.

7. Click the `N=` chip on any return cell in the by-label table (e.g., click the chip labelled "N=42" on the "Risk-on" 20-day return cell)
   - **Expect:** A new browser tab opens at a URL beginning with `http://localhost:3255/research/samples`. The Samples page shows a "Total observations" count that matches the number in the chip you clicked (e.g., 42). The original Regime Lab tab remains open.
   - **Broken looks like:** Clicking the chip has no effect, the Samples page opens in the same tab, the Samples count does not match the clicked n, or the Samples page shows an error.

---

## What "Working Correctly" Looks Like

- The `/research` hub shows a "Regime Lab" tile with a Gauge icon among the other lab tiles
- `/research/regime-lab` renders two stacked tables (6-row by-label + 10-row D1–D10 decile) with a survivorship caveat banner and no native date picker on the page
- Sort headers reorder rows client-side (no page reload), with NA values always at the bottom
- Toggling As-of mode reduces the `N=` chip counts in both tables
- Clicking an `N=` chip opens Research Samples in a new tab with a matching total observation count

## Common Issues

- **"Backend unavailable" card on `/research/regime-lab`**: The backend is not running or is not responding. Run `curl http://localhost:8000/health` to confirm. Start the backend with `./scripts/dev.sh` from the project root.
- **Tables show all "NA" cells**: The backend may have no data yet (empty database). Check that at least one scanner run has completed.
- **N= chip count does not match Samples total**: This is a count-coherence failure. Note the mismatched values and report them — do not proceed past this step.
- **Sort header has no effect**: Try a hard-reload of the page (Shift+F5) and retry. If the issue persists, it is a frontend bug.
