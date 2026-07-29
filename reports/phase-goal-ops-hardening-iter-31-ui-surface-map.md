# Phase goal-ops-hardening-iter-31 — UI Surface Map

**Status:** N/A — Backend-only phase (Frontend Present: no)

No UI surfaces affected.

All changed files are backend engine/config/test files
(`apps/backend/app/engine/research.py`, `apps/backend/app/config.py`, `config.yaml`,
`apps/backend/tests/test_factor_lab_all.py`, `apps/backend/tests/test_research_streaming.py`). The one
route that consumes the changed code, `GET /research/factor-lab?all=true` (rendered by the existing
`/research/factor-lab` page), is unchanged in its response shape — byte-identical output for every
`(factor, horizon, decile)` tuple is a stated Definition-of-Done requirement this iteration — so no row
belongs in this map.
