You are the browser-qa-agent for phased development.

Phase: goal-ops-hardening-iter-27
Phase spec: /home/dennis-chan/Git/trendora/docs/phases/goal-ops-hardening-iter-27.md
Agent instructions: .claude/agents/browser-qa-agent.md  <-- read this first
(CLAUDE.md is already in your system prompt — do not Read it again.)
Skill: .claude/skills/browser-workflow-executor.md  <-- read for Chrome MCP technique

UI test plan: /home/dennis-chan/Git/trendora/reports/phase-goal-ops-hardening-iter-27-ui-test-plan.md  <-- execute each test case in this file
UI surface map: /home/dennis-chan/Git/trendora/reports/phase-goal-ops-hardening-iter-27-ui-surface-map.md

GOAL-MODE REGRESSION LANES (goal-session iteration — IN ADDITION to the test plan):
- Deterministic replay has ALREADY re-verified these Required-still-passing journeys from stored golden scripts: J-01 J-03 J-04 J-06 J-09. Do NOT re-test them and do NOT emit rows for them — their rows merge into the results automatically after your run. (If a test-plan case you execute anyway covers one, that is fine; your row supersedes the replay's.)
- ALSO execute these regression journeys this run: J-06. For each: read its numbered steps + Acceptance line from the "Must-have user journeys" section of docs/goal.md, execute it like a test case, and add a results-table row using the journey ID as the Test ID (e.g. UT-J-01).
- The replay lane flagged possible regression(s) on: J-06 (already included in the list above). Re-confirm each by executing the journey yourself; if it passes, the replay FAIL was a stale golden script — repair that journey's golden so the next iteration replays clean.

GOLDEN REPLAY SCRIPTS (goal-mode regression speedup): for every journey you verify
PASS, ALSO write a self-contained deterministic replay script to
/home/dennis-chan/Git/trendora/runs/goal-session-ops-hardening/journey-scripts/<J-XX>.json (overwrite if present), IMMEDIATELY after that
journey passes — follow the 'Golden replay script' section of your agent
instructions for the exact JSON shape. Best-effort: if you cannot produce one for
a journey, skip it (that journey just falls back to the LLM lane next time).

Frontend URL: http://localhost:3255
Frontend available: yes
Note: browser-qa-phase.sh manages backend (http://localhost:8255/health, log: /home/dennis-chan/.cache/iad/iad.goal-ops-hard-be18659f.820599/browser-qa-backend-8255.log) and frontend (http://localhost:3255, log: /home/dennis-chan/.cache/iad/iad.goal-ops-hard-be18659f.820599/browser-qa-frontend-8255.log). Services are restarted automatically if they die during quota-retry sleeps.

Chrome MCP browser checks ARE required. Use mcp__plugin_superpowers-chrome_chrome__use_browser for each test case.

Execute the test plan:
- For each UT-XX test case: execute steps, verify expected result, record PASS/FAIL/SKIP
- Take screenshots for key states and save to reports/qa/goal-ops-hardening-iter-27-evidence/
- For failures: record exact failure description

Write your results to: /home/dennis-chan/Git/trendora/reports/phase-goal-ops-hardening-iter-27-ui-test-results.llm.md
Use template: templates/ui-test-results.md

The report MUST contain a line at the top:
**Browser QA Verdict:** PASS
  or
**Browser QA Verdict:** FAIL
  or
**Browser QA Verdict:** SKIPPED

Then STOP.

Environment note: this pipeline run isolates temp files. Before running tests or any command that writes temporary files, run: export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-be18659f.820599" TMP="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-be18659f.820599" TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-be18659f.820599"

Note: your agent definition (the .claude/agents/*.md file named above) is already loaded as your system prompt — do not Read it again; treat its 'read this first' pointer as satisfied.