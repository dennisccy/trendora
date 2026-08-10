"""GET /api/health via FastAPI TestClient against the loaded temp DB."""
from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import event, func, select as sa_select
from sqlmodel import Session, select

import main
from app.api.health import _distinct_symbol_count
from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import readiness
from app.engine.scanner import get_run_for_date
from app.engine.warmup import _warmup_dates
from app.models import DailyPrice, ScannerRun


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
    # iter-35 (J-21/B-304) added the 4th `drift` component (the live-vs-seed overlap check).
    assert set(preflight["components"]) == {"servability", "freshness", "integrity", "drift"}
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
# ops-hardening iter-24 (J-09) -- the additive `background_compute` field: the historical background-
# dispatch registry's disclosure, composed by compute_readiness and re-served here verbatim.
# ==================================================================================================
def test_health_carries_additive_background_compute_field(loaded_engine, tmp_path, monkeypatch):
    """TC-1 shape check: `background_compute` is ADDITIVE -- every existing key stays present, and the
    new field carries exactly the `{active, recent_outcomes}` shape `get_background_compute_status()`
    produces (never a second/divergent read path)."""
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    with TestClient(main.app) as client:
        body = client.get("/api/health").json()
    existing_keys = {
        "status", "db_ok", "provider", "last_run_date", "seed_latest_date", "symbol_count",
        "readiness", "readiness_detail", "warmup", "poll_interval_seconds", "poll_idle_interval_seconds",
        "preflight",
    }
    assert existing_keys <= set(body)  # every pre-iter-24 key is still present, unchanged
    bg = body["background_compute"]
    assert set(bg) == {"active", "recent_outcomes"}
    assert isinstance(bg["active"], list)
    assert isinstance(bg["recent_outcomes"], list)


def _background_compute_identity(status: dict) -> dict:
    """Reduce a `background_compute` payload to the parts two back-to-back LIVE reads of the SAME
    process-lifetime registry can be compared on without flaking (audit T1 fix): `elapsed_ms` on each
    active entry is computed fresh at READ TIME from its own `started_at`, so it can legitimately grow
    between two reads of a genuinely in-flight window -- it is excluded here. `recent_outcomes` is
    reduced to its ordering/length (the identifying `(asof_key, dataset_version)` sequence), since a
    window completing between the two reads would append a new entry -- a real state change, not a
    flake, but also not what this test is pinning."""
    return {
        "active": [{k: v for k, v in entry.items() if k != "elapsed_ms"} for entry in status["active"]],
        "recent_outcomes_order": [(o["asof_key"], o["dataset_version"]) for o in status["recent_outcomes"]],
        "recent_outcomes_count": len(status["recent_outcomes"]),
    }


def test_health_background_compute_is_single_source(loaded_engine, tmp_path, monkeypatch):
    """The served `background_compute` field matches a DIRECT `compute_readiness` call's own composed
    value for the same session/config -- re-displayed verbatim, never re-derived by the endpoint.
    Compared on identity/shape (active-window keys/count, recent_outcomes ordering/length) excluding the
    read-time-volatile `elapsed_ms` field, rather than raw equality of two live reads (closes audit T1 --
    a false-alarm risk whenever an earlier test in the same whole-file run left a real background
    compute in flight)."""
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    cfg = load_config()
    with TestClient(main.app) as client:
        served = client.get("/api/health").json()["background_compute"]
    with Session(loaded_engine) as session:
        direct = readiness.compute_readiness(session, config=cfg)["background_compute"]
    assert len(served["active"]) == len(direct["active"])
    assert _background_compute_identity(served) == _background_compute_identity(direct)


def test_health_background_compute_serves_failed_outcome_verbatim(loaded_engine, tmp_path, monkeypatch):
    """goal-ops-hardening iter-26 (J-09 confirm-gap 2): a crafted `failed` outcome -- the branch every
    captured panel state to date has never exercised -- is composed and served VERBATIM, field-for-field,
    never dropped/re-derived/silently swallowed. Monkeypatches the ONE producer accessor
    (`app.engine.forward_testing.get_background_compute_status`) rather than a byte-frozen module's
    internals -- `compute_readiness`/`app/api/health.py` themselves are untouched by this iteration."""
    import app.engine.forward_testing as forward_testing_module

    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    crafted = {
        "active": [],
        "recent_outcomes": [{
            "asof_key": "2026-01-04",
            "dataset_version": "r1-f2",
            "outcome": "failed",
            "started_at": "2026-01-04T00:00:00+00:00",
            "finished_at": "2026-01-04T00:00:05+00:00",
            "duration_ms": 5000,
            "reason": "forced test failure — simulated dispatch error",
        }],
    }
    monkeypatch.setattr(forward_testing_module, "get_background_compute_status", lambda: crafted)
    with TestClient(main.app) as client:
        body = client.get("/api/health").json()
    served = body["background_compute"]["recent_outcomes"][0]
    assert served == crafted["recent_outcomes"][0]
    assert served["outcome"] == "failed"
    assert served["reason"] == "forced test failure — simulated dispatch error"


def test_health_background_compute_degrades_honestly_when_readiness_fails(loaded_engine, monkeypatch):
    """A total `compute_readiness` failure degrades the WHOLE readiness payload to `unavailable` (the
    pre-existing convention) -- `background_compute` still serves the honest empty shape, never omitted
    and never left dangling on a partially-constructed fallback dict."""
    import app.api.health as health_module

    def _boom(session, engine=None, config=None):
        raise RuntimeError("simulated readiness failure")

    monkeypatch.setattr(health_module, "compute_readiness", _boom)
    with TestClient(main.app) as client:
        body = client.get("/api/health").json()
    assert body["readiness"] == "unavailable"
    assert body["background_compute"] == {"active": [], "recent_outcomes": []}


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


# ==================================================================================================
# ops-hardening iter-57 (TC-5) -- `_distinct_symbol_count`'s fast indexed-walk replaces the per-request
# `COUNT(DISTINCT symbol)` covering-index scan (0.117-0.119s live on the grown dev DB, the confirmed
# majority of GET /api/health's steady-state latency against the committed <=0.1s budget). Fast,
# hand-built fixtures -- NOT `loaded_engine` -- so these run in milliseconds, mirroring `coverage_engine`
# in test_data_manager.py rather than the slow 30-year-seed session fixture.
# ==================================================================================================
def test_distinct_symbol_count_byte_identical_to_naive_count_distinct(tmp_path):
    """TC-5 byte-identity: the fast indexed-walk query returns the SAME value as a plain
    `SELECT COUNT(DISTINCT symbol)` for the same DB state -- multiple symbols, multiple dates per
    symbol, and one symbol repeated across every date (proving it counts distinct SYMBOLS, not rows)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'symcount.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for sym in ("SPY", "AAA", "BBB"):
            for d in (date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)):
                session.add(DailyPrice(symbol=sym, date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    with Session(engine) as session:
        fast = _distinct_symbol_count(session)
        naive = int(session.execute(sa_select(func.count(func.distinct(DailyPrice.symbol)))).scalar_one() or 0)
    assert fast == naive == 3


def test_distinct_symbol_count_empty_db_is_zero(tmp_path):
    """An empty / bars-less DB reports 0 -- never an error, never a fabricated count."""
    engine = make_engine(f"sqlite:///{tmp_path / 'symcount_empty.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        assert _distinct_symbol_count(session) == 0


def test_distinct_symbol_count_single_symbol(tmp_path):
    """A DB with exactly one symbol across several dates counts 1, not the row count (4)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'symcount_one.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for d in (date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4), date(2024, 1, 5)):
            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()
    with Session(engine) as session:
        assert _distinct_symbol_count(session) == 1


def test_health_symbol_count_matches_naive_count_distinct_on_loaded_engine(loaded_engine):
    """TC-5 byte-identity on the realistic seeded fixture: `GET /api/health`'s `symbol_count` (now served
    by `_distinct_symbol_count`) equals a plain `COUNT(DISTINCT symbol)` for the SAME DB state -- proving
    the query-shape change introduced no value drift on real data, not just the small hand-built cases
    above."""
    with Session(loaded_engine) as session:
        naive = int(session.execute(sa_select(func.count(func.distinct(DailyPrice.symbol)))).scalar_one() or 0)
    with TestClient(main.app) as client:
        body = client.get("/api/health").json()
    assert body["symbol_count"] == naive
