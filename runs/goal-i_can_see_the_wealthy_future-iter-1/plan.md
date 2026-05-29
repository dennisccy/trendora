# goal-i_can_see_the_wealthy_future-iter-1 Execution Plan

Foundation & deterministic spine. First real code. Builds the offline seed-driven backend
(`/api/health`) + the Next.js nav shell. **No scoring, no journey data** — every page is a styled empty
state. Target journeys: **none** (infra). The success signal is a real `apps/` tree + committed seed +
`/api/health` returning ok offline + the passing keystone seed-integrity test — *not* any journey going
green. (Confirmed against goal.md, the approved blueprint, the design doc, and the roadmap: **no drift**.)

## What to Build

**Backend** (`apps/backend/`, uvicorn `main:app` via `scripts/start-backend.sh`, `--app-dir apps/backend`):
- App skeleton: `main.py` exposes FastAPI `app`; CORS read from the `CORS_ORIGINS` env var (set by the start script); startup order = **load config → create tables → load seed if DB empty**.
- `app/config.py` → `load_config()` returning typed (pydantic) settings from the **repo-root `config.yaml`**. The *only* access path to tunables. Validate keys iter-1 consumes (`provider ∈ {seed, stooq}`, non-empty `universe`, ETF lists, `themes` map, `buckets` edges, `database`); raise an explicit error on missing/invalid (no silent default).
- `config.yaml` at repo root — single source of tunables: `provider`, `database` (engine URL; default SQLite `apps/backend/data/trendora.db`), `universe` (~120–150 liquid US common stocks + `filters`), ETF lists (`index`: SPY/QQQ/IWM/RSP; 11 `sector` ETFs; `industry` ETFs; `^VIX`), `themes` (theme→tickers, many-to-many), `buckets` (A–E edges). Scoring/regime/decision/walk-forward sections **may be scaffolded** but are **not consumed/wired** this iteration.
- `app/db.py`: SQLModel engine from `config.database` (no SQLite-only SQL — Postgres-ready), session helper, `create_all()` on startup. Create **only iter-1 tables**: `stocks`, `etfs`, `sectors`, `industries`, `themes`, `theme_members`, `daily_prices` (unique + indexed `(symbol, date)`), `data_provider_runs`. Snapshot/score/forward/watchlist tables are **deferred** — do not create them.
- `app/data_providers/`: `PriceProvider` ABC (`get_daily(symbol, start, end) -> bars`) + deterministic `SeedProvider` (reads committed fixture; config default; no network, no keys). On failure → explicit unavailable/raised error; **MUST NOT** return synthesized bars. (Live `StooqProvider` request-path class is **out of scope**.)
- **One-shot seed ingest** `apps/backend/scripts/ingest_seed.py` (dev runs ONCE, *not* on boot/request path): fetch real daily EOD OHLCV from **Stooq** (free, no key) for every universe symbol + ETF + `^VIX`, over **≈3–4 years** (must span both a risk-off and a risk-on stretch), write a frozen fixture (CSV/Parquet) under `apps/backend/data/seed/`, and **commit it**. Loop then only READS it.
- Seed load on first boot (idempotent — `(symbol, date)` uniqueness guards against duplicate rows on restart); log a `data_provider_runs` row (provider=seed, symbols_ok/failed, status).
- `GET /api/health` → `{"status":"ok", "db_ok":true, "provider":"seed", "last_run_date":null, "seed_latest_date":"<max daily_prices.date>", "symbol_count":<n>}`.
- `apps/backend/requirements.txt` pinned (fastapi, uvicorn, sqlmodel, pydantic, pandas, pyyaml, pytest, httpx; APScheduler may be listed but no jobs wired).

**Frontend** (`apps/frontend/`, Next.js 15 App Router, `scripts/start-frontend.sh`, reads `NEXT_PUBLIC_API_URL`):
- Persistent **left-sidebar** layout matching the approved IA — 7 nav routes: `Dashboard /`, `Stocks /stocks`, `Themes /themes`, `Sectors /sectors`, `Scanner Runs /scanner-runs`, `System Health /system-health`, `Watchlist /watchlist`. Each is a **styled empty-state placeholder** (e.g. "No scan yet — results appear once the scanner runs"), not a raw string.
- Two **detail-route stubs** so routes resolve: `/stocks/[ticker]`, `/scanner-runs/[runId]` (reached from rows that don't exist yet — not in nav).
- Design tokens (Tailwind + dark analytical palette as CSS vars), `tabular-nums` monospace for numerics, shadcn/ui initialized. iter-2+ pages inherit this chrome.
- `lib/api` typed fetch wrapper (NO client-side business computation) calling `GET /api/health`; a header/sidebar **status badge** showing connectivity + `provider` + `seed_latest_date`, with an explicit **"backend unavailable"** state on failure (no fabricated "ok").

## Agents Required
- developer: yes -- implements both the backend spine and the frontend shell below (single phase, TDD).
- backend-data: yes -- `config.yaml` + config loader, SQLModel schema (iter-1 subset), `PriceProvider`/`SeedProvider`, one-shot Stooq ingest + committed seed, idempotent seed load, `GET /api/health`, pytest suite.
- frontend-ux: yes -- Next.js 15 shell, sidebar (7 routes + 2 detail stubs), dark design tokens + shadcn/ui, `lib/api` client + live health badge with unavailable state.

## Frontend Present
Frontend Present: yes

## Files to Create/Modify
Backend:
- `config.yaml` (repo root) -- single source of tunables (provider/database/universe/ETFs/themes/buckets; scoring may be scaffolded, not wired).
- `apps/backend/main.py` -- FastAPI `app`, CORS from `CORS_ORIGINS`, startup (load config → create_all → seed-if-empty), include `/api` routers.
- `apps/backend/app/__init__.py`, `apps/backend/app/config.py` -- typed config loader + key validation.
- `apps/backend/app/db.py` -- engine from config, session helper, `create_all()`.
- `apps/backend/app/models.py` -- SQLModel iter-1 tables (or `app/models/` package): stocks, etfs, sectors, industries, themes, theme_members, daily_prices, data_provider_runs.
- `apps/backend/app/data_providers/base.py` (`PriceProvider` ABC), `apps/backend/app/data_providers/seed_provider.py` (`SeedProvider`).
- `apps/backend/app/seed_loader.py` -- idempotent first-boot load + `data_provider_runs` row.
- `apps/backend/app/api/health.py` -- `GET /api/health` router.
- `apps/backend/scripts/ingest_seed.py` -- one-shot Stooq ingest (dev-run; produces & commits the frozen fixture).
- `apps/backend/data/seed/` -- **committed** frozen real-EOD fixture (CSV/Parquet). The runtime `apps/backend/data/trendora.db` stays gitignored.
- `apps/backend/requirements.txt` -- pinned deps.
- `apps/backend/tests/` -- `test_config.py`, `test_seed_provider.py`, `test_seed_integrity.py` (keystone), `test_db.py`, `test_health.py`.

Frontend:
- `apps/frontend/` scaffold -- `package.json`, `next.config.*`, `tsconfig.json`, `tailwind.config.*`, `postcss.config.*`, `components.json` (shadcn), `.env.example` (NEXT_PUBLIC_API_URL).
- `apps/frontend/app/globals.css` -- dark palette CSS variables + tabular-nums.
- `apps/frontend/app/layout.tsx` -- root layout: sidebar + header health badge.
- `apps/frontend/app/page.tsx`, `app/stocks/page.tsx`, `app/stocks/[ticker]/page.tsx`, `app/themes/page.tsx`, `app/sectors/page.tsx`, `app/scanner-runs/page.tsx`, `app/scanner-runs/[runId]/page.tsx`, `app/system-health/page.tsx`, `app/watchlist/page.tsx` -- empty-state pages / detail stubs.
- `apps/frontend/components/sidebar.tsx`, `components/health-badge.tsx`, `components/empty-state.tsx`, `components/ui/*` (shadcn).
- `apps/frontend/lib/api.ts` -- typed `/api/health` fetch wrapper.

*Gitignore: `.venv`, `*.db`/`*.db-journal`, `node_modules/`, `.next`, `.env*` (keeps `.env.example`) are already covered — no gitignore change needed. The seed fixture under `apps/backend/data/seed/` is intentionally tracked.*

## UI Evolution (Frontend Present: yes)
- New user-facing capability: open the app and see the **navigable Trendora workstation shell** — the persistent sidebar with all eight destinations and a live backend status badge proving the offline seed spine is up.
- New information displayed: backend connectivity (status), provider (`seed`), latest seed date, universe symbol count; the navigation skeleton; styled per-page empty states describing what arrives once scoring lands.
- New user actions: navigate between the seven sidebar destinations (no forms/filters/data actions yet).
- UI surface changes: new persistent sidebar layout + 7 top-level pages + 2 detail-route stubs (all empty shells, dense-dark analytical style); new header status badge.
- Navigation changes: the full approved sidebar (Dashboard, Stocks, Themes, Sectors, Scanner Runs, System Health, Watchlist) added — exactly the approved IA, **no blueprint change / no re-approval requested**.

## Visual Requirements (Frontend Present: yes)
- Component patterns: shadcn/ui (Card for empty-state panels, Badge/status dot for the health badge, sidebar nav links). No raw `<div>` soup where a component exists.
- Layout: left persistent sidebar + main content area; single mobile breakpoint ~640px (wide tables scroll later). Dashboard-grid scaffolding for iter-2 cards.
- Key visual effects: dense-dark analytical workstation — palette tokens only (`--bg #0a0e14`, `--surface`, `--border`, `--accent #4fd1c5`, `--pos`, `--neg`, `--warn`, `--text`, `--text-muted`); numbers in monospace `tabular-nums`. No flashy consumer-trading aesthetic; no arbitrary hex/px/font sizes.
- States to handle: **empty** (every page this iteration — styled empty-state, not a bare string) and **error/unavailable** (health badge shows an explicit "backend unavailable" state when `/api/health` fails — never a fabricated "ok"). Loading state on the badge while the health call is in flight.

## Key Test Scenarios
Backend (`cd apps/backend && .venv/bin/python -m pytest tests/ -v`):
- **Config loader:** loads `config.yaml` → typed settings; **error case** — unknown `provider` (or missing required key) raises an explicit error, not a silent default.
- **SeedProvider determinism:** fixed `(symbol, start, end)` returns identical bars on repeated calls, matching the committed fixture exactly.
- **Provider failure (anti-goal):** missing symbol / unreadable fixture surfaces an explicit unavailable/raised error — assert it does **not** return synthesized/placeholder bars.
- **Seed-integrity keystone (anti-goal: No fabricated data):** on the real committed SPY bars, assert a sustained **risk-off** stretch (contiguous ≈≥20 trading days with close < SMA200) **and** a sustained **risk-on** stretch (contiguous ≈≥40 days with close > a *rising* SMA200) both exist; assert key universe symbols + index/sector ETFs + `^VIX` are present with reasonable bar counts and unique `(symbol, date)`. *(These day-counts are test parameters, not scoring magic numbers.)*
- **DB:** `create_all()` produces exactly the iter-1 tables; loading the seed twice is idempotent (row counts unchanged on the second load).
- **Health endpoint:** `TestClient` → `GET /api/health` is 200 with `status:"ok"`, `db_ok:true`, `provider:"seed"`, non-null `seed_latest_date`.

Frontend: `cd apps/frontend && npm run build` compiles + typechecks with no errors.

Browser (render/connectivity smoke — **NOT a journey pass**): with both services up, each of the 7 sidebar routes loads (HTTP 200, sidebar + styled empty state render), the 2 detail-route stubs resolve, and the status badge shows the backend connected (provider = seed, latest seed date). Plus error case: badge shows "backend unavailable" when `/api/health` fails. **Record explicitly that no J-\* journey is expected to pass this iteration** — all 11 remain `failing` (expected, not a regression).

## Assumptions, Risks & Scope Flags
- **KEYSTONE RISK — real seed, no fabrication.** The seed must be genuine Stooq EOD history. The one-shot `ingest_seed.py` is the *only* step that needs **network access** (Stooq, no key, dev-time only). If a 3–4 yr window doesn't exhibit both a sustained risk-off and risk-on stretch, **widen the window and re-ingest — never edit bars** to force it. The keystone test runs on the real committed bars. The dev handoff **must** state whether the live ingest succeeded and the actual seed window + confirmed regime coverage (per DoD). Approach is locked by spec; not a user decision.
- **Determinism over convenience.** The running app defaults to `SeedProvider` and must never touch the network on boot or request. Stooq is a one-shot build step, not a runtime dependency; the loop must not re-fetch (re-fetching breaks later walk-forward reproducibility).
- **Four anti-goals actively engaged:** No fabricated data (keystone), No magic numbers (config-only tunables via the loader), No secrets in source (Stooq needs none; keep `.env*`/`*.db`/`.venv`/`node_modules`/`.next` ignored), No order/execution path (none exists — confirm nothing brokerage-like is introduced).
- **Ports / CORS auto-wired:** `scripts/start-backend.sh` / `start-frontend.sh` derive per-project offset ports and set `CORS_ORIGINS` + `NEXT_PUBLIC_API_URL`. `main.py` must read `CORS_ORIGINS`, or browser QA hits CORS errors. No Alembic (the start script's alembic block is skipped — `create_all()` only).
- **Deferred-decision note (non-blocking):** the blueprint Data Contract proposes engine module paths as `app.engine.*` while the design doc uses `app/<module>/`; **no engine module is created this iteration**, so reconcile that naming when scoring lands in iter-2 — nothing to decide now.
- **No questions for the user:** the spec is exhaustive and internally consistent with goal.md, the approved blueprint, the design doc, and the roadmap; Stooq requires no credentials. Assumptions above are documented rather than blocked, per the token policy.
