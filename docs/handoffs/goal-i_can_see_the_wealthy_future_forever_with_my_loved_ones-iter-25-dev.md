# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25
**Date:** 2026-06-16
**Agent:** developer
**Status:** complete

## What Was Built

**J-83 — As-of deep link renders with no React hydration mismatch (server-aware seeding; hardens J-73).**
Frontend-only, zero backend diff. The ONE global as-of state is now seeded identically on the server and the client, so opening / reloading / new-tabbing a `?asof=D` deep link renders at D from the first server-rendered paint with no React-19 hydration-mismatch console error and no Clock→History icon flip.

The mechanism (the only thing that changed is *where* the one global as-of state is first read — a server-forwarded header instead of a client-only `window` read):
- A NEW Next.js App-Router **middleware** reads the request's `?asof` query param and, only when it is a shape-valid `yyyy-MM-dd`, forwards it as the `x-asof` REQUEST header. It forwards nothing else (no provider key, no other query param, no non-ISO value).
- The server-component **root layout** (`app/layout.tsx`) reads that `x-asof` header via `next/headers` `headers()` (async in Next 15 → layout is now `async`, still NO `"use client"`) and passes it as a new `initialAsOf` prop into `<AsOfProvider>`.
- The **`AsOfProvider`** accepts the new optional `initialAsOf` prop; its EXISTING lazy `useState` initializer for the single `asOf` state now PREFERS `initialAsOf` (when shape-valid) over the client-only `readAsofFromUrl()` — so the server-rendered HTML and the client's first paint seed the SAME resolved as-of (`window` is undefined on the server, which was the root cause: the server seeded null while the client seeded D). `readAsofFromUrl()` stays the client fallback.
- The `?asof` param literal was lifted into `@/lib/dates` (`ASOF_PARAM`) alongside the new `ASOF_HEADER`, so the Edge-runtime middleware and the `"use client"` asof-provider share the SAME constant (one name, one owner) without the middleware importing a client module.

No new value, no new column, no new endpoint, no new page, no new user action. The J-43 serialize/degrade pass, the J-79 stepping, the J-62 calendar, the J-50 href-stamping, the iter-2 `searchKey` serialize-dep fix, and the `AsOfUrlSync` single-restore `restored` guard are all untouched.

## Files Changed

- `apps/frontend/middleware.ts` -- NEW. App-Router middleware: forwards a shape-valid `?asof` as the `x-asof` request header; `matcher` excludes `/api/*`, `/_next/static/*`, `/_next/image/*`, `favicon.ico`, and any file with an extension.
- `apps/frontend/app/layout.tsx` -- reads the `x-asof` header (async `headers()`), re-shape-validates it, and passes it as `initialAsOf` into `<AsOfProvider>`. Stays a server component (no `"use client"`); now `async`.
- `apps/frontend/components/asof-provider.tsx` -- `AsOfProvider` accepts optional `initialAsOf`; the existing single `asOf` lazy `useState` initializer prefers it over `readAsofFromUrl()`. Imports `ASOF_PARAM` from `@/lib/dates` (removed the local const). No new state, no listener.
- `apps/frontend/lib/dates.ts` -- adds the shared `ASOF_PARAM` (`"asof"`) and `ASOF_HEADER` (`"x-asof"`) constants (server/edge-safe, dependency-free module) so the middleware and the asof-provider share one literal.

## Tests Run

Command (frontend gate per project + spec — ESLint is genuinely not installed in `apps/frontend`; `tsc --noEmit` is the gate, iter-1 lesson):
`cd apps/frontend && npx tsc --noEmit`
Result: EXIT 0 (clean) — re-confirmed after reverting Next dev's auto-edit to `tsconfig.json`.

Backend: no full pytest suite required (lean, no-backend-diff iteration).
`git diff --stat HEAD -- apps/backend` shows only the pre-existing out-of-scope seed artifacts (see Known Issues) — I touched ZERO backend code files.

Runtime SSR verification (live dev server on `:3835` against backend `:8835`, throwaway `NEXT_DIST_DIR=.next-iter25` so the running `.next` was never clobbered; both servers stopped by port and the throwaway dir removed afterward):
- `?asof=2026-06-10` (a real historical run; latest is `2026-06-16`): SSR HTML renders the `lucide-history` icon inside `data-testid="asof-indicator"` AND sidebar nav hrefs carry `?asof=2026-06-10` (`/?asof=…`, `/stocks?asof=…`, `/themes?asof=…`) — the server seeded D, identical to the client → no Clock→History flip, no flash. (The historical badge appears in the server HTML ONLY because the layout received `x-asof`; a client-only read returns null on the server — this is the direct proof the middleware→header→layout→provider path works.)
- `/` (latest, date-free): no "Viewing as-of" badge, Clock icon, no `?asof` href — clean.
- `?asof=not-a-date` and `?asof=2026-13-40` (invalid): middleware shape-gate rejects → server seeds latest, NO fabricated historical badge, the invalid value appears in NO href. Client also seeds latest → no mismatch.
- `?asof=1999-01-04` (shape-valid but unknown): middleware forwards it → server seeds it historical, client seeds it identically (NO mismatch), then the J-43 `ready` step degrades it to latest after the run list loads — exactly the designed degrade with no mismatch because both sides started from the same seed.

## Known Issues

- **Live hydration-console check is the browser-qa-agent's job.** A React hydration mismatch is only observable at runtime in a real browser console. My runtime evidence is at the SSR boundary (server HTML now carries the correct historical/latest chrome and `?asof` hrefs, which is the necessary-and-sufficient condition that eliminates the server↔client divergence). The load-bearing positive evidence — a live console capture showing ZERO "Hydration failed / server rendered HTML didn't match" errors on direct-open + reload + new-tab — must come from browser-qa (iter-17/18 lesson: confirm `:3835`/`:8835`/`:9222` reachability first; never upgrade an `unknown` to `passing` on source review alone).
- **Pre-existing, OUT-OF-SCOPE backend seed artifacts** (`apps/backend/data/seed/meta.json` modified, `apps/backend/data/seed/universe.json` with `members: 0`) were present in the working tree BEFORE this iteration (they appear in the conversation-start git status; `meta.json` last committed at iter-1, commit 63cba98). They are the visible result of a failed live Yahoo market-cap fetch — the J-84 401 premise — and the iter-25 spec explicitly places them OUT OF SCOPE (J-84 owns them). I neither addressed nor reverted them. I changed no backend file.
- **Next dev auto-edited `tsconfig.json`** (added the throwaway `.next-iter25` include) when I ran a verification dev server; I reverted it (`git checkout -- apps/frontend/tsconfig.json`) and re-ran `tsc --noEmit` (EXIT 0) — `tsconfig.json` is unchanged from HEAD.
- **Service cleanup done:** both verification servers (frontend `:3835`, backend `:8835`) were stopped by port (not a broad `pkill`, per the multi-project-machine memory). No port conflict left behind; throwaway dist dir removed.

## Anti-goal compliance (J-18 critical invariant — verified statically)

- Exactly ONE `asOf` `useState` in `asof-provider.tsx` (`dates`/`latest`/`asOf`/`ready` — the same four as before; the `asOf` initializer just gained an `initialAsOf` preference). NO second/page-local date state, NO new date `useState`.
- NO new `window`/`document` keydown/listener in any changed/new file (the only opt-in J-79 listener lives in `asof-switcher.tsx`, untouched).
- The middleware sets ONLY `x-asof`, ONLY when `isValidIsoDate(raw)` — no provider key/secret, no other param.
- `app/layout.tsx` stays a server component (no `"use client"`; only became `async` to await `headers()`).
- The asof-provider remains the sole `?asof` reader/writer; the shared `ASOF_PARAM` literal lives once in `@/lib/dates`.
