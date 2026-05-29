# Goal Iteration 2 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future-iter-2
**Date:** 2026-05-29
**Written by:** developer

---

## Features Implemented

- **Market Regime read (Dashboard, `/`)**: After the close, the app now states whether the overall
  US market is risk-on, risk-off, or somewhere in between — one of six labels (Strong risk-on,
  Risk-on, Narrow leadership, Choppy, Defensive, Risk-off) — alongside a 0–100 score and the named
  reasons behind it (index trend, market breadth, new-highs vs new-lows, and a volatility/VIX check).
- **Sector & Industry Leaderboard (`/sectors`)**: The Sectors page now ranks every sector ETF and
  industry-group ETF strongest-to-weakest, each with a letter grade A–E (colour-graded green→red),
  its strength relative to the S&P 500 (RS-vs-SPY), how far it sits below its 52-week high, and a
  plain trend label. Clicking any row reveals the individual components that produced its grade.
- **Market breadth & data-as-of date (Dashboard)**: Shows what share of tracked stocks are above
  their 50-day and 200-day averages — clearly labelled "universe-relative" for honesty — plus the
  exact date the underlying data reflects.
- **Top Sectors at a glance (Dashboard)**: A short list of the strongest sectors that reads the
  *same* ranking the full Sector Leaderboard shows (one source of truth — no second computation).
- **Honest "pending" placeholders (Dashboard)**: Candidate counts (# Actionable / Breakout-watch /
  Pullback-watch) and Top Themes display an explicit "pending" marker instead of a fabricated zero,
  because they depend on per-stock and theme scoring that arrives in the next iteration.

---

## Changed Behavior

- **Dashboard (`/`)**: Previously rendered an empty "coming soon" placeholder. Now renders the live
  Market Regime panel, breadth metrics, the data date, the Top Sectors list, and honest pending
  markers for the not-yet-built sections.
- **Sectors (`/sectors`)**: Previously an empty placeholder. Now a populated, ranked, expandable
  leaderboard table.

---

## Backend-Only Items

- None. Every new value the backend computes this iteration (market regime, sector/industry scores,
  breadth, data-as-of date) is surfaced on a page. The indicator math, the date-boundary accessor,
  and the A–E grading function are internal building blocks of those features, not separate
  user-facing capabilities.

---

## Incomplete Items

These are deferred by design per the iteration plan — not omissions:

- **Candidate counts and Top Themes (Dashboard)**: Shown as "pending"; they require the per-stock
  scoring and theme scoring scheduled for the next iteration (iter-3).
- **Daily dashboard journey (J-01)**: Only *partially* advanced this iteration (regime + breadth +
  data date + top sectors are real). It fully completes once candidate counts and Top Themes land in
  iter-3. The Sector Leaderboard journey (J-04) is fully delivered this iteration.
- **Saved / immutable run history**: The regime and sector rankings are computed fresh on each
  request from the frozen dataset. Saving each day's scan as an immutable snapshot (and showing a
  "scan ran at" timestamp) is scheduled for a later iteration (iter-5); until then the displayed
  "Data as-of <date>" is the latest date in the dataset.

---

## Config and Environment Changes

- **`config.yaml`** gained three additions (every tunable number lives here, never in code):
  - a new **`indicators:`** section — moving-average lengths, relative-strength lookback windows,
    the 52-week-high window, volume and ATR periods, and the minimum-history floor below which a
    symbol's long-window metrics report "NA".
  - a new **`sectors:`** section — the weighting of the six leadership components and the score→trend
    label cutoffs.
  - **`regime.label_edges`** — the score→regime-label cutoffs (the six label names already existed).
- The app refuses to start with an explicit error if any of these are missing or inconsistent (e.g.
  weights that don't add up, or cutoffs that don't cover the full 0–100 range) — it never silently
  guesses a default.
- **No environment variables changed. No secrets, keys, or credentials added.**

---

## Known Limitations

- **Universe-relative breadth**: The breadth and new-high/new-low figures are computed from the
  ~120-stock tracked universe, not the entire US market. They are labelled "universe-relative"
  everywhere they appear so they are never mistaken for full-market internals.
- **Short-history ETFs**: A few newer ETFs (e.g. WGMI, BKCH, GEV) lack a full year of history, so
  their long-window metrics (6-month relative strength, distance-from-52-week-high) display "NA"
  rather than a guessed number. They are still ranked on the components that *can* be computed.
- **Offline frozen data**: All figures come from the committed seed dataset (latest date
  2026-05-28). No live/network data is fetched this iteration, so results are fully reproducible.
- **Backend must be running**: If the backend is unreachable, both pages show an explicit "Backend
  unavailable" message rather than any fabricated rows or scores.
