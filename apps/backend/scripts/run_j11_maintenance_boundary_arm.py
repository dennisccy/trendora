"""goal-market-compass iter-17 -- J-11 maintenance-boundary lifecycle: the ARM entrypoint (docs/goal.md
J-11 step 11, "OWNER RULING -- J-11 maintenance-boundary lifecycle AUTHORIZED", implementation
requirement 4: "Provide an explicit arm path... a committed, production-capable path for
registering/activating the J-11 boundary... It must not live only inside a test fixture or a one-off
Python snippet.").

Thin CLI wrapper around the ALREADY-EXISTING, unchanged `app.engine.j11_preboot_guard.
register_j11_incident_boundary` -- this script introduces NO new registration logic. It:
  - sources its date-set EXCLUSIVELY from `app.engine.j11_maintenance.INCIDENT_DATES` (never re-typed --
    the exact trap the owner's dispatch note names) via that reused function, and additionally
    cross-checks the code constant against docs/goal.md's own two 11-date lists (the existing
    `app.engine.j11_stage_c.check_c1_date_set_boundary`, reused unchanged) BEFORE writing anything --
    satisfies requirement 4's "must validate the exact incident-date set";
  - is idempotent (a second identical invocation against the same database is a safe no-op on content --
    `register_boundary` upserts by unique `name`, never inserting a duplicate row -- TC-7);
  - writes ONLY to `maintenance_boundaries` (the reused, unchanged `register_j11_incident_boundary` /
    `register_boundary` touch no other table -- TC-8);
  - makes its mutation obvious: prints the boundary row before and after;
  - REFUSES (no database write of any kind) if the target table does not already exist -- creating
    `maintenance_boundaries` is a SEPARATE, NOT-yet-authorized decision (docs/goal.md's own "BLOCKER ON
    RECORD" paragraph: "do not create it and do not migrate to it"). This script never calls
    `create_db_and_tables`/`metadata.create_all`.

Mirrors `run_j11_stage_c_bounded_clear.py`'s established idiom: an explicit `--confirm` gate (no database
interaction of any kind without it, not even a read), and an explicit REQUIRED `--database-url` with NO
default pointing at the real configured database (goal-market-compass iter-14's lesson, generalized: a
silently-defaulted path/target argument is how committed evidence/state gets overwritten or touched by
accident) -- so this script can NEVER reach `apps/backend/data/trendora.db` unless that exact URL is typed
out by a caller who means it. **This iteration never invokes it against that file** -- fixture/temp-DB
invocation only, from tests.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_maintenance_boundary_arm.py \\
        --confirm \\
        --database-url sqlite:////absolute/path/to/some-disposable.db
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
from sqlmodel import Session, select  # noqa: E402

from app.db import make_engine  # noqa: E402
from app.engine import j11_preboot_guard as guard  # noqa: E402
from app.engine import j11_stage_c as jsc  # noqa: E402
from app.models import MaintenanceBoundary  # noqa: E402


def _print_boundary_row(session: Session, label: str) -> None:
    row = session.exec(
        select(MaintenanceBoundary).where(MaintenanceBoundary.name == guard.J11_INCIDENT_BOUNDARY_NAME)
    ).first()
    if row is None:
        print(f"{label}: no {guard.J11_INCIDENT_BOUNDARY_NAME!r} row exists", file=sys.stderr)
    else:
        print(
            f"{label}: id={row.id} name={row.name!r} active={row.active} "
            f"quarantined_dates_json={row.quarantined_dates_json} updated_at={row.updated_at}",
            file=sys.stderr,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--database-url", type=str, default=None,
        help=(
            "required -- no default on purpose. This iteration is NEVER authorized to invoke this script "
            "against the real configured database (docs/goal.md J-11 step 11's 'BLOCKER ON RECORD' -- the "
            "live maintenance_boundaries table does not exist and creating it is NOT authorized). Point "
            "this at a disposable fixture/temp database only."
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

    goal_md_text = jsc.read_goal_md_text()
    date_set_check = jsc.check_c1_date_set_boundary(goal_md_text)
    if not date_set_check["ok"]:
        print(
            "refusing to arm: the code's j11_maintenance.INCIDENT_DATES disagrees with docs/goal.md's own "
            f"11-date lists ({date_set_check}) -- arming would risk quarantining the wrong date set. No "
            "database interaction, not even a read, has occurred.",
            file=sys.stderr,
        )
        return 1

    engine = make_engine(args.database_url)
    if not sa_inspect(engine).has_table(MaintenanceBoundary.__tablename__):
        print(
            f"STALLED: the {MaintenanceBoundary.__tablename__!r} table does not exist in "
            f"{args.database_url!r}. Creating it is a SEPARATE, NOT-yet-authorized decision (docs/goal.md "
            "J-11 step 11's 'BLOCKER ON RECORD' -- 'do not create it and do not migrate to it'). This "
            "script never calls create_db_and_tables()/metadata.create_all(). No write of any kind has "
            "occurred.",
            file=sys.stderr,
        )
        return 3

    with Session(engine) as session:
        _print_boundary_row(session, "BEFORE")

    with Session(engine) as session:
        row = guard.register_j11_incident_boundary(session, active=True)

    with Session(engine) as session:
        _print_boundary_row(session, "AFTER")

    print(
        f"J-11 MAINTENANCE BOUNDARY: ACTIVE (id={row.id}, dates={row.quarantined_dates_json})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
