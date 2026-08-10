# Phase goal-ops-hardening-iter-57 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-57
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and reachable, idle (no ingest job already in progress)
- No login required
- The database already has at least one completed ingest (the shared dev DB qualifies)

---

## Verification Steps

1. Open `http://localhost:3255/` in your browser
   - **Expect:** Dashboard loads, and the badge in the top-right of the header reads "Ready" (green dot) within about a second — no long stall before it settles

2. Click "Data Manager" in the left navigation (or navigate to `http://localhost:3255/data`)
   - **Expect:** Heading "Data Manager" is visible, and the "Per-date availability" card near the top shows a real colored calendar grid of days — NOT the message "No availability yet"

3. Navigate to `http://localhost:3255/stocks/AAPL`
   - **Expect:** "AAPL" appears on the page, and within about a second the "Price & moving averages" card shows a caption like "N bars · as of YYYY-MM-DD · history since YYYY-MM-DD" plus a price chart with moving-average lines

4. Open your browser's DevTools (F12), click the "Network" tab, then reload the `/stocks/AAPL` page
   - **Expect:** The request to `api/stocks/AAPL/bars?through=latest` completes in well under 1.5 seconds (previously this could take over 6 seconds)

5. In the same Network tab, find the request to `api/health`
   - **Expect:** It completes in well under 100 milliseconds (previously this could take 150-240ms)

6. Go back to `http://localhost:3255/data`. In the job form near the bottom, set "Job kind" to "Fetch EOD prices", pick the smallest date range you can (a single day), and click the "Start" button
   - **Expect:** The button changes to show "Job running…"

7. Within a few seconds, reload `http://localhost:3255/data`
   - **Expect:** Either the job has already finished (grid looks normal, no banner — that's fine, it means the range was too small to catch mid-flight), OR you see a calm text banner reading "Data as of `<date>` — updating" directly above the calendar grid, with the grid still showing real colored cells underneath it (never the empty "No availability yet" message)

---

## What "Working Correctly" Looks Like

- The header's "Ready" badge and the two Network-tab timings (step 4, step 5) are consistently fast — no multi-second waits anywhere in normal browsing.
- The `/data` availability heatmap always shows real data (colored cells) whenever the database has any — it should never show the "No availability yet" empty message unless the database is genuinely brand-new.
- If you do catch the job mid-flight in step 7, the "Data as of … — updating" banner looks calm and factual, not like an error (muted gray text, no red/alarm styling) — it should look like a normal status note, not a warning.

## Common Issues

- **Blank page / error screen**: Check that the backend is running (`curl http://localhost:8000/health` or the port configured for this environment).
- **Step 7 never shows the banner**: The job likely finished before your reload — this is expected for a very small date range and is not a failure. Retry with "Backfill snapshots" as the job kind, which takes longer, or a wider date range.
- **Network tab timings look slow (over 1.5s for bars, over 100ms for health)**: Confirm no other heavy job (backfill, test suite) is running concurrently on the same machine — these fixes apply to steady-state, uncontended reads.
