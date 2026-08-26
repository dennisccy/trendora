"""goal-market-compass iter-17 -- J-11 Stage D readiness rider: re-run the AVB decision-impact trace WITH
`volume_override` (docs/goal.md J-11 step 11, "OWNER RULING -- J-11 maintenance-boundary lifecycle
AUTHORIZED" section's own rider instruction).

Iteration 16 established the corrected `daily_prices` raw-input baseline (the AVB two-cell volume
correction) and re-ran the readiness classification, but its OWN decision-impact trace call passed NO
`volume_override` to `trace_universe_resolver_impact` / `trace_scoring_and_selection_impact` (Goal 8's own
instruction at the time: "representation A reads the corrected stored rows directly"). That left
representation B pairing a COUNTERFACTUAL close (`stored_bridged_close / bridge_factor`, undoing the
bridge on price only) with the ALREADY-CORRECTED stored volume (calibrated to compensate for the BRIDGED
close, not the un-bridged one) -- an inconsistent hybrid whose single-bar dollar-volume ratio (A / B) lands
EXACTLY on `bridge_factor` by construction (verified algebraically and empirically below), not because of
any genuine material effect. That mechanical artifact is what produced classification `AVB-B` instead of
the honest `AVB-A`.

This rider supplies `volume_override` -- built from iteration-15's ALREADY-COMMITTED, already-fetched
`j11-avb-provider-fetch-evidence.json` (`{iso_date: {"close": ..., "volume": ...}}` for the two
RECOVERED_DATES) -- to BOTH decision-impact trace calls, unchanged function signatures, no new engine
logic (`volume_override` has been an accepted optional parameter on both functions since iteration 15;
iteration 16 simply never passed it). With the override, representation B pairs the SAME counterfactual
close with the RAW fetched provider volume -- both genuinely on the un-bridged basis -- so its dollar
volume should land near representation A's (within the calibration window's own relative tolerance), not
on `bridge_factor`.

Reused, UNCHANGED: `j11_stage_d.capture_stage_d_preflight` / `compare_stage_d_preflight_to_certified` /
`stage_d_preflight_verdict` / `produce_stage_d_readiness_artifact`; `j11_avb_diagnostic.
fetch_avb_stored_series` / `classify_local_convention_with_volume_evidence` /
`trace_universe_resolver_impact` / `trace_scoring_and_selection_impact` / `classify_avb` /
`load_j10_avb_evidence` / `summarize_pool_bridge_factor_distribution`. This script does NOT re-run
`run_j11_avb_correction.py` (already spent, one-time -- AG-9's dated exception #2 is exhausted) and does
NOT edit iteration 16's `j11-stage-d-certified-baseline.json` or `j11-stage-d-readiness.json` -- both are
loaded read-only as this iteration's certified baseline (nothing in `daily_prices` has changed since
iteration 16 minted them, so no NEW baseline needs building; only Goal 5's own supersession is reused).

Zero writes: opens the live database through an ACTUAL read-only SQLite handle (`file:<path>?mode=ro` +
`PRAGMA query_only=ON`, the SAME `_read_only_engine` idiom `run_j11_iter16_stage_d_readiness.py` /
`run_j11_iter17_live_preboot_guard_verification.py` already established).

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/run_j11_iter17_stage_d_readiness.py \\
        --evidence-dir runs/goal-market-compass-iter-17
"""
from __future__ import annotations

import argparse
import hashlib
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

DEFAULT_ITERATION_16_CERTIFIED_BASELINE_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-16" / "j11-stage-d-certified-baseline.json"
)
DEFAULT_ITERATION_16_READINESS_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-16" / "j11-stage-d-readiness.json"
)
DEFAULT_ITERATION_14_IDENTITY_PATH = (
    REPO_ROOT / "runs" / "goal-market-compass-iter-14" / "j11-stage-d-attempt-identity.json"
)
PERMITTED_DATES = diag.CALIBRATION_DATES + diag.RECOVERED_DATES

# goal-market-compass iter-18 rider (docs/goal.md J-11 step 11 ruling; iteration-17's own filed
# recommendation -- "one can overwrite three of iteration 16's saved evidence files if its destination
# folder is mistyped"): every filename THIS script ever writes, checked for a pre-existing collision
# BEFORE any other work runs. All three of `j11-stage-d-preflight.json` / `-preflight-gate.json` /
# `j11-avb-bridge-diagnostic.json` already exist under `runs/goal-market-compass-iter-16/` -- exactly the
# destination a mistyped `--evidence-dir` would collide with.
OUTPUT_FILENAMES = (
    "j11-stage-d-preflight.json",
    "j11-stage-d-preflight-gate.json",
    "j11-avb-bridge-diagnostic.json",
    "j11-iter17-stage-d-readiness.json",
    "j11-iter17-stage-d-readiness-zero-write-proof.json",
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


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
    print(f"wrote {path}", file=sys.stderr)


def _refuse_if_evidence_files_exist(evidence_dir: Path, filenames: tuple) -> list[str]:
    """goal-market-compass iter-18 rider: mirrors the SAME collision guard added to
    `run_j11_iter17_live_preboot_guard_verification.py`. Returns the (possibly empty) list of filenames
    that ALREADY EXIST under `evidence_dir` -- pure filesystem check, no database interaction."""
    return [name for name in filenames if (evidence_dir / name).exists()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--evidence-dir", type=Path, default=None,
        help="required -- no default on purpose (mirrors every other J-11 evidence-writing script).",
    )
    parser.add_argument(
        "--iteration-16-certified-baseline-path", type=Path, default=DEFAULT_ITERATION_16_CERTIFIED_BASELINE_PATH,
        help="iteration 16's own already-built certified baseline -- loaded READ-ONLY, never rebuilt "
             "(nothing in daily_prices changed since iteration 16 minted it).",
    )
    parser.add_argument("--iteration-16-readiness-path", type=Path, default=DEFAULT_ITERATION_16_READINESS_PATH)
    parser.add_argument("--iteration-14-identity-path", type=Path, default=DEFAULT_ITERATION_14_IDENTITY_PATH)
    parser.add_argument("--provider-fetch-evidence-path", type=Path, default=corr.DEFAULT_PROVIDER_FETCH_EVIDENCE_PATH)
    parser.add_argument("--j10-evidence-path", type=Path, default=diag.DEFAULT_J10_EVIDENCE_PATH)
    args = parser.parse_args()

    if args.evidence_dir is None:
        print(
            "refusing to run without an explicit --evidence-dir. No config has been loaded, no database "
            "engine has been constructed, and nothing has been written.",
            file=sys.stderr,
        )
        return 2

    # --- rider 6a: refuse BEFORE any other work if the destination already holds any of THIS script's ---
    # --- own output filenames (a mistyped --evidence-dir pointed at an earlier iteration's folder). -----
    colliding = _refuse_if_evidence_files_exist(args.evidence_dir, OUTPUT_FILENAMES)
    if colliding:
        print(
            f"refusing to run: --evidence-dir {args.evidence_dir} already contains {colliding} -- this "
            "looks like a mistyped destination pointed at an existing, already-populated evidence folder "
            "rather than a fresh one for this run. No config has been loaded, no database engine has been "
            "constructed, and no existing file has been touched.",
            file=sys.stderr,
        )
        return 2

    # --- byte-unedited proof for iteration 16's own artifact, hashed BEFORE anything else runs -----------
    iter16_readiness_hash_before = hashlib.sha256(args.iteration_16_readiness_path.read_bytes()).hexdigest()

    cfg = load_config()
    resolved_url = resolve_database_url(cfg.database.url)
    db_path = _db_file_path(resolved_url)
    if db_path is None or not db_path.exists():
        print(f"FAIL: could not resolve a live sqlite db file from {resolved_url!r}", file=sys.stderr)
        return 1
    print(f"database (READ-ONLY handle, mode=ro + PRAGMA query_only=ON): {db_path}", file=sys.stderr)

    db_file_before = jsc.db_file_fingerprint(db_path)

    goal_md_text = jsc.read_goal_md_text()
    git_head = jsc.read_git_head()
    engine = _read_only_engine(db_path)

    prior_identity_value = None
    if args.iteration_14_identity_path is not None and Path(args.iteration_14_identity_path).exists():
        prior_identity_value = json.loads(Path(args.iteration_14_identity_path).read_text()).get("engine_identity")

    # --- Step 1: fresh Stage D preflight against the (still-)corrected live database ---------------------
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

    # --- Step 2: gate against iteration 16's OWN certified baseline -- expect a CLEAN match this time -----
    # (unlike iteration 16 vs 15, which expected an honest mismatch because the correction itself moved
    # the fingerprint that iteration -- nothing has mutated daily_prices since iteration 16 landed it).
    certified = json.loads(args.iteration_16_certified_baseline_path.read_text())
    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
    verdict = jsd.stage_d_preflight_verdict(gate)
    _write_json(args.evidence_dir / "j11-stage-d-preflight-gate.json", {"comparison": gate, "verdict": verdict})
    print(
        f"gate vs iteration-16 certified baseline: all_invariants_hold={gate['all_invariants_hold']} "
        f"daily_prices_fingerprint_unchanged={gate['checks']['daily_prices_fingerprint_unchanged']} "
        "(EXPECTED True -- no daily_prices mutation has occurred since iteration 16)",
        file=sys.stderr,
    )
    if not gate["all_invariants_hold"]:
        failing = [k for k, v in gate["checks"].items() if not v]
        print(
            f"UNEXPECTED: failing checks against iteration 16's certified baseline: {failing} -- something "
            "changed the raw/manifest state since iteration 16 landed its correction. STOPPING rather than "
            "silently proceeding to classify against a baseline that no longer matches live state.",
            file=sys.stderr,
        )
        return 1

    # --- Step 3: re-run the AVB bridge diagnostic WITH volume_override on BOTH decision-impact traces -----
    fetch_evidence = json.loads(Path(args.provider_fetch_evidence_path).read_text())
    provider_evidence_by_date: dict = fetch_evidence.get("per_date", {})
    evidence_row = diag.load_j10_avb_evidence(args.j10_evidence_path)
    bridge_factor = evidence_row["bridge_factor"]
    pool_distribution = diag.summarize_pool_bridge_factor_distribution(args.j10_evidence_path)

    # The volume_override map this rider exists to supply: RAW fetched provider volume (iteration-15
    # evidence) for exactly the RECOVERED_DATES -- never a re-derivation, never the corrected stored value.
    volume_override: dict = {}
    for one_date in diag.RECOVERED_DATES:
        key = one_date.isoformat()
        entry = provider_evidence_by_date.get(key)
        if entry is not None and entry.get("volume") is not None:
            volume_override[one_date] = entry["volume"]
    print(
        f"volume_override built from {args.provider_fetch_evidence_path} for "
        f"{sorted(d.isoformat() for d in volume_override)}: "
        f"{ {d.isoformat(): v for d, v in volume_override.items()} }",
        file=sys.stderr,
    )
    if set(volume_override) != set(diag.RECOVERED_DATES):
        print(
            "FAIL: volume_override does not cover both RECOVERED_DATES -- iteration-15's provider-fetch "
            "evidence is missing volume for at least one of them. Refusing to classify on incomplete "
            "override evidence.",
            file=sys.stderr,
        )
        return 1

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

        # THE rider's own change: volume_override IS threaded through this time, to BOTH calls.
        decision_impact_by_date: dict[str, dict] = {}
        single_bar_ab_ratio_by_date: dict[str, dict] = {}
        for one_date in diag.RECOVERED_DATES:
            key = one_date.isoformat()
            print(f"tracing decision impact for {key} (WITH volume_override this time) ...", file=sys.stderr)
            ur_impact = diag.trace_universe_resolver_impact(
                session, cfg, one_date, bridge_factor, volume_override=volume_override
            )
            scoring_impact = diag.trace_scoring_and_selection_impact(
                session, cfg, one_date, bridge_factor, volume_override=volume_override
            )
            decision_impact_by_date[key] = {"universe_resolver": ur_impact, "scoring_and_selection": scoring_impact}
            print(
                f"  {key}: admission_changed={ur_impact['admission_changed']} "
                f"avb_resolved_member={scoring_impact.get('avb_resolved_member')} "
                f"risk_bucket_a={scoring_impact.get('risk_bucket_a')} risk_bucket_b={scoring_impact.get('risk_bucket_b')} "
                f"eligible_a={scoring_impact.get('eligible_a')} eligible_b={scoring_impact.get('eligible_b')}",
                file=sys.stderr,
            )

            # --- TC-13's own explicit check: the SINGLE-BAR A/B dollar-volume ratio for the target date --
            # (a script-level composition of already-existing values, no new engine logic): representation
            # A is the stored bar as-is (post iter-16 correction); representation B is the SAME
            # close/bridge_factor transform `_build_bars_with_transformed_close` applies internally, paired
            # with the override volume -- reproduced here explicitly so the ratio is a directly inspectable,
            # persisted number rather than buried inside the window-averaged ADV fields above.
            stored_row = stored_rows_by_date[key]
            close_a, volume_a = stored_row["close"], stored_row["volume"]
            close_b = close_a / bridge_factor
            volume_b = volume_override[one_date]
            dollar_a = close_a * volume_a
            dollar_b = close_b * volume_b
            ratio_a_over_b = dollar_a / dollar_b if dollar_b else None
            single_bar_ab_ratio_by_date[key] = {
                "close_a": close_a, "volume_a": volume_a, "dollar_a": dollar_a,
                "close_b": close_b, "volume_b_override_applied": volume_b, "dollar_b": dollar_b,
                "ratio_a_over_b": ratio_a_over_b,
                "within_relative_tolerance_of_one": diag._within_relative_tolerance(ratio_a_over_b, 1.0),
                "landed_on_bridge_factor": diag._within_relative_tolerance(ratio_a_over_b, bridge_factor),
                "tolerance": diag._RATIO_RELATIVE_TOLERANCE,
                "note": (
                    "iteration 16 (no volume_override) paired counterfactual close_b=close_a/bridge_factor "
                    "with the UNCHANGED stored (already-corrected/compensating) volume, so this exact ratio "
                    "landed EXACTLY on bridge_factor by construction. With volume_override applying the RAW "
                    "fetched provider volume to volume_b instead, this ratio should land near 1.0 within "
                    "the calibration window's own relative tolerance -- both A and B now express genuinely "
                    "independent, self-consistent (price, volume) pairs."
                ),
            }

    classification = diag.classify_avb(local_convention, decision_impact_by_date)
    if not fetch_evidence.get("sufficient_evidence", False):
        classification = dict(classification)
        classification["classification"] = "AVB-D"
        classification["stage_d_ready_per_avb"] = False
        classification["reasoning"] = (
            "iteration-15's AG-9 dated-exception-#2 fetch did NOT supply sufficient evidence for all six "
            "permitted dates; classifying AVB-D per the amendment's own fail-closed rule."
        )

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
        "volume_override_by_date": {d.isoformat(): v for d, v in volume_override.items()},
        "single_bar_ab_dollar_volume_ratio_by_date": single_bar_ab_ratio_by_date,
        "classification": classification,
        "note": (
            "goal-market-compass iter-17 rider: re-runs iteration 16's decision-impact trace WITH "
            "volume_override supplied to both trace_universe_resolver_impact and "
            "trace_scoring_and_selection_impact (both have accepted this optional parameter unchanged "
            "since iteration 15; iteration 16 simply never passed it). Cite runs/goal-market-compass-"
            "iter-16/j11-avb-bridge-diagnostic.json as historically accurate for the NO-volume_override "
            "state -- never edited, never deleted."
        ),
    }
    _write_json(args.evidence_dir / "j11-avb-bridge-diagnostic.json", avb_diagnostic_result)
    print(
        f"AVB classification (WITH volume_override): {classification['classification']} "
        f"stage_d_ready_per_avb={classification['stage_d_ready_per_avb']}",
        file=sys.stderr,
    )
    for key, r in single_bar_ab_ratio_by_date.items():
        print(
            f"  single-bar A/B dollar-volume ratio {key}: {r['ratio_a_over_b']} "
            f"within_tolerance_of_1={r['within_relative_tolerance_of_one']} "
            f"landed_on_bridge_factor={r['landed_on_bridge_factor']} (bridge_factor={bridge_factor})",
            file=sys.stderr,
        )

    # --- Step 4: combine into the final readiness verdict (reused unchanged) ------------------------------
    readiness = jsd.produce_stage_d_readiness_artifact(
        args.evidence_dir / "j11-stage-d-preflight-gate.json",
        args.evidence_dir / "j11-avb-bridge-diagnostic.json",
        output_path=args.evidence_dir / "j11-iter17-stage-d-readiness.json",
    )

    db_file_after = jsc.db_file_fingerprint(db_path)
    zero_write_proof = {
        "db_file_before": db_file_before,
        "db_file_after": db_file_after,
        "mtime_unchanged": db_file_before.get("mtime") == db_file_after.get("mtime"),
        "size_unchanged": db_file_before.get("size_bytes") == db_file_after.get("size_bytes"),
        "wal_unchanged": db_file_before.get("wal") == db_file_after.get("wal"),
    }
    _write_json(args.evidence_dir / "j11-iter17-stage-d-readiness-zero-write-proof.json", zero_write_proof)
    print(
        f"this-script zero-write proof: mtime_unchanged={zero_write_proof['mtime_unchanged']} "
        f"size_unchanged={zero_write_proof['size_unchanged']} wal_unchanged={zero_write_proof['wal_unchanged']}",
        file=sys.stderr,
    )

    iter16_readiness_hash_after = hashlib.sha256(args.iteration_16_readiness_path.read_bytes()).hexdigest()
    print(
        f"iteration-16 j11-stage-d-readiness.json hash unchanged: "
        f"{iter16_readiness_hash_before == iter16_readiness_hash_after} "
        f"(before={iter16_readiness_hash_before}, after={iter16_readiness_hash_after})",
        file=sys.stderr,
    )

    print(f"avb_classification={readiness['avb_classification']} preflight_gate_passed={readiness['preflight_gate_passed']}", file=sys.stderr)
    print(f"J-11 STAGE D READY: {'YES' if readiness['ready'] else 'NO'}", file=sys.stderr)
    print("J-11 STAGE D AUTHORIZED: NO", file=sys.stderr)
    return 0 if readiness["ready"] and iter16_readiness_hash_before == iter16_readiness_hash_after else 1


if __name__ == "__main__":
    raise SystemExit(main())
