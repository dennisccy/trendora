**Verdict:** PASS_WITH_NOTES

```yaml
phase: goal-mcp-loop-iter-41
date: 2026-07-15
reviewer: reviewer
summary: |
  Implements J-25's phase-conditional drawdown & dry-spell expectations panel: two new append-only
  ForwardReturn columns computed in the existing INSERT pass (zero extra bar reads, identical NA gate
  to max_drawdown), a pure compute_drawdown_expectations aggregation (cohort via the existing
  compute_samples selectors, phase join via the untouched causal phase_context_by_date), a J-72
  EventStudyCache-backed cache that fixes a discovered ~3x /api/evidence latency regression, and an
  additive /evidence panel. Manually re-derived the fixture median/p90/streak math by hand and it is
  exact; independently re-ran all claimed tests (29+17+5+135+3 backend, 42 frontend, tsc clean) and they
  pass; the full-universe rebuild memory (VSZ+RSS, 2 runs, real seed) and a live correctness spot-check
  are recorded in perf-budgets.md; ledgers stay byte-identical (divisor 8); no proven/advice language
  introduced; existing forward_testing/scoring/evidence tests unedited and green.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues:
  - severity: MINOR
    file: apps/frontend/app/evidence/page.tsx
    line: 282
    category: ui
    summary: phase Badge uses a flat variant="default" instead of the codebase's single-source phase-color mapping (lib/phase.ts's phasePosture, already used by market-phase-card.tsx/app/page.tsx for every other phase badge), and diverges from the plan's own "mirror the existing regime Badge" (accent) instruction
    fix: color the phase Badge via lib/phase.ts's phasePosture (or the existing phaseVariant mapping) so Bear/Correction/Pullback/Expansion/Recovery read consistently with every other phase badge in the app
  - severity: NOTE
    file: apps/backend/app/engine/evidence.py
    line: 130
    category: code-quality
    summary: docstring claims "~13 existing call sites (incl. test_graveyard.py, test_api_graveyard.py, test_api_budget.py, test_budget_accounting.py)" but those 4 files never call build_evidence_payload (only test_evidence.py's 15 sites do, all independently re-verified green) — inherited from an inaccurate plan reference
    fix: correct the docstring's file list to test_evidence.py only
standards:
  state_transitions_server_side: n/a
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  ui_evolved_with_capability: pass
  navigation_updated: n/a
  architecture_principles: pass
```
