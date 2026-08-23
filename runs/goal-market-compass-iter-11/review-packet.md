# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 7. Shown in full: 7.

```diff
diff --git a/apps/backend/app/engine/compass.py b/apps/backend/app/engine/compass.py
index 2713362f..8aba9c64 100644
--- a/apps/backend/app/engine/compass.py
+++ b/apps/backend/app/engine/compass.py
@@ -1098,16 +1098,40 @@ def list_manifest_versions(session: Session, as_of: date) -> list[NextSessionMan
 
 
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
+      - `generation_json` parses but omits the `source_run_created_at` key (TC-12) — present but
+        incomplete, exactly as unverifiable as absent.
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
+    if "source_run_created_at" not in generation:
+        # well-formed JSON, but the one field this comparison depends on is absent.
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
index ee6a61f5..7e503e71 100644
--- a/apps/backend/tests/test_manifest_invariants.py
+++ b/apps/backend/tests/test_manifest_invariants.py
@@ -207,6 +207,86 @@ def test_basis_disclosure_reads_rebuilt_when_the_source_run_is_recreated(engine,
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
index 8125124e..d4548129 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -868,6 +868,17 @@ manifest artifact (it must be self-describing and self-caveating).
       introduced without an owner amendment. If some symbols ultimately cannot be restored under the
       fixed methodology, surface the **exact residual set and the per-symbol reasons** for
       owner/reviewer decision rather than silently lowering the coverage requirement.
+    - **J-10 CLOSED — residual set accepted (owner, 2026-08-23).** The owner/reviewer decision the
+      completion rule above calls for has now been made. **J-10 is raw-layer terminal at 585 restored
+      / 2 explicitly unrestorable.** The final fail-closed residual set is exactly:
+      - **EA** — Yahoo has no trading data past 2026-08-10; a real delisting, not a gate failure.
+      - **EQR** — only 1 comparable calibration pair, below the fixed 3-pair floor; the gate correctly
+        refused to write.
+      This is an acceptance of a **named, per-symbol-reasoned residual set**, NOT a partial-completion
+      threshold: no "enough symbols" number is introduced, and the ban on inventing one stands. Do not
+      reopen J-10 to retry EA or EQR, do not fetch further data for them under J-10, and do not treat
+      this acceptance as licence to lower coverage for any future population. AG-9's live-fetch
+      exception for J-10 is **exhausted** — it authorizes nothing further.
     - **Recorded finding — the one-series rule worked, and a vendor-provenance correction
       (iteration 8; corrected 2026-08-21 by the out-of-band audit — read the correction, it changes
       what the result means):** running the comparison and the restore through the same raw-close
@@ -1133,10 +1144,19 @@ manifest artifact (it must be self-describing and self-caveating).
        `available_at_utc`, or `prospective_eligible`. The implementer must determine the safest
        schema/migration strategy and **prove it before the destructive phase**. This repository has no
        Alembic, so a table rewrite must not be prescribed casually — any approach must be shown to
-       preserve every historical artifact byte-for-byte. Reassuringly, the read path already does the
-       right thing and needs no change: `compass.basis_disclosure` (`compass.py:1100-1115`) resolves
-       the current run **by `as_of`** and compares the recorded `source_run_created_at` against that
-       run's `created_at` — it never dereferences `source_run_id`.
+       preserve every historical artifact byte-for-byte. The read path's **design** is right and stays
+       authoritative: `compass.basis_disclosure` (`compass.py:1100-1115`) resolves the current run **by
+       `as_of`** and compares the recorded `source_run_created_at` against that run's `created_at` — it
+       never dereferences `source_run_id`. **Correction (owner, 2026-08-23): its implementation is
+       nevertheless defective and must be fixed — the earlier "needs no change" reading is withdrawn.**
+       `compass.py:1108-1109` short-circuits to `{"status": "available"}` when `generation_json` is
+       empty, so a manifest with no recorded basis reports its original basis as intact. Verified live:
+       the 2026-08-12 version-1 manifest (recorded source run 3081, long gone; current run 3148) reports
+       `available` while its five sibling versions correctly report `rebuilt`, and **8 of 24 live
+       manifests carry `generation_json` NULL** (count corrected 2026-08-23 from the "10" first recorded
+       by the iteration-10 evaluator; re-verified read-only: 24 rows total, 8 NULL, 0 empty-string).
+       `basis_disclosure` rides on every `GET /api/compass` payload,
+       so this is a fabricated-state defect on a served surface — precisely the class AG-1 forbids.
        **Stage C may not begin until all six of these are proven:**
        1. the live schema's manifest/run relationship matches the documented
           manifest-survives-rebuild contract;
@@ -1157,6 +1177,60 @@ manifest artifact (it must be self-describing and self-caveating).
        "repair" an orphaned foreign key.
        **If this contradiction cannot be resolved safely inside the current repository without a risky
        migration, STOP before J-11 and surface it as an owner decision.**
+       **That STOP fired at iteration 10 and the owner has now decided (owner, 2026-08-23).** Verified
+       live at that point: the table DDL still ends in `FOREIGN KEY(source_run_id) REFERENCES
+       scanner_runs (id)`, `PRAGMA foreign_keys` reads `0`, and `pragma_foreign_key_check` returns 12
+       violations — so acceptance items 1 and 4 were false on the live database, and the iter-10
+       `models.py` declaration change fixed only metadata-built databases, not the live file Stage C
+       deletes from. The ruling:
+       - **A1 — Bounded live-schema migration is AUTHORIZED.** A narrowly bounded live-schema migration
+         of `next_session_manifests` **only** is authorized, for the **sole** purpose of removing the
+         `source_run_id -> scanner_runs.id` foreign-key constraint. SQLite cannot drop a constraint in
+         place, so the mechanical table rebuild (create constraint-free table → copy rows → drop old →
+         rename) is authorized **as a mechanical relocation**. No other table's schema may be altered
+         under this authorization, and this is the **only** destructive-schema operation authorized
+         anywhere in this goal. It is not a precedent for any other table or any later convenience.
+       - **A2 — Absolute preservation.** All **24** manifest rows and **every stored value** must
+         survive **exactly**. `source_run_id` **values are preserved as stored historical provenance**
+         — only the constraint is removed — including the orphaned ids (3048, 3049, 3081, 3112), which
+         must keep their recorded values and must **not** be nulled, rebound, or "repaired". **No
+         manifest may be regenerated, rebound, rehashed, upgraded, deleted, or newly minted** (see
+         AG-18). AG-12 and AG-17 are **not** waived: the rebuild is byte-preserving relocation, never
+         mutation. Any changed stored value is an AG-12 violation and a REGRESSION, not a fixable note.
+       - **A3 — Proof obligations, all on the LIVE database, all before Stage C.**
+         1. **Pre/post full-row equality:** dump all 24 rows × all columns to a persisted evidence
+            artifact **before** the migration, re-dump **after**, and prove equality per row and per
+            column (not an aggregate-only check — iteration 9's lesson). Row count 24 → 24.
+         2. The six acceptance items above are then re-proven against the live database, not against a
+            fixture. Item 4 in particular must be demonstrated with `PRAGMA foreign_keys=ON`, since
+            "it works because FK checking is off" is exactly what item 4 excludes.
+         3. `sqlite_master` DDL for `next_session_manifests` contains no `FOREIGN KEY` clause, and
+            `pragma_foreign_key_check(next_session_manifests)` returns **zero** rows.
+         4. Mutation accounting: prove no table other than `next_session_manifests` was written.
+       - **A4 — `basis_disclosure` fail-closed fix is a Stage C precondition.** Before Stage C, fix the
+         defect recorded above so the read path **fails closed**: when `generation_json` is missing,
+         empty, or malformed, or when `source_run_created_at` is absent, `basis_disclosure` must **never**
+         report `available`. It must return an explicit unverifiable/unknown state and the UI must render
+         the honest "not yet proven"-class placeholder — never a confident claim that the original basis
+         is intact (AG-1). Cover each degenerate input with its own test, and re-verify read-only against
+         the 8 live manifests that carry `generation_json` NULL. Treat the *count* as evidence to
+         re-derive, not to trust: verify it yourself read-only rather than quoting this line.
+       - **A5 — Maintenance isolation stays ACTIVE.** No application-service boot, no browser-QA lane,
+         and no deterministic-replay lane, unchanged, until Stage G. The migration iteration is the
+         **single** authorized exception to "zero writes to `trendora.db`", and its writes are bounded to
+         the `next_session_manifests` rebuild alone. One controlled writer, no backend warmup, and the
+         7.8 GB file is never copied or opened for write by anything else.
+       - **A6 — Hard gate on Stage C.** **Stage C may not begin until BOTH the schema migration and the
+         `basis_disclosure` fix have passed reviewer, QA, and auditor review AND live read-only
+         verification.** This gate is **in addition to** the six acceptance items, not a substitute for
+         them. Reviewer and QA marking the DoD "complete" is not sufficient evidence — at iteration 10
+         both did so while two acceptance items were false on the live database; the claim must be
+         re-derived from the live database by the verifying agent.
+       - **A7 — Failure semantics.** If pre/post row equality cannot be proven, roll the table back to
+         its pre-migration state, write the evidence, and STOP for owner review. Never proceed to Stage C
+         from a partially migrated or unproven table.
+       This work is **Stage B1-completion**, a separate iteration (or iterations) before Stage C — it is
+       not part of the Stage C destructive unit and does not start it.
     12. **Stage B2 — freeze ONE engine identity for the whole attempt (owner, 2026-08-21).** J-11's
        claim is that the incident set ends up as one internally consistent current-engine derivation;
        that claim must be testable. Before Stage C, freeze the intended current engine identity and
@@ -1409,6 +1483,14 @@ manifest artifact (it must be self-describing and self-caveating).
   drill result, its handoff, the reviewer/QA evidence already produced, and the explicit statement that the
   committed seed could not restore these dates MUST NOT be deleted, rewritten, or silently superseded.
   Repairing the database never rewrites historical causality. *(critical)*
+- **AG-18 — The authorized manifest migration preserves everything (owner, 2026-08-23):** the bounded
+  `next_session_manifests` schema migration authorized in J-11 step 11 (ruling A1) removes the
+  `source_run_id` foreign-key constraint and **nothing else**. No manifest may be **regenerated,
+  rebound, rehashed, upgraded, deleted, or newly minted** by it or around it. All 24 rows and every
+  stored column value — `as_of`, `source_run_id` (orphans included), `generation_json`, `content_hash`,
+  `manifest_hash`, `version`, `available_at_utc`, `prospective_eligible` — survive exactly, proven by
+  persisted pre/post per-row evidence. No other table's schema may be altered under that authorization.
+  A changed stored value is a REGRESSION, never a note. *(critical)*
 
 ## Loop mechanics (for the iteration planner)
 
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-market-compass-index.html     |  4 +-
 .../goal-session-market-compass/.engine.lock/epoch |  2 +-
 runs/goal-session-market-compass/.engine.lock/pid  |  2 +-
 runs/goal-session-market-compass/engine.pid        |  2 +-
 runs/goal-session-market-compass/session.json      | 11 +++---
 .../state/assumptions.md                           | 22 +++++++++++
 .../goal-session-market-compass/state/blueprint.md | 16 +++++++-
 runs/goal-session-market-compass/state/lessons.md  | 25 +-----------
 .../state/lessons.md.archive.md                    | 32 +++++++++++++++
 runs/goal-session-market-compass/summary.md        | 46 ++++++++++++++--------
 runs/goal-session-market-compass/telemetry.jsonl   | 22 +++++++++++
 runs/goal-session-market-compass/trace/.next-step  |  2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |  4 ++
 13 files changed, 139 insertions(+), 51 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
