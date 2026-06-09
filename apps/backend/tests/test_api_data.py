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

import json
import time
from datetime import date, datetime

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlmodel import Session

import app.db as db_module
from app.api.data import JobCreate, ResumeRequest, data_overview, job_status, resume_job, start_job
from app.config import get_config
from app.db import create_db_and_tables, make_engine
from app.engine import data_manager
from app.models import DailyPrice, DataProviderRun, ImportCheckpoint


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
    assert set(payload) == {"coverage", "runs", "sources", "resumable_imports", "unfinished_imports"}
    assert payload["resumable_imports"] == []  # J-34: no paused imports on a fresh DB
    assert payload["unfinished_imports"] == []  # J-38: nothing unfinished on a fresh DB
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


def test_seed_import_source_surfaces_under_flag_via_api(data_api_engine, monkeypatch):
    """iter-26: with the env flag set, the offline `seed` source appears in GET /api/data `sources`
    (no-key, market-cap-capable, available) so the browser harness can drive an offline pull/expand;
    without the flag it is ABSENT. It carries the same metadata shape as every other source — no key."""
    # absent by default
    monkeypatch.delenv(data_manager.SEED_IMPORT_ENV_FLAG, raising=False)
    with Session(data_api_engine) as session:
        off = data_overview(session=session)
    assert "seed" not in {s["id"] for s in off["sources"]}
    # present under the flag
    monkeypatch.setenv(data_manager.SEED_IMPORT_ENV_FLAG, "1")
    with Session(data_api_engine) as session:
        on = data_overview(session=session)
    by_id = {s["id"]: s for s in on["sources"]}
    assert "seed" in by_id
    seed = by_id["seed"]
    assert seed["needs_key"] is False and seed["available"] is True
    assert seed["supports_market_cap"] is True and seed["env_var"] is None
    # same metadata contract as every other source (no extra/secret field)
    assert set(seed) == {"id", "label", "needs_key", "env_var", "supports_market_cap", "available", "reason"}


def test_post_seed_source_job_dispatches_without_key(data_api_engine, monkeypatch):
    """A `seed`-source fetch POSTed to /api/data/jobs is ACCEPTED under the flag (no key needed) and runs
    through the EXISTING job path to a final summary — echoing the source (not secret) and no key. Without
    the flag the same request is rejected 400 (the seed source is a test/dev affordance only)."""
    # rejected without the flag
    monkeypatch.delenv(data_manager.SEED_IMPORT_ENV_FLAG, raising=False)
    with Session(data_api_engine) as session:
        with pytest.raises(HTTPException) as exc:
            start_job(JobCreate(kind="fetch", start=date(2024, 6, 1), end=date(2024, 6, 2), source="seed"),
                      session=session)
    assert exc.value.status_code == 400
    # accepted under the flag, runs to a final summary (a future-dated window is a deterministic no-op)
    monkeypatch.setenv(data_manager.SEED_IMPORT_ENV_FLAG, "1")
    with Session(data_api_engine) as session:
        resp = start_job(JobCreate(kind="fetch", start=date(2099, 1, 1), end=date(2099, 1, 2), source="seed"),
                         session=session)
    assert resp["source"] == "seed"
    assert "api_key" not in resp
    snap = _await_job(resp["job_id"])
    assert snap is not None and snap["status"] in {"ok", "partial", "failed"}
    assert snap["source"] == "seed"  # the chosen source is recorded; no key field present


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


# --- iter-22 (J-34): resume endpoint 404/409/400 + resumable_imports carries no key ----------
def _add_checkpoint(session, *, import_id, source, status):
    """Insert a durable import checkpoint (job-control state — no key column) for the resume tests."""
    session.add(ImportCheckpoint(
        import_id=import_id, source=source, kind="fetch", start=date(2024, 1, 1), end=date(2024, 1, 2),
        symbol_plan_json=json.dumps(["AAA", "BBB"]), chunk_total=2, next_chunk_index=1, symbols_ok=1,
        status=status, created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1),
    ))
    session.commit()


def test_resume_unknown_import_is_404(data_api_engine):
    """Resuming an unknown import → explicit 404 (never a fabricated job)."""
    with Session(data_api_engine) as session:
        with pytest.raises(HTTPException) as exc:
            resume_job("not-an-import", payload=ResumeRequest(), session=session)
    assert exc.value.status_code == 404


def test_resume_completed_import_is_409(data_api_engine):
    """Resuming a non-resumable (already `ok`) import → explicit 409."""
    with Session(data_api_engine) as session:
        _add_checkpoint(session, import_id="done-import", source="yahoo", status="ok")
        with pytest.raises(HTTPException) as exc:
            resume_job("done-import", payload=ResumeRequest(), session=session)
    assert exc.value.status_code == 409


def test_resume_needs_key_source_without_key_is_400(data_api_engine, monkeypatch):
    """Resuming a needs-key source with neither an env key nor a re-supplied session key → explicit 400
    (the checkpoint stores no key, so a restart-then-resume of a key source must re-supply it)."""
    monkeypatch.delenv("TIINGO_API_KEY", raising=False)
    with Session(data_api_engine) as session:
        _add_checkpoint(session, import_id="paused-tiingo", source="tiingo", status="resumable")
        with pytest.raises(HTTPException) as exc:
            resume_job("paused-tiingo", payload=ResumeRequest(), session=session)
    assert exc.value.status_code == 400
    assert "requires a key" in str(exc.value.detail)


def test_resumable_imports_in_overview_carries_no_key(data_api_engine):
    """A `resumable` checkpoint surfaces in GET /api/data `resumable_imports` (newest first) with chunk
    progress + symbols done/remaining — and NEVER any key field/value (anti-goal: keys never persisted)."""
    secret = "sk-NEVER-IN-RESUMABLE-LIST-abc"
    with Session(data_api_engine) as session:
        _add_checkpoint(session, import_id="paused-1", source="tiingo", status="resumable")
        payload = data_overview(session=session)
    listed = payload["resumable_imports"]
    assert len(listed) == 1 and listed[0]["import_id"] == "paused-1"
    assert listed[0]["chunk_index"] == 1 and listed[0]["chunk_total"] == 2
    assert listed[0]["symbols_remaining"] == 1  # 2 total - 1 ok - 0 failed
    # no key field anywhere on the row, and the sentinel never appears
    assert "api_key" not in listed[0] and "key" not in listed[0]
    assert secret not in json.dumps(payload)


# --- iter-23 (J-35): the `expand` job kind via the API surface ----------------------------------
def test_job_payload_accepts_expand_kind():
    """The typed POST model accepts `kind="expand"` (J-35) and still rejects an unknown kind (422)."""
    payload = JobCreate(kind="expand", start=date(2024, 3, 1), end=date(2024, 3, 1), source="yahoo")
    assert payload.kind == "expand"
    with pytest.raises(ValidationError):
        JobCreate(kind="enlarge", start=date(2024, 3, 1), end=date(2024, 3, 1))


def test_post_expand_over_ineligible_source_is_400(data_api_engine):
    """An expand over a `supports_market_cap: false` source (alpha_vantage / stooq) is rejected with an
    explicit 400 at the API layer — never a silent no-op, never a fabricated cap."""
    for ineligible in ("alpha_vantage", "stooq"):
        with Session(data_api_engine) as session:
            with pytest.raises(HTTPException) as exc:
                start_job(
                    JobCreate(kind="expand", start=date(2024, 3, 1), end=date(2024, 3, 1), source=ineligible),
                    session=session,
                )
        assert exc.value.status_code == 400
        assert "market cap" in str(exc.value.detail)


def test_post_expand_needs_key_source_without_key_is_400(data_api_engine, monkeypatch):
    """An expand over a needs-key, market-cap-capable source (tiingo) with no env/pasted key → explicit
    400 (the J-33 key gate is reused for expand — never a silent expand)."""
    monkeypatch.delenv("TIINGO_API_KEY", raising=False)
    with Session(data_api_engine) as session:
        with pytest.raises(HTTPException) as exc:
            start_job(
                JobCreate(kind="expand", start=date(2024, 3, 1), end=date(2024, 3, 1), source="tiingo"),
                session=session,
            )
    assert exc.value.status_code == 400
    assert "requires a key" in str(exc.value.detail)


def test_get_data_overview_sources_expose_market_cap_capability(data_api_engine):
    """The import-source catalog exposes each source's `supports_market_cap` flag (the UI gates the expand
    option on it): yahoo/tiingo/finnhub true, alpha_vantage/stooq false — config-driven, no hardcoded list."""
    with Session(data_api_engine) as session:
        sources = data_overview(session=session)["sources"]
    by_id = {s["id"]: s for s in sources}
    assert by_id["yahoo"]["supports_market_cap"] is True
    assert by_id["tiingo"]["supports_market_cap"] is True
    assert by_id["finnhub"]["supports_market_cap"] is True
    assert by_id["alpha_vantage"]["supports_market_cap"] is False
    assert by_id["stooq"]["supports_market_cap"] is False


def test_expand_job_status_shape_has_passers_and_omitted():
    """The job-status payload (GET /api/data/jobs/{id}) carries the J-35 expand screen fields — `passers`,
    `omitted_total`, and a bounded `omitted` [{symbol, reason}] list — so the UI can render the screen
    result. Built directly from a JobProgress (the in-memory record the endpoint serializes)."""
    prog = data_manager.JobProgress(
        job_id="exp-1", kind="expand", start=date(2024, 3, 1), end=date(2024, 3, 1), source="yahoo"
    )
    prog.passers = 3
    data_manager._record_omitted(prog, "CHEAP", "price 4.0 < 10")
    data_manager._record_omitted(prog, "NOCAP", "no_market_cap")
    snap = prog.to_dict()
    assert snap["kind"] == "expand" and snap["passers"] == 3
    assert snap["omitted_total"] == 2
    assert snap["omitted"] == [
        {"symbol": "CHEAP", "reason": "price 4.0 < 10"},
        {"symbol": "NOCAP", "reason": "no_market_cap"},
    ]


# ==================================================================================================
# J-39 — Remove-data API: POST /api/data/remove/preview (read-only) + POST /api/data/remove (destructive)
# ==================================================================================================
@pytest.fixture()
def removal_api_engine(tmp_path):
    """An isolated DB + a committed-seed manifest where SPY is wholly seed (2024-01-02..03) and AAA has a
    user-added bar beyond its seed window (2024-01-02 seed; 2024-01-09 user-added). Set as the process
    engine and restored afterward so the audit row writes here. The endpoints read the manifest from
    `data_manager.DEFAULT_SEED_DIR`, which we monkeypatch to a temp seed dir holding our meta.json."""
    import json as _json
    from app.engine import data_manager as dm
    from app.models import ScannerRun

    prev = db_module._engine
    seed_dir = tmp_path / "seed"
    seed_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "symbols_ok": 2, "symbols_failed": 0,
        "symbols": [
            {"symbol": "SPY", "first": "2024-01-02", "last": "2024-01-03", "bars": 2},
            {"symbol": "AAA", "first": "2024-01-02", "last": "2024-01-02", "bars": 1},
        ],
    }
    (seed_dir / "meta.json").write_text(_json.dumps(meta) + "\n")

    engine = make_engine(f"sqlite:///{tmp_path / 'remove_api.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for d in (date(2024, 1, 2), date(2024, 1, 3)):
            session.add(DailyPrice(symbol="SPY", date=d, open=1, high=1, low=1, close=1, volume=1))
        session.add(DailyPrice(symbol="AAA", date=date(2024, 1, 2), open=1, high=1, low=1, close=1, volume=1))
        # AAA user-added bar beyond its seed window (2024-01-02) → removable
        session.add(DailyPrice(symbol="AAA", date=date(2024, 1, 9), open=1, high=1, low=1, close=1, volume=1))
        # a snapshot on the user-added date → cascaded when that bar is removed
        session.add(ScannerRun(
            asof_date=date(2024, 1, 9), created_at=datetime(2024, 1, 9), provider="seed", benchmark="SPY",
            regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        ))
        session.commit()
    db_module.set_engine(engine)
    yield engine, seed_dir, prev
    db_module.set_engine(prev)


def test_remove_preview_endpoint_shape_deletes_nothing(removal_api_engine, monkeypatch):
    """POST /api/data/remove/preview returns the plan (removable bars + range, not-removable committed-seed
    breakdown, cascade) and DELETES NOTHING."""
    from app.api.data import RemoveScope, remove_preview
    from app.engine import data_manager as dm
    from app.models import ScannerRun
    engine, seed_dir, _prev = removal_api_engine
    monkeypatch.setattr(dm, "DEFAULT_SEED_DIR", seed_dir)

    with Session(engine) as session:
        runs_before = len(session.exec(__import__("sqlmodel").select(ScannerRun)).all())
        resp = remove_preview(
            RemoveScope(symbols=["AAA"], start=date(2024, 1, 5), end=date(2024, 1, 10)), session=session
        )
        runs_after = len(session.exec(__import__("sqlmodel").select(ScannerRun)).all())
    assert runs_before == runs_after  # preview deleted nothing
    assert resp["removable_bar_count"] == 1  # AAA on 2024-01-09
    assert resp["removable_first"] == "2024-01-09"
    assert resp["cascade"]["snapshot_count"] == 1  # the 2024-01-09 snapshot
    assert resp["refused"] is False
    assert "removable_bars" not in resp  # internal objects never serialized


def test_remove_endpoint_executes_and_audits(removal_api_engine, monkeypatch):
    """POST /api/data/remove deletes the user-added bar + cascades, and the next coverage read reflects the
    smaller dataset (the snapshot date is gone)."""
    from app.api.data import RemoveScope, remove_data_endpoint, data_overview
    from app.engine import data_manager as dm
    engine, seed_dir, _prev = removal_api_engine
    monkeypatch.setattr(dm, "DEFAULT_SEED_DIR", seed_dir)

    with Session(engine) as session:
        resp = remove_data_endpoint(
            RemoveScope(symbols=["AAA"], start=date(2024, 1, 5), end=date(2024, 1, 10)), session=session
        )
    assert resp["removed_bar_count"] == 1
    assert resp["cascade"]["snapshot_count"] == 1
    # coverage now reflects the smaller dataset: the 2024-01-09 snapshot date is gone.
    with Session(engine) as session:
        cov = data_overview(session=session)["coverage"]
    assert "2024-01-09" not in cov["snapshot_dates"]
    assert cov["snapshot_count"] == 0


def test_remove_endpoint_seed_only_is_400(removal_api_engine, monkeypatch):
    """A wholly-committed-seed scope (SPY is entirely seed) is refused with 400 — the committed seed is
    never deletable; never a silent partial."""
    from app.api.data import RemoveScope, remove_data_endpoint
    from app.engine import data_manager as dm
    engine, seed_dir, _prev = removal_api_engine
    monkeypatch.setattr(dm, "DEFAULT_SEED_DIR", seed_dir)
    with Session(engine) as session:
        with pytest.raises(HTTPException) as exc:
            remove_data_endpoint(
                RemoveScope(symbols=["SPY"], start=date(2024, 1, 1), end=date(2024, 1, 3)), session=session
            )
    assert exc.value.status_code == 400
    assert "committed seed" in str(exc.value.detail).lower()


def test_remove_preview_seed_only_returns_refused(removal_api_engine, monkeypatch):
    """The PREVIEW of a seed-only scope returns refused=True with a reason (a 200 the UI renders to disable
    the destructive confirm) — distinct from the destructive endpoint's 400."""
    from app.api.data import RemoveScope, remove_preview
    from app.engine import data_manager as dm
    engine, seed_dir, _prev = removal_api_engine
    monkeypatch.setattr(dm, "DEFAULT_SEED_DIR", seed_dir)
    with Session(engine) as session:
        resp = remove_preview(
            RemoveScope(symbols=["SPY"], start=date(2024, 1, 1), end=date(2024, 1, 3)), session=session
        )
    assert resp["refused"] is True and resp["removable_bar_count"] == 0
    assert "committed seed" in resp["reason"].lower()
    assert resp["not_removable_bar_count"] == 2  # SPY × 2 seed days


def test_remove_endpoint_empty_scope_is_400(removal_api_engine, monkeypatch):
    """An empty scope (no symbols, no range) is rejected with 400 — never an accidental wipe."""
    from app.api.data import RemoveScope, remove_data_endpoint
    from app.engine import data_manager as dm
    engine, seed_dir, _prev = removal_api_engine
    monkeypatch.setattr(dm, "DEFAULT_SEED_DIR", seed_dir)
    with Session(engine) as session:
        with pytest.raises(HTTPException) as exc:
            remove_data_endpoint(RemoveScope(), session=session)
    assert exc.value.status_code == 400


def test_remove_endpoint_unknown_symbol_is_400(removal_api_engine, monkeypatch):
    """An unknown symbol (no stored bars) is rejected with 400 — never a silent no-op or fabricated row."""
    from app.api.data import RemoveScope, remove_data_endpoint
    from app.engine import data_manager as dm
    engine, seed_dir, _prev = removal_api_engine
    monkeypatch.setattr(dm, "DEFAULT_SEED_DIR", seed_dir)
    with Session(engine) as session:
        with pytest.raises(HTTPException) as exc:
            remove_data_endpoint(
                RemoveScope(symbols=["NOPE"], start=date(2024, 1, 1), end=date(2024, 1, 10)), session=session
            )
    assert exc.value.status_code == 400


def test_remove_preview_inverted_range_is_400(removal_api_engine, monkeypatch):
    """An inverted date range (start > end) is rejected with 400."""
    from app.api.data import RemoveScope, remove_preview
    from app.engine import data_manager as dm
    engine, seed_dir, _prev = removal_api_engine
    monkeypatch.setattr(dm, "DEFAULT_SEED_DIR", seed_dir)
    with Session(engine) as session:
        with pytest.raises(HTTPException) as exc:
            remove_preview(
                RemoveScope(symbols=["AAA"], start=date(2024, 1, 10), end=date(2024, 1, 1)), session=session
            )
    assert exc.value.status_code == 400


def test_remove_endpoint_error_carries_no_secret(removal_api_engine, monkeypatch):
    """J-33 carry: the remove/preview error strings carry no key/secret. These paths take no provider key,
    so the surface is small — assert no `?token=`/`?apikey=` could appear in an error detail."""
    from app.api.data import RemoveScope, remove_data_endpoint
    from app.engine import data_manager as dm
    engine, seed_dir, _prev = removal_api_engine
    monkeypatch.setattr(dm, "DEFAULT_SEED_DIR", seed_dir)
    with Session(engine) as session:
        with pytest.raises(HTTPException) as exc:
            remove_data_endpoint(
                RemoveScope(symbols=["SPY"], start=date(2024, 1, 1), end=date(2024, 1, 3)), session=session
            )
    detail = str(exc.value.detail)
    assert "?token=" not in detail and "?apikey=" not in detail and "api_key" not in detail


# --- iter-25 (J-37 pull / J-38 retry+dismiss) API surface ----------------------------------------
def test_post_job_accepts_symbols_for_pull(data_api_engine):
    """POST /api/data/jobs accepts a J-37 pull body: a fetch carrying the diagnosed-gap `symbols`. The
    response echoes the normalized symbols (the gap-exact scope), and carries no key."""
    payload = JobCreate(kind="fetch", start=date(2024, 1, 2), end=date(2024, 1, 3), symbols=["DDD", "", "  "])
    with Session(data_api_engine) as session:
        resp = start_job(payload, session=session)
    job_id = resp["job_id"]
    assert resp["symbols"] == ["DDD"]  # whitespace/empty normalized away
    assert "api_key" not in resp
    _await_job(job_id)  # let the (offline) job finish so the thread is clean


def test_get_data_overview_has_unfinished_imports(data_api_engine):
    """GET /api/data now also carries the unified `unfinished_imports` list (J-38)."""
    with Session(data_api_engine) as session:
        _add_checkpoint(session, import_id="paused-x", source="tiingo", status="resumable")
        payload = data_overview(session=session)
    assert "unfinished_imports" in payload
    ids = {(r["record_type"], r["id"]) for r in payload["unfinished_imports"]}
    assert ("checkpoint", "paused-x") in ids


def test_retry_unknown_run_is_404(data_api_engine):
    """Retrying an unknown run id → explicit 404 (never a fabricated job)."""
    from app.api.data import retry_job
    with Session(data_api_engine) as session:
        with pytest.raises(HTTPException) as exc:
            retry_job(99999, payload=ResumeRequest(), session=session)
    assert exc.value.status_code == 404


def test_retry_clean_run_is_409(data_api_engine):
    """Retrying a clean (ok) run → explicit 409 (only partial/failed runs are retryable)."""
    from app.api.data import retry_job
    with Session(data_api_engine) as session:
        run = DataProviderRun(
            provider="yahoo", started_at=datetime(2024, 1, 3), finished_at=datetime(2024, 1, 3),
            symbols_ok=5, symbols_failed=0, status="ok",
            message=json.dumps({"kind": "fetch", "start": "2024-01-02", "end": "2024-01-03", "summary": "ok"}),
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        with pytest.raises(HTTPException) as exc:
            retry_job(run.id, payload=ResumeRequest(), session=session)
    assert exc.value.status_code == 409


def test_retry_needs_key_source_without_key_is_400(data_api_engine, monkeypatch):
    """Retrying a partial run whose source needs a key, with no env/session key → explicit 400."""
    from app.api.data import retry_job
    monkeypatch.delenv("TIINGO_API_KEY", raising=False)
    with Session(data_api_engine) as session:
        run = DataProviderRun(
            provider="tiingo", started_at=datetime(2024, 1, 3), finished_at=datetime(2024, 1, 3),
            symbols_ok=1, symbols_failed=1, status="partial",
            message=json.dumps({"kind": "fetch", "start": "2024-01-02", "end": "2024-01-03", "summary": "partial"}),
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        with pytest.raises(HTTPException) as exc:
            retry_job(run.id, payload=ResumeRequest(), session=session)
    assert exc.value.status_code == 400
    assert "requires a key" in str(exc.value.detail)


def test_dismiss_run_endpoint_soft_dismisses(data_api_engine):
    """POST /api/data/jobs/{id}/dismiss (record_type=run) soft-dismisses; the run leaves unfinished_imports
    but stays in Run history."""
    from app.api.data import dismiss_job
    with Session(data_api_engine) as session:
        run = DataProviderRun(
            provider="yahoo", started_at=datetime(2024, 1, 3), finished_at=datetime(2024, 1, 3),
            symbols_ok=1, symbols_failed=1, status="partial",
            message=json.dumps({"kind": "fetch", "start": "2024-01-02", "end": "2024-01-03", "summary": "partial"}),
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        resp = dismiss_job(str(run.id), record_type="run", session=session)
        assert resp["dismissed"] is True
        payload = data_overview(session=session)
    run_ids = {r["id"] for r in payload["unfinished_imports"] if r["record_type"] == "run"}
    assert run.id not in run_ids  # left the actionable list
    assert any(r["id"] == run.id for r in payload["runs"])  # still in Run history audit


def test_dismiss_unknown_is_404(data_api_engine):
    from app.api.data import dismiss_job
    with Session(data_api_engine) as session:
        with pytest.raises(HTTPException) as exc:
            dismiss_job("88888", record_type="run", session=session)
    assert exc.value.status_code == 404


def test_pull_key_leak_scrubbed_through_job_status_surface(data_api_engine, monkeypatch):
    """CRITICAL key-leak regression (J-33 carry on the J-37 pull): a pull whose provider raises a REAL
    httpx error EMBEDDING the session key in the URL must have the key SCRUBBED from the job-status surface
    (`GET /api/data/jobs/{id}`), the checkpoint, and run history — driven through the API's own job path."""
    secret = "sk-PULL-LEAK-25-9f3a"
    # a REAL httpx.HTTPStatusError str carrying the key as ?token= (the exact iter-21 leak vector)
    req = __import__("httpx").Request(
        "GET", "https://api.tiingo.com/tiingo/daily/DDD/prices", params={"token": secret}
    )
    try:
        __import__("httpx").Response(429, request=req).raise_for_status()
    except Exception as e:  # noqa: BLE001
        leak = str(e)
    assert secret in leak  # sanity: there IS a key to scrub

    from app.data_providers.base import PriceProvider, ProviderUnavailableError

    class _Leak(PriceProvider):
        def get_daily(self, symbol, start=None, end=None):
            raise ProviderUnavailableError(leak)

    # dispatch a gap-exact pull (symbols=["DDD"]) through the engine with the injected leaking provider
    cfg = get_config()
    job = data_manager.create_job("fetch", date(2024, 1, 2), date(2024, 1, 3), source="tiingo")
    data_manager.run_data_job(
        job.job_id, config=cfg, engine=data_api_engine, provider=_Leak(),
        api_key=secret, sleep_fn=lambda _s: None, symbols=["DDD"],
    )
    status = job_status(job.job_id)  # the GET /api/data/jobs/{id} surface
    assert status["status"] == "failed"
    assert secret not in json.dumps(status)  # absent from the job-status surface
    assert "***" in json.dumps(status["errors"])  # the scrub fired
    with Session(data_api_engine) as session:
        overview = data_overview(session=session)
    assert secret not in json.dumps(overview)  # absent from unfinished_imports + run history
