# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-10 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-10
**Date:** 2026-06-13
**Agent:** developer
**Status:** complete

## What Was Built

A frontend-only, view-transform iteration (zero backend diff) delivering the two target journeys:

- **J-64 — `/research/samples` sortable + ticker-filterable table.** The samples drill-down table is now
  click-sortable on every column (Ticker, Snapshot date, each qualifying-value column, and Forward return)
  and carries a type-to-filter ticker input — both pure client-side view transforms over the
  already-served `data.rows` (re-order / narrow the rendered list only; recompute / re-rank / refetch
  nothing). The default order is exactly the served order.
  - Sort follows the J-48 contract reused from `/stocks`: click a header → ascending; click again →
    toggle to descending; **third click on the active column clears the sort back to the served order**
    (J-64 step 5 — "clear the sort → the served order returns"). Exactly ONE sort indicator
    (`data-testid="sort-indicator"`) is visible at a time (rendered only on the active column).
  - The ticker filter narrows visible rows by case-insensitive substring match as the user types (no
    submit button). While active it renders an honest **"Showing x of N observations"** line
    (`data-testid="samples-view-count"`); the published cohort total (`data-testid="samples-total"` in
    `CohortSummary`) continues to read the served `data.total` **unchanged** — the filter never touches
    the cohort total.
  - An all-filtered-out result renders a **distinct honest view-empty state** ("No observations match this
    filter", `icon=Search`) — distinct from the existing valid-n=0 cohort empty state ("This cohort has
    zero observations", `icon=Microscope`). Never a fabricated row. Clearing the filter restores every row.
  - The transform is layered **filter THEN sort**, each `useMemo`-memoized (the iter-9 `/stocks`
    structure), so they compose and the ~20k-row rank-IC pool stays responsive. Stable tie-break preserves
    the served/filtered order on ties.
  - Nested-interactive-element hazard avoided (iter-5 lesson): the new sort `<button>` and the existing
    `TermInfo` info trigger are SIBLINGS inside each `<th>` (a local `SortHeader` component mirroring the
    `/stocks` `SortHeader` structure) — never nested.

- **J-65 — `N=` chips open the drill-down in a new tab.** `SampleLink` now renders with
  `target="_blank"` + `rel="noopener noreferrer"`. The href construction is **byte-unchanged** (same
  two-step `buildSamplesHref(cohort, scope)` + `useAsOfHref` serialization, so cohort params + `scope` +
  `?asof` all carry — J-51 / J-50 hold). Opening the drill-down no longer disturbs the originating Research
  tab's lab/scope/scroll state. The samples page's own "Back to Research" link stays same-window.

J-51 deep-link/reload behavior, J-52 row-ticker links, the cohort summary, the caveat banner, and the
valid-n=0 cohort empty state are all byte-unchanged (the sort/filter view state is intentionally NOT
serialized to the URL — see OUT OF SCOPE — so the J-51 cohort-param contract is untouched).

## Files Changed

- `apps/frontend/app/research/samples/page.tsx` — added `SortCol`/`SortDir` types + per-column
  comparators (null-last ordering), a local `SortHeader` component (sort button + `TermInfo` sibling), the
  ticker filter input + "Showing x of N observations" view-count line, the memoized filter-then-sort
  transform, and the distinct view-empty state; imported `SampleRow` type + `ArrowUp`/`ArrowDown`/
  `ArrowUpDown`/`Search` icons.
- `apps/frontend/components/sample-link.tsx` — `N=` chip now opens in a new tab (`target="_blank"` +
  `rel="noopener noreferrer"`); updated the doc comment (href construction unchanged).

## Tests Run

Command: `cd apps/frontend && npx tsc --noEmit` (the configured frontend gate — ESLint is not installed)
Result: **PASS (exit 0)**, no type errors.

Backend gate: `git diff --name-only -- apps/backend/` is **empty** — frontend-only contract honored, the
backend suite is not re-gated this iteration (per the iter spec).

Verified all expected `data-testid`s are present and correctly placed: `samples-total` (cohort total,
untouched by filter), `samples-view-count`, `samples-ticker-filter`, `sort-indicator` (active column only),
`samples-table`, `samples-ticker-link`, `cohort-summary`.

## Known Issues

- Browser QA not run by dev (deferred to browser-qa-agent). Per the iter spec's TESTING REQUIREMENTS,
  J-64 must be graded against a **high-cardinality cohort** (e.g. a Factor Lab decile, ~2k rows, many
  distinct tickers + a value spread per sortable column) — confirm the chosen cohort's data ceiling
  supports every leg BEFORE grading (iter-9 dormant-overflow lesson). Count coherence ("x of N",
  drill-down total == published N) must be asserted **same-instant** against the live aggregate, never
  against an earlier capture's N (iter-7 N-drift lesson).
- The dev server was not started by dev (this multi-project machine: never broad-`pkill` dev servers; the
  configured frontend gate is `tsc --noEmit`, which passed). browser-qa-agent will start the frontend on
  port 3835 for the live UI verification.
- No new dependencies were added (no post-install step needed).
