**Verdict:** PASS_WITH_NOTES

```yaml
phase: goal-ops-hardening-iter-47
date: 2026-08-04
reviewer: reviewer
summary: |
  Re-review after the audit-fix pass (audit FAIL on B1/B2, IMPORTANT B3/B4/B5). Product code changed
  since the prior review: forward_testing.py's date filter re-scoped from per-chunk-union to per-ticker
  (4.4%->90% reduction) with _MAX_IN_PARAMS batching, and research.py's _factor_decile_observations
  PASS 1 now streams into a proven-upper-bound _BoundedRankWindow instead of retaining the whole
  population's sort keys. Verified the window's monotonicity argument (capacity from n_max bounds the
  true [lo,hi) slice regardless of keep-smallest/largest choice) and its degrade-to-exact underflow
  path. Spot-ran a representative subset of new/changed backend tests (cached_with_status,
  factor_decile suite, warmup log_isolation, evidence refreshing, date-filter/batching) plus
  tsc --noEmit and evidence.test.ts — all pass, matching the handoff's reported counts. No scope creep.
spec_alignment:
  definition_of_done: partial
  scope_creep: none
issues:
  - severity: MINOR
    file: apps/backend/tests/test_samples_memory_pressure.py
    line: 216
    category: tests
    summary: TC-4's 5-consecutive-run MemoryError proof (test_shipped_survives_five_consecutive_tight_cap_runs) was run against the pre-audit-fix implementation, where samples.py:156 was only "reduced" (audit B3). After the fix pass added the true _BoundedRankWindow bound, the handoff explicitly states this test was not re-run against the final shipped code — safety is inferred from a lower isolated peak-RSS measurement, not re-proven.
    fix: re-run test_shipped_survives_five_consecutive_tight_cap_runs against current HEAD before scoring complete — this is exactly the "one green run on different code is not proven" shape the binding iter-44 lesson names.
  - severity: NOTE
    file: apps/backend/app/engine/research.py
    line: 365
    category: code-quality
    summary: "_BoundedRankWindow's docstring claims peak retention is O(the requested decile's own member count); true only for extreme deciles (1 or count). A middle decile (e.g. 5 of 10) commits capacity = min(hi, n-lo) ~ n/2, not n/deciles_count. Byte-identity is still proven for decile=5 by test, so correctness holds — only the memory-bound tightness claim overstates the general case (all 5 live claims use extreme deciles, per the handoff)."
    fix: narrow the docstring's claim to the extreme-decile case actually exercised in production, or note the middle-decile capacity is weaker.
standards:
  state_transitions_server_side: n/a
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  architecture_principles: pass
```
