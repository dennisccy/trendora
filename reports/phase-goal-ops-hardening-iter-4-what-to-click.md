# Phase goal-ops-hardening-iter-4 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-4
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and reachable (e.g., started via `scripts/start-backend.sh`)
- No login required — this is a single-user local application
- No special seed data needed beyond the normal committed database (it already has some price
  history and at least one existing backfill gap)
- **Not covered by this quick guide:** this iteration's one brand-new badge message
  ("Snapshot pending") requires a specific database precondition that a plain 5-minute click session
  cannot create — it needs a developer/QA engineer to insert one row on an isolated database copy
  first. See `reports/phase-goal-ops-hardening-iter-4-ui-test-plan.md`'s UT-03 if you need to verify
  that exact state. This guide instead focuses on confirming nothing broke for everyday use, which
  is the higher-risk regression this iteration touches.

---

## Verification Steps

1. Open `http://localhost:3255` in your browser
   - **Expect:** The "Dashboard" page loads with its "The daily snapshot at a glance" subtitle. In the
     header, a status badge is visible (most commonly reading **"Ready"**), and a thin green strip
     reading **"GO — today's board is current."** appears directly below the header. No error page,
     no blank screen.

2. Read the header badge's exact text
   - **Expect:** It reads **"Ready"** or **"Initializing… history N/M"** — the everyday states. *(If
     it already reads "Snapshot pending — …", that's this iteration's new state — confirm its status
     dot is a calm, steady, non-red color, and the sentence names SPY, a specific date, and points to
     Data Manager.)*

3. Click **"Data Manager"** in the left sidebar
   - **Expect:** Navigates to `http://localhost:3255/data`. The "Data Manager" heading, a "Dataset
     coverage" panel, and a "Job progress" panel are all visible. No "Backend unavailable" card.

4. In "Start a fetch / backfill job," leave the pre-filled "Start date"/"End date" fields as they
   are, set "Job kind" to **"Backfill snapshots"**, then click **"Start"**
   - **Expect:** The "Job progress" panel's status badge starts spinning. A heartbeat line like
     "updated 2s ago" appears next to a short current-activity line, and the heartbeat keeps resetting
     to a low number every second or two.

5. Watch until the status badge settles (usually a few seconds to under a minute for the default
   seeded range)
   - **Expect:** Status reaches **"ok"** (or shows a "Zero-work outcome" note if there was nothing new
     to do). The heartbeat text never shows **"· possibly stalled"** while it was still "running".

6. Glance at the header badge again (still visible at the top of `/data`)
   - **Expect:** It reads EXACTLY what it did in step 2 — an ordinary backfill/fetch job must never
     flip it to **"Backend unavailable"**.

7. Press **F5** to hard-reload the page
   - **Expect:** The badge and the "Dataset coverage" numbers are unchanged from just before the
     reload — nothing reverts or blanks out.

---

## What "Working Correctly" Looks Like

- The header badge and the green "GO" strip appear on every page, never blank.
- Starting an ordinary backfill/fetch job never flips the header badge to "Backend unavailable" —
  that used to be possible before this iteration's fix and must not happen now.
- The job card's heartbeat text keeps ticking every 1–2 seconds while a job runs, with no
  "· possibly stalled" while the job is healthy.
- Everything survives a hard reload (F5) unchanged.

## If Something Looks Wrong

- **Badge flips to "Backend unavailable" right after starting or finishing an ordinary
  fetch/backfill job:** this is exactly the regression this iteration was built to fix — flag it
  immediately.
- **Heartbeat text freezes and shows "· possibly stalled" while the job is still healthy and
  running** (most likely to show up on a long job, e.g. the "Rebuild snapshots for current universe"
  button, which can run for around 15 minutes): this is the other regression this iteration fixed —
  see the full UI Test Plan's UT-07 for the dedicated long-running check. Flag it if seen.
- **"Backend unavailable" card / blank page:** the backend isn't running or isn't reachable — start
  it with `scripts/start-backend.sh` and reload.
- **The badge ever shows "Snapshot pending" text that reads exactly "Backend unavailable," or shows
  a red/pulsing-red dot for that state:** wrong text or styling for the new state — flag it.
