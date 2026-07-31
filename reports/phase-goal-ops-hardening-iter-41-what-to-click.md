# Phase goal-ops-hardening-iter-41 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-41
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode — standing in for ui-test-designer per SPEED-24)

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and reachable at `http://localhost:8255/api/health`
- No login required
- No new seed data required — the seeded May 2026 basis already supports the backfill check below

---

## Verification Steps

This iteration shipped **no new feature** — it repaired the automated test pipeline and shrank one
internal memory footprint. There is nothing new to click. This guide instead confirms the six
required-still-passing journeys named in this iteration's spec still work, since that verification is
the whole point of the fix.

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

4. Scroll down to "Run history"
   - **Expect:** A row appears for the `2026-05-02 → 2026-05-29` range with a Kind, Status, and
     Snapshots count

5. Refresh the page (press F5)
   - **Expect:** The same run row is STILL listed in "Run history" after the reload — job history
     survived the refresh, it does not reset to empty

6. Click "Scanner Runs" in the top navigation (or go to `http://localhost:3255/scanner-runs`), then
   click the row for `2026-05-29`
   - **Expect:** The Scanner Run detail page opens and shows a populated leaderboard table — not
     "No stored stock rows"

7. Click "Backtest" in the top navigation (or go to `http://localhost:3255/backtest`)
   - **Expect:** The page renders evidence values without a blank or frozen screen — either normal
     values, or (if a backfill's finalize step is still running) a banner reading "Refreshing — showing
     the last complete evidence"

8. Look at the top-bar badge one more time
   - **Expect:** Still reads "Ready" — with an extra "background compute running (N)" chip next to it
     only if a compute window happens to still be in flight from step 7; otherwise no extra chip

---

## What "Working Correctly" Looks Like

- The badge in the top-right corner is always either "Ready", an explicit initializing state, or
  "Backend unavailable" — never a blank header with nothing in it
- A backfill you start on `/data` finishes, and its row is still in "Run history" after you refresh the
  page — job history is never lost on reload
- `/backtest` never shows a blank or endlessly-spinning screen — it either shows real numbers or an
  honest "Refreshing…" note

## Common Issues

- **Blank page / error screen:** confirm the backend is actually up —
  `curl http://localhost:8255/api/health` should return HTTP 200 with JSON, not a connection error
- **"Start" button stays disabled:** both date fields must contain a valid `yyyy-MM-dd` date before the
  button becomes clickable
- **Run history row never appears:** wait for the "Job progress" panel to leave the "running" state
  first — the row is added once the job resolves, not while it is still in flight
- This iteration made no application-code UI changes, so any UI difference from what you remember seeing
  before is unexpected — if something looks different, flag it, since none of the changes in this
  iteration were supposed to touch the frontend at all
