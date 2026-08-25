"""goal-market-compass iter-14 -- J-11 Stage D readiness tests: fresh attempt identity (TC-1), the three
fail-closed identity COMPARE checks (TC-ID-1..6), the Stage D preflight capture/comparison/verdict
(TC-8..13), and the genuinely-new Stage D-specific negative check -- unexpected incident `ScannerRun`
population (TC-19, the Stage D half; the Stage C `compare_preflight_to_certified` half lives in
`test_j11_stage_c_preflight.py`).

File-scoped, fixture-DB-only (fresh `sqlite://` engine, `SQLModel.metadata.create_all`) -- the SAME
pattern `test_j11_maintenance.py`/`test_j11_stage_c_preflight.py` use, never `loaded_engine` and never
`apps/backend/data/trendora.db`.
"""
from __future__ import annotations

import copy
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from app.config import load_config
from app.engine import j11_stage_d as jsd
from app.engine.j11_maintenance import INCIDENT_DATES
from app.models import ScannerRun

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

_NOT_AN_INCIDENT_DATE = date(2026, 1, 5)
assert _NOT_AN_INCIDENT_DATE not in INCIDENT_DATES


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


def _mk_run(
    session: Session, asof: date, *, engine_identity_value: str | None = None
) -> ScannerRun:
    run = ScannerRun(
        asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
        regime_score=55.0, regime_label="Expansion", regime_components_json="[]",
        breadth_above_50dma=50.0, breadth_above_200dma=55.0,
        new_high_low_json="{}", candidate_counts_json="{}",
        engine_identity=engine_identity_value,
    )
    session.add(run)
    session.flush()
    return run


# --- TC-1: fresh Stage D attempt identity ------------------------------------------------------------


def test_tc1_freeze_stage_d_attempt_identity_is_fresh_never_hardcoded(engine, cfg):
    with Session(engine) as session:
        identity = jsd.freeze_stage_d_attempt_identity(
            session, cfg, git_head="deadbeef", goal_md_text=_GOAL_MD_MATCHING
        )
    from app.engine.engine_identity import compute_engine_identity

    # the recorded value is whatever `compute_engine_identity` freshly computes RIGHT NOW -- proven by
    # equality with an INDEPENDENT second call, never asserted against a specific prior iteration's
    # value (iteration 10's `6261ca17...` and iteration 13's `53d2ffd1...` are both real values THIS
    # value may legitimately equal or differ from; what matters is that it is RECOMPUTED, not hardcoded
    # -- docs/goal.md J-11 step 12's 2026-08-24 clarification: "the new attempt's identity must be
    # recomputed... and recorded honestly, never hardcoded").
    assert identity["engine_identity"] == compute_engine_identity(cfg)
    assert not identity["engine_identity"].startswith("6261ca17")  # never FORCED onto the earlier attempt's value
    assert identity["incident_dates"] == [d.isoformat() for d in INCIDENT_DATES]
    assert identity["git_head"] == "deadbeef"
    assert "config_subset_hash" in identity and "config_subset" in identity
    assert "provenance" in identity and "engine_files" in identity["provenance"]
    assert "6261ca17" in identity["scope_note"]
    assert "NOT members of this attempt" in identity["scope_note"]


def test_freeze_stage_d_attempt_identity_reproducible_from_same_config(engine, cfg):
    with Session(engine) as session:
        first = jsd.freeze_stage_d_attempt_identity(session, cfg, git_head="a", goal_md_text=_GOAL_MD_MATCHING)
        second = jsd.freeze_stage_d_attempt_identity(session, cfg, git_head="a", goal_md_text=_GOAL_MD_MATCHING)
    assert first["engine_identity"] == second["engine_identity"]
    assert first["config_subset_hash"] == second["config_subset_hash"]
    assert first["attempt_id"] != second["attempt_id"]  # each freeze mints its OWN attempt id


# --- TC-ID-1/2: Check (A) -- before the first write -----------------------------------------------


def test_tc_id_1_check_a_passes_on_matching_identity():
    frozen = {"engine_identity": "A"}
    result = jsd.check_identity_before_first_write(frozen, "A")
    assert result["ok"] is True
    assert result["check"] == "before_first_write"


def test_tc_id_2_check_a_fails_closed_on_drift_before_first_write():
    frozen = {"engine_identity": "A"}
    result = jsd.check_identity_before_first_write(frozen, "B")
    assert result["ok"] is False
    # the bare-string frozen-identity form is accepted identically to the dict form
    result_bare = jsd.check_identity_before_first_write("A", "B")
    assert result_bare["ok"] is False


# --- TC-ID-3: Check (B) -- before a subsequent date, drift stops the attempt before that date --------


def test_tc_id_3_check_b_passes_on_matching_then_fails_closed_on_drift():
    frozen = {"engine_identity": "A"}
    date1, date2 = INCIDENT_DATES[0], INCIDENT_DATES[1]
    result_date1 = jsd.check_identity_before_date(frozen, "A", date1)
    assert result_date1["ok"] is True and result_date1["in_scope"] is True

    result_date2 = jsd.check_identity_before_date(frozen, "B", date2)
    assert result_date2["ok"] is False and result_date2["in_scope"] is True
    assert result_date2["date"] == date2.isoformat()


# --- TC-ID-4/5: Check (C) -- after persistence, NULL or mismatched is failure -----------------------


def test_tc_id_4_check_c_fails_on_null_persisted_identity():
    frozen = {"engine_identity": "A"}
    result = jsd.check_identity_after_persist(frozen, None, run_id=42, one_date=INCIDENT_DATES[0])
    assert result["ok"] is False
    assert result["in_scope"] is True


def test_tc_id_5_check_c_fails_on_mismatched_persisted_identity():
    frozen = {"engine_identity": "A"}
    result = jsd.check_identity_after_persist(frozen, "B", run_id=42, one_date=INCIDENT_DATES[0])
    assert result["ok"] is False


def test_check_c_passes_on_matching_persisted_identity():
    frozen = {"engine_identity": "A"}
    result = jsd.check_identity_after_persist(frozen, "A", run_id=42, one_date=INCIDENT_DATES[0])
    assert result["ok"] is True


# --- TC-ID-6: the 34 surviving out-of-scope runs -- no failure, no mutation, vacuous pass -----------


def test_tc_id_6_out_of_scope_date_never_raises_a_failure_regardless_of_identity_mismatch():
    frozen = {"engine_identity": "A"}
    # a surviving run stamped an EARLIER attempt's identity ("6261ca17...") on a date that is NOT one of
    # this attempt's 11 incident dates -- exactly the 34 surviving runs' shape.
    result_b = jsd.check_identity_before_date(frozen, "6261ca17-earlier-attempt", _NOT_AN_INCIDENT_DATE)
    assert result_b["ok"] is True
    assert result_b["in_scope"] is False
    assert "outside_j11_stage_d_attempt_scope" in result_b["reason"]

    result_c = jsd.check_identity_after_persist(
        frozen, "6261ca17-earlier-attempt", run_id=999, one_date=_NOT_AN_INCIDENT_DATE
    )
    assert result_c["ok"] is True
    assert result_c["in_scope"] is False

    # Check (A) never even reads a run's stamped identity at all (its inputs are frozen/current computed
    # values, never a ScannerRun row) -- so it structurally can never be affected by the 34 survivors'
    # stamps either, confirming no code path in this module ever compares against them.
    result_a = jsd.check_identity_before_first_write(frozen, "A")
    assert result_a["ok"] is True


# --- TC-8..13: the Stage D preflight capture + comparison gate + verdict, fixture-DB shape ----------


def _fresh_preflight(engine, cfg):
    with Session(engine) as session:
        return jsd.capture_stage_d_preflight(
            session, engine, None, goal_md_text=_GOAL_MD_MATCHING, git_head="deadbeef", config=cfg,
        )


def test_tc8_preflight_reports_zero_scanner_runs_on_all_11_incident_dates_when_empty(engine, cfg):
    preflight = _fresh_preflight(engine, cfg)
    per_date = preflight["pre_reset_inventory"]["per_date"]
    assert set(per_date) == {d.isoformat() for d in INCIDENT_DATES}
    assert all(not per_date[key]["scanner_run"]["present"] for key in per_date)


def test_tc9_and_tc10_preflight_capture_shape_includes_manifest_and_prices(engine, cfg):
    preflight = _fresh_preflight(engine, cfg)
    assert preflight["manifest_row_count"] == 0  # empty fixture DB
    assert "table_sql" in preflight["manifest_ddl"]
    assert preflight["pre_reset_inventory"]["daily_prices"]["row_count"] == 0


def test_tc11_check_a_passes_against_the_freshly_frozen_identity(engine, cfg):
    preflight = _fresh_preflight(engine, cfg)
    assert preflight["identity_check_a"]["ok"] is True
    assert preflight["identity_check_a"]["current_engine_identity"] == preflight["attempt_identity"]["engine_identity"]


def test_tc12_c1_date_set_boundary_matches_goal_md(engine, cfg):
    preflight = _fresh_preflight(engine, cfg)
    assert preflight["c1_date_set_boundary_check"]["ok"] is True


def test_tc13_maintenance_isolation_env_recorded_verbatim(engine, cfg, monkeypatch):
    monkeypatch.setenv("CHAIN_MAINTENANCE_ISOLATION", "required")
    preflight = _fresh_preflight(engine, cfg)
    assert preflight["maintenance_isolation_env"] == {"present": True, "value": "required"}

    monkeypatch.delenv("CHAIN_MAINTENANCE_ISOLATION", raising=False)
    preflight_absent = _fresh_preflight(engine, cfg)
    assert preflight_absent["maintenance_isolation_env"] == {"present": False, "value": None}


# --- the comparison gate against a certified baseline -------------------------------------------------


def _certified_from(preflight: dict) -> dict:
    """A certified-baseline dict in `load_stage_d_certified_baseline`'s OWN return shape, built as a
    self-diff of a fresh preflight (an unchanged database) -- mirrors
    `test_j11_stage_c_preflight.py`'s `test_tc2_comparison_gate_passes_when_certified_state_matches_
    fresh_state` pattern."""
    return {
        "daily_prices_fingerprint": preflight["pre_reset_inventory"]["daily_prices"]["fingerprint"],
        "manifest_row_count": preflight["manifest_row_count"],
        "manifest_ddl": copy.deepcopy(preflight["manifest_ddl"]),
        "manifest_dump": copy.deepcopy(preflight["manifest_dump"]),
        "data_provider_runs_count": preflight["pre_reset_inventory"]["data_provider_runs_count"],
        "watchlist_count": preflight["pre_reset_inventory"]["watchlist_count"],
    }


def test_gate_passes_when_certified_state_matches_fresh_state(engine, cfg):
    preflight = _fresh_preflight(engine, cfg)
    certified = _certified_from(preflight)
    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
    assert gate["all_invariants_hold"] is True
    assert gate["material_mismatch"] is False
    verdict = jsd.stage_d_preflight_verdict(gate)
    assert verdict["passed"] is True


def test_gate_stops_on_daily_prices_fingerprint_drift(engine, cfg):
    preflight = _fresh_preflight(engine, cfg)
    certified = _certified_from(preflight)
    certified["daily_prices_fingerprint"] = "a-different-fingerprint"
    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
    assert gate["all_invariants_hold"] is False
    assert gate["checks"]["daily_prices_fingerprint_unchanged"] is False
    verdict = jsd.stage_d_preflight_verdict(gate)
    assert verdict["passed"] is False
    assert "daily_prices_fingerprint_unchanged" in verdict["failing_checks"]


# --- TC-19 (Stage D half): unexpected incident ScannerRun population -> refusal ---------------------


def test_tc19_unexpected_incident_scanner_run_population_refuses(engine, cfg):
    with Session(engine) as session:
        _mk_run(session, INCIDENT_DATES[0])  # a ScannerRun exists where the Stage D precondition
        session.commit()                     # requires zero -- the boot-warmup-race / retry-collision shape

    preflight = _fresh_preflight(engine, cfg)
    certified = _certified_from(preflight)
    # the certified baseline expects the ORIGINAL (empty) per-date state; compare_stage_d_preflight_to_
    # certified derives its own "all_incident_dates_zero_scanner_runs" check straight from the FRESH
    # preflight's own per_date inventory, so an unexpected run is caught without needing a certified-side
    # per-date field at all.
    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
    assert gate["checks"]["all_incident_dates_zero_scanner_runs"] is False
    assert gate["material_mismatch"] is True
    verdict = jsd.stage_d_preflight_verdict(gate)
    assert verdict["passed"] is False


def test_scanner_run_on_a_non_incident_date_does_not_trip_the_zero_runs_check(engine, cfg):
    with Session(engine) as session:
        _mk_run(session, _NOT_AN_INCIDENT_DATE, engine_identity_value="6261ca17-earlier-attempt")
        session.commit()

    preflight = _fresh_preflight(engine, cfg)
    certified = _certified_from(preflight)
    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
    assert gate["checks"]["all_incident_dates_zero_scanner_runs"] is True


# --- Goal 5: the readiness verdict -- AVB-C/D forces NO regardless of the preflight gate (TC-25) ------


@pytest.mark.parametrize(
    "avb_classification,preflight_passed,expected_ready",
    [
        ("AVB-A", True, True),
        ("AVB-B", True, True),
        ("AVB-A", False, False),
        ("AVB-C", True, False),
        ("AVB-D", True, False),
        ("AVB-C", False, False),
    ],
)
def test_tc25_readiness_verdict_combines_preflight_and_avb_classification(
    avb_classification, preflight_passed, expected_ready
):
    preflight_verdict = {"passed": preflight_passed, "reason": "x"}
    readiness = jsd.stage_d_readiness_verdict(preflight_verdict, avb_classification)
    assert readiness["ready"] is expected_ready
    assert readiness["authorized"] is False  # unconditional, per every parametrized case


def test_readiness_verdict_rejects_unknown_avb_classification():
    with pytest.raises(ValueError):
        jsd.stage_d_readiness_verdict({"passed": True, "reason": "x"}, "AVB-Z")
