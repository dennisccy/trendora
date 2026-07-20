# Phase goal-ops-hardening-iter-2 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-2
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend already running with at least one completed backfill/scan in its database (so Run history,
  Snapshot dates, and the Dashboard's Market Phase card have something to show)
- No login is required
- For step 6 only: terminal access to restart the backend via `scripts/start-backend.sh` (a single
  documented command — skip step 6 if you don't have terminal access; the rest of the guide still works)

---

## Verification Steps

1. Open `http://localhost:3255/data` in your browser
   - **Expect:** The "Data Manager" heading loads, the "Dataset coverage" panel shows 7 stat tiles with
     real numbers (not blank), and no red "Backend unavailable" error card appears

2. Under the coverage tiles, read the "Gap range: X → Y" line (or, if it instead says "no backfill
   gaps," use the date `2026-05-15`). In the "Start a fetch / backfill job" form, type that date into
   both the "Start date" field and the "End date" field, leave "Job kind" set to "Backfill snapshots,"
   then click the "Start" button
   - **Expect:** The "Job progress" panel appears with a spinning "running" status badge

3. Wait for the job to finish (watch the status badge)
   - **Expect:** The badge settles to "ok" (or "no new snapshots" if that day was already covered), and
     a new line reading **"Refreshed: coverage, market phase, membership timeline, research hot keys"**
     (or a similar comma-separated list) appears directly under the "N calendar days · ..." line — this
     is the phase's headline new capability

4. Refresh the page (press F5), then scroll down to the "Run history" table at the bottom and find the
   row matching the date you entered
   - **Expect:** That row's "Snapshots" column shows the SAME "Refreshed: ..." line you saw in step 3 —
     confirms the value was saved to storage, not just shown once live

5. In the top bar, click the as-of date button (it reads "Latest") to open the calendar, then pick an
   older date that already has data (not the newest one)
   - **Expect:** The "Dataset coverage" tiles immediately show that older date's real, non-zero numbers
     — NOT an all-zero or blank panel. (This exact behavior was almost broken by this iteration; it was
     caught and fixed before release, so it is the most important regression to double-check.) Click the
     date button again and pick the newest date (or click the "▶" arrow next to the date button) to
     return to "Latest" — the tiles should instantly show your original numbers again

6. *(Optional — needs terminal access)* Restart the backend: stop it, then run `scripts/start-backend.sh`
   again. The instant it comes back up (top-bar badge reads "Ready"), reload
   `http://localhost:3255/data`
   - **Expect:** The coverage tiles fill in almost instantly (well under a second) with the exact same
     numbers as before the restart — no multi-second wait like this page used to have

7. Navigate to `http://localhost:3255/`
   - **Expect:** The "Dashboard" heading loads and the "Market Phase & Severity" card shows a phase badge
     (e.g. "Expansion" or "Pullback") — NOT a "Market phase unavailable" message

8. Navigate to `http://localhost:3255/scanner-runs`
   - **Expect:** The "Scanner Runs" heading loads and the date you backfilled in step 2 appears as a row
     in the list — NOT "No scanner runs yet"

---

## What "Working Correctly" Looks Like

- After a backfill/rebuild job finishes, a small muted line "Refreshed: ..." appears under the existing
  breakdown line — both live in the Job progress panel and later in the Run history table row — and it
  uses plain words ("market phase," not "market_phase")
- Stepping the top-bar as-of date control back to any older, already-ingested date always shows that
  date's real numbers on `/data` — it never flashes to an all-zero "nothing here" panel
- A fresh page load of `/data` (especially right after a backend restart) shows the coverage numbers
  almost instantly, not after a multi-second wait

## Common Issues

- **"Backend unavailable" red card on `/data`**: the backend isn't running or crashed — check
  `curl http://localhost:8000/api/health` (or the configured backend port) and restart it
- **Old date shows all zeros on the coverage panel**: this is the exact defect this iteration fixed —
  if you see it, the fix has regressed; flag it immediately as a P1 failure (see UT-05 in the full test
  plan)
- **"Refreshed: ..." line never appears after a backfill finishes**: confirm the job's "Job kind" was
  "Backfill snapshots" (or "Fetch + backfill") and its status badge is "ok," not "failed" or
  "interrupted" — the line is only ever populated for a cleanly finished backfill-like job
