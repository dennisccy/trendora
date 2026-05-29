# Goal Iteration 1 — Foundation & deterministic spine (FastAPI + config + DB + provider + frozen seed + Next.js shell)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future
- **Iteration:** 1
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** none (infrastructure foundation — **no J-\* journey is expected to pass this
  iteration**; this is the planned "(infra)" step per the roadmap and the iter-0 evaluator). See
  *Journeys unblocked (groundwork only)* below for what this iteration lays the rails for.
- **Journeys unblocked (groundwork only — not targeted to pass):** J-01…J-11 all depend on the spine
  built here (config-driven universe, the committed deterministic seed, the DB schema, the provider
  abstraction, and the nav shell). The first journeys to actually go green are J-04 + part of J-01 in
  iter-2 once indicators/regime/sectors land.
- **Required-still-passing journeys:** none (nothing is passing yet — all 11 are `failing` at baseline).
- **Anti-goal reminders** (verbatim from `docs/goal.md` — these govern this iteration; the four most
  directly engaged this iteration are flagged ⟵ and expanded in NOTES):
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward
    returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future
    bar influences an as-of score. *(critical)* ⟵ *(enabled here: schema + as-of seed window)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or
    overwritten after creation; forward returns live in a separate append-only table keyed to the
    snapshot. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status)
    MUST be computed exactly once by the scoring/regime engine and read identically by every page; the
    API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views.
    *(critical)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe
    entry, and theme definition MUST come from the config file — no such literal in calculation code. ⟵
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/
    unavailable state and MUST NOT synthesize prices or scores to force a green journey. ⟵ **KEYSTONE**
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or
    be reachable; Trendora is research-only. *(critical)* ⟵
  - **No secrets in source.** No hard-coded credentials, API keys, or tokens anywhere; the default seed
    path requires none, and any live-provider key is read only from the environment. ⟵
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks
    "Actionable" (watchlist-only). *(critical)*
  - **Scores must be explainable.** Every displayed score MUST carry its named component breakdown — no
    score may be shown as a bare number with no reasons.
  - **Honest limitations surfaced.** Breadth and new-high/new-low metrics computed from the seed
    universe MUST be labelled "universe-relative" (not full-market internals), and walk-forward
    evidence MUST be labelled as carrying survivorship bias (current-membership universe) so results
    are never overstated.
  - The frontend MUST NOT store auth tokens in `localStorage` (applies only if auth is ever added; this
    version has no auth).

## GOAL

Stand up the deterministic, offline spine the whole product builds on: a FastAPI backend that boots
against a **committed, frozen, real-history seed** and answers `/api/health`, a config-driven
universe/theme definition (`config.yaml`), the SQLModel/SQLite schema needed to load that seed, the
`PriceProvider` abstraction with a deterministic `SeedProvider` default, and a Next.js 15 shell with the
approved sidebar navigation that reads the backend health. No scoring, no journey data yet — this proves
the offline seed spine and frontend↔backend connectivity that every journey will sit on.

## BACKGROUND

This is the **iter-1 foundation** the iter-0 baseline pointed to, dispatched at **full** depth on the
evaluator's recommendation (first real code; broad; crosses backend + frontend; defines the data model;
needs real unit tests beyond a browser smoke; immediately engages four critical anti-goals). The
repository is verified greenfield (no `apps/`, no root `config.yaml`). The blueprint
(`runs/goal-session-i_can_see_the_wealthy_future/state/blueprint.md`) is **approved**, so the 8-page
information architecture and the Data Contract are locked; this iteration builds the empty nav shell for
that IA and the backend spine, **not** any canonical value yet.

The **keystone risk** (carried forward from iter-0 and the design doc §2.3/§9-#15): the seed must be
**real EOD history** — built once by a one-shot Stooq ingest, then committed and frozen — and it must
contain **both** a genuine risk-on stretch (so real Actionable candidates exist for J-02 later) **and** a
genuine risk-off stretch (so a real Risk-Off run exists for J-07 later). Synthesizing or hand-editing
data to manufacture those regimes would violate the *No fabricated data* anti-goal. We turn that risk
into a **real unit test on the real bars** (see TESTING → seed-integrity keystone test).

No `lessons.md` entries exist yet (iter-1 is the first build), so there are none to apply. No
`coherence.md` was produced at baseline (a no-op has no diff), so there is no prior COHERENCE-FAIL to
consolidate — this iteration is free to add the planned foundation scope.

## IN SCOPE

### Backend
- [ ] **App skeleton** under `apps/backend/`: `main.py` exposes the FastAPI `app` (uvicorn entry
      `main:app` via `scripts/start-backend.sh`, `--app-dir apps/backend`, CORS set by the start script);
      package code under `apps/backend/app/` (imported as `app.*`). Startup: load config → create tables
      → load seed if DB empty.
- [ ] **Config loader** `app/config.py` → `load_config()` returning typed (pydantic) settings read from
      the repo-root **`config.yaml`**. Validate required keys (e.g., `provider ∈ {seed, stooq}`, a
      non-empty universe, ETF lists, theme map, bucket edges); raise an explicit error on missing/invalid
      keys. This is the only entry point to tunables — no scoring/threshold/universe/theme literal may be
      hard-coded in code anywhere.
- [ ] **`config.yaml`** authored at repo root as the single source of tunables (structure per design
      §7.6). MUST contain the sections iter-1 consumes: `provider`, `database` (engine URL, default
      SQLite `apps/backend/data/trendora.db`), `universe` (the ~120–150 liquid US common stocks +
      `filters`), the ETF lists (`index`: SPY/QQQ/IWM/RSP; the 11 `sector` ETFs; the `industry` ETFs;
      `^VIX`), `themes` (theme→member-ticker map, many-to-many), and `buckets` (A–E edges). The
      scoring/decision/regime/walk-forward sections MAY be scaffolded now (they are config, not code) but
      are **not consumed** until later iterations — do not wire them this iteration.
- [ ] **DB layer** `app/db.py`: SQLModel engine from `config.database` (no SQLite-only SQL — Postgres-
      ready), session helper, `create_all()` on startup. Create **only the tables iter-1 exercises**:
      `stocks`, `etfs`, `sectors`, `industries`, `themes`, `theme_members`, `daily_prices`
      (unique `(symbol, date)`, indexed `(symbol, date)`), and `data_provider_runs` (data-quality log).
      The snapshot/score/forward/watchlist tables (design §5) are **deferred to their iterations** — do
      not create unused tables this iteration.
- [ ] **Provider abstraction** `app/data_providers/`: `PriceProvider` ABC
      (`get_daily(symbol, start, end) -> bars`) + deterministic **`SeedProvider`** (reads the committed
      frozen fixture; the config default; no network, no keys). On any provider failure it MUST surface an
      explicit unavailable/raised error — it MUST NOT return synthesized bars. (The live `StooqProvider`
      request-path class is **out of scope** this iteration — see below; only the one-shot ingest uses
      Stooq.)
- [ ] **One-shot seed ingest** (standalone script, e.g. `apps/backend/scripts/ingest_seed.py`, run once
      by the developer — **not** on the boot/request path): fetch real daily EOD OHLCV from **Stooq**
      (free, no API key) for every universe symbol + ETF + `^VIX` listed in `config.yaml`, over a window
      wide enough to contain both regimes (guidance: **≈3–4 years** so a sustained risk-off/bear stretch
      *and* a risk-on/bull stretch are both present), write the frozen fixture (CSV or Parquet) under
      `apps/backend/data/seed/`, and **commit it**. After this, the build loop only READS the committed
      files and MUST NOT re-fetch live data mid-loop (re-fetching makes future walk-forward evidence
      irreproducible).
- [ ] **Seed load** on first boot: if the DB has no prices, load the committed seed files into the
      reference tables + `daily_prices`. Idempotent — restarting MUST NOT duplicate rows (the
      `(symbol, date)` uniqueness guards prices); log a `data_provider_runs` row (provider=seed,
      symbols_ok/failed, status).
- [ ] **`GET /api/health`** router → `{"status":"ok", "db_ok": true, "provider": "seed",
      "last_run_date": null, "seed_latest_date": "<max daily_prices.date>", "symbol_count": <n>}`
      (`last_run_date` is null — no scanner run exists yet).
- [ ] **`apps/backend/requirements.txt`** pinned (fastapi, uvicorn, sqlmodel, pydantic, pandas, pyyaml,
      pytest, httpx for the ingest/tests; APScheduler may be listed but no jobs are wired this iteration).

### Frontend
- [ ] **Next.js 15 (App Router) shell** under `apps/frontend/`: persistent **left sidebar** layout
      matching the approved blueprint IA — `Dashboard /`, `Stocks /stocks`, `Themes /themes`,
      `Sectors /sectors`, `Scanner Runs /scanner-runs`, `System Health /system-health`,
      `Watchlist /watchlist`. Each page is an **empty-state placeholder** ("No scan yet — results appear
      once the scanner runs", styled, not a raw string). Boots under `scripts/start-frontend.sh`
      (port 3835; reads `NEXT_PUBLIC_API_URL`).
- [ ] **Detail-route stubs** `/stocks/[ticker]` and `/scanner-runs/[runId]`: minimal empty-state pages so
      the routes resolve (they are reached from rows that do not exist yet — not linked from nav).
- [ ] **Design tokens / shell chrome**: Tailwind + the dark analytical palette from project-template
      DESIGN SYSTEM as CSS variables (`--bg #0a0e14`, `--surface`, `--border`, `--accent #4fd1c5`,
      `--pos`, `--neg`, `--warn`, `--text`, …), monospace `tabular-nums` set up for numeric columns,
      shadcn/ui initialized. New pages must visually match this so iter-2+ pages inherit it.
- [ ] **API client + health badge** `lib/api`: typed fetch wrapper (NO business computation client-side)
      that calls `GET /api/health`; a header/sidebar **status badge** renders backend connectivity +
      `provider` + `seed_latest_date` (and an explicit "backend unavailable" state when the call fails —
      no fabricated "ok"). This is the visible proof the frontend talks to the backend.

### New user-facing capability
The user can open the app and see the **navigable Trendora workstation shell**: the persistent sidebar
with all eight destinations, and a live **backend status badge** confirming the offline seed spine is up
(provider = seed, latest seed date, symbol count). No rankings or scores yet — every page shows a styled
empty state.

### New information displayed
- Backend health/connectivity: status, provider (`seed`), latest seed date, universe symbol count.
- The navigation skeleton itself (the eight destinations of the approved IA).
- Styled empty states on each page describing what will appear once scoring lands.

### New user actions
- Navigate between the eight sidebar destinations.
- (No forms, filters, or data actions yet — those arrive with their journeys.)

### UI surface changes
- New persistent sidebar layout + the seven top-level pages (+ two detail-route stubs), all as empty
  shells in the dense-dark analytical style. New header status badge.

### Product surface delta
The product goes from "nothing runs" to "the workstation shell boots offline against a real committed
seed and proves end-to-end connectivity." It is intentionally data-empty: this iteration earns trust by
standing up a deterministic, reproducible spine, not by showing numbers.

### Blueprint conformance
Conforms to the **already-approved** blueprint with **no edits required**:
- **No nav-skeleton change.** The seven sidebar sections + the two row-reached detail routes
  (`/stocks/[ticker]`, `/scanner-runs/[runId]`) are exactly the approved Information Architecture; this
  iteration *implements* that skeleton as empty shells. → **No** `blueprint.reapproval-requested` is
  written.
- **No new home introduced** — every page created lives under an existing IA section.

### Data-contract additions
**None.** This iteration introduces no new *displayed canonical value*. `GET /api/health` is already
listed in the blueprint Data Contract as the health probe carrying no canonical value. The config, DB
schema, provider abstraction, and seed are infrastructure that the contract's future values will be
computed/served from in iter-2+; nothing new to register now. → **No blueprint.md edit this iteration.**

## OUT OF SCOPE

- Any indicator math, Market Regime / Sector / Theme / stock (Leadership / Entry Quality / Risk) scoring,
  the A–E bucketing function, setup classification, or reason/invalidation text. (iter-2 → iter-4.)
- Scanner runs / immutable snapshots and the snapshot/score tables; walk-forward + forward returns +
  System Health analytics + control groups; watchlist add/persist logic. (iter-5 → iter-7.) Do **not**
  create their DB tables yet.
- The **live `StooqProvider` request-path** (live EOD refresh during a request/boot). Stooq is used
  **only** by the one-shot ingest to BUILD the seed; the running app uses `SeedProvider` over committed
  files and never fetches live in the loop.
- APScheduler jobs (daily scan / forward-return updater).
- Any real data populating the UI pages — empty states only this iteration.
- Re-fetching or mutating the seed after it is committed (would break reproducibility).
- Any order/brokerage/portfolio code path (permanently out of scope per anti-goal).

## DEFINITION OF DONE

- [ ] Backend boots **offline** under `scripts/start-backend.sh` against the committed seed;
      `GET /api/health` returns `{"status":"ok", "db_ok":true, "provider":"seed", "last_run_date":null,
      "seed_latest_date": <date>, "symbol_count": <n>}`.
- [ ] `config.yaml` exists at repo root with `provider`, `database`, `universe` (+`filters`), the ETF
      lists, `themes`, and `buckets`; it is read **only** via `app/config.py`; no scoring/threshold/
      universe/theme/bucket literal is hard-coded in any code path (no-magic-numbers).
- [ ] SQLModel reference tables + `daily_prices` + `data_provider_runs` are created via `create_all()` on
      startup; seed load is **idempotent** (a second boot adds no duplicate rows).
- [ ] The committed frozen seed is **real Stooq EOD history** for the configured universe + ETFs + `^VIX`
      and is **proven** (keystone unit test) to contain **both** a sustained risk-off stretch **and** a
      sustained risk-on stretch — with **no fabricated or hand-edited bars**.
- [ ] `PriceProvider` ABC + deterministic `SeedProvider` (config default) exist; the same call returns
      identical bars across invocations; a provider failure surfaces an explicit unavailable/raised error
      and **never** returns synthesized bars.
- [ ] Next.js 15 shell renders the persistent sidebar (all seven routes + two detail stubs) in the
      dark analytical style; the status badge reads `/api/health` and shows connectivity + provider +
      latest seed date (and an explicit unavailable state on failure).
- [ ] Backend unit tests pass (config load + validation/error case; SeedProvider determinism + failure
      path; seed-integrity keystone; DB create_all + idempotent load; `/api/health` via TestClient);
      frontend `npm run build` succeeds (compiles + typechecks).
- [ ] No anti-goal violated — in particular **No fabricated data**, **No magic numbers**, **No secrets in
      source** (no key needed/committed; `.env*`, `*.db`, `.venv/`, `node_modules/`, `.next/` gitignored),
      and **No order/execution path** (none exists).
- [ ] No journey regresses: J-01…J-11 all remain `failing` (expected — none targeted to pass; the browser
      pass confirms the shell renders and connects, not a journey).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-1-dev.md` (incl. an
      explicit statement of whether the live Stooq ingest succeeded and the seed window/regime coverage).

## TESTING REQUIREMENTS

- **Unit/integration (backend — pytest, `cd apps/backend && .venv/bin/python -m pytest tests/ -v`):**
  - **Config loader:** loads `config.yaml`, returns typed settings, validates required keys; **error
    case** — missing/invalid required key (e.g., unknown `provider`) raises an explicit error (not a
    silent default).
  - **SeedProvider determinism:** a fixed `(symbol, start, end)` returns identical bars on repeated
    calls; values match the committed fixture exactly.
  - **Provider failure path (anti-goal):** a missing symbol / unreadable fixture surfaces an explicit
    unavailable/raised error — assert it does **not** return synthesized/placeholder bars.
  - **Seed-integrity keystone test (anti-goal: No fabricated data):** over the real committed SPY bars,
    assert there exists a **sustained risk-off stretch** (a contiguous run of ≈≥20 trading days with
    close < 200-day SMA) **and** a **sustained risk-on stretch** (a contiguous run of ≈≥40 trading days
    with close > a *rising* 200-day SMA, i.e. SMA200 increasing). Also assert key universe symbols + the
    index/sector ETFs + `^VIX` are present with a reasonable bar count and unique `(symbol, date)`.
    *(These day-count cutoffs are **test parameters** proving a stretch is sustained, not scoring magic
    numbers — scoring config is separate and untouched here.)*
  - **DB:** `create_all()` produces exactly the iter-1 tables; loading the seed twice is idempotent
    (row counts unchanged on the second load).
  - **Health endpoint:** FastAPI `TestClient` → `GET /api/health` returns 200 with `status:"ok"`,
    `db_ok:true`, `provider:"seed"`, and a non-null `seed_latest_date`.
- **Frontend:** `cd apps/frontend && npm run build` compiles and typechecks with no errors.
- **Browser (full pipeline browser-qa — render/connectivity smoke, NOT a journey pass):** with both
  services up, confirm each of the seven sidebar routes loads (HTTP 200, sidebar + styled empty state
  render), the two detail-route stubs resolve, and the status badge shows the backend connected
  (provider = seed, latest seed date). Record explicitly that **no J-\* journey is expected to pass** this
  iteration; this step verifies the shell is present, navigable, and wired to the backend.
- **Error cases:** unknown `provider` in config rejected; missing seed fixture surfaces unavailable (not
  fabricated); frontend renders an explicit "backend unavailable" badge when `/api/health` fails.

## NOTES

- **Four anti-goals are actively engaged this iteration** (flagged ⟵ in metadata):
  1. **No fabricated data (KEYSTONE).** The seed is the foundation of every later journey's evidence; it
     must be genuine Stooq history spanning both regimes, proven by the seed-integrity test on real bars.
     If a 3–4 year window does not exhibit both a sustained risk-off and risk-on stretch, widen the
     window and re-ingest — **never** edit bars to force it. The dev handoff must state the actual window
     and confirm both regimes are present from real data.
  2. **No magic numbers.** `config.yaml` is created now and is the single source of universe, themes, ETF
     lists, and bucket edges; the loader is the only access path. Establishing this contract early is why
     the universe/theme lists live in config from day one, before any scoring consumes weights.
  3. **No secrets in source.** Stooq needs no key; ensure none is added or committed; keep `.env*`,
     `*.db`/`*.db-journal`, `.venv/`, `node_modules/`, `.next/` gitignored (project-template GIT
     WORKFLOW). The committed *frozen seed fixture* is data, not a secret — it is intentionally tracked;
     the runtime `apps/backend/data/trendora.db` stays gitignored.
  4. **No order/execution path.** Trivially satisfied (no such code), but stated so the reviewer/auditor
     confirm nothing brokerage-like is introduced.
- **No-lookahead is *enabled* here, tested later.** The schema (`daily_prices` unique `(symbol, date)`)
  and a sufficiently long seed window are the groundwork for the iter-6 walk-forward and its dedicated
  no-lookahead test; that test is **not** in scope now (no scanner exists), but the seed must be long
  enough (≈3–4 yrs) to support it.
- **Determinism over convenience.** The running app must default to `SeedProvider` and never touch the
  network during boot or a request. The Stooq fetch is a one-shot developer action that produces a
  committed artifact; treat it like a build step, not a runtime dependency.
- **Reproducibility checkpoint for the evaluator:** after this iteration `git diff` should show a real
  `apps/backend` + `apps/frontend` + root `config.yaml` + a committed `apps/backend/data/seed/` fixture,
  and `GET /api/health` should return ok offline — that, plus the passing keystone seed test, is the
  iter-1 success signal (not any journey turning green).
- **References:** design doc §2 (layout), §2.3 (seed), §3 (backend modules), §4 (frontend routes), §5
  (schema — only the iter-1 subset is built now), §6 (`/api/health` shape), §7.6 (`config.yaml` shape),
  §13 (recommended first build task); project-template STACK / DESIGN SYSTEM / TEST + SERVICE START
  COMMANDS / GIT WORKFLOW; blueprint IA + Data Contract (approved).
