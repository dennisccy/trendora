# Phase goal-i_can_see_the_wealthy_future_forever-iter-18 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-18
**Date:** 2026-06-04
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On the **Research** page (`/research`) → **Factor Lab** → **"Multi-factor combination cohort"** section, users can now read a **Combined (composite rank-blend)** cohort that is actually populated — it shows real mean/median forward return, hit-rate, downside risk-adjusted figures, and n — instead of the perpetually-empty "NA" row they saw before. This makes "does combining factors beat either factor alone?" an answerable question.
- Users can now combine **up to all 11 catalog factors** in a single combination (the "Add condition" control no longer stops at 3 conditions). Adding more factors keeps the Combined (composite) cohort populated rather than collapsing it to NA.
- Users can still see the **exact strict intersection** of their selected factors, now shown as a clearly-labelled secondary **"Strict overlap (AND)"** row beside the composite — so they can compare the populated rank-blend against the honest exact overlap (which shows **NA + n** when the intersection is empty).
- Users can read the **blend's settings inline** from the section hint: the composite quantile (e.g. "Quintile (20%)") and the weighting scheme (e.g. "equal"), with explicit wording that the blend is a transparent ranking of stored values, **not** a fitted/ML prediction model.

---

## What Changed in the Visible UI

- The **comparison table** in the "Multi-factor combination cohort" section now renders rows in this order: **Baseline (all names)** → each **single-factor** cohort → **Combined (composite rank-blend)** (the emphasized headline row, with a highlighted background and bold label) → **Strict overlap (AND)** (a secondary, muted row). Columns are unchanged: Cohort / n / Mean fwd return / Median / Hit-rate / Risk-adjusted (downside).
- The previous single highlighted **"Combined (AND)"** row is replaced: the highlighted/emphasized row is now the populated **composite** cohort, and the exact AND-intersection moves into the new muted **"Strict overlap (AND)"** row below it.
- The section **hint text** under the "Multi-factor combination cohort" title was rewritten. It now reads "Combine 2–all factor conditions … read the Combined (composite rank-blend) cohort — the top {quantile} of the pool by a {scheme}-weighted blend of the conditions' percentile ranks (a transparent ranking of stored values, NOT a fitted/ML model) …" and explains the Strict overlap (AND) row as the optional secondary exact intersection.
- The **"Add condition" control** now allows adding conditions up to all 11 catalog factors (driven by the payload's `max_conditions`, raised from 3 to 11), instead of disabling at 3.

---

## What Old Behavior Changed

- **"Combined" cohort in the combination section:** previously the highlighted Combined row was the exact AND set-intersection of all selected conditions, which was almost always 0/NA (especially for 3+ factors). Now the highlighted Combined row is a populated composite percentile-rank blend; the exact intersection still exists but is demoted to the secondary "Strict overlap (AND)" row.
- **Maximum number of combination conditions:** previously capped at 3; now up to 11 (all catalog factors). Testers should re-verify the add/remove controls across the full range.
- **`GET /api/research/factor-combination` response shape:** the `combined` field is removed and replaced by `composite` + `strict_overlap` cohorts, plus echoed `composite_quantile` and `weighting` metadata. Any client reading the old `combined` key would break — the frontend has been updated to the new shape. The request signature is unchanged.

---

## Not Visible Yet

- **No date / as-of control was added to `/research`** — this is intentional and out of scope (the Research all-history ↔ as-of-date toggle, J-32, is deferred to iter-19). The page continues to use only the shared `horizon` selector for date scoping. There is no backend `as_of` capability on `/research` endpoints in this iteration.
- All implemented backend capabilities in this iteration (composite cohort, strict-overlap secondary, raised condition cap, echoed blend metadata) are fully wired through to the `/research` UI — there are no other hidden backend-only capabilities from this change.
