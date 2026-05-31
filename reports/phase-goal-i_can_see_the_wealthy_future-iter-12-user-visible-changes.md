# Phase goal-i_can_see_the_wealthy_future-iter-12 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future-iter-12
**Date:** 2026-05-31
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now open a new **Methodology / Glossary** page by clicking the **"Methodology"** item in the left sidebar (placed after "Watchlist") or by navigating to `/methodology`.
- Users can now read, for **all six setup statuses** (Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist) **and the VCP pattern**, a plain-language meaning, the exact thresholds that define it, and a worked example — all on one page.
- Users can now **hover, tap, or keyboard-focus** the small info (ⓘ) affordance next to a **setup badge** on the `/stocks` leaderboard to read that status's definition inline, without leaving the page.
- Users can now read the **VCP pattern definition** inline on `/stocks` by opening the info affordance on a VCP badge (the per-row reason still shows on the badge's native hover tooltip).
- Users can still filter the `/stocks` leaderboard by Setup status — the dropdown options are now sourced from the same catalog (the six statuses are unchanged from the user's point of view).

---

## What Changed in the Visible UI

- A new **"Methodology"** link (book icon) was added to the sidebar navigation, after "Watchlist" — bringing the app to 9 top-level nav items and 12 routes.
- A brand-new **`/methodology` page** renders each catalog entry as a card: the entry name + a **Setup / Pattern** chip, the plain-language meaning, a compact thresholds list (each row shows `label comparison value unit`, or a prose rule verbatim), and a worked example. It uses the existing dark analytical style (PageHeading, Card, monospace numbers) and the standard loading-skeleton / "Backend unavailable" error / empty-state patterns.
- On `/stocks`, each **setup badge** now carries a small info (ⓘ) button that opens a `role="tooltip"` panel containing the catalog definition for that row's status.
- On `/stocks`, each **VCP badge** now also exposes the catalog VCP definition through the same info affordance.

---

## What Old Behavior Changed

- **`/stocks` Setup filter source:** previously the Setup-filter dropdown options came from a hard-coded `SETUP_STATUSES` array in the frontend. Now they come from the methodology catalog (`kind:"setup"` entries, in catalog order). The visible options are the same six statuses, but if the catalog fetch fails the filter **gracefully falls back** to the setup statuses present in the loaded data, so the leaderboard and all filters keep working.
- **`/stocks` page load:** the page now makes an additional small fetch to `GET /api/methodology` to power the tooltips and the Setup-filter vocabulary. This fetch is non-blocking and degrades gracefully, so warm load and existing filters are not expected to break.

---

## Not Visible Yet

- None for this iteration's scope. The new `GET /api/methodology` endpoint is fully wired to both the `/methodology` page and the `/stocks` badge tooltips/filter.
- Intentionally **out of scope** (not built, not a gap): inline catalog tooltips on pages other than `/stocks` (e.g. the Stock Detail page), a config-editing UI, and any charting/visualisation of thresholds.
