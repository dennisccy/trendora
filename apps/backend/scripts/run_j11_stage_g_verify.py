"""goal-market-compass iter-22 -- J-11 Stage G FULL VERIFICATION: the terminal, owner-authorized
acceptance gate proving the whole D->G recovery arc holds against the live database
(`docs/goal.md`'s "OWNER RULING -- J-11 Stage D through Stage G recovery execution AUTHORIZED", owner
2026-08-26, item 9 -- authorized unconditionally following a successful Stage F; iteration 21 already
executed and independently-evaluator-verified Stage F).

Mirrors `run_j11_stage_f_execute.py`'s idiom exactly: NO database interaction of any kind, not even a
read, without `--confirm`; every checkpoint is persisted BEFORE the next step runs so a mid-run crash
still leaves a forensic trail; the outcome/terminal-lines marker is written LAST, UNCONDITIONALLY,
whichever of Stage G's two honest terminal states verification proves. Sequence:

  1. Fresh, READ-ONLY preflight -- boundary/guard re-check (`j11_stage_d_execute.
     recheck_maintenance_boundary_and_guard`, REUSED directly), the 11 incident runs' presence + identity
     + EXACT recorded ForwardReturn count (`j11_stage_f_execute.confirm_stage_e_complete_and_unrestamped`,
     REUSED directly -- see `j11_stage_g_verify`'s module docstring for why this function, not
     `j11_stage_e_execute.confirm_stage_d_runs_present_unrestamped`, is the correct reuse here), a fresh
     `engine_identity` equality check against Stage D's frozen value (`j11_stage_e_execute.
     check_engine_identity_matches_stage_d`, REUSED directly), and a `next_session_manifests` unchanged
     check against the certified iter-16 baseline (`j11_stage_e_execute.confirm_manifests_unchanged`,
     REUSED directly) -- combined into ONE preflight gate. STOPS here (zero further checks, zero writes)
     unless the gate's `proceed` is True.
  2. Every acceptance-category check, read-only: raw inputs, snapshot scope (ids 3148-3158 + Stage D's own
     execution evidence -- never `engine_identity` alone), forward-return populations (a)/(b)/(c) (population
     (b) = 0 scored as CORRECT, not a gap), manifests (direct SQL only -- never `get_or_create_manifest`),
     audit/evidence/user-state, cache dispositions, the `membership_timeline_cache` B2 per-date
     recompute-and-compare, the 18 named traps, a fresh write-path call-site re-enumeration + classification,
     an evidence-reinterpretation static check, and operational isolation.
  3. Aggregate verdict (`stage_g_verdict`) -- no boolean permitted to pass by construction.
  4. The ONE conditional corrective write this iteration may perform outside `finalize_stage_g` itself: if
     the membership-timeline B2 check found a stale row, delete it (Stage F's own pre-approved fallback) --
     this happens regardless of the overall verdict (a stale cache row is repaired either way, per the phase
     spec's own wording: "the membership-timeline delete already covered above if that specific check is
     what failed" is explicitly still authorized on a FAIL attempt).
  5. `finalize_stage_g` -- the ONE further conditional write: on a full PASS, deactivate (never delete) the
     `j11-incident-recovery` boundary; on any FAIL, zero further writes, boundary stays `active=1`.
  6. Post-write, read-only cross-iteration mutation accounting -- reconciles every changed table's delta
     since iteration 18's pre-Stage-D baseline sweep to exactly Stage D + Stage E + Stage F + this
     iteration's own two possible conditional writes. Written LAST, alongside the final terminal-outcome
     block, unconditionally.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_g_verify.py \\
        --confirm \\
        --evidence-dir runs/goal-market-compass-iter-22

Without `--confirm`, the script performs NO database interaction at all (not even a read) and exits
non-zero. `--evidence-dir` is REQUIRED and has no implicit default (mirrors every other J-11
evidence-writing script -- an omitted flag must never fall back to overwriting a committed evidence
directory).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

# scripts/ -> backend -> apps -> repo root
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import func as sa_func  # noqa: E402
from sqlmodel import Session, select  # noqa: E402

from app.config import load_config  # noqa: E402
from app.db import get_engine, resolve_database_url  # noqa: E402
from app.engine import engine_identity  # noqa: E402
from app.engine import j11_maintenance  # noqa: E402
from app.engine import j11_schema_migration as migration  # noqa: E402
from app.engine import j11_stage_c as jsc  # noqa: E402
from app.engine import j11_stage_d_execute as jsde  # noqa: E402
from app.engine import j11_stage_e_execute as jsee  # noqa: E402
from app.engine import j11_stage_f_execute as jsfe  # noqa: E402
from app.engine import j11_stage_g_verify as jsgv  # noqa: E402
from app.models import MaintenanceBoundary, MembershipTimelineCache  # noqa: E402

DEFAULT_STAGE_D_FROZEN_IDENTITY_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-19" / "j11-stage-d-execute-frozen-identity.json"
)
DEFAULT_STAGE_D_REGENERATION_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-19" / "j11-stage-d-execute-regeneration.json"
)
DEFAULT_STAGE_E_POPULATION_REPORT_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-20" / "j11-stage-e-execute-population-report.json"
)
DEFAULT_STAGE_F_DISPOSITIONS_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-21" / "j11-stage-f-execute-dispositions.json"
)
DEFAULT_CERTIFIED_BASELINE_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-16" / "j11-stage-d-certified-baseline.json"
)
DEFAULT_PRE_RESET_INVENTORY_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-10" / "j11-pre-reset-inventory.json"
)
DEFAULT_ITER18_PRE_STAGE_D_SWEEP_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-18" / "j11-iter18-full-table-sweep-after.json"
)

TESTS_DIR = BACKEND_DIR / "tests"
APP_DIR = BACKEND_DIR / "app"
THIS_MODULE_PATH = APP_DIR / "engine" / "j11_stage_g_verify.py"
THIS_SCRIPT_PATH = Path(__file__).resolve()

OUTPUT_FILENAMES = (
    "j11-stage-g-verify-db-file-true-start.json",
    "j11-stage-g-verify-boundary-recheck.json",
    "j11-stage-g-verify-stage-d-e-check.json",
    "j11-stage-g-verify-identity-comparison.json",
    "j11-stage-g-verify-manifest-preflight-check.json",
    "j11-stage-g-verify-preflight-gate.json",
    "j11-stage-g-verify-raw-inputs.json",
    "j11-stage-g-verify-snapshot-scope.json",
    "j11-stage-g-verify-forward-returns.json",
    "j11-stage-g-verify-manifests.json",
    "j11-stage-g-verify-audit-evidence-and-user-state.json",
    "j11-stage-g-verify-cache-dispositions.json",
    "j11-stage-g-verify-membership-timeline-check.json",
    "j11-stage-g-verify-membership-timeline-delete-action.json",
    "j11-stage-g-verify-named-traps.json",
    "j11-stage-g-verify-write-path-sites.json",
    "j11-stage-g-verify-write-path-classification.json",
    "j11-stage-g-verify-evidence-reinterpretation-check.json",
    "j11-stage-g-verify-network-import-check.json",
    "j11-stage-g-verify-operational-isolation.json",
    "j11-stage-g-verify-verdict.json",
    "j11-stage-g-verify-finalize.json",
    "j11-stage-g-verify-memory-check.json",
    "j11-stage-g-verify-mutation-accounting.json",
    "j11-stage-g-verify-outcome.json",
    "j11-stage-g-verify-db-file-true-end.json",
)


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
    print(f"wrote {path}", file=sys.stderr)


def _refuse_if_evidence_files_exist(evidence_dir: Path, filenames: tuple) -> list[str]:
    return [name for name in filenames if (evidence_dir / name).exists()]


def _load_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _db_file_path(database_url: str) -> "Path | None":
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None
    raw = database_url[len(prefix):]
    if not raw or raw == ":memory:":
        return None
    path = Path(raw)
    return path if path.is_absolute() else (REPO_ROOT / raw)


def _load_stage_d_frozen_identity(path: Path) -> Optional[str]:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        return None
    value = payload.get("engine_identity")
    return value if isinstance(value, str) else None


def _load_expected_run_id_by_date(path: Path) -> dict[str, int]:
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


def _load_expected_forward_return_count_by_run_id(path: Path) -> dict[str, int]:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        return {}
    population_a = payload.get("population_a_rebuilt_incident_runs")
    if not isinstance(population_a, dict):
        return {}
    out: dict[str, int] = {}
    for run_id_str, entry in population_a.items():
        if isinstance(entry, dict) and isinstance(entry.get("post"), int):
            out[run_id_str] = entry["post"]
    return out


def _load_certified_manifest_dump(path: Path) -> list[dict]:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        return []
    dump = payload.get("manifest_dump")
    return dump if isinstance(dump, list) else []


def _load_stage_f_new_dates(path: Path) -> list[str]:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        return []
    mt = payload.get("membership_timeline_cache")
    if not isinstance(mt, dict):
        return []
    reuse_eval = mt.get("membership_reuse_evaluation")
    if not isinstance(reuse_eval, dict):
        return []
    new_dates = reuse_eval.get("new_dates")
    return new_dates if isinstance(new_dates, list) else []


def _print_terminal_lines(terminal_lines: str) -> None:
    print(terminal_lines, file=sys.stderr)


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
    parser.add_argument("--stage-e-population-report-path", type=Path, default=DEFAULT_STAGE_E_POPULATION_REPORT_PATH)
    parser.add_argument("--stage-f-dispositions-path", type=Path, default=DEFAULT_STAGE_F_DISPOSITIONS_PATH)
    parser.add_argument("--certified-baseline-path", type=Path, default=DEFAULT_CERTIFIED_BASELINE_PATH)
    parser.add_argument("--pre-reset-inventory-path", type=Path, default=DEFAULT_PRE_RESET_INVENTORY_PATH)
    parser.add_argument("--iter18-pre-stage-d-sweep-path", type=Path, default=DEFAULT_ITER18_PRE_STAGE_D_SWEEP_PATH)
    args = parser.parse_args()

    if not args.confirm:
        print(
            "refusing to run without --confirm (this is J-11's terminal Stage G verification -- "
            "docs/goal.md's Stage D-through-G OWNER RULING, item 9). No database interaction, not even a "
            "read, has occurred.",
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
    _write_json(evidence_dir / "j11-stage-g-verify-db-file-true-start.json", db_file_true_start)

    engine = get_engine()  # the SAME pooled writable engine the real backend uses.

    stage_d_frozen_identity = _load_stage_d_frozen_identity(args.stage_d_frozen_identity_path)
    expected_run_id_by_date = _load_expected_run_id_by_date(args.stage_d_regeneration_path)
    expected_forward_return_count_by_run_id = _load_expected_forward_return_count_by_run_id(args.stage_e_population_report_path)
    stage_e_population_report = _load_json(args.stage_e_population_report_path) or {}
    stage_f_dispositions = _load_json(args.stage_f_dispositions_path) or {}
    stage_f_new_dates = _load_stage_f_new_dates(args.stage_f_dispositions_path)
    certified_baseline = _load_json(args.certified_baseline_path) or {}
    certified_manifest_dump = _load_certified_manifest_dump(args.certified_baseline_path)
    certified_pre_reset_inventory = _load_json(args.pre_reset_inventory_path) or {}
    iter18_pre_stage_d_sweep_wrapper = _load_json(args.iter18_pre_stage_d_sweep_path) or {}
    iter18_pre_stage_d_sweep = iter18_pre_stage_d_sweep_wrapper.get("sweep") or {}
    incident_run_ids = sorted(expected_run_id_by_date.values())

    missing_inputs = []
    if stage_d_frozen_identity is None:
        missing_inputs.append("stage_d_frozen_identity")
    if not expected_run_id_by_date:
        missing_inputs.append("expected_run_id_by_date")
    if not expected_forward_return_count_by_run_id:
        missing_inputs.append("expected_forward_return_count_by_run_id")
    if not certified_manifest_dump:
        missing_inputs.append("certified_manifest_dump")
    if not certified_pre_reset_inventory:
        missing_inputs.append("certified_pre_reset_inventory")
    if not iter18_pre_stage_d_sweep:
        missing_inputs.append("iter18_pre_stage_d_sweep")

    def _stop(reason: str, preflight_gate: dict) -> int:
        finalize = {
            "generated_at": None, "outcome": "NOT_REPAIRED_ATTEMPT_INCOMPLETE",
            "boundary_deactivated": False,
            "terminal_lines": (
                "J-11 STAGE D EXECUTED: YES\n"
                "J-11 STAGE E COMPLETE: YES\n"
                "J-11 STAGE F COMPLETE: YES\n"
                "J-11 STAGE G VERIFIED: NO\n"
                "J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE\n"
                "J-11 MAINTENANCE BOUNDARY: ACTIVE"
            ),
        }
        _write_json(evidence_dir / "j11-stage-g-verify-finalize.json", finalize)
        outcome = {"generated_at": None, "reason": reason, "preflight_gate": preflight_gate}
        _write_json(evidence_dir / "j11-stage-g-verify-outcome.json", outcome)
        db_file_true_end = jsc.db_file_fingerprint(db_path)
        _write_json(evidence_dir / "j11-stage-g-verify-db-file-true-end.json", db_file_true_end)
        print(f"STOP before any write: {reason}", file=sys.stderr)
        _print_terminal_lines(finalize["terminal_lines"])
        return 1

    if missing_inputs:
        return _stop(f"missing/unloadable required historical evidence inputs: {missing_inputs}", {"proceed": False})

    # === Step 1: fresh, read-only preflight ============================================================
    with Session(engine) as session:
        boundary_recheck = jsde.recheck_maintenance_boundary_and_guard(session)
    _write_json(evidence_dir / "j11-stage-g-verify-boundary-recheck.json", boundary_recheck)
    print(f"boundary/guard recheck: ok={boundary_recheck['ok']}", file=sys.stderr)

    with Session(engine) as session:
        stage_d_e_check = jsfe.confirm_stage_e_complete_and_unrestamped(
            session,
            expected_run_id_by_date=expected_run_id_by_date,
            expected_forward_return_count_by_run_id=expected_forward_return_count_by_run_id,
            frozen_engine_identity=stage_d_frozen_identity or "",
        )
    _write_json(evidence_dir / "j11-stage-g-verify-stage-d-e-check.json", stage_d_e_check)
    print(f"Stage D/E end-state check: ok={stage_d_e_check['ok']}", file=sys.stderr)

    fresh_identity = engine_identity.compute_engine_identity(cfg)
    identity_check = jsee.check_engine_identity_matches_stage_d(fresh_identity, stage_d_frozen_identity)
    _write_json(evidence_dir / "j11-stage-g-verify-identity-comparison.json", identity_check)
    print(f"engine_identity check: ok={identity_check['ok']} fresh={fresh_identity}", file=sys.stderr)

    manifest_preflight_check = jsee.confirm_manifests_unchanged(engine, certified_manifest_dump=certified_manifest_dump)
    _write_json(evidence_dir / "j11-stage-g-verify-manifest-preflight-check.json", manifest_preflight_check)
    print(f"manifest preflight check: ok={manifest_preflight_check['ok']}", file=sys.stderr)

    preflight_gate = jsgv.stage_g_preflight_gate_verdict(
        boundary_recheck=boundary_recheck, stage_d_e_check=stage_d_e_check,
        identity_check=identity_check, manifest_check=manifest_preflight_check,
    )
    _write_json(evidence_dir / "j11-stage-g-verify-preflight-gate.json", preflight_gate)
    print(f"preflight gate: proceed={preflight_gate['proceed']} reasons={preflight_gate['blocking_reasons']}", file=sys.stderr)

    if not preflight_gate["proceed"]:
        return _stop("preflight gate did not proceed", preflight_gate)

    # === Step 2: every acceptance-category check, read-only ============================================
    with Session(engine) as session:
        raw_inputs = jsgv.verify_raw_inputs(
            session,
            certified_daily_prices_fingerprint=certified_baseline.get("daily_prices_fingerprint", ""),
            module_and_script_paths=(THIS_MODULE_PATH, THIS_SCRIPT_PATH),
        )
    _write_json(evidence_dir / "j11-stage-g-verify-raw-inputs.json", raw_inputs)
    print(f"raw inputs: ok={raw_inputs['ok']}", file=sys.stderr)

    with Session(engine) as session:
        live_full_table_sweep_pre = j11_maintenance.capture_full_table_sweep(session)
        snapshot_scope = jsgv.verify_snapshot_scope(
            session, expected_run_id_by_date=expected_run_id_by_date,
            iter18_pre_stage_d_sweep=iter18_pre_stage_d_sweep, live_full_table_sweep=live_full_table_sweep_pre,
        )
    _write_json(evidence_dir / "j11-stage-g-verify-snapshot-scope.json", snapshot_scope)
    print(f"snapshot scope: ok={snapshot_scope['ok']}", file=sys.stderr)

    with Session(engine) as session:
        forward_returns = jsgv.verify_forward_returns(
            session, incident_run_ids=incident_run_ids, stage_e_population_report=stage_e_population_report,
        )
    _write_json(evidence_dir / "j11-stage-g-verify-forward-returns.json", forward_returns)
    print(f"forward returns: ok={forward_returns['ok']} population_b_delta={forward_returns['population_b_delta_from_pre_stage_e_baseline']}", file=sys.stderr)

    with Session(engine) as session:
        manifests = jsgv.verify_manifests(session, engine, certified_manifest_dump=certified_manifest_dump)
    _write_json(evidence_dir / "j11-stage-g-verify-manifests.json", manifests)
    print(f"manifests: ok={manifests['ok']} live_count={manifests['live_row_count']}", file=sys.stderr)

    with Session(engine) as session:
        audit_evidence_and_user_state = jsgv.verify_audit_evidence_and_user_state(
            session, engine,
            certified_pre_reset_inventory=certified_pre_reset_inventory,
            certified_data_provider_runs_count=certified_baseline.get("data_provider_runs_count", -1),
            certified_watchlist_count=certified_baseline.get("watchlist_count", -1),
        )
    _write_json(evidence_dir / "j11-stage-g-verify-audit-evidence-and-user-state.json", audit_evidence_and_user_state)
    print(f"audit/evidence/user-state: ok={audit_evidence_and_user_state['ok']}", file=sys.stderr)

    with Session(engine) as session:
        cache_dispositions = jsgv.verify_cache_dispositions(session, cfg, certified_dispositions=stage_f_dispositions)
    _write_json(evidence_dir / "j11-stage-g-verify-cache-dispositions.json", cache_dispositions)
    print(f"cache dispositions: ok={cache_dispositions['ok']}", file=sys.stderr)

    with Session(engine) as session:
        membership_timeline_check = jsgv.verify_membership_timeline_preserved_row(
            session, cfg, stage_f_new_dates=stage_f_new_dates,
        )
    _write_json(evidence_dir / "j11-stage-g-verify-membership-timeline-check.json", membership_timeline_check)
    print(
        f"membership timeline check: disposition={membership_timeline_check['disposition']} "
        f"dates_checked={membership_timeline_check['already_cached_incident_dates']}",
        file=sys.stderr,
    )

    pre_stage_c_run_id_by_date = {
        iso: (rec.get("scanner_run", {}) or {}).get("run_id")
        for iso, rec in (certified_pre_reset_inventory.get("per_date") or {}).items()
    }
    with Session(engine) as session:
        named_traps = jsgv.verify_named_traps(
            session, tests_dir=TESTS_DIR, expected_run_id_by_date=expected_run_id_by_date,
            frozen_engine_identity=stage_d_frozen_identity or "", boundary_recheck=boundary_recheck,
            pre_stage_c_run_id_by_date=pre_stage_c_run_id_by_date,
        )
    _write_json(evidence_dir / "j11-stage-g-verify-named-traps.json", named_traps)
    print(f"named traps: ok={named_traps['ok']} count={named_traps['trap_count']}", file=sys.stderr)

    write_path_sites = jsgv.enumerate_write_path_call_sites(APP_DIR)
    _write_json(evidence_dir / "j11-stage-g-verify-write-path-sites.json", write_path_sites)
    write_path_classification = jsgv.classify_write_path_call_sites(write_path_sites)
    _write_json(evidence_dir / "j11-stage-g-verify-write-path-classification.json", write_path_classification)
    print(
        f"write-path classification: ok={write_path_classification['ok']} "
        f"counts={write_path_classification['counts_by_classification']}",
        file=sys.stderr,
    )

    other_j11_stage_modules = sorted(
        p for p in (APP_DIR / "engine").glob("j11_*.py") if p.name != "j11_stage_g_verify.py"
    )
    evidence_reinterpretation_check = jsgv.confirm_no_evidence_reinterpretation_calls(*other_j11_stage_modules)
    _write_json(evidence_dir / "j11-stage-g-verify-evidence-reinterpretation-check.json", evidence_reinterpretation_check)
    print(f"evidence reinterpretation check: clean={evidence_reinterpretation_check['clean']}", file=sys.stderr)

    network_import_check = jsgv.confirm_no_network_capable_import(THIS_MODULE_PATH, THIS_SCRIPT_PATH)
    _write_json(evidence_dir / "j11-stage-g-verify-network-import-check.json", network_import_check)
    print(f"network import check: clean={network_import_check['clean']}", file=sys.stderr)

    backend_port = int(os.environ.get("CHAIN_BACKEND_PORT", "8000"))
    frontend_port = int(os.environ.get("CHAIN_FRONTEND_PORT", "3000"))
    operational_isolation = jsgv.verify_operational_isolation(backend_port=backend_port, frontend_port=frontend_port)
    _write_json(evidence_dir / "j11-stage-g-verify-operational-isolation.json", operational_isolation)
    print(f"operational isolation: ok={operational_isolation['ok']}", file=sys.stderr)

    # === Step 3: the mutation-accounting input, captured BEFORE any Stage G write ======================
    with Session(engine) as session:
        pre_maintenance_boundary_dump = migration.dump_table(engine, MaintenanceBoundary.__table__)

    stage_g_pre_write_mutation_accounting = jsgv.build_stage_g_cross_iteration_mutation_accounting(
        iter18_pre_stage_d_sweep=iter18_pre_stage_d_sweep, live_post_sweep=live_full_table_sweep_pre,
        pre_maintenance_boundary_dump=pre_maintenance_boundary_dump,
        post_maintenance_boundary_dump=pre_maintenance_boundary_dump,  # no write has happened yet
        membership_timeline_row_deleted_this_iteration=False, boundary_deactivated_this_iteration=False,
    )
    print(
        f"pre-write cross-iteration mutation accounting: ok={stage_g_pre_write_mutation_accounting['ok']} "
        f"unexplained={stage_g_pre_write_mutation_accounting['unexplained_by_sweep']}",
        file=sys.stderr,
    )

    with Session(engine) as session:
        vm_peak_kb = jsee.read_process_vm_peak_kb()
        memory_check = jsee.build_memory_check(vm_peak_kb=vm_peak_kb, memory_cap_mb=cfg.server.memory_cap_mb)
    _write_json(evidence_dir / "j11-stage-g-verify-memory-check.json", memory_check)
    print(f"memory check: vm_peak_mb={memory_check['vm_peak_mb']} within_cap={memory_check['within_cap']}", file=sys.stderr)

    # === Step 4: aggregate verdict ======================================================================
    verdict = jsgv.stage_g_verdict(
        preflight_gate=preflight_gate, raw_inputs=raw_inputs, snapshot_scope=snapshot_scope,
        forward_returns=forward_returns, manifests=manifests,
        audit_evidence_and_user_state=audit_evidence_and_user_state, cache_dispositions=cache_dispositions,
        membership_timeline_check=membership_timeline_check, named_traps=named_traps,
        write_path_classification=write_path_classification,
        evidence_reinterpretation_check=evidence_reinterpretation_check,
        operational_isolation=operational_isolation,
    )
    # the pre-write cross-iteration mutation accounting is folded in as an explicit extra gate (the
    # dedicated stage_g_verdict() signature intentionally excludes it -- see that function's own docstring
    # -- because the FINAL, post-write version is what actually gets persisted as evidence; this pre-write
    # copy is a strictly EARLIER, narrower proof over the SAME already-historical Stage D/E/F writes, so
    # requiring it here can only ever make the gate stricter, never looser).
    if not stage_g_pre_write_mutation_accounting["ok"]:
        verdict = {
            **verdict,
            "full_pass": False,
            "failing_categories": sorted(set(verdict["failing_categories"]) | {"cross_iteration_mutation_accounting"}),
        }
    _write_json(evidence_dir / "j11-stage-g-verify-verdict.json", verdict)
    print(f"STAGE G VERDICT: full_pass={verdict['full_pass']} failing={verdict['failing_categories']}", file=sys.stderr)

    # === Step 5: the one conditional corrective write (membership-timeline delete-if-stale) ============
    with Session(engine) as session:
        membership_timeline_delete_action = jsgv.execute_membership_timeline_delete_if_stale(
            session, verification=membership_timeline_check,
        )
    _write_json(evidence_dir / "j11-stage-g-verify-membership-timeline-delete-action.json", membership_timeline_delete_action)
    print(f"membership timeline delete action: deleted={membership_timeline_delete_action['deleted']}", file=sys.stderr)

    # === Step 6: finalize -- the ONE further conditional write on a full PASS ==========================
    with Session(engine) as session:
        finalize = jsgv.finalize_stage_g(session, verdict=verdict)
    _write_json(evidence_dir / "j11-stage-g-verify-finalize.json", finalize)
    print(f"finalize: outcome={finalize['outcome']} boundary_deactivated={finalize['boundary_deactivated']}", file=sys.stderr)

    # === Step 7: post-write, read-only mutation accounting -- written LAST, as final evidence ==========
    with Session(engine) as session:
        live_post_sweep = j11_maintenance.capture_full_table_sweep(session)
        post_maintenance_boundary_dump = migration.dump_table(engine, MaintenanceBoundary.__table__)
        live_membership_timeline_row_count = session.scalar(
            select(sa_func.count()).select_from(MembershipTimelineCache)
        )

    mutation_accounting = jsgv.build_stage_g_cross_iteration_mutation_accounting(
        iter18_pre_stage_d_sweep=iter18_pre_stage_d_sweep, live_post_sweep=live_post_sweep,
        pre_maintenance_boundary_dump=pre_maintenance_boundary_dump,
        post_maintenance_boundary_dump=post_maintenance_boundary_dump,
        membership_timeline_row_deleted_this_iteration=bool(membership_timeline_delete_action["deleted"]),
        boundary_deactivated_this_iteration=bool(finalize["boundary_deactivated"]),
    )
    mutation_accounting["live_membership_timeline_row_count_post"] = int(live_membership_timeline_row_count or 0)
    mutation_accounting["membership_timeline_delete_reconciles"] = (
        (not membership_timeline_delete_action["deleted"]) or int(live_membership_timeline_row_count or 0) == 0
    )
    _write_json(evidence_dir / "j11-stage-g-verify-mutation-accounting.json", mutation_accounting)
    print(
        f"post-write mutation accounting: ok={mutation_accounting['ok']} "
        f"membership_timeline_delete_reconciles={mutation_accounting['membership_timeline_delete_reconciles']}",
        file=sys.stderr,
    )

    outcome = {
        "generated_at": finalize["generated_at"],
        "stage_g_verdict_full_pass": verdict["full_pass"],
        "finalize_outcome": finalize["outcome"],
        "post_write_mutation_accounting_ok": mutation_accounting["ok"],
        "membership_timeline_delete_reconciles": mutation_accounting["membership_timeline_delete_reconciles"],
    }
    _write_json(evidence_dir / "j11-stage-g-verify-outcome.json", outcome)

    db_file_true_end = jsc.db_file_fingerprint(db_path)
    _write_json(evidence_dir / "j11-stage-g-verify-db-file-true-end.json", db_file_true_end)

    _print_terminal_lines(finalize["terminal_lines"])

    return 0 if (verdict["full_pass"] and mutation_accounting["ok"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
