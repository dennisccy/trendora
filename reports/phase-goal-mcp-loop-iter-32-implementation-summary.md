# goal-mcp-loop-iter-32 — Implementation Summary

**Phase:** goal-mcp-loop-iter-32
**Date:** 2026-07-14
**Written by:** developer

---

## Features Implemented

- **Certification-budget accounting panel** (`/research/budget`): a new, read-only page that shows,
  before any new scan is proposed, exactly how much of the platform's statistical "credibility budget"
  has already been spent. It shows four figures — how many trials have been run so far, how strict the
  bar for the next trial will be, how much of the reusable-holdout budget is left, and how much
  capacity the internal exploration economy has left — each with a small trend chart showing how that
  figure has moved trial by trial. Today it shows: 7 trials run, next trial judged at 1-in-160 odds
  (0.00625), 90% of the holdout budget remaining, and the internal exploration economy's next-trial
  bar at roughly 4-in-10,000 odds.
- **New "Certification-budget accounting" card** on the Research hub page, next to the existing
  "Pre-registration registry" and "Negative-results graveyard" cards, so the new panel is reachable in
  two clicks from anywhere in the app (Research → this card).

## Changed Behavior

None. This is a purely additive read-only page — no existing feature's behavior changed.

## Backend-Only Items

None. The new backend accounting logic (`app/engine/budget_accounting.py`) and its endpoint
(`GET /api/research/budget`) are both fully wired to the new page — nothing was built without a
corresponding UI.

## Incomplete Items

- **Browser-verified click-through**: this handoff confirms the panel via direct API/HTTP checks and a
  live-server smoke test (all pages return correctly, the numbers match the ledger on disk), but an
  actual in-browser click-through (clicking the new card, watching the four numbers and trend lines
  render) has not yet run. That is the next pipeline step (browser QA), not something left undone by
  this implementation.
- **J-19 re-verification (the "click a graveyard entry and land on the right registry row" journey)**:
  the underlying fix was already in place before this iteration started and required no code changes
  here. What's still needed is a fresh browser-verified confirmation against this iteration's final
  build — also the next pipeline step, not a gap in this implementation.

## Config and Environment Changes

None. No new environment variables, config file changes, or database migrations. The new panel reads
existing, already-configured ledger locations and existing statistical-economy settings (the same ones
the certification process itself already uses) — nothing new to configure.

## Known Limitations

- The panel is descriptive only — it has no alerts or per-category breakdowns (those are explicitly
  planned as separate, future additions, not part of this iteration).
- Because today's real data has all 7 trials registered on the same date, the "trials over time" trend
  line looks like a simple staircase rather than a spread-out timeline — this is an honest reflection
  of the real data, not a display bug, and it will show real spacing once trials happen on different
  dates.
- A small, unrelated batch of leftover work-in-progress from an earlier, stalled iteration was noted in
  this iteration's plan as pre-existing; by the time work started, it was no longer present in the
  working files, so it required no action here. A few pipeline-internal bookkeeping files (progress
  logs, not product code) show as changed as a normal side effect of the automation process running —
  this is expected and unrelated to the feature described above.
