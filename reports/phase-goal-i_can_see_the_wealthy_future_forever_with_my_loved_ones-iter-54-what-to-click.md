# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-54 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-54
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and responding (verify with `curl http://localhost:8000/health` — expect HTTP 200)
- No special login or seed data required; the app uses the existing populated database

---

## Verification Steps

1. Navigate to `http://localhost:3255/research`
   - **Expect:** The Research hub loads. A tile labelled "Market Phase & Severity Lab" with a Thermometer icon is visible in the LABS section alongside other existing lab tiles (e.g., Regime Lab, Factor Lab).
   - **Broken looks like:** No such tile exists, the tile shows a broken image/icon, or the hub page itself errors.

2. Click the "Market Phase & Severity Lab" tile
   - **Expect:** Browser navigates to `http://localhost:3255/research/phase-severity-lab`. The page heading "Market Phase & Severity Lab" is visible. A caveat about survivorship bias or descriptive evidence appears in the page header. Two tables begin loading.
   - **Broken looks like:** Page shows 404, blank screen, spinner that never resolves, or an unhandled error overlay.

3. Wait for both tables to fully load, then count the rows in the upper table (by-phase-label)
   - **Expect:** Exactly five rows appear — one each for Expansion, Recovery, Pullback, Correction, and Bear — each showing numeric or "NA" values in the horizon columns. No row is blank or shows "undefined".
   - **Broken looks like:** Fewer or more than five rows, all cells show "NA", or cells contain raw JS values like "[object Object]".

4. Scroll down to the lower table (by-severity-decile) and confirm it contains 11 rows
   - **Expect:** One Rank-IC header row at the top, followed by ten rows labelled D1 through D10. Each decile row shows a score range (two numbers) in its first column.
   - **Broken looks like:** Fewer than 11 rows, no score range column, or the Rank-IC row is missing.

5. Click the column header for the 20-day forward-return column in the by-phase-label table (it should have a sort arrow or change cursor on hover)
   - **Expect:** The five phase rows reorder. The row that was first before clicking is now in a different position. No page reload occurs (URL stays the same). Any "NA" cells remain at the bottom of the column.
   - **Broken looks like:** Row order does not change, page reloads, or "NA" cells move to the top.

6. In the browser address bar, append `?asof=2024-06-01` to the current URL and press Enter (full URL: `http://localhost:3255/research/phase-severity-lab?asof=2024-06-01`)
   - **Expect:** The page reloads. The N= values on the chips in both tables decrease compared to the values you saw in steps 3–4 (fewer observations because only data up to 2024-06-01 is included). No new date picker control appears on the page.
   - **Broken looks like:** N= values are unchanged, an extra date input field appears, or the page errors on the `asof` parameter.

7. Ctrl+click (Cmd+click on Mac) any N= chip in the by-phase-label table — for example, the chip in the "Bear" row under the 20-day horizon column — to open it in a new tab
   - **Expect:** A new browser tab opens at a URL starting with `http://localhost:3255/research/samples`. The Samples page loads successfully. The "Total observations" figure at the top of the Samples page matches exactly the number shown on the chip you clicked. The cohort description references the "Bear" phase and/or the 20-day horizon.
   - **Broken looks like:** New tab shows 404, Samples page shows a different observation count, or cohort description says "Setup & Pattern Lab" or another wrong label.

8. Navigate back to `http://localhost:3255/research` and click the "Regime Lab" tile
   - **Expect:** The Regime Lab page loads at `/research/regime-lab` with its own tables visible. The Research hub tile click still works (regression check — this tile was present before iter-54).
   - **Broken looks like:** Regime Lab tile is missing, navigation goes to the wrong page, or the Regime Lab page errors.

9. From the Regime Lab page, Ctrl+click any N= chip to open it in a new tab; check the Samples page cohort heading
   - **Expect:** The Samples page cohort heading says "Regime Lab" (or clearly references the Regime Lab), not "Setup & Pattern Lab".
   - **Broken looks like:** Cohort heading says "Setup & Pattern Lab" — this is the regression fixed in iter-54 and should no longer occur.

---

## What "Working Correctly" Looks Like

- The Research hub shows the "Market Phase & Severity Lab" tile alongside all existing lab tiles — nothing is missing or duplicated.
- The phase-severity-lab page shows two populated tables: five phase rows and eleven decile rows (Rank-IC + D1–D10), with numeric or "NA" cells and a survivorship-bias caveat in the header.
- Sorting any numeric column visibly reorders the rows; NA cells always stay at the bottom.
- Appending `?asof=<date>` to the URL reduces N= values across all chips — no second date picker appears.
- N= chips open count-coherent Samples cohorts in new tabs (the total observations match the chip number exactly).
- Regime Lab N= chip cohorts are labelled "Regime Lab" on the Samples page (not a generic label).

## Common Issues

- **"Backend unavailable" banner or endless spinner:** Check that the backend is running (`curl http://localhost:8000/health`). If it is not running, start it with `./scripts/dev.sh` or the equivalent backend start command.
- **N= chip opens Samples with wrong count:** This indicates a data consistency issue. Verify the backend is using the same `as_of` date as the page. If you appended `?asof=2024-06-01`, confirm the Samples URL also carries that date.
- **Sort does not change row order:** The by-phase-label table only has five rows, so all-numeric sorts may appear unchanged if all values are distinct but the difference is not visually obvious. Try clicking a column where you can see "NA" cells — they should always move to the bottom.
- **Regime Lab cohort label still says "Setup & Pattern Lab":** Hard-refresh the browser (Ctrl+Shift+R / Cmd+Shift+R) to clear any cached frontend bundle from a previous iteration. If the issue persists after refresh, the fix in iter-54 may not have been applied correctly.
