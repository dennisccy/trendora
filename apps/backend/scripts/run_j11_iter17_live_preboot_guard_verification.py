"""goal-market-compass iter-17 -- TC-11/TC-12: strictly READ-ONLY live verification of the AG-8-fixed
`evaluate_boundary_for_date` against the real `apps/backend/data/trendora.db`, plus the zero-live-writes
proof (docs/goal.md J-11 step 11, "OWNER RULING -- J-11 maintenance-boundary lifecycle AUTHORIZED",
implementation requirement 7: "verify through the same production guard entry point using a non-writing
diagnostic/test harness").

This script performs ZERO writes of any kind. It opens the live database through an ACTUAL read-only
SQLite handle (`file:<path>?mode=ro` + `PRAGMA query_only=ON`, the SAME `_read_only_engine` idiom
`run_j11_iter16_stage_d_readiness.py` already established -- copied here unchanged, never imported cross-
script since no shared utility module holds it today), calls the REAL, unmodified
`app.engine.j11_preboot_guard.evaluate_boundary_for_date` for 2026-08-12, and independently confirms via a
companion `sqlite_master` query that `maintenance_boundaries` does not exist. The database file's mtime +
size + `-wal` sidecar size are fingerprinted at the TRUE start and TRUE end of the process (iteration-12's
lesson: this bracket, not a narrow internal one, is the proof that matters) and written to their own
before/after evidence files, mirroring `run_j11_stage_c_bounded_clear.py`'s / `run_j11_iter16_stage_d_
readiness.py`'s established naming.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_iter17_live_preboot_guard_verification.py \\
        --evidence-dir runs/goal-market-compass-iter-17
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

# scripts/ -> backend -> apps -> repo root
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, event, text  # noqa: E402
from sqlmodel import Session  # noqa: E402

from app.config import load_config  # noqa: E402
from app.db import resolve_database_url  # noqa: E402
from app.engine import j11_preboot_guard as guard  # noqa: E402
from app.engine import j11_stage_c as jsc  # noqa: E402

TARGET_DATE = date(2026, 8, 12)


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
    """Mirrors `run_j11_iter16_stage_d_readiness.py`'s own helper of the same name, unchanged."""
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
    args = parser.parse_args()

    if args.evidence_dir is None:
        print(
            "refusing to run without an explicit --evidence-dir. No config has been loaded, no database "
            "engine has been constructed, and nothing has been written.",
            file=sys.stderr,
        )
        return 2

    evidence_dir: Path = args.evidence_dir

    cfg = load_config()
    resolved_url = resolve_database_url(cfg.database.url)
    db_path = _db_file_path(resolved_url)
    if db_path is None or not db_path.exists():
        print(f"FAIL: could not resolve a live sqlite db file from {resolved_url!r}", file=sys.stderr)
        return 1
    print(f"database (READ-ONLY handle, mode=ro + PRAGMA query_only=ON): {db_path}", file=sys.stderr)

    # --- TRUE process start: the db file + WAL sidecar fingerprint, before anything else touches it -----
    db_file_true_start = jsc.db_file_fingerprint(db_path)
    _write_json(evidence_dir / "j11-iter17-readiness-db-file-true-start.json", db_file_true_start)

    engine = _read_only_engine(db_path)

    with Session(engine) as session:
        table_count = session.exec(
            text(
                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='maintenance_boundaries'"
            )
        ).one()[0]
        guard_result = guard.evaluate_boundary_for_date(session, TARGET_DATE)

    # --- TRUE process end: captured LAST, after every read above -------------------------------------
    db_file_true_end = jsc.db_file_fingerprint(db_path)
    _write_json(evidence_dir / "j11-iter17-readiness-db-file-true-end.json", db_file_true_end)

    zero_write_proof = {
        "mtime_unchanged": db_file_true_start.get("mtime") == db_file_true_end.get("mtime"),
        "size_unchanged": db_file_true_start.get("size_bytes") == db_file_true_end.get("size_bytes"),
        "wal_unchanged": db_file_true_start.get("wal") == db_file_true_end.get("wal"),
    }

    verification = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_date": TARGET_DATE.isoformat(),
        "db_path": str(db_path),
        "maintenance_boundaries_table_count": int(table_count),
        "guard_result": guard_result,
        "expected": {"maintenance_boundaries_table_count": 0, "guard_result_blocked": False},
        "matches_expected": (
            int(table_count) == 0 and guard_result.get("blocked") is False
        ),
        "db_file_true_start": db_file_true_start,
        "db_file_true_end": db_file_true_end,
        "zero_write_proof": zero_write_proof,
        "recipe": (
            "apps/backend/.venv/bin/python "
            "apps/backend/scripts/run_j11_iter17_live_preboot_guard_verification.py "
            f"--evidence-dir {evidence_dir}"
        ),
    }
    _write_json(evidence_dir / "j11-iter17-live-preboot-guard-verification.json", verification)

    print(
        f"maintenance_boundaries_table_count={table_count} guard_result={guard_result} "
        f"matches_expected={verification['matches_expected']}",
        file=sys.stderr,
    )
    print(
        f"zero-write proof: mtime_unchanged={zero_write_proof['mtime_unchanged']} "
        f"size_unchanged={zero_write_proof['size_unchanged']} wal_unchanged={zero_write_proof['wal_unchanged']}",
        file=sys.stderr,
    )
    print("J-11 MAINTENANCE BOUNDARY: NOT ACTIVE", file=sys.stderr)
    print("J-11 LIVE PRE-BOOT GUARD: NOT ARMED", file=sys.stderr)
    return 0 if verification["matches_expected"] and all(zero_write_proof.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
