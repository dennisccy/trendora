# Iteration 61 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-61
**Date:** 2026-08-11
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Summary

This iteration is a narrow, well-scoped bug-fix + evidence pass, not a feature addition. It
targets the iter-60-found `/data` coverage-staleness defect and re-measures J-07 step 2. Diff
against snapshot `b250924e` touches exactly three code files:

- `apps/backend/tests/test_data_manager.py` — new regression test only (production backend code
  unchanged; the diagnosis concluded the backend already served the freshest row correctly).
- `apps/frontend/app/data/page.tsx` — adds one ambient `setInterval` effect that re-invokes the
  page's **existing** `loadOverview()` / `loadAvailability()` / `refresh()` loaders on the shared
  idle poll cadence.
- `apps/frontend/components/readiness-provider.tsx` — exposes an **already-fetched** field
  (`poll_idle_interval_seconds`, already read off the existing `GET /api/health` response, just
  not previously surfaced in context) as `pollIdleIntervalSeconds`, so `/data` can key its ambient
  refresh off the same single poll rather than adding a second one.

No production file in `app/engine/data_manager.py`, `app/api/data.py`, or `app/api/health.py`
changed. No new endpoint, no new route, no new nav entry. `runs/goal-session-ops-hardening/state/blueprint.md`
gained a 2-line narrative update (iter-60 catch-up + iter-61 summary) consistent with the code
diff — no IA or Data Contract table row changed.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Coverage payload (`snapshot_count`/`gap_count`/`snapshot_dates`) | OK | `apps/backend/tests/test_data_manager.py:4192-4278` (new test pins `app.api.data.data_overview`, the existing serving function, against the existing `coverage_snapshot` table — no second producer added); `apps/frontend/app/data/page.tsx:375-393` (new `useEffect` calls the pre-existing `loadOverview`/`loadAvailability` at `page.tsx:329`/`353`, which call `fetchDataCoverage`/`fetchDataAvailability` → `GET /api/data` / `GET /api/data/availability`, unchanged endpoints) |
| Backend readiness / `poll_idle_interval_seconds` | OK | `apps/frontend/components/readiness-provider.tsx:84` (field was already read off the single existing `GET /api/health` poll at `readiness-provider.tsx:74-90`; this iteration only adds it to the exported context value, `:114-115` — no second poll, no second endpoint) |
| Membership timeline / research hot-key caches (Regime Lab "Unavailable" indicator) | OK | No code change this iteration (`reports/phase-goal-ops-hardening-iter-61-ui-surface-map.md:16` confirms evidence-only capture of iter-60-shipped `sample-link.tsx`); reads the same `by_horizon[].status` field via the same `GET /api/research/regime-lab` endpoint |

No new function recomputes coverage, no new UI surface fetches it from a non-canonical source, and
no genuinely new displayed value was introduced this iteration.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/data` (ambient refresh behavior change) | OK | No new route; same existing "Data Manager" home. `apps/frontend/components/sidebar.tsx` unchanged in this diff (not in `git diff b250924e --stat` file list) |
| `/research/regime-lab` (evidence capture only) | OK | No new route; same existing "Research" home; no component change this iteration |

No new page, route, or nav entry was added or needed — `reports/phase-goal-ops-hardening-iter-61-ui-surface-map.md`'s own summary confirms "New pages/routes: 0" and "Navigation changes: no."

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None. The fix reuses the existing `useReadiness()` single poll and the existing `loadOverview`/`loadAvailability` loaders rather than adding parallel fetch logic — this is the coherent pattern the blueprint's IA/Data Contract call for.
