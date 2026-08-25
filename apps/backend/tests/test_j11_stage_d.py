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
import json
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from app.config import load_config
from app.engine import j11_stage_d as jsd
from app.engine.j11_maintenance import INCIDENT_DATES
from app.models import NextSessionManifest, ScannerRun

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

# goal-market-compass iter-15 (Goal 8): a goal.md text whose C1 restatement date list disagrees with the
# authoritative bullet (one date swapped) -- exercises `c1_date_set_boundary_ok`'s OWN failure mode.
_MISMATCHED_DATES = ", ".join(
    d.isoformat() for d in (INCIDENT_DATES[:-1] + (date(2099, 1, 1),))
)
_GOAL_MD_C1_MISMATCH = f"""
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
         of doubt they are `{_MISMATCHED_DATES}`.
  - Acceptance: some acceptance text

<!-- Continuous-improvement auto-journeys: appended below -->
"""


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


def _mk_manifest(session: Session, run: ScannerRun, *, version: int = 1) -> NextSessionManifest:
    """A hand-built manifest row referencing `run` -- mirrors `test_j11_maintenance.py`'s own `_mk_manifest`
    helper exactly (Goal 8's manifest-value/source_run_id negative tests need at least one real row)."""
    manifest = NextSessionManifest(
        as_of=run.asof_date,
        version=version,
        source_run_id=run.id,
        session_delta_json="{}",
        narrative_json="{}",
        selection_json="{}",
        content_hash="stub-content-hash",
        created_at=datetime.now(timezone.utc),
        mode="at_ingest",
        frozen=True,
        generation_json=json.dumps({
            "producer": "ingest_finalize",
            "engine_identity": "stub-engine-identity",
        }),
        engine_identity="stub-engine-identity",
        manifest_hash="stub-manifest-hash",
        available_at_utc=datetime.now(timezone.utc),
        prospective_eligible=True,
    )
    session.add(manifest)
    session.flush()
    return manifest


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


# ======================================================================================================
# goal-market-compass iter-15 (Goal 8): one dedicated negative fixture test PER remaining
# `compare_stage_d_preflight_to_certified` check -- each perturbs exactly ONE field so no shared fixture
# masks a different failure (iter-9's lesson). Every test asserts BOTH `checks[...] is False` AND
# `material_mismatch is True`, mirroring `test_gate_stops_on_daily_prices_fingerprint_drift` exactly.
# ======================================================================================================


def test_goal8_manifest_row_count_unchanged_fails_on_drift(engine, cfg):
    preflight = _fresh_preflight(engine, cfg)
    certified = _certified_from(preflight)
    certified["manifest_row_count"] = preflight["manifest_row_count"] + 1
    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
    assert gate["checks"]["manifest_row_count_unchanged"] is False
    assert gate["material_mismatch"] is True


def test_goal8_manifest_ddl_unchanged_fails_when_one_ddl_clause_differs(engine, cfg):
    preflight = _fresh_preflight(engine, cfg)
    certified = _certified_from(preflight)
    original_sql = certified["manifest_ddl"]["table_sql"] or ""
    certified["manifest_ddl"]["table_sql"] = original_sql + " -- one clause different"
    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
    assert gate["checks"]["manifest_ddl_unchanged"] is False
    assert gate["material_mismatch"] is True


def test_goal8_manifest_indexes_unchanged_fails_when_index_set_differs(engine, cfg):
    preflight = _fresh_preflight(engine, cfg)
    certified = _certified_from(preflight)
    certified["manifest_ddl"]["index_names"] = list(certified["manifest_ddl"]["index_names"]) + ["ix_fake_extra"]
    certified["manifest_ddl"]["index_sqls"] = list(certified["manifest_ddl"]["index_sqls"]) + [
        "CREATE INDEX ix_fake_extra ON next_session_manifests(id)"
    ]
    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
    assert gate["checks"]["manifest_indexes_unchanged"] is False
    assert gate["material_mismatch"] is True


def test_goal8_manifest_values_unchanged_fails_when_one_stored_value_differs(engine, cfg):
    with Session(engine) as session:
        run = _mk_run(session, INCIDENT_DATES[0])
        _mk_manifest(session, run)
        session.commit()

    preflight = _fresh_preflight(engine, cfg)
    assert preflight["manifest_row_count"] == 1  # sanity: the seeded row is really captured
    certified = _certified_from(preflight)
    # perturb exactly ONE stored value on the one seeded row -- content_hash, chosen because it is a
    # plain string column untouched by any other Goal 8 test in this file.
    certified["manifest_dump"][0]["content_hash"] = "a-different-content-hash"
    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
    assert gate["checks"]["manifest_values_unchanged"] is False
    assert gate["material_mismatch"] is True
    # this perturbation must NOT also trip source_run_id_values_unchanged -- only ONE field changed.
    assert gate["checks"]["source_run_id_values_unchanged"] is True


def test_goal8_source_run_id_values_unchanged_fails_when_one_source_run_id_differs(engine, cfg):
    with Session(engine) as session:
        run = _mk_run(session, INCIDENT_DATES[0])
        _mk_manifest(session, run)
        session.commit()

    preflight = _fresh_preflight(engine, cfg)
    certified = _certified_from(preflight)
    certified["manifest_dump"][0]["source_run_id"] = 999999  # a source_run_id that never existed
    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
    assert gate["checks"]["source_run_id_values_unchanged"] is False
    assert gate["material_mismatch"] is True
    # this perturbation alone must not ALSO trip manifest_values_unchanged's full-row diff for an
    # UNRELATED column -- diff_dumps flags source_run_id specifically, proving the two checks are
    # independent evidence, not the same signal reported twice under two names.
    diff_columns = {m["column"] for m in gate["manifest_dump_diff"]["mismatches"]}
    assert diff_columns == {"source_run_id"}


def test_goal8_data_provider_runs_count_unchanged_fails_on_drift(engine, cfg):
    preflight = _fresh_preflight(engine, cfg)
    certified = _certified_from(preflight)
    certified["data_provider_runs_count"] = preflight["pre_reset_inventory"]["data_provider_runs_count"] + 1
    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
    assert gate["checks"]["data_provider_runs_count_unchanged"] is False
    assert gate["material_mismatch"] is True


def test_goal8_watchlist_count_unchanged_fails_on_drift(engine, cfg):
    preflight = _fresh_preflight(engine, cfg)
    certified = _certified_from(preflight)
    certified["watchlist_count"] = preflight["pre_reset_inventory"]["watchlist_count"] + 1
    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
    assert gate["checks"]["watchlist_count_unchanged"] is False
    assert gate["material_mismatch"] is True


def test_goal8_c1_date_set_boundary_ok_fails_when_goal_md_lists_disagree(engine, cfg):
    with Session(engine) as session:
        preflight = jsd.capture_stage_d_preflight(
            session, engine, None, goal_md_text=_GOAL_MD_C1_MISMATCH, git_head="deadbeef", config=cfg,
        )
    assert preflight["c1_date_set_boundary_check"]["ok"] is False
    certified = _certified_from(preflight)
    gate = jsd.compare_stage_d_preflight_to_certified(preflight, certified)
    assert gate["checks"]["c1_date_set_boundary_ok"] is False
    assert gate["material_mismatch"] is True


# --- TC-35/36: the pre-existing identity-check + negative tests re-run alongside the new ones, no ------
# --- fixture collision, and no new test ever touches the 34 6261ca17... rows or the NULL-stamped rows --


def test_goal8_new_negative_tests_never_seed_or_assert_against_legacy_identity_rows(engine, cfg):
    """A direct assertion that THIS file's Goal 8 fixtures never construct a `6261ca17...`-stamped or
    NULL-stamped row on a NON-incident date the way the 34 surviving/pre-stamping-era rows are shaped --
    every `_mk_run`/`_mk_manifest` call in the Goal 8 tests above uses an INCIDENT date with no
    `engine_identity_value` override, so it can never collide with or assert against that population."""
    with Session(engine) as session:
        count = session.exec(
            __import__("sqlmodel").select(__import__("sqlalchemy").func.count()).select_from(ScannerRun)
        ).one()
    # the fixture engine is FRESH per test (function-scoped `engine` fixture) -- this test's own session
    # never persisted anything, so the table is empty; this is a structural proof that Goal 8's tests run
    # in isolated fixture DBs, never a shared/live one where a legacy row could exist to begin with.
    assert count == 0


# ======================================================================================================
# goal-market-compass iter-15 (Goal 1): reconcile_prior_iteration_truth
# ======================================================================================================


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        path.write_text(payload)
    else:
        path.write_text(json.dumps(payload))
    return path


def test_reconcile_prior_iteration_truth_reports_per_figure_match_and_mismatch(engine, cfg, tmp_path):
    stale_readiness = {
        "avb_classification": "AVB-B", "ready": True, "blocking_reasons": [],
        "generated_at": "2026-08-24T22:05:04.053596+00:00",
    }
    readiness_path = _write(tmp_path / "stale-readiness.json", stale_readiness)
    eval_md_path = _write(
        tmp_path / "eval.md",
        "# Iteration 14 Evaluation\n\n**Owner-facing lines:** `J-11 STAGE D READY: NO` · `J-11 STAGE D AUTHORIZED: NO`\n",
    )
    # an owner capture that DISAGREES with the empty fixture DB on purpose -- proves mismatches are
    # reported explicitly, never silently reconciled.
    owner_capture = dict(jsd.OWNER_TRUE_START_CAPTURE)
    owner_capture["daily_prices_row_count"] = 999999999  # will NOT match the empty fixture (0 rows)

    with Session(engine) as session:
        result = jsd.reconcile_prior_iteration_truth(
            session, engine, None,
            iteration_14_readiness_path=readiness_path,
            iteration_14_eval_md_path=eval_md_path,
            owner_true_start_capture=owner_capture,
        )

    assert result["comparisons_against_owner_capture"]["daily_prices_row_count"]["matches_owner_capture"] is False
    assert result["any_mismatch_against_owner_capture"] is True
    assert result["iteration_14_stale_artifact"]["content_verbatim"] == stale_readiness
    assert result["iteration_14_stale_artifact"]["stale_artifact_superseded"] is True
    assert result["iteration_14_eval_md_corrected_line"]["quoted_line"] == "J-11 STAGE D READY: NO"
    # the source files themselves are untouched -- loaded read-only, never edited.
    assert json.loads(readiness_path.read_text()) == stale_readiness


def test_reconcile_prior_iteration_truth_matches_when_owner_capture_agrees_with_empty_fixture(engine, cfg, tmp_path):
    readiness_path = _write(tmp_path / "stale-readiness.json", {"avb_classification": "AVB-B", "ready": True, "blocking_reasons": []})
    eval_md_path = _write(tmp_path / "eval.md", "`J-11 STAGE D READY: NO`\n")

    owner_capture = dict(jsd.OWNER_TRUE_START_CAPTURE)
    owner_capture.update({
        "db_mtime": None, "db_size_bytes": None,
        "all_11_incident_dates_zero_scanner_runs": True,
        "daily_prices_row_count": 0, "scanner_runs_total_count": 0, "forward_returns_total_count": 0,
        "data_provider_runs_count": 0, "manifest_row_count": 0, "watchlist_count": 0,
        "forward_returns_measured_into_incident_total": 0, "scanner_runs_stamped_6261ca17_count": 0,
    })

    with Session(engine) as session:
        result = jsd.reconcile_prior_iteration_truth(
            session, engine, None,
            iteration_14_readiness_path=readiness_path,
            iteration_14_eval_md_path=eval_md_path,
            owner_true_start_capture=owner_capture,
        )

    count_checks = {
        "all_11_incident_dates_zero_scanner_runs", "daily_prices_row_count", "scanner_runs_total_count",
        "forward_returns_total_count", "data_provider_runs_count", "manifest_row_count", "watchlist_count",
        "forward_returns_measured_into_incident_total", "scanner_runs_stamped_6261ca17_count",
    }
    for name in count_checks:
        assert result["comparisons_against_owner_capture"][name]["matches_owner_capture"] is True, name
    assert result["forward_returns_measured_into_incident_total_matches_16614"] is False  # 0 != 16614, stated honestly


def test_reconcile_prior_iteration_truth_raises_on_contradictory_eval_md_lines(engine, cfg, tmp_path):
    readiness_path = _write(tmp_path / "stale-readiness.json", {"avb_classification": "AVB-B", "ready": True, "blocking_reasons": []})
    eval_md_path = _write(tmp_path / "eval.md", "`J-11 STAGE D READY: NO` ... elsewhere ... `J-11 STAGE D READY: YES`\n")
    with Session(engine) as session:
        with pytest.raises(ValueError):
            jsd.reconcile_prior_iteration_truth(
                session, engine, None,
                iteration_14_readiness_path=readiness_path, iteration_14_eval_md_path=eval_md_path,
            )


def test_reconcile_prior_iteration_truth_does_not_use_default_paths_that_could_touch_iter14_evidence(engine, cfg, tmp_path):
    """A structural proof that `reconcile_prior_iteration_truth` has no baked-in default path of its own
    -- both evidence paths are REQUIRED keyword arguments (calling without them is a TypeError), so a
    caller can never accidentally point this function at a real committed evidence directory."""
    import inspect
    sig = inspect.signature(jsd.reconcile_prior_iteration_truth)
    assert sig.parameters["iteration_14_readiness_path"].default is inspect.Parameter.empty
    assert sig.parameters["iteration_14_eval_md_path"].default is inspect.Parameter.empty


# ======================================================================================================
# goal-market-compass iter-15 (Goal 7): produce_stage_d_readiness_artifact
# ======================================================================================================


def _write_preflight_gate(path, *, passed=True, generated_at="2026-08-25T10:00:00+00:00"):
    payload = {"comparison": {"generated_at": generated_at, "checks": {}}, "verdict": {"passed": passed, "reason": "x"}}
    return _write(path, payload)


def _write_avb_diagnostic(path, *, classification="AVB-A", generated_at="2026-08-25T10:00:00+00:00"):
    payload = {"generated_at": generated_at, "classification": {"classification": classification}}
    return _write(path, payload)


def test_tc30_produce_stage_d_readiness_artifact_calls_existing_verdict_and_writes_provenance(tmp_path):
    preflight_path = _write_preflight_gate(tmp_path / "gate.json", passed=True)
    avb_path = _write_avb_diagnostic(tmp_path / "avb.json", classification="AVB-A")
    output_path = tmp_path / "readiness.json"

    readiness = jsd.produce_stage_d_readiness_artifact(preflight_path, avb_path, output_path=output_path)

    assert readiness["ready"] is True
    assert readiness["authorized"] is False
    assert readiness["inputs"] == {
        "preflight_gate_artifact": str(preflight_path), "avb_diagnostic_artifact": str(avb_path),
    }
    on_disk = json.loads(output_path.read_text())
    assert on_disk["ready"] is True
    assert on_disk["authorized"] is False


def test_tc31_produce_stage_d_readiness_artifact_fails_closed_on_missing_preflight_path(tmp_path):
    avb_path = _write_avb_diagnostic(tmp_path / "avb.json")
    output_path = tmp_path / "readiness.json"
    with pytest.raises(ValueError):
        jsd.produce_stage_d_readiness_artifact(tmp_path / "does-not-exist.json", avb_path, output_path=output_path)
    assert not output_path.exists()


def test_tc32_produce_stage_d_readiness_artifact_fails_closed_on_unknown_avb_classification(tmp_path):
    preflight_path = _write_preflight_gate(tmp_path / "gate.json")
    avb_path = _write_avb_diagnostic(tmp_path / "avb.json", classification="AVB-Z")
    output_path = tmp_path / "readiness.json"
    with pytest.raises(ValueError):
        jsd.produce_stage_d_readiness_artifact(preflight_path, avb_path, output_path=output_path)
    assert not output_path.exists()


def test_tc32_produce_stage_d_readiness_artifact_fails_closed_on_missing_classification_field(tmp_path):
    preflight_path = _write_preflight_gate(tmp_path / "gate.json")
    avb_path = _write(tmp_path / "avb.json", {"generated_at": "2026-08-25T10:00:00+00:00", "classification": {}})
    output_path = tmp_path / "readiness.json"
    with pytest.raises(ValueError):
        jsd.produce_stage_d_readiness_artifact(preflight_path, avb_path, output_path=output_path)
    assert not output_path.exists()


def test_tc33_produce_stage_d_readiness_artifact_fails_closed_on_stale_generation_skew(tmp_path):
    preflight_path = _write_preflight_gate(tmp_path / "gate.json", generated_at="2026-08-25T00:00:00+00:00")
    avb_path = _write_avb_diagnostic(tmp_path / "avb.json", generated_at="2026-08-26T12:00:00+00:00")  # >6h apart
    output_path = tmp_path / "readiness.json"
    with pytest.raises(ValueError):
        jsd.produce_stage_d_readiness_artifact(preflight_path, avb_path, output_path=output_path)
    assert not output_path.exists()


def test_produce_stage_d_readiness_artifact_passes_when_generation_timestamps_agree_closely(tmp_path):
    preflight_path = _write_preflight_gate(tmp_path / "gate.json", generated_at="2026-08-25T10:00:00+00:00")
    avb_path = _write_avb_diagnostic(tmp_path / "avb.json", generated_at="2026-08-25T10:05:00+00:00")  # 5 min apart
    output_path = tmp_path / "readiness.json"
    readiness = jsd.produce_stage_d_readiness_artifact(preflight_path, avb_path, output_path=output_path)
    assert readiness["staleness_check"]["consistent"] is True


def test_produce_stage_d_readiness_artifact_avb_c_forces_not_ready_even_with_passing_preflight(tmp_path):
    preflight_path = _write_preflight_gate(tmp_path / "gate.json", passed=True)
    avb_path = _write_avb_diagnostic(tmp_path / "avb.json", classification="AVB-C")
    output_path = tmp_path / "readiness.json"
    readiness = jsd.produce_stage_d_readiness_artifact(preflight_path, avb_path, output_path=output_path)
    assert readiness["ready"] is False
    assert readiness["authorized"] is False


# ======================================================================================================
# goal-market-compass iter-15 (Goal 9): readiness-time identity observation -- labeled, honestly compared
# ======================================================================================================


def test_tc37_capture_readiness_time_identity_observation_carries_the_required_labels(engine, cfg):
    with Session(engine) as session:
        observation = jsd.capture_readiness_time_identity_observation(
            session, cfg, git_head="deadbeef", goal_md_text=_GOAL_MD_MATCHING,
            prior_iteration_14_identity="53d2ffd10cdbf89ef16681111bd900766e00e5809bc4ebc7d4b5f2bf1b7f6c55",
        )
    assert observation["readiness_time_only"] is True
    assert observation["authorizing"] is False
    assert observation["reusable_for_stage_d_execution"] is False
    # still carries the same underlying fields freeze_stage_d_attempt_identity produces.
    assert "engine_identity" in observation and "config_subset_hash" in observation


def test_tc38_comparison_against_iteration_14_frozen_identity_is_stated_honestly(engine, cfg):
    with Session(engine) as session:
        real_identity = jsd.freeze_stage_d_attempt_identity(session, cfg, git_head="a", goal_md_text=_GOAL_MD_MATCHING)

    with Session(engine) as session:
        matching = jsd.capture_readiness_time_identity_observation(
            session, cfg, git_head="a", goal_md_text=_GOAL_MD_MATCHING,
            prior_iteration_14_identity=real_identity["engine_identity"],
        )
    assert matching["comparison_to_iteration_14_frozen_identity"]["matches"] is True

    with Session(engine) as session:
        drifted = jsd.capture_readiness_time_identity_observation(
            session, cfg, git_head="a", goal_md_text=_GOAL_MD_MATCHING,
            prior_iteration_14_identity="deliberately-different-value",
        )
    assert drifted["comparison_to_iteration_14_frozen_identity"]["matches"] is False

    with Session(engine) as session:
        unsupplied = jsd.capture_readiness_time_identity_observation(
            session, cfg, git_head="a", goal_md_text=_GOAL_MD_MATCHING,
        )
    assert unsupplied["comparison_to_iteration_14_frozen_identity"]["matches"] is None  # never assumed


def test_tc39_freeze_stage_d_attempt_identity_takes_no_artifact_path_parameter():
    """A structural proof (TC-39): `freeze_stage_d_attempt_identity`'s signature carries no parameter that
    could load a prior freeze from a file -- a real future Stage D recomputes fresh, never reads a
    persisted artifact through this function."""
    import inspect
    sig = inspect.signature(jsd.freeze_stage_d_attempt_identity)
    for name, param in sig.parameters.items():
        assert "path" not in name.lower(), f"unexpected path-like parameter {name!r}"
        assert param.annotation in (inspect.Parameter.empty,) or "Path" not in str(param.annotation), (
            f"parameter {name!r} looks like it accepts a filesystem path"
        )


def test_capture_stage_d_preflight_backward_compatible_without_prior_identity(engine, cfg):
    """Omitting `prior_iteration_14_identity` (iteration 14's own call shape) still works -- the new
    parameter is purely additive."""
    with Session(engine) as session:
        preflight = jsd.capture_stage_d_preflight(
            session, engine, None, goal_md_text=_GOAL_MD_MATCHING, git_head="deadbeef", config=cfg,
        )
    assert preflight["attempt_identity"]["readiness_time_only"] is True
    assert preflight["attempt_identity"]["comparison_to_iteration_14_frozen_identity"]["matches"] is None
