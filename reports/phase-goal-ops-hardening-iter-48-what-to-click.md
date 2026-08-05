# Phase goal-ops-hardening-iter-48 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-48
**Time required:** ~5 minutes (plus a few minutes of watching a badge — see step 5)
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running (started via `scripts/start-backend.sh`, not `dev.sh`) — no login required anywhere in
  this app
- No data job currently running on `/data` (check the "Job progress" panel is idle or shows a completed job
  before you start)
- Target date `2012-06-15` should NOT already appear as a row on `/scanner-runs`. If it does (a prior
  verification pass already used it), pick any other date between `2005-05-24` and `2019-02-25` that is
  NOT yet on `/scanner-runs`, and use that date in every step below instead.

---

## Verification Steps

1. Open `http://localhost:3255/data` in your browser
   - **Expect:** "Data Manager" heading loads, no error page. A "Start a fetch / backfill job" panel is
     visible with two date fields and a "Job kind" dropdown.

2. In the "Start date" field type `2012-06-15`, then in the "End date" field type `2012-06-15`. Leave
   "Job kind" on its default, "Backfill snapshots".
   - **Expect:** The "Start" button becomes enabled (no longer greyed out).

3. Click the "Start" button
   - **Expect:** A "Job progress" panel appears showing a spinning badge labeled "running" and
     "Snapshots backfilled 0/1 dates".

4. Wait about 30 seconds, then look at the "Job progress" panel again
   - **Expect:** A new line appears reading "Refreshed: …" and mentioning "membership timeline" — this
     confirms the specific defect this iteration fixed (a step that used to take well over an hour for an
     old date) finished in well under a minute.

5. Keep the page open and watch the status badge for up to a few minutes
   - **Expect:** The badge eventually stops spinning and settles to "ok" (or "no new snapshots"). If it is
     STILL spinning after 20 minutes, that is a known, already-disclosed gap (a separate, unrelated slow
     step this iteration did not fix) — move on to step 6 rather than waiting indefinitely; that step is
     what actually confirms the app is still healthy.

6. While the badge from step 5 is (or was) still "running", look at the small "Ready" badge in the page
   header (green dot, top of the page)
   - **Expect:** It stays on "Ready" (green) the whole time. It must never flip to "Backend unavailable"
     (red) — that would mean the app froze, which this fix specifically guarantees will not happen even on
     a slow finalize.

7. Once the badge from step 5 reads "ok" (or "no new snapshots"), navigate to
   `http://localhost:3255/scanner-runs`
   - **Expect:** A row with "As of" date `2012-06-15` appears in the table, as a clickable link.

8. Click the `2012-06-15` link
   - **Expect:** Page navigates to `/scanner-runs/<some-id>` and shows "Immutable snapshot — as of
     2012-06-15" with a populated stock leaderboard table below it (not a blank or "not found" page).

9. Navigate to `http://localhost:3255/evidence`
   - **Expect:** Page loads without an error screen; at least one claim's "Historical drawdown & dry-spell
     expectations" table shows real percentage numbers (confirms the second, memory-only fix in this
     iteration didn't change what's displayed).

10. Go back to `/data` and repeat steps 2–3 with the SAME date `2012-06-15` a second time
    - **Expect:** This time the badge reads "no new snapshots" (not "ok"), and a note appears saying
      "Zero-work outcome — every requested trading day already had a snapshot…" — confirms a re-run over
      an already-scanned date is reported honestly, never as a fabricated fresh success.

---

## What "Working Correctly" Looks Like

- The `/data` job-status badge for a historical-date backfill eventually stops spinning on "running"
  (typically within a few minutes) — it used to be stuck there indefinitely for this exact scenario.
- The "Ready" badge in the header never turns red/"Backend unavailable" while that job is finalizing, even
  if the job itself is still slow to finish.
- The backfilled date shows up as a real, clickable row on `/scanner-runs` with a working leaderboard —
  it used to never get there.

## Common Issues

- **Blank page / error screen on `/data`**: Check the backend is running — look at the "Ready" badge in the
  header; if it reads "Backend unavailable," restart the backend with `scripts/start-backend.sh`.
- **Job status badge never moves off "running" past 20+ minutes**: This is the known, disclosed remaining
  gap (a separate, unrelated finalize-tail step this iteration did not fix) — check the "Ready" badge
  first (step 6); if it's still green, the app is healthy and this is the already-recorded gap, not a new
  bug.
- **`2012-06-15` already has a row on `/scanner-runs` before you start**: A prior verification pass already
  consumed that date. Pick any other date in `2005-05-24` … `2019-02-25` and use it consistently across all
  steps.
- **Evidence/Factor Lab page shows an error or blank drawdown table**: Check the backend logs for a
  `MemoryError` — this iteration's second fix specifically targets that failure mode; a recurrence would be
  a real regression worth flagging.
