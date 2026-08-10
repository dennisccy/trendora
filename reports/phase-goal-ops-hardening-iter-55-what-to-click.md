# Phase goal-ops-hardening-iter-55 — What to Click (Operator Verification Guide)

**Time required:** ~5 minutes (plus job wait time noted below)
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running (`scripts/start-backend.sh`) and reachable
- No login required
- This iteration shipped **zero frontend code changes** — every step below is a regression/reliability
  check of already-shipped pages, not a new feature

---

## Verification Steps

1. Open `http://localhost:3255/data` in your browser
   - **Expect:** Page loads, no blank screen or error boundary; the readiness pill in the top-right of the
     header shows `data-state="ready"` (hover/inspect, or just confirm it does NOT read "Backend
     unavailable" or "Checking backend…")

2. Look at the "Start a fetch / backfill job" panel — leave "Start date" and "End date" as their
   pre-filled values, confirm "Job kind" reads "Backfill snapshots"
   - **Expect:** The "Start" button (with a play icon) is enabled, not greyed out

3. Click the "Start" button
   - **Expect:** The "Job progress" card appears with a status badge showing a spinner and "running…"

4. Watch the readiness pill (top-right header) and the banner just below it while the job runs, for the
   next several minutes — this is the iteration's own target and its known, disclosed miss
   - **Expect:** The pill may occasionally flip to "Backend unavailable" and recover — this iteration's own
     measured drill saw 11 such moments out of 1,839 one-second polls (worse than the prior 6/1,822, root
     cause disclosed in `reports/perf-budgets.md` Addendum 19). A brief flip-and-recover is the KNOWN
     condition, not a new bug. A flip that never recovers after the job finishes IS a new bug — report it.

5. Once the job's status badge reaches a terminal, non-spinner label (e.g. "ok") — this can take several
   minutes for a job that runs a full forward-aggregate warm — read the "Refreshed: …" line just below it
   - **Expect:** The text includes "forward aggregates" among the comma-separated categories (e.g.
     "coverage, market phase, forward aggregates, latest snapshot, …") — this confirms the honest-status fix
     did not break the normal, all-horizons-complete path

6. Refresh the page (F5 or Cmd+R)
   - **Expect:** The same "Refreshed: …" line and job outcome are still shown — data persisted, nothing lost

7. Click "Backtest" in the left sidebar
   - **Expect:** Navigate to `http://localhost:3255/backtest`; the forward-test scorecard renders with real
     numeric rows (not placeholders or "—"), and the evidence section shows a real "Snapshots contributing"
     count

8. Click "Dashboard" in the left sidebar
   - **Expect:** Navigate to `http://localhost:3255/`; the readiness pill appears again in the same header
     position, in the same state as it settled on `/data`/`/backtest`

---

## What "Working Correctly" Looks Like

- The "Refreshed: …" line on `/data` lists "forward aggregates" after a normal (uninterrupted) backfill —
  the fix did not break the common case
- The readiness pill and banner recover to "ready"/"GO" shortly after any job finishes, even if they flip
  briefly during it
- `/backtest`'s scorecard and evidence numbers look identical to what you'd expect from before this
  iteration (this iteration promises byte-identical output, not new numbers)

## Common Issues

- **Blank page / error screen on `/data` or `/backtest`**: check the backend is running
  (`curl http://localhost:3255/api/health` should return HTTP 200 — if it hangs or errors, the backend
  process itself may be down, not just slow)
- **Readiness pill stuck on "Backend unavailable" AFTER the job has finished (does not recover)**: this is
  a genuine regression, not the known disclosed flip-and-recover behavior above — capture a screenshot and
  the job's ID from the "Job progress" card
- **"Refreshed: …" line missing "forward aggregates" after a job that showed NO error/warning**: this would
  be a real defect in the honest-status fix (it should only omit the category when a horizon genuinely
  failed) — capture the job's ID and the exact "Refreshed: …" text shown
- **This iteration cannot be verified to have closed the health-badge reliability gap** — it explicitly did
  not (see step 4). Do not treat a brief flip during a job as a failure of this checklist.
