# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27
**Date:** 2026-06-17
**Agent:** developer
**Status:** complete

## What Was Built (UI)

### J-86 — paired max-drawdown columns/values everywhere
- **Shared cell helper** (`components/forward-return.tsx`): `fmtMdd` (format a ≤ 0 fraction or em dash),
  `mddClass` (negative → red, 0/NA → muted — MDD is risk, never green), and a `MaxDrawdown` cell. Reused
  across every surface (no second formatter).
- **`/stocks`**: five PAIRED max-drawdown columns (`{h}d MDD`) to the RIGHT of the forward-return
  columns. Sortable under the J-48 view-transform contract (NA-last, re-order only — recomputes/refetches
  nothing). Cells render NA where the return is NA; `data-testid="mdd-{h}"`.
- **`/stocks/[ticker]`** (Stock Detail): each forward-return horizon card now shows its paired "Max
  drawdown" underneath the return; `data-testid="detail-mdd-{h}"`.
- **`/themes`** and **`/sectors`**: five paired MDD columns to the right of the forward returns
  (sortable, NA-honest); the sector value is the ETF's own drawdown, the theme value the equal-weight
  member-basket drawdown — matching Backtest for the same date+horizon. `data-testid="theme-mdd-{h}"` /
  `data-testid="sector-mdd-{h}"`. The expanded-row `colSpan` was widened to cover the new columns.
- **Backtest** (`components/evidence-panels.tsx`): a "Mean MDD" column on the by-bucket and the
  by-setup/by-regime breakdown panels, plus a "Mean max drawdown" figure in the evidence summary header.
- **Research** (`app/research/page.tsx`): a "Mean MDD" column on the event-study per-horizon table and on
  the Regime × Setup × Pattern table (NA + low-sample gated like the other cells).

### J-85 — coverage diagnostic banner + confirm-gated rebuild on `/data`
- **`RebuildPanel`** (`app/data/page.tsx`): an amber diagnostic banner
  (`data-testid="coverage-absent-banner"`) appears ONLY when `coverage.absent_from_latest_snapshot.
  absent_count > 0` ("N universe members absent from the latest snapshot — rebuild to include them", with
  a bounded preview of the absent tickers). When none are absent it shows a calm "all members present"
  note (`data-testid="coverage-absent-none"`) — no alarming banner.
- **Rebuild action** (`data-testid="rebuild-button"`): a confirm-gated "Rebuild snapshots for current
  universe" button. The confirm dialog (`RebuildConfirmModal`, `data-testid="rebuild-confirm-modal"`)
  reuses the J-69 pattern (Card + fixed overlay; the Confirm button stays OUTSIDE the scroll region so it
  is persistently visible). Confirming (`data-testid="rebuild-confirm-button"`) POSTs `kind="rebuild"`
  and surfaces progress through the EXISTING live job card (the same poll path; J-66). The rebuild button
  is disabled while any job is running.
- The `/data` job-form kind dropdown deliberately does NOT include "rebuild" — the rebuild is exclusively
  the dedicated confirm-gated action (a destructive-class operation gets its own gate).

## Design / token compliance
- Palette tokens only: `text-neg` / `text-text-muted` for graded MDD cells (MDD ≤ 0 → negative scale);
  `text-warn` / `border-warn` for the absent-member banner + rebuild action; existing surface/border
  tokens for the modal. No arbitrary hex, no new effects.
- States handled: loading (job in flight → existing J-66 progress card), empty (0 absent → no banner; NA
  MDD at/near latest → em dash, never a fabricated 0), error (start-rebuild failure surfaced in the modal;
  backend-unavailable uses the existing `/data` treatment).
- The MDD columns sit to the RIGHT of the forward-return columns (capture wide/scrolled in QA).

## Files Changed (frontend)
- `apps/frontend/lib/api.ts` — `ForwardReturnEntry.max_drawdown`; `mean_max_drawdown` on group / event-
  study / RSP stat types; `max_drawdown?` on the three leadership-return types;
  `DataCoverage.absent_from_latest_snapshot` + `AbsentFromLatestSnapshot`; `DataJobKind` += `rebuild`.
- `apps/frontend/components/forward-return.tsx` — `fmtMdd` / `mddClass` / `MaxDrawdown`.
- `apps/frontend/app/stocks/page.tsx` — paired MDD columns + sort + cell renderer.
- `apps/frontend/app/stocks/[ticker]/page.tsx` — paired MDD per forward-return card.
- `apps/frontend/app/themes/page.tsx` — paired MDD columns + sort + colSpan.
- `apps/frontend/app/sectors/page.tsx` — paired MDD columns + sort + colSpan.
- `apps/frontend/components/evidence-panels.tsx` — Backtest mean-MDD cells + summary figure.
- `apps/frontend/app/research/page.tsx` — event-study + RSP mean-MDD cells.
- `apps/frontend/app/data/page.tsx` — `RebuildPanel` + `RebuildConfirmModal` + render wiring + import.

## Gate
- `cd apps/frontend && npx tsc --noEmit` → EXIT 0 (ESLint is not installed here — iter-1 lesson).

## Known Issues
- No live browser walkthrough was performed in this dev turn (that is browser-QA's job). The MDD columns
  are to the RIGHT of the forward-return columns and the `/data` rebuild progress is below the fold —
  capture wide/scrolled and view the pixels (iter-3/7/10/13/15/18 evidence-hygiene lesson).
- The absent-member banner only renders when `absent_count > 0`. With the fully-warmed committed seed
  every universe member is present (0 absent), so QA should source-corroborate the banner branch and
  assert the rebuild action + confirm-gated modal exist and POST `kind="rebuild"` (per the spec's J-85
  test note).
