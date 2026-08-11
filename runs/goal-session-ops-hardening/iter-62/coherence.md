# Iteration 62 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-62
**Date:** 2026-08-11
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Backend readiness / boot phase + preflight verdict (`GET /api/health` payload) | OK | `apps/backend/app/api/health.py:83-92` |
| Coverage payload (`GET /api/data`) | OK — untouched this iteration | `-` |

Details:

- `last_run_date` was already a field of the registered `GET /api/health` payload (previously
  hardcoded `None`); this iteration only makes its *value* honest. The fix adds
  `session.scalar(select(func.max(ScannerRun.asof_date)))` directly inside the existing `health()`
  handler (`apps/backend/app/api/health.py:83-92`, imported `ScannerRun` from `app.models`), wrapped
  in the handler's existing `db_ok` try/except so a DB error degrades to `None` — the identical
  pattern the SAME handler already uses for its sibling field `seed_latest_date`
  (`session.scalar(select(func.max(DailyPrice.date)))`, line 84). No new function, class, or module
  was introduced; this is a one-line scalar read, not a business-logic computation with its own
  derivation semantics, so it does not create a second "computing module" for the row.
- `app/engine/data_manager.py` contains prior, pre-existing instances of the exact same
  `select(func.max(ScannerRun.asof_date))` shape (e.g. lines 382, 1203) used for unrelated internal
  purposes (run-history resolution, snapshot-date bookkeeping). This is not a duplicate-computation
  violation under Part A rule 1: it is a trivial `MAX()` read with no transformation logic (unlike a
  `_compute_cagr`/`_compute_sharpe`-style derivation that could diverge), it does not serve the same
  display surface as the `data_manager.py` call sites, and `last_run_date` is not displayed anywhere
  a duplicate could be seen side-by-side (verified below).
- Confirmed `last_run_date` is NOT rendered anywhere in the frontend — `grep -rn "last_run_date"
  apps/frontend/` matches only the pre-existing type declaration at `apps/frontend/lib/api.ts:191`.
  No new UI surface reads this field, so there is no non-canonical-source or synonym-display risk
  (Part A rules 2/4 do not apply).
- The `/data` ambient-refresh fix (`apps/frontend/lib/data-overview-refresh.ts`,
  `apps/frontend/app/data/page.tsx:346-365`) changes only client-side failure-handling state
  transitions on an already-registered value (Coverage payload / availability heatmap). It does not
  add a second fetch source, a second endpoint, or client-side recomputation of the value itself —
  both `loadOverview`'s and `loadAvailability`'s `.catch` handlers still call the SAME
  `fetchDataCoverage`/`fetchDataAvailability` functions against the SAME canonical endpoints
  (`GET /api/data`, `GET /api/data/availability`); only what happens to already-rendered state on a
  rejected promise changed. Grepped for other `setState`/`setAvailability` call sites in the file to
  confirm both catch sites (and only those two) were converted — no inconsistent third site left
  behind (`apps/frontend/app/data/page.tsx:333,349,359,363`).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| N/A — no new page/route/feature this iteration | OK | `-` |

No new page, route, or nav entry was introduced. `/data` and `GET /api/health` both keep their
existing registered homes; no parallel shell or duplicate home was created.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None.
