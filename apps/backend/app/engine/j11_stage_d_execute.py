"""app.engine.j11_stage_d_execute -- J-11 Stage D EXECUTION (goal-market-compass iter-19).

`docs/goal.md`'s "OWNER RULING -- J-11 Stage D through Stage G recovery execution AUTHORIZED"
(owner, 2026-08-26) authorizes the live canonical regeneration of the 11 incident dates'
`ScannerRun`/`ScannerResult`/`SectorScoreRow`/`ThemeScoreRow` state. `j11_stage_d.py` stays
COMPLETELY UNCHANGED by this module -- it is deliberately readiness-only ("It performs NO Stage D
execution"). This module is the actual write path: it COMPOSES `j11_stage_d.py`'s already-built
identity/preflight/check functions, `j11_avb_diagnostic.py`'s classification pipeline,
`j11_preboot_guard.py`'s live guard, and `scanner.run_scan` -- never a second implementation of any
of those.

Sequence (mirrors the plan's own ordering, and `run_j11_stage_c_bounded_clear.py`'s "evidence
persisted before the destructive step" idiom):

  1. Fresh, READ-ONLY preflight -- `j11_stage_d.capture_stage_d_preflight` /
     `compare_stage_d_preflight_to_certified` / `stage_d_preflight_verdict` against the certified
     Stage-C/AVB-correction baseline, PLUS a fresh read-only AVB reclassification
     (`run_fresh_avb_reclassification`, the SAME call sequence
     `run_j11_iter17_stage_d_readiness.py` established) PLUS a fresh read-only re-verification that
     the `j11-incident-recovery` maintenance boundary is active with EXACTLY
     `j11_maintenance.INCIDENT_DATES` and the live guard blocks all of them
     (`recheck_maintenance_boundary_and_guard`). `stage_d_execution_gate_verdict` combines the three
     into the single go/no-go: proceed ONLY if the preflight comparison passes AND the AVB
     classification is EXACTLY `AVB-A` AND the boundary/guard re-check agrees -- stricter than (and
     distinct from) `j11_stage_d.stage_d_readiness_verdict`'s broader AVB-A/AVB-B "ready" concept,
     which never authorizes anything on its own.
  2. Freeze ONE fresh execution identity -- `freeze_fresh_stage_d_execution_identity` calls
     `j11_stage_d.freeze_stage_d_attempt_identity` DIRECTLY (never the `readiness_time_only`
     wrapper), immediately before the first write. `compare_identity_against_historical` reports an
     HONEST equal-or-not comparison against every historical identity value the caller supplies --
     see the module note below on why an EQUAL `engine_identity` value is an expected, non-blocking
     outcome here, not a failure.
  3. Per-date loop (`execute_stage_d_regeneration` / `execute_stage_d_for_date`) -- ascending
     chronological order over the supplied incident dates: confirm no `ScannerRun` already exists ->
     Check (B) `check_identity_before_date` -> `scanner.run_scan` called DIRECTLY (never through
     `data_manager`/`warmup`/`forward_testing`) -> Check (C) `check_identity_after_persist`. STOPS
     the WHOLE attempt at the first failing precondition/check -- no further date attempted, no
     resume-from-next-date on any retry.
  4. Post-execution mutation accounting (`build_stage_d_mutation_accounting`) -- proves
     `changed_existing_tables` is a subset of exactly `{scanner_runs, scanner_results, sector_scores,
     theme_scores}`, `next_session_manifests` is byte-unchanged, the 34 iteration-10-era
     `6261ca17...` runs and every NULL-stamped pre-stamping-era row are byte-unchanged (by a direct
     query, never by absence from a diff), and `daily_prices`/`data_provider_runs`/`watchlist`/
     `maintenance_boundaries` show zero fingerprint change.

**Why an EQUAL `engine_identity` value against the iteration-14/16/17 readiness observation is
expected, not a bug (verified empirically before this module was written, 2026-08-26):**
`engine_identity.compute_engine_identity` is a PURE function of exactly three files
(`compass.py`, `session_delta.py`, `engine_identity.py`) plus three config keys
(`compass.selection`, `compass.delta`, `compass.manifest`) -- none of which this iteration, or any
of iterations 15-18 (all J-11-only maintenance), touched; the last commit to touch `compass.py` at
all was iteration 12, already reflected in iteration 14's own frozen value. A live, independent
recomputation on this iteration's own commit reproduces `53d2ffd1...` byte-for-byte (differs
CORRECTLY from iteration 10's `6261ca17...`, which predates iteration 12's compass.py changes).
This module's Guardrails explicitly forbid touching `compass.py` to manufacture a different hash.
TC-3's own wording governs: the comparison must be "honestly compared (equal-or-not, stated either
way)" -- never silently assumed distinct, but never required to differ either. The per-run
consistency checks (A)/(B)/(C) this module relies on for safety compare the frozen identity against
itself WITHIN this one attempt, never against a historical attempt's value -- an equal
`engine_identity` carries no safety implication, since iteration 14/16/17 never wrote a single
`ScannerRun` row (readiness-only) and so never created any ambiguity in the live data.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import or_
from sqlmodel import Session, select

from app.config import Config, get_config
from app.engine import engine_identity
from app.engine import j11_avb_diagnostic as diag
from app.engine import j11_maintenance
from app.engine import j11_preboot_guard as guard
from app.engine import j11_schema_migration as migration
from app.engine import j11_stage_d as jsd
from app.engine import scanner
from app.engine.j11_maintenance import INCIDENT_DATES
from app.engine.prices import bar_cache
from app.models import MaintenanceBoundary, ScannerRun

# The five tables THIS module's one authorized write may ever touch (ruling 6: "Stage D may create
# ONLY the canonical derived state required for the eleven authorized incident dates, through the
# existing canonical scanner path"). Mirrors `j11_stage_c._CHILD_MODELS`'s table-name literal set.
STAGE_D_WRITE_TABLES: tuple[str, ...] = ("scanner_runs", "scanner_results", "sector_scores", "theme_scores")

# Same historical-fact literal `j11_stage_d.py` uses for the 34 surviving iteration-10 runs -- not a
# reusable threshold (test_no_magic_numbers.CALC_FILES excludes this module for the same reason it
# excludes every other j11_*.py file: nothing here is a scoring weight, band edge, or decision cutoff).
_LEGACY_ATTEMPT_IDENTITY_PREFIX = "6261ca17"

# The Stage D EXECUTION gate (distinct from `jsd.stage_d_readiness_verdict`'s broader "ready" concept,
# which accepts AVB-A OR AVB-B and never authorizes anything): this iteration's own What-to-Build gate
# requires the classification to be EXACTLY AVB-A.
_REQUIRED_AVB_CLASSIFICATION = "AVB-A"

# The fixed, literal AVB stored-series inspection window `run_j11_iter17_stage_d_readiness.py`
# established -- a bounded historical-evidence window for THIS incident's diagnostic, not a reusable
# threshold (same posture as `j11_avb_diagnostic.CALIBRATION_DATES`/`RECOVERED_DATES`).
_AVB_STORED_SERIES_WINDOW_START = date(2026, 6, 1)
_AVB_STORED_SERIES_WINDOW_END = date(2026, 12, 31)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ================================================================================================
# Step 1a -- fresh, read-only maintenance-boundary + live-guard re-verification
# ================================================================================================


def recheck_maintenance_boundary_and_guard(
    session: Session,
    incident_dates: tuple[date, ...] = INCIDENT_DATES,
    *,
    boundary_name: str = guard.J11_INCIDENT_BOUNDARY_NAME,
) -> dict:
    """Fresh, READ-ONLY re-verification that the named maintenance boundary is `active=1`, its
    persisted date-set is EXACTLY `incident_dates`, and the live fail-closed guard
    (`j11_preboot_guard.evaluate_boundary_for_date_fail_closed`) reports `blocked=True` for every one
    of them. Never re-arms, never disarms, never writes anything -- read-only re-verification only,
    mirroring every other J-11 precondition function's posture."""
    row = session.exec(select(MaintenanceBoundary).where(MaintenanceBoundary.name == boundary_name)).first()
    expected_dates = sorted(d.isoformat() for d in incident_dates)

    row_active = False
    persisted_dates: list[str] = []
    if row is not None:
        row_active = bool(row.active)
        try:
            parsed = json.loads(row.quarantined_dates_json)
            if isinstance(parsed, list) and all(isinstance(d, str) for d in parsed):
                persisted_dates = sorted(parsed)
        except (TypeError, ValueError, json.JSONDecodeError):
            persisted_dates = []
    exact_date_set_match = row is not None and persisted_dates == expected_dates

    per_date_guard: dict[str, dict] = {
        one_date.isoformat(): guard.evaluate_boundary_for_date_fail_closed(session, one_date)
        for one_date in incident_dates
    }
    all_dates_blocked = bool(per_date_guard) and all(r["blocked"] for r in per_date_guard.values())

    ok = row is not None and row_active and exact_date_set_match and all_dates_blocked
    return {
        "checked_at": _now_iso(),
        "boundary_name": boundary_name,
        "boundary_row_present": row is not None,
        "boundary_active": row_active,
        "persisted_dates": persisted_dates,
        "expected_dates": expected_dates,
        "exact_date_set_match": exact_date_set_match,
        "per_date_guard_result": per_date_guard,
        "all_dates_blocked": all_dates_blocked,
        "ok": ok,
    }


# ================================================================================================
# Step 1b -- fresh, read-only AVB reclassification (same call sequence as
# run_j11_iter17_stage_d_readiness.py; never a second implementation of any diag.* function)
# ================================================================================================


def run_fresh_avb_reclassification(
    session: Session,
    config: Optional[Config] = None,
    *,
    provider_fetch_evidence_path: Path,
    j10_evidence_path: Path,
) -> dict:
    """Fresh, READ-ONLY re-derivation of the AVB bridge/volume classification. Loads the
    already-committed AG-9 dated-exception-#2 provider-fetch evidence and the persisted J-10 evidence
    (never re-fetches -- AG-9 stays closed), classifies the stored local convention, traces the
    decision impact through `j11_avb_diagnostic.trace_universe_resolver_impact` /
    `trace_scoring_and_selection_impact` WITH `volume_override` on both (the SAME fix
    `run_j11_iter17_stage_d_readiness.py` applied), then `classify_avb`. Never mutates
    `daily_prices`; calls no fetch/recovery function of any kind."""
    cfg = config or get_config()
    fetch_evidence = json.loads(Path(provider_fetch_evidence_path).read_text())
    provider_evidence_by_date: dict = fetch_evidence.get("per_date", {})
    evidence_row = diag.load_j10_avb_evidence(j10_evidence_path)
    bridge_factor = evidence_row["bridge_factor"]

    volume_override: dict = {}
    for one_date in diag.RECOVERED_DATES:
        entry = provider_evidence_by_date.get(one_date.isoformat())
        if entry is not None and entry.get("volume") is not None:
            volume_override[one_date] = entry["volume"]

    stored_series = diag.fetch_avb_stored_series(
        session, _AVB_STORED_SERIES_WINDOW_START, _AVB_STORED_SERIES_WINDOW_END
    )
    local_convention = diag.classify_local_convention_with_volume_evidence(
        stored_series, evidence_row, provider_evidence_by_date
    )

    if set(volume_override) != set(diag.RECOVERED_DATES):
        # Incomplete override evidence -- fail closed to AVB-D (insufficient evidence), never guess.
        classification = {
            "classification": "AVB-D",
            "stage_d_ready_per_avb": False,
            "reasoning": (
                "volume_override does not cover both RECOVERED_DATES -- the committed provider-fetch "
                "evidence is missing volume for at least one of them; refusing to classify on "
                "incomplete override evidence"
            ),
        }
        decision_impact_by_date: dict = {}
    else:
        decision_impact_by_date = {}
        for one_date in diag.RECOVERED_DATES:
            key = one_date.isoformat()
            ur_impact = diag.trace_universe_resolver_impact(
                session, cfg, one_date, bridge_factor, volume_override=volume_override
            )
            scoring_impact = diag.trace_scoring_and_selection_impact(
                session, cfg, one_date, bridge_factor, volume_override=volume_override
            )
            decision_impact_by_date[key] = {
                "universe_resolver": ur_impact, "scoring_and_selection": scoring_impact,
            }
        classification = diag.classify_avb(local_convention, decision_impact_by_date)
        if not fetch_evidence.get("sufficient_evidence", False):
            classification = dict(classification)
            classification["classification"] = "AVB-D"
            classification["stage_d_ready_per_avb"] = False
            classification["reasoning"] = (
                "the committed AG-9 dated-exception-#2 fetch evidence does not itself report "
                "sufficient_evidence=true -- classifying AVB-D per the amendment's own fail-closed rule"
            )

    return {
        "generated_at": _now_iso(),
        "j10_evidence_path": str(j10_evidence_path),
        "provider_fetch_evidence_path": str(provider_fetch_evidence_path),
        "provider_fetch_evidence_sufficient": fetch_evidence.get("sufficient_evidence"),
        "bridge_factor": bridge_factor,
        "stored_series_window": {
            "start": _AVB_STORED_SERIES_WINDOW_START.isoformat(),
            "end": _AVB_STORED_SERIES_WINDOW_END.isoformat(),
            "row_count": len(stored_series),
        },
        "local_convention": local_convention,
        "volume_override_by_date": {d.isoformat(): v for d, v in volume_override.items()},
        "decision_impact_by_date": decision_impact_by_date,
        "classification": classification,
    }


# ================================================================================================
# Step 1c -- the combined Stage D EXECUTION gate
# ================================================================================================


def stage_d_execution_gate_verdict(*, preflight_verdict: dict, avb_classification: str, boundary_recheck: dict) -> dict:
    """The single go/no-go decision for Stage D EXECUTION -- requires the preflight comparison to
    have passed, the AVB classification to be EXACTLY `AVB-A`, and the boundary/guard re-check to
    agree. Any one failing means `proceed: False`, and the caller MUST perform zero writes."""
    preflight_ok = bool(preflight_verdict.get("passed"))
    avb_ok = avb_classification == _REQUIRED_AVB_CLASSIFICATION
    boundary_ok = bool(boundary_recheck.get("ok"))
    proceed = preflight_ok and avb_ok and boundary_ok

    blocking_reasons: list[str] = []
    if not preflight_ok:
        blocking_reasons.append(f"preflight_gate_failed:{preflight_verdict.get('reason')}")
    if not avb_ok:
        blocking_reasons.append(f"avb_classification_not_avb_a:{avb_classification}")
    if not boundary_ok:
        blocking_reasons.append("maintenance_boundary_or_guard_recheck_failed")

    return {
        "generated_at": _now_iso(),
        "proceed": proceed,
        "preflight_ok": preflight_ok,
        "avb_classification": avb_classification,
        "avb_ok": avb_ok,
        "boundary_ok": boundary_ok,
        "blocking_reasons": blocking_reasons,
    }


# ================================================================================================
# Step 2 -- freeze ONE fresh execution identity + honest historical comparison
# ================================================================================================


def freeze_fresh_stage_d_execution_identity(
    session: Session,
    config: Optional[Config] = None,
    *,
    git_head: Optional[str] = None,
    goal_md_text: Optional[str] = None,
) -> dict:
    """Freezes ONE fresh Stage D EXECUTION attempt identity, immediately before the first write --
    calls `j11_stage_d.freeze_stage_d_attempt_identity` DIRECTLY (never the `readiness_time_only`
    wrapper), per the owner ruling's item 2. A thin, explicitly-labeled call site; introduces no new
    identity-computation logic of its own."""
    frozen = jsd.freeze_stage_d_attempt_identity(session, config, git_head=git_head, goal_md_text=goal_md_text)
    return {**frozen, "execution_identity": True, "readiness_time_only": False}


def compare_identity_against_historical(fresh_engine_identity: str, historical: dict[str, Optional[str]]) -> dict:
    """Honest, per-label comparison of the fresh `engine_identity` against every historical value the
    caller supplies (e.g. `{"iteration_10": "6261ca17...", "iteration_14": "53d2ffd1...", ...}`,
    INJECTED by the caller -- this function performs no file I/O). Every comparison is stated
    explicitly, whichever way it falls (TC-3: "honestly compared (equal-or-not, stated either way)")
    -- an equal value is recorded, never silently hidden or treated as an error by this function
    itself (see the module docstring for why an equal `engine_identity` against the
    iteration-14/16/17 readiness observation is an expected, non-blocking outcome)."""
    comparisons = {
        label: {
            "historical_value": value,
            "matches_fresh": value is not None and value == fresh_engine_identity,
        }
        for label, value in historical.items()
    }
    return {
        "generated_at": _now_iso(),
        "fresh_engine_identity": fresh_engine_identity,
        "comparisons": comparisons,
        "any_historical_match": any(c["matches_fresh"] for c in comparisons.values()),
    }


# ================================================================================================
# Step 3 -- the per-date write loop (the ONE authorized write sequence)
# ================================================================================================


def confirm_no_existing_scanner_run(session: Session, one_date: date) -> dict:
    """The pre-write guard every incident date must pass before Check (B)/`run_scan`: a `ScannerRun`
    unexpectedly already existing for this date STOPS the whole attempt (the fresh preflight already
    proved zero rows at gate time -- a row appearing here means live state moved between the gate and
    this date's turn in the loop; never silently reused, never silently treated as this attempt's
    own)."""
    existing = session.exec(
        select(ScannerRun.id, ScannerRun.engine_identity).where(ScannerRun.asof_date == one_date)
    ).first()
    return {
        "date": one_date.isoformat(),
        "already_exists": existing is not None,
        "existing_run_id": int(existing[0]) if existing is not None else None,
        "existing_engine_identity": existing[1] if existing is not None else None,
    }


def execute_stage_d_for_date(session: Session, one_date: date, frozen_identity: dict, config: Config) -> dict:
    """The per-date sequence: the pre-existing-run guard -> Check (B) `check_identity_before_date` ->
    `scanner.run_scan` (called DIRECTLY -- never through `data_manager`'s backfill/ingest-finalize
    path, never through `warmup`/`forward_testing`) -> Check (C) `check_identity_after_persist`.
    Stops (`stopped: True`) at the FIRST failing precondition/check -- never proceeds past one."""
    pre_check = confirm_no_existing_scanner_run(session, one_date)
    if pre_check["already_exists"]:
        return {
            "date": one_date.isoformat(), "stopped": True,
            "stop_reason": "scanner_run_already_exists_before_write", "pre_check": pre_check,
        }

    current_identity = engine_identity.compute_engine_identity(config)
    check_b = jsd.check_identity_before_date(frozen_identity, current_identity, one_date)
    if not check_b["ok"]:
        return {
            "date": one_date.isoformat(), "stopped": True, "stop_reason": "check_b_failed",
            "pre_check": pre_check, "check_b": check_b,
        }

    run = scanner.run_scan(session, one_date, config)

    check_c = jsd.check_identity_after_persist(frozen_identity, run.engine_identity, run.id, one_date)
    if not check_c["ok"]:
        return {
            "date": one_date.isoformat(), "stopped": True, "stop_reason": "check_c_failed",
            "pre_check": pre_check, "check_b": check_b, "check_c": check_c, "run_id": run.id,
        }

    return {
        "date": one_date.isoformat(), "stopped": False, "run_id": run.id,
        "pre_check": pre_check, "check_b": check_b, "check_c": check_c,
    }


def execute_stage_d_regeneration(
    session: Session, incident_dates: tuple[date, ...], frozen_identity: dict, config: Config,
) -> dict:
    """The whole-attempt per-date loop, ascending chronological order over EVERY date in
    `incident_dates`. STOPS the ENTIRE attempt at the first failing date -- no further date
    attempted, no resume-from-next-date on any later retry (a future retry is a full Stage C->G
    restart for all eleven dates).

    Runs inside `app.engine.prices.bar_cache(session)` -- the SAME load-once cache
    `scanner._bootstrap`'s own multi-date `run_scan` loop already uses for exactly this shape of call
    ("USE ONLY around READ-ONLY multi-date snapshot loops"; this loop qualifies -- it never adds a
    price bar, only `ScannerRun`/children derived state). Each symbol's price series then loads once
    for the whole attempt instead of once per incident date -- materially less I/O/memory pressure on
    this AG-10-constrained host, and faster (directly relevant to completing within one turn)."""
    ordered_dates = sorted(incident_dates)
    per_date_results: list[dict] = []
    with bar_cache(session):
        for one_date in ordered_dates:
            result = execute_stage_d_for_date(session, one_date, frozen_identity, config)
            per_date_results.append(result)
            if result["stopped"]:
                return {
                    "generated_at": _now_iso(), "completed": False, "stopped_at_date": one_date.isoformat(),
                    "incident_dates": [d.isoformat() for d in ordered_dates],
                    "per_date_results": per_date_results,
                    "new_run_ids": [r["run_id"] for r in per_date_results if r.get("run_id") is not None],
                }
    return {
        "generated_at": _now_iso(), "completed": True, "stopped_at_date": None,
        "incident_dates": [d.isoformat() for d in ordered_dates],
        "per_date_results": per_date_results,
        "new_run_ids": [r["run_id"] for r in per_date_results],
    }


# ================================================================================================
# Step 4 -- post-execution mutation accounting
# ================================================================================================


def capture_legacy_and_null_scanner_run_fingerprint(session: Session) -> dict:
    """A full, column-projected (id, asof_date, engine_identity, created_at) snapshot of every
    `ScannerRun` row that is EITHER pre-stamping-era NULL-`engine_identity` OR stamped with iteration
    10's legacy `6261ca17...` identity prefix -- the complete population Stage D must never touch (it
    only ever INSERTs new rows for the incident dates; it issues no UPDATE of any kind). A full
    per-row list, not merely an aggregate -- ~3,117 rows is small and bounded (never a
    multi-million-row hydration -- AG-8), and the DoD explicitly requires this proven "by a direct
    query, not by absence from the diff." Column-projected only."""
    rows = session.exec(
        select(ScannerRun.id, ScannerRun.asof_date, ScannerRun.engine_identity, ScannerRun.created_at)
        .where(
            or_(
                ScannerRun.engine_identity.is_(None),
                ScannerRun.engine_identity.like(f"{_LEGACY_ATTEMPT_IDENTITY_PREFIX}%"),
            )
        )
        .order_by(ScannerRun.id)
    ).all()
    payload = [
        {
            "id": int(r[0]),
            "asof_date": r[1].isoformat() if r[1] is not None else None,
            "engine_identity": r[2],
            "created_at": r[3].isoformat() if r[3] is not None else None,
        }
        for r in rows
    ]
    null_count = sum(1 for r in payload if r["engine_identity"] is None)
    legacy_count = len(payload) - null_count
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    return {
        "captured_at": _now_iso(),
        "row_count": len(payload),
        "null_count": null_count,
        "legacy_6261ca17_count": legacy_count,
        "rows": payload,
        "fingerprint": fingerprint,
    }


def build_stage_d_mutation_accounting(
    *,
    pre_full_table_sweep: dict,
    post_full_table_sweep: dict,
    pre_manifest_dump: list,
    post_manifest_dump: list,
    pre_legacy_null_fingerprint: dict,
    post_legacy_null_fingerprint: dict,
    pre_daily_prices: dict,
    post_daily_prices: dict,
    pre_provider_runs: dict,
    post_provider_runs: dict,
    pre_watchlist: dict,
    post_watchlist: dict,
    pre_maintenance_boundary_dump: list,
    post_maintenance_boundary_dump: list,
    db_file_true_start: dict,
    db_file_true_end: dict,
) -> dict:
    """Pure composition of every pre/post capture into the DoD's mutation-accounting proof
    obligations (TC-7, TC-12, TC-13, TC-16). Takes no session/engine -- trivially fixture-tested with
    synthetic dicts, mirroring `j11_stage_c.build_mutation_accounting`'s own pure-composition idiom.
    ANY False in `checks` means `all_checks_pass` is False and the caller MUST NOT report
    `STAGE D EXECUTED: YES`."""
    checks: dict[str, Any] = {}

    table_sweep_diff = j11_maintenance.diff_full_table_sweeps(pre_full_table_sweep, post_full_table_sweep)
    checks["no_unexpected_new_tables"] = not table_sweep_diff["unexpected_new_tables"]
    checks["no_unexpected_removed_tables"] = not table_sweep_diff["unexpected_removed_tables"]
    checks["changed_tables_subset_of_stage_d_write_tables"] = set(
        table_sweep_diff["changed_existing_tables"]
    ).issubset(set(STAGE_D_WRITE_TABLES))

    manifest_diff = migration.diff_dumps(pre_manifest_dump, post_manifest_dump)
    checks["manifests_unchanged"] = manifest_diff["equal"] and len(pre_manifest_dump) == len(post_manifest_dump)

    checks["legacy_and_null_scanner_runs_unchanged"] = (
        pre_legacy_null_fingerprint["fingerprint"] == post_legacy_null_fingerprint["fingerprint"]
        and pre_legacy_null_fingerprint["rows"] == post_legacy_null_fingerprint["rows"]
    )

    checks["daily_prices_unchanged"] = pre_daily_prices["fingerprint"] == post_daily_prices["fingerprint"]
    checks["data_provider_runs_unchanged"] = pre_provider_runs == post_provider_runs
    checks["watchlist_unchanged"] = pre_watchlist == post_watchlist

    maintenance_boundary_diff = migration.diff_dumps(pre_maintenance_boundary_dump, post_maintenance_boundary_dump)
    checks["maintenance_boundary_unchanged"] = maintenance_boundary_diff["equal"]

    all_checks_pass = all(bool(v) for v in checks.values())
    return {
        "generated_at": _now_iso(),
        "checks": checks,
        "table_sweep_diff": table_sweep_diff,
        "manifest_diff": manifest_diff,
        "legacy_and_null_scanner_run_counts": {
            "pre": {
                "row_count": pre_legacy_null_fingerprint["row_count"],
                "null_count": pre_legacy_null_fingerprint["null_count"],
                "legacy_6261ca17_count": pre_legacy_null_fingerprint["legacy_6261ca17_count"],
            },
            "post": {
                "row_count": post_legacy_null_fingerprint["row_count"],
                "null_count": post_legacy_null_fingerprint["null_count"],
                "legacy_6261ca17_count": post_legacy_null_fingerprint["legacy_6261ca17_count"],
            },
        },
        "daily_prices": {"pre": pre_daily_prices, "post": post_daily_prices},
        "data_provider_runs": {"pre": pre_provider_runs, "post": post_provider_runs},
        "watchlist": {"pre": pre_watchlist, "post": post_watchlist},
        "maintenance_boundary_diff": maintenance_boundary_diff,
        "db_file": {"true_start": db_file_true_start, "true_end": db_file_true_end},
        "all_checks_pass": all_checks_pass,
    }


def stage_d_execution_outcome(
    *, execution_gate: dict, regeneration_result: Optional[dict], mutation_accounting: Optional[dict],
) -> dict:
    """The final `STAGE D EXECUTED: YES/NO` decision -- `YES` only if the gate allowed proceeding, the
    per-date loop completed every supplied date with no stop, AND the post-execution mutation
    accounting proves every check passes. Any other combination is `NO`, with the exact reason
    recorded -- never an invented third state (docs/goal.md item 14)."""
    if not execution_gate.get("proceed"):
        return {
            "executed": False, "reason": "execution_gate_did_not_proceed",
            "blocking_reasons": execution_gate.get("blocking_reasons", []),
        }
    if regeneration_result is None:
        return {"executed": False, "reason": "no_regeneration_attempted"}
    if not regeneration_result.get("completed"):
        return {
            "executed": False, "reason": "per_date_loop_stopped_early",
            "stopped_at_date": regeneration_result.get("stopped_at_date"),
        }
    if mutation_accounting is None or not mutation_accounting.get("all_checks_pass"):
        return {"executed": False, "reason": "post_execution_mutation_accounting_failed"}
    return {"executed": True, "reason": "all_incident_dates_regenerated_and_verified"}
