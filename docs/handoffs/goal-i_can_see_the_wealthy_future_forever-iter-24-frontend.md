# goal-i_can_see_the_wealthy_future_forever-iter-24 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-24
**Date:** 2026-06-08
**Agent:** developer
**Status:** complete

## What Was Built

All additive on the existing `/data` (Data Manager) page — no new route, no nav entry, no second date state.

- **Coverage definitions block (J-36).** Each aggregate figure (`Price history`, `Universe`, `Symbols`,
  `Trading days`, `Snapshot dates`, `Backfill gaps`) is shown beside a one-line plain-language definition,
  plus a universe-vs-symbols prose line (universe = config-screened scored names; symbols = every ticker
  with bars, incl. ETFs + `^VIX`) and a backfill-gap definition. Re-formats backend values only.
- **Per-symbol coverage table (J-36).** One row per stored symbol AND per universe member, with columns:
  in-universe / has-data / date range / bar count / thin-or-missing flag. UI-only sort (symbol, bar count)
  and filter (symbol search + "Universe members only" toggle). Thin/missing rows get an amber/muted
  treatment. Header line shows in-universe row count (= universe_count) and with-data row count (= symbol_count).
- **Remove-data control + confirm-preview modal (J-39).** Scope inputs (symbols and/or date range — action
  parameters, `type="date"`, NOT a viewing-date control). "Preview removal" opens an in-page modal
  (`Card` + fixed overlay; no Dialog primitive in this project) enumerating: removable user-added bars
  (count + range + symbols), the not-removable committed-seed breakdown (per symbol, reason "committed
  seed"), and the dependent cascade (snapshots + forward returns). A wholly-seed scope shows the refusal
  and disables the destructive confirm. Confirm calls the destructive endpoint, then re-reads coverage +
  refreshes the global as-of switcher (removed-only dates drop out).

## Files Changed

- `apps/frontend/lib/api.ts` -- `PerSymbolCoverage` (added to `DataCoverage`), `RemoveScope`,
  `RemoveSeedLine`, `RemoveCascade`, `RemovePreview` types; `previewDataRemoval`, `executeDataRemoval`.
- `apps/frontend/app/data/page.tsx` -- `CoveragePanel` (definitions block), `PerSymbolCoverageTable`,
  `RemoveDataPanel`, `RemoveConfirmModal`.

## Design System Conformance

- Reused the existing `/data` primitives: `Card`, `Badge`, `PanelTitle`, `Metric`/`DefinedMetric`, the
  `num` tabular class, `border-neg`/`text-neg` destructive affordance, `warn` amber for thin/missing.
- Raw semantic `<table>` over a `Card` (the established `/data` pattern — there is no shadcn `Table`/`Dialog`
  primitive). Interactive elements carry hover/focus/active states. Loading (spinner), error (alert), and
  empty (members-only rows / NA range) states handled.

## Test IDs (for browser-qa-agent)

- Coverage: `universe-count`, `universe-count-defined`, `per-symbol-coverage`, `table-in-universe-count`,
  `table-with-data-count`, `coverage-row`, `universe-members-only-toggle`.
- Remove: `remove-data`, `remove-preview-button`, `remove-confirm-modal`, `remove-removable`,
  `remove-not-removable`, `remove-cascade`, `remove-refused`, `remove-confirm-button`, `remove-done`.
- Expand (J-35): `expand-screen-result`, `expand-passers`, `expand-omitted-count`, `expand-omitted-list`,
  `chunk-progress`.

## J-18 Preservation

`data/page.tsx` contains **zero** `<select>` elements. The global as-of switcher lives in
`components/asof-switcher.tsx` (mounted via the layout). The 4 `type="date"` inputs on `/data` (fetch/backfill
range + removal range) are action parameters — they add no viewing-date state.

## Verification

`npx tsc --noEmit` → exit 0. `/data` served HTTP 200 with `main-app.js` chunk 200 (hydrated, no dead-shell).

## Known Limitations

- Destructive removal not exercised in the browser on the live host (seed + real user-added NVDA bars,
  no DB restore); the browser-qa-agent should preview-only on the live host and prove the destructive
  confirm against a user-added-bar fixture host.
