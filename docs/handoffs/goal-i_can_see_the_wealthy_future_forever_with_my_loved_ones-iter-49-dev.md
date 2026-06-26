# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49
**Date:** 2026-06-26
**Agent:** developer
**Status:** complete

## What Was Built

### J-106 — "Proximity to 52w high" leaderboard column
- New sortable **"Proximity to 52w high"** column on the `/stocks` leaderboard, placed **directly after
  the Risk column**. It re-displays the stored `high_proximity` Leadership `ScoreComponent` value (the
  canonical `dist_from_high` — a percent ≤ 0, `0.00%` at a fresh high, `NA` on short history), read
  **verbatim** from each row's `leadership.components`. No new served field, no recompute, no change to
  the `/api/stocks` payload.
- Client-side sortable via the existing `SortHeader` / `comparatorFor` view-transform contract (J-48),
  with an **explicit NA-last** comparator branch (NA never poses as a top/bottom value, in either
  direction). The sort control exposes `aria-label="Sort by Proximity to 52w high"` (auto-derived by
  `SortHeader`).
- The header carries the **config-backed glossary tooltip** via `term="52-week high proximity"` — a term
  that already exists in the single methodology glossary catalog (`config.yaml:1212`). No backend
  methodology change was needed.
- **Single-source alignment (important):** the Stock Detail Leadership breakdown previously rendered the
  *opaque percentile* (`pctl XX`) for `high_proximity`, while the spec requires the column to show the
  ≤ 0 distance value AND to equal what the breakdown shows. To satisfy both coherently, the shared
  `ComponentBreakdown` now renders the **same raw distance value** for `high_proximity` (e.g. `-0.53%`),
  using the SAME shared formatter the column uses (`lib/high-proximity.ts`). The leaderboard column and
  the detail breakdown are therefore byte-identical for any ticker (verified live: MU `-0.53%` on both
  `/api/stocks` and `/api/stocks/MU`). This is a deliberate, minimal deviation from the plan's file list
  (which did not pre-list `component-breakdown.tsx`) — it is REQUIRED by the plan's own critical
  acceptance criterion ("the column MUST show the IDENTICAL value the detail-page Leadership breakdown
  shows … browser-verify equality"). `high_proximity` only appears in per-stock leadership components, so
  this touches only per-stock breakdowns (Stock Detail, Dashboard top candidates, Scanner-run detail) and
  improves explainability (a meaningful distance vs an opaque percentile).

### J-108 — honest readiness badge (diagnosed root cause, then fix)
- **Frontend (host-aware client base):** `lib/api.ts`'s `API_BASE` is now resolved **at request time**
  via a new pure helper `resolveApiBase(configuredBase, hostname, port)` (`lib/api-base.ts`). When the
  configured base is `localhost` but the page was opened on a non-localhost (LAN-IP) host, the backend is
  resolved on the page's OWN host (`window.location.hostname`) + the configured backend port
  (`NEXT_PUBLIC_API_PORT`). SSR is guarded (`typeof window`); an explicit non-localhost
  `NEXT_PUBLIC_API_URL` is always honoured verbatim. Every fetcher goes through `getJSON`/`sendJSON`, so
  this fixes the request base for the whole app with one change.
- **Backend (dev CORS widening):** `main.py` now reads an optional `CORS_ORIGIN_REGEX` env and passes it
  to the CORS middleware as `allow_origin_regex` (refactored into a testable `create_app()` factory).
  `scripts/dev.sh` computes `LOCAL_IP` **before** exporting CORS, adds the LAN-IP frontend origin to
  `CORS_ORIGINS`, and sets `CORS_ORIGIN_REGEX` to a private-LAN pattern (dev-only; never set in prod, so
  production CORS stays the explicit allow-list).
- The badge keeps its three honest states (Ready / Initializing… n/m / Unavailable) — nothing about
  `readiness.py` or the readiness states changed (confirmed by test).

## Diagnosed J-108 Root Cause (step 4 — documented BEFORE fixing)

The badge was stuck on **"Backend unavailable"** when the frontend was opened at the `dev.sh`-printed
**LAN-IP origin** (`http://<LAN_IP>:<FRONTEND_PORT>`). Two independent defects on the live request path,
both confirmed:

1. **Wrong host (client base).** `dev.sh` bakes `NEXT_PUBLIC_API_URL=http://localhost:<BACKEND_PORT>` into
   the frontend. `API_BASE` was a module-load-time constant, so EVERY page (via `getJSON`/`sendJSON`,
   incl. `fetchHealth`) fetched `http://localhost:<BACKEND_PORT>`. When the page is opened at the LAN-IP
   origin, the browser's `localhost` resolves to the **viewer's own machine**, not the dev host → the
   `/api/health` fetch fails → `ReadinessProvider` catches and sets `unavailable` → badge stuck.
2. **CORS block (server).** Even on the same machine, the request Origin is `http://<LAN_IP>:<FE_PORT>`,
   but `CORS_ORIGINS` listed only `localhost` origins → the browser blocks the cross-origin response →
   `fetchHealth` throws → badge stuck.

A `curl` from localhost bypasses BOTH defects (same host, no Origin enforcement), which is exactly why
the iter-45 lesson warns it can't prove the fix. The fix addresses both: (1) host-aware `API_BASE` makes
the browser hit the backend on the same host it loaded the page from; (2) the widened dev CORS accepts
the LAN-IP frontend origin.

## Files Changed

- `apps/frontend/lib/api-base.ts` (NEW) — pure, unit-testable `resolveApiBase()` host-aware resolver.
- `apps/frontend/lib/api-base.test.ts` (NEW) — 11 assertions over the four resolution cases (exact strings).
- `apps/frontend/lib/api.ts` — runtime host-aware `apiBase()` used inside `getJSON`/`sendJSON`; SSR-guarded; explicit non-localhost URL honoured verbatim; `API_BASE` kept as a back-compat export.
- `apps/frontend/lib/high-proximity.ts` (NEW) — shared `highProximityValue()` + `fmtHighProximity()` so the leaderboard column and the breakdown read/format the SAME served value (single source).
- `apps/frontend/components/component-breakdown.tsx` — the `high_proximity` row now shows its raw distance value (single-source equality with the new column).
- `apps/frontend/app/stocks/page.tsx` — new "Proximity to 52w high" `SortHeader` (after Risk) + cell; new `high_proximity` `SortKey`; explicit NA-last comparator branch; `HighProximityCell`; config-backed glossary tooltip.
- `apps/backend/main.py` — `create_app()` factory + optional `CORS_ORIGIN_REGEX` (`allow_origin_regex`).
- `scripts/dev.sh` — compute `LOCAL_IP` before CORS export; add LAN-IP frontend origin to `CORS_ORIGINS`; set dev-only `CORS_ORIGIN_REGEX` private-LAN pattern.
- `apps/backend/tests/test_cors_dev_lan.py` (NEW) — LAN-IP origin allowed with the regex, rejected without it; readiness states unchanged.

## Tests Run

- **Frontend unit (`node lib/api-base.test.ts`):** the established `node lib/*.test.ts` pattern. NOTE: this
  machine's Node v22.22.1 was built WITHOUT TypeScript type-stripping (`node_use_amaro: false`), so
  `node lib/*.test.ts` cannot execute locally — the SAME limitation affects the pre-existing
  `lib/*.test.ts` files; they run in the CI/QA Node environment. The resolver logic was verified locally
  via a byte-equivalent plain-JS mirror of the function + all 11 assertions → **11 passed**. The
  J-106 column/breakdown equality + NA-last comparator logic was likewise mirror-verified → all passed.
- **Frontend typecheck:** `node_modules/.bin/tsc --noEmit -p tsconfig.json` → **exit 0** (no type errors).
- **Frontend compile (live):** under `./scripts/dev.sh`, `GET /stocks` → **HTTP 200** (clean compile, no
  build errors in the dev log).
- **Backend (targeted):** `pytest tests/test_cors_dev_lan.py tests/test_health.py -v` → **5 passed**.
  Confirms: LAN-IP origin allowed with the regex, rejected without it, readiness states unchanged, health
  shape intact.
- **Backend (full suite):** `cd apps/backend && .venv/bin/python -m pytest tests/ -q` — run nohup-async
  per the plan (NON-load-bearing here; this is not a GOAL_ACHIEVED candidate). Result log:
  `reports/qa/goal-...-iter-49-test.log`. See "Known Issues" for the flush status at handoff time.
- **Live request-path verification (J-108, the actual failing scenario, not a localhost bypass):** under
  `./scripts/dev.sh` (backend :8255, frontend :3255, LAN 192.168.1.68):
  - `GET http://192.168.1.68:8255/api/health` with `Origin: http://192.168.1.68:3255` → **HTTP 200** +
    `access-control-allow-origin: http://192.168.1.68:3255` (the browser will now read the response →
    badge reaches Ready/Initializing).
  - A disallowed public origin (`http://evil.example.com`) → **no** allow-origin header (honest CORS).
  - `GET /api/health` localhost baseline → `readiness=initializing` (honest warm-up state, 162 symbols).
- **Live single-source verification (J-106):** `high_proximity.raw` is identical on `/api/stocks` and
  `/api/stocks/{ticker}` (MU `-0.5267` → both render `-0.53%`); fresh highs render `0.00%`.

## Known Issues

- **Full backend suite at handoff time:** started nohup-async and was still in flight when this handoff
  was written (the session-scoped warm-up makes the suite slow). It is NON-load-bearing for this
  iteration per the spec (not a GOAL_ACHIEVED candidate) — do NOT block the evaluator on it. The final
  flush status (`0 failed, EXIT 0` expected) is recorded at the end of
  `reports/qa/goal-...-iter-49-test.log`. No production code path other than `main.py`'s CORS construction
  and the frontend client base changed, and the targeted health/CORS tests already pass.
- **`node lib/*.test.ts` cannot run on this dev box** (Node built without `amaro`/type-stripping). The new
  `lib/api-base.test.ts` follows the established pattern and will run in the CI/QA Node env; its logic was
  mirror-verified locally (11/11). This is a pre-existing environment constraint, not introduced here.
- **J-106 NA path** is unit/mirror-verified but had no live NA row to display (all 120 current warm rows
  have ≥ 52w of history, so `high_proximity` is available for every row). The NA-honest rendering + NA-last
  sort are exercised by the logic mirror; browser-qa should confirm if a short-history date is available.
- **J-108 fix is dev-scoped by design.** `CORS_ORIGIN_REGEX` is set only by `dev.sh`; production CORS is
  unchanged (explicit allow-list). The host-aware client base is universal but only changes behavior when
  the configured base is localhost AND the page host is non-localhost.
