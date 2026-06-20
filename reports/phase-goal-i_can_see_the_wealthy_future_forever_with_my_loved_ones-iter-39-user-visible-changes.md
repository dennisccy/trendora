# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39
**Date:** 2026-06-20
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see the full phase-colored history bands, the 0–100 severity line, and the filtered bear-probability line in the **bottom pane of the two-stacked cross-view chart** on the Dashboard (`/`) at the current (live) date — previously that bottom pane was blank.
- Users can now compare the market's **regime lens** (top pane: normalized index paths) against its **phase/severity lens** (bottom pane: colored phase bands, severity line, P(bear) line) in a synchronized view at the current as-of date.
- Users can scroll the Dashboard below the cross-view chart and see the compact at-a-glance Market Phase & Severity figure populated with real data at the current as-of (it depends on the same data feed that was previously broken at the live date).

---

## What Changed in the Visible UI

- The **bottom pane of the cross-view chart** on the Dashboard (`/`) now renders phase-colored bands, a 0–100 severity line, and a filtered P(bear) line when viewing the current (live) as-of date. Before this fix it rendered empty for any date whose market-phase data had been cached before last iteration's `timeline_full` series was added.
- The **compact at-a-glance Market Phase & Severity figure** (the "at a glance" panel in the Dashboard's restructured layout from iter-38) now displays correctly at the current date, because it draws from the same data feed that the cross-view chart uses.
- The **synced zoom** between the top and bottom panes of the cross-view chart is now meaningful at the current date — zooming in either pane now shows two byte-distinct, non-identical frames rather than one populated pane and one empty pane.

---

## What Old Behavior Changed

- **Cross-view bottom pane at the live/current as-of:** previously always empty (returned no series data from the backend cache). Now populates on the first view after the fix (the backend recomputes once and re-caches in the corrected format), then serves from cache on all subsequent views.
- **Backend market-phase cache invalidation:** previously a stale cached payload was served even when its internal shape was out of date (missing newly-added series). Now the cache is keyed on both the data version AND a payload-schema token, so any payload whose shape predates the current schema is automatically treated as a miss and recomputed once. This is invisible to users except that they see correct data instead of missing data.

---

## Not Visible Yet

- None. All backend changes in this iteration directly resolve the empty-bottom-pane defect that users were experiencing. No new capability was added to the backend without a corresponding UI surface.

---

## Notes for Testers

- The bottom pane sits **below the fold** on the Dashboard — scroll down past the cross-view chart header and top pane to bring it into view.
- For dates before market-phase history exists (very early as-of dates), the bottom pane is expected to render honestly empty. This is correct behavior, not a defect.
- The first request for the full cross-view chart at a previously-cached date will trigger a single bounded recompute (a few seconds). Subsequent views are served from cache.
- The card-view (compact Market Phase & Severity figure) and the retrospective analysis view are unchanged in their data — only the `timeline_full` series (used by the bottom pane) was missing and is now present.
