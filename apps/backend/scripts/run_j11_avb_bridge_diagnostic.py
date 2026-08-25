"""goal-market-compass iter-14 -- J-11 Stage D readiness: the READ-ONLY AVB bridge/volume diagnostic
(Goal 4). No `--confirm` needed -- this script performs ZERO writes of any kind: it opens the live
database through an ACTUAL read-only SQLite handle (`file:<path>?mode=ro` + `PRAGMA query_only=ON`,
mirroring `run_j11_stage_b1_live_reverification.py`'s helper), so any accidental write attempt anywhere
in the call graph would raise `OperationalError` rather than silently succeeding. It still captures the
db-file mtime/size and `-wal` sidecar size at the TRUE process start and TRUE process end as corroborating
evidence (iteration 12's lesson), even though no writable connection is ever opened.

Composes `app.engine.j11_avb_diagnostic`'s pure/read functions:
  - re-derives the bridge factor + calibration pairs from the PERSISTED J-10 evidence file (never
    re-fetched -- AG-9's recovery-fetch exception is exhausted);
  - classifies AVB's actual stored local convention per window from the stored `daily_prices` series
    itself;
  - computes the three counterfactual ADV representations (A/B/C) for both recovered dates;
  - traces the decision impact through the named canonical modules
    (`universe_resolver._adv_dollar`/`resolve_candidate`, `scoring`'s liquidity component, the Risk
    score/bucket, setup status, candidate eligibility, and the pool-wide liquidity-percentile shift) for
    both 2026-08-11 and 2026-08-12;
  - classifies into exactly one of AVB-A/B/C/D.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_avb_bridge_diagnostic.py \\
        [--output-path runs/goal-market-compass-iter-14/j11-avb-bridge-diagnostic.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

# scripts/ -> backend -> apps -> repo root
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, event  # noqa: E402
from sqlmodel import Session  # noqa: E402

from app.config import load_config  # noqa: E402
from app.db import resolve_database_url  # noqa: E402
from app.engine import j11_avb_diagnostic as diag  # noqa: E402
from app.engine.j11_stage_c import db_file_fingerprint  # noqa: E402

DEFAULT_OUTPUT_PATH = REPO_ROOT / "runs" / "goal-market-compass-iter-14" / "j11-avb-bridge-diagnostic.json"


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
    url = f"sqlite:///file:{db_path}?mode=ro&uri=true"
    engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _set_query_only(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA query_only=ON")

    return engine


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument(
        "--j10-evidence-path", type=Path, default=diag.DEFAULT_J10_EVIDENCE_PATH,
        help="the persisted J-10 population-recovery evidence file -- never re-fetched.",
    )
    args = parser.parse_args()

    cfg = load_config()
    resolved_url = resolve_database_url(cfg.database.url)
    db_path = _db_file_path(resolved_url)
    if db_path is None or not db_path.exists():
        print(f"FAIL: could not resolve a live sqlite db file from {resolved_url!r}", file=sys.stderr)
        return 1
    print(f"database (READ-ONLY handle, mode=ro + PRAGMA query_only=ON): {db_path}", file=sys.stderr)

    db_file_true_start = db_file_fingerprint(db_path)

    evidence_row = diag.load_j10_avb_evidence(args.j10_evidence_path)
    bridge_factor = evidence_row["bridge_factor"]
    pool_distribution = diag.summarize_pool_bridge_factor_distribution(args.j10_evidence_path)
    print(
        f"bridge_factor={bridge_factor} avb_is_unique_material_outlier="
        f"{pool_distribution['avb_is_unique_material_outlier']}",
        file=sys.stderr,
    )

    engine = _read_only_engine(db_path)
    with Session(engine) as session:
        # a broad window around the incident: from well before the calibration window through the
        # current stored frontier, so the convention classifier's continuity check has real adjacent
        # context on both sides of the recovery boundary.
        stored_series = diag.fetch_avb_stored_series(session, date(2026, 6, 1), date(2026, 12, 31))
        local_convention = diag.classify_local_convention(stored_series, evidence_row)

        recovered_rows_by_date = {row["date"]: row for row in stored_series if row["date"] in
                                   {d.isoformat() for d in diag.RECOVERED_DATES}}
        representations_by_date = {
            iso_date: diag.compute_counterfactual_representations(bridge_factor, row["close"], row["volume"])
            for iso_date, row in recovered_rows_by_date.items()
        }

        decision_impact_by_date: dict[str, dict] = {}
        for one_date in diag.RECOVERED_DATES:
            key = one_date.isoformat()
            print(f"tracing decision impact for {key} ...", file=sys.stderr)
            ur_impact = diag.trace_universe_resolver_impact(session, cfg, one_date, bridge_factor)
            scoring_impact = diag.trace_scoring_and_selection_impact(session, cfg, one_date, bridge_factor)
            decision_impact_by_date[key] = {
                "universe_resolver": ur_impact,
                "scoring_and_selection": scoring_impact,
            }
            print(
                f"  {key}: admission_changed={ur_impact['admission_changed']} "
                f"avb_resolved_member={scoring_impact.get('avb_resolved_member')} "
                f"risk_bucket_a={scoring_impact.get('risk_bucket_a')} "
                f"risk_bucket_b={scoring_impact.get('risk_bucket_b')} "
                f"eligible_a={scoring_impact.get('eligible_a')} eligible_b={scoring_impact.get('eligible_b')}",
                file=sys.stderr,
            )

    classification = diag.classify_avb(local_convention, decision_impact_by_date)

    db_file_true_end = db_file_fingerprint(db_path)
    zero_write = {
        "db_file_true_start": db_file_true_start,
        "db_file_true_end": db_file_true_end,
        "mtime_unchanged": db_file_true_start.get("mtime") == db_file_true_end.get("mtime"),
        "size_unchanged": db_file_true_start.get("size_bytes") == db_file_true_end.get("size_bytes"),
        "wal_empty_at_start": (db_file_true_start.get("wal") or {}).get("size_bytes", 0) in (0, None)
        if db_file_true_start.get("wal", {}).get("exists") else True,
        "wal_empty_at_end": (db_file_true_end.get("wal") or {}).get("size_bytes", 0) in (0, None)
        if db_file_true_end.get("wal", {}).get("exists") else True,
    }

    result = {
        "generated_at": diag._now_iso(),
        "j10_evidence_path": str(args.j10_evidence_path),
        "bridge_factor": bridge_factor,
        "calibration_pairs": evidence_row.get("pairs"),
        "pool_bridge_factor_distribution": pool_distribution,
        "stored_series_window": {"start": "2026-06-01", "end": "2026-12-31", "row_count": len(stored_series)},
        "local_convention": local_convention,
        "counterfactual_representations_by_date": representations_by_date,
        "decision_impact_by_date": decision_impact_by_date,
        "classification": classification,
        "zero_write_proof": zero_write,
    }

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(json.dumps(result, indent=2, sort_keys=True, default=str))
    print(f"wrote {args.output_path}", file=sys.stderr)
    print(
        f"AVB classification: {classification['classification']} "
        f"stage_d_ready_per_avb={classification['stage_d_ready_per_avb']}",
        file=sys.stderr,
    )
    print(f"zero_write_proof: {zero_write}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
