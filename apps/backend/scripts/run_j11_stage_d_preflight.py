"""goal-market-compass iter-14 -- J-11 Stage D readiness: the READ-ONLY Stage D preflight gate (Goal 1 +
Goal 3a), executed live against `apps/backend/data/trendora.db` THIS iteration -- permitted (zero
writes), distinct from Stage D's own regeneration, which remains unauthorized and is NOT attempted
anywhere in this script.

Opens the live database through an ACTUAL read-only SQLite handle (`file:<path>?mode=ro` + `PRAGMA
query_only=ON`, mirroring `run_j11_stage_b1_live_reverification.py`'s helper) -- any accidental write
attempt anywhere in the call graph would raise `OperationalError` rather than silently succeeding. No
`--confirm` flag: there is nothing here to confirm, since nothing is ever written.

Sequence:
  1. Freeze a FRESH Stage D attempt identity (`j11_stage_d.freeze_stage_d_attempt_identity`) -- never
     hardcodes iteration 10's `6261ca17...` or iteration 13's `53d2ffd1...`.
  2. Capture the Stage D preflight (`j11_stage_d.capture_stage_d_preflight`) -- re-derives live state
     fresh, including Check (A)'s identity comparison against a SECOND independent recomputation.
  3. Load the certified post-Stage-C baseline from iteration 13's own persisted artifacts
     (`j11_stage_d.load_stage_d_certified_baseline`) and run the comparison gate
     (`compare_stage_d_preflight_to_certified`) + verdict (`stage_d_preflight_verdict`).
  4. Persist every artifact; the verdict alone does NOT authorize Stage D (a separate owner instruction
     is required -- the C10/A12 pattern).

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_d_preflight.py \\
        [--evidence-dir runs/goal-market-compass-iter-14] \\
        [--stage-c-preflight-path runs/goal-market-compass-iter-13/j11-stage-c-preflight.json] \\
        [--stage-c-mutation-accounting-path runs/goal-market-compass-iter-13/j11-stage-c-mutation-accounting.json] \\
        [--db-file-true-start-path PATH]   # reuse an earlier-in-this-iteration true-start capture, if any
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

DEFAULT_EVIDENCE_DIR = REPO_ROOT / "runs" / "goal-market-compass-iter-14"
DEFAULT_STAGE_C_PREFLIGHT_PATH = REPO_ROOT / "runs" / "goal-market-compass-iter-13" / "j11-stage-c-preflight.json"
DEFAULT_STAGE_C_MUTATION_ACCOUNTING_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-13" / "j11-stage-c-mutation-accounting.json"
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
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE_DIR)
    parser.add_argument("--stage-c-preflight-path", type=Path, default=DEFAULT_STAGE_C_PREFLIGHT_PATH)
    parser.add_argument(
        "--stage-c-mutation-accounting-path", type=Path, default=DEFAULT_STAGE_C_MUTATION_ACCOUNTING_PATH
    )
    parser.add_argument(
        "--db-file-true-start-path", type=Path, default=None,
        help="an earlier-in-this-iteration TRUE process-start db-file fingerprint (e.g. from the AVB "
             "diagnostic script, if it ran first) -- reused verbatim as the whole-iteration start instead "
             "of re-capturing one here, so the whole-iteration zero-write proof brackets every live read "
             "this iteration performed, not just this script's own span.",
    )
    args = parser.parse_args()

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
    _write_json(args.evidence_dir / "j11-stage-d-db-file-true-start.json", db_file_true_start)

    goal_md_text = jsc.read_goal_md_text()
    git_head = jsc.read_git_head()
    engine = _read_only_engine(db_path)

    with Session(engine) as session:
        attempt_identity = jsd.freeze_stage_d_attempt_identity(
            session, cfg, git_head=git_head, goal_md_text=goal_md_text
        )
        _write_json(args.evidence_dir / "j11-stage-d-attempt-identity.json", attempt_identity)
        print(f"frozen Stage D attempt identity: engine_identity={attempt_identity['engine_identity']}", file=sys.stderr)

        preflight = jsd.capture_stage_d_preflight(
            session, engine, db_path, goal_md_text=goal_md_text, git_head=git_head, config=cfg,
        )
    _write_json(args.evidence_dir / "j11-stage-d-preflight.json", preflight)
    print(
        f"preflight captured: manifest_row_count={preflight['manifest_row_count']} "
        f"c1_ok={preflight['c1_date_set_boundary_check']['ok']} "
        f"identity_check_a_ok={preflight['identity_check_a']['ok']}",
        file=sys.stderr,
    )

    certified = jsd.load_stage_d_certified_baseline(
        args.stage_c_preflight_path, args.stage_c_mutation_accounting_path
    )
    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
    verdict = jsd.stage_d_preflight_verdict(gate)
    _write_json(args.evidence_dir / "j11-stage-d-preflight-gate.json", {"comparison": gate, "verdict": verdict})
    print(f"preflight comparison gate: all_invariants_hold={gate['all_invariants_hold']} verdict={verdict}", file=sys.stderr)
    if not gate["all_invariants_hold"]:
        failing = [k for k, v in gate["checks"].items() if not v]
        print(f"FAILING CHECKS: {failing}", file=sys.stderr)

    db_file_true_end = jsc.db_file_fingerprint(db_path)
    _write_json(args.evidence_dir / "j11-stage-d-db-file-true-end.json", db_file_true_end)
    mtime_unchanged = db_file_true_start.get("mtime") == db_file_true_end.get("mtime")
    print(f"whole-iteration zero-write proof: mtime_unchanged={mtime_unchanged}", file=sys.stderr)

    print(f"J-11 STAGE D PREFLIGHT PASSED: {'YES' if verdict['passed'] else 'NO'}", file=sys.stderr)
    print("J-11 STAGE D AUTHORIZED: NO", file=sys.stderr)
    return 0 if verdict["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
