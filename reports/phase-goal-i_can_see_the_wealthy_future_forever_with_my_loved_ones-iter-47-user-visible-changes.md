# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47
**Date:** 2026-06-22
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Navigate to `/research/event-study` and see a populated matrix of per-horizon mean return / win-rate / N cells for every setup pattern — these previously showed "Backend unavailable" / a permanent loading state on the full live dataset and now load successfully.
- Navigate to `/research` (Factor Lab) and see the decile sort table and rank-IC figure per factor — these previously returned HTTP 500 on the full live dataset and now render real figures within one minute of a cold cache.
- Navigate to `/research` and run a multi-factor composite query (Factor-combination) — this now returns results reliably on the full live dataset.
- Navigate to `/research/regime-setup-pattern` and see the Regime x Setup x Pattern ranked table — this previously MemoryError'd on the live data and now loads.
- Navigate to `/research/downtrend-opportunity` and see the Downtrend Opportunity lab figures — now loads on the full live dataset.
- Click any `N=` chip on any of the five heavy Research labs and drill into `/research/samples` — drill-down count is coherent with the parent figure's reported N, as before.

---

## What Changed in the Visible UI

- No visible UI elements changed. No layout, labels, navigation links, component structure, or displayed values were modified.
- Every matrix cell, mean return, win-rate, sample count (N=), and `N=` drill-down cohort is identical in value to what was shown before the iter-46 regression introduced the OOM failure.

---

## What Old Behavior Changed

- Research labs (event-study, Factor Lab, factor-combination, regime-setup-pattern, downtrend-opportunity): previously returned "Backend unavailable" or an HTTP 500 error when the full live dataset was used (~3 million rows). Now respond with HTTP 200 and render real figures. This is a restoration of behavior that worked before the data grew past available host RAM.

---

## Not Visible Yet

- None. All implemented capabilities are accessible via the existing `/research/*` UI surfaces. No new endpoints or pages were added; no backend capability exists without a corresponding UI access point.
