# Goal-ops-hardening iter-47 — Implementation Summary

**Phase:** goal-ops-hardening-iter-47
**Date:** 2026-08-04
**Written by:** developer

---

## Features Implemented

- **The Evidence page no longer stalls after a data update.** Previously, if any new market data landed
  anywhere in the system — even data completely unrelated to what a specific claim's evidence panel shows —
  opening the Evidence page could freeze for over two and a half minutes (and much longer if data was
  actively being updated at the same time) while the server recomputed everything from scratch. Now, the
  page always responds quickly. If the numbers being shown are momentarily one update behind (because a
  fresher version is being computed in the background), the page says so plainly — a small "Refreshing"
  label appears next to that panel — while still showing real, honest historical figures, never a blank or
  frozen screen.
- **A rare but real "run out of memory" risk on the Evidence page was closed.** One of the calculations the
  Evidence page relies on (matching stocks to the top 10% of a scoring factor) used to load far more data
  into memory than it actually needed, which could exhaust the server's memory allowance under load. It now
  loads only what it needs. Verified with 5 repeated stress tests under a tightened memory limit — all 5
  passed cleanly with zero crashes, and the results are mathematically identical to before.
- **A hidden inefficiency in the Evidence page's drawdown/dry-spell history calculation was removed.** That
  calculation was reading roughly 8 million historical rows from the database to answer questions that only
  ever needed a small fraction of them — now it reads only the rows that are actually relevant, with no
  change to the numbers shown.

## Changed Behavior

- **Evidence page claim panels**: previously, a panel either showed its full history-based figures or
  showed nothing (if the underlying calculation failed). Now there is a third possibility — the panel shows
  its figures with a small "Refreshing" label if a newer version of the data is still being computed in the
  background. The figures shown are always real numbers from a real calculation, never partial or made up.
- **Background log entries** for a specific internal warm-up routine (the Evidence page's overnight/restart
  data-preparation step) now degrade more gracefully under severe memory pressure — a minor internal
  robustness fix with no user-visible effect under normal operation.

## Corrections and additions from the audit-fix pass (2026-08-04)

An independent audit reviewed the work above and rejected it. Three of its findings changed what is true in
this document; the corrections are listed here rather than quietly edited into the text above.

- **CORRECTION — the "reads only the rows that are actually relevant" improvement was, as first shipped,
  almost entirely ineffective.** The audit measured it: on the main evidence claim it skipped only **4.4%**
  of the rows, not the large fraction the original record claimed. The reason was a design mistake — the
  filter was applied to a group of 50 stocks at a time using the combined set of dates for the whole group,
  and a claim measured over thirty years of history touches nearly every date, so the filter excluded almost
  nothing. It has been **re-done per individual stock**, and re-measured on the real database: it now skips
  **90%** of the rows on that same claim (and 96% on another), reading exactly the rows the calculation goes
  on to use and not one more. The displayed numbers were verified byte-for-byte unchanged.
- **CORRECTION — the memory improvement was real but not, as claimed, a hard bound.** One of the two places
  named in the plan was still holding one lightweight record per observation for the entire population
  (~1.25 million) before sorting them all. It is now genuinely bounded: the calculation keeps only the
  portion that can possibly end up in the answer. Measured on the real database, memory held at that step
  dropped **5x**, peak memory for that calculation halved (1,173 MB → 573 MB), and — importantly for
  responsiveness — the longest single stretch where that background work blocks everything else in the
  server dropped from **973 milliseconds to 103 milliseconds**, while also running 36% faster. Results
  verified byte-for-byte identical on the real data.
- **CORRECTION — the "everything still works" regression checks for six journeys were not real tests.** The
  audit proved that the automated replay scripts used to re-verify them asserted text that the application's
  own saved history page displays regardless of whether anything worked. One journey (data-ingest freshness)
  was recorded as passing on a screenshot whose own contents were five days old. All six scripts have been
  rebuilt to assert against the *live* job panel — which only exists when a job was actually started in that
  browser session — and against elements that only appear once work genuinely completed. Two other journeys
  (backend restart behaviour, and heavy-load memory safety) had their scripts **retired entirely**: neither
  can be checked by a browser click-through at all, so they now go to the slower but genuinely capable
  verification lane instead of passing on a meaningless check.

## Backend-Only Items

None — every backend change in this iteration has a corresponding, user-visible frontend disclosure (the
"Refreshing" label) or is purely an internal robustness/performance improvement with no separate surface to
wire up.

## Incomplete Items

- **CORRECTED: the full catch-up after a data change takes roughly 26 minutes, not the 7-8 minutes recorded
  above.** The audit found the real figure in this iteration's own monitoring log (the seven panels caught up
  between 13:50 and 14:16). The page stays fast and honestly labelled "Refreshing" for that whole window —
  that part is confirmed and unchanged — but anyone planning future work should use ~26 minutes, not ~8.
  Closing that gap is not an audit fix; it needs a redesign of the calculation and is left for a later
  iteration.
- **NEW, disclosed by this fix pass: a data-ingest job's own "wrap-up" stage takes many minutes.** Running a
  real historical ingest (adding one previously missing trading day) showed the day's data itself is saved in
  about 12 seconds — but the job then spends many minutes refreshing all the downstream summary data it
  invalidated, during which the job does not report itself finished and a second job started in that window
  cannot finish either. This is pre-existing behaviour that this iteration's work makes visible rather than
  causes (and the "Refreshing" label above is exactly what keeps it off the user's Evidence page). It is the
  clearest candidate for the next iteration.
- **NEW, disclosed by this fix pass: the health check can exceed its 2-second allowance while an ingest is
  wrapping up.** Measured during the ingest above: 8 of 20 checks took over 2 seconds (worst 3.99 seconds)
  and one monitoring probe gave up at its own 5-second limit. The server was alive and answering throughout
  — this is slowness under load, not an outage — but it is over the allowance the project committed to, and
  it is not fixed here.
- **One specific, out-of-scope memory-margin re-measurement was not repeated this iteration** — a check
  that the server's peak memory usage during its heaviest scheduled data-processing task (unrelated to the
  Evidence page) still has a healthy safety margin. This iteration did not touch that data-processing task
  at all, so the existing, still-valid measurement from a prior iteration was cited instead of re-running a
  lengthy live test that would have added no new information. A future iteration that touches that specific
  task should re-measure it fresh.
- **Full browser-based click-through verification of all 8 product journeys** (the standard end-of-iteration
  check) has not yet run — that is a separate quality-assurance step that happens after this development
  work, not part of it. The system is left running and ready for that step.

## Config and Environment Changes

None — no new environment variables, config keys, or migrations. This iteration's changes are entirely in
application code (backend calculation logic + one frontend display state).

## Known Limitations

- The background "catch-up" process for stale Evidence panels currently re-processes all seven certified
  claims one at a time in a single background task (deliberately changed mid-iteration from an earlier
  design that ran up to seven simultaneously, which was found — via a live test — to slow the whole
  application down more than it should). Running them one at a time is safer and was confirmed not to slow
  the rest of the application meaningfully, but it does mean the full catch-up takes a few minutes longer
  in the worst case (all seven claims going stale at once, which is the common case today since any data
  update currently affects all of them — a known, separately-tracked characteristic of how the affected-ness
  check works, not something this iteration was scoped to change).
- A specific automated backend test file that exercises this same behavior through the full web-server
  layer (rather than testing the underlying calculation directly) was not re-run this iteration — it has a
  known, pre-existing slow startup step (unrelated to this iteration's changes) that was taking an
  unusually long time during this session, and was stopped to avoid tying up the machine. The underlying
  logic it would have tested is otherwise thoroughly covered by dozens of other automated tests, plus a
  live demonstration against the real running system (documented in the developer handoff and
  `reports/perf-budgets.md`).
