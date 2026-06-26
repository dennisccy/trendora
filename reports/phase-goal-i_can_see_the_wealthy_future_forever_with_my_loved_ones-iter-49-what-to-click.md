# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- App started with `./scripts/dev.sh` (both backend and frontend must be running)
- Frontend accessible at `http://localhost:3255`
- No login required
- Note the LAN-IP URL printed by `./scripts/dev.sh` if you want to verify step 8 (the readiness-badge fix)

---

## Verification Steps

1. Navigate to `http://localhost:3255/stocks`
   - **Expect:** The Stocks leaderboard table loads with stock rows. A column header reading "Proximity to 52w high" appears immediately to the right of the "Risk" column header. Each row shows either a percentage (e.g., `-1.24%`) or a muted "NA" in that column.
   - **Broken if:** No "Proximity to 52w high" column header is visible, or the column appears in the wrong position (not directly after "Risk").

2. Click the "Proximity to 52w high" column header
   - **Expect:** The table rows reorder. A sort-direction arrow (↑ or ↓) appears on the "Proximity to 52w high" header. No other column header shows a sort arrow. The ticker symbol in the first row changes from its pre-click position.
   - **Broken if:** The table does not reorder, or no arrow appears, or the page shows a JavaScript error.

3. Click the "Proximity to 52w high" column header a second time
   - **Expect:** The sort order reverses. The arrow indicator on the header flips direction. The ticker that was in the first row after step 2 is no longer first.
   - **Broken if:** Order does not change, or a second click breaks the table layout.

4. Scroll to the bottom of the table and check the last several rows in the "Proximity to 52w high" column
   - **Expect:** Any rows showing "NA" appear at the very bottom. All rows with numeric percentage values are above them. The "NA" text is visually muted/grayed out compared to the numeric values.
   - **Broken if:** "NA" rows appear anywhere except the bottom, or "NA" appears in the same color/weight as numeric values.

5. Hover the mouse over the small info icon (ⓘ) on the "Proximity to 52w high" column header and hold for 2 seconds
   - **Expect:** A tooltip appears containing a plain-language definition of "Proximity to 52w high" from the methodology glossary (e.g., an explanation involving distance below the 52-week peak or percentage from high).
   - **Broken if:** No tooltip appears, or the tooltip is empty, says "undefined", or says "term not found".

6. In the leaderboard, find a row where "Proximity to 52w high" shows a percentage (not "NA"). Note the ticker and the exact value (e.g., "NVDA" shows "-3.10%"). Click that ticker link.
   - **Expect:** The Stock Detail page for that ticker loads. In the "Leadership" or "Leadership Score" section, the component row labeled "Proximity to 52w high" shows the same percentage you noted (e.g., "-3.10%"), not an internal rank like "pctl 45".
   - **Broken if:** The detail page shows "pctl XX" or any opaque internal rank instead of a matching percentage, or the values differ between the leaderboard and the breakdown.

7. Navigate to `http://localhost:3255` (the Dashboard home page)
   - **Expect:** The Dashboard loads with content (regime indicator, sector or theme cards). The readiness badge in the top bar shows "Ready" or "Initializing… n/m". No "Backend unavailable" banner appears.
   - **Broken if:** Dashboard shows "Backend unavailable" or is blank — this indicates the API_BASE change broke localhost data loading.

8. Open a new browser tab and navigate to the LAN-IP URL printed by `./scripts/dev.sh` (e.g., `http://192.168.1.68:3255`)
   - **Expect:** The page loads. Within 15 seconds the readiness badge transitions from "Initializing… history n/m" to "Ready". The badge never shows "Backend unavailable".
   - **Broken if:** The badge remains permanently on "Backend unavailable" — this means the LAN-IP CORS/host fix did not apply correctly.

---

## What "Working Correctly" Looks Like

- The Stocks leaderboard at `/stocks` has a "Proximity to 52w high" column directly after "Risk", with percentage values or muted "NA" per row, and clicking the header reorders the table
- A stock's "Proximity to 52w high" value on its Detail page matches what the leaderboard shows for that ticker — a percentage, not an internal rank
- The readiness badge in the top bar shows "Ready" both at `localhost` and at the LAN-IP address when the backend is running

## Common Issues

- **"Proximity to 52w high" column missing:** Confirm you are at `/stocks` and the backend is running; hard-refresh the page (Ctrl+Shift+R) to clear any cached bundle
- **Badge shows "Backend unavailable" at localhost:** Backend may not be fully started; wait 15 seconds and refresh; if still broken, run `curl http://localhost:8000/api/health` in the terminal to check whether the backend process is up
- **Badge shows "Backend unavailable" at LAN-IP but works at localhost:** The API_BASE host-aware fix did not apply; check that the frontend was rebuilt after the change (`./scripts/dev.sh` should rebuild on start)
- **Detail page shows "pctl XX" instead of a percentage:** The `component-breakdown.tsx` change did not deploy; hard-refresh the Stock Detail page
