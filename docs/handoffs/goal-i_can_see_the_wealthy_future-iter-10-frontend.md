# goal-i_can_see_the_wealthy_future-iter-10 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-10
**Date:** 2026-05-31
**Agent:** developer
**Status:** complete

## What Was Built

- **`/backtest` page** — the Backtest / Time-Machine workspace (J-14). A dedicated, client-rendered page
  with its OWN as-of date picker (independent of the global top-bar switcher), driving two sections:
  - **As-of scan summary** — market regime (label + 0–100 score), candidate counts, top sectors, top
    themes, and the ranked stock cohort (top 10). All fetched from the EXISTING canonical clients
    (`fetchDashboard` / `fetchSectors` / `fetchThemes` / `fetchStocks`) with `?as_of=D` — no new source
    or client-side recomputation (single source → byte-identical to the other pages for that date).
  - **Forward-test scorecard** — a dense, monospace, horizontally-scrollable table from `fetchBacktest(D)`:
    rows = 1/5/10/20/60-day horizons; columns = cohort mean return, excess vs SPY / QQQ / sector, the
    random-same-sector control, and the SPY / QQQ / sector-ETF control cohorts — each cell showing its
    sample size `n`. NA renders as "—" with `n=0`; `n < min_sample` is flagged with the `--warn` ⚠ token.
- **Sidebar entry** — a new top-level **Backtest** nav item (`FlaskConical` icon) placed after *Scanner
  Runs* and before *System Health*, matching the approved blueprint Information Architecture.
- **Shared forward-return helpers** — `components/forward-return.tsx` exports the `fmtPct` / `returnClass`
  / `SampleSize` / `Return` helpers (lifted verbatim from `system-health/page.tsx`). Both System Health and
  the Backtest scorecard now import them, so realized-return formatting has one source.
- **API client** — `fetchBacktest(asof, signal)` + the `ScorecardExcess` / `BacktestScorecardHorizonRow` /
  `BacktestScorecard` / `BacktestResponse` types (mirroring the existing `ForwardGroupRow` /
  `ControlGroupRow` / `SystemHealthResponse` shapes; `mean_return`/`mean_excess` are `number | null`,
  every figure carries `n`).

## Files Changed

- `apps/frontend/app/backtest/page.tsx` — **created**: the Backtest workspace (date picker + scan summary +
  scorecard; loading / empty / error / NA states).
- `apps/frontend/components/forward-return.tsx` — **created**: shared `fmtPct`/`returnClass`/`SampleSize`/
  `Return` display helpers (single source for realized-return formatting).
- `apps/frontend/app/system-health/page.tsx` — **modified**: imports the shared helpers; its four local
  copies were removed (no behaviour change).
- `apps/frontend/components/sidebar.tsx` — **modified**: added the `/backtest` "Backtest" nav entry
  (`FlaskConical`) after Scanner Runs / before System Health.
- `apps/frontend/lib/api.ts` — **modified**: added `fetchBacktest` + the four Backtest types.

## States Handled

- **Loading** — skeleton cards + a skeleton scorecard.
- **Empty / all-NA** — the latest (or any zero-post-bar) date renders an explanatory `EmptyState` plus an
  all-"—" scorecard (n=0) — never a fabricated number.
- **Error / "Backend unavailable"** — a styled `border-neg` alert; the scan-summary endpoints are
  best-effort and degrade individually without blanking the scorecard.
- **Historical vs latest** — a "Viewing as-of D (historical|latest)" badge (amber `--warn` for historical).

## Design System Conformance

- Dark analytical-workstation tokens only (`--bg`/`--surface`/`--border`/`--pos`/`--neg`/`--warn`/`--text*`).
- `shadcn/ui` `Card` / `Badge` / `Select` components; `ScoreBadge` + `bucketVariant` for buckets;
  monospace `num` (tabular-nums) for all numbers; green/red return grading via `returnClass`.
- Date picker mirrors the existing `asof-switcher` styling; survivorship banner mirrors System Health's.

## Tests Run

Command: `cd apps/frontend && npm run build`
Result: ✓ Compiled successfully; types valid; all 11 routes generated (incl. `/backtest`, 6.13 kB).

## Known Issues

- Two date controls are visible on `/backtest` (the page's own picker + the global top-bar switcher). This
  is by design — the spec requires the page to have its own picker independent of the global switcher; the
  global switcher does not drive this page.
- Live browser verification depends on the runner starting backend (with `CORS_ORIGINS` = frontend origin)
  and frontend (with `NEXT_PUBLIC_API_URL` = backend port); `await_text` should target a scorecard cell
  value (an `n=` or a `%`), never a heading or the date-picker placeholder.
