# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running (confirm with: the `/data` page does not show a "Backend unavailable" error)
- At least one symbol available to import (e.g., AAPL or any symbol already in the system)
- For steps 5–6: a prior job that failed during the backfill stage must exist in the database (a `failed_backfill` checkpoint). If none exists, skip those steps.

---

## Verification Steps

1. Open `http://localhost:3835/data` in your browser
   - **Expect:** The Data Manager page loads. You can see an "Unfinished Imports" section and a "Run History" section. No red error banners are visible.

2. Start a new import job: select any symbol and a short date range (1–2 months), then click the submit/start button
   - **Expect:** A live job card appears on the page. Within 2 seconds, scroll down to "Run History" — a new row with status "running" and an inline spinner appears immediately, before the job finishes.

3. Watch the live job card for 10 seconds while the job runs
   - **Expect:** Below the progress bar in the live job card, a current-activity line appears reading something like "fetching AAPL (1/1)" or "scanning 2024-06-01 (3/12)". The text changes as the job progresses. A heartbeat line reading "updated 1s ago" (or similar) is also visible and its counter increments each second.

4. While still watching the live job card, check the symbols counter (e.g., "Symbols: 2/5")
   - **Expect:** The left number (completed symbols) never exceeds the right number (total symbols). If you see "3/3", that is correct. If you ever see "4/3" or any value where the left exceeds the right, that is a bug.

5. After the job finishes, scroll to the "Unfinished Imports" section and look for an entry with an amber "failed at backfill" badge
   - **Expect:** If a `failed_backfill` checkpoint exists, the entry shows an amber badge labeled "failed at backfill", description text mentioning "Resumable from the backfill stage (the fetch is skipped — zero provider calls)", and an enabled "Resume" button. If no such entry exists, skip steps 5 and 6.

6. Click the "Resume" button on the "failed at backfill" entry
   - **Expect:** A new live job card appears showing the job starting at the backfill stage (the current-activity line says something like "scanning YYYY-MM-DD (N/M)" — NOT a fetch-stage message). The job completes with status "ok" or "partial" (not "failed"). A new row for this resumed job appears in Run History.

7. Scroll to the "Run History" section after one or more jobs have completed
   - **Expect:** Any job that ended in "partial" status shows a failure detail block listing which specific date(s) failed and their error messages, with a note that remaining dates completed. Rows with "ok" status show green styling. Rows with "partial" show amber. Any "interrupted" row (from a prior backend restart) shows a neutral/muted style.

---

## What "Working Correctly" Looks Like

- The live job card shows a current-activity line (e.g., "scanning 2024-06-01 (12/22)") that changes as the job progresses — this is new in this phase.
- The heartbeat line reads "updated Ns ago" and increments each second — if the number gets past 20 seconds, the text turns amber and says "possibly stalled".
- Run History shows a "running" row (with spinner) the moment a job starts — not only after it finishes.
- An unfinished "failed at backfill" import shows an amber badge and a Resume button that skips re-downloading data.

## Common Issues

- **Page shows "Backend unavailable" or data does not load:** The backend is not running. Start it, then refresh the page.
- **Live job card never appears after clicking submit:** Check the browser console (F12) for API errors. The backend may have rejected the job request.
- **Run History does not show a "running" row immediately:** The backend may be an older build that does not yet write the row on job start. Confirm you are running the iter-12 build.
- **Heartbeat line not visible in the live job card:** The job may have completed too quickly. Try a larger date range (3+ months) to observe the heartbeat during a longer job.
