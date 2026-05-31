# Phase goal-i_can_see_the_wealthy_future-iter-10 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future-iter-10
**Date:** 2026-05-31
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now open a **Backtest / Time-Machine** workspace by clicking the new **Backtest** entry in the left sidebar (route `/backtest`).
- Users can now **time-travel to any historical scan date** using the page's own "As-of date" picker (top-right of the Backtest page), independent of the global top-bar date switcher. Selecting a date re-fetches the whole page for that date.
- Users can now read a **per-date forward-test scorecard** — a table of how that date's top-ranked cohort actually performed over the next **1 / 5 / 10 / 20 / 60 trading days**, showing the cohort mean return, **excess vs SPY / QQQ / sector**, a **random same-sector control**, and the SPY / QQQ / sector-ETF control cohorts — each cell with its sample size `n`.
- Users can now see, on the same page, the **as-of scan summary** for the chosen date: market regime (label + 0–100 score), candidate counts (Actionable / Breakout-watch / Pullback-watch), top sectors, top themes, and the ranked stock cohort (top 10).
- Users can now distinguish **honest NA from real results**: horizons whose forward window has not elapsed in the seed show "—" with `n=0` (never a fabricated number); low-sample figures (`n < min_sample`) are flagged with a ⚠ token.
- Users can now see a **"Viewing as-of D (historical|latest)"** badge and a **survivorship-bias banner** clarifying the limitations of the walk-forward evidence.

---

## What Changed in the Visible UI

- A new **Backtest** navigation item (FlaskConical icon) was added to the sidebar, placed after *Scanner Runs* and before *System Health*.
- A new page at **`/backtest`** renders two sections: an **As-of scan summary** (regime, candidate counts, top sectors, top themes, ranked cohort) and a **Forward-test scorecard** table.
- The Backtest page has its **own "As-of date" dropdown** (defaulting to "Latest · <date>", with historical dates listed below).
- A **survivorship-bias warning banner** and an as-of indicator badge appear near the top of the page.
- The scorecard table is dense, monospace, and horizontally scrollable, with columns: Horizon, Cohort, vs SPY, vs QQQ, vs Sector, Random peers, SPY, QQQ, Sector ETF.
- The **System Health page** is visually unchanged but now imports its realized-return formatting helpers (`fmtPct` / `returnClass` / `SampleSize` / `Return`) from a new shared module — same rendering, single source.

---

## What Old Behavior Changed

- **System Health page formatting:** the four return-formatting helpers were moved out of `system-health/page.tsx` into a shared `components/forward-return.tsx`. No user-visible behavior change is expected — re-verify that System Health's forward-return figures and ⚠ low-sample flags still render identically.
- No other existing page (Dashboard, Stocks, Themes, Sectors, Scanner Runs, Stock Detail, Run Detail) changed behavior. The global top-bar as-of switcher's scope is unchanged and does **not** drive the Backtest page.

---

## Not Visible Yet

- None. The single new backend capability this iteration (the per-date forward-test scorecard, `GET /api/backtest`) is fully wired into the `/backtest` page and reachable from the sidebar.
- (Out of scope this iteration, not "hidden": VCP detection (J-16) and the config-backed glossary / `/methodology` page (J-12) are deferred to later iterations.)
