"""goal-market-compass iter-19 -- J-11 Stage D EXECUTION CLI control-flow tests
(`scripts/run_j11_stage_d_execute.py`), TC-10/TC-11 plus the stop-before-write control-flow proofs.

`unittest.mock`-based, NEVER a live DB -- every DB-touching name (`get_engine`, `Session`, and every
`jsd.*`/`jsde.*`/`j11_maintenance.*`/`migration.*`/`jsc.*` function the script calls) is patched to a
mock before `main()` runs, mirroring `test_j11_stage_c_cli_script.py`'s exact idiom -- these tests
exercise CONTROL FLOW only (which functions get called, in what order, and which never get called),
never real database I/O.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest import mock

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_stage_d_execute.py"
_MODULE_NAME = "run_j11_stage_d_execute_under_test"


def _load_script_module():
    """Mirrors `test_j11_stage_c_cli_script.py`'s own loader exactly -- a REAL module object via
    `importlib` (never `runpy.run_path`), so `monkeypatch.setattr(module, name, mock)` genuinely
    intercepts every call the script's top-level code makes to that name."""
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


# --- missing --confirm: NO database interaction of any kind -----------------------------------------


def test_missing_confirm_never_calls_get_engine_or_session(monkeypatch, script_ns):
    mock_get_engine = mock.MagicMock(name="get_engine")
    mock_session_cls = mock.MagicMock(name="Session")
    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
    monkeypatch.setattr(script_ns, "Session", mock_session_cls)
    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))
    monkeypatch.setattr(sys, "argv", ["run_j11_stage_d_execute.py"])  # no --confirm

    exit_code = script_ns.main()

    assert exit_code != 0
    mock_get_engine.assert_not_called()
    mock_session_cls.assert_not_called()


# --- --confirm but no --evidence-dir: refuses, writes nothing anywhere ------------------------------


def test_confirm_without_explicit_evidence_dir_refuses_before_writing_anything(monkeypatch, script_ns, capsys):
    mock_write_json = mock.MagicMock(name="_write_json")
    monkeypatch.setattr(script_ns, "_write_json", mock_write_json)
    mock_get_engine = mock.MagicMock(name="get_engine")
    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(name="Session"))
    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))

    monkeypatch.setattr(sys, "argv", ["run_j11_stage_d_execute.py", "--confirm"])

    exit_code = script_ns.main()

    assert exit_code == 2
    mock_write_json.assert_not_called()
    mock_get_engine.assert_not_called()
    assert "--evidence-dir" in capsys.readouterr().err


# --- collision guard: a pre-existing output file refuses before any DB interaction -------------------


def test_collision_guard_refuses_before_any_db_interaction(monkeypatch, script_ns, tmp_path, capsys):
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    (evidence_dir / "j11-stage-d-execute-outcome.json").write_text("{}")  # a prior run's leftover

    mock_get_engine = mock.MagicMock(name="get_engine")
    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(name="Session"))
    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))

    monkeypatch.setattr(
        sys, "argv",
        ["run_j11_stage_d_execute.py", "--confirm", "--evidence-dir", str(evidence_dir)],
    )

    exit_code = script_ns.main()

    assert exit_code == 2
    mock_get_engine.assert_not_called()
    assert "already contains" in capsys.readouterr().err


# --- shared happy-path mock rig, so individual tests only override ONE piece -------------------------


def _install_happy_path_mocks(monkeypatch, script_ns, *, evidence_dir: Path):
    """Patches every DB-touching / expensive name the script calls to a deterministic, fully-successful
    default. Returns a dict of the individual mocks so a test can override exactly one to prove a
    specific stop-before-write control-flow property."""
    mock_engine = mock.MagicMock(name="engine")
    monkeypatch.setattr(script_ns, "get_engine", mock.MagicMock(return_value=mock_engine))

    mock_session_instance = mock.MagicMock(name="session_instance")
    mock_session_cm = mock.MagicMock()
    mock_session_cm.__enter__ = mock.MagicMock(return_value=mock_session_instance)
    mock_session_cm.__exit__ = mock.MagicMock(return_value=False)
    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(return_value=mock_session_cm))

    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={"exists": False}))
    monkeypatch.setattr(script_ns.jsc, "read_goal_md_text", mock.MagicMock(return_value="goal md text"))
    monkeypatch.setattr(script_ns.jsc, "read_git_head", mock.MagicMock(return_value="deadbeef"))
    monkeypatch.setattr(
        script_ns.jsc, "small_table_id_snapshot", mock.MagicMock(return_value={"count": 0, "ids": []}),
    )

    mock_capture_preflight = mock.MagicMock(
        name="capture_stage_d_preflight",
        return_value={"manifest_row_count": 24, "c1_date_set_boundary_check": {"ok": True}},
    )
    monkeypatch.setattr(script_ns.jsd, "capture_stage_d_preflight", mock_capture_preflight)

    mock_compare_preflight = mock.MagicMock(
        name="compare_stage_d_preflight_to_certified", return_value={"all_invariants_hold": True, "checks": {}},
    )
    monkeypatch.setattr(script_ns.jsd, "compare_stage_d_preflight_to_certified", mock_compare_preflight)

    mock_preflight_verdict = mock.MagicMock(
        name="stage_d_preflight_verdict", return_value={"passed": True, "reason": "all_checks_passed"},
    )
    monkeypatch.setattr(script_ns.jsd, "stage_d_preflight_verdict", mock_preflight_verdict)

    mock_boundary_recheck = mock.MagicMock(
        name="recheck_maintenance_boundary_and_guard",
        return_value={"ok": True, "boundary_active": True, "all_dates_blocked": True},
    )
    monkeypatch.setattr(script_ns.jsde, "recheck_maintenance_boundary_and_guard", mock_boundary_recheck)

    mock_avb = mock.MagicMock(
        name="run_fresh_avb_reclassification",
        return_value={"classification": {"classification": "AVB-A"}},
    )
    monkeypatch.setattr(script_ns.jsde, "run_fresh_avb_reclassification", mock_avb)

    mock_gate_verdict = mock.MagicMock(
        name="stage_d_execution_gate_verdict",
        return_value={"proceed": True, "blocking_reasons": []},
    )
    monkeypatch.setattr(script_ns.jsde, "stage_d_execution_gate_verdict", mock_gate_verdict)

    mock_freeze = mock.MagicMock(
        name="freeze_fresh_stage_d_execution_identity",
        return_value={"engine_identity": "fresh-identity-value", "attempt_id": "j11-stage-d-x"},
    )
    monkeypatch.setattr(script_ns.jsde, "freeze_fresh_stage_d_execution_identity", mock_freeze)

    monkeypatch.setattr(
        script_ns.jsde, "compare_identity_against_historical",
        mock.MagicMock(return_value={"comparisons": {}, "any_historical_match": False}),
    )
    monkeypatch.setattr(
        script_ns.engine_identity, "compute_engine_identity", mock.MagicMock(return_value="fresh-identity-value"),
    )
    mock_check_a = mock.MagicMock(name="check_identity_before_first_write", return_value={"ok": True})
    monkeypatch.setattr(script_ns.jsd, "check_identity_before_first_write", mock_check_a)

    monkeypatch.setattr(script_ns.j11_maintenance, "capture_full_table_sweep", mock.MagicMock(return_value={}))
    monkeypatch.setattr(script_ns.migration, "dump_table", mock.MagicMock(return_value=[]))
    monkeypatch.setattr(
        script_ns.jsde, "capture_legacy_and_null_scanner_run_fingerprint",
        mock.MagicMock(return_value={"row_count": 0, "null_count": 0, "legacy_6261ca17_count": 0, "rows": [], "fingerprint": "x"}),
    )
    monkeypatch.setattr(
        script_ns.j11_maintenance, "capture_pre_reset_inventory",
        mock.MagicMock(return_value={"daily_prices": {"fingerprint": "p"}}),
    )

    mock_regen = mock.MagicMock(
        name="execute_stage_d_regeneration",
        return_value={"completed": True, "stopped_at_date": None, "new_run_ids": [1, 2]},
    )
    monkeypatch.setattr(script_ns.jsde, "execute_stage_d_regeneration", mock_regen)

    mock_mutation_accounting = mock.MagicMock(
        name="build_stage_d_mutation_accounting",
        return_value={"all_checks_pass": True, "checks": {}},
    )
    monkeypatch.setattr(script_ns.jsde, "build_stage_d_mutation_accounting", mock_mutation_accounting)

    fake_certified_path = evidence_dir.parent / "certified.json"
    fake_certified_path.write_text(json.dumps({"manifest_row_count": 24}))

    return {
        "capture_preflight": mock_capture_preflight,
        "compare_preflight": mock_compare_preflight,
        "preflight_verdict": mock_preflight_verdict,
        "boundary_recheck": mock_boundary_recheck,
        "avb": mock_avb,
        "gate_verdict": mock_gate_verdict,
        "freeze": mock_freeze,
        "check_a": mock_check_a,
        "regen": mock_regen,
        "mutation_accounting": mock_mutation_accounting,
        "certified_path": fake_certified_path,
    }


def _argv(evidence_dir: Path, certified_path: Path) -> list[str]:
    return [
        "run_j11_stage_d_execute.py", "--confirm",
        "--evidence-dir", str(evidence_dir),
        "--certified-baseline-path", str(certified_path),
    ]


# --- execution gate refusing to proceed: the write loop is NEVER reached -----------------------------


def test_execution_gate_not_proceed_never_calls_regeneration(monkeypatch, script_ns, tmp_path):
    evidence_dir = tmp_path / "evidence"
    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
    mocks["gate_verdict"].return_value = {"proceed": False, "blocking_reasons": ["avb_classification_not_avb_a:AVB-B"]}

    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks["certified_path"]))
    exit_code = script_ns.main()

    assert exit_code != 0
    mocks["freeze"].assert_not_called()
    mocks["regen"].assert_not_called()
    outcome = json.loads((evidence_dir / "j11-stage-d-execute-outcome.json").read_text())
    assert outcome["executed"] is False
    assert outcome["reason"] == "execution_gate_did_not_proceed"


# --- Check (A) failure: still stops before the write loop --------------------------------------------


def test_check_a_failure_never_calls_regeneration(monkeypatch, script_ns, tmp_path):
    evidence_dir = tmp_path / "evidence"
    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
    mocks["check_a"].return_value = {"ok": False}

    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks["certified_path"]))
    exit_code = script_ns.main()

    assert exit_code != 0
    mocks["regen"].assert_not_called()
    outcome = json.loads((evidence_dir / "j11-stage-d-execute-outcome.json").read_text())
    assert outcome["executed"] is False


# --- failed post-execution mutation accounting: outcome STILL written, exit non-zero -----------------


def test_failed_mutation_accounting_writes_outcome_executed_false_and_returns_nonzero(monkeypatch, script_ns, tmp_path):
    evidence_dir = tmp_path / "evidence"
    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
    mocks["mutation_accounting"].return_value = {"all_checks_pass": False, "checks": {"manifests_unchanged": False}}

    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks["certified_path"]))
    exit_code = script_ns.main()

    assert exit_code != 0
    mocks["regen"].assert_called_once()  # the gate passed, so the write loop DID run this time...
    outcome_path = evidence_dir / "j11-stage-d-execute-outcome.json"
    assert outcome_path.exists()  # ...but the outcome is STILL persisted either way (unlike Stage C)
    outcome = json.loads(outcome_path.read_text())
    assert outcome["executed"] is False
    assert outcome["reason"] == "post_execution_mutation_accounting_failed"


# --- the full successful path: exit 0, outcome executed=True -----------------------------------------


def test_successful_full_path_returns_zero_and_writes_outcome_executed_true(monkeypatch, script_ns, tmp_path):
    evidence_dir = tmp_path / "evidence"
    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)

    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks["certified_path"]))
    exit_code = script_ns.main()

    assert exit_code == 0
    mocks["regen"].assert_called_once()
    outcome = json.loads((evidence_dir / "j11-stage-d-execute-outcome.json").read_text())
    assert outcome["executed"] is True
    # every declared output filename was actually written
    for name in script_ns.OUTPUT_FILENAMES:
        assert (evidence_dir / name).exists(), f"missing evidence file {name}"


def test_none_of_the_default_paths_point_outside_the_repo(script_ns):
    """Sanity: every default evidence/identity path constant resolves under REPO_ROOT -- never an
    absolute path escaping the repository, never a path under apps/backend/data/ (the live db dir)."""
    repo_root = script_ns.REPO_ROOT
    for path in (
        script_ns.DEFAULT_CERTIFIED_BASELINE_PATH,
        script_ns.DEFAULT_ITERATION_10_IDENTITY_PATH,
        script_ns.DEFAULT_ITERATION_14_IDENTITY_PATH,
        script_ns.DEFAULT_ITERATION_16_17_18_PREFLIGHT_PATH,
    ):
        assert str(path).startswith(str(repo_root))
        assert "apps/backend/data" not in str(path)
