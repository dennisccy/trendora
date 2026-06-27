# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-54 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-54
**Date:** 2026-06-27
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Open the **Market Phase & Severity Lab** by navigating to `/research` (Research hub) and clicking the new "Market Phase & Severity Lab" tile (Thermometer icon).
- View how stocks' realized forward returns and paired max-drawdowns have differed across the five market-phase labels (Expansion, Recovery, Pullback, Correction, Bear) at 1, 5, 10, 20, and 60-day horizons — all in a single table with colour-graded cells.
- View how returns and drawdowns differ across ten severity-score deciles (D1 = lowest stress to D10 = highest stress), including each decile's severity-score range and a per-horizon Rank-IC (how well the severity score ordered forward returns).
- Sort any numeric column in either direction by clicking the column header; cells with insufficient data are always sorted last.
- Toggle between All-history and As-of (using the single global as-of date) to filter the evidence to a historical point in time — the displayed observation counts shrink to reflect only the qualifying history.
- Click any **N=** chip in either table to open the exact underlying observations in Research Samples in a new browser tab; the "Total observations" count on the Samples page matches the number shown on the chip.

---

## What Changed in the Visible UI

- The `/research` hub page now includes a **"Market Phase & Severity Lab"** tile (Thermometer icon) alongside the existing lab tiles.
- A new page `/research/phase-severity-lab` is now accessible. It shows:
  - A **by-phase-label table** with five rows (one per market-phase label) and, per horizon, a paired mean forward-return cell + mean max-drawdown cell + an `N=` drill chip.
  - A **by-severity-decile table** with a header Rank-IC row followed by rows D1–D10. Each row shows the decile's severity-score range plus the same per-horizon paired columns. The Rank-IC row shows the correlation of the severity score with forward returns at each horizon.
  - Colour-graded return cells (green-to-red scale) and max-drawdown cells (colour-coded via the shared `mddClass` tokens) throughout both tables.
  - An explicit "NA" display (never a fabricated number) for thin buckets, zero-count buckets, and near-latest horizons where fewer observations are available.
  - A survivorship-bias / descriptive-evidence caveat in the page header (rendered server-side).
  - Loading, warming, error, and backend-unavailable states.

---

## What Old Behavior Changed

- **Research Samples cohort header for Regime Lab drill-downs**: When a user clicked an `N=` chip in the Regime Lab and landed on the Samples page, the cohort header previously fell through to a generic "Setup & Pattern Lab" label. It now correctly identifies the cohort as originating from the Regime Lab. No observation counts or data changed — only the displayed cohort title.

---

## Not Visible Yet

- The backend serves both **Episodes** and **Pooled** views of the phase-severity lab and both are unit-tested. The frontend intentionally exposes only the Pooled view and provides no Episodes/Pooled toggle. This is a deliberate design constraint (Episodes degenerates for a whole-cross-section study), not an implementation gap.
