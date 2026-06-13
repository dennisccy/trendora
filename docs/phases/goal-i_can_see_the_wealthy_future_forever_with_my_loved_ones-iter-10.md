# Goal Iteration 10 — J-64 samples table sort + ticker filter, J-65 `N=` chips open in a new tab

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 10
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-64, J-65
- **Required-still-passing journeys:** J-25, J-26, J-29, J-32, J-43, J-50, J-51, J-52
- **Anti-goal reminders:**
  - **Leaderboard sorting, searching, and table filtering are view transforms.** Column sorting on
    `/stocks` (and on the `/research/samples` table — J-64), the J-55 symbol search, the J-56 theme
    filter, and the J-64 ticker filter MUST re-order or narrow only the client-rendered rows of the
    already-served payload; they MUST NOT change, recompute, or re-rank any stored value — the rank `#`,
    scores, buckets, setup statuses, pattern flags, and theme membership read exactly as served, and the
    default order remains the scanner's stored rank. A filtered view MUST stay honest about what it
    hides ("x of N") and MUST NOT alter a published cohort total. Sorting/searching/filtering MUST NOT
    introduce a new endpoint or any second compute path. *(extends Single source of truth + No recompute
    in the read path)*
  - **Sample drill-downs are read-only and count-coherent.** Every research samples page MUST list
    exactly the observations behind the published aggregate — the observation total MUST equal the N
    shown on `/research` (same membership filter, same observation set), and every displayed
    factor/indicator value and realized return MUST be the same stored per-observation value the
    aggregate was computed from; the drill-down MUST NOT recompute a factor, return, or membership,
    and an empty cohort renders an honest empty state, never a fabricated row. *(extends Research lab
    is read-only, honest & not predictive + No fabricated data)*
  - **The `?asof` URL param is a serialization, not a second date state.** Date-scoped pages MUST reflect
    the single global as-of state in the URL while historical (and stay date-free at latest), and a URL
    carrying `?asof` MUST restore it through the one global control; no page may parse, hold, or mutate
    its own independent date state. An invalid `?asof` MUST degrade to the latest view — never crash or
    fabricate a date. *(amends + extends Exactly one date selector)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/
    unavailable state and MUST NOT synthesize prices or scores to force a green journey.

## GOAL

The `/research/samples` drill-down table becomes click-sortable and ticker-filterable as an honest
client-side view transform ("showing x of N observations", cohort total untouched), and every `N=`
chip on `/research` opens its drill-down in a new tab without disturbing the Research tab's state.

## BACKGROUND

Iter-9 delivered J-55/J-56/J-57 (the `/stocks` search + theme filter and `/themes` member expansion)
with zero regressions and a COHERENCE-PASS, and the evaluator's explicit next-step recommendation is
J-64 + J-65 at lean depth: the exact view-transform contract just proven on `/stocks`, replayed on the
`/research/samples` table, plus the J-57 new-tab link contract applied to the `N=` chips. This is the
lowest-risk continuation of the J-55..J-67 extension — a frontend-only diff (expected files:
`apps/frontend/app/research/samples/page.tsx`, `apps/frontend/components/sample-link.tsx`) with no
backend change, no new endpoint, and no new Data Contract value. The samples endpoint already serves
every observation row uncapped (`total == len(rows)` in `apps/backend/app/engine/samples.py`), so the
sort/filter is a pure memoized transform over the already-served payload.

Lessons applied (see NOTES for full text): the iter-5 nested-interactive-element hazard (the samples
headers already carry `TermInfo` info-buttons — the new sort `<button>` MUST be a sibling, never a
wrapper, exactly like the `/stocks` `SortHeader` fix), the iter-9 dormant-overflow lesson (verify the
chosen QA cohort actually has enough distinct tickers/values to exercise sort + filter before claiming
a leg observed), and the iter-7 N-drift lesson (assert count coherence same-instant against the live
aggregate, never against an N from an earlier capture).

## IN SCOPE

### Backend

- None. Zero backend diff expected — `git diff --name-only -- apps/backend/` must come back empty
  (frontend-only contract, same as iter-9; the full pytest suite is therefore not re-gated this
  iteration).

### Frontend (if applicable)

- [ ] **J-64 sortable headers** in `apps/frontend/app/research/samples/page.tsx`: make the samples
  table's columns — Ticker, Snapshot date, each qualifying-value column, Forward return — click-sortable
  under the J-48 contract: asc/desc toggle on repeated click, exactly ONE visible sort indicator at a
  time, stable ties, and a pure client-side re-order of the already-served `data.rows` (recomputes and
  refetches nothing; every cell value reads exactly as served). Reuse the proven `/stocks` `SortHeader`
  structure (`apps/frontend/app/stocks/page.tsx`): the sort `<button>` and the `TermInfo` info trigger
  are SIBLINGS inside the `<th>` — never nested interactive elements (iter-5 lesson; extracting a shared
  component is acceptable but optional). Provide a discoverable way to restore the served order (e.g. a
  third click clears the sort, or an explicit reset affordance) — J-64 step 5 requires "clear the sort →
  the served order returns". Default order remains exactly the served order.
- [ ] **J-64 ticker type-to-filter** on the same page: a text input above the table that narrows visible
  rows by case-insensitive substring match on the ticker as the user types (no submit button). While
  active, render an honest **"showing x of N observations"** line; the cohort-total figure
  (`data-testid="samples-total"`, the published N) continues to read the served total unchanged. An
  all-filtered-out result renders an honest view-empty message (distinct from the existing n=0 cohort
  empty state — the cohort is NOT empty, the view is) — never a fabricated row. Clearing the input
  restores every row.
- [ ] **Filter-then-sort layering**: implement the transform as memoized filter THEN sort over
  `data.rows` (the iter-9 `/stocks` structure the evaluator code-verified), so the two compose and large
  cohorts (the rank-IC pool serves ~20k rows) stay responsive. No new endpoint, no change to
  `lib/api.ts`, no change to the cohort param parsing or fetch effect.
- [ ] **J-65 new-tab chips** in `apps/frontend/components/sample-link.tsx`: the `SampleLink` `N=` chip
  opens in a new tab — `target="_blank"` with `rel="noopener noreferrer"` — with the href construction
  byte-unchanged (the same two-step `buildSamplesHref(cohort, scope)` + `useAsOfHref` serialization, so
  cohort params + scope + `?asof` all carry; J-51/J-50 hold). Update the component's same-window doc
  comment. The samples page's own "Back to Research" link stays same-window.
- [ ] Keep J-52 row-ticker links, J-51 deep-link/reload behavior, the cohort summary, the caveat banner,
  and the n=0 cohort empty state byte-unchanged.

### New user-facing capability

A researcher can re-order the evidence behind any published N (by forward return, ticker, snapshot
date, or qualifying value) and narrow it to one ticker as they type — while the published cohort total
stays visibly untouched — and can open any `N=` drill-down in a new tab without losing their Research
lab selections, scope, and scroll position.

### New information displayed

The "showing x of N observations" view-count line while the ticker filter is active; per-column sort
indicators (one visible at a time); an honest "no rows match this filter" view-empty state. All
descriptive view metadata over the already-served payload — no new canonical value.

### New user actions

Click a samples-table column header to sort (toggle asc/desc; clearable back to served order); type in
the ticker filter box; clear the filter; click an `N=` chip to open the drill-down in a new tab.

### UI surface changes

`/research/samples` — sortable headers + a ticker filter input + view-count line above the existing
table. `/research` — the `N=` chips become new-tab links (visual appearance unchanged; the `n=…` chip
formatting still comes from the single `SampleSize` source).

### Product surface delta

The evidence-audit drill-down gains the same findability ergonomics the stock leaderboard already has
(J-48/J-55 contract), and the Research labs stop losing state when a user drills into a sample cohort —
chips behave like the other audit links (J-52/J-54/J-57): new tab, date-preserving href.

### Blueprint conformance

No new surfaces. Both touched pages are existing homes in the blueprint IA: **Research** (`/research`)
and its link-reached child **Samples** (`/research/samples`). The blueprint already registers J-64 and
J-65 as [TARGET] amendments to the built J-51/J-52 Data Contract row; tags updated to [TARGET iter-10].

### Data-contract additions

None. J-64 is a client-side view transform over the already-served samples payload (no new value, no
new endpoint, no second compute path — the "x of N" count is view metadata, like the J-55 "x / N" on
`/stocks`); J-65 changes only the link target attribute (href construction unchanged). Coherence
invariant 13 (view transforms & drill-downs never recompute) is the governing contract.

## OUT OF SCOPE

- Any backend, API, or config change (zero backend diff; the samples endpoint and observation builders
  are untouched).
- URL serialization of the sort/filter view state (`?q=`/`?sort=` on `/research/samples`) — not required
  by J-64 acceptance, and it would touch the cohort-param contract J-51 deep-links depend on. The J-51
  deep-link/reload behavior must remain byte-unchanged.
- J-58 (sectors config industry catalog — next, with a full pytest gate since it touches backend/config),
  J-61/J-62 (heatmap, calendar popover), J-63 (episodes), J-59/J-60/J-66/J-67 (jobs pipeline — planned
  FULL depth).
- Sorting the `/stocks` leaderboard or any other table — J-48 is built; do not touch
  `apps/frontend/app/stocks/page.tsx` except (optionally) to extract a shared `SortHeader` component
  with zero behavior change.
- Pagination/virtualization of the samples table — the table already renders the full served cohort;
  keep the transform memoized, nothing more.

## DEFINITION OF DONE

- [ ] Target journeys J-64, J-65 pass via browser-qa-agent against the committed seed (offline)
- [ ] Required-still-passing journeys (J-25, J-26, J-29, J-32, J-43, J-50, J-51, J-52) remain green
- [ ] No anti-goal violation introduced (view-transform contract, count coherence, one date state, no
      fabricated rows)
- [ ] `tsc --noEmit` clean in `apps/frontend` (the frontend gate — ESLint is not installed; iter-1
      lesson); no new dev-overlay error badge in any capture (iter-5 lesson)
- [ ] `git diff --name-only -- apps/backend/` is empty (frontend-only contract; backend suite not
      re-gated)
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-10-dev.md`

## TESTING REQUIREMENTS

- Browser (J-64): open a high-cardinality cohort first — e.g. a Factor Lab decile cohort (~2k rows,
  many distinct tickers) — and per the iter-9 dormant-overflow lesson confirm the data ceiling supports
  every leg BEFORE grading it (multiple distinct tickers for the filter; a spread of values per sortable
  column). Then: click Forward return → rows re-order; click again → direction toggles; exactly one
  visible indicator (assert via live DOM, e.g. count `data-testid="sort-indicator"`); sort Ticker,
  Snapshot date, and a qualifying-value column in turn; type in the ticker filter → rows narrow,
  "showing x of N observations" renders, AND `data-testid="samples-total"` still reads the served N in
  the SAME render (iter-7 lesson: count coherence asserted same-instant, never against an earlier
  capture's N); filter to a no-match string → honest view-empty state; clear filter + sort → full list
  in served order, every value as served.
- Browser (J-65): on `/research`, click an `N=` chip → `/research/samples` opens in a NEW tab with that
  exact cohort; switch back → the Research tab's lab selections, scope, and scroll are exactly as left;
  repeat with a historical global as-of AND the as-of scope mode active → the new tab resolves the same
  cohort, scope, and date (href carries cohort params + `scope=asof` + `?asof`); the drill-down's "Back
  to Research" link stays same-window. Verify `rel` contains `noopener`.
- Browser (regression): J-51 (drill-down total equals the published N clicked, same-instant against the
  live aggregate), J-52 (row ticker → dated detail in a new tab, unchanged), J-50 (`?asof` in hrefs
  while historical), J-25/J-26/J-29 (the three labs render with chips), J-32 (as-of scope mode), J-43
  (reload/deep-link restore).
- Browser (opportunistic, owed since iter-6 and skipped twice): capture the J-44 dashboard
  indexes-chart toggle cycle (off → reload → still-off → on) EARLY in the browser session, before any
  long/fragile legs.
- Unit/integration: no backend tests in scope (zero backend diff). Frontend gate is `tsc --noEmit`.
- Error cases: all-filtered-out ticker filter → explicit view-empty state, zero fabricated rows; the n=0
  cohort empty state and invalid-cohort (4xx) handling unchanged; clearing the filter restores the full
  served list.

## NOTES

- **Evaluator feedback driving this scope:** iter-9 eval — "Iter-10, lean: target J-64 + J-65 … the
  lowest-risk continuation: the exact contract just proven on `/stocks`, zero backend diff expected."
- **Lesson (iter-5, nested interactive elements):** the samples table headers already wrap labels with
  `TermInfo` (an `InfoTooltip` `<button>`). Making headers clickable MUST keep the sort `<button>` and
  the info trigger as SIBLINGS in the `<th>` (the `/stocks` `SortHeader` pattern, lines ~642-695 of
  `apps/frontend/app/stocks/page.tsx`) — nesting them is invalid DOM and previously surfaced as a red
  dev-overlay error badge in every capture. Reviewer + QA: treat any new dev-overlay badge as a
  must-explain regression even if every journey leg passes.
- **Lesson (iter-9, dormant affordances):** compute the data ceiling before claiming a leg observed —
  for J-64, confirm the chosen cohort actually has multiple distinct tickers and value spreads; if some
  qualifying-value column is constant in the chosen cohort, pick another cohort rather than grading the
  re-order leg on a no-op.
- **Lesson (iter-7, N drift across boots):** published research Ns change as the background warm-up
  matures forward returns. Every count-coherence assertion ("x of N", drill-down total == published N)
  must compare figures captured in the same instant/session.
- **Evidence hygiene (recurring):** md5sum the evidence directory first; one capture per claimed
  surface; no recycled bytes under new names (three prior iterations hit this).
- The blueprint Data Contract already carries J-64/J-65 as amendments to the J-51/J-52 row — this
  iteration registers no new value and requests no nav change (no re-approval needed).
