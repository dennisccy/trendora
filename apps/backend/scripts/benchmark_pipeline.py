"""Advisory per-stage pipeline benchmark (J-46) — OFFLINE, no network, no keys.

This is OPERATOR-FACING evidence ONLY. It is NEVER imported by the test suite and NO wall-clock
assertion gates CI — it just measures, on the committed seed, the per-stage timings the J-46 work makes
faster, so an operator can see the pipeline's speed at any time:

  * Stage A — symbol FETCH: serial (``fetch_workers: 1``) vs the config parallel pool. Both run against
    an INJECTED OFFLINE stub provider (a small per-symbol artificial latency so the thread pool's win is
    observable) — NO real network, NO keys. This isolates the bounded-worker fan-out (Capability 38).
  * Stage B — SCAN / snapshot per date: the walk-forward ``run_scan`` over K dates, UNCACHED (the old
    per-date bar reload) vs the J-46 load-once ``bar_cache`` — the vectorized-load win (Capability 33).
    NOTE on the crossover: the cache loads each symbol's FULL series ONCE (then slices ``<= D`` in
    memory), whereas the uncached per-date query reads only the ``<= D`` prefix. So at a SMALL K the
    cache can be SLOWER (it pre-loads the whole tail before any reuse); its win grows with K (the
    full load is amortized across more dates). The load-COUNT proof (``<= 1`` bar-store load per symbol
    for the whole job, asserted in ``tests/test_bar_cache.py``) is the deterministic J-46 evidence; this
    wall-clock ratio is advisory and K-dependent. Default K is chosen past the crossover for the seed.
  * Stage C — FORWARD RETURNS: ``backfill_forward_returns`` over the cadence (single timing).
  * Stage D — MULTI-DATE BACKFILL job (J-53): the real ``run_data_job`` backfill, serial
    (``backfill_workers: 1``) vs the config parallel pool, over the SAME K dates on a fresh temp DB
    each. Reports the job's own ``per_date_seconds_sum`` so the ≥~2× speedup is visible as the
    sequential per-date sum vs the parallel wall-clock — advisory only, never a CI wall-clock gate.

Everything runs against a THROWAWAY temp DB loaded from the committed seed — it NEVER touches the live
host DB (``apps/backend/data/trendora.db``) or the committed ``data/seed/`` tree, and it computes nothing
canonical of its own (it calls the SAME engines the app uses).

Real baselines for context (this machine, this session — see the iteration notes):
  * a single walk-forward scan (``run_scan`` for one date over the seed universe) is ~30–40 s today;
  * the full backend pytest suite is ~34 min (639+ passed).
The absolute numbers below depend on the host; the SERIAL-vs-POOL and UNCACHED-vs-CACHED *ratios* are
the point — they show the J-46 speedups are real, not the wall-clock value.

Usage (from ``apps/backend``):
    .venv/bin/python scripts/benchmark_pipeline.py [--dates K] [--fetch-symbols N]
                                                   [--fetch-latency-ms MS] [--json]

``--dates K``           how many walk-forward dates to time the scan stage over (default 3).
``--fetch-symbols N``   how many symbols to time the fetch stage over (default 24; capped at the seed set).
``--fetch-latency-ms``  artificial per-symbol provider latency for the fetch stage so the pool's win is
                        visible offline (default 30 ms; pure sleep, no CPU, no network).
``--json``              also print the timings as a JSON object (for scripting / comparison over time).
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from datetime import date as date_cls
from pathlib import Path

# Make `app` importable when run as a script from apps/backend.
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from sqlmodel import Session  # noqa: E402

from app.config import load_config  # noqa: E402
from app.data_providers.base import Bar, PriceProvider  # noqa: E402
from app.db import create_db_and_tables, make_engine  # noqa: E402
from app.engine import data_manager, forward_testing, scanner  # noqa: E402
from app.engine.data_manager import _trading_days, create_job, run_data_job  # noqa: E402
from app.engine.prices import bar_cache  # noqa: E402
from app.seed_loader import all_seed_symbols, load_seed  # noqa: E402


class _OfflineLatencyProvider(PriceProvider):
    """An INJECTED offline provider: returns one synthetic bar per symbol after a fixed artificial
    latency (a pure sleep — no network, no CPU). The latency makes the bounded thread pool's overlap
    win observable in the fetch stage. It fabricates a price for the FETCH-TIMING DEMO only — this
    script's output is advisory, never a canonical value or a committed bar."""

    def __init__(self, latency_s: float):
        self._latency = latency_s

    def get_daily(self, symbol, start=None, end=None):
        time.sleep(self._latency)
        return [Bar(date=start or date_cls(2024, 3, 1), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]


def _time_fetch_stage(cfg, symbols, latency_s: float) -> dict:
    """Time the fetch stage serial (fetch_workers=1) vs the config parallel pool, over a fresh temp DB
    each (so neither run sees the other's stored bars). Offline injected provider only."""
    fetch_day = date_cls(2024, 3, 1)
    timings = {}
    for label, workers in (("serial (workers=1)", 1), (f"pool (workers={cfg.data_manager.import_chunking.fetch_workers})", None)):
        ic = cfg.data_manager.import_chunking.model_copy(
            update={"fetch_workers": workers} if workers is not None else {}
        )
        run_cfg = cfg.model_copy(
            update={"data_manager": cfg.data_manager.model_copy(update={"import_chunking": ic})}
        )
        with tempfile.TemporaryDirectory() as tmp:
            engine = make_engine(f"sqlite:///{Path(tmp) / 'fetch.db'}")
            create_db_and_tables(engine)
            with Session(engine) as session:  # a calendar anchor so the fetch has a latest date
                from app.models import DailyPrice
                session.add(DailyPrice(symbol="SPY", date=date_cls(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
                session.commit()
            # restrict the seed symbol set to the chosen N for a quick, comparable timing. J-13 (iter-20):
            # a generic fetch's symbol plan now comes from `data_manager.price_load_symbols` (context ∪
            # pool), not `all_seed_symbols` alone — patch the function `_run_job` actually calls.
            orig = data_manager.price_load_symbols
            data_manager.price_load_symbols = lambda _c, _s, _syms=symbols: list(_syms)
            try:
                job = create_job("fetch", fetch_day, fetch_day, source="yahoo")
                t0 = time.perf_counter()
                run_data_job(
                    job.job_id, config=run_cfg, engine=engine,
                    provider=_OfflineLatencyProvider(latency_s), sleep_fn=lambda _s: None,
                )
                timings[label] = time.perf_counter() - t0
            finally:
                data_manager.price_load_symbols = orig
    return timings


def _time_scan_stage(cfg, engine, dates) -> dict:
    """Time the scan/snapshot stage UNCACHED (per-date bar reload) vs the J-46 load-once cache, over the
    SAME K dates, on a fresh temp DB each so neither run reuses the other's snapshots."""
    timings = {}
    for label, use_cache in (("uncached (reload per date)", False), ("cached (load-once)", True)):
        with tempfile.TemporaryDirectory() as tmp:
            eng = make_engine(f"sqlite:///{Path(tmp) / 'scan.db'}")
            create_db_and_tables(eng)
            load_seed(eng, cfg)
            with Session(eng) as session:
                t0 = time.perf_counter()
                if use_cache:
                    with bar_cache(session):
                        for d in dates:
                            scanner.run_scan(session, d, cfg)
                else:
                    for d in dates:
                        scanner.run_scan(session, d, cfg)
                timings[label] = time.perf_counter() - t0
    return timings


def _time_backfill_stage(cfg, dates) -> dict:
    """J-53: time the MULTI-DATE snapshot backfill JOB — sequential (backfill_workers=1) vs the config
    parallel pool — over the SAME K dates, on a fresh temp DB each so neither run reuses the other's
    snapshots. Runs the real `run_data_job` backfill path (compute fanned out, writes serialized) so the
    measured wall-clock is exactly what the job's own stage timings report. Also returns the job's own
    `per_date_seconds_sum` from the parallel run so the ratio (sum vs wall-clock) is visible."""
    from app.engine.data_manager import create_job, run_data_job  # local import — same module family

    timings: dict = {}
    extra: dict = {}
    seq_workers = 1
    par_workers = cfg.data_manager.import_chunking.backfill_workers
    r_start, r_end = dates[0], dates[-1]
    for label, workers in (("serial (workers=1)", seq_workers), (f"pool (workers={par_workers})", par_workers)):
        ic = cfg.data_manager.import_chunking.model_copy(update={"backfill_workers": workers})
        run_cfg = cfg.model_copy(
            update={"data_manager": cfg.data_manager.model_copy(update={"import_chunking": ic})}
        )
        with tempfile.TemporaryDirectory() as tmp:
            eng = make_engine(f"sqlite:///{Path(tmp) / 'backfill.db'}")
            create_db_and_tables(eng)
            load_seed(eng, run_cfg)
            job = create_job("backfill", r_start, r_end)
            t0 = time.perf_counter()
            summary = run_data_job(job.job_id, config=run_cfg, engine=eng)
            timings[label] = time.perf_counter() - t0
            stage = summary.get("stages", {}).get("backfill", {})
            extra[label] = {
                "dates_done": summary.get("dates_done"),
                "per_date_seconds_sum": stage.get("per_date_seconds_sum"),
                "concurrency": stage.get("concurrency"),
            }
    return {"timings": timings, "extra": extra}


def _time_forward_returns(cfg) -> float:
    """Time backfill_forward_returns over the cadence on a fresh temp DB (single timing)."""
    with tempfile.TemporaryDirectory() as tmp:
        eng = make_engine(f"sqlite:///{Path(tmp) / 'fr.db'}")
        create_db_and_tables(eng)
        load_seed(eng, cfg)
        scanner.bootstrap_runs(eng, cfg)
        t0 = time.perf_counter()
        forward_testing.backfill_forward_returns(eng, cfg)
        return time.perf_counter() - t0


def _print_table(title: str, rows: dict) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    width = max((len(k) for k in rows), default=0)
    for label, secs in rows.items():
        print(f"  {label:<{width}}  {secs:8.3f} s")
    if len(rows) == 2:
        a, b = list(rows.values())
        if b > 0:
            print(f"  {'speedup':<{width}}  {a / b:8.2f} x")


def main() -> int:
    parser = argparse.ArgumentParser(description="Advisory per-stage pipeline benchmark (offline, J-46).")
    parser.add_argument("--dates", type=int, default=6, help="walk-forward dates to time the scan stage over (past the cache crossover for the seed)")
    parser.add_argument("--fetch-symbols", type=int, default=24, help="symbols to time the fetch stage over")
    parser.add_argument("--fetch-latency-ms", type=float, default=30.0, help="artificial per-symbol fetch latency (ms)")
    parser.add_argument("--json", action="store_true", help="also print the timings as JSON")
    args = parser.parse_args()

    cfg = load_config()
    with tempfile.TemporaryDirectory() as tmp:
        engine = make_engine(f"sqlite:///{Path(tmp) / 'seed.db'}")
        create_db_and_tables(engine)
        load_seed(engine, cfg)
        with Session(engine) as session:
            trading = _trading_days(session, cfg)
    # choose K consecutive recent-ish dates with full history before them
    k = max(1, args.dates)
    scan_dates = trading[200:200 + k] if len(trading) >= 200 + k else trading[-k:]
    fetch_symbols = all_seed_symbols(cfg)[: max(1, args.fetch_symbols)]

    print("=" * 72)
    print("Trendora pipeline benchmark (OFFLINE / advisory — no network, no keys)")
    print("=" * 72)
    print(f"seed symbols (full set): {len(all_seed_symbols(cfg))}")
    print(f"fetch stage symbols:     {len(fetch_symbols)} (artificial {args.fetch_latency_ms:.0f} ms/symbol latency)")
    print(f"scan stage dates (K):    {len(scan_dates)}  {[d.isoformat() for d in scan_dates]}")
    print(f"fetch_workers (config):  {cfg.data_manager.import_chunking.fetch_workers}")
    print(f"backfill_workers (cfg):  {cfg.data_manager.import_chunking.backfill_workers}")

    fetch_timings = _time_fetch_stage(cfg, fetch_symbols, args.fetch_latency_ms / 1000.0)
    _print_table("Stage A — symbol FETCH (serial vs parallel pool)", fetch_timings)

    scan_timings = _time_scan_stage(cfg, engine, scan_dates)
    _print_table("Stage B — SCAN / snapshot per date (uncached vs load-once cache)", scan_timings)

    fr_time = _time_forward_returns(cfg)
    _print_table("Stage C — FORWARD RETURNS (cadence backfill)", {"backfill_forward_returns": fr_time})

    # J-53: the multi-date backfill JOB — sequential per-date sum vs the parallel pool (the real win).
    backfill = _time_backfill_stage(cfg, scan_dates)
    _print_table(
        f"Stage D — MULTI-DATE BACKFILL job (serial vs parallel, {len(scan_dates)} dates)",
        backfill["timings"],
    )
    for label, ex in backfill["extra"].items():
        sumv, conc = ex.get("per_date_seconds_sum"), ex.get("concurrency")
        if sumv is not None:
            print(f"    {label}: per-date-sum {sumv:.3f} s · concurrency {conc}× · dates {ex.get('dates_done')}")

    if args.json:
        print("\n" + json.dumps({
            "fetch": fetch_timings,
            "scan": scan_timings,
            "forward_returns": {"backfill_forward_returns": fr_time},
            "backfill": backfill,
            "params": {
                "dates": len(scan_dates),
                "fetch_symbols": len(fetch_symbols),
                "fetch_latency_ms": args.fetch_latency_ms,
                "fetch_workers": cfg.data_manager.import_chunking.fetch_workers,
                "backfill_workers": cfg.data_manager.import_chunking.backfill_workers,
            },
        }, indent=2))
    print("\n(advisory only — ratios matter more than absolute wall-clock; never gates CI)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
