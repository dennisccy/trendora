# goal-iter-9 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-9
**Date:** 2026-06-13
**Agent:** developer
**Status:** complete

## What Was Built

Three pure **frontend view-transform** journeys over the already-served snapshot rows — zero backend
diff, zero new endpoint, zero second compute path (every served value reads exactly as served).

- **J-55 — `/stocks` type-to-filter symbol search.** A `type="search"` input alongside the existing
  Sector / Setup / Pattern filters. Case-insensitive substring match on `row.ticker` **AND** `row.name`
  (company name), applied per keystroke — no submit button, no Enter, no refetch (the `[asOf]`-keyed
  fetch is untouched). Composes filter-THEN-sort with every existing filter, the new theme filter, and
  J-48 sorting. Serializes as `?q=` exactly like the existing filter params (init-once from the URL via
  a lazy initializer; reflected on change in the existing reflect-effect; trimmed; omitted when empty;
  never a date — J-18). The honest `x / N` visible count already present updates live; a no-match string
  renders the existing honest empty state (description now names the active search/theme too).

- **J-56 — `/stocks` Theme column + theme filter.** A new **Themes** column re-displays each row's
  already-served `row.themes` chips verbatim (the SAME config-derived membership the detail page shows —
  J-06; nothing fetched/recomputed per row). A row in many themes shows the first 3 chips plus a `+n`
  overflow whose full remaining membership is readable in place via a `title` tooltip on a plain
  non-interactive `<span>` (no nested interactive element — iter-5 lesson). A **Theme** filter whose
  vocabulary derives from the served rows' themes in config order (first-occurrence wins, keyed by slug,
  labelled with the shared `name`), keeping exactly the rows whose membership contains the selection.
  Serializes as `?theme=` like the other filter params. An unrecognized `?theme=` slug is treated as
  **inactive** (the `themeActive` guard — it fabricates no filter and hides no rows; mirrors
  `parsePatternParam`'s graceful fall-back to "all"). Composes with every existing filter, the J-55
  search, and J-48 sorting. The column is intentionally **non-sortable** (membership is a set, not an
  orderable scalar) so the J-48 SortKey set is unchanged.

- **J-57 — `/themes` expandable members + dated new-tab links.** The dead `+n` placeholder is now a
  working expand/collapse `<button>` ("+n" ⇄ "Show fewer") that reveals EVERY remaining member in place
  (re-display of the already-served `row.members` — nothing refetched), with local `membersExpanded`
  state independent of the row's own expand state. Every member ticker is now a `next/link` to
  `/stocks/[ticker]` opening in a **new tab** (`target="_blank"` + `rel="noopener noreferrer"`), the href
  built by the shared `useAsOfHref` helper so it embeds `?asof=D` while historical and is clean at latest
  (J-50). Both the member links and the `+n` button carry `onClick={(e) => e.stopPropagation()}` so
  activating them never toggles the theme summary row — and they live in the **separate, non-clickable**
  expanded-panel `<tr>`, not inside the `role="button"` summary row, so no interactive element is nested
  in another (iter-5 valid-DOM lesson). Member preview limit raised to 6 to match the prior truncation.

## Files Changed

- `apps/frontend/app/stocks/page.tsx` — J-55 search state + input; J-56 theme filter state, derived
  `themeOptions` vocabulary, `themeActive` guard, Theme column header + `ThemeChips` cell, `?q=`/`?theme=`
  serialization, enriched empty-state copy + `themeNameForSlug` helper.
- `apps/frontend/app/themes/page.tsx` — J-57 `useAsOfHref` wiring, member expand/collapse state,
  dated new-tab member links, `stopPropagation` on member links + the `+n` button, `MEMBER_PREVIEW_LIMIT`.

## Tests Run

Command (frontend gate — `npm run lint` is unfulfillable, iter-1 lesson):
`cd apps/frontend && npx tsc --noEmit`
Result: **clean (exit 0)** — both before (baseline) and after the change.

Dev-server smoke (frontend only, port-scoped per project memory — started on :3835, cleaned up by port):
- `GET /stocks` → HTTP 200, compiled in 4.5s (700 modules), healthy app-chunk shell (no dead shell).
- `GET /themes` → HTTP 200, compiled in 2.0s (713 modules), healthy app-chunk shell.
- No "Failed to compile" / "Module not found" / runtime error in the dev log.
- Port 3835 released after the smoke (clean — no lingering process).

Backend: **no backend diff** — `git diff --name-only -- apps/backend/` is **empty**, so the backend
pytest suite is not re-gated this iteration (frontend-only contract; session precedent).
`git diff --name-only -- apps/` lists exactly the two frontend files above.

## Known Issues

- The new filter toolbar (search input + Theme filter) and the Theme column render only when
  `state.kind === "ok"` (i.e. the backend returned rows). The SSR/loading shell shows the skeleton, as
  the existing filters already do — this is the established data-gated pattern, not a regression. Live
  verification of the per-keystroke narrowing, `?q=`/`?theme=` round-trip, `+n` expand, and new-tab
  member hrefs is for browser-qa-agent (the backend must be warm; project memory notes a slow first
  boot of several minutes).
- `?theme=` graceful degradation is **value-level** (an unknown slug is inactive, showing all rows) rather
  than stripped from the URL on load — matching how `sector` keeps an unmatched value. The select only
  ever offers in-vocabulary slugs, so this only affects a hand-typed/stale deep-link; it never crashes
  and never fabricates a filter (the J-56 acceptance).
- Sort state remains deliberately non-serialized (unchanged from J-48 — out of scope here).
