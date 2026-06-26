# Goal iter-52 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52
**Date:** 2026-06-26
**Written by:** developer

---

## Features Implemented

- **All-horizon Factor Lab (J-109)**: The Factor Lab page (`/research/factor-lab`) now shows every
  forward-return horizon (1, 5, 10, 20, 60 trading days) at the same time, instead of making the user
  pick one. The horizon dropdown is gone.
- **Edge AND downside side-by-side**: For each factor, the main table now shows the top-decile cohort's
  average forward return *and* its average max-drawdown (worst peak-to-trough decline) at every horizon —
  so a user sees the reward and the risk together at a glance.
- **Expandable per-factor decile grid**: Clicking any factor row opens its full ten-decile grid (D1 =
  lowest factor value … D10 = highest), again with the paired forward-return and max-drawdown figures at
  every horizon, plus the sample size for each bucket.
- **Drill into any cohort**: Every decile/horizon cell's "N=" chip opens the Research Samples page for that
  exact (factor, horizon, decile) group, and the count always matches the number shown on the chip.
- **Colour-graded risk**: Forward returns are coloured by sign; max-drawdowns are colour-graded by severity
  (a deeper drawdown reads more red), using the app's existing colour system.

---

## Changed Behavior

- **Factor Lab horizon control**: Previously the page showed one horizon at a time, chosen from a dropdown.
  Now it shows all horizons at once as paired return/drawdown columns; the dropdown is removed. The
  rank-IC and downside risk-adjusted figures are now always reported at the default horizon (20 days) and
  are labelled with it.
- **Factor decile data (everywhere it is read)**: Each factor decile now also carries a "mean max-drawdown"
  figure alongside its mean return. The single-factor Factor Lab API response gains this field too (purely
  additive — existing figures are byte-for-byte unchanged).

---

## Backend-Only Items

- None. Every new figure is surfaced in the UI.

---

## Incomplete Items

- None for J-109. The sibling labs J-110 (Regime Lab), J-111 (Phase & Severity Lab), and J-112
  (Regime × Phase × Factor) remain out of scope for this iteration (one heavy lab per iteration) and are
  deferred to later iterations.

---

## Config and Environment Changes

- None. No new environment variables, no schema migration, no new database table. The horizon list and
  default horizon are read from the existing `config.walk_forward` settings (no hardcoded numbers).
- Internal cache note (no operator action): the Factor Lab's cached result now carries a schema tag, so any
  result cached before this change is automatically recomputed once with the new columns and the stale entry
  is discarded.

---

## Known Limitations

- The all-factors table is wide (a forward-return column and a max-drawdown column for each of the five
  horizons, plus the default-horizon statistics). It scrolls sideways on narrow screens rather than hiding
  columns.
- In the expanded decile grid, the visible "Factor range" column shows the range at the default horizon;
  each horizon's own range (membership differs slightly per horizon) is available on hover over that
  horizon's return cell.
- A horizon (or decile) with too few qualifying observations, or with no stored drawdown, shows an honest
  "NA" plus the sample size — never a fabricated number.
- Live check: loading all horizons for all factors directly from the database (the heaviest, uncached case)
  took ~47 seconds and ~520 MB of memory on the current dataset (≈701k forward-return rows) — well within
  limits and with no out-of-memory error; repeat loads are served from cache in ~20 ms.
