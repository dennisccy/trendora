# goal-i_can_see_the_wealthy_future-iter-2 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-2
**Date:** 2026-05-29
**Agent:** developer
**Status:** complete

## What Was Built

The first **canonical values** — Market Regime + Sector/industry leadership — computed once in a
backend engine and served read-only from one endpoint each, plus the two UI surfaces that read them.

**Backend engine — `apps/backend/app/engine/` (new package; names match the Data Contract verbatim)**
- `prices.py` — `bars_asof(session, symbol, d)`: the **no-lookahead boundary** (rows with date ≤ d,
  ascending). All engine math reads bars through it. Also `latest_data_date(session)` (= max
  `daily_prices.date`, the deterministic as-of date) and the `closes/highs/lows/volumes` extractors.
- `indicators.py` — pure, DB-free, deterministic functions: `sma`, `rs_vs`, `atr_pct`,
  `dist_from_high`, `ma_stack`, `vol_trend`. Periods are arguments (sourced from config). Insufficient
  history returns `None` (NA) — never a fabricated value.
- `buckets.py` — `to_bucket(score)` → A/B/C/D/E from `config.buckets` edges. The ONLY place A–E is derived.
- `regime.py` — `score_regime(session, asof)` → `{score 0–100, label (one of six), breadth_above_50dma,
  breadth_above_200dma, new_high_low, components[], asof_date, universe_relative}`. Weights from
  `config.regime.weights`; label from `config.regime.label_edges`; a continuous **VIX gate**
  (uses only `vix_threshold` + the live ^VIX, no extra constant). Breadth + new-high/low are
  universe-relative.
- `sectors.py` — `score_sectors(session, asof)` → ranked rows (one per GICS sector SPDR `kind="sector"`
  and per industry-group ETF `kind="industry"`), each `{ticker, kind, name, score 0–100, bucket,
  rs_vs_spy, dist_from_52w_high_pct, trend_label, components[], rank}`. Score = config-weighted blend of
  each row's **cross-sectional percentile** on the six leadership components. **SPY is the RS benchmark
  and is excluded** from the ranked rows; short-history ETFs report NA for long-window components.

**Backend API — `apps/backend/app/api/` (registered under `/api` in `main.py`)**
- `GET /api/sectors` → `score_sectors(asof=latest_data_date)`. The canonical & only Sector Score endpoint.
- `GET /api/dashboard` → `{regime:{score,label,components,asof_date}, breadth:{above_50dma_pct,
  above_200dma_pct, new_high_low, label:"universe-relative"}, asof_date, candidate_counts: null,
  top_themes: null}`. The canonical & only Market Regime endpoint. Both return an explicit **503** when
  no price data exists (frontend renders "Backend unavailable" — never fabricated rows).

**Config (additive; every number lives in config — no literal in calc code)**
- New `indicators:` section (MA periods, RS windows 1m/3m/6m, ATR period, 52w-high window, volume
  period, `min_history_bars` NA floor, breadth short/long DMA).
- New `sectors:` section (component weights summing to 1.0 + trend-label cutoffs).
- Extended `regime:` with `label_edges` (kept existing `weights` + `vix_threshold`).
- `app/config.py` now types + **validates** these (typed `IndicatorsCfg`/`SectorsCfg`/`RegimeCfg`,
  `LabelEdge`); missing/invalid sections raise explicit `ConfigError` (weights must sum ~1.0, edges
  must be strictly descending and cover 0, label_edges must reference the six configured labels).

**Frontend — `apps/frontend/`**
- `lib/api.ts` — typed `fetchSectors()` / `fetchDashboard()` (+ interfaces); re-format only, throw on
  non-200. `/sectors` page: dense ranked table, A–E bucket foregrounded (raw secondary), RS-vs-SPY,
  dist-from-52w-high %, trend label, expandable per-row component breakdown; loading/empty/unavailable
  states. `/` (Dashboard): Market Regime panel (label + 0–100 score + component breakdown),
  universe-relative breadth metrics, Data-as-of indicator, Top Sectors (reads `/api/sectors`, slices
  top 5), and honest **pending** placeholders for candidate counts + Top Themes. New shared components:
  `score-badge.tsx`, `component-breakdown.tsx`.

## Files Changed

**Created**
- `apps/backend/app/engine/__init__.py` — engine package doc + module map
- `apps/backend/app/engine/prices.py` — `bars_asof` no-lookahead accessor + `latest_data_date` + extractors
- `apps/backend/app/engine/indicators.py` — pure indicator functions
- `apps/backend/app/engine/buckets.py` — single `to_bucket(score)`
- `apps/backend/app/engine/regime.py` — `score_regime`
- `apps/backend/app/engine/sectors.py` — `score_sectors`
- `apps/backend/app/api/sectors.py` — `GET /api/sectors`
- `apps/backend/app/api/dashboard.py` — `GET /api/dashboard`
- `apps/backend/tests/test_indicators.py`, `test_prices_asof.py`, `test_buckets.py`, `test_regime.py`,
  `test_sectors.py`, `test_api_engine.py`, `test_config_engine.py`, `test_no_magic_numbers.py`
- `apps/frontend/components/score-badge.tsx`, `apps/frontend/components/component-breakdown.tsx`

**Modified**
- `config.yaml` — added `indicators:` + `sectors:`; added `regime.label_edges`; updated header comment
- `apps/backend/app/config.py` — typed + validated `IndicatorsCfg`/`SectorsCfg`/`RegimeCfg`/`LabelEdge`
- `apps/backend/main.py` — `include_router` for `sectors` + `dashboard` under `/api`
- `apps/backend/tests/test_config.py` — `MINIMAL_VALID` now includes the (newly-required) iter-2 sections
- `apps/frontend/lib/api.ts` — `fetchSectors()`/`fetchDashboard()` + interfaces
- `apps/frontend/app/sectors/page.tsx` — populated ranked leaderboard table
- `apps/frontend/app/page.tsx` — populated dashboard (regime + breadth + data-as-of + Top Sectors + pending)

## Tests Run

**Backend** — `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **72 passed** (25 pre-existing + 47 new). No regressions.

**Frontend** — `cd apps/frontend && npm run build`
Result: **Compiled successfully**, types valid, all 10 routes generated. `/` and `/sectors` now carry
real content (3.45 kB / 3.76 kB).

**End-to-end (live, against the REAL committed seed via FastAPI TestClient — full boot + request path):**
- Seed loads: 211,535 price rows, 158 symbols, status ok. `GET /api/health` → ok.
- `GET /api/dashboard`: regime **"Risk-on"** score **74.32**; breadth 65.57% / 59.02% labelled
  "universe-relative"; new-high/low universe-relative; asof **2026-05-28**; `candidate_counts` and
  `top_themes` both **null**; components present and summing to the score (VIX 15.74 < 20 → factor 1).
- `GET /api/sectors`: **31 rows** ranked 93.67 → 7.17 (SOXX/WGMI/SMH lead, ITB trails), benchmark
  **SPY excluded**, every row carries RS-vs-SPY + dist-from-52w-high + trend label + A–E bucket +
  named components. Repeated calls are byte-identical (determinism).

## Known Issues

- **Live socket verification:** this agent's sandbox blocks long-lived listening sockets, so
  `scripts/start-backend.sh` could not be exercised as a bound server here (it exits before binding).
  The full boot + seed-load + routing + engine path was instead verified in-process via FastAPI
  `TestClient` against the real committed seed (identical code path, no network socket). **QA/browser-QA
  must start both managed servers and judge from the on-disk evidence directory** (iter-1 lesson).
- **Stale `next dev -p 3835` now cleared:** an iter-1-era Trendora frontend dev server (serving
  pre-iter-2 content) was found running and has been **terminated during finalization** so that
  browser-QA's `scripts/start-frontend.sh` boots a clean server against the new `/` + `/sectors`
  pages (pointed at `http://localhost:8835`). The sibling project's `next dev -p 3072` was left
  untouched. **Browser-QA must (re)start both managed servers and confirm stability before judging.**

## Finalization Re-verification (independent, this session)

The prior run's claims were independently re-checked before marking dev complete:
- **Backend:** `cd apps/backend && .venv/bin/python -m pytest tests/ -v` → **72 passed** (the 25
  pre-existing tests intact; no regressions).
- **Frontend:** `cd apps/frontend && npm run build` → **Compiled successfully**, types valid, all 10
  routes generated (`/` 3.45 kB, `/sectors` 3.76 kB) — run with a clean `.next` after clearing the
  stale dev server.
- **Anti-goal sweep:** grep over `apps/backend/app` for broker/order/secret/key/token patterns →
  **no matches** (research-only; no execution path; no secrets).
- **Single source of truth:** confirmed in code — regime computed only in `app.engine.regime` and
  served only by `/api/dashboard`; sector scores computed only in `app.engine.sectors` and served only
  by `/api/sectors`; A–E derived only in `app.engine.buckets`; `test_api_engine.py` asserts the served
  payloads are byte-for-byte equal to the engine outputs against the **real committed seed**.
- **`min_history_bars` NA path** is exercised only by a synthetic unit test (`test_sectors.py`): every
  real sector/industry ETF in the seed has ≥544 bars, so none triggers the floor in production. This is
  expected, not a gap — the floor + NA handling are proven by the synthetic test.
- **On-request (no persistence):** regime + sectors are computed per request from the frozen seed, as
  designed. Persistence into immutable `scanner_runs`/`sector_scores` + the run timestamp are deferred
  to iter-5 (per roadmap); the displayed "Data as-of <date>" is the latest seed date.
- **J-01 is partial by design:** candidate counts + Top Themes render explicit "pending" placeholders
  (per-stock + theme scoring land in iter-3). J-01 is expected to remain `failing` (partially advanced),
  not flip green this iteration; **J-04 is the full target**.
