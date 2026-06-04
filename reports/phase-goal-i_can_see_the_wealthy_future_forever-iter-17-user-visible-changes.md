# Phase goal-i_can_see_the_wealthy_future_forever-iter-17 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-17
**Date:** 2026-06-04
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now read the **forward-tested evidence aggregate** (the historical track record of how the
  rankings actually performed) directly on the **Backtest** page (`/backtest`), in a section at the very
  bottom titled **"Forward-tested evidence (expanding window ≤ D)"**. Previously this lived only on the
  now-removed System Health page.
- Users can now see this evidence **scoped to a point in time**: moving the existing single global as-of
  date switcher (top of the app) to an earlier date re-points the Backtest evidence to use **only** the
  snapshots taken on or before that date, and the displayed sample size `n` shrinks. Returning to the
  latest date reproduces the full all-history numbers.
- Users can now switch the evidence between forward-return horizons using the **existing Backtest horizon
  selector** — the bucket/setup/regime/excess/control-group figures all update **without a page reload or
  network refetch** (all horizons ship in one payload).
- Users can read, for the chosen as-of date and horizon: forward return **by A–E score bucket**, **excess
  vs SPY and vs QQQ**, **by setup type**, **by market regime**, **VCP vs non-VCP**, **pullback-to-rising-DMA
  vs not**, **flat-base breakout vs not**, and the **control-group comparison** (top-ranked cohort vs random
  same-sector peers vs the benchmarks) — each cell showing its sample size `n` and a low-sample ⚠ flag,
  with honest "—" (NA) instead of a fabricated number where there is no data.

---

## What Changed in the Visible UI

- The **Backtest page** (`/backtest`) gained a new bottom section: **"Forward-tested evidence (expanding
  window ≤ <as-of date>)"** with a summary line (snapshots contributing, contributing as-of range, mean
  forward return + `n`) and seven evidence panels plus a control-group table.
- The summary line and panels are visually distinct from, and explicitly labelled apart from, the existing
  per-date scorecard — the new section is the **expanding-window aggregate** ("every snapshot dated ≤ D"),
  the scorecard is "what this date's cohort did".
- The **System Health** entry was **removed from the left sidebar navigation** (it sat between Backtest/
  Research-area items previously). The sidebar now lists 10 items and no longer shows "System Health".
- The **`/system-health` page no longer exists** — navigating to it returns a 404 (the route, page, and its
  data client were deleted).
- When a chosen as-of window has no measurable forward return yet, the section shows an explicit empty
  state ("No forward-tested evidence for this window yet") rather than blank space or zeros.

---

## What Old Behavior Changed

- **Forward-test evidence location & date-awareness:** previously the forward-return-by-bucket / excess /
  control-group aggregate was shown on **`/system-health`**, was **all-history**, and ignored the global
  as-of date. Now it is shown only on **`/backtest`** and is **as-of-scoped** — it reflects only snapshots
  dated on or before the global as-of date.
- **System Health navigation:** previously a "System Health" link existed in the sidebar and opened a
  dedicated page. That link and page are gone; the evidence moved to Backtest.
- **Backtest payload:** the `/backtest` page now carries an additional `evidence_by_horizon` block in its
  single API response. The existing per-date scorecard, Return Attribution, and leadership lists (Top
  Sectors / Top Themes / Ranked Cohort) are **unchanged and remain in the same order** (leadership lists
  still below Return Attribution).

---

## Not Visible Yet

- None. Every backend capability added this iteration (the as-of-scoped aggregate served by
  `GET /api/backtest`) is rendered on the Backtest page. No backend feature was left without a UI home.
- Note: the as-of scoping **seam** added to `compute_forward_aggregates` is reused by later iterations
  (J-26 composite cohort, J-32 Research as-of toggle), but those are out of scope here and introduce no
  UI this iteration.
