# Phase goal-ops-hardening-iter-5 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-5
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Backend running in prod mode (`scripts/start-backend.sh`) — health check OK at
  `http://localhost:8255/api/health`
- Frontend running in prod mode (`scripts/start-frontend.sh`), reachable at `http://localhost:3255`
- The committed seed database is already warm/ingested — no setup needed
- No login required anywhere in this product

This iteration made one page dramatically faster (`/backtest`) and made backfill/rebuild jobs on `/data`
take a little longer to finish while quietly warming a new cache in the background. Nothing new was
added to click — you're confirming a speed fix and one new word in existing text.

---

## Steps

1. Open `http://localhost:3255/backtest` in your browser
   - **Expect:** Grey animated placeholder cards appear briefly, then within about 1-2 seconds real
     content replaces them: the heading "Backtest", a "Viewing as-of ... (latest)" badge, and a
     "Forward-test scorecard" table with rows for 1d/5d/10d/20d/60d showing real percentages
   - **Broken looks like:** the grey placeholder cards are still there after 10+ seconds, or a red
     "Backend unavailable" message appears

2. Scroll to the "Return attribution" heading and click the "20d" button in the row of horizon buttons
   next to it
   - **Expect:** The "20d" button highlights immediately, and the "Leadership cohorts" panels below
     relabel to "Fwd 20d" with different numbers than before — instant, no page reload

3. Open `http://localhost:3255/data` in a new tab (or navigate there)
   - **Expect:** Heading "Data Manager" loads, with a "Job progress" panel and a "Run history" table
     visible on the page

4. Scroll down to the "Rebuild snapshots for current universe" panel and note the date shown after "the
   latest snapshot" (e.g. "2026-06-15")
   - **Expect:** A real date is shown in that sentence

5. Scroll back up to "Start a fetch / backfill job," type that same date into both "Start date" and "End
   date," leave "Job kind" as "Backfill snapshots," then click "Start"
   - **Expect:** The job progress panel shows a spinning "running" badge, then finishes (likely as a
     "Zero-work outcome" note — that is normal, not a failure)

6. Once the job finishes, look directly below the "Snapshots backfilled" line
   - **Expect:** A line reading "Refreshed: ..." that includes the words **"forward aggregates"**
     somewhere in its comma-separated list (e.g., "Refreshed: coverage, market phase, forward
     aggregates, research hot keys")
   - **Broken looks like:** the "Refreshed: ..." line is missing entirely, or never includes "forward
     aggregates" after a Backfill/Fetch+backfill/Rebuild job

7. While that job was running, you should have seen a small "updated Ns ago" text near the progress bar
   - **Expect:** That text keeps resetting to a low number every second or two — never frozen on one
     number for 15+ seconds while the badge still says "running"

8. Navigate to `http://localhost:3255/` (Dashboard)
   - **Expect:** Heading "Dashboard" loads with real data (a market regime score, sector/theme info)
     within a few seconds — no blank page, no error

---

## What "Working Correctly" Looks Like

- `/backtest` populates its scorecard in about a second, not 30+ seconds
- The Data Manager's "Refreshed: ..." line includes "forward aggregates" after any Backfill/Fetch +
  backfill/Rebuild job, and the same wording shows up in the Run history table row too
- Every page you visit shows its heading and real data within a few seconds — nothing hangs or goes blank

## If Something Looks Wrong

- **`/backtest` stuck on grey placeholder cards for 10+ seconds:** the speed fix may not be active on
  this backend instance — confirm `scripts/start-backend.sh` was (re)started after this iteration's code
  changes, not a stale older process
- **"Refreshed: ..." line never shows "forward aggregates":** confirm the job kind was "Backfill
  snapshots," "Fetch + backfill," or "Rebuild snapshots for current universe" — a plain "Fetch EOD
  prices" job never runs this step, before or after this iteration, so it will never show this line
  changing
- **Blank page or error screen anywhere:** check the backend is actually running —
  `curl http://localhost:8255/api/health`
