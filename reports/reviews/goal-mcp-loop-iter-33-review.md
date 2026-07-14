**Verdict:** PASS_WITH_NOTES

```yaml
phase: goal-mcp-loop-iter-33
date: 2026-07-14
reviewer: reviewer
summary: |
  Implements J-20/B-301 exactly as scoped: compute_preflight (pure composer over servability/freshness/
  integrity) + ReadinessCfg + config.yaml block + additive GET /api/health "preflight" field + append-
  only verdict-history, and a layout-level PreflightBanner mounted once in app/layout.tsx reading only
  the existing ReadinessProvider poll. compute_readiness's state/warmup shape is verifiably untouched.
  Files changed match the plan exactly (no scope creep). Fixture-matrix and error-case tests are
  well-designed with tight, exact assertions; manually traced several against the code and they hold.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues:
  - severity: MINOR
    file: apps/backend/app/api/health.py
    line: 64
    category: tests
    summary: record_verdict_transition fires unconditionally in health(); only the 2 new preflight tests
      redirect READINESS_VERDICT_HISTORY_PATH — test_health.py's 2 pre-existing tests plus test_warmup.py/
      test_cors_dev_lan.py's /api/health hits do not, so ordinary suite runs can append to the real,
      git-tracked runs/goal-session-mcp-loop/state/preflight-verdict-history.jsonl.
    fix: add an autouse fixture in tests/conftest.py redirecting READINESS_VERDICT_HISTORY_PATH to a
      tmp path for the whole session, isolating every /api/health call by default.
  - severity: MINOR
    file: apps/backend/app/engine/readiness.py
    line: 238
    category: backend
    summary: compute_preflight re-invokes compute_readiness(session, config=cfg) instead of accepting the
      caller's already-computed dict; health.py already computed it once (line 50). Contradicts the "no
      second computation" claim repeated in the docstrings/comments — harmless (deterministic, identical
      inputs) but doubles a few DB round-trips on the ~2s-polled path.
    fix: thread the already-computed readiness dict through as an optional parameter instead of recalling
      compute_readiness inside compute_preflight.
  - severity: MINOR
    file: apps/backend/tests/test_readiness.py
    line: 91
    category: tests
    summary: dev handoff discloses 18-of-25 new tests (all loaded_engine-based — the fixture matrix, error
      cases, single-source, shape-unchanged) were not formally pytest-confirmed in-session (only
      equivalent live/script verification). My own background run of the same command was still building
      the shared loaded_engine fixture after 7+ minutes at review time, unresolved before this report.
    fix: QA must complete `pytest tests/test_readiness.py tests/test_health.py -v` (background, allow
      ~30-60min for the known-slow shared fixture) before merge.
standards:
  state_transitions_server_side: pass
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  ui_evolved_with_capability: pass
  navigation_updated: n/a
  architecture_principles: pass
```
