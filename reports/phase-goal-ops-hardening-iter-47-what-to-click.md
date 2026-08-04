# Phase goal-ops-hardening-iter-47 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-47
**Time required:** ~5 minutes (plus an optional ~8-minute wait to see the badge clear — skippable)
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Backend running at `http://localhost:8255`, frontend running at `http://localhost:3255`
- No login required
- The backend should have been running for at least a few minutes already (not freshly restarted seconds
  ago) so a prior generation of the Evidence data already exists

---

## Verification Steps

1. Open `http://localhost:3255/evidence` in your browser
   - **Expect:** The "Evidence" heading loads, followed by one or more claim cards (or, if none exist yet,
     a card titled "No certified claims yet"). No "Backend unavailable" error card.

2. On any visible claim card, look under the heading "Historical drawdown & dry-spell expectations (…-day
   hold)"
   - **Expect:** A table with real numbers (percentages, day counts) — no amber "Refreshing" badge next to
     the heading right now, and the page loaded quickly (no multi-second hang).

3. Open `http://localhost:3255/data` and find the "Price history" row in the "Dataset coverage" panel near
   the top
   - **Expect:** A value like "2005-01-03 → 2026-07-31" — note the SECOND (later) date shown; it will be
     different in your environment.

4. In the "Start date" field, type the calendar day right after the date you just noted (e.g. if you saw
   "→ 2026-07-31", type `2026-08-01`). Type the same date into the "End date" field, then click the
   "Start" button
   - **Expect:** A job progress panel appears/updates showing the new job running (a spinning icon next to
     its status badge).

5. Return to `http://localhost:3255/evidence` (open a new tab or navigate back) within the next few
   minutes and reload the page
   - **Expect:** At least one claim card now shows a small amber `Badge` reading **"Refreshing"** next to
     its "Historical drawdown & dry-spell expectations" heading, with an added sentence explaining a newer
     version is computing in the background — the table below it still shows real numbers, never a blank
     or loading table.

6. While that badge is showing, reload `http://localhost:3255/` (the home page)
   - **Expect:** The page loads normally and shows "Ready" somewhere on it — it is not slow or frozen even
     though a background catch-up is happening.

7. (Optional — skip if short on time) Wait about 8 minutes, then reload `http://localhost:3255/evidence`
   again
   - **Expect:** The "Refreshing" badge on the claim card from step 5 is gone; the table still shows real
     numbers.

---

## What "Working Correctly" Looks Like

- `/evidence` always loads within a couple of seconds, whether or not a data job is running in the
  background — it never appears to freeze or hang.
- When a claim's table is showing slightly-behind data, it says so with the calm amber "Refreshing" badge
  — it never silently shows old data with no indication, and it never shows a blank table while catching
  up.

## Common Issues

- **Blank page / "Backend unavailable" error**: confirm the backend is running
  (`curl http://localhost:8255/api/health` should return HTTP 200).
- **No "Refreshing" badge ever appears in step 5**: the badge only shows while a background catch-up is in
  flight after a genuinely NEW date was backfilled — double-check the date typed in step 4 was strictly
  later than the "Price history" end date read in step 3 (a date that was already ingested will not
  trigger it), and that you reloaded `/evidence` within a few minutes of starting the job.
- **"Start" button does nothing / shows a date format error**: dates must be typed as `yyyy-MM-dd` (e.g.
  `2026-08-01`).
