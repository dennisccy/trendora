# Phase goal-ops-hardening-iter-50 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-50
**Time required:** ~5 minutes of active clicking, plus roughly 15-20 minutes of occasional glancing while
the backfill job's finalize tail runs in the background (this iteration's whole point is that the backend
now survives being used normally during that wait — see steps 4-6)
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running (started via `scripts/start-backend.sh`, not `dev.sh`) — no login required anywhere in
  this app
- No data job currently running on `/data` (check the "Job progress" panel is idle or shows a completed job
  before you start)
- Target date `2012-01-04` should NOT already appear as a row on `/scanner-runs`. If it does, pick any
  other date between `2005-05-24` and `2019-02-25` that is NOT yet on `/scanner-runs`, and use that date in
  every step below instead.

---

## Verification Steps

1. Open `http://localhost:3255/research/factor-lab` in your browser
   - **Expect:** "Research — Factor Lab" heading loads, no error page, and the all-factors table shows
     real rank-IC and decile figures for multiple factors — not a blank screen, not "Backend unavailable."
     (This alone proves the crash fix works on an isolated page load; the steps below prove it holds under
     the specific concurrent load that used to crash the backend.)

2. Open `http://localhost:3255/data`, type `2012-01-04` into both the "Start date" and "End date" fields,
   leave "Job kind" on its default "Backfill snapshots," and click the "Start" button
   - **Expect:** A "Job progress" panel appears showing a spinning badge labeled "running."

3. Wait about 30 seconds, then look at the "Job progress" panel again
   - **Expect:** A line appears reading "Refreshed: …" mentioning "membership timeline" — the job has
     moved past its fast first stage into the slower finalize-tail phases this iteration protects.

4. Open a SECOND browser tab and navigate to `http://localhost:3255/research/factor-lab` WHILE the job from
   step 2 is still showing "running" in the first tab
   - **Expect:** The Factor Lab page finishes loading normally (same populated table as step 1) — it does
     NOT hang forever, crash to a blank page, or show "Backend unavailable." **This is the single most
     important check in this guide** — last round, doing exactly this (viewing Factor Lab while an ingest's
     background warm was running) killed the backend for over 12 minutes.

5. Switch back to the first tab (`/data`) and look at the small "Ready" badge in the page header
   - **Expect:** It shows "Ready" (green), both right after step 4 and if you check again a minute later.
     It should NOT flip to "Backend unavailable" (red) and stay there.

6. Keep the first tab open and check the job-status badge every few minutes — budget roughly 15-20 minutes
   total from when you clicked Start in step 2
   - **Expect:** The badge eventually stops spinning and settles to "ok" (or "no new snapshots"). A badge
     still spinning on "running" past 20 full minutes on an otherwise-idle host is a real finding worth
     reporting.

7. Once the badge from step 6 reads a settled state, navigate to `http://localhost:3255/scanner-runs`
   - **Expect:** A row with "As of" date `2012-01-04` appears in the table, as a clickable link.

8. Click the `2012-01-04` link
   - **Expect:** Page navigates to `/scanner-runs/<some-id>` and shows text containing "as of 2012-01-04"
     with a populated stock leaderboard table below it.

9. Navigate to `http://localhost:3255/evidence`
   - **Expect:** Page loads without an error screen; at least one claim's "Historical drawdown & dry-spell
     expectations" table shows real percentage numbers (confirms this iteration's internal changes to the
     same code path didn't disturb what's displayed).

10. Navigate to `http://localhost:3255/backtest`
    - **Expect:** Page loads without an error screen; the forward-test scorecard shows real numeric
      hit-rate/return figures for the default horizon (another regression confirmation).

---

## What "Working Correctly" Looks Like

- `/research/factor-lab` loads normally BOTH on its own AND while a data job's background finalize-tail
  warm is actively running — this is the exact combination that used to bring the whole backend down.
- The "Ready" badge in the header stays green throughout the entire wait, including the moment you open
  Factor Lab in a second tab.
- The `/data` job-status badge reliably stops spinning within about 15-20 minutes, and the backfilled date
  shows up as a real, clickable row on `/scanner-runs` with a working leaderboard.
- `/evidence` and `/backtest` still show real numbers — this iteration only changed internal reliability,
  never what's displayed on those pages.

## Common Issues

- **Blank page / error screen anywhere**: Check the "Ready" badge in the header; if it reads "Backend
  unavailable," restart the backend with `scripts/start-backend.sh`.
- **Factor Lab hangs or the backend goes "unavailable" during step 4-6**: This IS a genuine regression —
  it means the exact scenario this iteration was built to fix is still happening. Report it with a
  timestamp and which tab/action triggered it.
- **Job status badge never moves off "running" past 20+ minutes**: First rule out a busy host (another
  heavy process running concurrently can slow this down); if the host is otherwise idle, this is a real
  finding worth reporting.
- **`2012-01-04` already has a row on `/scanner-runs` before you start**: A prior verification pass already
  consumed that date. Pick any other date in `2005-05-24` … `2019-02-25` and use it consistently across all
  steps.
- **Evidence/Backtest page shows an error or blank table**: Check the backend logs for an unexpected
  exception — a genuine error here (not the known Factor Lab behavior from step 4) would be a real
  regression worth flagging.
