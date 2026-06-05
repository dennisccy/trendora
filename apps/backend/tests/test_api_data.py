"""GET/POST /api/data — the Data Manager API surface (iter-3, J-17).

Proves the HTTP contract: coverage + run-history shape; `POST /api/data/jobs` returns a `job_id`
IMMEDIATELY and the async job reaches a final summary; `GET /api/data/jobs/{id}` reports status;
malformed dates / unknown kind are 422 (typed model); an inverted or over-long range is 400; an
unknown job id is 404; no price data is 503.

These tests run against an ISOLATED temp engine (set as the process engine and restored afterward) so
the async job's appended `DataProviderRun` row never pollutes the shared `loaded_engine` (whose
provider-run count other modules assert). The realistic backfill MECHANICS (grows n, lookahead-free,
create-once) are proved in `test_data_manager.py`; here a future-dated range is a deterministic no-op
that exercises the thread + final-summary path without scanning.
"""
from __future__ import annotations

import time
from datetime import date

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlmodel import Session

import app.db as db_module
from app.api.data import JobCreate, data_overview, job_status, start_job
from app.db import create_db_and_tables, make_engine
from app.engine import data_manager
from app.models import DailyPrice


@pytest.fixture()
def data_api_engine(tmp_path):
    """A tiny isolated DB (a few SPY bars so a trading calendar + latest date exist), set as the process
    engine for the duration of the test and restored afterward — so a job's appended DataProviderRun
    row writes here, never to the shared `loaded_engine`."""
    prev = db_module._engine
    engine = make_engine(f"sqlite:///{tmp_path / 'data_api.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for d in (date(2024, 1, 2), date(2024, 1, 3)):
            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()
    db_module.set_engine(engine)
    yield engine
    db_module.set_engine(prev)


def _await_job(job_id: str, timeout_s: float = 10.0) -> dict:
    """Poll the in-memory registry until the job leaves `running` (the no-op job finishes near-instantly)."""
    deadline = time.monotonic() + timeout_s
    snap = data_manager.get_job(job_id)
    while snap is not None and snap["status"] == "running" and time.monotonic() < deadline:
        time.sleep(0.02)
        snap = data_manager.get_job(job_id)
    return snap


def test_get_data_overview_shape(data_api_engine):
    """GET /api/data returns coverage (descriptive metadata) + a run-history list + the import-source
    catalog (J-33). The `sources` list is config-driven with env-detected availability and carries the
    env-var NAME only — never a key value."""
    with Session(data_api_engine) as session:
        payload = data_overview(session=session)
    assert set(payload) == {"coverage", "runs", "sources"}
    cov = payload["coverage"]
    assert cov["symbol_count"] == 1  # only SPY in this tiny DB
    assert cov["trading_day_count"] == 2 and cov["gap_count"] == 2  # two SPY days, no snapshots yet
    assert cov["snapshot_count"] == 0
    assert isinstance(payload["runs"], list)
    # the import-source catalog renders from config (the named sources appear) with availability + env-var name
    sources = payload["sources"]
    by_id = {s["id"]: s for s in sources}
    assert {"yahoo", "tiingo", "stooq"}.issubset(set(by_id))
    assert by_id["yahoo"]["available"] is True and by_id["yahoo"]["needs_key"] is False
    assert by_id["tiingo"]["needs_key"] is True and by_id["tiingo"]["env_var"] == "TIINGO_API_KEY"
    # availability metadata carries only the env-var NAME + a boolean + a reason — never a key value
    for s in sources:
        assert set(s) == {"id", "label", "needs_key", "env_var", "supports_market_cap", "available", "reason"}


def test_post_job_defaults_source_when_omitted(data_api_engine):
    """A job that omits `source` resolves the config `default_source` (J-17 fetch behavior preserved); the
    response echoes it (not secret) and carries NO key. A backfill job needs no network."""
    payload = JobCreate(kind="backfill", start=date(2024, 6, 1), end=date(2024, 6, 5))
    with Session(data_api_engine) as session:
        resp = start_job(payload, session=session)
    assert resp["source"] == "yahoo"  # the config default_source
    assert "api_key" not in resp  # the key is never echoed back


def test_post_job_unknown_source_is_400(data_api_engine):
    """An unknown import source is rejected with 400 — an explicit error, never a silent no-op."""
    with Session(data_api_engine) as session:
        with pytest.raises(HTTPException) as exc:
            start_job(JobCreate(kind="backfill", start=date(2024, 1, 1), end=date(2024, 1, 2), source="bogus"),
                      session=session)
    assert exc.value.status_code == 400


def test_post_fetch_needs_key_source_without_key_is_400(data_api_engine, monkeypatch):
    """A FETCH against a needs-key source with neither an env key nor a pasted key is rejected with an
    explicit 400 (and so no live fetch is even started) — never a silent no-op or a fabricated bar."""
    monkeypatch.delenv("TIINGO_API_KEY", raising=False)
    with Session(data_api_engine) as session:
        with pytest.raises(HTTPException) as exc:
            start_job(JobCreate(kind="fetch", start=date(2024, 1, 1), end=date(2024, 1, 2), source="tiingo"),
                      session=session)
    assert exc.value.status_code == 400
    assert "requires a key" in str(exc.value.detail)


def test_post_job_payload_accepts_source_and_api_key_without_echo(data_api_engine):
    """The typed POST model accepts the J-33 `source` + session-only `api_key`; the start response NEVER
    contains the pasted key. (A backfill job carries the source through with no network call.)"""
    payload = JobCreate(kind="backfill", start=date(2024, 6, 1), end=date(2024, 6, 5),
                        source="yahoo", api_key="sk-PASTE-SESSION-ONLY-xyz")
    with Session(data_api_engine) as session:
        resp = start_job(payload, session=session)
    assert resp["source"] == "yahoo"
    assert "sk-PASTE-SESSION-ONLY-xyz" not in str(resp)
    assert "api_key" not in resp


def test_post_job_returns_job_id_and_reaches_final_summary(data_api_engine):
    """POST returns a job_id immediately (status running); the async job then reaches a final summary,
    and the run appears in the GET /api/data history. A future-dated range is a deterministic no-op."""
    payload = JobCreate(kind="backfill", start=date(2024, 6, 1), end=date(2024, 6, 5))
    with Session(data_api_engine) as session:
        resp = start_job(payload, session=session)
    assert resp["status"] == "running" and resp["kind"] == "backfill"
    job_id = resp["job_id"]
    assert job_id

    final = _await_job(job_id)
    assert final is not None and final["status"] == "ok"  # no in-range trading days -> clean no-op
    assert final["dates_total"] == 0 and final["snapshots_created"] == 0
    assert final["finished_at"] is not None

    # the GET status endpoint serves the same final summary
    assert job_status(job_id)["status"] == "ok"

    # and the run is recorded in the history (append-only DataProviderRun on the isolated engine)
    with Session(data_api_engine) as session:
        runs = data_overview(session=session)["runs"]
    assert any(r["kind"] == "backfill" and r["status"] == "ok" for r in runs)


def test_post_job_503_when_no_price_data(tmp_path):
    """No price data → explicit 503 on POST (the handler is called against an empty DB session)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'empty.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        with pytest.raises(HTTPException) as exc:
            start_job(JobCreate(kind="backfill", start=date(2024, 1, 1), end=date(2024, 1, 2)), session=session)
    assert exc.value.status_code == 503


def test_post_job_inverted_range_is_400(data_api_engine):
    """An inverted range (start > end) is rejected with 400 — an explicit error, never a silent no-op."""
    with Session(data_api_engine) as session:
        with pytest.raises(HTTPException) as exc:
            start_job(JobCreate(kind="backfill", start=date(2024, 1, 10), end=date(2024, 1, 1)), session=session)
    assert exc.value.status_code == 400


def test_post_job_over_long_range_is_400(data_api_engine):
    """A range exceeding config.data_manager.max_range_days is rejected with 400."""
    with Session(data_api_engine) as session:
        with pytest.raises(HTTPException) as exc:
            # default max_range_days is 370; a ~3-year span exceeds it
            start_job(JobCreate(kind="backfill", start=date(2020, 1, 1), end=date(2024, 1, 1)), session=session)
    assert exc.value.status_code == 400


def test_job_payload_rejects_malformed_date_and_unknown_kind():
    """The typed POST model rejects a malformed date and an unknown kind (FastAPI maps these to 422)."""
    with pytest.raises(ValidationError):
        JobCreate(kind="backfill", start="not-a-date", end="2024-01-02")
    with pytest.raises(ValidationError):
        JobCreate(kind="teleport", start=date(2024, 1, 1), end=date(2024, 1, 2))


def test_get_unknown_job_is_404():
    """An unknown job id → 404 (never a fabricated job record)."""
    with pytest.raises(HTTPException) as exc:
        job_status("definitely-not-a-real-job-id")
    assert exc.value.status_code == 404
