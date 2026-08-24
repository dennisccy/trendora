"""goal-market-compass iter-12 -- J-11 Stage B1 CLEANUP: read-only before/after fingerprint of the LIVE
database (ruling A13: "Expected live writes: ZERO... verify before and after... using the strongest
practical read-only fingerprinting the J-11 evidence framework already provides. Do not claim 'no write'
from row counts alone.").

Reuses the existing primitives directly rather than inventing new ones (per this iteration's plan):
  - `app.engine.j11_schema_migration.capture_full_db_snapshot` -- every table's row count + db file
    mtime/size.
  - `app.engine.j11_schema_migration.fetch_object_ddl` -- the manifest table's own `CREATE TABLE` text
    plus its named indexes' `CREATE INDEX` text, read verbatim from `sqlite_master`.
  - `app.engine.j11_schema_migration.dump_table` -- every row x every column of
    `next_session_manifests`, ordered by `id`.
  - `app.engine.j11_maintenance.capture_pre_reset_inventory` -- the `daily_prices` row-count + content
    fingerprint construction (row_count, min_date, max_date, id_sum, ohlcv_sum -> sha256), plus
    `data_provider_runs`/`watchlist` row counts and the certified/staging ledger file hashes, all in one
    read-only call.

Opens the live database through an ACTUAL read-only SQLite handle -- `file:<path>?mode=ro` (SQLite-level
read-only open; any write attempt raises `OperationalError`) plus an explicit `PRAGMA query_only=ON` on
every connection (belt-and-braces) -- never the pooled `app.db.get_engine()` writable engine this
iteration, since Stage B1 cleanup's live database contract is READ-ONLY (ruling A13), unlike iter-10/11's
scripts which were the ONE authorized writer for their own bounded operations.

Usage (run twice -- once before this iteration's work, once after -- then diffed by
`run_j11_stage_b1_cleanup_fingerprint_diff.py`):
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_b1_cleanup_fingerprint.py \\
        --output-path runs/goal-market-compass-iter-12/j11-stage-b1-cleanup-fingerprint-before.json
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
from app.engine import j11_schema_migration as migration  # noqa: E402
from app.engine.j11_maintenance import capture_pre_reset_inventory  # noqa: E402
from app.models import NextSessionManifest  # noqa: E402


def _db_file_path(database_url: str) -> "Path | None":
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None
    raw = database_url[len(prefix):]
    if not raw or raw == ":memory:":
        return None
    path = Path(raw)
    return path if path.is_absolute() else (REPO_ROOT / path)


def _read_only_engine(db_path: Path):
    """An ACTUAL read-only SQLite connection -- `mode=ro` at the SQLite C-API level (any write attempt
    raises `sqlite3.OperationalError: attempt to write a readonly database`) plus an explicit
    `PRAGMA query_only=ON` issued on every new connection (defense in depth), mirroring the pattern this
    repo's own iter-11 audit used for its live read-only checks and
    `apps/backend/tests/_seed_subset.py`'s `_attach_real_db_readonly`."""
    url = f"sqlite:///file:{db_path}?mode=ro&uri=true"
    engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _set_query_only(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA query_only=ON")

    return engine


def capture_fingerprint(engine, db_path: Path) -> dict:
    full_snapshot = migration.capture_full_db_snapshot(engine, db_path)
    manifest_ddl = migration.fetch_object_ddl(engine, migration.TABLE_NAME)
    manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
    with Session(engine) as session:
        pre_reset_inventory = capture_pre_reset_inventory(session)
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "full_db_snapshot": full_snapshot,
        "manifest_ddl": manifest_ddl,
        "manifest_dump": manifest_dump,
        "manifest_row_count": len(manifest_dump),
        "pre_reset_inventory": pre_reset_inventory,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-path", type=Path, required=True)
    args = parser.parse_args()

    cfg = load_config()
    resolved_url = resolve_database_url(cfg.database.url)
    db_path = _db_file_path(resolved_url)
    if db_path is None or not db_path.exists():
        print(f"FAIL: could not resolve a live sqlite db file from {resolved_url!r}", file=sys.stderr)
        return 1
    print(f"database (READ-ONLY handle, mode=ro + PRAGMA query_only=ON): {db_path}", file=sys.stderr)

    mtime_before = db_path.stat().st_mtime
    engine = _read_only_engine(db_path)
    fingerprint = capture_fingerprint(engine, db_path)
    mtime_after = db_path.stat().st_mtime
    fingerprint["db_file_mtime_before_capture"] = mtime_before
    fingerprint["db_file_mtime_after_capture"] = mtime_after
    fingerprint["db_file_mtime_unchanged_by_this_capture"] = mtime_before == mtime_after

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(json.dumps(fingerprint, indent=2, sort_keys=True, default=str))
    print(f"wrote {args.output_path}", file=sys.stderr)
    print(
        f"manifest_row_count={fingerprint['manifest_row_count']} "
        f"daily_prices_row_count={fingerprint['pre_reset_inventory']['daily_prices']['row_count']} "
        f"mtime_unchanged_by_this_capture={fingerprint['db_file_mtime_unchanged_by_this_capture']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
