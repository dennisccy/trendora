# Phase goal-i_can_see_the_wealthy_future_forever-iter-15 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-15
**Date:** 2026-06-03
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now jump from the **Setup & Pattern Lab** evidence straight to the matching names by clicking the new **"View the names expressing this on the leaderboard →"** link on the `/research` page. It opens the Stock Leaderboard already filtered to the stocks that express the setup or pattern they were just studying.
- Users can now open a **pre-filtered Stock Leaderboard via a shared/bookmarked link**, e.g. `/stocks?pattern=pullback_to_rising_dma__only`, `/stocks?setup=Breakout-watch`, or `/stocks?sector=Energy` (combinable) — the matching dropdown filters are already applied on load.
- Users can now **share or bookmark a filtered leaderboard view**: changing the Sector / Setup / Pattern dropdowns updates the page web address, so the exact filtered view can be copied from the address bar and re-opened later.

---

## What Changed in the Visible UI

- The **Setup & Pattern Lab card** on `/research` now shows a new accent link, **"View the names expressing this on the leaderboard →"**, with a one-line caption describing the synthesis path (lab evidence → the names expressing it at the current as-of date → Stock Detail). The link appears whenever a subject resolves, including a low-sample / NA subject.
- The **Stock Leaderboard `/stocks` page address now reflects its filters.** The Sector / Setup / Pattern dropdown filter row looks visually identical, but the active filters are now carried in the URL query string and update as the dropdowns change.
- The `/stocks` page now briefly shows the **existing loading skeleton** while it reads filters from the address (a transient Suspense fallback reusing the same skeleton as the normal loading state). No new visual style.

---

## What Old Behavior Changed

- **Stock Leaderboard filters:** Previously the Sector / Setup / Pattern filters were in-page only — the filtered view could not be linked, shared, or pointed at from another page. Now the filters live in the page address (so a link can pre-apply them) and the address updates when a filter changes. The rows shown, the scores/flags, the sort order, and the load speed are unchanged — only the address now reflects the filters and the page can be opened pre-filtered.
- **Setup & Pattern Lab:** Previously a read-only dead-end — you read the evidence and then had to navigate to the leaderboard by hand and re-pick the filter. Now it offers a direct one-click cross-link to the matching names.
- **Date control is unchanged:** the new filter links never carry a date. The top-bar as-of switcher remains the single date control; switching the date keeps the filter intact and re-points the page by date.

---

## Not Visible Yet

- **"Across timeframes" (the intraday 1D / 1h / 15m / 5m chart selector):** not built and out of scope. The underlying intraday data feed is blocked by an external rate limit, so this travel uses the standard daily chart. This is a pre-existing limitation, not a gap introduced here.
- No backend-only capabilities were added this iteration — no new server endpoint, value, or calculation. Everything implemented is reachable in the UI.
