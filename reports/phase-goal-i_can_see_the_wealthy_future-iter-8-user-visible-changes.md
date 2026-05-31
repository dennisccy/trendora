# Phase goal-i_can_see_the_wealthy_future-iter-8 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future-iter-8
**Date:** 2026-05-31
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now **time-travel the whole dashboard** — pick any past trading day from a new drop-down in the top bar and see the Dashboard, Stocks list, a Stock's detail page, Themes, and Sectors exactly as the scanner recorded them on that date.
- Users can now **tell at a glance whether they are looking at a historical view** — an amber "Viewing as-of D (historical)" badge appears in the top bar whenever a past date is selected, and a quiet "Latest" badge appears otherwise.
- Users can now **keep a chosen date while moving between pages** — selecting a date on the Dashboard and then clicking through to Stocks, Themes, Sectors, or a stock's detail page keeps showing that same date's snapshot (the date carries across in-app navigation).
- Users can now **return to the current view instantly** — choosing "Latest" in the switcher resets every as-of-aware page back to the newest snapshot.
- Users can now **see a stock's price/moving-average chart as of the selected date** — the chart shows only the bars up to and including that day, so no future price action appears in a historical view.

---

## What Changed in the Visible UI

- A new **as-of date switcher** (a drop-down listing "Latest" plus every stored Scanner-Run date) now sits in the top bar of every page, next to the existing health badge.
- A new **as-of indicator badge** sits beside the switcher: amber "Viewing as-of D (historical)" when a past date is selected, quiet "Latest" otherwise.
- The **Dashboard** "Data as-of {date}" label, and the "as of {date}" labels on the **Stocks list**, **Stock detail**, **Themes**, **Sectors**, and the **stock price chart**, now reflect the selected historical date instead of always showing the latest date.
- **No new page, route, or sidebar entry was added** — the only new UI is the global top-bar control and its indicator.

---

## What Old Behavior Changed

- **Dashboard / Stocks (list + detail) / Sectors / Themes**: previously each request recomputed the market regime, sector, theme, and per-stock scores live on every request. Now each page serves the stored values from the immutable snapshot for the resolved date and echoes which date it served. For the latest date the values are unchanged in meaning — they are the same numbers, now read from storage rather than recomputed. (Testers: re-verify these pages render correct numbers at latest, and that a stock's three scores match between the list and the detail page.)
- **Stock price chart**: previously always showed the latest available bars. Now it shows only the bars up to and including the selected as-of date.
- **Watchlist**: unchanged from the user's point of view. Internally its current scores/setup/invalidation are now read from the latest saved snapshot (the same row the Stocks page serves) instead of a separate live computation — keeping the two perfectly in sync. (Testers: re-verify watchlist current values still match the Stocks list at latest.)

---

## Not Visible Yet

- The backend can **create a snapshot on first view for any in-range seed trading day** that was never scanned, but the switcher only offers dates that already have a stored snapshot (the run-history dates). There is no free-form calendar widget in the UI to reach an arbitrary uncomputed date — this create-once path is exercised by tests, not normal use (out of scope this iteration by design).
- The selected as-of date is **not a bookmarkable URL** — a full browser reload returns to the "Latest" view (in-app navigation preserves the date; a hard refresh does not).
