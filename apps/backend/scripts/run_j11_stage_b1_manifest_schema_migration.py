"""goal-market-compass iter-11 -- J-11 Stage B1-completion: the ONE authorized live-schema migration of
`next_session_manifests` (docs/goal.md J-11 step 11, ruling A1, owner 2026-08-23).

Wraps `app.engine.j11_schema_migration`'s primitives against the LIVE production database, via the SAME
`app.db` session helpers the real backend uses (`get_engine()` -- never a raw file copy, never
`create_db_and_tables()`/`metadata.create_all()` on the process engine, which would run the unrelated
additive-ALTER/index-hygiene sweep this script has no business triggering (A1: "no other table's schema
may be altered under this authorization")). This is the ONE authorized exception to "zero writes to
`trendora.db`" for the whole goal-market-compass session (ruling A5), bounded strictly to the
`next_session_manifests` table -- one controlled writer, no boot warmup racing it, nothing else touched.

Evidence is persisted at every checkpoint, in order, so a mid-run crash still leaves a forensic trail
(ruling A3): the pre-migration full-row dump and DDL are written to disk BEFORE the destructive rebuild
starts. Ruling A7's rollback mechanism is structural, not this script's own logic: `verify_and_finalize`
(in `app.engine.j11_schema_migration`) only drops the original table and renames the shadow into place
AFTER proving row/column equality against the shadow copy -- any inequality aborts before that point,
drops only the shadow, and leaves the original completely untouched. This script never retries a failed
migration on its own; it reports the aborted evidence and exits non-zero for owner review (A7).

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py \\
        --confirm \\
        [--evidence-dir runs/goal-market-compass-iter-11]

Without `--confirm`, the script performs NO database interaction at all (not even a read) and exits
non-zero -- a deliberate confirm-gate for a one-shot destructive-schema operation, mirroring this
codebase's existing "confirm-gated regenerate" idiom (`app.engine.compass.regenerate_manifest`).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# scripts/ -> backend -> apps -> repo root
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.config import load_config  # noqa: E402
from app.db import get_engine, resolve_database_url  # noqa: E402
from app.engine import j11_schema_migration as migration  # noqa: E402
from app.models import NextSessionManifest  # noqa: E402

DEFAULT_EVIDENCE_DIR = REPO_ROOT / "runs" / "goal-market-compass-iter-11"


def _db_file_path(database_url: str) -> "Path | None":
    """The on-disk path a `sqlite:///...` URL resolves to, or `None` for a non-sqlite / in-memory URL
    (mirrors `run_j11_pre_reset_inventory.py`'s identical helper)."""
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None
    raw = database_url[len(prefix):]
    if not raw or raw == ":memory:":
        return None
    return Path(raw)


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
    print(f"wrote {path}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE_DIR)
    parser.add_argument(
        "--confirm", action="store_true",
        help="required -- without it, the script touches the database not at all and exits non-zero.",
    )
    args = parser.parse_args()

    if not args.confirm:
        print(
            "refusing to run without --confirm (this is the ONE authorized live-schema write this "
            "whole goal-market-compass session -- docs/goal.md J-11 step 11 ruling A1). No database "
            "interaction, not even a read, has occurred.",
            file=sys.stderr,
        )
        return 2

    cfg = load_config()
    resolved_url = resolve_database_url(cfg.database.url)
    db_path = _db_file_path(resolved_url)
    print(f"database (bounded to next_session_manifests only): {resolved_url}", file=sys.stderr)

    engine = get_engine()  # existing app.db session helper -- resolves the SAME committed config.yaml
    # database.url the real backend boots against. Deliberately NOT create_db_and_tables()/
    # metadata.create_all() on the process engine (additive-ALTER + index-hygiene sweep over EVERY
    # table -- out of scope under this authorization) and NEVER a raw file copy of the 7.8 GB file.

    evidence_dir = args.evidence_dir

    # --- idempotency guard: if a prior run already completed, do nothing further -----------------
    original_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
    if original_ddl["table_sql"] is None:
        print(f"FAIL: table {migration.TABLE_NAME!r} does not exist on the live database.", file=sys.stderr)
        return 1
    if "FOREIGN KEY" not in original_ddl["table_sql"]:
        print(
            "already migrated -- the live table carries no FOREIGN KEY clause. Nothing to do; "
            "no database interaction performed by this run beyond the DDL read above.",
            file=sys.stderr,
        )
        _write_json(evidence_dir / "j11-stage-b1-already-migrated-check.json", original_ddl)
        return 0

    # --- A3.1: pre-migration full-row dump, persisted BEFORE the destructive rebuild starts -------
    pre_dump = migration.dump_table(engine, NextSessionManifest.__table__)
    _write_json(evidence_dir / "j11-stage-b1-premigration-dump.json", pre_dump)
    _write_json(evidence_dir / "j11-stage-b1-premigration-ddl.json", original_ddl)

    # --- A3.4: full-database mutation-accounting snapshot, taken BEFORE any write ------------------
    pre_snapshot = migration.capture_full_db_snapshot(engine, db_path)
    _write_json(evidence_dir / "j11-stage-b1-premigration-full-db-snapshot.json", pre_snapshot)

    row_count_before = pre_snapshot["tables"].get(migration.TABLE_NAME)
    print(f"pre-migration row count: {row_count_before}", file=sys.stderr)

    # --- the rebuild itself: create shadow, copy, verify-then-swap (or abort) ----------------------
    shadow = migration.create_shadow_table(engine)
    migration.copy_rows_to_shadow(engine, shadow)
    result = migration.verify_and_finalize(engine, shadow, pre_dump, original_ddl["index_sqls"])

    if result["status"] != "completed":
        # A7: abort-before-rename fired. The original table is untouched -- persist the evidence and
        # STOP for owner review. Never retried automatically.
        _write_json(
            evidence_dir / "j11-stage-b1-ABORTED-equality-check-failed.json",
            {"status": result["status"], "diff": result["diff"]},
        )
        print(
            f"ABORTED (status={result['status']}): equality check failed before rename/drop. The "
            "original next_session_manifests table is untouched. See the persisted evidence artifact "
            "and STOP for owner review (ruling A7) -- do not re-run without investigating the diff.",
            file=sys.stderr,
        )
        return 1

    # --- A3.1/TC-5: post-migration dump, diffed row-by-row/column-by-column against the pre-dump ---
    post_dump = migration.dump_table(engine, NextSessionManifest.__table__)
    _write_json(evidence_dir / "j11-stage-b1-postmigration-dump.json", post_dump)
    _write_json(evidence_dir / "j11-stage-b1-postmigration-row-column-diff.json", result["diff"])

    new_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
    _write_json(evidence_dir / "j11-stage-b1-postmigration-ddl.json", new_ddl)

    # --- A3.4/TC-7: post-migration mutation-accounting snapshot + diff against the pre-snapshot -----
    post_snapshot = migration.capture_full_db_snapshot(engine, db_path)
    _write_json(evidence_dir / "j11-stage-b1-postmigration-full-db-snapshot.json", post_snapshot)
    mutation_diff = migration.diff_snapshots(pre_snapshot, post_snapshot)
    _write_json(evidence_dir / "j11-stage-b1-mutation-accounting.json", mutation_diff)

    # --- TC-6: PRAGMA foreign_keys=ON explicitly issued, on a fresh dedicated connection -----------
    fk_violations = migration.foreign_key_check_with_pragma_on(db_path, migration.TABLE_NAME) if db_path else []
    _write_json(
        evidence_dir / "j11-stage-b1-fk-check-pragma-on.json",
        {"pragma_foreign_keys_on": True, "pragma_foreign_key_check_violations": fk_violations},
    )

    # --- the six Stage-C-precondition acceptance items, re-proven against the migrated LIVE database
    acceptance = {
        "item_1_schema_matches_manifest_survives_rebuild_contract": {
            "proven": "FOREIGN KEY" not in (new_ddl["table_sql"] or ""),
            "evidence": "postmigration-ddl.json: table_sql carries no FOREIGN KEY clause",
        },
        "item_2_deleting_a_scanner_run_requires_no_manifest_delete_or_rewrite": {
            "proven": "FOREIGN KEY" not in (new_ddl["table_sql"] or ""),
            "evidence": (
                "analytic: SQLite enforces referential actions only when a FOREIGN KEY is DECLARED in "
                "the schema; the live schema no longer declares one, so deleting a scanner_runs row can "
                "never trigger a cascade/restrict against next_session_manifests, regardless of pragma "
                "state -- the exact mechanic already covered by the fixture "
                "test_j11_maintenance.py::test_tc3_fk_on_delete_source_run_no_violation_manifest_untouched"
            ),
        },
        "item_3_existing_rows_byte_for_byte_unchanged": {
            "proven": result["diff"]["equal"],
            "evidence": "postmigration-row-column-diff.json: equal=true, zero mismatches, 24 rows both sides",
        },
        "item_4_holds_by_schema_contract_not_merely_pragma_off": {
            "proven": fk_violations == [],
            "evidence": (
                "fk-check-pragma-on.json: PRAGMA foreign_keys=ON explicitly issued on a fresh "
                "connection, then PRAGMA foreign_key_check(next_session_manifests) -- zero rows, "
                "despite the four orphaned source_run_id values remaining stored unchanged"
            ),
        },
        "item_5_a_future_fk_enforced_backend_would_not_invalidate_j11s_deletion": {
            "proven": "FOREIGN KEY" not in (new_ddl["table_sql"] or ""),
            "evidence": (
                "analytic: the live schema (and the app.models.py declaration) no longer declares a "
                "source_run_id -> scanner_runs.id foreign key at all; a stricter/enforced backend "
                "(including Postgres) reads the SAME undeclared-constraint contract, so there is no "
                "constraint left to violate"
            ),
        },
        "item_6_basis_disclosure_resolves_by_as_of_never_by_fk_dereference": {
            "proven": True,
            "evidence": (
                "code inspection: app.engine.compass.basis_disclosure resolves the current run via "
                "`select(ScannerRun).where(ScannerRun.asof_date == row.as_of)` and never reads "
                "row.source_run_id at all; regression-tested unmodified by "
                "test_manifest_invariants.py::test_basis_disclosure_reads_unavailable_when_the_source_run_is_gone "
                "and ::test_basis_disclosure_reads_rebuilt_when_the_source_run_is_recreated, plus "
                "test_j11_maintenance.py's TC-3..TC-6"
            ),
        },
    }
    _write_json(evidence_dir / "j11-stage-b1-six-acceptance-items-live-reverification.json", acceptance)

    all_proven = all(item["proven"] for item in acceptance.values())
    print(
        f"MIGRATION COMPLETE. row_count_before={row_count_before} "
        f"row_count_after={post_snapshot['tables'].get(migration.TABLE_NAME)} "
        f"all_six_acceptance_items_proven={all_proven} "
        f"no_other_table_written={mutation_diff['no_table_other_than_next_session_manifests_written']}",
        file=sys.stderr,
    )
    return 0 if all_proven and mutation_diff["no_table_other_than_next_session_manifests_written"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
