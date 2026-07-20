# goal-ops-hardening-iter-2 Frontend Handoff

**Phase:** goal-ops-hardening-iter-2
**Date:** 2026-07-19
**Agent:** developer
**Status:** complete

## What Was Built

Exactly the plan's scope: **one additive read-only line** on `/data`'s existing run-detail views naming
which aggregates a completed backfill/both/rebuild run's ingest finalize hook refreshed. No new page,
panel, nav entry, button, or form — matching the plan's explicit "Explicitly out of scope" list.

- **`BackfillBreakdown` gains an optional `aggregatesRefreshed?: string[] | null` prop.** The component
  (shared by all 3 call sites) now renders TWO independent inline lines instead of one:
  - the existing four-count breakdown line (unchanged — still suppressed when all four counts are null),
  - a NEW line (`data-testid="aggregates-refreshed"`) reading `Refreshed: coverage, market phase, ...`
    (underscores replaced with spaces, comma-joined), rendered ONLY when `aggregatesRefreshed` is a
    non-null, non-empty array.
  - The component's outer suppression guard is now `!hasBreakdown && !hasAggregates` (previously "all four
    breakdown fields null") — so the component still renders nothing at all when BOTH are absent (a
    fetch/expand run, or a not-yet-computed row), but now correctly renders just the aggregates line alone
    if a future case ever had aggregates without the breakdown (does not happen today, since both come
    from the same backfill/both/rebuild-only gate, but the guard is now honest about each independently).
  - Same muted `text-xs text-text-faint` treatment as the existing breakdown line — no new color, badge,
    or emphasis, per the plan's Visual Requirements.
- **Threaded through all 3 existing call sites** (no new component, no fork):
  - `LastRunSummary` (persisted-run reduced view) — `aggregatesRefreshed={run.aggregates_refreshed}`
  - `JobProgressPanel`'s backfill section (live job view) — `aggregatesRefreshed={job.aggregates_refreshed}`
  - `RunHistoryPanel` (the Run history table) — `aggregatesRefreshed={run.aggregates_refreshed}`
- **`lib/api.ts` type updates:**
  - `DataRun.aggregates_refreshed: string[] | null` (required-but-nullable, matching the existing
    `calendar_days`-style nullability convention for a persisted/served field).
  - `DataJob.aggregates_refreshed?: string[] | null` (optional, matching the existing
    `calendar_days?`/`chunk_index?`-style live-poll convention).

## Visual/Design Compliance

- No new component — extended the existing shared `BackfillBreakdown` verbatim (added a prop, did not
  fork it), preserving the single render path across all 3 call sites exactly as the existing four
  breakdown fields already do.
- No new layout — same `Card`/`PanelTitle` structure for the Job progress panel, same `<table>` structure
  for Run history, same reduced-view `LastRunSummary` card. The new line is an additional `<p>` inside the
  same container the breakdown line already occupies.
- No new visual effect — matches the existing calm/muted `text-xs text-text-faint` inline-text treatment
  verbatim (the aggregates line omits only the `num` class the breakdown line uses, since it renders prose
  words like "coverage, market phase" rather than digits — `num` is this design system's numeric-alignment
  utility class, not meaningful here).
- No new user action — read-only, no new buttons/forms/controls.

## States Handled

- **Populated** (a completed backfill/both/rebuild run with a non-empty `aggregates_refreshed`): renders
  `Refreshed: <prettified, comma-joined list>`.
- **Null/absent** (a fetch/expand run, or a not-yet-computed/interrupted row): renders nothing — no
  placeholder, no "—", matching the existing breakdown-field convention exactly (the plan's explicit
  requirement: "omit the line entirely... never an empty placeholder").
- **Empty array** (defensively handled even though the backend never serves `[]` for a kind that reaches
  this gate — only `null` or a non-empty list per `_run_detail`'s gating): `hasAggregates` requires
  `.length > 0`, so an empty array also renders nothing, not a bare "Refreshed:" label.

## Files Changed

- `apps/frontend/app/data/page.tsx` — `BackfillBreakdown` (new prop + second conditional `<p>`, wrapped in
  a fragment), 3 call sites (`LastRunSummary`, `JobProgressPanel`, `RunHistoryPanel`) each pass the new
  prop. Net +21/-4 lines.
- `apps/frontend/lib/api.ts` — `DataRun` gains 1 required-nullable field; `DataJob` gains 1 optional field.

## Tests Run

- `npx tsc --noEmit -p tsconfig.json` — clean, zero errors, confirming `api.ts` and `page.tsx` type-check
  correctly together (the new prop, the new interface fields, and every one of the 3 call sites).
- No frontend unit/component test suite exists in this repo beyond the type-check (confirmed: no
  `apps/frontend/**/*.test.*` or `__tests__/` convention; `package.json`'s only scripts are
  `dev`/`build`/`start`/`lint` — same finding iter-1's frontend handoff recorded).
- Did **not** run `npm run build` or `npm run lint` (same reasoning as iter-1: `tsc --noEmit` covers the
  type-safety surface a build additionally checks; lint is style-only).
- Did **not** drive a live browser against a real backfill job that populates `aggregates_refreshed` with
  real data (see the dev handoff's Tests Run section: no real ingest job was run against the committed
  seed DB this pass, to avoid pre-empting the fresh unsnapshotted date the browser-qa-agent's J-05
  walkthrough needs to observe). The rendered line was verified by static/type-level review against the
  component's existing, already-battle-tested null-suppression pattern only — the browser-qa-agent's live
  run is what verifies the actual rendered pixels/DOM for TC-20.

## Known Issues

- The new line's actual rendering (a real `Refreshed: coverage, market phase, membership timeline, ...`
  string, in a real browser, against a real completed run) has not been visually confirmed by this step —
  only type-checked and read carefully against the existing `BackfillBreakdown` pattern the four prior
  fields already exercise successfully in production. This is exactly the kind of check the
  browser-qa-agent's J-05 walkthrough is designed to catch if the actual rendering has any surprise.
- The category strings are prettified with a simple `s.replace(/_/g, " ")` (e.g. `"market_phase"` →
  `"market phase"`, `"research_hot_keys"` → `"research hot keys"`) — a minimal, no-lookup-table
  transformation per the Simplicity Bar, not a full label dictionary. If a future category name reads
  awkwardly once de-underscored, that is a one-line fix in `BackfillBreakdown`, not a data-contract change.
