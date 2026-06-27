# Goal iter-55 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-55
**Date:** 2026-06-27
**Written by:** developer

---

## Features Implemented

- **Regime × Phase × Factor lab (J-112)**: A new Research lab at `/research/regime-phase-factor`. The
  operator picks a factor and sees a ranked, sortable, filterable, paginated table showing — for every
  `(regime-score decile × severity-score decile × factor decile)` combination — how stocks' realized forward
  returns and paired downside risk (max-drawdown) differed, at all five horizons (1/5/10/20/60 days) at once.
  This is the last unbuilt buildable Must-have.
- **Factor selector**: A dropdown (from the existing factor catalog) that re-queries the table for the chosen
  factor.
- **Three decile filters**: "Regime decile", "Severity decile" and "Factor decile" dropdowns (each defaulting
  to "All") narrow the displayed rows without re-fetching.
- **Column sorting**: Every column (the three decile coordinates and each horizon's forward-return /
  max-drawdown) is click-to-sort; combinations with no/low data always sink to the bottom ("NA-last").
- **Pagination**: 30 rows per page (the value comes from config), with Prev/Next controls and a page
  indicator. Pure client-side paging — no re-fetch.
- **As-of toggle**: The existing "All history / As of date" toggle filters the evidence to snapshots on or
  before the single global as-of date — it shrinks the sample counts, it never adds a second date control.
- **Count-coherent drill-downs**: Each combination's `N=` chip opens Research Samples in a new tab showing the
  exact underlying observations; the Samples "Total observations" equals the chip's number.
- **New hub tile**: A "Regime × Phase × Factor" tile on the `/research` hub links to the new lab.

---

## Changed Behavior

- **Research hub** (`/research`): now lists one additional lab tile (Regime × Phase × Factor). No existing
  tile or lab changed.
- **Research Samples** (`/research/samples`): now also describes the new `regime-phase-factor` cohort kind
  when opened from the new lab. Existing cohort kinds are unchanged.

---

## Backend-Only Items

- None. Every backend capability added this iteration (the new endpoint, the new cached study kind, and the
  new samples cohort kind) is wired to the new UI.

---

## Incomplete Items

- None. All in-scope spec items (engine study + cache, read-only endpoint, samples cohort, frontend page +
  tile + selector + filters + sort + pagination + As-of + N= chips) are implemented and tested.

---

## Config and Environment Changes

- `research.regime_phase_factor_page_size` — the rows-per-page of the new lab's table — default: `30`. Added to
  both the config model and `config.yaml`. It is served in the lab payload so the frontend reads it from
  config (no hard-coded `30` in the engine or component). No database migration; no new table (the existing
  `event_study_cache` table is reused for the new cached study kind).

---

## Known Limitations

- **Descriptive, survivorship-biased evidence only.** Like its sibling labs, this is historical association on
  the current-membership universe — it is explicitly NOT a forecast or a fitted model, and the survivorship /
  descriptive caveats are shown on the page.
- **Sparse three-way grid.** The interaction can emit up to ~1000 combinations per factor; most are
  low-sample. Combinations below the config minimum sample (`walk_forward.min_sample`, currently 30) show
  "NA + n" rather than a fabricated number, and the table paginates so the page never renders all of them at
  once.
- **Pinned to the pooled view.** Because this studies the whole cross-section (every stock × snapshot), the
  first-trigger "episodes" collapse would degenerate; the lab pins the pooled view (both the table fetch and
  every drill-down) and exposes no Episodes/Pooled toggle. The backend still serves and unit-proves both
  views.
- **Read-only.** The lab recomputes nothing — it reads the stored regime score, the served market-phase
  severity, the stored factor value, and the stored forward return / max-drawdown verbatim from their single
  canonical sources.
