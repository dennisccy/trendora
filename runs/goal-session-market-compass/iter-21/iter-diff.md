# Iteration diff (bounded)

Files changed: 4. Shown in full: 0.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/j11_stage_f_execute.py` (357 lines not shown)
- `apps/backend/scripts/run_j11_stage_f_execute.py` (40 lines not shown)
- `apps/backend/tests/test_j11_stage_f_execute.py` (715 lines not shown)
- `apps/backend/tests/test_j11_stage_f_execute_cli_script.py` (64 lines not shown)

```diff
diff --git a/apps/backend/app/engine/j11_stage_f_execute.py b/apps/backend/app/engine/j11_stage_f_execute.py
new file mode 100644
index 00000000..f0422a22
--- /dev/null
+++ b/apps/backend/app/engine/j11_stage_f_execute.py
@@ -0,0 +1,751 @@
+"""app.engine.j11_stage_f_execute -- J-11 Stage F EXECUTION (goal-market-compass iter-21).
+
+`docs/goal.md`'s "OWNER RULING -- J-11 Stage D through Stage G recovery execution AUTHORIZED" (owner,
+2026-08-26) item 8 authorizes Stage F, unconditionally, once Stage E has succeeded (iteration 20 --
+`runs/goal-market-compass-iter-20/j11-stage-e-execute-outcome.json`: `executed: true`). Stage F is the
+dependency-aware derived-CACHE invalidation: classify every `dataset_version`-bearing cache table Stage
+D/E's live writes could have made stale, and explicitly DELETE the rows a live, evidence-grounded reading
+proves are actually at risk -- so nothing in the database can silently serve pre-repair content once the
+app eventually reboots -- while touching no raw price, snapshot, or manifest row.
+
+**The correctness risk this module exists to fix (BACKGROUND finding 4):**
+`data_manager.availability_from_storage`'s "a row exists, its stamp does not match the current one, but
+no ingest job is in flight" branch (`data_manager.py:1741-1747`/`:1760-1763`) serves the SAME stale stored
+row with `stale: False` -- correct behavior for its designed case (an ordinary stamp bump with nothing
+running to chase it), but WRONG the first time `/api/data/availability` loads after a post-Stage-G reboot
+with no ingest job running: it would silently serve the PRE-INCIDENT heatmap labeled current. Leaving
+`availability_cache`'s stale row in place is a live AG-3/AG-8 risk, not hygiene.
+
+**The decisive classification signal is `created_at`, never the `dataset_version` stamp string alone**
+(iter-15b's "never trust a single fingerprint alone" lesson, and the TC-7 collision trap this module's
+tests prove against): a delete-and-recreate of `scanner_runs`/`forward_returns` that reproduces an
+IDENTICAL stamp string is still detected as stale by comparing every stored row's `created_at` against
+Stage D's frozen execution-start instant -- a row predating that instant describes a world Stage D/E have
+since changed, regardless of what its stamp string happens to read.
+
+**membership_timeline_cache is the one table with a genuine, proof-gated tradeoff** (BACKGROUND finding
+5): deleting its stale row forces the next real request onto `_membership_timeline`'s documented >300s
+full O(dates x pool) cold-compute sweep. `evaluate_membership_timeline_incremental_reuse_safety` proves,
+live and read-only, whether `data_manager.membership_timeline_cached`'s own MISS-repair logic
+(`data_manager.py:894-963`) would instead take the CHEAP "historical gap-insert" branch (reusing cached
+per-date `excluded` tallies) -- reusing `data_manager._membership_bars_are_forward_only`/
+`_parse_membership_stamp` DIRECTLY (never a second implementation of that exact correctness proof). Only
+when that proof holds does this table get `preserve_for_incremental_reuse`; otherwise it falls back to
+`explicit_delete` like every other stale cache.
+
+Sequence (composed by the CLI script, mirroring `j11_stage_e_execute.py`'s idiom exactly):
+
+  1. Fresh, READ-ONLY preflight -- reusing `j11_stage_d_execute.recheck_maintenance_boundary_and_guard`
+     and `j11_stage_e_execute.check_engine_identity_matches_stage_d`/`confirm_manifests_unchanged`
+     directly (never reimplemented, called by the CLI script); this module adds
+     `confirm_stage_e_complete_and_unrestamped` (per incident date: Stage D's own run id, unrestamped,
+     carrying the EXACT `ForwardReturn` count Stage E's own population report recorded -- including run
+     3158's legitimate 0), `derive_cache_table_inventory` (genuine runtime introspection, never a
+     hardcoded list -- TC-3), `derive_stage_d_execution_start_instant` (live re-derivation, never a
+     hardcoded citation), and `confirm_no_cache_row_at_or_after_stage_d_start` (the "gravest" check: an
+     unexplained cache write during maintenance isolation halts the WHOLE attempt).
+     `stage_f_preflight_gate_verdict` combines everything into one go/no-go.
+  2. `classify_cache_table`, once per inventoried table -- recomputes the table's CURRENT live stamp via
+     its ACTUAL writer/version function (`research._dataset_version` for the 3 broad-stamp caches,
+     `research._membership_dataset_version` for `availability_cache`/`coverage_snapshot`/
+     `membership_timeline_cache`, `indexes.index_series_dataset_version` for `index_series_cache`),
+     reads every distinct stored stamp + every row's `created_at`, and assigns one disposition:
+     `explicit_delete` (the default for 5 of the 7 tables -- decided by `created_at`, not the stamp),
+     `prove_unaffected_leave_alone` (`index_series_cache`, when its own re-derived stamp still equals the
+     stored one), or `preserve_for_incremental_reuse` (`membership_timeline_cache`, ONLY when the live
+     incremental-reuse proof holds).
+  3. `execute_stage_f_cache_disposition` -- the ONE authorized write: deletes every row in every table
+     classified `explicit_delete` (the preflight already proves every row in these tables predates Stage
+     D's start, so "delete everything" IS "delete exactly the already-proven-stale rows"); zero write to
+     any other table.
+  4. `live_verify_cache_dispositions` -- post-write, read-only: deleted tables hold zero rows; preserved
+     tables are row-count-unchanged.
+  5. `build_stage_f_mutation_accounting` -- proves `changed_existing_tables` is a subset of exactly the
+     tables classified `explicit_delete` (a set this run computes from live classification, never a fixed
+     literal the way Stage D/E's write-table sets were, since WHICH tables get deleted is itself
+     data-driven), and every other table (the 10 canonical J-11-protected tables, plus any cache table
+     NOT classified `explicit_delete`) shows zero fingerprint change.
+  6. `stage_f_execution_outcome` -- the final `STAGE F COMPLETE: YES/NO` decision, never an invented third
+     state.
+
+Never touches (imports nothing from, calls nothing in): `app/api/*`, `scoring.py`, `compass.py`,
+`data_manager.py`'s write paths, `scanner.py`, or any canonical producer/serving function's CODE (Stage F
+reads `data_manager.availability_from_storage`/`coverage_from_storage`'s DOCUMENTED behavior and the
+narrow stamp functions those modules already export -- it does not modify a line of any of them).
+"""
+from __future__ import annotations
+
+import json
+from datetime import date as date_cls
+from datetime import datetime, timezone
+from typing import Any, Optional
+
+from sqlalchemy import delete as sa_delete
+from sqlalchemy import func
+from sqlmodel import Session, SQLModel, select
+
+from app.config import Config
+from app.engine import data_manager
+from app.engine import indexes
+from app.engine import j11_maintenance
+from app.engine import j11_schema_migration as migration
+from app.engine import research
+from app.models import (
+    AvailabilityCache,
+    CoverageSnapshot,
+    EventStudyCache,
+    ForwardAggregateCache,
+    ForwardReturn,
+    IndexSeriesCache,
+    MarketPhaseCache,
+    MembershipTimelineCache,
+    ScannerRun,
+)
+
+# The seven tables confirmed exhaustive at planning time (2026-08-27, by grep against app/models.py --
+# see docs/goal.md BACKGROUND finding 1). This is an EXPECTATION used only for the inventory step's
+# honest comparison/reporting -- the inventory itself (`derive_cache_table_inventory`) is genuine runtime
+# introspection, never driven by this tuple (TC-3).
+EXPECTED_CACHE_TABLE_NAMES: tuple[str, ...] = (
+    "event_study_cache", "market_phase_cache", "forward_aggregate_cache", "index_series_cache",
+    "membership_timeline_cache", "availability_cache", "coverage_snapshot",
+)
+
+# The concrete SQLModel class per known table name -- used by classification/execution/verification
+# (typed ORM queries, matching every other query pattern in this codebase) for the tables the inventory
+# step's genuine introspection actually finds. A table name absent from this dict is classified
+# `unclassified_unknown_family` rather than guessed at (see `classify_cache_table`).
+CACHE_TABLE_MODEL_BY_NAME: dict[str, type] = {
+    "event_study_cache": EventStudyCache,
+    "market_phase_cache": MarketPhaseCache,
+    "forward_aggregate_cache": ForwardAggregateCache,
+    "index_series_cache": IndexSeriesCache,
+    "membership_timeline_cache": MembershipTimelineCache,
+    "availability_cache": AvailabilityCache,
+    "coverage_snapshot": CoverageSnapshot,
+}
+
+# Which live-stamp function each table's ACTUAL writer/version call site uses (docs/goal.md BACKGROUND
+# finding 2 -- verified at the call site, never trusted from a class docstring; MembershipTimelineCache's
+# own class-level docstring is stale and would give the WRONG family if trusted).
+CACHE_KEY_FAMILY: dict[str, str] = {
+    "event_study_cache": "broad",
+    "market_phase_cache": "broad",
+    "forward_aggregate_cache": "broad",
+    "index_series_cache": "index_narrow",
+    "membership_timeline_cache": "narrow",
+    "availability_cache": "narrow",
+    "coverage_snapshot": "narrow",
+}
+
+# The ten tables Stage F must never write to and must show zero fingerprint change on (mirrors
+# `j11_stage_e_execute.OUT_OF_SCOPE_TABLES`, widened by the two tables Stage E itself was authorized to
+# touch -- `forward_returns` -- plus `next_session_manifests`, spelled out explicitly rather than derived
+# so a future schema addition never silently narrows this list).
+OUT_OF_SCOPE_TABLES: tuple[str, ...] = (
+    "daily_prices", "scanner_runs", "scanner_results", "sector_scores", "theme_scores", "forward_returns",
+    "data_provider_runs", "watchlist", "maintenance_boundaries", "next_session_manifests",
+)
+
+
+def _now_iso() -> str:
+    return datetime.now(timezone.utc).isoformat()
+
+
+def _iso_or_none(value: Optional[datetime]) -> Optional[str]:
+    """Same tzinfo-safe re-serialization `j11_maintenance._utc_isoformat` uses (SQLite drops tzinfo on
+    round-trip) -- an honest `None` passes through unchanged, never a fabricated timestamp. Every
+    timestamp this module reads from the database goes through this ONE function, so every string it
+    hands to `_parse_iso_or_none` downstream is consistently tz-aware -- never a naive-vs-aware
+    comparison surprise against a caller-supplied `stage_d_start_instant`."""
+    if value is None:
+        return None
+    if value.tzinfo is None:
+        value = value.replace(tzinfo=timezone.utc)
+    return value.astimezone(timezone.utc).isoformat()
+
+
+def _parse_iso_or_none(value: Optional[str]) -> Optional[datetime]:
+    return datetime.fromisoformat(value) if value else None
+
+
+def _timestamp_attr_and_name(model: Any) -> tuple[Any, str]:
+    """The model's own audit-timestamp column -- `created_at` for six of the seven tables,
+    `computed_at` for `CoverageSnapshot` (`app/models.py:954`). Resolved by attribute presence, not a
+    per-table hardcoded name, so a future rename is caught rather than silently misread."""
+    if hasattr(model, "created_at"):
+        return model.created_at, "created_at"
+    return model.computed_at, "computed_at"
+
+
+# ================================================================================================
+# Step 1a -- genuine runtime introspection (TC-3): never a hardcoded list
+# ================================================================================================
+
+
+def derive_cache_table_inventory(metadata: Optional[Any] = None) -> dict:
+    """Introspects SQLModel metadata (defaulting to the REAL `SQLModel.metadata`, i.e. every table class
+    currently defined across the whole app -- including `app.models`) at RUNTIME for every table carrying
+    a `dataset_version` column -- never a hardcoded list (docs/goal.md J-11 step 6, TC-3). A table is
+    included iff its CURRENT schema declares the column; injecting a different `metadata` (a fixture-built
+    `sqlalchemy.MetaData()`) changes the returned set, proving this is genuine introspection wearing no
+    hardcoded-list costume."""
+    md = metadata if metadata is not None else SQLModel.metadata
+    table_names = sorted(name for name, table in md.tables.items() if "dataset_version" in table.columns)
+    expected_sorted = sorted(EXPECTED_CACHE_TABLE_NAMES)
+    return {
+        "generated_at": _now_iso(),
+        "table_names": table_names,
+        "table_count": len(table_names),
+        "expected_table_names": expected_sorted,
+        "matches_expected_seven": table_names == expected_sorted,
+    }
+
+
+# ================================================================================================
+# Step 1b -- Stage E end-state re-verification (mirrors confirm_stage_d_runs_present_unrestamped's
+# shape, widened to check the EXACT recorded ForwardReturn count rather than merely zero)
+# ================================================================================================
+
+
+def confirm_stage_e_complete_and_unrestamped(
+    session: Session,
+    *,
+    expected_run_id_by_date: dict[str, int],
+    expected_forward_return_count_by_run_id: dict[str, int],
+    frozen_engine_identity: str,
+) -> dict:
+    """For every one of Stage D's 11 rebuilt incident dates, confirm the live `ScannerRun` row is
+    present, carries the SAME `id` Stage D's own recorded regeneration evidence assigned to that date,
+    carries the SAME frozen `engine_identity`, and currently holds EXACTLY the `ForwardReturn` count
+    Stage E's own population report recorded for that run id (including a legitimate `0` -- e.g. run
+    3158, sitting on the frontier with no observable horizon -- never treated as a gap). Read-only --
+    never writes, never restamps."""
+    per_date: dict[str, dict] = {}
+    for date_str, expected_run_id in sorted(expected_run_id_by_date.items()):
+        one_date = date_cls.fromisoformat(date_str)
+        row = session.exec(
+            select(ScannerRun.id, ScannerRun.asof_date, ScannerRun.engine_identity, ScannerRun.created_at)
+            .where(ScannerRun.asof_date == one_date)
+        ).first()
+        present = row is not None
+        observed_id = int(row[0]) if present else None
+        observed_identity = row[2] if present else None
+        fr_count = (
+            int(session.scalar(select(func.count()).select_from(ForwardReturn).where(ForwardReturn.run_id == observed_id)) or 0)
+            if present else None
+        )
+        expected_fr_count = expected_forward_return_count_by_run_id.get(str(expected_run_id))
+        id_matches = present and observed_id == expected_run_id
+        identity_matches = present and observed_identity == frozen_engine_identity
+        fr_count_matches = present and expected_fr_count is not None and fr_count == expected_fr_count
+        per_date[date_str] = {
+            "expected_run_id": expected_run_id,
+            "present": present,
+            "observed_run_id": observed_id,
+            "id_matches": id_matches,
+            "observed_engine_identity": observed_identity,
+            "identity_matches": identity_matches,
+            "observed_created_at": _iso_or_none(row[3]) if present else None,
+            "expected_forward_return_count": expected_fr_count,
+            "observed_forward_return_count": fr_count,
+            "forward_return_count_matches": fr_count_matches,
+            "ok": present and id_matches and identity_matches and fr_count_matches,
+        }
+    ok = bool(per_date) and all(v["ok"] for v in per_date.values())
+    return {"checked_at": _now_iso(), "per_date": per_date, "ok": ok}
+
+
+# ================================================================================================
+# Step 1c -- Stage D's frozen execution-start instant, re-derived live (never hardcoded)
+# ================================================================================================
+
+
+def derive_stage_d_execution_start_instant(session: Session, incident_run_ids: list[int]) -> dict:
+    """Live, read-only re-derivation of Stage D's frozen execution-start instant -- the `created_at` of
+    the FIRST `ScannerRun` Stage D actually inserted (`MIN(created_at)` over the given ids). Never a
+    hardcoded citation (docs/goal.md classify_cache_table bullet: "never hardcode the citation").
+    `incident_run_ids` comes from Stage D's OWN recorded regeneration evidence
+    (`per_date_results[*].run_id`), loaded by the caller -- this function performs no file I/O."""
+    value = session.scalar(select(func.min(ScannerRun.created_at)).where(ScannerRun.id.in_(incident_run_ids)))
+    return {
+        "generated_at": _now_iso(),
+        "incident_run_ids": sorted(incident_run_ids),
+        "stage_d_execution_start_instant": _iso_or_none(value),
+    }
+
+
+# ================================================================================================
+# Step 1d -- per-table snapshot (row count, distinct stamps, audit-timestamp bounds) -- reused by
+# BOTH the late-row hygiene check and per-table classification
+# ================================================================================================
+
+
+def capture_cache_table_snapshot(session: Session, table_name: str) -> dict:
+    """A read-only snapshot of one cache table: row count, every DISTINCT stored `dataset_version` with
+    its own row count + timestamp bounds, and the table-wide MAX timestamp (the decisive value for the
+    late-row hygiene check -- see `confirm_no_cache_row_at_or_after_stage_d_start`). Column-projected
+    aggregates only -- never a full-row hydration (AG-8), even for `market_phase_cache`'s 1,000+ rows."""
+    model = CACHE_TABLE_MODEL_BY_NAME[table_name]
+    ts_attr, ts_attr_name = _timestamp_attr_and_name(model)
+    row_count = int(session.scalar(select(func.count()).select_from(model)) or 0)
+    stamp_rows = session.exec(
+        select(model.dataset_version, func.count(), func.min(ts_attr), func.max(ts_attr))
+        .group_by(model.dataset_version)
+    ).all()
+    distinct_stamps = [
+        {
+            "dataset_version": r[0], "count": int(r[1]),
+            "min_timestamp": _iso_or_none(r[2]), "max_timestamp": _iso_or_none(r[3]),
+        }
+        for r in stamp_rows
+    ]
+    overall_max_ts = session.scalar(select(func.max(ts_attr)))
+    return {
+        "table_name": table_name,
+        "timestamp_column": ts_attr_name,
+        "row_count": row_count,
+        "distinct_stamps": distinct_stamps,
+        "max_timestamp": _iso_or_none(overall_max_ts),
+    }
+
+
+# ================================================================================================
+# Step 1e -- the "gravest" preflight check: no cache row written during maintenance isolation
+# ================================================================================================
+
+
+def confirm_no_cache_row_at_or_after_stage_d_start(
+    snapshots_by_table: dict[str, dict], *, stage_d_start_instant: datetime,
+) -> dict:
+    """For the six tables whose stamp depends on `scanner_runs` and/or `forward_returns`
+    (`snapshots_by_table` must already EXCLUDE `index_series_cache` -- its stamp depends only on
+    `daily_prices`, proven byte-unchanged by Stage D/E's own mutation accounting, so it carries no
+    scanner-run-derived hygiene obligation): every stored row's timestamp must be STRICTLY EARLIER than
+    Stage D's frozen execution-start instant. A hit here means an unexplained write happened during
+    maintenance isolation -- graver than a routine classification disagreement -- and the caller MUST
+    halt the WHOLE attempt before any write, never silently delete or silently accept it. Fail-closed on
+    an empty `snapshots_by_table` (mirrors `confirm_stage_d_runs_present_unrestamped`'s
+    `bool(per_date) and all(...)` idiom, praised sound in the iter-20 audit)."""
+    per_table: dict[str, dict] = {}
+    for name, snap in snapshots_by_table.items():
+        max_ts = _parse_iso_or_none(snap["max_timestamp"])
+        table_ok = max_ts is None or max_ts < stage_d_start_instant
+        per_table[name] = {"max_timestamp": snap["max_timestamp"], "ok": table_ok}
+    ok = bool(per_table) and all(v["ok"] for v in per_table.values())
+    return {
+        "checked_at": _now_iso(),
+        "stage_d_start_instant": _iso_or_none(stage_d_start_instant),
+        "per_table": per_table,
+        "ok": ok,
+    }
+
+
+# ================================================================================================
+# Step 1f -- the combined Stage F preflight gate
+# ================================================================================================
+
+
+def stage_f_preflight_gate_verdict(
+    *,
+    boundary_recheck: dict,
+    stage_e_check: dict,
+    identity_check: dict,
+    manifest_check: dict,
+    inventory: dict,
+    late_rows_check: dict,
+) -> dict:
+    """The single go/no-go decision for Stage F EXECUTION. Any one of the six checks failing means
+    `proceed: False`, and the caller MUST perform zero writes to any table."""
+    boundary_ok = bool(boundary_recheck.get("ok"))
+    stage_e_ok = bool(stage_e_check.get("ok"))
+    identity_ok = bool(identity_check.get("ok"))
+    manifest_ok = bool(manifest_check.get("ok"))
+    inventory_ok = bool(inventory.get("matches_expected_seven"))
+    late_rows_ok = bool(late_rows_check.get("ok"))
+    proceed = boundary_ok and stage_e_ok and identity_ok and manifest_ok and inventory_ok and late_rows_ok
+
+    blocking_reasons: list[str] = []
+    if not boundary_ok:
+        blocking_reasons.append("maintenance_boundary_or_guard_recheck_failed")
+    if not stage_e_ok:
+        blocking_reasons.append("stage_e_runs_not_present_unrestamped_or_forward_return_count_mismatch")
+    if not identity_ok:
+        blocking_reasons.append("engine_identity_drifted_since_stage_d")
+    if not manifest_ok:
+        blocking_reasons.append("next_session_manifests_changed_since_stage_d")
+    if not inventory_ok:
+        blocking_reasons.append(f"cache_table_inventory_mismatch:{inventory.get('table_names')}")
+    if not late_rows_ok:
+        blocking_reasons.append("cache_row_created_at_or_after_stage_d_start_detected")
+
+    return {
+        "generated_at": _now_iso(),
+        "proceed": proceed,
+        "boundary_ok": boundary_ok,
+        "stage_e_ok": stage_e_ok,
+        "identity_ok": identity_ok,
+        "manifest_ok": manifest_ok,
+        "inventory_ok": inventory_ok,
+        "late_rows_ok": late_rows_ok,
+        "blocking_reasons": blocking_reasons,
+    }
+
+
... [diff_bound] apps/backend/app/engine/j11_stage_f_execute.py: 357 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/scripts/run_j11_stage_f_execute.py b/apps/backend/scripts/run_j11_stage_f_execute.py
new file mode 100644
index 00000000..a80816f0
--- /dev/null
+++ b/apps/backend/scripts/run_j11_stage_f_execute.py
@@ -0,0 +1,434 @@
+"""goal-market-compass iter-21 -- J-11 Stage F EXECUTION: the ONE owner-authorized live,
+dependency-aware derived-cache invalidation over the seven `dataset_version`-bearing cache tables
+(`docs/goal.md`'s "OWNER RULING -- J-11 Stage D through Stage G recovery execution AUTHORIZED", owner
+2026-08-26, item 8 -- authorized unconditionally following a successful Stage E; iteration 20 already
+executed and independently-evaluator-verified Stage E).
+
+Mirrors `run_j11_stage_e_execute.py`'s idiom exactly: NO database interaction of any kind, not even a
+read, without `--confirm`; evidence is persisted at every checkpoint BEFORE the write so a mid-run crash
+still leaves a forensic trail; the completion/outcome marker is written ONLY after full post-execution
+verification completes (whichever of the two honest terminal states -- `STAGE F COMPLETE: YES` or
+`STAGE F COMPLETE: NO` -- that verification proves). Sequence:
+
+  1. Fresh, READ-ONLY preflight: boundary/guard re-check (`j11_stage_d_execute.
+     recheck_maintenance_boundary_and_guard`, REUSED directly), the 11 Stage-D/E incident runs
+     present/unrestamped/exact-ForwardReturn-count check (`j11_stage_f_execute.
+     confirm_stage_e_complete_and_unrestamped`), a fresh `engine_identity` equality check against Stage
+     D's frozen value (`j11_stage_e_execute.check_engine_identity_matches_stage_d`, REUSED directly), a
+     `next_session_manifests` unchanged check against the same certified baseline (`j11_stage_e_execute.
+     confirm_manifests_unchanged`, REUSED directly), a genuine runtime cache-table inventory
+     (`derive_cache_table_inventory`), and the "gravest" hygiene check that no cache row was written
+     during maintenance isolation (`confirm_no_cache_row_at_or_after_stage_d_start`) -- combined into ONE
+     execution gate. STOPS here (zero writes of any kind) unless the gate's `proceed` is True.
+  2. Pre-write captures for mutation accounting (full table sweep, `daily_prices`/`data_provider_runs`/
+     `watchlist`/`maintenance_boundaries`/`next_session_manifests` snapshots).
+  3. Per-table classification (`classify_cache_table`) for every inventoried table -- read-only, still no
+     write.
+  4. THE ONE authorized write (`execute_stage_f_cache_disposition`) -- deletes every row in every table
+     classified `explicit_delete`; zero write to any other table.
+  5. Live, read-only post-write verification (`live_verify_cache_dispositions`).
+  6. Post-execution mutation accounting, proving every out-of-scope AND every preserved cache table shows
+     zero fingerprint change, and only the classified `explicit_delete` tables changed.
+  7. The final outcome, written UNCONDITIONALLY as the LAST evidence artifact -- Stage F's own contract
+     defines TWO honest terminal states (`YES`/`NO`), and BOTH require full evidence preserved
+     (docs/goal.md item 14) -- never a bare non-zero exit with no persisted outcome record.
+
+Usage:
+    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_f_execute.py \\
+        --confirm \\
+        --evidence-dir runs/goal-market-compass-iter-21
+
+Without `--confirm`, the script performs NO database interaction at all (not even a read) and exits
+non-zero. `--evidence-dir` is REQUIRED and has no implicit default (mirrors every other J-11
+evidence-writing script -- an omitted flag must never fall back to overwriting a committed evidence
+directory).
+"""
+from __future__ import annotations
+
+import argparse
+import json
+import sys
+from datetime import datetime
+from pathlib import Path
+from typing import Optional
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
+from app.engine import engine_identity  # noqa: E402
+from app.engine import j11_maintenance  # noqa: E402
+from app.engine import j11_schema_migration as migration  # noqa: E402
+from app.engine import j11_stage_c as jsc  # noqa: E402
+from app.engine import j11_stage_d_execute as jsde  # noqa: E402
+from app.engine import j11_stage_e_execute as jsee  # noqa: E402
+from app.engine import j11_stage_f_execute as jsfe  # noqa: E402
+from app.models import DataProviderRun, MaintenanceBoundary, NextSessionManifest, Watchlist  # noqa: E402
+
+DEFAULT_STAGE_D_FROZEN_IDENTITY_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-19" / "j11-stage-d-execute-frozen-identity.json"
+)
+DEFAULT_STAGE_D_REGENERATION_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-19" / "j11-stage-d-execute-regeneration.json"
+)
+DEFAULT_STAGE_E_POPULATION_REPORT_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-20" / "j11-stage-e-execute-population-report.json"
+)
+DEFAULT_CERTIFIED_BASELINE_PATH = (
+    REPO_ROOT / "runs" / "goal-market-compass-iter-16" / "j11-stage-d-certified-baseline.json"
+)
+
+OUTPUT_FILENAMES = (
+    "j11-stage-f-execute-db-file-true-start.json",
+    "j11-stage-f-execute-boundary-recheck.json",
+    "j11-stage-f-execute-stage-e-check.json",
+    "j11-stage-f-execute-identity-comparison.json",
+    "j11-stage-f-execute-manifest-check.json",
+    "j11-stage-f-execute-inventory.json",
+    "j11-stage-f-execute-stage-d-start-instant.json",
+    "j11-stage-f-execute-late-rows-check.json",
+    "j11-stage-f-execute-preflight-gate.json",
+    "j11-stage-f-execute-dispositions.json",
+    "j11-stage-f-execute-execution-result.json",
+    "j11-stage-f-execute-verification-result.json",
+    "j11-stage-f-execute-memory-check.json",
+    "j11-stage-f-execute-mutation-accounting.json",
+    "j11-stage-f-execute-outcome.json",
+    "j11-stage-f-execute-db-file-true-end.json",
+)
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
+def _refuse_if_evidence_files_exist(evidence_dir: Path, filenames: tuple) -> list[str]:
+    """Mirrors the SAME collision guard `run_j11_stage_e_execute.py` uses -- a pure filesystem check, no
+    database interaction."""
+    return [name for name in filenames if (evidence_dir / name).exists()]
+
+
+def _load_json(path: Path) -> Optional[dict]:
+    """Loads one historical evidence artifact. Never raises on a missing/malformed file -- an absent
+    cross-iteration artifact is recorded honestly as `None`, never fabricated and never a crash."""
+    if not path.exists():
+        return None
+    try:
+        return json.loads(path.read_text())
+    except (OSError, json.JSONDecodeError):
+        return None
+
+
+def _load_stage_d_frozen_identity(path: Path) -> Optional[str]:
+    payload = _load_json(path)
+    if not isinstance(payload, dict):
+        return None
+    value = payload.get("engine_identity")
+    return value if isinstance(value, str) else None
+
+
+def _load_expected_run_id_by_date(path: Path) -> dict[str, int]:
+    """`{iso_date: run_id}` from Stage D's own recorded regeneration evidence
+    (`per_date_results[*].date`/`.run_id`) -- never a fresh hardcoded literal. An absent/malformed file
+    yields an empty mapping (the stage-E check then honestly reports every date as `present: False` and
+    the gate refuses to proceed -- fail closed, never fabricated)."""
+    payload = _load_json(path)
+    if not isinstance(payload, dict):
+        return {}
+    entries = payload.get("per_date_results")
+    if not isinstance(entries, list):
+        return {}
+    out: dict[str, int] = {}
+    for entry in entries:
+        if isinstance(entry, dict) and isinstance(entry.get("date"), str) and isinstance(entry.get("run_id"), int):
+            out[entry["date"]] = entry["run_id"]
+    return out
+
+
+def _load_expected_forward_return_count_by_run_id(path: Path) -> dict[str, int]:
+    """`{str(run_id): post_count}` from Stage E's own recorded population report
+    (`population_a_rebuilt_incident_runs[*].post`) -- never a fresh hardcoded literal, and never treats a
+    legitimate `0` (run 3158's own recorded outcome) as missing/absent."""
+    payload = _load_json(path)
+    if not isinstance(payload, dict):
+        return {}
+    population_a = payload.get("population_a_rebuilt_incident_runs")
+    if not isinstance(population_a, dict):
+        return {}
+    out: dict[str, int] = {}
+    for run_id_str, entry in population_a.items():
+        if isinstance(entry, dict) and isinstance(entry.get("post"), int):
+            out[run_id_str] = entry["post"]
+    return out
+
+
+def _load_certified_manifest_dump(path: Path) -> list[dict]:
+    payload = _load_json(path)
+    if not isinstance(payload, dict):
+        return []
+    dump = payload.get("manifest_dump")
+    return dump if isinstance(dump, list) else []
+
+
+def main() -> int:
+    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
+    parser.add_argument(
+        "--evidence-dir", type=Path, default=None,
+        help="required -- no default on purpose (mirrors every other J-11 evidence-writing script).",
+    )
+    parser.add_argument(
+        "--confirm", action="store_true",
+        help="required -- without it, the script touches the database not at all and exits non-zero.",
+    )
+    parser.add_argument("--stage-d-frozen-identity-path", type=Path, default=DEFAULT_STAGE_D_FROZEN_IDENTITY_PATH)
+    parser.add_argument("--stage-d-regeneration-path", type=Path, default=DEFAULT_STAGE_D_REGENERATION_PATH)
+    parser.add_argument("--stage-e-population-report-path", type=Path, default=DEFAULT_STAGE_E_POPULATION_REPORT_PATH)
+    parser.add_argument("--certified-baseline-path", type=Path, default=DEFAULT_CERTIFIED_BASELINE_PATH)
+    args = parser.parse_args()
+
+    if not args.confirm:
+        print(
+            "refusing to run without --confirm (this is the ONE owner-authorized live Stage F write "
+            "this iteration -- docs/goal.md J-11 step 11's Stage D-through-G OWNER RULING, item 8). No "
+            "database interaction, not even a read, has occurred.",
+            file=sys.stderr,
+        )
+        return 2
+
+    if args.evidence_dir is None:
+        print(
+            "refusing to run without an explicit --evidence-dir. No database interaction, not even a "
+            "read, has occurred, and nothing has been written.",
+            file=sys.stderr,
+        )
+        return 2
+
+    evidence_dir: Path = args.evidence_dir
+    colliding = _refuse_if_evidence_files_exist(evidence_dir, OUTPUT_FILENAMES)
+    if colliding:
+        print(
+            f"refusing to run: --evidence-dir {evidence_dir} already contains {colliding} -- this looks "
+            "like a re-run pointed at an already-populated evidence folder rather than a fresh one. No "
+            "database interaction, not even a read, has occurred, and no existing file has been touched.",
+            file=sys.stderr,
+        )
+        return 2
+
+    cfg = load_config()
+    resolved_url = resolve_database_url(cfg.database.url)
+    db_path = _db_file_path(resolved_url)
+    print(f"database: {resolved_url}", file=sys.stderr)
+
+    # --- TRUE process start: the db file + WAL sidecar fingerprint, before anything else touches it ---
+    db_file_true_start = jsc.db_file_fingerprint(db_path)
+    _write_json(evidence_dir / "j11-stage-f-execute-db-file-true-start.json", db_file_true_start)
+
+    engine = get_engine()  # the SAME pooled writable engine the real backend uses.
+
+    stage_d_frozen_identity = _load_stage_d_frozen_identity(args.stage_d_frozen_identity_path)
+    expected_run_id_by_date = _load_expected_run_id_by_date(args.stage_d_regeneration_path)
+    expected_forward_return_count_by_run_id = _load_expected_forward_return_count_by_run_id(args.stage_e_population_report_path)
+    certified_manifest_dump = _load_certified_manifest_dump(args.certified_baseline_path)
+    incident_run_ids = sorted(expected_run_id_by_date.values())
+
+    def _stop(reason: str, preflight_gate: dict, boundary_recheck: "dict | None" = None) -> int:
+        outcome = jsfe.stage_f_execution_outcome(
+            preflight_gate=preflight_gate, dispositions=None, execution_result=None,
+            verification_result=None, mutation_accounting=None,
+        )
+        _write_json(evidence_dir / "j11-stage-f-execute-outcome.json", outcome)
+        db_file_true_end = jsc.db_file_fingerprint(db_path)
+        _write_json(evidence_dir / "j11-stage-f-execute-db-file-true-end.json", db_file_true_end)
+        print(f"STOP before any write: {reason}", file=sys.stderr)
+        _print_terminal_lines(outcome, boundary_recheck=boundary_recheck)
+        return 1
+
+    # === Step 1: fresh, read-only preflight ============================================================
+    with Session(engine) as session:
+        boundary_recheck = jsde.recheck_maintenance_boundary_and_guard(session)
+    _write_json(evidence_dir / "j11-stage-f-execute-boundary-recheck.json", boundary_recheck)
+    print(
+        f"boundary/guard recheck: ok={boundary_recheck['ok']} "
+        f"all_dates_blocked={boundary_recheck['all_dates_blocked']}",
+        file=sys.stderr,
+    )
+
+    with Session(engine) as session:
+        stage_e_check = jsfe.confirm_stage_e_complete_and_unrestamped(
+            session,
+            expected_run_id_by_date=expected_run_id_by_date,
+            expected_forward_return_count_by_run_id=expected_forward_return_count_by_run_id,
+            frozen_engine_identity=stage_d_frozen_identity or "",
+        )
+    _write_json(evidence_dir / "j11-stage-f-execute-stage-e-check.json", stage_e_check)
+    print(f"Stage E end-state check: ok={stage_e_check['ok']}", file=sys.stderr)
+
+    fresh_identity = engine_identity.compute_engine_identity(cfg)
+    identity_check = jsee.check_engine_identity_matches_stage_d(fresh_identity, stage_d_frozen_identity)
+    _write_json(evidence_dir / "j11-stage-f-execute-identity-comparison.json", identity_check)
+    print(f"engine_identity check: ok={identity_check['ok']} fresh={fresh_identity}", file=sys.stderr)
+
+    manifest_check = jsee.confirm_manifests_unchanged(engine, certified_manifest_dump=certified_manifest_dump)
+    _write_json(evidence_dir / "j11-stage-f-execute-manifest-check.json", manifest_check)
+    print(f"manifest check: ok={manifest_check['ok']}", file=sys.stderr)
+
+    inventory = jsfe.derive_cache_table_inventory()
+    _write_json(evidence_dir / "j11-stage-f-execute-inventory.json", inventory)
+    print(f"cache table inventory: {inventory['table_names']} matches_expected_seven={inventory['matches_expected_seven']}", file=sys.stderr)
+
+    with Session(engine) as session:
+        start_instant_result = jsfe.derive_stage_d_execution_start_instant(session, incident_run_ids)
+    _write_json(evidence_dir / "j11-stage-f-execute-stage-d-start-instant.json", start_instant_result)
+    stage_d_start_instant_str = start_instant_result["stage_d_execution_start_instant"]
+    print(f"Stage D execution-start instant (re-derived live): {stage_d_start_instant_str}", file=sys.stderr)
+    if stage_d_start_instant_str is None:
+        preflight_gate = jsfe.stage_f_preflight_gate_verdict(
+            boundary_recheck=boundary_recheck, stage_e_check=stage_e_check, identity_check=identity_check,
+            manifest_check=manifest_check, inventory=inventory, late_rows_check={"ok": False},
+        )
+        _write_json(evidence_dir / "j11-stage-f-execute-preflight-gate.json", preflight_gate)
+        return _stop("could not derive Stage D's execution-start instant (no incident runs found live)", preflight_gate, boundary_recheck)
+    stage_d_start_instant = datetime.fromisoformat(stage_d_start_instant_str)
+
+    non_index_table_names = [n for n in inventory["table_names"] if n != "index_series_cache"]
+    with Session(engine) as session:
+        snapshots_for_late_check = {n: jsfe.capture_cache_table_snapshot(session, n) for n in non_index_table_names if n in jsfe.CACHE_TABLE_MODEL_BY_NAME}
+    late_rows_check = jsfe.confirm_no_cache_row_at_or_after_stage_d_start(snapshots_for_late_check, stage_d_start_instant=stage_d_start_instant)
+    _write_json(evidence_dir / "j11-stage-f-execute-late-rows-check.json", late_rows_check)
+    print(f"late-row hygiene check: ok={late_rows_check['ok']}", file=sys.stderr)
+
+    preflight_gate = jsfe.stage_f_preflight_gate_verdict(
+        boundary_recheck=boundary_recheck, stage_e_check=stage_e_check, identity_check=identity_check,
+        manifest_check=manifest_check, inventory=inventory, late_rows_check=late_rows_check,
+    )
+    _write_json(evidence_dir / "j11-stage-f-execute-preflight-gate.json", preflight_gate)
+    print(f"preflight gate: proceed={preflight_gate['proceed']} reasons={preflight_gate['blocking_reasons']}", file=sys.stderr)
+
+    if not preflight_gate["proceed"]:
+        return _stop("preflight gate did not proceed", preflight_gate, boundary_recheck)
+
+    # === Step 2: pre-write captures =====================================================================
+    with Session(engine) as session:
+        pre_full_table_sweep = j11_maintenance.capture_full_table_sweep(session)
+        pre_manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
+        pre_daily_prices = j11_maintenance.capture_pre_reset_inventory(session)["daily_prices"]
+        pre_provider_runs = jsc.small_table_id_snapshot(session, DataProviderRun)
+        pre_watchlist = jsc.small_table_id_snapshot(session, Watchlist)
+        pre_maintenance_boundary_dump = migration.dump_table(engine, MaintenanceBoundary.__table__)
+
+    print("pre-write captures done", file=sys.stderr)
+
+    # === Step 3: per-table classification (still read-only) ============================================
+    with Session(engine) as session:
+        dispositions = {
+            name: jsfe.classify_cache_table(session, cfg, name, stage_d_start_instant=stage_d_start_instant)
+            for name in inventory["table_names"]
+        }
+    _write_json(evidence_dir / "j11-stage-f-execute-dispositions.json", dispositions)
+    for name, record in dispositions.items():
+        print(f"classification: {name} -> {record['disposition']} ({record['reason'][:120]})", file=sys.stderr)
+
+    unresolved = sorted(
+        name for name, d in dispositions.items()
+        if d["disposition"] in ("blocked_late_row_detected", "unclassified_unknown_family")
+    )
+    if unresolved:
+        outcome = jsfe.stage_f_execution_outcome(
+            preflight_gate=preflight_gate, dispositions=dispositions, execution_result=None,
+            verification_result=None, mutation_accounting=None,
+        )
+        _write_json(evidence_dir / "j11-stage-f-execute-outcome.json", outcome)
+        db_file_true_end = jsc.db_file_fingerprint(db_path)
+        _write_json(evidence_dir / "j11-stage-f-execute-db-file-true-end.json", db_file_true_end)
+        print(f"STOP before any write: unresolved table classification {unresolved}", file=sys.stderr)
+        _print_terminal_lines(outcome, boundary_recheck=boundary_recheck)
+        return 1
+
+    # === Step 4: THE per-table write -- the ONE authorized write sequence ==============================
+    with Session(engine) as session:
+        execution_result = jsfe.execute_stage_f_cache_disposition(session, dispositions=dispositions)
+    _write_json(evidence_dir / "j11-stage-f-execute-execution-result.json", execution_result)
+    print(f"execution: total_rows_deleted={execution_result['total_rows_deleted']}", file=sys.stderr)
+
+    vm_peak_kb = jsee.read_process_vm_peak_kb()
+    memory_check = jsee.build_memory_check(vm_peak_kb=vm_peak_kb, memory_cap_mb=cfg.server.memory_cap_mb)
+    _write_json(evidence_dir / "j11-stage-f-execute-memory-check.json", memory_check)
+    print(f"memory check: vm_peak_mb={memory_check['vm_peak_mb']} within_cap={memory_check['within_cap']}", file=sys.stderr)
+
+    # === Step 5: live, read-only post-write verification ================================================
+    with Session(engine) as session:
+        verification_result = jsfe.live_verify_cache_dispositions(session, dispositions=dispositions)
+    _write_json(evidence_dir / "j11-stage-f-execute-verification-result.json", verification_result)
+    print(f"live verification: ok={verification_result['ok']}", file=sys.stderr)
+
+    # === Step 6: post-write captures + mutation accounting ==============================================
+    with Session(engine) as session:
+        post_full_table_sweep = j11_maintenance.capture_full_table_sweep(session)
+        post_manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
+        post_daily_prices = j11_maintenance.capture_pre_reset_inventory(session)["daily_prices"]
+        post_provider_runs = jsc.small_table_id_snapshot(session, DataProviderRun)
+        post_watchlist = jsc.small_table_id_snapshot(session, Watchlist)
+        post_maintenance_boundary_dump = migration.dump_table(engine, MaintenanceBoundary.__table__)
+
+    db_file_true_end = jsc.db_file_fingerprint(db_path)
+    _write_json(evidence_dir / "j11-stage-f-execute-db-file-true-end.json", db_file_true_end)
+
+    mutation_accounting = jsfe.build_stage_f_mutation_accounting(
... [diff_bound] apps/backend/scripts/run_j11_stage_f_execute.py: 40 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_j11_stage_f_execute.py b/apps/backend/tests/test_j11_stage_f_execute.py
new file mode 100644
index 00000000..57787529
--- /dev/null
+++ b/apps/backend/tests/test_j11_stage_f_execute.py
@@ -0,0 +1,1109 @@
+"""goal-market-compass iter-21 -- J-11 Stage F EXECUTION tests (TC-1 through TC-12, TC-16 from the phase
+spec's TESTING REQUIREMENTS; TC-13/TC-14/TC-15/TC-17/TC-18/TC-19 live in the CLI-script test file / are
+proven by grep in the dev handoff).
+
+File-scoped, fixture-DB-only (fresh `sqlite://` engine, `SQLModel.metadata.create_all`) -- the SAME
+pattern `test_j11_stage_e_execute.py` uses, never `loaded_engine` and never `apps/backend/data/trendora.db`.
+"""
+from __future__ import annotations
+
+import ast
+import json
+from datetime import date, datetime, timedelta, timezone
+from pathlib import Path
+
+import pytest
+from sqlalchemy import event
+from sqlmodel import Session, SQLModel, create_engine, select
+
+from app.config import load_config
+from app.engine import data_manager
+from app.engine import j11_stage_f_execute as jsfe
+from app.engine import research
+from app.engine.j11_maintenance import INCIDENT_DATES
+from app.models import (
+    AvailabilityCache,
+    CoverageSnapshot,
+    DailyPrice,
+    EventStudyCache,
+    ForwardAggregateCache,
+    ForwardReturn,
+    IndexSeriesCache,
+    MarketPhaseCache,
+    MembershipTimelineCache,
+    NextSessionManifest,
+    ScannerResult,
+    ScannerRun,
+)
+
+pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+MODULE_PATH = BACKEND_DIR / "app" / "engine" / "j11_stage_f_execute.py"
+CLI_SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_stage_f_execute.py"
+
+EARLY = datetime(2020, 1, 1, tzinfo=timezone.utc)  # "created well before any repair" -- past the fixture's
+# own Stage D start instant in every test below unless a test deliberately constructs a LATE row.
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
+# --- shared fixture helpers (mirrors test_j11_stage_e_execute.py's idiom) --------------------------
+
+
+def _mk_run(session: Session, asof: date, *, engine_identity_value: "str | None" = "stub-identity", created_at=None) -> ScannerRun:
+    run = ScannerRun(
+        asof_date=asof, created_at=created_at or datetime.now(timezone.utc), provider="seed", benchmark="SPY",
+        regime_score=55.0, regime_label="Expansion", regime_components_json="[]",
+        breadth_above_50dma=50.0, breadth_above_200dma=55.0,
+        new_high_low_json="{}", candidate_counts_json="{}",
+        engine_identity=engine_identity_value,
+    )
+    session.add(run)
+    session.flush()
+    return run
+
+
+def _mk_result(session: Session, run: ScannerRun, ticker: str, rank: int = 1) -> ScannerResult:
+    result = ScannerResult(
+        run_id=run.id, ticker=ticker, name=ticker, sector="Technology",
+        leadership_score=50.0, leadership_bucket="Neutral",
+        entry_quality_score=50.0, entry_quality_bucket="Neutral",
+        risk_score=50.0, risk_bucket="Neutral", setup_status="None", rank=rank,
+        record_json="{}",
+    )
+    session.add(result)
+    session.flush()
+    return result
+
+
+def _mk_forward_return(session: Session, run: ScannerRun, symbol: str, *, horizon: int = 1, measured_date=None) -> ForwardReturn:
+    fr = ForwardReturn(
+        run_id=run.id, symbol=symbol, horizon=horizon, asof_date=run.asof_date,
+        entry_close=100.0, measured_date=measured_date or (run.asof_date + timedelta(days=horizon)),
+        realized_return=0.01,
+    )
+    session.add(fr)
+    session.flush()
+    return fr
+
+
+def _mk_prices(session: Session, symbol: str, start: date, n_days: int, *, price: float = 100.0) -> None:
+    d = start
+    for _ in range(n_days):
+        session.add(DailyPrice(symbol=symbol, date=d, open=price, high=price, low=price, close=price, volume=1000))
+        d = d + timedelta(days=1)
+    session.flush()
+
+
+def _mk_manifest(session: Session, run: ScannerRun, *, version: int = 1) -> NextSessionManifest:
+    manifest = NextSessionManifest(
+        as_of=run.asof_date, version=version, source_run_id=run.id,
+        session_delta_json="{}", narrative_json="{}", selection_json="{}",
+        content_hash="stub-content-hash", created_at=datetime.now(timezone.utc),
+        mode="at_ingest", frozen=True,
+        generation_json=json.dumps({"producer": "ingest_finalize", "engine_identity": "stub-engine-identity"}),
+        engine_identity="stub-engine-identity", manifest_hash="stub-manifest-hash",
+        available_at_utc=datetime.now(timezone.utc), prospective_eligible=True,
+    )
+    session.add(manifest)
+    session.flush()
+    return manifest
+
+
+def _mk_event_study_row(session, *, dataset_version, created_at=EARLY, subject="AAA", view="episodes", asof_key="all", horizon=5):
+    row = EventStudyCache(subject=subject, view=view, asof_key=asof_key, dataset_version=dataset_version, horizon=horizon, payload_json="{}", created_at=created_at)
+    session.add(row); session.flush(); return row
+
+
+def _mk_market_phase_row(session, *, dataset_version, created_at=EARLY, asof_key="2026-01-01"):
+    row = MarketPhaseCache(asof_key=asof_key, dataset_version=dataset_version, payload_json="{}", created_at=created_at)
+    session.add(row); session.flush(); return row
+
+
+def _mk_forward_aggregate_row(session, *, dataset_version, created_at=EARLY, horizon=5, asof_key="2026-01-01"):
+    row = ForwardAggregateCache(horizon=horizon, asof_key=asof_key, dataset_version=dataset_version, payload_json="{}", created_at=created_at)
+    session.add(row); session.flush(); return row
+
+
+def _mk_index_series_row(session, *, dataset_version, created_at=EARLY, range_key="all", full=True):
+    row = IndexSeriesCache(range_key=range_key, full=full, dataset_version=dataset_version, payload_json="{}", created_at=created_at)
+    session.add(row); session.flush(); return row
+
+
+def _mk_membership_timeline_row(session, *, dataset_version, created_at=EARLY, points=None):
+    payload = {"candidate_pool_count": 1, "points": points or [], "labels": {}}
+    row = MembershipTimelineCache(dataset_version=dataset_version, payload_json=json.dumps(payload), created_at=created_at)
+    session.add(row); session.flush(); return row
+
+
+def _mk_availability_row(session, *, dataset_version, created_at=EARLY):
+    payload = {"total_symbols": 3, "trading_day_count": 1, "cells": [{"date": "2026-01-01", "symbols_with_bars": 3, "total_symbols": 3, "snapshot_exists": True}]}
+    row = AvailabilityCache(dataset_version=dataset_version, payload_json=json.dumps(payload), created_at=created_at)
+    session.add(row); session.flush(); return row
+
+
+def _mk_coverage_snapshot_row(session, *, dataset_version, computed_at=EARLY, asof_key="2026-01-01"):
+    row = CoverageSnapshot(asof_key=asof_key, dataset_version=dataset_version, payload_json="{}", computed_at=computed_at)
+    session.add(row); session.flush(); return row
+
+
+# =======================================================================================================
+# TC-19-style static proof: zero network-capable call appears anywhere in the diff
+# =======================================================================================================
+
+_NETWORK_TOKENS = ("requests", "httpx", "urllib", "socket", "yfinance", "aiohttp", "http.client")
+
+
+def _imported_roots(path: Path) -> set[str]:
+    tree = ast.parse(path.read_text())
+    roots: set[str] = set()
+    for node in ast.walk(tree):
+        if isinstance(node, ast.Import):
+            for alias in node.names:
+                roots.add(alias.name.split(".")[0])
+        elif isinstance(node, ast.ImportFrom) and node.module:
+            roots.add(node.module.split(".")[0])
+    return roots
+
+
+def test_module_imports_no_network_capable_library():
+    assert not (_imported_roots(MODULE_PATH) & set(_NETWORK_TOKENS))
+
+
+def test_cli_script_imports_no_network_capable_library():
+    assert not (_imported_roots(CLI_SCRIPT_PATH) & set(_NETWORK_TOKENS))
+
+
+def test_module_never_modifies_a_canonical_producer_or_serving_function():
+    """Static proof this module contains no `def compute_` / `def _compute_` definition of its own for
+    any of the seven canonical derivations it composes -- it only READS them (docs/goal.md OUT OF SCOPE:
+    'Stage F composes and reads them as-is')."""
+    tree = ast.parse(MODULE_PATH.read_text())
+    defined_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
+    forbidden = {
+        "compute_event_study", "compute_market_phase", "compute_forward_aggregates",
+        "_membership_timeline", "compute_availability", "_compute_coverage_uncached", "compute_index_series",
+    }
+    assert not (defined_names & forbidden)
+
+
+# =======================================================================================================
+# TC-3 -- genuine runtime introspection, never a hardcoded list
+# =======================================================================================================
+
+
+def test_tc3_inventory_matches_live_seven_tables():
+    inv = jsfe.derive_cache_table_inventory()
+    assert inv["table_count"] == 7
+    assert inv["table_names"] == sorted(jsfe.EXPECTED_CACHE_TABLE_NAMES)
+    assert inv["matches_expected_seven"] is True
+
+
+def test_tc3_injecting_different_metadata_changes_the_returned_set():
+    """Proves `derive_cache_table_inventory` is genuine introspection, not a hardcoded list wearing an
+    introspection costume: a FRESH, independent `MetaData` containing only a synthetic 8th
+    `dataset_version`-bearing table (and no real cache table at all) makes the function return THAT set,
+    not the real seven."""
+    from sqlalchemy import Column, Integer, MetaData, String, Table
+
+    synthetic_md = MetaData()
+    Table(
+        "eighth_synthetic_cache", synthetic_md,
+        Column("id", Integer, primary_key=True),
+        Column("dataset_version", String),
+    )
+    Table(
+        "unrelated_table_no_stamp", synthetic_md,
+        Column("id", Integer, primary_key=True),
+        Column("name", String),
+    )
+
+    inv = jsfe.derive_cache_table_inventory(metadata=synthetic_md)
+    assert inv["table_names"] == ["eighth_synthetic_cache"]
+    assert inv["table_count"] == 1
+    assert inv["matches_expected_seven"] is False
+
+
+# =======================================================================================================
+# confirm_stage_e_complete_and_unrestamped
+# =======================================================================================================
+
+
+def test_stage_e_check_ok_when_present_matching_id_identity_and_exact_forward_return_count(engine):
+    with Session(engine) as session:
+        run = _mk_run(session, date(2026, 5, 12), engine_identity_value="frozen-id")
+        _mk_forward_return(session, run, "AAA", horizon=1)
+        _mk_forward_return(session, run, "AAA", horizon=5)
+        session.commit()
+        run_id = run.id
+        check = jsfe.confirm_stage_e_complete_and_unrestamped(
+            session,
+            expected_run_id_by_date={"2026-05-12": run_id},
+            expected_forward_return_count_by_run_id={str(run_id): 2},
+            frozen_engine_identity="frozen-id",
+        )
+    assert check["ok"] is True
+    assert check["per_date"]["2026-05-12"]["forward_return_count_matches"] is True
+
+
+def test_stage_e_check_accepts_a_legitimate_zero_count_never_treats_it_as_a_gap(engine):
+    """Mirrors run 3158's own recorded outcome (0 forward returns -- sitting on the frontier)."""
+    with Session(engine) as session:
+        run = _mk_run(session, date(2026, 8, 12), engine_identity_value="frozen-id")
+        session.commit()
+        run_id = run.id
+        check = jsfe.confirm_stage_e_complete_and_unrestamped(
+            session,
+            expected_run_id_by_date={"2026-08-12": run_id},
+            expected_forward_return_count_by_run_id={str(run_id): 0},
+            frozen_engine_identity="frozen-id",
+        )
+    assert check["ok"] is True
+    assert check["per_date"]["2026-08-12"]["observed_forward_return_count"] == 0
+
+
+def test_stage_e_check_fails_when_run_missing(engine):
+    with Session(engine) as session:
+        check = jsfe.confirm_stage_e_complete_and_unrestamped(
+            session, expected_run_id_by_date={"2026-05-12": 999},
+            expected_forward_return_count_by_run_id={"999": 0}, frozen_engine_identity="frozen-id",
+        )
+    assert check["ok"] is False
+    assert check["per_date"]["2026-05-12"]["present"] is False
+
+
+def test_stage_e_check_fails_when_id_does_not_match_expected(engine):
+    with Session(engine) as session:
+        run = _mk_run(session, date(2026, 5, 12), engine_identity_value="frozen-id")
+        session.commit()
+        check = jsfe.confirm_stage_e_complete_and_unrestamped(
+            session, expected_run_id_by_date={"2026-05-12": run.id + 999},
+            expected_forward_return_count_by_run_id={str(run.id + 999): 0}, frozen_engine_identity="frozen-id",
+        )
+    assert check["ok"] is False
+
+
+def test_stage_e_check_fails_when_identity_does_not_match(engine):
+    with Session(engine) as session:
+        run = _mk_run(session, date(2026, 5, 12), engine_identity_value="drifted-id")
+        session.commit()
+        check = jsfe.confirm_stage_e_complete_and_unrestamped(
+            session, expected_run_id_by_date={"2026-05-12": run.id},
+            expected_forward_return_count_by_run_id={str(run.id): 0}, frozen_engine_identity="frozen-id",
+        )
+    assert check["ok"] is False
+    assert check["per_date"]["2026-05-12"]["identity_matches"] is False
+
+
+def test_stage_e_check_fails_when_forward_return_count_mismatched(engine):
+    with Session(engine) as session:
+        run = _mk_run(session, date(2026, 5, 12), engine_identity_value="frozen-id")
+        _mk_forward_return(session, run, "AAA", horizon=1)
+        session.commit()
+        check = jsfe.confirm_stage_e_complete_and_unrestamped(
+            session, expected_run_id_by_date={"2026-05-12": run.id},
+            expected_forward_return_count_by_run_id={str(run.id): 999}, frozen_engine_identity="frozen-id",
+        )
+    assert check["ok"] is False
+    assert check["per_date"]["2026-05-12"]["forward_return_count_matches"] is False
+
+
+def test_stage_e_check_fails_closed_on_empty_expected_map(engine):
+    with Session(engine) as session:
+        check = jsfe.confirm_stage_e_complete_and_unrestamped(
+            session, expected_run_id_by_date={}, expected_forward_return_count_by_run_id={}, frozen_engine_identity="x",
+        )
+    assert check["ok"] is False
+
+
+# =======================================================================================================
+# derive_stage_d_execution_start_instant
+# =======================================================================================================
+
+
+def test_derive_stage_d_start_instant_is_min_created_at_over_given_ids_only(engine):
+    with Session(engine) as session:
+        early = datetime(2026, 1, 1, tzinfo=timezone.utc)
+        mid = datetime(2026, 1, 2, tzinfo=timezone.utc)
+        late = datetime(2026, 1, 3, tzinfo=timezone.utc)
+        r1 = _mk_run(session, date(2026, 1, 1), created_at=mid)
+        r2 = _mk_run(session, date(2026, 1, 2), created_at=early)
+        r3_not_in_set = _mk_run(session, date(2026, 1, 3), created_at=datetime(2020, 1, 1, tzinfo=timezone.utc))
+        session.commit()
+        r1_id, r2_id, r3_id = r1.id, r2.id, r3_not_in_set.id
+        result = jsfe.derive_stage_d_execution_start_instant(session, [r1_id, r2_id])
+    assert result["stage_d_execution_start_instant"] == early.isoformat()
+    assert r3_id not in result["incident_run_ids"]
+
+
+# =======================================================================================================
+# capture_cache_table_snapshot -- generic across created_at / computed_at
+# =======================================================================================================
+
+
+def test_snapshot_reads_created_at_column_for_event_study_cache(engine):
+    with Session(engine) as session:
+        _mk_event_study_row(session, dataset_version="r1-f0", created_at=EARLY)
+        _mk_event_study_row(session, dataset_version="r2-f0", created_at=EARLY + timedelta(days=1), subject="BBB")
+        session.commit()
+        snap = jsfe.capture_cache_table_snapshot(session, "event_study_cache")
+    assert snap["timestamp_column"] == "created_at"
+    assert snap["row_count"] == 2
+    assert {s["dataset_version"] for s in snap["distinct_stamps"]} == {"r1-f0", "r2-f0"}
+    assert snap["max_timestamp"] == (EARLY + timedelta(days=1)).isoformat()
+
+
+def test_snapshot_reads_computed_at_column_for_coverage_snapshot(engine):
+    with Session(engine) as session:
+        _mk_coverage_snapshot_row(session, dataset_version="r1-x", computed_at=EARLY)
+        session.commit()
+        snap = jsfe.capture_cache_table_snapshot(session, "coverage_snapshot")
+    assert snap["timestamp_column"] == "computed_at"
+    assert snap["row_count"] == 1
+    assert snap["max_timestamp"] == EARLY.isoformat()
+
+
+def test_snapshot_honest_empty_on_zero_rows(engine):
+    with Session(engine) as session:
+        snap = jsfe.capture_cache_table_snapshot(session, "availability_cache")
+    assert snap["row_count"] == 0
+    assert snap["distinct_stamps"] == []
+    assert snap["max_timestamp"] is None
+
+
+# =======================================================================================================
+# confirm_no_cache_row_at_or_after_stage_d_start -- the "gravest" check
+# =======================================================================================================
... [diff_bound] apps/backend/tests/test_j11_stage_f_execute.py: 715 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_j11_stage_f_execute_cli_script.py b/apps/backend/tests/test_j11_stage_f_execute_cli_script.py
new file mode 100644
index 00000000..a49a480c
--- /dev/null
+++ b/apps/backend/tests/test_j11_stage_f_execute_cli_script.py
@@ -0,0 +1,458 @@
+"""goal-market-compass iter-21 -- J-11 Stage F EXECUTION CLI control-flow tests
+(`scripts/run_j11_stage_f_execute.py`), TC-13/TC-14/TC-15 plus the stop-before-write control-flow proofs.
+
+`unittest.mock`-based, NEVER a live DB -- every DB-touching name (`get_engine`, `Session`, and every
+`jsfe.*`/`jsde.*`/`jsee.*`/`j11_maintenance.*`/`migration.*`/`jsc.*` function the script calls) is patched
+to a mock before `main()` runs, mirroring `test_j11_stage_e_execute_cli_script.py`'s exact idiom -- these
+tests exercise CONTROL FLOW only (which functions get called, in what order, and which never get called),
+never real database I/O.
+"""
+from __future__ import annotations
+
+import importlib.util
+import json
+import sys
+from pathlib import Path
+from unittest import mock
+
+import pytest
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_stage_f_execute.py"
+_MODULE_NAME = "run_j11_stage_f_execute_under_test"
+
+
+def _load_script_module():
+    """Mirrors `test_j11_stage_e_execute_cli_script.py`'s own loader exactly -- a REAL module object via
+    `importlib` (never `runpy.run_path`), so `monkeypatch.setattr(module, name, mock)` genuinely
+    intercepts every call the script's top-level code makes to that name."""
+    spec = importlib.util.spec_from_file_location(_MODULE_NAME, SCRIPT_PATH)
+    module = importlib.util.module_from_spec(spec)
+    sys.modules[_MODULE_NAME] = module
+    spec.loader.exec_module(module)
+    return module
+
+
+@pytest.fixture()
+def script_ns():
+    original_argv = sys.argv
+    try:
+        module = _load_script_module()
+        yield module
+    finally:
+        sys.argv = original_argv
+        sys.modules.pop(_MODULE_NAME, None)
+
+
+# --- TC-14: missing --confirm -- NO database interaction of any kind ----------------------------------
+
+
+def test_missing_confirm_never_calls_get_engine_or_session(monkeypatch, script_ns):
+    mock_get_engine = mock.MagicMock(name="get_engine")
+    mock_session_cls = mock.MagicMock(name="Session")
+    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
+    monkeypatch.setattr(script_ns, "Session", mock_session_cls)
+    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))
+    monkeypatch.setattr(sys, "argv", ["run_j11_stage_f_execute.py"])  # no --confirm
+
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mock_get_engine.assert_not_called()
+    mock_session_cls.assert_not_called()
+
+
+# --- TC-14: --confirm but no --evidence-dir -- refuses, writes nothing anywhere -----------------------
+
+
+def test_confirm_without_explicit_evidence_dir_refuses_before_writing_anything(monkeypatch, script_ns, capsys):
+    mock_write_json = mock.MagicMock(name="_write_json")
+    monkeypatch.setattr(script_ns, "_write_json", mock_write_json)
+    mock_get_engine = mock.MagicMock(name="get_engine")
+    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
+    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(name="Session"))
+    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))
+
+    monkeypatch.setattr(sys, "argv", ["run_j11_stage_f_execute.py", "--confirm"])
+
+    exit_code = script_ns.main()
+
+    assert exit_code == 2
+    mock_write_json.assert_not_called()
+    mock_get_engine.assert_not_called()
+    assert "--evidence-dir" in capsys.readouterr().err
+
+
+# --- collision guard: a pre-existing output file refuses before any DB interaction ----------------------
+
+
+def test_collision_guard_refuses_before_any_db_interaction(monkeypatch, script_ns, tmp_path, capsys):
+    evidence_dir = tmp_path / "evidence"
+    evidence_dir.mkdir()
+    (evidence_dir / "j11-stage-f-execute-outcome.json").write_text("{}")  # a prior run's leftover
+
+    mock_get_engine = mock.MagicMock(name="get_engine")
+    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
+    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(name="Session"))
+    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))
+
+    monkeypatch.setattr(
+        sys, "argv",
+        ["run_j11_stage_f_execute.py", "--confirm", "--evidence-dir", str(evidence_dir)],
+    )
+
+    exit_code = script_ns.main()
+
+    assert exit_code == 2
+    mock_get_engine.assert_not_called()
+    assert "already contains" in capsys.readouterr().err
+
+
+# --- shared happy-path mock rig, so individual tests only override ONE piece --------------------------
+
+
+def _install_happy_path_mocks(monkeypatch, script_ns, *, evidence_dir: Path):
+    """Patches every DB-touching / expensive name the script calls to a deterministic, fully-successful
+    default. Returns a dict of the individual mocks so a test can override exactly one to prove a
+    specific stop-before-write control-flow property. Mirrors Stage E's CLI test rig: the LEAF checks are
+    mocked, but the REAL `jsfe.stage_f_execution_outcome` composition logic runs (already separately
+    unit-tested for its own correctness in `test_j11_stage_f_execute.py`)."""
+    mock_engine = mock.MagicMock(name="engine")
+    monkeypatch.setattr(script_ns, "get_engine", mock.MagicMock(return_value=mock_engine))
+
+    mock_session_instance = mock.MagicMock(name="session_instance")
+    mock_session_instance.scalar = mock.MagicMock(return_value=100)
+    mock_session_cm = mock.MagicMock()
+    mock_session_cm.__enter__ = mock.MagicMock(return_value=mock_session_instance)
+    mock_session_cm.__exit__ = mock.MagicMock(return_value=False)
+    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(return_value=mock_session_cm))
+
+    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={"exists": False}))
+    monkeypatch.setattr(
+        script_ns.jsc, "small_table_id_snapshot", mock.MagicMock(return_value={"count": 0, "ids": []}),
+    )
+
+    mock_boundary_recheck = mock.MagicMock(
+        name="recheck_maintenance_boundary_and_guard",
+        return_value={"ok": True, "boundary_active": True, "all_dates_blocked": True},
+    )
+    monkeypatch.setattr(script_ns.jsde, "recheck_maintenance_boundary_and_guard", mock_boundary_recheck)
+
+    mock_stage_e_check = mock.MagicMock(
+        name="confirm_stage_e_complete_and_unrestamped", return_value={"ok": True, "per_date": {}},
+    )
+    monkeypatch.setattr(script_ns.jsfe, "confirm_stage_e_complete_and_unrestamped", mock_stage_e_check)
+
+    monkeypatch.setattr(
+        script_ns.engine_identity, "compute_engine_identity", mock.MagicMock(return_value="fresh-identity-value"),
+    )
+    mock_identity_check = mock.MagicMock(
+        name="check_engine_identity_matches_stage_d", return_value={"ok": True, "matches": True},
+    )
+    monkeypatch.setattr(script_ns.jsee, "check_engine_identity_matches_stage_d", mock_identity_check)
+
+    mock_manifest_check = mock.MagicMock(name="confirm_manifests_unchanged", return_value={"ok": True})
+    monkeypatch.setattr(script_ns.jsee, "confirm_manifests_unchanged", mock_manifest_check)
+
+    mock_inventory = mock.MagicMock(
+        name="derive_cache_table_inventory",
+        return_value={
+            "table_names": ["event_study_cache", "index_series_cache"], "table_count": 2,
+            "expected_table_names": ["event_study_cache", "index_series_cache"], "matches_expected_seven": True,
+        },
+    )
+    monkeypatch.setattr(script_ns.jsfe, "derive_cache_table_inventory", mock_inventory)
+
+    mock_start_instant = mock.MagicMock(
+        name="derive_stage_d_execution_start_instant",
+        return_value={"stage_d_execution_start_instant": "2026-01-01T00:00:00+00:00", "incident_run_ids": [1, 2]},
+    )
+    monkeypatch.setattr(script_ns.jsfe, "derive_stage_d_execution_start_instant", mock_start_instant)
+
+    monkeypatch.setattr(
+        script_ns.jsfe, "capture_cache_table_snapshot",
+        mock.MagicMock(return_value={"table_name": "x", "timestamp_column": "created_at", "row_count": 0, "distinct_stamps": [], "max_timestamp": None}),
+    )
+
+    mock_late_rows_check = mock.MagicMock(
+        name="confirm_no_cache_row_at_or_after_stage_d_start", return_value={"ok": True, "per_table": {}},
+    )
+    monkeypatch.setattr(script_ns.jsfe, "confirm_no_cache_row_at_or_after_stage_d_start", mock_late_rows_check)
+
+    mock_gate_verdict = mock.MagicMock(
+        name="stage_f_preflight_gate_verdict", return_value={"proceed": True, "blocking_reasons": []},
+    )
+    monkeypatch.setattr(script_ns.jsfe, "stage_f_preflight_gate_verdict", mock_gate_verdict)
+
+    monkeypatch.setattr(script_ns.j11_maintenance, "capture_full_table_sweep", mock.MagicMock(return_value={}))
+    monkeypatch.setattr(script_ns.migration, "dump_table", mock.MagicMock(return_value=[]))
+    monkeypatch.setattr(
+        script_ns.j11_maintenance, "capture_pre_reset_inventory",
+        mock.MagicMock(return_value={"daily_prices": {"fingerprint": "p"}}),
+    )
+
+    mock_classify = mock.MagicMock(
+        name="classify_cache_table",
+        return_value={"disposition": "explicit_delete", "reason": "stale", "snapshot": {"row_count": 5}, "table_name": "x"},
+    )
+    monkeypatch.setattr(script_ns.jsfe, "classify_cache_table", mock_classify)
+
+    mock_execute = mock.MagicMock(
+        name="execute_stage_f_cache_disposition",
+        return_value={"total_rows_deleted": 5, "per_table": {}},
+    )
+    monkeypatch.setattr(script_ns.jsfe, "execute_stage_f_cache_disposition", mock_execute)
+
+    monkeypatch.setattr(script_ns.jsee, "read_process_vm_peak_kb", mock.MagicMock(return_value=500_000))
+    monkeypatch.setattr(
+        script_ns.jsee, "build_memory_check",
+        mock.MagicMock(return_value={"vm_peak_mb": 488.3, "within_cap": True}),
+    )
+
+    mock_verify = mock.MagicMock(
+        name="live_verify_cache_dispositions", return_value={"ok": True, "per_table": {}},
+    )
+    monkeypatch.setattr(script_ns.jsfe, "live_verify_cache_dispositions", mock_verify)
+
+    mock_mutation_accounting = mock.MagicMock(
+        name="build_stage_f_mutation_accounting",
+        return_value={"all_checks_pass": True, "checks": {}},
+    )
+    monkeypatch.setattr(script_ns.jsfe, "build_stage_f_mutation_accounting", mock_mutation_accounting)
+
+    fake_frozen_identity_path = evidence_dir.parent / "frozen-identity.json"
+    fake_frozen_identity_path.write_text(json.dumps({"engine_identity": "fresh-identity-value"}))
+    fake_regeneration_path = evidence_dir.parent / "regeneration.json"
+    fake_regeneration_path.write_text(json.dumps({"per_date_results": [
+        {"date": "2026-05-12", "run_id": 3148}, {"date": "2026-05-13", "run_id": 3149},
+    ]}))
+    fake_population_report_path = evidence_dir.parent / "population-report.json"
+    fake_population_report_path.write_text(json.dumps({"population_a_rebuilt_incident_runs": {
+        "3148": {"pre": 0, "post": 10, "newly_inserted": 10}, "3149": {"pre": 0, "post": 0, "newly_inserted": 0},
+    }}))
+    fake_certified_path = evidence_dir.parent / "certified.json"
+    fake_certified_path.write_text(json.dumps({"manifest_dump": []}))
+
+    return {
+        "boundary_recheck": mock_boundary_recheck,
+        "stage_e_check": mock_stage_e_check,
+        "identity_check": mock_identity_check,
+        "manifest_check": mock_manifest_check,
+        "inventory": mock_inventory,
+        "start_instant": mock_start_instant,
+        "late_rows_check": mock_late_rows_check,
+        "gate_verdict": mock_gate_verdict,
+        "classify": mock_classify,
+        "execute": mock_execute,
+        "verify": mock_verify,
+        "mutation_accounting": mock_mutation_accounting,
+        "frozen_identity_path": fake_frozen_identity_path,
+        "regeneration_path": fake_regeneration_path,
+        "population_report_path": fake_population_report_path,
+        "certified_path": fake_certified_path,
+    }
+
+
+def _argv(evidence_dir: Path, mocks: dict) -> list[str]:
+    return [
+        "run_j11_stage_f_execute.py", "--confirm",
+        "--evidence-dir", str(evidence_dir),
+        "--stage-d-frozen-identity-path", str(mocks["frozen_identity_path"]),
+        "--stage-d-regeneration-path", str(mocks["regeneration_path"]),
+        "--stage-e-population-report-path", str(mocks["population_report_path"]),
+        "--certified-baseline-path", str(mocks["certified_path"]),
+    ]
+
+
+# --- preflight gate refusing to proceed -- classification/execution NEVER reached ----------------------
+
+
+def test_preflight_gate_not_proceed_never_calls_classify_or_execute(monkeypatch, script_ns, tmp_path):
+    evidence_dir = tmp_path / "evidence"
+    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
+    mocks["gate_verdict"].return_value = {"proceed": False, "blocking_reasons": ["engine_identity_drifted_since_stage_d"]}
+
+    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks))
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mocks["classify"].assert_not_called()
+    mocks["execute"].assert_not_called()
+    outcome = json.loads((evidence_dir / "j11-stage-f-execute-outcome.json").read_text())
+    assert outcome["executed"] is False
+    assert outcome["reason"] == "preflight_gate_did_not_proceed"
+
+
+# --- an unresolved classification (a late row, or an unknown table) stops BEFORE the write --------------
+
+
+def test_unresolved_classification_never_calls_execute(monkeypatch, script_ns, tmp_path):
+    evidence_dir = tmp_path / "evidence"
+    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
+    mocks["classify"].return_value = {
+        "disposition": "blocked_late_row_detected", "reason": "late row", "snapshot": {"row_count": 1}, "table_name": "x",
+    }
+
+    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks))
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mocks["execute"].assert_not_called()
+    outcome = json.loads((evidence_dir / "j11-stage-f-execute-outcome.json").read_text())
+    assert outcome["executed"] is False
+    assert outcome["reason"] == "unresolved_table_classification"
+
+
+# --- failed post-execution mutation accounting -- outcome STILL written, exit non-zero -------------------
+
+
+def test_failed_mutation_accounting_writes_outcome_executed_false_and_returns_nonzero(monkeypatch, script_ns, tmp_path):
+    evidence_dir = tmp_path / "evidence"
+    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
+    mocks["mutation_accounting"].return_value = {"all_checks_pass": False, "checks": {"daily_prices_unchanged": False}}
+
+    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks))
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    mocks["execute"].assert_called_once()  # the gate passed, so the write DID run this time...
+    outcome_path = evidence_dir / "j11-stage-f-execute-outcome.json"
+    assert outcome_path.exists()  # ...but the outcome is STILL persisted either way
+    outcome = json.loads(outcome_path.read_text())
+    assert outcome["executed"] is False
+    assert outcome["reason"] == "post_execution_mutation_accounting_failed"
+
+
+# --- failed live verification -- outcome executed=False, exact reason -----------------------------------
+
+
+def test_failed_live_verification_writes_outcome_executed_false(monkeypatch, script_ns, tmp_path):
+    evidence_dir = tmp_path / "evidence"
+    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
+    mocks["verify"].return_value = {"ok": False, "per_table": {}}
+
+    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks))
+    exit_code = script_ns.main()
+
+    assert exit_code != 0
+    outcome = json.loads((evidence_dir / "j11-stage-f-execute-outcome.json").read_text())
+    assert outcome["executed"] is False
+    assert outcome["reason"] == "post_execution_live_verification_failed"
+
+
+# --- the full successful path: exit 0, outcome executed=True, every declared file written ---------------
+
+
+def test_successful_full_path_returns_zero_and_writes_outcome_executed_true(monkeypatch, script_ns, tmp_path):
+    evidence_dir = tmp_path / "evidence"
+    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
+
+    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks))
+    exit_code = script_ns.main()
+
+    assert exit_code == 0
+    mocks["execute"].assert_called_once()
+    assert mocks["classify"].call_count == 2  # once per inventoried table name
+    outcome = json.loads((evidence_dir / "j11-stage-f-execute-outcome.json").read_text())
+    assert outcome["executed"] is True
+    for name in script_ns.OUTPUT_FILENAMES:
+        assert (evidence_dir / name).exists(), f"missing evidence file {name}"
+
+
+# --- terminal vocabulary -- exact required lines, both outcomes -----------------------------------------
+
+
+def test_terminal_lines_success(monkeypatch, script_ns, tmp_path, capsys):
+    evidence_dir = tmp_path / "evidence"
+    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
+    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks))
+
+    script_ns.main()
+    err = capsys.readouterr().err
+
+    assert "J-11 STAGE D EXECUTED: YES" in err
+    assert "J-11 STAGE E COMPLETE: YES" in err
+    assert "J-11 STAGE F COMPLETE: YES" in err
+    assert "J-11 STAGE G VERIFIED: NO" in err
+    assert "J-11 INCIDENT STATUS: NOT REPAIRED" in err
+    assert "J-11 MAINTENANCE BOUNDARY: ACTIVE" in err
+    assert "J-11 LIVE PRE-BOOT GUARD: ARMED" in err
+
+
+def test_terminal_lines_blocked_at_preflight(monkeypatch, script_ns, tmp_path, capsys):
+    evidence_dir = tmp_path / "evidence"
+    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
+    mocks["gate_verdict"].return_value = {"proceed": False, "blocking_reasons": ["x"]}
+    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks))
+
+    script_ns.main()
+    err = capsys.readouterr().err
+
+    assert "J-11 STAGE D EXECUTED: YES" in err
+    assert "J-11 STAGE E COMPLETE: YES" in err
+    assert "J-11 STAGE F COMPLETE: NO" in err
+    assert "J-11 MAINTENANCE BOUNDARY: ACTIVE" in err
... [diff_bound] apps/backend/tests/test_j11_stage_f_execute_cli_script.py: 64 more diff lines omitted — Read the file for full detail
```
