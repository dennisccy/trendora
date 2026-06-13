# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12

**Mode:** record
**Date:** 2026-06-13
**Frontend URL:** http://localhost:3835
**Iteration:** 12

## Highlights

### Step 01 — Open the Data Manager  [NEW]

- **Narration:** The Data Manager is where you kick off and monitor stock-data imports. It now shows everything about every job — from the moment it starts to long after it finishes.
- **Action:** Navigate to /data
- **Point out:** The page loads cleanly with a Data Manager heading, an Unfinished Imports section, and a Run History section — no error banners.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12/step-01.png

### Step 02 — Run History captures every job from the start  [NEW]

- **Narration:** The moment you dispatch a job, a new row with a spinning indicator appears in Run History — you no longer have to wait for a job to finish before you can see it was started.
- **Action:** Navigate to /data
- **Point out:** Look for a row labelled 'running' with an inline spinner that appears immediately after a job is submitted, before any results come back.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12/step-02.png

### Step 03 — Live job card — current-activity line  [NEW]

- **Narration:** While a backfill runs, the live job card shows exactly which date the engine is working on right now, updated every second so you can see real progress rather than a static bar.
- **Action:** Navigate to /data
- **Point out:** The current-activity line reads something like 'scanning 2022-01-26 (17/62)' and the number advances as each date completes.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12/step-03.png

### Step 04 — Heartbeat tells you if the job is alive  [NEW]

- **Narration:** Below the activity line a small timestamp reads 'updated 1s ago' and counts up every second. If the job ever stops advancing for more than 20 seconds the text turns amber and says 'possibly stalled' — a clear signal between a slow job and a hung one.
- **Action:** Navigate to /data
- **Point out:** The 'updated Ns ago' line in the live job card — watch the counter tick up while the job runs.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12/step-04.png

### Step 05 — Stage timings with server-computed speedup  [NEW]

- **Narration:** After a parallel backfill completes, the Stage Timings panel shows how long each stage took and how much faster the parallel run was compared to running each date in sequence — that figure is now calculated on the server so you always see an accurate number.
- **Action:** Navigate to /data
- **Point out:** The Stage Timings section shows 'Elapsed', 'Dates', 'Concurrency', and a speedup factor like '0.5x faster than the per-date sum' — a real server-computed value, not a browser estimate.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12/step-05.png

### Step 06 — Partial job surfaces per-date failure detail  [NEW]

- **Narration:** When a multi-date backfill hits one bad date, it no longer aborts — the remaining dates complete and the job ends as 'partial'. The Run History entry lists exactly which dates failed and their error messages so you know precisely what to fix.
- **Action:** Navigate to /data
- **Point out:** A 'partial' row in Run History expands to show the specific dates that failed, each with its error message, plus a note that the other dates completed successfully.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12/step-06.png

### Step 07 — Visually distinct status badges  [NEW]

- **Narration:** Every job status has its own color: green for completed, amber for partial or resumable, a spinning blue indicator for running, and neutral for interrupted. You can scan the entire Run History at a glance and know the health of every past job.
- **Action:** Navigate to /data
- **Point out:** Status badges in Run History — 'ok' is green, 'partial' is amber, 'running' has a spinning blue badge, and 'seed load' is neutral grey.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12/step-07.png

### Step 08 — Unfinished Imports — resume from backfill  [NEW]

- **Narration:** If a job that already downloaded all its data later fails during the snapshot-building stage, it appears in Unfinished Imports with an amber 'failed at backfill' badge and a Resume button. Clicking Resume picks up exactly where things stopped — no re-downloading, no wasted time.
- **Action:** Navigate to /data
- **Point out:** The Unfinished Imports section shows entries with amber badges and action buttons. A 'failed at backfill' entry offers a Resume button that skips the download stage entirely.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12/step-08.png
