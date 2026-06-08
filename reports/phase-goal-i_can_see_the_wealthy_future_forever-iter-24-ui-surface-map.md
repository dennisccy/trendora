# Phase goal-i_can_see_the_wealthy_future_forever-iter-24 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-24
**Date:** 2026-06-08
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|---------------------|-------------|-------------|--------------|
| `/data` | `CoveragePanel` — `DefinedMetric` blocks | Updated layout | Each aggregate figure now carries a one-line plain-language definition (J-36) | Navigate to `/data`, confirm the "Universe" figure shows a number AND a definition sentence directly below it (e.g. "The config-screened, SCORED names…") |
| `/data` | `CoveragePanel` — universe-vs-symbols prose line | New component | J-36 requires the universe/symbols distinction surfaced in plain language | Scroll to the bottom of the Dataset coverage card and confirm a sentence appears distinguishing the universe count from the symbols count by name (not just numbers) |
| `/data` | `PerSymbolCoverageTable` — scrollable table | New component | J-36 per-symbol / per-universe-member coverage table | After page loads, confirm the table shows rows with Symbol, In universe, Has data, Date range, Bars, and Flag columns; confirm a universe member row shows the "universe" badge in the "In universe" column |
| `/data` | `PerSymbolCoverageTable` — symbol search input | New component | J-36 UI-only filter | Type "AAPL" in the "Filter symbol…" input and confirm only rows whose symbol contains "AAPL" remain visible in the table |
| `/data` | `PerSymbolCoverageTable` — "Universe members only" toggle (`data-testid="universe-members-only-toggle"`) | New component | J-36 filter to confirm every scored name is data-or-flagged | Click the "Universe members only" toggle, confirm only in-universe rows remain, and confirm every row either has "yes" in Has data or shows a "missing" or "thin" badge in the Flag column |
| `/data` | `PerSymbolCoverageTable` — Symbol column sort header | New component | J-36 UI-only sort | Click the "Symbol" column header twice; confirm rows first sort A→Z then Z→A |
| `/data` | `PerSymbolCoverageTable` — Bars column sort header | New component | J-36 UI-only sort | Click the "Bars" column header; confirm rows reorder so the symbol with the highest bar count appears first |
| `/data` | `PerSymbolCoverageTable` — "thin" badge rows | New component | J-36 honest thin/missing display | If any row shows a "thin" badge, confirm its date range is non-null and its bar count is a positive number below the threshold; confirm the row background is visually distinct (amber/muted) |
| `/data` | `PerSymbolCoverageTable` — "missing" badge rows | New component | J-36 honest missing display — universe member with no data | If any row shows a "missing" badge, confirm its Has data column shows "no" and its Date range column shows "NA" (not a fabricated date) |
| `/data` | `RemoveDataPanel` (`data-testid="remove-data"`) | New component | J-39 seed-safe Remove-data control | Scroll to the "Remove imported data" panel and confirm it is present with a symbols text field, "From date" and "To date" date inputs, and a "Preview removal" button with a red-border destructive style |
| `/data` | `RemoveDataPanel` — "Preview removal" button (`data-testid="remove-preview-button"`) | New component | J-39 opens the confirm-preview modal | Leave all three scope inputs empty, confirm the "Preview removal" button is disabled; enter a symbol (e.g. "NVDA") and confirm the button becomes enabled |
| `/data` | `RemoveConfirmModal` (`data-testid="remove-confirm-modal"`) | New modal | J-39 confirm-preview enumerates what would be deleted before any deletion | Enter "NVDA" in the symbols field, click "Preview removal", confirm the modal opens and shows a "Will be removed (user-added)" section with a bar count and date range |
| `/data` | `RemoveConfirmModal` — not-removable committed-seed block (`data-testid="remove-not-removable"`) | New modal section | J-39 committed-seed bars must be shown as protected | After the preview modal opens for any symbol, confirm a "Not removable — committed seed (protected)" section appears listing the per-symbol bar count and the reason "committed seed" |
| `/data` | `RemoveConfirmModal` — cascade block (`data-testid="remove-cascade"`) | New modal section | J-39 dependent snapshots and forward returns are shown before deletion | In the preview modal, confirm a "Cascade — dependent rows removed with the bars" section shows a snapshot count and forward returns count |
| `/data` | `RemoveConfirmModal` — refused state (`data-testid="remove-refused"`) | New modal section | J-39 wholly-seed scope must be refused with explicit reason | For a scope that covers only committed-seed bars (or use a symbol whose only bars are in the seed), confirm the modal shows an amber refusal message with the text "committed seed" and the "Remove N bars" button is disabled |
| `/data` | `RemoveConfirmModal` — Cancel button | New modal action | J-39 operator must be able to dismiss without deleting | Click "Preview removal", then click "Cancel" in the modal; confirm the modal closes and no data changes occur (the coverage table numbers remain the same) |
| `/data` | `RemoveConfirmModal` — "Remove N bars" confirm button (`data-testid="remove-confirm-button"`) | New modal action | J-39 destructive confirm triggers the removal | In a fixture environment with user-added bars: confirm the removal, then confirm the green `data-testid="remove-done"` success notice appears showing the removed bar count and cascade counts |
| `/data` | `RemoveDataPanel` — post-removal success notice (`data-testid="remove-done"`) | New component | J-39 operator feedback after a successful removal | After confirming a removal, confirm a green notice appears stating how many bars, snapshots, and forward returns were removed, and confirm the per-symbol table no longer shows the removed bars' date range for that symbol |
| `/data` | Global as-of switcher refresh after removal | Changed behavior | J-39 removed dates must drop out of the date selector | After confirming a removal that eliminates all snapshots for certain dates, confirm those dates no longer appear in the global as-of switcher in the top navigation |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/data_manager.py` — `load_seed_windows`, `is_seed_bar`, `_classify_scope`, `_cascade_targets`, `_build_removal_plan`, `_record_removal_run` — internal seed classifier and cascade logic; no direct UI rendering, but consumed by the preview and removal endpoints which the frontend calls.
- `apps/backend/tests/test_data_manager.py` — J-36 and J-39 unit/integration tests covering exact per-symbol values, seed classifier, preview-deletes-nothing, cascade-solely, and no-recompute assertions — test files only, no UI surface.
- `apps/backend/tests/test_api_data.py` — endpoint shape, 4xx error cases, and key-safety tests — test files only, no UI surface.

---

## Summary

- **Frontend surfaces changed:** 1 page (`/data`)
- **New pages/routes:** 0
- **Modified components:** 1 (`CoveragePanel` — richer definitions + per-symbol table)
- **New components on the page:** `PerSymbolCoverageTable`, `RemoveDataPanel`, `RemoveConfirmModal`, `DefinedMetric` blocks
- **Navigation changes:** no
- **Backend-only changes:** 2 test files, multiple internal engine functions (all consumed by endpoints the frontend already calls)
