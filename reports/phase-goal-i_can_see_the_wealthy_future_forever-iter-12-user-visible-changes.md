# Phase goal-i_can_see_the_wealthy_future_forever-iter-12 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-12
**Date:** 2026-06-02
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now build a **2–3 factor combination cohort** on the Factor Lab (`/research`) in the new "Multi-factor combination cohort" section, found below the regime-effectiveness table.
- For each condition, users can pick a **factor** (from a dropdown), a **side** (Top / Bottom segmented toggle), and a **quantile** (e.g. quintile / quartile / tertile / half — from a dropdown). The factor and quantile lists are server-driven, so they always match the live catalog.
- Users can **add a condition** ("+ Add condition", disabled once 3 conditions exist) and **remove a condition** (per-row Remove, disabled once only 2 remain).
- Users can read a **comparison table** showing the unconditional **Baseline (all names)**, one row per **single condition**, and the **Combined (AND)** cohort — each with sample size (n), mean forward return, median, hit-rate (% positive), and downside-risk-adjusted return — so they can see whether combining factors beats either factor alone.
- Users can change the page's shared **horizon** selector and the combination table re-points along with the existing decile/IC and regime tables.
- Users see an honest **NA + n** in any cohort cell that is low-sample (n below the configured minimum), empty, or otherwise undefined — never a fabricated number; a deliberately thin combined cohort (e.g. opposing extremes) shows NA + n.

---

## What Changed in the Visible UI

- The `/research` Factor Lab page now has a new **"Multi-factor combination cohort"** Card section appended below the regime-effectiveness table (`data-testid="combination-section"`).
- The section shows **2–3 condition control rows**, each with a Factor `<Select>`, a Top/Bottom side toggle, and a Quantile `<Select>`, plus an "+ Add condition" button and per-row Remove buttons.
- A new **comparison table** (`data-testid="combination-table"`) renders rows for Baseline, each single condition (labelled e.g. "Relative strength vs SPY (3m) · top Quintile (20%)"), and the visually-emphasised Combined (AND) row; columns are Cohort / n / Mean fwd return / Median / Hit-rate / Risk-adjusted (downside).
- A short **honest scope note** appears under the table stating the risk-adjusted column is downside-deviation only and that return/MAE and MAE/MFE excursion measures arrive with the later event-study lab (J-29).
- The section has its own **loading skeleton** on first load, a subtle dim during re-fetch, a **"Backend unavailable"** error card, and an honest **empty-pool message** when no observations exist for the chosen conditions/horizon.

---

## What Old Behavior Changed

- None. The change is strictly additive. The existing decile table, rank-IC, regime-effectiveness table, the global as-of date control, and the shared horizon selector are unchanged. Toggling the global as-of date still leaves the entire `/research` page (including the new combination table) byte-identical with no date-scoped requests (J-18 preserved — the new section adds no date state).

---

## Not Visible Yet

- **return/MAE and MAE/MFE excursion** risk measures are not yet available — they require the post-snapshot daily high/low excursion path that is part of a later iteration (J-29). The UI states this explicitly so the single downside-deviation column is not read as "all" risk measures.
- **Boolean pattern-flag conditions** (e.g. "VCP-flagged" as a combination condition) are not built; conditions are catalog-factor top/bottom quantiles only this iteration.
