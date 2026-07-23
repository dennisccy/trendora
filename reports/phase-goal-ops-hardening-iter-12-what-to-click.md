# Phase goal-ops-hardening-iter-12 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-12
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`, backend at `http://localhost:8255` — both are already up
  with host-guard caps live; you do not need to start or restart anything for steps 1–7 below
- No login required (this app has no auth)
- Chrome with DevTools available (Network panel, "Disable cache" option)
- Nothing new shipped this iteration — every step below checks that an EXISTING page still behaves
  correctly, and that one existing endpoint's speed has now been measured honestly under a controlled,
  idle-host condition

---

## Verification Steps

1. Open `http://localhost:3255/data` in a **brand-new** Chrome tab with the Network panel open and cache
   disabled
   - **Expect:** the "Data Manager" page loads (heading "Data Manager"). No "Backend unavailable" red
     error card anywhere on the page.
   - *Note:* this page is very tall (~17,800px) — a screenshot of the whole page can come back blank. Don't
     rely on a screenshot here; scroll to the "Index & benchmark data provenance" panel directly, or use
     DevTools' Elements panel to confirm it's present.

2. In the Network panel, find the request to `/api/indexes?full=true` and note its duration once it turns
   green (status 200)
   - **Expect:** the request completes with status 200 and shows a duration (this is the number this
     iteration exists to measure honestly — it does not need to be under any particular value for you to
     consider the page "working," but note it).

3. Scroll to the "Index & benchmark data provenance" panel
   - **Expect:** a table of index/benchmark tickers, each with a vendor name (Stooq / Yahoo / FRED-macro
     proxy or "—") and a first-bar date. Not stuck on a gray pulsing loading block, not showing "Vendor
     disclosure unavailable".

4. In the job form near the top of `/data`, type `2025-06-01` into "Start date" and `2026-07-17` into "End
   date" (leave "Job kind" on its default "Backfill snapshots"), then click the "Start" button
   - **Expect:** NO "date range too large" error appears. The button switches to a spinner with the text
     "Job running…", and the "Job progress" panel below shows a live status badge.
   - **Broken looks like:** a red error message rejecting the date range, or nothing happening when you
     click "Start".

5. Wait for the job to finish (the spinner stops, the badge shows a final status), then press F5 to reload
   the page
   - **Expect:** the "Run history" table at the bottom still lists this run with the same status badge and
     the same counts as just before you reloaded — the result persisted, it didn't vanish or reset.

6. Navigate to `http://localhost:3255/scanner-runs`
   - **Expect:** a table of dates loads (columns "As of", "Regime", "Actionable", etc.) with real values in
     every row the instant the loading skeleton clears — no row stuck on a spinner or a "—" placeholder.

7. Navigate to `http://localhost:3255/` (home)
   - **Expect:** the "Dashboard" heading loads, and the "Market Phase & Severity" card fills in with a
     phase badge (e.g. "Risk-on", "Defensive") and an "as of `<date>`" label within about 1–2 seconds — not
     stuck on its gray loading block, and not showing "Market phase unavailable".

---

## What "Working Correctly" Looks Like

- `/data`, `/scanner-runs`, and `/` all load real data with no red "Backend unavailable" cards
- The `/api/indexes?full=true` request on `/data` completes (status 200) and its duration got recorded —
  that recording is this iteration's actual deliverable, not a new button or feature
- The backfill form still accepts a wide (>1-year) date range and the result still survives a page reload

## If Something Looks Wrong

- **A red "Backend unavailable" card appears on `/data`, `/scanner-runs`, or `/`**: confirm the backend is
  actually still running at `http://localhost:8255` (you did not start/stop it, so if it's down, tell the
  operator rather than restarting it yourself). If it IS running and the error persists, this may be the
  already-known critical issue where a large in-memory computation can exhaust backend memory — note it,
  it is a pre-existing tracked issue, not something this iteration introduced or was supposed to fix.
- **The date-range backfill in step 4 is rejected**: this WOULD be a genuine regression (this exact
  workflow has been verified working in every prior iteration) — flag it immediately.
- **The `/api/indexes?full=true` request in step 2 never completes / spins forever**: note the exact wait
  time and leave the tab open; do not force-close and retry more than twice.

Steps requiring a backend restart or crash (to check the health badge and the "Interrupted" job state) are
**intentionally not included above** — those require an operator to physically restart/kill the backend
process, which this guide's 5-minute check does not assume you'll do. If you want to verify that behavior
too, see UT-12/UT-13/UT-14 in `reports/phase-goal-ops-hardening-iter-12-ui-test-plan.md`.
