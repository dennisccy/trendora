You are the goal-decomposer agent for goal-mode iteration planning.

Mode: next
Session ID: mcp-loop
Iteration index: 41
Iter name: goal-mcp-loop-iter-41
Prior verdict: CONTINUE
Prior depth: full

Project template: .claude/project-template.md
Project goal (SLICED — vision + anti-goals + failing/target journeys verbatim; stable passing journeys digested to one line): /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/iter-41/goal-slice.md
  Full goal file: /home/dennis-chan/Git/trendora/docs/goal.md — Read it ONLY if a digested journey becomes relevant to your plan.
Agent instructions: .claude/agents/goal-decomposer.md  <-- read this first
(CLAUDE.md is already in your system prompt — do not Read it again.)

NOTE — dispatch reconstruction (read this): the usual inlined "recent evaluator log (last N entries)" block and the inline journey-state digest were OMITTED from this prompt because the full dispatch payload exceeded the OS argument-size limit (a known framework bug: interactive-dispatch.sh builds the JSON via `jq --arg`, which caps at MAX_ARG_STRLEN and fails on the ever-growing inlined evaluator-log). Nothing is lost — read the real on-disk sources directly, which are authoritative:
  - Last iteration eval (prior verdict, full reasoning, and the explicit next-step recommendation you should weigh): /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/iter-40/eval.md
  - Full evaluator log (its tail holds the recent per-iteration entries that would have been inlined): /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/evaluator-log.md
  - Journey state (AUTHORITATIVE — 24 passing, J-25 the sole `unknown`/unbuilt journey): /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/journey-history.json
  - Accumulated lessons + recorded assumptions: /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/lessons.md and /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/assumptions.md
  - This iteration's snapshot SHA (baseline for the diff, if you need it): /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/iter-41/snapshot-sha

Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.

Write the iteration spec to: docs/phases/goal-mcp-loop-iter-41.md
Also keep /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/blueprint.md current per your agent instructions: register any new displayed value in the Data Contract and place new pages under an existing Information-Architecture home (additive edits only). For a nav-skeleton change, make the edit AND write a one-line reason to /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/blueprint.reapproval-requested.

The spec MUST include a 'Goal Mode Metadata' section with at minimum:
  - Mode: next
  - Depth: lean | full
  - Target journeys: <comma-separated journey IDs>

Do NOT write code or implement anything. The iteration spec and any blueprint edits are planning documents, not code. STOP after writing them.

Environment note: this pipeline run isolates temp files. Before running tests or any command that writes temporary files, run: export TMPDIR="/tmp/iad.goal-mcp-loop-iter-41.2778307" TMP="/tmp/iad.goal-mcp-loop-iter-41.2778307" TEMP="/tmp/iad.goal-mcp-loop-iter-41.2778307"