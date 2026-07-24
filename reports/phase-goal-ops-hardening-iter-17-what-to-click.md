# Phase goal-ops-hardening-iter-17 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-17
**Time required:** ~5 minutes (core steps below); an optional deeper check adds ~8 more minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Main frontend running at `http://localhost:3255` (backend at `http://localhost:8255`) — already running,
  no login required.
- A SEPARATE, disposable throwaway frontend also running at `http://127.0.0.1:13255` (backend
  `:18255`), pointed at a never-used copy of the database — already booted for you specifically for step
  1 below. It is NOT the main app; nothing you do there touches your real data.
- No test data setup needed — both instances are already in the right state.

---

## Verification Steps

1. Open `http://127.0.0.1:13255/backtest` in your browser — **this is the separate throwaway instance,
   not your main app.**
   - **Expect:** near the bottom of the page, a dashed-bordered card with a flask icon reading "Backtest
     evidence not yet computed", followed by: *"No forward-tested evidence exists yet for this date.
     Backfilling or fetching data that covers it will compute this evidence — no numbers are fabricated in
     the meantime."*

2. On that same card, check that the words **"run an ingest"** do NOT appear anywhere in the description.
   - **Expect:** they don't. That phrasing was removed this iteration because it could wrongly imply you
     hadn't already started an ingest, even if you had.

3. Refresh that page (F5).
   - **Expect:** the exact same card and wording reappear — no crash, no blank page, no different text.

4. Now open `http://localhost:3255/backtest` — your regular, main app — in a new tab.
   - **Expect:** the page loads normally with a "Viewing as-of `<date>` (latest)" badge near the top.

5. Scroll to the very bottom of this MAIN page.
   - **Expect:** a populated evidence section with real numbers — NOT the empty "not yet computed" card
     from step 1. (If you instead see an amber "Refreshing — showing the last complete evidence" banner
     above populated numbers, that's also correct — see below.)

6. Scroll back up and check the "Forward-test scorecard" table and the "Leadership cohorts" section (Top
   Sectors / Top Themes / Ranked cohort), above the evidence section.
   - **Expect:** all three still show real tickers, scores, and returns — unaffected by this iteration's
     backend change.

7. Confirm neither page (throwaway or main) ever showed a red "Backend unavailable" error card.
   - **Expect:** no red error card on either page, at any point above.

---

## What "Working Correctly" Looks Like

- The throwaway instance (step 1) shows the new, honest empty-state wording — never blank, never an error.
- The main app (steps 4-6) looks exactly as it did before this iteration: fully populated, numbers intact.
- The two instances never interfere with each other.

## If Something Looks Wrong

- **Blank page / error screen on either instance**: confirm you used the right port for each step (`13255`
  for steps 1-3, `3255` for steps 4-6) — mixing them up is the most common mistake.
- **The "not yet computed" card is missing on the throwaway instance**: check you're on `:13255`, not
  `:3255` — the main app should never show this card while it has real data.
- **The main app's evidence section is empty**: this would be a regression — this iteration's whole point
  was to stop that from happening. Flag this immediately; do not assume it's expected.

---

## Optional deeper check (~8 extra minutes): seeing the corrected "Refreshing" banner itself

Steps 1-7 above confirm the safe, quick things. The ONE thing this iteration adds that still has no live
browser screenshot on file is the corrected "Refreshing" banner text itself (it now names WHICH date's
evidence is shown, not just when it was generated) — reaching it requires waiting through a real data
update. Only do this if you have the extra time; skipping it and noting why is acceptable.

8. On the main app, go to `http://localhost:3255/data` and look at the "Start a fetch / backfill job"
   panel. If the "Start date"/"End date" fields already show dates (they auto-fill from real gaps in the
   dataset), leave the "Job kind" dropdown on "Backfill snapshots" and click "Start". Do **not** click
   "Rebuild snapshots for current universe" — that's a much bigger, unrelated action.
9. Keep reloading `http://localhost:3255/backtest` (a second tab) every 30-60 seconds for up to ~8 minutes.
   - **Expect:** at some point before the job finishes, the amber "Refreshing — showing the last complete
     evidence" banner appears, and its text now includes "evidence as of `<a real date>`" right before
     "generated `<timestamp>`".
10. If you never catch it within ~8 minutes, that's fine — just note that the window was missed rather
    than treating it as a failure; the underlying logic is separately verified by 15 passing backend tests.
