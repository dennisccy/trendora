# Phase goal-ops-hardening-iter-9 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-9
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Backend running at `http://localhost:8255` (launched via `scripts/start-backend.sh` — this is the launch
  script this iteration hardened; launching any other way does not exercise this iteration's fix)
- Frontend running at `http://localhost:3255`
- No login required
- Pick a historical trading day with no existing scanner snapshot. `2026-05-15` is used below — before you
  start, check the "Snapshot dates" figure and gaps on `/data`'s coverage panel; if `2026-05-15` is already
  covered, substitute any other date shown as a gap.

**Note:** this iteration shipped no new UI feature — the point of this check is to confirm the four already-
shipped journeys (backfill → cached aggregates, no range cap, visible boot status, crash handling) still
work exactly as before, now that the backend's launch scripts apply host-safety CPU/memory caps.

---

## Steps

1. Open `http://localhost:3255/data` in your browser
   - **Expect:** The "Data Manager" page loads with a "Dataset coverage" panel showing numbers (not a blank
     page or a red "Backend unavailable" card)

2. In the "Start a fetch / backfill job" panel, type `2026-05-15` into both the "Start date" and "End date"
   fields, leave "Job kind" set to "Backfill snapshots", then click the "Start" button
   - **Expect:** The "Job progress" panel appears below and shows a status badge that starts animating
     (spinning icon, status "running")

3. Wait for the job to finish (watch the "Job progress" panel — do not refresh the page)
   - **Expect:** The status badge settles on "ok" (green), and a line appears reading "Refreshed:" followed
     by a list of names like "latest date snapshot, coverage payload, ... market phase, ..." — this proves
     the new day's aggregates were actually written to storage, not silently skipped

4. Navigate to `http://localhost:3255/scanner-runs`
   - **Expect:** A row showing the date `May 15, 2026` appears in the table immediately, with a Regime badge
     and non-zero counts in the Actionable/Breakout-watch/Pullback-watch/Stocks columns — no blank row, no
     loading spinner stuck in place

5. Click the `May 15, 2026` date link in that row
   - **Expect:** The "Scanner Run" detail page opens and shows a leaderboard table of stocks with score/status
     badges — not a "Run not found" message

6. Navigate back to `http://localhost:3255/data`, and start a second backfill for the exact same range
   (`2026-05-15` to `2026-05-15`, "Backfill snapshots")
   - **Expect:** This time the status badge reads "no new snapshots" with a grey/neutral color — visually
     different from step 3's green "ok" — because that day is now already covered (a zero-work re-run must
     never look like a fresh success)

7. Look at the top of the page (any page) — the small colored pill in the top bar
   - **Expect:** It reads "Ready" in green. Below it, a thin green banner strip reads "GO — today's board is
     current."

8. Stop the backend process (kill it), then watch the same page WITHOUT reloading
   - **Expect:** Within a few seconds, the thin green banner is replaced by a loud red banner reading exactly
     "NO-GO — do not rely on today's board." with the reason "Backend is unavailable — the preflight check
     could not run." listed underneath

9. Restart the backend via `scripts/start-backend.sh`, and immediately watch the top-bar pill without
   reloading the page
   - **Expect:** The pill briefly shows an amber "Initializing… history n/m" state (a progress fraction)
     before turning back to green "Ready" — never a bare "Backend unavailable" during this window

10. Once "Ready" is showing again, navigate to `http://localhost:3255/data` and type `2025-06-01` into
    "Start date" and `2026-07-17` into "End date" (more than a year apart), then click "Start"
    - **Expect:** The job is accepted and starts running (no "date range too large" error message) — the
      "Job progress" panel shows a "chunk 1/N" badge and a progress bar advancing

---

## What "Working Correctly" Looks Like

- A backfill for a new day always ends in a clearly labeled "ok" state with a non-empty "Refreshed: ..."
  list — never a silent partial result
- Re-running the exact same range shows a visually distinct "no new snapshots" outcome, never the same green
  badge as a productive run
- The top-bar badge and the banner always show what's really happening (Ready/GO, Initializing…, or
  NO-GO) — you should never see a blank page or a frozen "Checking backend…" state for more than a few
  seconds

## Common Issues

- **Red "Backend unavailable" card on `/data` or `/scanner-runs`**: the backend process is not running or
  not reachable at `http://localhost:8255` — confirm it was started with `scripts/start-backend.sh` and
  check its terminal output for a crash.
- **Job stuck on "running" forever**: check the backend's terminal/log for a crash; if the backend died, its
  affected job should show "interrupted" in the "Unfinished imports" panel on `/data` after a restart and
  reload — a still-"running" row with no living backend process is the bug this iteration hardened against.
- **"Start" button stays disabled**: the typed date is not a valid `yyyy-MM-dd` value (e.g. `2026-13-40`) — a
  red message "Enter a valid date as yyyy-MM-dd" appears below the field; fix the date to enable the button.
- **Banner never turns to NO-GO after killing the backend**: wait one full health-poll cycle (a few seconds)
  before concluding it's broken — the banner updates on the next poll, not instantly.
