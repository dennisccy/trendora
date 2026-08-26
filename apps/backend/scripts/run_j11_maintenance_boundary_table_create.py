"""goal-market-compass iter-18 -- J-11 maintenance-boundary lifecycle: the exact single-table
CREATE-or-VERIFY entrypoint (docs/goal.md J-11 step 11, "OWNER RULING -- J-11 exact maintenance-boundary
table creation and live arm AUTHORIZED", implementation requirements 1-2).

The prior owner ruling ("OWNER RULING -- J-11 maintenance-boundary lifecycle AUTHORIZED", iter-16/17)
explicitly forbade creating `maintenance_boundaries` -- `run_j11_maintenance_boundary_arm.py` (iter-17)
REFUSES when the table is absent for exactly that reason. The 2026-08-25 ruling now authorizes creating
that ONE table, exactly, through a dedicated bounded entrypoint -- never through ordinary backend boot
(`create_db_and_tables`, which runs `SQLModel.metadata.create_all()` over the COMPLETE application
metadata and could mint some other unrelated missing table as a side effect) and never through a
hand-authored duplicate schema.

This script:
  - creates EXACTLY `maintenance_boundaries`, sourced ONLY from the already-committed
    `app.models.MaintenanceBoundary.__table__`, via that Table object's own `.create(bind=engine)` --
    SQLAlchemy's single-table DDL operation, never `SQLModel.metadata.create_all()` (which operates over
    every table SQLModel knows about) and never a hand-typed `CREATE TABLE` string;
  - if `maintenance_boundaries` already exists, inspects its LIVE columns (name, type, nullable) against
    the model's own declared columns: an EXACT match is a no-op ("already correct, no action taken"); any
    mismatch -- a missing column, an extra column, a type or nullability difference -- STOPs (exits
    non-zero, performs no write of any kind, names the exact mismatched column(s)) rather than
    `ALTER`/migrate/guess-repair;
  - REFUSES (zero database interaction of any kind, not even a read) without both an explicit `--confirm`
    flag and an explicit, no-default `--database-url` -- mirrors `run_j11_maintenance_boundary_arm.py`'s
    established idiom exactly (goal-market-compass iter-14's lesson: a silently-defaulted path/target
    argument is how committed evidence/state gets overwritten or touched by accident);
  - never touches any table other than `maintenance_boundaries` -- no `_ensure_additive_columns`, no
    `_ensure_index_hygiene`, no index/schema maintenance over the rest of the schema.

This iteration DOES invoke this script against the real `apps/backend/data/trendora.db`, but ONLY once,
ONLY after every fixture/unit test in `test_j11_preboot_guard_cli_scripts.py` (TC-5 through TC-8) is
green, and ONLY as the FIRST of the two authorized live writes (table-create, then the unmodified
`run_j11_maintenance_boundary_arm.py`) -- see the dev handoff for the full live-sequence evidence trail.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_maintenance_boundary_table_create.py \\
        --confirm \\
        --database-url sqlite:////absolute/path/to/trendora.db
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# scripts/ -> backend -> apps -> repo root
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import inspect as sa_inspect  # noqa: E402

from app.db import make_engine  # noqa: E402
from app.models import MaintenanceBoundary  # noqa: E402

TABLE_NAME = MaintenanceBoundary.__tablename__  # "maintenance_boundaries" -- never re-typed as a literal


def _expected_columns() -> dict[str, dict]:
    """The exact column shape the live table must match, read directly off the committed
    `MaintenanceBoundary.__table__` -- never a second, hand-typed schema description."""
    return {
        col.name: {"type": str(col.type), "nullable": bool(col.nullable)}
        for col in MaintenanceBoundary.__table__.columns
    }


def _live_columns(engine) -> dict[str, dict]:
    """The live table's actual columns, via SQLAlchemy's own inspector (never a hand-rolled
    `PRAGMA table_info` parse)."""
    inspector = sa_inspect(engine)
    return {
        col["name"]: {"type": str(col["type"]), "nullable": bool(col["nullable"])}
        for col in inspector.get_columns(TABLE_NAME)
    }


def _schema_mismatches(expected: dict, live: dict) -> list[str]:
    """Every column-level disagreement between `expected` (the model) and `live` (the real table) --
    missing, unexpected-extra, or a type/nullable difference. Empty list == exact match. Every label in
    this small, closed vocabulary (missing / extra / type mismatch / nullable mismatch) is exercised by a
    real test (TC-7) -- never merely declared reachable (goal-market-compass iter-14/14b's lesson)."""
    mismatches: list[str] = []
    for name, expected_shape in sorted(expected.items()):
        live_shape = live.get(name)
        if live_shape is None:
            mismatches.append(f"{name} (missing from live table)")
            continue
        if live_shape["type"] != expected_shape["type"]:
            mismatches.append(
                f"{name} (type mismatch: live={live_shape['type']!r} expected={expected_shape['type']!r})"
            )
        if live_shape["nullable"] != expected_shape["nullable"]:
            mismatches.append(
                f"{name} (nullable mismatch: live={live_shape['nullable']!r} "
                f"expected={expected_shape['nullable']!r})"
            )
    for name in sorted(set(live) - set(expected)):
        mismatches.append(f"{name} (unexpected extra column on the live table)")
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--database-url", type=str, default=None,
        help=(
            "required -- no default on purpose (mirrors run_j11_maintenance_boundary_arm.py exactly). "
            "Point this at the real configured database only once every fixture/unit test is green."
        ),
    )
    parser.add_argument(
        "--confirm", action="store_true",
        help="required -- without it, the script touches no database at all and exits non-zero.",
    )
    args = parser.parse_args()

    if not args.confirm:
        print(
            "refusing to run without --confirm. No database interaction, not even a read, has occurred.",
            file=sys.stderr,
        )
        return 2

    if args.database_url is None:
        print(
            "refusing to run without an explicit --database-url. There is no default -- this script must "
            "never be able to reach the real configured database by omission. No database interaction, "
            "not even a read, has occurred.",
            file=sys.stderr,
        )
        return 2

    engine = make_engine(args.database_url)
    expected = _expected_columns()

    if not sa_inspect(engine).has_table(TABLE_NAME):
        # The ONE authorized write: a single-table CREATE sourced from the committed model's own Table
        # object -- never `create_db_and_tables()`/`SQLModel.metadata.create_all()` (either could mint an
        # unrelated missing table as a side effect), never a hand-authored duplicate CREATE TABLE string.
        MaintenanceBoundary.__table__.create(bind=engine, checkfirst=True)
        print(f"created table {TABLE_NAME!r} from app.models.MaintenanceBoundary.__table__", file=sys.stderr)

        # Verify immediately after creating -- the freshly created table must match the model exactly
        # (a real mismatch here would mean this script's OWN create path disagrees with the model, which
        # should never happen since both read the SAME Table object, but this is checked, not assumed).
        mismatches = _schema_mismatches(expected, _live_columns(engine))
        if mismatches:
            print(
                f"STALLED: {TABLE_NAME!r} was created but does not match "
                f"app.models.MaintenanceBoundary.__table__ immediately afterward: {mismatches}. "
                "This should not be possible (both paths read the same Table object) -- surfacing rather "
                "than silently proceeding.",
                file=sys.stderr,
            )
            return 1
        print(f"J-11 MAINTENANCE_BOUNDARIES TABLE: CREATED (schema-exact)", file=sys.stderr)
        return 0

    # Table already exists -- inspect, never blindly trust, never ALTER/migrate/guess-repair.
    mismatches = _schema_mismatches(expected, _live_columns(engine))
    if mismatches:
        print(
            f"STOP: table {TABLE_NAME!r} already exists but does not exactly match "
            f"app.models.MaintenanceBoundary.__table__. Mismatched column(s): {mismatches}. No write of "
            "any kind has occurred -- this script never ALTERs, migrates, or guess-repairs an existing "
            "table. Resolve the mismatch manually before re-running.",
            file=sys.stderr,
        )
        return 1

    print(f"{TABLE_NAME!r} already correct, no action taken", file=sys.stderr)
    print(f"J-11 MAINTENANCE_BOUNDARIES TABLE: ALREADY CORRECT (no-op)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
