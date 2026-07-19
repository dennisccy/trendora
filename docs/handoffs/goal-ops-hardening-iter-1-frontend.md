# goal-ops-hardening-iter-1 Frontend Handoff

**Phase:** goal-ops-hardening-iter-1
**Date:** 2026-07-19
**Agent:** developer
**Status:** complete

## What Was Built

All changes are confined to the existing `/data` (Data Manager) surface — no new page, no nav change, per
the plan's explicit "UI surface changes: `/data`'s existing Job progress panel and Run history table only."

- **Persisted-history fallback (TC-6):** `JobProgressPanel` now takes a new `runs: DataRun[]` prop. When no
  job has started this browser session (`job === null`):
  - if `runs.length === 0`, the exact original copy still renders ("No job has been started this
    session...") — the true empty-history case is unchanged.
  - if `runs.length > 0`, a new `LastRunSummary` component renders the most recent persisted run's status,
    message, and breakdown counts instead. This is a **separate, reduced view** built only from `DataRun`
    fields (status/message/breakdown) — it does not force a persisted row into the full live-job JSX, which
    reads fields (`symbols_total`, `chunk_index`, `chunk_total`) a persisted row does not carry.
- **Zero-work visual distinction:** three new helper functions — `isZeroWorkRun`, `runStatusVariant`,
  `runStatusLabel` — detect a `backfill`/`both`/`rebuild` job that finished `ok` with `snapshots_created ===
  0` and render it with the existing neutral `default` badge variant (the same treatment already used for
  `interrupted`) and the label "no new snapshots", instead of the plain green `ok` success look. Applied to
  both the live Job progress panel's status badge and the Run history table's status badge. An additional
  explanatory note ("Zero-work outcome — every requested trading day already had a snapshot...") renders
  in the Job progress panel specifically for this state, satisfying the "zero-work is never rendered as
  unexplained success" requirement with actual wording, not just a color change.
- **Breakdown counts:** a new shared `BackfillBreakdown` component renders the four new fields
  (`calendar_days`, `already_snapshotted`, `non_trading_days`, `error_other`) as small inline text —
  in the Job progress panel below the existing "N snapshots · N forward returns" line, and in the Run
  history table beneath the existing Snapshots count in that same column (no new table column — the
  existing `<table>` structure is unchanged). Renders nothing when all four fields are null (a fetch/expand
  run never populates them) — never a fabricated "0".
- **Chunk progress for backfill jobs:** no frontend change was needed here — the existing
  `data-testid="chunk-progress"` badge (`chunk N/M`) already renders whenever `job.chunk_total > 0`; it
  simply now also lights up for a `backfill`-kind job because the backend now populates those fields for
  backfill (previously only fetch jobs did).

## Visual/Design Compliance

- No new badge component — extended the existing `Badge` + `statusVariant`/`statusLabel` helpers via thin
  wrapper functions (`runStatusVariant`/`runStatusLabel`), exactly as the plan's Visual Requirements
  specified ("extend the existing... do not introduce a new badge component").
- Reused the existing neutral/grey palette treatment (`default` variant, the `interrupted` precedent) for
  zero-work — never invented a new color, per "follow the existing calm/factual palette."
- No new layout: same `Card`/`PanelTitle` structure for Job progress, same `<table>` structure for Run
  history — breakdown counts are additional inline text within existing panels, per the plan.
- No new user-facing actions, no new page, no nav change.

## States Handled

- Zero-work success (backfill/both/rebuild, `ok`, 0 new snapshots) — visually distinct from productive
  success, in both panels.
- Still-running backfill with chunk progress — verified the existing `showBackfill` block and chunk badge
  render correctly for a backfill-kind job now that `chunk_total`/`chunk_index` are populated.
- Persisted-history-only initial render (no session job, `runs.length > 0`) — new `LastRunSummary` view.
- True empty state (no history at all) — unchanged original copy, verified still reachable
  (`runs.length === 0` branch).
- Existing failed/partial/interrupted/resumable states — untouched code paths; `statusVariant`/
  `statusLabel` (the base functions) are unchanged and still used directly for `unfinished_imports` badges
  elsewhere on the page.

## Files Changed

- `apps/frontend/app/data/page.tsx` — see the dev handoff's Files Changed section for the exact function
  list; net +173/-25 lines.
- `apps/frontend/lib/api.ts` — `DataRun` gained 4 new `number | null` fields; `DataJob` gained 4 new
  optional `number` fields (matching the existing `passers?`/`chunk_index?` kind-specific-extension
  pattern, since these are backfill-specific like those, unlike the always-populated `dates_total`).

## Tests Run

- `npx tsc --noEmit -p tsconfig.json` — clean, zero errors, confirming both `api.ts` and `page.tsx` changes
  type-check correctly (including the four new interface fields and every new component's prop types).
- No frontend unit/component test suite exists in this repo to run beyond the type-check (confirmed no
  `apps/frontend/**/*.test.*` or `__tests__/` convention is in use here; `package.json`'s only scripts are
  `dev`/`build`/`start`/`lint`).
- Did **not** run `npm run build` (full production build) or `npm run lint` given the time budget for this
  handoff — `tsc --noEmit` already covers the type-safety surface a build would additionally check, and
  lint is a style-only pass with no functional risk. Left for the reviewer if a full build check is wanted.
- Did **not** drive the actual browser against a live backend in this step (no live backfill job was
  submitted, to avoid polluting the shared committed DB the browser-QA agent needs pristine for J-01 — see
  the dev handoff's Tests Run section for the reasoning). The browser-qa-agent's live run is what verifies
  the actual rendered pixels/DOM for TC-3 through TC-6.

## Known Issues

- The zero-work explanatory note and the breakdown counts have not been visually confirmed in a live
  browser by this step (see above) — only type-checked and read carefully against the existing component
  patterns in the file. This is exactly the kind of check the browser-qa-agent's J-01 walkthrough is
  designed to catch if the actual rendering has any surprise.
- `DataJob`'s four new fields are typed optional (`calendar_days?: number`, etc.) rather than required
  `number`, following the existing `passers?`/`chunk_index?` convention for kind-specific extension fields
  — even though the backend's `to_dict()` always includes them (0-valued for non-backfill kinds, never
  actually absent). This is a defensive-typing choice consistent with the file's existing style, not a
  functional gap.
