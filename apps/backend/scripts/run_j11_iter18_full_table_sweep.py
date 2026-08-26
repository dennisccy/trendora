"""goal-market-compass iter-18 -- strictly READ-ONLY mutation-accounting snapshot for the J-11 table-create
+ arm live sequence (docs/goal.md J-11 step 11, "OWNER RULING -- J-11 exact maintenance-boundary table
creation and live arm AUTHORIZED", implementation requirement 4: "capture before/after evidence proving no
unrelated application state changed").

Run TWICE against the real database -- once immediately BEFORE the table-create step, once immediately
AFTER the live-verification step -- each time with a different `--label` (e.g. `before` / `after`) so the
two snapshots land in separate, clearly-named files. The dev handoff diffs the two using
`app.engine.j11_maintenance.diff_full_table_sweeps`.

Opens the live database through an ACTUAL read-only SQLite handle (`file:<path>?mode=ro` +
`PRAGMA query_only=ON`, the SAME `_read_only_engine` idiom every other J-11 live-verification script
already established -- copied here unchanged) and calls the REAL, unmodified
`app.engine.j11_maintenance.capture_full_table_sweep` -- no second sweep implementation. Performs ZERO
writes of any kind. The db file's mtime + size + `-wal` sidecar size are fingerprinted at the TRUE process
start and TRUE process end (iteration-12's lesson), the SAME as every other J-11 live-verification script.

goal-market-compass iter-18 rider (the SAME evidence-destination-collision refusal every other J-11
evidence-writing script now carries): refuses before any read if the target output file already exists.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_iter18_full_table_sweep.py \\
        --evidence-dir runs/goal-market-compass-iter-18 --label before
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# scripts/ -> backend -> apps -> repo root
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, event  # noqa: E402
from sqlmodel import Session  # noqa: E402

from app.config import load_config  # noqa: E402
from app.db import resolve_database_url  # noqa: E402
from app.engine import j11_maintenance as jm  # noqa: E402
from app.engine import j11_stage_c as jsc  # noqa: E402


def _db_file_path(database_url: str) -> "Path | None":
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None
    raw = database_url[len(prefix):]
    if not raw or raw == ":memory:":
        return None
    path = Path(raw)
    return path if path.is_absolute() else (REPO_ROOT / raw)


def _read_only_engine(db_path: Path):
    """Mirrors every other J-11 live-verification script's own helper of the same name, unchanged."""
    url = f"sqlite:///file:{db_path}?mode=ro&uri=true"
    engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _set_query_only(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA query_only=ON")

    return engine


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
    print(f"wrote {path}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--evidence-dir", type=Path, default=None,
        help="required -- no default on purpose (mirrors every other J-11 evidence-writing script).",
    )
    parser.add_argument(
        "--label", type=str, default=None,
        help="required -- e.g. 'before' or 'after'; names the output file "
             "j11-iter18-full-table-sweep-<label>.json.",
    )
    args = parser.parse_args()

    if args.evidence_dir is None or args.label is None:
        print(
            "refusing to run without both an explicit --evidence-dir and --label. No config has been "
            "loaded, no database engine has been constructed, and nothing has been written.",
            file=sys.stderr,
        )
        return 2

    output_path = args.evidence_dir / f"j11-iter18-full-table-sweep-{args.label}.json"
    if output_path.exists():
        print(
            f"refusing to run: {output_path} already exists -- this looks like a mistyped destination or "
            "a repeated --label pointed at an existing, already-populated evidence file rather than a "
            "fresh one for this run. No database interaction, not even a read, has occurred.",
            file=sys.stderr,
        )
        return 2

    cfg = load_config()
    resolved_url = resolve_database_url(cfg.database.url)
    db_path = _db_file_path(resolved_url)
    if db_path is None or not db_path.exists():
        print(f"FAIL: could not resolve a live sqlite db file from {resolved_url!r}", file=sys.stderr)
        return 1
    print(f"database (READ-ONLY handle, mode=ro + PRAGMA query_only=ON): {db_path}", file=sys.stderr)

    db_file_true_start = jsc.db_file_fingerprint(db_path)
    engine = _read_only_engine(db_path)
    with Session(engine) as session:
        sweep = jm.capture_full_table_sweep(session)
    db_file_true_end = jsc.db_file_fingerprint(db_path)

    zero_write_proof = {
        "mtime_unchanged": db_file_true_start.get("mtime") == db_file_true_end.get("mtime"),
        "size_unchanged": db_file_true_start.get("size_bytes") == db_file_true_end.get("size_bytes"),
    }

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "label": args.label,
        "db_path": str(db_path),
        "sweep": sweep,
        "db_file_true_start": db_file_true_start,
        "db_file_true_end": db_file_true_end,
        "zero_write_proof": zero_write_proof,
        "recipe": (
            "apps/backend/.venv/bin/python apps/backend/scripts/run_j11_iter18_full_table_sweep.py "
            f"--evidence-dir {args.evidence_dir} --label {args.label}"
        ),
    }
    _write_json(output_path, payload)
    print(
        f"label={args.label} table_count={sweep['table_count']} "
        f"mtime_unchanged={zero_write_proof['mtime_unchanged']} size_unchanged={zero_write_proof['size_unchanged']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
