# goal-i_can_see_the_wealthy_future_forever-iter-17 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-17
**Date:** 2026-06-04
**Agent:** developer
**Status:** complete

## What Was Built

- **Backtest evidence-aggregate section (J-09/J-10/J-16/J-28)** — a new, clearly-labelled
  "Forward-tested evidence (expanding window ≤ D)" block at the **very bottom** of `/backtest` (after the
  leadership lists), rendering from the single `/api/backtest` payload's `evidence_by_horizon[selectedHorizon]`:
  - Summary line: snapshots contributing (`n_runs`), the contributing as-of range, mean stock forward
    return + `n` — the visible proof the sample shrinks as the as-of date moves earlier.
  - Panels: forward return **by A–E bucket**, **excess vs SPY & QQQ**, **by setup**, **by regime**,
    **VCP-vs-non-VCP**, **pullback-to-rising-DMA** and **flat-base-breakout** breakdowns, and the
    **control-group comparison** — each cell with `n`, honest NA below `min_sample`, survivorship label.
  - Re-points on (a) the global as-of switcher (the existing `[asOf]` fetch effect) and (b) the existing
    client-side horizon selector (**no refetch** — it selects a different key in the already-fetched payload).
- **System Health page + sidebar entry removed** — `/system-health` no longer exists; the sidebar lost
  its "System Health" item (and the now-unused `Activity` icon import).
- **Shared evidence panels module** — the panels (`BucketPanel`, `ExcessPanel`, `BreakdownPanel`,
  `ControlGroupPanel`, and the top-level `EvidenceAggregateSection`) were extracted from the deleted
  System Health page into `components/evidence-panels.tsx`, so the contract value has **one** UI home.

## Files Changed

- `apps/frontend/components/evidence-panels.tsx` — **new**; the shared forward-tested evidence panels +
  `EvidenceAggregateSection` (extracted from the retired System Health page).
- `apps/frontend/app/backtest/page.tsx` — render `EvidenceAggregateSection` at the bottom of
  `BacktestResults`, keyed off `backtest.evidence_by_horizon[selected.horizon]` (the same lifted horizon
  view-selector that already drives attribution + leadership returns). No new date state added.
- `apps/frontend/lib/api.ts` — renamed `SystemHealthResponse` → `EvidenceAggregate`; added
  `evidence_by_horizon: Record<number, EvidenceAggregate>` to `BacktestResponse`; **removed**
  `fetchSystemHealth`; updated the section comment.
- `apps/frontend/components/sidebar.tsx` — removed the `/system-health` NAV entry + the unused `Activity`
  icon import.
- `apps/frontend/app/system-health/page.tsx` — **deleted** (after extracting the shared panels).

## Design / DESIGN-SYSTEM conformance

- Reuses existing components only — `Card`, `Badge`, the shared `Return`/`SampleSize`/`fmtPct` cells,
  `bucketVariant`, `EmptyState`. Numbers are monospace (`num`); A–E buckets are colour-graded green→red
  via `bucketVariant`; NA uses the muted/`--warn` tokens; no arbitrary hex/spacing. Loading skeleton,
  backend-unavailable, and empty/NA states are all handled.
- The evidence section is **visually distinct** from the per-date scorecard and explicitly labelled the
  expanding-window aggregate ("every snapshot dated ≤ D") vs the scorecard ("what this date's cohort did").

## J-21 ordering preserved

The page order is unchanged where it matters: as-of scan summary → forward-test scorecard → **Return
Attribution** (the single, per-date attribution section, with the horizon selector) → **Top Sectors /
Top Themes / Ranked Cohort** (leadership lists, still BELOW Return Attribution) → the new evidence
aggregate at the very bottom. There is exactly **one** "Return attribution" heading on the page (the
aggregate's attribution value is served in the payload but not rendered as a second attribution section,
deliberately, to avoid any J-21 ambiguity).

## Tests Run

Command: `cd apps/frontend && npm run build` (compiles + typechecks)
Result: **✓ Compiled successfully**; 13 routes generated (was 14 — `/system-health` gone); `/backtest`
grew to 9.54 kB. Type-check clean. The production `.next` was removed afterward so the browser-QA agent
starts `next dev` on a clean cache (iter-15 lesson).

## Known Issues

- None functionally. UI behaviour (the as-of re-point, the n-drop, no page-local date control) is covered
  by browser QA, not a unit suite. The `EvidenceAggregateSection` carries `data-testid="evidence-aggregate"`
  and the summary line `data-testid="evidence-summary"` to anchor the browser assertions.
