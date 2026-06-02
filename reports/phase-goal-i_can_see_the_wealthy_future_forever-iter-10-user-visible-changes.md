# Phase goal-i_can_see_the_wealthy_future_forever-iter-10 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-10
**Date:** 2026-06-02
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now open the **Research** lab by clicking the new **Research** item in the left sidebar (between System Health and Watchlist), reaching the new `/research` page in ≤2 clicks.
- Users can now read a **decile table (D1…D10)** of mean forward return for any catalogued factor, where D1 holds the lowest factor values and D10 the highest — answering "does this factor sort future returns?" from stored, forward-tested evidence.
- Users can now read a **downside risk-adjusted column** beside each decile's raw mean return, so the top decile can be judged on a risk-adjusted basis (not just raw return). "Risk" is downside-deviation only — healthy upside moves are never penalized.
- Users can now read the factor's **rank-IC** (Spearman rank information coefficient) as a large signed number with a plain-language one-liner interpreting its sign, plus its sample size `n`.
- Users can now **select a factor** from a dropdown whose options come from the server's config-driven catalog (8 factors: `leadership_score`, `entry_quality_score`, `risk_score`, `rs_spy_3m`, `ma_stack`, `high_proximity`, `up_down_vol`, `atr_pct`).
- Users can now **select a forward horizon** from a button group (1d / 5d / 10d / 20d / 60d) built from the server's `horizons` list; changing the factor or horizon re-points the decile table and rank-IC to the server's values.
- Users can now see the **sample size `n`** on every decile cell and on the rank-IC, and read the **survivorship-bias / universe-relative / descriptive-not-predictive** caveat banner stating the evidence is honest and not a predictive model.

---

## What Changed in the Visible UI

- A new **"Research"** link (Microscope icon) was added to the left sidebar, placed between "System Health" and "Watchlist".
- A new page at **`/research`** (Research — Factor Lab) was added, modeled on the System Health analytical-workstation layout (dark theme, `tabular-nums` figures, colour-graded returns).
- The page header shows the title/subtitle plus a **factor dropdown** (`data-testid="factor-select"`) and a **horizon button group** (`data-testid="horizon-select"`).
- A **caveat banner** (warning-coloured) shows the survivorship-bias label and the descriptive/universe-relative caveat, rendered verbatim from the server payload.
- A **decile table** with columns: Decile (D1…D10), Factor range, Mean fwd return (raw, %), and Risk-adjusted (downside, unitless ratio) — each value colour-graded by sign with its `n`.
- A **Rank-IC card** showing the signed Spearman rank-IC as a large number with `n` and a sign-interpretation sentence.
- Low-sample (`n < min_sample`) or empty decile cells render an explicit **"NA"** plus the `n` — never blank and never a fabricated number.
- **Loading** (skeleton), **empty** (`n_total === 0` EmptyState), and **error** ("Backend unavailable", no fabricated figures) states are styled consistently with System Health.

---

## What Old Behavior Changed

- **Sidebar navigation:** the sidebar now has 11 items instead of 10 (the new "Research" entry). All existing entries and their order are unchanged; this is purely additive.

No existing page's contract or behavior changed. No scoring, regime, setup, pattern, snapshot, watchlist, or date-control path was touched, and no existing endpoint payload changed.

---

## Not Visible Yet

- **NA / low-sample decile rendering is not observable on the committed seed.** Every catalogued factor has ~1218 observations (~121 per decile) at every horizon, all well above `min_sample=30`, so no decile renders NA by switching factor/horizon on this data. The NA path is real and unit-tested on the backend; it simply is not triggered by the current seed (this is correct, honest behavior — not a gap to flag).
- **The `/research` home currently contains only the Factor Lab.** The read-only lab-analytics seam (`app.engine.research`) is designed to grow, but the later labs — J-26 (multi-factor combination cohorts), J-27 (regime-conditioned effectiveness), J-29 (event study: expectancy/MAE/MFE), J-30 (full volatility family), J-31 (synthesis) — are out of scope this iteration and have no UI yet.
