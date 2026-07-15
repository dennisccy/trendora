**Verdict:** PASS_WITH_NOTES

```yaml
phase: goal-mcp-loop-iter-36
date: 2026-07-14
reviewer: reviewer
summary: |
  J-22 referee-calibration harness (permutation null generator + lookahead-contaminated factor +
  Wilson CI + isolated orchestrator), config block, GET /api/research/referee-audit, and the
  /research/referee-audit page (6 states: loading/error/empty/unreadable/calm/tripwire) with a
  4th governance nav card. Isolation independently re-verified: certified-claims.jsonl,
  staging-ledger.jsonl, pre-registrations.jsonl are byte-identical to HEAD both before and after
  I ran the new + a broader regression test subset myself (referee.py/ledger.py/mcp/tools.py have
  zero diff). tsc --noEmit clean. All DoD-listed displayed fields present and correctly wired to
  the persisted artifact; no proven-language; harness never wired to any request path (grep-
  confirmed, CLI-only). Additive-only diff, no scope creep, blueprint.md rows pre-existing as
  claimed.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues:
  - severity: MINOR
    file: docs/handoffs/goal-mcp-loop-iter-36-dev.md
    line: 113
    category: tests
    summary: "handoff claims '41 tests'/'46 passed' for test_referee_audit.py + test_api_referee_audit.py; actual collected+run count is 34 + 5 = 39 (verified via pytest --collect-only and a fresh run — all 39 genuinely pass, no regression). The broader '251 passed' regression claim is accurate."
    fix: correct the test counts in the handoff to 34/5/39 before this iteration closes out
standards:
  state_transitions_server_side: pass
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  ui_evolved_with_capability: pass
  navigation_updated: pass
  architecture_principles: pass
```
