# goal-iter-9 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-9
**Date:** 2026-06-13
**Agent:** developer
**Status:** complete

## UI Surface Changes

### `/stocks` (Stock Leaderboard)
- **New search input** (left of the Sector filter): `type="search"`, placeholder "Search ticker or
  name…", a leading magnifier icon, `aria-label="Search by ticker or company name"`,
  `data-testid="stocks-search"`. Narrows the table per keystroke (case-insensitive substring on ticker
  AND company name). No submit button, no Enter required. Native clear "x" clears it.
- **New Theme filter select** (right of the Pattern filter): `aria-label="Filter by theme"`, options =
  "All themes" + every theme present in the served rows, in config order, labelled with the theme name.
- **New Themes column** (between Setup and Reason): each row shows up to 3 theme chips
  (`data-testid="theme-chips"`) plus a `+n` overflow (`data-testid="theme-overflow"`, a `<span title>`
  listing the rest in place). A row in no theme shows a dash.
- **Visible count** span now carries `data-testid="visible-count"` (the existing `x / N`).
- Empty-state copy now names the active search string and theme when they are what hid the rows.
- Existing columns, the J-48 sort headers/indicators, and the J-54 new-tab ticker links are unchanged.

### `/themes` (Theme Leaderboard)
- **Expandable members.** In an expanded theme row's panel, the first 6 members show inline; if more
  exist a `+n` button (`data-testid="theme-members-toggle"`) reveals every remaining member in place and
  toggles to "Show fewer".
- **Member tickers are now links** (`data-testid="theme-member-link"`) to `/stocks/[ticker]`, opening in
  a **new tab** (`target="_blank"`, `rel="noopener noreferrer"`). The href carries `?asof=D` while a
  historical date is selected (via `useAsOfHref`) and is clean at the latest date.
- Clicking a member link or the `+n` button **never toggles the theme summary row** (`stopPropagation`;
  the controls also live in a separate non-clickable panel `<tr>`).

## Design-System Conformance
- Reused the `Badge`, `Card`, `Select`, `TermInfo`, `EmptyState` components and the existing palette
  tokens (`border`, `surface-2`, `accent`, `text-faint`, etc.). The search input mirrors the methodology
  glossary search styling. No arbitrary colors/effects introduced.
- Every new interactive element has hover + focus-visible states (search input, Theme select, member
  links, `+n` button). The `+n` overflow on `/stocks` is intentionally a non-interactive `title` tooltip
  (set membership, read-only) to avoid nesting interactive elements (iter-5 lesson).

## Accessibility / DOM Hygiene
- No interactive element is nested inside another. On `/stocks` the `+n` overflow is a plain `<span>`.
  On `/themes` the member links and `+n` button live in the non-clickable expanded panel row, never in
  the `role="button"` summary row. No Next dev-overlay error badge expected (verified the routes compile
  cleanly with no runtime error in the dev log).

## Verification for browser-qa-agent
- J-55: type `nv` on `/stocks` → rows narrow (NVDA matches); compose with a Sector filter + a J-48 header
  sort; clear restores all rows; reload `?q=nv` restores the search (assert post-hydration
  `window.location.href` + DOM row count); a no-match string → honest empty state.
- J-56: Theme chips per row; a `+n` overflow readable in place; the Theme filter keeps only member rows;
  composes with Sector/Setup/Pattern + search + sort; open a filtered row's detail → its chips match the
  leaderboard (J-06); `?theme=` round-trips; an unknown `?theme=` value degrades (shows all rows, no
  crash). Drive the Theme select via the native-setter + bubbled change event (project memory: Chrome MCP
  `select` does not fire React onChange here).
- J-57: expand a >6-member theme, click `+n` → all members render; "Show fewer" collapses; a member
  link opens a new tab (assert `target`/`rel`/`href` on the live DOM) while the themes tab keeps
  expansion + scroll + date; at historical D the member href carries `?asof=D`, clean at latest; clicking
  a member link or `+n` never toggles the row.
