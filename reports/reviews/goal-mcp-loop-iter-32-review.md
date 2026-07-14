**Verdict:** PASS

```yaml
phase: goal-mcp-loop-iter-32
date: 2026-07-14
reviewer: reviewer
summary: |
  Implements the certification-budget accounting panel (J-17/B-903): a pure read-compose
  module, GET /api/research/budget, and /research/budget page, mirroring the graveyard
  (J-19) pattern exactly. Verified single-source correctness against live ledgers by hand
  and via tests; all 20 new + 68 regression-sweep backend tests pass, tsc is clean, the
  real ledgers are byte-untouched, no proven-language anywhere on the panel.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues:
  - severity: NOTE
    file: apps/backend/app/engine/budget_accounting.py
    line: 116
    category: backend
    summary: staging next_level unconditionally calls online_fdr.test_level, whereas verify_edge gates that call on cfg.evidence.fdr.enabled (falling back to Bonferroni when off) -- today enabled=true so behavior is correct and tested, but the gate itself isn't mirrored.
    fix: optional -- mirror tools.py's use_fdr gate for full single-source parity if fdr.enabled is ever toggled off later.
standards:
  state_transitions_server_side: n/a
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: pass
  ui_evolved_with_capability: pass
  navigation_updated: pass
  architecture_principles: pass
```
