# Phase goal-ops-hardening-iter-16 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-16
**Time required:** ~5 minutes for the core check (steps 1-3). Seeing the new "refreshing" disclosure live
is a real, honest bonus: it needs a live backfill that takes ~6-7 minutes end-to-end, so steps 4-7 are
optional and add that much time — they are not a 5-minute check.
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`, backend at `http://localhost:8255` — both already up for
  this session. No login required.
- For the optional steps 4-7 only: on `/data`, note one calendar date the coverage panel shows as a "gap"
  (not yet snapshotted), to use as a single-day backfill target.

---

## Verification Steps (core check — ~5 minutes)

1. Open `http://localhost:3255/backtest` in your browser
   - **Expect:** The page loads with the heading "Backtest" near the top. No red error card, no blank screen.

2. Look at the small status pill near the top of the page (backend readiness indicator)
   - **Expect:** It reads "Ready" in green. If it instead reads "Initializing…", the whole page is still
     background-warming and none of the checks below apply yet — wait and reload.

3. Scroll all the way to the bottom of the page, past the "Leadership cohorts" section
   - **Expect:** A section titled "Forward-tested evidence (expanding window ≤ `<today's date>`)" with
     normal populated tables (e.g. "Forward return by score bucket", "Excess vs benchmarks"). Right now it
     should look completely ordinary — no colored banner above it, and no "not yet computed" message in its
     place. This is the section this iteration changed; today's check confirms the everyday case still
     works exactly as before.

## Optional: watch the new "refreshing" disclosure happen live (+~7 minutes)

4. Navigate to `http://localhost:3255/data`. In the "Start a fetch / backfill job" card, type your chosen
   not-yet-snapshotted date into BOTH the "Start date" field and the "End date" field (making it a
   single-day job), leave "Job kind" set to "Backfill snapshots", then click "Start"
   - **Expect:** The "Job progress" card's status badge switches to "running" with a spinning icon.

5. Every ~30 seconds, reload `http://localhost:3255/backtest` and check the bottom of the page again
   - **Expect:** Within a few minutes, a small amber-colored card appears directly ABOVE "Forward-tested
     evidence," reading "Refreshing — showing the last complete evidence" plus a timestamp. The numbers
     below it should stay fully visible the entire time — never blank, never replaced by a spinner.

6. Keep reloading `http://localhost:3255/data` until the job's status badge reads "ok"
   - **Expect:** The job finishes; a line reading "Refreshed: forward aggregates" appears on the same job
     card.

7. Reload `http://localhost:3255/backtest` one more time
   - **Expect:** The amber "Refreshing" banner from step 5 is now gone, and the evidence numbers below are
     still shown normally — confirming the page updated itself automatically once the background job
     finished, with no extra action needed from you.

---

## What "Working Correctly" Looks Like

- The bottom "Forward-tested evidence" section ALWAYS shows exactly one of three things, never nothing:
  ordinary populated numbers (normal day), the same numbers with a small amber "Refreshing" banner above
  them (while new data is being processed in the background), or an explicit "Backtest evidence not yet
  computed" message (only ever expected on a brand-new, never-ingested install — not on this environment).
- The rest of the page (scan summary, scorecard, leadership lists near the top and middle) never changes
  appearance because of this feature — the disclosure is confined to the one bottom section.

## If Something Looks Wrong

- **Blank page / red "Backend unavailable" card**: confirm the backend is actually reachable
  (`http://localhost:8255`) and the frontend (`http://localhost:3255`) — do not attempt to start either
  service yourself if you are an automated agent; ask the operator.
- **The bottom section is completely blank with no banner and no message**: this is a bug — it should never
  render nothing.
- **The "Refreshing" banner never appears after starting the backfill in step 4**: reload `/data` and check
  the job's status badge actually reached "running" (not stuck on something else) — the disclosure feature
  can only be observed while an actual backfill job is genuinely in progress.
- **`/data` looks like it isn't loading or a screenshot of it looks blank**: this page is very long
  (renders roughly 17,800px tall) — scroll down manually rather than assuming the page failed; a full-page
  screenshot of it has been known to come back blank even when the page is fine.
