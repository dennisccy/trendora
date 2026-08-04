# Phase goal-ops-hardening-iter-46 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-46
**Time required:** ~10 minutes (longer than usual — this iteration fixed a memory-safety bug, not a
speed bug, and the live database currently makes it hard to get a fast happy-path confirmation; you're
verifying the reliability side and honestly recording the speed side)
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running via `scripts/start-backend.sh` (not `dev.sh`) and reachable at
  `http://localhost:8255/api/health`
- No login required
- No new seed data required — the committed DB already has what you need
- A terminal, for two `curl` timing checks (steps 6 and 8) and to confirm a date is unsnapshotted (step 3)

---

## Verification Steps

This iteration shipped **no new feature and no frontend code change at all** — confirmed: zero files
under `apps/frontend/` changed. It fixed two places in the backend where loading the Evidence page (or
running certain research computations) could build up an unbounded amount of memory instead of processing
data in bounded pieces, and closed the last two spots where a rare logging failure could crash a job
silently instead of recording it safely. There is nothing new to click.

**Before you start, know this — it changes what you should expect below:** this iteration's own developer
already tried the exact scenario this fix targets (loading the Evidence page while a heavy backfill runs)
and reported HONESTLY that it did **not** fully meet the strict pass bar — not because of a memory crash
(zero were logged), but because a single, unrelated, already-existing slow computation hogs the whole
Python process (a "GIL contention" issue) while a historical backfill's finalize step runs. **This guide
also found, in a fresh check just before writing it, that the Evidence page can be slow (over two minutes,
no response) even with NOTHING else running** — so do not be surprised if `/evidence` is slow for you too.
What you ARE checking is: (1) does it ever actually crash with a memory error, and (2) does the rest of
the app (the badge, `/backtest`) stay usable even while `/evidence` itself is slow.

1. Open `http://localhost:3255/` in your browser
   - **Expect:** The top-bar badge in the upper right reads "Ready" with a green dot; the page also shows
     the text "provider: seed" somewhere — never a blank header

2. Click "Data Manager" in the left sidebar (or go directly to `http://localhost:3255/data`)
   - **Expect:** The "Start a fetch / backfill job" panel is visible with "Start date" / "End date"
     fields, a "Run history" section below it, and a "Backfill gaps" stat showing a number around 2,531
     (the exact figure may have moved slightly since this guide was written — every backfill of a missing
     historical day lowers it by one, so a nearby number is fine; a blank panel or an error is not)

3. Open `http://localhost:3255/evidence` in a NEW tab, right now, before starting anything else, and start
   a stopwatch
   - **Expect:** Eventually either the 7 evidence claim rows render, or a "Backend unavailable" message
     appears. **Record how long it actually took** — this guide's own check found this can take over two
     minutes with nothing else running. That is a real, currently-open finding, not something you did
     wrong. Only flag it as broken if the tab NEVER resolves (stays on a loading skeleton forever, even
     after 5+ minutes) or shows a genuinely blank/crashed page — a long wait that eventually resolves is
     the expected-but-concerning result right now

4. Back on `http://localhost:3255/data`, pick a historical trading day not already in the "Run history"
   list or `/scanner-runs`. Try `2019-02-25` first (confirmed missing when this guide was written — it is
   the closest missing day to this database's current "latest filled" boundary, and a recent attempt on
   this SAME date already failed with a memory error, so retrying it is the most informative thing you can
   do). If it's no longer missing by the time you try it, look at the "Backfill gaps" number from step 2,
   or just try a day a week or two earlier, e.g. `2019-02-18`. Type it into both "Start date" and
   "End date", then click the "Start" button
   - **Expect:** The "Job progress" panel starts moving (status changes to "running", the live-activity
     line updates). Watch for whether it fails again — if it does, check whether the failure message now
     names a clear reason (this iteration specifically fixed two logging spots so failures are recorded,
     not silently dropped)

5. While that job keeps running, watch the top-bar badge for a couple of minutes, and separately reload
   `http://localhost:3255/backtest` in a second tab
   - **Expect:** The badge still reads "Ready" the whole time — never "Backend unavailable". The
     `/backtest` tab renders promptly — either normal evidence values, or a banner reading "Refreshing —
     showing the last complete evidence" — never a blank page or a screen that never finishes loading. (It
     is normal to see the "Refreshing" banner immediately, even before this job affects anything — an
     earlier, unrelated backfill already left the evidence in a "refreshing" state)

6. Open a terminal and run this three times, about 10 seconds apart, while the job from step 4 is still
   running:
   `curl -s -o /dev/null -w "%{http_code} took %{time_total}s\n" http://localhost:8255/api/health`
   - **Expect:** Every line shows `200`, though the `took` time may occasionally be a few seconds instead
     of instant — this iteration's own developer testing found health checks stayed reachable throughout a
     similar heavy job, even when individual polls were slow. Report the exact numbers you see; only flag
     a response that is NOT `200`

7. Look for the text "n=14647" somewhere near the Return Attribution section on the `/backtest` tab (you
   may need to scroll)
   - **Expect:** The text "n=14647" is visible exactly as written. This number must stay byte-identical
     after this iteration's backend refactor — this is a direct check that the fix didn't change any
     served value, not just that the page loads

8. In your terminal, run this once:
   `curl -s -o /dev/null -w "%{http_code} took %{time_total}s\n" http://localhost:8255/api/evidence`
   (it may take a while to return — that's expected right now per step 3's finding)
   - **Expect:** Eventually a `200`. Report how many seconds it took. A very long wait (even a minute or
     more) is a known, disclosed, currently-open finding — only flag it as urgent/new if it returns
     anything OTHER than `200` (e.g. a connection error, a 500) or if it never returns at all after several
     minutes

9. Click "Stocks" in the top navigation, then click "AAPL" in the list (or go directly to
   `http://localhost:3255/stocks/AAPL`)
   - **Expect:** The page loads and shows "AAPL" — confirms an unrelated, frequently-used page still works
     after this iteration's backend changes

10. Find the "Run history" row for the job you started in step 4
    - **Expect:** Its "Refreshed:" text lists at least "latest snapshot" and "coverage" if it succeeded, or
      an explicit failure state if it didn't. It may still read something short of complete even several
      minutes later — that matches this session's own disclosed, intentional limitation for backfilling an
      OLD missing day (a slow, pre-existing recompute path this iteration did not speed up). This is
      expected behavior right now, not something to flag as newly broken. Write down the literal text you
      see and roughly how long you waited

---

## What "Working Correctly" Looks Like

- The badge in the top-right corner is always either "Ready", an explicit initializing state, or "Backend
  unavailable" — never a blank header — and it stays "Ready" even while a backfill runs in the background
- `/api/health` always returns HTTP 200, even under heavy load — the badge and health check are the
  reliability property that keeps working right now
- `/api/evidence` and the `/evidence` page eventually load — possibly slowly (this iteration's own honest,
  disclosed finding) — but they must NEVER return a memory-error crash or a permanently blank page.
  "Slow but eventually correct" is the expected result today; "crashes with a memory error" or "the app
  itself goes fully unreachable" would be a genuine regression
- `/backtest` never shows a blank or endlessly-spinning screen, even during a heavy background warm — it
  either shows real numbers or an honest "Refreshing…" note
- The "n=14647" figure on `/backtest` renders exactly as written — this iteration's refactor is required
  to produce byte-identical output

## Common Issues

- **Blank page / error screen:** confirm the backend is actually up —
  `curl http://localhost:8255/api/health` should return HTTP 200 with JSON, not a connection error
- **"Start" button stays disabled:** both date fields must contain a valid `yyyy-MM-dd` date before the
  button becomes clickable
- **"Backfill gaps" (step 2) shows a different number than "around 2,531":** expected — this count
  decreases by one every time any historical gap gets filled, including by earlier testing this same
  session. Only flag it if the panel is blank, shows an error, or the number is wildly different (e.g.
  zero, negative, or in the tens of thousands)
- **`/evidence` (steps 3 and 8) takes a long time to load:** expected and already disclosed by this
  session's own testing (over two minutes observed with nothing else running). Only flag this as a NEW
  problem if it returns an error/crash, or if it genuinely never returns after several minutes of waiting
- **A backfill on `2019-02-25` (step 4) fails again with a memory error:** worth flagging specifically —
  this exact date already failed with a memory error once before this iteration's fix; if it fails the
  SAME way again, that is directly relevant evidence about whether this iteration's fix actually worked.
  If it fails with a DIFFERENT, clearly-logged reason, that's a smaller but still real finding (the
  logging fix working as intended)
- **A job's "Refreshed:" text (step 10) never fully completes:** expected right now specifically for an
  OLD/historical missing day — this iteration did not speed up that case, only fixed its memory behavior.
  Only flag this if the app becomes unresponsive (badge goes to "Backend unavailable" and stays there) —
  a slow-but-alive app is the expected, disclosed state
- **`/api/health` responses look slow or occasionally miss 200 (step 6):** flag any non-200 response
  immediately — that would be a real regression. A `took` value that's occasionally a bit high is worth
  noting but is not automatically a failure; report the actual numbers
- This iteration made no application-code UI changes, so any UI difference from what you remember seeing
  before is unexpected — if something looks different, flag it
