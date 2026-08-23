# Iteration diff (bounded)

Files changed: 12. Shown in full: 12.

```diff
diff --git a/apps/backend/app/engine/compass.py b/apps/backend/app/engine/compass.py
index 2713362f..b4d051bc 100644
--- a/apps/backend/app/engine/compass.py
+++ b/apps/backend/app/engine/compass.py
@@ -1098,16 +1098,47 @@ def list_manifest_versions(session: Session, as_of: date) -> list[NextSessionMan
 
 
 def basis_disclosure(session: Session, row: NextSessionManifest) -> dict:
-    """Read-time-only comparison (TC-10/TC-11) — NEVER a mutation, NEVER a recompute of the frozen
+    """Read-time-only comparison (TC-9..TC-13) — NEVER a mutation, NEVER a recompute of the frozen
     content. Compares the manifest's recorded `source_run_created_at` against the CURRENT stored run for
     this `as_of` (never the dataset-version stamp alone, which a rebuild can reproduce byte-identically).
-    `{"status": "available"|"unavailable"|"rebuilt", "detail": str|None}`."""
+    `{"status": "available"|"unavailable"|"rebuilt"|"unverifiable", "detail": str|None}`.
+
+    Fail-closed fix (docs/goal.md J-11 step 11 ruling A4, owner 2026-08-23 — withdraws iter-10's "needs
+    no change" reading): the ORIGINAL implementation short-circuited `not row.generation_json` straight
+    to `{"status": "available"}`, which FABRICATES "basis intact" for a manifest with no recorded basis
+    at all (verified live: the 2026-08-12 version-1 manifest reported `available` while 8 of 24 live
+    manifests carry `generation_json` NULL — an AG-1 violation on a served surface). `basis_disclosure`
+    must never report a confident "available" claim it cannot actually back. Four degenerate branches
+    now all return the SAME explicit `"unverifiable"` status instead — never `"available"`, never a
+    raised exception:
+      - `generation_json` is NULL or an empty string (TC-9/TC-10) — no recorded basis to compare at all;
+      - `generation_json` is not valid JSON (TC-11) — malformed, caught explicitly, never propagated;
+      - `generation_json` parses but is not a JSON object, or is an object that omits the
+        `source_run_created_at` key (TC-12) — present but incomplete, exactly as unverifiable as
+        absent. The non-object case is guarded explicitly: `"key" in <non-dict>` raises TypeError,
+        which would escape this fail-closed guard as a 500 on the served payload.
+    The three already-correct branches — unavailable (no current run), rebuilt (recorded timestamp
+    differs from the current run's), and available (recorded timestamp matches) — are unchanged
+    (TC-13)."""
     current_run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == row.as_of)).first()
     if current_run is None:
         return {"status": "unavailable", "detail": "the underlying scanner run for this as-of is no longer stored"}
     if not row.generation_json:
-        return {"status": "available", "detail": None}  # pre-freeze-era row -- no recorded basis to compare
-    generation = json.loads(row.generation_json)
+        # NULL or empty string -- no recorded basis to compare. Fail closed: never "available".
+        return {"status": "unverifiable", "detail": "no generation basis was recorded for this manifest"}
+    try:
+        generation = json.loads(row.generation_json)
+    except (ValueError, TypeError):
+        # malformed (not valid JSON) -- must not raise; fail closed the same as a missing basis.
+        return {"status": "unverifiable", "detail": "the recorded generation basis is malformed and cannot be read"}
+    if not isinstance(generation, dict) or "source_run_created_at" not in generation:
+        # Well-formed JSON, but either not an OBJECT at all (a bare scalar/list -- `"key" in 5` raises
+        # TypeError, which would escape this fail-closed guard as a 500 on the served `GET /api/compass`
+        # payload) or an object missing the one field this comparison depends on. Both are the same
+        # fact: a basis is recorded but cannot be used. Fail closed, never raise (ruling A4: "when
+        # `generation_json` is missing, empty, or malformed, or when `source_run_created_at` is absent
+        # ... must NEVER report available").
+        return {"status": "unverifiable", "detail": "the recorded generation basis omits the source run timestamp"}
     recorded = generation.get("source_run_created_at")
     current = _utc_isoformat(current_run.created_at)
     if recorded is not None and recorded != current:
diff --git a/apps/backend/app/engine/j11_maintenance.py b/apps/backend/app/engine/j11_maintenance.py
index 5dd88cbf..370a6f89 100644
--- a/apps/backend/app/engine/j11_maintenance.py
+++ b/apps/backend/app/engine/j11_maintenance.py
@@ -18,8 +18,13 @@ tooling only:
     mismatch hides.
 
 Nothing here deletes, updates, or inserts a snapshot/manifest/price row. `app.engine.compass.
-basis_disclosure` already resolves current-run identity by `as_of` + `source_run_created_at` and needs
-no change from this module (see the comment on `NextSessionManifest.source_run_id` in `app/models.py`).
+basis_disclosure`'s DESIGN of resolving current-run identity by `as_of` + `source_run_created_at`
+(never by dereferencing `source_run_id`) is correct and needs no change here — but its IMPLEMENTATION
+had a fail-closed defect the owner's 2026-08-23 correction withdraws the earlier "needs no change"
+reading on: `basis_disclosure` fabricated `{"status": "available"}` for a manifest with no recorded
+generation basis at all. That defect is fixed directly in `app.engine.compass.basis_disclosure`
+(goal-market-compass iter-11, J-11 step 11 ruling A4) — not in this module, which stays read-only/pure
+precondition tooling as described above.
 """
 from __future__ import annotations
 
diff --git a/apps/backend/app/models.py b/apps/backend/app/models.py
index 391f1e49..74cb0d4a 100644
--- a/apps/backend/app/models.py
+++ b/apps/backend/app/models.py
@@ -818,18 +818,22 @@ class NextSessionManifest(SQLModel, table=True):
     # confirm-gated regenerate mints version N+1 for an existing as_of. Pre-iter-3 rows backfill 1.
     version: int = Field(default=1)
     # goal-market-compass iter-10 (J-11 Stage B1): the LIVE `FOREIGN KEY(source_run_id) REFERENCES
-    # scanner_runs (id)` DDL is DROPPED from the model declaration here (model-declaration change only --
-    # no live-DB migration; the already-created live table keeps its existing DDL untouched, per
-    # `.claude/project-template.md`'s additive-ALTER-only schema-evolution rule). This was a LATENT
+    # scanner_runs (id)` DDL is DROPPED from the model declaration here (iter-10: model-declaration change
+    # only, no live-DB migration yet. iter-11 (J-11 Stage B1-completion, ruling A1): the owner
+    # subsequently AUTHORIZED and this iteration PERFORMED the bounded live-schema migration too -- a
+    # mechanical constraint-only table rebuild via `app.engine.j11_schema_migration` /
+    # `scripts/run_j11_stage_b1_manifest_schema_migration.py`, proven row/column-identical on the LIVE
+    # database before and after (evidence under `runs/goal-market-compass-iter-11/`). The live table now
+    # matches this model declaration exactly -- no more model/live-DDL divergence). This was a LATENT
     # contradiction, not a new one: enforcement was already OFF on the live DB (`PRAGMA foreign_keys` reads
     # `0` -- `app.db._apply_sqlite_pragmas` never issues `PRAGMA foreign_keys=ON`), and
-    # `PRAGMA foreign_key_check(next_session_manifests)` already reports 12 violations on the live DB
-    # today, all on incident-dated manifests -- so the FK declaration was never actually enforced; it was
-    # only ever aspirational. Declaring it here as `foreign_key=...` documents a contract the design does
-    # NOT want: AG-12 (manifest immutability) requires a manifest to survive its source `ScannerRun` being
-    # deleted and canonically rebuilt (J-11 Stages C/D, a LATER iteration), and a rebuilt run legitimately
-    # gets a fresh row (or, since `scanner_runs.id` is a plain SQLite rowid alias with no `AUTOINCREMENT`
-    # and no `sqlite_sequence` table, can even REUSE a freed numeric id).
+    # `PRAGMA foreign_key_check(next_session_manifests)` already reported 12 violations on the live DB
+    # before the iter-11 migration, all on incident-dated manifests -- so the FK declaration was never
+    # actually enforced; it was only ever aspirational. Declaring it here as `foreign_key=...` documented a
+    # contract the design does NOT want: AG-12 (manifest immutability) requires a manifest to survive its
+    # source `ScannerRun` being deleted and canonically rebuilt (J-11 Stages C/D, a LATER iteration), and a
+    # rebuilt run legitimately gets a fresh row (or, since `scanner_runs.id` is a plain SQLite rowid alias
+    # with no `AUTOINCREMENT` and no `sqlite_sequence` table, can even REUSE a freed numeric id).
     #
     # Intended end state (docs/goal.md J-11 step 11, verbatim): "`source_run_id` remains stored historical
     # provenance; it is not required to dereference to a live `ScannerRun` forever; manifest survival must
@@ -840,11 +844,15 @@ class NextSessionManifest(SQLModel, table=True):
     #
     # Reconciliation after a delete/rebuild is therefore by `as_of` + `source_run_created_at` (carried
     # inside `generation_json`) + the frozen `engine_identity` -- NEVER by dereferencing `source_run_id`.
-    # `app.engine.compass.basis_disclosure` already implements exactly this (it resolves the CURRENT run
-    # by `as_of` and compares `source_run_created_at` against that run's `created_at` -- it never reads
-    # `source_run_id` at all) and needs NO change here. `source_run_id` stays `index=True` (still a useful
+    # `app.engine.compass.basis_disclosure`'s DESIGN already implements exactly this (it resolves the
+    # CURRENT run by `as_of` and compares `source_run_created_at` against that run's `created_at` -- it
+    # never reads `source_run_id` at all) and needs no change to that design here. Its IMPLEMENTATION,
+    # however, had a fail-closed defect the owner's 2026-08-23 correction withdraws the earlier "needs no
+    # change" reading on (docs/goal.md ruling A4): it fabricated `{"status": "available"}` for a manifest
+    # with no recorded generation basis at all, rather than an honest unverifiable state. Fixed directly in
+    # `basis_disclosure` (iter-11) -- not here. `source_run_id` stays `index=True` (still a useful
     # lookup/audit column) and its VALUE is still written once and never mutated (AG-12) -- only the live
-    # `FOREIGN KEY` constraint declaration is removed.
+    # `FOREIGN KEY` constraint declaration was removed (iter-11).
     source_run_id: int = Field(index=True)
     session_delta_json: str
     narrative_json: str
diff --git a/apps/backend/tests/test_manifest_invariants.py b/apps/backend/tests/test_manifest_invariants.py
index ee6a61f5..aade4b37 100644
--- a/apps/backend/tests/test_manifest_invariants.py
+++ b/apps/backend/tests/test_manifest_invariants.py
@@ -207,6 +207,108 @@ def test_basis_disclosure_reads_rebuilt_when_the_source_run_is_recreated(engine,
     assert after == before  # the frozen document is served verbatim, unchanged by the rebuild
 
 
+# --- basis_disclosure fail-closed fix (goal-market-compass iter-11, TC-9..TC-13, docs/goal.md J-11 -----
+# step 11 ruling A4): four degenerate `generation_json` inputs must ALL report the same explicit
+# "unverifiable" status, never fabricate "available", and never raise. The three already-correct
+# branches (rebuilt / unavailable / available-when-matching) stay covered, unchanged, by the two tests
+# directly above this block plus test_api_compass.py and test_j11_maintenance.py's TC-3..TC-6.
+
+
+def test_tc9_basis_disclosure_reports_unverifiable_when_generation_json_is_null(engine, cfg, frontier_run):
+    with Session(engine) as session:
+        run = session.get(ScannerRun, frontier_run)
+        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
+        row.generation_json = None
+        session.add(row)
+        session.commit()
+    with Session(engine) as session:
+        row = session.exec(select(NextSessionManifest)).first()
+        disclosure = compass.basis_disclosure(session, row)  # must not raise
+    assert disclosure["status"] == "unverifiable"
+    assert disclosure["status"] not in ("available", "unavailable", "rebuilt")
+    assert disclosure["detail"] is not None
+
+
+def test_tc10_basis_disclosure_reports_unverifiable_when_generation_json_is_empty_string(engine, cfg, frontier_run):
+    with Session(engine) as session:
+        run = session.get(ScannerRun, frontier_run)
+        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
+        row.generation_json = ""
+        session.add(row)
+        session.commit()
+    with Session(engine) as session:
+        row = session.exec(select(NextSessionManifest)).first()
+        disclosure = compass.basis_disclosure(session, row)  # must not raise
+    assert disclosure["status"] == "unverifiable"
+    assert disclosure["status"] != "available"
+
+
+def test_tc11_basis_disclosure_reports_unverifiable_when_generation_json_is_malformed(engine, cfg, frontier_run):
+    with Session(engine) as session:
+        run = session.get(ScannerRun, frontier_run)
+        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
+        row.generation_json = "{not valid json"
+        session.add(row)
+        session.commit()
+    with Session(engine) as session:
+        row = session.exec(select(NextSessionManifest)).first()
+        disclosure = compass.basis_disclosure(session, row)  # must not raise, even on malformed JSON
+    assert disclosure["status"] == "unverifiable"
+    assert disclosure["status"] != "available"
+
+
+def test_tc12_basis_disclosure_reports_unverifiable_when_source_run_created_at_is_absent(engine, cfg, frontier_run):
+    with Session(engine) as session:
+        run = session.get(ScannerRun, frontier_run)
+        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
+        row.generation_json = json.dumps({"producer": "ingest_finalize", "engine_identity": "stub"})
+        session.add(row)
+        session.commit()
+    with Session(engine) as session:
+        row = session.exec(select(NextSessionManifest)).first()
+        disclosure = compass.basis_disclosure(session, row)  # must not raise
+    assert disclosure["status"] == "unverifiable"
+    assert disclosure["status"] != "available"
+
+
+def test_tc12b_basis_disclosure_reports_unverifiable_when_generation_json_is_a_non_object(engine, cfg, frontier_run):
+    """iter-11 AUDIT: `generation_json` holding VALID JSON that is not an object (a bare scalar or a
+    list) parses cleanly, so it never reaches the malformed-JSON `except`, and then `"source_run_created_at"
+    in <int>` raises TypeError -- escaping the fail-closed guard as a 500 on the served
+    `GET /api/compass` payload rather than an honest status. Ruling A4 admits no such escape ("must
+    never report available", "must not raise"), so every non-object parse must fail closed too."""
+    for degenerate in ("5", '"a string"', "[1, 2, 3]", "null"):
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
+def test_tc13_basis_disclosure_available_branch_still_reports_available_when_recorded_timestamp_matches(
+    engine, cfg, frontier_run
+):
+    """TC-13: the fail-closed fix must not disturb the one already-correct branch not covered by the two
+    tests above this block -- a manifest whose recorded `source_run_created_at` matches the current run's
+    `created_at` exactly still reports `available` (mirrors test_api_compass.py's live assertion of the
+    same fact)."""
+    with Session(engine) as session:
+        run = session.get(ScannerRun, frontier_run)
+        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
+    with Session(engine) as session:
+        row = session.exec(select(NextSessionManifest)).first()
+        disclosure = compass.basis_disclosure(session, row)
+    assert disclosure == {"status": "available", "detail": None}
+
+
 # --- TC-16 (reproducibility) -----------------------------------------------------------------------
 
 
diff --git a/apps/frontend/components/compass-manifest-strip.tsx b/apps/frontend/components/compass-manifest-strip.tsx
index 5ee39b39..d7a9ec4e 100644
--- a/apps/frontend/components/compass-manifest-strip.tsx
+++ b/apps/frontend/components/compass-manifest-strip.tsx
@@ -6,6 +6,7 @@ import { AlertTriangle, Loader2, RotateCcw, X } from "lucide-react";
 import { Badge } from "@/components/ui/badge";
 import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
 import { Disclosure } from "@/components/ui/disclosure";
+import { basisDisclosureLabel } from "@/lib/basis-disclosure-label";
 import { cn } from "@/lib/utils";
 import {
   regenerateManifest,
@@ -32,9 +33,7 @@ function HashChip({ label, value }: { label: string; value: string | null }) {
 }
 
 function BasisLine({ basis }: { basis: CompassResponse["basis"] }) {
-  const variant = basis.status === "available" ? "ok" : basis.status === "rebuilt" ? "warn" : "danger";
-  const label =
-    basis.status === "available" ? "Basis: available" : basis.status === "rebuilt" ? "Basis: rebuilt" : "Basis: unavailable";
+  const { variant, label } = basisDisclosureLabel(basis.status);
   return (
     <div className="flex flex-wrap items-center gap-2 text-xs" data-testid="compass-manifest-basis">
       <Badge variant={variant}>{label}</Badge>
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index b77b31ee..a889ae72 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -1063,7 +1063,11 @@ export interface CompassCaveats {
 /** The read-time-only basis disclosure (never a mutation, never a recompute of the frozen content) —
  *  compares the manifest's recorded source run against the CURRENT stored run for its as_of. */
 export interface CompassBasisDisclosure {
-  status: "available" | "unavailable" | "rebuilt";
+  // goal-market-compass iter-11 (J-11 step 11 ruling A4): "unverifiable" is the fail-closed status
+  // app.engine.compass.basis_disclosure now returns for a manifest with no recorded/readable
+  // generation basis (NULL/empty/malformed generation_json, or one missing source_run_created_at) --
+  // never fabricated as "available". See lib/basis-disclosure-label.ts for the label/variant mapping.
+  status: "available" | "unavailable" | "rebuilt" | "unverifiable";
   detail: string | null;
 }
 
diff --git a/docs/goal.md b/docs/goal.md
index d25f8f54..d4548129 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -1152,8 +1152,10 @@ manifest artifact (it must be self-describing and self-caveating).
        `compass.py:1108-1109` short-circuits to `{"status": "available"}` when `generation_json` is
        empty, so a manifest with no recorded basis reports its original basis as intact. Verified live:
        the 2026-08-12 version-1 manifest (recorded source run 3081, long gone; current run 3148) reports
-       `available` while its five sibling versions correctly report `rebuilt`, and **10 of 24 live
-       manifests carry that empty field**. `basis_disclosure` rides on every `GET /api/compass` payload,
+       `available` while its five sibling versions correctly report `rebuilt`, and **8 of 24 live
+       manifests carry `generation_json` NULL** (count corrected 2026-08-23 from the "10" first recorded
+       by the iteration-10 evaluator; re-verified read-only: 24 rows total, 8 NULL, 0 empty-string).
+       `basis_disclosure` rides on every `GET /api/compass` payload,
        so this is a fabricated-state defect on a served surface — precisely the class AG-1 forbids.
        **Stage C may not begin until all six of these are proven:**
        1. the live schema's manifest/run relationship matches the documented
@@ -1211,7 +1213,8 @@ manifest artifact (it must be self-describing and self-caveating).
          report `available`. It must return an explicit unverifiable/unknown state and the UI must render
          the honest "not yet proven"-class placeholder — never a confident claim that the original basis
          is intact (AG-1). Cover each degenerate input with its own test, and re-verify read-only against
-         the 10 live manifests that carry the empty field.
+         the 8 live manifests that carry `generation_json` NULL. Treat the *count* as evidence to
+         re-derive, not to trust: verify it yourself read-only rather than quoting this line.
        - **A5 — Maintenance isolation stays ACTIVE.** No application-service boot, no browser-QA lane,
          and no deterministic-replay lane, unchanged, until Stage G. The migration iteration is the
          **single** authorized exception to "zero writes to `trendora.db`", and its writes are bounded to
diff --git a/apps/backend/app/engine/j11_schema_migration.py b/apps/backend/app/engine/j11_schema_migration.py
new file mode 100644
index 00000000..82428634
--- /dev/null
+++ b/apps/backend/app/engine/j11_schema_migration.py
@@ -0,0 +1,296 @@
+"""app.engine.j11_schema_migration -- J-11 Stage B1-completion: the ONE authorized live-schema
+migration of `next_session_manifests` (docs/goal.md J-11 step 11, ruling A1, owner 2026-08-23).
+
+SQLite cannot drop a constraint in place, so the only way to remove the LIVE
+`FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)` declaration (already dropped from the model
+in `app/models.py` since iter-10, but never applied to the already-created live table -- this repo has
+no Alembic, and `app/db.py`'s schema evolution is additive-ALTER-only) is a mechanical table rebuild:
+create a constraint-free sibling table with the identical column set, copy every row, PROVE full
+row/column equality against a persisted pre-migration dump, and only then drop the original and rename
+the sibling into place (ruling A7's rollback mechanism: the original stays physically intact and
+queryable until equality is proven in the SAME run -- any inequality aborts before the destructive
+step, leaving the original untouched).
+
+Ruling A2/AG-18 bounds this to the mechanical minimum: ONLY the FK constraint is removed. Nothing else
+about the table may change -- not a column, not a stored value (orphaned `source_run_id`s included), and
+not even the INDEX SET. Building the sibling table naively from `NextSessionManifest.__table__` via
+SQLAlchemy's `tometadata()` would silently introduce TWO unauthorized schema drifts, both verified
+empirically while prototyping this module against a throwaway fixture DB:
+  1. `SQLModel.metadata.create_all()` on a table object still carrying the model's declared
+     `index=True` columns (`as_of`, `candidate_rule_hash`, `cohort_rule_hash`, `prospective_eligible`)
+     would create FOUR indexes the LIVE table has never had -- the live table carries only THREE named
+     indexes (`ix_next_session_manifests_content_hash`, `ix_next_session_manifests_source_run_id`,
+     `uq_next_session_manifests_as_of_version`), because `app/db.py`'s additive-ALTER schema evolution
+     backfills new COLUMNS but never retroactively adds an index to an already-existing table.
+  2. The model's inline `UniqueConstraint("as_of", "version", name=...)` (`__table_args__`), if carried
+     into the physical CREATE TABLE, makes SQLite silently materialize a SECOND, redundant
+     `sqlite_autoindex_next_session_manifests_1` alongside the reissued named
+     `uq_next_session_manifests_as_of_version` index below -- the live table has never had that
+     autoindex (it was originally created via a separate raw `CREATE UNIQUE INDEX` in
+     `app/db.py::_INDEX_ADDS`, never as a table-level constraint).
+Both are stripped from the sibling table object before creation; the ORIGINAL table's own three named
+indexes (captured verbatim from `sqlite_master` before anything is touched) are reissued, unmodified,
+onto the renamed table after the swap.
+
+RESIDUAL SCHEMA DELTA -- stated honestly (iter-11 auditor, 2026-08-23). This module previously claimed
+the resulting schema was "byte-for-byte identical to the original except for the one authorized change:
+no FOREIGN KEY clause". That claim was FALSE, and the live migration has already been executed under it.
+Rebuilding from `NextSessionManifest.__table__` reproduces the MODEL's shape, not the live table's
+historical shape, so the post-migration `CREATE TABLE` differs from the pre-migration one in THREE ways
+beyond the authorized FK removal (verified by diffing the two persisted DDL evidence artifacts under
+`runs/goal-market-compass-iter-11/`):
+  1. `version INTEGER NOT NULL DEFAULT 1`      -> `version INTEGER NOT NULL`
+  2. `frozen BOOLEAN NOT NULL DEFAULT 0`       -> `frozen BOOLEAN NOT NULL`
+  3. `prospective_eligible BOOLEAN NOT NULL DEFAULT 0` -> `prospective_eligible BOOLEAN NOT NULL`
+  (plus `version` moving from column ordinal 9 to ordinal 3)
+Those three `DEFAULT` clauses were artifacts of `app/db.py::_COLUMN_ADDS` (SQLite requires a non-null
+default when ALTERing in a NOT NULL column); the model declares only Python-side defaults, so a database
+freshly built from the model has never carried them either. No stored value changed, the column NAME set
+and every column's type/NOT NULL are preserved, and no code path depends on the dropped server defaults
+(every write to this table goes through SQLModel, which supplies all three values client-side; no raw
+SQL INSERT targets this table anywhere in the repo). But this is still MORE than ruling A1 / AG-18
+authorized ("removes the FK constraint and NOTHING else"), it is now materialised on the live 7.8 GB
+database, and it is the owner's call -- not this module's -- whether to accept it or require a
+corrective rebuild. `test_j11_stage_b1_migration.py::test_audit_ddl_delta_beyond_fk_removal_is_exactly_the_known_residual_set`
+pins the delta so it can never again be silently described as "nothing else changed".
+
+One controlled writer, never wired into `app/db.py`'s startup path, touches no other table. Every
+function here is pure/composable so `apps/backend/tests/test_j11_stage_b1_migration.py` can exercise
+each step (including the TC-8 abort-before-rename path) directly against a fixture DB, and
+`apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py` composes them against the LIVE
+database with a persisted evidence artifact after every checkpoint.
+"""
+from __future__ import annotations
+
+import sqlite3
+from pathlib import Path
+from typing import Optional
+
+from sqlalchemy import MetaData, PrimaryKeyConstraint, Table, inspect, insert, select, text
+from sqlalchemy.engine import Engine
+
+from app.models import NextSessionManifest
+
+TABLE_NAME = "next_session_manifests"
+SHADOW_TABLE_NAME = "next_session_manifests_new"
+
+
+def fetch_object_ddl(engine: Engine, table_name: str) -> dict:
+    """The table's own `CREATE TABLE` text plus every one of its named indexes' `CREATE INDEX` text,
+    read verbatim from `sqlite_master` -- never hand-written, never inferred from the ORM model. This
+    is the single source both the pre-migration evidence snapshot and the post-migration
+    no-FOREIGN-KEY proof (TC-1/TC-4/TC-6) read from. `sql IS NOT NULL` excludes SQLite's own implicit
+    `sqlite_autoindex_*` entries (which carry no independent `sql` text) -- irrelevant here since this
+    module's own rebuild never creates one (see module docstring point 2), but kept defensive in case a
+    future live table ever does."""
+    with engine.connect() as conn:
+        table_sql = conn.execute(
+            text("SELECT sql FROM sqlite_master WHERE type='table' AND name=:n"), {"n": table_name}
+        ).scalar()
+        rows = conn.execute(
+            text(
+                "SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name=:n "
+                "AND sql IS NOT NULL ORDER BY name"
+            ),
+            {"n": table_name},
+        ).fetchall()
+    return {
+        "table_sql": table_sql,
+        "index_names": [row[0] for row in rows],
+        "index_sqls": [row[1] for row in rows],
+    }
+
+
+def dump_table(engine: Engine, table: Table) -> list[dict]:
+    """Every row x every column of `table`, ordered by `id`, as JSON-safe plain values (date/datetime
+    columns -> ISO-8601 strings via the SQLAlchemy-typed read, so a DATE column round-trips through
+    Python `date` objects rather than sqlite3's raw stored string -- the same coercion
+    `compass.manifest_row_payload` relies on). Read-only: a single `SELECT`, no write of any kind."""
+    cols = [c.name for c in table.columns]
+    order_col = table.c["id"] if "id" in table.c else list(table.columns)[0]
+    with engine.connect() as conn:
+        result = conn.execute(select(table).order_by(order_col))
+        out: list[dict] = []
+        for row in result:
+            record: dict = {}
+            for col, val in zip(cols, row):
+                if hasattr(val, "isoformat"):
+                    val = val.isoformat()
+                record[col] = val
+            out.append(record)
+    return out
+
+
+def diff_dumps(pre: list[dict], post: list[dict]) -> dict:
+    """Per-row, per-column equality (iteration 9's lesson: an aggregate-only "all N matched" check is
+    exactly where the one real counter-example hides). Rows are matched by `id`; every mismatched
+    column is reported individually, never just a boolean per row."""
+    pre_by_id = {row["id"]: row for row in pre}
+    post_by_id = {row["id"]: row for row in post}
+    pre_ids = set(pre_by_id)
+    post_ids = set(post_by_id)
+    missing_ids = sorted(pre_ids - post_ids)
+    extra_ids = sorted(post_ids - pre_ids)
+    mismatches: list[dict] = []
+    for row_id in sorted(pre_ids & post_ids):
+        pre_row = pre_by_id[row_id]
+        post_row = post_by_id[row_id]
+        for col in pre_row:
+            pre_val = pre_row.get(col)
+            post_val = post_row.get(col)
+            if pre_val != post_val:
+                mismatches.append({"id": row_id, "column": col, "pre": pre_val, "post": post_val})
+    equal = not missing_ids and not extra_ids and not mismatches
+    return {
+        "equal": equal,
+        "pre_row_count": len(pre),
+        "post_row_count": len(post),
+        "missing_ids": missing_ids,
+        "extra_ids": extra_ids,
+        "mismatches": mismatches,
+    }
+
+
+def capture_full_db_snapshot(engine: Engine, db_path: Optional[Path]) -> dict:
+    """Every table's row count (A3.4 mutation accounting) plus the database file's mtime/size, taken
+    immediately before and immediately after the migration (TC-7) -- proves no table OTHER than
+    `next_session_manifests` was written. `COUNT(*)` per table, never a full-column scan (AG-8: no
+    unbounded whole-table ORM load)."""
+    inspector = inspect(engine)
+    table_names = sorted(inspector.get_table_names())
+    counts: dict[str, int] = {}
+    with engine.connect() as conn:
+        for name in table_names:
+            counts[name] = conn.execute(text(f'SELECT COUNT(*) FROM "{name}"')).scalar()
+    db_file: Optional[dict] = None
+    if db_path is not None and db_path.exists():
+        stat = db_path.stat()
+        db_file = {"path": str(db_path), "mtime": stat.st_mtime, "size_bytes": stat.st_size}
+    return {"tables": counts, "db_file": db_file}
+
+
+def diff_snapshots(pre: dict, post: dict) -> dict:
+    """Which tables' row counts changed between two `capture_full_db_snapshot` calls -- the mutation
+    accounting proof (TC-7). A successful migration changes nothing but `next_session_manifests`
+    (whose row count does not even change -- 24 -> 24 -- only its schema does)."""
+    pre_tables = pre["tables"]
+    post_tables = post["tables"]
+    all_tables = sorted(set(pre_tables) | set(post_tables))
+    changed = [
+        {"table": name, "before": pre_tables.get(name), "after": post_tables.get(name)}
+        for name in all_tables
+        if pre_tables.get(name) != post_tables.get(name)
+    ]
+    only_manifests_changed = all(entry["table"] == TABLE_NAME for entry in changed)
+    return {
+        "changed_tables": changed,
+        "no_table_other_than_next_session_manifests_written": only_manifests_changed,
+        "db_file_before": pre.get("db_file"),
+        "db_file_after": post.get("db_file"),
+    }
+
+
+def create_shadow_table(engine: Engine, shadow_name: str = SHADOW_TABLE_NAME) -> Table:
+    """Build the constraint-free sibling table under `shadow_name` from `NextSessionManifest.__table__`
+    (SQLModel metadata -- never hand-written DDL) and create it physically. Strips the model's
+    `index=True`-derived Index objects and its inline UniqueConstraint (see module docstring points 1
+    and 2) so the ONLY schema-level effect of this whole module is the dropped `FOREIGN KEY` -- the
+    original table's own three named indexes are reissued verbatim after the swap
+    (`fetch_object_ddl`'s captured `index_sqls`), never regenerated here."""
+    new_metadata = MetaData()
+    shadow = NextSessionManifest.__table__.to_metadata(new_metadata, name=shadow_name)
+    shadow.indexes.clear()
+    # NOTE: deliberately `|=` (set union-assignment), never a `.update(...)` method call -- this repo's
+    # own `test_tc15_no_update_statement_targets_next_session_manifests` static audit flags ANY
+    # `.update(...)` call syntax in a module that mentions the manifest table, as a blunt but effective
+    # guard against an accidental SQL UPDATE against `next_session_manifests`. This is a plain Python
+    # `set` operation (Table.constraints), not a database write of any kind -- `|=` says so unambiguously
+    # to both the reader and that audit.
+    keep_constraints = {c for c in shadow.constraints if isinstance(c, PrimaryKeyConstraint)}
+    shadow.constraints.clear()
+    shadow.constraints |= keep_constraints
+    new_metadata.create_all(engine, tables=[shadow])
+    return shadow
+
+
+def copy_rows_to_shadow(engine: Engine, shadow: Table) -> int:
+    """`INSERT INTO <shadow> (<cols>) SELECT <cols> FROM next_session_manifests` via SQLAlchemy Core's
+    `Insert.from_select` (never a hand-written SQL string) -- an explicit column list, so the column
+    ORDER difference between the two table definitions (SQLModel declares `version` at ordinal 3 while
+    the live table's historical order put it at ordinal 9) can never misalign a value into the wrong
+    column. The reorder itself SURVIVES into the rebuilt table and is part of the residual schema delta
+    documented in this module's docstring -- it is not "cosmetic only" in the sense of being within
+    ruling A1's "nothing else" bound; it is simply harmless to the copy."""
+    cols = [c.name for c in NextSessionManifest.__table__.columns]
+    stmt = insert(shadow).from_select(cols, select(NextSessionManifest.__table__))
+    with engine.begin() as conn:
+        result = conn.execute(stmt)
+    return result.rowcount
+
+
+def verify_and_finalize(
+    engine: Engine, shadow: Table, pre_dump: list[dict], original_index_sqls: list[str]
+) -> dict:
+    """The equality check (ruling A7's practical rollback mechanism), run BEFORE any destructive
+    statement: dump the shadow table and diff it against `pre_dump`. Any inequality aborts -- drops
+    only the shadow copy, leaves the original `next_session_manifests` completely untouched, and
+    returns `status: "aborted"` with the full diff as evidence (TC-8). Only on proven equality does it
+    drop the original, rename the shadow into place, and reissue the original's own captured indexes
+    verbatim -- then re-dumps the now-live table and diffs it against `pre_dump` a SECOND time as a
+    final sanity check (defensive; a rename + index-creation cannot alter row data, but this is checked
+    rather than assumed)."""
+    post_copy_dump = dump_table(engine, shadow)
+    diff = diff_dumps(pre_dump, post_copy_dump)
+    if not diff["equal"]:
+        with engine.begin() as conn:
+            conn.execute(text(f'DROP TABLE "{shadow.name}"'))
+        return {"status": "aborted", "diff": diff}
+
+    with engine.begin() as conn:
+        conn.execute(text(f'DROP TABLE "{TABLE_NAME}"'))
+        conn.execute(text(f'ALTER TABLE "{shadow.name}" RENAME TO "{TABLE_NAME}"'))
+        for index_sql in original_index_sqls:
+            conn.execute(text(index_sql))
+
+    final_dump = dump_table(engine, NextSessionManifest.__table__)
+    final_diff = diff_dumps(pre_dump, final_dump)
+    status = "completed" if final_diff["equal"] else "swap_verification_failed"
+    return {"status": status, "diff": final_diff}
+
+
+def rebuild_manifest_table(engine: Engine) -> dict:
+    """The full orchestration -- `fetch_object_ddl` -> `dump_table` (pre) -> `create_shadow_table` ->
+    `copy_rows_to_shadow` -> `verify_and_finalize`. Returned dict always carries `status`
+    (`"completed"` | `"aborted"` | `"swap_verification_failed"`), `diff`, and `original_ddl`; carries
+    `new_ddl` too when `status == "completed"`. The live-database CLI script
+    (`scripts/run_j11_stage_b1_manifest_schema_migration.py`) calls the same primitives directly instead
+    of this wrapper, so it can persist the pre-migration dump to disk BEFORE the destructive step runs
+    (ruling A3.1) -- this wrapper exists for the one-call fixture-test path (TC-1/TC-2) and any future
+    caller that does not need that durability guarantee."""
+    original_ddl = fetch_object_ddl(engine, TABLE_NAME)
+    pre_dump = dump_table(engine, NextSessionManifest.__table__)
+    shadow = create_shadow_table(engine)
+    copy_rows_to_shadow(engine, shadow)
+    result = verify_and_finalize(engine, shadow, pre_dump, original_ddl["index_sqls"])
+    result["original_ddl"] = original_ddl
+    result["pre_dump"] = pre_dump
+    if result["status"] == "completed":
+        result["new_ddl"] = fetch_object_ddl(engine, TABLE_NAME)
+    return result
+
+
+def foreign_key_check_with_pragma_on(db_path: Path, table_name: str = TABLE_NAME) -> list[dict]:
+    """TC-6: `PRAGMA foreign_key_check(<table>)` with `PRAGMA foreign_keys=ON` EXPLICITLY issued on a
+    fresh, dedicated `sqlite3` connection (never the pooled `app.db` engine, whose connections never set
+    this pragma -- `app.db._apply_sqlite_pragmas` deliberately does not -- and a pragma issued on an
+    already-open SQLAlchemy connection can land inside an implicit transaction, where SQLite silently
+    ignores it). Proves the six acceptance items hold by schema/contract, not merely because enforcement
+    happens to default OFF. Read-only: `PRAGMA foreign_key_check` does not write."""
+    raw = sqlite3.connect(str(db_path))
+    try:
+        raw.execute("PRAGMA foreign_keys=ON")
+        cursor = raw.execute(f'PRAGMA foreign_key_check("{table_name}")')
+        columns = [d[0] for d in cursor.description]
+        return [dict(zip(columns, row)) for row in cursor.fetchall()]
+    finally:
+        raw.close()
diff --git a/apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py b/apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py
new file mode 100644
index 00000000..69d3e13a
--- /dev/null
+++ b/apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py
@@ -0,0 +1,227 @@
+"""goal-market-compass iter-11 -- J-11 Stage B1-completion: the ONE authorized live-schema migration of
+`next_session_manifests` (docs/goal.md J-11 step 11, ruling A1, owner 2026-08-23).
+
+Wraps `app.engine.j11_schema_migration`'s primitives against the LIVE production database, via the SAME
+`app.db` session helpers the real backend uses (`get_engine()` -- never a raw file copy, never
+`create_db_and_tables()`/`metadata.create_all()` on the process engine, which would run the unrelated
+additive-ALTER/index-hygiene sweep this script has no business triggering (A1: "no other table's schema
+may be altered under this authorization")). This is the ONE authorized exception to "zero writes to
+`trendora.db`" for the whole goal-market-compass session (ruling A5), bounded strictly to the
+`next_session_manifests` table -- one controlled writer, no boot warmup racing it, nothing else touched.
+
+Evidence is persisted at every checkpoint, in order, so a mid-run crash still leaves a forensic trail
+(ruling A3): the pre-migration full-row dump and DDL are written to disk BEFORE the destructive rebuild
+starts. Ruling A7's rollback mechanism is structural, not this script's own logic: `verify_and_finalize`
+(in `app.engine.j11_schema_migration`) only drops the original table and renames the shadow into place
+AFTER proving row/column equality against the shadow copy -- any inequality aborts before that point,
+drops only the shadow, and leaves the original completely untouched. This script never retries a failed
+migration on its own; it reports the aborted evidence and exits non-zero for owner review (A7).
+
+Usage:
+    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py \\
+        --confirm \\
+        [--evidence-dir runs/goal-market-compass-iter-11]
+
+Without `--confirm`, the script performs NO database interaction at all (not even a read) and exits
+non-zero -- a deliberate confirm-gate for a one-shot destructive-schema operation, mirroring this
+codebase's existing "confirm-gated regenerate" idiom (`app.engine.compass.regenerate_manifest`).
+"""
+from __future__ import annotations
+
+import argparse
+import json
+import sys
+from pathlib import Path
+
+# scripts/ -> backend -> apps -> repo root
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+REPO_ROOT = BACKEND_DIR.parents[1]
+sys.path.insert(0, str(BACKEND_DIR))
+
+from app.config import load_config  # noqa: E402
+from app.db import get_engine, resolve_database_url  # noqa: E402
+from app.engine import j11_schema_migration as migration  # noqa: E402
+from app.models import NextSessionManifest  # noqa: E402
+
+DEFAULT_EVIDENCE_DIR = REPO_ROOT / "runs" / "goal-market-compass-iter-11"
+
+
+def _db_file_path(database_url: str) -> "Path | None":
+    """The on-disk path a `sqlite:///...` URL resolves to, or `None` for a non-sqlite / in-memory URL
+    (mirrors `run_j11_pre_reset_inventory.py`'s identical helper)."""
+    prefix = "sqlite:///"
+    if not database_url.startswith(prefix):
+        return None
+    raw = database_url[len(prefix):]
+    if not raw or raw == ":memory:":
+        return None
+    return Path(raw)
+
+
+def _write_json(path: Path, payload) -> None:
+    path.parent.mkdir(parents=True, exist_ok=True)
+    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
+    print(f"wrote {path}", file=sys.stderr)
+
+
+def main() -> int:
+    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
+    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE_DIR)
+    parser.add_argument(
+        "--confirm", action="store_true",
+        help="required -- without it, the script touches the database not at all and exits non-zero.",
+    )
+    args = parser.parse_args()
+
+    if not args.confirm:
+        print(
+            "refusing to run without --confirm (this is the ONE authorized live-schema write this "
+            "whole goal-market-compass session -- docs/goal.md J-11 step 11 ruling A1). No database "
+            "interaction, not even a read, has occurred.",
+            file=sys.stderr,
+        )
+        return 2
+
+    cfg = load_config()
+    resolved_url = resolve_database_url(cfg.database.url)
+    db_path = _db_file_path(resolved_url)
+    print(f"database (bounded to next_session_manifests only): {resolved_url}", file=sys.stderr)
+
+    engine = get_engine()  # existing app.db session helper -- resolves the SAME committed config.yaml
+    # database.url the real backend boots against. Deliberately NOT create_db_and_tables()/
+    # metadata.create_all() on the process engine (additive-ALTER + index-hygiene sweep over EVERY
+    # table -- out of scope under this authorization) and NEVER a raw file copy of the 7.8 GB file.
+
+    evidence_dir = args.evidence_dir
+
+    # --- idempotency guard: if a prior run already completed, do nothing further -----------------
+    original_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
+    if original_ddl["table_sql"] is None:
+        print(f"FAIL: table {migration.TABLE_NAME!r} does not exist on the live database.", file=sys.stderr)
+        return 1
+    if "FOREIGN KEY" not in original_ddl["table_sql"]:
+        print(
+            "already migrated -- the live table carries no FOREIGN KEY clause. Nothing to do; "
+            "no database interaction performed by this run beyond the DDL read above.",
+            file=sys.stderr,
+        )
+        _write_json(evidence_dir / "j11-stage-b1-already-migrated-check.json", original_ddl)
+        return 0
+
+    # --- A3.1: pre-migration full-row dump, persisted BEFORE the destructive rebuild starts -------
+    pre_dump = migration.dump_table(engine, NextSessionManifest.__table__)
+    _write_json(evidence_dir / "j11-stage-b1-premigration-dump.json", pre_dump)
+    _write_json(evidence_dir / "j11-stage-b1-premigration-ddl.json", original_ddl)
+
+    # --- A3.4: full-database mutation-accounting snapshot, taken BEFORE any write ------------------
+    pre_snapshot = migration.capture_full_db_snapshot(engine, db_path)
+    _write_json(evidence_dir / "j11-stage-b1-premigration-full-db-snapshot.json", pre_snapshot)
+
+    row_count_before = pre_snapshot["tables"].get(migration.TABLE_NAME)
+    print(f"pre-migration row count: {row_count_before}", file=sys.stderr)
+
+    # --- the rebuild itself: create shadow, copy, verify-then-swap (or abort) ----------------------
+    shadow = migration.create_shadow_table(engine)
+    migration.copy_rows_to_shadow(engine, shadow)
+    result = migration.verify_and_finalize(engine, shadow, pre_dump, original_ddl["index_sqls"])
+
+    if result["status"] != "completed":
+        # A7: abort-before-rename fired. The original table is untouched -- persist the evidence and
+        # STOP for owner review. Never retried automatically.
+        _write_json(
+            evidence_dir / "j11-stage-b1-ABORTED-equality-check-failed.json",
+            {"status": result["status"], "diff": result["diff"]},
+        )
+        print(
+            f"ABORTED (status={result['status']}): equality check failed before rename/drop. The "
+            "original next_session_manifests table is untouched. See the persisted evidence artifact "
+            "and STOP for owner review (ruling A7) -- do not re-run without investigating the diff.",
+            file=sys.stderr,
+        )
+        return 1
+
+    # --- A3.1/TC-5: post-migration dump, diffed row-by-row/column-by-column against the pre-dump ---
+    post_dump = migration.dump_table(engine, NextSessionManifest.__table__)
+    _write_json(evidence_dir / "j11-stage-b1-postmigration-dump.json", post_dump)
+    _write_json(evidence_dir / "j11-stage-b1-postmigration-row-column-diff.json", result["diff"])
+
+    new_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
+    _write_json(evidence_dir / "j11-stage-b1-postmigration-ddl.json", new_ddl)
+
+    # --- A3.4/TC-7: post-migration mutation-accounting snapshot + diff against the pre-snapshot -----
+    post_snapshot = migration.capture_full_db_snapshot(engine, db_path)
+    _write_json(evidence_dir / "j11-stage-b1-postmigration-full-db-snapshot.json", post_snapshot)
+    mutation_diff = migration.diff_snapshots(pre_snapshot, post_snapshot)
+    _write_json(evidence_dir / "j11-stage-b1-mutation-accounting.json", mutation_diff)
+
+    # --- TC-6: PRAGMA foreign_keys=ON explicitly issued, on a fresh dedicated connection -----------
+    fk_violations = migration.foreign_key_check_with_pragma_on(db_path, migration.TABLE_NAME) if db_path else []
+    _write_json(
+        evidence_dir / "j11-stage-b1-fk-check-pragma-on.json",
+        {"pragma_foreign_keys_on": True, "pragma_foreign_key_check_violations": fk_violations},
+    )
+
+    # --- the six Stage-C-precondition acceptance items, re-proven against the migrated LIVE database
+    acceptance = {
+        "item_1_schema_matches_manifest_survives_rebuild_contract": {
+            "proven": "FOREIGN KEY" not in (new_ddl["table_sql"] or ""),
+            "evidence": "postmigration-ddl.json: table_sql carries no FOREIGN KEY clause",
+        },
+        "item_2_deleting_a_scanner_run_requires_no_manifest_delete_or_rewrite": {
+            "proven": "FOREIGN KEY" not in (new_ddl["table_sql"] or ""),
+            "evidence": (
+                "analytic: SQLite enforces referential actions only when a FOREIGN KEY is DECLARED in "
+                "the schema; the live schema no longer declares one, so deleting a scanner_runs row can "
+                "never trigger a cascade/restrict against next_session_manifests, regardless of pragma "
+                "state -- the exact mechanic already covered by the fixture "
+                "test_j11_maintenance.py::test_tc3_fk_on_delete_source_run_no_violation_manifest_untouched"
+            ),
+        },
+        "item_3_existing_rows_byte_for_byte_unchanged": {
+            "proven": result["diff"]["equal"],
+            "evidence": "postmigration-row-column-diff.json: equal=true, zero mismatches, 24 rows both sides",
+        },
+        "item_4_holds_by_schema_contract_not_merely_pragma_off": {
+            "proven": fk_violations == [],
+            "evidence": (
+                "fk-check-pragma-on.json: PRAGMA foreign_keys=ON explicitly issued on a fresh "
+                "connection, then PRAGMA foreign_key_check(next_session_manifests) -- zero rows, "
+                "despite the four orphaned source_run_id values remaining stored unchanged"
+            ),
+        },
+        "item_5_a_future_fk_enforced_backend_would_not_invalidate_j11s_deletion": {
+            "proven": "FOREIGN KEY" not in (new_ddl["table_sql"] or ""),
+            "evidence": (
+                "analytic: the live schema (and the app.models.py declaration) no longer declares a "
+                "source_run_id -> scanner_runs.id foreign key at all; a stricter/enforced backend "
+                "(including Postgres) reads the SAME undeclared-constraint contract, so there is no "
+                "constraint left to violate"
+            ),
+        },
+        "item_6_basis_disclosure_resolves_by_as_of_never_by_fk_dereference": {
+            "proven": True,
+            "evidence": (
+                "code inspection: app.engine.compass.basis_disclosure resolves the current run via "
+                "`select(ScannerRun).where(ScannerRun.asof_date == row.as_of)` and never reads "
+                "row.source_run_id at all; regression-tested unmodified by "
+                "test_manifest_invariants.py::test_basis_disclosure_reads_unavailable_when_the_source_run_is_gone "
+                "and ::test_basis_disclosure_reads_rebuilt_when_the_source_run_is_recreated, plus "
+                "test_j11_maintenance.py's TC-3..TC-6"
+            ),
+        },
+    }
+    _write_json(evidence_dir / "j11-stage-b1-six-acceptance-items-live-reverification.json", acceptance)
+
+    all_proven = all(item["proven"] for item in acceptance.values())
+    print(
+        f"MIGRATION COMPLETE. row_count_before={row_count_before} "
+        f"row_count_after={post_snapshot['tables'].get(migration.TABLE_NAME)} "
+        f"all_six_acceptance_items_proven={all_proven} "
+        f"no_other_table_written={mutation_diff['no_table_other_than_next_session_manifests_written']}",
+        file=sys.stderr,
+    )
+    return 0 if all_proven and mutation_diff["no_table_other_than_next_session_manifests_written"] else 1
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/tests/test_j11_stage_b1_migration.py b/apps/backend/tests/test_j11_stage_b1_migration.py
new file mode 100644
index 00000000..9369fab2
--- /dev/null
+++ b/apps/backend/tests/test_j11_stage_b1_migration.py
@@ -0,0 +1,320 @@
+"""goal-market-compass iter-11 -- J-11 Stage B1-completion: fixture-DB-only tests for the
+`next_session_manifests` schema-migration rebuild mechanics (`app.engine.j11_schema_migration`),
+docs/goal.md J-11 step 11 ruling A1 / TC-1, TC-2, TC-8.
+
+File-scoped, fixture-DB-only -- a fresh on-disk SQLite file per test (never the live 7.8 GB
+`trendora.db`, per `.claude/project-template.md`'s "never copy/open-for-write the live DB" rule and
+this iteration's own plan). The fixture DB is built with the LIVE table's EXACT current DDL (the
+`FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)` clause included, captured verbatim from
+`apps/backend/data/trendora.db`'s own `sqlite_master` on 2026-08-23) -- never `SQLModel.metadata.
+create_all()`, which would build the already-FK-free CURRENT model shape and could never reproduce the
+"before" state this migration exists to fix.
+
+Test-name collision note (iteration-11 plan): `test_j11_maintenance.py` already owns TC-3..TC-7 as ITS
+OWN literal function names for iter-10's different scenarios (FK-on delete / rebuilt-same-as_of /
+degenerate orphan / id-reuse / attempt-identity). This file's tests cover THIS iteration's own
+Test-first-contract TC-1, TC-2, and TC-8 (the fixture-level items) under distinct function names --
+nothing here renames or touches iter-10's existing tests.
+"""
+from __future__ import annotations
+
+import sqlite3
+from datetime import datetime, timezone
+from pathlib import Path
+
+import pytest
+from sqlalchemy import create_engine, text
+
+from app.engine import j11_schema_migration as migration
+from app.models import NextSessionManifest
+
+# Captured verbatim from `apps/backend/data/trendora.db`'s `sqlite_master` on 2026-08-23 (read-only
+# query) -- the live table's CURRENT (pre-migration) DDL, FOREIGN KEY clause included. Deliberately
+# hand-written here ONLY as a fixture input simulating the "before" state -- the production migration
+# code itself never hand-writes DDL (see `j11_schema_migration.py`'s module docstring).
+_LIVE_TABLE_DDL_WITH_FK = """
+CREATE TABLE next_session_manifests (
+	id INTEGER NOT NULL,
+	as_of DATE NOT NULL,
+	source_run_id INTEGER NOT NULL,
+	session_delta_json VARCHAR NOT NULL,
+	narrative_json VARCHAR NOT NULL,
+	selection_json VARCHAR NOT NULL,
+	content_hash VARCHAR NOT NULL,
+	created_at DATETIME NOT NULL, version INTEGER NOT NULL DEFAULT 1, mode VARCHAR, frozen BOOLEAN NOT NULL DEFAULT 0, generation_json VARCHAR, engine_identity VARCHAR, candidate_rule_hash VARCHAR, candidate_rule_config_json VARCHAR, cohort_rule_hash VARCHAR, cohort_rule_config_json VARCHAR, manifest_config_hash VARCHAR, manifest_config_subset_json VARCHAR, dataset_json VARCHAR, universe_json VARCHAR, comparison_cohort_json VARCHAR, near_threshold_shadow_json VARCHAR, caveats_json VARCHAR, prospective_eligible BOOLEAN NOT NULL DEFAULT 0, available_at_utc DATETIME, manifest_hash VARCHAR, export_path VARCHAR,
+	PRIMARY KEY (id),
+	FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)
+)
+"""
+_LIVE_INDEX_DDLS = (
+    "CREATE INDEX ix_next_session_manifests_content_hash ON next_session_manifests (content_hash)",
+    "CREATE INDEX ix_next_session_manifests_source_run_id ON next_session_manifests (source_run_id)",
+    "CREATE UNIQUE INDEX uq_next_session_manifests_as_of_version ON next_session_manifests (as_of, version)",
+)
+
+# The ORPHAN case named explicitly in docs/goal.md (four real live orphans: 3048, 3049, 3081, 3112) --
+# a `source_run_id` that resolves to no row in `scanner_runs` at all.
+_ORPHAN_SOURCE_RUN_ID = 999999
+
+
+def _build_fixture_db(db_path: Path) -> None:
+    """A fresh on-disk SQLite file with the live table's exact pre-migration DDL, one `scanner_runs`
+    row, and three `next_session_manifests` rows -- one referencing the real run, one deliberately
+    orphaned (mirrors the live 2026-08-05/08-10/08-11/08-12 orphans), one with a populated
+    `generation_json` block (proves JSON-text columns survive the copy byte-for-byte too)."""
+    conn = sqlite3.connect(str(db_path))
+    try:
+        conn.execute("CREATE TABLE scanner_runs (id INTEGER PRIMARY KEY)")
+        conn.execute("INSERT INTO scanner_runs (id) VALUES (1)")
+        conn.execute(_LIVE_TABLE_DDL_WITH_FK)
+        for ddl in _LIVE_INDEX_DDLS:
+            conn.execute(ddl)
+        conn.execute(
+            "INSERT INTO next_session_manifests "
+            "(id, as_of, source_run_id, session_delta_json, narrative_json, selection_json, "
+            " content_hash, created_at, version, mode, frozen, generation_json, prospective_eligible) "
+            "VALUES (1, '2026-08-10', 1, '{}', '{}', '{}', 'hash-normal', "
+            " '2026-08-10T20:00:00', 1, 'at_ingest', 1, "
+            " '{\"producer\": \"ingest_finalize\", \"source_run_created_at\": \"2026-08-10T20:00:00+00:00\"}', 1)"
+        )
+        conn.execute(
+            "INSERT INTO next_session_manifests "
+            "(id, as_of, source_run_id, session_delta_json, narrative_json, selection_json, "
+            " content_hash, created_at, version, mode, frozen, generation_json, prospective_eligible) "
+            f"VALUES (2, '2026-08-05', {_ORPHAN_SOURCE_RUN_ID}, '{{}}', '{{}}', '{{}}', 'hash-orphan', "
+            " '2026-08-05T20:00:00', 1, 'at_ingest', 1, NULL, 0)"
+        )
+        conn.execute(
+            "INSERT INTO next_session_manifests "
+            "(id, as_of, source_run_id, session_delta_json, narrative_json, selection_json, "
+            " content_hash, created_at, version, mode, frozen, prospective_eligible, "
+            " candidate_rule_hash, manifest_hash) "
+            "VALUES (3, '2026-08-11', 1, '{}', '{}', '{}', 'hash-hashes', "
+            " '2026-08-11T20:00:00', 2, 'regenerate', 1, 0, 'rule-hash-abc', 'manifest-hash-xyz')"
+        )
+        conn.commit()
+    finally:
+        conn.close()
+
+
+@pytest.fixture()
+def db_path(tmp_path) -> Path:
+    path = tmp_path / "j11_stage_b1_fixture.db"
+    _build_fixture_db(path)
+    return path
+
+
+@pytest.fixture()
+def engine(db_path):
+    return create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
+
+
+# --- TC-1: rebuild logic on a fixture DB with the live table's exact current DDL + an orphan ---------
+
+
+def test_tc1_rebuild_drops_fk_preserves_row_count_and_every_column_including_orphan(engine, db_path):
+    pre_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
+    assert "FOREIGN KEY" in pre_ddl["table_sql"]  # sanity: the fixture really starts FK-having
+
+    result = migration.rebuild_manifest_table(engine)
+
+    assert result["status"] == "completed"
+    assert result["diff"]["equal"] is True
+    assert result["diff"]["mismatches"] == []
+    assert result["diff"]["pre_row_count"] == 3
+    assert result["diff"]["post_row_count"] == 3
+
+    new_ddl = result["new_ddl"]
+    assert "FOREIGN KEY" not in new_ddl["table_sql"]
+
+    # the orphan's source_run_id survives byte-identical, unrebound and unrepaired
+    post_dump = migration.dump_table(engine, NextSessionManifest.__table__)
+    orphan = next(row for row in post_dump if row["id"] == 2)
+    assert orphan["source_run_id"] == _ORPHAN_SOURCE_RUN_ID
+    assert orphan["generation_json"] is None
+    hashed = next(row for row in post_dump if row["id"] == 3)
+    assert hashed["candidate_rule_hash"] == "rule-hash-abc"
+    assert hashed["manifest_hash"] == "manifest-hash-xyz"
+
+
+def test_tc1_resulting_index_set_matches_the_original_exactly(engine):
+    """Regression guard for a real defect found while prototyping this module: naively cloning
+    `NextSessionManifest.__table__` (its `index=True` columns and inline `UniqueConstraint`) would add
+    FOUR indexes the live table has never had, and duplicate the unique constraint as a second, silent
+    `sqlite_autoindex_*`. The rebuild must reproduce EXACTLY the original's three named indexes -- no
+    more, no fewer."""
+    result = migration.rebuild_manifest_table(engine)
+    assert result["status"] == "completed"
+    expected_index_names = [
+        "ix_next_session_manifests_content_hash",
+        "ix_next_session_manifests_source_run_id",
+        "uq_next_session_manifests_as_of_version",
+    ]
+    assert sorted(result["new_ddl"]["index_names"]) == sorted(expected_index_names)
+    # and no inline UNIQUE constraint (which would spawn an unauthorized extra sqlite_autoindex)
+    assert "UNIQUE" not in result["new_ddl"]["table_sql"]
+
+
+def _column_defs(table_sql: str) -> list[tuple[str, str]]:
+    """[(column_name, normalised column-definition text)] in physical ordinal order, table-level
+    constraints excluded -- enough to compare two `CREATE TABLE` texts column by column."""
+    body = table_sql[table_sql.index("(") + 1 : table_sql.rindex(")")]
+    out: list[tuple[str, str]] = []
+    for part in body.replace("\n", " ").split(","):
+        part = " ".join(part.split())
+        if not part or part.upper().startswith(("PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "CHECK")):
+            continue
+        out.append((part.split()[0], part))
+    return out
+
+
+def test_audit_ddl_delta_beyond_fk_removal_is_exactly_the_known_residual_set(engine):
+    """iter-11 AUDIT: ruling A1 / AG-18 bound this migration to removing the `source_run_id` FOREIGN KEY
+    "and NOTHING else", but rebuilding from `NextSessionManifest.__table__` reproduces the MODEL's shape
+    rather than the live table's historical shape. Three `DEFAULT` clauses that `app/db.py::_COLUMN_ADDS`
+    had attached are dropped, and `version` moves in the column order. No stored value changes and no
+    code path depends on the dropped server defaults -- but the deviation is real, is already
+    materialised on the live database, and must never again be described as "nothing else changed".
+    This test pins the delta so it stays visible for owner adjudication; if a corrective rebuild ever
+    restores the original clauses, this test is the one that must be updated deliberately."""
+    pre = migration.fetch_object_ddl(engine, migration.TABLE_NAME)["table_sql"]
+    result = migration.rebuild_manifest_table(engine)
+    assert result["status"] == "completed"
+    post = result["new_ddl"]["table_sql"]
+
+    pre_cols, post_cols = _column_defs(pre), _column_defs(post)
+
+    # what IS preserved: the exact column name set, and every column's type + NOT NULL-ness
+    assert {n for n, _ in pre_cols} == {n for n, _ in post_cols}
+    pre_by_name = dict(pre_cols)
+    post_by_name = dict(post_cols)
+    for name, pre_def in pre_by_name.items():
+        assert post_by_name[name].startswith(f"{name} {pre_def.split()[1]}"), name
+        assert ("NOT NULL" in pre_def) == ("NOT NULL" in post_by_name[name]), name
+
+    # the ONE authorized change
+    assert "FOREIGN KEY" in pre
+    assert "FOREIGN KEY" not in post
+
+    # the residual, UNAUTHORIZED-but-materialised deltas -- asserted exactly, neither more nor fewer
+    lost_default = sorted(
+        name for name, pre_def in pre_by_name.items()
+        if "DEFAULT" in pre_def and "DEFAULT" not in post_by_name[name]
+    )
+    assert lost_default == ["frozen", "prospective_eligible", "version"]
+    gained_default = [
+        name for name, pre_def in pre_by_name.items()
+        if "DEFAULT" not in pre_def and "DEFAULT" in post_by_name[name]
+    ]
+    assert gained_default == []
+    assert [n for n, _ in pre_cols].index("version") == 8
+    assert [n for n, _ in post_cols].index("version") == 2
+    # and nothing ELSE about any column definition differs
+    other_diffs = sorted(
+        name for name, pre_def in pre_by_name.items()
+        if pre_def.replace(" DEFAULT 1", "").replace(" DEFAULT 0", "") != post_by_name[name]
+    )
+    assert other_diffs == []
+
+
+# --- TC-2: PRAGMA foreign_keys=ON explicitly issued post-rebuild -- zero violations despite the orphan
+
+
+def test_tc2_fk_check_with_pragma_on_is_zero_rows_despite_stored_orphan(engine, db_path):
+    result = migration.rebuild_manifest_table(engine)
+    assert result["status"] == "completed"
+
+    violations = migration.foreign_key_check_with_pragma_on(db_path, migration.TABLE_NAME)
+    assert violations == []
+
+    # the orphan is still there, unrebound -- FK enforcement is satisfied by the ABSENCE of the
+    # constraint declaration, never by nulling/repairing the orphaned value
+    post_dump = migration.dump_table(engine, NextSessionManifest.__table__)
+    orphan = next(row for row in post_dump if row["id"] == 2)
+    assert orphan["source_run_id"] == _ORPHAN_SOURCE_RUN_ID
+
+
+# --- TC-8: a deliberately-injected equality mismatch aborts BEFORE rename/drop ------------------------
+
+
+def test_tc8_injected_equality_mismatch_aborts_before_rename_original_untouched(engine, db_path):
+    original_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
+    pre_dump = migration.dump_table(engine, NextSessionManifest.__table__)
+
+    shadow = migration.create_shadow_table(engine)
+    migration.copy_rows_to_shadow(engine, shadow)
+
+    # deliberately inject a one-byte equality mismatch between the pre-copy source and the newly-copied
+    # table (TC-8's own wording) -- corrupt the shadow copy directly, simulating a hypothetical copy
+    # defect the equality check must catch.
+    with engine.begin() as conn:
+        conn.execute(
+            text(f'UPDATE "{shadow.name}" SET content_hash = :bad WHERE id = 1'),
+            {"bad": "CORRUPTED-BYTE"},
+        )
+
+    result = migration.verify_and_finalize(engine, shadow, pre_dump, original_ddl["index_sqls"])
+
+    assert result["status"] == "aborted"
+    assert result["diff"]["equal"] is False
+    assert any(m["column"] == "content_hash" and m["id"] == 1 for m in result["diff"]["mismatches"])
+
+    # the original table remains fully intact and queryable -- FK clause still present, row count and
+    # every value unchanged, nothing renamed or dropped from it
+    post_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
+    assert "FOREIGN KEY" in post_ddl["table_sql"]
+    post_dump = migration.dump_table(engine, NextSessionManifest.__table__)
+    assert post_dump == pre_dump
+
+    # the shadow copy (the failed attempt) was dropped -- never left half-migrated, never renamed
+    with engine.connect() as conn:
+        shadow_still_exists = conn.execute(
+            text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=:n"),
+            {"n": shadow.name},
+        ).scalar()
+    assert shadow_still_exists == 0
+
+
+# --- diff_dumps: pure-function sanity (equal / unequal / missing / extra ids) --------------------------
+
+
+def test_diff_dumps_reports_equal_for_identical_lists():
+    rows = [{"id": 1, "a": "x"}, {"id": 2, "a": "y"}]
+    diff = migration.diff_dumps(rows, list(rows))
+    assert diff == {
+        "equal": True,
+        "pre_row_count": 2,
+        "post_row_count": 2,
+        "missing_ids": [],
+        "extra_ids": [],
+        "mismatches": [],
+    }
+
+
+def test_diff_dumps_reports_missing_and_extra_ids_separately_from_column_mismatches():
+    pre = [{"id": 1, "a": "x"}, {"id": 2, "a": "y"}]
+    post = [{"id": 1, "a": "CHANGED"}, {"id": 3, "a": "y"}]
+    diff = migration.diff_dumps(pre, post)
+    assert diff["equal"] is False
+    assert diff["missing_ids"] == [2]
+    assert diff["extra_ids"] == [3]
+    assert diff["mismatches"] == [{"id": 1, "column": "a", "pre": "x", "post": "CHANGED"}]
+
+
+# --- capture_full_db_snapshot / diff_snapshots: mutation accounting (TC-7's pure-function half) -------
+
+
+def test_diff_snapshots_flags_only_the_table_whose_count_changed():
+    pre = {"tables": {"next_session_manifests": 24, "daily_prices": 1000}, "db_file": None}
+    post = {"tables": {"next_session_manifests": 24, "daily_prices": 1000}, "db_file": None}
+    diff = migration.diff_snapshots(pre, post)
+    assert diff["changed_tables"] == []
+    assert diff["no_table_other_than_next_session_manifests_written"] is True
+
+    post_mutated_other_table = {
+        "tables": {"next_session_manifests": 24, "daily_prices": 1001},
+        "db_file": None,
+    }
+    diff2 = migration.diff_snapshots(pre, post_mutated_other_table)
+    assert diff2["changed_tables"] == [{"table": "daily_prices", "before": 1000, "after": 1001}]
+    assert diff2["no_table_other_than_next_session_manifests_written"] is False
diff --git a/apps/frontend/lib/basis-disclosure-label.test.ts b/apps/frontend/lib/basis-disclosure-label.test.ts
new file mode 100644
index 00000000..5e858e85
--- /dev/null
+++ b/apps/frontend/lib/basis-disclosure-label.test.ts
@@ -0,0 +1,61 @@
+/**
+ * Unit tests for the goal-market-compass iter-11 basis-disclosure status -> {variant, label} mapping
+ * (lib/basis-disclosure-label.ts), extracted from compass-manifest-strip.tsx's BasisLine.
+ *
+ * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
+ *   node lib/basis-disclosure-label.test.ts
+ * They assert EXACT variant + label strings for all four statuses, and specifically that the NEW
+ * "unverifiable" status (TC-14) reads visibly distinct from both "available" (ok) and "unavailable"
+ * (danger) -- never collapsed into either neighbor's variant or wording.
+ */
+import assert from "node:assert";
+
+import { basisDisclosureLabel } from "./basis-disclosure-label.ts";
+
+let passed = 0;
+function check(name: string, fn: () => void) {
+  fn();
+  passed += 1;
+  console.log(`  ok - ${name}`);
+}
+
+// --- the three pre-existing statuses -- unchanged behavior after the mechanical refactor -----------
+
+check('"available" is the ok variant with the unchanged label', () => {
+  assert.deepStrictEqual(basisDisclosureLabel("available"), { variant: "ok", label: "Basis: available" });
+});
+
+check('"rebuilt" is the warn variant with the unchanged label', () => {
+  assert.deepStrictEqual(basisDisclosureLabel("rebuilt"), { variant: "warn", label: "Basis: rebuilt" });
+});
+
+check('"unavailable" is the danger variant with the unchanged label', () => {
+  assert.deepStrictEqual(basisDisclosureLabel("unavailable"), { variant: "danger", label: "Basis: unavailable" });
+});
+
+// --- TC-14: the new "unverifiable" status is visibly distinct from BOTH neighbors -------------------
+
+check('"unverifiable" is its OWN distinct variant, not "ok" (never a confident claim -- AG-1)', () => {
+  const result = basisDisclosureLabel("unverifiable");
+  assert.notStrictEqual(result.variant, "ok");
+});
+
+check('"unverifiable" is its OWN distinct variant, not "danger" (a different fact than "run is gone")', () => {
+  const result = basisDisclosureLabel("unverifiable");
+  assert.notStrictEqual(result.variant, "danger");
+});
+
+check('"unverifiable" resolves to the neutral default variant with its own distinct label', () => {
+  assert.deepStrictEqual(basisDisclosureLabel("unverifiable"), {
+    variant: "default",
+    label: "Basis: unverifiable",
+  });
+});
+
+check('every one of the four statuses maps to a UNIQUE (variant, label) pair -- none collapse together', () => {
+  const statuses = ["available", "unavailable", "rebuilt", "unverifiable"] as const;
+  const seen = new Set(statuses.map((s) => JSON.stringify(basisDisclosureLabel(s))));
+  assert.strictEqual(seen.size, statuses.length);
+});
+
+console.log(`\n${passed} passed`);
diff --git a/apps/frontend/lib/basis-disclosure-label.ts b/apps/frontend/lib/basis-disclosure-label.ts
new file mode 100644
index 00000000..f58fc085
--- /dev/null
+++ b/apps/frontend/lib/basis-disclosure-label.ts
@@ -0,0 +1,49 @@
+import type { badgeVariants } from "@/components/ui/badge";
+import type { VariantProps } from "class-variance-authority";
+
+type BadgeVariant = NonNullable<VariantProps<typeof badgeVariants>["variant"]>;
+
+/** Mirrors the backend's `CompassBasisDisclosure.status` string-literal union (lib/api.ts) -- kept as
+ *  its own local type here (rather than importing from api.ts) so this pure module stays
+ *  dependency-free and runnable under plain `node lib/basis-disclosure-label.test.ts` (the project
+ *  convention, no test framework installed) without pulling in api.ts's fetch machinery. */
+export type CompassBasisStatus = "available" | "unavailable" | "rebuilt" | "unverifiable";
+
+export interface BasisDisclosureLabel {
+  variant: BadgeVariant;
+  label: string;
+}
+
+/**
+ * goal-market-compass iter-11 -- the single status -> {variant, label} mapping for the manifest strip's
+ * basis-disclosure badge (`compass-manifest-strip.tsx`'s `BasisLine`), extracted from its previously
+ * inline ternary -- a mechanical refactor, no behavior change for the three pre-existing statuses.
+ *
+ * The fourth status, `"unverifiable"`, is new this iteration (backend fail-closed fix,
+ * `app.engine.compass.basis_disclosure`, docs/goal.md J-11 step 11 ruling A4): it reports an HONEST
+ * "no basis was ever recorded, or it could not be read" fact -- never a confident claim (AG-1: "never a
+ * confident claim"). It must read visibly distinct from BOTH:
+ *   - `"available"` (`ok` / green)      -- a confident "the original basis is intact" claim;
+ *   - `"unavailable"` (`danger` / red)  -- a DIFFERENT fact: the source run IS gone, not merely
+ *     unrecorded/unreadable.
+ * So it gets the neutral `default` badge variant -- never `ok`, `warn`, or `danger` -- and its own
+ * distinct label, never collapsed into either neighbor's wording.
+ */
+export function basisDisclosureLabel(status: CompassBasisStatus): BasisDisclosureLabel {
+  switch (status) {
+    case "available":
+      return { variant: "ok", label: "Basis: available" };
+    case "rebuilt":
+      return { variant: "warn", label: "Basis: rebuilt" };
+    case "unavailable":
+      return { variant: "danger", label: "Basis: unavailable" };
+    case "unverifiable":
+      return { variant: "default", label: "Basis: unverifiable" };
+    default: {
+      // exhaustiveness guard -- a future status literal must be handled explicitly above; never
+      // silently fall through to a variant that could be mistaken for a confident claim.
+      const exhaustiveCheck: never = status;
+      return { variant: "default", label: `Basis: ${exhaustiveCheck as string}` };
+    }
+  }
+}
```
