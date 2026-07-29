# goal-ops-hardening-iter-31 — Implementation Summary

**Phase:** goal-ops-hardening-iter-31
**Date:** 2026-07-29
**Written by:** developer

---

## Features Implemented

- **The Factor Lab "all factors" view no longer crashes.** Opening `/research/factor-lab` (the view that
  shows every scoring factor against every time horizon at once) used to reliably return a server error
  ("out of memory") every single time it was opened. It now loads successfully and shows the same numbers
  it was always supposed to show — nothing about what's displayed has changed, it simply works now.
- **Two people opening the Factor Lab at the same moment no longer waste double the work.** Previously, if
  two requests for the same Factor Lab data arrived close together while nothing was cached yet, the
  backend would (wastefully, and riskily from a memory standpoint) compute the whole thing twice at once.
  Now only one computation runs; the second request waits for the first to finish and reuses its answer.
  The second request is willing to wait up to 15 minutes — deliberately far longer than the 2-5 minutes
  this calculation actually takes on this machine — so that a normal, legitimately slow calculation is
  never mistaken for a stuck one. If something genuinely does get stuck, the waiting request still gives
  up after those 15 minutes and does the work itself rather than hanging forever, and it now writes a
  warning to the log when that happens, so the situation can never pass unnoticed.
- **A new safety tripwire for the future.** If the amount of stock/day/factor data ever grows large enough
  to approach the same kind of memory pressure again, the backend will now write a warning to its log file
  instead of silently building toward another crash. It never blocks or slows down a normal request to do
  this — it's a log line, not a behavior change.

---

## Changed Behavior

- **`/research/factor-lab` (all-factors view)**: Previously crashed with a server error on every visit.
  Now returns the correct data every time, verified by loading it twice in a row and confirming the
  results were identical down to the byte.

---

## Backend-Only Items

- None. This is a backend memory/concurrency fix to an existing page; there is no new capability requiring
  UI wiring. The Factor Lab page's existing look and numbers are unchanged — it just stops failing.

---

## Incomplete Items

- None from this iteration's assigned scope. Three separate, unrelated memory-safety risks that were
  identified earlier in this project (in the boot warm-up process, in a coverage-refresh calculation, and
  in one other research calculation) were deliberately left untouched — the project's own safety rule
  limits each release to fixing one risky area at a time, and those three are queued for future iterations.

---

## Config and Environment Changes

- New setting `research.factor_pool_max_observations` (in `config.yaml`, default 2,000,000) — the safety
  tripwire threshold described above. It does not change what gets computed or displayed; it only controls
  when the new warning-log message fires. Set with wide headroom above today's real data volume
  (measured today at roughly 770,000-800,000 records per time horizon), so normal operation will never
  trigger it.

---

## Known Limitations

- The live memory measurement (see the developer handoff for full numbers) shows the fixed page now uses
  about 2.1-2.4 GB of memory at its busiest moment, comfortably under the server's 6 GB safety ceiling —
  roughly 60% headroom to spare. This was confirmed twice, on two separate fresh backend restarts, with
  identical results both times.
- Loading this specific page (all factors, all time horizons, all of history) is still slow — a few minutes
  — because it is a very large, one-off calculation that is deliberately not cached ahead of time. That
  slowness is not new and is not part of what this iteration was asked to fix; the important change is that
  it now finishes successfully instead of crashing.
- The double-request safety fix (the "two people at once" item above) was proven with automated tests that
  simulate five simultaneous requests; it was not separately re-tested by hand in a live browser, since
  reproducing that exact timing by hand is impractical and the automated proof is the standard the project
  uses for this kind of fix elsewhere.

---

## Correction Made After Code Review

The first version of this work shipped the "two people at once" protection with a **45-second** patience
window, copied from a similar but much faster calculation elsewhere in the system. Code review caught that
this was too short to be useful: the Factor Lab calculation itself takes 2-5 minutes on this machine, so
the second request would always have given up part-way through and started its own duplicate calculation —
the exact waste the fix was supposed to prevent. This was not hypothetical; it was reproduced on this
machine (with the old 45-second setting, an automated test observed the calculation run twice instead of
once).

The patience window is now **15 minutes**, chosen as three times the slowest real measurement, and it is
written in the code as "the measured time × a safety factor" rather than as a bare number, so the reason
for the value is visible to whoever reads it next. Two automated tests now guard it: one fails if anyone
lowers the setting back below the real measured duration, and one runs a genuine slow calculation past the
old 45-second mark to confirm the second request really does wait it out. Nothing else was changed — the
memory fix, the numbers shown on the page, and the measured memory figures above are all unaffected (a
single request is always the one doing the work and never waits).
