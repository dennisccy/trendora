# goal-ops-hardening-iter-14 — Implementation Summary

**Phase:** goal-ops-hardening-iter-14
**Date:** 2026-07-23
**Written by:** developer

---

## Features Implemented

- **Memory-safe rewrite of the forward-return evidence calculation**: the calculation behind the
  Backtest page's evidence panel (mean forward return by bucket/setup/regime, excess vs. SPY/QQQ,
  control-group comparisons) now reads its underlying data in small, bounded chunks instead of loading
  the entire two largest database tables into memory at once. Nothing about what the page shows, or the
  numbers it displays, changes — this is entirely an internal efficiency fix. Verified: the new
  calculation produces byte-for-byte identical results to the old one, across every configured time
  horizon and both "as of today" and "as of a past date" views.
- **Proof the fix actually closes the memory problem**: a real, induced low-memory condition (not a
  simulated/pretend one) was used to show that the OLD calculation genuinely runs out of memory under
  that condition, while the NEW calculation comfortably completes under the identical constraint — this
  is direct evidence the rewrite works, not just a code-reading argument that it should.
- **Proof the fix survives multiple simultaneous requests**: 5 requests were fired at the calculation at
  the same time (mirroring the exact situation — 4 simultaneous data-loading jobs plus one extra
  request — that caused a ~12-minute full outage two iterations ago). All 5 completed quickly with
  identical answers; none hung or blocked the others.
- **Performance record updated**: the project's performance-tracking document
  (`reports/perf-budgets.md`) now has the already-measured, already-passing page-load timings from two
  iterations ago recorded in the one place they're supposed to live, closing a bookkeeping gap.

## Changed Behavior

- **Forward-return evidence calculation (Backtest page, and the underlying data behind it)**: previously,
  computing this evidence read the ENTIRE relevant portion of the two largest database tables into memory
  at once before doing any math on it. Now it reads the same data in small pieces, doing the same math
  incrementally, and discards each piece once it's used. The displayed numbers are unchanged; only how
  much memory the calculation needs at any one moment is different (much less).

## Backend-Only Items

None — this is an internal change to an existing calculation with no new endpoint, page, or user-facing
control. The Backtest page and its API already existed and are unchanged in what they display.

## Incomplete Items

- **The full-scale, real-database measurement pass is not done yet.** The spec calls for one supervised
  run of the fixed calculation against the ACTUAL, full-size project database (rather than the small
  test versions used to prove correctness above), measuring: (a) how much memory the real calculation
  peaks at, compared against the project's hard memory ceiling, (b) whether the backend keeps answering
  health checks throughout, and (c) how fast the backend starts up. This requires starting the actual
  backend server, which was not possible this turn (the servers were off, and this session's setup does
  not allow this agent to start them). Everything needed to fix the underlying problem and prove it works
  on realistic data sizes IS done; only this one supervised, full-scale confirmation run remains, and the
  exact steps for it are written down in `reports/perf-budgets.md` for whoever runs it next.
- **Browser-based regression checks are not part of this developer turn.** Confirming that the app's
  "is the backend ready?" indicator never freezes or goes blank while this fixed calculation runs during
  a real, browser-driven data-loading job is the next pipeline stage's job (browser-based QA), not
  something this turn produces evidence for.

## Config and Environment Changes

None. No new environment variables, config file entries, or database schema changes. The existing
`read_batch_size` setting (already used elsewhere in the project for exactly this kind of "read data in
small pieces" behavior) is reused as-is — no new setting was invented for this.

## Known Limitations

- Two groups of existing automated tests were intentionally not re-run this turn because they each
  require loading the ENTIRE real 30-year project dataset into a fresh copy first (a slow, multi-minute
  setup step this project's own conventions say to avoid unless directly necessary). Neither group tests
  the specific calculation that changed; correctness for those code paths is instead covered by the
  byte-for-byte-identical-results proof described above, which directly targets the changed calculation
  across every relevant input.
- One pre-existing, unrelated test failure (a stale test expecting an old, incomplete list of database
  table names) continues to fail, exactly as it has since an earlier iteration — untouched and unrelated
  to this change.
- The servers (backend and frontend) were off for this entire turn and were not started, per this
  iteration's explicit operating instructions. This did not block anything in this turn's actual scope,
  since all new proof-of-fix tests run against small, disposable, self-contained test databases rather
  than the live app.
