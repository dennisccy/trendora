"""goal-market-compass iter-20 -- J-11 Stage E EXECUTION: the ONE owner-authorized live, global,
create-once forward-return hole repair over the retained + Stage-D-rebuilt `scanner_runs` population
(`docs/goal.md`'s "OWNER RULING -- J-11 Stage D through Stage G recovery execution AUTHORIZED", owner
2026-08-26, item 7 -- authorized unconditionally following a successful Stage D regeneration; iteration
19 already executed and independently-evaluator-verified Stage D).

Mirrors `run_j11_stage_d_execute.py`'s idiom exactly: NO database interaction of any kind, not even a
read, without `--confirm`; evidence is persisted at every checkpoint BEFORE the write so a mid-run crash
still leaves a forensic trail; the completion/outcome marker is written ONLY after full post-execution
verification completes (whichever of the two honest terminal states -- `STAGE E COMPLETE: YES` or
`STAGE E COMPLETE: NO` -- that verification proves). Sequence:

  1. Fresh, READ-ONLY preflight: boundary/guard re-check (`j11_stage_d_execute.
     recheck_maintenance_boundary_and_guard`, REUSED directly -- never reimplemented), the 11
     Stage-D-rebuilt runs present/unrestamped/zero-`ForwardReturn` check, a fresh `engine_identity`
     equality check against Stage D's frozen value, and a `next_session_manifests` unchanged check
     against the same certified baseline Stage D's own preflight used -- combined into ONE execution
     gate. STOPS here (zero writes of any kind) unless the gate's `proceed` is True.
  2. Pre-write captures for mutation accounting (full table sweep, the full `scanner_runs` fingerprint,
     `daily_prices`/`data_provider_runs`/`watchlist`/`maintenance_boundaries`/`next_session_manifests`
     snapshots, the retained-run incident-hole population count, and the `forward_returns` row count).
  3. THE per-run write loop (`j11_stage_e_execute.execute_stage_e_repair_loop`) over EVERY row currently
     in `scanner_runs`, ascending `asof_date` -- the ONE authorized write sequence, calling ONLY
     `forward_testing.backfill_run_forward_returns` (never `backfill_forward_returns`, the whole-database
     entry point -- see the module docstring).
  4. Live, read-only re-verification of the three named populations, directly against `forward_returns`.
  5. Post-execution mutation accounting, proving every out-of-scope table shows zero fingerprint change
     and the `forward_returns` delta reconciles exactly with the loop's own self-reported total.
  6. The final outcome, written UNCONDITIONALLY as the LAST evidence artifact -- Stage E's own contract
     defines TWO honest terminal states (`YES`/`NO`), and BOTH require full evidence preserved
     (docs/goal.md item 14) -- never a bare non-zero exit with no persisted outcome record.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_e_execute.py \\
        --confirm \\
        --evidence-dir runs/goal-market-compass-iter-20

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

from sqlalchemy import func  # noqa: E402
from sqlmodel import Session, select  # noqa: E402

from app.config import load_config  # noqa: E402
from app.db import get_engine, resolve_database_url  # noqa: E402
from app.engine import engine_identity  # noqa: E402
from app.engine import j11_maintenance  # noqa: E402
from app.engine import j11_schema_migration as migration  # noqa: E402
from app.engine import j11_stage_c as jsc  # noqa: E402
from app.engine import j11_stage_d_execute as jsde  # noqa: E402
from app.engine import j11_stage_e_execute as jsee  # noqa: E402
from app.models import DataProviderRun, ForwardReturn, MaintenanceBoundary, NextSessionManifest, Watchlist  # noqa: E402

DEFAULT_STAGE_D_FROZEN_IDENTITY_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-19" / "j11-stage-d-execute-frozen-identity.json"
)
DEFAULT_STAGE_D_REGENERATION_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-19" / "j11-stage-d-execute-regeneration.json"
)
DEFAULT_CERTIFIED_BASELINE_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-16" / "j11-stage-d-certified-baseline.json"
)

OUTPUT_FILENAMES = (
    "j11-stage-e-execute-db-file-true-start.json",
    "j11-stage-e-execute-boundary-recheck.json",
    "j11-stage-e-execute-runs-check.json",
    "j11-stage-e-execute-identity-comparison.json",
    "j11-stage-e-execute-manifest-check.json",
    "j11-stage-e-execute-preflight-gate.json",
    "j11-stage-e-execute-repair-loop.json",
    "j11-stage-e-execute-population-report.json",
    "j11-stage-e-execute-memory-check.json",
    "j11-stage-e-execute-mutation-accounting.json",
    "j11-stage-e-execute-outcome.json",
    "j11-stage-e-execute-db-file-true-end.json",
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
    """Mirrors the SAME collision guard `run_j11_stage_d_execute.py` uses -- a pure filesystem check, no
    database interaction."""
    return [name for name in filenames if (evidence_dir / name).exists()]


def _load_json(path: Path) -> Optional[dict]:
    """Loads one historical evidence artifact. Never raises on a missing/malformed file -- an absent
    cross-iteration artifact is recorded honestly as `None`, never fabricated and never a crash."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _load_stage_d_frozen_identity(path: Path) -> Optional[str]:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        return None
    value = payload.get("engine_identity")
    return value if isinstance(value, str) else None


def _load_expected_run_id_by_date(path: Path) -> dict[str, int]:
    """`{iso_date: run_id}` from Stage D's own recorded regeneration evidence
    (`per_date_results[*].date`/`.run_id`) -- never a fresh hardcoded literal. An absent/malformed file
    yields an empty mapping (the runs-check then honestly reports every date as `present: False` and the
    gate refuses to proceed -- fail closed, never fabricated)."""
    payload = _load_json(path)
    if not isinstance(payload, dict):
        return {}
    entries = payload.get("per_date_results")
    if not isinstance(entries, list):
        return {}
    out: dict[str, int] = {}
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("date"), str) and isinstance(entry.get("run_id"), int):
            out[entry["date"]] = entry["run_id"]
    return out


def _load_certified_manifest_dump(path: Path) -> list[dict]:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        return []
    dump = payload.get("manifest_dump")
    return dump if isinstance(dump, list) else []


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
    parser.add_argument("--stage-d-frozen-identity-path", type=Path, default=DEFAULT_STAGE_D_FROZEN_IDENTITY_PATH)
    parser.add_argument("--stage-d-regeneration-path", type=Path, default=DEFAULT_STAGE_D_REGENERATION_PATH)
    parser.add_argument("--certified-baseline-path", type=Path, default=DEFAULT_CERTIFIED_BASELINE_PATH)
    args = parser.parse_args()

    if not args.confirm:
        print(
            "refusing to run without --confirm (this is the ONE owner-authorized live Stage E write "
            "this iteration -- docs/goal.md J-11 step 11's Stage D-through-G OWNER RULING, item 7). No "
            "database interaction, not even a read, has occurred.",
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
    _write_json(evidence_dir / "j11-stage-e-execute-db-file-true-start.json", db_file_true_start)

    engine = get_engine()  # the SAME pooled writable engine the real backend uses.

    stage_d_frozen_identity = _load_stage_d_frozen_identity(args.stage_d_frozen_identity_path)
    expected_run_id_by_date = _load_expected_run_id_by_date(args.stage_d_regeneration_path)
    certified_manifest_dump = _load_certified_manifest_dump(args.certified_baseline_path)

    def _stop(reason: str, preflight_gate: dict, boundary_recheck: "dict | None" = None) -> int:
        outcome = jsee.stage_e_execution_outcome(
            preflight_gate=preflight_gate, repair_loop_result=None,
            population_verification=None, mutation_accounting=None,
        )
        _write_json(evidence_dir / "j11-stage-e-execute-outcome.json", outcome)
        db_file_true_end = jsc.db_file_fingerprint(db_path)
        _write_json(evidence_dir / "j11-stage-e-execute-db-file-true-end.json", db_file_true_end)
        print(f"STOP before any write: {reason}", file=sys.stderr)
        _print_terminal_lines(outcome, boundary_recheck=boundary_recheck)
        return 1

    # === Step 1: fresh, read-only preflight (boundary/guard + Stage-E-specific checks) ================
    with Session(engine) as session:
        boundary_recheck = jsde.recheck_maintenance_boundary_and_guard(session)
    _write_json(evidence_dir / "j11-stage-e-execute-boundary-recheck.json", boundary_recheck)
    print(
        f"boundary/guard recheck: ok={boundary_recheck['ok']} "
        f"all_dates_blocked={boundary_recheck['all_dates_blocked']}",
        file=sys.stderr,
    )

    with Session(engine) as session:
        runs_check = jsee.confirm_stage_d_runs_present_unrestamped(
            session,
            expected_run_id_by_date=expected_run_id_by_date,
            frozen_engine_identity=stage_d_frozen_identity or "",
        )
    _write_json(evidence_dir / "j11-stage-e-execute-runs-check.json", runs_check)
    print(f"Stage D runs check: ok={runs_check['ok']}", file=sys.stderr)

    fresh_identity = engine_identity.compute_engine_identity(cfg)
    identity_check = jsee.check_engine_identity_matches_stage_d(fresh_identity, stage_d_frozen_identity)
    _write_json(evidence_dir / "j11-stage-e-execute-identity-comparison.json", identity_check)
    print(f"engine_identity check: ok={identity_check['ok']} fresh={fresh_identity}", file=sys.stderr)

    manifest_check = jsee.confirm_manifests_unchanged(engine, certified_manifest_dump=certified_manifest_dump)
    _write_json(evidence_dir / "j11-stage-e-execute-manifest-check.json", manifest_check)
    print(f"manifest check: ok={manifest_check['ok']}", file=sys.stderr)

    preflight_gate = jsee.stage_e_preflight_gate_verdict(
        boundary_recheck=boundary_recheck, runs_check=runs_check,
        identity_check=identity_check, manifest_check=manifest_check,
    )
    _write_json(evidence_dir / "j11-stage-e-execute-preflight-gate.json", preflight_gate)
    print(f"preflight gate: proceed={preflight_gate['proceed']} reasons={preflight_gate['blocking_reasons']}", file=sys.stderr)

    if not preflight_gate["proceed"]:
        return _stop("preflight gate did not proceed", preflight_gate, boundary_recheck)

    incident_run_ids = sorted(expected_run_id_by_date.values())

    # === Step 2: pre-write captures ====================================================================
    with Session(engine) as session:
        pre_full_table_sweep = j11_maintenance.capture_full_table_sweep(session)
        pre_manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
        pre_all_scanner_run_fp = jsee.capture_all_scanner_run_fingerprint(session)
        pre_daily_prices = j11_maintenance.capture_pre_reset_inventory(session)["daily_prices"]
        pre_provider_runs = jsc.small_table_id_snapshot(session, DataProviderRun)
        pre_watchlist = jsc.small_table_id_snapshot(session, Watchlist)
        pre_maintenance_boundary_dump = migration.dump_table(engine, MaintenanceBoundary.__table__)
        pre_retained_hole_counts = jsee.capture_retained_incident_hole_counts(
            session, incident_run_ids=incident_run_ids,
        )
        pre_forward_returns_count = int(
            session.scalar(select(func.count()).select_from(ForwardReturn)) or 0
        )

    print(
        f"pre-write captures done: scanner_runs={pre_all_scanner_run_fp['row_count']} "
        f"forward_returns={pre_forward_returns_count} retained_hole_runs={pre_retained_hole_counts['run_count']}",
        file=sys.stderr,
    )

    # === Step 3: THE per-run write loop -- the ONE authorized write sequence ==========================
    with Session(engine) as session:
        repair_loop_result = jsee.execute_stage_e_repair_loop(session, cfg)
    _write_json(evidence_dir / "j11-stage-e-execute-repair-loop.json", repair_loop_result)
    print(
        f"repair loop: runs_processed={repair_loop_result['total_runs_processed']} "
        f"total_inserted={repair_loop_result['total_rows_inserted']} "
        f"incident={repair_loop_result['rows_inserted_on_rebuilt_incident_runs']} "
        f"retained={repair_loop_result['rows_inserted_on_retained_runs']}",
        file=sys.stderr,
    )

    vm_peak_kb = jsee.read_process_vm_peak_kb()
    memory_check = jsee.build_memory_check(vm_peak_kb=vm_peak_kb, memory_cap_mb=cfg.server.memory_cap_mb)
    _write_json(evidence_dir / "j11-stage-e-execute-memory-check.json", memory_check)
    print(f"memory check: vm_peak_mb={memory_check['vm_peak_mb']} within_cap={memory_check['within_cap']}", file=sys.stderr)

    # === Step 4: live, read-only re-verification of the three named populations =======================
    with Session(engine) as session:
        population_report = jsee.live_verify_three_populations(
            session, incident_run_ids=incident_run_ids,
            pre_retained_hole_counts_by_run=pre_retained_hole_counts["per_run_id_counts"],
        )
    _write_json(evidence_dir / "j11-stage-e-execute-population-report.json", population_report)
    print(f"population report: all_checks_pass={population_report['all_checks_pass']}", file=sys.stderr)

    # === Step 5: post-write captures + mutation accounting =============================================
    with Session(engine) as session:
        post_full_table_sweep = j11_maintenance.capture_full_table_sweep(session)
        post_manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
        post_all_scanner_run_fp = jsee.capture_all_scanner_run_fingerprint(session)
        post_daily_prices = j11_maintenance.capture_pre_reset_inventory(session)["daily_prices"]
        post_provider_runs = jsc.small_table_id_snapshot(session, DataProviderRun)
        post_watchlist = jsc.small_table_id_snapshot(session, Watchlist)
        post_maintenance_boundary_dump = migration.dump_table(engine, MaintenanceBoundary.__table__)
        post_forward_returns_count = int(
            session.scalar(select(func.count()).select_from(ForwardReturn)) or 0
        )

    db_file_true_end = jsc.db_file_fingerprint(db_path)
    _write_json(evidence_dir / "j11-stage-e-execute-db-file-true-end.json", db_file_true_end)

    mutation_accounting = jsee.build_stage_e_mutation_accounting(
        pre_full_table_sweep=pre_full_table_sweep, post_full_table_sweep=post_full_table_sweep,
        pre_manifest_dump=pre_manifest_dump, post_manifest_dump=post_manifest_dump,
        pre_all_scanner_run_fingerprint=pre_all_scanner_run_fp, post_all_scanner_run_fingerprint=post_all_scanner_run_fp,
        pre_daily_prices=pre_daily_prices, post_daily_prices=post_daily_prices,
        pre_provider_runs=pre_provider_runs, post_provider_runs=post_provider_runs,
        pre_watchlist=pre_watchlist, post_watchlist=post_watchlist,
        pre_maintenance_boundary_dump=pre_maintenance_boundary_dump, post_maintenance_boundary_dump=post_maintenance_boundary_dump,
        pre_forward_returns_count=pre_forward_returns_count, post_forward_returns_count=post_forward_returns_count,
        self_reported_total_inserted=repair_loop_result["total_rows_inserted"],
        db_file_true_start=db_file_true_start, db_file_true_end=db_file_true_end,
    )
    _write_json(evidence_dir / "j11-stage-e-execute-mutation-accounting.json", mutation_accounting)
    print(f"mutation accounting: all_checks_pass={mutation_accounting['all_checks_pass']}", file=sys.stderr)
    if not mutation_accounting["all_checks_pass"]:
        failing = [k for k, v in mutation_accounting["checks"].items() if not v]
        print(f"FAILING CHECKS: {failing}", file=sys.stderr)

    # === Final outcome -- written UNCONDITIONALLY, whichever of the two honest terminal states =========
    outcome = jsee.stage_e_execution_outcome(
        preflight_gate=preflight_gate, repair_loop_result=repair_loop_result,
        population_verification=population_report, mutation_accounting=mutation_accounting,
    )
    _write_json(evidence_dir / "j11-stage-e-execute-outcome.json", outcome)
    _print_terminal_lines(outcome, boundary_recheck=boundary_recheck)
    return 0 if outcome["executed"] else 1


def _print_terminal_lines(outcome: dict, *, boundary_recheck: "dict | None") -> None:
    executed = bool(outcome.get("executed"))
    boundary_active = boundary_recheck.get("boundary_active") if boundary_recheck else True
    guard_armed = boundary_recheck.get("all_dates_blocked") if boundary_recheck else True
    print("J-11 STAGE D EXECUTED: YES", file=sys.stderr)
    print(f"J-11 STAGE E COMPLETE: {'YES' if executed else 'NO'}", file=sys.stderr)
    print("J-11 STAGE F COMPLETE: NO", file=sys.stderr)
    print("J-11 STAGE G VERIFIED: NO", file=sys.stderr)
    print("J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE", file=sys.stderr)
    print(f"J-11 MAINTENANCE BOUNDARY: {'ACTIVE' if boundary_active else 'NOT ACTIVE'}", file=sys.stderr)
    print(f"J-11 LIVE PRE-BOOT GUARD: {'ARMED' if guard_armed else 'NOT ARMED'}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
