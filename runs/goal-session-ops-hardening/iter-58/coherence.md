# Iteration 58 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-58
**Date:** 2026-08-10
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Scope of this iteration's diff

Bounded diff (`runs/goal-session-ops-hardening/iter-58/iter-diff.md`, 8 files, shown in full — no
truncation) confirmed complete against `git diff 6225bd78bda2c6dd3622c0f6afd6b03dc1d8d07c` (product-code
paths only): `README.md` (prose), `apps/backend/app/engine/data_manager.py`,
`apps/backend/app/models.py`, `apps/backend/tests/test_api_data.py`,
`apps/backend/tests/test_data_manager.py`, `apps/frontend/components/availability-heatmap.tsx`, plus two
new files `apps/frontend/lib/availability-empty-state.ts` and
`apps/frontend/lib/availability-empty-state.test.ts`. The excluded-path `--stat` shows only
`runs/*`/`reports/*`/`docs/handoffs/*` bookkeeping churn (perf-budgets.md correction addendum, J-05.json
golden-date rotation, blueprint changelog paragraph, iter-57 status.json correction) — harness/operational
scope, outside this audit. No product file outside the 8 listed above changed for this iteration (other
working-tree modifications, e.g. `apps/frontend/lib/api.ts`, `apps/backend/app/api/health.py`, pre-date the
iter-58 snapshot SHA and are not part of this diff).

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Availability heatmap — `stale: bool` field | OK | `apps/backend/app/engine/data_manager.py:1708-1758` — same function `availability_from_storage`, same module, same endpoint `GET /api/data/availability` (unchanged). New private helper `_ingest_job_in_flight` (line 1744-1758) reads `DataProviderRun.status == "running"` — verified this is the SAME signal `sweep_orphaned_runs` already reads at `data_manager.py:5296`, not a second/divergent producer. |
| Availability heatmap — `served_dataset_version` field | OK | Unchanged shape/meaning; still read from the single `AvailabilityCache` row (`app/models.py:739-114` docstring corrected, no schema change). |
| Availability heatmap — frontend empty-state gate | OK | `apps/frontend/lib/availability-empty-state.ts:19-20` — pure function `shouldShowAvailabilityEmptyState(data)` derives its answer entirely from the `AvailabilityResponse` object already fetched from the canonical `GET /api/data/availability` endpoint (`cells`/`stale` fields). No new fetch, no client-side recomputation of the underlying value — this is a display-logic extraction, not a second data source. Confirmed precedent: `apps/frontend/lib/background-compute-panel-branch.ts` already establishes this pure-predicate-extraction pattern in this codebase. |
| Availability heatmap — stale banner copy | OK (advisory win, not a violation) | `apps/frontend/components/availability-heatmap.tsx:332` now reads "Data as of a prior scan (version …) — refreshes on the next data job", matching the sibling Coverage panel's phrasing at `apps/frontend/app/data/page.tsx:764` verbatim pattern ("Coverage as of a prior scan (version …) — refreshes on the next data job") — closes the iter-57 coherence advisory rather than introducing a new inconsistency. |

No new displayed value/entity was introduced this iteration (blueprint's own "Data-contract additions:
None" is accurate — confirmed against the diff: no new field, no new table, no new endpoint).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/data` availability heatmap (existing surface, honesty-only fix) | OK | No nav/sidebar/router file touched in this diff. Blueprint IA table (`state/blueprint.md:406`) already lists the Availability heatmap's home as `/data` under Data Manager (J-05/J-09 rows) — unchanged. No new page, route, or parallel shell introduced. |

No new page/route/feature was introduced this iteration — confirmed by the diff (backend: one function's
gating logic + one new private helper in an existing module; frontend: one existing component wired to a
newly-extracted pure predicate function, plus its unit test). Blueprint's own "Blueprint conformance" /
"Product surface delta" fields for this iteration state no IA change, and the diff bears that out.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None beyond what's already noted above (the banner-copy alignment is a positive coherence fix, not a
  new issue).
- Test-file evidence confirms the developer's chosen signal (`data_provider_runs.status == "running"`,
  DB-status-only) was deliberately chosen over the in-memory `_JOBS` registry specifically to avoid a
  false-negative on a crashed-worker's stuck `running` row (`test_availability_from_storage_stuck_running_row_from_crashed_process_still_reads_as_in_flight`,
  `apps/backend/tests/test_data_manager.py:247-274`) — this is the exact edge case the iteration spec's
  "Error cases" section called out; worth noting as good practice, not a coherence issue.
