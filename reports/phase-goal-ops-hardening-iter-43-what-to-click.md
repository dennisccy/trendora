# Phase goal-ops-hardening-iter-43 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-43
**Time required:** ~5-10 minutes (longer than usual — this iteration's whole point is a live memory/
latency re-verification, not a quick click-through)
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and reachable at `http://localhost:8255/api/health`
- No login required
- No new seed data required — the committed seed basis already supports every check below
- A terminal, for two `curl` timing checks (steps 7 and one follow-up)

---

## Verification Steps

This iteration shipped **no new feature** — it reverted a proven-net-negative memory optimization,
closed a job-launch silent-failure gap, extended host-guard coverage to the frontend launch script,
and live re-verified the two journeys (J-05, J-07) that failed last iteration against the owner's
raised memory cap. There is nothing new to click. This guide instead confirms those two target
journeys plus the most exposed regression points, in the time you have.

**Before you start, know this:** the developer's own live test this session found that while the
system stayed memory-safe and available under a heavy load, `/api/health` sometimes answered slowly
(over the intended 2-second ceiling) during that load, and this was NOT fixed this iteration — it is
an open, disclosed finding. Step 7 below is your chance to reproduce or clear that concern. Report
what you actually observe, not what you expect to see.

1. Open `http://localhost:3255/` in your browser
   - **Expect:** The top-bar badge in the upper right reads "Ready" with a green dot; the page also
     shows the text "provider: seed" somewhere — never a blank header

2. Click "Data Manager" in the left sidebar (or go directly to `http://localhost:3255/data`)
   - **Expect:** The "Start a fetch / backfill job" panel is visible with "Start date" / "End date"
     fields, and a "Run history" section is present below it

3. Type `2005-04-12` in "Start date" and `2005-04-12` in "End date", then click the "Start" button
   (accent button, play icon)
   - **Expect:** The "Job progress" panel moves off "running" within about a minute. Then navigate to
     `http://localhost:3255/scanner-runs/1882` — it should show "as of 2005-04-12" with a populated
     leaderboard table

4. Back on `http://localhost:3255/data`, type `2025-06-01` in "Start date" and `2026-07-17` in "End
   date" (a wide, 412-day range), then click "Start"
   - **Expect:** No "date range too large" (or similar rejection) message appears. The "Job progress"
     panel shows a running state with visible movement — the wide range is accepted and starts
     executing; it is NOT rejected. This job also kicks off the heavy background compute the next
     steps watch.

5. While that job keeps running, watch the top-bar badge for a couple of minutes
   - **Expect:** Still reads "Ready" the whole time — it should never flip to "Backend unavailable"
     while the heavy job runs in the background

6. Still while it runs, open `http://localhost:3255/backtest` in a second tab
   - **Expect:** The page renders promptly — either normal evidence values, or a banner reading
     "Refreshing — showing the last complete evidence" — never a blank page or a screen that never
     finishes loading

7. Open a terminal and run this three times, about 10 seconds apart, while the job from step 4 is
   still running:
   `curl -s -o /dev/null -w "%{http_code} took %{time_total}s\n" http://localhost:8255/api/health`
   - **Expect:** Every line shows `200`. The `took` time is the important number this iteration left
     unresolved — it SHOULD be under 2 seconds, but a prior live test this session saw responses as
     slow as 6.6 seconds during the same kind of heavy job. If you see anything over ~2 seconds,
     that is not automatically "broken" (it is a known, disclosed open issue) — just report the exact
     number you saw rather than assuming it is fine

8. Go to `http://localhost:3255/data` and scroll to the "Background compute" panel
   - **Expect:** If a window is in flight, it lists that window with elapsed time and horizons
     done/total, and the panel states its history is "process-lifetime only, never persisted" — never
     a blank panel with no explanation

9. Once the job from step 4 finishes, reload `http://localhost:3255/data` and find its "Run history"
   row
   - **Expect:** The row's summary includes "412 calendar days" (confirms the full wide range
     processed, not a truncated subset) and its "Refreshed:" text is not blank

10. Click "Stocks" in the top navigation, then click "AAPL" in the list (or go directly to
    `http://localhost:3255/stocks/AAPL`)
    - **Expect:** The page loads and shows "AAPL" — confirms an unrelated, frequently-used page still
      works after this iteration's backend changes (watch for it loading noticeably slower than you
      remember — this iteration widened exposure to a known, separately-tracked slow-path affecting
      per-symbol pages)

---

## What "Working Correctly" Looks Like

- The badge in the top-right corner is always either "Ready", an explicit initializing state, or
  "Backend unavailable" — never a blank header — and it stays "Ready" even while a large backfill and
  its aggregate warm run in the background
- A single-day backfill (step 3) resolves within about a minute and its target scanner-run page shows
  a populated leaderboard, not an empty table
- A wide, multi-month date range on `/data` (step 4) is accepted and starts running — it is never
  rejected for being "too large"
- `/backtest` never shows a blank or endlessly-spinning screen, even during a heavy background warm —
  it either shows real numbers or an honest "Refreshing…" note
- `/api/health` always returns HTTP 200, even under heavy load — but its RESPONSE TIME during that
  load is the one open question this iteration did not close; report the real number

## Common Issues

- **Blank page / error screen:** confirm the backend is actually up —
  `curl http://localhost:8255/api/health` should return HTTP 200 with JSON, not a connection error
- **"Start" button stays disabled:** both date fields must contain a valid `yyyy-MM-dd` date before
  the button becomes clickable
- **A job's "Run history" row never leaves "running":** this is the EXACT regression this iteration's
  thread-launch guard was meant to fix (a launch failure should now mark the job "failed" with a
  message, never leave it silently stuck) — if you see a row stuck at "running" with no progress for
  many minutes, flag it, it should not happen anymore
- **Badge goes to "Backend unavailable" while a job runs:** this is the exact regression this
  iteration's `_BarCache.prefill` revert and raised memory cap target — if you can reproduce it, flag
  it, it means the fix did not hold
- **`/api/health` responses over 2 seconds during the heavy job (step 7):** expected to be an open,
  disclosed issue this iteration — report the number, do not treat it as a silent pass or a hard
  failure on its own
- This iteration made no application-code UI changes, so any UI difference from what you remember
  seeing before is unexpected — if something looks different, flag it
