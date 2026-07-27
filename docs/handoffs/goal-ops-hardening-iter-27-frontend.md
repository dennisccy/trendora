# goal-ops-hardening-iter-27 Frontend Handoff

**Phase:** goal-ops-hardening-iter-27
**Date:** 2026-07-26
**Agent:** developer
**Status:** complete

## What Was Built

One new labeled state on the ALREADY-SHIPPED Data Manager coverage panel (`/data`) — no new page, panel,
route, or user action. When the backend's `GET /api/data` response carries `coverage.coverage_status ===
"stale"` (a real, previously-computed coverage snapshot survives under an older internal dataset version —
see the dev handoff for the backend root cause), the panel now discloses that honestly instead of silently
looking identical to the two OTHER states (`"current"` and `"not_yet_computed"`, both unchanged).

- **`CoveragePanel` (`apps/frontend/app/data/page.tsx`)** — added one conditional notice directly below the
  panel title, before the existing metric grid:
  > Coverage as of a prior scan (version {stale_dataset_version}) — refreshes on the next data job

  Rendered only when `coverage_status === "stale"`; `data-testid="coverage-stale-notice"` for QA/test
  targeting. Styled with the panel's existing muted/calm text tone (`text-text-muted`, a thin
  `border-b`/`bg-surface-2` divider matching the panel's other section dividers) — deliberately NOT an
  alarming/warning color, per the spec ("this is a routine, expected state, not an error").
  - The existing metric grid (price history, universe counts, snapshot dates, etc.) needed NO code
    change for the stale case: the backend already serves the OLDER row's real figures verbatim in the
    SAME `price_start`/`price_end`/`universe_count`/etc. fields the grid already reads — no client-side
    derivation was added or needed.
  - The `not_yet_computed` (genuinely never-computed DB) empty-state rendering is byte-unchanged — it was
    already the same all-zero grid render as today; only `"stale"` gets the new notice.
- **`DataCoverage` interface (`apps/frontend/lib/api.ts`)** — added the three new fields
  (`coverage_status: "current" | "stale" | "not_yet_computed"`, `stale_dataset_version: string | null`,
  `stale_computed_at: string | null`) with comments explaining each state.

## Files Changed

- `apps/frontend/app/data/page.tsx` -- `CoveragePanel` renders the new conditional stale notice
- `apps/frontend/lib/api.ts` -- `DataCoverage` interface gains the 3 new fields

## Visual Verification

No frontend unit test framework covers this file (this project's `.test.ts` files run via Node's native
TS stripping, one file at a time — there was no existing `CoveragePanel`-focused test file to extend, and
the spec's own test plan routes TC-6 through browser-qa, not a frontend unit test). Instead:

- `npx tsc --noEmit -p tsconfig.json` (whole-project type-check): zero errors.
- Live verification in a real browser (Chrome, via the browsing skill) against a live backend that had
  naturally reached the `"stale"` state (see the dev handoff's "Live Verification" section for how that
  state was reproduced): the page rendered the exact label text specified in the spec, in the panel's
  existing calm/muted tone. Screenshots saved to `runs/goal-ops-hardening-iter-27/coverage-stale-panel.png`
  (full page) and `coverage-stale-label-only.png` (cropped to the new notice).

## Known Issues

- A full QA pass (both viewport and full-page captures, plus the `current`/`not_yet_computed` states side
  by side for visual contrast) is left to the downstream browser-qa-agent step — this developer pass
  verified the `"stale"` state renders correctly live but did not re-capture the two unchanged states
  (their code path is untouched, and the existing golden/smoke coverage for J-05 already exercises them).
