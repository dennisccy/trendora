"""ops-hardening iter-38 (J-07 closure, TC-1/TC-2) -- widens the iter-34/37 throwaway-DB drill lineage so a
submitted backfill genuinely targets a REAL K>=3-trading-day range (none pre-snapshotted), closing the
iter-37 gap (eval.md finding iter-37/o): the prior fixture
(runs/goal-ops-hardening-iter-34/mem-drill/seed_throwaway_db.py) deliberately seeded a single non-benchmark
DailyPrice row so EVERY backfill request against it was a fast 0-target no-op (needed for that iteration's
OWN step-4 memory-pressure goal, out of scope this iteration) -- `_do_backfill` never built
`prog._shared_bar_cache` and the finalize tail's `cache_ctx` (data_manager.py:3337-3338, this iteration's
line numbers) always resolved to `nullcontext()`, so the ONE state iter-37's own change creates (the shared
bar cache held resident across the WHOLE finalize tail, not just the compute stage) was never measured.

This script instead loads the REAL committed seed (`load_seed` -- the same ~590-symbol, 30-year price
history every other test module's `backfilled_job`-style fixture already uses) into a FRESH, disposable
sqlite file -- never the live `apps/backend/data/trendora.db` -- so the shared bar cache this drill
exercises carries realistic weight (comparable to the live basis' own documented ~1.13 GB figure,
reports/perf-budgets.md), not a near-empty synthetic stub that would make a VmPeak comparison mostly noise.

A K>=3-trading-day window comfortably BEFORE the seed's own latest trading day is picked as the backfill
target (`BUFFER_FROM_LATEST` trading days of buffer) so none of the K dates collide with
`_resolve_coverage_asof`'s "current" stamp -- `_persist_per_date_coverage_snapshots`'s own `todo` filter
skips whichever date equals "current" (already persisted by the direct `refresh_coverage_snapshot` call
that runs just before it in `_refresh_ingest_aggregates`), so picking a non-current window keeps all K
dates inside that loop's own per-date warm, maximizing what this drill actually exercises.

Usage: <venv python> seed_throwaway_db.py <db_path>
Prints a JSON summary line (target dates, seed stats) to stdout for the orchestrating shell.
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
from app.engine.data_manager import _trading_days  # noqa: E402
from app.seed_loader import load_seed  # noqa: E402

K = 3  # J-07 DoD: "dates_total >= 3"
BUFFER_FROM_LATEST = 8  # trading days of buffer before the seed's own latest date -- keeps every target
                         # date strictly non-"current" (see module docstring)


def main() -> None:
    db_path = sys.argv[1]
    t0 = time.perf_counter()

    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    cfg = load_config()

    load_summary = load_seed(engine, cfg)
    assert load_summary["loaded"], f"expected a fresh throwaway DB to load the seed fresh: {load_summary}"
    seed_elapsed = time.perf_counter() - t0

    with Session(engine) as session:
        trading = _trading_days(session, cfg)
    assert len(trading) > (BUFFER_FROM_LATEST + K), (
        f"seed should provide a long trading calendar, got {len(trading)} days"
    )

    end_idx = len(trading) - 1 - BUFFER_FROM_LATEST
    start_idx = end_idx - (K - 1)
    target_dates = trading[start_idx : end_idx + 1]
    assert len(target_dates) == K
    assert trading[-1] not in target_dates, "sanity: target dates must exclude the resolved 'current' as-of"

    out = {
        "db_path": db_path,
        "price_rows": load_summary["price_rows"],
        "symbols_ok": load_summary["symbols_ok"],
        "symbols_failed": load_summary["symbols_failed"],
        "seed_load_seconds": round(seed_elapsed, 2),
        "trading_calendar_span": [trading[0].isoformat(), trading[-1].isoformat()],
        "trading_calendar_days": len(trading),
        "target_start": target_dates[0].isoformat(),
        "target_end": target_dates[-1].isoformat(),
        "target_dates": [d.isoformat() for d in target_dates],
        "k": K,
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
