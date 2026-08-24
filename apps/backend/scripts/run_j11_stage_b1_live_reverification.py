"""goal-market-compass iter-12 -- J-11 Stage B1 CLEANUP: read-only live re-verification of

  (TC-20) the FIXED `app.engine.compass.basis_disclosure`'s status distribution across all 24 live
  `next_session_manifests` rows -- independently re-derived, never copied from the plan/spec, and
  asserting none of the degenerate-`generation_json` rows reports `available`.

  (TC-23) the `preFreezeEra` branch honesty question (ruling A11a) -- a fresh read-only query for live
  manifests where `generation_json` is NULL/empty/malformed AND `mode IS NULL`, independently re-deriving
  whether that set is complete, partial, or empty relative to the total `mode IS NULL` count.

Opens the live database through an ACTUAL read-only SQLite handle (`file:<path>?mode=ro` +
`PRAGMA query_only=ON`), mirroring `run_j11_stage_b1_cleanup_fingerprint.py`'s helper. `basis_disclosure`
itself only ever issues SELECTs (never a write) -- confirmed by the read-only handle itself: any write
attempt anywhere in this call graph would raise `OperationalError` rather than silently succeeding.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_b1_live_reverification.py \\
        --output-path runs/goal-market-compass-iter-12/j11-stage-b1-live-reverification.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# scripts/ -> backend -> apps -> repo root
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, event, func, text  # noqa: E402
from sqlmodel import Session, select  # noqa: E402

from app.config import load_config  # noqa: E402
from app.db import resolve_database_url  # noqa: E402
from app.engine import compass  # noqa: E402
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
    url = f"sqlite:///file:{db_path}?mode=ro&uri=true"
    engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _set_query_only(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA query_only=ON")

    return engine


def _is_degenerate_generation_json(value) -> bool:
    """NULL, empty string, or malformed/non-object/key-absent JSON -- the exact predicate
    `basis_disclosure`'s fail-closed guards apply, re-derived independently here (never assumed) for the
    TC-23 overlap question. Mirrors `basis_disclosure`'s own guard logic exactly (no second formula)."""
    if not value:
        return True
    try:
        parsed = json.loads(value)
    except (ValueError, TypeError):
        return True
    return not isinstance(parsed, dict) or "source_run_created_at" not in parsed


def reverify_basis_disclosure_distribution(session: Session) -> dict:
    """TC-20: run the FIXED `basis_disclosure` read-only against every live manifest row, tally the
    resulting status distribution, and separately tally it restricted to the rows whose `generation_json`
    is degenerate (NULL/empty/malformed/non-object/key-absent) -- asserting none of those report
    `available` (the exact fail-open this iteration's A4/A4-bis fixes close)."""
    rows = session.exec(select(NextSessionManifest).order_by(NextSessionManifest.as_of, NextSessionManifest.version)).all()
    overall = Counter()
    degenerate_generation_json = Counter()
    per_row = []
    for row in rows:
        disclosure = compass.basis_disclosure(session, row)
        overall[disclosure["status"]] += 1
        degenerate = _is_degenerate_generation_json(row.generation_json)
        if degenerate:
            degenerate_generation_json[disclosure["status"]] += 1
        per_row.append(
            {
                "id": row.id,
                "as_of": row.as_of.isoformat(),
                "version": row.version,
                "mode": row.mode,
                "generation_json_degenerate": degenerate,
                "basis_status": disclosure["status"],
                "basis_detail": disclosure["detail"],
            }
        )
    return {
        "total_manifest_rows": len(rows),
        "overall_status_distribution": dict(overall),
        "degenerate_generation_json_status_distribution": dict(degenerate_generation_json),
        "no_degenerate_row_reports_available": degenerate_generation_json.get("available", 0) == 0,
        "per_row": per_row,
    }


def reverify_pre_freeze_era_overlap(session: Session) -> dict:
    """TC-23: independently re-derive (a) the count of live manifests where `generation_json` is
    degenerate AND `mode IS NULL` (the `preFreezeEra` predicate in `compass-manifest-strip.tsx`), (b) the
    total `mode IS NULL` count, and (c) whether the overlap is complete (every `mode IS NULL` row is also
    generation_json-degenerate and vice versa), partial, or empty. Read-only re-derivation only -- never
    copied from a prior iteration's or this iteration's own plan."""
    mode_null_count = session.scalar(select(func.count()).select_from(NextSessionManifest).where(NextSessionManifest.mode.is_(None)))
    rows = session.exec(select(NextSessionManifest)).all()
    mode_null_ids = {row.id for row in rows if row.mode is None}
    degenerate_ids = {row.id for row in rows if _is_degenerate_generation_json(row.generation_json)}
    overlap = mode_null_ids & degenerate_ids
    only_mode_null = mode_null_ids - degenerate_ids
    only_degenerate = degenerate_ids - mode_null_ids
    complete_overlap = mode_null_ids == degenerate_ids and len(mode_null_ids) > 0
    return {
        "mode_is_null_count": int(mode_null_count or 0),
        "generation_json_degenerate_count": len(degenerate_ids),
        "overlap_count": len(overlap),
        "mode_is_null_but_not_degenerate_ids": sorted(only_mode_null),
        "degenerate_but_mode_is_not_null_ids": sorted(only_degenerate),
        "complete_overlap": complete_overlap,
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
    with Session(engine) as session:
        tc20 = reverify_basis_disclosure_distribution(session)
        tc23 = reverify_pre_freeze_era_overlap(session)
    mtime_after = db_path.stat().st_mtime

    result = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "tc20_basis_disclosure_live_reverification": tc20,
        "tc23_pre_freeze_era_overlap_reverification": tc23,
        "db_file_mtime_before": mtime_before,
        "db_file_mtime_after": mtime_after,
        "db_file_mtime_unchanged": mtime_before == mtime_after,
    }

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(json.dumps(result, indent=2, sort_keys=True, default=str))
    print(f"wrote {args.output_path}", file=sys.stderr)
    print(
        f"TC-20 overall={tc20['overall_status_distribution']} "
        f"degenerate={tc20['degenerate_generation_json_status_distribution']} "
        f"no_degenerate_available={tc20['no_degenerate_row_reports_available']}",
        file=sys.stderr,
    )
    print(
        f"TC-23 mode_null={tc23['mode_is_null_count']} degenerate={tc23['generation_json_degenerate_count']} "
        f"overlap={tc23['overlap_count']} complete={tc23['complete_overlap']}",
        file=sys.stderr,
    )
    print(f"mtime_unchanged={result['db_file_mtime_unchanged']}", file=sys.stderr)
    return 0 if tc20["no_degenerate_row_reports_available"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
