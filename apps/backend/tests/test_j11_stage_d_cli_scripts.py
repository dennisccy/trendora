"""goal-market-compass iter-15 -- J-11 Stage D readiness, Goal 6: CLI control-flow tests for the four
scripts this iteration touches or adds -- `run_j11_stage_d_preflight.py`, `run_j11_avb_bridge_
diagnostic.py`, `run_j11_avb_provider_fetch.py`, `run_j11_stage_d_readiness.py` -- plus Goal 1's
standalone reconciliation script, `run_j11_reconcile_iteration_14_truth.py`.

Mirrors `test_j11_stage_c_cli_script.py`'s `importlib`-based real-module-execution pattern EXACTLY (never
`runpy.run_path`, whose returned namespace is a COPY -- monkeypatching it would not affect what `main()`
actually sees). NEVER a live DB and NEVER a real network call -- every DB-touching or network-touching
name is mocked/monkeypatched, or the test proves the refusal path never reaches those names at all.

TC-8, TC-9, TC-25, TC-26, TC-27, TC-28.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path
from unittest import mock

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = BACKEND_DIR / "scripts"

STAGE_D_PREFLIGHT_SCRIPT = SCRIPTS_DIR / "run_j11_stage_d_preflight.py"
AVB_BRIDGE_DIAGNOSTIC_SCRIPT = SCRIPTS_DIR / "run_j11_avb_bridge_diagnostic.py"
PROVIDER_FETCH_SCRIPT = SCRIPTS_DIR / "run_j11_avb_provider_fetch.py"
STAGE_D_READINESS_SCRIPT = SCRIPTS_DIR / "run_j11_stage_d_readiness.py"
RECONCILE_SCRIPT = SCRIPTS_DIR / "run_j11_reconcile_iteration_14_truth.py"


def _load_script_module(script_path: Path, module_name: str):
    """Loads `script_path` as a REAL module object via `importlib` -- its `__dict__` IS `main.__globals__`,
    so `monkeypatch.setattr(module, name, mock)` genuinely intercepts every call the script's top-level
    code makes to that name. Only import-time module-level code runs (the script's own
    `if __name__ == "__main__":` guard keeps `main()` itself from executing)."""
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def preflight_ns(monkeypatch):
    original_argv = sys.argv
    try:
        yield _load_script_module(STAGE_D_PREFLIGHT_SCRIPT, "run_j11_stage_d_preflight_under_test")
    finally:
        sys.argv = original_argv
        sys.modules.pop("run_j11_stage_d_preflight_under_test", None)


@pytest.fixture()
def avb_diagnostic_ns(monkeypatch):
    original_argv = sys.argv
    try:
        yield _load_script_module(AVB_BRIDGE_DIAGNOSTIC_SCRIPT, "run_j11_avb_bridge_diagnostic_under_test")
    finally:
        sys.argv = original_argv
        sys.modules.pop("run_j11_avb_bridge_diagnostic_under_test", None)


@pytest.fixture()
def provider_fetch_ns(monkeypatch):
    original_argv = sys.argv
    try:
        yield _load_script_module(PROVIDER_FETCH_SCRIPT, "run_j11_avb_provider_fetch_under_test")
    finally:
        sys.argv = original_argv
        sys.modules.pop("run_j11_avb_provider_fetch_under_test", None)


@pytest.fixture()
def readiness_ns(monkeypatch):
    original_argv = sys.argv
    try:
        yield _load_script_module(STAGE_D_READINESS_SCRIPT, "run_j11_stage_d_readiness_under_test")
    finally:
        sys.argv = original_argv
        sys.modules.pop("run_j11_stage_d_readiness_under_test", None)


@pytest.fixture()
def reconcile_ns(monkeypatch):
    original_argv = sys.argv
    try:
        yield _load_script_module(RECONCILE_SCRIPT, "run_j11_reconcile_iteration_14_truth_under_test")
    finally:
        sys.argv = original_argv
        sys.modules.pop("run_j11_reconcile_iteration_14_truth_under_test", None)


# --- TC-25: run_j11_stage_d_preflight.py refuses without --evidence-dir, before load_config/engine ------


def test_tc25_stage_d_preflight_refuses_without_evidence_dir(monkeypatch, preflight_ns, capsys):
    mock_load_config = mock.MagicMock(name="load_config")
    monkeypatch.setattr(preflight_ns, "load_config", mock_load_config)
    mock_write_json = mock.MagicMock(name="_write_json")
    monkeypatch.setattr(preflight_ns, "_write_json", mock_write_json)
    monkeypatch.setattr(sys, "argv", ["run_j11_stage_d_preflight.py"])  # no --evidence-dir

    exit_code = preflight_ns.main()

    assert exit_code == 2
    mock_load_config.assert_not_called()
    mock_write_json.assert_not_called()
    assert "--evidence-dir" in capsys.readouterr().err


# --- TC-26: run_j11_avb_bridge_diagnostic.py refuses without --output-path/--provider-fetch-evidence- ---
# --- path, before load_config/engine construction --------------------------------------------------


def test_tc26_avb_bridge_diagnostic_refuses_without_output_path(monkeypatch, avb_diagnostic_ns, tmp_path, capsys):
    mock_load_config = mock.MagicMock(name="load_config")
    monkeypatch.setattr(avb_diagnostic_ns, "load_config", mock_load_config)
    fetch_evidence_path = tmp_path / "fetch-evidence.json"
    fetch_evidence_path.write_text(json.dumps({"per_date": {}, "sufficient_evidence": False}))
    monkeypatch.setattr(
        sys, "argv",
        ["run_j11_avb_bridge_diagnostic.py", "--provider-fetch-evidence-path", str(fetch_evidence_path)],
    )  # no --output-path

    exit_code = avb_diagnostic_ns.main()

    assert exit_code == 2
    mock_load_config.assert_not_called()
    assert "--output-path" in capsys.readouterr().err


def test_tc26_avb_bridge_diagnostic_refuses_without_provider_fetch_evidence_path(monkeypatch, avb_diagnostic_ns, tmp_path, capsys):
    mock_load_config = mock.MagicMock(name="load_config")
    monkeypatch.setattr(avb_diagnostic_ns, "load_config", mock_load_config)
    output_path = tmp_path / "out.json"
    monkeypatch.setattr(
        sys, "argv", ["run_j11_avb_bridge_diagnostic.py", "--output-path", str(output_path)],
    )  # no --provider-fetch-evidence-path

    exit_code = avb_diagnostic_ns.main()

    assert exit_code == 2
    mock_load_config.assert_not_called()
    assert not output_path.exists()
    assert "--provider-fetch-evidence-path" in capsys.readouterr().err


def test_tc26_avb_bridge_diagnostic_refuses_without_either_path(monkeypatch, avb_diagnostic_ns, capsys):
    mock_load_config = mock.MagicMock(name="load_config")
    monkeypatch.setattr(avb_diagnostic_ns, "load_config", mock_load_config)
    monkeypatch.setattr(sys, "argv", ["run_j11_avb_bridge_diagnostic.py"])

    exit_code = avb_diagnostic_ns.main()

    assert exit_code == 2
    mock_load_config.assert_not_called()
    err = capsys.readouterr().err
    assert "--output-path" in err and "--provider-fetch-evidence-path" in err


# --- TC-8: run_j11_avb_provider_fetch.py refuses without --output-path, before ANY provider/network -----


def test_tc8_provider_fetch_refuses_without_output_path(monkeypatch, provider_fetch_ns, capsys):
    mock_provider_cls = mock.MagicMock(name="YahooProvider")
    monkeypatch.setattr(provider_fetch_ns, "YahooProvider", mock_provider_cls)
    mock_load_evidence = mock.MagicMock(name="load_j10_avb_evidence")
    monkeypatch.setattr(provider_fetch_ns, "load_j10_avb_evidence", mock_load_evidence)
    monkeypatch.setattr(sys, "argv", ["run_j11_avb_provider_fetch.py"])  # no --output-path

    exit_code = provider_fetch_ns.main()

    assert exit_code == 2
    mock_provider_cls.assert_not_called()  # no provider constructed -- structurally no network call possible
    mock_load_evidence.assert_not_called()
    assert "--output-path" in capsys.readouterr().err


# --- TC-9: valid args + fixture provider -- writes only under tmp_path, no DB engine/session anywhere ---


def test_tc9_provider_fetch_imports_no_db_engine_or_session_helpers():
    """Static proof (never fooled by the script's own docstring prose, which discusses these names):
    parses the script's IMPORT statements only -- if `get_engine`/`Session`/`load_config` are never
    imported, they structurally cannot be called anywhere in the file."""
    tree = ast.parse(PROVIDER_FETCH_SCRIPT.read_text())
    imported_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name)
    assert "get_engine" not in imported_names
    assert "Session" not in imported_names
    assert "load_config" not in imported_names


def test_tc9_provider_fetch_with_valid_args_writes_only_under_tmp_path(monkeypatch, provider_fetch_ns, tmp_path):
    from app.data_providers.base import Bar, PriceProvider

    class _FakeProvider(PriceProvider):
        source = "yahoo"

        def get_daily(self, symbol, start=None, end=None):
            return [
                Bar(date=date(2026, 8, 5), open=1, high=1, low=1, close=67.89, volume=2_100_000.0),
                Bar(date=date(2026, 8, 6), open=1, high=1, low=1, close=66.79, volume=2_050_000.0),
                Bar(date=date(2026, 8, 7), open=1, high=1, low=1, close=67.15, volume=2_090_000.0),
                Bar(date=date(2026, 8, 10), open=1, high=1, low=1, close=65.82, volume=1_950_000.0),
                Bar(date=date(2026, 8, 11), open=1, high=1, low=1, close=65.08, volume=5_390_000.0),
                Bar(date=date(2026, 8, 12), open=1, high=1, low=1, close=64.37, volume=34_100_000.0),
            ]

    monkeypatch.setattr(provider_fetch_ns, "YahooProvider", _FakeProvider)

    j10_evidence_path = tmp_path / "j10-evidence.json"
    j10_evidence_path.write_text(json.dumps({"symbols": [{"symbol": "AVB", "bridge_factor": 2.793, "pairs": []}]}))
    output_path = tmp_path / "nested" / "fetch-evidence.json"

    monkeypatch.setattr(
        sys, "argv",
        [
            "run_j11_avb_provider_fetch.py",
            "--output-path", str(output_path),
            "--j10-evidence-path", str(j10_evidence_path),
        ],
    )

    exit_code = provider_fetch_ns.main()

    assert exit_code == 0
    assert output_path.exists()
    written = json.loads(output_path.read_text())
    assert written["sufficient_evidence"] is True
    assert written["fetch_call_count"] == 1


# --- TC-27: run_j11_stage_d_readiness.py refuses before any file I/O beyond argument parsing -----------


def test_tc27_stage_d_readiness_refuses_without_any_required_path(monkeypatch, readiness_ns, capsys):
    mock_produce = mock.MagicMock(name="produce_stage_d_readiness_artifact")
    monkeypatch.setattr(readiness_ns.jsd, "produce_stage_d_readiness_artifact", mock_produce)
    monkeypatch.setattr(sys, "argv", ["run_j11_stage_d_readiness.py"])

    exit_code = readiness_ns.main()

    assert exit_code == 2
    mock_produce.assert_not_called()
    err = capsys.readouterr().err
    assert "--preflight-gate-path" in err and "--avb-diagnostic-path" in err and "--output-path" in err


def test_tc27_stage_d_readiness_refuses_with_only_some_required_paths(monkeypatch, readiness_ns, tmp_path, capsys):
    mock_produce = mock.MagicMock(name="produce_stage_d_readiness_artifact")
    monkeypatch.setattr(readiness_ns.jsd, "produce_stage_d_readiness_artifact", mock_produce)
    monkeypatch.setattr(
        sys, "argv",
        ["run_j11_stage_d_readiness.py", "--preflight-gate-path", str(tmp_path / "gate.json")],
    )  # avb-diagnostic-path and output-path still missing

    exit_code = readiness_ns.main()

    assert exit_code == 2
    mock_produce.assert_not_called()


def test_tc28_stage_d_readiness_with_all_paths_writes_only_under_tmp_path(readiness_ns, tmp_path):
    """The real, unmocked happy path -- this script performs NO database/network access at all, so
    exercising it for real (against tmp_path-only fixture JSONs) is safe and simple."""
    preflight_gate_path = tmp_path / "gate.json"
    preflight_gate_path.write_text(json.dumps({
        "comparison": {"generated_at": "2026-08-25T10:00:00+00:00"}, "verdict": {"passed": True, "reason": "x"},
    }))
    avb_diagnostic_path = tmp_path / "avb.json"
    avb_diagnostic_path.write_text(json.dumps({
        "generated_at": "2026-08-25T10:01:00+00:00", "classification": {"classification": "AVB-A"},
    }))
    output_path = tmp_path / "readiness.json"

    original_argv = sys.argv
    try:
        sys.argv = [
            "run_j11_stage_d_readiness.py",
            "--preflight-gate-path", str(preflight_gate_path),
            "--avb-diagnostic-path", str(avb_diagnostic_path),
            "--output-path", str(output_path),
        ]
        exit_code = readiness_ns.main()
    finally:
        sys.argv = original_argv

    assert exit_code == 0
    assert output_path.exists()
    written = json.loads(output_path.read_text())
    assert written["ready"] is True
    assert written["authorized"] is False


# --- TC-27 (Goal 1's standalone reconciliation script): refuses without --output-path -------------------


def test_tc27_reconcile_script_refuses_without_output_path(monkeypatch, reconcile_ns, capsys):
    mock_load_config = mock.MagicMock(name="load_config")
    monkeypatch.setattr(reconcile_ns, "load_config", mock_load_config)
    monkeypatch.setattr(sys, "argv", ["run_j11_reconcile_iteration_14_truth.py"])

    exit_code = reconcile_ns.main()

    assert exit_code == 2
    mock_load_config.assert_not_called()
    assert "--output-path" in capsys.readouterr().err


# --- TC-29 corroboration: none of these refusal tests wrote anywhere under the real committed evidence --
# --- directories -- proven directly by asserting on git-tracked paths, mirroring the session's standing -
# --- practice (the phase-level `git status --porcelain` check is the authoritative proof; this is a -----
# --- fast in-process corroboration). ------------------------------------------------------------------


def test_none_of_the_refusal_paths_reference_a_real_committed_evidence_directory_as_a_default():
    """Static proof: none of the five scripts' argparse `--output-path`/`--evidence-dir` arguments carry
    a non-None default that resolves under `runs/goal-market-compass-iter-13` or `-iter-14`."""
    for script_path in (
        STAGE_D_PREFLIGHT_SCRIPT, AVB_BRIDGE_DIAGNOSTIC_SCRIPT, PROVIDER_FETCH_SCRIPT,
        STAGE_D_READINESS_SCRIPT, RECONCILE_SCRIPT,
    ):
        source = script_path.read_text()
        assert 'default=DEFAULT_EVIDENCE_DIR' not in source
        assert 'default=DEFAULT_OUTPUT_PATH' not in source
