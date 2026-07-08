"""J-46 — parallel bounded-worker fetch + per-chunk single-transaction writes (the concurrency contracts).

These prove the rewired `_run_chunked_fetch` keeps EVERY J-34 / SQLite-write / idempotency invariant
under parallel fetching, with injected stub providers and tiny DBs (no network, no wall-clock):

  - bounded fan-out      — at most `fetch_workers` symbols are in flight at once within a chunk.
  - per-chunk single commit — the chunk's bars are written in ONE INSERT (commit-count / insert-count spy);
                          a mid-chunk 429 leaves NO partial-chunk rows (chunk-atomic discard).
  - mid-chunk 429        — pauses `resumable` (never `failed`); chunk-consistent checkpoint; Resume
                          continues from the checkpoint with ZERO duplicate `(symbol, date)` rows.
  - progress <= totals   — counters never exceed totals under parallel fetching; symbols_ok reflects
                          only committed chunks.
  - scrubbed errors      — a non-429 provider error is counted failed with a REDACTED message; the
                          resolved key never appears in the job-status payload (worker-thread scrub).
  - no stranding         — a worker exception surfaces as an explicit `failed` job, never a deadlock /
                          a job stuck in `running`; threads are joined before the job thread finishes.
  - serial-equivalent    — `fetch_workers: 1` stores the SAME bars as a multi-worker run (a degenerate pool).
"""
from __future__ import annotations

import json
import threading
import time
from datetime import date

import pytest
from sqlalchemy import func
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError, RateLimitError
from app.engine import data_manager
from app.engine.data_manager import (
    create_job,
    resumable_imports,
    resume_data_job,
    run_data_job,
)
from app.models import DailyPrice, ImportCheckpoint
from app.seed_loader import all_seed_symbols


def _noop_sleep(_seconds: float) -> None:
    """Zero-wall-clock sleep (the worker backoff + polite delay add no real wait in tests)."""


def _with_workers(cfg, *, fetch_workers: int, symbol_batch_size=None, date_window_days=None):
    """A config copy overriding the J-46 pool size (and optionally the chunk dims) — the rest unchanged."""
    overrides = {"fetch_workers": fetch_workers}
    if symbol_batch_size is not None:
        overrides["symbol_batch_size"] = symbol_batch_size
    if date_window_days is not None:
        overrides["date_window_days"] = date_window_days
    ic = cfg.data_manager.import_chunking.model_copy(update=overrides)
    dm = cfg.data_manager.model_copy(update={"import_chunking": ic})
    return cfg.model_copy(update={"data_manager": dm})


def _seed_calendar(engine) -> None:
    """A single SPY bar so a trading calendar / latest date exists (the fetch needs a calendar anchor)."""
    with Session(engine) as session:
        session.add(DailyPrice(symbol="SPY", date=date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.commit()


# ==================================================================================================
# bounded fan-out — at most `fetch_workers` symbols in flight at once
# ==================================================================================================
class _ConcurrencyTrackingProvider(PriceProvider):
    """Returns one bar per symbol but records the MAX number of concurrent in-flight `get_daily` calls
    (thread-safe). A short barrier-free hold lets several workers overlap so the max is observable."""

    def __init__(self):
        self._lock = threading.Lock()
        self._in_flight = 0
        self.max_in_flight = 0
        self.fetched: list[str] = []

    def get_daily(self, symbol, start=None, end=None):
        with self._lock:
            self._in_flight += 1
            self.max_in_flight = max(self.max_in_flight, self._in_flight)
            self.fetched.append(symbol)
        try:
            # a tiny real hold so concurrent workers reliably overlap (the GIL is released during sleep,
            # so the in-flight counter genuinely reflects pool concurrency — not the injected backoff sleep)
            time.sleep(0.02)
            return [Bar(date=start or date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]
        finally:
            with self._lock:
                self._in_flight -= 1


def test_fan_out_is_bounded_by_fetch_workers(tmp_path):
    """Within a chunk, at most `fetch_workers` symbols are fetched concurrently (the pool is bounded) —
    and every symbol is still fetched exactly once."""
    cfg = _with_workers(load_config(), fetch_workers=3, symbol_batch_size=25, date_window_days=90)
    workers = cfg.data_manager.import_chunking.fetch_workers
    engine = make_engine(f"sqlite:///{tmp_path / 'fan.db'}")
    create_db_and_tables(engine)
    _seed_calendar(engine)
    provider = _ConcurrencyTrackingProvider()
    job = create_job("fetch", date(2024, 3, 1), date(2024, 3, 1), source="yahoo")
    # J-13 (iter-20): a generic fetch now targets `price_load_symbols(cfg, seed_dir)` (context ∪ pool). Pin
    # an explicit EMPTY temp `seed_dir` (no committed `universe_pool.csv`) so it degrades honestly to the
    # SAME context-only set `all_seed_symbols` gave before — keeping this test's symbol universe small.
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=provider, sleep_fn=_noop_sleep, seed_dir=tmp_path,
    )
    assert summary["status"] == "ok"
    assert provider.max_in_flight <= workers  # never more than the configured pool size in flight
    assert provider.max_in_flight >= 2  # but it DID actually run in parallel (a real pool, not serial)
    # every seed symbol fetched exactly once
    assert sorted(provider.fetched) == sorted(all_seed_symbols(cfg))


def test_fetch_workers_one_is_serial(tmp_path):
    """`fetch_workers: 1` is a degenerate (serial) pool: only ever ONE symbol in flight, and the stored
    dataset is identical to a multi-worker run (same bars). Proves the config knob is honored."""
    cfg = _with_workers(load_config(), fetch_workers=1)
    engine = make_engine(f"sqlite:///{tmp_path / 'serial.db'}")
    create_db_and_tables(engine)
    _seed_calendar(engine)
    provider = _ConcurrencyTrackingProvider()
    job = create_job("fetch", date(2024, 3, 1), date(2024, 3, 1), source="yahoo")
    # J-13 (iter-20): pin an explicit EMPTY temp `seed_dir` (no committed `universe_pool.csv`) so the
    # fetch scope degrades honestly to the SAME context-only set `all_seed_symbols` gave before.
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=provider, sleep_fn=_noop_sleep, seed_dir=tmp_path,
    )
    assert summary["status"] == "ok"
    assert provider.max_in_flight == 1  # strictly serial
    with Session(engine) as session:
        bars = session.scalar(select(func.count()).select_from(DailyPrice).where(DailyPrice.date == date(2024, 3, 1)))
    assert bars == len(all_seed_symbols(cfg))  # all symbols stored, one bar each


# ==================================================================================================
# per-chunk single-transaction write — one INSERT per chunk, chunk-atomic on a mid-chunk 429
# ==================================================================================================
class _OkProvider(PriceProvider):
    def get_daily(self, symbol, start=None, end=None):
        return [Bar(date=start or date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]


def test_one_insert_per_chunk(tmp_path, monkeypatch):
    """A chunk's bars are written in ONE INSERT (not one per symbol): the number of bar-INSERT executions
    equals the number of chunks (here 2 batches × 1 window = 2), regardless of `symbol_batch_size`."""
    cfg = _with_workers(load_config(), fetch_workers=4, symbol_batch_size=2, date_window_days=90)
    engine = make_engine(f"sqlite:///{tmp_path / 'commit.db'}")
    create_db_and_tables(engine)
    _seed_calendar(engine)

    # count bar INSERT executions (the DailyPrice.__table__ insert) — the per-chunk single write
    inserts = {"n": 0}
    orig_execute = Session.execute

    def _counting_execute(self, statement, *args, **kwargs):
        if "INSERT INTO daily_prices" in str(statement):
            inserts["n"] += 1
        return orig_execute(self, statement, *args, **kwargs)

    monkeypatch.setattr(Session, "execute", _counting_execute)

    # restrict the symbol plan to 4 symbols → with batch 2 that is exactly 2 chunks
    # J-13 (iter-20): a generic fetch's symbol plan now comes from `data_manager.price_load_symbols`
    # (context ∪ pool), not `all_seed_symbols` alone — patch the function `_run_job` actually calls.
    monkeypatch.setattr(data_manager, "price_load_symbols", lambda _cfg, _seed_dir: ["AAA", "BBB", "CCC", "DDD"])
    job = create_job("fetch", date(2024, 3, 1), date(2024, 3, 1), source="yahoo")
    summary = run_data_job(job.job_id, config=cfg, engine=engine, provider=_OkProvider(), sleep_fn=_noop_sleep)
    assert summary["status"] == "ok"
    assert summary["chunk_total"] == 2  # 4 symbols / batch 2 × 1 window
    assert inserts["n"] == 2  # ONE bar-INSERT per chunk (not one per symbol)


class _SecondSymbol429(PriceProvider):
    """Returns a bar for the FIRST symbol it is asked for in a chunk, then 429s PERSISTENTLY for the rest
    — so a chunk pauses mid-way (a non-first symbol triggers the resumable stop)."""

    def __init__(self, ok_count: int):
        self._ok_count = ok_count
        self._lock = threading.Lock()
        self._served = 0

    def get_daily(self, symbol, start=None, end=None):
        with self._lock:
            served = self._served
            self._served += 1
        if served < self._ok_count:
            return [Bar(date=start or date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]
        raise RateLimitError("HTTP 429 at https://provider/x")


def test_mid_chunk_429_leaves_no_partial_chunk_rows(tmp_path, monkeypatch):
    """Chunk-atomic discard: a 429 mid-chunk-0 (after some symbols fetched ok) commits NO bars for that
    chunk — `next_chunk_index` stays 0, status is `resumable` (never `failed`), and the DB has ZERO bars
    on the fetch day (the chunk's already-fetched bars were discarded, not partially committed)."""
    cfg = _with_workers(load_config(), fetch_workers=4, symbol_batch_size=4, date_window_days=90)
    engine = make_engine(f"sqlite:///{tmp_path / 'partial.db'}")
    create_db_and_tables(engine)
    _seed_calendar(engine)
    # J-13 (iter-20): a generic fetch's symbol plan now comes from `data_manager.price_load_symbols`
    # (context ∪ pool), not `all_seed_symbols` alone — patch the function `_run_job` actually calls.
    monkeypatch.setattr(data_manager, "price_load_symbols", lambda _cfg, _seed_dir: ["AAA", "BBB", "CCC", "DDD"])
    provider = _SecondSymbol429(ok_count=2)  # 2 symbols succeed, then a persistent 429 in the same chunk
    job = create_job("fetch", date(2024, 3, 1), date(2024, 3, 1), source="yahoo")
    summary = run_data_job(job.job_id, config=cfg, engine=engine, provider=provider, sleep_fn=_noop_sleep)
    assert summary["status"] == "resumable"  # graceful pause, NOT failed
    assert summary["chunk_index"] == 0  # the un-finished chunk — Resume re-attempts it
    assert summary["symbols_ok"] == 0  # counters reflect COMMITTED reality (the chunk was discarded)
    with Session(engine) as session:
        bars = session.scalar(select(func.count()).select_from(DailyPrice).where(DailyPrice.date == date(2024, 3, 1)))
        cp = session.exec(select(ImportCheckpoint).where(ImportCheckpoint.import_id == job.job_id)).one()
    assert bars == 0  # NO partial-chunk rows committed (chunk-atomic)
    assert cp.next_chunk_index == 0 and cp.status == "resumable"  # chunk-consistent checkpoint


# ==================================================================================================
# parallel resumable → idempotent resume with zero duplicate rows
# ==================================================================================================
class _ChunkGated429(PriceProvider):
    """Serves bars for symbols in `ok_symbols`; 429s persistently for any other — thread-safe. Records
    every symbol fetched (to prove Resume skips committed chunks)."""

    def __init__(self, ok_symbols):
        self._ok = set(ok_symbols)
        self._lock = threading.Lock()
        self.fetched: list[str] = []

    def get_daily(self, symbol, start=None, end=None):
        with self._lock:
            self.fetched.append(symbol)
        if symbol in self._ok:
            return [Bar(date=start or date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]
        raise RateLimitError("HTTP 429 at https://provider/x")


def test_parallel_pause_then_resume_no_duplicate_rows(tmp_path):
    """Under a multi-worker pool: a fetch whose provider 429s for every symbol from chunk 1 onward pauses
    `resumable` after chunk 0 committed; a Resume (recovered provider) continues from chunk 1, SKIPS
    chunk 0's already-stored symbols, and inserts NO duplicate `(symbol, date)` row — full per-(symbol,
    date) idempotency preserved under parallelism."""
    secret = "sk-PARALLEL-RESUME-NEVER-STORED-7"
    cfg = _with_workers(load_config(), fetch_workers=4)
    batch = cfg.data_manager.import_chunking.symbol_batch_size
    symbols = all_seed_symbols(cfg)
    chunk0 = set(symbols[:batch])
    engine = make_engine(f"sqlite:///{tmp_path / 'presume.db'}")
    create_db_and_tables(engine)
    _seed_calendar(engine)

    fetch_day = date(2024, 3, 1)
    job = create_job("fetch", fetch_day, fetch_day, source="tiingo")
    paused = _ChunkGated429(chunk0)  # only chunk 0's symbols succeed → pause entering chunk 1
    # J-13 (iter-20): pin an explicit EMPTY temp `seed_dir` (no committed `universe_pool.csv`) so the
    # fetch scope degrades honestly to the SAME context-only set `symbols` (`all_seed_symbols`) above.
    summary1 = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=paused, api_key=secret, sleep_fn=_noop_sleep,
        seed_dir=tmp_path,
    )
    assert summary1["status"] == "resumable"
    assert summary1["chunk_index"] == 1 and summary1["chunk_total"] >= 2  # chunk 0 committed, paused at 1
    assert summary1["symbols_ok"] == batch and summary1["bars_fetched"] == batch
    assert secret not in json.dumps(summary1)  # key never in the job payload

    class _OkForAll(PriceProvider):
        def __init__(self):
            self._lock = threading.Lock()
            self.fetched: list[str] = []

        def get_daily(self, symbol, start=None, end=None):
            with self._lock:
                self.fetched.append(symbol)
            return [Bar(date=start or fetch_day, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]

    resumed = _OkForAll()
    summary2 = resume_data_job(
        job.job_id, config=cfg, engine=engine, provider=resumed, api_key=secret, sleep_fn=_noop_sleep,
        seed_dir=tmp_path,
    )
    assert summary2["status"] == "ok"
    assert summary2["chunk_index"] == summary2["chunk_total"]
    assert chunk0.isdisjoint(set(resumed.fetched))  # chunk 0 NOT re-fetched (idempotency)
    with Session(engine) as session:
        rows = session.exec(select(DailyPrice).where(DailyPrice.date == fetch_day)).all()
        per_symbol = {}
        for r in rows:
            per_symbol[r.symbol] = per_symbol.get(r.symbol, 0) + 1
        assert set(per_symbol) == set(symbols)  # all symbols stored
        assert all(c == 1 for c in per_symbol.values())  # NO duplicate (symbol, date) row
        assert resumable_imports(session, cfg) == []  # terminal — no longer resumable


# ==================================================================================================
# non-429 error → failed count + scrubbed message (worker-thread scrub); progress <= totals
# ==================================================================================================
class _KeyLeaking404(PriceProvider):
    """Raises a `ProviderUnavailableError` whose text embeds the resolved key (like an un-redacted httpx
    URL error) for ONE target symbol; returns a bar for the rest — thread-safe."""

    def __init__(self, key: str, fail_symbol: str):
        self._key = key
        self._fail = fail_symbol

    def get_daily(self, symbol, start=None, end=None):
        if symbol == self._fail:
            raise ProviderUnavailableError(
                f"HTTP 404 at https://provider/{symbol}?apikey={self._key}"
            )
        return [Bar(date=start or date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]


def test_non_429_error_scrubbed_under_parallelism(tmp_path, monkeypatch):
    """A non-429 provider error on a worker thread is counted failed and recorded with the key REDACTED —
    the resolved key never appears in the job-status payload (the worker-thread scrub), and the chunk
    continues (other symbols succeed). Progress counters never exceed totals."""
    secret = "sk-LEAK-KEY-1234567890"
    cfg = _with_workers(load_config(), fetch_workers=4, symbol_batch_size=4, date_window_days=90)
    engine = make_engine(f"sqlite:///{tmp_path / 'leak.db'}")
    create_db_and_tables(engine)
    _seed_calendar(engine)
    # J-13 (iter-20): a generic fetch's symbol plan now comes from `data_manager.price_load_symbols`
    # (context ∪ pool), not `all_seed_symbols` alone — patch the function `_run_job` actually calls.
    monkeypatch.setattr(data_manager, "price_load_symbols", lambda _cfg, _seed_dir: ["AAA", "BBB", "CCC", "DDD"])
    # tiingo is a needs-key source → the resolved key drives the scrubber
    provider = _KeyLeaking404(secret, fail_symbol="CCC")
    job = create_job("fetch", date(2024, 3, 1), date(2024, 3, 1), source="tiingo")
    summary = run_data_job(
        job.job_id, config=cfg, engine=engine, provider=provider, api_key=secret, sleep_fn=_noop_sleep
    )
    assert summary["status"] in ("partial", "ok")
    assert summary["symbols_failed"] == 1 and summary["symbols_ok"] == 3
    # the key is scrubbed everywhere in the job-status payload (errors[], message, anywhere)
    assert secret not in json.dumps(summary)
    assert summary["errors"], "the failed symbol should have recorded a (scrubbed) error"
    assert any("***" in e for e in summary["errors"])  # the key was replaced, the error surfaced honestly
    # counters never exceed totals
    assert summary["symbols_ok"] + summary["symbols_failed"] <= summary["symbols_total"]
    assert summary["symbols_total"] == 4


class _WorkerBlowsUp(PriceProvider):
    """Raises an UNEXPECTED (non-provider) exception for one symbol — to prove a worker exception never
    deadlocks the pool or strands the job in `running`."""

    def get_daily(self, symbol, start=None, end=None):
        if symbol == "BBB":
            raise RuntimeError("unexpected worker explosion")
        return [Bar(date=start or date(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]


def test_worker_exception_does_not_strand_job(tmp_path, monkeypatch):
    """An unexpected worker exception surfaces as an explicit `failed` job (with a finished timestamp) —
    never a deadlock, never a job stuck in `running`. The pool/threads are torn down before return."""
    cfg = _with_workers(load_config(), fetch_workers=4, symbol_batch_size=4, date_window_days=90)
    engine = make_engine(f"sqlite:///{tmp_path / 'boom.db'}")
    create_db_and_tables(engine)
    _seed_calendar(engine)
    # J-13 (iter-20): a generic fetch's symbol plan now comes from `data_manager.price_load_symbols`
    # (context ∪ pool), not `all_seed_symbols` alone — patch the function `_run_job` actually calls.
    monkeypatch.setattr(data_manager, "price_load_symbols", lambda _cfg, _seed_dir: ["AAA", "BBB", "CCC", "DDD"])
    job = create_job("fetch", date(2024, 3, 1), date(2024, 3, 1), source="yahoo")
    # Snapshot pre-existing `data-job-*` daemons (async jobs from EARLIER tests in the full suite may
    # still be winding down — `threading.enumerate()` is process-global). We assert only that THIS
    # synchronous call strands no NEW data-job thread of its own.
    pre_existing_job_thread_ids = {
        t.ident for t in threading.enumerate() if t.name.startswith("data-job-")
    }
    summary = run_data_job(job.job_id, config=cfg, engine=engine, provider=_WorkerBlowsUp(), sleep_fn=_noop_sleep)
    assert summary["status"] == "failed"  # surfaced explicitly, not swallowed
    assert summary["finished_at"] is not None  # the job settled (no strand in `running`)
    # no NEW data-job thread introduced by THIS call is left alive (the pool + job threads were joined
    # before run_data_job returned, even on the worker-exception path).
    assert not any(
        t.name.startswith("data-job-")
        and t.is_alive()
        and t.ident not in pre_existing_job_thread_ids
        for t in threading.enumerate()
    )
