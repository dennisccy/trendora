# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-19 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-19
**Date:** 2026-06-15
**Agent:** developer
**Status:** complete

## What Was Built

A LEAN goal-mode iteration with two precisely-scoped, low-risk targets.

### J-78 — Dashboard major-indexes chart defaults to All (full history)
- Changed `config.yaml` `index_chart.default_range` from `"6M"` to `"all"`.
- `"all"` is an already-valid preset key (line 304: `{ key: "all", label: "All", days: null }`).
- **No Python code change**: `app/engine/indexes.py:_resolve_preset` already resolves the default
  from `cfg.index_chart.default_range`, and `app/config.py` (`IndexChartCfg._validate`, line 137)
  already validates `default_range` against the preset keys.
- **No frontend code change**: `components/major-indexes-card.tsx` already initializes `rangeKey = null`
  ("server's config default"), sends no `range` on the default fetch, and reads the active preset back
  from `indexes.range.key`. So the dashboard shows "All" active on a fresh load automatically.
- Result (verified live, backend restarted): `GET /api/indexes` with no range now serves
  `range.key = "all"` with the full history (1356 SPY points, `2021-01-04 → 2026-05-28`, first point
  rebased to `0.0%`). Explicit `?range=6M` still serves a 115-point window — all presets still switch.

### J-73 — No as-of date-flash (synchronous URL hydration)
- In `components/asof-provider.tsx`, the SINGLE global as-of state's `useState` now takes a **lazy
  initializer** `readAsofFromUrl` that synchronously reads a shape-valid `?asof=D` from the current URL
  on first mount, seeding the EXISTING `asOf` state. A historical deep-link / reload / new-tab / in-app
  nav therefore renders at D from first paint — its first data fetch is already at D, with **no
  latest→D flash**.
- This is **not a second date state**: it is a lazy initializer on the one existing `asOf` `useState`
  (the provider still holds exactly 4 states: `dates`, `latest`, `asOf`, `ready`).
- `readAsofFromUrl()` is **server-safe**: during SSR `window` is undefined, so it returns `null` (the
  server cannot know the URL); the client's lazy initializer reads `window.location.search` on
  hydration. It validates shape only (`isValidIsoDate`) — the run-list `ready` step still does the J-43
  semantic validate/degrade.
- The run-list `ready` step is now purely the **J-43 validate/degrade pass**: once `GET /api/runs`
  resolves, a confirmed known historical date is kept (a no-op when already seeded); an unknown /
  malformed / equals-latest value **degrades to latest** — and I **fixed its degrade branch to also
  `setAsOf(null)`** (not merely strip the URL param), so a synchronously-seeded-but-invalid date does
  not stick. J-43 behaviour is otherwise unchanged (invalid → latest, no fabricated date).
- The asof-provider remains the **SOLE** `?asof` reader/writer (one owner). The iter-2 `searchKey`
  serialize dependency fix and the `restored` single-restore ref guard are **preserved untouched** so
  the deep-link restore never races the serializer; at latest the URL stays date-free.

## Files Changed
- `config.yaml` — J-78: `index_chart.default_range` `"6M"` → `"all"` (one line; config-value edit only).
- `apps/frontend/components/asof-provider.tsx` — J-73: added `readAsofFromUrl()` helper + lazy
  initializer on the existing `asOf` state; degrade branch now also resets the state to null. No new
  state, no new listener.
- `apps/backend/tests/test_indexes.py` — added 2 J-78 unit tests (default_range=`all` validates +
  resolves to full history; a non-preset default is still rejected).
- `docs/handoffs/...-iter-19-dev.md` (+ `...-iter-19-frontend.md`) — this handoff.

## Tests Run
Command (backend): `cd apps/backend && .venv/bin/python -m pytest tests/test_indexes.py tests/test_config.py tests/test_config_engine.py tests/test_api_indexes.py -q`
Result: **124 passed in 285.25s** (includes the 2 new J-78 tests; the api-indexes suite boots the app
with the live config change, confirming no regression).

Command (frontend gate): `cd apps/frontend && npx tsc --noEmit`
Result: **clean (exit 0)**. (ESLint is not installed in `apps/frontend`; `tsc --noEmit` is the gate —
no `npm run lint` line, per the iter-1 lesson.)

### Static anti-goal checks (all PASS)
- Exactly **4** `useState` in `asof-provider.tsx` (`dates`, `latest`, `asOf`, `ready`) — **zero new
  date state**. `asOf` uses a lazy initializer (a function reference), not a new state.
- **Zero** `window`/`document` `keydown`/`scroll`/`addEventListener` in the diff.
- **No hardcoded range literal in code** for J-78 (config-value edit only; no `"6M"`/`"all"` literal
  added to any `.ts`/`.tsx`/`.py`).
- **Sole-owner invariant**: grep finds **no** `ASOF_PARAM` / `.get('asof')` / `.set('asof')` reader or
  writer of the `?asof` param outside `asof-provider.tsx`.

### Live smokes (service-startup verification)
- Backend restarted cleanly on `:8835` (warm DB, fast-ready boot) — `GET /api/health` 200, picks up the
  new config; `GET /api/indexes` default now serves `range.key="all"` / full history.
- Frontend dev server live on `:3835` (webpack HMR present, chunks resolve 200 — **not** a dead `.next`
  shell). Deep-link pages serve HTTP 200: `/?asof=2026-05-28`, `/stocks?asof=2026-05-28`, and the
  invalid `/stocks?asof=2026-13-99` (client degrades to latest).

## Known Issues
- **No-flash + post-hydration `window.location.href` assertion is NOT browser-verified by this dev
  turn** — it is the browser-qa-agent's job and is the primary gate this iteration. HTTP-200 smokes
  **cannot** catch the deep-link-vs-serializer race (per the iter-1/iter-2 `searchKey` lesson). The
  browser-qa-agent must: open `?asof=D` via deep link / reload / new tab / in-app nav from a historical
  page and confirm the first rendered data is at D with no latest→D swap, AND assert the post-hydration
  URL carries `?asof=D`; confirm latest → latest view (date-free URL, no flash); and confirm an invalid
  `?asof` degrades to latest with the stale param stripped and no wrong-date flash.
- The backend on `:8835` was restarted by this dev turn so the live host reflects the J-78 config change
  (the previously-running backend was started before the edit and still served `6M`). It is running and
  serving correctly; downstream QA can use it as-is or restart via `scripts/start-backend.sh`.
- Use date constants for QA: latest = `2026-06-12`, a historical run date = `2026-05-28` (1357 run dates
  available; oldest `2021-01-04`).
- J-22 / J-23 / J-24 remain honestly blocked-NA (data-walled, non-halting per `goal.md`); untouched and
  not in scope.
