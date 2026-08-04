# goal-ops-hardening-iter-45 — Implementation Summary

**Phase:** goal-ops-hardening-iter-45
**Date:** 2026-08-04
**Written by:** developer
**Revision:** 2 — updated after the audit returned FAIL. Sections marked *(fix pass)* are new; everything
else is carried from revision 1 and is still accurate.

---

## Features Implemented

- **Faster backfills for the common case**: when you backfill one or more NEW trading days that are all
  more recent than every day already in the system, Trendora now only recalculates the "who's in the
  investable universe" history for those new days — not the entire multi-decade history all over again.
  Previously, adding even one new day forced the system to re-check every historical day (thousands of
  them) against the full symbol list before it would finish, which is what made recent backfills and
  aggregate warm-ups take many minutes or appear to hang.
- **A logging bug that could crash the safety net is closed**: the code that catches "out of memory"
  problems during a data-ingest job and writes a note about it to the log was, in rare timing-dependent
  cases, itself capable of triggering a second out-of-memory error while writing that note — which could
  let the crash escape past the safety net it was supposed to be caught by. The log-writing itself is now
  guarded, so a memory problem is always safely recorded and the job always finishes cleanly instead of
  crashing the whole ingest step.
- *(fix pass)* **A failed data job now always leaves a trace in the log.** Until now, when a data-ingest
  job died outright, the system recorded a one-line reason on the job itself and wrote **nothing at all**
  to the server log. That is exactly what happened to the most important failure of this round: a job
  failed with "out of memory", and afterwards nobody — including the auditor — could work out *where*
  in the job it had failed, because there was no log entry to read. Every fatal job failure is now written
  to the log with the job's id, its type, the same reason the job itself reports, and the technical detail
  of exactly where it failed. Three further safety properties were specifically tested: writing that log
  entry can never itself take the job down (the original failure is what matters, not the note about it);
  if the detailed version of the note can't be written under memory pressure, a short version is written
  instead — so the failure is never silent; and **any data-provider API key is redacted out of that
  technical detail before it is written**. That last point was a real defect caught during this fix pass,
  not a hypothetical: the first version of the new log entry would have written a provider key into the
  server log in clear text whenever a data-fetch job failed. It is now redacted (shown as `***`), matching
  how every other error surface in the product already handles keys, and there is a test that fails if the
  key ever reappears.
- *(fix pass)* **Screenshot evidence now identifies itself.** Each automated end-to-end check saves one
  screenshot as its evidence. Two of this round's checks happen to finish on the *same* page in the same
  state, so their two screenshots came out byte-for-byte identical — which made an automated integrity
  check (designed to catch one screenshot being passed off as evidence for several checks) fire on
  evidence that was actually honest. Each screenshot now carries its own invisible label recording which
  check it belongs to, which round it was taken in, and when. The picture itself is completely unchanged —
  not a single pixel is altered — the file simply now says what it is.

## Changed Behavior

- **Backfilling a new, more-recent trading day**: previously recalculated the whole historical membership
  timeline (thousands of days) on every such backfill. Now recalculates only the new day(s); everything
  already calculated is reused unchanged. The numbers shown to users are identical either way — this only
  changes how much work the server does, not what it reports.
- **Backfilling an OLD trading day that falls before data you already have** (a "gap fill" — filling in a
  day from years ago that was somehow skipped): unchanged, still does the full recalculation as before.
  This is a known, intentional limitation of this update (see "Known Limitations" below) — closing this
  case is left for a future update.
- *(fix pass)* **Failed data jobs are logged** (see above). Successful jobs are unaffected; nothing about
  what a job does, or what it reports back to the page, has changed.
- *(fix pass)* **One automated check's expected number was corrected.** The saved end-to-end script for
  the "heavy background work never takes the service down" check was looking for a sample-size figure of
  `n=8991` on the Backtest page. That figure was never actually on the page — the live value is `n=14647`.
  The script now looks for the correct number, checked directly against the running system.

## Backend-Only Items

None — this iteration has no user-facing UI change in shape; the improvement is purely about how quickly
the server responds after certain operations, using the same pages and displays as before. The fix pass
adds no user-visible surface either: log entries are for operators, and the screenshot labels are internal
test evidence.

## Incomplete Items

- **The round's headline goal was NOT achieved, and the fix pass does not change that.** During the live
  browser checks, the server became completely unreachable for roughly 42 minutes — it stayed running, but
  answered nothing at all. Both of the two journeys this round targeted (a single-day backfill completing,
  and heavy background work never taking the service down) **failed** their live checks. The cause the
  audit identified — the server running so low on memory that it could no longer even create the internal
  worker needed to answer a request — is not something this round was scoped to fix; the two changes that
  would address it were explicitly listed as out of scope for this round and are the top items for the
  next one.
- **The target "day-one backfill completes quickly" scenario (J-05) could not be demonstrated as fixed
  against today's actual database**, because every currently "missing" day available to backfill in this
  installation's database happens to be an OLD gap (from 2019 or earlier) rather than a NEW, more-recent
  day — and only the NEW-day case was sped up this round (see "Changed Behavior" above). I ran a real
  backfill of one of those old missing days as a check: it was still running after 18+ minutes, confirming
  it is not sped up by this update. This is expected and intentional given this round's scope, not a bug
  — but it means the specific before/after speed improvement this round targeted may not be directly
  observable through this installation's current data without either (a) a future update that also speeds
  up the "old gap" case, or (b) a differently-set-up test database that has a genuinely new day available
  to backfill. *(fix pass: re-confirmed against the running system — the most recent missing day is from
  February 2019, while the newest day on file is July 2026, so there is genuinely no "new day" to test
  against, and fetching newer data to create one is not permitted.)*
- One good sign from that same check: while the slow backfill was running (18+ minutes), the app's own
  "is the server alive" health check kept responding normally the entire time — no freeze, no outage. That
  matches this round's OTHER goal (the server staying responsive during heavy background work), even
  though the backfill itself wasn't accelerated. *(This was a different, earlier run than the 42-minute
  outage described above — both observations are real; the system's behaviour under load is not
  consistent.)*
- *(fix pass)* **The two identical screenshots from this round are left exactly as they were.** The
  underlying cause is fixed for future runs, but the existing files were captured before the fix. They
  were deliberately NOT re-labelled after the fact: doing so would have made the integrity check pass
  while implying the evidence had been captured correctly the first time, which it was not.

## Config and Environment Changes

None. No new environment variables, no config file changes, no database schema changes.

## Known Limitations

- **"Old gap" backfills (filling in a historical day from before your most recent data) are still slow.**
  Only backfills of NEW, more-recent days were sped up this round. If your day-to-day workflow is mostly
  "catch up with the latest trading day," you should see the improvement. If it's "go back and fill in
  historical gaps," you will not see a speed change from this update — that remains a known follow-up item.
- **One test database row from this round's verification is left in an honest "interrupted" state** — a
  real backfill job that was intentionally stopped mid-way to gather timing evidence. The system already
  has a mechanism (used every time the server restarts) that automatically marks any such interrupted job
  correctly the next time the server starts — nothing further to do.
- *(fix pass)* **Better logging is not the same as better reliability.** The fatal-failure log entry makes
  the *next* outage explainable; it does nothing to make an outage less likely. The reliability work
  itself is still ahead.
- *(fix pass)* **The automated checks pin exact on-screen numbers that move whenever data is added.** The
  Backtest sample-size figure has now needed correcting twice. It is correct today and was verified against
  the running system, but it will go stale again the next time new data lands — worth re-pointing at a
  figure that does not move.
- *(fix pass)* **Two similar unguarded log-writing spots remain** elsewhere in the data-job code (on the
  path that handles a job that failed before it ever started). They were not part of what the audit asked
  to be fixed and were left alone rather than changed quietly; they are recorded as a follow-up item.
