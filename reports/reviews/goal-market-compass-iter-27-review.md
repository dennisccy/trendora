**Verdict:** PASS

```yaml
phase: goal-market-compass-iter-27
date: 2026-08-28
reviewer: reviewer
summary: |
  GET /api/compass now checks latest_manifest_for_date (via resolved_date, which never self-heals)
  before ever calling resolved_run/run_scan, so a frozen manifest whose source run was removed
  honestly serves basis.status == "unavailable" instead of silently self-healing. Independently
  re-derived the error-mapping equivalence by reading scanner.py:304-348 and snapshot_serving.py,
  reran the targeted suite (93 passed, matches handoff), reverted the source via git stash and
  confirmed the flipped/new tests fail for the claimed reason (2 failed, 1 passed) then restored the
  fix, and re-checked canonical-DB row counts (25/3128/3,310,374) and the 7 incident-date manifest
  count (0) read-only. All matched the handoff exactly.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues:
  - severity: NOTE
    file: apps/backend/app/api/compass.py
    line: 68
    category: code-quality
    summary: on the no-manifest-yet (create) branch, resolve_as_of_date now runs twice (once via resolved_date, once again inside resolved_run/resolve_run) — redundant but harmless read
    fix: optional — thread the already-resolved date into resolved_run to avoid the second lookup
standards:
  state_transitions_server_side: pass
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  architecture_principles: pass
```
