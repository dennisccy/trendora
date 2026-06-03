# goal-i_can_see_the_wealthy_future_forever-iter-15 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-15
**Date:** 2026-06-03
**Agent:** developer
**Status:** complete

## What Was Built (UI)

The **synthesis travel J-31**: the Research labs stop being a read-only dead-end — their evidence now
leads, in one click, to the actionable name list and the per-name detail.

- **Stock Leaderboard (`/stocks`) filters are now URL-backed (shareable / deep-linkable).**
  - Open `/stocks?pattern=pullback_to_rising_dma__only`, `/stocks?setup=Breakout-watch`, or
    `/stocks?sector=Energy` (combinable) and the matching dropdown filter is **pre-applied** on load.
  - Changing any of the Sector / Setup / Pattern dropdowns now **updates the URL** (shallow,
    no scroll jump), so the filtered view can be shared or reached with the browser back button.
  - Filtering is unchanged behaviourally — it is still the existing pure client-side re-display of the
    server rows (no re-sort, no recomputed score/flag, no new fetch on filter change).
  - An unrecognized or empty filter param falls back to "all" (no crash); a filter matching zero rows
    shows the **existing honest empty-state** (no fabricated row).

- **Setup & Pattern Lab (`/research`) gains a cross-link.**
  - Whenever a subject (setup or pattern) is resolved, a **"View the names expressing this on the
    leaderboard →"** accent link appears next to the subject selector, with a one-line caption naming
    the synthesis path (lab evidence → the names expressing it at the current as-of date → Stock
    Detail). Clicking it lands on `/stocks` **pre-filtered** to that subject.
  - The link renders even for a low-sample / NA subject (today's expressing names are independent of
    the historical event-study sample). It asserts no name count it cannot prove.

## How a user travels it (the J-31 flow)
1. `/research` → Factor Lab: pick a factor (e.g. the volatility-family contraction measure or
   `RS-vs-SPY-3m`); read the decile means + downside risk-adjusted column + rank-IC + n, and the
   by-regime split.
2. Same page → Setup & Pattern Lab: select a **data-rich** aligned subject (pattern
   `pullback_to_rising_dma`, or setup `Breakout-watch`) and read its event study (distribution /
   expectancy / MAE-MFE / best exit-horizon / by-regime / by-sector, with n + honest NA).
3. Click **"View the names expressing this on the leaderboard →"**.
4. Land on `/stocks` **pre-filtered** — the active filter control reflects the subject and the
   `visible / total` count is the narrowed subset; each visible row genuinely expresses the subject.
5. Click a row → `/stocks/[ticker]` → the subject's badge (pattern pivot/invalidation, or setup
   status) + the three A–E scores + invalidation render, byte-consistent with the leaderboard row, on
   the daily chart.

## Visual / design notes
- No new component-library surface. The cross-link is a **plain accent link** (`text-accent`,
  `hover:underline`, `focus-visible:ring-accent`) — not a button. The `/stocks` filter row is
  visually unchanged.
- Palette/spacing/typography tokens only; numbers stay `tabular-nums`. Additive layout (one link line
  inside the existing `EventStudyLab` card; the leaderboard filter row is untouched).
- The Suspense fallback on `/stocks` reuses the existing `StocksSkeleton` (same look as the loading
  state) and is transient.

## States handled
- **Pre-filtered load** (deep-link) · **filter change → URL reflect** · **unrecognized param → "all"
  fallback** · **zero-match filter → existing honest empty-state** · loading/error states on `/stocks`
  and the lab **unchanged**.

## Date control (J-18 — the principal risk this iter)
- The leaderboard URL carries **filter params only** (`sector`/`setup`/`pattern`). There is **no
  `as_of`/date query param** and **no second date state**. The global top-bar as-of switcher
  (`useAsOf()`) remains the single date control; toggling it re-points the page by date while leaving
  the deep-linked filter intact and firing no extra date param.
- In-app navigation (clicking the cross-link / clicking a row) carries the global as-of across; the
  as-of resets on a hard reload (in-memory provider), so the live flow must be driven by **clicks**,
  not hard reloads.

## Build
- `cd apps/frontend && npm run build` — **PASS** (`✓ Compiled successfully`, `✓ Checking validity of
  types`, `✓ Generating static pages (14/14)`). `/stocks` stays statically prerendered, proving the
  `<Suspense>` boundary is correct.

## Test guidance for browser QA
- Drive the full travel by **clicks** (not hard reloads). Pick a subject with ≥1 expressing name today
  (pattern `pullback_to_rising_dma` ≈ 9 names; setup `Breakout-watch` is populous) so step 5 lands on a
  real row.
- J-18 cross-check: with a filter deep-linked, toggle the global as-of and confirm (distinct
  screenshots + a DOM/network assertion) that the filter stays intact, the page re-points by date, and
  **no `as_of` appears in a leaderboard fetch as a second date state**; confirm exactly one date control.
- Shareable-link check: open `/stocks?pattern=<key>__only` and `/stocks?setup=<status>` directly in a
  fresh nav → the filter is pre-applied.
