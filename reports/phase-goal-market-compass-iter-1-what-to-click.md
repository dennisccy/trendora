# Phase goal-market-compass-iter-1 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-1
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3255`, backend running at `http://localhost:8255`. No login is
  required — this app has no auth.
- No special seed data needed beyond what's already committed. The dates below (`2026-08-13` /
  `2026-08-14`) are the two most recent trading days at the time this guide was written — if the
  "Snapshot dates" list on `/data` now shows newer dates, use the two most recent ones shown there instead.

---

## Verification Steps

1. Open `http://localhost:3255/stocks` in your browser
   - **Expect:** "Stocks" heading loads, table renders. Look at the "Sector" column — many rows read
     "Unassigned" right now (this is the BEFORE state; today it's the large majority of rows).

2. Open `http://localhost:3255/data`. In the "Remove imported data" box, type `2026-08-13` into "From date
   (required)" and `2026-08-14` into "To date (required)", then click "Preview removal"
   - **Expect:** A "Confirm data removal" popup opens showing a bar count and symbol count greater than
     zero, with no orange "refused" warning.

3. Click the "Remove `<N>` bars" button in the popup (N is whatever number the popup showed)
   - **Expect:** The popup closes and a green line appears: "Removed `<N>` user-added bars;
     cascade-removed... snapshots and... forward returns."

4. In the "Start a fetch / backfill job" box, type `2026-08-13` into "Start date" and `2026-08-14` into
   "End date". Leave "Job kind" set to "Backfill snapshots", then click "Start"
   - **Expect:** A live job status box appears on the page.

5. Wait for the job status badge to stop saying "running" (this should take well under a minute for a
   2-day range)
   - **Expect:** The badge turns to "ok" and the text below it reads "`<N>` snapshots · `<N>` forward
     returns inserted", both numbers greater than zero.

6. Go back to `http://localhost:3255/stocks` and type `GRMN` into the "Search ticker or name…" box
   - **Expect:** The Sector cell for the GRMN row now reads "Consumer Discretionary" — it read
     "Unassigned" in step 1.

7. Clear the search box and type `DELL`
   - **Expect:** The Sector cell for the DELL row reads "Technology" — unchanged from before (proves the
     fix only fills in missing sectors, it never overwrites a name that already had one).

8. Refresh the page (press F5 or Cmd+R), then search `GRMN` again
   - **Expect:** GRMN still shows "Consumer Discretionary" — confirms the value is saved in the database,
     not just shown once on screen.

9. Open `http://localhost:3255/methodology`
   - **Expect:** The page loads normally ("Methodology" heading, entry cards, glossary). A "Universe
     Selection" card will **NOT** appear — see "Common Issues" below, this is expected in this
     environment and is unrelated to this phase's work.

---

## What "Working Correctly" Looks Like

- On `/stocks`, after steps 2–5, the "Sector" column shows real sector names (Technology, Health Care,
  Financials, Utilities, etc.) for almost every row — only a small handful, if any, still read
  "Unassigned".
- Tickers that already had a sector before this change (like DELL) show the exact same sector as before —
  the fix only adds coverage, it never changes an existing correct value.

## Common Issues

- **Blank page / error screen**: check the backend is running — `curl http://localhost:8255/api/health`
  should return `"status":"ok"`.
- **"Preview removal" button stays greyed out**: both From and To dates are required and must be typed as
  `yyyy-MM-dd`. If the popup shows an orange "refused" message instead of a count, the range you picked
  falls entirely inside the protected, non-deletable committed seed — pick the two most recent dates shown
  in the "Snapshot dates" list on the same page instead.
- **"Universe Selection" card never appears on `/methodology`, even after the backfill**: this is expected
  in this environment. That entire card (not just this phase's new part) needs a separate, one-time setup
  step that has never been run here — it's unrelated to this phase and there is no button in the app for
  it. Do not treat this as a failure of steps 1–8 above.
- **Sector column still shows "Unassigned" for a stock you expected to change**: check the date shown in
  the top-right corner of the page (near "View as-of date") reads "Latest", not an older date — the sector
  fix only applies to freshly-scored runs, not runs scored before this phase shipped.
