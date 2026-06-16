# Goal Iteration 25 — As-of deep link renders with no React hydration mismatch (server-aware seeding, hardens J-73)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 25
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-83
- **Required-still-passing journeys:** J-73, J-18, J-43, J-50, J-13, J-42, J-62, J-79, J-80, J-20, J-45
- **Anti-goal reminders:**
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page (including Backtest) reads the single global as-of control.
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them.
  - **No secrets in source.** No hard-coded credentials, API keys, or tokens anywhere; the default seed path requires none, and any live-provider key is read only from the environment.

## GOAL

Opening (or reloading, or new-tabbing) a `?asof=D` deep link renders the selected date from the first server-rendered paint with zero React hydration-mismatch console errors and no Clock→History icon flip — the single global as-of state is seeded identically on the server and the client.

## BACKGROUND

This is an in-place resume after the iter-24 GOAL_ACHIEVED. `docs/goal.md` (commit e06b7a8) queued four new buildable Must-haves J-83..J-86; this iteration targets **J-83 only** — the cleanest, most isolated of the four (a frontend-only SSR/URL-hydration correctness fix with zero backend diff), keeping the iteration tight and scoreable, exactly as the J-73 predecessor was shipped lean in iter-19. The heavier backend journeys (J-84 expand-universe Yahoo cookie+crumb auth, J-85 confirm-gated snapshot rebuild + coverage diagnostic, J-86 max-drawdown columns everywhere) follow at FULL depth in subsequent iterations. J-83 hardens J-73: today `AsOfProvider` is a client component whose lazy `useState(readAsofFromUrl)` initializer returns `null` during SSR (`apps/frontend/components/asof-provider.tsx:69-75` — `window` is undefined on the server) while the client seeds D — so a historical deep-link produces the React-19 "hydration failed / server rendered HTML didn't match" mismatch in the sidebar `?asof` hrefs (J-50) and the as-of indicator chrome. The fix forwards the request's `?asof` query into a request header via a NEW Next.js middleware, the server-component root layout reads that header and passes it as `initialAsOf` into `AsOfProvider`, and the provider's lazy initializer prefers that server-provided value (present and identical on both sides because it is serialized into the RSC payload), keeping `readAsofFromUrl()` only as a client fallback. Depth is lean because this is frontend-only with no backend diff (no full pytest gate), verified by the browser-qa console-error check plus the load-bearing single-date-state invariants.

## IN SCOPE

### Backend
- [ ] None — backend diff MUST be empty (verify `git diff --stat HEAD -- apps/backend` is empty in the dev handoff).

### Frontend
- [ ] Add `apps/frontend/middleware.ts` (Next.js App Router middleware) that reads the request's `?asof` query param and forwards it as a request header (e.g. `x-asof`) to the matched routes. Forward ONLY a shape-valid `yyyy-MM-dd` value (reuse the existing `isValidIsoDate` shape check / `ASOF_PARAM` name — no second param name, no magic literal); never forward provider keys or any other query param. Use a `matcher` that covers app pages but excludes static assets / `_next` / API routes.
- [ ] In `apps/frontend/app/layout.tsx` (server component — keep it server-only; do NOT add `"use client"`), read the forwarded header via `next/headers` `headers()` and pass it as a new `initialAsOf` prop into `<AsOfProvider initialAsOf={…}>`.
- [ ] In `apps/frontend/components/asof-provider.tsx`, accept the new optional `initialAsOf` prop and make the EXISTING lazy `useState` initializer for the single `asOf` state PREFER `initialAsOf` (when a shape-valid `yyyy-MM-dd`) over the client-only `readAsofFromUrl()` — so the server-rendered HTML and the client's first paint carry the SAME resolved as-of. Keep `readAsofFromUrl()` as the client fallback only. Do NOT add a new `useState`, a second/page-local date state, or a `window`/`document` listener; the asof-provider stays the SOLE `?asof` reader/writer; the iter-2 `searchKey` serialize-dep fix and the single-restore guard (`restored` ref) in `AsOfUrlSync` are preserved untouched. The J-43 run-list `ready` validate/degrade pass (unknown/now-latest/malformed `?asof` → strip to latest) stays unchanged.

### New user-facing capability
A historical `?asof=D` deep link (typed, reloaded, opened in a new tab, or middle-clicked) renders fully at D from the first paint with no console hydration error and no visible Clock→History (latest→historical) chrome flip — the as-of badge and the sidebar `?asof` hrefs are correct in the server HTML itself.

### New information displayed
None — no new value, no new column, no new endpoint. Same resolved as-of date, same historical badge, same `?asof` hrefs — only now correct in the server-rendered HTML (eliminating the hydration mismatch and the icon flip).

### New user actions
None.

### UI surface changes
No new page or route. The persistent layout shell (`app/layout.tsx`) gains a server-side `initialAsOf` read; a new `middleware.ts` runs ahead of route rendering. The as-of indicator chrome (History/Clock icon + "Viewing as-of D (historical)") and the sidebar nav links (J-50 hrefs) now render at D in the server HTML.

### Product surface delta
Deep-linked / reloaded / new-tab historical arrivals are visibly clean — no flash, no console error — which is what an analyst sharing a dated link expects. No analytical content changes.

### Blueprint conformance
No new surfaces. J-83 is a cross-cutting hardening of the existing top-bar as-of switcher / `?asof` serialization (the same cross-cutting "J-13/J-43 top-bar as-of switcher" home in `blueprint.md` Information Architecture). The blueprint's Information-Architecture nav skeleton and Data Contract are unchanged except for an additive J-83 annotation on the existing "Resolved as-of date + available dates (ONE global state)" Data-Contract row.

### Data-contract additions
None. J-83 introduces no new displayed value and no new endpoint. It only changes *where* the ONE existing global as-of state is first read (a server-forwarded `x-asof` header instead of a client-only `window` read) so the server and client seed identically. The "Resolved as-of date + available dates (ONE global state)" Data-Contract row gets an additive J-83 annotation (server-aware seeding) — registered in `blueprint.md`; no row is duplicated and no second date source is created (the asof-provider stays the sole `?asof` owner).

## OUT OF SCOPE

- J-84 (expand-universe Yahoo cookie+crumb market-cap auth + pause-resumable) — separate FULL iteration.
- J-85 (confirm-gated snapshot rebuild + coverage diagnostic) — separate FULL iteration.
- J-86 (max-drawdown columns everywhere) — separate FULL iteration.
- Any backend change (provider, snapshot, scoring, serving, schema, config).
- Any change to the J-43 serialize/degrade logic, the J-79 stepping, the J-62 calendar, or the J-50 href-stamping behavior beyond the seeding-source change above.
- The uncommitted working-tree seed artifacts (`apps/backend/data/seed/meta.json` modified, `apps/backend/data/seed/universe.json` with `members: 0`) — these are the visible result of a failed live Yahoo market-cap fetch (the J-84 401 premise) and are NOT addressed or reverted here; J-84 owns them.

## DEFINITION OF DONE

- [ ] Target journey J-83 passes via browser-qa-agent: a `?asof=D` deep link (direct open + reload + new tab) shows NO "Hydration failed / server rendered HTML didn't match" console error; the as-of badge and sidebar `?asof` hrefs render at D in the first paint with no Clock→History icon swap and no latest→D flip; the latest (date-free) URL has no error and no flash; an invalid `?asof` still degrades to latest (J-43) with no hydration error.
- [ ] Required-still-passing journeys remain green: J-73 (no date flash — the predecessor; first data fetch still at D), J-18 (exactly one date selector — the critical invariant), J-43 (`?asof` serialize + invalid→latest degrade), J-50 (`?asof` in every in-app href incl. new tabs), J-13 (browse past date), J-42 (yyyy-MM-dd dates), J-62 (calendar popover), J-79 (◀▶/opt-in arrow stepping), J-80 (/stocks header re-display), J-20/J-45 (chart marker/regime bands).
- [ ] No anti-goal violation introduced — verify: exactly one `asOf` `useState` in `asof-provider.tsx` (the lazy initializer just gains an `initialAsOf` preference; NO second/page-local date state, NO new `useState` for a date, NO `window`/`document` keydown listener); the asof-provider remains the sole `?asof` reader/writer; the middleware forwards ONLY the shape-valid `?asof` value and NO provider key/secret; `app/layout.tsx` stays a server component (no `"use client"`).
- [ ] `tsc --noEmit` is clean (EXIT 0) — the frontend gate (ESLint is genuinely not installed in `apps/frontend`; do NOT add an `npm run lint` DoD line — iter-1 lesson).
- [ ] Backend diff is empty (`git diff --stat HEAD -- apps/backend` shows no change) — no full pytest suite is required for this lean, no-backend-diff iteration.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25-dev.md`.
- [ ] `blueprint.md` "Resolved as-of date + available dates" Data-Contract row carries the additive J-83 annotation (done by the decomposer).

## TESTING REQUIREMENTS

- **Browser (J-83):**
  1. Open `?asof=2026-06-10` (a real historical run date) directly; assert the browser console shows NO hydration-mismatch error AND the as-of badge reads "Viewing as-of 2026-06-10 (historical)" with the History (not Clock) icon from first paint, and a sidebar nav link `href` already carries `?asof=2026-06-10` (capture the console panel + the badge full-viewport).
  2. Reload that same deep link and open it in a NEW tab — same clean result both times.
  3. Open the latest (date-free) URL — no console error, no flash, Clock icon, clean hrefs.
  4. Open an invalid `?asof=not-a-date` (and a well-formed-but-unknown date) — degrades to latest (J-43) with NO hydration error and NO fabricated/wrong-date flash; the stale param is stripped.
  5. After arrival, exercise client-side nav + the ◀▶/arrow stepping (J-79) + the calendar — the date and `?asof` URL still update exactly as before (J-43/J-50/J-62/J-79 unchanged).
  6. Re-smoke the critical J-18 invariant: `/backtest` has zero page-local `<select>`/date inputs; the single global control drives the date.
- **Unit/integration:** none required beyond `tsc --noEmit` (frontend-only, no backend diff; no testable backend code path changes). The middleware's `?asof` shape-guard reuses the existing `isValidIsoDate` — no new validation logic to unit-test.
- **Error cases:** invalid / unknown / malformed `?asof` must degrade to latest with no hydration error and no fabricated date; the middleware must NOT forward a non-ISO value or any provider key/secret header.

## NOTES

- **Lessons applied (from the session ledger):**
  - iter-1: ESLint is not installed in `apps/frontend` — use `tsc --noEmit` as the frontend gate; do NOT write an `npm run lint` DoD line. App-Router URL↔state sync needs `searchParams` in the serialize effect's dependency array; the iter-2 `searchKey` serialize-dep fix and the `AsOfUrlSync` single-restore guard MUST be preserved untouched — verify the J-43 deep-link restore still works post-hydration via `window.location.href` assertions, not just HTTP-200 (HTTP-200 cannot catch a deep-link-vs-serializer race).
  - iter-16: a "two isolated frontend files" lean iteration can carry the critical J-18 anti-goal at its center — the decisive check is STATIC: grep the diff for `window`/`document.addEventListener` keydown (must be none) and confirm `asof-provider.tsx` keeps exactly ONE `asOf` `useState` (the lazy initializer just gains an `initialAsOf` preference). Verify the middleware adds no second date state.
  - iter-17/iter-18: browser-qa can hard-SKIP when Chrome DevTools `:9222` is unreachable, leaving the journey `unknown` with no evidence — confirm `:3835`/`:8835`/`:9222` reachability BEFORE scoring; never upgrade an `unknown` target journey to `passing` on source review alone. The hydration-error check is the load-bearing positive evidence for J-83 and MUST come from a live console capture (a hydration mismatch is only observable at runtime).
  - Evidence hygiene (recurring iters 3/5/7/9/10/13/15/18): md5sum the evidence dir FIRST; reject byte-identical/blank captures and filename-vs-content mismatches; capture the console panel showing zero hydration errors (not just the rendered page).
- **In-place resume context:** per the iter-22 lesson, "every journey in journey-history.json is green" is NOT GOAL_ACHIEVED while goal.md has queued new buildable Must-haves with no journey-history entry (J-83..J-86). After J-83 passes, J-84/J-85/J-86 remain to build before GOAL_ACHIEVED.
- **Why J-83 first / alone:** it is the lowest-risk, fully-isolated, frontend-only fix and it hardens an already-passing journey (J-73) — a clean opening iteration for the extension. The three heavy backend journeys warrant their own full-depth iterations with the full pytest gate.
- **Critical-invariant focus for the reviewer/evaluator:** J-83 changes only *where* the ONE global as-of state is first read (server header vs client `window`). The single-date-state guarantee (J-18) is the load-bearing thing to protect — assert no second date state, no new date `useState`, no global window listener, and the asof-provider stays the sole `?asof` owner.
