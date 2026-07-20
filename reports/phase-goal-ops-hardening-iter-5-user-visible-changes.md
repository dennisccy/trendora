# Phase goal-ops-hardening-iter-5 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-5
**Date:** 2026-07-20
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- None. This iteration (J-06, "Pages load only what they need") was scoped as a measurement + code-audit
  pass with only a *contingent* new capability — an honest loading indicator, but only on a page found
  over its committed latency budget. No page was over budget on the final clean measurement, so that
  contingent frontend work was never triggered, and no new capability was added anywhere in the product.

---

## What Changed in the Visible UI

- **Data Manager (`/data`) — the "Refreshed: ..." line can now show one more item.** This page already has
  a small text line (component `BackfillBreakdown`, `data-testid="aggregates-refreshed"`) that lists,
  generically, whichever behind-the-scenes aggregates a backfill/rebuild job's finalize step just warmed —
  it displays whatever list of names the backend sends, with underscores turned into spaces (e.g.
  "coverage, market phase, research hot keys"). This iteration's backend change adds a brand-new possible
  entry to that backend-sent list — `forward_aggregates`, shown as **"forward aggregates"**. So after a
  **"Backfill snapshots"**, **"Fetch + backfill"**, or **"Rebuild snapshots for current universe"** job
  completes successfully, this line will typically read something like "Refreshed: coverage, market phase,
  forward aggregates, research hot keys" — one new word inside a line that already existed. This appears in
  all three places that share this one component: the live Job progress panel while/after a job runs, the
  cross-session "last run" summary card, and the matching row of the Run History table below it.
  No frontend file was changed to produce this — the existing generic renderer simply received a new value
  from the backend. (This side effect is not called out in the dev handoff, which focused on the
  loading-indicator contingency; it was found by reading `apps/frontend/app/data/page.tsx`'s
  `BackfillBreakdown` component and the backend's finalize-hook diff directly.)
- No other visible display, label, or layout changed anywhere in the product this iteration.

---

## What Old Behavior Changed

- **Backtest page (`/backtest`) — the "evidence by horizon" panel now loads dramatically faster.**
  Previously, opening this page (for any as-of date whose statistic wasn't already fresh) could take
  roughly 35 seconds for its main data panel to populate, because the backend recalculated a large
  statistic from scratch on every single view. It now populates in well under a second for the current
  (most recently ingested) date. The existing loading skeleton shown while data is in flight is unchanged
  and was already present during that old 35-second wait — the page was never blank or frozen even
  before this fix — but the wait itself is now essentially gone. The numbers the panel shows are
  byte-for-byte identical to before; only the speed changed.
- **Data Manager (`/data`) — backfill/rebuild jobs may now take a little longer to reach "completed."**
  The speed fix above works by pre-computing the Backtest page's statistic once, right after new data is
  ingested, instead of on every page view. That means a "Backfill snapshots," "Fetch + backfill," or
  "Rebuild snapshots for current universe" job's finalize step now does up to 5 extra calculations (one
  per configured lookback horizon) before the job reports as fully complete. In the worst case (the first
  time this cache is warmed for a given date) this can add up to roughly the same ~35 seconds the Backtest
  page itself used to spend — but only once per ingest job, not once per page view afterward. While this
  is happening, the job card's live "updated Ns ago" heartbeat keeps refreshing rather than going stale, the
  same way it already behaves during the job's other finalize steps — so the job does not look frozen, it
  may just take a bit longer to reach its final status badge. A plain "Fetch EOD prices" job (fetch-only,
  not backfill/both/rebuild) is unaffected — it never runs this finalize step, before or after this change.

---

## Not Visible Yet

- None. Every code change this iteration lands on a value already reachable through an existing page
  (`/backtest`) or an existing generic display (`/data`'s "Refreshed: ..." line) — nothing was built
  without a UI path this iteration.
