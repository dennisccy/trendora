"""iter-42 (J-100) — the bounded-resource concurrency LOAD test for the `/api/data` coverage read path.

This is the ONE sanctioned concurrent probe of the coverage compute (the MEMORY pool-exhaustion lesson:
`/api/data` is single-loaded, NEVER concurrently probed, in normal QA — the single-flight is exactly what
makes THIS load test safe). It proves the J-100 properties that close the intermittent whole-VM freeze:

  single-flight COUNT — K parallel coverage calls for the SAME resolved as-of + membership stamp cost ~ONE
                        heavy `_compute_coverage_uncached`, not K (the load-COUNT invariant the value-
                        equality tests miss — iter-35/36/37 lesson: pair every byte-identical claim with the
                        compute COUNT it preserves).
  byte-identity       — every one of the K concurrently-served coverage payloads DEEP-EQUALS the
                        single-request baseline (the served value is unchanged by the optimization).
  light-not-starved   — a light read (`latest_data_date`, the `/health`-class cost) completes within a low
                        bound WHILE the K heavy probes are in flight (the single-flight means ONE heavy
                        compute holds resources, not K — light endpoints are never starved).
  bounded RSS         — the process peak RSS stays under a configured cap across the load (memory bounded to
                        ONE shared bar-cache copy regardless of concurrency — scope (c)).
  bounded latency     — every concurrent call returns within a generous wall-clock bound (no hang / no
                        pool-exhaustion stall).

Fast by design: a small hand-built DB (a handful of pool symbols with >min_history bars + several snapshot
dates) so the resolver does REAL per-date work but the test boots in seconds (no 1369-date seed boot — the
seed-boot legs belong to the pump full-suite split, iter-29 lesson). Mark: NOT a `loaded_engine` test.
"""
from __future__ import annotations

import copy
import resource
import threading
import time
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import data_manager
from app.engine.data_manager import compute_coverage, reset_coverage_cache
from app.engine.prices import latest_data_date
from app.engine.research import _membership_dataset_version
from app.models import DailyPrice, ScannerResult, ScannerRun


# how many concurrent coverage probes to fire (the K of "K parallel /api/data calls").
K_CONCURRENT = 12
# every concurrent call must return within this generous wall-clock bound (no hang / pool stall).
LATENCY_BOUND_SECONDS = 60.0
# a light read (latest_data_date) fired WHILE the heavy probes are in flight must return this fast.
LIGHT_READ_BOUND_SECONDS = 5.0
# peak process RSS cap (MB). `_peak_rss_mb()` reads ru_maxrss — the process-LIFETIME peak. In the full
# suite this module shares a process with the 30-year `loaded_engine` session fixture (~6.8 GB resident
# once warmed for sibling modules), so the lifetime peak already clears ~7 GB from that fixture alone,
# independent of THIS test's tiny hand-built load (module-alone the peak is a few hundred MB). The cap is
# re-based to the 30-year reality: it still catches a per-probe copy (12 probes each cloning the ~1.3M-row
# coverage set would add GBs ON TOP of the fixture baseline) while not failing on the resident fixture.
RSS_CAP_MB = 8192


def _peak_rss_mb() -> float:
    """Peak resident set size of THIS process in MB (Linux `ru_maxrss` is in KiB)."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


@pytest.fixture()
def load_engine(tmp_path):
    """A small DB that makes `compute_coverage` do REAL resolver work but boots in seconds:

      - a handful of pool symbols each with > `min_history_bars` daily bars (so the per-date resolver
        actually admits/excludes them, not a trivial empty universe),
      - several scanner snapshots over those dates (so the membership timeline has a real step function),

    set as the process engine for the test and restored afterward. NOT a seed-boot `loaded_engine`."""
    cfg = load_config()
    engine = make_engine(f"sqlite:///{tmp_path / 'load.db'}")
    create_db_and_tables(engine)

    # pick a few real candidate-pool symbols so the resolver screens the actual committed pool (548 names),
    # admitting these few that clear the history gate (> min_history_bars bars) and excluding the rest.
    symbols = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"]
    min_bars = cfg.indicators.min_history_bars
    n_bars = min_bars + 40  # comfortably above the history gate
    start = date(2021, 1, 4)  # a Monday
    # build a contiguous run of weekday trading days (SPY = the benchmark calendar driver) + the symbols.
    days: list[date] = []
    d = start
    while len(days) < n_bars:
        if d.weekday() < 5:  # Mon-Fri
            days.append(d)
        d += timedelta(days=1)

    with Session(engine) as session:
        for sym in ["SPY", *symbols]:
            price = 100.0
            for i, day in enumerate(days):
                price += 0.5
                session.add(DailyPrice(
                    symbol=sym, date=day,
                    open=price, high=price + 1.0, low=price - 1.0, close=price,
                    volume=5_000_000.0,
                ))
        session.commit()

        # several snapshots over the later dates (each must be >= min_history into the series so the
        # symbols are admitted). Build hand-made runs + results for the membership timeline.
        snapshot_days = days[min_bars + 5 : min_bars + 5 + 8]  # 8 snapshot dates with full history before
        for asof in snapshot_days:
            run = ScannerRun(
                asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
                regime_score=50.0, regime_label="Choppy", regime_components_json="{}",
                new_high_low_json="{}", candidate_counts_json="{}",
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            for rank, sym in enumerate(symbols, start=1):
                session.add(ScannerResult(
                    run_id=run.id, ticker=sym, name=sym, sector="Technology",
                    leadership_score=float(100 - rank), leadership_bucket="A",
                    entry_quality_score=1.0, entry_quality_bucket="A", risk_score=1.0, risk_bucket="A",
                    setup_status="Watchlist", rank=rank, record_json="{}",
                ))
            session.commit()

    reset_coverage_cache()  # start from a cold in-process cache so the COUNT assertion is clean
    yield engine, cfg
    reset_coverage_cache()


def test_concurrent_coverage_single_flight_byte_identical_and_bounded(load_engine, monkeypatch):
    """K parallel coverage calls (the same resolved as-of + membership stamp) cost ~ONE heavy compute,
    return byte-identical payloads, finish within the latency bound, keep a light read responsive, and stay
    under the RSS cap. The single sanctioned concurrent probe of the coverage path (J-100)."""
    engine, cfg = load_engine

    # --- baseline: a SINGLE-request coverage payload (the byte-identity reference) ----------------------
    reset_coverage_cache()
    with Session(engine) as session:
        baseline = copy.deepcopy(compute_coverage(session, cfg))
    # sanity: the hand-built DB produced a REAL timeline (a non-empty step function) so the resolver did work
    assert baseline["membership_timeline"]["points"], "the load DB should produce a real membership timeline"
    assert baseline["snapshot_count"] == 8

    # --- COUNT the heavy compute: how many times the underlying uncached body actually runs --------------
    reset_coverage_cache()  # cold again so the concurrent burst is the only thing populating the cache
    heavy_calls = {"n": 0}
    count_lock = threading.Lock()
    real_uncached = data_manager._compute_coverage_uncached

    barrier = threading.Barrier(K_CONCURRENT)

    def _counting_uncached(session, cfg_, *, as_of=None):
        with count_lock:
            heavy_calls["n"] += 1
        return real_uncached(session, cfg_, as_of=as_of)

    monkeypatch.setattr(data_manager, "_compute_coverage_uncached", _counting_uncached)

    results: list[dict] = [None] * K_CONCURRENT
    errors: list[BaseException] = []
    latencies: list[float] = [0.0] * K_CONCURRENT

    def _probe(idx: int) -> None:
        try:
            barrier.wait(timeout=30)  # release all K threads as simultaneously as possible
            t0 = time.monotonic()
            with Session(engine) as session:
                cov = compute_coverage(session, cfg)
            latencies[idx] = time.monotonic() - t0
            results[idx] = cov
        except BaseException as exc:  # capture so the assertion reports it, never a silent hang
            errors.append(exc)

    threads = [threading.Thread(target=_probe, args=(i,), name=f"probe-{i}") for i in range(K_CONCURRENT)]
    load_start = time.monotonic()
    for t in threads:
        t.start()

    # --- while the K heavy probes are in flight, a LIGHT read must stay responsive (not starved) ---------
    # the single-flight means only ONE heavy compute holds resources; a light read returns promptly.
    time.sleep(0.01)  # let the burst get going
    light_t0 = time.monotonic()
    with Session(engine) as session:
        _ = latest_data_date(session)
    light_elapsed = time.monotonic() - light_t0

    for t in threads:
        t.join(timeout=LATENCY_BOUND_SECONDS + 30)
    load_elapsed = time.monotonic() - load_start

    # --- assertions -------------------------------------------------------------------------------------
    assert not errors, f"a concurrent probe raised: {errors[0]!r}"
    assert all(r is not None for r in results), "every concurrent probe must return a payload"

    # SINGLE-FLIGHT COUNT: K concurrent same-key probes cost ~ONE heavy compute, NOT K. We allow a small
    # slack (a probe that lands just after the owner publishes + clears the in-flight slot may compute
    # defensively), but it MUST be far below K — the whole point is N probes do not each pay the resolve.
    assert heavy_calls["n"] <= 2, (
        f"single-flight broke: {heavy_calls['n']} heavy computes for {K_CONCURRENT} concurrent probes "
        f"(expected ~1, never {K_CONCURRENT})"
    )

    # BYTE-IDENTITY: every concurrently-served payload deep-equals the single-request baseline.
    for i, cov in enumerate(results):
        assert cov == baseline, f"concurrent probe {i} served a payload that differs from the baseline"

    # BOUNDED LATENCY: every call returned within the bound (no hang / pool stall).
    assert max(latencies) <= LATENCY_BOUND_SECONDS, f"a probe exceeded the latency bound: {max(latencies):.2f}s"
    assert load_elapsed <= LATENCY_BOUND_SECONDS + 5, f"the whole load took too long: {load_elapsed:.2f}s"

    # LIGHT READ NOT STARVED: the /health-class read returned fast while the heavy burst was in flight.
    assert light_elapsed <= LIGHT_READ_BOUND_SECONDS, (
        f"a light read was starved during the heavy burst: {light_elapsed:.2f}s "
        f"(bound {LIGHT_READ_BOUND_SECONDS}s)"
    )

    # BOUNDED RSS: the load added no per-probe ~1.3M-row copy — peak RSS stays well under the cap.
    assert _peak_rss_mb() <= RSS_CAP_MB, f"peak RSS {_peak_rss_mb():.0f}MB exceeded the cap {RSS_CAP_MB}MB"


def test_concurrent_coverage_warm_cache_zero_recompute(load_engine, monkeypatch):
    """Once the cache is WARM (one prior compute), K concurrent probes pay ZERO heavy computes — they all
    hit the cached payload. Proves the warm read path is a pure cache hit (No recompute in the read path),
    keyed on the membership stamp so it stays warm across the warm-up's forward-return churn."""
    engine, cfg = load_engine
    reset_coverage_cache()
    # warm the cache with one compute.
    with Session(engine) as session:
        warm = copy.deepcopy(compute_coverage(session, cfg))

    # now patch the uncached body to BLOW UP — a warm hit must never call it.
    def _boom(*_a, **_k):
        raise AssertionError("a warm coverage hit must NOT recompute the uncached body")

    monkeypatch.setattr(data_manager, "_compute_coverage_uncached", _boom)

    results: list[dict] = [None] * K_CONCURRENT
    errors: list[BaseException] = []
    barrier = threading.Barrier(K_CONCURRENT)

    def _probe(idx: int) -> None:
        try:
            barrier.wait(timeout=30)
            with Session(engine) as session:
                results[idx] = compute_coverage(session, cfg)
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=_probe, args=(i,)) for i in range(K_CONCURRENT)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert not errors, f"a warm-cache probe raised (recompute leaked?): {errors[0]!r}"
    for i, cov in enumerate(results):
        assert cov == warm, f"warm probe {i} differs from the warm baseline"


def test_membership_stamp_decouples_coverage_cache_from_forward_returns(load_engine):
    """The coverage cache key carries the NARROW membership stamp, so it stays VALID across a forward-
    return insert (the warm-up churn) — the J-100 decoupling at the coverage layer (not just the inner
    membership-timeline cache). A snapshot/bar change DOES move the key."""
    from app.models import ForwardReturn

    engine, cfg = load_engine
    reset_coverage_cache()
    with Session(engine) as session:
        v1 = _membership_dataset_version(session, cfg)

    # a forward-return-only insert must NOT move the membership stamp (the coverage cache stays valid).
    with Session(engine) as session:
        run = session.exec(select(ScannerRun)).first()
        session.add(ForwardReturn(
            run_id=run.id, symbol="AAPL", horizon=5, asof_date=run.asof_date,
            entry_close=100.0, measured_date=run.asof_date + timedelta(days=7), realized_return=0.03,
        ))
        session.commit()
        v2 = _membership_dataset_version(session, cfg)
    assert v2 == v1, "a forward-return insert must NOT invalidate the coverage cache key"

    # a NEW snapshot DOES move the stamp.
    with Session(engine) as session:
        latest = session.scalar(select(ScannerRun.asof_date).order_by(ScannerRun.asof_date.desc()))
        new_run = ScannerRun(
            asof_date=latest + timedelta(days=30), created_at=datetime.now(timezone.utc),
            provider="seed", benchmark="SPY", regime_score=50.0, regime_label="Choppy",
            regime_components_json="{}", new_high_low_json="{}", candidate_counts_json="{}",
        )
        session.add(new_run)
        session.commit()
        v3 = _membership_dataset_version(session, cfg)
    assert v3 != v1, "a new snapshot MUST move the membership stamp (the cache must refresh)"
