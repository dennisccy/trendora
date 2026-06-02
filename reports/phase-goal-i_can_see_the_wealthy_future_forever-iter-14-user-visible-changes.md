# Phase goal-i_can_see_the_wealthy_future_forever-iter-14 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-14
**Date:** 2026-06-02
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now run a **Setup & Pattern Lab event study** by going to `/research`, scrolling to the new "Setup & Pattern Lab — event study" section (below the Factor Lab and the Multi-factor Combination Lab), and picking a subject from the **Subject** selector.
- Users can now pick **any setup** (Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist) or **any detected pattern** (VCP, Pullback-to-a-rising-DMA, Flat-base) from a single grouped **Subject** dropdown (Setups group vs Patterns group) and see that subject's pooled, cross-snapshot forward-return evidence.
- Users can now read, **per forward horizon**, the forward-return distribution (mean, median, % positive / hit-rate, dispersion), the per-occurrence **expectancy**, the **mean MAE** (max adverse excursion) and **mean MFE** (max favorable excursion), and two **downside-only risk-adjusted ratios** (return ÷ downside-deviation and return ÷ mean-|MAE|), all shown beside the raw mean, with sample size `n` on every row.
- Users can now see the **best exit-horizon** highlighted in the per-horizon table (the horizon that maximizes the downside risk-adjusted metric among non-low-sample horizons), reading the per-horizon curve directly.
- Users can now read how a subject behaves **by market regime** (one row per configured regime label) and **by sector** (one row per sector with members) for the currently selected horizon.
- Users can now re-point the whole event study to a different forward horizon using the page's existing shared **Horizon** selector (the by-regime / by-sector panels follow the selected horizon).

---

## What Changed in the Visible UI

- The `/research` page gains a **third lab section**: "Setup & Pattern Lab — event study", rendered below the Factor Lab and the Multi-factor Combination Lab. No new page, route, or nav entry was added.
- A new **Subject** `<select>` appears in that section, grouped into "Setups" and "Patterns" `<optgroup>`s, built entirely from the API payload's subject catalog (config-driven — no hard-coded list).
- A new **per-horizon distribution / exit-horizon table** appears (columns: Mean, Median, % Positive, Dispersion, Expectancy, Mean MAE, Mean MFE, Return ÷ downside-dev, Return ÷ MAE, n). The best-exit-horizon row is highlighted with a "best exit" badge; low-sample rows render literal "NA" with an `n` chip.
- A new **By market regime** panel appears (n / mean / hit-rate / downside risk-adjusted per regime label; empty or low-sample regimes show NA + n).
- A new **By sector** panel appears (n / mean / downside risk-adjusted per sector with members; empty slice shows an honest note).
- The shared **CaveatBanner** (survivorship-bias + descriptive "not predictive" labels) now also renders inside this new section.
- The Multi-factor Combination Lab's footnote text was updated (it previously referenced being the last/most-recent lab; now corrected for the added section).

---

## What Old Behavior Changed

- **Stored forward returns now also carry MAE/MFE.** The append-only `forward_returns` table gained two new per-(run, symbol, horizon) columns (max adverse / max favorable excursion). This is not directly shown on any existing page (System Health, Backtest, Stock Detail, leaderboard are unchanged) — it surfaces only through the new event study. Existing aggregates that read `realized_return` (System Health by-bucket/setup/regime/VCP, the Backtest scorecard) are unaffected.
- **The local DB was regenerated** from the committed seed so existing rows carry the new MAE/MFE columns. Because the scoring/snapshot path is untouched, snapshots regenerate byte-identical — no user-visible change to scores, buckets, setups, or the Risk-Off gate is expected. Re-verify J-06 (NVDA scores byte-identical leaderboard↔detail) and J-07 (Risk-Off → Actionable = 0) as criticals after the regen.

---

## Not Visible Yet

- The per-(run, symbol, horizon) **MAE/MFE excursion values** are stored but are **not surfaced on existing pages** (Stock Detail, System Health, Backtest). They are exposed to users **only** in aggregated form through the new event study — there is no raw per-row MAE/MFE display, by design.
- Note for QA: the **default** subject on first load is **Actionable**, a genuinely rare setup with only ~2 historical occurrences in this seed, so the default view honestly renders **NA + n=2** rather than numbers. This is correct low-sample behavior, not a missing-UI gap. To see populated figures, select a data-rich subject (e.g. **Breakout-watch** in Setups, or **Pullback to a rising DMA** in Patterns).
