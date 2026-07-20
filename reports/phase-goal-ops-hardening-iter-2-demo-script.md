# Demo Script — goal-ops-hardening-iter-2

**Mode:** record
**Date:** 2026-07-20
**Frontend URL:** http://localhost:3255
**Iteration:** 2

## Highlights

### Step 01 — Tour the dashboard

- **Narration:** Let's start where every visit begins — the dashboard, which sums up today's market regime and phase at a glance.
- **Action:** Navigate to /
- **Point out:** The Market Regime and Market Phase & Severity cards show real, up-to-date figures pulled from stored data.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-2/step-01.png

### Step 02 — Open the Data Manager  [NEW]

- **Narration:** Now let's visit the Data Manager, the page an operator uses to grow the dataset. This iteration made its coverage numbers load from storage instead of being recalculated on every visit.
- **Action:** Navigate to /data
- **Point out:** The Dataset coverage tiles — Universe, Symbols, Trading days, Snapshot dates, Backfill gaps — populate immediately with real figures, not a multi-second wait.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-2/step-02.png

### Step 05 — Run the backfill job  [NEW]

- **Narration:** With "Backfill snapshots" already selected, clicking Start submits the job and we watch it finish.
- **Action:** Click the "Start" button
- **Point out:** A short status message appears, then a new "Refreshed" line names — in plain, comma-separated words — exactly which background data this run kept up to date.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-2/step-05.png

### Step 07 — Check the Run History table  [NEW]

- **Narration:** Scrolling down to the permanent Run History table shows every job this dataset has ever run.
- **Action:** Click the "Run history" heading
- **Point out:** That same run's row carries the identical "Refreshed" note in its Snapshots column — a durable record, not a live-only message.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-2/step-07.png

### Step 08 — Step back to an older date  [NEW]

- **Narration:** Using the date switcher's back arrow, let's step to an older, already-ingested date.
- **Action:** Click the "Previous available date" button
- **Point out:** The badge now reads "Viewing as-of … (historical)", and the coverage tiles show that older date's real, non-zero figures — never a false-empty panel.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-2/step-08.png

### Step 10 — Check the Scanner Runs list

- **Narration:** Let's also visit the Scanner Runs page, which reads from the same underlying stored data.
- **Action:** Navigate to /scanner-runs
- **Point out:** The list of dated scans still loads correctly, including the date we just backfilled.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-2/step-10.png

### Step 11 — Open a stored scan

- **Narration:** Opening that date's entry shows the scan exactly as it looked on that day.
- **Action:** Click the "2026-05-15" link
- **Point out:** The full leaderboard, regime score, and stock-by-stock rows all render normally, proving this update didn't disturb anything else in the product.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-2/step-11.png

## Full tour (text only)

### Step 03 — Enter a backfill start date

- **Narration:** Let's run a quick backfill so we can see this iteration's new capability for ourselves.
- **Action:** Type "2026-05-15" into "job-start-date"
- **Point out:** The Start date field now holds the date we're backfilling.

### Step 04 — Enter the matching end date

- **Narration:** A single-day backfill just needs the same date in both fields.
- **Action:** Type "2026-05-15" into "job-end-date"
- **Point out:** The End date field now matches the start date.

### Step 06 — Reload to confirm it was saved  [NEW]

- **Narration:** Let's fully reload the page, to make sure that note wasn't just a one-time, in-session display.
- **Action:** Navigate to /data
- **Point out:** The same "Refreshed" note is still there after the reload — proof it was genuinely saved, not just shown once.

### Step 09 — Return to the latest date

- **Narration:** Stepping forward again brings us right back to today's latest view.
- **Action:** Click the "Next available date" button
- **Point out:** The badge reads "Latest" again, and the numbers instantly match what we started with.
