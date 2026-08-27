"""goal-market-compass iter-23 -- `scripts/run_j11_disposable_clone.py` CLI control-flow + integration
tests. The confirm-gating test is `unittest.mock`-based (mirrors `test_j11_stage_g_verify_cli_script.py`'s
idiom); the happy-path and failure-path tests run the REAL `app.engine.j11_disposable_clone` functions
against tiny synthetic SQLite fixtures under `tmp_path` -- never `apps/backend/data/trendora.db`."""
from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = BACKEND_DIR / "scripts" / "run_j11_disposable_clone.py"
_MODULE_NAME = "run_j11_disposable_clone_under_test"


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


def _make_fixture_db(path: Path, *, prices: int = 5, manifests: int = 24, max_provider_run_id: int = 549) -> None:
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(
            """
            CREATE TABLE daily_prices (id INTEGER PRIMARY KEY, symbol TEXT, date TEXT, close REAL);
            CREATE TABLE next_session_manifests (id INTEGER PRIMARY KEY, as_of TEXT, version INTEGER);
            CREATE TABLE data_provider_runs (id INTEGER PRIMARY KEY, provider TEXT);
            """
        )
        for i in range(prices):
            conn.execute(
                "INSERT INTO daily_prices (symbol, date, close) VALUES (?, ?, ?)",
                (f"SYM{i}", f"2026-01-{i + 1:02d}", 100.0 + i),
            )
        for i in range(manifests):
            conn.execute(
                "INSERT INTO next_session_manifests (as_of, version) VALUES (?, ?)",
                (f"2026-02-{i + 1:02d}", 1),
            )
        conn.execute(
            "INSERT INTO data_provider_runs (id, provider) VALUES (?, ?)", (max_provider_run_id, "yahoo")
        )
        conn.commit()
    finally:
        conn.close()


# --- missing --confirm: no filesystem interaction ---------------------------------------------------


def test_missing_confirm_never_touches_the_filesystem(monkeypatch, script_ns, tmp_path):
    mock_get_config = mock.MagicMock(name="get_config")
    monkeypatch.setattr(script_ns, "get_config", mock_get_config)

    exit_code = script_ns.main(
        ["--dest-dir", str(tmp_path / "dest"), "--evidence-dir", str(tmp_path / "evidence")]
    )  # no --confirm

    assert exit_code != 0
    mock_get_config.assert_not_called()
    assert not (tmp_path / "dest").exists()
    assert not (tmp_path / "evidence").exists()


def test_missing_required_dest_dir_or_evidence_dir_raises(script_ns):
    with pytest.raises(SystemExit):
        script_ns.main(["--confirm"])  # missing --dest-dir/--evidence-dir


# --- happy path: real functions, tiny fixture DB -------------------------------------------------------


def test_full_run_produces_matching_clone_and_config(monkeypatch, script_ns, tmp_path):
    source_db = tmp_path / "canonical" / "trendora.db"
    source_db.parent.mkdir(parents=True)
    _make_fixture_db(source_db, prices=13, manifests=24, max_provider_run_id=549)

    committed_config = tmp_path / "config.yaml"
    canonical_url = f"sqlite:///{source_db}"
    committed_config.write_text(f'database:\n  url: "{canonical_url}"\n  pool_size: 24\n')

    monkeypatch.setattr(script_ns, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        script_ns, "get_config", lambda: SimpleNamespace(database=SimpleNamespace(url=canonical_url))
    )
    # resolve_database_url normally rebases a relative path onto REPO_ROOT; here the url is already
    # absolute so the real function's behavior is unaffected by monkeypatching REPO_ROOT above.

    dest_dir = tmp_path / "verify-clone"
    evidence_dir = tmp_path / "evidence"

    exit_code = script_ns.main(
        ["--confirm", "--dest-dir", str(dest_dir), "--evidence-dir", str(evidence_dir)]
    )

    assert exit_code == 0
    clone_db = dest_dir / "trendora-clone.db"
    assert clone_db.exists()
    verify_config = dest_dir / "config.verify.yaml"
    assert verify_config.exists()
    assert canonical_url not in verify_config.read_text()
    assert "sqlite:////" in verify_config.read_text()

    # the canonical source db must be byte-unchanged
    assert source_db.stat().st_size > 0
    from app.engine import j11_disposable_clone as jdc

    clone_prov = jdc.capture_db_provenance(clone_db, include_sha256=False)
    assert clone_prov["daily_prices_count"] == 13
    assert clone_prov["next_session_manifests_count"] == 24
    assert clone_prov["data_provider_runs_max_id"] == 549

    import json

    summary = json.loads((evidence_dir / "j11-disposable-clone-summary.json").read_text())
    assert summary["tc1_clone_matches_canonical"] is True
    assert summary["canonical_unchanged"]["equal"] is True
    assert summary["launch_guard_refuses_when_unset"]["raised"] is True


def test_refuses_and_stops_if_canonical_changes_during_clone_creation(monkeypatch, script_ns, tmp_path):
    """A mutation-style proof: force `capture_db_provenance`'s SECOND call (the post-clone canonical
    re-check) to report different content than the first -- the script must detect this and exit
    non-zero rather than proceed to build a verification config."""
    source_db = tmp_path / "canonical" / "trendora.db"
    source_db.parent.mkdir(parents=True)
    _make_fixture_db(source_db)

    canonical_url = f"sqlite:///{source_db}"
    monkeypatch.setattr(script_ns, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        script_ns, "get_config", lambda: SimpleNamespace(database=SimpleNamespace(url=canonical_url))
    )

    real_capture = script_ns.jdc.capture_db_provenance
    call_count = {"n": 0}

    def _flaky_capture(path, **kwargs):
        call_count["n"] += 1
        result = real_capture(path, **kwargs)
        if call_count["n"] == 2:
            result = {**result, "sha256": "deliberately-different-to-simulate-a-mutation"}
        return result

    monkeypatch.setattr(script_ns.jdc, "capture_db_provenance", _flaky_capture)

    dest_dir = tmp_path / "verify-clone"
    evidence_dir = tmp_path / "evidence"

    exit_code = script_ns.main(
        ["--confirm", "--dest-dir", str(dest_dir), "--evidence-dir", str(evidence_dir)]
    )

    assert exit_code != 0
    assert not (dest_dir / "config.verify.yaml").exists()
