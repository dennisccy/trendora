"""goal-market-compass iter-17/iter-18 -- strictly READ-ONLY live verification of
`evaluate_boundary_for_date` (and, from iter-18, `evaluate_boundary_for_date_fail_closed`) against the
real `apps/backend/data/trendora.db`, plus the zero-live-writes proof (docs/goal.md J-11 step 11).

Iteration 17 built this to prove the boundary was NOT yet armed (the table did not exist). Iteration 18's
"OWNER RULING -- J-11 exact maintenance-boundary table creation and live arm AUTHORIZED" implementation
requirement 6 now requires the OPPOSITE direction: after the table-create + arm steps run, prove ARMED --
all eleven canonical incident dates blocked, a non-incident control date NOT blocked, the current latest
stored date (one of the eleven) blocked, PLUS that the background-warmup call site's own guard check
(added in iter-18, `j11_preboot_guard.evaluate_boundary_for_date_fail_closed` -- the literal function both
`warmup._run_warmup`'s cadence loop and `forward_testing._backfill`'s cadence loop call) ALSO reports
blocked for a quarantined date -- not merely that the synchronous-path function agrees with itself. This
script is EXTENDED in place (never replaced) to serve BOTH iterations honestly: it reports the ACTUAL live
result rather than asserting a hardcoded expectation baked in at iter-17 time, so `J-11 MAINTENANCE
BOUNDARY` / `J-11 LIVE PRE-BOOT GUARD` print ACTIVE/ARMED or NOT ACTIVE/NOT ARMED based on what the live
database actually shows today.

This script performs ZERO writes of any kind. It opens the live database through an ACTUAL read-only
SQLite handle (`file:<path>?mode=ro` + `PRAGMA query_only=ON`, the SAME `_read_only_engine` idiom
`run_j11_iter16_stage_d_readiness.py` already established -- copied here unchanged, never imported cross-
script since no shared utility module holds it today), calls the REAL, unmodified
`app.engine.j11_preboot_guard.evaluate_boundary_for_date` / `evaluate_boundary_for_date_fail_closed` for
every canonical incident date plus one control date, and independently confirms via `sqlite_master` +
direct row inspection that `maintenance_boundaries` exists (or does not) and, if present, that its
`j11-incident-recovery` row's persisted date set matches the canonical `INCIDENT_DATES` exactly. The
database file's mtime + size + `-wal` sidecar size are fingerprinted at the TRUE start and TRUE end of
THIS SCRIPT's own process (iteration-12's lesson: this bracket, not a narrow internal one, is the proof
that matters for THIS script's own zero-write claim -- the broader before/after-the-WHOLE-live-sequence
mutation accounting is a separate, wider bracket captured by the dev handoff's own evidence, per Goal 5).

goal-market-compass iter-18 rider (docs/goal.md J-11 step 11 ruling, iteration-17's own filed
recommendation -- "one can overwrite three of iteration 16's saved evidence files if its destination
folder is mistyped"): before ANY read or write, refuses (exits non-zero, touches nothing) if ANY of this
invocation's own output filenames ALREADY EXISTS under `--evidence-dir` -- catching exactly a mistyped
`--evidence-dir` pointed at an earlier iteration's already-populated evidence folder. A fresh, not-yet-
written directory (the normal case) never trips this.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_iter17_live_preboot_guard_verification.py \\
        --evidence-dir runs/goal-market-compass-iter-18
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
from app.engine import j11_maintenance as jm  # noqa: E402
from app.engine import j11_preboot_guard as guard  # noqa: E402
from app.engine import j11_stage_c as jsc  # noqa: E402
from app.models import MaintenanceBoundary, ScannerRun  # noqa: E402

# phase spec TC-3's own example: "a surviving, non-incident date" -- reused unchanged from iter-17's test
# file convention (`test_j11_preboot_guard.py`'s `NON_INCIDENT_DATE`).
CONTROL_DATE = date(2026, 7, 23)

# This invocation's own output filenames -- the rider 6a collision-refusal check enumerates exactly these
# BEFORE touching the database at all.
OUTPUT_FILENAMES = (
    "j11-iter17-readiness-db-file-true-start.json",
    "j11-iter17-readiness-db-file-true-end.json",
    "j11-iter18-live-preboot-guard-verification.json",
)


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


def _wal_effectively_unchanged(start_wal, end_wal) -> bool:
    """goal-market-compass iter-18 fix: a plain `start_wal == end_wal` (iter-17's original check) is too
    strict. `db_file_fingerprint`'s OWN docstring already documents why: "SQLite touches the WAL file on
    any connection open in WAL mode, including read-only ones" -- so if NO `-wal` sidecar exists yet the
    instant this script's read-only engine first connects, SQLite creates an empty one as a side effect of
    the connection itself, which is a harmless bookkeeping artifact, never a data write (the WAL file
    holds PENDING writes; a 0-byte WAL has none). Iter-17's own live run never exercised this branch
    (its `-wal` sidecar already existed, unchanged, at both ends) -- this iteration's live sequence is the
    first to hit it, because the table-create + arm steps immediately before this script apparently left
    SQLite's own auto-checkpoint with no `-wal` file present at all by the time their connections closed.
    Effectively unchanged means: the two dicts are identical (the common case), OR the transition is
    EXACTLY absent -> present-with-zero-bytes (the harmless connect-time artifact). Any OTHER difference
    (a WAL that grew past 0 bytes, one that disappeared, or a present-but-different one) still fails this
    check -- this fix narrows the false positive, it does not blunt the detector."""
    if start_wal == end_wal:
        return True
    start_exists = bool(start_wal) and start_wal.get("exists")
    end_exists = bool(end_wal) and end_wal.get("exists")
    return (not start_exists) and end_exists and end_wal.get("size_bytes") == 0


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
    print(f"wrote {path}", file=sys.stderr)


def _refuse_if_evidence_files_exist(evidence_dir: Path, filenames: tuple) -> list[str]:
    """goal-market-compass iter-18 rider: the destination-collision guard every J-11 evidence-writing
    script now carries. Returns the (possibly empty) list of filenames that ALREADY EXIST under
    `evidence_dir` -- a non-empty result means "refuse before writing anything, this destination has
    already been used" (catches a mistyped `--evidence-dir` pointed at an earlier iteration's populated
    folder; a fresh, not-yet-written directory never collides). Pure filesystem check -- no database
    interaction of any kind."""
    return [name for name in filenames if (evidence_dir / name).exists()]


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

    # --- rider 6a: refuse BEFORE any read or write if the destination already holds any of THIS run's ----
    # --- own output filenames (a mistyped --evidence-dir pointed at an earlier iteration's folder). ------
    colliding = _refuse_if_evidence_files_exist(evidence_dir, OUTPUT_FILENAMES)
    if colliding:
        print(
            f"refusing to run: --evidence-dir {evidence_dir} already contains {colliding} -- this looks "
            "like a mistyped destination pointed at an existing, already-populated evidence folder rather "
            "than a fresh one for this run. No database interaction, not even a read, has occurred, and "
            "no existing file has been touched.",
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
        scanner_run_count_before = session.exec(text("SELECT count(*) FROM scanner_runs")).one()[0]
        latest_daily_price_date_raw = session.exec(text("SELECT max(date) FROM daily_prices")).one()[0]

        boundary_row = None
        if table_count:
            row = session.exec(
                text(
                    "SELECT id, name, active, quarantined_dates_json, reason, updated_at "
                    "FROM maintenance_boundaries WHERE name = :name"
                ).bindparams(name=guard.J11_INCIDENT_BOUNDARY_NAME)
            ).first()
            if row is not None:
                boundary_row = {
                    "id": row[0], "name": row[1], "active": bool(row[2]),
                    "quarantined_dates_json": row[3], "reason": row[4], "updated_at": str(row[5]),
                }

        # --- the SIX live-verification conditions (ruling requirement 6), through the SAME production ---
        # --- guard entry points every boot-initiated path actually calls -- never re-derived logic. -----
        incident_date_results = {
            d.isoformat(): guard.evaluate_boundary_for_date(session, d) for d in jm.INCIDENT_DATES
        }
        control_result = guard.evaluate_boundary_for_date(session, CONTROL_DATE)

        latest_incident_date = jm.INCIDENT_DATES[-1]  # 2026-08-12, the current latest stored incident date
        latest_date_blocked = incident_date_results[latest_incident_date.isoformat()]["blocked"]

        # The background-warmup call site's OWN guard check (iter-18's new call sites in `warmup._run_
        # warmup` and `forward_testing._backfill` both call this EXACT function) -- exercised directly
        # against the live read-only session, never by starting FastAPI or running either loop for real.
        background_warmup_site_result = guard.evaluate_boundary_for_date_fail_closed(session, latest_incident_date)

        scanner_run_count_after = session.exec(text("SELECT count(*) FROM scanner_runs")).one()[0]

    # --- TRUE process end: captured LAST, after every read above -------------------------------------
    db_file_true_end = jsc.db_file_fingerprint(db_path)
    _write_json(evidence_dir / "j11-iter17-readiness-db-file-true-end.json", db_file_true_end)

    zero_write_proof = {
        "mtime_unchanged": db_file_true_start.get("mtime") == db_file_true_end.get("mtime"),
        "size_unchanged": db_file_true_start.get("size_bytes") == db_file_true_end.get("size_bytes"),
        "wal_unchanged": _wal_effectively_unchanged(db_file_true_start.get("wal"), db_file_true_end.get("wal")),
    }
    zero_scanner_runs_created = int(scanner_run_count_before) == int(scanner_run_count_after)

    all_eleven_blocked = all(r["blocked"] for r in incident_date_results.values())
    control_not_blocked = control_result["blocked"] is False
    persisted_dates = None
    persisted_dates_match_canonical = False
    if boundary_row is not None:
        try:
            persisted_dates = sorted(json.loads(boundary_row["quarantined_dates_json"]))
            persisted_dates_match_canonical = persisted_dates == sorted(
                d.isoformat() for d in jm.INCIDENT_DATES
            )
        except (TypeError, ValueError, json.JSONDecodeError):
            persisted_dates = None

    boundary_exists_and_active = boundary_row is not None and boundary_row["active"] is True
    armed = (
        boundary_exists_and_active
        and persisted_dates_match_canonical
        and all_eleven_blocked
        and control_not_blocked
        and latest_date_blocked
        and background_warmup_site_result["blocked"]
        and zero_scanner_runs_created
    )

    verification = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "control_date": CONTROL_DATE.isoformat(),
        "latest_incident_date": latest_incident_date.isoformat(),
        "latest_daily_price_date": latest_daily_price_date_raw,
        "db_path": str(db_path),
        "maintenance_boundaries_table_count": int(table_count),
        "boundary_row": boundary_row,
        "persisted_dates_match_canonical": persisted_dates_match_canonical,
        "incident_date_results": incident_date_results,
        "control_result": control_result,
        "all_eleven_incident_dates_blocked": all_eleven_blocked,
        "control_date_not_blocked": control_not_blocked,
        "latest_incident_date_blocked": latest_date_blocked,
        "background_warmup_site_result": background_warmup_site_result,
        "background_warmup_site_blocked": background_warmup_site_result["blocked"],
        "scanner_run_count_before": int(scanner_run_count_before),
        "scanner_run_count_after": int(scanner_run_count_after),
        "zero_scanner_runs_created_by_this_verification": zero_scanner_runs_created,
        "armed": armed,
        "db_file_true_start": db_file_true_start,
        "db_file_true_end": db_file_true_end,
        "zero_write_proof": zero_write_proof,
        "recipe": (
            "apps/backend/.venv/bin/python "
            "apps/backend/scripts/run_j11_iter17_live_preboot_guard_verification.py "
            f"--evidence-dir {evidence_dir}"
        ),
    }
    _write_json(evidence_dir / "j11-iter18-live-preboot-guard-verification.json", verification)

    print(
        f"maintenance_boundaries_table_count={table_count} all_eleven_blocked={all_eleven_blocked} "
        f"control_not_blocked={control_not_blocked} latest_date_blocked={latest_date_blocked} "
        f"background_warmup_site_blocked={background_warmup_site_result['blocked']} "
        f"zero_scanner_runs_created={zero_scanner_runs_created} armed={armed}",
        file=sys.stderr,
    )
    print(
        f"zero-write proof: mtime_unchanged={zero_write_proof['mtime_unchanged']} "
        f"size_unchanged={zero_write_proof['size_unchanged']} wal_unchanged={zero_write_proof['wal_unchanged']}",
        file=sys.stderr,
    )
    print(f"J-11 MAINTENANCE BOUNDARY: {'ACTIVE' if boundary_exists_and_active else 'NOT ACTIVE'}", file=sys.stderr)
    print(f"J-11 LIVE PRE-BOOT GUARD: {'ARMED' if armed else 'NOT ARMED'}", file=sys.stderr)
    return 0 if armed and all(zero_write_proof.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
