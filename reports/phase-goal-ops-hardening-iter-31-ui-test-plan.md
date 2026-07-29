# Phase goal-ops-hardening-iter-31 — UI Test Plan

**Status:** N/A — Backend-only phase. No UI tests required.

This iteration bounds the return-value memory representation of
`_all_factor_observations_by_horizon` and adds a single-flight de-dup guard to
`factor_lab_all_cached` (`apps/backend/app/engine/research.py`), plus a new `ResearchCfg`
config knob (`apps/backend/app/config.py`, `config.yaml`). All changed files are backend
engine/config/test files. The one route that consumes the changed code,
`GET /research/factor-lab?all=true` (rendered by the existing `/research/factor-lab` page),
is unchanged in its response shape — byte-identical output for every
`(factor, horizon, decile)` tuple is a stated Definition-of-Done requirement — so there is
no UI surface to test.

Functional/API-level coverage (byte-identity, single-flight, shipped-config memory bound,
concurrent-load, MemoryError absence) is exercised by the existing functional test plan at
`reports/qa/goal-ops-hardening-iter-31-test-plan.md` and the backend unit tests in
`apps/backend/tests/test_factor_lab_all.py` — not duplicated here.
