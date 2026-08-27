"""goal-market-compass iter-20 -- J-11 Stage E EXECUTION tests (TC-1 through TC-9, TC-12, TC-15, TC-16
from the phase spec's TESTING REQUIREMENTS; TC-10/TC-11/TC-13/TC-14/TC-17/TC-18/TC-19/TC-20 live in the
CLI-script test file / are proven by grep in the dev handoff).

File-scoped, fixture-DB-only (fresh `sqlite://` engine, `SQLModel.metadata.create_all`) -- the SAME
pattern `test_j11_stage_d_execute.py` uses, never `loaded_engine` and never `apps/backend/data/trendora.db`.

`scanner.run_scan`/`compute_run_payload` are NOT exercised here -- fixture `ScannerRun`/`ScannerResult`
rows are built directly (mirroring `test_j11_stage_d_execute.py`'s `_mk_run` idiom), so
`forward_testing.backfill_run_forward_returns` runs against real, small, hand-built price/snapshot data.
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
from app.engine import j11_stage_e_execute as jsee
from app.engine.j11_maintenance import INCIDENT_DATES
from app.models import DailyPrice, ForwardReturn, MaintenanceBoundary, NextSessionManifest, ScannerResult, ScannerRun

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

BACKEND_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = BACKEND_DIR / "app" / "engine" / "j11_stage_e_execute.py"
CLI_SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_stage_e_execute.py"


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


# --- shared fixture helpers -----------------------------------------------------------------------


def _mk_run(session: Session, asof: date, *, engine_identity_value: "str | None" = "stub-identity") -> ScannerRun:
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


def _mk_prices(session: Session, symbol: str, start: date, n_days: int, *, price: float = 100.0) -> None:
    """N consecutive calendar-day bars (fine for these fixture tests -- no trading-calendar gaps needed;
    forward_testing counts DISTINCT stored dates, not real trading-day semantics)."""
    d = start
    for i in range(n_days):
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


LOOP_DATES = INCIDENT_DATES[:2]  # a 2-date real-incident-date subset


# =======================================================================================================
# TC-3 -- static/import-level proof: backfill_forward_returns is NEVER imported or called
# =======================================================================================================


def _collect_all_identifiers(tree: ast.AST) -> set[str]:
    """Every `Name.id`, `Attribute.attr`, and `alias.name`/`alias.asname` in the file -- covers BOTH a
    direct `from ... import backfill_forward_returns` AND a `forward_testing.backfill_forward_returns(...)`
    attribute-call form. Deliberately walks the WHOLE tree, not just top-level `Import` nodes -- an
    attribute access is not an import statement."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.name)
                if alias.asname:
                    names.add(alias.asname)
    return names


def test_tc3_module_never_references_backfill_forward_returns():
    tree = ast.parse(MODULE_PATH.read_text())
    identifiers = _collect_all_identifiers(tree)
    assert "backfill_forward_returns" not in identifiers
    # sanity: the module DOES reference the correct, per-run, create-once sibling function
    assert "backfill_run_forward_returns" in identifiers


def test_tc3_cli_script_never_references_backfill_forward_returns():
    tree = ast.parse(CLI_SCRIPT_PATH.read_text())
    identifiers = _collect_all_identifiers(tree)
    assert "backfill_forward_returns" not in identifiers


# =======================================================================================================
# TC-20 -- static proof: zero network-capable call appears anywhere in the diff
# =======================================================================================================


_NETWORK_TOKENS = ("requests", "httpx", "urllib", "socket", "yfinance", "aiohttp", "http.client")


def test_tc20_module_imports_no_network_capable_library():
    tree = ast.parse(MODULE_PATH.read_text())
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    assert not (imported_roots & set(_NETWORK_TOKENS))


def test_tc20_cli_script_imports_no_network_capable_library():
    tree = ast.parse(CLI_SCRIPT_PATH.read_text())
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    assert not (imported_roots & set(_NETWORK_TOKENS))


# =======================================================================================================
# recheck reuse -- confirm the module reuses j11_stage_d_execute's function rather than reimplementing it
# =======================================================================================================


def test_reuses_stage_d_boundary_recheck_never_reimplements_it():
    """Neither the module nor the CLI script may DEFINE a competing
    `recheck_maintenance_boundary_and_guard` (that would be reimplementation), but the reused identifier
    must be REFERENCED somewhere across the Stage E deliverable (module + CLI script) -- whichever file
    actually calls into `j11_stage_d_execute`'s already-built function, per the plan's Alignment check."""
    module_source = MODULE_PATH.read_text()
    cli_source = CLI_SCRIPT_PATH.read_text()
    assert "def recheck_maintenance_boundary_and_guard(" not in module_source
    assert "def recheck_maintenance_boundary_and_guard(" not in cli_source

    module_identifiers = _collect_all_identifiers(ast.parse(module_source))
    cli_identifiers = _collect_all_identifiers(ast.parse(cli_source))
    assert "recheck_maintenance_boundary_and_guard" in (module_identifiers | cli_identifiers)


# =======================================================================================================
# confirm_stage_d_runs_present_unrestamped
# =======================================================================================================


def test_runs_check_ok_when_present_matching_id_and_identity_and_zero_forward_returns(engine):
    with Session(engine) as session:
        run = _mk_run(session, LOOP_DATES[0], engine_identity_value="53d2ffd1...")
        session.commit()
        run_id = run.id

    with Session(engine) as session:
        result = jsee.confirm_stage_d_runs_present_unrestamped(
            session,
            expected_run_id_by_date={LOOP_DATES[0].isoformat(): run_id},
            frozen_engine_identity="53d2ffd1...",
        )
    assert result["ok"] is True
    entry = result["per_date"][LOOP_DATES[0].isoformat()]
    assert entry["present"] is True
    assert entry["id_matches"] is True
    assert entry["identity_matches"] is True
    assert entry["zero_forward_returns"] is True


def test_runs_check_fails_when_run_missing(engine):
    with Session(engine) as session:
        result = jsee.confirm_stage_d_runs_present_unrestamped(
            session,
            expected_run_id_by_date={LOOP_DATES[0].isoformat(): 999},
            frozen_engine_identity="53d2ffd1...",
        )
    assert result["ok"] is False
    assert result["per_date"][LOOP_DATES[0].isoformat()]["present"] is False


def test_runs_check_fails_when_id_does_not_match_expected(engine):
    """A different id at the same asof_date than Stage D recorded -- the row was deleted and recreated
    since Stage D, even if its engine_identity happens to match (the exact 'restamped' trap)."""
    with Session(engine) as session:
        run = _mk_run(session, LOOP_DATES[0], engine_identity_value="53d2ffd1...")
        session.commit()
        real_id = run.id

    with Session(engine) as session:
        result = jsee.confirm_stage_d_runs_present_unrestamped(
            session,
            expected_run_id_by_date={LOOP_DATES[0].isoformat(): real_id + 1000},  # wrong expected id
            frozen_engine_identity="53d2ffd1...",
        )
    assert result["ok"] is False
    assert result["per_date"][LOOP_DATES[0].isoformat()]["id_matches"] is False


def test_runs_check_fails_when_identity_does_not_match(engine):
    with Session(engine) as session:
        run = _mk_run(session, LOOP_DATES[0], engine_identity_value="some-other-identity")
        session.commit()
        run_id = run.id

    with Session(engine) as session:
        result = jsee.confirm_stage_d_runs_present_unrestamped(
            session,
            expected_run_id_by_date={LOOP_DATES[0].isoformat(): run_id},
            frozen_engine_identity="53d2ffd1...",  # does not match the row's stamped identity
        )
    assert result["ok"] is False
    entry = result["per_date"][LOOP_DATES[0].isoformat()]
    assert entry["present"] is True
    assert entry["id_matches"] is True
    assert entry["identity_matches"] is False


def test_runs_check_fails_when_forward_return_already_present(engine):
    with Session(engine) as session:
        run = _mk_run(session, LOOP_DATES[0], engine_identity_value="53d2ffd1...")
        session.flush()
        session.add(ForwardReturn(
            run_id=run.id, symbol="AAA", horizon=5, asof_date=LOOP_DATES[0],
            entry_close=100.0, measured_date=LOOP_DATES[0] + timedelta(days=10), realized_return=0.01,
        ))
        session.commit()
        run_id = run.id

    with Session(engine) as session:
        result = jsee.confirm_stage_d_runs_present_unrestamped(
            session,
            expected_run_id_by_date={LOOP_DATES[0].isoformat(): run_id},
            frozen_engine_identity="53d2ffd1...",
        )
    assert result["ok"] is False
    entry = result["per_date"][LOOP_DATES[0].isoformat()]
    assert entry["zero_forward_returns"] is False
    assert entry["forward_return_count"] == 1


# =======================================================================================================
# check_engine_identity_matches_stage_d
# =======================================================================================================


def test_identity_check_ok_when_equal():
    result = jsee.check_engine_identity_matches_stage_d("abc123", "abc123")
    assert result["ok"] is True
    assert result["matches"] is True


def test_identity_check_fails_when_different_stated_honestly_both_ways():
    result = jsee.check_engine_identity_matches_stage_d("abc123", "def456")
    assert result["ok"] is False
    assert result["fresh_engine_identity"] == "abc123"
    assert result["stage_d_frozen_engine_identity"] == "def456"


def test_identity_check_fails_when_historical_value_missing():
    result = jsee.check_engine_identity_matches_stage_d("abc123", None)
    assert result["ok"] is False


# =======================================================================================================
# confirm_manifests_unchanged
# =======================================================================================================


def test_manifest_check_ok_when_live_dump_matches_certified(engine):
    with Session(engine) as session:
        run = _mk_run(session, date(2029, 12, 1))
        _mk_manifest(session, run)
        session.commit()

    from app.engine import j11_schema_migration as migration
    live_dump = migration.dump_table(engine, NextSessionManifest.__table__)

    result = jsee.confirm_manifests_unchanged(engine, certified_manifest_dump=live_dump)
    assert result["ok"] is True
    assert result["live_row_count"] == 1


def test_manifest_check_fails_when_live_dump_diverges_from_certified(engine):
    with Session(engine) as session:
        run = _mk_run(session, date(2029, 12, 1))
        _mk_manifest(session, run)
        session.commit()

    result = jsee.confirm_manifests_unchanged(engine, certified_manifest_dump=[])  # certified says 0 rows
    assert result["ok"] is False
    assert result["diff"]["equal"] is False


# =======================================================================================================
# stage_e_preflight_gate_verdict
# =======================================================================================================


@pytest.mark.parametrize(
    "boundary_ok,runs_ok,identity_ok,manifest_ok,expected",
    [
        (True, True, True, True, True),
        (False, True, True, True, False),
        (True, False, True, True, False),
        (True, True, False, True, False),
        (True, True, True, False, False),
    ],
)
def test_preflight_gate_requires_all_four_checks(boundary_ok, runs_ok, identity_ok, manifest_ok, expected):
    verdict = jsee.stage_e_preflight_gate_verdict(
        boundary_recheck={"ok": boundary_ok}, runs_check={"ok": runs_ok},
        identity_check={"ok": identity_ok}, manifest_check={"ok": manifest_ok},
    )
    assert verdict["proceed"] is expected
    if not expected:
        assert verdict["blocking_reasons"]


# =======================================================================================================
# TC-5, TC-6, TC-8 -- the three-population classification, TC-4/TC-7 -- byte-unchanged proofs
# =======================================================================================================


def test_tc5_tc8_repair_loop_fills_rebuilt_run_visits_retained_and_leaves_immature_absent(engine, cfg):
    """A Stage-D-shaped fixture: one 'rebuilt incident' run (an INCIDENT_DATES member, zero ForwardReturn
    rows to start), one RETAINED (non-incident) run, and the frontier (latest) run whose horizons are all
    not-yet-mature. Reproduces TC-5 and TC-8 end-to-end; TC-6's retained-run REFILL is covered separately
    by `test_tc6_retained_run_incident_dated_hole_is_refilled_and_reported_in_population_b`."""
    incident_asof = LOOP_DATES[0]
    retained_asof = incident_asof - timedelta(days=40)  # earlier -- a RETAINED (non-incident) run
    frontier_asof = date(2030, 6, 1)  # the LATEST run in the fixture -- no post-snapshot bars at all

    with Session(engine) as session:
        # enough daily bars for AAA/SPY spanning both runs' as-of dates and forward windows
        _mk_prices(session, "AAA", retained_asof - timedelta(days=5), 400)
        _mk_prices(session, "SPY", retained_asof - timedelta(days=5), 400)

        incident_run = _mk_run(session, incident_asof, engine_identity_value="53d2ffd1...")
        _mk_result(session, incident_run, "AAA")
        retained_run = _mk_run(session, retained_asof, engine_identity_value="6261ca17...")
        _mk_result(session, retained_run, "AAA")
        frontier_run = _mk_run(session, frontier_asof, engine_identity_value="53d2ffd1...")
        _mk_result(session, frontier_run, "AAA")
        session.commit()
        incident_run_id, retained_run_id, frontier_run_id = incident_run.id, retained_run.id, frontier_run.id

    with Session(engine) as session:
        result = jsee.execute_stage_e_repair_loop(session, cfg, pool_symbols={"AAA"})

    assert result["total_runs_processed"] == 3
    per_run = {r["run_id"]: r for r in result["per_run_results"]}
    # TC-5: the incident run started at zero and should now carry newly-inserted rows (AAA has 400 days
    # of history from retained_asof - 5d, so several configured horizons are elapsed for both runs).
    assert per_run[incident_run_id]["rows_inserted"] > 0
    assert per_run[incident_run_id]["classification"] == "rebuilt_incident_run"
    # This fixture's retained run is only proven to be VISITED and CLASSIFIED -- it pre-deletes nothing,
    # so a create-once no-op here is indistinguishable from "already complete", and the live iter-20 run
    # inserted zero retained-run rows (no retained-run hole was possible -- see the dev handoff), so the
    # live evidence does not exercise the fill path either. TC-6's actual REFILL behaviour is proven by
    # `test_tc6_retained_run_incident_dated_hole_is_refilled_and_reported_in_population_b` below, which
    # constructs a genuine deleted-row hole and asserts it comes back.
    assert per_run[retained_run_id]["classification"] == "retained_run"
    # TC-8: the frontier run (latest asof in the WHOLE table) has zero observable post-snapshot days ->
    # zero rows inserted for it, never fabricated.
    assert per_run[frontier_run_id]["rows_inserted"] == 0

    with Session(engine) as session:
        frontier_fr_count = len(session.exec(select(ForwardReturn).where(ForwardReturn.run_id == frontier_run_id)).all())
    assert frontier_fr_count == 0  # TC-8: genuinely immature -> zero rows, never fabricated


def test_tc6_retained_run_incident_dated_hole_is_refilled_and_reported_in_population_b(engine, cfg):
    """TC-6, proven on a GENUINE hole rather than a create-once no-op (iter-20 audit finding T1).

    Two RETAINED (non-incident) runs are fully backfilled, then ONE incident-dated `ForwardReturn` row is
    DELETED to manufacture exactly the defensive-sweep hole shape `docs/goal.md` step 5's population (b)
    names. The second retained run keeps its own incident-dated row so `capture_retained_incident_hole_counts`
    returns a NON-EMPTY pre-map -- without that, `population_b_never_decreased` is vacuously true over an
    empty mapping and proves nothing. Asserts the deleted row actually comes back, that the loop's own
    `rows_inserted_on_retained_runs` counter is genuinely non-zero (never hardwired), and that population
    B's live post-total grew against a real, non-empty pre-total.

    With `_mk_prices`'s consecutive-calendar-day bars, horizon 5 off 2026-05-07/2026-05-08 measures into
    2026-05-12/2026-05-13 -- the first two real `INCIDENT_DATES` members."""
    incident_a, incident_b = INCIDENT_DATES[0], INCIDENT_DATES[1]
    retained_a_asof = incident_a - timedelta(days=5)   # h=5 -> measured_date == incident_a
    retained_b_asof = incident_b - timedelta(days=5)   # h=5 -> measured_date == incident_b

    with Session(engine) as session:
        _mk_prices(session, "AAA", retained_a_asof - timedelta(days=5), 200)
        retained_a = _mk_run(session, retained_a_asof, engine_identity_value="6261ca17...")
        _mk_result(session, retained_a, "AAA")
        retained_b = _mk_run(session, retained_b_asof, engine_identity_value="6261ca17...")
        _mk_result(session, retained_b, "AAA")
        session.commit()
        retained_a_id, retained_b_id = retained_a.id, retained_b.id

    # 1) fully backfill both retained runs through the module's own loop (idempotent, create-once).
    with Session(engine) as session:
        jsee.execute_stage_e_repair_loop(session, cfg, pool_symbols={"AAA"})

    # 2) manufacture the hole: delete retained_a's incident-dated row (what the incident cascade's
    #    defensive sweep did), leaving retained_b's intact so the pre-map is non-empty.
    with Session(engine) as session:
        hole_row = session.exec(
            select(ForwardReturn).where(
                ForwardReturn.run_id == retained_a_id, ForwardReturn.symbol == "AAA", ForwardReturn.horizon == 5
            )
        ).one()
        assert hole_row.measured_date == incident_a  # the fixture geometry really does land on an incident date
        session.delete(hole_row)
        session.commit()

    with Session(engine) as session:
        pre_holes = jsee.capture_retained_incident_hole_counts(session, incident_run_ids=[])
    assert pre_holes["per_run_id_counts"] == {retained_b_id: 1}, "pre-map must be NON-empty, else never_decreased is vacuous"
    assert pre_holes["total"] == 1

    # 3) re-run the repair loop -- the create-once path must refill exactly the deleted row.
    with Session(engine) as session:
        result = jsee.execute_stage_e_repair_loop(session, cfg, pool_symbols={"AAA"})
    per_run = {r["run_id"]: r for r in result["per_run_results"]}
    assert per_run[retained_a_id]["classification"] == "retained_run"
    assert per_run[retained_a_id]["rows_inserted"] == 1
    assert per_run[retained_b_id]["rows_inserted"] == 0  # already complete -> create-once inserts nothing
    assert result["rows_inserted_on_retained_runs"] == 1  # the retained-run counter is real, not hardwired 0
    assert result["rows_inserted_on_rebuilt_incident_runs"] == 0

    # 4) the row is back, and population B reports the growth against the real, non-empty pre-map.
    with Session(engine) as session:
        refilled = session.exec(
            select(ForwardReturn).where(
                ForwardReturn.run_id == retained_a_id, ForwardReturn.symbol == "AAA", ForwardReturn.horizon == 5
            )
        ).one()
        assert refilled.measured_date == incident_a
        report = jsee.live_verify_three_populations(
            session, incident_run_ids=[], pre_retained_hole_counts_by_run=pre_holes["per_run_id_counts"],
        )
    pop_b = report["population_b_retained_run_holes"]
    assert pop_b["pre_total"] == 1
    assert pop_b["post_total"] == 2, "the refilled hole must show up in population B's live post-count"
    assert pop_b["post_by_run_id"] == {retained_a_id: 1, retained_b_id: 1}
    assert pop_b["never_decreased"] is True
    assert report["all_checks_pass"] is True


def test_tc7_preexisting_forward_return_rows_are_byte_unchanged_after_the_loop(engine, cfg):
    """A ForwardReturn row that already exists before Stage E runs (outside the two hole populations)
    must be byte-identical after -- the create-once guard never overwrites it."""
    asof = date(2020, 1, 1)
    with Session(engine) as session:
        _mk_prices(session, "AAA", asof - timedelta(days=5), 400)
        run = _mk_run(session, asof, engine_identity_value="53d2ffd1...")
        _mk_result(session, run, "AAA")
        session.flush()
        pre_existing = ForwardReturn(
            run_id=run.id, symbol="AAA", horizon=1, asof_date=asof,
            entry_close=100.0, measured_date=asof + timedelta(days=1), realized_return=0.0123,
            mae=-0.01, mfe=0.02, max_drawdown=-0.015, underwater_days=2, time_to_recover_days=3,
        )
        session.add(pre_existing)
        session.commit()
        run_id = run.id

    with Session(engine) as session:
        jsee.execute_stage_e_repair_loop(session, cfg, pool_symbols={"AAA"})

    with Session(engine) as session:
        row = session.exec(
            select(ForwardReturn).where(ForwardReturn.run_id == run_id, ForwardReturn.symbol == "AAA", ForwardReturn.horizon == 1)
        ).one()
        assert row.realized_return == 0.0123
        assert row.mae == -0.01
        assert row.mfe == 0.02
        assert row.max_drawdown == -0.015
        assert row.underwater_days == 2
        assert row.time_to_recover_days == 3


# =======================================================================================================
# execute_stage_e_repair_loop -- B4 hard assertion + ascending order
# =======================================================================================================


def test_repair_loop_processes_every_scanner_run_row_ascending_asof_date(engine, cfg):
    with Session(engine) as session:
        _mk_prices(session, "AAA", date(2019, 1, 1), 10)
        for i, d in enumerate([date(2020, 3, 1), date(2020, 1, 1), date(2020, 2, 1)]):
            run = _mk_run(session, d)
            _mk_result(session, run, "AAA")
        session.commit()

    with Session(engine) as session:
        result = jsee.execute_stage_e_repair_loop(session, cfg, pool_symbols={"AAA"})

    dates_seen = [r["asof_date"] for r in result["per_run_results"]]
    assert dates_seen == sorted(dates_seen)
    assert result["total_runs_processed"] == 3


# =======================================================================================================
# live_verify_three_populations
# =======================================================================================================


def test_live_population_verification_all_pass_on_clean_fixture(engine, cfg):
    asof = date(2020, 1, 1)
    with Session(engine) as session:
        _mk_prices(session, "AAA", asof - timedelta(days=5), 200)
        run = _mk_run(session, asof, engine_identity_value="53d2ffd1...")
        _mk_result(session, run, "AAA")
        session.commit()
        run_id = run.id

    with Session(engine) as session:
        jsee.execute_stage_e_repair_loop(session, cfg, pool_symbols={"AAA"})

    with Session(engine) as session:
        report = jsee.live_verify_three_populations(
            session, incident_run_ids=[run_id], pre_retained_hole_counts_by_run={},
        )
    assert report["all_checks_pass"] is True
    assert report["population_a_rebuilt_incident_runs"][str(run_id)]["newly_inserted"] > 0


def test_live_population_verification_fails_when_retained_hole_count_decreased(engine, cfg):
    with Session(engine) as session:
        report = jsee.live_verify_three_populations(
            session, incident_run_ids=[], pre_retained_hole_counts_by_run={42: 5},  # no such rows exist now -> 0 < 5
        )
    assert report["all_checks_pass"] is False
    assert report["population_b_retained_run_holes"]["never_decreased"] is False


# =======================================================================================================
# memory measurement (TC-11)
# =======================================================================================================


def test_vm_peak_reads_own_process_status():
    value = jsee.read_process_vm_peak_kb()
    assert value is None or value > 0


def test_vm_peak_none_on_nonexistent_pid():
    assert jsee.read_process_vm_peak_kb(pid=999999999) is None


def test_build_memory_check_within_cap():
    result = jsee.build_memory_check(vm_peak_kb=1_000_000, memory_cap_mb=8192)
    assert result["within_cap"] is True
    assert result["vm_peak_mb"] == 976.6


def test_build_memory_check_over_cap():
    result = jsee.build_memory_check(vm_peak_kb=9_000_000, memory_cap_mb=8192)
    assert result["within_cap"] is False


def test_build_memory_check_honest_none_on_unreadable():
    result = jsee.build_memory_check(vm_peak_kb=None, memory_cap_mb=8192)
    assert result["within_cap"] is False
    assert result["vm_peak_mb"] is None


# =======================================================================================================
# build_stage_e_mutation_accounting (TC-9, TC-12, TC-18) -- pure composition, synthetic dicts
# =======================================================================================================


def _base_sweep(table_fingerprints: dict) -> dict:
    return {"captured_at": "t", "table_names": list(table_fingerprints), "table_count": len(table_fingerprints),
            "per_table": {name: {"fingerprint": fp, "count": 0, "min_rowid": None, "max_rowid": None, "sum_rowid": None}
                          for name, fp in table_fingerprints.items()}}


def test_mutation_accounting_all_pass_when_only_forward_returns_changed():
    pre_sweep = _base_sweep({"forward_returns": "fp1", "scanner_runs": "fpA", "daily_prices": "fpB"})
    post_sweep = _base_sweep({"forward_returns": "fp2", "scanner_runs": "fpA", "daily_prices": "fpB"})
    scanner_fp = {"row_count": 1, "rows": [{"id": 1}], "fingerprint": "same"}
    small = {"count": 0, "ids": []}

    result = jsee.build_stage_e_mutation_accounting(
        pre_full_table_sweep=pre_sweep, post_full_table_sweep=post_sweep,
        pre_manifest_dump=[], post_manifest_dump=[],
        pre_all_scanner_run_fingerprint=scanner_fp, post_all_scanner_run_fingerprint=scanner_fp,
        pre_daily_prices={"fingerprint": "same"}, post_daily_prices={"fingerprint": "same"},
        pre_provider_runs=small, post_provider_runs=small,
        pre_watchlist=small, post_watchlist=small,
        pre_maintenance_boundary_dump=[], post_maintenance_boundary_dump=[],
        pre_forward_returns_count=100, post_forward_returns_count=142,
        self_reported_total_inserted=42,
        db_file_true_start={}, db_file_true_end={},
    )
    assert result["all_checks_pass"] is True


def test_mutation_accounting_fails_when_an_out_of_scope_table_changed():
    pre_sweep = _base_sweep({"forward_returns": "fp1", "scanner_runs": "fpA"})
    post_sweep = _base_sweep({"forward_returns": "fp2", "scanner_runs": "fpCHANGED"})
    scanner_fp = {"row_count": 1, "rows": [{"id": 1}], "fingerprint": "same"}
    small = {"count": 0, "ids": []}

    result = jsee.build_stage_e_mutation_accounting(
        pre_full_table_sweep=pre_sweep, post_full_table_sweep=post_sweep,
        pre_manifest_dump=[], post_manifest_dump=[],
        pre_all_scanner_run_fingerprint=scanner_fp, post_all_scanner_run_fingerprint=scanner_fp,
        pre_daily_prices={"fingerprint": "same"}, post_daily_prices={"fingerprint": "same"},
        pre_provider_runs=small, post_provider_runs=small,
        pre_watchlist=small, post_watchlist=small,
        pre_maintenance_boundary_dump=[], post_maintenance_boundary_dump=[],
        pre_forward_returns_count=100, post_forward_returns_count=142,
        self_reported_total_inserted=42,
        db_file_true_start={}, db_file_true_end={},
    )
    assert result["all_checks_pass"] is False
    assert result["checks"]["changed_tables_subset_of_stage_e_write_tables"] is False
    assert result["checks"]["out_of_scope_tables_zero_fingerprint_change"] is False


def test_tc12_mutation_accounting_fails_when_count_delta_does_not_reconcile():
    pre_sweep = _base_sweep({"forward_returns": "fp1"})
    post_sweep = _base_sweep({"forward_returns": "fp2"})
    scanner_fp = {"row_count": 0, "rows": [], "fingerprint": "same"}
    small = {"count": 0, "ids": []}

    result = jsee.build_stage_e_mutation_accounting(
        pre_full_table_sweep=pre_sweep, post_full_table_sweep=post_sweep,
        pre_manifest_dump=[], post_manifest_dump=[],
        pre_all_scanner_run_fingerprint=scanner_fp, post_all_scanner_run_fingerprint=scanner_fp,
        pre_daily_prices={"fingerprint": "same"}, post_daily_prices={"fingerprint": "same"},
        pre_provider_runs=small, post_provider_runs=small,
        pre_watchlist=small, post_watchlist=small,
        pre_maintenance_boundary_dump=[], post_maintenance_boundary_dump=[],
        pre_forward_returns_count=100, post_forward_returns_count=142,  # delta = 42
        self_reported_total_inserted=41,  # MISMATCH
        db_file_true_start={}, db_file_true_end={},
    )
    assert result["all_checks_pass"] is False
    assert result["checks"]["forward_returns_delta_reconciles_with_self_reported_total"] is False


def test_mutation_accounting_fails_when_manifests_changed():
    pre_sweep = _base_sweep({"forward_returns": "fp1"})
    post_sweep = _base_sweep({"forward_returns": "fp2"})
    scanner_fp = {"row_count": 0, "rows": [], "fingerprint": "same"}
    small = {"count": 0, "ids": []}

    result = jsee.build_stage_e_mutation_accounting(
        pre_full_table_sweep=pre_sweep, post_full_table_sweep=post_sweep,
        pre_manifest_dump=[{"id": 1, "version": 1}], post_manifest_dump=[{"id": 1, "version": 2}],
        pre_all_scanner_run_fingerprint=scanner_fp, post_all_scanner_run_fingerprint=scanner_fp,
        pre_daily_prices={"fingerprint": "same"}, post_daily_prices={"fingerprint": "same"},
        pre_provider_runs=small, post_provider_runs=small,
        pre_watchlist=small, post_watchlist=small,
        pre_maintenance_boundary_dump=[], post_maintenance_boundary_dump=[],
        pre_forward_returns_count=100, post_forward_returns_count=100,
        self_reported_total_inserted=0,
        db_file_true_start={}, db_file_true_end={},
    )
    assert result["all_checks_pass"] is False
    assert result["checks"]["manifests_unchanged"] is False


# =======================================================================================================
# stage_e_execution_outcome
# =======================================================================================================


def test_outcome_executed_true_only_when_every_stage_agrees():
    outcome = jsee.stage_e_execution_outcome(
        preflight_gate={"proceed": True},
        repair_loop_result={"total_rows_inserted": 5},
        population_verification={"all_checks_pass": True},
        mutation_accounting={"all_checks_pass": True},
    )
    assert outcome["executed"] is True


@pytest.mark.parametrize(
    "gate,loop,pop,accounting,expected_reason",
    [
        ({"proceed": False, "blocking_reasons": ["x"]}, None, None, None, "preflight_gate_did_not_proceed"),
        ({"proceed": True}, None, None, None, "no_repair_loop_attempted"),
        ({"proceed": True}, {}, {"all_checks_pass": False}, None, "live_population_verification_failed"),
        ({"proceed": True}, {}, {"all_checks_pass": True}, {"all_checks_pass": False}, "post_execution_mutation_accounting_failed"),
    ],
)
def test_outcome_executed_false_with_exact_reason(gate, loop, pop, accounting, expected_reason):
    outcome = jsee.stage_e_execution_outcome(
        preflight_gate=gate, repair_loop_result=loop,
        population_verification=pop, mutation_accounting=accounting,
    )
    assert outcome["executed"] is False
    assert outcome["reason"] == expected_reason


# =======================================================================================================
# TC-15 -- full end-to-end run against a Stage-D-shaped fixture via app.db.make_engine's isolated engine
# =======================================================================================================


def test_tc15_full_end_to_end_stage_d_shaped_fixture_via_make_engine(tmp_path, cfg):
    """A synthetic fixture DB (never `trendora.db`), built via `app.db.make_engine`: 11 incident dates
    each carrying a zero-ForwardReturn ScannerRun, one retained run, one genuinely-immature (frontier)
    run, and an active MaintenanceBoundary row scoped to exactly the 11 incident dates. Runs the
    execution module's own preflight + repair loop + live population verification end-to-end."""
    from app.db import create_db_and_tables, make_engine
    from app.engine import j11_stage_d_execute as jsde

    db_path = tmp_path / "stage_e_execute_fixture.db"
    fixture_engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(fixture_engine)

    frozen_identity = "fixture-frozen-identity"
    with Session(fixture_engine) as session:
        from app.engine import j11_preboot_guard as guard
        guard.register_boundary(session, name="j11-incident-recovery", dates=INCIDENT_DATES, reason="fixture", active=True)

        earliest = min(INCIDENT_DATES)
        _mk_prices(session, "AAA", earliest - timedelta(days=10), 200)

        expected_run_id_by_date: dict[str, int] = {}
        for one_date in INCIDENT_DATES:
            run = _mk_run(session, one_date, engine_identity_value=frozen_identity)
            _mk_result(session, run, "AAA")
            expected_run_id_by_date[one_date.isoformat()] = run.id
        retained_run = _mk_run(session, earliest - timedelta(days=5), engine_identity_value="legacy")
        _mk_result(session, retained_run, "AAA")
        frontier_run = _mk_run(session, date(2031, 1, 1), engine_identity_value=frozen_identity)  # immature
        _mk_result(session, frontier_run, "AAA")
        session.commit()
        incident_run_ids = sorted(expected_run_id_by_date.values())
        frontier_run_id = frontier_run.id

    with Session(fixture_engine) as session:
        boundary_recheck = jsde.recheck_maintenance_boundary_and_guard(session)
    assert boundary_recheck["ok"] is True

    with Session(fixture_engine) as session:
        runs_check = jsee.confirm_stage_d_runs_present_unrestamped(
            session, expected_run_id_by_date=expected_run_id_by_date, frozen_engine_identity=frozen_identity,
        )
    assert runs_check["ok"] is True

    from app.engine import j11_schema_migration as migration
    from app.models import NextSessionManifest
    certified_dump = migration.dump_table(fixture_engine, NextSessionManifest.__table__)
    manifest_check = jsee.confirm_manifests_unchanged(fixture_engine, certified_manifest_dump=certified_dump)
    assert manifest_check["ok"] is True  # nothing changed it since the dump was taken 2 lines above

    gate = jsee.stage_e_preflight_gate_verdict(
        boundary_recheck=boundary_recheck, runs_check=runs_check,
        identity_check=jsee.check_engine_identity_matches_stage_d(frozen_identity, frozen_identity),
        manifest_check=manifest_check,
    )
    assert gate["proceed"] is True

    with Session(fixture_engine) as session:
        pre_holes = jsee.capture_retained_incident_hole_counts(session, incident_run_ids=incident_run_ids)
        repair_result = jsee.execute_stage_e_repair_loop(session, cfg, pool_symbols={"AAA"})

    assert repair_result["total_runs_processed"] == len(INCIDENT_DATES) + 2
    assert repair_result["rows_inserted_on_rebuilt_incident_runs"] > 0

    with Session(fixture_engine) as session:
        population_report = jsee.live_verify_three_populations(
            session, incident_run_ids=incident_run_ids,
            pre_retained_hole_counts_by_run=pre_holes["per_run_id_counts"],
        )
    assert population_report["all_checks_pass"] is True
    # The retained run sits 5 days before the earliest incident date, so its horizon-5 row measures INTO
    # that incident date -- population B must actually SEE it, not just report a vacuously-true composite
    # (iter-20 review/QA MINOR: `all_checks_pass` alone passes for the wrong reason on an empty pre-map).
    assert population_report["population_b_retained_run_holes"]["post_total"] > 0

    with Session(fixture_engine) as session:
        frontier_fr_count = len(session.exec(select(ForwardReturn).where(ForwardReturn.run_id == frontier_run_id)).all())
    assert frontier_fr_count == 0  # TC-8 -- genuinely immature, never fabricated

    with Session(fixture_engine) as session:
        # zero ScannerRun/ScannerResult mutation: exactly the rows created above, none added/removed
        assert len(session.exec(select(ScannerRun)).all()) == len(INCIDENT_DATES) + 2
