"""app.engine.j11_schema_migration -- J-11 Stage B1-completion: the ONE authorized live-schema
migration of `next_session_manifests` (docs/goal.md J-11 step 11, ruling A1, owner 2026-08-23), FIXED
for future safety per ruling A10 (goal-market-compass iter-12, owner 2026-08-24).

SQLite cannot drop a constraint in place, so the only way to remove the LIVE
`FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)` declaration (already dropped from the model
in `app/models.py` since iter-10, but never applied to the already-created live table -- this repo has
no Alembic, and `app/db.py`'s schema evolution is additive-ALTER-only) is a mechanical table rebuild:
create a constraint-free sibling table, copy every row, PROVE full row/column equality against a
persisted pre-migration dump, and only then drop the original and rename the sibling into place
(ruling A7's rollback mechanism: the original stays physically intact and queryable until equality is
proven in the SAME run -- any inequality aborts before the destructive step, leaving the original
untouched).

DDL SOURCE OF TRUTH (ruling A10 -- the iter-12 fix). The sibling table's BODY is now built by
transforming the table's own CAPTURED `CREATE TABLE` text (`fetch_object_ddl(...)["table_sql"]`, read
verbatim from `sqlite_master` -- the LIVE historical shape), never from `NextSessionManifest.__table__`
/ SQLModel metadata (the MODEL shape). `_strip_source_run_id_foreign_key` locates the EXACT
`FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)` clause via a targeted regex anchored to that
literal column and table name (tolerant only of incidental whitespace, never a broad "any FOREIGN KEY"
pattern that could match something unrelated) and removes it -- and ONLY it -- along with its one
adjacent comma, so the remaining clause list stays syntactically valid SQL; every other token (column
names, order, types, nullability, server DEFAULTs, primary key, any other constraint) is carried through
byte-for-byte. If the clause cannot be located EXACTLY ONCE, `create_shadow_table` raises
`MigrationDdlShapeError` before creating or touching any table -- fail closed, never a guess.
`_rename_create_table` then retargets the (now FK-free) `CREATE TABLE` header at the shadow name, under
the identical exactly-once fail-closed discipline; the transformed text is executed verbatim as raw SQL
(mechanically transformed from the captured original, never hand-authored), and the newly-created table
is reflected back into a SQLAlchemy `Table` object (`autoload_with=engine` -- introspection of what was
just created, never a second schema construction) so `copy_rows_to_shadow`/`verify_and_finalize` keep
working unchanged. Because the shadow table's DDL now comes from the ORIGINAL text, this module no
longer builds anything from `NextSessionManifest.__table__` at table-construction time, and so has
nothing to strip -- no `index=True`-derived Index and no inline `UniqueConstraint` ever enters the
picture. The ORIGINAL table's own three named indexes (captured verbatim from `sqlite_master` before
anything is touched) are still reissued, unmodified, onto the renamed table after the swap by
`verify_and_finalize` -- unchanged from before this fix.

RESIDUAL SCHEMA DELTA -- a historical fact about the iter-11 LIVE MIGRATION, not a property of this
module's corrected code (iter-11 auditor, 2026-08-23; owner ruling A8/A9, 2026-08-24). The PRE-iter-12
version of this module built the shadow table from `NextSessionManifest.__table__.to_metadata(...)`
(the MODEL shape), and the iter-11 live run already executed that version against
`apps/backend/data/trendora.db` before this fix existed. That MODEL-shape rebuild silently reproduced
the model's shape rather than the live table's historical shape, so the ALREADY-EXECUTED migration's
post-migration `CREATE TABLE` differs from its pre-migration one in THREE ways beyond the authorized FK
removal (verified by diffing the two persisted DDL evidence artifacts under
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
SQL INSERT targets this table anywhere in the repo). The owner's 2026-08-24 ruling (A8/A9, `docs/goal.md`)
ACCEPTS this exact, already-materialized four-item residual on the LIVE database rather than ordering a
second live rewrite -- that acceptance is about the live table as it stands today, and this module makes
no attempt to touch it again (A13: the live database is READ-ONLY this iteration). The residual is
explicitly NOT a property of the CORRECTED implementation below, which reproduces the pre-migration DDL
text minus ONLY the FK clause (proven fixture-only by `test_j11_stage_b1_migration.py`'s TC-1..TC-8
against a fixture built with the pre-iter-11 shape). A regression-pin test in that file re-implements the
OLD ORM-metadata-derived construction LOCALLY (this module itself must never call
`NextSessionManifest.__table__.to_metadata()` or any other ORM-metadata table constructor again -- TC-11)
against the same fixture and proves it reproduces this exact residual, so the defect this fix closes
stays demonstrably real rather than asserted from memory.

One controlled writer, never wired into `app/db.py`'s startup path, touches no other table. Every
function here is pure/composable so `apps/backend/tests/test_j11_stage_b1_migration.py` can exercise
each step (including the abort-before-rename path) directly against a fixture DB, and
`apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py` composes them against the LIVE
database with a persisted evidence artifact after every checkpoint. This corrected implementation is
FIXTURE-ONLY for goal-market-compass iter-12 -- it is never invoked against
`apps/backend/data/trendora.db` this iteration (ruling A10/A13); the live table already carries the
iter-11-produced (owner-accepted) residual shape and stays exactly as it is.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Optional

from sqlalchemy import MetaData, Table, inspect, insert, select, text
from sqlalchemy.engine import Engine

from app.models import NextSessionManifest

TABLE_NAME = "next_session_manifests"
SHADOW_TABLE_NAME = "next_session_manifests_new"


class MigrationDdlShapeError(RuntimeError):
    """Raised when the captured `CREATE TABLE` text does not have the EXACT shape this migration is
    authorized to transform -- either the expected `FOREIGN KEY(source_run_id) REFERENCES
    scanner_runs (id)` clause is not found exactly once, or the `CREATE TABLE <name> (` header cannot be
    located exactly once. Fail closed (ruling A10): raised BEFORE any table is created or touched, never
    a guess from a broad pattern that could silently remove or rename the wrong thing."""


# Targeted at the ONE clause ruling A1/A10 authorizes removing -- anchored to the literal column
# (`source_run_id`) and referenced table (`scanner_runs`) names, tolerant only of incidental whitespace
# differences (SQLite's `sqlite_master.sql` preserves the CREATE TABLE text verbatim, tabs and all).
# Deliberately NOT a generic `FOREIGN KEY\(.*\)` pattern -- that could match an unrelated constraint on a
# differently-shaped future table and silently strip the wrong thing.
_SOURCE_RUN_ID_FK_RE = re.compile(
    r"FOREIGN\s+KEY\s*\(\s*source_run_id\s*\)\s*REFERENCES\s*scanner_runs\s*\(\s*id\s*\)",
    re.IGNORECASE,
)


def _strip_source_run_id_foreign_key(table_sql: str) -> str:
    """Remove ONLY the exact `FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)` table-constraint
    clause from a captured `CREATE TABLE` text -- verbatim otherwise. Fails closed
    (`MigrationDdlShapeError`) unless that exact clause is found exactly once in the text. In the live
    table's known shape this clause is the trailing table-constraint item, preceded by a comma from the
    prior clause (`PRIMARY KEY (id),`); that preceding comma is swallowed along with the clause so the
    remaining text stays valid SQL, falling back to swallowing a FOLLOWING comma if the clause is not
    last (defensive -- not the live table's shape today, but keeps this function correct if it ever is)."""
    matches = list(_SOURCE_RUN_ID_FK_RE.finditer(table_sql))
    if len(matches) != 1:
        raise MigrationDdlShapeError(
            "expected exactly one 'FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)' clause in "
            f"the captured DDL text, found {len(matches)} -- aborting before any table is created or "
            "touched (ruling A10 fail-closed contract)"
        )
    start, end = matches[0].span()
    before, after = table_sql[:start], table_sql[end:]
    before_without_comma = re.sub(r",\s*$", "", before)
    if before_without_comma != before:
        return before_without_comma + after
    after_without_comma = re.sub(r"^\s*,", "", after)
    return before + after_without_comma


def _rename_create_table(table_sql: str, old_name: str, new_name: str) -> str:
    """Retarget ONLY the `CREATE TABLE <old_name> (` header at `new_name` -- verbatim otherwise. Fails
    closed (`MigrationDdlShapeError`) unless that exact header is found exactly once, so a captured DDL
    text that does not start the way this module expects is never silently mis-renamed."""
    pattern = re.compile(r"(CREATE\s+TABLE\s+)" + re.escape(old_name) + r"(\s*\()", re.IGNORECASE)
    matches = list(pattern.finditer(table_sql))
    if len(matches) != 1:
        raise MigrationDdlShapeError(
            f"expected exactly one 'CREATE TABLE {old_name} (' header in the captured DDL text, found "
            f"{len(matches)} -- aborting before any table is created or touched"
        )
    match = matches[0]
    replacement = f"{match.group(1)}{new_name}{match.group(2)}"
    return table_sql[: match.start()] + replacement + table_sql[match.end() :]


def fetch_object_ddl(engine: Engine, table_name: str) -> dict:
    """The table's own `CREATE TABLE` text plus every one of its named indexes' `CREATE INDEX` text,
    read verbatim from `sqlite_master` -- never hand-written, never inferred from the ORM model. This
    is the single source both the pre-migration evidence snapshot and the post-migration
    no-FOREIGN-KEY proof read from. `sql IS NOT NULL` excludes SQLite's own implicit
    `sqlite_autoindex_*` entries (which carry no independent `sql` text) -- irrelevant here since this
    module's own rebuild never creates an autoindex (it neither builds from ORM metadata nor declares
    any inline table-level UNIQUE constraint), but kept defensive in case a future live table ever does."""
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


def create_shadow_table(
    engine: Engine, original_table_sql: str, shadow_name: str = SHADOW_TABLE_NAME
) -> Table:
    """Build the constraint-free sibling table by transforming the CAPTURED LIVE `CREATE TABLE` text
    (`original_table_sql`, from `fetch_object_ddl(...)["table_sql"]` -- never `NextSessionManifest.
    __table__` / SQLModel metadata, ruling A10): remove ONLY the exact `FOREIGN KEY(source_run_id)
    REFERENCES scanner_runs (id)` clause, retarget the `CREATE TABLE` header at `shadow_name`, execute
    the transformed text VERBATIM as raw SQL, then reflect the newly-created table back into a
    SQLAlchemy `Table` object (`autoload_with=engine` -- introspection of what was just created, never a
    second schema construction) so `copy_rows_to_shadow`/`verify_and_finalize` keep working unchanged.
    Every other token of the original DDL -- column names, order, types, nullability, server DEFAULTs,
    primary key, any other constraint -- passes through byte-for-byte; the original's own three named
    indexes are reissued separately, verbatim, by `verify_and_finalize` after the swap (unchanged from
    before this fix -- this function creates no index of any kind). Fails closed
    (`MigrationDdlShapeError`, creating/touching no table) if the expected FK clause -- or the
    `CREATE TABLE` header -- cannot be located exactly once in the captured text."""
    transformed = _strip_source_run_id_foreign_key(original_table_sql)
    shadow_sql = _rename_create_table(transformed, TABLE_NAME, shadow_name)
    with engine.begin() as conn:
        conn.execute(text(shadow_sql))
    shadow_metadata = MetaData()
    return Table(shadow_name, shadow_metadata, autoload_with=engine)


def copy_rows_to_shadow(engine: Engine, shadow: Table) -> int:
    """`INSERT INTO <shadow> (<cols>) SELECT <cols> FROM next_session_manifests` via SQLAlchemy Core's
    `Insert.from_select` (never a hand-written SQL string) -- an explicit column list, so this copy is
    correct regardless of the shadow table's physical column ORDER, which after the ruling-A10 fix
    matches the captured original's order exactly (no reorder occurs at all; before the fix, the
    ORM-metadata-derived shadow reordered `version` from its historical ordinal 9 to the model's ordinal
    3 -- part of the now-accepted, already-materialized iter-11 residual, ruling A8/A9 -- and this
    explicit-column-name discipline was what kept THAT reorder harmless to the data even though it was
    still an unauthorized schema change). This function's explicit-column-name discipline is unchanged by
    the fix (already A10-compliant) and needed either way."""
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
    shadow = create_shadow_table(engine, original_ddl["table_sql"])
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
