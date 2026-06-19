# Iteration 37 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37
**Date:** 2026-06-19
**Written by:** developer

---

## Features Implemented

- **Restored the "load each stock's price history only once per backfill job" guarantee.** When the
  system rebuilds or extends its daily snapshots across many dates in parallel, it now loads every
  stock's price series at most once for the whole job — including stocks in the candidate list that have
  no price bars at all. The previous iteration accidentally re-loaded those bar-less stocks once per date
  and per worker, which made a full rebuild far slower and tripped an internal correctness check. No
  numbers that users see changed — this is purely a how-it-loads fix.

---

## Changed Behavior

- **Data Manager `/data` page reliability:** Previously, the per-date universe diagnostic and the
  membership-timeline computation re-queried the database repeatedly for stocks that have no price
  history, making the underlying work slower than it needed to be. Now those stocks are accounted for
  once up front, so the work is bounded and the served values are exactly the same as before.

---

## Backend-Only Items

- None. This iteration changed only how existing data is loaded internally; it adds no new endpoint,
  no new screen, and no new displayed value.

---

## Incomplete Items

- **Optional `/api/data` speed-up (descoped, allowed by the spec):** The plan recommended (but did not
  require) caching the remaining ~10-second per-request coverage calculation so the `/data` page loads
  in under a second even under concurrent use. That optimization was intentionally left out this
  iteration to keep the change small and low-risk — see Known Limitations. The required primary fix (the
  load-once guarantee) is complete.

---

## Config and Environment Changes

- None. No new environment variables, config keys, migrations, or database tables.

---

## Known Limitations

- **The `/data` page still takes roughly 10 seconds to load on the full historical database.** A single
  user opening `/data` will see it populate within that window. The remaining cost is a per-request
  calculation of the as-of-date universe coverage (not the membership timeline, which is already cached).
  Because one such request holds a database connection for those ~10 seconds, opening or refreshing
  `/data` two or more times at once can briefly pressure the database connection pool. The recommended
  way to verify `/data` live is a single page load with a ~30-second wait — not repeated/concurrent
  loads. A future iteration can cache this coverage block (keyed to the existing dataset-version stamp)
  to make `/data` sub-second; the approach is documented in the dev handoff.
- **The destructive full snapshot rebuild was NOT triggered and must not be** — the data is already
  correct; this was a read-path fix only.
