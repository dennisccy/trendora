# Phase goal-ops-hardening-iter-1 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-1
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and reachable — no login is required for this app
- No special seed data needed beyond the committed database this project ships with

---

## Verification Steps

1. Open `http://localhost:3255/data` in your browser
   - **Expect:** The "Data Manager" page loads with a "Dataset coverage" panel, a "Start a fetch / backfill job" panel, a "Job progress" panel, and a "Run history" table below — no red error card, no blank page.

2. In the "Start a fetch / backfill job" panel, leave "Job kind" as "Backfill snapshots". Click into "Start date", select all and type `2026-05-02`; click into "End date", select all and type `2026-05-29`. Click the "Start" button.
   - **Expect:** Within a few seconds the "Job progress" panel shows a green badge reading "ok" and a grey text line reading "28 calendar days · 0 already snapshotted · 9 non-trading". (If this exact range was already backfilled by an earlier test run, you'll instead see a grey "no new snapshots" badge with "19 already snapshotted" — that is also correct, it just means this is a repeat run.)

3. Now submit a second job: Start date `2026-05-02`, End date `2026-05-03`, click "Start" again.
   - **Expect:** A grey badge reading "no new snapshots" (visibly different color from the green "ok" in step 2), plus a note box reading "Zero-work outcome — every requested trading day already had a snapshot (or the range contains no trading days). No new computation was needed; this is not a failure."

4. Refresh the page (press F5).
   - **Expect:** The "Run history" table still lists both runs you just created, with the same badges and breakdown text. Nowhere on the page does the text "No job has been started this session" appear.

5. Submit a third job: Start date `2025-06-01`, End date `2026-07-17` (a 412-day span), click "Start".
   - **Expect:** The job is accepted immediately — no "date range too large" error. A grey badge reading "chunk 1/M" appears next to the running status, where M is greater than 1.

6. Try one invalid submission: Start date `2026-06-01`, End date `2026-05-01` (end before start), click "Start".
   - **Expect:** The job is rejected — a red error message appears below the form mentioning "must be on or before". The "Job progress" panel does NOT switch to a running job.

7. Navigate to `http://localhost:3255/scanner-runs`
   - **Expect:** Rows now exist in the "As of" column for `2026-05-04`, `2026-05-15`, and `2026-05-29` — dates that only exist because of step 2's backfill.

8. Click the `2026-05-04` row.
   - **Expect:** A "Scanner Run" page opens showing a regime badge and a populated table of stocks for that date — not an empty page or error.

---

## What "Working Correctly" Looks Like

- The zero-work badge (step 3) is grey/neutral — visibly NOT the same green as a productive "ok" run in step 2. Zero-work always comes with a plain-English explanation box, never a bare success badge.
- The large 412-day request in step 5 is accepted and starts running (with a chunk-progress badge), instead of being rejected outright the way it used to be.
- After the refresh in step 4, all your run history is still there and the panel never falls back to the old "no job started" placeholder text once real history exists.

## Common Issues

- **Red "Backend unavailable" card instead of the Data Manager loading**: the backend isn't running or isn't reachable — confirm it's up and reload.
- **Step 5's job seems stuck "running" for a long time**: this is expected — a 412-day backfill is not required to finish quickly, only to be accepted and show forward progress. It will keep the "Start" button disabled on that tab until it finishes or you reload the page.
- **Step 2 shows "no new snapshots" instead of green "ok"**: this means that exact date range was already backfilled earlier (by you or an automated test) — it is not a bug; try a different, never-used May-2026 sub-range if you want to see the fresh productive path.
