# Phase goal-i_can_see_the_wealthy_future_forever-iter-11 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-11
**Date:** 2026-06-02
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On the Factor Lab (`/research`), users can now see whether a chosen factor still sorts forward returns **within each market regime** — not just overall. A new "Factor effectiveness by market regime" table appears below the existing decile table and rank-IC card.
- Users can read, for each configured regime (Strong risk-on, Risk-on, Narrow leadership, Choppy, Defensive, Risk-off), that regime's sample size `n`, its rank-IC, the top-decile mean, the bottom-decile mean, the raw long-short spread (top − bottom decile), and the downside-risk-adjusted spread — all on one row.
- Users can change the **Factor** dropdown or the **Horizon** selector and watch the regime table re-point (its rank-IC and spread values update) alongside the existing decile table — using the controls that already exist on the page (no new control was added).
- Users can spot a factor that "works overall" but is actually regime-dependent — e.g. a factor with a positive pooled rank-IC that shows a weak or negative rank-IC / spread in a specific regime row.

---

## What Changed in the Visible UI

- The `/research` Factor Lab page now shows a new "Factor effectiveness by market regime" panel (a `Card` with a dense numeric table) below the existing decile table + rank-IC grid.
- The new table has seven columns: **Regime · n · Rank-IC · Top-decile mean · Bottom-decile mean · Spread (top − bottom) · Risk-adjusted spread**.
- The table renders one row per configured regime label, driven entirely by the server payload (`by_regime`), so the regime list always matches the backend config.
- Regimes that lack enough samples (`n < min_sample`) or that have no downside risk render **"NA"** (muted) in the affected value cells, while the honest sample size `n` is still shown in the `n` column via the existing sample-size chip. No fabricated numbers are shown.

---

## What Old Behavior Changed

- None. The change is purely additive. The existing decile table, rank-IC card, factor/horizon selectors, loading skeleton, empty state (`n_total === 0`), and error card on `/research` are unchanged and still gate the new panel (the panel only renders when factor-lab data is present).
- No date control was added to `/research`; the page still ignores the global as-of switcher (J-18 preserved).

---

## Not Visible Yet

- None new from this phase. The `by_regime` data rides the same existing `GET /api/research/factor-lab` response and is fully surfaced in the new table. (Separate `/research` labs J-26, J-29, J-30, J-31 remain unbuilt and are out of scope for this iteration; J-22/J-23/J-24 remain externally data-walled.)
