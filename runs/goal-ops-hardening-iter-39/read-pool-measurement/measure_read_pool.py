"""ops-hardening iter-39 (TC-13, audit finding iter-38/B3) -- an IN-SITU wall-clock measurement of
`universe_screen.read_pool()`'s real cost during a REAL K>=3-date backfill, replacing the prior
micro-benchmark-times-call-count PROJECTION (`perf-budgets.md`: "0.5628 ms/call, warm cache, 2,000 calls"
projected against "~20,680 calls" derived from the batch width, `1,880 x 11` -- never an instrumented
count, per the iter-38 audit's own finding B3/annotation).

Method: monkeypatch `read_pool` in EVERY module that imports it directly (`data_manager`,
`universe_resolver` -- `seed_loader`'s own import is irrelevant here, seed loading already happened) with
a counting/timing wrapper that calls straight through to the REAL implementation (byte-identical return
value, zero behavior change) while accumulating call count + total elapsed wall-clock time. Then runs a
REAL K=3-date backfill through `run_data_job` -- the SAME function `POST /api/data/jobs` calls -- against a
FRESH throwaway DB seeded from the real committed seed (same lineage as `mem-drill/seed_throwaway_db.py`,
just a separate DB file so this measurement never shares a process/DB with the concurrent J-07 step-4
drill). No live backend/uvicorn process needed -- this calls the same engine functions directly, in-process.

Usage: <venv python> measure_read_pool.py <db_path>
Prints a JSON summary (call count, total/mean/min/max elapsed, K, dates) to stdout.
"""
from __future__ import annotations

import json
import sys
import time

BACKEND_ROOT = "/home/dennis-chan/Git/trendora/apps/backend"
sys.path.insert(0, BACKEND_ROOT)

from sqlmodel import Session  # noqa: E402

from app.config import load_config  # noqa: E402
from app.db import create_db_and_tables, make_engine  # noqa: E402
from app.engine import data_manager, universe_resolver  # noqa: E402
from app.engine.data_manager import _trading_days, create_job, run_data_job  # noqa: E402
from app.engine.universe_screen import read_pool as _real_read_pool  # noqa: E402
from app.seed_loader import load_seed  # noqa: E402

K = 3  # matches TC-13's own "K>=3" requirement and the J-07 step-4 drill's own K
BUFFER_FROM_LATEST = 5  # trading days of buffer before the seed's own latest date


class _Timer:
    def __init__(self) -> None:
        self.calls = 0
        self.total_s = 0.0
        self.samples: list[float] = []

    def wrapped(self, *args, **kwargs):
        t0 = time.perf_counter()
        result = _real_read_pool(*args, **kwargs)
        elapsed = time.perf_counter() - t0
        self.calls += 1
        self.total_s += elapsed
        self.samples.append(elapsed)
        return result


def main() -> None:
    db_path = sys.argv[1]
    t_setup0 = time.perf_counter()

    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    cfg = load_config()

    load_summary = load_seed(engine, cfg)
    assert load_summary["loaded"], f"expected a fresh throwaway DB to load the seed fresh: {load_summary}"

    with Session(engine) as session:
        trading = _trading_days(session, cfg)
    assert len(trading) > (BUFFER_FROM_LATEST + K), f"seed should provide a long trading calendar, got {len(trading)} days"

    end_idx = len(trading) - 1 - BUFFER_FROM_LATEST
    start_idx = end_idx - (K - 1)
    target_dates = trading[start_idx : end_idx + 1]
    assert len(target_dates) == K

    setup_elapsed = time.perf_counter() - t_setup0

    # Monkeypatch EVERY module-level reference read_pool was imported into (see module docstring) --
    # the wrapper calls straight through to the REAL function, so the backfill's own behavior/output is
    # byte-identical; only timing/counting is added.
    timer = _Timer()
    data_manager.read_pool = timer.wrapped
    universe_resolver.read_pool = timer.wrapped

    job = create_job("backfill", target_dates[0], target_dates[-1])
    t_job0 = time.perf_counter()
    summary = run_data_job(job.job_id, config=cfg, engine=engine)
    job_elapsed = time.perf_counter() - t_job0

    assert summary["status"] == "ok", f"expected the measurement backfill to complete cleanly: {summary}"

    out = {
        "db_path": db_path,
        "k": K,
        "target_dates": [d.isoformat() for d in target_dates],
        "seed_setup_seconds": round(setup_elapsed, 2),
        "backfill_job_seconds": round(job_elapsed, 3),
        "read_pool_calls": timer.calls,
        "read_pool_total_seconds": round(timer.total_s, 6),
        "read_pool_mean_ms": round((timer.total_s / timer.calls) * 1000, 4) if timer.calls else None,
        "read_pool_min_ms": round(min(timer.samples) * 1000, 4) if timer.samples else None,
        "read_pool_max_ms": round(max(timer.samples) * 1000, 4) if timer.samples else None,
        "aggregates_refreshed": summary.get("aggregates_refreshed"),
        "dates_total": summary.get("dates_total"),
        "snapshots_created": summary.get("snapshots_created"),
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
