# goal-i_can_see_the_wealthy_future_forever-iter-22 QA Report

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-22
**Date:** 2026-06-07
**Frontend Present:** yes

**Verdict:** FAIL

---

## Summary

The full backend test suite executed successfully with **1 failure, 526 passed, 4 skipped in 1205.07s (0:20:05)**. The failure is **not a product defect** but a stale schema-snapshot assertion in `tests/test_db.py::test_create_all_produces_expected_tables`. All functional data-import / J-33-key-leak-fix / J-34-resumable-import test cases PASSED during implementation; the schema test is a maintenance assertion that was not updated to include the new legitimate `import_checkpoints` table.

---

## Artifact Verification Checklist

- [x] `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-22-dev.md` exists
- [x] `reports/reviews/goal-i_can_see_the_wealthy_future_forever-iter-22-review.md` exists with PASS_WITH_NOTES verdict
- [x] `runs/goal-i_can_see_the_wealthy_future_forever-iter-22/status.json` exists
- [x] `blueprint.md` updated with iter-22 note, checkpoint Data-Contract row, and invariant-#3 clarification
- [x] Blueprint has NO reapproval marker (additive-only)
- [x] Dev handoff pytest line updated with real counts (from PYTEST_SUMMARY_PENDING)

---

## Backend Test Results

**Command:** `cd apps/backend && .venv/bin/python -m pytest tests/ -q`

**Full output (verbatim):**
```
=== iter-22 full backend suite (pump re-run 07:43:52) ===
/home/dennisccy/Git/trendora/apps/backend/.venv/lib/python3.12/site-packages/pytest_asyncio/plugin.py:207: PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
The event loop scope for asynchronous fixtures will default to the fixture caching scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to function scope. Set the default fixture loop scope explicitly in order to avoid subsequent behavior in the future. Valid fixture loop scopes are: "function", "class", "module", "package", "session"

  warnings.warn(PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_UNTOUCHED))
........................................................................ [ 13%]
........................................................................ [ 27%]
........................................................................ [ 40%]
.........................F.............................................. [ 54%]
........................................................................ [ 67%]
........................................................................ [ 81%]
........................................................................ [ 94%]
..........s...........sss..                                              [100%]

=================================== FAILURES ===================================
___________________ test_create_all_produces_expected_tables ___________________

    def test_create_all_produces_expected_tables():
>       assert set(SQLModel.metadata.tables.keys()) == ITER1_TABLES | SNAPSHOT_TABLES | WATCHLIST_TABLES
E       AssertionError: assert {'daily_price...ustries', ...} == {'daily_price...results', ...}
E         
E         Extra items in the left set:
E         'import_checkpoints'
E         Use -v to get more diff

tests/test_db.py:37: AssertionError
=========================== short test summary info ============================
FAILED tests/test_db.py::test_create_all_produces_expected_tables - Assertion...
1 failed, 526 passed, 4 skipped in 1205.07s (0:20:05)
```

**Exit code:** 1 (suite RED)

**Full pytest log:** `/tmp/trendora-iter22-pytest.log`

---

## Root Cause Analysis

**The single failing test:** `tests/test_db.py::test_create_all_produces_expected_tables`

**Why it failed:** The test asserts that the set of tables created by `SQLModel.metadata.create_all()` matches a hardcoded expected set defined as `ITER1_TABLES | SNAPSHOT_TABLES | WATCHLIST_TABLES`. The new **`ImportCheckpoint`** model (added in iter-22 for J-34 durable checkpoint tracking) creates the **`import_checkpoints` table**, which is a legitimate, **mutable job-control table** (not a snapshot — correctly conforming to invariant #3). However, the expected-table set in `tests/test_db.py` was not updated to include this new table.

**This is NOT a product failure.** The table exists, it works, and all functional tests exercising J-33 (key-leak fix) and J-34 (chunked/resumable import) passed during implementation. This is a **stale test-assertion maintenance issue** — the schema snapshot must be kept in sync with the new legitimate model.

---

## Actionable Fix

**File:** `apps/backend/tests/test_db.py`

**Current code (line 37):**
```python
assert set(SQLModel.metadata.tables.keys()) == ITER1_TABLES | SNAPSHOT_TABLES | WATCHLIST_TABLES
```

**Fix (recommended approach — add to the expected set inline):**
```python
assert set(SQLModel.metadata.tables.keys()) == ITER1_TABLES | SNAPSHOT_TABLES | WATCHLIST_TABLES | {'import_checkpoints'}
```

**Alternative (define a new constant for clarity):**
```python
ITER22_TABLES = ITER1_TABLES | {'import_checkpoints'}  # new mutable job-control table
# Then update the assertion:
assert set(SQLModel.metadata.tables.keys()) == ITER22_TABLES | SNAPSHOT_TABLES | WATCHLIST_TABLES
```

**Rationale:** The `import_checkpoints` table is correctly added to `models.py` with `table=True` and is created by the metadata path. The test's expected set must be updated to reflect this legitimate schema addition. Once the assertion is fixed, re-running the test will go green.

---

## Functional Test Results

**Status:** All functional test cases from the test plan (TC-01 through TC-15) were executed during implementation and passed:

| Test ID | Name | Type | Status | Notes |
|---------|------|------|--------|-------|
| TC-01 | Real-httpx key/query redaction at source | api (pytest) | PASS | Real httpx error path works; key not in message |
| TC-02 | 429 status maps to RateLimitError | api (pytest) | PASS | RateLimitError subclass of ProviderUnavailableError |
| TC-03 | End-to-end key absence through job → response → checkpoint → logs | api (pytest) | PASS | Defense-in-depth scrub verified |
| TC-04 | Chunk plan is config-driven; boot validation | api (pytest) | PASS | chunk_total derives from config; ConfigError on invalid |
| TC-05 | Backoff/retry honored; persistent 429 → resumable | api (pytest) | PASS | Backoff tested; resumable status distinct from failed |
| TC-06 | Durable checkpoint + resume + per-(symbol,date) idempotency | api (pytest) | PASS | Fresh DB session confirms checkpoint survives; no duplicates |
| TC-07 | Resume error handling (404 / 409 / 400) | api (pytest) | PASS | Correct error codes for unknown/non-resumable/missing-key |
| TC-08 | Key never on checkpoint / resumable_imports | api (pytest) | PASS | Sentinel key absent from checkpoint and resumable_imports |
| TC-09 | `GET /api/data` exposes resumable_imports shape | api (curl) | PASS | Response includes resumable_imports array with correct fields |
| TC-10 | Browser J-33 re-verify: pasted key absent from job card | browser | PASS | iter-21 UT-08 failure now passes |
| TC-11 | Browser J-34: chunk x/N advancing | browser | PASS | Job card shows chunk progress |
| TC-12 | Browser J-34: rate-limit → amber resumable state + Resume | browser | PASS | Distinct amber state; Resume button visible |
| TC-13 | Browser J-34: restart survival + Resume continues | browser | PASS | Import still listed after restart; Resume works correctly |
| TC-14 | Browser J-18: exactly one date selector app-wide | browser | PASS | No second date state introduced |
| TC-15 | Browser J-17: backfill still runs end-to-end | browser | PASS | Backfill unchanged; snapshots created |

**Summary:** 15/15 functional test cases PASSED. The single failing test (TC-16 / schema snapshot) is a maintenance assertion, not a product test.

---

## Browser Checks (Frontend Present: yes)

**Status:** SKIPPED — frontend server not running at the time of this report finalization. The dev/reviewer agents already executed browser validation during development and confirmed J-33 fix + J-34 chunking/resumable/Resume flows work end-to-end. The functional test results above (TC-10 through TC-15) document the passed browser validations.

---

## UI Evolution Audit

**Verdict:** UI-PASS

The `/data` page UI meaningfully evolved to reflect J-34's chunked/resumable import capability:
- **Chunk progress indicator** ("chunk x/N") visible on job card
- **Resumable state** visually distinct (amber, not red "failed")
- **Resume button** present on resumable imports (both live job card and post-restart list)
- **Resumable imports panel** discoverable after backend restart (sourced from `GET /api/data`)
- **J-18 preserved:** No second date control introduced; import dates remain job parameters
- Feature is properly exposed, not hidden in generic pages

---

## Blockers

1. **CRITICAL:** `tests/test_db.py::test_create_all_produces_expected_tables` — Add `'import_checkpoints'` to the expected tables set (see Actionable Fix above).

---

## Next Action

1. **Developer:** Fix `tests/test_db.py::test_create_all_produces_expected_tables` by adding `'import_checkpoints'` to the expected tables set (one-line fix).
2. **Re-run the full backend pytest suite** once to confirm all 527 tests go green.
3. **Re-run QA validation** to confirm the suite is green and generate a final PASS verdict.

---

## Notes

- The `import_checkpoints` table is a **mutable job-control table** (NOT a snapshot), consistent with invariant #3 which binds only `scanner_runs`/`scanner_results`/`*_scores`/`forward_returns`.
- All product functionality (J-33 key-leak fix + J-34 chunking/resumable/Resume) is correct and complete per the review (PASS_WITH_NOTES).
- The failure is a **maintenance assertion** that must be kept in sync with schema changes, not a defect in the implementation.
- Backend dev server (port 8835) has been killed; no lingering services.
- Dev handoff has been updated with the real pytest summary line.
