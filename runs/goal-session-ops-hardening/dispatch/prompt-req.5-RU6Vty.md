You are the developer agent for phased development.

Phase: goal-ops-hardening-iter-48
Phase spec: /home/dennis-chan/Git/trendora/docs/phases/goal-ops-hardening-iter-48.md
Project goal (SLICED — vision, anti-goals, and this iteration's target + failing journeys verbatim; stable passing journeys digested to one line): /home/dennis-chan/Git/trendora/runs/goal-ops-hardening-iter-48/goal-slice-exec.md  <-- read Must-have user journeys and Anti-goals here
Full goal file: docs/goal.md — Read it ONLY if a digested journey becomes relevant to your work.
Project template: .claude/project-template.md  <-- read this for stack info, test commands, architecture rules
Agent instructions: .claude/agents/developer.md  <-- read this first
(CLAUDE.md is already in your system prompt — do not Read it again.)

Execution plan: /home/dennis-chan/Git/trendora/runs/goal-ops-hardening-iter-48/plan.md  <-- read this to understand what to build

Mode: INITIAL BUILD

When complete:
- Write dev handoff to: docs/handoffs/goal-ops-hardening-iter-48-dev.md
- If frontend work was done, also write: docs/handoffs/goal-ops-hardening-iter-48-frontend.md
- Also write: reports/phase-goal-ops-hardening-iter-48-implementation-summary.md
  Use the template at templates/implementation-summary.md.
  Include: features implemented, changed behavior, backend-only items, incomplete items, config/env changes, known limitations.
  This report is for operators, not developers — write in plain language, not code.
- Update runs/goal-ops-hardening-iter-48/status.json with current_step: dev_complete

Environment note: this pipeline run isolates temp files. Before running tests or any command that writes temporary files, run: export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-e9cad6c2.18723" TMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-e9cad6c2.18723" TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-e9cad6c2.18723"

Note: your agent definition (the .claude/agents/*.md file named above) is already loaded as your system prompt — do not Read it again; treat its 'read this first' pointer as satisfied.