"""goal-market-compass iter-22 -- J-11 Stage G FULL VERIFICATION CLI control-flow tests
(`scripts/run_j11_stage_g_verify.py`), TC-27 plus the stop-before-write control-flow proofs this
iteration's own dev handoff relies on.

`unittest.mock`-based, NEVER a live DB -- every DB-touching name (`get_engine`, `Session`, and
`jsc.db_file_fingerprint`) is patched to a mock before `main()` runs, mirroring
`test_j11_stage_f_execute_cli_script.py`'s exact idiom. These tests exercise CONTROL FLOW only (the
argparse gating, the collision guard, and the missing-required-evidence stop) -- never real database I/O,
and never the full happy-path pipeline (that composition is already unit-tested function-by-function in
`test_j11_stage_g_verify.py`, and integration-proven by the live --confirm run cited in the dev handoff)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest import mock

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_stage_g_verify.py"
_MODULE_NAME = "run_j11_stage_g_verify_under_test"


def _load_script_module():
    """A REAL module object via `importlib` (never `runpy.run_path`), so
    `monkeypatch.setattr(module, name, mock)` genuinely intercepts every call the script's top-level code
    makes to that name -- mirrors `test_j11_stage_f_execute_cli_script.py`'s own loader exactly."""
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def script_ns():
    original_argv = sys.argv
    try:
        module = _load_script_module()
        yield module
    finally:
        sys.argv = original_argv
        sys.modules.pop(_MODULE_NAME, None)


# --- TC-27: missing --confirm -- NO database interaction of any kind -----------------------------------


def test_missing_confirm_never_calls_get_engine_or_session(monkeypatch, script_ns):
    mock_get_engine = mock.MagicMock(name="get_engine")
    mock_session_cls = mock.MagicMock(name="Session")
    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
    monkeypatch.setattr(script_ns, "Session", mock_session_cls)
    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))
    monkeypatch.setattr(sys, "argv", ["run_j11_stage_g_verify.py"])  # no --confirm

    exit_code = script_ns.main()

    assert exit_code != 0
    mock_get_engine.assert_not_called()
    mock_session_cls.assert_not_called()


def test_missing_confirm_never_calls_load_config(monkeypatch, script_ns):
    mock_load_config = mock.MagicMock(name="load_config")
    monkeypatch.setattr(script_ns, "load_config", mock_load_config)
    monkeypatch.setattr(sys, "argv", ["run_j11_stage_g_verify.py", "--evidence-dir", "/tmp/whatever"])

    exit_code = script_ns.main()

    assert exit_code != 0
    mock_load_config.assert_not_called()


# --- TC-27: --confirm but no --evidence-dir -- refuses before config/engine construction ----------------


def test_confirm_without_explicit_evidence_dir_refuses_before_config_construction(monkeypatch, script_ns, capsys):
    mock_load_config = mock.MagicMock(name="load_config")
    monkeypatch.setattr(script_ns, "load_config", mock_load_config)
    mock_get_engine = mock.MagicMock(name="get_engine")
    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(name="Session"))

    monkeypatch.setattr(sys, "argv", ["run_j11_stage_g_verify.py", "--confirm"])

    exit_code = script_ns.main()

    assert exit_code == 2
    mock_load_config.assert_not_called()
    mock_get_engine.assert_not_called()
    assert "--evidence-dir" in capsys.readouterr().err


# --- collision guard: a pre-existing output file refuses before any DB interaction -----------------------


def test_collision_guard_refuses_before_any_db_interaction(monkeypatch, script_ns, tmp_path, capsys):
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    (evidence_dir / "j11-stage-g-verify-outcome.json").write_text("{}")  # a prior run's leftover

    mock_load_config = mock.MagicMock(name="load_config")
    monkeypatch.setattr(script_ns, "load_config", mock_load_config)
    mock_get_engine = mock.MagicMock(name="get_engine")
    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(name="Session"))

    monkeypatch.setattr(
        sys, "argv",
        ["run_j11_stage_g_verify.py", "--confirm", "--evidence-dir", str(evidence_dir)],
    )

    exit_code = script_ns.main()

    assert exit_code == 2
    mock_load_config.assert_not_called()
    mock_get_engine.assert_not_called()
    assert "already contains" in capsys.readouterr().err


def test_collision_guard_checks_every_declared_output_filename(script_ns, tmp_path):
    """Every filename this script promises to write (OUTPUT_FILENAMES) is actually covered by the
    collision guard -- a filename added to one list but not the other would silently let a stale file
    survive a "fresh evidence dir" run, exactly the class of bug iterations 19-21 were flagged for."""
    for name in script_ns.OUTPUT_FILENAMES:
        evidence_dir = tmp_path / f"evidence_{name}"
        evidence_dir.mkdir()
        (evidence_dir / name).write_text("{}")
        colliding = script_ns._refuse_if_evidence_files_exist(evidence_dir, script_ns.OUTPUT_FILENAMES)
        assert name in colliding


# --- missing required historical evidence inputs -- stops before the preflight even reads the DB --------


def test_missing_required_evidence_inputs_stops_before_boundary_recheck(monkeypatch, script_ns, tmp_path, capsys):
    """When the caller-supplied historical evidence paths (Stage D's frozen identity, Stage D's
    regeneration, Stage E's population report, the certified baseline, iteration 18's sweep, iteration
    10's pre-reset inventory) cannot ALL be loaded, the script must stop before EVEN the first read-only
    preflight check runs -- never proceed on partial/fabricated evidence."""
    evidence_dir = tmp_path / "evidence"

    mock_load_config = mock.MagicMock(name="load_config")
    mock_load_config.return_value.database.url = "sqlite:///:memory:"
    monkeypatch.setattr(script_ns, "load_config", mock_load_config)
    monkeypatch.setattr(script_ns, "resolve_database_url", mock.MagicMock(return_value="sqlite:///:memory:"))
    mock_get_engine = mock.MagicMock(name="get_engine")
    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
    mock_recheck = mock.MagicMock(name="recheck_maintenance_boundary_and_guard")
    monkeypatch.setattr(script_ns.jsde, "recheck_maintenance_boundary_and_guard", mock_recheck)
    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={"exists": False}))

    # every --*-path flag points at a nonexistent file -- _load_json returns None for all of them
    nonexistent = tmp_path / "does-not-exist.json"
    monkeypatch.setattr(
        sys, "argv",
        [
            "run_j11_stage_g_verify.py", "--confirm", "--evidence-dir", str(evidence_dir),
            "--stage-d-frozen-identity-path", str(nonexistent),
            "--stage-d-regeneration-path", str(nonexistent),
            "--stage-e-population-report-path", str(nonexistent),
            "--stage-f-dispositions-path", str(nonexistent),
            "--certified-baseline-path", str(nonexistent),
            "--pre-reset-inventory-path", str(nonexistent),
            "--iter18-pre-stage-d-sweep-path", str(nonexistent),
        ],
    )

    exit_code = script_ns.main()

    assert exit_code == 1
    mock_recheck.assert_not_called()  # the preflight's first read-only check never even ran
    stderr = capsys.readouterr().err
    assert "missing" in stderr.lower()
