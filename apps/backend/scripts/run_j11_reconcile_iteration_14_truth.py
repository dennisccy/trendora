"""goal-market-compass iter-15 -- J-11 Stage D readiness, Goal 1: the READ-ONLY CLI wrapper for
`app.engine.j11_stage_d.reconcile_prior_iteration_truth`.

Re-derives, LIVE and READ-ONLY, the figures the dispatching coordinator's true-start capture named
(db mtime/size, all-11-incident-dates-zero, `daily_prices`/`scanner_runs`/`forward_returns`/
`data_provider_runs`/manifest/`watchlist`/AVB-fingerprint counts), compares each against that capture
(verify, never trust), and reconciles iteration 14's two contradictory J-11 Stage D readiness conclusions
-- the stale `runs/goal-market-compass-iter-14/j11-stage-d-readiness.json` (`avb_classification: "AVB-B"`,
`ready: true`) against `runs/goal-session-market-compass/iter-14/eval.md`'s own corrected owner-facing
line (`J-11 STAGE D READY: NO`).

Opens the live database through an ACTUAL read-only SQLite handle (`file:<path>?mode=ro` + `PRAGMA
query_only=ON`), so any accidental write attempt anywhere in the call graph would raise
`OperationalError` rather than silently succeeding. Does NOT edit, delete, or regenerate EITHER source
file -- both are loaded read-only and quoted verbatim inside the NEW artifact this script writes.

`--output-path` carries NO default (Goal 6's guard, applied to this new script from the start): an
omitted flag must fail loudly rather than silently landing this iteration's reconciliation artifact
somewhere unintended.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_reconcile_iteration_14_truth.py \\
        --output-path runs/goal-market-compass-iter-15/j11-iteration-14-truth-reconciliation.json \\
        [--iteration-14-readiness-path runs/goal-market-compass-iter-14/j11-stage-d-readiness.json] \\
        [--iteration-14-eval-md-path runs/goal-session-market-compass/iter-14/eval.md] \\
        [--db-file-true-start-path PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# scripts/ -> backend -> apps -> repo root
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, event  # noqa: E402
from sqlmodel import Session  # noqa: E402

from app.config import load_config  # noqa: E402
from app.db import resolve_database_url  # noqa: E402
from app.engine import j11_stage_c as jsc  # noqa: E402
from app.engine import j11_stage_d as jsd  # noqa: E402

DEFAULT_ITERATION_14_READINESS_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-14" / "j11-stage-d-readiness.json"
)
DEFAULT_ITERATION_14_EVAL_MD_PATH = REPO_ROOT / "runs" / "goal-session-market-compass" / "iter-14" / "eval.md"


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
            "required -- the reconciliation JSON this script writes. Has NO default on purpose (Goal 6): "
            "an omitted flag must fail loudly rather than silently landing this artifact somewhere "
            "unintended."
        ),
    )
    parser.add_argument(
        "--iteration-14-readiness-path", type=Path, default=DEFAULT_ITERATION_14_READINESS_PATH,
        help="read-only input -- iteration 14's stale j11-stage-d-readiness.json, loaded verbatim, "
             "never edited.",
    )
    parser.add_argument(
        "--iteration-14-eval-md-path", type=Path, default=DEFAULT_ITERATION_14_EVAL_MD_PATH,
        help="read-only input -- iteration 14's evaluator report, for its own corrected owner-facing line.",
    )
    parser.add_argument(
        "--db-file-true-start-path", type=Path, default=None,
        help="reuse an earlier-in-this-iteration TRUE process-start db-file fingerprint, if any -- "
             "brackets the whole-iteration zero-write proof across every script this iteration runs.",
    )
    args = parser.parse_args()

    if args.output_path is None:
        print(
            "refusing to run without an explicit --output-path. No config has been loaded, no database "
            "engine has been constructed, and nothing has been written.",
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

    if args.db_file_true_start_path is not None and args.db_file_true_start_path.exists():
        db_file_true_start = json.loads(args.db_file_true_start_path.read_text())
        print(f"reusing earlier TRUE process-start fingerprint from {args.db_file_true_start_path}", file=sys.stderr)
    else:
        db_file_true_start = jsc.db_file_fingerprint(db_path)

    engine = _read_only_engine(db_path)
    with Session(engine) as session:
        result = jsd.reconcile_prior_iteration_truth(
            session, engine, db_path,
            iteration_14_readiness_path=args.iteration_14_readiness_path,
            iteration_14_eval_md_path=args.iteration_14_eval_md_path,
        )

    db_file_true_end = jsc.db_file_fingerprint(db_path)
    result["zero_write_proof"] = {
        "db_file_true_start": db_file_true_start,
        "db_file_true_end": db_file_true_end,
        "mtime_unchanged": db_file_true_start.get("mtime") == db_file_true_end.get("mtime"),
        "size_unchanged": db_file_true_start.get("size_bytes") == db_file_true_end.get("size_bytes"),
    }

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(json.dumps(result, indent=2, sort_keys=True, default=str))
    print(f"wrote {args.output_path}", file=sys.stderr)
    print(f"any_mismatch_against_owner_capture={result['any_mismatch_against_owner_capture']}", file=sys.stderr)
    print(
        f"forward_returns_measured_into_incident_total_matches_16614="
        f"{result['forward_returns_measured_into_incident_total_matches_16614']}",
        file=sys.stderr,
    )
    print(
        f"iteration-14 stale artifact superseded: "
        f"{result['iteration_14_stale_artifact']['stale_artifact_superseded']}",
        file=sys.stderr,
    )
    return 0 if not result["any_mismatch_against_owner_capture"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
