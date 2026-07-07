"""As-of resolver — the snapshot-served read-path keystone (iter-8, J-15 + J-13).

`resolve_run(session, as_of, cfg)` maps an optional ?as_of= string to the IMMUTABLE stored snapshot
for the resolved date: it returns the existing `scanner_runs` row when present, else creates it
EXACTLY ONCE via the canonical `run_scan` (INSERT-only, bars <= D). These tests are named proofs of
the critical anti-goals the resolver must inherit:

  - default-is-latest-stored   — `as_of=None` resolves to the latest STORED run's as-of date.
  - given-date-resolves-stored — a provided date resolves to that date's stored snapshot.
  - create-once-immutable      — a not-yet-stored seed date creates the snapshot once; a SECOND view
                                 reads the existing rows (no UPDATE, no duplicate run / child rows).
                                 *(On-demand snapshots stay immutable)*
  - on-demand-no-lookahead     — an as-of-D snapshot created on demand uses only bars with date <= D
                                 (future bars cannot influence it).                 *(No lookahead)*
  - invalid-as-of-no-fabrication — unparseable / future / before-history raise AsOfError with the
                                 right semantic kind (the API maps them to 422 / 400) — never a
                                 fabricated snapshot.                          *(No fabricated data)*

Each test runs on an isolated temp engine (it never calls set_engine), so it does not touch the
shared process engine other API tests use.
"""
from __future__ import annotations

import pytest
from sqlalchemy import delete, func
from sqlmodel import Session, select

from app.db import create_db_and_tables, make_engine
from app.engine.prices import latest_data_date
from app.engine.scanner import (
    AsOfError,
    bootstrap_runs,
    get_run_for_date,
    resolve_as_of_date,
    resolve_run,
)
from app.engine.universe_screen import read_pool
from app.models import DailyPrice, ScannerResult, ScannerRun
from app.seed_loader import load_seed


@pytest.fixture(scope="module")
def resolver_engine(tmp_path_factory, config, seed_dir):
    """An isolated temp DB with the real seed loaded ONCE and the snapshot runs bootstrapped
    (the configured bootstrap dates + the latest data date), mirroring the live app — but NOT
    registered as the process engine, so it is independent of the FastAPI TestClient tests."""
    db_path = tmp_path_factory.mktemp("resolver_db") / "resolver.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    summary = load_seed(engine, config, seed_dir)
    assert summary["loaded"] is True and summary["price_rows"] > 0
    bootstrap_runs(engine, config)
    return engine


def test_resolve_default_is_latest_stored_run(resolver_engine, config):
    """`as_of=None` resolves to the latest STORED run — which, after bootstrap, is the latest data date."""
    with Session(resolver_engine) as session:
        latest = latest_data_date(session)
        run = resolve_run(session, None, config)
    assert run.asof_date == latest


def test_resolve_empty_string_is_latest_stored_run(resolver_engine, config):
    """An empty ?as_of= (the UI's "Latest" option) is treated like None — the latest stored run."""
    with Session(resolver_engine) as session:
        latest = latest_data_date(session)
        run = resolve_run(session, "", config)
    assert run.asof_date == latest


def test_resolve_given_date_returns_that_stored_snapshot(resolver_engine, config):
    """A provided historical date resolves to THAT date's already-stored snapshot (the existing run,
    not a new one) and echoes the resolved as-of date."""
    target = min(config.scanner.bootstrap_dates)
    with Session(resolver_engine) as session:
        existing = get_run_for_date(session, target)
        assert existing is not None  # bootstrap already stored it
        run = resolve_run(session, target.isoformat(), config)
    assert run.asof_date == target
    assert run.id == existing.id  # the SAME stored run, not a recreation


def test_resolve_as_of_date_echoes_resolved_date(resolver_engine, config):
    """The resolver returns the concrete date it will serve, so the API can echo `asof_date`."""
    target = max(config.scanner.bootstrap_dates)
    with Session(resolver_engine) as session:
        resolved = resolve_as_of_date(session, target.isoformat(), config)
    assert resolved == target


def test_resolve_run_create_once_then_immutable(tmp_path, config, seed_dir):
    """On-demand-snapshots-stay-immutable critical: viewing a not-yet-stored seed date CREATES the
    snapshot once; a SECOND view reads the existing rows — no UPDATE (created_at unchanged) and no
    duplicate run / child rows (counts + identity unchanged)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'create_once.db'}")
    create_db_and_tables(engine)
    load_seed(engine, config, seed_dir)
    target = min(config.scanner.bootstrap_dates)  # a real seed trading day, not yet stored here

    with Session(engine) as session:
        assert get_run_for_date(session, target) is None  # nothing stored for this date yet
        run1 = resolve_run(session, target.isoformat(), config)  # first view → create once
        run_id, created_at = run1.id, run1.created_at
        runs_for_date_1 = session.scalar(
            select(func.count()).select_from(ScannerRun).where(ScannerRun.asof_date == target)
        )
        results_1 = session.scalar(
            select(func.count()).select_from(ScannerResult).where(ScannerResult.run_id == run_id)
        )

    with Session(engine) as session:
        run2 = resolve_run(session, target.isoformat(), config)  # second view → read existing
        assert run2.id == run_id
        assert run2.created_at == created_at  # NOT mutated (no UPDATE)
        runs_for_date_2 = session.scalar(
            select(func.count()).select_from(ScannerRun).where(ScannerRun.asof_date == target)
        )
        results_2 = session.scalar(
            select(func.count()).select_from(ScannerResult).where(ScannerResult.run_id == run_id)
        )

    assert runs_for_date_1 == runs_for_date_2 == 1  # exactly one run for the date (create-once)
    # iter-33 (J-93): the child-row count is the resolved-at-D membership (stable across the two views —
    # no duplicate child rows), a non-empty subset of the BROADENED candidate pool at a full-universe
    # date. iter-18 resolves membership from `universe_screen.read_pool` (the 548-name 30y pool), NOT the
    # legacy static `config.universe.symbols` (122) — so the upper bound is the pool size.
    assert results_1 == results_2 and 0 < results_1 <= len(read_pool(seed_dir))


def test_resolve_run_on_demand_has_no_lookahead(tmp_path, config, seed_dir):
    """No-lookahead critical on on-demand creation: a snapshot created for date D against the FULL
    seed is byte-identical to one created against a DB truncated to bars with date <= D — so a future
    bar (date > D) cannot influence any stored as-of score (the resolver inherits run_scan's boundary)."""
    target = max(config.scanner.bootstrap_dates)  # historical date well within the seed

    full = make_engine(f"sqlite:///{tmp_path / 'full.db'}")
    create_db_and_tables(full)
    load_seed(full, config, seed_dir)

    trunc = make_engine(f"sqlite:///{tmp_path / 'trunc.db'}")
    create_db_and_tables(trunc)
    load_seed(trunc, config, seed_dir)
    with Session(trunc) as session:
        session.execute(delete(DailyPrice).where(DailyPrice.date > target))
        session.commit()
        assert latest_data_date(session) <= target

    with Session(full) as session:
        run_full = resolve_run(session, target.isoformat(), config)
        full_rows = [
            r.record_json
            for r in session.exec(
                select(ScannerResult).where(ScannerResult.run_id == run_full.id).order_by(ScannerResult.rank)
            ).all()
        ]
    with Session(trunc) as session:
        run_trunc = resolve_run(session, target.isoformat(), config)
        trunc_rows = [
            r.record_json
            for r in session.exec(
                select(ScannerResult).where(ScannerResult.run_id == run_trunc.id).order_by(ScannerResult.rank)
            ).all()
        ]

    assert full_rows == trunc_rows  # future bars did not influence the on-demand as-of snapshot


def test_resolve_unparseable_as_of_raises_unparseable(resolver_engine, config):
    with Session(resolver_engine) as session:
        with pytest.raises(AsOfError) as exc:
            resolve_as_of_date(session, "not-a-date", config)
    assert exc.value.kind == "unparseable"


def test_resolve_future_as_of_raises_future(resolver_engine, config):
    with Session(resolver_engine) as session:
        with pytest.raises(AsOfError) as exc:
            resolve_as_of_date(session, "2999-01-01", config)
    assert exc.value.kind == "future"


def test_resolve_before_history_as_of_raises_before_history(resolver_engine, config):
    with Session(resolver_engine) as session:
        with pytest.raises(AsOfError) as exc:
            resolve_as_of_date(session, "1900-01-01", config)
    assert exc.value.kind == "before_history"


def test_resolve_no_price_data_raises_no_data(tmp_path, config):
    """No price data at all → AsOfError(no_data) (the API maps it to 503) — never a fabricated run."""
    engine = make_engine(f"sqlite:///{tmp_path / 'empty.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        assert latest_data_date(session) is None
        with pytest.raises(AsOfError) as exc:
            resolve_run(session, None, config)
    assert exc.value.kind == "no_data"
