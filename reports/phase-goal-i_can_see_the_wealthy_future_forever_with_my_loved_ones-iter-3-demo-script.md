# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3

**Mode:** record
**Date:** 2026-06-11
**Frontend URL:** http://localhost:3835
**Iteration:** 3

## Highlights

### Step 01 — Stocks leaderboard

- **Narration:** The stocks leaderboard shows all 122 universe members ranked by their composite score, with Leadership, Entry Quality, and Risk grades visible at a glance. This is the daily starting point for finding the best-positioned equities.
- **Action:** Navigate to /stocks
- **Point out:** NVDA appears with three numeric scores and a letter bucket (E), confirming the scoring engine is live and producing results.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3/step-01.png

### Step 02 — NVDA detail — explainable scores

- **Narration:** Clicking any stock opens the detail page with a full breakdown of how each score was built — component by component — along with a price chart and an actionable invalidation level.
- **Action:** Navigate to /stocks/NVDA
- **Point out:** The Leadership, Entry Quality, and Risk scores shown here are identical to the list page values (43.14 / 54.05 / 35.80), confirming a single source of truth with no recomputation.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3/step-02.png

### Step 03 — Data Manager — import and backfill

- **Narration:** The Data Manager is where you grow the price history used for scoring. Start a live fetch job or run a backfill over existing seed data — both run asynchronously with a live progress counter.
- **Action:** Navigate to /data
- **Point out:** The page is fully interactive with no loading spinner. The import form and run history are both visible, showing the backend is healthy and responding.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3/step-03.png

### Step 04 — Rate-limited fetch — resumable checkpoint

- **Narration:** When a live fetch hits a provider rate limit mid-run, the job pauses gracefully in an amber resumable state rather than failing. The exact chunk where it paused is saved, so resuming picks up exactly where the work stopped — no data is re-fetched or duplicated.
- **Action:** Navigate to /data
- **Point out:** The job card shows 'rate-limited — resumable' in amber with a message describing the saved checkpoint and a Resume button. The status is never 'failed'.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3/step-04.png
