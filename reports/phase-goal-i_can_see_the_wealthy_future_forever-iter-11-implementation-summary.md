# Goal Iteration 11 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-11
**Date:** 2026-06-02
**Written by:** developer

---

## Features Implemented

- **Factor effectiveness by market regime (Factor Lab, `/research`)**: On the Research page, after you
  pick a factor and a forward horizon, a new table now shows — *for each market regime* — whether that
  factor actually sorts future returns within that regime. Each row reports the number of observations
  in the regime (`n`), the rank correlation (rank-IC), the average return of the top and bottom factor
  groups, and the "long-short" spread between them, shown both raw and downside-risk-adjusted. This lets
  you see when a factor that looks useful overall is really only working in certain market conditions
  (for example, strong in Risk-on but weak or absent in Risk-off).

---

## Changed Behavior

- **Research — Factor Lab page**: Previously it showed only the pooled (all-dates-combined) decile table
  and a single rank-IC for the whole sample. Now, below those, it additionally breaks the same evidence
  down by market regime. The original decile table and rank-IC are unchanged.

<!-- No other existing behavior changed. -->

---

## Backend-Only Items

<!-- None. The new backend calculation is fully wired to the new UI panel on /research. -->

- None — the new `by_regime` data is displayed in the new Research-page table.

---

## Incomplete Items

<!-- None. Every item in the iter-11 spec's Definition of Done is implemented. -->

- None for this iteration's scope (J-27). The broader Research lab still has planned future tables that
  were intentionally **out of scope** here: multi-factor combination cohorts (J-26), the event-study /
  drawdown-vs-runup view (J-29), the full volatility family (J-30), and the synthesis view (J-31).
  Three external-data journeys (J-22/J-23/J-24) remain blocked by a third-party data-provider rate limit
  and were not attempted, per the spec.

---

## Config and Environment Changes

<!-- None. -->

- None. No new configuration keys, environment variables, database changes, or migrations. The new table
  reuses existing settings: the regime labels, the low-sample threshold, and the decile count all come
  from the existing configuration file, and the market-regime label for each day is read exactly as it
  was already stored — nothing is recomputed.

---

## Known Limitations

- **Some regimes legitimately show "NA".** When a regime has too few observations (below the configured
  minimum sample), or when there is no downside in a group to risk-adjust against, the cell shows "NA"
  alongside the honest sample count rather than a made-up number. With the current frozen dataset, the
  "Strong risk-on" and "Defensive" regimes have no qualifying days, so they correctly appear as empty
  (n = 0, NA) — this is honest reporting, not a defect.
- **The evidence is descriptive, not predictive, and carries survivorship bias.** This is the same honest
  caveat already shown on the Research page; the regime breakdown inherits it. The numbers describe what
  happened historically on a current-membership universe — they are not a forecast.
- **Per-regime numbers do not "add up" to the pooled numbers**, and that is expected: each regime is a
  different subset of days, so its average return legitimately differs from the overall average. The only
  thing that reconciles across regimes is the sample counts — they sum to the page's total observation
  count (verified by an automated test).
