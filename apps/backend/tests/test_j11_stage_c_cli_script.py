"""goal-market-compass iter-14 -- J-11 Stage D readiness, Goal 3b: the still-missing CLI control-flow
tests for `scripts/run_j11_stage_c_bounded_clear.py` (TC-19's CLI half). `unittest.mock`-based, NEVER a
live DB -- every DB-touching name (`get_engine`, `Session`, `clear_snapshot_dates`) is patched to a mock
before `main()` runs, so these tests exercise CONTROL FLOW only (which functions get called, in what
order, and which never get called), never real database I/O.

Verified against the CURRENT script (`run_j11_stage_c_bounded_clear.py`) before writing these -- all
three behaviors are genuinely already implemented there, not invented:
  - without `--confirm`, `main()` returns before importing/calling anything DB-related at all;
  - without an explicit `--evidence-dir`, `main()` refuses before writing anything anywhere (added in
    iteration 14's fix pass, after the missing flag in THIS file's gate-failure test let the script fall
    back to its old default and overwrite three committed iteration-13 evidence files);
  - a failing preflight-comparison-gate (`all_invariants_hold: False`) returns before
    `clear_snapshot_dates` is ever called;
  - a failing post-delete `mutation_accounting` (`all_checks_pass: False`) returns before
    `build_completion_marker`/the completion-marker file is ever written.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest import mock

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_stage_c_bounded_clear.py"
_MODULE_NAME = "run_j11_stage_c_bounded_clear_under_test"


def _load_script_module():
    """Loads the script as a REAL module object via `importlib` (never `runpy.run_path` -- its returned
    namespace is a COPY, not the module's actual `__dict__`, so mutating it does not affect what `main()`
    sees at call time; verified directly: `runpy.run_path(...)['main'].__globals__ is <returned dict>` is
    `False`). `importlib.util.module_from_spec` + `exec_module` gives a module whose `__dict__` IS
    `main.__globals__`, so `monkeypatch.setattr(module, name, mock)` genuinely intercepts every call the
    script's top-level code makes to that name -- never executes `main()` itself (only import-time
    module-level code runs, which the script's own `if __name__ == "__main__":` guard keeps `main()` out
    of)."""
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def script_ns(monkeypatch):
    """The script's real, executed module object, with `sys.argv` restored afterward."""
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
    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))
    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
    monkeypatch.setattr(script_ns, "Session", mock_session_cls)
    monkeypatch.setattr(sys, "argv", ["run_j11_stage_c_bounded_clear.py"])  # no --confirm

    exit_code = script_ns.main()

    assert exit_code != 0
    mock_get_engine.assert_not_called()
    mock_session_cls.assert_not_called()


# --- --confirm but no --evidence-dir: refuses, writes nothing anywhere ------------------------------


def test_confirm_without_explicit_evidence_dir_refuses_before_writing_anything(
    monkeypatch, script_ns, capsys
):
    """The guard added after this very test file overwrote three committed iteration-13 Stage C evidence
    files: `--evidence-dir` used to DEFAULT to `runs/goal-market-compass-iter-13`, so a caller that forgot
    the flag wrote its payloads straight over real forensic evidence. There is no implicit default now --
    a committed evidence directory can only be reached by naming it explicitly."""
    mock_write_json = mock.MagicMock(name="_write_json")
    monkeypatch.setattr(script_ns, "_write_json", mock_write_json)
    mock_get_engine = mock.MagicMock(name="get_engine")
    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
    mock_session_cls = mock.MagicMock(name="Session")
    monkeypatch.setattr(script_ns, "Session", mock_session_cls)
    mock_fingerprint = mock.MagicMock(name="db_file_fingerprint", return_value={})
    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock_fingerprint)
    mock_clear = mock.MagicMock(name="clear_snapshot_dates")
    monkeypatch.setattr(script_ns, "clear_snapshot_dates", mock_clear)

    # --confirm present (the destructive-intent flag), --evidence-dir absent
    monkeypatch.setattr(sys, "argv", ["run_j11_stage_c_bounded_clear.py", "--confirm"])

    exit_code = script_ns.main()

    assert exit_code == 2
    mock_write_json.assert_not_called()  # NOTHING is written, to the default path or anywhere else
    mock_get_engine.assert_not_called()
    mock_session_cls.assert_not_called()
    mock_fingerprint.assert_not_called()
    mock_clear.assert_not_called()
    assert "--evidence-dir" in capsys.readouterr().err


# --- comparison-gate failure: clear_snapshot_dates is never called ----------------------------------


def test_comparison_gate_failure_never_calls_clear_snapshot_dates(monkeypatch, script_ns, tmp_path):
    fake_certified_path = tmp_path / "certified.json"
    import json as _json
    fake_certified_path.write_text(_json.dumps({"manifest_row_count": 24}))
    evidence_dir = tmp_path / "evidence"

    mock_engine = mock.MagicMock(name="engine")
    monkeypatch.setattr(script_ns, "get_engine", mock.MagicMock(return_value=mock_engine))
    mock_session_instance = mock.MagicMock(name="session_instance")
    mock_session_cm = mock.MagicMock()
    mock_session_cm.__enter__ = mock.MagicMock(return_value=mock_session_instance)
    mock_session_cm.__exit__ = mock.MagicMock(return_value=False)
    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(return_value=mock_session_cm))

    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))
    monkeypatch.setattr(script_ns.jsc, "read_goal_md_text", mock.MagicMock(return_value="goal md text"))
    monkeypatch.setattr(script_ns.jsc, "read_git_head", mock.MagicMock(return_value="deadbeef"))
    monkeypatch.setattr(
        script_ns.jsc, "capture_stage_c_preflight",
        mock.MagicMock(return_value={
            "captured_at": "2026-01-01T00:00:00+00:00",
            "manifest_row_count": 24,
            "c1_date_set_boundary_check": {"ok": True},
        }),
    )
    monkeypatch.setattr(
        script_ns.jsc, "compare_preflight_to_certified",
        mock.MagicMock(return_value={
            "all_invariants_hold": False, "material_mismatch": True,
            "checks": {"manifest_row_count_matches_certified": False}, "generated_at": "x",
        }),
    )

    mock_clear = mock.MagicMock(name="clear_snapshot_dates")
    monkeypatch.setattr(script_ns, "clear_snapshot_dates", mock_clear)

    monkeypatch.setattr(
        sys, "argv",
        [
            "run_j11_stage_c_bounded_clear.py", "--confirm",
            "--certified-state-path", str(fake_certified_path),
            # MANDATORY in every test that reaches the write path: without it the script used to fall back
            # to the REAL committed runs/goal-market-compass-iter-13/ directory and this test overwrote
            # three of iteration 13's Stage C evidence files with the mocked payloads above.
            "--evidence-dir", str(evidence_dir),
        ],
    )

    exit_code = script_ns.main()

    assert exit_code != 0
    mock_clear.assert_not_called()
    # the pre-gate evidence went to tmp_path, and only there
    assert (evidence_dir / "j11-stage-c-preflight.json").exists()
    assert (evidence_dir / "j11-stage-c-preflight-comparison-gate.json").exists()


# --- a failing check anywhere: no completion marker is written --------------------------------------


def test_failed_mutation_accounting_never_writes_a_completion_marker(monkeypatch, script_ns, tmp_path):
    fake_certified_path = tmp_path / "certified.json"
    import json as _json
    fake_certified_path.write_text(_json.dumps({"manifest_row_count": 24}))
    evidence_dir = tmp_path / "evidence"

    mock_engine = mock.MagicMock(name="engine")
    monkeypatch.setattr(script_ns, "get_engine", mock.MagicMock(return_value=mock_engine))
    mock_session_instance = mock.MagicMock(name="session_instance")
    mock_session_cm = mock.MagicMock()
    mock_session_cm.__enter__ = mock.MagicMock(return_value=mock_session_instance)
    mock_session_cm.__exit__ = mock.MagicMock(return_value=False)
    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(return_value=mock_session_cm))

    monkeypatch.setattr(script_ns.jsc, "db_file_fingerprint", mock.MagicMock(return_value={}))
    monkeypatch.setattr(script_ns.jsc, "read_goal_md_text", mock.MagicMock(return_value="goal md text"))
    monkeypatch.setattr(script_ns.jsc, "read_git_head", mock.MagicMock(return_value="deadbeef"))
    monkeypatch.setattr(
        script_ns.jsc, "capture_stage_c_preflight",
        mock.MagicMock(return_value={
            "captured_at": "2026-01-01T00:00:00+00:00",
            "manifest_row_count": 24,
            "c1_date_set_boundary_check": {"ok": True},
        }),
    )
    monkeypatch.setattr(
        script_ns.jsc, "compare_preflight_to_certified",
        mock.MagicMock(return_value={
            "all_invariants_hold": True, "material_mismatch": False,
            "checks": {}, "generated_at": "2026-01-01T00:00:01+00:00",
        }),
    )
    monkeypatch.setattr(
        script_ns.jsc, "capture_intended_delete_set",
        mock.MagicMock(return_value={
            "captured_at": "2026-01-01T00:00:02+00:00",
            "total_counts": {}, "deleted_run_ids": [], "per_date": {},
        }),
    )
    monkeypatch.setattr(script_ns.jsc, "capture_layer2_population_fingerprints", mock.MagicMock(return_value={}))
    monkeypatch.setattr(script_ns.jsc, "incident_scoped_counts", mock.MagicMock(return_value={}))
    monkeypatch.setattr(script_ns.jsc, "small_table_id_snapshot", mock.MagicMock(return_value={"count": 0, "ids": []}))
    monkeypatch.setattr(script_ns.migration, "capture_full_db_snapshot", mock.MagicMock(return_value={"tables": {}}))
    monkeypatch.setattr(script_ns.migration, "dump_table", mock.MagicMock(return_value=[]))
    monkeypatch.setattr(
        script_ns, "capture_pre_reset_inventory",
        mock.MagicMock(return_value={"daily_prices": {"row_count": 0, "fingerprint": "x"}}),
    )

    mock_clear = mock.MagicMock(
        name="clear_snapshot_dates",
        return_value={"totals": {}, "per_date": {}},
    )
    monkeypatch.setattr(script_ns, "clear_snapshot_dates", mock_clear)

    monkeypatch.setattr(
        script_ns.jsc, "build_mutation_accounting",
        mock.MagicMock(return_value={
            "generated_at": "2026-01-01T00:00:03+00:00",
            "all_checks_pass": False,
            "checks": {"daily_prices_unchanged": False},
        }),
    )
    mock_build_marker = mock.MagicMock(name="build_completion_marker")
    monkeypatch.setattr(script_ns.jsc, "build_completion_marker", mock_build_marker)
    monkeypatch.setattr(
        script_ns.jsc, "stage_c_overall_verdict",
        mock.MagicMock(return_value={"passed": False, "reason": "post_delete_verification_failed"}),
    )

    monkeypatch.setattr(
        sys, "argv",
        [
            "run_j11_stage_c_bounded_clear.py", "--confirm",
            "--certified-state-path", str(fake_certified_path),
            "--evidence-dir", str(evidence_dir),
        ],
    )

    exit_code = script_ns.main()

    assert exit_code != 0
    mock_clear.assert_called_once()  # the gate passed, so the ONE authorized write DID run this time...
    mock_build_marker.assert_not_called()  # ...but post-delete verification failed, so NO marker is built
    assert not (evidence_dir / "j11-stage-c-complete.json").exists()
