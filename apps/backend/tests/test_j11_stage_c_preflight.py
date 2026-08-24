"""goal-market-compass iter-13 -- J-11 Stage C preflight/gate/completion-marker tests (TC-1, TC-2, TC-3,
TC-13).

File-scoped, fixture-DB-only (fresh `sqlite://` engine, `SQLModel.metadata.create_all`) plus pure-dict
unit tests for the comparison gate / C1 check / completion-marker helpers -- never
`apps/backend/data/trendora.db`.
"""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from app.config import load_config
from app.engine import j11_stage_c as jsc
from app.engine.j11_maintenance import INCIDENT_DATES

# A minimal but well-formed synthetic goal.md excerpt reproducing the J-11 section's two literal anchors
# and both 11-date lists, standing in for the real (much larger) `docs/goal.md` file. Kept structurally
# identical to the real anchors so the extraction functions are exercised exactly as they run live.
_MATCHING_DATES = ", ".join(d.isoformat() for d in INCIDENT_DATES)
_GOAL_MD_MATCHING = f"""
# Project Goal

- **J-10: some other journey** — passing

- **J-11: Incident-bounded clean regeneration of derived state (owner, 2026-08-21)**
  - **The incident date set — all 11, not the 8 currently absent.** From the authoritative removal
    audit (`data_provider_runs` id=538, whose own cascade record lists them):
    `{_MATCHING_DATES}`.
  - Steps:
    1. some step text
       ## OWNER AUTHORIZATION — J-11 Stage C (owner, 2026-08-24)
       - **C1 — Date-set boundary.** For the avoidance
         of doubt they are `{_MATCHING_DATES}`.
  - Acceptance: some acceptance text

<!-- Continuous-improvement auto-journeys: appended below -->
"""

_DISAGREEING_DATES = ", ".join(d.isoformat() for d in INCIDENT_DATES[:-1]) + ", 2099-01-01"
_GOAL_MD_DISAGREEING = _GOAL_MD_MATCHING.replace(
    f"of doubt they are `{_MATCHING_DATES}`.",
    f"of doubt they are `{_DISAGREEING_DATES}`.",
)

_GOAL_MD_MISSING_C1 = _GOAL_MD_MATCHING.replace("For the avoidance\n         of doubt they are", "no such phrase here")


# --- TC-3: the C1 date-set boundary check ---------------------------------------------------------


def test_tc3_c1_boundary_matching_lists_pass():
    check = jsc.check_c1_date_set_boundary(_GOAL_MD_MATCHING)
    assert check["ok"] is True
    assert check["lists_agree"] is True
    assert check["code_matches_goal_md_lists"] is True
    assert check["code_dates"] == [d.isoformat() for d in INCIDENT_DATES]


def test_tc3_c1_boundary_disagreeing_lists_stop():
    check = jsc.check_c1_date_set_boundary(_GOAL_MD_DISAGREEING)
    assert check["ok"] is False
    assert check["lists_agree"] is False
    assert check["authoritative_bullet_dates"] != check["c1_restatement_dates"]


def test_tc3_c1_boundary_missing_anchor_stops_not_guesses():
    check = jsc.check_c1_date_set_boundary(_GOAL_MD_MISSING_C1)
    assert check["ok"] is False
    assert "extraction_error" in check


def test_contract_hash_extraction_bounded_to_j11_section():
    section = jsc.extract_j11_contract_text(_GOAL_MD_MATCHING)
    assert section.startswith("- **J-11:")
    assert "J-10: some other journey" not in section
    assert "Continuous-improvement auto-journeys" not in section
    # deterministic / reproducible
    assert jsc.compute_contract_hash(_GOAL_MD_MATCHING) == jsc.compute_contract_hash(_GOAL_MD_MATCHING)


def test_contract_text_missing_start_anchor_raises():
    with pytest.raises(ValueError):
        jsc.extract_j11_contract_text("no J-11 heading anywhere in this text")


# --- TC-1: fresh Stage C preflight capture, fixture-DB shape ---------------------------------------


@pytest.fixture()
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})

    @event.listens_for(eng, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture()
def cfg():
    return load_config()


def test_tc1_preflight_capture_shape(engine, cfg):
    with Session(engine) as session:
        preflight = jsc.capture_stage_c_preflight(
            session, engine, None,
            goal_md_text=_GOAL_MD_MATCHING, git_head="deadbeef", config=cfg,
        )
    assert preflight["git_head"] == "deadbeef"
    assert preflight["manifest_row_count"] == 0  # empty fixture DB
    assert preflight["c1_date_set_boundary_check"]["ok"] is True
    assert "engine_identity" in preflight["stage_c_attempt_identity"]["b2_engine_identity"]
    assert preflight["pre_reset_inventory"]["daily_prices"]["row_count"] == 0
    assert set(preflight["pre_reset_inventory"]["per_date"]) == {d.isoformat() for d in INCIDENT_DATES}
    assert "table_sql" in preflight["manifest_ddl"]
    assert "tables" in preflight["full_db_snapshot"]


# --- TC-2: the preflight comparison gate ------------------------------------------------------------


def _fresh_preflight(engine, cfg):
    with Session(engine) as session:
        return jsc.capture_stage_c_preflight(
            session, engine, None,
            goal_md_text=_GOAL_MD_MATCHING, git_head="deadbeef", config=cfg,
        )


def test_tc2_comparison_gate_passes_when_certified_state_matches_fresh_state(engine, cfg):
    preflight = _fresh_preflight(engine, cfg)
    # the certified baseline IS the fresh preflight's own shape (an unchanged database) -- a self-diff.
    certified = copy.deepcopy(preflight)
    gate = jsc.compare_preflight_to_certified(preflight, certified)
    assert gate["all_invariants_hold"] is True
    assert gate["material_mismatch"] is False
    assert all(gate["checks"].values())


def test_tc2_comparison_gate_stops_on_material_mismatch_manifest_row_count(engine, cfg):
    preflight = _fresh_preflight(engine, cfg)
    certified = copy.deepcopy(preflight)
    # simulate the certified baseline recording 24 manifest rows while the fresh read finds a different
    # count -- a materially-differs-from-certified-state case (TC-2's own worked example).
    certified["manifest_row_count"] = 24
    gate = jsc.compare_preflight_to_certified(preflight, certified)
    assert gate["all_invariants_hold"] is False
    assert gate["material_mismatch"] is True
    assert gate["checks"]["manifest_row_count_matches_certified"] is False


def test_tc2_comparison_gate_stops_on_per_date_scanner_run_drift(engine, cfg):
    preflight = _fresh_preflight(engine, cfg)
    certified = copy.deepcopy(preflight)
    # certified state claims a run existed on an incident date that the fresh read found absent --
    # exactly the "live state materially differs from the certified iteration-12 state" trap C2 exists
    # to catch.
    a_date_key = INCIDENT_DATES[0].isoformat()
    certified["pre_reset_inventory"]["per_date"][a_date_key]["scanner_run"] = {
        "present": True, "run_id": 999, "created_at": "2026-01-01T00:00:00+00:00", "engine_identity": "x",
    }
    gate = jsc.compare_preflight_to_certified(preflight, certified)
    assert gate["all_invariants_hold"] is False
    assert gate["checks"]["per_date_scanner_run_inventory_unchanged"] is False
    assert gate["per_date_scanner_run_mismatches"]


# --- TC-13: completion-marker gating -----------------------------------------------------------------


def test_tc13_overall_verdict_fails_when_preflight_gate_fails():
    verdict = jsc.stage_c_overall_verdict({"all_invariants_hold": False}, mutation_accounting=None)
    assert verdict["passed"] is False
    assert verdict["reason"] == "preflight_comparison_gate_failed"


def test_tc13_overall_verdict_fails_when_no_mutation_accounting_captured():
    verdict = jsc.stage_c_overall_verdict({"all_invariants_hold": True}, mutation_accounting=None)
    assert verdict["passed"] is False
    assert verdict["reason"] == "no_mutation_accounting_captured"


def test_tc13_overall_verdict_fails_when_post_delete_verification_fails():
    verdict = jsc.stage_c_overall_verdict(
        {"all_invariants_hold": True}, mutation_accounting={"all_checks_pass": False}
    )
    assert verdict["passed"] is False
    assert verdict["reason"] == "post_delete_verification_failed"


def test_tc13_overall_verdict_passes_when_everything_holds():
    verdict = jsc.stage_c_overall_verdict(
        {"all_invariants_hold": True}, mutation_accounting={"all_checks_pass": True}
    )
    assert verdict["passed"] is True


def test_tc13_build_completion_marker_refuses_on_failing_verdict():
    with pytest.raises(RuntimeError):
        jsc.build_completion_marker({"passed": False, "reason": "x"}, prior_artifact_timestamps=[])


def test_tc13_build_completion_marker_timestamp_strictly_after_prior_artifacts():
    earlier = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
    marker = jsc.build_completion_marker({"passed": True, "reason": "all_checks_passed"}, prior_artifact_timestamps=[earlier])
    assert marker["j11_stage_c_complete"] is True
    completed_at = datetime.fromisoformat(marker["completed_at"])
    assert completed_at > datetime.fromisoformat(earlier)


def test_tc13_build_completion_marker_rejects_a_future_prior_timestamp_defensively():
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    with pytest.raises(RuntimeError):
        jsc.build_completion_marker({"passed": True, "reason": "x"}, prior_artifact_timestamps=[future])
