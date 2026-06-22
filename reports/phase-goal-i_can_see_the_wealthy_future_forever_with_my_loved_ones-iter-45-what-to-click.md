# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8835` (confirm by visiting `http://localhost:8835/health` — it should return `{"status":"ok"}` or similar)
- Seed data loaded (the backend has committed 2021–2026 history — no action needed if the backend started cleanly)

---

## Verification Steps

1. Open `http://localhost:3835/research` in your browser
   - **Expect:** A card grid of seven named lab cards appears. No heavy study matrix or analysis table is shown on this page — just card links. The page loads in under 5 seconds.
   - **Broken looks like:** An old-style page showing analysis tables or charts directly (the pre-split monolith), a 404 error, or a blank white screen.

2. Click the card for the severity-velocity study (labelled "Severity-velocity", "Severity Velocity × Regime", or similar) on the hub
   - **Expect:** Browser navigates to `http://localhost:3835/research/severity-velocity`. A matrix table with 3 rows (Risk-on / Neutral / Risk-off) and 3 columns (Rising / Flat / Falling) loads. The page shows a horizon selector and a verdict card section below the matrix.
   - **Broken looks like:** A 404 page, a spinner that never resolves, or no matrix visible after 30 seconds.

3. On the `/research/severity-velocity` page, click "5d" in the horizon selector (or any option different from the current selection)
   - **Expect:** The numeric values (mean return, win-rate) in the matrix cells update within 2 seconds to reflect the 5-day forward-return horizon. No page reload occurs.
   - **Broken looks like:** Values do not change, the page goes blank, or an error message appears.

4. Scroll down on the `/research/severity-velocity` page to find the verdict card
   - **Expect:** The verdict card text contains "NOT supported" and explicitly mentions that rising stress under a red/Risk-off regime preceded a bounce. The words "survivorship", "bull-dominated", and "underpowered-for-crashes" (or close variants) appear in the card.
   - **Broken looks like:** The verdict says the hypothesis IS supported, the card is blank, or any of the three caveats is missing.

5. Click any N= chip in the severity-velocity matrix that shows a non-zero count (e.g., "N=32")
   - **Expect:** A new browser tab opens at a URL beginning with `http://localhost:3835/research/samples`. The Samples page in the new tab shows a human-readable description (mentioning the regime family and velocity sign, not a raw JSON string) and the total sample count matches the number shown on the N= chip you clicked.
   - **Broken looks like:** No new tab opens, the new tab shows a 4xx error, the sample count differs from the chip label, or the description reads as raw JSON.

6. Navigate back to `http://localhost:3835/research` (click your browser's back button or retype the URL)
   - **Expect:** The hub card grid reloads. Click the "Event Study" card. The Event Study lab loads at `http://localhost:3835/research/event-study` with its analysis table and N= chips visible.
   - **Broken looks like:** The event-study page shows a 404, a blank page, or the same content as a different lab.

7. While on `http://localhost:3835/research/event-study`, look at the left sidebar
   - **Expect:** The "Research" sidebar entry is highlighted or shown in an active state (e.g., bold, colored border, or filled background). No other sidebar item is highlighted.
   - **Broken looks like:** The sidebar shows no active Research entry, or the dashboard/stocks entry is highlighted instead.

8. Navigate to `http://localhost:3835/research/regime-setup-pattern`
   - **Expect:** The Regime × Setup × Pattern matrix table loads with numeric values (mean return, win-rate) and N= chips. Figures should match what this table showed before this iteration's changes.
   - **Broken looks like:** A 404 error, a blank page, or an empty table with no data rows.

9. Navigate to `http://localhost:3835` (the main dashboard)
   - **Expect:** Dashboard loads with at least one chart showing data and the current regime label (Risk-on / Neutral / Risk-off) visible somewhere on the page.
   - **Broken looks like:** A blank screen, "Checking backend…" that never resolves, or no charts rendered.

---

## What "Working Correctly" Looks Like

- The `/research` hub shows exactly seven lab cards with names and descriptions — no inline analysis content
- The `/research/severity-velocity` matrix has three rows and three columns; the verdict card explicitly says "NOT supported" with all three caveats
- An N= chip click always opens a new `/research/samples` tab whose total count matches the chip label
- All relocated labs (`/research/factor-lab`, `/research/event-study`, `/research/regime-setup-pattern`, `/research/downtrend-opportunity`, `/research/recovery-turn-edge`, `/research/factor-combination`) load independently without 404 errors
- The "Research" sidebar entry stays highlighted on any `/research/*` sub-route

## Common Issues

- **Hub shows "Checking backend…" indefinitely:** The backend is not running. Check by visiting `http://localhost:8835/health` in your browser — if that fails, the backend process needs to be restarted.
- **Severity-velocity page loads but matrix cells all show "NA":** The backend has no seed data for the required date range. Confirm the backend's seed covers 2021–2026 data by checking with whoever manages the backend setup.
- **N= chip opens a tab with a 422 or 404 error:** The cohort URL parameters did not include a valid `as_of` date. Navigate to the severity-velocity study without an `?asof` query parameter and try again with the default all-history view.
- **Verdict card is missing or blank:** The severity-velocity page loaded but failed to retrieve the verdict text from the backend. Check the browser console for a failed API call to `/api/research/severity-velocity`.
