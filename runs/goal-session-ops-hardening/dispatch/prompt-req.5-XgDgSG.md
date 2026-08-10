You are the auditor agent for phased development.

Phase: goal-ops-hardening-iter-57
Phase spec: /home/dennis-chan/Git/trendora/docs/phases/goal-ops-hardening-iter-57.md
Execution plan: /home/dennis-chan/Git/trendora/runs/goal-ops-hardening-iter-57/plan.md
Dev handoff: /home/dennis-chan/Git/trendora/docs/handoffs/goal-ops-hardening-iter-57-dev.md
Frontend handoff: /home/dennis-chan/Git/trendora/docs/handoffs/goal-ops-hardening-iter-57-frontend.md
Review report: /home/dennis-chan/Git/trendora/reports/reviews/goal-ops-hardening-iter-57-review.md
QA report: /home/dennis-chan/Git/trendora/reports/qa/goal-ops-hardening-iter-57-qa.md

Status file: /home/dennis-chan/Git/trendora/runs/goal-ops-hardening-iter-57/status.json  <-- read changed_files to know which source files to inspect
Project template: .claude/project-template.md  <-- read for test commands and architecture rules
Agent instructions: .claude/agents/auditor.md  <-- read this first
(CLAUDE.md is already in your system prompt — do not Read it again.)

Do not ask questions — assess from evidence in the code and artifacts.

Write your audit report to: /home/dennis-chan/Git/trendora/docs/handoffs/goal-ops-hardening-iter-57-audit.md

The report MUST begin with an Executive Verdict section containing exactly one of:
**Verdict:** PASS
  or
**Verdict:** PASS_WITH_GAPS
  or
**Verdict:** FAIL

IMPORTANT: The **Verdict:** prefix is required — scripts parse this line by machine. Do NOT use **PASS** or **PASS WITH GAPS** without the prefix.

Write the audit report and STOP.

Environment note: this pipeline run isolates temp files. Before running tests or any command that writes temporary files, run: export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-c997acd4.24705" TMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-c997acd4.24705" TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-c997acd4.24705"

Note: your agent definition (the .claude/agents/*.md file named above) is already loaded as your system prompt — do not Read it again; treat its 'read this first' pointer as satisfied.
