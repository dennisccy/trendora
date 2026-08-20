"""Shared pytest fixtures. The committed seed must exist (built by scripts/ingest_seed.py)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlmodel import Session

BACKEND_DIR = Path(__file__).resolve().parents[1]
SEED_DIR = BACKEND_DIR / "data" / "seed"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import db as db_module  # noqa: E402
from app.config import load_config  # noqa: E402
from app.db import create_db_and_tables, make_engine  # noqa: E402
from app.engine.forward_testing import backfill_forward_returns, forward_aggregates_ingest_cached  # noqa: E402
from app.engine.scanner import _latest_stored_run_date, bootstrap_runs  # noqa: E402
from app.seed_loader import load_seed  # noqa: E402


def pytest_configure(config):
    """Register the `integration` marker (real external network tests; may be skipped offline) so the
    Data Manager live-fetch integration test is selectable and warning-free."""
    config.addinivalue_line(
        "markers", "integration: hits a real external system (network); may be skipped offline"
    )


@pytest.fixture(scope="session", autouse=True)
def _isolated_compass_export_dir(tmp_path_factory):
    """goal-market-compass iter-3 (J-05/J-06) audit: point the next-session-manifest export writer
    (`compass._write_export`) at a per-run temp dir so NO test ever writes into the product's configured
    `compass.manifest.export_dir`. A synthetic fixture's as-of can collide with a real frozen at-ingest
    artifact's file name there, and an exported manifest is immutable (AG-12) — tests must never land in
    that directory at all. Env-var override only (name, never a value in files)."""
    import os

    os.environ["TRENDORA_COMPASS_EXPORT_DIR"] = str(tmp_path_factory.mktemp("compass_exports"))
    yield
    os.environ.pop("TRENDORA_COMPASS_EXPORT_DIR", None)


@pytest.fixture(scope="session")
def config():
    return load_config()


@pytest.fixture(scope="session")
def seed_dir() -> Path:
    return SEED_DIR


@pytest.fixture(scope="session")
def loaded_engine(tmp_path_factory, config, seed_dir):
    """A temp SQLite DB with the real committed seed loaded ONCE, then warmed to the FULL historical
    cadence ONCE. Also registered as the process engine so the FastAPI app (TestClient) reads the same
    database.

    iter-28: the FastAPI `lifespan` no longer does the historical walk-forward synchronously — it persists
    only the latest snapshot and warms the cadence in a BACKGROUND daemon thread (J-40). The API test suite
    has an implicit DETERMINISM CONTRACT with a fully-warm DB (research/backtest/runs/as-of tests need the
    complete cadence; J-08 needs >= 2 dated runs; immutability tests count snapshot rows expecting them
    stable). To restore that contract WITHOUT weakening the product's fast boot, this fixture brings the
    shared DB to the warm state ONCE here — via the SAME canonical engines the warm-up uses
    (`bootstrap_runs` + `backfill_forward_returns`); `test_warmup.py::test_..._only_old_synchronous_path_is_a_noop`
    proves this is byte-identical to what the background warm-up produces (no second compute path). With
    the DB already warm, the `TestClient` lifespan's single-flight-guarded warm-up is an idempotent no-op,
    so tests never assert against a mid-warm-up, concurrently-mutating DB.

    ops-hardening iter-16 (J-08): `GET /api/backtest` / MCP `query_backtest`'s LATEST (`is_latest==True`)
    view now serves `evidence_by_horizon` ONLY from the read-only `resolved_forward_aggregate_evidence`
    resolver, which NEVER computes on a request — so the latest run's `ForwardAggregateCache` rows must
    already exist before any test reads them, exactly as the real ingest finalize hook
    (`data_manager._refresh_ingest_aggregates`) would warm them at ingest time. This fixture mirrors that
    ONE warm sub-step here (via the SAME `forward_aggregates_ingest_cached` the finalize hook calls — no
    second compute path) so the many existing `loaded_engine`-based tests that read the latest date's
    `evidence_by_horizon` content keep seeing the SAME byte-identical values they did before the J-08
    split (previously warmed lazily on a test's first `/api/backtest` request; now warmed here up front,
    since the request path itself no longer computes)."""
    db_path = tmp_path_factory.mktemp("db") / "trendora_test.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    summary = load_seed(engine, config, seed_dir)
    assert summary["loaded"] is True and summary["price_rows"] > 0
    # Bring the DB to the fully-warm cadence ONCE, deterministically, via the canonical engines — the same
    # work the background warm-up does, only paid up-front + synchronously so the suite is deterministic.
    bootstrap_runs(engine, config)
    backfill_forward_returns(engine, config)
    with Session(engine) as session:
        latest_date = _latest_stored_run_date(session)
        if latest_date is not None:
            for h in config.walk_forward.horizons:
                forward_aggregates_ingest_cached(session, h, config, as_of=latest_date)
    db_module.set_engine(engine)
    return engine
