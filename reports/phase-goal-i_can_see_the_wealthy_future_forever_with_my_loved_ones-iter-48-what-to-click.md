# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48
**Time required:** ~5–7 minutes (Factor Lab cold compute takes 50–120 s)
**Written by:** ui-test-designer

---

## Prerequisites

- Backend running at `http://localhost:8835` — confirm it is ready by opening `http://localhost:8835/health` in your browser; wait until the response shows "ready" or "ok" (not "starting" or a connection error). The backend warm-up can take 1–2 minutes after a fresh start.
- Frontend running at `http://localhost:3835`
- No other heavy requests running against the backend (close any other tabs that might be computing a research lab)

---

## Verification Steps

1. Navigate to `http://localhost:3835/research/factor-lab`
   - **Expect:** The Factor Lab page loads showing a factor dropdown selector and a horizon dropdown selector. No "Backend unavailable" error banner appears. (If you see a completely blank page, the frontend may not be running — check that port 3835 is serving.)

2. Open the factor dropdown and select **"RS 3m"**, then open the horizon dropdown and select **"20d"**
   - **Expect:** The page begins computing — a loading skeleton or spinner appears within 5 seconds of making the selections. This is normal; the cold compute takes 50–120 seconds on the full live dataset.

3. Wait up to 120 seconds for the decile table to load
   - **Expect:** A table with exactly 10 rows labelled **D1 through D10** appears. Each row shows a numeric mean return (e.g. "1.23%" or "−0.45%") and a sample count (e.g. "N=312"). A **rank-IC** statistic (labelled "Rank IC" or "IC") appears above or below the table showing a numeric value such as "0.006" or "−0.012".
   - **Broken looks like:** The text "Backend unavailable — No figures are shown rather than fabricated values" remains on screen after 120 seconds, or the table rows show "NaN" or blank cells where return values should be.

4. Click the **"N="** chip on any decile row that shows a non-zero count (e.g. click "N=312" on the D1 row)
   - **Expect:** A new browser tab opens at `http://localhost:3835/research/samples` (URL will include query parameters). The samples page loads and displays a total observation count that matches the number shown in the chip you clicked (e.g. total = 312).
   - **Broken looks like:** The new tab shows an error page, a blank page, or a total count that differs from the chip value.

5. Navigate to `http://localhost:3835/research/setup-pattern` (Event Study)
   - **Expect:** The Event Study page loads and displays numeric event-study cells (mean return, risk-adjusted return, and sample count per cell). No "Backend unavailable" error banner appears. This page is cached and should load within 10–15 seconds.
   - **Broken looks like:** The page shows the "Backend unavailable" banner, or all cells show blank or "NaN" values.

6. Navigate to `http://localhost:3835/research/factor-combination` (Factor Combination)
   - **Expect:** The Factor Combination page loads. Select any two available factors and wait up to 60 seconds. A combined cohort table appears showing at least one numeric mean return and sample count. No error banner appears.
   - **Broken looks like:** The "Backend unavailable" banner appears, or the page stays on a loading skeleton past 60 seconds.

---

## What "Working Correctly" Looks Like

- The Factor Lab decile table shows 10 rows (D1–D10), each with real numeric return values and non-zero sample counts — not a blank table, not an error banner, and not "NaN"
- The rank-IC statistic is a specific number (positive or negative), not blank or "Loading…"
- Clicking an N= chip opens a matching samples page in a new tab
- The Event Study and Factor Combination pages also load successfully with real figures — this confirms all five heavy research labs are operating reliably after this fix

## Common Issues

- **"Backend unavailable" banner on Factor Lab after 120 s:** The backend may have crashed (check the terminal running uvicorn for a MemoryError log line). Restart the backend, wait for health "ready", then retry — allow one full 120-second wait before concluding broken.
- **Factor Lab spinner never resolves (stuck past 120 s):** Check that no other browser tabs are also requesting heavy research endpoints at the same time. Close them, wait 30 seconds, then reload this tab.
- **Samples tab shows wrong count:** Verify the factor and horizon selections in Factor Lab match what you expect — the N= count is specific to the factor/horizon/decile combination you selected.
- **Event Study or Factor Combination shows error while Factor Lab works:** These labs should also be working after this fix. If they show errors, the backend warm-up may not have completed — wait 60 seconds and reload.
