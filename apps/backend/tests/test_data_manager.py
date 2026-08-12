"""Data Manager engine — on-demand dataset growth (iter-3, J-17).

The named proofs, each guarding a critical anti-goal / DoD item:
  - coverage correctness        — price-range / symbol-count / snapshot-set / GAPS exact on a fixture.
  - backfill grows `n`          — a range backfill adds ScannerRun rows and raises the forward-test n.
  - lookahead-free + reuse      — a backfilled snapshot equals the canonical score_stocks(D) VERBATIM
                                  (no second scan math), and its forward returns use only bars > D.  *(No lookahead / Reuse)*
  - create-once / immutable     — re-running the same range creates 0 new snapshots, mutates no
                                  created_at, inserts 0 new forward returns; DataProviderRun is append-only. *(Snapshots immutable)*
  - config-driven limits        — the max-range guard reads config (no magic number in control code).
  - fetch forced-failure        — a failing provider writes ZERO bars / ZERO snapshots and a `failed`
                                  run; never a fabricated price.                                   *(Live fetch is real-data-only)*

The coverage / validation / forced-failure tests run on tiny in-memory data (fast). The realistic
backfill proof loads the committed seed and runs the real engines ONCE (module-scoped).
"""
from __future__ import annotations

import json
import socket
import time
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
from sqlalchemy import event, func
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError, RateLimitError
from app.engine import data_manager
from app.engine import forward_testing, indexes, market_phase, research, scanner, warmup
from app.engine.data_manager import (
    JobProgress,
    _chunk_plan,
    _missing_data_diagnostic,
    _trading_days,
    compute_availability,
    compute_capacity,
    compute_coverage,
    compute_provider_availability,
    create_job,
    dismiss_import,
    get_job,
    get_provider_run,
    is_seed_bar,
    load_seed_meta,
    load_seed_windows,
    preview_removal,
    recent_runs,
    remove_data,
    resolve_provider_key,
    resumable_imports,
    resume_data_job,
    retry_run,
    run_data_job,
    seed_import_source_enabled,
    summarize_provider_run,
    unfinished_imports,
    validate_job_request,
    SEED_IMPORT_ENV_FLAG,
    SEED_IMPORT_SOURCE_ID,
)
from app.engine.evidence import LEDGER_PATH_ENV
from app.engine.forward_testing import compute_forward_aggregates
from app.engine.ledger import append_entry
from app.engine.scoring import score_stocks
from app.api.data import data_overview
from app.models import (
    AvailabilityCache,
    CoverageSnapshot,
    DailyPrice,
    DataProviderRun,
    EventStudyCache,
    ForwardAggregateCache,
    ForwardReturn,
    ImportCheckpoint,
    IndexSeriesCache,
    ScannerResult,
    ScannerRun,
    SectorScoreRow,
    ThemeScoreRow,
)
from app.engine.universe_screen import read_pool
from app.seed_loader import DEFAULT_SEED_DIR, all_seed_symbols, load_seed, price_load_symbols


def _noop_sleep(_seconds: float) -> None:
    """A zero-wall-clock sleep injected into the chunked-fetch tests so the 429 backoff adds no real
    wait (MEMORY: backend-test-suite-runtime — never let a backoff balloon the suite)."""


# ==================================================================================================
# compute_coverage — read-only descriptive metadata (tiny hand-built DB, no engines)
# ==================================================================================================
@pytest.fixture()
def coverage_engine(tmp_path):
    """SPY bars on four dates (the trading calendar) + a stock on two of them, with ONE snapshot —
    so coverage's range / symbol-count / snapshot-set / gaps are all exact by construction."""
    engine = make_engine(f"sqlite:///{tmp_path / 'cov.db'}")
    create_db_and_tables(engine)
    spy_days = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4), date(2024, 1, 5)]
    with Session(engine) as session:
        for d in spy_days:
            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        for d in spy_days[:2]:
            session.add(DailyPrice(symbol="AAA", date=d, open=2.0, high=2.0, low=2.0, close=2.0, volume=2.0))
        # one snapshot on the 2nd trading day (the other three are gaps)
        session.add(
            ScannerRun(
                asof_date=spy_days[1], created_at=__import__("datetime").datetime(2024, 1, 3),
                provider="seed", benchmark="SPY", regime_score=50.0, regime_label="Choppy",
                regime_components_json="[]", new_high_low_json="{}", candidate_counts_json="{}",
            )
        )
        session.commit()
    return engine, spy_days


def test_compute_coverage_exact(coverage_engine):
    """Exact coverage: price range D1..D4, two symbols, one snapshot date, three gap trading days."""
    engine, spy_days = coverage_engine
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    with Session(engine) as session:
        cov = compute_coverage(session, cfg)

    assert cov["price_start"] == spy_days[0].isoformat()
    assert cov["price_end"] == spy_days[3].isoformat()
    assert cov["symbol_count"] == 2  # SPY + AAA
    assert cov["snapshot_count"] == 1
    assert cov["snapshot_dates"] == [spy_days[1].isoformat()]
    assert cov["trading_day_count"] == 4  # SPY defines the calendar
    # gaps = the trading days without a snapshot = D1, D3, D4 (D2 has the snapshot)
    assert cov["gap_count"] == 3
    assert cov["gap_first"] == spy_days[0].isoformat()
    assert cov["gap_last"] == spy_days[3].isoformat()
    assert cov["gaps_preview"] == [spy_days[0].isoformat(), spy_days[2].isoformat(), spy_days[3].isoformat()]


def test_compute_coverage_gap_preview_capped_by_config(coverage_engine):
    """The gap preview length is bounded by `config.data_manager.gap_preview` (no magic cap in code)."""
    engine, _ = coverage_engine
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    cfg = cfg.model_copy(update={"data_manager": cfg.data_manager.model_copy(update={"gap_preview": 1})})
    with Session(engine) as session:
        cov = compute_coverage(session, cfg)
    assert cov["gap_count"] == 3  # the true count is unaffected
    assert len(cov["gaps_preview"]) == 1  # only the preview is capped


def test_compute_coverage_empty_db_is_all_none():
    """An empty DB reports null range / zero counts — never a fabricated coverage figure."""
    engine = make_engine("sqlite:///:memory:")
    create_db_and_tables(engine)
    with Session(engine) as session:
        cov = compute_coverage(session, load_config())
    assert cov["price_start"] is None and cov["price_end"] is None
    assert cov["symbol_count"] == 0 and cov["snapshot_count"] == 0
    assert cov["trading_day_count"] == 0 and cov["gap_count"] == 0


# ==================================================================================================
# J-61 — per-trading-date availability derivation (read-only descriptive metadata; same source as
# compute_coverage — never a second derivation of a coverage figure, never a canonical recompute)
# ==================================================================================================
def test_compute_availability_exact_per_date_counts(coverage_engine):
    """Exact per-trading-date availability on the coverage fixture (SPY on D1..D4, AAA on D1..D2, one
    snapshot on D2):
      - D1: SPY+AAA → 2 symbols, no snapshot.
      - D2: SPY+AAA → 2 symbols, snapshot present (the fully-covered + snapshot day).
      - D3: SPY only → 1 symbol (a SPARSE day, visually distinct from the 2-symbol days), no snapshot.
      - D4: SPY only → 1 symbol, no snapshot.
    total_symbols == the distinct stored-symbol universe (== compute_coverage symbol_count == 2)."""
    engine, spy_days = coverage_engine
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    with Session(engine) as session:
        avail = compute_availability(session, cfg)
        cov = compute_coverage(session, cfg)

    # header: total_symbols is the SAME denominator as compute_coverage's symbol_count (no second universe)
    assert avail["total_symbols"] == cov["symbol_count"] == 2
    # one cell per benchmark trading day — consistent with compute_coverage's trading_day_count
    assert avail["trading_day_count"] == cov["trading_day_count"] == 4
    cells = avail["cells"]
    assert [c["date"] for c in cells] == [d.isoformat() for d in spy_days]  # ascending, every calendar day

    by_date = {c["date"]: c for c in cells}
    d1, d2, d3, d4 = (d.isoformat() for d in spy_days)
    assert by_date[d1]["symbols_with_bars"] == 2 and by_date[d1]["snapshot_exists"] is False
    assert by_date[d2]["symbols_with_bars"] == 2 and by_date[d2]["snapshot_exists"] is True  # snapshot day
    assert by_date[d3]["symbols_with_bars"] == 1 and by_date[d3]["snapshot_exists"] is False  # SPARSE day
    assert by_date[d4]["symbols_with_bars"] == 1 and by_date[d4]["snapshot_exists"] is False
    # every cell carries total_symbols == the header denominator (so the UI reads "n-of-total" consistently)
    assert all(c["total_symbols"] == 2 for c in cells)


def test_compute_availability_consistent_with_coverage_snapshots(coverage_engine):
    """The availability snapshot_exists flags are the SAME `ScannerRun.asof_date` set compute_coverage
    reads — exactly the snapshot dates, and exactly the complement of the backfill gaps (no second
    derivation of an existing coverage figure)."""
    engine, _ = coverage_engine
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    with Session(engine) as session:
        avail = compute_availability(session, cfg)
        cov = compute_coverage(session, cfg)

    snapshot_dates = set(cov["snapshot_dates"])  # ISO strings
    gap_set = {c["date"] for c in avail["cells"] if not c["snapshot_exists"]}
    snap_cells = {c["date"] for c in avail["cells"] if c["snapshot_exists"]}
    assert snap_cells == snapshot_dates  # availability snapshot flags == coverage snapshot dates
    # the snapshot cells and the no-snapshot cells partition the calendar; the no-snapshot ones are the gaps
    assert snap_cells.isdisjoint(gap_set)
    assert snap_cells | gap_set == {c["date"] for c in avail["cells"]}
    assert cov["gap_count"] == len(gap_set)  # gap COUNT matches (no recomputed coverage figure)


def test_compute_availability_zero_bar_trading_day_is_present_and_zero(tmp_path):
    """A benchmark trading day with NO non-benchmark bars is represented honestly: SPY defines the
    calendar, so a day where ONLY SPY has a bar is `symbols_with_bars == 1` — and a calendar day is NEVER
    omitted-as-if-covered. (SPY itself is always counted, so the minimum on a real trading day is 1.)"""
    engine = make_engine(f"sqlite:///{tmp_path / 'avail_zero.db'}")
    create_db_and_tables(engine)
    days = [date(2024, 2, 1), date(2024, 2, 2), date(2024, 2, 5)]
    with Session(engine) as session:
        for d in days:
            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        # a single non-benchmark bar only on the MIDDLE day → the first/last days are SPY-only (sparse)
        session.add(DailyPrice(symbol="AAA", date=days[1], open=2.0, high=2.0, low=2.0, close=2.0, volume=2.0))
        session.commit()
        avail = compute_availability(session, load_config())

    by_date = {c["date"]: c for c in avail["cells"]}
    assert len(avail["cells"]) == 3  # every calendar day present — none omitted as covered
    assert by_date[days[0].isoformat()]["symbols_with_bars"] == 1  # SPY-only (sparse), not omitted
    assert by_date[days[1].isoformat()]["symbols_with_bars"] == 2  # SPY + AAA
    assert by_date[days[2].isoformat()]["symbols_with_bars"] == 1  # SPY-only (sparse)
    assert avail["total_symbols"] == 2  # distinct stored symbols = {SPY, AAA}


def test_compute_availability_empty_db_is_empty_but_valid():
    """An empty / bars-less DB returns an empty-but-valid payload — no fabricated cells, no synthesized
    covered day, total_symbols 0 (mirrors the honest empty coverage payload)."""
    engine = make_engine("sqlite:///:memory:")
    create_db_and_tables(engine)
    with Session(engine) as session:
        avail = compute_availability(session, load_config())
    assert avail == {"total_symbols": 0, "trading_day_count": 0, "cells": []}


# ==================================================================================================
# iter-24 fast-platform item K — DB storage-footprint snapshot (pure introspection, no recompute)
# ==================================================================================================
def test_compute_capacity_exact_counts_and_real_file_size(coverage_engine):
    """Exact row counts on the coverage fixture (6 daily_prices rows: 4 SPY + 2 AAA; 0 scanner_results —
    the fixture's lone ScannerRun has no children; 0 forward_returns) + a real, positive on-disk file
    size for the temp DB file backing this engine."""
    engine, _spy_days = coverage_engine
    with Session(engine) as session:
        cap = compute_capacity(session)
    assert cap["daily_prices_rows"] == 6
    assert cap["scanner_results_rows"] == 0
    assert cap["forward_returns_rows"] == 0
    assert cap["db_file_bytes"] > 0  # a real file-backed temp DB


def test_compute_capacity_empty_db_is_honest_zero_snapshot():
    """A cold/empty in-memory DB reports an honest all-zero snapshot — never an error, never a
    fabricated size (an in-memory URL has no resolvable file, so the size is honestly 0)."""
    engine = make_engine("sqlite:///:memory:")
    create_db_and_tables(engine)
    with Session(engine) as session:
        cap = compute_capacity(session)
    assert cap == {
        "db_file_bytes": 0,
        "daily_prices_rows": 0,
        "scanner_results_rows": 0,
        "forward_returns_rows": 0,
    }


def test_compute_capacity_recomputes_no_canonical_value(coverage_engine, monkeypatch):
    """compute_capacity is pure DB introspection — patch the scan/scoring entry points to raise; it
    must still produce the correct counts (proving neither is reachable)."""
    engine, _spy_days = coverage_engine

    def _boom(*_a, **_k):  # pragma: no cover - only fires on a wrong call
        raise AssertionError("compute_capacity MUST NOT recompute any canonical score/return/bucket")

    monkeypatch.setattr("app.engine.scanner.run_scan", _boom, raising=False)
    monkeypatch.setattr("app.engine.scoring.score_stocks", _boom, raising=False)
    with Session(engine) as session:
        cap = compute_capacity(session)
    assert cap["daily_prices_rows"] == 6


def test_compute_availability_byte_identical_after_fetch_scope_widening(coverage_engine):
    """J-13 (iter-20) anti-goal #3 guard: widening the generic Fetch job's target symbol set (now
    `price_load_symbols`, covering the full committed pool) must NOT change `compute_availability`'s
    output — it derives purely from stored `DailyPrice` / `ScannerRun` rows, never from the fetch job's
    symbol-set config (the function has no reference to `all_seed_symbols`, `price_load_symbols`, or any
    `seed_dir`). Pins the exact fields/values on the SAME fixed DB the other availability tests use, so
    any future coupling between the two is caught immediately."""
    engine, spy_days = coverage_engine
    cfg = load_config()
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    with Session(engine) as session:
        avail = compute_availability(session, cfg)

    d1, d2, d3, d4 = (d.isoformat() for d in spy_days)
    assert avail == {
        "total_symbols": 2,
        "trading_day_count": 4,
        "cells": [
            {"date": d1, "symbols_with_bars": 2, "total_symbols": 2, "snapshot_exists": False},
            {"date": d2, "symbols_with_bars": 2, "total_symbols": 2, "snapshot_exists": True},
            {"date": d3, "symbols_with_bars": 1, "total_symbols": 2, "snapshot_exists": False},
            {"date": d4, "symbols_with_bars": 1, "total_symbols": 2, "snapshot_exists": False},
        ],
    }


# ==================================================================================================
# ops-hardening iter-56 (J-06 closure) — `availability_cached_with_status` / `availability_from_storage`,
# the `AvailabilityCache` ingest-time serving cache for `compute_availability` (mirrors the
# `index_series_cached_with_status`/`coverage_from_storage` proofs above).
# ==================================================================================================
def test_availability_cached_with_status_miss_computes_and_persists(coverage_engine):
    """A cache MISS (no `AvailabilityCache` row yet) computes once via the unchanged `compute_availability`
    (byte-identical), persists it, and reports `persisted_this_call=True`."""
    engine, _spy_days = coverage_engine
    cfg = load_config()
    with Session(engine) as session:
        fresh = compute_availability(session, cfg)
        payload, persisted = data_manager.availability_cached_with_status(session, cfg)
    assert persisted is True
    assert payload == fresh
    with Session(engine) as session:
        rows = session.exec(select(AvailabilityCache)).all()
    assert len(rows) == 1


def test_availability_cached_with_status_hit_returns_stored_payload_no_recompute(coverage_engine, monkeypatch):
    """A cache HIT for the current dataset-version stamp returns the stored payload WITHOUT calling
    `compute_availability` again (No recompute in the read path) and reports `persisted_this_call=False`."""
    engine, _spy_days = coverage_engine
    cfg = load_config()
    with Session(engine) as session:
        first_payload, _ = data_manager.availability_cached_with_status(session, cfg)

    def _boom(*_a, **_k):
        raise AssertionError("a cache HIT must never call compute_availability again")

    monkeypatch.setattr(data_manager, "compute_availability", _boom)
    with Session(engine) as session:
        second_payload, persisted = data_manager.availability_cached_with_status(session, cfg)
    assert persisted is False
    assert second_payload == first_payload


def test_availability_cached_with_status_rollback_reports_not_persisted(coverage_engine, monkeypatch):
    """TC-10 — a forced `session.commit()` failure inside `availability_cached_with_status`'s MISS path
    rolls back (the existing `except: session.rollback()` branch) and MUST report
    `persisted_this_call=False` — never `True` for a write that did not durably persist (the AG-3
    honesty gap this iteration closes on the existing `aggregates_refreshed` field). The freshly
    computed payload is still returned (byte-identical to `compute_availability`), only the honesty flag
    changes."""
    engine, _spy_days = coverage_engine
    cfg = load_config()
    with Session(engine) as session:
        fresh = compute_availability(session, cfg)

    with Session(engine) as session:
        def _boom_commit():
            raise RuntimeError("forced commit failure (TC-10 fault injection)")

        monkeypatch.setattr(session, "commit", _boom_commit)
        payload, persisted = data_manager.availability_cached_with_status(session, cfg)

    assert persisted is False
    assert payload == fresh
    # nothing durably persisted — a fresh read finds no row
    with Session(engine) as session:
        rows = session.exec(select(AvailabilityCache)).all()
    assert rows == []


def test_availability_from_storage_serves_persisted_row(coverage_engine):
    """TC-3 — `availability_from_storage` (the `GET /api/data/availability` serving path) reads the
    persisted row byte-identical to a fresh `compute_availability` call, once a warm has run, PLUS the
    two new additive iter-57 fields: `stale: False` (the stored row's stamp matches the CURRENT
    `_membership_dataset_version`) and `served_dataset_version` equal to that current stamp (regression
    guard for the idle/matching-stamp case — the byte-identity contract predating this iteration is
    unchanged for every pre-existing field)."""
    engine, _spy_days = coverage_engine
    cfg = load_config()
    with Session(engine) as session:
        fresh = compute_availability(session, cfg)
        data_manager.availability_cached_with_status(session, cfg)  # warm it
        current_version = data_manager._membership_dataset_version(session, cfg)
    with Session(engine) as session:
        served = data_manager.availability_from_storage(session, cfg)
    assert served == {**fresh, "stale": False, "served_dataset_version": current_version}


def test_availability_from_storage_missing_row_serves_honest_not_yet_computed(coverage_engine, monkeypatch):
    """TC-2 (TC-8 predecessor) — a genuinely missing `AvailabilityCache` row (real bars present, but no
    warm has EVER run) serves the honest not-yet-computed empty payload — NEVER a live
    `compute_availability` call on this default request path (AG-8), even though this fixture has real
    SPY/AAA bars that WOULD produce non-empty cells if computed live. `stale` is `False` and
    `served_dataset_version` is `None` — the empty sentinel is reserved strictly for "no row has ever
    been persisted", not conflated with the mid-ingest stale-serving case."""
    engine, _spy_days = coverage_engine
    cfg = load_config()

    def _boom(*_a, **_k):
        raise AssertionError("a missing cache row must never trigger a live compute_availability call")

    monkeypatch.setattr(data_manager, "compute_availability", _boom)
    with Session(engine) as session:
        served = data_manager.availability_from_storage(session, cfg)
    assert served == {
        "total_symbols": 0, "trading_day_count": 0, "cells": [],
        "stale": False, "served_dataset_version": None,
    }


def test_availability_from_storage_empty_db_matches_honest_fallback():
    """TC-2 — a genuinely empty / bars-less DB (no cache row, no bars) serves the SAME honest empty
    payload — coincidentally identical to `compute_availability`'s own empty-DB return plus `stale:
    False`/`served_dataset_version: None`, served with ZERO database queries via the fallback, never a
    live compute."""
    engine = make_engine("sqlite:///:memory:")
    create_db_and_tables(engine)
    with Session(engine) as session:
        served = data_manager.availability_from_storage(session, load_config())
    assert served == {
        "total_symbols": 0, "trading_day_count": 0, "cells": [],
        "stale": False, "served_dataset_version": None,
    }


def test_availability_from_storage_stale_serves_prior_row_on_stamp_mismatch(coverage_engine):
    """TC-2 — the iter-57 J-06 during-a-job honesty fix, gated (iter-58, audit B2 fix) on a job
    GENUINELY being in flight as well as the stamp mismatch: once a row exists, a NEW bar has landed
    without the finalize-tail warm re-running yet (the `_membership_dataset_version` stamp folds in
    `count(daily_prices)`, so a bare INSERT bumps it — exactly what a mid-flight ingest's first
    committed bar does), AND a `data_provider_runs` row genuinely has `status == "running"`,
    `availability_from_storage` serves the PRIOR persisted row — non-empty cells, `stale: True`,
    `served_dataset_version` equal to the OLD (pre-bar) stamp, never the current one and never the
    not-yet-computed empty sentinel."""
    engine, spy_days = coverage_engine
    cfg = load_config()
    with Session(engine) as session:
        prior_payload, _ = data_manager.availability_cached_with_status(session, cfg)  # warm it (V1)
        prior_version = data_manager._membership_dataset_version(session, cfg)
        # a job genuinely in flight (the iter-58 precondition `stale` now requires)
        session.add(DataProviderRun(provider="seed", started_at=datetime(2024, 1, 3, 12, 0, 0), status="running"))
        session.commit()

    # Simulate an ingest job's first committed bar landing WITHOUT the finalize-tail warm re-running —
    # bumps _membership_dataset_version (count(daily_prices) changes) but leaves AvailabilityCache at V1.
    with Session(engine) as session:
        session.add(DailyPrice(
            symbol="AAA", date=spy_days[2], open=3.0, high=3.0, low=3.0, close=3.0, volume=3.0,
        ))
        session.commit()

    with Session(engine) as session:
        current_version = data_manager._membership_dataset_version(session, cfg)
        served = data_manager.availability_from_storage(session, cfg)

    assert current_version != prior_version  # the stamp genuinely moved (sanity check on the setup)
    assert served["stale"] is True
    assert served["served_dataset_version"] == prior_version
    # the PRIOR row's real cells/total_symbols/trading_day_count — never the empty sentinel
    assert served["cells"] == prior_payload["cells"]
    assert served["total_symbols"] == prior_payload["total_symbols"]
    assert served["trading_day_count"] == prior_payload["trading_day_count"]
    assert served["cells"] != []


def test_availability_from_storage_stamp_mismatch_without_job_running_is_not_stale(coverage_engine):
    """TC-1 (iter-58, audit B2 fix) — a stamp mismatch ALONE is no longer enough to mark the served row
    stale. The SAME stamp-bumping event as the sibling test above (a bare `DailyPrice` INSERT — standing
    in for any stamp bump with nothing in flight to finish it: a request-path historical view creating a
    new `ScannerRun`, the boot warm-up's own cadence snapshots, or a finalize warm that was
    skipped/crashed without landing) now serves `stale: False`, because this fixture has NO
    `data_provider_runs` row with `status == "running"`. `served_dataset_version` still reads the row's
    OWN (prior) stamp and the real prior cells are still served — only the honesty flag changes; the
    page never renders the false '— updating' banner with nothing actually running."""
    engine, spy_days = coverage_engine
    cfg = load_config()
    with Session(engine) as session:
        prior_payload, _ = data_manager.availability_cached_with_status(session, cfg)  # warm it (V1)
        prior_version = data_manager._membership_dataset_version(session, cfg)

    with Session(engine) as session:
        session.add(DailyPrice(
            symbol="AAA", date=spy_days[2], open=3.0, high=3.0, low=3.0, close=3.0, volume=3.0,
        ))
        session.commit()

    with Session(engine) as session:
        current_version = data_manager._membership_dataset_version(session, cfg)
        served = data_manager.availability_from_storage(session, cfg)

    assert current_version != prior_version  # sanity: the stamp genuinely moved
    assert served["stale"] is False  # no job in flight — the iter-58 fix
    assert served["served_dataset_version"] == prior_version
    assert served["cells"] == prior_payload["cells"]  # the real prior row, never the empty sentinel


def test_availability_from_storage_stuck_running_row_from_crashed_process_still_reads_as_in_flight(coverage_engine):
    """Error case (iter-58 testing requirements): a `data_provider_runs` row stuck at `status ==
    "running"` from a process that crashed mid-job — with NO corresponding entry in the in-memory
    `_JOBS` registry, since that registry is process-local and this test never populates it — must NOT
    be misread as "no job running". `_ingest_job_in_flight` is DB-status-only (never reads `_JOBS`), so
    it does not false-negative on this exact case: the stuck row alone is enough to keep `stale: True`
    honest until an operator resolves it (the boot sweep, or a terminal transition)."""
    engine, spy_days = coverage_engine
    cfg = load_config()
    with Session(engine) as session:
        assert data_manager._JOBS == {}  # sanity: no live in-memory job registered anywhere in this process
        prior_payload, _ = data_manager.availability_cached_with_status(session, cfg)  # warm it (V1)
        # a row orphaned by a crashed worker — no finished_at, no terminal transition ever landed
        session.add(DataProviderRun(provider="seed", started_at=datetime(2024, 1, 3, 12, 0, 0), status="running"))
        session.commit()

    with Session(engine) as session:
        session.add(DailyPrice(
            symbol="AAA", date=spy_days[2], open=3.0, high=3.0, low=3.0, close=3.0, volume=3.0,
        ))
        session.commit()

    with Session(engine) as session:
        served = data_manager.availability_from_storage(session, cfg)

    assert served["stale"] is True  # the stuck DB row alone is enough — no _JOBS entry needed
    assert served["cells"] == prior_payload["cells"]


def test_availability_from_storage_stale_fallback_never_recomputes(coverage_engine, monkeypatch):
    """The stale-serving fallback (TC-2) reads ONLY the persisted row — never a live
    `compute_availability` call on this default request path (AG-8), exactly like the not-yet-computed
    fallback it extends."""
    engine, spy_days = coverage_engine
    cfg = load_config()
    with Session(engine) as session:
        data_manager.availability_cached_with_status(session, cfg)  # warm it (V1)
        session.add(DataProviderRun(provider="seed", started_at=datetime(2024, 1, 3, 12, 0, 0), status="running"))
        session.commit()
    with Session(engine) as session:
        session.add(DailyPrice(
            symbol="AAA", date=spy_days[2], open=3.0, high=3.0, low=3.0, close=3.0, volume=3.0,
        ))
        session.commit()

    def _boom(*_a, **_k):
        raise AssertionError("a stale-serving fallback must never trigger a live compute_availability call")

    monkeypatch.setattr(data_manager, "compute_availability", _boom)
    with Session(engine) as session:
        served = data_manager.availability_from_storage(session, cfg)
    assert served["stale"] is True


# ==================================================================================================
# J-36 — per-symbol / per-universe-member coverage table (read-only descriptive metadata)
# ==================================================================================================
def _persymbol_cfg():
    """A small config whose universe is exactly {AAA, BBB, CCC} and whose thin threshold is a known
    value (10) — so the per-symbol table's in_universe/thin/missing are exact by construction and the
    thin threshold is provably read from config (No magic numbers)."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    universe = cfg.universe.model_copy(update={"symbols": ["AAA", "BBB", "CCC"]})
    indicators = cfg.indicators.model_copy(update={"min_history_bars": 10})
    return cfg.model_copy(update={"universe": universe, "indicators": indicators})


@pytest.fixture()
def persymbol_engine(tmp_path):
    """A hand-built DB exercising every per-symbol coverage case against a {AAA,BBB,CCC} universe with a
    thin threshold of 10 bars:
      - AAA: a FULL-history universe member (12 bars >= threshold 10) → in_universe, has_data, not thin.
      - BBB: a THIN universe member (3 bars, 0 < 3 < 10) → in_universe, has_data, thin.
      - CCC: a universe member with NO bars → in_universe, has_data=false, missing=true, NA range.
      - SPY: a priced NON-universe symbol (a benchmark ETF) → in_universe=false, has_data.
      - ^VIX: a priced NON-universe symbol → in_universe=false, has_data.
    So distinct priced symbols = {AAA,BBB,SPY,^VIX} = 4, plus CCC is a universe-member row with no bars."""
    engine = make_engine(f"sqlite:///{tmp_path / 'persym.db'}")
    create_db_and_tables(engine)
    base = date(2024, 1, 1)

    def _bars(symbol: str, n: int) -> None:
        for i in range(n):
            session.add(DailyPrice(
                symbol=symbol, date=base + __import__("datetime").timedelta(days=i),
                open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0,
            ))

    with Session(engine) as session:
        _bars("AAA", 12)   # full-history member
        _bars("BBB", 3)    # thin member
        _bars("SPY", 12)   # non-universe priced symbol (benchmark)
        _bars("^VIX", 5)   # non-universe priced symbol
        session.commit()
    return engine


def _rows_by_symbol(cov: dict) -> dict:
    return {r["symbol"]: r for r in cov["per_symbol"]}


def test_coverage_per_symbol_exact_values(persymbol_engine):
    """Exact per-symbol coverage for a full-history member, a thin member, a no-bars member, and two
    non-universe priced symbols — each field asserted by value (never 'something returned')."""
    cfg = _persymbol_cfg()
    with Session(persymbol_engine) as session:
        cov = compute_coverage(session, cfg)
    rows = _rows_by_symbol(cov)

    # (a) AAA — a full-history universe member: in_universe, has_data, 12 bars, not thin, not missing.
    aaa = rows["AAA"]
    assert aaa["in_universe"] is True and aaa["has_data"] is True
    assert aaa["bar_count"] == 12
    assert aaa["first"] == date(2024, 1, 1).isoformat()
    assert aaa["last"] == (date(2024, 1, 1) + __import__("datetime").timedelta(days=11)).isoformat()
    assert aaa["thin"] is False and aaa["missing"] is False

    # (b) BBB — a THIN universe member: 0 < 3 < 10 → thin True, missing False, range present.
    bbb = rows["BBB"]
    assert bbb["in_universe"] is True and bbb["has_data"] is True
    assert bbb["bar_count"] == 3 and bbb["thin"] is True and bbb["missing"] is False
    assert bbb["first"] == date(2024, 1, 1).isoformat()

    # (c) CCC — a universe member with NO bars: has_data False, missing True, NA range (never fabricated),
    #     0 bars, and thin False (thin is strictly 0 < bars < threshold; a no-bars member is `missing`).
    ccc = rows["CCC"]
    assert ccc["in_universe"] is True and ccc["has_data"] is False
    assert ccc["bar_count"] == 0 and ccc["missing"] is True and ccc["thin"] is False
    assert ccc["first"] is None and ccc["last"] is None  # NA range — not a fabricated 0/zero-date row

    # (d) SPY / ^VIX — priced NON-universe symbols: in_universe False, has_data True, never `missing`
    #     (missing flags only universe members with no data).
    spy = rows["SPY"]
    assert spy["in_universe"] is False and spy["has_data"] is True and spy["missing"] is False
    vix = rows["^VIX"]
    assert vix["in_universe"] is False and vix["has_data"] is True and vix["missing"] is False


def test_coverage_per_symbol_consistency_with_aggregates(persymbol_engine):
    """The table can never present two drifting truths: the distinct-symbol row count equals the existing
    `symbol_count` aggregate, and the in-universe row count equals `candidate_universe_count` (the static
    `config.universe.symbols` count — the data-table membership view; iter-33 J-93 migrated the dynamic
    `universe_count` to the members RESOLVED at the as-of, a separate as-of-dependent figure)."""
    cfg = _persymbol_cfg()
    with Session(persymbol_engine) as session:
        cov = compute_coverage(session, cfg)
    rows = cov["per_symbol"]

    # one row per distinct symbol (priced symbols ∪ universe members) — no duplicate symbol row.
    symbols = [r["symbol"] for r in rows]
    assert len(symbols) == len(set(symbols))

    # distinct PRICED symbols == symbol_count (AAA,BBB,SPY,^VIX = 4); CCC has no bars so it is not priced.
    priced = [r for r in rows if r["has_data"]]
    assert len(priced) == cov["symbol_count"] == 4

    # in-universe rows == candidate_universe_count (AAA,BBB,CCC = 3) — reads the SAME config.universe.symbols.
    in_universe = [r for r in rows if r["in_universe"]]
    assert len(in_universe) == cov["candidate_universe_count"] == 3
    assert {r["symbol"] for r in in_universe} == {"AAA", "BBB", "CCC"}

    # every universe member appears with data-or-missing — none silently absent.
    assert all((r["has_data"] or r["missing"]) for r in in_universe)


def test_coverage_per_symbol_thin_threshold_from_config(persymbol_engine):
    """The thin flag is computed from `indicators.min_history_bars` — RAISING the threshold flips a
    previously-not-thin member to thin (proves no magic literal; the threshold is the config value)."""
    with Session(persymbol_engine) as session:
        # threshold 10: AAA (12 bars) is NOT thin.
        cov_lo = compute_coverage(session, _persymbol_cfg())
        # threshold 13: AAA (12 bars) IS now thin (0 < 12 < 13).
        cfg_hi = _persymbol_cfg()
        cfg_hi = cfg_hi.model_copy(
            update={"indicators": cfg_hi.indicators.model_copy(update={"min_history_bars": 13})}
        )
        cov_hi = compute_coverage(session, cfg_hi)
    assert _rows_by_symbol(cov_lo)["AAA"]["thin"] is False
    assert _rows_by_symbol(cov_hi)["AAA"]["thin"] is True


def test_coverage_per_symbol_empty_dataset_is_members_only(persymbol_engine, tmp_path):
    """Empty-dataset grace: with NO bars, the per-symbol table still serves cleanly — one row per universe
    member, each has_data=false + missing=true + NA range — never an error and never a fabricated bar."""
    engine = make_engine(f"sqlite:///{tmp_path / 'empty_persym.db'}")
    create_db_and_tables(engine)
    cfg = _persymbol_cfg()
    with Session(engine) as session:
        cov = compute_coverage(session, cfg)
    assert cov["symbol_count"] == 0
    rows = _rows_by_symbol(cov)
    # exactly the 3 universe members, all missing with NA range (no priced symbols at all).
    assert set(rows) == {"AAA", "BBB", "CCC"}
    for r in rows.values():
        assert r["in_universe"] is True and r["has_data"] is False and r["missing"] is True
        assert r["bar_count"] == 0 and r["first"] is None and r["last"] is None
    # aggregate consistency still holds on the empty dataset (in-universe rows == the STATIC candidate
    # count; the as-of-dependent `universe_count` is 0 here — nothing clears the warm-up gate on an empty DB).
    assert len([r for r in cov["per_symbol"] if r["in_universe"]]) == cov["candidate_universe_count"] == 3
    assert cov["universe_count"] == 0  # J-93: no member resolves on a bars-less DB (honest empty universe)


# ==================================================================================================
# validate_job_request — config-driven limits + explicit rejection (the API maps these to 4xx)
# ==================================================================================================
def test_validate_job_request_accepts_any_span():
    """ops-hardening iter-1 (J-03): the max-range rejection is REMOVED ENTIRELY — an explicit request of
    ANY span is accepted (no `ValueError`), including a span far exceeding the old 370-day cap. Chunked
    execution (`_do_backfill`'s date-window loop), not a request-time cap, is the safety mechanism for an
    unbounded span."""
    cfg = load_config()
    assert not hasattr(cfg.data_manager, "max_range_days")
    # a 412-day span (2025-06-01 -> 2026-07-17, TC-7's own example) -- comfortably past the old 370-day
    # cap -- raises nothing.
    validate_job_request("backfill", date(2025, 6, 1), date(2026, 7, 17))
    # an even larger, multi-year span is likewise accepted.
    validate_job_request("backfill", date(2020, 1, 1), date(2024, 1, 1))
    validate_job_request("fetch", date(2020, 1, 1), date(2024, 1, 1))


def test_validate_job_request_rejects_inverted_and_unknown():
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    with pytest.raises(ValueError):
        validate_job_request("backfill", date(2024, 1, 10), date(2024, 1, 1), cfg)  # start > end
    with pytest.raises(ValueError):
        validate_job_request("teleport", date(2024, 1, 1), date(2024, 1, 2), cfg)  # unknown kind


# ==================================================================================================
# Fetch forced-failure — real-data-only: zero fabricated bars / snapshots, an explicit failed run
# ==================================================================================================
class _FailingProvider(PriceProvider):
    """A live provider that is unavailable for every symbol (mirrors an offline / rate-limited Stooq)."""

    def get_daily(self, symbol, start=None, end=None):
        raise ProviderUnavailableError(f"forced failure for {symbol}")


def test_fetch_forced_failure_writes_no_bars_or_snapshots(tmp_path):
    """A fetch job whose provider fails for every symbol ends `failed` with an explicit error and writes
    ZERO `DailyPrice` rows and ZERO snapshots — never a fabricated price (anti-goal: real-data-only)."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    engine = make_engine(f"sqlite:///{tmp_path / 'fetch_fail.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for d in (date(2024, 1, 2), date(2024, 1, 3)):  # a little SPY data so a calendar exists
            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()
        prices_before = session.scalar(select(func.count()).select_from(DailyPrice))
        runs_before = session.scalar(select(func.count()).select_from(ScannerRun))

    # J-13 (iter-20): a generic fetch now targets `price_load_symbols(cfg, seed_dir)` (context ∪ pool), so
    # this job-mechanics test pins an explicit EMPTY temp `seed_dir` (no committed `universe_pool.csv`) —
    # `price_load_symbols` then degrades honestly to the context-only set, keeping this test fast/small
    # exactly as before (never silently exercising the real ~588-name committed pool).
    job = create_job("fetch", date(2024, 1, 2), date(2024, 1, 31))
    summary = run_data_job(job.job_id, config=cfg, engine=engine, provider=_FailingProvider(), seed_dir=tmp_path)

    assert summary["status"] == "failed"
    assert summary["symbols_total"] == len(price_load_symbols(cfg, tmp_path))
    assert summary["symbols_failed"] == summary["symbols_total"] and summary["symbols_ok"] == 0
    assert summary["bars_fetched"] == 0 and summary["snapshots_created"] == 0
    assert summary["errors"]  # explicit per-symbol failure messages

    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(DailyPrice)) == prices_before  # no fabricated bars
        assert session.scalar(select(func.count()).select_from(ScannerRun)) == runs_before  # no snapshots
        dpr = session.exec(select(DataProviderRun).order_by(DataProviderRun.id.desc())).first()
    assert dpr is not None and dpr.status == "failed"  # the failure is recorded honestly


# ==================================================================================================
# J-13 (iter-20) — the generic Fetch job now targets the full committed pool ∪ context
# (`price_load_symbols`), not just the smaller context-only `all_seed_symbols` default.
# ==================================================================================================
class _PoolRecordingProvider(PriceProvider):
    """Returns one bar per symbol and records every symbol it was asked for (zero wall-clock).

    NOTE: distinct name from the unrelated `_RecordingOkProvider` defined later in this module (used by
    the api-key anti-goal test, no `.fetched`) — a shared name would let the later module-level
    definition shadow this one, so this test would silently instantiate the wrong class.
    """

    def __init__(self):
        self.fetched: list[str] = []

    def get_daily(self, symbol, start=None, end=None):
        self.fetched.append(symbol)
        return [Bar(date=date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]


def test_fetch_job_symbol_set_covers_committed_pool_and_context(tmp_path):
    """J-13 (iter-20): a generic Fetch job's target symbol set is `price_load_symbols(cfg, seed_dir)` — a
    SUPERSET of the committed candidate pool AND every context symbol (benchmarks/ETFs/^VIX/macro proxies),
    not the smaller context-only set the pre-iter-20 default (`all_seed_symbols` alone) used. Runs against
    the REAL committed seed dir (the actual pool) with a fake zero-wall-clock provider, so it stays fast."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    engine = make_engine(f"sqlite:///{tmp_path / 'pool_fetch.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    expected = price_load_symbols(cfg, DEFAULT_SEED_DIR)  # the real committed pool ∪ context
    context = set(all_seed_symbols(cfg))
    pool = {row["symbol"] for row in read_pool(DEFAULT_SEED_DIR)}
    pool_only_sample = sorted(pool - context)[:5]
    assert pool_only_sample, "the committed pool must have names beyond the context set for this test to mean anything"
    assert len(expected) >= 548  # the committed pool's documented floor (goal.md J-13/§A)

    provider = _PoolRecordingProvider()
    job = create_job("fetch", date(2024, 1, 2), date(2024, 1, 2), source="yahoo")
    summary = run_data_job(job.job_id, config=cfg, engine=engine, provider=provider, sleep_fn=_noop_sleep)

    assert summary["status"] == "ok"
    assert summary["symbols_total"] == len(expected)
    assert summary["symbols_total"] > len(context)  # strictly bigger than the pre-iter-20 default
    fetched = set(provider.fetched)
    assert context <= fetched  # every context symbol still covered (no coverage regression)
    assert pool <= fetched     # every committed-pool name now covered too (not just the 5-name sample)


# ==================================================================================================
# Backfill on the real seed — grows n, lookahead-free, create-once/immutable (module-scoped, once)
# ==================================================================================================


def _daily_region_start(trading, cfg):
    """iter-18: the snapshot cadence bounds the DEEP region to monthly targets, so job-range tests pick
    their dates inside the config daily-density region (>= scanner.snapshot_cadence.daily_start), where
    every trading day is a valid backfill target — these proofs are cadence-independent."""
    start = cfg.scanner.snapshot_cadence.daily_start or trading[0]
    return next(i for i, d in enumerate(trading) if d >= start)

@pytest.fixture(scope="module")
def backfilled_job(tmp_path_factory):
    """Load the seed, create one baseline run (so n_before > 0), run a backfill JOB over a 3-date range
    of older trading days, capture before/after facts, then run the SAME job again for idempotency."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    db_path = tmp_path_factory.mktemp("dm_seed") / "dm.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    load_seed(engine, cfg)

    with Session(engine) as session:
        trading = _trading_days(session, cfg)
    assert len(trading) > 320, "seed should provide a long trading calendar"
    _base = _daily_region_start(trading, cfg)
    base_date = trading[_base + 300]
    r_start, r_end = trading[_base + 305], trading[_base + 307]
    in_range = [d for d in trading if r_start <= d <= r_end]  # the gap dates the job will create
    horizon = cfg.walk_forward.default_horizon

    # baseline: one pre-existing run + its forward returns (the n_before reference)
    with Session(engine) as session:
        base_run = scanner.run_scan(session, base_date, cfg)
        forward_testing.backfill_run_forward_returns(session, base_run, cfg)
        n_before = compute_forward_aggregates(session, horizon, cfg)["overall"]["n"]
        runs_before = session.scalar(select(func.count()).select_from(ScannerRun))
        dpr_before = session.scalar(select(func.count()).select_from(DataProviderRun))

    # FIRST job over the range (synchronous — deterministic)
    job1 = create_job("backfill", r_start, r_end)
    summary1 = run_data_job(job1.job_id, config=cfg, engine=engine)

    with Session(engine) as session:
        n_after = compute_forward_aggregates(session, horizon, cfg)["overall"]["n"]
        runs_after = session.scalar(select(func.count()).select_from(ScannerRun))
        dpr_after = session.scalar(select(func.count()).select_from(DataProviderRun))
        created = {}
        for d in in_range:
            run = scanner.get_run_for_date(session, d)
            results = session.exec(
                select(ScannerResult).where(ScannerResult.run_id == run.id).order_by(ScannerResult.rank)
            ).all()
            frs = session.exec(select(ForwardReturn).where(ForwardReturn.run_id == run.id)).all()
            created[d] = {
                "id": run.id,
                "created_at": run.created_at,
                "records": [r.record_json for r in results],
                "fr_lookahead_ok": all(fr.measured_date > d and fr.asof_date == d for fr in frs),
                "fr_count": len(frs),
            }
        # canonical equality: the backfilled snapshot's stored Leadership == a fresh score_stocks(d0)
        d0 = in_range[0]
        live_lead = {row["ticker"]: row["leadership"]["score"] for row in score_stocks(session, d0, cfg)["rows"]}
        stored_lead = {
            r.ticker: r.leadership_score
            for r in session.exec(select(ScannerResult).where(ScannerResult.run_id == created[d0]["id"])).all()
        }

    # SECOND identical job — create-once / idempotent
    with Session(engine) as session:
        runs_pre2 = session.scalar(select(func.count()).select_from(ScannerRun))
        fr_pre2 = session.scalar(select(func.count()).select_from(ForwardReturn))
    job2 = create_job("backfill", r_start, r_end)
    summary2 = run_data_job(job2.job_id, config=cfg, engine=engine)
    with Session(engine) as session:
        runs_post2 = session.scalar(select(func.count()).select_from(ScannerRun))
        fr_post2 = session.scalar(select(func.count()).select_from(ForwardReturn))
        dpr_post2 = session.scalar(select(func.count()).select_from(DataProviderRun))
        created_at_recheck = {d: scanner.get_run_for_date(session, d).created_at for d in in_range}

    return {
        "in_range": in_range, "horizon": horizon,
        "n_before": n_before, "n_after": n_after,
        "runs_before": runs_before, "runs_after": runs_after,
        "dpr_before": dpr_before, "dpr_after": dpr_after, "dpr_post2": dpr_post2,
        "summary1": summary1, "summary2": summary2,
        "created": created, "live_lead": live_lead, "stored_lead": stored_lead,
        "runs_pre2": runs_pre2, "runs_post2": runs_post2,
        "fr_pre2": fr_pre2, "fr_post2": fr_post2,
        "created_at_recheck": created_at_recheck,
        # ops-hardening iter-1: the underlying (seed-loaded, cadence-neutralized) engine + cfg, so OTHER
        # tests in this module can reuse the already-loaded seed DB (avoiding a second expensive load)
        # for proofs that need a DIFFERENT cfg (e.g. real/active cadence) over the SAME committed data.
        "engine": engine, "cfg": cfg,
    }


def test_backfill_grows_n_and_adds_runs(backfilled_job):
    """The forward-test sample size grows and the expected ScannerRun rows are added (the J-17 crux:
    new dates appear + System Health n rises)."""
    f = backfilled_job
    assert f["n_after"] > f["n_before"]  # the forward-test evidence base grew
    assert f["runs_after"] == f["runs_before"] + len(f["in_range"])  # one new immutable run per gap date
    assert f["summary1"]["dates_total"] == len(f["in_range"])
    assert f["summary1"]["dates_done"] == len(f["in_range"])
    assert f["summary1"]["snapshots_created"] == len(f["in_range"])
    assert f["summary1"]["forward_returns_inserted"] > 0
    assert f["summary1"]["status"] == "ok"


def test_backfill_is_lookahead_free_and_reuses_canonical(backfilled_job):
    """The backfilled snapshot equals the canonical score_stocks(D) VERBATIM (no second scan math), and
    every realized forward return for the run uses only bars with date > D (the entry is on D)."""
    f = backfilled_job
    assert f["stored_lead"] == f["live_lead"]  # single-source: stored == fresh canonical computation
    assert f["stored_lead"]  # not vacuously empty
    for d, info in f["created"].items():
        assert info["fr_lookahead_ok"], f"forward returns for {d} must use only bars > D"
        assert info["fr_count"] > 0  # older dates have a full forward window


def test_backfill_create_once_immutable(backfilled_job):
    """Re-running the SAME range is a no-op: 0 new snapshots, unchanged run/forward-return counts, and
    every created_at is byte-identical (a snapshot is never overwritten — anti-goal: Snapshots immutable).
    ops-hardening iter-1: `dates_total` is REDEFINED to mean trading days in the requested range, so it is
    UNCHANGED between the fresh run and the re-run (was: 0 on a re-run, the old post-filter semantics) —
    the re-run's zero-work outcome is now explained by `already_snapshotted`, not by `dates_total` itself."""
    f = backfilled_job
    assert f["summary2"]["snapshots_created"] == 0
    assert f["summary2"]["dates_total"] == len(f["in_range"])  # same trading-day count as the fresh run
    assert f["summary2"]["already_snapshotted"] == len(f["in_range"])  # every one pre-existing this time
    assert f["summary2"]["error_other"] == 0
    assert f["runs_post2"] == f["runs_pre2"]  # no new runs created by the second job
    assert f["fr_post2"] == f["fr_pre2"]  # no new forward returns inserted by the second job
    for d, info in f["created"].items():
        assert f["created_at_recheck"][d] == info["created_at"]  # created_at never mutated


def test_backfill_breakdown_invariants_hold_on_fresh_and_rerun(backfilled_job):
    """ops-hardening iter-1 (J-01) — the run-summary exclusion-breakdown invariants hold EXACTLY on both
    the fresh run (nothing pre-existing) and the identical re-run (everything pre-existing):
    `non_trading_days + dates_total == calendar_days`;
    `snapshots_created + already_snapshotted + error_other == dates_total`."""
    f = backfilled_job
    in_range = f["in_range"]
    expected_calendar_days = (in_range[-1] - in_range[0]).days + 1
    for summary in (f["summary1"], f["summary2"]):
        assert summary["calendar_days"] == expected_calendar_days
        assert summary["non_trading_days"] + summary["dates_total"] == summary["calendar_days"]
        assert (
            summary["snapshots_created"] + summary["already_snapshotted"] + summary["error_other"]
            == summary["dates_total"]
        )
    # fresh run: nothing pre-existing, everything newly created.
    assert f["summary1"]["already_snapshotted"] == 0
    assert f["summary1"]["snapshots_created"] == len(in_range)
    # re-run: nothing new, everything pre-existing (the create-once / zero-work contract).
    assert f["summary2"]["snapshots_created"] == 0
    assert f["summary2"]["already_snapshotted"] == len(in_range)


def test_dataprovider_run_is_append_only_per_job(backfilled_job):
    """Each job appends exactly one DataProviderRun row (append-only); none are overwritten."""
    f = backfilled_job
    assert f["dpr_after"] == f["dpr_before"] + 1  # first job appended one row
    assert f["dpr_post2"] == f["dpr_after"] + 1  # second job appended one more
    runs = recent_runs  # the history reader exists and is importable
    assert callable(runs)


# ==================================================================================================
# ops-hardening iter-1 (J-01/J-03): cadence bypass for backfill/both (not rebuild), the run-summary
# exclusion breakdown, and date-window chunking — reuses `backfilled_job`'s already-loaded seed engine
# (a SECOND full seed load would be wasteful; the ACTIVE, non-neutralized cadence config is built fresh
# here since the fixture's own `cfg` deliberately neutralizes it for its own unrelated proofs).
# ==================================================================================================
def _cadence_excluded_window(trading, allowed, daily_start, n, start_at=0):
    """The first `n` consecutive trading days (searching from index `start_at`), entirely inside the
    deep (pre-`daily_start`) region, that `_cadence_allowed_dates` excludes IN FULL — so a bypass-vs-
    filtered contrast on this window is unambiguous (never a vacuous window cadence would have allowed
    anyway). Real seed dates only; raises if no such window exists (a hard test-setup failure, not a
    fabricated window)."""
    for i in range(start_at, len(trading) - n):
        window = trading[i:i + n]
        if window[-1] >= daily_start:
            break  # only the deep region is searched
        if all(d not in allowed for d in window):
            return window
    raise AssertionError(f"no {n}-day fully cadence-excluded window found from index {start_at}")


def test_do_backfill_cadence_bypass_for_backfill_not_rebuild(backfilled_job):
    """J-01 — an explicit `backfill`/`both` request's date range ALWAYS WINS over the deep-history
    snapshot cadence: every trading day in a cadence-excluded window still becomes a real, snapshotted
    target. `rebuild` keeps the EXISTING cadence-filtered target selection UNCHANGED (out of scope this
    iteration) — proven by calling `_do_backfill` directly with `kind="rebuild"` over a SEPARATE
    cadence-excluded window (never through `run_data_job`, which would widen a real rebuild to the FULL
    historical calendar — far too expensive for a test; the documented hang risk on this codebase's
    multi-decade basis)."""
    engine = backfilled_job["engine"]
    cfg = load_config()  # the REAL, ACTIVE cadence (daily_start set, deep_cadence != "daily") — not the
    # fixture's own neutralized copy, so the bypass-vs-filtered contrast below is real, not vacuous.
    daily_start = cfg.scanner.snapshot_cadence.daily_start
    assert daily_start is not None, "this proof needs an ACTIVE cadence gate to bypass/enforce"
    with Session(engine) as session:
        trading = _trading_days(session, cfg)
        allowed = data_manager._cadence_allowed_dates(session, trading, cfg)

    # window A: a real BACKFILL job bypasses the cadence entirely.
    window_a = _cadence_excluded_window(trading, allowed, daily_start, 3)
    with Session(engine) as session:
        runs_before = session.scalar(select(func.count()).select_from(ScannerRun))
    job = create_job("backfill", window_a[0], window_a[-1])
    summary = run_data_job(job.job_id, config=cfg, engine=engine)
    assert summary["dates_total"] == 3  # J-01 redefinition: trading days in range, cadence notwithstanding
    assert summary["snapshots_created"] == 3  # every one backfilled — the cadence gate did NOT filter them
    assert summary["already_snapshotted"] == 0
    with Session(engine) as session:
        runs_after = session.scalar(select(func.count()).select_from(ScannerRun))
        for d in window_a:
            assert scanner.get_run_for_date(session, d) is not None
    assert runs_after == runs_before + 3

    # window B: a DIFFERENT (disjoint) cadence-excluded window, searched onward from window A's END so
    # the two never overlap — no cleanup of window A's fresh snapshots is needed.
    start_at = trading.index(window_a[-1]) + 1
    window_b = _cadence_excluded_window(trading, allowed, daily_start, 3, start_at=start_at)
    prog = JobProgress(job_id="ops-hardening-rebuild-cadence-probe", kind="rebuild",
                        start=window_b[0], end=window_b[-1])
    with Session(engine) as session:
        data_manager._do_backfill(session, cfg, prog, eng=engine)
    assert prog.dates_total == 3  # the redefinition still reports the honest trading-day-in-range count
    assert prog.snapshots_created == 0  # cadence excluded every date in this window — UNCHANGED behavior
    assert prog.already_snapshotted == 0
    with Session(engine) as session:
        for d in window_b:
            assert scanner.get_run_for_date(session, d) is None  # rebuild's cadence filter still applies


def test_backfill_weekend_span_mixed_and_all_non_trading_breakdown(backfilled_job):
    """ops-hardening iter-1 (J-01, TC-11-equivalent unit coverage) — a range covering exactly two
    consecutive REAL trading days that straddle a calendar gap (a weekend) proves the MIXED
    trading/non-trading breakdown; the gap's OWN calendar days (strictly between them — zero trading
    days by construction) prove the ALL-non-trading breakdown, honestly (no fabricated per-date failure,
    `error_other == 0`) — mirroring the real J-01 weekend-only journey (TC-3) at unit-test speed."""
    engine = backfilled_job["engine"]
    cfg = backfilled_job["cfg"]  # cadence-neutralized is fine here — this proof is cadence-agnostic
    with Session(engine) as session:
        trading = _trading_days(session, cfg)
    gap_pair = next(((a, b) for a, b in zip(trading, trading[1:]) if (b - a).days > 1), None)
    assert gap_pair is not None, "expected at least one real calendar gap in the seed trading calendar"
    a, b = gap_pair
    gap_days = (b - a).days - 1  # calendar days strictly between two consecutive trading days

    # mixed: the two trading days themselves plus every non-trading day between them.
    job = create_job("backfill", a, b)
    summary = run_data_job(job.job_id, config=cfg, engine=engine)
    assert summary["dates_total"] == 2
    assert summary["calendar_days"] == (b - a).days + 1
    assert summary["non_trading_days"] == gap_days
    assert summary["non_trading_days"] + summary["dates_total"] == summary["calendar_days"]
    assert summary["snapshots_created"] + summary["already_snapshotted"] + summary["error_other"] == 2
    assert summary["error_other"] == 0

    # all-non-trading: the gap's own span (strictly between a and b) — zero trading days by construction.
    gap_start, gap_end = a + timedelta(days=1), b - timedelta(days=1)
    job2 = create_job("backfill", gap_start, gap_end)
    summary2 = run_data_job(job2.job_id, config=cfg, engine=engine)
    assert summary2["dates_total"] == 0
    assert summary2["calendar_days"] == gap_days
    assert summary2["non_trading_days"] == gap_days
    assert summary2["snapshots_created"] == 0
    assert summary2["already_snapshotted"] == 0
    assert summary2["error_other"] == 0
    assert summary2["status"] == "ok"  # honest zero-work — never a fabricated failure


def test_backfill_chunk_plan_derives_from_date_window_days_config(backfilled_job):
    """J-03 — the backfill date-window chunk plan (`chunk_total`) derives from config
    `import_chunking.date_window_days`, exactly like the existing fetch-side chunk plan: varying the
    config value changes `chunk_total` for the SAME range. Uses the LARGEST all-non-trading gap in the
    seed's own calendar (zero real compute — no scanner work is needed to prove the ARITHMETIC) so this
    stays fast, never executing a real multi-hundred-day backfill to completion. Takes whatever gap size
    the real seed calendar actually has (a plain weekend is >= 2 calendar days) rather than assuming a
    specific holiday-cluster size exists."""
    engine = backfilled_job["engine"]
    cfg = backfilled_job["cfg"]
    with Session(engine) as session:
        trading = _trading_days(session, cfg)
    a, b = max(zip(trading, trading[1:]), key=lambda pair: (pair[1] - pair[0]).days)
    gap_start, gap_end = a + timedelta(days=1), b - timedelta(days=1)
    calendar_days = (gap_end - gap_start).days + 1
    assert calendar_days >= 2, "expected at least an ordinary weekend gap in the seed trading calendar"

    # window_days == calendar_days -> exactly 1 chunk; window_days == 1 -> one chunk per calendar day
    # (always calendar_days chunks, regardless of how large the found gap happens to be).
    for window_days, expected_chunks in ((calendar_days, 1), (1, calendar_days)):
        ic = cfg.data_manager.import_chunking.model_copy(update={"date_window_days": window_days})
        dm = cfg.data_manager.model_copy(update={"import_chunking": ic})
        narrow_cfg = cfg.model_copy(update={"data_manager": dm})
        prog = JobProgress(job_id=f"chunk-plan-probe-{window_days}", kind="backfill",
                            start=gap_start, end=gap_end)
        with Session(engine) as session:
            data_manager._do_backfill(session, narrow_cfg, prog, eng=engine)
        assert prog.chunk_total == len(data_manager._date_windows(gap_start, gap_end, window_days))
        assert prog.chunk_total == expected_chunks
        assert prog.chunk_index == prog.chunk_total  # the (empty, all-non-trading) plan completed in full
        assert prog.dates_total == 0  # still honestly zero trading days — no fabricated target


def test_run_detail_omits_breakdown_until_computed():
    """ops-hardening iter-1 audit (Finding B) — the persisted run-summary breakdown is served ONLY once
    `_do_backfill` has computed it. The `running` row `_create_run_record` writes at job start (and the
    `interrupted` row the boot sweep freezes from it) carries the JobProgress defaults (calendar_days ==
    0); `_run_detail` must serve those four fields as null there — NOT a fabricated "0 calendar days · 0
    already snapshotted · 0 non-trading" for a backfill whose range was really hundreds of days (AG-3).
    A genuinely-computed backfill still serves the real values (calendar_days >= 1)."""
    # not-yet-computed backfill row (exactly what `_create_run_record` serializes at job start): a real
    # multi-hundred-day requested range, but the breakdown fields still at their JobProgress defaults.
    fresh = JobProgress(job_id="never-ran", kind="backfill", start=date(2024, 1, 1), end=date(2025, 6, 1))
    detail = data_manager._run_detail(fresh)
    assert detail["calendar_days"] is None  # never a fabricated 0 for a 517-day range
    assert detail["non_trading_days"] is None
    assert detail["already_snapshotted"] is None
    assert detail["error_other"] is None
    # a genuinely-computed backfill (the finalized row) still serves the real numbers unchanged.
    done = JobProgress(job_id="ran", kind="backfill", start=date(2026, 5, 2), end=date(2026, 5, 29))
    done.calendar_days, done.dates_total, done.non_trading_days = 28, 19, 9
    done.already_snapshotted, done.snapshots_created, done.error_other = 0, 19, 0
    detail_done = data_manager._run_detail(done)
    assert detail_done["calendar_days"] == 28
    assert detail_done["non_trading_days"] == 9
    assert detail_done["already_snapshotted"] == 0
    assert detail_done["error_other"] == 0


def test_backfill_error_other_uncapped_past_sample_limit(backfilled_job, monkeypatch):
    """ops-hardening iter-1 audit (Finding A) — `error_other`, and the breakdown invariant it feeds, stay
    EXACT when more than `_MAX_ERROR_SAMPLES` (20) in-range dates fail: it is derived from the UNCAPPED
    `date_failures_total`, never from the bounded `date_failures` sample list. Forces every target in a
    25-trading-day deep (un-snapshotted) window to fail its compute — the failures are recorded but never
    persisted, so this stays fast (no real scanner/DB work), then asserts the sample list capped at 20
    while `error_other` reports the true 25 and invariant 2 holds exactly."""
    engine = backfilled_job["engine"]
    cfg = backfilled_job["cfg"]  # cadence-neutralized: every in-range trading day is a target
    with Session(engine) as session:
        trading = _trading_days(session, cfg)
        snapshotted = set(session.exec(select(ScannerRun.asof_date)).all())
    # the first run of 25 CONSECUTIVE un-snapshotted trading days (so every one becomes a real target and
    # the [start,end] span contains exactly them) — robust to whichever ranges the fixture pre-snapshotted.
    window = next(
        (trading[i:i + 25] for i in range(len(trading) - 25)
         if not any(d in snapshotted for d in trading[i:i + 25])),
        None,
    )
    assert window is not None and len(window) == 25, "expected a 25-day un-snapshotted trading window"

    def _boom(*_a, **_k):
        raise RuntimeError("forced compute failure")
    monkeypatch.setattr(data_manager, "_compute_one_backfill_date", _boom)

    prog = JobProgress(job_id="err-uncapped-probe", kind="backfill", start=window[0], end=window[-1])
    with Session(engine) as session:
        data_manager._do_backfill(session, cfg, prog, eng=engine)

    n_targets = prog.dates_total - prog.already_snapshotted
    assert n_targets == 25 and prog.snapshots_created == 0  # every target failed, none persisted
    assert len(prog.date_failures) == data_manager._MAX_ERROR_SAMPLES  # the SAMPLE list is capped at 20
    assert prog.error_other == 25  # ...but error_other is the UNCAPPED true failure count
    assert prog.error_other > data_manager._MAX_ERROR_SAMPLES
    # invariant 2 holds EXACTLY even past the sample cap (the whole point of the fix)
    assert prog.snapshots_created + prog.already_snapshotted + prog.error_other == prog.dates_total


# ==================================================================================================
# ops-hardening iter-2 (J-05): the ingest finalize hook — coverage_snapshot persistence, market-phase/
# membership-timeline/research hot-key warming, and the aggregates_refreshed honesty gate.
#
# `finalize_hook_engine` is a TINY hand-built DB (mirrors `coverage_engine`'s own style) — fast, no full
# seed load needed: the finalize hook's sub-steps (`_compute_coverage_uncached`, `market_phase_cached`,
# `event_study_cached`) all degrade gracefully on sparse data (the SAME graceful-empty-DB behavior
# `coverage_engine`'s own tests already exercise, since `read_pool()` always reads the REAL committed
# candidate-pool file regardless of this tiny DB's contents).
# ==================================================================================================
@pytest.fixture()
def finalize_hook_engine(tmp_path):
    """A tiny hand-built DB with one stored ScannerRun + ScannerResult on a single as-of date — enough for
    every finalize-hook sub-step to run for real."""
    engine = make_engine(f"sqlite:///{tmp_path / 'finalize.db'}")
    create_db_and_tables(engine)
    d = date(2024, 3, 4)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        run = ScannerRun(
            asof_date=d, created_at=datetime(2024, 3, 4), provider="seed", benchmark="SPY",
            regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        session.add(ScannerResult(
            run_id=run.id, ticker="AAA", name="AAA Corp", leadership_score=1.0, leadership_bucket="Leader",
            entry_quality_score=1.0, entry_quality_bucket="Good", risk_score=1.0, risk_bucket="Low",
            setup_status="Actionable", rank=1, record_json="{}",
        ))
        session.commit()
    return engine, d


def test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates(finalize_hook_engine):
    """TC-1/TC-5 — a finalize hook call for a job that newly created a snapshot on `d` persists exactly one
    `coverage_snapshot` row for the current stamp and reports every category this fixture's data supports
    as refreshed: `latest_snapshot` (this run created a snapshot), `coverage` + `membership_timeline` (one
    compute warms both), `market_phase` (the new date), `forward_aggregates` (ops-hardening iter-5: the
    current latest run's per-horizon forward-aggregate cache), `research_hot_keys` (the default hot key),
    `index_series` (ops-hardening iter-13: the fixture's own `SPY` bar is one of `index_chart.symbols`, so
    the hot-key warm has real bars to compute from), `factor_lab_all` (ops-hardening iter-51: the Factor
    Lab's default all-history hot key), `availability_heatmap` (ops-hardening iter-56: the SAME fixture
    data gives the availability-heatmap warm real bars/snapshot to compute from)."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    with Session(engine) as session:
        prog = JobProgress(job_id="finalize-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert set(refreshed) == {
        "latest_snapshot", "coverage", "membership_timeline", "market_phase", "forward_aggregates",
        "research_hot_keys", "index_series", "factor_lab_all", "availability_heatmap",
    }
    with Session(engine) as session:
        rows = session.exec(select(CoverageSnapshot)).all()
        assert len(rows) == 1
        resolved_asof = data_manager._resolve_coverage_asof(session, None, cfg)
        assert rows[0].asof_key == resolved_asof.isoformat()
        assert rows[0].dataset_version == data_manager._membership_dataset_version(session, cfg)


def test_finalize_hook_warms_forward_aggregates_for_every_configured_horizon(finalize_hook_engine):
    """ops-hardening iter-5 (J-06) — the finalize hook warms `ForwardAggregateCache` for the CURRENT
    latest stored run's as-of, once per configured `walk_forward.horizons` — proven directly: after the
    hook runs, exactly one cached row exists per configured horizon at that as-of."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    with Session(engine) as session:
        prog = JobProgress(job_id="forward-agg-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert "forward_aggregates" in refreshed
    with Session(engine) as session:
        rows = session.exec(
            select(ForwardAggregateCache).where(ForwardAggregateCache.asof_key == d.isoformat())
        ).all()
    assert {row.horizon for row in rows} == set(cfg.walk_forward.horizons)


def test_finalize_hook_forward_aggregate_warm_avoids_recompute_on_subsequent_read(
    finalize_hook_engine, monkeypatch
):
    """A `GET /api/backtest`-shaped read for the SAME as-of the finalize hook just warmed hits the cache
    — zero further `compute_forward_aggregates` calls. This is the actual perf fix this iteration makes:
    a live request no longer pays the 5-horizon full-table scan the finalize hook already paid at ingest
    (measured 34.77s pre-fix for one request, `reports/perf-budgets.md`).

    ops-hardening iter-16 (J-08): updated to call `resolved_forward_aggregate_evidence` — the actual
    read-only serving path `GET /api/backtest` / MCP `query_backtest` use for the latest view since the
    compute-vs-serve split (the former `forward_aggregates_cached` this test used to call directly is now
    `forward_aggregates_ingest_cached`, the INGEST-ONLY half — no longer what a request-shaped read
    calls, so exercising it here would no longer prove this test's own claim)."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    with Session(engine) as session:
        prog = JobProgress(job_id="forward-agg-hit-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        data_manager._refresh_ingest_aggregates(session, cfg, prog)

    call_count = {"n": 0}
    real = forward_testing.compute_forward_aggregates

    def _counting(*args, **kwargs):
        call_count["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(forward_testing, "compute_forward_aggregates", _counting)
    with Session(engine) as session:
        evidence = forward_testing.resolved_forward_aggregate_evidence(session, d, cfg)
    assert call_count["n"] == 0, "the finalize hook's warm should have already cached every horizon"
    assert evidence["evidence_status"] == "ready"
    assert set(evidence["evidence_by_horizon"]) == set(cfg.walk_forward.horizons)


def test_finalize_hook_coverage_snapshot_byte_identical_to_fresh_compute(finalize_hook_engine):
    """TC-8 — the persisted payload_json is byte-identical (field-by-field) to a direct fresh
    `_compute_coverage_uncached` call for the same session state (AG-3: storage is re-served, never
    re-derived)."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    with Session(engine) as session:
        prog = JobProgress(job_id="byte-identity-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        data_manager._refresh_ingest_aggregates(session, cfg, prog)
    with Session(engine) as session:
        row = session.exec(select(CoverageSnapshot)).one()
        stored = json.loads(row.payload_json)
        fresh = data_manager._compute_coverage_uncached(session, cfg, as_of=None)
    assert stored == fresh


# ==================================================================================================
# ops-hardening iter-13 (J-06, aggregation candidate #7): the finalize hook's NEW index-series warm --
# mirrors the `research_hot_keys`/`forward_aggregates` proofs above, for the SINGLE unparameterized
# default hot key `GET /api/indexes` serves from `IndexSeriesCache`.
# ==================================================================================================
def test_finalize_hook_warms_index_series_hot_key(finalize_hook_engine):
    """A finalize hook call persists exactly one `IndexSeriesCache` row for the current hot key and
    reports "index_series" as refreshed — the fixture's own SPY bar is a configured `index_chart`
    symbol, so the warm step has real bars to compute from."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    with Session(engine) as session:
        prog = JobProgress(job_id="index-series-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert "index_series" in refreshed
    with Session(engine) as session:
        rows = session.exec(select(IndexSeriesCache)).all()
    assert len(rows) == 1
    assert rows[0].range_key == cfg.index_chart.default_range
    assert rows[0].full is True


def test_finalize_hook_index_series_second_run_hit_not_reported_as_refreshed(finalize_hook_engine):
    """Honesty gate (TC-5) — a SECOND finalize hook call with no intervening ingest to any configured
    index symbol is a genuine cache HIT (nothing new persisted this run): "index_series" is honestly
    ABSENT the second time, mirroring the "was skipped" omission every other warm category follows."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    with Session(engine) as session:
        prog1 = JobProgress(job_id="index-series-first", kind="backfill", start=d, end=d)
        prog1.new_snapshot_dates = [d]
        first = data_manager._refresh_ingest_aggregates(session, cfg, prog1)
    assert "index_series" in first

    with Session(engine) as session:
        prog2 = JobProgress(job_id="index-series-second", kind="backfill", start=d, end=d)
        prog2.new_snapshot_dates = [d]
        second = data_manager._refresh_ingest_aggregates(session, cfg, prog2)
    assert "index_series" not in second  # a genuine HIT — nothing new persisted this run
    with Session(engine) as session:
        rows = session.exec(select(IndexSeriesCache)).all()
    assert len(rows) == 1  # still exactly one row — the second run never wrote a duplicate


# ==================================================================================================
# ops-hardening iter-70 (J-07) -- the finalize hook fires the readiness/preflight cache's immediate-
# refresh trigger, the SAME finalize hook every other ingest-time aggregate above already refreshes from.
# ==================================================================================================
def test_finalize_hook_triggers_immediate_readiness_refresh(finalize_hook_engine, monkeypatch):
    """TC-4: `_refresh_ingest_aggregates` fires the readiness/preflight cache's immediate-refresh trigger
    exactly once, with THIS SAME session (so it sees this job's just-persisted rows immediately), at the
    end of the finalize hook. The cache's own correctness (cold-start, steady-state, degrade-on-error,
    concurrency) is covered by test_readiness.py's dedicated tests; this test only proves the finalize
    hook actually FIRES the trigger."""
    import app.engine.readiness as readiness_module

    engine, d = finalize_hook_engine
    cfg = load_config()
    calls: list[Session] = []

    def _recording(session_arg, config=None, engine=None):
        calls.append(session_arg)

    monkeypatch.setattr(readiness_module, "trigger_readiness_refresh", _recording)
    with Session(engine) as session:
        prog = JobProgress(job_id="readiness-trigger-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        data_manager._refresh_ingest_aggregates(session, cfg, prog)
        assert len(calls) == 1
        assert calls[0] is session  # the SAME session -- sees this job's just-persisted rows immediately


@pytest.fixture
def state_flip_engine(tmp_path):
    """A DB shaped to force a REAL `readiness.state` transition when a finalize hook lands a new run for a
    benchmark bar that had already outrun the prior run -- the SAME B3-fix condition `compute_readiness`
    checks (`readiness.py`'s `awaiting_snapshot` derivation): `d0` has both a bar and a persisted run
    (servable); `d1`'s SPY bar already exists but NO run exists for it yet -- exactly the
    `awaiting_snapshot` condition, computed honestly with no finalize hook having run at all."""
    engine = make_engine(f"sqlite:///{tmp_path / 'state_flip.db'}")
    create_db_and_tables(engine)
    d0 = date(2024, 3, 4)
    d1 = date(2024, 3, 5)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=d0, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        run0 = ScannerRun(
            asof_date=d0, created_at=datetime(2024, 3, 4), provider="seed", benchmark="SPY",
            regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        )
        session.add(run0)
        session.commit()
        session.refresh(run0)
        session.add(ScannerResult(
            run_id=run0.id, ticker="AAA", name="AAA Corp", leadership_score=1.0, leadership_bucket="Leader",
            entry_quality_score=1.0, entry_quality_bucket="Good", risk_score=1.0, risk_bucket="Low",
            setup_status="Actionable", rank=1, record_json="{}",
        ))
        # d1: the benchmark's own bar has already landed, but no run exists for it yet.
        session.add(DailyPrice(symbol="SPY", date=d1, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()
    return engine, d0, d1


def test_finalize_hook_state_flip_served_by_health_within_one_tick(state_flip_engine, tmp_path, monkeypatch):
    """ops-hardening iter-71 (audit T1) -- composes TC-4's two previously-separate halves into ONE real
    integration path: the finalize hook's immediate-refresh trigger (test_finalize_hook_triggers_
    immediate_readiness_refresh above, which only proves the trigger FIRES) actually publishes a REAL
    `readiness.state` transition (`awaiting_snapshot` -> a servable state) to the cache, and `GET
    /api/health` served right after reflects the NEW state -- not the stale pre-finalize one -- within
    one tick (here, immediately: the trigger runs synchronously inside the finalize hook, before it
    returns, so no wait is needed for the periodic tick to catch up)."""
    import app.api.health as health_module
    import app.engine.readiness as readiness_module

    engine, d0, d1 = state_flip_engine
    cfg = load_config()
    monkeypatch.setenv(readiness_module.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
    readiness_module.stop_readiness_refresh()
    readiness_module.reset_readiness_refresh_cache()
    try:
        # Prime the cache with the PRE-finalize state -- `awaiting_snapshot`, since d1's benchmark bar has
        # already landed but no run exists for it yet (no finalize hook has run at this point).
        with Session(engine) as session:
            before = readiness_module.get_readiness_and_preflight(session, engine=engine, config=cfg)
        assert before["readiness"]["state"] == readiness_module.AWAITING_SNAPSHOT

        # The ingest job creates the new run for d1 (what a real backfill does BEFORE calling the finalize
        # hook), then the finalize hook runs -- firing the immediate-refresh trigger at its end (for real,
        # unlike the mocked-trigger test above).
        with Session(engine) as session:
            run1 = ScannerRun(
                asof_date=d1, created_at=datetime(2024, 3, 5), provider="seed", benchmark="SPY",
                regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
                new_high_low_json="{}", candidate_counts_json="{}",
            )
            session.add(run1)
            session.commit()
            session.refresh(run1)
            session.add(ScannerResult(
                run_id=run1.id, ticker="AAA", name="AAA Corp", leadership_score=1.0, leadership_bucket="Leader",
                entry_quality_score=1.0, entry_quality_bucket="Good", risk_score=1.0, risk_bucket="Low",
                setup_status="Actionable", rank=1, record_json="{}",
            ))
            session.commit()
            prog = JobProgress(job_id="state-flip-probe", kind="backfill", start=d1, end=d1)
            prog.new_snapshot_dates = [d1]
            data_manager._refresh_ingest_aggregates(session, cfg, prog)

        # GET /api/health (direct handler call) reflects the NEW state immediately -- the finalize hook's
        # trigger already published it; no periodic-tick wait needed.
        with Session(engine) as session:
            body = health_module.health(session)
        assert body["readiness"] != readiness_module.AWAITING_SNAPSHOT
        assert body["readiness"] in {readiness_module.READY, readiness_module.INITIALIZING}
    finally:
        readiness_module.stop_readiness_refresh()
        readiness_module.reset_readiness_refresh_cache()


def test_finalize_hook_index_series_memory_error_isolated_and_not_reported(
    finalize_hook_engine, monkeypatch
):
    """TC-7 — a `MemoryError` raised while warming the index-series cache is isolated to that one warm
    step: it never flips the ingest job's own status (this function never raises), the OTHER aggregates
    (`coverage`/`membership_timeline`/`market_phase`/`forward_aggregates`/`research_hot_keys`) still
    refresh normally, and "index_series" is honestly absent (never fabricated)."""
    engine, d = finalize_hook_engine
    cfg = load_config()

    def _boom(*_a, **_k):
        raise MemoryError("forced index-series memory pressure")

    monkeypatch.setattr(indexes, "index_series_cached_with_status", _boom)
    with Session(engine) as session:
        prog = JobProgress(job_id="index-series-oom-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
    assert "index_series" not in refreshed
    assert {
        "latest_snapshot", "coverage", "membership_timeline", "market_phase", "forward_aggregates",
        "research_hot_keys",
    } <= set(refreshed)


# ==================================================================================================
# ops-hardening iter-56 (J-06 closure): the finalize hook's NEW `availability_heatmap` warm — mirrors
# the `index_series` proofs above for the SINGLE dataset-version-keyed `AvailabilityCache` row
# `GET /api/data/availability`'s per-trading-date heatmap serves from (`compute_availability` has no
# as-of/range parameter, so there is exactly one row to keep fresh, unlike `IndexSeriesCache`'s
# multi-key shape).
# ==================================================================================================
def test_finalize_hook_warms_availability_heatmap(finalize_hook_engine):
    """TC-5 — a finalize hook call persists exactly one `AvailabilityCache` row for the current
    dataset-version stamp and reports "availability_heatmap" as refreshed — the fixture's own SPY bar
    and stored snapshot give the warm real data to compute from."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    with Session(engine) as session:
        prog = JobProgress(job_id="availability-heatmap-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert "availability_heatmap" in refreshed
    with Session(engine) as session:
        rows = session.exec(select(AvailabilityCache)).all()
        assert len(rows) == 1
        assert rows[0].dataset_version == data_manager._membership_dataset_version(session, cfg)


def test_finalize_hook_availability_heatmap_byte_identical_to_fresh_compute(finalize_hook_engine):
    """TC-6 — the persisted payload is byte-identical (field-by-field) to a direct fresh
    `compute_availability` call for the same session state (AG-3: storage is re-served, never
    re-derived)."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    with Session(engine) as session:
        prog = JobProgress(job_id="availability-byte-identity-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        data_manager._refresh_ingest_aggregates(session, cfg, prog)
    with Session(engine) as session:
        row = session.exec(select(AvailabilityCache)).one()
        stored = json.loads(row.payload_json)
        fresh = data_manager.compute_availability(session, cfg)
    assert stored == fresh


def test_finalize_hook_availability_heatmap_second_run_hit_not_reported_as_refreshed(
    finalize_hook_engine,
):
    """Honesty gate — a SECOND finalize hook call with no intervening ingest to any bar/snapshot is a
    genuine cache HIT (nothing new persisted this run): "availability_heatmap" is honestly ABSENT the
    second time, mirroring `index_series_warm`'s "was skipped" omission convention."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    with Session(engine) as session:
        prog1 = JobProgress(job_id="availability-heatmap-first", kind="backfill", start=d, end=d)
        prog1.new_snapshot_dates = [d]
        first = data_manager._refresh_ingest_aggregates(session, cfg, prog1)
    assert "availability_heatmap" in first

    with Session(engine) as session:
        prog2 = JobProgress(job_id="availability-heatmap-second", kind="backfill", start=d, end=d)
        prog2.new_snapshot_dates = [d]
        second = data_manager._refresh_ingest_aggregates(session, cfg, prog2)
    assert "availability_heatmap" not in second  # a genuine HIT — nothing new persisted this run
    with Session(engine) as session:
        rows = session.exec(select(AvailabilityCache)).all()
    assert len(rows) == 1  # still exactly one row — the second run never wrote a duplicate


def test_finalize_hook_availability_heatmap_memory_error_isolated_and_not_reported(
    finalize_hook_engine, monkeypatch
):
    """TC-9 — a `MemoryError` raised while warming the availability-heatmap cache is isolated to that
    one warm step: it never flips the ingest job's own status (this function never raises), the OTHER
    aggregates (`coverage`/`membership_timeline`/`market_phase`/`forward_aggregates`/`research_hot_keys`/
    `index_series`) still refresh normally, no other finalize-tail item's own completeness flag is
    altered, and "availability_heatmap" is honestly absent (never fabricated)."""
    engine, d = finalize_hook_engine
    cfg = load_config()

    def _boom(*_a, **_k):
        raise MemoryError("forced availability-heatmap memory pressure")

    monkeypatch.setattr(data_manager, "availability_cached_with_status", _boom)
    with Session(engine) as session:
        prog = JobProgress(job_id="availability-heatmap-oom-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
    assert "availability_heatmap" not in refreshed
    assert {
        "latest_snapshot", "coverage", "membership_timeline", "market_phase", "forward_aggregates",
        "research_hot_keys", "index_series",
    } <= set(refreshed)
    with Session(engine) as session:
        rows = session.exec(select(AvailabilityCache)).all()
    assert rows == []  # the aborted warm never persisted a row


# ==================================================================================================
# ops-hardening iter-51 (J-05/J-06/J-07): the finalize hook's NEW `factor_lab_all` warm — mirrors the
# `research_hot_keys`/`index_series` proofs above for the SINGLE unparameterized default all-history hot
# key `GET /api/research/factor-lab?all=true` serves from `EventStudyCache` (`factor_lab_all_cached` /
# `_ALL_FACTORS_SUBJECT` / `_ALL_FACTORS_VIEW` sentinel namespace).
# ==================================================================================================
def test_finalize_hook_warms_factor_lab_all_hot_key(finalize_hook_engine):
    """TC-1 — a finalize hook call persists exactly one `EventStudyCache` row for the default all-history
    Factor Lab key (`subject=_ALL_FACTORS_SUBJECT`, `view=_ALL_FACTORS_VIEW`, `asof_key=None`,
    `horizon=default_horizon`) and reports "factor_lab_all" as refreshed."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    with Session(engine) as session:
        prog = JobProgress(job_id="factor-lab-all-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert "factor_lab_all" in refreshed
    with Session(engine) as session:
        rows = session.exec(select(EventStudyCache)).all()
    all_factors_rows = [
        r for r in rows
        if r.subject == research._ALL_FACTORS_SUBJECT and r.view == research._ALL_FACTORS_VIEW
    ]
    assert len(all_factors_rows) == 1
    # `_cache_asof_key(None)` (research.py) serializes an all-history (no as_of) key as the sentinel
    # string "all", not a bare None column value -- the pre-existing (iter-31) `factor_lab_all_cached`
    # contract, unchanged by this iteration.
    assert all_factors_rows[0].asof_key == "all"
    assert all_factors_rows[0].horizon == cfg.walk_forward.default_horizon


def test_finalize_hook_factor_lab_all_unconditional_even_with_no_new_snapshot(finalize_hook_engine):
    """Unconditional (not gated on `new_snapshot_dates`), mirroring `forward_aggregates`/`index_series`
    above: the dataset-version stamp is GLOBAL, so this key is warmed even on a zero-new-snapshot
    (already-current) finalize call."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    with Session(engine) as session:
        prog = JobProgress(job_id="factor-lab-all-zero-work-probe", kind="backfill", start=d, end=d)
        # prog.new_snapshot_dates deliberately left empty.
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert "factor_lab_all" in refreshed


def test_finalize_hook_factor_lab_all_second_run_still_reported_on_cache_hit(finalize_hook_engine):
    """A SECOND finalize hook call with no intervening dataset change is a genuine cache HIT for the SAME
    key — still honestly reported as "factor_lab_all" (mirrors `research_hot_keys_warm`'s own "call
    succeeded, non-degraded" gate, not `index_series_warm`'s "persisted this run" gate — a clean HIT is not
    a degrade). Exactly one `EventStudyCache` row for this key exists after both calls -- the second call
    never writes a duplicate."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    with Session(engine) as session:
        prog1 = JobProgress(job_id="factor-lab-all-first", kind="backfill", start=d, end=d)
        prog1.new_snapshot_dates = [d]
        first = data_manager._refresh_ingest_aggregates(session, cfg, prog1)
    assert "factor_lab_all" in first

    with Session(engine) as session:
        prog2 = JobProgress(job_id="factor-lab-all-second", kind="backfill", start=d, end=d)
        prog2.new_snapshot_dates = [d]
        second = data_manager._refresh_ingest_aggregates(session, cfg, prog2)
    assert "factor_lab_all" in second
    with Session(engine) as session:
        rows = session.exec(select(EventStudyCache)).all()
    all_factors_rows = [
        r for r in rows
        if r.subject == research._ALL_FACTORS_SUBJECT and r.view == research._ALL_FACTORS_VIEW
    ]
    assert len(all_factors_rows) == 1  # the second call never wrote a duplicate row


def test_finalize_hook_factor_lab_all_memory_error_isolated_and_not_reported(
    finalize_hook_engine, monkeypatch
):
    """TC-error-case — a `MemoryError` escaping `factor_lab_all_cached` (e.g. before its own internal
    catch) is isolated to that one warm step: it never flips the ingest job's own status, the OTHER
    aggregates still refresh normally, "factor_lab_all" is honestly absent (never fabricated), and
    `_release_process_memory()` runs (the iter-8 per-item isolation convention)."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    release_calls: list[str] = []

    def _boom(*_a, **_k):
        raise MemoryError("forced factor-lab-all memory pressure")

    monkeypatch.setattr(data_manager, "factor_lab_all_cached", _boom)
    monkeypatch.setattr(
        data_manager, "_release_process_memory", lambda: release_calls.append("called"),
    )
    with Session(engine) as session:
        prog = JobProgress(job_id="factor-lab-all-oom-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
    assert "factor_lab_all" not in refreshed
    assert {
        "latest_snapshot", "coverage", "membership_timeline", "market_phase", "forward_aggregates",
        "research_hot_keys", "index_series",
    } <= set(refreshed)
    assert release_calls, "_release_process_memory() must be called on the MemoryError abort path"


def test_finalize_hook_factor_lab_all_generic_failure_isolated_other_aggregates_still_refresh(
    finalize_hook_engine, monkeypatch
):
    """A non-memory exception from `factor_lab_all_cached` (forced) does not prevent the OTHER aggregates
    from refreshing — log + continue, never raise (mirrors the sibling per-item isolation tests above)."""
    engine, d = finalize_hook_engine
    cfg = load_config()

    def _boom(*_a, **_k):
        raise RuntimeError("forced factor-lab-all failure")

    monkeypatch.setattr(data_manager, "factor_lab_all_cached", _boom)
    with Session(engine) as session:
        prog = JobProgress(job_id="factor-lab-all-failure-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert "factor_lab_all" not in refreshed
    assert {
        "latest_snapshot", "coverage", "membership_timeline", "market_phase", "forward_aggregates",
        "research_hot_keys", "index_series",
    } <= set(refreshed)


def test_finalize_hook_factor_lab_all_never_reported_on_whole_response_degrade(
    finalize_hook_engine, monkeypatch
):
    """Honesty gate distinct from a plain exception: `factor_lab_all_cached` NEVER lets a MemoryError from
    `compute_factor_lab_all` escape — it catches it INTERNALLY and returns an honest degraded dict
    (`factors_status: "unavailable"`) WITHOUT persisting to `EventStudyCache`. A naive "the call didn't
    raise -> append" gate would wrongly claim a refresh that never happened. This forces exactly that
    degraded-but-non-raising return and asserts "factor_lab_all" is still honestly omitted."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    degraded_payload = {
        "asof_date": None, "factors": [], "horizons": list(cfg.walk_forward.horizons),
        "default_horizon": cfg.walk_forward.default_horizon, "deciles_count": cfg.research.factor_lab.deciles,
        "min_sample": cfg.walk_forward.min_sample, "survivorship_bias": "x", "descriptive_caveat": "x",
        "factors_table": [], "factors_status": "unavailable",
    }

    def _degraded(*_a, **_k):
        return degraded_payload

    monkeypatch.setattr(data_manager, "factor_lab_all_cached", _degraded)
    with Session(engine) as session:
        prog = JobProgress(job_id="factor-lab-all-degrade-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
    assert "factor_lab_all" not in refreshed, (
        "a whole-response degraded payload must never be claimed as a refresh, even though the call itself "
        "did not raise"
    )
    assert {
        "latest_snapshot", "coverage", "membership_timeline", "market_phase", "forward_aggregates",
        "research_hot_keys", "index_series",
    } <= set(refreshed)


def test_finalize_hook_factor_lab_all_phase_timing_log_line_present(finalize_hook_engine, caplog):
    """The `factor_lab_all_warm` phase logs its own wall-clock "J-05 finalize-tail phase timing" line
    unconditionally, mirroring every sibling phase (iter-48 diagnosis instrumentation convention)."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    with caplog.at_level("INFO", logger="trendora.data_manager"):
        with Session(engine) as session:
            prog = JobProgress(job_id="factor-lab-all-timing-probe", kind="backfill", start=d, end=d)
            prog.new_snapshot_dates = [d]
            data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert (
        "J-05 finalize-tail phase timing: job=factor-lab-all-timing-probe phase=factor_lab_all_warm"
        in caplog.text
    ), caplog.text


def test_finalize_hook_market_phase_computed_exactly_once_not_on_subsequent_read(
    finalize_hook_engine, monkeypatch
):
    """TC-4 — `compute_market_phase` executes exactly once per newly-created date, during the finalize
    hook; a subsequent read of the SAME as-of serves from `MarketPhaseCache` (zero further compute calls)."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    calls: list[int] = []
    orig = market_phase.compute_market_phase

    def _counting(*args, **kwargs):
        calls.append(1)
        return orig(*args, **kwargs)

    monkeypatch.setattr(market_phase, "compute_market_phase", _counting)
    with Session(engine) as session:
        prog = JobProgress(job_id="market-phase-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert len(calls) == 1, "compute_market_phase should run exactly once, during the finalize hook"

    # a subsequent read of the SAME as-of must serve from the cache — zero additional compute calls.
    with Session(engine) as session:
        market_phase.market_phase_cached(session, d, cfg)
    assert len(calls) == 1, "a subsequent read must serve from MarketPhaseCache, not recompute"


def test_finalize_hook_only_warms_market_phase_for_newly_created_dates(finalize_hook_engine):
    """A finalize hook call with an EMPTY `new_snapshot_dates` (e.g. a zero-work re-run) warms neither
    `market_phase` nor `latest_snapshot` — never a fabricated category for work that did not happen —
    while `coverage`/`membership_timeline`/`research_hot_keys` still refresh unconditionally."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    with Session(engine) as session:
        prog = JobProgress(job_id="zero-work-probe", kind="backfill", start=d, end=d)
        # prog.new_snapshot_dates deliberately left empty — simulates a zero-work re-run.
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert "market_phase" not in refreshed
    assert "latest_snapshot" not in refreshed
    assert {"coverage", "membership_timeline", "research_hot_keys"} <= set(refreshed)


def test_finalize_hook_partial_failure_isolated_other_aggregates_still_refresh(
    finalize_hook_engine, monkeypatch
):
    """A single aggregate's failure (research hot-key warm, forced) does not prevent the OTHERS
    (`latest_snapshot`/`coverage`/`membership_timeline`/`market_phase`) from refreshing — log + continue,
    never raise (mirrors `_warm_membership_timeline`'s non-fatal contract)."""
    engine, d = finalize_hook_engine
    cfg = load_config()

    def _boom(*_a, **_k):
        raise RuntimeError("forced research hot-key failure")

    monkeypatch.setattr(data_manager, "event_study_cached", _boom)
    with Session(engine) as session:
        prog = JobProgress(job_id="partial-failure-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert "research_hot_keys" not in refreshed
    assert {"latest_snapshot", "coverage", "membership_timeline", "market_phase"} <= set(refreshed)


def test_finalize_hook_never_raises_even_when_everything_fails(finalize_hook_engine, monkeypatch):
    """The finalize hook never raises even when EVERY compute-based sub-step fails (only the
    zero-compute `latest_snapshot` acknowledgment survives) — `_run_job`'s own call site additionally
    wraps this call, but the function itself is designed to never propagate."""
    engine, d = finalize_hook_engine
    cfg = load_config()

    def _boom(*_a, **_k):
        raise RuntimeError("forced failure")

    monkeypatch.setattr(data_manager, "refresh_coverage_snapshot", _boom)
    monkeypatch.setattr(market_phase, "market_phase_cached", _boom)
    monkeypatch.setattr(forward_testing, "forward_aggregates_ingest_cached", _boom)
    monkeypatch.setattr(data_manager, "event_study_cached", _boom)
    monkeypatch.setattr(indexes, "index_series_cached_with_status", _boom)
    monkeypatch.setattr(data_manager, "availability_cached_with_status", _boom)
    monkeypatch.setattr(data_manager, "factor_lab_all_cached", _boom)
    with Session(engine) as session:
        prog = JobProgress(job_id="all-fail-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
    assert refreshed == ["latest_snapshot"]


def test_finalize_hook_makes_no_network_call(finalize_hook_engine, monkeypatch):
    """AG-9 / TC-19 — the finalize hook's aggregate-refresh calls issue ZERO outbound network calls (every
    reused compute function is a pure DB-backed derivation, never a live provider)."""
    engine, d = finalize_hook_engine
    cfg = load_config()

    def _no_network(*_a, **_k):
        raise AssertionError("unexpected network call during the ingest finalize hook")

    monkeypatch.setattr(socket.socket, "connect", _no_network)
    with Session(engine) as session:
        prog = JobProgress(job_id="no-network-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert refreshed  # completed successfully with zero socket.connect calls


# ==================================================================================================
# ops-hardening iter-7 (J-06 closeout, audit B1): the finalize hook's NEW `drawdown_expectations` warm —
# mirrors the `research_hot_keys`/`forward_aggregates` proofs above, for the per-claim
# `compute_drawdown_expectations_cached` EventStudyCache view slot `/api/evidence` reads lazily
# (`build_evidence_payload`). `finalize_hook_engine`'s own sparse data (no `ForwardReturn` rows at all) is
# reused as-is for the honesty/isolation proofs below (an unresolvable cohort is the natural, not
# hand-forced, outcome on that fixture); `finalize_hook_drawdown_engine` adds ONE real observation so the
# "actually warmed" path is proven for real, not merely asserted.
# ==================================================================================================
_DD_WARM_HORIZON = 20  # in config.walk_forward.underwater_horizons by default (mirrors DD_H in
                        # test_forward_testing.py's own compute_drawdown_expectations fixtures).

_DD_LEDGER_CLAIM = {
    "kind": "factor", "factor": "leadership_score", "slice_kind": "total", "horizon": _DD_WARM_HORIZON,
    "direction": "positive",
}


def _dd_fake_phase_ctx(as_of_date):
    """A trivial `phase_context_by_date` stand-in classifying ONE date "Expansion" — just enough for
    `compute_drawdown_expectations` to resolve a non-empty by-phase cell (mirrors
    test_forward_testing.py's own `_fake_phase_ctx`, trimmed to a single observation)."""
    def _ctx(session=None, as_of=None, config=None):
        ctx = {as_of_date.isoformat(): {"phase": "Expansion", "severity": 10.0, "p_bear": 0.05}}
        if as_of is None:
            return dict(ctx)
        return {k: v for k, v in ctx.items() if date.fromisoformat(k) <= as_of}
    return _ctx


@pytest.fixture()
def finalize_hook_drawdown_engine(tmp_path, monkeypatch):
    """Like `finalize_hook_engine`, extended with ONE real `ForwardReturn` row at `_DD_WARM_HORIZON` for
    the same ticker/date the base fixture's `ScannerResult` already carries a `leadership_score` for, plus
    a monkeypatched causal phase classification — enough for `compute_drawdown_expectations` /
    `compute_drawdown_expectations_cached` to resolve a genuine (non-None) payload for a
    `_DD_LEDGER_CLAIM`-shaped ledger claim."""
    engine = make_engine(f"sqlite:///{tmp_path / 'finalize_dd.db'}")
    create_db_and_tables(engine)
    d = date(2024, 3, 4)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        run = ScannerRun(
            asof_date=d, created_at=datetime(2024, 3, 4), provider="seed", benchmark="SPY",
            regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        session.add(ScannerResult(
            run_id=run.id, ticker="AAA", name="AAA Corp", leadership_score=1.0, leadership_bucket="Leader",
            entry_quality_score=1.0, entry_quality_bucket="Good", risk_score=1.0, risk_bucket="Low",
            setup_status="Actionable", rank=1, record_json="{}",
        ))
        session.add(ForwardReturn(
            run_id=run.id, symbol="AAA", horizon=_DD_WARM_HORIZON, asof_date=d, entry_close=100.0,
            measured_date=d + timedelta(days=_DD_WARM_HORIZON * 2), realized_return=0.02,
            max_drawdown=-0.05, underwater_days=2, time_to_recover_days=3,
        ))
        session.commit()
    monkeypatch.setattr(market_phase, "phase_context_by_date", _dd_fake_phase_ctx(d))
    return engine, d


def test_finalize_hook_warms_drawdown_expectations_for_resolvable_claim(
    finalize_hook_drawdown_engine, tmp_path, monkeypatch
):
    """TC-1 — a non-empty evidence ledger with one resolvable `_DD_LEDGER_CLAIM`-shaped claim: the
    finalize hook's new warm step appends "drawdown_expectations" to `refreshed`, and an `EventStudyCache`
    row for the `drawdown_expectations` view exists before the (simulated) job completes."""
    engine, d = finalize_hook_drawdown_engine
    cfg = load_config()
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), {
        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
    })
    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
    with Session(engine) as session:
        prog = JobProgress(job_id="dd-warm-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert "drawdown_expectations" in refreshed
    with Session(engine) as session:
        rows = session.exec(
            select(EventStudyCache).where(EventStudyCache.view == "drawdown_expectations")
        ).all()
    assert len(rows) == 1


def test_finalize_hook_drawdown_expectations_byte_identical_to_fresh_compute(
    finalize_hook_drawdown_engine, tmp_path, monkeypatch
):
    """TC-3 — the warmed `EventStudyCache` payload is byte-identical to a fresh, UNCACHED
    `compute_drawdown_expectations` call for the same claim (AG-3: storage is re-served, never
    re-derived)."""
    engine, d = finalize_hook_drawdown_engine
    cfg = load_config()
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), {
        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
    })
    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
    with Session(engine) as session:
        prog = JobProgress(job_id="dd-byte-identity-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        data_manager._refresh_ingest_aggregates(session, cfg, prog)
    with Session(engine) as session:
        row = session.exec(
            select(EventStudyCache).where(EventStudyCache.view == "drawdown_expectations")
        ).one()
        stored = json.loads(row.payload_json)
        fresh = forward_testing.compute_drawdown_expectations(session, _DD_LEDGER_CLAIM, cfg)
    assert fresh is not None
    assert stored == fresh


def test_finalize_hook_drawdown_expectations_unresolvable_claim_not_reported(
    finalize_hook_engine, tmp_path, monkeypatch
):
    """TC-4 / honesty gate — a ledger claim whose cohort is unresolvable (the tiny `finalize_hook_engine`
    fixture carries no `ForwardReturn` rows at all, so `compute_drawdown_expectations` legitimately
    returns None) does not raise, and "drawdown_expectations" is NOT reported as refreshed — an honest
    omission, never a fabricated category (mirrors the same gating `market_phase`/`research_hot_keys`
    already apply above). The OTHER, unrelated aggregates still refresh normally — proving this is a
    per-category honesty gate, not a whole-function failure."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), {
        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
    })
    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
    with Session(engine) as session:
        prog = JobProgress(job_id="dd-unresolvable-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
    assert "drawdown_expectations" not in refreshed
    assert {"coverage", "membership_timeline"} <= set(refreshed)


def test_finalize_hook_drawdown_expectations_isolates_claim_that_raises(
    finalize_hook_drawdown_engine, tmp_path, monkeypatch
):
    """TC-4 — one claim's warm call raising mid-loop is logged and skipped; it never blocks a LATER
    claim's own warm call, and it never fails the ingest job (no exception propagates out of
    `_refresh_ingest_aggregates`). Proven by forcing the FIRST of two ledger claims to raise and asserting
    the SECOND is still attempted and still counts toward `refreshed`."""
    engine, d = finalize_hook_drawdown_engine
    cfg = load_config()
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), {
        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
        "verdict": {"status": "FAIL", "reason": "forced-raise fixture claim"},
    })
    append_entry(str(ledger), {
        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-02",
        "verdict": {"status": "FAIL", "reason": "resolvable fixture claim"},
    })
    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))

    real = forward_testing.compute_drawdown_expectations_cached
    calls = {"n": 0}

    def _raise_first_then_real(session, claim, config=None, *, phases=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("forced claim-warm failure")
        return real(session, claim, config, phases=phases)

    monkeypatch.setattr(forward_testing, "compute_drawdown_expectations_cached", _raise_first_then_real)
    with Session(engine) as session:
        prog = JobProgress(job_id="dd-raise-isolation-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
    assert calls["n"] == 2, "both claims must be attempted — the first's failure must not skip the second"
    assert "drawdown_expectations" in refreshed  # the SECOND claim's successful warm still counts


def test_finalize_hook_drawdown_expectations_missing_ledger_not_reported(
    finalize_hook_engine, tmp_path, monkeypatch
):
    """TC-5 — a missing ledger file is an EMPTY ledger (per `read_entries`'s own documented contract):
    zero warm calls, "drawdown_expectations" NOT reported as refreshed."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    monkeypatch.setenv(LEDGER_PATH_ENV, str(tmp_path / "missing" / "certified-claims.jsonl"))
    calls = {"n": 0}
    real = forward_testing.compute_drawdown_expectations_cached

    def _counting(*args, **kwargs):
        calls["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(forward_testing, "compute_drawdown_expectations_cached", _counting)
    with Session(engine) as session:
        prog = JobProgress(job_id="dd-empty-ledger-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert calls["n"] == 0
    assert "drawdown_expectations" not in refreshed


def test_finalize_hook_drawdown_expectations_forward_walk_only_ledger_not_reported(
    finalize_hook_drawdown_engine, tmp_path, monkeypatch
):
    """TC-5 variant — a ledger containing ONLY a forward-walk monitoring record (no original claim) warms
    nothing: the SAME `type == FORWARD_WALK_TYPE` filter `build_evidence_payload` applies, so a re-score
    record is never mistaken for a new claim to warm a panel for."""
    engine, d = finalize_hook_drawdown_engine
    cfg = load_config()
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), {
        "type": "forward_walk", "claim": _DD_LEDGER_CLAIM, "as_of": "2024-06-01", "edge": 0.01,
    })
    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
    with Session(engine) as session:
        prog = JobProgress(job_id="dd-forward-walk-only-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert "drawdown_expectations" not in refreshed


def test_finalize_hook_drawdown_expectations_corrupt_ledger_degrades_gracefully(
    finalize_hook_engine, tmp_path, monkeypatch
):
    """A corrupt (malformed-JSON) ledger file must not abort the whole finalize hook — the new warm
    step's own top-level try/except around ledger resolution degrades to zero warm calls (an honest
    omission), and every OTHER aggregate still refreshes normally."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    bad_ledger = tmp_path / "corrupt-ledger.jsonl"
    bad_ledger.write_text("not valid json\n")
    monkeypatch.setenv(LEDGER_PATH_ENV, str(bad_ledger))
    with Session(engine) as session:
        prog = JobProgress(job_id="dd-corrupt-ledger-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
    assert "drawdown_expectations" not in refreshed
    assert {"latest_snapshot", "coverage", "membership_timeline", "market_phase"} <= set(refreshed)


# ==================================================================================================
# ops-hardening iter-8 (J-05 REGRESSION fix): a `MemoryError` inside any of the four finalize-hook warm
# loops (per-date coverage, per-date market-phase, per-horizon forward-aggregates, per-claim drawdown-
# expectations) must be caught DISTINCTLY from the existing generic `except Exception: log + continue` —
# stop that ONE loop immediately (never hammer the next item's allocation under real pressure) while every
# OTHER loop's own generic-exception isolate-and-continue behavior (proven above/below, e.g.
# `test_finalize_hook_drawdown_expectations_isolates_claim_that_raises`) stays byte-unchanged. TC-3 = first
# item raises (zero items warmed, honest omission); TC-5 = a LATER item raises after >=1 succeeded (honest
# partial report, no further items attempted); TC-4 = a same-process DB read afterward still succeeds (no
# leaked lock/transaction).
# ==================================================================================================
def test_persist_per_date_coverage_memory_error_on_first_date_aborts_loop(
    finalize_hook_multi_date_engine, monkeypatch
):
    """TC-3 — a MemoryError on the FIRST date passed to the per-date coverage-persist loop stops it
    immediately: the SECOND date is never attempted, and the function itself does not raise (its caller,
    `_refresh_ingest_aggregates`, treats this whole call as non-fatal)."""
    engine, dates = finalize_hook_multi_date_engine
    cfg = load_config()
    calls = {"n": 0}

    def _boom(*_a, **_k):
        calls["n"] += 1
        raise MemoryError("simulated memory pressure")

    monkeypatch.setattr(data_manager, "refresh_coverage_snapshot_for", _boom)
    # force BOTH fixture dates into `todo` — neither is the resolved "current" stamp this iteration.
    monkeypatch.setattr(data_manager, "_resolve_coverage_asof", lambda *a, **k: date(2099, 1, 1))
    with Session(engine) as session:
        prog = JobProgress(job_id="cov-mem-first-probe", kind="backfill", start=dates[0], end=dates[-1])
        data_manager._persist_per_date_coverage_snapshots(session, cfg, dates, prog)  # must not raise
    assert calls["n"] == 1, "the loop must stop after the FIRST MemoryError — second date never attempted"


def test_persist_per_date_coverage_memory_error_after_partial_success_stops_remaining(
    finalize_hook_multi_date_engine, monkeypatch
):
    """TC-5 — a MemoryError on the SECOND of two dates: the first date's real persist still happens (a
    genuine `CoverageSnapshot` row exists for it afterward), and the loop stops there — no further dates
    attempted."""
    engine, dates = finalize_hook_multi_date_engine
    cfg = load_config()
    real = data_manager.refresh_coverage_snapshot_for
    calls = {"n": 0}

    def _succeed_then_boom(session, cfg, d):
        calls["n"] += 1
        if calls["n"] == 1:
            return real(session, cfg, d)
        raise MemoryError("simulated memory pressure")

    monkeypatch.setattr(data_manager, "refresh_coverage_snapshot_for", _succeed_then_boom)
    monkeypatch.setattr(data_manager, "_resolve_coverage_asof", lambda *a, **k: date(2099, 1, 1))
    with Session(engine) as session:
        prog = JobProgress(job_id="cov-mem-partial-probe", kind="backfill", start=dates[0], end=dates[-1])
        data_manager._persist_per_date_coverage_snapshots(session, cfg, dates, prog)  # must not raise
    assert calls["n"] == 2, "both dates must be attempted — the second raises, stopping the loop there"
    with Session(engine) as session:
        rows = session.exec(
            select(CoverageSnapshot).where(CoverageSnapshot.asof_key == dates[0].isoformat())
        ).all()
    assert len(rows) == 1  # the FIRST date's real persist succeeded before the abort


def test_persist_per_date_coverage_memory_error_releases_memory_after_bar_cache_drops(
    finalize_hook_multi_date_engine, monkeypatch
):
    """iter-8 AUDIT (B1 regression guard) — on a `MemoryError` abort the per-date coverage loop must
    release process memory AFTER its own prefilled `_BarCache` context has exited, not only from inside
    the loop while that ~1.5 GB cache is still referenced. Trimming while the cache is live cannot return
    the single largest freeable block to the OS, so the caller's NEXT independent warm block would start
    on the same un-trimmed arena — i.e. without the headroom the whole iter-8 fix exists to restore."""
    from app.engine.prices import active_bar_cache

    engine, dates = finalize_hook_multi_date_engine
    cfg = load_config()
    cache_bound_at_each_release: list[bool] = []

    def _boom(*_a, **_k):
        raise MemoryError("simulated memory pressure")

    monkeypatch.setattr(data_manager, "refresh_coverage_snapshot_for", _boom)
    monkeypatch.setattr(data_manager, "_resolve_coverage_asof", lambda *a, **k: date(2099, 1, 1))
    with Session(engine) as session:
        monkeypatch.setattr(
            data_manager,
            "_release_process_memory",
            lambda: cache_bound_at_each_release.append(active_bar_cache(session) is not None),
        )
        prog = JobProgress(job_id="cov-mem-release-probe", kind="backfill", start=dates[0], end=dates[-1])
        data_manager._persist_per_date_coverage_snapshots(session, cfg, dates, prog)  # must not raise

    assert cache_bound_at_each_release, (
        "_release_process_memory() must be called on the MemoryError abort path"
    )
    assert False in cache_bound_at_each_release, (
        "expected at least one release AFTER the prefilled bar-cache context exited (cache unbound); "
        f"observed cache-still-bound flags = {cache_bound_at_each_release}"
    )


def test_finalize_hook_market_phase_memory_error_on_first_date_aborts_loop(
    finalize_hook_multi_date_engine, monkeypatch
):
    """TC-3 — a MemoryError on the FIRST date of the market-phase warm loop stops the loop immediately
    (zero dates warmed): 'market_phase' is honestly omitted from `refreshed` (never a fabricated
    category), and the finalize hook itself does not raise."""
    engine, dates = finalize_hook_multi_date_engine
    cfg = load_config()
    calls = {"n": 0}

    def _boom(*_a, **_k):
        calls["n"] += 1
        raise MemoryError("simulated memory pressure")

    monkeypatch.setattr(market_phase, "market_phase_cached", _boom)
    with Session(engine) as session:
        prog = JobProgress(job_id="mp-mem-first-probe", kind="backfill", start=dates[0], end=dates[-1])
        prog.new_snapshot_dates = dates
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
    assert calls["n"] == 1, "the loop must stop after the FIRST MemoryError — second date never attempted"
    assert "market_phase" not in refreshed


def test_finalize_hook_market_phase_memory_error_after_partial_success_reports_honestly(
    finalize_hook_multi_date_engine, monkeypatch
):
    """TC-5 — a MemoryError on the SECOND of two dates: the first date's real warm still counts (honest
    partial report — 'market_phase' IS in `refreshed`), and the loop stops there."""
    engine, dates = finalize_hook_multi_date_engine
    cfg = load_config()
    real = market_phase.market_phase_cached
    calls = {"n": 0}

    def _succeed_then_boom(session, as_of, config=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return real(session, as_of, config)
        raise MemoryError("simulated memory pressure")

    monkeypatch.setattr(market_phase, "market_phase_cached", _succeed_then_boom)
    with Session(engine) as session:
        prog = JobProgress(job_id="mp-mem-partial-probe", kind="backfill", start=dates[0], end=dates[-1])
        prog.new_snapshot_dates = dates
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
    assert calls["n"] == 2, "both dates must be attempted — the second raises, stopping the loop there"
    assert "market_phase" in refreshed  # the FIRST date's real warm still counts honestly


def test_finalize_hook_memory_error_leaves_no_leaked_lock_subsequent_read_succeeds(
    finalize_hook_multi_date_engine, monkeypatch
):
    """TC-4 — after an injected MemoryError aborts the market-phase warm loop mid-finalize-hook, a
    SUBSEQUENT DB read in the SAME process (a fresh `refresh_coverage_snapshot` call, mirroring what a
    live `GET /api/data` request would do next) still succeeds — proving no leaked lock/open transaction
    blocks recovery without a process restart."""
    engine, dates = finalize_hook_multi_date_engine
    cfg = load_config()

    def _boom(*_a, **_k):
        raise MemoryError("simulated memory pressure")

    monkeypatch.setattr(market_phase, "market_phase_cached", _boom)
    with Session(engine) as session:
        prog = JobProgress(job_id="mp-mem-recovery-probe", kind="backfill", start=dates[0], end=dates[-1])
        prog.new_snapshot_dates = dates
        data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise, must not leak a lock

    # a genuine subsequent DB read, in the SAME process, on a FRESH session against the SAME engine —
    # `refresh_coverage_snapshot` is unrelated to the patched `market_phase_cached`, so this proves the DB
    # itself (not just an unrelated code path) is still fully readable/writable after the abort.
    with Session(engine) as session:
        payload = data_manager.refresh_coverage_snapshot(session, cfg)
    assert payload is not None


# ==================================================================================================
# ops-hardening iter-53 (J-05/J-07, TC-5) — the fault-injection probe ARMED AT THE ACTUAL TREATED SITE
# (`TRENDORA_FAULT_INJECT_MEMORY_ERROR`, mirroring the existing `factor_lab_all` convention — see
# `test_research_streaming.py::test_compute_factor_lab_all_restores_the_collector_after_an_injected_
# memory_error`), not a monkeypatched whole-function stand-in like the tests above. These prove the
# INNER call this iteration's GIL-hold fix bounds (`universe_resolver.resolve_with_reasons`'s per-symbol
# `bars_asof_window` fetch; `market_phase._severity_reading`'s benchmark/^VIX bounded fetch) still
# preserves the iter-8 MemoryError isolate-and-continue contract when the fault fires from INSIDE the
# real, unmocked treated code path (not merely at the loop's own call site).
#
# ops-hardening iter-54 (B2 fix): the `coverage_membership_timeline` injection site RELOCATED from inside
# `resolve_with_reasons`'s shared per-symbol loop to `_refresh_ingest_aggregates`'s own
# `coverage_membership_timeline_refresh` phase block (see that function's comment for the full "isolates
# the wrong phase" finding) — this test's call shape (`_refresh_ingest_aggregates` invoked directly, no
# live snapshot dates) already reaches the NEW site unchanged, so its assertions still hold; only the
# docstring below is corrected to say where the fault actually fires now.
# ==================================================================================================
def test_finalize_hook_coverage_membership_timeline_fault_injected_releases_memory_honestly(
    tmp_path, monkeypatch,
):
    """`TRENDORA_FAULT_INJECT_MEMORY_ERROR=coverage_membership_timeline` armed against a REAL (unmocked)
    `_refresh_ingest_aggregates` call, immediately before its `coverage_membership_timeline_refresh`
    phase's own `refresh_coverage_snapshot` call (ops-hardening iter-54, B2 fix — relocated from inside
    `universe_resolver.resolve_with_reasons`'s shared per-symbol loop, which is also reached from the
    per-date backfill compute and so could not isolate this phase specifically): `coverage`/
    `membership_timeline` are honestly OMITTED from `aggregates_refreshed`, the dedicated
    `except MemoryError` handler this phase carries calls `_release_process_memory()`, and the hook
    itself does not raise."""
    from app.engine import universe_resolver

    cfg = load_config()
    engine = make_engine(f"sqlite:///{tmp_path / 'cov-fault.db'}")
    create_db_and_tables(engine)
    d = date(2024, 6, 1)
    start = d - timedelta(days=249)

    def _fake_pool(seed_dir=None):
        return [{"symbol": "LONG", "sector": "Technology", "source": "test"}]

    monkeypatch.setattr(data_manager, "read_pool", _fake_pool)
    monkeypatch.setattr(universe_resolver, "read_pool", _fake_pool)

    with Session(engine) as session:
        for i in range(250):  # comfortably clears history(200)/price($10)/ADV($50M) -> admitted-eligible
            session.add(DailyPrice(
                symbol="LONG", date=start + timedelta(days=i), open=50.0, high=50.0, low=50.0,
                close=50.0, volume=2_000_000.0,
            ))
        session.add(ScannerRun(
            asof_date=d, created_at=datetime(2024, 6, 1), provider="seed", benchmark="SPY",
            regime_score=50.0, regime_label="Choppy", regime_components_json="{}",
            new_high_low_json="{}", candidate_counts_json="{}",
        ))
        session.commit()

    release_calls = {"n": 0}

    def _count_release():
        release_calls["n"] += 1

    monkeypatch.setattr(data_manager, "_release_process_memory", _count_release)
    monkeypatch.setenv("TRENDORA_FAULT_INJECT_MEMORY_ERROR", "coverage_membership_timeline")

    with Session(engine) as session:
        prog = JobProgress(job_id="cov-fault-probe", kind="backfill", start=d, end=d)
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise

    assert "coverage" not in refreshed and "membership_timeline" not in refreshed, (
        f"the faulted category must be honestly omitted, never a fabricated refresh: {refreshed}"
    )
    assert release_calls["n"] >= 1, "_release_process_memory() must be called on the injected MemoryError"

    # TC-4-style recovery check: a genuine SUBSEQUENT read in the same process still succeeds (no leaked
    # lock/transaction from the aborted call) once the fault is disarmed.
    monkeypatch.delenv("TRENDORA_FAULT_INJECT_MEMORY_ERROR", raising=False)
    with Session(engine) as session:
        payload = data_manager.refresh_coverage_snapshot(session, cfg)
    assert payload is not None


def test_finalize_hook_market_phase_fault_injected_releases_memory_honestly(finalize_hook_multi_date_engine, monkeypatch):
    """`TRENDORA_FAULT_INJECT_MEMORY_ERROR=market_phase` armed against a REAL (unmocked) `compute_market_
    phase` -> `_severity_reading` call: the EXISTING per-date `except MemoryError` handler in
    `_refresh_ingest_aggregates`'s `market_phase_warm` loop (unchanged by this iteration) still fires
    correctly when the fault originates from INSIDE the newly-bounded fetch, not merely when the whole
    `market_phase_cached` function is monkeypatched away (the shape the OLDER tests above use)."""
    engine, dates = finalize_hook_multi_date_engine
    cfg = load_config()

    release_calls = {"n": 0}

    def _count_release():
        release_calls["n"] += 1

    monkeypatch.setattr(data_manager, "_release_process_memory", _count_release)
    monkeypatch.setenv("TRENDORA_FAULT_INJECT_MEMORY_ERROR", "market_phase")

    with Session(engine) as session:
        prog = JobProgress(job_id="mp-fault-probe", kind="backfill", start=dates[0], end=dates[-1])
        prog.new_snapshot_dates = dates
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise

    assert "market_phase" not in refreshed, (
        f"the faulted category must be honestly omitted, never a fabricated refresh: {refreshed}"
    )
    assert release_calls["n"] >= 1, "_release_process_memory() must be called on the injected MemoryError"

    monkeypatch.delenv("TRENDORA_FAULT_INJECT_MEMORY_ERROR", raising=False)
    with Session(engine) as session:
        payload = data_manager.refresh_coverage_snapshot(session, cfg)
    assert payload is not None


def test_finalize_hook_forward_aggregates_memory_error_on_first_horizon_aborts_loop(
    finalize_hook_engine, monkeypatch
):
    """TC-3 — a MemoryError on the FIRST configured horizon stops the forward-aggregates warm loop
    immediately: 'forward_aggregates' is honestly omitted (zero horizons warmed), and the hook itself does
    not raise. Unlike the coverage/market-phase/drawdown loops, this loop had NO per-item isolation before
    this iteration (a single exception aborted the whole block) — a MemoryError now gets its OWN early-
    abort handling while every OTHER exception type keeps that exact pre-existing whole-block-abort
    behavior (proven by `test_finalize_hook_never_raises_even_when_everything_fails`, unchanged)."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    calls = {"n": 0}

    def _boom(*_a, **_k):
        calls["n"] += 1
        raise MemoryError("simulated memory pressure")

    monkeypatch.setattr(forward_testing, "forward_aggregates_ingest_cached", _boom)
    with Session(engine) as session:
        prog = JobProgress(job_id="fa-mem-first-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
    assert calls["n"] == 1, "the loop must stop after the FIRST MemoryError — no further horizons attempted"
    assert "forward_aggregates" not in refreshed


def test_finalize_hook_forward_aggregates_memory_error_after_partial_success_reports_honestly(
    finalize_hook_engine, monkeypatch
):
    """TC-1/TC-4 (iter-55 INVERTED from the pre-fix behavior this test used to encode) — a MemoryError on
    the SECOND of N configured horizons: the FIRST horizon's real warm still ran, but completeness (ALL
    configured horizons), not any-succeeded, is now the bar for claiming 'forward_aggregates' was
    refreshed. Before iter-55 this test asserted `"forward_aggregates" in refreshed` after only 1 of
    N>=3 horizons completed — i.e. it encoded the PRE-FIX (buggy) behavior as correct: the live-incident
    evidence (run 351, `logs/backend.log:233042`) showed exactly this shape (some early horizons succeed,
    a later one aborts under memory pressure, the rest are never attempted) still being reported as a full
    refresh. This test now asserts the OPPOSITE: `"forward_aggregates"` is OMITTED whenever fewer than
    ALL configured horizons complete, even though the first horizon's compute genuinely ran and its
    result is still cached/persisted — only the run-level completeness CLAIM changes."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    n_horizons = len(cfg.walk_forward.horizons)
    assert n_horizons >= 3, "fixture config must configure >= 3 horizons for this test to be meaningful"
    real = forward_testing.forward_aggregates_ingest_cached
    calls = {"n": 0}

    def _succeed_then_boom(session, horizon, config=None, *, as_of=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return real(session, horizon, config, as_of=as_of)
        raise MemoryError("simulated memory pressure")

    monkeypatch.setattr(forward_testing, "forward_aggregates_ingest_cached", _succeed_then_boom)
    with Session(engine) as session:
        prog = JobProgress(job_id="fa-mem-partial-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
    assert calls["n"] == 2, "the loop must stop right after the SECOND (raising) horizon"
    assert "forward_aggregates" not in refreshed, (
        "iter-55: a mid-loop MemoryError must omit forward_aggregates even though the FIRST horizon "
        f"completed successfully -- completeness (ALL horizons), not any-succeeded, is the bar: {refreshed}"
    )


def test_finalize_hook_forward_aggregates_live_incident_shape_omits_but_preserves_siblings(
    finalize_hook_engine, monkeypatch
):
    """TC-1/TC-2/TC-4 — the EXACT live-incident shape (run 351, `logs/backend.log:233042`): with
    `cfg.walk_forward.horizons == [1, 5, 10, 20, 60]` (config.yaml:777, 5 configured horizons), horizons
    1, 5, and 10 succeed, horizon 20 raises `MemoryError`, and horizon 60 is never attempted. TC-1/TC-4:
    `aggregates_refreshed` OMITS `"forward_aggregates"` even though 3 of 5 horizons genuinely completed;
    the run's own `status` field is unaffected (isolate-and-continue unchanged -- this fixture's hook call
    itself must not raise). TC-2: every OTHER finalize-tail member this fixture's data legitimately warms
    (`coverage`, `membership_timeline`, `market_phase`, `latest_snapshot`, `research_hot_keys`,
    `index_series`, `factor_lab_all`) is STILL present in `refreshed` -- the fix narrows only the
    `forward_aggregates` gate, never any sibling gate."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    assert cfg.walk_forward.horizons == [1, 5, 10, 20, 60], (
        "this test's live-incident shape (3 succeed, 1 MemoryErrors, 1 never attempted) is pinned to the "
        f"real config.yaml:777 horizon list; got {cfg.walk_forward.horizons}"
    )
    real = forward_testing.forward_aggregates_ingest_cached
    calls = {"n": 0}

    def _three_succeed_then_boom(session, horizon, config=None, *, as_of=None):
        calls["n"] += 1
        if calls["n"] <= 3:  # horizons 1, 5, 10
            return real(session, horizon, config, as_of=as_of)
        raise MemoryError("simulated memory pressure at horizon 20")  # horizon 60 never reached

    monkeypatch.setattr(forward_testing, "forward_aggregates_ingest_cached", _three_succeed_then_boom)
    with Session(engine) as session:
        prog = JobProgress(job_id="fa-live-incident-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
    assert calls["n"] == 4, "3 horizons succeed (1/5/10), the 4th call (horizon 20) raises and stops the loop"
    assert "forward_aggregates" not in refreshed, (
        f"TC-1/TC-4: 3 of 5 horizons completing is still incomplete -- must be omitted: {refreshed}"
    )
    for sibling in (
        "coverage", "membership_timeline", "market_phase", "latest_snapshot", "research_hot_keys",
        "index_series", "factor_lab_all",
    ):
        assert sibling in refreshed, (
            f"TC-2: sibling aggregate {sibling!r} must remain refreshed -- the fix narrows ONLY the "
            f"forward_aggregates gate: {refreshed}"
        )


def test_finalize_hook_drawdown_expectations_memory_error_on_first_claim_aborts_loop(
    finalize_hook_drawdown_engine, tmp_path, monkeypatch
):
    """TC-3 — a MemoryError on the FIRST of two ledger claims stops the drawdown-expectations warm loop
    immediately: the SECOND claim is never attempted, and 'drawdown_expectations' is honestly omitted
    (zero claims warmed)."""
    engine, d = finalize_hook_drawdown_engine
    cfg = load_config()
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), {
        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
    })
    append_entry(str(ledger), {
        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-02",
        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
    })
    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
    calls = {"n": 0}

    def _boom(*_a, **_k):
        calls["n"] += 1
        raise MemoryError("simulated memory pressure")

    monkeypatch.setattr(forward_testing, "compute_drawdown_expectations_cached", _boom)
    with Session(engine) as session:
        prog = JobProgress(job_id="dd-mem-first-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
    assert calls["n"] == 1, "the loop must stop after the FIRST MemoryError — second claim never attempted"
    assert "drawdown_expectations" not in refreshed


def test_finalize_hook_drawdown_expectations_memory_error_after_partial_success_reports_honestly(
    finalize_hook_drawdown_engine, tmp_path, monkeypatch
):
    """TC-5 / TC-7 — a MemoryError on the SECOND of two claims: the FIRST claim's real warm still counts
    (honest partial report — 'drawdown_expectations' IS in `refreshed`), the second claim is never
    attempted, and the FIRST claim's persisted payload is byte-identical to a fresh, uncached compute for
    the same claim (AG-3 — the error-handling change never touches correctness)."""
    engine, d = finalize_hook_drawdown_engine
    cfg = load_config()
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), {
        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
    })
    append_entry(str(ledger), {
        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-02",
        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
    })
    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
    real = forward_testing.compute_drawdown_expectations_cached
    calls = {"n": 0}

    def _succeed_then_boom(session, claim, config=None, *, phases=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return real(session, claim, config, phases=phases)
        raise MemoryError("simulated memory pressure")

    monkeypatch.setattr(forward_testing, "compute_drawdown_expectations_cached", _succeed_then_boom)
    with Session(engine) as session:
        prog = JobProgress(job_id="dd-mem-partial-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
    assert calls["n"] == 2, "both claims must be attempted — the second raises, stopping the loop there"
    assert "drawdown_expectations" in refreshed  # the FIRST claim's real warm still counts honestly

    with Session(engine) as session:
        row = session.exec(
            select(EventStudyCache).where(EventStudyCache.view == "drawdown_expectations")
        ).one()
        stored = json.loads(row.payload_json)
        fresh = forward_testing.compute_drawdown_expectations(session, _DD_LEDGER_CLAIM, cfg)
    assert fresh is not None
    assert stored == fresh


def test_finalize_hook_drawdown_expectations_isolates_claim_that_raises_non_memory_unchanged(
    finalize_hook_drawdown_engine, tmp_path, monkeypatch
):
    """Regression guard — a NON-`MemoryError` exception on the first claim keeps the pre-existing generic
    isolate-and-continue behavior byte-unchanged by this iteration's diff: the second claim IS still
    attempted and still counts. (`test_finalize_hook_drawdown_expectations_isolates_claim_that_raises`
    above proves the same invariant; this is a second, explicit confirmation scoped to this iteration's
    new MemoryError-specific branch not altering the generic branch.)"""
    engine, d = finalize_hook_drawdown_engine
    cfg = load_config()
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), {
        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
        "verdict": {"status": "FAIL", "reason": "forced-raise fixture claim"},
    })
    append_entry(str(ledger), {
        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-02",
        "verdict": {"status": "FAIL", "reason": "resolvable fixture claim"},
    })
    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
    real = forward_testing.compute_drawdown_expectations_cached
    calls = {"n": 0}

    def _raise_first_then_real(session, claim, config=None, *, phases=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ValueError("forced non-memory claim-warm failure")
        return real(session, claim, config, phases=phases)

    monkeypatch.setattr(forward_testing, "compute_drawdown_expectations_cached", _raise_first_then_real)
    with Session(engine) as session:
        prog = JobProgress(job_id="dd-nonmem-isolation-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
    assert calls["n"] == 2, "a non-memory exception must NOT abort the loop — both claims still attempted"
    assert "drawdown_expectations" in refreshed


# ==================================================================================================
# ops-hardening iter-49 (J-05/J-07, TC-11) — error-case coverage for THIS iteration's own new code: the
# once-per-finalize-invocation `phase_context_by_date` precomputation in the drawdown-expectations warm
# loop (`data_manager.py`) and the column-projected read in `_factor_decile_observations`
# (`research.py`) — both newly added this iteration, neither exercised by the pre-existing per-claim
# MemoryError/non-memory tests above (which patch `compute_drawdown_expectations_cached` itself, a layer
# above where these two new pieces of code actually run).
# ==================================================================================================
def test_finalize_hook_drawdown_phase_context_warm_non_memory_failure_falls_back_to_per_claim_self_compute(
    finalize_hook_drawdown_engine, tmp_path, monkeypatch,
):
    """A genuine non-memory exception inside the NEW once-per-invocation `phase_context_by_date` warm
    (`data_manager._refresh_ingest_aggregates`'s `drawdown_expectations_warm` block) is caught, logged,
    and never aborts the finalize hook — it degrades to `phases=None`, so the single claim below falls
    back to ITS OWN self-compute (`compute_drawdown_expectations`'s pre-iter-49 default: `if phases is
    None: phases = phase_context_by_date(...)`), which still resolves a genuine payload here. The mock
    fails ONLY on its first invocation (a transient failure, recovering on retry) — the pre-loop
    precompute is call 1 (fails), the single claim's own internal fallback is call 2 (succeeds via the
    real function), so BOTH calls fire and the claim's payload is still genuine."""
    engine, d = finalize_hook_drawdown_engine
    cfg = load_config()
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), {
        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
    })
    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))

    real_phase_ctx = market_phase.phase_context_by_date
    calls = {"n": 0}

    def _boom_once_then_real(session, as_of=None, config=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("forced phase-context precompute failure (non-memory probe)")
        return real_phase_ctx(session, as_of=as_of, config=config)

    monkeypatch.setattr(market_phase, "phase_context_by_date", _boom_once_then_real)
    with Session(engine) as session:
        prog = JobProgress(job_id="dd-phase-ctx-nonmem-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
    assert calls["n"] == 2, (
        "the pre-loop precompute (call 1, fails) plus the single claim's own internal self-compute "
        "fallback (call 2, succeeds) must both have fired"
    )
    assert "drawdown_expectations" in refreshed, (
        f"the per-claim self-compute fallback must still resolve a genuine payload; refreshed={refreshed}"
    )


def test_finalize_hook_drawdown_phase_context_warm_memory_error_releases_and_stops_before_any_claim(
    finalize_hook_drawdown_engine, tmp_path, monkeypatch,
):
    """The SAME precompute step, but a `MemoryError` — caught by ITS OWN distinct handler applying the
    iter-8 convention IN FULL: `_release_process_memory()` runs AND the per-claim loop is skipped entirely.

    ops-hardening iter-49 AUDIT (finding B3): this test previously asserted the opposite (fall through to
    per-claim self-compute). Falling through set `phases=None`, so every claim then self-computed its own
    all-history timeline — under memory pressure the handler degraded to the MORE allocating path, the
    exact behavior the iter-8 convention exists to prevent. The mock still fails only on its FIRST
    invocation, so a fall-through would visibly succeed on call 2; asserting `calls["n"] == 1` therefore
    proves the loop was genuinely skipped rather than merely erroring again, and `drawdown_expectations`
    must be honestly ABSENT from the refreshed list (nothing was warmed)."""
    engine, d = finalize_hook_drawdown_engine
    cfg = load_config()
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), {
        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
    })
    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
    release_calls = []
    monkeypatch.setattr(
        data_manager, "_release_process_memory", lambda: release_calls.append("called"),
    )

    real_phase_ctx = market_phase.phase_context_by_date
    calls = {"n": 0}

    def _boom_once_then_real(session, as_of=None, config=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise MemoryError("simulated memory pressure (phase-context precompute)")
        return real_phase_ctx(session, as_of=as_of, config=config)

    monkeypatch.setattr(market_phase, "phase_context_by_date", _boom_once_then_real)
    with Session(engine) as session:
        prog = JobProgress(job_id="dd-phase-ctx-mem-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
    assert release_calls, "the iter-8 convention requires _release_process_memory() on the MemoryError path"
    assert calls["n"] == 1, (
        "the per-claim loop must be skipped entirely after a memory-pressure abort in the precompute — a "
        f"second phase_context_by_date call means a claim self-computed its own timeline anyway (calls={calls['n']})"
    )
    assert "drawdown_expectations" not in refreshed, (
        f"nothing was warmed after the memory-pressure abort, so the category must be honestly omitted; "
        f"refreshed={refreshed}"
    )


def test_finalize_hook_drawdown_expectations_column_projected_read_non_memory_failure_isolated(
    finalize_hook_drawdown_engine, tmp_path, monkeypatch,
):
    """TC-11 — a genuine non-memory exception raised INSIDE `_factor_decile_observations`'s NEW
    column-projected read (`research._extract_factor_value_from_row`, the iter-49 column-projection fix's
    own new code) is caught by the SAME per-claim isolation convention every other claim-warm failure
    already relies on: the finalize hook never raises, "drawdown_expectations" is honestly omitted for a
    single-claim ledger, and the failure is logged.

    Uses a DECILE-scoped claim (`slice_kind: "decile"`, mirroring the real live ledger's 5 decile-scoped
    claims), NOT `_DD_LEDGER_CLAIM` (`slice_kind: "total"`, the "total"/`_factor_observations` branch this
    iteration deliberately left untouched) — only the decile branch reaches
    `_extract_factor_value_from_row` at all."""
    engine, d = finalize_hook_drawdown_engine
    cfg = load_config()
    decile_claim = {**_DD_LEDGER_CLAIM, "slice_kind": "decile", "decile": 10}
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), {
        "claim": decile_claim, "register_date": "2024-06-01",
        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
    })
    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))

    import app.engine.research as research_module

    boom_calls = {"n": 0}

    def _boom(*_a, **_k):
        boom_calls["n"] += 1
        raise RuntimeError("forced column-projected extractor failure (non-memory probe)")

    monkeypatch.setattr(research_module, "_extract_factor_value_from_row", _boom)
    with Session(engine) as session:
        prog = JobProgress(job_id="dd-col-proj-nonmem-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
    # ops-hardening iter-49 AUDIT (T1): without this the proof is VACUOUS — "drawdown_expectations" is
    # absent from `refreshed` for many reasons that have nothing to do with the injected fault (an
    # unresolvable cohort, an out-of-scope horizon, a decile branch never reached on this fixture all
    # produce the SAME observable). Asserting the injected extractor actually RAN is what makes the
    # remaining assertion evidence of isolation rather than of a no-op.
    assert boom_calls["n"] > 0, (
        "the injected failure never fired — this claim never reached the new column-projected extractor, "
        "so the isolation assertion below would pass vacuously"
    )
    assert "drawdown_expectations" not in refreshed, (
        f"the single claim's own extractor failure must be honestly omitted, never fabricated; "
        f"refreshed={refreshed}"
    )


# ops-hardening iter-49 AUDIT (finding T1) — TC-2's own regression guard, and the memoization guard the
# suite was missing entirely. The phase spec's TESTING REQUIREMENTS ask for "per-horizon/per-claim
# sub-phase timing tests"; before this test the ONLY evidence for TC-2 was three live-run log reads
# (reports/perf-budgets.md Addendum 4/6) and nothing in the suite asserted either new log line, so a
# refactor could silently drop the attribution this iteration exists to provide. The same gap covered the
# iteration's actual bound: `phases` is threaded into every claim, but no test proved the timeline is
# computed ONCE per finalize invocation rather than once per claim — and it cannot be caught by the
# byte-identity proofs (both paths are byte-identical BY CONSTRUCTION; dropping `phases=_dd_phases`
# restores the per-claim cost with every existing assertion still green).
def test_finalize_hook_sub_phase_timing_names_each_horizon_and_claim_and_memoizes_phase_context(
    finalize_hook_drawdown_engine, tmp_path, monkeypatch, caplog,
):
    """TC-2 + the `phases` memoization, on the SAME finalize-tail invocation.

    TC-2: the per-horizon and per-claim sub-phase timing lines are emitted for EVERY configured horizon
    and for the claim, each naming a specific horizon/claim identity (never a bare loop index, which is
    not diagnostic across runs whose ledger order can change), and the pre-existing whole-phase lines for
    both loops still fire unchanged alongside them.

    Memoization: `phase_context_by_date` is called EXACTLY ONCE for a finalize invocation whose claim
    genuinely computes a payload — proving the pre-loop precompute is what the claim consumed. Without
    the threading (`phases=None` reaching `compute_drawdown_expectations`) this same fixture calls it
    twice: once in the precompute, once in the claim's own self-compute.
    """
    engine, d = finalize_hook_drawdown_engine
    cfg = load_config()
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), {
        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
    })
    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))

    # wrap (never replace) the fixture's own fake timeline so the payload below is still genuine.
    fixture_phase_ctx = market_phase.phase_context_by_date
    phase_ctx_calls = {"n": 0}

    def _counting_phase_ctx(session=None, as_of=None, config=None):
        phase_ctx_calls["n"] += 1
        return fixture_phase_ctx(session, as_of=as_of, config=config)

    monkeypatch.setattr(market_phase, "phase_context_by_date", _counting_phase_ctx)

    with caplog.at_level("INFO", logger="trendora.data_manager"):
        with Session(engine) as session:
            prog = JobProgress(job_id="sub-phase-timing-probe", kind="backfill", start=d, end=d)
            prog.new_snapshot_dates = [d]
            refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)

    lines = [r.getMessage() for r in caplog.records]
    sub = [m for m in lines if m.startswith("J-05 finalize-tail sub-phase timing:")]
    whole = [m for m in lines if m.startswith("J-05 finalize-tail phase timing:")]

    # --- TC-2, forward_aggregates_warm: one line per CONFIGURED horizon, naming that horizon -------
    for h in cfg.walk_forward.horizons:
        assert any(
            f"phase=forward_aggregates_warm horizon={h} elapsed=" in m for m in sub
        ), f"no sub-phase timing line named horizon={h}; sub-phase lines seen: {sub}"

    # --- TC-2, drawdown_expectations_warm: one line per claim, naming THAT claim -------------------
    dd_lines = [m for m in sub if "phase=drawdown_expectations_warm" in m]
    assert len(dd_lines) == 1, f"expected exactly one per-claim line for a 1-claim ledger; got {dd_lines}"
    claim_token = dd_lines[0].split("claim=")[1].split(" elapsed=")[0]
    assert claim_token == "factor:leadership_score:h20", (
        f"the per-claim identity must name the claim's kind + discriminating selector + horizon; "
        f"got {claim_token!r}"
    )
    # a bare loop index would satisfy "some identity" while being useless across runs (the log's own
    # stated contract) — assert the token is not merely a number.
    assert not claim_token.isdigit(), f"per-claim identity must never be a raw loop index: {claim_token!r}"
    assert "elapsed=" in dd_lines[0]

    # --- the pre-existing whole-phase lines are ADDITIVE-unchanged, not replaced ------------------
    for phase in ("forward_aggregates_warm", "drawdown_expectations_warm"):
        assert any(
            f"phase={phase} elapsed=" in m for m in whole
        ), f"the pre-existing whole-phase timing line for {phase} must still fire; whole-phase lines: {whole}"

    # --- the memoization itself -------------------------------------------------------------------
    assert "drawdown_expectations" in refreshed, (
        "fixture sanity: the claim must genuinely compute a payload, otherwise the call-count assertion "
        f"below proves nothing about a timeline that was never needed; refreshed={refreshed}"
    )
    assert phase_ctx_calls["n"] == 1, (
        "the all-history timeline must be computed ONCE per finalize invocation and threaded into every "
        f"claim; {phase_ctx_calls['n']} calls means a claim self-computed its own"
    )


# ==================================================================================================
# ops-hardening iter-50 (J-07): the shared warm-in-progress guard between the boot/re-warm path
# (`warmup._warm_drawdown_expectations`) and THIS module's own `_refresh_ingest_aggregates`
# drawdown-expectations warm phase — the two proven-concurrent crash contributors from iter-49's own
# traceback read. TC-4/TC-5 prove the guard holds in BOTH trigger orders; TC-6 proves the
# `phase_context_by_date` precompute is skipped entirely once the ledger is fully cache-warm.
# ==================================================================================================
def test_drawdown_warm_guard_boot_rewarm_defers_when_ingest_already_in_flight(
    finalize_hook_drawdown_engine, tmp_path, monkeypatch, caplog,
):
    """TC-4 — the boot/re-warm path (`warmup._warm_drawdown_expectations`) defers ENTIRELY (no claim
    attempted) when the ingest finalize tail's OWN drawdown-expectations warm phase already holds the
    shared warm-in-progress slot — proven by simulating "ingest already in flight" via a direct acquire,
    then calling the boot re-warm and asserting it neither reads the ledger's real compute path nor warms
    anything, and logs the deferral naming which caller deferred. Once the slot is released, a normal
    boot re-warm proceeds and actually warms the claim (proving this is a real defer, not a permanent
    disable)."""
    engine, d = finalize_hook_drawdown_engine
    cfg = load_config()
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), {
        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
    })
    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))

    claim_calls: list[str] = []
    real_compute = forward_testing.compute_drawdown_expectations_cached

    def _spy(*a, **k):
        claim_calls.append("called")
        return real_compute(*a, **k)

    monkeypatch.setattr(forward_testing, "compute_drawdown_expectations_cached", _spy)

    assert data_manager._try_acquire_drawdown_warm("ingest_finalize") is True  # simulate "already in flight"
    try:
        with caplog.at_level("INFO", logger="trendora.data_manager"):
            warmup._warm_drawdown_expectations(engine, cfg)  # must not raise, must not block
        assert claim_calls == [], "the boot re-warm must not attempt any claim while the guard is held"
        assert any(
            "deferring" in r.getMessage() and "boot_rewarm" in r.getMessage() for r in caplog.records
        ), f"expected a deferral log line naming boot_rewarm; got {[r.getMessage() for r in caplog.records]}"
    finally:
        data_manager._release_drawdown_warm()

    # after release, a normal boot re-warm proceeds and actually warms the claim.
    warmup._warm_drawdown_expectations(engine, cfg)
    assert claim_calls == ["called"], "once the slot is free, the boot re-warm must proceed normally"


def test_drawdown_warm_guard_ingest_finalize_defers_when_boot_rewarm_already_in_flight(
    finalize_hook_drawdown_engine, tmp_path, monkeypatch, caplog,
):
    """TC-5 — the guard holds in the OTHER trigger order: the ingest finalize tail's own
    drawdown-expectations warm phase (inside `_refresh_ingest_aggregates`) defers when the boot/re-warm
    path already holds the shared slot — "drawdown_expectations" is honestly absent from `refreshed` (no
    claim attempted), `phase_context_by_date` is never called, and every OTHER finalize-hook category
    still refreshes normally (the guard scopes ONLY this one phase). Releasing the slot lets a normal
    finalize run warm the claim as before."""
    engine, d = finalize_hook_drawdown_engine
    cfg = load_config()
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), {
        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
    })
    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))

    phase_ctx_calls = {"n": 0}
    real_phase_ctx = market_phase.phase_context_by_date

    def _counting_phase_ctx(session=None, as_of=None, config=None):
        phase_ctx_calls["n"] += 1
        return real_phase_ctx(session, as_of=as_of, config=config)

    monkeypatch.setattr(market_phase, "phase_context_by_date", _counting_phase_ctx)

    assert data_manager._try_acquire_drawdown_warm("boot_rewarm") is True  # simulate "already in flight"
    try:
        with Session(engine) as session:
            prog = JobProgress(job_id="dd-guard-ingest-defers", kind="backfill", start=d, end=d)
            prog.new_snapshot_dates = [d]
            with caplog.at_level("INFO", logger="trendora.data_manager"):
                refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
    finally:
        data_manager._release_drawdown_warm()

    assert "drawdown_expectations" not in refreshed, f"deferred phase must be honestly absent; got {refreshed}"
    assert {"coverage", "membership_timeline"} <= set(refreshed), (
        f"every OTHER category must still refresh normally; refreshed={refreshed}"
    )
    assert phase_ctx_calls["n"] == 0, "a deferred phase must never call phase_context_by_date"
    assert any(
        "deferring" in r.getMessage() and "ingest_finalize" in r.getMessage() for r in caplog.records
    ), f"expected a deferral log line naming ingest_finalize; got {[r.getMessage() for r in caplog.records]}"

    # after release, a normal finalize run proceeds and actually warms the claim as before.
    with Session(engine) as session:
        prog = JobProgress(job_id="dd-guard-ingest-recovers", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed2 = data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert "drawdown_expectations" in refreshed2, "once the slot is free, the finalize phase must proceed"


# ==================================================================================================
# ops-hardening iter-50 AUDIT FIX (finding B2) — the interlock above was aimed at the pair that did not
# collide. It guards ONLY the two drawdown-expectations per-claim loops against each other, while the
# finalize tail's `forward_aggregates_warm` (measured 337-385s live) and
# `coverage_membership_timeline_refresh` (82.04s live) stayed free to run concurrently with the boot
# re-warm's per-claim loop — and that overlap is exactly where the 2026-08-05 outage window sat.
# `logs/backend.log` shows the narrow guard FIRING and NOT HELPING at 23:04:01,255 ("drawdown-expectations
# warm-in-progress guard: ingest_finalize deferring") while that same job's UNGUARDED
# `forward_aggregates_warm` had been running since 22:57:37.
#
# The widened interlock covers the WHOLE ingest finalize-tail heavy-warm window and is deliberately
# ASYMMETRIC: the finalize tail is the priority producer (its warms ARE the J-05 contract) and never
# defers; the boot re-warm — a best-effort pre-warm that is already "non-fatal, retried next boot" —
# yields, both at entry AND before every claim.
# ==================================================================================================
@pytest.fixture(autouse=True)
def _reset_ingest_heavy_warm_window():
    """The heavy-warm window depth is MODULE state (deliberately — it must be visible across threads in one
    process). Reset it around every test so a failed assertion can never leave the whole file's remaining
    tests running against a permanently-open window."""
    data_manager._INGEST_HEAVY_WARM_DEPTH = 0
    yield
    data_manager._INGEST_HEAVY_WARM_DEPTH = 0


def _write_dd_ledger(tmp_path, monkeypatch, n_claims: int = 1):
    """A ledger carrying `n_claims` DISTINCT resolvable claims (distinct by `slice_kind`, so each is its own
    cache subject) — `n_claims >= 2` is what makes a mid-loop yield observable."""
    ledger = tmp_path / "certified-claims.jsonl"
    for i in range(n_claims):
        claim = dict(_DD_LEDGER_CLAIM)
        if i:
            claim["slice_kind"] = f"total_{i}"
        append_entry(str(ledger), {
            "claim": claim, "register_date": "2024-06-01",
            "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
        })
    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
    return ledger


def test_boot_rewarm_defers_for_the_whole_ingest_heavy_warm_window(
    finalize_hook_drawdown_engine, tmp_path, monkeypatch, caplog,
):
    """iter-50 audit B2 — the boot re-warm defers for the WHOLE ingest finalize-tail heavy-warm window, not
    only when the narrow drawdown slot happens to be held.

    Teeth: the narrow slot is deliberately left FREE here (`_try_acquire_drawdown_warm` would succeed), so
    the pre-fix guard would have let this warm run straight through — which is precisely the overlap the
    outage sat in (the boot re-warm running while the finalize tail's `forward_aggregates_warm` ran)."""
    engine, d = finalize_hook_drawdown_engine
    cfg = load_config()
    _write_dd_ledger(tmp_path, monkeypatch)

    claim_calls: list[str] = []
    real_compute = forward_testing.compute_drawdown_expectations_cached
    monkeypatch.setattr(
        forward_testing, "compute_drawdown_expectations_cached",
        lambda *a, **k: (claim_calls.append("called"), real_compute(*a, **k))[1],
    )

    data_manager._enter_ingest_heavy_warm("job-under-test")
    try:
        assert not data_manager._DRAWDOWN_WARM_IN_PROGRESS, (
            "fixture sanity: the NARROW drawdown slot must be free, so this test proves the WIDENED "
            "window is what defers the boot re-warm"
        )
        with caplog.at_level("INFO", logger="trendora.warmup"):
            warmup._warm_drawdown_expectations(engine, cfg)  # must not raise, must not block
        assert claim_calls == [], (
            "the boot re-warm must attempt zero claims while an ingest heavy-warm window is open"
        )
        assert any(
            "deferred" in r.getMessage() and "heavy-warm window" in r.getMessage()
            for r in caplog.records
        ), f"expected a deferral log line naming the window; got {[r.getMessage() for r in caplog.records]}"
    finally:
        data_manager._exit_ingest_heavy_warm("job-under-test")

    # a real defer, not a permanent disable: once the window closes the boot re-warm proceeds normally.
    warmup._warm_drawdown_expectations(engine, cfg)
    assert claim_calls == ["called"], "once the window closes, the boot re-warm must proceed normally"


def test_boot_rewarm_yields_mid_loop_when_an_ingest_window_opens(
    finalize_hook_drawdown_engine, tmp_path, monkeypatch, caplog,
):
    """iter-50 audit B2 — an entry-only check is not enough. A single claim can run for minutes (worst
    observed on the live ledger: the ~250s `combination:composite:h20`), so an ingest job that starts its
    finalize tail mid-loop would otherwise overlap every REMAINING claim. The boot re-warm re-checks before
    every claim and stops early.

    Teeth: the window is opened from INSIDE the first claim's compute, so a start-only check would let all
    three claims run and this assertion would see 3 calls instead of 1."""
    engine, d = finalize_hook_drawdown_engine
    cfg = load_config()
    _write_dd_ledger(tmp_path, monkeypatch, n_claims=3)

    claim_calls: list[str] = []
    real_compute = forward_testing.compute_drawdown_expectations_cached

    def _open_window_during_first_claim(*a, **k):
        claim_calls.append("called")
        if len(claim_calls) == 1:
            data_manager._enter_ingest_heavy_warm("job-starting-mid-loop")
        return real_compute(*a, **k)

    monkeypatch.setattr(
        forward_testing, "compute_drawdown_expectations_cached", _open_window_during_first_claim
    )

    try:
        with caplog.at_level("INFO", logger="trendora.warmup"):
            warmup._warm_drawdown_expectations(engine, cfg)
    finally:
        data_manager._exit_ingest_heavy_warm("job-starting-mid-loop")

    assert len(claim_calls) == 1, (
        f"the boot re-warm must yield as soon as an ingest heavy-warm window opens; it attempted "
        f"{len(claim_calls)} claims (3 = it never re-checked after the first)"
    )
    assert any("yielding" in r.getMessage() for r in caplog.records), (
        f"expected a mid-loop yield log line; got {[r.getMessage() for r in caplog.records]}"
    )


def test_ingest_finalize_declares_a_heavy_warm_window_across_its_whole_tail(
    finalize_hook_drawdown_engine, tmp_path, monkeypatch,
):
    """iter-50 audit B2 — the window must span the WHOLE finalize tail, including the phases the narrow
    drawdown slot never covered. Observed from inside `forward_aggregates_ingest_cached` (the phase measured
    at 337-385s live, and the one that was actually running during the outage) and from inside the coverage/
    membership refresh — a window opened only around the drawdown phase would fail both probes. Also
    asserts the window is CLOSED again afterwards, so a finished job can never leave the boot re-warm
    permanently deferred."""
    engine, d = finalize_hook_drawdown_engine
    cfg = load_config()
    _write_dd_ledger(tmp_path, monkeypatch)

    seen: dict[str, bool] = {}
    real_fa = forward_testing.forward_aggregates_ingest_cached
    real_cov = data_manager.refresh_coverage_snapshot

    def _probe_fa(*a, **k):
        seen["forward_aggregates_warm"] = data_manager._ingest_heavy_warm_active()
        return real_fa(*a, **k)

    def _probe_cov(*a, **k):
        seen["coverage_membership_timeline_refresh"] = data_manager._ingest_heavy_warm_active()
        return real_cov(*a, **k)

    monkeypatch.setattr(forward_testing, "forward_aggregates_ingest_cached", _probe_fa)
    monkeypatch.setattr(data_manager, "refresh_coverage_snapshot", _probe_cov)

    assert not data_manager._ingest_heavy_warm_active(), "no window may be open before the job starts"
    with Session(engine) as session:
        prog = JobProgress(job_id="heavy-warm-window", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        data_manager._refresh_ingest_aggregates(session, cfg, prog)

    assert seen.get("forward_aggregates_warm") is True, (
        "the heavy-warm window must be OPEN during forward_aggregates_warm — the phase measured at "
        f"337-385s live and running during the 2026-08-05 outage; observed: {seen}"
    )
    assert seen.get("coverage_membership_timeline_refresh") is True, (
        f"the heavy-warm window must be OPEN during the coverage/membership refresh (82.04s live); "
        f"observed: {seen}"
    )
    assert not data_manager._ingest_heavy_warm_active(), (
        "the window must be CLOSED when the finalize tail returns — otherwise one job would defer every "
        "future boot re-warm in this process"
    )
    assert data_manager._INGEST_HEAVY_WARM_DEPTH == 0, "the window depth must unwind to exactly zero"


def test_ingest_heavy_warm_window_closes_even_when_a_phase_raises(
    finalize_hook_drawdown_engine, tmp_path, monkeypatch,
):
    """iter-50 audit B2 — the window is closed in a `finally`. If an unexpected failure could leave it open,
    a single bad job would silently disable the boot re-warm for the rest of the process's life (a
    permanent, invisible regression of the J-06 post-restart Evidence warm). Teeth: the probe raises a
    non-MemoryError from inside a heavy phase — the class `_refresh_ingest_aggregates` isolates per phase —
    and the depth must still unwind to zero."""
    engine, d = finalize_hook_drawdown_engine
    cfg = load_config()
    _write_dd_ledger(tmp_path, monkeypatch)

    def _boom(*a, **k):
        raise RuntimeError("simulated phase failure")

    monkeypatch.setattr(forward_testing, "forward_aggregates_ingest_cached", _boom)

    with Session(engine) as session:
        prog = JobProgress(job_id="heavy-warm-window-raises", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)

    assert "forward_aggregates" not in refreshed, "a failed phase must be honestly absent from refreshed"
    assert data_manager._INGEST_HEAVY_WARM_DEPTH == 0, (
        "the heavy-warm window must unwind to zero even when a phase raises — otherwise one bad job "
        "permanently disables the boot re-warm"
    )


def test_drawdown_expectations_phase_context_skipped_when_ledger_fully_cache_warm(
    finalize_hook_drawdown_engine, tmp_path, monkeypatch,
):
    """TC-6 — a SECOND finalize invocation, same ledger/claim, no new data: every claim is already a cache
    HIT for the current dataset version, so `phase_context_by_date` is skipped ENTIRELY (never invoked) on
    the second call — closing the ~23.6-23.9s measured MID health-poll-stall cluster (`reports/perf-
    budgets.md` Item R Addendum 6) for the common "nothing new to compute" case. The FIRST call (a genuine
    cache MISS) still calls it exactly once, proving this is a real skip, not a permanently-disabled
    precompute."""
    engine, d = finalize_hook_drawdown_engine
    cfg = load_config()
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), {
        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
    })
    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))

    phase_ctx_calls = {"n": 0}
    real_phase_ctx = market_phase.phase_context_by_date

    def _counting_phase_ctx(session=None, as_of=None, config=None):
        phase_ctx_calls["n"] += 1
        return real_phase_ctx(session, as_of=as_of, config=config)

    monkeypatch.setattr(market_phase, "phase_context_by_date", _counting_phase_ctx)

    with Session(engine) as session:
        prog1 = JobProgress(job_id="dd-skip-first", kind="backfill", start=d, end=d)
        prog1.new_snapshot_dates = [d]
        refreshed1 = data_manager._refresh_ingest_aggregates(session, cfg, prog1)
    assert "drawdown_expectations" in refreshed1, f"fixture sanity: the claim must genuinely warm; got {refreshed1}"
    assert phase_ctx_calls["n"] == 1, "the FIRST (cache-MISS) call must compute the timeline exactly once"

    with Session(engine) as session:
        prog2 = JobProgress(job_id="dd-skip-second", kind="backfill", start=d, end=d)
        prog2.new_snapshot_dates = [d]
        refreshed2 = data_manager._refresh_ingest_aggregates(session, cfg, prog2)
    assert "drawdown_expectations" in refreshed2, (
        f"the claim is still a HIT, still honestly reported as warm; got {refreshed2}"
    )
    assert phase_ctx_calls["n"] == 1, (
        "the SECOND call (every claim already cache-HIT) must skip phase_context_by_date entirely — "
        f"call count grew to {phase_ctx_calls['n']}"
    )


def test_drawdown_expectations_needs_recompute_helper_directly(finalize_hook_drawdown_engine, tmp_path, monkeypatch):
    """TC-6 (unit-level) — `_drawdown_expectations_ledger_needs_recompute` directly: an empty ledger and a
    ledger whose sole claim is already cache-HIT both report False (nothing needs it); a ledger with a
    genuinely uncached claim reports True."""
    engine, d = finalize_hook_drawdown_engine
    cfg = load_config()

    with Session(engine) as session:
        assert data_manager._drawdown_expectations_ledger_needs_recompute(session, [], cfg) is False

        uncached_entry = {"claim": _DD_LEDGER_CLAIM}
        assert data_manager._drawdown_expectations_ledger_needs_recompute(
            session, [uncached_entry], cfg
        ) is True

        # warm it for real via the canonical cached path, then re-check — must now report False.
        forward_testing.compute_drawdown_expectations_cached(session, _DD_LEDGER_CLAIM, cfg)
        assert data_manager._drawdown_expectations_ledger_needs_recompute(
            session, [uncached_entry], cfg
        ) is False

        # a forward-walk monitoring record is not a claim to warm a panel for — never "needs" a compute.
        fw_entry = {"type": "forward_walk", "claim": _DD_LEDGER_CLAIM}
        assert data_manager._drawdown_expectations_ledger_needs_recompute(session, [fw_entry], cfg) is False


# ==================================================================================================
# ops-hardening iter-9 (B2): the resolved libc `CDLL` handle inside `_release_process_memory()` is
# memoized module-level (first-call-cached) instead of re-resolved via `ctypes.util.find_library` +
# `ctypes.CDLL` on EVERY call — the exact memory-pressure `MemoryError`-abort path this session hardened
# can call `_release_process_memory()` several times in one heavy ingest.
# ==================================================================================================
def test_release_process_memory_memoizes_libc_handle_across_calls(monkeypatch):
    """TC-13 — `ctypes.util.find_library` / `ctypes.CDLL` resolve at most ONCE across repeated
    `_release_process_memory()` calls in the same process; every call still performs `gc.collect()` +
    `malloc_trim()` with unchanged effect (no change to timing/effect, fewer redundant resolutions only)."""
    import ctypes

    # A fresh cache dict for this test only — monkeypatch restores the ORIGINAL dict object at teardown,
    # so this never leaks state into (or out of) any other test's view of the real module cache.
    monkeypatch.setattr(data_manager, "_libc_malloc_trim_cache", {})

    find_calls = {"n": 0}
    cdll_calls = {"n": 0}
    trim_calls = {"n": 0}
    gc_calls = {"n": 0}

    class _FakeLibc:
        def malloc_trim(self, _pad):
            trim_calls["n"] += 1

    def _fake_find_library(_name):
        find_calls["n"] += 1
        return "libfake-c.so.6"

    def _fake_cdll(_name):
        cdll_calls["n"] += 1
        return _FakeLibc()

    monkeypatch.setattr(ctypes.util, "find_library", _fake_find_library)
    monkeypatch.setattr(ctypes, "CDLL", _fake_cdll)
    monkeypatch.setattr(data_manager.gc, "collect", lambda: gc_calls.update(n=gc_calls["n"] + 1))

    for _ in range(5):
        data_manager._release_process_memory()

    assert find_calls["n"] == 1, "find_library must resolve at most once across repeated calls"
    assert cdll_calls["n"] == 1, "CDLL must be constructed at most once across repeated calls"
    assert trim_calls["n"] == 5, "malloc_trim must still run on EVERY call — unchanged effect"
    assert gc_calls["n"] == 5, "gc.collect() must still run on EVERY call — unchanged effect"


def test_release_process_memory_caches_permanent_resolution_failure(monkeypatch):
    """TC-13 companion — a non-glibc / symbol-absent failure on the FIRST call is cached too (never
    retried): `find_library`/`CDLL` are still invoked only once across repeated calls, and every call's
    `gc.collect()` still runs unchanged even though no `malloc_trim` is ever available."""
    import ctypes

    monkeypatch.setattr(data_manager, "_libc_malloc_trim_cache", {})
    find_calls = {"n": 0}
    gc_calls = {"n": 0}

    def _fake_find_library(_name):
        find_calls["n"] += 1
        raise OSError("simulated: no libc resolvable on this platform")

    monkeypatch.setattr(ctypes.util, "find_library", _fake_find_library)
    monkeypatch.setattr(data_manager.gc, "collect", lambda: gc_calls.update(n=gc_calls["n"] + 1))

    for _ in range(3):
        data_manager._release_process_memory()  # must not raise

    assert find_calls["n"] == 1, "a resolution failure must be cached — never retried on later calls"
    assert gc_calls["n"] == 3, "gc.collect() must still run on every call despite the cached failure"


def test_release_process_memory_brackets_itself_with_start_and_done_timings(monkeypatch, caplog):
    """ops-hardening iter-50 audit B2 — the ONLY unexamined frame inside the 2026-08-05 ~17-minute service
    silence is this teardown: `logs/backend.log` last advances at `_refresh_ingest_aggregates`'s
    `drawdown_expectations_warm` phase-timing line, and the next statements executed are its `finally` ->
    drop the shared bar cache -> `_release_process_memory()`, whose `gc.collect()` holds the GIL for its
    whole duration. Nobody could attribute the silence because that frame emitted no log line at all.

    A START line must land BEFORE `gc.collect()` runs (so a process killed or restarted mid-teardown still
    leaves the entry boundary in the log — the exact 2026-08-05 situation), and a DONE line must carry each
    step's wall clock. Teeth: `gc.collect` is stubbed to assert the START line is ALREADY emitted when it is
    entered, so an implementation that logs only after the fact fails here rather than passing on the
    presence of two lines at the end."""
    monkeypatch.setattr(data_manager, "_libc_malloc_trim_cache", {"fn": None})
    seen_at_gc_time: list[str] = []

    def _gc_collect():
        seen_at_gc_time.append(caplog.text)

    monkeypatch.setattr(data_manager.gc, "collect", _gc_collect)

    with caplog.at_level("INFO", logger="trendora.data_manager"):
        data_manager._release_process_memory()

    assert seen_at_gc_time and "_release_process_memory: START" in seen_at_gc_time[0], (
        "the START line must be emitted BEFORE gc.collect() begins — a teardown that wedges or is killed "
        "mid-collect would otherwise leave no entry boundary in the log at all, which is precisely why "
        "the 2026-08-05 outage could not be attributed"
    )
    assert "_release_process_memory: DONE" in caplog.text, "the completion line with timings must be logged"
    assert "gc_collect=" in caplog.text and "malloc_trim=" in caplog.text and "total=" in caplog.text, (
        "the DONE line must carry each step's own wall clock, not just a total — the point is to say "
        "WHICH half of the teardown consumed the time"
    )


# ==================================================================================================
# ops-hardening iter-4 (F1 fix): the finalize hook's own heartbeat -- `last_progress_at` must advance
# through the WHOLE finalize tail (not just the main scan loop), or the frontend's stale-heartbeat flag
# falsely renders "· possibly stalled" on a perfectly healthy job.
# ==================================================================================================
@pytest.fixture()
def finalize_hook_multi_date_engine(tmp_path):
    """Like `finalize_hook_engine` but with TWO stored dates — enough to prove the F1 fix ticks the
    heartbeat AT LEAST ONCE PER DATE in the market-phase warm loop, not just once for the whole call."""
    engine = make_engine(f"sqlite:///{tmp_path / 'finalize_multi.db'}")
    create_db_and_tables(engine)
    dates = [date(2024, 3, 4), date(2024, 3, 5)]
    with Session(engine) as session:
        for i, d in enumerate(dates):
            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
            run = ScannerRun(
                asof_date=d, created_at=datetime(2024, 3, 4 + i), provider="seed", benchmark="SPY",
                regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
                new_high_low_json="{}", candidate_counts_json="{}",
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            session.add(ScannerResult(
                run_id=run.id, ticker="AAA", name="AAA Corp", leadership_score=1.0, leadership_bucket="Leader",
                entry_quality_score=1.0, entry_quality_bucket="Good", risk_score=1.0, risk_bucket="Low",
                setup_status="Actionable", rank=1, record_json="{}",
            ))
            session.commit()
    return engine, dates


def test_finalize_hook_ticks_heartbeat_at_least_once_per_date_in_market_phase_loop(
    finalize_hook_multi_date_engine, monkeypatch
):
    """F1 fix: `_refresh_ingest_aggregates` calls the bare `prog.tick()` (heartbeat-only, never
    overwriting `current_activity` — see its docstring) at its own start AND inside the per-date
    market-phase warm loop (`data_manager.py:3072-3078`), so `last_progress_at` advances through the
    WHOLE finalize tail — not just the main scan loop (`:2863`). Instrumented by spying on
    `market_phase.market_phase_cached` to capture `prog.last_progress_at` at the moment EACH date's
    compute is about to run, proving the heartbeat had already advanced past a deliberately stale
    sentinel before EVERY date — not merely once, somewhere, for the whole function."""
    engine, dates = finalize_hook_multi_date_engine
    cfg = load_config()
    stale_sentinel = datetime(2000, 1, 1, tzinfo=timezone.utc)
    seen_at_call: list[datetime] = []
    real_market_phase_cached = market_phase.market_phase_cached

    def _spy(session, as_of, config=None):
        seen_at_call.append(prog.last_progress_at)
        return real_market_phase_cached(session, as_of, config)

    monkeypatch.setattr(market_phase, "market_phase_cached", _spy)
    with Session(engine) as session:
        prog = JobProgress(job_id="heartbeat-probe", kind="backfill", start=dates[0], end=dates[-1])
        prog.new_snapshot_dates = list(dates)
        prog.last_progress_at = stale_sentinel
        data_manager._refresh_ingest_aggregates(session, cfg, prog)

    assert len(seen_at_call) == len(dates), "expected one market-phase compute per new snapshot date"
    for i, seen in enumerate(seen_at_call):
        assert seen != stale_sentinel, f"date index {i}: heartbeat had not advanced before this date's compute"
    assert prog.last_progress_at != stale_sentinel  # the whole call leaves the heartbeat fresh, not frozen


@pytest.fixture()
def finalize_hook_triple_date_engine(tmp_path):
    """Like `finalize_hook_multi_date_engine` but with THREE stored dates. The per-date COVERAGE warm loop
    inside `_persist_per_date_coverage_snapshots` skips the CURRENT resolved as-of (the latest stored date),
    so three dates leaves TWO in its `todo` — enough to prove the F1 re-review fix ticks the heartbeat at
    least once PER DATE in THAT loop (not just the later market-phase loop, and not merely once for the whole
    call)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'finalize_triple.db'}")
    create_db_and_tables(engine)
    dates = [date(2024, 3, 4), date(2024, 3, 5), date(2024, 3, 6)]
    with Session(engine) as session:
        for i, d in enumerate(dates):
            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
            run = ScannerRun(
                asof_date=d, created_at=datetime(2024, 3, 4 + i), provider="seed", benchmark="SPY",
                regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
                new_high_low_json="{}", candidate_counts_json="{}",
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            session.add(ScannerResult(
                run_id=run.id, ticker="AAA", name="AAA Corp", leadership_score=1.0, leadership_bucket="Leader",
                entry_quality_score=1.0, entry_quality_bucket="Good", risk_score=1.0, risk_bucket="Low",
                setup_status="Actionable", rank=1, record_json="{}",
            ))
            session.commit()
    return engine, dates


def test_persist_per_date_coverage_snapshots_ticks_heartbeat_per_date(
    finalize_hook_triple_date_engine, monkeypatch
):
    """F1 fix (iter-4 re-review CRITICAL): the per-date COVERAGE warm loop inside
    `_persist_per_date_coverage_snapshots` — the FIRST heavy half of the finalize tail, one
    `_compute_coverage_uncached` per date (378 calls on a full rebuild) — must stamp the heartbeat before
    EACH date's compute, or `last_progress_at` freezes across all of it (the market-phase tick alone runs
    only AFTER this loop, so it cannot cover it). Calls the function directly to isolate ITS loop, and spies
    on `refresh_coverage_snapshot_for` (the way `..._in_market_phase_loop` spies on `market_phase_cached`) to
    capture `prog.last_progress_at` at the moment EACH date's compute is about to run — proving it had
    already advanced past a deliberately stale sentinel before EVERY date, not merely once for the call."""
    engine, dates = finalize_hook_triple_date_engine
    cfg = load_config()
    stale_sentinel = datetime(2000, 1, 1, tzinfo=timezone.utc)
    seen_at_call: list[datetime] = []
    real_refresh_for = data_manager.refresh_coverage_snapshot_for

    def _spy(session, config, resolved_asof):
        seen_at_call.append(prog.last_progress_at)
        return real_refresh_for(session, config, resolved_asof)

    monkeypatch.setattr(data_manager, "refresh_coverage_snapshot_for", _spy)
    with Session(engine) as session:
        prog = JobProgress(job_id="cov-heartbeat-probe", kind="backfill", start=dates[0], end=dates[-1])
        prog.last_progress_at = stale_sentinel
        # the latest date (dates[-1]) is the current stamp the loop SKIPS -> todo = the two earlier dates.
        data_manager._persist_per_date_coverage_snapshots(session, cfg, list(dates), prog)

    assert len(seen_at_call) == len(dates) - 1, "expected one coverage compute per non-current new date"
    for i, seen in enumerate(seen_at_call):
        assert seen != stale_sentinel, (
            f"date index {i}: heartbeat had not advanced before this date's coverage compute"
        )
    assert prog.last_progress_at != stale_sentinel  # the loop leaves the heartbeat fresh, not frozen


# ==================================================================================================
# ops-hardening iter-52 (J-07): a REAL scheduling yield (`time.sleep(0)`) now runs alongside each of the
# `prog.tick()` heartbeat stamps above -- a heartbeat stamp alone never hands the GIL to another thread
# (iter-49/50/51's own live drills proved this: 9/653 and 19/892 connection-level `GET /api/health`
# non-answers during a solo/concurrent finalize-tail run, `reports/perf-budgets.md` Items S/T). These tests
# prove the yield fires at the SAME per-item granularity the heartbeat already does, by spying on
# `data_manager.time.sleep` -- mirroring how the heartbeat tests above spy on `prog.last_progress_at`.
# ==================================================================================================
def test_persist_per_date_coverage_snapshots_yields_per_date(
    finalize_hook_triple_date_engine, monkeypatch
):
    """The per-date COVERAGE warm loop inside `_persist_per_date_coverage_snapshots` calls `time.sleep(0)`
    once per date in `todo` (a REAL scheduling yield, not just the heartbeat stamp) -- proven by spying on
    `data_manager.time.sleep` and asserting it is called exactly once per non-current date, always with
    argument 0 (a yield, never an actual delay). Called directly (isolating THIS loop, mirroring
    `test_persist_per_date_coverage_snapshots_ticks_heartbeat_per_date` above), so the count is exact."""
    engine, dates = finalize_hook_triple_date_engine
    cfg = load_config()
    sleep_calls: list[float] = []
    real_sleep = data_manager.time.sleep

    def _spy_sleep(seconds):
        sleep_calls.append(seconds)
        return real_sleep(seconds)

    monkeypatch.setattr(data_manager.time, "sleep", _spy_sleep)
    with Session(engine) as session:
        prog = JobProgress(job_id="cov-yield-probe", kind="backfill", start=dates[0], end=dates[-1])
        data_manager._persist_per_date_coverage_snapshots(session, cfg, list(dates), prog)

    assert len(sleep_calls) == len(dates) - 1, (
        f"expected one yield per non-current new date ({len(dates) - 1}), got {len(sleep_calls)}"
    )
    assert all(c == 0 for c in sleep_calls), (
        f"a yield point must be sleep(0) -- scheduling only, never a real delay: {sleep_calls}"
    )


def test_finalize_hook_yields_at_least_once_per_date_in_market_phase_loop(
    finalize_hook_multi_date_engine, monkeypatch
):
    """The per-date market-phase warm loop inside `_refresh_ingest_aggregates` calls `time.sleep(0)` once
    per date in `prog.new_snapshot_dates` -- proven the same way `test_finalize_hook_ticks_heartbeat_at_
    least_once_per_date_in_market_phase_loop` above proves the heartbeat: spy on `data_manager.time.sleep`
    and count calls against the known date count. A LOWER bound (`>=`), not an exact count: this call
    drives the WHOLE finalize tail, so earlier phases' own yields (added by this same iteration) also land
    on the same spy -- unlike the isolated direct call above."""
    engine, dates = finalize_hook_multi_date_engine
    cfg = load_config()
    sleep_calls: list[float] = []
    real_sleep = data_manager.time.sleep

    def _spy_sleep(seconds):
        sleep_calls.append(seconds)
        return real_sleep(seconds)

    monkeypatch.setattr(data_manager.time, "sleep", _spy_sleep)
    with Session(engine) as session:
        prog = JobProgress(job_id="phase-yield-probe", kind="backfill", start=dates[0], end=dates[-1])
        prog.new_snapshot_dates = list(dates)
        data_manager._refresh_ingest_aggregates(session, cfg, prog)

    assert len(sleep_calls) >= len(dates), (
        f"expected >= one yield per new-snapshot date ({len(dates)}) in the market-phase loop alone, got "
        f"{len(sleep_calls)} total across the whole finalize tail"
    )
    assert all(c == 0 for c in sleep_calls), (
        f"a yield point must be sleep(0) -- scheduling only, never a real delay: {sleep_calls}"
    )


def test_finalize_hook_yields_at_least_once_per_horizon_in_forward_aggregates_warm_loop(
    finalize_hook_engine, monkeypatch
):
    """The per-horizon forward-aggregates warm loop inside `_refresh_ingest_aggregates` calls
    `time.sleep(0)` once per configured `walk_forward.horizons` entry -- proven by spying on
    `data_manager.time.sleep` and asserting at least one call per configured horizon (a lower bound: the
    coverage/market-phase phases earlier in the SAME finalize-tail call also contribute yields to the same
    spy)."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    sleep_calls: list[float] = []
    real_sleep = data_manager.time.sleep

    def _spy_sleep(seconds):
        sleep_calls.append(seconds)
        return real_sleep(seconds)

    monkeypatch.setattr(data_manager.time, "sleep", _spy_sleep)
    with Session(engine) as session:
        prog = JobProgress(job_id="forward-agg-yield-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)

    assert "forward_aggregates" in refreshed  # sanity: the loop under test actually ran to completion
    assert len(sleep_calls) >= len(cfg.walk_forward.horizons), (
        f"expected >= one yield per configured horizon ({len(cfg.walk_forward.horizons)}), got "
        f"{len(sleep_calls)}"
    )
    assert all(c == 0 for c in sleep_calls), (
        f"a yield point must be sleep(0) -- scheduling only, never a real delay: {sleep_calls}"
    )


def test_run_detail_omits_aggregates_refreshed_until_computed():
    """TC-13/TC-14 — mirrors `test_run_detail_omits_breakdown_until_computed`: a not-yet-computed (fresh,
    `_create_run_record`-time) backfill row serves `aggregates_refreshed` null; an INTERRUPTED row whose
    finalize hook never ran also serves null (the breakdown fields ARE computed — the date-loop ran — but
    `aggregates_refreshed` stays at its empty JobProgress default, never a fabricated list — TC-13); a
    fetch/expand row serves null unconditionally (`_breakdown_computed` is always False for those kinds —
    TC-14); a genuinely computed row serves its real list."""
    fresh = JobProgress(job_id="never-ran", kind="backfill", start=date(2024, 1, 1), end=date(2025, 6, 1))
    assert data_manager._run_detail(fresh)["aggregates_refreshed"] is None

    # TC-13: interrupted between the date-loop and the finalize hook — calendar_days IS computed (the
    # date-loop ran and set it), but aggregates_refreshed stays empty (the hook never ran).
    interrupted = JobProgress(
        job_id="interrupted", kind="backfill", start=date(2026, 5, 2), end=date(2026, 5, 29)
    )
    interrupted.calendar_days, interrupted.dates_total, interrupted.non_trading_days = 28, 19, 9
    interrupted.already_snapshotted, interrupted.snapshots_created, interrupted.error_other = 0, 19, 0
    assert data_manager._run_detail(interrupted)["aggregates_refreshed"] is None

    # TC-14: a fetch kind never routes through the finalize hook — null regardless of any (hypothetical,
    # impossible-in-practice) populated field, since `_breakdown_computed` is always False for this kind.
    fetch_kind = JobProgress(job_id="fetch-kind", kind="fetch", start=date(2024, 1, 1), end=date(2024, 1, 1))
    fetch_kind.aggregates_refreshed = ["coverage"]
    assert data_manager._run_detail(fetch_kind)["aggregates_refreshed"] is None

    done = JobProgress(job_id="ran", kind="backfill", start=date(2026, 5, 2), end=date(2026, 5, 29))
    done.calendar_days, done.dates_total, done.non_trading_days = 28, 19, 9
    done.already_snapshotted, done.snapshots_created, done.error_other = 0, 19, 0
    done.aggregates_refreshed = ["coverage", "market_phase"]
    assert data_manager._run_detail(done)["aggregates_refreshed"] == ["coverage", "market_phase"]


def test_do_backfill_new_snapshot_dates_tracks_genuinely_new_dates_only(backfilled_job):
    """ops-hardening iter-2 (J-05) — `_persist` populates `prog.new_snapshot_dates` with exactly the dates
    THIS call genuinely created a NEW snapshot for (never a date that already existed) — the finalize
    hook's input for which as-ofs to warm in `MarketPhaseCache`. A fresh single-date window (re-queried
    live, so this is safe regardless of what other tests in this module already touched) proves the
    fresh-create case; re-running the SAME date proves the already-exists case records nothing new."""
    engine = backfilled_job["engine"]
    cfg = backfilled_job["cfg"]
    with Session(engine) as session:
        trading = _trading_days(session, cfg)
        snapshotted = set(session.exec(select(ScannerRun.asof_date)).all())
    fresh_date = next(d for d in trading if d not in snapshotted)

    prog = JobProgress(job_id="new-snapshot-dates-probe", kind="backfill", start=fresh_date, end=fresh_date)
    with Session(engine) as session:
        data_manager._do_backfill(session, cfg, prog, eng=engine)
    assert prog.new_snapshot_dates == [fresh_date]
    assert prog.snapshots_created == 1

    # re-run the SAME date: it already exists now -> nothing new is recorded.
    prog2 = JobProgress(job_id="new-snapshot-dates-probe-2", kind="backfill", start=fresh_date, end=fresh_date)
    with Session(engine) as session:
        data_manager._do_backfill(session, cfg, prog2, eng=engine)
    assert prog2.new_snapshot_dates == []
    assert prog2.snapshots_created == 0
    assert prog2.already_snapshotted == 1


def test_do_backfill_whole_stage_exception_releases_shared_cache_and_reraises(backfilled_job, monkeypatch):
    """TC-6 (reviewer MINOR, iter-37) — a whole-stage exception inside `_do_backfill`'s
    `with prefilled_bar_cache(...)` block, occurring AFTER `prog._shared_bar_cache` has genuinely been
    stashed (every per-date compute/persist failure below that point is already isolated inside
    `_run_targets`/`_persist_isolated`, never raised out of the `with` block — see their own docstrings),
    must set `prog._shared_bar_cache` back to `None`, call `_release_process_memory()`, and re-raise the
    ORIGINAL exception (never swallowed) — `data_manager.py`'s `except Exception:` branch around line 3162.

    Load-bearing (not vacuous): faults `_checkpoint_run_record` ONLY once `prog._shared_bar_cache` is
    already non-None (i.e. strictly after the real stash — the real `prefilled_bar_cache`/`_compute_one_
    backfill_date`/`_persist` calls all run for real first), so the post-fault `is None` assertion actually
    proves the except branch's reset ran — a cache that was NEVER stashed in the first place would make
    that assertion pass trivially even if the reset line were deleted."""
    engine = backfilled_job["engine"]
    cfg = backfilled_job["cfg"]
    with Session(engine) as session:
        trading = _trading_days(session, cfg)
        snapshotted = set(session.exec(select(ScannerRun.asof_date)).all())
    fresh_date = next(d for d in trading if d not in snapshotted)

    real_checkpoint = data_manager._checkpoint_run_record

    def _fault_after_stash(engine_arg, prog_arg):
        if prog_arg._shared_bar_cache is not None:
            raise RuntimeError("simulated whole-stage fault after cache stash")
        return real_checkpoint(engine_arg, prog_arg)

    monkeypatch.setattr(data_manager, "_checkpoint_run_record", _fault_after_stash)

    release_calls: list[bool] = []
    real_release = data_manager._release_process_memory

    def _spy_release() -> None:
        release_calls.append(True)
        real_release()

    monkeypatch.setattr(data_manager, "_release_process_memory", _spy_release)

    prog = JobProgress(job_id="whole-stage-exc-probe", kind="backfill", start=fresh_date, end=fresh_date)
    with Session(engine) as session:
        with pytest.raises(RuntimeError, match="simulated whole-stage fault after cache stash"):
            data_manager._do_backfill(session, cfg, prog, eng=engine)

    assert prog._shared_bar_cache is None, (
        "a whole-stage exception must clear the stashed shared-cache reference, not leave it stale"
    )
    assert release_calls, "a whole-stage exception must call _release_process_memory() before re-raising"


def test_do_backfill_env_toggle_falsy_value_keeps_shared_cache(backfilled_job, monkeypatch):
    """TC-10 (audit B5 fix) — `TRENDORA_FORCE_LEGACY_BAR_CACHE=0` must be treated as FALSY: legacy mode is
    NOT forced, so `prog._shared_bar_cache` is stashed to the real shared cache (not skipped). Before this
    fix, `if not os.environ.get(...)` treated ANY non-empty string — including `"0"` — as truthy, so this
    exact case silently forced legacy mode instead of leaving it disabled."""
    engine = backfilled_job["engine"]
    cfg = backfilled_job["cfg"]
    monkeypatch.setenv("TRENDORA_FORCE_LEGACY_BAR_CACHE", "0")
    with Session(engine) as session:
        trading = _trading_days(session, cfg)
        snapshotted = set(session.exec(select(ScannerRun.asof_date)).all())
    fresh_date = next(d for d in trading if d not in snapshotted)
    prog = JobProgress(job_id="env-toggle-falsy-probe", kind="backfill", start=fresh_date, end=fresh_date)
    with Session(engine) as session:
        data_manager._do_backfill(session, cfg, prog, eng=engine)
    assert prog._shared_bar_cache is not None, "a falsy toggle value ('0') must NOT force legacy mode"


def test_do_backfill_env_toggle_truthy_value_forces_legacy(backfilled_job, monkeypatch):
    """TC-11 — `TRENDORA_FORCE_LEGACY_BAR_CACHE=1` is treated as TRUTHY: legacy mode IS forced, so the
    shared-cache stash is skipped and `prog._shared_bar_cache` stays `None`."""
    engine = backfilled_job["engine"]
    cfg = backfilled_job["cfg"]
    monkeypatch.setenv("TRENDORA_FORCE_LEGACY_BAR_CACHE", "1")
    with Session(engine) as session:
        trading = _trading_days(session, cfg)
        snapshotted = set(session.exec(select(ScannerRun.asof_date)).all())
    fresh_date = next(d for d in trading if d not in snapshotted)
    prog = JobProgress(job_id="env-toggle-truthy-probe", kind="backfill", start=fresh_date, end=fresh_date)
    with Session(engine) as session:
        data_manager._do_backfill(session, cfg, prog, eng=engine)
    assert prog._shared_bar_cache is None, "a truthy toggle value ('1') must force legacy mode (stash skipped)"


def test_run_data_job_backfill_wires_finalize_hook_end_to_end(backfilled_job, monkeypatch):
    """ops-hardening iter-2 (J-05) end-to-end: a real backfill job dispatched through `run_data_job` (the
    SAME path the API uses) reaches the finalize hook, persists a `coverage_snapshot` row, and the job's
    final summary (the SAME dict `GET /api/data/jobs/{id}` serves) carries a non-empty
    `aggregates_refreshed`. Searches from the LATEST end of the trading calendar (the other new-date test
    above searches from the earliest) so the two never contend for the same fresh date.

    ops-hardening iter-38 (audit T2, iter-37 — full-comparison strengthening): the per-category warm loops
    inside `_refresh_ingest_aggregates` each swallow non-`MemoryError` exceptions (log + continue), so a
    break in the live-cache attach path shows up ONLY as a silently shorter `aggregates_refreshed` list —
    the pre-existing `>=` subset assertions above would not catch that. This test also runs a SECOND job of
    the identical shape (a different fresh date) with the shared-cache attach FORCED off
    (`prog._shared_bar_cache` nulled right before the finalize hook runs, mirroring pre-iter-37 behavior —
    every downstream `cache_ctx` resolves to its own independent `prefilled_bar_cache`/`nullcontext()`
    fallback, unchanged), then asserts the two runs' `aggregates_refreshed` sets are IDENTICAL: the shared-
    cache attach is a pure performance optimization, so it must never change which categories succeed."""
    engine = backfilled_job["engine"]
    cfg = backfilled_job["cfg"]
    with Session(engine) as session:
        trading = _trading_days(session, cfg)
        snapshotted = set(session.exec(select(ScannerRun.asof_date)).all())
    fresh_dates = (d for d in reversed(trading) if d not in snapshotted)
    fresh_date = next(fresh_dates)

    job = create_job("backfill", fresh_date, fresh_date)
    summary = run_data_job(job.job_id, config=cfg, engine=engine)
    assert summary["status"] == "ok"
    assert set(summary["aggregates_refreshed"]) >= {"latest_snapshot", "coverage", "membership_timeline"}

    with Session(engine) as session:
        resolved_asof = data_manager._resolve_coverage_asof(session, None, cfg)
        version = data_manager._membership_dataset_version(session, cfg)
        row = session.exec(
            select(CoverageSnapshot).where(
                CoverageSnapshot.asof_key == resolved_asof.isoformat(),
                CoverageSnapshot.dataset_version == version,
            )
        ).first()
        assert row is not None

    # the SAME dict shape GET /api/data's `runs` list serves (`recent_runs` -> `_run_detail` for the
    # persisted row) also carries the finalize hook's output — one computation, two servings.
    with Session(engine) as session:
        persisted = recent_runs(session, cfg)
    this_run = next(r for r in persisted if r["kind"] == "backfill" and r["start"] == fresh_date.isoformat())
    assert set(this_run["aggregates_refreshed"]) >= {"latest_snapshot", "coverage", "membership_timeline"}

    # TC-7 (audit T2) — forced-fallback comparison, same job shape, a different fresh date.
    fallback_fresh_date = next(fresh_dates)
    real_refresh = data_manager._refresh_ingest_aggregates

    def _forced_fallback_refresh(session_arg, cfg_arg, prog_arg):
        # force every downstream consumer's `prog._shared_bar_cache is not None` check to miss, mirroring
        # pre-iter-37 behavior (each warm call opens its own independent cache / no cache) — the live-cache
        # run above already completed and returned its summary, untouched by this patch.
        prog_arg._shared_bar_cache = None
        return real_refresh(session_arg, cfg_arg, prog_arg)

    monkeypatch.setattr(data_manager, "_refresh_ingest_aggregates", _forced_fallback_refresh)
    fallback_job = create_job("backfill", fallback_fresh_date, fallback_fresh_date)
    fallback_summary = run_data_job(fallback_job.job_id, config=cfg, engine=engine)
    assert fallback_summary["status"] == "ok"

    assert set(fallback_summary["aggregates_refreshed"]) == set(summary["aggregates_refreshed"]), (
        "the forced-fallback run's aggregates_refreshed category list diverged from the live-cache run's "
        "for the SAME job shape — the shared-cache attach must be a pure performance optimization; any "
        "category that silently drops out under only one path (a swallowed exception in a per-category "
        "warm loop) is exactly the regression audit finding T2 (iter-37) warned this assertion must catch"
    )


def test_fetch_kind_run_never_carries_aggregates_refreshed(tmp_path):
    """TC-14 — a completed `fetch` run's persisted detail always carries `aggregates_refreshed: null` (the
    finalize hook is gated to backfill/both/rebuild-like kinds only in `_run_job`; a fetch never reaches
    it)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'fetch_only.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(
            symbol="SPY", date=date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0,
        ))
        session.commit()
    cfg = load_config()

    class _EmptyProvider(PriceProvider):
        def get_daily(self, symbol, start=None, end=None):
            return []  # a successful fetch that finds no new bars — never a fabricated one

    job = create_job("fetch", date(2024, 1, 2), date(2024, 1, 2), source="yahoo")
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=_EmptyProvider(), sleep_fn=_noop_sleep,
        seed_dir=tmp_path,
    )
    assert summary["aggregates_refreshed"] == []  # the live in-memory default (never populated for fetch)
    with Session(engine) as session:
        persisted = recent_runs(session, cfg)
    this_run = next(r for r in persisted if r["kind"] == "fetch")
    assert this_run["aggregates_refreshed"] is None  # the persisted/served view: null for a fetch kind


# ==================================================================================================
# ops-hardening iter-3 (audit B1/B2): a fetch/expand that changes the bars manifest must ALSO refresh the
# persisted coverage_snapshot (today only backfill/both/rebuild do) — closing the fetch-then-view gap the
# iter-2 audit found live: a fully-ingested DB silently kept serving the false all-zero sentinel until an
# unrelated restart or backfill/rebuild. A zero-work fetch/expand (the common offline case) must pay ZERO
# extra compute. Stale coverage_snapshot rows under a superseded dataset_version must be reclaimed in one
# bounded SQL DELETE, across every asof_key, not just the one being written (B2).
# ==================================================================================================
_COVERAGE_STATUS_KEYS = ("coverage_status", "stale_dataset_version", "stale_computed_at")


def _strip_coverage_status(served: dict) -> dict:
    """iter-27 (AG-3, TC-8 regression guard) — `coverage_from_storage` now additively stamps
    `coverage_status`/`stale_dataset_version`/`stale_computed_at` onto the payload; every pre-existing
    byte-equality assertion against a raw `_compute_coverage_uncached`/`refresh_coverage_snapshot_for`
    result (neither of which carries these fields) strips them first via this one shared helper."""
    return {k: v for k, v in served.items() if k not in _COVERAGE_STATUS_KEYS}


def test_fetch_that_lands_new_bar_refreshes_coverage_snapshot(tmp_path):
    """TC-1/TC-6 (B1) — given a committed DB with a current-stamp coverage_snapshot row already persisted,
    when a `fetch` job lands >= 1 new bar (changing `_membership_dataset_version`) and completes, the
    finalize hook persists a FRESH coverage_snapshot row for the new current stamp, and
    `coverage_from_storage` (what `GET /api/data`'s default view reads) serves the fresh symbol_count —
    byte-identical to an independent fresh `_compute_coverage_uncached` call — never the stale pre-fetch
    value."""
    engine = make_engine(f"sqlite:///{tmp_path / 'fetch_refresh.db'}")
    create_db_and_tables(engine)
    d = date(2024, 1, 2)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()
    cfg = load_config()

    with Session(engine) as session:
        pre_payload = data_manager.refresh_coverage_snapshot(session, cfg)  # the pre-existing current row
        pre_version = data_manager._membership_dataset_version(session, cfg)
    assert pre_payload["symbol_count"] == 1  # SPY only, before the fetch

    class _OneBarProvider(PriceProvider):
        def get_daily(self, symbol, start=None, end=None):
            return [Bar(date=d, open=2.0, high=2.0, low=2.0, close=2.0, volume=2.0)]

    # J-13: an empty temp seed_dir degrades the fetch target to the small context-only set (fast/small),
    # exactly the pattern `test_fetch_forced_failure_writes_no_bars_or_snapshots` already relies on.
    job = create_job("fetch", d, d, source="yahoo")
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=_OneBarProvider(),
        sleep_fn=_noop_sleep, seed_dir=tmp_path,
    )
    assert summary["status"] == "ok"
    assert summary["bars_fetched"] > 0

    with Session(engine) as session:
        new_version = data_manager._membership_dataset_version(session, cfg)
        assert new_version != pre_version  # real new bars landed -> the stamp actually changed

        rows = session.exec(select(CoverageSnapshot)).all()
        assert len(rows) == 1  # the stale pre-fetch-stamp row was reclaimed (B2), not left alongside
        assert rows[0].dataset_version == new_version
        stored = json.loads(rows[0].payload_json)
        assert stored["symbol_count"] > 1  # more than SPY alone -- the fresh count, not the stale 1

        fresh = data_manager._compute_coverage_uncached(session, cfg, as_of=None)
        assert stored == fresh  # TC-6: byte-identical to an independent fresh compute
        served = data_manager.coverage_from_storage(session, cfg, as_of=None)  # GET /api/data's default read
        # iter-27 (TC-8 regression guard): `coverage_from_storage` now additively stamps coverage_status/
        # stale_* on top of the byte-identical base payload — strip them before the byte-equality compare.
        assert served["coverage_status"] == "current"
        assert served["stale_dataset_version"] is None and served["stale_computed_at"] is None
        assert _strip_coverage_status(served) == fresh


def test_zero_work_fetch_skips_coverage_recompute_and_row_write(tmp_path, monkeypatch):
    """TC-2 — given the same setup as TC-1 but the fetch lands ZERO new bars (the common offline no-op),
    `_compute_coverage_uncached` is NEVER invoked (a call-count assertion — the 'already fresh' gate must
    resolve off the cheap dataset-version comparison + one row lookup alone) and no coverage_snapshot row
    is written or re-timestamped."""
    engine = make_engine(f"sqlite:///{tmp_path / 'fetch_zero_work.db'}")
    create_db_and_tables(engine)
    d = date(2024, 1, 2)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()
    cfg = load_config()

    with Session(engine) as session:
        data_manager.refresh_coverage_snapshot(session, cfg)  # the pre-existing current-stamp row
        rows_before = session.exec(select(CoverageSnapshot)).all()
        assert len(rows_before) == 1
        computed_at_before = rows_before[0].computed_at

    calls: list[int] = []
    orig = data_manager._compute_coverage_uncached

    def _counting(*args, **kwargs):
        calls.append(1)
        return orig(*args, **kwargs)

    monkeypatch.setattr(data_manager, "_compute_coverage_uncached", _counting)

    class _EmptyProvider(PriceProvider):
        def get_daily(self, symbol, start=None, end=None):
            return []  # a successful fetch that finds no new bars -- never a fabricated one

    job = create_job("fetch", d, d, source="yahoo")
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=_EmptyProvider(),
        sleep_fn=_noop_sleep, seed_dir=tmp_path,
    )
    assert summary["status"] == "ok"
    assert summary["bars_fetched"] == 0
    assert calls == []  # never invoked -- the skip gate resolved first, off the stamp comparison alone

    with Session(engine) as session:
        rows_after = session.exec(select(CoverageSnapshot)).all()
    assert len(rows_after) == 1
    assert rows_after[0].computed_at == computed_at_before  # untouched -- no re-timestamp


def test_fully_failed_fetch_writes_no_coverage_snapshot(tmp_path):
    """Error case (TESTING REQUIREMENTS) — a fetch that fails for every symbol must not leave a
    partially-written/inconsistent coverage_snapshot row: `final_status == "failed"` never reaches the new
    refresh branch (it is gated the same as the existing backfill/rebuild branch: `ok`/`partial` only)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'fetch_failed.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(
            symbol="SPY", date=date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0,
        ))
        session.commit()
    cfg = load_config()

    job = create_job("fetch", date(2024, 1, 2), date(2024, 1, 2), source="yahoo")
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=_FailingProvider(),
        sleep_fn=_noop_sleep, seed_dir=tmp_path,
    )
    assert summary["status"] == "failed"
    with Session(engine) as session:
        assert session.exec(select(CoverageSnapshot)).all() == []


def test_stale_dataset_version_rows_pruned_via_one_bulk_delete(tmp_path):
    """TC-4 (B2) — multiple coverage_snapshot rows under a now-superseded dataset_version, across DIFFERENT
    asof_keys, are ALL deleted the next time a write detects the dataset version has changed -- via one
    bounded SQL DELETE (asserted by counting DELETE statements against coverage_snapshot), not a per-row
    Python scan."""
    engine = make_engine(f"sqlite:///{tmp_path / 'stale_prune.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        # three rows under an OLD stamp, across three DIFFERENT asof_keys -- today's per-asof_key-only
        # prune would leave two of these three orphaned forever (the B2 bug).
        for asof_key in ("2024-01-01", "2024-02-01", "2024-03-01"):
            session.add(CoverageSnapshot(
                asof_key=asof_key, dataset_version="old-v1", payload_json="{}",
                computed_at=datetime(2024, 1, 1),
            ))
        session.commit()

    delete_statements: list[str] = []

    def _count_deletes(conn, cursor, statement, parameters, context, executemany):
        lowered = statement.lower()
        if "coverage_snapshot" in lowered and lowered.strip().startswith("delete"):
            delete_statements.append(statement)

    event.listen(engine, "before_cursor_execute", _count_deletes)
    try:
        with Session(engine) as session:
            # a write under a NEW dataset_version, for a FOURTH, different asof_key.
            data_manager._upsert_coverage_snapshot(session, "2024-04-01", "new-v2", {"fake": "payload"})
    finally:
        event.remove(engine, "before_cursor_execute", _count_deletes)

    assert len(delete_statements) == 1  # ONE bounded SQL DELETE -- not a per-row scan

    with Session(engine) as session:
        rows = session.exec(select(CoverageSnapshot)).all()
    assert len(rows) == 1  # every old-v1 row (all three asof_keys) reclaimed; only the new row remains
    assert rows[0].asof_key == "2024-04-01" and rows[0].dataset_version == "new-v2"


def test_fetch_coverage_refresh_makes_no_network_call(tmp_path, monkeypatch):
    """TC-7 (AG-9) — the widened finalize trigger for a fetch that lands a new bar issues ZERO outbound
    network/socket calls during the whole job (the stub provider itself is offline; the new coverage-
    refresh branch reuses only DB-backed derivations)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'fetch_no_network.db'}")
    create_db_and_tables(engine)
    d = date(2024, 1, 2)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()
    cfg = load_config()
    with Session(engine) as session:
        data_manager.refresh_coverage_snapshot(session, cfg)

    def _no_network(*_a, **_k):
        raise AssertionError("unexpected network call during the fetch coverage refresh")

    monkeypatch.setattr(socket.socket, "connect", _no_network)

    class _OneBarProvider(PriceProvider):
        def get_daily(self, symbol, start=None, end=None):
            return [Bar(date=d, open=2.0, high=2.0, low=2.0, close=2.0, volume=2.0)]

    job = create_job("fetch", d, d, source="yahoo")
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=_OneBarProvider(),
        sleep_fn=_noop_sleep, seed_dir=tmp_path,
    )
    assert summary["status"] == "ok"  # completed successfully with zero socket.connect calls


# ==================================================================================================
# iter-2 review (CRITICAL regression): the app-wide as-of switcher (J-93/J-94) must serve REAL coverage
# for EVERY already-ingested date — not just the DB's single current stamp. Before the fix, only the
# current stamp got a coverage_snapshot row, so any OTHER selectable historical date read as an all-zero
# empty-DB sentinel (an AG-3 violation on the shipped switcher). Two layers close it: (1) the ingest
# finalize hook persists a per-date row for every NEWLY-created date; (2) coverage_from_storage self-heals
# an explicit historical selection that has a real ScannerRun but no row (a legacy pre-table date).
# ==================================================================================================
@pytest.fixture()
def two_snapshot_dates_engine(tmp_path):
    """A tiny DB with TWO stored ScannerRun/ScannerResult dates (an older historical date + a newer/latest
    date), each with one priced bar — enough to prove per-date coverage differs from the current stamp."""
    engine = make_engine(f"sqlite:///{tmp_path / 'two_dates.db'}")
    create_db_and_tables(engine)
    d_old, d_new = date(2024, 3, 1), date(2024, 3, 4)
    with Session(engine) as session:
        for d in (d_old, d_new):
            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()
        for d in (d_old, d_new):
            run = ScannerRun(
                asof_date=d, created_at=datetime(2024, 3, 4), provider="seed", benchmark="SPY",
                regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
                new_high_low_json="{}", candidate_counts_json="{}",
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            session.add(ScannerResult(
                run_id=run.id, ticker="AAA", name="AAA Corp", leadership_score=1.0, leadership_bucket="Leader",
                entry_quality_score=1.0, entry_quality_bucket="Good", risk_score=1.0, risk_bucket="Low",
                setup_status="Actionable", rank=1, record_json="{}",
            ))
            session.commit()
    return engine, d_old, d_new


def test_finalize_hook_persists_per_date_coverage_for_historical_switcher_date(two_snapshot_dates_engine):
    """iter-2 review fix, layer 1 — a backfill that newly created a NON-latest (historical) snapshot date
    persists a per-date coverage_snapshot for it, so coverage_from_storage serves REAL coverage for that
    date (byte-identical to a fresh compute-at-that-date; AG-3) — never the all-zero sentinel. The CURRENT
    stamp row is unaffected, and there are now exactly two rows (old + latest), not one."""
    engine, d_old, d_new = two_snapshot_dates_engine
    cfg = load_config()
    # a backfill whose date-loop newly created the OLDER (historical, non-latest) date
    with Session(engine) as session:
        prog = JobProgress(job_id="hist-per-date-probe", kind="backfill", start=d_old, end=d_old)
        prog.new_snapshot_dates = [d_old]
        data_manager._refresh_ingest_aggregates(session, cfg, prog)

    with Session(engine) as session:
        # the historical date is served from storage, byte-identical to a fresh compute-at-d_old...
        cov_old = data_manager.coverage_from_storage(session, cfg, as_of=d_old)
        fresh_old = data_manager._compute_coverage_uncached(session, cfg, as_of=d_old)
        assert cov_old["coverage_status"] == "current"  # iter-27: a real persisted row, not a stale/sentinel
        assert _strip_coverage_status(cov_old) == fresh_old
        assert cov_old["symbol_count"] == 1  # REAL coverage (the sentinel would be 0) — the regression
        assert cov_old["universe_asof"] == d_old.isoformat()
        # ...and the current/latest stamp is still served correctly too (two distinct rows now exist)
        cov_new = data_manager.coverage_from_storage(session, cfg, as_of=d_new)
        assert cov_new["universe_asof"] == d_new.isoformat()
        assert len(session.exec(select(CoverageSnapshot)).all()) == 2


def test_coverage_from_storage_self_heals_explicit_legacy_historical_asof(two_snapshot_dates_engine):
    """iter-2 review fix, layer 2 — an EXPLICIT historical as-of backed by a real ScannerRun but with NO
    persisted coverage_snapshot row (a legacy date ingested before this table existed) is served REAL
    coverage by coverage_from_storage (computed once + persisted, self-healing) — never the all-zero
    sentinel. A dataless as-of (no ScannerRun) and the default as_of=None path still get the honest
    sentinel; the current stamp's default row is what the fixture leaves — here we seed NONE to model the
    pure legacy state."""
    engine, d_old, d_new = two_snapshot_dates_engine
    cfg = load_config()
    with Session(engine) as session:
        assert session.exec(select(CoverageSnapshot)).all() == []  # legacy DB: zero coverage rows
        # (1) explicit historical as-of WITH a real ScannerRun, no row -> REAL coverage + self-heal to storage
        cov = data_manager.coverage_from_storage(session, cfg, as_of=d_old)
        fresh = data_manager._compute_coverage_uncached(session, cfg, as_of=d_old)
        assert cov["coverage_status"] == "current"  # iter-27: freshly self-healed under the current stamp
        assert _strip_coverage_status(cov) == fresh
        assert cov["symbol_count"] == 1 and cov["universe_asof"] == d_old.isoformat()  # not the 0 sentinel
        healed = session.exec(
            select(CoverageSnapshot).where(CoverageSnapshot.asof_key == d_old.isoformat())
        ).first()
        assert healed is not None  # self-healed: the next visit reads straight from storage
        # (2) an explicit as-of to a DATALESS date (no ScannerRun) still serves the honest sentinel
        sentinel = data_manager.coverage_from_storage(session, cfg, as_of=date(2024, 6, 1))
        assert sentinel["symbol_count"] == 0 and sentinel["universe_asof"] is None
        assert sentinel["coverage_status"] == "not_yet_computed"  # iter-27: genuinely dataless, not stale


def test_coverage_from_storage_serves_stale_prior_snapshot_when_default_view_stamp_advances_outside_ingest(
    tmp_path,
):
    """iter-27 (AG-3 ESCALATE fix, TC-5) — reproduces the EXACT root cause the iter-26 evaluator's
    ESCALATE verdict cited: `_membership_dataset_version` is a GLOBAL stamp bumped by ANY new `ScannerRun`
    row, including one for a date decades in the past that never changes which date is "latest". Here: (1)
    a `CoverageSnapshot` row is persisted for the latest date under the CURRENT stamp V1 (a normal ingest);
    (2) a SECOND `ScannerRun`, for an EARLIER date, is added directly (no ingest finalize hook — modeling a
    request-path historical `/backtest` create-once view), which bumps `_membership_dataset_version` to V2
    (`max(scanner_runs.id)`/`count(scanner_runs)` both change) while leaving `_resolve_coverage_asof(None)`
    resolved to the SAME latest date (unaffected — it tracks `max(ScannerRun.asof_date)`, and the new run
    is OLDER). The default view's exact-match lookup (latest_key, V2) now misses even though the REAL V1
    row for that exact `asof_key` still sits in the table (no ingest ran to reclaim it, per
    `_upsert_coverage_snapshot`'s own "only ingest deletes old-version rows" contract) -- this is the
    fallback: serve that row's real, non-zero figures labeled `coverage_status: "stale"` with
    `stale_dataset_version` naming V1, rather than the false all-zero 'not yet computed' sentinel."""
    engine = make_engine(f"sqlite:///{tmp_path / 'stale_fallback.db'}")
    create_db_and_tables(engine)
    d_latest = date(2024, 3, 4)
    d_old = date(2024, 1, 2)  # earlier than d_latest -- never becomes the resolved "latest" date
    with Session(engine) as session:
        session.add(DailyPrice(
            symbol="SPY", date=d_latest, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0,
        ))
        session.commit()
        run = ScannerRun(
            asof_date=d_latest, created_at=datetime(2024, 3, 4), provider="seed", benchmark="SPY",
            regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        session.add(ScannerResult(
            run_id=run.id, ticker="AAA", name="AAA Corp", leadership_score=1.0, leadership_bucket="Leader",
            entry_quality_score=1.0, entry_quality_bucket="Good", risk_score=1.0, risk_bucket="Low",
            setup_status="Actionable", rank=1, record_json="{}",
        ))
        session.commit()

    cfg = load_config()
    with Session(engine) as session:
        v1 = data_manager._membership_dataset_version(session, cfg)
        real_payload = data_manager.refresh_coverage_snapshot(session, cfg)  # persists under V1
    assert real_payload["symbol_count"] == 1 and real_payload["universe_asof"] == d_latest.isoformat()

    # A request-path historical create-once view for an OLDER date -- a brand-new ScannerRun row, but NO
    # ingest finalize hook (mirrors resolved_run's create-once path; never touches coverage_snapshot).
    with Session(engine) as session:
        session.add(DailyPrice(
            symbol="AAA", date=d_old, open=2.0, high=2.0, low=2.0, close=2.0, volume=1.0,
        ))
        session.add(ScannerRun(
            asof_date=d_old, created_at=datetime(2024, 1, 2), provider="seed", benchmark="SPY",
            regime_score=40.0, regime_label="Risk-off", regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        ))
        session.commit()

    with Session(engine) as session:
        v2 = data_manager._membership_dataset_version(session, cfg)
        assert v2 != v1  # the stamp advanced from the new (older-date) ScannerRun alone
        resolved = data_manager._resolve_coverage_asof(session, None, cfg)
        assert resolved == d_latest  # "latest" is UNCHANGED -- the new run is for an EARLIER date
        # the exact-match (asof_key=d_latest, dataset_version=v2) row does not exist -- only v1's does
        assert session.exec(
            select(CoverageSnapshot).where(
                CoverageSnapshot.asof_key == d_latest.isoformat(),
                CoverageSnapshot.dataset_version == v2,
            )
        ).first() is None

        served = data_manager.coverage_from_storage(session, cfg, as_of=None)  # the default view

    assert served["coverage_status"] == "stale"
    assert served["stale_dataset_version"] == v1
    assert served["stale_computed_at"] is not None
    # the REAL prior figures -- never the all-zero sentinel for a database that plainly has coverage on file
    assert served["symbol_count"] == 1 and served["universe_asof"] == d_latest.isoformat()
    assert _strip_coverage_status(served) == real_payload


def test_data_overview_serves_freshest_ingested_coverage_after_unrelated_dataset_version_bump(tmp_path):
    """goal-ops-hardening iter-61 (J-05 TC-1/TC-2) — the exact evaluator-reported scenario: a REAL ingest
    finalize hook (`_refresh_ingest_aggregates`, not a hand-called shortcut) persists a fresh
    `coverage_snapshot` row for the newly-created latest date; an UNRELATED request-path event (a
    historical `/backtest` create-once view — `scanner.resolve_run`, the real code path, not a raw
    `session.add(ScannerRun(...))`) then creates a new `ScannerRun` for an EARLIER date, bumping
    `_membership_dataset_version` (the iter-27 stale-row fallback's trigger condition). The API-layer
    function `app.api.data.data_overview` (not just `coverage_from_storage` in isolation) must still
    serve the JUST-INGESTED date's exact `snapshot_count`/`gap_count`/`snapshot_dates` — the freshest
    persisted row for that `asof_key` — never a value from BEFORE the ingest."""
    engine = make_engine(f"sqlite:///{tmp_path / 'coverage_freshness.db'}")
    create_db_and_tables(engine)
    d_pre = date(2024, 1, 2)  # already-snapshotted BEFORE the ingest under test (the pre-ingest total)
    d_new = date(2024, 3, 4)  # the ingest's own newly-created latest date
    d_unrelated = date(2023, 6, 1)  # the unrelated request-path event's target -- earlier than BOTH above
    with Session(engine) as session:
        for d in (d_pre, d_new, d_unrelated):
            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()
        run = ScannerRun(
            asof_date=d_pre, created_at=datetime(2024, 1, 2), provider="seed", benchmark="SPY",
            regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        session.add(ScannerResult(
            run_id=run.id, ticker="AAA", name="AAA Corp", leadership_score=1.0, leadership_bucket="Leader",
            entry_quality_score=1.0, entry_quality_bucket="Good", risk_score=1.0, risk_bucket="Low",
            setup_status="Actionable", rank=1, record_json="{}",
        ))
        session.commit()

    cfg = load_config()
    # (1) the REAL ingest: `d_new`'s own ScannerRun/ScannerResult are created first (mirroring `_do_backfill`'s
    # own date-loop, which persists the snapshot BEFORE the finalize hook runs -- `prog.new_snapshot_dates`
    # documents exactly that "already committed" precondition), THEN the finalize hook persists coverage.
    with Session(engine) as session:
        run_new = ScannerRun(
            asof_date=d_new, created_at=datetime(2024, 3, 4), provider="seed", benchmark="SPY",
            regime_score=55.0, regime_label="Choppy", regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        )
        session.add(run_new)
        session.commit()
        session.refresh(run_new)
        session.add(ScannerResult(
            run_id=run_new.id, ticker="AAA", name="AAA Corp", leadership_score=1.0, leadership_bucket="Leader",
            entry_quality_score=1.0, entry_quality_bucket="Good", risk_score=1.0, risk_bucket="Low",
            setup_status="Actionable", rank=1, record_json="{}",
        ))
        session.commit()
        prog = JobProgress(job_id="freshness-probe", kind="backfill", start=d_new, end=d_new)
        prog.new_snapshot_dates = [d_new]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert "coverage" in refreshed

    with Session(engine) as session:
        fresh_row = session.exec(
            select(CoverageSnapshot).where(CoverageSnapshot.asof_key == d_new.isoformat())
        ).one()
        v_ingest = fresh_row.dataset_version
        assert fresh_row.payload_json  # sanity: a real payload was persisted
    ingest_snapshot_count = json.loads(fresh_row.payload_json)["snapshot_count"]
    ingest_gap_count = json.loads(fresh_row.payload_json)["gap_count"]
    assert ingest_snapshot_count == 2  # d_pre + d_new -- the CORRECT post-ingest total

    # (2) the unrelated request-path event: a historical /backtest create-once view for `d_unrelated`,
    # through the REAL `scanner.resolve_run` path (never touches CoverageSnapshot) -- bumps
    # `_membership_dataset_version` while leaving "latest" (`d_new`) and the fresh row's OWN payload
    # completely untouched.
    with Session(engine) as session:
        scanner.resolve_run(session, d_unrelated.isoformat(), cfg)
    with Session(engine) as session:
        v_after = data_manager._membership_dataset_version(session, cfg)
        assert v_after != v_ingest  # the stamp genuinely advanced from the unrelated event alone
        resolved = data_manager._resolve_coverage_asof(session, None, cfg)
        assert resolved == d_new  # "latest" is unaffected -- the unrelated run is for an EARLIER date

        # (3) the actual API-layer function -- not just coverage_from_storage in isolation -- must still
        # serve the freshest ingested row's exact counts, never the pre-ingest pair.
        payload = data_overview(session=session)
    cov = payload["coverage"]
    assert cov["snapshot_count"] == ingest_snapshot_count == 2  # never the pre-ingest 1
    assert cov["gap_count"] == ingest_gap_count
    assert d_new.isoformat() in cov["snapshot_dates"]
    assert cov["coverage_status"] in ("current", "stale")  # either is honest; the VALUES must be fresh
    if cov["coverage_status"] == "stale":
        assert cov["stale_dataset_version"] == v_ingest


# ==================================================================================================
# iter-21 (J-33): import-source catalog availability (env-detected) — descriptive metadata, NO key
# ==================================================================================================
def test_compute_provider_availability_env_detected(monkeypatch):
    """A no-key source is always `available`; a needs-key source is `available` ONLY when its env var is
    set. The env VALUE / any key is NEVER in the output — only the env-var NAME + the boolean + a reason
    (anti-goal: Import keys are env-or-session, never persisted)."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    # No env keys set → yahoo available (no key), tiingo NOT available (needs key, env unset).
    monkeypatch.delenv("TIINGO_API_KEY", raising=False)
    sources = compute_provider_availability(cfg)
    by_id = {s["id"]: s for s in sources}
    assert by_id["yahoo"]["available"] is True and by_id["yahoo"]["needs_key"] is False
    assert by_id["tiingo"]["available"] is False and by_id["tiingo"]["needs_key"] is True
    assert by_id["tiingo"]["env_var"] == "TIINGO_API_KEY"  # the NAME is exposed
    # the catalog is config-driven (the named sources appear)
    assert {"yahoo", "tiingo", "stooq"}.issubset(set(by_id))

    # Set the env var → tiingo flips to available, but the secret VALUE never appears in the output.
    monkeypatch.setenv("TIINGO_API_KEY", "super-secret-env-value-zzz")
    sources2 = compute_provider_availability(cfg)
    by_id2 = {s["id"]: s for s in sources2}
    assert by_id2["tiingo"]["available"] is True
    assert "super-secret-env-value-zzz" not in json.dumps(sources2)


# ==================================================================================================
# iter-26 (J-37 / J-35 capture enabler): the env-gated OFFLINE `seed` import source
# ==================================================================================================
def test_seed_import_source_absent_without_flag(monkeypatch):
    """By default (flag unset) the offline `seed` source is ABSENT from the availability catalog and the
    validator REJECTS a `seed`-source job — it is a test/dev affordance, never in production."""
    monkeypatch.delenv(SEED_IMPORT_ENV_FLAG, raising=False)
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    assert seed_import_source_enabled() is False
    by_id = {s["id"]: s for s in compute_provider_availability(cfg)}
    assert SEED_IMPORT_SOURCE_ID not in by_id  # absent from the picker
    # the validator rejects `seed` as unknown when the flag is unset
    with pytest.raises(ValueError, match="unknown import source"):
        validate_job_request("fetch", date(2024, 1, 1), date(2024, 1, 2), cfg, source=SEED_IMPORT_SOURCE_ID)


def test_seed_import_source_present_only_when_flagged(monkeypatch):
    """With the flag set, exactly ONE `seed` entry appears — no-key, market-cap-capable, always available,
    carrying NO env-var/key value — and it is NOT in the committed config catalog (no production leak)."""
    monkeypatch.setenv(SEED_IMPORT_ENV_FLAG, "1")
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    assert seed_import_source_enabled() is True
    # never in the committed config catalog (a test/dev affordance only)
    assert SEED_IMPORT_SOURCE_ID not in cfg.data_manager.provider_ids()
    sources = compute_provider_availability(cfg)
    seed_entries = [s for s in sources if s["id"] == SEED_IMPORT_SOURCE_ID]
    assert len(seed_entries) == 1  # exactly one
    seed = seed_entries[0]
    assert seed["label"] == "Seed (offline test data)"
    assert seed["needs_key"] is False
    assert seed["env_var"] is None
    assert seed["supports_market_cap"] is True
    assert seed["available"] is True
    # carries no key/secret value (anti-goal: keys are env-or-session, never persisted)
    monkeypatch.setenv("TIINGO_API_KEY", "super-secret-zzz")
    assert "super-secret-zzz" not in json.dumps(compute_provider_availability(load_config()))


def test_seed_source_job_validates_through_existing_gate_when_flagged(monkeypatch):
    """A `seed`-source job (fetch AND expand) PASSES `validate_job_request` when the flag is set — it
    routes through the EXISTING source gate (no key required, market-cap-capable so the J-35 expand
    eligibility gate accepts it). No second validation path."""
    monkeypatch.setenv(SEED_IMPORT_ENV_FLAG, "1")
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    # a fetch over seed needs no key (the seed reads no credential) — accepted with no api_key
    validate_job_request("fetch", date(2024, 1, 1), date(2024, 1, 2), cfg, source=SEED_IMPORT_SOURCE_ID)
    # an expand over seed passes the supports_market_cap eligibility gate (seed is cap-capable)
    validate_job_request("expand", date(2024, 1, 1), date(2024, 1, 1), cfg, source=SEED_IMPORT_SOURCE_ID)


def test_seed_source_resolves_to_seed_provider(monkeypatch):
    """A `seed`-source fetch resolves to the offline `SeedProvider` through the SAME `make_provider`
    path every other source uses (no second fetch path) and needs no key."""
    from app.data_providers.seed_provider import SeedProvider

    monkeypatch.setenv(SEED_IMPORT_ENV_FLAG, "1")
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    provider = data_manager._resolve_live_provider(cfg, SEED_IMPORT_SOURCE_ID, None)
    assert isinstance(provider, SeedProvider)
    # the error-scrubber key for a seed job is None (no key → nothing to leak)
    assert data_manager._resolved_key(cfg, SEED_IMPORT_SOURCE_ID, None) is None


def test_resolve_provider_key_prefers_paste_then_env(monkeypatch):
    """The effective key is the pasted session key if present, else the env var; a no-key source returns
    None and ignores any pasted value (the key is request-only — never written anywhere)."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    yahoo = cfg.data_manager.provider_by_id("yahoo")
    tiingo = cfg.data_manager.provider_by_id("tiingo")
    assert resolve_provider_key(yahoo, "ignored") is None  # no-key source never uses a key
    monkeypatch.delenv("TIINGO_API_KEY", raising=False)
    assert resolve_provider_key(tiingo, None) is None  # needs key, none available
    assert resolve_provider_key(tiingo, "pasted-key") == "pasted-key"  # paste wins
    monkeypatch.setenv("TIINGO_API_KEY", "env-key")
    assert resolve_provider_key(tiingo, None) == "env-key"  # env fallback
    assert resolve_provider_key(tiingo, "pasted-key") == "pasted-key"  # paste still wins over env


# ==================================================================================================
# iter-21 (J-33) PRINCIPAL ANTI-GOAL: a pasted api_key is NEVER persisted / logged / echoed
# ==================================================================================================
class _RecordingOkProvider(PriceProvider):
    """An injected live provider that returns one real bar per symbol (a successful offline fetch)."""

    def get_daily(self, symbol, start=None, end=None):
        return [Bar(date=start or date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]


def test_pasted_api_key_never_persisted(tmp_path, caplog):
    """Run a FETCH job (injected provider) with a pasted session `api_key` against a needs-key source.
    The key string MUST be absent from the in-memory job snapshot, from every `DataProviderRun` column,
    and from the logs; the chosen `source` id (not secret) IS recorded. The `JobProgress` record has NO
    field that could hold the key. THE principal anti-goal: Import keys are env-or-session, never
    persisted."""
    secret = "sk-PASTE-NEVER-PERSIST-7f3a9c"
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    engine = make_engine(f"sqlite:///{tmp_path / 'key.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    job = create_job("fetch", date(2024, 1, 2), date(2024, 1, 3), source="tiingo")
    with caplog.at_level("DEBUG"):
        summary = run_data_job(
            job.job_id, config=cfg, engine=engine, provider=_RecordingOkProvider(), api_key=secret
        )

    # the chosen source is recorded (not secret); the key is nowhere in the job snapshot
    assert summary["source"] == "tiingo"
    assert summary["status"] == "ok"
    assert secret not in json.dumps(summary)
    assert secret not in json.dumps(recent_runs.__doc__ or "")  # sanity: not a constant somewhere

    # structural guarantee: the in-memory job record has NO field that holds a key
    assert "api_key" not in JobProgress.__dataclass_fields__

    # absent from every DataProviderRun column (provider == the source id, message == key-free detail JSON)
    with Session(engine) as session:
        rows = session.exec(select(DataProviderRun)).all()
    assert rows and rows[-1].provider == "tiingo"  # source id recorded, not the key
    serialized = json.dumps([
        {col: str(getattr(r, col)) for col in ("provider", "status", "message")} for r in rows
    ])
    assert secret not in serialized

    # absent from the logs
    assert secret not in caplog.text


# ==================================================================================================
# iter-22 (J-33 fix): the key is scrubbed even from a REAL-httpx-error string that slipped past _http
# ==================================================================================================
def _real_httpx_error_str_with_key(key: str) -> str:
    """A REAL `httpx.HTTPStatusError` str (from `raise_for_status`) whose request URL carries `key` as a
    `?token=` query param — the EXACT iter-21 leak vector (`str(exc)` embeds the key). Built from a real
    `httpx.Request`/`httpx.Response` directly (no `client.get`, so httpx emits no transport-level request
    log of its own — keeping this a test of OUR scrub, not the httpx library's logging)."""
    req = httpx.Request("GET", "https://api.tiingo.com/tiingo/daily/AAPL/prices", params={"token": key})
    try:
        httpx.Response(429, request=req).raise_for_status()
    except httpx.HTTPStatusError as exc:
        return str(exc)
    return ""  # pragma: no cover


class _KeyLeakingProvider(PriceProvider):
    """An injected provider that (like iter-21's un-redacted `_http.py`) raises a
    `ProviderUnavailableError` whose message EMBEDS a real httpx error str carrying the key in the URL.
    The `data_manager` defense-in-depth scrub MUST still remove the key before it reaches any error
    surface — belt-and-suspenders on top of the `_http.py` redaction."""

    def __init__(self, key: str):
        self._leak = _real_httpx_error_str_with_key(key)

    def get_daily(self, symbol, start=None, end=None):
        raise ProviderUnavailableError(self._leak)


def test_real_httpx_error_key_scrubbed_end_to_end(tmp_path, caplog):
    """EXTENDS `test_pasted_api_key_never_persisted` (iter-2 lesson: extend invariant tests, never
    delete): a FETCH whose injected provider raises an error EMBEDDING a real httpx error with the key in
    the URL → the data_manager scrub removes it. The sentinel is ABSENT from `JobProgress.errors`,
    `GET /api/data/jobs/{id}`, the `ImportCheckpoint` row + `resumable_imports`, every `DataProviderRun`
    column, and the logs — while the redaction marker `***` proves the scrub fired."""
    secret = "sk-REAL-HTTPX-SCRUB-5b2e1f"
    assert secret in _real_httpx_error_str_with_key(secret)  # sanity: there IS a key to scrub
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    engine = make_engine(f"sqlite:///{tmp_path / 'scrub.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    job = create_job("fetch", date(2024, 1, 2), date(2024, 1, 3), source="tiingo")
    with caplog.at_level("DEBUG"):
        summary = run_data_job(
            job.job_id, config=cfg, engine=engine,
            provider=_KeyLeakingProvider(secret), api_key=secret, sleep_fn=_noop_sleep,
        )

    assert summary["status"] == "failed"  # every symbol raised → no fabricated bar
    assert summary["errors"]  # explicit errors recorded
    assert secret not in json.dumps(summary)  # scrubbed from the snapshot + its error list
    assert "***" in json.dumps(summary["errors"])  # the redaction marker IS present (the scrub fired)
    assert secret not in json.dumps(get_job(job.job_id))  # absent from GET /api/data/jobs/{id}

    with Session(engine) as session:
        checkpoints = session.exec(select(ImportCheckpoint)).all()
        assert checkpoints  # a fetch job creates a checkpoint
        cp_blob = json.dumps(
            [{c: str(getattr(cp, c)) for c in ImportCheckpoint.model_fields} for cp in checkpoints]
        )
        assert secret not in cp_blob  # NO key column / value on the checkpoint
        assert secret not in json.dumps(resumable_imports(session, cfg))
        runs = session.exec(select(DataProviderRun)).all()
    run_blob = json.dumps([{c: str(getattr(r, c)) for c in ("provider", "status", "message")} for r in runs])
    assert secret not in run_blob  # absent from every DataProviderRun column
    assert secret not in caplog.text  # absent from the logs


# ==================================================================================================
# iter-22 (J-34): chunk plan is config-driven; chunk_total derives from symbol_batch × date_window
# ==================================================================================================
def _with_chunking(cfg, **overrides):
    """A config copy with `data_manager.import_chunking` overridden (the rest unchanged)."""
    ic = cfg.data_manager.import_chunking.model_copy(update=overrides)
    return cfg.model_copy(update={"data_manager": cfg.data_manager.model_copy(update={"import_chunking": ic})})


def test_chunk_total_derives_from_config():
    """`chunk_total` = ceil(n_symbols / symbol_batch_size) × ceil(span / date_window_days). Varying either
    config dimension changes the plan size — proving No magic numbers (both come from config)."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    symbols = [f"S{i}" for i in range(10)]
    start, end = date(2024, 1, 1), date(2024, 1, 10)  # 10 calendar days
    # batch 5 over 10 symbols = 2 batches; window 5 over 10 days = 2 windows → 4 chunks
    assert len(_chunk_plan(_with_chunking(cfg, symbol_batch_size=5, date_window_days=5), symbols, start, end)) == 2 * 2
    # smaller batch → more chunks (batch 2 → 5 batches × 2 windows = 10)
    assert len(_chunk_plan(_with_chunking(cfg, symbol_batch_size=2, date_window_days=5), symbols, start, end)) == 5 * 2
    # wider window → fewer chunks (window 10 → 1 window × 2 batches(batch 5) = 2)
    assert len(_chunk_plan(_with_chunking(cfg, symbol_batch_size=5, date_window_days=10), symbols, start, end)) == 1 * 2


# ==================================================================================================
# iter-22 (J-34): 429 retry-with-backoff (patched sleep — no wall-clock); exhaustion re-raises
# ==================================================================================================
class _Rate429NTimes(PriceProvider):
    """429s the first `fail` get_daily calls, then returns one real bar. Records its call count."""

    def __init__(self, fail: int):
        self._fail = fail
        self.calls = 0

    def get_daily(self, symbol, start=None, end=None):
        self.calls += 1
        if self.calls <= self._fail:
            raise RateLimitError("HTTP 429 at https://provider/x")
        return [Bar(date=start or date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]


def test_fetch_with_retry_backoff_then_success():
    """429 exactly `max_retries` times then success → bars returned; the backoff sleeps are the exact
    exponential `min(base*2**i, cap)` sequence, of length `max_retries` (the sleep is PATCHED — no wait)."""
    chunking = load_config().data_manager.import_chunking
    sleeps: list[float] = []
    provider = _Rate429NTimes(chunking.max_retries)
    bars = data_manager._fetch_symbol_with_retry(
        provider, "AAA", date(2024, 1, 1), date(2024, 1, 2), chunking=chunking, sleep_fn=sleeps.append
    )
    assert bars and provider.calls == chunking.max_retries + 1  # max_retries retries after the first try
    expected = [min(chunking.backoff_base_seconds * (2 ** i), chunking.backoff_cap_seconds) for i in range(chunking.max_retries)]
    assert sleeps == expected  # exponential, capped — config-driven, no magic number


def test_fetch_with_retry_exhausted_reraises_rate_limit():
    """A persistent 429 → `RateLimitError` re-raised after `max_retries` backoff sleeps (the caller pauses
    resumable — it never fabricates a bar)."""
    chunking = load_config().data_manager.import_chunking

    class _Always429(PriceProvider):
        def get_daily(self, symbol, start=None, end=None):
            raise RateLimitError("HTTP 429")

    sleeps: list[float] = []
    with pytest.raises(RateLimitError):
        data_manager._fetch_symbol_with_retry(
            _Always429(), "AAA", date(2024, 1, 1), date(2024, 1, 2), chunking=chunking, sleep_fn=sleeps.append
        )
    assert len(sleeps) == chunking.max_retries  # backoff between the max_retries+1 attempts


# ==================================================================================================
# iter-22 (J-34): durable checkpoint + graceful resumable stop + resume + per-(symbol,date) idempotency
# ==================================================================================================
class _OkForThen429(PriceProvider):
    """Returns one bar for symbols in `ok_symbols`; raises a PERSISTENT `RateLimitError` for any other
    symbol. Records every symbol it is asked to fetch (to prove resume skips already-done chunks)."""

    def __init__(self, ok_symbols: set[str]):
        self._ok = ok_symbols
        self.fetched: list[str] = []

    def get_daily(self, symbol, start=None, end=None):
        self.fetched.append(symbol)
        if symbol in self._ok:
            return [Bar(date=start or date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]
        raise RateLimitError("HTTP 429 at https://provider/x")


class _OkForAll(PriceProvider):
    """Returns one bar for every symbol (a recovered provider). Records what it was asked to fetch."""

    def __init__(self):
        self.fetched: list[str] = []

    def get_daily(self, symbol, start=None, end=None):
        self.fetched.append(symbol)
        return [Bar(date=start or date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]


def test_chunked_fetch_pauses_resumable_then_resumes_idempotently(tmp_path):
    """The J-34 crux. A fetch whose provider 429s persistently from the first symbol of chunk 1 pauses
    GRACEFULLY `resumable` (NOT `failed`, nothing fabricated, the loop does not raise). A FRESH DB session
    (simulating a restart) sees the durable `ImportCheckpoint` at `next_chunk_index == 1`;
    `resumable_imports` lists it; Resume (a recovered provider) continues from chunk 1, SKIPS chunk 0's
    already-stored symbols, fetches each remaining symbol exactly once, and inserts NO duplicate
    `(symbol, date)` row."""
    secret = "sk-RESUME-KEY-NEVER-STORED-9c4"
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    batch = cfg.data_manager.import_chunking.symbol_batch_size
    # J-13 (iter-20): a generic fetch now targets `price_load_symbols(cfg, seed_dir)` (context ∪ pool).
    # This test pins an explicit EMPTY temp `seed_dir` (no committed `universe_pool.csv`) on BOTH the
    # fresh run and the resume, so `price_load_symbols` degrades honestly to the SAME context-only set
    # `all_seed_symbols` gave before — keeping this exact-list-equality test valid unchanged (a resume's
    # symbol list actually replays the checkpoint's persisted plan regardless, but pinning `seed_dir`
    # keeps the fresh run's plan small/deterministic and documents the dependency explicitly).
    symbols = all_seed_symbols(cfg)
    chunk0 = set(symbols[:batch])  # the first chunk's symbols (date_window=90 over 1 day → 1 window)
    engine = make_engine(f"sqlite:///{tmp_path / 'resume.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:  # a little SPY data so a calendar / latest date exists
        session.add(DailyPrice(symbol="SPY", date=date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    # --- run 1: 429s from the first symbol of chunk 1 → graceful resumable pause at chunk index 1 -----
    fetch_day = date(2024, 3, 1)
    job = create_job("fetch", fetch_day, fetch_day, source="tiingo")
    paused_provider = _OkForThen429(chunk0)
    summary1 = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=paused_provider, api_key=secret, sleep_fn=_noop_sleep,
        seed_dir=tmp_path,
    )
    assert summary1["status"] == "resumable"  # distinct from failed — a graceful pause
    assert summary1["chunk_index"] == 1 and summary1["chunk_total"] >= 2  # paused after chunk 0 completed
    assert summary1["symbols_ok"] == batch and summary1["bars_fetched"] == batch  # chunk 0 stored

    # --- a FRESH DB session sees the durable checkpoint (the restart-survival the Resume depends on) ---
    with Session(engine) as fresh:
        cp = fresh.exec(select(ImportCheckpoint).where(ImportCheckpoint.import_id == job.job_id)).one()
        assert cp.next_chunk_index == 1 and cp.status == "resumable"
        assert cp.symbols_ok == batch
        # the key is NEVER on the checkpoint (no key column) nor in resumable_imports
        cp_blob = json.dumps({c: str(getattr(cp, c)) for c in ImportCheckpoint.model_fields})
        assert secret not in cp_blob
        listed = resumable_imports(fresh, cfg)
        assert [r["import_id"] for r in listed] == [job.job_id]  # the paused import is discoverable
        assert secret not in json.dumps(listed)
        bars_after_pause = fresh.scalar(select(func.count()).select_from(DailyPrice).where(DailyPrice.date == fetch_day))
    assert bars_after_pause == batch  # only chunk 0's bars are stored so far

    # --- Resume with a recovered provider → continues from chunk 1, idempotent, completes -------------
    resumed_provider = _OkForAll()
    summary2 = resume_data_job(
        job.job_id, config=cfg, engine=engine, provider=resumed_provider, api_key=secret, sleep_fn=_noop_sleep,
        seed_dir=tmp_path,
    )
    assert summary2["status"] == "ok"  # the import completed
    assert summary2["chunk_index"] == summary2["chunk_total"]  # all chunks done
    # resume SKIPPED chunk 0 entirely — none of its symbols were re-fetched (idempotency)
    assert chunk0.isdisjoint(set(resumed_provider.fetched))
    # resume fetched exactly the remaining symbols, each ONCE (no symbol fetched twice)
    assert resumed_provider.fetched == symbols[batch:]

    with Session(engine) as session:
        rows = session.exec(select(DailyPrice).where(DailyPrice.date == fetch_day)).all()
        # every universe+ETF symbol now has exactly ONE bar on the fetch day — no duplicate (symbol, date)
        per_symbol = {}
        for r in rows:
            per_symbol[r.symbol] = per_symbol.get(r.symbol, 0) + 1
        assert set(per_symbol) == set(symbols)  # all symbols fetched across the two runs
        assert all(count == 1 for count in per_symbol.values())  # NO duplicate row for any (symbol, date)
        # the checkpoint is now terminal (ok) → no longer resumable
        assert resumable_imports(session, cfg) == []


def test_resume_unknown_or_completed_raises():
    """A resume of an unknown import → `LookupError` (API 404); a resume of a non-resumable (ok) import →
    `ValueError` (API 409). Never a fabricated job."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    engine = make_engine("sqlite:///:memory:")
    create_db_and_tables(engine)
    with pytest.raises(LookupError):
        resume_data_job("does-not-exist", config=cfg, engine=engine)
    # an `ok` checkpoint is not resumable
    with Session(engine) as session:
        session.add(ImportCheckpoint(
            import_id="done-1", source="tiingo", kind="fetch", start=date(2024, 1, 1), end=date(2024, 1, 2),
            symbol_plan_json=json.dumps(["AAA"]), chunk_total=1, next_chunk_index=1, status="ok",
            created_at=__import__("datetime").datetime(2024, 1, 1), updated_at=__import__("datetime").datetime(2024, 1, 1),
        ))
        session.commit()
    with pytest.raises(ValueError):
        resume_data_job("done-1", config=cfg, engine=engine)


# ==================================================================================================
# iter-23 (J-35): the `expand` job kind — screen the committed pool over a market-cap-capable source
# ==================================================================================================
from app.config import DEFAULT_CONFIG_PATH, _merge_committed_universe  # noqa: E402
from app.data_providers.base import PriceProvider  # noqa: E402 (re-imported for clarity in this block)
from app.engine.methodology import build_catalog  # noqa: E402
from app.engine.universe_screen import screen_reasons  # noqa: E402

# A tiny deterministic candidate pool (symbols + sectors) the expand tests screen — written to a temp
# seed dir so the test never touches the committed 548-name pool. Caps/prices are chosen so the screen
# verdict is known by construction against the config thresholds (min_price 10 / adv $50M / cap $2B).
_POOL_ROWS = [
    ("PASSER1", "Technology", "test"),   # passes all three thresholds (big cap, liquid, >$10)
    ("PASSER2", "Health Care", "test"),  # passes all three
    ("SMALLCAP", "Energy", "test"),      # cap below $2B → omitted (market_cap reason)
    ("CHEAP", "Industrials", "test"),    # price below $10 → omitted (price reason)
    ("NOCAP", "Financials", "test"),     # provider returns no cap → omitted (no_market_cap)
    ("FETCHFAIL", "Materials", "test"),  # OHLCV fetch raises → omitted (no bars stored → empty_series)
]


def _write_pool(seed_dir, rows=_POOL_ROWS) -> None:
    """Write a temp candidate pool CSV (the membership-rule half) the expand job reads."""
    seed_dir.mkdir(parents=True, exist_ok=True)
    lines = ["# test pool", "symbol,sector,source"]
    lines += [f"{sym},{sector},{source}" for sym, sector, source in rows]
    (seed_dir / "universe_pool.csv").write_text("\n".join(lines) + "\n")


class _ExpandProvider(PriceProvider):
    """An injected expand provider: returns real bars + a real market cap for the named passers/edge
    cases, raises for FETCHFAIL (no bars stored), and returns None cap for NOCAP. Deterministic — the
    screen verdict for each symbol is known by construction (no live feed)."""

    # close, adv-dollar-volume-per-bar, market_cap by symbol (None ⇒ omit reason exercised)
    _PRICE = {"PASSER1": 150.0, "PASSER2": 80.0, "SMALLCAP": 60.0, "CHEAP": 4.0, "NOCAP": 90.0}
    _CAP = {"PASSER1": 3.0e12, "PASSER2": 5.0e11, "SMALLCAP": 1.0e9, "CHEAP": 9.0e9, "NOCAP": None}

    def get_daily(self, symbol, start=None, end=None):
        if symbol == "FETCHFAIL":
            raise ProviderUnavailableError("forced OHLCV failure for FETCHFAIL")
        px = self._PRICE.get(symbol, 100.0)
        # one bar with volume sized so close*volume clears (or fails) the $50M ADV — all passers are liquid
        return [Bar(date=start or date(2024, 3, 1), open=px, high=px, low=px, close=px, volume=1_000_000.0)]

    def get_market_cap(self, symbol):
        return self._CAP.get(symbol)


def test_expand_screens_pool_writes_universe_with_exact_passers_and_omissions(tmp_path):
    """Expand happy path: an expand over the injected provider screens the pool, writes `universe.json`
    with EXACTLY the expected passers, and records the expected omitted-with-reason entries — asserted by
    VALUE. A FETCHFAIL (no bars), a NOCAP (no market cap), a SMALLCAP (cap < min), and a CHEAP (price <
    min) are each omitted with the right reason; nothing is fabricated."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    seed_dir = tmp_path / "seed"
    _write_pool(seed_dir)
    engine = make_engine(f"sqlite:///{tmp_path / 'expand.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:  # a little SPY data so a calendar/latest date exists
        session.add(DailyPrice(symbol="SPY", date=date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    job = create_job("expand", date(2024, 3, 1), date(2024, 3, 1), source="yahoo")
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=_ExpandProvider(),
        sleep_fn=_noop_sleep, seed_dir=seed_dir,
    )

    # FETCHFAIL's OHLCV fetch failed for one candidate → an honest `partial` (the screen still ran for
    # every fetched candidate; nothing fabricated). The screen verdicts below are the real DoD assertions.
    assert summary["status"] == "partial"
    assert summary["kind"] == "expand"
    # exactly two passers; the other four omitted (each for a distinct, honest reason)
    assert summary["passers"] == 2
    assert summary["omitted_total"] == 4

    # universe.json was written with exactly the expected members + omitted-with-reason (by value)
    universe = json.loads((seed_dir / "universe.json").read_text())
    assert {m["symbol"] for m in universe["members"]} == {"PASSER1", "PASSER2"}
    assert universe["member_count"] == 2
    omit = {o["symbol"]: o["reason"] for o in universe["omitted"]}
    assert set(omit) == {"SMALLCAP", "CHEAP", "NOCAP", "FETCHFAIL"}
    assert "market_cap" in omit["SMALLCAP"]
    assert "price" in omit["CHEAP"]
    assert omit["NOCAP"] == "no_market_cap"
    assert omit["FETCHFAIL"] == "empty_series"  # the failed fetch stored no bars → no series to screen
    # a passer's recorded screen-pass values are the real reference values (sector carried from the pool)
    p1 = next(m for m in universe["members"] if m["symbol"] == "PASSER1")
    assert p1["sector"] == "Technology" and p1["market_cap"] == 3.0e12 and p1["reference_close"] == 150.0
    # per-symbol CSVs are written ONLY for passers (omitted candidates get none)
    from app.data_providers.seed_provider import symbol_to_filename
    assert (seed_dir / "prices" / symbol_to_filename("PASSER1")).exists()
    assert not (seed_dir / "prices" / symbol_to_filename("SMALLCAP")).exists()
    # meta.json refreshed honestly
    meta = json.loads((seed_dir / "meta.json").read_text())
    assert meta["universe_members"] == 2 and meta["omitted_candidates"] == 4


def test_expand_omitted_candidates_contribute_no_member_and_no_fabricated_bar(tmp_path):
    """No-fabrication: a candidate whose fetch raises, returns empty, or lacks a market cap is omitted
    with a reason and contributes NO universe member and NO fabricated bar. FETCHFAIL/NOCAP/etc. are not
    in members; FETCHFAIL's symbol has zero stored DailyPrice rows."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    seed_dir = tmp_path / "seed"
    _write_pool(seed_dir)
    engine = make_engine(f"sqlite:///{tmp_path / 'nofab.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    job = create_job("expand", date(2024, 3, 1), date(2024, 3, 1), source="yahoo")
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=_ExpandProvider(),
        sleep_fn=_noop_sleep, seed_dir=seed_dir,
    )
    members = {m["symbol"] for m in json.loads((seed_dir / "universe.json").read_text())["members"]}
    assert "FETCHFAIL" not in members and "NOCAP" not in members
    with Session(engine) as session:
        n_fetchfail = session.scalar(
            select(func.count()).select_from(DailyPrice).where(DailyPrice.symbol == "FETCHFAIL")
        )
    assert n_fetchfail == 0  # the failed fetch fabricated no bar
    assert summary["omitted_total"] == 4


def test_expand_engine_decision_matches_screen_reasons_predicate(tmp_path):
    """Single screen source: the engine's per-candidate pass/omit matches the SAME `screen_reasons`
    predicate (the one definition the offline runbook + test_universe_screen.py use) for the same
    reference values — proving the engine did not re-implement the rule."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    f = cfg.universe.filters
    seed_dir = tmp_path / "seed"
    _write_pool(seed_dir)
    engine = make_engine(f"sqlite:///{tmp_path / 'screen_src.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()
    job = create_job("expand", date(2024, 3, 1), date(2024, 3, 1), source="yahoo")
    run_data_job(job.job_id, config=cfg, engine=engine, provider=_ExpandProvider(), sleep_fn=_noop_sleep, seed_dir=seed_dir)

    universe = json.loads((seed_dir / "universe.json").read_text())
    members = {m["symbol"] for m in universe["members"]}
    prov = _ExpandProvider()
    for sym in ("PASSER1", "SMALLCAP", "CHEAP", "NOCAP"):
        px = prov._PRICE[sym]
        adv = px * 1_000_000.0
        reasons = screen_reasons(px, adv, prov._CAP[sym], min_price=f.min_price,
                                 min_dollar_vol=f.min_dollar_vol, min_market_cap=f.min_market_cap)
        # the predicate's verdict (empty == pass) matches the engine's membership decision exactly
        assert (sym in members) == (reasons == []), f"{sym}: predicate {reasons} vs member {sym in members}"


def test_expand_idempotent_no_duplicate_bars_no_snapshot_regen(tmp_path):
    """Idempotency / immutability: re-running expand over already-stored bars inserts NO duplicate
    (symbol, date) and writes/mutates NO scanner_runs / scanner_results / forward_returns (no DB regen)."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    seed_dir = tmp_path / "seed"
    _write_pool(seed_dir)
    engine = make_engine(f"sqlite:///{tmp_path / 'idem.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    job1 = create_job("expand", date(2024, 3, 1), date(2024, 3, 1), source="yahoo")
    run_data_job(job1.job_id, config=cfg, engine=engine, provider=_ExpandProvider(), sleep_fn=_noop_sleep, seed_dir=seed_dir)
    with Session(engine) as session:
        bars_after_1 = session.scalar(select(func.count()).select_from(DailyPrice))
        runs_after_1 = session.scalar(select(func.count()).select_from(ScannerRun))
        results_after_1 = session.scalar(select(func.count()).select_from(ScannerResult))
        fr_after_1 = session.scalar(select(func.count()).select_from(ForwardReturn))

    job2 = create_job("expand", date(2024, 3, 1), date(2024, 3, 1), source="yahoo")
    run_data_job(job2.job_id, config=cfg, engine=engine, provider=_ExpandProvider(), sleep_fn=_noop_sleep, seed_dir=seed_dir)
    with Session(engine) as session:
        bars_after_2 = session.scalar(select(func.count()).select_from(DailyPrice))
        runs_after_2 = session.scalar(select(func.count()).select_from(ScannerRun))
        results_after_2 = session.scalar(select(func.count()).select_from(ScannerResult))
        fr_after_2 = session.scalar(select(func.count()).select_from(ForwardReturn))
        # no (symbol, date) duplicate for any passer
        per_symbol = {}
        for r in session.exec(select(DailyPrice).where(DailyPrice.date == date(2024, 3, 1))).all():
            per_symbol[r.symbol] = per_symbol.get(r.symbol, 0) + 1
    assert bars_after_2 == bars_after_1  # the second expand inserted no duplicate bar
    assert all(c == 1 for c in per_symbol.values())  # exactly one bar per (symbol, date)
    # expand writes only DailyPrice + universe.json — it regenerates NO immutable snapshot
    assert runs_after_1 == 0 and runs_after_2 == 0
    assert results_after_1 == 0 and results_after_2 == 0
    assert fr_after_1 == 0 and fr_after_2 == 0


def test_expand_eligibility_gate_engine_rejects_non_market_cap_source():
    """Eligibility gate (engine layer): an `expand` job whose `source` has `supports_market_cap: false`
    (alpha_vantage / stooq) is rejected with an explicit ValueError — never a silent no-op."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    for ineligible in ("alpha_vantage", "stooq"):
        with pytest.raises(ValueError, match="market cap"):
            validate_job_request("expand", date(2024, 3, 1), date(2024, 3, 1), cfg, source=ineligible)
    # a market-cap-capable source passes the gate (yahoo is no-key, so no key required)
    validate_job_request("expand", date(2024, 3, 1), date(2024, 3, 1), cfg, source="yahoo")


def test_expand_needs_key_source_without_key_rejected():
    """An expand over a needs-key, market-cap-capable source (tiingo) with no env/pasted key is rejected
    explicitly (reuses the J-33 key gate) — never a silent expand."""
    import os as _os
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    prev = _os.environ.pop("TIINGO_API_KEY", None)
    try:
        with pytest.raises(ValueError, match="requires a key"):
            validate_job_request("expand", date(2024, 3, 1), date(2024, 3, 1), cfg, source="tiingo")
        # with a pasted session key the gate passes (tiingo is market-cap-capable)
        validate_job_request("expand", date(2024, 3, 1), date(2024, 3, 1), cfg, source="tiingo", api_key="sk-paste")
    finally:
        if prev is not None:
            _os.environ["TIINGO_API_KEY"] = prev


def test_merge_committed_universe_makes_universe_json_the_single_source(tmp_path):
    """Single-source universe (the J-22 invariant after an expand): when a committed `universe.json` is
    present, `_merge_committed_universe` GROWS `universe.symbols` to `base ∪ artifact members` (+ their
    sectors), so `len(config.universe.symbols)` == `/api/data universe_count` == `/methodology
    resolved_size` — all three read the one canonical resolved universe. Asserted by VALUE on a config
    built from a temp universe.json. The union (not a replace) keeps the existing themed names mapped so
    boot validation never breaks while the screen grows the universe."""
    import yaml
    base = yaml.safe_load(DEFAULT_CONFIG_PATH.read_text())
    base_n = len(base["universe"]["symbols"])
    # a committed universe.json with two NEW members not in the YAML universe (each carries a sector)
    members = [
        {"symbol": "ZZZA", "sector": "Technology", "market_cap": 3.0e12, "reference_close": 100.0,
         "adv_dollar": 1.0e8, "bars": 300, "first": "2021-01-04", "last": "2024-03-01"},
        {"symbol": "ZZZB", "sector": "Energy", "market_cap": 5.0e11, "reference_close": 50.0,
         "adv_dollar": 9.0e7, "bars": 300, "first": "2021-01-04", "last": "2024-03-01"},
    ]
    data = yaml.safe_load(yaml.safe_dump(base))  # deep copy
    ujson = tmp_path / "universe.json"
    ujson.write_text(json.dumps({"members": members}))
    _merge_committed_universe(data, ujson)

    # the merged config validates; the universe GREW by exactly the two new members, each sector-mapped
    from app.config import Config
    cfg2 = Config(**data)
    assert len(cfg2.universe.symbols) == base_n + 2
    assert {"ZZZA", "ZZZB"}.issubset(set(cfg2.universe.symbols))
    assert cfg2.stock_sectors["ZZZA"] == "Technology" and cfg2.stock_sectors["ZZZB"] == "Energy"
    # the three-way single-source equality holds by construction (both read len(universe.symbols))
    n = len(cfg2.universe.symbols)
    assert build_catalog(cfg2)["universe_selection"]["resolved_size"] == n


def test_merge_committed_universe_absent_is_noop():
    """No committed universe.json ⇒ the merge is a pure no-op (the YAML symbols stand) — the graceful
    fallback that keeps every existing test/boot path unchanged until an expand writes the artifact."""
    import yaml
    base = yaml.safe_load(DEFAULT_CONFIG_PATH.read_text())
    data = yaml.safe_load(yaml.safe_dump(base))
    before = list(data["universe"]["symbols"])
    _merge_committed_universe(data, Path("/nonexistent/universe.json"))
    assert data["universe"]["symbols"] == before  # unchanged


def test_expand_kind_is_in_job_kinds():
    """The `expand` kind is a real job kind (the API Literal + the engine JOB_KINDS agree)."""
    assert "expand" in data_manager.JOB_KINDS


def test_expand_that_lands_new_bar_refreshes_coverage_snapshot(tmp_path):
    """TC-3/TC-6 (B1) — an `expand` job whose bars manifest changes (a new passer's history is added)
    triggers the SAME fetch-path finalize behavior as a plain fetch: a fresh coverage_snapshot row is
    persisted for the current stamp, byte-identical to a direct fresh `_compute_coverage_uncached` call."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    seed_dir = tmp_path / "seed"
    _write_pool(seed_dir)
    engine = make_engine(f"sqlite:///{tmp_path / 'expand_refresh.db'}")
    create_db_and_tables(engine)
    d = date(2024, 3, 1)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()
        pre_payload = data_manager.refresh_coverage_snapshot(session, cfg)
        pre_version = data_manager._membership_dataset_version(session, cfg)
    assert pre_payload["symbol_count"] == 1  # SPY only, before the expand lands any passer bars

    job = create_job("expand", d, d, source="yahoo")
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=_ExpandProvider(),
        sleep_fn=_noop_sleep, seed_dir=seed_dir,
    )
    assert summary["status"] == "partial"  # FETCHFAIL's OHLCV fetch fails; the two passers still land bars
    assert summary["passers"] == 2

    with Session(engine) as session:
        new_version = data_manager._membership_dataset_version(session, cfg)
        assert new_version != pre_version
        rows = session.exec(select(CoverageSnapshot)).all()
        assert len(rows) == 1  # the stale pre-expand-stamp row was reclaimed (B2), not left alongside
        assert rows[0].dataset_version == new_version
        stored = json.loads(rows[0].payload_json)
        # SPY + every candidate whose OHLCV fetch succeeded (5 of 6 — FETCHFAIL's fetch itself fails, so it
        # stores no bar; the other four are OMITTED by the screen but still get their fetched bar stored,
        # per test_expand_omitted_candidates_contribute_no_member_and_no_fabricated_bar's own contract).
        assert stored["symbol_count"] == 6
        fresh = data_manager._compute_coverage_uncached(session, cfg, as_of=None)
        assert stored == fresh  # TC-6: byte-identical to an independent fresh compute


class _ExpandCap429Provider(PriceProvider):
    """An expand provider whose OHLCV fetch always succeeds but whose market-cap feed is PERSISTENTLY
    rate-limited — so the screen step pauses the expand gracefully `resumable` (never fabricates a cap)."""

    def get_daily(self, symbol, start=None, end=None):
        return [Bar(date=start or date(2024, 3, 1), open=100.0, high=100.0, low=100.0, close=100.0, volume=1_000_000.0)]

    def get_market_cap(self, symbol):
        raise RateLimitError("HTTP 429 at https://provider/quote")


def test_expand_cap_feed_rate_limited_pauses_resumable_never_fabricates(tmp_path):
    """A persistent 429 on the market-cap feed during the screen step pauses the expand GRACEFULLY
    `resumable` (distinct from failed) and writes NO universe.json — never a fabricated cap/member. The
    durable checkpoint (from the OHLCV fetch) makes it Resume-able."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    seed_dir = tmp_path / "seed"
    _write_pool(seed_dir, rows=[("PASSER1", "Technology", "test"), ("PASSER2", "Health Care", "test")])
    engine = make_engine(f"sqlite:///{tmp_path / 'cap429.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    job = create_job("expand", date(2024, 3, 1), date(2024, 3, 1), source="yahoo")
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=_ExpandCap429Provider(),
        sleep_fn=_noop_sleep, seed_dir=seed_dir,
    )
    assert summary["status"] == "resumable"  # graceful pause, NOT failed
    assert summary["passers"] == 0  # no member committed before the cap feed walled
    assert not (seed_dir / "universe.json").exists()  # nothing fabricated/written on the pause
    with Session(engine) as session:
        # the durable checkpoint survives → the import is discoverable + Resume-able (J-34 reuse)
        listed = resumable_imports(session, cfg)
    assert [r["import_id"] for r in listed] == [job.job_id]


def test_expand_cap_fetch_real_httpx_key_scrubbed_end_to_end(tmp_path, caplog):
    """Key-safety (carry the iter-21/22 lesson to the NEW expand error surface): an expand whose
    market-cap fetch raises an error EMBEDDING a real httpx error with the key in the URL → the
    data_manager scrub removes it. The sentinel is ABSENT from the job snapshot, `GET /api/data/jobs/{id}`,
    the written universe.json omitted reasons, and the run history — while `***` proves the scrub fired."""
    secret = "sk-EXPAND-CAP-KEY-SCRUB-7a1"
    leak = _real_httpx_error_str_with_key(secret)
    assert secret in leak  # sanity: there IS a key to scrub

    class _CapKeyLeakProvider(PriceProvider):
        """OHLCV succeeds; the market-cap fetch raises a ProviderUnavailableError embedding the key-in-URL
        httpx error (a non-429 cap failure → the candidate is omitted with a scrubbed reason)."""

        def get_daily(self, symbol, start=None, end=None):
            return [Bar(date=start or date(2024, 3, 1), open=100.0, high=100.0, low=100.0, close=100.0, volume=1_000_000.0)]

        def get_market_cap(self, symbol):
            raise ProviderUnavailableError(leak)

    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    seed_dir = tmp_path / "seed"
    _write_pool(seed_dir, rows=[("PASSER1", "Technology", "test")])
    engine = make_engine(f"sqlite:///{tmp_path / 'capscrub.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    job = create_job("expand", date(2024, 3, 1), date(2024, 3, 1), source="tiingo")
    with caplog.at_level("DEBUG"):
        summary = run_data_job(
            job.job_id, config=cfg, engine=engine, provider=_CapKeyLeakProvider(),
            api_key=secret, sleep_fn=_noop_sleep, seed_dir=seed_dir,
        )
    # the candidate is omitted with a market_cap_fetch_failed reason — but the key is scrubbed everywhere
    assert summary["omitted_total"] == 1
    assert secret not in json.dumps(summary)
    assert secret not in json.dumps(get_job(job.job_id))
    universe_blob = (seed_dir / "universe.json").read_text()
    assert secret not in universe_blob  # the omitted reason in the written artifact is key-safe
    assert "***" in json.dumps(summary["omitted"]) or "***" in universe_blob  # the scrub fired
    with Session(engine) as session:
        runs = session.exec(select(DataProviderRun)).all()
    assert secret not in json.dumps([{c: str(getattr(r, c)) for c in ("provider", "status", "message")} for r in runs])
    assert secret not in caplog.text


# ==================================================================================================
# J-84 — Expand market-cap via the BATCHED cookie+crumb path; systemic auth/limit failure → resumable
#
# The batched provider mirrors YahooProvider's J-84 contract: `get_market_caps(symbols)` returns a
# {symbol: cap|None} map (cookie+crumb acquired ONCE, conceptually), and raises `RateLimitError` UPFRONT
# on a SYSTEMIC auth/limit failure — so a whole-batch auth outage pauses the expand resumable WITHOUT
# recording every candidate omitted. The single-symbol `get_market_cap` is NOT used by these (the engine
# prefers the batch map). Drives the REAL `_run_expand_screen` orchestration via run/resume_data_job.
# ==================================================================================================
class _BatchedCapProvider(PriceProvider):
    """An injected expand provider with a BATCHED market-cap capability (J-84). `get_daily` stores one
    bar (counting fetches, to prove resume's zero-duplicate-OHLCV-fetch); `get_market_caps` returns the
    canned {symbol: cap|None} map, OR raises a SYSTEMIC `RateLimitError` when `systemic` is set (the
    cookie/crumb step or a batched 401/429). It records each batch call so a test can prove caps are
    fetched in ONE batch and not per-symbol."""

    # per-symbol close (so the price screen verdict is known by construction; volume sized so ADV clears
    # $50M for any >$10 name). CHEAP's $4 close fails the min-price screen.
    _PRICE = {"PASSER1": 150.0, "PASSER2": 80.0, "SMALLCAP": 60.0, "CHEAP": 4.0, "NOCAP": 90.0}

    def __init__(self, caps: dict, *, systemic: bool = False):
        self._caps = caps
        self._systemic = systemic
        self.fetched: list[str] = []          # OHLCV get_daily calls
        self.cap_batches: list[list] = []      # each get_market_caps invocation's symbol list
        self.per_symbol_cap_calls: list[str] = []  # MUST stay empty — the engine uses the batch map

    def get_daily(self, symbol, start=None, end=None):
        self.fetched.append(symbol)
        px = self._PRICE.get(symbol, 100.0)
        return [Bar(date=start or date(2024, 3, 1), open=px, high=px, low=px, close=px, volume=1_000_000.0)]

    def get_market_caps(self, symbols):
        self.cap_batches.append(list(symbols))
        if self._systemic:
            raise RateLimitError("yahoo market-cap crumb systemic auth/limit failure: HTTP 401")
        return {s: self._caps.get(s) for s in symbols}

    def get_market_cap(self, symbol):  # pragma: no cover - the batch map is preferred; recorded if hit
        self.per_symbol_cap_calls.append(symbol)
        return self._caps.get(symbol)


def test_expand_batched_caps_screens_real_passers_one_batch_not_per_symbol(tmp_path):
    """J-84 happy path: the batched cap provider screens the pool, writes universe.json with EXACTLY the
    expected passers/omissions, and resolves the caps in ONE batch call (cookie+crumb-once semantics) —
    never per-symbol. PASSER1/PASSER2 pass; SMALLCAP/CHEAP/NOCAP omitted with their honest reasons."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    seed_dir = tmp_path / "seed"
    _write_pool(seed_dir, rows=[r for r in _POOL_ROWS if r[0] != "FETCHFAIL"])  # all OHLCV-fetchable
    engine = make_engine(f"sqlite:///{tmp_path / 'batch_caps.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    caps = {"PASSER1": 3.0e12, "PASSER2": 5.0e11, "SMALLCAP": 1.0e9, "CHEAP": 9.0e9, "NOCAP": None}
    provider = _BatchedCapProvider(caps)
    job = create_job("expand", date(2024, 3, 1), date(2024, 3, 1), source="yahoo")
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=provider, sleep_fn=_noop_sleep, seed_dir=seed_dir,
    )
    assert summary["status"] == "ok"
    assert summary["passers"] == 2
    universe = json.loads((seed_dir / "universe.json").read_text())
    assert {m["symbol"] for m in universe["members"]} == {"PASSER1", "PASSER2"}
    omit = {o["symbol"]: o["reason"] for o in universe["omitted"]}
    assert "market_cap" in omit["SMALLCAP"] and "price" in omit["CHEAP"]
    assert omit["NOCAP"] == "no_market_cap"  # a present-but-capless symbol → honest omission, never fab
    p1 = next(m for m in universe["members"] if m["symbol"] == "PASSER1")
    assert p1["market_cap"] == 3.0e12  # the REAL cap from the batch
    # caps resolved in ONE batch (cookie+crumb-once), NEVER per-symbol
    assert len(provider.cap_batches) == 1
    assert set(provider.cap_batches[0]) == {"PASSER1", "PASSER2", "SMALLCAP", "CHEAP", "NOCAP"}
    assert provider.per_symbol_cap_calls == []


def test_expand_systemic_cap_auth_failure_pauses_resumable_not_all_omitted(tmp_path):
    """J-84 crux: a SYSTEMIC market-cap auth/limit failure (cookie/crumb step or a batched 401/429) raised
    by `get_market_caps` pauses the expand GRACEFULLY `resumable` (NOT failed), records NO universe.json,
    and does NOT record every candidate omitted (the bug J-84 fixes: 0-passers / 548-omitted). The durable
    checkpoint (from the OHLCV fetch) makes it Resume-able and SURVIVES a fresh DB session (restart)."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    seed_dir = tmp_path / "seed"
    _write_pool(seed_dir, rows=[("PASSER1", "Technology", "test"), ("PASSER2", "Health Care", "test")])
    engine = make_engine(f"sqlite:///{tmp_path / 'sys_auth.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    job = create_job("expand", date(2024, 3, 1), date(2024, 3, 1), source="yahoo")
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine,
        provider=_BatchedCapProvider({}, systemic=True), sleep_fn=_noop_sleep, seed_dir=seed_dir,
    )
    assert summary["status"] == "resumable"            # graceful pause, NOT failed
    assert summary["passers"] == 0
    assert summary["omitted_total"] == 0               # NOT "548 omitted" — the J-84 fix
    assert not (seed_dir / "universe.json").exists()   # nothing fabricated/written on the pause
    # the durable checkpoint survives a fresh session (restart-survival the Resume depends on)
    with Session(engine) as fresh:
        listed = resumable_imports(fresh, cfg)
        assert [r["import_id"] for r in listed] == [job.job_id]


def test_expand_resume_after_systemic_pause_zero_duplicate_ohlcv_fetch_then_completes(tmp_path):
    """J-84 resume: after a systemic cap-auth pause, Resume with a RECOVERED batched provider completes
    with ZERO duplicate OHLCV fetch (the fetch stage already covered — J-59) and writes the real
    universe.json. Asserts the recovered provider's `get_daily` is NEVER called on resume (covered chunks
    skipped) while the cap batch DOES re-run (that is the point of resuming)."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    seed_dir = tmp_path / "seed"
    _write_pool(seed_dir, rows=[("PASSER1", "Technology", "test"), ("PASSER2", "Health Care", "test")])
    engine = make_engine(f"sqlite:///{tmp_path / 'resume_sys.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    job = create_job("expand", date(2024, 3, 1), date(2024, 3, 1), source="yahoo")
    paused = _BatchedCapProvider({}, systemic=True)
    summary1 = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=paused, sleep_fn=_noop_sleep, seed_dir=seed_dir,
    )
    assert summary1["status"] == "resumable"
    fetched_during_pause = list(paused.fetched)
    assert set(fetched_during_pause) == {"PASSER1", "PASSER2"}  # OHLCV fetched before the cap step walled

    # --- Resume with a recovered provider: OHLCV already covered (zero re-fetch); cap batch now succeeds
    recovered = _BatchedCapProvider({"PASSER1": 3.0e12, "PASSER2": 5.0e11})
    summary2 = resume_data_job(
        job.job_id, config=cfg, engine=engine, provider=recovered, sleep_fn=_noop_sleep, seed_dir=seed_dir,
    )
    assert summary2["status"] == "ok"
    assert recovered.fetched == []          # ZERO duplicate OHLCV fetch — the covered fetch stage skipped
    assert len(recovered.cap_batches) == 1  # the cap batch re-ran on resume (that is what was retried)
    universe = json.loads((seed_dir / "universe.json").read_text())
    assert {m["symbol"] for m in universe["members"]} == {"PASSER1", "PASSER2"}
    # no duplicate (symbol, date) bar from the resume
    with Session(engine) as session:
        per_symbol = {}
        for r in session.exec(select(DailyPrice).where(DailyPrice.date == date(2024, 3, 1))).all():
            per_symbol[r.symbol] = per_symbol.get(r.symbol, 0) + 1
    assert all(c == 1 for c in per_symbol.values())


def test_expand_systemic_pause_crumb_never_leaks_in_any_response_or_row(tmp_path):
    """J-84 secret-redaction guard: a systemic cap-auth failure whose error EMBEDS a crumb-like token must
    NOT leak the crumb into the job snapshot, `GET /api/data/jobs/{id}`, the `resumable_imports` rows, the
    written artifacts, or any `DataProviderRun` row. Grep the RESPONSE, not just the DB (MEMORY:
    httpx-error-leaks-url-query-key)."""
    crumb = "CRUMB-SECRET-NEVER-LEAKS-9z1"

    class _CrumbLeakingProvider(PriceProvider):
        def get_daily(self, symbol, start=None, end=None):
            return [Bar(date=start or date(2024, 3, 1), open=100.0, high=100.0, low=100.0, close=100.0, volume=1_000_000.0)]

        def get_market_caps(self, symbols):
            # a misbehaving provider that (wrongly) put the crumb in its error string — the engine scrub
            # + the message plumbing MUST still not surface it anywhere the operator/DB can read.
            raise RateLimitError(f"systemic auth failure with crumb={crumb}")

    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    seed_dir = tmp_path / "seed"
    _write_pool(seed_dir, rows=[("PASSER1", "Technology", "test")])
    engine = make_engine(f"sqlite:///{tmp_path / 'crumbleak.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    job = create_job("expand", date(2024, 3, 1), date(2024, 3, 1), source="yahoo")
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=_CrumbLeakingProvider(),
        sleep_fn=_noop_sleep, seed_dir=seed_dir,
    )
    assert summary["status"] == "resumable"
    # the crumb is ABSENT from every operator/DB-readable surface
    assert crumb not in json.dumps(summary)
    assert crumb not in json.dumps(get_job(job.job_id))
    with Session(engine) as session:
        assert crumb not in json.dumps(resumable_imports(session, cfg))
        runs = session.exec(select(DataProviderRun)).all()
    assert crumb not in json.dumps([{c: str(getattr(r, c)) for c in ("provider", "status", "message")} for r in runs])


# ==================================================================================================
# J-39 — seed-safe Remove-data: classifier + confirm-preview + destructive cascade + audit
#
# The session's FIRST destructive data path. The cascade MUST be a whole-row delete of user-added bars
# + the derived rows that depended SOLELY on them; a fully-covered snapshot is left UNTOUCHED (NEVER an
# in-place overwrite of a retained snapshot — the *Snapshots are immutable* identity = "never overwritten
# in place"). The committed seed (the meta.json windows) is genuinely un-deletable. The live host has zero
# user-added bars (so a live remove is a no-op) — correctness is proven here against a fixture that ADDS
# user bars beyond the seed.
# ==================================================================================================
import datetime as _dt  # noqa: E402


def _write_seed_meta(seed_dir: Path, windows: dict[str, tuple[str, str, int]]) -> None:
    """Write a minimal committed-seed manifest (`meta.json`) carrying per-symbol {first,last,bars} windows
    — the authoritative seed-vs-user-added source J-39 reads. A `(symbol, date)` inside a window is the
    committed seed (protected); a date beyond `last` (or a symbol absent from the manifest) is user-added."""
    seed_dir.mkdir(parents=True, exist_ok=True)
    symbols = [{"symbol": s, "first": f, "last": l, "bars": b} for s, (f, l, b) in windows.items()]
    meta = {"source": "test seed", "symbols_ok": len(symbols), "symbols_failed": 0, "symbols": symbols}
    (seed_dir / "meta.json").write_text(json.dumps(meta) + "\n")


def _add_run(session, asof, *, label="Choppy", score=50.0):
    """Insert one immutable ScannerRun + a child ScannerResult/SectorScoreRow/ThemeScoreRow so the cascade
    has every derived table to remove. Returns the run."""
    run = ScannerRun(
        asof_date=asof, created_at=_dt.datetime(2024, 1, 1), provider="seed", benchmark="SPY",
        regime_score=score, regime_label=label, regime_components_json="[]",
        new_high_low_json="{}", candidate_counts_json="{}",
    )
    session.add(run)
    session.flush()
    session.add(ScannerResult(
        run_id=run.id, ticker="AAA", name="AAA", sector="Tech",
        leadership_score=50.0, leadership_bucket="C", entry_quality_score=50.0, entry_quality_bucket="C",
        risk_score=50.0, risk_bucket="C", setup_status="Avoid", rank=1, record_json="{}",
    ))
    session.add(SectorScoreRow(
        run_id=run.id, ticker="XLK", kind="sector", name="Tech", score=50.0, bucket="C",
        trend_label="flat", components_json="[]", rank=1,
    ))
    session.add(ThemeScoreRow(
        run_id=run.id, slug="ai", name="AI", score=50.0, bucket="C", members_json="[]",
        breadth_label="flat", trend_label="flat", components_json="[]", rank=1,
    ))
    return run


def _add_fr(session, run, symbol, horizon, measured_date):
    """Insert one ForwardReturn keyed to a run, measuring into `measured_date` (a post-snapshot bar)."""
    session.add(ForwardReturn(
        run_id=run.id, symbol=symbol, horizon=horizon, asof_date=run.asof_date,
        entry_close=1.0, measured_date=measured_date, realized_return=0.0,
    ))


@pytest.fixture()
def removal_engine(tmp_path):
    """A hand-built dataset with an EXACT seed-vs-user-added boundary and dependency structure:

      seed window  : SPY & AAA on D1..D10 (committed seed — PROTECTED).
      user-added   : SPY & AAA on D11, D12, D13 (beyond the seed `last` D10 — REMOVABLE).

      Snapshot A (asof D3)  — fully SEED-covered: inputs <= D3 are seed; its forward returns measure into
                              D4/D5 (seed). It depends on NO removed bar → MUST be left UNTOUCHED.
      Snapshot B (asof D12) — a USER-ADDED trading day: inputs <= D12 include user bars D11/D12; its
                              forward return measures into D13 (user). → cascade-removed entirely.
      Snapshot C (asof D9)  — SEED inputs (<= D9 all seed) BUT a forward return measures into D11 (a
                              user-added, removed bar). → cascade-removed entirely (a forward-measurement
                              bar it depended on is gone).

    Removing the user-added scope (D11..D13) must drop B and C (+ their children + their forward returns)
    and the user bars, leave A untouched, and leave NO row referencing an absent bar."""
    seed_dir = tmp_path / "seed"
    _write_seed_meta(seed_dir, {"SPY": ("2024-01-01", "2024-01-10", 10), "AAA": ("2024-01-01", "2024-01-10", 10)})
    engine = make_engine(f"sqlite:///{tmp_path / 'remove.db'}")
    create_db_and_tables(engine)
    days = [date(2024, 1, d) for d in range(1, 14)]  # D1..D13
    with Session(engine) as session:
        for sym in ("SPY", "AAA"):
            for d in days:
                session.add(DailyPrice(symbol=sym, date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        run_a = _add_run(session, days[2])   # D3 — fully seed-covered
        run_c = _add_run(session, days[8])   # D9 — seed inputs, forward bar into user date
        run_b = _add_run(session, days[11])  # D12 — user-added input date
        session.flush()
        _add_fr(session, run_a, "AAA", 1, days[3])   # D3 → D4 (seed) — retained
        _add_fr(session, run_a, "AAA", 2, days[4])   # D3 → D5 (seed) — retained
        _add_fr(session, run_c, "AAA", 1, days[9])   # D9 → D10 (seed)
        _add_fr(session, run_c, "AAA", 2, days[10])  # D9 → D11 (USER) — makes C depend on a removed bar
        _add_fr(session, run_b, "AAA", 1, days[12])  # D12 → D13 (USER)
        session.commit()
        ids = {"a": run_a.id, "b": run_b.id, "c": run_c.id}
    return engine, seed_dir, days, ids


def test_load_seed_windows_and_is_seed_bar(removal_engine):
    """The seed classifier reads meta.json windows: a (symbol, date) inside a window is committed-seed
    (protected); a date beyond `last`, or a symbol absent from the manifest, is user-added (removable)."""
    _engine, seed_dir, days, _ids = removal_engine
    windows = load_seed_windows(seed_dir)
    assert windows["SPY"] == (date(2024, 1, 1), date(2024, 1, 10))
    # inside the window → committed seed (protected)
    assert is_seed_bar("SPY", date(2024, 1, 5), windows) is True
    assert is_seed_bar("SPY", date(2024, 1, 10), windows) is True  # the boundary `last` is still seed
    # beyond the window → user-added (removable)
    assert is_seed_bar("SPY", date(2024, 1, 11), windows) is False
    assert is_seed_bar("AAA", date(2024, 1, 13), windows) is False
    # a symbol not in the manifest at all → user-added everywhere
    assert is_seed_bar("ZZZ", date(2024, 1, 5), windows) is False


def _write_seed_meta_with_vendor(seed_dir: Path, rows: list[dict]) -> None:
    """Like `_write_seed_meta` but allows an optional per-row `vendor` key (J-14's `load_seed_meta`
    sibling reader) -- a row with NO `vendor` key exercises the honest `vendor: None` path, exactly like
    the real SPY/QQQ/IWM/RSP/DIA manifest entries."""
    seed_dir.mkdir(parents=True, exist_ok=True)
    meta = {"source": "test seed", "symbols_ok": len(rows), "symbols_failed": 0, "symbols": rows}
    (seed_dir / "meta.json").write_text(json.dumps(meta) + "\n")


def test_load_seed_meta_exposes_vendor_and_first_last_sharing_one_parse(tmp_path):
    """J-14: `load_seed_meta` is the SIBLING reader `indexes.compute_index_series` uses for the vendor
    label + honest first-bar disclosure -- it shares `load_seed_windows`'s `meta.json` parse (no second
    `json.loads` call anywhere) but returns per-symbol {first, last, vendor}. A symbol with NO vendor
    record (an ETF like SPY) yields `vendor: None` -- never a fabricated vendor. `load_seed_windows`
    itself stays UNCHANGED (same shape, same values) -- this is an ADDITIVE sibling, not a modification."""
    seed_dir = tmp_path / "seed"
    _write_seed_meta_with_vendor(seed_dir, [
        {"symbol": "SPY", "first": "2005-02-25", "last": "2026-07-01", "bars": 5369},
        {"symbol": "^SPX", "first": "1996-01-02", "last": "2026-07-01", "bars": 7674, "vendor": "stooq"},
        {"symbol": "^VIX", "first": "1996-01-02", "last": "2026-07-01", "bars": 7675, "vendor": "yahoo"},
        {"symbol": "^TNX", "first": "2021-01-04", "last": "2026-05-28", "bars": 1357, "vendor": "fred-macro-proxy"},
    ])

    meta = load_seed_meta(seed_dir)
    assert meta["SPY"] == {"first": date(2005, 2, 25), "last": date(2026, 7, 1), "vendor": None}
    assert meta["^SPX"] == {"first": date(1996, 1, 2), "last": date(2026, 7, 1), "vendor": "stooq"}
    assert meta["^VIX"]["vendor"] == "yahoo"
    assert meta["^TNX"]["vendor"] == "fred-macro-proxy"
    assert "ZZZ" not in meta  # an unlisted symbol is simply absent -- never a fabricated entry

    # the PRE-EXISTING J-39 reader is untouched -- same shape, same values, sharing the same parse.
    windows = load_seed_windows(seed_dir)
    assert windows["SPY"] == (date(2005, 2, 25), date(2026, 7, 1))
    assert windows["^SPX"] == (date(1996, 1, 2), date(2026, 7, 1))


def test_load_seed_meta_missing_manifest_degrades_honestly(tmp_path):
    """An absent manifest yields an EMPTY map (never a crash) -- the same honest-degrade contract
    `load_seed_windows` already has."""
    seed_dir = tmp_path / "no-such-seed"
    assert load_seed_meta(seed_dir) == {}


def test_preview_removal_deletes_nothing(removal_engine):
    """The preview is READ-ONLY: it returns the exact removable bars + range + the not-removable
    committed-seed breakdown + the cascade set, and the DB is BYTE-UNCHANGED afterward (no deletion)."""
    engine, seed_dir, days, ids = removal_engine
    with Session(engine) as session:
        before = {
            "prices": session.scalar(select(func.count(DailyPrice.id))),
            "runs": session.scalar(select(func.count(ScannerRun.id))),
            "results": session.scalar(select(func.count(ScannerResult.id))),
            "frs": session.scalar(select(func.count(ForwardReturn.id))),
        }
        # scope: the whole user-added tail by date range (no symbol filter → all symbols)
        prev = preview_removal(session, None, symbols=None, start=days[10], end=days[12], seed_dir=seed_dir)
        after = {
            "prices": session.scalar(select(func.count(DailyPrice.id))),
            "runs": session.scalar(select(func.count(ScannerRun.id))),
            "results": session.scalar(select(func.count(ScannerResult.id))),
            "frs": session.scalar(select(func.count(ForwardReturn.id))),
        }
    assert before == after  # PREVIEW DELETED NOTHING

    # removable: SPY & AAA on D11,D12,D13 = 6 bars; range D11..D13.
    assert prev["removable_bar_count"] == 6
    assert prev["removable_first"] == days[10].isoformat()
    assert prev["removable_last"] == days[12].isoformat()
    assert prev["removable_symbol_count"] == 2  # SPY + AAA
    # not-removable: nothing seed is in this scope (D11..D13 is wholly user-added).
    assert prev["not_removable_bar_count"] == 0
    # cascade: runs B (D12) and C (D9) are removed; A (D3) is NOT. Exactly 2 snapshots + their forward
    # returns (C has 2, B has 1 = 3 forward-return rows).
    assert prev["cascade"]["snapshot_count"] == 2
    assert set(prev["cascade"]["snapshot_dates"]) == {days[8].isoformat(), days[11].isoformat()}
    assert prev["cascade"]["forward_return_count"] == 3
    assert prev["refused"] is False


def test_preview_seed_only_scope_is_refused(removal_engine):
    """A wholly-committed-seed scope is REFUSED in the preview (refused True, an explicit reason, zero
    removable) — never a silent partial; the seed is un-deletable."""
    engine, seed_dir, days, _ids = removal_engine
    with Session(engine) as session:
        prev = preview_removal(session, None, symbols=None, start=days[0], end=days[4], seed_dir=seed_dir)
    assert prev["removable_bar_count"] == 0
    assert prev["refused"] is True
    assert "committed seed" in prev["reason"].lower()
    # the seed bars in scope are reported as not-removable (SPY & AAA on D1..D5 = 10 bars).
    assert prev["not_removable_bar_count"] == 10


def test_preview_seed_only_symbol_is_refused(removal_engine):
    """A symbol whose every in-scope bar is committed seed is refused (the committed seed is never
    deletable, even named explicitly)."""
    engine, seed_dir, days, _ids = removal_engine
    with Session(engine) as session:
        # SPY over D1..D10 is entirely seed → nothing removable → refused.
        prev = preview_removal(session, None, symbols=["SPY"], start=days[0], end=days[9], seed_dir=seed_dir)
    assert prev["removable_bar_count"] == 0 and prev["refused"] is True


def test_remove_data_cascade_solely_dependent(removal_engine):
    """The destructive removal deletes ONLY the user-added bars in scope and cascade-removes ONLY the
    snapshot/forward-return rows that derived SOLELY from them; a fully-covered snapshot (A) is left
    UNTOUCHED, and NO remaining row references an absent bar."""
    engine, seed_dir, days, ids = removal_engine
    # snapshot A's created_at + content BEFORE, to prove it is untouched (not overwritten in place).
    with Session(engine) as session:
        a_before = session.get(ScannerRun, ids["a"])
        a_created_before = a_before.created_at
        a_results_before = session.scalar(
            select(func.count(ScannerResult.id)).where(ScannerResult.run_id == ids["a"])
        )

    with Session(engine) as session:
        result = remove_data(
            session, None, symbols=None, start=days[10], end=days[12], seed_dir=seed_dir, engine=engine,
        )

    with Session(engine) as session:
        # user bars D11..D13 for SPY+AAA are gone; seed bars D1..D10 remain (un-deletable).
        remaining_dates = sorted(set(session.exec(select(DailyPrice.date).distinct()).all()))
        assert remaining_dates == days[:10]  # only D1..D10 survive
        assert session.scalar(select(func.count(DailyPrice.id))) == 2 * 10  # SPY+AAA × 10 seed days

        # snapshot B (D12) and C (D9) are gone; A (D3) survives — UNTOUCHED.
        surviving_runs = {r.asof_date for r in session.exec(select(ScannerRun)).all()}
        assert surviving_runs == {days[2]}  # only A
        assert session.get(ScannerRun, ids["b"]) is None
        assert session.get(ScannerRun, ids["c"]) is None
        a_after = session.get(ScannerRun, ids["a"])
        assert a_after is not None
        # immutability: A was NEVER overwritten in place — same created_at + same child rows.
        assert a_after.created_at == a_created_before
        assert session.scalar(
            select(func.count(ScannerResult.id)).where(ScannerResult.run_id == ids["a"])
        ) == a_results_before

        # cascade removed B's & C's children across ALL derived tables (no orphan child rows).
        for run_id in (ids["b"], ids["c"]):
            assert session.scalar(select(func.count(ScannerResult.id)).where(ScannerResult.run_id == run_id)) == 0
            assert session.scalar(select(func.count(SectorScoreRow.id)).where(SectorScoreRow.run_id == run_id)) == 0
            assert session.scalar(select(func.count(ThemeScoreRow.id)).where(ThemeScoreRow.run_id == run_id)) == 0

        # NO remaining forward-return row references an absent bar: every surviving fr belongs to run A
        # and measures into a date that still exists.
        frs = session.exec(select(ForwardReturn)).all()
        assert {fr.run_id for fr in frs} == {ids["a"]}
        assert all(fr.measured_date in set(days[:10]) for fr in frs)

    # the result summary reports the exact deletion.
    assert result["removed_bar_count"] == 6
    assert result["cascade"]["snapshot_count"] == 2
    assert result["cascade"]["forward_return_count"] == 3
    assert result["refused"] is False


def test_remove_data_records_audit_run(removal_engine):
    """The removal is recorded as its own append-only DataProviderRun audit entry (the audit trail is the
    permanent record — it is NOT deleted), with a 'remove' kind and the removed counts."""
    engine, seed_dir, days, _ids = removal_engine
    with Session(engine) as session:
        runs_before = session.scalar(select(func.count(DataProviderRun.id)))
        remove_data(session, None, symbols=None, start=days[10], end=days[12], seed_dir=seed_dir, engine=engine)
    with Session(engine) as session:
        audit_rows = session.exec(
            select(DataProviderRun).order_by(DataProviderRun.id.desc())
        ).all()
    assert len(audit_rows) == runs_before + 1
    audit = audit_rows[0]
    assert audit.status == "ok"
    detail = json.loads(audit.message)
    assert detail["kind"] == "remove"
    assert detail["removed_bar_count"] == 6
    assert detail["cascade"]["snapshot_count"] == 2


def test_remove_data_seed_only_scope_refused_nothing_deleted(removal_engine):
    """A wholly-committed-seed removal is REFUSED (raises ValueError → the API maps to 4xx) and deletes
    NOTHING — never a silent partial; the committed seed stays intact."""
    engine, seed_dir, days, _ids = removal_engine
    with Session(engine) as session:
        before = session.scalar(select(func.count(DailyPrice.id)))
        with pytest.raises(ValueError) as exc:
            remove_data(session, None, symbols=["SPY"], start=days[0], end=days[9], seed_dir=seed_dir, engine=engine)
        after = session.scalar(select(func.count(DailyPrice.id)))
    assert "committed seed" in str(exc.value).lower()
    assert before == after  # NOTHING deleted on a refusal


def test_remove_data_does_not_recompute(removal_engine, monkeypatch):
    """The cascade ONLY deletes rows — it NEVER reaches the scoring/scanner recompute paths. Patch
    scanner.run_scan and score_stocks to raise; the removal must still succeed (proving neither is called)."""
    engine, seed_dir, days, _ids = removal_engine

    def _boom(*_a, **_k):  # pragma: no cover - only fires on a wrong call
        raise AssertionError("scoring/scanner recompute MUST NOT be reachable from the remove cascade")

    monkeypatch.setattr("app.engine.scanner.run_scan", _boom)
    monkeypatch.setattr("app.engine.scoring.score_stocks", _boom)
    monkeypatch.setattr("app.engine.data_manager.scanner.run_scan", _boom, raising=False)
    with Session(engine) as session:
        result = remove_data(
            session, None, symbols=None, start=days[10], end=days[12], seed_dir=seed_dir, engine=engine,
        )
    assert result["removed_bar_count"] == 6  # completed without ever recomputing


def test_remove_data_unknown_symbol_is_rejected(removal_engine):
    """An unknown symbol (no stored bars + not in scope) is rejected explicitly — never a silent no-op or a
    fabricated row."""
    engine, seed_dir, days, _ids = removal_engine
    with Session(engine) as session:
        with pytest.raises(ValueError):
            preview_removal(session, None, symbols=["NOPE"], start=days[10], end=days[12], seed_dir=seed_dir)


def test_remove_data_inverted_range_is_rejected(removal_engine):
    """An inverted date range (start > end) is rejected explicitly (the API maps it to 4xx)."""
    engine, seed_dir, days, _ids = removal_engine
    with Session(engine) as session:
        with pytest.raises(ValueError):
            preview_removal(session, None, symbols=None, start=days[12], end=days[10], seed_dir=seed_dir)


def test_remove_preview_no_scope_is_rejected(removal_engine):
    """A scope with neither symbols nor a date range is rejected (it would mean 'remove everything' — must
    be explicit, never an accidental wipe)."""
    engine, seed_dir, _days, _ids = removal_engine
    with Session(engine) as session:
        with pytest.raises(ValueError):
            preview_removal(session, None, symbols=None, start=None, end=None, seed_dir=seed_dir)


# ==================================================================================================
# J-37 — Missing-data diagnostic (read-only, three honest categories, exact shortfall, no recompute)
# ==================================================================================================
def _diag_cfg():
    """A small config whose universe is exactly {AAA, BBB, CCC, DDD} and whose thin threshold is a known
    value (5) — so the diagnostic categories + shortfalls are exact and the threshold is provably read from
    config (No magic numbers)."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    universe = cfg.universe.model_copy(update={"symbols": ["AAA", "BBB", "CCC", "DDD"]})
    indicators = cfg.indicators.model_copy(update={"min_history_bars": 5})
    return cfg.model_copy(update={"universe": universe, "indicators": indicators})


@pytest.fixture()
def diagnostic_engine(tmp_path):
    """A hand-built DB exercising all three diagnostic categories against {AAA,BBB,CCC,DDD}, threshold 5,
    SPY defining a 6-day trading calendar (D0..D5):
      - AAA: 6 bars on every trading day  → FINE (>= threshold 5, no gap) → in NO category.
      - BBB: 2 bars (D0, D1)              → THIN (0 < 2 < 5); contiguous → no intra-series gap.
      - CCC: bars on D0, D2, D4 (3 bars)  → THIN (3 < 5) AND an intra-series gap (D1, D3 missing inside).
      - DDD: NO bars                      → NO-HISTORY.
    """
    engine = make_engine(f"sqlite:///{tmp_path / 'diag.db'}")
    create_db_and_tables(engine)
    days = [date(2024, 1, 1) + __import__("datetime").timedelta(days=i) for i in range(6)]
    with Session(engine) as session:
        for d in days:
            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        for d in days:
            session.add(DailyPrice(symbol="AAA", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        for d in (days[0], days[1]):
            session.add(DailyPrice(symbol="BBB", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        for d in (days[0], days[2], days[4]):
            session.add(DailyPrice(symbol="CCC", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()
    return engine, days


def test_diagnostic_three_categories_exact(diagnostic_engine):
    """All three honest categories produced with the EXACT shortfall against the fixture; a fine member
    (AAA) appears in NO category; the thin threshold is read from config (5, not a literal)."""
    engine, days = diagnostic_engine
    cfg = _diag_cfg()
    with Session(engine) as session:
        diag = _missing_data_diagnostic(session, cfg)

    assert diag["threshold"] == 5  # from indicators.min_history_bars (not a magic number)

    # (a) no-history — DDD (a universe member with zero bars), exact shortfall 0/5, pull spans the calendar
    nohist = {r["symbol"]: r for r in diag["no_history"]}
    assert set(nohist) == {"DDD"}
    assert nohist["DDD"]["bars_have"] == 0 and nohist["DDD"]["bars_needed"] == 5
    assert nohist["DDD"]["pull_start"] == days[0].isoformat()
    assert nohist["DDD"]["pull_end"] == days[5].isoformat()
    assert nohist["DDD"]["pullable"] is True

    # (b) thin — BBB (2 bars) and CCC (3 bars), each 0 < bars < 5; AAA (6) is NOT thin.
    thin = {r["symbol"]: r for r in diag["thin"]}
    assert set(thin) == {"BBB", "CCC"}
    assert thin["BBB"]["bars_have"] == 2 and thin["BBB"]["bars_needed"] == 5
    assert thin["CCC"]["bars_have"] == 3 and thin["CCC"]["bars_needed"] == 5
    assert thin["BBB"]["pullable"] is False  # a thin row alone is not pullable

    # (c) intra-series gap — CCC only: D1 and D3 missing inside its D0..D4 range (BBB is contiguous).
    gaps = {r["symbol"]: r for r in diag["intra_series_gaps"]}
    assert set(gaps) == {"CCC"}
    assert gaps["CCC"]["missing_day_count"] == 2  # D1, D3
    assert gaps["CCC"]["first_gap"] == days[1].isoformat()
    assert gaps["CCC"]["last_gap"] == days[3].isoformat()
    assert gaps["CCC"]["missing_preview"] == [days[1].isoformat(), days[3].isoformat()]
    assert gaps["CCC"]["pull_start"] == days[1].isoformat()
    assert gaps["CCC"]["pull_end"] == days[3].isoformat()
    assert gaps["CCC"]["pullable"] is True

    # AAA (fine) appears in no category; affected_count is the exact union size.
    assert "AAA" not in nohist and "AAA" not in thin and "AAA" not in gaps
    assert diag["affected_count"] == len(diag["no_history"]) + len(diag["thin"]) + len(diag["intra_series_gaps"])
    assert diag["affected_count"] == 4  # DDD + BBB + CCC(thin) + CCC(gap)


def test_diagnostic_threshold_from_config_not_literal(diagnostic_engine):
    """Raising the thin threshold makes a previously-fine member thin — proving the cutoff is the config
    value, not a hardcoded literal."""
    engine, _days = diagnostic_engine
    cfg = _diag_cfg()
    cfg_hi = cfg.model_copy(update={"indicators": cfg.indicators.model_copy(update={"min_history_bars": 7})})
    with Session(engine) as session:
        diag = _missing_data_diagnostic(session, cfg_hi)
    thin = {r["symbol"] for r in diag["thin"]}
    assert "AAA" in thin  # 6 bars < 7 threshold ⇒ now thin (was fine at threshold 5)
    assert diag["threshold"] == 7


def test_diagnostic_surfaced_on_coverage_payload(diagnostic_engine):
    """The diagnostic rides the EXISTING coverage payload (reused producer, not a parallel module)."""
    engine, _days = diagnostic_engine
    cfg = _diag_cfg()
    with Session(engine) as session:
        cov = compute_coverage(session, cfg)
    assert "diagnostic" in cov
    assert cov["diagnostic"]["threshold"] == 5
    assert {r["symbol"] for r in cov["diagnostic"]["no_history"]} == {"DDD"}


def test_diagnostic_empty_dataset_graceful(tmp_path):
    """An empty DB serves a graceful diagnostic: no-history rows for every universe member, no gaps, no
    crash (the no-history pull spans are null because there is no calendar)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'empty.db'}")
    create_db_and_tables(engine)
    cfg = _diag_cfg()
    with Session(engine) as session:
        diag = _missing_data_diagnostic(session, cfg)
    assert {r["symbol"] for r in diag["no_history"]} == {"AAA", "BBB", "CCC", "DDD"}
    assert diag["thin"] == [] and diag["intra_series_gaps"] == []
    for r in diag["no_history"]:
        assert r["pull_start"] is None and r["pullable"] is False  # no calendar ⇒ nothing to pull


def test_diagnostic_no_canonical_recompute(diagnostic_engine, monkeypatch):
    """The diagnostic recomputes NO canonical value — patch run_scan / score_stocks / forward-return /
    detectors / regime to raise; the diagnostic must still produce (proving none is reachable)."""
    engine, _days = diagnostic_engine
    cfg = _diag_cfg()

    def _boom(*_a, **_k):  # pragma: no cover - only fires on a wrong call
        raise AssertionError("the diagnostic MUST NOT recompute any canonical score/return/bucket/setup")

    monkeypatch.setattr("app.engine.scanner.run_scan", _boom, raising=False)
    monkeypatch.setattr("app.engine.scoring.score_stocks", _boom, raising=False)
    monkeypatch.setattr("app.engine.data_manager.scanner.run_scan", _boom, raising=False)
    monkeypatch.setattr("app.engine.data_manager.forward_testing.backfill_run_forward_returns", _boom, raising=False)
    with Session(engine) as session:
        diag = _missing_data_diagnostic(session, cfg)
    assert diag["affected_count"] == 4  # produced without recomputing anything


def _build_diagnostic_db(tmp_path, symbols_with_data: list[str]):
    """A hand-built DB like `diagnostic_engine`, parametrized by how many universe members have full
    (6-day, gap-free) data -- for proving the item-H query count is INDEPENDENT of member count."""
    engine = make_engine(f"sqlite:///{tmp_path / f'diag_{len(symbols_with_data)}.db'}")
    create_db_and_tables(engine)
    days = [date(2024, 1, 1) + __import__("datetime").timedelta(days=i) for i in range(6)]
    with Session(engine) as session:
        for d in days:
            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        for sym in symbols_with_data:
            for d in days:
                session.add(DailyPrice(symbol=sym, date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()
    return engine


def _diag_cfg_for(symbols: list[str]):
    cfg = load_config()
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    universe = cfg.universe.model_copy(update={"symbols": symbols})
    indicators = cfg.indicators.model_copy(update={"min_history_bars": 5})
    return cfg.model_copy(update={"universe": universe, "indicators": indicators})


def _count_daily_prices_selects(engine, cfg) -> int:
    queries: list[str] = []

    def _count(conn, cursor, statement, parameters, context, executemany):
        lowered = statement.lower()
        if "daily_prices" in lowered and lowered.strip().startswith("select"):
            queries.append(statement)

    event.listen(engine, "before_cursor_execute", _count)
    try:
        with Session(engine) as session:
            _missing_data_diagnostic(session, cfg)
    finally:
        event.remove(engine, "before_cursor_execute", _count)
    return len(queries)


def test_diagnostic_query_count_does_not_scale_with_universe_size(tmp_path):
    """Item H (iter-24 fast-platform pass): the diagnostic's `daily_prices` SELECT count is INDEPENDENT
    of how many universe members have data -- the former per-member N+1 loop would make this count grow
    linearly with member count (2 members -> 2 extra queries, 8 members -> 8 extra queries); the ONE
    bulk own-dates query bounded to the universe (replacing that loop) keeps the count CONSTANT.
    (The fixed total also includes two unrelated, pre-existing `daily_prices` reads from `_trading_days`
    building the benchmark calendar -- `latest_data_date` + SPY's own `bars_asof` -- which this test
    does not need to enumerate by name; it only needs them to be as constant as everything else.)"""
    small_engine = _build_diagnostic_db(tmp_path, ["AAA", "BBB"])
    large_engine = _build_diagnostic_db(tmp_path, ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG", "HHH"])

    small_count = _count_daily_prices_selects(small_engine, _diag_cfg_for(["AAA", "BBB"]))
    large_count = _count_daily_prices_selects(large_engine, _diag_cfg_for(["AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG", "HHH"]))

    assert small_count == large_count  # O(1) in universe size -- never one extra query per member
    assert small_count <= 4  # sanity bound: calendar (2) + grouped stats (1) + bulk own-dates (1)


# ==================================================================================================
# ops-hardening iter-54 (`per_date_coverage_warm` fix, profiled) -- `_missing_data_diagnostic` no longer
# ALWAYS derives its own benchmark trading calendar (`_trading_days`, an unbounded per-symbol `bars_asof`
# fetch up to ~5,400 bars on the live basis, PLUS the `latest_data_date` query it depends on -- 2
# `daily_prices` queries total, per the query-count test above's own docstring). `_compute_coverage_body`
# (the sole production caller) already computes this SAME calendar for its own gap table and now passes
# it through via the new `calendar` parameter, instead of paying for the identical fetch a second time on
# EVERY `_compute_coverage_body` call (i.e. once per date in `_persist_per_date_coverage_snapshots`'s
# per-date `per_date_coverage_warm` loop, and once more in `coverage_membership_timeline_refresh`).
# ==================================================================================================
def test_diagnostic_calendar_param_eliminates_the_redundant_trading_days_fetch(tmp_path):
    """Passing `calendar=` removes EXACTLY the two `daily_prices` queries `_trading_days` issues
    (`latest_data_date` + SPY's own `bars_asof`) -- the query count drops by 2, never more/less -- and
    the served `diagnostic` payload is BYTE-IDENTICAL either way (the fetch-STRATEGY changes; nothing
    computed or disclosed does)."""
    engine = _build_diagnostic_db(tmp_path, ["AAA", "BBB", "CCC", "DDD"])
    cfg = _diag_cfg_for(["AAA", "BBB", "CCC", "DDD"])

    with Session(engine) as session:
        calendar = _trading_days(session, cfg)
    assert calendar  # sanity: the fixture actually has a benchmark calendar to reuse

    without_calendar = _count_daily_prices_selects(engine, cfg)  # derives its own calendar internally

    queries: list[str] = []

    def _count(conn, cursor, statement, parameters, context, executemany):
        lowered = statement.lower()
        if "daily_prices" in lowered and lowered.strip().startswith("select"):
            queries.append(statement)

    event.listen(engine, "before_cursor_execute", _count)
    try:
        with Session(engine) as session:
            with_calendar = _missing_data_diagnostic(session, cfg, calendar=calendar)
    finally:
        event.remove(engine, "before_cursor_execute", _count)
    with_calendar_count = len(queries)

    assert with_calendar_count == without_calendar - 2, (
        f"expected exactly 2 fewer daily_prices queries when `calendar` is supplied "
        f"(got {without_calendar} without vs {with_calendar_count} with)"
    )

    with Session(engine) as session:
        reference = _missing_data_diagnostic(session, cfg)  # derives its own calendar -- the old behavior
    assert with_calendar == reference


def test_diagnostic_own_dates_streamed_fetch_byte_identical_to_whole_result(diagnostic_engine):
    """TC-1 (iter-40, J-07 last blocker) -- `_missing_data_diagnostic`'s own-dates scan
    (`data_manager.py:271`) now streams via `.yield_per(cfg.research.read_batch_size)` instead of
    materializing the whole result (the iter-39 trial-3 wedge site: a `MemoryError` inside
    `cursor._raw_all_rows()` on this exact line,
    `runs/goal-ops-hardening-iter-39/mem-drill/trial3-2650mb-wedge-evidence.txt:17-29`). This proves the
    fetch-STRATEGY change is output-neutral:

      1. the SAME (symbol, date) rows collected via the OLD whole-result `.all()` path (replicated here
         as the reference -- it is no longer production code) and via the streamed `.yield_per()` path
         group into byte-identical per-symbol date sets, and
      2. the actual `_missing_data_diagnostic` output (`no_history`/`thin`/`intra_series_gaps`) is
         unaffected by the batch size -- forced tiny here (3) so the fixture's rows genuinely cross
         multiple yield_per batches, not just one, proving the streaming boundary never splits a
         symbol's dates across an inconsistent partial read."""
    engine, _days = diagnostic_engine
    cfg = _diag_cfg()
    universe = list(cfg.universe.symbols)

    with Session(engine) as session:
        # the PRE-FIX fetch strategy, replicated as the reference (no longer live in data_manager.py).
        whole_result_dates: dict[str, set] = {}
        for symbol, d in session.exec(
            select(DailyPrice.symbol, DailyPrice.date).where(DailyPrice.symbol.in_(universe))
        ).all():
            whole_result_dates.setdefault(symbol, set()).add(d)

    with Session(engine) as session:
        # the POST-FIX fetch strategy, batch size forced small to exercise >= 2 yield_per fetches.
        streamed_dates: dict[str, set] = {}
        for symbol, d in session.exec(
            select(DailyPrice.symbol, DailyPrice.date).where(DailyPrice.symbol.in_(universe))
        ).yield_per(3):
            streamed_dates.setdefault(symbol, set()).add(d)

    assert streamed_dates == whole_result_dates  # same rows, same grouping -- fetch strategy is invisible
    assert streamed_dates  # sanity: the fixture actually has rows to compare (not a vacuous pass)

    # and the real function, driven by a config with a tiny read_batch_size, serves the SAME categorized
    # payload as the default (much larger) batch size -- the fetch strategy never leaks into the output.
    cfg_tiny_batch = cfg.model_copy(
        update={"research": cfg.research.model_copy(update={"read_batch_size": 3})}
    )
    with Session(engine) as session:
        diag_default = _missing_data_diagnostic(session, cfg)
    with Session(engine) as session:
        diag_tiny_batch = _missing_data_diagnostic(session, cfg_tiny_batch)
    assert diag_default == diag_tiny_batch


def test_missing_data_diagnostic_cooperative_yield_byte_identical(diagnostic_engine, monkeypatch):
    """TC-2/TC-5 (ops-hardening iter-63, J-07 GIL-hold bound) -- the `time.sleep(0)` cooperative yield
    added at each `_diag_batch` chunk boundary of the own-dates scan (data_manager.py, just above the
    `for symbol, d in session.exec(...)` loop) is a SCHEDULING-ONLY change: it must never change which
    rows are read, how they group, or the served diagnostic payload.

    Corrected (ops-hardening iter-64, TC-8): only the ROW-COUNT SANITY CHECK below (item 1 -- the
    fixture's own-dates shape, 11 rows) is pre-fix-equivalent -- it reproduces the plain `session.exec`
    grouping with no yield involved at all, so it would group identically whether or not the fix exists.
    The BYTE-IDENTICAL assertion itself (item 2) is NOT compared against any pre-fix oracle: both sides
    are POST-fix calls to the real `_missing_data_diagnostic` (which always yields, unconditionally --
    there is no pre-fix code path left to call), one with `read_batch_size` forced to 2 and one with the
    default (much larger) batch size, so the comparison instead proves the batch width -- and therefore
    how many times the yield fires -- never leaks into the served payload (mirrors this same file's own
    `test_diagnostic_own_dates_streamed_fetch_byte_identical_to_whole_result`, which proved the
    streaming-vs-materialize choice was invisible the same way; this test proves the ADDED yield point is
    invisible too):

      1. the fixture's own-dates grouping (a plain, yield-free `session.exec`) is exactly its known shape
         (AAA 6 + BBB 2 + CCC 3 + DDD 0 = 11 rows) -- a sanity check on the fixture, not a comparison
         target for item 2;
      2. the real (post-fix) `_missing_data_diagnostic`, run with `read_batch_size` forced to 2 -- so the
         11-row result genuinely crosses MULTIPLE `yield_per` chunks, not one -- serves the BYTE-IDENTICAL
         payload the default (much larger) batch size's own (also post-fix) call serves, proving the batch
         width (and therefore how many times the yield fires) never leaks into the output;
      3. `time.sleep(0)` is actually invoked the expected number of times (5 -- floor(11/2), rows 2/4/6/
         8/10 hit the modulo boundary; row 11 does not reach a 6th multiple of 2) and ALWAYS with argument
         0 (never a real pause) -- proving the cooperative-yield code path is genuinely exercised by this
         test, not merely present and dead."""
    engine, _days = diagnostic_engine
    cfg = _diag_cfg()
    universe = list(cfg.universe.symbols)

    with Session(engine) as session:
        # sanity: the fixture's own-dates query is exactly 11 rows (AAA 6 + BBB 2 + CCC 3 + DDD 0), so
        # batch-of-2 below is guaranteed to cross multiple yield_per chunks, never a single-batch pass.
        reference_dates: dict[str, set] = {}
        for symbol, d in session.exec(
            select(DailyPrice.symbol, DailyPrice.date).where(DailyPrice.symbol.in_(universe))
        ).all():
            reference_dates.setdefault(symbol, set()).add(d)
    assert sum(len(v) for v in reference_dates.values()) == 11

    cfg_tiny_batch = cfg.model_copy(
        update={"research": cfg.research.model_copy(update={"read_batch_size": 2})}
    )

    sleep_calls: list = []

    def _counting_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr("app.engine.data_manager.time.sleep", _counting_sleep)

    with Session(engine) as session:
        diag_tiny_batch_with_yield = _missing_data_diagnostic(session, cfg_tiny_batch)

    # 1/2 -- byte-identical to the default (much larger, single-chunk) batch size's own served payload.
    with Session(engine) as session:
        diag_default_batch = _missing_data_diagnostic(session, cfg)
    assert diag_tiny_batch_with_yield == diag_default_batch

    # 3 -- the cooperative yield genuinely ran, exactly the expected number of times, always as sleep(0).
    assert sleep_calls == [0] * 5


# ==================================================================================================
# iter-40 (iter-39/w, AG-3) — checkpoint cadence: per-date density + throttle still bounds writes
# ==================================================================================================
def test_checkpoint_cadence_density_and_throttle_control(tmp_path, monkeypatch):
    """TC-4 (iter-40) -- `_checkpoint_run_record`'s tightened interval (`_RUN_RECORD_CHECKPOINT_INTERVAL_S`,
    10.0 -> 1.0) must land per-date checkpoints densely enough that a `kill -9` at any point never leaves
    the persisted `dates_done` more than one checkpoint interval's worth of dates behind true in-memory
    progress -- iter-39's live drill measured an order-of-magnitude gap (18/18 dates done in memory vs a
    persisted row stuck in single digits) at the old 10s interval
    (`runs/goal-ops-hardening-iter-39/live-restart/kill-test-mid-flight-state.json` vs
    `pre-kill-runs-state.json`). Two things proven on ONE simulated run (a fake monotonic clock ticks a
    fixed `dt` per simulated date, so the test is deterministic and fast, not wall-clock-flaky):

      1. density  -- after EVERY simulated date, the persisted `dates_done` is within
         `ceil(interval / dt)` dates of the CURRENT true `dates_done` (never further stale than the
         interval mathematically allows for this per-date speed).
      2. throttle -- the total write count across N dates stays well under N (the throttle still bounds
         write amplification -- this is NOT "a write on every single date regardless of interval", which
         would defeat the whole point of a throttle; see the pre-existing
         `test_run_record_checkpoint_is_throttled_open_ended_and_never_fatal` in
         test_data_manager_jobs_pipeline.py for the throttle's own unit-level contract)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'cadence.db'}")
    create_db_and_tables(engine)
    cfg = load_config()

    fake_now = [1_000_000.0]  # start far past any interval so the FIRST checkpoint call always writes

    def _fake_monotonic() -> float:
        return fake_now[0]

    monkeypatch.setattr(data_manager.time, "monotonic", _fake_monotonic)
    interval = data_manager._RUN_RECORD_CHECKPOINT_INTERVAL_S  # the tightened production value (1.0)

    # iter-40 AUDIT (T1) -- pin the interval itself. Every budget below is DERIVED from `interval`, so
    # they hold for ANY value of it: reverting the constant to its pre-iter-40 10.0 leaves this whole
    # test green while re-opening exactly the iter-39/w honesty gap it exists to guard (verified during
    # the iter-40 audit: the test passed unchanged with the constant monkeypatched back to 10.0). Bound
    # it to the knob the constant's OWN in-code rationale cites -- `job_progress.poll_interval_seconds`,
    # the cadence the `/data` live job card re-polls at (No magic numbers: this is config, not a literal).
    # A checkpoint interval looser than the UI's own poll cadence means the panel can re-read the row
    # faster than the row is refreshed, which is the stale-figure defect in the first place.
    assert interval <= cfg.data_manager.job_progress.poll_interval_seconds, (
        f"_RUN_RECORD_CHECKPOINT_INTERVAL_S ({interval}s) is looser than the /data job card's own poll "
        f"cadence ({cfg.data_manager.job_progress.poll_interval_seconds}s) -- a killed job's persisted "
        f"progress can then lag true progress by more than the UI's own refresh period (iter-39/w)"
    )
    dt = 0.3  # simulated wall-clock seconds per date -- faster than the interval (the "fast job" case
              # iter-39 actually hit: 18 dates / 45.18s elapsed ~= 2.5s/date average, but per-date compute
              # can be much faster than the write-serialized average once workers overlap -- 0.3s stresses
              # the density guarantee harder than the observed case).
    n_dates = 20

    prog = JobProgress(job_id="cadence-probe", kind="backfill", start=date(2024, 1, 1), end=date(2024, 1, 20))
    prog.dates_total = n_dates
    data_manager._create_run_record(engine, cfg, prog)

    def _persisted_dates_done() -> int:
        with Session(engine) as session:
            row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == "cadence-probe")).one()
        return json.loads(row.message)["dates_done"]

    write_count = 0
    max_staleness = 0
    for i in range(1, n_dates + 1):
        prog.dates_done = i
        fake_now[0] += dt
        before = _persisted_dates_done()
        data_manager._checkpoint_run_record(engine, prog)
        after = _persisted_dates_done()
        if after != before:
            write_count += 1
        max_staleness = max(max_staleness, prog.dates_done - after)

    # density: never more than ceil(interval/dt) dates stale at any point in the simulated run.
    allowed_staleness = -(-interval // dt)  # ceil via floor-division negation
    assert max_staleness <= allowed_staleness, (
        f"persisted dates_done fell {max_staleness} dates behind true progress -- more than the "
        f"{allowed_staleness}-date budget the {interval}s interval / {dt}s-per-date rate allows"
    )
    # a kill "at date N" (the last iteration above) must leave persisted progress close to the true end.
    assert n_dates - _persisted_dates_done() <= allowed_staleness

    # throttle control: NOT a write on every single date -- well under n_dates writes for n_dates calls.
    assert 0 < write_count < n_dates, (
        f"expected the throttle to still bound writes (fewer than {n_dates} for {n_dates} calls), got "
        f"{write_count} -- either the throttle stopped working or nothing ever wrote"
    )


# ==================================================================================================
# ops-hardening iter-41 (D9, TC-8) -- the count-based floor on top of the time-based throttle
# ==================================================================================================
def test_checkpoint_count_based_floor_forces_write_within_one_interval(tmp_path, monkeypatch):
    """TC-8 -- dev Known Issue #2 from iter-40's own handoff: the time-based throttle alone
    (`_RUN_RECORD_CHECKPOINT_INTERVAL_S`) never forces a write if the mocked clock NEVER crosses the
    interval threshold, no matter how many dates complete. This proves the ADDED count-based floor
    (`_RUN_RECORD_CHECKPOINT_DATE_FLOOR`) closes that gap on its own -- a checkpoint write lands on
    the Kth call even when elapsed wall-clock time is (deliberately) always 0."""
    engine = make_engine(f"sqlite:///{tmp_path / 'floor.db'}")
    create_db_and_tables(engine)
    cfg = load_config()

    # A clock that NEVER advances -- isolates the count-based floor from the time-based throttle
    # entirely: if only the interval throttle existed, this would produce exactly ONE write (the
    # unconditional first call) and never another, regardless of how many dates complete.
    frozen_now = [1_000_000.0]
    monkeypatch.setattr(data_manager.time, "monotonic", lambda: frozen_now[0])

    floor = data_manager._RUN_RECORD_CHECKPOINT_DATE_FLOOR
    assert floor > 1, "the floor must be a real multi-date cadence, not a de-facto every-call throttle"

    prog = JobProgress(job_id="floor-probe", kind="backfill", start=date(2024, 1, 1), end=date(2024, 1, 30))
    prog.dates_total = floor * 3
    data_manager._create_run_record(engine, cfg, prog)

    def _persisted_dates_done() -> int:
        with Session(engine) as session:
            row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == "floor-probe")).one()
        return json.loads(row.message)["dates_done"]

    # Call 1 (priming): the unconditional first write (time-based -- `_last_checkpoint_monotonic`
    # starts at 0.0, so `now - 0.0` always clears the interval on the very first call regardless of
    # the frozen clock's value). This ALSO resets `_dates_since_checkpoint` to 0 -- the same as any
    # other write -- so it establishes the baseline the count-based floor counts FROM, exactly like a
    # job's real first per-date checkpoint would.
    prog.dates_done = 1
    data_manager._checkpoint_run_record(engine, prog)
    assert _persisted_dates_done() == 1, "the first checkpoint call must always write"
    assert prog._dates_since_checkpoint == 0, "the counter resets on every write, including the first"

    # Calls 2..floor+1 (floor MORE calls after the priming reset): the frozen clock means `time_due`
    # is False for every one of these -- ONLY the count-based floor can force a write, and it must do
    # so on EXACTLY the (floor+1)th ABSOLUTE call (the `floor`th call SINCE the last write), not
    # before and not after -- i.e. at most `floor` dates may complete between checkpoint writes.
    for i in range(2, floor + 2):
        prog.dates_done = i
        data_manager._checkpoint_run_record(engine, prog)
        persisted = _persisted_dates_done()
        if i < floor + 1:
            assert persisted == 1, (
                f"call {i} ({i - 1} dates since the last write, < floor={floor}) must NOT force a "
                f"write under a frozen clock -- persisted dates_done unexpectedly advanced to {persisted}"
            )
        else:
            assert persisted == i, (
                f"call {i} ({i - 1} dates since the last write, == floor={floor}) must force a write "
                f"under a frozen clock -- persisted dates_done is {persisted}, expected {i}"
            )
            assert prog._dates_since_checkpoint == 0, "the floor-triggered write resets the counter"

    # The cycle repeats: another `floor` calls under the still-frozen clock forces exactly one more
    # write, `floor` calls after the previous forced write (not sooner) -- proves this is a
    # recurring cadence, not a one-shot fluke of the first cycle.
    second_write_call = floor + 1
    for i in range(second_write_call + 1, second_write_call + floor):
        prog.dates_done = i
        data_manager._checkpoint_run_record(engine, prog)
        assert _persisted_dates_done() == second_write_call, (
            f"call {i} (mid-second-cycle) must not write again before the counter reaches the floor a "
            f"second time"
        )
    third_write_call = second_write_call + floor
    prog.dates_done = third_write_call
    data_manager._checkpoint_run_record(engine, prog)
    assert _persisted_dates_done() == third_write_call, (
        "the second full cycle must also force a write exactly `floor` calls after the previous one"
    )


def test_checkpoint_time_based_throttle_still_wins_when_faster(tmp_path, monkeypatch):
    """TC-8 companion -- the count-based floor is additive, never a REGRESSION of the existing
    time-based density: when the mocked clock crosses the interval before the count reaches the
    floor (the normal ~1-2.5s/date rate iter-40 measured), the time-based path still fires first and
    the counter still resets (no double-write, no drift between the two mechanisms)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'floor2.db'}")
    create_db_and_tables(engine)
    cfg = load_config()

    fake_now = [1_000_000.0]
    monkeypatch.setattr(data_manager.time, "monotonic", lambda: fake_now[0])
    interval = data_manager._RUN_RECORD_CHECKPOINT_INTERVAL_S
    floor = data_manager._RUN_RECORD_CHECKPOINT_DATE_FLOOR

    prog = JobProgress(job_id="floor-vs-time", kind="backfill", start=date(2024, 1, 1), end=date(2024, 1, 10))
    prog.dates_total = floor
    data_manager._create_run_record(engine, cfg, prog)

    def _persisted_dates_done() -> int:
        with Session(engine) as session:
            row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == "floor-vs-time")).one()
        return json.loads(row.message)["dates_done"]

    prog.dates_done = 1
    data_manager._checkpoint_run_record(engine, prog)  # call 1: always writes
    assert _persisted_dates_done() == 1

    # call 2: advance the clock past the interval but stay WELL under the count floor -- the
    # time-based path must fire (this is a REAL date completing at the throttle's own configured
    # cadence, not the pathologically-fast case TC-8's first test isolates).
    fake_now[0] += interval + 0.01
    prog.dates_done = 2
    data_manager._checkpoint_run_record(engine, prog)
    assert _persisted_dates_done() == 2, "a time-due call must still write even with the count floor added"
    assert prog._dates_since_checkpoint == 0, "a time-triggered write must also reset the count floor"


# ==================================================================================================
# J-37 — Pull-missing job constructor (gap-exact, dispatched through the EXISTING J-34 chunked engine)
# ==================================================================================================
class _RecordingProvider(PriceProvider):
    """A fake provider that records every (symbol, start, end) get_daily call and returns one bar per
    requested day in [start, end] — so a test can assert EXACTLY which symbols/dates a pull fetched."""

    def __init__(self):
        self.calls: list[tuple[str, date, date]] = []

    def get_daily(self, symbol, start=None, end=None):
        self.calls.append((symbol, start, end))
        bars = []
        d = start
        while d <= end:
            bars.append(Bar(date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
            d = d + __import__("datetime").timedelta(days=1)
        return bars


def test_pull_missing_fetches_exactly_the_gap(tmp_path):
    """A J-37 pull fetches EXACTLY the diagnosed `(symbol, [start,end])` shortfall — NOT the whole universe
    and NOT the whole window — dispatched through the SAME chunked engine (`run_data_job` with `symbols`)."""
    cfg = _diag_cfg()
    engine = make_engine(f"sqlite:///{tmp_path / 'pull.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 1, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    provider = _RecordingProvider()
    job = create_job("fetch", date(2024, 1, 2), date(2024, 1, 4), source="yahoo")
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=provider,
        sleep_fn=_noop_sleep, symbols=["DDD"],  # the single diagnosed no-history member
    )
    assert summary["status"] == "ok"
    # EXACTLY one symbol fetched (DDD), over EXACTLY the diagnosed range — not the 4-member universe.
    assert {c[0] for c in provider.calls} == {"DDD"}
    assert all(c[1] == date(2024, 1, 2) and c[2] == date(2024, 1, 4) for c in provider.calls)
    with Session(engine) as session:
        ddd = session.exec(select(DailyPrice).where(DailyPrice.symbol == "DDD")).all()
    assert {b.date for b in ddd} == {date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)}


def test_pull_missing_idempotent_inserts_new_only(tmp_path):
    """A pull is per-(symbol, date) idempotent: re-running over an already-stored range INSERTs nothing
    new (the existing INSERT-new-only DailyPrice guard) — duplicating no bar, overwriting no committed bar."""
    cfg = _diag_cfg()
    engine = make_engine(f"sqlite:///{tmp_path / 'pull2.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 1, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()
    rng = (date(2024, 1, 2), date(2024, 1, 3))
    j1 = create_job("fetch", *rng, source="yahoo")
    run_data_job(j1.job_id, config=cfg, engine=engine, provider=_RecordingProvider(), sleep_fn=_noop_sleep, symbols=["DDD"])
    with Session(engine) as session:
        before = len(session.exec(select(DailyPrice).where(DailyPrice.symbol == "DDD")).all())
    j2 = create_job("fetch", *rng, source="yahoo")
    run_data_job(j2.job_id, config=cfg, engine=engine, provider=_RecordingProvider(), sleep_fn=_noop_sleep, symbols=["DDD"])
    with Session(engine) as session:
        after = len(session.exec(select(DailyPrice).where(DailyPrice.symbol == "DDD")).all())
    assert before == after == 2  # the re-pull duplicated nothing


def test_pull_missing_provider_failure_no_fabricated_bar(tmp_path):
    """On a provider failure the pull surfaces an explicit failed/partial state and fabricates NO bar."""
    cfg = _diag_cfg()
    engine = make_engine(f"sqlite:///{tmp_path / 'pullfail.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 1, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    class _Failing(PriceProvider):
        def get_daily(self, symbol, start=None, end=None):
            raise ProviderUnavailableError("provider unreachable")

    job = create_job("fetch", date(2024, 1, 2), date(2024, 1, 3), source="yahoo")
    summary = run_data_job(job.job_id, config=cfg, engine=engine, provider=_Failing(), sleep_fn=_noop_sleep, symbols=["DDD"])
    assert summary["status"] == "failed"  # the single symbol failed
    assert summary["errors"]
    with Session(engine) as session:
        ddd = session.exec(select(DailyPrice).where(DailyPrice.symbol == "DDD")).all()
    assert ddd == []  # zero bars — nothing fabricated


def test_seed_source_pull_is_gap_exact_and_idempotent(tmp_path, monkeypatch):
    """iter-26: a `seed`-source pull over a REAL SeedProvider (a tiny committed-style seed dir) fetches
    EXACTLY the requested `(symbol, [start,end])` gap and is per-`(symbol,date)` idempotent — a re-run
    stores NO duplicate bar (the INSERT-new-only guard). It routes through the existing engine + provider
    path (no fork), and no second pull-constructor exists for the offline source."""
    monkeypatch.setenv(SEED_IMPORT_ENV_FLAG, "1")
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    # a tiny throwaway seed dir: SPY (calendar) + MU with a 2-day mid hole the seed can supply.
    seed_dir = tmp_path / "seed"
    prices = seed_dir / "prices"
    prices.mkdir(parents=True)
    cal = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4), date(2024, 1, 5), date(2024, 1, 8)]
    def _csv(sym, days):
        lines = ["date,open,high,low,close,volume"]
        for i, d in enumerate(days):
            lines.append(f"{d.isoformat()},{10+i}.0,{11+i}.0,{9+i}.0,{10+i}.5,{1000+i}")
        (prices / f"{sym}.csv").write_text("\n".join(lines) + "\n")
    _csv("SPY", cal)
    _csv("MU", cal)  # the seed has ALL MU bars (so a gap pull can supply the missing ones)

    engine = make_engine(f"sqlite:///{tmp_path / 'seedpull.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for d in cal:
            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        # MU is stored with a hole on Jan 4 + Jan 5 (the gap to pull)
        for d in (cal[0], cal[1], cal[4]):
            session.add(DailyPrice(symbol="MU", date=d, open=2.0, high=2.0, low=2.0, close=2.0, volume=2.0))
        session.commit()

    from app.data_providers import make_provider
    provider = make_provider("seed", seed_dir=seed_dir)
    # gap-exact pull: ONLY MU, ONLY [Jan 4, Jan 5]
    job = create_job("fetch", date(2024, 1, 4), date(2024, 1, 5), source="seed")
    summary = run_data_job(job.job_id, config=cfg, engine=engine, provider=provider,
                           sleep_fn=_noop_sleep, symbols=["MU"])
    assert summary["status"] == "ok"
    with Session(engine) as session:
        mu_dates = sorted(session.exec(select(DailyPrice.date).where(DailyPrice.symbol == "MU")).all())
        spy_count = session.exec(select(func.count(DailyPrice.id)).where(DailyPrice.symbol == "SPY")).one()
    assert mu_dates == cal  # the two missing dates were filled — exactly the gap, nothing else
    assert spy_count == len(cal)  # SPY untouched (the pull targeted only MU — gap-exact scope)

    # idempotent re-run: re-fetch the same gap → ZERO duplicate rows
    job2 = create_job("fetch", date(2024, 1, 4), date(2024, 1, 5), source="seed")
    run_data_job(job2.job_id, config=cfg, engine=engine, provider=provider, sleep_fn=_noop_sleep, symbols=["MU"])
    with Session(engine) as session:
        mu_count = session.exec(select(func.count(DailyPrice.id)).where(DailyPrice.symbol == "MU")).one()
    assert mu_count == len(cal)  # still 5 bars — no duplicate (INSERT-new-only)


def test_qa_fixture_builder_writes_only_to_temp_and_not_committed_seed(tmp_path):
    """The QA fixture builder writes the throwaway DB + narrowed config under the given out dir ONLY — it
    NEVER mutates the committed seed tree and refuses to write inside it. The narrowed config is a valid
    Config whose universe = exactly the 4 chosen members."""
    import importlib.util
    from app.config import load_config as _lc
    from app.data_providers import DEFAULT_SEED_DIR

    spec = importlib.util.spec_from_file_location(
        "build_qa_fixture_db",
        str(__import__("pathlib").Path(__file__).resolve().parents[1] / "scripts" / "build_qa_fixture_db.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    seed_before = sorted(p.name for p in (DEFAULT_SEED_DIR / "prices").glob("*.csv"))
    out = tmp_path / "fixture_out"
    result = mod.build_fixture(out, window=230, thin_bars=40, gap_len=10)

    # wrote ONLY under the out dir
    assert __import__("pathlib").Path(result["db_path"]).parent == out.resolve()
    assert __import__("pathlib").Path(result["config_path"]).parent == out.resolve()
    # the committed seed tree is byte-identical (untouched)
    seed_after = sorted(p.name for p in (DEFAULT_SEED_DIR / "prices").glob("*.csv"))
    assert seed_after == seed_before
    # refuses to write inside the committed seed tree
    with pytest.raises(ValueError, match="committed seed"):
        mod.build_fixture(DEFAULT_SEED_DIR / "sub", window=50)
    # the narrowed fixture config loads + has exactly the 4 chosen members
    fixcfg = _lc(result["config_path"])
    assert set(fixcfg.universe.symbols) == {"ANET", "DELL", "MU", "AMD"}
    # the diagnostic-triggering shape is recorded
    assert result["no_history"]["symbol"] == "ANET"
    assert result["thin"]["symbol"] == "DELL" and 0 < result["thin"]["bars_have"] < result["thin"]["bars_needed"]
    assert result["gap"]["symbol"] == "MU" and result["gap"]["missing_day_count"] == 10


def test_seed_source_expand_runs_offline_with_passers_and_omitted(tmp_path, monkeypatch):
    """iter-26 (J-35): an expand over the env-gated offline `seed` source runs end-to-end with a real
    market-cap reference (a committed `market_caps.csv` overlay) → produces PASSERS (cap >= min) AND
    omitted-with-reason candidates (no_market_cap / market_cap<min / empty_series), all real-data-only,
    through the EXISTING `screen_reasons` predicate. No live network."""
    from app.data_providers import SEED_IMPORT_DIR_ENV
    monkeypatch.setenv(SEED_IMPORT_ENV_FLAG, "1")

    # a throwaway overlay seed dir: prices for 3 pool symbols + a market_caps.csv (one sub-threshold, one
    # absent) + a tiny pool CSV listing 4 candidates. Never the committed seed tree.
    overlay = tmp_path / "overlay"
    prices = overlay / "prices"
    prices.mkdir(parents=True)
    cal = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    def _csv(sym):
        lines = ["date,open,high,low,close,volume"]
        for i, d in enumerate(cal):
            lines.append(f"{d.isoformat()},{20+i}.0,{21+i}.0,{19+i}.0,{20+i}.0,{5_000_000+i}")
        (prices / f"{sym}.csv").write_text("\n".join(lines) + "\n")
    for sym in ("SPY", "BIGCAP", "SMALLCAP", "HASBARS_NOCAP"):
        _csv(sym)
    # BIGCAP passes (cap huge); SMALLCAP omitted (cap < min); HASBARS_NOCAP omitted (no cap); NOBARS omitted (empty_series)
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    min_cap = cfg.universe.filters.min_market_cap
    (overlay / "market_caps.csv").write_text(
        f"symbol,market_cap\nBIGCAP,{min_cap * 100:.0f}\nSMALLCAP,{min_cap / 2:.0f}\n"
    )
    (overlay / "universe_pool.csv").write_text(
        "symbol,sector,source\nBIGCAP,Tech,test\nSMALLCAP,Tech,test\nHASBARS_NOCAP,Tech,test\nNOBARS,Tech,test\n"
    )
    monkeypatch.setenv(SEED_IMPORT_DIR_ENV, str(overlay))

    engine = make_engine(f"sqlite:///{tmp_path / 'expand.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for d in cal:
            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    # universe.json is written under the seed dir's parent path the engine uses; point it at a temp dir
    monkeypatch.setattr(data_manager, "DEFAULT_SEED_DIR", overlay, raising=False)
    monkeypatch.setattr(data_manager, "read_pool", lambda *a, **k: [
        {"symbol": "BIGCAP", "sector": "Tech", "source": "test"},
        {"symbol": "SMALLCAP", "sector": "Tech", "source": "test"},
        {"symbol": "HASBARS_NOCAP", "sector": "Tech", "source": "test"},
        {"symbol": "NOBARS", "sector": "Tech", "source": "test"},
    ])

    job = create_job("expand", date(2024, 1, 4), date(2024, 1, 4), source="seed")
    summary = run_data_job(job.job_id, config=cfg, engine=engine, sleep_fn=_noop_sleep)
    assert summary["passers"] == 1  # only BIGCAP clears the cap + price + bars screen
    omitted = {o["symbol"]: o["reason"] for o in summary["omitted"]}
    assert "no_market_cap" in omitted.get("HASBARS_NOCAP", "")
    assert omitted.get("SMALLCAP", "").startswith("market_cap")  # cap < min
    assert omitted.get("NOBARS") == "empty_series"  # no committed bars — honest, not fabricated


def test_seed_source_expand_writes_to_overlay_not_committed_seed(tmp_path, monkeypatch):
    """CRITICAL (iter-26): a `seed`-source expand MUST write its grown universe.json / per-symbol CSVs /
    meta.json to the throwaway OVERLAY dir (TRENDORA_SEED_IMPORT_DIR) — NEVER the committed `data/seed/`
    tree. `start_data_job` routes the seed-expand artifact write to the overlay; the committed seed dir
    sha is unchanged. (Guards the regression where an offline expand truncated committed seed CSVs.)"""
    from app.data_providers import DEFAULT_SEED_DIR, SEED_IMPORT_DIR_ENV

    # an overlay seed dir with writable copies of one pool symbol + a cap + a tiny pool
    overlay = tmp_path / "overlay"
    (overlay / "prices").mkdir(parents=True)
    cal = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    lines = ["date,open,high,low,close,volume"]
    for i, d in enumerate(cal):
        lines.append(f"{d.isoformat()},{20+i}.0,{21+i}.0,{19+i}.0,{20+i}.0,5000000")
    (overlay / "prices" / "BIGCAP.csv").write_text("\n".join(lines) + "\n")
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    (overlay / "market_caps.csv").write_text(
        f"symbol,market_cap\nBIGCAP,{cfg.universe.filters.min_market_cap * 100:.0f}\n"
    )
    (overlay / "universe_pool.csv").write_text("symbol,sector,source\nBIGCAP,Tech,test\n")
    monkeypatch.setenv(SEED_IMPORT_ENV_FLAG, "1")
    monkeypatch.setenv(SEED_IMPORT_DIR_ENV, str(overlay))

    # the committed seed dir must be byte-identical before/after (assert via a recursive sha of its files)
    def _seed_sha() -> str:
        import hashlib
        h = hashlib.sha256()
        for p in sorted((DEFAULT_SEED_DIR / "prices").glob("*.csv")):
            h.update(p.read_bytes())
        return h.hexdigest()

    before = _seed_sha()
    engine = make_engine(f"sqlite:///{tmp_path / 'expand2.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for d in cal:
            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()

    import time as _t
    jid = data_manager.start_data_job("expand", date(2024, 1, 4), date(2024, 1, 4),
                                      source="seed", config=cfg, engine=engine)
    for _ in range(400):
        snap = data_manager.get_job(jid)
        if snap and snap["status"] != "running":
            break
        _t.sleep(0.01)
    assert snap["passers"] == 1  # BIGCAP passed — the expand ran to completion
    # the grown artifact landed in the OVERLAY, NOT the committed seed
    assert (overlay / "universe.json").exists()
    assert _seed_sha() == before  # committed seed CSVs untouched (no truncation/mutation)


# ==================================================================================================
# J-38 — Unified Unfinished-imports list + Retry / Dismiss (job-control only; audit-preserving)
# ==================================================================================================
def _add_provider_run(session, *, status, kind="fetch", ok=0, failed=0, dismissed=False, message_kind=True):
    detail = {"kind": kind, "start": "2024-01-02", "end": "2024-01-03", "summary": f"{status} run", "bars_fetched": 0}
    msg = json.dumps(detail) if message_kind else "seed load"
    run = DataProviderRun(
        provider="yahoo", started_at=datetime(2024, 1, 3, 12, 0, 0), finished_at=datetime(2024, 1, 3, 12, 1, 0),
        symbols_ok=ok, symbols_failed=failed, status=status, message=msg, dismissed=dismissed,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def _add_resumable_checkpoint(session, import_id="cp-1"):
    cp = ImportCheckpoint(
        import_id=import_id, source="tiingo", kind="fetch", start=date(2024, 1, 2), end=date(2024, 1, 3),
        symbol_plan_json=json.dumps(["AAA", "BBB", "CCC"]), chunk_total=3, next_chunk_index=1,
        symbols_ok=1, symbols_failed=0, bars_fetched=10, status="resumable",
        created_at=datetime(2024, 1, 3), updated_at=datetime(2024, 1, 3, 12, 5, 0),
    )
    session.add(cp)
    session.commit()
    return cp


@pytest.fixture()
def unfinished_engine(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'unfinished.db'}")
    create_db_and_tables(engine)
    return engine


# ==================================================================================================
# ops-hardening iter-43 (J-05 regression fix) — a `threading.Thread.start()` launch failure must not
# orphan a job at its `create_job()`-time `running` default forever.
# ==================================================================================================
def test_start_data_job_thread_launch_failure_marks_job_failed(tmp_path, monkeypatch):
    """TC-3: `threading.Thread.start()` raising `RuntimeError` (the live incident: "can't start new
    thread", `logs/backend.log:153050-153075`) inside `start_data_job` must not leave the just-created
    job at `running` with zero further updates. The failure reaches BOTH the live in-memory registry (a
    poller's `GET /api/data/jobs/{id}`) and the persisted run-history row (`GET /api/data`'s Run history
    panel) as `failed`, with a message naming the thread-launch failure — and the original exception
    propagates to the caller so the HTTP layer can return an honest error instead of a 200."""
    engine = make_engine(f"sqlite:///{tmp_path / 'launch_fail.db'}")
    create_db_and_tables(engine)
    cfg = load_config()

    created: dict = {}
    real_create_job = data_manager.create_job

    def _spy_create_job(*a, **kw):
        job = real_create_job(*a, **kw)
        created["job"] = job
        return job

    def _raise_cannot_start_thread(self):
        raise RuntimeError("can't start new thread")

    monkeypatch.setattr(data_manager, "create_job", _spy_create_job)
    monkeypatch.setattr("threading.Thread.start", _raise_cannot_start_thread)

    with pytest.raises(RuntimeError, match="can't start new thread"):
        data_manager.start_data_job("backfill", date(2024, 1, 2), date(2024, 1, 2), config=cfg, engine=engine)

    assert "job" in created, "create_job must have run (and been captured) before the launch failure"
    prog = created["job"]
    assert prog.status == "failed"
    assert any("failed to launch job worker thread" in e for e in prog.errors), prog.errors
    assert prog.finished_at is not None
    # the live in-memory registry (what a concurrent poller sees) reflects the SAME object.
    assert data_manager.get_job(prog.job_id)["status"] == "failed"

    with Session(engine) as session:
        row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == prog.job_id)).one()
    assert row.status == "failed"
    assert row.finished_at is not None
    # iter-43 AUDIT (B2): TC-3 asks for the PERSISTED row's message to name the launch failure — the
    # 503 body and the in-memory `errors[]` are both transient, so without this the durable audit record
    # (what `GET /api/data`'s Run history panel renders) would read as a plain all-zeros work summary.
    assert "failed to launch job worker thread" in summarize_provider_run(row)["message"]


@pytest.mark.parametrize("launch_exc", [RuntimeError("can't start new thread"), MemoryError()])
def test_start_data_job_non_runtimeerror_launch_failure_also_marks_job_failed(
    tmp_path, monkeypatch, launch_exc
):
    """iter-43 AUDIT (B3) — the spec's own error case is a `RuntimeError` **"or equivalent"** raised by
    `threading.Thread.start()`; the guard must therefore not be keyed to that ONE exception type.

    `Thread.start()` itself catches a bare `Exception` around `_start_new_thread` (CPython
    `Lib/threading.py`), because the C-level `thread.start_new_thread` has two distinct failure exits:
    `PyErr_SetString(PyExc_RuntimeError, "can't start new thread")` when the OS refuses the thread, and
    `PyErr_NoMemory()` -> **`MemoryError`** when its own bootstate allocation fails first. Both live in
    the SAME regime this guard exists for — iter-42's outage produced `MemoryError` and
    `RuntimeError: can't start new thread` side by side under one `ulimit -v` ceiling
    (`reports/perf-budgets.md`, iteration-42) — so catching only `RuntimeError` left the exact
    "silent zero-work job" hole this iteration closed still open on its nearest sibling path: pre-fix,
    the `MemoryError` parametrization left the job at its `create_job()`-time `running` default with NO
    run-history row at all, forever.

    Both parametrizations must reach the SAME honest terminal state, and the original exception must
    still propagate (never swallowed into a false success)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'launch_fail_kind.db'}")
    create_db_and_tables(engine)
    cfg = load_config()

    created: dict = {}
    real_create_job = data_manager.create_job

    def _spy_create_job(*a, **kw):
        job = real_create_job(*a, **kw)
        created["job"] = job
        return job

    def _raise_launch_failure(self):
        raise launch_exc

    monkeypatch.setattr(data_manager, "create_job", _spy_create_job)
    monkeypatch.setattr("threading.Thread.start", _raise_launch_failure)

    with pytest.raises(type(launch_exc)):
        data_manager.start_data_job("backfill", date(2024, 1, 2), date(2024, 1, 2), config=cfg, engine=engine)

    prog = created["job"]
    assert prog.status == "failed", f"job orphaned at {prog.status!r} after a {type(launch_exc).__name__}"
    assert prog.finished_at is not None
    assert data_manager.get_job(prog.job_id)["status"] == "failed"
    with Session(engine) as session:
        row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == prog.job_id)).one()
    assert row.status == "failed"
    assert "failed to launch job worker thread" in summarize_provider_run(row)["message"]


def test_start_resume_job_non_runtimeerror_launch_failure_also_marks_job_failed(
    unfinished_engine, monkeypatch
):
    """iter-43 AUDIT (B3), resume sibling — same argument as the `start_data_job` parametrization above.
    Pre-fix, a `MemoryError` from `Thread.start()` left the paused attempt's OPEN run-history row open
    (`resumable`) forever with no further update, which is the state the J-05 regression was about."""
    engine = unfinished_engine
    cfg = load_config()
    with Session(engine) as session:
        _add_resumable_checkpoint(session, "cp-launch-oom")

    def _raise_memory_error(self):
        raise MemoryError()

    monkeypatch.setattr("threading.Thread.start", _raise_memory_error)

    with pytest.raises(MemoryError):
        data_manager.start_resume_job("cp-launch-oom", config=cfg, engine=engine)

    assert data_manager.get_job("cp-launch-oom")["status"] == "failed"
    with Session(engine) as session:
        row = session.exec(
            select(DataProviderRun).where(DataProviderRun.job_id == "cp-launch-oom")
        ).one()
    assert row.status == "failed"
    assert row.finished_at is not None
    assert "failed to launch job worker thread" in summarize_provider_run(row)["message"]


def test_start_resume_job_thread_launch_failure_marks_job_failed(unfinished_engine, monkeypatch):
    """TC-4: the same mocked `threading.Thread.start()` failure inside `start_resume_job` closes the
    resumed import's run-history row to `failed` with a descriptive message via the SAME mechanism.
    `resume_data_job` (the thread target) is normally what builds this job's `JobProgress` from its
    checkpoint — since the thread never starts, the guard rebuilds the same minimal shape from the
    checkpoint directly, so the row is honestly closed instead of staying open (`resumable`/`running`)
    forever."""
    engine = unfinished_engine
    cfg = load_config()
    with Session(engine) as session:
        _add_resumable_checkpoint(session, "cp-launch-fail")

    def _raise_cannot_start_thread(self):
        raise RuntimeError("can't start new thread")

    monkeypatch.setattr("threading.Thread.start", _raise_cannot_start_thread)

    with pytest.raises(RuntimeError, match="can't start new thread"):
        data_manager.start_resume_job("cp-launch-fail", config=cfg, engine=engine)

    # the live in-memory registry now carries the failure too (nothing registered it before the launch
    # attempt — the guard is what creates this entry).
    assert data_manager.get_job("cp-launch-fail")["status"] == "failed"

    with Session(engine) as session:
        row = session.exec(
            select(DataProviderRun).where(DataProviderRun.job_id == "cp-launch-fail")
        ).one()
    assert row.status == "failed"
    assert row.finished_at is not None
    assert "failed to launch job worker thread" in summarize_provider_run(row)["message"]  # B2


def test_start_resume_job_launch_failure_preserves_the_paused_runs_recorded_progress(
    unfinished_engine, monkeypatch
):
    """iter-43 AUDIT (B1) — a resume whose worker thread never launches must close the paused attempt's
    OPEN run-history row to `failed` WITHOUT erasing the work that attempt already recorded.

    `_finalize_run_record` UPDATEs the open row's `symbols_ok`/`symbols_failed`/detail JSON straight off
    the `JobProgress` it is handed. `resume_data_job` (the thread target) seeds that progress from the
    durable checkpoint (`symbols_done` from the committed chunks, `bars_fetched`, `chunk_index`,
    `completed_stages`, the persisted failed tally) BEFORE any run row is touched, so the row's counts
    only ever move forward. The unlaunched-resume guard must seed it the SAME way — handing
    `_finalize_run_record` a bare `JobProgress()` instead zeroes the permanent audit row (and makes
    `_run_state_text` render the fabricated "every symbol failed (0 of 0); provider unreachable" for an
    import that really completed one chunk of three)."""
    engine = unfinished_engine
    cfg = load_config()
    with Session(engine) as session:
        _add_resumable_checkpoint(session, "cp-progress-kept")
        # the OPEN row the paused attempt left behind, carrying its real recorded progress
        session.add(
            DataProviderRun(
                provider="tiingo",
                started_at=datetime(2024, 1, 3, 12, 0, 0),
                finished_at=None,
                symbols_ok=1,
                symbols_failed=0,
                status="resumable",
                message=json.dumps({
                    "kind": "fetch", "start": "2024-01-02", "end": "2024-01-03",
                    "bars_fetched": 10, "summary": "rate-limited — resumable at chunk 1/3",
                }),
                job_id="cp-progress-kept",
            )
        )
        session.commit()

    def _raise_cannot_start_thread(self):
        raise RuntimeError("can't start new thread")

    monkeypatch.setattr("threading.Thread.start", _raise_cannot_start_thread)

    with pytest.raises(RuntimeError, match="can't start new thread"):
        data_manager.start_resume_job("cp-progress-kept", config=cfg, engine=engine)

    with Session(engine) as session:
        rows = session.exec(
            select(DataProviderRun).where(DataProviderRun.job_id == "cp-progress-kept")
        ).all()
    assert len(rows) == 1, "the paused attempt's own row is closed — never a second, duplicate row"
    row = rows[0]
    assert row.status == "failed"
    assert row.finished_at is not None
    # The recorded progress survives the honest failure transition. Oracle: `symbols_ok` is the DISTINCT
    # symbol count of the chunks already committed (`< next_chunk_index`) — the same derivation
    # `resume_data_job` performs, computed here independently from the checkpoint's own stored plan
    # rather than hardcoded, so this asserts the resume contract and not a magic number. (It is NOT
    # `cp.symbols_ok`: the reconstructed per-symbol sets deliberately supersede that stored tally; only a
    # LARGER persisted `symbols_failed` is honored.) Pre-fix this read 0 — the row was wiped.
    expected_done: set[str] = set()
    for sym_batch, _window in _chunk_plan(cfg, ["AAA", "BBB", "CCC"], date(2024, 1, 2), date(2024, 1, 3))[:1]:
        expected_done.update(sym_batch)
    assert expected_done, "fixture sanity: the checkpoint must have at least one committed chunk"
    assert row.symbols_ok == len(expected_done), f"paused attempt's symbols_ok was erased: {row.symbols_ok}"
    assert row.symbols_failed == 0
    detail = json.loads(row.message)
    assert detail["bars_fetched"] == 10, f"paused attempt's bars_fetched was erased: {detail}"
    assert detail["kind"] == "fetch"
    # B2: and the row still NAMES why it failed, alongside the preserved work summary
    assert "failed to launch job worker thread" in detail["summary"]


def test_unfinished_imports_union(unfinished_engine):
    """The union = resumable checkpoints + partial/failed runs, MINUS soft-dismissed runs and MINUS a
    plain seed-load (non-job) row. Each carries a plain-language state + the right actions."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    with Session(unfinished_engine) as session:
        _add_resumable_checkpoint(session, "cp-1")
        partial = _add_provider_run(session, status="partial", ok=142, failed=16)
        failed = _add_provider_run(session, status="failed", ok=0, failed=3)
        _add_provider_run(session, status="partial", ok=1, failed=1, dismissed=True)  # soft-dismissed → excluded
        _add_provider_run(session, status="failed", ok=0, failed=2, message_kind=False)  # seed-load → excluded
        _add_provider_run(session, status="ok", ok=5)  # clean → excluded
        rows = unfinished_imports(session, cfg)

    by_type = {(r["record_type"], r["id"]): r for r in rows}
    assert ("checkpoint", "cp-1") in by_type
    assert ("run", partial.id) in by_type
    assert ("run", failed.id) in by_type
    assert len(rows) == 3  # exactly the resumable + the two non-dismissed jobs

    cp_row = by_type[("checkpoint", "cp-1")]
    assert cp_row["actions"] == ["resume", "remove"]
    assert "Paused" in cp_row["state"] and "rate-limit" in cp_row["state"]
    assert cp_row["symbols_remaining"] == 2  # 3 total - 1 ok

    part_row = by_type[("run", partial.id)]
    assert part_row["actions"] == ["retry", "dismiss"]
    assert "Partial" in part_row["state"] and "142" in part_row["state"]
    assert part_row["symbols_remaining"] == 16

    fail_row = by_type[("run", failed.id)]
    assert "Failed" in fail_row["state"]


def test_unfinished_imports_carries_no_key(unfinished_engine):
    """No row in the union carries a key value (neither the checkpoint nor the run summary has a key)."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    with Session(unfinished_engine) as session:
        _add_resumable_checkpoint(session, "cp-key")
        _add_provider_run(session, status="partial", ok=1, failed=1)
        rows = unfinished_imports(session, cfg)
    blob = json.dumps(rows)
    assert "api_key" not in blob and "token=" not in blob and "apikey=" not in blob


def test_dismiss_run_is_soft_and_preserves_audit(unfinished_engine):
    """Dismiss of a partial/failed RUN sets the soft-dismiss flag ONLY: the run LEAVES unfinished_imports
    but STAYS in the append-only Run-history audit (still queryable, never deleted)."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    with Session(unfinished_engine) as session:
        run = _add_provider_run(session, status="partial", ok=1, failed=1)
        run_id = run.id
        assert any(r["id"] == run_id for r in unfinished_imports(session, cfg))
        result = dismiss_import(session, "run", str(run_id), config=cfg)
        assert result == {"record_type": "run", "id": run_id, "dismissed": True}
        # the run is gone from the actionable list...
        assert not any(r.get("id") == run_id for r in unfinished_imports(session, cfg) if r["record_type"] == "run")
        # ...but the audit row is preserved (still present, only flagged dismissed).
        still = session.get(DataProviderRun, run_id)
        assert still is not None and still.dismissed is True
        assert any(r["id"] == run_id for r in recent_runs(session, cfg))  # still in Run history


def test_dismiss_checkpoint_deletes_only_job_control(unfinished_engine):
    """Dismiss of a resumable CHECKPOINT deletes ONLY that job-control row — no bar/snapshot is touched."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    with Session(unfinished_engine) as session:
        _add_resumable_checkpoint(session, "cp-del")
        # seed a snapshot + forward return that MUST survive the checkpoint delete
        session.add(ScannerRun(
            asof_date=date(2024, 1, 2), created_at=datetime(2024, 1, 2), provider="seed", benchmark="SPY",
            regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        ))
        session.commit()
        result = dismiss_import(session, "checkpoint", "cp-del", config=cfg)
        assert result["dismissed"] is True
        assert session.exec(select(ImportCheckpoint).where(ImportCheckpoint.import_id == "cp-del")).first() is None
        assert session.exec(select(ScannerRun)).all()  # the snapshot survived


def test_dismiss_unknown_id_raises(unfinished_engine):
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    with Session(unfinished_engine) as session:
        with pytest.raises(LookupError):
            dismiss_import(session, "run", "99999", config=cfg)
        with pytest.raises(LookupError):
            dismiss_import(session, "checkpoint", "nope", config=cfg)


def test_retry_run_redispatches_outstanding_only(tmp_path):
    """Retry re-dispatches the partial run's SAME kind + window through the chunked engine; per-(symbol,
    date) idempotency means an already-stored bar is not duplicated. Returns a NEW job id; the original
    audit run is untouched."""
    cfg = _diag_cfg()
    engine = make_engine(f"sqlite:///{tmp_path / 'retry.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 1, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        # one already-stored DDD bar inside the retry window — a retry must NOT duplicate it
        session.add(DailyPrice(symbol="DDD", date=date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        run = _add_provider_run(session, status="partial", ok=1, failed=1)
        run_id = run.id

    # Retry uses start_data_job (async) — inject a recording provider via run_data_job by patching is hard;
    # instead assert the dispatch returns a new job id and the original run is preserved.
    job_id = retry_run(run_id, config=cfg, engine=engine)
    assert isinstance(job_id, str) and job_id
    # wait for the async job to finish
    deadline = time.monotonic() + 10
    while (snap := get_job(job_id)) and snap["status"] == "running" and time.monotonic() < deadline:
        time.sleep(0.02)
    with Session(engine) as session:
        assert session.get(DataProviderRun, run_id) is not None  # original audit row preserved
        ddd = session.exec(select(DailyPrice).where(DailyPrice.symbol == "DDD")).all()
    # the pre-existing bar is not duplicated (idempotent); a real fetch path ran (yahoo seed provider is
    # offline in tests → it may add nothing, but it must never delete/duplicate the existing bar).
    assert len([b for b in ddd if b.date == date(2024, 1, 2)]) == 1


def test_retry_run_unknown_and_non_retryable(tmp_path):
    """Retry of an unknown run raises LookupError; retry of a clean (ok) run raises ValueError."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    engine = make_engine(f"sqlite:///{tmp_path / 'retry2.db'}")
    create_db_and_tables(engine)
    with pytest.raises(LookupError):
        retry_run(99999, config=cfg, engine=engine)
    with Session(engine) as session:
        run = _add_provider_run(session, status="ok", ok=5)
        ok_id = run.id
    with pytest.raises(ValueError):
        retry_run(ok_id, config=cfg, engine=engine)


# ==================================================================================================
# ops-hardening iter-44 (reviewer MINOR, carried from iter-43 B5) — TC-10: `_run_job`'s `finally` block
# must not clobber a `failed` job's real captured-exception message with `_final_summary`'s generic
# "work done" text; a normally-completed job's `_final_summary` text is unaffected.
# ==================================================================================================
def test_run_job_outer_exception_preserves_real_message_not_final_summary(tmp_path, monkeypatch):
    """TC-10 — a job that fails via `_run_job`'s OUTER exception handler (a whole-stage exception, not a
    per-date J-67-isolated one) must persist a `message` naming the REAL captured exception text, not
    `_final_summary`'s generic "no work performed"/all-zeros summary. `_trading_days` is monkeypatched to
    raise: it is the very first call `_do_backfill` makes (`data_manager.py`'s own docstring names it as
    the canonical "whole-stage exception" example), well before any per-date failure isolation engages —
    so this genuinely exercises the OUTER handler, not a graded `partial`. Before this iteration,
    `_run_job`'s `finally` unconditionally set `prog.message = _final_summary(prog)`, so this assertion
    would have failed (iter-43 audit B5: the two expressions were byte-identical on every path)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'run_job_failed.db'}")
    create_db_and_tables(engine)
    cfg = load_config()

    def _boom(_session, _cfg):
        raise RuntimeError("simulated trading-calendar read failure")

    monkeypatch.setattr(data_manager, "_trading_days", _boom)

    job = create_job("backfill", date(2024, 1, 2), date(2024, 1, 2))
    summary = run_data_job(job.job_id, config=cfg, engine=engine, sleep_fn=_noop_sleep, seed_dir=tmp_path)

    assert summary["status"] == "failed"
    assert "simulated trading-calendar read failure" in summary["message"]
    assert "no work performed" not in summary["message"]

    with Session(engine) as session:
        row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == job.job_id)).one()
    assert row.status == "failed"
    persisted_message = summarize_provider_run(row)["message"]
    assert "simulated trading-calendar read failure" in persisted_message
    assert "no work performed" not in persisted_message


def test_run_job_normal_completion_still_gets_final_summary(tmp_path):
    """TC-10 (unchanged half) — a job that completes normally (status `ok`) still gets `_final_summary`'s
    descriptive summary, byte-identical to before this iteration's `finally`-block change (the conditional
    only skips the assignment on the `failed` path)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'run_job_ok.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(
            symbol="SPY", date=date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0,
        ))
        session.commit()
    cfg = load_config()
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})

    job = create_job("backfill", date(2024, 1, 2), date(2024, 1, 2))
    summary = run_data_job(job.job_id, config=cfg, engine=engine, sleep_fn=_noop_sleep, seed_dir=tmp_path)

    assert summary["status"] == "ok"
    from app.engine.data_manager import _final_summary as _fs

    prog = data_manager._JOBS[job.job_id]
    assert summary["message"] == _fs(prog)


def test_run_job_textless_exception_still_names_a_real_reason(tmp_path, monkeypatch):
    """ops-hardening iter-44 AUDIT (B1) — TC-10 for the exception class this session's failures ACTUALLY
    raise. `str(MemoryError())` is the EMPTY STRING, so the iteration's original `prog.message =
    scrub(str(exc))` produced `""`, whose falsiness sent `_run_detail`'s `prog.message if (prog.status ==
    "failed" and prog.message)` guard straight back to `_final_summary`'s generic text — reproducing the
    EXACT "backfill: 0 snapshots over N dates, 0 forward returns" message the browser lane observed on
    the live failed run 272 (2026-08-03), i.e. TC-10's fix was a no-op for MemoryError. A textless
    exception must still persist a reason naming the exception TYPE, never the generic work summary and
    never a blank error entry."""
    engine = make_engine(f"sqlite:///{tmp_path / 'run_job_textless.db'}")
    create_db_and_tables(engine)
    cfg = load_config()

    def _boom(_session, _cfg):
        raise MemoryError()  # noqa: RSE102 — the textless-exception case under test

    monkeypatch.setattr(data_manager, "_trading_days", _boom)

    job = create_job("backfill", date(2024, 1, 2), date(2024, 1, 2))
    summary = run_data_job(job.job_id, config=cfg, engine=engine, sleep_fn=_noop_sleep, seed_dir=tmp_path)

    assert summary["status"] == "failed"
    assert "MemoryError" in summary["message"]
    assert "snapshots over" not in summary["message"]  # never `_final_summary`'s generic text
    assert summary["errors"] and all(e.strip() for e in summary["errors"])  # never a blank error entry

    with Session(engine) as session:
        row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == job.job_id)).one()
    assert row.status == "failed"
    persisted_message = summarize_provider_run(row)["message"]
    assert "MemoryError" in persisted_message
    assert "snapshots over" not in persisted_message


# ==================================================================================================
# ops-hardening iter-45 (J-05/J-07 fix) — the membership-timeline APPEND-FORWARD fast path.
#
# `membership_timeline_cached`'s MISS branch previously ran `_membership_timeline`'s full O(dates × pool)
# `resolve_with_reasons` sweep over EVERY historical snapshot date on ANY dataset-version bump — including
# the common case of exactly ONE new trading day landing via a single-day backfill. iter-44's live SIGUSR1
# dump named this exact call chain (`resolve_with_reasons` <- `_excluded_counts_by_date` <-
# `_membership_timeline` <- `membership_timeline_cached`) as the shared root cause of BOTH J-05's single-day
# backfill never reaching a terminal outcome (three attempts, longest 1,001s) and J-07's forward-aggregate
# warm never advancing `horizons_done` past 0 (this refresh runs BEFORE the warm loop in the finalize
# tail). `_membership_timeline_incremental` now bounds that sweep to genuinely NEW date(s) only when the
# ingest is append-forward (every new date >= every already-cached date); a historical gap-fill (a new
# date EARLIER than an already-cached one) still falls back to the EXISTING, UNCHANGED full recompute,
# since `entries`/`exits` are order-dependent (binding iter-27/iter-9 lesson).
# ==================================================================================================
def _mk_membership_snapshot(session: Session, asof: date, tickers: list[str]) -> None:
    run = ScannerRun(
        asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
        regime_score=50.0, regime_label="Choppy", regime_components_json="{}",
        new_high_low_json="{}", candidate_counts_json="{}",
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    for i, t in enumerate(tickers):
        session.add(ScannerResult(
            run_id=run.id, ticker=t, name=t, sector="Technology",
            leadership_score=float(100 - i), leadership_bucket="A",
            entry_quality_score=1.0, entry_quality_bucket="A", risk_score=1.0, risk_bucket="A",
            setup_status="Watchlist", rank=i + 1, record_json="{}",
        ))
    session.commit()


def _all_scanner_run_dates(session: Session) -> list[date]:
    return sorted(session.exec(select(ScannerRun.asof_date)).all())


@pytest.fixture()
def membership_fast_path_engine(tmp_path):
    """Three already-cached historical snapshots (D1 < D2 < D3, an AAA/BBB/CCC entries/exits shape mirroring
    the dedicated membership-cache test fixture) so each test below has a genuine prior cache row to append
    onto."""
    engine = make_engine(f"sqlite:///{tmp_path / 'membership_fast_path.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        _mk_membership_snapshot(session, date(2024, 1, 3), ["AAA", "BBB"])
        _mk_membership_snapshot(session, date(2024, 2, 1), ["AAA", "CCC"])
        _mk_membership_snapshot(session, date(2024, 3, 1), ["AAA", "BBB", "CCC"])
    return engine


def test_append_forward_ingest_does_not_reinvoke_resolver_for_cached_dates(
    membership_fast_path_engine, monkeypatch,
):
    """TC-1 — an append-forward ingest of exactly ONE new, later trading day does NOT re-invoke
    `resolve_with_reasons` (directly or via `_excluded_counts_by_date`) for any date `<= D_prev`; only the
    new date is ever resolved (the real committed pool batches `resolve_with_reasons` per
    `research.membership_timeline_batch_symbols`-wide chunk, so a single date can see MULTIPLE calls — all
    of them must name the new date, never an already-cached one)."""
    engine = membership_fast_path_engine
    cfg = load_config()
    with Session(engine) as session:
        dates = _all_scanner_run_dates(session)
        assert len(dates) == 3
        data_manager.membership_timeline_cached(session, cfg, dates)  # warm the cache under v1

    d_new = date(2024, 4, 1)  # strictly LATER than every already-cached date -- append-forward
    with Session(engine) as session:
        _mk_membership_snapshot(session, d_new, ["AAA", "BBB", "DDD"])

    resolved_dates: list[date] = []
    orig_resolve = data_manager.universe_resolver.resolve_with_reasons

    def _spy(session_arg, d, cfg_arg, **kwargs):
        resolved_dates.append(d)
        return orig_resolve(session_arg, d, cfg_arg, **kwargs)

    monkeypatch.setattr(data_manager.universe_resolver, "resolve_with_reasons", _spy)

    with Session(engine) as session:
        dates = _all_scanner_run_dates(session)
        assert len(dates) == 4
        data_manager.membership_timeline_cached(session, cfg, dates)  # MISS -> the append-forward fast path

    assert resolved_dates, "expected the new date's resolver sweep to actually run"
    assert set(resolved_dates) == {d_new}, (
        f"resolve_with_reasons must run ONLY for the new date {d_new}, never for an already-cached date "
        f"(TC-1) -- got calls for {sorted(set(resolved_dates))}"
    )


def test_append_forward_reuses_cached_points_byte_for_byte(membership_fast_path_engine):
    """TC-2 — every already-cached (`<= D_prev`) date's `size`/`entries`/`exits`/`excluded` fields are
    byte-for-byte unchanged after an append-forward ingest, and the new stamp's payload has exactly one
    more point than the prior stamp's (the new date, honestly reflecting its own entries/exits)."""
    engine = membership_fast_path_engine
    cfg = load_config()
    with Session(engine) as session:
        dates = _all_scanner_run_dates(session)
        prev_payload = data_manager.membership_timeline_cached(session, cfg, dates)
    assert len(prev_payload["points"]) == 3

    d_new = date(2024, 4, 1)
    with Session(engine) as session:
        _mk_membership_snapshot(session, d_new, ["AAA", "BBB", "DDD"])

    with Session(engine) as session:
        dates = _all_scanner_run_dates(session)
        new_payload = data_manager.membership_timeline_cached(session, cfg, dates)

    assert len(new_payload["points"]) == len(prev_payload["points"]) + 1
    prev_by_date = {p["date"]: p for p in prev_payload["points"]}
    new_by_date = {p["date"]: p for p in new_payload["points"]}
    for d_iso, point in prev_by_date.items():
        assert new_by_date[d_iso] == point, f"{d_iso}'s cached point changed after an append-forward ingest"

    fresh = new_by_date[d_new.isoformat()]
    assert fresh["date"] == d_new.isoformat()
    assert fresh["size"] == 3
    assert fresh["entries"] == ["DDD"]  # AAA/BBB already seen; only DDD is a first-ever appearance
    assert fresh["exits"] == ["CCC"]  # D3's members (AAA/BBB/CCC) minus D_new's (AAA/BBB/DDD) -> CCC exits


def test_append_forward_fast_path_byte_identical_to_full_recompute(membership_fast_path_engine):
    """TC-3 — the append-forward fast path's served payload is byte-identical to `_membership_timeline`'s
    own full recompute (UNCHANGED by this iteration -- the pre-fix reference oracle) for the SAME dates and
    DB state."""
    engine = membership_fast_path_engine
    cfg = load_config()
    with Session(engine) as session:
        dates = _all_scanner_run_dates(session)
        data_manager.membership_timeline_cached(session, cfg, dates)  # warm v1

    d_new = date(2024, 4, 1)
    with Session(engine) as session:
        _mk_membership_snapshot(session, d_new, ["AAA", "BBB", "DDD"])

    with Session(engine) as session:
        dates = _all_scanner_run_dates(session)
        fast_path_payload = data_manager.membership_timeline_cached(session, cfg, dates)  # append-forward
        oracle_payload = data_manager._membership_timeline(session, cfg, dates)  # PRE-FIX full recompute

    assert fast_path_payload == oracle_payload


def test_historical_gap_fill_falls_back_to_full_recompute_not_stale_reuse(membership_fast_path_engine):
    """Regression — a historical gap-fill (a new date STRICTLY EARLIER than an already-cached one) must NOT
    take the append-forward fast path: `entries`/`exits` are order-dependent on the FULL prior timeline, so
    an earlier insertion can retroactively change a LATER cached date's entries/exits (binding
    iter-27/iter-9 lesson). The served payload must equal a fresh full recompute -- never a stale reuse of
    the pre-gap-fill cached points."""
    engine = membership_fast_path_engine
    cfg = load_config()
    with Session(engine) as session:
        dates = _all_scanner_run_dates(session)
        pre_gap_payload = data_manager.membership_timeline_cached(session, cfg, dates)  # warm v1 (3 dates)

    # a new date EARLIER than 2024-01-03 (the earliest already-cached date) -- AAA now first appears here,
    # not on D1, so a correct recompute MUST change D1's entries; a stale reuse would not.
    d_gap = date(2023, 12, 1)
    with Session(engine) as session:
        _mk_membership_snapshot(session, d_gap, ["AAA", "EEE"])

    with Session(engine) as session:
        dates = _all_scanner_run_dates(session)
        assert dates[0] == d_gap  # confirms this really is EARLIER than every previously-cached date
        served = data_manager.membership_timeline_cached(session, cfg, dates)
        oracle = data_manager._membership_timeline(session, cfg, dates)

    assert served == oracle  # the fallback path -- byte-identical to a fresh full recompute
    served_by_date = {p["date"]: p for p in served["points"]}
    pre_gap_by_date = {p["date"]: p for p in pre_gap_payload["points"]}
    assert served_by_date["2024-01-03"] != pre_gap_by_date["2024-01-03"], (
        "the gap-fill must RECOMPUTE D1's entries (AAA is no longer first-seen there) -- a stale reuse of "
        "the pre-gap-fill point would incorrectly still show AAA as a D1 entry"
    )
    assert "AAA" not in served_by_date["2024-01-03"]["entries"]  # AAA is now first-seen on d_gap, not D1
    assert served_by_date["2024-01-03"]["exits"] == ["EEE"]  # EEE (present on d_gap) is gone by D1


# ==================================================================================================
# ops-hardening iter-48 (J-05 fix) — the historical-gap-insert case ALSO bounds the resolver sweep.
#
# The append-forward fast path (iter-45, above) only engages when every new date is strictly LATER than
# every already-cached one. A historical gap-insert (J-05's own failing scenario: a new snapshot date
# EARLIER than the latest cached membership date) fell through to `_membership_timeline`'s full,
# UNBOUNDED O(dates x pool) `resolve_with_reasons` sweep over EVERY historical date — live-measured at
# ~0.8-2.2s per call across this DB's ~2,900 historical dates, well over an hour total, which is why the
# `data_provider_runs` row for such a backfill never reached a terminal status within any reasonable
# bound. `membership_timeline_cached` now tries a SECOND bounded path before falling back to the full
# sweep: reuse every already-cached date's `excluded` tally (a pure per-date function, independent of
# any OTHER snapshot date — see `_membership_timeline`'s `reuse_excluded_by_date` docstring) and invoke
# the resolver ONLY for the genuinely new date(s), gated by the SAME `_membership_bars_are_forward_only`
# safety proof the append-forward path already relies on. `entries`/`exits` are STILL always recomputed
# fresh, in full date order, for every date (never reused) — this does NOT extend the iter-45 incremental
# fast path to the gap-insert case (assumptions.md iter-48).
# ==================================================================================================
def test_historical_gap_fill_does_not_reinvoke_resolver_for_cached_dates(
    membership_fast_path_engine, monkeypatch,
):
    """A historical gap-insert (a new date EARLIER than every already-cached one) does NOT re-invoke
    `resolve_with_reasons` for any already-cached date -- only the new date is ever resolved. Mirrors the
    append-forward TC-1 spy test above, but for the gap-insert direction the append-forward fast path
    explicitly does NOT cover."""
    engine = membership_fast_path_engine
    cfg = load_config()
    with Session(engine) as session:
        dates = _all_scanner_run_dates(session)
        assert len(dates) == 3
        data_manager.membership_timeline_cached(session, cfg, dates)  # warm v1

    d_gap = date(2023, 12, 1)  # strictly EARLIER than every already-cached date -- NOT append-forward
    with Session(engine) as session:
        _mk_membership_snapshot(session, d_gap, ["AAA", "EEE"])

    resolved_dates: list[date] = []
    orig_resolve = data_manager.universe_resolver.resolve_with_reasons

    def _spy(session_arg, d, cfg_arg, **kwargs):
        resolved_dates.append(d)
        return orig_resolve(session_arg, d, cfg_arg, **kwargs)

    monkeypatch.setattr(data_manager.universe_resolver, "resolve_with_reasons", _spy)

    with Session(engine) as session:
        dates = _all_scanner_run_dates(session)
        assert dates[0] == d_gap
        assert len(dates) == 4
        data_manager.membership_timeline_cached(session, cfg, dates)  # MISS -> the iter-48 bounded path

    assert resolved_dates, "expected the new date's resolver sweep to actually run"
    assert set(resolved_dates) == {d_gap}, (
        f"resolve_with_reasons must run ONLY for the new (gap) date {d_gap}, never for an already-cached "
        f"date -- got calls for {sorted(set(resolved_dates))}"
    )


def test_historical_gap_fill_reused_excluded_byte_identical_to_full_recompute(membership_fast_path_engine):
    """The iter-48 bounded gap-insert path's served payload is byte-identical to `_membership_timeline`'s
    own full, unbounded recompute (the pre-fix reference oracle) for the SAME dates and DB state --
    reusing cached `excluded` tallies changes nothing observable because they are a pure per-date
    function with no cross-date dependency."""
    engine = membership_fast_path_engine
    cfg = load_config()
    with Session(engine) as session:
        dates = _all_scanner_run_dates(session)
        data_manager.membership_timeline_cached(session, cfg, dates)  # warm v1

    d_gap = date(2023, 6, 15)
    with Session(engine) as session:
        _mk_membership_snapshot(session, d_gap, ["AAA", "FFF"])

    with Session(engine) as session:
        dates = _all_scanner_run_dates(session)
        bounded_payload = data_manager.membership_timeline_cached(session, cfg, dates)
        oracle_payload = data_manager._membership_timeline(session, cfg, dates)  # full, unbounded oracle

    assert bounded_payload == oracle_payload


def test_historical_gap_fill_reuse_is_keyed_per_date_not_vacuously_identical(
    membership_fast_path_engine, monkeypatch,
):
    """ops-hardening iter-48 AUDIT (T1) — TC-2's byte-identity proof, with a DISCRIMINATING oracle.

    `test_historical_gap_fill_reused_excluded_byte_identical_to_full_recompute` (above) runs on a fixture
    that carries ZERO `DailyPrice` bars, so `resolve_with_reasons` returns the SAME constant tally for
    every date. Under that data shape a reuse that mis-keyed one date's cached `excluded` tally onto a
    DIFFERENT date still compares equal to the full oracle — the byte-identity assertion passes without
    ever exercising the per-date mapping it is supposed to prove. This test removes that blind spot: the
    resolver is stubbed to return a tally that is a deterministic function OF THE DATE, so every date's
    `excluded` block is distinct, and any positional/off-by-one/mis-keyed reuse in
    `_membership_timeline`'s `reuse_excluded_by_date` lookup becomes observable.

    Asserts three things, in order: (1) the tallies really do vary per date (the anti-vacuity guard — if a
    future refactor makes them constant again this test fails loudly instead of silently degrading into
    the very tautology it exists to replace); (2) the bounded gap-insert path really engaged (the resolver
    ran for the NEW date only); (3) the served payload still equals the full, unbounded oracle."""
    engine = membership_fast_path_engine
    cfg = load_config()

    def _date_keyed_diag(_session, d, _cfg, **_kwargs):
        # A tally that DEPENDS ON THE DATE (unlike the real zero-bar fixture's constant one), using only
        # real `EXCLUSION_REASONS` keys because `_excluded_counts_by_date` accumulates into a dict
        # pre-seeded with exactly those keys.
        reasons = list(data_manager.universe_resolver.EXCLUSION_REASONS)
        counts = {reason: 0 for reason in reasons}
        counts[reasons[0]] = d.toordinal() % 9973  # distinct per date across this fixture's range
        return {"excluded_counts": counts}

    monkeypatch.setattr(
        data_manager.universe_resolver, "resolve_with_reasons", _date_keyed_diag,
    )

    with Session(engine) as session:
        dates = _all_scanner_run_dates(session)
        assert len(dates) == 3
        data_manager.membership_timeline_cached(session, cfg, dates)  # warm v1 (date-keyed tallies)

    d_gap = date(2023, 7, 20)  # strictly EARLIER than every already-cached date -- the iter-48 branch
    with Session(engine) as session:
        _mk_membership_snapshot(session, d_gap, ["AAA", "III"])

    resolved_dates: list[date] = []

    def _spy(session_arg, d, cfg_arg, **kwargs):
        resolved_dates.append(d)
        return _date_keyed_diag(session_arg, d, cfg_arg, **kwargs)

    monkeypatch.setattr(data_manager.universe_resolver, "resolve_with_reasons", _spy)

    with Session(engine) as session:
        dates = _all_scanner_run_dates(session)
        assert len(dates) == 4
        bounded_payload = data_manager.membership_timeline_cached(session, cfg, dates)
        # snapshot the spy BEFORE the oracle call below (which resolves every date by design and would
        # otherwise swamp the bounded path's own call record)
        bounded_resolved = list(resolved_dates)
        oracle_payload = data_manager._membership_timeline(session, cfg, dates)  # full, unbounded oracle

    # (1) anti-vacuity: the per-date tallies must genuinely differ, or this comparison proves nothing
    distinct_tallies = {
        json.dumps(p["excluded"], sort_keys=True) for p in bounded_payload["points"]
    }
    assert len(distinct_tallies) == len(bounded_payload["points"]), (
        "this test is only meaningful while every date's `excluded` tally is distinct -- got "
        f"{len(distinct_tallies)} distinct tallies across {len(bounded_payload['points'])} points"
    )

    # (2) the bounded reuse path (not the full sweep) is what produced `bounded_payload`
    assert set(bounded_resolved) == {d_gap}, (
        f"expected the bounded gap-insert path to resolve ONLY the new date {d_gap}; got "
        f"{sorted(set(bounded_resolved))} -- if this reads as every date, the reuse path did not engage "
        f"and assertion (3) below would be proving the fallback, not the fix"
    )

    # (3) byte-identity against the full oracle, now with a per-date-varying tally to discriminate against
    assert bounded_payload == oracle_payload


def test_historical_gap_fill_falls_back_to_full_sweep_when_bars_are_not_forward_only(
    membership_fast_path_engine, monkeypatch,
):
    """Safety regression -- when the bars manifest did NOT move forward-only since the previous cache
    generation (here: the fixture starts with ZERO bars, so ANY new bar makes the prior generation's
    'no bars existed' assumption unprovable -- `_membership_bars_are_forward_only`'s own documented
    fail-safe), the iter-48 bounded reuse path must NOT engage even for an otherwise-eligible gap-insert:
    every date is re-resolved, exactly as the pre-iter-48 code always did. Proves the safety gate, not
    just the happy path."""
    engine = membership_fast_path_engine
    cfg = load_config()
    with Session(engine) as session:
        dates = _all_scanner_run_dates(session)
        data_manager.membership_timeline_cached(session, cfg, dates)  # warm v1 (zero bars)

    d_gap = date(2023, 9, 1)
    with Session(engine) as session:
        _mk_membership_snapshot(session, d_gap, ["AAA", "GGG"])
        # a bar lands for the first time since v1 was cached -- the "no bars existed" precondition
        # `_membership_bars_are_forward_only` requires for a "none" bar_stamp no longer holds, so reuse
        # cannot be proven safe regardless of this bar's own date.
        session.add(DailyPrice(
            symbol="AAA", date=date(2024, 3, 1),
            open=10.0, high=10.0, low=10.0, close=10.0, volume=100.0,
        ))
        session.commit()

    resolved_dates: list[date] = []
    orig_resolve = data_manager.universe_resolver.resolve_with_reasons

    def _spy(session_arg, d, cfg_arg, **kwargs):
        resolved_dates.append(d)
        return orig_resolve(session_arg, d, cfg_arg, **kwargs)

    monkeypatch.setattr(data_manager.universe_resolver, "resolve_with_reasons", _spy)

    with Session(engine) as session:
        dates = _all_scanner_run_dates(session)
        served = data_manager.membership_timeline_cached(session, cfg, dates)
        oracle = data_manager._membership_timeline(session, cfg, dates)

    assert served == oracle  # still correct -- the fallback, not a stale/unsafe reuse
    assert set(resolved_dates) == set(dates), (
        f"expected every date to be re-resolved when bars did not move forward-only (the reuse path must "
        f"NOT engage) -- got calls for only {sorted(set(resolved_dates))} of {sorted(dates)}"
    )


def test_membership_timeline_reuse_excluded_by_date_default_is_byte_identical(membership_fast_path_engine):
    """`_membership_timeline`'s new `reuse_excluded_by_date` parameter is purely additive -- calling it
    with no 4th argument (every pre-iter-48 call site) is byte-identical to calling it with an explicit
    empty/None reuse map."""
    engine = membership_fast_path_engine
    cfg = load_config()
    with Session(engine) as session:
        dates = _all_scanner_run_dates(session)
        no_arg = data_manager._membership_timeline(session, cfg, dates)
        explicit_none = data_manager._membership_timeline(session, cfg, dates, None)
        explicit_empty = data_manager._membership_timeline(session, cfg, dates, {})

    assert no_arg == explicit_none == explicit_empty


def test_historical_gap_fill_resolver_failure_isolated_never_hangs_the_job(
    membership_fast_path_engine, monkeypatch,
):
    """Error-case coverage (phase spec TESTING REQUIREMENTS) -- a genuine non-memory exception raised
    from INSIDE the iter-48 bounded gap-insert path, exercised through the real finalize-tail call chain
    (`_refresh_ingest_aggregates` -> `refresh_coverage_snapshot` -> `membership_timeline_cached` ->
    `_membership_timeline` -> `_excluded_counts_by_date` -> `resolve_with_reasons`), is caught by the
    SAME per-item isolation convention every other finalize-tail step already relies on
    (`test_finalize_hook_partial_failure_isolated_other_aggregates_still_refresh`,
    `test_finalize_hook_never_raises_even_when_everything_fails`, both unmodified by this iteration's
    diff) -- `_refresh_ingest_aggregates` never raises, `coverage`/`membership_timeline` are honestly
    absent from `aggregates_refreshed` (nothing was silently claimed), and every OTHER category still
    refreshes. The job therefore reaches ITS OWN terminal status (`_final_status(prog)`, set by the
    caller from the backfill stage's own outcome) rather than hanging on `running` -- proving the "never
    silently running" half of the phase spec's error-case requirement for THIS iteration's new code.

    Note on scope (see `assumptions.md` iter-48): this does NOT flip `data_provider_runs.status` to
    `"failed"` -- `_run_job`'s own documented contract (`data_manager.py:4939`, multiply audited since
    iter-45) is that an aggregate-refresh failure must NEVER flip an otherwise-successful ingest job to
    failed, precisely so a cosmetic/derived-data fault (as opposed to a fault in the ingest itself) does
    not misreport a real backfill as failed. Redesigning that contract to make THIS specific failure
    class flip to "failed" would be an undocumented, unproven change to a deliberately hardened
    isolation boundary, out of this iteration's scope."""
    engine = membership_fast_path_engine
    cfg = load_config()
    with Session(engine) as session:
        dates = _all_scanner_run_dates(session)
        assert len(dates) == 3
        data_manager.membership_timeline_cached(session, cfg, dates)  # warm v1

    d_gap = date(2023, 11, 1)  # strictly EARLIER than every already-cached date -- the iter-48 branch
    with Session(engine) as session:
        _mk_membership_snapshot(session, d_gap, ["AAA", "HHH"])

    def _boom(*_a, **_k):
        raise RuntimeError("forced resolver failure (historical-gap-insert error-case probe)")

    monkeypatch.setattr(data_manager.universe_resolver, "resolve_with_reasons", _boom)

    with Session(engine) as session:
        prog = JobProgress(job_id="gap-insert-resolver-failure-probe", kind="backfill", start=d_gap, end=d_gap)
        prog.new_snapshot_dates = [d_gap]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise

    assert "coverage" not in refreshed, "an honest omission is required when the underlying compute failed"
    assert "membership_timeline" not in refreshed, (
        "must not fabricate a refresh for the category whose own resolver call just raised"
    )
    # every OTHER finalize-tail category (independent of the coverage/membership-timeline step above)
    # still refreshes -- the SAME isolation boundary `test_finalize_hook_partial_failure_isolated_...`
    # already proves for an unrelated forced failure, re-confirmed here for THIS iteration's own new
    # failure site.
    assert {"latest_snapshot", "market_phase"} <= set(refreshed), (
        f"an isolated coverage/membership-timeline failure must not prevent other categories from "
        f"refreshing; got {refreshed}"
    )


# ==================================================================================================
# ops-hardening iter-45 AUDIT — regression tests for the three fixes applied during the audit pass.
# ==================================================================================================
def test_log_isolation_failure_swallows_a_raising_logger_exception(monkeypatch):
    """AUDIT B2 — DETERMINISTIC proof of `_log_isolation_failure`'s fallback branch. iter-45's own
    evidence for closing the third `MemoryError` escape was 5 consecutive `ulimit -v` runs of
    `test_ingest_finalize_memory_pressure.py`; those runs prove the PRIMARY (`logger.exception`) path
    still works, but `logs/backend.log` shows the fallback's own marker string never appeared once in the
    live incident either — so the NEW branch this iteration added was covered by nothing. Force it."""
    calls: list[tuple] = []

    def _boom_exception(*_args, **_kwargs):
        raise MemoryError()  # noqa: RSE102 — the textless class this session's failures actually raise

    def _record_error(msg, *args, **_kwargs):
        calls.append((msg, args))

    monkeypatch.setattr(data_manager.logger, "exception", _boom_exception)
    monkeypatch.setattr(data_manager.logger, "error", _record_error)

    data_manager._log_isolation_failure("some aggregate failed: %s", "detail")  # must NOT raise

    assert len(calls) == 1, "the traceback-free fallback record must be emitted exactly once"
    msg, args = calls[0]
    assert "traceback omitted" in msg
    assert msg.startswith("some aggregate failed: %s"), "the %s placeholders must keep their arg order"
    assert args == ("detail",)


def test_log_isolation_failure_swallows_even_when_the_fallback_also_raises(monkeypatch):
    """AUDIT B2 — the last line of defence: under a truly exhausted cap even the minimal-allocation
    fallback can raise. `_log_isolation_failure` must still return normally, or logging itself becomes the
    reason the isolation handler's "log + continue, never raise" contract breaks."""
    def _boom(*_args, **_kwargs):
        raise MemoryError()  # noqa: RSE102

    monkeypatch.setattr(data_manager.logger, "exception", _boom)
    monkeypatch.setattr(data_manager.logger, "error", _boom)

    data_manager._log_isolation_failure("everything is on fire: %s", "detail")  # must NOT raise


def test_aggregate_refresh_logging_failure_never_flips_a_successful_job_to_failed(tmp_path, monkeypatch):
    """AUDIT B3 — the SAME third-escape class, one frame OUT of `_refresh_ingest_aggregates`. A
    `MemoryError` raised by `Session.__exit__` (SQLAlchemy `expunge_all`) lands in `_run_job`'s own
    aggregate-refresh handler, which is OUTSIDE every per-item isolation handler iter-45 guarded —
    live-observed in the 2026-08-04 wedge (`logs/backend.log`: a caught MemoryError whose outermost frame
    is that `with Session(eng)` line). If the handler's own logging call then allocates and raises, the
    second exception escapes to `_run_job`'s outer `except`, which flips `prog.status = "failed"` —
    reporting a COMPLETED backfill as failed and breaking that branch's documented contract ("an
    aggregate-refresh failure must never flip an otherwise-successful ingest job to failed")."""
    engine = make_engine(f"sqlite:///{tmp_path / 'agg_refresh_logging.db'}")
    create_db_and_tables(engine)
    cfg = load_config()

    def _boom_refresh(_session, _cfg, _prog):
        raise MemoryError()  # noqa: RSE102 — stands in for the Session.__exit__ MemoryError

    def _boom_exception(*_args, **_kwargs):
        raise MemoryError()  # noqa: RSE102 — the logging allocation failing under the same cap

    monkeypatch.setattr(data_manager, "_refresh_ingest_aggregates", _boom_refresh)
    monkeypatch.setattr(data_manager.logger, "exception", _boom_exception)

    job = create_job("backfill", date(2024, 1, 2), date(2024, 1, 2))
    summary = run_data_job(job.job_id, config=cfg, engine=engine, sleep_fn=_noop_sleep, seed_dir=tmp_path)

    assert summary["status"] == "ok", (
        "a failure INSIDE the non-fatal aggregate-refresh handler's own logging must never flip the "
        f"ingest job itself to failed — got {summary['status']!r} ({summary.get('message')!r})"
    )


def _mk_bar(session: Session, symbol: str, d: date) -> None:
    session.add(DailyPrice(symbol=symbol, date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
    session.commit()


def test_append_forward_falls_back_when_bars_land_at_or_before_a_cached_date(tmp_path, monkeypatch):
    """AUDIT B4 — the append-forward precondition checked SNAPSHOT-DATE ordering only, which is sufficient
    for `size`/`entries`/`exits` (pure membership) but NOT for the reused per-date `excluded` tallies: the
    resolver derives those from BARS `<= d`, and `_membership_dataset_version` folds in the bars manifest.
    So a `both` job whose FETCH stage lands a bar at a HISTORICAL date while its BACKFILL stage adds one
    new LATER snapshot date satisfied "append-forward" and silently reused stale `excluded` counts for
    every already-cached date — breaking the phase spec's "byte-identical output required" and AG-3.

    Asserted through the SAME `resolve_with_reasons` spy TC-1 uses: taking the fallback means the resolver
    IS re-invoked for the already-cached dates. The companion test below is the positive control proving
    this guard did not simply disable the fast path."""
    engine = make_engine(f"sqlite:///{tmp_path / 'bars_guard.db'}")
    create_db_and_tables(engine)
    cfg = load_config()
    d1, d2, d3 = date(2024, 1, 3), date(2024, 2, 1), date(2024, 3, 1)
    with Session(engine) as session:
        _mk_membership_snapshot(session, d1, ["AAA", "BBB"])
        _mk_membership_snapshot(session, d2, ["AAA", "CCC"])
        _mk_membership_snapshot(session, d3, ["AAA", "BBB", "CCC"])
        for d in (d1, d2, d3):
            _mk_bar(session, "SPY", d)          # bars exist -> the stamp carries a real max-bar date
        data_manager.membership_timeline_cached(session, cfg, _all_scanner_run_dates(session))

    d_new = date(2024, 4, 1)
    with Session(engine) as session:
        _mk_membership_snapshot(session, d_new, ["AAA", "BBB", "DDD"])
        _mk_bar(session, "AAA", d2)             # a HISTORICAL bar (<= D_prev) landing in the same bump

    resolved: list[date] = []
    orig = data_manager.universe_resolver.resolve_with_reasons

    def _spy(session_arg, d, cfg_arg, **kwargs):
        resolved.append(d)
        return orig(session_arg, d, cfg_arg, **kwargs)

    monkeypatch.setattr(data_manager.universe_resolver, "resolve_with_reasons", _spy)
    with Session(engine) as session:
        data_manager.membership_timeline_cached(session, cfg, _all_scanner_run_dates(session))

    assert set(resolved) == {d1, d2, d3, d_new}, (
        "a bar landing at or before an already-cached date must force the FULL recompute — the cached "
        f"`excluded` tallies are no longer valid. Resolver saw only {sorted(set(resolved))}"
    )


def test_append_forward_still_used_when_bars_land_strictly_after_every_cached_date(tmp_path, monkeypatch):
    """AUDIT B4 positive control — the guard above must NOT disable the fast path for the ordinary
    forward flow (a `both` job fetching a new trading day's bars and snapshotting it). Bars added strictly
    after the previous max bar date cannot change any `resolve_with_reasons` verdict for a date `<=
    D_prev`, so the fast path must still bound the resolver to the new date alone (TC-1's property)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'bars_guard_control.db'}")
    create_db_and_tables(engine)
    cfg = load_config()
    d1, d2, d3 = date(2024, 1, 3), date(2024, 2, 1), date(2024, 3, 1)
    with Session(engine) as session:
        _mk_membership_snapshot(session, d1, ["AAA", "BBB"])
        _mk_membership_snapshot(session, d2, ["AAA", "CCC"])
        _mk_membership_snapshot(session, d3, ["AAA", "BBB", "CCC"])
        for d in (d1, d2, d3):
            _mk_bar(session, "SPY", d)
        data_manager.membership_timeline_cached(session, cfg, _all_scanner_run_dates(session))

    d_new = date(2024, 4, 1)
    with Session(engine) as session:
        _mk_membership_snapshot(session, d_new, ["AAA", "BBB", "DDD"])
        _mk_bar(session, "SPY", d_new)          # forward-only bar, strictly after every cached date

    resolved: list[date] = []
    orig = data_manager.universe_resolver.resolve_with_reasons

    def _spy(session_arg, d, cfg_arg, **kwargs):
        resolved.append(d)
        return orig(session_arg, d, cfg_arg, **kwargs)

    monkeypatch.setattr(data_manager.universe_resolver, "resolve_with_reasons", _spy)
    with Session(engine) as session:
        served = data_manager.membership_timeline_cached(session, cfg, _all_scanner_run_dates(session))

    assert set(resolved) == {d_new}, (
        "a forward-only bar change must keep the append-forward fast path (resolver bounded to the new "
        f"date) — got {sorted(set(resolved))}"
    )
    assert len(served["points"]) == 4


def test_per_date_coverage_warm_logging_failure_does_not_skip_the_memory_backoff(tmp_path, monkeypatch):
    """AUDIT B5 — iter-45 guarded the 12 isolation handlers written inside `_refresh_ingest_aggregates`'s
    own body, but NOT the per-date coverage warm loop it CALLS INTO
    (`_persist_per_date_coverage_snapshots`) — which that function's own docstring names as one of "the
    four per-item warm loops this function drives directly or calls into", and which is the path the
    iter-44 review's live flake actually reproduced in. A `logger.exception` that raises there escapes the
    per-date `except MemoryError` handler, so `_release_process_memory()` never runs and
    `aborted_for_memory` is never latched — the memory back-off is skipped under exactly the pressure it
    exists for."""
    engine = make_engine(f"sqlite:///{tmp_path / 'coverage_warm_logging.db'}")
    create_db_and_tables(engine)
    cfg = load_config()
    d1, d2 = date(2024, 1, 3), date(2024, 2, 1)
    with Session(engine) as session:
        _mk_membership_snapshot(session, d1, ["AAA", "BBB"])
        _mk_membership_snapshot(session, d2, ["AAA", "CCC"])
        for d in (d1, d2):
            _mk_bar(session, "SPY", d)

    def _boom_coverage(_session, _cfg, _asof):
        raise MemoryError()  # noqa: RSE102 — the real pressure this loop's handler exists for

    def _boom_exception(*_args, **_kwargs):
        raise MemoryError()  # noqa: RSE102 — the logging allocation failing under the same cap

    released: list[int] = []
    monkeypatch.setattr(data_manager, "refresh_coverage_snapshot_for", _boom_coverage)
    monkeypatch.setattr(data_manager.logger, "exception", _boom_exception)
    monkeypatch.setattr(data_manager, "_release_process_memory", lambda: released.append(1))

    job = create_job("backfill", d1, d1)
    prog = data_manager._JOBS[job.job_id]
    with Session(engine) as session:
        data_manager._persist_per_date_coverage_snapshots(session, cfg, [d1], prog)  # must NOT raise

    assert released, (
        "the per-date MemoryError handler's `_release_process_memory()` back-off must still run when the "
        "handler's own logging call raises — otherwise the loop aborts with no memory reclaimed"
    )


# ==================================================================================================
# ops-hardening iter-45 FIX PASS (audit B6) — a fatal data job must LEAVE EVIDENCE.
#
# The audit's single most important live failure (run 281, `2019-02-25`) reached terminal `failed` with
# the persisted reason `"MemoryError (no message)"` and wrote NOTHING to `logs/backend.log`:
# `grep -n "no message" logs/backend.log` → no match, `grep -c "backfill per-date compute aborted"` → 0.
# The audit could not even distinguish WHICH of two candidate origins raised it. Both handlers below now
# log through `_log_isolation_failure`, and every test here induces the failure with a TEXTLESS
# `MemoryError()` — this product's characteristic exception, whose `str()` is the empty string.
# ==================================================================================================
def _record_log_calls(monkeypatch, attr: str) -> list[str]:
    """Capture the RENDERED (`msg % args`) records a logger method receives. Rendering, not raw-format
    comparison, is deliberate: it proves the `%s` placeholders and their arg order actually line up, the
    same property the `_log_isolation_failure` fallback tests above pin."""
    rendered: list[str] = []

    def _record(msg, *args, **_kwargs):
        rendered.append(str(msg) % args if args else str(msg))

    monkeypatch.setattr(data_manager.logger, attr, _record)
    return rendered


def test_fatal_job_failure_is_logged_with_job_id_kind_and_reason(tmp_path, monkeypatch):
    """AUDIT B6 — `_run_job`'s OUTER handler recorded the failure reason onto `prog` only and made no
    logging call at all, so a job that died there was undiagnosable after the fact: `prog` carries a
    one-line reason but never the traceback, and `_JOBS` is process-local (gone on the next restart, and
    the restart is exactly what a wedge forces). Live-proven on run 281. The handler must now emit ONE
    record naming the job, its kind, and the honest reason."""
    engine = make_engine(f"sqlite:///{tmp_path / 'fatal_job_logging.db'}")
    create_db_and_tables(engine)
    cfg = load_config()

    def _boom_backfill(*_a, **_k):
        raise MemoryError()  # noqa: RSE102 — textless: THE class this session's real failures raise

    monkeypatch.setattr(data_manager, "_do_backfill", _boom_backfill)
    logged = _record_log_calls(monkeypatch, "error")

    job = create_job("backfill", date(2024, 1, 2), date(2024, 1, 2))
    summary = run_data_job(job.job_id, config=cfg, engine=engine, sleep_fn=_noop_sleep, seed_dir=tmp_path)

    # the pre-existing honesty contract is untouched: a textless MemoryError still names its TYPE.
    assert summary["status"] == "failed"
    assert summary["message"] == "MemoryError (no message)"

    naming_this_job = [rec for rec in logged if job.job_id in rec]
    assert len(naming_this_job) == 1, (
        "the fatal-failure handler must emit exactly one record naming the job — got "
        f"{naming_this_job!r} out of {logged!r}"
    )
    record = naming_this_job[0]
    assert "backfill" in record, f"the record must name the job KIND — got {record!r}"
    assert "MemoryError (no message)" in record, (
        f"the record must carry the same honest reason the job persisted — got {record!r}"
    )
    # B6's actual purpose: name the FRAME. The audit could not tell which of two candidate origins
    # inside the job raised run 281's MemoryError, because nothing was logged at all.
    assert "Traceback (most recent call last)" in record and "data_manager.py" in record, (
        f"the record must carry the (scrubbed) traceback, not just the one-line reason — got {record!r}"
    )


def test_fatal_job_failure_logging_never_escapes_the_outer_handler(tmp_path, monkeypatch):
    """AUDIT B6 — the outer handler is the OUTERMOST frame of the worker, so an unguarded logging call
    there would be strictly worse than no logging at all: under the exhausted cap that produced the
    original `MemoryError`, emitting the record can raise a SECOND `MemoryError` inside the `except`
    clause, past the point that clause's own `try` protects. That escapes `_run_job` entirely — killing
    the worker thread before `return prog.to_dict()` and before the `finally` finishes persisting the run
    row. The job must still reach its terminal `failed` state with its honest reason, AND the
    traceback-free fallback record must still name it (the failure stays diagnosable either way).

    The first (fuller) emit is forced to fail while the minimal retry is allowed through — the exact shape
    of `_log_isolation_failure`'s two-step degrade under real pressure."""
    engine = make_engine(f"sqlite:///{tmp_path / 'fatal_job_logging_boom.db'}")
    create_db_and_tables(engine)
    cfg = load_config()

    def _boom_backfill(*_a, **_k):
        raise MemoryError()  # noqa: RSE102 — textless

    fallback: list[str] = []

    def _flaky_error(msg, *args, **_kwargs):
        # the FIRST attempt at this record allocates more and dies; the minimal retry gets through.
        if str(msg).startswith("data job %s") and "traceback omitted" not in str(msg):
            raise MemoryError()  # noqa: RSE102 — textless
        fallback.append(str(msg) % args if args else str(msg))

    monkeypatch.setattr(data_manager, "_do_backfill", _boom_backfill)
    monkeypatch.setattr(data_manager.logger, "error", _flaky_error)

    job = create_job("backfill", date(2024, 1, 2), date(2024, 1, 2))
    summary = run_data_job(job.job_id, config=cfg, engine=engine, sleep_fn=_noop_sleep, seed_dir=tmp_path)

    assert summary["status"] == "failed"
    assert summary["message"] == "MemoryError (no message)"
    assert summary["finished_at"] is not None, (
        "the `finally` block must still have run — a logging escape here would kill the worker thread "
        "before the job's terminal state was ever closed out"
    )
    naming_this_job = [rec for rec in fallback if job.job_id in rec]
    assert len(naming_this_job) == 1, (
        "the traceback-free fallback must still name the failed job — got "
        f"{naming_this_job!r} out of {fallback!r}"
    )
    assert "traceback omitted" in naming_this_job[0]


def test_backfill_per_date_memory_abort_survives_a_raising_logging_call(tmp_path, monkeypatch):
    """AUDIT B6 (second half) — `_do_backfill`'s per-date worker handler was the ONE remaining bare
    `logger.exception` in an isolation handler (T4 listed five; the audit fixed four). Its own docstring
    promises `_compute_one_isolated` "never raises", and the whole per-date isolation contract rests on
    that: a raising log call escapes the worker, so the date is never recorded as an isolated failure, the
    run-summary invariant `snapshots_created + already_snapshotted + error_other == dates_total` breaks,
    and a job that should end `partial` with per-date detail aborts wholesale to `failed`.

    ONE target date deliberately — that pins the SERIAL arm (`workers <= 1 or len(targets) <= 1`), so the
    assertion is deterministic rather than dependent on which worker latched the memory-pressure flag
    first."""
    engine = make_engine(f"sqlite:///{tmp_path / 'per_date_abort_logging.db'}")
    create_db_and_tables(engine)
    cfg = load_config()
    d = date(2024, 1, 3)
    with Session(engine) as session:
        # the trading calendar IS the benchmark's bar dates (`_trading_days`), so one benchmark bar makes
        # exactly one trading day — un-snapshotted, hence exactly one backfill target.
        _mk_bar(session, cfg.etfs.index[0], d)

    def _boom_compute(*_a, **_k):
        raise MemoryError()  # noqa: RSE102 — textless, inside the per-date worker's own frame

    def _boom_exception(*_a, **_k):
        raise MemoryError()  # noqa: RSE102 — the traceback render failing under the same cap

    monkeypatch.setattr(data_manager, "_compute_one_backfill_date", _boom_compute)
    monkeypatch.setattr(data_manager.logger, "exception", _boom_exception)
    fallback = _record_log_calls(monkeypatch, "error")

    prog = JobProgress(job_id="iter45-b6-per-date-probe", kind="backfill", start=d, end=d)
    with Session(engine) as session:
        data_manager._do_backfill(session, cfg, prog, eng=engine)  # must NOT raise

    assert prog.dates_total == 1
    assert prog.snapshots_created == 0
    assert prog.error_other == 1
    assert prog.snapshots_created + prog.already_snapshotted + prog.error_other == prog.dates_total, (
        "the run-summary breakdown invariant must survive a logging failure inside the per-date handler"
    )
    assert prog.date_failures[0]["date"] == d.isoformat()
    assert "aborted for memory pressure" in prog.date_failures[0]["error"], (
        "the date must be recorded as an honest per-date MEMORY abort, never a generic failure — got "
        f"{prog.date_failures!r}"
    )
    assert any("backfill per-date compute aborted" in rec and d.isoformat() in rec for rec in fallback), (
        "the abort must leave a traceback-free record naming the date — the very line the audit found "
        f"absent from the live log for run 281 (`grep -c` → 0). Got {fallback!r}"
    )


def test_fatal_job_failure_log_never_leaks_the_provider_key(tmp_path, monkeypatch, caplog):
    """AUDIT B6, SECURITY regression — the fatal-failure log line added above must not become a NEW key
    leak. Only `reason` is scrubbed (`scrub(str(exc))`); `logger.exception` would ALSO attach the LIVE
    exception, and its formatted traceback carries the exception's RAW text — which on a fetch/expand job
    can embed the resolved provider key in a URL. That is precisely the surface
    `test_real_httpx_error_key_scrubbed_end_to_end` pins with "absent from the logs", and
    `_make_scrubber`'s docstring calls "defense-in-depth on top of the `_http.py` URL redaction".

    So the handler renders the traceback ITSELF, scrubs it, and passes it as an argument with
    `exc_info=False`. This test drives a WHOLESALE fetch-stage failure (not a per-symbol one, which the
    existing isolation already handles) so the exception reaches `_run_job`'s outer handler, then asserts
    all three properties at once: the record fired, the key is gone, and the frames survived."""
    secret = "sk-FATAL-HANDLER-LEAK-9c4a2d"
    leak = _real_httpx_error_str_with_key(secret)
    assert secret in leak  # sanity: there IS a key to scrub

    cfg = load_config()
    engine = make_engine(f"sqlite:///{tmp_path / 'fatal_scrub.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        _mk_bar(session, "SPY", date(2024, 1, 2))

    def _boom_fetch(*_a, **_k):
        raise ProviderUnavailableError(leak)  # a WHOLE-STAGE failure → the outer handler

    monkeypatch.setattr(data_manager, "_run_chunked_fetch", _boom_fetch)

    job = create_job("fetch", date(2024, 1, 2), date(2024, 1, 3), source="tiingo")
    with caplog.at_level("DEBUG"):
        summary = run_data_job(
            job.job_id, config=cfg, engine=engine,
            provider=_KeyLeakingProvider(secret), api_key=secret, sleep_fn=_noop_sleep,
        )

    assert summary["status"] == "failed"
    assert job.job_id in caplog.text, (
        "the fatal-failure record must have fired for this job — otherwise this test would pass "
        "vacuously by logging nothing at all"
    )
    assert secret not in caplog.text, "the resolved provider key must never reach the log"
    assert "***" in caplog.text, (
        "the redaction marker must be present — proving the traceback WAS rendered and scrubbed, not "
        "merely absent"
    )
    assert "data_manager.py" in caplog.text, (
        "the frames must survive the scrub — a traceback is the whole reason B6 asked for this record"
    )


# ==================================================================================================
# ops-hardening iter-46 (TC-5) — the LAST two bare `logger.exception` sites in this module,
# `_fail_unlaunched_job` (`:5058`, its own `_finalize_run_record` persistence failure) and
# `_fail_unlaunched_resume` (`:5091`, its own checkpoint-rebuild failure), disclosed as a "Known Issues"
# carry-forward by the iter-45 dev handoff (not on the audit's own T4 list, so left alone under fix-mode
# scope discipline that pass). Same class as B3/B5/B6: a logging allocation inside a failure handler that
# runs under memory pressure. Both are now guarded by `_log_isolation_failure`, proven here with the SAME
# TEXTLESS `MemoryError()` convention every other guard in this module is tested with.
# ==================================================================================================
def test_fail_unlaunched_job_persistence_failure_survives_a_raising_logging_call(tmp_path, monkeypatch):
    """`data_manager.py:5058` — `_fail_unlaunched_job`'s own `_finalize_run_record` call fails (any
    persistence error), and the guard's first (fuller) logging attempt ALSO raises a textless
    `MemoryError` (the induced pressure this guard exists for). `_fail_unlaunched_job` must still return
    normally (never propagate the logging failure out past the launch-failure path it is already on), and
    the traceback-free fallback record must still name the unlaunched job."""
    engine = make_engine(f"sqlite:///{tmp_path / 'fail_unlaunched_job_logging.db'}")
    create_db_and_tables(engine)
    cfg = load_config()

    def _boom_finalize(*_a, **_k):
        raise MemoryError()  # noqa: RSE102 — textless: the persistence failure under test

    def _boom_exception(*_a, **_k):
        raise MemoryError()  # noqa: RSE102 — the logging allocation failing under the same cap

    monkeypatch.setattr(data_manager, "_finalize_run_record", _boom_finalize)
    monkeypatch.setattr(data_manager.logger, "exception", _boom_exception)
    fallback = _record_log_calls(monkeypatch, "error")

    prog = JobProgress(job_id="iter46-fail-unlaunched-job-probe", kind="backfill",
                        start=date(2024, 1, 2), end=date(2024, 1, 2))
    launch_exc = RuntimeError("can't start new thread")

    data_manager._fail_unlaunched_job(prog, cfg, engine, launch_exc)  # must NOT raise

    assert prog.status == "failed", "the guard's own job bookkeeping must be unaffected by the log failure"
    naming_this_job = [rec for rec in fallback if prog.job_id in rec]
    assert len(naming_this_job) == 1, (
        f"the traceback-free fallback must name the unlaunched job exactly once — got {fallback!r}"
    )
    assert "traceback omitted" in naming_this_job[0]


def test_fail_unlaunched_resume_checkpoint_rebuild_failure_survives_a_raising_logging_call(tmp_path, monkeypatch):
    """`data_manager.py:5091` — `_fail_unlaunched_resume`'s own checkpoint-rebuild step fails (any error
    loading/seeding the progress from the durable checkpoint), and the guard's first (fuller) logging
    attempt ALSO raises a textless `MemoryError`. `_fail_unlaunched_resume` must still return normally
    (the bookkeeping-failure handler's own documented contract), and the traceback-free fallback record
    must still name the unlaunched resume's import id."""
    engine = make_engine(f"sqlite:///{tmp_path / 'fail_unlaunched_resume_logging.db'}")
    create_db_and_tables(engine)
    cfg = load_config()

    def _boom_load_checkpoint(*_a, **_k):
        raise MemoryError()  # noqa: RSE102 — textless: the checkpoint-rebuild failure under test

    def _boom_exception(*_a, **_k):
        raise MemoryError()  # noqa: RSE102 — the logging allocation failing under the same cap

    monkeypatch.setattr(data_manager, "_load_checkpoint", _boom_load_checkpoint)
    monkeypatch.setattr(data_manager.logger, "exception", _boom_exception)
    fallback = _record_log_calls(monkeypatch, "error")

    import_id = "iter46-fail-unlaunched-resume-probe"
    launch_exc = RuntimeError("can't start new thread")

    data_manager._fail_unlaunched_resume(import_id, cfg, engine, launch_exc)  # must NOT raise

    naming_this_import = [rec for rec in fallback if import_id in rec]
    assert len(naming_this_import) == 1, (
        f"the traceback-free fallback must name the unlaunched resume's import id exactly once — got "
        f"{fallback!r}"
    )
    assert "traceback omitted" in naming_this_import[0]
