**Verdict:** COHERENCE-PASS

# Coherence Audit — Iteration 22

**Iteration:** goal-i_can_see_the_wealthy_future_forever-iter-22
**Date:** 2026-06-07
**Written by:** coherence-auditor

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Resumable import checkpoint (chunk progress, `import_id`, symbols done/remaining, `status`) — J-34 (NEW) | OK | Single computing module: `app.engine.data_manager.resumable_imports()` (`apps/backend/app/engine/data_manager.py:894`). Single canonical serving paths: `GET /api/data` `resumable_imports` (`apps/backend/app/api/data.py:74`), `GET /api/data/jobs/{id}` chunk fields (`apps/backend/app/engine/data_manager.py:206-208`), `POST /api/data/jobs/{import_id}/resume` (`apps/backend/app/api/data.py:118`). Registered in blueprint Data Contract (J-34 row). Not a duplicate of any existing value. |
| Fetched bars (DailyPrice rows) written by the chunked loop | OK | All fetched bars flow through the existing canonical INSERT-new-only `_existing_dates` guard (`apps/backend/app/engine/data_manager.py:284-304`). No second write path introduced. |
| Import provider availability (J-33, existing) | OK | Still computed solely by `compute_provider_availability()` and served by `GET /api/data`. No second computation path added. |
| Dataset coverage / run history (J-17, existing) | OK | `compute_coverage()` and `recent_runs()` unchanged. Not touched by this iteration. |
| All other registered values (six canonical scores, A-E bucket, setup status, forward returns, research analytics, etc.) | OK | Diff confined to `data_providers/`, `engine/data_manager.py`, `api/data.py`, `models.py`, `config.py`, `config.yaml`, `apps/frontend/app/data/page.tsx`, `apps/frontend/lib/api.ts`, and test files. No scoring/snapshot/forward-test/research/read-serving path in the diff. |

The frontend reads `resumable_imports` from `GET /api/data` via `fetchDataCoverage()` (`apps/frontend/app/data/page.tsx:83`) and re-formats it for display only — no client-side recomputation. The `RateLimitError` is a new exception subclass, not a new value computation. The key-leak fix in `_http.py:_provider_error` reshapes an error string at source and computes no canonical value.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/data` — chunk progress badge (`data-testid="chunk-progress"`) | OK | Additive component within the existing `/data` page. Sidebar link confirmed at `apps/frontend/components/sidebar.tsx:39`. Reachable in 1 click. |
| `/data` — amber resumable callout + Resume button on the job card (`data-testid="resumable-state"`) | OK | Same existing `/data` page. No new route or nav entry. |
| `/data` — `ResumableImportsPanel` (`data-testid="resumable-imports"`) | OK | Same existing `/data` page. Consumes `GET /api/data` `resumable_imports` field (existing canonical overview endpoint). Not a second home. |
| `POST /api/data/jobs/{import_id}/resume` | OK | An action endpoint, not a navigable route. Invoked from within the existing `/data` page. No nav entry required or created. |

No new page, route, or nav entry was introduced. No existing entity was given a second home. The sidebar navigation is unchanged. All nine changed UI surfaces (`apps/backend/app/... ui-surface-map.md`) live within the existing approved `/data` (Data Manager) home — reachable in 1 click from the sidebar. The blueprint iter-22 note correctly records NO skeleton change and writes no `blueprint.reapproval-requested` marker.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- J-18 / invariant #5 (exactly one date selector) confirmed: the new chunk/Resume controls add zero date inputs and zero date `useState` (no `type="date"`, no `asOf`/`as_of` state in the `+` lines of the diff). The pre-existing `start`/`end` inputs remain job parameters, not a viewing-date control. Single global as-of switcher is the only viewing-date control. Noted as confirmation, not a finding.
- `resumable` status shares the amber `warn` palette token with `partial` in `statusVariant` (`apps/frontend/app/data/page.tsx:44`). The two states are visually disambiguated by badge text ("rate-limited — resumable" vs "partial") and a dedicated amber callout block. Acceptable design reuse — no actionable coherence drift.
