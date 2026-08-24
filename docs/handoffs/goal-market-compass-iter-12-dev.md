# goal-market-compass-iter-12 Dev Handoff

**Phase:** goal-market-compass-iter-12 (J-11 Stage B1 CLEANUP)
**Date:** 2026-08-24
**Agent:** developer
**Status:** complete

## Governing context

Iteration 11 REGRESSED: the live schema migration removed the unwanted `source_run_id -> scanner_runs.id`
foreign key and preserved all 24 manifest rows exactly, but it rebuilt the shadow table from
`NextSessionManifest.__table__.to_metadata(...)` (MODEL shape) instead of the captured live DDL (LIVE
historical shape), silently dropping three server `DEFAULT` clauses and moving `version` from column
ordinal 9 to 3. The owner's second, binding 2026-08-24 ruling (`docs/goal.md` J-11 step 11, rulings
A8-A14) **accepted** that exact, already-materialized four-item residual, **explicitly refused a second
live rewrite**, and **did not** retroactively clear iter-11's REGRESSION verdict (A14 stands). This
iteration performs the narrow four-job B1 cleanup the owner scoped. **Maintenance isolation stayed
ACTIVE throughout** (ruling A5/A13) — no backend/frontend boot, no browser, no replay lane, and the live
database was **READ-ONLY** for this entire iteration (zero writes, proven below).

## What Was Built

### Job 1 — `j11_schema_migration.create_shadow_table` fixed for future safety (ruling A10)

Root cause: `create_shadow_table` built the shadow table's body from
`NextSessionManifest.__table__.to_metadata(...)` (ORM/model shape) while `rebuild_manifest_table` already
captured the live original `CREATE TABLE` text via `fetch_object_ddl(...)["table_sql"]` and discarded it.

Rewired the flow to: captured original `CREATE TABLE` SQL -> a targeted regex
(`_strip_source_run_id_foreign_key`) locates the EXACT
`FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)` clause (anchored to that literal column and
table name, tolerant only of incidental whitespace — never a generic "any FOREIGN KEY" pattern) -> removes
it and its one adjacent comma -> `_rename_create_table` retargets the `CREATE TABLE` header at the shadow
name (same exactly-once fail-closed discipline) -> the transformed text is executed VERBATIM as raw SQL
-> the newly-created table is reflected back into a SQLAlchemy `Table` via `autoload_with=engine`
(introspection of what was just created, never a second schema construction) so
`copy_rows_to_shadow`/`verify_and_finalize` keep working unchanged. Both fail closed
(`MigrationDdlShapeError`) and abort **before** any table is created or touched if their target text
cannot be located exactly once — never a broad regex that could silently strip an unrelated constraint.

`create_shadow_table`'s signature changed to `create_shadow_table(engine, original_table_sql, shadow_name=...)`.
All three call sites updated: `rebuild_manifest_table` (production orchestration), the live migration
script `scripts/run_j11_stage_b1_manifest_schema_migration.py` (never invoked this iteration — A10/A13),
and the existing TC-8 test.

Static audit (TC-11, AST-level, docstring excluded so its own explanatory prose can't false-positive):
`create_shadow_table`'s CODE contains no call to `.to_metadata(` and no reference to `__table__` — the
production module never builds a table from ORM metadata again.

Module docstring rewritten: the historical "RESIDUAL SCHEMA DELTA" section is preserved (a fact about the
already-executed iter-11 live migration) but reframed as NOT a property of this corrected code path.

**This corrected implementation is fixture-only this iteration — it was never invoked against
`apps/backend/data/trendora.db`** (confirmed: I never opened the live DB for write; the only live-DB
interaction anywhere in this iteration is three read-only SQL scripts, detailed under "Live read-only
verification" below).

### Job 2 — `basis_disclosure`'s A4-bis timestamp-value fail-open closed (`compass.py`)

The confirmed defect: `recorded = generation.get("source_run_created_at")` then
`if recorded is not None and recorded != current: rebuilt` / `else: available` meant `{"source_run_created_at": null}`
reached `available` (fail-open), and `""`/`"garbage"` were reported as `rebuilt` (asserting a rebuild
never actually established, via raw string inequality against a value that was never a real timestamp).

Implemented the complete A4-bis status table, validated BEFORE the match/mismatch branch (iter-7's
ordering lesson):
- `recorded` absent, `None`, non-string, or empty/whitespace-only string -> `unverifiable`
- `recorded` present but fails `datetime.fromisoformat` -> `unverifiable`
- `recorded` parses and, re-canonicalized through the SAME `_utc_isoformat` helper the writer uses, does
  NOT equal the current run's canonicalized `created_at` -> `rebuilt`
- `recorded` parses and equals the current run's -> `available`
- no current `ScannerRun` for this as-of -> `unavailable` (unchanged, already correct)

The already-correct `unavailable` branch and the already-fixed iter-11 branches (`generation_json`
NULL/empty/malformed/non-object/key-absent) are untouched.

### Job 3 — `models.py`'s false provenance comment corrected

Replaced the false claim at the `source_run_id` field ("the live table now matches this model declaration
exactly — no more model/live-DDL divergence") with the true A8/A9 end state: the live table matches the
INTENDED *referential contract* (no live FK; `source_run_id` remains `index=True` historical provenance)
but does NOT physically match model-generated DDL in every historical detail. Names the four owner-accepted
residual differences (`version`/`frozen`/`prospective_eligible` DEFAULT drop; `version` ordinal 9->3) as
known, accepted, and not grounds to reintroduce the FK or rewrite the live table again.

### Job 4 — `preFreezeEra` honesty re-check (static, no boot, no browser)

Read `apps/frontend/components/compass-manifest-strip.tsx`. The `preFreezeEra` branch (`view.mode === null`)
renders ONLY the static sentence "This manifest predates the freeze/integrity block — no stamps were
recorded for it." and NEVER reaches `BasisLine` (that call sits in the `else` branch) or any other status
claim — confirmed by direct source read, line 146-149 vs. the `BasisLine` call at line 186.

Independently re-derived (fresh read-only SQL, not copied from the plan/spec) via
`run_j11_stage_b1_live_reverification.py`:
- `mode IS NULL` count: **8**
- `generation_json` NULL/empty/malformed/non-object/key-absent count: **8**
- Overlap: **8** (complete)

The overlap is complete (8/8), and the component asserts no basis status for this set — **honest,
fail-closed**. No STOP triggered. **Recorded as a Stage G product-verification item** (per A11a); no UI
code change made this iteration.

## Live read-only re-verification

**No application boot, no browser, no network fetch.** The live database
(`apps/backend/data/trendora.db`) was opened ONLY through an ACTUAL SQLite read-only handle
(`file:<path>?mode=ro` — write attempts raise `OperationalError` at the SQLite layer — plus an explicit
`PRAGMA query_only=ON` on every connection) in three scripts, none of which issues a write statement:

- `apps/backend/scripts/run_j11_stage_b1_cleanup_fingerprint.py` — captures a read-only bundle: every
  table's row count + db file mtime/size (`j11_schema_migration.capture_full_db_snapshot`), the manifest
  table's DDL + index text (`fetch_object_ddl`), every manifest row's every column value (`dump_table`),
  and `daily_prices`'s row-count + content fingerprint plus `data_provider_runs`/`watchlist` counts and
  ledger file hashes (`j11_maintenance.capture_pre_reset_inventory`, reused directly). Run once at the
  START of this iteration's work and once at the END.
- `apps/backend/scripts/run_j11_stage_b1_cleanup_fingerprint_diff.py` — diffs the two captures. Result:
  **`identical_except_capture_timestamps: true`** — zero differences other than the two capture-instant
  timestamp fields.
- `apps/backend/scripts/run_j11_stage_b1_live_reverification.py` — TC-20 (fixed `basis_disclosure` run
  read-only against all 24 live manifests) and TC-23 (the `preFreezeEra` overlap, above).

**TC-20 result — the exact live status distribution, independently re-derived (not copied from the
spec):**

| status | count |
|---|---|
| `unverifiable` | 8 |
| `rebuilt` | 9 |
| `available` | 5 |
| `unavailable` | 2 |
| **total** | **24** |

All 8 `unverifiable` rows are exactly the 8 rows whose `generation_json` is degenerate — **zero of them
report `available`** (`no_degenerate_row_reports_available: true`). This live distribution is new evidence
this iteration derived; the planning-time note in `docs/goal.md` said "today, the live database has zero
rows that would newly change status under A4-bis's null/empty/unparseable-value branches" (i.e. every
present `source_run_created_at` value was already well-formed) — my re-run against the FIXED code confirms
that observation held: the 8 `unverifiable` rows are exactly the pre-existing (iter-11-fixed) degenerate-JSON
population, not a new A4-bis-triggered population. A4-bis is a preventive fail-closed guard for a defect
class not yet observed live, exactly as the spec anticipated.

**Additional independent live checks (raw read-only `sqlite3`, `mode=ro`, `PRAGMA foreign_keys=ON`):**
- Live `next_session_manifests` DDL: `FOREIGN KEY` clause absent — confirmed.
- `PRAGMA foreign_key_check(next_session_manifests)` with `foreign_keys=ON`: **0 violations**.
- Manifest row count: **24**.

Full evidence artifacts persisted under `runs/goal-market-compass-iter-12/`:
`j11-stage-b1-cleanup-fingerprint-before.json`, `j11-stage-b1-cleanup-fingerprint-after.json`,
`j11-stage-b1-cleanup-fingerprint-diff.json`, `j11-stage-b1-live-reverification.json`.

## Files Changed

- `apps/backend/app/engine/j11_schema_migration.py` -- `create_shadow_table` now derives the shadow
  table body from the captured live DDL text (never ORM metadata); new `MigrationDdlShapeError`,
  `_strip_source_run_id_foreign_key`, `_rename_create_table`; `rebuild_manifest_table` and
  `copy_rows_to_shadow`'s docstring updated; module docstring reframed (RESIDUAL SCHEMA DELTA is now a
  historical fact about iter-11's live run, not this code path).
- `apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py` -- call-site fix: passes
  `original_ddl["table_sql"]` to `create_shadow_table` (never invoked against the live DB this iteration).
- `apps/backend/app/engine/compass.py` -- `basis_disclosure`: A4-bis fail-closed fix on the recorded
  timestamp VALUE (validate-then-compare, canonicalized through `_utc_isoformat`).
- `apps/backend/app/models.py` -- `source_run_id` field comment corrected to the true A8/A9 end state.
- `apps/backend/tests/test_j11_stage_b1_migration.py` -- `test_audit_ddl_delta_beyond_fk_removal_is_exactly_the_known_residual_set`
  replaced by `test_tc1_through_tc7_corrected_rebuild_matches_original_ddl_exactly_except_the_fk_clause`
  (its premise — that `rebuild_manifest_table` reproduces the residual — is no longer true); new
  `test_tc9_*`, `test_tc10_*` (x2), `test_tc11_*`, `test_tc12_*`, `test_tc21_*` tests added.
- `apps/backend/tests/test_manifest_invariants.py` -- new `test_a4bis_*` cluster (5 tests) covering the
  A4-bis matrix.
- `apps/backend/scripts/run_j11_stage_b1_cleanup_fingerprint.py` -- new: read-only before/after
  fingerprint capture (TC-22).
- `apps/backend/scripts/run_j11_stage_b1_cleanup_fingerprint_diff.py` -- new: diffs two fingerprint
  captures.
- `apps/backend/scripts/run_j11_stage_b1_live_reverification.py` -- new: TC-20 (`basis_disclosure` live
  distribution) + TC-23 (`preFreezeEra` overlap re-derivation).
- `runs/goal-market-compass-iter-12/j11-stage-b1-cleanup-fingerprint-before.json`,
  `-after.json`, `-diff.json`, `j11-stage-b1-live-reverification.json` -- persisted evidence.

No frontend files were modified (Job 4 was a static read + a read-only SQL check only).

## Tests Run

All fixture-DB-only, single process, one file at a time (resource contract). Never run against
`apps/backend/data/trendora.db`; never two pytest processes concurrently.

```
cd apps/backend && .venv/bin/python -m pytest tests/test_j11_stage_b1_migration.py -v
  -> 14 passed
cd apps/backend && .venv/bin/python -m pytest tests/test_manifest_invariants.py -v
  -> 48 passed
cd apps/backend && .venv/bin/python -m pytest tests/test_j11_maintenance.py -q
  -> 9 passed (regression, unmodified)
cd apps/backend && .venv/bin/python -m pytest tests/test_compass.py -q
  -> 28 passed (regression, unmodified)
cd apps/backend && .venv/bin/python -m pytest tests/test_api_compass.py -q
  -> 8 passed (regression, unmodified)
```

**Total: 107 passed, 0 failed** across the five targeted files. No other test file was run (resource
contract — targeted files only, never the full suite, never `-k`-wide sweeps).

**Deliberately NOT run:** anything requiring a backend/frontend boot or a browser (maintenance isolation,
ruling A5) — there is no frontend test command applicable since no frontend file changed.

## Known Issues

- **Pre-existing, unrelated test failure (not introduced by this iteration):**
  `tests/test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers` fails on literals in
  `indicators.py`, `forward_testing.py`, and `research.py` — none of which this iteration touches
  (confirmed via `git status`/`git diff --stat`: only `compass.py`, `j11_schema_migration.py`,
  `models.py`, the migration script, and the test files listed above were modified). `compass.py` IS in
  `CALC_FILES` and passes cleanly — my `basis_disclosure` edit introduced no numeric literal. This
  pre-existing failure is out of this iteration's scope and not fixed here.
- Per ruling A11a/A11b, the manifest export-file discrepancies (recorded `export_path` values with no
  file on disk; files on disk with no manifest row) were NOT investigated or repaired this iteration —
  deferred to Stage G as scoped.
- `models.py`'s `basis_disclosure`-adjacent aside comment (a few lines below the corrected block) still
  says "Fixed directly in `basis_disclosure` (iter-11) — not here" without separately naming iter-12's
  A4-bis follow-on fix. This is not FALSE (iter-11's fix is real and is one of the fixes), just
  incomplete; left as-is to keep this iteration's `models.py` diff narrow, per the spec's explicit
  instruction.
- Job 1's corrected migration code is proven ONLY on fixture databases this iteration, per A10/A13 (never
  run against the live 7.8 GB database). A future authorized live run remains the owner's decision.

## J-11 Stage C readiness — ruling A12 checklist, evaluated individually against this iteration's own evidence

| # | A12 item | Held? | Evidence |
|---|---|---|---|
| 1 | J-10 closed, no stale "20/567" wording remaining | YES | `docs/goal.md` J-11 step 11's own text: "J-10 prerequisite SATISFIED (owner, 2026-08-24)... corrected here rather than deleted." The stale line is explicitly superseded, not deleted, and this iteration does not reopen it (out-of-scope list). |
| 2 | Exact four-item DDL residual accepted and documented | YES | `docs/goal.md` ruling A8/A9 (owner text); `j11_schema_migration.py`'s module docstring "RESIDUAL SCHEMA DELTA" section; `models.py`'s corrected `source_run_id` comment (both name all four: `version`/`frozen`/`prospective_eligible` DEFAULT drop + `version` ordinal 9->3). `test_tc21_models_py_source_run_id_comment_states_the_true_a8_a9_end_state` and `test_tc12_old_orm_metadata_construction_reproduces_the_known_iter11_residual` both pass. |
| 3 | Live manifest FK still absent | YES | Independent read-only query this iteration (`mode=ro`, fresh connection): `FOREIGN KEY` clause absent from `sqlite_master.sql` for `next_session_manifests`. |
| 4 | 24 manifest rows still unchanged | YES | `run_j11_stage_b1_cleanup_fingerprint.py` before/after captures both report `manifest_row_count: 24`, full per-row-per-column values, DDL, and index set; `run_j11_stage_b1_cleanup_fingerprint_diff.py` reports `identical_except_capture_timestamps: true` (zero content diffs). |
| 5 | Migration utility fixed for future exact-DDL-minus-FK behaviour | YES | `test_tc1_through_tc7_corrected_rebuild_matches_original_ddl_exactly_except_the_fk_clause` (TC-1..TC-7), `test_tc9_*` (FK enforcement holds), `test_tc10_*` (fail-closed abort, x2), `test_tc11_*` (static: no ORM-metadata construction), `test_tc12_*` (regression pin proves the OLD code really did produce the residual) — all pass against a PRE-iter-11-shaped fixture. Never run live this iteration (A10/A13). |
| 6 | `basis_disclosure` null/malformed timestamp cases failing closed | YES | `test_a4bis_*` cluster (5 new tests) + pre-existing TC-9..TC-13 (all re-pass unmodified) in `test_manifest_invariants.py`; live re-verification (TC-20) confirms zero of the 8 degenerate-basis live rows report `available`. |
| 7 | `models.py` comment no longer falsely claiming exact physical match | YES | `test_tc21_models_py_source_run_id_comment_states_the_true_a8_a9_end_state` passes; comment rewritten to state the referential-contract-vs-physical-DDL distinction and name the four residuals. |
| 8 | Maintenance isolation still active | YES | No backend/frontend boot, no browser, no replay lane, no network fetch anywhere in this iteration's work. All live-DB interaction was read-only (`mode=ro` + `PRAGMA query_only=ON`). |
| 9 | All targeted tests passing | YES | 107/107 across the five named files (see "Tests Run" above); zero regressions. |
| 10 | Zero live-database writes in the cleanup iteration | YES | `run_j11_stage_b1_cleanup_fingerprint_diff.py`: `identical_except_capture_timestamps: true`. DB file mtime (`1787522416...`) and size (`8365871104`) unchanged from before this iteration's first read to its last. `git status` on `apps/backend/data/` shows nothing. |
| 11 | No new blocker discovered | YES | Job 4's static/read-only re-check confirmed the `preFreezeEra` branch is honest (no STOP triggered). No other new defect surfaced. |

**All eleven items hold, each independently re-derived by this iteration's own evidence (not copied from
the plan or spec).**

**Important caveat, per ruling A6 (unchanged by this iteration):** "Stage C may not begin until BOTH the
schema migration and the `basis_disclosure` fix have passed reviewer, QA, and auditor review AND live
read-only verification... Reviewer and QA marking the DoD 'complete' is not sufficient evidence... the
claim must be re-derived from the live database by the verifying agent." This dev-stage assessment is my
own independently-derived evidence, not a substitute for the reviewer/QA/auditor re-derivation A6
requires. Stage C itself is **not executed** by this iteration regardless of this answer, and requires
explicit owner instruction to resume.

**J-11 STAGE C READY: YES**
