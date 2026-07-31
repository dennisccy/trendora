**Verdict:** PASS

```yaml
phase: goal-ops-hardening-iter-42
date: 2026-07-31
reviewer: reviewer
summary: |
  Closes the iter-41 target-journey verification gap (ui-test-designer emits UT-<journey-id> rows
  for Target journeys: too; merge_ui_test_results.py's new target_journeys guard forces BLOCKED on
  a missing/all-SKIP target; wiring threaded through replay-lane.sh/browser-qa-phase.sh, confirmed
  goal-iter-lean.sh needed no change), fixes the B4 frontend-restart race centrally in
  ensure_services_running, and lands a fifth, verified-modest _BarCache.prefill bound (WHERE symbol
  IN filter, live-measured 2.5% VmPeak / 5.9% row reduction, honestly reported as partial not
  resolved) plus B6 NULL-tolerance. All claims verified: code inspection confirms both real prefill
  callers pass expected_symbols=pool_symbols, and regime.py/market_phase.py route excluded symbols
  through the unchanged lazy bars_asof path. Independently reran test_bar_cache.py (20 passed),
  merge_ui_test_results.py self-test (29 passed), test-frontend-restart-reprobe.sh (7 passed),
  test-replay-lane.sh (68 passed), lint_contracts.py self-test, and sync-cli-assets --check (0
  drift) — all match the handoff's reported results. The T2 finding (_SymbolColumns ~70-80x
  read-latency regression from iter-41) is a new, honestly surfaced, out-of-scope-to-fix discovery,
  correctly disclosed rather than fixed or hidden.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues: []
standards:
  state_transitions_server_side: n/a
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  architecture_principles: pass
```
