# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/tests/test_api_compass.py b/apps/backend/tests/test_api_compass.py
index 21895ea3..23179f11 100644
--- a/apps/backend/tests/test_api_compass.py
+++ b/apps/backend/tests/test_api_compass.py
@@ -14,7 +14,8 @@ from datetime import date, datetime, timezone
 
 import pytest
 from fastapi import HTTPException
-from sqlmodel import Session
+from sqlalchemy import delete as sa_delete
+from sqlmodel import Session, select
 
 from app.config import load_config
 from app.db import create_db_and_tables, make_engine
@@ -244,3 +245,77 @@ def test_regenerate_route_mints_version_2_leaves_version_1_untouched(compass_eng
     assert versions[0].manifest_hash == v1["manifest_hash"]
     assert versions[0].content_hash == v1["content_hash"]
     assert versions[0].prospective_eligible is False  # historical as_of was never eligible either
+
+
+# --- TC-8 / TC-9 (route-level basis disclosure, iter-26) ------------------------------------------
+#
+# test_manifest_invariants.py already covers `basis_disclosure()` directly at the UNIT level (calling it
+# with a hand-built row + session where the current run has been deleted / recreated) --
+# `test_basis_disclosure_reads_unavailable_when_the_source_run_is_gone` and
+# `test_basis_disclosure_reads_rebuilt_when_the_source_run_is_recreated`. What was NOT previously proven
+# is what `GET /api/compass` ITSELF observes end-to-end when the underlying run is actually removed --
+# the route calls `resolved_run()` (snapshot_serving -> scanner.resolve_run -> scanner.run_scan) BEFORE
+# `get_or_create_manifest`/`basis_disclosure` ever run, and `run_scan` SELF-HEALS: if the requested as_of
+# still resolves to a valid date (any earlier bar exists), a missing `ScannerRun` is silently
+# RECREATED right there, so by the time `basis_disclosure` looks up "the current run for this as_of" it
+# is never actually absent. The test below proves this empirically (RE-VERIFIED, iter-26 -- iter-3's own
+# audit flagged this exact mechanism as finding B2 and it was never fixed): the live route can reach
+# "available" or "rebuilt", but "unavailable" is structurally UNREACHABLE through this endpoint as
+# currently wired -- it is real, correct, unit-tested code that a request can never actually observe.
+# This is a genuine, pre-existing finding (not a regression introduced this iteration, and fixing the
+# self-heal ordering is a deliberate change outside this iteration's IN SCOPE list) -- recorded here and
+# in the dev handoff for reviewer/auditor visibility. What IS safety-critical and IS proven here: the
+# route never 404s, never crashes, and the frozen manifest's payload/version/manifest_hash stay
+# BYTE-IDENTICAL across the self-heal (AG-12) -- only the read-time basis disclosure differs.
+
+
+def test_compass_route_never_404s_and_manifest_bytes_survive_a_removed_historical_run(compass_engine, cfg, monkeypatch, tmp_path):
+    from app.api.compass import compass as compass_route
+
+    monkeypatch.setenv("TRENDORA_COMPASS_EXPORT_DIR", str(tmp_path))
+
+    # freeze 2024-06-08's manifest while it is still the frontier (mirrors the ingest-finalize freeze)
+    _freeze_frontier(compass_engine, cfg)
+    with Session(compass_engine) as session:
+        before = compass_route("2024-06-08", session)
+    assert before["mode"] == "at_ingest"
+    before_hash = before["manifest_hash"]
+    before_version = before["version"]
+
+    # push the frontier forward with a THIRD, LATER run -- 2024-06-08 becomes a historical as_of, and
+    # 2024-06-01's earlier bar stays in place so as-of resolution for 2024-06-08 still succeeds after its
+    # own bar is removed below (has_bar_on_or_before)
+    with Session(compass_engine) as session:
+        session.add(DailyPrice(symbol="SPY", date=date(2024, 6, 15), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+        session.add(ScannerRun(
+            asof_date=date(2024, 6, 15), created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+            regime_score=61.0, regime_label="Expansion", regime_components_json="[]",
+            breadth_above_50dma=55.0, breadth_above_200dma=60.0, new_high_low_json="{}", candidate_counts_json="{}",
+        ))
+        session.commit()
+
+    # remove 2024-06-08's ScannerRun (+ children) + its own DailyPrice bar -- mirrors remove_data's cascade
+    with Session(compass_engine) as session:
+        removed_run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == date(2024, 6, 8))).first()
+        session.execute(sa_delete(ScannerResult).where(ScannerResult.run_id == removed_run.id))
+        session.execute(sa_delete(ScannerRun).where(ScannerRun.id == removed_run.id))
+        session.execute(sa_delete(DailyPrice).where(DailyPrice.date == date(2024, 6, 8)))
+        session.commit()
+
+    with Session(compass_engine) as session:
+        gone = session.exec(select(ScannerRun).where(ScannerRun.asof_date == date(2024, 6, 8))).first()
+    assert gone is None  # confirmed removed immediately before the route call below
+
+    with Session(compass_engine) as session:
+        after = compass_route("2024-06-08", session)  # must NEVER 404, NEVER raise
+
+    assert after["manifest_hash"] == before_hash  # AG-12: the frozen manifest payload is byte-unchanged
+    assert after["version"] == before_version
+    # the re-verified finding: self-heal recreates the run before basis_disclosure runs, so the live
+    # route observes "rebuilt", never "unavailable" -- see the block docstring above.
+    assert after["basis"]["status"] == "rebuilt"
+
+    with Session(compass_engine) as session:
+        healed = session.exec(select(ScannerRun).where(ScannerRun.asof_date == date(2024, 6, 8))).first()
+    assert healed is not None  # confirms the self-heal actually fired (not merely absent-run tolerance)
diff --git a/apps/backend/tests/test_manifest_invariants.py b/apps/backend/tests/test_manifest_invariants.py
index 3df682b4..0ca8e0d4 100644
--- a/apps/backend/tests/test_manifest_invariants.py
+++ b/apps/backend/tests/test_manifest_invariants.py
@@ -99,23 +99,126 @@ def test_tc14_time_safety_content_hash_unchanged_by_post_asof_bar_change(engine,
 # --- TC-15 (immutability) -------------------------------------------------------------------------
 
 
-def test_tc15_no_update_statement_targets_next_session_manifests():
-    """A static source-text audit: no UPDATE statement (SQLAlchemy `.update(...)` call or raw SQL) targets
-    `NextSessionManifest` / `next_session_manifests` anywhere in the engine layer."""
+def _references_manifest_target(node: "ast.AST") -> bool:
+    """True if `node` names the `NextSessionManifest` ORM model, a `.NextSessionManifest` attribute
+    access, or the literal `next_session_manifests` table-name string."""
+    import ast
+
+    for sub in ast.walk(node):
+        if isinstance(sub, ast.Name) and sub.id == "NextSessionManifest":
+            return True
+        if isinstance(sub, ast.Attribute) and sub.attr == "NextSessionManifest":
+            return True
+        if isinstance(sub, ast.Constant) and sub.value == "next_session_manifests":
+            return True
+    return False
+
+
+def _scan_source_for_manifest_update_offenders(filename: str, text: str) -> list[str]:
+    """Flags only a genuine SQLAlchemy Update-statement / ORM bulk-update call reachable against
+    `NextSessionManifest` / `next_session_manifests`:
+      - the Core `update(NextSessionManifest)` construct, called bare (`update(...)`) or as a module
+        attribute (`sa.update(...)`);
+      - the ORM bulk-update idiom `<query-chain ending in .query(NextSessionManifest)>.update(...)`;
+      - a raw SQL string literal containing both "update" and the table name.
+    Any OTHER `.update(...)` attribute call (dict.update, hashlib digest.update, or any object unrelated
+    to the manifest query/model) is not an UPDATE statement against the manifest table and is never
+    flagged -- this is the iter-26 narrowing that fixes the false positive on `.update()` calls in the
+    J-11 stage modules (dict/hashlib-digest updates that merely live in a module which also mentions the
+    manifest table/model in unrelated text)."""
     import ast
 
+    offenders: list[str] = []
+    tree = ast.parse(text)
+    for node in ast.walk(tree):
+        if isinstance(node, ast.Constant) and isinstance(node.value, str):
+            lowered = node.value.lower()
+            if "update" in lowered and "next_session_manifests" in lowered:
+                offenders.append(f"{filename}: raw SQL string literal UPDATEs the manifest table")
+            continue
+
+        if not isinstance(node, ast.Call):
+            continue
+
+        if isinstance(node.func, ast.Name) and node.func.id == "update":
+            # bare `update(...)` -- the SQLAlchemy Core update() construct, imported directly
+            args = list(node.args) + [kw.value for kw in node.keywords]
+            if any(_references_manifest_target(a) for a in args):
+                offenders.append(f"{filename}: update(...) construct targets the manifest table")
+            continue
+
+        if isinstance(node.func, ast.Attribute) and node.func.attr == "update":
+            value = node.func.value
+            if isinstance(value, ast.Call):
+                # a chained call -- walk back through `.filter(...)`/`.filter_by(...)`/etc. looking for
+                # a `.query(NextSessionManifest)` link: the ORM bulk-update idiom
+                # `session.query(NextSessionManifest)....update(...)`
+                chain_node = value
+                while isinstance(chain_node, ast.Call):
+                    if isinstance(chain_node.func, ast.Attribute) and chain_node.func.attr == "query":
+                        if any(_references_manifest_target(a) for a in chain_node.args):
+                            offenders.append(f"{filename}: <query>.update(...) bulk-updates the manifest table")
+                        break
+                    chain_node = chain_node.func.value if isinstance(chain_node.func, ast.Attribute) else None
+            else:
+                # module-attribute style, e.g. `sa.update(NextSessionManifest)`
+                if any(_references_manifest_target(a) for a in node.args):
+                    offenders.append(f"{filename}: update(...) construct targets the manifest table")
+            continue
+    return offenders
+
+
+def test_tc15_no_update_statement_targets_next_session_manifests():
+    """A static source-text audit: no UPDATE statement (the SQLAlchemy Core `update(...)` construct, the
+    ORM `.query(NextSessionManifest)....update(...)` bulk-update idiom, or raw SQL) targets
+    `NextSessionManifest` / `next_session_manifests` anywhere in the engine layer. Narrowed (iter-26,
+    TC-1) to flag only a call reachable against the manifest model/table -- see
+    `_scan_source_for_manifest_update_offenders` for exactly what is and is not flagged; an unrelated
+    `.update(...)` attribute call (dict, hashlib digest, or any other object) is never flagged even in a
+    module that mentions the manifest table/model elsewhere in unrelated text."""
     offenders: list[str] = []
     for path in (REPO_ROOT / "apps/backend/app/engine").glob("*.py"):
         text = path.read_text()
         if "next_session_manifests" not in text and "NextSessionManifest" not in text:
             continue
-        tree = ast.parse(text)
-        for node in ast.walk(tree):
-            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "update":
-                offenders.append(f"{path.name}: a .update(...) call in a module referencing the manifest table")
+        offenders.extend(_scan_source_for_manifest_update_offenders(path.name, text))
     assert not offenders, offenders
 
 
+def test_tc15_scanner_mutation_check_catches_a_real_manifest_update_statement():
+    """TC-1 mutation-kill check (iter-26): the narrowed scanner above must still catch a REAL manifest
+    UPDATE if one is ever introduced. Exercises the scanner directly against synthetic source text --
+    never by injecting an actual bug into shipped `app/engine` code -- so this test is itself safe to
+    run every time."""
+    core_construct_src = (
+        "from sqlalchemy import update\n"
+        "from app.models import NextSessionManifest\n"
+        "def _bad(session):\n"
+        "    session.execute(update(NextSessionManifest).where(NextSessionManifest.id == 1).values(frozen=False))\n"
+    )
+    assert _scan_source_for_manifest_update_offenders("synthetic.py", core_construct_src)
+
+    orm_bulk_update_src = (
+        "from app.models import NextSessionManifest\n"
+        "def _bad(session):\n"
+        "    session.query(NextSessionManifest).filter_by(id=1).update({'frozen': False})\n"
+    )
+    assert _scan_source_for_manifest_update_offenders("synthetic.py", orm_bulk_update_src)
+
+    raw_sql_src = 'def _bad(session):\n    session.execute("UPDATE next_session_manifests SET frozen = 0")\n'
+    assert _scan_source_for_manifest_update_offenders("synthetic.py", raw_sql_src)
+
+    # sanity: the exact false-positive shapes already living in app/engine stay clean
+    false_positive_src = (
+        "from app.models import NextSessionManifest\n"
+        "def _fine(entry, digest, chunk):\n"
+        "    entry.update({'a': 1})\n"
+        "    digest.update(chunk)\n"
+        "    return NextSessionManifest\n"
+    )
+    assert _scan_source_for_manifest_update_offenders("synthetic.py", false_positive_src) == []
+
+
 def test_tc15_clear_snapshot_set_and_remove_data_delete_zero_manifest_rows(engine, cfg, frontier_run):
     from app.engine import data_manager
 
@@ -164,6 +267,78 @@ def test_tc15_export_writer_never_rewrites_an_existing_artifact(engine, cfg, fro
     assert sorted(p.name for p in tmp_path.iterdir()) == [Path(first_path).name]
 
 
+# --- TC-2 (export-byte-equality, audit finding B3, iter-3 -- closed iter-26) -----------------------
+
+
+def test_tc2_export_file_bytes_equal_served_payload_and_manifest_hash_reproduces(
+    engine, cfg, frontier_run, tmp_path, monkeypatch
+):
+    """TC-2 / audit finding B3 (iter-3, closed iter-26): the on-disk export file's bytes equal the
+    `manifest_row_payload` reconstruction (the served `GET /api/compass` shape) byte-for-byte -- the
+    same read path production serves, not the in-memory write-time `document` dict -- and recomputing
+    `manifest_hash` over the exported bytes, with the `manifest_hash` field itself excluded per the
+    canonical rule, reproduces the embedded value. Fixture-scoped (isolated engine) -- mirrors, and is
+    cited alongside, the live read-only spot-check against `2026-08-12_v6.json` recorded in the dev
+    handoff."""
+    monkeypatch.setenv("TRENDORA_COMPASS_EXPORT_DIR", str(tmp_path))
+
+    with Session(engine) as session:
+        run = session.get(ScannerRun, frontier_run)
+        row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
+        export_path = row.export_path
+        served = compass.manifest_row_payload(row)
+    assert export_path is not None, "an at_ingest freeze must export"
+
+    exported_bytes = Path(export_path).read_bytes()
+    served_bytes = compass._canonical_dumps(served).encode()
+    assert exported_bytes == served_bytes, "export file bytes must equal the served payload byte-for-byte"
+
+    exported_document = json.loads(exported_bytes)
+    embedded_hash = exported_document["manifest_hash"]
+    without_hash = {key: value for key, value in exported_document.items() if key != "manifest_hash"}
+    recomputed_hash = compass._sha256_hex(compass._canonical_dumps(without_hash))
+    assert recomputed_hash == embedded_hash, "manifest_hash recomputed over the exported bytes must match"
+    assert compass.verify_manifest_hash(exported_document) is True  # same fact via the production helper
+
+
+# --- TC-7 (J-06 step 1): backfilling a SEPARATE date leaves a stored manifest untouched -------------
+
+
+def test_tc7_backfilling_a_separate_date_leaves_the_first_stored_manifest_unchanged(engine, cfg, frontier_run, tmp_path, monkeypatch):
+    """TC-7 / J-06 step 1: with one manifest already frozen (`frontier_run`, as_of 2024-07-01), freezing a
+    SEPARATE, later date's manifest -- exactly what the finalize hook does for each newly-processed date
+    -- leaves the FIRST manifest's stored bytes and version byte-identical. Not already its own assertion
+    elsewhere: `test_tc15_clear_snapshot_set_and_remove_data_delete_zero_manifest_rows` proves ROW COUNT
+    survives a full snapshot clear; `test_tc14_time_safety_...` proves `content_hash` survives a
+    POST-AS-OF bar perturbation on the SAME as_of; neither proves an entirely SEPARATE date's own freeze
+    leaves this manifest's PAYLOAD BYTES/version untouched."""
+    monkeypatch.setenv("TRENDORA_COMPASS_EXPORT_DIR", str(tmp_path))
+
+    with Session(engine) as session:
+        run = session.get(ScannerRun, frontier_run)
+        first_row = compass.get_or_create_manifest(session, run, cfg, producer="ingest_finalize")
+        before_payload = compass.manifest_row_payload(first_row)
+        before_version = first_row.version
+
+    # freeze a SEPARATE, later date's manifest -- unrelated to the first manifest's as_of
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="SPY", date=date(2024, 7, 8), open=1, high=1, low=1, close=1, volume=1))
+        other_run = _mk_run(session, date(2024, 7, 8))
+        _mk_result(session, other_run.id, "BBB")
+        session.commit()
+        session.refresh(other_run)
+        compass.get_or_create_manifest(session, other_run, cfg, producer="ingest_finalize")
+
+    with Session(engine) as session:
+        rows = session.exec(
+            select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 7, 1))
+        ).all()
+    assert len(rows) == 1  # still exactly one version -- the separate freeze minted no second version here
+    after_row = rows[0]
+    assert after_row.version == before_version
+    assert compass.manifest_row_payload(after_row) == before_payload
+
+
 # --- read-time basis disclosure (TC-10 / TC-11 branches) ------------------------------------------
 
 
```
