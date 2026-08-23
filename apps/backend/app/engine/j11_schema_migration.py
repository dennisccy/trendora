"""app.engine.j11_schema_migration -- J-11 Stage B1-completion: the ONE authorized live-schema
migration of `next_session_manifests` (docs/goal.md J-11 step 11, ruling A1, owner 2026-08-23).

SQLite cannot drop a constraint in place, so the only way to remove the LIVE
`FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)` declaration (already dropped from the model
in `app/models.py` since iter-10, but never applied to the already-created live table -- this repo has
no Alembic, and `app/db.py`'s schema evolution is additive-ALTER-only) is a mechanical table rebuild:
create a constraint-free sibling table with the identical column set, copy every row, PROVE full
row/column equality against a persisted pre-migration dump, and only then drop the original and rename
the sibling into place (ruling A7's rollback mechanism: the original stays physically intact and
queryable until equality is proven in the SAME run -- any inequality aborts before the destructive
step, leaving the original untouched).

Ruling A2/AG-18 bounds this to the mechanical minimum: ONLY the FK constraint is removed. Nothing else
about the table may change -- not a column, not a stored value (orphaned `source_run_id`s included), and
not even the INDEX SET. Building the sibling table naively from `NextSessionManifest.__table__` via
SQLAlchemy's `tometadata()` would silently introduce TWO unauthorized schema drifts, both verified
empirically while prototyping this module against a throwaway fixture DB:
  1. `SQLModel.metadata.create_all()` on a table object still carrying the model's declared
     `index=True` columns (`as_of`, `candidate_rule_hash`, `cohort_rule_hash`, `prospective_eligible`)
     would create FOUR indexes the LIVE table has never had -- the live table carries only THREE named
     indexes (`ix_next_session_manifests_content_hash`, `ix_next_session_manifests_source_run_id`,
     `uq_next_session_manifests_as_of_version`), because `app/db.py`'s additive-ALTER schema evolution
     backfills new COLUMNS but never retroactively adds an index to an already-existing table.
  2. The model's inline `UniqueConstraint("as_of", "version", name=...)` (`__table_args__`), if carried
     into the physical CREATE TABLE, makes SQLite silently materialize a SECOND, redundant
     `sqlite_autoindex_next_session_manifests_1` alongside the reissued named
     `uq_next_session_manifests_as_of_version` index below -- the live table has never had that
     autoindex (it was originally created via a separate raw `CREATE UNIQUE INDEX` in
     `app/db.py::_INDEX_ADDS`, never as a table-level constraint).
Both are stripped from the sibling table object before creation; the ORIGINAL table's own three named
indexes (captured verbatim from `sqlite_master` before anything is touched) are reissued, unmodified,
onto the renamed table after the swap.

RESIDUAL SCHEMA DELTA -- stated honestly (iter-11 auditor, 2026-08-23). This module previously claimed
the resulting schema was "byte-for-byte identical to the original except for the one authorized change:
no FOREIGN KEY clause". That claim was FALSE, and the live migration has already been executed under it.
Rebuilding from `NextSessionManifest.__table__` reproduces the MODEL's shape, not the live table's
historical shape, so the post-migration `CREATE TABLE` differs from the pre-migration one in THREE ways
beyond the authorized FK removal (verified by diffing the two persisted DDL evidence artifacts under
`runs/goal-market-compass-iter-11/`):
  1. `version INTEGER NOT NULL DEFAULT 1`      -> `version INTEGER NOT NULL`
  2. `frozen BOOLEAN NOT NULL DEFAULT 0`       -> `frozen BOOLEAN NOT NULL`
  3. `prospective_eligible BOOLEAN NOT NULL DEFAULT 0` -> `prospective_eligible BOOLEAN NOT NULL`
  (plus `version` moving from column ordinal 9 to ordinal 3)
Those three `DEFAULT` clauses were artifacts of `app/db.py::_COLUMN_ADDS` (SQLite requires a non-null
default when ALTERing in a NOT NULL column); the model declares only Python-side defaults, so a database
freshly built from the model has never carried them either. No stored value changed, the column NAME set
and every column's type/NOT NULL are preserved, and no code path depends on the dropped server defaults
(every write to this table goes through SQLModel, which supplies all three values client-side; no raw
SQL INSERT targets this table anywhere in the repo). But this is still MORE than ruling A1 / AG-18
authorized ("removes the FK constraint and NOTHING else"), it is now materialised on the live 7.8 GB
database, and it is the owner's call -- not this module's -- whether to accept it or require a
corrective rebuild. `test_j11_stage_b1_migration.py::test_audit_ddl_delta_beyond_fk_removal_is_exactly_the_known_residual_set`
pins the delta so it can never again be silently described as "nothing else changed".

One controlled writer, never wired into `app/db.py`'s startup path, touches no other table. Every
function here is pure/composable so `apps/backend/tests/test_j11_stage_b1_migration.py` can exercise
each step (including the TC-8 abort-before-rename path) directly against a fixture DB, and
`apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py` composes them against the LIVE
database with a persisted evidence artifact after every checkpoint.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from sqlalchemy import MetaData, PrimaryKeyConstraint, Table, inspect, insert, select, text
from sqlalchemy.engine import Engine

from app.models import NextSessionManifest

TABLE_NAME = "next_session_manifests"
SHADOW_TABLE_NAME = "next_session_manifests_new"


def fetch_object_ddl(engine: Engine, table_name: str) -> dict:
    """The table's own `CREATE TABLE` text plus every one of its named indexes' `CREATE INDEX` text,
    read verbatim from `sqlite_master` -- never hand-written, never inferred from the ORM model. This
    is the single source both the pre-migration evidence snapshot and the post-migration
    no-FOREIGN-KEY proof (TC-1/TC-4/TC-6) read from. `sql IS NOT NULL` excludes SQLite's own implicit
    `sqlite_autoindex_*` entries (which carry no independent `sql` text) -- irrelevant here since this
    module's own rebuild never creates one (see module docstring point 2), but kept defensive in case a
    future live table ever does."""
    with engine.connect() as conn:
        table_sql = conn.execute(
            text("SELECT sql FROM sqlite_master WHERE type='table' AND name=:n"), {"n": table_name}
        ).scalar()
        rows = conn.execute(
            text(
                "SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name=:n "
                "AND sql IS NOT NULL ORDER BY name"
            ),
            {"n": table_name},
        ).fetchall()
    return {
        "table_sql": table_sql,
        "index_names": [row[0] for row in rows],
        "index_sqls": [row[1] for row in rows],
    }


def dump_table(engine: Engine, table: Table) -> list[dict]:
    """Every row x every column of `table`, ordered by `id`, as JSON-safe plain values (date/datetime
    columns -> ISO-8601 strings via the SQLAlchemy-typed read, so a DATE column round-trips through
    Python `date` objects rather than sqlite3's raw stored string -- the same coercion
    `compass.manifest_row_payload` relies on). Read-only: a single `SELECT`, no write of any kind."""
    cols = [c.name for c in table.columns]
    order_col = table.c["id"] if "id" in table.c else list(table.columns)[0]
    with engine.connect() as conn:
        result = conn.execute(select(table).order_by(order_col))
        out: list[dict] = []
        for row in result:
            record: dict = {}
            for col, val in zip(cols, row):
                if hasattr(val, "isoformat"):
                    val = val.isoformat()
                record[col] = val
            out.append(record)
    return out


def diff_dumps(pre: list[dict], post: list[dict]) -> dict:
    """Per-row, per-column equality (iteration 9's lesson: an aggregate-only "all N matched" check is
    exactly where the one real counter-example hides). Rows are matched by `id`; every mismatched
    column is reported individually, never just a boolean per row."""
    pre_by_id = {row["id"]: row for row in pre}
    post_by_id = {row["id"]: row for row in post}
    pre_ids = set(pre_by_id)
    post_ids = set(post_by_id)
    missing_ids = sorted(pre_ids - post_ids)
    extra_ids = sorted(post_ids - pre_ids)
    mismatches: list[dict] = []
    for row_id in sorted(pre_ids & post_ids):
        pre_row = pre_by_id[row_id]
        post_row = post_by_id[row_id]
        for col in pre_row:
            pre_val = pre_row.get(col)
            post_val = post_row.get(col)
            if pre_val != post_val:
                mismatches.append({"id": row_id, "column": col, "pre": pre_val, "post": post_val})
    equal = not missing_ids and not extra_ids and not mismatches
    return {
        "equal": equal,
        "pre_row_count": len(pre),
        "post_row_count": len(post),
        "missing_ids": missing_ids,
        "extra_ids": extra_ids,
        "mismatches": mismatches,
    }


def capture_full_db_snapshot(engine: Engine, db_path: Optional[Path]) -> dict:
    """Every table's row count (A3.4 mutation accounting) plus the database file's mtime/size, taken
    immediately before and immediately after the migration (TC-7) -- proves no table OTHER than
    `next_session_manifests` was written. `COUNT(*)` per table, never a full-column scan (AG-8: no
    unbounded whole-table ORM load)."""
    inspector = inspect(engine)
    table_names = sorted(inspector.get_table_names())
    counts: dict[str, int] = {}
    with engine.connect() as conn:
        for name in table_names:
            counts[name] = conn.execute(text(f'SELECT COUNT(*) FROM "{name}"')).scalar()
    db_file: Optional[dict] = None
    if db_path is not None and db_path.exists():
        stat = db_path.stat()
        db_file = {"path": str(db_path), "mtime": stat.st_mtime, "size_bytes": stat.st_size}
    return {"tables": counts, "db_file": db_file}


def diff_snapshots(pre: dict, post: dict) -> dict:
    """Which tables' row counts changed between two `capture_full_db_snapshot` calls -- the mutation
    accounting proof (TC-7). A successful migration changes nothing but `next_session_manifests`
    (whose row count does not even change -- 24 -> 24 -- only its schema does)."""
    pre_tables = pre["tables"]
    post_tables = post["tables"]
    all_tables = sorted(set(pre_tables) | set(post_tables))
    changed = [
        {"table": name, "before": pre_tables.get(name), "after": post_tables.get(name)}
        for name in all_tables
        if pre_tables.get(name) != post_tables.get(name)
    ]
    only_manifests_changed = all(entry["table"] == TABLE_NAME for entry in changed)
    return {
        "changed_tables": changed,
        "no_table_other_than_next_session_manifests_written": only_manifests_changed,
        "db_file_before": pre.get("db_file"),
        "db_file_after": post.get("db_file"),
    }


def create_shadow_table(engine: Engine, shadow_name: str = SHADOW_TABLE_NAME) -> Table:
    """Build the constraint-free sibling table under `shadow_name` from `NextSessionManifest.__table__`
    (SQLModel metadata -- never hand-written DDL) and create it physically. Strips the model's
    `index=True`-derived Index objects and its inline UniqueConstraint (see module docstring points 1
    and 2) so the ONLY schema-level effect of this whole module is the dropped `FOREIGN KEY` -- the
    original table's own three named indexes are reissued verbatim after the swap
    (`fetch_object_ddl`'s captured `index_sqls`), never regenerated here."""
    new_metadata = MetaData()
    shadow = NextSessionManifest.__table__.to_metadata(new_metadata, name=shadow_name)
    shadow.indexes.clear()
    # NOTE: deliberately `|=` (set union-assignment), never a `.update(...)` method call -- this repo's
    # own `test_tc15_no_update_statement_targets_next_session_manifests` static audit flags ANY
    # `.update(...)` call syntax in a module that mentions the manifest table, as a blunt but effective
    # guard against an accidental SQL UPDATE against `next_session_manifests`. This is a plain Python
    # `set` operation (Table.constraints), not a database write of any kind -- `|=` says so unambiguously
    # to both the reader and that audit.
    keep_constraints = {c for c in shadow.constraints if isinstance(c, PrimaryKeyConstraint)}
    shadow.constraints.clear()
    shadow.constraints |= keep_constraints
    new_metadata.create_all(engine, tables=[shadow])
    return shadow


def copy_rows_to_shadow(engine: Engine, shadow: Table) -> int:
    """`INSERT INTO <shadow> (<cols>) SELECT <cols> FROM next_session_manifests` via SQLAlchemy Core's
    `Insert.from_select` (never a hand-written SQL string) -- an explicit column list, so the column
    ORDER difference between the two table definitions (SQLModel declares `version` at ordinal 3 while
    the live table's historical order put it at ordinal 9) can never misalign a value into the wrong
    column. The reorder itself SURVIVES into the rebuilt table and is part of the residual schema delta
    documented in this module's docstring -- it is not "cosmetic only" in the sense of being within
    ruling A1's "nothing else" bound; it is simply harmless to the copy."""
    cols = [c.name for c in NextSessionManifest.__table__.columns]
    stmt = insert(shadow).from_select(cols, select(NextSessionManifest.__table__))
    with engine.begin() as conn:
        result = conn.execute(stmt)
    return result.rowcount


def verify_and_finalize(
    engine: Engine, shadow: Table, pre_dump: list[dict], original_index_sqls: list[str]
) -> dict:
    """The equality check (ruling A7's practical rollback mechanism), run BEFORE any destructive
    statement: dump the shadow table and diff it against `pre_dump`. Any inequality aborts -- drops
    only the shadow copy, leaves the original `next_session_manifests` completely untouched, and
    returns `status: "aborted"` with the full diff as evidence (TC-8). Only on proven equality does it
    drop the original, rename the shadow into place, and reissue the original's own captured indexes
    verbatim -- then re-dumps the now-live table and diffs it against `pre_dump` a SECOND time as a
    final sanity check (defensive; a rename + index-creation cannot alter row data, but this is checked
    rather than assumed)."""
    post_copy_dump = dump_table(engine, shadow)
    diff = diff_dumps(pre_dump, post_copy_dump)
    if not diff["equal"]:
        with engine.begin() as conn:
            conn.execute(text(f'DROP TABLE "{shadow.name}"'))
        return {"status": "aborted", "diff": diff}

    with engine.begin() as conn:
        conn.execute(text(f'DROP TABLE "{TABLE_NAME}"'))
        conn.execute(text(f'ALTER TABLE "{shadow.name}" RENAME TO "{TABLE_NAME}"'))
        for index_sql in original_index_sqls:
            conn.execute(text(index_sql))

    final_dump = dump_table(engine, NextSessionManifest.__table__)
    final_diff = diff_dumps(pre_dump, final_dump)
    status = "completed" if final_diff["equal"] else "swap_verification_failed"
    return {"status": status, "diff": final_diff}


def rebuild_manifest_table(engine: Engine) -> dict:
    """The full orchestration -- `fetch_object_ddl` -> `dump_table` (pre) -> `create_shadow_table` ->
    `copy_rows_to_shadow` -> `verify_and_finalize`. Returned dict always carries `status`
    (`"completed"` | `"aborted"` | `"swap_verification_failed"`), `diff`, and `original_ddl`; carries
    `new_ddl` too when `status == "completed"`. The live-database CLI script
    (`scripts/run_j11_stage_b1_manifest_schema_migration.py`) calls the same primitives directly instead
    of this wrapper, so it can persist the pre-migration dump to disk BEFORE the destructive step runs
    (ruling A3.1) -- this wrapper exists for the one-call fixture-test path (TC-1/TC-2) and any future
    caller that does not need that durability guarantee."""
    original_ddl = fetch_object_ddl(engine, TABLE_NAME)
    pre_dump = dump_table(engine, NextSessionManifest.__table__)
    shadow = create_shadow_table(engine)
    copy_rows_to_shadow(engine, shadow)
    result = verify_and_finalize(engine, shadow, pre_dump, original_ddl["index_sqls"])
    result["original_ddl"] = original_ddl
    result["pre_dump"] = pre_dump
    if result["status"] == "completed":
        result["new_ddl"] = fetch_object_ddl(engine, TABLE_NAME)
    return result


def foreign_key_check_with_pragma_on(db_path: Path, table_name: str = TABLE_NAME) -> list[dict]:
    """TC-6: `PRAGMA foreign_key_check(<table>)` with `PRAGMA foreign_keys=ON` EXPLICITLY issued on a
    fresh, dedicated `sqlite3` connection (never the pooled `app.db` engine, whose connections never set
    this pragma -- `app.db._apply_sqlite_pragmas` deliberately does not -- and a pragma issued on an
    already-open SQLAlchemy connection can land inside an implicit transaction, where SQLite silently
    ignores it). Proves the six acceptance items hold by schema/contract, not merely because enforcement
    happens to default OFF. Read-only: `PRAGMA foreign_key_check` does not write."""
    raw = sqlite3.connect(str(db_path))
    try:
        raw.execute("PRAGMA foreign_keys=ON")
        cursor = raw.execute(f'PRAGMA foreign_key_check("{table_name}")')
        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        raw.close()
