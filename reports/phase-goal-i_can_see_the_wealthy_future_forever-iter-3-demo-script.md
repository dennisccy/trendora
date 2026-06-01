# Demo Script — goal-i_can_see_the_wealthy_future_forever-iter-3

**Mode:** record
**Date:** 2026-06-01
**Frontend URL:** http://localhost:3835
**Iteration:** 3

## Highlights

### Step 01 — Open Trendora

- **Narration:** We start on Trendora's daily dashboard — the after-the-close view of the market. A brand-new entry, Data Manager, now sits at the very bottom of the left sidebar.
- **Action:** Navigate to /
- **Point out:** The 'Data Manager' item (database icon) at the bottom of the left navigation — present on every page.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-3/step-01.png

### Step 02 — Open the Data Manager  [NEW]

- **Narration:** Clicking Data Manager opens a new page that shows exactly how much history the system holds — the price-date range, the number of symbols and trading days, how many saved snapshot dates exist, and how many days still need one.
- **Action:** Click the "Data Manager" link
- **Point out:** The 'Dataset coverage' panel with real numbers (about 158 symbols, thousands of trading days) and the amber 'Backfill gaps' count with its gap range — the days that have prices but no snapshot yet.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-3/step-02.png

### Step 03 — Start a backfill job  [NEW]

- **Narration:** The job form already comes pre-filled with a range of missing days. We keep the kind as 'Backfill snapshots' and press Start — and the job runs live, building one immutable snapshot per day, its progress bar advancing about once a second until it finishes with an 'ok' summary in the run history.
- **Action:** Click the "Start" button
- **Point out:** The Start button now reads 'Job running…' and the 'Snapshots backfilled' bar climbs, with its snapshot and forward-return counts rising in real time.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-3/step-03.png

### Step 04 — New dates appear — no reload  [NEW]

- **Narration:** As the job finishes, the snapshot dates it just built become selectable in the single global date control at the top of the app — without reloading the page. We pick one of those backfilled days, 2021-01-13.
- **Action:** Type "2021-01-13" into the "View as-of date" field
- **Point out:** The top-bar control switches to 'Viewing as-of 2021-01-13 (historical)' — a date that had no snapshot moments ago is now a first-class choice.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-3/step-04.png

### Step 05 — It resolves across the product

- **Narration:** That backfilled date now drives the whole dashboard. Opening the Stocks leaderboard shows a complete, ranked scorecard for that exact day — real recorded data, never a placeholder.
- **Action:** Click the "Stocks" link
- **Point out:** The Stocks leaderboard rendered 'as of 2021-01-13' with a full ranked table — the one date control carried straight over from the Data Manager.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-3/step-05.png

### Step 09 — An honest failure  [NEW]

- **Narration:** The live provider needs an API key this environment doesn't have — so the job fails out in the open. It lists the per-symbol errors and states plainly that nothing was fabricated: no invented prices, no fake 'success'. That refusal to make up data is exactly the point.
- **Action:** Click the "Start" button
- **Point out:** A red 'failed' status with the per-symbol error list and the '(no data fabricated)' note — and not a single new snapshot claimed for the failed symbols.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-3/step-09.png

## Full tour (text only)

### Step 06 — The evidence base grows

- **Narration:** Because every backfilled day adds more forward-tested history, the System Health page stands on a larger sample over time — more evidence behind every claim the product makes about its own track record.
- **Action:** Click the "System Health" link
- **Point out:** The forward-test sample size (n) reflects the enlarged dataset that the Data Manager just helped grow.

### Step 07 — Back to the Data Manager

- **Narration:** Back on the Data Manager, we'll show the other side of the story — what the product does when live market data simply isn't available.
- **Action:** Click the "Data Manager" link
- **Point out:** The job form, ready for a new run.

### Step 08 — Choose a live fetch  [NEW]

- **Narration:** This time we switch the job kind to 'Fetch EOD prices', which reaches out to a live market-data provider instead of using the built-in offline seed.
- **Action:** Type "Fetch EOD prices" into the "Job kind" field
- **Point out:** The Job kind control now set to 'Fetch EOD prices'.
