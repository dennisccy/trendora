# goal-i_can_see_the_wealthy_future_forever-iter-2 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-2
**Date:** 2026-06-01
**Agent:** developer
**Status:** complete

## What Was Built

- A single **shared** `ReturnAttributionSection` component (`components/return-attribution.tsx`)
  rendering the four read-only attribution panels (J-19), consumed by BOTH `/system-health` and
  `/backtest` so the contract value has ONE UI home (coherence: no duplicate home):
  - **Top contributors & detractors** — a two-column panel naming the individual tickers (with sector,
    realized mean return, and `n`) that most drove or dragged the cohort.
  - **Distribution & hit-rate** — a stat panel: mean, median, % positive (hit rate), dispersion (σ),
    and `n`.
  - **Forward return by sector** — mean realized return + `n` per stored sector.
  - **Forward return by rank band** — mean realized return + `n` per config rank band (1–10 / 11–50 /
    51+); every band always shown (padded to NA when empty).
- `/system-health`: the section is appended below the existing control-group panel and rides the page's
  existing horizon selector (no new control there).
- `/backtest`: the section is appended below the scorecard, with a NEW client-side **horizon view
  selector** (`HorizonViewSelector`) that picks which already-fetched `by_horizon[*].attribution` to
  display. It triggers NO refetch, takes NO fetch param, and keys NO date effect — the page still holds
  **no independent date state** and reads only the global `useAsOf()` switcher (preserves J-18).

## Files Changed

- `apps/frontend/lib/api.ts` — added `PerStockRow`, `PerStockAttribution`, `BySectorRow`,
  `ByRankBandRow`, `Distribution`, `ReturnAttribution`; added `attribution: ReturnAttribution` to
  `SystemHealthResponse` and to `BacktestScorecardHorizonRow`. No fetcher signature changed.
- `apps/frontend/components/return-attribution.tsx` — **new** shared four-panel section, reusing the
  existing `Return` / `fmtPct` / `returnClass` / `SampleSize` primitives and palette tokens only.
- `apps/frontend/app/system-health/page.tsx` — import + render `<ReturnAttributionSection>` below the
  control-group panel (rides the existing horizon state).
- `apps/frontend/app/backtest/page.tsx` — import + new `HorizonViewSelector` and
  `BacktestAttributionSection` (client-side horizon view, no refetch); rendered below the scorecard.

## Design System Compliance

- shadcn `Card` for every panel; numbers use the `num` (tabular-nums monospace) class.
- Colour only from palette tokens: `--pos` / `--neg` via `returnClass` for directional mean/median,
  `--warn` for the low-sample `⚠` flag, `--text` / `--text-muted` / `--text-faint`, `--border`,
  `--surface-2`, `--accent` (active selector). No arbitrary hex, no new effects.
- Hit-rate and dispersion are unsigned magnitudes (not directional returns), shown neutral — no +/-
  sign, no green/red grade.
- States handled: empty per-stock list ("No ticker had a measurable forward return…"), `n=0` slice → NA
  em dash, `n < min_sample` → existing `⚠`, no-elapsed-window → NA per panel. Nothing fabricated.
- The horizon view selector matches the System Health `HorizonSelector` segmented-button style, with
  hover / focus-visible / aria-pressed states.

## Tests Run

Command: `cd apps/frontend && npm run build`
Result: ✓ Compiled successfully; types valid; all 12 routes generated (incl. `/system-health` 2.86 kB,
`/backtest` 4.4 kB). No type or build errors.

## Known Issues

- On `/backtest` the distribution mean is over the full observed set at the selected horizon, so it
  need not equal the scorecard's top-ranked cohort mean shown above it (documented for QA — not a bug).
- UI behaviour is verified by the production build (compile + typecheck); user-flow validation is left
  to browser QA (J-19 primary + J-09/J-10/J-13/J-14/J-18/J-01 regression).
