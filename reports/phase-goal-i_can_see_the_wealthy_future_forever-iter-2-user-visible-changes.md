# Phase goal-i_can_see_the_wealthy_future_forever-iter-2 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-2
**Date:** 2026-06-01
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

This iteration delivers **return attribution / contribution analysis (J-19)**: a read-only "Return
attribution" section that opens any forward-test mean return into its drivers. It appears on two
existing pages.

- Users can now see **which individual tickers most drove or dragged a cohort's forward return** by
  scrolling to the new "Return attribution" section on `/system-health` (aggregate, across all
  contributing snapshots) or `/backtest` (for the selected as-of date). The "Top contributors &
  detractors" panel names each ticker with its sector, realized mean return, and sample size `n`.
- Users can now see the **shape of the return distribution**, not just the mean, in the
  "Distribution & hit-rate" panel: mean, median, % positive (hit rate), dispersion (σ), and `n`.
- Users can now see **forward return broken down by sector** ("Forward return by sector" panel) and
  **by rank band** ("Forward return by rank band" panel — e.g. 1–10 / 11–50 / 51+), each band shown
  even when empty (rendered as NA).
- On `/backtest`, users can now **switch which horizon the attribution section describes** using a new
  segmented "Horizon" selector (1d / 5d / 10d / 20d / 60d) in the section header — this re-renders the
  attribution panels from data already loaded for that date, without changing the as-of date and
  without a refetch.

---

## What Changed in the Visible UI

- The **`/system-health` page** now shows a new "Return attribution" section appended below the
  existing "Control-group comparison" panel. It rides the page's existing top-right Horizon selector —
  no new control was added there.
- The **`/backtest` page** now shows a new "Return attribution" section appended below the
  "Forward-test scorecard" table. Its header carries a **new segmented "Horizon" view selector**.
- Both sections render four shadcn Card panels in a two-column grid: "Top contributors & detractors",
  "Distribution & hit-rate", "Forward return by sector", and "Forward return by rank band".
- Directional values (mean / median) use the existing green/red return colouring; hit rate and
  dispersion are shown as neutral unsigned magnitudes. NA values (n=0) render an em dash; figures with
  `n` below `min_sample` carry the existing low-sample `⚠` flag.

---

## What Old Behavior Changed

- **No existing behavior changed.** The iteration is additive: no existing canonical value is
  recomputed, no existing endpoint signature changed, and no navigation changed. The attribution
  figures are re-formatted from data the backend already derived from stored per-observation forward
  returns.
- **`/backtest` date behavior is preserved (J-18).** The new Horizon control on `/backtest` is a *view*
  selector over already-fetched data — it holds no date state, triggers no refetch, and keys no date
  effect. The page still reads only the single global as-of switcher.
- Note for regression testers: on `/backtest`, the "Distribution & hit-rate" mean is computed over the
  full observed set at the selected horizon and need **not** equal the scorecard's top-ranked-cohort
  mean shown above it. This is expected, not an inconsistency. (The aggregate `/system-health`
  distribution mean does equal the page's overall mean.)

---

## Not Visible Yet

- **J-17 (Data Manager)** — the `/data` page and `/api/data` fetch/backfill job — remains unbuilt and
  was explicitly out of scope this iteration. It is the natural next target.
- No backend attribution capability is left unexposed: every slice the engine produces
  (`per_stock`, `distribution`, `by_sector`, `by_rank_band`) is rendered in the new UI section on both
  pages.
