"""GET /api/health via FastAPI TestClient against the loaded temp DB."""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlmodel import Session, select

import main
from app.config import load_config
from app.engine import readiness
from app.engine.scanner import get_run_for_date
from app.engine.warmup import _warmup_dates
from app.models import ScannerRun


def test_health_returns_ok_shape(loaded_engine):
    # loaded_engine registers the temp DB as the process engine (see conftest).
    with TestClient(main.app) as client:
        resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["db_ok"] is True
    assert body["provider"] == "seed"
    assert body["last_run_date"] is None
    assert body["seed_latest_date"] is not None
    assert body["symbol_count"] > 100


def test_health_carries_readiness_and_warmup(loaded_engine):
    """iter-28 (J-40): the single canonical readiness endpoint extends /api/health with the honest
    readiness state + warm-up progress. The TestClient runs the lifespan (fast latest-snapshot + the
    background warm-up), so by the time we read /api/health the latest snapshot is servable -> the state
    is one of the three honest labels and the warm-up progress is a real {done, total} (never fabricated)."""
    with TestClient(main.app) as client:
        body = client.get("/api/health").json()
    assert body["readiness"] in {"ready", "initializing", "unavailable"}
    # the latest snapshot is produced synchronously before serving, so it is never 'unavailable' here.
    assert body["readiness"] != "unavailable"
    warmup = body["warmup"]
    assert set(warmup) == {"done", "total", "status", "message"}
    assert isinstance(warmup["done"], int) and warmup["done"] >= 0
    assert isinstance(warmup["total"], int) and warmup["total"] >= 0
    assert warmup["done"] <= warmup["total"]
    assert warmup["message"] == f"history {warmup['done']}/{warmup['total']}"
    # the config-derived poll cadences the frontend badge reads (no client-side poll literal)
    assert body["poll_interval_seconds"] > 0
    assert body["poll_idle_interval_seconds"] >= body["poll_interval_seconds"]


# ==================================================================================================
# iter-33 (J-20 / backlog B-301) -- the additive daily preflight verdict on the SAME /api/health payload
# ==================================================================================================
def test_health_carries_additive_preflight_field(loaded_engine, tmp_path, monkeypatch):
    """The `preflight` field is ADDITIVE: every EXISTING key stays present (the J-40 contract is
    untouched) and the new field carries the exact GO/DEGRADED/NO-GO shape -- never a second endpoint."""
    # Redirect the verdict-history append so this test never writes the REAL session's history log.
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    with TestClient(main.app) as client:
        body = client.get("/api/health").json()
    existing_keys = {
        "status", "db_ok", "provider", "last_run_date", "seed_latest_date", "symbol_count",
        "readiness", "warmup", "poll_interval_seconds", "poll_idle_interval_seconds",
    }
    assert existing_keys <= set(body)  # every pre-iter-33 key is still present, unchanged
    preflight = body["preflight"]
    assert set(preflight) == {"verdict", "reasons", "components", "as_of", "reference"}
    assert preflight["verdict"] in {"GO", "DEGRADED", "NO-GO"}
    assert isinstance(preflight["reasons"], list)
    assert preflight["as_of"] == preflight["reference"]  # same value under both spec-named keys
    assert set(preflight["components"]) == {"servability", "freshness", "integrity"}
    for component in preflight["components"].values():
        assert set(component) == {"ok", "severity", "detail"}
        assert component["severity"] in {"degraded", "no-go"}


def test_health_preflight_is_single_source(loaded_engine, tmp_path, monkeypatch):
    """The served `preflight` field equals a DIRECT `compute_preflight` call for the same session/config
    -- the endpoint re-displays the ONE composer's output verbatim, never a second/divergent computation."""
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    cfg = load_config()
    with TestClient(main.app) as client:
        served = client.get("/api/health").json()["preflight"]
    with Session(loaded_engine) as session:
        direct = readiness.compute_preflight(session, config=cfg)
    assert served == direct


# ==================================================================================================
# iter-24 fast-platform item G — cheap readiness probe (memoized cadence dates + one grouped query)
# ==================================================================================================
def test_readiness_memoizes_cadence_dates_across_repeated_calls(loaded_engine, monkeypatch):
    """compute_readiness does NOT re-derive the cadence-date set on a second call with the SAME
    (latest_date, cfg) -- the expensive `_warmup_dates` derivation (an ORM SPY-bars read) runs at most
    once; the memo hit returns the byte-identical result."""
    readiness.reset_readiness_cache()
    cfg = load_config()
    calls: list[int] = []
    real_warmup_dates = readiness._warmup_dates

    def _counting(session, cfg_arg):
        calls.append(1)
        return real_warmup_dates(session, cfg_arg)

    monkeypatch.setattr(readiness, "_warmup_dates", _counting)
    with Session(loaded_engine) as session:
        first = readiness.compute_readiness(session, config=cfg)
        second = readiness.compute_readiness(session, config=cfg)
    assert len(calls) == 1  # the second call hit the memo -- no re-derivation
    assert first == second


def test_readiness_recomputes_when_config_object_differs(loaded_engine):
    """A DIFFERENT config object (e.g. a distinct test fixture, or a config reload) never serves
    another config's memoized cadence dates -- the memo key includes `id(cfg)`."""
    readiness.reset_readiness_cache()
    cfg_a = load_config()
    cfg_b = cfg_a.model_copy(deep=True)  # same content, a DIFFERENT object identity
    assert cfg_a is not cfg_b
    with Session(loaded_engine) as session:
        result_a = readiness.compute_readiness(session, config=cfg_a)
        result_b = readiness.compute_readiness(session, config=cfg_b)
    # same content -> same figures (proves correctness), even though the memo missed on the second call
    assert result_a == result_b


def test_readiness_issues_two_scanner_runs_queries_not_one_per_cadence_date(loaded_engine):
    """The former per-date `get_run_for_date` existence loop (one SELECT per cadence date -- dozens on
    the deep basis) is replaced by ONE grouped query. Only two SELECTs ever touch `scanner_runs` in a
    single `compute_readiness` call: the latest-run-date check, and the ONE grouped existence query."""
    readiness.reset_readiness_cache()
    cfg = load_config()
    queries: list[str] = []

    def _count(conn, cursor, statement, parameters, context, executemany):
        lowered = statement.lower()
        if "scanner_runs" in lowered and lowered.strip().startswith("select"):
            queries.append(statement)

    event.listen(loaded_engine, "before_cursor_execute", _count)
    try:
        with Session(loaded_engine) as session:
            readiness.compute_readiness(session, config=cfg)
    finally:
        event.remove(loaded_engine, "before_cursor_execute", _count)
    assert len(queries) == 2


def test_readiness_grouped_existence_query_matches_per_date_check(loaded_engine):
    """The ONE grouped `asof_date IN (...)` existence query returns exactly the same persisted-date set
    as the former per-date `get_run_for_date` check -- proving the item-G change is a pure performance
    refactor (byte-identical `done` count), never a value change."""
    cfg = load_config()
    with Session(loaded_engine) as session:
        cadence_dates = _warmup_dates(session, cfg)
        assert cadence_dates, "the warm fixture's cadence must be non-empty for this check to be meaningful"
        manual_persisted = {d for d in cadence_dates if get_run_for_date(session, d) is not None}
        grouped_persisted = set(
            session.exec(select(ScannerRun.asof_date).where(ScannerRun.asof_date.in_(cadence_dates))).all()
        )
    assert grouped_persisted == manual_persisted
