"""goal-market-compass iter-11 -- J-11 Stage B1-completion: fixture-DB-only tests for the
`next_session_manifests` schema-migration rebuild mechanics (`app.engine.j11_schema_migration`),
docs/goal.md J-11 step 11 ruling A1 / TC-1, TC-2, TC-8.

File-scoped, fixture-DB-only -- a fresh on-disk SQLite file per test (never the live 7.8 GB
`trendora.db`, per `.claude/project-template.md`'s "never copy/open-for-write the live DB" rule and
this iteration's own plan). The fixture DB is built with the LIVE table's EXACT current DDL (the
`FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)` clause included, captured verbatim from
`apps/backend/data/trendora.db`'s own `sqlite_master` on 2026-08-23) -- never `SQLModel.metadata.
create_all()`, which would build the already-FK-free CURRENT model shape and could never reproduce the
"before" state this migration exists to fix.

Test-name collision note (iteration-11 plan): `test_j11_maintenance.py` already owns TC-3..TC-7 as ITS
OWN literal function names for iter-10's different scenarios (FK-on delete / rebuilt-same-as_of /
degenerate orphan / id-reuse / attempt-identity). This file's tests cover THIS iteration's own
Test-first-contract TC-1, TC-2, and TC-8 (the fixture-level items) under distinct function names --
nothing here renames or touches iter-10's existing tests.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.engine import j11_schema_migration as migration
from app.models import NextSessionManifest

# Captured verbatim from `apps/backend/data/trendora.db`'s `sqlite_master` on 2026-08-23 (read-only
# query) -- the live table's CURRENT (pre-migration) DDL, FOREIGN KEY clause included. Deliberately
# hand-written here ONLY as a fixture input simulating the "before" state -- the production migration
# code itself never hand-writes DDL (see `j11_schema_migration.py`'s module docstring).
_LIVE_TABLE_DDL_WITH_FK = """
CREATE TABLE next_session_manifests (
	id INTEGER NOT NULL,
	as_of DATE NOT NULL,
	source_run_id INTEGER NOT NULL,
	session_delta_json VARCHAR NOT NULL,
	narrative_json VARCHAR NOT NULL,
	selection_json VARCHAR NOT NULL,
	content_hash VARCHAR NOT NULL,
	created_at DATETIME NOT NULL, version INTEGER NOT NULL DEFAULT 1, mode VARCHAR, frozen BOOLEAN NOT NULL DEFAULT 0, generation_json VARCHAR, engine_identity VARCHAR, candidate_rule_hash VARCHAR, candidate_rule_config_json VARCHAR, cohort_rule_hash VARCHAR, cohort_rule_config_json VARCHAR, manifest_config_hash VARCHAR, manifest_config_subset_json VARCHAR, dataset_json VARCHAR, universe_json VARCHAR, comparison_cohort_json VARCHAR, near_threshold_shadow_json VARCHAR, caveats_json VARCHAR, prospective_eligible BOOLEAN NOT NULL DEFAULT 0, available_at_utc DATETIME, manifest_hash VARCHAR, export_path VARCHAR,
	PRIMARY KEY (id),
	FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)
)
"""
_LIVE_INDEX_DDLS = (
    "CREATE INDEX ix_next_session_manifests_content_hash ON next_session_manifests (content_hash)",
    "CREATE INDEX ix_next_session_manifests_source_run_id ON next_session_manifests (source_run_id)",
    "CREATE UNIQUE INDEX uq_next_session_manifests_as_of_version ON next_session_manifests (as_of, version)",
)

# The ORPHAN case named explicitly in docs/goal.md (four real live orphans: 3048, 3049, 3081, 3112) --
# a `source_run_id` that resolves to no row in `scanner_runs` at all.
_ORPHAN_SOURCE_RUN_ID = 999999


def _build_fixture_db(db_path: Path) -> None:
    """A fresh on-disk SQLite file with the live table's exact pre-migration DDL, one `scanner_runs`
    row, and three `next_session_manifests` rows -- one referencing the real run, one deliberately
    orphaned (mirrors the live 2026-08-05/08-10/08-11/08-12 orphans), one with a populated
    `generation_json` block (proves JSON-text columns survive the copy byte-for-byte too)."""
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("CREATE TABLE scanner_runs (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO scanner_runs (id) VALUES (1)")
        conn.execute(_LIVE_TABLE_DDL_WITH_FK)
        for ddl in _LIVE_INDEX_DDLS:
            conn.execute(ddl)
        conn.execute(
            "INSERT INTO next_session_manifests "
            "(id, as_of, source_run_id, session_delta_json, narrative_json, selection_json, "
            " content_hash, created_at, version, mode, frozen, generation_json, prospective_eligible) "
            "VALUES (1, '2026-08-10', 1, '{}', '{}', '{}', 'hash-normal', "
            " '2026-08-10T20:00:00', 1, 'at_ingest', 1, "
            " '{\"producer\": \"ingest_finalize\", \"source_run_created_at\": \"2026-08-10T20:00:00+00:00\"}', 1)"
        )
        conn.execute(
            "INSERT INTO next_session_manifests "
            "(id, as_of, source_run_id, session_delta_json, narrative_json, selection_json, "
            " content_hash, created_at, version, mode, frozen, generation_json, prospective_eligible) "
            f"VALUES (2, '2026-08-05', {_ORPHAN_SOURCE_RUN_ID}, '{{}}', '{{}}', '{{}}', 'hash-orphan', "
            " '2026-08-05T20:00:00', 1, 'at_ingest', 1, NULL, 0)"
        )
        conn.execute(
            "INSERT INTO next_session_manifests "
            "(id, as_of, source_run_id, session_delta_json, narrative_json, selection_json, "
            " content_hash, created_at, version, mode, frozen, prospective_eligible, "
            " candidate_rule_hash, manifest_hash) "
            "VALUES (3, '2026-08-11', 1, '{}', '{}', '{}', 'hash-hashes', "
            " '2026-08-11T20:00:00', 2, 'regenerate', 1, 0, 'rule-hash-abc', 'manifest-hash-xyz')"
        )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture()
def db_path(tmp_path) -> Path:
    path = tmp_path / "j11_stage_b1_fixture.db"
    _build_fixture_db(path)
    return path


@pytest.fixture()
def engine(db_path):
    return create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})


# --- TC-1: rebuild logic on a fixture DB with the live table's exact current DDL + an orphan ---------


def test_tc1_rebuild_drops_fk_preserves_row_count_and_every_column_including_orphan(engine, db_path):
    pre_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
    assert "FOREIGN KEY" in pre_ddl["table_sql"]  # sanity: the fixture really starts FK-having

    result = migration.rebuild_manifest_table(engine)

    assert result["status"] == "completed"
    assert result["diff"]["equal"] is True
    assert result["diff"]["mismatches"] == []
    assert result["diff"]["pre_row_count"] == 3
    assert result["diff"]["post_row_count"] == 3

    new_ddl = result["new_ddl"]
    assert "FOREIGN KEY" not in new_ddl["table_sql"]

    # the orphan's source_run_id survives byte-identical, unrebound and unrepaired
    post_dump = migration.dump_table(engine, NextSessionManifest.__table__)
    orphan = next(row for row in post_dump if row["id"] == 2)
    assert orphan["source_run_id"] == _ORPHAN_SOURCE_RUN_ID
    assert orphan["generation_json"] is None
    hashed = next(row for row in post_dump if row["id"] == 3)
    assert hashed["candidate_rule_hash"] == "rule-hash-abc"
    assert hashed["manifest_hash"] == "manifest-hash-xyz"


def test_tc1_resulting_index_set_matches_the_original_exactly(engine):
    """Regression guard for a real defect found while prototyping this module: naively cloning
    `NextSessionManifest.__table__` (its `index=True` columns and inline `UniqueConstraint`) would add
    FOUR indexes the live table has never had, and duplicate the unique constraint as a second, silent
    `sqlite_autoindex_*`. The rebuild must reproduce EXACTLY the original's three named indexes -- no
    more, no fewer."""
    result = migration.rebuild_manifest_table(engine)
    assert result["status"] == "completed"
    expected_index_names = [
        "ix_next_session_manifests_content_hash",
        "ix_next_session_manifests_source_run_id",
        "uq_next_session_manifests_as_of_version",
    ]
    assert sorted(result["new_ddl"]["index_names"]) == sorted(expected_index_names)
    # and no inline UNIQUE constraint (which would spawn an unauthorized extra sqlite_autoindex)
    assert "UNIQUE" not in result["new_ddl"]["table_sql"]


def _column_defs(table_sql: str) -> list[tuple[str, str]]:
    """[(column_name, normalised column-definition text)] in physical ordinal order, table-level
    constraints excluded -- enough to compare two `CREATE TABLE` texts column by column."""
    body = table_sql[table_sql.index("(") + 1 : table_sql.rindex(")")]
    out: list[tuple[str, str]] = []
    for part in body.replace("\n", " ").split(","):
        part = " ".join(part.split())
        if not part or part.upper().startswith(("PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "CHECK")):
            continue
        out.append((part.split()[0], part))
    return out


def test_audit_ddl_delta_beyond_fk_removal_is_exactly_the_known_residual_set(engine):
    """iter-11 AUDIT: ruling A1 / AG-18 bound this migration to removing the `source_run_id` FOREIGN KEY
    "and NOTHING else", but rebuilding from `NextSessionManifest.__table__` reproduces the MODEL's shape
    rather than the live table's historical shape. Three `DEFAULT` clauses that `app/db.py::_COLUMN_ADDS`
    had attached are dropped, and `version` moves in the column order. No stored value changes and no
    code path depends on the dropped server defaults -- but the deviation is real, is already
    materialised on the live database, and must never again be described as "nothing else changed".
    This test pins the delta so it stays visible for owner adjudication; if a corrective rebuild ever
    restores the original clauses, this test is the one that must be updated deliberately."""
    pre = migration.fetch_object_ddl(engine, migration.TABLE_NAME)["table_sql"]
    result = migration.rebuild_manifest_table(engine)
    assert result["status"] == "completed"
    post = result["new_ddl"]["table_sql"]

    pre_cols, post_cols = _column_defs(pre), _column_defs(post)

    # what IS preserved: the exact column name set, and every column's type + NOT NULL-ness
    assert {n for n, _ in pre_cols} == {n for n, _ in post_cols}
    pre_by_name = dict(pre_cols)
    post_by_name = dict(post_cols)
    for name, pre_def in pre_by_name.items():
        assert post_by_name[name].startswith(f"{name} {pre_def.split()[1]}"), name
        assert ("NOT NULL" in pre_def) == ("NOT NULL" in post_by_name[name]), name

    # the ONE authorized change
    assert "FOREIGN KEY" in pre
    assert "FOREIGN KEY" not in post

    # the residual, UNAUTHORIZED-but-materialised deltas -- asserted exactly, neither more nor fewer
    lost_default = sorted(
        name for name, pre_def in pre_by_name.items()
        if "DEFAULT" in pre_def and "DEFAULT" not in post_by_name[name]
    )
    assert lost_default == ["frozen", "prospective_eligible", "version"]
    gained_default = [
        name for name, pre_def in pre_by_name.items()
        if "DEFAULT" not in pre_def and "DEFAULT" in post_by_name[name]
    ]
    assert gained_default == []
    assert [n for n, _ in pre_cols].index("version") == 8
    assert [n for n, _ in post_cols].index("version") == 2
    # and nothing ELSE about any column definition differs
    other_diffs = sorted(
        name for name, pre_def in pre_by_name.items()
        if pre_def.replace(" DEFAULT 1", "").replace(" DEFAULT 0", "") != post_by_name[name]
    )
    assert other_diffs == []


# --- TC-2: PRAGMA foreign_keys=ON explicitly issued post-rebuild -- zero violations despite the orphan


def test_tc2_fk_check_with_pragma_on_is_zero_rows_despite_stored_orphan(engine, db_path):
    result = migration.rebuild_manifest_table(engine)
    assert result["status"] == "completed"

    violations = migration.foreign_key_check_with_pragma_on(db_path, migration.TABLE_NAME)
    assert violations == []

    # the orphan is still there, unrebound -- FK enforcement is satisfied by the ABSENCE of the
    # constraint declaration, never by nulling/repairing the orphaned value
    post_dump = migration.dump_table(engine, NextSessionManifest.__table__)
    orphan = next(row for row in post_dump if row["id"] == 2)
    assert orphan["source_run_id"] == _ORPHAN_SOURCE_RUN_ID


# --- TC-8: a deliberately-injected equality mismatch aborts BEFORE rename/drop ------------------------


def test_tc8_injected_equality_mismatch_aborts_before_rename_original_untouched(engine, db_path):
    original_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
    pre_dump = migration.dump_table(engine, NextSessionManifest.__table__)

    shadow = migration.create_shadow_table(engine)
    migration.copy_rows_to_shadow(engine, shadow)

    # deliberately inject a one-byte equality mismatch between the pre-copy source and the newly-copied
    # table (TC-8's own wording) -- corrupt the shadow copy directly, simulating a hypothetical copy
    # defect the equality check must catch.
    with engine.begin() as conn:
        conn.execute(
            text(f'UPDATE "{shadow.name}" SET content_hash = :bad WHERE id = 1'),
            {"bad": "CORRUPTED-BYTE"},
        )

    result = migration.verify_and_finalize(engine, shadow, pre_dump, original_ddl["index_sqls"])

    assert result["status"] == "aborted"
    assert result["diff"]["equal"] is False
    assert any(m["column"] == "content_hash" and m["id"] == 1 for m in result["diff"]["mismatches"])

    # the original table remains fully intact and queryable -- FK clause still present, row count and
    # every value unchanged, nothing renamed or dropped from it
    post_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
    assert "FOREIGN KEY" in post_ddl["table_sql"]
    post_dump = migration.dump_table(engine, NextSessionManifest.__table__)
    assert post_dump == pre_dump

    # the shadow copy (the failed attempt) was dropped -- never left half-migrated, never renamed
    with engine.connect() as conn:
        shadow_still_exists = conn.execute(
            text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=:n"),
            {"n": shadow.name},
        ).scalar()
    assert shadow_still_exists == 0


# --- diff_dumps: pure-function sanity (equal / unequal / missing / extra ids) --------------------------


def test_diff_dumps_reports_equal_for_identical_lists():
    rows = [{"id": 1, "a": "x"}, {"id": 2, "a": "y"}]
    diff = migration.diff_dumps(rows, list(rows))
    assert diff == {
        "equal": True,
        "pre_row_count": 2,
        "post_row_count": 2,
        "missing_ids": [],
        "extra_ids": [],
        "mismatches": [],
    }


def test_diff_dumps_reports_missing_and_extra_ids_separately_from_column_mismatches():
    pre = [{"id": 1, "a": "x"}, {"id": 2, "a": "y"}]
    post = [{"id": 1, "a": "CHANGED"}, {"id": 3, "a": "y"}]
    diff = migration.diff_dumps(pre, post)
    assert diff["equal"] is False
    assert diff["missing_ids"] == [2]
    assert diff["extra_ids"] == [3]
    assert diff["mismatches"] == [{"id": 1, "column": "a", "pre": "x", "post": "CHANGED"}]


# --- capture_full_db_snapshot / diff_snapshots: mutation accounting (TC-7's pure-function half) -------


def test_diff_snapshots_flags_only_the_table_whose_count_changed():
    pre = {"tables": {"next_session_manifests": 24, "daily_prices": 1000}, "db_file": None}
    post = {"tables": {"next_session_manifests": 24, "daily_prices": 1000}, "db_file": None}
    diff = migration.diff_snapshots(pre, post)
    assert diff["changed_tables"] == []
    assert diff["no_table_other_than_next_session_manifests_written"] is True

    post_mutated_other_table = {
        "tables": {"next_session_manifests": 24, "daily_prices": 1001},
        "db_file": None,
    }
    diff2 = migration.diff_snapshots(pre, post_mutated_other_table)
    assert diff2["changed_tables"] == [{"table": "daily_prices", "before": 1000, "after": 1001}]
    assert diff2["no_table_other_than_next_session_manifests_written"] is False
