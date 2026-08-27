"""goal-market-compass iter-22 -- J-11 Stage G FULL VERIFICATION tests (TC-1 through TC-19, TC-22,
TC-24, TC-25, TC-26, TC-29 from the phase spec's TESTING REQUIREMENTS; TC-20/TC-21/TC-27/TC-28/TC-30 are
proven by a fresh live grep/`git status`/`git diff` cited in the dev handoff, or live in the CLI-script
test file).

File-scoped, fixture-DB-only (fresh `sqlite://` engine, `SQLModel.metadata.create_all`) -- the SAME
pattern `test_j11_stage_e_execute.py`/`test_j11_stage_f_execute.py` use, never `loaded_engine` and never
`apps/backend/data/trendora.db`.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import load_config
from app.engine import data_manager
from app.engine import j11_stage_g_verify as jsgv
from app.engine.j11_maintenance import INCIDENT_DATES
from app.models import (
    AvailabilityCache,
    CoverageSnapshot,
    DailyPrice,
    EventStudyCache,
    ForwardAggregateCache,
    ForwardReturn,
    IndexSeriesCache,
    MaintenanceBoundary,
    MarketPhaseCache,
    MembershipTimelineCache,
    NextSessionManifest,
    ScannerResult,
    ScannerRun,
)

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

BACKEND_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = BACKEND_DIR / "app" / "engine" / "j11_stage_g_verify.py"
CLI_SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_stage_g_verify.py"


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


# --- shared fixture helpers (mirrors test_j11_stage_e_execute.py/test_j11_stage_f_execute.py's idiom) ---


def _mk_run(session: Session, asof: date, *, engine_identity_value: "str | None" = "stub-identity", created_at=None) -> ScannerRun:
    run = ScannerRun(
        asof_date=asof, created_at=created_at or datetime.now(timezone.utc), provider="seed", benchmark="SPY",
        regime_score=55.0, regime_label="Expansion", regime_components_json="[]",
        breadth_above_50dma=50.0, breadth_above_200dma=55.0,
        new_high_low_json="{}", candidate_counts_json="{}",
        engine_identity=engine_identity_value,
    )
    session.add(run)
    session.flush()
    return run


def _mk_result(session: Session, run: ScannerRun, ticker: str, rank: int = 1) -> ScannerResult:
    result = ScannerResult(
        run_id=run.id, ticker=ticker, name=ticker, sector="Technology",
        leadership_score=50.0, leadership_bucket="Neutral",
        entry_quality_score=50.0, entry_quality_bucket="Neutral",
        risk_score=50.0, risk_bucket="Neutral", setup_status="None", rank=rank,
        record_json="{}",
    )
    session.add(result)
    session.flush()
    return result


def _mk_forward_return(session: Session, run: ScannerRun, symbol: str, *, horizon: int = 1, measured_date=None) -> ForwardReturn:
    fr = ForwardReturn(
        run_id=run.id, symbol=symbol, horizon=horizon, asof_date=run.asof_date,
        entry_close=100.0, measured_date=measured_date or (run.asof_date + timedelta(days=horizon)),
        realized_return=0.01,
    )
    session.add(fr)
    session.flush()
    return fr


def _mk_prices(session: Session, symbol: str, start: date, n_days: int, *, price: float = 100.0) -> None:
    d = start
    for _ in range(n_days):
        session.add(DailyPrice(symbol=symbol, date=d, open=price, high=price, low=price, close=price, volume=1000))
        d = d + timedelta(days=1)
    session.flush()


def _mk_manifest(session: Session, run: ScannerRun, *, version: int = 1) -> NextSessionManifest:
    manifest = NextSessionManifest(
        as_of=run.asof_date, version=version, source_run_id=run.id,
        session_delta_json="{}", narrative_json="{}", selection_json="{}",
        content_hash="stub-content-hash", created_at=datetime.now(timezone.utc),
        mode="at_ingest", frozen=True,
        generation_json=json.dumps({"producer": "ingest_finalize", "engine_identity": "stub-engine-identity"}),
        engine_identity="stub-engine-identity", manifest_hash="stub-manifest-hash",
        available_at_utc=datetime.now(timezone.utc), prospective_eligible=True,
    )
    session.add(manifest)
    session.flush()
    return manifest


def _mk_boundary(session: Session, *, dates=INCIDENT_DATES, active: bool = True) -> MaintenanceBoundary:
    from app.engine import j11_preboot_guard as guard
    return guard.register_boundary(session, name=guard.J11_INCIDENT_BOUNDARY_NAME, dates=dates, reason="fixture", active=active)


def _mk_membership_timeline_row(session, *, dataset_version, created_at=None, points=None):
    payload = {"candidate_pool_count": 1, "points": points or [], "labels": {}}
    row = MembershipTimelineCache(
        dataset_version=dataset_version, payload_json=json.dumps(payload),
        created_at=created_at or datetime.now(timezone.utc),
    )
    session.add(row); session.flush(); return row


def _empty_sweep() -> dict:
    """A minimal `capture_full_table_sweep`-shaped dict with zero tables -- for tests that need a valid
    shape but do not care about its content."""
    return {"captured_at": "2020-01-01T00:00:00+00:00", "table_names": [], "table_count": 0, "per_table": {}}


# =======================================================================================================
# TC-19-style static proof: zero network-capable call appears in this module or the CLI script
# =======================================================================================================


def test_module_imports_no_network_capable_import():
    result = jsgv.confirm_no_network_capable_import(MODULE_PATH)
    assert result["clean"], result


def test_cli_script_imports_no_network_capable_import():
    result = jsgv.confirm_no_network_capable_import(CLI_SCRIPT_PATH)
    assert result["clean"], result


def test_network_capable_import_check_FAILS_on_a_file_that_imports_a_network_library(tmp_path):
    """iter-22 AUDIT: the two AG-9 tests above only ever assert `clean is True`, so hardwiring
    `confirm_no_network_capable_import` to return `clean: True` left the whole suite green (proven by the
    audit's own mutation run). AG-9 is a *critical* anti-goal and this check feeds `verify_raw_inputs`'s
    `ok` -- it must be provably falsifiable, not merely correct-looking."""
    offender = tmp_path / "networky.py"
    offender.write_text("import requests\nfrom urllib import request\n")
    result = jsgv.confirm_no_network_capable_import(offender)
    assert result["clean"] is False
    assert result["per_file"][str(offender)]["network_hits"] == ["requests", "urllib"]
    # and the clean/dirty distinction really is per-file, not a global constant
    mixed = jsgv.confirm_no_network_capable_import(MODULE_PATH, offender)
    assert mixed["clean"] is False
    assert mixed["per_file"][str(MODULE_PATH)]["clean"] is True


# =======================================================================================================
# TC-1 / TC-2 -- preflight gate
# =======================================================================================================


@pytest.mark.parametrize(
    "boundary_ok, stage_d_e_ok, identity_ok, manifest_ok, expected",
    [
        (True, True, True, True, True),
        (False, True, True, True, False),
        (True, False, True, True, False),
        (True, True, False, True, False),
        (True, True, True, False, False),
    ],
)
def test_preflight_gate_requires_all_four_checks(boundary_ok, stage_d_e_ok, identity_ok, manifest_ok, expected):
    gate = jsgv.stage_g_preflight_gate_verdict(
        boundary_recheck={"ok": boundary_ok}, stage_d_e_check={"ok": stage_d_e_ok},
        identity_check={"ok": identity_ok}, manifest_check={"ok": manifest_ok},
    )
    assert gate["proceed"] is expected
    if not expected:
        assert gate["blocking_reasons"]
    else:
        assert gate["blocking_reasons"] == []


# =======================================================================================================
# TC-3 -- verify_raw_inputs
# =======================================================================================================


def test_tc3_raw_inputs_matches_when_fingerprint_equal(engine, cfg):
    with Session(engine) as session:
        _mk_prices(session, "AAA", date(2024, 1, 1), 5)
        certified = data_manager if False else None  # noqa: F841 -- placeholder, replaced below
    with Session(engine) as session:
        from app.engine import j11_maintenance
        fresh = j11_maintenance.capture_pre_reset_inventory(session)["daily_prices"]
        result = jsgv.verify_raw_inputs(
            session, certified_daily_prices_fingerprint=fresh["fingerprint"],
            module_and_script_paths=(MODULE_PATH,),
        )
    assert result["ok"] is True
    assert result["fingerprint_matches"] is True
    assert "recipe" in result and result["recipe"]


def test_tc3_raw_inputs_fails_when_fingerprint_mismatched(engine):
    with Session(engine) as session:
        _mk_prices(session, "AAA", date(2024, 1, 1), 5)
        result = jsgv.verify_raw_inputs(
            session, certified_daily_prices_fingerprint="not-the-real-fingerprint",
            module_and_script_paths=(MODULE_PATH,),
        )
    assert result["ok"] is False
    assert result["fingerprint_matches"] is False


# =======================================================================================================
# TC-4 -- verify_snapshot_scope, the ids+evidence membership rule (never identity alone)
# =======================================================================================================


def test_tc4_snapshot_scope_maps_expected_ids_one_to_one(engine):
    frozen_identity = "frozen-abc"
    expected_run_id_by_date = {}
    with Session(engine) as session:
        for one_date in INCIDENT_DATES:
            run = _mk_run(session, one_date, engine_identity_value=frozen_identity)
            expected_run_id_by_date[one_date.isoformat()] = run.id
        session.commit()
    with Session(engine) as session:
        from app.engine import j11_maintenance
        sweep = j11_maintenance.capture_full_table_sweep(session)
        result = jsgv.verify_snapshot_scope(
            session, expected_run_id_by_date=expected_run_id_by_date,
            iter18_pre_stage_d_sweep=_empty_sweep(), live_full_table_sweep=sweep,
        )
    assert result["complete_11_of_11"] is True
    assert result["per_date_ok"] is True
    for iso, rec in result["per_date"].items():
        assert rec["ok"] is True


def test_tc4_a_twelfth_run_sharing_the_frozen_identity_but_a_different_date_is_excluded(engine):
    """The owner's binding membership rule: identity alone can never carry membership. A 12th run sharing
    the IDENTICAL frozen engine_identity but whose date is NOT one of the 11 incident dates must be
    structurally invisible to verify_snapshot_scope -- proven here by constructing exactly that fixture
    and asserting the function's result never references it."""
    frozen_identity = "frozen-abc"
    expected_run_id_by_date = {}
    with Session(engine) as session:
        for one_date in INCIDENT_DATES:
            run = _mk_run(session, one_date, engine_identity_value=frozen_identity)
            expected_run_id_by_date[one_date.isoformat()] = run.id
        # the 12th run: SAME identity, a date well outside the incident set
        outsider = _mk_run(session, date(2027, 1, 4), engine_identity_value=frozen_identity)
        session.commit()
        outsider_id = outsider.id
    with Session(engine) as session:
        from app.engine import j11_maintenance
        sweep = j11_maintenance.capture_full_table_sweep(session)
        result = jsgv.verify_snapshot_scope(
            session, expected_run_id_by_date=expected_run_id_by_date,
            iter18_pre_stage_d_sweep=_empty_sweep(), live_full_table_sweep=sweep,
        )
    assert result["complete_11_of_11"] is True
    assert result["per_date_ok"] is True
    assert len(result["per_date"]) == 11
    assert all(rec["observed_ids"] != [outsider_id] for rec in result["per_date"].values())
    assert outsider_id not in {v for rec in result["per_date"].values() for v in rec["observed_ids"]}


def test_tc4_snapshot_scope_fails_when_an_incident_date_maps_to_the_wrong_id(engine):
    expected_run_id_by_date = {}
    with Session(engine) as session:
        for one_date in INCIDENT_DATES:
            run = _mk_run(session, one_date)
            expected_run_id_by_date[one_date.isoformat()] = run.id + 999  # deliberately wrong
        session.commit()
    with Session(engine) as session:
        from app.engine import j11_maintenance
        sweep = j11_maintenance.capture_full_table_sweep(session)
        result = jsgv.verify_snapshot_scope(
            session, expected_run_id_by_date=expected_run_id_by_date,
            iter18_pre_stage_d_sweep=_empty_sweep(), live_full_table_sweep=sweep,
        )
    assert result["per_date_ok"] is False
    assert result["ok"] is False


# =======================================================================================================
# TC-6 -- verify_forward_returns: population (a) matches, population (b) zero delta is CORRECT
# =======================================================================================================


def test_tc6_forward_returns_population_b_zero_delta_scored_as_correct(engine, cfg):
    with Session(engine) as session:
        run = _mk_run(session, date(2026, 8, 12))
        # enough post-run trading days for horizon=1 to be genuinely observable (otherwise
        # population_c_latest_run_observable_ceiling_respected correctly flags an inconsistent fixture --
        # a forward-return row existing with zero observable days after it -- as a real failure).
        _mk_prices(session, "AAA", date(2026, 8, 13), 5)
        _mk_forward_return(session, run, "AAA", horizon=1)
        session.commit()
        run_id = run.id

    stage_e_report = {
        "population_a_rebuilt_incident_runs": {str(run_id): {"pre": 0, "post": 1, "newly_inserted": 1}},
        "population_a_total_newly_inserted": 1,
        "population_b_retained_run_holes": {"pre_total": 0, "post_total": 0, "pre_by_run_id": {}, "post_by_run_id": {}},
    }
    with Session(engine) as session:
        result = jsgv.verify_forward_returns(
            session, incident_run_ids=[run_id], stage_e_population_report=stage_e_report,
        )
    assert result["population_b_is_zero_correct_outcome"] is True
    assert result["population_b_delta_from_pre_stage_e_baseline"] == 0
    assert result["checks"]["population_a_matches_stage_e_recorded_fill"] is True
    assert result["ok"] is True


def test_tc6_forward_returns_fails_when_population_a_count_drifts_from_recorded(engine):
    with Session(engine) as session:
        run = _mk_run(session, date(2026, 8, 12))
        # NO forward return inserted -- live count 0, but the recorded baseline claims 1
        session.commit()
        run_id = run.id

    stage_e_report = {
        "population_a_rebuilt_incident_runs": {str(run_id): {"pre": 0, "post": 1, "newly_inserted": 1}},
        "population_a_total_newly_inserted": 1,
        "population_b_retained_run_holes": {"pre_total": 0, "post_total": 0, "pre_by_run_id": {}, "post_by_run_id": {}},
    }
    with Session(engine) as session:
        result = jsgv.verify_forward_returns(
            session, incident_run_ids=[run_id], stage_e_population_report=stage_e_report,
        )
    assert result["checks"]["population_a_matches_stage_e_recorded_fill"] is False
    assert result["ok"] is False


def test_forward_returns_fails_when_a_new_hole_appears_since_stage_e(engine):
    """A NON-zero population (b) delta -- something wrote a forward return on a retained run measuring
    into an incident date SINCE Stage E's own recorded baseline -- must be a real, falsifiable FAIL, never
    silently treated as fine."""
    incident_date = INCIDENT_DATES[0]
    with Session(engine) as session:
        retained_run = _mk_run(session, date(2026, 1, 1))
        _mk_forward_return(session, retained_run, "AAA", measured_date=incident_date)
        session.commit()
        retained_run_id = retained_run.id

    stage_e_report = {
        "population_a_rebuilt_incident_runs": {},
        "population_a_total_newly_inserted": 0,
        "population_b_retained_run_holes": {
            "pre_total": 0, "post_total": 0, "pre_by_run_id": {}, "post_by_run_id": {},
        },
    }
    with Session(engine) as session:
        result = jsgv.verify_forward_returns(
            session, incident_run_ids=[], stage_e_population_report=stage_e_report,
        )
    assert result["population_b_delta_from_pre_stage_e_baseline"] == 1
    assert result["population_b_is_zero_correct_outcome"] is False
    assert result["ok"] is False


# =======================================================================================================
# TC-7 -- verify_manifests: direct SQL only, minting trap avoided
# =======================================================================================================


def test_tc7_manifests_matches_and_never_calls_get_or_create_manifest(engine, monkeypatch, cfg):
    with Session(engine) as session:
        run = _mk_run(session, date(2026, 8, 12))
        _mk_manifest(session, run)
        session.commit()

    from app.engine import j11_schema_migration as migration
    certified_dump = migration.dump_table(engine, NextSessionManifest.__table__)

    # poison compass.get_or_create_manifest -- if verify_manifests ever calls it, the test fails loudly.
    import app.engine.compass as compass_mod
    def _boom(*args, **kwargs):
        raise AssertionError("verify_manifests must never call get_or_create_manifest (the minting trap)")
    monkeypatch.setattr(compass_mod, "get_or_create_manifest", _boom)

    with Session(engine) as session:
        result = jsgv.verify_manifests(session, engine, certified_manifest_dump=certified_dump)
    assert result["ok"] is True
    assert result["live_row_count"] == 1
    assert result["no_manifest_minted_for_manifest_less_dates"] is True
    assert set(result["manifest_less_incident_dates"]) == {d.isoformat() for d in INCIDENT_DATES if d != date(2026, 8, 12)}


def test_manifests_fails_when_a_manifest_less_date_unexpectedly_has_a_row():
    """If a manifest row somehow exists for a date the certified baseline recorded as manifest-less, that
    is exactly the fabricated-historical-prior AG-1/AG-12 class defect Stage G exists to catch."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        run = _mk_run(session, INCIDENT_DATES[0])  # a date the certified baseline (empty) shows manifest-less
        _mk_manifest(session, run)
        session.commit()
    result_certified_dump: list = []  # certified baseline claims ZERO manifests exist anywhere
    with Session(engine) as session:
        result = jsgv.verify_manifests(session, engine, certified_manifest_dump=result_certified_dump)
    assert result["no_manifest_minted_for_manifest_less_dates"] is False
    assert result["ok"] is False


# =======================================================================================================
# TC-9 -- verify_audit_evidence_and_user_state
# =======================================================================================================


def test_tc9_audit_evidence_matches_certified_baseline(engine, tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    staging_path = tmp_path / "staging.jsonl"
    registry_path = tmp_path / "registry.jsonl"
    for _ in range(7):
        ledger_path.write_text(ledger_path.read_text() + '{"verdict": {"status": "FAIL"}}\n' if ledger_path.exists() else '{"verdict": {"status": "FAIL"}}\n')
        staging_path.write_text(staging_path.read_text() + '{"verdict": {"status": "FAIL"}}\n' if staging_path.exists() else '{"verdict": {"status": "FAIL"}}\n')
    registry_path.write_text("")

    monkeypatch.setenv("LEDGER_PATH", str(ledger_path))
    monkeypatch.setenv("STAGING_LEDGER_PATH", str(staging_path))
    monkeypatch.setenv("TRENDORA_REGISTRY_PATH", str(registry_path))

    from app.engine import j11_maintenance
    with Session(engine) as session:
        fresh = j11_maintenance.capture_pre_reset_inventory(session)

    certified_pre_reset_inventory = {
        "data_provider_runs_count": fresh["data_provider_runs_count"],
        "watchlist_count": fresh["watchlist_count"],
        "certified_claims_ledger": fresh["certified_claims_ledger"],
        "staging_ledger": fresh["staging_ledger"],
    }
    with Session(engine) as session:
        result = jsgv.verify_audit_evidence_and_user_state(
            session, engine,
            certified_pre_reset_inventory=certified_pre_reset_inventory,
            certified_data_provider_runs_count=fresh["data_provider_runs_count"],
            certified_watchlist_count=fresh["watchlist_count"],
        )
    assert result["canonical_seven_all_fail"] is True
    assert result["staging_seven_all_fail"] is True
    assert result["certified_ledger_file_hash_ok"] is True
    assert result["staging_ledger_file_hash_ok"] is True
    assert result["ok"] is True


def test_audit_evidence_fails_when_data_provider_runs_count_drifts(engine, tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("LEDGER_PATH", str(ledger_path))
    monkeypatch.setenv("STAGING_LEDGER_PATH", str(tmp_path / "staging.jsonl"))
    monkeypatch.setenv("TRENDORA_REGISTRY_PATH", str(tmp_path / "registry.jsonl"))

    from app.engine import j11_maintenance
    with Session(engine) as session:
        fresh = j11_maintenance.capture_pre_reset_inventory(session)
    certified_pre_reset_inventory = {
        "data_provider_runs_count": fresh["data_provider_runs_count"],
        "watchlist_count": fresh["watchlist_count"],
        "certified_claims_ledger": fresh["certified_claims_ledger"],
        "staging_ledger": fresh["staging_ledger"],
    }
    with Session(engine) as session:
        result = jsgv.verify_audit_evidence_and_user_state(
            session, engine,
            certified_pre_reset_inventory=certified_pre_reset_inventory,
            certified_data_provider_runs_count=fresh["data_provider_runs_count"] + 5,  # deliberately wrong
            certified_watchlist_count=fresh["watchlist_count"],
        )
    assert result["data_provider_runs_count_ok"] is False
    assert result["ok"] is False


# =======================================================================================================
# TC-10 -- verify_cache_dispositions
# =======================================================================================================


def test_tc10_cache_dispositions_ok_when_five_tables_empty_and_index_series_matches(engine, cfg):
    _mk_prices_session_free = None  # noqa: F841
    with Session(engine) as session:
        _mk_prices(session, "SPY", date(2024, 1, 1), 3)
        session.commit()
        from app.engine import indexes
        stamp = indexes.index_series_dataset_version(session, cfg)
        session.add(IndexSeriesCache(range_key="all", full=True, dataset_version=stamp, payload_json="{}", created_at=datetime.now(timezone.utc)))
        session.commit()

    certified_dispositions = {
        "event_study_cache": {"disposition": "explicit_delete"},
        "market_phase_cache": {"disposition": "explicit_delete"},
        "forward_aggregate_cache": {"disposition": "explicit_delete"},
        "coverage_snapshot": {"disposition": "explicit_delete"},
        "availability_cache": {"disposition": "explicit_delete"},
        "index_series_cache": {"disposition": "prove_unaffected_leave_alone"},
        "membership_timeline_cache": {"disposition": "preserve_for_incremental_reuse"},
    }
    with Session(engine) as session:
        result = jsgv.verify_cache_dispositions(session, cfg, certified_dispositions=certified_dispositions)
    assert result["ok"] is True
    for name in ("event_study_cache", "market_phase_cache", "forward_aggregate_cache", "coverage_snapshot", "availability_cache"):
        assert result["per_table"][name]["live_count"] == 0
        assert result["per_table"][name]["ok"] is True
    assert result["per_table"]["index_series_cache"]["ok"] is True


def test_cache_dispositions_fails_when_an_explicit_delete_table_still_has_a_row(engine, cfg):
    with Session(engine) as session:
        session.add(EventStudyCache(subject="AAA", view="episodes", asof_key="all", dataset_version="stale", horizon=5, payload_json="{}", created_at=datetime.now(timezone.utc)))
        session.commit()

    certified_dispositions = {"event_study_cache": {"disposition": "explicit_delete"}}
    with Session(engine) as session:
        result = jsgv.verify_cache_dispositions(session, cfg, certified_dispositions=certified_dispositions)
    assert result["per_table"]["event_study_cache"]["ok"] is False
    assert result["ok"] is False


# =======================================================================================================
# TC-11 / TC-12 -- verify_membership_timeline_preserved_row (auditor gap B2)
# =======================================================================================================


def test_tc11_membership_timeline_recompute_matches_stored_point_exactly(engine, cfg):
    target_date = INCIDENT_DATES[0]
    with Session(engine) as session:
        run = _mk_run(session, target_date)
        _mk_result(session, run, "AAA")
        session.commit()
        from app.engine import data_manager as dm
        fresh = dm._membership_timeline(session, cfg, [target_date])
        point = fresh["points"][0]
        session.add(MembershipTimelineCache(
            dataset_version="stub-stamp", payload_json=json.dumps({"candidate_pool_count": 1, "points": [point], "labels": {}}),
            created_at=datetime.now(timezone.utc),
        ))
        session.commit()

    with Session(engine) as session:
        result = jsgv.verify_membership_timeline_preserved_row(session, cfg, stage_f_new_dates=[])
    assert result["already_cached_incident_dates"] == [target_date.isoformat()]
    assert result["disposition"] == "preserve_for_incremental_reuse"
    assert result["mismatches"] == []
    assert result["per_date"][target_date.isoformat()]["ok"] is True


def test_tc12_membership_timeline_mismatch_flips_disposition_to_explicit_delete(engine, cfg):
    target_date = INCIDENT_DATES[0]
    with Session(engine) as session:
        run = _mk_run(session, target_date)
        _mk_result(session, run, "AAA")
        session.commit()
        # a DELIBERATELY WRONG stored point -- size claims 999 members, never matching the live single-member run
        stale_point = {"date": target_date.isoformat(), "size": 999, "entries": ["ZZZ"], "exits": [], "excluded": {}}
        session.add(MembershipTimelineCache(
            dataset_version="stub-stamp",
            payload_json=json.dumps({"candidate_pool_count": 1, "points": [stale_point], "labels": {}}),
            created_at=datetime.now(timezone.utc),
        ))
        session.commit()

    with Session(engine) as session:
        result = jsgv.verify_membership_timeline_preserved_row(session, cfg, stage_f_new_dates=[])
    assert result["disposition"] == "explicit_delete"
    assert result["mismatches"], "a real mismatch must be recorded, never silently swallowed"
    assert any(m["field"] == "size" for m in result["mismatches"])

    # the caller's fallback action actually deletes the row
    with Session(engine) as session:
        action = jsgv.execute_membership_timeline_delete_if_stale(session, verification=result)
    assert action["deleted"] is True
    with Session(engine) as session:
        assert session.exec(select(MembershipTimelineCache)).first() is None


def test_tc12_deletion_confirmed_reconciles_stage_g_verdict_after_a_genuine_repair(engine, cfg):
    """Closes the loop end-to-end over REAL database state (not hand-constructed dicts, unlike the
    `test_deletion_check_*`/`test_stage_g_verdict_membership_timeline_*` unit tests above): a genuinely
    stale row is found, genuinely deleted, and a genuine live post-delete `COUNT(*)` confirms it -- proving
    the full corrected chain (`verify_membership_timeline_preserved_row` ->
    `execute_membership_timeline_delete_if_stale` -> `confirm_membership_timeline_deletion_matches_
    verification` -> `stage_g_verdict`) composes correctly for the exact repair scenario this iteration's
    own live run actually hit (a genuine B2 mismatch, genuinely corrected)."""
    target_date = INCIDENT_DATES[0]
    with Session(engine) as session:
        run = _mk_run(session, target_date)
        _mk_result(session, run, "AAA")
        session.commit()
        stale_point = {"date": target_date.isoformat(), "size": 999, "entries": ["ZZZ"], "exits": [], "excluded": {}}
        session.add(MembershipTimelineCache(
            dataset_version="stub-stamp",
            payload_json=json.dumps({"candidate_pool_count": 1, "points": [stale_point], "labels": {}}),
            created_at=datetime.now(timezone.utc),
        ))
        session.commit()

    with Session(engine) as session:
        verification = jsgv.verify_membership_timeline_preserved_row(session, cfg, stage_f_new_dates=[])
    assert verification["disposition"] == "explicit_delete"

    with Session(engine) as session:
        delete_action = jsgv.execute_membership_timeline_delete_if_stale(session, verification=verification)
    assert delete_action["deleted"] is True

    with Session(engine) as session:
        live_row_count_after = len(session.exec(select(MembershipTimelineCache)).all())
    assert live_row_count_after == 0  # sanity: the row is genuinely gone, not merely reported as deleted

    deletion_check = jsgv.confirm_membership_timeline_deletion_matches_verification(
        verification=verification, delete_action=delete_action, live_row_count_after_action=live_row_count_after,
    )
    assert deletion_check["matches"] is True

    verdict = jsgv.stage_g_verdict(**{**_all_pass_inputs(), "membership_timeline_deletion_check": deletion_check})
    assert verdict["category_results"]["membership_timeline_reconciled"] is True
    assert verdict["full_pass"] is True


def test_membership_timeline_dates_in_stage_f_new_dates_are_never_targeted(engine, cfg):
    """A date Stage F itself recorded as `new_dates` (never previously cached) must be excluded from the
    B2 verification target set -- there is nothing stale to prove about a date that was never cached
    before Stage F's own incremental evaluation."""
    target_date = INCIDENT_DATES[0]
    with Session(engine) as session:
        run = _mk_run(session, target_date)
        _mk_result(session, run, "AAA")
        session.commit()
        point = {"date": target_date.isoformat(), "size": 1, "entries": ["AAA"], "exits": [], "excluded": {}}
        session.add(MembershipTimelineCache(
            dataset_version="stub-stamp",
            payload_json=json.dumps({"candidate_pool_count": 1, "points": [point], "labels": {}}),
            created_at=datetime.now(timezone.utc),
        ))
        session.commit()

    with Session(engine) as session:
        result = jsgv.verify_membership_timeline_preserved_row(session, cfg, stage_f_new_dates=[target_date.isoformat()])
    assert result["already_cached_incident_dates"] == []
    assert result["disposition"] == "preserve_for_incremental_reuse"


def test_membership_timeline_no_stored_row_is_a_vacuous_pass_no_write():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        result = jsgv.verify_membership_timeline_preserved_row(session, load_config(), stage_f_new_dates=[])
    assert result["row_present"] is False
    assert result["disposition"] == "explicit_delete"
    with Session(engine) as session:
        action = jsgv.execute_membership_timeline_delete_if_stale(session, verification=result)
    assert action["deleted"] is False


# =======================================================================================================
# named traps -- citation existence + live spot checks
# =======================================================================================================


def test_named_traps_assembles_exactly_18_and_every_citation_exists(engine):
    with Session(engine) as session:
        for one_date in INCIDENT_DATES:
            _mk_run(session, one_date, engine_identity_value="frozen-xyz")
        session.commit()
        expected_run_id_by_date = {d.isoformat(): rid for d, rid in zip(
            sorted(INCIDENT_DATES), sorted(session.exec(select(ScannerRun.id)).all()),
        )}
    # synthetic pre-Stage-C ids for 2026-08-11/2026-08-12, deliberately DIFFERENT from their post-Stage-D
    # ids above -- proves the id-reuse trap's evidence-grounded (never hardcoded) comparison.
    pre_stage_c_run_id_by_date = {
        "2026-08-11": expected_run_id_by_date["2026-08-11"] - 1000,
        "2026-08-12": expected_run_id_by_date["2026-08-12"] - 1000,
    }
    with Session(engine) as session:
        result = jsgv.verify_named_traps(
            session, tests_dir=BACKEND_DIR / "tests", expected_run_id_by_date=expected_run_id_by_date,
            frozen_engine_identity="frozen-xyz",
            boundary_recheck={"boundary_active": True, "all_dates_blocked": True},
            pre_stage_c_run_id_by_date=pre_stage_c_run_id_by_date,
        )
    assert result["trap_count"] == 18
    for trap in result["traps"]:
        assert trap["ok"] is True, trap


def test_named_traps_procedural_entries_are_labelled_asserted_not_verified(engine):
    """iter-22 AUDIT (finding B1): exactly two of the 18 traps resolve to an unconditional `ok: True` with
    no query behind them. That cannot be fixed by code -- both are facts about the iteration history -- but
    it MUST NOT be presented as a live spot-check. This test pins the honest labelling so a future edit
    cannot quietly re-merge them into the evidence-bearing set, and pins the count at exactly two so a
    third unconditional pass cannot be added without failing here."""
    with Session(engine) as session:
        for one_date in INCIDENT_DATES:
            _mk_run(session, one_date, engine_identity_value="frozen-xyz")
        session.commit()
        expected_run_id_by_date = {d.isoformat(): rid for d, rid in zip(
            sorted(INCIDENT_DATES), sorted(session.exec(select(ScannerRun.id)).all()),
        )}
    with Session(engine) as session:
        result = jsgv.verify_named_traps(
            session, tests_dir=BACKEND_DIR / "tests", expected_run_id_by_date=expected_run_id_by_date,
            frozen_engine_identity="frozen-xyz",
            boundary_recheck={"boundary_active": True, "all_dates_blocked": True},
            pre_stage_c_run_id_by_date={
                "2026-08-11": expected_run_id_by_date["2026-08-11"] - 1000,
                "2026-08-12": expected_run_id_by_date["2026-08-12"] - 1000,
            },
        )
    procedural = [t for t in result["traps"] if "procedural_fact" in t]
    assert len(procedural) == 2, procedural
    assert {t["procedural_fact"] for t in procedural} == set(jsgv._PROCEDURAL_ONLY_TRAP_CHECKS)
    for trap in procedural:
        assert trap["live_check_performed"] is False
        assert trap["evidence_class"] == "procedural_not_live_verifiable"
        assert trap["rationale"]
        # and they must NEVER carry the live_spot_check key that the four real probes carry
        assert "live_spot_check" not in trap

    live = [t for t in result["traps"] if "live_spot_check" in t]
    assert len(live) == 4, live
    # every genuinely-live spot-check carries observed payload, not just a bare `ok`
    for trap in live:
        assert set(trap) - {"family", "trap_id", "description", "live_spot_check", "ok"}, trap


def test_named_traps_fails_when_a_citation_is_dangling(tmp_path):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    empty_tests_dir = tmp_path  # no test files at all -- every citation must fail to resolve
    with Session(engine) as session:
        result = jsgv.verify_named_traps(
            session, tests_dir=empty_tests_dir, expected_run_id_by_date={},
            frozen_engine_identity="x", boundary_recheck={"boundary_active": False, "all_dates_blocked": False},
        )
    assert result["ok"] is False
    citation_traps = [t for t in result["traps"] if "citation" in t]
    assert citation_traps and all(t["ok"] is False for t in citation_traps)


def test_named_traps_all_11_share_frozen_identity_fails_on_a_drifted_run(engine):
    with Session(engine) as session:
        dates = sorted(INCIDENT_DATES)
        for i, one_date in enumerate(dates):
            identity = "frozen-xyz" if i > 0 else "DRIFTED"  # the first date's run carries the WRONG identity
            _mk_run(session, one_date, engine_identity_value=identity)
        session.commit()
        expected_run_id_by_date = {
            d.isoformat(): rid for d, rid in zip(dates, sorted(session.exec(select(ScannerRun.id)).all()))
        }
    with Session(engine) as session:
        result = jsgv.verify_named_traps(
            session, tests_dir=BACKEND_DIR / "tests", expected_run_id_by_date=expected_run_id_by_date,
            frozen_engine_identity="frozen-xyz",
            boundary_recheck={"boundary_active": True, "all_dates_blocked": True},
        )
    identity_trap = next(t for t in result["traps"] if t.get("live_spot_check") == "all_11_runs_share_frozen_identity")
    assert identity_trap["ok"] is False
    assert result["ok"] is False


# =======================================================================================================
# TC-16 / TC-17 / TC-18 -- the coverage_from_storage guard edit (in data_manager.py; exercised here via
# the live-imported function, proving the SIBLING production edit actually behaves as this module assumes)
# =======================================================================================================


def test_tc16_coverage_from_storage_refuses_self_heal_for_a_boundary_blocked_incident_date(engine, cfg):
    from app.engine import j11_preboot_guard as guard
    incident_date = INCIDENT_DATES[0]
    with Session(engine) as session:
        guard.register_boundary(session, name=guard.J11_INCIDENT_BOUNDARY_NAME, dates=INCIDENT_DATES, reason="fixture", active=True)
        _mk_prices(session, "SPY", incident_date, 1)
        _mk_run(session, incident_date)
        session.commit()

    with Session(engine) as session:
        assert session.exec(select(CoverageSnapshot)).first() is None
        result = data_manager.coverage_from_storage(session, cfg, as_of=incident_date)
    assert result["coverage_status"] == "not_yet_computed"
    with Session(engine) as session:
        assert session.exec(select(CoverageSnapshot)).first() is None  # zero write -- self-heal was refused


def test_tc17_coverage_from_storage_self_heals_an_ordinary_unblocked_date_unchanged(engine, cfg):
    from app.engine import j11_preboot_guard as guard
    ordinary_date = date(2024, 3, 1)
    with Session(engine) as session:
        guard.register_boundary(session, name=guard.J11_INCIDENT_BOUNDARY_NAME, dates=INCIDENT_DATES, reason="fixture", active=True)
        _mk_prices(session, "SPY", ordinary_date, 1)
        _mk_run(session, ordinary_date)
        session.commit()

    with Session(engine) as session:
        result = data_manager.coverage_from_storage(session, cfg, as_of=ordinary_date)
    assert result["coverage_status"] == "current"
    with Session(engine) as session:
        healed = session.exec(select(CoverageSnapshot).where(CoverageSnapshot.asof_key == ordinary_date.isoformat())).first()
    assert healed is not None  # self-heal fired exactly as before the guard edit


def test_tc18_coverage_from_storage_read_of_already_persisted_row_unaffected_by_guard(engine, cfg):
    from app.engine import j11_preboot_guard as guard
    incident_date = INCIDENT_DATES[0]
    with Session(engine) as session:
        guard.register_boundary(session, name=guard.J11_INCIDENT_BOUNDARY_NAME, dates=INCIDENT_DATES, reason="fixture", active=True)
        _mk_prices(session, "SPY", incident_date, 1)
        _mk_run(session, incident_date)
        session.commit()
        # persist a coverage row directly (mirrors a legitimate Stage-D-era ingest finalize write) --
        # never through the self-heal path this test is proving is UNTOUCHED for an already-persisted row.
        dataset_version = data_manager._membership_dataset_version(session, cfg)
        payload = data_manager._compute_coverage_uncached(session, cfg, as_of=incident_date)
        data_manager._upsert_coverage_snapshot(session, incident_date.isoformat(), dataset_version, payload)

    with Session(engine) as session:
        before_count = len(session.exec(select(CoverageSnapshot)).all())
        result = data_manager.coverage_from_storage(session, cfg, as_of=incident_date)
    assert result["coverage_status"] == "current"
    with Session(engine) as session:
        after_count = len(session.exec(select(CoverageSnapshot)).all())
    assert after_count == before_count == 1  # the guard is never even consulted for a read of an existing row


# =======================================================================================================
# TC-20 -- write-path call-site re-enumeration + classification
# =======================================================================================================


def test_tc20_live_write_path_enumeration_is_fully_classified_with_no_unclassified_or_stale_entries():
    app_dir = BACKEND_DIR / "app"
    sites = jsgv.enumerate_write_path_call_sites(app_dir)
    result = jsgv.classify_write_path_call_sites(sites)
    assert result["unclassified"] == [], result["unclassified"]
    assert result["stale_table_entries"] == [], result["stale_table_entries"]
    assert result["ok"] is True
    # sanity: the three named function patterns are genuinely represented, and the classification
    # excludes non-call mentions (e.g. docstring prose) -- proven by the exact expected total.
    assert result["total_sites_found"] == len(jsgv.WRITE_PATH_CLASSIFICATION)


def test_write_path_enumeration_skips_docstring_mentions_never_matches_a_def_line(tmp_path):
    synthetic = tmp_path / "synthetic.py"
    synthetic.write_text(
        '"""This module calls run_scan(session, d, cfg) as documented in prose."""\n'
        "def run_scan(session, d, cfg):\n"
        "    pass\n"
        "def caller(session, d, cfg):\n"
        "    return run_scan(session, d, cfg)\n"
    )
    sites = jsgv.enumerate_write_path_call_sites(tmp_path)
    assert len(sites) == 1  # only the REAL call inside `caller`, never the docstring, never the `def`
    assert sites[0]["enclosing_function"] == "caller"
    assert sites[0]["matched_name"] == "run_scan"


def test_write_path_classification_reports_unclassified_for_an_unreviewed_new_call_site(tmp_path):
    synthetic = tmp_path / "new_site.py"
    synthetic.write_text(
        "def some_new_function(session, d, cfg):\n"
        "    return get_or_create_manifest(session, d)\n"
    )
    sites = jsgv.enumerate_write_path_call_sites(tmp_path)
    result = jsgv.classify_write_path_call_sites(sites)
    assert result["ok"] is False
    assert len(result["unclassified"]) == 1
    assert result["unclassified"][0]["enclosing_function"] == "some_new_function"


# =======================================================================================================
# evidence-reinterpretation static check (docs/goal.md J-11 step 7)
# =======================================================================================================


def test_evidence_reinterpretation_check_clean_over_real_j11_stage_modules():
    engine_dir = BACKEND_DIR / "app" / "engine"
    paths = sorted(p for p in engine_dir.glob("j11_*.py") if p.name != "j11_stage_g_verify.py")
    result = jsgv.confirm_no_evidence_reinterpretation_calls(*paths)
    assert result["clean"] is True, result["per_file"]


def test_evidence_reinterpretation_check_flags_a_forbidden_token(tmp_path):
    poisoned = tmp_path / "poisoned.py"
    poisoned.write_text("from app.engine import forward_walk\n")
    result = jsgv.confirm_no_evidence_reinterpretation_calls(poisoned)
    assert result["clean"] is False
    assert "forward_walk" in result["per_file"][str(poisoned)]["hits"]


# =======================================================================================================
# verify_operational_isolation
# =======================================================================================================


def test_operational_isolation_ok_when_nothing_listens_on_the_probed_ports():
    # ports in the ephemeral/ typically-unused range -- vanishingly unlikely to collide with a real
    # listener on the CI/dev host; a false failure here would indicate an actual service IS listening.
    result = jsgv.verify_operational_isolation(backend_port=48213, frontend_port=48214)
    assert result["backend_listening"] is False
    assert result["frontend_listening"] is False
    assert result["ok"] is True


@pytest.mark.parametrize("which", ["backend", "frontend"])
def test_operational_isolation_FAILS_when_a_real_listener_occupies_a_probed_port(which):
    """iter-22 AUDIT: the pass-case test above was the ONLY coverage of this function, so hardwiring
    `verify_operational_isolation` to return `ok: True` left the whole suite green (proven by the audit's
    own mutation run). `operational_isolation` is one of `stage_g_verdict`'s twelve gating categories --
    the category that stands for "no application service booted during the incident window" -- so a check
    no test can distinguish from an unconditional pass is exactly the flagged-tautology pattern this
    iteration is held to. Binds a real loopback listener and proves the probe reports it."""
    import socket as _socket

    listener = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
    listener.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    busy_port = listener.getsockname()[1]
    try:
        ports = {"backend_port": 48213, "frontend_port": 48214}
        ports[f"{which}_port"] = busy_port
        result = jsgv.verify_operational_isolation(**ports)
        assert result[f"{which}_listening"] is True
        assert result["ok"] is False
    finally:
        listener.close()

    # and it goes clean again once the listener is gone -- the probe reads live state, not a constant
    after = jsgv.verify_operational_isolation(backend_port=busy_port, frontend_port=48214)
    assert after["backend_listening"] is False
    assert after["ok"] is True


# =======================================================================================================
# TC-22 -- cross-iteration mutation accounting
# =======================================================================================================


def _sweep(per_table: dict) -> dict:
    return {"captured_at": "2020-01-01T00:00:00+00:00", "table_names": sorted(per_table), "table_count": len(per_table), "per_table": per_table}


def test_tc22_mutation_accounting_passes_when_only_expected_stage_tables_changed():
    pre = _sweep({
        "scanner_runs": {"count": 3117, "min_rowid": 1, "max_rowid": 3147, "sum_rowid": 100, "fingerprint": "a"},
        "forward_returns": {"count": 100, "min_rowid": 1, "max_rowid": 100, "sum_rowid": 5, "fingerprint": "b"},
        "event_study_cache": {"count": 3, "min_rowid": 1, "max_rowid": 3, "sum_rowid": 6, "fingerprint": "c"},
        "watchlist": {"count": 6, "min_rowid": 1, "max_rowid": 6, "sum_rowid": 21, "fingerprint": "d"},
    })
    post = _sweep({
        "scanner_runs": {"count": 3128, "min_rowid": 1, "max_rowid": 3158, "sum_rowid": 200, "fingerprint": "a2"},
        "forward_returns": {"count": 16692, "min_rowid": 1, "max_rowid": 16692, "sum_rowid": 999, "fingerprint": "b2"},
        "event_study_cache": {"count": 0, "min_rowid": None, "max_rowid": None, "sum_rowid": None, "fingerprint": "c2"},
        "watchlist": {"count": 6, "min_rowid": 1, "max_rowid": 6, "sum_rowid": 21, "fingerprint": "d"},
    })
    boundary_row = {"id": 1, "name": "j11-incident-recovery", "active": True, "reason": "r", "created_at": "t", "updated_at": "t1"}
    boundary_row_after = {**boundary_row, "active": False, "updated_at": "t2"}
    result = jsgv.build_stage_g_cross_iteration_mutation_accounting(
        iter18_pre_stage_d_sweep=pre, live_post_sweep=post,
        pre_maintenance_boundary_dump=[boundary_row], post_maintenance_boundary_dump=[boundary_row_after],
        membership_timeline_row_deleted_this_iteration=False, boundary_deactivated_this_iteration=True,
    )
    assert result["unexplained_by_sweep"] == []
    assert result["boundary_check"]["ok"] is True
    assert result["ok"] is True


def test_mutation_accounting_fails_when_an_unexplained_table_changed():
    pre = _sweep({"watchlist": {"count": 6, "min_rowid": 1, "max_rowid": 6, "sum_rowid": 21, "fingerprint": "d"}})
    post = _sweep({"watchlist": {"count": 7, "min_rowid": 1, "max_rowid": 7, "sum_rowid": 28, "fingerprint": "d2"}})
    result = jsgv.build_stage_g_cross_iteration_mutation_accounting(
        iter18_pre_stage_d_sweep=pre, live_post_sweep=post,
        pre_maintenance_boundary_dump=[], post_maintenance_boundary_dump=[],
        membership_timeline_row_deleted_this_iteration=False, boundary_deactivated_this_iteration=False,
    )
    assert "watchlist" in result["unexplained_by_sweep"]
    assert result["ok"] is False


def test_mutation_accounting_fails_when_boundary_changed_columns_beyond_active_and_updated_at():
    boundary_row = {"id": 1, "name": "j11-incident-recovery", "active": True, "reason": "r", "created_at": "t", "updated_at": "t1"}
    tampered = {**boundary_row, "active": False, "updated_at": "t2", "reason": "TAMPERED"}
    result = jsgv.build_stage_g_cross_iteration_mutation_accounting(
        iter18_pre_stage_d_sweep=_empty_sweep(), live_post_sweep=_empty_sweep(),
        pre_maintenance_boundary_dump=[boundary_row], post_maintenance_boundary_dump=[tampered],
        membership_timeline_row_deleted_this_iteration=False, boundary_deactivated_this_iteration=True,
    )
    assert result["boundary_check"]["ok"] is False
    assert result["ok"] is False


def test_mutation_accounting_fails_when_boundary_changed_but_no_deactivation_was_expected():
    boundary_row = {"id": 1, "name": "j11-incident-recovery", "active": True, "reason": "r", "created_at": "t", "updated_at": "t1"}
    changed = {**boundary_row, "active": False, "updated_at": "t2"}
    result = jsgv.build_stage_g_cross_iteration_mutation_accounting(
        iter18_pre_stage_d_sweep=_empty_sweep(), live_post_sweep=_empty_sweep(),
        pre_maintenance_boundary_dump=[boundary_row], post_maintenance_boundary_dump=[changed],
        membership_timeline_row_deleted_this_iteration=False, boundary_deactivated_this_iteration=False,
    )
    assert result["boundary_check"]["ok"] is False
    assert result["ok"] is False


# =======================================================================================================
# stage_g_verdict -- no boolean permitted to pass by construction; flipping any ONE input flips the verdict
# =======================================================================================================


def _all_pass_inputs() -> dict:
    return {
        "preflight_gate": {"proceed": True},
        "raw_inputs": {"ok": True},
        "snapshot_scope": {"ok": True},
        "forward_returns": {"ok": True},
        "manifests": {"ok": True},
        "audit_evidence_and_user_state": {"ok": True},
        "cache_dispositions": {"ok": True},
        "membership_timeline_deletion_check": {"matches": True, "disposition": "preserve_for_incremental_reuse"},
        "named_traps": {"ok": True},
        "write_path_classification": {"ok": True},
        "evidence_reinterpretation_check": {"clean": True},
        "operational_isolation": {"ok": True},
    }


def test_stage_g_verdict_full_pass_when_every_category_holds():
    verdict = jsgv.stage_g_verdict(**_all_pass_inputs())
    assert verdict["full_pass"] is True
    assert verdict["failing_categories"] == []


@pytest.mark.parametrize(
    "category, broken_value",
    [
        ("preflight_gate", {"proceed": False}),
        ("raw_inputs", {"ok": False}),
        ("snapshot_scope", {"ok": False}),
        ("forward_returns", {"ok": False}),
        ("manifests", {"ok": False}),
        ("audit_evidence_and_user_state", {"ok": False}),
        ("cache_dispositions", {"ok": False}),
        ("membership_timeline_deletion_check", {"matches": False, "disposition": "explicit_delete"}),
        ("named_traps", {"ok": False}),
        ("write_path_classification", {"ok": False}),
        ("evidence_reinterpretation_check", {"clean": False}),
        ("operational_isolation", {"ok": False}),
    ],
)
def test_stage_g_verdict_fails_when_any_single_category_fails(category, broken_value):
    """The full 12-category tautology guard (review FAIL fix -- the old 11-case list deliberately EXCLUDED
    the membership-timeline category, the exact gap that let its unconditional-pass bug through review).
    Every one of `stage_g_verdict`'s 12 `category_results` keys is now covered here: flipping any ONE
    input, including this one, must flip the verdict."""
    inputs = _all_pass_inputs()
    inputs[category] = broken_value
    verdict = jsgv.stage_g_verdict(**inputs)
    assert verdict["full_pass"] is False
    # the `membership_timeline_deletion_check` PARAMETER feeds the `membership_timeline_reconciled`
    # CATEGORY key (pre-existing asymmetry: every other parameter name already equals its category key).
    expected_failing_category = (
        "membership_timeline_reconciled" if category == "membership_timeline_deletion_check" else category
    )
    assert expected_failing_category in verdict["failing_categories"]


def test_stage_g_verdict_membership_timeline_reconciled_when_deletion_confirmed_after_explicit_delete():
    """A stale row that got correctly caught, deleted, AND confirmed gone by a live post-action COUNT(*)
    is a SUCCESSFUL repair -- `membership_timeline_reconciled` is real evidence of the confirmed outcome,
    never the mere fact that `disposition` held one of its two possible strings."""
    inputs = _all_pass_inputs()
    inputs["membership_timeline_deletion_check"] = {
        "matches": True, "disposition": "explicit_delete", "deleted": True, "live_row_count_after_action": 0,
    }
    verdict = jsgv.stage_g_verdict(**inputs)
    assert verdict["category_results"]["membership_timeline_reconciled"] is True
    assert verdict["full_pass"] is True


def test_stage_g_verdict_membership_timeline_NOT_reconciled_when_corrective_delete_silently_fails():
    """The exact scenario the review's CRITICAL finding named: `disposition == "explicit_delete"` (a
    corrective write was required) but the write did not verifiably take effect (`matches: False`) --
    `membership_timeline_reconciled` must be False and the overall verdict must FAIL, never silently pass
    through to a FULLY REPAIRED declaration and the boundary-deactivation write."""
    inputs = _all_pass_inputs()
    inputs["membership_timeline_deletion_check"] = {
        "matches": False, "disposition": "explicit_delete", "deleted": False, "live_row_count_after_action": 1,
    }
    verdict = jsgv.stage_g_verdict(**inputs)
    assert verdict["category_results"]["membership_timeline_reconciled"] is False
    assert verdict["full_pass"] is False
    assert "membership_timeline_reconciled" in verdict["failing_categories"]


# =======================================================================================================
# confirm_membership_timeline_deletion_matches_verification -- the real, failable check itself
# (review FAIL fix: proves the fixed check can actually fail, closing the mutation-bar gap the coordinator
# flagged -- only 2 of 12 acceptance checks were mutation-tested in the original submission).
# =======================================================================================================


def test_deletion_check_preserve_disposition_trivially_matches_with_no_delete_action_needed():
    result = jsgv.confirm_membership_timeline_deletion_matches_verification(
        verification={"disposition": "preserve_for_incremental_reuse"},
        delete_action={"deleted": False, "reason": "nothing to delete"},
        live_row_count_after_action=1,  # the preserved row is still there -- correctly irrelevant here
    )
    assert result["matches"] is True


def test_deletion_check_explicit_delete_matches_when_deleted_true_and_row_confirmed_absent():
    result = jsgv.confirm_membership_timeline_deletion_matches_verification(
        verification={"disposition": "explicit_delete"},
        delete_action={"deleted": True, "reason": "stale row deleted per verification mismatch"},
        live_row_count_after_action=0,
    )
    assert result["matches"] is True


def test_deletion_check_explicit_delete_does_NOT_match_when_delete_action_never_reported_deleted():
    """The delete-if-stale action never actually ran the DELETE (e.g. it raised and was swallowed, or ran
    against the wrong session) -- `deleted=False` even though the disposition said a delete was required."""
    result = jsgv.confirm_membership_timeline_deletion_matches_verification(
        verification={"disposition": "explicit_delete"},
        delete_action={"deleted": False, "reason": "row already absent"},
        live_row_count_after_action=0,
    )
    assert result["matches"] is False


def test_deletion_check_explicit_delete_does_NOT_match_when_row_survives_the_delete():
    """The critical silent-failure scenario: the delete action REPORTED `deleted=True`, but a live,
    independent post-action COUNT(*) still finds the row present (e.g. a rolled-back transaction, a session
    that never committed, or a stale read) -- this must NOT be treated as a successful repair."""
    result = jsgv.confirm_membership_timeline_deletion_matches_verification(
        verification={"disposition": "explicit_delete"},
        delete_action={"deleted": True, "reason": "stale row deleted per verification mismatch"},
        live_row_count_after_action=1,
    )
    assert result["matches"] is False


def test_deletion_check_unrecognized_disposition_fails_closed():
    result = jsgv.confirm_membership_timeline_deletion_matches_verification(
        verification={"disposition": "not_a_real_disposition"},
        delete_action={"deleted": False},
        live_row_count_after_action=0,
    )
    assert result["matches"] is False


# =======================================================================================================
# TC-24 / TC-25 -- finalize_stage_g
# =======================================================================================================


def test_tc24_finalize_on_full_pass_deactivates_boundary_and_emits_fully_repaired(engine):
    with Session(engine) as session:
        _mk_boundary(session, active=True)

    with Session(engine) as session:
        result = jsgv.finalize_stage_g(session, verdict={"full_pass": True, "failing_categories": []})
    assert result["outcome"] == "FULLY_REPAIRED"
    assert result["boundary_deactivated"] is True
    assert "J-11 INCIDENT STATUS: FULLY REPAIRED" in result["terminal_lines"]

    with Session(engine) as session:
        row = session.exec(select(MaintenanceBoundary)).first()
    assert row.active is False  # row PRESERVED, only the flag flipped -- never deleted


def test_tc25_finalize_on_fail_performs_zero_writes_and_emits_incomplete(engine):
    with Session(engine) as session:
        _mk_boundary(session, active=True)

    with Session(engine) as session:
        result = jsgv.finalize_stage_g(session, verdict={"full_pass": False, "failing_categories": ["raw_inputs"]})
    assert result["outcome"] == "NOT_REPAIRED_ATTEMPT_INCOMPLETE"
    assert result["boundary_deactivated"] is False
    assert "J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE" in result["terminal_lines"]
    assert "J-11 MAINTENANCE BOUNDARY: ACTIVE" in result["terminal_lines"]

    with Session(engine) as session:
        row = session.exec(select(MaintenanceBoundary)).first()
    assert row.active is True  # never touched


# =======================================================================================================
# Full end-to-end, Stage-G-shaped fixture (mirrors test_j11_stage_f_execute.py's own idiom)
# =======================================================================================================


def test_full_end_to_end_stage_g_shaped_fixture_reaches_fully_repaired(tmp_path, cfg, monkeypatch):
    from app.db import create_db_and_tables, make_engine
    from app.engine import j11_maintenance
    from app.engine import j11_preboot_guard as guard
    from app.engine import j11_schema_migration as migration

    ledger_path = tmp_path / "ledger.jsonl"
    ledger_path.write_text('{"verdict": {"status": "FAIL"}}\n' * 7)
    staging_path = tmp_path / "staging.jsonl"
    staging_path.write_text('{"verdict": {"status": "FAIL"}}\n' * 7)
    registry_path = tmp_path / "registry.jsonl"
    registry_path.write_text("")
    monkeypatch.setenv("LEDGER_PATH", str(ledger_path))
    monkeypatch.setenv("STAGING_LEDGER_PATH", str(staging_path))
    monkeypatch.setenv("TRENDORA_REGISTRY_PATH", str(registry_path))

    db_path = tmp_path / "stage_g_fixture.db"
    fixture_engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(fixture_engine)

    frozen_identity = "fixture-frozen-identity"
    with Session(fixture_engine) as session:
        guard.register_boundary(session, name=guard.J11_INCIDENT_BOUNDARY_NAME, dates=INCIDENT_DATES, reason="fixture", active=True)
        for one_date in INCIDENT_DATES:
            _mk_prices(session, "AAA", one_date, 1)
        # a few extra post-frontier trading days so the LATEST incident-date run's horizon=1 forward
        # return is genuinely observable (population_c_latest_run_observable_ceiling_respected) -- part
        # of the SAME immutable raw daily_prices layer, present before any Stage D/E/F/G write.
        _mk_prices(session, "AAA", max(INCIDENT_DATES) + timedelta(days=1), 5)
        session.commit()
        # index_series_cache's own narrow stamp depends only on daily_prices (untouched by this fixture's
        # ScannerRun-only writes below) -- computed and seeded BEFORE the "iteration 18" baseline, mirroring
        # the real disposition ("prove_unaffected_leave_alone": the row existed before Stage D and stays
        # correct throughout, per Stage F's own already-certified proof).
        from app.engine import indexes
        index_stamp = indexes.index_series_dataset_version(session, cfg)
        session.add(IndexSeriesCache(range_key="all", full=True, dataset_version=index_stamp, payload_json="{}", created_at=datetime.now(timezone.utc)))
        # membership_timeline_cache's OWN row -- like index_series_cache, this row must ALREADY EXIST
        # before the "iteration 18" baseline sweep, at the SAME rowid it carries throughout (Stage F never
        # INSERTs/DELETEs a "preserved" row -- execute_stage_f_cache_disposition's own contract:
        # attempted_write=False for anything not classified explicit_delete). Seeded with placeholder
        # content here (the 11 ScannerRuns do not exist yet); its CONTENT is corrected via an in-place
        # UPDATE below, once the correct values are computable -- a same-rowid content UPDATE is (by
        # design, mirroring the real system) invisible to the rowid-based full-table sweep, exactly
        # matching how the real preserved row was never re-inserted either.
        session.add(MembershipTimelineCache(
            dataset_version="fixture-membership-stamp",
            payload_json=json.dumps({"candidate_pool_count": 0, "points": [], "labels": {}}),
            created_at=datetime.now(timezone.utc),
        ))
        session.commit()

    # the "iteration 18" baseline: captured BEFORE any ScannerRun/ForwardReturn row exists -- the SAME
    # point in the REAL timeline the real iter-18 sweep occupies (boundary armed, both pre-existing caches
    # already present, but Stage D/E/F not yet run). Everything below this line mirrors what Stage D
    # through G's OWN writes subsequently added.
    with Session(fixture_engine) as session:
        iter18_pre_stage_d_sweep = j11_maintenance.capture_full_table_sweep(session)

    expected_run_id_by_date: dict[str, int] = {}
    expected_fr_count_by_run_id: dict[str, int] = {}
    with Session(fixture_engine) as session:
        for one_date in sorted(INCIDENT_DATES):
            run = _mk_run(session, one_date, engine_identity_value=frozen_identity)
            _mk_result(session, run, "AAA")
            _mk_forward_return(session, run, "AAA", horizon=1)
            expected_run_id_by_date[one_date.isoformat()] = run.id
            expected_fr_count_by_run_id[str(run.id)] = 1
        session.commit()

    # membership_timeline_cache's preserved row: corrected IN PLACE (same row, same rowid -- never a
    # delete+insert) to the GENUINELY CORRECT points (computed via the real _membership_timeline, never
    # hand-typed) for all 11 incident dates -- modeling the B2-closed state where every already-cached
    # date's content is proven still correct after Stage D's regeneration (stage_f_new_dates=[] below:
    # none of them are treated as "newly added by Stage F" in this fixture).
    with Session(fixture_engine) as session:
        live_dates = sorted(session.exec(select(ScannerRun.asof_date)).all())
        correct_timeline = data_manager._membership_timeline(session, cfg, live_dates)
        row = session.exec(select(MembershipTimelineCache)).one()
        row.payload_json = json.dumps(correct_timeline)
        session.add(row)
        session.commit()

    certified_manifest_dump: list = []

    stage_e_population_report = {
        "population_a_rebuilt_incident_runs": {
            str(rid): {"pre": 0, "post": 1, "newly_inserted": 1} for rid in expected_run_id_by_date.values()
        },
        "population_a_total_newly_inserted": len(expected_run_id_by_date),
        "population_b_retained_run_holes": {"pre_total": 0, "post_total": 0, "pre_by_run_id": {}, "post_by_run_id": {}},
    }
    stage_f_dispositions = {
        "event_study_cache": {"disposition": "explicit_delete"},
        "market_phase_cache": {"disposition": "explicit_delete"},
        "forward_aggregate_cache": {"disposition": "explicit_delete"},
        "coverage_snapshot": {"disposition": "explicit_delete"},
        "availability_cache": {"disposition": "explicit_delete"},
        "index_series_cache": {"disposition": "prove_unaffected_leave_alone"},
        "membership_timeline_cache": {
            "disposition": "preserve_for_incremental_reuse",
            "membership_reuse_evaluation": {"new_dates": []},
        },
    }
    certified_pre_reset_inventory = None
    with Session(fixture_engine) as session:
        certified_pre_reset_inventory_full = j11_maintenance.capture_pre_reset_inventory(session)
    certified_pre_reset_inventory = {
        "data_provider_runs_count": certified_pre_reset_inventory_full["data_provider_runs_count"],
        "watchlist_count": certified_pre_reset_inventory_full["watchlist_count"],
        "certified_claims_ledger": certified_pre_reset_inventory_full["certified_claims_ledger"],
        "staging_ledger": certified_pre_reset_inventory_full["staging_ledger"],
    }

    # === preflight ===
    with Session(fixture_engine) as session:
        boundary_recheck = guard.evaluate_boundary_for_date_fail_closed(session, sorted(INCIDENT_DATES)[0])
    assert boundary_recheck["blocked"] is True  # sanity: the boundary is genuinely active

    from app.engine import j11_stage_d_execute as jsde
    from app.engine import j11_stage_e_execute as jsee
    from app.engine import j11_stage_f_execute as jsfe

    with Session(fixture_engine) as session:
        boundary_recheck_full = jsde.recheck_maintenance_boundary_and_guard(session)
    assert boundary_recheck_full["ok"] is True

    with Session(fixture_engine) as session:
        stage_d_e_check = jsfe.confirm_stage_e_complete_and_unrestamped(
            session, expected_run_id_by_date=expected_run_id_by_date,
            expected_forward_return_count_by_run_id=expected_fr_count_by_run_id,
            frozen_engine_identity=frozen_identity,
        )
    assert stage_d_e_check["ok"] is True

    identity_check = jsee.check_engine_identity_matches_stage_d(frozen_identity, frozen_identity)
    manifest_check = jsee.confirm_manifests_unchanged(fixture_engine, certified_manifest_dump=certified_manifest_dump)
    assert manifest_check["ok"] is True

    preflight_gate = jsgv.stage_g_preflight_gate_verdict(
        boundary_recheck=boundary_recheck_full, stage_d_e_check=stage_d_e_check,
        identity_check=identity_check, manifest_check=manifest_check,
    )
    assert preflight_gate["proceed"] is True

    # === acceptance categories ===
    with Session(fixture_engine) as session:
        raw_inputs = jsgv.verify_raw_inputs(
            session, certified_daily_prices_fingerprint=j11_maintenance.capture_pre_reset_inventory(session)["daily_prices"]["fingerprint"],
            module_and_script_paths=(MODULE_PATH,),
        )
    assert raw_inputs["ok"] is True

    with Session(fixture_engine) as session:
        live_sweep = j11_maintenance.capture_full_table_sweep(session)
        snapshot_scope = jsgv.verify_snapshot_scope(
            session, expected_run_id_by_date=expected_run_id_by_date,
            iter18_pre_stage_d_sweep=iter18_pre_stage_d_sweep, live_full_table_sweep=live_sweep,
        )
    assert snapshot_scope["ok"] is True

    with Session(fixture_engine) as session:
        forward_returns = jsgv.verify_forward_returns(
            session, incident_run_ids=sorted(expected_run_id_by_date.values()),
            stage_e_population_report=stage_e_population_report,
        )
    assert forward_returns["ok"] is True

    with Session(fixture_engine) as session:
        manifests = jsgv.verify_manifests(session, fixture_engine, certified_manifest_dump=certified_manifest_dump)
    assert manifests["ok"] is True

    with Session(fixture_engine) as session:
        audit = jsgv.verify_audit_evidence_and_user_state(
            session, fixture_engine, certified_pre_reset_inventory=certified_pre_reset_inventory,
            certified_data_provider_runs_count=certified_pre_reset_inventory["data_provider_runs_count"],
            certified_watchlist_count=certified_pre_reset_inventory["watchlist_count"],
        )
    assert audit["ok"] is True

    with Session(fixture_engine) as session:
        caches = jsgv.verify_cache_dispositions(session, cfg, certified_dispositions=stage_f_dispositions)
    assert caches["ok"] is True

    with Session(fixture_engine) as session:
        membership = jsgv.verify_membership_timeline_preserved_row(
            session, cfg, stage_f_new_dates=[],
        )
    assert membership["disposition"] == "preserve_for_incremental_reuse"

    pre_stage_c_run_id_by_date = {
        "2026-08-11": expected_run_id_by_date["2026-08-11"] - 1000,
        "2026-08-12": expected_run_id_by_date["2026-08-12"] - 1000,
    }
    with Session(fixture_engine) as session:
        traps = jsgv.verify_named_traps(
            session, tests_dir=BACKEND_DIR / "tests", expected_run_id_by_date=expected_run_id_by_date,
            frozen_engine_identity=frozen_identity, boundary_recheck=boundary_recheck_full,
            pre_stage_c_run_id_by_date=pre_stage_c_run_id_by_date,
        )
    assert traps["ok"] is True

    write_path_sites = jsgv.enumerate_write_path_call_sites(BACKEND_DIR / "app")
    write_path_classification = jsgv.classify_write_path_call_sites(write_path_sites)
    assert write_path_classification["ok"] is True

    other_modules = sorted(p for p in (BACKEND_DIR / "app" / "engine").glob("j11_*.py") if p.name != "j11_stage_g_verify.py")
    reinterpretation = jsgv.confirm_no_evidence_reinterpretation_calls(*other_modules)
    assert reinterpretation["clean"] is True

    isolation = jsgv.verify_operational_isolation(backend_port=48215, frontend_port=48216)
    assert isolation["ok"] is True

    with Session(fixture_engine) as session:
        pre_boundary_dump = migration.dump_table(fixture_engine, MaintenanceBoundary.__table__)
    pre_write_accounting = jsgv.build_stage_g_cross_iteration_mutation_accounting(
        iter18_pre_stage_d_sweep=iter18_pre_stage_d_sweep, live_post_sweep=live_sweep,
        pre_maintenance_boundary_dump=pre_boundary_dump, post_maintenance_boundary_dump=pre_boundary_dump,
        membership_timeline_row_deleted_this_iteration=False, boundary_deactivated_this_iteration=False,
    )
    assert pre_write_accounting["ok"] is True

    # The delete-if-stale action and its real reconciliation check now run BEFORE stage_g_verdict /
    # finalize_stage_g (review FAIL fix) -- mirrors the corrected script ordering exactly, so this
    # end-to-end fixture exercises the SAME sequence the live CLI script now runs, not the buggy one.
    with Session(fixture_engine) as session:
        delete_action = jsgv.execute_membership_timeline_delete_if_stale(session, verification=membership)
    assert delete_action["deleted"] is False  # confirmed fresh, nothing to delete

    with Session(fixture_engine) as session:
        live_membership_row_count_after_delete = len(session.exec(select(MembershipTimelineCache)).all())
    deletion_check = jsgv.confirm_membership_timeline_deletion_matches_verification(
        verification=membership, delete_action=delete_action,
        live_row_count_after_action=live_membership_row_count_after_delete,
    )
    assert deletion_check["matches"] is True

    verdict = jsgv.stage_g_verdict(
        preflight_gate=preflight_gate, raw_inputs=raw_inputs, snapshot_scope=snapshot_scope,
        forward_returns=forward_returns, manifests=manifests, audit_evidence_and_user_state=audit,
        cache_dispositions=caches, membership_timeline_deletion_check=deletion_check, named_traps=traps,
        write_path_classification=write_path_classification, evidence_reinterpretation_check=reinterpretation,
        operational_isolation=isolation,
    )
    assert verdict["full_pass"] is True, verdict["failing_categories"]

    with Session(fixture_engine) as session:
        finalize = jsgv.finalize_stage_g(session, verdict=verdict)
    assert finalize["outcome"] == "FULLY_REPAIRED"
    assert finalize["boundary_deactivated"] is True

    with Session(fixture_engine) as session:
        post_sweep = j11_maintenance.capture_full_table_sweep(session)
        post_boundary_dump = migration.dump_table(fixture_engine, MaintenanceBoundary.__table__)
    post_write_accounting = jsgv.build_stage_g_cross_iteration_mutation_accounting(
        iter18_pre_stage_d_sweep=iter18_pre_stage_d_sweep, live_post_sweep=post_sweep,
        pre_maintenance_boundary_dump=pre_boundary_dump, post_maintenance_boundary_dump=post_boundary_dump,
        membership_timeline_row_deleted_this_iteration=False, boundary_deactivated_this_iteration=True,
    )
    assert post_write_accounting["ok"] is True, post_write_accounting["checks"]

    with Session(fixture_engine) as session:
        boundary_row = session.exec(select(MaintenanceBoundary)).first()
    assert boundary_row.active is False
