**Verdict:** PASS_WITH_NOTES

```yaml
phase: goal-ops-hardening-iter-15
date: 2026-07-23
reviewer: reviewer
summary: |
  Adds a single-flight de-dup to forward_aggregates_cached's MISS path, correctly scoped
  (compute_forward_aggregates byte-identical, unchanged; app.db untouched with a measured
  justification; all 3 call sites unmodified). Root cause (no de-dup) confirmed by measurement
  (9.91x -> 1.04x on a 60k-row fixture); TC-1/TC-2/TC-8 tests are tight, and TC-8 was validated by
  a break-the-fix check. The operator-supervised live pass is transcribed with unusually rigorous
  honesty: every figure I independently spot-checked against the raw CSVs/logs (cold-MISS
  178.743092s, an unflagged second 5.373490s spike, health 498/500 with exact non-200 epochs,
  VmPeak 4,005,376 KB, Tctl 48-84C/620 of 655 samples >64C) matched exactly. WARN and a thermal
  discrepancy are recorded plainly, not smoothed over; no J-06/J-07 pass is self-certified.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues:
  - severity: MINOR
    file: reports/perf-budgets.md
    line: 2279
    category: code-quality
    summary: the root-cause section's "candidate (a)... fully accounts for a 211.8s finding" claim
      (extrapolated from the 60k-row fixture's 9.91x ratio) is never reconciled against the live
      TC-4 pass further down the same file, which shows only a 15.6% reduction (211.8s -> 178.74s)
      -- far short of what a 9.91x-driven "fully accounts for" would predict
    fix: add a forward-reference/caveat in the Root-cause section pointing to the Summary, noting
      the live pass shows most of the residual cost is one cold compute's own cost at deep-basis
      scale, not redundant stacking -- so a reader stopping before the Summary is not misled
  - severity: NOTE
    file: apps/backend/app/engine/forward_testing.py
    line: 1076
    category: code-quality
    summary: the in-flight de-dup key (horizon, asof_key, dataset_version) has no engine/session
      identity component, so the gate is process-wide across any engine, not scoped to app.db's
      one global engine (harmless today -- single global engine in production)
    fix: optional -- note this single-engine assumption in the module comment for future
      maintainers before this cache is ever exercised against multiple engines in one process
standards:
  state_transitions_server_side: n/a
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  ui_evolved_with_capability: n/a
  navigation_updated: n/a
  architecture_principles: pass
```
