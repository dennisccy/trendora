# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37

**Mode:** record
**Date:** 2026-06-19
**Frontend URL:** http://localhost:3835
**Iteration:** 37

## Highlights

### Step 01 — Dashboard — market regime at a glance

- **Narration:** The dashboard loads instantly, showing the current market regime and a composite score that tells you at a glance whether conditions favour active positioning or caution.
- **Action:** Navigate to /
- **Point out:** The regime label (Risk-on) and the composite score (73.44) with its component breakdown — all rendered without any skeleton delay.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37/step-01.png

### Step 02 — Stock Leaderboard — ranked by composite score

- **Narration:** The stock leaderboard shows every universe member ranked by their three explainable scores. Top names like NVDA, AAPL, and SPY appear right away from the persisted snapshot — no waiting for live recomputation.
- **Action:** Navigate to /stocks
- **Point out:** Ticker rows with bucket labels and scores populate within a few seconds. A single as-of date control sits in the toolbar — exactly one, no duplicates.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37/step-02.png

### Step 03 — NVDA detail — three explainable scores

- **Narration:** Clicking into any ticker reveals the three scores that drove its ranking: Leadership, Entry, and Risk. Every number shown here is byte-identical to what the leaderboard displayed — a single source of truth, never recomputed on this page.
- **Action:** Navigate to /stocks/NVDA
- **Point out:** The NVDA heading, its bucket label, numeric score values, and setup indicator all appear without a 404 or blank field.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37/step-03.png

### Step 04 — Data Manager — reliable page hydration (iter-37 fix)  [NEW]

- **Narration:** This iteration restored the bar-cache load-once invariant that a previous optimisation had silently broken. The /data page now hydrates cleanly within 30 seconds on a single load, without exhausting the database connection pool.
- **Action:** Navigate to /data
- **Point out:** The Data Manager heading and the coverage-diagnostic admitted count (544) are both visible — no persistent 'Checking backend…' skeleton. This is the direct evidence of the iter-37 fix.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37/step-04.png

### Step 05 — Coverage diagnostic — admitted and exclusion counts

- **Narration:** The coverage-diagnostic section shows exactly how many symbols made it into the universe for the current as-of date, and why the rest were excluded — not enough history, too low a price, or below minimum daily volume.
- **Action:** Navigate to /data
- **Point out:** ADMITTED shows 544 members (of 548 candidates). The three exclusion-reason fields — BELOW MIN HISTORY (1), BELOW MIN PRICE (2), and BELOW ADV — each show real integers, not dashes or NaN.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37/step-05.png
