# Demo Script — goal-ops-hardening-iter-4

**Mode:** record
**Date:** 2026-07-20
**Frontend URL:** http://localhost:3255
**Iteration:** 4

## Highlights

### Step 01 — Open the dashboard

- **Narration:** Trendora opens straight to its daily dashboard, with a live status badge and a health banner right at the top of every page.
- **Action:** Navigate to /
- **Point out:** The badge reads "Ready" and the green banner underneath confirms today's board is current — both check in with the backend before showing anything.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-4/step-01.png

### Step 02 — Open Data Manager

- **Narration:** A single click from the sidebar takes you to Data Manager, where the app tracks exactly how much price history and how many daily snapshots it has on hand.
- **Action:** Click the "Data Manager" link
- **Point out:** The Dataset coverage panel shows real counts — symbols, trading days, snapshot dates, and any backfill gaps — never placeholder numbers.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-4/step-02.png

### Step 03 — Choose a backfill job

- **Narration:** In the "Start a fetch / backfill job" panel, switch the job kind to Backfill snapshots — the date range is already pre-filled to the data's current gap.
- **Action:** Type "Backfill snapshots" into the "Job kind" field
- **Point out:** No guesswork needed: the form already knows which dates need attention.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-4/step-03.png

### Step 04 — Run the backfill

- **Narration:** Clicking Start kicks off the backfill immediately — no scripts or terminal needed.
- **Action:** Click the "Start" button
- **Point out:** The Job progress panel appears right away with a real breakdown — calendar days, days already snapshotted, and non-trading days — plus a live "updated Ns ago" heartbeat that keeps ticking for as long as the job runs.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-4/step-04.png

### Step 05 — Confirm the status badge never breaks  [NEW]

- **Narration:** Reloading the page proves everything survives the round trip — and, importantly, that an everyday backfill job never falsely flips the top status badge to "Backend unavailable" anymore.
- **Action:** Navigate to /data
- **Point out:** The badge still reads "Ready," exactly as before the job started — that stability is what this iteration fixed.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-4/step-05.png
