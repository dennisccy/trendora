# Phase goal-ops-hardening-iter-31 — User-Visible Changes

**Status:** N/A — Backend-only phase (Frontend Present: no)

No user-visible changes. All changes are internal backend implementation.

## Context (for the record, not a deviation from the stub verdict)

This iteration closed the session's oldest still-open critical AG-8 finding: `/research/factor-lab?all=true`
crashed with `MemoryError` at `research.py:583` (deferred at iter-29 and iter-30). The fix bounds the return
value's memory representation in `_all_factor_observations_by_horizon` and adds a single-flight de-dup guard
to `factor_lab_all_cached`. Both the plan and the phase spec are explicit that this is availability/
concurrency hardening only: the Factor Lab page's existing decile-table and rank-IC rendering is unchanged,
the response payload is byte-identical to the pre-iteration reference for every `(factor, horizon, decile)`
tuple, and no route, component, label, or layout changed. Files touched are all backend
(`apps/backend/app/engine/research.py`, `apps/backend/app/config.py`, `config.yaml`,
`apps/backend/tests/test_factor_lab_all.py`, `apps/backend/tests/test_research_streaming.py`) — zero
frontend files in the dev handoff's changed-files list.

The only end-user-observable effect is availability: a request that previously 500'd (crashed with
`MemoryError`) on the all-factors view now returns HTTP 200 with the same numeric content it would have
served had the crash not occurred. This is a reliability fix to an existing capability, not a new capability,
not new information displayed, and not a new user action — per the phase spec's own "New user-facing
capability" / "New information displayed" / "New user actions" / "UI surface changes" sections, all of which
state "None" or describe only the crash-to-success transition.
