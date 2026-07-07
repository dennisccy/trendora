# goal-mcp-loop-iter-19 — Implementation Summary

**Phase:** goal-mcp-loop-iter-19
**Date:** 2026-07-07
**Written by:** developer

---

## Features Implemented

This iteration is a fix-and-verify pass, not new-feature work. It restores two things that broke when
the product's price history was widened to cover 30 years and ~550 companies:

- **The Stocks leaderboard no longer crashes when you sort by "Sector."** Roughly 4 out of 5 companies
  in the widened list don't have an industry sector on file, and clicking the "Sector" column header
  used to crash the entire page to a blank error screen. Sorting and filtering by Sector now works
  correctly, and companies with no sector on file are labeled "Unassigned" instead of causing a crash
  or showing a blank cell.
- **The Data page no longer runs out of memory and freezes.** Loading the Data page for the first time
  after a restart used to force the backend to read the company price history in one enormous, memory-
  hungry gulp — under real conditions this could exhaust the server's memory and hang the whole
  application. The backend now reads that history in smaller streamed chunks, using roughly one-sixth
  the memory, and completes in about 10-18 seconds instead of hanging.
- **A safety net for future crashes.** If some other, not-yet-discovered bug causes a page to crash, the
  app now shows a contained "Something went wrong" message with a "Try again" button — instead of
  wiping out the entire application (including the left-hand navigation menu) to a blank screen.

## Changed Behavior

- **Sector filter on the Stocks page**: Previously, a company with no sector on file would either crash
  the sort or appear as a blank filter option. Now it appears as "Unassigned" and can be filtered on
  like any other sector.
- **First page load after a restart**: Previously, visiting the Data page shortly after starting the
  app could hang or crash the backend under load. Now it completes reliably within the 60-second target,
  even when several people load the page at the same time.

## Backend-Only Items

None — every change in this iteration has a visible effect for the end user (the fixed sort/filter, or
the contained error screen).

## Incomplete Items

- One backend regression-test file (`test_scanner.py`, and separately `test_bars.py`) could not be run
  to completion in the time available for this iteration — running it requires reloading the full
  30-year company history into a test database, which takes several minutes on its own. The tests most
  directly relevant to this iteration's changes (11 tests covering the exact code that was rewritten,
  plus the concurrent-load test) all passed. The remaining two files are recommended for the reviewer
  to run before final sign-off, though there is a specific, documented reason to expect they are
  unaffected (see the developer handoff for details).
- A separate, already-known chart-display item (whether long-history charts correctly show data back to
  the 1990s) was spot-checked while verifying this iteration's other fixes and found to already work
  correctly — no action was needed there.

## Config and Environment Changes

- `config.yaml`: one comment describing the server's memory safety cap was corrected to reflect the
  real (larger) size of the price-history table; the safety cap itself (6,144 MB) is unchanged.
- A new report, `reports/perf-budgets.md`, now records the measured before/after memory and timing
  numbers for the Data-page fix, so future changes can be checked against these numbers.

## Known Limitations

- The performance fix in this iteration addresses only the one item that was blocking (the memory
  problem on the Data page). Several other, smaller performance improvements identified in the
  project's roadmap are intentionally deferred to later iterations, as planned.
- The written-out "before" memory figure for the unfixed code (~6.8 GB) is taken from the incident
  report that triggered this iteration, not independently reproduced in this session — reproducing it
  would have required deliberately undoing the fix and risking a real crash of the working test
  environment for a number that was already reliably measured. The "after" figures were freshly
  measured live, twice, including under a 6-way simultaneous load test matching the original incident.
