# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20
**Date:** 2026-06-15
**Agent:** developer
**Status:** complete

## What Was Built (UI)

- **`/stocks` — five forward-return columns (J-75):** the leaderboard table gains five columns
  (1d/5d/10d/20d/60d, derived from the served rows' `forward_returns` — config-driven, no hardcoded
  horizons). Each cell is colour-graded by sign via the shared `forward-return.tsx` helpers
  (`fmtPct`/`returnClass`); NA where no stored row ("NA", muted). Columns are client-side sortable under the
  J-48 view-transform contract (`comparatorFor` adds `fwd_<horizon>` keys; a null/NA return always sorts
  LAST; default order stays the stored rank; forward-return columns lead descending = best-first). No
  refetch/recompute — a pure re-order of the already-served rows.

- **`/stocks/[ticker]` — Realized forward returns panel (J-75):** a new card above the price chart showing
  the SAME five returns for the resolved as-of date (one tile per config horizon), colour-graded, NA honest.
  Read verbatim from the served row (identical to the leaderboard cell — J-06).

- **`/research` — Regime × Setup × Pattern study section (J-77):** a new section below the existing labs
  with its OWN independent fetch + loading/skeleton state (per-section loading — no single slow query blocks
  the page, J-15/J-72). A ranked, client-side-sortable dense table (`regime-setup-pattern-table`): one row
  per (regime, setup, pattern) combination with n, mean, median, hit-rate, expectancy, and both downside
  risk-adjusted figures. Default order = the served risk-adjusted rank (sort is a view transform; NA-last).
  Its own Episodes ⇄ Pooled toggle (reuses `EventStudyViewToggle`, J-63); reuses the page's shared horizon
  selector + analysis-mode toggle (J-18/J-32 — no second date control). Each row's `N=` chip opens
  `/research/samples` for that exact combination in a NEW tab (J-65), with `?asof` href-stamped while
  historical (J-50) — both via the shared `SampleLink` + `useAsOfHref`. The survivorship-bias caveat banner
  persists; low-sample/empty cells render NA + n. The pattern dimension uses a `— (none)` label for the
  no-pattern-flagged sentinel.

- **`/research/samples` — drill-down header for the new cohort (J-77):** `describeCohort` gains a
  `regime-setup-pattern` branch rendering the combination + the Episodes/Pooled view in the page heading.
  The samples table renders the new cohort's value columns (Regime / Setup / Pattern) generically from the
  served rows; the count-coherence "total" and the J-64 sort/filter are unchanged.

## Files Changed

- `apps/frontend/lib/api.ts` — `StockForwardReturn` + `StockRow.forward_returns`; `RegimeSetupPatternStats`/`Row`/`Response` + `fetchRegimeSetupPattern`; `SampleCohort` new kind + `setup`/`pattern` fields.
- `apps/frontend/lib/samples-link.ts` — `RegimeSetupPatternCohortParams` + its `buildSamplesHref` serialization (regime/setup/pattern/view).
- `apps/frontend/app/research/page.tsx` — the new `RegimeSetupPatternLab` (fetch + loading + sortable table + view toggle + N= chips) rendered after `EventStudyLab`.
- `apps/frontend/app/stocks/page.tsx` — `fwd_<horizon>` sort keys + `comparatorFor`; five sortable headers (server-driven horizons) + `ForwardReturnCell` cells.
- `apps/frontend/app/stocks/[ticker]/page.tsx` — `ForwardReturnPanel` rendered above the chart.
- `apps/frontend/app/research/samples/page.tsx` — `describeCohort` branch for `regime-setup-pattern`.

## Design / Contract Adherence

- Dense dark analytical tables; monospace/tabular numerics; colour-graded return cells from the existing
  palette tokens (`text-pos`/`text-neg`/`text-text-muted`) via `forward-return.tsx` — no new effects, no
  arbitrary colours.
- All UI elements use the existing component library (`Card`, `Badge`, `Select`, `TermInfo`, `SampleLink`,
  `EmptyState`). Loading (skeleton), empty/NA (honest cells), and error (styled "Backend unavailable" card)
  states all handled. Sort headers are accessible buttons with hover/focus states and direction arrows; the
  glossary `TermInfo` sits OUTSIDE the sort button (no nested interactive element — iter-5/6 lesson).
- New surfaces land on EXISTING IA homes (`/research`, `/stocks`, `/stocks/[ticker]`, the reused
  `/research/samples`) — no new page, no new top-level nav, no `blueprint.reapproval-requested`.

## Tests Run

- `cd apps/frontend && npx tsc --noEmit` — clean (exit 0). ESLint not installed (iter-1 lesson).
- Live pages (frontend on :3835, backend on :8835): `/research` 200, `/stocks` 200, `/stocks/AAPL` 200 — no
  errors in the dev server log. Deep browser verification (sort re-orders, view toggle re-points, N= chip
  opens the new-tab drill-down with total == row n, five columns at a historical as-of) is for browser QA.

## Known Issues / Notes

- The `/research` page's FIRST (FactorLab) section still shares the page-level loading state; the
  Combination, Event-study, and the new Regime × Setup × Pattern sections each fetch independently with
  their own loading state (per-section loading discipline preserved + extended).
- Frontend served by `next dev` (not a prod `next build`) so the `.next` cache is the dev cache (avoids the
  dead-shell trap from a prod build clobbering the dev cache — browser-qa-dead-shell lesson).
