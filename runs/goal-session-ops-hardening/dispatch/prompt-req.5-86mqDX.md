You are the reviewer agent for phased development.

Phase: goal-ops-hardening-iter-50
Phase spec: /home/dennis-chan/Git/trendora/docs/phases/goal-ops-hardening-iter-50.md
Dev handoff: /home/dennis-chan/Git/trendora/docs/handoffs/goal-ops-hardening-iter-50-dev.md
Execution plan: /home/dennis-chan/Git/trendora/runs/goal-ops-hardening-iter-50/plan.md
Project template (relevant sections, pre-sliced):
````
## ARCHITECTURE PRINCIPLES

List project-specific rules ALL agents must follow when writing code.
Example:
- Keep API routes thin — business logic lives in services, not routers
- All database access goes through the repository layer
- Frontend never contains business logic — calls backend APIs only
- Every resource has explicit status transitions; invalid transitions are rejected

```
- <principle 1>
- <principle 2>
- <principle 3>
```

---

## DESIGN SYSTEM

Define your project's visual identity. Agents use this to ensure consistent, polished UI output.

```
Component library: <e.g., shadcn/ui, Radix + Tailwind, Material UI, Chakra UI>
Icon library:      <e.g., Lucide, Heroicons, Phosphor>

Visual style:      <e.g., cyber-dark, minimal-light, corporate-clean>
Color mode:        <dark / light / system>

Color palette:
  Background:      <e.g., #0a0a0f — deep dark base>
  Surface:         <e.g., #12121a — card/panel background>
  Border:          <e.g., #1e1e2e — subtle borders>
  Primary:         <e.g., #00f0ff — neon cyan accent>
  Secondary:       <e.g., #7c3aed — electric purple>
  Success:         <e.g., #10b981>
  Warning:         <e.g., #f59e0b>
  Danger:          <e.g., #ef4444>
  Text primary:    <e.g., #e2e8f0 — high contrast on dark>
  Text muted:      <e.g., #64748b>

Typography:
  Font family:     <e.g., Inter for body, JetBrains Mono for code/data>
  Scale:           <e.g., Tailwind default: text-sm/base/lg/xl/2xl>

Spacing:           <e.g., Tailwind default 4px grid: p-1/p-2/p-3/p-4/p-6/p-8>

Effects (use sparingly):
  - <e.g., glassmorphism on cards: backdrop-blur-md bg-white/5 border border-white/10>
  - <e.g., glow on primary actions: shadow-[0_0_15px_rgba(0,240,255,0.3)]>
  - <e.g., subtle gradient borders on hero sections>
  - <e.g., smooth transitions: transition-all duration-200>

Responsive breakpoints: <e.g., sm:640px md:768px lg:1024px xl:1280px>
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
````
Agent instructions: .claude/agents/reviewer.md  <-- read this first
(CLAUDE.md is already in your system prompt — do not Read it again.)

Read the phase spec, the dev handoff, and each changed file listed in the handoff.
Bounded diff packet (read FIRST if present): /home/dennis-chan/Git/trendora/runs/goal-ops-hardening-iter-50/review-packet.md — hunks capped, noise excluded, truncations NAMED. The phase spec + dev handoff remain required reading — never verdict from the diff alone (D7).
Run these only for files the packet marks truncated or excluded (or if the packet file is absent):
Run: git diff HEAD -- . ':(exclude)*package-lock.json' ':(exclude)*yarn.lock' ':(exclude)*pnpm-lock.yaml' ':(exclude)*poetry.lock' ':(exclude)*uv.lock' ':(exclude)*Cargo.lock' ':(exclude)*.min.js' ':(exclude)*.min.css' ':(exclude)*.map' ':(exclude)runs/*' ':(exclude)reports/*' ':(exclude)docs/handoffs/*' ':(exclude)*.png' ':(exclude)*.jpg' ':(exclude)*.jpeg' ':(exclude)*.gif' ':(exclude)*.svg' ':(exclude)*.ico' ':(exclude)*.pdf' ':(exclude)*.woff' ':(exclude)*.woff2' ':(exclude)*.ttf'
  (this is the diff to review — lockfile/minified/binary/harness-artifact noise is pre-excluded)
Then run: git diff HEAD --stat -- '*package-lock.json' '*yarn.lock' '*pnpm-lock.yaml' '*poetry.lock' '*uv.lock' '*Cargo.lock' '*.min.js' '*.min.css' '*.map' 'runs/*' 'reports/*' 'docs/handoffs/*' '*.png' '*.jpg' '*.jpeg' '*.gif' '*.svg' '*.ico' '*.pdf' '*.woff' '*.woff2' '*.ttf'
  (stat of ONLY the excluded paths: if it lists dependency lockfiles, note WHICH changed and review the matching package.json/pyproject edit in the main diff; runs/ and reports/ churn is harness bookkeeping, outside review scope)

Write your review report to: reports/reviews/goal-ops-hardening-iter-50-review.md

The report MUST start with a line matching exactly:
**Verdict:** PASS
  or
**Verdict:** PASS_WITH_NOTES
  or
**Verdict:** FAIL

Environment note: this pipeline run isolates temp files. Before running tests or any command that writes temporary files, run: export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-6c792d42.227710" TMP="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-6c792d42.227710" TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-6c792d42.227710"

Note: your agent definition (the .claude/agents/*.md file named above) is already loaded as your system prompt — do not Read it again; treat its 'read this first' pointer as satisfied.
