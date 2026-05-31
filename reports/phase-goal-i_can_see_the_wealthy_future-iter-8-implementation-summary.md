# Goal Iteration 8 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future-iter-8
**Date:** 2026-05-31
**Written by:** developer

---

## Features Implemented

- **Time-travel the whole dashboard (global as-of date switcher)**: A new control in the top bar lets
  you pick any past trading day from a drop-down and see the Dashboard, Stocks, Themes, Sectors, and a
  Stock's detail page exactly as the scanner recorded them on that date. The list of dates comes from
  the immutable Scanner Runs history. Switching back to "Latest" restores the current view.
- **Clear "historical" indicator**: Whenever you are viewing a past date, an amber badge in the top bar
  reads "Viewing as-of D (historical)". When you are on the latest date it shows a quiet "Latest" badge,
  so it is always obvious whether you are looking at today's snapshot or an older one.
- **Pages now render from saved snapshots, not a fresh recomputation**: The Dashboard, Stocks (list +
  detail), Sectors, and Themes pages now read their numbers from the immutable snapshot the scanner
  saved for the resolved date, instead of recomputing every score on each request. The numbers are
  unchanged in meaning — they are the same values, now served from storage.
- **As-of price chart**: A stock's price/moving-average chart also respects the selected date, showing
  only the bars up to and including that day (no future data leaks into a historical view).

---

## Changed Behavior

- **Dashboard / Stocks / Stock detail / Sectors / Themes endpoints**: Previously each request recomputed
  the market regime, sector, theme, and per-stock scores live. Now each serves the stored values from
  the immutable snapshot for the resolved date and echoes which date it served. For the latest date the
  output is identical to before (the stored snapshot is a faithful copy of the same computation).
- **Selecting a past date**: New behavior — the same five pages re-fetch that date's snapshot and the
  whole view (including the per-page "as of" label) reflects the historical date.
- **First view of a brand-new date**: If a date has never been scanned, the first view computes and
  saves its snapshot exactly once (using only data up to that day); every later view of that date reads
  the saved snapshot — it is never recomputed or overwritten. (In the shipped product every date offered
  by the switcher is already saved, so this path is exercised by tests, not normal use.)
- **Watchlist**: Unchanged for the user. Internally, the current scores/setup/invalidation it shows are
  now read from the latest saved snapshot (the same row the Stocks page serves) rather than a separate
  live computation — keeping the two perfectly in sync.

---

## Backend-Only Items

- The create-once-on-first-view path for an arbitrary in-range trading day works for any seed date, but
  the UI only ever offers the already-saved run dates (which resolve instantly). The on-demand-create
  path is covered by unit/integration tests rather than a free-form calendar in the UI (by design — see
  the spec's Out of Scope).

---

## Incomplete Items

- None for this iteration's scope (J-15 + J-13). The remaining new Must-have journeys — J-12 (glossary),
  J-14 (backtest scorecard), J-16 (VCP) — are explicitly out of scope and deferred to later iterations.

---

## Config and Environment Changes

- None. No new environment variables, config keys, or schema changes. The switcher's dates come from the
  existing `GET /api/runs`; the read endpoints reuse the existing immutable snapshot tables.

---

## Known Limitations

- The selected as-of date lives in client state and survives in-app navigation (clicking the sidebar or a
  leaderboard row keeps the date). A full browser reload returns to the latest view — the switcher is a
  live control, not a bookmarkable URL parameter (a deliberate choice to keep the build simple and avoid
  a Suspense boundary around search params).
- The only historical dates offered are the trading days for which an immutable snapshot exists (the
  bootstrap Risk-Off dates plus the walk-forward cadence dates plus the latest). This is intentional —
  those dates always resolve instantly and reproducibly from the frozen offline seed.
- Breadth / new-high-low remain universe-relative (not full-market internals) on historical views too,
  exactly as on the latest view — labelled as such wherever shown.
