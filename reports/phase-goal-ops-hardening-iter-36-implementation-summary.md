# goal-ops-hardening-iter-36 — Implementation Summary

**Phase:** goal-ops-hardening-iter-36
**Date:** 2026-07-30
**Written by:** developer

---

## Features Implemented

- **Bounded candidate-pool bar loading for the membership timeline**: when the backend refreshes its
  "how has the tradeable universe changed over time" data (shown on the Data page), it used to load every
  tradeable stock's entire 30-year price history into memory at once before it could answer. It now loads
  that data in small batches (50 stocks at a time), processes each batch, and discards it before loading
  the next. Measured on the real database, this cut the peak memory this step uses by about 71%. The
  numbers shown on the Data page are unchanged — this is purely an internal efficiency fix.
- **Bounded per-claim evidence read on the Evidence page**: the "drawdown & dry-spell expectations" panel
  shown under each proven/unproven claim on the Evidence page reads its supporting data in smaller pieces
  instead of one large read. This reduces (but does not eliminate) how much memory a single claim's panel
  needs when many stocks and many years of history are involved. The figures shown are unchanged.
- **Honest "still computing" and Retry on 4 more Research pages**: the Factor Lab, Market Phase & Severity
  Lab, Regime × Phase × Factor, and Severity-velocity × Regime pages now show the same "Still computing —
  Ns elapsed" message with a spinner (instead of a plain unlabelled loading animation) when a page takes a
  while to load, and a working Retry button if the backend is briefly unreachable. This already existed on
  the Regime Lab page; it is now consistent across all 5 Research labs.

---

## Changed Behavior

- **Data page coverage refresh**: previously, refreshing the "universe membership timeline" data always
  loaded the entire price history for every stock into memory first. Now it loads it in small batches. The
  numbers shown to the user are byte-for-byte identical before and after — only how the backend computes
  them internally changed.
- **Evidence page per-claim panels**: previously, a claim covering many stocks and many years read all of
  its supporting price-return data in one large database read. Now it reads that data in smaller chunks.
  The figures shown are byte-for-byte identical; the difference is only in how much memory the read needs
  at its peak.
- **4 Research lab pages' loading/error screens**: previously these showed a plain animated placeholder with
  no explanation while loading, and an error message with no way to retry if the backend was unreachable.
  Now they show the same clear "still working" message and a working Retry button already used on the
  Regime Lab page.

---

## Backend-Only Items

None — both backend fixes are internal-only with no user-visible change in the numbers shown; the frontend
change (the loading/retry wiring) is the user-visible counterpart already described above.

---

## Incomplete Items

- **The evidence-panel memory fix is a partial improvement, not a full guarantee.** Testing on the real
  database showed the fix reduces the peak memory a single claim's panel needs by only a modest amount
  (roughly 4%), because most of the memory that panel uses comes from an earlier, unrelated step that this
  iteration did not touch (deliberately, per the approved plan). Under a very heavy load, this panel can
  still show its honest "not available right now" message instead of the figures — exactly as it already
  did before this change, just less often. This is disclosed in detail in the developer handoff and in
  `reports/perf-budgets.md`.
- **A pre-existing test failure was found, not caused by this work.** One automated test
  (`test_kdate_backfill_loads_each_symbol_at_most_once`) already failed before this iteration started — a
  multi-day historical data backfill loads each stock's price history 3 times instead of the ideal 1, due
  to a separate, unrelated internal step. This iteration's fix reduced that to 2 times (an improvement, not
  a regression), but did not fully resolve it, since fully resolving it was outside this iteration's
  approved scope. Recorded as a follow-up item for a future iteration.

---

## Config and Environment Changes

- `research.membership_timeline_batch_symbols` (in `config.yaml`) — how many stocks' price history the
  Data-page refresh loads into memory at once when recomputing the universe-membership timeline. Default:
  `50`.
- `research.drawdown_expectations_ticker_chunk` (in `config.yaml`) — how many stocks' worth of stored
  price-return data the Evidence page's per-claim panel reads at once. Default: `50`.
- No database migration — no schema change.

---

## Known Limitations

- The full automated backend regression suite (a broader battery of tests covering related data-management
  behavior, 267 tests across 8 files) was still finishing at the time this summary was written; roughly
  three-quarters had completed with zero failures. The remaining tests include one that is known to run
  for an extended time on this specific database (a documented, pre-existing characteristic of the deep
  30-year test data, unrelated to this iteration's changes).
- The frontend loading/retry changes were verified by starting the real application and confirming each
  affected page loads successfully; a full interactive browser walkthrough (watching the "still computing"
  message appear and clicking Retry) was not independently captured by this development pass and is
  expected from the browser-based QA step that follows.
