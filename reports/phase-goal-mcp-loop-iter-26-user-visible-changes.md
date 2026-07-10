# Phase goal-mcp-loop-iter-26 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-26
**Date:** 2026-07-10
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Nothing new. This iteration adds no new page, endpoint, button, form, or displayed value. Every
  action available to a user before this iteration (Fetch, Backfill, warm-up on `/data`; browsing
  `/stocks` and ticker detail pages; viewing `/evidence`) is still exactly the same set of actions,
  unchanged.

---

## What Changed in the Visible UI

- Nothing. Zero files under `apps/frontend/` were touched by this iteration (confirmed via `git diff
  --stat` — every changed file is under `apps/backend/`, `config.yaml`, or `reports/`). Every route,
  component, label, layout, and pixel is byte-identical to the pre-iteration UI. The execution plan
  itself states this explicitly: "No new user-facing capability... no frontend source change."

---

## What Old Behavior Changed

- **Backfill and warm-up data jobs now complete materially faster.** The developer's measured,
  real-data before/after numbers (same host, prod-mode memory cap, committed 30-year database):
  - Per-date scoring on the latest deep-history cadence date: 1.68 s → 0.32 s (**81% faster**)
  - A 12-date deep-history warm-up sample: 10.17 s → 2.25 s (**78% faster**)
  - The warm-up's realized-forward-return read step (6,110 stock-date lookups): 2.81 s → 0.30 s
    (**89% faster**)

  A user starting a Backfill or warm-up job from `/data` will see the job finish sooner than before.
  The job-progress panel's own DISPLAY behavior must stay exactly as it was — this iteration's
  Definition of Done requires browser-qa to confirm the panel still ticks `done/total` incrementally
  and honestly on the faster backend, never jumping straight to "done" and never marking partial data
  as complete. If the panel's honesty regresses because the backend now finishes faster, that would be
  a genuine defect of this iteration, not an intended change — it is called out here as the one
  behavior a re-tester must watch closely.

- **The underlying scoring computation changed its input scope, but not its output.** Each stock's
  score is now computed from a bounded ~320-trading-day trailing slice of price history instead of the
  full multi-decade history that was being fed in before. A new automated test
  (`test_scoring_window.py`) proves this produces byte-for-byte identical output — every score, bucket,
  and detected pattern — across 3 real historical dates and the full ~583-stock pool. **No value shown
  anywhere in the product (`/stocks`, a ticker detail page, `/evidence`, etc.) changes as a result of
  this iteration.** This item is listed here only because the compute path behind those displays did
  change, even though the displayed result did not — a re-tester comparing before/after screenshots of
  any score, bucket, or pattern flag should see no difference.

---

## Not Visible Yet

- The measured performance numbers above (81% / 78% / 89% faster; peak RSS 1,330.6 MB, under the
  6,144 MB cap) are recorded only in the committed engineering report `reports/perf-budgets.md` (a new
  "Item F" section). They are not surfaced anywhere in the product UI — there is no "jobs are now
  faster" banner, timer, or speed indicator on `/data`, nor was one in scope for this iteration.
