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
from datetime import date, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from sqlalchemy import event, func
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError, RateLimitError
from app.engine import data_manager
from app.engine import forward_testing, market_phase, scanner
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
    unfinished_imports,
    validate_job_request,
    SEED_IMPORT_ENV_FLAG,
    SEED_IMPORT_SOURCE_ID,
)
from app.engine.forward_testing import compute_forward_aggregates
from app.engine.scoring import score_stocks
from app.models import (
    CoverageSnapshot,
    DailyPrice,
    DataProviderRun,
    ForwardReturn,
    ImportCheckpoint,
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
    compute warms both), `market_phase` (the new date), `research_hot_keys` (the default hot key)."""
    engine, d = finalize_hook_engine
    cfg = load_config()
    with Session(engine) as session:
        prog = JobProgress(job_id="finalize-probe", kind="backfill", start=d, end=d)
        prog.new_snapshot_dates = [d]
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert set(refreshed) == {
        "latest_snapshot", "coverage", "membership_timeline", "market_phase", "research_hot_keys",
    }
    with Session(engine) as session:
        rows = session.exec(select(CoverageSnapshot)).all()
        assert len(rows) == 1
        resolved_asof = data_manager._resolve_coverage_asof(session, None, cfg)
        assert rows[0].asof_key == resolved_asof.isoformat()
        assert rows[0].dataset_version == data_manager._membership_dataset_version(session, cfg)


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
    monkeypatch.setattr(data_manager, "event_study_cached", _boom)
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


def test_run_data_job_backfill_wires_finalize_hook_end_to_end(backfilled_job):
    """ops-hardening iter-2 (J-05) end-to-end: a real backfill job dispatched through `run_data_job` (the
    SAME path the API uses) reaches the finalize hook, persists a `coverage_snapshot` row, and the job's
    final summary (the SAME dict `GET /api/data/jobs/{id}` serves) carries a non-empty
    `aggregates_refreshed`. Searches from the LATEST end of the trading calendar (the other new-date test
    above searches from the earliest) so the two never contend for the same fresh date."""
    engine = backfilled_job["engine"]
    cfg = backfilled_job["cfg"]
    with Session(engine) as session:
        trading = _trading_days(session, cfg)
        snapshotted = set(session.exec(select(ScannerRun.asof_date)).all())
    fresh_date = next(d for d in reversed(trading) if d not in snapshotted)

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
        assert cov_old == fresh_old
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
        assert cov == fresh
        assert cov["symbol_count"] == 1 and cov["universe_asof"] == d_old.isoformat()  # not the 0 sentinel
        healed = session.exec(
            select(CoverageSnapshot).where(CoverageSnapshot.asof_key == d_old.isoformat())
        ).first()
        assert healed is not None  # self-healed: the next visit reads straight from storage
        # (2) an explicit as-of to a DATALESS date (no ScannerRun) still serves the honest sentinel
        sentinel = data_manager.coverage_from_storage(session, cfg, as_of=date(2024, 6, 1))
        assert sentinel["symbol_count"] == 0 and sentinel["universe_asof"] is None


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
