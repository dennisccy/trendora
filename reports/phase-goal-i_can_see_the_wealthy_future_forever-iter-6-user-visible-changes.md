# Phase goal-i_can_see_the_wealthy_future_forever-iter-6 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-6
**Date:** 2026-06-02
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On a stock's detail page (`/stocks/[ticker]`), users now see the price chart drawn **all the way through the latest available date**, not just up to the chosen as-of date. When viewing a past ("historical") as-of, the days that came *after* that date are shown so the user can see how the stock actually moved next.
- Users can now visually tell apart the **as-of snapshot** from the **forward (after-the-as-of) days** on the chart: the forward candles and their volume bars are greyed out, a marker arrow labelled "as-of {date}" sits exactly at the as-of boundary, and the chart legend gains a "Forward — after as-of {date} (display only)" swatch.
- On the Backtest page (`/backtest`), users now see, for the **Top Sectors, Top Themes, and Ranked Cohort** lists, a **realized forward-return value** for each row at the currently selected horizon — i.e. how much that sector / theme / stock actually returned after the as-of date.
- Users can re-point all of those return figures (and the existing Return Attribution panels) at a different horizon using the **single horizon view selector** in the Return Attribution header — one control now drives both the attribution and the three lists' return columns at once, with no page reload or refetch.

---

## What Changed in the Visible UI

- The price chart on `/stocks/[ticker]` now requests the full price path through the latest seed date. At a historical as-of it shows a muted "forward" region; at the latest as-of there is no forward region and the chart looks the same as before.
- A new **one-line caption** appears above the chart (only when a forward region is present) stating that the forward bars are display-only and do **not** affect the scores / setup / VCP shown below.
- The chart legend now conditionally shows a **"Forward — after as-of {date} (display only)"** entry, and an **as-of divider marker** (arrow + label) is drawn at the as-of boundary.
- The Backtest page sections were **re-ordered**. New top-to-bottom order: **As-of scan summary (regime + candidate counts) → Forward-test scorecard → Return Attribution → Top Sectors → Top Themes → Ranked Cohort**. The three leadership lists, which previously sat above the scorecard, now sit **below** Return Attribution.
- Each of the three leadership lists (Top Sectors, Top Themes, Ranked Cohort) gained a **realized-return column** at the selected horizon, rendered with the existing return component (shows "—"/NA when a horizon has no after-the-as-of data, and the existing low-sample ⚠ when the sample is small).
- The Ranked Cohort table is horizontally scrollable on narrow screens to accommodate the new column.

---

## What Old Behavior Changed

- **Stock-detail chart range:** previously the chart stopped at the as-of date. Now it extends through the latest date when viewing a historical as-of (the extra region is greyed out and clearly labelled). The scores, setup, VCP, and invalidation panels are unchanged — they still read only the as-of snapshot.
- **Backtest leadership lists position:** previously Top Sectors / Top Themes / Ranked Cohort appeared above the forward-test scorecard. They now appear below Return Attribution and carry a new return column.
- **Horizon selector scope:** previously the horizon view selector re-pointed only the Return Attribution panels. It now also re-points the realized-return columns on the three leadership lists. It remains a *view* selector — it does not change the as-of date or trigger a data refetch (the global as-of switcher is still the only date control).

---

## Not Visible Yet

- The new `through=latest` mode of the bars API and the per-bar `is_forward` / `latest_date` fields are consumed only by the stock-detail chart; no other surface exposes them. (This is intentional — they are display-only and explicitly never feed scores/setups/VCP/rankings.)
- All implemented backend capability for this iteration is surfaced in the UI; there is no hidden new endpoint or unwired feature.
