**Verdict:** PASS_WITH_NOTES

```yaml
phase: goal-ops-hardening-iter-20
date: 2026-07-24
reviewer: reviewer
summary: |
  Implements a single-flight-guarded background dispatch (own DB session, mirrors the established
  data_manager/warmup thread-plus-own-session idiom) that removes the historical /backtest ensure-loop
  from the request thread. Request-path block iter-19's UT-04 measured at 9.6-54s is now 0.082s live,
  ensure_loop_ms ~2ms (was 9288-54281ms). Guard release-on-exception (TC-7), byte-identity, and
  route/MCP parity are verified in code (compute_forward_aggregates/resolved_forward_aggregate_evidence
  confirmed byte-unchanged via diff) and in 91 scoped tests with genuine RED/GREEN TDD evidence.
  Live re-measurement honestly surfaced a residual: GIL/CPU contention during the ~30s background
  window pushes other concurrent traffic to 3.0-6.3s, and two DoD-named verification items are not
  fully closed this session.
spec_alignment:
  definition_of_done: partial
  scope_creep: none
issues:
  - severity: MINOR
    file: apps/backend/app/engine/forward_testing.py
    line: 1235
    category: tests
    summary: TC-5 (GET /api/health stays <=0.1s throughout a background warm) has no dedicated automated test; the live re-check confirmed only HTTP 200 status, not response latency, during the same window that showed 3.0-6.3s contention spikes on other traffic
    fix: capture a direct /api/health latency measurement (not just status) during a live historical-dispatch window, or add a lightweight regression test, given /api/health's historically ~98%-of-budget margin (reports/perf-budgets.md)
  - severity: MINOR
    file: apps/backend/tests/test_data_manager.py
    line: 1
    category: tests
    summary: one of the five DoD-named regression files (exercises compute_forward_aggregates/forward_aggregates_ingest_cached directly) was not run this session and not cited as excluded, unlike test_forward_testing.py which has a documented iter-19 timeout exclusion
    fix: run test_data_manager.py host-guard-confined before closing this iteration, or add an explicit citation to the dev handoff
  - severity: NOTE
    file: reports/perf-budgets.md
    line: 3358
    category: backend
    summary: the disclosed GIL/CPU contention residual (3.0-6.3s spikes on other concurrent traffic during the ~30s background compute) does not violate the DoD's literal per-view/TC-3 same-date wording, but is a structural cost of a background-thread (not background-process) approach
    fix: no action required this iteration; track against other journeys' own latency budgets in future perf passes
standards:
  state_transitions_server_side: pass
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  ui_evolved_with_capability: n/a
  navigation_updated: n/a
  architecture_principles: pass
```
