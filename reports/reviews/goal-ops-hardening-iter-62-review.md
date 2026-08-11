**Verdict:** PASS

```yaml
phase: goal-ops-hardening-iter-62
date: 2026-08-11
reviewer: reviewer
summary: |
  Replaces /api/health's hardcoded last_run_date: null with a real
  select(func.max(ScannerRun.asof_date)) read inside the existing db_ok try/except (same query shape
  data_manager.py already uses), with TC-1 updated and TC-2 (empty-DB null) added. Extracts a pure
  nextStateAfterFetchError helper and routes /data's loadOverview/loadAvailability .catch handlers
  through it so a transient ambient-refresh failure no longer erases already-rendered good data, while
  the initial-mount-failure path is unchanged. Diff is tight and exactly matches spec scope; verified
  the fast test subset, the new lib test, and tsc --noEmit locally.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues: []
standards:
  state_transitions_server_side: n/a
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: pass
  architecture_principles: pass
```
