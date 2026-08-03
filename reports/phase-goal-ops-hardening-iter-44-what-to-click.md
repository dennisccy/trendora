# Phase goal-ops-hardening-iter-44 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-44
**Time required:** ~10 minutes (longer than usual — this iteration's whole point is confirming the
backend stays reachable during a heavy background compute that is now diagnosed but still slow)
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running via `scripts/start-backend.sh` (not `dev.sh`) and reachable at
  `http://localhost:8255/api/health`
- No login required
- No new seed data required — the committed seed basis already supports every check below
- A terminal, for one `curl` timing check (step 6) and to confirm a date is unsnapshotted (step 3)

---

## Verification Steps

This iteration shipped **no new feature and no frontend code change at all** (`git diff` confirms
zero files under `apps/frontend/` touched). It wired three previously-unenforced launcher settings
into the backend's startup script, live-diagnosed (but did not fix) the cause of a slow background
computation, fixed two backend error-message honesty gaps, and re-verified that heavy background work
doesn't take the service down. There is nothing new to click. This guide instead confirms the two
target journeys (a real never-before-snapshotted backfill, and the service staying reachable under
heavy load) plus a couple of the most-used pages.

**Before you start, know this:** the developer's own live test this session found — for the SECOND
time in two iterations — that a single-day historical backfill's background "finalize" step
(computing which stocks were eligible on which day, going back to 1996) can take 15+ minutes and may
still be running when you check. This is now explained (a full-history recompute runs on every
ingest) but NOT fixed. The new day's actual data and its scanner-run page still appear in well under
a minute — it's specifically the "Refreshed: forward aggregates" line and the Background Compute
panel that can stay incomplete for a long time. This is expected and disclosed, not a fresh bug.

1. Open `http://localhost:3255/` in your browser
   - **Expect:** The top-bar badge in the upper right reads "Ready" with a green dot; the page also
     shows the text "provider: seed" somewhere — never a blank header

2. Click "Data Manager" in the left sidebar (or go directly to `http://localhost:3255/data`)
   - **Expect:** The "Start a fetch / backfill job" panel is visible with "Start date" / "End date"
     fields, and a "Run history" section is present below it

3. Pick a historical trading day NOT already in the "Run history" list or `/scanner-runs` (e.g. try
   `2019-02-26` — do not reuse `2005-04-12`, which prior iterations may already have snapshotted).
   Type it into both "Start date" and "End date", then click the "Start" button
   - **Expect:** The "Job progress" panel moves off "running" within about a minute — this confirms
     the new day's actual data lands quickly. Then click through to that run's scanner-run page from
     the "Run history" row — it should show "as of <your date>" with a populated leaderboard table

4. Back on `http://localhost:3255/data`, type `2025-06-01` in "Start date" and `2026-07-17` in "End
   date" (a wide, 412-day range), then click "Start"
   - **Expect:** No "date range too large" (or similar rejection) message appears. The "Job progress"
     panel shows a running state with visible movement — the wide range is accepted and starts
     executing; it is NOT rejected. This job also kicks off the heavy background compute the next
     steps watch.

5. While that job keeps running, watch the top-bar badge for a couple of minutes, and separately open
   `http://localhost:3255/backtest` in a second tab
   - **Expect:** The badge still reads "Ready" the whole time — never "Backend unavailable". The
     `/backtest` tab renders promptly — either normal evidence values, or a banner reading
     "Refreshing — showing the last complete evidence" — never a blank page or a screen that never
     finishes loading

6. Open a terminal and run this three times, about 10 seconds apart, while the job from step 4 is
   still running:
   `curl -s -o /dev/null -w "%{http_code} took %{time_total}s\n" http://localhost:8255/api/health`
   - **Expect:** Every line shows `200`. The `took` time should mostly be under 2 seconds — this
     iteration measured 93.3% of polls within that budget (a large improvement over last iteration's
     63.6%), so an occasional poll a bit over 2s is a known, disclosed open issue, not a failure —
     but report the exact numbers you see rather than assuming it's fine

7. Go to `http://localhost:3255/data` and scroll to the "Background compute" panel
   - **Expect:** If a window is in flight, it lists that window with elapsed time and horizons
     done/total, and the panel states its history is "process-lifetime only, never persisted". It is
     normal this iteration for "horizons done" to stay at 0 for many minutes while elapsed time keeps
     climbing — that reflects the newly-diagnosed slow finalize step, not a frozen panel

8. Find the "Run history" row for the job you started in step 3 (the single-day backfill)
   - **Expect:** Its "Refreshed:" text lists at least "latest snapshot" and "coverage". It may still
     read something short of complete even several minutes later — that matches this iteration's own
     disclosed finding that the background bookkeeping step can run 15+ minutes. This is expected
     behavior right now, not something to flag as newly broken

9. Click "Stocks" in the top navigation, then click "AAPL" in the list (or go directly to
   `http://localhost:3255/stocks/AAPL`)
   - **Expect:** The page loads and shows "AAPL" — confirms an unrelated, frequently-used page still
     works after this iteration's backend changes

10. On `http://localhost:3255/data`, find any job in "Run history" whose status is "failed" or
    "partial" (from a prior run) and, if a "Retry" button is present, click it
    - **Expect:** Either the retry starts a new run (status moves to "running"), or — if the backend
      genuinely can't launch it right now — you see a clear "temporarily unavailable" style message
      rather than a raw/blank server error. (If no failed/partial run exists to retry, skip this step
      — it is not required to complete the other 9.)

---

## What "Working Correctly" Looks Like

- The badge in the top-right corner is always either "Ready", an explicit initializing state, or
  "Backend unavailable" — never a blank header — and it stays "Ready" even while a large backfill and
  its aggregate warm run in the background
- A single-day backfill's new data (step 3) resolves within about a minute and its scanner-run page
  shows a populated leaderboard, not an empty table — even though the background "Refreshed:" status
  for that same run may take much longer to fully complete
- A wide, multi-month date range on `/data` (step 4) is accepted and starts running — it is never
  rejected for being "too large"
- `/backtest` never shows a blank or endlessly-spinning screen, even during a heavy background warm —
  it either shows real numbers or an honest "Refreshing…" note
- `/api/health` always returns HTTP 200, even under heavy load, and now stays within budget the large
  majority (but not 100%) of the time — that gap is a known, disclosed open issue this iteration
  improved but did not close

## Common Issues

- **Blank page / error screen:** confirm the backend is actually up —
  `curl http://localhost:8255/api/health` should return HTTP 200 with JSON, not a connection error
- **"Start" button stays disabled:** both date fields must contain a valid `yyyy-MM-dd` date before
  the button becomes clickable
- **A job's "Refreshed:" text never fully completes:** expected right now for a single-day backfill —
  this iteration diagnosed (but did not yet fix) why the background finalize step is slow. Only flag
  this if the ACTUAL new-day data or the scanner-run leaderboard itself fails to appear — that part
  should always finish in well under a minute
- **`/api/health` responses over 2 seconds during the heavy job (step 6):** expected to be an open,
  disclosed issue this iteration improved (93.3% within budget) but did not fully close — report the
  number, do not treat an occasional slow poll as a silent pass or a hard failure on its own. Any
  non-200 response, or a response taking many seconds, IS worth flagging as new
- **"Retry" button (step 10) returns a raw/blank server error instead of a clear message:** this is
  the exact regression this iteration's fix was meant to prevent — flag it if you see it
- This iteration made no application-code UI changes, so any UI difference from what you remember
  seeing before is unexpected — if something looks different, flag it
