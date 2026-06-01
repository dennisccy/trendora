# goal-i_can_see_the_wealthy_future_forever-iter-3 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-3
**Date:** 2026-06-01
**Agent:** developer
**Status:** complete

## What Was Built

- **`/data` Data Manager page** (`apps/frontend/app/data/page.tsx`) — a new dense-dark analytical screen:
  - **Coverage panel** — price-history range, symbol count, trading-day count, snapshot-date count, and
    backfill gap count + gap range (amber when gaps exist). All figures are server values, monospace
    (`num`), re-formatted only — nothing is computed client-side.
  - **Job form** — `Start date` / `End date` (`<input type="date">`) + a job-kind `Select`
    (Backfill / Fetch / Fetch+backfill) + a Start CTA (`--accent`). The range is pre-filled once from the
    real gap dates so the default Start does useful work. **These date inputs are job parameters only —
    they are NOT wired to `useAsOf`; they never change the global viewing date** (J-18 preserved).
  - **Live progress panel** — polls `GET /api/data/jobs/{job_id}` every second; shows a determinate
    progress bar (`symbols X/Y`, `snapshots A/B dates`), a status badge (running/ok/partial/failed using
    `--pos`/`--warn`/`--neg`/`--accent`), counts (new bars / snapshots / forward returns), and an explicit
    error card listing per-symbol failures (never a fabricated success).
  - **Run history table** — recent fetch/backfill runs (+ seed load) from `GET /api/data`: started, kind,
    range, status, symbols ok/failed, snapshots, summary. Empty-state when there are no runs yet.
  - Loading skeleton + a styled "Backend unavailable" error card.
- **Global as-of switcher refresh** (`apps/frontend/components/asof-provider.tsx`) — added an additive
  `refresh()` to the context that re-fetches `GET /api/runs`. The Data Manager calls it on job completion
  so **newly created snapshot dates become selectable in the global switcher without a hard reload**.
  `refresh()` only updates the available `dates`/`latest`; it never changes the user's current `asOf`
  selection (backfilling older dates leaves `latest` and the current view untouched).
- **Sidebar entry** (`apps/frontend/components/sidebar.tsx`) — one additive nav item
  `{ href: "/data", label: "Data Manager", icon: Database }` (the blueprint-approved home for J-17).
- **API client** (`apps/frontend/lib/api.ts`) — typed `fetchDataCoverage()`, `startDataJob(kind,start,end)`,
  `fetchDataJob(jobId)` + the `DataCoverage` / `DataRun` / `DataOverviewResponse` / `DataJob` /
  `StartJobResponse` / `DataJobKind` types. Errors throw the backend's honest `detail` so the UI shows an
  explicit failure.

## Files Changed

- `apps/frontend/app/data/page.tsx` — **new** Data Manager page (coverage, job form, live progress polling, run history).
- `apps/frontend/components/asof-provider.tsx` — added additive `refresh()` (extract loader to `useCallback`; expose in context).
- `apps/frontend/components/sidebar.tsx` — added the `Data Manager → /data` nav entry + `Database` icon import.
- `apps/frontend/lib/api.ts` — added the Data Manager types + `fetchDataCoverage` / `startDataJob` / `fetchDataJob`.

## Tests Run

Command: `cd apps/frontend && npm run build`
Result: ✓ Compiled successfully, types valid, all 13 routes generated (incl. `○ /data`, 6.3 kB). No type errors.

UI behavior (workflows, states) is covered by browser QA, not a unit suite (per project-template).

## Design System Conformance

- shadcn/ui components only (`Card`, `Badge`, `Select`, `EmptyState`, `PageHeading`); no raw-div soup.
- Palette tokens only — `--accent` (Start/running), `--pos`/`--neg` (ok/failed counts), `--warn`
  (partial / gaps present), `--surface`/`--border` (panels). No arbitrary hex.
- Monospace/tabular (`num`) for every figure; 4px spacing grid; responsive (single-column stack on mobile,
  tables scroll horizontally).
- Loading (skeleton), empty (EmptyState), error (styled `--neg` card), in-progress (Start disabled +
  spinner), done (final summary + refreshed history) states all handled.
- Interactive elements carry hover/focus/active states (inherited from the shared field/CTA/Select styles).

## Known Issues

- Live "fetch" cannot retrieve real data here because Stooq now requires an API key (the UI shows this as
  an explicit per-symbol failure with zero fabricated prices — correct behavior). J-17's acceptance flow
  uses the offline **backfill** path, which is fully functional. See the dev handoff for detail.
- Live job progress is in-memory on the backend (resets on backend restart); the final summary of every
  run persists in the run-history table.
