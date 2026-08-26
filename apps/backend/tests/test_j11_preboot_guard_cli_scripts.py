"""goal-market-compass iter-17 -- CLI-script tests for the J-11 maintenance-boundary arm/disarm
entrypoints (`scripts/run_j11_maintenance_boundary_arm.py` / `_disarm.py`), covering the owner's TC-6
through TC-10 (docs/goal.md J-11 step 11, "OWNER RULING -- J-11 maintenance-boundary lifecycle
AUTHORIZED"). Exclusively fixture/temp-file SQLite databases -- `apps/backend/data/trendora.db` is never
opened, copied, or referenced anywhere in this file (maintenance isolation stays active; the arm/disarm
paths are proven on disposable state only, per the ruling's own instruction not to invoke either against
live-armed/live state this iteration).

Two test styles, mirroring `test_j11_stage_c_cli_script.py`'s established idiom:
  - `unittest.mock`-based control-flow tests (missing `--confirm` / missing `--database-url` / missing
    `--name`) -- prove NO database interaction of any kind occurs before the refusal, by mocking
    `make_engine`/`Session` and asserting they are never called;
  - real fixture-database tests (TC-6 through TC-10) -- a real temp-file SQLite database, actually
    executed through `main()`, then independently re-opened and inspected."""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import mock

import pytest
from sqlmodel import Session, select

BACKEND_DIR = Path(__file__).resolve().parents[1]
ARM_SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_maintenance_boundary_arm.py"
DISARM_SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_maintenance_boundary_disarm.py"

sys.path.insert(0, str(BACKEND_DIR))
from app.db import create_db_and_tables, make_engine  # noqa: E402
from app.engine import j11_maintenance as jm  # noqa: E402
from app.engine import j11_preboot_guard as guard  # noqa: E402
from app.models import DailyPrice, MaintenanceBoundary, ScannerRun, Watchlist  # noqa: E402


def _load_script_module(path: Path, name: str):
    """Loads the script as a REAL module object via `importlib` (mirrors `test_j11_stage_c_cli_script.py`
    exactly) so `monkeypatch.setattr(module, name, mock)` genuinely intercepts every call the script's
    top-level code makes -- never executes `main()` itself at import time."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def arm_ns():
    original_argv = sys.argv
    try:
        yield _load_script_module(ARM_SCRIPT_PATH, "run_j11_maintenance_boundary_arm_under_test")
    finally:
        sys.argv = original_argv
        sys.modules.pop("run_j11_maintenance_boundary_arm_under_test", None)


@pytest.fixture()
def disarm_ns():
    original_argv = sys.argv
    try:
        yield _load_script_module(DISARM_SCRIPT_PATH, "run_j11_maintenance_boundary_disarm_under_test")
    finally:
        sys.argv = original_argv
        sys.modules.pop("run_j11_maintenance_boundary_disarm_under_test", None)


def _fixture_db_url(tmp_path: Path, name: str = "fixture.db") -> tuple[str, Path]:
    db_path = tmp_path / name
    return f"sqlite:///{db_path}", db_path


# --- control-flow refusals (mock-based, mirrors test_j11_stage_c_cli_script.py) --------------------------


def test_arm_missing_confirm_never_touches_database(monkeypatch, arm_ns, capsys):
    mock_make_engine = mock.MagicMock(name="make_engine")
    monkeypatch.setattr(arm_ns, "make_engine", mock_make_engine)
    monkeypatch.setattr(sys, "argv", ["run_j11_maintenance_boundary_arm.py", "--database-url", "sqlite:///x.db"])

    exit_code = arm_ns.main()

    assert exit_code != 0
    mock_make_engine.assert_not_called()
    assert "--confirm" in capsys.readouterr().err


def test_arm_confirm_without_database_url_refuses(monkeypatch, arm_ns, capsys):
    mock_make_engine = mock.MagicMock(name="make_engine")
    monkeypatch.setattr(arm_ns, "make_engine", mock_make_engine)
    monkeypatch.setattr(sys, "argv", ["run_j11_maintenance_boundary_arm.py", "--confirm"])

    exit_code = arm_ns.main()

    assert exit_code != 0
    mock_make_engine.assert_not_called()
    assert "--database-url" in capsys.readouterr().err


def test_arm_refuses_when_c1_date_set_check_fails(monkeypatch, arm_ns, tmp_path, capsys):
    """A corrupted/disagreeing goal.md date-set check must refuse BEFORE any engine is constructed --
    requirement 4's "must validate the exact incident-date set"."""
    mock_make_engine = mock.MagicMock(name="make_engine")
    monkeypatch.setattr(arm_ns, "make_engine", mock_make_engine)
    monkeypatch.setattr(arm_ns.jsc, "read_goal_md_text", mock.MagicMock(return_value="not the real goal.md"))
    monkeypatch.setattr(
        arm_ns.jsc, "check_c1_date_set_boundary",
        mock.MagicMock(return_value={"ok": False, "extraction_error": "anchor not found"}),
    )
    db_url, _ = _fixture_db_url(tmp_path)
    monkeypatch.setattr(sys, "argv", ["run_j11_maintenance_boundary_arm.py", "--confirm", "--database-url", db_url])

    exit_code = arm_ns.main()

    assert exit_code != 0
    mock_make_engine.assert_not_called()


def test_disarm_missing_confirm_never_touches_database(monkeypatch, disarm_ns, capsys):
    mock_make_engine = mock.MagicMock(name="make_engine")
    monkeypatch.setattr(disarm_ns, "make_engine", mock_make_engine)
    monkeypatch.setattr(
        sys, "argv",
        ["run_j11_maintenance_boundary_disarm.py", "--database-url", "sqlite:///x.db", "--name", "b"],
    )

    exit_code = disarm_ns.main()

    assert exit_code != 0
    mock_make_engine.assert_not_called()


def test_disarm_confirm_and_url_without_name_refuses(monkeypatch, disarm_ns, tmp_path, capsys):
    mock_make_engine = mock.MagicMock(name="make_engine")
    monkeypatch.setattr(disarm_ns, "make_engine", mock_make_engine)
    db_url, _ = _fixture_db_url(tmp_path)
    monkeypatch.setattr(sys, "argv", ["run_j11_maintenance_boundary_disarm.py", "--confirm", "--database-url", db_url])

    exit_code = disarm_ns.main()

    assert exit_code != 0
    mock_make_engine.assert_not_called()
    assert "--name" in capsys.readouterr().err


# --- table-absent: refuse (arm) / no-op (disarm), no write of any kind ------------------------------------


def test_arm_refuses_when_table_absent_and_writes_nothing(tmp_path, capsys):
    db_url, db_path = _fixture_db_url(tmp_path, "no-tables.db")
    # No create_db_and_tables() call at all -- the file may not even exist yet.
    sys.argv = ["run_j11_maintenance_boundary_arm.py", "--confirm", "--database-url", db_url]
    ns = _load_script_module(ARM_SCRIPT_PATH, "run_j11_maintenance_boundary_arm_under_test_absent")
    try:
        exit_code = ns.main()
    finally:
        sys.modules.pop("run_j11_maintenance_boundary_arm_under_test_absent", None)

    assert exit_code != 0
    assert "does not exist" in capsys.readouterr().err
    if db_path.exists():
        with Session(make_engine(db_url)) as session:
            from sqlalchemy import inspect as sa_inspect
            assert not sa_inspect(session.get_bind()).has_table("maintenance_boundaries")


def test_disarm_is_noop_when_table_absent(tmp_path, capsys):
    db_url, db_path = _fixture_db_url(tmp_path, "no-tables.db")
    sys.argv = [
        "run_j11_maintenance_boundary_disarm.py", "--confirm", "--database-url", db_url, "--name", "anything",
    ]
    ns = _load_script_module(DISARM_SCRIPT_PATH, "run_j11_maintenance_boundary_disarm_under_test_absent")
    try:
        exit_code = ns.main()
    finally:
        sys.modules.pop("run_j11_maintenance_boundary_disarm_under_test_absent", None)

    assert exit_code == 0
    assert "no-op" in capsys.readouterr().err


# --- TC-6/TC-7: arm creates exactly one row, idempotently -------------------------------------------------


def test_tc6_arm_creates_exactly_one_row_with_correct_fields(tmp_path):
    db_url, db_path = _fixture_db_url(tmp_path, "tc6.db")
    create_db_and_tables(make_engine(db_url))

    sys.argv = ["run_j11_maintenance_boundary_arm.py", "--confirm", "--database-url", db_url]
    ns = _load_script_module(ARM_SCRIPT_PATH, "run_j11_maintenance_boundary_arm_under_test_tc6")
    try:
        exit_code = ns.main()
    finally:
        sys.modules.pop("run_j11_maintenance_boundary_arm_under_test_tc6", None)
    assert exit_code == 0

    with Session(make_engine(db_url)) as session:
        rows = session.exec(select(MaintenanceBoundary)).all()
    assert len(rows) == 1
    assert rows[0].name == guard.J11_INCIDENT_BOUNDARY_NAME
    assert rows[0].active is True
    assert json.loads(rows[0].quarantined_dates_json) == sorted(d.isoformat() for d in jm.INCIDENT_DATES)


def test_tc7_arm_is_idempotent_on_second_invocation(tmp_path):
    db_url, db_path = _fixture_db_url(tmp_path, "tc7.db")
    create_db_and_tables(make_engine(db_url))

    for _ in range(2):
        sys.argv = ["run_j11_maintenance_boundary_arm.py", "--confirm", "--database-url", db_url]
        ns = _load_script_module(ARM_SCRIPT_PATH, "run_j11_maintenance_boundary_arm_under_test_tc7")
        try:
            exit_code = ns.main()
        finally:
            sys.modules.pop("run_j11_maintenance_boundary_arm_under_test_tc7", None)
        assert exit_code == 0

    with Session(make_engine(db_url)) as session:
        rows = session.exec(
            select(MaintenanceBoundary).where(MaintenanceBoundary.name == guard.J11_INCIDENT_BOUNDARY_NAME)
        ).all()
    assert len(rows) == 1
    assert rows[0].active is True
    assert json.loads(rows[0].quarantined_dates_json) == sorted(d.isoformat() for d in jm.INCIDENT_DATES)


# --- TC-8: arm writes ONLY to maintenance_boundaries -------------------------------------------------------


def _seed_other_tables(session: Session) -> dict:
    session.add(DailyPrice(symbol="AAPL", date=date(2026, 8, 10), open=1, high=2, low=0.5, close=1.5, volume=100))
    run = ScannerRun(
        asof_date=date(2026, 8, 10), created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
        regime_score=50.0, regime_label="Expansion", regime_components_json="[]",
        breadth_above_50dma=50.0, breadth_above_200dma=50.0,
        new_high_low_json="{}", candidate_counts_json="{}",
    )
    session.add(run)
    session.add(Watchlist(ticker="AAPL", reason="test", created_at=datetime.now(timezone.utc), asof_date_added=date(2026, 8, 10)))
    session.commit()
    return _snapshot_other_tables(session)


def _snapshot_other_tables(session: Session) -> dict:
    return {
        "daily_prices": [row.model_dump() for row in session.exec(select(DailyPrice)).all()],
        "scanner_runs": [row.model_dump() for row in session.exec(select(ScannerRun)).all()],
        "watchlist": [row.model_dump() for row in session.exec(select(Watchlist)).all()],
    }


def test_tc8_arm_writes_only_to_maintenance_boundaries(tmp_path):
    db_url, db_path = _fixture_db_url(tmp_path, "tc8.db")
    create_db_and_tables(make_engine(db_url))
    with Session(make_engine(db_url)) as session:
        before = _seed_other_tables(session)

    sys.argv = ["run_j11_maintenance_boundary_arm.py", "--confirm", "--database-url", db_url]
    ns = _load_script_module(ARM_SCRIPT_PATH, "run_j11_maintenance_boundary_arm_under_test_tc8")
    try:
        exit_code = ns.main()
    finally:
        sys.modules.pop("run_j11_maintenance_boundary_arm_under_test_tc8", None)
    assert exit_code == 0

    with Session(make_engine(db_url)) as session:
        after = _snapshot_other_tables(session)
        boundary_rows = session.exec(select(MaintenanceBoundary)).all()

    assert before == after  # zero changed rows in every OTHER table
    assert len(boundary_rows) == 1  # the ONE authorized write


# --- TC-9/TC-10: disarm scoped strictly to the named boundary ---------------------------------------------


def test_tc9_disarm_scoped_to_named_boundary_only(tmp_path):
    db_url, db_path = _fixture_db_url(tmp_path, "tc9.db")
    create_db_and_tables(make_engine(db_url))
    with Session(make_engine(db_url)) as session:
        guard.register_j11_incident_boundary(session, active=True)
        other = guard.register_boundary(
            session, name="other-incident", dates=[date(2027, 1, 4)], reason="unrelated boundary",
        )
    other_before = other.model_dump()

    sys.argv = [
        "run_j11_maintenance_boundary_disarm.py", "--confirm", "--database-url", db_url,
        "--name", guard.J11_INCIDENT_BOUNDARY_NAME,
    ]
    ns = _load_script_module(DISARM_SCRIPT_PATH, "run_j11_maintenance_boundary_disarm_under_test_tc9")
    try:
        exit_code = ns.main()
    finally:
        sys.modules.pop("run_j11_maintenance_boundary_disarm_under_test_tc9", None)
    assert exit_code == 0

    with Session(make_engine(db_url)) as session:
        j11_row = session.exec(
            select(MaintenanceBoundary).where(MaintenanceBoundary.name == guard.J11_INCIDENT_BOUNDARY_NAME)
        ).first()
        other_row = session.exec(
            select(MaintenanceBoundary).where(MaintenanceBoundary.name == "other-incident")
        ).first()

    assert j11_row.active is False
    other_after = other_row.model_dump()
    assert other_after == other_before  # untouched in EVERY field, including updated_at


def test_tc10_after_disarm_incident_dates_unblocked_other_boundary_still_blocks(tmp_path):
    db_url, db_path = _fixture_db_url(tmp_path, "tc10.db")
    create_db_and_tables(make_engine(db_url))
    other_date = date(2027, 1, 4)
    with Session(make_engine(db_url)) as session:
        guard.register_j11_incident_boundary(session, active=True)
        guard.register_boundary(session, name="other-incident", dates=[other_date], reason="unrelated boundary")

    sys.argv = [
        "run_j11_maintenance_boundary_disarm.py", "--confirm", "--database-url", db_url,
        "--name", guard.J11_INCIDENT_BOUNDARY_NAME,
    ]
    ns = _load_script_module(DISARM_SCRIPT_PATH, "run_j11_maintenance_boundary_disarm_under_test_tc10")
    try:
        exit_code = ns.main()
    finally:
        sys.modules.pop("run_j11_maintenance_boundary_disarm_under_test_tc10", None)
    assert exit_code == 0

    with Session(make_engine(db_url)) as session:
        incident_result = guard.evaluate_boundary_for_date(session, jm.INCIDENT_DATES[0])
        other_result = guard.evaluate_boundary_for_date(session, other_date)

    assert incident_result["blocked"] is False
    assert other_result["blocked"] is True
    assert other_result["boundary_name"] == "other-incident"


def test_disarm_is_noop_when_named_boundary_not_registered(tmp_path):
    db_url, db_path = _fixture_db_url(tmp_path, "tc-noop.db")
    create_db_and_tables(make_engine(db_url))

    sys.argv = [
        "run_j11_maintenance_boundary_disarm.py", "--confirm", "--database-url", db_url, "--name", "never-armed",
    ]
    ns = _load_script_module(DISARM_SCRIPT_PATH, "run_j11_maintenance_boundary_disarm_under_test_noop")
    try:
        exit_code = ns.main()
    finally:
        sys.modules.pop("run_j11_maintenance_boundary_disarm_under_test_noop", None)
    assert exit_code == 0

    with Session(make_engine(db_url)) as session:
        rows = session.exec(select(MaintenanceBoundary)).all()
    assert rows == []


# --- neither script silently falls back to a real database when the flag is omitted ----------------------
# (already proven above by `test_arm_confirm_without_database_url_refuses` and
# `test_disarm_confirm_and_url_without_name_refuses`, which assert `make_engine` is never called at all
# when `--database-url`/`--name` is omitted -- goal-market-compass iter-14's lesson: a silently-defaulted
# path/target argument is how committed evidence/state gets touched by accident.)


# ==========================================================================================================
# goal-market-compass iter-18 -- TC-5 through TC-8: the new table-create-or-verify entrypoint
# (`run_j11_maintenance_boundary_table_create.py`, docs/goal.md J-11 step 11, "OWNER RULING -- J-11 exact
# maintenance-boundary table creation and live arm AUTHORIZED", implementation requirements 1-2).
# ==========================================================================================================

TABLE_CREATE_SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_maintenance_boundary_table_create.py"


@pytest.fixture()
def table_create_ns():
    original_argv = sys.argv
    try:
        yield _load_script_module(TABLE_CREATE_SCRIPT_PATH, "run_j11_maintenance_boundary_table_create_under_test")
    finally:
        sys.argv = original_argv
        sys.modules.pop("run_j11_maintenance_boundary_table_create_under_test", None)


def test_table_create_missing_confirm_never_touches_database(monkeypatch, table_create_ns, capsys):
    mock_make_engine = mock.MagicMock(name="make_engine")
    monkeypatch.setattr(table_create_ns, "make_engine", mock_make_engine)
    monkeypatch.setattr(
        sys, "argv", ["run_j11_maintenance_boundary_table_create.py", "--database-url", "sqlite:///x.db"],
    )

    exit_code = table_create_ns.main()

    assert exit_code != 0
    mock_make_engine.assert_not_called()
    assert "--confirm" in capsys.readouterr().err


def test_table_create_confirm_without_database_url_refuses(monkeypatch, table_create_ns, capsys):
    mock_make_engine = mock.MagicMock(name="make_engine")
    monkeypatch.setattr(table_create_ns, "make_engine", mock_make_engine)
    monkeypatch.setattr(sys, "argv", ["run_j11_maintenance_boundary_table_create.py", "--confirm"])

    exit_code = table_create_ns.main()

    assert exit_code != 0
    mock_make_engine.assert_not_called()
    assert "--database-url" in capsys.readouterr().err


# --- TC-5: table absent -> created, schema-exact, no other table touched ----------------------------------


def test_tc5_table_create_creates_exact_schema_when_absent_and_touches_nothing_else(tmp_path):
    db_url, db_path = _fixture_db_url(tmp_path, "tc5.db")
    # `create_db_and_tables` creates EVERY SQLModel table, `MaintenanceBoundary` included -- so, to model
    # "every OTHER table exists, maintenance_boundaries does not" (proving the create is scoped to ONLY
    # that one table, not a side effect of "some table is missing"), create normally then drop back to
    # absent. This fixture-setup DROP is not the script under test.
    create_db_and_tables(make_engine(db_url))
    with make_engine(db_url).begin() as conn:
        conn.exec_driver_sql("DROP TABLE maintenance_boundaries")
    with Session(make_engine(db_url)) as session:
        before = _seed_other_tables(session)

    from sqlalchemy import inspect as sa_inspect
    assert not sa_inspect(make_engine(db_url)).has_table("maintenance_boundaries")

    sys.argv = ["run_j11_maintenance_boundary_table_create.py", "--confirm", "--database-url", db_url]
    ns = _load_script_module(TABLE_CREATE_SCRIPT_PATH, "run_j11_maintenance_boundary_table_create_under_test_tc5")
    try:
        exit_code = ns.main()
    finally:
        sys.modules.pop("run_j11_maintenance_boundary_table_create_under_test_tc5", None)
    assert exit_code == 0

    engine = make_engine(db_url)
    assert sa_inspect(engine).has_table("maintenance_boundaries")
    live_cols = {c["name"] for c in sa_inspect(engine).get_columns("maintenance_boundaries")}
    expected_cols = {c.name for c in MaintenanceBoundary.__table__.columns}
    assert live_cols == expected_cols
    with Session(engine) as session:
        assert session.exec(select(MaintenanceBoundary)).all() == []  # created empty -- arming is separate
        after = _snapshot_other_tables(session)
    assert before == after  # no other table's rows changed


# --- TC-6: table present and exact -> idempotent no-op ------------------------------------------------------


def test_tc6_table_create_is_a_noop_when_already_exact(tmp_path, capsys):
    db_url, db_path = _fixture_db_url(tmp_path, "tc6.db")
    create_db_and_tables(make_engine(db_url))  # maintenance_boundaries already created, schema-exact
    with Session(make_engine(db_url)) as session:
        guard.register_boundary(session, name="pre-existing", dates=[date(2027, 1, 4)], reason="r")

    sys.argv = ["run_j11_maintenance_boundary_table_create.py", "--confirm", "--database-url", db_url]
    ns = _load_script_module(TABLE_CREATE_SCRIPT_PATH, "run_j11_maintenance_boundary_table_create_under_test_tc6")
    try:
        exit_code = ns.main()
    finally:
        sys.modules.pop("run_j11_maintenance_boundary_table_create_under_test_tc6", None)
    assert exit_code == 0
    assert "already correct, no action taken" in capsys.readouterr().err

    with Session(make_engine(db_url)) as session:
        rows = session.exec(select(MaintenanceBoundary)).all()
    assert len(rows) == 1
    assert rows[0].name == "pre-existing"  # untouched -- a no-op writes nothing, not even a re-save


# --- TC-7: table present but mismatched (missing a column) -> STOP, zero write, names the column -----------


def _create_mismatched_table(db_url: str) -> None:
    """A `maintenance_boundaries` table missing the `reason` column -- everything else matches exactly."""
    engine = make_engine(db_url)
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE maintenance_boundaries (
                id INTEGER NOT NULL,
                name VARCHAR NOT NULL,
                quarantined_dates_json VARCHAR NOT NULL,
                active BOOLEAN NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                PRIMARY KEY (id)
            )
            """
        )


def test_tc7_table_create_stops_on_mismatch_and_names_the_missing_column(tmp_path, capsys):
    db_url, db_path = _fixture_db_url(tmp_path, "tc7.db")
    create_db_and_tables(make_engine(db_url))
    # Replace the just-created exact table with a deliberately mismatched one (drop it first -- this
    # fixture setup step, not the script under test, performs the drop).
    with make_engine(db_url).begin() as conn:
        conn.exec_driver_sql("DROP TABLE maintenance_boundaries")
    _create_mismatched_table(db_url)
    with Session(make_engine(db_url)) as session:
        before = _seed_other_tables(session)

    sys.argv = ["run_j11_maintenance_boundary_table_create.py", "--confirm", "--database-url", db_url]
    ns = _load_script_module(TABLE_CREATE_SCRIPT_PATH, "run_j11_maintenance_boundary_table_create_under_test_tc7")
    try:
        exit_code = ns.main()
    finally:
        sys.modules.pop("run_j11_maintenance_boundary_table_create_under_test_tc7", None)

    assert exit_code != 0
    stderr = capsys.readouterr().err
    assert "STOP" in stderr
    assert "reason" in stderr  # the exact missing column is named

    with Session(make_engine(db_url)) as session:
        after = _snapshot_other_tables(session)
    assert before == after  # zero write of any kind -- not even to the mismatched table itself
    from sqlalchemy import inspect as sa_inspect
    live_cols = {c["name"] for c in sa_inspect(make_engine(db_url)).get_columns("maintenance_boundaries")}
    assert "reason" not in live_cols  # untouched -- never ALTERed to "fix" the mismatch


# --- TC-8: refuse without --confirm / --database-url, zero interaction (already covered above by the two ---
# --- `test_table_create_*_never_touches_database` tests; this pair adds the SAME assertions phrased ------
# --- against TC-8's own two separate invocations for direct traceability). ---------------------------------


def test_tc8_missing_confirm_refuses_with_zero_database_interaction(monkeypatch, table_create_ns, capsys):
    mock_make_engine = mock.MagicMock(name="make_engine")
    monkeypatch.setattr(table_create_ns, "make_engine", mock_make_engine)
    monkeypatch.setattr(
        sys, "argv",
        ["run_j11_maintenance_boundary_table_create.py", "--database-url", "sqlite:///should-never-open.db"],
    )
    exit_code = table_create_ns.main()
    assert exit_code != 0
    mock_make_engine.assert_not_called()


def test_tc8_missing_database_url_refuses_with_zero_database_interaction(monkeypatch, table_create_ns, capsys):
    mock_make_engine = mock.MagicMock(name="make_engine")
    monkeypatch.setattr(table_create_ns, "make_engine", mock_make_engine)
    monkeypatch.setattr(sys, "argv", ["run_j11_maintenance_boundary_table_create.py", "--confirm"])
    exit_code = table_create_ns.main()
    assert exit_code != 0
    mock_make_engine.assert_not_called()


# ==========================================================================================================
# goal-market-compass iter-18 -- TC-13 (rider 6a): both `run_j11_iter17_live_preboot_guard_verification.py`
# and `run_j11_iter17_stage_d_readiness.py` refuse to write -- and touch nothing at all -- when their
# `--evidence-dir` already contains one of their own output filenames (iteration-17's own filed
# recommendation: "one can overwrite three of iteration 16's saved evidence files if its destination
# folder is mistyped").
# ==========================================================================================================

LIVE_VERIFICATION_SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_iter17_live_preboot_guard_verification.py"
STAGE_D_READINESS_SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_iter17_stage_d_readiness.py"


def test_tc13_live_verification_refuses_on_evidence_destination_collision(tmp_path, capsys):
    evidence_dir = tmp_path / "colliding-evidence"
    evidence_dir.mkdir()
    colliding_path = evidence_dir / "j11-iter17-readiness-db-file-true-start.json"
    original_content = '{"already": "here", "from": "a prior run"}'
    colliding_path.write_text(original_content)

    sys.argv = [
        "run_j11_iter17_live_preboot_guard_verification.py", "--evidence-dir", str(evidence_dir),
    ]
    ns = _load_script_module(LIVE_VERIFICATION_SCRIPT_PATH, "run_j11_iter17_live_preboot_guard_verification_under_test_tc13")
    try:
        exit_code = ns.main()
    finally:
        sys.modules.pop("run_j11_iter17_live_preboot_guard_verification_under_test_tc13", None)

    assert exit_code != 0
    assert colliding_path.read_text() == original_content  # byte-unchanged
    # no OTHER output file was written either -- the refusal happens before ANY write, not just this one
    assert not (evidence_dir / "j11-iter17-readiness-db-file-true-end.json").exists()
    assert not (evidence_dir / "j11-iter18-live-preboot-guard-verification.json").exists()
    assert "mistyped" in capsys.readouterr().err


def test_tc13_live_verification_collision_guard_does_not_fire_on_a_fresh_dir(monkeypatch, tmp_path, capsys):
    """The refusal is narrowly scoped -- a genuinely FRESH, empty --evidence-dir (the normal case for a
    new iteration) must not be refused merely for existing as a directory. This script has no fixture-DB
    argument (it always resolves the live configured database path), so `_db_file_path` is monkeypatched
    to return None -- the SAME "could not resolve a live sqlite db file" branch the script already has
    for a genuinely missing/non-sqlite URL -- so this test proves the collision guard specifically did
    NOT fire, without opening `apps/backend/data/trendora.db` (this test file's own docstring: "never
    opened, copied, or referenced anywhere in this file")."""
    evidence_dir = tmp_path / "fresh-evidence"
    evidence_dir.mkdir()

    sys.argv = ["run_j11_iter17_live_preboot_guard_verification.py", "--evidence-dir", str(evidence_dir)]
    ns = _load_script_module(LIVE_VERIFICATION_SCRIPT_PATH, "run_j11_iter17_live_preboot_guard_verification_under_test_fresh")
    try:
        monkeypatch.setattr(ns, "_db_file_path", lambda _url: None)
        exit_code = ns.main()
    finally:
        sys.modules.pop("run_j11_iter17_live_preboot_guard_verification_under_test_fresh", None)

    assert exit_code == 1  # the LATER "could not resolve a live sqlite db file" branch, not the refusal
    assert "mistyped" not in capsys.readouterr().err
    # the collision guard did not write anything either (it never got that far) -- confirms the refusal
    # branch and the "could not resolve" branch are genuinely different code paths, not the same message
    assert not (evidence_dir / "j11-iter17-readiness-db-file-true-start.json").exists()


def test_tc13_stage_d_readiness_refuses_on_evidence_destination_collision(tmp_path, capsys):
    evidence_dir = tmp_path / "colliding-evidence"
    evidence_dir.mkdir()
    colliding_path = evidence_dir / "j11-avb-bridge-diagnostic.json"
    original_content = '{"already": "here", "from": "a prior run"}'
    colliding_path.write_text(original_content)

    sys.argv = ["run_j11_iter17_stage_d_readiness.py", "--evidence-dir", str(evidence_dir)]
    ns = _load_script_module(STAGE_D_READINESS_SCRIPT_PATH, "run_j11_iter17_stage_d_readiness_under_test_tc13")
    try:
        exit_code = ns.main()
    finally:
        sys.modules.pop("run_j11_iter17_stage_d_readiness_under_test_tc13", None)

    assert exit_code != 0
    assert colliding_path.read_text() == original_content  # byte-unchanged
    # no OTHER output file was written -- the refusal fires before the iteration-16 hash read, before
    # config load, before any database engine is constructed
    assert not (evidence_dir / "j11-stage-d-preflight.json").exists()
    assert not (evidence_dir / "j11-stage-d-preflight-gate.json").exists()
    assert not (evidence_dir / "j11-iter17-stage-d-readiness.json").exists()
    assert "mistyped" in capsys.readouterr().err


def test_tc13_stage_d_readiness_collision_check_runs_before_reading_iteration_16_files(monkeypatch, tmp_path, capsys):
    """Proves the refusal is checked BEFORE `hashlib.sha256(args.iteration_16_readiness_path.read_bytes())`
    -- pointing `--iteration-16-readiness-path` at a nonexistent file would otherwise raise FileNotFoundError
    before the collision check ever ran, which would be a DIFFERENT (and misleading) failure mode."""
    evidence_dir = tmp_path / "colliding-evidence"
    evidence_dir.mkdir()
    (evidence_dir / "j11-stage-d-preflight.json").write_text('{"already": "here"}')

    sys.argv = [
        "run_j11_iter17_stage_d_readiness.py", "--evidence-dir", str(evidence_dir),
        "--iteration-16-readiness-path", str(tmp_path / "does-not-exist.json"),
    ]
    ns = _load_script_module(STAGE_D_READINESS_SCRIPT_PATH, "run_j11_iter17_stage_d_readiness_under_test_tc13b")
    try:
        exit_code = ns.main()  # must return the refusal code, NOT raise FileNotFoundError
    finally:
        sys.modules.pop("run_j11_iter17_stage_d_readiness_under_test_tc13b", None)

    assert exit_code != 0
    assert "mistyped" in capsys.readouterr().err


# ==========================================================================================================
# goal-market-compass iter-18 -- `run_j11_iter18_full_table_sweep.py`: the mutation-accounting evidence
# capture used to bracket the whole live table-create + arm + verify sequence (docs/goal.md J-11 step 11
# ruling requirement 4). Not one of the phase spec's own numbered TC scenarios (it is this developer's own
# evidence-capture tooling, layered on the already-tested `j11_maintenance.capture_full_table_sweep`) --
# proportionate coverage: the one genuinely new behavior here (the CLI wrapper + its collision refusal),
# not a re-test of the sweep function itself.
# ==========================================================================================================

FULL_TABLE_SWEEP_SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_iter18_full_table_sweep.py"


def test_full_table_sweep_missing_evidence_dir_or_label_refuses(tmp_path, capsys):
    for argv in (
        ["run_j11_iter18_full_table_sweep.py", "--label", "before"],
        ["run_j11_iter18_full_table_sweep.py", "--evidence-dir", str(tmp_path)],
    ):
        sys.argv = argv
        ns = _load_script_module(FULL_TABLE_SWEEP_SCRIPT_PATH, "run_j11_iter18_full_table_sweep_under_test_refuse")
        try:
            exit_code = ns.main()
        finally:
            sys.modules.pop("run_j11_iter18_full_table_sweep_under_test_refuse", None)
        assert exit_code != 0


def test_full_table_sweep_refuses_on_output_collision(tmp_path, capsys):
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    colliding = evidence_dir / "j11-iter18-full-table-sweep-before.json"
    colliding.write_text('{"already": "here"}')

    sys.argv = [
        "run_j11_iter18_full_table_sweep.py", "--evidence-dir", str(evidence_dir), "--label", "before",
    ]
    ns = _load_script_module(FULL_TABLE_SWEEP_SCRIPT_PATH, "run_j11_iter18_full_table_sweep_under_test_collision")
    try:
        exit_code = ns.main()
    finally:
        sys.modules.pop("run_j11_iter18_full_table_sweep_under_test_collision", None)

    assert exit_code != 0
    assert colliding.read_text() == '{"already": "here"}'


def test_full_table_sweep_writes_expected_shape_against_a_fixture_db(monkeypatch, tmp_path):
    db_url, db_path = _fixture_db_url(tmp_path, "sweep-fixture.db")
    create_db_and_tables(make_engine(db_url))
    evidence_dir = tmp_path / "evidence"

    sys.argv = ["run_j11_iter18_full_table_sweep.py", "--evidence-dir", str(evidence_dir), "--label", "before"]
    ns = _load_script_module(FULL_TABLE_SWEEP_SCRIPT_PATH, "run_j11_iter18_full_table_sweep_under_test_shape")
    try:
        monkeypatch.setattr(ns, "resolve_database_url", lambda _url: db_url)
        exit_code = ns.main()
    finally:
        sys.modules.pop("run_j11_iter18_full_table_sweep_under_test_shape", None)

    assert exit_code == 0
    payload = json.loads((evidence_dir / "j11-iter18-full-table-sweep-before.json").read_text())
    assert payload["label"] == "before"
    assert "maintenance_boundaries" in payload["sweep"]["table_names"]
    assert payload["zero_write_proof"]["mtime_unchanged"] is True
    assert payload["zero_write_proof"]["size_unchanged"] is True


# ==========================================================================================================
# goal-market-compass iter-18 -- `_wal_effectively_unchanged`: discovered live, during this iteration's OWN
# authorized live sequence (docs/goal.md J-11 step 11 ruling requirement 6's zero-write proof). A naive
# `start_wal == end_wal` (iter-17's original check) false-flagged the harmless "no -wal sidecar existed yet,
# a read-only connection created an empty one" artifact `db_file_fingerprint`'s own docstring already
# documents. Fixed in `run_j11_iter17_live_preboot_guard_verification.py`; tested here directly (pure
# function, no database needed).
# ==========================================================================================================


def _load_live_verification_module():
    return _load_script_module(LIVE_VERIFICATION_SCRIPT_PATH, "run_j11_iter17_live_preboot_guard_verification_under_test_wal")


def test_wal_effectively_unchanged_identical_dicts_is_true():
    ns = _load_live_verification_module()
    try:
        wal = {"exists": True, "mtime": 123.0, "size_bytes": 0}
        assert ns._wal_effectively_unchanged(wal, dict(wal)) is True
        assert ns._wal_effectively_unchanged({"exists": False}, {"exists": False}) is True
    finally:
        sys.modules.pop("run_j11_iter17_live_preboot_guard_verification_under_test_wal", None)


def test_wal_effectively_unchanged_absent_to_present_zero_bytes_is_true():
    """The exact shape this iteration's own live run hit: no -wal sidecar existed at true-start, and a
    read-only connect created an empty one by true-end -- a harmless artifact, not a write."""
    ns = _load_live_verification_module()
    try:
        assert ns._wal_effectively_unchanged(
            {"exists": False}, {"exists": True, "mtime": 999.0, "size_bytes": 0},
        ) is True
    finally:
        sys.modules.pop("run_j11_iter17_live_preboot_guard_verification_under_test_wal", None)


def test_wal_effectively_unchanged_still_fails_on_a_real_change():
    ns = _load_live_verification_module()
    try:
        # a WAL that grew past zero bytes -- genuine pending-write evidence, must still fail
        assert ns._wal_effectively_unchanged(
            {"exists": True, "mtime": 1.0, "size_bytes": 0}, {"exists": True, "mtime": 2.0, "size_bytes": 4096},
        ) is False
        # a WAL that DISAPPEARED -- must still fail (never expected, never silently accepted)
        assert ns._wal_effectively_unchanged(
            {"exists": True, "mtime": 1.0, "size_bytes": 0}, {"exists": False},
        ) is False
        # present at start with NON-zero size, present at end with a DIFFERENT non-zero size -- must fail
        assert ns._wal_effectively_unchanged(
            {"exists": True, "mtime": 1.0, "size_bytes": 100}, {"exists": True, "mtime": 2.0, "size_bytes": 200},
        ) is False
    finally:
        sys.modules.pop("run_j11_iter17_live_preboot_guard_verification_under_test_wal", None)


# ==========================================================================================================
# goal-market-compass iter-18 AUDIT fix (B2): `_schema_mismatches`' own docstring claims "Every label in
# this small, closed vocabulary (missing / extra / type mismatch / nullable mismatch) is exercised by a
# real test (TC-7)". TC-7 above exercises ONLY the `missing` label -- the other three were declared
# reachable, never proven, which is the exact inversion of the iter-14/14b lesson the phase spec cites
# ("check that every label/branch in a classifier's declared vocabulary is reachable ... exercised by a
# real test, not merely declared reachable"). This test closes that gap directly against the classifier.
# ==========================================================================================================


def test_audit_schema_mismatch_classifier_exercises_every_declared_label():
    ns = _load_script_module(
        TABLE_CREATE_SCRIPT_PATH, "run_j11_maintenance_boundary_table_create_under_test_labels"
    )
    try:
        expected = ns._expected_columns()
        assert ns._schema_mismatches(expected, dict(expected)) == []  # exact match -> no label at all

        missing = {name: shape for name, shape in expected.items() if name != "reason"}
        assert ns._schema_mismatches(expected, missing) == ["reason (missing from live table)"]

        wrong_type = dict(expected)
        wrong_type["name"] = {"type": "TEXT", "nullable": False}
        assert ns._schema_mismatches(expected, wrong_type) == [
            "name (type mismatch: live='TEXT' expected='VARCHAR')"
        ]

        wrong_nullable = dict(expected)
        wrong_nullable["reason"] = {"type": "VARCHAR", "nullable": True}
        assert ns._schema_mismatches(expected, wrong_nullable) == [
            "reason (nullable mismatch: live=True expected=False)"
        ]

        extra = dict(expected)
        extra["bogus_extra_column"] = {"type": "VARCHAR", "nullable": True}
        assert ns._schema_mismatches(expected, extra) == [
            "bogus_extra_column (unexpected extra column on the live table)"
        ]
    finally:
        sys.modules.pop("run_j11_maintenance_boundary_table_create_under_test_labels", None)


def test_audit_table_create_stops_on_an_extra_column_and_names_it(tmp_path, capsys):
    """The end-to-end counterpart of the `extra` label above: a live table carrying an UNEXPECTED extra
    column must STOP the script (exit non-zero, zero write, name the column) exactly as a missing one
    does -- never be silently tolerated as "close enough"."""
    db_url, _db_path = _fixture_db_url(tmp_path, "audit-extra-col.db")
    create_db_and_tables(make_engine(db_url))
    with make_engine(db_url).begin() as conn:
        conn.exec_driver_sql("DROP TABLE maintenance_boundaries")
        conn.exec_driver_sql(
            """
            CREATE TABLE maintenance_boundaries (
                id INTEGER NOT NULL,
                name VARCHAR NOT NULL,
                quarantined_dates_json VARCHAR NOT NULL,
                active BOOLEAN NOT NULL,
                reason VARCHAR NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                stowaway VARCHAR,
                PRIMARY KEY (id)
            )
            """
        )
    with Session(make_engine(db_url)) as session:
        before = _seed_other_tables(session)

    sys.argv = ["run_j11_maintenance_boundary_table_create.py", "--confirm", "--database-url", db_url]
    ns = _load_script_module(
        TABLE_CREATE_SCRIPT_PATH, "run_j11_maintenance_boundary_table_create_under_test_extra"
    )
    try:
        exit_code = ns.main()
    finally:
        sys.modules.pop("run_j11_maintenance_boundary_table_create_under_test_extra", None)

    assert exit_code != 0
    stderr = capsys.readouterr().err
    assert "STOP" in stderr
    assert "stowaway" in stderr  # the exact unexpected column is named

    with Session(make_engine(db_url)) as session:
        after = _snapshot_other_tables(session)
    assert before == after  # zero write of any kind
    from sqlalchemy import inspect as sa_inspect
    live_cols = {c["name"] for c in sa_inspect(make_engine(db_url)).get_columns("maintenance_boundaries")}
    assert "stowaway" in live_cols  # untouched -- never ALTERed away to "fix" the mismatch
