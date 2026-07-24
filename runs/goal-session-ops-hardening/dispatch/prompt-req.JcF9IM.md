You are the qa agent operating in TEST PLAN GENERATION mode for phased development.

Phase: goal-ops-hardening-iter-19
Phase spec: /home/dennis-chan/Git/trendora/docs/phases/goal-ops-hardening-iter-19.md
Execution plan: /home/dennis-chan/Git/trendora/runs/goal-ops-hardening-iter-19/plan.md
Agent instructions: .claude/agents/qa.md  <-- read this first, follow MODE 1 instructions

Frontend Present for this phase: yes

Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.
Do not ask questions — derive all test cases from the phase spec.

Write the functional test plan to: /home/dennis-chan/Git/trendora/reports/qa/goal-ops-hardening-iter-19-test-plan.md

The plan must include:
- Phase goal summary
- Numbered test cases (TC-01, TC-02, ...)
- For each test case: type, preconditions, steps, expected outcome, pass criteria
- A summary of total test cases by type

Keep it concise (1-3 pages). Write the plan and STOP.

Environment note: this pipeline run isolates temp files. Before running tests or any command that writes temporary files, run: export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-har-65b40472.2114908" TMP="/home/dennis-chan/.cache/iad/iad.goal-ops-har-65b40472.2114908" TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-har-65b40472.2114908"