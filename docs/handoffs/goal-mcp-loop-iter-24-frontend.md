# goal-mcp-loop-iter-24 Frontend Handoff

**Phase:** goal-mcp-loop-iter-24
**Date:** 2026-07-09
**Agent:** developer
**Status:** complete

## What Was Built

- **Storage-footprint card on the Data Manager (`/data`).** A new read-only card,
  `StorageCapacityPanel`, rendering the DB's current on-disk footprint: file size (human-readable,
  e.g. "1.22 GB") and row counts for the three largest tables (`daily_prices`, `scanner_results`,
  `forward_returns`). Placed directly after the existing `CoveragePanel` in the `/data` page's render
  order (same column as `MembershipTimelinePanel`/other single-column panels).
- Reuses the EXISTING `Card` + `PanelTitle` + `DefinedMetric` composition `CoveragePanel` already uses --
  no new card primitive introduced. Grid layout matches `CoveragePanel`'s
  `grid grid-cols-1 gap-3 p-4 sm:grid-cols-2 lg:grid-cols-4` pattern (four metrics fit one row on `lg`).
- A small `fmtBytes()` helper (module-scoped in `page.tsx`, alongside the existing `fmtDuration`) formats
  the raw byte count into a human-readable size (B/KB/MB/GB/TB, 1024-based) -- pure display formatting,
  no computation of the underlying value.

## Files Changed

- `apps/frontend/lib/api.ts` -- new `DataCapacity` interface (`db_file_bytes`, `daily_prices_rows`,
  `scanner_results_rows`, `forward_returns_rows`); added `capacity: DataCapacity` to
  `DataOverviewResponse` (additive -- every existing field on that interface is unchanged)
- `apps/frontend/app/data/page.tsx` -- new `fmtBytes()` formatter; new `StorageCapacityPanel` component;
  wired `<StorageCapacityPanel capacity={state.data.capacity} />` into the page render, directly after
  `<CoveragePanel data={state.data} />`

## Data Flow

The card reads `capacity` off the SAME `GET /api/data` response the rest of the page already fetches
(`fetchDataCoverage` in `lib/api.ts` -- no new API call, no new loading/error state beyond what the page
already has). Business logic lives entirely in the backend's `compute_capacity()` -- the frontend only
formats and displays the four numbers verbatim.

## States Handled

- **Loaded (normal):** renders the real file size + three row counts.
- **Cold/empty DB:** the backend's `compute_capacity()` already returns `0`/`"0 B"`-formattable values
  on an empty database (never null, never an error) -- so no separate empty-state branch was needed in
  the component; `fmtBytes(0)` renders `"0 B"` naturally.
- **Backend fetch failure:** falls through to the `/data` page's EXISTING "Backend unavailable" error
  card (the `state.kind === "error"` branch) -- no second, duplicate error UI was introduced for this
  one card, matching the plan's explicit instruction.
- **Loading:** covered by the page's existing `DataSkeleton` (shown while `state.kind === "loading"`,
  before the whole overview -- including `capacity` -- has loaded).

## Tests Run

- `npx tsc --noEmit` (from `apps/frontend/`): clean, exit code 0.
- `npx next build` (via `scripts/start-frontend.sh`'s own rebuild-on-stamp-mismatch logic, exercised
  live): succeeded, producing a working production bundle -- confirms the new component compiles and
  bundles correctly, not just typechecks.
- Live verification: brought up the backend + this frontend build in prod mode
  (`start-backend.sh`/`start-frontend.sh`, ports 8255/3255), confirmed `GET /api/data` serves the
  `capacity` field with real numbers (`db_file_bytes: 1307414528`, `daily_prices_rows: 3293160`,
  `scanner_results_rows: 165755`, `forward_returns_rows: 821054`) and that `/data` returns HTTP 200 with
  a valid server-rendered HTML shell. Did not do a full browser-driven visual/interactive check of the
  rendered card (no browser automation tool in this role) -- that verification belongs to the
  browser-qa-agent stage per the pipeline; the DoD's "browser-verified" storage-card item should be
  confirmed there against a live, non-empty evidence dir.

## Known Issues

- No dedicated frontend unit/component test exists for `StorageCapacityPanel`/`fmtBytes` -- this project
  has no jest/testing-library harness configured (confirmed: `package.json` has no `test` script and no
  test runner dependency), consistent with how every other component in this codebase is verified (`tsc`
  + `next build` + live/browser-qa, not unit tests). This matches the existing project convention, not a
  gap introduced by this iteration.
- Deep interactive/visual confirmation of the card's real-data rendering (matching the DoD's "browser-
  verified" requirement) was not performed by this developer pass -- see the QA/browser-qa stage for
  that check.
