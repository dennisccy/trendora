# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8835`
- No login required — the app is open access
- Seed data must be loaded (covers 2021–2026 including the 2022 bear market); if the Dashboard shows blank cards, confirm the backend started cleanly by checking `http://localhost:8835/api/health`

---

## Verification Steps

1. Open `http://localhost:3835/` in your browser
   - **Expect:** The Dashboard loads. A "Market Phase & Severity" card appears below the "Major Indexes & Regime" card. The new card header shows two colored badges: a phase label (e.g., "Expansion") in green and a P(bear) value (e.g., "P(bear) 0.05") in green. If you see only the "Major Indexes & Regime" card and nothing below it, the new card is missing — this is a failure.

2. Scroll down to the "Market Phase & Severity" card and read the card body
   - **Expect:** A numeric severity score in the format "X.XX / 100 severity" (e.g., "28.75 / 100 severity") is visible. Below it, a table lists exactly five rows: "Drawdown depth", "Time underwater", "Market regime (stored)", "Breadth below 200-DMA", and "VIX stress gate" — each with a numeric Value and a numeric Contribution. If all five rows are absent or if the only thing visible is a blank white area, the breakdown is not rendering.

3. Still on the "Market Phase & Severity" card, scroll to the very bottom of the card body
   - **Expect:** A row labeled "Filter observations · drives P(bear)" appears with a series of date-labeled chips. There should be multiple chips visible. Hover over any chip to see a tooltip with a stress reading and a per-date P(bear) value. If the row is absent entirely, the observation vector is missing.

4. Use the global as-of date navigation control (the arrow buttons or date input at the top of the Dashboard) to navigate to `2022-10-07`
   - **Expect:** The URL changes to include `?asof=2022-10-07`. The "Market Phase & Severity" card briefly shows a gray skeleton, then updates. The phase badge in the card header now shows "Bear" in red. The severity score rises to 70 or higher. The P(bear) badge changes to red and shows a value near "P(bear) 1.00". If the card still shows "Expansion" or a low severity score, the as-of repoint is not working.

5. With the date still at 2022-10-07, navigate the global as-of forward to `2024-12-31` (use the same date controls or type the date directly)
   - **Expect:** The URL changes to `?asof=2024-12-31`. The "Market Phase & Severity" card updates again. The phase badge returns to green and shows "Expansion" (or "Recovery"). The severity score drops well below the 2022 value. The P(bear) badge returns to green with a near-zero value. This confirms the card correctly time-travels with the global as-of.

6. Press F5 to refresh the page (the URL still contains `?asof=2024-12-31`)
   - **Expect:** After reload, the "Market Phase & Severity" card still shows the same phase label and the same severity score as before the refresh. The URL still contains `?asof=2024-12-31`. This confirms the result is deterministic and the as-of date survives a page reload.

7. Scroll back to the top and confirm the "Major Indexes & Regime" card above the new card
   - **Expect:** The "Major Indexes & Regime" card shows its normal index price charts and regime label (e.g., "Risk-On"). It has not been visually altered by this iteration — same layout, same content, no new controls inside it.

8. Navigate to `http://localhost:3835/stocks`
   - **Expect:** The stocks leaderboard page loads with at least one stock row visible. Stock scores or setups are displayed. Clicking any ticker link opens the stock detail page without a JavaScript error. This confirms no regression in the core stocks surface.

---

## What "Working Correctly" Looks Like

- The Dashboard has two adjacent information cards: "Major Indexes & Regime" (unchanged) followed by "Market Phase & Severity" (new)
- At any recent date, the new card shows a green "Expansion" or "Recovery" badge, a severity score below 30, and a P(bear) below 0.2
- At `2022-10-07`, the new card shows a red "Bear" badge, a severity score above 70, and a P(bear) near 1.00
- Stepping the date forward or backward updates the card content automatically — no page reload needed

## Common Issues

- **"Market Phase & Severity" card is absent:** The frontend component was not mounted. Confirm the frontend built correctly; check the browser console for import errors.
- **Card shows "Market phase unavailable" alert:** The backend is not running or not reachable. Confirm the backend is up by visiting `http://localhost:8835/api/health` in a browser tab — it should return a JSON response.
- **Card body shows skeleton that never resolves:** The `/api/market-phase` request is hanging or returning a non-200 status. Open Chrome DevTools (F12), go to the Network tab, filter by "market-phase", and check the response status and body.
- **2022-10-07 still shows "Expansion":** The as-of parameter is not being passed to the backend. Check the Network tab request URL — it should include `?as_of=2022-10-07`.
- **Severity score shows "NA" on a recent 2024 date:** The backend may not have enough stored snapshot rows for the selected date. Confirm the seed data is loaded by checking `http://localhost:8835/api/stocks` — if that returns empty, the seed is missing.
