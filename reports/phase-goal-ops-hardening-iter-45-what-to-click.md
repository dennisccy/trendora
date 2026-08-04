# Phase goal-ops-hardening-iter-45 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-45
**Time required:** ~10 minutes (longer than usual — this iteration's whole point is a backfill-speed
change whose fast path this DB currently can't exercise; you're verifying the reliability side and
honestly recording the speed side, not confirming a fast happy path)
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running via `scripts/start-backend.sh` (not `dev.sh`) and reachable at
  `http://localhost:8255/api/health`
- No login required
- No new seed data required — the committed DB already has what you need
- A terminal, for one `curl` timing check (step 6) and to confirm a date is unsnapshotted (step 3)

---

## Verification Steps

This iteration shipped **no new feature and no frontend code change at all** — confirmed: zero files
under `apps/frontend/` changed. It made backfilling a NEW, more-recent trading day faster (by skipping a
full multi-decade history recheck it used to do every time), closed a rare logging bug that could let an
out-of-memory error crash a data job instead of being recorded safely, and refreshed two stale numbers in
an internal test script. There is nothing new to click.

**Before you start, know this — it changes what you should expect in steps 3-4 below:** the ONE kind of
backfill this iteration sped up (a brand-new, more-recent day) has no example left to test with in this
installation's current data — every day this database is still missing is an OLDER historical gap, and
those were deliberately NOT sped up this round (that's a known, disclosed, intentional limitation, not a
bug). So when you backfill a missing day below, expect it to behave like it did BEFORE this update — the
new day's actual price data appears quickly, but the background "Refreshed: forward aggregates" bookkeeping
can take well over 15 minutes, possibly not finishing in the time you have. That's expected. What you ARE
checking is that the app stays responsive and reachable the whole time.

1. Open `http://localhost:3255/` in your browser
   - **Expect:** The top-bar badge in the upper right reads "Ready" with a green dot; the page also shows
     the text "provider: seed" somewhere — never a blank header

2. Click "Data Manager" in the left sidebar (or go directly to `http://localhost:3255/data`)
   - **Expect:** The "Start a fetch / backfill job" panel is visible with "Start date" / "End date"
     fields, a "Run history" section below it, and a "Backfill gaps" stat showing a number around 2,530
     (the exact figure may have moved slightly since this guide was written — every backfill of a missing
     historical day lowers it by one, so a nearby number is fine; a blank panel or an error is not)

3. Pick a historical trading day NOT already in the "Run history" list or `/scanner-runs`. Try
   `2019-02-25` first (confirmed missing when this guide was written — it is the closest missing day to
   this database's current "latest filled" boundary). If it's no longer missing by the time you try it,
   look at the "Backfill gaps" number from step 2 and its neighboring "gap_last" style hint on the page,
   or just try a day a week or two earlier, e.g. `2019-02-18`. Type it into both "Start date" and
   "End date", then click the "Start" button
   - **Expect:** The "Job progress" panel starts moving (status changes to "running", the live-activity
     line updates). Within roughly a minute, click through to that run's row in "Run history" and open its
     scanner-run page — it should show "as of <your date>" with a populated leaderboard table, even if the
     job's OWN "Refreshed:" status (checked in step 8) is still not fully done yet

4. Back on `http://localhost:3255/data`, type `2019-01-01` in "Start date" and `2019-02-25` in "End date"
   (a range that still has real missing days in it), then click "Start"
   - **Expect:** No "date range too large" (or similar rejection) message appears. The "Job progress"
     panel shows a running state with visible movement — accepted and executing, not rejected. This job
     also kicks off the heavy background compute the next steps watch

5. While that job keeps running, watch the top-bar badge for a couple of minutes, and separately open
   `http://localhost:3255/backtest` in a second tab
   - **Expect:** The badge still reads "Ready" the whole time — never "Backend unavailable". The
     `/backtest` tab renders promptly — either normal evidence values, or a banner reading "Refreshing —
     showing the last complete evidence" — never a blank page or a screen that never finishes loading. (It
     is normal if you see the "Refreshing" banner immediately, even before this job affects anything — an
     earlier, unrelated backfill this session already left the evidence in a "refreshing" state)

6. Open a terminal and run this three times, about 10 seconds apart, while the job from step 4 is still
   running:
   `curl -s -o /dev/null -w "%{http_code} took %{time_total}s\n" http://localhost:8255/api/health`
   - **Expect:** Every line shows `200`. This iteration's own developer testing found the health check
     kept responding normally for the ENTIRE duration of a similar heavy job (over 18 minutes straight, no
     freeze) — so a consistent `200` here, even if a `took` value is occasionally a bit slow, is the
     expected and important result. Report the exact numbers you see

7. Go to `http://localhost:3255/data` and scroll to the "Background compute" panel
   - **Expect:** If a window is in flight, it lists that window with elapsed time and horizons done/total,
     and the panel states its history is "process-lifetime only, never persisted". It is normal for
     "horizons done" to stay at 0 for a long time while elapsed time keeps climbing — that reflects the
     same known-slow historical-gap-fill case named above, not a frozen panel

8. Find the "Run history" row for the job you started in step 3 (the single-day backfill)
   - **Expect:** Its "Refreshed:" text lists at least "latest snapshot" and "coverage". It will very
     likely still read something short of complete even several minutes later, possibly for the rest of
     your 10-minute check — that matches this iteration's own disclosed, intentional limitation for
     backfilling an OLD missing day. This is expected behavior right now, not something to flag as newly
     broken. Write down the literal text you see and roughly how long you waited

9. Click "Stocks" in the top navigation, then click "AAPL" in the list (or go directly to
   `http://localhost:3255/stocks/AAPL`)
   - **Expect:** The page loads and shows "AAPL" — confirms an unrelated, frequently-used page still works
     after this iteration's backend changes

10. On `http://localhost:3255/backtest`, look for the text "n=8991" somewhere near the Return Attribution
    section (you may need to scroll)
    - **Expect:** The text "n=8991" is visible. This is a data-count check this iteration specifically
      refreshed and verified against the live database — confirms the page is still serving the real,
      current numbers

---

## What "Working Correctly" Looks Like

- The badge in the top-right corner is always either "Ready", an explicit initializing state, or "Backend
  unavailable" — never a blank header — and it stays "Ready" even while a backfill and its aggregate warm
  run in the background
- A single-day backfill's new data (step 3) resolves within about a minute and its scanner-run page shows
  a populated leaderboard, not an empty table — even though the background "Refreshed:" status for that
  same run may take much longer, or may not finish in your session at all when the day being filled is an
  old historical gap (expected this iteration, disclosed above)
- `/backtest` never shows a blank or endlessly-spinning screen, even during a heavy background warm — it
  either shows real numbers or an honest "Refreshing…" note
- `/api/health` always returns HTTP 200, even under heavy load — this is the reliability property this
  iteration's real point is proving, independent of whether the backfill itself finishes quickly

## Common Issues

- **Blank page / error screen:** confirm the backend is actually up —
  `curl http://localhost:8255/api/health` should return HTTP 200 with JSON, not a connection error
- **"Start" button stays disabled:** both date fields must contain a valid `yyyy-MM-dd` date before the
  button becomes clickable
- **"Backfill gaps" (step 2) shows a different number than "around 2,530":** expected — this count
  decreases by one every time any historical gap gets filled, including by earlier testing this same
  session. Only flag it if the panel is blank, shows an error, or the number is wildly different (e.g.
  zero, negative, or in the tens of thousands)
- **A job's "Refreshed:" text (step 8) never fully completes:** expected right now specifically for an
  OLD/historical missing day — this iteration intentionally did not speed up that case (only NEW,
  more-recent days got faster). Only flag this if the ACTUAL new-day data or the scanner-run leaderboard
  itself fails to appear — that part should always finish in well under a minute
- **`/api/health` responses look slow or occasionally miss 200 (step 6):** flag any non-200 response
  immediately — that would be a real regression. A `took` value that's occasionally a bit high is worth
  noting but is not automatically a failure; report the actual numbers
- This iteration made no application-code UI changes, so any UI difference from what you remember seeing
  before is unexpected — if something looks different, flag it
