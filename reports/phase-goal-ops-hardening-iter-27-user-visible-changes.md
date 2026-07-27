# Phase goal-ops-hardening-iter-27 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-27
**Date:** 2026-07-26
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

This is a hardening/reliability iteration — the spec and dev handoff both confirm "no new journey, page,
endpoint, or user-facing capability." Only one new thing becomes *visible* to a user, and it is a capability
to perceive/trust data, not a new interactive action:

- Users can now tell, at a glance on the Data Manager page (`/data`), whether the "Dataset coverage" panel's
  numbers are fully current, are a real prior reading that is momentarily out of date, or come from a
  database that has genuinely never been scanned. Previously the second and third cases looked identical
  (both rendered as "— → —" / "Universe: 0"), so a user had no way to distinguish "we have years of real
  data, just a slightly stale reading" from "this database has nothing in it."
- No new page, button, form, filter, or workflow was added anywhere in the product this iteration.

---

## What Changed in the Visible UI

- The Data Manager (`/data`) page's coverage panel now shows a new muted notice line — "Coverage as of a
  prior scan (version {stale_dataset_version}) — refreshes on the next data job" — directly below the panel
  title, above the existing metric grid. It appears ONLY when the backend reports the coverage snapshot is
  from an older internal dataset version (the new "stale" state).
- In that same "stale" state, the coverage panel's price-history and universe-count figures now show the
  REAL prior numbers (e.g., a real date range and a non-zero universe count) instead of the misleading
  "— → —" / "Universe: 0" placeholder it used to show for this condition.
- The two pre-existing states are unchanged: a fully current coverage reading still renders exactly as
  before, and a genuinely never-scanned (fresh-install) database still shows the same byte-identical
  all-zero empty state it always has. Most visits to `/data` will look exactly as before.
- No navigation, menu, or page-layout changes anywhere in the product.

---

## What Old Behavior Changed

- **Backtest page concurrency (`/backtest`):** previously, if two requests for the SAME never-before-viewed
  historical date landed close together (e.g., two browser tabs, or a person and an automated check hitting
  the same date at nearly the same moment), one of the two could occasionally come back as an unhandled
  server error (HTTP 500) instead of the normal evidence page. Now both requests always succeed and both
  display the normal Backtest evidence content (Scorecard / As-Of Scan Summary) — the race is caught and
  resolved internally, with no duplicate data ever written. There is no new visible element for this fix —
  it shows up only as the ABSENCE of a crash that could previously occur under this specific timing
  collision.
- **Data Manager coverage panel honesty (`/data`):** previously, whenever the panel's internal "which
  numbers are current" check missed — which could happen after certain historical Backtest lookups nudged
  an internal version stamp — the panel silently fell back to the SAME all-zero, blank-looking display used
  for "this database has never been scanned," even for a database holding decades of real data. Now it
  distinguishes the two cases and only shows the all-zero display for the genuinely-never-scanned case,
  using the new "stale" label + real prior figures otherwise (see above).

---

## Not Visible Yet

- None. The dev and frontend handoffs both confirm the three new coverage fields (`coverage_status`,
  `stale_dataset_version`, `stale_computed_at`) are wired all the way from the backend engine
  (`coverage_from_storage`) through the existing `GET /api/data` response to the `/data` page's
  `CoveragePanel` — nothing new was added to the backend that lacks a UI consumer this iteration.
- The Backtest concurrency fix intentionally has no new UI affordance — it is a reliability fix, not a
  feature, so there is nothing further to expose in the UI for it.
