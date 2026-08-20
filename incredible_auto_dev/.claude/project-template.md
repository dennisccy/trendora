# Project Configuration — Trendora

Filled 2026-08-20 (was the unfilled framework template; agents previously had no
authoritative commands and improvised — including resource-heavy test runs).
Agents read this file to understand the stack, conventions, and constraints.

---

## PROJECT GOAL

```
Goal document: docs/goal.md
```

`docs/goal.md` is the binding product contract (vision, Must-have journeys J-01…,
anti-goals AG-1…, binding traps). All agents read it before any phase/iteration.

---

## PROJECT

```
Name:        Trendora
Description: Deterministic US-equity market scanner — 30 years of daily history,
             append-only scanner snapshots, evidence-gated signals, and a
             next-session "market compass" UI.
Repository:  git@github.com:dennisccy/trendora.git
```

---

## STACK

```
Backend:
  Language:   Python 3.12 (venv pinned 3.12.13)
  Framework:  FastAPI 0.115.6 + uvicorn 0.34.0 (entry: apps/backend/main.py)
  ORM/DB lib: SQLModel 0.0.22 (SQLAlchemy 2.x) — tables in app/models.py
  Migrations: NONE (no Alembic). Schema evolves via additive ALTER TABLE in
              app/db.py at startup — add-column only, never destructive.
  Test runner: pytest 8.3.4 + pytest-asyncio 0.25.0 (single-process; xdist NOT installed)
  Package mgr: pip (apps/backend/requirements.txt, pinned)
  Venv/env:   apps/backend/.venv/

Frontend:
  Enabled:    yes
  Framework:  Next.js 15.1.3 App Router (apps/frontend/app/)
  Language:   TypeScript
  Styling:    Tailwind (class-based dark mode) + shadcn-style components in
              apps/frontend/components/ui/
  Package mgr: npm

Database:
  Type:       SQLite (WAL). All pragmas/pool sizing come from root config.yaml
              `database:` — the ONLY place tunables live (anti-goal: no magic numbers).
  Location:   apps/backend/data/trendora.db  (~7.8 GB, gitignored — see NOTES)

Services:
  Backend URL:  http://localhost:8000   (CHAIN_BACKEND_PORT overrides)
  Frontend URL: http://localhost:3000   (CHAIN_FRONTEND_PORT overrides)
  Health check: http://localhost:8000/api/health
```

---

## DESIGN SYSTEM

```
Component library: shadcn-style primitives in apps/frontend/components/ui/
                   (Card, Badge, Disclosure, …) — reuse these, do not add a new library
Icon library:      lucide-react

Visual style:      data-dense analytical dashboard; restrained, evidence-first
Color mode:        class-based dark mode (tailwind.config.ts darkMode: ["class"])

Color palette:     Defined as CSS custom properties in apps/frontend/app/globals.css
                   and mapped in tailwind.config.ts — extend THOSE tokens; never
                   hard-code new hex values in components.

Typography:        Font families defined in tailwind.config.ts fontFamily; Tailwind
                   default type scale (text-sm/base/lg/xl/2xl).

Spacing:           Tailwind default 4px grid.

Effects:           Subtle only (existing transitions/borders). No new glows/gradients
                   without a journey that asks for them.

Responsive:        Tailwind defaults (sm 640 / md 768 / lg 1024 / xl 1280).
```

---

## TEST COMMANDS

Agents will run these to validate their work. Be exact.

```
Backend tests (TARGETED ONLY — the only sanctioned form):
    cd apps/backend && .venv/bin/python -m pytest tests/test_<module>.py -v
  Run ONLY the test files for the modules you touched (plus any new test files).
  New tests must be file-scoped with small synthetic fixtures (docs/goal.md:
  "the full suite takes hours and is never run by pipeline agents").

Frontend "tests" = the production compile + typecheck:
    cd apps/frontend && npm run build
Migrations:     N/A (additive ALTERs run automatically at backend startup)
Lint:           frontend: cd apps/frontend && npm run lint
                backend:  N/A (no linter pinned; the post-edit hook py_compiles)
```

**NEVER (resource contract — a 26.7 GB host; violations have frozen the machine):**
- NEVER run the full backend suite (`pytest tests/`, `pytest` bare, or `-k`-wide
  sweeps). It builds the 30-year `loaded_engine` fixture — multi-GB resident,
  multi-hour wall — and is run only by the owner via `scripts/run_iter18_fullsuite.sh`.
- NEVER run two pytest processes concurrently (each can hold a multi-GB fixture).
- NEVER copy, move, or open-for-write `apps/backend/data/trendora.db` (7.8 GB).
  The memory-pressure test modules that copy it are owner-run only.
- NEVER start a second backend/frontend when the canonical ports (8000/3000 or
  the CHAIN_* pins) already answer — reuse the running service.

---

## SERVICE START COMMANDS

Used by qa-phase.sh to auto-start services during QA validation.

```
Start backend:  bash scripts/start-backend.sh    (applies config.yaml server caps:
                ulimit -v memory_cap_mb, MALLOC_ARENA_MAX, uvicorn limit-concurrency)
Start frontend: bash scripts/start-frontend.sh   (builds only when stale, then next start)
```

Always start services through these scripts — they carry the HOST-GUARD cap blocks
(stripping those blocks is a REGRESSION per docs/goal.md AG-10).

---

## PHASE SPECS

```
Phase spec directory:   docs/phases/
Phase spec naming:      goal-<session>-iter-<N>.md (goal mode) / <phase-id>-<name>.md
```

---

## ROADMAP

Goal-mode project — the roadmap IS `docs/goal.md`'s Must-have journeys plus
`runs/goal-session-<sid>/journey-history.json`. This table is not used.

| Phase | Name | Status |
|-------|------|--------|
| goal: market-compass | see docs/goal.md journeys | 🔄 In Progress |

---

## ARCHITECTURE PRINCIPLES

```
- No magic numbers: every threshold/weight/tunable lives in root config.yaml and is
  loaded through the typed loader in app/config.py (tests/test_no_magic_numbers.py
  enforces this). Never inline a numeric decision value in engine code.
- Single producer / canonical values: displayed values are served from stored
  snapshots (app/engine/snapshot_serving.py) or the evidence resolver
  (app/engine/evidence.py, which RECOMPUTES NOTHING). Never recompute a Data
  Contract value in a new code path — the coherence audit hard-fails it.
- Scanner snapshots are append-only; a resolved ScannerRun is immutable.
- Evidence gating: an unbacked signal renders "Not yet proven", never a confident
  number (docs/goal.md anti-goal).
- Frontend contains no business logic — it calls the backend via
  apps/frontend/lib/api.ts typed fetchers only.
- Keep API routes thin: engine logic lives in app/engine/*, routes in app/api/*.
```

---

## DATA MODEL RULES

```
- SQLModel tables in app/models.py; schema changes are additive-only ALTERs wired
  in app/db.py (add nullable columns; index changes use explicit named ix_/uq_).
- Dates are trading-day ISO strings (YYYY-MM-DD); "as-of" semantics everywhere.
- JSON columns only where the spec explicitly calls for schema flexibility.
```

---

## GIT WORKFLOW

```
Branch naming:      goal/<session-id> (goal mode) / phase/<phase-id>
PR title format:    feat: <iter/phase id> — <one-line summary>
Main branch:        main
Never commit:
  - .env, credentials.json, any secrets
  - *.db / apps/backend/data/ (7.8 GB live database — gitignored; keep it that way)
  - node_modules/, .venv/, .next*/ build output
  - seed CSVs beyond the committed seed set
```

---

## NOTES FOR AGENTS

```
- RESOURCE BUDGET IS BINDING (docs/goal.md AG-10): this is a 26.7 GB / 16-thread
  host shared with a desktop session and a sibling project. The backend runs under
  ulimit -v memory_cap_mb (config.yaml server:) — treat OOM/MemoryError inside the
  backend as a real product bug, not an environment nuisance.
- 2026-08-20 incident: goal-mode runs froze the desktop via memory overcommit +
  swap-thrash. The mitigations are the TEST COMMANDS never-list above and the
  resource-fit work in docs/goal.md — do not undo either.
- The full 30-year dataset is the committed seed (docs/goal.md AG-9: no network
  ingest). Product boots fast; only the full test suite is slow — do not conflate.
- Long-running commands: prefer targeted work; anything expected to exceed ~10
  minutes belongs to the owner, not a pipeline agent, unless the iteration spec
  says otherwise.
```
