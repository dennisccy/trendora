# Demo Script — goal-ops-hardening-iter-3

**Mode:** record
**Date:** 2026-07-20
**Frontend URL:** http://localhost:3255
**Iteration:** 3

## Highlights

### Step 01 — Open the Data Manager

- **Narration:** Let's start on the Data Manager page, where the app shows exactly how much market data it has and lets you grow it on demand.
- **Action:** Navigate to /data
- **Point out:** The Dataset coverage panel is already filled in with real figures — Universe, Symbols, Trading days, Snapshot dates, and Backfill gaps — nothing blank and nothing stuck loading.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-3/step-01.png

### Step 02 — Pick a job type

- **Narration:** The "Job kind" dropdown offers three plain-language choices for growing the dataset. Let's pick "Fetch EOD prices" first.
- **Action:** Type "Fetch EOD prices" into the "Job kind" field
- **Point out:** As soon as a fetch-style job is chosen, an "Import source" dropdown appears, since a fetch needs to know where to pull prices from.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-3/step-02.png

### Step 03 — Switch to a backfill job

- **Narration:** Now let's switch to "Backfill snapshots" instead, since that's the job we'll actually run next.
- **Action:** Type "Backfill snapshots" into the "Job kind" field
- **Point out:** The Import source dropdown disappears again — the form only ever asks for what the chosen job actually needs.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-3/step-03.png

### Step 04 — Run a backfill job

- **Narration:** With a real multi-day range already filled in from the app's own list of gaps, clicking Start kicks off the job.
- **Action:** Click the "Start" button
- **Point out:** A plain-language breakdown appears — how many calendar days, how many were already covered, how many weren't trading days — and a "Refreshed" note lists exactly which stored figures this run kept current, with the Snapshot dates and Backfill gaps tiles above updating to match, no reload needed.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-3/step-04.png

### Step 05 — Check the run history

- **Narration:** Scrolling down to the Run history table shows a permanent log of every job that's ever run.
- **Action:** Click the "Run history" heading
- **Point out:** This run's row carries the exact same "Refreshed" note — proof it's a durable record, not just a one-time message that vanishes on reload.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-3/step-05.png

### Step 06 — See input validation in action

- **Narration:** Finally, let's see what happens if a date is mistyped. Typing an impossible date should be caught right away, before it can ever be submitted.
- **Action:** Type "2026-13-40" into the "Start date" field
- **Point out:** A clear red message and warning icon appear immediately below the field explaining exactly what's wrong, and the Start button greys out until it's fixed.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-3/step-06.png
