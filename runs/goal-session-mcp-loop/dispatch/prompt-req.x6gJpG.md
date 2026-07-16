You are the iteration-summarizer agent.

mode: normal
Phase id: goal-mcp-loop-iter-42
Output path (iteration summary): /home/dennis-chan/Git/trendora/reports/phase-goal-mcp-loop-iter-42-iteration-summary.md
Output path (project story, GOAL MODE ONLY): /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/project-story.md
Agent instructions: .claude/agents/iteration-summarizer.md  <-- read this first
Template: templates/iteration-summary.md  <-- exact section structure your output must follow
(CLAUDE.md is already in your system prompt -- do not Read it again.)

Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.

Read every relevant input listed in your agent instructions. Files that don't
exist should be silently skipped. Use what is present.

NOTE — dispatch reconstruction (read this): the usual inlined "recent evaluator log (last 300 lines)" and "assumption-ledger tail" blocks were OMITTED from this prompt because the full dispatch payload exceeded the OS argument-size limit (a known framework bug: interactive-dispatch.sh builds the dispatch JSON via `jq --arg`, which caps at MAX_ARG_STRLEN and fails on the ever-growing inlined evaluator-log — the engine published a 0-byte .ready). Nothing is lost — read the real on-disk sources directly, which are authoritative:
  - The goal-evaluator's verdict for THIS iteration (the top-line verdict you must render): /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/iter-42/eval.md  (**Verdict: GOAL_ACHIEVED** — confirmed by the two-key /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/iter-42/eval-confirm.md = CONFIRM_ACHIEVED, and the deterministic gate-report.md = PASS)
  - Full evaluator log (its tail holds the recent per-iteration entries that would have been inlined): /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/evaluator-log.md
  - Assumption ledger tail: /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/assumptions.md
  - Journey history (AUTHORITATIVE — all 25 Must-have journeys `passing`; the goal is ACHIEVED): /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/journey-history.json

This iteration's other inputs (read what exists):
  Iter spec: /home/dennis-chan/Git/trendora/docs/phases/goal-mcp-loop-iter-42.md
  Status: /home/dennis-chan/Git/trendora/runs/goal-mcp-loop-iter-42/status.json
  Dev handoff: /home/dennis-chan/Git/trendora/docs/handoffs/goal-mcp-loop-iter-42-dev.md
  Review: /home/dennis-chan/Git/trendora/reports/reviews/goal-mcp-loop-iter-42-review.md
  Coherence: /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/iter-42/coherence.md
  Browser QA (merged) results: /home/dennis-chan/Git/trendora/reports/phase-goal-mcp-loop-iter-42-ui-test-results.md
  Deterministic replay results: /home/dennis-chan/Git/trendora/reports/phase-goal-mcp-loop-iter-42-regression-replay-results.md

Write the iteration summary to: /home/dennis-chan/Git/trendora/reports/phase-goal-mcp-loop-iter-42-iteration-summary.md

This is a GOAL-MODE iteration. After writing the iteration summary, also
maintain /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/project-story.md per the 'Cumulative project story' section of your
agent instructions. Read the existing file if present, then rewrite it as one
flowing plain-language narrative that ends with this iteration — the terminal
one: iter-42 is the lean deterministic-replay closeout that reached GOAL_ACHIEVED
with all 25 Must-have journeys passing.

Follow the section structure in templates/iteration-summary.md EXACTLY -- the
HTML renderer keys off the section headings. The verdict line must match the
form '**Verdict:** VALUE' where VALUE is one of: GOAL_ACHIEVED, CONTINUE,
ESCALATE, REGRESSION, STALLED, PASS, FAIL, IN-PROGRESS.

When finished, STOP.

Environment note: this pipeline run isolates temp files. Before running tests or any command that writes temporary files, run: export TMPDIR="/tmp/iad.goal-mcp-loop-iter-42.2778307" TMP="/tmp/iad.goal-mcp-loop-iter-42.2778307" TEMP="/tmp/iad.goal-mcp-loop-iter-42.2778307"