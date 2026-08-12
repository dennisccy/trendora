"""ops-hardening iter-66 (J-07, TC-4/TC-5) — the canonical `scripts/qa/poll_health.py` health-poll drill
script: CSV schema (TC-4) + the host-load column (TC-5).

Loads `scripts/qa/poll_health.py` via `importlib.util.spec_from_file_location`, exactly as
`test_gate_registry_enforcement.py::_load_gate` / `test_staging_ledger_routing.py::_load_gate` already do
for other project-tooling scripts that live outside the `app` package. No live HTTP call is made — `urllib
.request.urlopen` is monkeypatched to a stub response so this test needs no running backend.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import time
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "qa" / "poll_health.py"


def _load_poll_health():
    spec = importlib.util.spec_from_file_location("poll_health_test_module", _SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def poll_health():
    return _load_poll_health()


class _FakeResponse:
    def __init__(self, status: int, body: bytes = b"{}"):
        self.status = status
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_csv_fields_match_tc4_schema(poll_health):
    """TC-4: the CSV column schema is EXACTLY these five names, in this order."""
    assert poll_health.CSV_FIELDS == [
        "timestamp", "http_status", "elapsed_s", "breach_over_2s", "load_avg_1m",
    ]


def test_poll_once_records_populated_load_avg_1m(monkeypatch, poll_health):
    """TC-5: every poll row carries a non-null `load_avg_1m` sampled at poll time."""
    monkeypatch.setattr(poll_health, "host_load_avg_1m", lambda: 1.23)
    monkeypatch.setattr(
        poll_health.urllib.request, "urlopen", lambda req, timeout=5.0: _FakeResponse(200),
    )
    row = poll_health.poll_once("http://example.invalid/api/health")
    assert row["load_avg_1m"] == 1.23
    assert row["http_status"] == 200
    assert row["breach_over_2s"] == 0
    assert isinstance(row["elapsed_s"], float)
    assert row["timestamp"]  # non-empty ISO-8601 string


def test_poll_once_flags_breach_over_2s(monkeypatch, poll_health):
    """A poll whose wall-clock duration exceeds HEALTH_CEILING_S (2.0s) is flagged, not silently recorded."""
    def _slow_urlopen(req, timeout=5.0):
        time.sleep(0)  # keep the test fast; simulate elapsed time via monkeypatched monotonic instead
        return _FakeResponse(200)

    times = iter([0.0, 2.5])  # t0, t1 -> elapsed_s = 2.5
    monkeypatch.setattr(poll_health.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(poll_health, "host_load_avg_1m", lambda: 0.5)
    monkeypatch.setattr(poll_health.urllib.request, "urlopen", _slow_urlopen)
    row = poll_health.poll_once("http://example.invalid/api/health")
    assert row["elapsed_s"] == 2.5
    assert row["breach_over_2s"] == 1


def test_poll_once_records_status_zero_on_connection_error(monkeypatch, poll_health):
    """A starved/unreachable client is recorded as http_status=0, never fabricated as a fake 200."""
    def _raise(req, timeout=5.0):
        raise OSError("connection refused")

    monkeypatch.setattr(poll_health.urllib.request, "urlopen", _raise)
    monkeypatch.setattr(poll_health, "host_load_avg_1m", lambda: 0.1)
    row = poll_health.poll_once("http://example.invalid/api/health")
    assert row["http_status"] == 0


def test_run_writes_exact_schema_and_meta_json(tmp_path, monkeypatch, poll_health):
    """`run()` (the canonical entry both the dev evidence-drill and the browser-qa J-07 case call) writes
    one CSV row per poll with the TC-4 header, plus a sibling `.meta.json` carrying `cpu_count` (the IN
    SCOPE ask's other host-load figure, recorded once per run rather than duplicated onto every row —
    see the script's own module docstring for the rationale)."""
    monkeypatch.setattr(poll_health, "host_load_avg_1m", lambda: 2.0)
    monkeypatch.setattr(
        poll_health.urllib.request, "urlopen", lambda req, timeout=5.0: _FakeResponse(200),
    )
    out_path = tmp_path / "poll.csv"
    rows_written = poll_health.run(
        "http://example.invalid/api/health", str(out_path), None, count=3, interval_s=0.0,
    )
    assert rows_written == 3

    with open(out_path, newline="") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == poll_health.CSV_FIELDS
        rows = list(reader)
    assert len(rows) == 3
    for row in rows:
        assert row["load_avg_1m"] == "2.0"
        assert row["http_status"] == "200"
        assert row["breach_over_2s"] == "0"

    meta_path = Path(str(out_path) + ".meta.json")
    assert meta_path.exists()
    meta = json.loads(meta_path.read_text())
    assert meta["cpu_count"] == poll_health.os.cpu_count()
    assert meta["rows"] == 3
    assert meta["health_ceiling_s"] == 2.0


def test_run_stops_on_stop_file(tmp_path, monkeypatch, poll_health):
    """No `count` given: `run()` polls until `stop_file` appears (the pre-existing per-iteration scripts'
    own convention, preserved verbatim for the browser-qa lane's long-running drills)."""
    monkeypatch.setattr(poll_health, "host_load_avg_1m", lambda: 0.75)
    monkeypatch.setattr(
        poll_health.urllib.request, "urlopen", lambda req, timeout=5.0: _FakeResponse(200),
    )
    out_path = tmp_path / "poll.csv"
    stop_path = tmp_path / "STOP"
    stop_path.write_text("")  # already present -> run() exits after checking, before any poll
    rows_written = poll_health.run(
        "http://example.invalid/api/health", str(out_path), str(stop_path), interval_s=0.0,
    )
    assert rows_written == 0
