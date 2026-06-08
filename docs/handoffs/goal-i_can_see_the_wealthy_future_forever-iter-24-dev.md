# goal-i_can_see_the_wealthy_future_forever-iter-24 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-24
**Date:** 2026-06-08
**Agent:** developer
**Status:** complete

## What Was Built

This iteration completes two fully-deterministic Data-Manager Must-haves on the existing `/data` page
(no new route, no nav entry) plus sets up the J-35 expand-flow browser capture.

- **J-36 — per-symbol coverage + plain-language definitions (read-only, descriptive).**
  `app.engine.data_manager.compute_coverage` now also returns a `per_symbol` table: one row per stored
  `DailyPrice.symbol` AND one row per `config.universe.symbols` member, each carrying `symbol`,
  `in_universe`, `has_data`, `first`/`last` (NA/`null` when no bars — never fabricated), `bar_count`,
  `thin` (`0 < bar_count < indicators.min_history_bars`, threshold from config — no magic number), and
  `missing` (a universe member with no bars). Internal consistency holds by construction: distinct
  has-data rows == `symbol_count`, in-universe rows == `universe_count` (single canonical universe source).
  No score/return/bucket recomputed.

- **J-39 — seed-safe Remove-data with confirm-preview + consistency-preserving cascade.** The session's
  first destructive data path. Added: a seed-vs-user-added classifier reading `apps/backend/data/seed/meta.json`
  windows (`load_seed_windows` / `is_seed_bar`); a read-only `preview_removal` (`POST /api/data/remove/preview`)
  that enumerates exactly what would be removed (removable user-added bars + range + symbols, the
  not-removable committed-seed breakdown with reason `"committed seed"`, and the dependent
  snapshot/forward-return cascade) and deletes nothing; a destructive `remove_data`
  (`POST /api/data/remove`) that whole-row-deletes only user-added `DailyPrice` rows and cascade-removes
  only the `ScannerRun`/`ScannerResult`/`SectorScoreRow`/`ThemeScoreRow`/`ForwardReturn` rows derived
  SOLELY from them (a fully-covered snapshot is left untouched — never overwritten in place), records the
  removal on the append-only `DataProviderRun` audit log, and refuses a wholly-committed-seed scope with an
  explicit reason. Empty/inverted/unknown scope → 400. No scoring/scanner recompute is reachable from the
  remove path.

- **Frontend `/data`:** a richer Coverage panel (each aggregate figure beside its plain-language
  definition + a universe-vs-symbols prose line + backfill-gap definition), a sortable/filterable
  per-symbol coverage table (UI-only sort/filter, universe-members-only toggle, thin/missing amber/muted
  treatment), and a Remove-data control with an in-page confirm-preview modal (built from `Card` + overlay —
  there is no Dialog primitive in this project). Re-reads coverage + refreshes the as-of switcher after a
  successful removal.

- **J-35 prep:** verified the expand-screen-result block (`expand-screen-result`, `expand-passers`,
  `expand-omitted-count`, `expand-omitted-list`) renders from the existing machinery; no code change was
  needed for the capture. Browser capture is the browser-qa-agent's step.

## Files Changed

- `apps/backend/app/engine/data_manager.py` -- added `_per_symbol_coverage` (J-36 table) wired into
  `compute_coverage`; added the J-39 seed classifier (`load_seed_windows`, `is_seed_bar`), scope
  validation, `_classify_scope`, `_cascade_targets` (the "derives solely" predicate), `_build_removal_plan`,
  `preview_removal`, `remove_data`, and `_record_removal_run` (append-only audit insert).
- `apps/backend/app/api/data.py` -- added `RemoveScope` request model and the `POST /api/data/remove/preview`
  (read-only) + `POST /api/data/remove` (destructive) endpoints; `ValueError` → 400.
- `apps/frontend/lib/api.ts` -- `PerSymbolCoverage` type added to `DataCoverage`; `RemoveScope`,
  `RemoveSeedLine`, `RemoveCascade`, `RemovePreview` types; `previewDataRemoval` + `executeDataRemoval` clients.
- `apps/frontend/app/data/page.tsx` -- `CoveragePanel` definitions block, `PerSymbolCoverageTable`,
  `RemoveDataPanel` + `RemoveConfirmModal`; re-read coverage after removal.
- `apps/backend/tests/test_data_manager.py` -- J-36 per-symbol exact-value + consistency + thin-threshold +
  empty-dataset tests; J-39 seed classifier + preview-deletes-nothing + cascade-solely + fully-covered-
  snapshot-untouched + seed-only-refused + audit-recorded + no-recompute + error-case tests.
- `apps/backend/tests/test_api_data.py` -- preview/removal endpoint shape + 4xx cases + key-safety tests.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py tests/test_api_data.py -q`
Result: **73 passed** in ~70s.

Frontend typecheck: `cd apps/frontend && npx tsc --noEmit` → exit 0 (clean).

Note: the full backend suite (~14 min) was NOT re-run here per the iteration note (run once at the QA gate;
no DB regen, scoring/scanner/snapshot paths untouched, so J-06/J-07 stay byte-identical). The two affected
test files plus a live API smoke covered the changed surface.

## Live Verification (real host, committed-seed + existing user-added NVDA bars)

Both services started cleanly by port (frontend :3835, backend :8835; `.next` cleared first):
- `GET /api/data` — `universe_count`=122, `symbol_count`=162, `per_symbol`=162 rows; in-universe rows (122)
  == universe_count and with-data rows (162) == symbol_count (J-36 consistency invariant holds live).
- `POST /api/data/remove/preview {"symbols":["NVDA"]}` — removable=6 user-added bars (2026-05-29..06-05),
  not-removable=1356 committed-seed bars (reason "committed seed"), cascade=14 snapshots / 5384 forward
  returns; deleted nothing (preview-only on the live host per the destructive-path safety rule).
- Seed-only scope → `refused=true` with the "committed seed" reason; empty scope → 400.
- Frontend `/data` → 200 and `/_next/static/chunks/main-app.js` → 200 (hydrated, no dead-shell).

Servers were stopped by port afterward (including the lingering `next dev` child) — all ports clear.

## Known Issues

- The destructive removal was NOT executed against the live host (it has real user-added NVDA bars and
  `trendora.db` is gitignored with no restore — per MEMORY `j39-live-host-has-user-added-nvda-bars`).
  Destructive-path correctness is proven by the unit/integration fixture that adds user bars beyond the
  seed (`test_remove_data_cascade_solely_dependent`, etc.). The live smoke uses the preview path only.
- J-35's defining end-to-end browser capture (injected-provider expand → passers + omitted-with-reason →
  grown universe-count) is the browser-qa-agent's step; the machinery is integration-proven and the result
  block renders. No code change was required.
- J-37 and J-38 are explicitly out of scope (deferred to iter-25) — not built. GOAL_ACHIEVED is not
  reachable this iter.
