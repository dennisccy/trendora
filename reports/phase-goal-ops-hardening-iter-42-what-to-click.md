# Phase goal-ops-hardening-iter-42 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-42
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and reachable at `http://localhost:8255/api/health`
- No login required
- No new seed data required — the seeded May 2026 basis already supports the backfill checks below

---

## Verification Steps

This iteration shipped **no new feature** — it closed a gap in the automated test pipeline (so the
two journeys below, J-05 and J-07, actually get checked instead of silently skipped) and attempted a
memory-footprint reduction in one backend code path. There is nothing new to click. This guide instead
confirms the eight journeys named in this iteration's spec — the six "required-still-passing" ones
plus the two "target" ones (J-05, J-07) — still work, since making that verification trustworthy is
the whole point of this iteration.

1. Open `http://localhost:3255/` in your browser
   - **Expect:** Dashboard loads; the top-bar badge in the upper right reads "Ready" with a green dot —
     never a blank header

2. Click "Data" in the top navigation (or go directly to `http://localhost:3255/data`)
   - **Expect:** The "Start a fetch / backfill job" panel is visible with "Start date" / "End date"
     fields and a "Job kind" dropdown defaulted to "Backfill snapshots"

3. Type `2026-05-02` in "Start date" and `2026-05-29` in "End date", then click the "Start" button
   (accent button, play icon)
   - **Expect:** The "Job progress" panel moves off "running" to a finished state; the summary
     mentions "19" trading days, or — if this range was already backfilled before — shows a distinct
     "no new snapshots" explanation (never an unexplained plain success badge)

4. Scroll down to "Run history" and find the row for the run you just started
   - **Expect:** The row's summary text starts with "Refreshed:" and lists at least "latest snapshot"
     and "coverage" — this shows aggregates were computed once at ingest time, not blank and not
     computed later on request

5. Refresh the page (press F5)
   - **Expect:** The same run row is STILL listed in "Run history" after the reload — job history
     survived the refresh, it does not reset to empty

6. Click "Scanner Runs" in the top navigation (or go to `http://localhost:3255/scanner-runs`), then
   click the row for `2026-05-29`
   - **Expect:** The Scanner Run detail page opens and shows a populated leaderboard table — not
     "No stored stock rows"

7. Back on `http://localhost:3255/data`, type `2025-06-01` in "Start date" and `2026-07-17` in "End
   date" (a much wider, 411-day range), then click "Start"
   - **Expect:** No "date range too large" (or similar rejection) message appears; the "Job progress"
     panel shows a running state with visible movement — the wide range is accepted and starts
     executing, it is not rejected

8. While that job is still running, click "Backtest" in the top navigation (or go to
   `http://localhost:3255/backtest`)
   - **Expect:** The page renders promptly — either normal evidence values, or a banner reading
     "Refreshing — showing the last complete evidence" — never a blank page or a screen that never
     finishes loading, even while the heavy job from step 7 keeps running in the background

9. Look at the top-bar badge one more time
   - **Expect:** Still reads "Ready" — confirming the backend stayed responsive throughout the heavy
     job — with an extra "background compute running (N)" chip next to it if a compute window happens
     to still be in flight; otherwise no extra chip

10. Go back to `http://localhost:3255/data` and scroll to the "Background compute" panel
    - **Expect:** If a window was in flight, it lists that window with elapsed time and horizons
      done/total; once finished, its "Last outcome" section shows a completed result with a real
      measured duration — never a blank panel with no explanation

---

## What "Working Correctly" Looks Like

- The badge in the top-right corner is always either "Ready", an explicit initializing state, or
  "Backend unavailable" — never a blank header with nothing in it, and it stays "Ready" even while a
  large backfill and its aggregate warm are running in the background
- A backfill you start on `/data` finishes, its "Run history" row names which aggregates it
  refreshed, and the row is still there after you refresh the page — job history and its aggregate
  disclosure are never lost or blank
- `/backtest` never shows a blank or endlessly-spinning screen, even during a heavy background warm —
  it either shows real numbers or an honest "Refreshing…" note
- A wide, multi-month date range on `/data` is accepted and starts running — it is never rejected for
  being "too large"

## Common Issues

- **Blank page / error screen:** confirm the backend is actually up —
  `curl http://localhost:8255/api/health` should return HTTP 200 with JSON, not a connection error
- **"Start" button stays disabled:** both date fields must contain a valid `yyyy-MM-dd` date before the
  button becomes clickable
- **Run history row never appears:** wait for the "Job progress" panel to leave the "running" state
  first — the row is added once the job resolves, not while it is still in flight
- **Badge goes to "Backend unavailable" while a job runs:** this is the specific regression this
  iteration's `_BarCache.prefill` and `common.sh` fixes target — if you can reproduce it, it means the
  fix did not hold and should be flagged, not dismissed as a fluke
- This iteration made no application-code UI changes, so any UI difference from what you remember
  seeing before is unexpected — if something looks different, flag it, since none of the changes in
  this iteration were supposed to touch the frontend at all
