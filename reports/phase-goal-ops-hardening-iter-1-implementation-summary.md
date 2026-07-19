# Phase goal-ops-hardening-iter-1 — Implementation Summary

**Phase:** goal-ops-hardening-iter-1
**Date:** 2026-07-19
**Written by:** developer

---

## Features Implemented

- **Backfill now respects the exact date range you ask for.** Previously, requesting a backfill for a
  range of dates (for example, all of May 2026) could silently do nothing if that range fell into an
  older part of history where the system only keeps monthly snapshots by default. Now, an explicit
  backfill request always processes every trading day in the range you asked for — the automatic
  "keep it light on old history" behavior only applies to the system's own background upkeep, never to
  something you explicitly requested.
- **No more size limit on backfill requests.** You can now request a backfill spanning any number of
  days — a week, a year, several years — and it will be accepted and start running. Previously, anything
  longer than about a year (370 days) was rejected outright.
- **Large backfills now run in visible chunks.** A very long backfill (spanning more than the old limit)
  is automatically broken into manageable pieces behind the scenes and processes them one at a time, so
  memory use stays under control and you can watch it progress chunk by chunk — the same progress
  indicator already used for large data downloads now also appears for large backfills.
- **Honest, detailed explanations for every backfill outcome.** Every completed backfill (or attempted
  backfill) now reports exactly how many calendar days were in the range, how many of those were actual
  trading days, how many days were skipped because they already had data, how many were skipped because
  they aren't trading days (weekends/holidays), and how many failed. These numbers are guaranteed to add
  up correctly — the plain calendar-day count always splits cleanly into trading and non-trading days, and
  the trading days always split cleanly into newly-created, already-done, or failed.
- **"Nothing new to do" no longer looks like an unexplained success.** If you re-run a backfill over a
  range that's already fully up to date (or a range that has no trading days in it at all, like a
  weekend), the result now shows a clearly different, neutral-colored badge and a short explanation —
  instead of looking exactly like a normal successful run with no context.
- **The job progress panel now shows your last backfill even after a page reload or new visit.** Before,
  if you reloaded the Data Manager page without having started a job in that browser session, it always
  said "No job has been started this session" — even if jobs had been run earlier and were sitting right
  there in the history table below. Now it shows the most recent run's outcome instead.

## Changed Behavior

- **Backfill request size limit removed.** Previously, any backfill request longer than 370 calendar days
  was rejected with an error. That limit no longer exists anywhere in the system — requests of any length
  are accepted, and the system's internal chunking keeps large requests safe and memory-bounded.
- **What "total days" means in a backfill result has changed.** Before, the reported "total days" number
  only counted the days that still needed work (excluding days that already had data). Now it always
  means "every trading day in the date range you asked for," whether or not it needed new work. This
  makes the reported numbers more transparent, but it does mean older saved reports and this number will
  read differently than before for a re-run of the same range (the new breakdown fields explain why).

## Backend-Only Items

None. Every backend change in this phase has a corresponding visible change on the `/data` page (the
breakdown counts, the zero-work badge, the persisted-history fallback, and the chunk-progress indicator
for backfills).

## Incomplete Items

Nothing from this iteration's assigned scope was left incomplete. Two related but explicitly separate
efforts remain for future work (as planned, not a gap in this iteration):
- The "instant boot with a visible starting-up status" and "persistent backend log file" work is a
  separate, already-scheduled effort and was not touched here.
- Making the system's heavier calculations (like coverage numbers and market status) precompute
  automatically at the same time as a backfill, rather than only being computed on-demand, is also a
  separate, already-scheduled effort not touched here.
- One internal-only edge case is worth knowing about: the confirm-gated "regenerate everything from
  scratch" action (a rare, deliberate full rebuild) still uses the system's existing "go easy on very old
  history" behavior exactly as before — that specific action was intentionally left unchanged this round,
  since normal day-to-day backfill use does not go through it.

## Config and Environment Changes

- Removed the `max_range_days` setting from the system's configuration file — this was the setting that
  capped backfill requests at 370 days. There is no replacement setting; the chunking behavior described
  above is now what keeps large requests safe, so no configuration action is needed.
- No new environment variables, database changes, or migrations were introduced.

## Known Limitations

- The one rare, manually-triggered "regenerate everything from scratch" action does not get the full
  benefit of the new detailed breakdown numbers in every case — because it deliberately still applies the
  "go easy on very old history" behavior, its reported day-count breakdown may not always add up as
  precisely as it does for a normal backfill request. This has no effect on everyday backfill use, which
  is what this iteration was about.
- This implementation has been verified with automated tests and by starting the actual backend and
  confirming it comes up correctly with the new settings. The full guided walkthrough in the browser
  (visiting the Data Manager page, submitting a real May-2026 backfill, and confirming the on-screen
  numbers and colors match expectations) is the next pipeline step's job, not yet independently confirmed
  step-by-step in a live browser session as part of this write-up.
