# Goal Iteration 18 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-18
**Date:** 2026-06-04
**Written by:** developer

---

## Features Implemented

- **Combined (composite rank-blend) cohort (J-26 headline)**: On the Factor Lab (`/research` → "Multi-factor
  combination cohort"), the headline **Combined** cohort is now a *composite percentile-rank blend* of the
  selected factors instead of the old strict AND-intersection. Each condition's stored factor value is
  percentile-ranked within the shared observation pool, oriented by the chosen Top/Bottom side, averaged
  with config weights (equal-weight by default), and the top config-quantile of that blend is the cohort.
  For a sensible selection it is **populated** (non-empty and clears the 30-observation min-sample
  threshold) instead of perpetually NA — so "does combining factors beat either alone?" is finally
  answerable. On the real seed the default two-factor selection yields a composite cohort of ~244
  observations.
- **Strict overlap (AND) secondary cohort**: The previous exact AND-intersection is retained as a clearly
  labelled *secondary* row beside the composite — it honestly shows **NA + n** when the intersection is
  empty (e.g. many factors, or opposing extremes of one factor), never a fabricated 0.
- **Combine up to all catalog factors**: The condition cap is raised from 3 to 11 (the number of catalog
  factors), config-driven. A user can now add conditions up to every catalog factor; the composite cohort
  stays non-empty across the whole catalog.
- **Transparent blend labelling**: The payload echoes the resolved composite quantile (e.g. "Quintile
  (20%)") and the weighting scheme ("equal") so the UI labels the blend honestly — it is described as a
  transparent ranking of stored values, explicitly *not* a fitted/ML model.

---

## Changed Behavior

- **"Multi-factor combination cohort" section on `/research`**: Previously the headline **Combined (AND)**
  row was the exact set-intersection of the conditions, which was usually 0/NA (especially for 3+ factors).
  Now the headline **Combined (composite rank-blend)** row is the populated composite cohort, and the exact
  intersection is demoted to a secondary **Strict overlap (AND)** row. Row order is Baseline → each single
  factor → Combined (composite) → Strict overlap (AND).
- **`GET /api/research/factor-combination` payload**: The `combined` key is **removed** and replaced by
  `composite` + `strict_overlap` cohorts, plus echoed `composite_quantile` and `weighting` metadata. The
  request signature is unchanged (`condition` repeatable + `horizon`). The condition-count limit it accepts
  rose from 3 to 11 (config-driven).
- **Config `research.factor_lab.combination`**: `max_conditions` raised 3 → 11; a new required `composite`
  sub-block (`quantile` + `weighting`) added.

---

## Backend-Only Items

- None. Every backend change (composite cohort, strict-overlap secondary, echoed metadata, raised cap) is
  wired through to the `/research` UI in the same iteration.

---

## Incomplete Items

- None deferred from this iteration's spec. Explicitly **out of scope** (and not started, per spec):
  J-32 / any as-of/date state on `/research` (that is iter-19); request-level custom per-condition weights
  (the config equal-weight default is the must); boolean pattern-flag conditions; return/MAE risk-adjustment
  in the combination cohort.

---

## Config and Environment Changes

- `config.yaml` → `research.factor_lab.combination.max_conditions`: **3 → 11** (= the catalog factor count;
  the cap lives in config, not code, so it scales if the catalog grows).
- `config.yaml` → `research.factor_lab.combination.composite` (**new, required**):
  - `quantile: quintile` — the top fraction of the composite-score-sorted pool taken as the Combined cohort
    (must be a real `quantiles` key; validated loudly at boot).
  - `weighting: { scheme: equal, default_weight: 1.0 }` — the config-declared blend weighting; each
    condition's oriented percentile rank is weighted by `default_weight`, normalized to sum to 1 (so no
    `1/k` weight literal lives in calculation code). `default_weight` must be `> 0`.
- No environment variable, database schema, or migration changes. No DB regeneration — the scoring/snapshot
  path is byte-identical (J-06/J-07 unaffected).

---

## Known Limitations

- The composite blend is **descriptive, not predictive**. It is a deterministic ranking/grouping of stored
  factor values (the same read-only class as the J-25 decile sort) — it recomputes no factor and no return,
  and it is **not** a fitted/learned/ML model. Read it as historical association, never a forecast. The
  survivorship-bias and "descriptive, not predictive" labels persist on the payload and page.
- For a *contradictory* selection (e.g. the Top **and** Bottom quintile of the same factor), the two
  opposing oriented ranks average to a flat blend, so the composite honestly selects the whole pool (no
  differentiating signal) rather than collapsing to NA. This is the correct, transparent behavior — and it
  is precisely the case where the strict-overlap intersection is empty (NA + n).
- "Risk-adjusted" in this section remains **downside-deviation only** (mean ÷ downside deviation; NA when
  there is no downside or n < 2) — never total volatility. return/MAE and MAE/MFE excursion ratios live in
  the Setup & Pattern event study (J-29), not here.
- Evidence is universe-relative and survivorship-biased to the current seed membership (carried as an
  explicit caveat).
