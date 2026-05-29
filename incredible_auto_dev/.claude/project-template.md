# Project Configuration

Filled for this project. Agents read this file to understand the stack, conventions, and constraints.

---

## PROJECT GOAL

```
Goal document: docs/goal.md
```

The goal doc defines the vision, target users, success criteria, key capabilities, and non-goals.
All agents read it before starting any iteration. The full architecture/decision record is
`docs/trendora-design.md`. The session blueprint (information architecture + data contract) will live
at `runs/goal-session-trendora/state/blueprint.md` once goal mode starts.

---

## PROJECT

```
Name:        Trendora
Description: Local-first, research-only US-equity leadership scanner. After the close it ranks
             market regime → sectors → industries → themes → stocks, reporting three independent
             scores per stock (Leadership / Entry Quality / Risk), classifies setups, saves immutable
             daily snapshots, and proves its own usefulness via a walk-forward forward-testing engine
             (do high-ranked names/themes beat SPY/QQQ/sector/random peers?). Decision support only —
             no orders, no broker keys.
Repository:  https://github.com/dennisccy/trendora.git
```

---

## STACK

```
Backend:
  Language:    Python 3.12
  Framework:   FastAPI (uvicorn ASGI)
  ORM/DB lib:  SQLModel (SQLAlchemy 2.0 under the hood)
  Migrations:  N/A — SQLModel.metadata.create_all() on startup (no Alembic). Engine URL from config
               (DATABASE_URL) so SQLite→Postgres is a config-only switch; no SQLite-only SQL.
  Test runner: pytest (+ pytest-asyncio where needed)
  Package mgr: pip + venv
  Venv/env:    apps/backend/.venv/   (from apps/backend/requirements.txt)
  Data libs:   Pandas (indicator/return math), APScheduler (daily scan + forward-return jobs)
  HTTP client: httpx — ONLY used by the optional live EOD provider; the DEFAULT provider is the
               committed offline seed (no network, no keys).
  Entry point: apps/backend/main.py exposes `app` (FastAPI). uvicorn runs `main:app` with
               --app-dir apps/backend (see start-backend.sh). Package code lives under apps/backend/app/.

Frontend:
  Enabled:     yes
  Framework:   Next.js 15 (App Router)
  Language:    TypeScript
  Styling:     Tailwind CSS + shadcn/ui
  Charts:      Lightweight-Charts (candles/MAs/volume); Recharts acceptable for simple bar/line panels
  Package mgr: npm
  Reads env:   NEXT_PUBLIC_API_URL (base URL of the backend API)

Database:
  Type:        SQLite (Postgres-ready via DATABASE_URL)
  Location:    apps/backend/data/trendora.db   (gitignored; created at runtime)

Services:
  Backend URL:  http://localhost:8835    (auto-offset per project path; honors CHAIN_BACKEND_PORT)
  Frontend URL: http://localhost:3835    (auto-offset per project path; honors CHAIN_FRONTEND_PORT)
  Health check: http://localhost:8835/api/health   (returns {"status":"ok", ...})
```

---

## DESIGN SYSTEM

```
Component library: shadcn/ui (Radix + Tailwind)
Icon library:      Lucide (sparingly; numbers and status dots/badges carry the signal)

Visual style:      dense, dark, data-forward analytical workstation (reference: gap_gap_filler /
                   finovae_strategy_platform). Skeptical and evidence-driven — invalidation levels,
                   reason components, sample sizes, and honest limitations are always visible.
Color mode:        dark

Color palette (Tailwind tokens / CSS variables):
  Background:     #0a0e14   (--bg)
  Surface:        #111722   (--surface)   / #18202d (--surface-2)
  Border:         #232c3b   (--border)    / #303d52 (--border-strong)
  Accent:         #4fd1c5   (--accent, teal)
  Positive:       #34d399   (--pos, green — strength / positive forward return)
  Negative:       #f87171   (--neg, red — risk / negative forward return)
  Warning/stale:  #fbbf24   (--warn — stale data, caution, low sample size)
  Text primary:   #e6edf3   (--text)
  Text muted:     #8b98a9   (--text-muted) / #5b6677 (--text-faint)

Score buckets (foregrounded over raw numbers):
  A (90+) strongest → E (<60) weakest, colour-graded green→red; raw 0–100 shown secondary.

Typography:
  Font family:    system sans for labels; monospace (tabular-nums) for ALL numbers (scores, prices,
                  returns) so columns align.
Spacing:          4px grid (Tailwind default). No arbitrary pixel values.
Responsive:       single mobile breakpoint ~640px; tables become horizontally scrollable.
```

Discipline: the UI re-formats values from the API only — it NEVER recomputes a score, bucket, or
forward return client-side. Colour-coding uses palette tokens only.

---

## TEST COMMANDS

```
Backend tests:   cd apps/backend && .venv/bin/python -m pytest tests/ -v
Frontend tests:  cd apps/frontend && npm run build
                 (compiles + typechecks; UI behaviour is covered by browser QA, not a unit suite)
Migrations:      N/A (SQLModel create_all on startup)
Lint:            N/A (none configured for MVP)
```

First-time setup the start scripts assume already done:
- Backend: `python3 -m venv apps/backend/.venv && apps/backend/.venv/bin/pip install -r apps/backend/requirements.txt`
- Frontend: `cd apps/frontend && npm install`

---

## SERVICE START COMMANDS

```
Start backend:  bash scripts/start-backend.sh    (auto-offset port 8835; honors CHAIN_BACKEND_PORT; sets CORS)
Start frontend: bash scripts/start-frontend.sh   (auto-offset port 3835; honors CHAIN_FRONTEND_PORT; sets NEXT_PUBLIC_API_URL)
```

---

## PHASE SPECS

```
Phase spec directory:   docs/phases/
Phase spec naming:      goal-<session-id>-iter-<N>.md   (goal mode)
```

---

## ROADMAP

Goal mode (`./scripts/automation/run-goal.sh --session-id trendora`). The decomposer chooses order
adaptively from failing journeys; this is the expected sequence.

| Iteration | Focus | Journeys |
|-----------|-------|----------|
| iter-0 | Baseline verify (greenfield) | — |
| iter-1 | Foundation: FastAPI /api/health + config loader + SQLModel models + provider abstraction + SeedProvider + **one-shot ingest → build & commit the frozen seed (real Stooq EOD; risk-on + risk-off stretches)** + seed load + Next.js shell | (infra) |
| iter-2 | Indicators + Regime + Sectors → Sector Leaderboard + dashboard parts | J-04, part J-01 |
| iter-3 | Themes + 3 stock scores + bucketing (canonical values) + Stock & Theme Leaderboards | J-02, J-03, J-06, rest J-01 |
| iter-4 | Setups + reasons + invalidation + Stock Detail (chart + breakdowns) + regime-gating logic | J-05 |
| iter-5 | Scanner snapshots + Scanner Runs pages (immutability); seed a Risk-Off historical run + ≥1 earlier run | J-07, J-08 |
| iter-6 | Walk-forward + forward returns + aggregates + control groups + System Health | J-09, J-10 |
| iter-7 | Watchlist (persistence) + polish | J-11 |

Deferred to later sessions: paper portfolio, news/LLM enrichment.

---

## ARCHITECTURE PRINCIPLES

```
- The backend is the single source of truth; the frontend only re-formats values from the API.
- The SIX canonical values — Market Regime, Sector Score, Theme Score, Leadership, Entry Quality,
  Risk (plus the A–E bucket and setup status) — are each computed EXACTLY ONCE in the scoring/regime
  engine and read identically by every page. No recomputation in the API or frontend.
- NO MAGIC NUMBERS: every scoring weight, threshold, decision-rule cutoff, bucket edge, universe
  entry, and theme definition comes from config.yaml. No such literal in calculation code.
- NO LOOKAHEAD: scoring for a snapshot dated D uses only price bars with date ≤ D; forward returns use
  only bars with date > D. This MUST be unit-tested.
- Scanner snapshots are IMMUTABLE: a scanner_run and its result rows are never updated after creation;
  forward_returns is a separate append-only table keyed to (run_id, stock_id, horizon).
- Every score is EXPLAINABLE: it carries its named component breakdown (component → contribution),
  which is the source of the reason summary. No black-box scores.
- Provider abstraction: SeedProvider (offline, deterministic) is the DEFAULT; a live EOD provider is
  config-selected. On provider failure, surface an explicit stale/unavailable state — NEVER fabricate
  prices or scores to force a green journey.
- NO order-placement / brokerage / capital-deployment code path may exist or be reachable. Trendora is
  research/decision-support only. Structure code so paper-portfolio and news COULD be added later, but
  neither exists in this session.
- Risk-Off regime gates Actionable: when regime is Risk-Off, zero stocks are marked "Actionable".
- Surface honest limitations: breadth / new-high-low are universe-relative (not full-market internals);
  walk-forward evidence carries survivorship bias; small samples are labelled with n.
```

---

## DATA MODEL RULES

```
- SQLModel models; integer auto-increment primary keys; engine URL from config (DATABASE_URL).
- Dates stored as ISO date/datetime; daily_prices unique on (symbol, date), indexed (symbol, date).
- Score component breakdowns stored as JSON text columns (components_json).
- Snapshot tables (scanner_runs, *_scores, setup_classifications, scanner_results) are append-only.
- forward_returns is a SEPARATE table keyed to (run_id, stock_id, horizon) — the snapshot is never mutated.
- paper_portfolios / paper_portfolio_positions are DESIGNED but NOT created this session.
```

---

## GIT WORKFLOW

```
Branch naming:      goal/<session-id>   (goal mode manages branches; default goal/trendora)
PR title format:    goal(<session-id>): iter <N> — <summary>
Main branch:        main
Never commit:
  - apps/backend/.venv/                 (Python virtualenv)
  - apps/frontend/node_modules/ , apps/frontend/.next/
  - apps/backend/data/trendora.db        (and *.db / *.db-journal)
  - .env / .env.*                        (only .env.example is tracked)
  - any API keys, secrets, or credentials (the offline seed path needs none)
```

---

## NOTES FOR AGENTS

```
- The app lives under apps/ (apps/backend, apps/frontend) so it never clobbers the embedded dev-chain
  root symlinks (config, scripts, tests, templates, .claude, CLAUDE.md).
- DEFAULT data provider is the committed offline seed (apps/backend/data/seed/) — no network, no keys.
  Build and verify everything against the seed; the live provider is optional and config-selected.
- BUILD THE SEED IN iter-1: a one-shot ingest script fetches real EOD history from Stooq (free, no key)
  for the universe + ETFs, then COMMITS and FREEZES it. After that the build loop only READS the
  committed files and MUST NOT re-fetch live data mid-loop (re-fetching makes the walk-forward evidence
  irreproducible). The live provider is for going-forward refresh OUTSIDE the loop, not the build.
- The seed window must contain BOTH a risk-on stretch (real Actionable candidates for J-02) and a
  risk-off stretch (a real Risk-Off run for J-07). Use real history; do not fabricate data to pass journeys.
- Browser journeys assert RELATIONAL / STRUCTURAL properties (same value in two places, buckets
  ordered, zero Actionable in risk-off, a number renders, filters change rows) — NOT exact score
  numbers — so tuning weights in config.yaml never breaks a journey.
- This project-template.md and config.yaml live in the trendora repo's subtree copy of the dev-chain;
  do NOT `git subtree push` project-specific config upstream to incredible_auto_dev.
- config.yaml at the repo root holds ALL tunables (weights, thresholds, universe, themes, provider,
  walk-forward params). Read it via the backend config loader; never hard-code these in calc code.
```
