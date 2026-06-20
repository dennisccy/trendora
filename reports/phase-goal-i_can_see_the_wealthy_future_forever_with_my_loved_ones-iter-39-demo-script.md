# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39

**Mode:** record
**Date:** 2026-06-20
**Frontend URL:** http://localhost:3835
**Iteration:** 39

## Highlights

### Step 01 — Dashboard loads with market data

- **Narration:** The Dashboard opens and immediately shows at-a-glance market figures near the top — regime label, phase, and severity score — all drawn from live data without any manual refresh.
- **Action:** Navigate to /
- **Point out:** Look for a regime label such as Bull or Bear and a numeric severity score between 0 and 100 near the top of the page.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39/step-01.png

### Step 02 — Market Phase & Severity at-a-glance figure  [NEW]

- **Narration:** Just below the regime summary sits a compact Market Phase and Severity figure that shows the current phase label alongside a 0–100 severity score — both pulled from the same backend data feed that was previously broken at the live date.
- **Action:** Navigate to /
- **Point out:** A phase label (Recovery, Distribution, Accumulation, or similar) and a number in the 0–100 range should both be visible and non-blank.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39/step-02.png

### Step 03 — Cross-view chart — bottom pane now populated  [NEW]

- **Narration:** Scrolling down reveals the two-pane cross-view chart. The bottom pane, which was blank before this fix, now displays color-coded phase bands across the full historical time axis with the severity and bear-probability lines drawn over them.
- **Action:** Navigate to /
- **Point out:** The bottom pane should show colored rectangular bands — each color representing a market phase period — with at least one line overlay. A 0–100 scale appears on its vertical axis.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39/step-03.png

### Step 04 — Top pane vs bottom pane — two distinct lenses  [NEW]

- **Narration:** The top pane shows normalized index price paths as plain lines on a neutral background, while the bottom pane shows the phase and severity lens with colored bands. Together they let you compare market momentum and market regime in one synchronized view.
- **Action:** Navigate to /
- **Point out:** The top pane has no colored background fills; the bottom pane does. The two panes use different y-axis scales and different visual styles.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39/step-04.png

### Step 05 — As-of date change — chart and figures update together

- **Narration:** Picking a different as-of date from the date selector near the top of the Dashboard causes both the at-a-glance figures and the cross-view chart to re-render for that date, including the bottom pane's phase bands and the as-of marker line.
- **Action:** Navigate to /?asof=2026-06-10
- **Point out:** After selecting 2026-06-10 the date picker should reflect that date and the cross-view chart bottom pane should remain populated with phase bands, not go blank.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39/step-05.png

### Step 06 — Early historical date — bottom pane honestly empty

- **Narration:** When you travel back to a very early date before market-phase history exists, the bottom pane shows an empty canvas rather than fabricated data — honest about what it does not yet know.
- **Action:** Navigate to /?asof=2010-01-15
- **Point out:** At 2010-01-15 the bottom pane should be visually empty with no colored bands and no lines, but no error message either.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39/step-06.png

### Step 07 — Return to live date — bottom pane repopulates  [NEW]

- **Narration:** Switching back to today's date confirms that the fix is persistent: the bottom pane repopulates with its full phase-band history and the at-a-glance figures return their live values.
- **Action:** Navigate to /
- **Point out:** The colored phase bands and the severity line should reappear in the bottom pane, and the Market Phase and Severity figure should show a non-blank label and score.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39/step-07.png

### Step 08 — Stocks page — other sections unaffected

- **Narration:** Navigating to the Stocks leaderboard confirms that the cache fix is surgical and left the rest of the product working as expected.
- **Action:** Click the "Stocks" link
- **Point out:** The Stocks page should load a list of tickers with scores — no blank screen or spinner that never clears.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39/step-08.png
