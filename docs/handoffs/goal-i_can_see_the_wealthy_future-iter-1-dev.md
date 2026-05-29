# goal-i_can_see_the_wealthy_future-iter-1 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-1
**Date:** 2026-05-29
**Agent:** developer
**Status:** complete

## What Was Built

Foundation & deterministic offline spine — backend + frontend shell. No scoring/journey data
(every page is a styled empty state); the success signal is a real `apps/` tree + committed seed
+ `/api/health` ok offline + the passing keystone seed-integrity test.

**Backend (`apps/backend/`)**
- **FastAPI app** (`main.py`, uvicorn entry `main:app`). Lifespan startup order = **load config →
  create tables → load seed if DB empty**. CORS origins read from `CORS_ORIGINS`. Reads the offline
  `SeedProvider` only — **no network on boot or any request**.
- **Typed config loader** (`app/config.py`, `load_config()`): the single access path to tunables.
  Validates the iter-1-consumed keys (`provider ∈ {seed, stooq}`, non-empty universe + filters, ETF
  lists, themes map, descending bucket edges, database url) and raises an explicit `ConfigError` on
  missing/invalid keys — never a silent default. Also validates that every theme member exists in the
  universe (single-source integrity).
- **`config.yaml`** at repo root — the single source of all tunables (provider, database, 122-stock
  universe + filters, ETF lists [4 index / 11 sector / 20 industry / `^VIX`], 11-theme many-to-many
  map, A–E bucket edges). Scoring / regime / decision_rules / walk_forward sections are **scaffolded
  but NOT wired** this iteration (they are config, not code).
- **DB layer** (`app/db.py`): SQLModel engine from `config.database.url` (relative sqlite paths
  resolved against repo root → Postgres-ready, no SQLite-only SQL), session helper, `create_all()`.
- **Models** (`app/models.py`): exactly the **8 iter-1 tables** — `stocks`, `etfs`, `sectors`,
  `industries`, `themes`, `theme_members`, `daily_prices` (unique + indexed `(symbol, date)`),
  `data_provider_runs`. Snapshot/score/forward/watchlist tables are deferred (not defined).
- **Provider abstraction** (`app/data_providers/`): `PriceProvider` ABC + deterministic `SeedProvider`
  (reads the committed CSV fixture; config default; no network/keys). On a missing/unreadable fixture
  it **raises `ProviderUnavailableError`** and never returns synthesized bars.
- **One-shot ingest** (`app/scripts/ingest_seed.py`): fetched **real EOD OHLCV** for all 158 symbols,
  computed split/dividend-adjusted OHLC, wrote the frozen fixture under `data/seed/prices/` + a
  `meta.json` provenance record. Dev-run once; the loop only reads it afterward.
- **Idempotent seed load** (`app/seed_loader.py`): reference tables from config + prices from the
  committed CSVs; logs a `data_provider_runs` row. A second boot/load is a no-op (no duplicate rows).
- **`GET /api/health`** (`app/api/health.py`) → `{"status":"ok","db_ok":true,"provider":"seed",
  "last_run_date":null,"seed_latest_date":"2026-05-28","symbol_count":158}`.
- **`requirements.txt`** pinned (fastapi, uvicorn, sqlmodel, pydantic, pandas, pyyaml, httpx,
  APScheduler [listed, no jobs wired], pytest, pytest-asyncio).

**Frontend (`apps/frontend/`, Next.js 15 App Router + TS + Tailwind + shadcn-style UI)**
- Persistent **left sidebar** (the 7 approved IA routes) + a header live **health badge**.
- 7 nav pages + 2 detail-route stubs (`/stocks/[ticker]`, `/scanner-runs/[runId]`) — all styled
  empty states in the dense-dark analytical palette.
- `lib/api.ts` typed `/api/health` fetch (no client-side business computation); `HealthBadge` shows
  loading → connected (provider + latest seed date + symbol count) or an explicit **"Backend
  unavailable"** — never a fabricated "ok".

## KEYSTONE — live ingest result & seed regime coverage (per DoD)

- **Did the live ingest succeed?** **Yes** — 158/158 configured symbols fetched with real EOD history.
- **Source (documented deviation):** the plan named **Stooq**, but Stooq's bulk CSV download is now
  gated behind an **apikey obtained via captcha**. Committing such a key would violate the *No secrets
  in source* anti-goal, and a captcha is not reproducible/unattended. I used the free, **no-key Yahoo
  Finance chart API** (`query1.finance.yahoo.com/v8/finance/chart`) instead. Same hard guarantees:
  **real EOD history, no key, no secret, deterministic + frozen once committed.** No bars were
  fabricated or hand-edited.
- **One symbol dropped, not faked:** `CYBR` (CyberArk) returned “No data found, symbol may be delisted”
  (Palo Alto acquisition). It was **removed from `config.yaml`** so the committed seed covers every
  config symbol with **zero failures** — rather than fabricating data. Universe is now 122 stocks.
- **Seed window:** **2021-01-04 → 2026-05-28** (~5.4 years), 158 symbols, ~13 MB committed CSVs.
- **Both regimes proven on REAL SPY bars (keystone test, not assertions of exact scores):**
  - **Risk-off:** longest contiguous run with close < SMA200 = **87 trading days** (2022-04-11 →
    2022-08-15, the 2022 bear). Spec floor: ≥20. ✅
  - **Risk-on:** longest contiguous run with close > a *rising* SMA200 = **337 trading days**
    (2023-11-01 → 2025-03-07, the 2023–25 bull). Spec floor: ≥40. ✅

## Files Changed

**Backend**
- `config.yaml` — single source of tunables (repo root).
- `apps/backend/requirements.txt` — pinned deps.
- `apps/backend/main.py` — FastAPI app, CORS, lifespan startup.
- `apps/backend/app/config.py` — typed loader + validation (`ConfigError`).
- `apps/backend/app/db.py` — engine/session/create_all (Postgres-ready URL resolution).
- `apps/backend/app/models.py` — the 8 iter-1 SQLModel tables.
- `apps/backend/app/data_providers/base.py` — `PriceProvider` ABC, `Bar`, `ProviderUnavailableError`.
- `apps/backend/app/data_providers/seed_provider.py` — deterministic `SeedProvider`.
- `apps/backend/app/seed_loader.py` — idempotent reference + price load.
- `apps/backend/app/api/health.py` — `GET /api/health`.
- `apps/backend/scripts/ingest_seed.py` — one-shot Yahoo ingest (dev-run; produced the seed).
- `apps/backend/data/seed/prices/*.csv` (158 files) + `apps/backend/data/seed/meta.json` — **committed
  frozen real-EOD fixture** (intentionally tracked).
- `apps/backend/tests/{conftest,test_config,test_seed_provider,test_seed_integrity,test_db,test_health}.py`

**Frontend**
- `apps/frontend/{package.json,next.config.mjs,tsconfig.json,postcss.config.mjs,tailwind.config.ts,components.json,.env.example,.gitignore}`
- `apps/frontend/app/globals.css` — dark palette CSS variables + tabular-nums.
- `apps/frontend/app/layout.tsx` — sidebar + header health badge shell.
- `apps/frontend/app/{page,stocks/page,stocks/[ticker]/page,themes/page,sectors/page,scanner-runs/page,scanner-runs/[runId]/page,system-health/page,watchlist/page}.tsx`
- `apps/frontend/components/{sidebar,health-badge,empty-state,page-heading,ui/card,ui/badge}.tsx`
- `apps/frontend/lib/{api,utils}.ts`

## Tests Run

- **Backend:** `cd apps/backend && .venv/bin/python -m pytest tests/ -v` → **25 passed** (~3s).
  Covers: config load + 6 validation/error cases; SeedProvider determinism + exact-fixture match +
  date filter + the no-fabrication failure path; the **seed-integrity keystone** (both regimes on real
  SPY bars, key symbols present, unique dates); DB exact-table set + idempotent load; `/api/health`
  via TestClient.
- **Frontend:** `cd apps/frontend && npm run build` → **compiled + type-checked successfully**, all 10
  routes generated.
- **Live service boot (offline):** `scripts/start-backend.sh` + `scripts/start-frontend.sh` both start
  with no errors; `/api/health` returns ok; homepage serves HTTP 200 with all 7 nav labels rendered;
  both detail-route stubs (`/stocks/NVDA`, `/scanner-runs/1`) resolve 200. **All test servers were
  killed** after verification.

## Known Issues / Limitations

- **Data source = Yahoo, not Stooq** (forced by Stooq's new captcha/apikey gate — see KEYSTONE above).
  Both are real, free, no-key sources; the committed seed is frozen, so this has no runtime effect.
- **Prices are pre-adjusted; volume is raw.** OHLC are split/dividend-adjusted via Yahoo's adjclose
  factor (continuous long MAs/RS). Volume is stored unadjusted — volume ratios can step at a split.
  Matches the design's "no runtime corporate-action engine" documented limitation.
- **`industries` table is created but not populated** this iteration. Industry-group ETFs are loaded
  into `etfs` (kind=`industry`); the `industries` reference rows arrive with industry scoring (iter-2).
  No iter-1 test/journey needs them.
- **No journey passes (expected).** This is the planned `(infra)` step — J-01…J-11 all remain
  `failing`; the browser pass confirms the shell renders + connects, not a journey.
- A few newer constituents have shorter histories (GEV ~since 2024-04, WGMI ~since 2022-02, ARM ~since
  2023-09); they are NOT in the keystone "key symbols ≥400 bars" set and don't affect this iteration.

## Suggested Next Phase

iter-2 (full): indicators (MAs/RS/ATR%/breadth) + Market Regime engine + Sector/industry scoring,
reading only the committed seed via `bars_asof(symbol, d)` (date ≤ d). Populate the `industries`
reference rows, wire the `regime` config section, and light up J-04 + the regime/sector parts of J-01
on the Dashboard + Sector Leaderboard. Reconcile the `app.engine.*` (blueprint) vs `app/<module>/`
(design) module naming when the first engine module is created.
