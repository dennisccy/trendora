# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-33 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-33
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8835` (check: `curl http://localhost:8835/health` should return 200)
- The database has been warmed up — at least one full scan run is available (the app shows data, not just a loading spinner on the Data Manager page)

---

## Verification Steps

1. Navigate to `http://localhost:3835/data`
   - **Expect:** Page loads with a coverage block visible at the top. You should see TWO universe metrics side by side: one labeled "Universe (as of date)" showing a number around 120 with a date annotation, and one labeled "Candidate universe" showing a number equal to or slightly higher. If you see only a single static "Universe: 122" label with no date, the point-in-time migration did not land.

2. Scroll down on the same `/data` page until you find a panel labeled "Universe Diagnostic" (or similar)
   - **Expect:** The panel shows an "Admitted" count greater than 0 and three exclusion reason rows: "below history", "below price", and "below liquidity" — each with a numeric count and a threshold value (e.g., "min price: $5.00"). If the panel is missing entirely or shows only a spinner, the diagnostic component is not rendering.

3. Continue scrolling down on `/data` until you find a panel labeled "Membership Timeline" (or similar)
   - **Expect:** An SVG chart with a step-function line is visible inside the panel — the line starts near 0 on the left and rises toward ~120 on the right. Below the chart, a per-date table lists dates with columns for size, entries, and exits. Three plain-English labels are visible in or near the panel: one mentioning "survivorship", one mentioning "warm-up", and one mentioning "universe-relative" breadth. If the chart area is blank or a white rectangle, the step-function rendering is broken.

4. On the same `/data` page, scroll to the "Extend history backward" section and click the "Extend history backward" button
   - **Expect:** A confirmation modal (overlay dialog) appears on screen. The modal body contains a survivorship caveat mentioning "current-constituent" or "survivorship bias". The modal has a "Confirm" (or "Proceed") button and a "Cancel" button. Do NOT confirm yet — just verify the modal opened correctly. Then click "Cancel" to dismiss.

5. Use the global as-of date control (the "◀" left-arrow button in the top bar or date panel) to step the date backward to approximately 2021-01-04 (use multiple presses or the date picker if available)
   - **Expect:** On the `/data` coverage block, the "Universe (as of date)" count drops to 0 (or a very small number near 0). The "Universe Diagnostic" panel renders an explicit "empty universe" or "warm-up" banner — NOT a spinner, NOT an error, NOT a positive admitted count. If you see a positive admitted count at this early date, the warm-up gate is not applied.

6. While still on as-of 2021-01-04, navigate to `http://localhost:3835/stocks`
   - **Expect:** The stock leaderboard shows zero rows OR an empty-state message that explicitly mentions "warm-up" and references the Data Manager diagnostic. The message must NOT read generic phrases like "No stocks found" without further context. If you see 120 rows at this early date, the point-in-time resolver is not connected.

7. Step the global as-of date forward to 2022-03-01 (using the "▶" right-arrow button or date picker)
   - **Expect:** The stock leaderboard at `/stocks` now shows more than 100 rows. The row count is visibly much larger than at 2021-01-04. This confirms the dynamic universe correctly grows as history accumulates.

8. Navigate to `http://localhost:3835/themes` (while still at as-of 2022-03-01), note any theme's member count, then step the date back to 2021-03-01 and observe the same themes
   - **Expect:** Theme member counts at 2021-03-01 are smaller than at 2022-03-01 (some may show 0). If every theme shows the same count regardless of the date, the membership is not point-in-time.

9. Reset the as-of date to the latest available date (click the "▶" button until it stops, or select today's date). Navigate to `http://localhost:3835/stocks`, find NVDA in the leaderboard, and note its score and bucket. Then click NVDA to open its detail page.
   - **Expect:** Every score visible on NVDA's detail page exactly matches what was shown on the leaderboard row. The bucket letter (A–E) also matches. If any value differs between leaderboard and detail, the single-source-of-truth invariant has regressed.

10. Navigate to `http://localhost:3835/` (the Dashboard)
    - **Expect:** All existing dashboard panels load normally — market regime chart, sector leaders, theme leaders, and stock leadership panels are all visible and populated with data. No blank panels or error banners. This confirms that the new universe resolver changes did not break the dashboard.

---

## What "Working Correctly" Looks Like

- The Data Manager coverage block shows TWO labeled metrics ("Universe (as of date)" and "Candidate universe") with the resolved-count smaller than or equal to the candidate count
- Stepping to an early date (2021-01-04) drops the universe count to near 0 and the stock leaderboard shows an honest warm-up message — not 120 rows of data
- The Membership Timeline panel on `/data` has a visible step-function chart (not a blank frame) and three readable honesty labels

## Common Issues

- **Coverage block shows old static "122" count**: Backend universe_count migration is incomplete — the as-of-date resolver is not connected to the data endpoint
- **Universe Diagnostic panel missing entirely**: The frontend component did not deploy; check that `apps/frontend/app/data/page.tsx` was updated
- **Membership Timeline chart is blank / white rectangle**: The SVG step-function rendering failed; may be a data shape mismatch between the API payload and the frontend chart component
- **Stock leaderboard shows 120 rows at 2021-01-04**: The `score_stocks` function was not repointed to the resolver — it is still iterating the static symbol list
- **Confirm modal does not appear on "Extend history backward" click**: The backward-history panel confirm gate is not wired; check the button's onClick handler in the frontend
- **Backend unavailable**: Run `curl http://localhost:8835/health` — if it fails, the backend is not running; start it with the project's backend start command (see CLAUDE.md)
