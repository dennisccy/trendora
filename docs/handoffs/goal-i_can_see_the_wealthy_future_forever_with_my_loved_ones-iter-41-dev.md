# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-41 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-41
**Date:** 2026-06-20
**Agent:** developer
**Status:** complete

## What Was Built

J-99 — the Data Manager `/data` membership-timeline panel (J-96 `MembershipTimelinePanel`) gains a **pure
client-side view-transform layer**: client-side pagination (10 rows/page, newest-first, Prev/Next + "Page x
of N") and Year + Month dropdown filters over the already-served `coverage.membership_timeline.points`
payload. Zero backend diff — no new endpoint, no query param, no stored value, no second date state.

- **New frontend module `apps/frontend/lib/membership-timeline-view.ts`** — pure helpers, the single source
  of the page-size constant and the filter/paginate math, mirroring the existing `lib/asof-step.ts` pattern:
  - `MEMBERSHIP_TIMELINE_PAGE_SIZE = 10` (named constant — not an inline magic literal).
  - `ALL_SENTINEL` — the "All" wildcard value for the Year/Month dropdowns.
  - `deriveYearOptions(points)` — distinct calendar years present, newest-first.
  - `deriveMonthOptions(points, year)` — distinct MM present, ascending, optionally year-scoped.
  - `filterTimelinePoints(points, year, month)` — selects EXACTLY the dates whose ISO year/month match;
    returns the SAME object references (verbatim subset, no recomputation).
  - `paginateTimelinePoints(filtered, page)` — newest-first 10/page; clamps `page` to `[1, pageCount]`
    (out-of-range never renders a fabricated/blank row); `pageCount = max(1, ceil(total/10))`; flags
    `isEmpty` for the honest empty state.
- **`MembershipTimelinePanel` (in `apps/frontend/app/data/page.tsx`) wired to those helpers:**
  - Year + Month `Select` dropdowns (the already-imported `Select` control), options derived via `useMemo`
    from the dates present in the payload; both default to "All". Changing a filter resets the page to 1
    (and a Year change drops a now-out-of-scope Month).
  - Prev/Next buttons (disabled at the bounds) + a "Page x of N" readout, shown only when `pageCount > 1`.
  - Honest "Showing X of N dates (filtered from M)" readout above the table.
  - Honest empty state (`No snapshot dates match this filter`) when a filter combination matches zero dates
    — never a fabricated row.
  - The three honesty labels, the step-function chart, the table columns (Snapshot date / Size / Entries /
    Exits / Excl. hist·price·liq), and the `data-testid` hooks (`membership-timeline-panel`, `timeline-table`,
    `timeline-row-${date}`) are unchanged; the rows shown are now the filtered+paged slice.
  - New `data-testid`/`aria-label` hooks for browser-QA (resolve by aria-label, NOT visible text —
    iter-27/28 lesson): `timeline-year-filter` (aria "Filter membership timeline by year"),
    `timeline-month-filter` (aria "Filter membership timeline by month"), `timeline-prev-page` /
    `timeline-next-page` (aria "Previous/Next page of snapshot dates"), `timeline-page-readout`,
    `timeline-count-readout`, `timeline-controls`, `timeline-pagination`, `timeline-empty-filter`.
  - `MONTH_NAMES` module constant maps the ISO `MM` option value to a friendly label (Jan…Dec); the option
    VALUE stays `MM` so the filter matches `date.slice(5,7)` exactly.

### Single-source / no-recompute invariant (the J-99 crux)
The rendered rows are a verbatim `filter`/`slice`/`reverse` over the served `points` objects — no per-date
`size`/`entries`/`exits`/`excluded` value is re-derived, summed, or restated. The unit test asserts the paged
and filtered rows are the SAME object references from the input array. (Single source of truth; No recompute
in the read path; protects J-96/J-06.)

### J-18 invariant
The Year/Month `Select`s and the page index are LOCAL list-view `useState` only. Grep of the diff confirms NO
`setAsOf`, NO `?asof` write, NO `useAsOf()` read for a date, and NO `window`/`document` keydown listener in
the new code. The filters are list controls, not the global as-of switcher (verified live: 0 native
`input[type=date]` on `/data`).

## Files Changed
- `apps/frontend/lib/membership-timeline-view.ts` — NEW: pure J-99 view-transform helpers + the named
  page-size constant.
- `apps/frontend/lib/membership-timeline-view.test.ts` — NEW: 18-check Node-native unit test for the helpers.
- `apps/frontend/app/data/page.tsx` — wired the helpers into `MembershipTimelinePanel` (Year/Month filters,
  pagination, honest readouts, empty state, aria/testid hooks); added `MONTH_NAMES` constant; added
  `ChevronLeft`/`ChevronRight` to the lucide import and the new module to the imports.
- Blueprint: the J-96 Data-Contract row in
  `runs/goal-session-.../state/blueprint.md` ALREADY carries the additive
  "**J-99 view transform [TARGET iter-41, LEAN]**" annotation (pre-seeded by the decomposer); no new row, no
  human re-approval needed — left as-is.

## Tests Run
Command (no JS test framework is installed in this frontend; pure helpers run under Node native TS
type-stripping, the established `lib/*.test.ts` pattern):
`cd apps/frontend && node lib/membership-timeline-view.test.ts`
Result: **18 checks passed.** Asserts: (a) Year/Month filtering selects exactly the matching ISO dates;
(b) pagination yields ≤10 rows/page newest-first and `pageCount === ceil(filteredCount/10)`; (c) filtered+
paged rows are verbatim object references (no recomputation of size/entries/exits/excluded); (d) an empty
filter combination yields zero rows + `isEmpty` true, never a fabricated row; (e) an out-of-range page clamps
to bounds (page 999→last, page 0→1) and never fabricates a row.

Regression of the other frontend lib tests: `node lib/asof-step.test.ts` (13 passed),
`node lib/mdd-color.test.ts` (9 passed) — green.

Type-check: `cd apps/frontend && npx tsc --noEmit` → **clean (exit 0)**.

No backend code changed (`git status --short apps/backend/` empty), so the iter-39 SCHEMA_VERSION green-suite
gate stands for the byte-unchanged backend; per the iter spec this LEAN iter is NOT a GOAL_ACHIEVED candidate
(J-100 still unbuilt), so a flushed full backend suite is not load-bearing here.

### Live render verification (developer pre-handoff; Playwright fallback — Chrome MCP CDP timed out, the
documented iter-38/39/40 host issue)
Backend `:8835` brought up and warmed to readiness `ready` (warmup 10/10, 585 symbols). A SINGLE sequential
`/api/data` probe (never concurrent — MEMORY pool-exhaustion lesson) returned the intact
`coverage.membership_timeline.points` = **1371 dates** spanning 2021-01-04 … 2026-06-16. Frontend `:3835` via
`next dev` (NOT `next build` — protects the `.next` cache). The Chrome MCP CDP WebSocket timed out (host
issue), so I ran the live check via the cached Playwright Chromium. Results (with a viewed, non-skeleton
screenshot at `/tmp/iter41/p1.png`, and the page1/page2 frames md5-confirmed BYTE-DISTINCT):
- Page 1: 10 rows, newest-first (`2026-06-16`, size 544), "Page 1 of 138", "Showing 10 of 1371 dates", Prev
  disabled at the bound.
- Next → Page 2: "Page 2 of 138", first row `2026-06-02` (older, distinct frame; md5 differs from page 1).
- Year=2021: "Showing 10 of 253 dates (filtered from 1371)", "Page 1 of 26", first row `2021-12-31`.
- Year=2021 + Month=03: "Showing 10 of 23 dates", first row `2021-03-31` (exactly March 2021).
- Year=2026 + Month=06: "Showing 10 of 12 dates" (page reset to 1 on filter change confirmed).
- J-18: 0 native `input[type=date]` on `/data`.

Both dev servers were then stopped by PORT (8835, 3835) — never a broad pkill (MEMORY lesson); Chrome `:9222`
(the user's persistent browser) was left untouched. Ports verified free.

## Known Issues
- **Honest empty state not reachable via the live UI dropdowns by design.** Because the Month options are
  derived constrained to the months actually present in the selected Year, no in-UI Year+Month combination
  resolves to zero rows — a deliberately good UX property (you can never pick a combination that hides
  everything). The honest empty state (`timeline-empty-filter` / `view.isEmpty`) is therefore covered by the
  unit test (`filterTimelinePoints(POINTS, "2025", "01") → []` and `paginateTimelinePoints([],1).isEmpty`)
  and the component's `view.isEmpty` guard, rather than by a live dropdown path. For a LIVE empty-state
  capture, browser-QA can force `timeline-month-filter` to a value not present in the chosen year via the
  controlled-`<select>` native-setter idiom (React `onChange` needs the native value setter + bubbling
  change event on this frontend — MEMORY note "React controlled select needs native setter"); the render
  then shows the honest "No snapshot dates match this filter" message with no fabricated row.
- The full live browser-QA capture leg (scrolling the below-the-fold panel into view, the differential
  page-1/page-2 frames, the filtered-rows frame, and the empty-state frame) is the browser-qa-agent's job;
  the developer live check above is a pre-handoff sanity pass only. Plan the Playwright fallback UP FRONT —
  Chrome MCP CDP timed out here too (iter-38/39/40 lesson), and the cached Playwright Chromium lives at
  `~/.cache/ms-playwright/chromium-1208` (drive it with `/usr/bin/python3` which has the Playwright sync API;
  set `PLAYWRIGHT_BROWSERS_PATH=~/.cache/ms-playwright`).
