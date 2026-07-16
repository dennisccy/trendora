You are the iteration-summarizer agent.

mode: normal
Phase id: goal-mcp-loop-iter-41
Output path (iteration summary): /home/dennis-chan/Git/trendora/reports/phase-goal-mcp-loop-iter-41-iteration-summary.md
Output path (project story, GOAL MODE ONLY): /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/project-story.md
Agent instructions: .claude/agents/iteration-summarizer.md  <-- read this first
Template: templates/iteration-summary.md  <-- exact section structure your output must follow
(CLAUDE.md is already in your system prompt -- do not Read it again.)

Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.

Read every relevant input listed in your agent instructions. Files that don't
exist should be silently skipped. Use what is present.

NOTE — dispatch reconstruction (read this): the usual inlined "recent evaluator log (last 300 lines)" block was OMITTED from this prompt because the full dispatch payload exceeded the OS argument-size limit (a known framework bug: interactive-dispatch.sh builds the dispatch JSON via `jq --arg`, which caps at MAX_ARG_STRLEN and fails on the ever-growing inlined evaluator-log — the engine published a 0-byte .ready). Nothing is lost — read the real on-disk sources directly, which are authoritative:
  - The goal-evaluator's verdict for THIS iteration (the top-line verdict you must render): /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/iter-41/eval.md  (**Verdict: CONTINUE**)
  - Full evaluator log (its tail holds the recent per-iteration entries that would have been inlined): /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/evaluator-log.md
  - Journey history (AUTHORITATIVE — all 25 journeys `passing` as of iter-41; J-25 just flipped unknown→passing): /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/journey-history.json
  - Assumption ledger tail (if you need the recent scoring-assumption context): /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/assumptions.md

This iteration's other inputs (read what exists):
  Iter spec: /home/dennis-chan/Git/trendora/docs/phases/goal-mcp-loop-iter-41.md
  Status: /home/dennis-chan/Git/trendora/runs/goal-mcp-loop-iter-41/status.json
  Dev handoff: /home/dennis-chan/Git/trendora/docs/handoffs/goal-mcp-loop-iter-41-dev.md
  Review: /home/dennis-chan/Git/trendora/reports/reviews/goal-mcp-loop-iter-41-review.md
  QA: /home/dennis-chan/Git/trendora/reports/qa/goal-mcp-loop-iter-41-qa.md
  Audit: /home/dennis-chan/Git/trendora/docs/handoffs/goal-mcp-loop-iter-41-audit.md
  Browser QA results: /home/dennis-chan/Git/trendora/reports/phase-goal-mcp-loop-iter-41-ui-test-results.md
  Closure verdict: /home/dennis-chan/Git/trendora/reports/phase-goal-mcp-loop-iter-41-closure-verdict.md
  UX regression: /home/dennis-chan/Git/trendora/reports/phase-goal-mcp-loop-iter-41-ux-regression.md
  Implementation summary: /home/dennis-chan/Git/trendora/reports/phase-goal-mcp-loop-iter-41-implementation-summary.md
  User-visible changes: /home/dennis-chan/Git/trendora/reports/phase-goal-mcp-loop-iter-41-user-visible-changes.md

Write the iteration summary to: /home/dennis-chan/Git/trendora/reports/phase-goal-mcp-loop-iter-41-iteration-summary.md
(NOTE: an earlier in-pipeline draft of this file exists that fell back to a CLOSURE-PASS-derived `PASS` because eval.md did not yet exist; overwrite it with the authoritative goal-evaluator verdict CONTINUE now that iter-41/eval.md is present — eval.md outranks the closure verdict per your verdict-resolution priority.)

This is a GOAL-MODE iteration. After writing the iteration summary, also
maintain /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/project-story.md per the 'Cumulative project story' section of your
agent instructions. Read the existing file if present, then rewrite it as one
flowing plain-language narrative that ends with this iteration (all 25 journeys now passing; GOAL_ACHIEVED pending the iter-42 lean replay closeout).

Follow the section structure in templates/iteration-summary.md EXACTLY -- the
HTML renderer keys off the section headings. The verdict line must match the
form '**Verdict:** VALUE' where VALUE is one of: GOAL_ACHIEVED, CONTINUE,
ESCALATE, REGRESSION, STALLED, PASS, FAIL, IN-PROGRESS.

When finished, STOP.

Environment note: this pipeline run isolates temp files. Before running tests or any command that writes temporary files, run: export TMPDIR="/tmp/iad.goal-mcp-loop-iter-41.2778307" TMP="/tmp/iad.goal-mcp-loop-iter-41.2778307" TEMP="/tmp/iad.goal-mcp-loop-iter-41.2778307"