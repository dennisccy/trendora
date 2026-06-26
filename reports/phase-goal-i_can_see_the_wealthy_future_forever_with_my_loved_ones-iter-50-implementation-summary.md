# Goal iter-50 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50
**Date:** 2026-06-26
**Written by:** developer

---

## Features Implemented

- **Factor Lab "all factors at once" table (J-107)**: The Research → Factor Lab page now shows every factor
  in the catalog on one screen — each row is a factor with its market "family", its predictive-edge score
  (rank-IC) and how many observations back it (N), and a downside-risk-adjusted return figure — instead of
  forcing the user to pick one factor at a time from a dropdown.
- **Sort any column (best-first, blanks last)**: Clicking a column header re-orders the table instantly
  (for example, sort by rank-IC to see the factors that best sort future returns first). Factors with too
  few samples to report a value always sink to the bottom rather than masquerading as zero.
- **Expand a factor in place**: Clicking a factor row (or pressing Enter/Space on it) expands it to reveal
  that factor's full decile sort — the same 10-bucket table the old single-factor view showed — and clicking
  again collapses it.
- **Drill into the evidence**: Inside an expanded factor, each decile's "N=" chip still opens the underlying
  observations in the Research Samples view in a new browser tab, with a count that matches the published N.
- **Faster, consistent figures**: The whole table is computed once and cached, and every number is exactly
  the same as the old per-factor view (the page never recalculates anything — it only re-displays).

---

## Changed Behavior

- **Research → Factor Lab page**: Previously a single-factor dropdown that loaded one factor's decile table,
  rank-IC card, and a per-market-regime effectiveness table. Now an all-factors comparison table where each
  factor expands in place to its decile table. The factor dropdown and the per-regime effectiveness table
  are no longer shown on this page. The horizon selector and the "All history / As of date" mode toggle are
  unchanged.
- **`GET /api/research/factor-lab`**: Previously always returned one factor's analysis. Now accepts an
  optional `all=true` flag that returns the all-factors block instead. Without the flag the endpoint behaves
  exactly as before (the single-factor analysis the Research Samples drill-downs rely on is untouched).

---

## Backend-Only Items

- None — the all-factors aggregate is fully wired into the Factor Lab page.

---

## Incomplete Items

- None — all in-scope spec items are implemented: the all-factors aggregate, byte-identity with the
  single-factor view, the derived-once cache, the bounded streamed read, and the frontend table with
  sorting + expand + decile drill-downs.
- (Out of scope, unchanged as intended: the multi-factor Combination Lab; the per-regime effectiveness
  computation in the backend; the data-walled journeys J-22/J-23/J-24.)

---

## Config and Environment Changes

- None. No new environment variables, no config keys, no database migration, and no new database table (the
  all-factors result reuses the existing event-study cache table under a reserved key).

---

## Known Limitations

- **The "Risk-adjusted (downside)" column is the factor's top-decile figure.** It shows the downside
  risk-adjusted return of the names with the highest value of that factor (re-displayed from the factor's
  own decile table — not a newly computed number). The direction of the factor (higher-is-better vs
  lower-is-better) is conveyed by the rank-IC's sign and a small hint next to the factor name, not by
  flipping to the bottom decile.
- **First paint after a data change is a cold compute (~25 seconds on the live dataset).** The all-factors
  view scans the full forward-return history once, then caches the result so every later load (and every
  other horizon/as-of after its first) is instant. Allow time for that first compute before expecting the
  cache-fast experience.
- **As-of at the earliest date shows N = 0 honestly.** Restricting to the very oldest snapshot yields no
  completed forward returns yet, so the table honestly shows zero observations rather than a fabricated
  figure; pick a more recent as-of date to see populated, smaller-sample numbers.
- The full automated backend test suite is run asynchronously by the pipeline (per the iteration's
  green-suite gate); the developer verified the relevant research + guard test files (231 passed) plus a
  live end-to-end check on the real database.
