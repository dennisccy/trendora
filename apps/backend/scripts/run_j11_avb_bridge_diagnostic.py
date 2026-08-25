"""goal-market-compass iter-14/15 -- J-11 Stage D readiness: the READ-ONLY AVB bridge/volume diagnostic
(Goal 4). No `--confirm` needed -- this script performs ZERO writes of any kind: it opens the live
database through an ACTUAL read-only SQLite handle (`file:<path>?mode=ro` + `PRAGMA query_only=ON`,
mirroring `run_j11_stage_b1_live_reverification.py`'s helper), so any accidental write attempt anywhere
in the call graph would raise `OperationalError` rather than silently succeeding. It still captures the
db-file mtime/size and `-wal` sidecar size at the TRUE process start and TRUE process end as corroborating
evidence (iteration 12's lesson), even though no writable connection is ever opened. This script performs
NO network fetch of any kind -- it consumes `app.engine.j11_avb_provider_fetch`'s ALREADY-PERSISTED
evidence (`--provider-fetch-evidence-path`, produced separately by
`run_j11_avb_provider_fetch.py`), never constructs a provider itself.

Composes `app.engine.j11_avb_diagnostic`'s pure/read functions:
  - re-derives the bridge factor + calibration pairs from the PERSISTED J-10 evidence file (never
    re-fetched -- AG-9's ORIGINAL J-10 recovery-fetch exception is exhausted; this is a SEPARATE, later
    dated exception);
  - goal-market-compass iter-15 (Goals 2/3): classifies AVB's actual stored convention per window from a
    GENUINE cross-source comparison against Goal 2's fetched provider close+volume evidence
    (`classify_local_convention_with_volume_evidence`) -- no longer the price-only tautology iteration 14
    left behind;
  - computes the three counterfactual ADV representations (A/B/C) for ALL SIX AG-9-permitted dates (the
    calibration window AND the two recovered dates -- not only the recovered dates, as iteration 14 did),
    representation B now sourced from the FETCHED evidence;
  - traces the decision impact through the named canonical modules
    (`universe_resolver._adv_dollar`/`resolve_candidate`, `scoring`'s liquidity component, the Risk
    score/bucket, setup status, candidate eligibility, and the pool-wide liquidity-percentile shift) for
    both 2026-08-11 and 2026-08-12, now substituting BOTH close AND fetched volume (`volume_override`);
  - classifies into exactly one of AVB-A/B/C/D, mechanically, from the volume-aware evidence.

goal-market-compass iter-15 (Goal 6): `--output-path` carries NO default -- it used to default to
`runs/goal-market-compass-iter-14`, a real committed evidence directory, the exact footgun pattern that
overwrote three committed iteration-13 evidence files in iteration 14. Refuses BEFORE any engine
construction, mirroring the already-fixed `run_j11_stage_c_bounded_clear.py` pattern exactly.
`--provider-fetch-evidence-path` is ALSO required -- Goal 2's fetch evidence is this script's ONLY source
of provider close/volume; there is no fallback default that could silently substitute a stale or wrong
fetch artifact.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_avb_bridge_diagnostic.py \\
        --output-path runs/goal-market-compass-iter-15/j11-avb-bridge-diagnostic.json \\
        --provider-fetch-evidence-path runs/goal-market-compass-iter-15/j11-avb-provider-fetch-evidence.json
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

CANONICAL_OUTPUT_PATH_FOR_DOCS = REPO_ROOT / "runs" / "goal-market-compass-iter-15" / "j11-avb-bridge-diagnostic.json"
PERMITTED_DATES = diag.CALIBRATION_DATES + diag.RECOVERED_DATES


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
    parser.add_argument(
        "--output-path", type=Path, default=None,
        help=(
            "required -- the diagnostic JSON this script writes. Has NO default on purpose (Goal 6): the "
            f"real target this iteration ({CANONICAL_OUTPUT_PATH_FOR_DOCS}) is a committed evidence "
            "directory, and an implicit default meant a forgotten flag could overwrite committed "
            "forensic evidence instead of failing."
        ),
    )
    parser.add_argument(
        "--provider-fetch-evidence-path", type=Path, default=None,
        help=(
            "required -- Goal 2's persisted AVB provider-fetch evidence JSON (produced by "
            "run_j11_avb_provider_fetch.py). This is this script's ONLY source of provider close/volume "
            "-- it performs no network fetch itself, and there is no fallback default."
        ),
    )
    parser.add_argument(
        "--j10-evidence-path", type=Path, default=diag.DEFAULT_J10_EVIDENCE_PATH,
        help="the persisted J-10 population-recovery evidence file (for the bridge factor) -- read-only "
             "input, never re-fetched.",
    )
    args = parser.parse_args()

    missing = [
        name for name, value in (
            ("--output-path", args.output_path), ("--provider-fetch-evidence-path", args.provider_fetch_evidence_path),
        ) if value is None
    ]
    if missing:
        print(
            f"refusing to run without explicit {', '.join(missing)}. No config has been loaded, no "
            "database engine has been constructed, and nothing has been written.",
            file=sys.stderr,
        )
        return 2

    fetch_evidence = json.loads(Path(args.provider_fetch_evidence_path).read_text())
    provider_evidence_by_date: dict = fetch_evidence.get("per_date", {})
    print(
        f"loaded Goal 2 fetch evidence from {args.provider_fetch_evidence_path}: "
        f"sufficient_evidence={fetch_evidence.get('sufficient_evidence')} "
        f"missing_dates={fetch_evidence.get('missing_dates')}",
        file=sys.stderr,
    )

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
        # goal-market-compass iter-15 (Goals 2/3): the volume-aware classifier, fed Goal 2's fetched
        # evidence -- NOT the old price-only `classify_local_convention` (kept unchanged elsewhere as a
        # documented fallback/cross-check, never used here as the primary classification input anymore).
        local_convention = diag.classify_local_convention_with_volume_evidence(
            stored_series, evidence_row, provider_evidence_by_date
        )

        # goal-market-compass iter-15 (Goal 3): ALL SIX permitted dates, not only the two recovered ones.
        stored_rows_by_date = {row["date"]: row for row in stored_series}
        representations_by_date = {}
        for one_date in PERMITTED_DATES:
            key = one_date.isoformat()
            stored_row = stored_rows_by_date.get(key)
            if stored_row is None:
                continue
            representations_by_date[key] = diag.compute_counterfactual_representations(
                bridge_factor, stored_row["close"], stored_row["volume"],
                provider_evidence=provider_evidence_by_date.get(key),
            )

        # goal-market-compass iter-15 (Goal 5): the decision-impact trace substitutes BOTH close AND the
        # GENUINELY FETCHED volume for the two recovered dates -- volume_override sourced strictly from
        # dates with sufficient fetched evidence; a date without it simply has no override entry (the
        # trace degrades gracefully to close-only substitution for THAT date, while the classifier above
        # already forces AVB-D on any missing-evidence date, so a degraded trace for that one date is
        # never trusted as the basis for readiness either way).
        volume_override = {
            one_date: provider_evidence_by_date[one_date.isoformat()]["volume"]
            for one_date in diag.RECOVERED_DATES
            if one_date.isoformat() in provider_evidence_by_date
            and provider_evidence_by_date[one_date.isoformat()].get("volume") is not None
        }

        decision_impact_by_date: dict[str, dict] = {}
        for one_date in diag.RECOVERED_DATES:
            key = one_date.isoformat()
            print(f"tracing decision impact for {key} ...", file=sys.stderr)
            ur_impact = diag.trace_universe_resolver_impact(
                session, cfg, one_date, bridge_factor, volume_override=volume_override
            )
            scoring_impact = diag.trace_scoring_and_selection_impact(
                session, cfg, one_date, bridge_factor, volume_override=volume_override
            )
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
    # Goal 4: the fetch itself failing closed (insufficient evidence for one or more permitted dates)
    # forces AVB-D regardless of what the convention/impact classification above concluded -- named per
    # the amendment's own words ("If the fetch comes back insufficient... the correct outcome is AVB-D").
    if not fetch_evidence.get("sufficient_evidence", False):
        classification = dict(classification)
        classification["classification"] = "AVB-D"
        classification["stage_d_ready_per_avb"] = False
        classification["reasoning"] = (
            "Goal 2's AG-9 dated-exception-#2 fetch did NOT supply sufficient evidence for all six "
            f"permitted dates (missing_dates={fetch_evidence.get('missing_dates')}); classifying AVB-D "
            "per the amendment's own fail-closed rule -- never a guess, never a substituted adjacent-day "
            f"statistic. Underlying convention/impact classification (informational only, NOT trusted "
            f"as the basis for readiness): {classification['classification']} -- {classification['reasoning']}"
        )

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
        "provider_fetch_evidence_path": str(args.provider_fetch_evidence_path),
        "provider_fetch_evidence_sufficient": fetch_evidence.get("sufficient_evidence"),
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
