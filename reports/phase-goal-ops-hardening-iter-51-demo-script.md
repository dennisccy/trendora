# Demo Script — goal-ops-hardening-iter-51

**Mode:** record
**Date:** 2026-08-07
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Open the Data Manager to see factor lab refresh status

- **Narration:** The Data Manager shows what aggregates were refreshed during each data-loading job. Let's check the most recent run to confirm the new factor lab warm completed successfully.
- **Action:** Navigate to /data
- **Point out:** Look for the 'Refreshed:' line in the Job progress card — it now includes 'factor lab all'.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-51/step-01.png

### Step 02 — Verify factor lab all appears in the completed job's refresh list  [NEW]

- **Narration:** This tells us the ingest-time factor lab warm ran during the job's finalize step. The page already shows this status for completed runs.
- **Action:** Click the "Job progress" heading
- **Point out:** The gray text under the job card reads 'Refreshed: … factor lab all, coverage, research hot keys, …' — a new entry this iteration.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-51/step-02.png

### Step 03 — Navigate to the Factor Lab research page  [NEW]

- **Narration:** Opening Factor Lab used to sometimes trigger a live, multi-minute computation on first visit after new data loaded. That computation now runs during ingest instead, so the page responds immediately.
- **Action:** Navigate to /research/factor-lab
- **Point out:** Notice the page loads with data in just a few seconds — no multi-minute 'Still computing' amber card.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-51/step-03.png

### Step 04 — Confirm the factor table loads with real data

- **Narration:** The all-factors comparison is now served from the cache warmed at ingest time, delivering real numbers immediately instead of waiting for a live compute.
- **Action:** Click the "Research" button
- **Point out:** The table shows 11 real factor rows (e.g., 'Leadership score') with numeric columns like 'N', 'Mean', 'Rank IC'. No placeholder data, no 'Still computing' notice.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-51/step-04.png

### Step 08 — Open the Research hub to confirm Factor Lab is discoverable

- **Narration:** Factor Lab remains accessible from the main Research page, unchanged in wording and position.
- **Action:** Navigate to /research
- **Point out:** The 'Factor Lab' tile is present in the lab grid. Clicking it navigates back to the Factor Lab page.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-51/step-08.png

## Full tour (text only)

### Step 05 — Return to Factor Lab and test sort interaction

- **Narration:** The sort controls work client-side on the cached data. Click a column header to verify rows re-order without a page reload.
- **Action:** Navigate to /research/factor-lab
- **Point out:** Clicking the 'N' header flips the sort direction, rows re-order immediately, and the sort indicator shows the new direction.

### Step 06 — Click the N column header to trigger a client-side sort

- **Narration:** Sorting should be instant on cache-warmed data.
- **Action:** Click "[data-testid='factor-lab-table'] thead th:nth-child(2)"
- **Point out:** Rows re-order without any spinner or network request.

### Step 07 — Expand a factor row to view its decile distribution

- **Narration:** Clicking a row reveals its D1–D10 decile breakdown. This detail view also works instantly on the cached data.
- **Action:** Click "[data-testid='factor-lab-table'] tbody tr:first-child"
- **Point out:** The first row expands to show a decile grid below it — no error, no loading delay.
