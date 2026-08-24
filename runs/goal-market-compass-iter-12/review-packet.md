# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 7. Shown in full: 7.

```diff
diff --git a/apps/backend/app/engine/compass.py b/apps/backend/app/engine/compass.py
index b4d051bc..547dc1f5 100644
--- a/apps/backend/app/engine/compass.py
+++ b/apps/backend/app/engine/compass.py
@@ -1098,28 +1098,37 @@ def list_manifest_versions(session: Session, as_of: date) -> list[NextSessionMan
 
 
 def basis_disclosure(session: Session, row: NextSessionManifest) -> dict:
-    """Read-time-only comparison (TC-9..TC-13) — NEVER a mutation, NEVER a recompute of the frozen
+    """Read-time-only comparison (TC-9..TC-19) — NEVER a mutation, NEVER a recompute of the frozen
     content. Compares the manifest's recorded `source_run_created_at` against the CURRENT stored run for
     this `as_of` (never the dataset-version stamp alone, which a rebuild can reproduce byte-identically).
     `{"status": "available"|"unavailable"|"rebuilt"|"unverifiable", "detail": str|None}`.
 
-    Fail-closed fix (docs/goal.md J-11 step 11 ruling A4, owner 2026-08-23 — withdraws iter-10's "needs
-    no change" reading): the ORIGINAL implementation short-circuited `not row.generation_json` straight
-    to `{"status": "available"}`, which FABRICATES "basis intact" for a manifest with no recorded basis
-    at all (verified live: the 2026-08-12 version-1 manifest reported `available` while 8 of 24 live
-    manifests carry `generation_json` NULL — an AG-1 violation on a served surface). `basis_disclosure`
-    must never report a confident "available" claim it cannot actually back. Four degenerate branches
-    now all return the SAME explicit `"unverifiable"` status instead — never `"available"`, never a
-    raised exception:
-      - `generation_json` is NULL or an empty string (TC-9/TC-10) — no recorded basis to compare at all;
-      - `generation_json` is not valid JSON (TC-11) — malformed, caught explicitly, never propagated;
-      - `generation_json` parses but is not a JSON object, or is an object that omits the
-        `source_run_created_at` key (TC-12) — present but incomplete, exactly as unverifiable as
-        absent. The non-object case is guarded explicitly: `"key" in <non-dict>` raises TypeError,
-        which would escape this fail-closed guard as a 500 on the served payload.
-    The three already-correct branches — unavailable (no current run), rebuilt (recorded timestamp
-    differs from the current run's), and available (recorded timestamp matches) — are unchanged
-    (TC-13)."""
+    Fail-closed fix, part 1 (docs/goal.md J-11 step 11 ruling A4, owner 2026-08-23 — withdraws iter-10's
+    "needs no change" reading): the ORIGINAL implementation short-circuited `not row.generation_json`
+    straight to `{"status": "available"}`, which FABRICATES "basis intact" for a manifest with no
+    recorded basis at all. Four degenerate branches — `generation_json` NULL/empty (TC-9/TC-10),
+    malformed JSON (TC-11), and well-formed JSON that is not an object or omits
+    `source_run_created_at` (TC-12) — all return the SAME explicit `"unverifiable"` status, never
+    `"available"`, never a raised exception.
+
+    Fail-closed fix, part 2 — ruling A4-bis (owner 2026-08-24): part 1 closed the branches above `recorded
+    = generation.get("source_run_created_at")`, but left the VALUE of `recorded` unchecked: the original
+    code was `if recorded is not None and recorded != current: rebuilt` / `else: available`, so a key
+    present with JSON value `null` fell through to `available` (still fail-open), and an empty or
+    unparseable string was reported as `rebuilt` — asserting a rebuild that was never established, by raw
+    string inequality rather than a real timestamp comparison. `recorded` is now validated BEFORE any
+    match/mismatch branch is reached (iter-7's ordering lesson: the fail-closed floor must sit before the
+    comparison, never after) — `None`, a non-string, or an empty/whitespace-only string is `unverifiable`
+    (no verifiable timestamp at all); a string that fails to parse via `datetime.fromisoformat` is
+    `unverifiable` (TC-15, e.g. `"garbage"`); only a value that PARSES is re-canonicalized through the
+    SAME `_utc_isoformat` helper the writer used to produce `current` (never a raw string compare) and
+    then compared — equal is `available` (TC-17), unequal is `rebuilt` (TC-16). The complete status
+    table (docs/goal.md A4-bis):
+      absent / `null` / empty / unusable / unparseable  -> `unverifiable`
+      valid timestamp != current run's                  -> `rebuilt`
+      valid timestamp == current run's                  -> `available`
+      no current `ScannerRun` for this as-of             -> `unavailable` (unchanged, TC-18)
+    Never report `available` unless an actual recorded timestamp exists AND matches the current run."""
     current_run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == row.as_of)).first()
     if current_run is None:
         return {"status": "unavailable", "detail": "the underlying scanner run for this as-of is no longer stored"}
@@ -1139,9 +1148,31 @@ def basis_disclosure(session: Session, row: NextSessionManifest) -> dict:
         # `generation_json` is missing, empty, or malformed, or when `source_run_created_at` is absent
         # ... must NEVER report available").
         return {"status": "unverifiable", "detail": "the recorded generation basis omits the source run timestamp"}
+
     recorded = generation.get("source_run_created_at")
     current = _utc_isoformat(current_run.created_at)
-    if recorded is not None and recorded != current:
+
+    # A4-bis, validated BEFORE any match/mismatch branch: `null`, a non-string, or an empty/unusable
+    # string carries no verifiable timestamp at all -- fail closed, never "available", never "rebuilt"
+    # by virtue of a raw string inequality against a value that was never a real timestamp.
+    if recorded is None or not isinstance(recorded, str) or not recorded.strip():
+        return {
+            "status": "unverifiable",
+            "detail": "the recorded source run timestamp is null or empty and cannot be verified",
+        }
+    try:
+        recorded_dt = datetime.fromisoformat(recorded)
+    except (ValueError, TypeError):
+        # present but not parseable as the expected timestamp representation -- fail closed, never
+        # "rebuilt" (that would assert a rebuild this value never actually establishes).
+        return {
+            "status": "unverifiable",
+            "detail": "the recorded source run timestamp could not be parsed and cannot be verified",
+        }
+    # Re-canonicalize the PARSED value through the SAME helper the writer used to produce `current` --
+    # never a raw string compare between two independently-formatted timestamps.
+    recorded_canonical = _utc_isoformat(recorded_dt)
+    if recorded_canonical != current:
         return {"status": "rebuilt", "detail": "the source scanner run was recreated after this manifest was frozen"}
     return {"status": "available", "detail": None}
 
diff --git a/apps/backend/app/engine/j11_schema_migration.py b/apps/backend/app/engine/j11_schema_migration.py
index 82428634..6a374ef3 100644
--- a/apps/backend/app/engine/j11_schema_migration.py
+++ b/apps/backend/app/engine/j11_schema_migration.py
@@ -1,43 +1,48 @@
 """app.engine.j11_schema_migration -- J-11 Stage B1-completion: the ONE authorized live-schema
-migration of `next_session_manifests` (docs/goal.md J-11 step 11, ruling A1, owner 2026-08-23).
+migration of `next_session_manifests` (docs/goal.md J-11 step 11, ruling A1, owner 2026-08-23), FIXED
+for future safety per ruling A10 (goal-market-compass iter-12, owner 2026-08-24).
 
 SQLite cannot drop a constraint in place, so the only way to remove the LIVE
 `FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)` declaration (already dropped from the model
 in `app/models.py` since iter-10, but never applied to the already-created live table -- this repo has
 no Alembic, and `app/db.py`'s schema evolution is additive-ALTER-only) is a mechanical table rebuild:
-create a constraint-free sibling table with the identical column set, copy every row, PROVE full
-row/column equality against a persisted pre-migration dump, and only then drop the original and rename
-the sibling into place (ruling A7's rollback mechanism: the original stays physically intact and
-queryable until equality is proven in the SAME run -- any inequality aborts before the destructive
-step, leaving the original untouched).
-
-Ruling A2/AG-18 bounds this to the mechanical minimum: ONLY the FK constraint is removed. Nothing else
-about the table may change -- not a column, not a stored value (orphaned `source_run_id`s included), and
-not even the INDEX SET. Building the sibling table naively from `NextSessionManifest.__table__` via
-SQLAlchemy's `tometadata()` would silently introduce TWO unauthorized schema drifts, both verified
-empirically while prototyping this module against a throwaway fixture DB:
-  1. `SQLModel.metadata.create_all()` on a table object still carrying the model's declared
-     `index=True` columns (`as_of`, `candidate_rule_hash`, `cohort_rule_hash`, `prospective_eligible`)
-     would create FOUR indexes the LIVE table has never had -- the live table carries only THREE named
-     indexes (`ix_next_session_manifests_content_hash`, `ix_next_session_manifests_source_run_id`,
-     `uq_next_session_manifests_as_of_version`), because `app/db.py`'s additive-ALTER schema evolution
-     backfills new COLUMNS but never retroactively adds an index to an already-existing table.
-  2. The model's inline `UniqueConstraint("as_of", "version", name=...)` (`__table_args__`), if carried
-     into the physical CREATE TABLE, makes SQLite silently materialize a SECOND, redundant
-     `sqlite_autoindex_next_session_manifests_1` alongside the reissued named
-     `uq_next_session_manifests_as_of_version` index below -- the live table has never had that
-     autoindex (it was originally created via a separate raw `CREATE UNIQUE INDEX` in
-     `app/db.py::_INDEX_ADDS`, never as a table-level constraint).
-Both are stripped from the sibling table object before creation; the ORIGINAL table's own three named
-indexes (captured verbatim from `sqlite_master` before anything is touched) are reissued, unmodified,
-onto the renamed table after the swap.
-
-RESIDUAL SCHEMA DELTA -- stated honestly (iter-11 auditor, 2026-08-23). This module previously claimed
-the resulting schema was "byte-for-byte identical to the original except for the one authorized change:
-no FOREIGN KEY clause". That claim was FALSE, and the live migration has already been executed under it.
-Rebuilding from `NextSessionManifest.__table__` reproduces the MODEL's shape, not the live table's
-historical shape, so the post-migration `CREATE TABLE` differs from the pre-migration one in THREE ways
-beyond the authorized FK removal (verified by diffing the two persisted DDL evidence artifacts under
+create a constraint-free sibling table, copy every row, PROVE full row/column equality against a
+persisted pre-migration dump, and only then drop the original and rename the sibling into place
+(ruling A7's rollback mechanism: the original stays physically intact and queryable until equality is
+proven in the SAME run -- any inequality aborts before the destructive step, leaving the original
+untouched).
+
+DDL SOURCE OF TRUTH (ruling A10 -- the iter-12 fix). The sibling table's BODY is now built by
+transforming the table's own CAPTURED `CREATE TABLE` text (`fetch_object_ddl(...)["table_sql"]`, read
+verbatim from `sqlite_master` -- the LIVE historical shape), never from `NextSessionManifest.__table__`
+/ SQLModel metadata (the MODEL shape). `_strip_source_run_id_foreign_key` locates the EXACT
+`FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)` clause via a targeted regex anchored to that
+literal column and table name (tolerant only of incidental whitespace, never a broad "any FOREIGN KEY"
+pattern that could match something unrelated) and removes it -- and ONLY it -- along with its one
+adjacent comma, so the remaining clause list stays syntactically valid SQL; every other token (column
+names, order, types, nullability, server DEFAULTs, primary key, any other constraint) is carried through
+byte-for-byte. If the clause cannot be located EXACTLY ONCE, `create_shadow_table` raises
+`MigrationDdlShapeError` before creating or touching any table -- fail closed, never a guess.
+`_rename_create_table` then retargets the (now FK-free) `CREATE TABLE` header at the shadow name, under
+the identical exactly-once fail-closed discipline; the transformed text is executed verbatim as raw SQL
+(mechanically transformed from the captured original, never hand-authored), and the newly-created table
+is reflected back into a SQLAlchemy `Table` object (`autoload_with=engine` -- introspection of what was
+just created, never a second schema construction) so `copy_rows_to_shadow`/`verify_and_finalize` keep
+working unchanged. Because the shadow table's DDL now comes from the ORIGINAL text, this module no
+longer builds anything from `NextSessionManifest.__table__` at table-construction time, and so has
+nothing to strip -- no `index=True`-derived Index and no inline `UniqueConstraint` ever enters the
+picture. The ORIGINAL table's own three named indexes (captured verbatim from `sqlite_master` before
+anything is touched) are still reissued, unmodified, onto the renamed table after the swap by
+`verify_and_finalize` -- unchanged from before this fix.
+
+RESIDUAL SCHEMA DELTA -- a historical fact about the iter-11 LIVE MIGRATION, not a property of this
+module's corrected code (iter-11 auditor, 2026-08-23; owner ruling A8/A9, 2026-08-24). The PRE-iter-12
+version of this module built the shadow table from `NextSessionManifest.__table__.to_metadata(...)`
+(the MODEL shape), and the iter-11 live run already executed that version against
+`apps/backend/data/trendora.db` before this fix existed. That MODEL-shape rebuild silently reproduced
+the model's shape rather than the live table's historical shape, so the ALREADY-EXECUTED migration's
+post-migration `CREATE TABLE` differs from its pre-migration one in THREE ways beyond the authorized FK
+removal (verified by diffing the two persisted DDL evidence artifacts under
 `runs/goal-market-compass-iter-11/`):
   1. `version INTEGER NOT NULL DEFAULT 1`      -> `version INTEGER NOT NULL`
   2. `frozen BOOLEAN NOT NULL DEFAULT 0`       -> `frozen BOOLEAN NOT NULL`
@@ -48,25 +53,35 @@ default when ALTERing in a NOT NULL column); the model declares only Python-side
 freshly built from the model has never carried them either. No stored value changed, the column NAME set
 and every column's type/NOT NULL are preserved, and no code path depends on the dropped server defaults
 (every write to this table goes through SQLModel, which supplies all three values client-side; no raw
-SQL INSERT targets this table anywhere in the repo). But this is still MORE than ruling A1 / AG-18
-authorized ("removes the FK constraint and NOTHING else"), it is now materialised on the live 7.8 GB
-database, and it is the owner's call -- not this module's -- whether to accept it or require a
-corrective rebuild. `test_j11_stage_b1_migration.py::test_audit_ddl_delta_beyond_fk_removal_is_exactly_the_known_residual_set`
-pins the delta so it can never again be silently described as "nothing else changed".
+SQL INSERT targets this table anywhere in the repo). The owner's 2026-08-24 ruling (A8/A9, `docs/goal.md`)
+ACCEPTS this exact, already-materialized four-item residual on the LIVE database rather than ordering a
+second live rewrite -- that acceptance is about the live table as it stands today, and this module makes
+no attempt to touch it again (A13: the live database is READ-ONLY this iteration). The residual is
+explicitly NOT a property of the CORRECTED implementation below, which reproduces the pre-migration DDL
+text minus ONLY the FK clause (proven fixture-only by `test_j11_stage_b1_migration.py`'s TC-1..TC-8
+against a fixture built with the pre-iter-11 shape). A regression-pin test in that file re-implements the
+OLD ORM-metadata-derived construction LOCALLY (this module itself must never call
+`NextSessionManifest.__table__.to_metadata()` or any other ORM-metadata table constructor again -- TC-11)
+against the same fixture and proves it reproduces this exact residual, so the defect this fix closes
+stays demonstrably real rather than asserted from memory.
 
 One controlled writer, never wired into `app/db.py`'s startup path, touches no other table. Every
 function here is pure/composable so `apps/backend/tests/test_j11_stage_b1_migration.py` can exercise
-each step (including the TC-8 abort-before-rename path) directly against a fixture DB, and
+each step (including the abort-before-rename path) directly against a fixture DB, and
 `apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py` composes them against the LIVE
-database with a persisted evidence artifact after every checkpoint.
+database with a persisted evidence artifact after every checkpoint. This corrected implementation is
+FIXTURE-ONLY for goal-market-compass iter-12 -- it is never invoked against
+`apps/backend/data/trendora.db` this iteration (ruling A10/A13); the live table already carries the
+iter-11-produced (owner-accepted) residual shape and stays exactly as it is.
 """
 from __future__ import annotations
 
+import re
 import sqlite3
 from pathlib import Path
 from typing import Optional
 
-from sqlalchemy import MetaData, PrimaryKeyConstraint, Table, inspect, insert, select, text
+from sqlalchemy import MetaData, Table, inspect, insert, select, text
 from sqlalchemy.engine import Engine
 
 from app.models import NextSessionManifest
@@ -75,14 +90,73 @@ TABLE_NAME = "next_session_manifests"
 SHADOW_TABLE_NAME = "next_session_manifests_new"
 
 
+class MigrationDdlShapeError(RuntimeError):
+    """Raised when the captured `CREATE TABLE` text does not have the EXACT shape this migration is
+    authorized to transform -- either the expected `FOREIGN KEY(source_run_id) REFERENCES
+    scanner_runs (id)` clause is not found exactly once, or the `CREATE TABLE <name> (` header cannot be
+    located exactly once. Fail closed (ruling A10): raised BEFORE any table is created or touched, never
+    a guess from a broad pattern that could silently remove or rename the wrong thing."""
+
+
+# Targeted at the ONE clause ruling A1/A10 authorizes removing -- anchored to the literal column
+# (`source_run_id`) and referenced table (`scanner_runs`) names, tolerant only of incidental whitespace
+# differences (SQLite's `sqlite_master.sql` preserves the CREATE TABLE text verbatim, tabs and all).
+# Deliberately NOT a generic `FOREIGN KEY\(.*\)` pattern -- that could match an unrelated constraint on a
+# differently-shaped future table and silently strip the wrong thing.
+_SOURCE_RUN_ID_FK_RE = re.compile(
+    r"FOREIGN\s+KEY\s*\(\s*source_run_id\s*\)\s*REFERENCES\s*scanner_runs\s*\(\s*id\s*\)",
+    re.IGNORECASE,
+)
+
+
+def _strip_source_run_id_foreign_key(table_sql: str) -> str:
+    """Remove ONLY the exact `FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)` table-constraint
+    clause from a captured `CREATE TABLE` text -- verbatim otherwise. Fails closed
+    (`MigrationDdlShapeError`) unless that exact clause is found exactly once in the text. In the live
+    table's known shape this clause is the trailing table-constraint item, preceded by a comma from the
+    prior clause (`PRIMARY KEY (id),`); that preceding comma is swallowed along with the clause so the
+    remaining text stays valid SQL, falling back to swallowing a FOLLOWING comma if the clause is not
+    last (defensive -- not the live table's shape today, but keeps this function correct if it ever is)."""
+    matches = list(_SOURCE_RUN_ID_FK_RE.finditer(table_sql))
+    if len(matches) != 1:
+        raise MigrationDdlShapeError(
+            "expected exactly one 'FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)' clause in "
+            f"the captured DDL text, found {len(matches)} -- aborting before any table is created or "
+            "touched (ruling A10 fail-closed contract)"
+        )
+    start, end = matches[0].span()
+    before, after = table_sql[:start], table_sql[end:]
+    before_without_comma = re.sub(r",\s*$", "", before)
+    if before_without_comma != before:
+        return before_without_comma + after
+    after_without_comma = re.sub(r"^\s*,", "", after)
+    return before + after_without_comma
+
+
+def _rename_create_table(table_sql: str, old_name: str, new_name: str) -> str:
+    """Retarget ONLY the `CREATE TABLE <old_name> (` header at `new_name` -- verbatim otherwise. Fails
+    closed (`MigrationDdlShapeError`) unless that exact header is found exactly once, so a captured DDL
+    text that does not start the way this module expects is never silently mis-renamed."""
+    pattern = re.compile(r"(CREATE\s+TABLE\s+)" + re.escape(old_name) + r"(\s*\()", re.IGNORECASE)
+    matches = list(pattern.finditer(table_sql))
+    if len(matches) != 1:
+        raise MigrationDdlShapeError(
+            f"expected exactly one 'CREATE TABLE {old_name} (' header in the captured DDL text, found "
+            f"{len(matches)} -- aborting before any table is created or touched"
+        )
+    match = matches[0]
+    replacement = f"{match.group(1)}{new_name}{match.group(2)}"
+    return table_sql[: match.start()] + replacement + table_sql[match.end() :]
+
+
 def fetch_object_ddl(engine: Engine, table_name: str) -> dict:
     """The table's own `CREATE TABLE` text plus every one of its named indexes' `CREATE INDEX` text,
     read verbatim from `sqlite_master` -- never hand-written, never inferred from the ORM model. This
     is the single source both the pre-migration evidence snapshot and the post-migration
-    no-FOREIGN-KEY proof (TC-1/TC-4/TC-6) read from. `sql IS NOT NULL` excludes SQLite's own implicit
+    no-FOREIGN-KEY proof read from. `sql IS NOT NULL` excludes SQLite's own implicit
     `sqlite_autoindex_*` entries (which carry no independent `sql` text) -- irrelevant here since this
-    module's own rebuild never creates one (see module docstring point 2), but kept defensive in case a
-    future live table ever does."""
+    module's own rebuild never creates an autoindex (it neither builds from ORM metadata nor declares
+    any inline table-level UNIQUE constraint), but kept defensive in case a future live table ever does."""
     with engine.connect() as conn:
         table_sql = conn.execute(
             text("SELECT sql FROM sqlite_master WHERE type='table' AND name=:n"), {"n": table_name}
@@ -190,37 +264,40 @@ def diff_snapshots(pre: dict, post: dict) -> dict:
     }
 
 
-def create_shadow_table(engine: Engine, shadow_name: str = SHADOW_TABLE_NAME) -> Table:
-    """Build the constraint-free sibling table under `shadow_name` from `NextSessionManifest.__table__`
-    (SQLModel metadata -- never hand-written DDL) and create it physically. Strips the model's
-    `index=True`-derived Index objects and its inline UniqueConstraint (see module docstring points 1
-    and 2) so the ONLY schema-level effect of this whole module is the dropped `FOREIGN KEY` -- the
-    original table's own three named indexes are reissued verbatim after the swap
-    (`fetch_object_ddl`'s captured `index_sqls`), never regenerated here."""
-    new_metadata = MetaData()
-    shadow = NextSessionManifest.__table__.to_metadata(new_metadata, name=shadow_name)
-    shadow.indexes.clear()
-    # NOTE: deliberately `|=` (set union-assignment), never a `.update(...)` method call -- this repo's
-    # own `test_tc15_no_update_statement_targets_next_session_manifests` static audit flags ANY
-    # `.update(...)` call syntax in a module that mentions the manifest table, as a blunt but effective
-    # guard against an accidental SQL UPDATE against `next_session_manifests`. This is a plain Python
-    # `set` operation (Table.constraints), not a database write of any kind -- `|=` says so unambiguously
-    # to both the reader and that audit.
-    keep_constraints = {c for c in shadow.constraints if isinstance(c, PrimaryKeyConstraint)}
-    shadow.constraints.clear()
-    shadow.constraints |= keep_constraints
-    new_metadata.create_all(engine, tables=[shadow])
-    return shadow
+def create_shadow_table(
+    engine: Engine, original_table_sql: str, shadow_name: str = SHADOW_TABLE_NAME
+) -> Table:
+    """Build the constraint-free sibling table by transforming the CAPTURED LIVE `CREATE TABLE` text
+    (`original_table_sql`, from `fetch_object_ddl(...)["table_sql"]` -- never `NextSessionManifest.
+    __table__` / SQLModel metadata, ruling A10): remove ONLY the exact `FOREIGN KEY(source_run_id)
+    REFERENCES scanner_runs (id)` clause, retarget the `CREATE TABLE` header at `shadow_name`, execute
+    the transformed text VERBATIM as raw SQL, then reflect the newly-created table back into a
+    SQLAlchemy `Table` object (`autoload_with=engine` -- introspection of what was just created, never a
+    second schema construction) so `copy_rows_to_shadow`/`verify_and_finalize` keep working unchanged.
+    Every other token of the original DDL -- column names, order, types, nullability, server DEFAULTs,
+    primary key, any other constraint -- passes through byte-for-byte; the original's own three named
+    indexes are reissued separately, verbatim, by `verify_and_finalize` after the swap (unchanged from
+    before this fix -- this function creates no index of any kind). Fails closed
+    (`MigrationDdlShapeError`, creating/touching no table) if the expected FK clause -- or the
+    `CREATE TABLE` header -- cannot be located exactly once in the captured text."""
+    transformed = _strip_source_run_id_foreign_key(original_table_sql)
+    shadow_sql = _rename_create_table(transformed, TABLE_NAME, shadow_name)
+    with engine.begin() as conn:
+        conn.execute(text(shadow_sql))
+    shadow_metadata = MetaData()
+    return Table(shadow_name, shadow_metadata, autoload_with=engine)
 
 
 def copy_rows_to_shadow(engine: Engine, shadow: Table) -> int:
     """`INSERT INTO <shadow> (<cols>) SELECT <cols> FROM next_session_manifests` via SQLAlchemy Core's
-    `Insert.from_select` (never a hand-written SQL string) -- an explicit column list, so the column
-    ORDER difference between the two table definitions (SQLModel declares `version` at ordinal 3 while
-    the live table's historical order put it at ordinal 9) can never misalign a value into the wrong
-    column. The reorder itself SURVIVES into the rebuilt table and is part of the residual schema delta
-    documented in this module's docstring -- it is not "cosmetic only" in the sense of being within
-    ruling A1's "nothing else" bound; it is simply harmless to the copy."""
+    `Insert.from_select` (never a hand-written SQL string) -- an explicit column list, so this copy is
+    correct regardless of the shadow table's physical column ORDER, which after the ruling-A10 fix
+    matches the captured original's order exactly (no reorder occurs at all; before the fix, the
+    ORM-metadata-derived shadow reordered `version` from its historical ordinal 9 to the model's ordinal
+    3 -- part of the now-accepted, already-materialized iter-11 residual, ruling A8/A9 -- and this
+    explicit-column-name discipline was what kept THAT reorder harmless to the data even though it was
+    still an unauthorized schema change). This function's explicit-column-name discipline is unchanged by
+    the fix (already A10-compliant) and needed either way."""
     cols = [c.name for c in NextSessionManifest.__table__.columns]
     stmt = insert(shadow).from_select(cols, select(NextSessionManifest.__table__))
     with engine.begin() as conn:
@@ -269,7 +346,7 @@ def rebuild_manifest_table(engine: Engine) -> dict:
     caller that does not need that durability guarantee."""
     original_ddl = fetch_object_ddl(engine, TABLE_NAME)
     pre_dump = dump_table(engine, NextSessionManifest.__table__)
-    shadow = create_shadow_table(engine)
+    shadow = create_shadow_table(engine, original_ddl["table_sql"])
     copy_rows_to_shadow(engine, shadow)
     result = verify_and_finalize(engine, shadow, pre_dump, original_ddl["index_sqls"])
     result["original_ddl"] = original_ddl
diff --git a/apps/backend/app/models.py b/apps/backend/app/models.py
index 74cb0d4a..10668ec3 100644
--- a/apps/backend/app/models.py
+++ b/apps/backend/app/models.py
@@ -819,21 +819,39 @@ class NextSessionManifest(SQLModel, table=True):
     version: int = Field(default=1)
     # goal-market-compass iter-10 (J-11 Stage B1): the LIVE `FOREIGN KEY(source_run_id) REFERENCES
     # scanner_runs (id)` DDL is DROPPED from the model declaration here (iter-10: model-declaration change
-    # only, no live-DB migration yet. iter-11 (J-11 Stage B1-completion, ruling A1): the owner
+    # only, no live-DB migration yet). iter-11 (J-11 Stage B1-completion, ruling A1): the owner
     # subsequently AUTHORIZED and this iteration PERFORMED the bounded live-schema migration too -- a
     # mechanical constraint-only table rebuild via `app.engine.j11_schema_migration` /
     # `scripts/run_j11_stage_b1_manifest_schema_migration.py`, proven row/column-identical on the LIVE
-    # database before and after (evidence under `runs/goal-market-compass-iter-11/`). The live table now
-    # matches this model declaration exactly -- no more model/live-DDL divergence). This was a LATENT
-    # contradiction, not a new one: enforcement was already OFF on the live DB (`PRAGMA foreign_keys` reads
-    # `0` -- `app.db._apply_sqlite_pragmas` never issues `PRAGMA foreign_keys=ON`), and
-    # `PRAGMA foreign_key_check(next_session_manifests)` already reported 12 violations on the live DB
-    # before the iter-11 migration, all on incident-dated manifests -- so the FK declaration was never
-    # actually enforced; it was only ever aspirational. Declaring it here as `foreign_key=...` documented a
-    # contract the design does NOT want: AG-12 (manifest immutability) requires a manifest to survive its
-    # source `ScannerRun` being deleted and canonically rebuilt (J-11 Stages C/D, a LATER iteration), and a
-    # rebuilt run legitimately gets a fresh row (or, since `scanner_runs.id` is a plain SQLite rowid alias
-    # with no `AUTOINCREMENT` and no `sqlite_sequence` table, can even REUSE a freed numeric id).
+    # database before and after (evidence under `runs/goal-market-compass-iter-11/`).
+    #
+    # CORRECTED (goal-market-compass iter-12, owner ruling A8/A9, 2026-08-24 -- withdraws the claim this
+    # comment used to make here, that "the live table now matches this model declaration exactly, no more
+    # model/live-DDL divergence"). That claim was FALSE: the iter-11 migration rebuilt the live table's
+    # BODY from `NextSessionManifest.__table__.to_metadata(...)` (MODEL shape) rather than the captured
+    # live DDL (LIVE historical shape), which silently dropped three server-side `DEFAULT` clauses
+    # (`version`, `frozen`, `prospective_eligible`) and moved `version` from column ordinal 9 to 3 --
+    # beyond ruling A1/AG-18's "removes the FK constraint and NOTHING else" bound. The owner's 2026-08-24
+    # ruling ACCEPTS this exact, already-materialized four-item residual on the live database rather than
+    # ordering a second live rewrite (explicitly NOT a general waiver, NOT a precedent, and NOT permission
+    # for further drift -- ruling A8). The TRUE end state: the live table matches the INTENDED
+    # *referential contract* below -- `source_run_id` carries no live FOREIGN KEY constraint and remains
+    # `index=True` historical provenance -- but it does NOT physically match this model's generated DDL in
+    # every historical detail. Both facts are permanent and accepted; neither is grounds to reintroduce
+    # the FK or to rewrite the live table again (`app.engine.j11_schema_migration` was separately fixed in
+    # iter-12, ruling A10, to derive any FUTURE rebuild from captured live DDL rather than ORM metadata --
+    # but that fix is not itself a live rewrite and does not retroactively change today's live shape).
+    #
+    # This was a LATENT contradiction, not a new one: enforcement was already OFF on the live DB
+    # (`PRAGMA foreign_keys` reads `0` -- `app.db._apply_sqlite_pragmas` never issues
+    # `PRAGMA foreign_keys=ON`), and `PRAGMA foreign_key_check(next_session_manifests)` already reported
+    # 12 violations on the live DB before the iter-11 migration, all on incident-dated manifests -- so the
+    # FK declaration was never actually enforced; it was only ever aspirational. Declaring it here as
+    # `foreign_key=...` documented a contract the design does NOT want: AG-12 (manifest immutability)
+    # requires a manifest to survive its source `ScannerRun` being deleted and canonically rebuilt (J-11
+    # Stages C/D, a LATER iteration), and a rebuilt run legitimately gets a fresh row (or, since
+    # `scanner_runs.id` is a plain SQLite rowid alias with no `AUTOINCREMENT` and no `sqlite_sequence`
+    # table, can even REUSE a freed numeric id).
     #
     # Intended end state (docs/goal.md J-11 step 11, verbatim): "`source_run_id` remains stored historical
     # provenance; it is not required to dereference to a live `ScannerRun` forever; manifest survival must
diff --git a/apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py b/apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py
index 69d3e13a..0da3d455 100644
--- a/apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py
+++ b/apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py
@@ -121,7 +121,9 @@ def main() -> int:
     print(f"pre-migration row count: {row_count_before}", file=sys.stderr)
 
     # --- the rebuild itself: create shadow, copy, verify-then-swap (or abort) ----------------------
-    shadow = migration.create_shadow_table(engine)
+    # goal-market-compass iter-12 (ruling A10 fix): the shadow table is now built from the CAPTURED
+    # original DDL text (`original_ddl["table_sql"]`), never from `NextSessionManifest.__table__`.
+    shadow = migration.create_shadow_table(engine, original_ddl["table_sql"])
     migration.copy_rows_to_shadow(engine, shadow)
     result = migration.verify_and_finalize(engine, shadow, pre_dump, original_ddl["index_sqls"])
 
diff --git a/apps/backend/tests/test_j11_stage_b1_migration.py b/apps/backend/tests/test_j11_stage_b1_migration.py
index 9369fab2..7788fd2f 100644
--- a/apps/backend/tests/test_j11_stage_b1_migration.py
+++ b/apps/backend/tests/test_j11_stage_b1_migration.py
@@ -15,15 +15,30 @@ OWN literal function names for iter-10's different scenarios (FK-on delete / reb
 degenerate orphan / id-reuse / attempt-identity). This file's tests cover THIS iteration's own
 Test-first-contract TC-1, TC-2, and TC-8 (the fixture-level items) under distinct function names --
 nothing here renames or touches iter-10's existing tests.
+
+goal-market-compass iter-12 addendum (ruling A10 fix, owner 2026-08-24): `create_shadow_table` now
+takes the captured `original_table_sql` explicitly (all three call sites updated: `rebuild_manifest_table`,
+this file's TC-8 test, and `scripts/run_j11_stage_b1_manifest_schema_migration.py`), and its output
+DDL preserves the original column order and server DEFAULTs verbatim -- so
+`test_audit_ddl_delta_beyond_fk_removal_is_exactly_the_known_residual_set`'s PREMISE (that
+`rebuild_manifest_table` reproduces the iter-11 residual) is no longer true and that test is replaced
+below by `test_tc1_through_tc7_corrected_rebuild_matches_original_ddl_exactly_except_the_fk_clause`,
+which asserts the OPPOSITE (no residual). The historical residual itself is not erased -- it stays real
+and pinned by a NEW regression test, `test_tc12_old_orm_metadata_construction_reproduces_the_known_iter11_residual`,
+which re-implements the OLD (pre-iter-12) ORM-metadata-derived construction LOCALLY in this test file
+only (TC-11 requires the production module itself never do this again). New tests in this addendum use
+distinct names (`test_tc9_*`, `test_tc10_*`, `test_tc11_*`, `test_tc12_*`) that do not collide with any
+existing name in this file or in `test_j11_maintenance.py`.
 """
 from __future__ import annotations
 
+import inspect
 import sqlite3
 from datetime import datetime, timezone
 from pathlib import Path
 
 import pytest
-from sqlalchemy import create_engine, text
+from sqlalchemy import MetaData, PrimaryKeyConstraint, create_engine, text
 
 from app.engine import j11_schema_migration as migration
 from app.models import NextSessionManifest
@@ -168,15 +183,21 @@ def _column_defs(table_sql: str) -> list[tuple[str, str]]:
     return out
 
 
-def test_audit_ddl_delta_beyond_fk_removal_is_exactly_the_known_residual_set(engine):
-    """iter-11 AUDIT: ruling A1 / AG-18 bound this migration to removing the `source_run_id` FOREIGN KEY
-    "and NOTHING else", but rebuilding from `NextSessionManifest.__table__` reproduces the MODEL's shape
-    rather than the live table's historical shape. Three `DEFAULT` clauses that `app/db.py::_COLUMN_ADDS`
-    had attached are dropped, and `version` moves in the column order. No stored value changes and no
-    code path depends on the dropped server defaults -- but the deviation is real, is already
-    materialised on the live database, and must never again be described as "nothing else changed".
-    This test pins the delta so it stays visible for owner adjudication; if a corrective rebuild ever
-    restores the original clauses, this test is the one that must be updated deliberately."""
+def test_tc1_through_tc7_corrected_rebuild_matches_original_ddl_exactly_except_the_fk_clause(engine):
+    """goal-market-compass iter-12 (ruling A10 fix): SUPERSEDES the pre-iter-12
+    `test_audit_ddl_delta_beyond_fk_removal_is_exactly_the_known_residual_set`, whose premise -- that
+    `rebuild_manifest_table` reproduces the iter-11 residual -- is no longer true now that
+    `create_shadow_table` builds the shadow body from the CAPTURED live DDL text instead of
+    `NextSessionManifest.__table__.to_metadata(...)`. Proves TC-1 (ordered column name list), TC-2
+    (column types), TC-3 (NOT NULL flags), TC-4 (DEFAULT clauses -- including the three the OLD
+    implementation dropped), TC-5 (primary key), and TC-7 (the captured pre/post `CREATE TABLE` text
+    differs in EXACTLY one way: the absent FK clause -- column order, including `version`'s ordinal, is
+    untouched). TC-6 (index set) stays covered by `test_tc1_resulting_index_set_matches_the_original_exactly`
+    above, unaffected by this change. TC-8 (row values) stays covered by
+    `test_tc1_rebuild_drops_fk_preserves_row_count_and_every_column_including_orphan` above. The
+    historical iter-11 residual this test used to pin is NOT erased -- see
+    `test_tc12_old_orm_metadata_construction_reproduces_the_known_iter11_residual` below, which proves it
+    against a local reimplementation of the OLD construction instead."""
     pre = migration.fetch_object_ddl(engine, migration.TABLE_NAME)["table_sql"]
     result = migration.rebuild_manifest_table(engine)
     assert result["status"] == "completed"
@@ -184,37 +205,182 @@ def test_audit_ddl_delta_beyond_fk_removal_is_exactly_the_known_residual_set(eng
 
     pre_cols, post_cols = _column_defs(pre), _column_defs(post)
 
-    # what IS preserved: the exact column name set, and every column's type + NOT NULL-ness
-    assert {n for n, _ in pre_cols} == {n for n, _ in post_cols}
+    # TC-1: identical ORDERED column name list (not just the same set)
+    assert [n for n, _ in pre_cols] == [n for n, _ in post_cols]
+
     pre_by_name = dict(pre_cols)
     post_by_name = dict(post_cols)
     for name, pre_def in pre_by_name.items():
-        assert post_by_name[name].startswith(f"{name} {pre_def.split()[1]}"), name
-        assert ("NOT NULL" in pre_def) == ("NOT NULL" in post_by_name[name]), name
-
-    # the ONE authorized change
+        post_def = post_by_name[name]
+        # TC-2: identical declared TYPE
+        assert post_def.split()[1] == pre_def.split()[1], name
+        # TC-3: identical NOT NULL flag
+        assert ("NOT NULL" in pre_def) == ("NOT NULL" in post_def), name
+        # TC-4: identical DEFAULT clause presence AND value -- the exact three columns the OLD approach
+        # dropped (`version`, `frozen`, `prospective_eligible`) now survive the rebuild unchanged
+        assert ("DEFAULT" in pre_def) == ("DEFAULT" in post_def), name
+        if "DEFAULT" in pre_def:
+            assert pre_def.split("DEFAULT", 1)[1] == post_def.split("DEFAULT", 1)[1], name
+
+    for name in ("version", "frozen", "prospective_eligible"):
+        assert "DEFAULT" in post_by_name[name], f"{name}'s server DEFAULT must survive (ruling A10 fix)"
+
+    # TC-5: identical PRIMARY KEY declaration
+    assert "PRIMARY KEY (id)" in pre
+    assert "PRIMARY KEY (id)" in post
+
+    # TC-7: the ONLY textual difference between pre and post column definitions is the absent FK
+    # clause -- no column reorder (unlike the pre-iter-12 implementation, which moved `version` from
+    # ordinal 9 to 3), and every column definition is byte-identical
     assert "FOREIGN KEY" in pre
     assert "FOREIGN KEY" not in post
+    assert [n for n, _ in pre_cols].index("version") == 8
+    assert [n for n, _ in post_cols].index("version") == 8
+    assert pre_by_name == post_by_name
+
+
+# --- TC-9: FK enforcement holds by contract, not merely because it is off -------------------------------
+
+
+def test_tc9_deleting_scanner_run_with_fk_enforcement_on_succeeds_and_manifest_survives(engine, db_path):
+    """TC-9: with `PRAGMA foreign_keys=ON` explicitly issued on the SAME connection that performs the
+    delete, deleting the `ScannerRun` two manifest rows point at succeeds, and both manifest rows survive
+    unchanged -- the contract holds by schema (no declared FK), not merely because enforcement defaults
+    off."""
+    result = migration.rebuild_manifest_table(engine)
+    assert result["status"] == "completed"
+
+    raw = sqlite3.connect(str(db_path))
+    try:
+        raw.execute("PRAGMA foreign_keys=ON")
+        raw.execute("DELETE FROM scanner_runs WHERE id = 1")
+        raw.commit()
+        remaining = raw.execute(
+            "SELECT COUNT(*) FROM next_session_manifests WHERE source_run_id = 1"
+        ).fetchone()[0]
+    finally:
+        raw.close()
+    # fixture rows 1 and 3 both carry source_run_id=1 -- both survive the delete unrebound
+    assert remaining == 2
 
-    # the residual, UNAUTHORIZED-but-materialised deltas -- asserted exactly, neither more nor fewer
-    lost_default = sorted(
-        name for name, pre_def in pre_by_name.items()
-        if "DEFAULT" in pre_def and "DEFAULT" not in post_by_name[name]
+
+# --- TC-10: fail-closed abort BEFORE any table is created or touched -------------------------------------
+
+
+def test_tc10_ambiguous_fk_clause_aborts_before_any_table_created_or_touched(engine):
+    """TC-10: if the expected FK clause has been altered so it no longer matches exactly,
+    `create_shadow_table` raises `MigrationDdlShapeError` before creating or touching any table -- no
+    shadow table is left behind, and the original table is completely untouched."""
+    original_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
+    mangled = original_ddl["table_sql"].replace(
+        "FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)",
+        "FOREIGN KEY(some_other_column) REFERENCES some_other_table (id)",
     )
-    assert lost_default == ["frozen", "prospective_eligible", "version"]
-    gained_default = [
-        name for name, pre_def in pre_by_name.items()
-        if "DEFAULT" not in pre_def and "DEFAULT" in post_by_name[name]
-    ]
-    assert gained_default == []
-    assert [n for n, _ in pre_cols].index("version") == 8
-    assert [n for n, _ in post_cols].index("version") == 2
-    # and nothing ELSE about any column definition differs
-    other_diffs = sorted(
-        name for name, pre_def in pre_by_name.items()
-        if pre_def.replace(" DEFAULT 1", "").replace(" DEFAULT 0", "") != post_by_name[name]
+    assert mangled != original_ddl["table_sql"]  # sanity: the mangle actually took effect
+
+    with pytest.raises(migration.MigrationDdlShapeError):
+        migration.create_shadow_table(engine, mangled)
+
+    with engine.connect() as conn:
+        shadow_exists = conn.execute(
+            text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=:n"),
+            {"n": migration.SHADOW_TABLE_NAME},
+        ).scalar()
+    assert shadow_exists == 0
+
+    post_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
+    assert post_ddl == original_ddl
+
+
+def test_tc10_duplicated_fk_clause_also_aborts_before_any_table_created_or_touched(engine):
+    """TC-10 (second case): a captured DDL text containing the expected FK clause TWICE is just as
+    ambiguous as containing it zero times -- "exactly once" is enforced both ways, never "at least
+    once"."""
+    original_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
+    duplicated = original_ddl["table_sql"].replace(
+        "FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)\n)",
+        "FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id),\n"
+        "\tFOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)\n)",
     )
-    assert other_diffs == []
+    assert duplicated != original_ddl["table_sql"]
+
+    with pytest.raises(migration.MigrationDdlShapeError):
+        migration.create_shadow_table(engine, duplicated)
+
+    with engine.connect() as conn:
+        shadow_exists = conn.execute(
+            text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=:n"),
+            {"n": migration.SHADOW_TABLE_NAME},
+        ).scalar()
+    assert shadow_exists == 0
+
+
+# --- TC-11: static audit -- create_shadow_table never builds from ORM metadata ---------------------------
+
+
+def test_tc11_create_shadow_table_never_builds_from_orm_metadata():
+    """TC-11: static source-level audit (same style as
+    `test_manifest_invariants.py::test_tc15_no_update_statement_targets_next_session_manifests`) --
+    the corrected `create_shadow_table` references only the captured `original_table_sql` text as the
+    table-body source and contains no call to `NextSessionManifest.__table__.to_metadata()` or any other
+    ORM-metadata table constructor. Checked at the AST level over the function BODY only (the docstring
+    is dropped first) so the docstring's own prose -- which names exactly these forbidden patterns to
+    explain what changed -- can never produce a false positive."""
+    import ast
+
+    source = inspect.getsource(migration.create_shadow_table)
+    func_node = ast.parse(source).body[0]
+    body = func_node.body
+    if (
+        body
+        and isinstance(body[0], ast.Expr)
+        and isinstance(getattr(body[0], "value", None), ast.Constant)
+        and isinstance(body[0].value.value, str)
+    ):
+        body = body[1:]  # drop the docstring node -- checking CODE, never prose
+    code_dump = ast.dump(ast.Module(body=body, type_ignores=[]))
+    assert "to_metadata" not in code_dump
+    assert "__table__" not in code_dump
+    assert "create_all" not in code_dump
+
+
+# --- TC-12: regression pin -- the OLD ORM-metadata construction really did produce the residual ----------
+
+
+def test_tc12_old_orm_metadata_construction_reproduces_the_known_iter11_residual(engine):
+    """TC-12: the OLD (pre-iter-12) `NextSessionManifest.__table__`-derived construction, RE-IMPLEMENTED
+    HERE ONLY -- never in the production module again, per TC-11 -- run against the SAME PRE-iter-11
+    fixture, reproduces exactly the known iter-11 residual: three dropped server DEFAULT clauses and
+    `version` moved from column ordinal 9 to 3. This proves the corrected implementation (TC-1..TC-8
+    above) fixes a REAL, reproduced defect, not merely a hypothetical one. The throwaway table this test
+    creates is dropped at the end; it is never the live `next_session_manifests` table."""
+    pre = migration.fetch_object_ddl(engine, migration.TABLE_NAME)["table_sql"]
+
+    old_shadow_name = "next_session_manifests_old_orm_pin"
+    new_metadata = MetaData()
+    shadow = NextSessionManifest.__table__.to_metadata(new_metadata, name=old_shadow_name)
+    shadow.indexes.clear()
+    keep_constraints = {c for c in shadow.constraints if isinstance(c, PrimaryKeyConstraint)}
+    shadow.constraints.clear()
+    shadow.constraints |= keep_constraints
+    new_metadata.create_all(engine, tables=[shadow])
+
+    try:
+        post = migration.fetch_object_ddl(engine, old_shadow_name)["table_sql"]
+
+        pre_cols, post_cols = _column_defs(pre), _column_defs(post)
+        pre_by_name, post_by_name = dict(pre_cols), dict(post_cols)
+
+        lost_default = sorted(
+            name for name, pre_def in pre_by_name.items()
+            if "DEFAULT" in pre_def and "DEFAULT" not in post_by_name[name]
+        )
+        assert lost_default == ["frozen", "prospective_eligible", "version"]
+        assert [n for n, _ in pre_cols].index("version") == 8
+        assert [n for n, _ in post_cols].index("version") == 2
+    finally:
+        with engine.begin() as conn:
+            conn.execute(text(f'DROP TABLE "{old_shadow_name}"'))
 
 
 # --- TC-2: PRAGMA foreign_keys=ON explicitly issued post-rebuild -- zero violations despite the orphan
@@ -241,7 +407,7 @@ def test_tc8_injected_equality_mismatch_aborts_before_rename_original_untouched(
     original_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
     pre_dump = migration.dump_table(engine, NextSessionManifest.__table__)
 
-    shadow = migration.create_shadow_table(engine)
+    shadow = migration.create_shadow_table(engine, original_ddl["table_sql"])
     migration.copy_rows_to_shadow(engine, shadow)
 
     # deliberately inject a one-byte equality mismatch between the pre-copy source and the newly-copied
@@ -318,3 +484,33 @@ def test_diff_snapshots_flags_only_the_table_whose_count_changed():
     diff2 = migration.diff_snapshots(pre, post_mutated_other_table)
     assert diff2["changed_tables"] == [{"table": "daily_prices", "before": 1000, "after": 1001}]
     assert diff2["no_table_other_than_next_session_manifests_written"] is False
+
+
+# --- TC-21: models.py's source_run_id comment states the TRUE A8/A9 end state ----------------------------
+
+
+def test_tc21_models_py_source_run_id_comment_states_the_true_a8_a9_end_state():
+    """TC-21: `models.py`'s `source_run_id` field comment must state the TRUE A8/A9 end state -- the
+    live table matches the intended REFERENTIAL CONTRACT (no live FK; `source_run_id` remains
+    `index=True` historical provenance) but does NOT claim exact physical DDL match, and must name the
+    four owner-accepted residual differences (ruling A8/A9). The FALSE claim this replaced -- "the live
+    table now matches this model declaration exactly -- no more model/live-DDL divergence" -- must never
+    reappear."""
+    import app.models as models_module
+
+    source = Path(models_module.__file__).read_text()
+    marker = "source_run_id: int = Field(index=True)"
+    field_pos = source.index(marker)
+    preceding_comment = "\n".join(source[:field_pos].splitlines()[-45:])
+
+    # the withdrawn false claim must not reappear
+    assert "matches this model declaration exactly" not in preceding_comment
+    assert "no more model/live-DDL divergence" not in preceding_comment
+
+    # the true end state: referential contract yes, exact physical DDL match no
+    assert "referential contract" in preceding_comment.lower()
+    assert "not physically match" in preceding_comment.lower()
+
+    # the four owner-accepted residual differences (ruling A8/A9) are named
+    for token in ("version", "frozen", "prospective_eligible", "ordinal"):
+        assert token in preceding_comment, token
diff --git a/apps/backend/tests/test_manifest_invariants.py b/apps/backend/tests/test_manifest_invariants.py
index aade4b37..3df682b4 100644
--- a/apps/backend/tests/test_manifest_invariants.py
+++ b/apps/backend/tests/test_manifest_invariants.py
@@ -309,6 +309,114 @@ def test_tc13_basis_disclosure_available_branch_still_reports_available_when_rec
     assert disclosure == {"status": "available", "detail": None}
 
 
+# --- A4-bis: the recorded-TIMESTAMP-VALUE fail-open (goal-market-compass iter-12, docs/goal.md J-11 -----
+# step 11 ruling A4-bis, owner 2026-08-24). The iter-11 fix above closed every branch that examines
+# `generation_json`'s SHAPE (missing/empty/malformed/non-object/key-absent). It left the VALUE of a
+# PRESENT `source_run_created_at` key unchecked: `recorded = generation.get(...)` followed by
+# `if recorded is not None and recorded != current: rebuilt` / `else: available` meant a key present
+# with JSON value `null` fell through to "available" (still fail-open), and an empty or unparseable
+# string was reported as "rebuilt" by raw string inequality -- asserting a rebuild that was never
+# established. These tests cover the A4-bis status table; valid-matched -> available is already covered
+# by test_tc13_basis_disclosure_available_branch_still_reports_available_when_recorded_timestamp_matches
+# above and no-current-run -> unavailable is already covered by
+# test_basis_disclosure_reads_unavailable_when_the_source_run_is_gone above -- both re-confirmed
+# unchanged by this fix and not duplicated here.
+
+
+def test_a4bis_recorded_timestamp_null_value_is_unverifiable_not_available(engine, cfg, frontier_run):
+    """A4-bis (TC-13): a `source_run_created_at` key present with JSON value `null` must report
+    `unverifiable`, never `available` -- the exact fail-open the ORIGINAL `recorded is not None` guard
+    let through."""
+    with Session(engine) as session:
+        run = session.get(ScannerRun, frontier_run)
+        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
+        row.generation_json = json.dumps({"producer": "ingest_finalize", "source_run_created_at": None})
+        session.add(row)
+        session.commit()
+    with Session(engine) as session:
+        row = session.exec(select(NextSessionManifest)).first()
+        disclosure = compass.basis_disclosure(session, row)  # must not raise
+    assert disclosure["status"] == "unverifiable"
+    assert disclosure["status"] != "available"
+
+
+def test_a4bis_recorded_timestamp_empty_string_is_unverifiable_not_rebuilt(engine, cfg, frontier_run):
+    """A4-bis (TC-14): an empty-string `source_run_created_at` is unusable, not a valid timestamp that
+    happens to differ -- must report `unverifiable`, never the confident `rebuilt` claim a raw string
+    inequality against "" would have produced."""
+    with Session(engine) as session:
+        run = session.get(ScannerRun, frontier_run)
+        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
+        row.generation_json = json.dumps({"producer": "ingest_finalize", "source_run_created_at": ""})
+        session.add(row)
+        session.commit()
+    with Session(engine) as session:
+        row = session.exec(select(NextSessionManifest)).first()
+        disclosure = compass.basis_disclosure(session, row)  # must not raise
+    assert disclosure["status"] == "unverifiable"
+    assert disclosure["status"] not in ("available", "rebuilt")
+
+
+def test_a4bis_recorded_timestamp_unparseable_string_is_unverifiable_not_rebuilt(engine, cfg, frontier_run):
+    """A4-bis (TC-15): a `source_run_created_at` value that is not parseable as the canonical UTC
+    timestamp representation (e.g. "garbage") must report `unverifiable`, never `rebuilt` -- the
+    ORIGINAL raw-string-inequality comparison would have called this "rebuilt", asserting a rebuild the
+    value never actually establishes."""
+    with Session(engine) as session:
+        run = session.get(ScannerRun, frontier_run)
+        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
+        row.generation_json = json.dumps(
+            {"producer": "ingest_finalize", "source_run_created_at": "garbage"}
+        )
+        session.add(row)
+        session.commit()
+    with Session(engine) as session:
+        row = session.exec(select(NextSessionManifest)).first()
+        disclosure = compass.basis_disclosure(session, row)  # must not raise
+    assert disclosure["status"] == "unverifiable"
+    assert disclosure["status"] not in ("available", "rebuilt")
+
+
+def test_a4bis_recorded_timestamp_valid_but_mismatched_is_rebuilt(engine, cfg, frontier_run):
+    """A4-bis (TC-16): a VALID, PARSEABLE `source_run_created_at` that does not equal the current run's
+    canonicalized `created_at` still reports `rebuilt` -- the fail-closed validation gates entry to the
+    mismatch branch, it does not disturb it."""
+    with Session(engine) as session:
+        run = session.get(ScannerRun, frontier_run)
+        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
+        row.generation_json = json.dumps(
+            {"producer": "ingest_finalize", "source_run_created_at": "2020-01-01T00:00:00+00:00"}
+        )
+        session.add(row)
+        session.commit()
+    with Session(engine) as session:
+        row = session.exec(select(NextSessionManifest)).first()
+        disclosure = compass.basis_disclosure(session, row)
+    assert disclosure["status"] == "rebuilt"
+
+
+def test_a4bis_full_generation_json_degenerate_matrix_never_available(engine, cfg, frontier_run):
+    """A4-bis (widened TC-19 matrix): the required minimum degenerate-input set -- NULL, empty string,
+    malformed JSON, `[]`, `{}` -- re-run after this fix, each still resolves to `unverifiable`, never
+    raises, and never reports `available`. `[]` and `{}` were not previously exercised by their own name
+    (iter-11's tests used "5" / a populated non-object dict / a non-empty list); added here for the
+    explicit minimum matrix this iteration's spec names."""
+    for degenerate in (None, "", "{not valid json", "[]", "{}"):
+        with Session(engine) as session:
+            row = session.exec(select(NextSessionManifest)).first()
+            if row is None:
+                run = session.get(ScannerRun, frontier_run)
+                row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
+            row.generation_json = degenerate
+            session.add(row)
+            session.commit()
+        with Session(engine) as session:
+            row = session.exec(select(NextSessionManifest)).first()
+            disclosure = compass.basis_disclosure(session, row)  # must not raise
+        assert disclosure["status"] == "unverifiable", degenerate
+        assert disclosure["status"] != "available", degenerate
+
+
 # --- TC-16 (reproducibility) -----------------------------------------------------------------------
 
 
diff --git a/docs/goal.md b/docs/goal.md
index d4548129..2579dedc 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -791,6 +791,11 @@ manifest artifact (it must be self-describing and self-caveating).
        > Completing the remaining 567 raw-price rows does not automatically refresh the already-existing
        > 2026-08-11 / 2026-08-12 `ScannerRun`s. They remain derived from the partial raw basis until
        > J-11 deliberately clears and regenerates them.
+       **(Status update, owner 2026-08-24: those 567 rows WERE completed in iteration 9 — J-10 is closed
+       at 585 restored. Nothing here is outstanding work. The conclusion nevertheless still binds: those
+       two `ScannerRun`s were created over the partial basis and are STILL stale, so J-11 Stage C/D must
+       clear and regenerate them. Read this paragraph as the reason they are stale, never as a claim that
+       raw-price rows remain to be fetched.)**
        They are therefore **not** final reconstructed snapshots, and J-10 must not describe them as
        such. **Status of those rows, recorded explicitly:**
        > Any `ScannerRun` for 2026-08-11 or 2026-08-12 created before J-10's final raw-input recovery
@@ -940,11 +945,15 @@ manifest artifact (it must be self-describing and self-caveating).
     snapshot row format inside the incident set.
   - **Prerequisite — J-10 first, hard gate.** J-11 does NOT replace or bypass J-10. J-10 still owns
     restoration of the canonical `daily_prices` rows for 2026-08-11 and 2026-08-12 across the proven
-    587-symbol population (**currently 20 restored / 567 pending**). J-11 may not begin until **the
-    authorized J-10 raw-input recovery has reached its accepted terminal state and the canonical
-    daily-price coverage needed by every incident date has been verified.** Never run the derived
-    rebuild against a knowingly incomplete price layer, and never lower J-10's acceptance criteria to
-    unblock this journey.
+    587-symbol population. **J-10 prerequisite SATISFIED (owner, 2026-08-24): the raw layer is terminal
+    at 585 restored, with EA and EQR explicitly accepted as unrestorable, and AG-9's recovery-fetch
+    authorization is exhausted** — see the "J-10 CLOSED — residual set accepted" bullet in J-10. The
+    superseded status line this bullet used to carry ("currently 20 restored / 567 pending") described
+    the state at iteration 6 and is **stale**; it is corrected here rather than deleted so the lineage
+    stays legible. **J-10 is closed and MUST NOT be reopened** — not by the decomposer, not to retry EA
+    or EQR, not to "finish the remaining 567", which no longer exist. The original gate still binds for
+    its own sake: never run the derived rebuild against a knowingly incomplete price layer, and never
+    lower J-10's acceptance criteria to unblock this journey.
   - **The incident date set — all 11, not the 8 currently absent.** From the authoritative removal
     audit (`data_provider_runs` id=538, whose own cascade record lists them):
     `2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27, 2026-08-03, 2026-08-05,
@@ -1215,6 +1224,33 @@ manifest artifact (it must be self-describing and self-caveating).
          is intact (AG-1). Cover each degenerate input with its own test, and re-verify read-only against
          the 8 live manifests that carry `generation_json` NULL. Treat the *count* as evidence to
          re-derive, not to trust: verify it yourself read-only rather than quoting this line.
+         **A4-bis — the recorded-timestamp cases must also fail closed (owner, 2026-08-24).** The iter-11
+         fix closed the missing/empty/malformed/non-object/key-absent branches but left the *value* of
+         `source_run_created_at` unchecked: `recorded = generation.get(...)` followed by
+         `if recorded is not None and recorded != current: return rebuilt` / `return available` means a
+         key present with value `null` falls through to **`available`** — still fail-open — and an empty
+         or unparseable string is reported as **`rebuilt`**, which asserts a rebuild that was never
+         established. A key whose value is `null` does not provide a verifiable source timestamp. Required
+         behaviour, complete:
+         | recorded `source_run_created_at` | status |
+         |---|---|
+         | absent | `unverifiable` |
+         | `null` | `unverifiable` |
+         | empty / unusable | `unverifiable` |
+         | present but unparseable as the expected timestamp representation | `unverifiable` |
+         | valid timestamp ≠ current run's | `rebuilt` |
+         | valid timestamp = current run's | `available` |
+         | no current `ScannerRun` for the `as_of` | `unavailable` |
+         **Never report `available` unless an actual recorded timestamp exists and matches the current
+         run.** Do not compare arbitrary strings as though they were valid timestamps — validate the
+         recorded value into the same canonical UTC representation the writer and the current-run
+         comparison use; if it cannot be parsed, the answer is `unverifiable`, **not** `rebuilt` and
+         certainly not `available`. The semantic question is whether the original basis can be *proven*;
+         unreadable provenance means unverifiable. Keep this change narrow. Test at minimum: NULL, `""`,
+         malformed JSON, `[]`, `{}`, `{"source_run_created_at": null}`, `{"source_run_created_at": ""}`,
+         `{"source_run_created_at": "garbage"}`, valid-mismatched, valid-matched, and no-current-run. Then
+         re-run the read-only classification across all 24 live manifests without mutating them and report
+         the exact new distribution — the live count is evidence to re-derive, never a hardcoded expectation.
        - **A5 — Maintenance isolation stays ACTIVE.** No application-service boot, no browser-QA lane,
          and no deterministic-replay lane, unchanged, until Stage G. The migration iteration is the
          **single** authorized exception to "zero writes to `trendora.db`", and its writes are bounded to
@@ -1231,6 +1267,80 @@ manifest artifact (it must be self-describing and self-caveating).
          from a partially migrated or unproven table.
        This work is **Stage B1-completion**, a separate iteration (or iterations) before Stage C — it is
        not part of the Stage C destructive unit and does not start it.
+
+       **OWNER RULING — iter-11 DDL residual accepted (owner, 2026-08-24).** The iter-11 live migration
+       successfully removed the unwanted `source_run_id -> scanner_runs.id` foreign key and preserved all
+       24 manifest rows and every stored value, **but it also changed four DDL properties beyond the
+       original A1/AG-18 authorization.** The owner accepts **exactly** these four already-materialized
+       residual differences, and nothing else:
+       | # | property | before | after |
+       |---|---|---|---|
+       | 1 | `version` | `INTEGER NOT NULL DEFAULT 1` | `INTEGER NOT NULL` |
+       | 2 | `frozen` | `BOOLEAN NOT NULL DEFAULT 0` | `BOOLEAN NOT NULL` |
+       | 3 | `prospective_eligible` | `BOOLEAN NOT NULL DEFAULT 0` | `BOOLEAN NOT NULL` |
+       | 4 | `version` column ordinal | 9 | 3 |
+       **A second live rewrite is NOT authorized** merely to restore those historical DDL details. The
+       reason for accepting rather than rewriting is risk minimization, all independently verified: all 24
+       rows survived; all 24 × 28 stored cells were proven identical; every `source_run_id` value is
+       unchanged; the unwanted live FK is gone; FK enforcement can be enabled with zero manifest/run
+       violations; the three removed defaults are not required by the current canonical SQLModel writer;
+       the ordinal change carries no intended semantic meaning; and a second destructive table rewrite
+       would add live operational risk for low-value restoration of historical DDL shape.
+       - **A8 — What this acceptance is NOT.** It is a narrow, enumerated, post-incident acceptance of
+         four known residual differences. It is **NOT** a general waiver of AG-18; **NOT** permission for
+         further schema drift; **NOT** permission to mutate any manifest value; **NOT** permission to
+         perform another live rewrite; **NOT** permission to broaden Stage B1; and **NOT** a claim that
+         the migration originally stayed within its authorization. **The iter-11 migration DID exceed the
+         original A1/AG-18 schema bound — record that fact honestly.** The four residual differences are
+         **not desirable**; they are merely accepted as the current bounded end state. The accepted
+         residual set **must not become a precedent**.
+       - **A9 — B1 live end state (the operative contract).**
+         > manifest values unchanged · `source_run_id` FK absent · original indexes preserved ·
+         > known four-item DDL residual accepted · no second corrective live rewrite required
+       - **A10 — Migration implementation must derive from captured live DDL (future safety only).** Root
+         cause of the residual: `j11_schema_migration.py` captured the original live DDL but then built
+         the replacement table from `NextSessionManifest.__table__.to_metadata(...)`, reconstructing MODEL
+         shape rather than LIVE historical shape. A future migration must produce **the original live
+         `CREATE TABLE`, MINUS ONLY the `FOREIGN KEY(source_run_id) REFERENCES scanner_runs(id)` clause**:
+         take the captured original DDL as the authoritative physical schema source, transform only that
+         one FK clause, create the shadow table from the transformed DDL, copy rows by explicit column
+         name, and reissue the original indexes verbatim. Never generate the table body from SQLModel
+         metadata; never hand-author the replacement schema independently. Column names, order, types,
+         nullability, server defaults, primary key, unrelated constraints and indexes must all be
+         untouched. **The transformation fails closed** if the expected FK clause cannot be identified
+         exactly — no broad regex that could silently remove an unrelated constraint. This fix is for
+         correctness, testability and future retry safety; **it must NOT be run against the live database.**
+       - **A11 — Deferred to Stage G, not blockers, not to be mutated.** (a) The `preFreezeEra` branch in
+         the manifest strip currently masks the new `unverifiable` badge on live rows. If that branch
+         remains honest and fail-closed it is a **Stage G product-verification item**, not a Stage C
+         blocker, and no UI/browser work may be pulled forward into a cleanup iteration; if it is actually
+         misleading or fail-open, surface the exact contradiction and STOP rather than broadening
+         silently. (b) Manifest export-file discrepancies (recorded `export_path` values with no file on
+         disk; files on disk for dates with no manifest row) predate this work: do **not** repair or
+         delete files, mint manifests, or change `export_path`. Record it as an immutable-evidence
+         reconciliation item for Stage G; only if inspection shows it makes Stage C unsafe should it be
+         surfaced as a blocker.
+       - **A12 — Stage C READY gate.** Stage C may be marked READY only when ALL of these hold, and the
+         iteration must return the explicit owner-facing line `J-11 STAGE C READY: YES / NO`:
+         J-10 closed with no stale `20/567` operative wording remaining; the exact four-item DDL residual
+         accepted and documented; the live manifest FK still absent; 24 manifest rows still unchanged; the
+         migration utility fixed for future exact-DDL-minus-FK behaviour; `basis_disclosure` null/malformed
+         timestamp cases failing closed; the `models.py` comment no longer falsely claiming an exact
+         physical match; maintenance isolation still active; all targeted tests passing; **zero live-database
+         writes** in the cleanup iteration; and no new blocker discovered. **Stage C is still NOT executed
+         in that iteration** — it waits for an explicit owner instruction to resume.
+       - **A13 — Live database is READ-ONLY for the B1 cleanup iteration.** Expected live writes: **ZERO**.
+         No further `DROP TABLE`, table swap, corrective `ALTER`, ordinal reconstruction, manifest-row copy,
+         or any schema mutation to `next_session_manifests`. Verify before and after — `daily_prices`,
+         `scanner_runs`, manifest row count, manifest values, manifest live DDL, indexes, `forward_returns`,
+         provider runs, and any user state already tracked in the Stage B inventory — using the strongest
+         practical read-only fingerprinting the J-11 evidence framework already provides. **Do not claim
+         "no write" from row counts alone.**
+       - **A14 — iter-11's REGRESSION verdict stands.** Do not rewrite or delete it. This acceptance
+         resolves only whether the already-materialized residual must be undone; it does **not**
+         retroactively turn iter-11 into a clean PASS. The honest lineage to preserve is: *iter-11
+         migration — primary goal succeeded, stored state preserved, unauthorized DDL residual detected,
+         REGRESSION recorded, owner later accepted the exact residual instead of ordering a second rewrite.*
     12. **Stage B2 — freeze ONE engine identity for the whole attempt (owner, 2026-08-21).** J-11's
        claim is that the incident set ends up as one internally consistent current-engine derivation;
        that claim must be testable. Before Stage C, freeze the intended current engine identity and
@@ -1272,8 +1382,11 @@ manifest artifact (it must be self-describing and self-caveating).
        destructive scope (11 dates, allowlisted tables), complete-attempt restart semantics (above),
        pre/post inventories, and fail-closed verification. Do not specify or imply "transaction
        rollback" unless and until the implementation actually supports it.
-  - Sequencing (explicit): **A** finish J-10's canonical input repair (567 remaining under the fixed
-    per-symbol gate → verify 2026-08-11/12 coverage → close the temporary fetch authorization) →
+  - Sequencing (explicit; **operative form as of 2026-08-24** — the pre-iteration-9 form began "finish
+    J-10's canonical input repair (567 remaining)", which is now stale and satisfied): **A** J-10 terminal
+    prerequisite **already satisfied** (585 restored; EA/EQR accepted unrestorable; AG-9 exhausted; the
+    temporary fetch authorization is closed) → **B/B1/B2 completed in iterations 10-11, to be re-verified
+    rather than redone** →
     **B** freeze a read-only pre-reset inventory (the exact 11-date target set; row counts by relevant
     table and date; `daily_prices` coverage/fingerprint; manifest count and hashes; manifest export
     fingerprints where practical; `data_provider_runs` audit state; the certified-ledger file hash;
@@ -1490,7 +1603,17 @@ manifest artifact (it must be self-describing and self-caveating).
   stored column value — `as_of`, `source_run_id` (orphans included), `generation_json`, `content_hash`,
   `manifest_hash`, `version`, `available_at_utc`, `prospective_eligible` — survive exactly, proven by
   persisted pre/post per-row evidence. No other table's schema may be altered under that authorization.
-  A changed stored value is a REGRESSION, never a note. *(critical)*
+  A changed stored value is a REGRESSION, never a note.
+  **Bounded exception on record (owner, 2026-08-24) — narrowing nothing.** The iter-11 migration **did
+  exceed** this rule: it removed three server-side defaults (`version`, `frozen`, `prospective_eligible`)
+  and moved `version` from column ordinal 9 to 3. That event was **detected** (by the auditor, after the
+  developer, reviewer and QA all missed it), **enumerated** exactly, **reviewed**, and **accepted by the
+  owner after the fact** as an already-materialized end state — explicitly in preference to a second
+  live rewrite, on risk grounds. It is **not generalized**. AG-18 continues to prohibit schema drift
+  beyond an explicitly authorized migration; future migrations remain subject to strict schema-delta
+  proof, must derive the replacement table body from the captured live DDL rather than from ORM metadata
+  (ruling A10), and must fail closed when the targeted clause cannot be identified exactly. **The
+  accepted residual set is not a precedent and may not be cited as one.** *(critical)*
 
 ## Loop mechanics (for the iteration planner)
 
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-market-compass/session.json      |   2 +-
 .../state/assumptions.md                           | 171 +++------------------
 .../state/assumptions.md.archive.md                | 150 ++++++++++++++++++
 .../goal-session-market-compass/state/blueprint.md |  15 ++
 runs/goal-session-market-compass/state/lessons.md  |  28 +---
 .../state/lessons.md.archive.md                    |  37 +++++
 runs/goal-session-market-compass/telemetry.jsonl   |  15 ++
 runs/goal-session-market-compass/trace/.next-step  |   2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |   3 +
 9 files changed, 248 insertions(+), 175 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
