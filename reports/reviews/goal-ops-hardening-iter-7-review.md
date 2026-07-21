**Verdict:** PASS

```yaml
phase: goal-ops-hardening-iter-7
date: 2026-07-21
reviewer: reviewer
summary: |
  Extends `_refresh_ingest_aggregates` with a `drawdown_expectations` ingest-time warm step, mirroring the
  existing `research_hot_keys` block exactly: same ledger filter as `build_evidence_payload`, same claim
  extraction, same `compute_drawdown_expectations_cached` call, honest "actually warmed" gating, and
  per-claim try/except isolation. 7 new tests (TC-1/3/4/5 + variants) all pass, plus the 12 pre-existing
  finalize-hook tests remain green (19/19, 112.58s). No frontend files touched, matching the spec's
  backend-only scope. perf-budgets.md and blueprint.md are consistent with the shipped code.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues: []
standards:
  state_transitions_server_side: n/a
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  ui_evolved_with_capability: n/a
  navigation_updated: n/a
  architecture_principles: pass
```
