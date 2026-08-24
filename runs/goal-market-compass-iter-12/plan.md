# goal-market-compass-iter-12 Execution Plan

## Governing context (read before touching anything)

This is a narrow J-11 **Stage B1 CLEANUP** iteration under the owner's second, binding 2026-08-24
ruling (`docs/goal.md` J-11 step 11: rulings A8-A14, AG-18's "Bounded exception on record", the J-10
"SATISFIED" bullet, and the "operative form as of 2026-08-24" sequencing note). That ruling **accepted**
the iter-11 four-item DDL residual (dropped `DEFAULT` on `version`/`frozen`/`prospective_eligible`;
`version` ordinal 9→3) after the fact, **refused a second live rewrite**, and explicitly did **not**
clear iter-11's REGRESSION verdict (A14 — must stand, untouched). Nothing in this iteration reopens
that residual or touches the live table's data.

**Maintenance isolation is ACTIVE** (ruling A5/A13). No backend/frontend boot, no browser automation,
no deterministic-replay lane. All live-DB verification is read-only SQL (`mode=ro` engine / explicit
`PRAGMA query_only=ON`, per iter-11 audit's own pattern) — never open `trendora.db` for write, never
copy the 7.8 GB file (AG-10 — a second full copy is the exact pattern that froze the host 2026-08-20).

**Resource contract:** targeted pytest files only, one process at a time, never the full suite.

## What to Build

Four backend jobs, all fixture-tested + read-only live-verified, zero live writes:

1. **Fix `j11_schema_migration.create_shadow_table` (and its call site in `rebuild_manifest_table`)**
   to derive the shadow table body from the captured live `CREATE TABLE` text
   (`fetch_object_ddl(engine, TABLE_NAME)["table_sql"]`, already captured earlier in
   `rebuild_manifest_table` at `j11_schema_migration.py:270` but currently discarded by
   `create_shadow_table`) instead of `NextSessionManifest.__table__.to_metadata(...)`
   (`j11_schema_migration.py:193-213`, the iter-11 root cause per ruling A10). Transform ONLY the
   exact `FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)` clause out of that captured text
   (verbatim otherwise — column order, types, NOT NULL, server DEFAULTs, PK, unrelated constraints all
   pass through unchanged); execute the transformed DDL (renamed to the shadow table name) via raw SQL,
   then reflect it back into a SQLAlchemy `Table` object so `copy_rows_to_shadow`/`verify_and_finalize`
   keep working unchanged. **Fail closed** (raise before creating/touching any table) if the FK clause
   cannot be located exactly once — no broad regex. Do not redesign `copy_rows_to_shadow` (explicit
   column-name copy, already A10-compliant) or `verify_and_finalize` (verbatim original-index reissue,
   already A10-compliant) — only the table-body source in `create_shadow_table` changes. This corrected
   path is **fixture-only this iteration** — never invoked against `apps/backend/data/trendora.db`
   (A10, A13).
   - Update the module docstring's "RESIDUAL SCHEMA DELTA" section (`j11_schema_migration.py:26-46`):
     keep the historical iter-11 residual record (that's an accepted fact about the *already-migrated
     live table*, not to be deleted), but make clear the corrected implementation itself now reproduces
     the entire pre-migration DDL minus only the FK clause — the residual is a property of iter-11's
     run, not of this iteration's fixed code path.

2. **Close the A4-bis fail-open in `compass.py::basis_disclosure`** (`compass.py:1100-1146`, the
   fall-through at lines 1142-1146: `recorded = generation.get("source_run_created_at")` then
   `if recorded is not None and recorded != current: rebuilt` else `available` — a JSON `null` value
   falls to `available`; an unparseable string falls to `rebuilt` by raw string inequality). Implement
   the full status table from `docs/goal.md` A4-bis (absent/null/empty/unusable/unparseable →
   `unverifiable`; valid timestamp ≠ current → `rebuilt`; valid timestamp = current → `available`; no
   current run → `unavailable`, unchanged). Validate `recorded` into the SAME canonical UTC
   representation the writer already uses — `_utc_isoformat` (`compass.py:664-670`) is what produced
   `current` (line 929's writer path and line 1143's comparison); parse `recorded` (e.g.
   `datetime.fromisoformat`, catching `ValueError`/`TypeError` for non-parseable/non-string values) and
   re-canonicalize through the same helper before comparing — no new independent parser. Validation
   must happen BEFORE the mismatch/match branch (iter-7's ordering lesson, cited in the spec). Do not
   touch the already-correct `unavailable` branch (line 1124-1125) or the already-fixed iter-11
   null/empty/malformed/non-object/key-absent branches (lines 1126-1141).

3. **Correct the false provenance comment in `models.py`** (`models.py:820-856`, specifically the claim
   at line 826-827: *"The live table now matches this model declaration exactly -- no more model/live-DDL
   divergence"*). Replace with the true A8/A9 end state: the live table matches the intended
   *referential contract* (no live FK; `source_run_id` stays `index=True` historical provenance) but does
   **not** physically match model-generated DDL in every historical detail — name the four owner-accepted
   residual differences (A8/A9) as known, accepted, and not grounds to reintroduce the FK or rewrite the
   live table again.

4. **Static, no-boot honesty re-check of the `preFreezeEra` branch** in
   `apps/frontend/components/compass-manifest-strip.tsx` (around line 146, per iter-11's audit finding
   F1) — a fresh, independent read-only SQL query for live manifests where `generation_json` is
   NULL/empty/malformed AND `mode IS NULL`; do not copy iter-11's audit's "8/8 complete overlap, honest"
   conclusion or this spec's own re-statement of it — re-derive both counts from the live DB and
   re-confirm from the component source that the `preFreezeEra` branch never renders `BasisLine` or any
   other status claim. If re-derivation instead finds it asserting/implying a basis status, **STOP the
   iteration** and surface the exact contradiction — do not attempt a UI fix (out of scope, deferred to
   Stage G per A11a).

Plus, mandatory closing artifact: a **read-only before/after fingerprint** of `daily_prices` (row count
+ content fingerprint, reusing `j11_maintenance.capture_pre_reset_inventory`'s price-fingerprint
construction), `scanner_runs`/`forward_returns`/`data_provider_runs`/`watchlist` (row counts), and
`next_session_manifests` (row count + full per-row-per-column values + live DDL text + index set, reusing
`j11_schema_migration.capture_full_db_snapshot`/`diff_snapshots`/`fetch_object_ddl`), taken at the start
and end of this iteration's work, diffed, and persisted under `runs/goal-market-compass-iter-12/` —
proving TC-22 zero live writes.

The dev handoff must end with the explicit line **`J-11 STAGE C READY: YES / NO`**, with every item of
ruling A12's checklist evaluated individually with cited evidence (TC-24). Note per NOTES/A7 in the
spec: if the TC-22 diff shows ANY unexpected change, or a fail-closed abort doesn't hold on a fixture,
STOP and surface for owner review rather than proceeding to any Definition-of-Done claim (this would
also make the answer to Stage C readiness `NO`).

## Agents Required

- **backend-data: yes** — all four jobs above are backend Python (migration engine, `compass.py`,
  `models.py`, fixture tests, read-only live verification scripts).
- **frontend-ux: no** — job 4 is a *static read* of an existing `.tsx` file plus a read-only SQL query;
  no frontend file is edited, no boot, no browser. (The A4-bis status literal set is unchanged — reuses
  the existing 4-member union from iter-11 — so no frontend type/component change is implied either.)

## Frontend Present: no

## Files to Create/Modify

- `apps/backend/app/engine/j11_schema_migration.py` -- fix `create_shadow_table` to build from captured
  live DDL text (not ORM metadata); update module docstring; fail-closed FK-clause extraction.
- `apps/backend/app/engine/compass.py` -- `basis_disclosure`: close the A4-bis timestamp-value fail-open
  (lines ~1142-1146), reusing `_utc_isoformat`.
- `apps/backend/app/models.py` -- correct the `source_run_id` field comment (lines ~820-856, specifically
  826-827) to the true A8/A9 end state.
- `apps/backend/tests/test_j11_stage_b1_migration.py` -- extend with TC-1..TC-11 against the CORRECTED
  implementation (reuse/extend the existing `_LIVE_TABLE_DDL_WITH_FK` / `_LIVE_INDEX_DDLS` fixture,
  lines 35-69) using NEW function names (do not collide with existing `test_tc1_*`/`test_tc2_*`/
  `test_tc8_*`) plus a TC-12 regression-pin test that runs the OLD `__table__`-derived construction
  against the same fixture and asserts it reproduces the known residual.
- `apps/backend/tests/test_manifest_invariants.py` -- extend the `basis_disclosure` cluster (existing
  `test_tc9_*`..`test_tc13_*` at lines 217-320) with new `test_a4bis_*`-named tests covering TC-13..TC-19.
- New read-only verification script(s)/notebook-equivalent (developer's choice of location, e.g. under
  `apps/backend/scripts/` following the existing thin-CLI convention, or an ad-hoc one-off invoked via
  `python -c`/pytest) for: TC-20 (live `basis_disclosure` re-run + status distribution), TC-22
  (before/after fingerprint diff), TC-23 (`preFreezeEra` overlap re-derivation).
- `runs/goal-market-compass-iter-12/*.json` (or `.md`) -- persisted evidence: before/after fingerprints
  and their diff, TC-20's live status distribution, TC-23's re-derived overlap result.
- `docs/handoffs/goal-market-compass-iter-12-dev.md` -- dev handoff, ending with the explicit
  `J-11 STAGE C READY: YES / NO` line and A12 checklist evaluation.

No frontend files are modified.

## Key Test Scenarios

- TC-1..TC-8: fixture-DB proof that the corrected migration output differs from the PRE-iter-11-shaped
  input in exactly one semantic way (FK clause absent) — columns, types, NOT NULL, DEFAULTs, PK, and all
  three original indexes otherwise byte-identical; row values (including the orphaned `source_run_id`)
  unchanged.
- TC-9: with `PRAGMA foreign_keys=ON`, deleting an authorized `ScannerRun` succeeds and the manifest row
  survives, on the fixture.
- TC-10/TC-11: fail-closed abort-before-any-table-touch when the FK clause can't be identified exactly;
  static source-level assertion that `create_shadow_table` never calls `NextSessionManifest.__table__
  .to_metadata()` or any other ORM-metadata table constructor.
- TC-12: the OLD construction, run against the same fixture, reproduces the known iter-11 residual
  (three dropped DEFAULTs, ordinal 9→3) — proves the fix actually fixes something real.
- TC-13..TC-19: `basis_disclosure` A4-bis matrix (null / empty / unusable / unparseable →
  `unverifiable`; valid-mismatched → `rebuilt`; valid-matched → `available`; no-current-run →
  `unavailable`; all iter-11 branches re-confirmed unchanged) — must never raise.
- TC-20: fixed `basis_disclosure` re-run read-only against all 24 live manifests; independently
  re-derived status distribution cited in the handoff (not copied from this plan or the spec); zero of
  the 8 degenerate-`generation_json` rows report `available`.
- TC-21: `models.py` comment no longer claims exact physical DDL match; names the four accepted residual
  differences.
- TC-22: read-only before/after fingerprint across `daily_prices`, `scanner_runs`,
  `next_session_manifests` (values + DDL + indexes), `forward_returns`, `data_provider_runs`,
  `watchlist` — identical, proving zero live writes.
- TC-23: independent re-derivation of the `generation_json`-degenerate ∩ `mode IS NULL` overlap against
  the live DB, cross-checked against the `preFreezeEra` branch's rendered text — record as Stage G item
  if honest, STOP with the exact contradiction if not.
- TC-24: dev handoff's `J-11 STAGE C READY: YES / NO` line, each A12 checklist item evaluated
  individually with its own cited evidence.
- Regression: `test_j11_stage_b1_migration.py`, `test_j11_maintenance.py`, `test_manifest_invariants.py`,
  `test_compass.py`, `test_api_compass.py` re-run unmodified (single process, targeted files only) — zero
  regressions.

## Out of scope (do not build)

- J-11 Stages C-G (destructive clear, regeneration, forward-return repair, cache invalidation, final
  verification) — Stage C begins only after explicit owner instruction following this iteration's
  `J-11 STAGE C READY` answer.
- Running the corrected migration against `apps/backend/data/trendora.db` or any copy of it; any
  `DROP TABLE`, table swap, corrective `ALTER`, ordinal reconstruction, or manifest-row copy live.
  Live database is READ-ONLY this iteration (A13).
- A second live rewrite to restore the three DEFAULT clauses or the original `version` ordinal —
  explicitly not authorized (A8/AG-18's bounded exception).
- Rewriting or softening iter-11's REGRESSION verdict (A14 stands).
- Reopening J-10 or reintroducing "20 restored / 567 pending" framing (superseded/corrected).
- Any actual code fix to the `preFreezeEra` branch (assessed statically only; Stage G's job unless the
  static check finds it dishonest, in which case STOP rather than fix).
- Manifest export-file discrepancy reconciliation (Stage G, ruling A11b).
- Any application-service boot, browser-QA run, or deterministic-replay run.
- Full binary copy/backup of `trendora.db` (AG-10 — the 2026-08-20 freeze-incident pattern).
