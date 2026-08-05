# Phase goal-ops-hardening-iter-49 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-49
**Time required:** ~5 minutes of active clicking, plus roughly 17-18 minutes of waiting/occasional
glancing for the backfill job itself to finish (this iteration's whole point is proving that wait now
reliably stays under 20 minutes — see step 5)
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running (started via `scripts/start-backend.sh`, not `dev.sh`) — no login required anywhere in
  this app
- No data job currently running on `/data` (check the "Job progress" panel is idle or shows a completed
  job before you start)
- Ideally an otherwise-idle host (no other heavy test suite or ingest job running concurrently) — a busy
  host can genuinely slow this down, per this iteration's own diagnosis
- Target date `2012-01-05` should NOT already appear as a row on `/scanner-runs`. If it does (a prior
  verification pass already used it), pick any other date between `2005-05-24` and `2019-02-25` that is
  NOT yet on `/scanner-runs`, and use that date in every step below instead.

---

## Verification Steps

1. Open `http://localhost:3255/data` in your browser
   - **Expect:** "Data Manager" heading loads, no error page. A "Start a fetch / backfill job" panel is
     visible with two date fields and a "Job kind" dropdown.

2. In the "Start date" field type `2012-01-05`, then in the "End date" field type `2012-01-05`. Leave
   "Job kind" on its default, "Backfill snapshots".
   - **Expect:** The "Start" button becomes enabled (no longer greyed out).

3. Click the "Start" button
   - **Expect:** A "Job progress" panel appears showing a spinning badge labeled "running" and
     "Snapshots backfilled 0/1 dates".

4. Wait about 30 seconds, then look at the "Job progress" panel again
   - **Expect:** A new line appears reading "Refreshed: …" and mentioning "membership timeline" — this
     confirms the job is proceeding normally through the step iter-48 already fixed, before this
     iteration's own two newly-bounded steps even begin.

5. Keep the page open and check the status badge every few minutes. This is the core thing this iteration
   fixes — budget roughly 17-18 minutes total.
   - **Expect:** The badge stops spinning and settles to "ok" (or "no new snapshots") comfortably before
     the 20-minute mark. Unlike a prior iteration's known gap, this SHOULD now reliably happen — if the
     badge is still spinning on "running" past 20 full minutes on an otherwise-idle host, that is a real
     finding worth reporting, not an expected wait.

6. While the badge from step 5 is still "running," glance at the small "Ready" badge in the page header
   (green dot, top of the page) a few times over the wait, especially in the first couple of minutes
   - **Expect:** It shows "Ready" (green) almost the entire time. A newly-disclosed, already-known gap: it
     MAY flicker briefly (a few seconds) to "Backend unavailable" (red) roughly 40-45 seconds after you
     clicked Start in step 3, then recover on its own — that specific brief blip is a known, out-of-scope
     issue, not a new bug. It should NOT stay red for more than about 15 seconds, and should NOT flip red
     at any other point in the run.

7. Once the badge from step 5 reads "ok" (or "no new snapshots"), navigate to
   `http://localhost:3255/scanner-runs`
   - **Expect:** A row with "As of" date `2012-01-05` appears in the table, as a clickable link.

8. Click the `2012-01-05` link
   - **Expect:** Page navigates to `/scanner-runs/<some-id>` and shows text containing "as of 2012-01-05"
     with a populated stock leaderboard table below it (not a blank or "not found" page).

9. Navigate to `http://localhost:3255/evidence`
   - **Expect:** Page loads without an error screen; at least one claim's "Historical drawdown & dry-spell
     expectations" table shows real percentage numbers (confirms the speed-only fixes in this iteration
     didn't change what's displayed).

10. Go back to `/data` and repeat steps 2–3 with the SAME date `2012-01-05` a second time
    - **Expect:** This time the badge reads "no new snapshots" (not "ok"), and a note appears saying
      "Zero-work outcome — every requested trading day already had a snapshot…" — confirms a re-run over
      an already-scanned date is reported honestly, never as a fabricated fresh success.

---

## What "Working Correctly" Looks Like

- The `/data` job-status badge for a historical-date backfill reliably stops spinning on "running" within
  about 17-18 minutes — this used to take 20+ minutes (or, in a prior iteration's worst case, never
  finish).
- The "Ready" badge in the header stays green the whole time, with at most one brief (~10 second) flicker
  very early in the run — a known, disclosed, unfixed gap, not a new crash.
- The backfilled date shows up as a real, clickable row on `/scanner-runs` with a working leaderboard,
  reliably within the promised ~20-minute window.
- `/evidence` and `/backtest` still show the same real numbers as before — this iteration only made the
  server-side calculation faster, not different.

## Common Issues

- **Blank page / error screen on `/data`**: Check the backend is running — look at the "Ready" badge in the
  header; if it reads "Backend unavailable," restart the backend with `scripts/start-backend.sh`.
- **Job status badge never moves off "running" past 20+ minutes**: Unlike a prior iteration, this IS now a
  genuine finding worth reporting (this iteration's whole purpose was closing exactly this gap) — first
  rule out a busy host (another heavy process running concurrently can slow this down), then report it.
- **Brief red flicker on the "Ready" badge around 40-45 seconds into the run**: This is a known, already-
  disclosed gap (not something this iteration introduced or was asked to fix) — as long as it recovers
  within about 10 seconds and doesn't recur later in the run, it's expected, not a new bug.
- **`2012-01-05` already has a row on `/scanner-runs` before you start**: A prior verification pass already
  consumed that date. Pick any other date in `2005-05-24` … `2019-02-25` and use it consistently across all
  steps.
- **Evidence/Factor Lab/Backtest page shows an error or blank table**: Check the backend logs for an
  unexpected exception — this iteration touched the calculation paths feeding these pages, so a genuine
  error here (not the known health-badge flicker above) would be a real regression worth flagging.
