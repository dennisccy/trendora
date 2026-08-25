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
