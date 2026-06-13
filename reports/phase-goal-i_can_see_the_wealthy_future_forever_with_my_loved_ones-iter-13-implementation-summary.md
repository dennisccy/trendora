# Iteration 13 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13
**Date:** 2026-06-13
**Written by:** developer

---

## Features Implemented

- **Per-date availability heatmap (J-61)**: On the Data Manager page (`/data`), a new calendar grid shows,
  for every trading day, how many symbols have price data that day (the cell's color depth) and whether a
  saved snapshot exists for it (a ring around the cell). Hovering or focusing a day shows the exact figures
  — the date, "X of Y symbols", and whether a snapshot exists. A day with little data looks visibly fainter
  than a fully-covered day; a day with no extra data is shown honestly, never hidden as if it were covered.
- **Click a day to set up the next data job (J-61)**: Clicking a day in the heatmap fills in the Start and
  End dates of the fetch/backfill form below it. Shift-clicking a second day fills in a date range. This
  only fills the job form — it does NOT change the date the rest of the dashboard is viewing.
- **The heatmap refreshes itself (J-61)**: After a data job finishes, or after data is removed, the heatmap
  re-reads and shows the new coverage automatically.
- **As-of date calendar picker (J-62)**: The date control in the top bar changed from a plain dropdown to a
  calendar pop-up. The calendar marks only the dates that actually have a saved snapshot as selectable;
  every other day is greyed out and unclickable. You can page through months back to the oldest stored
  month, press "Latest" to return to today's view, and operate the whole thing by keyboard.

---

## Changed Behavior

- **Top-bar date control**: Previously a flat dropdown listing every available date. Now a calendar pop-up
  that visually distinguishes selectable snapshot dates from unavailable days. It picks the SAME dates and
  drives the SAME single date control as before — the historical "viewing as-of …" badge, the shareable
  `?asof` link, and links that carry the date are all unchanged in behavior.
- **Data Manager page**: Now shows the availability heatmap directly under the existing coverage figures.
  Everything else on the page is unchanged.

---

## Backend-Only Items

- None. The one new backend endpoint (`GET /api/data/availability`) is fully wired to the heatmap UI.

---

## Incomplete Items

- None deferred from this iteration's spec. J-63 (event-study first-trigger episodes) is explicitly out of
  scope and is the next iteration's target.

---

## Config and Environment Changes

- None. No new configuration setting, no environment variable, no database column or migration. The
  heatmap's color scale is purely a presentation detail in the frontend (no server-side threshold was
  added), which deliberately avoids the configuration fan-out that caused last iteration's failure.

---

## Known Limitations

- The data figures shown are descriptive only — counts of stored price bars and existing snapshots. The
  endpoint deliberately recomputes no score, return, or ranking; it reads the exact same data the existing
  coverage figures read, so the two can never disagree.
- The heatmap draws one clickable square per trading day (about 1,356 on the current dataset). It scrolls
  within its card and performs fine at this scale; a far larger history would eventually warrant a more
  optimized rendering approach.
- The QA backend that was already running when this work was done does not auto-reload, so it must be
  restarted once before the new availability endpoint is reachable in the browser. A fresh backend start
  picks it up automatically; the endpoint itself was verified working against the real dataset.
