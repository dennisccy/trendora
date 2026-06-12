# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5
**Date:** 2026-06-12
**Agent:** developer
**Status:** complete

## Scope
Lean goal-mode iteration. Three pure **frontend view-transform** journeys that share the `/stocks`
surfaces and the cross-cutting nav contract: **J-48** (sortable leaderboard columns), **J-50** (one
shared as-of `href` helper applied to every in-app link), **J-54** (leaderboard tickers open a new tab).
**Zero backend change** — see the frontend-only assertion below.

## What Was Built

### J-50 — one canonical as-of `href` helper (the mechanism the other two ride on)
- Added `useAsOfHref()` to `components/asof-provider.tsx` — the **single** author of every in-app link's
  `?asof` serialization, mirroring how the existing `AsOfUrlSync` is the sole writer of `?asof` onto the
  *current* page. It reads the one global as-of state (`asOf` + `isHistorical`) and returns
  `asofHref(path)`:
  - while **historical** → appends `asof=<D>`; at **latest** (or before the run list resolves) → emits the
    clean path with **no** `asof` and strips any `asof` a caller mistakenly included;
  - **merges** the param into a path that already carries its own query string (e.g. the research link
    `/stocks?pattern=vcp__only`) without clobbering it, and **preserves a trailing `#hash`**;
  - never fabricates a date and holds **no** second date state — it only re-formats the one global value.
- Applied it to **every in-app navigational link** (no component builds the param string itself):
  - `components/sidebar.tsx` — all 10 nav entries (`isActive` still keys on the route, not the query, so
    the active highlight is unaffected by the `?asof` serialization).
  - `app/stocks/page.tsx` — leaderboard row → detail links (also the J-54 new-tab tickers).
  - `app/stocks/[ticker]/page.tsx` — back-to-leaderboard links (×2) + theme chip links (`/themes`).
  - `app/scanner-runs/page.tsx` — run row links; `app/scanner-runs/[runId]/page.tsx` — "All runs" back link.
  - `app/research/page.tsx` — the `SubjectLeaderboardLink` (merges `?asof` into its existing
    `?pattern=`/`?setup=` query).
  - `app/watchlist/page.tsx` — ticker → detail links.
- **Untouched (correctly):** the `/data` date/symbol inputs (job parameters, not the date control), and
  `asof-provider.tsx` **state semantics** (only an additive exported hook; the J-43 restore/serialize
  path and the iter-1/iter-2 `searchKey`-dependency fix are unchanged).

### J-48 — sortable leaderboard columns (`app/stocks/page.tsx`)
- A pure client-side, **stable** sort memo (`sorted`) layered **on top of** the existing filter memo
  (`visible`) — filter THEN sort compose. It re-orders the already-served, already-filtered rows and
  **recomputes/re-ranks/re-formats nothing**: the rank `#`, the six scores, the A–E buckets, the setup
  status, and the pattern flags all read exactly as the API served them (single source of truth).
- Headers `#`, `Ticker`, `Sector`, `Leadership`, `Entry Quality`, `Risk`, `Setup` are click-sortable
  (`SortHeader`, a keyboard-accessible `<button>` with `aria-sort`); `Reason` stays non-sortable.
- Comparators sort by the **served** value: scores by the stored 0–100 number (the A–E bucket rides
  along), `Setup` alphabetically on the served status string, `Ticker`/`Sector` lexicographically.
- **Exactly one** visible sort indicator: only the active column shows an up/down arrow
  (`data-testid="sort-indicator"`); inactive columns show a faint neutral glyph on hover only.
- Initial state = the scanner's **stored rank** (`#` ascending). Clicking a new column adopts ascending;
  clicking the active column toggles asc⇄desc; clicking `#` **restores** the default stored-rank order.
- **Stability:** rows are tagged with their pre-sort index and ties fall back to it, so equal-key rows
  keep stored-rank order and the default `rank`-asc reproduces the stored scanner order exactly. Sort
  state is deliberately **not** URL-serialized (out of scope). Empty filtered set never throws.

### J-54 — leaderboard tickers open a new tab (`app/stocks/page.tsx`)
- The `/stocks` row ticker `<Link>` now carries `target="_blank"` + `rel="noopener noreferrer"`, with its
  `href` built by the J-50 helper — so the new tab lands on `/stocks/[ticker]?asof=D` while historical
  (clean at latest). This applies **only** to the stocks-leaderboard tickers; every other in-app link
  (theme/sector chips, back links, sidebar, etc.) stays same-window.

## Files Changed
- `apps/frontend/components/asof-provider.tsx` -- new exported `useAsOfHref()` helper (additive; no state change)
- `apps/frontend/components/sidebar.tsx` -- all 10 nav hrefs via the helper
- `apps/frontend/app/stocks/page.tsx` -- J-48 sort (state, memo, `SortHeader`, indicator) + J-50 row href + J-54 new-tab ticker
- `apps/frontend/app/stocks/[ticker]/page.tsx` -- back-to-leaderboard (×2) + theme chip hrefs via the helper
- `apps/frontend/app/scanner-runs/page.tsx` -- run row href via the helper
- `apps/frontend/app/scanner-runs/[runId]/page.tsx` -- "All runs" back href via the helper
- `apps/frontend/app/research/page.tsx` -- subject→leaderboard link merges `?asof` into its existing query
- `apps/frontend/app/watchlist/page.tsx` -- ticker→detail href via the helper

## Frontend-only assertion (DoD)
`git diff --stat -- apps/` shows **8 files, all under `apps/frontend/`, ZERO under `apps/backend/`**:
```
 apps/frontend/app/research/page.tsx             |  10 +-
 apps/frontend/app/scanner-runs/[runId]/page.tsx |   4 +-
 apps/frontend/app/scanner-runs/page.tsx         |   4 +-
 apps/frontend/app/stocks/[ticker]/page.tsx      |  12 +-
 apps/frontend/app/stocks/page.tsx               | 161 +++++++++++++++++++++---
 apps/frontend/app/watchlist/page.tsx            |   4 +-
 apps/frontend/components/asof-provider.tsx      |  39 ++++++
 apps/frontend/components/sidebar.tsx            |   8 +-
 8 files changed, 216 insertions(+), 26 deletions(-)
```
`git diff --name-only -- apps/backend/` = empty. Therefore the full backend pytest suite is **not** a
gate for this iteration (per DoD); no backend restart was performed (project memory: do not restart :8835).

## Tests Run
- **Frontend gate:** `cd apps/frontend && npx tsc --noEmit` → **clean (exit 0)**. (ESLint is not
  installed in this project — `tsc --noEmit` is the frontend gate, per the iter spec's lessons.)
- **Pure-logic verification (extracted & run under node, since the frontend has no test runner):**
  - `useAsOfHref` merge logic: **14/14** cases pass — historical adds `?asof=D`; merges into an existing
    `?pattern=`/`?setup=` query without clobbering; preserves `#hash`; overrides/strips a stale `asof`;
    latest emits a clean path; defensive `isHistorical && asOf==null` stays clean.
  - J-48 stable sort memo: **8/8** cases pass — `rank`-asc reproduces stored order; leadership/risk ties
    keep stored-rank order in both directions; ticker/setup alphabetical; input array not mutated
    (memo purity); empty rows never throw.

## Anti-goal compliance
- **Sorting changes no served value** — it is a pure re-order memo over `visible`; `#`/scores/buckets/
  setup/flags are rendered exactly as served; the default order remains the scanner's stored rank; no new
  endpoint, no second fetch, no value re-formatted differently.
- **One helper builds every `?asof` href** — `useAsOfHref()` is the single author; no component
  constructs the param string itself.
- **No second date state** — the helper only reads the one global `asOf`; `asof-provider.tsx` state
  semantics are unchanged; the `/data` inputs are untouched.
- **No new endpoint / no recompute in the read path.**

## Known Issues
- **Live browser QA not run here:** both services (`:8835` backend, `:3835` frontend) were down and the
  iter spec says not to restart the backend; the browser-qa-agent starts services and runs the live
  J-48/J-50/J-54 + required-still-passing checks against the goal.md journey text verbatim. The two
  load-bearing mechanisms were instead verified by extracted pure-logic tests (above) plus `tsc`.
- **No production `next build` was run** to avoid clobbering the dev `.next` cache (project memory:
  a prod build over a dev server's `.next` produces dead un-hydrated shells); `tsc --noEmit` is the
  spec's gate and the browser-qa-agent owns the live dev-server run.
- Sort state is intentionally **not** URL-serialized (explicitly out of scope) — a reload/new-tab opens
  the leaderboard in the default stored-rank order, which is the spec's intended behavior.
