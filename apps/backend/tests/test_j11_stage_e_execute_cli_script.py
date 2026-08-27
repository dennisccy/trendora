"""goal-market-compass iter-20 -- J-11 Stage E EXECUTION CLI control-flow tests
(`scripts/run_j11_stage_e_execute.py`), TC-10/TC-13/TC-14/TC-17/TC-18 plus the stop-before-write
control-flow proofs.

`unittest.mock`-based, NEVER a live DB -- every DB-touching name (`get_engine`, `Session`, and every
`jsee.*`/`jsde.*`/`j11_maintenance.*`/`migration.*`/`jsc.*` function the script calls) is patched to a
mock before `main()` runs, mirroring `test_j11_stage_d_execute_cli_script.py`'s exact idiom -- these
tests exercise CONTROL FLOW only (which functions get called, in what order, and which never get
called), never real database I/O.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest import mock

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_stage_e_execute.py"
_MODULE_NAME = "run_j11_stage_e_execute_under_test"


def _load_script_module():
    """Mirrors `test_j11_stage_d_execute_cli_script.py`'s own loader exactly -- a REAL module object via
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


# --- TC-13: missing --confirm -- NO database interaction of any kind ---------------------------------


def test_tc13_missing_confirm_never_calls_get_engine_or_session(monkeypatch, script_ns):
    mock_get_engine = mock.MagicMock(name="get_engine")
    mock_session_cls = mock.MagicMock(name="Session")
    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
    monkeypatch.setattr(script_ns, "Session", mock_session_cls)
    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))
    monkeypatch.setattr(sys, "argv", ["run_j11_stage_e_execute.py"])  # no --confirm

    exit_code = script_ns.main()

    assert exit_code != 0
    mock_get_engine.assert_not_called()
    mock_session_cls.assert_not_called()


# --- TC-14: --confirm but no --evidence-dir -- refuses, writes nothing anywhere ----------------------


def test_tc14_confirm_without_explicit_evidence_dir_refuses_before_writing_anything(monkeypatch, script_ns, capsys):
    mock_write_json = mock.MagicMock(name="_write_json")
    monkeypatch.setattr(script_ns, "_write_json", mock_write_json)
    mock_get_engine = mock.MagicMock(name="get_engine")
    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(name="Session"))
    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))

    monkeypatch.setattr(sys, "argv", ["run_j11_stage_e_execute.py", "--confirm"])

    exit_code = script_ns.main()

    assert exit_code == 2
    mock_write_json.assert_not_called()
    mock_get_engine.assert_not_called()
    assert "--evidence-dir" in capsys.readouterr().err


# --- collision guard: a pre-existing output file refuses before any DB interaction --------------------


def test_collision_guard_refuses_before_any_db_interaction(monkeypatch, script_ns, tmp_path, capsys):
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    (evidence_dir / "j11-stage-e-execute-outcome.json").write_text("{}")  # a prior run's leftover

    mock_get_engine = mock.MagicMock(name="get_engine")
    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(name="Session"))
    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))

    monkeypatch.setattr(
        sys, "argv",
        ["run_j11_stage_e_execute.py", "--confirm", "--evidence-dir", str(evidence_dir)],
    )

    exit_code = script_ns.main()

    assert exit_code == 2
    mock_get_engine.assert_not_called()
    assert "already contains" in capsys.readouterr().err


# --- shared happy-path mock rig, so individual tests only override ONE piece --------------------------


def _install_happy_path_mocks(monkeypatch, script_ns, *, evidence_dir: Path):
    """Patches every DB-touching / expensive name the script calls to a deterministic, fully-successful
    default. Returns a dict of the individual mocks so a test can override exactly one to prove a
    specific stop-before-write control-flow property. Mirrors Stage D's CLI test rig: the LEAF checks
    are mocked, but the REAL `jsee.stage_e_execution_outcome` composition logic runs (already separately
    unit-tested for its own correctness in `test_j11_stage_e_execute.py`)."""
    mock_engine = mock.MagicMock(name="engine")
    monkeypatch.setattr(script_ns, "get_engine", mock.MagicMock(return_value=mock_engine))

    mock_session_instance = mock.MagicMock(name="session_instance")
    # the script's own `int(session.scalar(select(func.count())...) or 0)` calls (pre/post
    # forward_returns row count) need a REAL int back, not an auto-generated MagicMock (which has no
    # usable `__int__`) -- `select`/`func` themselves are left real (harmless: `session.scalar` is what's
    # actually mocked, so the real SQLAlchemy statement-building code runs but is never executed against
    # a real connection).
    mock_session_instance.scalar = mock.MagicMock(return_value=100)
    mock_session_cm = mock.MagicMock()
    mock_session_cm.__enter__ = mock.MagicMock(return_value=mock_session_instance)
    mock_session_cm.__exit__ = mock.MagicMock(return_value=False)
    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(return_value=mock_session_cm))

    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={"exists": False}))
    monkeypatch.setattr(
        script_ns.jsc, "small_table_id_snapshot", mock.MagicMock(return_value={"count": 0, "ids": []}),
    )

    mock_boundary_recheck = mock.MagicMock(
        name="recheck_maintenance_boundary_and_guard",
        return_value={"ok": True, "boundary_active": True, "all_dates_blocked": True},
    )
    monkeypatch.setattr(script_ns.jsde, "recheck_maintenance_boundary_and_guard", mock_boundary_recheck)

    mock_runs_check = mock.MagicMock(
        name="confirm_stage_d_runs_present_unrestamped", return_value={"ok": True, "per_date": {}},
    )
    monkeypatch.setattr(script_ns.jsee, "confirm_stage_d_runs_present_unrestamped", mock_runs_check)

    monkeypatch.setattr(
        script_ns.engine_identity, "compute_engine_identity", mock.MagicMock(return_value="fresh-identity-value"),
    )
    mock_identity_check = mock.MagicMock(
        name="check_engine_identity_matches_stage_d", return_value={"ok": True, "matches": True},
    )
    monkeypatch.setattr(script_ns.jsee, "check_engine_identity_matches_stage_d", mock_identity_check)

    mock_manifest_check = mock.MagicMock(name="confirm_manifests_unchanged", return_value={"ok": True})
    monkeypatch.setattr(script_ns.jsee, "confirm_manifests_unchanged", mock_manifest_check)

    mock_gate_verdict = mock.MagicMock(
        name="stage_e_preflight_gate_verdict", return_value={"proceed": True, "blocking_reasons": []},
    )
    monkeypatch.setattr(script_ns.jsee, "stage_e_preflight_gate_verdict", mock_gate_verdict)

    monkeypatch.setattr(script_ns.j11_maintenance, "capture_full_table_sweep", mock.MagicMock(return_value={}))
    monkeypatch.setattr(script_ns.migration, "dump_table", mock.MagicMock(return_value=[]))
    monkeypatch.setattr(
        script_ns.jsee, "capture_all_scanner_run_fingerprint",
        mock.MagicMock(return_value={"row_count": 0, "rows": [], "fingerprint": "x"}),
    )
    monkeypatch.setattr(
        script_ns.j11_maintenance, "capture_pre_reset_inventory",
        mock.MagicMock(return_value={"daily_prices": {"fingerprint": "p"}}),
    )
    mock_retained_holes = mock.MagicMock(
        name="capture_retained_incident_hole_counts",
        return_value={"per_run_id_counts": {}, "total": 0, "run_count": 0},
    )
    monkeypatch.setattr(script_ns.jsee, "capture_retained_incident_hole_counts", mock_retained_holes)

    mock_repair_loop = mock.MagicMock(
        name="execute_stage_e_repair_loop",
        return_value={
            "total_runs_processed": 2, "total_rows_inserted": 5,
            "rows_inserted_on_rebuilt_incident_runs": 3, "rows_inserted_on_retained_runs": 2,
            "per_run_results": [],
        },
    )
    monkeypatch.setattr(script_ns.jsee, "execute_stage_e_repair_loop", mock_repair_loop)

    monkeypatch.setattr(script_ns.jsee, "read_process_vm_peak_kb", mock.MagicMock(return_value=500_000))
    monkeypatch.setattr(
        script_ns.jsee, "build_memory_check",
        mock.MagicMock(return_value={"vm_peak_mb": 488.3, "within_cap": True}),
    )

    mock_population_report = mock.MagicMock(
        name="live_verify_three_populations", return_value={"all_checks_pass": True},
    )
    monkeypatch.setattr(script_ns.jsee, "live_verify_three_populations", mock_population_report)

    mock_mutation_accounting = mock.MagicMock(
        name="build_stage_e_mutation_accounting",
        return_value={"all_checks_pass": True, "checks": {}},
    )
    monkeypatch.setattr(script_ns.jsee, "build_stage_e_mutation_accounting", mock_mutation_accounting)

    fake_frozen_identity_path = evidence_dir.parent / "frozen-identity.json"
    fake_frozen_identity_path.write_text(json.dumps({"engine_identity": "fresh-identity-value"}))
    fake_regeneration_path = evidence_dir.parent / "regeneration.json"
    fake_regeneration_path.write_text(json.dumps({"per_date_results": [
        {"date": "2026-05-12", "run_id": 3148}, {"date": "2026-05-13", "run_id": 3149},
    ]}))
    fake_certified_path = evidence_dir.parent / "certified.json"
    fake_certified_path.write_text(json.dumps({"manifest_dump": []}))

    return {
        "boundary_recheck": mock_boundary_recheck,
        "runs_check": mock_runs_check,
        "identity_check": mock_identity_check,
        "manifest_check": mock_manifest_check,
        "gate_verdict": mock_gate_verdict,
        "repair_loop": mock_repair_loop,
        "population_report": mock_population_report,
        "mutation_accounting": mock_mutation_accounting,
        "frozen_identity_path": fake_frozen_identity_path,
        "regeneration_path": fake_regeneration_path,
        "certified_path": fake_certified_path,
    }


def _argv(evidence_dir: Path, mocks: dict) -> list[str]:
    return [
        "run_j11_stage_e_execute.py", "--confirm",
        "--evidence-dir", str(evidence_dir),
        "--stage-d-frozen-identity-path", str(mocks["frozen_identity_path"]),
        "--stage-d-regeneration-path", str(mocks["regeneration_path"]),
        "--certified-baseline-path", str(mocks["certified_path"]),
    ]


# --- TC-2-adjacent: preflight gate refusing to proceed -- the write loop is NEVER reached -------------


def test_preflight_gate_not_proceed_never_calls_repair_loop(monkeypatch, script_ns, tmp_path):
    evidence_dir = tmp_path / "evidence"
    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
    mocks["gate_verdict"].return_value = {"proceed": False, "blocking_reasons": ["engine_identity_drifted_since_stage_d"]}

    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks))
    exit_code = script_ns.main()

    assert exit_code != 0
    mocks["repair_loop"].assert_not_called()
    outcome = json.loads((evidence_dir / "j11-stage-e-execute-outcome.json").read_text())
    assert outcome["executed"] is False
    assert outcome["reason"] == "preflight_gate_did_not_proceed"


# --- TC-18/TC-9: failed post-execution mutation accounting -- outcome STILL written, exit non-zero ----


def test_failed_mutation_accounting_writes_outcome_executed_false_and_returns_nonzero(monkeypatch, script_ns, tmp_path):
    evidence_dir = tmp_path / "evidence"
    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
    mocks["mutation_accounting"].return_value = {"all_checks_pass": False, "checks": {"daily_prices_unchanged": False}}

    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks))
    exit_code = script_ns.main()

    assert exit_code != 0
    mocks["repair_loop"].assert_called_once()  # the gate passed, so the write loop DID run this time...
    outcome_path = evidence_dir / "j11-stage-e-execute-outcome.json"
    assert outcome_path.exists()  # ...but the outcome is STILL persisted either way
    outcome = json.loads(outcome_path.read_text())
    assert outcome["executed"] is False
    assert outcome["reason"] == "post_execution_mutation_accounting_failed"


# --- failed live population verification -- outcome executed=False, exact reason ----------------------


def test_failed_population_verification_writes_outcome_executed_false(monkeypatch, script_ns, tmp_path):
    evidence_dir = tmp_path / "evidence"
    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
    mocks["population_report"].return_value = {"all_checks_pass": False}

    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks))
    exit_code = script_ns.main()

    assert exit_code != 0
    outcome = json.loads((evidence_dir / "j11-stage-e-execute-outcome.json").read_text())
    assert outcome["executed"] is False
    assert outcome["reason"] == "live_population_verification_failed"


# --- the full successful path: exit 0, outcome executed=True, every declared file written -------------


def test_successful_full_path_returns_zero_and_writes_outcome_executed_true(monkeypatch, script_ns, tmp_path):
    evidence_dir = tmp_path / "evidence"
    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)

    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks))
    exit_code = script_ns.main()

    assert exit_code == 0
    mocks["repair_loop"].assert_called_once()
    outcome = json.loads((evidence_dir / "j11-stage-e-execute-outcome.json").read_text())
    assert outcome["executed"] is True
    # every declared output filename was actually written
    for name in script_ns.OUTPUT_FILENAMES:
        assert (evidence_dir / name).exists(), f"missing evidence file {name}"


# --- TC-16: terminal vocabulary -- exact required lines, both outcomes --------------------------------


def test_tc16_terminal_lines_success(monkeypatch, script_ns, tmp_path, capsys):
    evidence_dir = tmp_path / "evidence"
    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks))

    script_ns.main()
    err = capsys.readouterr().err

    assert "J-11 STAGE D EXECUTED: YES" in err
    assert "J-11 STAGE E COMPLETE: YES" in err
    assert "J-11 STAGE F COMPLETE: NO" in err
    assert "J-11 STAGE G VERIFIED: NO" in err
    assert "J-11 INCIDENT STATUS: NOT REPAIRED" in err
    assert "J-11 MAINTENANCE BOUNDARY: ACTIVE" in err
    assert "J-11 LIVE PRE-BOOT GUARD: ARMED" in err


def test_tc16_terminal_lines_blocked_at_preflight(monkeypatch, script_ns, tmp_path, capsys):
    evidence_dir = tmp_path / "evidence"
    mocks = _install_happy_path_mocks(monkeypatch, script_ns, evidence_dir=evidence_dir)
    mocks["gate_verdict"].return_value = {"proceed": False, "blocking_reasons": ["x"]}
    monkeypatch.setattr(sys, "argv", _argv(evidence_dir, mocks))

    script_ns.main()
    err = capsys.readouterr().err

    assert "J-11 STAGE D EXECUTED: YES" in err
    assert "J-11 STAGE E COMPLETE: NO" in err
    assert "J-11 MAINTENANCE BOUNDARY: ACTIVE" in err
    assert "J-11 LIVE PRE-BOOT GUARD: ARMED" in err


# --- TC-19-adjacent static safety net: no default path escapes the repo -------------------------------


def test_none_of_the_default_paths_point_outside_the_repo(script_ns):
    repo_root = script_ns.REPO_ROOT
    for path in (
        script_ns.DEFAULT_STAGE_D_FROZEN_IDENTITY_PATH,
        script_ns.DEFAULT_STAGE_D_REGENERATION_PATH,
        script_ns.DEFAULT_CERTIFIED_BASELINE_PATH,
    ):
        assert str(path).startswith(str(repo_root))


# --- helper-function unit tests (pure, no mocking needed) ----------------------------------------------


def test_load_expected_run_id_by_date_honest_empty_on_missing_file(script_ns, tmp_path):
    result = script_ns._load_expected_run_id_by_date(tmp_path / "does-not-exist.json")
    assert result == {}


def test_load_expected_run_id_by_date_parses_real_shape(script_ns, tmp_path):
    path = tmp_path / "regen.json"
    path.write_text(json.dumps({"per_date_results": [
        {"date": "2026-05-12", "run_id": 3148}, {"date": "2026-05-13", "run_id": 3149},
    ]}))
    result = script_ns._load_expected_run_id_by_date(path)
    assert result == {"2026-05-12": 3148, "2026-05-13": 3149}


def test_load_stage_d_frozen_identity_honest_none_on_missing_file(script_ns, tmp_path):
    assert script_ns._load_stage_d_frozen_identity(tmp_path / "nope.json") is None


def test_load_stage_d_frozen_identity_parses_real_shape(script_ns, tmp_path):
    path = tmp_path / "identity.json"
    path.write_text(json.dumps({"engine_identity": "abc123"}))
    assert script_ns._load_stage_d_frozen_identity(path) == "abc123"
