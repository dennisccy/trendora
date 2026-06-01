# goal-i_can_see_the_wealthy_future_forever-iter-1 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-1
**Date:** 2026-06-01
**Agent:** developer
**Mode:** INITIAL BUILD — lean goal-mode iteration
**Status:** complete

## Summary

J-18 / coherence-invariant-#5 consolidation: the **Backtest** page now reads the **single global
top-bar as-of switcher** and holds **no date state of its own**. The page-local "Backtest as-of
date" `<Select>` dropdown (`BacktestDatePicker`) and its independent date machinery are deleted; the
page consumes `useAsOf()` exactly like `app/stocks/page.tsx` already does, so one resolved date now
governs every date-scoped page — Dashboard, Stocks, Themes, Sectors, Stock Detail, **and Backtest**.

This is a **single-file frontend refactor** consuming an already-proven provider. Per the iter spec:
no backend, API, config, data-model, engine, or contract change. The resolved as-of date is the
existing canonical value; Backtest now reads it from the one global source instead of computing its
own option list via a second `fetchRuns()`.

## What Was Built
- `apps/frontend/app/backtest/page.tsx` now imports and uses `useAsOf()` (`const { asOf, isHistorical } = useAsOf()`) and drives **every** fetch from the global `asOf`:
  - `fetchBacktest(asOf ?? undefined, signal)` (the scorecard — the page's reason to exist)
  - the best-effort scan-summary fetches `fetchDashboard` / `fetchSectors` / `fetchThemes` / `fetchStocks`, each `(asOf ?? undefined, signal)`
  - the data `useEffect` is keyed on `[asOf]`, so changing the global switcher re-points the page.
- The read-only **"Viewing as-of D (historical|latest)"** badge is re-derived from the backtest
  response (`state.backtest.asof_date` / `!state.backtest.is_latest`), falling back to the global
  switcher's own state (`asOf` / `isHistorical`) before the response loads. It is a **display
  indicator, not a control** — no `<Select>` and no independent date state were reintroduced.

### Deleted (page-local date machinery — the J-18 violation)
- The `dates` / `latest` / `ready` / `selected` `useState` hooks (the page's own date state).
- The `useEffect` that called `fetchRuns()` to populate the page's own picker options.
- The `<BacktestDatePicker .../>` usage in the page header (and the now-pointless `justify-between`
  flex wrapper around the heading).
- The `BacktestDatePicker` component definition itself (the `<Select aria-label="Backtest as-of date">`).
- The now-unused imports: `fetchRuns` (from `@/lib/api`) and `Select` (from `@/components/ui/select`).

### Preserved (unchanged behavior — protects J-14 and the other journeys)
- The as-of scan summary (Market Regime, Candidate Counts, Top Sectors, Top Themes, Ranked cohort).
- The forward-test scorecard: per-horizon cohort return, excess vs SPY/QQQ/sector, random-same-sector
  + SPY/QQQ/sector-ETF control columns, each with sample size **n**, and the honest **NA (n=0)** / low-sample
  (`n < min ⚠`) / empty-state rendering — nothing fabricated.
- The survivorship-bias banner and the backend-unavailable error card.

## Files Changed
- `apps/frontend/app/backtest/page.tsx` — consume the global `useAsOf()` provider; delete the
  page-local date picker, date state, and `fetchRuns()` effect; re-derive the as-of badge.
  (git diff: **1 file changed, 17 insertions(+), 81 deletions(-)** — net −64 lines.)

No other file (provider, switcher, other pages, backend, config) was touched — surgical-change
discipline per the spec NOTES.

## J-18 source-level verification gate (per spec NOTES / the iter-0 lesson)

The iter-0 lesson: *when the Chrome-MCP tool layer is degraded, browser-QA's negative interaction
findings are unreliable — confirm single-source-of-truth / date-control claims against frontend
source, not a screenshot.* Confirmed against the edited source:

- **(a) No page-local picker / no `<Select>` for dates.**
  `grep -nE "BacktestDatePicker|<Select" app/backtest/page.tsx` → **no matches**. The
  `BacktestDatePicker` definition, its usage, and the `Select` import are all gone.
- **(b) Imports `useAsOf` and keys the data effect on `asOf`.**
  Line 6 `import { useAsOf } from "@/components/asof-provider";`; line 54
  `const { asOf, isHistorical: globalIsHistorical } = useAsOf();`; the data effect ends `}, [asOf]`.
- **(c) Holds no independent date state.**
  `grep -nE "\bselected\b|setDates|setLatest|setReady|fetchRuns" app/backtest/page.tsx` → **no
  matches**. The only `useState` remaining is the `state` machine (loading/ok/error) — no date state.

## Error-case degradation (spec TESTING REQUIREMENTS — error cases)
The page no longer depends on its own `fetchRuns()` for graceful degradation. When `GET /api/runs`
is unavailable, the **provider** catches it and degrades to latest-only (`asOf = null`, switcher
disabled); Backtest then reads `asOf = null` → `fetchBacktest(undefined)` → renders the **latest**
scorecard (or its existing honest error/empty state) and does **not** crash. This is now inherited
from the single global source rather than duplicated on the page.

## Anti-goal check
- **Exactly one date selector (invariant #5) — SATISFIED.** Backtest now reads the single global
  as-of control and exposes no picker of its own; the frontend holds no second, independent date
  state. (This is exactly the live violation iter-0 recorded; it is now resolved in source —
  enabling the evaluator to mark the journey-history `anti_goal_violations` date-selector entry
  `resolved: true`.)
- **Single source of truth / No recompute in the read path — preserved.** No score, return, bucket,
  or date is computed on the page; all values come from the existing endpoints for the resolved
  `asOf`. No new computation, endpoint, or contract value was introduced.
- **No fabricated data — preserved.** The scorecard's NA/n honesty and empty/error states are
  unchanged.
- No new anti-goal violation introduced.

## Tests Run
- **Frontend (primary gate — typechecks the rewiring):** `cd apps/frontend && npm run build`
  → **✓ Compiled successfully**, "Checking validity of types" passed, exit 0; 12 routes generated
  incl. `/backtest` (5.9 kB, down from the removed code). TypeScript validates the deleted-state /
  removed-import rewiring.
- **Backend (guard — no backend change):** `cd apps/backend && .venv/bin/python -m pytest tests/`
  → **248 passed / 0 failed in 832.47s (0:13:52)** — unchanged from the iter-0 baseline (248/0),
  confirming no backend regression.

## Notes for downstream (browser-QA / coherence-auditor / evaluator)
1. **Authoritative J-18 / J-13 / J-14 verdicts come from browser-QA**, but per the iter-0 lesson the
   **J-18 pass is governed by the source-level gate above** — do not pass/fail J-18 on a visual
   "no dropdown" screenshot alone (iter-0 QA wrongly reported "no separate date dropdown" while the
   source still had `BacktestDatePicker`).
2. **J-13 re-verify:** the J-18 flow (change global switcher → every page incl. Backtest re-points)
   is J-13's acceptance extended to Backtest; **no code change beyond this edit** is needed. If the
   Chrome-MCP layer is degraded and the interaction can't be driven, record **PARTIAL** with the
   reason (per DoD) — it must not be reported as a failure.
3. **Browser-QA setup:** start backend (port 8835) + frontend (port 3835); the provider/switcher are
   already mounted in `app/layout.tsx`, and available dates come from `GET /api/runs` (same source
   the page previously used) so the option list + default-latest behavior are unchanged.
4. **Out of scope (do not expect here):** J-19 return attribution and J-17 Data Manager — deliberately
   deferred so they build onto a Backtest already wired to the global date control.

## Known Issues
- None introduced. The page's loading-state badge shows nothing until the first response when viewing
  *latest* (because the global `asOf` is `null` for latest); once the scorecard loads it shows
  "Viewing as-of D (latest)". For a selected *historical* date the badge shows immediately from the
  global `asOf`. This is a cosmetic display-timing nuance, not a regression (the prior page had the
  same "no badge until `latest` resolved" behavior on first paint).
