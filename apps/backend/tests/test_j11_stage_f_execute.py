"""goal-market-compass iter-21 -- J-11 Stage F EXECUTION tests (TC-1 through TC-12, TC-16 from the phase
spec's TESTING REQUIREMENTS; TC-13/TC-14/TC-15/TC-17/TC-18/TC-19 live in the CLI-script test file / are
proven by grep in the dev handoff).

File-scoped, fixture-DB-only (fresh `sqlite://` engine, `SQLModel.metadata.create_all`) -- the SAME
pattern `test_j11_stage_e_execute.py` uses, never `loaded_engine` and never `apps/backend/data/trendora.db`.
"""
from __future__ import annotations

import ast
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import load_config
from app.engine import data_manager
from app.engine import j11_stage_f_execute as jsfe
from app.engine import research
from app.engine.j11_maintenance import INCIDENT_DATES
from app.models import (
    AvailabilityCache,
    CoverageSnapshot,
    DailyPrice,
    EventStudyCache,
    ForwardAggregateCache,
    ForwardReturn,
    IndexSeriesCache,
    MarketPhaseCache,
    MembershipTimelineCache,
    NextSessionManifest,
    ScannerResult,
    ScannerRun,
)

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

BACKEND_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = BACKEND_DIR / "app" / "engine" / "j11_stage_f_execute.py"
CLI_SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_stage_f_execute.py"

EARLY = datetime(2020, 1, 1, tzinfo=timezone.utc)  # "created well before any repair" -- past the fixture's
# own Stage D start instant in every test below unless a test deliberately constructs a LATE row.


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


# --- shared fixture helpers (mirrors test_j11_stage_e_execute.py's idiom) --------------------------


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


def _mk_event_study_row(session, *, dataset_version, created_at=EARLY, subject="AAA", view="episodes", asof_key="all", horizon=5):
    row = EventStudyCache(subject=subject, view=view, asof_key=asof_key, dataset_version=dataset_version, horizon=horizon, payload_json="{}", created_at=created_at)
    session.add(row); session.flush(); return row


def _mk_market_phase_row(session, *, dataset_version, created_at=EARLY, asof_key="2026-01-01"):
    row = MarketPhaseCache(asof_key=asof_key, dataset_version=dataset_version, payload_json="{}", created_at=created_at)
    session.add(row); session.flush(); return row


def _mk_forward_aggregate_row(session, *, dataset_version, created_at=EARLY, horizon=5, asof_key="2026-01-01"):
    row = ForwardAggregateCache(horizon=horizon, asof_key=asof_key, dataset_version=dataset_version, payload_json="{}", created_at=created_at)
    session.add(row); session.flush(); return row


def _mk_index_series_row(session, *, dataset_version, created_at=EARLY, range_key="all", full=True):
    row = IndexSeriesCache(range_key=range_key, full=full, dataset_version=dataset_version, payload_json="{}", created_at=created_at)
    session.add(row); session.flush(); return row


def _mk_membership_timeline_row(session, *, dataset_version, created_at=EARLY, points=None):
    payload = {"candidate_pool_count": 1, "points": points or [], "labels": {}}
    row = MembershipTimelineCache(dataset_version=dataset_version, payload_json=json.dumps(payload), created_at=created_at)
    session.add(row); session.flush(); return row


def _mk_availability_row(session, *, dataset_version, created_at=EARLY):
    payload = {"total_symbols": 3, "trading_day_count": 1, "cells": [{"date": "2026-01-01", "symbols_with_bars": 3, "total_symbols": 3, "snapshot_exists": True}]}
    row = AvailabilityCache(dataset_version=dataset_version, payload_json=json.dumps(payload), created_at=created_at)
    session.add(row); session.flush(); return row


def _mk_coverage_snapshot_row(session, *, dataset_version, computed_at=EARLY, asof_key="2026-01-01"):
    row = CoverageSnapshot(asof_key=asof_key, dataset_version=dataset_version, payload_json="{}", computed_at=computed_at)
    session.add(row); session.flush(); return row


# =======================================================================================================
# TC-19-style static proof: zero network-capable call appears anywhere in the diff
# =======================================================================================================

_NETWORK_TOKENS = ("requests", "httpx", "urllib", "socket", "yfinance", "aiohttp", "http.client")


def _imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_module_imports_no_network_capable_library():
    assert not (_imported_roots(MODULE_PATH) & set(_NETWORK_TOKENS))


def test_cli_script_imports_no_network_capable_library():
    assert not (_imported_roots(CLI_SCRIPT_PATH) & set(_NETWORK_TOKENS))


def test_module_never_modifies_a_canonical_producer_or_serving_function():
    """Static proof this module contains no `def compute_` / `def _compute_` definition of its own for
    any of the seven canonical derivations it composes -- it only READS them (docs/goal.md OUT OF SCOPE:
    'Stage F composes and reads them as-is')."""
    tree = ast.parse(MODULE_PATH.read_text())
    defined_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    forbidden = {
        "compute_event_study", "compute_market_phase", "compute_forward_aggregates",
        "_membership_timeline", "compute_availability", "_compute_coverage_uncached", "compute_index_series",
    }
    assert not (defined_names & forbidden)


# =======================================================================================================
# TC-3 -- genuine runtime introspection, never a hardcoded list
# =======================================================================================================


def test_tc3_inventory_matches_live_seven_tables():
    inv = jsfe.derive_cache_table_inventory()
    assert inv["table_count"] == 7
    assert inv["table_names"] == sorted(jsfe.EXPECTED_CACHE_TABLE_NAMES)
    assert inv["matches_expected_seven"] is True


def test_tc3_injecting_different_metadata_changes_the_returned_set():
    """Proves `derive_cache_table_inventory` is genuine introspection, not a hardcoded list wearing an
    introspection costume: a FRESH, independent `MetaData` containing only a synthetic 8th
    `dataset_version`-bearing table (and no real cache table at all) makes the function return THAT set,
    not the real seven."""
    from sqlalchemy import Column, Integer, MetaData, String, Table

    synthetic_md = MetaData()
    Table(
        "eighth_synthetic_cache", synthetic_md,
        Column("id", Integer, primary_key=True),
        Column("dataset_version", String),
    )
    Table(
        "unrelated_table_no_stamp", synthetic_md,
        Column("id", Integer, primary_key=True),
        Column("name", String),
    )

    inv = jsfe.derive_cache_table_inventory(metadata=synthetic_md)
    assert inv["table_names"] == ["eighth_synthetic_cache"]
    assert inv["table_count"] == 1
    assert inv["matches_expected_seven"] is False


# =======================================================================================================
# confirm_stage_e_complete_and_unrestamped
# =======================================================================================================


def test_stage_e_check_ok_when_present_matching_id_identity_and_exact_forward_return_count(engine):
    with Session(engine) as session:
        run = _mk_run(session, date(2026, 5, 12), engine_identity_value="frozen-id")
        _mk_forward_return(session, run, "AAA", horizon=1)
        _mk_forward_return(session, run, "AAA", horizon=5)
        session.commit()
        run_id = run.id
        check = jsfe.confirm_stage_e_complete_and_unrestamped(
            session,
            expected_run_id_by_date={"2026-05-12": run_id},
            expected_forward_return_count_by_run_id={str(run_id): 2},
            frozen_engine_identity="frozen-id",
        )
    assert check["ok"] is True
    assert check["per_date"]["2026-05-12"]["forward_return_count_matches"] is True


def test_stage_e_check_accepts_a_legitimate_zero_count_never_treats_it_as_a_gap(engine):
    """Mirrors run 3158's own recorded outcome (0 forward returns -- sitting on the frontier)."""
    with Session(engine) as session:
        run = _mk_run(session, date(2026, 8, 12), engine_identity_value="frozen-id")
        session.commit()
        run_id = run.id
        check = jsfe.confirm_stage_e_complete_and_unrestamped(
            session,
            expected_run_id_by_date={"2026-08-12": run_id},
            expected_forward_return_count_by_run_id={str(run_id): 0},
            frozen_engine_identity="frozen-id",
        )
    assert check["ok"] is True
    assert check["per_date"]["2026-08-12"]["observed_forward_return_count"] == 0


def test_stage_e_check_fails_when_run_missing(engine):
    with Session(engine) as session:
        check = jsfe.confirm_stage_e_complete_and_unrestamped(
            session, expected_run_id_by_date={"2026-05-12": 999},
            expected_forward_return_count_by_run_id={"999": 0}, frozen_engine_identity="frozen-id",
        )
    assert check["ok"] is False
    assert check["per_date"]["2026-05-12"]["present"] is False


def test_stage_e_check_fails_when_id_does_not_match_expected(engine):
    with Session(engine) as session:
        run = _mk_run(session, date(2026, 5, 12), engine_identity_value="frozen-id")
        session.commit()
        check = jsfe.confirm_stage_e_complete_and_unrestamped(
            session, expected_run_id_by_date={"2026-05-12": run.id + 999},
            expected_forward_return_count_by_run_id={str(run.id + 999): 0}, frozen_engine_identity="frozen-id",
        )
    assert check["ok"] is False


def test_stage_e_check_fails_when_identity_does_not_match(engine):
    with Session(engine) as session:
        run = _mk_run(session, date(2026, 5, 12), engine_identity_value="drifted-id")
        session.commit()
        check = jsfe.confirm_stage_e_complete_and_unrestamped(
            session, expected_run_id_by_date={"2026-05-12": run.id},
            expected_forward_return_count_by_run_id={str(run.id): 0}, frozen_engine_identity="frozen-id",
        )
    assert check["ok"] is False
    assert check["per_date"]["2026-05-12"]["identity_matches"] is False


def test_stage_e_check_fails_when_forward_return_count_mismatched(engine):
    with Session(engine) as session:
        run = _mk_run(session, date(2026, 5, 12), engine_identity_value="frozen-id")
        _mk_forward_return(session, run, "AAA", horizon=1)
        session.commit()
        check = jsfe.confirm_stage_e_complete_and_unrestamped(
            session, expected_run_id_by_date={"2026-05-12": run.id},
            expected_forward_return_count_by_run_id={str(run.id): 999}, frozen_engine_identity="frozen-id",
        )
    assert check["ok"] is False
    assert check["per_date"]["2026-05-12"]["forward_return_count_matches"] is False


def test_stage_e_check_fails_closed_on_empty_expected_map(engine):
    with Session(engine) as session:
        check = jsfe.confirm_stage_e_complete_and_unrestamped(
            session, expected_run_id_by_date={}, expected_forward_return_count_by_run_id={}, frozen_engine_identity="x",
        )
    assert check["ok"] is False


# =======================================================================================================
# derive_stage_d_execution_start_instant
# =======================================================================================================


def test_derive_stage_d_start_instant_is_min_created_at_over_given_ids_only(engine):
    with Session(engine) as session:
        early = datetime(2026, 1, 1, tzinfo=timezone.utc)
        mid = datetime(2026, 1, 2, tzinfo=timezone.utc)
        late = datetime(2026, 1, 3, tzinfo=timezone.utc)
        r1 = _mk_run(session, date(2026, 1, 1), created_at=mid)
        r2 = _mk_run(session, date(2026, 1, 2), created_at=early)
        r3_not_in_set = _mk_run(session, date(2026, 1, 3), created_at=datetime(2020, 1, 1, tzinfo=timezone.utc))
        session.commit()
        r1_id, r2_id, r3_id = r1.id, r2.id, r3_not_in_set.id
        result = jsfe.derive_stage_d_execution_start_instant(session, [r1_id, r2_id])
    assert result["stage_d_execution_start_instant"] == early.isoformat()
    assert r3_id not in result["incident_run_ids"]


# =======================================================================================================
# capture_cache_table_snapshot -- generic across created_at / computed_at
# =======================================================================================================


def test_snapshot_reads_created_at_column_for_event_study_cache(engine):
    with Session(engine) as session:
        _mk_event_study_row(session, dataset_version="r1-f0", created_at=EARLY)
        _mk_event_study_row(session, dataset_version="r2-f0", created_at=EARLY + timedelta(days=1), subject="BBB")
        session.commit()
        snap = jsfe.capture_cache_table_snapshot(session, "event_study_cache")
    assert snap["timestamp_column"] == "created_at"
    assert snap["row_count"] == 2
    assert {s["dataset_version"] for s in snap["distinct_stamps"]} == {"r1-f0", "r2-f0"}
    assert snap["max_timestamp"] == (EARLY + timedelta(days=1)).isoformat()


def test_snapshot_reads_computed_at_column_for_coverage_snapshot(engine):
    with Session(engine) as session:
        _mk_coverage_snapshot_row(session, dataset_version="r1-x", computed_at=EARLY)
        session.commit()
        snap = jsfe.capture_cache_table_snapshot(session, "coverage_snapshot")
    assert snap["timestamp_column"] == "computed_at"
    assert snap["row_count"] == 1
    assert snap["max_timestamp"] == EARLY.isoformat()


def test_snapshot_honest_empty_on_zero_rows(engine):
    with Session(engine) as session:
        snap = jsfe.capture_cache_table_snapshot(session, "availability_cache")
    assert snap["row_count"] == 0
    assert snap["distinct_stamps"] == []
    assert snap["max_timestamp"] is None


# =======================================================================================================
# confirm_no_cache_row_at_or_after_stage_d_start -- the "gravest" check
# =======================================================================================================


def test_late_row_check_ok_when_every_table_predates_stage_d_start(engine):
    with Session(engine) as session:
        _mk_event_study_row(session, dataset_version="r1-f0", created_at=EARLY)
        _mk_availability_row(session, dataset_version="r1-x", created_at=EARLY)
        session.commit()
        snapshots = {
            "event_study_cache": jsfe.capture_cache_table_snapshot(session, "event_study_cache"),
            "availability_cache": jsfe.capture_cache_table_snapshot(session, "availability_cache"),
        }
    check = jsfe.confirm_no_cache_row_at_or_after_stage_d_start(
        snapshots, stage_d_start_instant=datetime(2026, 8, 26, tzinfo=timezone.utc),
    )
    assert check["ok"] is True


def test_late_row_check_fails_when_one_table_has_a_row_at_or_after_stage_d_start(engine):
    """Mutation-check: this MUST be able to fail -- a row created exactly AT the cutoff instant is a
    real, live-computed violation, not a construction-time tautology."""
    cutoff = datetime(2026, 8, 26, tzinfo=timezone.utc)
    with Session(engine) as session:
        _mk_event_study_row(session, dataset_version="r1-f0", created_at=EARLY)
        _mk_availability_row(session, dataset_version="r1-x", created_at=cutoff)  # AT the cutoff -- not strictly before
        session.commit()
        snapshots = {
            "event_study_cache": jsfe.capture_cache_table_snapshot(session, "event_study_cache"),
            "availability_cache": jsfe.capture_cache_table_snapshot(session, "availability_cache"),
        }
    check = jsfe.confirm_no_cache_row_at_or_after_stage_d_start(snapshots, stage_d_start_instant=cutoff)
    assert check["ok"] is False
    assert check["per_table"]["availability_cache"]["ok"] is False
    assert check["per_table"]["event_study_cache"]["ok"] is True


def test_late_row_check_fails_closed_on_empty_snapshots():
    check = jsfe.confirm_no_cache_row_at_or_after_stage_d_start({}, stage_d_start_instant=datetime.now(timezone.utc))
    assert check["ok"] is False


# =======================================================================================================
# stage_f_preflight_gate_verdict -- each of the six checks independently gates `proceed`
# =======================================================================================================


@pytest.mark.parametrize(
    "boundary_ok, stage_e_ok, identity_ok, manifest_ok, inventory_ok, late_rows_ok, expected",
    [
        (True, True, True, True, True, True, True),
        (False, True, True, True, True, True, False),
        (True, False, True, True, True, True, False),
        (True, True, False, True, True, True, False),
        (True, True, True, False, True, True, False),
        (True, True, True, True, False, True, False),
        (True, True, True, True, True, False, False),
    ],
)
def test_preflight_gate_requires_all_six_checks(boundary_ok, stage_e_ok, identity_ok, manifest_ok, inventory_ok, late_rows_ok, expected):
    verdict = jsfe.stage_f_preflight_gate_verdict(
        boundary_recheck={"ok": boundary_ok},
        stage_e_check={"ok": stage_e_ok},
        identity_check={"ok": identity_ok},
        manifest_check={"ok": manifest_ok},
        inventory={"matches_expected_seven": inventory_ok, "table_names": []},
        late_rows_check={"ok": late_rows_ok},
    )
    assert verdict["proceed"] is expected
    if not expected:
        assert verdict["blocking_reasons"]


# =======================================================================================================
# classify_cache_table -- TC-4/TC-5 (broad + narrow default-delete families)
# =======================================================================================================


def test_tc4_broad_family_table_with_stale_stamp_classified_explicit_delete(engine, cfg):
    with Session(engine) as session:
        # seed an OLD population, capture that stamp, seed a cache row under it, then GROW the population
        # so the live stamp moves past it (mirrors the real r{max_id}-f{count} progression).
        old_run = _mk_run(session, date(2026, 1, 1))
        session.commit()
        stale_stamp = research._dataset_version(session)
        _mk_event_study_row(session, dataset_version=stale_stamp, created_at=EARLY)
        _mk_run(session, date(2026, 1, 2))
        session.commit()
        live_stamp = research._dataset_version(session)
        assert live_stamp != stale_stamp

        record = jsfe.classify_cache_table(
            session, cfg, "event_study_cache", stage_d_start_instant=datetime(2026, 8, 26, tzinfo=timezone.utc),
        )
    assert record["disposition"] == "explicit_delete"
    assert record["live_stamp"] == live_stamp
    assert record["stamp_matches_live"] is False
    assert record["all_rows_created_before_stage_d_start"] is True


def test_tc5_narrow_family_table_with_stale_stamp_classified_explicit_delete(engine, cfg):
    with Session(engine) as session:
        old_run = _mk_run(session, date(2026, 1, 1))
        session.commit()
        stale_stamp = research._membership_dataset_version(session, cfg)
        _mk_availability_row(session, dataset_version=stale_stamp, created_at=EARLY)
        _mk_run(session, date(2026, 1, 2))
        session.commit()
        live_stamp = research._membership_dataset_version(session, cfg)
        assert live_stamp != stale_stamp

        record = jsfe.classify_cache_table(
            session, cfg, "availability_cache", stage_d_start_instant=datetime(2026, 8, 26, tzinfo=timezone.utc),
        )
    assert record["disposition"] == "explicit_delete"
    assert record["stamp_matches_live"] is False


def test_narrow_family_coverage_snapshot_also_classified_explicit_delete(engine, cfg):
    with Session(engine) as session:
        _mk_run(session, date(2026, 1, 1))
        session.commit()
        stale_stamp = research._membership_dataset_version(session, cfg)
        _mk_coverage_snapshot_row(session, dataset_version=stale_stamp, computed_at=EARLY)
        _mk_run(session, date(2026, 1, 2))
        session.commit()
        record = jsfe.classify_cache_table(
            session, cfg, "coverage_snapshot", stage_d_start_instant=datetime(2026, 8, 26, tzinfo=timezone.utc),
        )
    assert record["disposition"] == "explicit_delete"


def test_classify_zero_rows_table_is_still_explicit_delete_but_trivially_so(engine, cfg):
    with Session(engine) as session:
        record = jsfe.classify_cache_table(
            session, cfg, "market_phase_cache", stage_d_start_instant=datetime(2026, 8, 26, tzinfo=timezone.utc),
        )
    assert record["disposition"] == "explicit_delete"
    assert record["snapshot"]["row_count"] == 0


def test_classify_unknown_table_name_is_unclassified(engine, cfg):
    with Session(engine) as session:
        record = jsfe.classify_cache_table(
            session, cfg, "some_future_cache_table", stage_d_start_instant=datetime(2026, 8, 26, tzinfo=timezone.utc),
        )
    assert record["disposition"] == "unclassified_unknown_family"


def test_classify_blocks_when_a_row_is_at_or_after_stage_d_start(engine, cfg):
    """Mutation-check: `classify_cache_table`'s own late-row branch (defense-in-depth alongside the
    preflight's own check) must independently be able to fire."""
    cutoff = datetime(2026, 8, 26, tzinfo=timezone.utc)
    with Session(engine) as session:
        _mk_run(session, date(2026, 1, 1))
        session.commit()
        live_stamp = research._dataset_version(session)
        _mk_event_study_row(session, dataset_version=live_stamp + "-old", created_at=cutoff + timedelta(seconds=1))
        session.commit()
        record = jsfe.classify_cache_table(session, cfg, "event_study_cache", stage_d_start_instant=cutoff)
    assert record["disposition"] == "blocked_late_row_detected"
    assert record["all_rows_created_before_stage_d_start"] is False


# =======================================================================================================
# classify_cache_table -- TC-6 (index_series_cache proven unaffected)
# =======================================================================================================


def test_tc6_index_series_cache_stamp_matches_prove_unaffected(engine, cfg):
    with Session(engine) as session:
        _mk_prices(session, "SPY", date(2026, 1, 1), 5)
        session.commit()
        from app.engine import indexes
        live_stamp = indexes.index_series_dataset_version(session, cfg)
        _mk_index_series_row(session, dataset_version=live_stamp, created_at=EARLY)
        session.commit()

        record = jsfe.classify_cache_table(
            session, cfg, "index_series_cache", stage_d_start_instant=datetime(2026, 8, 26, tzinfo=timezone.utc),
        )
    assert record["disposition"] == "prove_unaffected_leave_alone"
    assert record["stamp_matches_live"] is True


def test_index_series_cache_stamp_mismatch_falls_back_to_explicit_delete(engine, cfg):
    """Mutation-check: if daily_prices somehow DID move (a scenario this iteration must never allow, but
    the classifier must not silently trust a mismatched stamp), the safe fallback is deletion, never
    'leave alone' by default."""
    with Session(engine) as session:
        _mk_prices(session, "SPY", date(2026, 1, 1), 5)
        session.commit()
        _mk_index_series_row(session, dataset_version="stale-stamp-that-cannot-match", created_at=EARLY)
        session.commit()

        record = jsfe.classify_cache_table(
            session, cfg, "index_series_cache", stage_d_start_instant=datetime(2026, 8, 26, tzinfo=timezone.utc),
        )
    assert record["disposition"] == "explicit_delete"


# =======================================================================================================
# TC-7 -- the collision trap: identical stamp string via delete-and-recreate, caught by created_at
# =======================================================================================================


def test_tc7_stamp_collision_still_classified_stale_via_created_at(engine, cfg):
    with Session(engine) as session:
        r1 = _mk_run(session, date(2020, 1, 1))
        r2 = _mk_run(session, date(2020, 1, 2))
        session.commit()
        stamp_before_repair = research._dataset_version(session)

        # a cache row genuinely computed BEFORE the "repair" -- well before the repair-start instant.
        _mk_event_study_row(session, dataset_version=stamp_before_repair, created_at=EARLY)
        session.commit()

        repair_start = datetime(2026, 8, 26, 10, 0, 0, tzinfo=timezone.utc)

        # the "repair": delete both runs, then recreate two runs -- SQLite's rowid-alias reuse (no
        # AUTOINCREMENT) reproduces the SAME max(id) and hence the SAME r{id}-f{count} stamp string.
        session.delete(session.get(ScannerRun, r1.id))
        session.delete(session.get(ScannerRun, r2.id))
        session.commit()
        r3 = _mk_run(session, date(2020, 2, 1), created_at=repair_start + timedelta(seconds=1))
        r4 = _mk_run(session, date(2020, 2, 2), created_at=repair_start + timedelta(seconds=2))
        session.commit()
        stamp_after_repair = research._dataset_version(session)

        assert stamp_after_repair == stamp_before_repair, "fixture must reproduce a genuine stamp collision"

        record = jsfe.classify_cache_table(session, cfg, "event_study_cache", stage_d_start_instant=repair_start)

    # the pure stamp-string comparison alone would report a match...
    assert record["stamp_matches_live"] is True
    # ...but the created_at comparison against the repair-start instant proves the row predates the
    # repair, and the COMBINED disposition is still explicit_delete -- proving created_at, not the stamp
    # string, is the decisive signal.
    assert record["disposition"] == "explicit_delete"
    assert record["all_rows_created_before_stage_d_start"] is True


# =======================================================================================================
# membership_timeline_cache -- TC-9, the one genuine tradeoff
# =======================================================================================================


def test_tc9_membership_timeline_safe_branch_preserves(engine, cfg):
    with Session(engine) as session:
        # two already-cached, already-snapshotted historical dates...
        _mk_run(session, date(2020, 1, 1))
        _mk_run(session, date(2020, 1, 2))
        session.commit()
        prev_stamp = research._membership_dataset_version(session, cfg)
        points = [{"date": "2020-01-01", "size": 1, "entries": [], "exits": [], "excluded": {}},
                  {"date": "2020-01-02", "size": 1, "entries": [], "exits": [], "excluded": {}}]
        _mk_membership_timeline_row(session, dataset_version=prev_stamp, created_at=EARLY, points=points)
        session.commit()

        # ...then a NEW date is added HISTORICALLY EARLIER than the cached tail (2020-01-01, i.e. before
        # the cached max 2020-01-02) with NO bars added at all (daily_prices untouched) -- the exact
        # "historical gap-insert, bars unchanged" shape J-11's own incident dates exhibit.
        _mk_run(session, date(2019, 12, 31))
        session.commit()

        record = jsfe.classify_cache_table(
            session, cfg, "membership_timeline_cache", stage_d_start_instant=datetime(2026, 8, 26, tzinfo=timezone.utc),
        )
    assert record["disposition"] == "preserve_for_incremental_reuse"
    assert record["membership_reuse_evaluation"]["safe_for_incremental_reuse"] is True
    assert record["membership_reuse_evaluation"]["append_forward"] is False


def test_tc9_membership_timeline_append_forward_case_falls_back_to_delete(engine, cfg):
    """An append-forward-eligible date pattern (the new date is STRICTLY LATER than every cached date) is
    the narrower fast path, not the 'historical gap-insert' branch this disposition specifically
    requires -- must fall back to explicit_delete, never silently preserved."""
    with Session(engine) as session:
        _mk_run(session, date(2020, 1, 1))
        session.commit()
        prev_stamp = research._membership_dataset_version(session, cfg)
        points = [{"date": "2020-01-01", "size": 1, "entries": [], "exits": [], "excluded": {}}]
        _mk_membership_timeline_row(session, dataset_version=prev_stamp, created_at=EARLY, points=points)
        session.commit()

        _mk_run(session, date(2020, 1, 2))  # strictly LATER than the cached tail
        session.commit()

        record = jsfe.classify_cache_table(
            session, cfg, "membership_timeline_cache", stage_d_start_instant=datetime(2026, 8, 26, tzinfo=timezone.utc),
        )
    assert record["membership_reuse_evaluation"]["append_forward"] is True
    assert record["membership_reuse_evaluation"]["safe_for_incremental_reuse"] is False
    assert record["disposition"] == "explicit_delete"


def test_membership_timeline_missing_date_falls_back_to_delete(engine, cfg):
    with Session(engine) as session:
        _mk_run(session, date(2020, 1, 1))
        session.commit()
        prev_stamp = research._membership_dataset_version(session, cfg)
        points = [
            {"date": "2019-12-01", "size": 1, "entries": [], "exits": [], "excluded": {}},
            {"date": "2020-01-01", "size": 1, "entries": [], "exits": [], "excluded": {}},
        ]
        _mk_membership_timeline_row(session, dataset_version=prev_stamp, created_at=EARLY, points=points)
        session.commit()
        # the run for 2019-12-01 was never created live -- its cached date is now "missing" live.

        record = jsfe.classify_cache_table(
            session, cfg, "membership_timeline_cache", stage_d_start_instant=datetime(2026, 8, 26, tzinfo=timezone.utc),
        )
    assert record["membership_reuse_evaluation"]["missing_dates"] == ["2019-12-01"]
    assert record["disposition"] == "explicit_delete"


def test_membership_timeline_zero_stored_rows_is_explicit_delete(engine, cfg):
    with Session(engine) as session:
        record = jsfe.classify_cache_table(
            session, cfg, "membership_timeline_cache", stage_d_start_instant=datetime(2026, 8, 26, tzinfo=timezone.utc),
        )
    assert record["disposition"] == "explicit_delete"
    assert record["membership_reuse_evaluation"] is None


# =======================================================================================================
# execute_stage_f_cache_disposition -- TC-8, the ONE authorized write
# =======================================================================================================


def test_tc8_execution_deletes_exactly_explicit_delete_tables(engine, cfg):
    with Session(engine) as session:
        _mk_event_study_row(session, dataset_version="stale")
        _mk_event_study_row(session, dataset_version="stale2", subject="BBB")
        _mk_index_series_row(session, dataset_version="fresh")
        session.commit()

        dispositions = {
            "event_study_cache": {"disposition": "explicit_delete", "snapshot": {"row_count": 2}},
            "index_series_cache": {"disposition": "prove_unaffected_leave_alone", "snapshot": {"row_count": 1}},
        }
        result = jsfe.execute_stage_f_cache_disposition(session, dispositions=dispositions)

    assert result["per_table"]["event_study_cache"]["rows_deleted"] == 2
    assert result["per_table"]["index_series_cache"]["attempted_write"] is False
    assert result["total_rows_deleted"] == 2

    with Session(engine) as session:
        remaining_event_study = session.exec(select(EventStudyCache)).all()
        assert remaining_event_study == []
        remaining_index = session.exec(select(IndexSeriesCache)).all()
        assert len(remaining_index) == 1
        assert remaining_index[0].dataset_version == "fresh"


def test_live_verify_ok_true_when_deleted_empty_and_preserved_unchanged(engine, cfg):
    with Session(engine) as session:
        _mk_index_series_row(session, dataset_version="fresh")
        session.commit()
        dispositions = {
            "event_study_cache": {"disposition": "explicit_delete", "snapshot": {"row_count": 0}},
            "index_series_cache": {"disposition": "prove_unaffected_leave_alone", "snapshot": {"row_count": 1}},
        }
        check = jsfe.live_verify_cache_dispositions(session, dispositions=dispositions)
    assert check["ok"] is True


def test_live_verify_fails_when_a_deleted_table_still_has_rows(engine, cfg):
    """Mutation-check: proves this function can genuinely fail (e.g. a buggy execution left a row behind)."""
    with Session(engine) as session:
        _mk_event_study_row(session, dataset_version="leftover")
        session.commit()
        dispositions = {"event_study_cache": {"disposition": "explicit_delete", "snapshot": {"row_count": 1}}}
        check = jsfe.live_verify_cache_dispositions(session, dispositions=dispositions)
    assert check["ok"] is False
    assert check["per_table"]["event_study_cache"]["ok"] is False


def test_live_verify_fails_when_a_preserved_table_count_changed(engine, cfg):
    with Session(engine) as session:
        _mk_index_series_row(session, dataset_version="fresh")
        _mk_index_series_row(session, dataset_version="fresh2", range_key="3M")
        session.commit()
        dispositions = {"index_series_cache": {"disposition": "prove_unaffected_leave_alone", "snapshot": {"row_count": 1}}}
        check = jsfe.live_verify_cache_dispositions(session, dispositions=dispositions)
    assert check["ok"] is False


# =======================================================================================================
# TC-10 -- the correctness payoff: availability_from_storage never serves a stale payload post-deletion
# =======================================================================================================


def test_tc10_availability_from_storage_honest_after_deletion(engine, cfg):
    with Session(engine) as session:
        _mk_availability_row(session, dataset_version="stale-pre-incident-stamp", created_at=EARLY)
        session.commit()

        # sanity: BEFORE deletion, the documented risk is real -- a stamp-mismatched row with no ingest
        # job in flight is served with stale: False (the bug this iteration exists to close).
        before = data_manager.availability_from_storage(session, cfg)
        assert before["stale"] is False
        assert before["served_dataset_version"] == "stale-pre-incident-stamp"

        dispositions = {"availability_cache": {"disposition": "explicit_delete", "snapshot": {"row_count": 1}}}
        jsfe.execute_stage_f_cache_disposition(session, dispositions=dispositions)

        after = data_manager.availability_from_storage(session, cfg)
    assert after == data_manager._availability_not_yet_computed_payload()
    assert after["stale"] is False
    assert after["served_dataset_version"] is None
    assert after["cells"] == []


# =======================================================================================================
# build_stage_f_mutation_accounting -- TC-11/TC-12
# =======================================================================================================


def _table_sweep(names_and_counts: dict[str, int]) -> dict:
    per_table = {name: {"count": n, "min_rowid": 1 if n else None, "max_rowid": n or None, "sum_rowid": n or None, "fingerprint": f"fp-{name}-{n}"} for name, n in names_and_counts.items()}
    return {"captured_at": "t", "table_names": sorted(names_and_counts), "table_count": len(names_and_counts), "per_table": per_table}


def test_mutation_accounting_all_pass_when_only_explicit_delete_tables_changed():
    pre = _table_sweep({"event_study_cache": 5, "daily_prices": 100, "index_series_cache": 1})
    post = _table_sweep({"event_study_cache": 0, "daily_prices": 100, "index_series_cache": 1})
    dispositions = {
        "event_study_cache": {"disposition": "explicit_delete"},
        "index_series_cache": {"disposition": "prove_unaffected_leave_alone"},
    }
    accounting = jsfe.build_stage_f_mutation_accounting(
        pre_full_table_sweep=pre, post_full_table_sweep=post, dispositions=dispositions,
        pre_manifest_dump=[{"id": 1}], post_manifest_dump=[{"id": 1}],
        pre_daily_prices={"fingerprint": "x"}, post_daily_prices={"fingerprint": "x"},
        pre_provider_runs={"count": 0, "ids": []}, post_provider_runs={"count": 0, "ids": []},
        pre_watchlist={"count": 0, "ids": []}, post_watchlist={"count": 0, "ids": []},
        pre_maintenance_boundary_dump=[{"id": 1, "active": 1}], post_maintenance_boundary_dump=[{"id": 1, "active": 1}],
        db_file_true_start={}, db_file_true_end={},
    )
    assert accounting["all_checks_pass"] is True
    assert accounting["explicit_delete_tables"] == ["event_study_cache"]


def test_mutation_accounting_fails_when_an_out_of_scope_table_changed():
    pre = _table_sweep({"event_study_cache": 5, "daily_prices": 100})
    post = _table_sweep({"event_study_cache": 0, "daily_prices": 101})  # daily_prices MOVED -- forbidden
    dispositions = {"event_study_cache": {"disposition": "explicit_delete"}}
    accounting = jsfe.build_stage_f_mutation_accounting(
        pre_full_table_sweep=pre, post_full_table_sweep=post, dispositions=dispositions,
        pre_manifest_dump=[], post_manifest_dump=[],
        pre_daily_prices={"fingerprint": "x"}, post_daily_prices={"fingerprint": "x"},
        pre_provider_runs={}, post_provider_runs={}, pre_watchlist={}, post_watchlist={},
        pre_maintenance_boundary_dump=[], post_maintenance_boundary_dump=[],
        db_file_true_start={}, db_file_true_end={},
    )
    assert accounting["all_checks_pass"] is False
    assert accounting["checks"]["out_of_scope_tables_zero_fingerprint_change"] is False


def test_mutation_accounting_fails_when_a_preserved_cache_table_changed():
    """A cache table classified anything OTHER than explicit_delete must ALSO show zero fingerprint
    change -- proves preserved tables (index_series_cache / a preserved membership_timeline_cache) are
    protected too, not just the ten canonical J-11 tables."""
    pre = _table_sweep({"index_series_cache": 1})
    post = _table_sweep({"index_series_cache": 2})  # changed despite being "preserved"
    dispositions = {"index_series_cache": {"disposition": "prove_unaffected_leave_alone"}}
    accounting = jsfe.build_stage_f_mutation_accounting(
        pre_full_table_sweep=pre, post_full_table_sweep=post, dispositions=dispositions,
        pre_manifest_dump=[], post_manifest_dump=[],
        pre_daily_prices={"fingerprint": "x"}, post_daily_prices={"fingerprint": "x"},
        pre_provider_runs={}, post_provider_runs={}, pre_watchlist={}, post_watchlist={},
        pre_maintenance_boundary_dump=[], post_maintenance_boundary_dump=[],
        db_file_true_start={}, db_file_true_end={},
    )
    assert accounting["all_checks_pass"] is False
    assert accounting["checks"]["out_of_scope_tables_zero_fingerprint_change"] is False


def test_mutation_accounting_fails_when_a_wholly_unrelated_table_changed():
    """Isolates `changed_tables_subset_of_explicit_delete_set` from `out_of_scope_tables_zero_
    fingerprint_change`: a table that is NEITHER one of the ten named OUT_OF_SCOPE_TABLES NOR any of the
    seven cache tables in `dispositions` at all (e.g. `stocks`) still must not be allowed to change
    unnoticed. This is the ONE check with unique coverage for that case -- proven here by mutation-check:
    hardwiring `changed_tables_subset_of_explicit_delete_set = True` while leaving every other check
    untouched makes THIS test (and only this test, among the mutation-accounting suite) go green when it
    should not, which is exactly why this test exists as its own scenario rather than folding into the
    two above."""
    pre = _table_sweep({"event_study_cache": 5, "stocks": 500})
    post = _table_sweep({"event_study_cache": 0, "stocks": 501})  # `stocks` is in NEITHER protected set
    dispositions = {"event_study_cache": {"disposition": "explicit_delete"}}
    accounting = jsfe.build_stage_f_mutation_accounting(
        pre_full_table_sweep=pre, post_full_table_sweep=post, dispositions=dispositions,
        pre_manifest_dump=[], post_manifest_dump=[],
        pre_daily_prices={"fingerprint": "x"}, post_daily_prices={"fingerprint": "x"},
        pre_provider_runs={}, post_provider_runs={}, pre_watchlist={}, post_watchlist={},
        pre_maintenance_boundary_dump=[], post_maintenance_boundary_dump=[],
        db_file_true_start={}, db_file_true_end={},
    )
    assert accounting["checks"]["out_of_scope_tables_zero_fingerprint_change"] is True  # stocks isn't tracked there
    assert accounting["checks"]["changed_tables_subset_of_explicit_delete_set"] is False  # but IS caught here
    assert accounting["all_checks_pass"] is False


def test_mutation_accounting_fails_when_manifests_changed():
    pre = _table_sweep({"event_study_cache": 5})
    post = _table_sweep({"event_study_cache": 0})
    dispositions = {"event_study_cache": {"disposition": "explicit_delete"}}
    accounting = jsfe.build_stage_f_mutation_accounting(
        pre_full_table_sweep=pre, post_full_table_sweep=post, dispositions=dispositions,
        pre_manifest_dump=[{"id": 1, "content_hash": "a"}], post_manifest_dump=[{"id": 1, "content_hash": "CHANGED"}],
        pre_daily_prices={"fingerprint": "x"}, post_daily_prices={"fingerprint": "x"},
        pre_provider_runs={}, post_provider_runs={}, pre_watchlist={}, post_watchlist={},
        pre_maintenance_boundary_dump=[], post_maintenance_boundary_dump=[],
        db_file_true_start={}, db_file_true_end={},
    )
    assert accounting["all_checks_pass"] is False
    assert accounting["checks"]["manifests_unchanged"] is False


# =======================================================================================================
# stage_f_execution_outcome -- no invented third state
# =======================================================================================================


@pytest.mark.parametrize(
    "gate_proceed, dispositions, execution, verification, accounting, expected_executed, expected_reason",
    [
        (False, None, None, None, None, False, "preflight_gate_did_not_proceed"),
        (True, {}, None, None, None, False, "no_dispositions_computed"),
        (True, {"x": {"disposition": "blocked_late_row_detected"}}, None, None, None, False, "unresolved_table_classification"),
        (True, {"x": {"disposition": "explicit_delete"}}, None, None, None, False, "no_execution_attempted"),
        (True, {"x": {"disposition": "explicit_delete"}}, {}, {"ok": False}, None, False, "post_execution_live_verification_failed"),
        (True, {"x": {"disposition": "explicit_delete"}}, {}, {"ok": True}, {"all_checks_pass": False}, False, "post_execution_mutation_accounting_failed"),
        (True, {"x": {"disposition": "explicit_delete"}}, {}, {"ok": True}, {"all_checks_pass": True}, True, "cache_dispositions_classified_applied_and_verified"),
    ],
)
def test_execution_outcome_exact_reason(gate_proceed, dispositions, execution, verification, accounting, expected_executed, expected_reason):
    outcome = jsfe.stage_f_execution_outcome(
        preflight_gate={"proceed": gate_proceed, "blocking_reasons": [] if gate_proceed else ["x"]},
        dispositions=dispositions, execution_result=execution, verification_result=verification,
        mutation_accounting=accounting,
    )
    assert outcome["executed"] is expected_executed
    assert outcome["reason"] == expected_reason


# =======================================================================================================
# TC-15-style full end-to-end fixture, via app.db.make_engine
# =======================================================================================================


def test_full_end_to_end_stage_f_shaped_fixture_via_make_engine(tmp_path, cfg):
    from app.db import create_db_and_tables, make_engine
    from app.engine import j11_stage_d_execute as jsde
    from app.engine import j11_preboot_guard as guard

    db_path = tmp_path / "stage_f_execute_fixture.db"
    fixture_engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(fixture_engine)

    frozen_identity = "fixture-frozen-identity"
    with Session(fixture_engine) as session:
        guard.register_boundary(session, name="j11-incident-recovery", dates=INCIDENT_DATES, reason="fixture", active=True)

        earliest = min(INCIDENT_DATES)
        latest = max(INCIDENT_DATES)
        _mk_prices(session, "AAA", earliest - timedelta(days=10), 200)

        # index_series_cache's own narrow stamp depends only on daily_prices (untouched by this fixture's
        # ScannerRun-only writes below), so it is computed ONCE, up front, and the stored row is seeded
        # with that SAME value -- proving it stays unaffected exactly as J-11's real run does.
        from app.engine import indexes
        index_stamp = indexes.index_series_dataset_version(session, cfg)

        # the LATEST incident date's run is created FIRST and its own narrow membership stamp captured
        # immediately after -- this is the "cached tail" a real pre-Stage-D membership_timeline_cache row
        # would already include. The remaining ten incident dates (all EARLIER than this tail) are then
        # added, reproducing the exact "historical gap-insert, bars unchanged" shape J-11's real incident
        # dates exhibit (append_forward requires the new dates to be LATER than the tail -- here they are
        # all earlier, so append_forward must evaluate False; see evaluate_membership_timeline_incremental_
        # reuse_safety).
        expected_run_id_by_date: dict[str, int] = {}
        expected_fr_count_by_run_id: dict[str, int] = {}
        created_at = datetime(2026, 8, 26, 10, 53, tzinfo=timezone.utc)

        latest_run = _mk_run(session, latest, engine_identity_value=frozen_identity, created_at=created_at)
        _mk_result(session, latest_run, "AAA")
        expected_run_id_by_date[latest.isoformat()] = latest_run.id
        expected_fr_count_by_run_id[str(latest_run.id)] = 0
        session.flush()

        membership_stamp = research._membership_dataset_version(session, cfg)
        membership_points = [{"date": latest.isoformat(), "size": 1, "entries": ["AAA"], "exits": [], "excluded": {}}]

        # a stale, pre-repair cache row in each of the five default-delete families + the one deliberately
        # preservable membership_timeline_cache row, all seeded BEFORE the remaining ten incident dates
        # are created (so their created_at genuinely predates the "repair").
        _mk_event_study_row(session, dataset_version="stale-broad", created_at=EARLY)
        _mk_market_phase_row(session, dataset_version="stale-broad", created_at=EARLY)
        _mk_forward_aggregate_row(session, dataset_version="stale-broad", created_at=EARLY)
        _mk_availability_row(session, dataset_version="stale-narrow", created_at=EARLY)
        _mk_coverage_snapshot_row(session, dataset_version="stale-narrow", computed_at=EARLY)
        _mk_index_series_row(session, dataset_version=index_stamp, created_at=EARLY)
        _mk_membership_timeline_row(session, dataset_version=membership_stamp, created_at=EARLY, points=membership_points)
        session.commit()

        for one_date in INCIDENT_DATES:
            if one_date == latest:
                continue
            run = _mk_run(session, one_date, engine_identity_value=frozen_identity, created_at=created_at)
            _mk_result(session, run, "AAA")
            expected_run_id_by_date[one_date.isoformat()] = run.id
            expected_fr_count_by_run_id[str(run.id)] = 0  # zero forward returns in this minimal fixture
        session.commit()

        certified_manifest_dump: list = []

    with Session(fixture_engine) as session:
        boundary_recheck = jsde.recheck_maintenance_boundary_and_guard(session)
    assert boundary_recheck["ok"] is True

    with Session(fixture_engine) as session:
        stage_e_check = jsfe.confirm_stage_e_complete_and_unrestamped(
            session, expected_run_id_by_date=expected_run_id_by_date,
            expected_forward_return_count_by_run_id=expected_fr_count_by_run_id,
            frozen_engine_identity=frozen_identity,
        )
    assert stage_e_check["ok"] is True

    from app.engine import j11_stage_e_execute as jsee
    identity_check = jsee.check_engine_identity_matches_stage_d(frozen_identity, frozen_identity)
    assert identity_check["ok"] is True

    from app.engine import j11_schema_migration as migration
    manifest_check = jsee.confirm_manifests_unchanged(fixture_engine, certified_manifest_dump=certified_manifest_dump)
    assert manifest_check["ok"] is True

    inventory = jsfe.derive_cache_table_inventory()
    assert inventory["matches_expected_seven"] is True

    with Session(fixture_engine) as session:
        incident_run_ids = sorted(expected_run_id_by_date.values())
        start_instant_result = jsfe.derive_stage_d_execution_start_instant(session, incident_run_ids)
        stage_d_start_instant = datetime.fromisoformat(start_instant_result["stage_d_execution_start_instant"])

        non_index_names = [n for n in inventory["table_names"] if n != "index_series_cache"]
        snapshots = {n: jsfe.capture_cache_table_snapshot(session, n) for n in non_index_names}
        late_rows_check = jsfe.confirm_no_cache_row_at_or_after_stage_d_start(snapshots, stage_d_start_instant=stage_d_start_instant)
    assert late_rows_check["ok"] is True

    gate = jsfe.stage_f_preflight_gate_verdict(
        boundary_recheck=boundary_recheck, stage_e_check=stage_e_check, identity_check=identity_check,
        manifest_check=manifest_check, inventory=inventory, late_rows_check=late_rows_check,
    )
    assert gate["proceed"] is True

    with Session(fixture_engine) as session:
        dispositions = {
            name: jsfe.classify_cache_table(session, cfg, name, stage_d_start_instant=stage_d_start_instant)
            for name in inventory["table_names"]
        }
    assert dispositions["event_study_cache"]["disposition"] == "explicit_delete"
    assert dispositions["market_phase_cache"]["disposition"] == "explicit_delete"
    assert dispositions["forward_aggregate_cache"]["disposition"] == "explicit_delete"
    assert dispositions["availability_cache"]["disposition"] == "explicit_delete"
    assert dispositions["coverage_snapshot"]["disposition"] == "explicit_delete"
    assert dispositions["index_series_cache"]["disposition"] == "prove_unaffected_leave_alone"
    assert dispositions["membership_timeline_cache"]["disposition"] == "preserve_for_incremental_reuse"

    from app.engine import j11_maintenance
    with Session(fixture_engine) as session:
        pre_sweep = j11_maintenance.capture_full_table_sweep(session)
        pre_manifest_dump = migration.dump_table(fixture_engine, NextSessionManifest.__table__)
        from app.models import DataProviderRun, MaintenanceBoundary, Watchlist
        from app.engine import j11_stage_c as jsc
        pre_provider_runs = jsc.small_table_id_snapshot(session, DataProviderRun)
        pre_watchlist = jsc.small_table_id_snapshot(session, Watchlist)
        pre_maintenance_boundary_dump = migration.dump_table(fixture_engine, MaintenanceBoundary.__table__)
        pre_daily_prices = j11_maintenance.capture_pre_reset_inventory(session)["daily_prices"]

        execution_result = jsfe.execute_stage_f_cache_disposition(session, dispositions=dispositions)

    with Session(fixture_engine) as session:
        verification_result = jsfe.live_verify_cache_dispositions(session, dispositions=dispositions)
    assert verification_result["ok"] is True

    with Session(fixture_engine) as session:
        post_sweep = j11_maintenance.capture_full_table_sweep(session)
        post_manifest_dump = migration.dump_table(fixture_engine, NextSessionManifest.__table__)
        post_provider_runs = jsc.small_table_id_snapshot(session, DataProviderRun)
        post_watchlist = jsc.small_table_id_snapshot(session, Watchlist)
        post_maintenance_boundary_dump = migration.dump_table(fixture_engine, MaintenanceBoundary.__table__)
        post_daily_prices = j11_maintenance.capture_pre_reset_inventory(session)["daily_prices"]

    mutation_accounting = jsfe.build_stage_f_mutation_accounting(
        pre_full_table_sweep=pre_sweep, post_full_table_sweep=post_sweep, dispositions=dispositions,
        pre_manifest_dump=pre_manifest_dump, post_manifest_dump=post_manifest_dump,
        pre_daily_prices=pre_daily_prices, post_daily_prices=post_daily_prices,
        pre_provider_runs=pre_provider_runs, post_provider_runs=post_provider_runs,
        pre_watchlist=pre_watchlist, post_watchlist=post_watchlist,
        pre_maintenance_boundary_dump=pre_maintenance_boundary_dump, post_maintenance_boundary_dump=post_maintenance_boundary_dump,
        db_file_true_start={}, db_file_true_end={},
    )
    assert mutation_accounting["all_checks_pass"] is True, mutation_accounting["checks"]

    outcome = jsfe.stage_f_execution_outcome(
        preflight_gate=gate, dispositions=dispositions, execution_result=execution_result,
        verification_result=verification_result, mutation_accounting=mutation_accounting,
    )
    assert outcome["executed"] is True

    # the correctness payoff, exercised end-to-end: post-deletion, the serving function is honest.
    with Session(fixture_engine) as session:
        after = data_manager.availability_from_storage(session, cfg)
    assert after["stale"] is False
    assert after["served_dataset_version"] is None
