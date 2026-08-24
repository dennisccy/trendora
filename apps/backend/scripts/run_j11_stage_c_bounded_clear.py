"""goal-market-compass iter-13 -- J-11 Stage C: the ONE owner-authorized bounded destructive clear of
the 11 incident dates' Layer-2 derived state (docs/goal.md J-11 step 11's "## OWNER AUTHORIZATION --
J-11 Stage C (owner, 2026-08-24)" block, rulings C1-C12).

Mirrors `run_j11_stage_b1_manifest_schema_migration.py`'s idiom exactly: NO database interaction of any
kind, not even a read, without `--confirm`; evidence is persisted at every checkpoint BEFORE the
destructive step so a mid-run crash still leaves a forensic trail; the completion marker is written ONLY
after every verification check passes (ruling C9). Sequence, exactly as ruling C10/step 11's own
ordering requires: fresh preflight (C2) -> preflight comparison gate against iteration 12's certified
state (TC-2) -> C1 date-set boundary check (TC-3) -> intended-delete-set capture (C9, BEFORE any DELETE)
-> `clear_snapshot_dates` (the ONE authorized write) -> post-delete mutation accounting (TC-7..TC-12) ->
completion marker (TC-13). ANY failure at ANY stage before the delete STOPS before the first destructive
statement; ANY failure AFTER the delete still writes no marker, exits non-zero, and preserves every
artifact already captured -- Stage C never claims completion it cannot prove (ruling C9/step 13).

This is the ONE authorized live write anywhere in goal-market-compass iter-13 (ruling C10: "Stage C
stands alone, and STOPS" -- no Stage D/E/F/G work follows in this process). One controlled writer, no
boot warmup racing it (maintenance isolation stays active this whole iteration), no network call
anywhere in this process, never a raw file copy of the 7.8+ GB database.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_stage_c_bounded_clear.py \\
        --confirm \\
        [--evidence-dir runs/goal-market-compass-iter-13] \\
        [--certified-state-path runs/goal-market-compass-iter-12/j11-stage-b1-cleanup-fingerprint-after.json]

Without `--confirm`, the script performs NO database interaction at all (not even a read) and exits
non-zero.
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

from sqlmodel import Session  # noqa: E402

from app.config import load_config  # noqa: E402
from app.db import get_engine, resolve_database_url  # noqa: E402
from app.engine import j11_stage_c as jsc  # noqa: E402
from app.engine.data_manager import clear_snapshot_dates  # noqa: E402
from app.engine.j11_maintenance import INCIDENT_DATES, capture_pre_reset_inventory  # noqa: E402
from app.engine import j11_schema_migration as migration  # noqa: E402
from app.models import DataProviderRun, NextSessionManifest, Watchlist  # noqa: E402

DEFAULT_EVIDENCE_DIR = REPO_ROOT / "runs" / "goal-market-compass-iter-13"
DEFAULT_CERTIFIED_STATE_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-12" / "j11-stage-b1-cleanup-fingerprint-after.json"
)
EXPECTED_CERTIFIED_MANIFEST_ROW_COUNT = 24  # sanity check on WHICH baseline file was loaded, not a gate


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE_DIR)
    parser.add_argument("--certified-state-path", type=Path, default=DEFAULT_CERTIFIED_STATE_PATH)
    parser.add_argument(
        "--confirm", action="store_true",
        help="required -- without it, the script touches the database not at all and exits non-zero.",
    )
    args = parser.parse_args()

    if not args.confirm:
        print(
            "refusing to run without --confirm (this is the ONE owner-authorized bounded destructive "
            "write this iteration -- docs/goal.md J-11 step 11 OWNER AUTHORIZATION block). No database "
            "interaction, not even a read, has occurred.",
            file=sys.stderr,
        )
        return 2

    evidence_dir: Path = args.evidence_dir

    cfg = load_config()
    resolved_url = resolve_database_url(cfg.database.url)
    db_path = _db_file_path(resolved_url)
    print(f"database: {resolved_url}", file=sys.stderr)

    # --- TRUE process start: the db file + WAL sidecar fingerprint, before anything else touches it ---
    db_file_true_start = jsc.db_file_fingerprint(db_path)
    _write_json(evidence_dir / "j11-stage-c-db-file-true-start.json", db_file_true_start)

    engine = get_engine()  # the SAME pooled writable engine the real backend uses -- never a raw file
    # copy, never create_db_and_tables()/metadata.create_all() (out of scope under this authorization).

    goal_md_text = jsc.read_goal_md_text()
    git_head = jsc.read_git_head()

    # --- C2: fresh Stage C preflight, persisted BEFORE any gate decision -------------------------------
    with Session(engine) as session:
        preflight = jsc.capture_stage_c_preflight(
            session, engine, db_path, goal_md_text=goal_md_text, git_head=git_head, config=cfg,
        )
    _write_json(evidence_dir / "j11-stage-c-preflight.json", preflight)
    print(
        f"preflight captured: manifest_row_count={preflight['manifest_row_count']} "
        f"c1_ok={preflight['c1_date_set_boundary_check']['ok']} git_head={git_head}",
        file=sys.stderr,
    )

    # --- TC-2: the preflight comparison gate against iteration 12's certified state --------------------
    certified = jsc.load_certified_state(args.certified_state_path)
    if certified.get("manifest_row_count") != EXPECTED_CERTIFIED_MANIFEST_ROW_COUNT:
        print(
            f"FAIL: the loaded certified-state baseline ({args.certified_state_path}) does not carry the "
            f"expected {EXPECTED_CERTIFIED_MANIFEST_ROW_COUNT} manifest rows "
            f"(found {certified.get('manifest_row_count')!r}) -- wrong baseline file, refusing to compare "
            "against it. No DELETE statement has executed.",
            file=sys.stderr,
        )
        return 1

    gate = jsc.compare_preflight_to_certified(preflight, certified)
    _write_json(evidence_dir / "j11-stage-c-preflight-comparison-gate.json", gate)
    print(f"preflight comparison gate: all_invariants_hold={gate['all_invariants_hold']}", file=sys.stderr)

    verdict = jsc.stage_c_overall_verdict(gate, mutation_accounting=None)
    if not gate["all_invariants_hold"]:
        print(
            "STOP: the preflight comparison gate found a material mismatch against the certified "
            "iteration-12 state (or a B/B1/B2 invariant no longer holds). No DELETE statement has "
            "executed. See j11-stage-c-preflight-comparison-gate.json for the failing checks.",
            file=sys.stderr,
        )
        return 1

    # --- TC-3: the C1 date-set boundary check (already computed inside the preflight; re-asserted here
    # as its own explicit stop point, per the spec's own numbered step ordering) -------------------------
    if not preflight["c1_date_set_boundary_check"]["ok"]:
        print(
            "STOP: the C1 date-set boundary check failed -- the code's INCIDENT_DATES list disagrees "
            "with one or both of docs/goal.md's own 11-date lists, or an anchor could not be located. "
            "No DELETE statement has executed.",
            file=sys.stderr,
        )
        return 1

    # --- C9: the intended delete set, captured and persisted BEFORE any DELETE statement executes -------
    with Session(engine) as session:
        intended_delete_set = jsc.capture_intended_delete_set(session, INCIDENT_DATES)
    _write_json(evidence_dir / "j11-stage-c-intended-delete-set.json", intended_delete_set)
    deleted_run_ids = intended_delete_set["deleted_run_ids"]
    print(
        f"intended delete set: {intended_delete_set['total_counts']} deleted_run_ids={deleted_run_ids}",
        file=sys.stderr,
    )

    # --- pre-delete mutation-accounting inputs, captured immediately before the destructive call --------
    with Session(engine) as session:
        pre_layer2_population = jsc.capture_layer2_population_fingerprints(session, deleted_run_ids)
        pre_incident_scoped = jsc.incident_scoped_counts(session, deleted_run_ids)
        pre_daily_prices = capture_pre_reset_inventory(session)["daily_prices"]
        pre_manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
        pre_provider_runs = jsc.small_table_id_snapshot(session, DataProviderRun)
        pre_watchlist = jsc.small_table_id_snapshot(session, Watchlist)
    pre_full_db_snapshot = migration.capture_full_db_snapshot(engine, db_path)

    # --- THE ONE AUTHORIZED DESTRUCTIVE WRITE -------------------------------------------------------
    with Session(engine) as session:
        clear_result = clear_snapshot_dates(session, INCIDENT_DATES)
    print(f"clear_snapshot_dates totals: {clear_result['totals']}", file=sys.stderr)

    # --- post-delete mutation-accounting inputs -----------------------------------------------------
    with Session(engine) as session:
        post_layer2_population = jsc.capture_layer2_population_fingerprints(session, deleted_run_ids)
        post_incident_scoped = jsc.incident_scoped_counts(session, deleted_run_ids)
        post_daily_prices = capture_pre_reset_inventory(session)["daily_prices"]
        post_manifest_dump = migration.dump_table(engine, NextSessionManifest.__table__)
        post_provider_runs = jsc.small_table_id_snapshot(session, DataProviderRun)
        post_watchlist = jsc.small_table_id_snapshot(session, Watchlist)
    post_full_db_snapshot = migration.capture_full_db_snapshot(engine, db_path)

    # --- TRUE process end: the db file + WAL sidecar fingerprint, captured last ------------------------
    db_file_true_end = jsc.db_file_fingerprint(db_path)
    _write_json(evidence_dir / "j11-stage-c-db-file-true-end.json", db_file_true_end)

    mutation_accounting = jsc.build_mutation_accounting(
        pre_layer2_population=pre_layer2_population,
        post_layer2_population=post_layer2_population,
        pre_full_db_snapshot=pre_full_db_snapshot,
        post_full_db_snapshot=post_full_db_snapshot,
        pre_daily_prices=pre_daily_prices,
        post_daily_prices=post_daily_prices,
        pre_manifest_dump=pre_manifest_dump,
        post_manifest_dump=post_manifest_dump,
        pre_provider_runs=pre_provider_runs,
        post_provider_runs=post_provider_runs,
        pre_watchlist=pre_watchlist,
        post_watchlist=post_watchlist,
        pre_incident_scoped_counts=pre_incident_scoped,
        post_incident_scoped_counts=post_incident_scoped,
        intended_delete_set=intended_delete_set,
        clear_result=clear_result,
        db_file_true_start=db_file_true_start,
        db_file_true_end=db_file_true_end,
    )
    _write_json(evidence_dir / "j11-stage-c-mutation-accounting.json", mutation_accounting)
    print(f"mutation accounting: all_checks_pass={mutation_accounting['all_checks_pass']}", file=sys.stderr)
    if not mutation_accounting["all_checks_pass"]:
        failing = [k for k, v in mutation_accounting["checks"].items() if not v]
        print(f"FAILING CHECKS: {failing}", file=sys.stderr)

    final_verdict = jsc.stage_c_overall_verdict(gate, mutation_accounting)
    if not final_verdict["passed"]:
        print(
            f"STAGE C DID NOT VERIFY (reason={final_verdict['reason']!r}). The delete already executed "
            "and cannot be undone by this script (no transaction spans the whole batch -- see docs/"
            "goal.md J-11 step 14). No completion marker is written. All captured evidence is preserved "
            "for owner review. Do NOT continue toward Stage D.",
            file=sys.stderr,
        )
        return 1

    prior_timestamps = [
        preflight["captured_at"], gate["generated_at"], intended_delete_set["captured_at"],
        mutation_accounting["generated_at"],
    ]
    marker = jsc.build_completion_marker(final_verdict, prior_timestamps)
    _write_json(evidence_dir / "j11-stage-c-complete.json", marker)

    print(
        f"J-11 STAGE C COMPLETE: YES (completed_at={marker['completed_at']})",
        file=sys.stderr,
    )
    print("J-11 STAGE D AUTHORIZED: NO", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
