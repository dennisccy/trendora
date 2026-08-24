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

goal-market-compass iter-12 addendum (ruling A10 fix, owner 2026-08-24): `create_shadow_table` now
takes the captured `original_table_sql` explicitly (all three call sites updated: `rebuild_manifest_table`,
this file's TC-8 test, and `scripts/run_j11_stage_b1_manifest_schema_migration.py`), and its output
DDL preserves the original column order and server DEFAULTs verbatim -- so
`test_audit_ddl_delta_beyond_fk_removal_is_exactly_the_known_residual_set`'s PREMISE (that
`rebuild_manifest_table` reproduces the iter-11 residual) is no longer true and that test is replaced
below by `test_tc1_through_tc7_corrected_rebuild_matches_original_ddl_exactly_except_the_fk_clause`,
which asserts the OPPOSITE (no residual). The historical residual itself is not erased -- it stays real
and pinned by a NEW regression test, `test_tc12_old_orm_metadata_construction_reproduces_the_known_iter11_residual`,
which re-implements the OLD (pre-iter-12) ORM-metadata-derived construction LOCALLY in this test file
only (TC-11 requires the production module itself never do this again). New tests in this addendum use
distinct names (`test_tc9_*`, `test_tc10_*`, `test_tc11_*`, `test_tc12_*`) that do not collide with any
existing name in this file or in `test_j11_maintenance.py`.
"""
from __future__ import annotations

import inspect
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import MetaData, PrimaryKeyConstraint, create_engine, text

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


def test_tc1_through_tc7_corrected_rebuild_matches_original_ddl_exactly_except_the_fk_clause(engine):
    """goal-market-compass iter-12 (ruling A10 fix): SUPERSEDES the pre-iter-12
    `test_audit_ddl_delta_beyond_fk_removal_is_exactly_the_known_residual_set`, whose premise -- that
    `rebuild_manifest_table` reproduces the iter-11 residual -- is no longer true now that
    `create_shadow_table` builds the shadow body from the CAPTURED live DDL text instead of
    `NextSessionManifest.__table__.to_metadata(...)`. Proves TC-1 (ordered column name list), TC-2
    (column types), TC-3 (NOT NULL flags), TC-4 (DEFAULT clauses -- including the three the OLD
    implementation dropped), TC-5 (primary key), and TC-7 (the captured pre/post `CREATE TABLE` text
    differs in EXACTLY one way: the absent FK clause -- column order, including `version`'s ordinal, is
    untouched). TC-6 (index set) stays covered by `test_tc1_resulting_index_set_matches_the_original_exactly`
    above, unaffected by this change. TC-8 (row values) stays covered by
    `test_tc1_rebuild_drops_fk_preserves_row_count_and_every_column_including_orphan` above. The
    historical iter-11 residual this test used to pin is NOT erased -- see
    `test_tc12_old_orm_metadata_construction_reproduces_the_known_iter11_residual` below, which proves it
    against a local reimplementation of the OLD construction instead."""
    pre = migration.fetch_object_ddl(engine, migration.TABLE_NAME)["table_sql"]
    result = migration.rebuild_manifest_table(engine)
    assert result["status"] == "completed"
    post = result["new_ddl"]["table_sql"]

    pre_cols, post_cols = _column_defs(pre), _column_defs(post)

    # TC-1: identical ORDERED column name list (not just the same set)
    assert [n for n, _ in pre_cols] == [n for n, _ in post_cols]

    pre_by_name = dict(pre_cols)
    post_by_name = dict(post_cols)
    for name, pre_def in pre_by_name.items():
        post_def = post_by_name[name]
        # TC-2: identical declared TYPE
        assert post_def.split()[1] == pre_def.split()[1], name
        # TC-3: identical NOT NULL flag
        assert ("NOT NULL" in pre_def) == ("NOT NULL" in post_def), name
        # TC-4: identical DEFAULT clause presence AND value -- the exact three columns the OLD approach
        # dropped (`version`, `frozen`, `prospective_eligible`) now survive the rebuild unchanged
        assert ("DEFAULT" in pre_def) == ("DEFAULT" in post_def), name
        if "DEFAULT" in pre_def:
            assert pre_def.split("DEFAULT", 1)[1] == post_def.split("DEFAULT", 1)[1], name

    for name in ("version", "frozen", "prospective_eligible"):
        assert "DEFAULT" in post_by_name[name], f"{name}'s server DEFAULT must survive (ruling A10 fix)"

    # TC-5: identical PRIMARY KEY declaration
    assert "PRIMARY KEY (id)" in pre
    assert "PRIMARY KEY (id)" in post

    # TC-7: the ONLY textual difference between pre and post column definitions is the absent FK
    # clause -- no column reorder (unlike the pre-iter-12 implementation, which moved `version` from
    # ordinal 9 to 3), and every column definition is byte-identical
    assert "FOREIGN KEY" in pre
    assert "FOREIGN KEY" not in post
    assert [n for n, _ in pre_cols].index("version") == 8
    assert [n for n, _ in post_cols].index("version") == 8
    assert pre_by_name == post_by_name


# --- TC-9: FK enforcement holds by contract, not merely because it is off -------------------------------


def test_tc9_deleting_scanner_run_with_fk_enforcement_on_succeeds_and_manifest_survives(engine, db_path):
    """TC-9: with `PRAGMA foreign_keys=ON` explicitly issued on the SAME connection that performs the
    delete, deleting the `ScannerRun` two manifest rows point at succeeds, and both manifest rows survive
    unchanged -- the contract holds by schema (no declared FK), not merely because enforcement defaults
    off."""
    result = migration.rebuild_manifest_table(engine)
    assert result["status"] == "completed"

    raw = sqlite3.connect(str(db_path))
    try:
        raw.execute("PRAGMA foreign_keys=ON")
        raw.execute("DELETE FROM scanner_runs WHERE id = 1")
        raw.commit()
        remaining = raw.execute(
            "SELECT COUNT(*) FROM next_session_manifests WHERE source_run_id = 1"
        ).fetchone()[0]
    finally:
        raw.close()
    # fixture rows 1 and 3 both carry source_run_id=1 -- both survive the delete unrebound
    assert remaining == 2


# --- TC-10: fail-closed abort BEFORE any table is created or touched -------------------------------------


def test_tc10_ambiguous_fk_clause_aborts_before_any_table_created_or_touched(engine):
    """TC-10: if the expected FK clause has been altered so it no longer matches exactly,
    `create_shadow_table` raises `MigrationDdlShapeError` before creating or touching any table -- no
    shadow table is left behind, and the original table is completely untouched."""
    original_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
    mangled = original_ddl["table_sql"].replace(
        "FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)",
        "FOREIGN KEY(some_other_column) REFERENCES some_other_table (id)",
    )
    assert mangled != original_ddl["table_sql"]  # sanity: the mangle actually took effect

    with pytest.raises(migration.MigrationDdlShapeError):
        migration.create_shadow_table(engine, mangled)

    with engine.connect() as conn:
        shadow_exists = conn.execute(
            text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=:n"),
            {"n": migration.SHADOW_TABLE_NAME},
        ).scalar()
    assert shadow_exists == 0

    post_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
    assert post_ddl == original_ddl


def test_tc10_duplicated_fk_clause_also_aborts_before_any_table_created_or_touched(engine):
    """TC-10 (second case): a captured DDL text containing the expected FK clause TWICE is just as
    ambiguous as containing it zero times -- "exactly once" is enforced both ways, never "at least
    once"."""
    original_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
    duplicated = original_ddl["table_sql"].replace(
        "FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)\n)",
        "FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id),\n"
        "\tFOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)\n)",
    )
    assert duplicated != original_ddl["table_sql"]

    with pytest.raises(migration.MigrationDdlShapeError):
        migration.create_shadow_table(engine, duplicated)

    with engine.connect() as conn:
        shadow_exists = conn.execute(
            text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=:n"),
            {"n": migration.SHADOW_TABLE_NAME},
        ).scalar()
    assert shadow_exists == 0


# --- TC-11: static audit -- create_shadow_table never builds from ORM metadata ---------------------------


def test_tc11_create_shadow_table_never_builds_from_orm_metadata():
    """TC-11: static source-level audit (same style as
    `test_manifest_invariants.py::test_tc15_no_update_statement_targets_next_session_manifests`) --
    the corrected `create_shadow_table` references only the captured `original_table_sql` text as the
    table-body source and contains no call to `NextSessionManifest.__table__.to_metadata()` or any other
    ORM-metadata table constructor. Checked at the AST level over the function BODY only (the docstring
    is dropped first) so the docstring's own prose -- which names exactly these forbidden patterns to
    explain what changed -- can never produce a false positive."""
    import ast

    source = inspect.getsource(migration.create_shadow_table)
    func_node = ast.parse(source).body[0]
    body = func_node.body
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(getattr(body[0], "value", None), ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]  # drop the docstring node -- checking CODE, never prose
    code_dump = ast.dump(ast.Module(body=body, type_ignores=[]))
    assert "to_metadata" not in code_dump
    assert "__table__" not in code_dump
    assert "create_all" not in code_dump


# --- TC-12: regression pin -- the OLD ORM-metadata construction really did produce the residual ----------


def test_tc12_old_orm_metadata_construction_reproduces_the_known_iter11_residual(engine):
    """TC-12: the OLD (pre-iter-12) `NextSessionManifest.__table__`-derived construction, RE-IMPLEMENTED
    HERE ONLY -- never in the production module again, per TC-11 -- run against the SAME PRE-iter-11
    fixture, reproduces exactly the known iter-11 residual: three dropped server DEFAULT clauses and
    `version` moved from column ordinal 9 to 3. This proves the corrected implementation (TC-1..TC-8
    above) fixes a REAL, reproduced defect, not merely a hypothetical one. The throwaway table this test
    creates is dropped at the end; it is never the live `next_session_manifests` table."""
    pre = migration.fetch_object_ddl(engine, migration.TABLE_NAME)["table_sql"]

    old_shadow_name = "next_session_manifests_old_orm_pin"
    new_metadata = MetaData()
    shadow = NextSessionManifest.__table__.to_metadata(new_metadata, name=old_shadow_name)
    shadow.indexes.clear()
    keep_constraints = {c for c in shadow.constraints if isinstance(c, PrimaryKeyConstraint)}
    shadow.constraints.clear()
    shadow.constraints |= keep_constraints
    new_metadata.create_all(engine, tables=[shadow])

    try:
        post = migration.fetch_object_ddl(engine, old_shadow_name)["table_sql"]

        pre_cols, post_cols = _column_defs(pre), _column_defs(post)
        pre_by_name, post_by_name = dict(pre_cols), dict(post_cols)

        lost_default = sorted(
            name for name, pre_def in pre_by_name.items()
            if "DEFAULT" in pre_def and "DEFAULT" not in post_by_name[name]
        )
        assert lost_default == ["frozen", "prospective_eligible", "version"]
        assert [n for n, _ in pre_cols].index("version") == 8
        assert [n for n, _ in post_cols].index("version") == 2
    finally:
        with engine.begin() as conn:
            conn.execute(text(f'DROP TABLE "{old_shadow_name}"'))


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

    shadow = migration.create_shadow_table(engine, original_ddl["table_sql"])
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


# --- TC-21: models.py's source_run_id comment states the TRUE A8/A9 end state ----------------------------


def test_tc21_models_py_source_run_id_comment_states_the_true_a8_a9_end_state():
    """TC-21: `models.py`'s `source_run_id` field comment must state the TRUE A8/A9 end state -- the
    live table matches the intended REFERENTIAL CONTRACT (no live FK; `source_run_id` remains
    `index=True` historical provenance) but does NOT claim exact physical DDL match, and must name the
    four owner-accepted residual differences (ruling A8/A9). The FALSE claim this replaced -- "the live
    table now matches this model declaration exactly -- no more model/live-DDL divergence" -- must never
    reappear."""
    import app.models as models_module

    source = Path(models_module.__file__).read_text()
    marker = "source_run_id: int = Field(index=True)"
    field_pos = source.index(marker)
    preceding_comment = "\n".join(source[:field_pos].splitlines()[-45:])

    # the withdrawn false claim must not reappear
    assert "matches this model declaration exactly" not in preceding_comment
    assert "no more model/live-DDL divergence" not in preceding_comment

    # the true end state: referential contract yes, exact physical DDL match no
    assert "referential contract" in preceding_comment.lower()
    assert "not physically match" in preceding_comment.lower()

    # the four owner-accepted residual differences (ruling A8/A9) are named
    for token in ("version", "frozen", "prospective_eligible", "ordinal"):
        assert token in preceding_comment, token
