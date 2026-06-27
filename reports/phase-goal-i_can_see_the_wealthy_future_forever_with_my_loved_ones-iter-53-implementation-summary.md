# Goal iter-53 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-53
**Date:** 2026-06-27
**Written by:** developer

---

## Features Implemented

- **Regime Lab (new Research page).** A new lab at `/research/regime-lab`, reachable from the Research hub,
  that answers: "How have stocks' future returns and downside risk differed depending on the market
  regime?" It shows, for every forward-return horizon at once (1, 5, 10, 20, 60 trading days):
  - **By regime label** — one row for each of the six regime labels (Strong risk-on, Risk-on, Narrow
    leadership, Choppy, Defensive, Risk-off): the average realized forward return and the average paired
    worst-drawdown of all stock observations that happened under that regime, plus the sample size.
  - **By regime-score decile** — ten rows splitting the 0–100 regime score into ten equal-count buckets
    (D1 = lowest scores → D10 = highest): the same average return + paired drawdown per bucket, the bucket's
    score range, and a "Rank-IC" header row showing how strongly the regime score tracks the forward return
    at each horizon.
- **Drill into any number.** Every cell carries a clickable `N=` chip that opens the exact underlying
  observations (which stocks, on which dates) in the Research Samples view in a new browser tab. The count
  shown on the chip always equals the number of rows you see after drilling in.
- **Sort any column.** Click any column header to sort the table (ascending/descending); cells with too few
  observations always sort to the bottom rather than masquerading as a real number.
- **Point-in-time view.** The page honors the single global "As of date" toggle: switching to "As of date"
  restricts the evidence to snapshots on or before the chosen date, so the sample sizes shrink to a true
  walk-forward window. There is no separate date picker on the page.

---

## Changed Behavior

- **Research hub** now lists one additional lab tile ("Regime Lab"). No other Research page changed.

<!-- No existing figures or endpoints changed behavior. -->

---

## Backend-Only Items

<!-- None — every backend capability added is surfaced in the new page. -->

- None. The new `GET /api/research/regime-lab` endpoint and the new `regime-lab` Research-samples cohort are
  both wired to the UI (the page reads the endpoint; the `N=` chips read the samples cohort).

---

## Incomplete Items

- **Episodes vs Pooled view.** The endpoint supports both the "Episodes" (first-trigger) and "Pooled"
  (every observation) overlap-honesty views the sibling event-study labs use, but the page intentionally
  uses the "Pooled" view only and does not show a view toggle. Reason: this lab studies the entire universe
  of stocks, so the Episodes collapse would degenerate to each stock's first appearance and lose the point
  of a regime study. This matches the spec, which lists only the As-of toggle, column sort, and `N=` chips
  as the page's controls.

---

## Config and Environment Changes

- None. No new environment variables, no config-file changes, no database migration, and no new database
  table. The lab reuses the existing forward-return / scanner-run / regime values and the existing cache
  table.

---

## Known Limitations

- **Descriptive, survivorship-biased evidence — not a forecast.** All figures are realized historical
  averages over the current-membership universe, labelled as such on the page. They are association, never a
  prediction, and never an order/trade suggestion.
- **Thin buckets show NA + sample size, never a fabricated number.** A regime label or score decile with too
  few observations (or at/near the latest date, where forward returns are not yet known) is shown as "NA"
  with its honest sample count.
- **Wide tables scroll sideways.** Showing all five horizons as paired (return, drawdown) columns makes the
  tables wide; they scroll horizontally on narrow screens rather than hiding columns.
- The first (uncached) load of the page runs one heavy read over the full forward-return history and can
  take tens of seconds; subsequent loads are served from cache and are near-instant. The cache refreshes
  automatically whenever the underlying data changes.
