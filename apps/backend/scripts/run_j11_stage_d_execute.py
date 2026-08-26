"""goal-market-compass iter-19 -- J-11 Stage D EXECUTION: the ONE owner-authorized live canonical
regeneration of the eleven incident dates' `ScannerRun`/`ScannerResult`/`SectorScoreRow`/`ThemeScoreRow`
state (`docs/goal.md`'s "OWNER RULING -- J-11 Stage D through Stage G recovery execution AUTHORIZED",
owner 2026-08-26).

Mirrors `run_j11_stage_c_bounded_clear.py`'s idiom exactly: NO database interaction of any kind, not
even a read, without `--confirm`; evidence is persisted at every checkpoint BEFORE the destructive
step so a mid-run crash still leaves a forensic trail; the completion/outcome marker is written ONLY
after full post-execution verification completes (whichever of the two honest terminal states --
`STAGE D EXECUTED: YES` or `STAGE D EXECUTED: NO` -- that verification proves). Sequence, exactly as
the plan's ordering requires:

  1. Fresh, READ-ONLY preflight (`j11_stage_d.capture_stage_d_preflight` /
     `compare_stage_d_preflight_to_certified` / `stage_d_preflight_verdict`) + a fresh, READ-ONLY
     maintenance-boundary/live-guard re-check + a fresh, READ-ONLY AVB reclassification, combined into
     ONE execution gate (`j11_stage_d_execute.stage_d_execution_gate_verdict`). STOPS here (zero
     writes of any kind) unless the gate's `proceed` is True.
  2. Freeze ONE fresh execution identity (`freeze_fresh_stage_d_execution_identity`), immediately
     before the first write; an honest comparison against the iteration-10/14/16-17-18 historical
     identity values already on disk; Check (A) `check_identity_before_first_write` as a defensive
     sanity check the plan recommends. STOPS here (still zero regeneration writes) on any failure.
  3. THE per-date write loop (`execute_stage_d_regeneration`) over every date in
     `app.engine.j11_maintenance.INCIDENT_DATES`, in ascending order -- the ONE authorized write
     sequence, calling `scanner.run_scan` directly. Stops the WHOLE attempt at the first failing
     precondition/check.
  4. Post-execution mutation accounting (`build_stage_d_mutation_accounting`), proving every table
     Stage D is forbidden to touch shows zero fingerprint change, and every table it IS allowed to
     touch changed in exactly the expected way.
  5. The final outcome (`stage_d_execution_outcome`) is written UNCONDITIONALLY as the LAST evidence
     artifact -- unlike `run_j11_stage_c_bounded_clear.py` (which writes a completion marker only on a
     PASS), Stage D's own contract defines TWO honest terminal states (`YES`/`NO`), and BOTH require
     full evidence preserved (docs/goal.md item 14) -- never a bare non-zero exit with no persisted
     outcome record.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_d_execute.py \\
        --confirm \\
        --evidence-dir runs/goal-market-compass-iter-19

Without `--confirm`, the script performs NO database interaction at all (not even a read) and exits
non-zero. `--evidence-dir` is REQUIRED and has no implicit default (mirrors every other J-11
evidence-writing script -- an omitted flag must never fall back to overwriting a committed evidence
directory).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# scripts/ -> backend -> apps -> repo root
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlmodel import Session  # noqa: E402

from app.config import load_config  # noqa: E402
from app.db import get_engine, resolve_database_url  # noqa: E402
from app.engine import engine_identity  # noqa: E402
from app.engine import j11_avb_correction as corr  # noqa: E402
from app.engine import j11_avb_diagnostic as diag  # noqa: E402
from app.engine import j11_maintenance  # noqa: E402
from app.engine import j11_schema_migration as migration  # noqa: E402
from app.engine import j11_stage_c as jsc  # noqa: E402
from app.engine import j11_stage_d as jsd  # noqa: E402
from app.engine import j11_stage_d_execute as jsde  # noqa: E402
from app.engine.j11_maintenance import INCIDENT_DATES  # noqa: E402
from app.models import DataProviderRun, MaintenanceBoundary, NextSessionManifest, Watchlist  # noqa: E402

DEFAULT_CERTIFIED_BASELINE_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-16" / "j11-stage-d-certified-baseline.json"
)
DEFAULT_ITERATION_10_IDENTITY_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-10" / "j11-frozen-identity.json"
)
DEFAULT_ITERATION_14_IDENTITY_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-14" / "j11-stage-d-attempt-identity.json"
)
# iteration 16, 17, and (by citation) 18 all carry the SAME readiness-time engine_identity value
# (verified: nothing touched compass.py/session_delta.py/engine_identity.py or the compass.selection/
# delta/manifest config keys across any of them) -- iteration 17's own preflight capture is the LATEST
# re-derivation, so it is the one representative file loaded here for the "16/17/18" comparison label.
DEFAULT_ITERATION_16_17_18_PREFLIGHT_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-17" / "j11-stage-d-preflight.json"
)

OUTPUT_FILENAMES = (
    "j11-stage-d-execute-db-file-true-start.json",
    "j11-stage-d-execute-preflight.json",
    "j11-stage-d-execute-preflight-gate.json",
    "j11-stage-d-execute-boundary-recheck.json",
    "j11-stage-d-execute-avb-reclassification.json",
    "j11-stage-d-execute-gate-verdict.json",
    "j11-stage-d-execute-frozen-identity.json",
    "j11-stage-d-execute-historical-identity-comparison.json",
    "j11-stage-d-execute-check-a.json",
    "j11-stage-d-execute-regeneration.json",
    "j11-stage-d-execute-mutation-accounting.json",
    "j11-stage-d-execute-outcome.json",
    "j11-stage-d-execute-db-file-true-end.json",
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


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
    print(f"wrote {path}", file=sys.stderr)


def _refuse_if_evidence_files_exist(evidence_dir: Path, filenames: tuple) -> list[str]:
    """Mirrors the SAME collision guard `run_j11_iter17_stage_d_readiness.py`/`...iter18_...py` added
    after a mistyped `--evidence-dir` once silently overwrote committed evidence. Pure filesystem
    check, no database interaction."""
    return [name for name in filenames if (evidence_dir / name).exists()]


def _load_historical_identity(path: Path, *, json_pointer: tuple[str, ...]) -> Optional[str]:
    """Loads one historical identity artifact and walks `json_pointer` to the `engine_identity` string.
    Never raises on a missing file or missing key -- an absent historical artifact is recorded honestly
    as `None`, never fabricated and never a crash."""
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    node = payload
    for key in json_pointer:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node if isinstance(node, str) else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--evidence-dir", type=Path, default=None,
        help="required -- no default on purpose (mirrors every other J-11 evidence-writing script).",
    )
    parser.add_argument(
        "--confirm", action="store_true",
        help="required -- without it, the script touches the database not at all and exits non-zero.",
    )
    parser.add_argument("--certified-baseline-path", type=Path, default=DEFAULT_CERTIFIED_BASELINE_PATH)
    parser.add_argument("--provider-fetch-evidence-path", type=Path, default=corr.DEFAULT_PROVIDER_FETCH_EVIDENCE_PATH)
    parser.add_argument("--j10-evidence-path", type=Path, default=diag.DEFAULT_J10_EVIDENCE_PATH)
    parser.add_argument("--iteration-10-identity-path", type=Path, default=DEFAULT_ITERATION_10_IDENTITY_PATH)
    parser.add_argument("--iteration-14-identity-path", type=Path, default=DEFAULT_ITERATION_14_IDENTITY_PATH)
    parser.add_argument(
        "--iteration-16-17-18-preflight-path", type=Path, default=DEFAULT_ITERATION_16_17_18_PREFLIGHT_PATH,
    )
    args = parser.parse_args()

    if not args.confirm:
        print(
            "refusing to run without --confirm (this is the ONE owner-authorized live Stage D write "
            "this iteration -- docs/goal.md J-11 step 11's Stage D-through-G OWNER RULING). No database "
            "interaction, not even a read, has occurred.",
            file=sys.stderr,
        )
        return 2

    if args.evidence_dir is None:
        print(
            "refusing to run without an explicit --evidence-dir. No database interaction, not even a "
            "read, has occurred, and nothing has been written.",
            file=sys.stderr,
        )
        return 2

    evidence_dir: Path = args.evidence_dir
    colliding = _refuse_if_evidence_files_exist(evidence_dir, OUTPUT_FILENAMES)
    if colliding:
        print(
            f"refusing to run: --evidence-dir {evidence_dir} already contains {colliding} -- this looks "
            "like a re-run pointed at an already-populated evidence folder rather than a fresh one. No "
            "database interaction, not even a read, has occurred, and no existing file has been touched.",
            file=sys.stderr,
        )
        return 2

    cfg = load_config()
    resolved_url = resolve_database_url(cfg.database.url)
    db_path = _db_file_path(resolved_url)
    print(f"database: {resolved_url}", file=sys.stderr)

    # --- TRUE process start: the db file + WAL sidecar fingerprint, before anything else touches it ---
    db_file_true_start = jsc.db_file_fingerprint(db_path)
    _write_json(evidence_dir / "j11-stage-d-execute-db-file-true-start.json", db_file_true_start)

    engine = get_engine()  # the SAME pooled writable engine the real backend uses.
    goal_md_text = jsc.read_goal_md_text()
    git_head = jsc.read_git_head()

    def _stop(reason: str, execution_gate: dict, boundary_recheck: "dict | None" = None) -> int:
        outcome = jsde.stage_d_execution_outcome(
            execution_gate=execution_gate, regeneration_result=None, mutation_accounting=None,
        )
        _write_json(evidence_dir / "j11-stage-d-execute-outcome.json", outcome)
        db_file_true_end = jsc.db_file_fingerprint(db_path)
        _write_json(evidence_dir / "j11-stage-d-execute-db-file-true-end.json", db_file_true_end)
        print(f"STOP before any write: {reason}", file=sys.stderr)
        # `boundary_recheck` is threaded through when the caller already computed a REAL one (both stop
        # sites below do) so the printed MAINTENANCE BOUNDARY/LIVE PRE-BOOT GUARD lines reflect the
        # actual fresh re-verification -- never a blind assumed-True default when real evidence exists.
        _print_terminal_lines(outcome, boundary_recheck=boundary_recheck)
        return 1

    # === Step 1: fresh, read-only preflight + boundary/guard recheck + AVB reclassification =========
    with Session(engine) as session:
        preflight = jsd.capture_stage_d_preflight(
            session, engine, db_path, goal_md_text=goal_md_text, git_head=git_head, config=cfg,
        )
    _write_json(evidence_dir / "j11-stage-d-execute-preflight.json", preflight)
    print(
        f"fresh preflight captured: manifest_row_count={preflight['manifest_row_count']} "
        f"c1_ok={preflight['c1_date_set_boundary_check']['ok']}",
        file=sys.stderr,
    )

    certified = json.loads(args.certified_baseline_path.read_text())
    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
    preflight_verdict = jsd.stage_d_preflight_verdict(gate)
    _write_json(evidence_dir / "j11-stage-d-execute-preflight-gate.json", {"comparison": gate, "verdict": preflight_verdict})
    print(f"preflight comparison gate: all_invariants_hold={gate['all_invariants_hold']}", file=sys.stderr)

    with Session(engine) as session:
        boundary_recheck = jsde.recheck_maintenance_boundary_and_guard(session, INCIDENT_DATES)
    _write_json(evidence_dir / "j11-stage-d-execute-boundary-recheck.json", boundary_recheck)
    print(
        f"boundary/guard recheck: ok={boundary_recheck['ok']} "
        f"all_dates_blocked={boundary_recheck['all_dates_blocked']}",
        file=sys.stderr,
    )

    with Session(engine) as session:
        avb_result = jsde.run_fresh_avb_reclassification(
            session, cfg,
            provider_fetch_evidence_path=args.provider_fetch_evidence_path,
            j10_evidence_path=args.j10_evidence_path,
        )
    _write_json(evidence_dir / "j11-stage-d-execute-avb-reclassification.json", avb_result)
    avb_classification = avb_result["classification"]["classification"]
    print(f"fresh AVB reclassification: {avb_classification}", file=sys.stderr)

    execution_gate = jsde.stage_d_execution_gate_verdict(
        preflight_verdict=preflight_verdict, avb_classification=avb_classification, boundary_recheck=boundary_recheck,
    )
    _write_json(evidence_dir / "j11-stage-d-execute-gate-verdict.json", execution_gate)
    print(f"execution gate: proceed={execution_gate['proceed']} reasons={execution_gate['blocking_reasons']}", file=sys.stderr)

    if not execution_gate["proceed"]:
        return _stop("execution gate did not proceed", execution_gate, boundary_recheck)

    # === Step 2: freeze ONE fresh execution identity + honest historical comparison + Check (A) ======
    with Session(engine) as session:
        frozen_identity = jsde.freeze_fresh_stage_d_execution_identity(
            session, cfg, git_head=git_head, goal_md_text=goal_md_text,
        )
    _write_json(evidence_dir / "j11-stage-d-execute-frozen-identity.json", frozen_identity)
    print(f"frozen execution identity: {frozen_identity['engine_identity']}", file=sys.stderr)

    historical = {
        "iteration_10": _load_historical_identity(args.iteration_10_identity_path, json_pointer=("engine_identity",)),
        "iteration_14": _load_historical_identity(args.iteration_14_identity_path, json_pointer=("engine_identity",)),
        "iteration_16_17_18_readiness": _load_historical_identity(
            args.iteration_16_17_18_preflight_path, json_pointer=("attempt_identity", "engine_identity"),
        ),
    }
    identity_comparison = jsde.compare_identity_against_historical(frozen_identity["engine_identity"], historical)
    _write_json(evidence_dir / "j11-stage-d-execute-historical-identity-comparison.json", identity_comparison)
    print(f"historical identity comparison: {identity_comparison['comparisons']}", file=sys.stderr)

    current_identity_for_check_a = engine_identity.compute_engine_identity(cfg)
    check_a = jsd.check_identity_before_first_write(frozen_identity, current_identity_for_check_a)
    _write_json(evidence_dir / "j11-stage-d-execute-check-a.json", check_a)
    if not check_a["ok"]:
        return _stop(
            "Check (A) failed immediately after freezing -- refusing to proceed to any write",
            execution_gate, boundary_recheck,
        )

    # === Step 3: pre-write mutation-accounting captures, THEN the one authorized write sequence ======
    with Session(engine) as session:
        pre_full_table_sweep = j11_maintenance.capture_full_table_sweep(session)
        pre_manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
        pre_legacy_null_fp = jsde.capture_legacy_and_null_scanner_run_fingerprint(session)
        pre_daily_prices = j11_maintenance.capture_pre_reset_inventory(session)["daily_prices"]
        pre_provider_runs = jsc.small_table_id_snapshot(session, DataProviderRun)
        pre_watchlist = jsc.small_table_id_snapshot(session, Watchlist)
        pre_maintenance_boundary_dump = migration.dump_table(engine, MaintenanceBoundary.__table__)

    with Session(engine) as session:
        regen = jsde.execute_stage_d_regeneration(session, INCIDENT_DATES, frozen_identity, cfg)
    _write_json(evidence_dir / "j11-stage-d-execute-regeneration.json", regen)
    print(
        f"regeneration: completed={regen['completed']} stopped_at_date={regen['stopped_at_date']} "
        f"new_run_ids={regen['new_run_ids']}",
        file=sys.stderr,
    )

    # === Step 4: post-write captures + mutation accounting ============================================
    with Session(engine) as session:
        post_full_table_sweep = j11_maintenance.capture_full_table_sweep(session)
        post_manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
        post_legacy_null_fp = jsde.capture_legacy_and_null_scanner_run_fingerprint(session)
        post_daily_prices = j11_maintenance.capture_pre_reset_inventory(session)["daily_prices"]
        post_provider_runs = jsc.small_table_id_snapshot(session, DataProviderRun)
        post_watchlist = jsc.small_table_id_snapshot(session, Watchlist)
        post_maintenance_boundary_dump = migration.dump_table(engine, MaintenanceBoundary.__table__)

    db_file_true_end = jsc.db_file_fingerprint(db_path)
    _write_json(evidence_dir / "j11-stage-d-execute-db-file-true-end.json", db_file_true_end)

    mutation_accounting = jsde.build_stage_d_mutation_accounting(
        pre_full_table_sweep=pre_full_table_sweep, post_full_table_sweep=post_full_table_sweep,
        pre_manifest_dump=pre_manifest_dump, post_manifest_dump=post_manifest_dump,
        pre_legacy_null_fingerprint=pre_legacy_null_fp, post_legacy_null_fingerprint=post_legacy_null_fp,
        pre_daily_prices=pre_daily_prices, post_daily_prices=post_daily_prices,
        pre_provider_runs=pre_provider_runs, post_provider_runs=post_provider_runs,
        pre_watchlist=pre_watchlist, post_watchlist=post_watchlist,
        pre_maintenance_boundary_dump=pre_maintenance_boundary_dump, post_maintenance_boundary_dump=post_maintenance_boundary_dump,
        db_file_true_start=db_file_true_start, db_file_true_end=db_file_true_end,
    )
    _write_json(evidence_dir / "j11-stage-d-execute-mutation-accounting.json", mutation_accounting)
    print(f"mutation accounting: all_checks_pass={mutation_accounting['all_checks_pass']}", file=sys.stderr)
    if not mutation_accounting["all_checks_pass"]:
        failing = [k for k, v in mutation_accounting["checks"].items() if not v]
        print(f"FAILING CHECKS: {failing}", file=sys.stderr)

    # === Final outcome -- written UNCONDITIONALLY, whichever of the two honest terminal states =========
    outcome = jsde.stage_d_execution_outcome(
        execution_gate=execution_gate, regeneration_result=regen, mutation_accounting=mutation_accounting,
    )
    _write_json(evidence_dir / "j11-stage-d-execute-outcome.json", outcome)
    _print_terminal_lines(outcome, boundary_recheck=boundary_recheck)
    return 0 if outcome["executed"] else 1


def _print_terminal_lines(outcome: dict, *, boundary_recheck: "dict | None") -> None:
    executed = bool(outcome.get("executed"))
    boundary_active = boundary_recheck.get("boundary_active") if boundary_recheck else True
    guard_armed = boundary_recheck.get("all_dates_blocked") if boundary_recheck else True
    print("J-11 STAGE D AUTHORIZED: YES", file=sys.stderr)
    print(f"J-11 STAGE D EXECUTED: {'YES' if executed else 'NO'}", file=sys.stderr)
    print("J-11 STAGE E COMPLETE: NO", file=sys.stderr)
    print("J-11 STAGE F COMPLETE: NO", file=sys.stderr)
    print("J-11 STAGE G VERIFIED: NO", file=sys.stderr)
    print("J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE", file=sys.stderr)
    print(f"J-11 MAINTENANCE BOUNDARY: {'ACTIVE' if boundary_active else 'NOT ACTIVE'}", file=sys.stderr)
    print(f"J-11 LIVE PRE-BOOT GUARD: {'ARMED' if guard_armed else 'NOT ARMED'}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
