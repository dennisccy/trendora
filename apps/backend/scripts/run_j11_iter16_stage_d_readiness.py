"""goal-market-compass iter-16 -- J-11 Goals 5 + 8: establish the new certified raw-input baseline (Goal
5) and re-run Stage D readiness against it (Goal 8), per the two 2026-08-25 owner rulings' explicit
sequencing: "AVB bounded correction -> verify the new raw-input baseline -> implement and prove the
pre-boot guard -> re-run Stage D readiness -> if READY: YES, STOP for owner authorization."

This is a NEW, thin iteration-16 driver script (the plan's own "developer's choice" option) rather than
an additive extension of THREE separate existing scripts (`run_j11_stage_d_preflight.py`,
`run_j11_avb_bridge_diagnostic.py`, `run_j11_stage_d_readiness.py`) -- every underlying engine function it
calls is reused UNCHANGED from those scripts' own call shapes; nothing is reimplemented.

Opens the live database through an ACTUAL read-only SQLite handle (`file:<path>?mode=ro` + `PRAGMA
query_only=ON`, mirroring `run_j11_stage_d_preflight.py`/`run_j11_avb_bridge_diagnostic.py`'s own helper)
-- this script performs ZERO writes; Goal 3's write already landed for real, earlier in this iteration,
via the separate confirm-gated `run_j11_avb_correction.py`. No `--confirm` flag: there is nothing here to
confirm.

Sequence:
  1. Fresh Stage D preflight capture against the CORRECTED live database (`j11_stage_d.
     capture_stage_d_preflight`, reused unchanged) -- its own `pre_reset_inventory.daily_prices.
     fingerprint` IS the new certified fingerprint (re-derived fresh here, not read back from Goal 4's
     own artifact).
  2. Gate the fresh preflight against the OLD (pre-correction) certified baseline
     (`j11_stage_d.load_stage_d_certified_baseline` + `compare_stage_d_preflight_to_certified`, both
     reused unchanged) -- MUST report `daily_prices_fingerprint_unchanged: False` (an honest, EXPECTED
     mismatch -- the correction is supposed to have moved it).
  3. Build the NEW certified baseline (`j11_stage_d.build_avb_correction_superseded_baseline`, Goal 5) and
     re-gate the SAME fresh preflight against it -- MUST report `all_invariants_hold: True`.
  4. Re-run the AVB bridge diagnostic against the corrected live `daily_prices`
     (`j11_avb_diagnostic.fetch_avb_stored_series` / `classify_local_convention_with_volume_evidence` /
     `compute_counterfactual_representations` / `trace_universe_resolver_impact` /
     `trace_scoring_and_selection_impact` / `classify_avb`, ALL reused unchanged), reusing iteration 15's
     already-committed provider-fetch evidence (zero new network fetch) -- per the plan's own instruction,
     the decision-impact trace is called WITHOUT `volume_override`: the write already landed for real, so
     representation A reads the corrected stored rows directly.
  5. Combine into the final verdict (`j11_stage_d.produce_stage_d_readiness_artifact`, reused unchanged),
     which writes `authorized: false` UNCONDITIONALLY.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_iter16_stage_d_readiness.py \\
        --evidence-dir runs/goal-market-compass-iter-16
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
from app.engine import j11_avb_correction as corr  # noqa: E402
from app.engine import j11_avb_diagnostic as diag  # noqa: E402
from app.engine import j11_stage_c as jsc  # noqa: E402
from app.engine import j11_stage_d as jsd  # noqa: E402

CANONICAL_EVIDENCE_DIR_FOR_DOCS = REPO_ROOT / "runs" / "goal-market-compass-iter-16"
DEFAULT_STAGE_C_PREFLIGHT_PATH = REPO_ROOT / "runs" / "goal-market-compass-iter-13" / "j11-stage-c-preflight.json"
DEFAULT_STAGE_C_MUTATION_ACCOUNTING_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-13" / "j11-stage-c-mutation-accounting.json"
)
DEFAULT_ITERATION_14_IDENTITY_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-14" / "j11-stage-d-attempt-identity.json"
)
DEFAULT_MUTATION_EVIDENCE_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-16" / "j11-avb-correction-mutation-evidence.json"
)
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


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
    print(f"wrote {path}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--evidence-dir", type=Path, default=None,
        help=(
            "required -- the directory every evidence JSON is written to. No default on purpose: the "
            f"real target ({CANONICAL_EVIDENCE_DIR_FOR_DOCS}) is a committed evidence directory."
        ),
    )
    parser.add_argument("--stage-c-preflight-path", type=Path, default=DEFAULT_STAGE_C_PREFLIGHT_PATH)
    parser.add_argument("--stage-c-mutation-accounting-path", type=Path, default=DEFAULT_STAGE_C_MUTATION_ACCOUNTING_PATH)
    parser.add_argument("--iteration-14-identity-path", type=Path, default=DEFAULT_ITERATION_14_IDENTITY_PATH)
    parser.add_argument(
        "--mutation-evidence-path", type=Path, default=DEFAULT_MUTATION_EVIDENCE_PATH,
        help="Goal 4's own consolidated mutation-evidence artifact -- cited as provenance on the new "
             "certified baseline (read-only input).",
    )
    parser.add_argument(
        "--provider-fetch-evidence-path", type=Path, default=corr.DEFAULT_PROVIDER_FETCH_EVIDENCE_PATH,
    )
    parser.add_argument("--j10-evidence-path", type=Path, default=diag.DEFAULT_J10_EVIDENCE_PATH)
    args = parser.parse_args()

    if args.evidence_dir is None:
        print(
            "refusing to run without an explicit --evidence-dir. No config has been loaded, no database "
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

    db_file_true_start = jsc.db_file_fingerprint(db_path)
    _write_json(args.evidence_dir / "j11-iter16-readiness-db-file-true-start.json", db_file_true_start)

    goal_md_text = jsc.read_goal_md_text()
    git_head = jsc.read_git_head()
    engine = _read_only_engine(db_path)

    prior_identity_value = None
    if args.iteration_14_identity_path is not None and Path(args.iteration_14_identity_path).exists():
        prior_identity_value = json.loads(Path(args.iteration_14_identity_path).read_text()).get("engine_identity")

    # --- Step 1: fresh Stage D preflight against the CORRECTED live database --------------------------
    with Session(engine) as session:
        preflight = jsd.capture_stage_d_preflight(
            session, engine, db_path, goal_md_text=goal_md_text, git_head=git_head, config=cfg,
            prior_iteration_14_identity=prior_identity_value,
        )
    _write_json(args.evidence_dir / "j11-stage-d-preflight.json", preflight)
    fresh_daily_prices_fingerprint = preflight["pre_reset_inventory"]["daily_prices"]["fingerprint"]
    print(
        f"fresh preflight captured: manifest_row_count={preflight['manifest_row_count']} "
        f"daily_prices_fingerprint={fresh_daily_prices_fingerprint} "
        f"c1_ok={preflight['c1_date_set_boundary_check']['ok']} "
        f"identity_check_a_ok={preflight['identity_check_a']['ok']}",
        file=sys.stderr,
    )

    # --- Step 2: gate against the OLD (pre-correction) certified baseline -- expect an HONEST mismatch --
    old_certified = jsd.load_stage_d_certified_baseline(
        args.stage_c_preflight_path, args.stage_c_mutation_accounting_path
    )
    gate_vs_old = jsd.compare_stage_d_preflight_to_certified(preflight, old_certified)
    verdict_vs_old = jsd.stage_d_preflight_verdict(gate_vs_old)
    _write_json(
        args.evidence_dir / "j11-stage-d-preflight-gate-vs-old-baseline.json",
        {"comparison": gate_vs_old, "verdict": verdict_vs_old},
    )
    print(
        f"gate vs OLD (pre-correction) certified baseline: "
        f"daily_prices_fingerprint_unchanged={gate_vs_old['checks']['daily_prices_fingerprint_unchanged']} "
        "(EXPECTED False -- the AVB correction is supposed to have moved this fingerprint)",
        file=sys.stderr,
    )

    # --- Step 3: build + gate the NEW certified baseline (Goal 5) ---------------------------------------
    new_certified = jsd.build_avb_correction_superseded_baseline(
        old_certified,
        post_correction_daily_prices_fingerprint=fresh_daily_prices_fingerprint,
        iteration=16,
        mutation_evidence_artifact_path=str(args.mutation_evidence_path),
    )
    _write_json(args.evidence_dir / "j11-stage-d-certified-baseline.json", new_certified)

    gate_vs_new = jsd.compare_stage_d_preflight_to_certified(preflight, new_certified)
    verdict_vs_new = jsd.stage_d_preflight_verdict(gate_vs_new)
    _write_json(args.evidence_dir / "j11-stage-d-preflight-gate.json", {"comparison": gate_vs_new, "verdict": verdict_vs_new})
    print(
        f"gate vs NEW (superseded) certified baseline: all_invariants_hold={gate_vs_new['all_invariants_hold']}",
        file=sys.stderr,
    )
    if not gate_vs_new["all_invariants_hold"]:
        failing = [k for k, v in gate_vs_new["checks"].items() if not v]
        print(f"FAILING CHECKS against the NEW baseline: {failing}", file=sys.stderr)

    # --- Step 4: re-run the AVB bridge diagnostic against the corrected live daily_prices ---------------
    fetch_evidence = json.loads(Path(args.provider_fetch_evidence_path).read_text())
    provider_evidence_by_date: dict = fetch_evidence.get("per_date", {})
    evidence_row = diag.load_j10_avb_evidence(args.j10_evidence_path)
    bridge_factor = evidence_row["bridge_factor"]
    pool_distribution = diag.summarize_pool_bridge_factor_distribution(args.j10_evidence_path)
    print(
        f"reusing iteration-15 provider-fetch evidence (sufficient_evidence="
        f"{fetch_evidence.get('sufficient_evidence')}, zero new network fetch this iteration): "
        f"bridge_factor={bridge_factor}",
        file=sys.stderr,
    )

    with Session(engine) as session:
        stored_series = diag.fetch_avb_stored_series(session, date(2026, 6, 1), date(2026, 12, 31))
        local_convention = diag.classify_local_convention_with_volume_evidence(
            stored_series, evidence_row, provider_evidence_by_date
        )

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

        # Goal 8's own instruction: NO volume_override -- the write already landed for real, so
        # representation A reads the corrected stored rows directly, never an in-memory substitution.
        decision_impact_by_date: dict[str, dict] = {}
        for one_date in diag.RECOVERED_DATES:
            key = one_date.isoformat()
            print(f"tracing decision impact for {key} (no volume_override -- corrected DB read directly) ...", file=sys.stderr)
            ur_impact = diag.trace_universe_resolver_impact(session, cfg, one_date, bridge_factor)
            scoring_impact = diag.trace_scoring_and_selection_impact(session, cfg, one_date, bridge_factor)
            decision_impact_by_date[key] = {"universe_resolver": ur_impact, "scoring_and_selection": scoring_impact}
            print(
                f"  {key}: admission_changed={ur_impact['admission_changed']} "
                f"avb_resolved_member={scoring_impact.get('avb_resolved_member')} "
                f"risk_bucket_a={scoring_impact.get('risk_bucket_a')} risk_bucket_b={scoring_impact.get('risk_bucket_b')} "
                f"eligible_a={scoring_impact.get('eligible_a')} eligible_b={scoring_impact.get('eligible_b')}",
                file=sys.stderr,
            )

    classification = diag.classify_avb(local_convention, decision_impact_by_date)
    if not fetch_evidence.get("sufficient_evidence", False):
        classification = dict(classification)
        classification["classification"] = "AVB-D"
        classification["stage_d_ready_per_avb"] = False
        classification["reasoning"] = (
            "iteration-15's AG-9 dated-exception-#2 fetch did NOT supply sufficient evidence for all six "
            "permitted dates; classifying AVB-D per the amendment's own fail-closed rule."
        )

    db_file_true_end_for_diag = jsc.db_file_fingerprint(db_path)
    zero_write_proof = {
        "db_file_true_start": db_file_true_start,
        "db_file_true_end": db_file_true_end_for_diag,
        "mtime_unchanged": db_file_true_start.get("mtime") == db_file_true_end_for_diag.get("mtime"),
        "size_unchanged": db_file_true_start.get("size_bytes") == db_file_true_end_for_diag.get("size_bytes"),
    }

    avb_diagnostic_result = {
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
        "zero_write_proof": zero_write_proof,
        "note": (
            "goal-market-compass iter-16 re-run against the CORRECTED live daily_prices (Goal 3's write "
            "already landed for real) -- decision-impact traced WITHOUT volume_override (reads the "
            "corrected stored rows directly). Cite runs/goal-market-compass-iter-15/"
            "j11-avb-bridge-diagnostic.json as historically accurate FOR THE PRE-CORRECTION state -- "
            "never edited, never deleted."
        ),
    }
    _write_json(args.evidence_dir / "j11-avb-bridge-diagnostic.json", avb_diagnostic_result)
    print(
        f"AVB classification (mechanically derived, corrected baseline): {classification['classification']} "
        f"stage_d_ready_per_avb={classification['stage_d_ready_per_avb']}",
        file=sys.stderr,
    )

    # --- Step 5: combine into the final readiness verdict (reused unchanged) ----------------------------
    readiness = jsd.produce_stage_d_readiness_artifact(
        args.evidence_dir / "j11-stage-d-preflight-gate.json",
        args.evidence_dir / "j11-avb-bridge-diagnostic.json",
        output_path=args.evidence_dir / "j11-stage-d-readiness.json",
    )

    db_file_true_end = jsc.db_file_fingerprint(db_path)
    _write_json(args.evidence_dir / "j11-iter16-readiness-db-file-true-end.json", db_file_true_end)
    print(
        f"whole-script zero-write proof: mtime_unchanged="
        f"{db_file_true_start.get('mtime') == db_file_true_end.get('mtime')} "
        f"size_unchanged={db_file_true_start.get('size_bytes') == db_file_true_end.get('size_bytes')}",
        file=sys.stderr,
    )

    print(
        f"avb_classification={readiness['avb_classification']} "
        f"preflight_gate_passed={readiness['preflight_gate_passed']} "
        f"blocking_reasons={readiness['blocking_reasons']}",
        file=sys.stderr,
    )
    print(
        "citing runs/goal-market-compass-iter-15/j11-stage-d-readiness.json as historically accurate for "
        "the PRE-CORRECTION state (avb_classification=AVB-C, ready=false) -- never edited, never deleted; "
        "this iteration's result reflects the NEW corrected baseline.",
        file=sys.stderr,
    )
    print(f"J-11 STAGE D READY: {'YES' if readiness['ready'] else 'NO'}", file=sys.stderr)
    print("J-11 STAGE D AUTHORIZED: NO", file=sys.stderr)
    return 0 if readiness["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
