You are the phase-closure-auditor for phased development.

Phase: goal-ops-hardening-iter-17
Phase spec: /home/dennis-chan/Git/trendora/docs/phases/goal-ops-hardening-iter-17.md
Agent instructions: .claude/agents/phase-closure-auditor.md  <-- read this first
(CLAUDE.md is already in your system prompt — do not Read it again.)
Skill: .claude/skills/phase-closure-gate.md

Execution plan: /home/dennis-chan/Git/trendora/runs/goal-ops-hardening-iter-17/plan.md
Review report: /home/dennis-chan/Git/trendora/reports/reviews/goal-ops-hardening-iter-17-review.md
QA report: /home/dennis-chan/Git/trendora/reports/qa/goal-ops-hardening-iter-17-qa.md
Audit report: /home/dennis-chan/Git/trendora/docs/handoffs/goal-ops-hardening-iter-17-audit.md (if exists)

UI visibility artifacts (check each exists and has real content):
  - reports/phase-goal-ops-hardening-iter-17-implementation-summary.md
  - reports/phase-goal-ops-hardening-iter-17-user-visible-changes.md
  - reports/phase-goal-ops-hardening-iter-17-ui-surface-map.md
  - reports/phase-goal-ops-hardening-iter-17-ui-test-plan.md
  - reports/phase-goal-ops-hardening-iter-17-ui-test-results.md
  - reports/phase-goal-ops-hardening-iter-17-what-to-click.md

UX regression report (if exists): reports/phase-goal-ops-hardening-iter-17-ux-regression.md

Your job:
1. Verify all standard pipeline gates passed (review, QA, audit)
2. Verify all 6 UI visibility artifacts exist and are non-vague
3. Cross-reference claims vs evidence for consistency
4. Check for backend-only claims when frontend work was expected
5. Write closure verdict to: /home/dennis-chan/Git/trendora/reports/phase-goal-ops-hardening-iter-17-closure-verdict.md

Use template: templates/closure-verdict.md

Verdict line MUST appear at the top of the file:
**Verdict:** CLOSURE-PASS
  or
**Verdict:** CLOSURE-FAIL

For CLOSURE-FAIL: list exact blocking issues and specific remediation steps.

Then STOP.

Environment note: this pipeline run isolates temp files. Before running tests or any command that writes temporary files, run: export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-b612f488.372082" TMP="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-b612f488.372082" TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-b612f488.372082"