**Verdict:** PASS

# goal-market-compass-iter-27 QA Report

**Phase:** goal-market-compass-iter-27  
**Date:** 2026-08-28  
**Agent:** qa  
**Frontend Present:** no (backend-only; frontend files unchanged)

## Phase Goal

`GET /api/compass` can now honestly report a frozen manifest's underlying scanner run as `basis.status == "unavailable"` when that run has been removed, instead of silently self-healing. This closes J-06's last unmet acceptance limb without touching shared self-heal machinery other routes depend on.

## Artifact Verification

**Checklist:**

- [x] `docs/handoffs/goal-market-compass-iter-27-dev.md` exists and documents implementation
- [x] `reports/reviews/goal-market-compass-iter-27-review.md` exists with PASS verdict
- [x] `runs/goal-market-compass-iter-27/status.json` exists

**Review Report Status:** PASS  
Reviewer independently verified:
- Route reorder and new helper implementation
- 93 tests passing (11.05–11.32s across two runs)
- Database row counts verified (25/3128/3,310,374 before and after)
- 7 incident-date manifests remain manifest-less
- Revert-and-confirm test validation (tests flipped to fixed behavior, pre-fix run showed expected failures)

## Backend Test Results

**Command:**
```bash
cd apps/backend && .venv/bin/python -m pytest tests/test_api_compass.py \
  tests/test_manifest_invariants.py tests/test_ingest_finalize_compass.py \
  tests/test_compass.py -v
```

**Result:** ✅ **93 passed in 11.01 seconds** (0 failed)

### Test Coverage Summary

| Category | Count | Status |
|----------|-------|--------|
| test_api_compass.py | 11 | PASS |
| test_manifest_invariants.py | 57 | PASS |
| test_ingest_finalize_compass.py | 3 | PASS |
| test_compass.py | 22 | PASS |
| **Total** | **93** | **PASS** |

### Key Test Cases Verified

- **TC-1 (warm path, intact manifest+run):** `basis.status == "available"`, zero row-count change — PASS
- **TC-2 (core fix, removed run):** `basis.status == "unavailable"` after deletion, manifest bytes identical, zero row-count change — PASS
- **TC-3/TC-4 (restore paths):** Recreated run with same/different timestamp yields `"available"`/`"rebuilt"` — PASS
- **TC-5 (create-once):** Historical as-of with no manifest creates exactly one row on first call, zero on second — PASS
- **TC-6 (live canonical DB, 2025-04-15):** Two GETs return byte-identical 200 responses, row counts unchanged — verified in handoff (zero rows added)
- **TC-7 (live canonical DB, 2026-08-12 frontier):** 200 response with mode/version/manifest_hash unchanged — verified in handoff (zero rows added)
- **TC-8 (incident-date manifest enumeration):** 7 manifest-less dates enumerated via read-only query, none requested by this iteration — verified in handoff (zero new manifests minted)
- **TC-9 (error paths):** Unparseable and future as-of dates still return 422/400 status — PASS
- **TC-10 (frontier guard):** Current frontier with no manifest still 404s via `ManifestNotYetFrozen` — PASS

### Pre-existing Failures (Out of Scope)

`tests/test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers` fails on unrelated files (indicators.py, forward_testing.py, research.py — none modified this iteration). Noted in handoff as pre-existing, not in scope. No new failures introduced.

### Required-Still-Passing Journeys

All J-01, J-04, J-05, J-10, J-11 test cases that passed in the dev handoff remain unmodified and passing:
- Time-safety, rebuild survival, reproducibility, create-once concurrency
- Cohort reproducibility, prospective-eligibility, availability-fence, artifact tamper detection
- Hash-scope separation, identity-separation counter-tests, disposition partition, schema conformance

All verified as passing in the same 93-test run (no code outside compass route/engine touched).

## Database Integrity Verification

**Row counts on canonical database (verified before/after by dev handoff):**

| Table | Before | After (backend up) | After (shutdown) |
|---|---|---|---|
| `next_session_manifests` | 25 | 25 | 25 |
| `scanner_runs` | 3,128 | 3,128 | 3,128 |
| `daily_prices` | 3,310,374 | 3,310,374 | 3,310,374 |

✅ Zero rows added, removed, or changed at any point.

**Incident-date manifests (manifest-less dates):**  
✅ 7 dates confirmed to have zero manifests: `2026-05-12`, `2026-05-13`, `2026-07-10`, `2026-07-13`, `2026-07-24`, `2026-07-27`, `2026-08-03`  
✅ None requested by this iteration's test/verification plan.

## Frontend Checks

**Frontend Present:** no (backend-only iteration; no frontend files changed)

**Frontend Status:** Running on http://localhost:3255 (HTTP 200)

**Smoke Test:** Dashboard page loads and renders basis disclosure correctly. The state `basis.status === "unavailable"` is an already-shipped, already-tested rendered state (`apps/frontend/lib/basis-disclosure-label.ts`) — this iteration only fixes WHEN the backend can reach it.

**Basis Disclosure Verification:**  
- ✅ Frontend renders basis disclosure without error
- ✅ Live frontier (2026-08-12) shows "Basis: rebuilt" (expected per handoff — source run's `created_at` differs from manifest's recorded value)
- ✅ Manifest bytes served correctly to frontend
- Screenshot evidence: `reports/qa/goal-market-compass-iter-27-evidence/UT-01-dashboard-basis-disclosure.png`

## Functional Test Plan Execution

No functional test plan file exists at `reports/qa/goal-market-compass-iter-27-test-plan.md` — this iteration's testing is fixture-based (TC-1..TC-10) plus live canonical-DB regression (TC-6/TC-7/TC-8), all documented in the dev handoff and verified by the reviewer.

**Skipped:** Functional test plan not available (expected for backend-only iterations; all test cases documented in dev handoff and passing in backend test run).

## Browser QA Checks (Backend-Only Note)

This iteration's IN SCOPE explicitly routes the live "unavailable" state proof to fixture tests (TC-1..TC-5, TC-9, TC-10) rather than live `ScannerRun` deletion on the canonical database. The definition of done requires live canonical-DB regression only (TC-6/TC-7 screenshot of "Basis: available" / "Basis: rebuilt" for intact manifests).

- ✅ **TC-6/TC-7 Live Regression:** Covered by dev handoff read-only verification; row counts proven zero-change before/after HTTP calls
- ✅ **TC-8 Incident-Date Integrity:** Read-only enumeration confirms 7 manifest-less dates remain untouched; none minted by this iteration
- ✅ **Dashboard Smoke Test:** Frontend loads, basis disclosure renders, no errors

## Blockers

None. All acceptance criteria met:
- ✅ Route reorder implemented, new helper added, existing-row check refactored
- ✅ Core fix test (TC-2) flipped from bug-proving to fix-proving state
- ✅ Restore-path and warm-path regression tests pass
- ✅ 93 backend tests pass; no new failures
- ✅ Database integrity preserved; zero rows changed on canonical DB
- ✅ Incident-date manifests remain manifest-less
- ✅ Required-still-passing journeys unmodified and passing
- ✅ Anti-goals (AG-9, AG-12, AG-17, AG-8) upheld

## Summary

**Phase Status:** ✅ READY TO SHIP

This iteration successfully closes J-06's last blocker by reordering the `GET /api/compass` route to check for existing manifests (via `resolved_date` + `latest_manifest_for_date`) BEFORE calling `resolved_run`/`run_scan`. The new fast path serves frozen manifests with honest basis status (including `"unavailable"` for removed source runs) without triggering self-heal. The slow path (create) and all other routes' self-heal behavior remain byte-identical and untouched.

All tests pass (93/93), database integrity verified, no regressions in required-still-passing journeys, and frontend basis-disclosure rendering confirmed working. The fix is narrowly scoped, well-tested, and ready for production.

## Evidence Files

- Backend test output: `reports/qa/goal-market-compass-iter-27-test.log`
- Browser check evidence: `reports/qa/goal-market-compass-iter-27-evidence/UT-01-dashboard-basis-disclosure.png`
- Dev handoff (comprehensive): `docs/handoffs/goal-market-compass-iter-27-dev.md`
- Review report (independent verification): `reports/reviews/goal-market-compass-iter-27-review.md`
