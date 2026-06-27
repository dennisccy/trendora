# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-55 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-55
**Date:** 2026-06-27
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now open the **Regime × Phase × Factor** lab by navigating to `/research` and clicking the new "Regime × Phase × Factor" tile (Boxes icon).
- Users can now pick any factor from a dropdown selector on the lab page to see how that factor's decile interacts with regime-score decile and market-severity decile.
- Users can now read a ranked combination table showing, for every `(regime-decile, severity-decile, factor-decile)` triple, the mean realized forward return and paired mean max-drawdown at the 1/5/10/20/60-day horizons — with sample size n shown alongside each figure.
- Users can now filter the table by regime decile, severity decile, or factor decile (each defaulting to "All") to narrow the visible combinations without reloading data.
- Users can now sort any column in the table in either direction; combinations with no qualifying samples (NA) always sink to the bottom regardless of sort direction.
- Users can now paginate through the combination table in 30-row pages using the prev/next pagination footer.
- Users can now toggle the **As-of vs All-history** switch to restrict the observation set to snapshots up to a historical date, causing the n values to decrease to reflect the narrowed window.
- Users can now click any **N= chip** on a combination row to open the exact `(regime-decile, severity-decile, factor-decile, horizon)` sample cohort in a new Research Samples tab, where the "Total observations" count matches the chip's n value.

---

## What Changed in the Visible UI

- The Research hub page (`/research`) now includes a new **"Regime × Phase × Factor"** tile (Boxes icon) with a one-line description, placed alongside the existing Regime Lab, Phase & Severity Lab, and other research tiles.
- A new page exists at `/research/regime-phase-factor`, accessible from the hub tile, displaying the full 3-way combination lab — factor selector, three decile filter dropdowns, the combination table, As-of toggle, and pagination footer.
- The survivorship-bias / descriptive-evidence caution banner is displayed on the new lab page, consistent with the sibling labs.
- The Research Samples page (`/research/samples`) now shows a meaningful cohort description when arriving from a Regime × Phase × Factor N= chip drill-down (e.g. listing the regime decile, severity decile, factor decile, and horizon of the cohort), rather than an unrecognised cohort label.

---

## What Old Behavior Changed

- None. This phase is entirely additive — no existing pages, components, or behaviors were modified. The Research hub, the sibling labs (Regime Lab, Phase & Severity Lab), the Stocks header, and the Dashboard panel all remain byte-identical to their previous state.

---

## Not Visible Yet

- The backend endpoint (`GET /api/research/regime-phase-factor`) accepts and serves an **Episodes** view in addition to the Pooled view, and the samples builder is structurally proven for both. The frontend is intentionally pinned to `view=pooled` and exposes no Episodes/Pooled toggle — the Episodes view is not accessible to users (the whole-cross-section episode collapse degenerates for this lab type).
