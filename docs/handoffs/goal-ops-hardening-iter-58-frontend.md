# goal-ops-hardening-iter-58 Frontend Handoff

**Phase:** goal-ops-hardening-iter-58
**Date:** 2026-08-10
**Agent:** developer
**Status:** complete

## What Was Built

- **`apps/frontend/lib/availability-empty-state.ts` (new):** a single, pure, unit-tested predicate,
  `shouldShowAvailabilityEmptyState(data: AvailabilityResponse): boolean`, returning
  `data.cells.length === 0 && !data.stale`. No React, no DOM types — mirrors the existing
  `lib/background-compute-panel-branch.ts` convention (a resolver function the component calls, kept
  testable under Node/`tsx` without a component-testing environment).
- **`apps/frontend/components/availability-heatmap.tsx`:**
  - The "No availability yet — Fetch real EOD prices" empty state now gates on
    `shouldShowAvailabilityEmptyState(state.data)` instead of the bare `state.data.cells.length === 0`
    check. Closes audit finding B5: a persisted `AvailabilityCache` row that happens to be BOTH stale
    (an ingest is mid-flight) AND empty (its stored `cells` array is empty — a narrow precondition) can
    no longer render the false "no data has ever been ingested" message. That row now falls through to
    the existing stale banner above with no grid rendered below it (there are no cells to show).
  - The stale banner's copy changed from `"Data as of {version} — updating"` to `"Data as of a prior
    scan (version {version}) — refreshes on the next data job"` — realigned with the sibling Coverage
    panel's existing `coverage-stale-notice` wording pattern (`apps/frontend/app/data/page.tsx:759-764`,
    a coherence-auditor iter-57 advisory). Same `data-testid="availability-stale-notice"`, same
    surrounding tokens (`border-b border-border bg-surface-2 px-4 py-2 text-xs text-text-muted`) — wording
    only, zero behavior/markup-structure change.
  - The component's top-of-file docstring gained a new iter-58 paragraph documenting both changes and
    pointing at the new predicate module.

No new page, route, or nav entry — this is a correctness/honesty tightening of the EXISTING `/data`
Availability heatmap widget, matching the iter spec's "New user-facing capability: None" / "UI surface
changes: ... no longer shows the false 'No availability yet' message on a stale-but-persisted row."

## Backend contract this relies on (unchanged shape, corrected computation)

`GET /api/data/availability`'s `stale`/`served_dataset_version` fields keep their iter-57 shape and JSON
types (`stale: boolean`, `served_dataset_version: string | null`) — only the BACKEND's computation of
`stale` changed this iteration (now gated on a genuinely in-flight ingest job, not stamp mismatch alone;
see the dev handoff, `docs/handoffs/goal-ops-hardening-iter-58-dev.md`, for the backend-side detail). No
frontend type (`apps/frontend/lib/api.ts`'s `AvailabilityResponse`) needed any change.

## Files Changed

- `apps/frontend/lib/availability-empty-state.ts` -- new.
- `apps/frontend/lib/availability-empty-state.test.ts` -- new, 4 tests.
- `apps/frontend/components/availability-heatmap.tsx` -- empty-state gate + banner copy + docstring.

## Tests Run

- `npx tsc --noEmit` (from `apps/frontend/`) — clean, zero type errors.
- `npx tsx lib/availability-empty-state.test.ts` — **4 passed**:
  1. never-warmed (empty cells, not stale) still shows the empty state — unchanged regression guard.
  2. TC-4's exact precondition: stale + empty cells — empty state does NOT show.
  3. non-empty, not stale — never the empty state.
  4. non-empty, stale — never the empty state (the stale banner handles it).

  (`node lib/availability-empty-state.test.ts` directly is documented as the project's nominal command,
  but this dev box's Node build lacks native TS-stripping support — the same pre-existing, documented
  limitation noted in `docs/handoffs/goal-ops-hardening-iter-25-dev.md`; `npx tsx` is the local
  fallback, same CI/QA-environment caveat as every other `lib/*.test.ts` file in this project.)

## Manual verification

Live-checked `GET /api/data/availability` against a real running backend
(`scripts/start-backend.sh`, port 8255) at rest: `stale: false`, non-empty `cells` — the unchanged idle
case renders correctly. The job-in-flight `stale: true` case and the TC-4 stale+empty case are proven by
the unit tests above (a live drill that reliably lands the request during the ~1-2 second stamp-mismatch
window before the finalize-tail warm re-runs is not a practical browser-QA target; TC-1/TC-2/TC-3's
backend-layer unit tests are the primary proof for the gating logic itself, and TC-4's frontend predicate
test is the primary proof for the empty-state gate).

## Known Issues

None beyond what's in the dev handoff (`docs/handoffs/goal-ops-hardening-iter-58-dev.md`) — this
iteration's frontend diff is small, self-contained, and does not touch any other page or component.
