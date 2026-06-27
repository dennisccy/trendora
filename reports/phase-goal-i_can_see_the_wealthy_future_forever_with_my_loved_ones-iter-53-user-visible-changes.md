# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-53 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-53
**Date:** 2026-06-27
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now open the **Regime Lab** by clicking the new "Regime Lab" tile (Gauge icon) on the Research hub at `/research`, then arriving at `/research/regime-lab` in two clicks from the nav.
- Users can now view a by-regime-label summary table showing mean realized forward returns and paired mean max-drawdown for each of the six market regime labels (e.g. Risk-on, Risk-off) at 1/5/10/20/60-day horizons.
- Users can now view a by-regime-score-decile table (D1–D10) showing forward returns and max-drawdown per horizon per decile, with each decile's regime-score range displayed, letting them see whether high vs. low regime scores historically preceded better or worse returns.
- Users can now check the **rank-IC** (rank information coefficient of regime score vs. forward return) per horizon, shown as a header row above the decile table.
- Users can now **sort any column** in either table — clicking a column header sorts NA-last in ascending order; clicking again reverses to descending — without any page reload.
- Users can now **filter observations to a point-in-time** by toggling the As-of / All-history control: the observation count (n) displayed in each cell decreases when As-of mode is active, reflecting only data available at the selected global as-of date.
- Users can now **drill into any bucket's underlying observations** by clicking the `N=` chip on any return cell; `/research/samples` opens in a new tab pre-filtered to the exact (regime label or regime-score decile, horizon) cohort, and the Samples page "Total observations" count matches the clicked n.

---

## What Changed in the Visible UI

- A new **"Regime Lab"** tile with a Gauge icon appears on the `/research` hub page alongside the existing lab tiles (Factor Lab, Event Study, etc.).
- A new page `/research/regime-lab` is accessible, containing:
  - A page title and descriptive-evidence subtitle explaining the survivorship-bias caveat.
  - A **survivorship-bias / descriptive-evidence caveat banner** (`ResearchCaveat`) at the top.
  - A **by-regime-label table** with 6 rows (one per canonical regime label), with paired forward-return and max-drawdown columns per horizon and a count `N=` chip on each return cell.
  - A **by-regime-score-decile table** with D1–D10 rows, a Rank-IC header row, score-range column, paired (return, MDD) columns per horizon, and `N=` chips. Both tables scroll horizontally (`overflow-x-auto`) on narrow screens rather than dropping columns.
  - An **As-of / All-history toggle** (shared `ResearchControls` component). No second date picker or native `input[type=date]` is present on the page.
- Forward-return cells are colour-graded using the existing return design tokens; max-drawdown cells use the `lib/mdd-color` severity scale — consistent with the Factor Lab (iter-52).
- Loading, backend-unavailable, and empty states are handled with skeleton, error card, and empty-state components rather than blank or broken UI.

---

## What Old Behavior Changed

None. This iteration is purely additive. No existing pages, tables, forms, or navigation elements were removed or altered in behavior.

---

## Not Visible Yet

- The **Episodes view** (`GET /api/research/regime-lab?view=episodes`) is implemented and tested in the backend, but is intentionally not exposed on the frontend. The page always uses the pooled view (every stock × snapshot tagged by that snapshot's regime), which is the meaningful cross-sectional study. Users have no Episodes/Pooled toggle on this page.
