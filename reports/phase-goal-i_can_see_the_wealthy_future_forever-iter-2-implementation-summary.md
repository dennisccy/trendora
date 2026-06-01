# Goal Iteration 2 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-2
**Date:** 2026-06-01
**Written by:** developer

---

## Features Implemented

- **Return attribution (J-19)**: On both the **System Health** and **Backtest** pages, any forward-test
  return can now be opened into four diagnostic layers for a chosen horizon, so a weak (or strong)
  headline number is explainable rather than taken at face value:
  - **Top contributors & detractors** — the individual tickers that drove the cohort up or dragged it
    down, each shown with its mean realized forward return, its sample size, and its sector.
  - **Forward return by sector** — the mean realized return per sector, each with its sample size.
  - **Forward return by rank band** — the mean realized return for the configured rank bands
    (1–10 / 11–50 / 51+), each with its sample size.
  - **Distribution & hit-rate** — the shape of the same returns: mean, median, percent-positive
    (hit rate), and dispersion (standard deviation), with the sample size.
- **Backtest horizon view selector**: a small segmented control on the Backtest page lets the operator
  pick which horizon's attribution to read (1 / 5 / 10 / 20 / 60 days). It only changes which
  already-loaded numbers are shown — it does **not** re-run anything, fetch anything, or change the
  date being viewed.

---

## Changed Behavior

- **System Health page**: Previously ended with the control-group comparison. Now also shows a
  "Return attribution" section below it for the selected horizon.
- **Backtest page**: Previously ended with the forward-test scorecard table. Now also shows a
  "Return attribution" section (with its own horizon view selector) below the scorecard, for the same
  resolved as-of date.
- The data served by `GET /api/system-health` and `GET /api/backtest` now carries an additional
  `attribution` block. No existing field in either response changed.

---

## Backend-Only Items

- None. Every new piece of data (the four attribution slices) is surfaced in the UI on both pages.

---

## Incomplete Items

- None. Every item in the phase spec's "In Scope" and "Definition of Done" is implemented:
  the config block + typed accessor, the single shared engine helper wired into both engine payloads,
  the frontend types, the shared four-panel component, and its placement on both pages with honest
  empty / NA states.
- The other failing journey, **J-17 Data Manager**, was explicitly out of scope and is untouched.

---

## Config and Environment Changes

- `config.yaml` → new `walk_forward.attribution` block (no environment variables):
  - `top_contributors_k` — how many contributors / detractors to list per side — default: `5`.
  - `rank_bands` — the ordered rank bands a stock's rank is grouped into — default:
    `1–10`, `11–50`, `51+` (the last band open-ended). The band edges and the list size live in config,
    not in code, so they can be re-tuned without a code change.
- No database, migration, or secret changes. The attribution figures are derived entirely from data
  already stored by earlier iterations (the per-observation forward returns joined to the immutable
  scan snapshots) — nothing new is fetched, fabricated, or recomputed.

---

## Known Limitations

- **Attribution is only as deep as the elapsed forward window.** For a recent as-of date whose forward
  window has not yet elapsed in the frozen seed, the panels honestly show "—" (NA) with a sample size
  of 0 — no number is invented to fill the gap. Pick an older date (≥ ~60 post-snapshot trading days)
  on Backtest to see fully populated panels.
- **Small samples are flagged, not hidden.** Any figure whose sample size is below the configured
  minimum (`walk_forward.min_sample`, currently 30) is shown with the standard "⚠" low-sample marker;
  it is still displayed (with its n) rather than suppressed, consistent with the rest of the evidence.
- **On Backtest, the distribution mean is over the full observed set at that horizon, not the
  top-ranked cohort** shown in the scorecard table above it. The two means therefore need not match —
  the scorecard headline is the rank ≤ top-N cohort, while the distribution describes every observed
  name at that horizon. (On System Health the distribution mean does equal the page's overall mean.)
- **Contributors and detractors can overlap when very few names are observed.** With fewer names than
  the list size, the same name can appear on both sides (sorted opposite ways). This is the honest
  reading of a tiny sample, not a bug.
