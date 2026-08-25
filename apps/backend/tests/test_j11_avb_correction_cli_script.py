"""goal-market-compass iter-16 -- J-11 AVB correction CLI control-flow tests (Goal 3). `unittest.mock`-
based, NEVER a live DB -- every DB-touching name (`get_engine`, `Session`) is patched before `main()`
runs, mirroring `test_j11_stage_c_cli_script.py`'s established idiom exactly (same `importlib`-based real
module load, same monkeypatch-on-module-namespace pattern, same reasoning for why `importlib.util.
module_from_spec` is used instead of `runpy.run_path`)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest import mock

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_avb_correction.py"
_MODULE_NAME = "run_j11_avb_correction_under_test"


def _load_script_module():
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


# --- missing --confirm: NO database interaction of any kind -------------------------------------------


def test_missing_confirm_never_calls_get_engine_or_session(monkeypatch, script_ns):
    mock_get_engine = mock.MagicMock(name="get_engine")
    mock_session_cls = mock.MagicMock(name="Session")
    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
    monkeypatch.setattr(script_ns, "Session", mock_session_cls)
    monkeypatch.setattr(sys, "argv", ["run_j11_avb_correction.py"])  # no --confirm

    exit_code = script_ns.main()

    assert exit_code != 0
    mock_get_engine.assert_not_called()
    mock_session_cls.assert_not_called()


# --- --confirm but missing --evidence-dir and/or --output-path: refuses, writes nothing ----------------


def test_confirm_without_evidence_dir_refuses_before_writing_anything(monkeypatch, script_ns):
    mock_write_json = mock.MagicMock(name="_write_json")
    mock_get_engine = mock.MagicMock(name="get_engine")
    monkeypatch.setattr(script_ns, "_write_json", mock_write_json)
    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
    monkeypatch.setattr(
        sys, "argv",
        ["run_j11_avb_correction.py", "--confirm", "--output-path", "/tmp/out.json"],  # no --evidence-dir
    )

    exit_code = script_ns.main()

    assert exit_code != 0
    mock_write_json.assert_not_called()
    mock_get_engine.assert_not_called()


def test_confirm_without_output_path_refuses_before_writing_anything(monkeypatch, script_ns):
    mock_write_json = mock.MagicMock(name="_write_json")
    mock_get_engine = mock.MagicMock(name="get_engine")
    monkeypatch.setattr(script_ns, "_write_json", mock_write_json)
    monkeypatch.setattr(script_ns, "get_engine", mock_get_engine)
    monkeypatch.setattr(
        sys, "argv",
        ["run_j11_avb_correction.py", "--confirm", "--evidence-dir", "/tmp/ev"],  # no --output-path
    )

    exit_code = script_ns.main()

    assert exit_code != 0
    mock_write_json.assert_not_called()
    mock_get_engine.assert_not_called()


# --- true-start comparison mismatch stops BEFORE any derivation/write ----------------------------------


def test_true_start_mismatch_stops_before_derivation_and_write(monkeypatch, script_ns, tmp_path):
    fake_true_start = {"daily_prices": {"row_count": 1}, "avb_target_rows": {}, "db_file": {}}
    monkeypatch.setattr(script_ns, "load_config", lambda: mock.MagicMock(database=mock.MagicMock(url="sqlite:///x")))
    monkeypatch.setattr(script_ns, "resolve_database_url", lambda url: "sqlite:///x")
    monkeypatch.setattr(script_ns, "get_engine", mock.MagicMock(name="get_engine"))
    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(name="Session"))
    monkeypatch.setattr(script_ns.corr, "capture_true_envelope", lambda *a, **k: fake_true_start)
    monkeypatch.setattr(
        script_ns.corr, "compare_true_envelope_to_coordinator_capture",
        lambda *a, **k: {"any_mismatch": True, "comparisons": {"x": {"matches": False}}},
    )
    mock_derive = mock.MagicMock(name="derive_avb_volume_correction")
    mock_apply = mock.MagicMock(name="apply_avb_volume_correction")
    monkeypatch.setattr(script_ns.corr, "derive_avb_volume_correction", mock_derive)
    monkeypatch.setattr(script_ns.corr, "apply_avb_volume_correction", mock_apply)

    evidence_dir = tmp_path / "ev"
    output_path = tmp_path / "out.json"
    monkeypatch.setattr(
        sys, "argv",
        [
            "run_j11_avb_correction.py", "--confirm",
            "--evidence-dir", str(evidence_dir), "--output-path", str(output_path),
        ],
    )

    exit_code = script_ns.main()

    assert exit_code != 0
    mock_derive.assert_not_called()
    mock_apply.assert_not_called()
    assert not output_path.exists()  # the final consolidated artifact is never written


# --- derivation not verified: stops BEFORE the write, nothing written to output-path --------------------


def test_derivation_not_verified_stops_before_the_write(monkeypatch, script_ns, tmp_path):
    fake_true_start = {
        "daily_prices": {"row_count": 1}, "db_file": {},
        "avb_target_rows": {"2026-08-11": {"volume": 1.0, "close": 1.0}, "2026-08-12": {"volume": 2.0, "close": 2.0}},
    }
    monkeypatch.setattr(script_ns, "load_config", lambda: mock.MagicMock(database=mock.MagicMock(url="sqlite:///x")))
    monkeypatch.setattr(script_ns, "resolve_database_url", lambda url: "sqlite:///x")
    monkeypatch.setattr(script_ns, "get_engine", mock.MagicMock(name="get_engine"))
    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(name="Session"))
    monkeypatch.setattr(script_ns.corr, "capture_true_envelope", lambda *a, **k: fake_true_start)
    monkeypatch.setattr(
        script_ns.corr, "compare_true_envelope_to_coordinator_capture",
        lambda *a, **k: {"any_mismatch": False, "comparisons": {}},
    )
    monkeypatch.setattr(script_ns.corr, "load_provider_fetch_evidence", lambda *a, **k: {})
    monkeypatch.setattr(script_ns.diag, "load_j10_avb_evidence", lambda *a, **k: {})
    monkeypatch.setattr(
        script_ns.corr, "derive_avb_volume_correction",
        lambda *a, **k: {"verified": False, "per_date": {}},
    )
    mock_apply = mock.MagicMock(name="apply_avb_volume_correction")
    monkeypatch.setattr(script_ns.corr, "apply_avb_volume_correction", mock_apply)

    evidence_dir = tmp_path / "ev"
    output_path = tmp_path / "out.json"
    monkeypatch.setattr(
        sys, "argv",
        [
            "run_j11_avb_correction.py", "--confirm",
            "--evidence-dir", str(evidence_dir), "--output-path", str(output_path),
        ],
    )

    exit_code = script_ns.main()

    assert exit_code != 0
    mock_apply.assert_not_called()  # the ONE write must never execute on an unverified derivation
    assert not output_path.exists()
    assert (evidence_dir / "j11-avb-correction-derivation.json").exists()  # the failure evidence IS persisted


# --- happy path: exactly one apply call, all expected files written, success exit ----------------------


def test_success_path_calls_apply_exactly_once_and_writes_all_artifacts(monkeypatch, script_ns, tmp_path):
    fake_true_start = {
        "daily_prices": {"row_count": 1, "min_date": "2026-01-01", "max_date": "2026-08-12", "id_sum": 1, "ohlcv_sum": 100.0},
        "db_file": {"mtime": 1, "size_bytes": 1, "wal": {"exists": False}},
        "avb_target_rows": {
            "2026-08-11": {"open": 1, "high": 1, "low": 1, "close": 1.0, "volume": 10.0},
            "2026-08-12": {"open": 1, "high": 1, "low": 1, "close": 1.0, "volume": 20.0},
        },
        "isolating_hashes": {
            "avb_ohlc_only": {"sha256": "a"}, "avb_other_dates_full_row": {"sha256": "b"}, "non_avb_full_row": {"sha256": "c"},
        },
        "scanner_runs_by_identity_group": {}, "forward_returns_total_count": 0,
        "forward_returns_measured_into_incident_total": 0, "data_provider_runs_count": 0,
        "manifest_row_count": 0, "manifest_ddl_sha256": "d", "manifest_row_dump_fingerprint": {"sha256": "e"},
        "watchlist_count": 0, "all_11_incident_dates_zero_scanner_runs": True,
    }
    fake_true_end = {
        **fake_true_start,
        "avb_target_rows": {
            "2026-08-11": {"open": 1, "high": 1, "low": 1, "close": 1.0, "volume": 5.0},
            "2026-08-12": {"open": 1, "high": 1, "low": 1, "close": 1.0, "volume": 8.0},
        },
        "daily_prices": {
            "row_count": 1, "min_date": "2026-01-01", "max_date": "2026-08-12", "id_sum": 1,
            "ohlcv_sum": 100.0 - (10.0 - 5.0) - (20.0 - 8.0),
        },
        "db_file": {"mtime": 2, "size_bytes": 2, "wal": {"exists": False}},
    }
    envelopes = iter([fake_true_start, fake_true_end])
    monkeypatch.setattr(script_ns, "load_config", lambda: mock.MagicMock(database=mock.MagicMock(url="sqlite:///x")))
    monkeypatch.setattr(script_ns, "resolve_database_url", lambda url: "sqlite:///x")
    monkeypatch.setattr(script_ns, "get_engine", mock.MagicMock(name="get_engine"))
    monkeypatch.setattr(script_ns, "Session", mock.MagicMock(name="Session"))
    monkeypatch.setattr(script_ns.corr, "capture_true_envelope", lambda *a, **k: next(envelopes))
    monkeypatch.setattr(
        script_ns.corr, "compare_true_envelope_to_coordinator_capture",
        lambda *a, **k: {"any_mismatch": False, "comparisons": {}},
    )
    monkeypatch.setattr(script_ns.corr, "load_provider_fetch_evidence", lambda *a, **k: {})
    monkeypatch.setattr(script_ns.diag, "load_j10_avb_evidence", lambda *a, **k: {})
    monkeypatch.setattr(
        script_ns.corr, "derive_avb_volume_correction",
        lambda *a, **k: {
            "verified": True,
            "per_date": {"2026-08-11": {"corrected_volume": 5.0}, "2026-08-12": {"corrected_volume": 8.0}},
        },
    )
    mock_apply = mock.MagicMock(name="apply_avb_volume_correction", return_value={"2026-08-11": 5.0, "2026-08-12": 8.0})
    monkeypatch.setattr(script_ns.corr, "apply_avb_volume_correction", mock_apply)
    monkeypatch.setattr(
        script_ns.corr, "checkpoint_wal", lambda *a, **k: {"busy": 0, "log_pages": 0, "checkpointed_pages": 0}
    )

    evidence_dir = tmp_path / "ev"
    output_path = tmp_path / "out.json"
    monkeypatch.setattr(
        sys, "argv",
        [
            "run_j11_avb_correction.py", "--confirm",
            "--evidence-dir", str(evidence_dir), "--output-path", str(output_path),
        ],
    )

    exit_code = script_ns.main()

    assert exit_code == 0
    mock_apply.assert_called_once()
    assert (evidence_dir / "j11-avb-correction-true-start.json").exists()
    assert (evidence_dir / "j11-avb-correction-true-start-comparison.json").exists()
    assert (evidence_dir / "j11-avb-correction-derivation.json").exists()
    assert (evidence_dir / "j11-avb-correction-true-end.json").exists()
    assert output_path.exists()
