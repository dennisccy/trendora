# Phase goal-i_can_see_the_wealthy_future-iter-10 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future-iter-10
**Date:** 2026-05-31
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` (all pages) | `Sidebar` nav | Added navigation | New top-level "Backtest" section (J-14), placed after Scanner Runs / before System Health | Confirm a **Backtest** item (FlaskConical icon) appears between "Scanner Runs" and "System Health"; click it and confirm the URL becomes `/backtest` and the item shows the active indicator |
| `/backtest` | `BacktestPage` | New page | Backtest / Time-Machine workspace landing | Navigate to `/backtest`; confirm the page heading "Backtest", the As-of date picker, the survivorship banner, the As-of scan summary, and the Forward-test scorecard all render without error |
| `/backtest` | `BacktestDatePicker` (As-of date `Select`) | New component | Page-local date picker drives all fetches independent of the global switcher | Open the "As-of date" dropdown; confirm it lists "Latest · <date>" plus historical dates; select an older date and confirm the as-of badge, scan summary, and scorecard re-fetch for that date |
| `/backtest` | `ScanSummarySection` — Market Regime card | New component | Re-displays the canonical regime for the chosen date (reuses `fetchDashboard(D)`) | Pick a historical date with data; confirm the regime label is one of the six valid labels and a numeric 0–100 score is shown (matches the Dashboard page for the same date) |
| `/backtest` | `CandidateCountsCard` | New component | Shows Actionable / Breakout-watch / Pullback-watch counts for the date | Confirm three numeric counts render; cross-check the Actionable count equals the Dashboard's for the same as-of date |
| `/backtest` | `ScanSummarySection` — Top Sectors list | New component | Re-displays top-N sectors for the date (reuses `fetchSectors(D)`) | Pick a full-window historical date; confirm ≥3 ranked sectors appear, each with rank, ticker, trend label, and a score badge |
| `/backtest` | `ScanSummarySection` — Top Themes list | New component | Re-displays top-N themes for the date (reuses `fetchThemes(D)`) | Confirm ≥3 ranked themes appear, each with rank, name, trend label, and a score badge |
| `/backtest` | `ScanSummarySection` — Ranked cohort table | New table | Shows the top-10 ranked stocks the scorecard forward-tests (reuses `fetchStocks(D)`) | Confirm up to 10 rows render with rank, ticker, setup status, and leadership score badge |
| `/backtest` | `ScorecardSection` — Forward-test scorecard table | New table | The genuinely new per-date value from `GET /api/backtest` (J-14) | Pick an older date (≥60 post-bars); confirm rows for 1/5/10/20/60d with **numeric** Cohort return, vs SPY/QQQ/Sector excess, Random peers, and SPY/QQQ/Sector-ETF cohorts, each showing `n=` |
| `/backtest` | `ScorecardSection` — NA / partial rendering | New behavior | Honest NA for windows not yet elapsed in the seed | Pick the **Latest** (or a recent) date; confirm longer horizons show "—" with `n=0` and that **no** fabricated numbers appear; confirm the "No elapsed forward window" empty state shows when every horizon is NA |
| `/backtest` | `ScorecardSection` — low-sample ⚠ flag | New behavior | Flags figures with `n < min_sample` | Find a horizon/cohort with a small `n`; confirm it is flagged with the ⚠ `--warn` token |
| `/backtest` | `SurvivorshipBanner` | New component | Surfaces honest limitation (survivorship bias) | Confirm a warn-styled banner with survivorship-bias text is visible on the page |
| `/backtest` | As-of indicator `Badge` (`data-testid="backtest-asof"`) | New component | Shows whether the resolved date is historical or latest | Select a historical date → confirm an amber "Viewing as-of D (historical)" badge; reset to Latest → confirm a "Viewing as-of D (latest)" badge |
| `/backtest` | Error state card ("Backend unavailable") | New behavior | Degrades safely when the scorecard API fails | With the backend stopped, load `/backtest`; confirm a "Backend unavailable" card appears and no fabricated figures are shown |
| `/system-health` | `system-health/page.tsx` (return helpers) | Changed behavior (refactor) | Return-formatting helpers moved to shared `components/forward-return.tsx` | Re-verify System Health's forward-return figures, percentages, sample sizes, and ⚠ low-sample flags render identically to before (regression check) |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/forward_testing.py` — `_insert_run_forward_returns` (factored shared INSERT helper), `backfill_run_forward_returns`, `_scorecard_excess`, `compute_run_scorecard` — power the `/api/backtest` scorecard but are not themselves UI surfaces (their output is surfaced via the scorecard table above).
- `apps/backend/main.py` — registers the new `backtest` router under `/api`; no direct UI surface.
- `apps/backend/tests/test_backtest_scorecard.py`, `apps/backend/tests/test_api_backtest.py` — new tests; no UI surface.

> Note: `apps/backend/app/api/backtest.py` (`GET /api/backtest`) is a backend-API change, but it **is** consumed by the frontend (`fetchBacktest` in `lib/api.ts`, used by `/backtest`), so its user-visible impact is captured by the scorecard rows above — it is not "not visible yet".

---

## Summary

- **Frontend surfaces changed:** 14 (13 new on `/backtest` + 1 sidebar nav + System Health refactor regression check)
- **New pages/routes:** 1 (`/backtest`)
- **Modified components:** `sidebar.tsx` (nav entry), `system-health/page.tsx` (shared-helper refactor), `lib/api.ts` (`fetchBacktest` + types); new shared `components/forward-return.tsx`
- **Navigation changes:** yes — new top-level **Backtest** sidebar entry
- **Backend-only changes:** 4 files (`forward_testing.py`, `main.py`, 2 test files); `backtest.py` is backend-API but consumed by the frontend
