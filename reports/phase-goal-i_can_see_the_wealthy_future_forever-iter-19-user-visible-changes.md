# Phase goal-i_can_see_the_wealthy_future_forever-iter-19 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-19
**Date:** 2026-06-04
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now switch the **Research** page (`/research`) between **All history** and **As of date** analysis modes using a new segmented toggle at the top of the page.
- In **As of date** mode, users can re-point every Research figure — Factor Lab deciles, rank-IC, the multi-factor combination cohort, and the Setup & Pattern event study — to a historical point-in-time window by setting the existing single top-bar as-of date switcher to an earlier trading day. Each lab then pools only the snapshots dated on or before that date.
- Users can read an inline context label that explains the active mode in plain language: in As-of mode it states the point-in-time cutoff date being applied; at the latest date it explains that As-of equals all history; in All-history mode it states that every snapshot is pooled.
- Users can return to the full sample at any time by clicking **All history**, restoring the larger-sample figures.

---

## What Changed in the Visible UI

- The `/research` page now has a new **All history ⟷ As of date** segmented button toggle (`data-testid="analysis-mode-toggle"`) at the top, styled like the existing horizon/side selectors.
- A new inline mode-context line (`data-testid="analysis-mode-context"`) appears below the toggle, describing what the current mode pools and showing the resolved as-of date when scoped.
- All three labs (Factor Lab, Multi-factor combination cohort, Setup & Pattern event study) now re-render their figures according to the selected mode — smaller `n` and honest **NA** cells appear at early historical dates instead of fabricated numbers.
- Stale on-page copy that previously asserted "NO as-of/date control" was updated to the mode-aware description.
- The survivorship / universe-relative / descriptive caveat banner continues to render in **both** modes.

---

## What Old Behavior Changed

- **Research page point-in-time behavior:** Previously `/research` always pooled all history with no date scoping. Now it defaults to All-history (identical to before) but can be scoped to a point-in-time window via the new As-of mode. In All-history mode, moving the global date does **not** change or refetch the Research figures — only As-of mode responds to the global date.

---

## Not Visible Yet

- None. The backend `as_of` scoping seam on the three research endpoints is fully wired to the new UI toggle. There is no new date picker — As-of mode reads the existing global top-bar switcher, so no second date control was introduced.
