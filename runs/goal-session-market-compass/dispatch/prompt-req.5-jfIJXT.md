You are the browser-qa-agent for goal-mode lean iteration.

Iteration: goal-market-compass-iter-28
Iter spec: /home/dennis-chan/Git/trendora/docs/phases/goal-market-compass-iter-28.md
Project goal (SLICED — every journey you are asked to test below is verbatim; stable passing journeys digested to one line): /home/dennis-chan/Git/trendora/runs/goal-session-market-compass/iter-28/goal-slice-bqa.md  <-- read "Must-have user journeys" section for journey definitions
Full goal file: /home/dennis-chan/Git/trendora/docs/goal.md — Read it ONLY if a journey definition you need is missing from the sliced file.
Agent instructions: .claude/agents/browser-qa-agent.md  <-- read this first
(CLAUDE.md is already in your system prompt — do not Read it again.)
Skill: .claude/skills/browser-workflow-executor.md  <-- read for Chrome MCP technique

GOAL-MODE LEAN MODE — test EXACTLY these journeys this run: J-07,J-08
Do NOT test these — a deterministic replay verifies them separately: J-01 J-02 J-03 J-04 J-05 J-06 J-10 J-11 
  1. For each journey ID above, read its numbered steps + Acceptance line from the "Must-have user journeys" section of the goal file named above.
  2. Execute the steps with Chrome MCP; use the journey ID as the test case ID (e.g. UT-J-01).

Frontend URL: http://localhost:3255
Frontend available: yes

Chrome MCP browser checks ARE required. Use mcp__plugin_superpowers-chrome_chrome__use_browser.

For each journey:
  - Execute the numbered steps exactly as written in the goal file named above
  - Verify the Acceptance condition
  - Take a screenshot of the end state, save to reports/qa/goal-market-compass-iter-28-evidence/
  - Record PASS / FAIL / SKIP with a short failure description if FAIL

GOLDEN REPLAY SCRIPTS (goal-mode regression speedup): for every journey you verify
PASS, ALSO write a self-contained deterministic replay script to
/home/dennis-chan/Git/trendora/runs/goal-session-market-compass/journey-scripts/<J-XX>.json (overwrite if present) so future iterations can
re-verify it without a browser-driving model. Follow the 'Golden replay script'
section of your agent instructions for the exact JSON shape. Best-effort: if you
cannot produce one for a journey, skip it (that journey just falls back to the LLM
next time).


Write your results to: /home/dennis-chan/Git/trendora/reports/phase-goal-market-compass-iter-28-ui-test-results.llm.md
Use template: templates/ui-test-results.md
Map each journey ID to a UT row.

The report MUST contain a line at the top:
**Browser QA Verdict:** PASS
  or
**Browser QA Verdict:** FAIL
  or
**Browser QA Verdict:** SKIPPED

Then STOP.

Environment note: this pipeline run isolates temp files. Before running tests or any command that writes temporary files, run: export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-market--ff46920c.1361600" TMP="/home/dennis-chan/.cache/iad/iad.goal-market--ff46920c.1361600" TEMP="/home/dennis-chan/.cache/iad/iad.goal-market--ff46920c.1361600"

Note: your agent definition (the .claude/agents/*.md file named above) is already loaded as your system prompt — do not Read it again; treat its 'read this first' pointer as satisfied.
