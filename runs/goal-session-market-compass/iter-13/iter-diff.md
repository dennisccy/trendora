# Iteration diff (bounded)

Files changed: 5. Shown in full: 4.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/j11_stage_c.py` (241 lines not shown)

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index cd2fa001..6ddc9599 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -43,7 +43,7 @@ from contextlib import nullcontext
 from dataclasses import dataclass, field
 from datetime import date as date_cls, datetime, timedelta, timezone
 from pathlib import Path
-from typing import Callable, Optional
+from typing import Callable, Iterable, Optional
 
 from sqlalchemy import delete, func, insert
 from sqlalchemy.engine import Engine
@@ -2236,6 +2236,92 @@ def clear_snapshot_set(session: Session) -> dict:
     return {"runs_cleared": runs_cleared, "bars_before": bars_before, "bars_after": bars_after}
 
 
+# --------------------------------------------------------------------------------------------------
+# goal-market-compass iter-13 -- J-11 Stage C: the bounded, EXACT-DATE-FILTERED specialization of
+# `clear_snapshot_set` above (docs/goal.md J-11 step 11's OWNER AUTHORIZATION block, ruling C6: "Use
+# `clear_snapshot_dates(EXACT_INCIDENT_DATE_SET)` ... never `clear_snapshot_set()`"). SAME
+# child-before-parent deletion order, SAME whole-row-delete discipline, SAME `daily_prices`-untouched
+# assertion -- but scoped to only the `ScannerRun`s whose `asof_date` is IN `exact_date_set`, never the
+# entire snapshot history. This function NEVER calls `clear_snapshot_set` (which takes no date filter).
+# --------------------------------------------------------------------------------------------------
+def clear_snapshot_dates(session: Session, exact_date_set: Iterable[date_cls]) -> dict:
+    """DELETE only the Layer-2 derived-state rows owned (by `run_id`) by a `ScannerRun` whose
+    `asof_date` is one of `exact_date_set` (J-11 Stage C). For each date: freshly queries the CURRENT
+    `ScannerRun` for that `asof_date` (never a cached/prior inventory -- iter-9's "never inherit a prior
+    claim without re-checking it" lesson); no run -> a documented zero-row no-op for that date, never an
+    error; a run exists -> deletes every `ForwardReturn` / `ScannerResult` / `SectorScoreRow` /
+    `ThemeScoreRow` row whose `run_id` equals that run's id, then the `ScannerRun` row itself --
+    children before parents, mirroring `clear_snapshot_set`'s own order exactly. Never deletes a row
+    keyed only by `measured_date`/other-date membership outside this run-owned scope -- that population
+    is either already absent (the original incident's own defensive sweep already removed it) or Stage
+    E's repair target, never Stage C's (runs/goal-session-market-compass/state/assumptions.md, iter-13
+    entry #1).
+
+    Asserts the `daily_prices` row count is identical immediately before and after the WHOLE batch
+    (mirrors `clear_snapshot_set`'s `bars_before == bars_after` invariant; `daily_prices` is never even
+    referenced by a DELETE here). Never calls `compass.get_or_create_manifest`, `scanner.run_scan`,
+    `scanner.persist_run_payload`, or `_refresh_ingest_aggregates` -- issues DELETE statements only
+    (ruling C8: Stage C is deletion only).
+
+    Returns `{per_date: {date_iso: {run_id, deleted: {table: count}}}, totals: {table: count},
+    bars_before, bars_after}` -- the caller's own mutation-accounting evidence is built from this plus
+    the pre-declared intended-delete-set (`app.engine.j11_stage_c.capture_intended_delete_set`), never
+    from a second independent count."""
+    bars_before = int(session.scalar(select(func.count()).select_from(DailyPrice)) or 0)
+    per_date: dict[str, dict] = {}
+    totals: dict[str, int] = {
+        "scanner_runs": 0,
+        "forward_returns": 0,
+        "scanner_results": 0,
+        "sector_scores": 0,
+        "theme_scores": 0,
+    }
+    for one_date in exact_date_set:
+        key = one_date.isoformat()
+        run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == one_date)).first()
+        if run is None:
+            per_date[key] = {
+                "run_id": None,
+                "deleted": {
+                    "scanner_runs": 0, "forward_returns": 0, "scanner_results": 0,
+                    "sector_scores": 0, "theme_scores": 0,
+                },
+            }
+            continue
+        run_id = run.id
+        deleted = {
+            "forward_returns": int(
+                session.scalar(select(func.count()).select_from(ForwardReturn).where(ForwardReturn.run_id == run_id)) or 0
+            ),
+            "scanner_results": int(
+                session.scalar(select(func.count()).select_from(ScannerResult).where(ScannerResult.run_id == run_id)) or 0
+            ),
+            "sector_scores": int(
+                session.scalar(select(func.count()).select_from(SectorScoreRow).where(SectorScoreRow.run_id == run_id)) or 0
+            ),
+            "theme_scores": int(
+                session.scalar(select(func.count()).select_from(ThemeScoreRow).where(ThemeScoreRow.run_id == run_id)) or 0
+            ),
+        }
+        # children first (FK order), then the parent run. Whole-row deletes; daily_prices never referenced.
+        session.execute(delete(ForwardReturn).where(ForwardReturn.run_id == run_id))
+        session.execute(delete(ScannerResult).where(ScannerResult.run_id == run_id))
+        session.execute(delete(SectorScoreRow).where(SectorScoreRow.run_id == run_id))
+        session.execute(delete(ThemeScoreRow).where(ThemeScoreRow.run_id == run_id))
+        session.execute(delete(ScannerRun).where(ScannerRun.id == run_id))
+        deleted["scanner_runs"] = 1
+        per_date[key] = {"run_id": run_id, "deleted": deleted}
+        for table_name, count_value in deleted.items():
+            totals[table_name] += count_value
+    session.commit()
+    bars_after = int(session.scalar(select(func.count()).select_from(DailyPrice)) or 0)
+    if bars_after != bars_before:
+        raise RuntimeError(
+            f"Stage C bounded clear corrupted the price seed: {bars_before} bars before, {bars_after} after"
+        )
+    return {"per_date": per_date, "totals": totals, "bars_before": bars_before, "bars_after": bars_after}
+
+
 # --------------------------------------------------------------------------------------------------
 # Import provider catalog + env-detected availability (J-33) — descriptive metadata, NO key value
 # --------------------------------------------------------------------------------------------------
diff --git a/apps/backend/app/engine/j11_stage_c.py b/apps/backend/app/engine/j11_stage_c.py
new file mode 100644
index 00000000..21c1ef28
--- /dev/null
+++ b/apps/backend/app/engine/j11_stage_c.py
@@ -0,0 +1,635 @@
+"""app.engine.j11_stage_c -- J-11 Stage C precondition/evidence tooling (goal-market-compass iter-13).
+
+`docs/goal.md` J-11 step 11's "## OWNER AUTHORIZATION -- J-11 Stage C (owner, 2026-08-24)" block
+(rulings C1-C12) authorizes exactly ONE destructive action this iteration: the bounded, exact-11-date
+clear of Layer 2 derived state via `app.engine.data_manager.clear_snapshot_dates`. Everything in THIS
+module is read-only precondition/evidence tooling around that one call -- it deletes, updates, and
+inserts nothing:
+
+  - `capture_stage_c_preflight` (ruling C2) -- re-derives live state fresh (git HEAD, the J-11 contract
+    text hash, a NEW Stage C attempt id wrapping the re-derived Stage B2 `engine_identity`, the 11-date
+    inventory, the manifest table's DDL/index/full dump, and every table's row count), never trusting a
+    prior iteration's certified figures.
+  - `compare_preflight_to_certified` (TC-1/TC-2) -- the preflight comparison gate against iteration 12's
+    certified live state. ANY invariant failing here means the caller MUST stop before the first
+    destructive statement.
+  - `check_c1_date_set_boundary` / `extract_incident_date_lists` (TC-3) -- proves the code's
+    `INCIDENT_DATES` list is byte-identical to BOTH goal.md's "the incident date set -- all 11" bullet
+    and the C1 restatement; a disagreement between the two, or either date list going missing, halts
+    before any deletion (fail-closed anchor-based extraction -- never a broad guess).
+  - `capture_intended_delete_set` (ruling C9) -- the exact per-table row-id set to be removed, captured
+    and persisted BEFORE `clear_snapshot_dates` runs, so the post-delete evidence has something concrete
+    to be checked against.
+  - `capture_layer2_population_fingerprints` / `incident_scoped_counts` / `small_table_id_snapshot` /
+    `build_mutation_accounting` -- the post-delete mutation-accounting proof: per-table PRE/DELETED/POST
+    counts split incident vs. non-incident, an explicit ID-set-derived diff (never aggregate counts
+    alone), and `daily_prices`/manifest/provider-run/watchlist fingerprints proven unchanged.
+
+Every DB-facing function here composes ALREADY-EXISTING read-only primitives
+(`app.engine.j11_maintenance.capture_pre_reset_inventory` / `freeze_attempt_identity` / `INCIDENT_DATES`,
+`app.engine.j11_schema_migration.fetch_object_ddl` / `dump_table` / `diff_dumps` /
+`capture_full_db_snapshot`) rather than reinventing an inventory formula. The ONE destructive mechanism
+(`clear_snapshot_dates`) deliberately lives in `app.engine.data_manager`, next to the pattern it
+specializes (`clear_snapshot_set`) -- NOT in this module, which stays read-only/pure precondition and
+evidence-assembly tooling, mirroring `j11_maintenance.py`'s own "nothing here deletes" posture.
+
+`_population_fingerprint`'s design note (AG-8 / host resource ceiling): `forward_returns` alone holds
+~6.8M rows and `scanner_results` ~1.3M on the live database. Proving "every non-incident-date row id
+present before is still present after" therefore uses a cheap SQL-side aggregate (count, min id, max id,
+id sum -> sha256) over the population EXCLUDING the deleted run ids, rather than materializing millions
+of ids into a Python set (an unbounded whole-table load AG-8 forbids). This is sufficient because Stage C
+is DELETE-ONLY (ruling C8, mechanically proven by the fixture call-count assertions in
+`test_j11_stage_c_bounded_clear.py`): no INSERT path is ever exercised, so the only way the excluded
+population's count/min/max/sum could move is if the DELETE predicate matched a row outside the declared
+run-id set -- exactly what `capture_intended_delete_set`'s own exact, fully-enumerated id lists (small
+and bounded, since only the currently-run-bearing incident dates own any rows at all) independently
+catch. Combined, the two proofs are strictly stronger than either alone and touch no unbounded table
+scan.
+"""
+from __future__ import annotations
+
+import hashlib
+import json
+import re
+import subprocess
+from datetime import date, datetime, timezone
+from pathlib import Path
+from typing import Any, Optional
+
+from sqlalchemy import func, text
+from sqlalchemy.engine import Engine
+from sqlmodel import Session, select
+
+from app.config import Config, REPO_ROOT
+from app.engine import j11_maintenance
+from app.engine import j11_schema_migration as migration
+from app.engine.j11_maintenance import INCIDENT_DATES
+from app.models import (
+    DataProviderRun,
+    ForwardReturn,
+    NextSessionManifest,
+    ScannerResult,
+    ScannerRun,
+    SectorScoreRow,
+    ThemeScoreRow,
+    Watchlist,
+)
+
+DEFAULT_GOAL_MD_PATH = REPO_ROOT / "docs" / "goal.md"
+
+# The five Layer-2 tables ruling C4 authorizes clearing, keyed by their table name (used consistently
+# across the delete-set capture, the population fingerprints, and the mutation-accounting report).
+_CHILD_MODELS: dict[str, Any] = {
+    "forward_returns": ForwardReturn,
+    "scanner_results": ScannerResult,
+    "sector_scores": SectorScoreRow,
+    "theme_scores": ThemeScoreRow,
+}
+
+
+# ----------------------------------------------------------------------------------------------
+# Filesystem/git I/O wrappers -- kept thin and separately swappable so every computation function
+# below stays a pure, fixture-testable composition (the CLI script calls these two, then passes the
+# results in as plain values).
+# ----------------------------------------------------------------------------------------------
+
+
+def read_goal_md_text(path: Path = DEFAULT_GOAL_MD_PATH) -> str:
+    """The committed goal.md file's raw text -- read-only, no parsing here."""
+    return path.read_text()
+
+
+def read_git_head(repo_root: Path = REPO_ROOT) -> Optional[str]:
+    """Current git HEAD commit hash, or `None` if it cannot be determined (never raises -- a missing git
+    context must not crash preflight capture; it is recorded honestly as `None` instead)."""
+    try:
+        result = subprocess.run(
+            ["git", "rev-parse", "HEAD"],
+            cwd=str(repo_root),
+            capture_output=True,
+            text=True,
+            timeout=10,
+            check=True,
+        )
+        return result.stdout.strip() or None
+    except Exception:
+        return None
+
+
+# ----------------------------------------------------------------------------------------------
+# C1 -- the J-11 contract text + the two goal.md 11-date lists (TC-3)
+# ----------------------------------------------------------------------------------------------
+
+_J11_SECTION_START = "- **J-11: Incident-bounded clean regeneration of derived state (owner, 2026-08-21)**"
+_J11_SECTION_END = "<!-- Continuous-improvement auto-journeys:"
+
+# Anchored to the literal surrounding prose from docs/goal.md so this never matches an unrelated date
+# list elsewhere in the document -- fails closed (raises) rather than guessing from a broad date pattern.
+_AUTHORITATIVE_BULLET_ANCHOR = "whose own cascade record lists them):"
+_C1_RESTATEMENT_ANCHOR = "doubt they are"
+_BACKTICK_DATE_LIST_RE = re.compile(
+    r"`(\d{4}-\d{2}-\d{2}(?:,\s*\d{4}-\d{2}-\d{2})*)`"
+)
+
+
+def extract_j11_contract_text(goal_md_text: str) -> str:
+    """The literal J-11 journey section (steps 1-14 plus the OWNER AUTHORIZATION block), sliced out of
+    the full `docs/goal.md` text between two literal anchors. Fails closed (`ValueError`) if either
+    boundary cannot be found exactly -- never hashes a partial or guessed slice."""
+    start = goal_md_text.find(_J11_SECTION_START)
+    if start == -1:
+        raise ValueError(f"J-11 section start anchor not found: {_J11_SECTION_START!r}")
+    end = goal_md_text.find(_J11_SECTION_END, start)
+    if end == -1 or end <= start:
+        raise ValueError(f"J-11 section end anchor not found after start: {_J11_SECTION_END!r}")
+    return goal_md_text[start:end]
+
+
+def compute_contract_hash(goal_md_text: str) -> str:
+    """sha256 hex digest of the extracted J-11 contract section text (UTF-8 bytes, verbatim)."""
+    section = extract_j11_contract_text(goal_md_text)
+    return hashlib.sha256(section.encode("utf-8")).hexdigest()
+
+
+def _next_backtick_date_list(section_text: str, anchor: str) -> list[str]:
+    idx = section_text.find(anchor)
+    if idx == -1:
+        raise ValueError(f"anchor text not found: {anchor!r}")
+    match = _BACKTICK_DATE_LIST_RE.search(section_text, idx)
+    if match is None:
+        raise ValueError(f"no backtick-quoted comma-separated date list found after anchor: {anchor!r}")
+    return [item.strip() for item in match.group(1).split(",")]
+
+
+def extract_incident_date_lists(goal_md_text: str) -> dict:
+    """The two independently-authored 11-date lists in the J-11 contract text: the authoritative "the
+    incident date set -- all 11" bullet, and the OWNER AUTHORIZATION block's C1 restatement. Raises
+    (fails closed) if the J-11 section or either anchor cannot be located."""
+    section = extract_j11_contract_text(goal_md_text)
+    return {
+        "authoritative_bullet_dates": _next_backtick_date_list(section, _AUTHORITATIVE_BULLET_ANCHOR),
+        "c1_restatement_dates": _next_backtick_date_list(section, _C1_RESTATEMENT_ANCHOR),
+    }
+
+
+def check_c1_date_set_boundary(goal_md_text: str, incident_dates: tuple = INCIDENT_DATES) -> dict:
+    """TC-3: the C1 date-set boundary check. Byte-identity of THREE things: the code's own
+    `INCIDENT_DATES` (as ISO strings), the authoritative "incident date set -- all 11" bullet, and the C1
+    restatement. If the two goal.md lists disagree with each other, or either cannot be located, `ok` is
+    False and the caller MUST stop before any deletion -- never reconciled by silently preferring one."""
+    code_dates = [d.isoformat() for d in incident_dates]
+    try:
+        lists = extract_incident_date_lists(goal_md_text)
+    except ValueError as exc:
+        return {
+            "ok": False,
+            "extraction_error": str(exc),
+            "code_dates": code_dates,
+        }
+    bullet = lists["authoritative_bullet_dates"]
+    restatement = lists["c1_restatement_dates"]
+    lists_agree = bullet == restatement
+    code_matches_goal_md_lists = bullet == code_dates and restatement == code_dates
+    return {
+        "ok": lists_agree and code_matches_goal_md_lists,
+        "authoritative_bullet_dates": bullet,
+        "c1_restatement_dates": restatement,
+        "code_dates": code_dates,
+        "lists_agree": lists_agree,
+        "code_matches_goal_md_lists": code_matches_goal_md_lists,
+    }
+
+
+# ----------------------------------------------------------------------------------------------
+# C2 -- Stage C attempt identity + fresh preflight capture
+# ----------------------------------------------------------------------------------------------
+
+
+def freeze_stage_c_attempt_identity(session: Session, config: Optional[Config] = None) -> dict:
+    """A NEW Stage C bookkeeping attempt id/timestamp, layered ON TOP OF -- never replacing -- the
+    existing Stage B2 `engine_identity` (logged assumption #2,
+    `runs/goal-session-market-compass/state/assumptions.md` iter-13 entry). Re-derives the B2 identity
+    fresh via `j11_maintenance.freeze_attempt_identity` rather than trusting a prior certified value."""
+    b2_identity = j11_maintenance.freeze_attempt_identity(session, config)
+    return {
+        "stage_c_attempt_frozen_at": datetime.now(timezone.utc).isoformat(),
+        "b2_engine_identity": b2_identity,
+    }
+
+
+def capture_stage_c_preflight(
+    session: Session,
+    engine: Engine,
+    db_path: Optional[Path],
+    *,
+    goal_md_text: str,
+    git_head: Optional[str],
+    config: Optional[Config] = None,
+) -> dict:
+    """Ruling C2's fresh Stage C preflight -- re-derives live state fresh (never trusting iteration
+    10/11/12's certified figures), composed entirely from already-existing read-only primitives. Writes
+    nothing. `goal_md_text`/`git_head` are injected by the caller (this function performs no file/git I/O
+    itself) so the whole capture stays a pure, fixture-testable composition."""
+    pre_reset_inventory = j11_maintenance.capture_pre_reset_inventory(session)
+    stage_c_attempt_identity = freeze_stage_c_attempt_identity(session, config)
+    manifest_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
+    manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
+    full_db_snapshot = migration.capture_full_db_snapshot(engine, db_path)
+    c1_check = check_c1_date_set_boundary(goal_md_text)
+    return {
+        "captured_at": datetime.now(timezone.utc).isoformat(),
+        "git_head": git_head,
+        "goal_md_j11_contract_hash": compute_contract_hash(goal_md_text),
+        "c1_date_set_boundary_check": c1_check,
+        "stage_c_attempt_identity": stage_c_attempt_identity,
+        "pre_reset_inventory": pre_reset_inventory,
+        "manifest_ddl": manifest_ddl,
+        "manifest_dump": manifest_dump,
+        "manifest_row_count": len(manifest_dump),
+        "full_db_snapshot": full_db_snapshot,
+    }
+
+
+def load_certified_state(path: Path) -> dict:
+    """Loads a prior iteration's persisted fingerprint artifact (shape:
+    `{full_db_snapshot, manifest_ddl, manifest_dump, manifest_row_count, pre_reset_inventory}`) as the
+    certified-state baseline the fresh preflight is compared against (ruling C2). The default caller
+    (the CLI script) points this at
+    `runs/goal-market-compass-iter-12/j11-stage-b1-cleanup-fingerprint-after.json` -- iteration 12's own
+    diff artifact already proves that file `identical_except_capture_timestamps` against iteration 12's
+    own before-capture, which is itself proven byte-identical to iteration 11's post-migration state."""
+    return json.loads(path.read_text())
+
+
+def compare_preflight_to_certified(preflight: dict, certified: dict) -> dict:
+    """TC-1/TC-2: the preflight comparison gate. Every B/B1/B2 invariant re-checked against the supplied
+    certified state: 24 manifest rows; no live FK on `source_run_id`; the manifest DDL/index set
+    unchanged (the four owner-accepted residuals included, since they are already baked into the
+    certified DDL text -- this checks for NO FURTHER drift, not a return to the pre-iter-11 shape);
+    `source_run_id` provenance values unchanged; every manifest column value unchanged (a full row/column
+    diff, never an aggregate-only check); `daily_prices`/`data_provider_runs`/`watchlist` counts
+    unchanged; the C1 date-set boundary check passing; and the per-incident-date `ScannerRun` inventory
+    unchanged. ANY False in `checks` means `material_mismatch` is True and the caller MUST stop before
+    the first destructive statement."""
+    checks: dict[str, Any] = {}
+
+    fresh_ddl_sql = preflight["manifest_ddl"]["table_sql"] or ""
+    certified_ddl_sql = certified["manifest_ddl"]["table_sql"] or ""
+    # the manifest row count must match the CERTIFIED baseline exactly (dynamic equality -- never a
+    # hardcoded literal here, so this function stays correct if a later iteration's certified baseline
+    # legitimately differs from today's 24; the CLI script separately sanity-checks that the specific
+    # baseline file it loaded for THIS iteration is the expected 24-row iteration-12 certification).
+    checks["manifest_row_count_matches_certified"] = preflight["manifest_row_count"] == certified["manifest_row_count"]
+    checks["no_live_fk_on_source_run_id"] = "FOREIGN KEY" not in fresh_ddl_sql
+    checks["manifest_ddl_unchanged_from_certified"] = fresh_ddl_sql == certified_ddl_sql
+    checks["manifest_indexes_unchanged"] = (
+        sorted(preflight["manifest_ddl"]["index_names"]) == sorted(certified["manifest_ddl"]["index_names"])
+        and sorted(preflight["manifest_ddl"]["index_sqls"]) == sorted(certified["manifest_ddl"]["index_sqls"])
+    )
+
+    manifest_dump_diff = migration.diff_dumps(certified["manifest_dump"], preflight["manifest_dump"])
+    checks["manifest_values_unchanged"] = manifest_dump_diff["equal"]
+
+    certified_source_ids = {row["id"]: row["source_run_id"] for row in certified["manifest_dump"]}
+    fresh_source_ids = {row["id"]: row["source_run_id"] for row in preflight["manifest_dump"]}
+    checks["source_run_id_values_unchanged"] = certified_source_ids == fresh_source_ids
+
+    checks["daily_prices_fingerprint_unchanged"] = (
+        preflight["pre_reset_inventory"]["daily_prices"]["fingerprint"]
+        == certified["pre_reset_inventory"]["daily_prices"]["fingerprint"]
+    )
+    checks["data_provider_runs_count_unchanged"] = (
+        preflight["pre_reset_inventory"]["data_provider_runs_count"]
+        == certified["pre_reset_inventory"]["data_provider_runs_count"]
+    )
+    checks["watchlist_count_unchanged"] = (
+        preflight["pre_reset_inventory"]["watchlist_count"]
+        == certified["pre_reset_inventory"]["watchlist_count"]
+    )
+    checks["c1_date_set_boundary_ok"] = bool(preflight["c1_date_set_boundary_check"]["ok"])
+
+    fresh_per_date = preflight["pre_reset_inventory"]["per_date"]
+    certified_per_date = certified["pre_reset_inventory"]["per_date"]
+    per_date_mismatches: list[dict] = []
+    for key, fresh_row in fresh_per_date.items():
+        certified_row = certified_per_date.get(key, {})
+        fresh_run = fresh_row.get("scanner_run", {})
+        certified_run = certified_row.get("scanner_run", {})
+        if (
+            fresh_run.get("present") != certified_run.get("present")
+            or fresh_run.get("run_id") != certified_run.get("run_id")
+            or fresh_run.get("created_at") != certified_run.get("created_at")
+        ):
+            per_date_mismatches.append({"date": key, "fresh": fresh_run, "certified": certified_run})
+    checks["per_date_scanner_run_inventory_unchanged"] = not per_date_mismatches
+
+    all_invariants_hold = all(bool(v) for v in checks.values())
+    return {
+        "generated_at": datetime.now(timezone.utc).isoformat(),
+        "checks": checks,
+        "per_date_scanner_run_mismatches": per_date_mismatches,
+        "manifest_dump_diff": manifest_dump_diff,
+        "all_invariants_hold": all_invariants_hold,
+        "material_mismatch": not all_invariants_hold,
+    }
+
+
+# ----------------------------------------------------------------------------------------------
+# C9 -- the intended-delete-set, captured and persisted BEFORE any DELETE statement executes
+# ----------------------------------------------------------------------------------------------
+
+
+def capture_intended_delete_set(session: Session, exact_date_set) -> dict:
+    """Ruling C9: BEFORE any DELETE, the exact row-id set to be removed, per table, for each
+    currently-run-bearing incident date, plus every associated child row's id. Column-projected `id`
+    SELECTs only (AG-8) -- never a full-row hydration. This is the pre-declared plan the post-hoc
+    actual-delete evidence (`clear_snapshot_dates`'s own return value) is checked against."""
+    per_date: dict[str, dict] = {}
+    totals: dict[str, list[int]] = {
+        "scanner_runs": [], "forward_returns": [], "scanner_results": [], "sector_scores": [], "theme_scores": [],
+    }
+    for one_date in exact_date_set:
+        key = one_date.isoformat()
+        run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == one_date)).first()
+        if run is None:
+            per_date[key] = {
+                "run_id": None,
+                "ids": {"scanner_runs": [], "forward_returns": [], "scanner_results": [], "sector_scores": [], "theme_scores": []},
+            }
+            continue
+        run_id = run.id
+        ids: dict[str, list[int]] = {"scanner_runs": [run_id]}
+        for table_name, model in _CHILD_MODELS.items():
+            rows = session.exec(select(model.id).where(model.run_id == run_id)).all()
+            ids[table_name] = sorted(int(r) for r in rows)
+        per_date[key] = {"run_id": run_id, "ids": ids}
+        for table_name, id_list in ids.items():
+            totals[table_name].extend(id_list)
+    sorted_totals = {table_name: sorted(id_list) for table_name, id_list in totals.items()}
+    return {
+        "captured_at": datetime.now(timezone.utc).isoformat(),
+        "per_date": per_date,
+        "totals": sorted_totals,
+        "total_counts": {table_name: len(id_list) for table_name, id_list in sorted_totals.items()},
+        "deleted_run_ids": sorted(int(rid) for rid in sorted_totals["scanner_runs"]),
+    }
+
+
+# ----------------------------------------------------------------------------------------------
+# Post-delete mutation accounting
+# ----------------------------------------------------------------------------------------------
+
+
+def _population_fingerprint(session: Session, agg_column, filter_column, exclude_values: list[int]) -> dict:
+    """Cheap SQL-side aggregate fingerprint (count, min id, max id, id sum -> sha256) of every row whose
+    `filter_column` is NOT in `exclude_values` -- see the module docstring for why this suffices in place
+    of a full millions-of-ids Python diff."""
+    stmt = select(func.count(agg_column), func.min(agg_column), func.max(agg_column), func.sum(agg_column))
+    if exclude_values:
+        stmt = stmt.where(~filter_column.in_(exclude_values))
+    row = session.exec(stmt).one()
+    count, min_id, max_id, id_sum = row
+    payload = {
+        "count": int(count or 0),
+        "min_id": int(min_id) if min_id is not None else None,
... [diff_bound] apps/backend/app/engine/j11_stage_c.py: 241 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/scripts/run_j11_stage_c_bounded_clear.py b/apps/backend/scripts/run_j11_stage_c_bounded_clear.py
new file mode 100644
index 00000000..54827076
--- /dev/null
+++ b/apps/backend/scripts/run_j11_stage_c_bounded_clear.py
@@ -0,0 +1,253 @@
+"""goal-market-compass iter-13 -- J-11 Stage C: the ONE owner-authorized bounded destructive clear of
+the 11 incident dates' Layer-2 derived state (docs/goal.md J-11 step 11's "## OWNER AUTHORIZATION --
+J-11 Stage C (owner, 2026-08-24)" block, rulings C1-C12).
+
+Mirrors `run_j11_stage_b1_manifest_schema_migration.py`'s idiom exactly: NO database interaction of any
+kind, not even a read, without `--confirm`; evidence is persisted at every checkpoint BEFORE the
+destructive step so a mid-run crash still leaves a forensic trail; the completion marker is written ONLY
+after every verification check passes (ruling C9). Sequence, exactly as ruling C10/step 11's own
+ordering requires: fresh preflight (C2) -> preflight comparison gate against iteration 12's certified
+state (TC-2) -> C1 date-set boundary check (TC-3) -> intended-delete-set capture (C9, BEFORE any DELETE)
+-> `clear_snapshot_dates` (the ONE authorized write) -> post-delete mutation accounting (TC-7..TC-12) ->
+completion marker (TC-13). ANY failure at ANY stage before the delete STOPS before the first destructive
+statement; ANY failure AFTER the delete still writes no marker, exits non-zero, and preserves every
+artifact already captured -- Stage C never claims completion it cannot prove (ruling C9/step 13).
+
+This is the ONE authorized live write anywhere in goal-market-compass iter-13 (ruling C10: "Stage C
+stands alone, and STOPS" -- no Stage D/E/F/G work follows in this process). One controlled writer, no
+boot warmup racing it (maintenance isolation stays active this whole iteration), no network call
+anywhere in this process, never a raw file copy of the 7.8+ GB database.
+
+Usage:
+    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_c_bounded_clear.py \\
+        --confirm \\
+        [--evidence-dir runs/goal-market-compass-iter-13] \\
+        [--certified-state-path runs/goal-market-compass-iter-12/j11-stage-b1-cleanup-fingerprint-after.json]
+
+Without `--confirm`, the script performs NO database interaction at all (not even a read) and exits
+non-zero.
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
+from sqlmodel import Session  # noqa: E402
+
+from app.config import load_config  # noqa: E402
+from app.db import get_engine, resolve_database_url  # noqa: E402
+from app.engine import j11_stage_c as jsc  # noqa: E402
+from app.engine.data_manager import clear_snapshot_dates  # noqa: E402
+from app.engine.j11_maintenance import INCIDENT_DATES, capture_pre_reset_inventory  # noqa: E402
+from app.engine import j11_schema_migration as migration  # noqa: E402
+from app.models import DataProviderRun, NextSessionManifest, Watchlist  # noqa: E402
+
+DEFAULT_EVIDENCE_DIR = REPO_ROOT / "runs" / "goal-market-compass-iter-13"
+DEFAULT_CERTIFIED_STATE_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-12" / "j11-stage-b1-cleanup-fingerprint-after.json"
+)
+EXPECTED_CERTIFIED_MANIFEST_ROW_COUNT = 24  # sanity check on WHICH baseline file was loaded, not a gate
+
+
+def _db_file_path(database_url: str) -> "Path | None":
+    prefix = "sqlite:///"
+    if not database_url.startswith(prefix):
+        return None
+    raw = database_url[len(prefix):]
+    if not raw or raw == ":memory:":
+        return None
+    path = Path(raw)
+    return path if path.is_absolute() else (REPO_ROOT / raw)
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
+    parser.add_argument("--certified-state-path", type=Path, default=DEFAULT_CERTIFIED_STATE_PATH)
+    parser.add_argument(
+        "--confirm", action="store_true",
+        help="required -- without it, the script touches the database not at all and exits non-zero.",
+    )
+    args = parser.parse_args()
+
+    if not args.confirm:
+        print(
+            "refusing to run without --confirm (this is the ONE owner-authorized bounded destructive "
+            "write this iteration -- docs/goal.md J-11 step 11 OWNER AUTHORIZATION block). No database "
+            "interaction, not even a read, has occurred.",
+            file=sys.stderr,
+        )
+        return 2
+
+    evidence_dir: Path = args.evidence_dir
+
+    cfg = load_config()
+    resolved_url = resolve_database_url(cfg.database.url)
+    db_path = _db_file_path(resolved_url)
+    print(f"database: {resolved_url}", file=sys.stderr)
+
+    # --- TRUE process start: the db file + WAL sidecar fingerprint, before anything else touches it ---
+    db_file_true_start = jsc.db_file_fingerprint(db_path)
+    _write_json(evidence_dir / "j11-stage-c-db-file-true-start.json", db_file_true_start)
+
+    engine = get_engine()  # the SAME pooled writable engine the real backend uses -- never a raw file
+    # copy, never create_db_and_tables()/metadata.create_all() (out of scope under this authorization).
+
+    goal_md_text = jsc.read_goal_md_text()
+    git_head = jsc.read_git_head()
+
+    # --- C2: fresh Stage C preflight, persisted BEFORE any gate decision -------------------------------
+    with Session(engine) as session:
+        preflight = jsc.capture_stage_c_preflight(
+            session, engine, db_path, goal_md_text=goal_md_text, git_head=git_head, config=cfg,
+        )
+    _write_json(evidence_dir / "j11-stage-c-preflight.json", preflight)
+    print(
+        f"preflight captured: manifest_row_count={preflight['manifest_row_count']} "
+        f"c1_ok={preflight['c1_date_set_boundary_check']['ok']} git_head={git_head}",
+        file=sys.stderr,
+    )
+
+    # --- TC-2: the preflight comparison gate against iteration 12's certified state --------------------
+    certified = jsc.load_certified_state(args.certified_state_path)
+    if certified.get("manifest_row_count") != EXPECTED_CERTIFIED_MANIFEST_ROW_COUNT:
+        print(
+            f"FAIL: the loaded certified-state baseline ({args.certified_state_path}) does not carry the "
+            f"expected {EXPECTED_CERTIFIED_MANIFEST_ROW_COUNT} manifest rows "
+            f"(found {certified.get('manifest_row_count')!r}) -- wrong baseline file, refusing to compare "
+            "against it. No DELETE statement has executed.",
+            file=sys.stderr,
+        )
+        return 1
+
+    gate = jsc.compare_preflight_to_certified(preflight, certified)
+    _write_json(evidence_dir / "j11-stage-c-preflight-comparison-gate.json", gate)
+    print(f"preflight comparison gate: all_invariants_hold={gate['all_invariants_hold']}", file=sys.stderr)
+
+    verdict = jsc.stage_c_overall_verdict(gate, mutation_accounting=None)
+    if not gate["all_invariants_hold"]:
+        print(
+            "STOP: the preflight comparison gate found a material mismatch against the certified "
+            "iteration-12 state (or a B/B1/B2 invariant no longer holds). No DELETE statement has "
+            "executed. See j11-stage-c-preflight-comparison-gate.json for the failing checks.",
+            file=sys.stderr,
+        )
+        return 1
+
+    # --- TC-3: the C1 date-set boundary check (already computed inside the preflight; re-asserted here
+    # as its own explicit stop point, per the spec's own numbered step ordering) -------------------------
+    if not preflight["c1_date_set_boundary_check"]["ok"]:
+        print(
+            "STOP: the C1 date-set boundary check failed -- the code's INCIDENT_DATES list disagrees "
+            "with one or both of docs/goal.md's own 11-date lists, or an anchor could not be located. "
+            "No DELETE statement has executed.",
+            file=sys.stderr,
+        )
+        return 1
+
+    # --- C9: the intended delete set, captured and persisted BEFORE any DELETE statement executes -------
+    with Session(engine) as session:
+        intended_delete_set = jsc.capture_intended_delete_set(session, INCIDENT_DATES)
+    _write_json(evidence_dir / "j11-stage-c-intended-delete-set.json", intended_delete_set)
+    deleted_run_ids = intended_delete_set["deleted_run_ids"]
+    print(
+        f"intended delete set: {intended_delete_set['total_counts']} deleted_run_ids={deleted_run_ids}",
+        file=sys.stderr,
+    )
+
+    # --- pre-delete mutation-accounting inputs, captured immediately before the destructive call --------
+    with Session(engine) as session:
+        pre_layer2_population = jsc.capture_layer2_population_fingerprints(session, deleted_run_ids)
+        pre_incident_scoped = jsc.incident_scoped_counts(session, deleted_run_ids)
+        pre_daily_prices = capture_pre_reset_inventory(session)["daily_prices"]
+        pre_manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
+        pre_provider_runs = jsc.small_table_id_snapshot(session, DataProviderRun)
+        pre_watchlist = jsc.small_table_id_snapshot(session, Watchlist)
+    pre_full_db_snapshot = migration.capture_full_db_snapshot(engine, db_path)
+
+    # --- THE ONE AUTHORIZED DESTRUCTIVE WRITE -------------------------------------------------------
+    with Session(engine) as session:
+        clear_result = clear_snapshot_dates(session, INCIDENT_DATES)
+    print(f"clear_snapshot_dates totals: {clear_result['totals']}", file=sys.stderr)
+
+    # --- post-delete mutation-accounting inputs -----------------------------------------------------
+    with Session(engine) as session:
+        post_layer2_population = jsc.capture_layer2_population_fingerprints(session, deleted_run_ids)
+        post_incident_scoped = jsc.incident_scoped_counts(session, deleted_run_ids)
+        post_daily_prices = capture_pre_reset_inventory(session)["daily_prices"]
+        post_manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
+        post_provider_runs = jsc.small_table_id_snapshot(session, DataProviderRun)
+        post_watchlist = jsc.small_table_id_snapshot(session, Watchlist)
+    post_full_db_snapshot = migration.capture_full_db_snapshot(engine, db_path)
+
+    # --- TRUE process end: the db file + WAL sidecar fingerprint, captured last ------------------------
+    db_file_true_end = jsc.db_file_fingerprint(db_path)
+    _write_json(evidence_dir / "j11-stage-c-db-file-true-end.json", db_file_true_end)
+
+    mutation_accounting = jsc.build_mutation_accounting(
+        pre_layer2_population=pre_layer2_population,
+        post_layer2_population=post_layer2_population,
+        pre_full_db_snapshot=pre_full_db_snapshot,
+        post_full_db_snapshot=post_full_db_snapshot,
+        pre_daily_prices=pre_daily_prices,
+        post_daily_prices=post_daily_prices,
+        pre_manifest_dump=pre_manifest_dump,
+        post_manifest_dump=post_manifest_dump,
+        pre_provider_runs=pre_provider_runs,
+        post_provider_runs=post_provider_runs,
+        pre_watchlist=pre_watchlist,
+        post_watchlist=post_watchlist,
+        pre_incident_scoped_counts=pre_incident_scoped,
+        post_incident_scoped_counts=post_incident_scoped,
+        intended_delete_set=intended_delete_set,
+        clear_result=clear_result,
+        db_file_true_start=db_file_true_start,
+        db_file_true_end=db_file_true_end,
+    )
+    _write_json(evidence_dir / "j11-stage-c-mutation-accounting.json", mutation_accounting)
+    print(f"mutation accounting: all_checks_pass={mutation_accounting['all_checks_pass']}", file=sys.stderr)
+    if not mutation_accounting["all_checks_pass"]:
+        failing = [k for k, v in mutation_accounting["checks"].items() if not v]
+        print(f"FAILING CHECKS: {failing}", file=sys.stderr)
+
+    final_verdict = jsc.stage_c_overall_verdict(gate, mutation_accounting)
+    if not final_verdict["passed"]:
+        print(
+            f"STAGE C DID NOT VERIFY (reason={final_verdict['reason']!r}). The delete already executed "
+            "and cannot be undone by this script (no transaction spans the whole batch -- see docs/"
+            "goal.md J-11 step 14). No completion marker is written. All captured evidence is preserved "
+            "for owner review. Do NOT continue toward Stage D.",
+            file=sys.stderr,
+        )
+        return 1
+
+    prior_timestamps = [
+        preflight["captured_at"], gate["generated_at"], intended_delete_set["captured_at"],
+        mutation_accounting["generated_at"],
+    ]
+    marker = jsc.build_completion_marker(final_verdict, prior_timestamps)
+    _write_json(evidence_dir / "j11-stage-c-complete.json", marker)
+
+    print(
+        f"J-11 STAGE C COMPLETE: YES (completed_at={marker['completed_at']})",
+        file=sys.stderr,
+    )
+    print("J-11 STAGE D AUTHORIZED: NO", file=sys.stderr)
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/tests/test_j11_stage_c_bounded_clear.py b/apps/backend/tests/test_j11_stage_c_bounded_clear.py
new file mode 100644
index 00000000..8bfea9e2
--- /dev/null
+++ b/apps/backend/tests/test_j11_stage_c_bounded_clear.py
@@ -0,0 +1,243 @@
+"""goal-market-compass iter-13 -- J-11 Stage C bounded-clear tests (TC-4, TC-5, TC-6).
+
+File-scoped, fixture-DB-only (fresh `sqlite://` engine, `SQLModel.metadata.create_all`, hand-built rows)
+-- the SAME pattern `test_j11_maintenance.py` uses, never `loaded_engine` and never
+`apps/backend/data/trendora.db` (docs/goal.md: "NEVER copy, move, or open-for-write trendora.db"; the
+resource contract this whole session runs under).
+"""
+from __future__ import annotations
+
+import json
+from datetime import date, datetime, timezone
+from unittest import mock
+
+import pytest
+from sqlalchemy import event
+from sqlmodel import Session, SQLModel, create_engine
+
+from app.engine import compass, scanner
+from app.engine.data_manager import clear_snapshot_dates
+from app.engine.j11_maintenance import INCIDENT_DATES
+from app.models import (
+    DailyPrice,
+    ForwardReturn,
+    NextSessionManifest,
+    ScannerResult,
+    ScannerRun,
+    SectorScoreRow,
+    ThemeScoreRow,
+)
+
+
+@pytest.fixture()
+def engine():
+    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
+
+    @event.listens_for(eng, "connect")
+    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
+        cursor = dbapi_connection.cursor()
+        cursor.execute("PRAGMA foreign_keys=ON")
+        cursor.close()
+
+    SQLModel.metadata.create_all(eng)
+    return eng
+
+
+def _mk_run(session: Session, asof: date, *, created_at: datetime | None = None) -> ScannerRun:
+    run = ScannerRun(
+        asof_date=asof,
+        created_at=created_at or datetime.now(timezone.utc),
+        provider="seed",
+        benchmark="SPY",
+        regime_score=55.0,
+        regime_label="Expansion",
+        regime_components_json="[]",
+        breadth_above_50dma=50.0,
+        breadth_above_200dma=55.0,
+        new_high_low_json="{}",
+        candidate_counts_json="{}",
+    )
+    session.add(run)
+    session.flush()
+    return run
+
+
+def _mk_children(session: Session, run: ScannerRun, *, n: int = 2) -> dict:
+    """Inserts `n` rows into each of the four Layer-2 child tables owned by `run` and returns their ids."""
+    ids: dict[str, list[int]] = {"scanner_results": [], "sector_scores": [], "theme_scores": [], "forward_returns": []}
+    for i in range(n):
+        result = ScannerResult(
+            run_id=run.id, ticker=f"T{run.id}{i}", name="Test Co", leadership_score=50.0,
+            leadership_bucket="C", entry_quality_score=50.0, entry_quality_bucket="C",
+            risk_score=50.0, risk_bucket="C", setup_status="none", rank=i + 1, record_json="{}",
+        )
+        session.add(result)
+        sector = SectorScoreRow(
+            run_id=run.id, ticker=f"XL{run.id}{i}", kind="sector", name="Test Sector",
+            score=50.0, bucket="C", trend_label="flat", components_json="{}", rank=i + 1,
+        )
+        session.add(sector)
+        theme = ThemeScoreRow(
+            run_id=run.id, slug=f"theme-{run.id}-{i}", name="Test Theme", score=50.0, bucket="C",
+            members_json="[]", breadth_label="flat", trend_label="flat", components_json="{}", rank=i + 1,
+        )
+        session.add(theme)
+        fwd = ForwardReturn(
+            run_id=run.id, symbol=f"T{run.id}{i}", horizon=5, asof_date=run.asof_date,
+            entry_close=100.0, measured_date=run.asof_date, realized_return=0.01,
+        )
+        session.add(fwd)
+        session.flush()
+        ids["scanner_results"].append(result.id)
+        ids["sector_scores"].append(sector.id)
+        ids["theme_scores"].append(theme.id)
+        ids["forward_returns"].append(fwd.id)
+    return ids
+
+
+def _mk_prices(session: Session, n: int = 5) -> int:
+    for i in range(n):
+        session.add(
+            DailyPrice(
+                symbol="SPY", date=date(2020, 1, 1 + i), open=1.0, high=1.0, low=1.0, close=1.0, volume=100,
+            )
+        )
+    session.flush()
+    return n
+
+
+# --- TC-4: bounded-date deletion at the id level; non-incident rows survive with identical ids --------
+
+
+def test_tc4_bounded_deletion_only_incident_dates_touched_non_incident_ids_survive(engine):
+    with Session(engine) as session:
+        bars_before = _mk_prices(session, 7)
+
+        incident_run_a = _mk_run(session, INCIDENT_DATES[0])  # 2026-05-12
+        incident_ids_a = _mk_children(session, incident_run_a, n=2)
+        incident_run_b = _mk_run(session, INCIDENT_DATES[-1])  # 2026-08-12
+        incident_ids_b = _mk_children(session, incident_run_b, n=3)
+
+        non_incident_date = date(2026, 8, 15)
+        assert non_incident_date not in INCIDENT_DATES
+        non_incident_run = _mk_run(session, non_incident_date)
+        non_incident_ids = _mk_children(session, non_incident_run, n=2)
+        session.commit()
+
+        non_incident_run_id = non_incident_run.id
+
+        result = clear_snapshot_dates(session, INCIDENT_DATES)
+
+        # the two incident-date runs and every one of their children are gone.
+        assert session.get(ScannerRun, incident_run_a.id) is None
+        assert session.get(ScannerRun, incident_run_b.id) is None
+        for model, ids_a, ids_b in (
+            (ScannerResult, incident_ids_a["scanner_results"], incident_ids_b["scanner_results"]),
+            (SectorScoreRow, incident_ids_a["sector_scores"], incident_ids_b["sector_scores"]),
+            (ThemeScoreRow, incident_ids_a["theme_scores"], incident_ids_b["theme_scores"]),
+            (ForwardReturn, incident_ids_a["forward_returns"], incident_ids_b["forward_returns"]),
+        ):
+            for row_id in ids_a + ids_b:
+                assert session.get(model, row_id) is None
+
+        # the non-incident-date run and every one of its children survive with their EXACT original ids.
+        assert session.get(ScannerRun, non_incident_run_id) is not None
+        for model, ids in (
+            (ScannerResult, non_incident_ids["scanner_results"]),
+            (SectorScoreRow, non_incident_ids["sector_scores"]),
+            (ThemeScoreRow, non_incident_ids["theme_scores"]),
+            (ForwardReturn, non_incident_ids["forward_returns"]),
+        ):
+            for row_id in ids:
+                assert session.get(model, row_id) is not None
+
+        # daily_prices invariant: identical row count before/after, table never referenced by a DELETE.
+        assert result["bars_before"] == bars_before
+        assert result["bars_after"] == bars_before
+
+        # totals reconcile with the two incident runs' own child counts.
+        assert result["totals"]["scanner_runs"] == 2
+        assert result["totals"]["scanner_results"] == 5  # 2 + 3
+        assert result["totals"]["sector_scores"] == 5
+        assert result["totals"]["theme_scores"] == 5
+        assert result["totals"]["forward_returns"] == 5
+
+
+# --- TC-5: a date with no existing ScannerRun is a documented no-op, never an error --------------------
+
+
+def test_tc5_no_op_on_absent_run_never_raises(engine):
+    with Session(engine) as session:
+        _mk_prices(session, 3)
+        # only ONE incident date carries a run; the other 10 have none.
+        run = _mk_run(session, INCIDENT_DATES[0])
+        _mk_children(session, run, n=1)
+        session.commit()
+
+        result = clear_snapshot_dates(session, INCIDENT_DATES)  # must not raise
+
+        for one_date in INCIDENT_DATES[1:]:
+            key = one_date.isoformat()
+            assert result["per_date"][key]["run_id"] is None
+            assert result["per_date"][key]["deleted"] == {
+                "scanner_runs": 0, "forward_returns": 0, "scanner_results": 0,
+                "sector_scores": 0, "theme_scores": 0,
+            }
+
+        key0 = INCIDENT_DATES[0].isoformat()
+        assert result["per_date"][key0]["run_id"] == run.id
+        assert result["per_date"][key0]["deleted"]["scanner_runs"] == 1
+
+
+# --- TC-6: never calls get_or_create_manifest / run_scan / persist_run_payload; manifest byte-unchanged
+
+
+def test_tc6_never_calls_manifest_or_scan_paths_manifest_row_byte_unchanged(engine):
+    with Session(engine) as session:
+        _mk_prices(session, 2)
+        run = _mk_run(session, INCIDENT_DATES[0])
+        _mk_children(session, run, n=1)
+
+        # a manifest referencing the soon-to-be-deleted run -- the exact FK-orphaning scenario Stage C
+        # must leave completely untouched (never "repaired", never rebound, never regenerated).
+        manifest = NextSessionManifest(
+            as_of=run.asof_date,
+            version=1,
+            source_run_id=run.id,
+            session_delta_json="{}",
+            narrative_json="{}",
+            selection_json="{}",
+            content_hash="stub-content-hash",
+            created_at=datetime.now(timezone.utc),
+            mode="at_ingest",
+            frozen=True,
+            generation_json=json.dumps({"producer": "ingest_finalize", "source_run_created_at": compass._utc_isoformat(run.created_at)}),
+            manifest_hash="stub-manifest-hash",
+            prospective_eligible=True,
+        )
+        session.add(manifest)
+        session.commit()
+
+        manifest_before = json.loads(json.dumps({c: getattr(manifest, c) for c in manifest.__class__.model_fields}, default=str))
+
+        with (
+            mock.patch.object(compass, "get_or_create_manifest") as mock_get_or_create,
+            mock.patch.object(scanner, "run_scan") as mock_run_scan,
+            mock.patch.object(scanner, "persist_run_payload") as mock_persist,
+        ):
+            clear_snapshot_dates(session, INCIDENT_DATES)
+
+        mock_get_or_create.assert_not_called()
+        mock_run_scan.assert_not_called()
+        mock_persist.assert_not_called()
+
+        # the manifest row itself: still present, every column byte-unchanged (never UPDATEd/"repaired").
+        session.expire_all()
+        refreshed = session.get(NextSessionManifest, manifest.id)
+        assert refreshed is not None
+        manifest_after = json.loads(json.dumps({c: getattr(refreshed, c) for c in refreshed.__class__.model_fields}, default=str))
+        assert manifest_after == manifest_before
+
+        # and its source_run_id is now a genuine orphan (the run it pointed to is gone) -- proof this
+        # scenario was actually exercised, not accidentally skipped.
+        assert session.get(ScannerRun, manifest.source_run_id) is None
diff --git a/apps/backend/tests/test_j11_stage_c_preflight.py b/apps/backend/tests/test_j11_stage_c_preflight.py
new file mode 100644
index 00000000..9a38c9bc
--- /dev/null
+++ b/apps/backend/tests/test_j11_stage_c_preflight.py
@@ -0,0 +1,224 @@
+"""goal-market-compass iter-13 -- J-11 Stage C preflight/gate/completion-marker tests (TC-1, TC-2, TC-3,
+TC-13).
+
+File-scoped, fixture-DB-only (fresh `sqlite://` engine, `SQLModel.metadata.create_all`) plus pure-dict
+unit tests for the comparison gate / C1 check / completion-marker helpers -- never
+`apps/backend/data/trendora.db`.
+"""
+from __future__ import annotations
+
+import copy
+from datetime import datetime, timedelta, timezone
+
+import pytest
+from sqlalchemy import event
+from sqlmodel import Session, SQLModel, create_engine
+
+from app.config import load_config
+from app.engine import j11_stage_c as jsc
+from app.engine.j11_maintenance import INCIDENT_DATES
+
+# A minimal but well-formed synthetic goal.md excerpt reproducing the J-11 section's two literal anchors
+# and both 11-date lists, standing in for the real (much larger) `docs/goal.md` file. Kept structurally
+# identical to the real anchors so the extraction functions are exercised exactly as they run live.
+_MATCHING_DATES = ", ".join(d.isoformat() for d in INCIDENT_DATES)
+_GOAL_MD_MATCHING = f"""
+# Project Goal
+
+- **J-10: some other journey** — passing
+
+- **J-11: Incident-bounded clean regeneration of derived state (owner, 2026-08-21)**
+  - **The incident date set — all 11, not the 8 currently absent.** From the authoritative removal
+    audit (`data_provider_runs` id=538, whose own cascade record lists them):
+    `{_MATCHING_DATES}`.
+  - Steps:
+    1. some step text
+       ## OWNER AUTHORIZATION — J-11 Stage C (owner, 2026-08-24)
+       - **C1 — Date-set boundary.** For the avoidance
+         of doubt they are `{_MATCHING_DATES}`.
+  - Acceptance: some acceptance text
+
+<!-- Continuous-improvement auto-journeys: appended below -->
+"""
+
+_DISAGREEING_DATES = ", ".join(d.isoformat() for d in INCIDENT_DATES[:-1]) + ", 2099-01-01"
+_GOAL_MD_DISAGREEING = _GOAL_MD_MATCHING.replace(
+    f"of doubt they are `{_MATCHING_DATES}`.",
+    f"of doubt they are `{_DISAGREEING_DATES}`.",
+)
+
+_GOAL_MD_MISSING_C1 = _GOAL_MD_MATCHING.replace("For the avoidance\n         of doubt they are", "no such phrase here")
+
+
+# --- TC-3: the C1 date-set boundary check ---------------------------------------------------------
+
+
+def test_tc3_c1_boundary_matching_lists_pass():
+    check = jsc.check_c1_date_set_boundary(_GOAL_MD_MATCHING)
+    assert check["ok"] is True
+    assert check["lists_agree"] is True
+    assert check["code_matches_goal_md_lists"] is True
+    assert check["code_dates"] == [d.isoformat() for d in INCIDENT_DATES]
+
+
+def test_tc3_c1_boundary_disagreeing_lists_stop():
+    check = jsc.check_c1_date_set_boundary(_GOAL_MD_DISAGREEING)
+    assert check["ok"] is False
+    assert check["lists_agree"] is False
+    assert check["authoritative_bullet_dates"] != check["c1_restatement_dates"]
+
+
+def test_tc3_c1_boundary_missing_anchor_stops_not_guesses():
+    check = jsc.check_c1_date_set_boundary(_GOAL_MD_MISSING_C1)
+    assert check["ok"] is False
+    assert "extraction_error" in check
+
+
+def test_contract_hash_extraction_bounded_to_j11_section():
+    section = jsc.extract_j11_contract_text(_GOAL_MD_MATCHING)
+    assert section.startswith("- **J-11:")
+    assert "J-10: some other journey" not in section
+    assert "Continuous-improvement auto-journeys" not in section
+    # deterministic / reproducible
+    assert jsc.compute_contract_hash(_GOAL_MD_MATCHING) == jsc.compute_contract_hash(_GOAL_MD_MATCHING)
+
+
+def test_contract_text_missing_start_anchor_raises():
+    with pytest.raises(ValueError):
+        jsc.extract_j11_contract_text("no J-11 heading anywhere in this text")
+
+
+# --- TC-1: fresh Stage C preflight capture, fixture-DB shape ---------------------------------------
+
+
+@pytest.fixture()
+def engine():
+    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
+
+    @event.listens_for(eng, "connect")
+    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
+        cursor = dbapi_connection.cursor()
+        cursor.execute("PRAGMA foreign_keys=ON")
+        cursor.close()
+
+    SQLModel.metadata.create_all(eng)
+    return eng
+
+
+@pytest.fixture()
+def cfg():
+    return load_config()
+
+
+def test_tc1_preflight_capture_shape(engine, cfg):
+    with Session(engine) as session:
+        preflight = jsc.capture_stage_c_preflight(
+            session, engine, None,
+            goal_md_text=_GOAL_MD_MATCHING, git_head="deadbeef", config=cfg,
+        )
+    assert preflight["git_head"] == "deadbeef"
+    assert preflight["manifest_row_count"] == 0  # empty fixture DB
+    assert preflight["c1_date_set_boundary_check"]["ok"] is True
+    assert "engine_identity" in preflight["stage_c_attempt_identity"]["b2_engine_identity"]
+    assert preflight["pre_reset_inventory"]["daily_prices"]["row_count"] == 0
+    assert set(preflight["pre_reset_inventory"]["per_date"]) == {d.isoformat() for d in INCIDENT_DATES}
+    assert "table_sql" in preflight["manifest_ddl"]
+    assert "tables" in preflight["full_db_snapshot"]
+
+
+# --- TC-2: the preflight comparison gate ------------------------------------------------------------
+
+
+def _fresh_preflight(engine, cfg):
+    with Session(engine) as session:
+        return jsc.capture_stage_c_preflight(
+            session, engine, None,
+            goal_md_text=_GOAL_MD_MATCHING, git_head="deadbeef", config=cfg,
+        )
+
+
+def test_tc2_comparison_gate_passes_when_certified_state_matches_fresh_state(engine, cfg):
+    preflight = _fresh_preflight(engine, cfg)
+    # the certified baseline IS the fresh preflight's own shape (an unchanged database) -- a self-diff.
+    certified = copy.deepcopy(preflight)
+    gate = jsc.compare_preflight_to_certified(preflight, certified)
+    assert gate["all_invariants_hold"] is True
+    assert gate["material_mismatch"] is False
+    assert all(gate["checks"].values())
+
+
+def test_tc2_comparison_gate_stops_on_material_mismatch_manifest_row_count(engine, cfg):
+    preflight = _fresh_preflight(engine, cfg)
+    certified = copy.deepcopy(preflight)
+    # simulate the certified baseline recording 24 manifest rows while the fresh read finds a different
+    # count -- a materially-differs-from-certified-state case (TC-2's own worked example).
+    certified["manifest_row_count"] = 24
+    gate = jsc.compare_preflight_to_certified(preflight, certified)
+    assert gate["all_invariants_hold"] is False
+    assert gate["material_mismatch"] is True
+    assert gate["checks"]["manifest_row_count_matches_certified"] is False
+
+
+def test_tc2_comparison_gate_stops_on_per_date_scanner_run_drift(engine, cfg):
+    preflight = _fresh_preflight(engine, cfg)
+    certified = copy.deepcopy(preflight)
+    # certified state claims a run existed on an incident date that the fresh read found absent --
+    # exactly the "live state materially differs from the certified iteration-12 state" trap C2 exists
+    # to catch.
+    a_date_key = INCIDENT_DATES[0].isoformat()
+    certified["pre_reset_inventory"]["per_date"][a_date_key]["scanner_run"] = {
+        "present": True, "run_id": 999, "created_at": "2026-01-01T00:00:00+00:00", "engine_identity": "x",
+    }
+    gate = jsc.compare_preflight_to_certified(preflight, certified)
+    assert gate["all_invariants_hold"] is False
+    assert gate["checks"]["per_date_scanner_run_inventory_unchanged"] is False
+    assert gate["per_date_scanner_run_mismatches"]
+
+
+# --- TC-13: completion-marker gating -----------------------------------------------------------------
+
+
+def test_tc13_overall_verdict_fails_when_preflight_gate_fails():
+    verdict = jsc.stage_c_overall_verdict({"all_invariants_hold": False}, mutation_accounting=None)
+    assert verdict["passed"] is False
+    assert verdict["reason"] == "preflight_comparison_gate_failed"
+
+
+def test_tc13_overall_verdict_fails_when_no_mutation_accounting_captured():
+    verdict = jsc.stage_c_overall_verdict({"all_invariants_hold": True}, mutation_accounting=None)
+    assert verdict["passed"] is False
+    assert verdict["reason"] == "no_mutation_accounting_captured"
+
+
+def test_tc13_overall_verdict_fails_when_post_delete_verification_fails():
+    verdict = jsc.stage_c_overall_verdict(
+        {"all_invariants_hold": True}, mutation_accounting={"all_checks_pass": False}
+    )
+    assert verdict["passed"] is False
+    assert verdict["reason"] == "post_delete_verification_failed"
+
+
+def test_tc13_overall_verdict_passes_when_everything_holds():
+    verdict = jsc.stage_c_overall_verdict(
+        {"all_invariants_hold": True}, mutation_accounting={"all_checks_pass": True}
+    )
+    assert verdict["passed"] is True
+
+
+def test_tc13_build_completion_marker_refuses_on_failing_verdict():
+    with pytest.raises(RuntimeError):
+        jsc.build_completion_marker({"passed": False, "reason": "x"}, prior_artifact_timestamps=[])
+
+
+def test_tc13_build_completion_marker_timestamp_strictly_after_prior_artifacts():
+    earlier = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
+    marker = jsc.build_completion_marker({"passed": True, "reason": "all_checks_passed"}, prior_artifact_timestamps=[earlier])
+    assert marker["j11_stage_c_complete"] is True
+    completed_at = datetime.fromisoformat(marker["completed_at"])
+    assert completed_at > datetime.fromisoformat(earlier)
+
+
+def test_tc13_build_completion_marker_rejects_a_future_prior_timestamp_defensively():
+    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
+    with pytest.raises(RuntimeError):
+        jsc.build_completion_marker({"passed": True, "reason": "x"}, prior_artifact_timestamps=[future])
```
