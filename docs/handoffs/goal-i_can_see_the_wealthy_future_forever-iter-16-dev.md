# goal-i_can_see_the_wealthy_future_forever-iter-16 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-16
**Date:** 2026-06-03
**Agent:** developer
**Status:** complete
**Mode:** INITIAL BUILD (lean, verify-only re-run — environment remediation, no source change)

## Summary (one line)

J-31 is **built, committed, and present** (iter-15). This iteration's real work was **environment
remediation**: the iter-15 dead-shell `.next` clobber was reproduced, diagnosed, and fixed so the
browser-qa-agent can finally capture the J-31 cross-page travel on a clean, hydrated build.
**No source change was needed** (`git diff -- apps/` is empty).

## What Was Built

- **Nothing new in source.** Per the iter spec, no backend or frontend code change was expected, and
  none was required — the captured-at-API-level travel surfaced **no functional defect**.
- **The deliverable is verification readiness**: a clean, hydrated `next dev` server is running on
  port 3835 with the dead-shell clobber removed, the J-31 feature confirmed present in the tree, and
  the deep-link data contract confirmed sound against ground truth.

## Environment Remediation Performed (the actual blocker — iter spec "PRE-TEST")

### 1. Diagnosed the dead shell (smoking-gun, BEFORE any change)

The iter-15 `npm run build` had clobbered the running `next dev` server's shared `.next/`
(MEMORY `browser-qa-dead-shell-next-cache`). Confirmed unambiguously:

| Check | Before (clobbered) |
|---|---|
| `GET /_next/static/chunks/main-app.js` | **HTTP 404** (smoking gun) |
| `.next/BUILD_ID` | **present** (`wOGVe68WvuBLXS_8p7g-5`) — prod build artifact |
| `.next/static/chunks/main-app-<hash>.js` | **present** (`main-app-9475b33838c5bcd7.js`) — prod chunk |
| unhashed dev `main-app.js` on disk | **absent** |
| `.next` prod signatures (`prerender-manifest.json`, `export-marker.json`, `required-server-files.json`) | **present** |

Disk held only content-hashed PROD chunks while the dev server kept emitting HTML pointing at the
unhashed dev chunk `main-app.js` → framework-chunk 404 → un-hydrated SSR shell on every route.
This is an **environmental fault, not a code defect**.

### 2. Stopped the frontend dev server BY PORT (not broad pkill)

Per MEMORY `dev-server-cleanup-by-port` (multi-project machine — never broad `pkill -f "next dev"`).
Mapped the exact process chain on port 3835 — all rooted in `apps/frontend` and bound to `-p 3835`:
`npm exec` (265292) → `sh -c next` (265313) → `node next dev` (265314) → `next-server` listener (265326).
Killed only those PIDs (each guarded by re-confirming `3835` in its cmdline before kill). Port 3835
freed in 1s. **Backend (uvicorn pid 265265 on 8835) left untouched and confirmed still up.**

### 3. Cleared the clobbered build and restarted a clean dev server

- `rm -rf apps/frontend/.next` (removed the prod-clobbered tree).
- Restarted `next dev` via `scripts/start-frontend.sh` (which is pure `npx next dev -p 3835`, **not** a
  build), launched **detached (`setsid`)** so it survives for the browser-qa-agent. Logs:
  `/tmp/trendora-frontend-iter16.log`. Ready in 2.4s; `/` and `/stocks` compiled cleanly on warm.

### 4. Confirmed the shell is HYDRATED (DoD pre-flight gate — all green)

| Check | After (remediated) |
|---|---|
| `GET /_next/static/chunks/main-app.js` | **HTTP 200 ✓** |
| `.next/BUILD_ID` | **absent ✓** (dev mode) |
| `.next` prod signatures (prerender-manifest / export-marker) | **absent ✓** |
| unhashed dev `main-app.js` on disk | **present ✓** (6.4 MB dev chunk) |
| hashed prod `main-app-<hash>.js` | **gone ✓** |
| page HTML chunk refs (`/stocks`) | unhashed dev set: `main-app.js`, `webpack.js`, `app-pages-internals.js`, `polyfills.js` ✓ |
| `GET /api/stocks` | **HTTP 200, 122 rows** (asof 2026-05-28) ✓ — health badge will clear, rows render |
| backend `/api/health` | `{"status":"ok","db_ok":true,"provider":"seed","symbol_count":158}` ✓ |

> **DO NOT run `npm run build` against this live dev `.next`.** That is the iter-15 root cause and
> would immediately re-introduce the dead shell. If a build check is ever wanted, run it in a
> throwaway dir or before the dev server starts — never against the served `.next`.

## J-31 Source Verification (present & committed — no change)

- `apps/frontend/app/research/page.tsx`: `SubjectLeaderboardLink` at **:1002** (rendered :956), link
  text "View the names expressing this on the leaderboard" at **:1013**.
- `apps/frontend/app/stocks/page.tsx`: Next-15 `<Suspense>` boundary (**:88–94**), `useSearchParams`
  (**:102**), `parsePatternParam` (**:55**), URL-initialized `sector`/`setup`/`pattern` state
  (**:108–110**), `router.replace` URL round-trip (**:154**).

## API/Route Smoke of the J-31 Travel (no defect surfaced)

All HTTP 200 — Suspense boundary holds, no 500s, unknown-pattern degrades gracefully:

```
GET /stocks                                -> 200
GET /stocks?pattern=vcp                    -> 200
GET /stocks?pattern=flat_base_breakout     -> 200
GET /stocks?pattern=pullback_to_rising_dma -> 200
GET /stocks?setup=Breakout-watch           -> 200
GET /stocks?pattern=bogus_unknown_pattern  -> 200   (honest fallback — no crash, no fabricated filter)
GET /stocks/MU            (detail page)     -> 200
GET /api/research/factor-lab                -> 200
GET /api/research/event-study               -> 200
GET /api/stocks/MU                          -> 200
```

**Ground-truth filter counts verified against live `/api/stocks` data** (the client-side filter's
source — confirms the deep-link's data contract is sound; browser DOM count assertions will have
correct backing). Pattern flags ride each row as a dict with a `flagged` boolean (plus reason / pivot /
invalidation / detail):

| Filter | Flagged count | Ground truth | Tickers |
|---|---|---|---|
| `vcp` | 4 ✓ | 4 | STX, TSLA, TSM, ORCL |
| `flat_base_breakout` | 3 ✓ | 3 | TPH, GS, ADI |
| `pullback_to_rising_dma` | 9 ✓ | 9 | TPH, VRT, ETN, COST, GEV, ANET, ABNB, VKTX, ENTG |
| setup `Breakout-watch` | 8 ✓ | 8 | WDC, CRWD, GFS, NXPI, FTNT, TXN, PANW, COHR |

## Files Changed

- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-16-dev.md` — this handoff.
- **No `apps/` source files changed** (`git diff --stat -- apps/` empty).

## Tests Run

- **Backend unit suite: NOT run — correctly skipped.** No source change → trivially green (committed
  suite was 453 passed / 4 skipped at iter-15). Per MEMORY `backend-test-suite-runtime` the full suite
  is ~14 min; running it would add no signal.
- **Frontend `npm run build`: NOT run — deliberately avoided.** Running a prod build against the live
  dev `.next` is the exact iter-15 clobber. The FE was already typecheck/build-clean at iter-15. The
  real "test" this iteration is the live hydration confirmation (above) + the browser-qa-agent's
  captured travel.
- **Live verification run:** dead-shell smoking-gun (before/after), J-31 route + endpoint smoke
  (all 200), ground-truth filter counts (all 4 match).

## Handoff to browser-qa-agent

- Frontend dev server is **up, clean, hydrated** on **http://localhost:3835** (detached; log at
  `/tmp/trendora-frontend-iter16.log`). Backend on **http://localhost:8835**.
- Pre-flight gate is **already satisfied** (`main-app.js` → 200; `/api/stocks` → 122 rows). If the
  agent restarts the frontend itself, `.next` is now clean — a fresh `next dev` will also hydrate
  correctly. **It must not run `npm run build` against the served `.next`.**
- Drive the J-31 travel under **exclusive Chrome**, serialize against other Chrome users, assert live
  DOM/URL/network state immediately before each shot, and **de-dup all evidence by sha256** (iter-3/6
  byte-identical-shot bug — note iter-15's own demo shots were byte-identical, the dead-shell tell).
- Ground-truth counts for the DOM assertion are above. For J-18: deep-link a filter, toggle the global
  as-of switcher, and assert (a) filter persists, (b) page re-points by date, (c) **zero** `as_of`/date
  query param on `/api/stocks` and **zero** date param written to the URL (only `sector`/`setup`/`pattern`).

## Known Issues

- **None introduced.** No source change; no anti-goal touched (exactly one date selector preserved —
  the `/stocks` URL carries only `sector`/`setup`/`pattern`, never a date; read-only / no recompute;
  honest NA on low-sample lab cells and honest empty-state on zero-match filters).
- **Out of scope, unchanged:** J-22 (~500-name universe), J-23 (intraday bars), J-24 (timeframe
  selector) remain externally Yahoo-429 data-walled. Backend reports `symbol_count: 158` (not ~500),
  as expected. **Not autonomously retried** (re-confirmed pointless in iters 7, 8). GOAL_ACHIEVED is
  not autonomously reachable; these unblock only on operator confirmation of a reachable no-key egress
  or a `docs/goal.md` scope edit.
- `backend /api/health` shows `last_run_date: null` while `/api/stocks` serves `asof 2026-05-28` with
  122 rows — the latest-date snapshot is computed-once-on-first-view and served from storage (expected
  snapshot-served-reads behavior), not a defect.
