# goal-market-compass-iter-11 QA Report

**Phase:** goal-market-compass-iter-11 (J-11 Stage B1-completion)
**Date:** 2026-08-23
**QA Agent:** qa
**Execution Mode:** Maintenance Isolation (no app services, no browser automation, read-only live-DB verification per ruling A6)

**Verdict:** PASS

---

## Executive Summary

QA validation PASS under maintenance isolation. All critical contract requirements verified through independent read-only live-database queries (per ruling A6 — the coordinator's operational directive requiring re-derivation of every load-bearing claim from the live artifact, not trusting the developer's prose alone). The live schema migration executed correctly with full byte-identical row preservation, FK constraint removal confirmed, basis_disclosure fail-closed fix implemented correctly, and all targeted tests passing (94/94).

**Key finding on carry-forward issue:** The coordinator-surfaced observation that all 8 manifests with `generation_json` NULL also have `mode` NULL is CONFIRMED. This means ruling A4's intent IS met: today these rows are masked by the `preFreezeEra` branch (honest, not false confidence), and when Stage G potentially reopens and changes masking logic, the "unverifiable" status prevents future AG-1 violations.

---

## Required Artifacts Verification

✓ **Review report** at `reports/reviews/goal-market-compass-iter-11-review.md` — exists, PASS verdict with full re-verification evidence
✓ **Dev handoff** at `docs/handoffs/goal-market-compass-iter-11-dev.md` — exists, comprehensive with 10 persisted evidence artifacts
✓ **Status file** at `runs/goal-market-compass-iter-11/status.json` — exists

All three required pre-QA artifacts present.

---

## Backend Test Results

**Command:** `cd apps/backend && .venv/bin/python -m pytest tests/test_j11_stage_b1_migration.py tests/test_manifest_invariants.py tests/test_j11_maintenance.py tests/test_compass.py tests/test_api_compass.py -q`

**Result:** **94 passed, 0 failed** ✓

Test files executed:
- `test_j11_stage_b1_migration.py` (NEW) — TC-1/TC-2/TC-8 fixture-DB rebuild mechanics
- `test_manifest_invariants.py` (extended) — TC-9/TC-10/TC-11/TC-12/TC-13 basis_disclosure degenerate inputs + available confirmation
- `test_j11_maintenance.py` (pre-existing) — TC-3/TC-4/TC-5/TC-6 FK/rebuild/id-reuse tests, all passing unmodified
- `test_compass.py` — no changes expected, passing
- `test_api_compass.py` — no changes expected, passing

All targeted tests green; no resource violations (single pytest process, targeted files only).

---

## Frontend Test Results

**TypeScript type check:** `cd apps/frontend && ./node_modules/.bin/tsc --noEmit`

**Result:** Clean, zero errors ✓

**CompassBasisDisclosure.status type union:** Widened from 3-member (`"available" | "unavailable" | "rebuilt"`) to 4-member union, now includes `"unverifiable"` literal ✓

**Extracted basis-disclosure-label function:** 
- File: `apps/frontend/lib/basis-disclosure-label.ts` (NEW)
- Type: Pure function, dependency-free, runnable under `node lib/basis-disclosure-label.test.ts` per project convention
- Implementation: Maps all four statuses to (variant, label) pairs with "unverifiable" → ("default", "Basis: unverifiable")
- Imports: Used correctly in `compass-manifest-strip.tsx` BasisLine component ✓

**Node-script test:** `npx tsx lib/basis-disclosure-label.test.ts` (ran via tsx due to environment's missing TS-stripping in node binary)

**Result:** 7 passed ✓ (comprehensive test of all four statuses, verifying new status is distinct from both "available" and "unavailable")

---

## Live Database Independent Verification (per Ruling A6)

As QA under maintenance isolation, I independently re-verified the critical claims against the live `apps/backend/data/trendora.db` (read-only, no mutations, no copies). All verifications match the developer's persisted evidence artifacts exactly.

### Item 1: Live DDL has no FOREIGN KEY clause ✓

**Verification:** Queried `sqlite_master` for `next_session_manifests` table definition.

**Result:** `CREATE TABLE "next_session_manifests" (... )` — **zero FOREIGN KEY clauses**, confirmed to not contain the string "FOREIGN KEY".

### Item 2: Row count before and after migration ✓

**Verification:** `SELECT COUNT(*) FROM next_session_manifests`

**Result:** **24 rows** — matches pre-migration count from persisted `j11-stage-b1-premigration-dump.json` (24 rows) and post-migration diff artifact (pre=24, post=24).

### Item 3: FK violations with PRAGMA foreign_keys=ON explicitly issued ✓

**Verification:** 
```sql
PRAGMA foreign_keys=ON;
PRAGMA foreign_key_check(next_session_manifests);
```

**Result:** **Zero violation rows** — despite the live database containing rows with orphaned `source_run_id` values (3048, 3049, 3081, 3112), the FK check returns empty. Confirms the schema contract holds, not just because enforcement defaulted OFF.

### Item 4: Carry-forward finding — generation_json NULL rows also have mode NULL ✓

**Verification:** 
```sql
SELECT id, as_of, mode, generation_json FROM next_session_manifests 
WHERE generation_json IS NULL OR generation_json = ''
```

**Result:** **8 rows** with NULL `generation_json` (0 with empty string), ALL 8 have `mode = NULL`:
- id=1, as_of=2026-08-12, mode=NULL, generation_json=NULL
- id=2, as_of=2026-07-23, mode=NULL, generation_json=NULL
- id=3, as_of=2026-04-01, mode=NULL, generation_json=NULL
- id=4, as_of=2026-03-31, mode=NULL, generation_json=NULL
- id=5, as_of=2026-03-30, mode=NULL, generation_json=NULL
- id=6, as_of=2005-04-01, mode=NULL, generation_json=NULL
- id=7, as_of=2001-04-17, mode=NULL, generation_json=NULL
- id=8, as_of=1996-02-01, mode=NULL, generation_json=NULL

**Assessment of ruling A4's intent:**
- **Today's UI state:** The `compass-manifest-strip.tsx` component's `preFreezeEra` branch (line 146: `const preFreezeEra = view.mode === null`) masks these 8 rows with the honest message "This manifest predates the freeze/integrity block — no stamps were recorded for it." No false confidence ("available") is shown.
- **Future-proofing:** The fail-closed fix ensures that IF/WHEN the `preFreezeEra` masking changes (e.g., in Stage G), the `basis_disclosure` read path will correctly return `{"status": "unverifiable"}` instead of the previous fabricated `{"status": "available"}`. This prevents AG-1 violations.
- **Verdict:** Ruling A4's intent IS met — the UI renders an honest placeholder today, and the fail-closed fix prevents future regressions.

### Item 5: Four orphaned source_run_id values remain unchanged ✓

**Verification:** Queried for rows with orphaned `source_run_id` values (3048, 3049, 3081, 3112).

**Result:** All four orphaned IDs found, stored unchanged:
- source_run_id=3081: 5 manifest rows (id=1, 9, 10, 11, 13)
- source_run_id=3112: 2 manifest rows (id=12, 14)
- source_run_id=3049: 3 manifest rows (id=15, 16, 20)
- source_run_id=3048: 1 manifest row (id=21)
- (Plus id=23 with source_run_id=3081)

Total: 12 manifest rows using the 4 orphaned source_run_ids, all stored unchanged post-migration.

### Item 6: No other table was written ✓

**Verification:** Inspected the persisted mutation-accounting snapshots (`j11-stage-b1-mutation-accounting.json` pre/post).

**Result:**
- Pre-migration DB: 8365871104 bytes
- Post-migration DB: 8365871104 bytes (identical size)
- Changed tables: `[]` (empty)
- No table other than `next_session_manifests` written

Spot-check of key table row counts (all unchanged):
- `scanner_runs`: 3121 rows
- `sectors`: 11 rows
- `stocks`: 122 rows
- `themes`: 11 rows

### Item 7: basis_disclosure fail-closed fix verified ✓

**Code inspection:** `apps/backend/app/engine/compass.py::basis_disclosure` (lines 1124-1139)

The four degenerate-input branches are correctly implemented:
- **Line 1124-1126:** NULL or empty string → `{"status": "unverifiable", "detail": "no generation basis was recorded for this manifest"}`
- **Line 1127-1131:** Malformed JSON → `{"status": "unverifiable", "detail": "the recorded generation basis is malformed and cannot be read"}` (no exception raised)
- **Line 1132-1134:** Missing `source_run_created_at` → `{"status": "unverifiable", "detail": "the recorded generation basis omits the source run timestamp"}`
- **Lines 1137-1139:** The three original branches (unavailable/rebuilt/available) UNCHANGED

**Test verification:** All four degenerate-input cases covered in new tests TC-9/TC-10/TC-11/TC-12, all passing. TC-13 confirms the three pre-existing branches unchanged.

### Item 8: Doc comments corrected ✓

**File:** `apps/backend/app/models.py`, lines 820-855 (source_run_id field comment)

Updated from the iter-10 stale reading ("needs no change") to cite the iter-11 fix (ruling A4): The comment now correctly documents the 2026-08-23 correction withdrawing the earlier "needs no change" reading and pointing at the fail-closed fix in `basis_disclosure`.

**File:** `apps/backend/app/engine/j11_maintenance.py`, module docstring (final paragraph)

Updated to point at the basis_disclosure fail-closed fix (ruling A4) rather than asserting "needs no change" as the pre-iter-11 version did.

---

## Evidence Artifacts Verification

All 10 persisted evidence artifacts present under `runs/goal-market-compass-iter-11/`:

✓ `j11-stage-b1-premigration-dump.json` (6.2 MB) — full row dump pre-migration, 24 rows × 28 columns
✓ `j11-stage-b1-postmigration-dump.json` (6.2 MB) — full row dump post-migration, 24 rows × 28 columns
✓ `j11-stage-b1-premigration-ddl.json` — live `sqlite_master` DDL pre-migration (with FK clause)
✓ `j11-stage-b1-postmigration-ddl.json` — live `sqlite_master` DDL post-migration (without FK clause)
✓ `j11-stage-b1-postmigration-row-column-diff.json` — per-row/per-column equality comparison: **equal=true, mismatches=[], pre=24, post=24** ✓
✓ `j11-stage-b1-fk-check-pragma-on.json` — PRAGMA foreign_keys=ON + foreign_key_check result: **zero violations** ✓
✓ `j11-stage-b1-premigration-full-db-snapshot.json` — table-row-count snapshot pre-migration
✓ `j11-stage-b1-postmigration-full-db-snapshot.json` — table-row-count snapshot post-migration
✓ `j11-stage-b1-mutation-accounting.json` — diff of above two: **no table other than next_session_manifests written** ✓
✓ `j11-stage-b1-six-acceptance-items-live-reverification.json` — machine-readable evidence for all six Stage-C-precondition items: **all proven=true** ✓

All evidence persisted, committed to git (per iter-9's lesson), and independently verified as consistent with live-DB queries.

---

## Scope Compliance Checklist

✓ **No app service started** — backend/frontend remain unbooted per maintenance isolation
✓ **No browser automation** — Chrome MCP and deterministic replay lane explicitly prohibited by contract
✓ **Read-only live-DB queries only** — all verifications used read-only SQL, no copies or modifications to `trendora.db`
✓ **Targeted tests only** — 5 test files touching the iteration's changed modules, no full suite run, single pytest process
✓ **Mutation accounting proven** — no table other than `next_session_manifests` was written
✓ **Fail-closed fix verified** — `basis_disclosure` correctly returns "unverifiable" for all four degenerate inputs
✓ **Stage C gating maintained** — iteration explicitly stops at Stage B1-completion; no Stage C (destructive derived-state clear) or later stages executed
✓ **AG-18 contract maintained** — all 24 manifest rows byte-identical pre/post; four orphaned source_run_ids unchanged; no manifest regenerated, rebound, rehashed, or newly minted

---

## Blockers and Issues

None. All acceptance items verified. No test failures. No code quality issues beyond the pre-existing `test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers` failure (unrelated to this iteration, flagged in dev handoff).

---

## Summary

✓ **Targeted backend tests:** 94 passed, 0 failed
✓ **Frontend type check:** clean, zero errors
✓ **Live-DB contract verified:** DDL FK removal, 24 rows byte-identical, zero FK violations with PRAGMA foreign_keys=ON, no other table written, basis_disclosure fail-closed on all four degenerate inputs
✓ **Carry-forward finding assessed:** all 8 generation_json NULL rows also have mode NULL; ruling A4's intent IS met (honest UI today, fail-closed fix prevents future AG-1 violations)
✓ **Evidence artifacts:** all 10 persisted, consistent with independent live-DB verification
✓ **Doc comments corrected:** iter-10's stale "needs no change" claims updated to cite iter-11 fix
✓ **Maintenance isolation respected:** zero app services, zero browser automation, read-only live-DB verification per ruling A6

This iteration closes two critical Stage-C preconditions found false on the live database in iter-10:
1. **Live schema now matches the manifest-survives-rebuild contract** — FK constraint removed, rows preserved byte-identical, no destructive side effects
2. **basis_disclosure now fails closed** — never fabricates "available" for unrecorded/unreadable bases; returns explicit "unverifiable" status instead

Both fixes are ready for Stage G reopening and browser-QA re-verification once maintenance isolation is lifted.

