# goal-ops-hardening-iter-46 — Implementation Summary

**Phase:** goal-ops-hardening-iter-46
**Date:** 2026-08-04
**Written by:** developer

---

## Features Implemented

- **Bounded memory footprint for the Evidence page's two heaviest computations.** Two backend functions
  that power the Evidence page and the Combination Lab used to build one big in-memory lookup table over
  a large slice of the database before doing their real work — for one of them, live-measured at over
  1.28 million rows for a single request. Both now process the data in small, bounded chunks and discard
  each chunk before starting the next, so the peak memory a single request can use is capped to one
  chunk's worth, not the whole dataset. The numbers each page shows are unchanged — this is purely an
  internal memory-safety change, verified by dedicated tests that compare the new chunked computation
  against the old one, value for value.
- **Two remaining unguarded error-logging spots closed.** Two small code paths that record a job-launch
  failure could themselves fail while trying to write their own log entry (under the SAME kind of memory
  pressure that caused the original failure), and previously that would silently swallow the failure
  record. Both now use the same safe "always leave a trace" logging helper already used everywhere else
  in the data-ingest code.

## Changed Behavior

- None visible to a user in the normal, healthy case. The Evidence page, `/backtest`, `/data`, and every
  other page render the exact same numbers as before — this iteration only changes how much memory the
  backend uses while computing them, never what it computes.

## Backend-Only Items

- Both memory-bounding fixes are backend-internal; there is no UI to wire up (the phase spec explicitly
  scoped this iteration as backend-only, no frontend change).

## Incomplete Items

- **The live proof that a single historical backfill stays fast and the Evidence page stays responsive
  while it runs did not fully succeed.** We ran the actual drill against the running app: submitted a
  real one-day backfill for a date confirmed missing from the data, and while it ran, repeatedly loaded
  the Evidence page and polled the health check.
  - The backfill itself did NOT finish within the 5-minute window we gave it — it was still working
    (not stuck, not crashed) more than 16 minutes in. This matches a known, already-disclosed limitation:
    every date currently available to backfill in this database is an "old gap" rather than a "new day,"
    and old-gap backfills hit a slow, not-yet-optimized recomputation path that a PRIOR iteration
    intentionally left for a future iteration to address.
  - While that slow backfill was running, the Evidence page did not load within 40 seconds, and the
    health check itself sometimes took several seconds to answer instead of its usual instant response.
    We traced this to the SAME backend process being single-threaded in a way that lets one very long,
    uninterrupted calculation (the same slow recomputation above) block everything else the app is doing
    — not to the memory problem this iteration fixed. We confirmed directly: the backend's memory usage
    stayed well under its safety cap the whole time, and no memory-related errors were recorded in the
    log during this test. So the SPECIFIC problem this iteration targeted (the app running out of memory
    while someone is just browsing) did not happen. A DIFFERENT, pre-existing problem (one slow
    calculation freezing the whole app for everyone else) did happen, and is not something this
    iteration's fix addresses.
  - This is reported honestly as an incomplete/failed live proof, not rounded up to a pass. See the dev
    handoff's "Known Issues" for the recommended follow-up.

## Config and Environment Changes

- None. No config keys were added, removed, or changed. Both fixes reuse existing, already-shipped
  tuning knobs.

## Known Limitations

- A single old-gap backfill can take well over 15 minutes and, while it runs, can make the rest of the
  app (including the Evidence page and the health indicator) very slow to respond — sometimes not
  responding within 40 seconds. This is a pre-existing limitation of how the backend recomputes its
  membership timeline for old dates, not something introduced by this iteration, and a fix for it is
  recommended as a future iteration (see the dev handoff).
- One journey-script reference number (`/backtest`'s "n=14647" figure) is expected to shift slightly once
  the backfill triggered during testing finishes updating its cached figures — it was double-checked and
  correct at the moment of writing, but whoever verifies the app next should re-check it against
  whatever the app is showing then, not assume this number is still current.

---
---

# FIX PASS ADDENDUM (2026-08-04, after QA returned FAIL)

Everything above describes the original pass. This section covers the fix pass that followed QA's FAIL
verdict (5 of 8 user journeys failed on live execution).

## What this pass was for

Both the original development notes and the QA report blamed those journey failures on "the app competing
with itself for CPU while a data job runs", and concluded it was an architectural problem for a future
round rather than something fixable here.

That explanation was wrong, and this pass established that by measuring rather than reasoning. **With the
app completely idle and no data job running at all**, simply opening the Evidence page took **2 minutes 43
seconds**. Opening it again immediately afterwards took **11 milliseconds**. Nothing was competing for
anything. Two of QA's four reported problems were therefore fixable inside this iteration, and both now are.

## Features Implemented (fix pass)

- **The Evidence page is now prepared during start-up.** The app already prepared the Evidence page's
  figures after every data import, but nothing prepared them after a plain restart — so the first person to
  open Evidence after any restart sat through the full calculation themselves. Start-up now does that
  preparation in the background. Measured on the real app: first Evidence load after a restart went from
  **163 seconds to 17–64 milliseconds**.

- **Import jobs with nothing to do now finish immediately.** An import covering only non-trading days, or
  only dates already held, used to trigger a full recalculation of the coverage figures regardless — which
  is why such a job could sit in "running" for over 15 minutes. The app now checks whether those figures are
  already current for the present data and skips the recalculation when they are. Measured on the real app:
  **15+ minutes → 5 seconds** (and a 412-day import over already-held dates: **10+ minutes → 5 seconds**).

## Changed Behavior (fix pass)

- **Start-up sequence:** now also prepares the Evidence page figures, as its final step. This runs *after*
  the app reports itself Ready, so the "Ready" badge appears on exactly the same schedule as before —
  verified live at 41 seconds both before and after the change.

- **Finish-up work after an import:** coverage figures are now recalculated only when the import actually
  changed the data. When the recalculation is skipped, the job's list of refreshed items honestly omits
  those entries rather than claiming work that did not happen.

- **A journey test's expected number was corrected.** The J-07 check looked for the gap count "2532" on the
  Data page; the true current figure is **2526** (the original pass's own test import filled six gaps). The
  old number does still appear elsewhere in the page data as an unrelated per-symbol bar count, so the check
  could otherwise have passed for the wrong reason.

## Backend-Only Items (fix pass)

None. No screens changed, no endpoints added, no displayed value altered. Every figure the app shows is
identical; only timing changed.

## Incomplete Items (fix pass)

- **J-05's defining case (single historical gap-fill) is still not met.** Filling a gap from years back
  still triggers the slow full recalculation. This was explicitly excluded from the iteration's scope and
  was not touched. Reported as still failing, not rounded up to a pass.

- **A window of slowness remains right after a restart.** The app reports Ready at ~41 seconds, but the
  Evidence preparation does not finish until ~385 seconds. Anyone opening Evidence in that gap still waits.
  A real improvement over "every restart, forever", but not a complete fix. **Whoever re-tests should let
  start-up finish before scoring the Evidence page.**

## Config and Environment Changes (fix pass)

None. No new settings, environment variables, schema changes, or migrations. The project's required host
resource caps were applied unchanged throughout (memory ceiling 8192 MB, allocator setting 2), and every app
launch used the standard start scripts.

## Known Limitations (fix pass)

- **The underlying calculation is still expensive; it was moved, not made cheaper.** Preparing the Evidence
  page's seven figures takes minutes of genuine work. This pass moved that work off the path where a person
  is waiting. Anything that clears those prepared figures — notably any data import — means the work happens
  again.

- **A newly discovered inefficiency was measured but deliberately left alone.** One query added earlier in
  this same iteration reads roughly **8 million rows to produce seven figures**, filtering by symbol but not
  by date and then discarding nearly everything it read. Filtering by date would give identical results for a
  fraction of the work. It was not changed here because fixing problems outside the reported failures is how
  fix passes become unreviewable rewrites; it is written up with full measurements in
  `reports/perf-budgets.md` (Item N) for the next round to take deliberately. For scale, of the 163-second
  page load: ~85% is a different step again (resolving each figure's underlying population), 12% is this
  query, 1% is a third repeated calculation.

- **One expected figure will drift again.** The `/backtest` check looks for "n=14647" — a running total that
  moves with every import. Correct as of this pass; needs re-checking after the next one.

- **Test coverage is targeted, not exhaustive.** The full suite takes 10–11 hours on this project's 30-year
  data set and cannot be run routinely. 90 tests across the seven suites most exposed to these changes were
  run, all passing. A regression in an unrelated area would not have been caught.

---
---

# AUDIT FIX PASS ADDENDUM (2026-08-04, after the audit returned FAIL)

Everything above describes the original pass and the QA fix pass. This section covers the small pass that
followed the independent audit's FAIL verdict.

## What this pass was for

The audit re-checked the whole iteration against the running app rather than the write-ups, and reached a
split conclusion: **the memory work itself is real and should be kept** (it verified both fixes against the
live app, found the Evidence page loading in 13 milliseconds with all seven figures present, and found zero
memory errors recorded since the fixes went in), but **three promises the round made were not delivered**,
and one new problem the previous fix pass had introduced needed closing.

The audit closed that new problem itself, in-audit. This pass verified that repair against the running app,
closed the two remaining items that were genuinely inside this round's remit, and — deliberately — left the
rest for the next round rather than reopening the same machinery twice in one iteration.

## Features Implemented (audit fix pass)

None. No new capability was added and no user-visible behaviour changed. This pass was verification plus
two records.

## Changed Behavior (audit fix pass)

- **None.** The only code edit in this pass is an internal explanatory comment (a function's written
  description had become inaccurate after the previous pass changed when it runs — the description now
  matches what the code actually does). Nothing a user can observe changed.

## What was verified against the running app (not re-argued on paper)

- **The audit's own repair holds.** The previous pass made "imports with nothing to do finish immediately"
  work by skipping a recalculation when the figures were already current — but the audit found a rebuild
  could, in a specific case, look "already current" when it was not, and fixed it. Re-tested live here: an
  import covering only non-trading days still finishes in **2 seconds**, and it honestly reports that it
  refreshed nothing it did not actually refresh.
- **The app is healthy and fast on the fixed build.** Health check 200 in 0.12 s; the Evidence page's data
  returns in **0.013–0.022 seconds** with all **7 of 7** figures populated; Backtest 0.02 s; Data 0.06 s;
  the web front end responds. **Zero memory errors** have been recorded since this build started.
- **The two reference numbers a journey test checks are still correct** (they drift with every data
  import, so they were re-checked rather than assumed): the Data page's gap count **2526** and the
  Backtest figure **14647** both match the live app right now.
- **Memory headroom, measured and now recorded.** This round promised to record how close the app comes to
  its memory ceiling, and never did. Measured over 120 consecutive one-second samples on the fully
  warmed-up app: peak memory **3,123 MB against the 8,192 MB ceiling — 61.9% headroom**, completely flat
  (zero growth) across the whole window, with **120 of 120** health checks answering in about 0.1 s. This
  is now written down in `reports/perf-budgets.md` (Item O), including an explicit note that it is a
  quiet-period reading, not a reading taken while a heavy import is running.

## Incomplete Items (audit fix pass) — reported unmet, not rounded up

- **The headline promise of this round is still not met: "the Evidence page stays fast while a data import
  runs."** The reason is now precisely understood. The Evidence page's prepared figures are tagged with a
  fingerprint that includes a count of the underlying data rows, so **the moment any import adds data, all
  seven prepared figures are discarded** and the next person to open Evidence pays the full multi-minute
  recalculation. Fixing that means either re-preparing the figures at a different moment in the import, or
  showing the previous figures behind an honest "recalculating" label — both are new machinery, and the
  audit assigned both to the next round. Attempting one here would mean rebuilding the same area twice in
  one round, which is how these changes become impossible to review.
- **One of the three places the Evidence page could exhaust memory is still open.** This round closed two
  and proved them closed; the third (a step that builds and sorts a whole list of observations at once) was
  recorded failing with a memory error in the logs hours before the fix, and is untouched. So the round's
  stated goal — "stop the backend exhausting its memory when someone simply loads the Evidence page" — is
  **two-thirds delivered**, not delivered.
- **A known inefficiency remains open by choice.** The query that reads roughly 8 million rows to produce
  seven figures still filters by symbol but not by date. Fixing it would give identical results for a small
  fraction of the work, and it is the next round's fourth queued item.
- **The through-the-browser checks still need to be re-run.** Every browser check on record was executed
  *before* these fixes existed, so it cannot speak to them, and one journey has no screenshot of its own at
  all. That re-run is the next step for whoever validates this round; it is not something a development
  pass can produce.
- **Backfilling an old missing date is still slow** — unchanged, and explicitly excluded from this round's
  scope.

## Config and Environment Changes (audit fix pass)

None. No settings, environment variables, schema changes, or migrations. The required host resource caps
were confirmed **on the running process itself** (memory ceiling 8,192 MB, allocator setting 2, CPU
restriction 0-15, math-library threads 8) rather than assumed, and the app was started only via the
standard launch script.

## Known Limitations (audit fix pass)

- **Sequencing matters for whoever re-tests this.** Any test that imports genuinely new data throws away
  the Evidence page's prepared figures, and the next Evidence load will then take minutes. The journey that
  backfills a missing day does exactly that (it added 840 rows last time). **Run that journey last**, or
  allow re-preparation to finish before scoring the Evidence-related checks. Likewise, do not restart the
  app immediately before testing without allowing about 6½ minutes for preparation to complete — that is
  the exact trap the earlier browser run fell into twice.
- **The memory-headroom figure above is a quiet-period reading.** No heavy import was run while measuring,
  deliberately: doing so would have discarded the Evidence page's prepared figures and handed the pending
  re-test the slow path this round just fixed. The closest under-load reading on record remains a previous
  round's, and it is cited as such.
- **Testing was targeted, not exhaustive**, for the same 10–11 hour reason as before. This pass ran 10
  focused tests (all passing) on top of the 88 the auditor independently ran.
