"""goal-market-compass iter-17 -- J-11 maintenance-boundary lifecycle: the DISARM entrypoint (docs/goal.md
J-11 step 11, "OWNER RULING -- J-11 maintenance-boundary lifecycle AUTHORIZED", implementation
requirement 5: "Provide a future disarm/deactivation path. Production-capable, scoped to exactly the J-11
boundary, must not delete unrelated maintenance history. Do not invoke it now.").

Thin CLI wrapper around the ALREADY-EXISTING, unchanged `app.engine.j11_preboot_guard.clear_boundary` --
this script introduces NO new deactivation logic. It:
  - takes the boundary's `name` as an explicit, REQUIRED command-line argument -- NEVER a hardcoded
    target (never defaults to `guard.J11_INCIDENT_BOUNDARY_NAME` or any other boundary), so a caller must
    always say exactly which boundary they mean;
  - is scoped strictly to that one named row: `clear_boundary` looks up by unique `name` and flips only
    that row's `active` flag to `False` -- every OTHER registered boundary's row is left untouched in
    every field (TC-9/TC-10);
  - NEVER deletes a row -- `active=False` only, so the maintenance history stays auditable (the owner's
    "Lifecycle -- deactivate, do not delete" instruction);
  - makes its mutation obvious: prints the boundary row before and after;
  - is a safe no-op (exit 0, nothing written) when the named boundary does not exist, OR when the
    `maintenance_boundaries` table itself does not exist -- "nothing is armed" is not an error condition
    for a disarm request.

Mirrors `run_j11_maintenance_boundary_arm.py`'s / `run_j11_stage_c_bounded_clear.py`'s idiom: an explicit
`--confirm` gate (no database interaction of any kind without it, not even a read), and an explicit
REQUIRED `--database-url` with NO default pointing at the real configured database. **This iteration never
invokes it against any live-armed state** -- nothing is live-armed yet (the arm step is itself blocked by
the live table's absence), so there is nothing for this script to legitimately disarm against
`apps/backend/data/trendora.db` this iteration; fixture/temp-DB invocation only, from tests.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_maintenance_boundary_disarm.py \\
        --confirm \\
        --database-url sqlite:////absolute/path/to/some-disposable.db \\
        --name j11-incident-recovery
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
from app.models import MaintenanceBoundary  # noqa: E402


def _print_boundary_row(session: Session, name: str, label: str) -> None:
    row = session.exec(select(MaintenanceBoundary).where(MaintenanceBoundary.name == name)).first()
    if row is None:
        print(f"{label}: no {name!r} row exists", file=sys.stderr)
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
        help="required -- no default on purpose (never able to reach the real configured database by omission).",
    )
    parser.add_argument(
        "--name", type=str, default=None,
        help=(
            "required -- the EXACT boundary name to disarm. Never defaults to "
            f"{guard.J11_INCIDENT_BOUNDARY_NAME!r} or any other boundary; scoped strictly to whatever is "
            "typed here, so this script can never accidentally touch an unrelated boundary."
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

    if not args.name:
        print(
            "refusing to run without an explicit --name. There is no default boundary -- this script must "
            "never guess which boundary to disarm. No database interaction, not even a read, has occurred.",
            file=sys.stderr,
        )
        return 2

    engine = make_engine(args.database_url)
    if not sa_inspect(engine).has_table(MaintenanceBoundary.__tablename__):
        print(
            f"no-op: the {MaintenanceBoundary.__tablename__!r} table does not exist in "
            f"{args.database_url!r} -- nothing is armed, so there is nothing to disarm. No write of any "
            "kind has occurred.",
            file=sys.stderr,
        )
        return 0

    with Session(engine) as session:
        _print_boundary_row(session, args.name, "BEFORE")

    with Session(engine) as session:
        row = guard.clear_boundary(session, args.name)

    with Session(engine) as session:
        _print_boundary_row(session, args.name, "AFTER")

    if row is None:
        print(f"no-op: no boundary named {args.name!r} was registered. No write has occurred.", file=sys.stderr)
        return 0

    print(f"J-11 MAINTENANCE BOUNDARY {args.name!r}: CLEARED (id={row.id})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
