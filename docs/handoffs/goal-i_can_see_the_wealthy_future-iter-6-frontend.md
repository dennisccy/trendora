# goal-i_can_see_the_wealthy_future-iter-6 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-6
**Date:** 2026-05-30
**Agent:** developer
**Status:** complete

## What Was Built

`/system-health` graduates from its iter-1 EmptyState stub to a populated, multi-panel **forward-tested evidence dashboard** (J-09, J-10), in the established dense-dark workstation style. It reads the single `GET /api/system-health` payload and **re-formats only** — it never recomputes a return, excess, or bucket.

### UI surfaces (all on `/system-health`)
- **Horizon selector** — a segmented button group (1d / 5d / 10d / 20d / 60d), default 20, whose options come from the payload's `horizons` (not hard-coded). Selecting a horizon re-fetches `GET /api/system-health?horizon=…` and updates every panel.
- **Survivorship-bias banner** — prominent, warn-toned, near the top; renders the server's `survivorship_bias` sentence verbatim.
- **Forward return by score bucket** — A–E table (colour-graded bucket badge via the shared `bucketVariant`), mean return + `n` per bucket (J-09).
- **Excess vs benchmarks** — Excess vs SPY and Excess vs QQQ, each showing the stock mean, the benchmark mean, and the excess + `n` (J-09).
- **By setup type** and **By market regime** breakdowns — each a table of mean return + `n` (J-09); both Risk-on and Risk-off rows appear.
- **Control-group comparison** panel (J-10) — top-ranked cohort (highlighted) vs random same-sector peers vs SPY / QQQ / sector-ETF, each numeric + labelled + `n`.
- **A summary strip** — snapshots contributing, as-of date range, overall mean forward return, and a legend that `n < min_sample ⚠` is low-sample.

### States handled
- **Loading** — skeleton panel grid.
- **Backend unavailable** — styled red alert (matches `/scanner-runs`/`/stocks`); no fabricated figures.
- **No evidence / low sample** — when `n_runs === 0` or the overall sample is empty (e.g. a horizon with no realized data yet), an explicit EmptyState rather than zeros; individual low-sample figures (`n < min_sample`) are flagged with the warn token, never hidden.

### Design-system compliance
- Shared `Card`, `PageHeading`, `Badge`, `bucketVariant`/`ScoreBadge` colours, `EmptyState`.
- ALL numbers use the `.num` (tabular-nums) class; positive returns use `--pos`, negative `--neg`, low-sample `--warn`. Palette tokens only — no arbitrary hex.
- Interactive horizon buttons have hover / focus-visible / active (`aria-pressed`) states.
- Sidebar unchanged (System Health link already present); no navigation change.

## Files Changed
- `apps/frontend/app/system-health/page.tsx` — the evidence dashboard (replaces the stub).
- `apps/frontend/lib/api.ts` — `SystemHealthResponse` (+ `ForwardBucketRow` / `ForwardSetupRow` / `ForwardRegimeRow` / `ExcessVsBenchmark` / `ControlGroupRow`) types and `fetchSystemHealth(horizon, signal)` (throws on non-200 → explicit unavailable state).

## Tests Run
Command: `cd apps/frontend && npm run build`
Result: **green** — all 10 routes typecheck and compile; `/system-health` is now 4.44 kB (was the stub). UI behaviour is covered by browser QA (J-09/J-10), per project convention.

## Notes for QA / browser-QA
- **J-09:** at a stated horizon, assert the A–E bucket table renders numbers, excess-vs-SPY and excess-vs-QQQ render numbers, and the by-setup and by-regime tables render numbers — each with an `n` shown; the survivorship banner is visible; changing the horizon selector changes the figures. (Assert structural/relational properties — NOT exact return numbers.)
- **J-10:** the control-group panel shows the top-ranked cohort alongside random same-sector, SPY, QQQ, and sector-ETF — each numeric and labelled.
- The backend's first boot runs the walk-forward backfill (~223 s on a fresh DB); the runtime DB was warmed during dev verification so the page loads immediately. If the backend is restarted on a fresh DB, allow generous readiness time before loading the page.
