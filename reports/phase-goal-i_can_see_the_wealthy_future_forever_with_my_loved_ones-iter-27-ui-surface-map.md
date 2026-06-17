# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27
**Date:** 2026-06-17
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/stocks` | Leaderboard table — MDD columns (`{h}d MDD`) | New table columns | J-86: paired max-drawdown surfaced beside forward returns | Navigate to `/stocks` at a historical as-of date with post-snapshot seed bars; confirm five MDD columns appear to the right of the forward-return columns; cells show negative percentages or "NA"; click a "5d MDD" column header and confirm NA rows sort to the bottom |
| `/stocks` | MDD cell colour grading | Changed behavior | J-86: MDD grades on negative/red scale | At a historical as-of date, confirm that a MDD value of −15% renders redder than −3%, and that a 0.0% drawdown renders in the muted colour (not green) |
| `/stocks/[ticker]` | Stock Detail — forward-return horizon cards | Updated layout | J-86: each horizon card gains a paired max-drawdown line | Open any stock's detail page at a historical as-of date; verify each of the five horizon cards shows "Max drawdown" beneath the return value; confirm the value is ≤ 0 or "NA" |
| `/themes` | Themes leaderboard table — MDD columns | New table columns | J-86: paired max-drawdown beside forward returns on themes | Navigate to `/themes` at a historical as-of date; confirm five MDD columns appear to the right of the forward-return columns; expand a theme's member row and confirm the colspan covers the new MDD columns |
| `/sectors` | Sectors leaderboard table — MDD columns | New table columns | J-86: paired max-drawdown beside forward returns on sectors | Navigate to `/sectors` at a historical as-of date; confirm five MDD columns appear to the right of the forward-return columns; sort by "20d MDD" header and confirm NA rows land last |
| `/backtest` | Evidence panels — by-bucket, by-setup, by-regime breakdown tables | Updated layout | J-86: aggregate mean-MDD beside return stats | Open the Backtest page, run a backtest that produces results, expand a breakdown panel (e.g. by-bucket); confirm a "Mean MDD" column appears beside the return/MAE columns and shows negative percentages or "NA" for low-sample rows |
| `/backtest` | Evidence summary header | Updated layout | J-86: mean max drawdown figure in summary header | On the Backtest evidence summary panel, confirm a "Mean max drawdown" figure is present; verify it shows a negative percentage (or "NA") and not a fabricated positive value |
| `/research` | Event-study per-horizon table — Mean MDD column | Updated layout | J-86: aggregate mean-MDD beside return stats on event study | Open the Research page, run an event study, and confirm a "Mean MDD" column appears in the per-horizon table beside the return stats; verify that horizons with fewer observations than the minimum-sample threshold display "NA" |
| `/research` | Regime × Setup × Pattern table — Mean MDD column | Updated layout | J-86: aggregate mean-MDD beside return stats on RSP table | On the Research RSP table, confirm a "Mean MDD" column is present; click a cell to inspect its value and confirm it is ≤ 0 or "NA", never a positive number |
| `/data` | `RebuildPanel` — coverage diagnostic banner | New component | J-85: absent-member count served, banner only when N > 0 | On `/data`, when no members are absent confirm the banner is NOT shown and a calm "all members present" note (`data-testid="coverage-absent-none"`) appears instead; to test the banner branch, source-corroborate the `coverage.absent_from_latest_snapshot.absent_count` field in the API response and confirm the component conditionally renders `data-testid="coverage-absent-banner"` with the correct count |
| `/data` | `RebuildPanel` — "Rebuild snapshots for current universe" button | New component | J-85: operator-triggered confirm-gated snapshot rebuild | On `/data`, confirm the rebuild button (`data-testid="rebuild-button"`) is present and enabled when no job is in flight; click it and confirm the confirm modal appears (`data-testid="rebuild-confirm-modal"`) with the Confirm button visible without scrolling; dismiss (cancel) and confirm no job is started |
| `/data` | `RebuildConfirmModal` — confirm dialog | New modal | J-85: destructive rebuild requires explicit operator confirmation | Click "Rebuild snapshots" then click the Confirm button (`data-testid="rebuild-confirm-button"`); confirm a job appears in the existing live job card and starts progressing; confirm the rebuild button becomes disabled while the job is running |
| `/data` | Rebuild job progress via existing job card | Changed behavior | J-85: rebuild kind surfaces progress through existing J-66 card | After confirming a rebuild, confirm the existing live job card shows progress counters (processed / total) that never exceed the total; confirm the run-history entry for the rebuild job appears in the run-history section after completion |
| `components/forward-return.tsx` | `MaxDrawdown` cell helper (`fmtMdd` / `mddClass`) | New component | J-86: shared MDD formatter reused across all leaderboard surfaces | On `/stocks` at a historical as-of date with a completed forward-return window, confirm the MDD value is formatted as a negative percentage (e.g. "−8.3%"), never as a raw decimal, and that "NA" appears for incomplete windows |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/models.py` (`ForwardReturn.max_drawdown` column) — schema change; the value is served via API and consumed by the frontend leaderboard and detail surfaces (UI impact is via the API layer above).
- `apps/backend/app/db.py` (`_ADDITIVE_COLUMNS` registration) — auto-migration DDL entry; runs on backend boot; no user-visible surface of its own.
- `apps/backend/app/engine/forward_testing.py` (`max_drawdown` computation helper, `_insert_run_forward_returns` population) — pure backend computation; values are stored and later served verbatim; no independent UI surface.
- `apps/backend/tests/test_forward_testing.py`, `tests/test_iter27_rebuild_mdd.py`, `tests/test_api_engine.py`, `tests/test_db.py` — test files; no UI impact.

---

## Summary

- **Frontend surfaces changed:** 10 (7 pages/routes + 3 shared components)
- **New pages/routes:** 0 (all changes land on existing pages)
- **Modified components:** 10
- **Navigation changes:** no
- **Backend-only changes:** 4 (model, db migration, computation helper, tests)
