# Goal Iteration 12 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-12
**Date:** 2026-06-02
**Written by:** developer

---

## Features Implemented

- **Multi-factor combination cohorts on the Factor Lab (J-26)**: On the Research page (`/research`), a
  new "Multi-factor combination cohort" section lets the user combine **2–3 factor conditions** — each a
  catalogued factor (e.g. *Relative strength vs SPY (3m)*, *ATR %*) at its **Top** or **Bottom**
  **quantile** (Quintile / Quartile / Tertile / Half) — and read whether **combining** those signals adds
  value. The section shows a comparison table of the **unconditional baseline (all names)**, **each single
  condition's cohort**, and the **combined (AND) cohort** side by side, each with **sample size (n)**,
  **mean** and **median forward return**, **hit-rate (% of names positive)**, and a **downside
  risk-adjusted** figure.
- **Compose / adjust the cohort interactively**: pick a factor, a side (Top/Bottom), and a quantile for
  each condition; **Add condition** (up to 3) or **Remove** a condition (down to 2); change the page's
  shared horizon — every change re-points the table from freshly fetched server values.
- **Honest small-sample handling**: when the combined cohort is too thin (fewer observations than the
  configured minimum) or empty, its figures show **"NA" with the honest n** instead of a fabricated
  number. A combined cohort smaller than each single cohort is the expected, visible sign that combining
  the factors narrows the population (the "interaction" effect the lab exists to surface).

---

## Changed Behavior

- **Research page (`/research`)**: Previously showed only the single-factor decile table, rank-IC, and the
  by-regime effectiveness table. Now it **additionally** shows the Multi-factor combination cohort section
  below the regime table. Everything that was there before is unchanged.

<!-- No other existing behavior changed — the iteration is strictly additive. -->

---

## Backend-Only Items

<!-- None — the new value is fully wired to the UI. -->

- None. The new `GET /api/research/factor-combination` endpoint is fully surfaced in the `/research` UI.

---

## Incomplete Items

- **return/MAE and MAE/MFE excursion measures** are intentionally **not** part of this iteration's
  risk-adjusted column. They need a post-snapshot daily high/low excursion path that is a later
  iteration's deliverable (the event-study lab, J-29). The combination section uses the established
  **downside-deviation** risk-adjusted measure and states this in the UI so it is not mistaken for "all"
  risk measures.
- **Boolean pattern-flag conditions** (e.g. "… AND VCP-flagged") are out of scope this iteration;
  conditions are catalog-factor top/bottom quantiles only. The condition model is left extensible for a
  later follow-on.

---

## Config and Environment Changes

- `config.yaml` → **`research.factor_lab.combination`** (new block; no existing tunable changed):
  - `min_conditions: 2`, `max_conditions: 3` — how many conditions a combination may have.
  - `quantiles:` the Top/Bottom tail vocabulary the dropdown offers — `quintile (20%)`, `quartile (25%)`,
    `tertile (33%)`, `half (50%)`. Adding/removing a quantile here changes the dropdown with no code edit.
  - `default_conditions:` the 2-condition combination shown on first load (RS vs SPY 3m top-quintile AND
    ATR% bottom-tertile).
  - The low-sample threshold is **reused** from the existing `walk_forward.min_sample` (no new threshold).
- No environment variables, secrets, or database/schema changes. The feature reads only already-stored
  data; nothing new is persisted.

---

## Known Limitations

- The combined cohort is the strict **AND-intersection** of the single-condition cohorts, so it can become
  small quickly (especially with three conditions or opposing extremes). This is by design and is shown
  honestly as **NA + n** below the minimum-sample threshold — it is never padded with a fabricated number.
- The quantile cutoff uses a deterministic **nearest-rank** rule with boundary ties included, so a Top/
  Bottom cohort may be marginally larger than the nominal fraction (e.g. a "top 20%" cohort on a small
  pool can include one extra boundary name). This is the documented, honest behavior of an empirical
  cutoff on a finite sample.
- The risk-adjusted column is **downside-deviation only** (mean ÷ downside deviation) and is shown as
  "NA" for a cohort with no losing observations (no downside risk) or fewer than two observations — never
  a total-volatility number that would penalise healthy upside.
- Like the rest of the Factor Lab, the section is a **cross-date aggregate** carrying the survivorship-bias
  / universe-relative / descriptive (not predictive) caveats; it is **not** affected by the global as-of
  date control.
