You are the qa agent operating in QA VALIDATION mode for phased development.

Phase: goal-ops-hardening-iter-49
Phase spec: /home/dennis-chan/Git/trendora/docs/phases/goal-ops-hardening-iter-49.md
Review report: /home/dennis-chan/Git/trendora/reports/reviews/goal-ops-hardening-iter-49-review.md
Execution plan: /home/dennis-chan/Git/trendora/runs/goal-ops-hardening-iter-49/plan.md
Project template (relevant sections, pre-sliced):
````
## STACK

Define your technology stack. Agents use this to know which commands to run and which files to touch.

```
Backend:
  Language:   <e.g., Python 3.12>
  Framework:  <e.g., FastAPI, Django, Express, Rails>
  ORM/DB lib: <e.g., SQLAlchemy 2.0, Prisma, ActiveRecord>
  Migrations: <e.g., Alembic, Flyway, Prisma Migrate, rake db:migrate>
  Test runner: <e.g., pytest, jest, rspec>
  Package mgr: <e.g., pip + uv, npm, cargo, bundler>
  Venv/env:   <e.g., apps/backend/.venv/, node_modules/ (auto)>

Frontend:
  Enabled:    yes/no
  Framework:  <e.g., Next.js 15 App Router, Vue 3, SvelteKit> (or "N/A")
  Language:   <e.g., TypeScript>
  Styling:    <e.g., CSS modules, Tailwind, styled-components>
  Package mgr: <e.g., npm, pnpm, yarn>

Database:
  Type:       <e.g., SQLite, PostgreSQL, MySQL, MongoDB>
  Location:   <e.g., apps/backend/app.db, postgresql://localhost:5432/mydb>

Services:
  Backend URL:  http://localhost:<port>
  Frontend URL: http://localhost:<port>  (or "N/A")
  Health check: <e.g., http://localhost:8000/health>
```

---

## TEST COMMANDS

Agents will run these to validate their work. Be exact.

```
Backend tests:  <e.g., cd apps/backend && .venv/bin/python -m pytest tests/ -v>
Frontend tests: <e.g., cd apps/frontend && npm test -- --passWithNoTests> (or "N/A")
Migrations:     <e.g., cd apps/backend && .venv/bin/alembic upgrade head> (or "N/A")
Lint:           <e.g., cd apps/backend && .venv/bin/ruff check .> (or "N/A")
```

---

## SERVICE START COMMANDS

Used by qa-phase.sh to auto-start services during QA validation.

```
Start backend:  <e.g., bash scripts/start-backend.sh> (or set CHAIN_START_BACKEND_CMD env var)
Start frontend: <e.g., bash scripts/start-frontend.sh> (or set CHAIN_START_FRONTEND_CMD env var)
```

---
````
Agent instructions: .claude/agents/qa.md  <-- read this first, follow MODE 2 instructions
(CLAUDE.md is already in your system prompt — do not Read it again.)

Frontend Present for this phase: yes
Chrome MCP browser checks ARE required. The frontend should be accessible at http://localhost:3255.

No functional test plan found at /home/dennis-chan/Git/trendora/reports/qa/goal-ops-hardening-iter-49-test-plan.md -- run standard QA checks only.

Note: The QA runner manages backend (http://localhost:8255/api/health, log: /home/dennis-chan/.cache/iad/iad.goal-ops-harde-0c6800fc.91778/qa-backend-8255.log) and frontend (http://localhost:3255, log: /home/dennis-chan/.cache/iad/iad.goal-ops-harde-0c6800fc.91778/qa-frontend-8255.log) for this validation.
Services are restarted automatically if they die during quota-retry sleeps.
You do NOT need to start or stop them yourself.

Write your QA report to: reports/qa/goal-ops-hardening-iter-49-qa.md

The report MUST contain a line matching exactly:
**Verdict:** PASS
  or
**Verdict:** FAIL

Environment note: this pipeline run isolates temp files. Before running tests or any command that writes temporary files, run: export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-0c6800fc.91778" TMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-0c6800fc.91778" TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-0c6800fc.91778"

Note: your agent definition (the .claude/agents/*.md file named above) is already loaded as your system prompt — do not Read it again; treat its 'read this first' pointer as satisfied.
