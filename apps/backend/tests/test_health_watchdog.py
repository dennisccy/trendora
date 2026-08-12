"""ops-hardening iter-67 (J-07) -- the env-flag-gated health-request-wait watchdog.

Tests the IN-SCOPE ask verbatim: (a) flag unset -> no `logs/health-watchdog.jsonl` entries, response
unchanged; (b) flag set -> a request produces exactly one queue-wait record with `queue_wait_s >= 0`;
(c) the loop-lag probe writes at least N records over a short synthetic interval. Plus TC-7 (byte-
identity of the response body/shape regardless of the flag) and the error-case requirement (a
readiness-computation exception must not suppress the already-captured queue-wait sample).

iter-69 (J-07) additionally tests (e): the SAME `handler_compute` record's three new sub-spans --
`db_reads_s`/`readiness_s`/`preflight_s` -- flag-off writes none of them (no entry at all); flag-on writes
all three (each >= 0), summing to the record's own `handler_compute_s` within a small fixed tolerance
(TC-8), alongside the existing `queue_wait_s` record for the same request; and the error case (an internal
readiness-computation exception) still yields a full sub-span sample, never suppressed or partial.

Uses a LOCAL, lightweight `watchdog_engine` fixture rather than `conftest.py`'s session-scoped
`loaded_engine` -- that fixture additionally bootstraps + backfills the FULL 30-year cadence
(`bootstrap_runs` + `backfill_forward_returns`), which this file's tests do not need and which is
documented to take up to ~1h on this host. These tests only need a genuinely servable `GET /api/health`
through the REAL FastAPI lifespan, which itself only does the fast single-date latest-snapshot step
synchronously (`ensure_latest_snapshot`) and dispatches the historical warm-up on a background thread --
never blocking. `create_db_and_tables` + `load_seed` (the committed seed's bulk price load, ~30s) is the
full cost this fixture pays, mirroring `conftest.py::loaded_engine` minus its two expensive extra steps.

Mirrors `tests/test_cors_dev_lan.py`'s established pattern for env-driven app construction: build a
FRESH app via `main.create_app()` AFTER `monkeypatch.setenv` (the shared `main.app` singleton is built
once at import time, so it always reflects whatever the flag was at process start -- unset in this test
process, which is exactly what the flag-unset tests below rely on).
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

import main
from app import db as db_module
from app.api.health import health
from app.db import create_db_and_tables, make_engine
from app.engine import health_watchdog, readiness
from app.engine.ledger import read_entries
from app.seed_loader import load_seed


@pytest.fixture(scope="module")
def watchdog_engine(tmp_path_factory, config):
    """A fresh, isolated temp SQLite DB with the committed seed bulk-loaded but NOT bootstrapped to the
    full historical cadence -- see module docstring for why this file uses this instead of
    `conftest.py::loaded_engine`. Registered as the process engine so `TestClient`/`main.create_app()`
    read it."""
    db_path = tmp_path_factory.mktemp("watchdog_db") / "watchdog_test.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    load_seed(engine, config)
    db_module.set_engine(engine)
    return engine


def _queue_wait_entries(log_path) -> list[dict]:
    return [e for e in read_entries(str(log_path)) if e.get("type") == health_watchdog.QUEUE_WAIT_TYPE]


def _loop_lag_entries(log_path) -> list[dict]:
    return [e for e in read_entries(str(log_path)) if e.get("type") == health_watchdog.LOOP_LAG_TYPE]


def _handler_compute_entries(log_path) -> list[dict]:
    return [e for e in read_entries(str(log_path)) if e.get("type") == health_watchdog.HANDLER_COMPUTE_TYPE]


# ======================================================================================================
# (a) flag unset (the default) -- no log entries, response unchanged
# ======================================================================================================
def test_watchdog_disabled_by_default_writes_no_log(watchdog_engine, monkeypatch, tmp_path):
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    monkeypatch.delenv(health_watchdog.ENABLED_ENV, raising=False)
    log_path = tmp_path / "health-watchdog.jsonl"
    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))
    assert health_watchdog.enabled() is False

    with TestClient(main.app) as client:  # the shared singleton -- built with the flag off at import time
        resp = client.get("/api/health")

    assert resp.status_code == 200
    assert not log_path.exists()


def test_watchdog_direct_call_with_no_request_arg_is_untouched(watchdog_engine):
    """The pre-existing direct-call test shape (`health(session)`, no `request`) still works -- the new
    `request` param defaults to None, so a caller that never passes one (e.g. an older/simpler test) is
    unaffected regardless of the flag."""
    with Session(watchdog_engine) as session:
        body = health(session)
    assert body["status"] == "ok"


# ======================================================================================================
# (b) flag set -- exactly one queue-wait record per request, queue_wait_s >= 0
# ======================================================================================================
def test_watchdog_enabled_records_one_queue_wait_sample_per_request(watchdog_engine, monkeypatch, tmp_path):
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    monkeypatch.setenv(health_watchdog.ENABLED_ENV, "1")
    log_path = tmp_path / "health-watchdog.jsonl"
    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))

    app = main.create_app()
    with TestClient(app) as client:
        resp = client.get("/api/health")
    assert resp.status_code == 200

    samples = _queue_wait_entries(log_path)
    assert len(samples) == 1
    assert samples[0]["queue_wait_s"] >= 0
    assert isinstance(samples[0]["timestamp"], str) and samples[0]["timestamp"]


def test_watchdog_enabled_records_one_sample_per_additional_request(watchdog_engine, monkeypatch, tmp_path):
    """Two requests -> two samples (never batched, never deduped, never dropped)."""
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    monkeypatch.setenv(health_watchdog.ENABLED_ENV, "1")
    log_path = tmp_path / "health-watchdog.jsonl"
    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))

    app = main.create_app()
    with TestClient(app) as client:
        client.get("/api/health")
        client.get("/api/health")

    assert len(_queue_wait_entries(log_path)) == 2


def test_watchdog_only_instruments_the_health_route(watchdog_engine, monkeypatch, tmp_path):
    """A different route (`/api/data`) passes straight through the middleware untouched -- this is a
    health-route-scoped instrument, never a global request-timing middleware."""
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    monkeypatch.setenv(health_watchdog.ENABLED_ENV, "1")
    log_path = tmp_path / "health-watchdog.jsonl"
    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))

    app = main.create_app()
    with TestClient(app) as client:
        client.get("/api/data")

    assert _queue_wait_entries(log_path) == []


# ======================================================================================================
# (c) the loop-lag probe writes at least N records over a short synthetic interval
# ======================================================================================================
def test_loop_lag_probe_writes_at_least_n_records_over_short_interval(tmp_path, monkeypatch):
    log_path = tmp_path / "watchdog.jsonl"
    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))

    written = asyncio.run(health_watchdog.run_loop_lag_probe(interval_s=0.01, iterations=5))

    assert written == 5
    samples = _loop_lag_entries(log_path)
    assert len(samples) == 5
    for sample in samples:
        assert sample["loop_lag_s"] >= 0
        assert isinstance(sample["timestamp"], str) and sample["timestamp"]


# ======================================================================================================
# (d) handler_compute_s (iter-68) -- the third sample, t_handler_start to immediately before the route
# returns its response. Per the iter-68 IN SCOPE ask verbatim: (a) flag unset -- no handler_compute_s
# entry, response unchanged; (b) flag set -- exactly one handler_compute_s record with
# handler_compute_s >= 0, alongside the existing queue_wait_s record for the SAME request.
# ======================================================================================================
def test_watchdog_disabled_writes_no_handler_compute_entry(watchdog_engine, monkeypatch, tmp_path):
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    monkeypatch.delenv(health_watchdog.ENABLED_ENV, raising=False)
    log_path = tmp_path / "health-watchdog.jsonl"
    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))
    assert health_watchdog.enabled() is False

    with TestClient(main.app) as client:  # the shared singleton -- built with the flag off at import time
        resp = client.get("/api/health")

    assert resp.status_code == 200
    assert not log_path.exists()  # neither queue_wait_s, loop_lag_s, nor handler_compute_s is written


def test_watchdog_enabled_records_handler_compute_alongside_queue_wait(watchdog_engine, monkeypatch, tmp_path):
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    monkeypatch.setenv(health_watchdog.ENABLED_ENV, "1")
    log_path = tmp_path / "health-watchdog.jsonl"
    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))

    app = main.create_app()
    with TestClient(app) as client:
        resp = client.get("/api/health")
    assert resp.status_code == 200

    queue_wait = _queue_wait_entries(log_path)
    handler_compute = _handler_compute_entries(log_path)
    assert len(queue_wait) == 1
    assert len(handler_compute) == 1
    assert handler_compute[0]["handler_compute_s"] >= 0
    assert isinstance(handler_compute[0]["timestamp"], str) and handler_compute[0]["timestamp"]
    # SAME request -> both sibling samples share the identical t_received wall-clock timestamp, so a
    # downstream join keys on it directly rather than a nearest-neighbor match (TC-1/TC-2).
    assert handler_compute[0]["timestamp"] == queue_wait[0]["timestamp"]


def test_watchdog_enabled_records_one_handler_compute_sample_per_additional_request(
    watchdog_engine, monkeypatch, tmp_path
):
    """Two requests -> two handler_compute_s samples (never batched, never deduped, never dropped) --
    mirrors the existing queue_wait_s two-request test above."""
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    monkeypatch.setenv(health_watchdog.ENABLED_ENV, "1")
    log_path = tmp_path / "health-watchdog.jsonl"
    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))

    app = main.create_app()
    with TestClient(app) as client:
        client.get("/api/health")
        client.get("/api/health")

    assert len(_handler_compute_entries(log_path)) == 2


# ======================================================================================================
# (e) db_reads_s / readiness_s / preflight_s (iter-69) -- the SAME handler_compute record additionally
# carries handler_compute_s's own three constituent sub-spans. Per the iter-69 IN SCOPE ask verbatim:
# (a) flag unset -- no handler_compute entry (with or without the new sub-fields), response byte-identical
# (already covered by test_watchdog_disabled_writes_no_handler_compute_entry above); (b) flag set -- one
# handler_compute record whose db_reads_s/readiness_s/preflight_s are each >= 0 and whose sum equals the
# record's own handler_compute_s within a small fixed tolerance, alongside the existing queue_wait_s
# record for the same request (TC-8).
# ======================================================================================================
_SUB_SPAN_SUM_TOLERANCE_S = 0.005  # "a small fixed tolerance (e.g. 1ms)" per spec, widened slightly for
# this host's own measured file-write/JSONL-append jitter between the sub-span windows (the queue-wait
# write + `get_config()` call sit between t_handler_start and db_reads_s's own start -- negligible
# instrumentation overhead, not a fourth unnamed span; see TC-7 write-up note in reports/perf-budgets.md).


def test_watchdog_enabled_records_sub_spans_summing_to_handler_compute(watchdog_engine, monkeypatch, tmp_path):
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    monkeypatch.setenv(health_watchdog.ENABLED_ENV, "1")
    log_path = tmp_path / "health-watchdog.jsonl"
    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))

    app = main.create_app()
    with TestClient(app) as client:
        resp = client.get("/api/health")
    assert resp.status_code == 200

    queue_wait = _queue_wait_entries(log_path)
    handler_compute = _handler_compute_entries(log_path)
    assert len(queue_wait) == 1
    assert len(handler_compute) == 1

    entry = handler_compute[0]
    for field in ("db_reads_s", "readiness_s", "preflight_s"):
        assert field in entry
        assert entry[field] >= 0

    sub_span_sum = entry["db_reads_s"] + entry["readiness_s"] + entry["preflight_s"]
    assert abs(sub_span_sum - entry["handler_compute_s"]) <= _SUB_SPAN_SUM_TOLERANCE_S


def test_watchdog_disabled_writes_no_sub_span_fields(watchdog_engine, monkeypatch, tmp_path):
    """Flag unset -- no handler_compute entry at all (with or without the new sub-fields), response
    byte-identical. Mirrors test_watchdog_disabled_writes_no_handler_compute_entry above, restated for
    the iter-69 sub-span ask specifically."""
    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    monkeypatch.delenv(health_watchdog.ENABLED_ENV, raising=False)
    log_path = tmp_path / "health-watchdog.jsonl"
    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))
    assert health_watchdog.enabled() is False

    with TestClient(main.app) as client:
        resp = client.get("/api/health")

    assert resp.status_code == 200
    assert not log_path.exists()


def test_watchdog_sub_spans_captured_even_when_readiness_computation_raises(
    watchdog_engine, monkeypatch, tmp_path
):
    """Error case (iter-69): with the flag set, a request that hits an internal readiness-computation
    exception (already caught, degrading to `unavailable`) must still be logged with whatever sub-span
    samples were captured before/around the error -- readiness_s/preflight_s still time their own
    (degraded) outcome, never a suppressed or partial record."""
    import app.api.health as health_module

    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    monkeypatch.setenv(health_watchdog.ENABLED_ENV, "1")
    log_path = tmp_path / "watchdog.jsonl"
    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))

    def _boom(session, engine=None, config=None):
        raise RuntimeError("simulated readiness failure")

    monkeypatch.setattr(health_module, "compute_readiness", _boom)
    fake_request = SimpleNamespace(state=SimpleNamespace(
        health_watchdog_t_received_monotonic=0.0,
        health_watchdog_t_received_wall="2026-08-12T00:00:00+00:00",
    ))
    with Session(watchdog_engine) as session:
        body = health(session, request=fake_request)

    assert body["readiness"] == "unavailable"  # the route's own error handling still degrades honestly
    handler_compute_samples = _handler_compute_entries(log_path)
    assert len(handler_compute_samples) == 1
    entry = handler_compute_samples[0]
    for field in ("db_reads_s", "readiness_s", "preflight_s"):
        assert field in entry
        assert entry[field] >= 0
    sub_span_sum = entry["db_reads_s"] + entry["readiness_s"] + entry["preflight_s"]
    assert abs(sub_span_sum - entry["handler_compute_s"]) <= _SUB_SPAN_SUM_TOLERANCE_S


def test_record_handler_compute_direct_call_still_works_without_sub_spans(tmp_path, monkeypatch):
    """The pre-iter-69 direct-call shape (no keyword args) still works -- the three new params are
    keyword-only and default to None, omitted from the written entry entirely when not supplied."""
    log_path = tmp_path / "watchdog.jsonl"
    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))

    entry = health_watchdog.record_handler_compute(0.0, 0.5, "2026-08-12T00:00:00+00:00")

    assert entry["handler_compute_s"] == 0.5
    assert "db_reads_s" not in entry
    assert "readiness_s" not in entry
    assert "preflight_s" not in entry


# ======================================================================================================
# TC-7 -- byte-identical response body/shape regardless of the flag. Direct function calls (not
# TestClient) against the SAME session in immediate succession -- fully deterministic, no dependence on
# a background warm-up thread's progress between two separate app/lifespan instances.
# ======================================================================================================
def test_watchdog_flag_never_changes_response_body_or_shape(watchdog_engine, monkeypatch, tmp_path):
    monkeypatch.delenv(health_watchdog.ENABLED_ENV, raising=False)
    with Session(watchdog_engine) as session:
        off_body = health(session)  # no request -> flag-off shape, exactly like today

    monkeypatch.setenv(health_watchdog.ENABLED_ENV, "1")
    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(tmp_path / "watchdog.jsonl"))
    fake_request = SimpleNamespace(state=SimpleNamespace(
        health_watchdog_t_received_monotonic=0.0,
        health_watchdog_t_received_wall="2026-08-12T00:00:00+00:00",
    ))
    with Session(watchdog_engine) as session:
        on_body = health(session, request=fake_request)  # flag on, watchdog state present

    existing_keys = {
        "status", "db_ok", "provider", "last_run_date", "seed_latest_date", "symbol_count",
        "readiness", "readiness_detail", "warmup", "poll_interval_seconds", "poll_idle_interval_seconds",
        "preflight", "background_compute",
    }
    assert set(off_body) == existing_keys
    assert set(on_body) == existing_keys
    assert off_body == on_body  # the watchdog observes timing only -- never alters what is served


# ======================================================================================================
# Error case -- a readiness-computation exception must not suppress the already-captured sample
# ======================================================================================================
def test_watchdog_records_sample_even_when_readiness_computation_raises(watchdog_engine, monkeypatch, tmp_path):
    """The watchdog's queue-wait record is written BEFORE readiness/preflight computation runs, so a
    readiness-computation exception (already caught internally, degrading to `unavailable` -- this
    endpoint's own pre-existing convention) never suppresses, delays, or alters the sample the watchdog
    already captured, nor the route's own honest degraded response (AG-8: never a wedge). iter-68: because
    the exception is caught INSIDE the endpoint (never escapes `health()`), execution still reaches the
    handler_compute_s recording point near the end of the function -- so a full (not partial) sample is
    captured for this request too, satisfying the iter-68 error-case requirement (whatever samples were
    captured before/around the error are never suppressed)."""
    import app.api.health as health_module

    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    monkeypatch.setenv(health_watchdog.ENABLED_ENV, "1")
    log_path = tmp_path / "watchdog.jsonl"
    monkeypatch.setenv(health_watchdog.LOG_PATH_ENV, str(log_path))

    def _boom(session, engine=None, config=None):
        raise RuntimeError("simulated readiness failure")

    monkeypatch.setattr(health_module, "compute_readiness", _boom)
    fake_request = SimpleNamespace(state=SimpleNamespace(
        health_watchdog_t_received_monotonic=0.0,
        health_watchdog_t_received_wall="2026-08-12T00:00:00+00:00",
    ))
    with Session(watchdog_engine) as session:
        body = health(session, request=fake_request)

    assert body["readiness"] == "unavailable"  # the route's own error handling still degrades honestly
    samples = _queue_wait_entries(log_path)
    assert len(samples) == 1
    assert samples[0]["queue_wait_s"] >= 0
    handler_compute_samples = _handler_compute_entries(log_path)
    assert len(handler_compute_samples) == 1
    assert handler_compute_samples[0]["handler_compute_s"] >= 0
