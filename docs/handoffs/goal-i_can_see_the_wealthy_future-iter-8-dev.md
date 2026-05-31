# goal-i_can_see_the_wealthy_future-iter-8 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-8
**Date:** 2026-05-31
**Agent:** developer
**Status:** complete

## What Was Built

Delivered the keystone **J-15 (snapshot-served reads)** + **J-13 (global as-of switcher)** together —
they are the same mechanism: resolve as-of → load-or-create-once the immutable snapshot → serve its
STORED rows. The critical read path was re-pointed once (not twice).

**Backend — re-point the read path to serve from the immutable snapshot (no recompute):**
- **As-of resolver** in `app/engine/scanner.py`: `resolve_as_of_date(session, as_of)` validates an
  optional `?as_of=` (None/empty → latest stored run date; unparseable → semantic `unparseable`;
  future → `future`; before-history → `before_history`; no data → `no_data`), and
  `resolve_run(session, as_of)` returns the existing stored `ScannerRun` for the resolved date **or
  creates it exactly once** via the existing `run_scan` (INSERT-only, bars ≤ D — immutability +
  no-lookahead inherited). A new `AsOfError(kind, detail)` carries the semantic reason (no HTTP/status
  literal in the engine — `scanner.py` stays magic-number-clean).
- **Snapshot-serving layer** `app/engine/snapshot_serving.py` (new): reshapes a resolved run + its
  stored children into the EXACT existing payloads (`dashboard` / `stocks` / `stock_detail` / `sectors`
  / `themes`), echoes the resolved `asof_date`, and maps `AsOfError` → explicit HTTP (`unparseable`→422,
  `future`/`before_history`→400, `no_data`→503). Per-stock rows rehydrate from the lossless `record_json`
  so list and detail are byte-identical (J-06). No score/regime/sector/theme/return is recomputed here.
- **Re-pointed endpoints** (`GET /api/dashboard`, `/api/stocks`, `/api/stocks/{ticker}`, `/api/sectors`,
  `/api/themes`) now accept `?as_of=` and serve the resolved stored snapshot — they no longer call the
  live `score_regime`/`score_stocks`/`score_sectors`/`score_themes`/`summarize_candidates` engines.
- **`GET /api/stocks/{ticker}/bars`** accepts `?as_of=` and returns OHLCV bars + the server MA series
  with date ≤ D (the as-of chart; no-lookahead). Not snapshot-stored (raw bars are not a recomputed score).
- **Watchlist coherence**: `/api/watchlist` now reads current scores/bucket/setup/invalidation from the
  latest stored snapshot row (the SAME row `/api/stocks` serves at latest), not a live `score_stocks`.
- **Not changed:** `/api/runs`, `/api/runs/{run_id}`, `/api/system-health` (J-07/J-08/J-09/J-10).

**Frontend — global top-bar as-of switcher (re-format only):**
- `AsOfProvider` (client context in `app/layout.tsx`) holds `{asOf, setAsOf, latest, dates, isHistorical,
  ready}`, loads dates from `GET /api/runs`, default = latest, survives client-side navigation.
- `AsOfSwitcher` (top bar): a `Select` of run dates + reset-to-latest + a "Viewing as-of D (historical)"
  amber (`--warn`) `Badge` when the date ≠ latest (a quiet "Latest" badge otherwise).
- Dashboard / Stocks / Themes / Sectors / Stock Detail (incl. chart) read `asOf` and pass it to their
  fetchers (`useEffect` deps include `asOf`). The frontend computes no score/bucket/return.

## Files Changed

**Backend**
- `app/engine/scanner.py` — ADD `AsOfError`, `resolve_as_of_date`, `resolve_run`, `_latest_stored_run_date`
  (default-latest, parse/validate, create-once via existing `run_scan`); import `func`, `DailyPrice`.
- `app/engine/snapshot_serving.py` — NEW. Reshape a resolved run + children into the existing payloads;
  `AsOfError` → HTTP; `resolved_run` / `resolved_date` wrappers; `stored_stock_rows`.
- `app/api/dashboard.py` — accept `as_of`; serve `dashboard_payload(resolved_run(...))`.
- `app/api/stocks.py` — re-point `/stocks` + `/stocks/{ticker}` to the resolved snapshot; `/bars` accepts
  + validates `as_of` and slices `bars_asof(D)`.
- `app/api/sectors.py` — accept `as_of`; serve stored `SectorScoreRow`; echo `asof_date`.
- `app/api/themes.py` — accept `as_of`; serve stored `ThemeScoreRow`; echo `asof_date`.
- `app/api/watchlist.py` — enrich from the latest resolved snapshot row (drop live `score_stocks`).

**Backend tests**
- `tests/test_asof_resolver.py` — NEW (12 tests): default→latest, given-date→stored, create-once +
  immutable (no UPDATE / no duplicate), on-demand no-lookahead (truncation equality), error kinds.
- `tests/test_api_engine.py` — ADD: echo `asof_date` on all re-pointed endpoints; historical as-of ==
  `/api/runs/{id}` (byte-identical); J-06 on a historical date; **no-recompute** (patch engines to raise
  → handlers still serve a persisted date); error cases (future/before/unparseable → 4xx). Fixed the
  503 direct-call test for the new `as_of`-first signature.
- `tests/test_bars.py` — ADD: `/bars?as_of=D` returns bars ≤ D; bad `as_of` → 4xx. Fixed the 503
  direct-call signature.

**Frontend**
- `lib/api.ts` — optional `asof?` (first arg) on the 6 fetchers + `withAsOf` helper.
- `components/asof-provider.tsx`, `components/asof-switcher.tsx` — NEW.
- `app/layout.tsx` — mount `<AsOfProvider>` + `<AsOfSwitcher>`.
- `app/page.tsx`, `app/stocks/page.tsx`, `app/themes/page.tsx`, `app/sectors/page.tsx`,
  `app/stocks/[ticker]/page.tsx` — read `asOf`, pass to fetchers, add to `useEffect` deps.

## Tests Run

**Backend:** `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
- New resolver suite (`tests/test_asof_resolver.py`): **12 passed**.
- Re-pointed API + bars + watchlist + runs (`test_api_engine` + `test_bars` + `test_api_watchlist` +
  `test_api_runs`): **37 passed**.
- `test_no_magic_numbers.py`: passed (scanner.py stays date-/literal-clean).
- **Full regression suite: `196 passed in 1215s (20:15)` — 0 failures, 0 regressions** (was 179+ at
  iter-7; +new resolver/API/bars tests). The whole existing suite (scoring, scanner, forward-testing,
  system-health, watchlist persistence, J-06/07/08 guards) stays green with the re-pointed read path.

**Frontend:** `cd apps/frontend && NEXT_PUBLIC_API_URL=http://localhost:8835 npm run build`
- **Build succeeded** — all 10 routes compiled + typechecked, 0 errors.

**Live service smoke test** (backend booted with `CORS_ORIGINS=http://localhost:3835`, real seeded DB):
- `/api/runs` lists **11 dates** (switcher options); latest `2026-05-28`.
- J-15: latest `/api/stocks` serves 122 rows from the snapshot; NVDA list row == detail row (byte-identical).
- J-13: `?as_of=2022-10-07` echoes the date on all 5 endpoints; its `/api/stocks` rows are byte-identical
  to `/api/runs/{id}`; that run is **Risk-off with 0 Actionable** (J-07 holds on a historical view too).
- Error cases: future→**400**, before-history→**400**, unparseable→**422** (never fabricated).
- As-of chart: NVDA `?as_of=2022-10-07` returns 445 bars, all with date ≤ D (no lookahead).
- `/api/watchlist` → **200** (J-11 smoke). **CORS** allows `http://localhost:3835` (iter-7 root cause guarded).
- Both backend and frontend start without errors; both torn down by port afterward.

## Known Issues

- The selected as-of date is live client state (survives in-app navigation) but is not a bookmarkable
  URL param, so a full browser reload returns to "Latest" (deliberate — avoids a `useSearchParams`
  Suspense boundary). In-app navigation preserves the date (J-13 step 3).
- The switcher offers only dates with a stored immutable snapshot (the run-history dates), which resolve
  instantly. The create-once path for an arbitrary in-range seed date works and is unit-tested, but no
  free-form calendar exists in the UI (out of scope this iteration).
- The full backend suite is slow (~minutes) because the app lifespan re-runs `bootstrap_runs` +
  `backfill_forward_returns` on each `TestClient` entry (idempotent — no behavioural impact).

## Suggested Next Phase

With the as-of snapshot read path in place, **J-14 (Backtest Time-Machine + per-date forward-test
scorecard)** is the natural next iteration — it builds directly on this resolver + the existing
forward-testing engine and will add a `/backtest` nav entry (so it needs `blueprint.reapproval-requested`).
J-16 (VCP) and J-12 (glossary, incl. the VCP catalog entry) pair naturally after that.
